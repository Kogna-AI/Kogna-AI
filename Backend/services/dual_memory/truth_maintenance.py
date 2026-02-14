"""
Truth Maintenance System for Kogna 1.5
=======================================

Prevents memory corruption through:
1. Deduplication: Detects if a fact already exists before inserting
2. Conflict Detection: Identifies contradictory facts
3. Conflict Resolution: Uses heuristics to resolve disputes

Design Philosophy:
- CONSERVATIVE: When in doubt, flag as CONTESTED rather than overwrite
- TRANSPARENT: Log all conflicts and resolutions for auditing
- USER-IN-THE-LOOP: For critical conflicts, ask user to resolve
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from supabase import Client
import difflib

logger = logging.getLogger(__name__)


class TruthMaintenanceSystem:
    """
    Manages the integrity of the knowledge base.

    Responsibilities:
    - Prevent duplicate facts from being stored
    - Detect contradictions between new and existing facts
    - Resolve conflicts using source authority and recency
    - Flag irresolvable conflicts for user review
    """

    def __init__(self, supabase: Client, user_id: str):
        """
        Initialize TMS.

        Args:
            supabase: Supabase client
            user_id: User ID (all operations are user-scoped)
        """
        self.supabase = supabase
        self.user_id = user_id

        # Authority hierarchy (higher number = more authoritative)
        self.authority_weights = {
            'ERP': 1.0,          # Highest: Integrated systems
            'USER_UPLOAD': 0.9,  # High: User explicitly uploaded
            'PDF': 0.8,          # Medium-High: Documents
            'API': 0.7,          # Medium: External APIs
            'CHAT': 0.5,         # Medium-Low: Conversational extraction
            'UNKNOWN': 0.3       # Low: Unverified source
        }

    async def verify_and_store_fact(
        self,
        fact_type: str,  # 'business_fact', 'risk', 'company_context', 'metric'
        fact_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Main entry point: Verify a fact before storing.

        This performs:
        1. Deduplication check
        2. Conflict detection
        3. Smart insertion/update

        Args:
            fact_type: Type of fact ('business_fact', 'risk', 'company_context')
            fact_data: The fact to store (must include all required fields)

        Returns:
            {
                'action': 'INSERTED' | 'UPDATED' | 'CONFIRMED' | 'CONTESTED' | 'SKIPPED',
                'fact_id': UUID or None,
                'conflict_id': UUID or None (if CONTESTED),
                'message': Human-readable explanation
            }
        """

        # Route to appropriate handler
        if fact_type == 'business_fact':
            return await self._verify_business_fact(fact_data)
        elif fact_type == 'risk':
            return await self._verify_risk(fact_data)
        elif fact_type == 'company_context':
            return await self._verify_company_context(fact_data)
        else:
            logger.warning(f"Unknown fact type: {fact_type}")
            return {
                'action': 'SKIPPED',
                'fact_id': None,
                'message': f'Unknown fact type: {fact_type}'
            }

    async def _verify_business_fact(self, fact_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify and store a business fact.

        Deduplication strategy:
        - Check if a fact with the same (subject, predicate) exists
        - If values match → CONFIRM (boost confidence)
        - If values differ → Check if it's an UPDATE or CONFLICT
        """

        subject = fact_data.get('subject', '').strip()
        predicate = fact_data.get('predicate', '').strip()
        new_value = fact_data.get('value', '').strip()
        new_confidence = fact_data.get('confidence_score', 0.7)
        new_source = fact_data.get('source_authority', 'UNKNOWN')

        # Find existing facts with same subject
        try:
            existing = self.supabase.table('user_business_facts').select('*').eq(
                'user_id', self.user_id
            ).ilike('subject', f'%{subject}%').is_(
                'valid_to', None  # Only active facts
            ).execute()

            existing_facts = existing.data or []

        except Exception as e:
            logger.error(f"Error querying existing facts: {e}")
            existing_facts = []

        # Scenario 1: No existing facts → INSERT
        if not existing_facts:
            return await self._insert_fact('user_business_facts', fact_data)

        # Scenario 2: Exact duplicate → CONFIRM
        for existing_fact in existing_facts:
            if self._is_semantic_duplicate(existing_fact, fact_data):
                # Same fact, boost confidence
                return await self._confirm_fact('user_business_facts', existing_fact['id'], new_confidence)

        # Scenario 3: Check for VALUE conflicts
        for existing_fact in existing_facts:
            if existing_fact.get('predicate', '').strip().lower() == predicate.lower():
                existing_value = existing_fact.get('value', '').strip()

                # Different values for same predicate → Potential CONFLICT
                if not self._values_are_compatible(existing_value, new_value):
                    # Check if this is a temporal update (old data → new data)
                    is_temporal_update = self._is_temporal_progression(existing_fact, fact_data)

                    if is_temporal_update:
                        # Graceful update: deprecate old, insert new
                        return await self._deprecate_and_insert(
                            'user_business_facts',
                            existing_fact['id'],
                            fact_data,
                            reason="Temporal progression (old data updated)"
                        )
                    else:
                        # True conflict: cannot auto-resolve
                        return await self._flag_conflict(
                            'user_business_facts',
                            existing_fact,
                            fact_data,
                            conflict_type='VALUE_MISMATCH'
                        )

        # Scenario 4: Related but different predicate → INSERT (new facet of same subject)
        return await self._insert_fact('user_business_facts', fact_data)

    async def _verify_risk(self, fact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify and store a risk."""

        title = fact_data.get('title', '').strip()

        # Find existing risks with similar titles
        try:
            existing = self.supabase.table('user_risks').select('*').eq(
                'user_id', self.user_id
            ).ilike('title', f'%{title[:20]}%').is_(
                'valid_to', None
            ).execute()

            existing_risks = existing.data or []

        except Exception as e:
            logger.error(f"Error querying existing risks: {e}")
            existing_risks = []

        # Deduplication: Use fuzzy string matching on title
        for existing_risk in existing_risks:
            similarity = difflib.SequenceMatcher(
                None,
                title.lower(),
                existing_risk.get('title', '').lower()
            ).ratio()

            if similarity > 0.8:  # 80% similar → likely duplicate
                return await self._confirm_fact('user_risks', existing_risk['id'], fact_data.get('confidence_score', 0.7))

        # No duplicate found → INSERT
        return await self._insert_fact('user_risks', fact_data)

    async def _verify_company_context(self, fact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify and store company context."""

        key = fact_data.get('key', '').strip()
        new_value = fact_data.get('value', '').strip()

        # Company context uses UPSERT (key is unique per user)
        try:
            existing = self.supabase.table('user_company_context').select('*').eq(
                'user_id', self.user_id
            ).eq('key', key).execute()

            existing_contexts = existing.data or []

        except Exception as e:
            logger.error(f"Error querying company context: {e}")
            existing_contexts = []

        if not existing_contexts:
            # No existing → INSERT
            return await self._insert_fact('user_company_context', fact_data)

        # Existing context found
        existing_context = existing_contexts[0]
        existing_value = existing_context.get('value', '').strip()

        # Same value → CONFIRM
        if existing_value.lower() == new_value.lower():
            return await self._confirm_fact('user_company_context', existing_context['id'], fact_data.get('confidence_score', 0.8))

        # Different value → Check source authority
        existing_source = existing_context.get('source_authority', 'UNKNOWN')
        new_source = fact_data.get('source_authority', 'UNKNOWN')

        existing_weight = self.authority_weights.get(existing_source, 0.3)
        new_weight = self.authority_weights.get(new_source, 0.3)

        if new_weight > existing_weight:
            # New source is more authoritative → UPDATE
            return await self._deprecate_and_insert(
                'user_company_context',
                existing_context['id'],
                fact_data,
                reason=f"Higher authority source ({new_source} > {existing_source})"
            )
        elif new_weight == existing_weight:
            # Equal authority → CONFLICT
            return await self._flag_conflict(
                'user_company_context',
                existing_context,
                fact_data,
                conflict_type='VALUE_MISMATCH'
            )
        else:
            # Existing source is more authoritative → SKIP
            return {
                'action': 'SKIPPED',
                'fact_id': existing_context['id'],
                'message': f'Existing source ({existing_source}) is more authoritative than new source ({new_source})'
            }

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _is_semantic_duplicate(self, existing: Dict, new: Dict) -> bool:
        """Check if two facts are semantically identical."""

        # For business facts: same subject, predicate, and value
        if 'subject' in existing and 'subject' in new:
            return (
                existing.get('subject', '').lower().strip() == new.get('subject', '').lower().strip() and
                existing.get('predicate', '').lower().strip() == new.get('predicate', '').lower().strip() and
                existing.get('value', '').lower().strip() == new.get('value', '').lower().strip()
            )

        # For risks: same title
        if 'title' in existing and 'title' in new:
            return existing.get('title', '').lower().strip() == new.get('title', '').lower().strip()

        return False

    def _values_are_compatible(self, val1: str, val2: str) -> bool:
        """
        Check if two values are compatible (not contradictory).

        Examples:
        - "$3.2M" vs "$3200000" → Compatible (same value, different format)
        - "$3.2M" vs "$4.5M" → Incompatible (different values)
        - "B2B SaaS" vs "SaaS" → Compatible (subset relationship)
        """

        v1 = val1.lower().strip()
        v2 = val2.lower().strip()

        # Exact match
        if v1 == v2:
            return True

        # One is substring of the other (e.g., "SaaS" in "B2B SaaS")
        if v1 in v2 or v2 in v1:
            return True

        # Numerical comparison (if both are numbers)
        try:
            # Strip common units
            n1 = self._extract_number(v1)
            n2 = self._extract_number(v2)

            if n1 is not None and n2 is not None:
                # Allow 5% tolerance for rounding errors
                return abs(n1 - n2) / max(n1, n2) < 0.05

        except Exception:
            pass

        # Otherwise, assume incompatible
        return False

    def _extract_number(self, value: str) -> Optional[float]:
        """Extract numerical value from string (e.g., '$3.2M' → 3200000)."""

        import re

        # Remove currency symbols and spaces
        cleaned = re.sub(r'[$£€,\s]', '', value)

        # Handle K/M/B suffixes
        multiplier = 1
        if 'k' in cleaned.lower():
            multiplier = 1_000
            cleaned = cleaned.lower().replace('k', '')
        elif 'm' in cleaned.lower():
            multiplier = 1_000_000
            cleaned = cleaned.lower().replace('m', '')
        elif 'b' in cleaned.lower():
            multiplier = 1_000_000_000
            cleaned = cleaned.lower().replace('b', '')

        # Extract the number
        match = re.search(r'([0-9]+\.?[0-9]*)', cleaned)
        if match:
            return float(match.group(1)) * multiplier

        return None

    def _is_temporal_progression(self, existing: Dict, new: Dict) -> bool:
        """
        Check if new fact is a temporal update of existing fact.

        E.g., Q3 2023 data being replaced by Q3 2024 data.
        """

        existing_time = existing.get('valid_from')
        new_time = new.get('valid_from')

        if existing_time and new_time:
            try:
                existing_dt = datetime.fromisoformat(existing_time.replace('Z', '+00:00'))
                new_dt = datetime.fromisoformat(new_time.replace('Z', '+00:00'))

                # New fact is from a later time period → likely an update
                return new_dt > existing_dt

            except Exception:
                pass

        return False

    async def _insert_fact(self, table: str, fact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new fact."""

        try:
            # Ensure user_id is set
            fact_data['user_id'] = self.user_id

            # Set defaults
            if 'valid_from' not in fact_data or not fact_data['valid_from']:
                fact_data['valid_from'] = datetime.now(timezone.utc).isoformat()

            if 'verification_status' not in fact_data:
                confidence = fact_data.get('confidence_score', 0.7)
                fact_data['verification_status'] = 'VERIFIED' if confidence >= 0.9 else 'PROVISIONAL'

            result = self.supabase.table(table).insert(fact_data).execute()

            if result.data:
                logger.info(f"✓ INSERTED new fact in {table}: {result.data[0]['id']}")
                return {
                    'action': 'INSERTED',
                    'fact_id': result.data[0]['id'],
                    'message': 'New fact stored successfully'
                }

        except Exception as e:
            logger.error(f"Error inserting fact: {e}")

        return {
            'action': 'SKIPPED',
            'fact_id': None,
            'message': f'Failed to insert: {str(e)[:100]}'
        }

    async def _confirm_fact(self, table: str, fact_id: str, new_confidence: float) -> Dict[str, Any]:
        """Confirm an existing fact (boost confidence)."""

        try:
            # Get current confidence
            current = self.supabase.table(table).select('confidence_score').eq('id', fact_id).execute()

            if current.data:
                old_confidence = current.data[0].get('confidence_score', 0.7)

                # Boost confidence (weighted average)
                boosted_confidence = min(1.0, (old_confidence * 0.7 + new_confidence * 0.3))

                # Update
                self.supabase.table(table).update({
                    'confidence_score': boosted_confidence,
                    'last_verified_at': datetime.now(timezone.utc).isoformat(),
                    'verification_status': 'VERIFIED' if boosted_confidence >= 0.9 else 'PROVISIONAL'
                }).eq('id', fact_id).execute()

                logger.info(f"✓ CONFIRMED fact {fact_id}: confidence {old_confidence:.2f} → {boosted_confidence:.2f}")

                return {
                    'action': 'CONFIRMED',
                    'fact_id': fact_id,
                    'message': f'Fact confidence boosted to {boosted_confidence:.2f}'
                }

        except Exception as e:
            logger.error(f"Error confirming fact: {e}")

        return {
            'action': 'SKIPPED',
            'fact_id': fact_id,
            'message': 'Failed to confirm'
        }

    async def _deprecate_and_insert(
        self,
        table: str,
        old_fact_id: str,
        new_fact_data: Dict[str, Any],
        reason: str
    ) -> Dict[str, Any]:
        """Deprecate old fact and insert new one (graceful update)."""

        try:
            # Mark old fact as deprecated
            self.supabase.table(table).update({
                'valid_to': datetime.now(timezone.utc).isoformat(),
                'verification_status': 'DEPRECATED'
            }).eq('id', old_fact_id).execute()

            # Insert new fact
            result = await self._insert_fact(table, new_fact_data)

            logger.info(f"✓ UPDATED fact {old_fact_id} → {result.get('fact_id')}: {reason}")

            return {
                'action': 'UPDATED',
                'fact_id': result.get('fact_id'),
                'old_fact_id': old_fact_id,
                'message': reason
            }

        except Exception as e:
            logger.error(f"Error deprecating fact: {e}")
            return {
                'action': 'SKIPPED',
                'fact_id': None,
                'message': f'Failed to update: {str(e)[:100]}'
            }

    async def _flag_conflict(
        self,
        table: str,
        existing_fact: Dict,
        new_fact: Dict,
        conflict_type: str
    ) -> Dict[str, Any]:
        """Flag an irresolvable conflict for user review."""

        try:
            # Insert into fact_conflicts table
            conflict_record = {
                'user_id': self.user_id,
                'fact_table': table,
                'fact_id': existing_fact['id'],
                'conflict_type': conflict_type,
                'conflicting_fact_id': None,  # New fact not yet inserted
                'resolution_status': 'PENDING',
                'details': {
                    'existing_value': existing_fact.get('value') or existing_fact.get('title'),
                    'new_value': new_fact.get('value') or new_fact.get('title'),
                    'existing_source': existing_fact.get('source_authority', 'UNKNOWN'),
                    'new_source': new_fact.get('source_authority', 'UNKNOWN')
                }
            }

            result = self.supabase.table('fact_conflicts').insert(conflict_record).execute()

            # Mark existing fact as CONTESTED
            self.supabase.table(table).update({
                'verification_status': 'CONTESTED'
            }).eq('id', existing_fact['id']).execute()

            logger.warning(f"⚠️  CONFLICT detected in {table}: {existing_fact['id']}")

            return {
                'action': 'CONTESTED',
                'fact_id': existing_fact['id'],
                'conflict_id': result.data[0]['id'] if result.data else None,
                'message': f"Conflict detected: {conflict_record['details']}"
            }

        except Exception as e:
            logger.error(f"Error flagging conflict: {e}")
            return {
                'action': 'SKIPPED',
                'fact_id': None,
                'message': f'Failed to flag conflict: {str(e)[:100]}'
            }

"""
Kogna Memory Manager V1.5 - Enhanced with Truth Maintenance
=============================================================

Upgrades from V1.0:
- Integrates TruthMaintenanceSystem for conflict detection
- Uses EnhancedFactExtractor with self-reflection
- Tracks source authority and confidence scores
- Hybrid search (Vector + Metadata filtering)

Usage (identical API to v1.0):
    from services.memory_manager_v15 import get_user_memory

    memory = get_user_memory(user_id="user_123")
    context = await memory.get_context(query="What are our risks?", session_id="session_1")
"""

import os
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone

# Import dual memory system (unchanged)
from services.dual_memory.memory_system import (
    UserMemorySystem,
    EmbeddingProvider,
    FactType,
    RiskSeverity,
)

# Import ENHANCED fact extraction (v1.5)
from services.dual_memory.fact_extraction_v15 import EnhancedFactExtractor

# Import Truth Maintenance System (NEW)
from services.dual_memory.truth_maintenance import TruthMaintenanceSystem

# Import Kogna's existing services
from supabase_connect import get_supabase_manager

# Use Google GenAI SDK directly for better control over Matryoshka dimensions
try:
    from google import genai
    from google.genai import types
    USE_GENAI_SDK = True
except ImportError:
    # Fallback to LangChain wrapper if google-genai not available
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    USE_GENAI_SDK = False

logger = logging.getLogger(__name__)


# ============================================================
# GEMINI EMBEDDING ADAPTER (V1.5 - Matryoshka Support)
# ============================================================

class GeminiEmbeddingProvider(EmbeddingProvider):
    """
    Adapter for Google Gemini embeddings with Matryoshka dimensionality control.

    Gemini embedding-001 uses Matryoshka Representation Learning:
    - Default: 3072 dimensions
    - Configurable: 768, 1536, or 3072
    - We use 1536 for optimal quality/storage balance
    """

    def __init__(self, output_dimensionality: int = 1536):
        """
        Initialize Gemini embedding provider.

        Args:
            output_dimensionality: Output embedding size (768, 1536, or 3072)
                                   Default: 1536 (recommended)
        """
        self.output_dimensionality = output_dimensionality

        if USE_GENAI_SDK:
            # Use official Google GenAI SDK (supports output_dimensionality)
            self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
            self.model_name = "gemini-embedding-001"
            logger.info(f"✓ Using Google GenAI SDK with {output_dimensionality} dims")
        else:
            # Fallback to LangChain (might not support dimensionality control)
            self.model = GoogleGenerativeAIEmbeddings(
                model="models/gemini-embedding-001",
                google_api_key=os.getenv("GOOGLE_API_KEY")
            )
            logger.warning(f"⚠️  Using LangChain wrapper (may return 3072 dims regardless of config)")

    async def embed(self, text: str) -> List[float]:
        """Generate embedding for single text"""
        try:
            if USE_GENAI_SDK:
                # Use Google GenAI SDK with explicit dimensionality
                import asyncio
                loop = asyncio.get_event_loop()

                def _embed():
                    result = self.client.models.embed_content(
                        model=self.model_name,
                        contents=text,
                        config=types.EmbedContentConfig(
                            output_dimensionality=self.output_dimensionality
                        )
                    )
                    return result.embeddings[0].values

                embedding = await loop.run_in_executor(None, _embed)
                return list(embedding)
            else:
                # Fallback to LangChain
                import asyncio
                loop = asyncio.get_event_loop()
                embedding = await loop.run_in_executor(None, self.model.embed_query, text)
                return embedding
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            return [0.0] * self.output_dimensionality

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for batch of texts"""
        try:
            if USE_GENAI_SDK:
                # Use Google GenAI SDK with explicit dimensionality
                import asyncio
                loop = asyncio.get_event_loop()

                def _embed_batch():
                    results = []
                    for text in texts:
                        result = self.client.models.embed_content(
                            model=self.model_name,
                            contents=text,
                            config=types.EmbedContentConfig(
                                output_dimensionality=self.output_dimensionality
                            )
                        )
                        results.append(list(result.embeddings[0].values))
                    return results

                embeddings = await loop.run_in_executor(None, _embed_batch)
                return embeddings
            else:
                # Fallback to LangChain
                import asyncio
                loop = asyncio.get_event_loop()
                embeddings = await loop.run_in_executor(None, self.model.embed_documents, texts)
                return embeddings
        except Exception as e:
            logger.error(f"Batch embedding error: {e}")
            return [[0.0] * self.output_dimensionality for _ in texts]


# ============================================================
# ENHANCED SUPABASE STORAGE (V1.5 with TMS Integration)
# ============================================================

class EnhancedSupabaseMemoryStorage:
    """
    Enhanced Supabase storage with Truth Maintenance.

    NEW in V1.5:
    - All save operations go through TruthMaintenanceSystem
    - Search operations use hybrid filtering (vector + metadata)
    - Tracks verification status and source authority
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.supabase = get_supabase_manager().client

        # Initialize Truth Maintenance System
        self.tms = TruthMaintenanceSystem(self.supabase, user_id)

    # ================================================================
    # CONVERSATIONAL MEMORY (unchanged from v1.0)
    # ================================================================

    async def save_conversation(self, entry: Dict) -> str:
        """Save conversation entry"""
        try:
            result = self.supabase.table("user_conversational_memory").insert({
                "user_id": self.user_id,
                "session_id": entry["session_id"],
                "query": entry["query"],
                "response_summary": entry["response_summary"],
                "entities": entry.get("entities", []),
                "embedding": entry.get("embedding"),
                "was_helpful": entry.get("was_helpful"),
                "source_authority": "CHAT",  # NEW: Track source
                "created_at": entry.get("created_at", datetime.now(timezone.utc).isoformat())
            }).execute()

            return result.data[0]["id"] if result.data else None

        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
            return None

    async def search_conversations(
        self,
        query_embedding: List[float],
        limit: int = 5,
        session_id: Optional[str] = None
    ) -> List[Dict]:
        """Search conversation history using vector similarity"""
        try:
            result = self.supabase.rpc('match_user_conversations', {
                'query_embedding': query_embedding,
                'match_count': limit,
                'p_user_id': self.user_id,
                'p_session_id': session_id
            }).execute()

            return result.data or []

        except Exception as e:
            logger.error(f"Error searching conversations: {e}")
            return []

    # ================================================================
    # BUSINESS FACTS (ENHANCED with TMS)
    # ================================================================

    async def save_fact(self, fact: Dict) -> Dict[str, Any]:
        """
        Save business fact with Truth Maintenance.

        NEW in V1.5:
        - Goes through TMS verification
        - Returns action taken (INSERTED, CONFIRMED, CONTESTED, etc.)
        """
        try:
            # Prepare fact data with v1.5 metadata
            fact_data = {
                "user_id": self.user_id,
                "fact_type": fact.get("fact_type", "unknown"),
                "subject": fact.get("subject"),
                "predicate": fact.get("predicate"),
                "value": fact.get("value"),
                "confidence_score": fact.get("confidence", 0.7),  # NEW
                "source_authority": fact.get("source_authority", "CHAT"),  # NEW
                "source_text": fact.get("source_text"),
                "source_conversation_id": fact.get("source_conversation_id"),
                "embedding": fact.get("embedding"),
                "valid_from": fact.get("valid_from", datetime.now(timezone.utc).isoformat()),
                "valid_to": fact.get("valid_to"),
            }

            # Go through Truth Maintenance System
            result = await self.tms.verify_and_store_fact('business_fact', fact_data)

            return result

        except Exception as e:
            logger.error(f"Error saving fact: {e}")
            return {
                'action': 'SKIPPED',
                'fact_id': None,
                'message': str(e)
            }

    async def search_facts(
        self,
        query_embedding: List[float],
        limit: int = 10,
        fact_types: Optional[List[str]] = None,
        min_confidence: float = 0.0  # NEW: Filter by confidence
    ) -> List[Dict]:
        """
        Search business facts using HYBRID search (Vector + Metadata).

        NEW in V1.5:
        - Filters out DEPRECATED and CONTESTED facts
        - Filters by min_confidence threshold
        - Only returns currently valid facts (valid_to IS NULL)
        """
        try:
            # Custom RPC that combines vector search with metadata filtering
            result = self.supabase.rpc('match_user_facts_v15', {
                'query_embedding': query_embedding,
                'match_count': limit,
                'p_user_id': self.user_id,
                'p_fact_types': fact_types,
                'p_min_confidence': min_confidence
            }).execute()

            return result.data or []

        except Exception as e:
            # Fallback to old RPC if v15 function doesn't exist yet
            logger.warning(f"V1.5 RPC not found, falling back to v1.0: {e}")

            try:
                result = self.supabase.rpc('match_user_facts', {
                    'query_embedding': query_embedding,
                    'match_count': limit,
                    'p_user_id': self.user_id,
                    'p_fact_types': fact_types
                }).execute()

                # Post-filter by confidence
                facts = result.data or []
                return [f for f in facts if f.get('confidence_score', 1.0) >= min_confidence]

            except Exception as e2:
                logger.error(f"Error searching facts: {e2}")
                return []

    # ================================================================
    # RISKS (ENHANCED with TMS)
    # ================================================================

    async def save_risk(self, risk: Dict) -> Dict[str, Any]:
        """Save risk with Truth Maintenance."""
        try:
            risk_data = {
                "user_id": self.user_id,
                "title": risk.get("title"),
                "description": risk.get("description"),
                "severity": risk.get("severity", "MEDIUM"),
                "category": risk.get("category"),
                "impact": risk.get("impact"),
                "mitigation": risk.get("mitigation"),
                "owner": risk.get("owner"),
                "confidence_score": risk.get("confidence", 0.7),  # NEW
                "source_authority": risk.get("source_authority", "CHAT"),  # NEW
                "embedding": risk.get("embedding"),
                "source_conversation_id": risk.get("source_conversation_id"),
                "identified_at": datetime.now(timezone.utc).isoformat(),
                "valid_from": datetime.now(timezone.utc).isoformat(),
            }

            # Go through TMS
            result = await self.tms.verify_and_store_fact('risk', risk_data)

            return result

        except Exception as e:
            logger.error(f"Error saving risk: {e}")
            return {
                'action': 'SKIPPED',
                'fact_id': None,
                'message': str(e)
            }

    async def get_active_risks(self, category: Optional[str] = None) -> List[Dict]:
        """
        Get active (non-deprecated) risks.

        NEW in V1.5:
        - Filters out DEPRECATED and CONTESTED risks
        - Returns only currently valid risks
        """
        try:
            query = self.supabase.table("user_risks").select("*").eq(
                "user_id", self.user_id
            ).is_("valid_to", None).not_.in_(
                "verification_status", ["DEPRECATED", "CONTESTED"]  # NEW: Filter contested
            )

            if category:
                query = query.eq("category", category)

            result = query.order("identified_at", desc=True).execute()

            return result.data or []

        except Exception as e:
            logger.error(f"Error fetching active risks: {e}")
            return []

    # ================================================================
    # COMPANY CONTEXT (ENHANCED with TMS)
    # ================================================================

    async def save_company_context(
        self,
        key: str,
        value: str,
        source_conversation_id: Optional[str] = None,
        source_authority: str = "CHAT",  # NEW parameter
        confidence: float = 0.8  # NEW parameter
    ) -> Dict[str, Any]:
        """Save company context with Truth Maintenance."""
        try:
            context_data = {
                "user_id": self.user_id,
                "key": key,
                "value": value,
                "confidence_score": confidence,  # NEW
                "source_authority": source_authority,  # NEW
                "source_conversation_id": source_conversation_id,
                "valid_from": datetime.now(timezone.utc).isoformat(),
            }

            # Go through TMS
            result = await self.tms.verify_and_store_fact('company_context', context_data)

            return result

        except Exception as e:
            logger.error(f"Error saving company context: {e}")
            return {
                'action': 'SKIPPED',
                'fact_id': None,
                'message': str(e)
            }

    async def get_company_context(self) -> Dict:
        """
        Get all active company context.

        NEW in V1.5:
        - Filters out DEPRECATED entries
        """
        try:
            result = self.supabase.table("user_company_context").select("*").eq(
                "user_id", self.user_id
            ).not_.eq(
                "verification_status", "DEPRECATED"  # NEW: Exclude deprecated
            ).execute()

            # Convert to dict
            context = {}
            for row in result.data or []:
                context[row["key"]] = row["value"]

            return context

        except Exception as e:
            logger.error(f"Error fetching company context: {e}")
            return {}

    # ================================================================
    # CONFLICT MANAGEMENT (NEW in V1.5)
    # ================================================================

    async def get_pending_conflicts(self) -> List[Dict]:
        """Get all pending conflicts for user review."""
        try:
            result = self.supabase.table("fact_conflicts").select("*").eq(
                "user_id", self.user_id
            ).eq(
                "resolution_status", "PENDING"
            ).order("detected_at", desc=True).execute()

            return result.data or []

        except Exception as e:
            logger.error(f"Error fetching conflicts: {e}")
            return []

    async def resolve_conflict(
        self,
        conflict_id: str,
        resolution_method: str,
        chosen_fact_id: Optional[str] = None
    ) -> bool:
        """Resolve a conflict (typically after user input)."""
        try:
            self.supabase.table("fact_conflicts").update({
                "resolution_status": "USER_RESOLVED",
                "resolution_method": resolution_method,
                "resolved_at": datetime.now(timezone.utc).isoformat(),
                "resolved_by": "USER"
            }).eq("id", conflict_id).execute()

            logger.info(f"✓ Conflict {conflict_id} resolved via {resolution_method}")

            return True

        except Exception as e:
            logger.error(f"Error resolving conflict: {e}")
            return False


# ============================================================
# KOGNA MEMORY MANAGER V1.5 (Main Class)
# ============================================================

class KognaMemoryManagerV15:
    """
    Enhanced Memory Manager for Kogna 1.5.

    NEW Features:
    - Truth Maintenance (conflict detection, deduplication)
    - Self-Reflective Extraction (reduces hallucinations)
    - Source tracking and confidence scoring
    - Hybrid search (vector + metadata)
    """

    def __init__(self, user_id: str, use_llm_extraction: bool = True):
        self.user_id = user_id

        # Initialize embedding provider (unchanged)
        self.embedding_provider = GeminiEmbeddingProvider()

        # Initialize dual memory system (unchanged)
        self.memory = UserMemorySystem(
            user_id=user_id,
            embedding_provider=self.embedding_provider
        )

        # Initialize ENHANCED Supabase storage (with TMS)
        self.storage = EnhancedSupabaseMemoryStorage(user_id)

        # Initialize ENHANCED fact extractor (with self-reflection)
        self.fact_extractor = EnhancedFactExtractor(
            llm_client=None,  # Will use default (gpt-4o-mini if available)
            use_llm=use_llm_extraction
        )

        logger.info(f"✓ KognaMemoryManagerV15 initialized for user {user_id}")

    async def get_context(
        self,
        query: str,
        session_id: Optional[str] = None,
        min_confidence: float = 0.5  # NEW: Filter low-confidence facts
    ) -> Dict:
        """
        Get relevant context for a query.

        NEW in V1.5:
        - Filters facts by min_confidence threshold
        - Excludes contested/deprecated facts automatically
        """

        # Get context from in-memory system (unchanged)
        context = await self.memory.get_context(query=query, session_id=session_id)

        # Enhance with Supabase data
        query_embedding = await self.embedding_provider.embed(query)

        # Get conversations (unchanged)
        context["relevant_conversations"] = await self.storage.search_conversations(
            query_embedding=query_embedding,
            limit=5,
            session_id=None  # Search across all sessions
        )

        # Get facts with NEW confidence filtering
        context["business_facts"] = await self.storage.search_facts(
            query_embedding=query_embedding,
            limit=10,
            min_confidence=min_confidence  # NEW: Filter low-confidence
        )

        # Get active risks (already filtered in v1.5)
        context["active_risks"] = await self.storage.get_active_risks()

        # Get company context (already filtered in v1.5)
        context["company_context"] = await self.storage.get_company_context()

        # NEW: Check for pending conflicts (warn user)
        pending_conflicts = await self.storage.get_pending_conflicts()
        if pending_conflicts:
            context["pending_conflicts"] = pending_conflicts
            logger.warning(f"⚠️  User has {len(pending_conflicts)} pending memory conflicts")

        return context

    async def process_interaction(
        self,
        query: str,
        response: str,
        session_id: str,
        source_type: str = "CHAT",  # NEW: Track where this came from
        auto_extract: bool = True
    ) -> Dict[str, Any]:
        """
        Process an interaction with ENHANCED extraction and TMS.

        NEW in V1.5:
        - Uses self-reflective extraction (2-pass)
        - All facts verified through TMS before storage
        - Returns detailed storage report (what was inserted/confirmed/contested)
        """

        # Store conversation in dual memory (unchanged)
        conversation_id = await self.memory.process_interaction(
            query=query,
            response=response,
            session_id=session_id
        )

        # Generate embedding (unchanged)
        query_embedding = await self.embedding_provider.embed(query)

        # Store in Supabase conversational memory
        await self.storage.save_conversation({
            "session_id": session_id,
            "query": query,
            "response_summary": response[:500],  # Truncate for storage
            "embedding": query_embedding,
            "entities": [],  # Could extract entities here
        })

        storage_report = {
            'conversation_id': conversation_id,
            'facts_stored': 0,
            'facts_confirmed': 0,
            'facts_contested': 0,
            'risks_stored': 0,
            'company_info_stored': 0,
            'conflicts_detected': []
        }

        # Auto-extract facts if enabled
        if auto_extract:
            try:
                # ENHANCED extraction with self-reflection
                extracted_facts = await self.fact_extractor.extract_facts_with_metadata(
                    query=query,
                    response=response,
                    source_type=source_type,
                    session_id=session_id
                )

                # Store each fact through TMS
                for fact_data in extracted_facts.get('company_info', []):
                    result = await self.storage.save_company_context(
                        key=fact_data['key'],
                        value=fact_data['value'],
                        source_conversation_id=conversation_id,
                        source_authority=fact_data.get('source_authority', source_type),
                        confidence=fact_data.get('confidence', 0.8)
                    )

                    # Track results
                    if result['action'] == 'INSERTED':
                        storage_report['company_info_stored'] += 1
                    elif result['action'] == 'CONFIRMED':
                        storage_report['facts_confirmed'] += 1
                    elif result['action'] == 'CONTESTED':
                        storage_report['facts_contested'] += 1
                        storage_report['conflicts_detected'].append(result.get('conflict_id'))

                # Similar for metrics, risks, etc.
                # (Implementation continues...)

                logger.info(f"✓ Fact extraction complete: {storage_report}")

            except Exception as e:
                logger.error(f"Fact extraction failed: {e}")

        return storage_report

    async def get_summary(self) -> Dict:
        """Get memory summary (unchanged from v1.0)."""
        return await self.memory.get_summary()


# ============================================================
# CONVENIENCE FUNCTION
# ============================================================

def get_user_memory(user_id: str, use_llm_extraction: bool = True) -> KognaMemoryManagerV15:
    """
    Get or create memory manager for a user (V1.5 Enhanced).

    Args:
        user_id: User ID
        use_llm_extraction: Whether to use LLM for fact extraction

    Returns:
        KognaMemoryManagerV15 instance
    """
    return KognaMemoryManagerV15(user_id, use_llm_extraction)

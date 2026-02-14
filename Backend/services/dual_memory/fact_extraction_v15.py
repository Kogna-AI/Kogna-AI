"""
Enhanced Fact Extraction for Kogna 1.5
=======================================

Upgrades from Kogna 1.0:
- Self-Reflective Extraction (critique loop to reduce hallucinations)
- Source authority tracking
- Confidence scoring
- Temporal validity extraction

Key Features:
- Extract facts WITH epistemic metadata
- Two-pass extraction: Extract → Critique → Filter
- Assigns source_authority based on context
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class EnhancedFactExtractor:
    """
    Kogna 1.5 Fact Extractor with Self-Reflection and Epistemic Metadata.

    Improvements over v1.0:
    - Extracts confidence scores alongside facts
    - Performs self-critique to filter low-quality extractions
    - Tracks source authority (where did this fact come from?)
    - Supports temporal validity (valid_from, valid_to)
    """

    def __init__(self, llm_client=None, use_llm: bool = True):
        """
        Initialize enhanced fact extractor.

        Args:
            llm_client: Optional LLM client for extraction (e.g., OpenAI)
            use_llm: Whether to use LLM-based extraction (vs rule-based)
        """
        self.llm_client = llm_client
        self.use_llm = use_llm

    async def extract_facts_with_metadata(
        self,
        query: str,
        response: str,
        source_type: str = "CHAT",
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract facts with epistemic metadata using self-reflective extraction.

        This is the main entry point for Kogna 1.5 fact extraction.

        Args:
            query: User's query
            response: Agent's response
            source_type: Where this came from ('CHAT', 'PDF', 'ERP', 'USER_UPLOAD', 'API')
            session_id: Session identifier

        Returns:
            {
                'company_info': [
                    {
                        'key': 'industry',
                        'value': 'B2B SaaS',
                        'confidence': 0.95,
                        'source_authority': 'CHAT',
                        'verified': True,
                        'extracted_from': 'query'
                    }
                ],
                'metrics': [...],
                'risks': [...],
                'temporal_events': [...],
                'relationships': [...]
            }
        """

        if not self.use_llm or not self.llm_client:
            # Fallback to rule-based extraction
            return await self._rule_based_extraction(query, response, source_type)

        # Two-pass extraction: Extract → Critique
        extracted_facts = await self._llm_extraction_pass(query, response, source_type)

        # Self-critique pass (filter low-quality facts)
        verified_facts = await self._self_critique_pass(extracted_facts, query, response)

        return verified_facts

    async def _llm_extraction_pass(
        self,
        query: str,
        response: str,
        source_type: str
    ) -> Dict[str, Any]:
        """
        First pass: Extract facts using LLM with enhanced prompt.

        This prompt explicitly asks the LLM to:
        1. Extract facts
        2. Assign confidence scores
        3. Mark explicit vs inferred facts
        """

        extraction_prompt = f"""You are a precise fact extraction system for a Business Intelligence agent.

Your task: Extract structured business facts from the conversation below.

For EACH fact you extract, you MUST:
1. Assign a confidence score (0.0 to 1.0)
   - 1.0 = Explicitly stated with numbers ("Revenue is $3.2M")
   - 0.8 = Explicitly stated, qualitative ("We are in the SaaS industry")
   - 0.6 = Strongly implied ("Our cloud product" → industry: Cloud/SaaS)
   - 0.4 = Weakly implied (uncertain inference)
   - DO NOT extract facts with confidence < 0.4

2. Mark if the fact is EXPLICIT or INFERRED
   - EXPLICIT: Directly stated in the text
   - INFERRED: You had to make an assumption

3. Extract temporal validity if mentioned
   - If a time period is mentioned (Q3, 2024, etc.), capture it
   - If no time period, set valid_from = NOW

**Conversation:**
User: {query}
Assistant: {response}

**Extract the following categories:**

1. **Company Information** (industry, location, size, business model, etc.)
2. **Metrics** (revenue, growth rate, KPIs with specific values)
3. **Risks** (identified problems, threats, challenges)
4. **Temporal Events** (things that happened at a specific time)
5. **Relationships** (causal links like "X caused Y")

**Output Format (strict JSON):**
{{
  "company_info": [
    {{
      "key": "industry",
      "value": "B2B SaaS",
      "confidence": 0.95,
      "explicit": true,
      "extracted_from": "query"  // or "response"
    }}
  ],
  "metrics": [
    {{
      "name": "Revenue",
      "value": "$3.2M",
      "unit": "USD",
      "time_period": "Q3 2024",
      "change": "-15%",
      "confidence": 1.0,
      "explicit": true,
      "extracted_from": "query"
    }}
  ],
  "risks": [
    {{
      "title": "Tariff Impact on APAC",
      "description": "Tariffs affecting APAC market",
      "severity": "HIGH",
      "category": "External/Regulatory",
      "confidence": 0.9,
      "explicit": true,
      "extracted_from": "query"
    }}
  ],
  "temporal_events": [
    {{
      "event": "Revenue dropped 15%",
      "timestamp": "Q3 2024",
      "entities": ["Revenue", "Q3"],
      "confidence": 1.0,
      "explicit": true
    }}
  ],
  "relationships": [
    {{
      "subject": "Tariffs",
      "predicate": "caused",
      "object": "Revenue Drop",
      "confidence": 0.7,
      "explicit": false,  // This is inferred
      "extracted_from": "query"
    }}
  ]
}}

**Critical Instructions:**
- Only extract facts that are actually present or strongly implied
- If confidence < 0.4, do NOT include the fact
- Be conservative: When in doubt, mark as INFERRED and lower the confidence
- If a metric has NO numerical value, do NOT extract it

Return ONLY the JSON, no other text.
"""

        try:
            # Call LLM
            if hasattr(self.llm_client, 'chat') and hasattr(self.llm_client.chat, 'completions'):
                # OpenAI-style client
                response = self.llm_client.chat.completions.create(
                    model="gpt-4o-mini",  # Fast, cheap model for extraction
                    messages=[
                        {"role": "system", "content": "You are a precise fact extraction system. Return only valid JSON."},
                        {"role": "user", "content": extraction_prompt}
                    ],
                    temperature=0.1,  # Low temperature for consistent extraction
                    response_format={"type": "json_object"}  # Force JSON output
                )

                extracted_json = response.choices[0].message.content
            else:
                # Generic LLM client
                extracted_json = await self.llm_client.generate(extraction_prompt)

            # Parse JSON
            extracted_facts = json.loads(extracted_json)

            # Add source_authority metadata to all facts
            for category in ['company_info', 'metrics', 'risks', 'temporal_events', 'relationships']:
                if category in extracted_facts:
                    for fact in extracted_facts[category]:
                        fact['source_authority'] = source_type
                        # Default verification status based on confidence
                        if fact.get('confidence', 0) >= 0.9 and fact.get('explicit', False):
                            fact['verification_status'] = 'VERIFIED'
                        else:
                            fact['verification_status'] = 'PROVISIONAL'

            return extracted_facts

        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            # Fallback to empty extraction
            return {
                'company_info': [],
                'metrics': [],
                'risks': [],
                'temporal_events': [],
                'relationships': []
            }

    async def _self_critique_pass(
        self,
        extracted_facts: Dict[str, Any],
        original_query: str,
        original_response: str
    ) -> Dict[str, Any]:
        """
        Second pass: Self-critique to filter hallucinations.

        This pass asks the LLM: "Are these facts ACTUALLY in the text?"
        Filters out low-quality extractions.
        """

        if not self.use_llm or not self.llm_client:
            # Skip critique if no LLM
            return extracted_facts

        critique_prompt = f"""You are a fact verification system.

**Original Conversation:**
User: {original_query}
Assistant: {original_response}

**Extracted Facts (claimed by another system):**
{json.dumps(extracted_facts, indent=2)}

**Your Task:**
Review EACH extracted fact and verify:
1. Is this fact ACTUALLY stated or strongly implied in the original conversation?
2. Is the confidence score reasonable?
3. Are there any hallucinated details (e.g., made-up numbers)?

**Output Format:**
For each fact, return:
- keep: true/false (should we keep this fact?)
- reason: brief explanation if rejecting

Return a JSON object with the same structure, but add "keep" and "critique_reason" to each fact.

{{
  "company_info": [
    {{
      ...original fact fields...,
      "keep": true,
      "critique_reason": "Explicitly stated in query"
    }}
  ],
  ...
}}

Be STRICT. If you're not 80% sure the fact is real, mark keep=false.
"""

        try:
            if hasattr(self.llm_client, 'chat') and hasattr(self.llm_client.chat, 'completions'):
                response = self.llm_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a strict fact verification system."},
                        {"role": "user", "content": critique_prompt}
                    ],
                    temperature=0,
                    response_format={"type": "json_object"}
                )

                critiqued_json = response.choices[0].message.content
            else:
                critiqued_json = await self.llm_client.generate(critique_prompt)

            critiqued_facts = json.loads(critiqued_json)

            # Filter: keep only facts where keep=true
            verified_facts = {
                'company_info': [],
                'metrics': [],
                'risks': [],
                'temporal_events': [],
                'relationships': []
            }

            for category in verified_facts.keys():
                if category in critiqued_facts:
                    verified_facts[category] = [
                        fact for fact in critiqued_facts[category]
                        if fact.get('keep', False)
                    ]

            # Log rejected facts
            total_extracted = sum(len(extracted_facts.get(cat, [])) for cat in verified_facts.keys())
            total_kept = sum(len(verified_facts[cat]) for cat in verified_facts.keys())
            logger.info(f"Self-Critique: Kept {total_kept}/{total_extracted} facts ({(total_kept/max(total_extracted,1))*100:.0f}% pass rate)")

            return verified_facts

        except Exception as e:
            logger.error(f"Self-critique failed: {e}")
            # If critique fails, keep original extraction (degraded mode)
            return extracted_facts

    async def _rule_based_extraction(
        self,
        query: str,
        response: str,
        source_type: str
    ) -> Dict[str, Any]:
        """
        Fallback: Simple rule-based extraction using regex.

        This is a degraded mode if LLM is unavailable.
        Uses keyword matching and regex patterns.
        """

        import re

        extracted = {
            'company_info': [],
            'metrics': [],
            'risks': [],
            'temporal_events': [],
            'relationships': []
        }

        combined_text = f"{query} {response}".lower()

        # Pattern: Company type mentions
        company_patterns = [
            (r'\b(b2b|b2c|saas|paas|iaas|e-commerce|fintech|healthtech)\b', 'industry'),
            (r'\b(sf|san francisco|ny|new york|london|singapore)\b', 'location'),
        ]

        for pattern, key_type in company_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            for match in matches:
                extracted['company_info'].append({
                    'key': key_type,
                    'value': match,
                    'confidence': 0.6,
                    'source_authority': source_type,
                    'verification_status': 'PROVISIONAL',
                    'explicit': True,
                    'extracted_from': 'query' if match.lower() in query.lower() else 'response'
                })

        # Pattern: Dollar amounts (metrics)
        money_pattern = r'\$([0-9]+\.?[0-9]*)\s*(m|million|k|thousand|b|billion)?'
        money_matches = re.findall(money_pattern, combined_text, re.IGNORECASE)

        for amount, unit in money_matches:
            extracted['metrics'].append({
                'name': 'Revenue',  # Assumption
                'value': f"${amount}{unit.upper() if unit else ''}",
                'unit': 'USD',
                'confidence': 0.5,  # Low confidence (could be any dollar amount)
                'source_authority': source_type,
                'verification_status': 'PROVISIONAL',
                'explicit': True,
                'extracted_from': 'query' if amount in query else 'response'
            })

        # Pattern: Risk keywords
        risk_keywords = ['risk', 'threat', 'problem', 'challenge', 'issue', 'tariff', 'competition']
        for keyword in risk_keywords:
            if keyword in combined_text:
                extracted['risks'].append({
                    'title': f'{keyword.title()} Identified',
                    'description': f'Mention of {keyword} in conversation',
                    'severity': 'MEDIUM',
                    'confidence': 0.4,
                    'source_authority': source_type,
                    'verification_status': 'PROVISIONAL',
                    'explicit': False,
                    'extracted_from': 'query' if keyword in query.lower() else 'response'
                })

        return extracted


# ============================================================================
# Backward Compatibility: FactExtractor alias
# ============================================================================

class FactExtractor(EnhancedFactExtractor):
    """Alias for backward compatibility with Kogna 1.0 code."""
    pass

"""
Kogna Memory Manager - Supabase Integration
===========================================

Adapts the dual memory system to use Kogna's existing Supabase infrastructure.

Usage:
    memory = get_user_memory(user_id="user_123")

    # Get context for query
    context = await memory.get_context(query="What are our risks?", session_id="session_1")

    # Store interaction with extracted facts
    await memory.process_interaction(
        query="Our Q3 revenue dropped 15% due to tariffs",
        response="I'll analyze that...",
        session_id="session_1",
        extracted_facts=[...]
    )
"""

import os
import logging
from typing import Optional, Dict, List
from datetime import datetime

# Import dual memory system
from .dual_memory.memory_system import (
    UserMemorySystem,
    EmbeddingProvider,
    FactType,
    RiskSeverity,
)

# Import fact extraction
from .dual_memory.fact_extraction import FactExtractor

# Import Kogna's existing services
from supabase_connect import get_supabase_manager
from langchain_google_genai import GoogleGenerativeAIEmbeddings

logger = logging.getLogger(__name__)


# ============================================================
# GEMINI EMBEDDING ADAPTER
# ============================================================

class GeminiEmbeddingProvider(EmbeddingProvider):
    """
    Adapter for Google Gemini embeddings (Kogna's existing embedding model).
    """

    def __init__(self):
        self.model = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )

    async def embed(self, text: str) -> List[float]:
        """Generate embedding for single text"""
        try:
            # Gemini's embed_query is synchronous, but we're in async context
            import asyncio
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(None, self.model.embed_query, text)
            return embedding
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            # Return zero vector as fallback
            return [0.0] * 768

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for batch of texts"""
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(None, self.model.embed_documents, texts)
            return embeddings
        except Exception as e:
            logger.error(f"Batch embedding error: {e}")
            # Return zero vectors as fallback
            return [[0.0] * 768 for _ in texts]


# ============================================================
# SUPABASE STORAGE ADAPTER
# ============================================================

class SupabaseMemoryStorage:
    """
    Stores memory data in Supabase.

    Tables needed:
    - user_conversational_memory: Conversation history with embeddings
    - user_business_facts: Business facts with embeddings
    - user_risks: Risk records
    - user_metric_definitions: Metric definitions
    - user_preferences: User preferences
    - user_company_context: Company context
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.supabase = get_supabase_manager().client

    # ----- CONVERSATIONAL MEMORY -----

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
                "created_at": entry.get("created_at", datetime.now().isoformat())
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
        """Search conversations using vector similarity"""
        try:
            # Use RPC function for vector search
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

    async def save_preference(self, preference: Dict):
        """Save or update user preference"""
        try:
            # Upsert (update if exists, insert if not)
            self.supabase.table("user_preferences").upsert({
                "user_id": self.user_id,
                "key": preference["key"],
                "value": preference["value"],
                "confidence": preference.get("confidence", 0.5),
                "learned_from_count": preference.get("learned_from_count", 1),
                "last_updated": datetime.now().isoformat()
            }, on_conflict="user_id,key").execute()
        except Exception as e:
            logger.error(f"Error saving preference: {e}")

    async def get_preferences(self) -> Dict:
        """Get all user preferences"""
        try:
            result = self.supabase.table("user_preferences").select("*").eq(
                "user_id", self.user_id
            ).execute()

            return {row["key"]: row for row in result.data} if result.data else {}
        except Exception as e:
            logger.error(f"Error getting preferences: {e}")
            return {}

    # ----- BUSINESS KNOWLEDGE MEMORY -----

    async def save_fact(self, fact: Dict) -> str:
        """Save business fact"""
        try:
            result = self.supabase.table("user_business_facts").insert({
                "user_id": self.user_id,
                "fact_type": fact["fact_type"],
                "subject": fact["subject"],
                "predicate": fact["predicate"],
                "value": fact["value"],
                "confidence": fact.get("confidence", 0.8),
                "source_text": fact.get("source_text"),
                "source_conversation_id": fact.get("source_conversation_id"),
                "embedding": fact.get("embedding"),
                "valid_from": fact.get("valid_from", datetime.now().isoformat()),
                "valid_to": fact.get("valid_to"),
                "recorded_at": datetime.now().isoformat()
            }).execute()

            return result.data[0]["id"] if result.data else None
        except Exception as e:
            logger.error(f"Error saving fact: {e}")
            return None

    async def search_facts(
        self,
        query_embedding: List[float],
        limit: int = 10,
        fact_types: Optional[List[str]] = None
    ) -> List[Dict]:
        """Search business facts using vector similarity"""
        try:
            result = self.supabase.rpc('match_user_facts', {
                'query_embedding': query_embedding,
                'match_count': limit,
                'p_user_id': self.user_id,
                'p_fact_types': fact_types
            }).execute()

            return result.data or []
        except Exception as e:
            logger.error(f"Error searching facts: {e}")
            return []

    async def save_risk(self, risk: Dict) -> str:
        """Save user risk"""
        try:
            result = self.supabase.table("user_risks").insert({
                "user_id": self.user_id,
                "title": risk["title"],
                "description": risk["description"],
                "category": risk["category"],
                "severity": risk["severity"],
                "cause": risk.get("cause"),
                "impact": risk.get("impact"),
                "mitigation": risk.get("mitigation"),
                "owner": risk.get("owner"),
                "embedding": risk.get("embedding"),
                "source_conversation_id": risk.get("source_conversation_id"),
                "identified_at": datetime.now().isoformat(),
                "valid_from": datetime.now().isoformat(),
                "last_mentioned": datetime.now().isoformat()
            }).execute()

            return result.data[0]["id"] if result.data else None
        except Exception as e:
            logger.error(f"Error saving risk: {e}")
            return None

    async def get_active_risks(self) -> List[Dict]:
        """Get all active risks (valid_to is null)"""
        try:
            result = self.supabase.table("user_risks").select("*").eq(
                "user_id", self.user_id
            ).is_("valid_to", "null").execute()

            return result.data or []
        except Exception as e:
            logger.error(f"Error getting risks: {e}")
            return []

    async def save_metric_definition(self, metric: Dict) -> str:
        """Save metric definition"""
        try:
            result = self.supabase.table("user_metric_definitions").insert({
                "user_id": self.user_id,
                "name": metric["name"],
                "user_definition": metric["user_definition"],
                "calculation": metric.get("calculation"),
                "context": metric.get("context"),
                "embedding": metric.get("embedding"),
                "recorded_at": datetime.now().isoformat(),
                "last_used": datetime.now().isoformat()
            }).execute()

            return result.data[0]["id"] if result.data else None
        except Exception as e:
            logger.error(f"Error saving metric: {e}")
            return None

    async def get_metric_definition(self, name: str) -> Optional[Dict]:
        """Get metric definition by name"""
        try:
            result = self.supabase.table("user_metric_definitions").select("*").eq(
                "user_id", self.user_id
            ).ilike("name", name).maybe_single().execute()

            return result.data if result.data else None
        except Exception as e:
            logger.error(f"Error getting metric: {e}")
            return None

    async def save_company_context(self, key: str, value: str, source_conversation_id: Optional[str] = None):
        """Save company context"""
        try:
            self.supabase.table("user_company_context").upsert({
                "user_id": self.user_id,
                "key": key,
                "value": value,
                "source_conversation_id": source_conversation_id,
                "valid_from": datetime.now().isoformat(),  # FIX: Set valid_from for retrieval
                "recorded_at": datetime.now().isoformat()
            }, on_conflict="user_id,key").execute()
        except Exception as e:
            logger.error(f"Error saving company context: {e}")

    async def get_company_context(self) -> Dict:
        """Get all company context"""
        try:
            result = self.supabase.table("user_company_context").select("*").eq(
                "user_id", self.user_id
            ).execute()

            return {row["key"]: row["value"] for row in result.data} if result.data else {}
        except Exception as e:
            logger.error(f"Error getting company context: {e}")
            return {}


# ============================================================
# MEMORY MANAGER (Main Interface)
# ============================================================

class KognaMemoryManager:
    """
    Main memory manager for Kogna.
    Combines dual memory system with Supabase storage.
    """

    def __init__(self, user_id: str, use_llm_extraction: bool = True):
        self.user_id = user_id

        # Initialize embedding provider (Gemini)
        self.embedding_provider = GeminiEmbeddingProvider()

        # Initialize dual memory system
        self.memory = UserMemorySystem(
            user_id=user_id,
            embedding_provider=self.embedding_provider
        )

        # Initialize Supabase storage
        self.storage = SupabaseMemoryStorage(user_id)

        # Initialize fact extractor
        self.fact_extractor = self._init_fact_extractor(use_llm_extraction)

        logger.info(f"✓ Memory manager initialized for user {user_id}")

    def _init_fact_extractor(self, use_llm: bool) -> FactExtractor:
        """Initialize fact extractor with LLM if available"""
        if use_llm:
            try:
                from Ai_agents.llm_factory import get_openai_client
                client = get_openai_client()
                return FactExtractor(llm_client=client, model="gpt-4o-mini")
            except Exception as e:
                logger.warning(f"LLM extraction unavailable, using rules: {e}")
                return FactExtractor()  # Rule-based fallback
        else:
            return FactExtractor()  # Rule-based

    async def get_context(self, query: str, session_id: str) -> Dict:
        """
        Get relevant memory context for a query.

        Returns enriched context with:
        - Session state
        - Relevant past conversations
        - User preferences
        - Business facts
        - Active risks
        - Relevant metrics
        - Company context
        """
        logger.info(f"Fetching memory context for query: {query[:60]}...")

        # Use in-memory system to get context
        context = await self.memory.get_context(query=query, session_id=session_id)

        # Enhance with Supabase data
        query_embedding = await self.embedding_provider.embed(query)

        # Get conversations from Supabase
        context["relevant_conversations"] = await self.storage.search_conversations(
            query_embedding=query_embedding,
            limit=5,
            session_id=None  # Search across all sessions
        )

        # Get facts from Supabase
        context["business_facts"] = await self.storage.search_facts(
            query_embedding=query_embedding,
            limit=10
        )

        # Get risks from Supabase
        context["active_risks"] = await self.storage.get_active_risks()

        # Get preferences from Supabase
        prefs = await self.storage.get_preferences()
        context["user_preferences"] = {k: v["value"] for k, v in prefs.items()}

        # Get company context from Supabase
        context["company_context"] = await self.storage.get_company_context()

        logger.info(f"✓ Context retrieved: {len(context['relevant_conversations'])} convos, "
                   f"{len(context['business_facts'])} facts, {len(context['active_risks'])} risks")

        return context

    async def process_interaction(
        self,
        query: str,
        response: str,
        session_id: str,
        auto_extract: bool = True
    ) -> Dict:
        """
        Process a conversation turn:
        1. Store conversation
        2. Extract and store facts (if auto_extract=True)

        Returns: Summary of what was stored
        """
        logger.info("Processing interaction...")

        stored = {
            "conversation_id": None,
            "facts_stored": 0,
            "risks_stored": 0,
            "metrics_stored": 0,
            "company_info_stored": 0,
            "preferences_learned": 0
        }

        # 1. Store conversation in memory
        conv_id = await self.memory.conversational.add_conversation(
            session_id=session_id,
            query=query,
            response=response
        )
        stored["conversation_id"] = conv_id

        # Also persist to Supabase
        await self.storage.save_conversation({
            "session_id": session_id,
            "query": query,
            "response_summary": response[:500],
            "created_at": datetime.now().isoformat()
        })

        # 2. Extract facts if enabled
        if auto_extract:
            extraction = await self.fact_extractor.extract(
                user_message=query,
                assistant_response=response
            )

            if extraction.has_extractable_content:
                # Store company info
                for info in extraction.company_info:
                    await self.storage.save_company_context(
                        key=info.info_type,
                        value=info.value,
                        source_conversation_id=conv_id
                    )
                    stored["company_info_stored"] += 1

                # Store metrics
                for metric in extraction.metrics:
                    if metric.metric_type == "definition" and metric.definition:
                        await self.storage.save_metric_definition({
                            "name": metric.metric_name,
                            "user_definition": metric.definition,
                            "context": metric.source_text
                        })
                        stored["metrics_stored"] += 1

                    # Also store metric values as facts
                    if metric.value is not None:
                        await self.memory.business.add_fact(
                            fact_type=FactType.METRIC_VALUE,
                            subject=metric.metric_name,
                            predicate="value",
                            value=f"{metric.value} {metric.unit or ''}".strip(),
                            confidence=metric.confidence,
                            source_text=metric.source_text,
                            source_conversation_id=conv_id
                        )
                        stored["facts_stored"] += 1

                # Store risks
                for risk in extraction.risks:
                    await self.storage.save_risk({
                        "title": risk.title,
                        "description": risk.description,
                        "category": risk.category,
                        "severity": risk.severity,
                        "cause": risk.cause,
                        "impact": risk.impact,
                        "source_conversation_id": conv_id
                    })
                    stored["risks_stored"] += 1

                # Store general facts
                for fact in extraction.facts:
                    fact_type = FactType(fact.fact_type) if fact.fact_type in FactType.__members__ else FactType.UNKNOWN
                    await self.memory.business.add_fact(
                        fact_type=fact_type,
                        subject=fact.subject,
                        predicate=fact.predicate,
                        value=fact.value,
                        confidence=fact.confidence,
                        source_text=fact.source_text,
                        source_conversation_id=conv_id
                    )
                    stored["facts_stored"] += 1

                # Store preferences
                for pref in extraction.preferences:
                    await self.memory.conversational.learn_preference(
                        key=pref.preference_type,
                        value=pref.value,
                        confidence_boost=pref.confidence
                    )
                    await self.storage.save_preference({
                        "key": pref.preference_type,
                        "value": pref.value,
                        "confidence": pref.confidence
                    })
                    stored["preferences_learned"] += 1

                logger.info(f"✓ Extracted: {stored['facts_stored']} facts, "
                           f"{stored['risks_stored']} risks, {stored['metrics_stored']} metrics, "
                           f"{stored['company_info_stored']} company info, "
                           f"{stored['preferences_learned']} preferences")

        return stored

    async def get_summary(self) -> Dict:
        """Get summary of stored memory"""
        return await self.memory.get_memory_summary()


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================

# Cache memory managers per user
_memory_managers: Dict[str, KognaMemoryManager] = {}


def get_user_memory(user_id: str, use_llm_extraction: bool = True) -> KognaMemoryManager:
    """
    Get or create memory manager for a user.

    Args:
        user_id: User ID
        use_llm_extraction: Use LLM for fact extraction (more accurate but requires API)

    Returns:
        KognaMemoryManager instance
    """
    if user_id not in _memory_managers:
        _memory_managers[user_id] = KognaMemoryManager(user_id, use_llm_extraction)
    return _memory_managers[user_id]


async def get_memory_context(user_id: str, query: str, session_id: str) -> Dict:
    """
    Quick helper to get memory context.

    Usage:
        context = await get_memory_context(user_id="user_123", query="What are our risks?", session_id="session_1")
    """
    memory = get_user_memory(user_id)
    return await memory.get_context(query, session_id)


async def store_interaction(user_id: str, query: str, response: str, session_id: str) -> Dict:
    """
    Quick helper to store interaction with auto fact extraction.

    Usage:
        result = await store_interaction(user_id="user_123", query="...", response="...", session_id="session_1")
    """
    memory = get_user_memory(user_id)
    return await memory.process_interaction(query, response, session_id, auto_extract=True)

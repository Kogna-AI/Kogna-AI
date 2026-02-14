# memory_system.py
"""
Kogna Dual Memory System - Complete Working Prototype
=====================================================

Two user-centric memories:
1. Conversational Memory - Chat history, preferences, session context
2. Business Knowledge Memory - Facts, risks, metrics, company info

Each user has isolated data. Phase 2 will add organizational connections.
"""

from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from enum import Enum
import uuid
import json
import asyncio
from abc import ABC, abstractmethod


# ============================================================
# ENUMS & BASE MODELS
# ============================================================

class FactType(str, Enum):
    COMPANY_INFO = "company_info"
    METRIC_VALUE = "metric_value"
    METRIC_DEFINITION = "metric_definition"
    METRIC_TARGET = "metric_target"
    METRIC_COMPARISON = "metric_comparison"
    RISK = "risk"
    TEMPORAL_EVENT = "temporal_event"
    RELATIONSHIP = "relationship"
    BUSINESS_RULE = "business_rule"
    PREFERENCE = "preference"
    UNKNOWN = "unknown"


class RiskSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class SessionContext(BaseModel):
    session_id: str
    user_id: str
    started_at: datetime = Field(default_factory=datetime.now)
    last_active: datetime = Field(default_factory=datetime.now)
    active_filters: Dict = Field(default_factory=dict)
    current_topic: Optional[str] = None
    conversation_history: List[Message] = Field(default_factory=list)


class UserPreference(BaseModel):
    user_id: str
    key: str
    value: str
    confidence: float = 0.5
    learned_from_count: int = 1
    last_updated: datetime = Field(default_factory=datetime.now)


class ConversationEntry(BaseModel):
    entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_id: str
    query: str
    response_summary: str
    entities: List[str] = Field(default_factory=list)
    embedding: Optional[List[float]] = None
    was_helpful: Optional[bool] = None
    created_at: datetime = Field(default_factory=datetime.now)


class BusinessFact(BaseModel):
    fact_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    fact_type: FactType
    subject: str
    predicate: str
    value: Any
    confidence: float = 0.8
    source_text: Optional[str] = None
    source_conversation_id: Optional[str] = None
    valid_from: datetime = Field(default_factory=datetime.now)
    valid_to: Optional[datetime] = None
    recorded_at: datetime = Field(default_factory=datetime.now)
    embedding: Optional[List[float]] = None


class UserRisk(BaseModel):
    risk_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    description: str
    category: str  # financial, operational, compliance, strategic, market
    severity: RiskSeverity = RiskSeverity.UNKNOWN
    cause: Optional[str] = None
    impact: Optional[str] = None
    mitigation: Optional[str] = None
    owner: Optional[str] = None
    identified_at: datetime = Field(default_factory=datetime.now)
    valid_from: datetime = Field(default_factory=datetime.now)
    valid_to: Optional[datetime] = None
    last_mentioned: datetime = Field(default_factory=datetime.now)
    source_conversation_id: Optional[str] = None
    embedding: Optional[List[float]] = None


class MetricDefinition(BaseModel):
    metric_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    user_definition: str
    calculation: Optional[str] = None
    context: Optional[str] = None
    recorded_at: datetime = Field(default_factory=datetime.now)
    last_used: datetime = Field(default_factory=datetime.now)
    embedding: Optional[List[float]] = None


class CompanyContext(BaseModel):
    context_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    key: str
    value: str
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    recorded_at: datetime = Field(default_factory=datetime.now)
    source_conversation_id: Optional[str] = None


# ============================================================
# EMBEDDING INTERFACE
# ============================================================

class EmbeddingProvider(ABC):
    """Abstract embedding provider interface"""
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        pass


class OpenAIEmbedding(EmbeddingProvider):
    """OpenAI embedding implementation"""
    
    def __init__(self, client, model: str = "text-embedding-3-small"):
        self.client = client
        self.model = model
    
    async def embed(self, text: str) -> List[float]:
        response = await self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        response = await self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        return [d.embedding for d in response.data]


class MockEmbedding(EmbeddingProvider):
    """Mock embedding for testing (no API needed)"""
    
    def __init__(self, dimension: int = 1536):
        self.dimension = dimension
    
    async def embed(self, text: str) -> List[float]:
        import hashlib
        # Create deterministic pseudo-embedding from text hash
        hash_bytes = hashlib.sha256(text.encode()).digest()
        # Expand to full dimension
        embedding = []
        for i in range(self.dimension):
            byte_idx = i % len(hash_bytes)
            embedding.append((hash_bytes[byte_idx] - 128) / 128.0)
        return embedding
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [await self.embed(t) for t in texts]


# ============================================================
# STORAGE BACKENDS
# ============================================================

class InMemoryVectorStore:
    """
    Simple in-memory vector store for prototyping.
    Replace with Qdrant in production.
    """
    
    def __init__(self):
        self.data: Dict[str, Dict] = {}  # id -> {embedding, payload}
    
    def add(self, id: str, embedding: List[float], payload: Dict):
        self.data[id] = {"embedding": embedding, "payload": payload}
    
    def search(
        self,
        query_embedding: List[float],
        filter_fn: callable = None,
        limit: int = 10
    ) -> List[Tuple[str, float, Dict]]:
        """Search with cosine similarity"""
        results = []
        
        for id, item in self.data.items():
            # Apply filter
            if filter_fn and not filter_fn(item["payload"]):
                continue
            
            # Calculate similarity
            score = self._cosine_similarity(query_embedding, item["embedding"])
            results.append((id, score, item["payload"]))
        
        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]
    
    def get(self, id: str) -> Optional[Dict]:
        return self.data.get(id)
    
    def update(self, id: str, payload_updates: Dict):
        if id in self.data:
            self.data[id]["payload"].update(payload_updates)
    
    def delete(self, id: str):
        if id in self.data:
            del self.data[id]
    
    def delete_by_filter(self, filter_fn: callable):
        to_delete = [id for id, item in self.data.items() if filter_fn(item["payload"])]
        for id in to_delete:
            del self.data[id]
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


class InMemoryCache:
    """
    Simple in-memory cache for prototyping.
    Replace with Redis in production.
    """
    
    def __init__(self):
        self.data: Dict[str, Tuple[Any, Optional[datetime]]] = {}  # key -> (value, expiry)
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        expiry = None
        if ttl_seconds:
            expiry = datetime.now() + timedelta(seconds=ttl_seconds)
        self.data[key] = (value, expiry)
    
    def get(self, key: str) -> Optional[Any]:
        if key not in self.data:
            return None
        value, expiry = self.data[key]
        if expiry and datetime.now() > expiry:
            del self.data[key]
            return None
        return value
    
    def delete(self, key: str):
        if key in self.data:
            del self.data[key]
    
    def keys(self, pattern: str = "*") -> List[str]:
        """Simple pattern matching (only supports prefix*)"""
        if pattern == "*":
            return list(self.data.keys())
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            return [k for k in self.data.keys() if k.startswith(prefix)]
        return [k for k in self.data.keys() if k == pattern]


# ============================================================
# MEMORY 1: CONVERSATIONAL MEMORY
# ============================================================

class ConversationalMemory:
    """
    Memory 1: Handles conversation history, session context, and user preferences.
    Stores HOW to talk with this user.
    """
    
    def __init__(self, user_id: str, embedding_provider: EmbeddingProvider):
        self.user_id = user_id
        self.embedding = embedding_provider
        
        # Storage backends
        self.vector_store = InMemoryVectorStore()
        self.cache = InMemoryCache()
        
        # In-memory for quick access
        self.sessions: Dict[str, SessionContext] = {}
        self.preferences: Dict[str, UserPreference] = {}
    
    # ----- SESSION MANAGEMENT -----
    
    async def get_or_create_session(self, session_id: str) -> SessionContext:
        """Get existing session or create new one"""
        if session_id in self.sessions:
            return self.sessions[session_id]
        
        # Check cache
        cached = self.cache.get(f"session:{self.user_id}:{session_id}")
        if cached:
            self.sessions[session_id] = SessionContext(**cached)
            return self.sessions[session_id]
        
        # Create new
        session = SessionContext(
            session_id=session_id,
            user_id=self.user_id
        )
        self.sessions[session_id] = session
        return session
    
    async def update_session(
        self,
        session_id: str,
        filters: Optional[Dict] = None,
        topic: Optional[str] = None
    ):
        """Update session state"""
        session = await self.get_or_create_session(session_id)
        
        if filters is not None:
            session.active_filters = filters
        if topic is not None:
            session.current_topic = topic
        
        session.last_active = datetime.now()
        
        # Persist to cache
        self.cache.set(
            f"session:{self.user_id}:{session_id}",
            session.model_dump(mode='json'),
            ttl_seconds=86400  # 24 hours
        )
    
    # ----- CONVERSATION STORAGE -----
    
    async def add_conversation(
        self,
        session_id: str,
        query: str,
        response: str,
        entities: List[str] = None,
        was_helpful: Optional[bool] = None
    ) -> str:
        """Store a conversation turn"""
        # Get/create session
        session = await self.get_or_create_session(session_id)
        
        # Add to session history
        session.conversation_history.append(Message(role="user", content=query))
        session.conversation_history.append(Message(role="assistant", content=response))
        session.last_active = datetime.now()
        
        # Create entry for vector search
        entry = ConversationEntry(
            user_id=self.user_id,
            session_id=session_id,
            query=query,
            response_summary=self._summarize(response),
            entities=entities or self._extract_entities(query + " " + response),
            was_helpful=was_helpful
        )
        
        # Generate embedding
        text_to_embed = f"{query} {entry.response_summary}"
        entry.embedding = await self.embedding.embed(text_to_embed)
        
        # Store in vector store
        self.vector_store.add(
            id=entry.entry_id,
            embedding=entry.embedding,
            payload=entry.model_dump(mode='json')
        )
        
        return entry.entry_id
    
    async def search_conversations(
        self,
        query: str,
        limit: int = 5,
        session_id: Optional[str] = None
    ) -> List[Dict]:
        """Find relevant past conversations"""
        query_embedding = await self.embedding.embed(query)
        
        def filter_fn(payload):
            if payload.get("user_id") != self.user_id:
                return False
            if session_id and payload.get("session_id") != session_id:
                return False
            return True
        
        results = self.vector_store.search(
            query_embedding=query_embedding,
            filter_fn=filter_fn,
            limit=limit
        )
        
        return [
            {"id": id, "score": score, **payload}
            for id, score, payload in results
        ]
    
    # ----- PREFERENCES -----
    
    async def learn_preference(
        self,
        key: str,
        value: str,
        confidence_boost: float = 0.1
    ):
        """Learn or reinforce a user preference"""
        if key in self.preferences:
            pref = self.preferences[key]
            pref.value = value
            pref.confidence = min(1.0, pref.confidence + confidence_boost)
            pref.learned_from_count += 1
            pref.last_updated = datetime.now()
        else:
            self.preferences[key] = UserPreference(
                user_id=self.user_id,
                key=key,
                value=value,
                confidence=0.5
            )
        
        # Persist
        self._save_preferences()
    
    async def get_preferences(self) -> Dict[str, UserPreference]:
        """Get all learned preferences"""
        return self.preferences.copy()
    
    async def get_preference(self, key: str) -> Optional[UserPreference]:
        """Get a specific preference"""
        return self.preferences.get(key)
    
    def _save_preferences(self):
        """Persist preferences to cache"""
        prefs_data = {k: v.model_dump(mode='json') for k, v in self.preferences.items()}
        self.cache.set(
            f"prefs:{self.user_id}",
            prefs_data,
            ttl_seconds=604800  # 7 days
        )
    
    # ----- HELPERS -----
    
    def _summarize(self, text: str, max_length: int = 500) -> str:
        """Simple summarization (truncation)"""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."
    
    def _extract_entities(self, text: str) -> List[str]:
        """Simple entity extraction (keyword-based)"""
        # In production, use NER or more sophisticated extraction
        words = text.lower().split()
        # Filter common words, keep potential entities
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                     'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                     'would', 'could', 'should', 'may', 'might', 'must', 'can',
                     'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she',
                     'it', 'we', 'they', 'what', 'which', 'who', 'when', 'where',
                     'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more',
                     'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
                     'own', 'same', 'so', 'than', 'too', 'very', 'just', 'and',
                     'but', 'or', 'because', 'as', 'until', 'while', 'of', 'at',
                     'by', 'for', 'with', 'about', 'against', 'between', 'into',
                     'through', 'during', 'before', 'after', 'above', 'below',
                     'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over',
                     'under', 'again', 'further', 'then', 'once', 'here', 'there',
                     'when', 'where', 'why', 'how', 'our', 'my', 'your', 'their'}
        
        entities = [w for w in words if w not in stopwords and len(w) > 2]
        return list(set(entities))[:20]  # Limit to 20 unique entities


# ============================================================
# MEMORY 2: BUSINESS KNOWLEDGE MEMORY
# ============================================================

class BusinessKnowledgeMemory:
    """
    Memory 2: Handles business facts, risks, metrics, and company context.
    Stores WHAT this user knows/has shared about their business.
    """
    
    def __init__(self, user_id: str, embedding_provider: EmbeddingProvider):
        self.user_id = user_id
        self.embedding = embedding_provider
        
        # Storage backends
        self.vector_store = InMemoryVectorStore()
        self.cache = InMemoryCache()
        
        # Structured storage for typed data
        self.risks: Dict[str, UserRisk] = {}
        self.metrics: Dict[str, MetricDefinition] = {}
        self.company_context: Dict[str, CompanyContext] = {}
    
    # ----- BUSINESS FACTS -----
    
    async def add_fact(
        self,
        fact_type: FactType,
        subject: str,
        predicate: str,
        value: Any,
        confidence: float = 0.8,
        source_text: Optional[str] = None,
        source_conversation_id: Optional[str] = None,
        valid_from: Optional[datetime] = None
    ) -> str:
        """Add a business fact"""
        fact = BusinessFact(
            user_id=self.user_id,
            fact_type=fact_type,
            subject=subject,
            predicate=predicate,
            value=value,
            confidence=confidence,
            source_text=source_text,
            source_conversation_id=source_conversation_id,
            valid_from=valid_from or datetime.now()
        )
        
        # Generate embedding
        text_to_embed = f"{subject} {predicate} {value}"
        fact.embedding = await self.embedding.embed(text_to_embed)
        
        # Check for existing similar fact
        existing = await self._find_similar_fact(fact)
        if existing:
            # Update existing fact if new one is higher confidence or more recent
            if fact.confidence >= existing.get("confidence", 0):
                await self.invalidate_fact(existing["fact_id"])
        
        # Store
        self.vector_store.add(
            id=fact.fact_id,
            embedding=fact.embedding,
            payload=fact.model_dump(mode='json')
        )
        
        return fact.fact_id
    
    async def search_facts(
        self,
        query: str,
        limit: int = 10,
        fact_types: Optional[List[FactType]] = None,
        include_invalid: bool = False
    ) -> List[Dict]:
        """Search business facts"""
        query_embedding = await self.embedding.embed(query)
        
        def filter_fn(payload):
            if payload.get("user_id") != self.user_id:
                return False
            if fact_types:
                if payload.get("fact_type") not in [ft.value for ft in fact_types]:
                    return False
            if not include_invalid and payload.get("valid_to") is not None:
                return False
            return True
        
        results = self.vector_store.search(
            query_embedding=query_embedding,
            filter_fn=filter_fn,
            limit=limit
        )
        
        return [
            {"id": id, "score": score, **payload}
            for id, score, payload in results
        ]
    
    async def invalidate_fact(self, fact_id: str, valid_to: Optional[datetime] = None):
        """Mark a fact as no longer valid"""
        self.vector_store.update(
            fact_id,
            {"valid_to": (valid_to or datetime.now()).isoformat()}
        )
    
    async def _find_similar_fact(self, fact: BusinessFact, threshold: float = 0.9) -> Optional[Dict]:
        """Find existing similar fact"""
        results = await self.search_facts(
            f"{fact.subject} {fact.predicate}",
            limit=1,
            fact_types=[fact.fact_type]
        )
        if results and results[0]["score"] > threshold:
            return results[0]
        return None
    
    # ----- RISKS -----
    
    async def add_risk(
        self,
        title: str,
        description: str,
        category: str,
        severity: RiskSeverity = RiskSeverity.UNKNOWN,
        cause: Optional[str] = None,
        impact: Optional[str] = None,
        mitigation: Optional[str] = None,
        owner: Optional[str] = None,
        source_conversation_id: Optional[str] = None
    ) -> str:
        """Add or update a risk"""
        risk = UserRisk(
            user_id=self.user_id,
            title=title,
            description=description,
            category=category,
            severity=severity,
            cause=cause,
            impact=impact,
            mitigation=mitigation,
            owner=owner,
            source_conversation_id=source_conversation_id
        )
        
        # Generate embedding
        text_to_embed = f"{title} {description} {category}"
        risk.embedding = await self.embedding.embed(text_to_embed)
        
        # Store in risks dict
        self.risks[risk.risk_id] = risk
        
        # Also store in vector store for search
        self.vector_store.add(
            id=risk.risk_id,
            embedding=risk.embedding,
            payload={
                **risk.model_dump(mode='json'),
                "fact_type": FactType.RISK.value
            }
        )
        
        return risk.risk_id
    
    async def get_active_risks(self) -> List[UserRisk]:
        """Get all currently active risks"""
        return [r for r in self.risks.values() if r.valid_to is None]
    
    async def get_risks_by_severity(self, min_severity: RiskSeverity = RiskSeverity.MEDIUM) -> List[UserRisk]:
        """Get risks at or above a severity level"""
        severity_order = [RiskSeverity.LOW, RiskSeverity.MEDIUM, RiskSeverity.HIGH, RiskSeverity.CRITICAL]
        min_idx = severity_order.index(min_severity) if min_severity in severity_order else 0
        
        return [
            r for r in self.risks.values()
            if r.valid_to is None and (
                r.severity in severity_order[min_idx:] or r.severity == RiskSeverity.UNKNOWN
            )
        ]
    
    async def resolve_risk(self, risk_id: str, resolution_note: Optional[str] = None):
        """Mark a risk as resolved"""
        if risk_id in self.risks:
            self.risks[risk_id].valid_to = datetime.now()
            await self.invalidate_fact(risk_id)
    
    # ----- METRICS -----
    
    async def add_metric_definition(
        self,
        name: str,
        user_definition: str,
        calculation: Optional[str] = None,
        context: Optional[str] = None
    ) -> str:
        """Store how user defines a metric"""
        metric = MetricDefinition(
            user_id=self.user_id,
            name=name,
            user_definition=user_definition,
            calculation=calculation,
            context=context
        )
        
        # Generate embedding
        text_to_embed = f"{name} {user_definition}"
        metric.embedding = await self.embedding.embed(text_to_embed)
        
        # Store (overwrite if exists)
        self.metrics[name.lower()] = metric
        
        # Also store as fact for search
        await self.add_fact(
            fact_type=FactType.METRIC_DEFINITION,
            subject=name,
            predicate="is_defined_as",
            value=user_definition,
            confidence=1.0
        )
        
        return metric.metric_id
    
    async def get_metric_definition(self, name: str) -> Optional[MetricDefinition]:
        """Get definition for a metric"""
        return self.metrics.get(name.lower())
    
    async def get_relevant_metrics(self, query: str) -> List[MetricDefinition]:
        """Get metrics relevant to a query"""
        query_lower = query.lower()
        return [m for name, m in self.metrics.items() if name in query_lower]
    
    # ----- COMPANY CONTEXT -----
    
    async def set_company_context(
        self,
        key: str,
        value: str,
        source_conversation_id: Optional[str] = None
    ):
        """Store company context"""
        context = CompanyContext(
            user_id=self.user_id,
            key=key,
            value=value,
            source_conversation_id=source_conversation_id
        )
        
        # Store (overwrite if exists)
        self.company_context[key] = context
        
        # Also store as fact
        await self.add_fact(
            fact_type=FactType.COMPANY_INFO,
            subject="company",
            predicate=key,
            value=value,
            confidence=1.0,
            source_conversation_id=source_conversation_id
        )
        
        # Cache for quick access
        self._save_company_context()
    
    async def get_company_context(self, key: Optional[str] = None) -> Dict:
        """Get company context"""
        if key:
            ctx = self.company_context.get(key)
            return {key: ctx.value} if ctx else {}
        return {k: v.value for k, v in self.company_context.items()}
    
    def _save_company_context(self):
        """Persist to cache"""
        ctx_data = {k: v.model_dump(mode='json') for k, v in self.company_context.items()}
        self.cache.set(
            f"company:{self.user_id}",
            ctx_data,
            ttl_seconds=604800  # 7 days
        )


# ============================================================
# UNIFIED MEMORY SYSTEM
# ============================================================

class UserMemorySystem:
    """
    Complete memory system for a single user.
    Combines both conversational and business knowledge memories.
    """
    
    def __init__(
        self,
        user_id: str,
        embedding_provider: Optional[EmbeddingProvider] = None
    ):
        self.user_id = user_id
        
        # Use mock embeddings if no provider specified
        self.embedding = embedding_provider or MockEmbedding()
        
        # Initialize both memories
        self.conversational = ConversationalMemory(user_id, self.embedding)
        self.business = BusinessKnowledgeMemory(user_id, self.embedding)
    
    async def process_interaction(
        self,
        query: str,
        response: str,
        session_id: str,
        extracted_facts: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Process a conversation turn:
        1. Store in conversational memory
        2. Store any extracted business facts
        
        Returns: Summary of what was stored
        """
        stored = {
            "conversation_id": None,
            "facts_stored": 0,
            "risks_stored": 0
        }
        
        # Store conversation
        conv_id = await self.conversational.add_conversation(
            session_id=session_id,
            query=query,
            response=response
        )
        stored["conversation_id"] = conv_id
        
        # Store extracted facts
        if extracted_facts:
            for fact_data in extracted_facts:
                fact_type = fact_data.get("fact_type")
                
                if fact_type == "risk":
                    await self.business.add_risk(
                        title=fact_data.get("title", ""),
                        description=fact_data.get("description", ""),
                        category=fact_data.get("category", "unknown"),
                        severity=RiskSeverity(fact_data.get("severity", "unknown")),
                        cause=fact_data.get("cause"),
                        impact=fact_data.get("impact"),
                        source_conversation_id=conv_id
                    )
                    stored["risks_stored"] += 1
                else:
                    # Handle fact type, with fallback for unknown types
                    try:
                        ft = FactType(fact_type) if fact_type else FactType.COMPANY_INFO
                    except ValueError:
                        ft = FactType.UNKNOWN
                    
                    await self.business.add_fact(
                        fact_type=ft,
                        subject=fact_data.get("subject", ""),
                        predicate=fact_data.get("predicate", ""),
                        value=fact_data.get("value", ""),
                        confidence=fact_data.get("confidence", 0.8),
                        source_text=fact_data.get("source_text"),
                        source_conversation_id=conv_id
                    )
                    stored["facts_stored"] += 1
        
        return stored
    
    async def get_context(
        self,
        query: str,
        session_id: str
    ) -> Dict:
        """
        Retrieve relevant context from both memories for a query.
        """
        context = {
            "session": None,
            "relevant_conversations": [],
            "user_preferences": {},
            "business_facts": [],
            "active_risks": [],
            "relevant_metrics": [],
            "company_context": {}
        }
        
        # Get session context
        context["session"] = await self.conversational.get_or_create_session(session_id)
        
        # Get relevant past conversations
        context["relevant_conversations"] = await self.conversational.search_conversations(
            query, limit=5
        )
        
        # Get preferences
        prefs = await self.conversational.get_preferences()
        context["user_preferences"] = {k: v.value for k, v in prefs.items()}
        
        # Get relevant business knowledge
        context["business_facts"] = await self.business.search_facts(query, limit=10)
        
        # Get active risks
        context["active_risks"] = [
            r.model_dump(mode='json')
            for r in await self.business.get_active_risks()
        ]
        
        # Get relevant metrics
        context["relevant_metrics"] = [
            m.model_dump(mode='json')
            for m in await self.business.get_relevant_metrics(query)
        ]
        
        # Get company context
        context["company_context"] = await self.business.get_company_context()
        
        return context
    
    async def get_memory_summary(self) -> Dict:
        """Get a summary of what's stored in memory"""
        return {
            "user_id": self.user_id,
            "conversational": {
                "sessions": len(self.conversational.sessions),
                "preferences": len(self.conversational.preferences),
                "conversations": len(self.conversational.vector_store.data)
            },
            "business": {
                "facts": len(self.business.vector_store.data),
                "risks": len(self.business.risks),
                "metrics": len(self.business.metrics),
                "company_context_keys": list(self.business.company_context.keys())
            }
        }

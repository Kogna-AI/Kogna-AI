"""
LangGraph State Machine for Kogna Agent Architecture.

This file is PURE ORCHESTRATION - it defines the flow, not the logic.

Flow:
1. GATE 1: Intent classification (greeting/chitchat vs data question)
2. Retrieve context (via HierarchicalRetriever)
3. GATE 2: Data sufficiency check
4. Classify query complexity (supervisor)
5. Route to specialist
6. Audit response
7. Handle reroutes if needed
8. Format final response
"""

import logging
from typing import TypedDict, Optional, Literal
from datetime import datetime

from langgraph.graph import StateGraph, END

from .supervisor import Supervisor, Category, ClassificationResult
from .specialist import Specialist, SpecialistConfig, SpecialistResponse
from .auditor import Auditor, AuditResult
from .responders import DirectResponder, DirectResponse
from .token_budget import TokenBudget, TokenUsage

# Import the hierarchical retriever
from services.hierarchical_retriever import HierarchicalRetriever

logger = logging.getLogger(__name__)


# =============================================================================
# State Definition
# =============================================================================

class AgentState(TypedDict, total=False):
    """State that flows through the agent graph."""
    # Input
    query: str
    user_id: str
    session_id: str
    team_id: str
    organization_id: str  # For KPI queries
    
    # Memory
    conversation_history: list[dict]
    
    # GATE 1: Intent Classification
    intent_type: str  # "greeting", "chitchat", "data_question", "clarification"
    query_scope: str  # "broad", "specific", "mixed" - for retrieval strategy
    
    # Retrieval
    retrieval_context: list[dict]  # Formatted for specialist
    retrieval_raw: dict            # Raw results from HierarchicalRetriever
    retrieval_strategy: str        # "hybrid", "tree_first", "vector_only"
    context_summary: str
    
    # GATE 2: Data Sufficiency
    data_sufficient: bool
    sufficiency_reason: str
    
    # Classification
    classification: Optional[ClassificationResult]
    category: str
    complexity: str
    
    # Processing
    reroute_count: int
    specialist_response: Optional[SpecialistResponse]
    
    # Audit
    audit_feedback: Optional[str]
    audit_retries: int
    
    # Token tracking
    token_usage: Optional[TokenUsage]
    
    # Output
    response: str
    sources_cited: list[str]
    confidence: float
    model_used: str
    
    # Metadata
    error: Optional[str]
    start_time: datetime
    end_time: datetime
    total_latency_ms: float
    skipped_rag: bool
    gate1_passed: bool
    gate2_passed: bool


# =============================================================================
# GATE 1: Intent Classification
# =============================================================================

GREETING_SET = {
    "hi", "hello", "hey", "yo", "howdy", "hiya", "greetings",
    "good morning", "good afternoon", "good evening",
    "hi there", "hello there", "hey there",
}

CHITCHAT_PREFIXES = [
    "how are you", "how's it going", "what's up",
    "thank you", "thanks", "appreciate",
    "bye", "goodbye", "see you", "take care",
    "who are you", "what are you", "what can you do",
    "nice to meet", "pleasure",
]

CLARIFICATION_SIGNALS = [
    "what do you mean", "can you explain", "tell me more",
    "what about", "and the", "also", "another question",
    "follow up", "following up", "regarding that", "about that",
]

# Keywords for query scope classification
BROAD_KEYWORDS = [
    'overview', 'summary', 'overall', 'generally', 'main',
    'key', 'themes', 'strategic', 'big picture', 'what are',
    'tell me about', 'explain', 'describe', 'strategy'
]

SPECIFIC_KEYWORDS = [
    'exact', 'specific', 'how much', 'when', 'who', 'where',
    'which', 'cost', 'price', 'date', 'number', 'list',
    'show me', 'find', 'what was', 'details'
]


async def classify_intent(state: AgentState) -> AgentState:
    """
    GATE 1: Classify intent before retrieval.
    Also classifies query scope (broad/specific) for retrieval strategy.
    
    Routes:
    - greeting/chitchat → respond_direct (skip RAG)
    - data_question → retrieve_context
    """
    query = state.get("query", "").strip()
    query_lower = query.lower().strip().rstrip("!?.")
    
    # Initialize state
    state["token_usage"] = state.get("token_usage") or TokenUsage()
    state["start_time"] = state.get("start_time") or datetime.now()
    state["reroute_count"] = state.get("reroute_count", 0)
    state["audit_retries"] = state.get("audit_retries", 0)
    
    # Check for greetings (exact match on short queries)
    if query_lower in GREETING_SET:
        state["intent_type"] = "greeting"
        state["skipped_rag"] = True
        state["gate1_passed"] = False
        logger.info("GATE 1: Greeting detected → skip RAG")
        return state
    
    # Check for chitchat (prefix match)
    for prefix in CHITCHAT_PREFIXES:
        if query_lower.startswith(prefix):
            state["intent_type"] = "chitchat"
            state["skipped_rag"] = True
            state["gate1_passed"] = False
            logger.info("GATE 1: Chitchat detected → skip RAG")
            return state
    
    # Check for clarification (needs conversation history)
    if state.get("conversation_history"):
        for signal in CLARIFICATION_SIGNALS:
            if signal in query_lower:
                state["intent_type"] = "clarification"
                state["skipped_rag"] = False
                state["gate1_passed"] = True
                state["query_scope"] = "specific"  # Clarifications are usually specific
                logger.info("GATE 1: Clarification detected → proceed with RAG")
                return state
    
    # Default: data question - also classify scope
    state["intent_type"] = "data_question"
    state["skipped_rag"] = False
    state["gate1_passed"] = True
    
    # Classify query scope for retrieval strategy
    broad_count = sum(1 for kw in BROAD_KEYWORDS if kw in query_lower)
    specific_count = sum(1 for kw in SPECIFIC_KEYWORDS if kw in query_lower)
    
    if broad_count > specific_count:
        state["query_scope"] = "broad"
    elif specific_count > broad_count:
        state["query_scope"] = "specific"
    else:
        state["query_scope"] = "mixed"
    
    logger.info(f"GATE 1: Data question (scope={state['query_scope']}) → proceed with RAG")
    return state


def route_after_intent(state: AgentState) -> str:
    """Route based on GATE 1 result."""
    intent = state.get("intent_type", "data_question")
    if intent in ("greeting", "chitchat"):
        return "respond_direct"
    return "retrieve_context"


async def respond_direct(state: AgentState) -> AgentState:
    """Handle greeting/chitchat responses via DirectResponder."""
    responder = DirectResponder()
    intent = state.get("intent_type", "greeting")
    query = state.get("query", "")
    
    if intent == "greeting":
        result = await responder.greeting(query)
    else:
        result = await responder.chitchat(query)
    
    state["response"] = result.content
    state["confidence"] = result.confidence
    state["model_used"] = result.model_used
    state["sources_cited"] = []
    
    _finalize_state(state)
    return state


# =============================================================================
# Retrieval (HierarchicalRetriever Integration)
# =============================================================================

async def retrieve_context(state: AgentState) -> AgentState:
    """
    Retrieve relevant context using HierarchicalRetriever.
    
    Strategy based on query scope:
    - broad: tree_first (high-level overview)
    - specific: hybrid (detailed information)
    - mixed: hybrid (comprehensive search)
    """
    logger.info("Retrieving context via HierarchicalRetriever")
    
    user_id = state.get("user_id")
    query = state.get("query", "")
    query_scope = state.get("query_scope", "mixed")
    
    if not user_id:
        logger.error("No user_id provided for retrieval")
        state["retrieval_context"] = []
        state["context_summary"] = "No user_id for retrieval"
        return state
    
    try:
        # Initialize retriever
        retriever = HierarchicalRetriever(user_id)
        
        # Determine strategy based on scope
        if query_scope == "broad":
            strategy = "tree_first"
            max_results = 5
        else:
            strategy = "hybrid"
            max_results = 10
        
        logger.info(f"Retrieval: strategy={strategy}, max_results={max_results}")
        
        # Execute retrieval
        retrieval_result = await retriever.retrieve(
            query=query,
            max_results=max_results,
            strategy=strategy
        )
        
        # Store raw results
        state["retrieval_raw"] = retrieval_result
        state["retrieval_strategy"] = retrieval_result.get("strategy_used", strategy)
        
        # Format results for specialist
        formatted_context = _format_retrieval_for_specialist(retrieval_result)
        state["retrieval_context"] = formatted_context
        
        # Generate summary
        state["context_summary"] = _generate_context_summary(retrieval_result)
        
        logger.info(f"Retrieved {len(formatted_context)} chunks via {state['retrieval_strategy']}")
        
    except Exception as e:
        logger.error(f"Retrieval failed: {e}", exc_info=True)
        state["retrieval_context"] = []
        state["retrieval_raw"] = {}
        state["context_summary"] = f"Retrieval error: {str(e)[:100]}"
    
    return state


def _format_retrieval_for_specialist(retrieval_result: dict) -> list[dict]:
    """
    Convert HierarchicalRetriever results to specialist format.
    
    From retriever:
        - summary: str
        - similarity: float
        - final_score: float (if hybrid)
        - title: str
        - file_path: str (for leaf notes)
        - level: int (99=root, 2=theme, 1=topic, 0=leaf)
        
    To specialist:
        - content: str
        - score: float
        - source_path: str
        - level: int
        - title: str
    """
    results = retrieval_result.get("results", [])
    formatted = []
    
    for result in results:
        # Get content (summary is the main content from notes)
        content = result.get("summary", "")
        
        # Add key_facts if available
        key_facts = result.get("key_facts", [])
        if key_facts:
            facts_str = "\n".join(f"• {fact}" for fact in key_facts[:5])
            content = f"{content}\n\nKey Facts:\n{facts_str}"
        
        # Get score (prefer final_score from hybrid, fallback to similarity)
        score = result.get("final_score", result.get("similarity", 0.0))
        
        # Get source path
        source_path = result.get("file_path") or result.get("title", "Unknown")
        
        # Get level for context
        level = result.get("level", 0)
        level_label = _get_level_label(level)
        
        formatted.append({
            "content": content,
            "score": score,
            "source_path": source_path,
            "title": result.get("title", "Untitled"),
            "level": level,
            "level_label": level_label,
            "source_type": result.get("source", "unknown"),  # 'super_note' or 'leaf_note'
            "topics": result.get("topics", []),
            # Keep parent context if enriched
            "parent_context": result.get("parent_context"),
        })
    
    return formatted


def _get_level_label(level: int) -> str:
    """Get human-readable label for tree level."""
    labels = {
        99: "Overview",
        2: "Theme",
        1: "Topic",
        0: "Detail",
    }
    return labels.get(level, f"Level {level}")


def _generate_context_summary(retrieval_result: dict) -> str:
    """Generate a brief summary of retrieved context for supervisor."""
    results = retrieval_result.get("results", [])
    strategy = retrieval_result.get("strategy_used", "unknown")
    levels = retrieval_result.get("levels_searched", [])
    
    if not results:
        return "No context retrieved"
    
    # Count by level
    level_counts = {}
    titles = []
    
    for r in results[:10]:
        level = r.get("level", 0)
        level_label = _get_level_label(level)
        level_counts[level_label] = level_counts.get(level_label, 0) + 1
        
        title = r.get("title", "")
        if title and title not in titles:
            titles.append(title)
    
    # Build summary
    parts = [f"Strategy: {strategy}"]
    parts.append(f"Results: {len(results)}")
    
    level_str = ", ".join(f"{k}: {v}" for k, v in level_counts.items())
    parts.append(f"Levels: {level_str}")
    
    if titles:
        parts.append(f"Sources: {', '.join(titles[:5])}")
    
    return " | ".join(parts)


# =============================================================================
# GATE 2: Data Sufficiency
# =============================================================================

async def check_data_sufficiency(state: AgentState) -> AgentState:
    """
    GATE 2: Check if retrieved data is sufficient.
    
    Routes:
    - insufficient → respond_no_data
    - sufficient → classify_query
    """
    context = state.get("retrieval_context", [])
    
    # No context
    if not context:
        state["data_sufficient"] = False
        state["sufficiency_reason"] = "no_context_retrieved"
        state["gate2_passed"] = False
        logger.info("GATE 2: No context → insufficient")
        return state
    
    # Check relevance scores
    scores = [c.get("score", 0) for c in context]
    
    if scores:
        max_score = max(scores)
        avg_score = sum(scores) / len(scores)
        
        # Very low relevance
        if max_score < 0.3:
            state["data_sufficient"] = False
            state["sufficiency_reason"] = f"low_relevance_score (max={max_score:.2f})"
            state["gate2_passed"] = False
            logger.info(f"GATE 2: Low relevance ({max_score:.2f}) → insufficient")
            return state
    
    # Check content length
    total_content = sum(len(c.get("content", "")) for c in context[:5])
    if total_content < 50:
        state["data_sufficient"] = False
        state["sufficiency_reason"] = "insufficient_content"
        state["gate2_passed"] = False
        logger.info("GATE 2: Content too short → insufficient")
        return state
    
    # Passed
    state["data_sufficient"] = True
    state["sufficiency_reason"] = "sufficient"
    state["gate2_passed"] = True
    logger.info(f"GATE 2: Sufficient ({len(context)} chunks, max_score={max(scores):.2f})")
    return state


def route_after_sufficiency(state: AgentState) -> str:
    """Route based on GATE 2 result."""
    if state.get("data_sufficient", False):
        return "classify_query"
    return "respond_no_data"


async def respond_no_data(state: AgentState) -> AgentState:
    """Handle insufficient data via DirectResponder."""
    responder = DirectResponder()
    
    result = await responder.no_data(
        query=state.get("query", ""),
        reason=state.get("sufficiency_reason", "unknown"),
        context=state.get("retrieval_context", []),
    )
    
    state["response"] = result.content
    state["confidence"] = result.confidence
    state["model_used"] = result.model_used
    state["sources_cited"] = []
    
    _finalize_state(state)
    return state


# =============================================================================
# Classification (Supervisor)
# =============================================================================

async def classify_query(state: AgentState) -> AgentState:
    """Classify query to determine specialist routing."""
    supervisor = Supervisor()
    
    result = await supervisor.classify(
        query=state["query"],
        context_summary=state.get("context_summary", ""),
        conversation_history=state.get("conversation_history"),
        token_usage=state.get("token_usage"),
        user_id=state.get("user_id"),
    )
    
    state["classification"] = result
    state["category"] = result.category.value
    state["complexity"] = result.complexity
    
    logger.info(f"Classified: {result.category.value} ({result.complexity})")
    return state


# =============================================================================
# Specialist
# =============================================================================

async def run_specialist(state: AgentState) -> AgentState:
    """Run the specialist agent."""
    specialist = Specialist()
    
    config = SpecialistConfig(
        category=state.get("category", "GENERAL"),
        complexity=state.get("complexity", "medium"),
    )
    
    response = await specialist.process(
        query=state["query"],
        context=state.get("retrieval_context", []),
        config=config,
        user_id=state.get("user_id"),
        conversation_history=state.get("conversation_history"),
        token_budget=TokenBudget(),
        token_usage=state.get("token_usage") or TokenUsage(),
        audit_feedback=state.get("audit_feedback"),
    )
    
    state["specialist_response"] = response
    state["model_used"] = response.model_used
    
    logger.info(f"Specialist: {response.model_used}, confidence={response.confidence:.0%}")
    return state


# =============================================================================
# Audit
# =============================================================================

async def audit_response(state: AgentState) -> AgentState:
    """Run the auditor on specialist response."""
    response = state.get("specialist_response")
    retries = state.get("audit_retries", 0)
    
    # Skip if max retries or low confidence
    if retries >= 1 or not response or response.confidence < 0.2:
        state["audit_feedback"] = None
        return state
    
    auditor = Auditor()
    result = await auditor.audit(
        query=state["query"],
        response_content=response.content,
        context=state.get("retrieval_context", []),
    )
    
    if not result.approved:
        state["audit_feedback"] = result.critique
        state["audit_retries"] = retries + 1
        logger.warning(f"Audit FAILED: {result.critique}")
    else:
        state["audit_feedback"] = None
        logger.info("Audit PASSED")
    
    return state


def check_audit_status(state: AgentState) -> Literal["retry", "finish"]:
    """Route based on audit result."""
    return "retry" if state.get("audit_feedback") else "finish"


# =============================================================================
# Confidence & Rerouting
# =============================================================================

async def check_confidence(state: AgentState) -> AgentState:
    """Check confidence for rerouting decision."""
    if not state.get("specialist_response"):
        state["error"] = "No specialist response"
    return state


def check_or_reroute(state: AgentState) -> Literal["accept", "reroute", "fallback"]:
    """Decide: accept, reroute, or fallback."""
    response = state.get("specialist_response")
    reroute_count = state.get("reroute_count", 0)
    
    if not response:
        return "fallback"
    if response.confidence >= 0.3 and not response.needs_reroute:
        return "accept"
    if reroute_count >= 1:
        return "fallback"
    return "reroute"


async def prepare_reroute(state: AgentState) -> AgentState:
    """Prepare for rerouting to different specialist."""
    response = state.get("specialist_response")
    original = state.get("category", "GENERAL")
    
    state["reroute_count"] = state.get("reroute_count", 0) + 1
    
    if response and response.reroute_suggestion:
        new_category = response.reroute_suggestion
    else:
        supervisor = Supervisor()
        decision = await supervisor.decide_reroute(
            query=state["query"],
            original_category=Category(original),
            specialist_confidence=response.confidence if response else 0.0,
            specialist_feedback=response.content[:500] if response else "",
            reroute_count=state["reroute_count"],
            token_usage=state.get("token_usage"),
            user_id=state.get("user_id"),
        )
        new_category = decision.new_category.value if decision.new_category else "GENERAL"
    
    state["category"] = "GENERAL" if new_category == original else new_category
    logger.info(f"Rerouting: {original} → {state['category']}")
    return state


async def fallback_to_general(state: AgentState) -> AgentState:
    """Fallback to GENERAL specialist."""
    state["category"] = "GENERAL"
    state["complexity"] = "medium"
    logger.info("Falling back to GENERAL")
    return state


# =============================================================================
# Response Formatting
# =============================================================================

async def format_response(state: AgentState) -> AgentState:
    """Format final response from specialist."""
    response = state.get("specialist_response")
    
    if response:
        state["response"] = response.content
        state["sources_cited"] = response.sources_cited
        state["confidence"] = response.confidence
    elif state.get("error"):
        state["response"] = f"I encountered an issue: {state['error']}"
        state["confidence"] = 0.0
        state["sources_cited"] = []
    else:
        state["response"] = "I couldn't generate a response."
        state["confidence"] = 0.0
        state["sources_cited"] = []
    
    _finalize_state(state)
    return state


# =============================================================================
# Helpers
# =============================================================================

def _finalize_state(state: AgentState) -> None:
    """Add timing metadata to state."""
    state["end_time"] = datetime.now()
    if "start_time" in state:
        latency = (state["end_time"] - state["start_time"]).total_seconds() * 1000
        state["total_latency_ms"] = latency
        logger.info(f"Total latency: {latency:.0f}ms")


# =============================================================================
# Graph Builder
# =============================================================================

def build_agent_graph() -> StateGraph:
    """
    Build the agent orchestration graph.
    
    ┌─────────────────────────────────────────────────────────────┐
    │  GATE 1: classify_intent                                    │
    │    ├── greeting/chitchat → respond_direct → END             │
    │    └── data_question → retrieve_context                     │
    │                              ↓                              │
    │                    (HierarchicalRetriever)                  │
    │                              ↓                              │
    │                    GATE 2: check_data_sufficiency           │
    │                      ├── insufficient → respond_no_data → END│
    │                      └── sufficient → classify_query        │
    │                                            ↓                │
    │                                        specialist           │
    │                                            ↓                │
    │                                      audit_response         │
    │                                            ↓                │
    │                                     check_confidence        │
    │                                       ├── accept → END      │
    │                                       ├── reroute → loop    │
    │                                       └── fallback → loop   │
    └─────────────────────────────────────────────────────────────┘
    """
    graph = StateGraph(AgentState)
    
    # Nodes
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("respond_direct", respond_direct)
    graph.add_node("retrieve_context", retrieve_context)
    graph.add_node("check_data_sufficiency", check_data_sufficiency)
    graph.add_node("respond_no_data", respond_no_data)
    graph.add_node("classify_query", classify_query)
    graph.add_node("specialist", run_specialist)
    graph.add_node("audit_response", audit_response)
    graph.add_node("check_confidence", check_confidence)
    graph.add_node("prepare_reroute", prepare_reroute)
    graph.add_node("fallback_to_general", fallback_to_general)
    graph.add_node("format_response", format_response)
    
    # Entry
    graph.set_entry_point("classify_intent")
    
    # GATE 1
    graph.add_conditional_edges(
        "classify_intent",
        route_after_intent,
        {"respond_direct": "respond_direct", "retrieve_context": "retrieve_context"}
    )
    graph.add_edge("respond_direct", END)
    
    # Retrieval → GATE 2
    graph.add_edge("retrieve_context", "check_data_sufficiency")
    graph.add_conditional_edges(
        "check_data_sufficiency",
        route_after_sufficiency,
        {"respond_no_data": "respond_no_data", "classify_query": "classify_query"}
    )
    graph.add_edge("respond_no_data", END)
    
    # Classification → Specialist
    graph.add_edge("classify_query", "specialist")
    
    # Specialist → Audit → Confidence
    graph.add_edge("specialist", "audit_response")
    graph.add_conditional_edges(
        "audit_response",
        check_audit_status,
        {"retry": "specialist", "finish": "check_confidence"}
    )
    graph.add_conditional_edges(
        "check_confidence",
        check_or_reroute,
        {"accept": "format_response", "reroute": "prepare_reroute", "fallback": "fallback_to_general"}
    )
    
    # Reroute loops
    graph.add_edge("prepare_reroute", "specialist")
    graph.add_edge("fallback_to_general", "specialist")
    
    # Exits
    graph.add_edge("format_response", END)
    
    return graph.compile()


# =============================================================================
# Main Interface
# =============================================================================

class KognaAgent:
    """
    Main interface for the Kogna agent.
    
    Usage:
        agent = KognaAgent()
        result = await agent.run(
            query="What was our Q3 revenue?",
            user_id="user_123",
        )
        print(result["response"])
    """
    
    def __init__(self):
        self._graph = None
    
    @property
    def graph(self) -> StateGraph:
        if self._graph is None:
            self._graph = build_agent_graph()
        return self._graph
    
    async def run(
        self,
        query: str,
        user_id: str,
        session_id: Optional[str] = None,
        team_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        conversation_history: Optional[list[dict]] = None,
    ) -> AgentState:
        """Run the agent on a query."""
        initial_state: AgentState = {
            "query": query,
            "user_id": user_id,
            "team_id": team_id or "",
            "organization_id": organization_id or "",
            "session_id": session_id or f"session_{datetime.now().timestamp()}",
            "conversation_history": conversation_history or [],
            "reroute_count": 0,
            "audit_retries": 0,
        }
        
        return await self.graph.ainvoke(initial_state)
    
    async def chat(
        self,
        query: str,
        user_id: str,
        session_id: Optional[str] = None,
    ) -> str:
        """Simple interface returning just the response text."""
        result = await self.run(query=query, user_id=user_id, session_id=session_id)
        return result.get("response", "I couldn't generate a response.")


# =============================================================================
# Convenience Functions
# =============================================================================

async def run_agent(
    query: str,
    user_id: str,
    session_id: Optional[str] = None,
    organization_id: Optional[str] = None,
) -> AgentState:
    """Convenience function to run the agent."""
    agent = KognaAgent()
    return await agent.run(
        query=query,
        user_id=user_id,
        session_id=session_id,
        organization_id=organization_id,
    )


def get_compiled_app():
    """
    Returns compiled graph for use in chat.py
    Compatible with old Orchestrator interface.
    """
    return build_agent_graph()
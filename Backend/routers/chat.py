"""
Chat Router - Kogna AI v2.1

Handles:
- Session management (create, list, history)
- Message persistence
- Agent execution via KognaAgent (with integrated HierarchicalRetriever)
- Step-by-step tracing

Note: Retrieval now happens INSIDE the agent (graph.py) using HierarchicalRetriever.
      No need to pass context from here - the agent fetches it based on query scope.
"""

import json
import time
import logging
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional

# --- Supabase & Auth Dependencies ---
from supabase_connect import get_supabase_manager 
from auth.dependencies import get_backend_user_id

# --- Kogna v2.1 Agent ---
from Agents import KognaAgent, AgentState

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Initializations ---
supabase = get_supabase_manager().client
router = APIRouter(prefix="/api/chat", tags=["Chat & Agent Execution"])

# Initialize the agent once at startup
kogna_agent = KognaAgent()


# =================================================================
# Pydantic Models
# =================================================================

class ChatRunIn(BaseModel):
    """Input model for running the chat agent."""
    session_id: str = Field(..., description="The UUID of the existing conversation session.")
    user_query: str = Field(..., description="The new message from the user.")
    execution_mode: str = Field("auto", description="Agent execution mode (unused - kept for backward compatibility).")


class MessageOut(BaseModel):
    """Output model for a single message in history."""
    id: str 
    session_id: str 
    user_id: str 
    role: str 
    content: str
    created_at: str


class SessionOut(BaseModel):
    """Output model for a single chat session."""
    id: str 
    user_id: str 
    title: str
    created_at: str


class ChatRunOut(BaseModel):
    """Output model for chat run response."""
    success: bool
    session_id: str
    user_query: str
    final_report: str
    assistant_message_id: str
    # Gate results
    intent_type: Optional[str] = None
    skipped_rag: Optional[bool] = None
    gate1_passed: Optional[bool] = None
    gate2_passed: Optional[bool] = None
    # Classification
    category: Optional[str] = None
    complexity: Optional[str] = None
    # Response metadata
    model_used: Optional[str] = None
    confidence: Optional[float] = None
    latency_ms: Optional[float] = None
    sources_cited: Optional[List[str]] = None
    # Retrieval metadata
    retrieval_strategy: Optional[str] = None
    context_summary: Optional[str] = None


# =================================================================
# Supabase Persistence Helpers
# =================================================================

def save_message(session_id: str, user_id: str, sender: str, content: str) -> str:
    """Saves a single message (user or assistant) to the messages table."""
    try:
        response = supabase.table("messages") \
            .insert({
                "session_id": session_id,
                "user_id": user_id, 
                "role": sender,     
                "content": content,
            }) \
            .execute()
        
        if not response.data:
            logger.error(f"Failed to save {sender} message for session {session_id}.")
            raise HTTPException(status_code=500, detail=f"Failed to save {sender} message.")
        
        return response.data[0]['id'] 
    except Exception as e:
        logger.error(f"Database error during message save: {e}")
        raise HTTPException(status_code=500, detail=f"Database error during message save: {str(e)}")


def save_agent_trace(
    user_id: str,
    message_id: str, 
    output_data: str,
    step_number: int,
    tool_used: str = "",
    prompt_used: str = "",
    llm_model: str = ""
):
    """Saves a record of the agent's internal thought process/trace."""
    try:
        supabase.table("agent_traces") \
            .insert({
                "user_id": user_id,
                "message_id": message_id,
                "step_number": step_number,
                "prompt_used": prompt_used[:1000] if prompt_used else None,
                "tool_used": tool_used,
                "llm_model": llm_model,
                "output_data": output_data,
            }) \
            .execute()
    except Exception as e:
        logger.error(f"Failed to save agent trace: {e}")
        pass  # Don't fail the whole request if tracing fails


def get_conversation_history(session_id: str, limit: int = 10) -> List[dict]:
    """Fetch recent conversation history for context."""
    try:
        response = supabase.table("messages") \
            .select("role, content") \
            .eq("session_id", session_id) \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()
        
        # Reverse to get chronological order
        messages = response.data[::-1] if response.data else []
        return messages
    except Exception as e:
        logger.error(f"Error fetching conversation history: {e}")
        return []


# =================================================================
# API Endpoints - Session Management
# =================================================================

@router.post("/sessions", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def create_new_session(ids: dict = Depends(get_backend_user_id)):
    """Creates a new chat session for the authenticated user."""
    user_id = ids['user_id'] 
    
    try:
        response = supabase.table("sessions") \
            .insert({"user_id": user_id, "title": f"New Chat - {time.strftime('%b %d')}"}) \
            .execute()

        if not response.data:
            logger.error(f"Failed to create session for user {user_id}.")
            raise HTTPException(status_code=500, detail="Failed to create chat session.")

        session_data = response.data[0]
        logger.info(f"New session created: {session_data['id']} for user {user_id}")
        return session_data
        
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create chat session: {str(e)}")


@router.get("/sessions", response_model=List[SessionOut])
def list_user_sessions(ids: dict = Depends(get_backend_user_id)):
    """Retrieves all chat sessions belonging to the authenticated user."""
    user_id = ids['user_id']
    
    try:
        response = supabase.table("sessions") \
            .select("id, user_id, title, created_at") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .execute()
            
        return response.data
    
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list chat sessions: {str(e)}")


@router.get("/history/{session_id}", response_model=List[MessageOut])
def get_session_history(
    session_id: str,
    ids: dict = Depends(get_backend_user_id)
):
    """Retrieves the message history for a specific session."""
    user_id = ids['user_id']
    
    try:
        # Verify the session belongs to the user
        session_check = supabase.table("sessions") \
            .select("id") \
            .eq("id", session_id) \
            .eq("user_id", user_id) \
            .single() \
            .execute()
            
        if not session_check.data:
            raise HTTPException(status_code=404, detail="Session not found or access denied.")

        # Fetch the messages
        response = supabase.table("messages") \
            .select("id, session_id, user_id, role, content, created_at") \
            .eq("session_id", session_id) \
            .order("created_at", desc=False) \
            .execute()
            
        return response.data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(e)}")


# =================================================================
# Main Agent Execution Endpoint
# =================================================================

@router.post("/run", response_model=ChatRunOut)
async def run_chat_agent(
    payload: ChatRunIn, 
    ids: dict = Depends(get_backend_user_id)
):
    """
    Executes the Kogna v2.1 agent with integrated retrieval.
    
    Flow:
    1. Save user message
    2. Load conversation history
    3. Run KognaAgent:
       - Gate 1: Intent classification (skip RAG for greetings)
       - Retrieval: HierarchicalRetriever (inside agent)
       - Gate 2: Data sufficiency check
       - Supervisor: Category + complexity classification
       - Specialist: Generate response
       - Auditor: Quality check
    4. Save assistant response
    5. Save agent traces
    
    Note: Retrieval happens INSIDE the agent based on query scope.
          - Broad queries → tree_first strategy
          - Specific queries → hybrid strategy
    """
    user_id = ids['user_id']
    organization_id = ids.get('organization_id', '')
    user_query = payload.user_query
    session_id = payload.session_id 
    
    # --- 1. Save User Message ---
    try:
        user_message_id = save_message(session_id, user_id, "user", user_query)
    except HTTPException as e:
        raise HTTPException(status_code=500, detail=f"Failed to save user message: {e.detail}")
    
    # --- 2. Load Conversation History ---
    conversation_history = get_conversation_history(session_id, limit=10)
    
    # --- 3. Run Kogna Agent (Retrieval happens inside) ---
    try:
        logger.info(f"Running KognaAgent for user={user_id}, session={session_id}")
        
        result: AgentState = await kogna_agent.run(
            query=user_query,
            user_id=user_id,
            session_id=session_id,
            team_id=organization_id,
            organization_id=organization_id,
            conversation_history=conversation_history,
        )
        
        # Extract results
        final_report = result.get("response", "I couldn't generate a response.")
        
        # Gate results
        intent_type = result.get("intent_type")
        skipped_rag = result.get("skipped_rag", False)
        gate1_passed = result.get("gate1_passed")
        gate2_passed = result.get("gate2_passed")
        
        # Classification
        category = result.get("category", "GENERAL")
        complexity = result.get("complexity", "medium")
        
        # Response metadata
        model_used = result.get("model_used", "unknown")
        confidence = result.get("confidence", 0.0)
        latency_ms = result.get("total_latency_ms", 0.0)
        sources_cited = result.get("sources_cited", [])
        
        # Retrieval metadata
        retrieval_strategy = result.get("retrieval_strategy")
        context_summary = result.get("context_summary")
        
        # For tracing
        classification = result.get("classification")
        specialist_response = result.get("specialist_response")
        token_usage = result.get("token_usage")
        
        logger.info(f"Agent completed: intent={intent_type}, category={category}, latency={latency_ms:.0f}ms")
        
    except Exception as e:
        logger.error(f"Agent execution failed: {e}", exc_info=True)
        final_report = f"An error occurred while processing your request: {str(e)}"
        intent_type = "error"
        skipped_rag = False
        gate1_passed = False
        gate2_passed = False
        category = "ERROR"
        complexity = "unknown"
        model_used = "none"
        confidence = 0.0
        latency_ms = 0.0
        sources_cited = []
        retrieval_strategy = None
        context_summary = None
        classification = None
        specialist_response = None
        token_usage = None
    
    # --- 4. Save Assistant Message ---
    try:
        assistant_message_id = save_message(session_id, user_id, "assistant", final_report)
    except HTTPException as e:
        logger.error(f"Failed to save assistant message: {e}")
        assistant_message_id = "save_failed"
    
    # --- 5. Save Agent Traces ---
    try:
        # Trace 1: Gate 1 - Intent Classification
        save_agent_trace(
            user_id=user_id,
            message_id=assistant_message_id,
            step_number=1,
            tool_used="gate1_intent_classification",
            llm_model="keyword_matching",
            output_data=json.dumps({
                "intent_type": intent_type,
                "skipped_rag": skipped_rag,
                "gate1_passed": gate1_passed,
                "query_scope": result.get("query_scope"),
            }, default=str),
            prompt_used=f"Query: {user_query[:200]}"
        )
        
        # Trace 2: Retrieval (if not skipped)
        if not skipped_rag:
            save_agent_trace(
                user_id=user_id,
                message_id=assistant_message_id,
                step_number=2,
                tool_used="hierarchical_retrieval",
                llm_model="embedding",
                output_data=json.dumps({
                    "strategy": retrieval_strategy,
                    "context_summary": context_summary,
                    "gate2_passed": gate2_passed,
                    "sufficiency_reason": result.get("sufficiency_reason"),
                }, default=str),
                prompt_used=""
            )
        
        # Trace 3: Classification (if Gate 2 passed)
        if gate2_passed and classification:
            save_agent_trace(
                user_id=user_id,
                message_id=assistant_message_id,
                step_number=3,
                tool_used="supervisor_classification",
                llm_model="gpt-4o-mini",
                output_data=json.dumps({
                    "category": classification.category.value if hasattr(classification, 'category') else category,
                    "complexity": classification.complexity if hasattr(classification, 'complexity') else complexity,
                    "confidence": classification.confidence if hasattr(classification, 'confidence') else 0.0,
                    "reasoning": classification.reasoning if hasattr(classification, 'reasoning') else "",
                    "key_entities": classification.key_entities if hasattr(classification, 'key_entities') else [],
                }, default=str),
                prompt_used=""
            )
        
        # Trace 4: Specialist execution
        if specialist_response:
            save_agent_trace(
                user_id=user_id,
                message_id=assistant_message_id,
                step_number=4,
                tool_used=f"{category.lower()}_specialist",
                llm_model=model_used,
                output_data=json.dumps({
                    "confidence": specialist_response.confidence if hasattr(specialist_response, 'confidence') else confidence,
                    "sources_cited": specialist_response.sources_cited if hasattr(specialist_response, 'sources_cited') else sources_cited,
                    "needs_reroute": specialist_response.needs_reroute if hasattr(specialist_response, 'needs_reroute') else False,
                }, default=str),
                prompt_used=f"Category: {category}, Complexity: {complexity}"
            )
        
        # Trace 5: Token usage summary
        if token_usage:
            save_agent_trace(
                user_id=user_id,
                message_id=assistant_message_id,
                step_number=5,
                tool_used="token_accounting",
                llm_model="",
                output_data=json.dumps({
                    "input_tokens": token_usage.input_tokens if hasattr(token_usage, 'input_tokens') else 0,
                    "output_tokens": token_usage.output_tokens if hasattr(token_usage, 'output_tokens') else 0,
                    "total_tokens": token_usage.total if hasattr(token_usage, 'total') else 0,
                }, default=str),
                prompt_used=""
            )
            
    except Exception as e:
        logger.error(f"Failed to save agent traces: {e}")
        # Don't fail the request if tracing fails
    
    # --- 6. Return Response ---
    return ChatRunOut(
        success=True,
        session_id=session_id,
        user_query=user_query,
        final_report=final_report,
        assistant_message_id=assistant_message_id,
        # Gate results
        intent_type=intent_type,
        skipped_rag=skipped_rag,
        gate1_passed=gate1_passed,
        gate2_passed=gate2_passed,
        # Classification
        category=category,
        complexity=complexity,
        # Response metadata
        model_used=model_used,
        confidence=confidence,
        latency_ms=latency_ms,
        sources_cited=sources_cited,
        # Retrieval metadata
        retrieval_strategy=retrieval_strategy,
        context_summary=context_summary,
    )


# =================================================================
# Health Check Endpoint
# =================================================================

@router.get("/health")
async def health_check():
    """Check if the chat service is healthy."""
    return {
        "status": "healthy",
        "agent": "kogna_v2.1",
        "architecture": {
            "gate1": "intent_classification",
            "retrieval": "hierarchical_retriever",
            "gate2": "data_sufficiency",
            "supervisor": "category_complexity",
            "specialist": "domain_expert",
            "auditor": "quality_check",
        },
        "features": {
            "skip_rag_for_greetings": True,
            "query_scope_detection": True,
            "tree_based_retrieval": True,
            "dynamic_model_selection": True,
        }
    }
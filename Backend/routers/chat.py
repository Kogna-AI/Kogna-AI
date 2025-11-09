import os
import json
import uuid
import time
import logging
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# --- Supabase & Auth Dependencies ---
from supabase_connect import get_supabase_manager 
from routers.Authentication import get_backend_user_id 

# --- LangGraph Orchestrator ---
# Update this import path to match your project structure
from Ai_agents.Orchestrator import get_compiled_app 

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO)

# --- Initializations ---
supabase = get_supabase_manager().client
router = APIRouter(prefix="/api/chat", tags=["Chat & Agent Execution"])
# Compile the graph once when the server starts
compiled_agent_app = get_compiled_app() 

# =================================================================
# Pydantic Models
# =================================================================
# (Pydantic models ChatRunIn, MessageOut, SessionOut are unchanged)

class ChatRunIn(BaseModel):
    """Input model for running the chat agent."""
    session_id: str = Field(..., description="The UUID of the existing conversation session.")
    user_query: str = Field(..., description="The new message from the user.")
    execution_mode: str = Field("auto", description="Agent execution mode: 'auto' or 'micromanage'.")

class MessageOut(BaseModel):
    """Output model for a single message in history (maps to 'messages' table)."""
    id: str 
    session_id: str 
    user_id: str 
    role: str 
    content: str
    created_at: str

class SessionOut(BaseModel):
    """Output model for a single chat session (maps to 'sessions' table)."""
    id: str 
    user_id: str 
    title: str
    created_at: str

# =================================================================
# Supabase Persistence Helpers
# =================================================================

def save_message(session_id: str, user_id: str, sender: str, content: str) -> str:
    """Saves a single message (user or assistant) to the messages table."""
    try:
        # This function is correct (no .select())
        response = supabase.table("messages") \
            .insert({
                "session_id": session_id,
                "user_id": user_id, 
                "role": sender,     
                "content": content,
            }) \
            .execute()
        
        if not response.data:
            logging.error(f"Failed to save {sender} message for session {session_id}.")
            raise HTTPException(status_code=500, detail=f"Failed to save {sender} message.")
        
        return response.data[0]['id'] 
    except Exception as e:
        logging.error(f"Database error during message save: {e}")
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
        # This function is now correct (removed session_id)
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
        logging.error(f"Failed to save agent trace: {e}")
        pass # Don't fail the whole request if tracing fails


# =================================================================
# API Endpoints
# =================================================================

@router.post("/sessions", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def create_new_session(ids: dict = Depends(get_backend_user_id)):
    """Creates a new chat session for the authenticated user."""
    user_id = ids['user_id'] 
    
    try:
        # This function is now correct (no .select())
        response = supabase.table("sessions") \
            .insert({"user_id": user_id, "title": f"New Chat - {time.strftime('%b %d')}"}) \
            .execute()

        if not response.data:
            logging.error(f"Failed to create session for user {user_id}.")
            raise HTTPException(status_code=500, detail="Failed to create chat session.")

        session_data = response.data[0]
        logging.info(f"New session created: {session_data['id']} for user {user_id}")
        return session_data
        
    except Exception as e:
        logging.error(f"Error creating session: {e}")
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
        logging.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list chat sessions: {str(e)}")

@router.get("/history/{session_id}", response_model=List[MessageOut])
def get_session_history(
    session_id: str, # Must be string (UUID)
    ids: dict = Depends(get_backend_user_id)
):
    """Retrieves the message history for a specific session."""
    user_id = ids['user_id']
    
    try:
        # First, verify the session belongs to the user
        session_check = supabase.table("sessions") \
            .select("id") \
            .eq("id", session_id) \
            .eq("user_id", user_id) \
            .single() \
            .execute()
            
        if not session_check.data:
            raise HTTPException(status_code=404, detail="Session not found or access denied.")

        # Then, fetch the messages
        response = supabase.table("messages") \
            .select("id, session_id, user_id, role, content, created_at") \
            .eq("session_id", session_id) \
            .order("created_at", desc=False) \
            .execute()
            
        return response.data
    
    except HTTPException:
        raise # Re-raise 404
    except Exception as e:
        logging.error(f"Error getting session history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(e)}")

# =================================================================
# ===== AGENT EXECUTION ENDPOINT (WITH STEP-BY-STEP TRACING) =====
# =================================================================

@router.post("/run")
def run_chat_agent(
    payload: ChatRunIn, 
    ids: dict = Depends(get_backend_user_id)
):
    """
    Executes the LangGraph orchestrator. 
    Saves user message, loads history, runs agent, saves assistant reply, 
    AND saves step-by-step agent traces.
    """
    user_id = ids['user_id']
    user_query = payload.user_query
    session_id = payload.session_id 
    execution_mode = payload.execution_mode
    
    # --- 1. Save User Message ---
    try:
        user_message_id = save_message(session_id, user_id, "user", user_query)
    except HTTPException as e:
        return {"status": "error", "message": f"Failed to save user message: {e.detail}"}
    
    final_report = "An error occurred, and the workflow failed to generate a response."
    
    # =================================================================
    # ===== NEW TRACING LOGIC STARTS HERE =====
    # =================================================================
    
    # This list will store the output of each agent node
    agent_steps = [] 
    
    try:
        # --- 2. Run LangGraph Orchestrator ---
        
        initial_state = {
            "user_query": user_query,
            "session_id": session_id,
            "execution_mode": execution_mode,
            "user_id": user_id, 
            "organization_id": ids.get('organization_id'),
            "chat_history": None,
            "query_classification": None,
            "internal_analysis_report": None,
            "internal_sources": None,
            "business_research_findings": None,
            "synthesis_report": None,
            "final_report": None,
            "error_message": None,
            "human_feedback": None,
        }

        # --- MODIFIED STREAMING LOOP ---
        # We iterate through the stream and capture the output of each node
        final_state = {}
        for s in compiled_agent_app.stream(initial_state, {"recursion_limit": 50}):
            # `s` is a dictionary where the key is the node name
            # e.g., s = {"triage_node": {"query_classification": "data_request"}}
            
            # Update the full final_state
            final_state.update(s) 
            
            # Add the step to our trace list.
            # We filter out "__end__" and other internal LangGraph keys
            node_name = list(s.keys())[0]
            if not node_name.startswith("__"):
                agent_steps.append(s)

        # --- Extract the final report (unchanged) ---
        if 'communicator_node' in final_state:
            final_report = final_state['communicator_node'].get("final_report", final_report)
        elif 'answer_general_query_node' in final_state:
            final_report = final_state['answer_general_query_node'].get("final_report", final_report)
        elif 'error_handler_node' in final_state:
            final_report = final_state['error_handler_node'].get("error_message", final_report)

        # --- 3. Save Assistant Message ---
        # We MUST do this *before* saving traces to get the ID
        assistant_message_id = save_message(session_id, user_id, "assistant", final_report)
        
        # --- 4. Save STEP-BY-STEP Agent Traces ---
        for i, step_data in enumerate(agent_steps):
            # `step_data` is like {"triage_node": {...}}
            node_name = list(step_data.keys())[0]
            node_output = step_data[node_name]
            
            # Get a specific prompt if it's the triage node
            prompt = "N/A"
            if node_name == "triage_node":
                prompt = final_state.get('query_classification', 'N/A')

            save_agent_trace(
                user_id=user_id,
                message_id=assistant_message_id, # Link all steps to the same final message
                step_number=i + 1,
                tool_used=node_name, # e.g., "triage_node", "researcher_node"
                output_data=json.dumps(node_output, default=str),
                prompt_used=prompt
            )
        # =================================================================
        # ===== NEW TRACING LOGIC ENDS HERE =====
        # =================================================================

        return {
            "success": True,
            "session_id": session_id,
            "user_query": user_query,
            "final_report": final_report,
            "assistant_message_id": assistant_message_id
        }

    except Exception as e:
        logging.error(f"LangGraph execution or final save failed: {e}", exc_info=True)
        error_report = f"An unexpected error occurred while processing your request: {str(e)}"
        try:
            save_message(session_id, user_id, "assistant", error_report)
        except:
            pass 
            
        raise HTTPException(status_code=500, detail=error_report)
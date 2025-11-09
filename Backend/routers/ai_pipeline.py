# from fastapi import APIRouter, HTTPException, Depends, status
# from pydantic import BaseModel
# from typing import List, Dict, Any, Optional
# from Ai_agents.Orchestrator import get_compiled_app
# from routers.Authentication import get_current_user ,get_backend_user_id

# class AiRunPayload(BaseModel):
#     user_query: str
#     execution_mode: str = "autonomous"
#     chat_history: List[Dict[str, Any]] = []

# router = APIRouter(prefix="/api/ai", tags=["AI Orchestration"])

# @router.post("/run")
# def run_ai_workflow(
#     payload: AiRunPayload, 
#     # --- 2. Add the dependency here ---
#     ids: dict = Depends(get_backend_user_id)
#     ):

#     try:
#         # --- 3. Access the user ID ---
#         current_user_id = ids['user_id'] 
#         current_org_id = ids['organization_id']
#         print(f"AI Workflow initiated by user_id: {current_user_id} in Org: {current_org_id}")

#         user_query = payload.user_query
#         execution_mode = payload.execution_mode
#         chat_history_dicts = payload.chat_history

#         # --- STRING CONVERSION STEP (no change) ---
#         converted_chat_history_strings = []
#         for msg in chat_history_dicts:
#             role = msg.get("role")
#             content = msg.get("content")
#             if not content:
#                 continue
            
#             if role == "user":
#                 converted_chat_history_strings.append(f"Human: {content}")
#             elif role == "assistant":
#                 converted_chat_history_strings.append(f"AI: {content}")
#             elif role == "system":
#                 converted_chat_history_strings.append(f"System: {content}")

#         app = get_compiled_app()

#         initial_state = {
#             "user_query": user_query,
#             # MODIFIED: Use the new list of strings
#             "chat_history": converted_chat_history_strings,
#             "execution_mode": execution_mode,
#             "user_id": current_user_id,
#             "organization_id": current_org_id,
#             "query_classification": None,
#             "internal_analysis_report": None,
#             "internal_sources": None,
#             "business_research_findings": None,
#             "synthesis_report": None,
#             "final_report": None,
#             "error_message": None,
#             "human_feedback": None,
#         }

#         final_report = None
#         stream_error = None

#         for s in app.stream(initial_state, {"recursion_limit": 25}):
#             if "answer_general_query_node" in s:
#                 final_report = s["answer_general_query_node"].get("final_report")
#             elif "communicator_node" in s:
#                 final_report = s["communicator_node"].get("final_report")
#             elif "error_handler_node" in s:
#                 final_report = s["error_handler_node"].get("error_message")
#                 stream_error = True

#         if not final_report:
#             final_report = "Workflow completed, but no report was generated."

#         return {
#             "success": not stream_error,
#             "user_query": user_query,
#             "execution_mode": execution_mode,
#             "final_report": final_report,
#         }

#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"An unexpected internal error occurred: {str(e)}")

from fastapi import APIRouter

# This router is now reserved for future AI-specific tasks 
# (e.g., model status checks, batch processing) but no longer handles
# the main chat execution, which has moved to /api/chat/run.

router = APIRouter(prefix="/api/ai", tags=["AI Orchestration"])

@router.get("/status")
def get_ai_status():
    """Simple status check for the AI services."""
    return {"status": "ok", "message": "AI services are running. Chat execution is at /api/chat/run."}
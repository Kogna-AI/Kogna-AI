from fastapi import APIRouter, HTTPException
from Ai_agents.Orchestrator import get_compiled_app
# REMOVED: No more langchain_core imports needed here

router = APIRouter(prefix="/api/ai", tags=["AI Orchestration"])

@router.post("/run")
def run_ai_workflow(request: dict):
    """
    Run the compiled Kogna AI orchestration pipeline once (non-interactive).
    """
    try:
        user_query = request.get("user_query")
        if not user_query:
            raise HTTPException(status_code=400, detail="Missing 'user_query' field")

        execution_mode = request.get("execution_mode", "autonomous")
        chat_history_dicts = request.get("chat_history", [])

        # --- NEW: STRING CONVERSION STEP ---
        # Convert the list of dicts into a list of formatted strings
        converted_chat_history_strings = []
        for msg in chat_history_dicts:
            role = msg.get("role")
            content = msg.get("content")
            if not content:
                continue
            
            # Format as simple, human-readable strings
            if role == "user":
                converted_chat_history_strings.append(f"Human: {content}")
            elif role == "assistant":
                converted_chat_history_strings.append(f"AI: {content}")
            elif role == "system":
                converted_chat_history_strings.append(f"System: {content}")
        # --- END OF NEW STEP ---

        app = get_compiled_app()

        initial_state = {
            "user_query": user_query,
            # MODIFIED: Use the new list of strings
            "chat_history": converted_chat_history_strings,
            "execution_mode": execution_mode,
            "query_classification": None,
            "internal_analysis_report": None,
            "internal_sources": None,
            "business_research_findings": None,
            "synthesis_report": None,
            "final_report": None,
            "error_message": None,
            "human_feedback": None,
        }

        final_report = None
        stream_error = None

        for s in app.stream(initial_state, {"recursion_limit": 25}):
            if "answer_general_query_node" in s:
                final_report = s["answer_general_query_node"].get("final_report")
            elif "communicator_node" in s:
                final_report = s["communicator_node"].get("final_report")
            elif "error_handler_node" in s:
                final_report = s["error_handler_node"].get("error_message")
                stream_error = True

        if not final_report:
            final_report = "Workflow completed, but no report was generated."

        return {
            "success": not stream_error,
            "user_query": user_query,
            "execution_mode": execution_mode,
            "final_report": final_report,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected internal error occurred: {str(e)}")
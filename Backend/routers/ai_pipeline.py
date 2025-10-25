from fastapi import APIRouter, HTTPException
from Ai_agents.Orchestrator import get_compiled_app

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
        chat_history = request.get("chat_history", [])

        app = get_compiled_app()

        initial_state = {
            "user_query": user_query,
            "chat_history": chat_history,
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
            # capture whichever node returns the answer
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

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



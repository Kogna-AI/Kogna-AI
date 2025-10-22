from fastapi import APIRouter, HTTPException
from Ai_agents.Orchestrator import run_full_pipeline
router = APIRouter(prefix="/api/ai", tags=["AI Orchestration"])

@router.post("/run")
def run_ai_workflow(request: dict):
    """
    Trigger the AI multi-agent workflow from API.
    """
    try:
        execution_mode = request.get("execution_mode", "autonomous")
        user_query = request.get("user_query", "Generate analysis summary")
        result = run_full_pipeline(execution_mode, user_query)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




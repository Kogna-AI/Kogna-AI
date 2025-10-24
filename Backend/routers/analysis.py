from fastapi import APIRouter, HTTPException
from core.models import AIAnalysisRequest
from services.ai_analysis import run_ai_analysis

router = APIRouter(prefix="/api/analysis", tags=["AI Analysis"])

@router.post("")
def analyze(req: AIAnalysisRequest):

    #kick off run_ai_analysis from services
    result = run_ai_analysis(req.organization_id, req.analysis_type, req.parameters or {})
    if not result.get("success", True):
        raise HTTPException(status_code=500, detail=result.get("error", "AI analysis failed"))
    return {"success": True, "analysis_type": req.analysis_type, "result": result}

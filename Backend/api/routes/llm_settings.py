from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from Ai_agents.llm_factory import (
    list_available_models,
    DEFAULT_AGENT_MODELS,
    get_user_model_preferences,
    save_user_model_preference,
    SUPPORTED_MODELS,
)

router = APIRouter(prefix="/api/settings/llm", tags=["LLM Settings"])


class ModelPreferenceRequest(BaseModel):
    agent_name: str
    model_name: str


@router.get("/available-models")
async def get_available_models():
    """
    List all models available (with valid API keys).

    Response:
    {
      "available": {
        "gpt-4o-mini": {"provider": "openai", "cost_tier": "low", ...},
        ...
      },
      "all_supported": ["gpt-4o", "gpt-4o-mini", "claude-sonnet", ...]
    }
    """
    result = list_available_models()
    return {
        "available": result["available"],
        "all_supported": result["all_supported"],
        "missing_keys": result.get("missing_keys", []),
    }


@router.get("/agent-defaults")
async def get_agent_defaults():
    """
    Get default model for each agent.

    Response:
    {
      "triage_agent": "gpt-4o-mini",
      "internal_analyst": "gpt-4o",
      ...
    }
    """
    return DEFAULT_AGENT_MODELS


@router.get("/preferences/{user_id}")
async def get_preferences(user_id: str):
    """
    Get user's current model preferences.

    Response:
    {
      "user_id": "user_123",
      "preferences": {"internal_analyst": "claude-sonnet"},
      "defaults": {...}
    }
    """
    preferences = get_user_model_preferences(user_id)
    return {
        "user_id": user_id,
        "preferences": preferences,
        "defaults": DEFAULT_AGENT_MODELS,
    }


@router.post("/preferences/{user_id}")
async def set_preference(user_id: str, request: ModelPreferenceRequest):
    """
    Set user's model preference for an agent.

    Request body:
    {
      "agent_name": "internal_analyst",
      "model_name": "claude-sonnet"
    }

    Response:
    {
      "status": "saved",
      "user_id": "user_123",
      "agent_name": "internal_analyst",
      "model_name": "claude-sonnet"
    }
    """
    if request.model_name not in SUPPORTED_MODELS:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_model",
                "message": f"Model '{request.model_name}' is not supported.",
                "supported_models": list(SUPPORTED_MODELS.keys()),
            },
        )
    try:
        ok = save_user_model_preference(user_id, request.agent_name, request.model_name)
        if not ok:
            raise HTTPException(
                status_code=500,
                detail="Failed to save preference.",
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "status": "saved",
        "user_id": user_id,
        "agent_name": request.agent_name,
        "model_name": request.model_name,
    }

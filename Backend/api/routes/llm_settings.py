from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

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
    pass


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
    pass


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
    pass


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
    pass

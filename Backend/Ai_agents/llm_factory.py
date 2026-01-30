import os
import logging
from typing import Optional, Dict, Any, List
from langchain_community.chat_models import ChatLiteLLM

logger = logging.getLogger(__name__)


SUPPORTED_MODELS = {
    # OpenAI Models
    "gpt-4o": {
        "provider": "openai",
        "model_string": "gpt-4o",
        "env_key": "OPENAI_API_KEY",
        "default_temperature": 0.3,
        "capabilities": ["reasoning", "coding", "analysis"],
        "cost_tier": "high"
    },
    "gpt-4o-mini": {
        "provider": "openai",
        "model_string": "gpt-4o-mini",
        "env_key": "OPENAI_API_KEY",
        "default_temperature": 0.3,
        "capabilities": ["reasoning", "coding", "analysis"],
        "cost_tier": "low"
    },
    
    # Anthropic Models
    "claude-sonnet": {
        "provider": "anthropic",
        "model_string": "claude-sonnet-4-20250514",
        "env_key": "ANTHROPIC_API_KEY",
        "default_temperature": 0.3,
        "capabilities": ["reasoning", "coding", "analysis", "long_context"],
        "cost_tier": "medium"
    },
    "claude-haiku": {
        "provider": "anthropic",
        "model_string": "claude-3-haiku-20240307",
        "env_key": "ANTHROPIC_API_KEY",
        "default_temperature": 0.3,
        "capabilities": ["fast_response", "simple_tasks"],
        "cost_tier": "low"
    },
    
    # Google Models
    "gemini-flash": {
        "provider": "google",
        "model_string": "gemini/gemini-2.0-flash-exp",
        "env_key": "GOOGLE_API_KEY",
        "default_temperature": 0.3,
        "capabilities": ["reasoning", "fast_response"],
        "cost_tier": "low"
    },
    "gemini-pro": {
        "provider": "google",
        "model_string": "gemini/gemini-1.5-pro",
        "env_key": "GOOGLE_API_KEY",
        "default_temperature": 0.3,
        "capabilities": ["reasoning", "long_context"],
        "cost_tier": "medium"
    },
}


DEFAULT_AGENT_MODELS = {
 "triage_agent": "gpt-4o-mini", # Fast, simple classification
 "internal_analyst": "gpt-4o", # Needs good reasoning
 "research_agent": "gpt-4o-mini", # Web search synthesis
 "synthesizer": "claude-sonnet", # Best at synthesis
 "communicator": "gpt-4o-mini", # Formatting, fast
 "note_generator": "gemini-flash", # Bulk processing, cost-effective
 "super_note_generator": "gemini-flash" # Bulk processing, cost-effective
}


def get_user_model_preferences(user_id: str) -> Dict[str, str]:
    """
    Fetch user's model preferences from database.
    
    Args:
        user_id: User identifier
    
    Returns:
        Dict mapping agent_name -> model_name
        Example: {"internal_analyst": "claude-sonnet", "communicator": "gpt-4o-mini"}
    
    Note:
        Currently returns empty dict (uses defaults).
        TODO: Implement database lookup when persistence layer is ready.
    """
    # TODO: Implement database lookup
    # For now, return empty dict (use defaults)
    try:
        return {}
    except Exception as e:
        logger.warning(f"Failed to fetch user preferences for {user_id}: {e}")
        return {}




def save_user_model_preference(user_id: str, agent_name: str, model_name: str) -> bool:
    """
    Save user's model preference for an agent.
    
    Args:
        user_id: User identifier
        agent_name: Name of the agent
        model_name: Name of the model
    
    Returns:
        True if saved successfully
    
    Raises:
        ValueError: If model_name is not in SUPPORTED_MODELS
    """
    if model_name not in SUPPORTED_MODELS:
        raise ValueError(
            f"Invalid model name: {model_name}. "
            f"Supported models: {list(SUPPORTED_MODELS.keys())}"
        )
    
    try:
        logger.info(
            f"Saved preference: user={user_id}, agent={agent_name}, "
            f"model={model_name}"
        )
        return True
    except Exception as e:
        logger.error(
            f"Failed to save preference for {user_id}/{agent_name}: {e}"
        )
        return False
    


def list_available_models() -> Dict[str, Any]:
    """
    List all models that have valid API keys configured.
    """
    available = {}
    missing_keys = set()
    
    for model_name, config in SUPPORTED_MODELS.items():
        env_key = config["env_key"]
        api_key = os.getenv(env_key)
        
        # Check if API key exists and is not empty
        if api_key is not None and api_key.strip() != "":
            available[model_name] = config.copy()
        else:
            missing_keys.add(env_key)
    
    return {
        "available": available,
        "all_supported": list(SUPPORTED_MODELS.keys()),
        "missing_keys": sorted(list(missing_keys))
    }



def _is_model_available(model_name: str) -> bool:
    """Return True if model is in SUPPORTED_MODELS and its API key is configured."""
    if model_name not in SUPPORTED_MODELS:
        return False
    env_key = SUPPORTED_MODELS[model_name]["env_key"]
    api_key = os.getenv(env_key)
    return api_key is not None and api_key.strip() != ""


def get_model_for_capability(capability: str, cost_preference: str = "low") -> Optional[str]:
    """
    Find the best available model for a specific capability.

    Args:
    capability: e.g., "reasoning", "coding", "long_context"
    cost_preference: "low", "medium", or "high"
    """
    cost_priority = {
        "low": ["low", "medium", "high"],
        "medium": ["medium", "low", "high"],
        "high": ["high", "medium", "low"]
    }
    
    priority_order = cost_priority.get(cost_preference, ["low", "medium", "high"])
    
    # Find models with the capability, grouped by cost tier
    candidates_by_tier = {tier: [] for tier in ["low", "medium", "high"]}
    
    for model_name, config in SUPPORTED_MODELS.items():
        if capability in config.get("capabilities", []):
            if _is_model_available(model_name):
                tier = config.get("cost_tier", "medium")
                candidates_by_tier[tier].append(model_name)
    
    # Return first available model in priority order
    for tier in priority_order:
        if candidates_by_tier[tier]:
            return candidates_by_tier[tier][0]
    
    return None



def get_llm_for_agent(agent_name: str, user_id: Optional[str] = None, fallback_model: Optional[str] = None,
                      temperature_override: Optional[float] = None) -> ChatLiteLLM:
    """
    Get configured LLM instance for an agent.

    Priority order:
    1. User preference (if user_id provided and preference exists)
    2. Default for this agent
    3. Fallback model (if provided)
    4. Global default (gpt-4o-mini)

    Args:
        agent_name: Name of the agent requesting LLM
        user_id: Optional user ID for personalized preferences
        fallback_model: Optional fallback if preferred model unavailable
        temperature_override: Optional temperature override

    Returns:
        Configured ChatLiteLLM instance

    Raises:
        ValueError: If no valid model can be configured (no API keys)
    """
    # Resolve model name in priority order
    user_prefs = get_user_model_preferences(user_id) if user_id else {}
    candidates: List[Optional[str]] = [
        user_prefs.get(agent_name),
        DEFAULT_AGENT_MODELS.get(agent_name),
        fallback_model,
        "gpt-4o-mini",
    ]

    chosen_model: Optional[str] = None
    for candidate in candidates:
        if candidate and candidate in SUPPORTED_MODELS and _is_model_available(candidate):
            chosen_model = candidate
            break

    if chosen_model is None:
        raise ValueError(
            f"No available LLM for agent '{agent_name}'. "
            "Ensure at least one supported model has its API key set (e.g. OPENAI_API_KEY)."
        )

    config = SUPPORTED_MODELS[chosen_model]
    temperature = (
        temperature_override
        if temperature_override is not None
        else config.get("default_temperature", 0.3)
    )
    api_key = os.getenv(config["env_key"])

    return ChatLiteLLM(
        model=config["model_string"],
        api_key=api_key,
        temperature=temperature,
    )
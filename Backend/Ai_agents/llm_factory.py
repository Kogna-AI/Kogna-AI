"""
LLM Factory - OpenAI Only

Simplified model configuration using only OpenAI models.
Single provider = one API key, one bill, simpler debugging.

Models:
- gpt-4o-mini: Fast, cheap ($0.15/1M in, $0.60/1M out) — 60% of queries
- gpt-4o: Balanced quality ($2.50/1M in, $10/1M out) — 40% of queries
"""

import os
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


# =============================================================================
# Model Configuration (OpenAI Only)
# =============================================================================

SUPPORTED_MODELS = {
    "gpt-4o-mini": {
        "provider": "openai",
        "model_string": "gpt-4o-mini",
        "default_temperature": 0.3,
        "capabilities": ["reasoning", "coding", "analysis", "function_calling", "fast_response", "json_mode"],
        "cost_tier": "low",
        "cost_per_1k_input": 0.00015,
        "cost_per_1k_output": 0.0006,
        "context_window": 128000,
    },
    "gpt-4o": {
        "provider": "openai",
        "model_string": "gpt-4o",
        "default_temperature": 0.3,
        "capabilities": ["reasoning", "coding", "analysis", "function_calling", "json_mode", "vision"],
        "cost_tier": "high",
        "cost_per_1k_input": 0.0025,
        "cost_per_1k_output": 0.01,
        "context_window": 128000,
    },
}


# =============================================================================
# Default Agent Model Assignments
# =============================================================================

DEFAULT_AGENT_MODELS = {
    # ----- Legacy CrewAI Agents -----
    "triage_agent": "gpt-4o-mini",
    "internal_analyst": "gpt-4o",
    "research_agent": "gpt-4o-mini",
    "synthesizer": "gpt-4o",           # Was claude-sonnet
    "communicator": "gpt-4o-mini",
    "note_generator": "gpt-4o-mini",   # Was gemini-flash
    "super_note_generator": "gpt-4o-mini",
    
    # ----- v2.1 LangGraph Agents -----
    "supervisor": "gpt-4o-mini",        # Fast classification
    
    # Specialists by domain
    "finance_specialist": "gpt-4o",     # Needs numerical reasoning
    "hr_specialist": "gpt-4o-mini",
    "operations_specialist": "gpt-4o-mini",
    "dashboard_specialist": "gpt-4o-mini",
    "general_specialist": "gpt-4o",
    
    # Specialists by complexity
    "specialist_simple": "gpt-4o-mini",  # 60% of queries
    "specialist_medium": "gpt-4o",       # 30% of queries
    "specialist_complex": "gpt-4o",      # 10% of queries (was claude)
}


# Complexity tier mapping
COMPLEXITY_TO_MODEL = {
    "simple": "gpt-4o-mini",
    "medium": "gpt-4o",
    "complex": "gpt-4o",  # Use best OpenAI model for complex
}


# =============================================================================
# API Key Validation
# =============================================================================

def _check_api_key() -> bool:
    """Check if OpenAI API key is configured."""
    api_key = os.getenv("OPENAI_API_KEY")
    return api_key is not None and api_key.strip() != ""


def _is_model_available(model_name: str) -> bool:
    """Check if model is supported and API key is set."""
    if model_name not in SUPPORTED_MODELS:
        return False
    return _check_api_key()


def list_available_models() -> Dict[str, Any]:
    """List all available models."""
    if _check_api_key():
        return {
            "available": SUPPORTED_MODELS.copy(),
            "all_supported": list(SUPPORTED_MODELS.keys()),
            "missing_keys": [],
        }
    else:
        return {
            "available": {},
            "all_supported": list(SUPPORTED_MODELS.keys()),
            "missing_keys": ["OPENAI_API_KEY"],
        }


# =============================================================================
# User Preferences (placeholder)
# =============================================================================

def get_user_model_preferences(user_id: str) -> Dict[str, str]:
    """
    Fetch user's model preferences from database.
    
    TODO: Implement Supabase lookup when ready.
    """
    # TODO: Implement database lookup
    # Example:
    # from supabase_connect import get_supabase_manager
    # supabase = get_supabase_manager().client
    # result = supabase.table("user_model_preferences").select("*").eq("user_id", user_id).execute()
    # return {row["agent_name"]: row["model_name"] for row in result.data}
    
    return {}


def save_user_model_preference(user_id: str, agent_name: str, model_name: str) -> bool:
    """Save user's model preference."""
    if model_name not in SUPPORTED_MODELS:
        raise ValueError(f"Invalid model: {model_name}. Supported: {list(SUPPORTED_MODELS.keys())}")
    
    # TODO: Implement database save
    logger.info(f"Saved preference: user={user_id}, agent={agent_name}, model={model_name}")
    return True


# =============================================================================
# Model Resolution
# =============================================================================

def resolve_model(
    agent_name: str,
    complexity: Optional[str] = None,
    user_id: Optional[str] = None,
    fallback: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Resolve which model to use for an agent.
    
    Priority:
    1. User preference (if user_id provided)
    2. Complexity-based selection (if complexity provided)
    3. Default for this agent
    4. Fallback (if provided)
    5. Global fallback (gpt-4o-mini)
    
    Args:
        agent_name: Name of the agent
        complexity: Optional complexity tier ("simple", "medium", "complex")
        user_id: Optional user ID for preference lookup
        fallback: Optional fallback model name
    
    Returns:
        Model configuration dict
    """
    if not _check_api_key():
        raise ValueError("OPENAI_API_KEY not set. Please configure your API key.")
    
    # Build candidate list
    candidates: List[Optional[str]] = []
    
    # 1. User preference
    if user_id:
        user_prefs = get_user_model_preferences(user_id)
        candidates.append(user_prefs.get(agent_name))
    
    # 2. Complexity-based
    if complexity:
        candidates.append(COMPLEXITY_TO_MODEL.get(complexity.lower()))
    
    # 3. Agent default
    candidates.append(DEFAULT_AGENT_MODELS.get(agent_name))
    
    # 4. Provided fallback
    candidates.append(fallback)
    
    # 5. Global fallback
    candidates.append("gpt-4o-mini")
    
    # Find first valid candidate
    chosen_model: Optional[str] = None
    for candidate in candidates:
        if candidate and candidate in SUPPORTED_MODELS:
            chosen_model = candidate
            break
    
    if chosen_model is None:
        chosen_model = "gpt-4o-mini"
    
    config = SUPPORTED_MODELS[chosen_model].copy()
    config["model_name"] = chosen_model
    
    logger.debug(f"Resolved model for '{agent_name}': {chosen_model}")
    
    return config


# =============================================================================
# Client Factory
# =============================================================================

_openai_client = None


def get_openai_client():
    """Get shared AsyncOpenAI client."""
    global _openai_client
    if _openai_client is None:
        from openai import AsyncOpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")
        _openai_client = AsyncOpenAI(api_key=api_key)
    return _openai_client


def get_sync_openai_client():
    """Get synchronous OpenAI client (for embeddings, etc.)."""
    from openai import OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")
    return OpenAI(api_key=api_key)


# =============================================================================
# Legacy Compatibility (for CrewAI agents)
# =============================================================================

def get_llm_for_agent(
    agent_name: str, 
    user_id: Optional[str] = None, 
    fallback_model: Optional[str] = None,
    temperature_override: Optional[float] = None
):
    """
    Get configured LLM instance for a LEGACY (CrewAI) agent.
    
    Returns ChatLiteLLM instance for backward compatibility.
    """
    from langchain_community.chat_models import ChatLiteLLM
    
    config = resolve_model(
        agent_name=agent_name,
        user_id=user_id,
        fallback=fallback_model,
    )
    
    temperature = (
        temperature_override
        if temperature_override is not None
        else config.get("default_temperature", 0.3)
    )
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    return ChatLiteLLM(
        model=config["model_string"],
        api_key=api_key,
        temperature=temperature,
    )


# =============================================================================
# Embeddings Helper
# =============================================================================

def get_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """
    Get embedding for text using OpenAI.
    
    Args:
        text: Text to embed
        model: Embedding model (default: text-embedding-3-small)
    
    Returns:
        List of floats (embedding vector)
    """
    client = get_sync_openai_client()
    
    response = client.embeddings.create(
        model=model,
        input=text,
    )
    
    return response.data[0].embedding


def get_embeddings_batch(texts: List[str], model: str = "text-embedding-3-small") -> List[List[float]]:
    """
    Get embeddings for multiple texts in one API call.
    
    Args:
        texts: List of texts to embed
        model: Embedding model
    
    Returns:
        List of embedding vectors
    """
    client = get_sync_openai_client()
    
    response = client.embeddings.create(
        model=model,
        input=texts,
    )
    
    # Sort by index to maintain order
    embeddings = sorted(response.data, key=lambda x: x.index)
    return [e.embedding for e in embeddings]

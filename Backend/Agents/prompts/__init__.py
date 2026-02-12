"""
Prompt templates for supervisor and specialist agents.

Flow context:
- Gate 1 (intent) filters greetings/chitchat
- Gate 2 (sufficiency) filters no-data cases
- Supervisor classifies domain + complexity
- Specialist answers with appropriate expertise
"""

from .supervisor_prompts import CLASSIFICATION_PROMPT, REROUTE_PROMPT
from .specialist_prompts import (
    FINANCE_SYSTEM_PROMPT,
    HR_SYSTEM_PROMPT,
    OPERATIONS_SYSTEM_PROMPT,
    DASHBOARD_SYSTEM_PROMPT,
    GENERAL_SYSTEM_PROMPT,
    SPECIALIST_PROMPTS,
    get_specialist_prompt,
)

__all__ = [
    # Supervisor
    "CLASSIFICATION_PROMPT",
    "REROUTE_PROMPT",
    
    # Specialists
    "FINANCE_SYSTEM_PROMPT",
    "HR_SYSTEM_PROMPT",
    "OPERATIONS_SYSTEM_PROMPT",
    "DASHBOARD_SYSTEM_PROMPT",
    "GENERAL_SYSTEM_PROMPT",
    "SPECIALIST_PROMPTS",
    "get_specialist_prompt",
]
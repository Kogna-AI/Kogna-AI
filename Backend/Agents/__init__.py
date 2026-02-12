"""
Kogna AI v2.1 — Layer 4: Agent Architecture

LangGraph-based supervisor-specialist pattern with two gates:
- GATE 1: Intent classification (greeting/chitchat vs data question)
- GATE 2: Data sufficiency check (after retrieval)

Components:
- Supervisor: Classifies intent, routes to specialists
- Specialist: Single dynamic agent configured per category
- Auditor: Quality check ("brutal honesty" loop)
- DirectResponder: Handles greetings, chitchat, no-data responses
- TokenBudget: 8K input + 2K output max, 1 re-route max

Usage:
    from agents import KognaAgent
    
    agent = KognaAgent()
    result = await agent.run(
        query="What was our Q3 revenue?",
        context=[...],
        user_id="user_123",
    )
    print(result["response"])
"""

from .graph import build_agent_graph, AgentState, KognaAgent, run_agent
from .supervisor import Supervisor, Category, ClassificationResult
from .specialist import Specialist, SpecialistConfig, SpecialistResponse
from .auditor import Auditor, AuditResult
from .responders import DirectResponder, DirectResponse
from .token_budget import TokenBudget, TokenUsage

__all__ = [
    # Main interface
    "KognaAgent",
    "run_agent",
    
    # Graph
    "build_agent_graph",
    "AgentState",
    
    # Supervisor
    "Supervisor",
    "Category",
    "ClassificationResult",
    
    # Specialist
    "Specialist",
    "SpecialistConfig",
    "SpecialistResponse",
    
    # Auditor
    "Auditor",
    "AuditResult",
    
    # Direct Responder (greetings, chitchat, no-data)
    "DirectResponder",
    "DirectResponse",
    
    # Token management
    "TokenBudget",
    "TokenUsage",
]
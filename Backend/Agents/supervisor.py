"""
Supervisor Agent.

Responsible for:
1. Classifying incoming queries into categories
2. Assessing query complexity for model selection
3. Routing to the appropriate specialist
4. Handling re-routes when specialist confidence is low

NOTE: By the time supervisor sees a query:
- Gate 1 has filtered greetings/chitchat
- Gate 2 has verified sufficient context exists

Uses Ai_agents/llm_factory.py for model selection.
"""

import json
import logging
from typing import Optional
from dataclasses import dataclass
from enum import Enum

from .token_budget import TokenUsage
from .prompts.supervisor_prompts import (
    CLASSIFICATION_PROMPT,
    REROUTE_PROMPT,
)

# Import centralized llm_factory
from Ai_agents.llm_factory import (
    resolve_model,
    get_openai_client,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Data Classes
# =============================================================================

class Category(str, Enum):
    """Query categories for routing."""
    FINANCE = "FINANCE"
    HR = "HR"
    OPERATIONS = "OPERATIONS"
    DASHBOARD = "DASHBOARD"
    GENERAL = "GENERAL"
    # Note: SIMPLE removed - complexity is now a separate field
    # All data questions go to a specialist; complexity determines the model


@dataclass
class ClassificationResult:
    """Result of query classification."""
    category: Category
    confidence: float
    complexity: str  # "simple", "medium", "complex" - determines model
    reasoning: str
    key_entities: list[str]
    input_tokens: int
    output_tokens: int


@dataclass
class RerouteDecision:
    """Decision on whether to reroute a query."""
    should_reroute: bool
    new_category: Optional[Category] = None
    reasoning: str = ""
    input_tokens: int = 0
    output_tokens: int = 0


# =============================================================================
# Supervisor Agent
# =============================================================================

class Supervisor:
    """
    Supervisor agent for query classification and routing.
    
    The supervisor receives queries that have already passed:
    - Gate 1: Intent classification (greetings/chitchat filtered)
    - Gate 2: Data sufficiency check (no-data cases filtered)
    
    It classifies:
    - Category: Which specialist domain (FINANCE, HR, etc.)
    - Complexity: Which model tier (simple→4o-mini, medium→4o, complex→claude)
    
    Uses llm_factory for model selection (default: gpt-4o-mini for speed).
    """
    
    def __init__(
        self,
        max_reroutes: int = 1,
        user_id: Optional[str] = None,
    ):
        """
        Initialize the supervisor.
        
        Args:
            max_reroutes: Maximum number of re-routes allowed per query (default: 1)
            user_id: Optional default user ID for model preferences
        """
        self.max_reroutes = max_reroutes
        self.default_user_id = user_id
    
    async def classify(
        self,
        query: str,
        context_summary: str = "",
        conversation_history: Optional[list[dict]] = None,
        token_usage: Optional[TokenUsage] = None,
        user_id: Optional[str] = None,
    ) -> ClassificationResult:
        """
        Classify a query to determine routing.
        
        Args:
            query: The user's query
            context_summary: Brief summary of available context
            conversation_history: Previous messages in conversation
            token_usage: Optional tracker for token accounting
            user_id: Optional user ID for model preferences
            
        Returns:
            ClassificationResult with category, complexity, and reasoning
        """
        # Resolve model for supervisor
        model_config = resolve_model(
            agent_name="supervisor",
            user_id=user_id or self.default_user_id,
        )
        model = model_config["model_string"]
        
        # Format conversation history
        history_str = ""
        if conversation_history:
            recent = conversation_history[-3:]
            history_str = "\n".join([
                f"{msg.get('role', 'user')}: {msg.get('content', '')[:200]}"
                for msg in recent
            ])
        
        # Build the classification prompt
        prompt = CLASSIFICATION_PROMPT.format(
            query=query,
            context_summary=context_summary or "General business data",
            conversation_history=history_str or "No prior conversation",
        )
        
        try:
            client = get_openai_client()
            
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            
            content = response.choices[0].message.content
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            
            if token_usage:
                token_usage.add_usage(input_tokens, output_tokens)
            
            result = json.loads(content)
            
            # Validate category
            category_str = result.get("category", "GENERAL").upper()
            try:
                category = Category(category_str)
            except ValueError:
                logger.warning(f"Unknown category '{category_str}', defaulting to GENERAL")
                category = Category.GENERAL
            
            return ClassificationResult(
                category=category,
                confidence=float(result.get("confidence", 0.7)),
                complexity=result.get("complexity", "medium"),
                reasoning=result.get("reasoning", ""),
                key_entities=result.get("key_entities", []),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse classification response: {e}")
            return self._default_classification(query)
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return self._default_classification(query)
    
    async def decide_reroute(
        self,
        query: str,
        original_category: Category,
        specialist_confidence: float,
        specialist_feedback: str,
        reroute_count: int,
        token_usage: Optional[TokenUsage] = None,
        user_id: Optional[str] = None,
    ) -> RerouteDecision:
        """
        Decide whether to reroute a query to a different specialist.
        
        Args:
            query: Original query
            original_category: Category that was initially assigned
            specialist_confidence: Confidence reported by specialist
            specialist_feedback: Feedback/reasoning from specialist
            reroute_count: Number of reroutes already attempted
            token_usage: Optional tracker for token accounting
            user_id: Optional user ID for model preferences
            
        Returns:
            RerouteDecision indicating whether to reroute and where
        """
        # Check reroute limit
        if reroute_count >= self.max_reroutes:
            logger.info(f"Reroute limit reached ({reroute_count}/{self.max_reroutes})")
            return RerouteDecision(
                should_reroute=True,
                new_category=Category.GENERAL,
                reasoning="Reroute limit reached, falling back to general specialist",
            )
        
        # Accept if confidence is reasonable
        if specialist_confidence >= 0.5:
            return RerouteDecision(
                should_reroute=False,
                reasoning=f"Specialist confidence ({specialist_confidence:.0%}) is acceptable",
            )
        
        # Resolve model
        model_config = resolve_model(
            agent_name="supervisor",
            user_id=user_id or self.default_user_id,
        )
        model = model_config["model_string"]
        
        # Ask supervisor whether to reroute
        prompt = REROUTE_PROMPT.format(
            query=query,
            original_category=original_category.value,
            confidence=f"{specialist_confidence:.0%}",
            feedback=specialist_feedback or "No specific feedback provided",
        )
        
        try:
            client = get_openai_client()
            
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            
            content = response.choices[0].message.content
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            
            if token_usage:
                token_usage.add_usage(input_tokens, output_tokens)
            
            result = json.loads(content)
            
            should_reroute = result.get("should_reroute", False)
            new_category = None
            
            if should_reroute:
                new_category_str = result.get("new_category", "GENERAL").upper()
                try:
                    new_category = Category(new_category_str)
                except ValueError:
                    new_category = Category.GENERAL
                
                # Don't reroute to the same category
                if new_category == original_category:
                    new_category = Category.GENERAL
            
            return RerouteDecision(
                should_reroute=should_reroute,
                new_category=new_category,
                reasoning=result.get("reasoning", ""),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
            
        except Exception as e:
            logger.error(f"Reroute decision error: {e}")
            return RerouteDecision(
                should_reroute=True,
                new_category=Category.GENERAL,
                reasoning=f"Error in reroute decision: {e}",
            )
    
    def _default_classification(self, query: str) -> ClassificationResult:
        """Return a safe default classification when API call fails."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["revenue", "budget", "cost", "profit", "margin", "financial"]):
            category = Category.FINANCE
        elif any(word in query_lower for word in ["employee", "hiring", "headcount", "hr", "team member"]):
            category = Category.HR
        elif any(word in query_lower for word in ["supply", "inventory", "shipping", "logistics", "process"]):
            category = Category.OPERATIONS
        elif any(word in query_lower for word in ["kpi", "metric", "dashboard", "trend", "chart"]):
            category = Category.DASHBOARD
        else:
            category = Category.GENERAL
        
        return ClassificationResult(
            category=category,
            confidence=0.5,
            complexity="medium",
            reasoning="Fallback classification (keyword-based)",
            key_entities=[],
            input_tokens=0,
            output_tokens=0,
        )
    
    def get_context_summary(self, context: list[dict]) -> str:
        """Generate a brief summary of available context for classification."""
        if not context:
            return "No context available"
        
        sources = set()
        doc_types = set()
        
        for chunk in context[:20]:
            source = chunk.get("source_path", chunk.get("source", ""))
            if source:
                source_name = source.split("/")[-1].split("\\")[-1]
                sources.add(source_name)
            
            doc_type = chunk.get("document_type", "")
            if doc_type:
                doc_types.add(doc_type)
        
        parts = []
        if sources:
            parts.append(f"Sources: {', '.join(list(sources)[:5])}")
        if doc_types:
            parts.append(f"Types: {', '.join(list(doc_types)[:5])}")
        parts.append(f"Chunks: {len(context)}")
        
        return "; ".join(parts) if parts else "General business data"


# =============================================================================
# Convenience Function
# =============================================================================

async def classify_query(
    query: str,
    context_summary: str = "",
    user_id: Optional[str] = None,
) -> ClassificationResult:
    """
    Simple interface to classify a query.
    
    Args:
        query: User's query
        context_summary: Brief description of available context
        user_id: Optional user ID for model preferences
        
    Returns:
        ClassificationResult
    """
    supervisor = Supervisor()
    return await supervisor.classify(query, context_summary, user_id=user_id)
"""
Dynamic Specialist Agent (OpenAI Only).

A single, reusable agent that handles all specialist domains.
Configuration (prompt, model) is passed at runtime based on the
supervisor's classification.

Uses Ai_agents/llm_factory.py for model selection.
"""

import logging
import re
from typing import Optional
from dataclasses import dataclass, field

from .token_budget import TokenBudget, TokenUsage
from .prompts.specialist_prompts import get_specialist_prompt, SPECIALIST_PROMPTS

from Ai_agents.llm_factory import resolve_model, get_openai_client

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class SpecialistConfig:
    """Configuration for a specialist invocation."""
    category: str                      # FINANCE, HR, OPERATIONS, DASHBOARD, GENERAL
    complexity: str = "medium"         # simple, medium, complex
    max_output_tokens: int = 1500
    temperature: float = 0.3


@dataclass
class SpecialistResponse:
    """Response from the specialist agent."""
    content: str
    confidence: float                  # 0.0 to 1.0
    category: str                      # Which specialist handled it
    model_used: str                    # Actual model name
    input_tokens: int
    output_tokens: int
    sources_cited: list[str] = field(default_factory=list)
    needs_reroute: bool = False
    reroute_suggestion: Optional[str] = None
    error: Optional[str] = None


# =============================================================================
# Specialist Agent
# =============================================================================

class Specialist:
    """
    Dynamic specialist agent (OpenAI only).
    
    Single agent that handles all specialist domains by:
    1. Loading the appropriate prompt based on category
    2. Selecting the appropriate model via llm_factory
    3. Generating a response with confidence scoring
    
    Usage:
        specialist = Specialist()
        response = await specialist.process(
            query="What was Q3 revenue?",
            context=[...],
            config=SpecialistConfig(category="FINANCE", complexity="simple"),
            user_id="user_123"
        )
    """
    
    def __init__(self):
        """Initialize the specialist."""
        pass
    
    async def process(
        self,
        query: str,
        context: list[dict],
        config: SpecialistConfig,
        user_id: Optional[str] = None,
        conversation_history: Optional[list[dict]] = None,
        token_budget: Optional[TokenBudget] = None,
        token_usage: Optional[TokenUsage] = None,
        audit_feedback: Optional[str] = None,  # Feedback from failed audit
    ) -> SpecialistResponse:
        """
        Process a query with the appropriate specialist configuration.
        
        Args:
            query: User's query
            context: Retrieved context chunks
            config: Specialist configuration (category, complexity, etc.)
            user_id: Optional user ID for model preference lookup
            conversation_history: Previous messages for context
            token_budget: Optional budget enforcer
            token_usage: Optional usage tracker
            audit_feedback: Feedback from auditor if this is a retry
            
        Returns:
            SpecialistResponse with content and metadata
        """
        # 1. Get the system prompt for this category
        system_prompt = get_specialist_prompt(config.category)
        
        # 2. Resolve model using llm_factory
        agent_name = f"{config.category.lower()}_specialist"
        try:
            model_config = resolve_model(
                agent_name=agent_name,
                complexity=config.complexity,
                user_id=user_id,
            )
        except ValueError as e:
            return SpecialistResponse(
                content=f"Model configuration error: {e}",
                confidence=0.0,
                category=config.category,
                model_used="none",
                input_tokens=0,
                output_tokens=0,
                error=str(e),
            )
        
        model_name = model_config["model_name"]
        model_string = model_config["model_string"]
        
        # 3. Build the user prompt with context (include audit feedback if retry)
        user_prompt = self._build_user_prompt(
            query=query,
            context=context,
            conversation_history=conversation_history,
            audit_feedback=audit_feedback,
        )
        
        # 4. Trim context if needed to fit token budget
        if token_budget and token_usage:
            system_tokens = token_budget.count_tokens(system_prompt)
            user_tokens = token_budget.count_tokens(user_prompt)
            
            estimate = token_budget.estimate_call_cost(
                prompt_tokens=system_tokens + user_tokens,
                expected_output_tokens=config.max_output_tokens,
                usage=token_usage
            )
            
            if not estimate["fits"]:
                trimmed_context = token_budget.trim_context_to_budget(
                    context,
                    other_prompt_tokens=system_tokens + 300,
                    usage=token_usage
                )
                user_prompt = self._build_user_prompt(
                    query=query,
                    context=trimmed_context,
                    conversation_history=conversation_history,
                    audit_feedback=audit_feedback,
                )
                logger.info(f"Trimmed context from {len(context)} to {len(trimmed_context)} chunks")
        
        # 5. Call OpenAI
        try:
            client = get_openai_client()
            
            response = await client.chat.completions.create(
                model=model_string,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=config.max_output_tokens,
                temperature=config.temperature,
            )
            
            content = response.choices[0].message.content
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            
        except Exception as e:
            logger.error(f"OpenAI call failed: {e}")
            return SpecialistResponse(
                content=f"I encountered an error generating a response: {str(e)}",
                confidence=0.0,
                category=config.category,
                model_used=model_name,
                input_tokens=0,
                output_tokens=0,
                error=str(e),
            )
        
        # 6. Update token usage if tracking
        if token_usage:
            token_usage.add_usage(input_tokens, output_tokens)
        
        # 7. Parse confidence and reroute signals
        confidence, needs_reroute, reroute_suggestion = self._extract_confidence(
            content, config.category
        )
        
        # 8. Extract cited sources
        sources_cited = self._extract_sources(content, context)
        
        return SpecialistResponse(
            content=content,
            confidence=confidence,
            category=config.category,
            model_used=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            sources_cited=sources_cited,
            needs_reroute=needs_reroute,
            reroute_suggestion=reroute_suggestion,
        )
    
    def _build_user_prompt(
        self,
        query: str,
        context: list[dict],
        conversation_history: Optional[list[dict]] = None,
        audit_feedback: Optional[str] = None,
    ) -> str:
        """Build the user prompt with context, history, and audit feedback."""
        parts = []
        
        # === AUDIT FEEDBACK (if this is a retry) ===
        if audit_feedback:
            parts.append("## ⚠️ IMPORTANT: Previous Response Failed Quality Check")
            parts.append(f"**Issue:** {audit_feedback}")
            parts.append("**You MUST fix these issues in your response.**")
            parts.append("")
        
        # === CONVERSATION HISTORY ===
        if conversation_history:
            parts.append("## Recent Conversation")
            for msg in conversation_history[-5:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                parts.append(f"**{role.title()}**: {content}")
            parts.append("")
        
        # === RETRIEVED CONTEXT ===
        if context:
            parts.append("## Retrieved Context")
            parts.append("Use the following information to answer. Cite sources as [1], [2], etc.")
            parts.append("")
            
            for i, chunk in enumerate(context, 1):
                source = chunk.get("source_path", chunk.get("source", "Unknown"))
                content = chunk.get("content", "")
                freshness = chunk.get("freshness_score", 1.0)
                
                parts.append(f"### Source [{i}]: {source}")
                if freshness < 0.5:
                    parts.append(f"*Note: This data may be outdated (freshness: {freshness:.0%})*")
                parts.append(content)
                parts.append("")
        else:
            parts.append("## Retrieved Context")
            parts.append("*No relevant context was retrieved for this query.*")
            parts.append("")
        
        # === USER QUERY ===
        parts.append("## User Query")
        parts.append(query)
        parts.append("")
        
        # === RESPONSE INSTRUCTIONS ===
        parts.append("## Instructions")
        parts.append("1. Answer the query using ONLY the context provided above")
        parts.append("2. Cite sources as [1], [2], etc. for EVERY claim")
        parts.append("3. If the context doesn't contain the information, say 'I don't have this information'")
        parts.append("4. End with: 'Confidence: HIGH/MEDIUM/LOW'")
        
        return "\n".join(parts)
    
    def _extract_confidence(
        self,
        response: str,
        category: str
    ) -> tuple[float, bool, Optional[str]]:
        """Extract confidence level and reroute signals from response."""
        response_lower = response.lower()
        
        # Extract confidence
        if "confidence: high" in response_lower:
            confidence = 0.85
        elif "confidence: medium" in response_lower:
            confidence = 0.6
        elif "confidence: low" in response_lower:
            confidence = 0.3
        else:
            # Infer from citations
            confidence = 0.7 if "[1]" in response else 0.5
        
        # Check for reroute signals
        needs_reroute = False
        reroute_suggestion = None
        
        reroute_phrases = [
            "different specialist",
            "better handled by",
            "outside my expertise",
        ]
        
        for phrase in reroute_phrases:
            if phrase in response_lower:
                needs_reroute = True
                for cat in SPECIALIST_PROMPTS.keys():
                    if cat.lower() in response_lower:
                        reroute_suggestion = cat
                        break
                break
        
        return confidence, needs_reroute, reroute_suggestion
    
    def _extract_sources(self, response: str, context: list[dict]) -> list[str]:
        """Extract which sources were cited in the response."""
        citations = re.findall(r'\[(\d+)\]', response)
        cited_indices = set(int(c) for c in citations)
        
        sources = []
        for idx in sorted(cited_indices):
            if 0 < idx <= len(context):
                source = context[idx - 1].get(
                    "source_path", 
                    context[idx - 1].get("source", f"Source {idx}")
                )
                sources.append(source)
        
        return sources


# =============================================================================
# Convenience Function
# =============================================================================

async def run_specialist(
    query: str,
    context: list[dict],
    category: str,
    complexity: str = "medium",
    user_id: Optional[str] = None,
) -> SpecialistResponse:
    """Simple interface to run a specialist query."""
    specialist = Specialist()
    config = SpecialistConfig(category=category, complexity=complexity)
    return await specialist.process(query, context, config, user_id=user_id)

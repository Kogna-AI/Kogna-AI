"""
Token Budget Enforcer.

Enforces per-query token ceiling to prevent cost overruns.
From v2.1 Plan Section 7.4:
- Max 8,000 input tokens + 2,000 output tokens per query
- If approaching 80% ceiling, stop further agent calls
- Generate response from available context
"""

import logging
from dataclasses import dataclass
from typing import Optional

import tiktoken

logger = logging.getLogger(__name__)


@dataclass
class TokenUsage:
    """Tracks token usage for a single query."""
    input_tokens: int = 0
    output_tokens: int = 0
    
    @property
    def total(self) -> int:
        return self.input_tokens + self.output_tokens
    
    def add_input(self, tokens: int) -> None:
        self.input_tokens += tokens
    
    def add_output(self, tokens: int) -> None:
        self.output_tokens += tokens
    
    def add_usage(self, input_tokens: int, output_tokens: int) -> None:
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens


class TokenBudget:
    """
    Enforces token budget constraints for a query.
    
    Budget from v2.1 Architecture Plan:
    - 8,000 input tokens max (context + prompt)
    - 2,000 output tokens max (response)
    - Warning at 80% of ceiling
    - Hard stop at 100%
    
    Cost impact at 50K queries/day:
    - Base cost: ~$0.0071/query
    - With 5% re-route: ~$0.0074/query
    - With 10% re-route: ~$0.0077/query
    """
    
    # Budget limits (from v2.1 plan)
    MAX_INPUT_TOKENS = 8000
    MAX_OUTPUT_TOKENS = 2000
    MAX_TOTAL_TOKENS = MAX_INPUT_TOKENS + MAX_OUTPUT_TOKENS  # 10,000
    
    # Warning threshold
    WARNING_THRESHOLD = 0.8  # 80%
    
    def __init__(
        self,
        max_input_tokens: Optional[int] = None,
        max_output_tokens: Optional[int] = None,
        encoding_name: str = "cl100k_base"
    ):
        """
        Initialize the token budget.
        
        Args:
            max_input_tokens: Override default input token limit
            max_output_tokens: Override default output token limit
            encoding_name: Tiktoken encoding for token counting
        """
        self.max_input = max_input_tokens or self.MAX_INPUT_TOKENS
        self.max_output = max_output_tokens or self.MAX_OUTPUT_TOKENS
        self.max_total = self.max_input + self.max_output
        
        try:
            self.tokenizer = tiktoken.get_encoding(encoding_name)
        except Exception:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string."""
        if not text:
            return 0
        return len(self.tokenizer.encode(text))
    
    def check_budget(self, usage: TokenUsage) -> dict:
        """
        Check if the current usage is within budget.
        
        Returns:
            dict with:
            - within_budget: bool
            - warning: bool (approaching limit)
            - input_remaining: int
            - output_remaining: int
            - utilization: float (0.0 to 1.0+)
        """
        input_remaining = self.max_input - usage.input_tokens
        output_remaining = self.max_output - usage.output_tokens
        utilization = usage.total / self.max_total
        
        within_budget = (
            usage.input_tokens <= self.max_input and
            usage.output_tokens <= self.max_output
        )
        
        warning = utilization >= self.WARNING_THRESHOLD and within_budget
        
        return {
            "within_budget": within_budget,
            "warning": warning,
            "input_remaining": max(0, input_remaining),
            "output_remaining": max(0, output_remaining),
            "utilization": utilization,
            "input_utilization": usage.input_tokens / self.max_input,
            "output_utilization": usage.output_tokens / self.max_output,
        }
    
    def can_proceed(self, usage: TokenUsage) -> bool:
        """
        Check if we can proceed with another agent call.
        
        Returns False if:
        - Already at or over 80% of total budget
        - Input tokens exhausted
        """
        status = self.check_budget(usage)
        
        if not status["within_budget"]:
            logger.warning(f"Token budget exceeded: {usage.total} / {self.max_total}")
            return False
        
        if status["warning"]:
            logger.warning(f"Token budget warning: {status['utilization']:.1%} utilized")
            return False
        
        return True
    
    def estimate_call_cost(
        self,
        prompt_tokens: int,
        expected_output_tokens: int,
        usage: TokenUsage
    ) -> dict:
        """
        Estimate if a proposed LLM call fits within budget.
        
        Args:
            prompt_tokens: Estimated tokens in the prompt
            expected_output_tokens: Expected output tokens
            usage: Current usage
            
        Returns:
            dict with fit assessment and recommendations
        """
        projected_input = usage.input_tokens + prompt_tokens
        projected_output = usage.output_tokens + expected_output_tokens
        projected_total = projected_input + projected_output
        
        fits_input = projected_input <= self.max_input
        fits_output = projected_output <= self.max_output
        fits_total = projected_total <= self.max_total
        
        # Calculate how much we need to trim if it doesn't fit
        input_overflow = max(0, projected_input - self.max_input)
        output_overflow = max(0, projected_output - self.max_output)
        
        return {
            "fits": fits_input and fits_output and fits_total,
            "fits_input": fits_input,
            "fits_output": fits_output,
            "projected_input": projected_input,
            "projected_output": projected_output,
            "projected_total": projected_total,
            "input_overflow": input_overflow,
            "output_overflow": output_overflow,
            "recommended_context_reduction": input_overflow,
            "recommended_max_output": self.max_output - usage.output_tokens,
        }
    
    def trim_context_to_budget(
        self,
        context_chunks: list[dict],
        other_prompt_tokens: int,
        usage: TokenUsage
    ) -> list[dict]:
        """
        Trim context chunks to fit within remaining input budget.
        
        Keeps highest-scored chunks first (assumes chunks are pre-sorted by relevance).
        
        Args:
            context_chunks: List of chunks with 'content' and optionally 'token_count'
            other_prompt_tokens: Tokens used by system prompt, query, etc.
            usage: Current token usage
            
        Returns:
            Trimmed list of chunks that fits budget
        """
        available_for_context = self.max_input - usage.input_tokens - other_prompt_tokens
        
        if available_for_context <= 0:
            logger.warning("No token budget remaining for context")
            return []
        
        selected_chunks = []
        tokens_used = 0
        
        for chunk in context_chunks:
            chunk_tokens = chunk.get("token_count") or self.count_tokens(chunk.get("content", ""))
            
            if tokens_used + chunk_tokens <= available_for_context:
                selected_chunks.append(chunk)
                tokens_used += chunk_tokens
            else:
                # Can't fit more chunks
                break
        
        if len(selected_chunks) < len(context_chunks):
            logger.info(
                f"Trimmed context from {len(context_chunks)} to {len(selected_chunks)} chunks "
                f"to fit token budget ({tokens_used}/{available_for_context} tokens)"
            )
        
        return selected_chunks
    
    def get_max_output_tokens(self, usage: TokenUsage) -> int:
        """Get the maximum output tokens allowed given current usage."""
        remaining = self.max_output - usage.output_tokens
        return max(100, remaining)  # Always allow at least 100 tokens for response


class TokenBudgetExceeded(Exception):
    """Raised when token budget is exceeded and cannot proceed."""
    
    def __init__(self, usage: TokenUsage, limit: int, message: str = "Token budget exceeded"):
        self.usage = usage
        self.limit = limit
        self.message = message
        super().__init__(f"{message}: {usage.total} / {limit}")


# Convenience functions

def create_budget() -> tuple[TokenBudget, TokenUsage]:
    """Create a new token budget and usage tracker for a query."""
    return TokenBudget(), TokenUsage()


def check_and_update(
    budget: TokenBudget,
    usage: TokenUsage,
    input_tokens: int,
    output_tokens: int
) -> bool:
    """
    Update usage and check if still within budget.
    
    Returns True if within budget, False if exceeded.
    """
    usage.add_usage(input_tokens, output_tokens)
    return budget.check_budget(usage)["within_budget"]

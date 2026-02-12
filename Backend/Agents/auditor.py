"""
Auditor Agent.

Responsible for the "Brutal Honesty" loop:
1. Critiquing specialist responses against context
2. Detecting hallucinations and vagueness
3. Enforcing strict data integrity
"""

import json
import logging
from typing import Optional
from dataclasses import dataclass

from Ai_agents.llm_factory import get_openai_client

logger = logging.getLogger(__name__)


# =============================================================================
# Critic Prompt (inline to avoid import issues)
# =============================================================================

CRITIC_SYSTEM_PROMPT = """You are a STRICT fact-checking auditor. Your job is to verify that AI responses are:
1. **Factually accurate** — Every claim MUST be supported by the provided context
2. **Properly cited** — Sources referenced as [1], [2] must match the actual context
3. **Not hallucinated** — NO information that isn't in the context
4. **Complete** — Answers the user's actual question

## Your Task
Review the agent's response against the retrieved context. Be BRUTAL.

## Response Format (JSON only)
{
    "approved": true/false,
    "critique": "Specific issues found (null if approved)",
    "missing_info": "What information is missing or wrong (null if approved)"
}

## Rules
- If ANY claim is not supported by context → approved: false
- If citations don't match sources → approved: false  
- If response is vague when context has specifics → approved: false
- If response invents data not in context → approved: false
- Only approve if response is accurate AND complete
"""


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class AuditResult:
    """Result of the audit process."""
    approved: bool
    critique: Optional[str] = None
    missing_info: Optional[str] = None


# =============================================================================
# Auditor Agent
# =============================================================================

class Auditor:
    """
    Quality Assurance Auditor.
    
    Uses a 'Critic' persona to review agent outputs before they reach the user.
    Catches hallucinations, unsupported claims, and missing information.
    """
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        """
        Initialize the auditor.
        
        Args:
            model_name: Model to use for auditing (default: gpt-4o-mini for cost)
        """
        self.model_name = model_name
    
    async def audit(
        self, 
        query: str, 
        response_content: str, 
        context: list[dict]
    ) -> AuditResult:
        """
        Run the brutal audit.
        
        Args:
            query: The original user query
            response_content: The specialist's proposed answer
            context: Retrieved context chunks
            
        Returns:
            AuditResult with approval status and critique
        """
        # Format context for audit
        formatted_context = ""
        for i, chunk in enumerate(context[:5]):  # Limit to 5 chunks
            source = chunk.get('source_path', chunk.get('source', f'Source {i+1}'))
            content = chunk.get('content', '')
            formatted_context += f"[{i+1}] {source}:\n{content}\n\n"
        
        if not formatted_context:
            formatted_context = "No context provided."
        
        # Build audit input
        audit_input = f"""## Original User Query:
{query}

## Retrieved Context Data:
{formatted_context}

## Agent Response to Audit:
{response_content}
"""
        
        client = get_openai_client()
        
        try:
            audit_response = await client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": CRITIC_SYSTEM_PROMPT},
                    {"role": "user", "content": audit_input}
                ],
                response_format={"type": "json_object"},
                temperature=0.0,  # Strict deterministic auditing
                max_tokens=300,
            )
            
            content = audit_response.choices[0].message.content
            result_json = json.loads(content)
            
            logger.debug(f"Audit result: approved={result_json.get('approved')}")
            
            return AuditResult(
                approved=result_json.get("approved", True),
                critique=result_json.get("critique"),
                missing_info=result_json.get("missing_info")
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Audit JSON parse failed: {e}")
            return AuditResult(approved=True)  # Fail open
            
        except Exception as e:
            logger.error(f"Audit failed due to error: {e}")
            # Fail open (approve) if the auditor breaks, to avoid blocking the user
            return AuditResult(approved=True)


# =============================================================================
# Convenience Function
# =============================================================================

async def run_audit(query: str, response: str, context: list[dict]) -> AuditResult:
    """Simple interface to run an audit."""
    auditor = Auditor()
    return await auditor.audit(query, response, context)

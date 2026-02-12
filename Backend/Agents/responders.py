"""
Direct Response Handlers.

Handles all responses that DON'T need the full RAG + Specialist pipeline:
- Greetings: "Hi", "Hello", etc.
- Chitchat: "How are you?", "Thanks", "Who are you?"
- No Data: When retrieval finds insufficient context

Uses cheap/fast LLM calls (gpt-4o-mini) for natural responses.
"""

import logging
import random
from typing import Optional
from dataclasses import dataclass

from Ai_agents.llm_factory import get_openai_client

logger = logging.getLogger(__name__)


# =============================================================================
# Response Types
# =============================================================================

@dataclass
class DirectResponse:
    """Response from direct handler (no specialist needed)."""
    content: str
    response_type: str  # "greeting", "chitchat", "no_data"
    model_used: str     # "hardcoded" or "gpt-4o-mini"
    confidence: float


# =============================================================================
# Configuration
# =============================================================================

# Set to True to use LLM for more natural responses
# Set to False for zero-latency hardcoded responses
USE_LLM_FOR_GREETING = False      # Greetings are simple, hardcoded is fine
USE_LLM_FOR_CHITCHAT = False      # Chitchat is predictable, hardcoded is fine
USE_LLM_FOR_NO_DATA = True        # No-data benefits from contextual LLM response

# Model for direct responses (cheap and fast)
DIRECT_RESPONSE_MODEL = "gpt-4o-mini"


# =============================================================================
# Hardcoded Response Templates
# =============================================================================

GREETING_RESPONSES = [
    "Hello! How can I help you with your data today?",
    "Hi there! What would you like to know?",
    "Hey! I'm ready to help. What can I look up for you?",
    "Hello! What information can I find for you?",
    "Hi! What data would you like me to search for?",
]

CHITCHAT_RESPONSES = {
    "how_are_you": [
        "I'm doing well, thanks for asking! How can I help you with your data?",
        "I'm great! Ready to help. What would you like to know?",
    ],
    "thanks": [
        "You're welcome! Let me know if you need anything else.",
        "Happy to help! Is there anything else you'd like to know?",
    ],
    "goodbye": [
        "Goodbye! Feel free to come back anytime.",
        "See you later! I'm here whenever you need data assistance.",
    ],
    "who_are_you": [
        "I'm Kogna, your data assistant. I can help you find information from your company's documents — financials, HR data, operations, and more. What would you like to know?",
    ],
    "capabilities": [
        "I can help you search through your company's documents and data. I'm good at answering questions about financials, HR, operations, KPIs, and more. What would you like to explore?",
    ],
    "default": [
        "I'm here to help! What data can I look up for you?",
        "Sure thing! What would you like to know about your data?",
    ],
}

NO_DATA_TEMPLATES = {
    "no_context_retrieved": (
        "I couldn't find any documents related to your question. "
        "This might mean the information isn't in the documents I have access to, "
        "or the question could be rephrased. What specific topic or document should I look in?"
    ),
    "low_relevance": (
        "I found some documents, but they don't seem to contain what you're looking for. "
        "Could you try being more specific, or let me know which documents should have this information?"
    ),
    "default": (
        "I don't have enough information to answer that question reliably. "
        "Could you rephrase or point me to where this data might be stored?"
    ),
}


# =============================================================================
# Direct Responder Class
# =============================================================================

class DirectResponder:
    """
    Handles all direct responses that bypass the specialist.
    
    Usage:
        responder = DirectResponder()
        
        # For greetings
        response = await responder.greeting("Hello!")
        
        # For chitchat
        response = await responder.chitchat("How are you?")
        
        # For no-data situations
        response = await responder.no_data(
            query="What's our Mars office revenue?",
            reason="no_context_retrieved",
            context=[]
        )
    """
    
    def __init__(self, model: str = DIRECT_RESPONSE_MODEL):
        self.model = model
    
    # -------------------------------------------------------------------------
    # Greeting Response
    # -------------------------------------------------------------------------
    
    async def greeting(self, query: str) -> DirectResponse:
        """
        Generate response for greetings.
        
        Args:
            query: The greeting query (e.g., "Hi", "Hello")
            
        Returns:
            DirectResponse with greeting reply
        """
        if USE_LLM_FOR_GREETING:
            content = await self._llm_greeting(query)
            model_used = self.model
        else:
            content = random.choice(GREETING_RESPONSES)
            model_used = "hardcoded"
        
        logger.debug(f"Greeting response: {content[:50]}...")
        
        return DirectResponse(
            content=content,
            response_type="greeting",
            model_used=model_used,
            confidence=1.0,
        )
    
    async def _llm_greeting(self, query: str) -> str:
        """Generate greeting using LLM."""
        prompt = f"""User greeted with: "{query}"

Respond warmly in 1 sentence, then ask how you can help with their data.
Keep it natural and brief."""

        return await self._call_llm(prompt, max_tokens=50)
    
    # -------------------------------------------------------------------------
    # Chitchat Response
    # -------------------------------------------------------------------------
    
    async def chitchat(self, query: str) -> DirectResponse:
        """
        Generate response for chitchat/small talk.
        
        Args:
            query: The chitchat query (e.g., "How are you?", "Thanks")
            
        Returns:
            DirectResponse with chitchat reply
        """
        if USE_LLM_FOR_CHITCHAT:
            content = await self._llm_chitchat(query)
            model_used = self.model
        else:
            content = self._hardcoded_chitchat(query)
            model_used = "hardcoded"
        
        logger.debug(f"Chitchat response: {content[:50]}...")
        
        return DirectResponse(
            content=content,
            response_type="chitchat",
            model_used=model_used,
            confidence=1.0,
        )
    
    def _hardcoded_chitchat(self, query: str) -> str:
        """Get hardcoded chitchat response based on query type."""
        query_lower = query.lower()
        
        if "how are you" in query_lower or "how's it going" in query_lower:
            return random.choice(CHITCHAT_RESPONSES["how_are_you"])
        elif "thank" in query_lower or "appreciate" in query_lower:
            return random.choice(CHITCHAT_RESPONSES["thanks"])
        elif "bye" in query_lower or "goodbye" in query_lower or "see you" in query_lower:
            return random.choice(CHITCHAT_RESPONSES["goodbye"])
        elif "who are you" in query_lower or "what are you" in query_lower:
            return random.choice(CHITCHAT_RESPONSES["who_are_you"])
        elif "what can you" in query_lower or "what do you do" in query_lower:
            return random.choice(CHITCHAT_RESPONSES["capabilities"])
        else:
            return random.choice(CHITCHAT_RESPONSES["default"])
    
    async def _llm_chitchat(self, query: str) -> str:
        """Generate chitchat response using LLM."""
        prompt = f"""User said: "{query}"

You are Kogna, a friendly data assistant. Respond naturally to this small talk,
then gently steer toward how you can help with their data questions.
Keep it to 1-2 sentences."""

        return await self._call_llm(prompt, max_tokens=75)
    
    # -------------------------------------------------------------------------
    # No Data Response
    # -------------------------------------------------------------------------
    
    async def no_data(
        self,
        query: str,
        reason: str,
        context: Optional[list[dict]] = None,
    ) -> DirectResponse:
        """
        Generate response when no sufficient data is found.
        
        Args:
            query: The user's original query
            reason: Why data was insufficient (e.g., "no_context_retrieved", "low_relevance")
            context: The retrieved context (even if insufficient)
            
        Returns:
            DirectResponse explaining lack of data
        """
        if USE_LLM_FOR_NO_DATA:
            content = await self._llm_no_data(query, reason, context or [])
            model_used = self.model
        else:
            content = self._hardcoded_no_data(reason)
            model_used = "hardcoded"
        
        logger.info(f"No-data response (reason={reason}): {content[:50]}...")
        
        return DirectResponse(
            content=content,
            response_type="no_data",
            model_used=model_used,
            confidence=0.0,  # No data = no confidence
        )
    
    def _hardcoded_no_data(self, reason: str) -> str:
        """Get hardcoded no-data response based on reason."""
        if "no_context" in reason:
            return NO_DATA_TEMPLATES["no_context_retrieved"]
        elif "low_relevance" in reason or "low_keyword" in reason:
            return NO_DATA_TEMPLATES["low_relevance"]
        else:
            return NO_DATA_TEMPLATES["default"]
    
    async def _llm_no_data(
        self,
        query: str,
        reason: str,
        context: list[dict],
    ) -> str:
        """Generate contextual no-data response using LLM."""
        # Extract available sources (even if not relevant)
        available_sources = []
        for chunk in context[:5]:
            source = chunk.get("source_path", chunk.get("source", ""))
            if source:
                source_name = source.split("/")[-1].split("\\")[-1]
                if source_name and source_name not in available_sources:
                    available_sources.append(source_name)
        
        # Extract what topics might be available
        available_topics = self._extract_topics_from_context(context)
        
        prompt = f"""User asked: "{query}"

I searched but couldn't find sufficient data to answer this.
Reason: {reason}

Available document sources (may not be relevant): {available_sources[:5] if available_sources else "None found"}
Topics I might be able to help with instead: {available_topics[:5] if available_topics else "Unknown"}

Write a helpful 2-3 sentence response that:
1. Acknowledges I don't have the specific data they need (be specific about what's missing)
2. If there are available sources/topics, briefly mention what I CAN help with
3. Suggest how they might rephrase OR what documents to upload

Rules:
- Be warm and helpful, not robotic
- Don't apologize excessively (one "sorry" max)
- Don't make up any data
- Don't use bullet points"""

        return await self._call_llm(prompt, max_tokens=150)
    
    def _extract_topics_from_context(self, context: list[dict]) -> list[str]:
        """Extract potential topics from context for suggestions."""
        topics = set()
        
        keywords_to_topics = {
            "revenue": "Revenue & Sales",
            "sales": "Revenue & Sales",
            "employee": "HR & Workforce",
            "headcount": "HR & Workforce",
            "budget": "Budgets & Forecasts",
            "expense": "Expenses",
            "cost": "Costs & Expenses",
            "inventory": "Inventory",
            "shipping": "Logistics",
            "customer": "Customer Data",
            "kpi": "KPIs & Metrics",
            "profit": "Profitability",
            "margin": "Margins",
        }
        
        for chunk in context[:10]:
            content = chunk.get("content", "").lower()
            for keyword, topic in keywords_to_topics.items():
                if keyword in content:
                    topics.add(topic)
        
        return list(topics)
    
    # -------------------------------------------------------------------------
    # LLM Helper
    # -------------------------------------------------------------------------
    
    async def _call_llm(self, prompt: str, max_tokens: int = 100) -> str:
        """Make a simple LLM call."""
        try:
            client = get_openai_client()
            
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"LLM call failed in DirectResponder: {e}")
            # Fallback to hardcoded
            return "I'm here to help! What would you like to know about your data?"


# =============================================================================
# Convenience Functions
# =============================================================================

async def respond_to_greeting(query: str) -> DirectResponse:
    """Quick function to respond to a greeting."""
    responder = DirectResponder()
    return await responder.greeting(query)


async def respond_to_chitchat(query: str) -> DirectResponse:
    """Quick function to respond to chitchat."""
    responder = DirectResponder()
    return await responder.chitchat(query)


async def respond_to_no_data(
    query: str,
    reason: str,
    context: Optional[list[dict]] = None,
) -> DirectResponse:
    """Quick function to respond when no data is available."""
    responder = DirectResponder()
    return await responder.no_data(query, reason, context)
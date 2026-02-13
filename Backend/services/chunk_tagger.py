"""
Pre-Cluster Classification (Tagging) Service

Tag-Constrained Recursive Retrieval (TCRR) - Classifies text chunks by domain
before clustering to prevent "domain bleeding" (e.g., Technical mixed with Financial).

Uses gpt-4o-mini for fast, cheap classification during ingestion.
Tags act as hard barriers during clustering.
"""

import json
import logging
import asyncio
from typing import List, Dict, Optional, Any

# Allowed tags for TCRR
ALLOWED_TAGS = frozenset({
    "Technical",   # Code, infrastructure, logs, architecture
    "Financial",   # Costs, revenue, pricing, budget
    "Legal",       # Contracts, compliance, terms, privacy
    "Operational", # Process, HR, team, schedules
    "Security",    # Vulnerabilities, auth, keys, risks
    "General",     # Fallback for introduction/generic text
})

DEFAULT_TAG = "General"

SYSTEM_PROMPT = """You are a precise data classifier. You will receive a text chunk from a business document.

Task: Classify the text into exactly ONE of the following categories:
- Technical (Code, infrastructure, logs, architecture)
- Financial (Costs, revenue, pricing, budget)
- Legal (Contracts, compliance, terms, privacy)
- Operational (Process, HR, team, schedules)
- Security (Vulnerabilities, auth, keys, risks)
- General (Fallback for introduction/generic text)

Constraint: Return ONLY a JSON object. Do not add markdown formatting.

Example Output: {"tag": "Technical", "confidence": 0.95}"""


def _build_user_prompt(chunk_text: str) -> str:
    """Build user prompt with truncated chunk for token efficiency."""
    # Limit to ~800 chars to stay within token limits and reduce cost
    text = chunk_text.strip()
    if len(text) > 800:
        text = text[:800] + "..."
    return f"Classify this text chunk:\n\n{text}"


def _parse_tag_response(response_text: str) -> Dict[str, Any]:
    """Parse LLM response into tag and confidence. Returns fallback on failure."""
    try:
        # Strip markdown code blocks if present
        text = response_text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        data = json.loads(text)
        tag = data.get("tag", DEFAULT_TAG)
        confidence = float(data.get("confidence", 0.5))

        # Validate tag
        if tag not in ALLOWED_TAGS:
            tag = DEFAULT_TAG

        return {"tag": tag, "confidence": min(1.0, max(0.0, confidence))}
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logging.warning(f"Chunk tagger parse error: {e}. Response: {response_text[:200]}")
        return {"tag": DEFAULT_TAG, "confidence": 0.0}


async def _tag_single_chunk(client, chunk_text: str) -> Dict[str, Any]:
    """Tag a single chunk via gpt-4o-mini."""
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_prompt(chunk_text)},
            ],
            temperature=0.0,
            max_tokens=50,
        )
        content = response.choices[0].message.content or "{}"
        return _parse_tag_response(content)
    except Exception as e:
        logging.warning(f"Chunk tagger API error: {e}")
        return {"tag": DEFAULT_TAG, "confidence": 0.0}


async def tag_chunks_batch(
    chunks: List[str],
    max_concurrent: int = 15,
) -> List[Dict[str, Any]]:
    """
    Tag multiple chunks in parallel. Designed for <1.5s per batch.

    Args:
        chunks: List of text chunks to classify
        max_concurrent: Max parallel API calls (default 15)

    Returns:
        List of {"tag": str, "confidence": float} for each chunk
    """
    if not chunks:
        return []

    try:
        from Ai_agents.llm_factory import get_openai_client
        client = get_openai_client()
    except Exception as e:
        logging.error(f"Chunk tagger: Could not get OpenAI client: {e}")
        return [{"tag": DEFAULT_TAG, "confidence": 0.0} for _ in chunks]

    semaphore = asyncio.Semaphore(max_concurrent)

    async def _tag_with_semaphore(text: str) -> Dict[str, any]:
        async with semaphore:
            return await _tag_single_chunk(client, text)

    results = await asyncio.gather(
        *[_tag_with_semaphore(chunk) for chunk in chunks],
        return_exceptions=True,
    )

    # Handle any exceptions
    output = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            logging.warning(f"Chunk {i} tagging failed: {r}")
            output.append({"tag": DEFAULT_TAG, "confidence": 0.0})
        else:
            output.append(r)

    return output



"""
Memory Nodes for Kogna Agent Graph
===================================

Graph nodes that integrate dual memory system into the agent flow:
1. enrich_with_memory: Fetch relevant memory before specialist
2. extract_and_store_facts: Extract and store facts after response

Version: 1.5 (Enhanced with Truth Maintenance)
"""

import logging
import os
from typing import Dict, Any
from datetime import datetime

# Try to import v1.5, fall back to v1.0 if not available
MEMORY_VERSION = os.getenv("MEMORY_VERSION", "1.5")

try:
    if MEMORY_VERSION == "1.5":
        from services.memory_manager_v15 import get_user_memory, KognaMemoryManagerV15 as KognaMemoryManager
        logger = logging.getLogger(__name__)
        logger.info("✓ Using Kogna Memory v1.5 (Enhanced with Truth Maintenance)")
    else:
        from services.memory_manager import get_user_memory, KognaMemoryManager
        logger = logging.getLogger(__name__)
        logger.info("✓ Using Kogna Memory v1.0")
except ImportError as e:
    # Fallback to v1.0 if v1.5 not available
    from services.memory_manager import get_user_memory, KognaMemoryManager
    logger = logging.getLogger(__name__)
    logger.warning(f"⚠️  Memory v1.5 not available, using v1.0: {e}")
    MEMORY_VERSION = "1.0"


# ============================================================
# MEMORY ENRICHMENT NODE
# ============================================================

async def enrich_with_memory(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich retrieval context with user memory.

    Adds:
    - Relevant past conversations
    - User preferences
    - Business facts (risks, metrics, company context)

    Called AFTER retrieve_context, BEFORE check_data_sufficiency.
    """
    logger.info("--- [Node] Enriching with Memory ---")

    user_id = state.get("user_id")
    query = state.get("query", "")
    session_id = state.get("session_id", "")

    if not user_id:
        logger.warning("No user_id provided, skipping memory enrichment")
        return state

    try:
        # Get memory manager
        memory: KognaMemoryManager = get_user_memory(user_id)

        # Fetch relevant memory context
        # V1.5: Add min_confidence filter to exclude low-quality facts
        if MEMORY_VERSION == "1.5":
            memory_context = await memory.get_context(
                query=query,
                session_id=session_id,
                min_confidence=0.5  # Only retrieve facts with >50% confidence
            )
        else:
            memory_context = await memory.get_context(
                query=query,
                session_id=session_id
            )

        # Add memory to state
        state["memory_context"] = memory_context

        # V1.5: Check for pending conflicts (warn user if needed)
        if MEMORY_VERSION == "1.5" and memory_context.get("pending_conflicts"):
            conflicts = memory_context["pending_conflicts"]
            logger.warning(f"   ⚠️  User has {len(conflicts)} pending memory conflicts")
            state["has_memory_conflicts"] = True
            state["pending_conflicts_count"] = len(conflicts)

        # Format memory for specialist
        memory_summary = _format_memory_for_specialist(memory_context)
        state["memory_summary"] = memory_summary

        # Merge with retrieval context
        state["retrieval_context"] = _merge_memory_with_retrieval(
            retrieval_context=state.get("retrieval_context", []),
            memory_context=memory_context
        )

        # Log what we found
        logger.info(f"   ✓ Memory enriched:")
        logger.info(f"     • {len(memory_context.get('relevant_conversations', []))} relevant conversations")
        logger.info(f"     • {len(memory_context.get('business_facts', []))} business facts")
        logger.info(f"     • {len(memory_context.get('active_risks', []))} active risks")
        logger.info(f"     • {len(memory_context.get('user_preferences', {}))} preferences")

        return state

    except Exception as e:
        logger.error(f"Memory enrichment failed: {e}", exc_info=True)
        # Don't fail the whole pipeline, just skip memory
        state["memory_error"] = str(e)
        return state


def _format_memory_for_specialist(memory_context: Dict) -> str:
    """
    Format memory context into a concise summary for the specialist.

    V1.5: Includes conflict warnings if present.
    """
    parts = []

    # V1.5: Pending Conflicts Warning
    if MEMORY_VERSION == "1.5":
        conflicts = memory_context.get("pending_conflicts", [])
        if conflicts:
            parts.append(f"⚠️ **Memory Conflicts:** {len(conflicts)} facts need verification")

    # User Preferences
    prefs = memory_context.get("user_preferences", {})
    if prefs:
        prefs_str = ", ".join(f"{k}: {v}" for k, v in list(prefs.items())[:5])
        parts.append(f"**User Preferences:** {prefs_str}")

    # Company Context
    company = memory_context.get("company_context", {})
    if company:
        company_str = ", ".join(f"{k}: {v}" for k, v in list(company.items())[:5])
        parts.append(f"**Company Context:** {company_str}")

    # Active Risks
    risks = memory_context.get("active_risks", [])
    if risks:
        risk_count = len(risks)
        high_severity = sum(1 for r in risks if r.get("severity") in ["critical", "high"])
        parts.append(f"**Active Risks:** {risk_count} total ({high_severity} high/critical)")

    # Relevant Past Conversations
    convos = memory_context.get("relevant_conversations", [])
    if convos:
        parts.append(f"**Related Past Discussions:** {len(convos)} relevant conversations")

    # Business Facts
    facts = memory_context.get("business_facts", [])
    if facts:
        parts.append(f"**Known Facts:** {len(facts)} relevant business facts")

    if not parts:
        return "No prior memory context available."

    return "\n".join(parts)


def _merge_memory_with_retrieval(
    retrieval_context: list,
    memory_context: Dict
) -> list:
    """
    Merge memory context into retrieval context for specialist consumption.

    Priority:
    1. Document retrieval (from HierarchicalRetriever)
    2. Business facts (from memory)
    3. Past conversations (from memory)
    """
    merged = retrieval_context.copy()

    # Add business facts as context chunks
    facts = memory_context.get("business_facts", [])
    for fact in facts[:5]:  # Top 5 most relevant
        merged.append({
            "content": f"{fact.get('subject', '')} {fact.get('predicate', '')} {fact.get('value', '')}",
            "score": fact.get("score", 0.7),  # From vector search
            "source_path": "User Memory: Business Fact",
            "source_type": "memory_fact",
            "fact_type": fact.get("fact_type", "unknown"),
            "confidence": fact.get("confidence", 0.8)
        })

    # Add relevant past conversations
    convos = memory_context.get("relevant_conversations", [])
    for convo in convos[:3]:  # Top 3 most relevant
        merged.append({
            "content": f"Previous discussion: {convo.get('query', '')} → {convo.get('response_summary', '')}",
            "score": convo.get("score", 0.6),
            "source_path": "User Memory: Past Conversation",
            "source_type": "memory_conversation",
            "session_id": convo.get("session_id")
        })

    # Add active risks if query is about risks
    risks = memory_context.get("active_risks", [])
    if risks and len(risks) <= 5:  # Only if manageable number
        for risk in risks:
            merged.append({
                "content": f"Known Risk: {risk.get('title', '')} - {risk.get('description', '')} (Severity: {risk.get('severity', 'unknown')})",
                "score": 0.8,  # High relevance for risk queries
                "source_path": "User Memory: Active Risk",
                "source_type": "memory_risk",
                "severity": risk.get("severity"),
                "category": risk.get("category")
            })

    # Add company context (industry, location, business type, etc.)
    company = memory_context.get("company_context", {})
    if company:
        # Format company context as a single context chunk
        company_str = ", ".join(f"{k}: {v}" for k, v in company.items())
        merged.append({
            "content": f"Company Information: {company_str}",
            "score": 0.9,  # High relevance - always useful
            "source_path": "User Memory: Company Context",
            "source_type": "memory_company_context"
        })

    return merged


# ============================================================
# FACT EXTRACTION & STORAGE NODE
# ============================================================

async def extract_and_store_facts(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract facts from the conversation and store in memory.

    Called AFTER format_response, BEFORE END.

    Extracts:
    - Company information
    - Metrics and KPIs
    - Risks
    - Preferences
    - Temporal events
    - Business relationships
    """
    logger.info("--- [Node] Extracting and Storing Facts ---")

    user_id = state.get("user_id")
    session_id = state.get("session_id", "")
    query = state.get("query", "")
    response = state.get("response", "")

    if not user_id or not query or not response:
        logger.warning("Insufficient data for fact extraction, skipping")
        return state

    # Skip fact extraction for non-data questions
    if state.get("intent_type") in ("greeting", "chitchat"):
        logger.info("   ⊗ Skipping extraction for greeting/chitchat")
        return state

    try:
        # Get memory manager
        memory: KognaMemoryManager = get_user_memory(user_id)

        # V1.5: Determine source type (where this data came from)
        source_type = "CHAT"  # Default to conversational extraction
        if state.get("from_pdf_upload"):
            source_type = "PDF"
        elif state.get("from_erp_sync"):
            source_type = "ERP"
        elif state.get("from_api_integration"):
            source_type = "API"
        elif state.get("from_user_upload"):
            source_type = "USER_UPLOAD"

        # Process interaction (stores conversation + extracts facts)
        # V1.5: Pass source_type for authority tracking
        if MEMORY_VERSION == "1.5":
            storage_result = await memory.process_interaction(
                query=query,
                response=response,
                session_id=session_id,
                source_type=source_type,  # ✨ V1.5: Track source
                auto_extract=True
            )
        else:
            storage_result = await memory.process_interaction(
                query=query,
                response=response,
                session_id=session_id,
                auto_extract=True
            )

        # Add to state
        state["facts_extracted"] = storage_result

        # Log what was stored
        logger.info(f"   ✓ Facts extracted and stored:")
        logger.info(f"     • Conversation ID: {storage_result.get('conversation_id', 'N/A')}")
        logger.info(f"     • Facts: {storage_result.get('facts_stored', 0)}")
        logger.info(f"     • Risks: {storage_result.get('risks_stored', 0)}")
        logger.info(f"     • Metrics: {storage_result.get('metrics_stored', 0)}")
        logger.info(f"     • Company Info: {storage_result.get('company_info_stored', 0)}")
        logger.info(f"     • Preferences: {storage_result.get('preferences_learned', 0)}")

        # V1.5: Log truth maintenance results
        if MEMORY_VERSION == "1.5":
            confirmed = storage_result.get('facts_confirmed', 0)
            contested = storage_result.get('facts_contested', 0)

            if confirmed > 0:
                logger.info(f"     • ✓ Confirmed (duplicates): {confirmed}")

            if contested > 0:
                logger.warning(f"     • ⚠️  Contested (conflicts): {contested}")
                conflicts = storage_result.get('conflicts_detected', [])
                logger.warning(f"        Conflict IDs: {conflicts}")

        return state

    except Exception as e:
        logger.error(f"Fact extraction failed: {e}", exc_info=True)
        state["extraction_error"] = str(e)
        return state


# ============================================================
# OPTIONAL: SESSION UPDATE NODE
# ============================================================

async def update_session_context(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update session context with current query topic/filters.

    Optional node - can be used to track session state.
    """
    logger.info("--- [Node] Updating Session Context ---")

    user_id = state.get("user_id")
    session_id = state.get("session_id", "")

    if not user_id:
        return state

    try:
        memory: KognaMemoryManager = get_user_memory(user_id)

        # Extract topic from classification
        topic = state.get("category", "general")

        # Update session
        await memory.memory.conversational.update_session(
            session_id=session_id,
            filters=state.get("active_filters", {}),
            topic=topic
        )

        logger.info(f"   ✓ Session updated: topic={topic}")

        return state

    except Exception as e:
        logger.error(f"Session update failed: {e}")
        return state


# ============================================================
# HELPER: GET MEMORY SUMMARY
# ============================================================

async def get_memory_summary(user_id: str) -> Dict:
    """
    Get a summary of what's stored in memory for a user.

    Useful for debugging/monitoring.
    """
    try:
        memory: KognaMemoryManager = get_user_memory(user_id)
        return await memory.get_summary()
    except Exception as e:
        logger.error(f"Failed to get memory summary: {e}")
        return {"error": str(e)}

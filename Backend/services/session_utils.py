"""
Session utility functions for metadata management and optimization.

Provides helper functions for:
- Session title generation
- Session statistics
- Session updates

Part of multi-session history MVP implementation.
"""

from typing import Optional, Dict, Any
from supabase_connect import get_supabase_manager

supabase = get_supabase_manager().client


def generate_session_title(first_message: str, max_length: int = 50) -> str:
    """
    Generate a session title from the first user message.

    Args:
        first_message: Content of first user message
        max_length: Maximum title length (default 50)

    Returns:
        Truncated title with ellipsis if needed

    Examples:
        >>> generate_session_title("What are our Q4 revenue projections?")
        "What are our Q4 revenue projections?"

        >>> generate_session_title("Can you help me analyze the very long document about market trends and competitive analysis?")
        "Can you help me analyze the very long document..."
    """
    if not first_message:
        return "New Chat"

    # Remove extra whitespace
    cleaned = " ".join(first_message.split())

    if len(cleaned) <= max_length:
        return cleaned

    # Truncate at word boundary
    truncated = cleaned[:max_length].rsplit(' ', 1)[0]
    return f"{truncated}..."


def get_session_stats(user_id: str) -> Dict[str, Any]:
    """
    Get aggregated session statistics for a user.

    Args:
        user_id: UUID of the user

    Returns:
        Dictionary with:
            - total_sessions: Total number of sessions
            - total_messages: Total messages across all sessions
            - avg_messages_per_session: Average messages per session
            - most_active_session_id: Session with most messages (if any)

    Example:
        >>> stats = get_session_stats("123e4567-e89b-12d3-a456-426614174000")
        >>> print(stats)
        {
            'total_sessions': 15,
            'total_messages': 342,
            'avg_messages_per_session': 22.8
        }
    """
    # Count sessions
    session_count_response = supabase.table("sessions") \
        .select("id", count="exact") \
        .eq("user_id", user_id) \
        .execute()

    total_sessions = session_count_response.count or 0

    if total_sessions == 0:
        return {
            'total_sessions': 0,
            'total_messages': 0,
            'avg_messages_per_session': 0.0,
            'most_active_session_id': None
        }

    # Get message counts
    sessions_response = supabase.table("sessions") \
        .select("id, message_count") \
        .eq("user_id", user_id) \
        .execute()

    sessions_data = sessions_response.data if sessions_response.data else []
    total_messages = sum(s.get('message_count', 0) for s in sessions_data)

    # Find most active session
    most_active = max(sessions_data, key=lambda s: s.get('message_count', 0)) if sessions_data else None

    return {
        'total_sessions': total_sessions,
        'total_messages': total_messages,
        'avg_messages_per_session': round(total_messages / total_sessions, 1) if total_sessions > 0 else 0.0,
        'most_active_session_id': most_active['id'] if most_active and most_active.get('message_count', 0) > 0 else None
    }


def update_session_title(session_id: str, user_id: str, new_title: str) -> bool:
    """
    Update session title (user can rename sessions).

    Args:
        session_id: UUID of the session
        user_id: UUID of the user (for authorization)
        new_title: New title to set

    Returns:
        True if successful, False otherwise

    Example:
        >>> success = update_session_title(
        ...     "123e4567-e89b-12d3-a456-426614174000",
        ...     "user-uuid",
        ...     "Q4 Revenue Planning"
        ... )
        >>> print(success)
        True
    """
    if not new_title or not new_title.strip():
        return False

    try:
        result = supabase.table("sessions") \
            .update({"title": new_title.strip()}) \
            .eq("id", session_id) \
            .eq("user_id", user_id) \
            .execute()

        return bool(result.data)
    except Exception:
        return False


def delete_session(session_id: str, user_id: str) -> bool:
    """
    Delete a session and all its messages (soft delete recommended in future).

    Args:
        session_id: UUID of the session
        user_id: UUID of the user (for authorization)

    Returns:
        True if successful, False otherwise

    Note:
        This performs a hard delete. Consider implementing soft delete
        (is_deleted flag) in future for data recovery.
    """
    try:
        # Delete messages first (foreign key constraint)
        supabase.table("messages") \
            .delete() \
            .eq("session_id", session_id) \
            .eq("user_id", user_id) \
            .execute()

        # Delete session
        result = supabase.table("sessions") \
            .delete() \
            .eq("id", session_id) \
            .eq("user_id", user_id) \
            .execute()

        return bool(result.data)
    except Exception:
        return False


def get_session_metadata(session_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed metadata for a session.

    Args:
        session_id: UUID of the session
        user_id: UUID of the user (for authorization)

    Returns:
        Dictionary with session metadata or None if not found

    Example:
        >>> metadata = get_session_metadata("session-uuid", "user-uuid")
        >>> print(metadata['message_count'])
        42
    """
    try:
        result = supabase.table("sessions") \
            .select("id, title, auto_title, preview_text, message_count, created_at, last_message_at") \
            .eq("id", session_id) \
            .eq("user_id", user_id) \
            .maybeSingle() \
            .execute()

        return result.data if result.data else None
    except Exception:
        return None

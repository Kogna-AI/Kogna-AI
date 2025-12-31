# services/conversation_service.py
"""
UPDATED: Conversation Service matching your existing schema

Key differences from my original:
- Uses session_id instead of conversation_id
- Uses key_facts instead of key_decisions
- Uses topics instead of topics_discussed
- Uses entities instead of separate entity types
- Has foreign key to users table
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from supabase_connect import get_supabase_manager
import logging

# Import the conversation note generator
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Ai_agents.conversation_note_agent import (
    ConversationNoteGenerator,
    should_generate_conversation_note,
    extract_referenced_documents
)

supabase = get_supabase_manager().client
logging.basicConfig(level=logging.INFO)

# Initialize generator (singleton)
_conversation_note_generator = None

def get_conversation_note_generator():
    """Get or create conversation note generator instance"""
    global _conversation_note_generator
    if _conversation_note_generator is None:
        _conversation_note_generator = ConversationNoteGenerator()
        logging.info(" Conversation note generator initialized")
    return _conversation_note_generator


# ============================================================
# CONVERSATION NOTE GENERATION
# ============================================================

async def generate_and_store_conversation_note(
    user_id: str,
    session_id: str,  # ← Changed from conversation_id
    conversation_history: List[Dict[str, str]],
    force: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Generate and store a conversation note.
    
    Args:
        user_id: User ID
        session_id: Session ID (your schema uses this instead of conversation_id)
        conversation_history: List of messages [{"role": "user/assistant", "content": "..."}]
        force: Force generation even if criteria not met
        
    Returns:
        Generated note or None if not generated
    """
    
    # Check if we should generate a note
    if not force and not should_generate_conversation_note(conversation_history):
        logging.info(f"  Skipping note generation for {session_id} (criteria not met)")
        return None
    
    logging.info(f" Generating conversation note for {session_id}...")
    
    try:
        # Get previous notes for context
        previous_notes = await get_recent_conversation_notes(user_id, limit=3)
        
        user_context = {
            'previous_notes': previous_notes
        }
        
        # Generate note
        generator = get_conversation_note_generator()
        note_data = generator.generate_note(
            conversation_history=conversation_history,
            conversation_id=session_id,  # Agent still uses this param name
            user_context=user_context
        )
        
        # Try to link to document notes
        document_notes = await get_user_document_notes(user_id)
        referenced_doc_ids = extract_referenced_documents(
            conversation_history,
            document_notes
        )
        
        # Map the fields to YOUR schema
        mapped_note_data = {
            'session_id': session_id,  # ← Your field name
            'title': note_data['title'],
            'summary': note_data['summary'],
            'user_perspective': note_data.get('user_perspective', ''),
            'key_facts': note_data.get('key_points', []),  # ← Map key_points to key_facts
            'action_items': note_data.get('action_items', []),
            'topics': note_data.get('topics_discussed', []),  # ← Map to topics
            'entities': note_data.get('entities', {}),
            'message_count': note_data.get('message_count', 0),
            'linked_document_notes': referenced_doc_ids  # Store in entities for now
        }
        
        # Store in database
        stored_note = await store_conversation_note(user_id, mapped_note_data)
        
        logging.info(f" Conversation note created: {note_data['title']}")
        logging.info(f"   • User perspective: {note_data.get('user_perspective', 'N/A')}")
        logging.info(f"   • Topics: {mapped_note_data.get('topics', [])}")
        logging.info(f"   • Linked documents: {len(referenced_doc_ids)}")
        
        return stored_note
        
    except Exception as e:
        logging.error(f" Failed to generate conversation note: {e}")
        import traceback
        traceback.print_exc()
        return None


async def store_conversation_note(
    user_id: str,
    note_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Store conversation note in database using YOUR schema.
    
    Args:
        user_id: User ID
        note_data: Note data (already mapped to your schema)
        
    Returns:
        Stored note with ID
    """
    
    # Prepare record matching YOUR schema
    record = {
        'user_id': user_id,
        'session_id': note_data['session_id'],  # ← Your field
        'title': note_data['title'],
        'summary': note_data['summary'],
        'user_perspective': note_data.get('user_perspective', ''),
        'key_facts': note_data.get('key_facts', []),  # ← Your field
        'action_items': note_data.get('action_items', []),
        'topics': note_data.get('topics', []),  # ← Your field
        'entities': note_data.get('entities', {}),
        'message_count': note_data.get('message_count', 0)
        # search_vector is auto-generated by your GENERATED ALWAYS column
        # created_at and updated_at have defaults
    }
    
    try:
        # Check if note already exists for this session
        existing = supabase.table('conversation_notes')\
            .select('id')\
            .eq('user_id', user_id)\
            .eq('session_id', note_data['session_id'])\
            .execute()
        
        if existing.data:
            # Update existing note
            result = supabase.table('conversation_notes')\
                .update(record)\
                .eq('id', existing.data[0]['id'])\
                .execute()
            
            logging.info(f" Updated existing conversation note: {existing.data[0]['id']}")
        else:
            # Insert new note
            result = supabase.table('conversation_notes')\
                .insert(record)\
                .execute()
            
            logging.info(f" Created new conversation note")
        
        return result.data[0] if result.data else None
        
    except Exception as e:
        logging.error(f" Failed to store conversation note: {e}")
        raise


# ============================================================
# CONVERSATION NOTE RETRIEVAL
# ============================================================

async def get_recent_conversation_notes(
    user_id: str,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Get user's most recent conversation notes.
    
    Args:
        user_id: User ID
        limit: Number of notes to retrieve
        
    Returns:
        List of conversation notes
    """
    try:
        result = supabase.table('conversation_notes')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .limit(limit)\
            .execute()
        
        return result.data or []
        
    except Exception as e:
        logging.error(f"Failed to get recent conversation notes: {e}")
        return []


async def get_conversation_note(
    user_id: str,
    session_id: str  # ← Changed from conversation_id
) -> Optional[Dict[str, Any]]:
    """
    Get note for specific session.
    
    Args:
        user_id: User ID
        session_id: Session ID
        
    Returns:
        Conversation note or None
    """
    try:
        result = supabase.table('conversation_notes')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('session_id', session_id)\
            .maybe_single()\
            .execute()
        
        return result.data
        
    except Exception as e:
        logging.error(f"Failed to get conversation note: {e}")
        return None


async def search_conversation_notes(
    user_id: str,
    query: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search conversation notes by text query using your search_vector.
    
    Args:
        user_id: User ID
        query: Search query
        limit: Max results
        
    Returns:
        List of matching conversation notes
    """
    try:
        # Use full-text search on your auto-generated search_vector
        result = supabase.table('conversation_notes')\
            .select('*, ts_rank(search_vector, plainto_tsquery($1)) as rank')\
            .eq('user_id', user_id)\
            .textSearch('search_vector', query, config='english')\
            .order('rank', desc=True)\
            .limit(limit)\
            .execute()
        
        return result.data or []
        
    except Exception as e:
        logging.error(f"Failed to search conversation notes: {e}")
        # Fallback to simple search if full-text fails
        try:
            result = supabase.table('conversation_notes')\
                .select('*')\
                .eq('user_id', user_id)\
                .or_(f'title.ilike.%{query}%,summary.ilike.%{query}%')\
                .limit(limit)\
                .execute()
            return result.data or []
        except:
            return []


async def get_notes_by_topic(
    user_id: str,
    topic: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Get conversation notes about specific topic using your topics JSONB field.
    
    Args:
        user_id: User ID
        topic: Topic to search for
        limit: Max results
        
    Returns:
        List of notes about topic
    """
    try:
        # Use JSONB contains operator
        result = supabase.table('conversation_notes')\
            .select('*')\
            .eq('user_id', user_id)\
            .contains('topics', [topic])\
            .order('created_at', desc=True)\
            .limit(limit)\
            .execute()
        
        return result.data or []
        
    except Exception as e:
        logging.error(f"Failed to get notes by topic: {e}")
        return []


async def get_user_context(user_id: str) -> Dict[str, Any]:
    """
    Get comprehensive user context from conversation notes.
    
    This provides context about what the user cares about,
    their concerns, and priorities based on past conversations.
    
    Args:
        user_id: User ID
        
    Returns:
        {
            "recent_notes": [...],
            "key_concerns": [...],
            "common_topics": [...],
            "user_priorities": "..."
        }
    """
    try:
        # Get recent notes
        recent_notes = await get_recent_conversation_notes(user_id, limit=10)
        
        if not recent_notes:
            return {
                "recent_notes": [],
                "key_concerns": [],
                "common_topics": [],
                "user_priorities": ""
            }
        
        # Extract key concerns (from user_perspective)
        key_concerns = []
        for note in recent_notes:
            perspective = note.get('user_perspective', '')
            if perspective:
                key_concerns.append(perspective)
        
        # Extract common topics
        all_topics = []
        for note in recent_notes:
            topics = note.get('topics', [])  # ← Your field name
            if isinstance(topics, list):
                all_topics.extend(topics)
        
        # Count topic frequency
        from collections import Counter
        topic_counts = Counter(all_topics)
        common_topics = [topic for topic, count in topic_counts.most_common(5)]
        
        # Build user priorities summary
        user_priorities = ""
        if key_concerns:
            user_priorities = "User has expressed concern about: " + "; ".join(key_concerns[:3])
        
        return {
            "recent_notes": recent_notes[:5],
            "key_concerns": key_concerns[:3],
            "common_topics": common_topics,
            "user_priorities": user_priorities
        }
        
    except Exception as e:
        logging.error(f"Failed to get user context: {e}")
        return {
            "recent_notes": [],
            "key_concerns": [],
            "common_topics": [],
            "user_priorities": ""
        }


# ============================================================
# HELPER FUNCTIONS
# ============================================================

async def get_user_document_notes(user_id: str) -> List[Dict[str, Any]]:
    """Get user's document notes for linking"""
    try:
        result = supabase.table('document_notes')\
            .select('id, title, topics_discussed')\
            .eq('user_id', user_id)\
            .limit(100)\
            .execute()
        
        return result.data or []
        
    except Exception as e:
        logging.error(f"Failed to get document notes: {e}")
        return []


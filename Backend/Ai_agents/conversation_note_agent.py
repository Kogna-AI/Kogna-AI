# Ai_agents/conversation_note_agent.py
"""
Conversation Note Generator Agent

Analyzes user conversations and generates intelligent notes that capture:
- What the user asked about
- User's concerns and perspective
- Key decisions made
- Topics discussed
- Links to referenced documents
"""

import os
import json
from typing import List, Dict, Any, Optional
from crewai import Agent, Task, Crew
from Ai_agents.llm_factory import get_llm_for_agent
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# AGENT CONFIGURATION
# ============================================================

CONVERSATION_ANALYST_ROLE = "Conversation Intelligence Analyst"

CONVERSATION_ANALYST_GOAL = (
    "Analyze user conversations to extract insights, perspective, and context"
)

CONVERSATION_ANALYST_BACKSTORY = """You are an expert at understanding conversations and 
extracting the underlying user perspective, concerns, and priorities. 
You don't just summarize what was said - you understand what the user 
cares about, what they're worried about, and what matters to them."""

CONVERSATION_ANALYST_TASK_DESCRIPTION = """Analyze this conversation and extract key insights.

Conversation:
{conversation_text}
{context_info}

You must provide a JSON response with EXACTLY this structure:
{{
    "title": "Brief title summarizing the conversation (e.g., 'User Inquiry: Q4 Financial Planning')",
    "summary": "2-3 sentence summary of what was discussed",
    "user_perspective": "What is the user concerned about? What do they prioritize? What matters to them? (1-2 sentences)",
    "key_facts": ["List any key facts or decisions mentioned", "Keep it practical"],
    "action_items": ["List any action items or next steps", "Be specific"],
    "topics": ["List 3-5 main topics as single words or short phrases"],
    "questions_asked": ["List the main questions the user asked"],
    "entities": {{
        "people": ["List people mentioned"],
        "companies": ["List companies mentioned"],
        "dates": ["List dates mentioned"],
        "metrics": ["List metrics/numbers mentioned"]
    }}
}}

CRITICAL RULES:
1. user_perspective should capture the USER'S view, not just facts
   - Good: "User is concerned about expenses growing faster than revenue"
   - Bad: "Expenses increased 15% in Q3"
2. topics should be searchable keywords
   - Good: ["finances", "Q4", "budget", "expenses"]
   - Bad: ["the financial situation", "quarterly planning"]
3. questions_asked should be the actual questions, not topics
   - Good: ["What's our expense trend?", "Can we reduce costs?"]
   - Bad: ["expenses", "cost reduction"]
4. Respond ONLY with valid JSON, no other text
5. Do not include markdown code fences (```json)
"""

CONVERSATION_ANALYST_EXPECTED_OUTPUT = "JSON object with conversation analysis"


# ============================================================
# CONVERSATION NOTE GENERATOR CLASS
# ============================================================

class ConversationNoteGenerator:
    """
    Generates intelligent notes from user conversations.
    
    This captures not just what was discussed, but:
    - User's perspective and concerns
    - Their priorities and goals
    - Decisions they made
    - What they care about
    """
    
    def __init__(self):
        """Initialize the conversation note generator"""
        self.llm = get_llm_for_agent(agent_name="some agent", user_id=user_id,temperature_override=0.3)
        
        # Create the analyst agent
        self.analyst = Agent(
            role=CONVERSATION_ANALYST_ROLE,
            goal=CONVERSATION_ANALYST_GOAL,
            backstory=CONVERSATION_ANALYST_BACKSTORY,
            llm=self.llm,
            verbose=False
        )
    
    def generate_note(
        self,
        conversation_history: List[Dict[str, str]],
        conversation_id: str,
        user_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate a note from conversation history.
        
        Args:
            conversation_history: List of messages [{"role": "user/assistant", "content": "..."}]
            conversation_id: Unique conversation identifier
            user_context: Optional context about user (previous notes, preferences)
            
        Returns:
            {
                "title": "User Inquiry: Q4 Financial Planning",
                "summary": "User asked about Q4 budget allocation...",
                "user_perspective": "User is concerned about expense growth...",
                "key_facts": ["Revenue increased 10%", "Decided to review contracts"],
                "action_items": ["Review vendor contracts", "Schedule CFO meeting"],
                "topics": ["finances", "budget", "Q4", "expenses"],
                "questions_asked": ["What's our expense trend?", "Can we reduce costs?"],
                "entities": {
                    "people": ["John", "CFO"],
                    "companies": ["Vendor Corp"],
                    "dates": ["Q4 2024"],
                    "metrics": ["$2M revenue", "15% growth"]
                }
            }
        """
        
        # Format conversation for analysis
        conversation_text = self._format_conversation(conversation_history)
        
        # Build context
        context_info = ""
        if user_context:
            previous_notes = user_context.get('previous_notes', [])
            if previous_notes:
                context_info = f"\n\nUser's Previous Concerns:\n"
                for note in previous_notes[:3]:  # Last 3 notes
                    context_info += f"- {note.get('user_perspective', 'N/A')}\n"
        
        # Create analysis task
        analysis_task = Task(
            description=CONVERSATION_ANALYST_TASK_DESCRIPTION.format(
                conversation_text=conversation_text,
                context_info=context_info
            ),
            expected_output=CONVERSATION_ANALYST_EXPECTED_OUTPUT,
            agent=self.analyst
        )
        
        # Create crew and execute
        crew = Crew(
            agents=[self.analyst],
            tasks=[analysis_task],
            verbose=False
        )
        
        try:
            result = crew.kickoff()
            
            # Extract JSON from result
            result_str = str(result)
            
            # Clean up result (remove markdown fences if present)
            result_str = result_str.strip()
            if result_str.startswith('```json'):
                result_str = result_str[7:]
            if result_str.startswith('```'):
                result_str = result_str[3:]
            if result_str.endswith('```'):
                result_str = result_str[:-3]
            result_str = result_str.strip()
            
            # Parse JSON
            note_data = json.loads(result_str)
            
            # Add metadata
            note_data['conversation_id'] = conversation_id
            note_data['message_count'] = len(conversation_history)
            
            return note_data
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON from conversation note: {e}")
            print(f"Raw result: {result}")
            
            # Fallback: Create basic note
            return self._create_fallback_note(conversation_history, conversation_id)
        
        except Exception as e:
            print(f"Error generating conversation note: {e}")
            import traceback
            traceback.print_exc()
            return self._create_fallback_note(conversation_history, conversation_id)
    
    def _format_conversation(self, history: List[Dict[str, str]]) -> str:
        """Format conversation history for analysis"""
        formatted = []
        for msg in history:
            role = "User" if msg['role'] == 'user' else "Assistant"
            content = msg['content']
            formatted.append(f"{role}: {content}")
        return "\n\n".join(formatted)
    
    def _create_fallback_note(
        self,
        conversation_history: List[Dict[str, str]],
        conversation_id: str
    ) -> Dict[str, Any]:
        """Create a basic note if AI generation fails"""
        
        # Extract user messages
        user_messages = [msg['content'] for msg in conversation_history if msg['role'] == 'user']
        
        # Create simple summary
        first_question = user_messages[0] if user_messages else "Conversation"
        
        return {
            "conversation_id": conversation_id,
            "title": f"Conversation: {first_question[:50]}...",
            "summary": f"User had a conversation with {len(conversation_history)} messages.",
            "user_perspective": "Unable to analyze - manual review needed",
            "key_facts": [],
            "action_items": [],
            "topics": [],
            "questions_asked": user_messages[:3],
            "entities": {
                "people": [],
                "companies": [],
                "dates": [],
                "metrics": []
            },
            "message_count": len(conversation_history)
        }


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def should_generate_conversation_note(
    conversation_history: List[Dict[str, str]],
    conversation_metadata: Dict[str, Any] = None
) -> bool:
    """
    Determine if we should generate a note for this conversation.
    
    Generate note when:
    - Conversation has 5+ messages
    - User explicitly saves conversation
    - User ends conversation (closes chat)
    - Conversation touches important topics (finance, planning, decisions)
    """
    
    # Check message count
    if len(conversation_history) < 5:
        return False
    
    # Check if user saved conversation
    if conversation_metadata and conversation_metadata.get('user_saved'):
        return True
    
    # Check if conversation ended
    if conversation_metadata and conversation_metadata.get('conversation_ended'):
        return True
    
    # Check for important keywords in user messages
    important_keywords = [
        'budget', 'cost', 'expense', 'revenue', 'finance', 'financial',
        'plan', 'planning', 'strategy', 'decision', 'decide',
        'concern', 'worried', 'issue', 'problem', 'risk'
    ]
    
    user_messages = [
        msg['content'].lower() 
        for msg in conversation_history 
        if msg['role'] == 'user'
    ]
    
    conversation_text = ' '.join(user_messages)
    
    for keyword in important_keywords:
        if keyword in conversation_text:
            return True
    
    return False


def extract_referenced_documents(
    conversation_history: List[Dict[str, str]],
    available_document_notes: List[Dict[str, Any]]
) -> List[str]:
    """
    Find which document notes were referenced in the conversation.
    
    Returns list of document note IDs that were discussed.
    """
    referenced_ids = []
    
    # Get assistant messages (which contain document references)
    assistant_messages = [
        msg['content'].lower() 
        for msg in conversation_history 
        if msg['role'] == 'assistant'
    ]
    
    conversation_text = ' '.join(assistant_messages)
    
    # Check each document note
    for doc_note in available_document_notes:
        # Check if document title or key topics appear in conversation
        title = doc_note.get('title', '').lower()
        topics = doc_note.get('topics_discussed', [])
        
        # Check title match
        if title and title in conversation_text:
            referenced_ids.append(doc_note['id'])
            continue
        
        # Check topic matches
        topic_matches = sum(1 for topic in topics if topic.lower() in conversation_text)
        if topic_matches >= 2:  # At least 2 topic matches
            referenced_ids.append(doc_note['id'])
    
    return referenced_ids



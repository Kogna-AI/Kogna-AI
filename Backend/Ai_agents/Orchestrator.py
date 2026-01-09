import os
from dotenv import load_dotenv
from typing import TypedDict, Optional, List
import json
import asyncio
from langgraph.graph import StateGraph, END
from supabase_connect import get_supabase_manager 
import logging
from langchain_litellm import ChatLiteLLM
import re
from .prompt import TRIAGE_PROMPT, GENERAL_ANSWER_PROMPT
from .retry_utils import retry_with_backoff, RetryConfig, retry_llm_call

# ✨ NEW: Import hierarchical retriever
from services.hierarchical_retriever import HierarchicalRetriever

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Supabase Setup ---
try:
    supabase_manager = get_supabase_manager()
    supabase = supabase_manager.client
except Exception as e:
    logging.error(f"Failed to initialize Supabase client: {e}")
    supabase = None

# Import your existing crew creation functions
from Ai_agents.internal_analyst_agent import create_internal_analyst_crew
from Ai_agents.reasearch_agent import create_research_crew
from Ai_agents.synthesize_agent import create_synthesis_crew
from Ai_agents.communication_agent import create_communication_crew
from services.conversation_service import generate_and_store_conversation_note, get_user_context

# --- Configure retry settings ---
LLM_RETRY_CONFIG = RetryConfig(
    max_retries=5,
    initial_delay=1.0,
    max_delay=60.0,
    exponential_base=2.0,
    jitter=True
)

CREW_RETRY_CONFIG = RetryConfig(
    max_retries=3,
    initial_delay=2.0,
    max_delay=90.0,
    exponential_base=2.0,
    jitter=True
)

# --- 1. Define the State for the Graph (UPDATED) ---
class WorkflowState(TypedDict):
    user_id: str
    organization_id: Optional[str]  # <-- Organization UUID for KPI queries
    session_id: Optional[str] # <-- Key to link history
    query_classification: Optional[str]
    query_scope: Optional[str]  # ✨ NEW: "broad", "specific", "mixed"
    user_query: str
    execution_mode: str
    chat_history: Optional[List[str]]
    
    # ✨ NEW: Hierarchical retrieval results
    retrieval_results: Optional[dict]  # Results from tree + vector search
    retrieval_strategy: Optional[str]  # Which strategy was used
    
    # Existing fields
    internal_sources: Optional[List[str]]
    internal_analysis_report: Optional[str]
    business_research_findings: Optional[str]
    synthesis_report: Optional[str]
    final_report: Optional[str]
    error_message: Optional[str]
    human_feedback: Optional[str] 


# -----------------------------------------------------------------
# --- Supabase Helper Function with Retry ---
# -----------------------------------------------------------------
@retry_with_backoff(RetryConfig(max_retries=3, initial_delay=0.5, max_delay=10.0))
def fetch_chat_history_for_session(session_id: str) -> List[str]:
    """
    Fetches past messages for a given session from Supabase.
    """
    if not supabase:
        logging.error("Supabase client not available.")
        return []
    
    response = supabase.table("messages") \
        .select("role, content") \
        .eq("session_id", session_id) \
        .order("created_at", desc=False) \
        .execute()
    
    history = response.data
    
    formatted_history = [
        f"{msg['role']}: {msg['content']}" 
        for msg in history
    ]
    
    logging.info(f"Loaded {len(formatted_history)} history items for session {session_id}.")
    return formatted_history


# -----------------------------------------------------------------
# --- NODE: Load Chat History ---
# -----------------------------------------------------------------
def node_load_history(state: WorkflowState) -> dict:
    print("\n--- [Node] Loading Chat History ---")
    session_id = state.get("session_id")
    
    if session_id:
        try:
            history = fetch_chat_history_for_session(session_id)
            return {"chat_history": history}
        except Exception as e:
            logging.error(f"Failed to load chat history: {e}")
            return {"chat_history": []}
    
    print("--- [Info] No session_id. Starting with empty history. ---")
    return {"chat_history": []}


# -----------------------------------------------------------------
# --- Helper: LLM Calls with Retry ---
# -----------------------------------------------------------------
@retry_llm_call
def call_llm_with_retry(model: str, api_key: str, prompt: str, temperature: float = 0.0) -> str:
    """
    Wrapper for LLM calls with automatic retry.
    """
    llm = ChatLiteLLM(
        model=model,
        api_key=api_key,
        temperature=temperature
    )
    response = llm.invoke(prompt)
    return response.content.strip()


# -----------------------------------------------------------------
# --- ✨ NEW NODE: Classify Query Scope ---
# -----------------------------------------------------------------
def node_classify_query_scope(state: WorkflowState) -> dict:
    """
    Classifies whether query is broad (high-level overview) or 
    specific (detailed information).
    
    This determines which tree levels to search.
    """
    print("\n--- [Node] Classifying Query Scope ---")
    
    user_query = state['user_query'].lower()
    
    # Keywords indicating broad queries
    broad_keywords = [
        'overview', 'summary', 'overall', 'generally', 'main', 
        'key', 'themes', 'strategic', 'big picture', 'what are',
        'tell me about', 'explain', 'describe', 'strategy'
    ]
    
    # Keywords indicating specific queries
    specific_keywords = [
        'exact', 'specific', 'how much', 'when', 'who', 'where',
        'which', 'cost', 'price', 'date', 'number', 'list',
        'show me', 'find', 'what was', 'details'
    ]
    
    broad_count = sum(1 for kw in broad_keywords if kw in user_query)
    specific_count = sum(1 for kw in specific_keywords if kw in user_query)
    
    if broad_count > specific_count:
        scope = "broad"
        print(f"--- [Info] Query scope: BROAD (search high-level super-notes) ---")
    elif specific_count > broad_count:
        scope = "specific"
        print(f"--- [Info] Query scope: SPECIFIC (search detailed leaf notes) ---")
    else:
        scope = "mixed"
        print(f"--- [Info] Query scope: MIXED (search all levels) ---")
    
    return {"query_scope": scope}


# -----------------------------------------------------------------
# --- NODE: Triage Query (UPDATED) ---
# -----------------------------------------------------------------
def node_triage_query(state: WorkflowState) -> dict:
    print("\n--- [Node] Triaging Query ---")
    user_query = state['user_query']
    chat_history = state.get("chat_history", []) 
    history_str = "\n".join(chat_history)

    try:
        prompt = TRIAGE_PROMPT.format(history_str=history_str, user_query=user_query)
        
        classification = call_llm_with_retry(
            model="gemini/gemini-2.0-flash",
            api_key=os.getenv("GOOGLE_API_KEY"),
            prompt=prompt,
            temperature=0.0
        ).lower()

        if "general_conversation" in classification:
            print("--- [Info] Query classified as: general_conversation ---")
            return {"query_classification": "general_conversation"}
        else:
            print("--- [Info] Query classified as: data_request ---")
            return {"query_classification": "data_request"}

    except Exception as e:
        print(f"--- [Error] Triage failed: {e}. Defaulting to data_request. ---")
        logging.error(f"Triage error: {e}", exc_info=True)
        return {"query_classification": "data_request"}


# -----------------------------------------------------------------
# --- NODE: Answer General Query (UPDATED) ---
# -----------------------------------------------------------------
def node_answer_general_query(state: WorkflowState) -> dict:
    print("\n--- [Node] Answering General Query ---")
    user_query = state['user_query']

    try:
        prompt = GENERAL_ANSWER_PROMPT.format(user_query=user_query)
        
        response = call_llm_with_retry(
            model="gemini/gemini-2.0-flash",
            api_key=os.getenv("GOOGLE_API_KEY"),
            prompt=prompt,
            temperature=0.7
        )
        
        return {"final_report": response}

    except Exception as e:
        print(f"--- [Error] General chat failed: {e} ---")
        logging.error(f"General chat error: {e}", exc_info=True)
        return {
            "final_report": "I'm having trouble connecting right now. Please try again."
        }


# -----------------------------------------------------------------
# --- DECISION: After Triage ---
# -----------------------------------------------------------------
def decide_after_triage(state: WorkflowState) -> str:
    """Routes based on query classification."""
    print("\n--- [Decision] Routing based on Triage ---")
    
    if state.get("query_classification") == "general_conversation":
        return "answer_general_query"
    else:
        return "classify_scope"  # ✨ NEW: Classify before retrieval


# -----------------------------------------------------------------
# --- ✨ NEW NODE: Hierarchical Retrieval ---
# -----------------------------------------------------------------
async def node_hierarchical_retrieval(state: WorkflowState) -> dict:
    """
    Uses HierarchicalRetriever to search the tree + leaf notes.
    
    Strategy based on query scope:
    - Broad: Search root + Level 2 (themes)
    - Specific: Search Level 1 + leaves (details)
    - Mixed: Hybrid search (all levels)
    """
    print("\n--- [Node] Hierarchical Retrieval ---")
    
    user_id = state.get("user_id")
    user_query = state.get("user_query")
    query_scope = state.get("query_scope", "mixed")
    
    if not user_id:
        print("--- [Error] user_id missing ---")
        return {
            "retrieval_results": None,
            "retrieval_strategy": "error"
        }
    
    try:
        # Initialize retriever
        retriever = HierarchicalRetriever(user_id)
        
        # Determine strategy based on scope
        if query_scope == "broad":
            strategy = "tree_first"
            max_results = 5
            print(f"   Strategy: TREE_FIRST (high-level overview)")
        elif query_scope == "specific":
            strategy = "hybrid"  # Still hybrid, but will prioritize leaves
            max_results = 10
            print(f"   Strategy: HYBRID (detailed information)")
        else:
            strategy = "hybrid"
            max_results = 10
            print(f"   Strategy: HYBRID (comprehensive search)")
        
        # Execute retrieval
        print(f"   Query: {user_query[:60]}...")
        
        retrieval_result = await retriever.retrieve(
            query=user_query,
            max_results=max_results,
            strategy=strategy
        )
        
        results = retrieval_result.get('results', [])
        
        print(f"   ✓ Retrieved {len(results)} results")
        print(f"     Levels searched: {retrieval_result.get('levels_searched', [])}")
        
        # Log what we found
        if results:
            level_distribution = {}
            for r in results:
                level = r.get('level', 0)
                level_distribution[level] = level_distribution.get(level, 0) + 1
            
            print(f"     Distribution: {level_distribution}")
        
        return {
            "retrieval_results": retrieval_result,
            "retrieval_strategy": strategy
        }
        
    except Exception as e:
        print(f"--- [Error] Retrieval failed: {e} ---")
        logging.error(f"Hierarchical retrieval error: {e}", exc_info=True)
        return {
            "retrieval_results": None,
            "retrieval_strategy": "error"
        }


# -----------------------------------------------------------------
# --- ✨ UPDATED NODE: Internal Analyst (uses tree results + KPI queries) ---
# -----------------------------------------------------------------
@retry_with_backoff(CREW_RETRY_CONFIG)
def _run_internal_analyst_with_tree(
    user_id: str,
    organization_id: str,
    user_query: str,
    chat_history_str: str,
    retrieval_results: dict
):
    """
    Enhanced internal analyst that uses hierarchical retrieval results and KPI queries.
    """
    google_key = os.getenv("GOOGLE_API_KEY")

    # Format retrieval results for the analyst
    formatted_context = _format_retrieval_results(retrieval_results)

    # Add to chat history
    enhanced_history = f"""
CONTEXT FROM KNOWLEDGE BASE:
{formatted_context}

CONVERSATION HISTORY:
{chat_history_str}
    """.strip()

    internal_analyst_crew = create_internal_analyst_crew(
        gemini_api_key=google_key,
        user_id=user_id,
        organization_id=organization_id
    )

    inputs = {
        'user_query': user_query,
        'chat_history_str': enhanced_history
    }

    analysis_result = internal_analyst_crew.kickoff(inputs=inputs)
    return analysis_result.raw


def _format_retrieval_results(retrieval_results: dict) -> str:
    """
    Format hierarchical retrieval results for LLM consumption.
    """
    if not retrieval_results or not retrieval_results.get('results'):
        return "No relevant information found in knowledge base."
    
    results = retrieval_results['results']
    strategy = retrieval_results.get('strategy_used', 'unknown')
    
    formatted_parts = [
        f"Retrieved using {strategy.upper()} strategy:",
        ""
    ]
    
    for i, result in enumerate(results[:10], 1):  # Top 10 results
        level = result.get('level', 0)
        
        # Level indicator
        if level == 99:
            level_label = "📚 OVERVIEW"
        elif level == 2:
            level_label = "📖 THEME"
        elif level == 1:
            level_label = "📄 TOPIC"
        else:
            level_label = "📝 DETAIL"
        
        title = result.get('title', 'Untitled')
        summary = result.get('summary', '')[:500]  # Limit length
        relevance = result.get('final_score', result.get('similarity', 0))
        
        formatted_parts.append(f"""
[Source {i}] {level_label}
Title: {title}
Relevance: {relevance:.2f}

{summary}

---
        """.strip())
    
    return "\n\n".join(formatted_parts)


def node_internal_analyst(state: WorkflowState) -> dict:
    """
    UPDATED: Now uses hierarchical retrieval results + KPI queries!
    """
    print("\n--- [Node] Executing Internal Analyst (with Tree + KPI Query) ---")
    user_id = state.get("user_id")
    organization_id = state.get("organization_id")

    if not user_id:
        print("--- [Error] user_id missing ---")
        return {"internal_analysis_report": "Error: user_id is missing."}

    if not organization_id:
        print("--- [Warning] organization_id is missing from state - KPI queries may fail ---")
        # Don't fail completely, but KPI tool won't work without organization_id
        organization_id = ""

    try:
        # Get user context from past conversations
        user_context = None
        try:
            user_context = asyncio.run(get_user_context(user_id))

            if user_context and user_context.get('user_priorities'):
                print(f"--- [Info] User context loaded ---")
        except Exception as ctx_error:
            logging.warning(f"Could not load user context: {ctx_error}")

        # Build chat history
        chat_history_str = "\n".join(state.get("chat_history", []))

        # Add user context if available
        if user_context and user_context.get('user_priorities'):
            context_prefix = f"""
USER CONTEXT (from past conversations):
{user_context['user_priorities']}

Common topics: {', '.join(user_context.get('common_topics', []))}

Recent concerns:
{chr(10).join(f"- {concern}" for concern in user_context.get('key_concerns', [])[:3])}

---
"""
            chat_history_str = context_prefix + chat_history_str

        # Get retrieval results
        retrieval_results = state.get("retrieval_results")

        if not retrieval_results:
            print("--- [Warning] No retrieval results available ---")
            retrieval_results = {"results": [], "strategy_used": "none"}

        # Run analyst with tree context + KPI queries
        analysis_report = _run_internal_analyst_with_tree(
            user_id=user_id,
            organization_id=organization_id,
            user_query=state['user_query'],
            chat_history_str=chat_history_str,
            retrieval_results=retrieval_results
        )

        print(f"--- [Node] Internal Analyst finished ---")
        return {"internal_analysis_report": analysis_report}

    except Exception as e:
        error_msg = f"Internal analysis failed: {str(e)[:200]}"
        print(f"--- [Error] {error_msg} ---")
        logging.error(f"Internal analyst error: {e}", exc_info=True)
        return {"internal_analysis_report": f"Error: {error_msg}"}


# -----------------------------------------------------------------
# --- EXISTING NODES (Unchanged) ---
# -----------------------------------------------------------------

@retry_with_backoff(CREW_RETRY_CONFIG)
def _run_research_with_validation(user_query: str, google_api_key: str, serper_api_key: str):
    """Helper function to run research with retry logic."""
    from Ai_agents.reasearch_agent import run_research_with_validation
    
    return run_research_with_validation(
        user_query=user_query,
        google_api_key=google_api_key,
        serper_api_key=serper_api_key,
        max_validation_retries=2
    )


def node_researcher(state: WorkflowState) -> dict:
    """Web research node (unchanged)."""
    print("\n--- [Node] Executing Research Crew ---")
    
    google_key = os.getenv("GOOGLE_API_KEY")
    serper_key = os.getenv("SERPAPI_API_KEY")
    
    if not serper_key or not google_key:
        print("--- [Warning] Missing API keys. Skipping research. ---")
        return {"business_research_findings": "Research skipped."}

    try:
        research_findings = _run_research_with_validation(
            user_query=state['user_query'],
            google_api_key=google_key,
            serper_api_key=serper_key
        )
        
        print(f"--- [Node] Research completed ---")
        return {"business_research_findings": research_findings}
            
    except Exception as e:
        print(f"--- [Error] Research failed: {str(e)[:200]} ---")
        logging.error(f"Research error: {e}", exc_info=True)
        return {
            "business_research_findings": "Research temporarily unavailable."
        }


@retry_with_backoff(CREW_RETRY_CONFIG)
def _run_synthesis_crew(
    internal_analysis_report: str, 
    internal_sources: Optional[List[str]], 
    business_research_findings: str, 
    google_api_key: str, 
    human_feedback: Optional[str]
):
    """Synthesis crew (unchanged)."""
    synthesizer_crew = create_synthesis_crew(
        internal_analysis_report=internal_analysis_report,
        internal_sources=internal_sources,
        business_research_findings=business_research_findings,
        google_api_key=google_api_key,
        human_feedback=human_feedback
    )
    synthesis_result = synthesizer_crew.kickoff()
    return synthesis_result.raw


def node_synthesizer(state: WorkflowState) -> dict:
    print("\n--- [Node] Executing Synthesizer Crew ---")
    google_key = os.getenv("GOOGLE_API_KEY")
    
    human_feedback = state.get("human_feedback")
    
    try:
        synthesis_report = _run_synthesis_crew(
            internal_analysis_report=state['internal_analysis_report'],
            internal_sources=state.get('internal_sources'),
            business_research_findings=state['business_research_findings'],
            google_api_key=google_key,
            human_feedback=human_feedback
        )
        
        return {"synthesis_report": synthesis_report, "human_feedback": None}
        
    except Exception as e:
        error_msg = f"Synthesis failed: {str(e)[:200]}"
        print(f"--- [Error] {error_msg} ---")
        logging.error(f"Synthesis error: {e}", exc_info=True)
        return {
            "synthesis_report": f"Error: {error_msg}",
            "human_feedback": None
        }


@retry_with_backoff(CREW_RETRY_CONFIG)
def _run_communication_crew(synthesis_context: str, user_query: str, google_api_key: str):
    """Communication crew (unchanged)."""
    communications_crew = create_communication_crew(
        synthesis_context=synthesis_context,
        user_query=user_query,
        google_api_key=google_api_key,
    )
    final_report_result = communications_crew.kickoff()
    return final_report_result.raw


def node_communicator(state: WorkflowState) -> dict:
    print("\n--- [Node] Executing Communicator Crew ---")
    
    try:
        google_key = os.getenv("GOOGLE_API_KEY")
        
        if not google_key:
            raise ValueError("GOOGLE_API_KEY not found.")

        final_report = _run_communication_crew(
            synthesis_context=state['synthesis_report'],
            user_query=state['user_query'],
            google_api_key=google_key
        )
        
        return {"final_report": final_report}
        
    except Exception as e:
        error_msg = f"Communication failed: {str(e)[:200]}"
        print(f"--- [Error] {error_msg} ---")
        logging.error(f"Communication error: {e}", exc_info=True)
        return {
            "final_report": "Error generating response. Please try again."
        }

    
def node_error_handler(state: WorkflowState) -> dict:
    print("\n--- [Node] Error Handler ---")
    error_reason = state.get('internal_analysis_report', 'Unknown error')
    return {"error_message": f"Workflow failed. Reason: {error_reason}"}


def node_human_approval(state: WorkflowState) -> dict:
    print("\n--- [Node] Human Approval Required ---")
    synthesis_report = state.get('synthesis_report', 'No report generated.')
    print("\nSYNTHESIS REPORT:")
    print("="*40, f"\n{synthesis_report}\n", "="*40)
    
    user_input = ""
    while user_input.lower() not in ['approve', 'reject']:
        user_input = input("Type 'approve' or 'reject': ")
        
    if user_input.lower() == 'reject':
        feedback = input("Provide feedback: ")
        return {"human_feedback": feedback}
    
    return {"human_feedback": None}


def node_save_conversation_note(state: WorkflowState) -> dict:
    """Saves conversation note (unchanged)."""
    print("\n--- [Node] Saving Conversation Note ---")
    
    user_id = state.get("user_id")
    session_id = state.get("session_id")
    
    if not user_id or not session_id:
        print("--- [Info] Skipping note: missing IDs ---")
        return {}
    
    try:
        chat_history = state.get("chat_history", [])
        current_query = state.get("user_query", "")
        final_response = state.get("final_report", "")
        
        conversation_history = []
        
        for msg in chat_history:
            if msg.startswith("user:"):
                conversation_history.append({
                    "role": "user",
                    "content": msg.replace("user:", "").strip()
                })
            elif msg.startswith("assistant:"):
                conversation_history.append({
                    "role": "assistant", 
                    "content": msg.replace("assistant:", "").strip()
                })
        
        if current_query:
            conversation_history.append({
                "role": "user",
                "content": current_query
            })
        
        if final_response:
            conversation_history.append({
                "role": "assistant",
                "content": final_response
            })
        
        should_generate = (
            len(conversation_history) >= 5 or
            any(keyword in current_query.lower() 
                for keyword in ['budget', 'cost', 'expense', 'revenue', 
                               'plan', 'strategy', 'decision', 'concern'])
        )
        
        if should_generate:
            print(f"--- [Info] Generating note (background) ---")
            
            async def generate_note_async():
                try:
                    await generate_and_store_conversation_note(
                        user_id=user_id,
                        session_id=session_id,
                        conversation_history=conversation_history,
                        force=False
                    )
                except Exception as e:
                    logging.error(f"Note generation failed: {e}")
            
            asyncio.create_task(generate_note_async())
        
        return {}
        
    except Exception as e:
        logging.error(f"Note save error: {e}")
        return {}


# -----------------------------------------------------------------
# --- DECISION FUNCTIONS ---
# -----------------------------------------------------------------

def decide_next_step_after_analysis(state: WorkflowState) -> str:
    print("\n--- [Decision] Evaluating Internal Analysis ---")
    report = state.get("internal_analysis_report", "")
    
    if (
        report.startswith("Error:") 
        or "failed after retries" in report.lower()
    ):
        print(f"--- [Decision] Error detected. Routing to error handler. ---")
        return "handle_error"
        
    print("--- [Decision] Analysis successful. Proceeding to research. ---")
    return "proceed_to_research"


def decide_if_human_approval_is_needed(state: WorkflowState) -> str:
    print("\n--- [Decision] Checking Execution Mode ---")
    if state.get("execution_mode") == "micromanage":
        return "request_approval"
    return "skip_approval"

        
def decide_after_approval(state: WorkflowState) -> str:
    print("\n--- [Decision] Evaluating Human Input ---")
    if state.get("human_feedback"):
        print("--- [Decision] Feedback received. Re-running synthesis. ---")
        return "rerun_synthesis"
    else:
        print("--- [Decision] Approved. Proceeding to comms. ---")
        return "proceed_to_comms"


# -----------------------------------------------------------------
# --- ✨ BUILD THE GRAPH (UPDATED) ---
# -----------------------------------------------------------------
def get_compiled_app():
    """
    Builds and compiles the LangGraph workflow with hierarchical retrieval.
    """
    workflow = StateGraph(WorkflowState)

    # --- Add nodes ---
    workflow.add_node("load_history_node", node_load_history)
    workflow.add_node("triage_node", node_triage_query)
    workflow.add_node("answer_general_query_node", node_answer_general_query)
    
    # ✨ NEW NODES
    workflow.add_node("classify_scope_node", node_classify_query_scope)
    workflow.add_node("hierarchical_retrieval_node", lambda s: asyncio.run(node_hierarchical_retrieval(s)))
    
    # Updated node
    workflow.add_node("internal_analyst_node", node_internal_analyst)
    
    workflow.add_node("researcher_node", node_researcher)
    workflow.add_node("synthesizer_node", node_synthesizer)
    workflow.add_node("human_approval_node", node_human_approval)
    workflow.add_node("communicator_node", node_communicator)
    workflow.add_node("error_handler_node", node_error_handler)
    workflow.add_node("save_note_node", node_save_conversation_note)

    # --- Entry point ---
    workflow.set_entry_point("load_history_node")

    # --- Edges ---
    workflow.add_edge("load_history_node", "triage_node")
    
    workflow.add_conditional_edges(
        "triage_node",
        decide_after_triage,
        {
            "answer_general_query": "answer_general_query_node",
            "classify_scope": "classify_scope_node"  # ✨ NEW
        }
    )
    
    # ✨ NEW: Scope classification → Hierarchical retrieval
    workflow.add_edge("classify_scope_node", "hierarchical_retrieval_node")
    workflow.add_edge("hierarchical_retrieval_node", "internal_analyst_node")
    
    workflow.add_edge("answer_general_query_node", "save_note_node") 
    workflow.add_edge("save_note_node", END) 
    
    workflow.add_conditional_edges(
        "internal_analyst_node",
        decide_next_step_after_analysis, 
        {
            "handle_error": "error_handler_node",
            "proceed_to_research": "researcher_node"
        }
    )
    
    workflow.add_edge("researcher_node", "synthesizer_node")
    
    workflow.add_conditional_edges(
        "synthesizer_node", 
        decide_if_human_approval_is_needed, 
        {
            "request_approval": "human_approval_node",
            "skip_approval": "communicator_node"
        }
    )
    
    workflow.add_conditional_edges(
        "human_approval_node", 
        decide_after_approval, 
        {
            "proceed_to_comms": "communicator_node",
            "rerun_synthesis": "synthesizer_node"
        }
    )
    
    workflow.add_edge("communicator_node", "save_note_node")
    workflow.add_edge("error_handler_node", END)

    # --- Compile ---
    return workflow.compile()
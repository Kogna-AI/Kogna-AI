import os
from dotenv import load_dotenv
from typing import TypedDict, Optional, List
import json
from langgraph.graph import StateGraph, END
# UNCOMMENTED: Connect to supabase
from supabase_connect import get_supabase_manager 
import logging
from langchain_litellm import ChatLiteLLM
import re
from .prompt import TRIAGE_PROMPT, GENERAL_ANSWER_PROMPT
from .retry_utils import retry_with_backoff, RetryConfig, retry_llm_call

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Supabase Setup ---
try:
    supabase_manager = get_supabase_manager()
    supabase = supabase_manager.client
except Exception as e:
    logging.error(f"Failed to initialize Supabase client: {e}")
    supabase = None # Set to None if initialization fails

# Import your existing crew creation functions
from Ai_agents.internal_analyst_agent import create_internal_analyst_crew
from Ai_agents.reasearch_agent import create_research_crew
from Ai_agents.synthesize_agent import create_synthesis_crew
from Ai_agents.communication_agent import create_communication_crew

# --- Configure retry settings for different operations ---
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
    session_id: Optional[str] # <-- NEW: Key to link history
    query_classification: Optional[str]
    user_query: str
    execution_mode: str
    chat_history: Optional[List[str]]
    internal_sources: Optional[List[str]]
    internal_analysis_report: Optional[str]
    business_research_findings: Optional[str]
    synthesis_report: Optional[str]
    final_report: Optional[str]
    error_message: Optional[str]
    human_feedback: Optional[str] 

# -----------------------------------------------------------------
# --- NEW: Supabase Helper Function with Retry ---
# -----------------------------------------------------------------
@retry_with_backoff(RetryConfig(max_retries=3, initial_delay=0.5, max_delay=10.0))
def fetch_chat_history_for_session(session_id: str) -> List[str]:
    """
    Fetches past messages for a given session from Supabase and formats them
    as a list of strings (e.g., ['user: I need X', 'assistant: I found Y']).
    """
    if not supabase:
        logging.error("Supabase client not available.")
        return []
    
    # This will retry on connection errors, timeouts, etc.
    response = supabase.table("messages") \
        .select("role, content") \
        .eq("session_id", session_id) \
        .order("created_at", desc=False) \
        .execute()
    
    history = response.data
    
    # Format the history for the LLM
    formatted_history = [
        f"{msg['role']}: {msg['content']}" 
        for msg in history
    ]
    
    logging.info(f"Loaded {len(formatted_history)} history items for session {session_id}.")
    return formatted_history

# -----------------------------------------------------------------
# --- NEW NODE: Loads Chat History ---
# -----------------------------------------------------------------
def node_load_history(state: WorkflowState) -> dict:
    print("\n--- [Node] Loading Chat History ---")
    session_id = state.get("session_id")
    
    if session_id:
        try:
            history = fetch_chat_history_for_session(session_id)
            return {"chat_history": history}
        except Exception as e:
            logging.error(f"Failed to load chat history after retries: {e}")
            print("--- [Info] Failed to load history. Starting with empty chat history. ---")
            return {"chat_history": []}
    
    print("--- [Info] No session_id found. Starting with empty chat history. ---")
    return {"chat_history": []}


# -----------------------------------------------------------------
# --- Helper function for LLM calls with retry ---
# -----------------------------------------------------------------
@retry_llm_call
def call_llm_with_retry(model: str, api_key: str, prompt: str, temperature: float = 0.0) -> str:
    """
    Wrapper function for LLM calls with automatic retry logic.
    """
    llm = ChatLiteLLM(
        model=model,
        api_key=api_key,
        temperature=temperature
    )
    response = llm.invoke(prompt)
    return response.content.strip()


# --- UPDATED NODE: Triage Query (with retry) ---
def node_triage_query(state: WorkflowState) -> dict:
    print("\n--- [Node] Triaging Query ---")
    user_query = state['user_query']
    chat_history = state.get("chat_history", []) 
    history_str = "\n".join(chat_history)

    try:
        prompt = TRIAGE_PROMPT.format(history_str=history_str, user_query=user_query)
        
        # This will automatically retry on timeouts/rate limits
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
        print(f"--- [Error] Triage failed after retries: {e}. Defaulting to data_request. ---")
        logging.error(f"Triage error: {e}", exc_info=True)
        return {"query_classification": "data_request"}


# --- UPDATED NODE: Answer General Query (with retry) ---
def node_answer_general_query(state: WorkflowState) -> dict:
    print("\n--- [Node] Answering General Query ---")
    user_query = state['user_query']

    try:
        prompt = GENERAL_ANSWER_PROMPT.format(user_query=user_query)
        
        # This will automatically retry on timeouts/rate limits
        response = call_llm_with_retry(
            model="gemini/gemini-2.0-flash",
            api_key=os.getenv("GOOGLE_API_KEY"),
            prompt=prompt,
            temperature=0.7
        )
        
        return {"final_report": response}

    except Exception as e:
        print(f"--- [Error] General chat failed after retries: {e} ---")
        logging.error(f"General chat error: {e}", exc_info=True)
        return {"final_report": f"I'm having trouble connecting to the AI service right now. Please try again in a moment."}


# --- EXISTING DECISION FUNCTION (Unchanged) ---
def decide_after_triage(state: WorkflowState) -> str:
    """Decides where to route the query after classification."""
    print("\n--- [Decision] Routing based on Triage ---")
    if state.get("query_classification") == "general_conversation":
        return "answer_general_query"
    else:
        return "start_data_workflow"


# --- UPDATED NODE: Internal Analyst (with retry) ---
@retry_with_backoff(CREW_RETRY_CONFIG)
def _run_internal_analyst_crew(user_id: str, user_query: str, chat_history_str: str):
    """Helper function to run the internal analyst crew with retry logic."""
    google_key = os.getenv("GOOGLE_API_KEY")
    
    internal_analyst_crew = create_internal_analyst_crew(
        gemini_api_key=google_key,
        user_id=user_id
    )
    
    inputs = {
        'user_query': user_query,
        'chat_history_str': chat_history_str
    }
    
    analysis_result = internal_analyst_crew.kickoff(inputs=inputs)
    return analysis_result.raw


def node_internal_analyst(state: WorkflowState) -> dict:
    print("\n--- [Node] Executing Internal Analyst Crew (RAG) ---")
    user_id = state.get("user_id")
    
    if not user_id:
        print("--- [Error] user_id is missing from state in node_internal_analyst ---")
        return {"internal_analysis_report": "Error: user_id is missing."}
    
    try:
        chat_history_str = "\n".join(state.get("chat_history", []))
        
        # This will retry the crew execution if it times out
        analysis_report = _run_internal_analyst_crew(
            user_id=user_id,
            user_query=state['user_query'],
            chat_history_str=chat_history_str
        )
        
        print(f"--- [Node] Internal Analyst finished. ---")
        return {"internal_analysis_report": analysis_report}
        
    except Exception as e:
        error_msg = f"Internal analysis failed after retries: {str(e)[:200]}"
        print(f"--- [Error] {error_msg} ---")
        logging.error(f"Internal analyst error: {e}", exc_info=True)
        return {"internal_analysis_report": f"Error: {error_msg}"}


# --- UPDATED NODE: Researcher (with retry) ---
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
    """
    This node runs web research with validation and retry logic.
    """
    print("\n--- [Node] Executing Research Crew ---")
    
    google_key = os.getenv("GOOGLE_API_KEY")
    serper_key = os.getenv("SERPAPI_API_KEY")
    
    if not serper_key or not google_key:
        print("--- [Node] Warning: Missing API keys. Skipping research. ---")
        return {"business_research_findings": "Research step skipped due to missing API keys."}

    try:
        # This now has both internal retry AND exponential backoff retry
        research_findings = _run_research_with_validation(
            user_query=state['user_query'],
            google_api_key=google_key,
            serper_api_key=serper_key
        )
        
        print(f"--- [Node] Research completed. Length: {len(research_findings)} chars ---")
        
        # Warn if results seem wrong
        if "online retailer" in research_findings.lower() and "ai" not in research_findings.lower():
            print("--- [Node] WARNING: Results may be about wrong entity ---")
        
        return {"business_research_findings": research_findings}
            
    except Exception as e:
        error_str = str(e)
        print(f"--- [Node] Research error after retries: {error_str[:200]}... ---")
        logging.error(f"Research error: {e}", exc_info=True)
        
        # Check if it's a rate limit that couldn't be resolved
        if "429" in error_str or "rate limit" in error_str.lower():
            return {
                "business_research_findings": (
                    "Research temporarily unavailable due to API rate limits. "
                    "Please try again in a few minutes."
                )
            }
        
        return {"business_research_findings": f"Research service temporarily unavailable. Please try again."}


# --- UPDATED NODE: Synthesizer (with retry) ---
@retry_with_backoff(CREW_RETRY_CONFIG)
def _run_synthesis_crew(internal_analysis_report: str, internal_sources: Optional[List[str]], 
                       business_research_findings: str, google_api_key: str, human_feedback: Optional[str]):
    """Helper function to run synthesis crew with retry logic."""
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
    if human_feedback:
        print(f"--- [Info] Synthesizer is re-running with human feedback: '{human_feedback}' ---")
    
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
        error_msg = f"Synthesis failed after retries: {str(e)[:200]}"
        print(f"--- [Error] {error_msg} ---")
        logging.error(f"Synthesis error: {e}", exc_info=True)
        return {
            "synthesis_report": f"Error during synthesis: {error_msg}",
            "human_feedback": None
        }


# --- UPDATED NODE: Communicator (with retry) ---
@retry_with_backoff(CREW_RETRY_CONFIG)
def _run_communication_crew(synthesis_context: str, user_query: str, google_api_key: str):
    """Helper function to run communication crew with retry logic."""
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
            raise ValueError("GOOGLE_API_KEY not found in .env file.")

        final_report = _run_communication_crew(
            synthesis_context=state['synthesis_report'],
            user_query=state['user_query'],
            google_api_key=google_key
        )
        
        return {"final_report": final_report}
        
    except Exception as e:
        error_msg = f"Communication failed after retries: {str(e)[:200]}"
        print(f"--- [Error] {error_msg} ---")
        logging.error(f"Communication error: {e}", exc_info=True)
        return {"final_report": "I encountered an issue generating the final response. Please try again."}

    
def node_error_handler(state: WorkflowState) -> dict:
    print("\n--- [Node] Executing Error Handler ---")
    error_reason = state.get('internal_analysis_report', 'Unknown error in analysis')
    error_report = f"Workflow failed.\nReason: {error_reason}"
    return {"error_message": error_report}


def node_human_approval(state: WorkflowState) -> dict:
    print("\n--- [Node] Human Approval Required ---")
    synthesis_report = state.get('synthesis_report', 'No report was generated.')
    print("\nSYNTHESIS REPORT:")
    print("="*40, f"\n{synthesis_report}\n", "="*40)
    
    user_input = ""
    while user_input.lower() not in ['approve', 'reject']:
        user_input = input("Please type 'approve' to continue or 'reject' to provide feedback: ")
        
    if user_input.lower() == 'reject':
        feedback = input("Please provide feedback on what to change: ")
        return {"human_feedback": feedback}
    
    return {"human_feedback": None} # Approved, no feedback needed


# --- EXISTING DECISION FUNCTIONS (Unchanged) ---
def decide_next_step_after_analysis(state: WorkflowState) -> str:
    print("\n--- [Decision] Evaluating Internal Analysis Report ---")
    report = state.get("internal_analysis_report", "")
    
    # Updated error checking
    if (
        report.startswith("Error:") 
        or "user_id is missing" in report
        or "Error during vector search" in report
        or "failed after retries" in report.lower()
    ):
        print(f"--- [Decision] Genuine error detected. Routing to error handler. ---")
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
        print("--- [Decision] Rejection with feedback received. Re-running synthesis. ---")
        return "rerun_synthesis"
    else:
        print("--- [Decision] Approved. Proceeding to communications. ---")
        return "proceed_to_comms"


# --- 4. Build the Graph (UPDATED) ---
def get_compiled_app():
    """
    Builds and compiles the LangGraph workflow.
    """
    workflow = StateGraph(WorkflowState)

    # --- Add all your nodes ---
    workflow.add_node("load_history_node", node_load_history)
    workflow.add_node("triage_node", node_triage_query)
    workflow.add_node("answer_general_query_node", node_answer_general_query)
    workflow.add_node("internal_analyst_node", node_internal_analyst)
    workflow.add_node("researcher_node", node_researcher)
    workflow.add_node("synthesizer_node", node_synthesizer)
    workflow.add_node("human_approval_node", node_human_approval)
    workflow.add_node("communicator_node", node_communicator)
    workflow.add_node("error_handler_node", node_error_handler)

    # --- Set the entry point ---
    workflow.set_entry_point("load_history_node")

    # --- Add all your edges ---
    workflow.add_edge("load_history_node", "triage_node")
    
    workflow.add_conditional_edges(
        "triage_node",
        decide_after_triage,
        {
            "answer_general_query": "answer_general_query_node", 
            "start_data_workflow": "internal_analyst_node"
        }
    )
    
    workflow.add_edge("answer_general_query_node", END) 
    workflow.add_conditional_edges(
        "internal_analyst_node",
        decide_next_step_after_analysis, 
        {"handle_error": "error_handler_node", "proceed_to_research": "researcher_node"}
    )
    workflow.add_edge("researcher_node", "synthesizer_node")
    workflow.add_conditional_edges(
        "synthesizer_node", 
        decide_if_human_approval_is_needed, 
        {"request_approval": "human_approval_node", "skip_approval": "communicator_node"}
    )
    workflow.add_conditional_edges(
        "human_approval_node", 
        decide_after_approval, 
        {"proceed_to_comms": "communicator_node", "rerun_synthesis": "synthesizer_node"}
    )
    workflow.add_edge("communicator_node", END)
    workflow.add_edge("error_handler_node", END)

    # --- Compile the app ---
    return workflow.compile()
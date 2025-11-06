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
# --- NEW: Supabase Helper Function ---
# -----------------------------------------------------------------
def fetch_chat_history_for_session(session_id: str) -> List[str]:
    """
    Fetches past messages for a given session from Supabase and formats them
    as a list of strings (e.g., ['user: I need X', 'assistant: I found Y']).
    """
    if not supabase:
        logging.error("Supabase client not available.")
        return []
    
    try:
        # We query the 'messages' table, filtered by session_id, ordered by creation time
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
        
    except Exception as e:
        logging.error(f"Error fetching chat history for session {session_id}: {e}")
        return []

# -----------------------------------------------------------------
# --- NEW NODE: Loads Chat History ---
# -----------------------------------------------------------------
def node_load_history(state: WorkflowState) -> dict:
    print("\n--- [Node] Loading Chat History ---")
    session_id = state.get("session_id")
    
    if session_id:
        history = fetch_chat_history_for_session(session_id)
        # We only pass the history, and then move to the next step
        return {"chat_history": history}
    
    print("--- [Info] No session_id found. Starting with empty chat history. ---")
    return {"chat_history": []}


# --- EXISTING NODE: Triage Query (Unchanged, but now uses history from state) ---
def node_triage_query(state: WorkflowState) -> dict:
    print("\n--- [Node] Triaging Query ---")
    user_query = state['user_query']
    # Uses history loaded in node_load_history
    chat_history = state.get("chat_history", []) 
    history_str = "\n".join(chat_history)

    # ... (rest of the triage node logic is the same) ...

    try:
        llm = ChatLiteLLM(
            model="gemini/gemini-2.0-flash",
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.0
        )

        # --- USE IMPORTED PROMPT ---
        prompt = TRIAGE_PROMPT.format(history_str=history_str, user_query=user_query)

        response = llm.invoke(prompt)
        classification = response.content.strip().lower()

        if "general_conversation" in classification:
            print("--- [Info] Query classified as: general_conversation ---")
            return {"query_classification": "general_conversation"}
        else:
            print("--- [Info] Query classified as: data_request ---")
            return {"query_classification": "data_request"}

    except Exception as e:
        print(f"--- [Error] Triage failed: {e}. Defaulting to data_request. ---")
        return {"query_classification": "data_request"}


# --- EXISTING NODES (Rest of your nodes remain the same) ---
def node_answer_general_query(state: WorkflowState) -> dict:
    print("\n--- [Node] Answering General Query ---")
    user_query = state['user_query']

    try:
        llm = ChatLiteLLM(
            model="gemini/gemini-2.0-flash",
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.7
        )

        # --- USE IMPORTED PROMPT ---
        prompt = GENERAL_ANSWER_PROMPT.format(user_query=user_query)

        response = llm.invoke(prompt)
        return {"final_report": response.content.strip()}

    except Exception as e:
        print(f"--- [Error] General chat failed: {e} ---")
        return {"final_report": f"Sorry, I had an error trying to respond: {e}"}

# --- EXISTING DECISION FUNCTION (Unchanged) ---
def decide_after_triage(state: WorkflowState) -> str:
    """Decides where to route the query after classification."""
    print("\n--- [Decision] Routing based on Triage ---")
    if state.get("query_classification") == "general_conversation":
        return "answer_general_query"
    else:
        return "start_data_workflow"

# --- EXISTING NODE: Internal Analyst (Unchanged) ---
def node_internal_analyst(state: WorkflowState) -> dict:
    print("\n--- [Node] Executing Internal Analyst Crew (RAG) ---")
    google_key = os.getenv("GOOGLE_API_KEY")
    user_id = state.get("user_id")
    
    if not user_id:
        print("--- [Error] user_id is missing from state in node_internal_analyst ---")
        return {"internal_analysis_report": "Error: user_id is missing."}
    
    # 1. Call the updated function with the user_id
    internal_analyst_crew = create_internal_analyst_crew(
        gemini_api_key=google_key,
        user_id=user_id
    )
    
    inputs = {
        'user_query': state['user_query'],
        'chat_history_str': "\n".join(state.get("chat_history", []))
    }
    analysis_result = internal_analyst_crew.kickoff(inputs=inputs)
    
    print(f"--- [Node] Internal Analyst finished. ---")
    
    # 3. Return only the report
    return {
        "internal_analysis_report": analysis_result.raw
    }
# --- EXISTING NODES (Researcher, Synthesizer, Communicator, Error Handler, Human Approval) ---

def node_researcher(state: WorkflowState) -> dict:
    """
    This node now ACTUALLY runs the web research crew.
    """
    print("\n--- [Node] Executing Research Crew ---")
    
    # Get API keys
    google_key = os.getenv("GOOGLE_API_KEY")
    serper_key = os.getenv("SERPAPI_API_KEY")
    
    if not serper_key or not google_key:
        print("--- [Node] Warning: Missing SERPAPI_API_KEY or GOOGLE_API_KEY. Skipping research. ---")
        return {"business_research_findings": "Research step skipped due to missing API keys."}

    try:
        # 1. Create the crew, passing in the user's query from the state
        research_crew = create_research_crew(
            user_query=state['user_query'], # <-- Pass the query
            google_api_key=google_key,
            serper_api_key=serper_key
        )
        
        # 2. Run the crew
        # This crew doesn't need inputs because the query is built into the task
        research_result = research_crew.kickoff()
        
        # Check if the result is not None before accessing .raw
        if research_result and hasattr(research_result, 'raw'):
            print(f"--- [Node] Research Crew finished. Findings: {research_result.raw[:100]}... ---")
            # 3. Return the findings
            return {"business_research_findings": research_result.raw}
        else:
             print("--- [Node] Research Crew returned no result. ---")
             return {"business_research_findings": "Research crew ran but produced no output."}
            
    except Exception as e:
        print(f"--- [Node] Error in Research Crew: {e} ---")
        return {"business_research_findings": f"Error during web research: {e}"}

def node_synthesizer(state: WorkflowState) -> dict:
    print("\n--- [Node] Executing Synthesizer Crew ---")
    google_key = os.getenv("GOOGLE_API_KEY")
    serper_key = os.getenv("SERPAPI_API_KEY")
    
    human_feedback = state.get("human_feedback")
    if human_feedback:
        print(f"--- [Info] Synthesizer is re-running with human feedback: '{human_feedback}' ---")
    
    synthesizer_crew = create_synthesis_crew(
        internal_analysis_report=state['internal_analysis_report'],
        internal_sources=state.get('internal_sources'), 
        business_research_findings=state['business_research_findings'],
        google_api_key=google_key,
        human_feedback=human_feedback
    )
    synthesis_result = synthesizer_crew.kickoff()
    
    return {"synthesis_report": synthesis_result.raw, "human_feedback": None} # Clear feedback after use

def node_communicator(state: WorkflowState) -> dict:
    try:
        google_key = os.getenv("GOOGLE_API_KEY")
        serper_key = os.getenv("SERPAPI_API_KEY")
        
        if not serper_key or not google_key:
            raise ValueError("SERPAPI_API_KEY or GOOGLE_API_KEY not found in .env file.")

        communications_crew = create_communication_crew(
            synthesis_context=state['synthesis_report'], 
            user_query=state['user_query'],
            google_api_key=google_key, 
        )
        final_report_result = communications_crew.kickoff()
        return {"final_report": final_report_result.raw}
    except Exception as e:
        return {"final_report": f"Error in node_communicator: {str(e)}"}
    
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
    workflow.add_node("load_history_node", node_load_history) # <-- NEW NODE
    workflow.add_node("triage_node", node_triage_query)
    workflow.add_node("answer_general_query_node", node_answer_general_query)
    workflow.add_node("internal_analyst_node", node_internal_analyst)
    workflow.add_node("researcher_node", node_researcher)
    workflow.add_node("synthesizer_node", node_synthesizer)
    workflow.add_node("human_approval_node", node_human_approval)
    workflow.add_node("communicator_node", node_communicator)
    workflow.add_node("error_handler_node", node_error_handler)

    # --- Set the entry point (UPDATED) ---
    workflow.set_entry_point("load_history_node")

    # --- Add all your edges (UPDATED) ---
    # 1. Load history runs, then proceeds to triage
    workflow.add_edge("load_history_node", "triage_node")
    
    # 2. Triage decides based on the query (which now includes history)
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



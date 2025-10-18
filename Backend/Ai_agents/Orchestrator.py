import os
from dotenv import load_dotenv
from typing import TypedDict, Optional
import json
from langgraph.graph import StateGraph, END

# Import your existing crew creation functions
# from data_ingestion_agent import create_scribe_crew
# from data_analyst_agent import create_data_analyst_crew
from internal_analyst_agent import create_internal_analyst_crew
from reasearch_agent import create_research_crew
from synthesize_agent import create_synthesis_crew
from communication_agent import create_communication_crew

# --- 1. Define the State for the Graph ---
# Added 'human_feedback' to store correction instructions.
class WorkflowState(TypedDict):
    # raw_data: str
    user_query: str
    execution_mode: str
    # structured_data: Optional[str]
    internal_analysis_report: Optional[str]
    business_research_findings: Optional[str]
    synthesis_report: Optional[str]
    final_report: Optional[str]
    error_message: Optional[str]
    human_feedback: Optional[str] # NEW: To store feedback for the loop

# --- 2. Define the Nodes for the Graph ---

# def node_scribe(state: WorkflowState) -> dict:
#     print("\n--- [Node] Executing Scribe Crew ---")
#     # ... (code is unchanged)
#     google_key = os.getenv("GOOGLE_API_KEY")
#     scribe_crew = create_scribe_crew(google_api_key=google_key)
#     ingested_data_result = scribe_crew.kickoff(inputs={'raw_data': state['raw_data']})
#     return {"structured_data": ingested_data_result.raw}

def node_internal_analyst(state: WorkflowState) -> dict:
    print("\n--- [Node] Executing Internal Analyst Crew (RAG) ---")
    google_key = os.getenv("GOOGLE_API_KEY")
    
    internal_analyst_crew = create_internal_analyst_crew(gemini_api_key=google_key)
    
    inputs = {'user_query': state['user_query']} 
    analysis_result = internal_analyst_crew.kickoff(inputs=inputs)
    
    return {"internal_analysis_report": analysis_result.raw}

def node_researcher(state: WorkflowState) -> dict:
    print("\n--- [Node] Executing Research Crew (Skipped) ---")
    # ... (code is unchanged)
    return {"business_research_findings": "Research step was skipped due to missing credentials for internal tools."}

def node_synthesizer(state: WorkflowState) -> dict:
    print("\n--- [Node] Executing Synthesizer Crew ---")
    google_key = os.getenv("GOOGLE_API_KEY")
    serper_key = os.getenv("SERPAPI_API_KEY")
    
    human_feedback = state.get("human_feedback")
    if human_feedback:
        print(f"--- [Info] Synthesizer is re-running with human feedback: '{human_feedback}' ---")
    
    synthesizer_crew = create_synthesis_crew(
        # --- PASS THE NEW REPORT ---
        internal_analysis_report=state['internal_analysis_report'], # Was: sql_analysis_report
        # ---------------------------
        business_research_findings=state['business_research_findings'],
        google_api_key=google_key,
        serper_api_key=serper_key,
        human_feedback=human_feedback
    )
    synthesis_result = synthesizer_crew.kickoff()
    
    return {"synthesis_report": synthesis_result.raw, "human_feedback": None}

def node_communicator(state: WorkflowState) -> dict:
    print("\n--- [Node] Executing Communications Crew ---")
    # ... (code is unchanged)
    google_key = os.getenv("GOOGLE_API_KEY")
    serper_key = os.getenv("SERPAPI_API_KEY")
    communications_crew = create_communication_crew(synthesis_context=state['synthesis_report'], google_api_key=google_key, serper_api_key=serper_key)
    final_report_result = communications_crew.kickoff()
    return {"final_report": final_report_result.raw}

def node_error_handler(state: WorkflowState) -> dict:
    print("\n--- [Node] Executing Error Handler ---")
    # --- UPDATE THIS ---
    error_reason = state.get('internal_analysis_report', 'Unknown error in analysis')
    error_report = f"Workflow failed.\nReason: {error_reason}"
    # -----------------
    return {"error_message": error_report}

# MODIFIED: This node now captures feedback upon rejection.
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

# --- 3. Define the Decision Functions ---

def decide_next_step_after_analysis(state: WorkflowState) -> str:
    """
    Decision 1: Checks if the internal analysis was successful.
    This is now smarter and looks for specific error *messages*,
    not just the word "error" (which could be in the data).
    """
    print("\n--- [Decision] Evaluating Internal Analysis Report ---")
    
    # Get the raw report string
    report = state.get("internal_analysis_report", "")
    
    # Check for our *specific* error messages
    if (
        report.startswith("Error:") 
        or report.startswith("No relevant internal documents were found")
        or "Error during router LLM call" in report
        or "Router failed" in report
    ):
        print(f"--- [Decision] Genuine error detected. Routing to error handler. ---")
        return "handle_error"
        
    print("--- [Decision] Analysis successful (data may contain 'error_rate', but this is not a system error). Proceeding to research. ---")
    return "proceed_to_research"

def decide_if_human_approval_is_needed(state: WorkflowState) -> str:
    print("\n--- [Decision] Checking Execution Mode ---")
    # ... (code is unchanged)
    if state.get("execution_mode") == "micromanage":
        return "request_approval"
    return "skip_approval"
        
# MODIFIED: The decision after approval now routes back for corrections.
def decide_after_approval(state: WorkflowState) -> str:
    print("\n--- [Decision] Evaluating Human Input ---")
    if state.get("human_feedback"):
        print("--- [Decision] Rejection with feedback received. Rerunning synthesis. ---")
        return "rerun_synthesis"
    else:
        print("--- [Decision] Approved. Proceeding to communications. ---")
        return "proceed_to_comms"

# --- 4. Build and Run the Graph ---

def run_full_pipeline(execution_mode: str, user_query: str): # <--- MUST ACCEPT 'user_query'
    load_dotenv()
    workflow = StateGraph(WorkflowState)

    # --- Add all your nodes ---
    workflow.add_node("internal_analyst_node", node_internal_analyst)
    workflow.add_node("researcher_node", node_researcher)
    workflow.add_node("synthesizer_node", node_synthesizer)
    workflow.add_node("human_approval_node", node_human_approval)
    workflow.add_node("communicator_node", node_communicator)
    workflow.add_node("error_handler_node", node_error_handler)

    # --- Set the entry point ---
    workflow.set_entry_point("internal_analyst_node")

    # --- Add all your edges ---
    workflow.add_conditional_edges(
        "internal_analyst_node",
        decide_next_step_after_analysis, 
        {"handle_error": "error_handler_node", "proceed_to_research": "researcher_node"}
    )
    workflow.add_edge("researcher_node", "synthesizer_node")
    workflow.add_conditional_edges("synthesizer_node", decide_if_human_approval_is_needed, {"request_approval": "human_approval_node", "skip_approval": "communicator_node"})
    workflow.add_conditional_edges("human_approval_node", decide_after_approval, {"proceed_to_comms": "communicator_node", "rerun_synthesis": "synthesizer_node"})
    workflow.add_edge("communicator_node", END)
    workflow.add_edge("error_handler_node", END)

    # --- Compile the app ---
    app = workflow.compile()
    
    # --- THIS IS THE CRITICAL FIX ---
    # Create the initial_state *with* the user_query
    initial_state = {
        "execution_mode": execution_mode,
        "user_query": user_query  # <-- This key must match the state definition
    }
    # ---------------------------------
    
    print("\n--- STARTING LANGGRAPH WORKFLOW (RAG VERSION) ---")
    
    # Pass the populated initial_state to the stream
    for s in app.stream(initial_state, {"recursion_limit": 25}):
        print(s)
        print("-" * 60)
    
    # ... (Your final output logic if any) ...

# --- Main execution block ---
# (Your __main__ block is 100% correct, leave it as-is)
if __name__ == "__main__":
    print("--- Welcome to the Kogna AI Orchestrator ---")
    
    mode = ""
    while mode not in ['1', '2']:
        mode = input("Please select an execution mode:\n1. Autonomous\n2. Micromanage\nEnter choice (1 or 2): ")
    selected_mode = "autonomous" if mode == '1' else "micromanage"
    
    print("\n--- Kogna AI is ready ---")
    query = ""
    while not query:
        query = input("Please enter your primary analysis request:\n> ")
    
    # This call is correct.
    run_full_pipeline(execution_mode=selected_mode, user_query=query)
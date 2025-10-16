import os
from dotenv import load_dotenv
from typing import TypedDict, Optional
import json
from langgraph.graph import StateGraph, END

# Import your existing crew creation functions
from data_ingestion_agent import create_scribe_crew
from data_analyst_agent import create_data_analyst_crew
from reasearch_agent import create_research_crew
from synthesize_agent import create_synthesis_crew
from communication_agent import create_communication_crew

# --- 1. Define the State for the Graph ---
# Added 'human_feedback' to store correction instructions.
class WorkflowState(TypedDict):
    raw_data: str
    execution_mode: str
    structured_data: Optional[str]
    sql_analysis_report: Optional[str]
    business_research_findings: Optional[str]
    synthesis_report: Optional[str]
    final_report: Optional[str]
    error_message: Optional[str]
    human_feedback: Optional[str] # NEW: To store feedback for the loop

# --- 2. Define the Nodes for the Graph ---

def node_scribe(state: WorkflowState) -> dict:
    print("\n--- [Node] Executing Scribe Crew ---")
    # ... (code is unchanged)
    google_key = os.getenv("GOOGLE_API_KEY")
    scribe_crew = create_scribe_crew(google_api_key=google_key)
    ingested_data_result = scribe_crew.kickoff(inputs={'raw_data': state['raw_data']})
    return {"structured_data": ingested_data_result.raw}

def node_data_analyst(state: WorkflowState) -> dict:
    print("\n--- [Node] Executing Data Analyst Crew ---")
    # ... (code is unchanged)
    google_key = os.getenv("GOOGLE_API_KEY")
    db_file_path = "pipeline_data.db"
    data_analyst_crew = create_data_analyst_crew(gemini_api_key=google_key, db_path=db_file_path)
    data_analysis_result = data_analyst_crew.kickoff(inputs={'structured_data': state['structured_data']})
    return {"sql_analysis_report": data_analysis_result.raw}

def node_researcher(state: WorkflowState) -> dict:
    print("\n--- [Node] Executing Research Crew (Skipped) ---")
    # ... (code is unchanged)
    return {"business_research_findings": "Research step was skipped due to missing credentials for internal tools."}

# MODIFIED: The synthesizer node is now aware of human feedback.
def node_synthesizer(state: WorkflowState) -> dict:
    print("\n--- [Node] Executing Synthesizer Crew ---")
    google_key = os.getenv("GOOGLE_API_KEY")
    serper_key = os.getenv("SERPAPI_API_KEY")
    
    # NEW: If feedback exists, add it to the agent's task description.
    human_feedback = state.get("human_feedback")
    if human_feedback:
        print(f"--- [Info] Synthesizer is re-running with human feedback: '{human_feedback}' ---")
    
    synthesizer_crew = create_synthesis_crew(
        sql_analysis_report=state['sql_analysis_report'],
        business_research_findings=state['business_research_findings'],
        google_api_key=google_key,
        serper_api_key=serper_key,
        human_feedback=human_feedback # Pass feedback to the crew creator
    )
    synthesis_result = synthesizer_crew.kickoff()
    
    # Clear feedback after it has been used
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
    # ... (code is unchanged)
    error_report = f"Workflow failed.\nReason: {state['sql_analysis_report']}"
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
    print("\n--- [Decision] Evaluating SQL Analysis Report ---")
    # ... (code is unchanged)
    report = state.get("sql_analysis_report", "").lower()
    if "error" in report or "no results" in report:
        return "handle_error"
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

def run_full_pipeline(execution_mode: str):
    # ... (This function remains mostly the same, but the graph definition changes)
    load_dotenv()
    workflow = StateGraph(WorkflowState)

    workflow.add_node("scribe_node", node_scribe)
    workflow.add_node("data_analyst_node", node_data_analyst)
    workflow.add_node("researcher_node", node_researcher)
    workflow.add_node("synthesizer_node", node_synthesizer)
    workflow.add_node("human_approval_node", node_human_approval)
    workflow.add_node("communicator_node", node_communicator)
    workflow.add_node("error_handler_node", node_error_handler)

    workflow.set_entry_point("scribe_node")
    workflow.add_edge("scribe_node", "data_analyst_node")
    workflow.add_conditional_edges("data_analyst_node", decide_next_step_after_analysis, {"handle_error": "error_handler_node", "proceed_to_research": "researcher_node"})
    workflow.add_edge("researcher_node", "synthesizer_node")
    workflow.add_conditional_edges("synthesizer_node", decide_if_human_approval_is_needed, {"request_approval": "human_approval_node", "skip_approval": "communicator_node"})

    # THIS IS THE NEW INTERACTIVE LOOP
    workflow.add_conditional_edges(
        "human_approval_node",
        decide_after_approval,
        {
            "proceed_to_comms": "communicator_node",
            "rerun_synthesis": "synthesizer_node" # On reject, go back to synthesizer
        }
    )

    workflow.add_edge("communicator_node", END)
    workflow.add_edge("error_handler_node", END)

    app = workflow.compile()

    data_dir = os.path.join(os.path.dirname(__file__), "mock_data_large")
    with open(os.path.join(data_dir, "employees.json")) as f:
        employees = json.load(f)
    with open(os.path.join(data_dir, "projects_and_tasks.json")) as f:
        projects = json.load(f)
    with open(os.path.join(data_dir, "emails.json")) as f:
        emails = json.load(f)
    with open(os.path.join(data_dir, "meetings.json")) as f:
        meetings = json.load(f)



    raw_data_to_process = employees + projects + emails + meetings
    raw_data_json_str = json.dumps({"records": raw_data_to_process}, indent=2)
    initial_state = {"raw_data": raw_data_json_str, "execution_mode": execution_mode}
    
    print("\n--- STARTING LANGGRAPH WORKFLOW ---")
    for s in app.stream(initial_state, {"recursion_limit": 25}):
        print(s)
        print("-" * 60)
    # ... (final output logic is unchanged)

# MODIFIED: The main execution block is now interactive.
if __name__ == "__main__":
    print("--- Welcome to the Kogna AI Orchestrator ---")
    
    mode = ""
    while mode not in ['1', '2']:
        mode = input("Please select an execution mode:\n1. Autonomous\n2. Micromanage\nEnter choice (1 or 2): ")

    selected_mode = "autonomous" if mode == '1' else "micromanage"
    
    run_full_pipeline(execution_mode=selected_mode)
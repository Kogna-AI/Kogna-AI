import os
from dotenv import load_dotenv
from typing import TypedDict, Optional

from langgraph.graph import StateGraph, END

# Import your existing crew creation functions
from data_ingestion_agent import create_scribe_crew
from data_analyst_agent import create_data_analyst_crew
from reasearch_agent import create_research_crew
from synthesize_agent import create_synthesis_crew
from communication_agent import create_communication_crew

# --- 1. Define the State for the Graph ---
# This class represents the shared state that flows through the graph.
# Each field will be populated by a node as the workflow progresses.
class WorkflowState(TypedDict):
    raw_data: str
    structured_data: Optional[str]
    sql_analysis_report: Optional[str]
    business_research_findings: Optional[str]
    synthesis_report: Optional[str]
    final_report: Optional[str]

# --- 2. Define the Nodes for the Graph ---
# Each node is a function that takes the current state and returns a dictionary
# with the fields to update.

def node_scribe(state: WorkflowState) -> dict:
    """Node to ingest and structure the raw data."""
    print("\n--- [Node] Executing Scribe Crew ---")
    google_key = os.getenv("GOOGLE_API_KEY")
    scribe_crew = create_scribe_crew(google_api_key=google_key)
    ingested_data_result = scribe_crew.kickoff(inputs={'raw_data': state['raw_data']})
    print("--- [Node] Scribe Crew Finished ---")
    return {"structured_data": ingested_data_result.raw}

def node_data_analyst(state: WorkflowState) -> dict:
    """Node to perform SQL analysis on the structured data."""
    print("\n--- [Node] Executing Data Analyst Crew ---")
    google_key = os.getenv("GOOGLE_API_KEY")
    db_file_path = "pipeline_data.db"
    data_analyst_crew = create_data_analyst_crew(
        gemini_api_key=google_key,
        db_path=db_file_path
    )
    data_analysis_result = data_analyst_crew.kickoff(inputs={'structured_data': state['structured_data']})
    print("--- [Node] Data Analyst Crew Finished ---")
    return {"sql_analysis_report": data_analysis_result.raw}

def node_researcher(state: WorkflowState) -> dict:
    """Node for business intelligence research (currently skipped)."""
    print("\n--- [Node] Executing Research Crew (Skipped) ---")
    # This node is a placeholder, as in the original script.
    research_findings = "Research step was skipped due to missing credentials for internal tools."
    return {"business_research_findings": research_findings}

def node_synthesizer(state: WorkflowState) -> dict:
    """Node to synthesize SQL analysis and business research."""
    print("\n--- [Node] Executing Synthesizer Crew ---")
    google_key = os.getenv("GOOGLE_API_KEY")
    serper_key = os.getenv("SERPAPI_API_KEY")
    synthesizer_crew = create_synthesis_crew(
        sql_analysis_report=state['sql_analysis_report'],
        business_research_findings=state['business_research_findings'],
        google_api_key=google_key,
        serper_api_key=serper_key
    )
    synthesis_result = synthesizer_crew.kickoff()
    print("--- [Node] Synthesizer Crew Finished ---")
    return {"synthesis_report": synthesis_result.raw}

def node_communicator(state: WorkflowState) -> dict:
    """Node to create the final executive report."""
    print("\n--- [Node] Executing Communications Crew ---")
    google_key = os.getenv("GOOGLE_API_KEY")
    serper_key = os.getenv("SERPAPI_API_KEY")
    communications_crew = create_communication_crew(
        synthesis_context=state['synthesis_report'],
        google_api_key=google_key,
        serper_api_key=serper_key
    )
    final_report_result = communications_crew.kickoff()
    print("--- [Node] Communications Crew Finished ---")
    return {"final_report": final_report_result.raw}

# --- 3. Build and Run the Graph ---

def run_full_pipeline():
    """
    Executes the full 5-step multi-agent workflow using LangGraph.
    """
    print("--- LOADING CREDENTIALS ---")
    load_dotenv()
    
    # Check for essential credentials
    google_key = os.getenv("GOOGLE_API_KEY")
    serper_key = os.getenv("SERPAPI_API_KEY")
    if not all([google_key, serper_key]):
        print("Error: One or more required API keys are not set in the .env file.")
        return

    print("--- CREDENTIALS LOADED SUCCESSFULLY ---")
    
    # Define the graph
    workflow = StateGraph(WorkflowState)

    # Add the nodes to the graph
    workflow.add_node("scribe_node", node_scribe)
    workflow.add_node("data_analyst_node", node_data_analyst)
    workflow.add_node("researcher_node", node_researcher)
    workflow.add_node("synthesizer_node", node_synthesizer)
    workflow.add_node("communicator_node", node_communicator)

    # Define the edges to connect the nodes in a sequence
    workflow.set_entry_point("scribe_node")
    workflow.add_edge("scribe_node", "data_analyst_node")
    workflow.add_edge("data_analyst_node", "researcher_node")
    workflow.add_edge("researcher_node", "synthesizer_node")
    workflow.add_edge("synthesizer_node", "communicator_node")
    workflow.add_edge("communicator_node", END)

    # Compile the graph into a runnable application
    app = workflow.compile()
    
    # Define the initial input data
    raw_data_to_process = (
        "record_id=A1, transaction_date=2025-10-15T00:55:00Z, product_id=P001, amount=250.00, status=success\n"
        "record_id=A2, transaction_date=2025-10-15T00:56:10Z, product_id=P002, amount=, status=failed\n"
    )
    
    # Set the initial state for the graph
    initial_state = {"raw_data": raw_data_to_process}
    
    print("\n--- STARTING LANGGRAPH WORKFLOW ---")
    
    final_state = {}
    # The .stream() method lets us see the output of each node as it runs
    for s in app.stream(initial_state, {"recursion_limit": 10}):
        final_state = s
        print(final_state)
        print("-" * 60)

    # --- Final Output ---
    final_report = final_state[next(reversed(final_state))]['final_report']

    print("\n--- WORKFLOW COMPLETE ---")
    print("=" * 60)
    print("Final Deliverables:")
    print("=" * 60)
    print(final_report)
    
    with open("final_executive_report_langgraph.txt", "w") as f:
        f.write(final_report)
    print("\nFinal report saved to final_executive_report_langgraph.txt")


if __name__ == "__main__":
    run_full_pipeline()
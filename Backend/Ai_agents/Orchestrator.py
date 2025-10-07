import os
from dotenv import load_dotenv

# Import all your crew creation functions from your other agent files
from scribe import create_scribe_crew
from data_analyst_agent import create_data_analyst_crew
from reasearch_agent import create_research_crew
from synthesize_agent import create_synthesis_crew
from communication_agent import create_communication_crew

# Load environment variables once for the whole project
load_dotenv()

def run_full_pipeline():
    """
    Executes the full 5-step multi-agent workflow from data ingestion to final reporting.
    """
    print("--- STARTING FULL AI WORKFLOW ---")

    # --- Step 1: Run the Scribe Agent Crew for Data Ingestion ---
    print("\n[Phase 1/5] Kicking off Scribe Crew for data ingestion...")
    scribe_crew = create_scribe_crew()
    ingested_data = scribe_crew.kickoff()
    # In a real workflow, this ingested_data would now be loaded into the database
    # that the Data Analyst will query.
    print("[Phase 1/5] Scribe Crew Finished. Data ingested and structured.")

    # --- Step 2: Run the Data Analyst Crew for SQL Analysis ---
    print("\n[Phase 2/5] Kicking off Data Analyst Crew...")
    data_analyst_crew = create_data_analyst_crew()
    data_analysis_report = data_analyst_crew.kickoff()
    print("[Phase 2/5] Data Analyst Crew Finished.")
    
    # --- Step 3: Run the Research Agent Crew for Business Intelligence ---
    print("\n[Phase 3/5] Kicking off Research Crew...")
    research_crew = create_research_crew()
    research_findings = research_crew.kickoff() 
    print("[Phase 3/5] Research Crew Finished.")

    # --- Step 4: Run the Synthesizer Agent Crew to Integrate All Findings ---
    print("\n[Phase 4/5] Kicking off Synthesizer Crew...")
    # The Synthesizer now receives context from BOTH the analyst and the researcher
    synthesizer_crew = create_synthesis_crew(
        sql_analysis_report=data_analysis_report,
        business_research_findings=research_findings
    )
    synthesis_report = synthesizer_crew.kickoff()
    print("[Phase 4/5] Synthesizer Crew Finished.")

    # --- Step 5: Run the Communications Agent Crew for Final Reporting ---
    print("\n[Phase 5/5] Kicking off Communications Crew...")
    communications_crew = create_communication_crew(synthesis_context=synthesis_report)
    final_report = communications_crew.kickoff()
    print("[Phase 5/5] Communications Crew Finished.")

    # --- Final Output ---
    print("\n--- WORKFLOW COMPLETE ---")
    print("="*60)
    print("Final Deliverables:")
    print("="*60)
    print(final_report)
    
    with open("final_executive_report.txt", "w") as f:
        f.write(final_report)
    print("\nFinal report saved to final_executive_report.txt")

if __name__ == "__main__":
    run_full_pipeline()
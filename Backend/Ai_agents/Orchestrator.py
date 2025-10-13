import os
from dotenv import load_dotenv

from data_ingestion_agent import create_scribe_crew
from data_analyst_agent import create_data_analyst_crew
from reasearch_agent import create_research_crew
from synthesize_agent import create_synthesis_crew
from communication_agent import create_communication_crew

def run_full_pipeline():
    """
    Executes the full 5-step multi-agent workflow.
    """
    print("--- LOADING CREDENTIALS ---")
    load_dotenv()

    google_key = os.getenv("GOOGLE_API_KEY")
    serper_key = os.getenv("SERPAPI_API_KEY")
    
    # REVERTED: Define a simple database file path.
    db_file_path = "pipeline_data.db"

    required_creds = [google_key, serper_key]
    if any(not cred for cred in required_creds):
        print("Error: One or more required API keys are not set in the .env file.")
        return
    
    print("--- CREDENTIALS LOADED SUCCESSFULLY ---")
    print("\n--- STARTING FULL AI WORKFLOW ---")

    # --- Step 1: Data Ingestion ---
    print("\n[Phase 1/5] Kicking off Scribe Crew...")
    scribe_crew = create_scribe_crew(google_api_key=google_key)
    raw_data_to_process = (
        "record_id=A1, transaction_date=2025-10-09T16:55:00Z, product_id=P001, amount=250.00, status=success\n"
        "record_id=A2, transaction_date=2025-10-09T16:56:10Z, product_id=P002, amount=, status=failed\n"
    )
    ingested_data_result = scribe_crew.kickoff(inputs={'raw_data': raw_data_to_process})
    print("[Phase 1/5] Scribe Crew Finished.")

    # --- Step 2: SQL Analysis ---
    print("\n[Phase 2/5] Kicking off Data Analyst Crew...")
    # REVERTED: Pass the simple db_path to the function.
    data_analyst_crew = create_data_analyst_crew(
        gemini_api_key=google_key,
        db_path=db_file_path 
    )
    data_analysis_result = data_analyst_crew.kickoff(inputs={'structured_data': ingested_data_result.raw})
    print("[Phase 2/5] Data Analyst Crew Finished.")
    
    # --- Step 3: Business Intelligence ---
    print("\n[Phase 3/5] Kicking off Research Crew...")
    research_findings = "Research step was skipped due to missing credentials for internal tools."
    print("[Phase 3/5] Research Crew Finished (Skipped).")

    # --- Step 4: Synthesis ---
    print("\n[Phase 4/5] Kicking off Synthesizer Crew...")
    synthesizer_crew = create_synthesis_crew(
        sql_analysis_report=data_analysis_result.raw,
        business_research_findings=research_findings,
        google_api_key=google_key,
        serper_api_key=serper_key
    )
    synthesis_result = synthesizer_crew.kickoff()
    print("[Phase 4/5] Synthesizer Crew Finished.")

    # --- Step 5: Final Reporting ---
    print("\n[Phase 5/5] Kicking off Communications Crew...")
    communications_crew = create_communication_crew(
        synthesis_context=synthesis_result.raw,
        google_api_key=google_key,
        serper_api_key=serper_key
    )
    final_report_result = communications_crew.kickoff()
    print("[Phase 5/5] Communications Crew Finished.")

    # --- Final Output ---
    print("\n--- WORKFLOW COMPLETE ---")
    print("="*60)
    print("Final Deliverables:")
    print("="*60)
    print(final_report_result.raw)
    
    with open("final_executive_report.txt", "w") as f:
        f.write(final_report_result.raw)
    print("\nFinal report saved to final_executive_report.txt")

if __name__ == "__main__":
    run_full_pipeline()
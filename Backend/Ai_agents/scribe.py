import os
import json
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool
from dotenv import load_dotenv

load_dotenv()

#
# This is the refactored script for the Scribe Agent.
# It now uses a deterministic Python function for parsing, making it more efficient and reliable.
#

# --- Tool Definitions ---

@tool("Raw Data Collector")
def raw_data_collector_tool() -> str:
    """Simulates collecting a chunk of raw, messy data from an external source."""
    print("--- Executing RawDataCollectorTool ---")
    return (
        "record_id=101, timestamp=2023-10-27T10:00:00Z, user_id=user1, value=150.5, status=success\n"
        "record_id=102, timestamp=2023-10-27T10:05:00Z, user_id=user2, value=, status=error\n"
        "record_id=103, timestamp=2023-10-27T10:10:00Z, user_id=user1, value=200.0, status=success\n"
    )

@tool("Deterministic Data Parser")
def data_parser_tool(raw_data: str) -> str:
    """
    Parses raw key-value string data into a clean JSON format using deterministic Python logic.
    This tool is fast, reliable, and does not use an LLM.
    Input must be the raw string data from the collector tool.
    """
    print("--- Executing DeterministicDataParserTool ---")
    records = []
    lines = raw_data.strip().split('\n')
    for line in lines:
        record = {}
        pairs = line.split(', ')
        for pair in pairs:
            try:
                key, value = pair.split('=', 1)
                # Handle missing values and convert types where possible
                if value == '':
                    record[key] = None
                elif key == 'record_id':
                    record[key] = int(value)
                elif key == 'value':
                    try:
                        record[key] = float(value)
                    except ValueError:
                        record[key] = None
                else:
                    record[key] = value
            except ValueError:
                continue # Skip malformed pairs
        records.append(record)
    
    return json.dumps({"records": records}, indent=2)

# --- Crew Creation Function ---

def create_scribe_crew():
    """
    Creates and configures the Scribe (Data Ingestion) Crew.
    """
    llm = LLM(
        model="gemini/gemini-2.0-flash",
        temperature=0.7,
        api_key=os.getenv("GEMINI_API_KEY")
    )

    scribe_agent = Agent(
        role='Data Ingestion Specialist',
        goal='Efficiently collect and parse raw data using specialized tools, then report on the outcome.',
        backstory=(
            "You are Scribe, an efficient agent that uses the best tool for the job. "
            "You orchestrate a workflow of collecting raw data and then passing it to a "
            "specialized, deterministic parser for fast and accurate structuring."
        ),
        verbose=True,
        allow_delegation=False,
        tools=[raw_data_collector_tool, data_parser_tool], # Agent now has both tools
        llm=llm
    )

    ingestion_task = Task(
        description=(
            "Execute a two-step data ingestion workflow:\n"
            "1. First, use the 'Raw Data Collector' tool to retrieve the latest raw data.\n"
            "2. Second, take the raw string output from the collector and pass it directly as input to the 'Deterministic Data Parser' tool.\n"
            "3. Finally, prepare a summary report stating the ingestion was successful, the number of records processed, and present the final, clean JSON data produced by the parser."
        ),
        expected_output=(
            "A final, well-formatted markdown report that includes a success message, a count of processed records, and the final structured JSON data from the parser tool."
        ),
        agent=scribe_agent
    )

    data_ingestion_crew = Crew(
        agents=[scribe_agent],
        tasks=[ingestion_task],
        process=Process.sequential,
        verbose=True
    )
    
    return data_ingestion_crew

# Note: This script is now designed to be executed via Orchestrator.py.
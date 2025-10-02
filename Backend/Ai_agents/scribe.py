# Scribe.py - The Data Ingestion Agent built with CrewAI

import os
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool


# --- Environment Setup ---
from dotenv import load_dotenv

# --- Robust .env file loading ---
script_dir = os.path.dirname(__file__)
dotenv_path = os.path.join(script_dir, 'scribe.env')
load_dotenv(dotenv_path=dotenv_path)


# --- LLM Configuration ---
# Using crewai's native LLM class is the most reliable way to configure models.
# By specifying the model with the "gemini/" prefix, we explicitly tell the
# underlying 'litellm' library which provider to use. This is the definitive fix.
GEMINI_api_key = os.getenv("GEMINI_API_KEY")
llm = LLM(
    model="gemini/gemini-2.0-flash",
    temperature=0.7,
)


# --- TOOLS DEFINITION ---

@tool("Mock Data Collector")
def mock_data_collector_tool() -> str:
    """Simulates collecting a chunk of raw, messy data from an external source."""
    print("--- Executing MockDataCollectorTool ---")
    # This is sample data.
    return (
        "record_id=101, timestamp=2023-10-27T10:00:00Z, user_id=user1, value=150.5, status=success\n"
        "record_id=102, timestamp=2023-10-27T10:05:00Z, user_id=user2, value=, status=error\n"
        "record_id=103, timestamp=2023-10-27T10:10:00Z, user_id=user1, value=200.0, status=success\n"
    )


# --- AGENT DEFINITION ---

scribe_agent = Agent(
    role='Data Ingestion Specialist',
    goal='Efficiently collect, clean, structure, and route incoming raw data.',
    backstory=(
        "You are a meticulous and highly efficient agent named Scribe. "
        "Your sole purpose is to be the first point of contact for all raw data. "
        "You take messy, unstructured information from various sources and methodically "
        "clean it, structure it into a usable format like JSON, and prepare it for its "
        "journey through the system. You pride yourself on accuracy and speed, "
        "ensuring no piece of data is lost or misinterpreted."
    ),
    verbose=True,
    allow_delegation=False,
    tools=[mock_data_collector_tool],
    llm=llm # Explicitly assign the configured LLM to the agent
)

# --- TASKS DEFINITION ---

# Task 1: Collect Data
collection_task = Task(
    description=(
        "Use the 'Mock Data Collector' tool to retrieve the latest raw data. "
        "Your job is to execute the tool and bring the raw data into the workflow."
    ),
    expected_output="A single text block containing the raw, unprocessed data from the source.",
    agent=scribe_agent
)

# Task 2: Process and Structure Data
processing_task = Task(
    description=(
        "Take the raw data block from the previous step and process it. "
        "Clean up inconsistencies, handle missing values gracefully, and "
        "transform the data into a clean, structured JSON format. "
        "Each record should be a JSON object within a list."
    ),
    expected_output=(
        "A final JSON object containing a list of structured records. Example:\n"
        '```json\n'
        '{\n'
        '  "records": [\n'
        '    {"record_id": 101, "timestamp": "2023-10-27T10:00:00Z", "user_id": "user1", "value": 150.5, "status": "success"},\n'
        '    ...\n'
        '  ]\n'
        '}\n'
        '```'
    ),
    agent=scribe_agent,
    context=[collection_task]
)

# Task 3: Prepare Final Report/Routing
routing_task = Task(
    description=(
        "Take the structured JSON data and prepare a final summary report. "
        "The report should state that the ingestion was successful, mention the "
        "number of records processed, and present the final, clean JSON data. "
        "This report signifies that the data is ready for the next stage (e.g., storage, further analysis)."
    ),
    expected_output="A final, well-formatted markdown report that includes a success message, a count of processed records, and the final JSON data.",
    agent=scribe_agent,
    context=[processing_task]
)

# --- CREW DEFINITION ---

data_ingestion_crew = Crew(
    agents=[scribe_agent],
    tasks=[collection_task, processing_task, routing_task],
    process=Process.sequential,
    verbose=True
)

# --- EXECUTION ---

if __name__ == "__main__":
    print("## Starting the Scribe Data Ingestion Crew...")
    print("-----------------------------------------------")
    
    result = data_ingestion_crew.kickoff()

    print("\n\n########################")
    print("## Crew Execution Result:")
    print("########################")
    print(result)

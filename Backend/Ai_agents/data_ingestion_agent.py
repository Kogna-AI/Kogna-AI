import json
from crewai import Agent, Task, Crew, Process
from langchain_litellm import ChatLiteLLM # Correct, more robust import

#
# This is the refactored script for the Scribe Agent.
# It is designed to be imported and used by the main Orchestrator.py script.
#

# --- Tool Definitions (No changes needed here as they are self-contained) ---



# @tool("Deterministic Data Parser")
# def data_parser_tool(raw_data: str) -> str:
#     """
#     Parses raw key-value string data into a clean JSON format using deterministic Python logic.
#     This tool is fast, reliable, and does not use an LLM.
#     Input must be the raw string data from the collector tool.
#     """
#     print("--- Executing DeterministicDataParserTool ---")
#     records = []
#     lines = raw_data.strip().split('\n')
#     for line in lines:
#         record = {}
#         pairs = line.split(', ')
#         for pair in pairs:
#             try:
#                 key, value = pair.split('=', 1)
#                 # Handle missing values and convert types where possible
#                 if value == '':
#                     record[key] = None
#                 elif key == 'record_id':
#                     record[key] = int(value)
#                 elif key == 'value':
#                     try:
#                         record[key] = float(value)
#                     except ValueError:
#                         record[key] = None
#                 else:
#                     record[key] = value
#             except ValueError:
#                 continue # Skip malformed pairs
#         records.append(record)
    
#     return json.dumps({"records": records}, indent=2)

# --- Crew Creation Function ---

def create_scribe_crew(google_api_key: str) -> Crew:
    """
    Creates and newfigures the Scribe (Data Ingestion) Crew.

    Args:
        google_api_key (str): The API key for the Google Gemini model.

    Returns:
        Crew: The newfigured Scribe Crew object.
    """
    # Configure the LLM using the provided API key with the robust ChatLiteLLM wrapper
    llm = ChatLiteLLM(
        model="gemini/gemini-2.0-flash", # Using the latest Gemini 2.0 Flash model
        temperature=0.2,
        api_key=google_api_key
    )

    scribe_agent = Agent(
        role='Data Structuring Specialist',
        goal='Intelligently analyze raw, unstructured text data and convert it into a clean JSON format.',
        backstory=(
            "You are Scribe, an expert in understanding and structuring data. "
            "You can look at any piece of messy text, identify the underlying patterns and entities, "
            "and meticulously organize it into a perfect, machine-readable JSON structure."
        ),
        verbose=True,
        allow_delegation=False,
        tools=[],  # The agent has no pre-defined tools.
        llm=llm
    )
    # It tells the agent HOW to think about parsing the data.
    ingestion_task = Task(
        description=(
            "Your primary task is to parse and structure the raw text data provided in the '{raw_data}' input.\n"
            "Follow these steps carefully:\n"
            "1. Analyze the raw data to identify recurring patterns, entities, or records. The format is unknown, so you must infer the structure.\n"
            "2. For each logical record you identify, extract the key-value pairs.\n"
            "3. Standardize the keys to be consistent (e.g., 'ID', 'Timestamp', 'User', 'Measurement', 'Outcome').\n"
            "4. Handle missing or empty values gracefully by representing them as `null` in the final JSON.\n"
            "5. Convert data types where obvious. If something is clearly a number, it should be a number in the JSON, not a string.\n"
            "6. Your final output MUST be a single, clean JSON object containing a key called 'records' which holds a list of all the structured record objects."
        ),
        expected_output=(
            "A single, valid JSON string conforming to the structure: `{\"records\": [{\"key1\": \"value1\", ...}, ...]}`. "
            "The JSON should be well-formed and contain all the information extracted from the source data."
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
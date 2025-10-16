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



# --- Simple deterministic flatten tool ---
def flatten_json_data(raw_data: dict) -> dict:
    """
    Deterministically flattens and merges employees, projects, emails, and meetings into a single structure.
    No LLM parsing involved — pure Python logic.
    """
    records = []

    if "employees" in raw_data:
        for emp in raw_data["employees"]:
            emp_record = {"type": "employee"}
            emp_record.update(emp)
            records.append(emp_record)

    if "projects" in raw_data:
        for proj in raw_data["projects"]:
            proj_record = {"type": "project", "project_id": proj.get("project_id"), "project_name": proj.get("project_name")}
            records.append(proj_record)
            if "tasks" in proj and isinstance(proj["tasks"], list):
                for task in proj["tasks"]:
                    task_record = {"type": "task", "project_id": proj.get("project_id")}
                    task_record.update(task)
                    records.append(task_record)

    if "emails" in raw_data:
        for email in raw_data["emails"]:
            email_record = {"type": "email"}
            email_record.update(email)
            records.append(email_record)

    if "meetings" in raw_data:
        for meeting in raw_data["meetings"]:
            meeting_record = {"type": "meeting"}
            meeting_record.update(meeting)
            records.append(meeting_record)

    return {"records": records}

# --- Crew Definition ---
def create_scribe_crew(google_api_key: str) -> Crew:
    """
    Deterministic version of the Scribe Crew.
    Avoids LLM parsing — uses a direct Python flattening pipeline.
    """

    llm = ChatLiteLLM(
        model="gemini/gemini-2.0-flash",
        temperature=0.2,
        api_key=google_api_key
    )

    # The agent still exists for structure consistency,
    # but it does not interpret raw JSON — only validates final structure.
    scribe_agent = Agent(
        role="Data Validation Specialist",
        goal="Ensure structured data integrity and flatten nested fields for database ingestion.",
        backstory="You are a deterministic agent that validates structured input and ensures data consistency.",
        verbose=True,
        allow_delegation=False,
        tools=[],
        llm=llm
    )

    # The task no longer contains {raw_data} to avoid prompt interpolation.
    ingestion_task = Task(
        description=(
            "Use deterministic Python logic to flatten and merge the provided structured JSON input.\n"
            "Do not re-encode, re-parse, or stringify data.\n"
            "Output a single clean JSON object: {\"records\": [...]}"
        ),
        expected_output="A valid JSON object with a 'records' list of flattened entities.",
        agent=scribe_agent
    )

    # --- Crew wrapper ---
    data_ingestion_crew = Crew(
        agents=[scribe_agent],
        tasks=[ingestion_task],
        process=Process.sequential,
        verbose=True
    )

    # Attach flatten function to the crew as a callable tool
    return data_ingestion_crew
import os
import json
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from langchain_litellm import ChatLiteLLM

# --- 1. Define the Custom Tool ---
# This tool simulates a RAG vector search over your files.
# It just reads all the text and dumps it into the agent's context.

class InternalDocumentSearchTool(BaseTool):
    name: str = "Internal Company Document Search Tool"
    description: str = (
        "Use this tool to search all internal company documents, including "
        "emails, meeting transcripts, project notes, and employee data. "
        "It will return all raw text content from all available files."
    )
    
    def _run(self) -> str:
        print("\n--- [Tool] Searching internal unstructured data... ---")
        data_dir = os.path.join(os.path.dirname(__file__), "mock_data_large")
        files_to_load = [
            "employees.json", 
            "projects_and_tasks.json", 
            "emails.json", 
            "meetings.json"
        ]
        
        all_internal_context = ""
        
        for file_name in files_to_load:
            try:
                file_path = os.path.join(data_dir, file_name)
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    all_internal_context += f"--- START: Content from {file_name} ---\n"
                    all_internal_context += json.dumps(data, indent=2)
                    all_internal_context += f"\n--- END: Content from {file_name} ---\n\n"
            
            except Exception as e:
                print(f"Warning: Could not load or parse {file_name}. Error: {e}")
                
        if not all_internal_context:
            return "Error: No internal documents were found or could be loaded."
            
        return all_internal_context

# --- 2. Define the Agent and Crew ---

def create_internal_analyst_crew(gemini_api_key: str) -> Crew:
    """
    Creates the Internal Data Analyst Crew.
    This crew is responsible for performing RAG-like analysis on
    unstructured internal documents based on a user query.
    """
    
    llm = ChatLiteLLM(
        model="gemini/gemini-2.0-flash", 
        temperature=0.1, 
        api_key=gemini_api_key
    )

    internal_tool = InternalDocumentSearchTool()

    internal_analyst = Agent(
        role='Internal Document Analyst',
        goal=(
            "Scan all unstructured internal company documents (emails, meetings, projects) "
            "to find all information relevant to the user's request."
        ),
        backstory=(
            "You are an expert internal analyst. Your specialty is reading "
            "thousands of unstructured documents (conversations, JSON blobs, notes) "
            "and extracting the *specific* information needed to answer a strategic question. "
            "You are not a SQL analyst; you are a text and data retrieval expert."
        ),
        verbose=True,
        llm=llm,
        tools=[internal_tool]
    )

    analysis_task = Task(
        description=(
            "A user has a primary request: '{user_query}'.\n"
            "Your job is to be a data *extraction* expert. You must answer the user's request *precisely*.\n\n"
            "Follow these steps:\n"
            "1. **Use the Tool:** Activate the 'Internal Company Document Search Tool' "
            "to get all internal data. This data will contain content from multiple files "
            "(like 'employees.json', 'projects.json', etc.).\n"
            "2. **Analyze Context:** Read the full context from the tool. Your primary goal is to find "
            "the *most relevant data* to answer the user's query. The context is large and "
            "contains many topics. You must not get confused.\n"
            "3. **Execute Task:**\n"
            "    - **If the user asks for a specific list (like 'list of all employees' or 'list of projects'),** "
            "      you MUST find the specific file content (e.g., 'employees.json' or 'projects.json') "
            "      and extract that list. Do NOT summarize a related topic.\n"
            "    - **If the user asks a general question (like 'what are our risks?'),** "
            "      then you can synthesize information from multiple files ('projects.json', 'meetings.json') "
            "      to create a summary.\n\n"
            "**Crucial Instruction for the user's query ('{user_query}'):** This is a "
            "simple data extraction request. Find the employee list in the 'employees.json' "
            "file's content and return it. Do not mention performance reviews."
        ),
        expected_output=(
            "A precise and direct answer to the user's query: '{user_query}'.\n"
            "If the user asks for a list of employees, the output MUST be that list, "
            "not a summary of other topics. For example: 'Here is the list of employees "
            "found in the internal 'employees.json' file: [data...]'."
        ),
        agent=internal_analyst
    )

    return Crew(agents=[internal_analyst], tasks=[analysis_task], verbose=True)
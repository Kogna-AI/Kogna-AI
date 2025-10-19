import os
import json
import re
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from langchain_litellm import ChatLiteLLM

# --- 1. Define the Tool (with a memory) ---

class InternalDocumentRouterTool(BaseTool):
    name: str = "Internal Company Document Search Tool"
    description: str = (
        "You MUST use this tool to find relevant internal company data. "
        "Pass the user's original query to this tool. "
        "It will intelligently search the company's knowledge base "
        "using content previews and return ALL relevant documents."
    )
    llm: ChatLiteLLM = None
    data_dir: str = ""
    file_previews: dict = {}
    last_chosen_files: list[str] = []  # <--- 1. ADD MEMORY

    def __init__(self, llm: ChatLiteLLM):
        super().__init__()
        self.llm = llm
        self.data_dir = os.path.join(os.path.dirname(__file__), "mock_data_large")
        self.file_previews = self._generate_previews()
        self.last_chosen_files = [] # Ensure it's reset on init

    def _generate_previews(self) -> dict:
        # ... (This function is unchanged)
        print("\n--- [Smart Tool Init] Generating file previews... ---")
        previews = {}
        try:
            for filename in os.listdir(self.data_dir):
                if filename.endswith(".json"):
                    file_path = os.path.join(self.data_dir, filename)
                    try:
                        with open(file_path, 'r') as f:
                            preview_lines = [next(f) for _ in range(10)]
                        preview_content = "".join(preview_lines)
                        previews[filename] = preview_content
                        print(f"--- [Smart Tool Init] Created preview for {filename}")
                    except Exception as e:
                        print(f"Warning: Could not read {filename} for preview: {e}")
            
            if not previews:
                print("--- [Smart Tool Init] CRITICAL: No .json files found in 'mock_data_large' directory. ---")
            
            return previews
        except FileNotFoundError:
            print(f"--- [Smart Tool Init] CRITICAL: 'mock_data_large' directory not found at {self.data_dir} ---")
            return {}

    def _run(self, query: str) -> str:
        # ... (This function is mostly unchanged, except for one line)
        print(f"\n--- [Smart Tool] Received query: '{query}' ---")
        self.last_chosen_files = [] # Reset for this run
        
        if not self.file_previews:
            return "Error: No internal documents are available. The tool was not initialized correctly."

        # ... (Router Prompt Logic is unchanged) ...
        previews_list = "\n\n".join([
            f"Filename: {file}\nPreview:\n{preview}" 
            for file, preview in self.file_previews.items()
        ])
        
        router_prompt = f"""
        You are an expert data router. Your job is to select ALL files
        that are relevant to answering the user's query, based on a preview of their content.

        User Query: "{query}"

        Available Data Files and their Content Previews:
        ---
        {previews_list}
        ---

        Return a JSON-formatted list of *all* relevant filenames.
        - If the query is 'list of employees', return `["employees.json"]`.
        - If the query is 'risks for Alpha project', you might return `["projects.json", "meetings.json"]`.
        - If no files are relevant, return an empty list `[]`.
        
        Return *only* the JSON list and nothing else.
        """
        
        # 2. Call the LLM to decide
        try:
            print("--- [Smart Tool] Asking router LLM to pick file(s)... ---")
            router_response = self.llm.invoke(router_prompt)
            
            match = re.search(r'\[.*\]', router_response.content, re.DOTALL)
            if not match:
                raise ValueError("Router LLM did not return a valid JSON list.")
            
            chosen_files = json.loads(match.group(0))
            
            self.last_chosen_files = chosen_files  # <--- 2. SAVE THE CHOICE

        except Exception as e:
            return f"Error during router LLM call or JSON parsing: {e}. Response was: {router_response.content}"

        # 3. Validate and load the chosen files
        if not chosen_files:
            print(f"--- [Smart Tool] Router found no relevant files. ---")
            return f"No relevant internal documents were found for the query: '{query}'"

        print(f"--- [Smart Tool] Router chose: {chosen_files} ---")
        
        all_relevant_content = ""
        # ... (Loading loop is unchanged) ...
        for filename in chosen_files:
            if filename in self.file_previews:
                print(f"--- [Smart Tool] Loading full content of {filename}... ---")
                try:
                    file_path = os.path.join(self.data_dir, filename)
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        content = json.dumps(data, indent=2)
                    
                    all_relevant_content += (
                        f"--- START: Full Content from {filename} ---\n"
                        f"{content}\n"
                        f"--- END: Full Content from {filename} ---\n\n"
                    )
                except Exception as e:
                    all_relevant_content += f"Error loading file {filename}: {e}\n\n"
            else:
                 all_relevant_content += f"Router chose an invalid file: {filename}\n\n"
        
        return all_relevant_content

# --- 2. Define the Agent and Crew ---

def create_internal_analyst_crew(gemini_api_key: str): # <--- 3. REMOVED -> Crew
    """
    Creates the Internal Data Analyst Crew.
    This function now returns BOTH the Crew and the tool instance.
    """
    
    llm = ChatLiteLLM(
        model="gemini/gemini-2.0-flash", 
        temperature=0.1, 
        api_key=gemini_api_key
    )

    internal_tool = InternalDocumentRouterTool(llm=llm)

    internal_analyst = Agent(
        role='Internal Document Analyst',
        goal=(
            "Use the provided search tool to find all relevant internal "
            "documents to answer the user's request."
        ),
        backstory=(
            "You are an expert retrieval analyst. You do not have direct access "
            "to the data. You MUST use your 'Internal Company Document Search Tool' "
            "to find the information you need. You trust the tool to be smart "
            "and give you all the relevant documents."
        ),
        verbose=True,
        llm=llm,
        tools=[internal_tool]
    )

    analysis_task = Task(
        description=(
            "A user has a primary request: '{user_query}'.\n"
            "Your job is to find the *internal* data to answer this.\n\n"
            "Follow these steps:\n"
            "1. **Use the Tool:** You MUST call the 'Internal Company Document Search Tool' "
            "and pass the user's *exact* query, '{user_query}', to it. "
            "This tool will use AI to search all internal files by preview "
            "and return the full content of ALL relevant document(s).\n"
            "2. **Analyze Content:** Read all the document content returned by the tool.\n"
            "3. **Synthesize Findings:** Based *only* on the documents provided by the tool, "
            "create the 'Internal Analysis Report' that directly answers '{user_query}'."
        ),
        expected_output=(
            "A comprehensive 'Internal Analysis Report' that summarizes all "
            "relevant information found in the *document(s)* retrieved by the tool "
            "to answer the user's query: '{user_query}'."
        ),
        agent=internal_analyst
    )

    # --- 4. RETURN BOTH THE CREW AND THE TOOL INSTANCE ---
    return Crew(agents=[internal_analyst], tasks=[analysis_task], verbose=True), internal_tool
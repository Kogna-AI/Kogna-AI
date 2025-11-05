# internal_analyst_agent.py (Supabase Storage Version)
import os
import json
import re
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from supabase_connect import get_supabase_manager # <-- Use the connector
from dotenv import load_dotenv
from langchain_litellm import ChatLiteLLM
load_dotenv()

# --- Connect to Supabase ---
try:
    supabase_manager = get_supabase_manager()
    supabase = supabase_manager.client
except Exception as e: # Catch a broader exception initially
    print(f"CRITICAL ERROR: Could not connect to Supabase in internal_analyst_agent.py. Check credentials and connection. Error: {e}")
    supabase = None # Set supabase to None to handle errors gracefully later

YOUR_BUCKET_NAME = "Kogna" # <-- Set to your bucket name

# --- 1. Define the Supabase-Aware Tool ---

class InternalDocumentRouterTool(BaseTool):
    name: str = "Internal Company Document Search Tool"
    description: str = (
        "You MUST use this tool to find relevant internal company data. "
        "Pass the user's original query to this tool. "
        "It will intelligently search the company's knowledge base "
        "using content previews and return ALL relevant documents."
    )
    llm: ChatLiteLLM = None
    supabase_client: any = None
    bucket_name: str = ""
    file_previews: dict = {}
    last_chosen_files: list[str] = []

    def __init__(self, llm: ChatLiteLLM, supabase_client: any, bucket_name: str):
        super().__init__()
        self.llm = llm
        self.supabase_client = supabase_client
        self.bucket_name = bucket_name
        # Generate previews only if Supabase client is valid
        if self.supabase_client:
            self.file_previews = self._generate_previews()
        else:
            self.file_previews = {}
            print("--- [Smart Tool Init] Supabase client is invalid. Cannot generate previews. ---")
        self.last_chosen_files = []

    def _generate_previews(self) -> dict:
        """
        Reads the first 10 lines of each .json file in the Supabase bucket
        to create a 'preview' for the routing LLM.
        """
        print(f"\n--- [Smart Tool Init] Generating file previews from Supabase bucket '{self.bucket_name}'... ---")
        previews = {}
        if not self.supabase_client:
            print("--- [Smart Tool Init] CRITICAL: Supabase client not available. ---")
            return {}

        try:
            # --- List files from Supabase bucket ---
            storage_interface = self.supabase_client.storage.from_(self.bucket_name)
            # Add error handling for the list operation itself
            try:
                files_list = storage_interface.list()
            except Exception as list_error:
                 print(f"--- [Smart Tool Init] CRITICAL: Failed to list files in Supabase bucket '{self.bucket_name}': {list_error} ---")
                 print("      Check bucket name, RLS policies (SELECT for anon/auth), and Supabase connection.")
                 return {}


            if not files_list:
                 print(f"--- [Smart Tool Init] Warning: No files found in Supabase bucket '{self.bucket_name}'. ---")
                 return {}

            print(f"--- [Smart Tool Init] Found {len(files_list)} item(s) in bucket. Processing JSON files... ---")
            json_found = False
            for file_info in files_list:
                # Supabase list() returns dicts like {'name': 'file.json', ...}
                filename = file_info.get('name')
                if filename and filename.endswith(".json"):
                    json_found = True
                    try:
                        # --- Download file content for preview ---
                        print(f"--- [Smart Tool Init] Downloading {filename} for preview...")
                        # Timeout added for robustness
                        file_content_bytes = storage_interface.download(filename)

                        if file_content_bytes:
                            preview_content = file_content_bytes.decode('utf-8')
                            preview_lines = preview_content.splitlines()[:10]
                            previews[filename] = "\n".join(preview_lines)
                            print(f"--- [Smart Tool Init] Created preview for {filename}")
                        else:
                             print(f"Warning: Download of {filename} returned empty content.")

                    except Exception as e:
                        print(f"Warning: Could not read {filename} from Supabase for preview: {e}")
                        # Provide more specific feedback if it's likely permissions
                        if "RLS" in str(e) or "policy" in str(e) or "403" in str(e) or "unauthorized" in str(e).lower():
                           print("      Hint: This might be a Supabase RLS Policy issue. Ensure SELECT permission is granted.")

            if not json_found:
                 print(f"--- [Smart Tool Init] CRITICAL: No .json files found in Supabase bucket '{self.bucket_name}'. Check file uploads and extensions. ---")
            elif not previews:
                 print(f"--- [Smart Tool Init] CRITICAL: Found JSON files, but failed to read any for previews. Check RLS policies and file integrity. ---")


            return previews
        except Exception as e:
            # Catch potential errors with the client/bucket interaction itself
            print(f"--- [Smart Tool Init] CRITICAL: An unexpected error occurred during preview generation: {e} ---")
            return {}


    def _run(self, query: str) -> str:
        print(f"\n--- [Smart Tool] Received query: '{query}' ---")
        self.last_chosen_files = []

        if not self.supabase_client:
             return "Error: Supabase client is not available. Cannot search documents."
        if not self.file_previews:
            # Give a more informative error based on initialization failure
            return "Error: No internal document previews are available. Tool initialization likely failed. Check Supabase connection, bucket name ('{}'), file permissions (RLS SELECT), and ensure valid .json files exist in the bucket.".format(self.bucket_name)


        # --- ROUTER LOGIC (UNCHANGED) ---
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
        - If no files are relevant, return an empty list `[]`.
        Return *only* the JSON list and nothing else.
        """

        try:
            print("--- [Smart Tool] Asking router LLM to pick file(s)... ---")
            router_response = self.llm.invoke(router_prompt)

            # Improved JSON extraction
            match = re.search(r'```json\s*(\[.*\])\s*```|(\[.*\])', router_response.content, re.DOTALL | re.IGNORECASE)
            if not match:
                # Try a simpler regex as fallback
                match = re.search(r'(\[.*\])', router_response.content, re.DOTALL)
                if not match:
                     raise ValueError(f"Router LLM did not return a valid JSON list format. Raw response: '{router_response.content}'")

            json_str = match.group(1) if match.group(1) and '[' in match.group(1) else match.group(2) # Prefer group 1 if it exists and looks like json
            if not json_str:
                 raise ValueError(f"Could not extract JSON list from LLM response. Raw response: '{router_response.content}'")

            chosen_files = json.loads(json_str)
            self.last_chosen_files = chosen_files

        except json.JSONDecodeError as json_err:
             raw_response_content = "N/A"
             if 'router_response' in locals() and hasattr(router_response, 'content'):
                 raw_response_content = router_response.content
             return f"Error parsing JSON list from LLM: {json_err}. Extracted string: '{json_str}'. Raw LLM Response: '{raw_response_content}'"
        except Exception as e:
             raw_response_content = "N/A"
             if 'router_response' in locals() and hasattr(router_response, 'content'):
                 raw_response_content = router_response.content
             return f"Error during router LLM call or JSON parsing: {e}. Raw LLM Response: '{raw_response_content}'"


        if not chosen_files:
            print(f"--- [Smart Tool] Router found no relevant files. ---")
            return f"No relevant internal documents were found for the query: '{query}'"

        # Ensure chosen_files is actually a list
        if not isinstance(chosen_files, list):
            print(f"--- [Smart Tool] Router returned non-list: {chosen_files}. Assuming no relevant files. ---")
            self.last_chosen_files = []
            return f"No relevant internal documents were found for the query: '{query}' (Router returned invalid format)."


        print(f"--- [Smart Tool] Router chose: {chosen_files} ---")

        # --- Load chosen files from Supabase ---
        all_relevant_content = ""
        storage_interface = self.supabase_client.storage.from_(self.bucket_name)
        loaded_any = False
        for filename in chosen_files:
            # Basic validation of filename format
            if not isinstance(filename, str) or not filename.endswith(".json"):
                all_relevant_content += f"Router chose an invalid filename format: {filename}\n\n"
                continue

            if filename in self.file_previews: # Check against known files from previews
                print(f"--- [Smart Tool] Loading full content of {filename} from Supabase... ---")
                try:
                    # Download the full file content
                    file_content_bytes = storage_interface.download(filename)
                    if file_content_bytes:
                        # Decode from bytes to string
                        content = file_content_bytes.decode('utf-8')
                        all_relevant_content += (
                            f"--- START: Full Content from {filename} ---\n"
                            f"{content}\n"
                            f"--- END: Full Content from {filename} ---\n\n"
                        )
                        loaded_any = True
                    else:
                        all_relevant_content += f"Warning: Download of {filename} returned empty content.\n\n"
                except Exception as e:
                    all_relevant_content += f"Error loading file {filename} from Supabase: {e}\n\n"
                    if "RLS" in str(e) or "policy" in str(e) or "403" in str(e) or "unauthorized" in str(e).lower():
                       print("      Hint: Check Supabase RLS Policies for SELECT permission on this file/bucket.")
            else:
                 all_relevant_content += f"Router chose a file not found during preview generation: {filename}. It might be new or misspelled.\n\n"

        # Check if router picked files but none could be loaded
        if not loaded_any and chosen_files:
             # Add the partial content which contains error messages
             return f"Error: Router selected files {chosen_files}, but failed to load content for any of them from Supabase.\n\nDetails:\n{all_relevant_content}"
        elif not all_relevant_content.strip() and chosen_files:
             # This case should ideally be covered above, but as a fallback
             return f"Error: Router selected files {chosen_files}, but resulted in empty content after attempting loads."

        return all_relevant_content


# --- 2. Define the Agent and Crew ---

def create_internal_analyst_crew(gemini_api_key: str):
    """
    Creates the Internal Data Analyst Crew using Supabase Storage.
    Returns BOTH the Crew and the tool instance.
    """

    # Handle case where Supabase connection failed at module level
    if not supabase:
        raise ConnectionError("Cannot create internal analyst crew: Supabase client failed to initialize.")

    llm = ChatLiteLLM(
        model="gemini/gemini-2.0-flash", # <-- Corrected Model Name
        temperature=0.1,
        api_key=gemini_api_key
    )

    # --- Pass Supabase Client and Bucket Name ---
    internal_tool = InternalDocumentRouterTool(
        llm=llm,
        supabase_client=supabase, # Use the client from the top of the file
        bucket_name=YOUR_BUCKET_NAME
    )

    internal_analyst = Agent(
        role='Internal Document Analyst',
        goal=(
            "Use the provided search tool to find all relevant internal "
            "documents to answer the user's request, using chat history for context."
        ),
        backstory=(
            "You are an expert retrieval analyst. You do not have direct access "
            "to the data. You MUST use your 'Internal Company Document Search Tool' "
            "to find the information you need. You trust the tool to be smart "
            "and give you all the relevant documents."
        ),
        verbose=False,
        llm=llm,
        tools=[internal_tool]
    )
    analysis_task = Task(
        description=(
            "A user has a primary request. You MUST analyze the conversation history for context, "
            "as the latest query may be a follow-up question.\n\n"
            "--- CONVERSATION HISTORY ---\n"
            "{chat_history_str}\n"
            "--- END HISTORY ---\n\n"
            "Your job is to find the *internal* data to answer the *latest* user query: '{user_query}'.\n"
            "Use the history to understand pronouns (like 'they', 'it', 'those').\n\n"
            "Follow these steps:\n"
            "1. **Analyze Context:** Look at the latest query '{user_query}' and the history.\n"
            "2. **Formulate Search Query:** Create an intelligent search query for the tool. "
            "   - If the query is 'who are they' and the history mentions 'Product Manager, Marketing Manager', "
            "     your search query for the tool should be 'details for Product Manager, Marketing Manager, Ops Lead'.\n"
            "   - If the query is 'summarize the data', just pass that to the tool.\n"
            "3. **Use the Tool:** Call the 'Internal Company Document Search Tool' with your formulated search query.\n"
            "4. **Synthesize Findings:** Based *only* on the documents provided by the tool, "
            "create the 'Internal Analysis Report' that directly answers the user's latest query."
        ),
        expected_output=(
            "A comprehensive 'Internal Analysis Report' that summarizes all "
            "relevant information found in the document(s) to answer the user's query: '{user_query}', "
            "using the provided conversation history for context. "
            "If the tool failed, report the error."
        ),
        agent=internal_analyst
    )
    return Crew(agents=[internal_analyst], tasks=[analysis_task], verbose=False), internal_tool
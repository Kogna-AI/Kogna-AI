import os
import json
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from supabase_connect import get_supabase_manager
from dotenv import load_dotenv
from langchain_litellm import ChatLiteLLM
# --- New Import ---
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from .prompt import ( # Use relative import if in the same directory
    INTERNAL_ANALYST_ROLE,
    INTERNAL_ANALYST_GOAL,
    INTERNAL_ANALYST_BACKSTORY,
    INTERNAL_ANALYST_TASK_DESCRIPTION,
    INTERNAL_ANALYST_EXPECTED_OUTPUT,
)
load_dotenv()

# --- Connect to Supabase ---
try:
    supabase_manager = get_supabase_manager()
    supabase = supabase_manager.client
except Exception as e: 
    print(f"CRITICAL ERROR: Could not connect to Supabase in internal_analyst_agent.py. Check credentials and connection. Error: {e}")
    supabase = None 

# --- 1. Define the NEW RAG Tool ---

class VectorSearchTool(BaseTool):
    name: str = "Internal Knowledge Base Search Tool"
    description: str = (
        "You MUST use this tool to find information about the company. "
        "Pass the user's original query to this tool. "
        "It will search all company documents (Jira, Google Drive, etc.) "
        "and return the most relevant text snippets."
    )
    llm: ChatLiteLLM = None
    supabase_client: any = None
    embeddings_model: any = None
    user_id: str = "" # We'll store the user ID here

    def __init__(self, llm: ChatLiteLLM, supabase_client: any, embeddings_model: any, user_id: str):
        super().__init__()
        self.llm = llm
        self.supabase_client = supabase_client
        self.embeddings_model = embeddings_model
        self.user_id = user_id # Store the user ID from the constructor

    def _run(self, query: str) -> str:
        """
        Runs the vector search against the user's query.
        """
        print(f"\n--- [RAG Tool] Received query: '{query}' for user {self.user_id} ---")
        
        if not self.supabase_client or not self.embeddings_model:
            return "Error: VectorSearchTool is not initialized."

        try:
            # 1. Embed the user's query
            print(f"--- [RAG Tool] Embedding user query...")
            query_embedding = self.embeddings_model.embed_query(query)

            # 2. Call the Supabase RPC function (that we created in SQL)
            print(f"--- [RAG Tool] Calling Supabase RPC 'match_document_chunks'...")
            response = self.supabase_client.rpc(
                "match_document_chunks",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": 0.5,  # Similarity threshold
                    "match_count": 10,       # Get top 10 chunks
                    "p_user_id": self.user_id  # Pass the user ID
                }
            ).execute()

            data = getattr(response, "data", [])
            if not data:
                print("--- [RAG Tool] No relevant chunks found.")
                return "No relevant internal documents were found for this query."
            
            print(f"--- [RAG Tool] Found {len(data)} relevant chunks.")

            # 3. Format the chunks into a single string for the agent
            context_string = "Here are the relevant information snippets found:\n\n"
            for i, item in enumerate(data):
                context_string += (
                    f"--- Snippet {i+1} from {item['file_path']} (Similarity: {item['similarity']:.2f}) ---\n"
                    f"{item['content']}\n"
                    f"-----------------------------------------------------------------------\n\n"
                )
            
            return context_string

        except Exception as e:
            print(f"Error in VectorSearchTool _run: {e}")
            import traceback
            traceback.print_exc()
            return f"Error during vector search: {e}"

# --- 2. Define the Agent and Crew (Updated) ---

def create_internal_analyst_crew(gemini_api_key: str, user_id: str):
    """
    Creates the Internal Data Analyst Crew using the RAG pipeline.
    Returns the Crew instance.
    """
    if not supabase:
        raise ConnectionError("Cannot create internal analyst crew: Supabase client failed to initialize.")

    # 1. Initialize the LLM for the Agent
    llm = ChatLiteLLM(
        model="gemini/gemini-2.0-flash",
        temperature=0.1,
        api_key=gemini_api_key
    )

    # 2. Initialize the Embedding Model for the Tool
    try:
        embeddings_model = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=gemini_api_key
        )
    except Exception as e:
        print(f"CRITICAL ERROR: Could not initialize embedding model in agent: {e}")
        raise ConnectionError(f"Failed to initialize embedding model: {e}")

    # 3. Create the new RAG Tool, passing the user_id
    rag_tool = VectorSearchTool(
        llm=llm,
        supabase_client=supabase,
        embeddings_model=embeddings_model,
        user_id=user_id
    )

    # 4. Create the Agent (No changes needed here)
    internal_analyst = Agent(
        role=INTERNAL_ANALYST_ROLE,          # <-- Use variable
        goal=INTERNAL_ANALYST_GOAL,          # <-- Use variable
        backstory=INTERNAL_ANALYST_BACKSTORY,# <-- Use variable
        verbose=False,
        llm=llm,
        tools=[rag_tool]
    )

    # 5. Create the Task (USE IMPORTED PROMPTS)
    analysis_task = Task(
        description=INTERNAL_ANALYST_TASK_DESCRIPTION, # <-- Use variable
        expected_output=INTERNAL_ANALYST_EXPECTED_OUTPUT, # <-- Use variable
        agent=internal_analyst
    )

    # 6. Create the Crew
    return Crew(agents=[internal_analyst], tasks=[analysis_task], verbose=False)
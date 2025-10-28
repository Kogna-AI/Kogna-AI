# Backend/Ai_agents/communication_agent.py

from crewai import Agent, Task, Crew, Process
# from crewai_tools import SerpApiGoogleSearchTool # Not needed
# from supabase_connect import get_supabase_manager # Not needed
from dotenv import load_dotenv
from typing import List, Optional
from langchain_litellm import ChatLiteLLM

# --- NEW: Import prompts ---
from .prompt import (
    COMMUNICATOR_ROLE,
    COMMUNICATOR_GOAL,
    COMMUNICATOR_BACKSTORY,
    COMMUNICATOR_TASK_DESCRIPTION,
    COMMUNICATOR_EXPECTED_OUTPUT
)

load_dotenv()

# No Supabase needed directly
# supabase_manager = get_supabase_manager()
# supabase = supabase_manager.client

def create_communication_crew(
    synthesis_context: str,
    user_query: str,
    # internal_sources: Optional[List[str]], # No longer needed for final formatting
    google_api_key: str,
    # serper_api_key: str # No longer needed
) -> Crew:
    """
    Creates and configures the Communications Crew using prompts from prompts.py.
    """

    llm = ChatLiteLLM(
        model="gemini/gemini-2.0-flash",
        temperature=0.2, # Low temp for factual formatting
        api_key=google_api_key
    )

    communications_agent = Agent(
        role=COMMUNICATOR_ROLE,                     # <-- Use variable
        goal=COMMUNICATOR_GOAL.format(user_query=user_query), # <-- Format goal
        backstory=COMMUNICATOR_BACKSTORY,           # <-- Use variable
        verbose=False,
        allow_delegation=False,
        llm=llm,
        tools=[] # Communicator doesn't need external tools
    )

    # --- Prepare dynamic parts for the task ---
    # Simplified source text handling as it's less critical for the final output formatting now
    # sources_text = "internal documents and web search"
    # if internal_sources:
    #     valid_sources = [s for s in internal_sources if s]
    #     if valid_sources:
    #         sources_text = ", ".join(valid_sources) + ", Web Search"


    # Format the task description
    task_description = COMMUNICATOR_TASK_DESCRIPTION.format(
        user_query=user_query,
        synthesis_context=synthesis_context,
        # sources_text=sources_text # Pass if needed by the prompt
    )

    # Format the expected output
    expected_output = COMMUNICATOR_EXPECTED_OUTPUT.format(user_query=user_query)

    # --- Create the Task ---
    dynamic_formatting_task = Task(
        description=task_description,
        expected_output=expected_output,
        agent=communications_agent
    )

    # Assemble the crew
    communication_crew = Crew(
        agents=[communications_agent],
        tasks=[dynamic_formatting_task],
        verbose=False, # Set to True for debugging steps
        process="sequential"
    )

    return communication_crew
# Backend/Ai_agents/research_agent.py

from crewai import Agent, Task, Crew
# from crewai.tools import tool # Not needed if only using SerpApi
from crewai_tools import SerpApiGoogleSearchTool
# import requests # Not needed if only using SerpApi
from langchain_litellm import ChatLiteLLM
# from supabase_connect import get_supabase_manager # Not needed for this agent
from dotenv import load_dotenv

# --- NEW: Import prompts ---
from .prompt import (
    RESEARCHER_ROLE,
    RESEARCHER_GOAL,
    RESEARCHER_BACKSTORY,
    RESEARCHER_TASK_DESCRIPTION,
    RESEARCHER_EXPECTED_OUTPUT
)

load_dotenv()

# No Supabase needed for this agent
# supabase_manager = get_supabase_manager()
# supabase = supabase_manager.client

def create_research_crew(
    user_query: str,
    google_api_key: str,
    serper_api_key: str,
) -> Crew:
    """
    Creates and configures the Business Research Crew using prompts from prompts.py.
    """

    # --- Agent Configuration ---
    llm = ChatLiteLLM(
        model="gemini/gemini-2.0-flash",
        temperature=0.7, # Keep some creativity for research synthesis
        api_key=google_api_key
    )

    search_tool = SerpApiGoogleSearchTool(api_key=serper_api_key)

    research_agent = Agent(
        role=RESEARCHER_ROLE,                   # <-- Use variable
        goal=RESEARCHER_GOAL.format(user_query=user_query), # <-- Format goal
        backstory=RESEARCHER_BACKSTORY,         # <-- Use variable
        verbose=False,
        allow_delegation=False,
        llm=llm,
        tools=[search_tool]
    )

    # --- Task Definition ---
    web_research_task = Task(
        description=RESEARCHER_TASK_DESCRIPTION.format(user_query=user_query), # <-- Format description
        expected_output=RESEARCHER_EXPECTED_OUTPUT.format(user_query=user_query), # <-- Format output
        agent=research_agent
    )

    # Create and return the Crew
    research_crew = Crew(
        agents=[research_agent],
        tasks=[web_research_task],
        verbose=False, # Set to True for debugging steps
        process="sequential"
    )

    return research_crew
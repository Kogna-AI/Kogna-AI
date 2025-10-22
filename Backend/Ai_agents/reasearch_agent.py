# research_crew.py (Corrected)

from crewai import Agent, Task, Crew
from crewai.tools import tool
from crewai_tools import SerpApiGoogleSearchTool
import requests
from langchain_litellm import ChatLiteLLM  # <-- Corrected import
from supabase_connect import get_supabase_manager
from dotenv import load_dotenv

load_dotenv()

#connect to supabase
supabase_manager = get_supabase_manager()
supabase = supabase_manager.client

def create_research_crew(
    user_query: str,  # <--- 1. IT MUST ACCEPT THE USER'S QUERY
    google_api_key: str,
    serper_api_key: str,
    # (Other creds are fine to leave commented out)
) -> Crew:
    """
    Creates and configures the Business Research Crew.
    This crew now focuses ONLY on web research based on the user's query.
    """

    # --- (Commented-out internal tools are fine) ---

    # --- Agent Configuration ---

    llm = ChatLiteLLM(
        model="gemini/gemini-2.0-flash", # <-- 2. FIXED MODEL NAME
        temperature=0.7,
        api_key=google_api_key
    )

    # This is the correct tool for this agent
    search_tool = SerpApiGoogleSearchTool(api_key=serper_api_key)

    research_agent = Agent(
        role='Senior Web Research Analyst', # <-- 3. Role is now web-focused
        goal='Conduct thorough external web research to find information relevant to the user query.',
        backstory="""You are an expert web research analyst. You use your
        SerpApiGoogleSearchTool to find the most relevant, up-to-date
        information from the internet to answer complex business questions.""",
        verbose=False,
        allow_delegation=False,
        llm=llm,
        tools=[search_tool] # <-- This is correct
    )

    # --- 4. DYNAMIC TASK (REPLACED HARD-CODED QBR TASK) ---
    web_research_task = Task(
        description=f"""
        A user has a primary request: '{user_query}'.
        
        Your job is to use your 'SerpApiGoogleSearchTool' to find
        external, public information that can help answer this request.
        
        Focus on finding competitor information, market trends, public news,
        and any other relevant data from the web.
        
        If the user's query seems purely internal (e.g., 'list my employees'),
        simply state that 'No external web research is relevant for this internal query.'
        """,
        expected_output="""
        A 'Business Research Findings' report. This report should
        summarize the top 3-5 key findings from your web search.
        
        If no relevant external information was found,
        return the string: 'No relevant external information found.'
        """,
        agent=research_agent
    )

    # Create and return the Crew
    research_crew = Crew(
        agents=[research_agent],
        tasks=[web_research_task], # <-- 5. Use the new dynamic task
        verbose=False,
        process="sequential"
    )
    
    return research_crew
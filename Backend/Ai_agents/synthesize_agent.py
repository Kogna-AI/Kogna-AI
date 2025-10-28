# Backend/Ai_agents/synthesize_agent.py

from crewai import Agent, Task, Crew, Process
from datetime import datetime
# from supabase_connect import get_supabase_manager # Not needed if agent doesn't directly access DB
from dotenv import load_dotenv
from typing import List, Optional
from langchain_litellm import ChatLiteLLM

# --- NEW: Import prompts ---
from .prompt import (
    SYNTHESIZER_ROLE,
    SYNTHESIZER_GOAL,
    SYNTHESIZER_BACKSTORY,
    SYNTHESIZER_TASK_DESCRIPTION,
    SYNTHESIZER_FEEDBACK_SUFFIX, # Import the feedback part
    SYNTHESIZER_EXPECTED_OUTPUT
)

load_dotenv()

# No Supabase needed directly by this agent
# supabase_manager = get_supabase_manager()
# supabase = supabase_manager.client

def create_synthesis_crew(
    internal_analysis_report: str,
    internal_sources: Optional[List[str]], # Still accept sources for context
    business_research_findings: str,
    google_api_key: str,
    human_feedback: Optional[str] = None # Use Optional here
) -> Crew:
    """
    Creates and configures the Strategic Synthesis Crew using prompts from prompts.py.
    """
    current_time = datetime.now().strftime("%I:%M %p %Z on %A, %B %d, %Y")
    current_date = datetime.now().strftime("%Y-%m-%d")

    llm = ChatLiteLLM(
        model="gemini/gemini-2.0-flash",
        temperature=0.6, # Keep some creativity for synthesis
        api_key=google_api_key
    )

    synthesizer_agent = Agent(
        role=SYNTHESIZER_ROLE,          # <-- Use variable
        goal=SYNTHESIZER_GOAL,          # <-- Use variable
        backstory=SYNTHESIZER_BACKSTORY,# <-- Use variable
        verbose=False,
        allow_delegation=False,
        llm=llm,
        tools=[] # Synthesizer doesn't need external tools
    )

    # --- Prepare dynamic parts for the description ---
    sources_text = "Not specified or not applicable (RAG snippets used)."
    if internal_sources:
        valid_sources = [s for s in internal_sources if s]
        if valid_sources:
            sources_text = ", ".join(valid_sources)

    # Format the base description
    task_description = SYNTHESIZER_TASK_DESCRIPTION.format(
        current_date=current_date,
        current_time=current_time,
        sources_text=sources_text,
        internal_analysis_report=internal_analysis_report,
        business_research_findings=business_research_findings
    )

    # Append feedback if provided
    if human_feedback:
        task_description += SYNTHESIZER_FEEDBACK_SUFFIX.format(human_feedback=human_feedback)

    # Prepare feedback string for expected output (optional, but good practice)
    feedback_str = f"(incorporating feedback: {human_feedback})" if human_feedback else "(no feedback provided)"

    # Format expected output
    expected_output = SYNTHESIZER_EXPECTED_OUTPUT # .format(human_feedback_str=feedback_str) # Uncomment if you add placeholder

    # --- Create the Task ---
    synthesis_task = Task(
        description=task_description,
        expected_output=expected_output,
        agent=synthesizer_agent
    )

    return Crew(
        agents=[synthesizer_agent],
        tasks=[synthesis_task],
        process=Process.sequential,
        verbose=False, # Set to True for debugging steps
    )
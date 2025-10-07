from crewai import Agent, Task, Crew
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool, DirectoryReadTool, SerperDevTool
import os
from dotenv import load_dotenv

load_dotenv()

#
# This is the refactored script for the Communications Agent.
# It is designed to be imported and used by the main Orchestrator.py script.
#

def create_communication_crew(synthesis_context: str):
    """
    Creates and configures the Communications Crew.

    Args:
        synthesis_context (str): The final synthesis report from the previous agent,
                                 passed in-memory to be used as context.

    Returns:
        Crew: The configured Communications Crew object.
    """

    # Define the LLM for this agent
    llm = LLM(
        model="claude/opus-4.1",  # Claude Opus is great for nuanced, high-quality writing
        temperature=0.5,
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )

    # Initialize tools
    search_tool = SerperDevTool(api_key=os.getenv("SERPER_API_KEY"))

    # Define the Communications Agent
    communications_agent = Agent(
        role="Executive Communications Strategist",
        goal="Translate complex analyses and strategic advice into clear, concise, and executive-ready language.",
        backstory="""You are the Communications Agent, an expert in transforming complex analytical reports
        into compelling narratives that executives can easily understand and act on.
        You focus on clarity, brevity, and strategic tone suitable for board meetings, investor updates, or QBRs.""",
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=[search_tool]  # Only web search is needed for broader context or definitions
    )

    # Define the tasks, now using the in-memory context
    task_executive_narrative = Task(
        description=f"""Using the provided synthesis report, create an executive-level narrative suitable for a leadership meeting.
        The report should be structured as:
        - Executive Summary (1-2 paragraphs)
        - Three strategic sections (e.g., Performance Highlights, Key Risks, Strategic Opportunities)
        - A final, actionable takeaway message.

        **Full Synthesis Report to Analyze:**
        ---
        {synthesis_context}
        ---
        """,
        expected_output="""A polished, executive-ready summary document including:
        - 1-2 compelling overview paragraphs.
        - 3 concise thematic sections that tell a clear story.
        - 1 closing paragraph with a strong call to action or recommendation.""",
        agent=communications_agent
    )

    task_communication_deliverables = Task(
        description="""Convert the executive narrative from the previous step into three distinct communication deliverables:
        1. A 3-paragraph summary email for the executive team.
        2. A concise 5-7 slide outline for a presentation (bullet points for each slide).
        3. A short (approx. 2-minute) script draft for an executive to present the key findings.""",
        expected_output="""Three separate, well-formatted deliverables:
        - The complete text for the executive email.
        - A slide-by-slide outline for a presentation.
        - A polished script summary for a presenter.""",
        agent=communications_agent,
        context=[task_executive_narrative]
    )

    # Assemble the crew
    communication_crew = Crew(
        agents=[communications_agent],
        tasks=[
            task_executive_narrative,
            task_communication_deliverables
        ],
        verbose=True,
        process="sequential"
    )

    return communication_crew

# Note: The 'if __name__ == "__main__":' block has been removed.
# This script should be executed via Orchestrator.py.
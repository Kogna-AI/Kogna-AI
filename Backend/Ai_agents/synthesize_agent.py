from crewai import Agent, Task, Crew, LLM, Process
from crewai_tools import FileReadTool, DirectoryReadTool, SerperDevTool
import os
from dotenv import load_dotenv

load_dotenv()

#
# This is the refactored script for the Synthesizer Agent.
# It is designed to be imported and used by the main Orchestrator.py script.
#

# --- Crew Creation Function ---

def create_synthesis_crew(sql_analysis_report: str, business_research_findings: str):
    """
    Creates and configures the Strategic Synthesis Crew.

    Args:
        sql_analysis_report (str): The report from the Data Analyst crew.
        business_research_findings (str): The report from the Research Agent crew.

    Returns:
        Crew: The configured Synthesis Crew object.
    """
    # Configure the LLM for this agent
    llm = LLM(
        model="claude/sonnet-4.5",
        temperature=0.6,
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )
    
    # Initialize tools (optional, but can be useful for cross-referencing)
    search_tool = SerperDevTool(api_key=os.getenv("SERPER_API_KEY"))

    # Define the Synthesizer Agent
    synthesizer_agent = Agent(
        role="Senior Strategic Synthesis Analyst",
        goal="Integrate quantitative analysis and qualitative business intelligence to produce a single, coherent executive summary with actionable insights.",
        backstory="""You are a master strategist, an expert at connecting dots that others miss.
        You take detailed quantitative reports from data analysts and qualitative findings from
        business researchers to weave a single, compelling narrative about the company's
        performance, risks, and opportunities.""",
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=[search_tool]
    )

    # Define a single, comprehensive synthesis task
    synthesis_task = Task(
        description=f"""Synthesize the following two reports into a single, unified executive summary.
        Your goal is to identify cross-functional themes, contradictions, and strategic implications.

        **Report 1: Quantitative Data Analysis Report**
        ---
        {sql_analysis_report}
        ---

        **Report 2: Qualitative Business Research Findings**
        ---
        {business_research_findings}
        ---

        **Your analysis must:**
        1.  Identify the top 3-5 cross-functional themes that appear in both reports.
        2.  Highlight any contradictions or data gaps between the quantitative analysis and the qualitative research.
        3.  Formulate a final executive summary that includes strategic highlights, critical risks, and actionable recommendations for the next quarter.""",
        expected_output="""A comprehensive executive summary document that includes:
        - An overview of the top 3-5 strategic themes, supported by evidence from both reports.
        - A section on identified data gaps or conflicting information.
        - A final summary with 3 strategic highlights, 3 critical risks, and 3 actionable recommendations.""",
        agent=synthesizer_agent
    )
    
    # Assemble and return the crew
    synthesis_crew = Crew(
        agents=[synthesizer_agent],
        tasks=[synthesis_task],
        process=Process.sequential,
        verbose=True
    )
    
    return synthesis_crew

# Note: The 'if __name__ == "__main__":' block has been removed.
# This script should be executed via Orchestrator.py.

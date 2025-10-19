from crewai import Agent, Task, Crew, Process
from crewai_tools import SerpApiGoogleSearchTool
from langchain_litellm import ChatLiteLLM
from datetime import datetime
from typing import List, Optional

def create_synthesis_crew(
    internal_analysis_report: str,
    internal_sources: Optional[List[str]],
    business_research_findings: str,
    google_api_key: str,
    serper_api_key: str,
    human_feedback: str = None  # Corrected: Added a comma before this argument
) -> Crew:
    """
    Creates and configures the Strategic Synthesis Crew.
    This crew can now receive feedback to revise its analysis.
    """
    current_time = datetime.now().strftime("%I:%M %p %Z on %A, %B %d, %Y")
    current_date = datetime.now().strftime("%Y-%m-%d")

    llm = ChatLiteLLM(
        model="gemini/gemini-2.0-flash",
        temperature=0.6,
        api_key=google_api_key
    )
    
    search_tool = SerpApiGoogleSearchTool(api_key=serper_api_key)

    synthesizer_agent = Agent(
        role="Senior Strategic Synthesis Analyst",
        goal="Integrate quantitative analysis and qualitative business intelligence to produce a single, coherent executive summary with actionable insights.",
        backstory=(
            "You are a master strategist, an expert at connecting dots that others miss. "
            "You take detailed quantitative reports from data analysts and qualitative findings from "
            "business researchers to weave a single, compelling narrative about the company's "
            "performance, risks, and opportunities. You are capable of revising your work based on feedback."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=[search_tool]
    )

    # --- Dynamic Task Description ---
    sources_text = "Not specified."
    if internal_sources:
        sources_text = ", ".join(internal_sources)

    task_description = f"""Synthesize the following two reports into a single, unified executive summary for the current business context of {current_date}.
    Your goal is to identify cross-functional themes, contradictions, and strategic implications.

    **Report 1: Internal Document Analysis Report (Received at {current_time})(Sourced from: {sources_text})**
    (This report is based on scanning all internal unstructured files like emails, meetings, etc.)
    ---
    {internal_analysis_report} 
    ---

    **Report 2: External Business Research Findings (Received at {current_time})**
    (This report is based on external Google searches)
    ---
    {business_research_findings}
    ---

    **Your analysis must:**
    1.  Identify the top 3-5 cross-functional themes that appear in both reports.
    2.  Highlight any contradictions or data gaps. (e.g., "Internal data from {sources_text} says X, but web search says Y").
    3.  Formulate a final executive summary that includes strategic highlights, critical risks, and actionable recommendations for the next quarter."""
    # If human feedback is provided, append it as a critical instruction.
    if human_feedback:
        task_description += (
            f"\n\n**IMPORTANT REVISION INSTRUCTION:** A previous version of your summary was rejected by a human. "
            f"You MUST revise your analysis to incorporate the following feedback:\n"
            f"--- FEEDBACK ---\n{human_feedback}\n--- END FEEDBACK ---"
        )

    synthesis_task = Task(
        description=task_description, # Use the dynamically generated description
        expected_output="""A comprehensive executive summary document that includes:
        - An overview of the top 3-5 strategic themes.
        - A section on identified data gaps or conflicting information.
        - A final summary with 3 strategic highlights, 3 critical risks, and 3 actionable recommendations.""",
        agent=synthesizer_agent
    )
    
    return Crew(
        agents=[synthesizer_agent],
        tasks=[synthesis_task],
        process=Process.sequential,
        verbose=True
    )
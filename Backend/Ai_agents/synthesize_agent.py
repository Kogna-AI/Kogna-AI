from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool
# POLISH: Switched from Anthropic to the LiteLLM wrapper for Google
from langchain_litellm import ChatLiteLLM
from datetime import datetime

def create_synthesis_crew(
    sql_analysis_report: str,
    business_research_findings: str,
    # POLISH: Changed the API key argument to be consistent
    google_api_key: str,
    serper_api_key: str
) -> Crew:
    """
    Creates and configures the Strategic Synthesis Crew.
    """
    current_time = datetime.now().strftime("%I:%M %p %Z on %A, %B %d, %Y")
    current_date = datetime.now().strftime("%Y-%m-%d")

<<<<<<< HEAD
'''
edge case:
no api key found
'''

# switched to Gemini due to limitation of Anthropic


if not os.getenv("GEMINI_API_KEY"):
    raise ValueError("GEMINI_API_KEY not found in .env file.")
=======
    # POLISH: Configured the agent to use the Google Gemini model
    llm = ChatLiteLLM(
        model="gemini/gemini-2.0-flash",
        temperature=0.6,
        api_key=google_api_key
    )
    
    search_tool = SerperDevTool(api_key=serper_api_key)
>>>>>>> orch

    synthesizer_agent = Agent(
        role="Senior Strategic Synthesis Analyst",
        goal="Integrate quantitative analysis and qualitative business intelligence to produce a single, coherent executive summary with actionable insights.",
        backstory=(
            "You are a master strategist, an expert at connecting dots that others miss. "
            "You take detailed quantitative reports from data analysts and qualitative findings from "
            "business researchers to weave a single, compelling narrative about the company's "
            "performance, risks, and opportunities."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=[search_tool]
    )

    synthesis_task = Task(
        description=f"""Synthesize the following two reports into a single, unified executive summary.
        Your goal is to identify cross-functional themes, contradictions, and strategic implications.

        **Report 1: Quantitative Data Analysis Report (Received at {current_time})**
        ---
        {sql_analysis_report}
        ---

<<<<<<< HEAD
llm = LLM(
    model="gemini/gemini-2.0-flash",
    temperature=0.6,
    api_key=os.getenv("GEMINI_API_KEY")
)
=======
        **Report 2: Qualitative Business Research Findings (Received at {current_time})**
        ---
        {business_research_findings}
        ---
>>>>>>> orch

        **Your analysis for the current business context of {current_date} must:**
        1.  Identify the top 3-5 cross-functional themes that appear in both reports.
        2.  Highlight any contradictions or data gaps. If you identify a critical data gap, briefly use the search tool to find external context that might help explain it.
        3.  Formulate a final executive summary that includes strategic highlights, critical risks, and actionable recommendations for the next quarter.""",
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
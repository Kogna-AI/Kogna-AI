from crewai import Agent, Task, Crew, LLM
from crewai_tools import FileReadTool, DirectoryReadTool, SerperDevTool
import os
from flask.cli import load_dotenv

load_dotenv()

'''
edge case:
no api key found
'''
if not os.getenv("ANTHROPIC_API_KEY"):
    raise ValueError("ANTHROPIC_API_KEY not found in .env file.")

if not os.getenv("SERPER_API_KEY"):
    raise ValueError("SERPER_API_KEY not found in .env file.")

# model -- claude/opus-4.1

llm = LLM(
    model="claude/opus-4.1",
    temperature=0.5,
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

#initialize built-in tools:
'''
FileReadTool - to read text files other agents generated
DirectoryReadTool - to read text files in a the work dir
SerperDevTool - to search the web
'''
file_tool = FileReadTool()
directory_tool = DirectoryReadTool()
search_tool = SerperDevTool(api_key=os.getenv("SERPER_API_KEY"))

# setup Communication Agent
communications_agent = Agent(
    role="Executive Communications Strategist",
    goal="Translate complex analyses and strategic advice into clear, concise, and executive-ready language.",
    backstory="""You are the Communications Agent, an expert in transforming complex analytical reports
    into compelling narratives that executives can easily understand and act on.
    You focus on clarity, brevity, and strategic tone suitable for board meetings, investor updates, or QBRs.""",
    verbose=True,
    allow_delegation=False,
    llm=llm,
    tools=[file_tool, directory_tool, search_tool]  # web search optional but useful for context
)

# setup tasks
#TODO: adjust the file other agents generated
task_summary_findings = Task(
    description="""Review prior agents' outputs:
    - research_output.txt
    - synthesis_output.txt
    Summarize their main findings and key insights.
    Focus on high-level implications and omit technical details.""",
    expected_output="""A concise synthesis summary with:
    - 5 key insights
    - Supporting context in plain language
    - One-sentence implication per insight""",
    agent=communications_agent
)

task_executive_narrative = Task(
    description="""Using the summarized insights, create an executive-level narrative suitable for a leadership meeting.
    It should be structured as:
    - Executive Summary paragraph
    - Three strategic sections (Performance, Risks, Opportunities)
    - Final takeaway message.""",
    expected_output="""Executive summary document including:
    - 1 overview paragraph
    - 3 concise thematic sections
    - 1 closing recommendation paragraph""",
    agent=communications_agent,
    context=[task_summary_findings]
)

task_communication_deliverables = Task(
    description="""Convert the executive narrative into three communication deliverables:
    1. A 3-paragraph email for executives
    2. A slide outline for presentation
    3. A short script draft for an executive presenter.""",
    expected_output="""Three deliverables:
    - Executive email draft
    - Slide outline (5–7 slides)
    - 2-minute script summary""",
    agent=communications_agent,
    context=[task_executive_narrative]
)

#crew setup

crew = Crew(
    agents=[communications_agent],
    tasks=[
        task_summary_findings,
        task_executive_narrative,
        task_communication_deliverables
    ],
    verbose=True,
    process="sequential"
)

#run

if __name__ == "__main__":
    print("Starting Communications Agent Crew...")
    print("=" * 60)

    result = crew.kickoff()

    print("\n" + "=" * 60)
    print("COMMUNICATIONS AGENT FINAL REPORT")
    print("=" * 60)
    print(result)

    with open("communications_output.txt", "w") as f:
        f.write(str(result))

    print("\nReport saved to communications_output.txt")

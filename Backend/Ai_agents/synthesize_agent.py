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


#config LLM

llm = LLM(
    model="claude/sonnet-4.5",
    temperature=0.6,
    api_key=os.getenv("ANTHROPIC_API_KEY")  # set ANTHROPIC_API_KEY or other provider if further decision made
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

# setup Synthesizer Agent

synthesizer_agent = Agent(
    role="Strategic Synthesis Analyst",
    goal="Integrate findings from all agents to identify strategic patterns, risks, and opportunities.",
    backstory="""You are the Synthesizer Agent, an expert at connecting dots across multiple analyses.
    You combine research, analytics, and operational insights into coherent, executive-ready intelligence.
    You excel at identifying hidden risks, emergent opportunities, and strategic implications.""",
    verbose=True,
    allow_delegation=False,
    llm=llm,
    tools=[file_tool, directory_tool, search_tool]
)

#set up the task 
#TODO: adjust the file other agents generated
task_integrate_findings = Task( 
    description="""Review and consolidate findings from prior agents.
    Look into: 
    - research_output.txt
    - analysis_output.txt
    - kpi_output.txt
    - churn_output.txt
    Identify recurring topics, cross-departmental insights, and conflicting conclusions.""",
    expected_output="""A unified synthesis of insights with:
    - Top 5 cross-functional themes
    - Key supporting evidence (with file references)
    - Contradictions or data gaps""",
    agent=synthesizer_agent
)

task_pattern_risk_analysis = Task(
    description="""From the synthesized insights, identify strategic patterns, risks, and emerging opportunities.
    Pay attention to:
    - Market trends (use web search if needed)
    - Operational bottlenecks
    - Growth signals or innovation opportunities""",
    expected_output="""A structured list of:
    - Strategic patterns
    - Emerging risks
    - Market or internal opportunities
    - Recommended areas for deeper exploration""",
    agent=synthesizer_agent
)

task_executive_summary = Task(
    description="""Compile an executive-level summary based on all findings.
    Present insights as:
    - Key takeaways
    - Strategic implications
    - Next quarter priorities""",
    expected_output="""Executive summary including:
    - 3 strategic highlights
    - 3 critical risks
    - 3 actionable recommendations
    - Concise conclusion for executive review""",
    agent=synthesizer_agent,
    context=[task_integrate_findings, task_pattern_risk_analysis]
)

# crew setup 

crew = Crew(
    agents=[synthesizer_agent],
    tasks=[
        task_integrate_findings,
        task_pattern_risk_analysis,
        task_executive_summary
    ],
    verbose=True,
    process="sequential"
)

#run 

if __name__ == "__main__":
    print("Starting Synthesizer Agent Crew...")
    print("=" * 60)

    result = crew.kickoff()

    print("\n" + "=" * 60)
    print("SYNTHESIZER AGENT FINAL REPORT")
    print("=" * 60)
    print(result)

    with open("synthesis_output.txt", "w") as f:
        f.write(str(result))

    print("\nReport saved to synthesis_output.txt")

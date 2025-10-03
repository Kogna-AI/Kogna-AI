from crewai import Agent, Task, Crew, LLM
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("SERPAPI_API_KEY")

#add LLM model

llm = LLM(
    model="gemini/gemini-2.0-flash-exp",  # or your preferred model
    temperature=0.7,
    api_key=os.getenv("GOOGLE_API_KEY")
)

# Create a custom research agent
agent = Agent(
    role='Research Analyst',
    goal='Conduct thorough research and analysis on business metrics, risks, and performance indicators',
    backstory="""You are an experienced business research analyst with expertise in 
    financial analysis, risk assessment, and performance evaluation. You excel at 
    gathering information from various sources, identifying patterns, and providing 
    actionable insights for executive decision-making.""",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

#Task 1: Find and summarize top product risks from Q3 reports

q3_task = Task(
    description="Find and summarize the top product risks identified in the Q3 company reports.",
    expected_output="A bullet-point summary of the risks with sources if available.",
    agent=agent
)

#Task 2: Find and summarize KOPs for each department

kop_task = Task(
    description="Retrieve and summarize the most recent KPIs for each department (Engineering, Sales, Marketing, Customer Success). Include top achievements, bottlenecks, and red flags.",
    expected_output="A short executive-level summary per department with KPIs, risks, and key highlights.",
    agent=agent
)


#Task 3: Find and summarize at-risk projects

risk_task = Task(
    description="Identify projects that are behind schedule or at risk of delay based on recent updates in Jira, Asana, or project trackers. Summarize the causes and suggested mitigation strategies.",
    expected_output="A list of 3–5 at-risk projects with: project name, delay cause, impacted teams, and recommendations.",
    agent=agent
)

#Task 4: Investigate revenue forecast deviations

return_forecast_task = Task(
    description="Investigate deviations from revenue forecast in the last quarter using finance reports, CRM deal statuses, and sales team updates.",
    expected_output="3–4 concrete reasons revenue was over/under forecast, with references to internal documents or data.",
    agent=agent
)

#Task 5: Prepare and get Quarterly Business Review (QBR) summary

qbr_task = Task(
    description="Aggregate key highlights, metrics, and milestones from the last 90 days to help prepare the company’s QBR.",
    expected_output="QBR-ready summary covering performance, challenges, customer wins, and financials.",
    agent=agent
)

#Task 6: Analyze customer churn signals

churn_task = Task(
    description="Analyze recent support tickets, NPS survey responses, and CRM notes to uncover trends in customer churn or dissatisfaction. Highlight root causes.",
    expected_output="Top 3 churn signals or pain points with supporting examples from internal data.",
    agent=agent
)




# Create a Crew to run the task
crew = Crew(
    agents=[agent],
    tasks=[q3_task, kop_task, risk_task, return_forecast_task, qbr_task, churn_task],
    verbose=True
)

result = crew.kickoff()

print("\nHere is the final result from Research Agent:\n")
print(result)
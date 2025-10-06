from crewai import Agent, Task, Crew, LLM
from crewai.tools import tool
from crewai_tools import SerperDevTool, FileReadTool, DirectoryReadTool, ScrapeWebsiteTool
import os
from flask.cli import load_dotenv
import requests  

load_dotenv()


#create custom tools
@tool("Jira Search")
def search_jira(query: str) -> str:
    """Search Jira for project information, issues, and status updates.
    Use this to find at-risk projects, delayed tasks, or project status."""
    try:
        # Example Jira API integration
        jira_url = os.getenv("JIRA_URL")  # e.g., "https://yourcompany.atlassian.net"
        jira_email = os.getenv("JIRA_EMAIL")
        jira_api_token = os.getenv("JIRA_API_TOKEN")
        
        if not all([jira_url, jira_email, jira_api_token]):
            return "Jira credentials not configured. Please set JIRA_URL, JIRA_EMAIL, and JIRA_API_TOKEN in .env file."
        
        # JQL (Jira Query Language) search
        search_url = f"{jira_url}/rest/api/3/search"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        auth = (jira_email, jira_api_token)
        
        # Build JQL based on query
        jql = query  # You can enhance this to parse natural language to JQL
        
        params = {
            "jql": jql,
            "maxResults": 50,
            "fields": "summary,status,assignee,duedate,priority,project"
        }
        
        response = requests.get(search_url, headers=headers, auth=auth, params=params)
        
        if response.status_code == 200:
            data = response.json()
            issues = data.get('issues', [])
            
            if not issues:
                return f"No Jira issues found for query: {query}"
            
            # Format results
            results = []
            for issue in issues:
                key = issue['key']
                fields = issue['fields']
                results.append(f"- {key}: {fields['summary']} (Status: {fields['status']['name']}, Priority: {fields.get('priority', {}).get('name', 'N/A')})")
            
            return f"Found {len(issues)} Jira issues:\n" + "\n".join(results)
        else:
            return f"Jira API error: {response.status_code} - {response.text}"
            
    except Exception as e:
        return f"Error searching Jira: {str(e)}"


@tool("CRM Query")
def query_crm(parameters: str) -> str:
    """Query CRM (Salesforce, HubSpot, etc.) for customer data, deals, and revenue information.
    Parameters should describe what data you need (e.g., 'Q3 closed deals', 'at-risk accounts')."""
    try:
        # Example for Salesforce (you can adapt for HubSpot, Pipedrive, etc.)
        sf_instance_url = os.getenv("SALESFORCE_INSTANCE_URL")
        sf_access_token = os.getenv("SALESFORCE_ACCESS_TOKEN")
        
        if not all([sf_instance_url, sf_access_token]):
            return "CRM credentials not configured. Please set SALESFORCE_INSTANCE_URL and SALESFORCE_ACCESS_TOKEN in .env file."
        
        # Example SOQL query (Salesforce Object Query Language)
        # You would parse 'parameters' to build appropriate queries
        query_url = f"{sf_instance_url}/services/data/v58.0/query"
        headers = {
            "Authorization": f"Bearer {sf_access_token}",
            "Content-Type": "application/json"
        }
        
        # Simple example query - you'd make this dynamic based on parameters
        soql = "SELECT Id, Name, Amount, StageName, CloseDate FROM Opportunity WHERE CloseDate = THIS_QUARTER ORDER BY Amount DESC LIMIT 20"
        
        response = requests.get(query_url, headers=headers, params={"q": soql})
        
        if response.status_code == 200:
            data = response.json()
            records = data.get('records', [])
            
            if not records:
                return f"No CRM records found for: {parameters}"
            
            # Format results
            results = []
            for record in records:
                results.append(f"- {record['Name']}: ${record['Amount']:,.0f} ({record['StageName']}) - Close: {record['CloseDate']}")
            
            return f"Found {len(records)} CRM opportunities:\n" + "\n".join(results)
        else:
            return f"CRM API error: {response.status_code} - {response.text}"
            
    except Exception as e:
        return f"Error querying CRM: {str(e)}"


@tool("Confluence Search")
def search_confluence(query: str) -> str:
    """Search Confluence for documentation, reports, and company knowledge.
    Use this to find Q3 reports, KPI dashboards, or project documentation."""
    try:
        confluence_url = os.getenv("CONFLUENCE_URL")
        confluence_email = os.getenv("CONFLUENCE_EMAIL")
        confluence_api_token = os.getenv("CONFLUENCE_API_TOKEN")
        
        if not all([confluence_url, confluence_email, confluence_api_token]):
            return "Confluence credentials not configured."
        
        search_url = f"{confluence_url}/rest/api/content/search"
        headers = {"Accept": "application/json"}
        auth = (confluence_email, confluence_api_token)
        
        params = {
            "cql": f"text ~ \"{query}\"",
            "limit": 10
        }
        
        response = requests.get(search_url, headers=headers, auth=auth, params=params)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            
            if not results:
                return f"No Confluence pages found for: {query}"
            
            output = []
            for result in results:
                title = result['title']
                page_url = f"{confluence_url}{result['_links']['webui']}"
                output.append(f"- {title}\n  URL: {page_url}")
            
            return f"Found {len(results)} Confluence pages:\n" + "\n".join(output)
        else:
            return f"Confluence API error: {response.status_code}"
            
    except Exception as e:
        return f"Error searching Confluence: {str(e)}"



#add LLM config

llm = LLM(
    model="gemini/gemini-2.0-flash",
    temperature=0.1,
    api_key=os.getenv("GOOGLE_API_KEY")
)


#initialize built-in tools

search_tool = SerperDevTool(api_key=os.getenv("SERPER_API_KEY"))
file_tool = FileReadTool()
directory_tool = DirectoryReadTool()
scrape_tool = ScrapeWebsiteTool()


#create research agent with tools

research_agent = Agent(
    role='Senior Business Research Analyst',
    goal='Conduct thorough research using company data sources and external information',
    backstory="""You are an experienced business research analyst with expertise in 
    financial analysis, risk assessment, and performance evaluation. You have access to 
    company systems like Jira, CRM, and Confluence, as well as web search capabilities.""",
    verbose=True,
    allow_delegation=False,
    llm=llm,
    tools=[
        # Custom tools
        search_jira,
        query_crm,
        search_confluence,
        # Built-in tools
        search_tool,
        file_tool,
        directory_tool,
        scrape_tool
    ]
)


#create tasks for the agent
task_q3_risks = Task(
    description="""Find Q3 company risk reports by:
    1. Using Confluence Search tool to find "Q3 risks" or "Q3 report"
    2. Using File Read tool to check ./reports/Q3 directory
    3. If nothing found, use web search for public company reports
    
    Summarize top 5 product/business risks with sources.""",
    expected_output="""Risk summary with:
    - Risk name and severity
    - Source document
    - Mitigation status""",
    agent=research_agent
)

task_kpis = Task(
    description="""Retrieve department KPIs using:
    1. Confluence Search for "KPI dashboard" or "department metrics"
    2. File Read tool for ./reports/KPIs directory
    3. Jira Search for project velocity and completion rates (Engineering)
    4. CRM Query for sales metrics and pipeline health
    
    Summarize for: Engineering, Sales, Marketing, Customer Success.""",
    expected_output="""Per-department summary with:
    - Key metrics and trends
    - Top 3 achievements
    - Bottlenecks and red flags""",
    agent=research_agent
)

task_at_risk_projects = Task(
    description="""Use Jira Search tool with query: 'status != Done AND duedate < now() ORDER BY priority DESC'
    to find delayed projects. For each project, determine:
    - Current status vs planned
    - Blockers and dependencies
    - Team impact""",
    expected_output="""List of 3-5 at-risk projects with:
    - Project key and name
    - Delay details
    - Root causes
    - Mitigation recommendations""",
    agent=research_agent
)

task_revenue_analysis = Task(
    description="""Analyze revenue using:
    1. CRM Query for "Q3 closed deals" and "pipeline forecast"
    2. File Read for ./finance directory
    3. Compare actual vs forecast
    
    Identify variance drivers.""",
    expected_output="""Revenue analysis with:
    - Actual vs forecast
    - 3-4 specific variance reasons
    - Supporting data""",
    agent=research_agent
)

task_churn_analysis = Task(
    description="""Analyze churn signals using:
    1. CRM Query for "at-risk accounts" or "low health score customers"
    2. File Read for ./support/tickets directory
    3. Look for patterns in complaints and engagement decline""",
    expected_output="""Churn analysis with:
    - Top 3 risk factors
    - Supporting examples
    - Recommended actions""",
    agent=research_agent
)

task_qbr_prep = Task(
    description="""Compile comprehensive QBR using insights from all previous tasks.
    Create executive summary covering performance, challenges, and priorities.""",
    expected_output="""QBR summary with:
    - Executive summary
    - Key metrics dashboard
    - Wins & challenges
    - Forward priorities""",
    agent=research_agent,
    context=[task_q3_risks, task_kpis, task_at_risk_projects, task_revenue_analysis, task_churn_analysis]
)


#create and run crew

crew = Crew(
    agents=[research_agent],
    tasks=[
        task_q3_risks,
        task_kpis,
        task_at_risk_projects,
        task_revenue_analysis,
        task_churn_analysis,
        task_qbr_prep
    ],
    verbose=True,
    process="sequential"
)

if __name__ == "__main__":
    print("Starting Research Agent Crew...")
    print("="*60)
    
    result = crew.kickoff()
    
    print("\n" + "="*60)
    print("RESEARCH AGENT FINAL REPORT")
    print("="*60)
    print(result)
    
    # Save output
    with open("research_output.txt", "w") as f:
        f.write(str(result))
    
    print("\nReport saved to research_output.txt")



# from crewai import Agent, Task, Crew, LLM
# from dotenv import load_dotenv
# import os

# load_dotenv()
# api_key = os.getenv("SERPAPI_API_KEY")

# #add LLM model

# llm = LLM(
#     model="gemini/gemini-2.0-flash",  # or your preferred model
#     temperature=0.7,
#     api_key=os.getenv("GOOGLE_API_KEY")
# )

# # Create a custom research agent
# agent = Agent(
#     role='Research Analyst',
#     goal='Conduct thorough research and analysis on business metrics, risks, and performance indicators',
#     backstory="""You are an experienced business research analyst with expertise in 
#     financial analysis, risk assessment, and performance evaluation. You excel at 
#     gathering information from various sources, identifying patterns, and providing 
#     actionable insights for executive decision-making.""",
#     verbose=True,
#     allow_delegation=False,
#     llm=llm
# )

# #Task 1: Find and summarize top product risks from Q3 reports

# q3_task = Task(
#     description="Find and summarize the top product risks identified in the Q3 company reports.",
#     expected_output="A bullet-point summary of the risks with sources if available.",
#     agent=agent
# )

# #Task 2: Find and summarize KOPs for each department

# kop_task = Task(
#     description="Retrieve and summarize the most recent KPIs for each department (Engineering, Sales, Marketing, Customer Success). Include top achievements, bottlenecks, and red flags.",
#     expected_output="A short executive-level summary per department with KPIs, risks, and key highlights.",
#     agent=agent
# )


# #Task 3: Find and summarize at-risk projects

# risk_task = Task(
#     description="Identify projects that are behind schedule or at risk of delay based on recent updates in Jira, Asana, or project trackers. Summarize the causes and suggested mitigation strategies.",
#     expected_output="A list of 3–5 at-risk projects with: project name, delay cause, impacted teams, and recommendations.",
#     agent=agent
# )

# #Task 4: Investigate revenue forecast deviations

# return_forecast_task = Task(
#     description="Investigate deviations from revenue forecast in the last quarter using finance reports, CRM deal statuses, and sales team updates.",
#     expected_output="3–4 concrete reasons revenue was over/under forecast, with references to internal documents or data.",
#     agent=agent
# )

# #Task 5: Prepare and get Quarterly Business Review (QBR) summary

# qbr_task = Task(
#     description="Aggregate key highlights, metrics, and milestones from the last 90 days to help prepare the company’s QBR.",
#     expected_output="QBR-ready summary covering performance, challenges, customer wins, and financials.",
#     agent=agent
# )

# #Task 6: Analyze customer churn signals

# churn_task = Task(
#     description="Analyze recent support tickets, NPS survey responses, and CRM notes to uncover trends in customer churn or dissatisfaction. Highlight root causes.",
#     expected_output="Top 3 churn signals or pain points with supporting examples from internal data.",
#     agent=agent
# )




# # Create a Crew to run the task
# crew = Crew(
#     agents=[agent],
#     tasks=[q3_task, kop_task, risk_task, return_forecast_task, qbr_task, churn_task],
#     verbose=True
# )

# result = crew.kickoff()

# print("\nHere is the final result from Research Agent:\n")
# print(result)






















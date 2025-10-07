from crewai import Agent, Task, Crew, LLM
from crewai.tools import tool
from crewai_tools import  SerperDevTool, FileReadTool, DirectoryReadTool, ScrapeWebsiteTool
import os
from dotenv import load_dotenv
import requests  

load_dotenv()

#
# This is the refactored script for the Research Agent.
# It is designed to be imported and used by the main Orchestrator.py script.
#

# --- Custom Tools Definition ---

@tool("Jira Search")
def search_jira(query: str) -> str:
    """Search Jira for project information, issues, and status updates using a JQL query."""
    try:
        jira_url = os.getenv("JIRA_URL")
        jira_email = os.getenv("JIRA_EMAIL")
        jira_api_token = os.getenv("JIRA_API_TOKEN")
        
        if not all([jira_url, jira_email, jira_api_token]):
            return "Jira credentials not configured in .env file."
        
        search_url = f"{jira_url}/rest/api/3/search"
        headers = {"Accept": "application/json"}
        auth = (jira_email, jira_api_token)
        params = {"jql": query, "maxResults": 50, "fields": "summary,status,priority,project"}
        
        response = requests.get(search_url, headers=headers, auth=auth, params=params)
        response.raise_for_status() # Raise an exception for bad status codes
        
        data = response.json()
        issues = data.get('issues', [])
        if not issues:
            return f"No Jira issues found for query: {query}"
        
        results = [f"- {i['key']}: {i['fields']['summary']} (Status: {i['fields']['status']['name']})" for i in issues]
        return f"Found {len(issues)} Jira issues:\n" + "\n".join(results)
            
    except Exception as e:
        return f"Error searching Jira: {str(e)}"

@tool("CRM Query")
def query_crm(parameters: str) -> str:
    """Query CRM for customer data, deals, and revenue info."""
    try:
        sf_instance_url = os.getenv("SALESFORCE_INSTANCE_URL")
        sf_access_token = os.getenv("SALESFORCE_ACCESS_TOKEN")
        
        if not all([sf_instance_url, sf_access_token]):
            return "CRM credentials not configured in .env file."
        
        query_url = f"{sf_instance_url}/services/data/v58.0/query"
        headers = {"Authorization": f"Bearer {sf_access_token}"}
        # A more dynamic query based on a simplified input
        soql = f"SELECT Name, Amount, StageName, CloseDate FROM Opportunity WHERE {parameters} LIMIT 20"
        
        response = requests.get(query_url, headers=headers, params={"q": soql})
        response.raise_for_status()
        
        data = response.json()
        records = data.get('records', [])
        if not records:
            return f"No CRM records found for: {parameters}"
        
        results = [f"- {r['Name']}: ${r.get('Amount', 0):,.0f} ({r['StageName']})" for r in records]
        return f"Found {len(records)} CRM opportunities:\n" + "\n".join(results)
            
    except Exception as e:
        return f"Error querying CRM: {str(e)}"

@tool("Confluence Search")
def search_confluence(query: str) -> str:
    """Search Confluence for documentation, reports, and company knowledge."""
    try:
        confluence_url = os.getenv("CONFLUENCE_URL")
        confluence_email = os.getenv("CONFLUENCE_EMAIL")
        confluence_api_token = os.getenv("CONFLUENCE_API_TOKEN")
        
        if not all([confluence_url, confluence_email, confluence_api_token]):
            return "Confluence credentials not configured."
        
        search_url = f"{confluence_url}/rest/api/content/search"
        auth = (confluence_email, confluence_api_token)
        params = {"cql": f'text ~ "{query}"', "limit": 10}
        
        response = requests.get(search_url, auth=auth, params=params)
        response.raise_for_status()
        
        data = response.json()
        results = data.get('results', [])
        if not results:
            return f"No Confluence pages found for: {query}"
        
        output = [f"- {r['title']}\n  URL: {confluence_url}{r['_links']['webui']}" for r in results]
        return f"Found {len(results)} Confluence pages:\n" + "\n".join(output)
            
    except Exception as e:
        return f"Error searching Confluence: {str(e)}"

# --- Crew Creation Function ---

def create_research_crew():
    """
    Creates and configures the Business Research Crew.

    Returns:
        Crew: The configured Research Crew object.
    """
    # Configure the LLM
    llm = LLM(
        model="gemini/gemini-2.0-flash",
        temperature=0.7,
        api_key=os.getenv("GOOGLE_API_KEY")
    )

    # Initialize built-in tools
    search_tool = SerperDevTool(api_key=os.getenv("SERPER_API_KEY"))

    # Create the Research Agent
    research_agent = Agent(
        role='Senior Business Research Analyst',
        goal='Conduct thorough research using company data sources and external information to compile a comprehensive business intelligence report',
        backstory="""You are an expert business research analyst. You have access to internal
        company systems like Jira, CRM, and Confluence, as well as web search capabilities.
        You methodically use these tools to answer complex business questions.""",
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=[search_jira, query_crm, search_confluence, search_tool]
    )

    # Create a single, comprehensive research task
    comprehensive_research_task = Task(
        description="""Compile a comprehensive business intelligence report for the last quarter.
        You must use your available tools to gather information on the following topics:
        1.  **Top Business Risks:** Use the Confluence Search tool to find "Q3 risks" or "quarterly risk report".
        2.  **At-Risk Projects:** Use the Jira Search tool with the JQL query 'status != Done AND duedate < now() ORDER BY priority DESC' to find delayed projects.
        3.  **Revenue & Sales Pipeline:** Use the CRM Query tool to analyze revenue. Use a query like 'CloseDate = THIS_QUARTER ORDER BY Amount DESC'.
        4.  **Customer Churn Signals:** Use the CRM Query tool to look for at-risk accounts. Use a query like 'Health_Score__c < 50'.
        5.  **Synthesize Findings:** Once all data is gathered, compile a unified report that summarizes the key findings from each area into a QBR-ready summary. Include sections for Performance, Challenges, and strategic priorities.""",
        expected_output="""A single, consolidated business intelligence report with distinct sections:
        - A summary of the top 3-5 business risks from Confluence.
        - A list of at-risk projects from Jira, including their status.
        - A summary of revenue performance and pipeline health from the CRM.
        - An analysis of potential customer churn signals from the CRM.
        - A final executive summary that synthesizes all points for a Quarterly Business Review (QBR).""",
        agent=research_agent
    )

    # Create and return the Crew
    research_crew = Crew(
        agents=[research_agent],
        tasks=[comprehensive_research_task],
        verbose=True,
        process="sequential"
    )
    
    return research_crew

# Note: The 'if __name__ == "__main__":' block and old code have been removed.
# This script should be executed via Orchestrator.py.

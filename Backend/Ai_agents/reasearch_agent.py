# research_crew.py

from crewai import Agent, Task, Crew
from crewai.tools import tool
from crewai_tools import SerpApiGoogleSearchTool
import requests
from langchain_community.chat_models import ChatLiteLLM
from supabase_connect import get_supabase_manager
from dotenv import load_dotenv

load_dotenv()

#connect to supabase
supabase_manager = get_supabase_manager()
supabase = supabase_manager.client

#
# This is the refactored script for the Research Agent.
# It is designed to be imported and used by the main Orchestrator.py script.
#

def create_research_crew(
    google_api_key: str,
    serper_api_key: str,
    # jira_creds: dict,
    # crm_creds: dict,
    # confluence_creds: dict
) -> Crew:
    """
    Creates and configures the Business Research Crew.

    This function is now fully self-contained and receives all necessary credentials
    and API keys as arguments, making it modular and secure.

    Args:
        google_api_key (str): API key for the Google Gemini model.
        serper_api_key (str): API key for the Serper search tool.
        jira_creds (dict): Dictionary with 'url', 'email', and 'api_token' for Jira.
        crm_creds (dict): Dictionary with 'instance_url' and 'access_token' for the CRM.
        confluence_creds (dict): Dictionary with 'url', 'email', and 'api_token' for Confluence.

    Returns:
        Crew: The configured Research Crew object.
    """

    # --- Custom Tools Definition (defined inside to access credentials) ---

    # @tool("Jira Search")
    # def search_jira(query: str) -> str:
    #     """Search Jira for project information, issues, and status updates using a JQL query."""
    #     try:
    #         if not all(k in jira_creds for k in ['url', 'email', 'api_token']):
    #             return "Jira credentials dictionary is incomplete."
            
    #         search_url = f"{jira_creds['url']}/rest/api/3/search"
    #         headers = {"Accept": "application/json"}
    #         auth = (jira_creds['email'], jira_creds['api_token'])
    #         params = {"jql": query, "maxResults": 50, "fields": "summary,status,priority,project"}
            
    #         response = requests.get(search_url, headers=headers, auth=auth, params=params)
    #         response.raise_for_status()
            
    #         data = response.json()
    #         issues = data.get('issues', [])
    #         if not issues:
    #             return f"No Jira issues found for query: {query}"
            
    #         results = [f"- {i['key']}: {i['fields']['summary']} (Status: {i['fields']['status']['name']})" for i in issues]
    #         return f"Found {len(issues)} Jira issues:\n" + "\n".join(results)
                
    #     except Exception as e:
    #         return f"Error searching Jira: {str(e)}"

    # @tool("CRM Query")
    # def query_crm(parameters: str) -> str:
    #     """Query CRM for customer data, deals, and revenue info."""
    #     try:
    #         if not all(k in crm_creds for k in ['instance_url', 'access_token']):
    #             return "CRM credentials dictionary is incomplete."
            
    #         query_url = f"{crm_creds['instance_url']}/services/data/v58.0/query"
    #         headers = {"Authorization": f"Bearer {crm_creds['access_token']}"}
    #         soql = f"SELECT Name, Amount, StageName, CloseDate FROM Opportunity WHERE {parameters} LIMIT 20"
            
    #         response = requests.get(query_url, headers=headers, params={"q": soql})
    #         response.raise_for_status()
            
    #         data = response.json()
    #         records = data.get('records', [])
    #         if not records:
    #             return f"No CRM records found for: {parameters}"
            
    #         results = [f"- {r['Name']}: ${r.get('Amount', 0):,.0f} ({r['StageName']})" for r in records]
    #         return f"Found {len(records)} CRM opportunities:\n" + "\n".join(results)
                
    #     except Exception as e:
    #         return f"Error querying CRM: {str(e)}"

    # @tool("Confluence Search")
    # def search_confluence(query: str) -> str:
    #     """Search Confluence for documentation, reports, and company knowledge."""
    #     try:
    #         if not all(k in confluence_creds for k in ['url', 'email', 'api_token']):
    #             return "Confluence credentials dictionary is incomplete."

    #         search_url = f"{confluence_creds['url']}/rest/api/content/search"
    #         auth = (confluence_creds['email'], confluence_creds['api_token'])
    #         params = {"cql": f'text ~ "{query}"', "limit": 10}
            
    #         response = requests.get(search_url, auth=auth, params=params)
    #         response.raise_for_status()
            
    #         data = response.json()
    #         results = data.get('results', [])
    #         if not results:
    #             return f"No Confluence pages found for: {query}"
            
    #         output = [f"- {r['title']}\n  URL: {confluence_creds['url']}{r['_links']['webui']}" for r in results]
    #         return f"Found {len(results)} Confluence pages:\n" + "\n".join(output)
                
    #     except Exception as e:
    #         return f"Error searching Confluence: {str(e)}"

    # --- Agent Configuration ---

    # Configure the LLM using the provided API key
    llm = ChatLiteLLM(
        model="gemini/gemini-2.0-flash", # Using the latest Gemini 2.0 Flash model
        temperature=0.7,
        api_key=google_api_key
    )

    # Initialize built-in tools with provided API key
    search_tool = SerpApiGoogleSearchTool(api_key=serper_api_key)

    # Create the Research Agent with all tools
    research_agent = Agent(
        role='Senior Business Research Analyst',
        goal='Conduct thorough research using company data sources and external information to compile a comprehensive business intelligence report',
        backstory="""You are an expert business research analyst. You have access to internal
        company systems like web search capabilities.
        You methodically use these tools to answer complex business questions.""",
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=[ search_tool]
    )

    # Create the research task
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
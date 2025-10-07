from crewai import Agent, Task, Crew, LLM
from crewai.tools import tool
from dotenv import load_dotenv
import os
import sqlite3
import pandas as pd

load_dotenv()

#
# This is the refactored script for the Data Analyst Agent.
# It is designed to be imported and used by the main Orchestrator.py script.
#

# --- Custom Tools Definition ---

@tool("SQL Query Executor")
def execute_sql_query(query: str) -> str:
    """
    Executes a SQL query against the 'company_data.db' database and returns results.
    Input must be a valid SQL query string.
    """
    try:
        conn = sqlite3.connect('company_data.db')
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            return "Query executed successfully but returned no results."
        
        return f"Query Results:\n{df.to_string()}\n\nRow Count: {len(df)}"
    
    except Exception as e:
        return f"Error executing query: {str(e)}"

@tool("Database Schema Inspector")
def get_database_schema() -> str:
    """
    Returns the database schema including table names, columns, and data types.
    No input required.
    """
    try:
        conn = sqlite3.connect('company_data.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        schema_info = "DATABASE SCHEMA:\n\n"
        for table in tables:
            table_name = table[0]
            schema_info += f"Table: {table_name}\n"
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            for col in columns:
                schema_info += f"  - {col[1]} ({col[2]})\n"
            schema_info += "\n"
        
        conn.close()
        return schema_info
    
    except Exception as e:
        return f"Error fetching schema: {str(e)}"


# --- Crew Creation Function ---

def create_data_analyst_crew():
    """
    Creates and configures the Data Analyst Crew.

    Returns:
        Crew: The configured Data Analyst Crew object.
    """
    # Configure LLM - Claude Sonnet is excellent for SQL and data analysis
    llm = LLM(
        model="claude/sonnet-4.5",  
        temperature=0.1,  
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )

    # Create the Data Analyst Agent
    data_analyst = Agent(
        role='Senior Data Analyst',
        goal='Analyze structured data to uncover actionable trends, metrics, and insights through SQL queries',
        backstory="""You are an expert data analyst with 10+ years of experience in SQL, 
        data warehousing, and business intelligence. You excel at writing optimized SQL queries,
        identifying trends, and translating business questions into data queries.""",
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=[execute_sql_query, get_database_schema]
    )

    # Define a comprehensive analysis task that combines previous goals
    comprehensive_analysis_task = Task(
        description="""Conduct a full strategic business analysis by performing the following steps:
        1.  **Inspect the Database Schema:** First, use the schema inspector tool to understand all available tables and their columns.
        2.  **Revenue Analysis:** Analyze monthly revenue trends for the last year, calculate MoM growth, and identify top products.
        3.  **Customer Metrics:** Calculate customer retention and churn rates.
        4.  **Product Performance:** Rank products by revenue and units sold.
        5.  **Sales Funnel:** Analyze conversion rates at each stage of the sales funnel.
        6.  **Synthesize Findings:** Compile all findings into a single, comprehensive report that summarizes the company's performance, highlights key trends, identifies risks (e.g., underperforming products, high churn), and suggests areas for improvement.""",
        expected_output="""A single, consolidated business analysis report containing:
        - A summary of the database schema.
        - A section on Revenue Trends with MoM growth rates.
        - A section on Customer Metrics with churn/retention rates.
        - A section on Product Performance with rankings.
        - A section on Sales Funnel analysis with conversion rates.
        - A final executive summary with 3 key takeaways and actionable recommendations.""",
        agent=data_analyst
    )

    # Create the Crew with a single, comprehensive task
    data_analyst_crew = Crew(
        agents=[data_analyst],
        tasks=[comprehensive_analysis_task],
        verbose=True
    )

    return data_analyst_crew

# Note: The 'if __name__ == "__main__":' block has been removed.
# This script should be executed via Orchestrator.py.
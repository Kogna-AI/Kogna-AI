# data_analyst_agent.py (Corrected version using sqlite3)

import json
import sqlite3
import pandas as pd
from crewai import Agent, Task, Crew
from crewai.tools import tool
from langchain_community.chat_models import ChatLiteLLM
from supabase_connect import get_supabase_manager
from dotenv import load_dotenv

load_dotenv()

#connect to supabase
supabase_manager = get_supabase_manager()
supabase = supabase_manager.client

def create_data_analyst_crew(
    gemini_api_key: str,
    # REVERTED: Now accepts a simple file path again
    db_path: str 
) -> Crew:
    """
    Creates the Data Analyst Crew using a direct SQLite database path.

    Args:
        gemini_api_key (str): The API key for the Google (Gemini) model.
        db_path (str): The file path for the SQLite database.
    """
    
    # --- Tools are defined inside the function to access db_path ---

    @tool("Load Data to DB")
    def load_data_to_db(json_data: str) -> str:
        """
        Loads structured JSON data into the 'recent_ingestion' table in the database.
        The table is replaced on each run. Input must be a valid JSON string.
        """
        try:
            data = json.loads(json_data)
            df = pd.DataFrame(data['records'])
            
            # REVERTED: Using sqlite3 directly
            conn = sqlite3.connect(db_path)
            df.to_sql('recent_ingestion', conn, if_exists='replace', index=False)
            conn.close()
            
            return f"Successfully loaded {len(df)} records into 'recent_ingestion' table."
        except Exception as e:
            return f"Error loading data to database: {str(e)}"

    @tool("SQL Query Executor")
    def execute_sql_query(query: str) -> str:
        """
        Executes a SQL query against the database and returns results.
        Input must be a valid SQL query string.
        """
        try:
            # REVERTED: Using sqlite3 directly
            conn = sqlite3.connect(db_path)
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if df.empty:
                return "Query executed successfully but returned no results."
            
            return f"Query Results:\n{df.to_string()}"
        
        except Exception as e:
            return f"Error executing query: {str(e)}"

    @tool("Database Schema Inspector")
    def get_database_schema() -> str:
        """Returns the database schema including table names and columns."""
        try:
            # REVERTED: Using sqlite3 directly
            conn = sqlite3.connect(db_path)
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

    llm = ChatLiteLLM(model="gemini/gemini-2.0-flash", temperature=0.2, api_key=gemini_api_key)

    data_analyst = Agent(
        role='Senior Data Analyst',
        goal='Analyze structured data to uncover insights through SQL queries.',
        backstory=(
            "You are an expert data analyst skilled in writing SQL queries to analyze new data and provide clear insights."
        ),
        verbose=True,
        llm=llm,
        tools=[load_data_to_db, execute_sql_query, get_database_schema]
    )

    dynamic_analysis_task = Task(
        description=(
            "Conduct a strategic analysis of the newly provided data from the '{structured_data}' input variable. "
            "1. **Load Data:** Use the 'Load Data to DB' tool to load the JSON data into the 'recent_ingestion' table. "
            "2. **Inspect Schema:** Use the schema inspector tool to understand the table structure. "
            "3. **Analyze Data:** Write and execute SQL queries on the 'recent_ingestion' table to find key insights. "
            "4. **Synthesize Findings:** Compile your findings into a comprehensive report."
        ),
        expected_output=(
            "A single, consolidated analysis report with key metrics from the new data "
            "and an executive summary with 1-2 key takeaways."
        ),
        agent=data_analyst
    )

    return Crew(agents=[data_analyst], tasks=[dynamic_analysis_task], verbose=True)
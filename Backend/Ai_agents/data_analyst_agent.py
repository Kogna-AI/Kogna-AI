from crewai import Agent, Task, Crew, LLM
from crewai.tools import tool
from dotenv import load_dotenv
import os
import sqlite3
import pandas as pd

load_dotenv()

# Configure LLM - Claude Sonnet is excellent for SQL and data analysis
llm = LLM(
    model="claude-sonnet-4-5-20250929",  
    temperature=0.1,  
    api_key=os.getenv("ANTHROPIC_API_KEY")
)


# Custom tool for SQL query execution
@tool("SQL Query Executor")
def execute_sql_query(query: str) -> str:
    """
    Executes a SQL query against the database and returns results.
    Input should be a valid SQL query string.
    """
    try:
        # Connect to your database (modify connection details as needed)
        # This example uses SQLite, but you can adapt for PostgreSQL, MySQL, etc.
        conn = sqlite3.connect('company_data.db')  # Replace with your DB
        
        # Execute query and get results as DataFrame
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Return formatted results
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
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        schema_info = "DATABASE SCHEMA:\n\n"
        
        for table in tables:
            table_name = table[0]
            schema_info += f"Table: {table_name}\n"
            
            # Get column info for each table
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            for col in columns:
                schema_info += f"  - {col[1]} ({col[2]})\n"
            schema_info += "\n"
        
        conn.close()
        return schema_info
    
    except Exception as e:
        return f"Error fetching schema: {str(e)}"


# Create the Data Analyst Agent
data_analyst = Agent(
    role='Senior Data Analyst',
    goal='Analyze structured data to uncover actionable trends, metrics, and insights through SQL queries',
    backstory="""You are an expert data analyst with 10+ years of experience in SQL, 
    data warehousing, and business intelligence. You excel at:
    - Writing optimized SQL queries for complex data analysis
    - Identifying trends and patterns in large datasets
    - Translating business questions into data queries
    - Presenting data insights in clear, actionable formats
    - Understanding data quality issues and anomalies
    You always validate your queries and explain your analytical approach.""",
    verbose=True,
    allow_delegation=False,
    llm=llm,
    tools=[execute_sql_query, get_database_schema]
)


# Task 1: Revenue Analysis
revenue_analysis_task = Task(
    description="""Analyze revenue trends over the last 12 months. 
    1. Query the database to get monthly revenue totals
    2. Identify growth patterns and any significant changes
    3. Calculate month-over-month growth rates
    4. Highlight top revenue-generating products/segments""",
    expected_output="""A comprehensive revenue analysis report including:
    - Monthly revenue breakdown
    - Growth percentages
    - Top performers
    - Key trends and anomalies""",
    agent=data_analyst
)


# Task 2: Customer Metrics Analysis
customer_metrics_task = Task(
    description="""Analyze customer engagement and retention metrics:
    1. Calculate customer acquisition, retention, and churn rates
    2. Identify customer segments by value (high/medium/low)
    3. Analyze customer lifetime value (CLV) trends
    4. Detect patterns in customer behavior""",
    expected_output="""Customer metrics dashboard summary with:
    - Acquisition, retention, and churn rates
    - Customer segmentation analysis
    - CLV trends
    - Behavioral insights""",
    agent=data_analyst
)


# Task 3: Product Performance Analysis
product_performance_task = Task(
    description="""Evaluate product performance across all offerings:
    1. Rank products by revenue, units sold, and profit margin
    2. Identify underperforming products
    3. Analyze product adoption rates
    4. Compare performance across different time periods""",
    expected_output="""Product performance report with:
    - Product rankings by key metrics
    - Underperformer identification
    - Adoption rate analysis
    - Period-over-period comparisons""",
    agent=data_analyst
)


# Task 4: Sales Funnel Analysis
sales_funnel_task = Task(
    description="""Analyze the sales funnel and conversion rates:
    1. Calculate conversion rates at each funnel stage
    2. Identify bottlenecks and drop-off points
    3. Compare funnel performance across channels
    4. Analyze time-to-conversion metrics""",
    expected_output="""Sales funnel analysis with:
    - Stage-by-stage conversion rates
    - Bottleneck identification
    - Channel comparison
    - Conversion time analysis""",
    agent=data_analyst
)


# Task 5: Department KPI Dashboard
department_kpi_task = Task(
    description="""Generate KPI metrics for each department:
    1. Extract key performance indicators per department
    2. Compare against targets/benchmarks
    3. Identify departments exceeding or missing goals
    4. Highlight critical metrics requiring attention""",
    expected_output="""Department KPI summary with:
    - KPIs by department
    - Target vs. actual comparison
    - Performance ratings
    - Priority action items""",
    agent=data_analyst
)


# Task 6: Predictive Insights
predictive_insights_task = Task(
    description="""Identify data patterns that could predict future trends:
    1. Analyze historical data for seasonal patterns
    2. Identify correlations between key metrics
    3. Flag early warning indicators for potential issues
    4. Suggest areas for deeper investigation""",
    expected_output="""Predictive insights report with:
    - Seasonal patterns identified
    - Key metric correlations
    - Early warning signals
    - Investigation recommendations""",
    agent=data_analyst
)


# Create the Crew
crew = Crew(
    agents=[data_analyst],
    tasks=[
        revenue_analysis_task,
        customer_metrics_task,
        product_performance_task,
        sales_funnel_task,
        department_kpi_task,
        predictive_insights_task
    ],
    verbose=True
)


# Execute the analysis
if __name__ == "__main__":
    print("\n" + "="*60)
    print("Starting Data Analyst Agent - Strategic Dashboard Analysis")
    print("="*60 + "\n")
    
    result = crew.kickoff()
    
    print("\n" + "="*60)
    print("FINAL DATA ANALYSIS RESULTS")
    print("="*60 + "\n")
    print(result)
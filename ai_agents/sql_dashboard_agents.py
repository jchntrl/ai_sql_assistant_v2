import streamlit as st
from openai import OpenAI
# from snowflake_utils import SnowflakeHandler
from pydantic import BaseModel
from typing import Optional, List, Tuple, Any
from decimal import Decimal
import asyncio
import io

import sys
import os
# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from snowflake_utils import SnowflakeHandler
from st_utils import get_dataframe_info, convert_decimals_to_float

from agents import Agent, Runner, function_tool, trace, handoff, ModelSettings
from ai_agents.chart_generator_agents import  data_vizualization_agent

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Global variable to hold the SnowflakeHandler instance
snowflake_db = None

### TOOLS

@function_tool
def get_database_context() -> str:
    """
    Retrieve the current schema name and table list with metadata from the database.
    
    Returns:
        str: Formatted markdown containing schema name and tables information
    """
    output = f"""
# Schema
{snowflake_db.schema}

# Tables
{snowflake_db.get_tables()}
    """
    return output

@function_tool
def get_tables_columns(table_list: list[str]) -> str:
    """
    Retrieve detailed column definitions for specified tables.
    
    Args:
        table_list: List of table names to get column information for
        
    Returns:
        str: Markdown formatted table definitions with column metadata
    """
    return snowflake_db.get_tables_columns(table_list)

@function_tool
def get_tables_info(table_list: list[str]) -> str:
    """
    Retrieve comprehensive table information including column definitions and sample data.
    
    Args:
        table_list: List of table names to get complete information for
        
    Returns:
        str: Markdown formatted output with table definitions and 5 sample rows for each table
    """
    return snowflake_db.get_tables_info_md(table_list)

class DistinctValueQuery(BaseModel):
    field: str
    table: str
    filter: str = ''

@function_tool
def get_distinct_values_from_table_list(queries: List[DistinctValueQuery])-> str:
    """
    Get distinct values for multiple field/table/filter combinations.
    
    Args:
        queries: List of DistinctValueQuery objects, each containing:
            - field: Column name to get distinct values for
            - table: Table name to query  
            - filter: Optional WHERE clause filter (default: '')
        
    Returns:
        str: Markdown formatted results with headers for each query (max 15 rows returned per query)
        
    Example:
        queries = [
            DistinctValueQuery(field='COUNTY', table='DEMOGRAPHICS', filter="STATE = 'LA'"),
            DistinctValueQuery(field='CATEGORY', table='PRODUCTS', filter='')
        ]
        get_distinct_values_from_table_list(queries)
    """
    # Convert Pydantic models to dictionaries for the underlying function
    query_dicts = [query.dict() for query in queries]
    return snowflake_db.get_distinct_values_from_table_list_dict(query_dicts)

@function_tool
def validate_sql_query(sql_query: str) -> str:
    """
    Validate SQL query syntax without executing it using EXPLAIN.
    
    Args:
        sql_query: SQL query string to validate
        
    Returns:
        str: "✅ Query is valid." if syntax is correct, error message if invalid
    """
    return snowflake_db.validate_query(sql_query)
    

@function_tool
def ask_user_for_clarification(clarifying_questions: List[str]) -> List[str]:
    """
    Present clarifying questions to the user for interactive input.
    
    Args:
        clarifying_questions: List of questions to ask the user
        
    Returns:
        List[str]: List of user responses corresponding to each question
    """
    answer = []
    for i, question in enumerate(clarifying_questions, start=1):
        answer.append(question + ": " + input(f"**Clarifying Question {i}:** {question}\n"))
    return answer

### AGENTS

class Visualization(BaseModel):
    visualization_name: str
    visualization_type: str
    caption: str
    sql_query: str
    chart_code: Optional[str]

class DashboardDesignerOutput(BaseModel):
    sufficient_context: bool
    comment: str
    visualizations: List[Visualization]
    # questions_for_user: Optional[List[str]]

dashboard_designer_agent = Agent(
    name="dashboard_designer_agent",
    instructions=("""
You are an expert SQL and Data Visualization Agent tasked with translating vague user requests (e.g., "tell me about the sales") into insightful dashboards using the structure and content of the database.

Your primary objective is to deeply understand the user's intent and the database schema, and to design a dashboard that provides the most relevant insights.

You have access to database metadata, including:
- Schema names
- Table and column names
- Data types
- Table relationships

Using this information, your task is to:
1. Analyze the user's message.
2. Identify relevant tables (using `get_database_context`), columns, and relationships (using `get_tables_columns`).
3. Make reasonable assumptions about user intent based on schema content.
4. Design **5 visualizations** that would provide meaningful insights.

For **each visualization**, output the following:
- `visualization_name`: A short descriptive title.
- `visualization_type`: Choose one of `line_chart`, `bar_chart`, `area_chart`, `scatter_chart`, `map`.
- `caption`: A short sentence describing the purpose or insight of the visualization.
- `sql_query`: A Snowflake-compatible SQL query to extract the necessary data. When referencing tables use the format <schema_name>.<table_name>
- Keep `chart_code` empty as it will be populated by the Chart Agent

Guidelines:
- If the user input is too vague or ambiguous, identify what additional information is needed, set `sufficient_context = false`.
- If confident in your interpretation and visual suggestions, set `sufficient_context = true`.
- Ensure the queries are aligned with the database structure and return fields suitable for the selected chart type.
   """
    ), 
    # model="gpt-4o",
    model="gpt-4.1",
    model_settings=ModelSettings(tool_choice="required", temperature=0.3),
    tools=[get_database_context,get_tables_info,get_distinct_values_from_table_list],
    output_type= DashboardDesignerOutput,
)

async def run_sql_dashboard_agents(user_input: str, snowflake_handler: SnowflakeHandler) -> DashboardDesignerOutput:
    """
    Generate a comprehensive dashboard with visualizations based on user request.
    
    Args:
        user_input: Natural language request from user for dashboard creation
        selected_db: Target database name
        selected_schema: Target schema name
        
    Returns:
        DashboardFinalOutput: Contains generated visualizations with SQL queries and chart code
    """

    # Set the global snowflake_db to the passed handler instance
    global snowflake_db
    snowflake_db = snowflake_handler

    dashboard_result = await Runner.run(dashboard_designer_agent, user_input)

    updated_visualizations = []

    for viz in dashboard_result.final_output.visualizations:
        upd_viz = viz
        df = snowflake_db.execute_query_df(viz.sql_query)
        df = convert_decimals_to_float(df)
    
        df_info_str = get_dataframe_info(df, include_sample=True)

        context = f"User: {dashboard_result.final_output.comment}\n\n# DataFrame Info \n{df_info_str}"

        chart = await Runner.run(data_vizualization_agent,context)

        # Create a new instance with added field
        upd_viz = viz.model_copy()
        # upd_viz.__dict__["code_block"] = chart.final_output.code_block
        upd_viz.chart_code = chart.final_output.code_block
        updated_visualizations.append(upd_viz)

    dashboard_result.final_output.visualizations = updated_visualizations


    print(("-" * 80) + "\nDashboard Designer Output:")
    print(dashboard_result)
    print("-" * 80) 

    return dashboard_result.final_output

if __name__ == "__main__":

    selected_db = 'SANDBOX'
    selected_schema = 'SUPERSTORE'

    user_input = "Tell me about the sales"

    # Initialize the Snowflake database handler
    snowflake_db = SnowflakeHandler(
        user=st.secrets["SNOWFLAKE_USER"],
        password=st.secrets["SNOWFLAKE_PASSWORD"],
        account=st.secrets["SNOWFLAKE_ACCOUNT"],
        warehouse=st.secrets["SNOWFLAKE_WAREHOUSE"],
        database=selected_db,
        schema=selected_schema)
    
    snowflake_db.connect()
    with trace("SQL Dashboard Agents"):
        asyncio.run(run_sql_dashboard_agents(user_input,snowflake_db))
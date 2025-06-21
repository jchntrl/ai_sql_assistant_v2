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

from agents import Agent, Runner, function_tool, trace, handoff, ModelSettings
from ai_agents.chart_generator_agents import  data_vizualization_agent

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Initialize the Snowflake database handler
snowflake_db = SnowflakeHandler(
    user=st.secrets["SNOWFLAKE_USER"],
    password=st.secrets["SNOWFLAKE_PASSWORD"],
    account=st.secrets["SNOWFLAKE_ACCOUNT"],
    warehouse=st.secrets["SNOWFLAKE_WAREHOUSE"],
    database=None,
    schema=None)

### TOOLS

@function_tool
def get_database_context() -> str:
    """
    Retrieve the database schema including tables and their columns.
    :return: markdown table as str.
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
    Retrieve the columns of specific tables in the database.
    :param table_list: List of tables to retrieve columns for.
    :return: markdown tables as str.
    """
    return snowflake_db.get_tables_columns(table_list)

@function_tool
def validate_sql_query(sql_query: str) -> str:
    """
    Validate the SQL query can be executed.
    :param sql_query: The SQL query to validate.
    :return: valid or not valid.
    """
    return snowflake_db.validate_query(sql_query)
    

@function_tool
def ask_user_for_clarification(clarifying_questions: List[str]) -> List[str]:
    """
    Ask the user for clarification on ambiguous points in the request.
    :param clarifying_questions: List of questions to ask the user.
    :return: User's response as a string.
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

class DashboardDesignerOutput(BaseModel):
    sufficient_context: bool
    comment: str
    visualizations: List[Visualization]
    questions_for_user: Optional[List[str]]

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
- `visualization_type`: Choose one of `line_chart`, `bar_chart`, `area_chart`, `scatter_chart`.
- `caption`: A short sentence describing the purpose or insight of the visualization.
- `sql_query`: A Snowflake-compatible SQL query to extract the necessary data. When referencing tables use the format <schema_name>.<table_name>

Guidelines:
- If the user input is too vague or ambiguous, identify what additional information is needed, set `sufficient_context = false` and call the tool `ask_user_for_clarification`.
- If confident in your interpretation and visual suggestions, set `sufficient_context = true`.
- Ensure the queries are aligned with the database structure and return fields suitable for the selected chart type.
   """
    ), 
    # model="gpt-4o",
    model="gpt-4.1",
    model_settings=ModelSettings(tool_choice="required"),
    tools=[get_database_context,get_tables_columns,ask_user_for_clarification],
    output_type= DashboardDesignerOutput,
)

class DashboardFinalOutput(BaseModel):
    message: str
    visualizations: List[Visualization]

async def run_sql_dashboard_agents(user_input,selected_db,selected_schema):

    snowflake_db.database = selected_db
    snowflake_db.schema = selected_schema

    snowflake_db.connect()

    with trace("SQL Dashboard Agents"):

        # response = DashboardFinalOutput(
        #     message = None, 
        #     visualizations = [None],
        #     )
        # Run the SME agent to analyze the request and extract context
        dashboard_result = await Runner.run(dashboard_designer_agent, user_input)

        # Print the structured context generated by the SME agent
        print("\nSME Agent Context:")
        print(dashboard_result)

        updated_visualizations = []

        for viz in dashboard_result.final_output.visualizations:
            upd_viz = viz
            df = snowflake_db.execute_query_df(viz.sql_query)
            if not df.empty:
                for col in df.columns:
                        if isinstance(df[col].iloc[0], Decimal):
                            df[col] = df[col].astype(float)
        
            buffer = io.StringIO()
            df.info(buf=buffer)
            df_info_str = buffer.getvalue()

            context = f"User: {dashboard_result.final_output.comment}\n\n# DataFrame Info \n{df_info_str}"

            chart = await Runner.run(data_vizualization_agent,context)

            # Create a new instance with added field
            upd_viz = viz.copy()
            upd_viz.__dict__["code_block"] = chart.final_output.code_block  # OR see below for better practice
            updated_visualizations.append(upd_viz)

        response = DashboardFinalOutput(
            message = dashboard_result.final_output.comment,
            visualizations = updated_visualizations
        )

        return response

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
    
    asyncio.run(run_sql_dashboard_agents(user_input,selected_db,selected_schema))
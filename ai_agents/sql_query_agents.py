import streamlit as st
from openai import OpenAI
# from snowflake_utils import SnowflakeHandler
from pydantic import BaseModel
from typing import Optional, List, Tuple, Any
import asyncio

from agents import Agent, Runner, function_tool, trace, handoff

import sys
import os
# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from snowflake_utils import SnowflakeHandler

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
    Retrieve the database schema and the list of its tables.
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
    :return: markdown tables.
    """
    return snowflake_db.get_table_list_columns(table_list)

@function_tool
def get_tables_sample(table_list: list[str]) -> str:
    """
    Retrieve a 5 rows sample of specific tables in the database.
    :param table_list: List of tables to retrieve sample for.
    :return: markdown tables.
    """
    return snowflake_db.get_tables_sample_md(table_list)

@function_tool
def get_tables_info(table_list: list[str]) -> str:
    """
    Retrieve the columns definition and a 5 rows sample of specific tables in the database.
    :param table_list: List of tables to retrieve sample for.
    :return: markdown tables.
    """
    return snowflake_db.get_tables_info_md(table_list)

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

class DBSMEOutput(BaseModel):
    sufficient_context: bool
    comment: str

database_sme_agent = Agent(
    name="database_sme_agent",
    instructions=("""
    You are an expert SQL SME Agent tasked with understanding a user's request and analyzing the database schema to extract relevant contextual information.
    Your main goal is to generate a clear, structured context that includes:
    - Schema name, key tables, columns, and relationships relevant to the request
    - Assumptions or inferred meanings
    - Potential filters, joins, or calculations that may be involved
                  
    You do not write the SQL query — your output will be used by another agent that specializes in SQL generation.
    You have access to the database metadata (e.g., table names, column names, datatypes, and relationships). Use this to deeply explore and describe how the user request maps to the schema.

    If there is not enough information to generate a SQL query, set `sufficient_context` to false and provide a detailed explanation of the problems.
    """
    ), 
    # model="gpt-4o",
    model="gpt-4.1",
    # tools=[get_database_context,get_tables_columns],
    tools=[get_database_context,get_tables_info],
    # tools=[get_database_context,get_tables_columns,get_tables_sample],
    # tools=[get_database_context,get_tables_columns,ask_user_for_clarification],
    output_type= DBSMEOutput,
)

    # In order to achieve your goal you must call the tools at your disposition in this order:
    # 1. use the `get_database_context` tool to retrieve the database schema, description and table list.
    # 2. use the 'get_tables_columns' tool to get the table definition of the table you deem relevant
    # 3. use the `ask_user_for_clarification` tool to ask the user clarifying questions.

    # Do not finish your analysis until you have called the 3 tools above.

class SQLQueryOutput(BaseModel):
    sql_query: str
    comment: str
    validation_result: bool

sql_query_builder_agent = Agent(
    name="sql_query_builder_agent",
    instructions=f""""
    You are a highly skilled Snowflake SQL Query Builder Agent. 
    Your task is to write efficient, accurate SQL queries based on structured context provided by a domain expert agent (SME).

    The context includes:
    - The user's original request
    - A summary of intent
    - Relevant tables and columns
    - Table relationships and join conditions

    Use this context to write a complete SQL query, handling joins, filters, aggregations, and expressions as needed. Prefer readable aliases and qualified column names (e.g., orders.order_date).
    ❗ You do not need to reanalyze schema metadata. Your sole responsibility is to generate the SQL query.

    Be cautious about:
    - Matching column names to their correct tables
    - Applying proper WHERE clauses and JOIN conditions
    - Using aggregation only if it matches the intent
    - Adding comments when helpful (optional)
    - Always using the <schema_name>.<table_name> format when referencing tables

    Provide a short explanation of what the query returns

    You must test that the SQL query is correct using the `validate_sql_query` tool.
    """,
    model = 'gpt-4.1-mini',
    tools=[validate_sql_query],
    output_type= SQLQueryOutput,
)

class SQLValidationOutput(BaseModel):
    sql_valid: bool
    comment: str

sql_query_validator_agent = Agent(
    name="sql_query_validator_agent",
    instructions=f""""
    You are a Snowflake SQL Validation Agent. Your role is to review and validate SQL queries generated by another agent.
    Your goal is to ensure the query is accurate, executable, and aligned with the context. You must check the following:
    - ✅ Correctness: Does the SQL use the correct tables, columns, and joins based on the schema?
    - ✅ Format: Is the SQL formatted correctly for Snowflake, including proper use of schema and table names? When referencing tables, always use the format <schema_name>.<table_name>.
    - ✅ Alignment: Does the logic match the user intent and structured context?
    - ✅ Syntax: Is the SQL syntactically valid?
    - ✅ Style & Best Practices: Is the SQL readable, uses aliases if helpful, and avoids unnecessary complexity?
    - ❓ Clarifications: Flag potential ambiguities or edge cases.
    You do not run the query — you simulate a reasoning-based review using the metadata and context.
    You have access to the tables definition by using the `get_tables_columns` tool and providing the just the table name of the tables as a list (no schema needed for this tool).
    If the query is valid, return "sql_valid" as true. 
    If the query is invalid, return "sql_valid" as false and provide a detailed explanation of the problems and suggestions for improvement and handoff to the sql_query_builder_agent.
    """,
    model = 'gpt-4.1-mini',
    # tools=[get_tables_columns,get_tables_sample,validate_sql_query],
    tools=[get_tables_info,validate_sql_query],
    output_type=SQLValidationOutput,
)

class SQLAgentFinalOutput(BaseModel):
    message: Optional[str]
    sql_query: Optional[str]

async def run_sql_query_agents(user_input,selected_db,selected_schema,force_validator_agent):

    snowflake_db.database = selected_db
    snowflake_db.schema = selected_schema

    snowflake_db.connect()

    response = SQLAgentFinalOutput(
        message = None, 
        sql_query = None,
        )
    # Run the SME agent to analyze the request and extract context
    sme_result = await Runner.run(database_sme_agent, user_input)

    # Print the structured context generated by the SME agent
    print("\nSME Agent Context:")
    print(sme_result.final_output.comment)

    if not sme_result.final_output.sufficient_context:
        print("\nNot enough context to generate a SQL query. Please provide more information.")
        print("SME Agent Comment:", sme_result.final_output.comment)

        response.message = sme_result.final_output.comment
        response.sql_query = ""
        return response

    # Now run the SQL query builder agent with the structured context
    sql_builder = await Runner.run(sql_query_builder_agent, sme_result.final_output.comment)

    # Print the generated SQL query
    print("\nSQL Builder:")
    print(sql_builder.final_output)

    if not sql_builder.final_output.validation_result or force_validator_agent:

        sql_validation = await Runner.run(sql_query_validator_agent, sql_builder.final_output.sql_query)
        # Print the validation result
        print("\nSQL Validation Result:")
        print(sql_validation.final_output) 

        max_retries = 3
        retry_count = 0
        while sql_validation.final_output.sql_valid is False and retry_count < max_retries:
            print("\nSQL Query is invalid. Handoff to SQL Query Builder Agent for rework.")

            context = f"""
            user request: {user_input}\n
            structured context: {sme_result.final_output}\n
            incorrect SQL query: {sql_builder.final_output.sql_query}\n
            suggested modifications: {sql_validation.final_output.comment}
            """

            # Handoff to the SQL Query Builder Agent for rework
            sql_builder = await Runner.run(sql_query_builder_agent,context)

            # Print the new generated SQL query
            print("\nNew Generated SQL Query:")
            print(sql_builder.final_output.sql_query)

            # Validate the new SQL query
            sql_validation = await Runner.run(sql_query_validator_agent, sql_builder.final_output.sql_query)
            print("\nSQL Validation Result:")
            print(sql_validation.final_output.comment)

            retry_count += 1

    # Print the generated SQL query
    print("\nFinal SQL Query:")
    print(sql_builder.final_output.sql_query)

    response.message = sql_builder.final_output.comment
    response.sql_query = sql_builder.final_output.sql_query
    
    snowflake_db.close_connection()

    return response

if __name__ == "__main__":

    selected_db = 'COVID19_EPIDEMIOLOGICAL_DATA'
    selected_schema = 'PUBLIC'

    user_input = "What is the city that has the highest number of COVID-19 case at the height of the pandemic in the US?"

    force_validator_agent = True

    # Initialize the Snowflake database handler
    snowflake_db = SnowflakeHandler(
        user=st.secrets["SNOWFLAKE_USER"],
        password=st.secrets["SNOWFLAKE_PASSWORD"],
        account=st.secrets["SNOWFLAKE_ACCOUNT"],
        warehouse=st.secrets["SNOWFLAKE_WAREHOUSE"],
        database=selected_db,
        schema=selected_schema)
    
    snowflake_db.connect()

    with trace("SQL Query Agents"):
    
        asyncio.run(run_sql_query_agents(user_input,selected_db,selected_schema,force_validator_agent))
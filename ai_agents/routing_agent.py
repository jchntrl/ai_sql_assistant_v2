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

class RoutingOutput(BaseModel):
    handoff: str
    questions_for_users: Optional[str]
    user_request: Optional[str]
    # comment: Optional[str]

routing_agent = Agent(
    name="routing_agent",
    instructions=("""
You are a Routing Agent responsible for analyzing a user's input and deciding what to do next.
Your job is to generate a structured response indicating how the request should be handled.

You must return a `RoutingOutput` object with the following fields:

- `handoff`: One of the following values:
    - "user" — if anything about the request is unclear, underspecified, or potentially ambiguous. Always prefer to ask clarifying questions when in doubt.
    - "sql_query_agent" — if the user's question is clear, specific, and can be answered with a precise SQL query.
    - "dashboard_agent" — if the user's request is vague, exploratory, or better suited to a visual summary. *Always ask the user confirmation before handing off to the dashboard agent*
- `questions_for_users`: A string containing a follow-up question (or multiple questions) if `handoff` is "user". Leave blank otherwise.
- `user_request`: The refined or original user request if `handoff` is not "user". Leave blank if asking a clarification question.

Instructions:

1. Carefully analyze the user’s request, and get the database context using the tool `get_database_context`
2. If the request contains any ambiguity, lacks specifics, or makes assumptions that need validation:
    - Set `handoff` to "user".
    - Ask one or more clarifying questions to refine the intent.
    - Leave `user_request` empty.
3. If the request is clearly formulated and includes all necessary information to form a SQL query (e.g., "Show me the sales over time for 2023"):
    - Set `handoff` to "sql_query_agent".
    - Leave `questions_for_users` empty.
    - Populate `user_request` with the parsed or cleaned version of the question.
4. If the request is open-ended or general (e.g., "Tell me about the sales"):
    - Always ask the user confirmation before handing off to the dashboard agent
        - Set `handoff` to "user" and populate `questions_for_users`
    - If the message history shows the user confirmed he wants a dashboard: 
        - Set `handoff` to "dashboard_agent" 
        - Leave `questions_for_users` empty.
        - Populate `user_request` with a cleaned-up or summarized version of the request.
5. If the request falls outside of data-related topics:
    - Set `handoff` to "user" and ask the user to rephrase or clarify their request in a way relevant to the database.

Be cautious. When in doubt, choose to clarify. It is better to ask a follow-up question than to risk misunderstanding the user's intent.
"""
    ), 
    model="gpt-4o",
    tools=[get_database_context],
    output_type= RoutingOutput,
)

async def run_routing_agent(user_input: str, snowflake_handler: SnowflakeHandler) -> RoutingOutput:
    """
    Route user requests to appropriate agents based on content analysis.
    
    Args:
        user_input: Natural language request from user
        selected_db: Target database name
        selected_schema: Target schema name
        
    Returns:
        RoutingOutput: Contains routing decision and any clarifying questions or refined requests
    """

    # Set the global snowflake_db to the passed handler instance
    global snowflake_db
    snowflake_db = snowflake_handler

    routing_result = await Runner.run(routing_agent, user_input)

    # Print the structured context generated by the SME agent
    # print("\nRouting Agent Context:\n\n")
    # print(routing_result.final_output)
    
    return routing_result.final_output

if __name__ == "__main__":

    selected_db = 'COVID19_EPIDEMIOLOGICAL_DATA'
    selected_schema = 'PUBLIC'

    user_input = "What is the city that has the highest number of COVID-19 case at the height of the pandemic in the US?"

    user_input = "How many covid cases?"

    user_input = "Who is the president of the United States of America?"

    user_input = "When was the height of the pandemic in NY?"



    # Initialize the Snowflake database handler
    snowflake_db = SnowflakeHandler(
        user=st.secrets["SNOWFLAKE_USER"],
        password=st.secrets["SNOWFLAKE_PASSWORD"],
        account=st.secrets["SNOWFLAKE_ACCOUNT"],
        warehouse=st.secrets["SNOWFLAKE_WAREHOUSE"],
        database=selected_db,
        schema=selected_schema)
    
    snowflake_db.connect()

    handoff = 'user'

    # class RoutingOutput(BaseModel):
    #     handoff: str
    #     questions_for_users: Optional[str]
    #     user_request: Optional[str]

    with trace("Routing Agent"):
        
        while handoff == 'user':
            
            routing = asyncio.run(run_routing_agent(user_input,selected_db,selected_schema))
            
            handoff = routing.handoff
            
            if handoff == 'user':
                user_answer = input(routing.questions_for_users + '\n')
                user_input = f"user: {user_input}\n\nrouting agent: {routing.questions_for_users}\n\nuser:{user_answer}"
                print(f"user: {user_input}\n\nrouting agent: {routing.user_request}\n\nuser:{user_answer}")
            else: 
                print(f"user: {user_input}\n\nhandoff -> {handoff}\n\nrouting agent: {routing.user_request}")
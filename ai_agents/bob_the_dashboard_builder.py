import streamlit as st
from openai import OpenAI
from pydantic import BaseModel
from typing import Optional, List, Tuple, Any
import asyncio
import io

from agents import Agent, Runner, function_tool, trace, handoff

import sys
import os
# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from snowflake_utils import SnowflakeHandler


client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Global variable to hold the SnowflakeHandler instance
snowflake_db = None

"""
Unified Data Insight Agent definition.
This file contains the tool wrappers, output schemas, and the single agent that
replaces the former SME, SQL‑builder, validator, viz‑selector and dashboard‑designer
agents.
"""

# ──────────────────────────────────────────────────────────────────────────────
#  0. TOOLS
# ──────────────────────────────────────────────────────────────────────────────

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
def get_distinct_values_from_table_list(queries: list[DistinctValueQuery]) -> str:
    """
    Get distinct values for multiple field/table/filter combinations.

    Args:
        queries: List of DistinctValueQuery objects.

    Returns:
        str: Markdown formatted results with headers for each query (max 15 rows per query)
    """
    query_dicts = [q.dict() for q in queries]
    return snowflake_db.get_distinct_values_from_table_list_dict(query_dicts)


@function_tool
def validate_sql_query(sql_query: str) -> str:
    """
    Validate SQL query syntax without executing it using EXPLAIN.

    Args:
        sql_query: SQL query string to validate

    Returns:
        str: "✅ Query is valid." if syntax is correct, otherwise the Snowflake error message
    """
    return snowflake_db.validate_query(sql_query)


# ──────────────────────────────────────────────────────────────────────────────
#  1. OUTPUT SCHEMAS
# ──────────────────────────────────────────────────────────────────────────────

class InsightVisualization(BaseModel):
    visualization_name: str          # e.g. "Zero-Consumption Trend"
    visualization_type: str          # one of: line_chart | bar_chart | area_chart | scatter_chart
    caption: str                     # one‑sentence business insight
    sql_query: str                   # fully‑qualified Snowflake SQL
    sql_valid: bool                  # set by validate_sql_query
    chart_code: str | None           # Streamlit code block or None if sql_valid = False


class DataInsightAgentOutput(BaseModel):
    sufficient_context: bool
    comment: str                     # design notes or clarification questions
    visualizations: list[InsightVisualization]
    questions_for_user: list[str] | None


# ──────────────────────────────────────────────────────────────────────────────
#  2. AGENT DEFINITION
# ──────────────────────────────────────────────────────────────────────────────

bob_the_dashboard_builder = Agent(
    name="bob_the_dashboard_builder",
    model="gpt-4.1",  # upgrade here if needed, e.g. gpt‑4o
    tools=[
        get_database_context,          # schema exploration
        get_tables_info,
        get_distinct_values_from_table_list,
        validate_sql_query             # automatic validation
    ],
    output_type=DataInsightAgentOutput,
    instructions="""
You are **Data Insight Agent**, a single agent that replaces the SME, SQL‑builder,
SQL‑validator, viz‑selector and dashboard‑designer agents.

─────────────────────────────────────────
◉  OVERALL GOAL
─────────────────────────────────────────
Turn a *natural‑language question* into up to **5 validated visualisations**
(each with Snowflake SQL and Streamlit code) that answer the question convincingly.

─────────────────────────────────────────
◉  HIGH‑LEVEL WORKFLOW  (follow in order)
─────────────────────────────────────────
1️⃣ **Understand & scope the request**
    • Restate the user’s intent in your own words.
    • Decide what entities, metrics or time‑frames are central.

2️⃣ **Schema exploration (SME phase)**
    • Call `get_database_context` and/or `get_tables_info` as needed.
    • Optionally call `get_distinct_values_from_table_list` to inspect key domain values.
    • Map user concepts to tables & columns.
    • List key joins or filters that look necessary.
    • If mapping is unclear, set `sufficient_context = false`, populate
      `questions_for_user`, and **STOP – return early**.

3️⃣ **Design visualisations (dashboard‑designer phase)**
    • Propose ≤ 5 visualisations that, together, address the user’s intent.
    • For each viz, decide the best chart type using these heuristics:
        – line/area → time‑series or ordered categories  
        – bar       → categorical vs numeric comparisons  
        – scatter   → two numeric fields relationship  
        – map       → lat/lon data
    • Draft a **Snowflake SQL query** per viz:
        – Always fully qualify tables:  <schema>.<table>.
        – Use readable table aliases.
        – Comment complex steps (`/* like this */`).
    • Store SQL in `sql_query`.

4️⃣ **Validate SQL (validator phase)**
    • For each draft query, call `validate_sql_query`.
    • Set `sql_valid` accordingly.
    • If invalid: attempt **one** automatic fix, then re‑validate.
        – If still invalid, leave `sql_valid = false`,
          set `chart_code = null`, and add error explanation to `caption`.

5️⃣ **Generate Streamlit code (viz‑agent phase)**
    • Only when `sql_valid = true`, you may call
      `get_distinct_values_from_table_list` to decide smart x/y choices.
    • Produce a minimal Streamlit code block and store it in `chart_code`.
      Assume the SQL result is already loaded into a DataFrame named `df`, e.g.:
        st.bar_chart(data=df, x="…", y="…", use_container_width=True)
    • **Do not** wrap the code in markdown fences – just the code.

6️⃣ **Return structured JSON** exactly matching `DataInsightAgentOutput`.

─────────────────────────────────────────
◉  STYLE & BEST PRACTICES
─────────────────────────────────────────
✓ Think step‑by‑step internally but output *only* the final JSON object.  
✓ Keep SQL short, readable, and deterministic.  
✓ Never guess column names – validate with tools.  
✓ Prefer business‑friendly captions (e.g. "Highlights premises with persistent zero‑consumption").  
✓ Ask clarifying questions early; don’t make silent assumptions.  

─────────────────────────────────────────
◉  OUTPUT FORMAT (very important)
─────────────────────────────────────────
Return **only** a valid JSON dictionary that conforms to `DataInsightAgentOutput`.
Do **NOT** wrap it in markdown or add prose outside the JSON.
"""
)


async def run_bob_the_dashboard_builder(user_input: str, snowflake_handler: SnowflakeHandler) -> DataInsightAgentOutput:
    """
    Run the bob_the_dashboard_builder agent with the provided user input and database context.

    Args:
        user_input: The natural language question from the user.
        snowflake_handler: Connected SnowflakeHandler instance to use for database operations.

    Returns:
        DataInsightAgentOutput: The output from the agent containing visualizations and comments.
    """
    # Set the global snowflake_db to the passed handler instance
    global snowflake_db
    snowflake_db = snowflake_handler

    # Run the agent with the user input
    response = await Runner.run(bob_the_dashboard_builder,user_input)

    return response.final_output

import streamlit as st
import asyncio
from st_utils import *
from snowflake_utils import SnowflakeHandler
import pandas as pd
from PIL import Image
import io
from decimal import Decimal

from ai_agents.sql_dashboard_agents import run_sql_dashboard_agents
from ai_agents.chart_generator_agents import  run_chart_generator_agents


st.title(":snowflake: :blue[SnowGPT:] Your AI-Powered SQL Assistant")

st.markdown("#### A smart assistant that queries your Snowflake data using natural language")

# password = st.text_input("Enter password to use SnowGPT", type="password")
# if password != st.secrets["APP_PW"]:
#     st.stop()

########################################################################################################
###########                               INIT                              ############################
########################################################################################################

# --------------- CHAT HISTORY --------------- #
# Initialize the chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# --------------- CHAT AVATARS --------------- #
user_avatar = Image.open("images/julien.png")
assistant_avatar = Image.open("images/snowgpt.png")

# --------------- SNOWFLAKE CONNECTION --------------- #
snowflake_db = SnowflakeHandler(
    user=st.secrets["SNOWFLAKE_USER"],
    password=st.secrets["SNOWFLAKE_PASSWORD"],
    account=st.secrets["SNOWFLAKE_ACCOUNT"],
    warehouse=st.secrets["SNOWFLAKE_WAREHOUSE"],
    database="SNOWFLAKE",
    schema=None
)

snowflake_db.connect()

selected_db = st.selectbox(
            "__Which database do you want to use?__",
            "SANDBOX",
            index=0,
            placeholder="Select database...",
        )

snowflake_db.database = selected_db

selected_schema = st.selectbox(
            "__Which schema do you want to use?__",
            "SUPERSTORE",
            index=0,
            placeholder="Select schema...",
        )

# Close the previous connection before changing database/schema
snowflake_db.close_connection()

# Update the database and schema in the SnowflakeHandler
snowflake_db.database = selected_db
snowflake_db.schema = selected_schema

# Reconnect to the Snowflake database with the selected database and schema
snowflake_db.connect()

run = st.selectbox(
    "Do you want to build the dashboard?",
    (False, True),
)

prompt = "Tell me about the sales"


from pydantic import BaseModel
from typing import List

class Visualization(BaseModel):
    visualization_name: str
    visualization_type: str
    caption: str
    sql_query: str

class DashboardFinalOutput(BaseModel):
    comment: str
    visualizations: List[Visualization]

import json

# If you have your JSON as a string:
json_str = """
{
  "comment": "Based on the 'SUPERSTORE_SALES' table, key sales metrics can be derived from the SALES field, supported by time, product, and geography dimensions.",
  "visualizations": [
        {
          "visualization_name": "Sales Trend Over Time",
          "visualization_type": "line_chart",
          "caption": "This visualization shows how total sales have trended over time, highlighting seasonality and growth patterns.",
          "sql_query": "SELECT ORDERDATE, SUM(SALES) AS TOTAL_SALES\\nFROM SUPERSTORE.SUPERSTORE_SALES\\nGROUP BY ORDERDATE\\nORDER BY ORDERDATE;"
        },
        {
          "visualization_name": "Sales by Category",
          "visualization_type": "bar_chart",
          "caption": "Compare total sales across product categories to identify top-performing categories.",
          "sql_query": "SELECT CATEGORY, SUM(SALES) AS TOTAL_SALES\\nFROM SUPERSTORE.SUPERSTORE_SALES\\nGROUP BY CATEGORY\\nORDER BY TOTAL_SALES DESC;"
        },
        {
          "visualization_name": "Top 10 States by Sales",
          "visualization_type": "bar_chart",
          "caption": "Highlight the top 10 states by total sales to see regional performance leaders.",
          "sql_query": "SELECT STATE, SUM(SALES) AS TOTAL_SALES\\nFROM SUPERSTORE.SUPERSTORE_SALES\\nGROUP BY STATE\\nORDER BY TOTAL_SALES DESC\\nLIMIT 10;"
        },
        {
          "visualization_name": "Sales by Customer Segment",
          "visualization_type": "bar_chart",
          "caption": "Break down sales by customer segment to understand which segment contributes most to revenue.",
          "sql_query": "SELECT SEGMENT, SUM(SALES) AS TOTAL_SALES\\nFROM SUPERSTORE.SUPERSTORE_SALES\\nGROUP BY SEGMENT\\nORDER BY TOTAL_SALES DESC;"
        },
        {
          "visualization_name": "Relationship Between Discount and Profit",
          "visualization_type": "scatter_chart",
          "caption": "Visualize how discount rates relate to profitability, helping assess the impact of discounting strategies.",
          "sql_query": "SELECT DISCOUNT, PROFIT\\nFROM SUPERSTORE.SUPERSTORE_SALES\\nWHERE DISCOUNT IS NOT NULL AND PROFIT IS NOT NULL;"
        }
  ]
}
"""

# Convert the JSON string to a Python dictionary
data = json.loads(json_str)

# Parse into your Pydantic model
dashboard = DashboardFinalOutput(**data)










if run == True:
      with st.spinner("Executing SQL query..."):
            # response = asyncio.run(run_sql_dashboard_agents(prompt,selected_db,selected_schema))
            response = dashboard

      with st.expander("Tables", expanded=True, icon=None):
            for viz in response.visualizations:
                  st.title(viz.visualization_name)
                  st.write(viz.visualization_type)
                  st.caption(viz.caption)
                  df = snowflake_db.execute_query_df(viz.sql_query)
                  # st.dataframe(snowflake_db.execute_query_df(viz.sql_query))

                  if not df.empty:
                        for col in df.columns:
                              if isinstance(df[col].iloc[0], Decimal):
                                    df[col] = df[col].astype(float)

                  st.dataframe(df)
                  with st.popover("Show SQL query",use_container_width=False):
                        st.code(viz.sql_query, language="sql")

                  buffer = io.StringIO()
                  df.info(buf=buffer)
                  df_info_str = buffer.getvalue()

                  with st.spinner("Generating chart..."):
                        chart = asyncio.run(run_chart_generator_agents(prompt,df_info_str))
                  
                  try:
                        exec(chart.code_block)
                        with st.popover("Show chart code",use_container_width=False):
                              st.code(chart.code_block, language="python")
                  except Exception as e:
                        print("❌ Chart error:", e)
                        print(chart.code_block)


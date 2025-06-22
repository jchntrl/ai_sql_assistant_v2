import streamlit as st
import asyncio
from st_utils import *
from snowflake_utils import SnowflakeHandler
import pandas as pd
from PIL import Image
import io
from streamlit_ace import st_ace
import time
import os



from agents import Agent, Runner, function_tool, trace, handoff

from ai_agents.bob_the_dashboard_builder import run_bob_the_dashboard_builder

st.set_page_config(
    # layout="wide",
    initial_sidebar_state="collapsed",
    )

st.title("👷‍♂️🛠️📊 :yellow[BobGPT:] Your AI-Powered SQL Assistant")

st.markdown("#### A smart assistant that queries your Snowflake data using natural language")


# password = st.text_input("Enter password to use SnowGPT", type="password")
# if password != st.secrets["APP_PW"]:
#     st.stop()

########################################################################################################
###########                               INIT                              ############################
########################################################################################################

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
            list([db[0] for db in snowflake_db.get_databases()]),
            # ["SANDBOX"],
            index=0,
            placeholder="Select database...",
        )

snowflake_db.database = selected_db

selected_schema = st.selectbox(
            "__Which schema do you want to use?__",
            list([schema[0] for schema in snowflake_db.get_schemas() if not schema[0].startswith("INFORMATION_SCHEMA")]),
            # ["SUPERSTORE"],
            index=0,
            placeholder="Select schema...",
        )

# Close the previous connection before changing database/schema
snowflake_db.close_connection()

# Check if database or schema has changed and reset session state if needed
if 'current_db' not in st.session_state:
    st.session_state.current_db = None
if 'current_schema' not in st.session_state:
    st.session_state.current_schema = None

# Reset session state if database or schema changed
if (st.session_state.current_db != selected_db or 
    st.session_state.current_schema != selected_schema):
    
    # Update current context tracking
    st.session_state.current_db = selected_db
    st.session_state.current_schema = selected_schema
    

# Update the database and schema in the SnowflakeHandler
snowflake_db.database = selected_db
snowflake_db.schema = selected_schema

# Reconnect to the Snowflake database with the selected database and schema
snowflake_db.connect()


# --------------- CHAT HISTORY --------------- #
# Initialize the chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# --------------- CHAT AVATARS --------------- #
user_avatar = Image.open("images/julien.png")
assistant_avatar = Image.open("images/snowgpt.png")


########################################################################################################
###########                         MAIN VIEW                               ############################
########################################################################################################

with st.chat_message("assistant",avatar=assistant_avatar):
    st.markdown(f"Hello boss, what can I do for you? I can answer questions about your {selected_db} database and I can even create an **entire dahsboard** if you say please!")
    st.markdown(f"Just FYI, like Dory in *Finding Nemo* I don't have any memory! :fish:")
    
    on = st.toggle("Force validator agent to review generated SQL queries")
    if on:
        force_validator_agent = True
    else: 
        force_validator_agent = False


########### Display chat message from history on app rerun ###########
for message in st.session_state.messages:
    ############ User message ############
    if message["role"] == "user":
        with st.chat_message(message["role"],avatar=user_avatar):
            st.markdown(message["msg"])

    ############ Chatbot message ############
    if message["role"] == "assistant":
        with st.chat_message(message["role"],avatar=assistant_avatar):
            if message["message"]: 
                st.write(message["message"])
            else:

                visualizations = message["visualizations"]
                num_viz = len(visualizations)
                if num_viz >= 2:
                        # First row (first 2 visualizations)
                        cols = st.columns(2)
                        for i in range(min(2, num_viz)):
                            with cols[i]:
                                render_visualization_bob(visualizations[i], snowflake_db)

                if num_viz >= 4:
                    # Second row (next 2 visualizations)
                    cols = st.columns(2)
                    for i in range(2, min(4, num_viz)):
                        with cols[i - 2]:
                            render_visualization_bob(visualizations[i], snowflake_db)

                if num_viz >= 5:
                    # Third row (the last visualization, full width)
                    render_visualization_bob(visualizations[4], snowflake_db)
                elif num_viz == 1:
                    # Single visualization, full width
                    render_visualization_bob(visualizations[0], snowflake_db)
                elif 2 < num_viz < 4:
                    # Handle 3 visualizations
                    render_visualization_bob(visualizations[2], snowflake_db)


########### React to user input ###########
if user_input := st.chat_input(key="Initial request"):
    
    # Display user message in chat container
    with st.chat_message("user",avatar=user_avatar):
        st.markdown(user_input)
    # Add user message to chat history
    st.session_state.messages.append({"role":"user","msg":user_input})

    # Display assistant response in chat message container
    with st.chat_message("assistant",avatar=assistant_avatar):

        with trace("Streamlit Bob the dashboard builder"):
            
            with st.spinner("Generating dashboard ...", show_time=True):
                # Log dashboard agent execution
                response = asyncio.run(run_bob_the_dashboard_builder(user_input, snowflake_db))

            if not response.sufficient_context: 
                st.write(response.comment)
                st.session_state.messages.append({"role": "assistant",
                                "agent": 'dashboard_agent',
                                "message": response.comment
                                })

            else:

                visualizations = response.visualizations
                num_viz = len(visualizations)
                
                if num_viz >= 2:
                    # First row (first 2 visualizations)
                    cols = st.columns(2)
                    for i in range(min(2, num_viz)):
                        with cols[i]:
                            render_visualization_bob(visualizations[i], snowflake_db)

                if num_viz >= 4:
                    # Second row (next 2 visualizations)
                    cols = st.columns(2)
                    for i in range(2, min(4, num_viz)):
                        with cols[i - 2]:
                            render_visualization_bob(visualizations[i], snowflake_db)

                if num_viz >= 5:
                    # Third row (the last visualization, full width)
                    render_visualization_bob(visualizations[4], snowflake_db)
                elif num_viz == 1:
                    # Single visualization, full width
                    render_visualization_bob(visualizations[0], snowflake_db)
                elif 2 < num_viz < 4:
                    # Handle 3 visualizations
                    render_visualization_bob(visualizations[2], snowflake_db)

                st.session_state.messages.append({"role": "assistant",
                                "agent": 'dashboard_agent',
                                "message": None,
                                "visualizations": visualizations,
                                })


# Clear the chat history
if st.session_state.messages:
    st.button("Clear chat history", on_click=clear_chat_history)

########################################################################################################
###########                           SIDE BAR                              ############################
########################################################################################################

with st.sidebar:
    st.title("SQL Query Editor")
    st.write(f"When referencing table use {snowflake_db.schema}.<table_name>")

    col1, col2 = st.columns(2)

    with col1:
        with st.popover(f"# Table list", icon="📋",use_container_width=True):
            st.write(snowflake_db.get_tables())

    with col2:
        with st.popover(f"# Table definition", icon="📋",use_container_width=True):
            st.write(snowflake_db.get_all_columns())

    content = st_ace(
        placeholder="Test your SQL query here",
        language="sql",
        # theme="sqlserver",
        theme="iplastic",
        font_size=14,
        tab_size=4,
        wrap=True,
        show_gutter=True,
        min_lines=10,
        key="ace",
    )

    # st.write(content)

    ### Add some logic to clear content on App rerun
    if content:
        try: 
            df = snowflake_db.execute_query_df(content)
            df = convert_decimals_to_float(df)
            st.dataframe(df)

        except Exception as e:
            print("❌ Snowflake error:", e)
            print(f"QUERY: \n {content}")
            st.error(df)

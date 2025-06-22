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

# Ensure logging is set up before importing logger
from logging_config import setup_logging, get_logger

# Initialize logging for the app
logger = setup_logging(
    log_level="INFO",
    log_file="logs/snowgpt.log",
    enable_console=True
)

from agents import Agent, Runner, function_tool, trace, handoff

from ai_agents.routing_agent import  run_routing_agent, routing_agent
from ai_agents.sql_query_agents import run_sql_query_agents
from ai_agents.chart_generator_agents import  run_chart_generator_agents
from ai_agents.sql_dashboard_agents import run_sql_dashboard_agents

st.set_page_config(
    layout="wide",
    initial_sidebar_state="collapsed",
    )

# Test logging setup
logger.info("Logging system fully configured and ready")

# Log app startup
logger.info("SnowGPT application started", extra={
    'app_startup': True,
    'session_id': st.session_state.get('session_id', 'unknown')
})

st.title(":snowflake: :blue[SnowGPT:] Your AI-Powered SQL Assistant")

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
    
    # Log the context change
    logger.info("Database/Schema context changed", extra={
        'previous_db': st.session_state.current_db,
        'new_db': selected_db,
        'previous_schema': st.session_state.current_schema,
        'new_schema': selected_schema
    })
    
    # Clear relevant session state
    keys_to_clear = ['messages', 'router_counter', 'handoff', 'routing', 'user_input_history']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # Update current context tracking
    st.session_state.current_db = selected_db
    st.session_state.current_schema = selected_schema
    
    logger.info("Session state reset due to context change")

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

        if message["agent"] == "routing_agent":
            with st.chat_message(message["role"],avatar=assistant_avatar):
                st.markdown(message["msg"])

        if message["agent"] == "sql_query_agent":
            with st.chat_message(message["role"],avatar=assistant_avatar):
                st.markdown(message["msg"])
                if not message["table"].empty:
                    df = message["table"]
                    st.dataframe(df)
                    with st.popover("Show SQL query",use_container_width=False):
                            st.code(message["query"], language="sql")
                    try:
                        if message["chart"] != "":
                            exec(message["chart"])
                            with st.popover("Show chart code",use_container_width=False):
                                st.code(message["chart"], language="python")
                    except Exception as e:
                        print("❌ Chart error:", e)
                        print(message["chart"])

        if message["agent"] == "dashboard_agent":
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
                                    render_visualization(visualizations[i], snowflake_db)

                    if num_viz >= 4:
                        # Second row (next 2 visualizations)
                        cols = st.columns(2)
                        for i in range(2, min(4, num_viz)):
                            with cols[i - 2]:
                                render_visualization(visualizations[i], snowflake_db)

                    if num_viz >= 5:
                        # Third row (the last visualization, full width)
                        render_visualization(visualizations[4], snowflake_db)
                    elif num_viz == 1:
                        # Single visualization, full width
                        render_visualization(visualizations[0], snowflake_db)
                    elif 2 < num_viz < 4:
                        # Handle 3 visualizations
                        render_visualization(visualizations[2], snowflake_db)


if "router_counter" not in st.session_state:
    st.session_state.router_counter = 0
if "handoff" not in st.session_state:
    st.session_state.handoff = 'user'
if "routing" not in st.session_state:
    st.session_state.routing = None
if "user_input_history" not in st.session_state:
    st.session_state.user_input_history = []

########### React to user input ###########
if user_input := st.chat_input(key="Initial request"):
    # Log user input
    log_user_interaction("user_input", {
        'input_length': len(user_input),
        'router_counter': st.session_state.get('router_counter', 0),
        'handoff_state': st.session_state.get('handoff', 'user')
    })
    
    # Display user message in chat container
    with st.chat_message("user",avatar=user_avatar):
        st.markdown(user_input)
    # Add user message to chat history
    st.session_state.messages.append({"role":"user","msg":user_input})

    # Display assistant response in chat message container
    with st.chat_message("assistant",avatar=assistant_avatar):

        with trace("Streamlit SnowGPT"):

            if st.session_state.handoff == 'user':
                
                with st.spinner("Analizing request...", show_time=False):
                    print(st.session_state.handoff)
                    print(st.session_state.router_counter)
                    if st.session_state.handoff == 'user':
                        if st.session_state.router_counter == 0:

                            st.session_state.router_counter += 1
                            st.session_state.user_input_history.append(f"user: {user_input}")

                            # Log routing agent execution
                            routing_start = time.time()
                            routing = asyncio.run(run_routing_agent(user_input, selected_db, selected_schema))
                            routing_time = time.time() - routing_start
                            
                            log_agent_performance("routing_agent", routing_time, True, {
                                'handoff_decision': routing.handoff,
                                'router_counter': st.session_state.router_counter
                            })

                            if routing.handoff == 'user':
                                st.session_state.user_input_history.append(f"routing agent: {routing.questions_for_users}")
                                st.markdown(routing.questions_for_users)
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "agent": 'routing_agent',
                                    "msg": routing.questions_for_users
                                    })
                                st.rerun()
                            else:
                                st.session_state.handoff = routing.handoff
                                st.session_state.routing = routing
                                print(f"handoff -> {routing.handoff}")

                        else:
                            st.session_state.user_input_history.append(f"user: {user_input}")

                            user_input = "\n".join(str(msg) for msg in st.session_state.user_input_history)

                            print(user_input)

                            routing = asyncio.run(run_routing_agent(user_input, selected_db, selected_schema))

                            if routing.handoff == 'user':
                                st.session_state.user_input_history.append(f"routing agent: {routing.questions_for_users}")
                                st.markdown(routing.questions_for_users)
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "agent": 'routing_agent',
                                    "msg": routing.questions_for_users
                                    })
                                st.rerun()
                            else: 
                                st.session_state.handoff = routing.handoff
                                st.session_state.routing = routing
                                print(f"handoff -> {routing.handoff}")
                        
                            st.session_state.routing = routing
                            # st.session_state.router_counter += 1

            if st.session_state.handoff == 'sql_query_agent': 

                with st.spinner("Executing SQL query...", show_time=True):
                    # Log SQL query agent execution
                    sql_start = time.time()
                    query_agent = asyncio.run(run_sql_query_agents(st.session_state.routing.user_request,selected_db,selected_schema,force_validator_agent))
                    sql_time = time.time() - sql_start

                    message = query_agent.message
                    sql_query = query_agent.sql_query
                    
                    log_agent_performance("sql_query_agent", sql_time, sql_query != "", {
                        'sql_generated': sql_query != "",
                        'query_length': len(sql_query) if sql_query else 0,
                        'database': selected_db,
                        'schema': selected_schema
                    })

                st.write(message)

                if sql_query == "": 
                    chart = ""
                else:

                    df = snowflake_db.execute_query_df(sql_query)
                    df = convert_decimals_to_float(df)
                    st.dataframe(df)

                    with st.popover("Show SQL query",use_container_width=False):
                            st.code(sql_query, language="sql")

                    df_info_str = get_dataframe_info(df, include_sample=True)

                    with st.spinner("Generating chart...", show_time=True):
                        chart = asyncio.run(run_chart_generator_agents(user_input,df_info_str))

                    if chart.chart_needed:
                        try:
                            exec(chart.code_block)
                            with st.popover("Show chart code",use_container_width=False):
                                st.code(chart.code_block, language="python")
                        except Exception as e:
                            print("❌ Chart error:", e)
                            print(chart.code_block)

                st.session_state.messages.append({"role": "assistant",
                                "agent": 'sql_query_agent',
                                "msg": message,
                                "query": sql_query, 
                                "table": (df if sql_query != "" else None),
                                "chart": (chart.code_block if sql_query != "" else None)
                                })

                del st.session_state['router_counter']
                st.session_state.handoff = 'user'
                del st.session_state['routing']
                del st.session_state['user_input_history']
            
            if st.session_state.handoff == 'dashboard_agent': 

                with st.spinner("Generating dashboard ...", show_time=True):
                    # Log dashboard agent execution
                    dashboard_start = time.time()
                    response = asyncio.run(run_sql_dashboard_agents(st.session_state.routing.user_request,selected_db,selected_schema))
                    dashboard_time = time.time() - dashboard_start
                    
                    log_agent_performance("dashboard_agent", dashboard_time, len(response.visualizations) > 0, {
                        'visualizations_count': len(response.visualizations),
                        'database': selected_db,
                        'schema': selected_schema
                    })

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
                                render_visualization(visualizations[i], snowflake_db)

                    if num_viz >= 4:
                        # Second row (next 2 visualizations)
                        cols = st.columns(2)
                        for i in range(2, min(4, num_viz)):
                            with cols[i - 2]:
                                render_visualization(visualizations[i], snowflake_db)

                    if num_viz >= 5:
                        # Third row (the last visualization, full width)
                        render_visualization(visualizations[4], snowflake_db)
                    elif num_viz == 1:
                        # Single visualization, full width
                        render_visualization(visualizations[0], snowflake_db)
                    elif 2 < num_viz < 4:
                        # Handle 3 visualizations
                        render_visualization(visualizations[2], snowflake_db)

                    st.session_state.messages.append({"role": "assistant",
                                    "agent": 'dashboard_agent',
                                    "message": None,
                                    "visualizations": visualizations,
                                    })

                del st.session_state['router_counter']
                st.session_state.handoff = 'user'
                del st.session_state['routing']
                del st.session_state['user_input_history']


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

        on = st.toggle("Generate chart")

        if on:
            buffer = io.StringIO()
            df.info(buf=buffer)
            df_info_str = buffer.getvalue()

            with st.spinner("Generating chart...", show_time=True):
                chart = asyncio.run(run_chart_generator_agents(content,df_info_str))

            if chart.code_block == "":
                st.write(chart.message)
            else:
                try:
                    exec(chart.code_block)
                    with st.popover("Show chart code",use_container_width=False):
                        st.code(chart.code_block, language="python")
                except Exception as e:
                    print("❌ Chart error:", e)
                    print(chart.code_block)



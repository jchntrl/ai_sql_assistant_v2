import streamlit as st
from decimal import Decimal


def clear_chat_history(key="messages"):
    del st.session_state[key]


def convert_decimals_to_float(df):
    """Convert Decimal columns to float in a DataFrame."""
    if not df.empty:
        for col in df.columns:
            if isinstance(df[col].iloc[0], Decimal):
                df[col] = df[col].astype(float)
    return df


def render_visualization(viz, snowflake_db):
    """Render a single visualization with title, chart, and controls."""
    st.title(viz.visualization_name)
    st.write(viz.visualization_type)
    st.caption(viz.caption)
    
    df = snowflake_db.execute_query_df(viz.sql_query)
    df = convert_decimals_to_float(df)

    col1, col2, col3 = st.columns(3)
    with col1:
        with st.popover("Show table", use_container_width=True):
            st.dataframe(df)
    with col2:
        with st.popover("Show SQL query", use_container_width=True):
            st.code(viz.sql_query, language="sql")
    
    try:
        exec(viz.code_block)
        with col3:
            with st.popover("Show chart code", use_container_width=True):
                st.code(viz.code_block, language="python")
    except Exception as e:
        print("❌ Chart error:", e)
        print(viz.code_block)


import streamlit as st
from decimal import Decimal
import time
import functools
import logging
import io

# Get the already configured logger from the main app
logger = logging.getLogger("snowgpt")


def clear_chat_history(key="messages"):
    """Clear chat history from session state."""
    logger.info("Chat history cleared", extra={'action': 'clear_chat'})
    del st.session_state[key]


def convert_decimals_to_float(df):
    """Convert Decimal columns to float in a DataFrame."""
    start_time = time.time()
    decimal_cols = []
    
    if not df.empty:
        for col in df.columns:
            if isinstance(df[col].iloc[0], Decimal):
                df[col] = df[col].astype(float)
                decimal_cols.append(col)
    
    conversion_time = time.time() - start_time
    logger.debug("Decimal conversion completed", extra={
        'conversion_time': conversion_time,
        'decimal_columns': decimal_cols,
        'total_columns': len(df.columns) if not df.empty else 0
    })
    
    return df


def render_visualization(viz, snowflake_db):
    """Render a single visualization with title, chart, and controls."""
    start_time = time.time()
    
    logger.info("Starting visualization render", extra={
        'viz_name': viz.visualization_name,
        'viz_type': viz.visualization_type,
        'code_block': viz.code_block,
        'action': 'visualization_render_start'
    })
    
    st.title(viz.visualization_name)
    st.write(viz.caption)
    
    # Execute query and convert data
    query_start = time.time()
    df = snowflake_db.execute_query_df(viz.sql_query)
    query_time = time.time() - query_start
    
    df = convert_decimals_to_float(df)

    col1, col2, col3 = st.columns(3)
    with col1:
        with st.popover("Show table", use_container_width=True):
            st.dataframe(df)
    with col2:
        with st.popover("Show SQL query", use_container_width=True):
            st.code(viz.sql_query, language="sql")
    
    # Execute chart code
    chart_success = True
    try:
        exec(viz.code_block)
        with col3:
            with st.popover("Show chart code", use_container_width=True):
                st.code(viz.code_block, language="python")
    except Exception as e:
        chart_success = False
        logger.error("Chart execution failed", extra={
            'viz_name': viz.visualization_name,
            'viz_type': viz.visualization_type,
            'error': str(e),
            'code_block': viz.code_block,
            'action': 'chart_execution_failed'
        })
        print("❌ Chart error:", e)
        print(viz.code_block)
    
    total_time = time.time() - start_time
    logger.info("Visualization render completed", extra={
        'viz_name': viz.visualization_name,
        'viz_type': viz.visualization_type,
        'total_time': total_time,
        'query_time': query_time,
        'chart_success': chart_success,
        'rows_returned': len(df),
        'code_block': viz.code_block,
        'action': 'visualization_render_completed'
    })


def log_user_interaction(action: str, details: dict = None):
    """Log user interactions with additional context."""
    extra_data = {'action': action, 'user_interaction': True}
    if details:
        extra_data.update(details)
    logger.info(f"User interaction: {action}", extra=extra_data)


def log_agent_performance(agent_type: str, execution_time: float, success: bool, details: dict = None):
    """Log agent performance metrics."""
    extra_data = {
        'agent_type': agent_type,
        'execution_time': execution_time,
        'success': success,
        'agent_performance': True
    }
    if details:
        extra_data.update(details)
    
    level = "info" if success else "warning"
    getattr(logger, level)(f"Agent {agent_type} execution completed", extra=extra_data)


def performance_timer(func_name: str = None):
    """Decorator to time function execution and log performance."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            name = func_name or func.__name__
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.debug(f"Function {name} completed", extra={
                    'function_name': name,
                    'execution_time': execution_time,
                    'success': True
                })
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"Function {name} failed", extra={
                    'function_name': name,
                    'execution_time': execution_time,
                    'success': False,
                    'error': str(e)
                })
                raise
        return wrapper
    return decorator


def get_dataframe_info(df, include_sample=True, sample_rows=5):
    """
    Generate comprehensive DataFrame information including schema and sample data.
    
    Args:
        df: pandas DataFrame
        include_sample: Whether to include sample data (default: True)
        sample_rows: Number of sample rows to include (default: 5)
        
    Returns:
        str: Formatted string with DataFrame info and optional sample
    """
    logger.debug("Generating DataFrame info", extra={
        'rows': len(df),
        'columns': len(df.columns),
        'include_sample': include_sample
    })
    
    # Get DataFrame schema info
    buffer = io.StringIO()
    df.info(buf=buffer)
    df_info_str = buffer.getvalue()
    
    # Add sample data if requested
    if include_sample and not df.empty:
        df_info_str += f"\n## DataFrame Sample (first {sample_rows} rows)\n"
        df_info_str += df.head(sample_rows).to_markdown()
    
    return df_info_str


def render_visualization_bob(viz, snowflake_db):
    """Render a single visualization with title, chart, and controls."""
    start_time = time.time()
    
    logger.info("Starting visualization render", extra={
        'viz_name': viz.visualization_name,
        'viz_type': viz.visualization_type,
        'code_block': viz.chart_code,
        'action': 'visualization_render_start'
    })
    
    st.title(viz.visualization_name)
    st.write(viz.caption)
    
    # Execute query and convert data
    query_start = time.time()
    df = snowflake_db.execute_query_df(viz.sql_query)
    query_time = time.time() - query_start
    
    df = convert_decimals_to_float(df)

    col1, col2, col3 = st.columns(3)
    with col1:
        with st.popover("Show table", use_container_width=True):
            st.dataframe(df)
    with col2:
        with st.popover("Show SQL query", use_container_width=True):
            st.code(viz.sql_query, language="sql")
    
    # Execute chart code
    chart_success = True
    try:
        exec(viz.chart_code)
        with col3:
            with st.popover("Show chart code", use_container_width=True):
                st.code(viz.chart_code, language="python")
    except Exception as e:
        chart_success = False
        logger.error("Chart execution failed", extra={
            'viz_name': viz.visualization_name,
            'viz_type': viz.visualization_type,
            'error': str(e),
            'code_block': viz.chart_code,
            'action': 'chart_execution_failed'
        })
        print("❌ Chart error:", e)
        print(viz.chart_code)
    
    total_time = time.time() - start_time
    logger.info("Visualization render completed", extra={
        'viz_name': viz.visualization_name,
        'viz_type': viz.visualization_type,
        'total_time': total_time,
        'query_time': query_time,
        'chart_success': chart_success,
        'rows_returned': len(df),
        'code_block': viz.chart_code,
        'action': 'visualization_render_completed'
    })
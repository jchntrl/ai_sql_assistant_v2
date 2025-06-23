# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

SnowGPT is an AI-powered SQL assistant built with Streamlit that connects to Snowflake databases. It provides natural language to SQL conversion, automated chart generation, and comprehensive dashboard creation using OpenAI's API and specialized AI agents.

## Core Architecture

### Application Structure
- **app.py**: Main Streamlit application with chat interface and agent orchestration
- **bob_app.py**: Simplified version focused on dashboard generation
- **snowflake_utils.py**: Database connection and query management (SnowflakeHandler class)
- **st_utils.py**: Streamlit utilities for UI components and visualization rendering
- **logging_config.py**: Structured JSON logging configuration

### AI Agents (`ai_agents/`)
- **routing_agent.py**: Analyzes user requests and routes to appropriate specialized agents
- **sql_query_agents.py**: Generates and validates SQL queries from natural language
- **chart_generator_agents.py**: Creates visualization code from query results
- **sql_dashboard_agents.py**: Builds comprehensive multi-panel dashboards
- **bob_the_dashboard_builder.py**: Simplified dashboard builder for bob_app.py

### Key Technologies
- **Streamlit**: Web application framework
- **OpenAI Agents**: AI agent orchestration with function tools
- **Snowflake**: Cloud data warehouse connectivity
- **Pandas**: Data manipulation and analysis
- **Altair**: Primary visualization library

## Development Commands

### Running the Application
```bash
# Main application
streamlit run app.py

# Bob variant (simplified dashboard builder)
streamlit run bob_app.py

# Windows batch file
run_app.bat
```

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Create virtual environment (if using run_app.bat)
python -m venv venv
venv\Scripts\activate
```

### Configuration
Create `.streamlit/secrets.toml` with:
```toml
[secrets]
SNOWFLAKE_USER = "your_snowflake_username"
SNOWFLAKE_PASSWORD = "your_snowflake_password"
SNOWFLAKE_ACCOUNT = "your_snowflake_account"
SNOWFLAKE_WAREHOUSE = "your_warehouse_name"
OPENAI_API_KEY = "your_openai_api_key"
```

## Agent Workflow

### Request Processing Flow
1. **User Input**: Natural language query or request
2. **Routing Agent**: Analyzes intent and determines appropriate handler
3. **Specialized Agent**: Executes specific task (SQL generation, chart creation, dashboard building)
4. **Visualization**: Renders results with interactive components

### Agent Handoffs
- `routing_agent` → `sql_query_agent`: For single SQL queries
- `routing_agent` → `dashboard_agent`: For comprehensive dashboards (triggered by "please" keyword)
- `routing_agent` → `user`: For clarification questions

## Database Integration

### SnowflakeHandler Features
- Dynamic database/schema switching
- Connection pooling and error handling
- Schema introspection (tables, columns, data types)
- Query validation and execution
- Performance logging and monitoring

### Key Methods
- `connect()`: Establish database connection
- `execute_query_df()`: Execute SQL and return pandas DataFrame
- `get_tables()`: Retrieve table metadata
- `get_all_columns()`: Schema introspection
- `validate_query()`: SQL syntax validation
- `close_connection()`: Clean connection closure

## Session Management

### State Variables
- `messages`: Chat history
- `router_counter`: Request routing counter
- `handoff`: Current agent handoff state
- `routing`: Routing agent response
- `current_db`/`current_schema`: Context tracking

### Context Switching
Session state is automatically reset when database or schema changes to maintain data consistency.

## Logging and Monitoring

### Structured Logging
- JSON-formatted logs with performance metrics
- Agent execution timing and success tracking
- SQL query logging with execution details
- User interaction analytics

### Log Categories
- Database operations
- Agent performance
- User interactions
- Visualization rendering
- Error tracking

## Visualization Pipeline

### Chart Generation Process
1. SQL query execution
2. DataFrame analysis for chart suitability
3. Automatic chart type selection
4. Streamlit/Altair code generation
5. Interactive chart rendering with source code access

### Supported Chart Types
- Bar charts, line charts, scatter plots
- Multi-panel dashboards with adaptive layouts
- Interactive Streamlit visualizations

## Development Notes

### Testing SQL Queries
Use the sidebar SQL editor for direct query testing with:
- Live schema browser
- Syntax highlighting
- Optional chart generation toggle

### Error Handling
- Comprehensive error logging
- Graceful fallback for failed visualizations
- User-friendly error messages

### Performance Considerations
- Connection pooling for database efficiency
- Asynchronous agent execution
- Decimal to float conversion for visualization compatibility
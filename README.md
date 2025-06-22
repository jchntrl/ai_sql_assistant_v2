# SnowGPT: AI-Powered SQL Assistant

SnowGPT is an intelligent Streamlit application that serves as your AI-powered SQL assistant for Snowflake databases. It allows users to interact with their Snowflake data using natural language, automatically generating SQL queries, creating visualizations, and building comprehensive dashboards.

## Features

### 🤖 Intelligent Query Routing
- **Routing Agent**: Analyzes user requests and determines the best approach
- Asks clarifying questions when requests are ambiguous
- Routes to appropriate specialized agents based on user intent

### 📊 SQL Query Generation
- **Natural Language to SQL**: Convert plain English questions into optimized SQL queries
- **Query Validation**: Built-in SQL validation to ensure query correctness
- **Interactive Results**: View query results in formatted tables with export options

### 📈 Automated Visualization
- **Chart Generation**: Automatically creates appropriate visualizations based on query results
- **Multiple Chart Types**: Supports bar charts, line charts, scatter plots, and more
- **Interactive Charts**: Streamlit-powered interactive visualizations

### 🏗️ Dashboard Creation
- **Multi-Panel Dashboards**: Creates comprehensive dashboards with multiple visualizations
- **Adaptive Layout**: Automatically arranges visualizations in responsive grid layouts
- **Executive Summaries**: Provides contextual insights alongside visual data

### 🗄️ Database Management
- **Multi-Database Support**: Switch between different Snowflake databases and schemas
- **Schema Exploration**: Browse tables, columns, and data types
- **Live SQL Editor**: Built-in SQL editor with syntax highlighting and query execution

## Installation

### Prerequisites
- Python 3.8+
- Access to a Snowflake account
- Required API keys (OpenAI)

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd ai_sql_assistant_v2
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure Streamlit secrets**
Create a `.streamlit/secrets.toml` file with your credentials:
```toml
[secrets]
SNOWFLAKE_USER = "your_snowflake_username"
SNOWFLAKE_PASSWORD = "your_snowflake_password"
SNOWFLAKE_ACCOUNT = "your_snowflake_account"
SNOWFLAKE_WAREHOUSE = "your_warehouse_name"
OPENAI_API_KEY = "your_openai_api_key"
```

4. **Run the application**
```bash
streamlit run app.py
```

## Usage

### Getting Started
1. Launch the application and select your target database and schema
2. Choose between natural language queries or direct SQL editing
3. Ask questions in plain English or write SQL directly in the sidebar editor

### Natural Language Queries
- "Show me sales trends over the past year"
- "What are the top 10 customers by revenue?"
- "Create a dashboard showing product performance metrics"

### Dashboard Generation
- Request comprehensive dashboards by saying "please" in your query
- The system will generate multiple related visualizations
- Dashboards automatically adapt to your data structure

### SQL Editor
- Use the sidebar SQL editor for direct query execution
- View table schemas and column definitions
- Generate charts from SQL results with the toggle option

## Architecture

### Core Components

#### AI Agents
- **Routing Agent** (`ai_agents/routing_agent.py`): Analyzes and routes user requests
- **SQL Query Agent** (`ai_agents/sql_query_agents.py`): Generates and validates SQL queries
- **Chart Generator** (`ai_agents/chart_generator_agents.py`): Creates visualization code
- **Dashboard Agent** (`ai_agents/sql_dashboard_agents.py`): Builds comprehensive dashboards

#### Utilities
- **SnowflakeHandler** (`snowflake_utils.py`): Database connection and query management
- **Streamlit Utilities** (`st_utils.py`): UI components and visualization rendering
- **Logging Configuration** (`logging_config.py`): Structured logging for monitoring

#### Main Application
- **app.py**: Primary Streamlit application with chat interface and routing logic

### Key Technologies
- **Streamlit**: Web application framework
- **OpenAI GPT-4**: Natural language processing and code generation
- **Snowflake**: Cloud data warehouse platform
- **Pandas**: Data manipulation and analysis
- **Altair**: Data visualization libraries

## Configuration

### Environment Variables
The application supports the following configuration options:

- `SNOWFLAKE_USER`: Your Snowflake username
- `SNOWFLAKE_PASSWORD`: Your Snowflake password
- `SNOWFLAKE_ACCOUNT`: Your Snowflake account identifier
- `SNOWFLAKE_WAREHOUSE`: Default warehouse for computations
- `OPENAI_API_KEY`: OpenAI API key for AI functionality

### Logging
Comprehensive logging is configured through `logging_config.py`:
- Application events and performance metrics
- SQL query execution tracking
- Agent performance monitoring
- Error tracking and debugging

## Features in Detail

### Chat Interface
- Persistent chat history within sessions
- Context-aware conversations
- Session state management for database/schema changes

### Query Processing
1. **Input Analysis**: Routing agent determines user intent
2. **Context Gathering**: Retrieves relevant database schema information
3. **SQL Generation**: Creates optimized queries based on natural language
4. **Validation**: Ensures query syntax and logic correctness
5. **Execution**: Runs queries against Snowflake with performance tracking

### Visualization Pipeline
1. **Data Analysis**: Examines query results for chart suitability
2. **Chart Selection**: Chooses appropriate visualization types
3. **Code Generation**: Creates executable Streamlit/Python visualization code
4. **Rendering**: Displays interactive charts with source code access

## Development

### Project Structure
```
ai_sql_assistant_v2/
├── ai_agents/           # AI agent implementations
├── images/             # Application assets
├── logs/              # Application logs
├── app.py             # Main Streamlit application
├── snowflake_utils.py # Database utilities
├── st_utils.py        # Streamlit utilities
├── logging_config.py  # Logging configuration
└── requirements.txt   # Python dependencies
```

### Extending the Application
- Add new agents in the `ai_agents/` directory
- Implement new visualization types in the chart generator
- Extend database support by modifying `snowflake_utils.py`
- Add new UI components in `st_utils.py`

## Performance and Monitoring

### Built-in Metrics
- SQL query execution times
- Agent processing durations
- Visualization rendering performance
- Database connection monitoring

### Logging Features
- Structured JSON logging
- Performance metrics tracking
- User interaction analytics
- Error reporting and debugging

## Troubleshooting

### Common Issues
1. **Connection Errors**: Verify Snowflake credentials and network connectivity
2. **API Limits**: Check OpenAI API usage and rate limits
3. **Query Failures**: Review SQL syntax and table permissions
4. **Visualization Errors**: Check data types and chart compatibility

### Debug Mode
Enable detailed logging by setting the log level to DEBUG in `logging_config.py`.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

For support and questions:
- Review the logs in the `logs/` directory
- Check the Streamlit console for real-time debugging
- Verify database connectivity and permissions
- Monitor Agents tool calls https://platform.openai.com/traces 
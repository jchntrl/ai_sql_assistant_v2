
# Outline


1. Quick Agent intro (Agent = LLM + tools)
2. Agents Frameworks
    - Mention the most popular ones (LangChain, CrewAI)
    - Mention ETL like Agents builder tools (LangFlow, n8n, Make)
    - Expend a bit on OpenAI's Agent SDK (the one I'll use for the demo)
3. Agents created for my Streamlit App
    - Triage Agent (decide if need to handoff to Query Agent or Dashboard Agent based on user's input)
    - SQL Query Agents -> Demo the agent directly from command-line
    - Chart Agent
    - Dashboard Agent
4. Debugging / Agents decisions tracing
5. Integration of my Agents with Streamlit 
    - Calling agents -> st.spinner + asyncio
    - Saving objects state ->  st.session_state.messages
5. Mention how MCP would be a better way to build the app back-end
    - Reusability in "Chat" app like Claud Desktop or Ollama
    - May be show LangFlow MCP example (if time allow)

# Datasets 
## 1 table
- Superstore

## A few tables
- IMDB
- GLOBAL_WEATHER__CLIMATE_DATA_FOR_BI.STANDARD_TILE
    - Copy over to `SANDBOX` 
    - Add ZIP_CODE table
- Another Sale Analysis example ???

## A lot of tables
- COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC
    - Show how we can run out of tokens if we send the definitions of all the tables to the Agents
        - That's why I provide 1. the list of table, 2. a tool to get the definition of the tables he's interested in

# MCP example (LangFlow)
- Generate a simple MCP server
    - Retrieve list of people + certs they have (Anonymize the names)
- Or Notion Example
- Demonstrate how we can use it in OpenWeb-UI and Claude Desktop 

LangFlow MCP -> Ollama -> OpenWebUI
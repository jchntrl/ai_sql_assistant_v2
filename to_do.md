# To Do List: 

## High priority 
- Add message history
- Create Read-only role for Snowflake
- Modify the `chart_generator_agent` so it work of a SQL query but know the data will be actually stored in a Pandas DataFrame and the decimals will be converted to 
- Test XML prompts
- for `get_table` modify the input class for the ai by List[TableName] and create `TableName`
- Add possibility to save dashboards
- Add possibility to save dashboard as an image

## Medium priority
- Add @function_tool to let the ai retrieve distinct values from table ```sql SELECT DISTINCT <field> from <schema_name>.<table_name>```
- Modify the `chart_generator_agent` so it work of a SQL query but know the data will be actually stored in a Pandas DataFrame

## Low Priority 
- Refactor sql_query_agents
- Refactor app.py -> sql_query_agent logic
    - Add spinner for each steps 
- Unify Agents final output class and its use (`response`) in app.py
- Clean SnowflakeHandler and separate clearly functions between those that return test, markdown table and dataframe
- Place `snowflake_utils` and `st_utils` into a subfolder named `utils`
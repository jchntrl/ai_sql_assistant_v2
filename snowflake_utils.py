import asyncio
import snowflake.connector
import streamlit as st
from typing import Optional, List, Tuple, Any
import time
import logging

# Get the already configured logger from the main app
logger = logging.getLogger("snowgpt")



class SnowflakeHandler:
    def __init__(self, user: str, password: str, account: str, warehouse: str, database: str, schema: str) -> None:
        """
        Initialize the SnowflakeHandler with connection parameters.
        
        Args:
            user: Snowflake username
            password: Snowflake password
            account: Snowflake account identifier
            warehouse: Snowflake warehouse name
            database: Initial database name (can be changed later)
            schema: Initial schema name (can be changed later)
        """
        self.user: str = user
        self.password: str = password
        self.account: str = account
        self.warehouse: str = warehouse
        self.database: str = database
        self.schema: str = schema
        self.connection: None = None

    def connect(self) -> None:
        """
        Establish a connection to Snowflake using the configured parameters.
        
        Raises:
            Exception: If connection fails due to invalid credentials or network issues
        """
        start_time = time.time()
        
        logger.info("Attempting Snowflake connection", extra={
            'account': self.account,
            'warehouse': self.warehouse,
            'database': self.database,
            'schema': self.schema
        })
        
        try:
            self.connection = snowflake.connector.connect(
                user=self.user,
                password=self.password,
                account=self.account,
                warehouse=self.warehouse,
                database=self.database,
                schema=self.schema
            )
            connection_time = time.time() - start_time
            
            logger.info("Snowflake connection established", extra={
                'connection_time': connection_time,
                'account': self.account,
                'database': self.database,
                'schema': self.schema
            })
            
            print(f"Connected to Snowflake ({self.database}.{self.schema}).")
            
        except Exception as e:
            connection_time = time.time() - start_time
            logger.error("Snowflake connection failed", extra={
                'connection_time': connection_time,
                'error': str(e),
                'account': self.account
            })
            raise

    def get_databases(self) -> List[str]:
        """
        Retrieve all available databases from Snowflake.
        
        Returns:
            List[str]: List of tuples containing database names
            
        Raises:
            Exception: If no connection is established or query fails
        """

        query = f"SELECT DATABASE_NAME FROM {self.database}.INFORMATION_SCHEMA.DATABASES ORDER BY 1 ASC"

        if not self.connection:
            raise Exception("Connection not established. Call connect() first.")
        
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            print("❌ Snowflake error:", e)
            print(f"QUERY: \n {query}")
            print(query)
            return "❌ Query is invalid \n" + str(e)
        finally:
            cursor.close()

    def get_schemas(self) -> List[str]:
        """
        Retrieve all available schemas from the current database.
        
        Returns:
            List[str]: List of tuples containing schema names
            
        Raises:
            Exception: If no connection is established or query fails
        """

        query = f"SELECT SCHEMA_NAME FROM {self.database}.INFORMATION_SCHEMA.SCHEMATA ORDER BY 1 ASC"

        if not self.connection:
            raise Exception("Connection not established. Call connect() first.")
        
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            print("❌ Snowflake error:", e)
            print(f"QUERY: \n {query}")
            print(query)
            return "❌ Query is invalid \n" + str(e)
        finally:
            cursor.close()

    def get_tables(self) -> str:
        """
        Retrieve all tables from the current schema with metadata.
        
        Returns:
            str: Table information (schema, name, type, row count) formatted as markdown table
            
        Raises:
            Exception: If no connection is established or query fails
        """

        query = f"SELECT TABLE_SCHEMA,TABLE_NAME,TABLE_TYPE,ROW_COUNT FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{self.schema}'"

        if not self.connection:
            raise Exception("Connection not established. Call connect() first.")
        
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            return cursor.fetch_pandas_all().to_markdown()
        except Exception as e:
            print("❌ Snowflake error:", e)
            print(f"QUERY: \n {query}")
            print(query)
            return "❌ Query is invalid \n" + str(e)
        finally:
            cursor.close()

    def get_all_columns(self,) -> str:
        """
        Query INFORMATION_SCHEMA.TABLES and return the columns' definition for a Schema.
        :return: markdown table as str.
        """

        query = f"""SELECT TABLE_SCHEMA,TABLE_NAME,COLUMN_NAME,ORDINAL_POSITION,COLUMN_DEFAULT,IS_NULLABLE,DATA_TYPE,CHARACTER_MAXIMUM_LENGTH,CHARACTER_OCTET_LENGTH,NUMERIC_PRECISION,NUMERIC_PRECISION_RADIX,NUMERIC_SCALE,DATETIME_PRECISION,IS_IDENTITY,COMMENT
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = '{self.schema}'
        ORDER BY TABLE_SCHEMA,TABLE_NAME,ORDINAL_POSITION
        """

        if not self.connection:
            raise Exception("Connection not established. Call connect() first.")
        
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            return cursor.fetch_pandas_all().to_markdown()
        except Exception as e:
            print("❌ Snowflake error:", e)
            print(f"QUERY: \n {query}")
            print(query)
            return "❌ Query is invalid \n" + str(e)
        finally:
            cursor.close()

    def get_table_columns(self, table: str) -> str:
        """
        Query INFORMATION_SCHEMA.TABLES and return the columns' definition for a table/view.
        :return: markdown table as str.
        """

        query = f"""SELECT TABLE_SCHEMA, TABLE_SCHEMA,TABLE_NAME,COLUMN_NAME,ORDINAL_POSITION,COLUMN_DEFAULT,IS_NULLABLE,DATA_TYPE,CHARACTER_MAXIMUM_LENGTH,CHARACTER_OCTET_LENGTH,NUMERIC_PRECISION,NUMERIC_PRECISION_RADIX,NUMERIC_SCALE,DATETIME_PRECISION,IS_IDENTITY,COMMENT
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = '{self.schema}' AND TABLE_NAME = '{table}'
        ORDER BY TABLE_SCHEMA,TABLE_NAME,ORDINAL_POSITION
        """

        if not self.connection:
            raise Exception("Connection not established. Call connect() first.")
        
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            return cursor.fetch_pandas_all().to_markdown()
        except Exception as e:
            print("❌ Snowflake error:", e)
            print(f"QUERY: \n {query}")
            print(query)
            return "❌ Query is invalid \n" + str(e)
        finally:
            cursor.close()

    def get_table_list_columns(self, table_list: List) -> str:
        """
        Query INFORMATION_SCHEMA.TABLES and return the columns' definition for a table/view.
        :param table_list: List of tables to retrieve sample for.
        :return: markdown table as str.
        """

        if not self.connection:
            raise Exception("Connection not established. Call connect() first.")
        
        output = "# Table definitions\n\n"

        for table in table_list: 

            query = f"""SELECT TABLE_SCHEMA,TABLE_NAME,COLUMN_NAME,ORDINAL_POSITION,COLUMN_DEFAULT,IS_NULLABLE,DATA_TYPE,CHARACTER_MAXIMUM_LENGTH,CHARACTER_OCTET_LENGTH,NUMERIC_PRECISION,NUMERIC_PRECISION_RADIX,NUMERIC_SCALE,DATETIME_PRECISION,IS_IDENTITY,COMMENT
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = '{self.schema}' AND TABLE_NAME = '{table}'
            ORDER BY TABLE_SCHEMA,TABLE_NAME,ORDINAL_POSITION
            """

            cursor = self.connection.cursor()
            try:
                cursor.execute(query)
                output += f"\n ## {self.schema}.{table}\n{cursor.fetch_pandas_all().to_markdown()}"
            except Exception as e:
                print("❌ Snowflake error:", e)
                print(f"QUERY: \n {query}")
                print(query)
                return "❌ Query is invalid \n" + str(e)
            finally:
                cursor.close()
            
        return output

    def execute_query_df(self, query: str):
        """
        Execute a SQL query and return results as a pandas DataFrame.
        
        Args:
            query: SQL query string to execute
            
        Returns:
            pandas.DataFrame: Query results as DataFrame, or error string if query fails
            
        Raises:
            Exception: If no connection is established
        """
        start_time = time.time()
        
        logger.info("Executing SQL query", extra={
            'query_length': len(query),
            'database': self.database,
            'schema': self.schema
        })
        
        if not self.connection:
            logger.error("Connection not established")
            raise Exception("Connection not established. Call connect() first.")
        
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            result = cursor.fetch_pandas_all()
            execution_time = time.time() - start_time
            
            logger.info("SQL query executed successfully", extra={
                'execution_time': execution_time,
                'rows_returned': len(result),
                'columns_returned': len(result.columns) if not result.empty else 0,
                'query_hash': hash(query) % 10000  # Simple hash for query identification
            })
            
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error("SQL query execution failed", extra={
                'execution_time': execution_time,
                'error': str(e),
                'query': query[:500] + "..." if len(query) > 500 else query  # Truncate long queries
            })
            print("❌ Snowflake error:", e)
            print(f"QUERY: \n {query}")
            print(query)
            return f"❌ Query execution failed \n{str(e)}\n{query}"
        finally:
            cursor.close()


    def get_tables_sample_md(self, table_list: str) -> str:
        """
        Execute a SQL query and return 5 rows.
        :param query: SQL query string to execute.
        :return: Markdown tables.
        """
        if not self.connection:
            raise Exception("Connection not established. Call connect() first.")
        
        output = "# Tables samples\n\n"

        for table in table_list: 

            query = f"SELECT * FROM {table} LIMIT 5"

            cursor = self.connection.cursor()
            try:
                cursor.execute(query)
                output += f"\n ## {self.schema}.{table}\n{cursor.fetch_pandas_all().to_markdown()}"
            except Exception as e:
                print("❌ Snowflake error:", e)
                print(f"QUERY: \n {query}")
                print(query)
                return "❌ Query is invalid \n" + str(e)
            finally:
                cursor.close()
            
        return output

    def get_tables_info_md(self, table_list: str) -> str:
        """
        Retrieve the columns definition and a 5 rows sample.
        :param table_list: SQL query string to execute.
        :return: Markdown tables.
        """
        if not self.connection:
            raise Exception("Connection not established. Call connect() first.")
        
        output = "# Tables information\n"

        for table in table_list: 

            output += f"\n## {self.schema}.{table}\n"

            query_definition = f"""SELECT COLUMN_NAME,ORDINAL_POSITION,COLUMN_DEFAULT,IS_NULLABLE,DATA_TYPE,CHARACTER_MAXIMUM_LENGTH,CHARACTER_OCTET_LENGTH,NUMERIC_PRECISION,NUMERIC_PRECISION_RADIX,NUMERIC_SCALE,DATETIME_PRECISION,IS_IDENTITY,COMMENT
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = '{self.schema}' AND TABLE_NAME = '{table}'
            ORDER BY TABLE_SCHEMA,TABLE_NAME,ORDINAL_POSITION
            """

            cursor = self.connection.cursor()
            try:
                cursor.execute(query_definition)
                output += "\n### Definition\n"
                output += f"{cursor.fetch_pandas_all().to_markdown()}\n"
            except Exception as e:
                print("❌ Snowflake error:", e)
                print(f"QUERY: \n {query_definition}")
                print(query_definition)
                return "❌ Query is invalid \n" + str(e)
            finally:
                cursor.close()

            
            query_sample = f"SELECT * FROM {table} LIMIT 5"

            cursor = self.connection.cursor()
            try:
                cursor.execute(query_sample)
                output += "\n### Sample\n"
                output += f"{cursor.fetch_pandas_all().to_markdown()}\n"
            except Exception as e:
                print("❌ Snowflake error:", e)
                print(f"QUERY: \n {query_sample}")
                print(query_sample)
                return "❌ Query is invalid \n" + str(e)
            finally:
                cursor.close()
            
        return output

    def execute_query_md(self, query: str) -> str:
        """
        Execute a SQL query and return results formatted as markdown table.
        
        Args:
            query: SQL query string to execute
            
        Returns:
            str: Query results formatted as markdown table, or error message if query fails
            
        Raises:
            Exception: If no connection is established
        """
        if not self.connection:
            raise Exception("Connection not established. Call connect() first.")
        
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            return cursor.fetch_pandas_all().to_markdown()
        except Exception as e:
            print("❌ Snowflake error:", e)
            print(f"QUERY: \n {query}")
            print(query)
            return f"❌ Query execution failed \n{str(e)}\n{query}"
        finally:
            cursor.close()

    def get_distinct_values_dict(self, field: str, table: str, filter: str ='', limit: str ='15') -> str:
        """
        Get distinct values for a specific field from a table.
        
        Args:
            field: Column name to get distinct values for
            table: Table name to query
            filter: Optional WHERE clause filter (default: '')
            limit: Maximum number of results to return (default: '15')
            
        Returns:
            str: Distinct values formatted as markdown table, or error message if query fails
            
        Raises:
            Exception: If no connection is established
        """
        if not self.connection:
            raise Exception("Connection not established. Call connect() first.")
        
        query = f"SELECT DISTINCT {field} FROM {table} {'WHERE ' + filter if filter else ''} {'LIMIT ' + limit if limit else ''}"

        print(query)
        
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            return cursor.fetch_pandas_all().to_markdown()
        except Exception as e:
            print("❌ Snowflake error:", e)
            print(f"QUERY: \n {query}")
            print(query)
            return f"❌ Query execution failed \n{str(e)}\n{query}"
        finally:
            cursor.close()

    def get_distinct_values_from_table_list_dict(
        self, queries: List[dict], limit: str = '15') -> str:
        """
        Get distinct values for multiple field/table/filter combinations.
        
        Args:
            queries: List of dictionaries, each containing:
                - 'field': Column name to get distinct values for
                - 'table': Table name to query  
                - 'filter': Optional WHERE clause filter (default: '')
            limit: Maximum number of results to return per query (default: '15')
            
        Returns:
            str: Distinct values formatted as markdown with headers for each query
            
        Raises:
            Exception: If no connection is established
            
        Example:
            queries = [
                {'field': 'COUNTY', 'table': 'DEMOGRAPHICS', 'filter': "STATE = 'LA'"},
                {'field': 'CATEGORY', 'table': 'PRODUCTS', 'filter': ''},
                {'field': 'STATUS', 'table': 'ORDERS', 'filter': "YEAR = 2023"}
            ]
        """
        if not self.connection:
            raise Exception("Connection not established. Call connect() first.")
        
        output = "# Distinct Values Results\n\n"
        
        for i, query_spec in enumerate(queries, start=1):
            field = query_spec.get('field', '')
            table = query_spec.get('table', '')
            filter_clause = query_spec.get('filter', '')
            
            # Create descriptive header
            filter_desc = f" (filtered: {filter_clause})" if filter_clause else ""
            output += f"## {i}. {field} from {self.schema}.{table}{filter_desc}\n\n"
            
            # Build and execute query
            query = f"SELECT DISTINCT {field} FROM {table} {'WHERE ' + filter_clause if filter_clause else ''} {'LIMIT ' + limit if limit else ''}"
            
            print(f"Executing query {i}: {query}")
            
            cursor = self.connection.cursor()
            try:
                cursor.execute(query)
                result = cursor.fetch_pandas_all().to_markdown()
                output += f"{result}\n\n"
            except Exception as e:
                print(f"❌ Snowflake error for query {i}:", e)
                print(f"QUERY: \n {query}")
                output += f"❌ Query {i} failed: {str(e)}\n\n"
            finally:
                cursor.close()
        
        return output

    def execute_query_sample_md(self, query: str) -> str:
        """
        Execute a SQL query and return results as markdown with limited rows for sampling.
        
        Args:
            query: SQL query string to execute
            
        Returns:
            str: Query results formatted as markdown table, or error message if query fails
            
        Raises:
            Exception: If no connection is established
        """
        if not self.connection:
            raise Exception("Connection not established. Call connect() first.")
        
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            return cursor.fetch_pandas_all().to_markdown()
        except Exception as e:
            print("❌ Snowflake error:", e)
            print(f"QUERY: \n {query}")
            print(query)
            return f"❌ Query execution failed \n{str(e)}\n{query}"
        finally:
            cursor.close()

    def validate_query(self, query: str) -> str:
        """
        Validate SQL query syntax without executing it using EXPLAIN.
        
        Args:
            query: SQL query string to validate
            
        Returns:
            str: "✅ Query is valid." if syntax is correct, error message if invalid
            
        Raises:
            Exception: If no connection is established
        """
        if not self.connection:
            raise Exception("Connection not established. Call connect() first.")
        
        cursor = self.connection.cursor()
        try:
            cursor.execute(f"EXPLAIN {query}")
            return "✅ Query is valid."
        except Exception as e:
            print("❌ Snowflake error:", e)
            print(f"QUERY: \n {query}")
            print(query)
            return f"❌ Query is invalid \n{str(e)}\n{query}"
        finally:
            cursor.close()

    def close_connection(self) -> None:
        """
        Close the active Snowflake connection and reset connection state.
        
        Note:
            Safe to call even if no connection exists. Logs closure information.
        """
        if self.connection:
            self.connection.close()
            self.connection = None
            print(f"Connection closed ({self.database}.{self.schema}).")

if __name__ == "__main__":

    selected_db = 'COVID19_EPIDEMIOLOGICAL_DATA' # 'AMAZON_AND_ECOMMERCE_WEBSITES_PRODUCT_VIEWS_AND_PURCHASES'
    selected_schema = 'PUBLIC' # 'DATAFEEDS'

    sql_query = "SELECT * FROM DATAFEEDS.PROyDUCT_VIEWS_AND_PURCHASES LIMIT 10;"

    table_list = 'CDC_INPATIENT_BEDS_ALL','CDC_INPATIENT_BEDS_COVID_19','CDC_INPATIENT_BEDS_ICU_ALL'

    # Example usage:
    snowflake_db = SnowflakeHandler(
        user=st.secrets["SNOWFLAKE_USER"],
        password=st.secrets["SNOWFLAKE_PASSWORD"],
        account=st.secrets["SNOWFLAKE_ACCOUNT"],
        warehouse=st.secrets["SNOWFLAKE_WAREHOUSE"],
        database=selected_db,
        schema=selected_schema
    )

    snowflake_db.connect()
    # results = snowflake_db.execute_query(sql_query)
    # results = snowflake_db.validate_query(sql_query)
    # results = snowflake_db.get_all_columns()
    # results = snowflake_db.get_table_columns("PRODUCT_VIEWS_AND_PURCHASES")
    # results = snowflake_db.get_tables_columns(table_list)

#     results = f"""    
# # Tables
# {snowflake_db.get_tables()}

# # Tables and Columns
# {snowflake_db.get_all_columns()}
#     """
#     print(results)

#     with open("snowflake_tables_columns.md", "w") as f:
#         f.write(results)

    # results = snowflake_db.get_tables_info_md(table_list)

    results = snowflake_db.get_distinct_values_dict('COUNTY','DEMOGRAPHICS',filter="STATE = 'LA'")

    print(results)


    snowflake_db.close_connection()
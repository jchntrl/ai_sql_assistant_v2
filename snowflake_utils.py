import asyncio
import snowflake.connector
import streamlit as st
from typing import Optional, List, Tuple, Any



class SnowflakeHandler:
    def __init__(self, user: str, password: str, account: str, warehouse: str, database: str, schema: str) -> None:
        """
        Initialize the SnowflakeHandler with connection parameters.
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
        Establish a connection to Snowflake.
        """
        self.connection = snowflake.connector.connect(
            user=self.user,
            password=self.password,
            account=self.account,
            warehouse=self.warehouse,
            database=self.database,
            schema=self.schema
        )
        print(f"Connected to Snowflake ({self.database}.{self.schema}).")

    def get_databases(self) -> List[str]:
        """
        Query INFORMATION_SCHEMA.TABLES and return the list of databases available .
        :return: markdown table as str.
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
        Query INFORMATION_SCHEMA.TABLES and return the list of schemas available .
        :return: markdown table as str.
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
        Query INFORMATION_SCHEMA.TABLES and return the list of tables in a Schema .
        :return: markdown table as str.
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
        Execute a SQL query and return the results.
        :param query: SQL query string to execute.
        :return: List of tuples containing query results.
        """
        if not self.connection:
            raise Exception("Connection not established. Call connect() first.")
        
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            return cursor.fetch_pandas_all()
        except Exception as e:
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
        Execute a SQL query and return the results.
        :param query: SQL query string to execute.
        :return: List of tuples containing query results.
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

    def execute_query_sample_md(self, query: str) -> str:
        """
        Execute a SQL query and return the results.
        :param query: SQL query string to execute.
        :return: List of tuples containing query results.
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
        Execute a SQL query and return the results.
        :param query: SQL query string to execute.
        :return: markdown table as str.
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
        Close the Snowflake connection.
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

    results = snowflake_db.get_tables_info_md(table_list)

    print(results)


    snowflake_db.close_connection()
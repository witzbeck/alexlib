"""
alexlib.db.managers
-------------------

The `alexlib.db.managers` module provides a set of classes for managing and interacting with databases,
specifically designed to simplify common database operations like creating, reading, updating, and deleting data.

Classes:
    DatabaseManager: A general database manager class that can be adapted to various database systems. It provides
    methods to execute SQL queries, fetch data, and perform CRUD (Create, Read, Update, Delete) operations. This class
    also includes decorators for handling database connections and cursors, ensuring that resources are properly managed.

    SqlLiteManager: A subclass of DatabaseManager that is specifically tailored for SQLite databases. It defaults to using
    SQLite's in-memory database for ease of use and quick setup, but can be configured to work with file-based SQLite databases.

Features:
    - Connection Management: Automated handling of database connections and cursors, ensuring efficient resource management.
    - Query Execution: Execute SQL queries directly and manage the results.
    - Data Retrieval: Fetch data from the database and return it in a convenient format.
    - CRUD Operations: Simplified methods for creating, reading, updating, and deleting database records.
    - Table Management: Tools for creating, dropping, and managing database tables.
    - Input Validation: Validation of table names to ensure they adhere to standard naming conventions.

Usage:
    This module is intended to be used in applications that require database interaction, providing a streamlined
    interface for common database tasks. It abstracts the lower-level details of database connection and query execution,
    allowing developers to focus on their application logic.

Note:
    While the module provides basic security and validation checks (e.g., table name validation), it's important to
    carefully handle SQL query parameters to avoid SQL injection attacks. Always validate and sanitize user inputs.

Example:
    To use this module, instantiate the appropriate manager class (e.g., SqlLiteManager for SQLite databases) and use
    the methods provided to interact with the database. For instance, you can create tables, insert data, and query
    data using simple method calls.

"""

from dataclasses import dataclass, field
from functools import cached_property
from logging import info, warning
from pathlib import Path
from shutil import copyfile
from typing import Any
from sqlite3 import Cursor, connect as sqlite_connect

from pandas import DataFrame, read_sql
from sqlalchemy import Connection, CursorResult, Engine, TextClause, create_engine
from psycopg.errors import DuplicateSchema, UndefinedTable
from sqlalchemy_utils import create_database, database_exists

from alexlib.auth import Auth, Curl
from alexlib.config import Settings
from alexlib.core import ping
from alexlib.db.objects import Name
from alexlib.db.sql import SQL, mk_view_text
from alexlib.db.sql import create_cmd, drop_cmd, truncate_table_cmd
from alexlib.df import get_distinct_col_vals
from alexlib.files import File, path_search


@dataclass
class ConnectionManager:
    """Connection manager class"""

    curl: Curl = field(repr=False, default=None)
    db_file: str = field(default=None)
    engine: Engine = field(init=False, repr=False)
    cnxn: Connection = field(init=False, repr=False)
    settings: Settings = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """sets attributes"""
        if self.curl is not None:
            self.engine = create_engine(self.curl)
            self.cnxn = self.engine.connect()
        else:
            raise ValueError("need curl for engine")

    def __del__(self) -> None:
        """closes connection"""
        if hasattr(self, "cnxn"):
            self.cnxn.close()
            del self.cnxn
        if hasattr(self, "engine"):
            del self.engine

    @property
    def isopen(self) -> bool:
        """checks if connection is open"""
        if not self.curl.canping:
            raise ValueError("need host and port to ping")
        return ping(self.curl.host, self.curl.port)

    @property
    def dbexists(self) -> bool:
        """checks if database exists"""
        if self.curl.database is None:
            return False
        return database_exists(str(self.curl))

    @classmethod
    def from_curl_parts(
        cls,
        username: str,
        password: str,
        host: str,
        port: int,
        database: str,
        dialect: str = "postgres",
        sid: str = None,
    ):
        """makes connection from curl parts"""
        curl = Curl(
            username=username,
            password=password,
            host=host,
            port=port,
            database=database,
            dialect=dialect,
            sid=sid,
        )
        return cls(curl)

    @classmethod
    def from_auth(cls, auth: str | tuple[str] | Auth) -> "DatabaseManager":
        """makes connection from auth"""
        auth = Auth(auth) if not isinstance(auth, Auth) else auth
        return cls(curl=auth.curl)

    @classmethod
    def from_env(cls) -> "DatabaseManager":
        """makes connection from environment variables"""
        return cls.from_auth(Auth.from_env())


@dataclass
class QueryManager:
    """Handles database queries and data operations."""

    cnxn_mgr: ConnectionManager = field(
        default_factory=ConnectionManager.from_env, repr=False
    )
    schema_col: str = field(default="table_schema", repr=False)
    table_col: str = field(default="table_name", repr=False)

    @staticmethod
    def execute_query(cursor: Cursor, query: str, params: tuple = None) -> CursorResult:
        """Internal method to execute a query"""
        sql = SQL(query)
        if ";" in sql.clause:
            for part in sql.clause.split(";"):
                if part:
                    QueryManager.execute_query(cursor, part)
        else:
            try:
                cursor.execute(sql.clause, params=params)
                cursor.commit()
            except UndefinedTable as e:
                raise UndefinedTable(f"{e} - {sql.clause}")
        return cursor

    def execute(self, query: SQL, params: tuple = None) -> CursorResult:
        """Execute a SQL query"""
        with self.cnxn_mgr.cnxn.cursor() as cursor:
            return QueryManager.execute_query(cursor, query, params=params)

    def executemany(self, query: str, params: list[tuple]) -> None:
        """Execute a SQL query multiple times"""
        with self.cnxn_mgr.cnxn.cursor() as cursor:
            cursor.executemany(query, params=params)
            cursor.commit()

    def fetchone(
        self, query: str, params: tuple = None
    ) -> str | int | float | bool | None:
        """Fetch data from the database"""
        cursor = self.execute(query, params=params)
        return cursor.fetchone()[0]

    def fetchall(self, query: str, params: tuple = None) -> DataFrame:
        """Fetch data from the database"""
        cursor = self.execute(query, params=params)
        return cursor.fetchall()

    def fetchmany(self, query: str, many: int, params: tuple = None) -> DataFrame:
        """Fetch data from the database"""
        cursor = self.execute(query, params=params)
        return cursor.fetchmany(many)

    def create_table(self, table_name: str, columns: str) -> None:
        """Create a table"""
        query = f"CREATE TABLE IF NOT EXISTS {Name(table_name)} ({columns})"
        self.execute(query)

    def insert(self, table_name: str, columns: tuple, values: tuple) -> None:
        """Insert rows into a table"""

        # Validate the table and column names
        table_name = Name(table_name)
        col_placeholder = ", ".join([Name(col) for col in columns])  # Column names

        # Construct column and value placeholders
        val_placeholder = ", ".join(["?" for _ in values])  # Value placeholders

        # Construct the SQL query
        query = (
            f"INSERT INTO {table_name} ({col_placeholder}) VALUES ({val_placeholder})"
        )

        # Prepare the parameters for the query
        params = values

        # Execute the query
        self.execute(query, params)

    def select(
        self,
        table_name: str,
        columns: str | list = "*",
        where_clause: str = None,
        where_params: tuple = None,
    ) -> DataFrame:
        """Select rows from a table"""

        # Validate table name
        table_name = Name(table_name)

        # Handle columns
        if isinstance(columns, list):
            columns = ", ".join(
                [Name(column) for column in columns]
            )  # Ensure column names are safe

        # Start constructing the query
        query = f"SELECT {columns} FROM {table_name}"

        # Add where clause if present
        params = ()
        if where_clause:
            query += f" WHERE {where_clause}"
            params = where_params

        return self.fetchall(query, params=params)

    def update(self, table_name: str, set_clause: dict, where_clause: dict) -> None:
        """Update rows in a table"""

        # Validate table name
        table_name = Name(table_name)

        # Construct set clause
        set_parts = [f"{column} = ?" for column in set_clause.keys()]
        set_statement = ", ".join(set_parts)

        # Construct where clause
        where_parts = [f"{column} = ?" for column in where_clause.keys()]
        where_statement = " AND ".join(where_parts)

        # Combine all parts of the query
        # Directly include the table name into the query string, as placeholders cannot be used for table names
        query = f"UPDATE {table_name} SET {set_statement} WHERE {where_statement}"

        # Prepare the parameters for the query
        # Ensure that only values are included in the parameters, not the table name
        params = tuple(set_clause.values()) + tuple(where_clause.values())

        # Execute the query
        self.execute(query, params=params)

    def delete(
        self,
        table_name: str,
        where_clause: list[str],
        where_params: tuple,
    ) -> None:
        """Delete rows from a table"""

        # Validate table name
        table_name = Name(table_name)

        # Construct where clause with placeholders
        where_parts = [f"{condition} = ?" for condition in where_clause]
        where_statement = " AND ".join(where_parts)

        # Combine all parts of the query
        query = f"DELETE FROM {table_name} WHERE {where_statement}"

        # Execute the query
        self.execute(query, params=where_params)

    def get_df(self, sql: SQL | str | TextClause, params: tuple = None) -> DataFrame:
        """gets dataframe from sql"""
        sql = SQL(sql) if not isinstance(sql, SQL) else sql
        return read_sql(sql.clause, self.cnxn_mgr.engine, params=params)

    @cached_property
    def info_schema_tables(self) -> DataFrame:
        """gets info schema"""
        return self.get_df("select * from information_schema.tables")

    @cached_property
    def info_schema_columns(self) -> DataFrame:
        """gets info schema"""
        return self.get_df("select * from information_schema.columns")

    @cached_property
    def allschemas(self) -> list[str]:
        """gets list of schemas"""
        return get_distinct_col_vals(self.info_schema_tables, self.schema_col)

    def schema_exists(self, schema: str) -> bool:
        """checks if schema exists"""
        return schema in self.allschemas

    @cached_property
    def schema_tables(self) -> dict[str : list[str]]:
        """gets all schemas and tables"""
        return {
            schema: self.get_all_schema_tables(schema) for schema in self.allschemas
        }

    def file_to_db(
        self,
        file: File,
        schema: str,
        table: str,
        engine: Engine = None,
        if_exists: str = "replace",
        index: bool = False,
    ) -> None:
        """writes file to database"""
        if file.issql:
            engine = self.cnxn_mgr.engine
        if not isinstance(schema, str):
            schema = str(schema)
        df = file.get_df(engine=engine)
        df.to_sql(
            table,
            engine,
            schema=schema,
            if_exists=if_exists,
            index=index,
        )

    def sql_to_file(
        self,
        sqlfile: File,
        writepath: Path,
    ) -> None:
        """writes data from executed query to file"""
        df = sqlfile.get_df(eng=self.cnxn_mgr.engine)
        return File.df_to_file(df, writepath)

    def show_row_counts(
        self,
        schema: str | list[str] | None = None,
        table: str | list[str] | None = None,
        system_schemas: bool = False,
    ) -> None:
        """prints row counts for tables"""
        if not system_schemas:
            d = {
                k: v
                for k, v in self.schema_tables.items()
                if k not in ["information_schema", "pg_catalog"]
            }
        if isinstance(schema, str):
            schema = [schema]
        if schema:
            d = {k: v for k, v in d.items() if k in schema}

        for schema_, tables in d.items():
            print(schema_)
            if isinstance(table, str):
                tables = [table]
            if table:
                tables = [tbl for tbl in tables if tbl in table]
            for tbl in tables:
                try:
                    sql = f'SELECT count(*) FROM {schema_}."{tbl}"'
                    rows = self.fetchone(sql)
                    print(f"\t{schema_}.{tbl} = {rows} rows")
                except UndefinedTable:
                    print(f"\t{schema_}.{tbl} = UndefinedTable")

    @property
    def table_rows(self) -> dict[str : dict[str:int]]:
        """gets row counts for all tables"""
        return {
            schema: {
                table: self.get_record_count(schema, table, print_=False)
                for table in tables
            }
            for schema, tables in self.schema_tables.items()
        }

    def table_exists(self, schema: str, table: str) -> bool:
        """checks if table exists"""
        try:
            return table in self.schema_tables[schema]
        except KeyError:
            return False

    def create_schema(self, schema: str) -> None:
        """creates schema"""
        try:
            self.execute(create_cmd("schema", schema))
        except DuplicateSchema:
            warning(f"Schema({schema}) already exists")

    def drop_schema(self, schema: str) -> None:
        """drops schema"""
        self.execute(drop_cmd("schema", schema))

    def drop_table(self, schema: str, table: str) -> None:
        """drops table"""
        self.execute(drop_cmd("table", table, schema=schema))

    def drop_all_schema_tables(self, schema: str) -> None:
        """drops all tables in schema"""
        self.drop_schema(schema)
        self.create_schema(schema)

    def drop_table_pattern(
        self,
        pattern: str,
        schema: str,
    ) -> None:
        """drops tables matching pattern"""
        return [
            self.drop_table(schema, table)
            for table in self.get_all_schema_tables(schema)
            if pattern in table
        ]

    def drop_view(self, schema: str, view: str) -> None:
        """drops view"""
        self.execute(drop_cmd("view", view, schema=schema))

    def truncate_table(self, schema: str, table: str) -> None:
        """truncates table"""
        self.execute(truncate_table_cmd(table, schema=schema))

    def get_all_schema_tables(self, schema: str) -> list[str]:
        """gets all tables in schema"""
        return get_distinct_col_vals(self.schema_tables[schema], self.table_col)

    def truncate_schema(self, schema: str) -> None:
        """truncates all tables in schema"""
        tabs = self.get_all_schema_tables(schema)
        for tab in tabs:
            self.truncate_table(schema, tab)

    def df_from_sqlfile(self, path: Path) -> DataFrame:
        """gets dataframe from sql file"""
        return self.fetchall(SQL.from_path(path).clause)

    def df_to_db(self, df: DataFrame, schema: str, table: str, **kwargs) -> None:
        """writes dataframe to database"""
        if schema not in self.allschemas:
            try:
                self.create_schema(schema)
            except DuplicateSchema:
                warning(f"schema[{schema}] already exists")
        df.to_sql(table, self.cnxn_mgr.engine, schema=schema, **kwargs)

    def get_table(self, schema: str, table: str, nrows: int = None) -> DataFrame:
        """gets table from database"""
        tbl = f"{schema}.{table}"
        params = (tbl, nrows) if nrows else (tbl,)
        sql = "select * from ?"
        if nrows:
            sql += " limit ?"
        return self.get_df(sql, params=params)

    def mk_view(self, name: str, sql: str) -> None:
        """makes view in database"""
        statement = mk_view_text(name, sql)
        return self.execute(statement)

    def get_last_id(self, schema: str, table: str, id_col: str) -> int:
        """gets last id in table"""
        sql = f"select max({id_col}) from {schema}.{table}"
        try:
            id_int = self.fetchone(sql)
            ret = 1 if id_int is None else int(id_int)
        except UndefinedTable:
            ret = 1
        return ret

    def get_next_id(self, *args) -> int:
        """gets next id in table"""
        return self.get_last_id(*args) + 1

    def get_last_record(
        self,
        schema: str,
        table: str,
        id_col: str,
    ) -> DataFrame:
        """gets last record in table"""
        last_id = self.get_last_id(schema, table, id_col)
        sql = f"select * from {schema}.{table} where {id_col} = {last_id}"
        return self.fetchone(sql)

    def get_record_count(self, schema: str, table: str, print_: bool = True) -> int:
        """gets record count for table"""
        sql = f"select count(*) from {schema}.{table}"
        val = self.fetchone(sql)
        if print_:
            print(f"{schema}.{table} record count: {val}")
        return val

    def get_last_val(self, schema: str, table: str, id_col: str, val_col: str) -> Any:
        """gets last value in column"""
        last_rec = self.get_last_record(schema, table, id_col)
        return last_rec.loc[0, val_col]


@dataclass
class DatabaseManager:
    """Database manager class"""

    cnxn_mgr: ConnectionManager = field(
        default_factory=ConnectionManager.from_env, repr=False
    )
    query_mgr: QueryManager = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """sets attributes"""
        self.query_mgr = QueryManager(cnxn_mgr=self.cnxn_mgr)

    def __del__(self) -> None:
        """closes connection"""
        del self.query_mgr
        del self.cnxn_mgr

    @staticmethod
    def _execute_query(
        cursor: Cursor, query: str, params: tuple = None
    ) -> CursorResult:
        """Internal method to execute a query"""
        sql = SQL(query)
        if ";" in sql.clause:
            for part in sql.split(";"):
                if part:
                    DatabaseManager._execute_query(cursor, part)
        else:
            try:
                cursor.execute(sql.clause, params=params)
                cursor.commit()
            except UndefinedTable as e:
                raise UndefinedTable(f"{e} - {sql.clause}")
        return cursor

    def execute(self, query: SQL, params: tuple = None) -> CursorResult:
        """Execute a SQL query"""
        with self.cnxn_mgr.cnxn.cursor() as cursor:
            return DatabaseManager._execute_query(cursor, query, params=params)

    def executemany(self, query: str, params: list[tuple]) -> None:
        """Execute a SQL query multiple times"""
        with self.cnxn_mgr.cnxn.cursor() as cursor:
            cursor.executemany(query, params=params)
            cursor.commit()

    def fetchone(
        self, query: str, params: tuple = None
    ) -> str | int | float | bool | None:
        """Fetch data from the database"""
        cursor = self.execute(query, params=params)
        return cursor.fetchone()[0]

    def fetchall(self, query: str, params: tuple = None) -> DataFrame:
        """Fetch data from the database"""
        cursor = self.execute(query, params=params)
        return cursor.fetchall()

    def fetchmany(self, query: str, many: int, params: tuple = None) -> DataFrame:
        """Fetch data from the database"""
        cursor = self.execute(query, params=params)
        return cursor.fetchmany(many)

    def create_table(self, table_name: str, columns: str) -> None:
        """Create a table"""
        query = f"CREATE TABLE IF NOT EXISTS {Name(table_name)} ({columns})"
        self.execute(query)

    def insert(self, table_name: str, columns: tuple, values: tuple) -> None:
        """Insert rows into a table"""

        # Validate the table and column names
        table_name = Name(table_name)
        col_placeholder = ", ".join([Name(col) for col in columns])  # Column names

        # Construct column and value placeholders
        val_placeholder = ", ".join(["?" for _ in values])  # Value placeholders

        # Construct the SQL query
        query = (
            f"INSERT INTO {table_name} ({col_placeholder}) VALUES ({val_placeholder})"
        )

        # Prepare the parameters for the query
        params = values

        # Execute the query
        self.execute(query, params)

    def select(
        self,
        table_name: str,
        columns: str | list = "*",
        where_clause: str = None,
        where_params: tuple = None,
    ) -> DataFrame:
        """Select rows from a table"""

        # Validate table name
        table_name = Name(table_name)

        # Handle columns
        if isinstance(columns, list):
            columns = ", ".join(
                [Name(column) for column in columns]
            )  # Ensure column names are safe

        # Start constructing the query
        query = f"SELECT {columns} FROM {table_name}"

        # Add where clause if present
        params = ()
        if where_clause:
            query += f" WHERE {where_clause}"
            params = where_params

        return self.fetchall(query, params=params)

    def update(self, table_name: str, set_clause: dict, where_clause: dict) -> None:
        """Update rows in a table"""

        # Validate table name
        table_name = Name(table_name)

        # Construct set clause
        set_parts = [f"{column} = ?" for column in set_clause.keys()]
        set_statement = ", ".join(set_parts)

        # Construct where clause
        where_parts = [f"{column} = ?" for column in where_clause.keys()]
        where_statement = " AND ".join(where_parts)

        # Combine all parts of the query
        # Directly include the table name into the query string, as placeholders cannot be used for table names
        query = f"UPDATE {table_name} SET {set_statement} WHERE {where_statement}"

        # Prepare the parameters for the query
        # Ensure that only values are included in the parameters, not the table name
        params = tuple(set_clause.values()) + tuple(where_clause.values())

        # Execute the query
        self.execute(query, params=params)

    def delete(
        self,
        table_name: str,
        where_clause: list[str],
        where_params: tuple,
    ) -> None:
        """Delete rows from a table"""

        # Validate table name
        table_name = Name(table_name)

        # Construct where clause with placeholders
        where_parts = [f"{condition} = ?" for condition in where_clause]
        where_statement = " AND ".join(where_parts)

        # Combine all parts of the query
        query = f"DELETE FROM {table_name} WHERE {where_statement}"

        # Execute the query
        self.execute(query, params=where_params)

    @property
    def isopen(self) -> bool:
        """checks if connection is open"""
        if not self.cnxn_mgr.curl.canping:
            raise ValueError("need host and port to ping")
        return ping(self.cnxn_mgr.curl.host, self.cnxn_mgr.curl.port)

    @property
    def dbexists(self) -> bool:
        """checks if database exists"""
        if self.cnxn_mgr.curl.database is None:
            return False
        return database_exists(str(self.cnxn_mgr.curl))

    @classmethod
    def from_auth(cls, auth: str | tuple[str] | Auth) -> "DatabaseManager":
        """makes connection from auth"""
        auth = Auth(auth) if not isinstance(auth, Auth) else auth
        return cls(cnxn_mgr=ConnectionManager.from_auth(auth))

    def get_df(self, sql: SQL | str | TextClause, params: tuple = None) -> DataFrame:
        """gets dataframe from sql"""
        sql = SQL(sql) if not isinstance(sql, SQL) else sql
        return read_sql(sql.clause, self.cnxn_mgr.engine, params=params)

    @cached_property
    def info_schema_tables(self) -> DataFrame:
        """gets info schema"""
        return self.get_df("select * from information_schema.tables")

    @cached_property
    def info_schema_columns(self) -> DataFrame:
        """gets info schema"""
        return self.get_df("select * from information_schema.columns")

    @cached_property
    def allschemas(self) -> list[str]:
        """gets list of schemas"""
        return get_distinct_col_vals(self.info_schema_tables, self.query_mgr.schema_col)

    def schema_exists(self, schema: str) -> bool:
        """checks if schema exists"""
        return schema in self.allschemas

    @cached_property
    def schema_tables(self) -> dict[str : list[str]]:
        """gets all schemas and tables"""
        return {
            schema: self.get_all_schema_tables(schema) for schema in self.allschemas
        }

    def file_to_db(
        self,
        file: File,
        schema: str,
        table: str,
        engine: Engine = None,
        if_exists: str = "replace",
        index: bool = False,
    ) -> None:
        """writes file to database"""
        if file.issql:
            engine = self.cnxn_mgr.engine
        if not isinstance(schema, str):
            schema = str(schema)
        df = file.get_df(engine=engine)
        df.to_sql(
            table,
            self.cnxn_mgr.engine,
            schema=schema,
            if_exists=if_exists,
            index=index,
        )

    def sql_to_file(
        self,
        sqlfile: File,
        writepath: Path,
    ) -> None:
        """writes data from executed query to file"""
        df = sqlfile.get_df(eng=self.cnxn_mgr.engine)
        return File.df_to_file(df, writepath)

    def show_row_counts(
        self,
        schema: str | list[str] | None = None,
        table: str | list[str] | None = None,
        system_schemas: bool = False,
    ) -> None:
        """prints row counts for tables"""
        if not system_schemas:
            d = {
                k: v
                for k, v in self.schema_tables.items()
                if k not in ["information_schema", "pg_catalog"]
            }
        if isinstance(schema, str):
            schema = [schema]
        if schema:
            d = {k: v for k, v in d.items() if k in schema}

        for schema_, tables in d.items():
            print(schema_)
            if isinstance(table, str):
                tables = [table]
            if table:
                tables = [tbl for tbl in tables if tbl in table]
            for tbl in tables:
                try:
                    sql = f'SELECT count(*) FROM {schema_}."{tbl}"'
                    rows = self.fetchone(sql)
                    print(f"\t{schema_}.{tbl} = {rows} rows")
                except UndefinedTable:
                    print(f"\t{schema_}.{tbl} = UndefinedTable")

    @property
    def table_rows(self) -> dict[str : dict[str:int]]:
        """gets row counts for all tables"""
        return {
            schema: {
                table: self.get_record_count(schema, table, print_=False)
                for table in tables
            }
            for schema, tables in self.schema_tables.items()
        }

    def table_exists(self, schema: str, table: str) -> bool:
        """checks if table exists"""
        try:
            return table in self.schema_tables[schema]
        except KeyError:
            return False

    @staticmethod
    def mk_cmd_sql(
        cmd: str, obj_type: str, obj_name: str, schema: str = None, addl_cmd: str = ""
    ) -> SQL:
        """makes sql for object commands"""
        if obj_type not in ["table", "view"]:
            name = obj_name
        elif schema is None:
            name = obj_name
        else:
            name = f"{schema}.{obj_name}"
        return SQL(f"{cmd} {obj_type} {name} {addl_cmd}")

    def obj_cmd(self, *args, **kwargs) -> None:
        """runs object command"""
        sql = DatabaseManager.mk_cmd_sql(*args, **kwargs)
        self.execute(sql.clause)

    def create_schema(self, schema: str) -> None:
        """creates schema"""
        try:
            self.obj_cmd("create", "schema", schema)
        except DuplicateSchema:
            print(f"schema[{schema}] already exists")

    def drop_schema(self, schema: str) -> None:
        """drops schema"""
        self.obj_cmd("drop", "schema", schema, addl_cmd="cascade")

    def drop_all_schema_tables(self, schema: str) -> None:
        """drops all tables in schema"""
        self.drop_schema(schema)
        self.create_schema(schema)

    def drop_table(self, schema: str, table: str, cascade: bool = True) -> None:
        """drops table"""
        addl_cmd = "cascade" if cascade else ""
        self.obj_cmd("drop", "table", table, schema=schema, addl_cmd=addl_cmd)

    def drop_table_pattern(
        self,
        pattern: str,
        schema: str,
        cascade: bool = True,
    ) -> None:
        """drops tables matching pattern"""
        return [
            self.drop_table(schema, tab, cascade=cascade)
            for tab in self.get_all_schema_tables(schema)
            if pattern in tab
        ]

    def drop_view(self, schema: str, view: str) -> None:
        """drops view"""
        self.obj_cmd("drop", "view", view, schema=schema)

    def truncate_table(self, schema: str, table: str) -> None:
        """truncates table"""
        self.obj_cmd("truncate", "table", table, schema=schema)

    def get_all_schema_tables(self, schema: str) -> list[str]:
        """gets all tables in schema"""
        return get_distinct_col_vals(
            self.schema_tables[schema], self.query_mgr.table_col
        )

    def truncate_schema(self, schema: str) -> None:
        """truncates all tables in schema"""
        tabs = self.get_all_schema_tables(schema)
        for tab in tabs:
            self.truncate_table(schema, tab)

    def df_from_sqlfile(self, filename: str, path: Path = None) -> DataFrame:
        """gets dataframe from sql file"""
        if path is None:
            path = path_search(filename)
        return self.execute(SQL.from_path(path).clause)

    def df_to_db(self, df: DataFrame, schema: str, table: str, **kwargs) -> None:
        """writes dataframe to database"""
        if schema not in self.allschemas:
            try:
                self.create_schema(schema)
            except DuplicateSchema:
                warning(f"schema[{schema}] already exists")
        df.to_sql(table, self.cnxn_mgr.engine, schema=schema, **kwargs)

    def mk_query(self, schema: str, table: str) -> SQL:
        """makes select * from table sql"""
        info_ = self.info_schema_columns
        info_ = info_[info_["table_schema"] == schema]
        info_ = info_[info_["table_name"] == table]
        return SQL.from_info_schema(schema, table, info_)

    def get_table(self, schema: str, table: str, nrows: int = None) -> DataFrame:
        """gets table from database"""
        tbl = f"{schema}.{table}"
        params = (tbl, nrows) if nrows else (tbl,)
        sql = "select * from ?"
        if nrows:
            sql += " limit ?"
        return self.get_df(sql, params=params)

    def mk_view(self, name: str, sql: str) -> None:
        """makes view in database"""
        statement = mk_view_text(name, sql)
        return self.execute(statement)

    def get_last_id(self, schema: str, table: str, id_col: str) -> int:
        """gets last id in table"""
        sql = f"select max({id_col}) from {schema}.{table}"
        try:
            id_int = self.fetchone(sql)
            ret = 1 if id_int is None else int(id_int)
        except UndefinedTable:
            ret = 1
        return ret

    def get_next_id(self, *args) -> int:
        """gets next id in table"""
        return self.get_last_id(*args) + 1

    def get_last_record(
        self,
        schema: str,
        table: str,
        id_col: str,
    ) -> DataFrame:
        """gets last record in table"""
        last_id = self.get_last_id(schema, table, id_col)
        sql = f"select * from {schema}.{table} where {id_col} = {last_id}"
        return self.fetchone(sql)

    def get_record_count(self, schema: str, table: str, print_: bool = True) -> int:
        """gets record count for table"""
        sql = f"select count(*) from {schema}.{table}"
        val = self.fetchone(sql)
        if print_:
            print(f"{schema}.{table} record count: {val}")
        return val

    def get_last_val(self, schema: str, table: str, id_col: str, val_col: str) -> Any:
        """gets last value in column"""
        last_rec = self.get_last_record(schema, table, id_col)
        return last_rec.loc[0, val_col]


@dataclass
class SqlLiteManager(DatabaseManager):
    """SqlLite manager class"""

    cnxn_mgr: ConnectionManager = field(
        init=False,
        repr=False,
    )
    db_file: str = field(default=":memory:")

    def __post_init__(self) -> None:
        """sets attributes"""
        self.engine = create_engine(f"sqlite:///{self.db_file}")
        self.cnxn_mgr = ConnectionManager(curl=self.engine.url)

    def __del__(self) -> None:
        try:
            self.cnxn.close()
        except AttributeError:
            info("no connection to close")
        super().__del__()

    def backup_database(self, backup_path: str) -> None:
        """Backup the SQLite database to a specified path"""
        if self.db_file != ":memory:":
            copyfile(self.db_file, backup_path)

    def restore_database(self, backup_path: str) -> None:
        """Restore the SQLite database from a backup"""
        if Path(backup_path).exists():
            copyfile(backup_path, self.db_file)

    def check_integrity(
        self,
    ) -> bool:
        """Check the integrity of the SQLite database"""
        return self.fetchone("PRAGMA integrity_check") == "ok"

    def load_database_to_memory(self) -> None:
        """Load a file-based SQLite database into memory"""
        if self.db_file == ":memory:":
            raise ValueError("The database is already in memory.")

        # Create a new in-memory database
        memory_conn = sqlite_connect(":memory:")
        file_conn = sqlite_connect(self.db_file)

        # Copy data from file to memory
        with memory_conn, file_conn:
            file_conn.backup(memory_conn)

        # Update the connection function to the in-memory database
        self.cnxn_mgr.cnxn = memory_conn

    def save_memory_database_to_file(self, file_path: str) -> None:
        """Save an in-memory SQLite database to a file"""
        if self.db_file != ":memory:":
            raise ValueError("The current database is not in memory.")

        # Create a new file-based database connection
        file_conn = sqlite_connect(file_path)
        memory_conn = sqlite_connect(":memory:")

        # Copy data from memory to file
        with memory_conn, file_conn:
            memory_conn.backup(file_conn)

        # Update the connection function and db_file to the new file-based database
        self.db_file = file_path
        self.cnxn_mgr.cnxn = file_conn


@dataclass
class MSSQLManager(DatabaseManager):
    """MSSQL manager class"""

    def __post_init__(self) -> None:
        self.engine = create_engine(self.cnxn_mgr.curl.mssql)
        if not database_exists(self.engine.url):
            create_database(self.engine.url)


# Postgres Manager
@dataclass
class PostgresManager(DatabaseManager):
    """Postgres manager class"""

    def __post_init__(self) -> None:
        self.engine = create_engine(self.cnxn_mgr.curl.postgres)
        if not database_exists(self.engine.url):
            create_database(self.engine.url)

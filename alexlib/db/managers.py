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


from collections.abc import Callable
from dataclasses import dataclass
from functools import partial, wraps
from pathlib import Path
from re import match
from shutil import copyfile
from typing import Any
from sqlite3 import Cursor, connect as sqlite3_connect

from attr import field
from pandas import DataFrame
from sqlalchemy import Connection, create_engine


def validate_name(name: str) -> None:
    """Validate a table name"""
    if not match(r"^[a-zA-Z0-9_]+$", name):
        raise ValueError(f"Invalid name: {name}")
    return name


@dataclass
class DatabaseManager:
    """Database manager class"""

    connect_func: Callable
    db_file: str = field(default=None)

    def __post_init__(self) -> None:
        if self.db_file:
            self.connect_func = partial(self.connect_func, self.db_file)

    def with_connection(self, func: Callable) -> Callable:
        """Decorator for creating and closing database connections"""

        @wraps(func)
        def with_connection_wrapper(self, *args, **kwargs) -> Any:
            """Execute a function with a connection"""
            cnxn = self.connect_func()
            result = func(self, cnxn, *args, **kwargs)
            cnxn.close()
            return result

        return with_connection_wrapper

    def with_cursor(self, func: Callable) -> Callable:
        """Decorator for creating and closing cursors"""

        @wraps(func)
        def with_cursor_wrapper(self, cnxn: Connection, *args, **kwargs) -> Any:
            """Execute a function with a cursor"""
            cursor = cnxn.cursor()
            result = func(self, cursor, *args, **kwargs)
            cnxn.commit()
            return result

        return with_cursor_wrapper

    @with_connection
    @with_cursor
    def execute(self, cursor: Cursor, query: str, params: tuple = None) -> None:
        """Execute a SQL query"""
        cursor.execute(query, params)

    def execute_table(self, table_name: str, query: str) -> None:
        """Execute a SQL query on a table"""
        table_name = validate_name(table_name)
        self.execute(query, (table_name,))

    @with_connection
    @with_cursor
    def executemany(self, cursor: Cursor, query: str, params: list[tuple]) -> None:
        """Execute a SQL query multiple times"""
        cursor.executemany(query, params)

    @with_connection
    @with_cursor
    def fetch(self, cursor: Cursor, query: str, params: tuple = None) -> DataFrame:
        """Fetch data from the database"""
        cursor.execute(query, params)
        return cursor.fetchall()

    def create_table(self, table_name: str, columns: str) -> None:
        """Create a table"""
        table_name = validate_name(table_name)
        # Columns definition should be carefully crafted or validated
        query = f"CREATE TABLE IF NOT EXISTS ? ({columns})"
        self.execute_table(table_name, query)

    def insert(self, table_name: str, columns: tuple, values: tuple) -> None:
        """Insert rows into a table"""

        # Validate the table name
        table_name = validate_name(table_name)

        # Validate or sanitize column names if needed
        # ...

        # Construct column and value placeholders
        col_placeholder = ", ".join([f"{col}" for col in columns])  # Column names
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
        table_name = validate_name(table_name)

        # Handle columns
        if isinstance(columns, list):
            columns = ", ".join(
                [validate_name(column) for column in columns]
            )  # Ensure column names are safe

        # Start constructing the query
        query = f"SELECT {columns} FROM {table_name}"

        # Add where clause if present
        params = ()
        if where_clause:
            query += f" WHERE {where_clause}"
            params = where_params

        return self.fetch(query, params)

    def update(self, table_name: str, set_clause: dict, where_clause: dict) -> None:
        """Update rows in a table"""

        # Validate table name
        table_name = validate_name(table_name)

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
        self.execute(query, params)

    def delete(
        self,
        table_name: str,
        where_clause: list[str],
        where_params: tuple,
    ) -> None:
        """Delete rows from a table"""

        # Validate table name
        table_name = validate_name(table_name)

        # Construct where clause with placeholders
        where_parts = [f"{condition} = ?" for condition in where_clause]
        where_statement = " AND ".join(where_parts)

        # Combine all parts of the query
        query = f"DELETE FROM {table_name} WHERE {where_statement}"

        # Execute the query
        self.execute(query, where_params)

    def drop_table(self, table_name: str) -> None:
        """Drop a table"""

        # Construct query with validated table name
        query = f"DROP TABLE IF EXISTS {validate_name(table_name)}"

        # Execute the query
        self.execute_table(table_name, query)


@dataclass
class SqlLiteManager(DatabaseManager):
    """SqlLite manager class"""

    connect_func: Callable = field(default=sqlite3_connect)
    db_file: str = field(default=":memory:")

    def backup_database(self, backup_path: str) -> None:
        """Backup the SQLite database to a specified path"""
        if self.db_file != ":memory:":
            copyfile(self.db_file, backup_path)

    def restore_database(self, backup_path: str) -> None:
        """Restore the SQLite database from a backup"""
        if Path(backup_path).exists():
            copyfile(backup_path, self.db_file)

    def check_integrity(self) -> bool:
        """Check the integrity of the SQLite database"""
        with self.connect_func() as conn:
            cursor = conn.execute("PRAGMA integrity_check;")
            result = cursor.fetchone()
            return result[0] == "ok"

    def load_database_to_memory(self) -> None:
        """Load a file-based SQLite database into memory"""
        if self.db_file == ":memory:":
            raise ValueError("The database is already in memory.")

        # Create a new in-memory database
        memory_conn = sqlite3_connect(":memory:")
        file_conn = sqlite3_connect(self.db_file)

        # Copy data from file to memory
        with memory_conn, file_conn:
            file_conn.backup(memory_conn)

        # Update the connection function to the in-memory database
        self.connect_func = lambda: memory_conn

    def save_memory_database_to_file(self, file_path: str) -> None:
        """Save an in-memory SQLite database to a file"""
        if self.db_file != ":memory:":
            raise ValueError("The current database is not in memory.")

        # Create a new file-based database connection
        file_conn = sqlite3_connect(file_path)
        memory_conn = self.connect_func()

        # Copy data from memory to file
        with memory_conn, file_conn:
            memory_conn.backup(file_conn)

        # Update the connection function and db_file to the new file-based database
        self.db_file = file_path
        self.connect_func = lambda: file_conn


@dataclass
class MSSQLManager(DatabaseManager):
    """MSSQL manager class"""

    connection_string: str = field(default=None)
    connect_func: Callable = field(default=create_engine)

    def __post_init__(self) -> None:
        if self.connection_string:
            self.connect_func = partial(self.connect_func, self.connection_string)


# Postgres Manager
@dataclass
class PostgresManager(DatabaseManager):
    """Postgres manager class"""

    connection_string: str = field(default=None)
    connect_func: Callable = field(default=create_engine)

    def __post_init__(self) -> None:
        if self.connection_string:
            self.connect_func = partial(self.connect_func, self.connection_string)

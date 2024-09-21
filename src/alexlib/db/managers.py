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
from logging import info
from pathlib import Path
from shutil import copyfile
from sqlite3 import Connection as SQLiteConnection
from sqlite3 import Cursor as SQLiteCursor
from sqlite3 import connect as sqlite_connect
from typing import Any

from pandas import DataFrame, read_sql
from psycopg import Cursor
from psycopg.errors import UndefinedTable
from sqlalchemy import Connection, Engine, create_engine
from sqlalchemy_utils import create_database, database_exists

from alexlib.auth import Auth, Curl
from alexlib.core import chkenv, ping
from alexlib.db.objects import Name, Schema, Table
from alexlib.db.sql import SQL, create_cmd, drop_cmd, mk_view_text, truncate_table_cmd
from alexlib.db.utils import get_dfs_threaded
from alexlib.df import get_distinct_col_vals
from alexlib.files.config import Settings
from alexlib.files.objects import Directory, File


def create_memory_db() -> SQLiteConnection:
    """creates memory database"""
    return sqlite_connect(":memory:", check_same_thread=False)


@dataclass
class ExecutionManager:
    """Base execution manager class"""

    engine: Engine = field(repr=False)
    cursor: Cursor = field(repr=False, init=False)

    def __post_init__(self) -> None:
        """sets attributes"""
        self.cursor = self.engine.connect().cursor()

    def __del__(self) -> None:
        """closes cursor"""
        self.cursor.close()
        self.engine.dispose()

    def execute(self, query: SQL, params: tuple = None) -> Cursor:
        """Execute a SQL query"""
        self.cursor.execute(query, params=params)
        self.cursor.commit()
        return self.cursor

    def executemany(self, query: str, params: list[tuple]) -> None:
        """Execute a SQL query multiple times"""
        self.cursor.executemany(query, params=params)
        self.cursor.commit()

    def fetchone(
        self, query: str, params: tuple = None
    ) -> str | int | float | bool | None:
        """Fetch data from the database"""
        cursor = self.execute(query, params=params)
        ret = cursor.fetchone()
        try:
            return ret[0]
        except IndexError:
            return ret

    def fetchall(self, query: str, params: tuple = None) -> tuple[tuple]:
        """Fetch data from the database"""
        cursor = self.execute(query, params=params)
        return cursor.fetchall()

    def fetchmany(self, query: str, many: int, params: tuple = None) -> tuple[tuple]:
        """Fetch data from the database"""
        cursor = self.cursor.execute(query, params=params)
        return cursor.fetchmany(many)

    def fetchdf(self, query: str, params: tuple = None) -> DataFrame:
        """Fetch data from the database"""
        return read_sql(query, self.engine, params=params)

    def fetchcol(self, query: str, params: tuple = None, idx: int = 0) -> list:
        """Fetch data from the database"""
        return [row[idx] for row in self.fetchall(query, params=params)]


@dataclass
class RecordManager:
    """Base record manager class"""

    exec_mgr: ExecutionManager = field(repr=False)

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

        return self.exec_mgr.fetchall(query, params=params)

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
        self.exec_mgr.execute(query, params)

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
        self.exec_mgr.execute(query, params=params)

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
        self.exec_mgr.execute(query, params=where_params)


@dataclass
class BaseObjectManager:
    """Base object manager class"""

    exec_mgr: ExecutionManager = field(repr=False)
    object_type: str = field(default=None, repr=False)
    object_col: str = field(default=None, repr=False)

    def drop(self, name: str, schema: str = None) -> None:
        """drops object"""
        self.exec_mgr.execute(drop_cmd(self.object_type, name, schema=schema))

    def create(self, name: str, schema: str = None) -> None:
        """creates object"""
        if not isinstance(name, Name):
            name = Name(name)
        self.exec_mgr.execute(create_cmd(self.object_type, name, schema=schema))


@dataclass
class SchemaManager(BaseObjectManager):
    """Schema manager class"""

    object_type: str = field(default="schema", repr=False)
    object_col: str = field(default="table_schema", repr=False)

    def exists(self, name: str) -> bool:
        """checks if schema exists"""
        return name in [
            self.exec_mgr.fetchall(
                "select schema_name from information_schema.schemata"
            )
        ]

    def truncate(self, schema: Schema) -> None:
        """truncates schema"""
        return [
            self.exec_mgr.execute(truncate_table_cmd(name, schema=schema))
            for name in schema.tables
        ]


@dataclass
class TableManager(BaseObjectManager):
    """Table manager class"""

    object_type: str = field(default="table", repr=False)
    object_col: str = field(default="table_name", repr=False)
    schema: Schema = field(default=None, repr=False)

    def truncate(self, name: str, schema: str = None) -> None:
        """truncates table"""
        self.exec_mgr.execute(truncate_table_cmd(name, schema=schema))

    def drop_schema_tables(self) -> None:
        """drops all tables in schema"""
        self.drop(self.schema.name)
        self.create(self.schema.name)

    def drop_table_pattern(self, pattern: str) -> None:
        """drops tables matching pattern"""
        return [self.drop(table) for table in self.schema.tables if pattern in table]


@dataclass
class ViewManager(TableManager):
    """View manager class"""

    object_type: str = field(default="view", repr=False)

    # pylint: disable=arguments-renamed
    def create(self, name: str, sql: SQL) -> None:
        """makes view in database"""
        statement = mk_view_text(name, sql)
        return self.exec_mgr.execute(statement)


@dataclass
class ColumnManager(BaseObjectManager):
    """Column manager class"""

    object_type: str = field(default="column", repr=False)
    object_col: str = field(default="column_name", repr=False)
    table: Table = field(default=None, repr=False)


@dataclass
class BaseConnectionManager:
    """Connection manager class"""

    curl: Curl = field(repr=False, default=None)
    db_path: Path = field(repr=False, default=None)
    engine: Engine = field(init=False, repr=False)
    cnxn: Connection = field(init=False, repr=False)
    exec_mgr: ExecutionManager = field(init=False, repr=False)
    settings: Settings = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """sets attributes"""
        if self.curl is not None:
            self.engine = create_engine(self.curl)
            self.cnxn = self.engine.connect()
            self.exec_mgr = ExecutionManager(self.engine)
        else:
            raise ValueError("need curl for engine")

    def __del__(self) -> None:
        """closes connection"""
        if hasattr(self, "cnxn"):
            self.cnxn.close()
            del self.cnxn
        if hasattr(self, "engine"):
            self.engine.dispose()
            del self.exec_mgr

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

    exec_mgr: ExecutionManager = field(repr=False)
    schema_col: str = field(default="table_schema", repr=False)
    table_col: str = field(default="table_name", repr=False)

    @cached_property
    def info_schema_schemata(self) -> DataFrame:
        """gets info schema"""
        return self.exec_mgr.fetchdf("select * from information_schema.schemata")

    @cached_property
    def info_schema_tables(self) -> DataFrame:
        """gets info schema"""
        return self.exec_mgr.fetchdf("select * from information_schema.tables")

    @cached_property
    def info_schema_columns(self) -> DataFrame:
        """gets info schema"""
        return self.exec_mgr.fetchdf("select * from information_schema.columns")

    @cached_property
    def allschemas(self) -> list[str]:
        """gets list of schemas"""
        return self.info_schema_schemata[self.schema_col].tolist()

    def schema_exists(self, schema: str) -> bool:
        """checks if schema exists"""
        return schema in self.allschemas

    @cached_property
    def schema_tables(self) -> dict[str : list[str]]:
        """gets all schemas and tables"""
        return {
            schema: self.get_all_schema_tables(schema) for schema in self.allschemas
        }

    def get_record_count(self, schema: str, table: str) -> int:
        """gets record count for table"""
        sql = f"select count(*) from {schema}.{table}"
        return self.exec_mgr.fetchone(sql)

    @property
    def get_table_row_counts(self) -> dict[str : dict[str:int]]:
        """gets row counts for all tables"""
        return {
            schema: {table: self.get_record_count(schema, table) for table in tables}
            for schema, tables in self.schema_tables.items()
        }

    def table_exists(self, schema: str, table: str) -> bool:
        """checks if table exists"""
        try:
            return table in self.schema_tables[schema]
        except KeyError:
            return False

    def get_all_schema_tables(self, schema: str) -> list[str]:
        """gets all tables in schema"""
        return get_distinct_col_vals(self.schema_tables[schema], self.table_col)

    def get_last_val(self, schema: str, table: str, id_col: str, val_col: str) -> Any:
        """gets last value in column"""
        last_rec = self.get_last_record(schema, table, id_col)
        return last_rec.loc[0, val_col]

    def get_last_id(self, schema: str, table: str, id_col: str) -> int:
        """gets last id in table"""
        return self.get_last_val(schema, table, id_col, id_col)

    def get_last_record(
        self,
        schema: str,
        table: str,
        id_col: str,
    ) -> DataFrame:
        """gets last record in table"""
        last_id = self.get_last_id(schema, table, id_col)
        sql = f"select * from {schema}.{table} where {id_col} = {last_id}"
        return self.exec_mgr.fetchone(sql)


@dataclass
class DatabaseManager:
    """Database manager class"""

    cnxn_mgr: BaseConnectionManager = field(
        default_factory=BaseConnectionManager.from_env, repr=False
    )
    query_mgr: QueryManager = field(init=False, repr=False)
    exec_mgr: ExecutionManager = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """sets attributes"""
        self.exec_mgr = ExecutionManager(self.cnxn_mgr.engine)
        self.query_mgr = QueryManager(exec_mgr=self.exec_mgr)

    def __del__(self) -> None:
        """closes connection"""
        try:
            del self.query_mgr
        except AttributeError:
            info("no query manager")
        try:
            del self.exec_mgr
        except AttributeError:
            info("no execution manager")
        try:
            del self.cnxn_mgr
        except AttributeError:
            info("no connection manager")

    @classmethod
    def from_auth(cls, auth: str | tuple[str] | Auth) -> "DatabaseManager":
        """makes connection from auth"""
        auth = Auth(auth) if not isinstance(auth, Auth) else auth
        return cls(cnxn_mgr=BaseConnectionManager.from_auth(auth))

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
                for k, v in self.query_mgr.schema_tables.items()
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
                    rows = self.query_mgr.fetchone(sql)
                    print(f"\t{schema_}.{tbl} = {rows} rows")
                except UndefinedTable:
                    print(f"\t{schema_}.{tbl} = UndefinedTable")

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

    def get_df_from_sqlfile(self, path: Path) -> DataFrame:
        """gets dataframe from sql file"""
        return self.exec_mgr.fetchdf(SQL.from_path(path).clause)

    def df_to_db(self, df: DataFrame, schema: str, table: str, **kwargs) -> None:
        """writes dataframe to database"""
        df.to_sql(table, self.cnxn_mgr.engine, schema=schema, **kwargs)


@dataclass
class SQLiteFileManager:
    """SQLLite backup manager class"""

    db_path: Path = field()
    backup_path: str = field(default="backup.db", repr=False)
    db_cnxn: SQLiteConnection = field(init=False, repr=False)
    backup_cnxn: SQLiteConnection = field(init=False, repr=False)

    @property
    def ismemory(self) -> bool:
        """checks if database is in memory"""
        return self.db_path == ":memory:"

    def backup_database(self) -> None:
        """Backup the SQLite database to a specified path"""
        if self.ismemory:
            self.db_cnxn.backup(self.backup_path)
        else:
            copyfile(self.db_path, self.backup_path)

    def restore_database(self) -> None:
        """Backup the SQLite database to a specified path"""
        if self.ismemory:
            query = "".join(self.backup_cnxn.iterdump())
            self.db_cnxn.executescript(query)
        else:
            copyfile(self.backup_path, self.db_path)

    def __post_init__(self) -> None:
        """sets attributes"""
        self.db_cnxn = sqlite_connect(self.db_path)
        self.backup_cnxn = sqlite_connect(self.backup_path)

    def __del__(self) -> None:
        """closes connection"""
        self.db_cnxn.close()
        self.backup_cnxn.close()


@dataclass
class SQLiteManager(DatabaseManager):
    """SqlLite manager class"""

    db_path: str = field(default=":memory:")
    backup_path: str = field(default="backup.db", repr=False)
    cursor_obj: SQLiteCursor = field(default=SQLiteCursor, repr=False)
    cnxn: SQLiteConnection = field(init=False, repr=False)
    file_mgr: SQLiteFileManager = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """sets attributes"""
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        self.cnxn = self.engine.connect()
        self.file_mgr = SQLiteFileManager(self.db_path, self.backup_path)

    def check_integrity(self) -> bool:
        """Check the integrity of the SQLite database"""
        cursor = self.cnxn.cursor()
        cursor.execute("PRAGMA integrity_check")
        ret = cursor.fetchone()[0] == "ok"
        cursor.close()
        return ret


@dataclass
class MSSQLManager(DatabaseManager):
    """MSSQL manager class"""

    def __post_init__(self) -> None:
        self.engine = create_engine(self.cnxn_mgr.curl.mssql)
        if not database_exists(self.engine.url):
            create_database(self.engine.url)


@dataclass
class PostgresManager(DatabaseManager):
    """Postgres manager class"""

    def __post_init__(self) -> None:
        self.engine = create_engine(self.cnxn_mgr.curl.postgres)
        if not database_exists(self.engine.url):
            create_database(self.engine.url)

    @staticmethod
    def copy_csv_str(table_name: str, csv_path: Path) -> str:
        """generates a copy statement for a csv file"""
        return f"COPY {table_name} FROM '{csv_path}' DELIMITER ',' CSV HEADER"


@dataclass
class LocalETL:
    """executes etl stages locally"""

    remote_engine: Engine = field()
    resources_dir: Directory = field()
    landing_prefix: str = field(default="landing", repr=False)
    main_prefix: str = field(default="main", repr=False)
    localdb_name: str = field(default=":memory:")
    replace: tuple[str, str] = field(default=None, repr=False)

    @cached_property
    def localdb(self) -> SQLiteConnection:
        """returns sqlite connection"""
        return sqlite_connect(self.localdb_name)

    @property
    def cursor(self) -> Cursor:
        """returns sqlite cursor"""
        return self.localdb.cursor()

    def get_local_table(self, name: str) -> list[Any]:
        """gets table from local database"""
        return self.cursor.execute("select * from ?;", (name,)).fetchall()

    @cached_property
    def sql_files(self) -> list[File]:
        """returns list of sql files in resources directory"""
        return [x for x in self.resources_dir.filelist if x.name.endswith(".sql")]

    @property
    def file_prefixes(self) -> list[str]:
        """returns list of prefixes for sql files"""
        return list(set(x.path.stem.split("_")[0] for x in self.sql_files))

    @cached_property
    def landing_files(self) -> dict[str:File]:
        """returns dict of landing files"""
        return {
            "_".join(x.path.stem.split("_")[1:]): x
            for x in self.sql_files
            if x.name.startswith(self.landing_prefix)
        }

    @cached_property
    def main_files(self) -> dict[str:File]:
        """returns dict of main files"""
        return {
            "_".join(x.path.stem.split("_")[1:]): x
            for x in self.sql_files
            if x.name.startswith(self.main_prefix)
        }

    @cached_property
    def file_dict(self) -> dict[str : dict[str:File]]:
        """returns dict of file dicts"""
        return {
            prefix: {
                "_".join(x.path.stem.split("_")[1:]): x
                for x in self.sql_files
                if x.name.startswith(prefix)
            }
            for prefix in self.file_prefixes
        }

    @cached_property
    def table_dict(self) -> dict[str:File]:
        """returns dict of tables"""
        return {k: list(v) for k, v in self.file_dict.items()}

    @cached_property
    def landing_tables(self) -> list[str]:
        """returns list of landing tables"""
        return list(self.landing_files.keys())

    @cached_property
    def main_tables(self) -> list[str]:
        """returns list of main tables"""
        return list(self.main_files.keys())

    @staticmethod
    def get_data_dict(
        files: dict[str:File],
        engine: Engine | SQLiteConnection,
        replace: tuple[str, str] = None,
    ) -> dict[str:DataFrame]:
        """gets dataframes from files"""
        return get_dfs_threaded(files, engine, replace=replace)

    @cached_property
    def landing_data(self) -> dict[str:DataFrame]:
        """returns dict of landing data"""
        return get_dfs_threaded(
            self.landing_files, self.remote_engine, replace=self.replace
        )

    def get_main_data(self) -> dict[str:DataFrame]:
        """returns dict of main data"""
        return get_dfs_threaded(
            self.main_files,
            self.localdb,
            replace=self.replace,
        )

    @property
    def main_data(self) -> dict[str:DataFrame]:
        """returns dict of main data"""
        return self.get_main_data()

    @staticmethod
    def get_df_dict_lens(data_dict: dict[DataFrame]) -> dict[str:int]:
        """gets dict of dataframe lengths"""
        return {k: len(v) for k, v in data_dict.items()}

    @cached_property
    def landing_lens(self) -> dict[str:int]:
        """returns dict of landing dataframe lengths"""
        return LocalETL.get_df_dict_lens(self.landing_data)

    @property
    def main_lens(self) -> dict[str:int]:
        """returns dict of main dataframe lengths"""
        return LocalETL.get_df_dict_lens(self.main_data)

    @staticmethod
    def insert_table(
        name: str,
        df: DataFrame,
        cnxn: SQLiteConnection,
        index: bool = False,
        if_exists: str = "replace",
    ) -> None:
        """inserts dataframe into database"""
        df.to_sql(name, cnxn, index=index, if_exists=if_exists)

    # pylint: disable=expression-not-assigned
    @staticmethod
    def insert_data(
        data_dict: dict[str:DataFrame],
        cnxn: SQLiteConnection,
        index: bool = False,
        if_exists: str = "replace",
    ) -> None:
        """inserts data into database"""
        [
            LocalETL.insert_table(
                name, data, cnxn=cnxn, index=index, if_exists=if_exists
            )
            for name, data in data_dict.items()
        ]

    def insert_landing_data(self, **kwargs) -> None:
        """inserts landing data into database"""
        try:
            LocalETL.insert_data(
                self.landing_data,
                self.localdb,
                **kwargs,
            )
        except AttributeError:
            self.insert_landing_data(**kwargs)

    def steps(self) -> None:
        """executes etl steps"""
        self.insert_landing_data()
        return self.main_data

    @staticmethod
    def to_csv(data_dict: dict[str:DataFrame], dirpath: Path | Directory) -> None:
        """writes dataframes to csv"""
        if isinstance(dirpath, Directory):
            path = dirpath.path
        elif isinstance(dirpath, Path):
            path = dirpath
        else:
            raise TypeError(f"got {dirpath} but need path/directory")
        env = chkenv("environment", need=None)
        if env:
            env = env + "_"
        else:
            env = ""
        for name, df in data_dict.items():
            csv_path = path / (env + name + ".csv")
            df.to_csv(csv_path, index=False)

    def main_to_csv(self, dirpath: Path | Directory) -> None:
        """writes main data to csv"""
        LocalETL.to_csv(self.main_data, dirpath)

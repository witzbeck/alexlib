"""
This Python module provides a comprehensive collection of classes and functions for managing and manipulating SQL databases and data. It includes functionalities for interacting with databases using SQLAlchemy and psycopg, handling data with Pandas, and various utilities for file and directory management. Key features include:

1. SQL Wrappers: Classes for managing SQL queries and connections, including the creation of views, execution of queries, and handling of data transfer between databases.
2. Data Handling: Functions for converting SQL queries to Pandas DataFrames, handling CSV files, and managing data in local SQLite databases.
3. ETL Processes: A framework for executing Extract-Transform-Load (ETL) processes locally, including handling SQL files, transforming data, and loading it into a specified database.
4. Utility Functions: A collection of utility functions for file manipulation, data processing, and SQL statement generation.

The module is designed to be versatile and efficient for data scientists and database administrators, facilitating complex data operations and database management tasks.
"""
from dataclasses import dataclass
from dataclasses import field
from functools import cached_property
from os import environ
from pathlib import Path
from queue import Queue
from random import choice
from sqlite3 import connect as lite_connect
from sqlite3 import Connection as LiteConnection
from sqlite3 import Cursor
from string import ascii_letters
from string import digits
from subprocess import PIPE
from subprocess import Popen
from threading import Thread
from typing import Any
from typing import Optional

from pandas import DataFrame
from pandas import read_sql
from pandas import Series
from psycopg import connect as pg_connect
from psycopg import Connection as PGConnection
from psycopg.errors import DuplicateSchema
from psycopg.errors import ProgrammingError
from psycopg.errors import UndefinedTable
from sqlalchemy import create_engine
from sqlalchemy import CursorResult
from sqlalchemy import Engine
from sqlalchemy import TextClause
from sqlalchemy.sql import text
from sqlalchemy_utils import create_database
from sqlalchemy_utils import database_exists

from alexlib.auth import Auth
from alexlib.auth import Curl
from alexlib.core import chkenv
from alexlib.core import ping
from alexlib.df import get_distinct_col_vals
from alexlib.df import series_col
from alexlib.files import Directory
from alexlib.files import File
from alexlib.files import path_search

SQL_CHARS = f"{ascii_letters} _{digits}"
QG_SUBS = {
    " ": "_",
    "-": "_",
    "#": "NUMBER",
    "&": "AND",
    "/": "_",
    "%": "PERCENT",
    ".": "",
}
QG_KEYS = list(QG_SUBS.keys())


def mk_devs(n: int = 1) -> list[str]:
    """makes list of dev names"""
    return [f"dev{x}" if n > 1 else "dev" for x in ascii_letters[-n:]]


def mk_envs(ndevs: list[str]) -> list[str]:
    """makes list of env names"""
    return mk_devs(ndevs) + ["test", "prod"]


@dataclass
class SQL:
    """wrapper for sqlalchemy TextClause"""

    text: str = field()
    toclip: bool = field(default=True)

    @property
    def isstr(self) -> bool:
        """checks if text is a string"""
        return isinstance(self.text, str)

    def __post_init__(self) -> None:
        """adds query to clipboard if toclip is True"""
        if self.toclip:
            self.to_clipboard(self.text)

    @property
    def clause(self) -> TextClause:
        """returns sqlalchemy TextClause"""
        return text(self.text)

    @staticmethod
    def to_clipboard(txt: str) -> bool:
        """copies text to clipboard"""

        with Popen(["pbcopy"], stdin=PIPE) as p:
            p.stdin.write(txt.encode())
            p.stdin.close()
            retcode = p.wait()
        return retcode == 0

    @staticmethod
    def mk_default_filename(
        schema: str, table: str, prefix: str = "select", suffix: str = ".sql"
    ) -> str:
        """makes filename from schema and table"""
        return f"{prefix}_{schema}_{table}{suffix}"

    @staticmethod
    def to_file(txt: str, path: Path, overwrite: bool = True) -> None:
        """writes text to file"""
        if path.exists() and not overwrite:
            raise FileExistsError("file already exists here. overwrite?")
        path.write_text(txt)

    @classmethod
    def from_info_schema(
        cls,
        schema: str,
        table: str,
        info_schema: DataFrame,
    ):
        """makes select * from table query from info_schema"""
        abrv = get_table_abrv(table)
        lines = ["select\n"]
        cols = list(info_schema.loc[:, "column_name"])
        for i, col in enumerate(cols):
            if i == 0:
                comma = " "
            else:
                comma = ","
            line = f"{comma}{abrv}.{col}\n"
            lines.append(line)
        lines.append(f"from {schema}.{table} {abrv}")
        return cls("".join(lines))

    @staticmethod
    def create_onehot_view(
        df: DataFrame,
        id_col: str,
        dist_col: str,
        schema: str,
        table: str,
        command: str = "create view",
    ) -> str:
        """creates onehot view from dataframe"""
        dist_col = [x for x in df.columns if x[-2:] != "id"][0]
        id_col = [x for x in df.columns if x != dist_col][0]
        dist_vals = get_distinct_col_vals(df, dist_col)

        first_line = f"{command} {schema}.v_{table}_onehot as select\n"
        lines = [first_line]
        lines.append(f" {id_col}\n")
        lines.append(f",{dist_col}\n")

        for val in dist_vals:
            new_col = f"is_{val}".replace(" ", "_")
            new_col = new_col.replace("%", "_percent")
            new_col = new_col.replace("-", "_")
            new_col = new_col.replace("<", "_less")
            new_col = new_col.replace("=", "_equal")
            new_col = new_col.replace(">", "_greater")
            case_stmt = onehot_case(dist_col, val)
            lines.append(f",{case_stmt} {new_col}\n")
        lines.append(f"from {schema}.{table}")
        return "".join(lines)


def execute_query(
    name: str,
    file: File,
    engine: Engine,
    result_queue: Queue = None,
    replace: tuple[str, str] = None,
) -> None:
    """executes query and puts result in queue"""
    print(f"getting {name}")
    df = file.get_df(eng=engine, replace=replace)
    res = {name: df}
    result_queue.put(res)
    print(f"got {name}")
    return result_queue


def get_dfs_threaded(
    files: dict[str:File],
    engine: Engine | LiteConnection,
    replace: tuple[str, str] = None,
) -> dict[str:DataFrame]:
    """gets dataframes from files"""
    if isinstance(engine, Engine):
        result_queue = Queue()
        threads = [
            Thread(
                target=execute_query,
                args=[name, file, engine],
                kwargs={"result_queue": result_queue, "replace": replace},
            )
            for name, file in files.items()
        ]
        _ = [thread.start() for thread in threads]
        results = {}
        while not result_queue.empty() or len(results) < len(files):
            results.update(result_queue.get())
        ret = results
    else:
        ret = {
            name: file.get_df(eng=engine, replace=replace)
            for name, file in files.items()
        }
    return ret


def get_data_dict_series(
    files: dict[str:File],
    engine: Engine | LiteConnection,
    replace: tuple[str, str] = None,
) -> dict[str:DataFrame]:
    """gets dataframes from files"""
    return {
        name: file.get_df(
            eng=engine,
            replace=replace,
        )
        for name, file in files.items()
    }


@dataclass
class Connection:
    """wrapper for sqlalchemy engine"""

    curl: Curl = field(repr=False, default=None)
    schema_col: str = field(default="table_schema", repr=False)
    table_col: str = field(default="table_name", repr=False)
    engine: Engine = field(repr=False, init=False)

    @property
    def hascurl(self) -> bool:
        """checks if curl is not None"""
        return self.curl is not None

    @property
    def pg_cnxn(self) -> PGConnection:
        """returns psycopg connection"""
        return pg_connect(self.curl.postgres)

    def __post_init__(self) -> None:
        """creates sqlalchemy engine"""
        self.engine = create_engine(str(self.curl))

    @property
    def isopen(self) -> bool:
        """checks if connection is open"""
        if not self.curl.canping:
            raise ValueError("need host and port to ping")
        return ping(self.curl.host, self.curl.port)

    @staticmethod
    def mk_view_text(name: str, sql: str) -> str:
        """makes create view text"""
        return f"CREATE VIEW {name} AS {sql};"

    @staticmethod
    def get_clause(
        sql: SQL | str | TextClause,
        asstr: bool = True,
    ) -> TextClause | str:
        """gets sqlalchemy TextClause from various inputs"""
        if isinstance(sql, Path):
            sql = Connection.get_clause(sql.read_text())
        elif isinstance(sql, File):
            sql = Connection.get_clause(sql.text)
        elif isinstance(sql, SQL):
            sql = sql.text
        elif isinstance(sql, str):
            sql = text(sql)
        if asstr:
            return str(sql)
        return sql

    # pylint: disable=raise-missing-from
    def execute(
        self,
        sql: SQL | str | TextClause | Path | File,
        fetch: bool | int = False,
    ) -> CursorResult:
        """executes sql"""
        clause = Connection.get_clause(sql)
        if ";" in clause:
            for part in clause.split(";"):
                if part:
                    self.execute(part, fetch=fetch)
        with self.pg_cnxn as cnxn:
            cnxn.autocommit = True
            with cnxn.cursor() as cursor:
                try:
                    cursor.execute(clause.encode("utf-8"))
                except UnicodeDecodeError:
                    cursor.execute(clause.encode())
                except UndefinedTable as e:
                    raise UndefinedTable(f"{e} - {clause}")
                if fetch == 1 and isinstance(fetch, int):
                    ret = cursor.fetchone()[0]
                elif fetch and isinstance(fetch, int):
                    ret = cursor.fetchmany(fetch)
                elif fetch:
                    ret = cursor.fetchall()
                if fetch:
                    return ret

    def get_df(self, sql: SQL | str | TextClause) -> DataFrame:
        """gets dataframe from sql"""
        clause = Connection.get_clause(sql)
        return read_sql(clause, self.engine)

    def mk_view(self, name: str, sql: str) -> None:
        """makes view in database"""
        statement = Connection.mk_view_text(name, sql)
        return self.execute(statement)

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
            engine = self.engine
        if not isinstance(schema, str):
            schema = str(schema)
        df = file.get_df(engine=engine)
        df.to_sql(
            table,
            self.engine,
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
        df = sqlfile.get_df(eng=self.engine)
        return File.df_to_file(df, writepath)

    def update_test_files(
        self,
        sql_files: list[File],
        test_paths: list[Path],
    ) -> None:
        """updates test files"""
        for i, sqlfile in enumerate(sql_files):
            self.sql_to_file(sqlfile, test_paths[i])

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
        return cls(str(curl))

    @classmethod
    def from_auth(
        cls,
        auth: str | tuple[str] | Auth,
    ):
        """makes connection from auth"""
        if not isinstance(auth, Auth):
            auth = Auth(auth)
        return cls(curl=auth.curl)

    @property
    def dbexists(self) -> bool:
        """checks if database exists"""
        if self.curl.database is None:
            return False
        return database_exists(str(self.curl))

    def create_db(self) -> None:
        """creates database"""
        if self.dbexists:
            print(f"database[{self.curl.database}] already exists")
        elif self.curl.database is None:
            raise ValueError("dbname is None")
        else:
            create_database(str(self.curl))

    def get_info_schema(
        self,
        schema: str = None,
        table: str = None,
    ) -> DataFrame:
        """gets information schema"""
        sql = mk_info_sql(schema=schema, table=table)
        return self.get_df(sql)

    @property
    def info_schema(self) -> DataFrame:
        """gets information schema"""
        return self.get_info_schema()

    def run_pg_sql(
        self,
        sql: SQL,
        todf: bool = True,
    ) -> DataFrame | bool:
        """runs sql using postgres connection"""
        isselect = "select" in sql.lower()[:10]
        with self.pg_cnxn as cnxn:
            cnxn.autocommit = True
            cursor = cnxn.cursor()
            cursor.execute(sql)
            if isselect:
                ret = cursor.fetchall()
            if isselect and todf:
                cols = [desc[0] for desc in cursor.description]
                df = DataFrame.from_records(ret)
                df.columns = cols
                ret = df
            elif not isselect:
                ret = True
            else:
                raise ProgrammingError("invalid sql")
            return ret

    @property
    def allschemas(self) -> list[str]:
        """gets all schemas"""
        return get_distinct_col_vals(self.info_schema, self.schema_col)

    def schema_exists(self, schema: str) -> bool:
        """checks if schema exists"""
        return schema in self.allschemas

    @property
    def schema_tables(self) -> dict[str : list[str]]:
        """gets all schemas and tables"""
        return {
            schema: self.get_all_schema_tables(schema) for schema in self.allschemas
        }

    def show_row_counts(
        self,
        schema: Optional[str],
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
                    rows = self.execute(sql, fetch=1)
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

    @property
    def alltables(self) -> list[str]:
        """gets all tables"""
        return get_distinct_col_vals(self.info_schema, self.table_col)

    @staticmethod
    def mk_cmd_sql(
        cmd: str, obj_type: str, obj_name: str, schema: str = None, addl_cmd: str = ""
    ) -> None:
        """makes sql for object commands"""
        if obj_type not in ["table", "view"]:
            name = obj_name
        elif schema is None:
            name = obj_name
        else:
            name = f"{schema}.{obj_name}"
        return f"{cmd} {obj_type} {name} {addl_cmd};"

    def obj_cmd(self, *args, **kwargs) -> None:
        """runs object command"""
        sql = Connection.mk_cmd_sql(*args, **kwargs)
        self.run_pg_sql(sql)

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
        info = self.get_info_schema(schema=schema)
        table_col = "table_name"
        return get_distinct_col_vals(info, table_col)

    def truncate_schema(self, schema: str) -> None:
        """truncates all tables in schema"""
        tabs = self.get_all_schema_tables(schema)
        for tab in tabs:
            self.truncate_table(schema, tab)

    def df_from_sqlfile(self, filename: str, path: Path = None) -> DataFrame:
        """gets dataframe from sql file"""
        if path is None:
            path = path_search(filename)
        return self.execute(path.read_text(), fetch=True)

    # pylint: disable=unspecified-encoding
    def run_sqlfile(self, path: Path) -> DataFrame:
        """runs sql file"""
        if not isinstance(path, Path):
            path = Path(path)
        if not path.exists():
            raise FileExistsError(path)
        return self.run_pg_sql(path.read_text())

    def df_to_db(self, df: DataFrame, schema: str, table: str, **kwargs) -> None:
        """writes dataframe to database"""
        if schema not in self.allschemas:
            try:
                self.create_schema(schema)
            except DuplicateSchema:
                pass
        df.to_sql(table, self.engine, schema=schema, **kwargs)

    @staticmethod
    def mk_star_select(
        schema: str,
        table: str,
        addl_sql: str = "",
        nrows: int = -1,
    ) -> SQL:
        """makes select * from table sql"""
        if nrows is None:
            rows = ""
        elif nrows <= 0:
            rows = ""
        else:
            rows = f"limit {str(nrows)}"
        sql = f"select * from {schema}.{table} "
        parts = [sql, addl_sql, rows, ";"]
        return SQL("".join(parts))

    def mk_query(
        self,
        schema: str,
        table: str,
    ) -> SQL:
        """makes select * from table sql"""
        info = self.get_info_schema(schema=schema, table=table)
        return SQL.from_info_schema(schema, table, info)

    def get_table(
        self,
        schema: str,
        table: str,
        nrows: int = -1,
    ) -> DataFrame:
        """gets table from database"""
        sql = Connection.mk_star_select(schema, table, nrows=nrows)
        return self.get_df(sql)

    def get_last_id(
        self,
        schema: str,
        table: str,
        id_col: str,
    ) -> int:
        """gets last id in table"""
        sql = f"select max({id_col}) from {schema}.{table}"
        try:
            id_int = self.run_pg_sql(sql).iloc[0, 0]
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
        return self.execute(sql, fetch=1)

    def get_record_count(self, schema: str, table: str, print_: bool = True) -> int:
        """gets record count for table"""
        sql = f"select count(*) from {schema}.{table};"
        val = self.run_pg_sql(sql).values[0][0]
        if print_:
            print(f"{schema}.{table} record count: {val}")
        return val

    def get_last_val(
        self,
        schema: str,
        table: str,
        id_col: str,
        val_col: str,
    ) -> Any:
        """gets last value in column"""
        last_rec = self.get_last_record(schema, table, id_col)
        return last_rec.loc[0, val_col]

    @classmethod
    def from_db(cls, dbname: str, **kwargs):
        """makes connection from database name"""
        environ["DBNAME"] = dbname
        return cls(**kwargs)


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
    def localdb(self) -> LiteConnection:
        """returns sqlite connection"""
        return lite_connect(self.localdb_name)

    @property
    def cursor(self) -> Cursor:
        """returns sqlite cursor"""
        return self.localdb.cursor()

    def get_local_table(self, name: str) -> list[Any]:
        """gets table from local database"""
        return self.cursor.execute(f"select * from {name};").fetchall()

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
        engine: Engine | LiteConnection,
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
        cnxn: LiteConnection,
        index: bool = False,
        if_exists: str = "replace",
    ) -> None:
        """inserts dataframe into database"""
        df.to_sql(name, cnxn, index=index, if_exists=if_exists)

    # pylint: disable=expression-not-assigned
    @staticmethod
    def insert_data(
        data_dict: dict[str:DataFrame],
        cnxn: LiteConnection,
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


def onehot_case(col: str, val: str) -> str:
    """makes case statement for onehot encoding"""
    return f"case when {col} = '{val}' then 1 else 0 end"


def get_table_abrv(table_name: str) -> str:
    """gets table abbreviation"""
    parts = table_name.split("_")
    firsts = [x[0] for x in parts]
    return "".join(firsts)


def mk_info_sql(
    schema=None, table=None, sql="select * from information_schema.columns"
) -> str:
    """makes information schema sql"""
    hasschema = schema is not None
    hastable = table is not None
    hasboth = hasschema and hastable
    haseither = hasschema or hastable
    stext = f"table_schema = '{schema}'" if hasschema else ""
    ttext = f"table_name = '{table}'" if hastable else ""
    sqllist = [
        sql,
        "where" if haseither else "",
        stext,
        "and" if hasboth else "",
        ttext,
    ]
    return " ".join(sqllist)


@dataclass
class Column:
    """wrapper for db column as pandas series"""

    name: str = field()
    table: str = field()
    schema: str = field()
    series: Series = field(repr=False)

    def __len__(self) -> int:
        """returns length of series"""
        return len(self.series)

    @cached_property
    def distvals(self) -> list[str]:
        """returns list of distinct values in series"""
        return list(self.series.unique())

    @property
    def ndistvals(self) -> int:
        """returns number of distinct values in series"""
        return len(self.distvals)

    @cached_property
    def frequencies(self) -> dict[str:int]:
        """returns dict of distinct values and frequencies"""
        return {x: sum(self.series == x) for x in self.distvals}

    @cached_property
    def proportions(self) -> dict[str:float]:
        """returns dict of distinct values and proportions"""
        freqs = self.frequencies
        n = len(self)
        return {x: freqs[x] / n for x in self.distvals}

    @property
    def isid(self) -> bool:
        """checks if column is id"""
        return self.name.lower().endswith("_id")

    @property
    def nnulls(self) -> int:
        """returns number of nulls in series"""
        return sum(self.series.isna())


@dataclass
class Table:
    """wrapper for db table as pandas dataframe"""

    cnxn: Connection = field()
    schema: str = field()
    table: str = field()
    df: DataFrame = field(
        default=None,
        repr=False,
    )
    nrows: int = field(default=None)
    col_series: DataFrame = field(
        init=False,
        repr=False,
    )
    col_objs: DataFrame = field(
        init=False,
        repr=False,
    )

    @property
    def cols(self) -> list[str]:
        """returns list of column names"""
        return list(self.df.columns)

    @property
    def ncols(self) -> int:
        """returns number of columns"""
        return len(self.cols)

    def get_col_series(self) -> dict[str:Series]:
        """returns dict of column names and series"""
        return {x: series_col(self.df, x) for x in self.cols}

    def set_col_series(self) -> None:
        """sets dict of column names and series"""
        self.col_series = self.get_col_series()

    def get_col_objs(self) -> dict[str:Column]:
        """returns dict of column names and column objects"""
        s, t, c, n = self.schema, self.table, self.col_series, self.cols
        return {x: Column(s, t, x, c[x]) for x in n}

    def set_col_objs(self) -> None:
        """sets dict of column names and column objects"""
        self.col_objs = self.get_col_objs()

    def head(self, x: int) -> DataFrame:
        """returns head of dataframe"""
        return self.df.head(x)

    @property
    def rand_col(self) -> Column:
        """returns random column"""
        return choice(self.cols)

    def __post_init__(self) -> None:
        """sets attributes"""
        self.df = self.cnxn.get_table(self.schema, self.table)
        self.set_col_series()
        self.set_col_objs()

    @classmethod
    def from_df(
        cls,
        df: DataFrame,
        context: str,
        schema: str,
        table: str,
    ):
        """makes table from dataframe"""
        return cls(context, schema, table, df=df)


def update_host_table(
    schema: str,
    table: str,
    source: Connection,
    dest: Connection,
) -> None:
    """updates table on host"""
    source_data = source.get_table(schema, table)
    if len(source_data) == 0:
        raise ValueError("source is empty")
    try:
        dest.truncate_table(schema, table)
    except UndefinedTable:
        pass
    source_data.to_sql(
        table,
        dest.engine,
        schema=schema,
        if_exists="append",
        index=False,
        method="multi",
    )


def update_host_schema(
    schema: str,
    source_cnxn: Connection,
    dest_cnxn: Connection,
) -> None:
    """updates schema on host"""
    schema_tables = source_cnxn.get_all_schema_tables(schema)
    for table in schema_tables:
        update_host_table(schema, table, source=source_cnxn, dest=dest_cnxn)

from dataclasses import dataclass, field
from functools import cached_property
from queue import Queue
from sqlite3 import Connection as LiteConnection, Cursor
from sqlite3 import DatabaseError, connect as lite_connect
from string import ascii_letters, digits
from threading import Thread
from typing import Any
from os import environ
from subprocess import Popen, PIPE
from random import choice
from pathlib import Path

from pandas import read_sql, DataFrame, Series
from psycopg import connect as pg_connect, Connection as PGConnection
from psycopg.errors import UndefinedTable, ProgrammingError
from psycopg.errors import DuplicateSchema
from sqlalchemy import CursorResult, TextClause, create_engine, Engine
from sqlalchemy.sql import text
from sqlalchemy_utils import database_exists, create_database

from alexlib.auth import Curl, Auth
from alexlib.core import chkenv, ping
from alexlib.df import get_distinct_col_vals, series_col
from alexlib.files import path_search, File, Directory

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
    return [f"dev{x}" if n > 1 else "dev" for x in ascii_letters[-n:]]


def mk_envs(ndevs: list[str]) -> list[str]:
    return mk_devs(ndevs) + ["test", "prod"]


@dataclass
class SQL:
    text: str = field()
    toclip: bool = field(default=True)

    @property
    def isstr(self):
        return isinstance(self.text, str)

    def __post_init__(self):
        if self.toclip:
            self.to_clipboard(self.text)

    @property
    def clause(self) -> TextClause:
        return text(self.text)

    @staticmethod
    def to_clipboard(text: str):
        p = Popen(["pbcopy"], stdin=PIPE)
        p.stdin.write(text.encode())
        p.stdin.close()
        retcode = p.wait()
        return True if retcode == 0 else False

    @staticmethod
    def mk_default_filename(
        schema: str, table: str, prefix: str = "select", suffix: str = ".sql"
    ) -> str:
        return f"{prefix}_{schema}_{table}{suffix}"

    @staticmethod
    def to_file(text: str, path: Path, overwrite: bool = True) -> bool:
        if path.exists() and not overwrite:
            raise FileExistsError("file already exists here. overwrite?")
        path.write_text(text)
        return path.exists()

    @classmethod
    def from_info_schema(
        cls,
        schema: str,
        table: str,
        info_schema: DataFrame,
    ):
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

    def create_onehot_view(
        df: DataFrame,
        id_col: str,
        dist_col: str,
        schema: str,
        table: str,
        command: str = "create view",
    ) -> str:
        dist_col = [x for x in df.columns if x[-2:] != "id"][0]
        id_col = [x for x in df.columns if x != dist_col][0]
        dist_vals = get_distinct_col_vals(df, dist_col)

        first_line = f"{command} {schema}.v_{table}_onehot as select\n"
        lines = [first_line]
        lines.append(f" {id_col}\n")
        lines.append(f",{dist_col}\n")

        for i in range(len(dist_vals)):
            com = ","
            val = dist_vals[i]
            new_col = f"is_{val}".replace(" ", "_")
            new_col = new_col.replace("%", "_percent")
            new_col = new_col.replace("-", "_")
            new_col = new_col.replace("<", "_less")
            new_col = new_col.replace("=", "_equal")
            new_col = new_col.replace(">", "_greater")
            case_stmt = onehot_case(dist_col, val)
            lines.append(f"{com}{case_stmt} {new_col}\n")
        lines.append(f"from {schema}.{table}")
        return "".join(lines)


def execute_query(
    name: str,
    file: File,
    engine: Engine,
    result_queue: Queue = None,
    replace: tuple[str, str] = None,
) -> None:
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
    if isinstance(engine, Engine):
        result_queue = Queue()
        threads = [
            Thread(
                target=execute_query,
                args=[name, file, engine],
                kwargs=dict(result_queue=result_queue, replace=replace),
            )
            for name, file in files.items()
        ]
        [thread.start() for thread in threads]
        results = {}
        while not result_queue.empty() or len(results) < len(files):
            results.update(result_queue.get())
        return results
    else:
        return {
            name: file.get_df(eng=engine, replace=replace)
            for name, file in files.items()
        }


def get_data_dict_series(
    files: dict[str:File],
    engine: Engine | LiteConnection,
    replace: tuple[str, str] = None,
) -> dict[str:DataFrame]:
    return {
        name: file.get_df(
            eng=engine,
            replace=replace,
        )
        for name, file in files.items()
    }


@dataclass
class Connection:
    curl: Curl = field(repr=False, default=None)
    schema_col: str = field(default="table_schema", repr=False)
    table_col: str = field(default="table_name", repr=False)
    engine: Engine = field(repr=False, init=False)

    @property
    def hasauth(self) -> bool:
        return isinstance(self.auth, Auth)

    @property
    def hascurl(self) -> bool:
        return self.curl is not None

    @property
    def pg_cnxn(self) -> PGConnection:
        return pg_connect(self.curl.postgres)

    def __post_init__(self) -> None:
        self.engine = create_engine(str(self.curl))

    @property
    def isopen(self) -> bool:
        if not self.curl.canping:
            raise ValueError("need host and port to ping")
        return ping(self.curl.host, self.curl.port)

    @staticmethod
    def mk_view_text(name: str, sql: str) -> str:
        return f"CREATE VIEW {name} AS {sql};"

    @staticmethod
    def get_clause(
        sql: SQL | str | TextClause,
        asstr: bool = True,
    ) -> TextClause | str:
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

    def execute(
        self,
        sql: SQL | str | TextClause | Path | File,
        fetch: bool | int = False,
    ) -> CursorResult:
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
        clause = Connection.get_clause(sql)
        return read_sql(clause, self.engine)

    def mk_view(self, name: str, sql: str):
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
        df = sqlfile.get_df(eng=self.engine)
        return File.df_to_file(df, writepath)

    def update_test_files(
        self,
        sql_files: list[File],
        test_paths: list[Path],
    ):
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
        driver: str = "pyodbc",
        sid: str = None,
    ):
        curl = Curl(
            username=username,
            password=password,
            host=host,
            port=port,
            database=database,
            dialect=dialect,
            driver=driver,
            sid=sid,
        )
        return cls(str(curl))

    @classmethod
    def from_auth(
        cls,
        auth: str | tuple[str] | Auth,
    ):
        if not isinstance(auth, Auth):
            auth = Auth(auth)
        return cls(curl=auth.curl)

    @property
    def dbexists(self) -> bool:
        if self.curl.database is None:
            return False
        return database_exists(str(self.curl))

    def create_db(self) -> None:
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
        sql = mk_info_sql(schema=schema, table=table)
        return self.get_df(sql)

    @property
    def info_schema(self) -> DataFrame:
        return self.get_info_schema()

    def run_pg_sql(
        self,
        sql: SQL,
        todf: bool = True,
    ) -> DataFrame | bool:
        isselect = "select" in sql.lower()[:10]
        # text = Connection.mk_text(sql)
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
        return get_distinct_col_vals(self.info_schema, self.schema_col)

    def schema_exists(self, schema: str) -> bool:
        return schema in self.allschemas

    @property
    def schema_tables(self) -> dict[str : list[str]]:
        return {
            schema: self.get_all_schema_tables(schema) for schema in self.allschemas
        }

    def show_row_counts(
        self,
        schema: str | list[str] | None = None,
        table: str | list[str] | None = None,
        system_schemas: bool = False,
    ) -> None:
        d = {k: v for k, v in self.schema_tables.items()}
        if not system_schemas:
            d = {
                k: v
                for k, v in d.items()
                if k not in ["information_schema", "pg_catalog"]
            }
        if isinstance(schema, str):
            schema = [schema]
        if schema:
            d = {k: v for k, v in d.items() if k in schema}

        for schema, tables in d.items():
            print(schema)
            if isinstance(table, str):
                tables = [table]
            if table:
                tables = [tbl for tbl in tables if tbl in table]
            for tbl in tables:
                try:
                    sql = f'SELECT count(*) FROM {schema}."{tbl}"'
                    rows = self.execute(sql, fetch=1)
                    print(f"\t{schema}.{tbl} = {rows} rows")
                except UndefinedTable:
                    print(f"\t{schema}.{tbl} = UndefinedTable")

    @property
    def table_rows(self) -> dict[str : dict[str:int]]:
        return {
            schema: {
                table: self.get_record_count(schema, table, print_=False)
                for table in tables
            }
            for schema, tables in self.schema_tables.items()
        }

    def table_exists(self, schema: str, table: str) -> bool:
        try:
            return table in self.schema_tables[schema]
        except KeyError:
            return False

    @property
    def alltables(self) -> list[str]:
        return get_distinct_col_vals(self.info_schema, self.table_col)

    @staticmethod
    def mk_cmd_sql(
        cmd: str, obj_type: str, obj_name: str, schema: str = None, addl_cmd: str = ""
    ) -> None:
        if obj_type not in ["table", "view"]:
            name = obj_name
        elif schema is None:
            name = obj_name
        else:
            name = f"{schema}.{obj_name}"
        return f"{cmd} {obj_type} {name} {addl_cmd};"

    def obj_cmd(self, *args, **kwargs) -> None:
        sql = Connection.mk_cmd_sql(*args, **kwargs)
        self.run_pg_sql(sql)

    def create_schema(self, schema: str) -> None:
        try:
            self.obj_cmd("create", "schema", schema)
        except DuplicateSchema:
            print(f"schema[{schema}] already exists")

    def drop_schema(self, schema: str) -> None:
        self.obj_cmd("drop", "schema", schema, addl_cmd="cascade")

    def drop_all_schema_tables(self, schema: str) -> None:
        self.drop_schema(schema)
        self.create_schema(schema)

    def drop_table(self, schema: str, table: str, cascade: bool = True) -> None:
        addl_cmd = "cascade" if cascade else ""
        self.obj_cmd("drop", "table", table, schema=schema, addl_cmd=addl_cmd)

    def drop_table_pattern(
        self,
        pattern: str,
        schema: str,
        cascade: bool = True,
    ) -> None:
        [
            self.drop_table(schema, tab, cascade=cascade)
            for tab in self.get_all_schema_tables(schema)
            if pattern in tab
        ]

    def drop_view(self, schema: str, view: str) -> None:
        self.obj_cmd("drop", "view", view, schema=schema)

    def truncate_table(self, schema: str, table: str) -> None:
        if table.startswith("v_"):
            pass
        else:
            self.obj_cmd("truncate", "table", table, schema=schema)

    def get_all_schema_tables(self, schema: str) -> list[str]:
        info = self.get_info_schema(schema=schema)
        table_col = "table_name"
        return get_distinct_col_vals(info, table_col)

    def truncate_schema(self, schema: str) -> None:
        tabs = self.get_all_schema_tables(schema)
        for tab in tabs:
            self.truncate_table(schema, tab)

    def df_from_sqlfile(self, filename: str, path: Path = None) -> DataFrame:
        if path is None:
            path = path_search(filename)
        text = path.read_text()
        return self.run_pd_sql(text)

    def run_sqlfile(
        self,
        path: Path,
    ) -> DataFrame:
        if not isinstance(path, Path):
            path = Path(path)
        if not path.exists():
            raise FileExistsError(path)
        text = path.read_text()
        return self.run_pg_sql(text)

    def df_to_db(self, df: DataFrame, schema: str, table: str, **kwargs) -> None:
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
        info = self.get_info_schema(schema=schema, table=table)
        return SQL.from_info_schema(schema, table, info)

    def get_table(
        self,
        schema: str,
        table: str,
        nrows: int = -1,
    ) -> DataFrame:
        sql = Connection.mk_star_select(schema, table, nrows=nrows)
        return self.get_df(sql)

    def get_last_id(
        self,
        schema: str,
        table: str,
        id_col: str,
    ) -> int:
        sql = f"select max({id_col}) from {schema}.{table}"
        try:
            id = self.run_pg_sql(sql)
            id_int = id.iloc[0, 0]
            if id_int is None:
                return 1
            else:
                return int(id_int)
        except UndefinedTable:
            return 1

    def get_next_id(self, *args) -> int:
        return self.get_last_id(*args) + 1

    def get_last_record(
        self,
        schema: str,
        table: str,
        id_col: str,
    ) -> DataFrame:
        last_id = self.get_last_id(schema, table, id_col)
        sql = f"select * from {schema}.{table} where {id_col} = {last_id}"
        return self.run_pd_query(sql)

    def get_record_count(self, schema: str, table: str, print_: bool = True) -> int:
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
        last_rec = self.get_last_record(schema, table, id_col)
        return last_rec.loc[0, val_col]

    @classmethod
    def from_context(cls, context: str, createdb: bool = False, **kwargs):
        return cls(
            context=context,
            createdb=createdb,
            **kwargs,
        )

    @classmethod
    def from_db(cls, dbname: str, **kwargs):
        environ["DBNAME"] = dbname
        return cls(**kwargs)


@dataclass
class LocalETL:
    remote_engine: Engine = field()
    resources_dir: Directory = field()
    landing_prefix: str = field(default="landing", repr=False)
    main_prefix: str = field(default="main", repr=False)
    localdb_name: str = field(default=":memory:")
    replace: tuple[str, str] = field(default=None, repr=False)

    @cached_property
    def localdb(self) -> LiteConnection:
        return lite_connect(self.localdb_name)

    @property
    def cursor(self) -> Cursor:
        return self.localdb.cursor()

    def get_local_table(self, name: str) -> list[Any]:
        return self.cursor.execute(f"select * from {name};").fetchall()

    @cached_property
    def sql_files(self) -> list[File]:
        return [x for x in self.resources_dir.filelist if x.name.endswith(".sql")]

    @property
    def file_prefixes(self) -> list[str]:
        return list(set([x.path.stem.split("_")[0] for x in self.sql_files]))

    @cached_property
    def landing_files(self) -> dict[str:File]:
        return {
            "_".join(x.path.stem.split("_")[1:]): x
            for x in self.sql_files
            if x.name.startswith(self.landing_prefix)
        }

    @cached_property
    def main_files(self) -> dict[str:File]:
        return {
            "_".join(x.path.stem.split("_")[1:]): x
            for x in self.sql_files
            if x.name.startswith(self.main_prefix)
        }

    @cached_property
    def file_dict(self) -> dict[str : dict[str:File]]:
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
        return {k: [x for x in v] for k, v in self.file_dict.items()}

    @cached_property
    def landing_tables(self) -> list[str]:
        return list(self.landing_files.keys())

    @cached_property
    def main_tables(self) -> list[str]:
        return list(self.main_files.keys())

    @staticmethod
    def get_data_dict(
        files: dict[str:File],
        engine: Engine | LiteConnection,
        replace: tuple[str, str] = None,
    ) -> dict[str:DataFrame]:
        return get_dfs_threaded(files, engine, replace=replace)

    @cached_property
    def landing_data(self) -> dict[str:DataFrame]:
        return get_dfs_threaded(
            self.landing_files, self.remote_engine, replace=self.replace
        )

    def get_main_data(self) -> dict[str:DataFrame]:
        return get_dfs_threaded(
            self.main_files,
            self.localdb,
            replace=self.replace,
        )

    @property
    def main_data(self) -> dict[str:DataFrame]:
        try:
            return self.get_main_data()
        except DatabaseError as e:
            raise NotImplementedError(f"{e} - landing data not inserted")

    @staticmethod
    def get_df_dict_lens(data_dict: dict[DataFrame]) -> dict[str:int]:
        return {k: len(v) for k, v in data_dict.items()}

    @cached_property
    def landing_lens(self) -> dict[str:int]:
        return LocalETL.get_df_dict_lens(self.landing_data)

    @property
    def main_lens(self) -> dict[str:int]:
        return LocalETL.get_df_dict_lens(self.main_data)

    @staticmethod
    def insert_table(
        name: str,
        df: DataFrame,
        cnxn: LiteConnection,
        index: bool = False,
        if_exists: str = "replace",
    ) -> None:
        df.to_sql(name, cnxn, index=index, if_exists=if_exists)

    @staticmethod
    def insert_data(
        data_dict: dict[str:DataFrame],
        cnxn: LiteConnection,
        index: bool = False,
        if_exists: str = "replace",
    ) -> None:
        [
            LocalETL.insert_table(
                name, data, cnxn=cnxn, index=index, if_exists=if_exists
            )
            for name, data in data_dict.items()
        ]

    def insert_landing_data(self, **kwargs):
        try:
            LocalETL.insert_data(
                self.landing_data,
                self.localdb,
                **kwargs,
            )
        except AttributeError:
            self.insert_landing_data(**kwargs)

    def steps(self):
        self.insert_landing_data()
        return self.main_data

    @staticmethod
    def to_csv(data_dict: dict[str:DataFrame], dirpath: Path | Directory) -> None:
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
        LocalETL.to_csv(self.main_data, dirpath)


def onehot_case(col: str, val: str):
    return f"case when {col} = '{val}' then 1 else 0 end"


def get_table_abrv(table_name: str):
    parts = table_name.split("_")
    firsts = [x[0] for x in parts]
    return "".join(firsts)


def mk_info_sql(
    schema=None, table=None, sql="select * from information_schema.columns"
) -> str:
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
    name: str = field()
    table: str = field()
    schema: str = field()
    series: Series = field(repr=False)
    distvals: list[str] = field(init=False, repr=False)
    freqs: dict[list[float]] = field(init=False, repr=False)
    props: dict[list[float]] = field(init=False, repr=False)

    def __len__(self) -> int:
        return len(self.series)

    def get_distvals(self):
        return list(self.series.unique())

    def set_distvals(self):
        self.distvals = self.get_distvals()

    def get_ndistvals(self):
        return len(self.distvals)

    def set_ndistvals(self):
        self.ndistvals = self.get_ndistvals()

    def get_freqs(self):
        return {x: sum(self.series == x) for x in self.distvals}

    def set_freqs(self):
        self.freqs = self.get_freqs()

    def get_props(self):
        freqs = self.freqs
        n = len(self)
        return {x: freqs[x] / n for x in self.distvals}

    def set_props(self):
        self.props = self.get_props()

    def __post_init__(self):
        self.set_distvals()
        self.set_ndistvals()
        self.set_freqs
        self.set_props()

    @property
    def isid(self):
        return False if self.name[-3:] != "_id" else True

    @property
    def nnulls(self):
        return sum(self.series.isna())


@dataclass
class Table:
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
    def cols(self):
        return list(self.df.columns)

    @property
    def ncols(self):
        return len(self.cols)

    def get_col_series(self):
        return {x: series_col(self.df, x) for x in self.cols}

    def set_col_series(self):
        self.col_series = self.get_col_series()

    def get_col_objs(self):
        s, t, c, n = self.schema, self.table, self.col_series, self.cols
        self.col_objs = {x: Column(s, t, x, c[x]) for x in n}

    def set_col_objs(self):
        self.col_objs = self.get_col_objs()

    def head(self, x: int) -> DataFrame:
        return self.df.head(x)

    @property
    def rand_col(self) -> Column:
        return choice(self.cols)

    def __post_init__(self) -> None:
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
        return cls(context, schema, table, df=df)

    @classmethod
    def from_context(
        cls,
        context: str,
        schema: str,
        table: str,
    ):
        c = Connection.from_context(context)
        df = c.get_table(schema, table)
        return cls(
            context,
            schema,
            table,
            df=df,
        )


def update_host_table(
    schema: str,
    table: str,
    source: str | Connection = "SERVER",
    dest: str | Connection = "LOCAL",
):
    if isinstance(source, str):
        source = Connection.from_context(source)
    elif isinstance(source, Connection):
        pass
    else:
        raise TypeError("source must be str or Connection")
    if isinstance(dest, str):
        dest = Connection.from_context(dest)
    elif isinstance(dest, Connection):
        pass
    else:
        raise TypeError("dest must be str or Connection")

    source_data = source.get_table(schema, table)
    if len(source_data) == 0:
        raise ValueError("source is empty")
    else:
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
    schema: str, source_context: str = "SERVER", dest_context: str = "LOCAL"
):
    source = Connection.from_context(source_context)
    dest = Connection.from_context(dest_context)
    schema_tables = source.get_all_schema_tables(schema)
    for table in schema_tables:
        update_host_table(schema, table, source=source, dest=dest)

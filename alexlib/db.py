from dataclasses import dataclass, field
from functools import cached_property
from queue import Queue
from sqlite3 import Connection as LiteConnection, Cursor
from sqlite3 import DatabaseError, connect as s3_connect
from string import ascii_letters, digits
from threading import Thread
from typing import Any
from os import environ
from subprocess import Popen, PIPE
from random import choice
from pathlib import Path

from pandas import read_sql, DataFrame, Series
from psycopg import connect as pg_connect
from psycopg.errors import UndefinedTable, ProgrammingError
from psycopg.errors import DuplicateSchema
from sqlalchemy import create_engine, Engine
from sqlalchemy.sql import text
from sqlalchemy_utils import database_exists, create_database

from alexlib.auth import Curl
from alexlib.core import chkenv, ping
from alexlib.config import ConfigFile
from alexlib.df import get_distinct_col_vals, series_col
from alexlib.file import path_search, File, Directory

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
    curl: Curl = field(
        repr=False,
    )
    engine: Engine = field(
        repr=False,
        init=False,
    )

    def __post_init__(self) -> None:
        if isinstance(self.curl, Curl):
            self.curl = str(self.curl)
        self.engine = create_engine(self.curl)

    @property
    def canping(self):
        return not (self.curl.host is None or self.curl.port is None)

    @property
    def isopen(self) -> bool:
        if not self.canping:
            raise ValueError("need host and port to ping")
        return ping(self.host, self.port)

    @staticmethod
    def mk_view_text(name: str, sql: str):
        return f"""CREATE VIEW {name} AS {sql}"""

    def get_df(self, sql: str) -> DataFrame:
        """plugs connection and sql into pandas to produce dataframe"""
        statement = text(sql)
        with self.engine.connect() as con:
            return read_sql(statement, con)

    def get_table(
        self,
        table: str,
        schema: str = None,
        db: str = None,
    ) -> DataFrame:
        tbl = ".".join([x for x in [db, schema, table] if x])
        return self.get_df(f"select * from {tbl}")

    def exe_sql(self, sql: str):
        statement = text(sql)
        with self.engine.connect() as con:
            return con.execute(statement)

    def mk_view(self, name: str, sql: str):
        statement = Connection.mk_view_text(name, sql)
        return self.exe_sql(statement)

    def file_to_db(
        self,
        file: File,
        schema: str,
        table: str,
        eng: Engine = None,
        if_exists: str = "replace",
    ) -> None:
        if file.issql:
            eng = self.engine
        df = file.get_df(eng=eng)
        df.to_sql(table, self.engine, schema=schema, if_exists=if_exists)

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
        return s3_connect(self.localdb_name)

    @property
    def cursor(self) -> Cursor:
        return self.localdb.cursor()

    def get_local_table(self, name: str) -> list[Any]:
        return self.cursor.execute(f"select * from {name};").fetchall()

    @cached_property
    def sql_files(self) -> list[File]:
        return [
            x for x in self.resources_dir.filelist
            if x.name.endswith(".sql")
        ]

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
    def to_csv(
        data_dict: dict[str:DataFrame],
        dirpath: Path | Directory
    ) -> None:
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
    def astext(self):
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


@dataclass
class ConnectionMP:
    context: str = field(default="LOCAL")
    driver: str = field(default="postgresql+psycopg://")
    engine: str = field(repr=False, default=None)
    createdb: bool = field(
        default=False,
        repr=False,
    )
    dotenv_name: str = field(
        default=".env",
        repr=False,
    )

    def get_context(self):
        if self.context is None:
            return chkenv("CONTEXT")
        else:
            return self.context

    def set_context(self, context: str):
        self.context = context

    @property
    def dbname(self):
        return chkenv("DBNAME", required=False)

    @property
    def issudo(self):
        return chkenv("ISSUDO", type=bool, required=False)

    @property
    def usertype(self):
        return "SUDO" if self.issudo else "USER"

    @property
    def host(self):
        try:
            ret = chkenv(f"{self.context}DBHOST")
        except ValueError:
            ret = chkenv("DBHOST")
        return ret

    @property
    def port(self):
        try:
            ret = chkenv(f"{self.context}DBPORT")
        except ValueError:
            ret = chkenv("DBPORT")
        return ret

    @property
    def user(self):
        return chkenv(f"{self.context}DB{self.usertype}")

    @property
    def pw(self):
        return chkenv(f"{self.context}DBPW")

    @property
    def login(self):
        return self.user if self.pw is None else f"{self.user}:{self.pw}"

    @property
    def enginestr(self):
        h, p = self.host, self.port
        return f"{self.driver}{self.login}@{h}:{p}/{self.dbname}"

    @staticmethod
    def get_engine(enginestr):
        return create_engine(enginestr)

    def set_engine(self):
        self.engine = Connection.get_engine(self.enginestr)

    @staticmethod
    def mk_text(sql: SQL):
        if isinstance(sql, SQL):
            ret = sql.text
        elif isinstance(sql, str):
            ret = text(sql)
        else:
            raise TypeError("sql must be SQL or str")
        return ret

    def run_pd_sql(self, sql: SQL):
        if self.engine is None:
            self.set_engine()
        text = Connection.mk_text(sql)
        return read_sql(text, self.engine)

    @property
    def connstr(self):
        deets = [
            f"dbname={self.dbname}",
            f"host={self.host}",
            f"port={self.port}",
            f"user={self.user}",
        ]
        if self.pw is not None:
            deets.append(f"password={self.pw}")
        return " ".join(deets)

    @property
    def conn(self):
        return pg_connect(self.connstr)

    @property
    def dbexists(self):
        if self.dbname is None:
            return False
        return database_exists(self.enginestr)

    def create_db(self):
        if self.dbexists:
            raise ValueError("database already exists")
        elif self.dbname is None:
            raise ValueError("dbname is None")
        elif self.createdb:
            create_database(self.enginestr)
        else:
            raise ValueError("createdb is False")

    def get_info_schema(
        self,
        schema: str = None,
        table: str = None,
    ):
        sql = mk_info_sql(schema=schema, table=table)
        return self.run_pd_sql(sql)

    @property
    def info_schema(self):
        return self.get_info_schema()

    def run_pg_sql(
        self,
        sql: SQL,
        todf: bool = True,
    ) -> DataFrame | bool:
        isselect = "select" in sql.lower()[:10]
        # text = Connection.mk_text(sql)
        with self.conn as cnxn:
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

    def __post_init__(self) -> None:
        if self.dbname is None:
            ConfigFile(name=self.dotenv_name)
        if self.createdb and not self.dbexists:
            self.create_db()

    @property
    def allschemas(self):
        return get_distinct_col_vals(self.info_schema, "table_schema")

    @property
    def alltables(self):
        return get_distinct_col_vals(self.info_schema, "table_name")

    @staticmethod
    def mk_cmd_sql(
        cmd: str,
        obj_type: str,
        obj_name: str,
        schema: str = None,
        addl_cmd: str = ""
    ) -> None:
        if obj_type not in ["table", "view"]:
            name = obj_name
        elif schema is None:
            name = obj_name
        else:
            name = f"{schema}.{obj_name}"
        return f"{cmd} {obj_type} {name} {addl_cmd};"

    def obj_cmd(self, *args, **kwargs):
        sql = Connection.mk_cmd_sql(*args, **kwargs)
        self.run_pg_sql(sql)

    def create_schema(self, schema: str):
        self.obj_cmd("create", "schema", schema)

    def drop_table(self, schema: str, table: str, cascade: bool = True):
        addl_cmd = "cascade" if cascade else ""
        self.obj_cmd("drop", "table", table, schema=schema, addl_cmd=addl_cmd)

    def drop_view(self, schema: str, view: str):
        self.obj_cmd("drop", "view", view, schema=schema)

    def truncate_table(self, schema: str, table: str) -> None:
        if table.startswith("v_"):
            pass
        else:
            self.obj_cmd("truncate", "table", table, schema=schema)

    def get_all_schema_tables(self, schema: str):
        info = self.get_info_schema(schema=schema)
        table_col = "table_name"
        return get_distinct_col_vals(info, table_col)

    def truncate_schema(self, schema: str):
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

    def df_to_db(
        self,
        df: DataFrame,
        schema: str,
        table: str,
        **kwargs
    ) -> None:
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
    ):
        info = self.get_info_schema(schema=schema, table=table)
        return SQL.from_info_schema(schema, table, info)

    def get_table(
        self,
        schema: str,
        table: str,
        nrows: int = -1,
    ) -> DataFrame:
        sql = Connection.mk_star_select(schema, table, nrows=nrows)
        return self.run_pd_sql(sql)

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

    def get_record_count(
        self,
        schema: str,
        table: str,
        print_: bool = True
    ) -> int:
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
    def from_db(
        cls,
        dbname: str,
        **kwargs,
    ):
        environ["DBNAME"] = dbname
        return cls(**kwargs)


@dataclass
class Column:
    name: str = field()
    table: str = field()
    schema: str = field()
    series: Series = field(
        repr=False,
    )
    distvals: list[str] = field(
        init=False,
        repr=False,
    )
    freqs: dict[list[float]] = field(
        init=False,
        repr=False,
    )
    props: dict[list[float]] = field(
        init=False,
        repr=False,
    )

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


if __name__ == "__main__":
    c = Connection()
    print(c.info_schema)

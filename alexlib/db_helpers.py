# standard library imports
from math import log, sqrt
from os import getenv
from pathlib import Path
from subprocess import Popen, PIPE
from typing import Any

# third party imports
from matplotlib.pyplot import xticks, subplots
from numpy.random import choice
from pandas import read_sql, DataFrame, Series
from psycopg2 import connect
from psycopg2.errors import UndefinedTable, ProgrammingError
from seaborn import histplot
from sqlalchemy import create_engine

from utils import get_distinct_col_vals, get_props, series_col
from utils import set_envs, filter_df, pathsearch

set_envs("db")

if getenv("CONTEXT") is None:
    set_envs("model")


def onehot_case(col: str, val: str):
    return f"case when {col} = '{val}' then 1 else 0 end"


def pyth(_list: list):
    return sqrt(sum([x ** 2 for x in _list]))


def get_deets(context: str):
    context = context.upper()
    dbname = "DBNAME"
    vars = ["DBHOST", "DBPORT", "DBSUDO"]
    deets = [dbname] + [context + x for x in vars]
    deets = [getenv(x) for x in deets]
    return deets[0], deets[1], deets[2], deets[3]


def create_conn(dbname: str,
                host: str,
                port: str,
                user: bool,
                pw: str = None
                ):
    dbname = f"dbname={dbname}"
    host = f"host={host}"
    port = f"port={port}"
    user = f"user={user}"
    deets = [dbname, host, port, user]
    if pw is not None:
        deets.append(f"password={pw}")
    con_str = " ".join(deets)
    return connect(con_str)


def get_conn(context: str):
    return create_conn(*get_deets(context))


def build_engine(dbname: str,
                 host: str,
                 port: str,
                 user: bool,
                 pw: str = None
                 ):
    pre_sqlalc = "postgresql+psycopg2://"
    post_sqlalc = f"@{host}:{port}/{dbname}"
    if pw is None:
        login = user
    else:
        login = f"{user}:{pw}"

    con_str = pre_sqlalc + login + post_sqlalc
    return create_engine(con_str)


def get_engine(context: str):
    return build_engine(*get_deets(context))


def get_table_abrv(table_name: str):
    parts = table_name.split("_")
    firsts = [x[0] for x in parts]
    return "".join(firsts)


class DbHelper:
    def generate_select_query(self,
                              schema: str,
                              table: str,
                              destination: Path = "clipboard",
                              overwrite: bool = False
                              ) -> Path:
        df = self.get_info_schema(schema=schema, table=table)
        if len(df) == 0:
            raise ValueError("object does not exist")
        abrv = get_table_abrv(table)

        lines = ["select\n"]

        cols = list(df.loc[:, "column_name"])
        for i, col in enumerate(cols):
            if i == 0:
                comma = " "
            else:
                comma = ","
            line = f"{comma}{abrv}.{col}\n"
            lines.append(line)
        lines.append(f"from {schema}.{table} {abrv}")
        text = "".join(lines)

        if destination == "clipboard":
            p = Popen(["pbcopy"], stdin=PIPE)
            p.stdin.write(text.encode())
            p.stdin.close()
            retcode = p.wait()
            return True if retcode == 0 else False
        else:
            filename = f"select_{schema}_{table}.sql"
            filepath = destination / filename

            if (filepath.exists() and not overwrite):
                raise FileExistsError("file already exists here. overwrite?")
            filepath.write_text(text)
            return filepath

    def get_info_schema(self,
                        schema=None,
                        table=None):
        sql = "select * from main.v_info_schema"
        if (schema is not None and table is None):
            sql = f"{sql} where table_schema = '{schema}'"
        elif (schema is not None and table is not None):
            sql = f"{sql} where table_schema = '{schema}'"
            sql = f"{sql} and table_name = '{table}'"
        elif (schema is None and table is not None):
            sql = f"{sql} where table_name = '{table}'"
        return read_sql(sql, self.engine)

    def __init__(self, context: str) -> None:
        set_envs("db")
        self.context = context
        self.db_name = getenv("DBNAME")
        self.engine = get_engine(context)
        self.info_schema = self.get_info_schema()

    def run_postgres_query(self, query):
        with get_conn(self.context) as cnxn:
            cnxn.autocommit = True
            cursor = cnxn.cursor()
            cursor.execute(query)
            if query[:6].lower() != "select":
                return True
            try:
                res = cursor.fetchall()
                cols = [desc[0] for desc in cursor.description]
                df = DataFrame.from_records(res)
                df.columns = cols
                return df
            except ProgrammingError:
                return False

    def obj_cmd(self,
                cmd: str,
                obj_type: str,
                obj_schema: str,
                obj_name: str,
                addl_cmd: str = ""
                ) -> None:
        sql = f"{cmd} {obj_type} {obj_schema}.{obj_name} {addl_cmd};"
        self.run_postgres_query(sql)

    def drop_table(self, schema: str, table: str, cascade: bool = True):
        if cascade:
            self.obj_cmd("drop", "table", schema, table, addl_cmd="cascade")
        else:
            self.obj_cmd("drop", "table", schema, table)

    def drop_view(self, schema: str, view: str):
        self.obj_cmd("drop", "view", schema, view)

    def trunc_table(self, schema: str, table: str):
        self.obj_cmd("truncate", "table", schema, table)

    def get_all_schema_tables(self, schema: str):
        info = self.info_schema
        table_col = "table_name"
        schema_col = "table_schema"
        schema_tabs = filter_df(info, schema_col, schema)
        schema_tabs = filter_df(schema_tabs, "table_type", "BASE TABLE")
        return get_distinct_col_vals(schema_tabs, table_col)

    def trunc_schema(self, schema: str):
        tabs = self.get_all_schema_tables(schema)
        for tab in tabs:
            self.trunc_table(schema, tab)

    def run_pd_query(self, query: str):
        return read_sql(query, self.engine)

    def df_from_file(self,
                     filename: str,
                     path: Path = None
                     ):
        if path is None:
            path = pathsearch(filename)
        text = path.read_text()
        return self.run_pd_query(text)

    def df_to_db(self,
                 df: DataFrame,
                 schema: str,
                 table: str,
                 **kwargs
                 ):
        df.to_sql(table,
                  self.engine,
                  schema=schema,
                  **kwargs)

    def get_table(self,
                  schema: str,
                  table: str,
                  nrows: int = None
                  ):
        query = f"select * from {schema}.{table}"
        if (nrows is not None and nrows != 'None'):
            query = f"{query} limit {str(nrows)};"
        return self.run_pd_query(query)

    def get_last_id(self,
                    schema: str,
                    table: str,
                    id_col: str,
                    ) -> int:
        sql = f"select max({id_col}) from {schema}.{table}"
        try:
            id = self.run_postgres_query(sql)
            id_int = id.iloc[0, 0]
            if id_int is None:
                return 1
            else:
                return int(id_int)
        except UndefinedTable:
            return 1

    def get_next_id(self, *args) -> int:
        return self.get_last_id(*args) + 1

    def get_last_record(self,
                        schema: str,
                        table: str,
                        id_col: str,
                        ) -> DataFrame:
        last_id = self.get_last_id(schema, table, id_col)
        sql = f"select * from {schema}.{table} where {id_col} = {last_id}"
        return self.run_pd_query(sql)

    def get_last_val(self,
                     schema: str,
                     table: str,
                     id_col: str,
                     val_col: str,
                     ) -> Any:
        last_rec = self.get_last_record(schema, table, id_col)
        return last_rec.loc[0, val_col]


def create_onehot_view(dbh: DbHelper,
                       schema: str,
                       table: str,
                       command: str = "create view"
                       ) -> str:
    df = dbh.run_pd_query(f"select * from {schema}.{table}")
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


class Column:
    def is_id(col: str):
        return False if col[-3:] != "_id" else True

    def auto_xtick_angle(self,
                         ndist_min: int = 5,
                         ndist_mult: int = 2,
                         len_min: int = 50,
                         len_mult: int = 2,
                         range_min: int = 100,
                         range_mult: int = 2,
                         text_min: int = 30,
                         text_mult: int = 2
                         ):
        uni = list(self.series.unique())
        self.ndist = len(uni)
        if self.ndist < ndist_min:
            return 0
        self.ndist_prod = ndist_mult * self.ndist

        text_len = sum([len(str(x)) for x in uni])
        if text_len > text_min:
            logtext = log(text_len)
            self.text_prod = text_mult * logtext
        else:
            return 0

        _len = len(self.series)
        if _len > len_min:
            _len = log(_len)
            self.len_prod = len_mult * _len
        else:
            self.len_prod = 0

        freq_range = max(self.freqs) - min(self.freqs)
        if freq_range > range_min:
            _range = log(freq_range)
        else:
            _range = 0
        self.logrange_prod = range_mult * _range

        to_pyth = [
            self.len_prod,
            self.ndist_prod,
            self.logrange_prod,
            self.text_prod
        ]
        angle = int(pyth(to_pyth))
        if angle > 45:
            return 45
        else:
            return angle

    def __init__(self,
                 schema: str,
                 table: str,
                 col_name: str,
                 series: Series,
                 calc_desc: bool = False
                 ) -> None:
        self.schema = schema
        self.table = table
        self.col_name = col_name
        self.series = series
        self.is_id = Column.is_id(self.col_name)

    def desc(self,
             show_props: bool = False,
             show_nulls: bool = False,
             show_series_desc: bool = False,
             show_hist: bool = False,
             **kwargs
             ):
        try:
            to_pyth = [
                self.len_prod,
                self.ndist_prod,
                self.logrange_prod,
                self.text_prod
            ]
        except AttributeError:
            pass
        db_col = self.col_name
        if self.schema is not None:
            db_col = f"{self.schema}.{self.table}.{db_col}"
        print(f"Describing {db_col}\n")
        if (ndist := len(list(self.series.unique()))) < 31:
            self.props = get_props(self.series)
            self.freqs = self.props["frequency"].values
            self.distvals = self.props["value"].values
            self.n_vals = sum(self.freqs)
            if show_props:
                print("Proportions:\n", self.props, "\n")
        if show_nulls:
            self.n_nulls = sum(self.series.isna())
            print(f"Null count: {self.n_nulls}")
        if show_series_desc:
            print(self.series.describe(), "\n")
        if (show_hist and not self.is_id and ndist <= 31):
            try:
                print([round(x, 4) for x in to_pyth])
            except AttributeError:
                pass
            except UnboundLocalError:
                pass
            self.xtick_angle = self.auto_xtick_angle()
        else:
            self.xtick_angle = 0
        if show_hist:
            fig, ax = subplots(nrows=1,
                               ncols=1,
                               figsize=(5, 4),
                               dpi=200,
                               )
            histplot(self.series,
                     ax=ax,
                     **kwargs
                     )
            xticks(rotation=self.xtick_angle)
            return fig, ax


class Table:
    def set_cols(self):
        self.col_names = self.df.columns
        self.ncols = len(self.col_names)
        self.col_series = {x: series_col(self.df, x) for x in self.col_names}
        s, t, c = self.schema, self.table, self.col_series
        d, n = self.calc_desc, self.col_names
        self.cols = {x: Column(s, t, x, c[x], calc_desc=d) for x in n}

    def set_funcs(self):
        self.rand_col = lambda: choice(list(self.cols.values()))
        self.head = lambda x: self.df.head(x)

    def __init__(self,
                 context: str,
                 schema: str,
                 table: str,
                 calc_desc: bool = False,
                 df: DataFrame = None,
                 nrows: int = None
                 ) -> None:
        self.schema = schema
        self.table = table
        if df is None:
            dbh = DbHelper(context)
            self.df = dbh.get_table(schema, table, nrows=nrows)
        else:
            self.df = df
        self.calc_desc = calc_desc
        self.set_cols()
        self.set_funcs()

    def desc_col(self, col: str, **kwargs):
        col = self.cols[col]
        col.desc(**kwargs)

    def desc_all_cols(self):
        for i, col in enumerate(self.col_names):
            print(f"({i+1}/{self.ncols})")
            self.desc_col(col, show_hist=False)

    @classmethod
    def from_df(cls,
                df: DataFrame,
                calc_desc: bool = False,
                context: str = None,
                schema: str = None,
                table: str = None,
                ):
        return cls(context, schema, table, calc_desc=calc_desc, df=df)


def update_host_table(schema: str,
                      table: str,
                      source_context: str = "SERVER",
                      dest_context: str = "LOCAL"
                      ):
    source_dbh: str = DbHelper(source_context),
    dest_dbh: str = DbHelper(dest_context)
    trunc_sql = f"truncate table {schema}.{table};"
    new_data = source_dbh.get_table(schema, table)
    if len(new_data) == 0:
        raise ValueError("did not grab data from source")
    else:
        try:
            dest_dbh.run_postgres_query(trunc_sql)
        except UndefinedTable:
            pass
        new_data.to_sql(
            table,
            dest_dbh.engine,
            schema=schema,
            if_exists="append",
            index=False,
            method="multi"
        )


def update_host_schema(schema: str,
                       source_context: str = "SERVER",
                       dest_context: str = "LOCAL"
                       ):
    source_dbh: str = DbHelper(source_context),
    dest_dbh: str = DbHelper(dest_context)

    schema_tables = source_dbh.get_all_schema_tables(schema)
    for table in schema_tables:
        update_host_table(
            schema,
            table,
            source_dbh=source_dbh,
            dest_dbh=dest_dbh
        )

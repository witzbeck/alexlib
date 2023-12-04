from datetime import datetime
from functools import partial
from typing import Any

from pandas import DataFrame, Series, to_datetime
from sqlalchemy import Engine

from alexlib.iters import rm_pattern


def add_col(
    df: DataFrame,
    col: str,
    val: Any
) -> DataFrame:
    df.loc[:, col] = val
    return df


add_timestamp_col = partial(
    add_col,
    col="datetime",
    val=datetime.now(),
)


def col_pair_to_dict(
    col1: str,
    col2: str,
    df: DataFrame
) -> dict:
    pairs = df.loc[:, [col1, col2]].to_dict("records")
    return {p[col1]: p[col2] for p in pairs}


def get_row_as_list(idx: int, df: DataFrame) -> list[Any]:
    return df.iloc[idx, :].values.tolist()


def get_rows_as_list(df: DataFrame) -> list[list]:
    rng = range(len(df))
    return [get_row_as_list(i, df) for i in rng]


def filter_df(
    df: DataFrame,
    col: str,
    val: Any
) -> DataFrame:
    if not isinstance(df, DataFrame):
        raise TypeError(f"{df} not {DataFrame}")
    return df[df.loc[:, col] == val]


def get_val_order(
    df: DataFrame,
    order_col: str,
    order_val: str | int | float,
    filter_col: str,
    filter_val: str | int | float,
):
    filtered_df = filter_df(
        df,
        filter_col,
        filter_val
    )
    series_list = filtered_df.loc[:, order_col].to_list()
    return series_list.index(order_val)


def get_unique_col_vals(
        col: str,
        df: DataFrame | list[DataFrame]
        ) -> list:
    """ gets unique vals from col in df
        inputs:
            col = column of interest to find unique values
            df = dataframe containing column
        returns:
            val_list = list of unique values
    """
    if isinstance(df, DataFrame):
        vals = df.loc[:, col].unique()         # str from slice
    elif isinstance(df, dict):
        vals = get_unique_col_vals(col, list(df.values()))
    elif isinstance(df, list):
        func = get_unique_col_vals
        vals_list = [func(col, d) for d in df]
        vals = set(chain.from_iterable(vals_list))
    else:
        raise TypeError("need df or list of dfs")
    return list(vals)


def make_unique_dict(
    key_col: str,
    df: DataFrame
) -> dict[str: Any]:
    """ creates a dict of slices from df using the unique vals from 1 col
        inputs:
            col = column of interest to use as keys
            df = dataframe
        returns:
            out_dict = dict of slices
    """
    return {
        key: filter_df(df, key_col, key)
        for key in get_unique_col_vals(key_col, df)
    }


def col_vals_to_dict(df: DataFrame,
                     key_col: str,
                     val_col: str
                     ):
    d = df.loc[:, [key_col, val_col]]
    recs = d.to_dict(orient="records")
    return {x[key_col]: x[val_col] for x in recs}


def ts_col_to_dt(
    df: DataFrame,
    ts_col: str,
    dt_col: str,
) -> DataFrame:
    col = df.loc[:, ts_col]
    df.loc[:, dt_col] = to_datetime(col)
    return df


def set_type_list(
    df: DataFrame,
    type: Any,
    cols: list[str]
) -> DataFrame:
    for col in cols:
        df.loc[:, col] = df.loc[:, col].astype(type)
    return df


def drop_invariate_cols(df: DataFrame):
    return df.loc[:, (df.iloc[0]).any()]


def split_df(
        df: DataFrame,
        ratio: float,
        head: bool = True
) -> DataFrame:
    to = int(len(df) * ratio)
    if head:
        return df.head(to)
    else:
        return df.tail(to)


def filter_df(df: DataFrame, col: str, val: str):
    return df[df.loc[:, col] == val]


def series_col(df: DataFrame, col: str):
    return Series(df.loc[:, col])


def get_distinct_col_vals(df: DataFrame, col: str):
    return list(df.loc[:, col].unique())


def rm_df_col_pattern(pattern: str | tuple | list,
                      df: DataFrame,
                      end: bool = True
                      ) -> DataFrame:
    isstr = isinstance(pattern, str)
    cols = df.columns
    if isstr and end:
        new_cols = rm_pattern(cols, pattern)
    elif isstr:
        new_cols = rm_pattern(cols, pattern, end=False)
    elif isinstance(pattern, tuple):
        new_pattern = pattern[0]
        end = pattern[-1]
        new_cols = rm_pattern(cols, new_pattern, end=end)
    elif isinstance(pattern, list):
        for pat in pattern:
            df = rm_df_col_pattern(pat, df)
        return df
    else:
        raise ValueError("input not recognized")
    return df.loc[:, new_cols]


def df_to_db(
    df: DataFrame,
    engine: Engine,
    table_name: str,
    schema: str = None,
    if_exists: str = "replace",
    index: bool = False,
    chunksize: int = 10000,
    method: str = "multi",
):
    df.to_sql(
        table_name,
        engine,
        if_exists=if_exists,
        schema=schema,
        index=index,
        chunksize=chunksize,
        method=method,
    )

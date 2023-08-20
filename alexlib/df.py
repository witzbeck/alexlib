from functools import partial
from typing import Any

from pandas import DataFrame, Series
from pandas import Timestamp, to_datetime


def add_col(
        df: DataFrame,
        col: str,
        val: Any
) -> DataFrame:
    df.loc[:, col] = val
    return df


add_timestamp_col = partial(
    col="datetime",
    val=Timestamp.now()
)


def col_pair_to_dict(
        col1: str,
        col2: str,
        df: DataFrame
) -> dict:
    pairs = df.loc[:, [col1, col2]].to_dict("records")
    return {p[col1]: p[col2] for p in pairs}


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

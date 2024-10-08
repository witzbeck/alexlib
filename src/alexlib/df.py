"""
This module provides a collection of functions designed for manipulating pandas DataFrames,
including adding columns, converting data types, filtering, and interacting with databases using SQLAlchemy.

Functions:
- add_col: Adds a new column to a DataFrame with a specified value.
- add_timestamp_col: Adds a timestamp column to a DataFrame using a partial function.
- col_pair_to_dict: Converts a pair of columns from a DataFrame into a dictionary.
- get_row_as_list: Retrieves a specific row from a DataFrame as a list.
- get_rows_as_list: Converts all rows of a DataFrame into a list of lists.
- filter_df: Filters a DataFrame based on a specified column's value.
- get_val_order: Determines the order of a value in a filtered DataFrame.
- get_unique_col_vals: Extracts unique values from a specified column in a DataFrame.
- make_unique_dict: Creates a dictionary from a DataFrame based on unique values of a specified column.
- col_vals_to_dict: Converts specified column values of a DataFrame into a dictionary.
- ts_col_to_dt: Converts a timestamp column in a DataFrame to datetime.
- set_type_list: Sets the data type for a list of columns in a DataFrame.
- drop_invariate_cols: Drops columns from a DataFrame that are invariable.
- split_df: Splits a DataFrame into two based on a specified ratio.
- series_col: Converts a column of a DataFrame into a pandas Series.
- get_distinct_col_vals: Retrieves distinct values from a specified column in a DataFrame.
- rm_df_col_pattern: Removes columns from a DataFrame based on a pattern match.
- df_to_db: Exports a DataFrame to a database using SQLAlchemy.

The module utilizes external libraries such as pandas and SQLAlchemy, emphasizing efficient data manipulation and database interaction. It is designed to simplify common data processing tasks for data scientists and Python developers.

Example:
    To add a new column with a fixed value to a DataFrame, use:
    >>> df = add_col(df, 'new_col', 100)

Note:
    This module assumes that input DataFrames are properly structured and does not handle malformed DataFrames.
"""

from datetime import datetime
from functools import partial
from itertools import chain
from typing import Any

from pandas import DataFrame

from alexlib.iters import rm_pattern


def add_col(df: DataFrame, col: str, val: Any) -> DataFrame:
    """adds a column to a dataframe"""
    if not isinstance(df, DataFrame):
        raise TypeError(f"{df} not {DataFrame}")
    df.loc[:, col] = val
    return df


add_timestamp_col = partial(
    add_col,
    col="datetime",
    val=datetime.now(),
)


def col_pair_to_dict(col1: str, col2: str, df: DataFrame) -> dict:
    """creates a dict from 2 columns in a dataframe"""
    pairs = df.loc[:, [col1, col2]].to_dict("records")
    return {p[col1]: p[col2] for p in pairs}


def get_row_as_list(idx: int, df: DataFrame) -> list[Any]:
    """gets row of df as a list"""
    return df.iloc[idx, :].values.tolist()


def get_rows_as_list(df: DataFrame) -> list[list]:
    """gets rows of df as a list of lists"""
    rng = range(len(df))
    return [get_row_as_list(i, df) for i in rng]


def filter_df(df: DataFrame, col: str, val: Any) -> DataFrame:
    """filters df by col == val"""
    if not isinstance(df, DataFrame):
        raise TypeError(f"{df} not {DataFrame}")
    return df[df.loc[:, col] == val]


def get_val_order(
    df: DataFrame,
    order_col: str,
    order_val: str | int | float,
    filter_col: str,
    filter_val: str | int | float,
) -> int:
    """gets the order of a value in a column after filtering"""
    filtered_df = filter_df(df, filter_col, filter_val)
    series_list = filtered_df.loc[:, order_col].to_list()
    return series_list.index(order_val)


def get_unique_col_vals(col: str, df: DataFrame | list[DataFrame]) -> list:
    """gets unique vals from col in df
    inputs:
        col = column of interest to find unique values
        df = dataframe containing column
    returns:
        val_list = list of unique values
    """
    # check if df is a single df
    if isinstance(df, DataFrame):
        vals = df.loc[:, col].unique()  # str from slice
    # check if df is a list of dfs
    elif isinstance(df, list):
        vals_list = [get_unique_col_vals(col, d) for d in df]
        vals = set(chain.from_iterable(vals_list))
    # check if df is a dict of dfs
    elif isinstance(df, dict):
        vals = get_unique_col_vals(col, list(df.values()))
    else:
        raise TypeError(f"need df or list of dfs but got {type(df)}")
    return list(vals)


def make_unique_dict(key_col: str, df: DataFrame) -> dict[str:Any]:
    """creates a dict of slices from df using the unique vals from 1 col
    inputs:
        col = column of interest to use as keys
        df = dataframe
    returns:
        out_dict = dict of slices
    """
    return {
        key: filter_df(df, key_col, key) for key in get_unique_col_vals(key_col, df)
    }


def col_vals_to_dict(df: DataFrame, key_col: str, val_col: str) -> dict[str:Any]:
    """creates a dict of slices from df using the unique vals from 1 col"""
    d = df.loc[:, [key_col, val_col]]
    recs = d.to_dict(orient="records")
    return {x[key_col]: x[val_col] for x in recs}


def set_type_list(df: DataFrame, type_: Any, cols: list[str]) -> DataFrame:
    """
    Efficiently sets the type of specified columns in a DataFrame.

    Args:
    df (DataFrame): The DataFrame to modify.
    type_ (Any): The new data type to be applied.
    cols (list[str]): A list of column names to change the type.

    Returns:
    DataFrame: The modified DataFrame with updated column types.
    """

    # Using .astype() with a dictionary allows conversion of multiple columns in a single call
    df = df.astype({col: type_ for col in cols if col in df.columns})

    return df


def drop_invariate_cols(df: DataFrame) -> DataFrame:
    """Drops columns that have the same value in every row."""
    keep_cols = df.columns[df.nunique() != 1]
    return df.loc[:, keep_cols]


def split_df(df: DataFrame, ratio: float, head: bool = True) -> DataFrame:
    """splits a dataframe into a head or tail slice"""
    if not 0 < ratio < 1:
        raise ValueError(f"{ratio} not between 0 and 1")
    if not isinstance(df, DataFrame):
        raise TypeError(f"{df} not {DataFrame}")
    if not isinstance(ratio, float):
        raise TypeError(f"{ratio} not {float}")
    to = int(len(df) * ratio)
    return df.head(to) if head else df.tail(to)


def get_distinct_col_vals(df: DataFrame, col: str) -> list:
    """gets distinct values from col in df"""
    return list(df.loc[:, col].unique())


def rm_df_col_pattern(
    pattern: str | tuple | list, df: DataFrame, end: bool = True
) -> DataFrame:
    """removes columns from df based on pattern"""
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

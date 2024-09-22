"""Unit tests for the filter_df function in the alexlib.df module."""

from datetime import datetime

from pandas import DataFrame
from pytest import mark, raises

from alexlib.df import (
    add_col,
    add_timestamp_col,
    col_pair_to_dict,
    filter_df,
    get_distinct_col_vals,
)


def test_add_timestamp_col(df_copy):
    """Test adding a new column with correct inputs."""
    result_df = add_timestamp_col(df_copy)
    assert "datetime" in result_df.columns
    assert all(isinstance(x, datetime) for x in result_df.loc[:, "datetime"])


def test_add_timestamp_col_invalid_input():
    # Test with invalid DataFrame input
    with raises(TypeError):
        add_timestamp_col("not_a_dataframe")


def test_add_col(df_copy):
    """Test adding a new column with correct inputs."""
    result_df = add_col(df_copy, "D", 100)
    assert "D" in result_df.columns
    assert (result_df["D"] == 100).all()


def test_add_col_invalid_input(df_copy):
    """Test with invalid DataFrame input."""
    with raises(TypeError):
        add_col("not_a_dataframe", "D", 100)


def test_col_pair_to_dict(df):
    """Test with valid inputs."""
    result_dict = col_pair_to_dict("col1", "col2", df)
    assert isinstance(result_dict, dict)

    # Test with non-existent columns
    with raises(KeyError):
        col_pair_to_dict("X", "Y", df)


def test_empty_df_is_df(empty_df):
    """Test that the empty DataFrame is a DataFrame."""
    assert isinstance(empty_df, DataFrame)


def test_df_is_df(df):
    """Test that the DataFrame is a DataFrame."""
    assert isinstance(df, DataFrame)


def test_df_with_duplicate_values_is_df(df_with_duplicate_values):
    """Test that the DataFrame with duplicate values is a DataFrame."""
    assert isinstance(df_with_duplicate_values, DataFrame)


def test_df_to_filter_is_df(df_to_filter):
    """Test that the DataFrame to filter is a DataFrame."""
    assert isinstance(df_to_filter, DataFrame)


@mark.parametrize(
    "column, value, expected",
    [
        ("city", "New York", 1),
        ("age", 30, 1),
        ("city", "Miami", 0),
        ("country", "USA", 0),
    ],
)
def test_filter_df(df_to_filter, column, value, expected):
    """Test filtering a DataFrame by column and value"""
    if column == "country":
        with raises(KeyError):
            filter_df(df_to_filter, column, value)
        return
    elif isinstance(df_to_filter, str):
        with raises(TypeError):
            filter_df(df_to_filter, column, value)
        return

    filtered_df = filter_df(df_to_filter, column, value)
    assert len(filtered_df) == expected
    if expected == 1:
        assert filtered_df[column].iloc[0] == value


def test_empty_dataframe(empty_df):
    """Test get_distinct_col_vals with an empty DataFrame."""
    with raises(KeyError):
        get_distinct_col_vals(empty_df, "any_column")


@mark.parametrize(
    "col, expected",
    [
        ("col1", [1, 2, 3]),
        ("col2", ["a", "b", "c"]),
    ],
)
def test_distinct_values(df_with_duplicate_values, col, expected):
    """Test retrieving distinct column values."""
    distinct_values = get_distinct_col_vals(df_with_duplicate_values, col)
    assert distinct_values == expected, f"Distinct values in {col} should be {expected}"

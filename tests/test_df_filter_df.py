"""Unit tests for the filter_df function in the alexlib.df module."""

from pandas import DataFrame
from pytest import fixture, mark, raises

from alexlib.df import filter_df


@fixture(scope="module")
def df():
    return DataFrame.from_dict(
        {
            "name": ["Alice", "Bob", "Charlie", "David"],
            "age": [25, 30, 35, 40],
            "city": ["New York", "Los Angeles", "Chicago", "Houston"],
        }
    )


@mark.parametrize(
    "column, value, expected",
    [
        ("city", "New York", 1),
        ("age", 30, 1),
        ("city", "Miami", 0),
        ("country", "USA", 0),
    ],
)
def test_filter_df(df, column, value, expected):
    """Test filtering a DataFrame by column and value"""
    filtered_df = filter_df(df, column, value)
    if value == "country":
        raises(KeyError)
    elif df == "not_a_dataframe":
        raises(TypeError)
    else:
        assert len(filtered_df) == expected
        assert filtered_df[column].iloc[0] == value

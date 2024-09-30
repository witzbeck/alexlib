"""Unit tests for the filter_df function in the alexlib.df module."""

from datetime import datetime
from random import randint

from pandas import DataFrame
from pytest import FixtureRequest, fixture, mark, raises

from alexlib.df import (
    add_col,
    add_timestamp_col,
    col_pair_to_dict,
    drop_invariate_cols,
    filter_df,
    get_distinct_col_vals,
    get_unique_col_vals,
    get_val_order,
    rm_df_col_pattern,
    set_type_list,
    split_df,
)


@fixture(scope="module")
def df_to_split():
    return DataFrame({"col1": range(10), "col2": range(10, 20)})


def test_split_df(df_to_split):
    """Test splitting the DataFrame based on a given ratio."""
    ratio = 0.5
    result = split_df(df_to_split, ratio)
    expected_length = int(len(df_to_split) * ratio)
    assert (
        len(result) == expected_length
    ), "DataFrame split did not result in the expected length"


def test_type_setting(df):
    """Test changing the data type of specified columns."""
    df = set_type_list(df, "float", ["col1"])
    assert all(
        isinstance(x, float) for x in df["col1"]
    ), "Column col1 should be converted to float."


def test_type_setting_invalid(df):
    """Test with an invalid data type."""
    with raises(TypeError):
        set_type_list(df, "invalid_type", ["col1"])


@mark.parametrize("ratio", [-1, 1.5])
def test_split_df_invalid_ratio(ratio, df_to_split):
    """Test with a ratio outside the range of 0 to 1."""
    with raises(ValueError):
        split_df(df_to_split, ratio)


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


@fixture(scope="module")
def df_with_column_pattern():
    return DataFrame.from_dict(
        {
            "alpha_1": [1, 2, 3],
            "beta_1": [4, 5, 6],
            "alpha_2": [7, 8, 9],
            "gamma": [10, 11, 12],
        }
    )


@mark.parametrize(
    "column_pattern, expected_columns",
    [
        ("alpha", ["beta_1", "gamma"]),
        ("beta", ["alpha_1", "alpha_2", "gamma"]),
        ("gamma", ["alpha_1", "beta_1", "alpha_2"]),
    ],
)
def test_rm_df_col_pattern(df_with_column_pattern, column_pattern, expected_columns):
    """Test removing columns based on a pattern."""
    result_df = rm_df_col_pattern(column_pattern, df_with_column_pattern, end=False)
    assert sorted(result_df.columns) == sorted(expected_columns)


def test_rm_df_col_pattern_no_match(df_with_column_pattern):
    """Test removing columns based on a pattern that does not match any columns."""
    result_df = rm_df_col_pattern("delta", df_with_column_pattern)
    assert sorted(result_df.columns) == sorted(df_with_column_pattern.columns)


@fixture(scope="module")
def sample_df():
    """Sample Data for Testing"""
    data = {"A": [1, 2, 3, 4, 5], "B": [10, 20, 30, 40, 50]}
    return DataFrame.from_dict(data)


@fixture(scope="module")
def filtered_valid_df(sample_df):
    return filter_df(sample_df, "A", 3)


def test_filter_df_with_one_valid_value(filtered_valid_df):
    """Test for Valid Value"""
    assert (
        len(filtered_valid_df) == 1
    ), "The filtered DataFrame should have only one row"


def test_filter_df_with_valid_value_by_index(filtered_valid_df):
    """Test for Valid Value"""
    assert filtered_valid_df["B"].iloc[0] == 30, "The value in column 'B' should be 30"


def test_filter_df_with_nonexistent_value(sample_df):
    """Test for Nonexistent Value"""
    filtered_df = filter_df(sample_df, "A", 99)
    assert filtered_df.empty, "DataFrame should be empty for a nonexistent value"


def test_get_val_order(sample_df):
    """Test for Value Order"""
    order = get_val_order(sample_df, "A", 3, "B", 30)
    assert (
        order == 0
    ), "The order of the value 3 in column 'A' after filtering 'B' for 30 should be 2"


@fixture(scope="module")
def sample_df_with_duplicates():
    """Fixture to provide a sample DataFrame."""
    data = {"col1": [1, 2, 2, 3, 3, 3], "col2": ["a", "b", "b", "c", "c", "c"]}
    return DataFrame.from_dict(data)


@fixture(
    scope="module",
    params=(
        ("col1", [1, 2, 3]),
        ("col2", ["a", "b", "c"]),
    ),
)
def col_expected(request: FixtureRequest) -> list:
    """Fixture to provide expected unique values for col1."""
    return request.param


def test_get_unique_col_vals(sample_df_with_duplicates, col_expected):
    """Test extracting unique values from a DataFrame."""
    col, col_expected = col_expected
    assert (
        sorted(get_unique_col_vals(col=col, df=sample_df_with_duplicates))
        == col_expected
    )


def test_get_unique_col_vals_invalid_input():
    """Test with invalid input to ensure proper error handling."""
    with raises(TypeError):
        get_unique_col_vals("col1", "not_a_dataframe")


@fixture(scope="module")
def df_scale_height_param() -> tuple[int]:
    return randint(1, 100)


@fixture(scope="module")
def df_scale_width_param() -> tuple[int]:
    return randint(1, 100)


@fixture(scope="module")
def invariate_df(df_scale_height_param, df_scale_width_param):
    return DataFrame.from_dict(
        {
            "A": [1] * df_scale_height_param,
            "B": [2] * df_scale_height_param,
            "C": [randint(1, 1000) for _ in range(df_scale_height_param)],
        }
    )


@fixture(scope="module")
def post_drop_df(invariate_df):
    return drop_invariate_cols(invariate_df)


@fixture(scope="module")
def variate_df(df_scale_height_param, df_scale_width_param):
    return DataFrame.from_dict(
        {
            "A": [randint(1, 1000) for _ in range(df_scale_height_param)],
            "B": [randint(1, 1000) for _ in range(df_scale_height_param)],
            "C": [randint(1, 1000) for _ in range(df_scale_height_param)],
        }
    )


@mark.parametrize("col,isretained", [("A", False), ("B", False), ("C", True)])
def test_drop_invariate_cols(post_drop_df: DataFrame, col: str, isretained: bool):
    """Test dropping invariable columns."""
    assert isinstance(post_drop_df, DataFrame), "Output should be a DataFrame."
    assert isinstance(col, str), "Column name should be a string."
    assert isinstance(isretained, bool), "isretained should be a boolean."
    assert (
        col in post_drop_df.columns
    ) == isretained, f"Columns = {post_drop_df.columns}"


def test_drop_variate_cols(variate_df: DataFrame):
    """Test with a DataFrame where all columns are variable."""
    assert isinstance(variate_df, DataFrame), "Input should be a DataFrame."
    result_df = drop_invariate_cols(variate_df)
    assert isinstance(result_df, DataFrame), "Output should be a DataFrame."
    assert sorted(result_df.columns) == sorted(
        variate_df.columns
    ), "All columns should be retained."


@fixture(scope="module")
def df_with_pair():
    return DataFrame({"A": [1, 2, 3], "B": ["one", "two", "three"], "C": [4, 5, 6]})


@fixture(scope="module")
def expected_pair_dict():
    return {1: "one", 2: "two", 3: "three"}


def test_invalid_columns_col_pair_to_dict(df_with_pair):
    with raises(KeyError):
        col_pair_to_dict("X", "Y", df_with_pair)


def test_dict_conversion_col_pair_to_dict(df_with_pair, expected_pair_dict):
    result_dict = col_pair_to_dict("A", "B", df_with_pair)
    assert result_dict == expected_pair_dict, f"Conversion failed, result={result_dict}"

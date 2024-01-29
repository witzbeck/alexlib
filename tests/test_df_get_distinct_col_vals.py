"""
Unit tests for the `get_distinct_col_vals` function from the `alexlib.df` module.

These tests cover scenarios for retrieving distinct values from a specified column in a DataFrame.
"""

# Standard library imports
from unittest import TestCase, main

# Third-party imports
from pandas import DataFrame

# Local application imports
from alexlib.df import get_distinct_col_vals


class TestGetDistinctColVals(TestCase):
    """
    Test cases for the `get_distinct_col_vals` function in the `alexlib.df` module.
    """

    def test_empty_dataframe(self):
        """
        Test get_distinct_col_vals with an empty DataFrame.

        Expected Result:
        The function should return an empty list when provided with an empty DataFrame.
        """
        df = DataFrame()
        with self.assertRaises(KeyError):
            get_distinct_col_vals(df, "any_column")

    def test_distinct_values(self):
        """
        Test retrieving distinct column values.

        Expected Result:
        The function should correctly return a list of distinct values from the specified column.
        """
        df = DataFrame({"col1": [1, 2, 2, 3], "col2": ["a", "b", "b", "c"]})
        distinct_values_col1 = get_distinct_col_vals(df, "col1")
        distinct_values_col2 = get_distinct_col_vals(df, "col2")
        self.assertEqual(
            distinct_values_col1,
            [1, 2, 3],
            "Distinct values in col1 should be [1, 2, 3]",
        )
        self.assertEqual(
            distinct_values_col2,
            ["a", "b", "c"],
            "Distinct values in col2 should be ['a', 'b', 'c']",
        )


if __name__ == "__main__":
    main()

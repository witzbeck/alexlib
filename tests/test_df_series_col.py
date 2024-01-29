# test_series_col.py

"""
Unit tests for the series_col function in the alexlib.df module.

These tests verify the functionality of converting a DataFrame column to a pandas Series
and handling of invalid column input.
"""

from unittest import TestCase, main
from pandas import DataFrame, Series
from alexlib.df import series_col


class TestSeriesCol(TestCase):
    """
    Test cases for the series_col function from the alexlib.df module.
    """

    def setUp(self):
        """
        Setup function to create a DataFrame for testing.
        """
        self.df = DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})

    def test_invalid_column(self):
        """
        Test series_col with a nonexistent column.
        This should raise a KeyError.
        """
        with self.assertRaises(KeyError):
            series_col(self.df, "Nonexistent")

    def test_series_conversion(self):
        """
        Test converting a DataFrame column to a Series.
        The function should return a Series object with the correct values.
        """
        result = series_col(self.df, "A")
        expected = Series([1, 2, 3])
        self.assertTrue(result.equals(expected))


if __name__ == "__main__":
    main()

"""
Unit tests for the `drop_invariate_cols` function from the `alexlib.df` module.

This module contains tests to ensure the correct functionality of the `drop_invariate_cols` function,
which drops columns from a DataFrame that are invariable (having the same value in every row).
"""

# Explicit imports
from unittest import TestCase, main

from pandas import DataFrame

from alexlib.df import drop_invariate_cols


class TestDropInvariateCols(TestCase):
    """TestCase class for testing `drop_invariate_cols` function."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create sample DataFrames
        self.df_invariable = DataFrame.from_dict(
            {"A": [1, 1, 1], "B": [2, 2, 2], "C": [3, 4, 5]}
        )

        self.df_variable = DataFrame.from_dict(
            {"A": [1, 2, 3], "B": [4, 5, 6], "C": [7, 8, 9]}
        )

    def test_drop_columns(self):
        """
        Test dropping invariable columns.
        The function should remove columns 'A' and 'B' as they are invariable.
        """
        result_df = drop_invariate_cols(self.df_invariable)
        cols = list(result_df.columns)
        self.assertNotIn("A", cols)
        self.assertNotIn("B", cols)
        self.assertIn("C", cols)

    def test_all_variable(self):
        """
        Test with a DataFrame where all columns are variable.
        The function should not drop any columns in this case.
        """
        result_df = drop_invariate_cols(self.df_variable)
        self.assertListEqual(list(result_df.columns), ["A", "B", "C"])


if __name__ == "__main__":
    main()

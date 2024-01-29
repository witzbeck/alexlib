"""
Unit tests for the rm_df_col_pattern function in the alexlib.df module.

These tests ensure that the function correctly removes columns from a DataFrame based on a given pattern and handles invalid patterns appropriately.
"""

from unittest import TestCase, main
from pandas import DataFrame
from alexlib.df import rm_df_col_pattern


class TestRmDfColPattern(TestCase):
    """TestCase class for testing rm_df_col_pattern function."""

    def setUp(self):
        """Set up test fixtures."""
        self.df = DataFrame.from_dict(
            {
                "alpha_1": [1, 2, 3],
                "beta_1": [4, 5, 6],
                "alpha_2": [7, 8, 9],
                "gamma": [10, 11, 12],
            }
        )

    def test_pattern_removal(self):
        """Test removing columns based on a pattern."""
        result_df = rm_df_col_pattern("alpha", self.df, end=False)
        self.assertNotIn("alpha_1", result_df.columns)
        self.assertNotIn("alpha_2", result_df.columns)
        self.assertIn("beta_1", result_df.columns)
        self.assertIn("gamma", result_df.columns)

    def test_invalid_pattern(self):
        """Test with a pattern not matching any column."""
        result_df = rm_df_col_pattern("delta", self.df)
        self.assertEqual(list(result_df.columns), list(self.df.columns))


if __name__ == "__main__":
    main()

"""
Unit tests for the alexlib.df module.

This module contains unit tests for the col_pair_to_dict function
from the alexlib.df module. It tests normal and edge cases to ensure
correct functionality and error handling.
"""

from unittest import TestCase, main
from pandas import DataFrame
from alexlib.df import col_pair_to_dict


class TestColPairToDict(TestCase):
    """
    Test cases for col_pair_to_dict function from the alexlib.df module.
    """

    def setUp(self):
        """
        Set up data for testing.
        """
        self.test_df = DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})

    def test_normal_case(self):
        """
        Test col_pair_to_dict with valid column names.
        """
        expected_result = {1: 4, 2: 5, 3: 6}
        result = col_pair_to_dict("A", "B", self.test_df)
        self.assertEqual(
            result,
            expected_result,
            "The function should correctly convert columns to dictionary.",
        )

    def test_invalid_columns(self):
        """
        Test col_pair_to_dict with nonexistent column names.
        """
        with self.assertRaises(KeyError):
            col_pair_to_dict("X", "Y", self.test_df)


if __name__ == "__main__":
    main()

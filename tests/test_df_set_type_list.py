"""
Unit tests for the set_type_list function in the alexlib.df module.

This module contains tests for different scenarios including setting data types
for specified columns, handling invalid data types, and handling nonexistent columns.
"""

from unittest import TestCase, main
from alexlib.df import set_type_list
from pandas import DataFrame


class TestSetTypeList(TestCase):
    """Test cases for the set_type_list function."""

    def setUp(self):
        """Set up test fixtures."""
        self.data = {"col1": [1, 2, 3], "col2": ["a", "b", "c"]}
        self.df = DataFrame(self.data)

    def test_type_setting(self):
        """Test changing the data type of specified columns."""
        self.df = set_type_list(self.df, "float", ["col1"])
        print(self.df.dtypes)
        self.assertTrue(
            all(isinstance(x, float) for x in self.df["col1"]),
            "Column col1 should be converted to float.",
        )

    def test_invalid_type(self):
        """Test with an invalid data type."""
        with self.assertRaises(TypeError):
            set_type_list(self.df, "invalid_type", ["col1"])


if __name__ == "__main__":
    main()

"""Test table object"""
from unittest import TestCase, main

from pandas import DataFrame

from alexlib.db.objects import Table


class TestTable(TestCase):
    """Test table object"""

    def setUp(self):
        """Set up test table and dataframe"""
        self.test_df = DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
        self.test_table = Table.from_df("test_schema", "test_table", self.test_df)

    def test_cols(self):
        """Test column names""" ""
        self.assertEqual(self.test_table.cols, ["col1", "col2"])

    def test_ncols(self):
        """Test number of columns"""
        self.assertEqual(self.test_table.ncols, 2)

    # Additional tests for head, rand_col, etc. can be added here


if __name__ == "__main__":
    main()

"""Test the column object"""
from unittest import TestCase, main

from pandas import DataFrame

from alexlib.db.objects import Name, Column


class TestColumn(TestCase):
    """Test column object"""

    def setUp(self) -> None:
        """Assuming setup for a test database and table"""
        self.test_df = DataFrame.from_dict({"col1": [1, 2, 3], "col2": [4, 5, 6]})
        series = self.test_df.loc[:, "col1"]
        name = Name("col1")
        self.test_column = Column(name, "test_table", "test_schema", series=series)

    def test_len(self) -> None:
        """Test the length of the series in the column"""
        self.assertEqual(len(self.test_column), 3)

    def test_distvals(self) -> None:
        """Test distinct values calculation"""
        self.assertListEqual(self.test_column.distvals.tolist(), [1, 2, 3])

    # Additional tests for frequencies, proportions, etc. can be added here


if __name__ == "__main__":
    main()

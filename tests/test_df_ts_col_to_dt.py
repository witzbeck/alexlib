"""Unit test module for the ts_col_to_dt function in alexlib.df."""

from unittest import TestCase, main
from pandas import DataFrame, to_datetime
from alexlib.df import ts_col_to_dt


class TestTsColToDt(TestCase):
    """Test cases for the ts_col_to_dt function."""

    def test_timestamp_conversion(self):
        """
        Test converting a timestamp column to datetime.
        It verifies that the function correctly converts a DataFrame column containing timestamp values into datetime.
        """
        df = DataFrame({"timestamp": ["2023-01-01 00:00:00", "2023-01-02 00:00:00"]})
        converted_df = ts_col_to_dt(df, "timestamp", "datetime")
        self.assertTrue(to_datetime(df["timestamp"]).equals(converted_df["datetime"]))

    def test_invalid_column(self):
        """
        Test with a nonexistent timestamp column.
        This test checks if the function raises a KeyError when a nonexistent column is passed.
        """
        df = DataFrame({"some_column": [1, 2]})
        with self.assertRaises(KeyError):
            ts_col_to_dt(df, "nonexistent_col", "datetime")


if __name__ == "__main__":
    main()

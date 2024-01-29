"""Unit tests for the filter_df function in the alexlib.df module."""
from pandas import DataFrame
from alexlib.df import filter_df
from unittest import TestCase, main


def get_sample_dataframe():
    data = {
        "name": ["Alice", "Bob", "Charlie", "David"],
        "age": [25, 30, 35, 40],
        "city": ["New York", "Los Angeles", "Chicago", "Houston"],
    }
    return DataFrame.from_dict(data)


class TestFilterDF(TestCase):
    def test_filter_by_string(self):
        """Test filtering by a string value"""
        filtered_df = filter_df(get_sample_dataframe(), "city", "New York")
        self.assertEqual(len(filtered_df), 1)
        self.assertEqual(filtered_df["name"].iloc[0], "Alice")

    def test_filter_by_integer(self):
        """Test filtering by an integer value"""
        filtered_df = filter_df(get_sample_dataframe(), "age", 30)
        self.assertEqual(len(filtered_df), 1)
        self.assertEqual(filtered_df["name"].iloc[0], "Bob")

    def test_filter_no_match(self):
        """Test filtering with no matching value"""
        filtered_df = filter_df(get_sample_dataframe(), "city", "Miami")
        self.assertTrue(filtered_df.empty)

    def test_filter_invalid_column(self):
        """Test filtering with invalid column name"""
        with self.assertRaises(KeyError):
            filter_df(get_sample_dataframe(), "country", "USA")

    def test_filter_invalid_dataframe(self):
        """Test filtering with invalid DataFrame input"""
        with self.assertRaises(TypeError):
            filter_df("not_a_dataframe", "age", 30)


if __name__ == "__main__":
    main()

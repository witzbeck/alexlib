from pandas import DataFrame, testing
from unittest import TestCase, main
from alexlib.df import add_col, col_pair_to_dict, filter_df

# Sample DataFrames for testing
sample_df = DataFrame.from_dict(
    {"A": [1, 2, 3], "B": ["a", "b", "c"], "C": [1.1, 2.2, 3.3]}
)


class TestAddCol(TestCase):
    """Test add_col function"""

    def test_add_col(self):
        """Test adding a new column with correct inputs"""
        result_df = add_col(sample_df.copy(), "D", 100)
        self.assertIn("D", result_df.columns)
        self.assertTrue((result_df["D"] == 100).all())

        # Test with invalid DataFrame input
        with self.assertRaises(TypeError):
            add_col("not_a_dataframe", "D", 100)

    # Test col_pair_to_dict function
    def test_col_pair_to_dict(self):
        """Test with valid inputs"""
        result_dict = col_pair_to_dict("A", "B", sample_df)
        expected_dict = {1: "a", 2: "b", 3: "c"}
        self.assertDictEqual(result_dict, expected_dict)

        # Test with non-existent columns
        with self.assertRaises(KeyError):
            col_pair_to_dict("X", "Y", sample_df)

    # Test filter_df function
    def test_filter_df(self):
        """Test filtering with correct inputs"""
        filtered_df = filter_df(sample_df, "A", 2)
        self.assertEqual(len(filtered_df), 1)
        self.assertEqual(filtered_df.iloc[0]["A"], 2)

        # Test with invalid DataFrame input
        with self.assertRaises(TypeError):
            filter_df("not_a_dataframe", "A", 2)

        # Test with non-existent column
        with self.assertRaises(KeyError):
            filter_df(sample_df, "X", 1)

    def test_add_col_constant(self):
        """Test adding a column with a constant value."""
        df = DataFrame.from_dict({"A": [1, 2, 3]})
        result = add_col(df, "B", 100)
        expected = DataFrame({"A": [1, 2, 3], "B": [100, 100, 100]})
        testing.assert_frame_equal(result, expected)

    def test_add_col_list(self):
        """Test adding a column with a list of values."""
        df = DataFrame.from_dict({"A": [1, 2, 3]})
        result = add_col(df, "B", [4, 5, 6])
        expected = DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        testing.assert_frame_equal(result, expected)

    def test_add_col_invalid_input(self):
        """Test adding a column with invalid input types."""
        with self.assertRaises(TypeError):
            add_col("not_a_dataframe", "B", 100)


if __name__ == "__main__":
    main()

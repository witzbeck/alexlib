from unittest import TestCase, main
from pandas import DataFrame
from datetime import datetime
from alexlib.df import add_col, add_timestamp_col

# Prepare a sample DataFrame
sample_df = DataFrame({"A": [1, 2, 3], "B": ["x", "y", "z"]})


class TestAddCol(TestCase):
    def test_add_col(self):
        """Test for add_col function"""
        # Column Check
        new_df = add_col(sample_df.copy(), "C", 100)
        self.assertIn("C", new_df.columns)
        self.assertTrue(all(new_df["C"] == 100))

        # Test with invalid DataFrame input
        with self.assertRaises(TypeError):
            add_col("not_a_dataframe", "D", 100)

    def test_add_timestamp_col(self):
        """Test for add_timestamp_col function"""
        # Timestamp Check
        new_df = add_timestamp_col(sample_df.copy())
        self.assertIn("datetime", new_df.columns)
        self.assertTrue(all(isinstance(x, datetime) for x in new_df["datetime"]))

        # Column Check
        self.assertIn("datetime", new_df.columns)

        # Test the type of values in the datetime column
        self.assertIsInstance(new_df.iloc[0]["datetime"], datetime)


if __name__ == "__main__":
    main()

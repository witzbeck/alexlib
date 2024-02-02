from unittest import TestCase, main
from pandas import DataFrame
from alexlib.df import filter_df, get_val_order


def get_sample_df():
    """Sample Data for Testing"""
    data = {"A": [1, 2, 3, 4, 5], "B": [10, 20, 30, 40, 50]}
    return DataFrame.from_dict(data)


class TestFilterDF(TestCase):
    def test_filter_df_with_valid_value(self):
        """Test for Valid Value"""
        filtered_df = filter_df(get_sample_df(), "A", 3)
        (
            self.assertEqual(len(filtered_df), 1),
            "The filtered DataFrame should have only one row",
        )
        (
            self.assertEqual(filtered_df["B"].iloc[0], 30),
            "The value in column 'B' should be 30",
        )

    def test_filter_df_with_nonexistent_value(self):
        """Test for Nonexistent Value"""
        filtered_df = filter_df(get_sample_df(), "A", 99)
        self.assertTrue(
            filtered_df.empty, "DataFrame should be empty for a nonexistent value"
        )

    def test_get_val_order(self):
        """Test for Value Order"""
        order = get_val_order(get_sample_df(), "A", 3, "B", 30)
        (
            self.assertEqual(order, 0),
            "The order of the value 3 in column 'A' after filtering 'B' for 30 should be 2",
        )


if __name__ == "__main__":
    main()

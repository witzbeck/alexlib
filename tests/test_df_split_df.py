# test_alexlib_df.py

from unittest import TestCase, main
from pandas import DataFrame
from alexlib.df import split_df


class TestSplitDf(TestCase):
    """
    Unit tests for the 'split_df' function in the 'alexlib.df' module.
    """

    def setUp(self):
        """
        Set up data for testing.
        """
        self.test_data = DataFrame({"col1": range(10), "col2": range(10, 20)})

    def test_splitting(self):
        """
        Test splitting the DataFrame based on a given ratio.
        """
        ratio = 0.5
        result = split_df(self.test_data, ratio)
        expected_length = int(len(self.test_data) * ratio)
        self.assertEqual(
            len(result),
            expected_length,
            "DataFrame split did not result in the expected length",
        )

    def test_invalid_ratio(self):
        """
        Test with a ratio outside the range of 0 to 1.
        """
        ratios = [-1, 1.5]
        for ratio in ratios:
            with self.assertRaises(
                ValueError,
                msg=f"Splitting with an invalid ratio {ratio} should raise a ValueError",
            ):
                split_df(self.test_data, ratio)


if __name__ == "__main__":
    main()

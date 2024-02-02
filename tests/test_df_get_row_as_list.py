import unittest
from alexlib.df import get_row_as_list
from pandas import DataFrame


class TestGetRowAsList(unittest.TestCase):
    """
    Unit tests for the get_row_as_list function in the alexlib.df module.
    """

    def setUp(self):
        """
        Set up a simple DataFrame for testing.
        """
        self.test_df = DataFrame({"A": [1, 2, 3], "B": [4, 5, 6], "C": [7, 8, 9]})

    def test_get_specific_row(self):
        """
        Test retrieving a specific row from a DataFrame.
        """
        expected = [2, 5, 8]
        result = get_row_as_list(1, self.test_df)
        self.assertEqual(
            result, expected, "The function should return the second row as a list."
        )

    def test_get_row_invalid_index(self):
        """
        Test retrieving a row using an out-of-range index.
        """
        with self.assertRaises(
            IndexError, msg="Should raise an IndexError for out-of-range index"
        ):
            get_row_as_list(5, self.test_df)


if __name__ == "__main__":
    unittest.main()

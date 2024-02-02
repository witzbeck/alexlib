# test_alexlib_df.py

import unittest
from alexlib.df import get_rows_as_list
from pandas import DataFrame


class TestGetRowsAsList(unittest.TestCase):
    """
    Unit tests for the get_rows_as_list function in the alexlib.df module.
    """

    def test_all_rows_conversion(self):
        """
        Test if get_rows_as_list correctly converts all DataFrame rows into a list of lists.
        """
        # Setting up a sample DataFrame
        data = {"col1": [1, 2, 3], "col2": [4, 5, 6]}
        df = DataFrame(data)

        # Expected result
        expected = [[1, 4], [2, 5], [3, 6]]

        # Test
        result = get_rows_as_list(df)
        self.assertEqual(
            result,
            expected,
            "The conversion of DataFrame rows to list of lists is incorrect.",
        )


if __name__ == "__main__":
    unittest.main()

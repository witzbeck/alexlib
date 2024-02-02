from pytest import raises
from pandas import DataFrame
from alexlib.df import col_pair_to_dict, col_vals_to_dict
from unittest import TestCase, main


class TestColPairToDict(TestCase):
    def test_invalid_columns_col_pair_to_dict(self):
        # Create a dummy DataFrame
        df = DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})

        # Test with non-existent columns
        with raises(KeyError):
            col_pair_to_dict("X", "Y", df)

    def test_invalid_columns_col_vals_to_dict(self):
        # Create a dummy DataFrame
        df = DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})

        # Test with non-existent columns
        with self.assertRaises(KeyError):
            col_vals_to_dict(df, "X", "Y")

    def test_dict_conversion_col_pair_to_dict(self):
        # Create a dummy DataFrame
        df = DataFrame({"A": [1, 2, 3], "B": ["one", "two", "three"]})

        # Expected dictionary
        expected_dict = {1: "one", 2: "two", 3: "three"}

        # Test conversion
        result_dict = col_pair_to_dict("A", "B", df)
        self.assertDictEqual(result_dict, expected_dict)

    def test_dict_conversion_col_vals_to_dict(self):
        # Create a dummy DataFrame
        df = DataFrame.from_dict({"A": [1, 2, 3], "B": ["one", "two", "three"]})

        # Expected dictionary
        expected_dict = {1: "one", 2: "two", 3: "three"}

        # Test conversion
        result_dict = col_vals_to_dict(df, "A", "B")
        self.assertDictEqual(result_dict, expected_dict)


if __name__ == "__main__":
    main()

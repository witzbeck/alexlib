from pandas import DataFrame
from alexlib.df import get_unique_col_vals
from unittest import TestCase, main


def get_sample_df():
    """Fixture to provide a sample DataFrame."""
    data = {"col1": [1, 2, 2, 3, 3, 3], "col2": ["a", "b", "b", "c", "c", "c"]}
    return DataFrame.from_dict(data)


class TestGetUniqueColVals(TestCase):
    def test_get_unique_col_vals_single_df(self):
        """Test extracting unique values from a single DataFrame."""
        expected_col1 = [1, 2, 3]
        expected_col2 = ["a", "b", "c"]

        self.assertListEqual(
            sorted(get_unique_col_vals("col1", get_sample_df())), expected_col1
        )
        self.assertListEqual(
            sorted(get_unique_col_vals("col2", get_sample_df())), expected_col2
        )

    def test_get_unique_col_vals_list_of_dfs(self):
        """Test extracting unique values from a list of DataFrames."""
        sample_df = get_sample_df()
        df_list = [sample_df, sample_df.copy()]
        expected_col1 = [1, 2, 3]
        expected_col2 = ["a", "b", "c"]

        self.assertListEqual(
            sorted(get_unique_col_vals("col1", df_list)), expected_col1
        )
        self.assertListEqual(
            sorted(get_unique_col_vals("col2", df_list)), expected_col2
        )

    def test_get_unique_col_vals_invalid_input(self):
        """Test with invalid input to ensure proper error handling."""
        with self.assertRaises(TypeError):
            get_unique_col_vals("col1", "not_a_dataframe")


if __name__ == "__main__":
    main()

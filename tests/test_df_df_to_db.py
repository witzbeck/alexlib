"""
Unit tests for the df_to_db function in the alexlib.df module.

The tests are designed to cover different aspects of the df_to_db function:
- Exporting a DataFrame to a database.
- Handling a non-SQLAlchemy engine.
- Handling different configurations of schema, if_exists, and index parameters.
"""

from unittest import TestCase, main
from pandas import DataFrame
from sqlalchemy import create_engine
from sqlalchemy.exc import ArgumentError
from alexlib.df import df_to_db


class TestDfToDb(TestCase):
    """Tests for the df_to_db function."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a test DataFrame
        self.test_df = DataFrame.from_dict({"a": [1, 2, 3], "b": [4, 5, 6]})

        # Create an in-memory SQLite database for testing
        self.engine = create_engine("sqlite:///:memory:")

    def test_database_export(self):
        """Test exporting a DataFrame to a database."""
        try:
            df_to_db(self.test_df, self.engine, "test_table")
        except Exception as e:
            self.fail(f"df_to_db raised an exception: {e}")

    def test_invalid_engine(self):
        """Test df_to_db with a non-SQLAlchemy engine."""
        with self.assertRaises(ArgumentError):
            df_to_db(self.test_df, "not_an_engine", "test_table")

    def test_schema_if_exists_index(self):
        """Test different configurations of schema, if_exists, and index parameters."""
        with self.assertRaises(ValueError):
            df_to_db(
                self.test_df, self.engine, "test_table", if_exists="append", index=False
            )
            df_to_db(self.test_df, self.engine, "test_table", if_exists="fail")

    def tearDown(self) -> None:
        """Tear down test fixtures."""
        self.engine.dispose()
        return super().tearDown()


if __name__ == "__main__":
    main()

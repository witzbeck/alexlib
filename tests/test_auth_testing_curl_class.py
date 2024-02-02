"""
Unit tests for the Curl class in the alexlib.auth module.

This module contains tests to verify the functionality of the Curl class,
which is used for constructing database connection strings and managing
different dialects.
"""

from unittest import TestCase, main
from alexlib.auth import Curl


class TestCurlClass(TestCase):
    """Test cases for the Curl class."""

    def setUp(self):
        """Set up test data."""
        self.username = "testuser"
        self.password = "testpass"
        self.host = "localhost"
        self.port = 5432
        self.database = "testdb"
        self.dialect = "postgres"
        self.curl = Curl(
            username=self.username,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.database,
            dialect=self.dialect,
        )

    def test_instantiation(self):
        """Test Curl instantiation and property values."""
        self.assertEqual(self.curl.username, self.username)
        self.assertEqual(self.curl.password, self.password)
        self.assertEqual(self.curl.host, self.host)
        self.assertEqual(self.curl.port, self.port)
        self.assertEqual(self.curl.database, self.database)
        self.assertEqual(self.curl.dialect, self.dialect)
        self.assertEqual(self.curl.clsname, "Curl")

    def test_connection_string_generation(self):
        """Test connection string generation for different dialects."""
        self.assertEqual(
            self.curl.__str__(),
            f"postgresql+psycopg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}",
        )
        self.curl.dialect = "mysql"
        self.assertEqual(
            self.curl.__str__(),
            f"mysql+mysqldb://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}",
        )

    def test_str_method(self):
        """Test __str__ method for correct connection string formatting."""
        expected_str = f"postgresql+psycopg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        self.assertEqual(str(self.curl), expected_str)


if __name__ == "__main__":
    main()

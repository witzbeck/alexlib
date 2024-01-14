"""
This module contains unit tests for the configuration file handling functionality provided by the alexlib.config.DotEnv class.

The TestConfigFile class in this module extends unittest.TestCase and includes methods to test various aspects of the DotEnv class. These tests ensure the correct initialization of DotEnv objects, the functionality of environment variable retrieval, and the integrity of the environment dictionary created by DotEnv.

Key Features Tested:
- Initialization of DotEnv objects from a given .env file path.
- Verification of the .env file name and instance type.
- Validation of the internal dictionary (envdict) representing environment variables.
- Checking the correct retrieval of random environment variables, ensuring that the values match those in the system environment.

These tests are crucial for verifying the correct behavior of the DotEnv class, which plays a vital role in managing environment variables for applications using the alexlib library.

Usage:
Run this module directly to execute all tests:
    python -m unittest path/to/this/file.py
"""
from os import getenv
from pathlib import Path
from unittest import main
from unittest import TestCase

from alexlib.config import DotEnv


class TestConfigFile(TestCase):
    """Test the config file."""

    def setUp(self) -> None:
        """Set up the test case."""
        self.dotenv = DotEnv.from_path(Path(__file__).parent.parent / ".env")
        self.rand_key = self.dotenv.rand_key
        self.rand_val = getenv(self.rand_key)

    def test_dotenv_init(self) -> None:
        """Test the dotenv init."""
        self.assertEqual(self.dotenv.name, ".env")
        self.assertIsInstance(self.dotenv, DotEnv)

    def test_envdict_init(self) -> None:
        """Test the envdict init."""
        self.assertTrue(issubclass(self.dotenv.envdict.__class__, dict))
        self.assertGreater(len(self.dotenv.envdict), 0)

    def test_gets_rand_env(self) -> None:
        """Test the gets_rand_env method."""
        self.assertEqual(self.dotenv.envdict[self.rand_key], self.rand_val)


if __name__ == "__main__":
    main()

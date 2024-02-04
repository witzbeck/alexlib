"""
Unit Tests for Config File Handling in Alexlib

This module contains a suite of unit tests for validating the functionality of the
Settings class in the alexlib.config module. It primarily focuses on ensuring that
the configuration file handling is correct and reliable.

Key Features Tested:
- Initialization of the Settings object from a JSON configuration file.
- Correct instantiation and properties of the Settings object.
- Functionality to read and process environment variables through the Settings object.

The tests are built using Python's unittest framework, making it easy to integrate
with standard testing and CI/CD workflows.

Note:
The tests rely on a 'settings.json' file located in the parent directory of this test module,
and environment variables specified in this settings file.

Example:
To run these tests, execute the module directly from the command line or use a test runner
compatible with unittest.

    $ python -m unittest path/to/this_module.py
"""
from os import getenv
from pathlib import Path
from unittest import main
from unittest import TestCase

from alexlib.files.config import Settings


class TestConfigFile(TestCase):
    """Test the config file."""

    def setUp(self) -> None:
        """Set up the test case."""
        self.settings = Settings.from_path(
            Path(__file__).parent.parent / "settings.json"
        )
        self.rand_key = self.settings.rand_key
        self.rand_val = getenv(self.rand_key)

    def test_settings_init(self) -> None:
        """Test the settings init."""
        self.assertEqual(self.settings.name, "settings.json")
        self.assertIsInstance(self.settings, Settings)

    def test_envdict_init(self) -> None:
        """Test the envdict init."""
        self.assertTrue(issubclass(self.settings.envdict.__class__, dict))
        self.assertGreater(len(self.settings.envdict), 0)

    def test_gets_rand_env(self) -> None:
        """Test the gets_rand_env method."""
        self.assertEqual(str(self.settings.envdict[self.rand_key]), self.rand_val)


if __name__ == "__main__":
    main()

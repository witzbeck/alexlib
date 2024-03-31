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
from random import choice
from unittest import main, TestCase
from tempfile import NamedTemporaryFile
from sys import version_info

from alexlib.files.config import Settings, DotEnv, ConfigFile


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


class TestDotEnvConfig(TestCase):
    """Test the dotenv file."""

    def setUp(self):
        # Create a temporary file to act as .env
        self.temp_env_file = NamedTemporaryFile(prefix=".env", mode="w+t", delete=False)
        self.path = Path(self.temp_env_file.name)
        # Write example environment variables to the temp file
        self.path.write_text(
            """
                             EXAMPLE_VAR=some_value
                             ANOTHER_VAR=another_value
                             """
        )
        self.dotenv = ConfigFile.from_dotenv(path=self.temp_env_file.name)

    def tearDown(self):
        # Remove the temporary file after tests
        self.path.unlink()

    def test_load_env_vars(self):
        # Verify that the environment variables were set correctly
        self.assertEqual(getenv("EXAMPLE_VAR"), "some_value")
        self.assertEqual(getenv("ANOTHER_VAR"), "another_value")

    def test_dotenv_init(self) -> None:
        """Test the dotenv init."""
        self.assertEqual(self.dotenv.name, ".env")

    def test_envdict_init(self) -> None:
        """Test the envdict init."""
        self.assertTrue(issubclass(self.dotenv.envdict.__class__, dict))
        self.assertGreater(len(self.dotenv.envdict), 0)


class TestDotEnvFile(TestCase):
    """Test the dotenv file."""

    def setUp(self) -> None:
        """Set up the test case."""
        self.path = Path(__file__).parent.parent / ".env"
        self.path.touch()
        self.path.write_text("RAND_ENV=1234")

    def test_dotenv_init(self) -> None:
        """Test the dotenv init."""
        de = DotEnv.from_path(self.path)
        self.assertEqual(de.name, ".env")
        self.assertTrue(de.isdotenv)
        self.assertTrue(de.path.exists())

    def test_envdict_init(self) -> None:
        """Test the envdict init."""
        de = DotEnv.from_parent(".env", __file__)
        self.assertTrue(issubclass(de.envdict.__class__, dict))
        self.assertGreater(len(de.envdict), 0)

    def tearDown(self) -> None:
        """Tear down the test case."""
        self.path.unlink()


class TestJsonSettings(TestCase):
    """Test the json settings file."""

    def setUp(self) -> None:
        """Set up the test case."""
        self.settings = Settings.from_path(
            Path(__file__).parent.parent / "settings.json"
        )

    def test_settings_init(self) -> None:
        """Test the settings init."""
        self.assertEqual(self.settings.name, "settings.json")
        self.assertIsInstance(self.settings, Settings)
        self.assertTrue(self.settings.isjson)

    def test_envdict_init(self) -> None:
        """Test the envdict init."""
        self.assertTrue(issubclass(self.settings.envdict.__class__, dict))
        self.assertGreater(len(self.settings.envdict), 0)

    def test_gets_rand_env(self) -> None:
        """Test the gets_rand_env method."""
        self.assertIsNotNone(getenv(choice(list(self.settings.envdict.keys()))))


if __name__ == "__main__":
    print(version_info)
    main()

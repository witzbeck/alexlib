"""
This module contains unit tests for the Auth class in the alexlib.auth module. It tests the functionality of the Auth class using different scenarios and configurations.

The tests are designed to ensure that the Auth class correctly handles various authentication cases, including handling different types of input (like a list or concatenated string) and validating the presence of authentication store files. It leverages the unittest framework for structuring the tests and assertions.

Additionally, the module uses the DotEnv class from alexlib.config to load environment variables from a .env file, and it uses constants from alexlib.constants for paths and credentials.

Classes:
    TestAuth(TestCase): Contains all the unit tests for testing the Auth class. It includes setup for tests and test cases for different input formats and validation scenarios.

Usage:
    This module is intended to be run as a standalone script to perform unit tests on the Auth class. It can be executed via the command line.

Note:
    The tests in this module depend on the external configuration and state of the file system, particularly the presence of a .env file and authentication store files.
"""
from pathlib import Path
from unittest import main
from unittest import TestCase

from alexlib.auth import Auth
from alexlib.constants import CREDS

proj = Path(__file__).parent.parent
dotenv_path = proj / ".env"


class TestAuth(TestCase):
    """Test the Auth class"""

    def setUp(self) -> None:
        """Set up the test"""
        self.list_name = ["local", "dev", "learning"]
        self.concat_name = ".".join(self.list_name)

    def test_concat_getauth(self) -> None:
        """Test the Auth class"""
        if (CREDS / f"{self.concat_name}.store").exists():
            auth = Auth(self.concat_name)
            self.assertIsInstance(auth, Auth)
        else:
            with self.assertRaises(ValueError):
                Auth(self.concat_name)

    def test_list_getauth(self) -> None:
        """Test the Auth class"""
        if (CREDS / f"{self.concat_name}.store").exists():
            auth = Auth(self.list_name)
            self.assertIsInstance(auth, Auth)
        else:
            with self.assertRaises(ValueError):
                Auth(self.list_name)


if __name__ == "__main__":
    main()

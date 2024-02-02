"""
Unit tests for the alexlib.auth module.

This module contains tests to ensure the correct functionality of the alexlib.auth module, including classes and methods for authentication and secret management. Tests cover the creation of various auth components, their properties, and functionalities.
"""

from unittest import TestCase, main
from alexlib.auth import AuthPart, Username, Password


class TestAlexlibAuth(TestCase):
    """Test suite for the alexlib.auth module."""

    def test_auth_part_length(self):
        """Test the length property of AuthPart."""
        auth_part = AuthPart("testname")
        self.assertEqual(auth_part.length, 8)

    def test_random_username_generation(self):
        """Test random username generation."""
        username = Username.rand()
        self.assertTrue(isinstance(username, Username))
        self.assertTrue(6 <= username.length <= 12)

    def test_random_password_generation(self):
        """Test random password generation."""
        password = Password.rand()
        self.assertTrue(isinstance(password, Password))
        self.assertTrue(12 <= password.length <= 24)


if __name__ == "__main__":
    main()

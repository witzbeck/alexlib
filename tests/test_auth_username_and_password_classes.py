# test_alexlib_auth.py
"""
Unit tests for the alexlib.auth module.

This module contains unit tests for the Username and Password classes in the alexlib.auth module, ensuring proper functionality and adherence to specifications.
"""

from unittest import TestCase, main
from alexlib.auth import AuthPart, Username, Password


class TestUsernameAndPasswordClasses(TestCase):
    """
    Test cases for Username and Password classes in alexlib.auth module.
    """

    def test_inheritance_from_AuthPart(self):
        """
        Test whether Username and Password correctly inherit from AuthPart.
        """
        self.assertTrue(issubclass(Username, AuthPart))
        self.assertTrue(issubclass(Password, AuthPart))

    def test_random_generation_method(self):
        """
        Test the random generation methods (rand) for Username and Password.
        """
        random_username = Username.rand()
        random_password = Password.rand()
        self.assertIsInstance(random_username, Username)
        self.assertIsInstance(random_password, Password)

    def test_length_of_generated_usernames(self):
        """
        Ensure that the length of generated usernames is as expected.
        """
        for _ in range(10):
            random_username = Username.rand()
            self.assertGreaterEqual(len(random_username.name), 6)

    def test_length_of_generated_passwords(self):
        """
        Ensure that the length of generated passwords is as expected.
        """
        for _ in range(10):
            random_password = Password.rand()
            self.assertGreaterEqual(len(random_password.name), 12)


if __name__ == "__main__":
    main()

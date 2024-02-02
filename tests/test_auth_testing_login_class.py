"""
Unit tests for the `Login` class in the `alexlib.auth` module.

This test module focuses on ensuring the correctness and reliability of the
`Login` class, which is used for creating login credentials. It includes tests
for object instantiation and the functionality of generating random credentials.
"""

# Necessary imports
from unittest import TestCase, main
from alexlib.auth import Login, Username, Password


class TestLogin(TestCase):
    """
    Test suite for the `Login` class in the `alexlib.auth` module.
    """

    def test_login_instantiation(self):
        """
        Test the instantiation of a `Login` object with `Username` and `Password`.
        """
        user = Username("testuser")
        pw = Password("testpass123")
        login = Login(user, pw)

        self.assertIsInstance(login, Login, "Login instantiation failed.")
        self.assertEqual(login.user, user, "Username not set correctly in Login.")
        self.assertEqual(login.pw, pw, "Password not set correctly in Login.")

    def test_login_rand_method(self):
        """
        Test the `rand` method to ensure it generates a valid `Login` object
        with random credentials.
        """
        random_login = Login.rand()

        self.assertIsInstance(random_login, Login, "Random Login instantiation failed.")
        self.assertIsInstance(
            random_login.user, Username, "Random Login does not have a valid Username."
        )
        self.assertIsInstance(
            random_login.pw, Password, "Random Login does not have a valid Password."
        )


if __name__ == "__main__":
    main()

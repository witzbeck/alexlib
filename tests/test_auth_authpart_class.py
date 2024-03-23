# test_alexlib_auth.py

from unittest import TestCase, main
from alexlib.auth import AuthPart


class TestAuthPart(TestCase):
    """
    Unit tests for the AuthPart class in the alexlib.auth module.
    """

    def test_instantiation(self):
        """
        Test instantiation of AuthPart with various parameters.
        """
        t, c = "test", "custom"
        # Test with default parameters
        auth_part_default = AuthPart(name=t)
        self.assertEqual(auth_part_default.name, t)
        self.assertEqual(auth_part_default.length, len(t))

        # Test with custom length
        auth_part_custom = AuthPart(name=c)
        self.assertEqual(auth_part_custom.name, c)
        self.assertEqual(auth_part_custom.length, len(c))

    def test_rand_method(self):
        """
        Test the `rand` class method for returning a valid AuthPart object.
        """
        for _ in range(10):
            random_auth_part = AuthPart.rand(letter=True)
            self.assertIsInstance(random_auth_part, AuthPart)
            self.assertEqual(len(random_auth_part.name), random_auth_part.length)

    def test_repr_method(self):
        """
        Test the `__repr__` method for correct string representation.
        """
        auth_part = AuthPart(name="reprtest")
        self.assertEqual(repr(auth_part), "AuthPart(reprtest)")


if __name__ == "__main__":
    main()

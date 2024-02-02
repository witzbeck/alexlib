# test_alexlib_auth.py

"""
Unit tests for the alexlib.auth module.

This module contains a suite of unit tests to verify the functionality of the alexlib.auth module, ensuring its classes and methods behave as expected.
"""

from unittest import TestCase, main
from alexlib.auth import Curl, Auth
from pathlib import Path
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
from tempfile import TemporaryDirectory


class TestAuth(TestCase):
    """
    Test cases for the alexlib.auth module.
    """

    def setUp(self):
        """
        Set up test fixtures before each test method.
        """
        self.test_auth = Auth.from_dict(
            name="test_auth",
            dict_={
                "username": "test_user",
                "password": "test_pass",
                "key": "value",
                "host": "test_host",
                "port": "test_port",
                "database": "test_database",
            },
        )

    def test_instantiation(self):
        """
        Test instantiation of Auth class and ensure correct initialization of attributes.
        """
        test_auth = Auth(name="test_auth")
        self.assertIsInstance(test_auth, Auth)
        self.assertEqual(test_auth.name, "test_auth")

    def test_key_and_store_file_handling(self):
        """
        Test key and store file handling including creation, reading, and writing.
        """
        test_auth = Auth(name="test_auth")
        self.assertTrue(test_auth.keypath.exists())
        self.assertTrue(test_auth.storepath.exists())

    def test_update_value_method(self):
        """
        Test `update_value` method for updating a single credential.
        """
        self.test_auth.update_value("new_key", "new_value")
        self.assertEqual(str(self.test_auth.store.get_cred("new_key")), "new_value")

    def test_update_values_method(self):
        """
        Test `update_values` method for updating multiple credentials.
        """
        updates = {"key1": "value1", "key2": "value2"}
        self.test_auth.update_values(updates)
        for key, value in updates.items():
            self.assertEqual(str(self.test_auth.store.get_cred(key)), value)

    def test_curl_and_authentication_objects(self):
        """
        Test generation of `Curl` and authentication objects (`basic`, `digest`).
        """
        self.assertIsInstance(self.test_auth.curl, Curl)
        self.assertIsInstance(self.test_auth.basic, HTTPBasicAuth)
        self.assertIsInstance(self.test_auth.digest, HTTPDigestAuth)

    def test_class_methods(self):
        """
        Test `from_dict`, `from_path`, and `from_env` class methods.
        """
        test_dict = {"username": "user", "password": "pass"}
        test_auth_from_dict = Auth.from_dict("test_auth", test_dict)
        self.assertIsInstance(test_auth_from_dict, Auth)

        with TemporaryDirectory() as tempdir:
            test_path = Path(tempdir, "test_auth")
            with self.assertRaises(FileNotFoundError):
                Auth.from_path(test_path)


if __name__ == "__main__":
    main()

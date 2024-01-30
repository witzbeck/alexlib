# test_alexlib_auth.py

"""
Unit tests for the alexlib.auth module.

This test module covers integration testing for the alexlib.auth module,
focusing on the interactions between its various classes and real-world
usage scenarios such as creating, updating, and using credentials.
"""

from unittest import TestCase, main
from alexlib.auth import Auth, SecretStore, Curl, Username, Password, Server, Login
from pathlib import Path
from tempfile import TemporaryDirectory


class TestAlexlibAuthIntegration(TestCase):
    """
    Integration tests for the alexlib.auth module.
    """

    def setUp(self):
        """
        Set up environment for each test.
        """
        self.temp_dir = TemporaryDirectory()
        self.test_auth_name = "test_auth"
        self.test_auth_path = Path(self.temp_dir.name) / "auth_store.json"

    def tearDown(self):
        """
        Clean up after each test.
        """
        self.temp_dir.cleanup()

    def test_creating_and_using_credentials(self):
        """
        Test the creation of credentials and their usage in various classes.
        """
        username = Username.rand()
        password = Password.rand()
        server = Server.rand()

        # Creating a login and a server instance
        login = Login(user=username, pw=password)
        curl = Curl(
            username=str(username),
            password=str(password),
            host=server.host,
            port=server.port,
        )

        self.assertEqual(login.user.name, curl.username)
        self.assertEqual(login.pw.name, curl.password)

    def test_updating_credentials_in_Auth(self):
        """
        Test updating credentials in the Auth class.
        """
        # Creating an Auth instance
        auth = Auth.from_dict(
            self.test_auth_name, {"username": "user1", "password": "pass1"}
        )
        auth.store.path = self.test_auth_path

        # Updating credentials
        auth.update_value("username", "user2")
        auth.update_value("password", "pass2")

        # Verifying updates
        updated_username = auth.run_getattr("get_username")
        updated_password = auth.run_getattr("get_password")

        self.assertEqual(str(updated_username), "user2")
        self.assertNotEqual(updated_password, "pass2")
        self.assertEqual(repr(updated_password), "<SecretValue>")

    def test_secret_store_encryption_and_decryption(self):
        """
        Test encryption and decryption of credentials in SecretStore.
        """
        secret_store = SecretStore.from_dict(
            {"username": "user", "password": "pass"}, path=self.test_auth_path
        )
        secret_store.secrets = SecretStore.encode_str_dict(secret_store.secrets)

        # Testing encryption and decryption
        encrypted_secrets = secret_store.secrets
        decrypted_secrets = {k: str(v) for k, v in encrypted_secrets.items()}

        self.assertEqual(decrypted_secrets["username"], "user")
        self.assertEqual(decrypted_secrets["password"], "pass")


if __name__ == "__main__":
    main()

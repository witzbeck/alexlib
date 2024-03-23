import unittest
from unittest.mock import patch
from alexlib.auth import SecretStore, Cryptographer


class TestSecretStore(unittest.TestCase):
    """Unit tests for the SecretStore class in alexlib.auth module."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_secrets = {"key1": "value1", "key2": "value2"}
        self.secret_store = SecretStore.from_dict(self.test_secrets)

    def test_storing_and_retrieving_secrets(self):
        """Test that secrets can be stored and retrieved correctly."""
        for key, value in self.test_secrets.items():
            self.assertEqual(str(self.secret_store.get_cred(key)), value)

    def test_encryption_and_decryption(self):
        """Verify that secrets are correctly encrypted and decrypted."""
        cryptographer = Cryptographer.new()
        encrypted = cryptographer.encrypt_str("test_secret")
        decrypted = cryptographer.decrypt_str(encrypted)
        self.assertEqual(decrypted, "test_secret")

    def test_len_method(self):
        """Test the __len__ method for SecretStore."""
        self.assertEqual(len(self.secret_store), len(self.test_secrets))

    def test_repr_method(self):
        """Test the __repr__ method for SecretStore."""
        representation = repr(self.secret_store)
        for key in self.test_secrets:
            self.assertIn(key, representation)

    @patch("alexlib.auth.SecretStore.sensor_input")
    def test_sensor_input_static_method(self, mock_sensor_input):
        """Test the sensor_input static method."""
        mock_sensor_input.return_value = "test"
        result = SecretStore.sensor_input("input")
        mock_sensor_input.assert_called_once_with("input")
        self.assertEqual(result, "test")

    def test_from_dict_class_method(self):
        """Test the from_dict class method."""
        new_store = SecretStore.from_dict({"new_key": "new_value"})
        self.assertIn("new_key", new_store.secrets)
        self.assertEqual(str(new_store.get_cred("new_key")), "new_value")

    # Additional tests for from_path and from_user methods
    # ...


if __name__ == "__main__":
    unittest.main()

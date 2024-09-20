# test_alexlib_auth.py

"""
Unit tests for the alexlib.auth module.

This test module covers integration testing for the alexlib.auth module,
focusing on the interactions between its various classes and real-world
usage scenarios such as creating, updating, and using credentials.
"""

from pathlib import Path

from alexlib.auth import Auth, SecretStore


def test_updating_credentials_in_Auth(auth: Auth, auth_path: Path):
    """
    Test updating credentials in the Auth class.
    """
    auth.store.path = auth_path

    # Updating credentials
    auth.update_value("username", "user2")
    auth.update_value("password", "pass2")

    # Verifying updates
    updated_username = auth.run_getattr("get_username")
    updated_password = auth.run_getattr("get_password")

    assert str(updated_username) == "user2", f"Expected user2, got {updated_username}"
    assert str(updated_password) == "pass2", f"Expected pass2, got {updated_password}"
    assert (
        repr(updated_password) == "<SecretValue>"
    ), f"Expected <SecretValue>, got {updated_password}"


def test_store_encryption_and_decryption(secret_store: SecretStore):
    """
    Test encryption and decryption of secrets in the SecretStore class.
    """
    secret_store.secrets = SecretStore.encode_str_dict(secret_store.secrets)

    # Testing encryption and decryption
    encrypted_secrets = secret_store.secrets
    decrypted_secrets = {k: str(v) for k, v in encrypted_secrets.items()}
    assert decrypted_secrets["username"] == "user"
    assert decrypted_secrets["password"] == "pass"

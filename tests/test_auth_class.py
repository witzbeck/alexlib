"""
Unit tests for the alexlib.auth module.

This module contains a suite of unit tests to verify the functionality of the alexlib.auth module, ensuring its classes and methods behave as expected.
"""

from pathlib import Path

from pytest import raises
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

from alexlib.auth import Auth, AuthPart, Curl, Login, Password, Server, Username


def test_auth_part(auth_part: AuthPart):
    assert issubclass(auth_part.__class__, AuthPart)
    assert len(auth_part.name) == len(auth_part)


def test_auth_part_repr(auth_part: AuthPart):
    assert auth_part.__class__.__name__ in repr(auth_part)


def test_login(login: Login):
    assert isinstance(login, Login)
    assert isinstance(login.user, Username)
    assert isinstance(login.pw, Password)


def test_server(server: Server):
    assert isinstance(server, Server)
    assert isinstance(server.host, str)
    assert isinstance(server.port, int)


def test_auth_init(auth: Auth):
    """Test the initialization of an Auth object."""
    assert isinstance(auth, Auth)


def test_auth_name(auth: Auth):
    """Test the `name` attribute of an Auth object."""
    assert auth.name == "test_auth"
    assert isinstance(auth.name, str)


def test_auth_keypath(auth: Auth):
    """Test the `keypath` attribute of an Auth object."""
    assert auth.keypath.exists()
    assert isinstance(auth.keypath, Path)


def test_auth_storepath(auth: Auth):
    """Test the `storepath` attribute of an Auth object."""
    assert auth.storepath.exists()
    assert isinstance(auth.storepath, Path)


def test_update_value(auth: Auth):
    """Test the `update_value` method of an Auth object."""
    auth.update_value("new_key", "new_value")
    assert str(auth.store.get_cred("new_key")) == "new_value"


def test_update_values(auth: Auth):
    """Test the `update_values` method of an Auth object."""
    updates = {"key1": "value1", "key2": "value2"}
    auth.update_values(updates)
    assert all(str(auth.store.get_cred(key)) == value for key, value in updates.items())


def test_auth_curl(auth: Auth):
    """Test the `curl` attribute of an Auth object."""
    assert isinstance(auth.curl, Curl)


def test_auth_basic(auth: Auth):
    """Test the `basic` attribute of an Auth object."""
    assert isinstance(auth.basic, HTTPBasicAuth)


def test_auth_digest(auth: Auth):
    """Test the `digest` attribute of an Auth object."""
    assert isinstance(auth.digest, HTTPDigestAuth)


def test_auth_from_nonexistent_path():
    """Test the `from_path` class method of the Auth class with a nonexistent path."""
    with raises(FileNotFoundError):
        Auth.from_path(Path("nonexistent_path"))


def test_updating_credentials_in_Auth(auth: Auth, auth_path: Path):
    """Test updating credentials in the Auth class."""
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

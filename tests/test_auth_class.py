"""
Unit tests for the alexlib.auth module.

This module contains a suite of unit tests to verify the functionality of the alexlib.auth module, ensuring its classes and methods behave as expected.
"""

from pathlib import Path

from pytest import raises
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

from alexlib.auth import Auth, Curl


def test_auth_init(auth: Auth):
    """
    Test the initialization of an Auth object.
    """
    assert isinstance(auth, Auth)


def test_auth_name(auth: Auth):
    """
    Test the `name` attribute of an Auth object.
    """
    assert auth.name == "test_auth"
    assert isinstance(auth.name, str)


def test_auth_keypath(auth: Auth):
    """
    Test the `keypath` attribute of an Auth object.
    """
    assert auth.keypath.exists()
    assert isinstance(auth.keypath, Path)


def test_auth_storepath(auth: Auth):
    """
    Test the `storepath` attribute of an Auth object.
    """
    assert auth.storepath.exists()
    assert isinstance(auth.storepath, Path)


def test_update_value(auth: Auth):
    """
    Test the `update_value` method of an Auth object.
    """
    auth.update_value("new_key", "new_value")
    assert str(auth.store.get_cred("new_key")) == "new_value"


def test_update_values(auth: Auth):
    """
    Test the `update_values` method of an Auth object.
    """
    updates = {"key1": "value1", "key2": "value2"}
    auth.update_values(updates)
    assert all(str(auth.store.get_cred(key)) == value for key, value in updates.items())


def test_auth_curl(auth: Auth):
    """
    Test the `curl` attribute of an Auth object.
    """
    assert isinstance(auth.curl, Curl)


def test_auth_basic(auth: Auth):
    """
    Test the `basic` attribute of an Auth object.
    """
    assert isinstance(auth.basic, HTTPBasicAuth)


def test_auth_digest(auth: Auth):
    """
    Test the `digest` attribute of an Auth object.
    """
    assert isinstance(auth.digest, HTTPDigestAuth)


def test_auth_from_nonexistent_path():
    """
    Test the `from_path` class method of the Auth class with a nonexistent path.
    """
    with raises(FileNotFoundError):
        Auth.from_path(Path("nonexistent_path"))

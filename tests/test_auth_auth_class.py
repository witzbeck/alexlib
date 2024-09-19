"""
Unit tests for the alexlib.auth module.

This module contains a suite of unit tests to verify the functionality of the alexlib.auth module, ensuring its classes and methods behave as expected.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

from pytest import raises
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

from alexlib.auth import Curl, Auth


def test_auth_init(test_auth: Auth):
    """
    Test the initialization of an Auth object.
    """
    assert isinstance(test_auth, Auth)


def test_auth_name(test_auth: Auth):
    """
    Test the `name` attribute of an Auth object.
    """
    assert test_auth.name == "test_auth"
    assert isinstance(test_auth.name, str)


def test_auth_keypath(test_auth: Auth):
    """
    Test the `keypath` attribute of an Auth object.
    """
    assert test_auth.keypath.exists()
    assert isinstance(test_auth.keypath, Path)


def test_auth_storepath(test_auth: Auth):
    """
    Test the `storepath` attribute of an Auth object.
    """
    assert test_auth.storepath.exists()
    assert isinstance(test_auth.storepath, Path)


def test_update_value(test_auth: Auth):
    """
    Test the `update_value` method of an Auth object.
    """
    test_auth.update_value("new_key", "new_value")
    assert str(test_auth.store.get_cred("new_key")) == "new_value"


def test_update_values(test_auth: Auth):
    """
    Test the `update_values` method of an Auth object.
    """
    updates = {"key1": "value1", "key2": "value2"}
    test_auth.update_values(updates)
    assert all(
        str(test_auth.store.get_cred(key)) == value for key, value in updates.items()
    )


def test_auth_curl(test_auth: Auth):
    """
    Test the `curl` attribute of an Auth object.
    """
    assert isinstance(test_auth.curl, Curl)


def test_auth_basic(test_auth: Auth):
    """
    Test the `basic` attribute of an Auth object.
    """
    assert isinstance(test_auth.basic, HTTPBasicAuth)


def test_auth_digest(test_auth: Auth):
    """
    Test the `digest` attribute of an Auth object.
    """
    assert isinstance(test_auth.digest, HTTPDigestAuth)


def test_auth_from_nonexistent_path():
    """
    Test the `from_path` class method of the Auth class with a nonexistent path.
    """
    with TemporaryDirectory() as tempdir:
        test_path = Path(tempdir, "test_auth")
        with raises(FileNotFoundError):
            Auth.from_path(test_path)

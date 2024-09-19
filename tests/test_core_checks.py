"""Test core functions."""

from os import environ
from pathlib import Path

from pytest import mark, raises

from alexlib.core import (
    chkenv,
    chktext,
    chktype,
    iswindows,
    islinux,
    ismacos,
)


def test_chktype_path_not_exist() -> None:
    """Test chktype function with Path object."""
    test_path = Path("non_existing_file.txt")  # Assume this file does not exist
    with raises(FileNotFoundError):
        chktype(test_path, Path)


def test_isplatform() -> None:
    """Test isplatform function."""
    assert any((iswindows(), islinux(), ismacos()))


@mark.parametrize(
    "text, kwargs, expected",
    (
        ("example text", {"prefix": "Exa"}, True),
        ("example text", {"prefix": "test"}, False),
        ("example text", {"value": "ample"}, True),
        ("example text", {"value": "none"}, False),
        ("example text", {"suffix": "text"}, True),
        ("example text", {"suffix": "exam"}, False),
        ("abc", {"prefix": "a"}, True),
        ("abc", {"prefix": "b"}, False),
        ("abc", {"suffix": "c"}, True),
        ("abc", {"suffix": "b"}, False),
        ("abc", {"value": "b"}, True),
        ("abc", {"value": "a"}, True),
    ),
)
def test_chktext(text: str, kwargs: dict, expected: bool) -> None:
    """Test chktext function."""
    assert chktext(text, **kwargs) == expected


def test_chktext_raises() -> None:
    """Test chktext function with no input."""
    with raises(ValueError):
        chktext("example text")


def test_file_exists(test_file: Path) -> None:
    """Test chktype function with Path object."""
    assert chktype(test_file, Path, mustexist=True) == test_file


def test_chktype_incorrect() -> None:
    """Test chktype function with incorrect input."""
    with raises(TypeError):
        chktype("value", int)


@mark.parametrize(
    "value, type_",
    (
        (123, int),
        ("abc", str),
        (Path(__file__), Path),
        ([1, 2, 3], list),
        ({"a": 1, "b": 2}, dict),
        (True, bool),
    ),
)
def test_chktype_correct(value: int, type_: type) -> None:
    """Test chktype function with correct input."""
    assert chktype(value, type_) == value


def test_default_for_non_existing_variable() -> None:
    """Test chkenv function with non existing variable."""
    assert chkenv("NON_EXISTING_VAR", need=False) is None


def test_default_for_empty_variable() -> None:
    """Test chkenv function with empty variable."""
    assert chkenv("EMPTY_VAR", need=False, ifnull="default") == "default"
    with raises(ValueError):
        chkenv("EMPTY_VAR", need=True)


@mark.parametrize(
    "env, value, astype",
    (
        ("TRUE_VAR", True, bool),
        ("FALSE_VAR", False, bool),
        ("TRUE_VAR", 1, int),
        ("FALSE_VAR", 0, int),
        ("TRUE_VAR", "True", str),
        ("FALSE_VAR", "False", str),
        ("TEST_VAR", 123, int),
    ),
)
def test_chkenv_bool(env: str, value: bool, astype: type) -> None:
    """Test chkenv function with boolean values."""
    environ[env] = str(value)
    assert chkenv(env, astype=astype) == value

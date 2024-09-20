"""Test core functions."""

from pathlib import Path
from typing import Any

from pytest import mark

from alexlib.core import (
    isdunder,
    ishidden,
    isnone,
    istrue,
)
from alexlib.files.utils import (
    is_dotenv,
    is_json,
)

ISJSON_TRUE_STRINGS = (
    "test.json",
    "settings.json",
    "config.json",
    "package.json",
)
ISJSON_TRUE_PATHS = (
    Path("test.json"),
    Path("settings.json"),
    Path("config.json"),
    Path("package.json"),
)
ISJSON_FALSE_STRINGS = (
    "test.txt",
    "test",
)
ISJSON_FALSE_PATHS = (
    Path("test.txt"),
    Path("test"),
)
ISDOTENV_TRUE_STRINGS = (
    ".env",
    ".env.example",
    ".env.local",
    ".env.test",
)
ISDOTENV_TRUE_PATHS = (
    Path(".env"),
    Path(".env.example"),
    Path(".env.local"),
    Path(".env.test"),
)
ISDOTENV_FALSE_STRINGS = (
    "env.development",
    "settings.json",
    "config.json",
    "package.json",
    "test.json",
    "test.txt",
)
ISDOTENV_FALSE_PATHS = (
    Path("env.development"),
    Path("settings.json"),
    Path("config.json"),
    Path("package.json"),
    Path("test.json"),
    Path("test.txt"),
)
ISJSON_TRUE = ISJSON_TRUE_STRINGS + ISJSON_TRUE_PATHS
ISJSON_FALSE = ISJSON_FALSE_STRINGS + ISJSON_FALSE_PATHS
ISDOTENV_TRUE = ISDOTENV_TRUE_STRINGS + ISDOTENV_TRUE_PATHS
ISDOTENV_FALSE = ISDOTENV_FALSE_STRINGS + ISDOTENV_FALSE_PATHS
ALL_STRINGS = (
    ISJSON_TRUE_STRINGS
    + ISJSON_FALSE_STRINGS
    + ISDOTENV_TRUE_STRINGS
    + ISDOTENV_FALSE_STRINGS
)
ALL_PATHS = (
    ISJSON_TRUE_PATHS + ISJSON_FALSE_PATHS + ISDOTENV_TRUE_PATHS + ISDOTENV_FALSE_PATHS
)

ISTRUE_TRUE = (
    True,
    "True",
    "true",
    "t",
    "T",
    "1",
)
ISTRUE_FALSE = (
    False,
    "False",
    "false",
    "f",
    "F",
    "0",
    "",
    None,
)
ISNONE_TRUE = (
    "None",
    "none",
    "",
    None,
)
ISNONE_FALSE = (
    True,
    "test",
    1,
    0.0,
)
ISDUNDER_TRUE = ("__dunder__",)
ISDUNDER_FALSE = (
    "dunder__",
    "__dunder",
    "test",
)
ISHIDDEN_TRUE = (
    "_hidden",
    "_hidden_",
)
ISHIDDEN_FALSE = (
    "hidden_",
    "test",
)


@mark.fast
@mark.parametrize("is_dotenv_true", ISDOTENV_TRUE)
def test_is_dotenv_true(is_dotenv_true: bool) -> None:
    """Test to check .env detection"""
    assert is_dotenv(is_dotenv_true) is True


@mark.fast
@mark.parametrize("is_dotenv_false", ISDOTENV_FALSE)
def test_is_dotenv_false(is_dotenv_false: bool) -> None:
    """Test to check non-.env files"""
    assert is_dotenv(is_dotenv_false) is False


@mark.fast
@mark.parametrize("is_json_true", ISJSON_TRUE)
def test_is_json_true(is_json_true: bool) -> None:
    """Test to check JSON file detection"""
    assert is_json(is_json_true) is True


@mark.fast
@mark.parametrize("is_json_false", ISJSON_FALSE)
def test_is_json_false(is_json_false: bool) -> None:
    assert is_json(is_json_false) is False


@mark.fast
@mark.parametrize("a_string", ALL_STRINGS)
def test_is_a_string(a_string: str) -> None:
    assert isinstance(a_string, str)


@mark.fast
@mark.parametrize("a_path", ALL_PATHS)
def test_is_a_path(a_path: Path) -> None:
    assert isinstance(a_path, Path)


@mark.fast
@mark.parametrize("value", ISTRUE_TRUE)
def test_istrue_true(value: Any) -> None:
    """Test istrue function."""
    assert istrue(value) is True


@mark.fast
@mark.parametrize("value", ISTRUE_FALSE)
def test_istrue_false(value: Any) -> None:
    """Test istrue function."""
    assert istrue(value) is False


@mark.fast
@mark.parametrize("value", ISNONE_TRUE)
def test_isnone_true(value: Any) -> None:
    """Test isnone function."""
    assert isnone(value) is True


@mark.fast
@mark.parametrize("value", ISNONE_FALSE)
def test_isnone_false(value: Any) -> None:
    """Test isnone function."""
    assert isnone(value) is False


@mark.fast
@mark.parametrize("value", ISDUNDER_TRUE)
def test_isdunder_true(value: Any) -> None:
    """Test isdunder function."""
    assert isdunder(value) is True


@mark.fast
@mark.parametrize("value", ISDUNDER_FALSE)
def test_isdunder_false(value: Any) -> None:
    """Test isdunder function."""
    assert isdunder(value) is False


@mark.fast
@mark.parametrize("value", ISHIDDEN_TRUE)
def test_ishidden_true(value: Any) -> None:
    """Test ishidden function."""
    assert ishidden(value) is True

"""Test core functions."""

from typing import Any

from pytest import mark

from alexlib.core import (
    isdunder,
    ishidden,
    isnone,
    istrue,
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

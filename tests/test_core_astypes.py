"""Test core functions."""

from datetime import timezone

from pytest import fixture, mark

from alexlib.core import (
    asdict,
    aslist,
    get_local_tz,
)


def test_get_local_tz():
    """Ensure it returns the correct local timezone."""
    assert isinstance(
        get_local_tz(), timezone
    ), "The returned value is not a timezone instance."


@mark.parametrize(
    "string, sep, expected",
    [
        ("a,b,c", ",", ["a", "b", "c"]),
        ("a|b|c", "|", ["a", "b", "c"]),
    ],
)
def test_aslist(string: str, sep: str, expected: list[str]) -> None:
    lst = aslist(string, sep=sep)
    assert isinstance(lst, list)
    assert lst == expected


@fixture
def _testclass():
    class TestClass:
        def __init__(self):
            self.a = 1
            self.b = 2
            self._c = 3

    return TestClass()


def test_asdict(_testclass):
    dct = asdict(_testclass)
    assert isinstance(dct, dict)
    assert dct == {"a": 1, "b": 2}

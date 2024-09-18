"""Test core functions."""

from pytest import fixture, mark

from alexlib.core import (
    asdict,
    aslist,
    concat_lists,
)


@mark.parametrize(
    "nested, expected",
    [
        ([[1, 2], [3, 4]], [1, 2, 3, 4]),
        ([[1, 2], [3, [4, 5]]], [1, 2, 3, 4, 5]),
    ],
)
def test_concat_lists(nested, expected):
    """Test with various lists of lists."""
    (
        concat_lists(nested) == expected,
        "Failed to correctly concatenate lists.",
    )


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

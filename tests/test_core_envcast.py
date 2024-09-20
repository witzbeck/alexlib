"""Test core functions."""

from pytest import mark, raises

from alexlib.core import envcast


@mark.parametrize(
    "string, type_, expected",
    [
        ("1", int, 1),
        ("1.0", float, 1.0),
        ("True", bool, True),
        ("true", bool, True),
        ("t", bool, True),
        ("T", bool, True),
        ("yes", bool, True),
        ("y", bool, True),
        ("on", bool, True),
        ("0", int, 0),
        ("0.0", float, 0.0),
        ("False", bool, False),
        ("false", bool, False),
        ("f", bool, False),
        ("F", bool, False),
        ("no", bool, False),
        ("n", bool, False),
        ("off", bool, False),
        ("[]", list, []),
        ("[1,2,3]", list, [1, 2, 3]),
        ("['a','b','c']", list, ["a", "b", "c"]),
        ('{"a":1,"b":2}', dict, {"a": 1, "b": 2}),
        ('{"a":1,"b":2,"c":3}', dict, {"a": 1, "b": 2, "c": 3}),
        ('{"a":1,"b":2,"c":3,"d":4}', dict, {"a": 1, "b": 2, "c": 3, "d": 4}),
    ],
)
def test_envcast_trues(string: str, type_: type, expected: bool) -> None:
    """Test envcast function for trues."""
    assert envcast(string, type_) == expected


@mark.parametrize(
    "value",
    ("None", "none", ""),
)
def test_envcast_falses(value: str) -> None:
    """Test envcast function for falses."""
    with raises(ValueError):
        envcast(value, list, need=True)

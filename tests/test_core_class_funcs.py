"""Tests for the `core` module's class functions."""

from pytest import FixtureRequest, fixture

from alexlib.core import (
    get_attrs,
    get_objects_by_attr,
)

ATTRS = (
    "public_attr",
    "_hidden_attr",
    "__dunder_attr__",
)
METHODS = (
    "public_method",
    "_hidden_method",
    "__dunder_method__",
)


@fixture(scope="module", params=ATTRS)
def attr(request: FixtureRequest) -> str:
    return request.param


@fixture(scope="module", params=METHODS)
def method(request: FixtureRequest) -> str:
    return request.param


@fixture(scope="module", params=ATTRS + METHODS)
def attr_or_method(request: FixtureRequest) -> str:
    return request.param


class _TestClass:
    """Test class for `get_attrs` function."""

    def __init__(
        self,
        public_attr: str = "public",
        hidden_attr: str = "hidden",
        dunder_attr: str = "dunder",
    ) -> None:
        self.public_attr = public_attr
        self._hidden_attr = hidden_attr
        self.__dunder_attr__ = dunder_attr

    def public_method(self):
        return self.public_attr

    def _hidden_method(self):
        return self._hidden_attr

    def __dunder_method__(self):
        return self.__dunder_attr__


@fixture(scope="module")
def test_obj():
    return _TestClass()


@fixture(scope="module")
def all_attrs(test_obj):
    return get_attrs(
        test_obj,
        hidden=True,
        dunder=True,
        methods=True,
    )


@fixture(scope="module")
def public_attrs(test_obj):
    return get_attrs(test_obj)


@fixture(scope="module")
def public_methods(test_obj):
    return get_attrs(test_obj, methods=True)


@fixture(scope="module")
def hidden_attrs(test_obj):
    return get_attrs(test_obj, hidden=True)


@fixture(scope="module")
def hidden_methods(test_obj):
    return get_attrs(test_obj, methods=True, hidden=True)


@fixture(scope="module")
def dunder_attrs(test_obj):
    return get_attrs(test_obj, dunder=True)


@fixture(scope="module")
def dunder_methods(test_obj):
    return get_attrs(test_obj, methods=True, dunder=True)


def test_get_all_attrs(all_attrs, attr_or_method):
    assert attr_or_method in all_attrs


def test_get_public_attrs(public_attrs):
    assert public_attrs == {"public_attr": "public"}


def test_get_public_methods(public_methods):
    assert "public_method" in public_methods
    assert "_hidden_method" not in public_methods


def test_get_hidden_attrs(hidden_attrs):
    assert hidden_attrs == {
        "public_attr": "public",
        "_hidden_attr": "hidden",
    }


def test_get_hidden_methods(hidden_methods):
    assert "_hidden_method" in hidden_methods
    assert "public_method" in hidden_methods
    assert "__dunder_method__" not in hidden_methods


def test_get_dunder_attrs(dunder_attrs):
    assert "__dunder_attr__" in dunder_attrs
    assert "public_attr" in dunder_attrs


def test_get_dunder_methods(dunder_methods):
    assert "__dunder_method__" in dunder_methods
    assert "public_method" in dunder_methods


def test_with_specific_attribute() -> None:
    """Test with specific attribute."""

    class _TestObj:
        def __init__(self, name):
            self.name = name

    objects = [_TestObj("test1"), _TestObj("test2")]
    result = get_objects_by_attr(objects, "name", "test1")
    assert len(result) == 1
    assert result[0].name == "test1"

"""Tests for the `core` module's class functions."""
from unittest import TestCase, main

from alexlib.core import (
    get_attrs,
    get_objects_by_attr,
)


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


class TestGetAttrs(TestCase):
    """Test the `get_attrs` function."""

    def setUp(self):
        self.test_obj = _TestClass()

    def test_get_all_attrs(self):
        d = get_attrs(
            self.test_obj,
            include_hidden=True,
            include_dunder=True,
            include_methods=True,
        )
        self.assertIn("public_attr", d.keys())
        self.assertIn("_hidden_attr", d.keys())
        self.assertIn("__dunder_attr__", d.keys())
        self.assertIn("public_method", d.keys())
        self.assertIn("_hidden_method", d.keys())
        self.assertIn("__dunder_method__", d.keys())

    def test_get_public_attrs(self):
        self.assertDictEqual(
            get_attrs(self.test_obj),
            {
                "public_attr": "public",
            },
        )

    def test_get_public_methods(self):
        d = get_attrs(self.test_obj, include_methods=True)
        self.assertIn("public_method", d)
        self.assertNotIn("_hidden_method", d)

    def test_get_hidden_attrs(self):
        self.assertDictEqual(
            get_attrs(self.test_obj, include_hidden=True),
            {
                "public_attr": "public",
                "_hidden_attr": "hidden",
            },
        )

    def test_get_hidden_methods(self):
        d = get_attrs(self.test_obj, include_methods=True, include_hidden=True)
        self.assertIn("_hidden_method", d)
        self.assertIn("public_method", d)
        self.assertNotIn("__dunder_method__", d)

    def test_get_dunder_attrs(self):
        d = get_attrs(self.test_obj, include_dunder=True)
        self.assertIn("__dunder_attr__", d)
        self.assertIn("public_attr", d)

    def test_get_dunder_methods(self):
        d = get_attrs(self.test_obj, include_methods=True, include_dunder=True)
        self.assertIn("__dunder_method__", d)
        self.assertIn("public_method", d)


class TestGetObjectsByAttr(TestCase):
    """Test the `get_objects_by_attr` function."""

    def test_with_specific_attribute(self) -> None:
        """Test with specific attribute."""

        class _TestObj:
            def __init__(self, name):
                self.name = name

        objects = [_TestObj("test1"), _TestObj("test2")]
        result = get_objects_by_attr(objects, "name", "test1")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "test1")

    def test_with_non_existing_attribute(self):
        objects = [{"name": "test1"}, {"name": "test2"}]
        with self.assertRaises(AttributeError):
            get_objects_by_attr(objects, "non_exist", "value")


if __name__ == "__main__":
    main()

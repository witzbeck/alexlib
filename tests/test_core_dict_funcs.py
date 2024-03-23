"""Tests for the `alexlib.core` module."""

from unittest import TestCase, main
from unittest.mock import patch

from alexlib.core import (
    invert_dict,
    mk_dictvals_distinct,
    show_dict,
    show_environ,
)


class TestClass:
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


class TestShowDict(TestCase):
    @patch("builtins.print")
    def test_show_dict_with_dict(self, mock_print):
        show_dict({"a": 1, "b": 2})
        mock_print.assert_called()

    @patch("builtins.print")
    def test_show_dict_with_list_of_dicts(self, mock_print):
        show_dict([{"a": 1}, {"b": 2}])
        self.assertEqual(mock_print.call_count, 4)

    @patch("builtins.print")
    def test_show_dict_with_show_environ(self, mock_print):
        show_environ()
        mock_print.assert_called()


class TestMkDictvalsDistinct(TestCase):
    """Test the `mk_dictvals_distinct` function."""

    def test_with_list_values_including_duplicates(self) -> None:
        """Test with list values including duplicates."""
        test_dict = {"a": [1, 2, 2, 3], "b": ["x", "y", "y"]}
        expected = {"a": [1, 2, 3], "b": ["x", "y"]}
        result = mk_dictvals_distinct(test_dict)
        self.assertIn("a", result)
        self.assertIn("b", result)
        result["a"].sort()
        result["b"].sort()
        self.assertListEqual(result["a"], expected["a"])
        self.assertListEqual(result["b"], expected["b"])


class TestInvertDict(TestCase):
    """Test the `invert_dict` function."""

    def test_with_dict(self) -> None:
        """Test with a dictionary."""
        test_dict = {"a": 1, "b": 2}
        expected = {1: "a", 2: "b"}
        result = invert_dict(test_dict)
        self.assertEqual(result, expected)

    def test_with_list_of_tuples(self) -> None:
        """Test with a list of tuples."""
        test_list = [("a", 1), ("b", 2)]
        expected = {1: "a", 2: "b"}
        result = invert_dict(dict(test_list))
        self.assertEqual(result, expected)


if __name__ == "__main__":
    main()

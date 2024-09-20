"""Tests for the `alexlib.core` module."""

from unittest import TestCase
from unittest.mock import patch

from alexlib.core import (
    invert_dict,
    mk_dictvals_distinct,
    show_dict,
    show_environ,
)


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


def test_with_list_values_including_duplicates() -> None:
    """Test with list values including duplicates."""
    test_dict = {"a": [1, 2, 2, 3], "b": ["x", "y", "y"]}
    expected = {"a": [1, 2, 3], "b": ["x", "y"]}
    result = mk_dictvals_distinct(test_dict)
    assert all(
        (sorted(result[key]) == sorted(expected[key]) for key in test_dict.keys())
    )


def test_with_dict() -> None:
    """Test with a dictionary."""
    test_dict = {"a": 1, "b": 2}
    expected = {1: "a", 2: "b"}
    result = invert_dict(test_dict)
    assert sorted(result.keys()) == sorted(expected.keys())
    assert sorted(result.values()) == sorted(expected.values())

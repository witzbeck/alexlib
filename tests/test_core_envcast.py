"""Test core functions."""
from unittest import main, TestCase

from alexlib.core import (
    envcast,
)


class TestCore(TestCase):
    """Test core functions."""

    def test_envcast_trues(self) -> None:
        """Test envcast function for trues."""
        self.assertEqual(envcast("1", int), 1)
        self.assertEqual(envcast("1.0", float), 1.0)
        self.assertEqual(envcast("True", bool), True)
        self.assertEqual(envcast("true", bool), True)
        self.assertEqual(envcast("t", bool), True)
        self.assertEqual(envcast("T", bool), True)

    def test_envcast_falses(self) -> None:
        """Test envcast function for falses."""
        self.assertEqual(envcast("0", "int"), 0)
        self.assertEqual(envcast("0.0", "float"), 0.0)
        self.assertEqual(envcast("False", "bool"), False)
        self.assertEqual(envcast("false", "bool"), False)
        self.assertEqual(envcast("f", bool), False)
        self.assertEqual(envcast("F", bool), False)

    def test_envcast_errors(self) -> None:
        """Test envcast function for errors."""
        with self.assertRaises(ValueError):
            envcast("None", list, need=True)
        with self.assertRaises(ValueError):
            envcast("none", list, need=True)
        with self.assertRaises(ValueError):
            envcast("", list, need=True)

    def test_envcast_list(self) -> None:
        """Test envcast function for lists."""
        self.assertEqual(envcast("[]", list), [])
        self.assertEqual(envcast("[1,2,3]", list), [1, 2, 3])
        self.assertListEqual(envcast("['a','b','c']", list), ["a", "b", "c"])

    def test_envcast_dict(self) -> None:
        """Test envcast function for dictionaries."""
        self.assertDictEqual(envcast('{"a":1,"b":2}', dict), {"a": 1, "b": 2})
        self.assertDictEqual(
            envcast('{"a":1,"b":2,"c":3}', dict), {"a": 1, "b": 2, "c": 3}
        )
        self.assertDictEqual(
            envcast('{"a":1,"b":2,"c":3,"d":4}', dict), {"a": 1, "b": 2, "c": 3, "d": 4}
        )


if __name__ == "__main__":
    main()

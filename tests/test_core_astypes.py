"""Test core functions."""
from unittest import main, TestCase

from alexlib.core import (
    asdict,
    aslist,
    concat_lists,
)


class TestCore(TestCase):
    """Test core functions."""

    def test_aslist(self) -> None:
        """Test aslist function."""
        lst = aslist("a,b,c")
        self.assertIsInstance(lst, list)
        self.assertIsInstance(aslist("a|b|c", sep="|"), list)
        self.assertEqual(lst, ["a", "b", "c"])

    def test_concat_lists(self):
        """Test with various lists of lists."""
        self.assertEqual(
            concat_lists([[1, 2], [3, 4]]),
            [1, 2, 3, 4],
            "Failed to correctly concatenate lists.",
        )

    def test_asdict(self) -> None:
        """Test asdict function."""

        class TestClass:
            """Test class."""

            def __init__(self):
                """Initialize the test class."""
                self.a = 1
                self.b = 2
                self._c = 3

        obj = TestClass()
        dct = asdict(obj)
        self.assertIsInstance(dct, dict)
        self.assertEqual(dct, {"a": 1, "b": 2})


if __name__ == "__main__":
    main()

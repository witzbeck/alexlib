"""Test core functions."""
from unittest import main, TestCase

from alexlib.core import (
    isdunder,
    ishidden,
    isnone,
    istrue,
)


class TestCore(TestCase):
    """Test core functions."""

    def test_istrue(self) -> None:
        """Test istrue function."""
        self.assertTrue(istrue(True))
        self.assertTrue(istrue("True"))
        self.assertTrue(istrue("true"))
        self.assertTrue(istrue("t"))
        self.assertTrue(istrue("T"))
        self.assertTrue(istrue("1"))
        self.assertFalse(istrue(False))
        self.assertFalse(istrue("False"))
        self.assertFalse(istrue("false"))
        self.assertFalse(istrue("f"))
        self.assertFalse(istrue("F"))
        self.assertFalse(istrue("0"))
        self.assertFalse(istrue(""))
        self.assertFalse(istrue(None))

    def test_isnone(self) -> None:
        """Test isnone function."""
        self.assertFalse(isnone(True))
        self.assertFalse(isnone("test"))
        self.assertFalse(isnone(1))
        self.assertFalse(isnone(0.0))
        self.assertTrue(isnone("None"))
        self.assertTrue(isnone("none"))
        self.assertTrue(isnone(""))
        self.assertTrue(isnone(None))
        self.assertFalse(isnone(False))
        self.assertFalse(isnone(0))

    def test_isdunder(self) -> None:
        """Test isdunder function."""
        self.assertTrue(isdunder("__dunder__"))
        self.assertFalse(isdunder("dunder__"))
        self.assertFalse(isdunder("__dunder"))
        self.assertFalse(isdunder("test"))

    def test_ishidden(self) -> None:
        """Test ishidden function."""
        self.assertTrue(ishidden("_hidden"))
        self.assertFalse(ishidden("hidden_"))
        self.assertFalse(ishidden("test"))
        self.assertTrue(ishidden("_hidden_"))


if __name__ == "__main__":
    main()

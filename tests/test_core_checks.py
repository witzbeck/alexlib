"""Test core functions."""
from os import environ
from pathlib import Path
from random import choice
from unittest import main, TestCase

from alexlib.core import (
    chkenv,
    chktext,
    chktype,
)


class TestCore(TestCase):
    """Test core functions."""

    @property
    def rand_env(self) -> str:
        """returns a random environment variable"""
        return choice(list(environ.keys()))

    def setUp(self) -> None:
        """Set up test environment."""
        self.env = self.rand_env
        environ["TEST_VAR"] = "123"
        environ["EMPTY_VAR"] = ""
        environ["TRUE_VAR"] = "True"
        environ["FALSE_VAR"] = "False"

    # Tests for chktext
    def test_chktext_prefix(self) -> None:
        """Test chktext function with prefix."""
        self.assertTrue(chktext("example text", prefix="Exa"))
        self.assertFalse(chktext("example text", prefix="test"))

    def test_chktext_value(self) -> None:
        """Test chktext function with value."""
        self.assertTrue(chktext("example text", value="ample"))
        self.assertFalse(chktext("example text", value="none"))

    def test_chktext_suffix(self) -> None:
        """Test chktext function with suffix."""
        self.assertTrue(chktext("example text", suffix="text"))
        self.assertFalse(chktext("example text", suffix="exam"))

    def test_chktext_no_input(self) -> None:
        """Test chktext function with no input."""
        with self.assertRaises(ValueError):
            chktext("example text")

    # Tests for chktype
    def test_chktype_correct(self) -> None:
        """Test chktype function with correct input."""
        self.assertEqual(chktype(123, int), 123)
        self.assertEqual(chktype("abc", str), "abc")

    def test_chktype_incorrect(self) -> None:
        """Test chktype function with incorrect input."""
        with self.assertRaises(TypeError):
            chktype(123, str)

    def test_chktype_path_exists(self) -> None:
        """Test chktype function with Path object."""
        test_path = Path("existing_file.txt")  # Assume this file exists
        self.assertEqual(chktype(test_path, Path, mustexist=False), test_path)

    def test_chktype_path_not_exist(self) -> None:
        """Test chktype function with Path object."""
        test_path = Path("non_existing_file.txt")  # Assume this file does not exist
        with self.assertRaises(FileExistsError):
            chktype(test_path, Path)

    def test_chktext(self) -> None:
        """Test with texts that meet and do not meet the prefix, value, and suffix conditions."""
        self.assertTrue(
            chktext("hello world", prefix="hello"),
            "Failed to recognize correct prefix.",
        )
        self.assertTrue(
            chktext("hello world", value="world"), "Failed to recognize correct value."
        )
        self.assertTrue(
            chktext("hello world", suffix="world"),
            "Failed to recognize correct suffix.",
        )
        self.assertFalse(
            chktext("hello world", prefix="world"),
            "Incorrectly identified incorrect prefix.",
        )
        self.assertFalse(
            chktext("hello world", suffix="hello"),
            "Incorrectly identified incorrect suffix.",
        )
        with self.assertRaises(ValueError):
            chktext("ab")
        self.assertTrue(chktext("abc", prefix="a"))
        self.assertTrue(chktext("abc", suffix="c"))
        self.assertTrue(chktext("abc", value="b"))
        self.assertTrue(chktext("abc", prefix="A"))
        self.assertTrue(chktext("abc", suffix="C"))
        self.assertTrue(chktext("abc", value="B"))
        self.assertFalse(chktext("abc", prefix="b"))
        self.assertFalse(chktext("abc", suffix="a"))
        self.assertFalse(chktext("abc", value="d"))

    def test_chktype(self) -> None:
        """Test with objects of correct and incorrect types. Also, test path existence if the object is a Path."""
        self.assertEqual(
            chktype("text", str), "text", "Failed to recognize correct type."
        )
        with self.assertRaises(TypeError):
            chktype(123, str)
        temp_file = Path("temp_file_for_testing.txt")
        temp_file.touch()  # Create the file for testing
        try:
            self.assertEqual(
                chktype(temp_file, Path, mustexist=True),
                temp_file,
                "Failed to recognize path existence.",
            )
        finally:
            temp_file.unlink()  # Clean up by removing the file
        with self.assertRaises(TypeError):
            chktype("a", int)
        with self.assertRaises(TypeError):
            chktype(1, str)
        self.assertEqual(chktype("a", str), "a")
        self.assertEqual(chktype(1, int), 1)
        self.assertEqual(chktype([], list), [])
        self.assertEqual(chktype({}, dict), {})

    def test_existing_variable(self) -> None:
        """Test chkenv function with existing variable."""
        self.assertEqual(chkenv("TEST_VAR"), "123")

    def test_non_existing_variable(self) -> None:
        """Test chkenv function with non existing variable."""
        with self.assertRaises(ValueError):
            chkenv("NON_EXISTING_VAR")

    def test_empty_variable(self) -> None:
        """Test chkenv function with empty variable."""
        with self.assertRaises(ValueError):
            chkenv("EMPTY_VAR")

    def test_default_for_non_existing_variable(self) -> None:
        """Test chkenv function with non existing variable."""
        self.assertIsNone(chkenv("NON_EXISTING_VAR", need=False))

    def test_default_for_empty_variable(self) -> None:
        """Test chkenv function with empty variable."""
        self.assertEqual(chkenv("EMPTY_VAR", need=False, ifnull="default"), "default")
        with self.assertRaises(ValueError):
            chkenv("EMPTY_VAR", need=True)

    def test_type_conversion(self) -> None:
        """Test chkenv function with type conversion."""
        self.assertEqual(chkenv("TEST_VAR", astype=int), 123)

    def test_boolean_true_value(self) -> None:
        """Test chkenv function with boolean true value."""
        self.assertTrue(chkenv("TRUE_VAR", astype=bool))

    def test_boolean_false_value(self) -> None:
        """Test chkenv function with boolean false value."""
        self.assertFalse(chkenv("FALSE_VAR", astype=bool))


if __name__ == "__main__":
    main()

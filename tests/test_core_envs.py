"""Test core functions."""
from os import environ
from pathlib import Path
from random import choice
from unittest import main
from unittest import TestCase

from alexlib.core import asdict
from alexlib.core import aslist
from alexlib.core import chkenv
from alexlib.core import chktext
from alexlib.core import chktype
from alexlib.core import envcast
from alexlib.core import isdunder
from alexlib.core import ishidden
from alexlib.core import isnone
from alexlib.core import istrue


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
        self.assertTrue(isnone("None"))
        self.assertTrue(isnone("none"))
        self.assertTrue(isnone(""))
        self.assertTrue(isnone(None))
        self.assertFalse(isnone(False))
        self.assertFalse(isnone(0))

    def test_aslist(self) -> None:
        """Test aslist function."""
        lst = aslist("a,b,c")
        self.assertIsInstance(lst, list)
        self.assertIsInstance(aslist("a|b|c", sep="|"), list)
        self.assertEqual(lst, ["a", "b", "c"])

    def test_chktext(self) -> None:
        """Test chktext function."""
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
        """Test chktype function."""
        with self.assertRaises(TypeError):
            chktype("a", int)
        with self.assertRaises(TypeError):
            chktype(1, str)
        self.assertEqual(chktype("a", str), "a")
        self.assertEqual(chktype(1, int), 1)
        self.assertEqual(chktype([], list), [])
        self.assertEqual(chktype({}, dict), {})

    def test_envcast(self) -> None:
        """Test envcast function."""
        self.assertEqual(envcast("1", int), 1)
        self.assertEqual(envcast("1.0", float), 1.0)
        self.assertEqual(envcast("True", bool), True)
        self.assertEqual(envcast("true", bool), True)
        self.assertEqual(envcast("t", bool), True)
        self.assertEqual(envcast("T", bool), True)
        self.assertEqual(envcast("0", "int"), 0)
        self.assertEqual(envcast("0.0", "float"), 0.0)
        self.assertEqual(envcast("False", "bool"), False)
        self.assertEqual(envcast("false", "bool"), False)
        self.assertEqual(envcast("f", bool), False)
        self.assertEqual(envcast("F", bool), False)
        with self.assertRaises(ValueError):
            envcast("None", list, need=True)
        with self.assertRaises(ValueError):
            envcast("none", list, need=True)
        with self.assertRaises(ValueError):
            envcast("", list, need=True)
        self.assertEqual(envcast("[]", list), [])
        self.assertEqual(envcast("[1,2,3]", list), [1, 2, 3])
        self.assertListEqual(envcast("['a','b','c']", list), ["a", "b", "c"])
        self.assertDictEqual(envcast('{"a":1,"b":2}', dict), {"a": 1, "b": 2})
        self.assertDictEqual(
            envcast('{"a":1,"b":2,"c":3}', dict), {"a": 1, "b": 2, "c": 3}
        )
        self.assertDictEqual(
            envcast('{"a":1,"b":2,"c":3,"d":4}', dict), {"a": 1, "b": 2, "c": 3, "d": 4}
        )

    def test_isdunder(self) -> None:
        """Test isdunder function."""
        self.assertTrue(isdunder("__dunder__"))
        self.assertFalse(isdunder("dunder__"))
        self.assertFalse(isdunder("__dunder"))

    def test_ishidden(self) -> None:
        """Test ishidden function."""
        self.assertTrue(ishidden("_hidden"))
        self.assertFalse(ishidden("hidden_"))
        self.assertTrue(ishidden("_hidden_"))

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

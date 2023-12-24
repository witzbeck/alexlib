from unittest import TestCase, main

from alexlib.core import istrue, isnone, aslist, chktext, chktype
from alexlib.core import envcast, chkenv, concat_lists, isdunder, ishidden
from alexlib.core import asdict, get_objects_by_attr, Object
from alexlib.core import mk_dictvals_distinct, invert_dict, sha256sum
from alexlib.core import get_last_tag, get_curent_version, Version, ping


class TestCore(TestCase):
    def test_istrue(self):
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

    def test_isnone(self):
        self.assertTrue(isnone("None"))
        self.assertTrue(isnone("none"))
        self.assertTrue(isnone(""))
        self.assertTrue(isnone(None))
        self.assertFalse(isnone(False))
        self.assertFalse(isnone(0))

    def test_aslist(self):
        lst = aslist("a,b,c")
        self.assertIsInstance(lst, list)
        self.assertIsInstance(aslist("a|b|c", sep="|"), list)
        self.assertEqual(lst, ["a", "b", "c"])

    def test_chktext(self):
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

    def test_chktype(self):
        with self.assertRaises(TypeError):
            chktype("a", int)
        with self.assertRaises(TypeError):
            chktype(1, str)
        self.assertEqual(chktype("a", str), "a")
        self.assertEqual(chktype(1, int), 1)
        self.assertEqual(chktype([], list), [])
        self.assertEqual(chktype({}, dict), {})

    def test_envcast(self):
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
        with self.assertRaises(TypeError):
            envcast("None", str)
        with self.assertRaises(TypeError):
            envcast("none", str)
        with self.assertRaises(TypeError):
            envcast("", str)
        self.assertEqual(envcast("[]", list), [])
        self.assertEqual(envcast("[1,2,3]", list), [1, 2, 3])
        self.assertListEqual(envcast("['a','b','c']", list), ["a", "b", "c"])
        self.assertDictEqual(envcast('{"a":1,"b":2}', dict), {"a": 1, "b": 2})
        self.assertDictEqual(envcast('{"a":1,"b":2,"c":3}', dict), {"a": 1, "b": 2, "c": 3})
        self.assertDictEqual(envcast('{"a":1,"b":2,"c":3,"d":4}', dict), {"a": 1, "b": 2, "c": 3, "d": 4})


if __name__ == "__main__":
    main()

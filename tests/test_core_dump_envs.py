from unittest import TestCase, main

from alexlib.core import is_json


class TestCoreDumpEnvs(TestCase):
    def test_is_json(self):
        self.assertTrue(is_json("test.json"))
        self.assertFalse(is_json("test.txt"))
        self.assertFalse(is_json("test"))


if __name__ == "__main__":
    main()

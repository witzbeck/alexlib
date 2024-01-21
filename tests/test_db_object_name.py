"""Test Name object"""
from unittest import TestCase, main

from alexlib.db.objects import Name


class TestName(TestCase):
    """Test Name object"""

    def test_name_validation(self) -> None:
        """Test to ensure that Name validates correctly"""
        self.assertTrue(Name("valid_name123"))
        with self.assertRaises(ValueError):
            Name("123invalid")

    def test_name_abrv(self) -> None:
        """Test abbreviation generation"""
        name = Name("test_table_name")
        self.assertEqual(name.abrv, "ttn")


if __name__ == "__main__":
    main()

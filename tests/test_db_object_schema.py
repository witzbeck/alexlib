"""Test schema object"""
from unittest import TestCase, main

from alexlib.db.objects import Schema


class TestSchema(TestCase):
    """Test schema object"""

    def setUp(self):
        """Assuming setup for a test database and schema"""
        self.test_schema = Schema("test_schema")

    def test_tables(self):
        """Test tables property"""
        self.assertIsInstance(self.test_schema.tables, list)
        self.assertIsInstance(self.test_schema, Schema)


if __name__ == "__main__":
    main()

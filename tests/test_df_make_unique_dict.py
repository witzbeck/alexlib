"""
This test module is designed to perform unit tests for the 'make_unique_dict' function
found in the 'alexlib.df' module. The tests ensure the correct creation of dictionaries
based on unique values from a DataFrame.
"""

# Imports
import unittest
from pandas import DataFrame
from alexlib.df import make_unique_dict


class TestMakeUniqueDict(unittest.TestCase):
    """
    Test suite for the 'make_unique_dict' function in the 'alexlib.df' module.
    """

    def setUp(self):
        """
        Set up data for testing.
        """
        self.data = DataFrame({"A": [1, 2, 2, 3], "B": [4, 5, 6, 7]})

    def test_dictionary_creation(self):
        """
        Test creating a dictionary based on unique values from a column.
        """
        result = make_unique_dict("A", self.data)
        expected = {
            1: self.data[self.data["A"] == 1],
            2: self.data[self.data["A"] == 2],
            3: self.data[self.data["A"] == 3],
        }
        self.assertEqual(result.keys(), expected.keys())
        for key in result:
            self.assertTrue(result[key].equals(expected[key]))

    # Additional tests can be added here as needed


if __name__ == "__main__":
    unittest.main()

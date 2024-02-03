"""Test cases for the SystemObject class."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from alexlib.files import SystemObject


class TestSystemObject(TestCase):
    """Test cases for the SystemObject class."""

    def test_instantiation(self):
        """Test instantiation with different names and paths."""
        with TemporaryDirectory() as td:
            path = Path(td) / "test_file.txt"
            self.system_object = SystemObject.from_path(path)
            self.assertEqual(self.system_object.name, "test_file.txt")
            self.assertEqual(self.system_object.path, Path(td) / "test_file.txt")

    def test_properties(self):
        """Test property methods like `isfile`, `isdir`, `haspath`, `user`, etc."""
        # Assuming the existence of a file at '/tmp/test_file.txt'
        with TemporaryDirectory() as td:
            path = Path(td) / "test_file.txt"
            self.system_object = SystemObject.from_path(path)
            path.touch()
            self.assertTrue(self.system_object.isfile)
            self.assertFalse(self.system_object.isdir)
            self.assertTrue(self.system_object.haspath)

    def test_path_manipulation(self):
        """Test path manipulation methods like `get_path`, `set_path`, `get_name`, `set_name`."""
        # Changing the path
        with TemporaryDirectory() as td:
            path = Path(td) / "test_file.txt"
            self.system_object = SystemObject.from_path(path)
            self.system_object.set_path()
            self.assertEqual(self.system_object.path, path)
            # Changing the name
            self.system_object.set_name("new_file.txt")
            self.assertEqual(self.system_object.name, "new_file.txt")

    def test_utility_methods(self):
        """Test other utility methods like `eval_method`, `from_path`, `from_name`."""
        # Testing from_path class method
        with TemporaryDirectory() as td:
            path = Path(td) / "test_file.txt"
            self.system_object = SystemObject.from_path(path)
            # self.assertEqual(self.system_object.name, "test_file.txt")
            # self.assertEqual(self.system_object.path, Path(td) / "test_file.txt")
            ## Testing from_name class method
            # self.system_object = SystemObject.from_name("test_file.txt")
            # self.assertEqual(self.system_object.name, "test_file.txt")
            # self.assertEqual(self.system_object.path, Path.cwd() / "test_file.txt")

    def tearDown(self):
        """Clean up any resources or temporary files created during testing."""
        super().tearDown()


if __name__ == "__main__":
    main()

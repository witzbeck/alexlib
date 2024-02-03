from os import unlink
from tempfile import NamedTemporaryFile, TemporaryDirectory
from unittest import TestCase, main
from pathlib import Path
from pandas import DataFrame

from alexlib.files import File, Directory


class TestFileOperations(TestCase):
    """
    Test suite for testing the File class in the alexlib.files module.
    This includes instantiation, file-specific property methods, file operations,
    file content manipulation methods, file data loading methods, and utility methods.
    """

    def setUp(self):
        """
        Setup method to create temporary files and directories before each test case.
        """
        # Setup a temporary directory
        self.temp_dir = TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        # Create a temporary file
        self.temp_file = NamedTemporaryFile(
            dir=self.temp_dir.name, delete=False, suffix=".txt"
        )
        self.addCleanup(unlink, self.temp_file.name)

        # Create a File object for testing
        self.file_obj = File.from_path(Path(self.temp_file.name))

    def test_instantiation(self):
        """
        Test instantiation of the File class and its properties.
        """
        self.assertEqual(self.file_obj.path, Path(self.temp_file.name))
        self.assertTrue(self.file_obj.exists)

    def test_is_type_methods(self):
        """
        Test the file-specific property methods (isxlsx, issql, iscsv, etc.).
        """
        # Assuming temp_file is a .txt file
        self.assertTrue(self.file_obj.istxt)
        self.assertFalse(self.file_obj.isxlsx)

    def test_content_manipulation_methods(self):
        """
        Test file content manipulation methods like write_lines, append_lines, replace_text.
        """
        # Write lines
        lines_to_write = ["Line 1", "Line 2"]
        self.file_obj.write_lines(lines_to_write)
        self.assertEqual(lines_to_write, self.file_obj.lines)

        # Append lines
        lines_to_append = ["Line 3"]
        self.file_obj.append_lines(lines_to_append)
        self.assertEqual(self.file_obj.lines, lines_to_write + lines_to_append)

        # Replace text
        self.file_obj.replace_text("Line 3", "Line 4")
        self.assertIn("Line 4", self.file_obj.lines)

    def test_utility_methods(self):
        """
        Test utility methods like copy_to, from_df.
        """
        # From df method - Creating a DataFrame and writing it to a file
        df = DataFrame.from_dict({"col1": [1, 2], "col2": [3, 4]})
        df_file_path = Path(self.temp_dir.name, "df_test_file.csv")
        File.from_df(df, df_file_path)
        self.assertTrue(df_file_path.exists())


class TestDirectoryOperations(TestCase):
    """
    Test suite for testing the Directory class in the alexlib.files module.
    This includes instantiation, directory-specific property methods, directory operations,
    directory content manipulation methods, and utility methods.
    """

    def setUp(self):
        """
        Setup method to create temporary files and directories before each test case.
        """
        # Setup a temporary directory
        self.temp_dir = TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        # Create a Directory object for testing
        self.dir_obj = Directory(path=Path(self.temp_dir.name))

    def test_instantiation(self):
        """
        Test instantiation of the Directory class and its properties.
        """
        self.assertEqual(self.dir_obj.path, Path(self.temp_dir.name))
        self.assertTrue(self.dir_obj.exists)

    def test_is_type_methods(self):
        """
        Test the directory-specific property methods (isdir, isempty, etc.).
        """
        # Assuming temp_dir is a directory
        self.assertTrue(self.dir_obj.path.is_dir())
        self.assertTrue(self.dir_obj.isempty)

    def test_utility_methods(self):
        """
        Test utility methods like get_type_filelist, tree, maxtreedepth.
        """
        # Tree structure representation and depth calculations
        tree = self.dir_obj.tree
        self.assertIsInstance(tree, dict)
        max_depth = self.dir_obj.maxtreedepth
        self.assertIsInstance(max_depth, int)

    def tearDown(self) -> None:
        """
        Clean up any resources or temporary files created during testing.
        """
        self.temp_dir.cleanup()
        return super().tearDown()


if __name__ == "__main__":
    main()

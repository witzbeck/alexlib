"""
This module contains unittests for testing the functionalities provided by the alexlib.files module,
including file and directory operations, manipulation, searching, and database interactions.
"""

from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
from unittest import TestCase, main

from alexlib.files.objects import Directory, File
from alexlib.files.utils import eval_parents


class TestAlexLibFiles(TestCase):
    """Test cases for the alexlib.files module, focusing on integration testing between Directory and File classes."""

    def setUp(self):
        """Set up a temporary directory and files for testing."""
        self.temp_dir = mkdtemp()
        self.temp_file_path = Path(self.temp_dir) / "test_file.txt"
        self.temp_file_path.write_text("This is a test file.")
        self.directory = Directory.from_path(Path(self.temp_dir))
        self.file = File.from_path(self.temp_file_path)

    def tearDown(self):
        """Clean up the temporary directory after tests."""
        rmtree(self.temp_dir)

    def test_directory_contains_file(self):
        """Test that the temporary directory contains the test file."""
        self.assertIn(
            self.temp_file_path.name, [f.name for f in self.directory.filelist]
        )

    def test_file_rename(self):
        """Test renaming a file within a directory."""
        new_name = "renamed_file.txt"
        self.file.rename(new_name)
        self.assertTrue((Path(self.temp_dir) / new_name).exists())

    def test_figsave(self):
        """Test saving a matplotlib figure to a specified directory."""
        # This test would require creating a simple matplotlib plot and saving it using figsave
        pass  # Implementation would go here, using a mock for matplotlib.pyplot.savefig if necessary

    def test_path_search(self):
        """Test searching for a file by pattern within a starting directory."""
        # This test would require setting up a specific file structure within the temporary directory
        pass  # Implementation would go here

    def test_eval_parents(self):
        """Test the evaluation of file paths based on inclusion and exclusion criteria."""
        self.assertTrue(
            eval_parents(
                Path(self.temp_file_path), include={"test_file.txt"}, exclude=set()
            )
        )

    def test_file_read(self):
        """Test reading the content of a file."""
        self.assertEqual(self.file.text, "This is a test file.")


if __name__ == "__main__":
    main()

import unittest
from unittest.mock import patch
from pathlib import Path
import tempfile
import shutil
from alexlib.files import File, update_file_version


class TestUpdateFileVersion(unittest.TestCase):
    """Test cases for the update_file_version function in the alexlib.files module."""

    def setUp(self):
        """Set up a temporary directory and files for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file_path = Path(self.temp_dir, "test_file.py")

    def tearDown(self):
        """Clean up the temporary directory after tests."""
        shutil.rmtree(self.temp_dir)

    def test_update_existing_version(self):
        """Test updating a file that already contains a version string."""
        # Setup: create a file with an existing version string
        with open(self.test_file_path, "w") as f:
            f.write("version = '1.0.0'\n")

        # Execute: update the version
        update_file_version("2.0.0", self.test_file_path)

        # Verify: the version string in the file is updated
        with open(self.test_file_path, "r") as f:
            content = f.read()
        self.assertIn("version = 2.0.0\n", content)

    def test_update_non_existing_version(self):
        """Test updating a file that does not contain a version string."""
        # Setup: create a file without a version string
        testfile = File.from_path(self.test_file_path)
        testfile.write_lines(["print('Hello, world!')"])

        # Execute: update the version
        update_file_version("1.0.1", self.test_file_path)

        # Verify: the file content remains unchanged
        self.assertNotIn("version = '1.0.1'", testfile.text)
        self.assertIn("print('Hello, world!')", testfile.text)

    def test_update_empty_file(self):
        """Test updating an empty file."""
        # Setup: create an empty file
        self.test_file_path.touch()

        # Execute: update the version
        update_file_version("1.0.2", self.test_file_path)

        # Verify: the file remains empty
        with open(self.test_file_path, "r") as f:
            content = f.read()
        self.assertEqual("", content)

    def test_update_file_with_multiple_lines(self):
        """Test updating a file with multiple lines of content."""
        # Setup: create a file with multiple lines and a version string
        testfile = File.from_path(self.test_file_path)
        testfile.write_lines(
            [
                "print('This is a test file')",
                "version = '0.9.0'",
                "print('End of file')",
            ]
        )
        # Execute: update the version
        update_file_version("'1.0.0'", self.test_file_path)

        # Verify: only the version line is updated
        self.assertIn("version = '1.0.0'\n", testfile.text)

    @patch("alexlib.files.File.from_path")
    def test_update_version_non_existent_file(self, mock_from_path):
        """Test gracefully handling the update of a non-existent file."""
        # Setup: configure the mock to simulate a FileNotFoundError
        mock_from_path.side_effect = FileNotFoundError

        # Execute & Verify: no exception is raised
        with self.assertRaises(FileNotFoundError):
            update_file_version("1.1.0", Path(self.temp_dir, "non_existent_file.py"))


if __name__ == "__main__":
    unittest.main()

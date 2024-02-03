from tempfile import TemporaryDirectory
from pathlib import Path
from unittest import TestCase, main
from unittest.mock import patch, MagicMock
from alexlib.files import (
    figsave,
    eval_parents,
    path_search,
    SystemObject,
    File,
    Directory,
)


class TestFigSave(TestCase):
    """Tests for the figsave function."""

    def test_figsave_success(self):
        """Test figsave successfully saves a figure to the specified directory."""
        # Setup
        name = "test_figure"
        dirpath = Path("./test_dir")
        fmt = "png"
        dirpath.mkdir(parents=True, exist_ok=True)

        # Execute
        result = figsave(name, dirpath, fmt)

        # Verify
        self.assertTrue(result)
        self.assertTrue((dirpath / f"{name}.{fmt}").exists())

        # Cleanup
        (dirpath / f"{name}.{fmt}").unlink()
        dirpath.rmdir()


class TestEvalParents(TestCase):
    """Tests for the eval_parents function."""

    def test_eval_parents_inclusion_exclusion(self):
        """Test eval_parents with specific include and exclude criteria."""
        path = Path("/user/test/include/exclude")
        include = {"include"}
        exclude = {"exclude"}

        result = eval_parents(path, include, exclude)
        self.assertFalse(result)

        result = eval_parents(path, include, set())
        self.assertTrue(result)


class TestPathSearch(TestCase):
    """Tests for the path_search function."""

    @patch("alexlib.files.Path.rglob")
    def test_path_search_found(self, mock_rglob):
        """Test path_search successfully finds the specified pattern."""
        pattern = "test_file.txt"
        start_path = Path(".")
        mock_path = MagicMock()
        mock_path.name = pattern
        mock_rglob.return_value = [mock_path]

        result = path_search(pattern, start_path)

        self.assertEqual(result, mock_path)


class TestSystemObject(TestCase):
    """Tests for the SystemObject class and its methods."""

    def test_system_object_initialization(self):
        """Test initialization of SystemObject with a path."""
        so = SystemObject(name="test", path=Path("."))

        self.assertIsNotNone(so)
        self.assertTrue(so.haspath)
        self.assertTrue(so.hasname)


class TestFile(TestCase):
    """Tests for the File class and its methods."""

    def test_file_read_write(self):
        """Test reading from and writing to a file."""
        file_path = Path("./test_file.txt")
        content = "Hello, world!"
        file = File.from_path(file_path)

        file.write_lines([content])
        read_content = file.text

        self.assertEqual(read_content, content)

        file.rm()


class TestDirectory(TestCase):
    """Tests for the Directory class and its methods."""

    def test_directory_operations(self):
        """Test directory creation, listing, and teardown."""
        with TemporaryDirectory() as temp_dir:
            dir = Directory.from_path(Path(temp_dir))
            file_path = dir.path / "test_file.txt"
            file_path.touch()

            self.assertTrue(dir.isdir)
            self.assertFalse(dir.isempty)

            dir.teardown(warn=False)
            self.assertFalse(dir.path.exists())


if __name__ == "__main__":
    main()

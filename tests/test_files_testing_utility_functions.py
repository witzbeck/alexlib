"""
Test Module: alexlib.files

This module contains unittests for testing the functionalities provided by the alexlib.files module,
including file and directory operations, manipulation, searching, and database interactions.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from alexlib.files import figsave, eval_parents, path_search
from matplotlib.figure import Figure


class TestFigsSave(TestCase):
    """
    Test the figsave function for saving matplotlib figures with various formats and parameters.
    """

    def test_save_png_format(self):
        """Test saving a figure in PNG format."""
        fig = Figure()
        ax = fig.subplots()
        ax.plot([1, 2, 3], [1, 2, 3])
        self.assertTrue(figsave("testfig", Path("./"), "png"))
        path = Path("./testfig.png")
        self.assertTrue(path.exists())
        path.unlink()

    def test_save_with_bbox_inches(self):
        """Test saving a figure with the bbox_inches parameter."""
        fig = Figure()
        ax = fig.subplots()
        ax.plot([1, 2, 3], [1, 2, 3])
        with TemporaryDirectory() as temp_dir:
            self.assertTrue(
                figsave("testfig", Path(temp_dir), "png", bbox_inches="tight")
            )
            path = Path(temp_dir) / "testfig.png"
            self.assertTrue(path.exists())
            path.unlink()


class TestEvalParents(TestCase):
    """
    Test the eval_parents function for evaluating file paths with different include and exclude criteria.
    """

    def test_include_criteria(self):
        """Test evaluation with include criteria."""
        path = Path("/test/dir/subdir/file.txt")
        self.assertTrue(eval_parents(path, include={"subdir"}, exclude=set()))

    def test_exclude_criteria(self):
        """Test evaluation with exclude criteria."""
        path = Path("/test/dir/exclude/file.txt")
        self.assertFalse(eval_parents(path, include=set(), exclude={"exclude"}))


class TestPathSearch(TestCase):
    """
    Test the path_search function for searching paths with various patterns and directory depths.
    """

    def test_search_with_pattern(self):
        """Test searching with a specific pattern."""
        # Setup - ensure the test directory and file exist
        testfile_name = "test_file.txt"
        with TemporaryDirectory() as temp_dir:
            (Path(temp_dir) / testfile_name).touch()
            found_path = path_search(testfile_name, start_path=Path(temp_dir))
            self.assertEqual(found_path.name, testfile_name)

    def test_search_nonexistent_file(self):
        """Test searching for a non-existent file."""
        with self.assertRaises(FileNotFoundError):
            path_search("nonexistent.txt", start_path=Path("test_dir"))


if __name__ == "__main__":
    main()

"""
Test Module: alexlib.files

This module contains unittests for testing the functionalities provided by the alexlib.files module,
including file and directory operations, manipulation, searching, and database interactions.
"""

from pathlib import Path

from matplotlib.figure import Figure
from pytest import fixture, mark, raises

from alexlib.files.objects import path_search
from alexlib.files.utils import eval_parents, figsave


@fixture(scope="class")
def figure():
    fig = Figure()
    ax = fig.subplots()
    ax.plot([1, 2, 3], [1, 2, 3])
    return fig


@fixture(scope="class")
def figure_path(dir_path: Path):
    return dir_path / "testfig.png"


def test_save_png_format(figure: Figure, figure_path: Path):
    """Test saving a figure in PNG format."""
    _ = figure
    assert figsave(figure_path.stem, figure_path.parent, "png")
    assert figure_path.exists()


def test_save_with_bbox_inches(figure: Figure, figure_path: Path):
    """Test saving a figure with the bbox_inches parameter."""
    _ = figure
    assert figsave(figure_path.stem, figure_path.parent, "png", bbox_inches="tight")
    assert figure_path.exists()


@mark.parametrize(
    "path, include, exclude, expected",
    [
        (Path("/test/dir/subdir/file.txt"), {"subdir"}, set(), True),
        (Path("/test/dir/exclude/file.txt"), set(), {"exclude"}, False),
    ],
)
def test_eval_parents(path: Path, include: set, exclude: set, expected: bool):
    """Test the eval_parents function for evaluating file paths with different include and exclude criteria."""
    assert eval_parents(path, include, exclude) is expected


def test_search_with_pattern(dir_path: Path):
    """Test searching with a specific pattern."""
    testfile_name = "test_file.txt"
    (dir_path / testfile_name).touch()
    found_path = path_search(testfile_name, start_path=dir_path)
    assert found_path.name == testfile_name


def test_search_nonexistent_file(dir_path: Path):
    """Test searching for a non-existent file."""
    with raises(FileNotFoundError):
        path_search("nonexistent.txt", start_path=dir_path, max_ascends=0)

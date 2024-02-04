from unittest import TestCase, main
from unittest.mock import patch, mock_open
from pathlib import Path
import os
from alexlib.files.objects import (
    SystemObject,
)
from alexlib.files.utils import eval_parents


def mock_path_exists(return_value=True):
    return patch("pathlib.Path.exists", return_value=return_value)


def mock_path_is_file(return_value=True):
    return patch("pathlib.Path.is_file", return_value=return_value)


def mock_path_is_dir(return_value=True):
    return patch("pathlib.Path.is_dir", return_value=return_value)


def mock_file_read_text(content=""):
    return patch("pathlib.Path.read_text", return_value=content)


def mock_os_env_get(env_var, return_value):
    return patch.dict(os.environ, {env_var: return_value})


def create_mock_file(path, content=""):
    m = mock_open(read_data=content)
    with patch("builtins.open", m):
        with open(path, "w") as f:
            f.write(content)


class TestEvalParents(TestCase):
    """Test cases for the eval_parents function."""

    def test_eval_parents_inclusion_exclusion(self):
        # Test various combinations of include and exclude criteria
        path = Path("/path/to/file")
        self.assertTrue(eval_parents(path, include={"path"}, exclude={"exclude"}))
        self.assertFalse(eval_parents(path, include={"other"}, exclude={"file"}))


class TestSystemObject(TestCase):
    """Test cases for the SystemObject class."""

    def test_system_object_initialization(self):
        # Test initialization and attribute setting
        obj = SystemObject(name="test", path=Path("/test/path"))
        self.assertTrue(obj.haspath)
        self.assertTrue(obj.hasname)


if __name__ == "__main__":
    main()

from os import environ
from unittest import TestCase, main
from unittest.mock import patch, mock_open
from pathlib import Path
from sys import version_info

from alexlib.files.objects import SystemObject, JsonFile, TomlFile
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
    return patch.dict(environ, {env_var: return_value})


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


class TestJsonFileInit(TestCase):
    """Test cases for the JsonFile class initialization."""

    def test_json_file_init(self):
        # Test the initialization of the JsonFile class
        path = Path("/path/to/file.json")
        create_mock_file(path)
        obj = JsonFile.from_path(path)
        self.assertTrue(obj.haspath)
        self.assertTrue(obj.hasname)
        self.assertTrue(obj.isjson)
        self.assertFalse(obj.exists)


class TestTomlFileInit(TestCase):
    """Test cases for the TomlFile class initialization."""

    def test_toml_file_init(self):
        # Test the initialization of the TomlFile class
        try:
            path = Path("/path/to/file.toml")
            create_mock_file(path)
            obj = TomlFile.from_path(path)
            self.assertTrue(obj.haspath)
            self.assertTrue(obj.hasname)
            self.assertTrue(obj.istoml)
            self.assertFalse(obj.exists)
        except AttributeError:
            if version_info.major == 3 and version_info.minor < 11:
                self.assertIsNone(TomlFile)


if __name__ == "__main__":
    main()

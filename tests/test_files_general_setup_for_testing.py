from os import environ
from pathlib import Path
from unittest.mock import mock_open, patch

from pytest import fixture, mark

from alexlib.files import JsonFile, TomlFile
from alexlib.files.objects import SystemObject
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


@mark.parametrize(
    "path, include, exclude, expected",
    [
        ("/path/to/file", {"path"}, {"exclude"}, True),
        ("/path/to/file", {"other"}, {"file"}, False),
    ],
)
def test_eval_parents_inclusion_exclusion(path, include, exclude, expected):
    """Test various combinations of include and exclude criteria"""
    path = Path(path)
    assert eval_parents(path, include, exclude) is expected


def test_system_object_initialization():
    # Test initialization and attribute setting
    obj = SystemObject(name="test", path=Path("/test/path"))
    assert obj.haspath
    assert obj.hasname


@fixture(scope="class")
def json_file():
    path = Path("/path/to/file.json")
    create_mock_file(path)
    return JsonFile.from_path(path)


@fixture(scope="class")
def toml_file():
    path = Path("/path/to/file.toml")
    create_mock_file(path)
    return TomlFile.from_path(path)


def test_json_file_init(json_file):
    """Test the initialization of the JsonFile class"""
    assert json_file.haspath
    assert json_file.hasname
    assert json_file.isjson
    assert not json_file.exists


def test_toml_file_init(toml_file):
    """Test the initialization of the TomlFile class"""
    assert toml_file.haspath
    assert toml_file.hasname
    assert toml_file.istoml
    assert not toml_file.exists

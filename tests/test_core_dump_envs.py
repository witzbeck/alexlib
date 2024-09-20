from json import loads as json_loads
from pathlib import Path

from pytest import mark, raises

from alexlib.files.utils import dump_envs


@mark.slow
def test_dump_dotenv(dir_path: Path):
    """Test dumping to dotenv format"""
    test_path = dir_path / "output.env"
    pairs = {"KEY": "VALUE"}
    dump_envs(test_path, pairs)
    assert test_path.exists()
    assert test_path.read_text() == "KEY=VALUE"


@mark.slow
def test_dump_json(dir_path: Path):
    """Test dumping to JSON format"""
    test_path = dir_path / "output.json"
    pairs = {"KEY": "VALUE"}
    dump_envs(test_path, pairs)
    assert test_path.exists()
    assert json_loads(test_path.read_text()) == pairs


@mark.slow
def test_dump_envs_force(dir_path: Path):
    """Test force overwrite"""
    test_path = dir_path / "output.json"
    test_path.touch()
    pairs = {"KEY": "NEW_VALUE"}
    dump_envs(test_path, pairs, force=True)
    assert test_path.exists()
    assert json_loads(test_path.read_text()) == pairs


@mark.slow
def test_dump_envs_unsupported_type(dir_path: Path):
    """Test unsupported file types"""
    test_path = dir_path / "output.unsupported"
    pairs = {"KEY": "VALUE"}
    with raises(ValueError):
        dump_envs(test_path, pairs)

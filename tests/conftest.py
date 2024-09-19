from os import environ
from pathlib import Path
from random import choice
from tempfile import TemporaryDirectory
from pytest import fixture

from alexlib.auth import Auth
from alexlib.core import chkcmd, get_clipboard_cmd


@fixture(scope="session")
def environ_keys():
    return list(environ.keys())


@fixture(scope="class")
def rand_env(environ_keys: list[str]) -> str:
    return choice(environ_keys)


@fixture(scope="session")
def test_dir():
    with TemporaryDirectory() as test_dir:
        yield Path(test_dir)


@fixture(scope="class")
def test_file(test_dir: Path):
    test_file = test_dir / "test.txt"
    test_file.touch()
    yield test_file
    test_file.unlink()


@fixture(scope="class")
def copy_text():
    return "Text copied to clipboard successfully."


@fixture(scope="class")
def copy_path(test_file: Path, copy_text: str):
    test_file.write_text(copy_text)
    return test_file


@fixture(scope="session")
def auth():
    return Auth.from_dict(
        name="test_auth",
        dict_={
            "username": "test_user",
            "password": "test_pass",
            "key": "value",
            "host": "test_host",
            "port": "test_port",
            "database": "test_database",
        },
    )


@fixture(scope="class")
def cmd():
    try:
        get_clipboard_cmd()
    except OSError:
        return None


@fixture(scope="class")
def hascmd(cmd):
    return chkcmd(cmd[0]) if cmd is not None else False

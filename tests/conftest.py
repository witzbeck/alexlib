from os import environ
from pathlib import Path
from random import choice
from tempfile import NamedTemporaryFile, TemporaryDirectory

from faker import Faker
from pytest import FixtureRequest, fixture

from alexlib.auth import Auth, AuthPart, Login, Password, SecretStore, Server, Username
from alexlib.core import chkcmd, get_clipboard_cmd
from alexlib.crypto import Cryptographer
from alexlib.files.objects import Directory, File


@fixture(scope="class")
def cryptographer() -> Cryptographer:
    return Cryptographer.new()


@fixture(scope="session")
def faker():
    return Faker()


@fixture(scope="session")
def environ_keys():
    return list(environ.keys())


@fixture(scope="class")
def rand_env(environ_keys: list[str]) -> str:
    return choice(environ_keys)


@fixture(scope="session")
def dir_path():
    with TemporaryDirectory() as test_dir:
        yield Path(test_dir)


@fixture(scope="session")
def dir_obj(dir_path: Path):
    return Directory.from_path(dir_path)


@fixture(scope="class")
def file_path(dir_path: Path, faker: Faker):
    test_file = dir_path / NamedTemporaryFile("w", delete=False).name
    test_file.write_text(faker.text())
    yield test_file
    test_file.unlink()


@fixture(scope="class")
def file_obj(file_path: Path) -> File:
    return File.from_path(file_path)


@fixture(scope="class")
def copy_text():
    return "Text copied to clipboard successfully."


@fixture(scope="class")
def copy_path(file_path: Path, copy_text: str):
    file_path.write_text(copy_text)
    return file_path


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


@fixture(scope="session")
def auth_path(dir_path: Path):
    return dir_path / "auth_store.json"


@fixture(scope="function")
def username():
    return Username.rand()


@fixture(scope="function")
def password():
    return Password.rand()


@fixture(scope="function")
def login(username: Username, password: Password):
    return Login(user=username, pw=password)


@fixture(scope="module", params=(Username, AuthPart, Password))
def auth_part(request: FixtureRequest) -> AuthPart:
    return request.param.rand(letter=True)


@fixture(scope="module")
def server() -> Server:
    return Server.rand()


@fixture(scope="class")
def secret_store(auth_path: Path):
    return SecretStore.from_dict(
        {"username": "user", "password": "pass"}, path=auth_path
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

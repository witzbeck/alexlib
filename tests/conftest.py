from collections.abc import Generator
from datetime import datetime
from os import environ
from pathlib import Path
from random import choice
from tempfile import NamedTemporaryFile, TemporaryDirectory

from faker import Faker
from matplotlib.figure import Figure
from pandas import DataFrame
from pytest import FixtureRequest, fixture

from alexlib.auth import Auth, AuthPart, Login, Password, SecretStore, Server, Username
from alexlib.constants import (
    CLIPBOARD_COMMANDS_PATH,
    COLUMN_SUB_PATH,
    CREDS,
    DATA_PATH,
    DATE_FORMAT,
    DATETIME_FORMAT,
    HOME,
    MODULE_PATH,
    PROJECT_PATH,
    PYPROJECT_PATH,
    RESOURCES_PATH,
    SA_DIALECT_MAP_PATH,
    SOURCE_PATH,
    SQL_CHARS,
    TIME_FORMAT,
    VENVS,
)
from alexlib.core import chkcmd, get_clipboard_cmd
from alexlib.crypto import Cryptographer
from alexlib.files import DotenvFile, JsonFile, SettingsFile, TomlFile
from alexlib.files.objects import Directory, File, SystemObject
from alexlib.files.utils import write_json
from alexlib.times import ONEDAY, CustomDatetime

CORE_PATHS = (
    MODULE_PATH,
    SOURCE_PATH,
    PROJECT_PATH,
    RESOURCES_PATH,
    DATA_PATH,
    PYPROJECT_PATH,
    HOME,
    CREDS,
    VENVS,
    CLIPBOARD_COMMANDS_PATH,
    COLUMN_SUB_PATH,
    SA_DIALECT_MAP_PATH,
)
CORE_STRINGS = (
    DATE_FORMAT,
    TIME_FORMAT,
    DATETIME_FORMAT,
    SQL_CHARS,
)


@fixture(scope="session", params=CORE_PATHS)
def core_path(request: FixtureRequest) -> Path:
    return request.param


@fixture(scope="session", params=CORE_STRINGS)
def core_string(request: FixtureRequest) -> str:
    return request.param


@fixture(scope="session")
def now():
    return datetime.now()


@fixture(scope="session")
def thisyear(now: datetime):
    return now.year


@fixture(scope="session")
def this_xmas(thisyear: int):
    return CustomDatetime(datetime(thisyear, 12, 25))


@fixture(scope="session")
def day_after_xmas(this_xmas: CustomDatetime):
    return this_xmas + ONEDAY


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


@fixture(scope="module")
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory and return its path."""
    with TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@fixture(scope="module", params=(f"test_dir{i}" for i in range(2)))
def subdir_with_files(faker: Faker, temp_dir: Path, request: FixtureRequest):
    subdir = temp_dir / request.param
    subdir.resolve()
    (subdir / faker.word()).mkdir(exist_ok=True, parents=True)
    for i in range(3):
        file = subdir / f"test_file{i}.txt"
        file.write_text(faker.text())
    return Directory.from_path(subdir)


@fixture(scope="module")
def dir_path(faker: Faker, temp_dir: Path):
    (path := temp_dir / faker.word()).mkdir(exist_ok=True, parents=True)
    return path


@fixture(scope="module")
def dir_obj(dir_path: Path):
    return Directory.from_path(dir_path)


@fixture(scope="class")
def sysobj(file_path: Path):
    return SystemObject.from_path(file_path)


@fixture(scope="class")
def text_file_path(dir_path: Path) -> Path:
    """Create a text file and return its path."""
    text_file = dir_path / "test.txt"
    text_file.resolve()
    text_file.write_text("Line 1\nLine 2")
    return text_file


@fixture(scope="class")
def text_file_obj(text_file_path: Path) -> File:
    """Create a File object and return it."""
    return File.from_path(text_file_path)


@fixture(scope="module")
def json_path(temp_dir: Path):
    return temp_dir / "test.json"


@fixture(scope="module")
def json_file(json_path: Path):
    write_json({"key": "value"}, json_path)
    return JsonFile.from_path(json_path)


@fixture(scope="module")
def toml_path(temp_dir: Path):
    return temp_dir / "test.toml"


@fixture(scope="module")
def toml_file(toml_path: Path):
    toml_path.write_text('key = "value"')
    return TomlFile.from_path(toml_path)


@fixture(scope="module")
def dotenv_path(dir_path: Path):
    path = dir_path / ".env"
    path.touch()
    path.write_text(
        """
        EXAMPLE_VAR=some_value
        ANOTHER_VAR=another_value
        """
    )
    return path


@fixture(scope="module")
def dotenv_file(dotenv_path: Path):
    return DotenvFile.from_path(dotenv_path)


@fixture(scope="module")
def settings_path(temp_dir: Path):
    return temp_dir / "settings.json"


@fixture(scope="module")
def settings_file(settings_path: Path):
    write_json(
        {
            "key": "value",
            "nested": {"key": "value"},
            "list": ["item1", "item2"],
            "bool": True,
            "int": 1,
            "float": 1.0,
            "none": None,
        },
        settings_path,
    )
    return SettingsFile.from_path(settings_path)


@fixture(scope="class")
def rand_key(settings_file: SettingsFile):
    return choice(list(settings_file.envdict.keys()))


@fixture(scope="class")
def rand_val(settings_file: SettingsFile, rand_key: str):
    return settings_file.envdict[rand_key]


@fixture(scope="class")
def file_path(temp_dir: Path, faker: Faker):
    test_file = temp_dir / NamedTemporaryFile("w", delete=False).name
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


@fixture(scope="module")
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


@fixture(scope="module")
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


@fixture(scope="class")
def csv_path(dir_path: Path):
    return dir_path / "test_df.csv"


@fixture(scope="class")
def df():
    return DataFrame.from_dict({"col1": [1, 2], "col2": [3, 4]})


@fixture(scope="class")
def figure():
    fig = Figure()
    ax = fig.subplots()
    ax.plot([1, 2, 3], [1, 2, 3])
    return fig


@fixture(scope="class")
def figure_path(dir_path: Path):
    return dir_path / "testfig.png"

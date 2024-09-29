from collections.abc import Generator
from datetime import datetime
from os import environ
from pathlib import Path
from random import choice
from tempfile import NamedTemporaryFile, TemporaryDirectory

from faker import Faker
from pandas import DataFrame
from pytest import FixtureRequest, fixture

from alexlib.constants import (
    CLIPBOARD_COMMANDS_MAP,
    COLUMN_SUB_MAP,
    CREDS,
    DATA_PATH,
    DATE_FORMAT,
    DATETIME_FORMAT,
    ENVIRONMENTS,
    EPOCH,
    HOME,
    LOG_FORMAT,
    LOG_PATH,
    MODULE_PATH,
    PROJECT_PATH,
    PYPROJECT_PATH,
    SA_DIALECT_MAP,
    SOURCE_PATH,
    SQL_CHARS,
    TIME_FORMAT,
    VENVS,
)
from alexlib.core import chkcmd, get_clipboard_cmd
from alexlib.files import (
    CreatedTimestamp,
    Directory,
    DotenvFile,
    File,
    JsonFile,
    ModifiedTimestamp,
    SettingsFile,
    SystemObject,
    TomlFile,
)
from alexlib.files.utils import write_json
from alexlib.times import ONEDAY, CustomDatetime

CORE_DATETIMES = (EPOCH,)
CORE_MAPS = (
    CLIPBOARD_COMMANDS_MAP,
    COLUMN_SUB_MAP,
    SA_DIALECT_MAP,
)
CORE_PATHS = (
    MODULE_PATH,
    SOURCE_PATH,
    PROJECT_PATH,
    DATA_PATH,
    LOG_PATH,
    PYPROJECT_PATH,
    HOME,
    CREDS,
    VENVS,
)
CORE_STRINGS = (
    LOG_FORMAT,
    DATE_FORMAT,
    TIME_FORMAT,
    DATETIME_FORMAT,
    SQL_CHARS,
) + ENVIRONMENTS


@fixture(scope="session", params=ENVIRONMENTS)
def environment(request: FixtureRequest) -> str:
    return request.param


@fixture(scope="session", params=CORE_MAPS)
def core_map(request: FixtureRequest) -> dict[str, str]:
    return request.param


@fixture(scope="session", params=CORE_DATETIMES)
def core_datetime(request: FixtureRequest) -> datetime:
    return request.param


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


@fixture(scope="session")
def faker():
    return Faker()


@fixture(scope="session")
def environ_keys():
    return list(environ.keys())


@fixture(scope="function")
def rand_env(environ_keys: list[str]) -> str:
    return choice(environ_keys)


@fixture(scope="session")
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory and return its path."""
    with TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@fixture(scope="session", params=(f"test_dir{i}" for i in range(2)))
def subdir_with_files(faker: Faker, temp_dir: Path, request: FixtureRequest):
    subdir = temp_dir / request.param
    subdir.resolve()
    (subdir / faker.word()).mkdir(exist_ok=True, parents=True)
    for i in range(3):
        file = subdir / f"test_file{i}.txt"
        file.write_text(faker.text())
    return Directory.from_path(subdir)


@fixture(scope="session")
def subdir_latest_file(subdir_with_files: Directory):
    return subdir_with_files.get_latest_file()


@fixture(scope="session")
def dir_path(faker: Faker, temp_dir: Path):
    (path := temp_dir / faker.word()).mkdir(exist_ok=True, parents=True)
    return path


@fixture(scope="module")
def dir_obj(dir_path: Path):
    return Directory.from_path(dir_path)


@fixture(scope="module")
def dir_obj_created_ts(dir_obj: Directory) -> CreatedTimestamp:
    return dir_obj.created_timestamp


@fixture(scope="module")
def dir_obj_modified_ts(dir_obj: Directory) -> ModifiedTimestamp:
    return dir_obj.modified_timestamp


@fixture(scope="function")
def sysobj(file_path: Path):
    return SystemObject.from_path(file_path)


@fixture(scope="function")
def text_file_path(dir_path: Path) -> Path:
    """Create a text file and return its path."""
    text_file = dir_path / "test.txt"
    text_file.resolve()
    text_file.write_text("Line 1\nLine 2")
    return text_file


@fixture(scope="function")
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


@fixture(scope="function")
def rand_key(settings_file: SettingsFile):
    return choice(list(settings_file.envdict.keys()))


@fixture(scope="function")
def rand_val(settings_file: SettingsFile, rand_key: str):
    return settings_file.envdict[rand_key]


@fixture(scope="function")
def file_path(temp_dir: Path, faker: Faker):
    test_file = temp_dir / NamedTemporaryFile("w", delete=False).name
    test_file.write_text(faker.text())
    yield test_file
    test_file.unlink()


@fixture(scope="function")
def file_obj(file_path: Path) -> File:
    return File.from_path(file_path)


@fixture(scope="function")
def copy_text():
    return "Text copied to clipboard successfully."


@fixture(scope="function")
def copy_path(file_path: Path, copy_text: str):
    file_path.write_text(copy_text)
    return file_path


@fixture(scope="function")
def cmd():
    try:
        get_clipboard_cmd()
    except OSError:
        return None


@fixture(scope="function")
def hascmd(cmd):
    return chkcmd(cmd[0]) if cmd is not None else False


@fixture(scope="function")
def csv_path(dir_path: Path):
    return dir_path / "test_df.csv"


@fixture(scope="session")
def empty_df():
    return DataFrame()


@fixture(scope="function")
def df():
    return DataFrame.from_dict({"col1": [1, 2], "col2": [3, 4]})


@fixture(scope="function")
def df_with_duplicate_values():
    return DataFrame.from_dict({"col1": [1, 2, 2, 3], "col2": ["a", "b", "b", "c"]})


@fixture(scope="function")
def df_to_filter():
    return DataFrame.from_dict(
        {
            "name": ["Alice", "Bob", "Charlie", "David"],
            "age": [25, 30, 35, 40],
            "city": ["New York", "Los Angeles", "Chicago", "Houston"],
        }
    )


@fixture(scope="function")
def df_copy(df):
    """Return a copy of the DataFrame."""
    return df.copy()

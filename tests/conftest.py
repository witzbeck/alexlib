from pathlib import Path
from tempfile import TemporaryDirectory
from pytest import FixtureRequest, fixture

ISJSON_TRUE_STRINGS = (
    "test.json",
    "settings.json",
    "config.json",
    "package.json",
)
ISJSON_TRUE_PATHS = (
    Path("test.json"),
    Path("settings.json"),
    Path("config.json"),
    Path("package.json"),
)
ISJSON_FALSE_STRINGS = (
    "test.txt",
    "test",
)
ISJSON_FALSE_PATHS = (
    Path("test.txt"),
    Path("test"),
)
ISDOTENV_TRUE_STRINGS = (
    ".env",
    ".env.example",
    ".env.local",
    ".env.test",
)
ISDOTENV_TRUE_PATHS = (
    Path(".env"),
    Path(".env.example"),
    Path(".env.local"),
    Path(".env.test"),
)
ISDOTENV_FALSE_STRINGS = (
    "env.development",
    "settings.json",
    "config.json",
    "package.json",
    "test.json",
    "test.txt",
)
ISDOTENV_FALSE_PATHS = (
    Path("env.development"),
    Path("settings.json"),
    Path("config.json"),
    Path("package.json"),
    Path("test.json"),
    Path("test.txt"),
)
ISJSON_TRUE = ISJSON_TRUE_STRINGS + ISJSON_TRUE_PATHS
ISJSON_FALSE = ISJSON_FALSE_STRINGS + ISJSON_FALSE_PATHS
ISDOTENV_TRUE = ISDOTENV_TRUE_STRINGS + ISDOTENV_TRUE_PATHS
ISDOTENV_FALSE = ISDOTENV_FALSE_STRINGS + ISDOTENV_FALSE_PATHS
ALL_STRINGS = (
    ISJSON_TRUE_STRINGS
    + ISJSON_FALSE_STRINGS
    + ISDOTENV_TRUE_STRINGS
    + ISDOTENV_FALSE_STRINGS
)
ALL_PATHS = (
    ISJSON_TRUE_PATHS + ISJSON_FALSE_PATHS + ISDOTENV_TRUE_PATHS + ISDOTENV_FALSE_PATHS
)


@fixture(params=ALL_STRINGS)
def a_string(request: FixtureRequest) -> str:
    return request.param


@fixture(params=ALL_PATHS)
def a_path(request: FixtureRequest) -> Path:
    return request.param


@fixture(params=ISJSON_TRUE)
def is_json_true(request: FixtureRequest) -> bool:
    return request.param


@fixture(params=ISJSON_FALSE)
def is_json_false(request: FixtureRequest) -> bool:
    return request.param


@fixture(params=ISDOTENV_TRUE)
def is_dotenv_true(request: FixtureRequest) -> bool:
    return request.param


@fixture(params=ISDOTENV_FALSE)
def is_dotenv_false(request: FixtureRequest) -> bool:
    return request.param


@fixture(scope="class")
def test_dir():
    with TemporaryDirectory() as test_dir:
        yield Path(test_dir)

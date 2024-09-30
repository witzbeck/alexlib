"""Test core functions."""

from datetime import datetime
from os import environ
from pathlib import Path
from socket import socket
from subprocess import Popen
from typing import Any

from pytest import FixtureRequest, fixture, mark, raises

from alexlib.core import (
    asdict,
    aslist,
    chkcmd,
    chkenv,
    chktext,
    chktype,
    copy_file_to_clipboard,
    envcast,
    get_attrs,
    get_objects_by_attr,
    invert_dict,
    isdunder,
    ishidden,
    islinux,
    ismacos,
    isnone,
    istrue,
    iswindows,
    mk_dictvals_distinct,
    ping,
    to_clipboard,
)
from alexlib.files.utils import dump_envs, is_dotenv, is_json, sha256sum


def test_core_path(core_path: Path):
    assert isinstance(core_path, Path)
    assert core_path.exists()


def test_core_string(core_string: str):
    assert isinstance(core_string, str)
    assert bool(core_string)


def test_environment(environment: str):
    assert isinstance(environment, str)
    assert bool(environment)


def test_core_map(core_map: dict[str, str]):
    assert isinstance(core_map, dict)
    assert all(
        isinstance(key, str) and isinstance(value, (str, list))
        for key, value in core_map.items()
    )


def test_core_datetime(core_datetime: datetime):
    assert isinstance(core_datetime, datetime)


@mark.parametrize(
    "string, sep, expected",
    [
        ("a,b,c", ",", ["a", "b", "c"]),
        ("a|b|c", "|", ["a", "b", "c"]),
        ("a b c", " ", ["a", "b", "c"]),
        ("", ",", []),
    ],
)
def test_aslist(string: str, sep: str, expected: list[str]) -> None:
    lst = aslist(string, sep=sep)
    assert isinstance(lst, list)
    assert lst == expected


@fixture(scope="module")
def _testclass():
    class TestClass:
        def __init__(self):
            self.a = 1
            self.b = 2
            self._c = 3
            self.__d__ = 4

    return TestClass()


@mark.parametrize(
    "key, value, include_hidden, include_dunder, isin",
    (
        (
            "a",
            1,
            False,
            False,
            True,
        ),
        (
            "b",
            2,
            False,
            False,
            True,
        ),
        (
            "_c",
            3,
            False,
            False,
            False,
        ),
        (
            "__d__",
            4,
            False,
            False,
            False,
        ),
        (
            "a",
            1,
            True,
            False,
            True,
        ),
        (
            "b",
            2,
            True,
            False,
            True,
        ),
        (
            "_c",
            3,
            True,
            False,
            True,
        ),
        (
            "__d__",
            4,
            True,
            False,
            False,
        ),
        (
            "a",
            1,
            False,
            True,
            True,
        ),
        (
            "b",
            2,
            False,
            True,
            True,
        ),
        (
            "_c",
            3,
            False,
            True,
            False,
        ),
        (
            "__d__",
            4,
            False,
            True,
            True,
        ),
        (
            "a",
            1,
            True,
            True,
            True,
        ),
        (
            "b",
            2,
            True,
            True,
            True,
        ),
        (
            "_c",
            3,
            True,
            True,
            True,
        ),
        (
            "__d__",
            4,
            True,
            True,
            True,
        ),
    ),
)
def test_asdict(_testclass, key, value, include_hidden, include_dunder, isin):
    dct = asdict(
        _testclass, include_hidden=include_hidden, include_dunder=include_dunder
    )
    assert isinstance(dct, dict)
    assert (key in dct) == isin
    if isin:
        assert dct[key] == value


def test_sha256sum_on_path(file_path: Path):
    """Test the `sha256sum` function on a path."""
    assert isinstance(sha256sum(file_path), str)


@mark.slow
def test_dump_envs_unsupported_type(dir_path: Path):
    """Test unsupported file types"""
    test_path = dir_path / "output.unsupported"
    pairs = {"KEY": "VALUE"}
    with raises(ValueError):
        dump_envs(test_path, pairs)


def test_with_list_values_including_duplicates() -> None:
    """Test with list values including duplicates."""
    test_dict = {"a": [1, 2, 2, 3], "b": ["x", "y", "y"]}
    expected = {"a": [1, 2, 3], "b": ["x", "y"]}
    result = mk_dictvals_distinct(test_dict)
    assert all(
        (sorted(result[key]) == sorted(expected[key]) for key in test_dict.keys())
    )


def test_with_dict() -> None:
    """Test with a dictionary."""
    test_dict = {"a": 1, "b": 2}
    expected = {1: "a", 2: "b"}
    result = invert_dict(test_dict)
    assert sorted(result.keys()) == sorted(expected.keys())
    assert sorted(result.values()) == sorted(expected.values())


@mark.parametrize(
    "value",
    (1, 0.0, None, False),
)
def test_to_clipboard_typeerror(value):
    with raises(TypeError):
        to_clipboard(value)


def test_copy_non_existing_file():
    with raises(FileNotFoundError):
        copy_file_to_clipboard(Path("/fake/path"))


def test_copy_existing_file(copy_path, copy_text):
    if iswindows() or ismacos():
        assert copy_file_to_clipboard(copy_path)
    else:
        assert islinux()
        has = chkcmd("xclip") or chkcmd("xsel")
        if has:
            assert copy_file_to_clipboard(copy_path)
        else:
            with raises(OSError):
                copy_file_to_clipboard(copy_path)


def test_to_clipboard_success(copy_text):
    if not islinux():
        assert (
            to_clipboard(copy_text)
            == Popen(["pbpaste"], stdout=-1).communicate()[0].decode()
        )
    else:
        has = chkcmd("xclip") or chkcmd("xsel")
        if has:
            assert (
                to_clipboard(copy_text)
                == Popen(["xclip", "-selection", "clipboard", "-o"], stdout=-1)
                .communicate()[0]
                .decode()
            )
        else:
            with raises(OSError):
                to_clipboard(copy_text)


def test_copy_path_not_a_file():
    try:
        with raises(FileNotFoundError):
            copy_file_to_clipboard(Path("/fake/path"))
    except OSError as e:
        with raises(OSError):
            assert copy_file_to_clipboard(Path("/fake/path")), e


ATTRS = (
    "public_attr",
    "_hidden_attr",
    "__dunder_attr__",
)
METHODS = (
    "public_method",
    "_hidden_method",
    "__dunder_method__",
)


@fixture(scope="module", params=ATTRS)
def attr(request: FixtureRequest) -> str:
    return request.param


@fixture(scope="module", params=METHODS)
def method(request: FixtureRequest) -> str:
    return request.param


@fixture(scope="module", params=ATTRS + METHODS)
def attr_or_method(request: FixtureRequest) -> str:
    return request.param


class _TestClass:
    """Test class for `get_attrs` function."""

    def __init__(
        self,
        public_attr: str = "public",
        hidden_attr: str = "hidden",
        dunder_attr: str = "dunder",
    ) -> None:
        self.public_attr = public_attr
        self._hidden_attr = hidden_attr
        self.__dunder_attr__ = dunder_attr

    def public_method(self):
        return self.public_attr

    def _hidden_method(self):
        return self._hidden_attr

    def __dunder_method__(self):
        return self.__dunder_attr__


@fixture(scope="module")
def test_obj():
    return _TestClass()


@fixture(scope="module")
def all_attrs(test_obj):
    return get_attrs(
        test_obj,
        hidden=True,
        dunder=True,
        methods=True,
    )


@fixture(scope="module")
def public_attrs(test_obj):
    return get_attrs(test_obj)


@fixture(scope="module")
def public_methods(test_obj):
    return get_attrs(test_obj, methods=True)


@fixture(scope="module")
def hidden_attrs(test_obj):
    return get_attrs(test_obj, hidden=True)


@fixture(scope="module")
def hidden_methods(test_obj):
    return get_attrs(test_obj, methods=True, hidden=True)


@fixture(scope="module")
def dunder_attrs(test_obj):
    return get_attrs(test_obj, dunder=True)


@fixture(scope="module")
def dunder_methods(test_obj):
    return get_attrs(test_obj, methods=True, dunder=True)


def test_get_all_attrs(all_attrs, attr_or_method):
    assert attr_or_method in all_attrs


def test_get_public_attrs(public_attrs):
    assert public_attrs == {"public_attr": "public"}


def test_get_public_methods(public_methods):
    assert "public_method" in public_methods
    assert "_hidden_method" not in public_methods


def test_get_hidden_attrs(hidden_attrs):
    assert hidden_attrs == {
        "public_attr": "public",
        "_hidden_attr": "hidden",
    }


def test_get_hidden_methods(hidden_methods):
    assert "_hidden_method" in hidden_methods
    assert "public_method" in hidden_methods
    assert "__dunder_method__" not in hidden_methods


def test_get_dunder_attrs(dunder_attrs):
    assert "__dunder_attr__" in dunder_attrs
    assert "public_attr" in dunder_attrs


def test_get_dunder_methods(dunder_methods):
    assert "__dunder_method__" in dunder_methods
    assert "public_method" in dunder_methods


def test_with_specific_attribute() -> None:
    """Test with specific attribute."""

    class _TestObj:
        def __init__(self, name):
            self.name = name

    objects = [_TestObj("test1"), _TestObj("test2")]
    result = get_objects_by_attr(objects, "name", "test1")
    assert len(result) == 1
    assert result[0].name == "test1"


@mark.parametrize(
    "string, type_, expected",
    [
        ("1", "int", 1),
        ("1", int, 1),
        ("1.0", float, 1.0),
        ("True", bool, True),
        ("true", bool, True),
        ("t", bool, True),
        ("T", bool, True),
        ("yes", bool, True),
        ("y", bool, True),
        ("on", bool, True),
        ("0", int, 0),
        ("0.0", float, 0.0),
        ("False", bool, False),
        ("false", bool, False),
        ("f", bool, False),
        ("F", bool, False),
        ("no", bool, False),
        ("n", bool, False),
        ("off", bool, False),
        ("[]", "list", []),
        ("[]", list, []),
        ("[1,2,3]", list, [1, 2, 3]),
        ("['a','b','c']", list, ["a", "b", "c"]),
        ('{"a":1,"b":2}', dict, {"a": 1, "b": 2}),
        ('{"a":1,"b":2,"c":3}', dict, {"a": 1, "b": 2, "c": 3}),
        ('{"a":1,"b":2,"c":3,"d":4}', dict, {"a": 1, "b": 2, "c": 3, "d": 4}),
    ],
)
def test_envcast_trues(string: str, type_: type, expected: bool) -> None:
    """Test envcast function for trues."""
    assert envcast(string, type_) == expected


@mark.parametrize(
    "value, type_, error",
    (
        ("None", str, ValueError),
        ("none", 1, TypeError),
    ),
)
def test_envcast_falses(value: str, type_: type, error: type) -> None:
    """Test envcast function for falses."""
    with raises(error):
        envcast(value, type_, need=True)


def test_chktype_path_not_exist() -> None:
    """Test chktype function with Path object."""
    test_path = Path("non_existing_file.txt")  # Assume this file does not exist
    with raises(FileNotFoundError):
        chktype(test_path, Path)


@mark.parametrize(
    "path, suffix",
    (
        (Path("test.txt"), ".json"),
        (Path("test.json"), ".txt"),
        (Path(".env"), ".json"),
        (Path("test.json"), ".env"),
    ),
)
def test_chktype_path_suffix_raises(path: Path, suffix: str) -> None:
    """Test chktype function with Path object."""
    with raises(ValueError):
        chktype(path, Path, suffix=suffix, mustexist=False)


def test_isplatform() -> None:
    """Test isplatform function."""
    assert any((iswindows(), islinux(), ismacos()))


@mark.parametrize(
    "text, kwargs, expected",
    (
        ("example text", {"prefix": "Exa"}, True),
        ("example text", {"prefix": "test"}, False),
        ("example text", {"value": "ample"}, True),
        ("example text", {"value": "none"}, False),
        ("example text", {"suffix": "text"}, True),
        ("example text", {"suffix": "exam"}, False),
        ("abc", {"prefix": "a"}, True),
        ("abc", {"prefix": "b"}, False),
        ("abc", {"suffix": "c"}, True),
        ("abc", {"suffix": "b"}, False),
        ("abc", {"value": "b"}, True),
        ("abc", {"value": "a"}, True),
    ),
)
def test_chktext(text: str, kwargs: dict, expected: bool) -> None:
    """Test chktext function."""
    assert chktext(text, **kwargs) == expected


def test_chktext_raises() -> None:
    """Test chktext function with no input."""
    with raises(ValueError):
        chktext("example text")


def test_file_exists(file_path: Path) -> None:
    """Test chktype function with Path object."""
    assert chktype(file_path, Path, mustexist=True) == file_path


def test_chktype_incorrect() -> None:
    """Test chktype function with incorrect input."""
    with raises(TypeError):
        chktype("value", int)


@mark.parametrize(
    "value, type_",
    (
        (123, int),
        ("abc", str),
        (Path(__file__), Path),
        ([1, 2, 3], list),
        ({"a": 1, "b": 2}, dict),
        (True, bool),
    ),
)
def test_chktype_correct(value: int, type_: type) -> None:
    """Test chktype function with correct input."""
    assert chktype(value, type_) == value


def test_chkenv_default_for_non_existing_variable() -> None:
    """Test chkenv function with non existing variable."""
    assert chkenv("NON_EXISTING_VAR", need=False) is None


def test_chkenv_default_for_empty_variable() -> None:
    """Test chkenv function with empty variable."""
    assert chkenv("EMPTY_VAR", need=False, ifnull="default") == "default"
    with raises(ValueError):
        chkenv("EMPTY_VAR", need=True)


def test_chkenv_existing_variable(rand_env: str) -> None:
    """Test chkenv function with existing variable."""
    assert chkenv(rand_env) == environ[rand_env]


@mark.parametrize(
    "env, value, astype",
    (
        ("TRUE_VAR", True, bool),
        ("FALSE_VAR", False, bool),
        ("TRUE_VAR", 1, int),
        ("FALSE_VAR", 0, int),
        ("TRUE_VAR", "True", str),
        ("FALSE_VAR", "False", str),
        ("TEST_VAR", 123, int),
    ),
)
def test_chkenv_bool(env: str, value: bool, astype: type) -> None:
    """Test chkenv function with boolean values."""
    environ[env] = str(value)
    assert chkenv(env, astype=astype) == value


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

ISTRUE_TRUE = (
    True,
    "True",
    "true",
    "t",
    "T",
    "1",
    "on",
    1,
    1.0,
    "yes",
    "y",
)
ISTRUE_FALSE = (
    False,
    "False",
    "false",
    "f",
    "F",
    "0",
    "",
    None,
    0,
    "no",
    "off",
    "n",
    0.0,
)
ISNONE_TRUE = (
    "None",
    "none",
    "",
    None,
)
ISNONE_FALSE = (
    True,
    "test",
    1,
    0.0,
)
ISDUNDER_TRUE = ("__dunder__",)
ISDUNDER_FALSE = (
    "dunder__",
    "__dunder",
    "test",
)
ISHIDDEN_TRUE = (
    "_hidden",
    "_hidden_",
)
ISHIDDEN_FALSE = (
    "hidden_",
    "test",
)


@mark.fast
@mark.parametrize("is_dotenv_true", ISDOTENV_TRUE)
def test_is_dotenv_true(is_dotenv_true: bool) -> None:
    """Test to check .env detection"""
    assert is_dotenv(is_dotenv_true) is True


@mark.fast
@mark.parametrize("is_dotenv_false", ISDOTENV_FALSE)
def test_is_dotenv_false(is_dotenv_false: bool) -> None:
    """Test to check non-.env files"""
    assert is_dotenv(is_dotenv_false) is False


@mark.fast
@mark.parametrize("is_json_true", ISJSON_TRUE)
def test_is_json_true(is_json_true: bool) -> None:
    """Test to check JSON file detection"""
    assert is_json(is_json_true) is True


@mark.fast
@mark.parametrize("is_json_false", ISJSON_FALSE)
def test_is_json_false(is_json_false: bool) -> None:
    assert is_json(is_json_false) is False


@mark.fast
@mark.parametrize("a_string", ALL_STRINGS)
def test_is_a_string(a_string: str) -> None:
    assert isinstance(a_string, str)


@mark.fast
@mark.parametrize("a_path", ALL_PATHS)
def test_is_a_path(a_path: Path) -> None:
    assert isinstance(a_path, Path)


@mark.fast
@mark.parametrize("value", ISTRUE_TRUE)
def test_istrue_true(value: Any) -> None:
    """Test istrue function."""
    assert istrue(value) is True


@mark.fast
@mark.parametrize("value", ISTRUE_FALSE)
def test_istrue_false(value: Any) -> None:
    """Test istrue function."""
    assert istrue(value) is False


def test_istrue_raises_typeerror(now: datetime) -> None:
    """Test istrue function."""
    with raises(TypeError):
        istrue(now)


@mark.fast
@mark.parametrize("value", ISNONE_TRUE)
def test_isnone_true(value: Any) -> None:
    """Test isnone function."""
    assert isnone(value) is True


@mark.fast
@mark.parametrize("value", ISNONE_FALSE)
def test_isnone_false(value: Any) -> None:
    """Test isnone function."""
    assert isnone(value) is False


@mark.fast
@mark.parametrize("value", ISDUNDER_TRUE)
def test_isdunder_true(value: Any) -> None:
    """Test isdunder function."""
    assert isdunder(value) is True


@mark.fast
@mark.parametrize("value", ISDUNDER_FALSE)
def test_isdunder_false(value: Any) -> None:
    """Test isdunder function."""
    assert isdunder(value) is False


@mark.fast
@mark.parametrize("value", ISHIDDEN_TRUE)
def test_ishidden_true(value: Any) -> None:
    """Test ishidden function."""
    assert ishidden(value) is True


def test_ping_port_open(monkeypatch):
    """Check if the function returns True when the port is open"""

    def mock_connect_ex(addr, port):
        return 0  # Simulate port being open

    # Monkeypatch the socket's connect_ex method
    monkeypatch.setattr(socket, "connect_ex", mock_connect_ex)

    result = ping("127.0.0.1", 8080)

    # Asserting the function returns True
    assert result is True


def test_ping_port_closed(monkeypatch):
    """Check if the function returns False when the port is closed"""

    def mock_connect_ex(addr, port):
        return 1  # Simulate port being closed

    # Monkeypatch the socket's connect_ex method
    monkeypatch.setattr(socket, "connect_ex", mock_connect_ex)

    result = ping("127.0.0.1", 8080)

    # Asserting the function returns False
    assert result is False


def test_ping_port_open_astext(monkeypatch):
    """Check if the function returns the correct text when astext is True and the port is open"""

    def mock_connect_ex(addr, port):
        return 0  # Simulate port being open

    # Monkeypatch the socket's connect_ex method
    monkeypatch.setattr(socket, "connect_ex", mock_connect_ex)

    result = ping("127.0.0.1", 8080, astext=True)

    # Asserting the function returns the correct text
    assert result == "127.0.0.1:8080 is open"


def test_ping_port_closed_astext(monkeypatch):
    """Check if the function returns the correct text when astext is True and the port is closed"""

    def mock_connect_ex(addr, port):
        return 1  # Simulate port being closed

    # Monkeypatch the socket's connect_ex method
    monkeypatch.setattr(socket, "connect_ex", mock_connect_ex)

    result = ping("127.0.0.1", 8080, astext=True)

    # Asserting the function returns the correct text
    assert result == "127.0.0.1:8080 is not open"


def test_ping_logger(monkeypatch, caplog):
    """Check if the function logs the correct message when the port is closed"""

    def mock_connect_ex(addr, port):
        return 1  # Simulate port being closed

    # Monkeypatch the socket's connect_ex method
    monkeypatch.setattr(socket, "connect_ex", mock_connect_ex)

    with caplog.at_level("DEBUG"):  # Capture log output at DEBUG level
        ping("127.0.0.1", 8080)

    # Asserting that logger.debug was called with the correct message
    assert "127.0.0.1:8080 is not open" in caplog.text

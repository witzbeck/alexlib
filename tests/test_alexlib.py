from sys import path, version_info

from pytest import fixture, mark, raises

from alexlib import Version
from alexlib.constants import MODULE_PATH


@fixture(scope="session")
def module_path_string() -> str:
    return str(MODULE_PATH)


@fixture(scope="session")
def version_from_sys() -> Version:
    return Version.from_sys()


@mark.slow
def test_version_from_sys(version_from_sys: Version):
    assert version_from_sys.major == version_info.major
    assert version_from_sys.minor == version_info.minor
    assert version_from_sys.patch == version_info.micro
    assert version_from_sys.project_name == "Python"


@mark.slow
def test_version_from_pyproject():
    if version_info.minor <= 10:
        with raises(ImportError):
            Version.from_pyproject()
    else:
        version_from_pyproject = Version.from_pyproject()
        assert isinstance(
            version_from_pyproject.major, int
        ), f"major: {version_from_pyproject.major} is {type(version_from_pyproject.major)}"
        assert isinstance(
            version_from_pyproject.minor, int
        ), f"minor: {version_from_pyproject.minor} is {type(version_from_pyproject.minor)}"
        assert isinstance(
            version_from_pyproject.patch, int
        ), f"patch: {version_from_pyproject.patch} is {type(version_from_pyproject.patch)}"
        assert version_from_pyproject.project_name == "alexlib"


@mark.slow
def test_version_eq(version_from_sys: Version):
    if version_info.minor <= 10:
        with raises(ImportError):
            Version.from_pyproject()
    else:
        version_from_pyproject = Version.from_pyproject()
        assert version_from_sys != version_from_pyproject


@fixture(scope="module")
def version_from_str() -> Version:
    return Version.from_str("1.2.3", project_name="alexlib")


@mark.slow
def test_version_from_str_init(version_from_str: Version):
    assert version_from_str.major == 1
    assert version_from_str.minor == 2
    assert version_from_str.patch == 3
    assert version_from_str == Version(1, 2, 3)


@mark.slow
def test_version_from_str_repr(version_from_str: Version):
    assert repr(version_from_str) == "alexlib v1.2.3"


@mark.slow
def test_module_path_on_syspath(module_path_string: str):
    assert module_path_string in path

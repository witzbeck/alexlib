from pathlib import Path
from sys import path, version_info

from pytest import fixture

from alexlib import Version
from alexlib.constants import MODULE_PATH


@fixture(scope="session")
def module_path_string() -> str:
    return str(MODULE_PATH)


@fixture(scope="session")
def version_from_sys() -> Version:
    return Version.from_sys()


@fixture(scope="session")
def version_from_pyproject() -> Version:
    return Version.from_pyproject()


def test_version_from_sys(version_from_sys: Version):
    assert version_from_sys.major == version_info.major
    assert version_from_sys.minor == version_info.minor
    assert version_from_sys.patch == version_info.micro
    assert version_from_sys.project_name == "Python"


def test_version_from_pyproject(version_from_pyproject: Version):
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


def test_version_eq(version_from_sys: Version, version_from_pyproject: Version):
    assert version_from_sys != version_from_pyproject


def test_version_from_str():
    version = Version.from_str("1.2.3")
    assert version.major == 1
    assert version.minor == 2
    assert version.patch == 3
    assert version == Version(1, 2, 3)


def test_module_path_on_syspath(module_path_string: str):
    assert module_path_string in path


def test_core_path(core_path: Path):
    assert isinstance(core_path, Path)
    assert core_path.exists()


def test_core_string(core_string: str):
    assert isinstance(core_string, str)
    assert bool(core_string)

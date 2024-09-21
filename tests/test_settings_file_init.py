"""
Unit Tests for Config File Handling in Alexlib

This module contains a suite of unit tests for validating the functionality of the
Settings class in the alexlib.config module. It primarily focuses on ensuring that
the configuration file handling is correct and reliable.

Key Features Tested:
- Initialization of the Settings object from a JSON configuration file.
- Correct instantiation and properties of the Settings object.
- Functionality to read and process environment variables through the Settings object.

The tests are built using Python's unittest framework, making it easy to integrate
with standard testing and CI/CD workflows.

Note:
The tests rely on a 'settings.json' file located in the parent directory of this test module,
and environment variables specified in this settings file.

Example:
To run these tests, execute the module directly from the command line or use a test runner
compatible with unittest.

    $ python -m unittest path/to/this_module.py
"""

from os import getenv
from pathlib import Path
from random import choice
from tempfile import NamedTemporaryFile, TemporaryDirectory

from pytest import fixture

from alexlib.files.config import DotEnv, Settings


@fixture(scope="class")
def settings():
    with TemporaryDirectory() as temp_dir:
        SETTINGS_PATH = Path(temp_dir) / "settings.json"
        SETTINGS_PATH.write_text(
            """
            {
                "rand_key": "RAND_ENV",
                "rand_val": "1234"
            }
            """
        )
        yield Settings.from_path(SETTINGS_PATH)


@fixture(scope="class")
def rand_key(settings):
    return choice(list(settings.envdict.keys()))


@fixture(scope="class")
def rand_val(settings, rand_key):
    return settings.envdict[rand_key]


def test_settings_init(settings):
    assert settings.name == "settings.json"
    assert isinstance(settings, Settings)


def test_settings_envdict_init(settings):
    assert isinstance(settings.envdict, dict)
    assert len(settings.envdict) > 0


def test_gets_rand_env(settings, rand_key):
    assert getenv(rand_key) == settings.envdict[rand_key]


@fixture(scope="class")
def dotenv():
    with NamedTemporaryFile(prefix=".env", mode="w+t") as temp_env_file:
        path = Path(temp_env_file.name)
        path.write_text(
            """
            EXAMPLE_VAR=some_value
            ANOTHER_VAR=another_value
            """
        )
        yield DotEnv.from_path(path)


def test_load_env_vars(dotenv):
    assert getenv("EXAMPLE_VAR") == "some_value"
    assert getenv("ANOTHER_VAR") == "another_value"


def test_dotenv_init(dotenv):
    assert dotenv.name == ".env"
    assert isinstance(dotenv, DotEnv)


def test_dotenv_envdict_init(dotenv):
    assert isinstance(dotenv.envdict, dict)
    assert len(dotenv.envdict) > 0

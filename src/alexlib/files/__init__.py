from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from alexlib.constants import DOTENV_PATH, PROJECT_PATH
from alexlib.core import flatten_dict
from alexlib.files.config import ConfigFile
from alexlib.files.objects import File
from alexlib.files.utils import read_dotenv, read_json, read_toml


@dataclass
class JsonFile(File):
    """class for json files"""

    read: Callable = field(default=read_json, repr=False)


@dataclass
class TomlFile(File):
    """class for json files"""

    read: Callable = field(default=read_toml, repr=False)


@dataclass
class DotenvFile(ConfigFile):
    """A class to handle dotenv files"""

    name: str = field(default=".env")
    path: Path = field(default=DOTENV_PATH)

    def get_envdict(self) -> dict:
        return read_dotenv(self.path)


@dataclass
class SettingsFile(ConfigFile, JsonFile):
    """A class to handle settings files"""

    name: str = field(default="settings.json")
    path: Path = field(default=PROJECT_PATH / "settings.json")

    def get_envdict(self) -> dict[str, str]:
        """Returns the environment variables from the settings file"""
        flat_dict = flatten_dict(read_json(self.path))
        return flat_dict

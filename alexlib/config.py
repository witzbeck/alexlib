"""
Module for managing environment variables, configuration files, and logging in Python applications.

This module provides classes for handling environment variables and configuration files. It includes
the `EnvironmentVariable` class for managing individual environment variables, and `ConfigFile`, `DotEnv`,
and `Settings` classes for handling different types of configuration files.

Features:
- Easy manipulation and retrieval of environment variables.
- Support for dotenv files, JSON settings files, and custom configuration files.
- Methods for reading from, writing to, and updating configuration files.
- Integration with Python's logging module for basic configuration setup based on file settings.

Classes:
- EnvironmentVariable: Handles individual environment variables.
- ConfigFile: Base class for handling configuration files with utilities for environment variable management.
- DotEnv: Subclass of ConfigFile for specifically handling .env files.
- Settings: Subclass of ConfigFile for managing settings stored in JSON format.

Usage:
This module is intended to be used in Python applications for centralized management of configuration settings
and environment variables, simplifying tasks such as setting up logging, reading configuration files, and
environment variable manipulation.
"""
from dataclasses import dataclass
from dataclasses import field
from logging import basicConfig
from logging import INFO
from os import environ
from pathlib import Path
from random import choice
from typing import Any

from alexlib.constants import DATETIME_FORMAT
from alexlib.core import envcast
from alexlib.core import isnone
from alexlib.files import Directory
from alexlib.files import File


@dataclass
class EnvironmentVariable:
    """A class to handle environment variables"""

    key: str = field(default=None)
    value: str = field(default=None)
    type_: type = field(default=str)

    def __str__(self) -> str:
        """Returns the key=value string"""
        return f"{self.key}={self.value}"

    @property
    def varisset(self) -> bool:
        """Returns True if the variable is set, False otherwise"""
        return not isnone(self.value)

    @property
    def envisset(self) -> bool:
        """Returns True if the variable is set in the environment, False otherwise"""
        return self.key in environ

    @property
    def isnotstr(self) -> bool:
        """Returns True if the variable is not a string, False otherwise"""
        return not isinstance(self.type_, str)

    @staticmethod
    def setenv(key: str, value: str) -> None:
        """Sets the environment variable"""
        try:
            environ[key] = value
        except TypeError:
            environ[key] = str(value).strip('"')

    def __post_init__(self) -> None:
        """Sets the environment variable if it is not set"""
        EnvironmentVariable.setenv(self.key, self.value)
        if self.isnotstr:
            self.value = envcast(self.value, self.type_)

    @classmethod
    def from_pair(cls, key: str, value: str):
        """Creates an EnvironmentVariable from a key-value pair"""
        return cls(key=key, value=value)

    @classmethod
    def from_line(cls, line: str):
        """Creates an EnvironmentVariable from a line"""
        idx = line.index("=")
        k, v = line[:idx], line[idx + 1 :]
        return cls.from_pair(k, v)


@dataclass
class ConfigFile(File):
    """A class to handle configuration files"""

    envdict: dict = field(default_factory=dict)
    logdirname: str = field(default="logs")
    loglevel: int = field(default=INFO)
    eventlevel: int = field(default=INFO)
    logformat: str = field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    def __repr__(self) -> str:
        """Returns a string representation of the object"""
        return f"{self.clsname}({self.path.drive}/.../{self.name})"

    @property
    def isdotenv(self) -> bool:
        """Returns True if the file is a dotenv, False otherwise"""
        return self.name.startswith(".env")

    @property
    def nenvs(self) -> int:
        """Returns the number of environment variables"""
        return len(self.envdict)

    @property
    def keys(self) -> list[str]:
        """Returns the keys of the environment variables"""
        return self.envdict.keys()

    @property
    def rand_key(self) -> str:
        """Returns a random key"""
        return choice(list(self.keys))

    @property
    def values(self) -> list[str]:
        """Returns the values of the environment variables"""
        return self.envdict.values()

    @property
    def items(self) -> list[tuple[str, str]]:
        """Returns the items of the environment variables"""
        return self.envdict.items()

    def add_pair(
        self,
        key: str,
        value: str,
        tofile: bool = True,
        toenv: bool = True,
        todict: bool = True,
    ) -> None:
        """Adds a key-value pair to the environment variables"""
        if toenv:
            environ[key] = value
        if todict:
            self.envdict[key] = value
        if tofile and self.isdotenv:
            self.append_lines([f"{key}={value}"])
        elif tofile:
            raise ValueError("only handles dotenvs rn")

    @staticmethod
    def to_dotenv(path: Path, dict_: dict) -> None:
        """Writes a dictionary to a dotenv file"""
        lines = [f"{key}={value}" for key, value in dict_.items()]
        path.write_text("\n".join(lines))

    @staticmethod
    def setenvs(dict_: dict) -> None:
        """Sets the environment variables from a dictionary"""
        return [EnvironmentVariable.setenv(k, v) for k, v in dict_.items()]

    def read_dotenv(self) -> dict[str:Any]:
        """Reads a dotenv file"""
        lst = [EnvironmentVariable.from_line(line) for line in self.lines]
        return {x.key: x.value for x in lst}

    def get_envdict(self) -> dict[str:str]:
        """Returns the environment variables as a dictionary"""
        if self.isjson:
            dict_ = self.load_json()
        elif self.isdotenv:
            dict_ = self.read_dotenv()
        return dict_

    def set_envdict(self) -> None:
        """Sets the environment variables from the dictionary"""
        self.envdict = self.get_envdict()
        ConfigFile.setenvs(self.envdict)

    def __post_init__(self) -> None:
        """Sets the environment variables and basic configuration"""
        super().__post_init__()
        self.set_envdict()
        self.set_basic_config()

    @classmethod
    def from_path(cls, path: str | Path, **kwargs):
        """Creates a ConfigFile from a path"""
        if isinstance(path, str):
            path = Path(path)
        if not path.exists():
            return cls(name=f"{path.name}{path.suffix}")
        return cls(path=path, **kwargs)

    @classmethod
    def from_name(cls, name: str, **kwargs):
        """Creates a ConfigFile from a name"""
        return cls(name=name, **kwargs)

    @classmethod
    def from_dotenv(cls, name: str = None, **kwargs):
        """Creates a ConfigFile from a dotenv name"""
        clsname = ".env"
        clsname = clsname if name is None else f"{clsname}.{name}"
        return cls.from_name(name=clsname, **kwargs)

    def __add__(self, other: object) -> object:
        """Adds two ConfigFiles"""
        self.envdict.update(other.envdict)
        return self

    @classmethod
    def from_name_list(cls, names: list[str], **kwargs):
        """Creates a ConfigFile from a list of names"""
        env_dict = {}
        for name in names:
            print(name)
            file = cls.from_name(name, **kwargs)
            env_dict.update(file.envdict)
        file.envdict = env_dict
        file.name = "envs"
        return file

    @classmethod
    def from_dotenv_name_list(cls, names: list[str], **kwargs):
        """Creates a ConfigFile from a list of dotenv names"""
        names = [f".env.{name}" for name in names]
        return cls.from_name_list(names, **kwargs)

    def mkdir(self, name: str, exist_ok: bool = True) -> Path:
        """Creates a directory"""
        d = self.path / name
        d.mkdir(name, exist_ok=exist_ok)
        return d

    @property
    def logdir(self) -> Directory:
        """Returns the log directory"""
        d = Directory(path=self.parent) / self.logdirname
        d.path.mkdir(exist_ok=True)
        return d

    @property
    def curfile(self) -> str:
        """Returns the current file"""
        return eval("__file__")

    @property
    def curpath(self) -> Path:
        """Returns the current path"""
        return Path(self.curfile)

    @property
    def curname(self) -> str:
        """Returns the current name"""
        return self.curpath.name

    def set_basic_config(self) -> None:
        """Sets the basic configuration"""
        logdir = self.logdir
        name = self.curname
        logfile = logdir.path / f"{name}.log"
        basicConfig(
            filename=logfile,
            format=self.logformat,
            datefmt=DATETIME_FORMAT,
            level=self.loglevel,
        )


@dataclass
class DotEnv(ConfigFile):
    """A class to handle dotenv files"""

    name: str = field(default=".env")

    @property
    def lines(self) -> list[str]:
        """Returns the lines of the file"""
        return [x for x in super().lines if not x.startswith("#") and "=" in x]


@dataclass
class Settings(ConfigFile):
    """A class to handle settings files"""

    name: str = field(default="settings.json")

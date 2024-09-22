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

from dataclasses import dataclass, field
from logging import INFO, basicConfig
from os import environ
from pathlib import Path

from alexlib.constants import (
    DATETIME_FORMAT,
    DOTENV_PATH,
    LOG_FORMAT,
    LOG_PATH,
    PROJECT_PATH,
)
from alexlib.core import chktype
from alexlib.files.objects import File
from alexlib.files.utils import is_dotenv, is_json, write_json


@dataclass
class ConfigFile(File):
    """A class to handle configuration files"""

    envdict: dict = field(default_factory=dict, repr=False)
    logdirname: str = field(default="logs")
    loglevel: int = field(default=INFO)
    eventlevel: int = field(default=INFO)
    logformat: str = field(
        default=LOG_FORMAT,
    )

    def __repr__(self) -> str:
        """Returns a string representation of the object"""
        return f"{self.clsname}({self.path.drive}/.../{self.name})"

    def __len__(self) -> int:
        """Returns the number of environment variables"""
        return len(self.envdict)

    def add_pair(
        self,
        key: str,
        value: str,
        tofile: bool = True,
        toenv: bool = True,
    ) -> None:
        """Adds a key-value pair to the environment variables"""
        chktype(key, str)
        self.envdict[key] = value
        if toenv:
            environ[key] = value
        if tofile and is_dotenv(self.path):
            self.append_lines([f"{key}={value}"])
        elif tofile and is_json(self.path):
            self.to_json()
        elif tofile:
            raise ValueError("only handles dotenvs rn")

    @property
    def dotenv_lines(self) -> list[str]:
        """Returns the lines of the dotenv file"""
        return [f"{key}={value}" for key, value in self.envdict.items()]

    def to_dotenv(self, path: Path = DOTENV_PATH) -> None:
        """Writes a dictionary to a dotenv file"""
        path.write_text("\n".join(self.dotenv_lines))

    def to_json(self, path: Path = PROJECT_PATH / "settings.json") -> None:
        """Writes a dictionary to a JSON file"""
        write_json(self.envdict, path)

    def get_envdict(self) -> dict[str:str]:
        """Returns the environment variables as a dictionary"""
        raise NotImplementedError("This method must be implemented in a subclass")

    def __post_init__(self) -> None:
        """Sets the environment variables and basic configuration"""
        if self.path.exists():
            self.envdict = self.get_envdict()
            environ.update({str(k): str(v) for k, v in self.envdict.items()})
        self.set_basic_config()

    def set_basic_config(self) -> None:
        """Sets the basic configuration"""
        logfile = LOG_PATH / f"{PROJECT_PATH.stem}.log"
        basicConfig(
            filename=logfile,
            format=self.logformat,
            datefmt=DATETIME_FORMAT,
            level=self.loglevel,
        )

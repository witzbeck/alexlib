from dataclasses import dataclass, field
from os import environ, getenv
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from alexlib.file import File


def istrue(w: str):
    if isinstance(w, bool):
        ret = w is True
    elif isinstance(w, str):
        ret = w == 'True'
    return ret


def isnone(w: str):
    if isinstance(w, str):
        ret = w == 'None'
    else:
        ret = w is None
    return ret


def aslist(val: str, separator: str = ","):
    return val.split(separator)


def astype(val: str, type_: type):
    if issubclass(type_, list):
        ret = aslist(val)
    elif issubclass(type_, bool):
        ret = istrue(val)
    else:
        ret = type_(val)
    return ret


def chkenv(
        key: str,
        type: type = None,
        required: bool = True,
) -> Any:
    val = getenv(key)
    if type is not None:
        val = astype(val, type)
    if (required and isnone(val)):
        raise ValueError("value required")
    return val


@dataclass
class EnvVar:
    key: str = field(default=None)
    value: str = field(default=None)
    type_: type = field(default=str)

    @property
    def varisset(self):
        return not isnone(self.value)

    @property
    def envisset(self):
        return self.key in environ

    @property
    def isnotstr(self):
        return not isinstance(self.type_, str)

    def __post_init__(self):
        self.set_value()

    @staticmethod
    def setenv(key: str, value: str):
        environ[key] = value

    def get_value(self, key: str):
        if self.varisset:
            ret = self.value
        elif self.envisset:
            ret = getenv(self.key)
        else:
            raise ValueError(f"{key} not set in env or var")
        if self.isnotstr:
            ret = astype(ret, self.type_)
        return ret

    def set_value(self):
        self.set_value_env()
        self.value = self.get_value()

    def set_value_env(self):
        if not self.envisset:
            self.setenv(self.key, self.value)

    @classmethod
    def from_pair(cls, key: str, value: str):
        return cls(key=key, value=value)


@dataclass
class ConfigFile(File):
    envdict: dict = field(default_factory=dict)

    @property
    def nenvs(self):
        return len(self.envdict)

    def read_dotenv(self):
        if not self.isdotenv:
            raise ValueError("not a dotenv file")
        try:
            load_dotenv(self.path)
        except FileNotFoundError:
            load_dotenv()

    def to_dotenv(self, _dict: dict):
        if not self.isdotenv:
            raise ValueError("not a dotenv file")
        with open(self.path, "w") as f:
            for key, value in _dict.items():
                f.write(f"{key}={value}\n")

    @staticmethod
    def setenvs(dict_: dict):
        keys = list(dict_.keys())
        [EnvVar.setenv(key, dict_[key]) for key in keys]

    def get_envdict(self):
        if self.nenvs > 0:
            return self.envdict
        elif self.isjson:
            self.envdict = self.read_json()
            ConfigFile.setenvs(self.envdict)
        elif self.isdotenv:
            self.read_dotenv()
        return environ

    def set_envdict(self):
        self.envdict = self.get_envdict()

    def __post_init__(self):
        super().__post_init__()
        self.set_envdict()

    @classmethod
    def from_path(cls, path: str | Path):
        if isinstance(path, str):
            path = Path(path)
        if not path.exists():
            return cls(name=f"{path.name}{path.suffix}")
        return cls(path=path)

    @classmethod
    def from_name(cls, name: str):
        return cls(name=name)

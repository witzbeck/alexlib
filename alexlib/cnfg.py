from dataclasses import dataclass, field
from logging import INFO, basicConfig, info
from os import environ, getenv
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from alexlib.file import File, Directory


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
    typeisnone = type is None
    valisnone = isnone(val)
    if (not valisnone and typeisnone):
        val = val
    elif (required and valisnone):
        raise ValueError("value required")
    elif (not required and valisnone):
        val = None
    elif not typeisnone:
        val = astype(val, type)
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
    logdirname: str = field(default="logs")
    loglevel: int = field(default=INFO)
    eventlevel: int = field(default=INFO)
    logformat: str = field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    dateformat: str = field(default="%m/%d/%Y %I:%M:%S %p")

    @property
    def environ(self) -> dict:
        return environ

    @property
    def nenvs(self) -> int:
        return len(self.envdict)

    @property
    def keys(self) -> list[str]:
        return list(self.envdict.keys())

    @property
    def values(self) -> list[str]:
        return list(self.envdict.values())

    def add_pair(
            self,
            key: str,
            value: str,
            tofile: bool = True,
            toenv: bool = True,
            todict: bool = True,
    ):
        if toenv:
            environ[key] = value
        if todict:
            self.envdict[key] = value
        if (tofile and self.isdotenv):
            self.append(f"{key}={value}")
        elif tofile:
            raise ValueError("only handles dotenvs rn")

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
        self.set_basic_config()

    @classmethod
    def from_path(cls, path: str | Path):
        if isinstance(path, str):
            path = Path(path)
        if not path.exists():
            return cls(name=f"{path.name}{path.suffix}")
        return cls(path=path)

    @classmethod
    def from_name(
        cls,
        name: str,
        **kwargs,
    ):
        return cls(name=name, **kwargs)

    @classmethod
    def from_dotenv(
        cls,
        name: str = None,
        **kwargs,
    ):
        clsname = ".env"
        clsname = clsname if name is None else f"{clsname}.{name}"
        return cls.from_name(name=clsname, **kwargs)

    def __add__(self, other: object):
        self.envdict.update(other.envdict)
        return self

    @classmethod
    def from_name_list(cls, names: list[str], **kwargs):
        first = names.pop(0)
        return sum([
            cls.from_name(name, **kwargs)
            for name in names],
            cls(name=first)
        )

    @classmethod
    def from_dotenv_name_list(cls, names: list[str], **kwargs):
        names = [f".env.{name}" for name in names]
        return cls.from_name_list(names, **kwargs)

    def mkdir(
            self,
            name: str,
            exist_ok: bool = True
    ):
        d = self / name
        d.path.mkdir(name, exist_ok=exist_ok)
        return d

    @property
    def logdir(self) -> Directory:
        d = Directory(path=self.parent) / self.logdirname
        d.path.mkdir(exist_ok=True)
        return d

    @property
    def curfile(self) -> str:
        return eval("__file__")

    @property
    def curpath(self) -> Path:
        return Path(self.curfile)

    @property
    def curname(self) -> str:
        return self.curpath.name

    def set_basic_config(self):
        logdir = self.logdir
        name = self.curname
        logfile = logdir.path / f"{name}.log"
        basicConfig(
            filename=logfile,
            format=self.logformat,
            datefmt=self.dateformat,
            level=self.loglevel,
        )


if __name__ == "__main__":
    c = ConfigFile.from_dotenv()
    c.set_basic_config()
    info("this is a logging test")

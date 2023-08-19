from dataclasses import dataclass, field
from datetime import datetime as dt, timedelta as td
from json import load, loads, dump, dumps
from pathlib import Path
from os import environ, getenv

from dotenv import load_dotenv


def pathsearch(pattern: str, start_path: Path = Path(__file__)):
    while True:
        try:
            return [x for x in start_path.rglob(pattern)][0]
        except IndexError:
            start_path = start_path.parent


def get_date_str(
        usedate: bool = True,
        usetime: bool = True,
        usenow: bool = True,
        datetime: dt = None,
) -> str:
    _dt = datetime
    dparts = []
    tparts = []
    if usenow:
        _dt = dt.now()
    if usedate:
        dparts = [_dt.year, _dt.month, _dt.day]
    if usetime:
        tparts = [_dt.hour, _dt.minute, _dt.second]
    date = "-".join([str(x) for x in dparts])
    time = ":".join([str(x) for x in tparts])
    return "_".join([date, time])


def eval_td(dt1: dt, dt2: dt = dt.now()):
    if isinstance(dt1, float):
        dt1 = dt.fromtimestamp(dt1)
    return dt2 - dt1


@dataclass
class EnvVar:
    key: str = field(default=None)
    value: str = field(default=None)
    type_: type = field(default=str)

    @staticmethod
    def astype(value: str, type_: type):
        if issubclass(type_, list):
            ret = value.split(",")
        else:
            ret = type_(value)
        return ret

    @property
    def varisset(self):
        return self.value is not None

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
            ret = EnvVar.astype(ret, self.type_)
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
class SystemObject:
    path: Path = field(default=None)
    name: str = field(default=None)
    _parent: Path = field(default=None)

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, path: Path):
        self._parent = path

    @property
    def stat(self):
        return self.path.stat()

    @property
    def exists(self):
        return self.path.exists()

    @property
    def isfile(self):
        return self.path.is_file()

    @property
    def isdir(self):
        return self.path.is_dir()

    @property
    def ctime_age(self):
        return eval_td(self.stat.st_ctime)

    @property
    def mtime_age(self):
        return eval_td(self.stat.st_mtime)

    def isnewenough(self, limit: td):
        if self.mtime_age < limit:
            return True
        else:
            return False

    def get_name(self):
        if self.name is not None:
            ret = self.name
        elif self.path.is_dir():
            ret = self.path.name
        elif self.path.is_file():
            name = self.path.name
            ext = self.path.suffix
            ret = f"{name}.{ext}"
        else:
            raise ValueError("need path or name")
        return ret

    def set_name(self):
        self.name = self.get_name()

    def get_path(self):
        if self.path is not None:
            return self.path
        else:
            return pathsearch(self.name)

    def set_path(self):
        self.path = self.get_path()

    def __post_init__(self):
        self.set_path()
        self.set_name()


@dataclass
class File(SystemObject):
    def istype(self, suffix: str, separator: str = "."):
        ret = self.path.suffix == suffix
        sepinret = separator in ret
        retidx = ret.index(separator)
        if (sepinret and retidx == 0):
            return True
        elif (sepinret and retidx > 0):
            return False
        
            or (not sepinret):
            ret.index(".")


    @property
    def isdotenv(self):
        return self.name.startswith(".env")

    @property
    def isjson(self):
        return self.istype(".json")

    def read_json(self):
        if not self.isjson:
            raise ValueError("not a json file")
        with open(self.path, "r") as file:
            try:
                ret = load(file)
            except TypeError:
                ret = loads(load(file))
        return ret

    def to_json(self, _dict: dict):
        if not self.isjson:
            raise ValueError("not a json file")
        with open(self.path, "w") as f:
            dump(dumps(_dict), fp=f)


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

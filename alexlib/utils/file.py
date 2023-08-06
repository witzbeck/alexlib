from dataclasses import dataclass, field
from datetime import datetime as dt, timedelta as td
from json import load, loads, dump, dumps
from pathlib import Path


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

    @path.getter
    def path(self):
        if self.path is not None:
            return self.path
        else:
            return pathsearch(self.name)


@dataclass
class File(SystemObject):
    def read_json(self):
        with open(self.path, "r") as file:
            return loads(load(file))

    def to_json(self, _dict: dict):
        with open(self.path, "w") as f:
            dump(dumps(_dict), fp=f)

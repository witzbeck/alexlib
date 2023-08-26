from dataclasses import dataclass, field
from datetime import datetime as dt, timedelta as td
from json import load, loads, dump, dumps, JSONDecodeError
from pathlib import Path
from typing import Any, Callable

from matplotlib.pyplot import savefig
from pandas import DataFrame
from pandas import read_csv, read_sql, read_excel
from sqlalchemy import engine

from alexlib.iters import link


def figsave(
        name: str,
        dirpath: Path,
        format: str = "png",
        **kwargs,  # use bb_inches=tight if cutoff
) -> bool:  # returns True if successful
    path = dirpath / f"{name}.{format}"
    savefig(path, format=format, **kwargs)
    return path.exists()


def pathsearch(
        pattern: str,
        start_path: Path = Path(__file__),
        listok: bool = False,
) -> Path | list[Path]:
    while True:
        try:
            ret = [x for x in start_path.rglob(pattern)]
            if listok:
                return ret
            else:
                return ret[0]
        except IndexError:
            start_path = start_path.parent


def path_list_to_dict(
        path_list: list[Path],
        func: Callable = None,
) -> dict[Any]:
    if func is not None:
        return {x.stem: x for x in path_list}
    else:
        return {x.stem: func(x) for x in path_list}


def df_to_db(
        df: DataFrame,
        engine: engine,
        table_name: str,
        schema: str = None,
        if_exists: str = "replace",
        index: bool = False,
        chunksize: int = 10000,
        method: str = "multi",
):
    df.to_sql(
        table_name,
        engine,
        if_exists=if_exists,
        schema=schema,
        index=index,
        chunksize=chunksize,
        method=method,
    )


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


def copy_csv_str(table_name, csv_path):
    return f"""COPY {table_name}
    FROM '{csv_path}'
    DELIMITER ','
    CSV HEADER
    """


def eval_td(dt1: dt, dt2: dt = dt.now()):
    if isinstance(dt1, float):
        dt1 = dt.fromtimestamp(dt1)
    return dt2 - dt1


@dataclass
class SystemObject:
    path: Path = field(default=None)
    name: str = field(default=None)

    def __repr__(self):
        clss = self.__class__.__name__
        parent = self.parent
        return f"{clss}({self.name}), parent: {str(parent)}"

    @property
    def parent(self):
        return self.path.parent

    @property
    def parents(self):
        return [x.name for x in self.path.parents]

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
            ret = self.path.name
        else:
            raise ValueError("need path or name")
        return ret

    def set_name(self):
        self.name = self.get_name()

    def get_path(self):
        notnone = self.path is not None
        isstr = isinstance(self.path, str)
        ispath = isinstance(self.path, Path)
        if (notnone and ispath):
            return self.path
        elif (notnone and isstr):
            return Path(self.path)
        elif self.name is not None:
            return pathsearch(self.name)
        else:
            raise ValueError("need path or name")

    def set_path(self):
        self.path = self.get_path()

    def __post_init__(self):
        self.set_path()
        self.set_name()


@dataclass
class File(SystemObject):
    schema: str = field(
        default=None,
        repr=False,
    )
    sep: str = field(
        default=".",
        repr=False,
    )
    df: DataFrame = field(
        default=None,
        repr=False,
    )

    @property
    def bytes(self):
        return self.path.read_bytes()

    @property
    def text(self):
        return self.path.read_text()

    @property
    def lines(self):
        return self.text.split("\n")

    def lineexists(self, line: str):
        return line in self.lines

    def write_lines(self, lines: list[str]):
        self.path.write_text("\n".join(lines))

    def filter_new_lines(self, tochk: str | list[str]):
        if isinstance(tochk, str):
            tochk = [tochk]
        return [x for x in tochk if not self.lineexists(x)]

    def get_toadd(
            self,
            toadd: list[str],
            onlynew: bool
    ):
        if isinstance(toadd, str):
            toadd = [toadd]
        if onlynew:
            toadd = self.filter_new_lines(toadd)
        return toadd

    def append(
            self,
            toadd: str | list[str],
            onlynew: bool = True,
    ) -> None:
        lines = self.lines
        toadd = self.get_toadd(toadd, onlynew)
        lines.extend(toadd)
        self.write_lines(lines)

    def insert_line(
            self,
            index: int,
            line: str,
            onlynew: bool = True,
    ) -> None:
        if (onlynew and self.lineexists(line)):
            pass
        else:
            lines = self.lines
            lines.insert(index, line)
            self.write_lines(lines)

    def prepend(
            self,
            toadd: str | list[str],
            onlynew: bool = True,
    ) -> None:
        lines = self.lines
        toadd = self.get_toadd(toadd, onlynew)
        toadd.extend(lines)
        self.write_lines(toadd)

    def __len__(self):
        return len(self.lines)

    @property
    def filetype(self):
        return self.path.suffix

    @property
    def ext(self):
        return self.path.suffix.strip(self.sep)

    def istype(self, suffix: str):
        return self.filetype.endswith(suffix)

    @property
    def isdotenv(self):
        return self.name.startswith(".env")

    @property
    def isjson(self):
        return self.istype(".json")

    @property
    def iscsv(self):
        return self.istype(".csv")

    @property
    def isxlxs(self):
        return self.istype(".xlsx")

    @property
    def issql(self):
        return self.istype(".sql")

    def read_json(self, path: Path, asdf: bool = False):
        if not path.suffix.endswith("json"):
            raise ValueError("not a json file")
        ret = recs = None
        with open(path, "r") as file:
            try:
                ret = load(file)
            except TypeError:
                ret = loads(load(file))
            except JSONDecodeError:
                recs = [loads(x) for x in self.lines if len(x) > 1]
        if (ret is not None and asdf):
            ret = DataFrame.from_dict(ret)
        elif (recs is not None and asdf):
            ret = DataFrame.from_records(recs)
        elif recs is not None:
            ret = recs
        return ret

    def to_json(self, _dict: dict):
        if not self.isjson:
            raise ValueError("not a json file")
        with open(self.path, "w") as f:
            dump(dumps(_dict), fp=f)
        pass

    @property
    def read_func(self):
        if self.iscsv:
            ret = read_csv
        elif self.isxlxs:
            ret = read_excel
        elif self.issql:
            ret = read_sql
        elif self.isjson:
            ret = self.read_json
        else:
            raise ValueError("not a valid filetype")
        return ret

    def get_df(
            self,
            schema: str = None,
            table: str = None,
            **kwargs,
    ) -> DataFrame:
        torsisnone = (table is None or schema is None)
        if (self.issql and torsisnone):
            raise ValueError("need schema.table for sql file")
        return self.read_func(
            self.path,
            *args,
            **kwargs,
    )



@dataclass
class Directory(SystemObject):
    @property
    def contents(self):
        return [x for x in self.path.iterdir()]

    @property
    def filepaths(self):
        return [x for x in self.contents if x.is_file()]

    @property
    def files(self):
        return [File(path=x) for x in self.filepaths]

    @property
    def dirpaths(self):
        return [x for x in self.contents if x.is_dir()]

    @property
    def dirs(self):
        return [Directory(path=x) for x in self.dirpaths]

    @property
    def nfiles(self):
        return len(self.filepaths)

    @property
    def ndirs(self):
        return len(self.dirpaths)

    @property
    def ncontents(self):
        return len(self.contents)

    @property
    def allchilddirs(self):
        childdirs = [x.allchilddirs for x in self.dirs]
        return self.dirs + link(childdirs)

    @property
    def allchildfiles(self):
        childfiles = [x.files for x in self.allchilddirs]
        return self.files + link(childfiles)

    def go_up(self, n: int | str = 1):
        for _ in range(n):
            try:
                self.path = self.path.parent
            except PermissionError:
                break
            if self.path == Path("/"):
                break
            elif self.path.name == n:
                break
        self.set_name()

    def insert_all_files(
            self,
            engine: engine,
            schema: str = None
    ) -> int:  # total rows inserted
        total_rows = 0
        if schema is None:
            schema = self.parent.name

        for file in self.files:
            try:
                file.to_db(engine, schema=schema)
                total_rows += file.nrows
            except ValueError:
                """only adds files with read function"""

        return total_rows


if __name__ == "__main__":
    """
    d = Directory(path=Path(__file__))
    d.go_up(3)
    print(d)
    for f in d.allchildfiles:
        if f.isdotenv:
            print(f)
    """
    f = File(name=".env")
    print(f)

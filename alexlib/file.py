from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import cached_property, partial
from json import load, loads, dump, dumps
from logging import info
from os import getenv
from pathlib import Path
from random import choice
from typing import Callable, Any

from matplotlib.pyplot import savefig
from pandas import DataFrame
from sqlalchemy import Engine

from alexlib.constants import date_format, datetime_format
from alexlib.core import sha256sum, chkenv
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


def eval_parents(
    path: Path,
    include: list[str],
    exclude: list[str],
) -> bool:
    ninclude = len(include)
    parts = path.parts

    nincluded = sum([x in include for x in parts])
    incpass = (nincluded == ninclude or include is None)

    nexcluded = sum([x in exclude for x in parts])
    excpass = (nexcluded == 0 or exclude is None)
    return (incpass and excpass)


def path_search(
        pattern: str,
        start_path: Path = eval("Path(__file__)"),
        listok: bool = False,
        include: list[str] = [],
        exclude: list[str] = [],
) -> Path | list[Path]:
    if isinstance(exclude, str):
        exclude = [exclude]
    if isinstance(include, str):
        include = [include]
    while True:
        try:
            ret = [x for x in start_path.rglob(pattern)]
            ret = [
                x for x in ret
                if eval_parents(x, include, exclude)
            ]
            if listok:
                return ret
            else:
                return ret[0]
        except IndexError:
            start_path = start_path.parent


def copy_csv_str(table_name: str, csv_path: Path) -> str:
    return f"""COPY {table_name} FROM '{csv_path}'
    DELIMITER ','
    CSV HEADER
    """


@dataclass
class SystemObject:
    name: str = field(default=None)
    path: Path = field(default=None)
    include: list[str] = field(
        default_factory=list,
        repr=False,
    )
    exclude: list[str] = field(
        default_factory=list,
        repr=False,
    )
    max_ascends: int = field(
        repr=False,
        default=8
    )

    @property
    def sysobj_names(self):
        return ["Directory", "File", "SystemObject"]

    @property
    def haspath(self):
        return self.path is not None

    @property
    def hasname(self):
        return self.name is not None

    @property
    def user(self):
        return getenv("USERNAME")

    @property
    def hasuser(self):
        return self.user is not None

    @staticmethod
    def add_path_cond(
        cur_list: list[str],
        toadd: str | list[str]
    ) -> list[str]:
        if isinstance(toadd, str):
            toadd = [toadd]
        elif not toadd:
            toadd = []
        if isinstance(cur_list, str):
            cur_list = [cur_list]
        return cur_list + toadd

    def get_path(
        self,
        include: list[str] | str = None,
        exclude: list[str] | str = None,
        start_path: Path = None,
    ) -> Path:
        if include or self.include:
            include = SystemObject.add_path_cond(self.include, include)
        if exclude or self.exclude:
            exclude = SystemObject.add_path_cond(self.exclude, exclude)
        if isinstance(self.path, Path):
            ret = self.path
        elif self.haspath and isinstance(self.path, str):
            ret = Path(self.path)
        elif self.haspath and self.__class__.__name__ in self.sysobj_names:
            ret = self.path.path
        elif self.name is not None:
            ret = path_search(
                self.name,
                include=include,
                exclude=exclude,
                start_path=start_path,
                max_ascends=self.max_ascends
            )
        else:
            raise ValueError(
                f"need name cur={self.name} or path cur={self.path}"
            )
        return ret

    def set_path(self):
        self.path = self.get_path(include=self.include)

    def get_name(self):
        if self.hasname:
            ret = self.name
        elif self.haspath and self.__class__.__name__ in self.sysobj_names:
            ret = self.path.name
        elif self.haspath:
            ret = self.path.stem
        elif self.name is None and self.path is None:
            raise ValueError("need name or path")
        else:
            ret = self.name
        return ret

    def set_name(self):
        self.name = self.get_name()

    def __post_init__(self):
        self.set_path()
        if not isinstance(self.path, Path):
            raise TypeError(f"{self.path} is not Path")
        self.set_name()
        if not isinstance(self.name, str):
            raise TypeError(f"{self.name} is not str")

    @property
    def parent(self) -> Path:
        return self.path.parent

    @property
    def parents(self) -> list[Path]:
        return [x for x in self.path.parents]

    @property
    def parts(self) -> list[Path]:
        return self.path.parts

    def get_parent(self, name: str) -> Path:
        if name not in self.parts:
            raise ValueError(f"{name} not in parents[{self.parts}]")
        else:
            return [x for x in self.parents if x.name == name][-1]

    @property
    def nparents(self) -> int:
        return len(self.parents)

    @property
    def stat(self):
        return self.path.stat()

    @property
    def uid(self):
        return self.stat.st_uid

    @property
    def gid(self):
        return self.stat.st_gid

    @property
    def uidiszero(self):
        return self.uid == 0

    @property
    def gidiszero(self):
        return self.gid == 0

    @property
    def owner(self):
        if not (self.gidiszero and self.uidiszero):
            ret = f"{self.gid}:{self.uid}"
        elif not self.uidiszero:
            ret = self.uid
        else:
            ret = self.user
        return ret

    @staticmethod
    def get_path_attr(path: Path, attr: str) -> Any:
        try:
            ret = getattr(path.stat(), attr)
        except AttributeError:
            ret = getattr(path, attr)
        return ret

    @property
    def modified_timestamp(self) -> float:
        return self.stat.st_mtime

    @property
    def created_timestamp(self) -> float:
        return self.stat.st_ctime

    @property
    def modified_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.modified_timestamp)

    @property
    def created_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.created_timestamp)

    @property
    def modified_strfdate(self) -> str:
        return self.modified_datetime.strftime(date_format)

    @property
    def created_strfdate(self) -> str:
        return self.created_datetime.strftime(date_format)

    @property
    def modified_strfdatetime(self) -> str:
        return self.modified_datetime.strftime(datetime_format)

    @property
    def created_strfdatetime(self) -> str:
        return self.created_datetime.strftime(datetime_format)

    @property
    def modified_delta(self) -> timedelta:
        return datetime.now() - self.modified_datetime

    @property
    def created_delta(self) -> timedelta:
        return datetime.now() - self.created_datetime

    def is_new_enough(
        self,
        min_delta: timedelta,
    ) -> bool:
        return self.created_delta < min_delta

    @cached_property
    def clsname(self) -> str:
        return self.__class__.__name__

    @property
    def exists(self):
        if not self.haspath:
            ret = False
        else:
            ret = self.path.exists()
        return ret

    def chk_exists(self):
        if not self.exists:
            raise FileNotFoundError(f"no {self.clsname} @ {self.path}")

    @classmethod
    def from_path(cls, path: Path, **kwargs):
        if isinstance(path, str):
            path = Path(path)
        return cls(path=path, **kwargs)

    @classmethod
    def from_name(cls, name: str, **kwargs):
        return cls(name=name, **kwargs)

    def eval_method(
        self,
        method: str,
        *args,
        **kwargs,
    ) -> Any:
        func = getattr(self, method)
        return func(*args, **kwargs)

    @classmethod
    def find(cls, name: str, **kwargs):
        return cls(path=path_search(name, **kwargs))


def eval_method_list(
    method: str, lst: list[SystemObject], *args, **kwargs
) -> list[Any]:
    return [x.eval_method(method, *args, **kwargs) for x in lst]


@dataclass
class File(SystemObject):
    name: str = field(default=None)
    path: Path = field(
        default=None,
        repr=False,
    )
    encrypted: bool = field(
        default=False,
        repr=False,
    )

    @property
    def hash(path: Path):
        return sha256sum(path)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name})"

    def rm(self):
        self.path.unlink()

    def rename(self, name: str, overwrite: bool = False):
        newpath = self.path.parent / name
        if overwrite and newpath.exists():
            newpath.unlink()
        self.path.rename(self.path.parent / name)
        self.path = newpath
        self.set_name()

    def istype(self, suffix: str):
        low = self.path.suffix.lower()
        other = suffix.strip(".").lower()
        return low.endswith(other)

    @property
    def isxlsx(self):
        return self.istype(".xlsx")

    @property
    def issql(self):
        return self.istype(".sql")

    @property
    def iscsv(self):
        return self.istype(".csv")

    @property
    def isjson(self):
        return self.istype(".json")

    @property
    def istxt(self):
        return self.istype(".txt")

    @property
    def ispy(self):
        return self.istype(".py")

    @property
    def isipynb(self):
        return self.istype(".ipynb")

    @property
    def text(self) -> str:
        try:
            return self.path.read_text()
        except UnicodeDecodeError:
            return self.path.read_text(encoding="utf8")

    @property
    def lines(self) -> list[str]:
        return self.text.split("\n")

    @staticmethod
    def filter_lines(
        lines: list[str],
        startchar: int,
        endchar: int,
    ):
        pass

    def get_filter_lines(self):
        pass

    @property
    def line_counter(self) -> Counter:
        return Counter(self.lines)

    @property
    def nlines(self) -> int:
        return len(self.lines)

    @property
    def line_indexes(self) -> dict[str: list[int]]:
        lines, rng = self.lines, range(self.nlines)
        return {
            line: [i + 1 for i in rng if line == lines[i]]
            for line in self.line_counter.keys()
        }

    @property
    def line_repeats(self) -> dict[str: list[int]]:
        return {
            k: v
            for k, v in self.line_indexes.items()
            if (len(v) > 1 and len(k) > 0)
        }

    @property
    def line_lengths(self) -> list[int]:
        return [len(x) for x in self.lines]

    def write_lines(self, lines: list[str]) -> None:
        self.path.write_text("\n".join(lines))

    def append_lines(self, lines: list[str]) -> None:
        self.write_lines(self.lines + lines)

    def prepend_lines(self, lines: list[str]) -> None:
        self.write_lines(lines + self.lines)

    def replace_text(self, old: str, new: str) -> None:
        self.path.write_text(self.text.replace(old, new))

    @staticmethod
    def use_majprod(
        sql: str,
        old: str = "EDW.dbo.",
        new: str = "MAJESCOPROD.EDW.dbo.",
    ) -> str:
        return sql.replace(old, new)

    @property
    def start_val(self) -> str:
        env = "report_start"
        val = chkenv(env, need=False)
        if val:
            return f"'{val}'"

    @property
    def end_val(self) -> str:
        env = "report_end"
        val = chkenv(env, need=False)
        if val:
            return f"'{val}'"

    @property
    def start_text(self) -> str:
        return chkenv("report_start_text", need=False)

    @property
    def end_text(self) -> str:
        return chkenv("report_end_text", need=False)

    def get_sql(
        self,
        replace: list[tuple[str, str]] = None
    ) -> str:
        sql = self.text
        if isinstance(replace, tuple):
            sql = sql.replace(*replace)
        elif isinstance(replace, list):
            for tup in replace:
                sql = sql.replace(*tup)
        elif replace is not None:
            raise ValueError(
                f"{replace} must be tuple | list[tuple] but is {type(replace)}"
            )
        if self.start_text and self.start_val and not replace:
            sql = sql.replace(self.start_text, self.start_val)
        if self.end_text and self.end_val and not replace:
            sql = sql.replace(self.end_text, self.end_val)
        if chkenv("use_majprod", need=False, ifnull=False):
            sql = File.use_majprod(sql)
        return sql

    @cached_property
    def read_func(self) -> Callable:
        if self.isxlsx:
            from pandas import read_excel

            ret = partial(read_excel, self.path)
        elif self.iscsv:
            from pandas import read_csv

            ret = partial(read_csv, self.path)
        elif self.issql:
            from pandas import read_sql

            ret = read_sql
        elif self.isjson:
            from pandas import read_json

            ret = partial(read_json, self.text)
        elif self.istxt:
            return self.path.read_text
        else:
            raise TypeError(f"read func not loaded for {self.path.suffix}")
        return ret

    def get_df(
        self,
        engine: Engine = None,
        replace: tuple[str, str] = None,
        **kwargs,
    ) -> DataFrame:
        if self.issql and engine is None:
            raise ValueError("need engine to get df from db")
        elif not self.issql:
            return self.read_func(**kwargs)
        sql = self.get_sql(replace=replace)
        return self.read_func(sql, engine)

    def load_json(self) -> dict:
        if not self.isjson:
            raise TypeError("this method is reserved for json files")
        else:
            with open(self.path, "r") as file:
                json = load(file)
        if isinstance(json, dict):
            ret = json
        elif isinstance(json, str):
            ret = loads(json)
        else:
            raise TypeError("failed to correctly load json")
        return ret

    @classmethod
    def to_json(cls, _dict: dict, path: Path) -> object:
        json_str = dumps(_dict)
        with open(path, "w") as file:
            dump(json_str, file)
        return cls(path=path)

    @classmethod
    def from_df(cls, df: DataFrame, path: Path):
        funcname = f"to_{path.suffix}"
        func = getattr(df, funcname)
        func(path)
        return cls(path=path)

    @cached_property
    def comment_chars(self):
        if self.issql:
            line = "--"
            multi = ["/*", """*/"""]
        elif self.ispy:
            line = """#"""
            multi = ['''"""''', '''"""''']
        elif self.isps1:
            line = """#"""
            multi = ["""<#""", """#>"""]
        else:
            line = ""
            multi = ["", ""]
        return {"line": line, "multi": multi}

    @cached_property
    def comment_line_chars(self):
        return self.comment_chars["line"]

    @cached_property
    def comment_lines_chars(self):
        return self.comment_chars["multi"]

    @staticmethod
    def mk_header_lines(
        created_by: str,
        created_on: str,
        comment_lines_chars: list[str],
    ) -> str:
        lc, rc = comment_lines_chars
        return [
            lc,
            f"\tCreated By: {created_by}",
            f"\tCreated On: {created_on}\n",
            "\tModified By:",
            "\tModified On:\n",
            rc,
        ]

    def get_header_lines(self):
        return File.mk_header_lines(
            self.user, self.created_strfdatetime, self.comment_lines_chars
        )

    @property
    def hasheader(self):
        ssmspart = "command from SSMS"
        leftchar = self.comment_lines_chars[0]
        firstline = self.text.split("\n")[0]
        return leftchar in firstline and ssmspart not in firstline

    def add_header(self):
        if not self.isheadertype:
            info(f"{self.path} not in header types")
        elif self.hasheader:
            info(f"{self.path} already has header")
        else:
            self.prepend_lines(self.get_header_lines())
            info(f"header written to {self.path}")

    def get_alir_date_from_name(self):
        if not self.name.startswith("cvgver"):
            raise ValueError("this doesn't seem like an alir output file")
        elif not self.istxt:
            raise TypeError("output files should be text files")
        datestr = self.name.split(".")[1]
        return datetime(datestr[:4], datestr[4:6], datestr[6:8])

    def copy_to(self, destination: Path, overwrite: bool = False):
        destexists = destination.exists()
        if destexists and not overwrite:
            raise FileExistsError(
                f"{destination} exists - if intentional, set overwrite=True"
            )
        elif destexists:
            destination.unlink()
        destination.write_bytes(self.path.read_bytes())
        return File.from_path(destination)


@dataclass
class Directory(SystemObject):
    name: str = field(default=None)
    path: Path = field(default=None, repr=False)
    test: bool = field(default=False)
    levels: int = field(default=1, repr=False)

    @property
    def contents(self) -> list[Path]:
        return list(self.path.iterdir())

    @property
    def dirlist(self) -> list[SystemObject]:
        return [Directory.from_path(x) for x in self.contents if x.is_dir()]

    @property
    def filelist(self) -> list[File]:
        return [File.from_path(x) for x in self.contents if x.is_file()]

    @property
    def objlist(self) -> list[SystemObject]:
        return self.dirlist + self.filelist

    @staticmethod
    def tree_item(obj: SystemObject) -> dict[str:SystemObject]:
        return obj if obj.path.is_file() else obj.tree

    @property
    def tree(self):
        return {
            self.name: {
                obj.name: Directory.tree_item(obj) for obj in self.objlist
            }
        }

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name})"

    def get_type_filelist(self, type_: str) -> list[File]:
        return [
            x for x in self.filelist
            if x.istype(type_) and isinstance(x, File)
        ]

    @property
    def sql_filelist(self) -> list[File]:
        return self.get_type_filelist("sql")

    @property
    def nfiles(self) -> int:
        return len(self.filelist)

    @property
    def ndirs(self) -> int:
        return len(self.dirlist)

    @property
    def hasnofiles(self) -> bool:
        return self.nfiles == 0

    @property
    def hasnodirs(self) -> bool:
        return self.ndirs == 0

    @property
    def dirswithfiles(self):
        d = self.dirlist
        return [x for x in d if not x.hasnofiles]

    @property
    def isempty(self) -> bool:
        return self.hasnodirs and self.hasnofiles

    @property
    def nchildfiles(self) -> int:
        dirfiles = sum([x.nchildfiles for x in self.dirlist])
        return dirfiles + self.nfiles

    @property
    def nchilddirs(self) -> int:
        dirdirs = sum([x.nchilddirs for x in self.dirlist])
        return dirdirs + self.ndirs

    @property
    def allchildfiles(self) -> list[File]:
        return self.filelist + link([
            x.allchildfiles for x in self.dirlist
        ])

    @property
    def allchilddirs(self) -> list[SystemObject]:
        return self.dirlist + link([
            x.allchilddirs for x in self.dirlist
        ])

    @property
    def childdirswithfiles(self):
        return [x for x in self.allchilddirs if not x.hasnofiles]

    def get_latest_file(self):
        """gets last produced file object"""
        try:
            dates = [x.modified_datetime for x in self.filelist]
            idx = dates.index(max(dates))
        except PermissionError("can't get last mod time"):
            names = [x.name for x in self.filelist]
            idx = names.index(max(names))
        return self.filelist[idx]

    def rm_files(self) -> None:
        for file in self.filelist:
            file.rm()

    def teardown(self, warn: bool = True) -> None:
        if warn:
            msg = """
            this is a dangerous method
            only set warn=False if you really want
            to destroy this
        """
            raise ValueError(msg)
        for d in self.dirlist:
            d.teardown(warn=warn)
            d.rm_files()
        self.rm_files()
        self.path.rmdir()

    def apply_to_files(
        self,
        method,
        *args,
        **kwargs,
    ) -> list[File]:
        eval_method_list(
            method,
            self.filelist,
            *args,
            **kwargs,
        )

    def add_header_to_files(
        self,
        method: str = "add_header",
        cascade: bool = True,
    ) -> None:
        self.apply_to_files(method)
        if cascade:
            for dir in self.dirlist:
                dir.add_header_to_files()

    @property
    def randfile(self):
        return choice(self.filelist)

    @property
    def randdir(self):
        return choice(self.dirlist)

    @property
    def randchildfile(self):
        return choice(self.allchildfiles)

    @property
    def randchilddir(self):
        return choice(self.allchilddirs)

    @property
    def randdirwithfiles(self):
        return choice(self.dirswithfiles)

    @property
    def maxtreedepth(self):
        if self.isempty:
            ret = self.nparents
        else:
            maxdirp = max([x.nparents for x in self.allchilddirs])
            maxfilep = max([x.nparents for x in self.allchildfiles])
            ret = max(maxdirp, maxfilep)
        return 1 + ret

    @property
    def maxchilddepth(self):
        return self.maxtreedepth - self.nparents

    def __div__(self, other: SystemObject | str):
        oisfile = isinstance(other, File)
        oisdir = isinstance(other, Directory)
        oispath = isinstance(other, Path)
        fdp = (oisfile or oisdir or oispath)
        oisstr = isinstance(other, str)
        oisnum = (isinstance(other, int) or isinstance(other, float))

        if fdp:
            path, name = self.path, other.name
        elif oisstr:
            path, name = self.path, other
        elif oisnum:
            path, name = self.path, str(other)
        else:
            raise ValueError("invalid type")

        self.path = path / name
        self.set_name()

        if not self.exists:
            return SystemObject(
                path=self.path,
                name=self.name,
            )
        elif self.isfile:
            return File(
                path=self.path,
                name=self.name,
            )
        elif self.isdir:
            return Directory(
                path=self.path,
                name=self.name,
            )
        else:
            raise ValueError("invalid path")

    def __truediv__(self, other: SystemObject | str):
        return self.__div__(other)

    def __floordiv__(self, other: SystemObject | str):
        return self.__div__(other)


def update_file_version(
    version: str,
    path: Path,
) -> None:
    file = File.from_path(path)
    newline = f"version = {version}"
    newlines = [
        newline if x.startswith("version") else x
        for x in file.lines
    ]
    file.write_lines(newlines)

"""
This module provides a collection of utility functions and classes for file and directory operations,
including manipulation, searching, and database interactions.

Key functionalities include:
- `figsave`: Save matplotlib figures to a specified directory.
- `eval_parents`, `path_search`: Evaluate and search for file paths based on inclusion and exclusion criteria.
- `copy_csv_str`: Generate a PostgreSQL COPY statement for a given CSV file.
- `SystemObject`: A base class for representing files and directories with utility methods for checking file types,
  retrieving system information, and more.
- `File`: A subclass of SystemObject specialized for file operations like renaming, deleting, reading content,
  and manipulating various file formats (CSV, SQL, JSON, etc.).
- `Directory`: A subclass of SystemObject for directory-specific operations, including retrieving directory contents,
  and applying operations to files within the directory.
- Utility functions for applying methods to lists of SystemObject instances and updating file versions.

The module leverages external libraries such as `pandas` for DataFrame operations, `pathlib` for path manipulations,
and `sqlalchemy` for database interactions. It is designed to facilitate common file and directory operations
in Python scripting and data processing tasks.

Dependencies: collections, dataclasses, datetime, functools, json, logging, os, pathlib, random, typing, matplotlib, pandas, sqlalchemy
"""
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import cached_property, partial
from json import JSONDecodeError, dumps, load, loads
from logging import info
from os import stat_result
from pathlib import Path
from random import choice
from typing import Any

from matplotlib.pyplot import savefig
from pandas import DataFrame
from sqlalchemy import Engine

from alexlib.constants import DATE_FORMAT, DATETIME_FORMAT
from alexlib.core import chkenv, sha256sum, to_clipboard
from alexlib.iters import link


def figsave(
    name: str,
    dirpath: Path,
    fmt: str = "png",
    **kwargs,  # use bb_inches=tight if cutoff
) -> bool:
    """save a figure to a path"""
    path = dirpath / f"{name}.{fmt}"
    savefig(path, format=fmt, **kwargs)
    return path.exists()


def eval_parents(path: Path, include: set, exclude: set) -> bool:
    """evaluates whether a path is included or excluded"""
    if isinstance(exclude, str):
        exclude = {exclude}
    elif exclude is None:
        exclude = set()
    else:
        exclude = set(exclude)
    if isinstance(include, str):
        include = {include}
    elif include is None:
        include = set()
    else:
        include = set(include)
    parts = set(path.parts)
    chk_include = not include or include.issubset(parts)
    chk_exclude = not exclude or not exclude.intersection(parts)
    return chk_include and chk_exclude


# pylint: disable=too-many-arguments
def path_search(
    pattern: str,
    start_path: Path = Path(__file__).parent,
    listok: bool = False,
    include: list[str] = None,
    exclude: list[str] = None,
    max_ascends: int = 8,
) -> Path | list[Path]:
    """searches for a path by pattern, ascending up to max_ascends times"""
    n_ascends, search_path = 0, start_path
    while n_ascends <= max_ascends:
        try:
            found_paths = [
                x
                for x in search_path.rglob(pattern)
                if eval_parents(x, include, exclude)
            ]
            if (len_ := len(found_paths)) == 1:
                ret = found_paths[0]
            elif len_ > 1 and listok:
                ret = found_paths
            elif len_ > 1:
                raise ValueError(f"multiple {pattern} found in {search_path}")
            else:
                raise FileNotFoundError(f"no {pattern} found in {search_path}")
            return ret
        except FileNotFoundError:
            search_path = search_path.parent
            n_ascends += 1
    raise FileNotFoundError(f"no {pattern} found in {start_path}")


def copy_csv_str(table_name: str, csv_path: Path) -> str:
    """generates a copy statement for a csv file"""
    return f"""COPY {table_name} FROM '{csv_path}'
    DELIMITER ','
    CSV HEADER
    """


@dataclass
class SystemObject:
    """base class for File and Directory"""

    name: str = field(default=None)
    path: Path = field(default=None)
    include: list[str] = field(default_factory=list, repr=False)
    exclude: list[str] = field(default_factory=list, repr=False)
    max_ascends: int = field(repr=False, default=8)

    @property
    def isfile(self) -> bool:
        """checks if path is a file"""
        return self.path.is_file()

    @property
    def isdir(self) -> bool:
        """checks if path is a directory"""
        return self.path.is_dir()

    @cached_property
    def sysobj_names(self) -> list[str]:
        """names of system object classes"""
        return ["Directory", "File", "SystemObject"]

    @property
    def haspath(self) -> bool:
        """checks if path is set"""
        return self.path is not None

    @property
    def hasname(self) -> bool:
        """checks if name is set"""
        return self.name is not None

    @property
    def user(self) -> str:
        """gets username from environment variable"""
        return chkenv("USERNAME", need=False)

    @property
    def hasuser(self) -> bool:
        """checks if user is set"""
        return self.user is not None

    @staticmethod
    def add_path_cond(cur_list: list[str], toadd: str | list[str]) -> list[str]:
        """adds a path condition to a list of path conditions"""
        if isinstance(toadd, str):
            toadd = [toadd]
        elif not toadd:
            toadd = []
        if isinstance(cur_list, str):
            cur_list = [cur_list]
        return cur_list + toadd

    # pylint: disable=no-member
    def get_path(
        self,
        include: list[str] | str = None,
        exclude: list[str] | str = None,
        start_path: Path = Path(__file__).parent,
    ) -> Path:
        """gets path from name or path"""
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
                max_ascends=self.max_ascends,
            )
        else:
            n, p = self.name, self.path
            raise ValueError(f"need name cur={n} or path cur={p}")
        return ret

    def set_path(self):
        """sets path from name or path"""
        self.path = self.get_path(include=self.include)

    def get_name(self):
        """gets name from path or name"""
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

    def set_name(self) -> None:
        """sets name from path or name"""
        self.name = self.get_name()

    def __post_init__(self) -> None:
        """sets path and name"""
        self.set_path()
        if not isinstance(self.path, Path):
            raise TypeError(f"{self.path} is not Path")
        self.set_name()
        if not isinstance(self.name, str):
            raise TypeError(f"{self.name} is not str")

    @property
    def parent(self) -> Path:
        """gets parent path"""
        return self.path.parent

    @property
    def parents(self) -> list[Path]:
        """gets parent paths"""
        return self.path.parents

    @property
    def parts(self) -> list[Path]:
        """gets path parts"""
        return self.path.parts

    def get_parent(self, name: str) -> Path:
        """gets parent path by name"""
        if name not in self.parts:
            raise ValueError(f"{name} not in parents[{self.parts}]")
        return [x for x in self.parents if x.name == name][-1]

    @property
    def nparents(self) -> int:
        """gets number of parents"""
        return len(self.parents)

    @property
    def stat(self) -> stat_result:
        """gets path stat"""
        return self.path.stat()

    @property
    def uid(self) -> int:
        """gets path uid"""
        return self.stat.st_uid

    @property
    def gid(self) -> int:
        """gets path gid"""
        return self.stat.st_gid

    @property
    def uidiszero(self) -> bool:
        """checks if uid is zero"""
        return self.uid == 0

    @property
    def gidiszero(self) -> bool:
        """checks if gid is zero"""
        return self.gid == 0

    @property
    def owner(self) -> str:
        """gets path owner"""
        if not (self.gidiszero and self.uidiszero):
            ret = f"{self.gid}:{self.uid}"
        elif not self.uidiszero:
            ret = self.uid
        else:
            ret = self.user
        return ret

    @staticmethod
    def get_path_attr(path: Path, attr: str) -> Any:
        """gets path attribute"""
        try:
            ret = getattr(path.stat(), attr)
        except AttributeError:
            ret = getattr(path, attr)
        return ret

    @property
    def modified_timestamp(self) -> float:
        """gets path modified timestamp"""
        return self.stat.st_mtime

    @property
    def created_timestamp(self) -> float:
        """gets path created timestamp"""
        return self.stat.st_ctime

    @property
    def modified_datetime(self) -> datetime:
        """gets path modified datetime"""
        return datetime.fromtimestamp(self.modified_timestamp)

    @property
    def created_datetime(self) -> datetime:
        """gets path created datetime"""
        return datetime.fromtimestamp(self.created_timestamp)

    @property
    def modified_strfdate(self) -> str:
        """gets path modified strfdate"""
        return self.modified_datetime.strftime(DATE_FORMAT)

    @property
    def created_strfdate(self) -> str:
        """gets path created strfdate"""
        return self.created_datetime.strftime(DATE_FORMAT)

    @property
    def modified_strfdatetime(self) -> str:
        """gets path modified strfdatetime"""
        return self.modified_datetime.strftime(DATETIME_FORMAT)

    @property
    def created_strfdatetime(self) -> str:
        """gets path created strfdatetime"""
        return self.created_datetime.strftime(DATETIME_FORMAT)

    @property
    def modified_delta(self) -> timedelta:
        """gets path modified delta"""
        return datetime.now() - self.modified_datetime

    @property
    def created_delta(self) -> timedelta:
        """gets path created delta"""
        return datetime.now() - self.created_datetime

    def is_new_enough(
        self,
        min_delta: timedelta,
    ) -> bool:
        """checks if path is new enough"""
        return self.created_delta < min_delta

    @cached_property
    def clsname(self) -> str:
        """gets class name"""
        return self.__class__.__name__

    @property
    def exists(self) -> bool:
        """checks if path exists"""
        return self.path.exists() if self.haspath else False

    def chk_exists(self) -> None:
        """checks if path exists"""
        if not self.exists:
            raise FileNotFoundError(f"no {self.clsname} @ {self.path}")

    @classmethod
    def from_path(cls, path: Path, **kwargs):
        """creates system object from path"""
        if isinstance(path, str):
            path = Path(path)
        return cls(path=path, **kwargs)

    @classmethod
    def from_name(cls, name: str, **kwargs):
        """creates system object from name"""
        return cls(name=name, **kwargs)

    def eval_method(
        self,
        method: str,
        *args,
        **kwargs,
    ) -> Any:
        """evaluates a method"""
        func = getattr(self, method)
        return func(*args, **kwargs)

    @classmethod
    def find(cls, name: str, **kwargs):
        """finds system object by name"""
        return cls(path=path_search(name, **kwargs))


def eval_method_list(
    method: str, lst: list[SystemObject], *args, **kwargs
) -> list[Any]:
    """evaluates a method on a list of system objects"""
    return [x.eval_method(method, *args, **kwargs) for x in lst]


@dataclass
class File(SystemObject):
    """class for files"""

    name: str = field(default=None)
    path: Path = field(default=None, repr=False)
    encrypted: bool = field(default=False, repr=False)

    @property
    def sha256(self) -> str:
        """gets file hash"""
        return sha256sum(self.path)

    def __repr__(self) -> str:
        """gets file representation"""
        return f"{self.__class__.__name__}({self.name})"

    def rm(self) -> None:
        """removes file"""
        self.path.unlink()

    def rename(self, name: str, overwrite: bool = False) -> None:
        """renames file"""
        newpath = self.path.parent / name
        if overwrite and newpath.exists():
            newpath.unlink()
        self.path.rename(self.path.parent / name)
        self.path = newpath
        self.set_name()

    def istype(self, suffix: str) -> bool:
        """checks if file is of type"""
        low = self.path.suffix.lower()
        other = suffix.strip(".").lower()
        return low.endswith(other)

    @property
    def isxlsx(self) -> bool:
        """checks if file is xlsx"""
        return self.istype(".xlsx")

    @property
    def issql(self) -> bool:
        """checks if file is sql"""
        return self.istype(".sql")

    @property
    def iscsv(self) -> bool:
        """checks if file is csv"""
        return self.istype(".csv")

    @property
    def isjson(self) -> bool:
        """checks if file is json"""
        return self.istype(".json")

    @property
    def istxt(self) -> bool:
        """checks if file is txt"""
        return self.istype(".txt")

    @property
    def ispy(self) -> bool:
        """checks if file is py"""
        return self.istype(".py")

    @property
    def isipynb(self) -> bool:
        """checks if file is ipynb"""
        return self.istype(".ipynb")

    # pylint: disable=unspecified-encoding
    @property
    def text(self) -> str:
        """gets file text"""
        try:
            return self.path.read_text()
        except UnicodeDecodeError:
            return self.path.read_text(encoding="utf8")

    def text_to_clipboard(self) -> None:
        """copies file text to clipboard"""
        return to_clipboard(self.text)

    @property
    def lines(self) -> list[str]:
        """gets file lines"""
        return self.text.split("\n")

    @property
    def line_counter(self) -> Counter:
        """gets file line counter"""
        return Counter(self.lines)

    @property
    def nlines(self) -> int:
        """gets number of lines"""
        return len(self.lines)

    @property
    def line_indexes(self) -> dict[str : list[int]]:
        """gets line indexes"""
        lines, rng = self.lines, range(self.nlines)
        return {
            line: [i + 1 for i in rng if line == lines[i]]
            for line in self.line_counter.keys()
        }

    @property
    def line_repeats(self) -> dict[str : list[int]]:
        """gets line repeats"""
        return {
            k: v for k, v in self.line_indexes.items() if (len(v) > 1 and len(k) > 0)
        }

    @property
    def line_lengths(self) -> list[int]:
        """gets line lengths"""
        return [len(x) for x in self.lines]

    def write_lines(self, lines: list[str]) -> None:
        """writes lines to file"""
        self.path.write_text("\n".join(lines))

    def append_lines(self, lines: list[str]) -> None:
        """appends lines to file"""
        self.write_lines(self.lines + lines)

    def prepend_lines(self, lines: list[str]) -> None:
        """prepends lines to file"""
        self.write_lines(lines + self.lines)

    def replace_text(self, old: str, new: str) -> None:
        """replaces text in file"""
        self.path.write_text(self.text.replace(old, new))

    @property
    def start_val(self) -> str:
        """gets start val"""
        env = "report_start"
        val = chkenv(env, need=False)
        return f"'{val}'"

    @property
    def end_val(self) -> str:
        """gets end val"""
        env = "report_end"
        val = chkenv(env, need=False)
        return f"'{val}'"

    @property
    def start_text(self) -> str:
        """gets start text"""
        return chkenv("report_start_text", need=False)

    @property
    def end_text(self) -> str:
        """gets end text"""
        return chkenv("report_end_text", need=False)

    def get_sql(self, replace: list[tuple[str, str]] = None) -> str:
        """gets sql from file"""
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
        return sql

    @cached_property
    def read_func(self) -> Callable:
        """gets read function"""
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
        """gets dataframe from file"""
        if self.issql and engine is None:
            raise ValueError("need engine to get df from db")
        if not self.issql and kwargs:
            ret = self.read_func(**kwargs)
        elif not self.issql:
            ret = self.read_func()
        else:
            sql = self.get_sql(replace=replace)
            ret = self.read_func(sql, engine)
        return ret

    def load_json(self) -> dict:
        """loads json from file"""
        if not self.isjson:
            raise TypeError("this method is reserved for json files")
        try:
            ret = loads(self.text)
        except JSONDecodeError:
            with self.path.open() as f:
                ret = load(f)
        return ret

    @classmethod
    def to_json(cls, _dict: dict, path: Path) -> object:
        """writes json to file"""
        json_str = dumps(_dict)
        path.write_text(json_str)
        return cls(path=path)

    @classmethod
    def from_df(cls, df: DataFrame, path: Path):
        """writes dataframe to file"""
        funcname = f"to_{path.suffix}"
        func = getattr(df, funcname)
        func(path)
        return cls(path=path)

    @cached_property
    def comment_chars(self):
        """gets comment chars"""
        if self.issql:
            line = "--"
            multi = ["/*", """*/"""]
        elif self.ispy:
            line = """#"""
            multi = ['''"""''', '''"""''']
        else:
            line = ""
            multi = ["", ""]
        return {"line": line, "multi": multi}

    @cached_property
    def comment_line_chars(self):
        """gets comment line chars"""
        return self.comment_chars["line"]

    @cached_property
    def comment_lines_chars(self):
        """gets comment lines chars"""
        return self.comment_chars["multi"]

    @staticmethod
    def mk_header_lines(
        created_by: str,
        created_on: str,
        comment_lines_chars: list[str],
    ) -> str:
        """makes header lines"""
        lc, rc = comment_lines_chars
        return [
            lc,
            f"\tCreated By: {created_by}",
            f"\tCreated On: {created_on}\n",
            "\tModified By:",
            "\tModified On:\n",
            rc,
        ]

    def get_header_lines(self) -> list[str]:
        """gets header lines"""
        return File.mk_header_lines(
            self.user, self.created_strfdatetime, self.comment_lines_chars
        )

    @property
    def hasheader(self) -> bool:
        """checks if file has header"""
        ssmspart = "command from SSMS"
        leftchar = self.comment_lines_chars[0]
        firstline = self.text.split("\n")[0]
        return leftchar in firstline and ssmspart not in firstline

    def add_header(self) -> None:
        """adds header to file"""
        if self.hasheader:
            info(f"{self.path} already has header")
        else:
            self.prepend_lines(self.get_header_lines())
            info(f"header written to {self.path}")

    def copy_to(self, destination: Path, overwrite: bool = False) -> "File":
        """copies file to destination"""
        destexists = destination.exists()
        if destexists and not overwrite:
            raise FileExistsError(
                f"{destination} exists - if intentional, set overwrite=True"
            )
        if destexists:
            destination.unlink()
        destination.write_bytes(self.path.read_bytes())
        return File.from_path(destination)

    @classmethod
    def df_to_file(cls, df: DataFrame, path: Path) -> "File":
        """writes dataframe to file"""
        funcname = f"to_{path.suffix}"
        func = getattr(df, funcname)
        func(path)
        return cls(path=path)


# pylint: disable=too-many-public-methods
@dataclass
class Directory(SystemObject):
    """class for directories"""

    name: str = field(default=None)
    path: Path = field(default=None, repr=False)
    test: bool = field(default=False)
    levels: int = field(default=1, repr=False)

    @property
    def contents(self) -> list[Path]:
        """gets directory contents"""
        return list(self.path.iterdir())

    @property
    def dirlist(self) -> list[SystemObject]:
        """gets directory list"""
        return [Directory.from_path(x) for x in self.contents if x.is_dir()]

    @property
    def filelist(self) -> list[File]:
        """gets file list"""
        return [File.from_path(x) for x in self.contents if x.is_file()]

    @property
    def objlist(self) -> list[SystemObject]:
        """gets object list"""
        return self.dirlist + self.filelist

    @staticmethod
    def tree_item(obj: SystemObject) -> dict[str:SystemObject]:
        """gets tree item"""
        return obj if obj.path.is_file() else obj.tree

    @property
    def tree(self) -> dict[str:SystemObject]:
        """gets tree"""
        return {self.name: {obj.name: Directory.tree_item(obj) for obj in self.objlist}}

    def __repr__(self) -> str:
        """gets directory representation"""
        return f"{self.__class__.__name__}({self.name})"

    def get_type_filelist(self, type_: str) -> list[File]:
        """gets file list by type"""
        return [x for x in self.filelist if x.istype(type_) and isinstance(x, File)]

    @property
    def csv_filelist(self) -> list[File]:
        """gets csv file list"""
        return self.get_type_filelist("csv")

    @property
    def sql_filelist(self) -> list[File]:
        """gets sql file list"""
        return self.get_type_filelist("sql")

    @property
    def nfiles(self) -> int:
        """gets number of files"""
        return len(self.filelist)

    @property
    def ndirs(self) -> int:
        """gets number of directories"""
        return len(self.dirlist)

    @property
    def hasnofiles(self) -> bool:
        """checks if directory has no files"""
        return self.nfiles == 0

    @property
    def hasnodirs(self) -> bool:
        """checks if directory has no directories"""
        return self.ndirs == 0

    @property
    def dirswithfiles(self) -> list[SystemObject]:
        """gets directories with files"""
        d = self.dirlist
        return [x for x in d if not x.hasnofiles]

    @property
    def isempty(self) -> bool:
        """checks if directory is empty"""
        return self.hasnodirs and self.hasnofiles

    @property
    def nchildfiles(self) -> int:
        """gets number of child files"""
        dirfiles = sum(x.nchildfiles for x in self.dirlist)
        return dirfiles + self.nfiles

    @property
    def nchilddirs(self) -> int:
        """gets number of child directories"""
        dirdirs = sum(x.nchilddirs for x in self.dirlist)
        return dirdirs + self.ndirs

    @property
    def allchildfiles(self) -> list[File]:
        """gets all child files"""
        return self.filelist + link([x.allchildfiles for x in self.dirlist])

    @property
    def allchilddirs(self) -> list[SystemObject]:
        """gets all child directories"""
        return self.dirlist + link([x.allchilddirs for x in self.dirlist])

    @property
    def childdirswithfiles(self) -> list[SystemObject]:
        """gets child directories with files"""
        return [x for x in self.allchilddirs if not x.hasnofiles]

    def get_latest_file(self) -> File:
        """gets last produced file object"""
        try:
            dates = [x.modified_datetime for x in self.filelist]
            idx = dates.index(max(dates))
        except PermissionError("can't get last mod time"):
            names = [x.name for x in self.filelist]
            idx = names.index(max(names))
        return self.filelist[idx]

    def rm_files(self) -> None:
        """removes files"""
        for file in self.filelist:
            file.rm()

    def teardown(self, warn: bool = True) -> None:
        """tears down directory"""
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
        """applies method to files"""
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
        """adds header to files"""
        self.apply_to_files(method)
        if cascade:
            for d in self.dirlist:
                d.add_header_to_files()

    @property
    def randfile(self) -> File:
        """gets random file"""
        return choice(self.filelist)

    @property
    def randdir(self) -> SystemObject:
        """gets random directory"""
        return choice(self.dirlist)

    @property
    def randchildfile(self) -> File:
        """gets random child file"""
        return choice(self.allchildfiles)

    @property
    def randchilddir(self) -> SystemObject:
        """gets random child directory"""
        return choice(self.allchilddirs)

    @property
    def randdirwithfiles(self) -> SystemObject:
        """gets random directory with files"""
        return choice(self.dirswithfiles)

    @property
    def maxtreedepth(self) -> int:
        """gets max tree depth"""
        if self.isempty:
            ret = self.nparents
        else:
            maxdirp = max(x.nparents for x in self.allchilddirs)
            maxfilep = max(x.nparents for x in self.allchildfiles)
            ret = max(maxdirp, maxfilep)
        return 1 + ret

    @property
    def maxchilddepth(self) -> int:
        """gets max child depth"""
        return self.maxtreedepth - self.nparents

    def __div__(self, other: SystemObject | str) -> SystemObject:
        """divides directory by other"""
        oisfile = isinstance(other, File)
        oisdir = isinstance(other, Directory)
        oispath = isinstance(other, Path)
        fdp = oisfile or oisdir or oispath
        oisstr = isinstance(other, str)
        oisnum = isinstance(other, (float, int))
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
            ret = SystemObject(
                path=self.path,
                name=self.name,
            )
        elif self.isfile:
            ret = File(
                path=self.path,
                name=self.name,
            )
        elif self.isdir:
            ret = Directory(
                path=self.path,
                name=self.name,
            )
        else:
            raise ValueError("invalid path")
        return ret

    def __truediv__(self, other: SystemObject | str) -> SystemObject:
        """divides directory by other"""
        return self.__div__(other)

    def __floordiv__(self, other: SystemObject | str) -> SystemObject:
        """divides directory by other"""
        return self.__div__(other)


def update_file_version(
    version: str,
    path: Path,
) -> None:
    """updates file version"""
    file = File.from_path(path)
    newline = f"version = {version}"
    newlines = [newline if x.startswith("version") else x for x in file.lines]
    file.write_lines(newlines)

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
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import cached_property
from itertools import chain
from os import stat_result
from pathlib import Path
from random import choice

from pandas import DataFrame

from alexlib.constants import DATE_FORMAT, DATETIME_FORMAT
from alexlib.core import (
    flatten_dict,
    path_istype,
    show_dict,
    to_clipboard,
)
from alexlib.files.utils import path_search, sha256sum

__sysobj_names__ = ("Directory", "File", "SystemObject")


@dataclass(frozen=True)
class SystemTimestamp:
    """class for system timestamps"""

    timestamp: float

    @property
    def datetime(self) -> datetime:
        """gets timestamp datetime"""
        return datetime.fromtimestamp(self.timestamp)

    @property
    def strfdate(self) -> str:
        """gets timestamp strfdate"""
        return self.datetime.strftime(DATE_FORMAT)

    @property
    def strfdatetime(self) -> str:
        """gets timestamp strfdatetime"""
        return self.datetime.strftime(DATETIME_FORMAT)

    @property
    def delta(self) -> timedelta:
        """gets timestamp delta"""
        return datetime.now() - self.datetime

    def is_new_enough(self, min_delta: timedelta) -> bool:
        """checks if timestamp is new enough"""
        if not isinstance(min_delta, timedelta):
            raise TypeError(f"{min_delta} is not a timedelta")
        return self.delta < min_delta

    def __repr__(self) -> str:
        """gets timestamp representation"""
        return f"{self.__class__.__name__}({self.strfdatetime})"

    def __str__(self) -> str:
        """gets timestamp string"""
        return self.strfdatetime

    @classmethod
    def from_stat_result(cls, stat: stat_result) -> "SystemTimestamp":
        """creates system timestamp from stat result"""
        raise NotImplementedError("Subclasses must implement this method")

    @classmethod
    def from_path(cls, path: Path) -> "SystemTimestamp":
        """creates system timestamp from path"""
        return cls.from_stat_result(path.stat())


@dataclass(frozen=True)
class CreatedTimestamp(SystemTimestamp):
    """class for created timestamps"""

    @classmethod
    def from_stat_result(cls, stat: stat_result) -> "CreatedTimestamp":
        """creates created timestamp from stat result"""
        return cls(stat.st_ctime)


@dataclass(frozen=True)
class ModifiedTimestamp(SystemTimestamp):
    """class for modified timestamps"""

    @classmethod
    def from_stat_result(cls, stat: stat_result) -> "ModifiedTimestamp":
        """creates modified timestamp from stat result"""
        return cls(stat.st_mtime)


@dataclass
class SystemObject:
    """base class for File and Directory"""

    path: Path

    @cached_property
    def isfile(self) -> bool:
        """checks if path is a file"""
        return self.path.is_file() or self.__class__.__name__ == "File"

    @cached_property
    def isdir(self) -> bool:
        """checks if path is a directory"""
        return self.path.is_dir() or self.__class__.__name__ == "Directory"

    @property
    def nparents(self) -> int:
        """gets number of parents"""
        return len(self.path.parents)

    @property
    def stat(self) -> stat_result:
        """gets path stat"""
        return self.path.stat()

    @property
    def size(self) -> int:
        """gets path size"""
        return self.stat.st_size

    @cached_property
    def modified_timestamp(self) -> ModifiedTimestamp:
        """gets path modified timestamp"""
        return ModifiedTimestamp.from_stat_result(self.stat)

    @cached_property
    def created_timestamp(self) -> CreatedTimestamp:
        """gets path created timestamp"""
        return CreatedTimestamp.from_stat_result(self.stat)

    @classmethod
    def from_path(cls, path: Path, **kwargs):
        """creates system object from path"""
        if isinstance(path, str):
            path = Path(path)
        return cls(path=path, **kwargs)

    @classmethod
    def from_name(cls, name: str, **kwargs):
        """creates system object from name"""
        return cls(path=path_search(name, **kwargs), **kwargs)

    @classmethod
    def from_parent(
        cls,
        filename: str,
        start_path: Path,
        notexistok: bool = False,
    ) -> "SystemObject":
        """returns file in parent directory"""
        if not isinstance(start_path, Path):
            start_path = Path(start_path)
        if not start_path.exists():
            raise FileNotFoundError(f"{start_path} does not exist")
        ret = [x for x in start_path.parents if (x / filename).exists()]
        if ret:
            return cls.from_path(ret[-1] / filename)
        if notexistok:
            return cls.from_path(start_path / filename)
        raise FileNotFoundError(f"{filename} not found in {start_path}")

    @classmethod
    def find(cls, name: str, **kwargs):
        """finds system object by name"""
        return cls(path=path_search(name, **kwargs))


@dataclass
class File(SystemObject):
    """class for files"""

    name: str = field(default=None)
    path: Path = field(default=None, repr=False)
    encrypted: bool = field(default=False, repr=False)

    def __hash__(self) -> str:
        """gets file hash"""
        return sha256sum(self.path)

    def __repr__(self) -> str:
        """gets file representation"""
        return f"{self.__class__.__name__}({self.name})"

    def rename(self, name: str, overwrite: bool = False) -> None:
        """renames file"""
        newpath = self.path.parent / name
        if overwrite and newpath.exists():
            newpath.unlink()
        self.path.rename(self.path.parent / name)

    def istype(self, suffix: str) -> bool:
        """checks if file is of type"""
        return path_istype(self.path, suffix)

    @property
    def text(self) -> str:
        """gets file text"""
        try:
            return self.path.read_text()
        except UnicodeDecodeError:
            return self.path.read_text(encoding="utf8")

    def clip(self) -> None:
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
    def dirlist(self) -> list["Directory"]:
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

    @property
    def _reprlist(self) -> list[SystemObject]:
        """returns list of contents for representation"""
        reprfiles = [repr(x) for x in self.filelist + self.dirswithoutfiles]
        dirswithfiles = [{repr(x): x._reprlist} for x in self.dirswithfiles]
        return reprfiles + dirswithfiles

    @staticmethod
    def _tree_item(obj: SystemObject) -> dict[str, SystemObject]:
        """returns item conditioned on system object type"""
        return obj if obj.path.is_file() else obj.tree

    @staticmethod
    def _show_tree_item(obj: SystemObject) -> dict[str, SystemObject]:
        """returns represention of item for console display"""
        return repr(obj) if obj.path.is_file() else obj._reprlist

    @staticmethod
    def _show_tree(top_repr: str, objlist: list[SystemObject]) -> None:
        """returns dict for pretty print representation of tree"""
        return {
            top_repr: {repr(obj): Directory._show_tree_item(obj) for obj in objlist}
        }

    @property
    def tree(self) -> dict[str:SystemObject]:
        """dictionary representation of directory"""
        return {
            self.name: {obj.name: Directory._tree_item(obj) for obj in self.objlist}
        }

    def show_tree(self, flat: bool = False) -> None:
        """pretty prints representation of tree"""
        d = Directory._show_tree(repr(self), self.objlist)
        if flat:
            d = flatten_dict(d)
        return show_dict(d)

    def __repr__(self) -> str:
        """gets directory representation"""
        return f"{self.__class__.__name__}({self.name})"

    @staticmethod
    def _get_type_filelist(
        type_: str,
        filelist: list[File],
    ) -> list[File]:
        """gets file list by type"""
        return [x for x in filelist if x.istype(type_) and isinstance(x, File)]

    def get_type_filelist(
        self,
        type_: str,
        allchildren: bool = False,
    ) -> list[File]:
        """gets file list by type"""
        filelist = self.allchildfiles if allchildren else self.filelist
        return Directory._get_type_filelist(type_, filelist)

    @property
    def csv_filelist(self) -> list[File]:
        """gets csv file list"""
        return self.get_type_filelist("csv", allchildren=True)

    @property
    def sql_filelist(self) -> list[File]:
        """gets sql file list"""
        return self.get_type_filelist("sql", allchildren=True)

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
    def dirswithoutfiles(self) -> list["Directory"]:
        """gets directories with files"""
        return [x for x in self.dirlist if x.hasnofiles]

    @property
    def dirswithfiles(self) -> list["Directory"]:
        """gets directories with files"""
        return [x for x in self.dirlist if not x.hasnofiles]

    @property
    def isempty(self) -> bool:
        """checks if directory is empty"""
        return len(self.contents) == 0

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
        return self.filelist + list(
            chain.from_iterable([x.allchildfiles for x in self.dirlist])
        )

    @property
    def size(self) -> int:
        """gets directory size"""
        return sum(x.size for x in self.allchildfiles)

    @property
    def allchilddirs(self) -> list[SystemObject]:
        """gets all child directories"""
        return self.dirlist + list(
            chain.from_iterable([x.allchilddirs for x in self.dirlist])
        )

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
            maxdirp = (
                max(x.nparents for x in self.allchilddirs) if self.allchilddirs else 0
            )
            maxfilep = (
                max(x.nparents for x in self.allchildfiles) if self.allchildfiles else 0
            )
            ret = max(maxdirp, maxfilep)
        return 1 + ret

    @property
    def maxchilddepth(self) -> int:
        """gets max child depth"""
        return self.maxtreedepth - self.nparents

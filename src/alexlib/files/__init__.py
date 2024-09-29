from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import cached_property
from itertools import chain
from logging import INFO, basicConfig
from os import environ, stat_result
from pathlib import Path
from random import choice

from pandas import DataFrame

from alexlib.constants import (
    DATETIME_FORMAT,
    DOTENV_PATH,
    LOG_FORMAT,
    LOG_PATH,
    PROJECT_PATH,
)
from alexlib.core import chktype, flatten_dict, path_istype, show_dict, to_clipboard
from alexlib.files.sizes import FileSize
from alexlib.files.times import CreatedTimestamp, ModifiedTimestamp
from alexlib.files.utils import (
    is_dotenv,
    is_json,
    path_search,
    read_dotenv,
    read_json,
    read_toml,
    write_json,
)

__sysobj_names__ = ("Directory", "File", "SystemObject")


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

    @cached_property
    def size(self) -> FileSize:
        """gets path size"""
        return FileSize(self.stat.st_size)

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
    def from_parent(
        cls,
        filename: str,
        start_path: Path,
        notexistok: bool = False,
    ) -> "SystemObject":
        """returns file in parent directory"""
        chktype(start_path, Path, mustexist=True)
        ret = [x for x in start_path.parents if (x / filename).exists()]
        if ret:
            return cls.from_path(ret[-1] / filename)
        if notexistok:
            return cls.from_path(start_path / filename)
        raise FileNotFoundError(f"{filename} not found in {start_path}")

    @classmethod
    def find(
        cls,
        pattern: str,
        start_path: Path = PROJECT_PATH,
        include: list[str] = None,
        exclude: list[str] = None,
        max_ascends: int = 5,
    ) -> "SystemObject":
        """finds system object by name"""
        return cls(
            path=path_search(
                pattern,
                start_path=start_path,
                include=include,
                exclude=exclude,
                max_ascends=max_ascends,
            )
        )


@dataclass
class File(SystemObject):
    """class for files"""

    name: str = field(default=None)
    path: Path = field(default=None, repr=False)
    encrypted: bool = field(default=False, repr=False)

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

    @cached_property
    def size(self) -> FileSize:
        """gets directory size"""
        return FileSize(sum(x.size for x in self.allchildfiles))

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
        if self.hasnofiles:
            raise FileNotFoundError("no files in directory")
        files = self.filelist
        idx = files.index(max(files, key=lambda x: x.modified_timestamp.timestamp))
        return files[idx]

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
            (f.path.unlink() for f in d.filelist)
        (f.path.unlink() for f in self.filelist)
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


@dataclass
class JsonFile(File):
    """class for json files"""

    read: Callable = field(default=read_json, repr=False)


@dataclass
class TomlFile(File):
    """class for json files"""

    read: Callable = field(default=read_toml, repr=False)


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


@dataclass
class DotenvFile(ConfigFile):
    """A class to handle dotenv files"""

    name: str = field(default=".env")
    path: Path = field(default=DOTENV_PATH)

    def get_envdict(self) -> dict:
        return read_dotenv(self.path)


@dataclass
class SettingsFile(ConfigFile, JsonFile):
    """A class to handle settings files"""

    name: str = field(default="settings.json")
    path: Path = field(default=PROJECT_PATH / "settings.json")

    def get_envdict(self) -> dict[str, str]:
        """Returns the environment variables from the settings file"""
        flat_dict = flatten_dict(read_json(self.path))
        return flat_dict

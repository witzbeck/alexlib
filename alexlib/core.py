"""
This module provides a collection of utility functions for various tasks such as data type checking,
environment variable handling, JSON operations, and working with file systems. It includes functions
for converting values to specific data types, validating and manipulating dictionaries and lists,
hashing files, managing environment variables, and more. The module is designed to enhance productivity
in data handling and processing tasks, offering a robust set of tools for common and advanced operations.

Key functionalities include:
- Type checking and conversion for various data types.
- Utilities for working with environment variables, including type casting and validation.
- JSON file reading and dictionary manipulation functions.
- Network utilities for checking socket connections.
- File hashing for integrity checks.
- Version control utilities for retrieving Git tags and versions.
- A custom `Version` data class for managing semantic versioning.

The module relies on standard Python libraries such as `dataclasses`, `datetime`, `hashlib`, `itertools`,
`json`, `logging`, `os`, `pathlib`, `socket`, `typing`, and `subprocess`, ensuring compatibility and ease of integration.
"""
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import partial
from hashlib import sha256
from itertools import chain
from json import dumps, JSONDecodeError, loads as json_loads, load as json_load
from shutil import which
from tomllib import load as toml_load, loads as toml_loads, TOMLDecodeError
from logging import debug
from os import environ, getenv
from pathlib import Path
from socket import AF_INET, SOCK_STREAM, socket
from subprocess import PIPE, CalledProcessError, Popen, SubprocessError, run
from sys import platform
from typing import Any, Hashable
from unittest.mock import MagicMock

from alexlib.constants import CLIPBOARD_CMDS


def get_local_tz() -> timezone:
    """returns local timezone"""
    return datetime.now().astimezone().tzinfo


def isnone(w: str) -> bool:
    """checks if input is None or empty string"""
    if isinstance(w, str):
        processed_str = w.strip().lower()
        ret = processed_str == "none" or len(processed_str) == 0
    else:
        ret = w is None
    return ret


def istrue(w: str | int) -> bool:
    """checks if input is True or 1"""
    if isnone(w):
        ret = False
    elif isinstance(w, bool):
        ret = w is True
    elif isinstance(w, int):
        ret = bool(w)
    elif isinstance(w, str):
        processed_str = w.strip().lower()
        ret = processed_str == "true" or processed_str == "t"
        ret = not (processed_str == "false" or processed_str == "f") if ret else ret
        ret = bool(int(w)) if w.isnumeric() else ret
    else:
        try:
            ret = bool(w)
        except TypeError:
            ret = False
    return ret


def isdunder(key: str) -> bool:
    """checks if input is a dunder variable"""
    return key.endswith("__") and key.startswith("__")


def ishidden(key: str) -> bool:
    """checks if input is a hidden variable"""
    return key.startswith("_") and not isdunder(key)


def asdict(
    obj: object,
    include_hidden: bool = False,
    include_dunder: bool = False,
) -> dict[str:Any]:
    """converts object to dictionary"""
    attrs = list(vars(obj).keys())
    if not include_dunder:
        attrs = [x for x in attrs if not isdunder(x)]
    if not include_hidden:
        attrs = [x for x in attrs if not ishidden(x)]
    return {x: getattr(obj, x) for x in attrs}


def aslist(val: str, sep: str = ",") -> list[Any]:
    """converts string to list"""
    if val == "":
        ret = []
    elif val.startswith("[") and val.endswith("]"):
        try:
            ret = json_loads(val)
        except JSONDecodeError:
            ret = val.strip("[]").split(sep)
            ret = [x.strip("'") for x in ret]
            ret = [x.strip('"') for x in ret]
    else:
        ret = val.split(sep)
    return ret


def chktext(
    text: str,
    prefix: str = None,
    value: str = None,
    suffix: str = None,
) -> bool:
    """checks if text starts with prefix, contains value, or ends with suffix"""
    text = text.lower()
    if prefix:
        ret = text.startswith(prefix.lower())
    elif value:
        ret = value.lower() in text
    elif suffix:
        ret = text.endswith(suffix.lower())
    else:
        raise ValueError("need valid input")
    return ret


iswindows = partial(chktext, platform, prefix="win")
ismacos = partial(chktext, platform, prefix="darwin")
islinux = partial(chktext, platform, prefix="linux")


def chktype(
    obj: object,
    type_: type,
    mustexist: bool = True,
) -> object:
    """confirms correct type or raises error"""
    if isinstance(obj, MagicMock):
        return obj
    if not isinstance(obj, type_):
        raise TypeError(f"input is {type(obj)}, not {type_}")

    ispath = isinstance(obj, Path)
    exists = obj.exists() if ispath else True

    if ispath and mustexist and not exists:
        raise FileExistsError(f"{obj} must exist but doesn't")
    return obj


def envcast(
    val: str,
    astype: type,
    need: bool = False,
    sep: str = ",",
) -> Any:
    """converts output to specified type"""
    if isinstance(astype, str):
        astype = eval(astype)  # nosec
    if not isinstance(astype, type):
        raise TypeError(f"astype must be type but is {type(astype)}")
    if issubclass(astype, list):
        ret = aslist(val, sep=sep)
    elif issubclass(astype, dict):
        ret = json_loads(val)
    elif issubclass(astype, bool):
        ret = istrue(val)
    elif issubclass(astype, datetime):
        ret = datetime.fromisoformat(val)
    elif isnone(val):
        ret = None
    else:
        ret = astype(val)
    if isnone(val) and need:
        raise ValueError(f"input must be {astype}")
    try:
        return chktype(ret, astype, mustexist=need)
    except TypeError:
        return ret


def chkenv(
    envname: str,
    need: bool = True,
    ifnull: bool = None,
    astype: type = None,
) -> Any:
    """gets/checks/converts environment variable"""
    val = getenv(envname)
    isblank = val == ""
    isnone_ = isnone(val)
    istrue_ = istrue(val)
    isfalse = val == "False"
    ifnotnone = ifnull is not None
    astypenotnone = astype is not None

    if val and astype is None:
        ret = val
    elif (isblank or isnone_) and ifnotnone:
        ret = ifnull
    elif isnone_ and need:
        raise ValueError(envname)
    elif isblank and need:
        raise ValueError(envname)
    elif isblank or isnone_:
        ret = None
    elif astypenotnone:
        ret = envcast(val, astype, need=need)
    elif istrue_:
        ret = True
    elif isfalse:
        ret = False
    else:
        ret = val
    return ret


def concat_lists(lists: list[list[Any]]) -> list[Any]:
    """concatenates list of lists"""
    return list(chain.from_iterable(lists))


def read_path_as_dict(
    path: Path,
    loadfunc: Callable,
    loadsfunc: Callable,
    decodeerror: Exception,
    mustexist: bool = True,
) -> dict[Hashable:Any]:
    """reads loadable file"""
    chktype(path, Path, mustexist=mustexist)
    try:
        with path.open(mode="rb") as file:
            ret = loadfunc(file)
    except (decodeerror, TypeError):
        ret = loadsfunc(path.read_text())
    return ret


read_json = partial(
    read_path_as_dict,
    loadfunc=json_load,
    loadsfunc=json_loads,
    decodeerror=JSONDecodeError,
)
read_toml = partial(
    read_path_as_dict,
    loadfunc=toml_load,
    loadsfunc=toml_loads,
    decodeerror=TOMLDecodeError,
)


def to_json(dict_: dict[str:str], path: Path) -> None:
    """writes dict to path"""
    path.write_text(dumps(dict_, indent=4))


def flatten_dict(
    d: dict,
    parent_key: str = None,
    sep: str = ":",
) -> dict[str:str]:
    """concatenates keys to create dict having only one level of key value pairs"""
    return {
        f"{parent_key}{sep}{k}" if parent_key else k: v
        for k, v in d.items()
        for k, v in (
            flatten_dict(v, k, sep=sep).items() if isinstance(v, dict) else [(k, v)]
        )
    }


def get_attrs(
    obj: object,
    include_hidden: bool = False,
    include_dunder: bool = False,
    include_methods: bool = False,
) -> dict[str:Any]:
    """returns all attributes of object"""
    attrs = {attr: getattr(obj, attr) for attr in dir(obj)}
    if not include_methods:
        attrs = {k: v for k, v in attrs.items() if not callable(v)}
    if not include_hidden:
        attrs = {k: v for k, v in attrs.items() if not ishidden(k)}
    if not include_dunder:
        attrs = {k: v for k, v in attrs.items() if not isdunder(k)}
    return attrs


def show_dict(d: dict, indent: int = 4) -> None:
    """prints dictionary or list of dictionaries"""
    if isinstance(d, list):
        print("[")
        _ = [print(dict_) for dict_ in d if not isinstance(dict_, dict)]
        _ = [show_dict(dict_) for dict_ in d if isinstance(dict_, dict)]
        print("]")
    else:
        d = {k: v for k, v in d.items() if not k.startswith("_")}
        print(dumps(d, indent=indent))


def show_environ() -> None:
    """prints environment variables"""
    show_dict(dict(environ))


def chkcmd(cmd: str) -> bool:
    """checks if command is available"""
    chktype(cmd, str)
    try:
        ret = which(cmd) is not None
    except OSError:
        run([cmd, "--version"], check=True, stdout=PIPE, stderr=PIPE)
        ret = True
    except (FileNotFoundError, SubprocessError, CalledProcessError):
        ret = False
    return ret


def get_clipboard_cmd() -> list[str]:
    """returns command to copy to clipboard"""
    if iswindows():
        ret = CLIPBOARD_CMDS["windows"]
    elif ismacos():
        ret = CLIPBOARD_CMDS["macos"]
    elif islinux():
        ret = CLIPBOARD_CMDS["linux"]
        cmds = next((cmd for cmd in ret if chkcmd(cmd[0])), None)
        if cmds is None:
            raise OSError(
                "Neither 'xclip' nor 'xsel' commands are available on this Linux system."
            )
        ret = cmds
    else:
        raise OSError(f"{platform} is an unsupported operating system")
    return ret


def to_clipboard(text: str) -> None:
    """
    Securely copies text to the system clipboard across Windows, macOS, and Linux.
    Raises an exception if the input is not a string or if any error occurs during the copy process.

    Args:
        text (str): The text to be copied to the clipboard.

    Raises:
        TypeError: If the input is not a string.
        OSError: For errors related to the subprocess command execution.
    """
    chktype(text, str)
    success = "Text copied to clipboard successfully."
    try:
        topipe = get_clipboard_cmd()
        with Popen(topipe, stdin=PIPE, close_fds=True) as process:
            process.communicate(input=text.encode("utf-8"))
            return success
    except FileNotFoundError as e:
        raise OSError("Clipboard command not found.") from e
    except SubprocessError as e:
        raise OSError(f"Error copying text to clipboard: {e}") from e
    except Exception as e:
        raise RuntimeError("An unexpected error occurred.") from e


def copy_file_to_clipboard(path: Path) -> bool:
    """Copies file to the clipboard. Returns True if successful, False otherwise."""
    chktype(path, Path)
    if not path.exists():
        raise FileNotFoundError(f"File {path} not found")
    if not path.is_file():
        raise ValueError(f"{path} is not a file")
    to_clipboard(path.read_text())
    return f"File content from {path} copied to clipboard."


def get_objects_by_attr(
    lst: list[object],
    attr: str,
    val: str,
) -> list[object]:
    """filters list of objects based on value of attribute"""
    return [x for x in lst if getattr(x, attr) == val]


class Object:
    """base class for objects"""

    @property
    def reg_attrs(self) -> dict[str:Any]:
        """returns all attributes except hidden ones"""
        return {k: v for k, v in get_attrs(self)}

    @property
    def reg_attrs_keys(self) -> list[str]:
        """returns all attributes except hidden ones"""
        return list(self.reg_attrs.keys())

    def set_hasattr(self, attr: str) -> None:
        """sets hasattr property for attribute"""

        def hasattr_func(
            self,
            attr: str,
        ) -> bool:
            """checks if object has attribute"""
            if not hasattr(self, attr):
                ret = False
            else:
                ret = getattr(self, attr) is not None
            return ret

        newattr = f"has{attr}"
        if not hasattr(self, newattr):
            setattr(self, newattr, property(hasattr_func))

    def set_hasattrs(self) -> None:
        """sets hasattr property for all attributes"""
        for k in self.reg_attrs_keys:
            if not k.startswith("has"):
                self.set_hasattr(k)


def mk_dictvals_distinct(dict_: dict[Hashable:Any]) -> dict[Hashable:Any]:
    """makes all values in dictionary distinct"""
    keys = list(dict_.keys())
    return {key: list(set(dict_[key])) for key in keys}


def invert_dict(dict_: dict) -> dict[Hashable:Hashable]:
    """flips the keys and values of a dictionary"""
    return {v: k for k, v in dict_.items()}


def sha256sum(
    path: Path,
    bytearr: bytearray = bytearray(128 * 1024),
) -> str:
    """inputs:
        filename = path + name of file to hash
    returns:
        hash of file
    """
    if not isinstance(path, Path):
        raise TypeError("func only computes sum on path")
    h, mv = sha256(), memoryview(bytearr)
    with open(path, "rb", buffering=0) as f:
        for n in iter(lambda: f.readinto(mv), 0):
            h.update(mv[:n])
    return h.hexdigest()


def chkhash(path: Path, stored_hash: str) -> bool:
    """checks if hash of file matches stored hash"""
    return sha256sum(path) == stored_hash


def get_curent_version(tag: str) -> str:
    """returns current version"""
    if tag.startswith("v"):
        tag = tag[1:]
    if "-" in tag:
        tag = tag[: tag.index("-")]
    return tag


@dataclass
class Version:
    """data class for semantic versioning"""

    major: int
    minor: int
    patch: int

    def __iter__(self):
        """returns version as iterable"""
        return iter(
            [
                self.major,
                self.minor,
                self.patch,
            ]
        )

    def __str__(self) -> str:
        """returns version as string"""
        return ".".join(list(self))

    def __repr__(self) -> str:
        """returns version as string"""
        return str(self)


def ping(host: str, port: int, astext: bool = False) -> bool | str:
    """checks if socket is open"""
    with socket(AF_INET, SOCK_STREAM) as sock:
        isopen = sock.connect_ex((host, port)) == 0
        text = "" if isopen else "not "
        text = f"{host}:{port} is {text}open"
        debug(text)
        return text if astext else isopen

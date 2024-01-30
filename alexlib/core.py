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
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from hashlib import sha256
from itertools import chain
from json import dumps
from json import JSONDecodeError
from json import loads
from logging import debug
from os import getenv
from pathlib import Path
from socket import AF_INET
from socket import SOCK_STREAM
from socket import socket
from subprocess import PIPE, Popen, check_output
from typing import Any
from typing import Hashable


def get_local_tz() -> timezone:
    """returns local timezone"""
    return datetime.now().astimezone().tzinfo


def isnone(w: str) -> bool:
    """checks if input is None or empty string"""
    if isinstance(w, str):
        ret = w.lower() == "none" or len(w) == 0
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
        ret = w.lower() == "true" or w.lower() == "t"
        ret = bool(int(w)) if w.isnumeric() else ret
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
    if val.startswith("[") and val.endswith("]"):
        try:
            ret = loads(val)
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


def chktype(
    obj: object,
    type_: type,
    mustexist: bool = True,
) -> object:
    """confirms correct type or raises error"""
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
        ret = loads(val)
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


def read_json(path: Path) -> dict[Hashable:Any]:
    """reads json file"""
    if isinstance(path, dict):
        return path
    return loads(path.read_text())


def flatten_dict(
    d: dict,
    parent_key: str = None,
    sep: str = ":",
) -> dict[str:str]:
    """concattenates keys to flatter dict"""
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
) -> dict[str:Any]:
    """returns all attributes of object"""
    attrs = {
        attr: getattr(obj, attr)
        for attr in dir(obj)
        if not callable(getattr(obj, attr))
    }
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
        print(dumps(d, indent=indent))


def to_clipboard(text: str) -> bool:
    """Copies text to the clipboard. Returns True if successful, False otherwise."""
    command = "/usr/bin/pbcopy"
    # Check if the command exists on the system
    if not Path(command).exists():
        print(f"Command {command} not found")
        return False
    try:
        with Popen([command], stdin=PIPE, shell=False) as p:
            p.stdin.write(text.encode("utf-8"))  # Specify encoding if necessary
            p.stdin.close()
            retcode = p.wait()
        return retcode == 0
    except OSError as e:
        print(f"Error during execution: {e}")
        return False


def copy_file_to_clipboard(path: Path) -> bool:
    """Copies file to the clipboard. Returns True if successful, False otherwise."""
    if not path.exists():
        raise FileNotFoundError(f"File {path} not found")
    if not path.is_file():
        raise ValueError(f"{path} is not a file")
    return to_clipboard(path.read_text())


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


def invert_dict(_dict: dict) -> dict[Hashable:Hashable]:
    """flips the keys and values of a dictionary"""
    rng = range(len(_dict))
    vals = list(_dict.values())
    return {vals[i]: _dict[vals[i]] for i in rng}


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


def get_last_tag() -> str:
    """returns last git tag"""
    return check_output(["git", "describe", "--tags"]).decode("ascii")  # nosec


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

    @classmethod
    def from_tag(cls):
        """returns version from git tag"""
        parts = get_curent_version(get_last_tag()).split(".")
        return cls(*parts)

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

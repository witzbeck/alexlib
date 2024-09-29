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

from datetime import datetime
from functools import partial
from json import JSONDecodeError, dumps
from json import loads as json_loads
from logging import debug, getLogger
from os import environ, getenv
from pathlib import Path
from shutil import which
from socket import AF_INET, SOCK_STREAM, socket
from subprocess import PIPE, CalledProcessError, Popen, SubprocessError, run
from sys import platform
from typing import Any, Hashable

from alexlib.constants import CLIPBOARD_COMMANDS_MAP

logger = getLogger(__name__)


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
        ret = processed_str in ("true", "t", "1", "yes", "y", "on")
        ret = (
            processed_str not in ("false", "f", "0", "no", "n", "off")
            if not ret
            else ret
        )
        ret = bool(int(w)) if w.isnumeric() else ret
    else:
        try:
            ret = bool(w)
        except TypeError:
            ret = False
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


def path_istype(path: Path, suffix: str) -> bool:
    """checks if path is of specified type"""
    path_suffix = path.suffix.lower()
    norm_suffix = suffix.lower().strip(".")
    return path_suffix.endswith(norm_suffix)


def chktype(
    obj: object,
    type_: type,
    mustexist: bool = True,
    suffix: str = None,
) -> object:
    """confirms correct type or raises error"""
    if not isinstance(obj, type_):
        raise TypeError(f"input is {type(obj)}, not {type_}")

    ispath = isinstance(obj, Path)
    exists = obj.exists() if ispath else True

    if ispath and mustexist and not exists:
        raise FileNotFoundError(f"{obj} must exist but doesn't")
    if ispath and suffix is not None and not path_istype(obj, suffix):
        raise ValueError(f"{obj} must be of type {suffix}")
    return obj


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
    hidden: bool = False,
    dunder: bool = False,
    methods: bool = False,
) -> dict[str:Any]:
    """returns all attributes of object"""
    attrs = {attr: getattr(obj, attr) for attr in dir(obj)}
    if not methods:
        attrs = {k: v for k, v in attrs.items() if not callable(v)}
    if not hidden:
        attrs = {k: v for k, v in attrs.items() if not ishidden(k)}
    if not dunder:
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
        ret = CLIPBOARD_COMMANDS_MAP["windows"]
    elif ismacos():
        ret = CLIPBOARD_COMMANDS_MAP["macos"]
    elif islinux():
        ret = CLIPBOARD_COMMANDS_MAP["linux"]
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


def copy_file_to_clipboard(path: Path) -> bool:
    """Copies file to the clipboard. Returns True if successful, False otherwise."""
    chktype(path, Path, mustexist=True)
    if not path.is_file():
        raise ValueError(f"{path} is not a file")
    to_clipboard(path.read_text())
    logger.info(f"File content from {path} copied to clipboard.")
    return True


def get_objects_by_attr(
    lst: list[object],
    attr: str,
    val: str,
) -> list[object]:
    """filters list of objects based on value of attribute"""
    return [x for x in lst if getattr(x, attr) == val]


def mk_dictvals_distinct(dict_: dict[Hashable, Any]) -> dict[Hashable:Any]:
    """makes all values in dictionary distinct"""
    return {key: set(value) for key, value in dict_.items()}


def invert_dict(dict_: dict) -> dict[Hashable, Hashable]:
    """flips the keys and values of a dictionary"""
    return {v: k for k, v in dict_.items()}


def get_curent_version(tag: str) -> str:
    """returns current version"""
    if tag.startswith("v"):
        tag = tag[1:]
    if "-" in tag:
        tag = tag[: tag.index("-")]
    return tag


def ping(host: str, port: int, astext: bool = False) -> bool | str:
    """checks if socket is open"""
    with socket(AF_INET, SOCK_STREAM) as sock:
        isopen = sock.connect_ex((host, port)) == 0
        text = "" if isopen else "not "
        text = f"{host}:{port} is {text}open"
        debug(text)
        return text if astext else isopen

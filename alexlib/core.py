from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from itertools import chain
from logging import debug
from os import getenv
from pathlib import Path
from socket import AF_INET, SOCK_STREAM, socket
from typing import Any, Hashable
from subprocess import check_output

""" core functions & objects must only use the standard lib
"""


def chktext(
    text: str,
    prefix: str = None,
    value: str = None,
    suffix: str = None,
) -> bool:
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
    else:
        ret = obj

    if (ispath := isinstance(obj, Path)):
        exists = obj.exists()
    else:
        exists = True

    if (ispath and mustexist and not exists):
        raise FileExistsError(f"{obj} must exist but doesn't")
    else:
        return ret


def envcast(
    val: str,
    astype: Any,
    spliton: str = ",",
    need: bool = True,
) -> Any:
    """converts output to specified type"""
    if isinstance(astype, str):
        astype = eval(astype)
    if issubclass(astype, list):
        ret = val.split(spliton)
    elif issubclass(astype, datetime):
        ret = datetime.fromisoformat(val)
    else:
        ret = astype(val)
    return chktype(ret, astype, mustexist=need)


def chkenv(
    envname: str,
    need: bool = True,
    ifnull: bool = None,
    astype: Any = None,
) -> Any:
    """gets/checks/converts environment variable"""
    val = getenv(envname)
    isblank = val == ""
    isnone = val is None
    istrue = val == "True"
    isfalse = val == "False"
    ifnotnone = ifnull is not None
    astypenotnone = astype is not None

    if ((isblank or isnone) and ifnotnone):
        return ifnull
    elif (isnone and need):
        raise ValueError(envname)
    elif (isblank and need):
        raise ValueError(envname)
    elif (isblank or isnone):
        return None
    elif astypenotnone:
        ret = envcast(val, astype, need=need)
    elif istrue:
        ret = True
    elif isfalse:
        ret = False
    else:
        ret = val
    return ret


def concat_lists(lists: list[list[Any]]) -> list[Any]:
    return list(chain.from_iterable(
        lists
    ))


def isdunder(key: str) -> bool:
    return (key.endswith("__") and key.startswith("__"))


def ishidden(key: str) -> bool:
    return (key.startswith("_") and not isdunder(key))


def asdict(
        obj: object,
        include_hidden: bool = False,
        include_dunder: bool = False,
) -> dict[str: Any]:
    attrs = list(vars(obj).keys())
    if not include_dunder:
        attrs = [x for x in attrs if not isdunder(x)]
    if not include_hidden:
        attrs = [x for x in attrs if not ishidden(x)]
    return {
        x: getattr(obj, x)
        for x in attrs
    }


def get_objects_by_attr(
    lst: list[object],
    attr: str,
    val: str,
) -> list[object]:
    """filters list of objects based on value of attribute"""
    return [x for x in lst if getattr(x, attr) == val]


class Object(object):
    @property
    def reg_attrs(self):
        return {k: v for k, v in self.__dict__.items() if k[0] != "_"}

    @property
    def reg_attrs_keys(self):
        return list(self.reg_attrs.keys())

    def set_hasattr(self, attr: str):
        def hasattr_func(
            self,
            attr: str,
        ) -> bool:
            if not hasattr(self, attr):
                ret = False
            else:
                ret = getattr(self, attr) is not None
            return ret

        newattr = f"has{attr}"
        if not hasattr(self, newattr):
            setattr(self, newattr, property(hasattr_func))

    def set_hasattrs(self):
        for k in self.reg_attrs_keys:
            if not k.startswith("has"):
                self.set_hasattr(k)


def mk_dictvals_distinct(
    dict_: dict[Hashable: Hashable]
) -> dict[Any:Any]:
    keys = list(dict_.keys())
    return {key: list(set(dict_[key])) for key in keys}


def invert_dict(_dict: dict):
    """flips the keys and values of a dictionary"""
    rng = range(len(_dict))
    vals = list(_dict.values())
    return {vals[i]: _dict[vals[i]] for i in rng}


def sha256sum(
    path: Path,
    bytearr: bytearray = bytearray(128 * 1024),
) -> str:
    """ inputs:
            filename = path + name of file to hash
        returns:
            hash of file
    """
    if not isinstance(path, Path):
        raise TypeError("func only computes sum on path")
    h, mv = sha256(), memoryview(bytearr)
    with open(path, 'rb', buffering=0) as f:
        for n in iter(lambda: f.readinto(mv), 0):
            h.update(mv[:n])
    return h.hexdigest()


def chkhash(path: Path, stored_hash: str) -> bool:
    return sha256sum(path) == stored_hash


def get_last_tag() -> str:
    return check_output(["git", "describe", "--tags"]).decode("ascii")


def get_curent_version(tag: str) -> str:
    if tag.startswith("v"):
        tag = tag[1:]
    if "-" in tag:
        tag = tag[:tag.index("-")]
    return tag


@dataclass
class Version:
    major: int
    minor: int
    patch: int

    @classmethod
    def from_tag(cls):
        parts = get_curent_version(get_last_tag()).split(".")
        return cls(*parts)

    def __iter__(self):
        return iter([
            self.major,
            self.minor,
            self.patch,
        ])

    def __str__(self) -> str:
        return ".".join(list(self))

    def __repr__(self) -> str:
        return str(self)


def ping(
    host: str,
    port: int,
    astext: bool = False
) -> bool | str:
    with socket(AF_INET, SOCK_STREAM) as sock:
        isopen = sock.connect_ex((host, port)) == 0
        text = "" if isopen else "not "
        text = f"{host}:{port} is {text}open"
        debug(text)
        return text if astext else isopen

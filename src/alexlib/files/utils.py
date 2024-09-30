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

from collections.abc import Hashable, Mapping
from hashlib import sha256
from json import dumps
from json import loads as json_loads
from logging import getLogger
from os import environ
from pathlib import Path
from typing import Union

from matplotlib.pyplot import savefig

from alexlib.core import chktype

logger = getLogger(__name__)


def get_parent(path: Path, parent_name: str) -> Path:
    """gets parent path by name"""
    chktype(path, Path, mustexist=True)
    if parent_name not in path.parts:
        toprint_parts = "\n" + "\n".join([f"\t{x}" for x in path.parts]) + "\n"
        raise ValueError(f"{parent_name} not in parents[{toprint_parts}]")
    return [x for x in path.parents if x.name == parent_name][-1]


def read_json(path: Path) -> dict[Hashable, str]:
    """reads json file"""
    chktype(path, Path, mustexist=True)
    return json_loads(path.read_text())


try:
    from tomllib import loads as toml_loads

    def read_toml(path: Path) -> dict[str, str]:
        """reads toml file"""
        chktype(path, Path, mustexist=True)
        return toml_loads(path.read_text())

except ImportError as e:  # pragma: no cover

    def read_toml(path: Path, e=e) -> dict[str, str]:
        """reads toml file"""
        raise ImportError("toml support requires tomllib package") from e

    logger.debug(f"toml support only available ^3.11: {e}")


def write_json(dict_: dict[str:str], path: Path) -> None:
    """writes dict to path"""
    path.write_text(dumps(dict_, indent=4))


def read_dotenv(dotenv_path: Path) -> dict[str, str]:
    """read a dotenv file into a dictionary"""
    chktype(dotenv_path, Path, mustexist=True)
    return {
        k: v.strip("'").strip('"').strip()
        for k, v in [
            x.split("=")
            for x in [
                x
                for x in dotenv_path.read_text().split("\n")
                if x and not x.startswith("#")
            ]
        ]
    }


def load_dotenv(dotenv_path: Path) -> dict[str, str]:
    """load a dotenv file into a dictionary"""
    return environ.update(read_dotenv(dotenv_path))


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


def sha256sum(path: Path) -> str:
    """inputs:
        path: path to file
    returns:
        hash of file
    """
    bytearr = bytearray(128 * 1024)
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


def normalize_path(path: Union[Path, str]) -> Path:
    """Ensure the path is a Path object."""
    return Path(path) if isinstance(path, str) else path


def is_dotenv(path: Union[Path, str]) -> bool:
    """Check if the file is a dotenv file."""
    path = normalize_path(path)
    name = path.name.lower()
    return name.startswith(".env") or path.suffix == ".env"


def is_json(path: Union[Path, str]) -> bool:
    """Check if the file is a JSON file."""
    path = normalize_path(path)
    return path.suffix.lower() == ".json"


def dump_envs(
    path: Union[Path, str, None] = None,
    pairs: Mapping[str, str] = None,
    force: bool = False,
) -> None:
    """Dump key-value pairs to a file. Supported file types are dotenv and JSON."""
    path = normalize_path(path) if path else Path.cwd() / ".env"
    if path.exists() and not force:
        raise FileExistsError(f"{path} already exists. Use force=True to overwrite.")
    pairs = pairs if pairs is not None else dict(environ)
    if is_dotenv(path):
        content = "\n".join(f"{key}={value}" for key, value in pairs.items())
        path.write_text(content)
    elif is_json(path):
        path.write_text(dumps(pairs, indent=4))
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")
    logger.info(f"Dumped {len(pairs)} environment variables to {path}")

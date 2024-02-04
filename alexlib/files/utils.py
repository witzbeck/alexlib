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
from pathlib import Path

from matplotlib.pyplot import savefig


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

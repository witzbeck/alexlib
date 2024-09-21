"""
This module provides tools for handling and manipulating SQL queries in Python, integrating with pandas DataFrames and SQLAlchemy for database interactions. It offers functionalities to convert SQL queries from files or strings into SQLAlchemy TextClauses, copy them to the clipboard, generate filenames for SQL scripts based on schema and table names, and write SQL queries to files. Additionally, it includes utilities for creating one-hot encoded views from pandas DataFrames.

Key Features:
- SQL class: A wrapper for SQLAlchemy TextClause with methods to initialize from files or strings, copy to clipboard, and convert to TextClause.
- File handling: Functions to create default filenames for SQL scripts and write SQL queries to files, with overwrite control.
- One-hot encoding: Utility to create a SQL view for one-hot encoding of specified columns in a DataFrame.

Dependencies:
- Requires the `pandas` library for DataFrame manipulation.
- Utilizes `SQLAlchemy` for database interaction.
- Interacts with the system clipboard, which is currently tailored for macOS (`pbcopy`).

Note:
- The module is part of the 'alexlib' package and assumes the presence of specific utility functions from other modules within the same package.
"""

from dataclasses import dataclass, field
from itertools import chain
from pathlib import Path
from re import sub

from pandas import DataFrame
from sqlalchemy import TextClause, text

from alexlib.constants import COLUMN_SUB_PATH
from alexlib.core import to_clipboard
from alexlib.db.objects import Name
from alexlib.df import filter_df, get_distinct_col_vals
from alexlib.files.objects import File
from alexlib.files.utils import read_json

LOGICALS = ("and", "or")

LIST_OPS = ("in", "not in")
BTWN_OPS = ("between", "not between")
SINGLE_OPS = ("is", "is not", "like", "not like")
DOUBLE_MAP = {"=": "eq", "!=": "ne", "<": "lt", ">": "gt", "<=": "le", ">=": "ge"}
DOUBLE_OPS = list(DOUBLE_MAP.keys())


def sanitize_col_name(col: str) -> str:
    """sanitizes column name"""
    COL_SUBS = read_json(COLUMN_SUB_PATH)
    "".join([COL_SUBS[x] if x in COL_SUBS else x for x in col])


@dataclass(init=False, frozen=True)
class SQL(str):
    """wrapper for sqlalchemy TextClause"""

    toclip: bool = field(default=False, repr=False)

    @classmethod
    def from_path(cls, path: Path, **kwargs) -> "SQL":
        """makes sql from path to a file"""
        return cls(path.read_text(), **kwargs)

    @classmethod
    def from_file(cls, file: File, **kwargs) -> "SQL":
        """makes sql from File object"""
        return cls(file.text, **kwargs)

    def __str__(self) -> str:
        return super().__str__(self.sanitized)

    def __new__(cls, content: str) -> "SQL":
        """creates new instance of SQL class"""
        if isinstance(content, Path):
            content = content.read_text()
        elif isinstance(content, File):
            content = content.text
        elif not isinstance(content, (str, SQL)):
            raise TypeError(f"content must be str, not {type(content)}")
        return super().__new__(cls, content)

    @property
    def sanitized(self) -> str:
        """
        Sanitize input string for SQL queries by escaping potentially dangerous characters.
        This is a basic method and not recommended for sanitizing queries directly.
        Use parameterized queries wherever possible.

        Parameters:
        input_string (str): The input string to be sanitized.

        Returns:
        str: Sanitized string.
        """
        ret = self.replace("\n", " ").replace(";", "").replace("  ", " ")
        ret = sub(r'["\']', "", ret)
        return ret

    @property
    def clause(self) -> TextClause:
        """returns sqlalchemy TextClause"""
        return text(self)

    def __post_init__(self) -> None:
        """actions:
        - adds query to clipboard if toclip is True
        """
        if self.toclip:
            to_clipboard(str(self))

    @staticmethod
    def mk_default_filename(
        schema: str, table: str, prefix: str = "select", suffix: str = ".sql"
    ) -> str:
        """makes filename from schema and table"""
        return f"{prefix}_{schema}_{table}{suffix}"

    @staticmethod
    def to_file(txt: str, path: Path, overwrite: bool = True) -> None:
        """writes text to file"""
        if path.exists() and not overwrite:
            raise FileExistsError("file already exists here. overwrite?")
        path.write_text(txt)

    @staticmethod
    def fmt_line(idx: int, col: str, abrv: str) -> str:
        """formats line for select statement"""
        comma = "," if idx else " "
        return f"{comma}{abrv}.{col}\n"

    @classmethod
    def from_info_schema(
        cls,
        schema: Name,
        table: Name,
        info_schema: DataFrame,
    ) -> "SQL":
        """makes select from table query from info_schema"""
        info_schema = filter_df(info_schema, table, "table_name")
        info_schema = filter_df(info_schema, schema, "table_schema")
        if not isinstance(table, Name):
            table = Name(table)
        abrv = table.abrv
        first = ["select\n"]
        lines = [
            cls.fmt_line(idx, col, abrv)
            for idx, col in enumerate(info_schema.loc[:, "column_name"].tolist())
        ]
        last = [f"from {schema}.{table} {abrv}"]
        return cls("".join(list(chain(first, lines, last))))

    @classmethod
    def mk_cmd(
        cls,
        cmd: str,
        obj_type: str,
        obj_name: str,
        schema: str = None,
        addl_cmd: str = "",
    ) -> "SQL":
        """makes sql command"""
        schema = f"{schema}." if schema else ""
        return cls(f"{cmd} {obj_type} {schema}{obj_name} {addl_cmd}")


def mk_view_text(name: str, sql: SQL) -> SQL:
    """makes create view text"""
    return f"CREATE VIEW {name} AS \n{sql}"


def mk_onehot_case_col(col: str) -> str:
    """makes column header for onehot encoding row"""
    return f"is_{sanitize_col_name(col)}"


def mk_onehot_case_row(col: str, val: str) -> str:
    """makes case statement for onehot encoding"""
    new_col = mk_onehot_case_col(val)
    return f",case when {col} = '{val}' then 1 else 0 end {new_col}\n"


def create_onehot_view(
    df: DataFrame,
    schema: str,
    table: str,
    dist_col: str,
    id_col: str = None,
) -> str:
    """creates onehot view from dataframe"""
    new_name = f"{schema}.v_{table}_onehot"
    lines = [
        mk_onehot_case_row(dist_col, val) for val in get_distinct_col_vals(df, dist_col)
    ]
    return "\n".join(
        chain(
            [
                f"create view {new_name} as select",
                f" {id_col}",
                f",{dist_col}",
            ],
            lines,
            [f"from {schema}.{table}"],
        )
    )

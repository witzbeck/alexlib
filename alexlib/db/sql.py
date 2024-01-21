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
from pathlib import Path
from subprocess import PIPE, Popen
from pandas import DataFrame
from sqlalchemy import TextClause, text
from alexlib.db import get_table_abrv, onehot_case

from alexlib.df import get_distinct_col_vals
from alexlib.files import File


@dataclass
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

    def __post_init__(self) -> None:
        """adds query to clipboard if toclip is True"""
        if self.toclip:
            self.to_clipboard(str(self))

    @property
    def clause(self) -> TextClause:
        """returns sqlalchemy TextClause"""
        return text(self)

    @staticmethod
    def to_clipboard(txt: str) -> bool:
        """Copies text to the clipboard. Returns True if successful, False otherwise."""
        command = "/usr/bin/pbcopy"

        # Check if the command exists on the system
        if not Path(command).exists():
            print(f"Command {command} not found")
            return False

        try:
            with Popen([command], stdin=PIPE, shell=False) as p:
                p.stdin.write(txt.encode("utf-8"))  # Specify encoding if necessary
                p.stdin.close()
                retcode = p.wait()
            return retcode == 0
        except OSError as e:
            print(f"Error during execution: {e}")
            return False

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

    @classmethod
    def from_info_schema(
        cls,
        schema: str,
        table: str,
        info_schema: DataFrame,
    ) -> "SQL":
        """makes select * from table query from info_schema"""
        abrv = get_table_abrv(table)
        lines = ["select\n"]
        cols = list(info_schema.loc[:, "column_name"])
        for i, col in enumerate(cols):
            if i == 0:
                comma = " "
            else:
                comma = ","
            line = f"{comma}{abrv}.{col}\n"
            lines.append(line)
        lines.append(f"from {schema}.{table} {abrv}")
        return cls("".join(lines))


def create_onehot_view(
    df: DataFrame,
    schema: str,
    table: str,
    command: str = "create view",
) -> str:
    """creates onehot view from dataframe"""
    dist_col = [x for x in df.columns if x[-2:] != "id"][0]
    id_col = [x for x in df.columns if x != dist_col][0]
    dist_vals = get_distinct_col_vals(df, dist_col)
    first_line = f"{command} {schema}.v_{table}_onehot as select\n"
    lines = [first_line]
    lines.append(f" {id_col}\n")
    lines.append(f",{dist_col}\n")
    for val in dist_vals:
        new_col = f"is_{val}".replace(" ", "_")
        new_col = new_col.replace("%", "_percent")
        new_col = new_col.replace("-", "_")
        new_col = new_col.replace("<", "_less")
        new_col = new_col.replace("=", "_equal")
        new_col = new_col.replace(">", "_greater")
        case_stmt = onehot_case(dist_col, val)
        lines.append(f",{case_stmt} {new_col}\n")
    lines.append(f"from {schema}.{table}")
    return "".join(lines)

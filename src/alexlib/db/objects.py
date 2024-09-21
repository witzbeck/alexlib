"""
This module provides a set of classes to wrap database objects like names, columns, tables, and schemas, offering convenient methods for interacting with them in a structured manner. It includes classes that validate and manage names, represent database columns with additional functionalities, handle tables as pandas dataframes, and encapsulate database schemas. The module integrates with pandas and SQLAlchemy, allowing for efficient and pythonic database operations.

Classes:
    Name: A wrapper class for database object names, ensuring they adhere to specific validation rules.
    Column: Represents a database column, integrating with pandas Series to provide additional data analysis functionalities like frequency and proportion calculations.
    Table: A wrapper class for database tables represented as pandas DataFrames, offering methods for column management and data access.
    Schema: Represents a database schema, allowing for aggregation and management of multiple tables within a schema.

Each class includes methods and properties to handle various aspects of database operations, such as data validation, retrieval of distinct values, frequency and proportion calculations, and conversion between different data representations.
"""

from dataclasses import dataclass, field
from functools import cached_property
from random import choice
from re import match

from numpy import ndarray
from pandas import DataFrame, Series

from alexlib.df import series_col

# Define a pattern for valid SQL object names.
# Adjust the pattern as per your DB's naming rules.
VALID_NAME_RULES = r"^[A-Za-z][A-Za-z0-9_]*$"


def get_abrv(table_name: str) -> str:
    """gets table abbreviation"""
    parts = table_name.split("_")
    firsts = [x[0] for x in parts]
    return "".join(firsts)


def validate_name(name: str) -> None:
    """validates name"""
    # This pattern allows alphanumeric characters and underscores, starting with a letter.
    if name.isnumeric():
        raise ValueError("name cannot be numeric")
    # Check if the name matches the pattern
    if not match(VALID_NAME_RULES, name):
        raise ValueError("name must be alphanumeric and start with a letter")


@dataclass(frozen=True, init=False)
class Name(str):
    """wrapper for db object name"""

    def __new__(cls, content: str) -> str:
        """returns name as str"""
        validate_name(content)
        return super().__new__(cls, content)

    @property
    def abrv(self) -> str:
        """returns abbreviation"""
        return get_abrv(self)


@dataclass
class Column:
    """wrapper for db column w pandas series"""

    name: Name = field()
    table_name: Name = field()
    schema_name: Name = field()
    series: Series = field(default=None, repr=False)

    def __len__(self) -> int:
        """returns length of series"""
        return len(self.series) if hasattr(self, "series") else 0

    def __post_init__(self) -> None:
        """sets attributes"""
        if not isinstance(self.name, Name):
            self.name = Name(self.name)
        if not isinstance(self.table_name, Name):
            self.table_name = Name(self.table_name)
        if not isinstance(self.schema_name, Name):
            self.schema_name = Name(self.schema_name)

    @cached_property
    def distvals(self) -> ndarray:
        """returns list of distinct values in series"""
        return self.series.unique()

    @property
    def ndistvals(self) -> int:
        """returns number of distinct values in series"""
        return len(self.distvals)

    @cached_property
    def frequencies(self) -> dict[str:int]:
        """returns dict of distinct values and frequencies"""
        return {x: sum(self.series == x) for x in self.distvals}

    @cached_property
    def proportions(self) -> dict[str:float]:
        """returns dict of distinct values and proportions"""
        freqs = self.frequencies
        n = len(self)
        return {x: freqs[x] / n for x in self.distvals}

    @property
    def isid(self) -> bool:
        """checks if column is id"""
        return self.name.lower().endswith("_id")

    @property
    def nnulls(self) -> int:
        """returns number of nulls in series"""
        return sum(self.series.isna())


@dataclass
class Table:
    """wrapper for db table as pandas dataframe"""

    name: Name
    schema_name: Name
    df: DataFrame = field(
        init=False,
        repr=False,
    )

    def __len__(self) -> int:
        """returns number of rows"""
        return len(self.df)

    def __post_init__(self) -> None:
        """sets attributes"""
        if not isinstance(self.name, Name):
            self.name = Name(self.name)
        if not isinstance(self.schema_name, Name):
            self.schema_name = Name(self.schema_name)

    @cached_property
    def cols(self) -> list[str]:
        """returns list of column names"""
        return list(self.df.columns)

    @property
    def ncols(self) -> int:
        """returns number of columns"""
        return len(self.cols)

    @cached_property
    def col_series(self) -> dict[str:Series]:
        """returns dict of column names and series"""
        return {x: series_col(self.df, x) for x in self.cols}

    @cached_property
    def col_objs(self) -> dict[str:Column]:
        """returns dict of column names and column objects"""
        s, t, cs = self.schema_name, self.name, self.col_series
        return {x: Column(x, t, s, series=cs[x]) for x in self.cols}

    @property
    def rand_col(self) -> Column:
        """returns random column"""
        return choice(self.cols)

    @classmethod
    def from_df(
        cls,
        schema_name: str,
        name: str,
        df: DataFrame,
    ) -> "Table":
        """makes table from dataframe"""
        cls_ = cls(schema_name=schema_name, name=name)
        cls_.df = df
        return cls_


@dataclass
class Schema:
    """wrapper for db schema"""

    name: Name = field()
    tables: list[Table] = field(default_factory=list, repr=False)


@dataclass
class Database:
    """wrapper for db"""

    name: Name = field()
    schemas: list[Schema] = field(init=False)

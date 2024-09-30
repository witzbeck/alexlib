"""Test schema object"""

from random import choice

from pandas import DataFrame, Series
from pytest import fixture, raises

from alexlib.db.objects import Column, Name, Schema, Table


@fixture(scope="function")
def schema():
    """Return a schema object"""
    return Schema("test_schema")


@fixture(scope="function")
def table(df):
    """Return a table object"""
    return Table.from_df(schema_name="test_schema", name="test_table", df=df)


@fixture(scope="function")
def series(df: DataFrame) -> Series:
    """Return a series object"""
    col = choice(list(df.columns))
    return df.loc[:, col].copy()


@fixture(scope="function")
def column(series: Series):
    """Return a column object"""
    return Column("test_column", "test_table", "test_schema", series=series)


@fixture(scope="function")
def valid_name():
    """Return a valid name object"""
    return Name("valid_name123")


def test_column_len(column: Column):
    """Test column length"""
    assert len(column) > 0


def test_column_distvals(column: Column):
    """Test column distinct values"""
    assert len(column.distvals) > 0


def test_column_dtype(column: Column):
    """Test column dtype"""
    assert column.series.dtype


def test_column_name(column: Column):
    """Test column name"""
    assert column.name == "test_column"
    assert isinstance(column.name, Name)


def test_column_table(column: Column):
    """Test column table"""
    assert column.table_name == "test_table"
    assert isinstance(column.table_name, Name)


def test_column_schema(column: Column):
    """Test column schema"""
    assert column.schema_name == "test_schema"
    assert isinstance(column.schema_name, Name)


def test_column_ndistvals(column: Column):
    """Test column number of distinct values"""
    assert column.ndistvals > 0


def test_column_frequencies(column: Column):
    """Test column frequencies"""
    assert isinstance(column.frequencies, dict)


def test_column_proportions(column: Column):
    """Test column proportions"""
    assert isinstance(column.proportions, dict)


def test_column_isid(column: Column):
    """Test column isid"""
    assert isinstance(column.isid, bool)


def test_column_nnulls(column: Column):
    """Test column nnulls"""
    assert column.nnulls >= 0


def test_name_validation(valid_name: Name):
    """Test to ensure that Name validates correctly"""
    assert valid_name


def test_name_abrv(valid_name: Name):
    """Test abbreviation generation"""
    assert valid_name.abrv == "vn"


def test_invalid_name():
    """Test invalid name"""
    with raises(ValueError):
        Name("123invalid")


def test_schema(schema: Schema):
    """Test tables property"""
    assert isinstance(schema.tables, list)
    assert isinstance(schema, Schema)


def test_table_obj(table: Table):
    """Test table object"""
    assert isinstance(table, Table)


def test_table_name(table: Table):
    assert str(table.name) == "test_table"
    assert isinstance(table.name, Name)


def test_table_cols(table: Table, df: DataFrame):
    """Test column names"""
    assert table.cols == df.columns.tolist()


def test_table_ncols(table: Table, df: DataFrame):
    """Test number of columns"""
    assert table.ncols == len(df.columns)

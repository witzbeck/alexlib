"""Test schema object"""

from pandas import DataFrame
from pytest import fixture, raises

from alexlib.db.objects import Name, Schema, Table


@fixture(scope="class")
def schema():
    """Return a schema object"""
    return Schema("test_schema")


@fixture(scope="class")
def table(df):
    """Return a table object"""
    return Table.from_df(schema_name="test_schema", name="test_table", df=df)


@fixture(scope="class")
def valid_name():
    """Return a valid name object"""
    return Name("valid_name123")


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


def test_tables(table: Table):
    """Test table object"""
    assert isinstance(table, Table)
    assert str(table.name) == "test_table"


def test_table_cols(table: Table, df: DataFrame):
    """Test column names"""
    assert table.cols == df.columns.tolist()


def test_table_ncols(table: Table, df: DataFrame):
    """Test number of columns"""
    assert table.ncols == len(df.columns)

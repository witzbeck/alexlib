"""
Unit tests for the Curl class in the alexlib.auth module.

This module contains tests to verify the functionality of the Curl class,
which is used for constructing database connection strings and managing
different dialects.
"""

from pytest import fixture

from alexlib.auth import Curl


@fixture(scope="module")
def curl():
    return Curl(
        username="testuser",
        password="testpass",
        host="localhost",
        port=5432,
        database="testdb",
        dialect="postgres",
    )


def test_instantiation(curl: Curl):
    assert isinstance(curl, Curl)
    assert isinstance(curl.username, str)
    assert isinstance(curl.password, str)
    assert isinstance(curl.host, str)
    assert isinstance(curl.port, int)
    assert isinstance(curl.database, str)


def test_connection_string_generation(curl: Curl):
    assert str(curl) == "postgresql+psycopg://testuser:testpass@localhost:5432/testdb"


def test_alternate_dialect(curl: Curl):
    curl.dialect = "mysql"
    assert str(curl).startswith("mysql+mysqldb")


def test_canping(curl: Curl):
    assert isinstance(
        curl.canping, bool
    ), f"canping should be a boolean but is {type(curl.canping)}"
    assert curl.host, f"host should not be empty but is {curl.host}"
    assert curl.port, f"port should not be empty but is {curl.port}"
    assert curl.canping is True, "canping should be True if host and port are not empty"


def test_login(curl: Curl):
    assert isinstance(curl.login, str)
    assert curl.login == "testuser:testpass"


def test_hostport(curl: Curl):
    assert isinstance(curl.hostport, str)
    assert curl.hostport == "localhost:5432"


def test_db(curl: Curl):
    assert isinstance(curl.database, str)
    assert curl.database == "testdb"

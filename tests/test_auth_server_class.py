"""
Unit tests for the Server class in the alexlib.auth module.

This test module focuses on testing the random generation methods
and the representation method of the Server class. It ensures that
the random generation methods return values in the expected format
and that the representation method correctly represents a Server object.
"""

from re import match

from pytest import fixture

from alexlib.auth import Server


@fixture(scope="module")
def ip() -> str:
    return Server.rand_ip()


@fixture(scope="module")
def addr() -> str:
    return Server.rand_addr()


@fixture(scope="module")
def host() -> str:
    return Server.rand_host()


@fixture(scope="module")
def port() -> int:
    return Server.rand_port()


@fixture(scope="module")
def rand_server() -> Server:
    return Server.rand()


@fixture(scope="module")
def regular_server() -> Server:
    return Server("127.0.0.1", 8080)


def test_rand_ip(ip: str):
    """Test the rand_ip method for generating a valid IP address."""
    # Check if the IP address is in the correct format
    assert match(r"\d{3}\.\d{3}\.\d\.\d{3}", ip)


def test_rand_addr(addr: str):
    """Test the rand_addr method for generating a valid address."""
    # Check if the address is in the correct format
    assert match(r"postgres\.(dev|test|prod)\.\w{6}\.(local|remote)", addr)


def test_rand_host(host: str):
    """Test the rand_host method for generating a valid host name."""
    # The host can be either an IP address or an address
    assert match(r"\d{3}\.\d{3}\.\d\.\d{3}", host) or match(
        r"postgres\.(dev|test|prod)\.\w{6}\.(local|remote)", host
    )


def test_rand_port(port: int):
    """Test the rand_port method for generating a valid port number."""
    # Check if the port is in the correct range
    assert 1000 <= port <= 9999


def test_rand_method(rand_server: Server):
    """Test the rand method for creating a valid Server object."""
    assert isinstance(rand_server, Server)


def test_repr_method(regular_server: Server):
    """Test the __repr__ method for the Server class."""
    assert isinstance(regular_server, Server)
    assert repr(regular_server) == "Server(127.0.0.1:8080)"

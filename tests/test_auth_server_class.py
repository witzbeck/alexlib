"""
Unit tests for the Server class in the alexlib.auth module.

This test module focuses on testing the random generation methods
and the representation method of the Server class. It ensures that
the random generation methods return values in the expected format
and that the representation method correctly represents a Server object.
"""

from unittest import TestCase, main
from re import match
from alexlib.auth import Server


class TestServerClass(TestCase):
    """Test cases for the Server class in alexlib.auth."""

    def test_rand_ip(self):
        """Test the rand_ip method for generating a valid IP address."""
        ip = Server.rand_ip()
        # Check if the IP address is in the correct format
        self.assertTrue(match(r"\d{3}\.\d{3}\.\d\.\d{3}", ip))

    def test_rand_addr(self):
        """Test the rand_addr method for generating a valid address."""
        addr = Server.rand_addr()
        # Check if the address is in the correct format
        self.assertTrue(
            match(r"postgres\.(dev|test|prod)\.\w{6}\.(local|remote)", addr)
        )

    def test_rand_host(self):
        """Test the rand_host method for generating a valid host name."""
        host = Server.rand_host()
        # The host can be either an IP address or an address
        self.assertTrue(
            match(r"\d{3}\.\d{3}\.\d\.\d{3}", host)
            or match(r"postgres\.(dev|test|prod)\.\w{6}\.(local|remote)", host)
        )

    def test_rand_port(self):
        """Test the rand_port method for generating a valid port number."""
        port = Server.rand_port()
        # Check if the port is in the correct range
        self.assertTrue(1000 <= port <= 9999)

    def test_rand_method(self):
        """Test the rand method for creating a valid Server object."""
        server = Server.rand()
        self.assertIsInstance(server, Server)

    def test_repr_method(self):
        """Test the __repr__ method for the Server class."""
        server = Server("127.0.0.1", 8080)
        self.assertEqual(repr(server), "Server(127.0.0.1:8080)")


if __name__ == "__main__":
    main()

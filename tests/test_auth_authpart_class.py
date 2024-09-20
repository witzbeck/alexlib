"""Tests for the AuthPart class and its subclasses."""

from alexlib.auth import AuthPart, Login, Password, Server, Username


def test_auth_part(auth_part: AuthPart):
    assert issubclass(auth_part.__class__, AuthPart)
    assert len(auth_part.name) == len(auth_part)


def test_auth_part_repr(auth_part: AuthPart):
    assert auth_part.__class__.__name__ in repr(auth_part)


def test_login(login: Login):
    assert isinstance(login, Login)
    assert isinstance(login.user, Username)
    assert isinstance(login.pw, Password)


def test_server(server: Server):
    assert isinstance(server, Server)
    assert isinstance(server.host, str)
    assert isinstance(server.port, int)

"""
Unit tests for the AuthGenerator class in the alexlib.auth module.

This test module provides a comprehensive suite of tests for ensuring the correct functionality of the AuthGenerator class, including instantiation, template generation, and the generation of Auth objects from templates.
"""

from pathlib import Path

from pytest import fixture, mark, FixtureRequest
from alexlib.auth import AuthGenerator, Auth

from alexlib.crypto import SecretValue


@fixture(
    scope="session",
    params=(
        "remote.dev.postgres",
        "remote.prod.postgres",
        "local.dev.postgres",
        "local.prod.postgres",
        "remote.dev.mysql",
        "remote.prod.mysql",
        "local.dev.mysql",
        "local.prod.mysql",
    ),
)
def auth_key(request: FixtureRequest) -> str:
    return request.param


@fixture(scope="session")
def auth_template_path(test_dir: Path):
    test_path = test_dir / "test_template.json"
    return test_path


@fixture(scope="session")
def auth_generator(auth_template_path: Path):
    return AuthGenerator(
        name="test_template",
        path=auth_template_path,
        locales=("remote", "local"),
        envs=("dev", "prod"),
        databases=("postgres", "mysql"),
    )


@fixture(scope="session")
def auth_templates(auth_generator: AuthGenerator) -> dict[str, dict[str, str]]:
    return auth_generator.mk_all_templates()


@fixture(scope="session")
def auth_objects(auth_templates: dict[str, dict[str, str]]) -> dict[str, Auth]:
    return {
        key: Auth.from_dict(key, template) for key, template in auth_templates.items()
    }


@fixture(scope="session")
def auth_object(auth_objects: dict[str, Auth], auth_key: str) -> Auth:
    return auth_objects[auth_key]


def test_auth_generator_init(auth_generator: AuthGenerator):
    assert isinstance(auth_generator, AuthGenerator)


def test_auth_template_path(auth_generator: AuthGenerator, auth_template_path: Path):
    assert auth_generator.path == auth_template_path
    assert isinstance(auth_generator.path, Path)
    assert auth_generator.path.exists()


def test_auth_templates(auth_templates: dict[str, dict[str, str]], auth_key: str):
    assert auth_key in auth_templates
    template = auth_templates[auth_key]
    assert isinstance(template, dict)
    assert len(template) == 7


def test_auth_object_is_auth(auth_object: Auth):
    assert isinstance(auth_object, Auth)


@mark.parametrize("attr", ("username", "password", "host", "port", "database"))
def test_auth_object_attrs(attr: str, auth_object: Auth):
    assert hasattr(auth_object, attr)
    assert isinstance(getattr(auth_object, attr), SecretValue)

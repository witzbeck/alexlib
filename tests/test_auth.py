"""
Unit tests for the AuthGenerator class in the alexlib.auth module.

This test module provides a comprehensive suite of tests for ensuring the correct functionality of the AuthGenerator class, including instantiation, template generation, and the generation of Auth objects from templates.
"""

from pathlib import Path
from re import match

from pytest import FixtureRequest, fixture, mark, raises
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

from alexlib.auth import (
    Auth,
    AuthGenerator,
    AuthPart,
    Curl,
    Login,
    Password,
    SecretStore,
    Server,
    Username,
)
from alexlib.crypto import Cryptographer, SecretValue


@fixture(
    scope="module",
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


@fixture(scope="module")
def auth_template_path(dir_path: Path):
    test_path = dir_path / "test_template.json"
    return test_path


@fixture(scope="module")
def auth_generator(auth_template_path: Path):
    return AuthGenerator(
        name="test_template",
        path=auth_template_path,
        locales=("remote", "local"),
        envs=("dev", "prod"),
        databases=("postgres", "mysql"),
    )


@fixture(scope="module")
def auth_templates(auth_generator: AuthGenerator) -> dict[str, dict[str, str]]:
    return auth_generator.mk_all_templates()


@fixture(scope="module")
def auth_template(
    auth_templates: dict[str, dict[str, str]], auth_key: str
) -> dict[str, str]:
    return auth_key, auth_templates[auth_key]


@fixture(scope="module")
def auth_object(auth_template: dict[str, str]) -> dict[str, Auth]:
    auth_key, template = auth_template
    return Auth.from_dict(auth_key, template)


def test_auth_generator_init(auth_generator: AuthGenerator):
    assert isinstance(auth_generator, AuthGenerator)


def test_auth_template_path(auth_generator: AuthGenerator, auth_template_path: Path):
    assert auth_generator.path == auth_template_path
    assert isinstance(auth_generator.path, Path)
    assert auth_generator.path.exists()


@mark.slow
def test_auth_templates(auth_template: tuple[str, dict[str, str]]):
    key, template = auth_template
    assert isinstance(key, str)
    assert isinstance(template, dict)
    assert len(template) == 7


def test_auth_object_is_auth(auth_object: Auth):
    assert isinstance(auth_object, Auth)


@mark.slow
@mark.parametrize("attr", ("username", "password", "host", "port", "database"))
def test_auth_object_attrs(attr: str, auth_object: Auth):
    assert hasattr(auth_object, attr)
    assert isinstance(getattr(auth_object, attr), SecretValue)


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


def test_auth_init(auth: Auth):
    """Test the initialization of an Auth object."""
    assert isinstance(auth, Auth)


def test_auth_name(auth: Auth):
    """Test the `name` attribute of an Auth object."""
    assert auth.name == "test_auth"
    assert isinstance(auth.name, str)


def test_auth_keypath(auth: Auth):
    """Test the `keypath` attribute of an Auth object."""
    assert auth.keypath.exists()
    assert isinstance(auth.keypath, Path)


def test_auth_storepath(auth: Auth):
    """Test the `storepath` attribute of an Auth object."""
    assert auth.storepath.exists()
    assert isinstance(auth.storepath, Path)


def test_update_value(auth: Auth):
    """Test the `update_value` method of an Auth object."""
    auth.update_value("new_key", "new_value")
    assert str(auth.store.get_cred("new_key")) == "new_value"


def test_update_values(auth: Auth):
    """Test the `update_values` method of an Auth object."""
    updates = {"key1": "value1", "key2": "value2"}
    auth.update_values(updates)
    assert all(str(auth.store.get_cred(key)) == value for key, value in updates.items())


def test_auth_curl(auth: Auth):
    """Test the `curl` attribute of an Auth object."""
    assert isinstance(auth.curl, Curl)


def test_auth_basic(auth: Auth):
    """Test the `basic` attribute of an Auth object."""
    assert isinstance(auth.basic, HTTPBasicAuth)


def test_auth_digest(auth: Auth):
    """Test the `digest` attribute of an Auth object."""
    assert isinstance(auth.digest, HTTPDigestAuth)


def test_auth_from_nonexistent_path():
    """Test the `from_path` class method of the Auth class with a nonexistent path."""
    with raises(FileNotFoundError):
        Auth.from_path(Path("nonexistent_path"))


def test_updating_credentials_in_Auth(auth: Auth, auth_path: Path):
    """Test updating credentials in the Auth class."""
    auth.store.path = auth_path

    # Updating credentials
    auth.update_value("username", "user2")
    auth.update_value("password", "pass2")

    # Verifying updates
    updated_username = auth.run_getattr("get_username")
    updated_password = auth.run_getattr("get_password")

    assert str(updated_username) == "user2", f"Expected user2, got {updated_username}"
    assert str(updated_password) == "pass2", f"Expected pass2, got {updated_password}"
    assert (
        repr(updated_password) == "<SecretValue>"
    ), f"Expected <SecretValue>, got {updated_password}"


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


def test_curl_login(curl: Curl):
    assert isinstance(curl.login, str)
    assert curl.login == "testuser:testpass"


def test_hostport(curl: Curl):
    assert isinstance(curl.hostport, str)
    assert curl.hostport == "localhost:5432"


def test_db(curl: Curl):
    assert isinstance(curl.database, str)
    assert curl.database == "testdb"


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


def test_storing_and_retrieving_secrets_repr_protected_by_default(
    secret_store: SecretStore,
):
    """Test that secrets can be stored and retrieved correctly."""
    assert all(
        str(secret_store.get_cred(key)) != value
        for key, value in secret_store.secrets.items()
    ), secret_store.secrets


def test_storing_and_retrieving_secrets(secret_store: SecretStore):
    """Test that secrets can be stored and retrieved correctly."""
    assert all(
        str(secret_store.get_cred(key)) == str(value)
        for key, value in secret_store.secrets.items()
    ), secret_store.secrets


@mark.parametrize("secret", ("test_secret", "another_secret"))
def test_encryption_and_decryption(cryptographer: Cryptographer, secret: str):
    """Test that secrets are correctly encrypted and decrypted."""
    encrypted = cryptographer.encrypt_str(secret)
    decrypted = cryptographer.decrypt_str(encrypted)
    assert decrypted == secret, f"Expected {secret}, got {decrypted}"


def test_secret_store_len(secret_store: SecretStore):
    """Test that the __len__ method returns the correct number of secrets."""
    assert len(secret_store) == len(secret_store.secrets)


def test_secret_store_repr(secret_store: SecretStore):
    """Test that the __repr__ method returns the correct representation."""
    representation = repr(secret_store)
    assert all(key in representation for key in secret_store.secrets.keys())


@mark.parametrize("value", ("test_value", "another_value"))
def test_secret_store_sensor_input(secret_store: SecretStore, value: str):
    """Test that the sensor_input method returns the correct value."""
    sensored_value = secret_store.sensor_input("input")
    assert sensored_value != value
    assert "*" in sensored_value


def test_authpart_str_method(auth_part: AuthPart):
    """Test the __str__ method for the AuthPart class."""
    assert isinstance(str(auth_part), str)


@fixture(scope="module")
def rand_login() -> Login:
    return Login.rand()


def test_login_rand_init(rand_login: Login):
    """Test the rand method for the Login class."""
    assert isinstance(rand_login, Login)


def test_login_rand_user(rand_login: Login):
    """Test the rand method for the Login class."""
    assert isinstance(rand_login.user, Username)


def test_login_rand_password(rand_login: Login):
    """Test the rand method for the Login class."""
    assert isinstance(rand_login.pw, Password)


def test_curl_repr_method(curl: Curl):
    """Test the __repr__ method for the Curl class."""
    assert isinstance(repr(curl), str)


def test_curl_clsname(curl: Curl):
    """Test the __class__.__name__ attribute for the Curl class."""
    assert isinstance(str(curl), str)


def test_curl_without_login():
    """Test the Curl class without a login."""
    curl = Curl(host="localhost", port=5432, database="testdb")
    assert isinstance(curl, Curl)
    assert curl.login == ""


def test_curl_without_port():
    """Test the Curl class without a port."""
    curl = Curl(host="localhost", database="testdb")
    assert isinstance(curl, Curl)
    assert curl.port is None
    assert curl.hostport == "localhost"


def test_curl_mssql():
    """Test the Curl class with an MSSQL database."""
    curl = Curl(host="localhost", port=1433, database="testdb", dialect="mssql")
    assert isinstance(curl, Curl)
    assert curl.dialect == "mssql"
    assert str(curl).startswith("mssql+pyodbc")


def test_curl_postgres():
    """Test the Curl class with a PostgreSQL database."""
    curl = Curl(host="localhost", port=5432, database="testdb", dialect="postgres")
    assert isinstance(curl, Curl)
    assert curl.dialect == "postgres"
    assert str(curl).startswith("postgresql+psycopg")

from pytest import FixtureRequest, fixture, mark

from alexlib.auth import Cryptographer, SecretStore


@fixture(
    scope="module",
    params=(
        {"username": "user", "password": "pass"},
        {"key1": "value1", "key2": "value2"},
    ),
)
def secrets(request: FixtureRequest) -> dict:
    return request.param


@fixture(scope="module")
def secret_store(secrets: dict) -> SecretStore:
    return SecretStore.from_dict(secrets)


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

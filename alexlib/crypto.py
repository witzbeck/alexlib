"""
This module provides a robust framework for managing and encrypting secret values in Python applications. It includes data structures and methods for securely handling sensitive data such as API keys, passwords, and cryptographic keys. The module is built using standard libraries and the cryptography package for enhanced security.

Classes:
- SecretValue: A data class for storing and handling secret values. It supports multiple types including strings, bytes, and file paths. It provides methods for type checking, conversion, and representation of secret values.
- secretdict: A dictionary subclass where keys are mapped to SecretValue instances. It includes mechanisms to convert standard dictionaries into secretdict instances, ensuring that all values are securely handled as SecretValue objects.
- Cryptographer: A class for encrypting and decrypting files. It utilizes the Fernet symmetric encryption system from the cryptography library. The class provides methods for key management, file encryption and decryption, and utility functions for reading and writing bytes to files.

Functions:
- mk_secretdict(dict): Converts a standard dictionary to a secretdict, ensuring all string values are converted to SecretValue instances.

Usage:
This module is designed to be used in applications where secure handling of sensitive data is critical. It simplifies the process of encrypting and decrypting data, managing cryptographic keys, and securely handling secret values in various formats.

Note:
It's important to handle instances of SecretValue with care, especially when converting to strings or bytes, to avoid unintentional exposure of sensitive data.
"""
from dataclasses import dataclass
from dataclasses import field
from functools import cached_property
from logging import debug
from logging import info
from pathlib import Path
from typing import Callable

from cryptography.fernet import Fernet


@dataclass(slots=True)
class SecretValue:
    """stores a secret value"""

    val: str | bytes | Path

    @property
    def clsname(self) -> str:
        """returns the class name"""
        return self.__class__.__name__

    def valistype(self, type_: object) -> bool:
        """returns True if the value is the given type"""
        return isinstance(self.val, type_)

    @property
    def isstr(self) -> bool:
        """returns True if the value is a string"""
        return self.valistype(str)

    @property
    def ispath(self) -> bool:
        """returns True if the value is a path"""
        return self.valistype(Path)

    @property
    def isbytes(self) -> bool:
        """returns True if the value is bytes"""
        return self.valistype(bytes)

    def __post_init__(self) -> None:
        """converts SecretValue to str"""
        if isinstance(self.val, SecretValue):
            self.val = str(self.val)

    def __repr__(self) -> str:
        """returns the class name"""
        return f"<{self.clsname}>"

    def __bytes__(self) -> bytes:
        """returns the value as bytes"""
        if self.val is None:
            ret = Fernet.generate_key()
        elif self.isstr:
            ret = self.val.encode()
        elif self.ispath:
            ret = self.val.read_bytes()
        elif self.isbytes:
            ret = self.val
        else:
            raise TypeError(f"cannot get bytes from {type(self.val)}")
        return ret

    def __str__(self) -> str:
        """returns the value as a string"""
        if self.val is None:
            ret = bytes(self).decode()
        elif self.isstr:
            ret = self.val
        elif self.ispath:
            ret = self.val.read_text()
        elif self.isbytes:
            ret = self.val.decode()
        else:
            raise TypeError(f"cannot get str from {type(self.val)}")
        return ret

    def __len__(self) -> int:
        """returns the length of the value"""
        return len(str(self))

    @property
    def as_pair(self) -> tuple[str, str]:
        """returns a tuple with the class name and the value"""
        return {self.clsname: str(self)}

    @classmethod
    def from_any(cls, obj: object, type_: type):
        """creates a new SecretValue from any object"""
        if not isinstance(obj, type_):
            try:
                obj = type_(obj)
            except ValueError:
                raise TypeError(f"{type(obj)} {obj} must be {type_}")
        return cls(obj)

    @classmethod
    def from_path(cls, path: Path):
        """creates a new SecretValue from a path"""
        if not path.exists():
            raise FileExistsError(path)
        return cls.from_any(path, Path)

    @classmethod
    def from_bytes(cls, b: bytes):
        """creates a new SecretValue from bytes"""
        return cls.from_any(b, bytes)

    @classmethod
    def new_key(cls):
        """creates a new SecretValue from a new key"""
        return cls.from_bytes(Fernet.generate_key())

    @classmethod
    def from_str(cls, s: str):
        """creates a new SecretValue from a string"""
        return cls.from_any(s, str)

    @classmethod
    def from_user(cls):
        """creates a new SecretValue from user input"""
        return cls.from_str(input(f"enter {cls.__name__.lower()}"))

    @cached_property
    def api_key_header(self) -> dict[str, str]:
        """returns a dict with the api key header"""
        return {"x-api-key": str(self)}


def mk_secretdict(dict_: dict) -> dict[str:SecretValue] | dict:
    """converts a dict to a secretdict"""
    return {
        k: SecretValue.from_str(v) if isinstance(v, str) else v
        for k, v in dict_.items()
    }


class SecretDict(dict):
    """dict with SecretValues"""

    def __init__(self, *args, **kwargs) -> None:
        """creates a new SecretDict"""
        super().__init__(*args, **kwargs)

    @classmethod
    def from_dict(cls, d: dict):
        """creates a new SecretDict from a dict"""
        return cls(
            {
                k: SecretValue.from_str(v) if isinstance(v, str) else v
                for k, v in d.items()
            }
        )


@dataclass
class Cryptographer:
    """encrypts and decrypts files"""

    key: SecretValue = field(default=None, repr=False)
    encoding: str = field(default="utf-8")

    @property
    def fernet(self) -> Fernet:
        """creates fernet object"""
        try:
            ret = Fernet(bytes(self.key))
        except ValueError:
            ret = Fernet(Fernet.generate_key())
        return ret

    @staticmethod
    def get_new_key() -> SecretValue:
        """generates new key"""
        debug("created new key")
        return SecretValue.from_bytes(Fernet.generate_key())

    def set_key(self, key: SecretValue) -> None:
        """sets key to new key"""
        self.key = key

    def reset_key(self) -> None:
        """resets key to new key"""
        self.set_key(Cryptographer.get_new_key())

    def encrypt_bytes(self, bytes_: bytes) -> bytes:
        """encrypts bytes"""
        return self.fernet.encrypt(bytes_)

    def encrypt_str(self, str_: str) -> bytes:
        """encrypts str"""
        return self.encrypt_bytes(str_.encode(self.encoding))

    def decrypt_bytes(self, bytes_: bytes) -> bytes:
        """decrypts bytes"""
        return self.fernet.decrypt(bytes_)

    def decrypt_str(self, bytes_: bytes) -> str:
        """decrypts bytes to str"""
        return self.decrypt_bytes(bytes_).decode(self.encoding)

    @staticmethod
    def read_bytes(path: Path) -> bytes:
        """reads bytes from path"""
        if not isinstance(path, Path):
            raise TypeError("input must be Path")
        try:
            ret = path.read_bytes()
            info(f"{path} read as bytes")
        except TypeError:
            ret = path.read_text().encode()
            info(f"{path} converted to bytes from text")
        return ret

    @staticmethod
    def write_bytes(bytes_: bytes, path: Path) -> Path:
        """writes bytes to path"""
        if not isinstance(bytes_, bytes):
            raise TypeError("bytes_ must be bytes")
        if not isinstance(path, Path):
            raise TypeError("path must be Path")
        path.write_bytes(bytes_)

    @staticmethod
    def crypt_file(path: Path, crypt_func: Callable) -> None:
        """encrypts or decrypts a file"""
        bytes_ = Cryptographer.read_bytes(path)
        info(f"{path} bytes read")

        crypt_bytes = crypt_func(bytes_)
        info(f"{crypt_func.__name__} {path}")

        Cryptographer.write_bytes(crypt_bytes, path)
        info(f"{path} bytes written")

    def encrypt_file(self, path: Path) -> None:
        """encrypts a file"""
        Cryptographer.crypt_file(path, self.encrypt_bytes)

    def decrypt_file(self, path: Path) -> None:
        """decrypts a file"""
        Cryptographer.crypt_file(path, self.decrypt_bytes)

    @classmethod
    def from_key(
        cls,
        key: SecretValue | str | bytes | Path,
    ):
        """creates a new cryptographer with a given key"""
        return cls(key=SecretValue(key))

    @classmethod
    def new(cls):
        """creates a new cryptographer with a new key"""
        return cls.from_key(SecretValue.new_key())

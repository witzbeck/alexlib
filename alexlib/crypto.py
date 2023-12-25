from dataclasses import dataclass, field
from functools import cached_property
from logging import debug, info
from pathlib import Path
from typing import Callable

from cryptography.fernet import Fernet


@dataclass(slots=True)
class SecretValue:
    val: str | bytes | Path

    @property
    def clsname(self):
        return self.__class__.__name__

    def valistype(self, type_: object):
        return isinstance(self.val, type_)

    @property
    def isstr(self):
        return self.valistype(str)

    @property
    def ispath(self):
        return self.valistype(Path)

    @property
    def isbytes(self):
        return self.valistype(bytes)

    def __post_init__(self):
        if isinstance(self.val, SecretValue):
            self.val = str(self.val)

    def __repr__(self) -> str:
        return f"<{self.clsname}>"

    def __bytes__(self) -> bytes:
        if self.val is None:
            return Fernet.generate_key()
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
        return len(str(self))

    @cached_property
    def here(self):  # creates base path object
        return Path(eval("__file__"))

    @property
    def as_pair(self):
        return {self.clsname: self.__str__()}

    @classmethod
    def from_any(cls, obj: object, type_: type):
        if not isinstance(obj, type_):
            try:
                obj = type_(obj)
            except ValueError:
                raise TypeError(f"{type(obj)} {obj} must be {type_}")
        return cls(obj)

    @classmethod
    def from_path(cls, path: Path):
        c = cls.from_any(path, Path)
        if not path.exists():
            raise FileExistsError(path)
        else:
            return c

    @classmethod
    def from_bytes(cls, b: bytes):
        return cls.from_any(b, bytes)

    @classmethod
    def new_key(cls):
        return cls.from_bytes(Fernet.generate_key())

    @classmethod
    def from_str(cls, s: str):
        return cls.from_any(s, str)

    @classmethod
    def from_user(cls):
        return cls.from_str(input(f"enter {cls.__name__.lower()}"))

    @property
    def api_key_header(self):
        return {"x-api-key": self.__str__()}


def mk_secretdict(dict: dict) -> dict[str:SecretValue]:
    return {
        k: SecretValue.from_str(v) if isinstance(v, str) else v
        for k, v in dict.items()
    }


class secretdict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self = self.__dict__ = mk_secretdict(self)


@dataclass
class Cryptographer:
    key: SecretValue = field(default=None, repr=False)
    encoding: str = field(default="utf-8")

    @property
    def fernet(self) -> Fernet:
        try:
            ret = Fernet(self.key.__bytes__())
        except ValueError:
            ret = Fernet(Fernet.generate_key())
        return ret

    @staticmethod
    def get_new_key() -> SecretValue:
        debug("created new key")
        return SecretValue.from_bytes(Fernet.generate_key())

    def set_key(self, key: SecretValue) -> None:
        self.key = key

    def reset_key(self):
        self.set_key(Cryptographer.get_new_key())

    @property
    def encrypt_func(self):
        return self.fernet.encrypt

    @property
    def decrypt_func(self):
        return self.fernet.decrypt

    def encrypt_bytes(self, bytes_: bytes) -> bytes:
        return self.encrypt_func(bytes_)

    def decrypt_bytes(self, bytes_: bytes) -> bytes:
        return self.decrypt_func(bytes_)

    @staticmethod
    def read_bytes(path: Path) -> bytes:
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
        if not isinstance(bytes_, bytes):
            raise TypeError("bytes_ must be bytes")
        if not isinstance(path, Path):
            raise TypeError("path must be Path")
        path.write_bytes(bytes_)

    @staticmethod
    def crypt_file(path: Path, crypt_func: Callable):
        bytes_ = Cryptographer.read_bytes(path)
        info(f"{path} bytes read")

        crypt_bytes = crypt_func(bytes_)
        info(f"{crypt_func.__name__} {path}")

        Cryptographer.write_bytes(crypt_bytes, path)
        info(f"{path} bytes written")

    def encrypt_file(self, path: Path) -> None:
        Cryptographer.crypt_file(path, self.encrypt_bytes)

    def decrypt_file(self, path: Path) -> None:
        Cryptographer.crypt_file(path, self.decrypt_bytes)

    @classmethod
    def from_key(
        cls,
        key: SecretValue | str | bytes | Path,
    ):
        return cls(key=SecretValue(key))

    @classmethod
    def new(cls):
        return cls.from_key(SecretValue.new_key())

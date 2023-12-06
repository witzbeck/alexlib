from dataclasses import dataclass, field
from functools import cached_property, partial
from itertools import chain, product
from json import JSONDecodeError, dumps, load, loads
from logging import debug, info
from multiprocessing import Value
from pathlib import Path
from typing import Callable
from urllib.request import HTTPBasicAuthHandler, HTTPDigestAuthHandler

from cryptography.fernet import Fernet

from alexlib.db import Curl
from alexlib.file import File, Directory, path_search
"""
make entry script for auth that generates a csv to fill in after producing product of details for scaffolding from input.txt
generates all auth objects, creates store, then deletes self

"""

@dataclass(slots=True, frozen=True)
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


def mk_secret_dict(dict: dict) -> dict[str: SecretValue]:
    return {
        k: SecretValue.from_str(v) if isinstance(v, str) else v
        for k, v in dict.items()
    }


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


@dataclass
class SecretStore(File):
    secrets: dict[str: SecretValue] = field(default_factory=dict)

    @property
    def keys(self) -> list[str]:
        return list(self.secrets.keys())

    def __len__(self) -> int:
        return len(self.keys)

    def get_cred(self, key: str) -> str:
        return self.secrets.get(key)

    def __post_init__(self) -> None:
        self.secrets = SecretStore.encode_str_dict(self.secrets)
        if self.exists:
            super().__post_init__()

    @staticmethod
    def sensor_input(input: str, fill: str = "*"):
        input = str(input)
        len_ = len(input)
        if len_ < 3:
            ret = fill * len_
        else:
            first, last = input[0], input[-1]
            fill = fill * (len_ - 2)
            ret = f"{first}{fill}{last}"
        return ret

    def __repr__(self):
        clsname = self.__class__.__name__
        lines = "\n".join(
            [
                f"\t{key} = {SecretStore.sensor_input(self.secrets[key])}"
                for key in self.keys
            ]
        )
        return f"{clsname}(\n{lines}\n)"

    @staticmethod
    def encode_str_dict(dict_: dict):
        return {k: SecretValue.from_str(v) for k, v in dict_.items()}

    @classmethod
    def from_path(
        cls,
        path: Path,
        key: Path | SecretValue = None,
    ) -> dict[str:SecretValue]:
        if not isinstance(path, Path):
            raise TypeError("input must be path")
        elif key is not None:
            crypt = Cryptographer.from_key(key)
            bytes_ = crypt.decrypt_bytes(path.read_bytes())
            ret = loads(bytes_.decode())
        else:
            try:
                ret = load(path.read_bytes())
            except JSONDecodeError:
                ret = loads(path.read_text())
        str_dict = SecretStore.encode_str_dict(ret)
        return cls(secrets=str_dict, name=path.stem, path=path)

    @classmethod
    def from_user(
        cls,
        name: str = None,
        path: Path = None,
    ) -> dict[str:SecretValue]:
        ret, in_ = {}, " "
        while len(in_) > 0:
            key = input("enter credential key [<enter> to end]")
            if not key:
                break
            val = input("enter credential value [<enter> to end]")
            if not val:
                break
            in_ = ret[key] = SecretValue.from_str(val)
        return cls(secrets=ret, name=name, path=path)

    @property
    def str_secrets_dict(self):
        return {
            k: str(v) for k, v in self.secrets.items()
        }


@dataclass
class Auth:
    username: SecretValue = field(
        default=None,
        repr=False
    )
    password: SecretValue = field(
        default=None,
        repr=False
    )
    host: SecretValue = field(
        default=None,
        repr=False
    )
    port: SecretValue = field(
        default=None,
        repr=False
    )
    database: SecretValue = field(
        default=None,
        repr=False
    )

    @property
    def clsname(self) -> str:
        return self.__class__.__name__

    @property
    def hostparts(self) -> list[str]:
        return self.host.split(".") if self.host else []

    @property
    def hashost(self) -> bool:
        return bool(self.host)

    @property
    def env(self) -> str:
        try:
            return self.hostparts[1]
        except IndexError:
            return self.hostparts[0] if self.hashost else ""

    def __repr__(self):
        lines = [x for x in [self.username, self.env, self.database] if x]
        return f"{self.clsname}(\n{"\n\t".join(lines)}\n)"


    @cached_property
    def curl(self) -> str:
        return str(
            Curl(
                username=self.username,
                password=self.password,
                host=self.host,
                port=self.port,
                database=self.database,
            )
        )

    @cached_property
    def basicauth(self):
        return HTTPBasicAuthHandler(
            self.username,
            self.password,
        )

    @cached_property
    def digestauth(self):
        return HTTPDigestAuthHandler(self.username, self.password)


@dataclass
class TrustedAuth(Auth):
    def __post_init__(self):
        if self.username:
            raise ValueError(f"{self.clsname} cannot have username")
        if self.password:
            raise ValueError(f"{self.clsname} cannot have password")

@dataclass
class AuthHandler:
    name: str = field()
    store: SecretStore = field(default=None, repr=False)
    crypt: Cryptographer = field(init=False, repr=False)
    from_user: bool = field(default=False, repr=False)
    path: Path = field(default=None, repr=False)
    """ accesses or creates encrypted credentials
    """

    def __repr__(self):
        clsname = self.__class__.__name__
        lines = "\n\t".join(
            [
                f"\tname =  {self.name}",
                f"nsecrets =  {len(self.store)}",
                f"storepath =  {self.storepath}",
            ]
        )
        return f"{clsname}(\n{lines}\n)"

    @property
    def hasname(self):
        return self.name is not None

    @property
    def haskey(self):
        return self.key is not None

    @property
    def hasstore(self):
        return self.store is not None

    @property
    def hascrypt(self):
        return hasattr(self, "crypt")

    @cached_property
    def keyname(self):
        end = ".key"
        if self.name.endswith(end):
            ret = self.name
        else:
            ret = f"{self.name}{end}"
        return ret

    @cached_property
    def keypath(self):
        return self.dirpath / self.keyname

    @cached_property
    def storename(self):
        end = ".store"
        if self.name.endswith(end):
            ret = self.name
        else:
            ret = f"{self.name}{end}"
        return ret

    @property
    def hasstorepath(self):
        return False if not self.hasstore else self.store.haspath

    @cached_property
    def here(self) -> Path:  # creates base path object
        return Path(eval("__file__"))

    @cached_property
    def dirpath(self) -> Path:
        if self.path:
            ret = self.path
        elif "dailib" in self.here.parts:
            ret = path_search("resources")
        elif self.hasstorepath:
            ret = self.store.parent
        else:
            ret = self.here.parent
        if isinstance(ret, Path) or isinstance(ret, Directory):
            return ret
        else:
            raise TypeError(f"{ret} should be Path or Directory")

    @cached_property
    def storepath(self):
        if self.store is None:
            ret = self.dirpath / self.storename
        elif self.store.haspath:
            ret = self.store.path
        elif self.store is not None:
            ret = self.dirpath / self.storename
        else:
            raise ValueError("store exists but has not path")
        return ret

    @property
    def key(self) -> SecretValue:
        if self.hascrypt:
            ret = self.crypt.key
        elif self.keypath.exists():
            ret = SecretValue.from_path(self.keypath)
        else:
            ret = SecretValue.new_key()
        return ret

    def get_store(self) -> SecretValue:
        isstore = isinstance(self.store, SecretStore)
        ispath = isinstance(self.store, Path)
        if self.from_user:
            ret = SecretStore.from_user(name=self.name, path=self.storepath)
        elif isstore:
            ret = self.store
        elif ispath:
            ret = SecretStore.from_path(self.store, key=self.key)
        elif self.storepath.exists():
            ret = SecretStore.from_path(self.storepath, key=self.key)
        else:
            ret = SecretStore(name=self.name)
        return ret

    def set_store(self):
        self.store = self.get_store()

    def get_crypt(self) -> Cryptographer:
        try:
            ret = Cryptographer.from_key(self.key)
        except ValueError:
            ret = Cryptographer.new()
        return ret

    def set_crypt(self) -> None:
        self.crypt = self.get_crypt()

    def get_secret_bytes(self):
        return dumps(self.store.str_secrets_dict).encode()

    @staticmethod
    def write_file(to_write: bytes | str, path: Path) -> None:
        isbytes = isinstance(to_write, bytes)
        isstr = isinstance(to_write, str)
        if not (isbytes or isstr):
            raise TypeError(f"{to_write} must be str or bytes")
        elif not isinstance(path, Path):
            raise TypeError("path must be Path")
        if isbytes:
            path.write_bytes(to_write)
        elif isstr:
            path.write_text(to_write)
        if not path.exists():
            raise FileExistsError(f"{type(to_write)} not written")

    def write_store(self):
        encrypted_bytes = self.crypt.encrypt_bytes(self.get_secret_bytes())
        AuthHandler.write_file(encrypted_bytes, self.storepath)

    def write_key(self):
        AuthHandler.write_file(str(self.crypt.key), self.keypath)

    def write_files(self):
        self.write_store()
        self.write_key()

    def reencrypt_files(self):
        self.crypt.reset_key()
        self.write_files()

    def set_get_attrs(self):
        [
            setattr(self, f"get_{key}", partial(self.store.get_cred, key=key))
            for key in self.store.keys
        ]

    def run_getattr(self, attr: str):
        ret = getattr(self, attr)()
        if ret is None:
            raise AttributeError(f"{attr} returned None")
        else:
            return ret

    @cached_property
    def username(self) -> str:
        return self.run_getattr("get_username")

    @cached_property
    def password(self) -> str:
        return self.run_getattr("get_password")

    @cached_property
    def host(self) -> str:
        return self.run_getattr("get_host")

    @cached_property
    def port(self) -> int:
        return self.run_getattr("get_port")

    @cached_property
    def database(self) -> str:
        return self.run_getattr("get_database")

    @cached_property
    def curl(self) -> str:
        return str(
            Curl(
                username=self.username,
                password=self.password,
                host=self.host,
                port=self.port,
                database=self.database,
            )
        )

    @cached_property
    def basicauth(self):
        u, p = self.user, self.pw
        return HTTPBasicAuthHandler(
            u,
            p,
        )

    @cached_property
    def digestauth(self):
        u, p = self.user, self.pw
        return HTTPDigestAuthHandler(u, p)

    def __post_init__(self):
        self.set_crypt()
        self.set_store()
        self.set_get_attrs()
        if not (self.storepath.exists() and self.keypath.exists()):
            self.write_files()
        elif self.from_user:
            self.write_files()
        if self.store.secrets and self.hasstorepath:
            self.reencrypt_files()

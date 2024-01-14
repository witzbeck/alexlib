from dataclasses import dataclass, field
from functools import cached_property, partial
from itertools import product
from json import dump, dumps, loads
from pathlib import Path
from typing import Callable
from random import choice, randint

from requests.auth import HTTPBasicAuth, HTTPDigestAuth

from alexlib.core import read_json
from alexlib.constants import creds
from alexlib.crypto import Cryptographer, SecretValue
from alexlib.fake import RandGen
from alexlib.files import File


@dataclass
class AuthPart:
    name: str
    length: int = field(default=10)
    randsrc: Callable = field(default=RandGen.randlet)

    @property
    def randfunc(self):
        return partial(self.randsrc, n=self.length)

    @classmethod
    def rand(cls):
        return cls(cls.randfunc())

    @property
    def clsname(self) -> str:
        return self.__class__.__name__

    def __repr__(self):
        return f"{self.clsname}({self.name})"


@dataclass
class Username(AuthPart):
    length: int = field(default=6)


@dataclass
class Password(AuthPart):
    length: int = field(default=12)
    randsrc: Callable = field(default=RandGen.randprint)


@dataclass
class Login:
    user: Username
    pw: Password

    @classmethod
    def rand(cls):
        return cls(Username.rand(), Password.rand())


@dataclass
class Server:
    host: str
    port: int

    @property
    def clsname(self) -> str:
        return self.__class__.__name__

    @staticmethod
    def rand_ip() -> str:
        return ".".join(
            [
                str(randint(180, 199)),
                str(randint(160, 179)),
                RandGen.randintstr(n=1),
                RandGen.randintstr(n=3),
            ]
        )

    @staticmethod
    def rand_addr() -> str:
        return ".".join(
            [
                "postgres",
                choice(["dev", "test", "prod"]),
                RandGen.randlet(n=6),
                choice(["local", "remote"]),
            ]
        )

    @staticmethod
    def rand_host() -> str:
        return choice([Server.rand_ip, Server.rand_addr])()

    @staticmethod
    def rand_port() -> int:
        return randint(1000, 9999)

    @classmethod
    def rand(cls):
        return cls(cls.rand_host(), cls.rand_port())

    def __repr__(self) -> str:
        return f"{self.clsname}({self.host}:{self.port})"


@dataclass
class Curl:
    username: str = field(default=None, repr=False)
    password: str = field(default=None, repr=False)
    host: str = field(default=None)
    port: int = field(default=None, repr=False)
    database: str = field(default=None)
    dialect: str = field(default="postgres", repr=False)
    sid: str = field(default=None, repr=False)

    @property
    def clsname(self) -> str:
        return self.__class__.__name__

    def __repr__(self) -> str:
        return str(self)

    @property
    def dialect_map(self):
        return {
            "postgres": "postgresql+psycopg://",
            "oracle": "oracle+oracledb://",
            "mssql": "mssql+pyodbc://",
            "mysql": "mysql+mysqldb://",
            "sqlite": "sqlite:///",
        }

    @property
    def canping(self):
        return self.host and self.port

    @property
    def system(self):
        return self.dialect_map[self.dialect]

    @property
    def login(self):
        if self.username and self.password:
            ret = f"{self.username}:{self.password}"
        elif self.username:
            ret = self.username
        else:
            ret = ""
        return ret

    @property
    def hostport(self):
        if not self.host:
            ret = None
        elif not self.port:
            ret = self.host
        else:
            ret = f"{self.host}:{self.port}"
        return ret

    @property
    def dbstr(self):
        return f"/{self.database}" if self.database else ""

    @property
    def driverstr(self):
        return "?driver=SQL+Server" if self.dialect == "mssql" else ""

    def __str__(self):
        return "".join(
            [
                self.system,
                self.login,
                "@",
                self.hostport,
                self.dbstr,
                self.driverstr,
            ]
        )

    @cached_property
    def postgres(self) -> str:
        deets = [
            f"dbname={self.database}",
            f"host={self.host}",
            f"port={self.port}",
            f"user={self.username}",
        ]
        if self.password:
            deets.append(f"password={self.password}")
        return " ".join(deets)


@dataclass
class SecretStore(File):
    secrets: dict[str:SecretValue] = field(default_factory=dict)

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
    def from_dict(
        cls,
        dict_: dict[str:str],
        name: Path = None,
        path: Path = None,
    ):
        return cls(
            secrets=cls.encode_str_dict(dict_),
            name=name,
            path=path,
        )

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
            read_json(path)
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
    def str_secrets_dict(self) -> dict[str:str]:
        return {k: str(v) for k, v in self.secrets.items()}


@dataclass
class Auth:
    name: str = field()
    store: SecretStore = field(default=None, repr=False)
    crypt: Cryptographer = field(init=False, repr=False)
    """ accesses or creates encrypted credentials
    """

    @property
    def clsname(self):
        return self.__class__.__name__

    def __repr__(self):
        return f"{self.clsname}({self.name})"

    @property
    def haskey(self) -> bool:
        return self.key is not None

    @property
    def hasstore(self) -> bool:
        return self.store is not None

    @property
    def hascrypt(self) -> bool:
        return hasattr(self, "crypt")

    @property
    def keyname(self) -> str:
        return f"{self.name}.key"

    @property
    def keypath(self) -> Path:
        return creds / self.keyname

    @property
    def storename(self) -> str:
        return f"{self.name}.store"

    @property
    def storepath(self) -> Path:
        return creds / self.storename

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
        if isstore:
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
        Auth.write_file(encrypted_bytes, self.storepath)

    def write_key(self):
        Auth.write_file(str(self.crypt.key), self.keypath)

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

    @property
    def username(self) -> str:
        return self.run_getattr("get_username")

    @property
    def password(self) -> str:
        return self.run_getattr("get_password")

    @property
    def host(self) -> str:
        return self.run_getattr("get_host")

    @property
    def port(self) -> int:
        return self.run_getattr("get_port")

    @property
    def database(self) -> str:
        return self.run_getattr("get_database")

    @property
    def curl(self) -> Curl:
        return Curl(
            username=self.username,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.database,
        )

    @cached_property
    def pg_curl(self) -> str:
        return self.curl.postgres

    @cached_property
    def basicauth(self):
        u, p = self.username, self.password
        return HTTPBasicAuth(u, p)

    @cached_property
    def digestauth(self):
        u, p = self.username, self.password
        return HTTPDigestAuth(u, p)

    def __post_init__(self):
        if isinstance(self.name, list):
            self.name = ".".join(self.name)
        elif isinstance(self.name, tuple):
            try:
                self.name = ".".join(self.name)
            except TypeError:
                self.name = ".".join(self.name[0])
        if not self.hasstore and not self.storepath.exists():
            raise ValueError("must have store or storepath")
        self.set_crypt()
        self.set_store()
        self.set_get_attrs()
        if not (self.storepath.exists() and self.keypath.exists()):
            self.write_files()
        if self.store.secrets:
            self.reencrypt_files()

    def update_value(self, key: str, value: str) -> None:
        self.store.secrets[key] = SecretValue.from_str(value)
        self.write_store()

    def update_values(self, dict_: dict[str:str]) -> None:
        for k, v in dict_.items():
            self.update_value(k, v)

    def rename(self, name: str) -> None:
        self.name = name
        self.write_files()

    @classmethod
    def from_dict(cls, name: str, dict_: dict[str:str]):
        crypt = Cryptographer.new()
        store_path = creds / f"{name}.store"
        store = SecretStore.from_dict(dict_, path=store_path, key=crypt.key)
        return cls(name=name, store=store, crypt=crypt)

    @classmethod
    def from_path(
        cls,
        path: Path,
        key: Path | SecretValue = None,
    ):
        name = ".".join(path.name.split(".")[:-1])
        auth = Auth.from_dict(name, read_json(path))
        return cls(auth=auth, path=path, key=key)


@dataclass
class AuthGenerator:
    name: str = field(default="auth_template")
    path: Path = field(default=None, repr=False)
    locales: list[str] = field(default_factory=list, repr=False)
    envs: list[str] = field(default_factory=list, repr=False)
    databases: list[str] = field(default_factory=list, repr=False)
    from_user: bool = field(default=False, repr=False)
    overwrite: bool = field(default=False, repr=False)
    """ generates all auth objects, creates store, then deletes self
    """

    @property
    def def_auth_dict(self) -> dict[str : list[str]]:
        return {
            k: v
            for k, v in {
                "locale": self.locales,
                "env": self.envs,
                "database": self.databases,
            }.items()
            if v
        }

    @property
    def def_auth_keys(self) -> dict[str:list]:
        return self.def_auth_dict.keys()

    @staticmethod
    def get_auth_template() -> dict[str:str]:
        return {
            "username": "",
            "password": "",
            "host": "",
            "port": "",
            "system": "",
            "option": "",
        }

    @staticmethod
    def mk_product_dict(**kwargs) -> dict[str:list]:
        keys, vals = kwargs.keys(), kwargs.values()
        return {".".join(inst): dict(zip(keys, inst)) for inst in product(*vals)}

    def mk_all_templates(self) -> dict[str:dict]:
        tmp = AuthGenerator.get_auth_template()
        pdict = AuthGenerator.mk_product_dict(**self.def_auth_dict)
        for d in pdict.values():
            d.update(tmp)
        return pdict

    @cached_property
    def here(self):
        return Path(eval("__file__")).parent

    @staticmethod
    def to_json(dict_: dict[str:str], path: Path) -> None:
        dump(dict_, path.open("w"), indent=4)

    def write_template_file(self) -> None:
        AuthGenerator.to_json(self.mk_all_templates(), self.path)

    @property
    def pathexists(self) -> bool:
        return self.path.exists()

    @property
    def towrite(self) -> bool:
        return (not self.pathexists) or self.overwrite

    def __post_init__(self) -> None:
        if self.path is None:
            self.path = self.here / f"{self.name}.json"
        if self.towrite:
            self.write_template_file()

    @property
    def schema(self) -> list[str]:
        return ["locales", "envs", "databases"]

    @staticmethod
    def generate(
        template_path: Path = Path("_auth_template.json"),
        creds_path: Path = Path.home() / ".creds",
    ) -> list[Auth]:
        print(creds_path)
        auths = read_json(template_path)
        for k, v in auths.items():
            store_path = creds_path / f"{k}.store"
            AuthGenerator.to_json(v, store_path)
            store = SecretStore.from_dict(v, path=store_path)
            handler = Auth(
                auth=Auth.from_dict(v),
                path=creds_path,
                store=store,
            )
            handler.crypt.reset_key()
            handler.write_files()
        return auths

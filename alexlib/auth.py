"""
This module provides a comprehensive framework for handling authentication and secret management in Python applications. It includes classes for generating and managing usernames, passwords, and server details, alongside tools for securely storing and retrieving credentials.

Features:
- `AuthPart`, `Username`, `Password`: Data classes for generating random usernames and passwords.
- `Login`: A data class for creating login credentials.
- `Server`: A class for generating random server hostnames and ports.
- `Curl`: A utility class for constructing database connection strings and managing different dialects.
- `SecretStore`: A class for managing encrypted storage of secrets.
- `Auth`: The main class for managing authentication, including encryption and storage of credentials.
- `AuthGenerator`: A class for generating authentication templates and initializing `Auth` objects.

The module uses `dataclasses` for structured data management, `functools` and `itertools` for functional programming constructs, and `json` and `pathlib` for file handling. It also integrates with the `alexlib` library for additional functionality like random generation and file management.

Usage:
This module is intended for developers who need to manage authentication and secrets in a secure and organized manner. It's particularly useful in scenarios where credentials need to be stored, retrieved, and used dynamically in a secure way.
"""
from ast import literal_eval
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import cached_property, partial
from itertools import product
from json import dump, dumps, loads
from pathlib import Path
from random import choice, randint

from requests.auth import HTTPBasicAuth, HTTPDigestAuth

from alexlib.constants import CREDS
from alexlib.core import chkenv, read_json
from alexlib.crypto import Cryptographer, SecretValue
from alexlib.fake import randlet, randprint, randdigit
from alexlib.files import File


@dataclass
class AuthPart:
    """constructs authentication parts"""

    name: str
    length: int = field(default=10)
    randsrc: Callable = field(default=randlet)

    @classmethod
    def rand(cls) -> "AuthPart":
        """returns a random AuthPart object"""
        return cls(cls.randsrc(n=cls.length))

    def __repr__(self) -> str:
        """returns the repr of the AuthPart object"""
        return f"{self.__class__.__name__}({self.name})"


@dataclass
class Username(AuthPart):
    """constructs username objects"""

    length: int = field(default=6)


@dataclass
class Password(AuthPart):
    """constructs password objects"""

    length: int = field(default=12)
    randsrc: Callable = field(default=randprint)


@dataclass
class Login:
    """constructs login objects"""

    user: Username
    pw: Password

    @classmethod
    def rand(cls):
        """returns a random Login object"""
        return cls(Username.rand(), Password.rand())


@dataclass
class Server:
    """constructs server objects"""

    host: str
    port: int

    @property
    def clsname(self) -> str:
        """returns the name of the Server class"""
        return self.__class__.__name__

    @staticmethod
    def rand_ip() -> str:
        """returns a random ip address"""
        return ".".join(
            [
                str(randint(180, 199)),
                str(randint(160, 179)),
                randdigit(n=1),
                randdigit(n=3),
            ]
        )

    @staticmethod
    def rand_addr() -> str:
        """returns a random address"""
        return ".".join(
            [
                "postgres",
                choice(["dev", "test", "prod"]),
                randlet(n=6),
                choice(["local", "remote"]),
            ]
        )

    @staticmethod
    def rand_host() -> str:
        """returns a random host name"""
        return choice([Server.rand_ip, Server.rand_addr])()

    @staticmethod
    def rand_port() -> int:
        """returns a random port number"""
        return randint(1000, 9999)

    @classmethod
    def rand(cls):
        """returns a random Server object"""
        return cls(cls.rand_host(), cls.rand_port())

    def __repr__(self) -> str:
        """returns the repr of the Server object"""
        return f"{self.clsname}({self.host}:{self.port})"


@dataclass
class Curl:
    """constructs database connection strings"""

    username: str = field(default=None, repr=False)
    password: str = field(default=None, repr=False)
    host: str = field(default=None)
    port: int = field(default=None, repr=False)
    database: str = field(default=None)
    dialect: str = field(default="postgres", repr=False)
    sid: str = field(default=None, repr=False)

    @property
    def clsname(self) -> str:
        """returns the name of the Curl class"""
        return self.__class__.__name__

    def __repr__(self) -> str:
        """returns the repr of the Curl object"""
        return str(self)

    @property
    def dialect_map(self) -> dict[str:str]:
        """returns a dict of dialects and connection strings"""
        return {
            "postgres": "postgresql+psycopg://",
            "oracle": "oracle+oracledb://",
            "mssql": "mssql+pyodbc://",
            "mysql": "mysql+mysqldb://",
            "sqlite": "sqlite:///",
        }

    @property
    def canping(self) -> bool:
        """returns True if host and port are not None"""
        return self.host and self.port

    @property
    def system(self) -> str:
        """returns a system string for connection urls"""
        return self.dialect_map[self.dialect]

    @property
    def login(self) -> str:
        """returns a username:password string for connection urls"""
        if self.username and self.password:
            ret = f"{self.username}:{self.password}"
        elif self.username:
            ret = self.username
        else:
            ret = ""
        return ret

    @property
    def hostport(self) -> str:
        """returns a host:port string for connection urls"""
        if not self.host:
            ret = None
        elif not self.port:
            ret = self.host
        else:
            ret = f"{self.host}:{self.port}"
        return ret

    @property
    def dbstr(self) -> str:
        """returns a database string for connection urls"""
        return f"/{self.database}" if self.database else ""

    @property
    def driverstr(self) -> str:
        """returns a driver string for mssql connection urls"""
        return "?driver=SQL+Server" if self.dialect == "mssql" else ""

    def __str__(self) -> str:
        """returns a connection string"""
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
    def mssql(self) -> str:
        """returns a mssql connection string"""
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
        """returns a postgres connection string"""
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
    """stores encrypted secrets"""

    secrets: dict[str:SecretValue] = field(default_factory=dict)

    @property
    def keys(self) -> list[str]:
        """returns a list of credential keys"""
        return list(self.secrets.keys())

    def __len__(self) -> int:
        """returns the number of credentials"""
        return len(self.keys)

    def get_cred(self, key: str) -> str:
        """returns a credential value"""
        return self.secrets.get(key)

    def __post_init__(self) -> None:
        """creates a SecretStore object"""
        self.secrets = SecretStore.encode_str_dict(self.secrets)
        if self.exists:
            super().__post_init__()

    @staticmethod
    def sensor_input(input_: str, fill: str = "*") -> str:
        """returns a string with the first and last characters visible"""
        input_ = str(input_) if not isinstance(input_, str) else input_
        len_ = len(input_)
        if len_ < 3:
            ret = fill * len_
        else:
            first, last = input_[0], input_[-1]
            fill = fill * (len_ - 2)
            ret = f"{first}{fill}{last}"
        return ret

    def __repr__(self) -> str:
        """returns the repr of the SecretStore object"""
        clsname = self.__class__.__name__
        lines = "\n".join(
            [
                f"\t{key} = {SecretStore.sensor_input(self.secrets[key])}"
                for key in self.keys
            ]
        )
        return f"{clsname}(\n{lines}\n)"

    @staticmethod
    def encode_str_dict(dict_: dict) -> dict[str:SecretValue]:
        """encodes a dict of strings to a dict of SecretValues"""
        return {k: SecretValue.from_str(v) for k, v in dict_.items()}

    @classmethod
    def from_dict(
        cls,
        dict_: dict[str:str],
        name: Path = None,
        path: Path = None,
    ) -> "SecretStore":
        """creates a SecretStore object from a dict"""
        return cls(
            secrets=cls.encode_str_dict(dict_),
            name=name,
            path=path,
        )

    # pylint: disable=arguments-differ
    @classmethod
    def from_path(
        cls,
        path: Path,
        key: Path | SecretValue = None,
    ) -> dict[str:SecretValue]:
        """creates a SecretStore object from a path"""
        if not isinstance(path, Path):
            raise TypeError("input must be path")
        if key is not None:
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
        """creates a SecretStore object from user input"""
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
        """returns a dict of secrets as strings"""
        return {k: str(v) for k, v in self.secrets.items()}


@dataclass
class Auth:
    """accesses or creates encrypted credentials"""

    name: str = field()
    store: SecretStore = field(default=None, repr=False)
    crypt: Cryptographer = field(init=False, repr=False)

    @property
    def clsname(self) -> str:
        """returns the name of the auth class"""
        return self.__class__.__name__

    def __repr__(self) -> str:
        """returns the repr of the auth object"""
        return f"{self.clsname}({self.name})"

    @property
    def haskey(self) -> bool:
        """returns True if key attribute exists"""
        return self.key is not None

    @property
    def hasstore(self) -> bool:
        """returns True if store attribute exists"""
        return self.store is not None

    @property
    def hascrypt(self) -> bool:
        """returns True if crypt attribute exists"""
        return hasattr(self, "crypt")

    @property
    def keyname(self) -> str:
        """returns the name of the key file"""
        return f"{self.name}.key"

    @property
    def keypath(self) -> Path:
        """returns the path to the key file"""
        return CREDS / self.keyname

    @property
    def storename(self) -> str:
        """returns the name of the store file"""
        return f"{self.name}.store"

    @property
    def storepath(self) -> Path:
        """returns the path to the store file"""
        return CREDS / self.storename

    @property
    def key(self) -> SecretValue:
        """returns a SecretValue object"""
        if self.hascrypt:
            ret = self.crypt.key
        elif self.keypath.exists():
            ret = SecretValue.from_path(self.keypath)
        else:
            ret = SecretValue.new_key()
        return ret

    def get_store(self) -> SecretValue:
        """returns a SecretStore object"""
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

    def set_store(self) -> None:
        """sets the store attribute"""
        self.store = self.get_store()

    def get_crypt(self) -> Cryptographer:
        """returns a Cryptographer object"""
        try:
            ret = Cryptographer.from_key(self.key)
        except ValueError:
            ret = Cryptographer.new()
        return ret

    def set_crypt(self) -> None:
        """sets the crypt attribute"""
        self.crypt = self.get_crypt()

    def get_secret_bytes(self) -> bytes:
        """returns the encrypted store as bytes"""
        return dumps(self.store.str_secrets_dict).encode()

    @staticmethod
    def write_file(to_write: bytes | str, path: Path) -> None:
        """writes bytes or str to path"""
        isbytes = isinstance(to_write, bytes)
        isstr = isinstance(to_write, str)
        if not (isbytes or isstr):
            raise TypeError(f"{to_write} must be str or bytes")
        if not isinstance(path, Path):
            raise TypeError("path must be Path")
        if isbytes:
            path.write_bytes(to_write)
        elif isstr:
            path.write_text(to_write)
        if not path.exists():
            raise FileExistsError(f"{type(to_write)} not written")

    def write_store(self) -> None:
        """writes the store file"""
        encrypted_bytes = self.crypt.encrypt_bytes(self.get_secret_bytes())
        Auth.write_file(encrypted_bytes, self.storepath)

    def write_key(self) -> None:
        """writes the key file"""
        Auth.write_file(str(self.crypt.key), self.keypath)

    def write_files(self) -> None:
        """writes the store and key files"""
        self.write_store()
        self.write_key()

    def reencrypt_files(self) -> None:
        """re-encrypts the store and key files"""
        self.crypt.reset_key()
        self.write_files()

    def set_get_attrs(self) -> list[Callable]:
        """sets get_attr methods"""
        return [
            setattr(self, f"get_{key}", partial(self.store.get_cred, key=key))
            for key in self.store.keys
        ]

    def run_getattr(self, attr: str) -> str:
        """runs a get_attr method"""
        ret = getattr(self, attr)()
        if ret is None:
            raise AttributeError(f"{attr} returned None")
        return ret

    @property
    def username(self) -> str:
        """returns the username"""
        return self.run_getattr("get_username")

    @property
    def password(self) -> str:
        """returns the password"""
        return self.run_getattr("get_password")

    @property
    def host(self) -> str:
        """returns the host name"""
        return self.run_getattr("get_host")

    @property
    def port(self) -> int:
        """returns the port number"""
        return self.run_getattr("get_port")

    @property
    def database(self) -> str:
        """returns the database name"""
        return self.run_getattr("get_database")

    @property
    def curl(self) -> Curl:
        """returns a Curl object"""
        return Curl(
            username=self.username,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.database,
        )

    @cached_property
    def pg_curl(self) -> str:
        """returns a postgres connection string"""
        return self.curl.postgres

    @cached_property
    def basic(self) -> HTTPBasicAuth:
        """returns a basic auth object"""
        u, p = self.username, self.password
        return HTTPBasicAuth(u, p)

    @cached_property
    def digest(self) -> HTTPDigestAuth:
        """returns a digest auth object"""
        u, p = self.username, self.password
        return HTTPDigestAuth(u, p)

    def __post_init__(self) -> None:
        """creates an auth object"""
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
        """updates a value in the auth object"""
        self.store.secrets[key] = SecretValue.from_str(value)
        self.write_store()

    def update_values(self, dict_: dict[str:str]) -> None:
        """updates the auth object with a dict"""
        for k, v in dict_.items():
            self.update_value(k, v)

    def rename(self, name: str) -> None:
        """renames the auth object"""
        self.name = name
        self.write_files()

    @classmethod
    def from_dict(cls, name: str, dict_: dict[str:str]) -> "Auth":
        """returns an Auth object from a dict"""
        store_path = CREDS / f"{name}.store"
        store = SecretStore.from_dict(dict_, path=store_path)
        return cls(name, store=store)

    @classmethod
    def from_path(
        cls,
        path: Path,
        key: Path | SecretValue = None,
    ) -> "Auth":
        """returns an Auth object from a path"""
        name = ".".join(path.name.split(".")[:-1])
        crypt = Cryptographer.from_key(key) if key else Cryptographer.new()
        store = SecretStore.from_path(path, key=crypt.key)
        return cls(name, store=store)

    @classmethod
    def from_env(cls, key: str = "AUTH") -> "Auth":
        """returns an Auth object from an environment variable"""
        return cls.from_path(Path(f"{chkenv(key)}.key"))


@dataclass
class AuthGenerator:
    """generates an auth template file"""

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
        """returns the default auth dict"""
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
        """returns the keys defining an auth object's name"""
        return self.def_auth_dict.keys()

    @cached_property
    def auth_template(self) -> dict[str:str]:
        """returns a dict of possible auth fields"""
        return {
            "username": "",
            "password": "",
            "host": "",
            "port": "",
            "database": "",
        }

    @staticmethod
    def mk_product_dict(**kwargs) -> dict[str:list]:
        """returns a dict of all possible auth templates"""
        keys, vals = kwargs.keys(), kwargs.values()
        return {".".join(inst): dict(zip(keys, inst)) for inst in product(*vals)}

    def mk_all_templates(self) -> dict[str:dict]:
        """returns a dict of all possible auth templates"""
        tmp = AuthGenerator.auth_template
        pdict = AuthGenerator.mk_product_dict(**self.def_auth_dict)
        for d in pdict.values():
            d.update(tmp)
        return pdict

    @cached_property
    def here(self) -> Path:
        """returns the directory of this file"""
        return Path(literal_eval("__file__")).parent

    @staticmethod
    def to_json(dict_: dict[str:str], path: Path) -> None:
        """writes dict to path"""
        dump(dict_, path.open("w"), indent=4)

    def write_template_file(self) -> None:
        """writes template file to path"""
        AuthGenerator.to_json(self.mk_all_templates(), self.path)

    @property
    def pathexists(self) -> bool:
        """returns True if template file exists"""
        return self.path.exists()

    @property
    def towrite(self) -> bool:
        """returns True if template file should be written"""
        return (not self.pathexists) or self.overwrite

    def __post_init__(self) -> None:
        """writes the template file to path"""
        if self.path is None:
            self.path = self.here / f"{self.name}.json"
        if self.towrite:
            self.write_template_file()

    @property
    def schema(self) -> list[str]:
        """returns the schema for the template file"""
        return ["locales", "envs", "databases"]

    @staticmethod
    def generate(
        template_path: Path = Path("_auth_template.json"),
    ) -> list[Auth]:
        """generates auth objects from template file"""
        auths = read_json(template_path)
        for k, v in auths.items():
            store_path = CREDS / f"{k}.store"
            AuthGenerator.to_json(v, store_path)
            store = SecretStore.from_dict(v, path=store_path)
            handler = Auth(
                name=k,
                store=store,
            )
            handler.crypt.reset_key()
            handler.write_files()
        return auths

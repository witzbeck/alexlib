
from dataclasses import dataclass, field
from functools import cached_property, partial
from itertools import product
from json import dump, dumps, loads
from pathlib import Path
from string import ascii_lowercase
from typing import Callable
from urllib.request import HTTPBasicAuthHandler, HTTPDigestAuthHandler
from random import choice, randint

from alexlib.core import read_json, chkenv
from alexlib.config import Settings
from alexlib.crypto import Cryptographer, SecretValue
from alexlib.fake import RandGen
from alexlib.file import File, Directory, path_search
"""
Generator
make entry script for auth
generates a json to fill in
product of details for scaffolding

Executor
generates all auth objects,
creates store,
then deletes self

locale.env.database.key
locale.env.database.store

"""
if (nameismain := __name__ == "__main__"):
    settings = Settings()


creds_path = Path.home() / ".creds"
ndevs = 6
n = ascii_lowercase[13]

databases = chkenv("databases", ifnull=["learning"], astype=list)
systems = ["postgres"]
devs = [
    f"dev{x}" if ndevs > 1 else "dev"
    for x in ascii_lowercase[-ndevs:]
]
envs = devs + ["test", "prod"]

locales = [
    "local",
    "remote"
]

rand_system = partial(choice, systems)
rand_env = partial(choice, envs)
rand_db = partial(choice, databases)


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
        return ".".join([
            str(randint(180, 199)),
            str(randint(160, 179)),
            RandGen.randintstr(n=1),
            RandGen.randintstr(n=3),
        ])

    @staticmethod
    def rand_addr() -> str:
        return ".".join([
            choice(systems),
            choice(envs),
            RandGen.randlet(n=6),
            choice(["local", "remote"])
        ])

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
    def dialect_map(self):
        return {
            "postgres": "postgresql+psycopg://",
            "oracle": "oracle+oracledb://",
            "mssql": "mssql+pyodbc://",
            "mysql": "mysql+mysqldb://",
            "sqlite": "sqlite:///",
        }

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


@dataclass
class Auth:
    locale: str = field(default=None, repr=False)
    env: str = field(default=None, repr=False)
    database: str = field(default=None, repr=False)
    username: str = field(default=None, repr=False)
    password: str = field(default=None, repr=False)
    host: str = field(default=None, repr=False)
    port: int = field(default=None, repr=False)
    system: str = field(default=None, repr=False)
    sid: str = field(default=None, repr=False)
    option: str = field(default=None, repr=False)

    @property
    def def_attrs(self) -> list[str]:
        return ["name", "env"]

    @property
    def defname(self) -> str:
        return f"{self.env}:{self.database}"

    @cached_property
    def curl(self) -> Curl:
        return Curl(
            username=self.username,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.database,
        )

    @cached_property
    def pg_cstr(self):
        deets = [
            f"dbname={self.database}",
            f"host={self.host}",
            f"port={self.port}",
            f"user={self.username}",
        ]
        if self.password:
            deets.append(f"password={self.password}")
        return " ".join(deets)

    @property
    def isoracle(self) -> bool:
        return self.system == "oracle"

    def set_option(self, option: str) -> None:
        if self.isoracle:
            self.sid = option

    @classmethod
    def rand(cls):
        return cls(
            system=rand_system(),
            env=rand_env(),
            username=Username.rand(),
            password=Password.rand(),
            host=Server.rand_host(),
            port=Server.rand_port(),
            database=rand_db(),
        )

    @property
    def clsname(self) -> str:
        return self.__class__.__name__

    @property
    def hostparts(self) -> list[str]:
        host = self.host
        return host.split(".") if host else []

    @property
    def hashost(self) -> bool:
        return bool(self.host)

    def __repr__(self):
        loc = f"{self.locale}:" if self.locale else ""
        d = self.database if self.database else self.system
        return f"{self.clsname}({loc}{self.env}:{d})"

    @cached_property
    def basicauth(self) -> HTTPBasicAuthHandler:
        return HTTPBasicAuthHandler(self.username, self.password)

    @cached_property
    def digestauth(self) -> HTTPDigestAuthHandler:
        return HTTPDigestAuthHandler(self.username, self.password)

    @classmethod
    def from_dict(cls, dict_: dict):
        return cls(**dict_)


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
    def from_dict(
        cls,
        dict_: dict[str: str],
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
    def str_secrets_dict(self):
        return {k: str(v) for k, v in self.secrets.items()}


@dataclass
class TrustedAuth(Auth):
    def __post_init__(self):
        if self.username:
            raise ValueError(f"{self.clsname} cannot have username")
        if self.password:
            raise ValueError(f"{self.clsname} cannot have password")


@dataclass
class AuthHandler:
    auth: Auth = field(default=None)
    store: SecretStore = field(default=None, repr=False)
    crypt: Cryptographer = field(init=False, repr=False)
    from_user: bool = field(default=False, repr=False)
    path: Path = field(default=creds_path, repr=False)
    """ accesses or creates encrypted credentials
    """

    def __repr__(self):
        clsname = self.__class__.__name__
        db = self.database if self.database else self.system
        lines = "\n\t".join(
            [
                f"\tenv:db =  {self.env}:{db}",
                f"nsecrets =  {len(self.store)}",
                f"storepath =  {self.storepath}",
            ]
        )
        return f"{clsname}(\n{lines}\n)"

    @property
    def name(self) -> bool:
        ds = self.auth.database if self.auth.database else self.auth.system
        return ".".join([
            x for x in [self.auth.locale, self.auth.env, ds] if x
        ])

    @property
    def hasname(self) -> bool:
        return bool(self.name)

    @property
    def haskey(self) -> bool:
        return self.key is not None

    @property
    def hasstore(self) -> bool:
        return self.store is not None

    @property
    def hascrypt(self) -> bool:
        return hasattr(self, "crypt")

    @cached_property
    def keyname(self) -> str:
        end = ".key"
        if self.name.endswith(end):
            ret = self.name
        else:
            ret = f"{self.name}{end}"
        return ret

    @cached_property
    def keypath(self) -> Path:
        return self.dirpath / self.keyname

    @cached_property
    def storename(self) -> str:
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
        elif "alexlib" in self.here.parts:
            ret = path_search(".creds")
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
        u, p = self.username, self.password
        return HTTPBasicAuthHandler(u, p)

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

    @classmethod
    def from_path(
        cls,
        path: Path,
        key: Path | SecretValue = None,
    ):
        auth = Auth.from_dict(read_json(path))
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
    def def_auth_dict(self) -> dict[str: list[str]]:
        return {k: v for k, v in {
            "locale": self.locales,
            "env": self.envs,
            "database": self.databases,
        }.items() if v}

    @property
    def def_auth_keys(self) -> dict[str: list]:
        return self.def_auth_dict.keys()

    @staticmethod
    def get_auth_template() -> dict[str: str]:
        return {
            "username": "",
            "password": "",
            "host": "",
            "port": "",
            "system": "",
            "option": "",
        }

    @staticmethod
    def mk_product_dict(**kwargs) -> dict[str: list]:
        keys, vals = kwargs.keys(), kwargs.values()
        return {
            ".".join(inst): dict(zip(keys, inst))
            for inst in product(*vals)
        }

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
    def to_json(dict_: dict[str: str], path: Path) -> None:
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
            handler = AuthHandler(
                auth=Auth.from_dict(v),
                path=creds_path,
                store=store,
            )
            handler.crypt.reset_key()
            handler.write_files()
        return auths


def getauth(*args) -> Auth:
    if isinstance(args, str):
        name = args
    elif isinstance(args, tuple):
        try:
            name = ".".join(args)
        except TypeError:
            name = ".".join(args[0])
    store_path = creds_path / f"{name}.store"
    key_path = creds_path / f"{name}.key"
    crypt = Cryptographer.from_key(key_path)
    store = SecretStore.from_path(store_path, key=crypt.key)
    return Auth.from_dict(store.secrets)


togen = False
if nameismain:
    if togen:
        AuthGenerator(
            envs=envs,
            databases=databases,
            locales=locales,
        ).write_template_file()
        print(AuthGenerator.generate())
    print(getauth("remote", "dev", "learning").curl)

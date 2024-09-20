"""This module contains all the API objects used in the library"""

from dataclasses import dataclass, field
from functools import cached_property

from requests.auth import HTTPBasicAuth


@dataclass(slots=True)
class ApiRequest:
    """Base class for all API requests"""

    url: str
    headers: dict = field(default_factory=dict, repr=False)
    params: dict = field(default_factory=dict, repr=False)
    data: dict = field(default_factory=dict, repr=False)
    json: dict = field(default_factory=dict, repr=False)
    files: dict = field(default_factory=dict, repr=False)
    auth: HTTPBasicAuth = field(default=None, repr=False)
    timeout: int = field(default=5, repr=False)

    def __post_init__(self):
        """Initializes the object"""
        self.headers.setdefault("Content-Type", "application/json")

    def __repr__(self) -> str:
        """Returns a string representation of the object"""
        return f"{self.__class__.__name__}({self.url})"


@dataclass
class ApiObject:
    """Base class for all API objects"""

    id: str = field(default=None)
    name: str = field(default=None)

    def __repr__(self) -> str:
        """Returns a string representation of the object"""
        return f"{self.__class__.__name__}({self.name})"

    @classmethod
    def from_dict(cls, d: dict):
        """Creates an instance from a dictionary"""
        d = {k: v for k, v in d.items() if not isinstance(v, dict)}
        _ = [d.update(v) for v in d.values() if isinstance(v, dict)]
        return cls(**d)


@dataclass
class AgentBase(ApiObject):
    """Base class for all API agents"""

    email: str = field(default=None)


@dataclass
class ClientBase(ApiObject):
    """Base class for all API clients"""

    host: str = field(default=None)
    token: str = field(default=None, repr=False)

    @cached_property
    def basic_auth(self) -> HTTPBasicAuth:
        """Returns basic authentication object"""
        return HTTPBasicAuth("", self.token)

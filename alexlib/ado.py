from dataclasses import dataclass, field
from alexlib.__init__ import dotenv

from requests import get, post
from requests.auth import HTTPBasicAuth

from alexlib.core import show_dict, chkenv

dotenv


@dataclass
class AdoAuth:
    host: str
    org: str
    project: str
    token: str

    @property
    def basic(self) -> HTTPBasicAuth:
        return HTTPBasicAuth("", self.token)

    @classmethod
    def from_envs(
        cls,
        envs: list[str] = [
            "host",
            "org",
            "project",
            "token",
        ],
    ):
        envs = [chkenv(f"ado_{x}".upper()) for x in envs]
        return cls(*envs)


@dataclass
class ProductBacklogItem:
    id: int
    auth: AdoAuth = field(default_factory=AdoAuth.from_envs)
    api_version: str = field(default="6.0")
    resource_path: str = field(default="_apis/wit/workitems")

    @property
    def api_part(self) -> str:
        return f"?api-version={self.api_version}"

    @property
    def url(self) -> str:
        return "/".join([
            self.auth.host,
            self.auth.org,
            self.auth.project,
            self.resource_path,
            str(self.id),
        ]) + self.api_part

    @classmethod
    def from_env(cls, env: str = "ADO_PBI_ID", **kwargs):
        return cls(chkenv(env, astype=int), **kwargs)

    def get_json(self) -> dict:
        return get(self.url, auth=self.auth.basic).json()


if __name__ == "__main__":
    pbi = ProductBacklogItem.from_env()
    print(pbi.url, "\n")
    d = pbi.get_json()["fields"]
    for k in d.keys():
        print(k)
    print()
    show_dict(d)

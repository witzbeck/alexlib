from dataclasses import dataclass
from pathlib import Path
from sys import path

from alexlib.constants import DOTENV_PATH, MODULE_PATH, PROJECT_PATH, PYPROJECT_PATH
from alexlib.files.utils import load_dotenv, read_toml

path.append(str(MODULE_PATH))
if DOTENV_PATH.exists():
    load_dotenv(DOTENV_PATH)


@dataclass(slots=True)
class Version:
    """data class for semantic versioning"""

    major: int
    minor: int
    patch: int
    project_name: str = PROJECT_PATH.name

    def __eq__(self, other: "Version") -> bool:
        return str(self) == str(other)

    @classmethod
    def from_str(cls, version: str, **kwargs) -> "Version":
        parts = version.split(".")
        return cls(*parts, **kwargs)

    @classmethod
    def from_pyproject(cls, path: Path = PYPROJECT_PATH) -> "Version":
        dict_ = read_toml(path)
        try:
            ret = dict_["project"]["version"]
        except KeyError:
            ret = dict_["tool"]["poetry"]["version"]
        return cls.from_str(ret, project_name=path.parent.name)

    def __iter__(self):
        """returns version as iterable"""
        return iter(
            [
                self.major,
                self.minor,
                self.patch,
            ]
        )

    def __str__(self) -> str:
        """returns version as string"""
        return ".".join(list(self))

    def __repr__(self) -> str:
        """displays project name and version as string"""
        return f"{self.project_name} v{str(self)}"

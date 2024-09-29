from dataclasses import dataclass
from pathlib import Path
from sys import path, version_info

from alexlib.constants import MODULE_PATH, PYPROJECT_PATH
from alexlib.files.utils import read_toml

path.append(str(MODULE_PATH))


@dataclass(slots=True)
class Version:
    """data class for semantic versioning"""

    major: int
    minor: int
    patch: int
    project_name: str = None

    def __eq__(self, other: "Version") -> bool:
        return str(self) == str(other)

    @classmethod
    def from_str(cls, version: str, **kwargs) -> "Version":
        parts = version.split(".")
        return cls(*parts, **kwargs)

    @classmethod
    def from_pyproject(cls, path: Path = PYPROJECT_PATH) -> "Version":
        if read_toml is None:
            raise ImportError("pyproject.toml support requires toml package")
        else:
            dict_ = read_toml(path)
        try:
            ret = dict_["project"]["version"]
        except KeyError:
            ret = dict_["tool"]["poetry"]["version"]
        return cls.from_str(ret, project_name=path.parent.name)

    @classmethod
    def from_sys(cls) -> "Version":
        return cls(*version_info[:3], project_name="Python")

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
        return ".".join([str(part) for part in self])

    def __repr__(self) -> str:
        """displays project name and version as string"""
        return f"{self.project_name} v{str(self)}"

    def __post_init__(self):
        """checks for valid version"""
        if not isinstance(self.major, int):
            self.major = int(self.major)
        if not isinstance(self.minor, int):
            self.minor = int(self.minor)
        if not isinstance(self.patch, int):
            self.patch = int(self.patch)

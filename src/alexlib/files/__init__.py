from collections.abc import Callable
from dataclasses import dataclass, field

from alexlib.files.objects import File
from alexlib.files.utils import read_json, read_toml


@dataclass
class JsonFile(File):
    """class for json files"""

    read: Callable = field(default=read_json, repr=False)

    def __post_init__(self) -> None:
        if not self.istype("json"):
            raise TypeError(f"{self.path} is not json")
        return super().__post_init__()


@dataclass
class TomlFile(File):
    """class for json files"""

    read: Callable = field(default=read_toml, repr=False)

    def __post_init__(self) -> None:
        if not self.istype("toml"):
            raise TypeError(f"{self.path} is not toml")
        return super().__post_init__()

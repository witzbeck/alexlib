from dataclasses import dataclass
from os import PathLike
from pathlib import Path

NBYTES_LABELS = ("bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
NBYTES_LABEL_MAP = {label: 1_000**i for i, label in enumerate(NBYTES_LABELS)}


@dataclass(frozen=True)
class FileSize:
    """size of a system object in bytes"""

    nbytes: int
    min_scale_level: int = 100
    roundto: int = 3

    @staticmethod
    def _get_nbytes_scaled(
        nbytes: int, min_scale_level: int = 100, roundto: int = 3
    ) -> tuple[str, int]:
        """determines filesize scale for label"""
        scaled = nbytes
        ret = "bytes", scaled
        for label, scale in NBYTES_LABEL_MAP.items():
            scaled = nbytes / scale
            if scaled < min_scale_level:
                ret = label, round(scaled, roundto)
                break
        return ret

    def __repr__(self) -> str:
        """scale file size representation"""
        label, scaled = FileSize._get_nbytes_scaled(
            self.nbytes, min_scale_level=self.min_scale_level, roundto=self.roundto
        )
        return f"{scaled} {label}"

    def __lt__(self, other: "FileSize") -> bool:
        if isinstance(other, FileSize):
            return self.nbytes < other.nbytes
        elif isinstance(other, (int, float)):
            return self.nbytes < other
        else:
            raise TypeError(f"{other} is {type(other)}, not FileSize or int")

    def __gt__(self, other: "FileSize") -> bool:
        if isinstance(other, FileSize):
            return self.nbytes > other.nbytes
        elif isinstance(other, (int, float)):
            return self.nbytes > other
        else:
            raise TypeError(f"{other} is {type(other)}, not FileSize or int")

    @classmethod
    def from_path(cls, path: Path) -> "FileSize":
        """filesize calc from path"""
        if not isinstance(path, Path):
            raise TypeError(f"{path} is {type(path)}, not Path")
        if not path.exists():
            raise ValueError(f"path {path} does not exist")
        return (
            cls(path.stat().st_size)
            if path.is_file()
            else sum(x.stat().st_size for x in path.iterdir() if x.is_file())
        )

    @classmethod
    def from_system_object(cls, obj: PathLike | object) -> "FileSize":
        """return formattable filesize obj from system object"""
        if issubclass(obj.__class__, PathLike):
            ret = cls.from_path(obj)
        elif obj.__class__.__name__ in ("SystemObject", "File", "Directory"):
            ret = cls(obj.size)
        else:
            raise TypeError(
                f"{obj} is {type(obj)}, not SystemObject subclass or PathLike"
            )
        return ret

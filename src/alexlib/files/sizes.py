from dataclasses import dataclass
from pathlib import Path

from alexlib.core import chktype

NBYTES_LABELS = ("bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
NBYTES_LABEL_MAP = {label: 1_000**i for i, label in enumerate(NBYTES_LABELS)}


def get_nbytes_scaled_comprehension(
    nbytes: int, min_scale_level: int = 100, roundto: int = 3
) -> tuple[str, float]:
    """Computes all possible scaled values and returns the appropriate one.

    Testing using alexlib.times module:
    Average time per loop: 44.486 μs"""
    scaled_values = {
        label: round(nbytes / scale, roundto)
        for label, scale in NBYTES_LABEL_MAP.items()
        if nbytes < scale * min_scale_level
    }
    key = list(scaled_values.keys())[0] if scaled_values else "bytes"
    return key, scaled_values.get(key, nbytes)


def get_nbytes_scaled_min_cycles(
    nbytes: int, min_scale_level: int = 100, roundto: int = 3
) -> tuple[str, float]:
    """Determines filesize scale for label efficiently

    Testing using alexlib.times module:
    Average time per loop: 12.673 μs
    """
    # If nbytes is less than the minimum scale level, return bytes
    if nbytes <= min_scale_level:
        return "bytes", nbytes
    # Iterate through the NBYTES_LABEL_MAP and return the first label that fits
    for label, scale in NBYTES_LABEL_MAP.items():
        scaled = nbytes / scale
        if scaled <= min_scale_level:
            return label, round(scaled, roundto)
    # If no label is found, return bytes as the default
    return "bytes", nbytes


@dataclass(frozen=True)
class FileSize:
    """size of a system object in bytes"""

    scaled: float
    label: str
    nbytes: int
    min_scale_level: int = 100
    roundto: int = 3

    def __repr__(self) -> str:
        """scale file size representation"""
        return f"{self.scaled} {self.label}"

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

    def __eq__(self, other: "FileSize") -> bool:
        if isinstance(other, FileSize):
            return self.nbytes == other.nbytes
        elif isinstance(other, (int, float)):
            return self.nbytes == other
        else:
            raise TypeError(f"{other} is {type(other)}, not FileSize or int")

    @classmethod
    def from_nbytes(
        cls, nbytes: int, min_scale_level: int = 100, roundto: int = 3
    ) -> "FileSize":
        """scale filesize from nbytes"""
        label, scaled = get_nbytes_scaled_min_cycles(
            nbytes, min_scale_level=min_scale_level, roundto=roundto
        )
        return cls(scaled, label, nbytes)

    @classmethod
    def from_path(cls, path: Path) -> "FileSize":
        """filesize calc from path"""
        chktype(path, Path, mustexist=True)
        nbytes = (
            path.stat().st_size
            if path.is_file()
            else sum(x.stat().st_size for x in path.rglob("*") if x.is_file())
        )
        return cls.from_nbytes(nbytes)

from dataclasses import dataclass
from datetime import datetime, timedelta
from os import stat_result
from pathlib import Path

from alexlib.constants import DATE_FORMAT, DATETIME_FORMAT


@dataclass(frozen=True)
class SystemTimestamp:
    """class for system timestamps"""

    timestamp: float

    @property
    def datetime(self) -> datetime:
        """gets timestamp datetime"""
        return datetime.fromtimestamp(self.timestamp)

    @property
    def strfdate(self) -> str:
        """gets timestamp strfdate"""
        return self.datetime.strftime(DATE_FORMAT)

    @property
    def strfdatetime(self) -> str:
        """gets timestamp strfdatetime"""
        return self.datetime.strftime(DATETIME_FORMAT)

    @property
    def delta(self) -> timedelta:
        """gets timestamp delta"""
        return datetime.now() - self.datetime

    def is_new_enough(self, min_delta: timedelta) -> bool:
        """checks if timestamp is new enough"""
        if not isinstance(min_delta, timedelta):
            raise TypeError(f"{min_delta} is not a timedelta")
        return self.delta < min_delta

    def __repr__(self) -> str:
        """gets timestamp representation"""
        return f"{self.__class__.__name__}({self.strfdatetime})"

    def __str__(self) -> str:
        """gets timestamp string"""
        return self.strfdatetime

    @classmethod
    def from_stat_result(cls, stat: stat_result) -> "SystemTimestamp":
        """creates system timestamp from stat result"""
        raise NotImplementedError("Subclasses must implement this method")

    @classmethod
    def from_path(cls, path: Path) -> "SystemTimestamp":
        """creates system timestamp from path"""
        return cls.from_stat_result(path.stat())


@dataclass(frozen=True)
class CreatedTimestamp(SystemTimestamp):
    """class for created timestamps"""

    @classmethod
    def from_stat_result(cls, stat: stat_result) -> "CreatedTimestamp":
        """creates created timestamp from stat result"""
        return cls(stat.st_ctime)


@dataclass(frozen=True)
class ModifiedTimestamp(SystemTimestamp):
    """class for modified timestamps"""

    @classmethod
    def from_stat_result(cls, stat: stat_result) -> "ModifiedTimestamp":
        """creates modified timestamp from stat result"""
        return cls(stat.st_mtime)

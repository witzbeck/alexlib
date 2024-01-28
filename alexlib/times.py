"""
This module provides custom implementations of the datetime and timedelta classes
from Python's standard library, along with utility functions and a decorator for
performance measurement.

Classes:
    CustomTimedelta: An enhanced version of the standard library's timedelta class,
                     providing additional methods such as random timedelta generation,
                     epoch time difference calculation, and rounding capabilities.
    CustomDatetime: An extended datetime class incorporating features for checking
                    holidays, business days, and generating random datetime instances.

Functions:
    get_rand_datetime(): Generates a random datetime object based on the CustomDatetime class.
    get_rand_timedelta(): Creates a random timedelta object using the CustomTimedelta class.
    timeit(func, *args, niter=None, **kwargs): A decorator to time the execution of a function,
                                               with the option to repeat the function call
                                               multiple times for averaging.

The module leverages external libraries such as pandas for handling specific date-time features
like business day calculations and US Federal Holiday determination. It is designed for
applications requiring custom date-time manipulations beyond the capabilities of the standard
datetime module.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import cached_property, partial
from logging import info
from math import floor
from os import getenv
from random import randint
from time import perf_counter
from collections.abc import Callable

from decorator import decorator
from pandas import Timestamp
from pandas.tseries.holiday import Holiday, USFederalHolidayCalendar
from pandas.tseries.offsets import BDay
from sqlalchemy import JSON, Column, DateTime, Integer, String, Float
from sqlalchemy.orm import declarative_base
from alexlib.constants import EPOCH_SECONDS

Base = declarative_base()

get_env_user = partial(getenv, "USER")


class CustomTimedelta(timedelta):
    """custom timedelta class with extra methods"""

    @classmethod
    def rand(cls) -> timedelta():
        """Generate a random timedelta object."""
        return cls(seconds=get_rand_timedelta().total_seconds())

    @property
    def epoch_self_dif(self) -> float:
        """returns the difference between the timedelta and epoch_seconds"""
        return self.total_seconds() - EPOCH_SECONDS

    @staticmethod
    def _find_smallest_unit(td: timedelta):
        """returns the smallest unit of time in a timedelta"""
        # Check each unit, starting from the largest to the smallest
        if td.days != 0:
            ret = "days"
        elif td.seconds != 0:
            ret = "seconds"
        elif td.microseconds != 0:
            ret = "microseconds"
        else:
            ret = "zero"  # Handle the case where timedelta is zero
        return ret

    def get_epoch_self_divmod(self, td: timedelta) -> tuple[float, float]:
        """returns the divmod of the timedelta and epoch_seconds"""
        return divmod(self.epoch_self_dif, td.total_seconds())

    def __round__(self, other: timedelta) -> timedelta:
        """rounds the timedelta to the nearest other"""
        diff = self.epoch_self_dif
        mod = diff % other.total_seconds()
        return self.__class__(seconds=diff - mod)


class CustomDatetime(datetime):
    """custom datetime class with extra methods"""

    @classmethod
    def rand(cls) -> datetime:
        """Generate a random datetime object."""
        return cls.fromtimestamp(get_rand_datetime().timestamp())

    @cached_property
    def holidays(self) -> list[Holiday]:
        """returns a list of US Federal Holidays"""
        return [x.date() for x in USFederalHolidayCalendar().holidays().to_pydatetime()]

    @property
    def isholiday(self) -> bool:
        """
        Check if the current date is a holiday.
        Returns:
            bool: True if the current date is a holiday, False otherwise.
        """
        return self.date() in self.holidays

    @property
    def isweekday(self) -> bool:
        """Check if the current date is a weekday."""
        return self.isoweekday() <= 5

    @property
    def isweekend(self) -> bool:
        """Check if the current date is a weekend."""
        return not self.isweekday

    @property
    def isbusinessday(self) -> bool:
        """Check if the current date is a business day."""
        return not (self.isholiday or self.isweekend)

    @property
    def yesterday(self) -> datetime:
        """returns the previous day"""
        return self - timedelta(days=1)

    @property
    def tomorrow(self) -> datetime:
        """returns the next day"""
        return self + timedelta(days=1)

    @cached_property
    def one_busday(self) -> BDay:
        """returns a pandas business day offset"""
        return BDay(1)

    def get_last_busday(self) -> datetime:
        """returns the last business day"""
        chkdate = Timestamp(self.yesterday)
        while chkdate in self.holidays:
            chkdate = chkdate - self.one_busday
        return chkdate.to_pydatetime()

    @property
    def epoch_self_dif(self) -> float:
        """returns the difference between the datetime and epoch_seconds"""
        return self.timestamp() - EPOCH_SECONDS

    def get_epoch_self_divmod(self, td: timedelta) -> tuple[float, float]:
        """returns the divmod of the datetime and epoch_seconds"""
        return divmod(self.epoch_self_dif, td.total_seconds())

    def __round__(self, td: timedelta) -> datetime:
        """rounds the datetime to the nearest td"""
        mod = self.epoch_self_dif % td.total_seconds()
        return self.fromtimestamp(EPOCH_SECONDS + self.epoch_self_dif - mod)


class Users(Base):
    """A user class for storing user information."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, default=get_env_user)


class TimerLog(Base):
    """A timer log class for storing timer logs."""

    __tablename__ = "timer_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True)
    action = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    duration = Column(Float, nullable=False)
    duration_unit = Column(String, nullable=False)
    additional_info = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        """Get the timer log representation."""
        attrs = "\n".join(
            [
                f"{key}: {val}"
                for key, val in {
                    "id": self.id,
                    "user_id": self.user_id,
                    "action": self.action,
                    "start_time": self.start_time,
                    "end_time": self.end_time,
                    "duration": self.duration,
                }.items()
                if val
            ]
        )
        return "\n".join([f"{self.__class__.__name__}(", attrs, ")"])


@dataclass(frozen=True)
class TimerLabel:
    """A timer label class for labeling timer records."""

    seconds: float
    label_dict: dict[str, str] = field(default_factory=dict)
    roundto: int = field(default=3, repr=False)
    minunit: float = field(default=0.1, repr=False)

    @staticmethod
    def _get_label_dict(
        seconds: float,
        minunit: float,
        label_dict: dict[str, str],
    ) -> dict[str, str]:
        """calculate the label dict"""
        minutes, seconds = divmod(seconds, 60)
        if (min_ := floor(minutes)) > 0:
            label_dict["min"] = min_
        if seconds > minunit:
            label_dict["sec"] = seconds
        elif (mili := seconds * 10e3) > minunit:
            label_dict["ms"] = mili
        elif (micro := seconds * 10e6) > minunit:
            label_dict["μs"] = micro
        else:
            label_dict["ns"] = seconds * 10e9
        if not label_dict:
            raise ValueError(f"label_dict is empty but seconds are {seconds}")
        return label_dict

    @staticmethod
    def _get_label_str(label_dict: dict[str, str], roundto: int) -> str:
        """calculate the label string"""
        return " ".join(
            [f"{round(val, roundto)} {key}" for key, val in label_dict.items()]
        )

    def __str__(self) -> str:
        """Get the timer label."""
        return TimerLabel._get_label_str(
            TimerLabel._get_label_dict(self.seconds, self.minunit, self.label_dict),
            self.roundto,
        )

    def __repr__(self) -> str:
        return str(self)


@dataclass(slots=True)
class Timer:
    """A timer class for measuring execution time."""

    start: float = field(default_factory=perf_counter, repr=False)
    record: list[float] = field(default_factory=list, repr=False)

    @staticmethod
    def _log_time(time: float, record: list[float]) -> None:
        """Log the time to the record."""
        record.append(time)
        return record

    def log_perf_counter(self) -> None:
        """Log the current time to the record."""
        self.record = Timer._log_time(perf_counter(), self.record)

    def __post_init__(self) -> None:
        """Initialize the timer."""
        self.record = Timer._log_time(self.start, self.record)

    @property
    def soft_last_record(self) -> float:
        """Get the most recent time without logging."""
        return self.record[-1]

    @property
    def hard_last_record(self) -> float:
        """Get the most recent time with logging."""
        ret = self.soft_last_record
        self.log_perf_counter()
        return ret

    @property
    def elapsed_from_start(self) -> float:
        """Get the elapsed time."""
        return self.hard_last_record - self.start

    @property
    def elapsed_from_start_label(self) -> TimerLabel:
        """Get the elapsed time representation."""
        return TimerLabel(self.elapsed_from_start)

    @property
    def elapsed_from_last(self) -> float:
        """Get the elapsed time."""
        soft = self.soft_last_record
        return self.hard_last_record - soft

    @property
    def elapsed_from_last_label(self) -> TimerLabel:
        """Get the elapsed time representation."""
        return TimerLabel(self.elapsed_from_last)

    def __enter__(self) -> "Timer":
        """Start the timer."""
        return self

    def __exit__(self, *args) -> None:
        """Stop the timer."""
        self.log_perf_counter()


@decorator
def timeit(func: Callable, *args, niter: int = None, **kwargs) -> None:
    """Decorator that times the execution of a function."""
    unit_index, threshold, roundto = 0, 0.09, 6
    units = ["s", "ms", "μs", "ns"]
    pc1 = perf_counter()
    result = func(*args, **kwargs) if niter is None else [func() for _ in range(niter)]
    dif = perf_counter() - pc1
    while dif <= threshold:
        unit_index += 1
        dif *= 10e3
    loopstr = f" in {niter} loops" if niter is not None else ""
    res = f"{str(round(dif, roundto))} {units[unit_index]}"
    msg = f"{func.__name__} took {res}{loopstr}"
    try:
        nres = len(result) if niter is None else sum(len(x) for x in result)
        msg = f"{msg} and returned {nres} results"
    except TypeError:
        info("timeit: result is not iterable")
    print(msg)
    return result


def get_rand_datetime() -> CustomDatetime:
    """Generate a random datetime object."""
    return CustomDatetime(
        randint(2, 3000),
        randint(1, 12),
        randint(1, 28),
        randint(0, 23),
        randint(0, 59),
        randint(0, 59),
        randint(0, 1000000),
    )


def get_rand_timedelta() -> CustomTimedelta:
    """Generate a random timedelta object."""
    return CustomTimedelta(
        weeks=randint(0, 100),
        days=randint(0, 30),
        hours=randint(0, 23),
        minutes=randint(0, 59),
        seconds=randint(0, 59),
        microseconds=randint(0, 1000000),
    )

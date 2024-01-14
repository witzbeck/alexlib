"""Module for custom datetime and timedelta classes."""
from datetime import datetime
from datetime import timedelta
from functools import cached_property
from logging import info
from random import randint
from time import perf_counter
from typing import Callable

from decorator import decorator
from pandas import Timestamp
from pandas.tseries.holiday import Holiday
from pandas.tseries.holiday import USFederalHolidayCalendar
from pandas.tseries.offsets import BDay

from alexlib.constants import epoch_seconds


class CustomTimedelta(timedelta):
    """custom timedelta class with extra methods"""

    @classmethod
    def rand(cls) -> timedelta():
        """Generate a random timedelta object."""
        return cls(seconds=get_rand_timedelta().total_seconds())

    @property
    def epoch_self_dif(self) -> float:
        """returns the difference between the timedelta and epoch_seconds"""
        return self.total_seconds() - epoch_seconds

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
        diff = self.epoch_self_diff
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
        return self.timestamp() - epoch_seconds

    def get_epoch_self_divmod(self, td: timedelta) -> tuple[float, float]:
        """returns the divmod of the datetime and epoch_seconds"""
        return divmod(self.epoch_self_dif, td.total_seconds())

    def __round__(self, td: timedelta) -> datetime:
        """rounds the datetime to the nearest td"""
        mod = self.epoch_self_dif % td.total_seconds()
        return self.fromtimestamp(epoch_seconds + self.epoch_self_dif - mod)


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

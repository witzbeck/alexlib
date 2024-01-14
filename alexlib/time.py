from datetime import datetime, timedelta
from logging import info
from decorator import decorator
from functools import cached_property
from random import randint
from time import perf_counter
from typing import Callable

from pandas import Timestamp
from pandas.tseries.offsets import BDay
from pandas.tseries.holiday import USFederalHolidayCalendar, Holiday

from alexlib.constants import epoch_seconds


def get_rand_datetime() -> datetime:
    """Generate a random datetime object."""
    return datetime(
        randint(2, 3000),
        randint(1, 12),
        randint(1, 28),
        randint(0, 23),
        randint(0, 59),
        randint(0, 59),
        randint(0, 1000000),
    )


def get_rand_timedelta() -> timedelta:
    """Generate a random timedelta object."""
    return timedelta(
        weeks=randint(0, 100),
        days=randint(0, 30),
        hours=randint(0, 23),
        minutes=randint(0, 59),
        seconds=randint(0, 59),
        microseconds=randint(0, 1000000),
    )


class CustomTimedelta(timedelta):
    """custom timedelta class with extra methods"""

    @classmethod
    def rand(cls) -> timedelta():
        return cls(seconds=get_rand_timedelta().total_seconds())

    @property
    def epoch_self_dif(self) -> float:
        return self.total_seconds() - epoch_seconds

    @staticmethod
    def _find_smallest_unit(td: timedelta):
        """returns the smallest unit of time in a timedelta"""
        # Check each unit, starting from the largest to the smallest
        if td.days != 0:
            return "days"
        elif td.seconds != 0:
            return "seconds"
        elif td.microseconds != 0:
            return "microseconds"
        else:
            return "zero"  # Handle the case where timedelta is zero

    def get_epoch_self_divmod(self, td: timedelta) -> tuple[float, float]:
        return divmod(self.epoch_self_dif, td.total_seconds())

    def __round__(self, other: timedelta) -> timedelta:
        diff = self.epoch_self_diff
        mod = diff % other.total_seconds()
        return self.__class__(seconds=diff - mod)


class CustomDatetime(datetime):
    """custom datetime class with extra methods"""

    @classmethod
    def rand(cls) -> datetime:
        return cls.fromtimestamp(get_rand_datetime().timestamp())

    @cached_property
    def holidays(self) -> list[Holiday]:
        return USFederalHolidayCalendar().holidays().to_pydatetime()

    @property
    def isholiday(self) -> bool:
        return self.date() in self.holidays

    @property
    def isweekday(self) -> bool:
        return self.isoweekday() <= 5

    @property
    def isweekend(self) -> bool:
        return not self.isweekday

    @property
    def isbusinessday(self) -> bool:
        return not (self.isholiday or self.isweekend)

    @property
    def yesterday(self) -> datetime:
        return self - timedelta(days=1)

    @property
    def tomorrow(self) -> datetime:
        return self + timedelta(days=1)

    @cached_property
    def one_busday(self) -> BDay:
        return BDay(1)

    def get_last_busday(self) -> datetime:
        chkdate = Timestamp(self.yesterday)
        while chkdate in self.holidays:
            chkdate = chkdate - self.one_busday
        return chkdate.to_pydatetime()

    @property
    def epoch_self_dif(self) -> float:
        return self.timestamp() - epoch_seconds

    def get_epoch_self_divmod(self, td: timedelta) -> tuple[float, float]:
        return divmod(self.epoch_self_dif, td.total_seconds())

    def __round__(self, td: timedelta) -> datetime:
        mod = self.epoch_self_dif % td.total_seconds()
        return self.fromtimestamp(epoch_seconds + self.epoch_self_dif - mod)


@decorator
def timeit(func: Callable, niter: int = None, *args, **kwargs) -> None:
    unit_index, threshold, roundto = 0, 0.09, 6
    UNITS = ["s", "ms", "μs", "ns"]
    pc1 = perf_counter()
    result = func(*args, **kwargs) if niter is None else [func() for _ in range(niter)]
    dif = perf_counter() - pc1
    while dif <= threshold:
        unit_index += 1
        dif *= 10e3
    loopstr = f" in {niter} loops" if niter is not None else ""
    res = f"{str(round(dif, roundto))} {UNITS[unit_index]}"
    msg = f"{func.__name__} took {res}{loopstr}"
    try:
        nres = len(result) if niter is None else sum([len(x) for x in result])
        msg = f"{msg} and returned {nres} results"
    except TypeError:
        info("timeit: result is not iterable")
    print(msg)
    return result

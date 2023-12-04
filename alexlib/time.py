from datetime import datetime, timedelta, date
from decorator import decorator
from functools import cached_property
from numpy import ndarray
from random import randint
from time import perf_counter
from typing import Callable

from pandas.tseries.holiday import USFederalHolidayCalendar

from alexlib.constants import epoch_s

difthresh = 0.09
roundto = 6

UNITS = ["s", "ms", "μs", "ns"]


class timedelta(timedelta):
    """new timedelta class with extra methods"""

    @classmethod
    def rand(cls) -> timedelta:
        return timedelta(
            years=randint(0, 100),
            months=randint(0, 12),
            days=randint(0, 30),
            hours=randint(0, 24),
            minutes=randint(0, 60),
            seconds=randint(0, 60),
            microseconds=randint(0, 1000000),
        )

    @property
    def self_s(self):
        return self.total_seconds()

    @property
    def epoch_self_dif(self) -> float:
        return self.self_s - epoch_s

    @classmethod
    def _find_smallest_unit(cls):
        # write a function that
        # returns the smallest
        # unit of time in a
        # dt datetime or
        # td timedelta
        print(dir(timedelta(days=1)))

        pass

    @staticmethod
    def get_td_s(td: timedelta) -> float:
        return td.total_seconds()

    def get_epoch_self_divmod(self, td_s: timedelta):
        return divmod(self.epoch_self_dif, timedelta.get_td_s(td_s))

    def __init__(self) -> None:
        super().__init__()

    def __round__(
        self,
        td: timedelta,
        epoch_s: datetime = epoch_s,
    ) -> timedelta:
        """
        allows for rounding timedelta to a timedelta
            returns rounded dateti
            1. converts both to seconds
            2. calcs difference between both and epoch
        """
        dif = self.epoch_self_dif
        td_s = timedelta.get_td_s(td)
        mod = dif % td_s
        return self.fromtimestamp(epoch_s + dif - mod)


class datetime(datetime):
    """new datetime class with extra methods"""

    @classmethod
    def rand(cls) -> datetime:
        return datetime(
            year=randint(2, 3000),
            month=randint(1, 12),
            day=randint(1, 28),
            hour=randint(0, 24),
            minute=randint(0, 60),
            second=randint(0, 60),
            microsecond=randint(0, 1000000),
        )

    @cached_property
    def holidays(self) -> ndarray(date):
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
    def yesterday(self):
        return self - timedelta(days=1)

    @property
    def tomorrow(self):
        return self + timedelta(days=1)

    def get_last_busday(self):
        chkdate = self.yesterday
        while not chkdate.isbusinessday:
            chkdate = chkdate.yesterday
        return chkdate

    @property
    def epoch_self_dif(self):
        return self.timestamp() - epoch_s

    @staticmethod
    def get_td_s(td: timedelta) -> float:
        return td.total_seconds()

    def get_epoch_self_divmod(self, td_s: timedelta) -> tuple[float, float]:
        return divmod(self.epoch_self_dif, datetime.get_td_s(td_s))

    def __init__(self):
        super().__init__()

    def __round__(
        self,
        td: timedelta,
        epoch_s: datetime = epoch_s,
    ) -> datetime:
        """
        allows for rounding datetime to a timedel
            returns rounded dateti
            1. converts both datetime and timedelta to seconds
            2. calcs difference between datetime and epoch
        self_s, td_s = self.timestamp(), td.total_seconds()
        dif = self_s - epoch_s      # dif = difference in seconds
        mod = dif % td_s            # mod = modulus of dif and td_s
        return self.fromtimestamp(epoch_s + (dif - mod))
        """
        dif = self.epoch_self_dif
        td_s = datetime.get_td_s(td)
        mod = dif % td_s
        return self.fromtimestamp(epoch_s + dif - mod)


@decorator
def timeit(
        func: Callable,
        niter: int = None,
        *args,
        **kwargs,
) -> None:
    pc1 = perf_counter()
    if niter is None:
        ret = func(*args, **kwargs)
    else:
        ret = [func() for _ in range(niter)]
    i, dif = 0, perf_counter() - pc1
    while dif <= difthresh:
        i += 1
        dif *= 10e3
    loopstr = f" in {niter} loops" if niter is not None else ""
    res = f"{str(round(dif, roundto))} {UNITS[i]}"
    msg = f"{func.__name__} took {res}{loopstr}"
    try:
        if niter is None:
            nres = len(ret)
        else:
            nres = sum([len(x) for x in ret])
        msg = f"{msg} and returned {nres} results"
    except TypeError:
        pass
    print(msg)
    return ret

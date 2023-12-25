from datetime import datetime, timedelta
from decorator import decorator
from functools import cached_property
from random import randint
from time import perf_counter
from typing import Callable

from pandas.tseries.holiday import USFederalHolidayCalendar, Holiday

from alexlib.constants import epoch_seconds

difthresh = 0.09
roundto = 6

UNITS = ["s", "ms", "μs", "ns"]


class timedelta(timedelta):
    """new timedelta class with extra methods"""

    @classmethod
    def rand(cls) -> timedelta():
        return timedelta(
            weeks=randint(0, 100),
            days=randint(0, 30),
            hours=randint(0, 23),
            minutes=randint(0, 59),
            seconds=randint(0, 59),
            microseconds=randint(0, 1000000),
        )

    @property
    def epoch_self_dif(self) -> float:
        return self.total_seconds() - epoch_seconds

    @classmethod
    def _find_smallest_unit(cls):
        """write a function that returns the smallest
        unit of time in a datetime or timedelta
        """
        print(dir(timedelta(days=1)))

    def get_epoch_self_divmod(self, td: timedelta) -> tuple[float, float]:
        return divmod(self.epoch_self_dif, td.total_seconds())

    def __round__(
        self,
        td: timedelta,
    ) -> timedelta:
        """
        allows for rounding timedelta to a timedelta
            returns rounded dateti
            1. converts both to seconds
            2. calcs difference between both and epoch
        """
        dif = self.epoch_self_dif
        mod = dif % td.total_seconds()
        return self.fromtimestamp(epoch_seconds + dif - mod)


class datetime(datetime):
    """new datetime class with extra methods"""

    @classmethod
    def rand(cls) -> datetime:
        return datetime(
            randint(2, 3000),
            randint(1, 12),
            randint(1, 28),
            randint(0, 23),
            randint(0, 59),
            randint(0, 59),
            randint(0, 1000000),
        )

    @cached_property
    def holidays(self) -> list[Holiday]:
        return USFederalHolidayCalendar().holidays().to_pydatetime()

    @property
    def isholiday(self) -> bool:
        dt = datetime(self.year, self.month, self.day)
        return dt in self.holidays

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

    def get_last_busday(self) -> datetime:
        chkdate = self.yesterday
        while not chkdate.isbusinessday:
            chkdate = chkdate.yesterday
        return chkdate

    @property
    def epoch_self_dif(self) -> float:
        return self.timestamp() - epoch_seconds

    def get_epoch_self_divmod(self, td: timedelta) -> tuple[float, float]:
        return divmod(self.epoch_self_dif, td.total_seconds())

    def __round__(self, td: timedelta) -> datetime:
        """
        allows for rounding datetime to a timedelta
            returns rounded datetime
            1. converts both datetime and timedelta to seconds
            2. calcs difference between datetime and epoch
        self_s, td_s = self.timestamp(), td.total_seconds()
        dif = self_s - epoch_s      # dif = difference in seconds
        mod = dif % td_s            # mod = modulus of dif and td_s
        return self.fromtimestamp(epoch_s + (dif - mod))
        """
        dif = self.epoch_self_dif
        mod = dif % td.total_seconds()
        return self.fromtimestamp(epoch_seconds + dif - mod)


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

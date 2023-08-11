from datetime import datetime as dt, timedelta as td
from random import randint


epoch = dt(
    year=2,
    month=1,
    day=1,
    hour=0,
    minute=0,
    second=0,
    microsecond=0,
)
epoch_s = epoch.timestamp()

istrue = lambda x: x is True


def mk_delta(td_obj: td):
    return td_obj(
        years=randint(0, 100),
        months=randint(0, 12),
        days=randint(0, 30),
        hours=randint(0, 24),
        minutes=randint(0, 60),
        seconds=randint(0, 60),
        microseconds=randint(0, 1000000),
    )


class timedelta(td):
    @classmethod
    def as_rand(cls) -> td:
        return mk_delta(cls)

    @property
    def epoch(self):
        return epoch

    @property
    def epoch_s(self):
        return epoch_s

    @property
    def self_s(self):
        return self.total_seconds()

    @property
    def epoch_self_dif(self):
        return self.self_s - self.epoch_s

    @classmethod
    def _find_smallest_unit(cls):
        # write a function that
        # returns the smallest
        # unit of time in a
        # dt datetime or
        # td timedelta
        print(dir(td(days=1)))

        pass

    @staticmethod
    def get_td_s(td: td) -> float:
        return td.total_seconds()

    def get_epoch_self_divmod(self, td_s: td):
        return divmod(self.epoch_self_dif, timedelta.get_td_s(td_s))

    def __init__(self):
        super().__init__()

    def __round__(
            self,
            td: td,
            epoch_s: dt = epoch_s,
    ) -> td:
        """
        allows for rounding timedelta to a timedelta
            returns rounded dateti
            1. converts both to seconds
            2. calcs difference between both and epoch
        self_s, td_s = self.timestamp(), td.total_seconds()   
        dif = self_s - epoch_s      # dif = difference in seconds
        mod = dif % td_s            # mod = modulus of dif and td_s
        return self.fromtimestamp(epoch_s + (dif - mod))
        """
        dif = self.epoch_self_dif
        td_s = timedelta.get_td_s(td)
        mod = dif % td_s
        return self.fromtimestamp(epoch_s + dif - mod)
        # returns rounded datetime
        # self/delta in seconds


def mk_date(dt_obj: dt):
    return dt_obj(
        year=randint(2, 3000),
        month=randint(1, 12),
        day=randint(1, 28),
        hour=randint(0, 24),
        minute=randint(0, 60),
        second=randint(0, 60),
        microsecond=randint(0, 1000000),
    )


class datetime(dt):
    @classmethod
    def as_rand(cls) -> dt:
        return mk_date(cls)

    @property
    def epoch(self):
        return epoch

    @property
    def epoch_s(self):
        return epoch_s

    @property
    def self_s(self):
        return self.timestamp()

    @property
    def epoch_self_dif(self):
        return self.self_s - self.epoch_s

    @staticmethod
    def get_td_s(td: td) -> float:
        return td.total_seconds()

    def get_epoch_self_divmod(self, td_s: td):
        return divmod(self.epoch_self_dif, datetime.get_td_s(td_s))

    def __init__(self):
        super().__init__()

    def __round__(
            self,
            td: td,
            epoch_s: dt = epoch_s,
    ) -> dt:      
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






now = datetime.now()
delta = td(hours=36)
print(now, round(now, delta))


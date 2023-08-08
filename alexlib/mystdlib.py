from datetime import datetime as dt, timedelta as td


epoch = dt(
    year=0,
    month=1,
    day=1,
    hour=0,
    minute=0,
    second=0,
    microsecond=0,
)


class datetime(dt):
    """allows for rounding datetime to a timedelta"""
    def __round__(
            self,
            td: td,
            epoch_s: dt = epoch.timestamp(),
    ) -> dt:
        self_s = self.timestamp()  # self_s = self in seconds
        td_s = td.total_seconds()  # td_s = tdelta in seconds
        dif = self_s - epoch_s  # dif = difference in seconds
        mod = dif % td_s  # mod = modulus of dif and td_s
        return self.fromtimestamp(epoch_s + (dif - mod)) #

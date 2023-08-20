from dataclasses import dataclass, field
from math import sqrt
from typing import Callable

from pandas import DataFrame, Series
from numpy import array


def pyth(_list: list):
    return sqrt(sum([x ** 2 for x in _list]))


def interpolate(
        x: int | float,
        x1: int | float,
        x2: int | float,
        y1: int | float | Callable,
        y2: int | float | Callable,
) -> float | int:
    if x1 == x2:
        return y1
    if isinstance(y1, Callable):
        y1 = y1(x1)
    if isinstance(y2, Callable):
        y2 = y2(x2)
    m = (y2 - y1) / (x2 - x1)
    b = y2 - (m * x2)
    return (m * x) + b


def fib(a: int = 0, b: int = 1):
    while True:
        c = a + b
        a = b
        b = c
        yield c


@dataclass
class GoldenRatio:
    n: int = field(default=0)
    est: float = field(default=None)
    fib1: int = field(
        default=fib(),
        repr=False
    )
    fib2: int = field(
        default=fib(a=1),
        repr=False
    )
    e: float = field(
        default=1e-6,
        repr=False
    )

    @property
    def a(self):
        return next(self.fib1)

    @property
    def b(self):
        return next(self.fib2)

    @property
    def ratio(self):
        self.n += 1
        self.est = self.b / self.a
        return self.est

    def loop(self, n: int):
        return [self.ratio for _ in range(n)][-1]

    def get_est(self):
        if self.n > 0:
            return self.loop(self.n)
        else:
            return self.estimate()

    def set_est(self):
        self.est = self.get_est

    def get_error(self):
        if self.est is None:
            return 1
        x = self.est
        y = self.ratio
        return abs(x - y)

    def estimate(self):
        error = self.get_error()
        while error >= self.e:
            error = self.get_error()
        return self.est

    def __post_init__(self):
        self.est = self.ratio
        self.set_est()


def get_quantiles(_list: list, tiles: int = 100):
    _list = list(_list)
    _list.sort(key=lambda x: int(x))
    _len = len(_list)
    out_dict = {}
    tile_ratio = (1 / tiles)
    idx_ratio = _len * tile_ratio

    out_dict['0'] = _list[0]
    for i in range(1, tiles):
        tile_idx = int(i * idx_ratio)
        out_dict[i] = _list[tile_idx]

    out_dict[tiles] = _list[-1]
    return out_dict


def get_list_difs(_list):
    _range = range(len(_list))
    return [_list[i - 1] - _list[i] for i in _range if i > 0]


def get_list_mids(_list: list):
    _range = range(len(_list))
    return [(_list[i - 1] + _list[i]) / 2 for i in _range if i > 0]


def get_rect_area(heights: list,
                  widths: list,
                  absolute: bool = True
                  ):
    _range = range(len(heights))
    rect_areas = [heights[i] * widths[i] for i in _range]
    if absolute:
        return sum([abs(x) for x in rect_areas])
    return sum(rect_areas)


def combine_domains(x1: list, x2: list):
    x = list(set(list(x1) + list(x2)))
    domain = x * 2
    domain.sort()
    return array(domain)


def get_props(series: Series):
    dist_vals = list(series.unique())
    n_all_vals = len(series)
    freqs = [sum(series == x) for x in dist_vals]
    props = [sum(series == x) / n_all_vals for x in dist_vals]
    return DataFrame.from_dict(
        {
            "value": dist_vals,
            "frequency": freqs,
            "proportion": props
        })


def make_prop_dict(df: DataFrame):
    non_id_cols = [x for x in df.columns if x[-3:] != "_id"]
    all_series = [Series(df.loc[:, x]) for x in non_id_cols]
    return {col: get_props(col) for col in all_series}

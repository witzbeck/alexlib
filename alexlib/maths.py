from dataclasses import dataclass, field
from math import sqrt
from typing import Callable
from random import choice

from numpy import array
from pandas import DataFrame, Series

from alexlib.perf import timeit


def randbool(asint: bool = False):
    if asint:
        choices = [0, 1]
    else:
        choices = [True, False]
    return choice(choices)


def euclidean_distance(lst: list):
    return sqrt(sum([x ** 2 for x in lst]))


def discrete_exp_dist(
        exp_min: int,
        exp_max: int,
        exp_int: int = 10,
        exp_inc: int = 1,
        numerator: int = 1
) -> list[float]:
    exp_max += 1
    rng = range(exp_min, exp_max, exp_inc)
    return [numerator / (exp_int ** i) for i in rng]


def isintorfloat(x: int | float) -> bool:
    return (isinstance(x, int) or isinstance(x, float))


def interpolate(
        x: int | float,
        x1: int | float,
        x2: int | float,
        y1: int | float | Callable,
        y2: int | float | Callable,
        e: float = 1e-6
) -> float | int:
    ret = None
    y1isnum = isintorfloat(y1)
    y2isnum = isintorfloat(y2)
    xsarezero = (x1 == 0. and x2 == 0.)
    xsareequal = (x1 == x2)
    xsbelowe = (x2 - x1) <= e
    rety1 = (xsarezero or xsareequal or xsbelowe)
    if rety1:
        ret = y1
    elif x == x1:
        ret = y1
    elif x == x2:
        ret = y2

    if y1isnum:
        pass
    elif issubclass(y1, Callable):
        y1 = y1(x1)
    else:
        raise TypeError("y1 must be a number or a function")

    if y2isnum:
        pass
    elif issubclass(y2, Callable):
        y2 = y2(x2)
    else:
        raise TypeError("y2 must be a number or a function")

    if ret is None:
        m = (y2 - y1) / (x2 - x1)
        b = y2 - (m * x2)
        ret = (m * x) + b
    return ret


@dataclass
class GoldenRatio:
    phi: float = field(
        default=None,
        repr=False
    )
    e: float = field(
        default=1e-6,
        repr=False
    )

    def __post_init__(self):
        self.phi = self.fast(e=self.e)

    @staticmethod
    def get_error(*args):
        return abs(args[0] - args[1])

    @staticmethod
    def phigen(phi: int = 1):
        while True:
            yield (phi := 1 + (1 / phi))

    @staticmethod
    def fibgen(a: int = 0, b: int = 1):
        while True:
            c = a + b
            a = b
            b = c
            yield c

    @staticmethod
    @timeit
    def fast(
        e: float = 1e-6,
        phi: int = 1,
    ) -> float:
        while True:
            if abs(phi - (phi := 1 + (1 / phi))) <= e:
                return phi


def get_quantiles(lst: list, tiles: int = 100):
    if not isinstance(lst, list):
        lst = list(lst)
    lst.sort(key=lambda x: int(x))
    tile_ratio = (1 / tiles)
    idx_ratio = len(lst) * tile_ratio
    tile_idx = lambda i: int(i * idx_ratio)
    rng = range(1, tiles)
    out_dict = {
        i: lst[tile_idx(i)]
        for i in rng
    }
    out_dict[0] = lst[0]
    out_dict[tiles] = lst[-1]
    return out_dict


def get_list_difs(lst: list[float]):
    rng = range(len(lst))
    return [lst[i - 1] - lst[i] if i > 0 else lst[0] for i in rng]


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


def combine_domains(
        x1: list,
        x2: list,
        toarray: bool = True
) -> array:
    x1.extend(x2)
    if toarray:
        domain = array(x1).unique()
    else:
        domain = list(set(x1))
    domain.sort()
    return domain


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

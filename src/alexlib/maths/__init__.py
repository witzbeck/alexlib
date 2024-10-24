"""
This module provides a collection of functions and classes for mathematical and statistical computations.
It includes functionalities for generating prime numbers, random booleans, calculating euclidean distances,
and handling exponential distributions. Additionally, it contains utilities for interpolating values,
quantile computation, and area calculation for rectangles.

Key classes include GoldenRatio, which calculates the golden ratio with precision, and VariableBaseNumber,
a class for representing numbers in different bases with various utilities. The module also offers functions
for processing lists, such as calculating differences, midpoints, and combining domains. Furthermore, it
provides tools for working with pandas DataFrames and Series, including generating frequency and proportion
dataframes from a given dataset.

Dependencies:
- Standard libraries: dataclasses, functools, math, random, string, typing
- Third-party libraries: numpy, pandas
- Custom libraries: alexlib.time

Features:
- Prime number generation
- Random boolean generation
- Euclidean distance calculation
- Discrete exponential distribution calculation
- Type checking for integers and floats
- Value interpolation
- Golden ratio computation with precision timing
- Fibonacci sequence generation
- Quantile calculation for lists
- Difference and midpoint calculation in lists
- Rectangle area calculation
- Domain combination for arrays
- Frequency and proportion calculation in pandas Series and DataFrames
- Representation of numbers in variable base systems
"""

from collections.abc import Generator
from dataclasses import dataclass, field
from functools import cached_property
from math import sqrt
from random import choice
from string import ascii_uppercase
from typing import Callable, Iterable

from pandas import DataFrame, Series


def get_primes(n: int) -> list[int]:
    """Returns  a list of primes < n"""
    sieve = [True] * n
    for i in range(3, int(n**0.5) + 1, 2):
        if sieve[i]:
            sieve[i * i :: 2 * i] = [False] * ((n - i * i - 1) // (2 * i) + 1)
    return [2] + [i for i in range(3, n, 2) if sieve[i]]


def randbool(asint: bool = False) -> bool | int:
    """returns a random boolean or integer"""
    return choice([0, 1] if asint else [True, False])


def euclidean_distance(itr: Iterable) -> float:
    """returns the euclidean distance of an iterable"""
    return sqrt(sum(x**2 for x in itr))


def discrete_exp_dist(
    exp_min: int, exp_max: int, exp_int: int = 10, exp_inc: int = 1, numerator: int = 1
) -> list[float]:
    """returns a list of discrete values for an exponential distribution"""
    return [numerator / (exp_int**i) for i in range(exp_min, exp_max + 1, exp_inc)]


def isintorfloat(x: int | float) -> bool:
    """returns True if x is an int or float"""
    return not isinstance(x, bool) and isinstance(x, (int, float))


def interpolate(
    x: int | float,
    x1: int | float,
    x2: int | float,
    y1: int | float | Callable,
    y2: int | float | Callable,
    e: float = 1e-6,
) -> float | int:
    """returns the interpolated value of x between x1 and x2"""
    ret = None
    y1isnum = isintorfloat(y1)
    y2isnum = isintorfloat(y2)
    xsarezero = x1 == 0.0 and x2 == 0.0
    xsareequal = x1 == x2
    xsbelowe = (x2 - x1) <= e
    rety1 = xsarezero or xsareequal or xsbelowe
    if rety1:
        ret = y1
    elif x == x1:
        ret = y1
    elif x == x2:
        ret = y2

    if y1isnum:
        pass
    elif issubclass(y1.__class__, Callable):
        y1 = y1(x1)
    else:
        raise TypeError("y1 must be a number or a function")

    if y2isnum:
        pass
    elif issubclass(y2.__class__, Callable):
        y2 = y2(x2)
    else:
        raise TypeError("y2 must be a number or a function")

    if ret is None:
        m = (y2 - y1) / (x2 - x1)
        b = y2 - (m * x2)
        ret = (m * x) + b
    return ret


def phi_generator(phi: int = 1) -> Generator[float]:
    """returns a generator for the golden ratio"""
    while True:
        yield (phi := 1 + (1 / phi))


def fibonacci_generator(a: int = 0, b: int = 1) -> Generator[int]:
    """returns a generator for the fibonacci sequence"""
    while True:
        c = a + b
        a = b
        b = c
        yield c


def get_phi_by_precision(e: float = 1e-6) -> float:
    """returns the golden ratio to the specified precision"""
    phi = 1
    while True:
        if abs(phi - (phi := 1 + (1 / phi))) <= e:
            return phi


def get_quantiles(lst: list, tiles: int = 100) -> dict[int, float]:
    """returns a dict of quantiles for a list"""
    if not isinstance(lst, list):
        lst = list(lst)
    lst.sort(key=lambda x: int(x))
    tile_ratio = 1 / tiles
    idx_ratio = len(lst) * tile_ratio
    out_dict = {i: lst[int(i * idx_ratio)] for i in range(1, tiles)}
    out_dict[0] = lst[0]
    out_dict[tiles] = lst[-1]
    return out_dict


def get_list_difs(lst: list[float]) -> list[float]:
    """returns a list of differences between list elements"""
    rng = range(len(lst))
    return [lst[i - 1] - lst[i] if i > 0 else lst[0] for i in rng]


def get_list_mids(_list: list) -> list:
    """returns a list of the midpoints between list elements"""
    _range = range(len(_list))
    return [(_list[i - 1] + _list[i]) / 2 for i in _range if i > 0]


def get_rect_area(heights: list, widths: list, absolute: bool = True) -> float:
    """returns the area of a rectangle"""
    _range = range(len(heights))
    rect_areas = [heights[i] * widths[i] for i in _range]
    return sum(abs(x) for x in rect_areas) if absolute else sum(rect_areas)


def combine_domains(x1: list, x2: list) -> list[float]:
    """returns a combined domain from two lists"""
    return sorted(set(x1).union(set(x2)))


def get_props(series: Series) -> DataFrame:
    """returns a dataframe of the frequency and proportion of values in a series"""
    dist_vals = list(series.unique())
    n_all_vals = len(series)
    freqs = [sum(series == x) for x in dist_vals]
    props = [sum(series == x) / n_all_vals for x in dist_vals]
    return DataFrame.from_dict(
        {
            "value": dist_vals,
            "frequency": freqs,
            "proportion": props,
        }
    )


def make_prop_dict(df: DataFrame) -> dict[str, DataFrame]:
    """returns a dict of dataframes of the frequency and proportion of values in a dataframe"""
    non_id_cols = [x for x in df.columns if x[-3:] != "_id"]
    all_series = [Series(df.loc[:, x]) for x in non_id_cols]
    return {col: get_props(col) for col in all_series}


@dataclass
class VariableBaseNumber:
    """Base Number class"""

    base10_val: float
    base: int
    error: float = 10e-8
    usexchar: bool = True
    exp_dict: dict[int:int] = field(repr=False, default_factory=dict)

    @cached_property
    def isnegative(self) -> bool:
        """returns True if the base10_val is negative"""
        return self.base10_val < 0

    @cached_property
    def sign(self) -> str:
        """returns the sign of the base10_val"""
        return "-" if self.isnegative else ""

    @cached_property
    def base10_str(self) -> bool:
        """returns the base10_val as a string"""
        return str(self.base10_val)

    @cached_property
    def hasdecimal(self) -> bool:
        """returns True if the base10_val has a decimal"""
        return "." in self.base10_str

    @cached_property
    def roundto(self) -> int:
        """returns the number of decimal places to round to"""
        return len(self.base10_str.split(".", maxsplit=1)[-1]) if self.hasdecimal else 0

    @cached_property
    def chars(self) -> dict[int:str]:
        """returns a dict of characters for each digit"""
        els = "x" * len(ascii_uppercase) if self.usexchar else ascii_uppercase
        return {
            i: str(i) if i < 10 else els[i - 10]
            for i in range(10 + len(ascii_uppercase))
        }

    def get_char(self, key: int) -> str:
        """returns the character for a digit"""
        try:
            return self.chars[key]
        except KeyError:
            return "x"

    def get_unit(self, exp: int) -> int:
        """returns the unit for an exponent"""
        return self.base**exp

    def get_highest_exp(self) -> int:
        """returns the highest exponent for the base10_val"""
        exp = 0
        unit = self.get_unit(exp)
        while unit < abs(self.base10_val):
            exp += 1
            unit = self.get_unit(exp)
        return exp - 1

    @cached_property
    def highest_exp(self) -> int:
        """returns the highest exponent for the base10_val"""
        return self.get_highest_exp()

    @cached_property
    def highest_unit(self) -> int:
        """returns the highest unit for the base10_val"""
        return self.get_unit(self.highest_exp)

    def __post_init__(self) -> None:
        """sets the exp_dict"""
        n = abs(self.base10_val)
        exp, unit = self.highest_exp, self.highest_unit
        while n != 0:
            val = n // unit
            n = round(n % unit, self.roundto)
            self.exp_dict[exp] = val
            exp -= 1
            unit = self.get_unit(exp)
        toupdate = {
            i: 0 for i in range(self.highest_exp) if i not in self.exp_dict.keys()
        }
        self.exp_dict.update(toupdate)

    @property
    def unit_dict(self) -> dict[int, int]:
        """returns a dict of units"""
        return {self.get_unit(exp): unit for exp, unit in self.exp_dict.items()}

    @property
    def lowest_exp(self) -> int:
        """returns the lowest exponent"""
        return min(self.exp_dict.keys())

    @property
    def lowest_unit(self) -> int:
        """returns the lowest unit"""
        return self.get_unit(self.lowest_exp)

    def __str__(self) -> str:
        """returns the base10_val as a string"""
        left = "".join(
            [self.get_char(val) for exp, val in self.exp_dict.items() if exp >= 0]
        )
        if self.hasdecimal:
            right = "." + "".join(
                [self.get_char(val) for exp, val in self.exp_dict.items() if exp < 0]
            )
        else:
            right = ""
        return self.sign + left + right

    def __repr__(self) -> str:
        """returns the class name and string representation"""
        return f"{self.__class__.__name__}({str(self)})"

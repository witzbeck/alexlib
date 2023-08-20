from dataclasses import dataclass, field
from typing import Callable


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
            return self.loop(n)
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

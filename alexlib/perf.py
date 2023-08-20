from time import perf_counter as pc
from typing import Callable

from decorator import decorator

difthresh = 0.09
niter = None
roundto = 6

UNITS = [
    "s",
    "ms",
    "μs",
    "ns",
]


@decorator
def timeit(
        func: Callable,
        niter: int = None,
        *args,
        **kwargs,
) -> None:
    pc1 = pc()
    if niter is None:
        ret = func(*args, **kwargs)
    else:
        ret = [func() for _ in range(niter)]
    i, dif = 0, pc() - pc1
    while dif <= difthresh:
        i += 1
        dif *= 10e3
    print(f"{str(round(dif, roundto))} {UNITS[i]}")
    return ret

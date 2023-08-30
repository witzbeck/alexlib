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


if __name__ == '__main__':
    @timeit(niter=1000)
    def test():
        return 1 + 1
    test()

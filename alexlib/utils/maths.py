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

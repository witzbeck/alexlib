"""
Created on Sun Jun 27 20:35:10 2021
https://examples.pyviz.org/attractors/attractors.html
@author: Fr333y3d3a
"""
from dataclasses import dataclass, field
from math import sin, cos, sqrt, fabs
from typing import Callable, Generator

from datashader import Canvas
from datashader.transfer_functions import Image, shade, stack
from datashader.colors import viridis
from matplotlib import pyplot as plt
from matplotlib import animation
from matplotlib.colors import _ColorMapping
from numba import jit
from numpy import zeros, sign, array
from pandas import DataFrame

from alexlib.iters import get_comb_gen


@jit(nopython=True)
def clifford(
        x: float,
        y: float,
        a: float,
        b: float,
        c: float,
        d: float
) -> tuple[float, float]:
    term1 = sin(a * y) + c * cos(a * x)
    term2 = sin(b * x) + d * cos(b * y)
    return term1, term2


@jit(nopython=True)
def dejong(
        x: float,
        y: float,
        a: float,
        b: float,
        c: float,
        d: float
) -> tuple[float, float]:
    term1 = sin(a * x) - cos(b * x)
    term2 = sin(c * y) - cos(d * y)
    return term1, term2


@jit(nopython=True)
def hopalong(
        x: float,
        y: float,
        a: float,
        b: float,
        c: float
) -> tuple[float, float]:
    term1 = y - 1 - sqrt(fabs(b * x - 1 - c)) * sign(x)
    term2 = a - x - 1
    return term1, term2


@jit(nopython=True)
def gum(x: float, mu: float):
    return mu * x + 2 * (1 - mu) * x ** 2 / (1. + x ** 2)


@jit(nopython=True)
def gumowski_mira(
        x: float,
        y: float,
        a: float,
        b: float,
        mu: float
) -> tuple[float, float]:
    xn = y + a * (1 - b * y ** 2) * y + gum(x, mu)
    yn = - x + gum(xn, mu)
    return xn, yn


fn_dict = {
    'gumowski_mira': gumowski_mira,
    'hopalong': hopalong,
    'dejong': dejong,
}

@jit(nopython=True)
def coords(
        n: int,
        x0: float,
        y0: float,
        func: Callable,
        **kwargs,
) -> tuple[array, array]:
    shape = (n, n)
    combs = get_comb_gen((n - 1, n - 1))
    grid = zeros((n, n))
    x, y = x0, y0
    for i, j in combs:
        grid[i][j] = func(x[i], y[i], *args, **kwargs)
    return x, y

def frame(
        func: Callable,
        x0: float = 0,
        y0: float = 0,
        a: float = -1.4,
        b: float = 1.56,
        c: float = 0.3,
        d: float = -0.3,
        mu: float = 0.2,
        n: int = 100000,
) -> Generator:
    
    gen = coords(func, n, x0=x0, y0=y0, a=a, b=b, c=c, d=d, mu=mu)



@dataclass
class Attractor:
    n: int = field(default=100000)
    nframes: int = field(default=200)
    figsize: tuple[int, int] = field(
        default=(10, 10),
        repr=False
    )
    plotsize: tuple[int, int] = field(
        default=(500, 500),
        repr=False
    )
    cycler: Generator = field(
        init=False,
        repr=False
    )
    func: Callable = field(
        default=clifford,
        repr=False
    )
    canvas: Canvas = field(
        default=None,
        repr=False
    )
    cmap: _ColorMapping = field(
        default=viridis,
        repr=False
    )

    def __post_init__(self):
        self.cycler = ""
        self.canvas = Canvas(
            plot_width=self.plotsize[0],
            plot_height=self.plotsize[1]
        )

    def cycle_etl(self, df: DataFrame):
        points = self.canvas.points(df, 'x', 'y')
        Image.border = 0
        img = shade(points, cmap=self.cmap).plot()
        return img

    def get_stack(self):
        pics = [next(self.trajectory.cycle) for _ in range(self.nframes)]
        imgs = [self.cycle_etl(df) for df in pics]
        return stack(imgs)

    def animate(self):
        fig, ax = plt.subplots(figsize=self.figsize)
        ax.set_xlim(-2.5, 2.5)
        ax.set_ylim(-2.5, 2.5)
        ax.set_axis_off()
        ax.set_title(self.func.__name__, fontsize=24)
        ax.set_aspect('equal')

        line, = ax.plot([], [], 'o', markersize=1, color='w')

        def init():
            line.set_data([], [])
            return line,

        def animate(i, x, y):
            line.set_data(x[:i], y[:i])
            return line,

        return animation.FuncAnimation(
            fig,
            animate,
            init_func=init,
            frames=self.nframes,
            interval=10,
            blit=True
        )


if __name__ == '__main__':
    a = Attractor()
    a.get_stack()

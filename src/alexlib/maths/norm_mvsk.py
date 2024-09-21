"""A simple example of a 4D normal distribution with changing parameters."""

from matplotlib.pyplot import axes, cm, figure, plot
from numpy import linspace
from statsmodels.sandbox.distributions.extras import pdf_mvsk

mvsk = [0, 1, 1, 3]
m1, v1, s1, k1 = 0.05, 1.04, 1.01, 1.41
iters = 30
xn = iters**2
xmin, xmax = mvsk[0] - (mvsk[1] * (v1**iters)), mvsk[0] + (mvsk[1] * (v1**iters))

fig = figure()
axis = axes()
(line,) = axis.plot([], [])


def init():
    line.set_data([], [])
    return (line,)


x = linspace(xmin, xmax, xn)

color = iter(cm.plasma(linspace(1, 0, iters)))


for i in range(iters):
    mvsk[0] = mvsk[0] + (m1)
    mvsk[1] = mvsk[1] * (v1)
    mvsk[2] = mvsk[2] * (s1**i) + abs(s1)
    mvsk[3] = mvsk[3] * (k1)
    c = next(color)
    pdf = pdf_mvsk(mvsk)
    plot(x, pdf(x), c=c)

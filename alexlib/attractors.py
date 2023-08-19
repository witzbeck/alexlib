"""
Created on Sun Jun 27 20:35:10 2021
https://examples.pyviz.org/attractors/attractors.html
@author: Fr333y3d3a
"""

from math import sin, cos, sqrt, fabs

from numpy import zeros, arange
from datashader import transfer_functions as tf
from datashader.colors import inferno, viridis

@jit(nopython=True)
def De_Jong(x,y,a,b,c,d,*o):
    return sin(a*x) - cos(b*x), \
        sin(c*x) - cos(d*y)

@jit(nopython=True)
def Hopalong1(x, y, a, b, c, *o):
    return y -1 - sqrt(fabs(b * x -1 - c)) * np.sign(x), \
        a - x -1
        
@jit(nopython=True)
def G(x, mu):
    return mu * x + 2 * (1 - mu) * x**2 / (1.0 + x**2)

@jit(nopython=True)
def Gumowski_Mira(x, y, a, b, mu, *o):
    xn = y + a*(1 - b*y**2)*y  +  G(x, mu)
    yn = -x + G(xn, mu)
    return xn, yn
           
           

n = 1000000

@jit(nopython=True)
def trajectory_coords(fn,x0,y0,a,b=0,c=0,d=0,e=0,f=0,n=n):
    x,y = np.zeros(n),np.zeros(n)
    x[0],y[0] = x0,y0
    for i in np.arange(n-1):
        x[i+1],y[i+1] = fn(x[i],y[i],a,b,c,d,e,f)
    return x,y

def trajectory(fn, x0, y0, a, b=0,c=0,d=0,e=0,f=0,n=n):
    x,y = trajectory_coords(fn, x0, y0, a, b, c, d, e, f, n)
    return pd.DataFrame(dict(x=x,y=y))


def animate():
    from matplotlib import pyplot as plt
    from matplotlib import animation
    pic_stack = []
    def init():
        cvs = ds.Canvas(plot_width=500,plot_height=500)
        return cvs
    
    for i in range(20):
        i = i/1000
        mu = 0.32 + i
        df = trajectory(Gumowski_Mira,0.5,.5,0.009,.015,mu)
        agg = cvs.points(df,'x','y')

        tf.Image.border=0
        pic_stack.append(tf.shade(agg,cmap=viridis).plot())
    tf.stack(pic_stack)
    return pic_stack

#animate()    

def just_image():
    cvs = ds.Canvas(plot_width=500,plot_height=500)
    
    mu = 0.32
    df = trajectory(Gumowski_Mira,0.5,.5,0.009,.015,mu)
    agg = cvs.points(df,'x','y')

    tf.Image.border=0
    tf.shade(agg,cmap=viridis).plot()
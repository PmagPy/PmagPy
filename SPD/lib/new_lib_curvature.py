#!/usr/bin/env python

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from builtins import range
from past.utils import old_div
import numpy
from . import lib_curvature as lib_k

#old_x = [0.0107, 0.0332, 0.0662, 0.0528, 0.1053, 0.1069, 0.1609, 0.1805, 0.2539, 0.3199, 0.4802, 0.5701, 0.6840, 0.7544, 0.8833]
#old_y = [0.9926, 0.9682, 0.8972, 0.7998, 0.7511,0.6740, 0.5238, 0.4447, 0.4142, 0.3229, 0.2457, 0.1625, 0.1178, 0.0772, 0.0508]

"""
x = [0.0107, 0.0332, 0.0662, 0.0528, 0.1053, 
     0.1069, 0.1609, 0.1805, 0.2539, 0.3199,
     0.4802, 0.5701, 0.6840, 0.7544, 0.8833]

y = [0.9926, 0.9682, 0.8972, 0.7998, 0.7511,
     0.6740, 0.5238, 0.4447, 0.4142, 0.3229, 
     0.2457, 0.1625, 0.1178, 0.0772, 0.0508]
"""

x = [  9., 35., -13.,  10.,  23.,   0.]
y = [ 34., 10.,   6., -14.,  27., -10.]



def fitcircle(n, x, y): 
# n points, x points, y points
    """c Fit circle to arbitrary number of x,y pairs, based on the
c modified least squares method of Umback and Jones (2000),
c IEEE Transactions on Instrumentation and Measurement."""
    # adding in normalize vectors step
    #x = numpy.array(x) / max(x)
    #y = numpy.array(y) / max(y)
    #
    
    sx, sx2, sx3, sy, sy2, sy3, sxy, sxy2, syx2 = (0,) * 9
    print(type(sx), sx)
    for i in range(n):
        sx = sx + x[i]
        sx2 = sx2 + x[i]**2
        sx3 = sx3 + x[i]**3
        sy = sy + y[i]
        sy2 = sy2 + y[i]**2
        sy3 = sy3 + y[i]**3
        sxy = sxy + x[i] * y[i]
        sxy2 = sxy2 + x[i] * y[i]**2
        syx2 = syx2 + y[i] * x[i]**2

    A = n * sx2 - sx**2
    B = n * sxy - sx*sy
    C = n * sy2 - sy**2
    D = 0.5 * (n * sxy2 - sx * sy2 + n * sx3 - sx * sx2)
    E = 0.5 * (n * syx2 - sy * sx2 + n * sy3 - sy * sy2)
    # values check out up to here

    xo = old_div((D * C - B * E), (A * C - B**2))
    yo = old_div((A * E - B * D), (A * C - B**2))
    print("xo", xo)
    print("yo", yo)

    r = 0
    for z in range(n):
        r = r + old_div(numpy.sqrt( (x[z]-xo)**2 + (y[z]-yo)**2 ), n)

    if xo <= numpy.mean(x) and yo <= numpy.mean(y):
        k = old_div(-1.,r)
    else:
        k = old_div(1.,r)

    SSE = lib_k.get_SSE(xo, yo, r, x, y)
    print("r", r)
    return k, xo, yo, SSE
    #return r, xo, yo



def do_fitcircle():
    fitcircle(len(x), x, y)

if __name__ == '__main__':
    fitcircle(len(x),x,y)
    




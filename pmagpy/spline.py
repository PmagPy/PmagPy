"""
Cubic spline approximation class.

Last Modified 9/9/97 by Johann Hibschman <johann@physics.berkeley.edu>
Updated to numpy 11/16/06 by Lisa Tauxe

To create a default ("natural") spline, simply use sp = Spline(x,y).
To specify the slope of the function at either of the endpoints,
use the "low_slope" and "high_slope" keywords.

Example usage:
>>> x = arange(10, typecode=Float) * 0.3
>>> y = cos(x)
>>> sp = Spline(x, y)
>>> print sp(0.5), cos(0.5)
0.878364380585 0.87758256189

Uses "searchsorted" from the Numeric module, aka "binarysearch" in older
versions.

"""
from __future__ import division
from __future__ import absolute_import

from builtins import range

from past.utils import old_div
from . import func
#from Numeric import *
import numpy
BadInput = "Bad xa input to routine splint."

class Spline(func.FuncOps):
    def __init__(self, x_array, y_array, low_slope=None, high_slope=None):
        self.x_vals = x_array
        self.y_vals = y_array
        self.low_slope  = low_slope
        self.high_slope = high_slope
        # must be careful, so that a slope of 0 still works...
        if low_slope is not None:
            self.use_low_slope  = 1
        else:
            self.use_low_slope  = 0   # i.e. false
        if high_slope is not None:
            self.use_high_slope = 1
        else:
            self.use_high_slope = 0
        self.calc_ypp()

    def calc_ypp(self):
        x_vals = self.x_vals
        y_vals = self.y_vals
        n = len(x_vals)
        y2_vals  = numpy.zeros(n, 'f')
        u        = numpy.zeros(n-1, 'f')

        if self.use_low_slope:
            u[0] = (old_div(3.0,(x_vals[1]-x_vals[0]))) * \
               (old_div((y_vals[1]-y_vals[0]),
                (x_vals[1]-x_vals[0]))-self.low_slope)
            y2_vals[0] = -0.5
        else:
            u[0] = 0.0
            y2_vals[0] = 0.0   # natural spline

        for i in range(1, n-1):
            sig = old_div((x_vals[i]-x_vals[i-1]), \
              (x_vals[i+1]-x_vals[i-1]))
            p   = sig*y2_vals[i-1]+2.0
            y2_vals[i] = old_div((sig-1.0),p)
            u[i] = old_div((y_vals[i+1]-y_vals[i]), \
               (x_vals[i+1]-x_vals[i])) - \
               old_div((y_vals[i]-y_vals[i-1]), \
               (x_vals[i]-x_vals[i-1]))
            u[i] = old_div((6.0*u[i]/(x_vals[i+1]-x_vals[i-1]) -
                sig*u[i-1]), p)

        if self.use_high_slope:
            qn = 0.5
            un = (old_div(3.0,(x_vals[n-1]-x_vals[n-2]))) * \
             (self.high_slope - old_div((y_vals[n-1]-y_vals[n-2]),
              (x_vals[n-1]-x_vals[n-2])))
        else:
            qn = 0.0
            un = 0.0    # natural spline

        y2_vals[n-1] = old_div((un-qn*u[n-2]),(qn*y2_vals[n-1]+1.0))

        rng = list(range(n-1))
        rng.reverse()
        for k in rng:         # backsubstitution step
            y2_vals[k] = y2_vals[k]*y2_vals[k+1]+u[k]
        self.y2_vals = y2_vals


    # compute approximation
    def __call__(self, arg):
        """
        Simulate a ufunc; handle being called on an array.
        """
        if type(arg) == func.ArrayType:
            return func.array_map(self.call, arg)
        else:
            return self.call(arg)

    def call(self, x):
        """
        Evaluate the spline, assuming x is a scalar.
        """
        # if out of range, return endpoint
        if x <= self.x_vals[0]:
            return self.y_vals[0]
        if x >= self.x_vals[-1]:
            return self.y_vals[-1]

        pos = numpy.searchsorted(self.x_vals, x)

        h = self.x_vals[pos]-self.x_vals[pos-1]
        if h == 0.0:
            raise BadInput

        a = old_div((self.x_vals[pos] - x), h)
        b = old_div((x - self.x_vals[pos-1]), h)
        return (a*self.y_vals[pos-1] + b*self.y_vals[pos] + \
            ((a*a*a - a)*self.y2_vals[pos-1] + \
             (b*b*b - b)*self.y2_vals[pos]) * h*h/6.0)


class LinInt(func.FuncOps):
    def __init__(self, x_array, y_array):
        self.x_vals = x_array
        self.y_vals = y_array

    # compute approximation
    def __call__(self, arg):
        """
        Simulate a ufunc; handle being called on an array.
        """
        if type(arg) == func.ArrayType:
            return func.array_map(self.call, arg)
        else:
            return self.call(arg)

    def call(self, x):
        """
        Evaluate the interpolant, assuming x is a scalar.
        """
    # if out of range, return endpoint
        if x <= self.x_vals[0]:
            return self.y_vals[0]
        if x >= self.x_vals[-1]:
            return self.y_vals[-1]

        pos = numpy.searchsorted(self.x_vals, x)

        h = self.x_vals[pos]-self.x_vals[pos-1]
        if h == 0.0:
            raise BadInput

        a = old_div((self.x_vals[pos] - x), h)
        b = old_div((x - self.x_vals[pos-1]), h)
        return a*self.y_vals[pos-1] + b*self.y_vals[pos]

def spline_interpolate(x1, y1, x2):
    """
    Given a function at a set of points (x1, y1), interpolate to
    evaluate it at points x2.
    """
    sp = Spline(x1, y1)
    return sp(x2)

def logspline_interpolate(x1, y1, x2):
    """
    Given a function at a set of points (x1, y1), interpolate to
    evaluate it at points x2.
    """
    sp = Spline(log(x1), log(y1))
    return exp(sp(log(x2)))


def linear_interpolate(x1, y1, x2):
    """
    Given a function at a set of points (x1, y1), interpolate to
    evaluate it at points x2.
    """
    li = LinInt(x1, y1)
    return li(x2)

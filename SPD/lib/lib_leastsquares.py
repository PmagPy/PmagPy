#!/usr/bin/env python

from __future__ import division
from __future__ import print_function
from builtins import map
from past.utils import old_div
from numpy import *
from scipy      import optimize



# Coordinates of the 2D points

x = r_[  9, 35, -13,  10,  23,   0]
y = r_[ 34., 10.,   6., -14.,  27., -10.]
#x = x / max(x)
#y = y / max(y)

# x = r_[36, 36, 19, 18, 33, 26]
# y = r_[14, 10, 28, 31, 18, 26]
# basename = 'arc'


def do_circlefit(x=x, y=y):
    print("x: ", x, "y: ", y)

    # ensure all values are floats, then norm them by largest value
    x = array(list(map(float, x)))
    x = old_div(x, max(x))
    y = array(list(map(float, y)))
    y = old_div(y, max(y))
    

    # coordinates of the barycenter
    x_m = mean(x)
    y_m = mean(y)

    # calculation of the reduced coordinates
    u = x - x_m
    v = y - y_m

    # linear system defining the center in reduced coordinates (uc, vc):
    #    Suu * uc +  Suv * vc = (Suuu + Suvv)/2
    #    Suv * uc +  Svv * vc = (Suuv + Svvv)/2
    Suv  = sum(u*v)
    Suu  = sum(u**2)
    Svv  = sum(v**2)
    Suuv = sum(u**2 * v)
    Suvv = sum(u * v**2)
    Suuu = sum(u**3)
    Svvv = sum(v**3)

    # Solving the linear system
    A = array([ [ Suu, Suv ], [Suv, Svv]])
    B = old_div(array([ Suuu + Suvv, Svvv + Suuv ]),2.0)
    uc, vc = linalg.solve(A, B)

    xc_1 = x_m + uc
    yc_1 = y_m + vc

    # Calculation of all distances from the center (xc_1, yc_1)
    Ri_1      = sqrt((x-xc_1)**2 + (y-yc_1)**2)
    R_1       = mean(Ri_1)
    residu_1  = sum((Ri_1-R_1)**2)
    residu2_1 = sum((Ri_1**2-R_1**2)**2)

    #  == METHOD 2 ==
    # Basic usage of optimize.leastsq
    #from scipy      import optimize

    method_2  = "leastsq"

    def calc_R(xc, yc):
        """ calculate the distance of each 2D points from the center (xc, yc) """
        return sqrt((x-xc)**2 + (y-yc)**2)

    def f_2(c):
        """ calculate the algebraic distance between the 2D points and the mean circle centered at c=(xc, yc) """
        Ri = calc_R(*c)
        return Ri - Ri.mean()

    center_estimate = x_m, y_m
    center_2, ier = optimize.leastsq(f_2, center_estimate)

    xc_2, yc_2 = center_2
    Ri_2       = calc_R(xc_2, yc_2)
    R_2        = Ri_2.mean()
    print("R_2", R_2)
    residu_2   = sum((Ri_2 - R_2)**2)
    residu2_2  = sum((Ri_2**2-R_2**2)**2)
    print("xc_2:", xc_2, "yc_2", yc_2)





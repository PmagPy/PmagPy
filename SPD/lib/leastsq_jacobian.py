from __future__ import division
from builtins import map
from builtins import range
from past.utils import old_div
import numpy
from scipy import optimize


# Coordinates of the 2D points                                                                                

X = [  9, 35, -13,  10,  23,   0]
Y = [ 34., 10.,   6., -14.,  27., -10.]

def AraiCurvature(x=X, y=Y):
    # ensure all values are floats, then norm them by largest value
    x = numpy.array(list(map(float, x)))
    x =old_div(x, max(x))
    y = numpy.array(list(map(float, y)))
    y =old_div(y, max(y))
    # if all x or all y values are identical, there is no curvature (it is a line)
    if len(set(x)) == 1 or len(set(y)) == 1:
        return -999., None, None, -999.
    best_a, best_b, r = do_circlefit(x, y)
    #print "best_a, best_b, r", best_a, best_b, r
    SSE = get_SSE(best_a, best_b, r, x, y)
    if best_a <= numpy.mean(x) and best_b <= numpy.mean(y):
        k = old_div(-1., r)
    else:
        k = old_div(1., r)
    return k, best_a, best_b, SSE

def do_circlefit(x, y):
    # taken from http://wiki.scipy.org/Cookbook/Least_Squares_Circle?action=AttachFile&do=get&target=least_squares_circle_v1d.py
    # coordinates of the barycenter
    x_m = numpy.mean(x)
    y_m = numpy.mean(y)
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
    A = numpy.array([ [ Suu, Suv ], [Suv, Svv]])
    B = old_div(numpy.array([ Suuu + Suvv, Svvv + Suuv ]),2.0)
    uc, vc = numpy.linalg.solve(A, B)

    xc_1 = x_m + uc
    yc_1 = y_m + vc

    # Calculation of all distances from the center (xc_1, yc_1)             
    Ri_1      = numpy.sqrt((x-xc_1)**2 + (y-yc_1)**2)
    R_1       = numpy.mean(Ri_1)
    residu_1  = sum((Ri_1-R_1)**2)
    residu2_1 = sum((Ri_1**2-R_1**2)**2)

    method_2b  = "leastsq with jacobian"

    def calc_R(xc, yc):
        """ calculate the distance of each data points from the center (xc, yc) """
        return numpy.sqrt((x-xc)**2 + (y-yc)**2)

    def f_2b(c):
        """ calculate the algebraic distance between the 2D points and the mean circle centered at c=(xc, yc) """
        Ri = calc_R(*c)
        return Ri - Ri.mean()

    def Df_2b(c):
        """ Jacobian of f_2b
        The axis corresponding to derivatives must be coherent with the col_deriv option of leastsq"""
        xc, yc     = c
        df2b_dc    = numpy.empty((len(c), x.size))

        Ri = calc_R(xc, yc)
        df2b_dc[0] = old_div((xc - x),Ri)                   # dR/dxc
        df2b_dc[1] = old_div((yc - y),Ri)                   # dR/dyc
        df2b_dc    = df2b_dc - df2b_dc.mean(axis=1)[:, numpy.newaxis]

        return df2b_dc

    center_estimate = x_m, y_m
    center_2b, ier = optimize.leastsq(f_2b, center_estimate, Dfun=Df_2b, col_deriv=True)

    xc_2b, yc_2b = center_2b
    Ri_2b        = calc_R(*center_2b)
    R_2b         = Ri_2b.mean()
    
    #residu_2b    = sum((Ri_2b - R_2b)**2)
    return xc_2b, yc_2b, R_2b

def get_SSE(a,b,r,x,y):
    """
    input: a, b, r, x, y.  circle center, radius, xpts, ypts
    output: SSE
    """
    SSE = 0
    X = numpy.array(x)
    Y = numpy.array(y)
    for i in range(len(X)):
        x = X[i]
        y = Y[i]
        v = (numpy.sqrt( (x -a)**2 + (y - b)**2 ) - r )**2
        SSE += v
    return SSE

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
# pylint: skip-file
# pylint: disable-all
# causes too many errors and crashes

##from Tkinter import *
from builtins import input
from builtins import str
from builtins import range
from past.utils import old_div
import sys
import os
sys.path.insert(0, os.getcwd())
import numpy

# no longer setting backend here
from pmag_env import set_env
isServer = set_env.isServer
verbose = set_env.verbose

# wmpl_version=matplotlib.__version__
import pmagpy.pmag as pmag
import pylab
globals = 0
graphmenu = 0
global version_num
version_num = pmag.get_version()
# matplotlib.ticker_Formatter.xaxis.set_powerlimits((-3,4))
# matplotlib.ticker_Formatter.yaxis.set_powerlimits((-3,4))


def poly(X, Y, deg):
    return pylab.polyfit(X, Y, deg)


def showFIG(fig):
    pylab.figure(fig)
    pylab.show()


def drawFIGS(FIGS):
    """
    Can only be used if matplotlib backend is set to TKAgg
    Does not play well with wxPython
    """
    pylab.ion()
    for fig in list(FIGS.keys()):
        pylab.figure(FIGS[fig])
        pylab.draw()
    pylab.ioff()


def clearFIG(fignum):
    pylab.figure(num=fignum)
    pylab.clf()
    if not isServer:
        pylab.figtext(.02, .01, version_num)

# def gui_init(gvars,interface):
#	global globals, graphmenu
##	globals = gvars
##	graphmenu = interface
#


def click(event):
    print('you clicked', event.xdata, event.ydata)
#
#


def delticks(fig):  # deletes half the x-axis tick marks
    locs = fig.xaxis.get_ticklocs()
    nlocs = numpy.delete(locs, list(range(0, len(locs), 2)))
    fig.set_xticks(nlocs)


fig_x_pos = 25
fig_y_pos = 25
plt_num = 0


def plot_init(fignum, w, h):
    """
    initializes plot number fignum with width w and height h
    """
    global fig_x_pos, fig_y_pos, plt_num
    dpi = 80
    # pylab.ion()
    plt_num += 1
    pylab.figure(num=fignum, figsize=(w, h), dpi=dpi)
    if not isServer:
        pylab.get_current_fig_manager().show()
        # pylab.get_current_fig_manager().window.wm_geometry('+%d+%d' %
        # (fig_x_pos,fig_y_pos)) # this only works with matplotlib.use('TKAgg')
        fig_x_pos = fig_x_pos + dpi * (w) + 25
        if plt_num == 3:
            plt_num = 0
            fig_x_pos = 25
            fig_y_pos = fig_y_pos + dpi * (h) + 25
        pylab.figtext(.02, .01, version_num)
# pylab.connect('button_press_event',click)
#
    # pylab.ioff()


def plot3d_init(fignum):
    """
    initializes 3D plot
    """
    from mpl_toolkits.mplot3d import Axes3D
    fig = pylab.figure(fignum)
    ax = fig.add_subplot(111, projection='3d')
    return ax


def plot_square(fignum):
    pylab.figure(num=fignum)
    pylab.axis('equal')


def gaussfunc(y, ybar, sigma):
    """
    cumulative normal distribution function of the variable y
    with mean ybar,standard deviation sigma
    uses expression 7.1.26 from Abramowitz & Stegun
    accuracy better than 1.5e-7 absolute
    """
    x = old_div((y - ybar), (numpy.sqrt(2.) * sigma))
    t = old_div(1.0, (1.0 + .3275911 * abs(x)))
    erf = 1.0 - numpy.exp(-x * x) * t * (.254829592 - t * (.284496736 -
                                                           t * (1.421413741 - t * (1.453152027 - t * 1.061405429))))
    erf = abs(erf)
    sign = old_div(x, abs(x))
    return 0.5 * (1.0 + sign * erf)


def k_s(X):
    """
    Kolmorgorov-Smirnov statistic. Finds the
    probability that the data are distributed
    as func - used method of Numerical Recipes (Press et al., 1986)
    """
    xbar, sigma = pmag.gausspars(X)
    d, f = 0, 0.
    for i in range(1, len(X) + 1):
        b = old_div(float(i), float(len(X)))
        a = gaussfunc(X[i - 1], xbar, sigma)
        if abs(f - a) > abs(b - a):
            delta = abs(f - a)
        else:
            delta = abs(b - a)
        if delta > d:
            d = delta
        f = b
    return d, xbar, sigma


def qsnorm(p):
    """
    rational approximation for x where q(x)=d, q being the cumulative
    normal distribution function. taken from Abramowitz & Stegun p. 933
    |error(x)| < 4.5*10**-4
    """
    d = p
    if d < 0. or d > 1.:
        print('d not in (1,1) ')
        sys.exit()
    x = 0.
    if (d - 0.5) > 0:
        d = 1. - d
    if (d - 0.5) < 0:
        t2 = -2. * numpy.log(d)
        t = numpy.sqrt(t2)
        x = t - old_div((2.515517 + .802853 * t + .010328 * t2),
                        (1. + 1.432788 * t + .189269 * t2 + .001308 * t * t2))
        if p < 0.5:
            x = -x
    return x


def plotNOTES(fignum, Notes):
    for note in Notes:
        pylab.text(note['X'], note['Y'], note['text'])


def plotPTS(fignum, PTs, x, y):
    for pt in PTs:
        pylab.scatter(pt[x], pt[y], marker=pt['marker'],
                      c=pt['color'], s=pt['size'])


def show(fig):
    pylab.figure(fig)
    pylab.show()


def plot3dPTS(ax, PTs):
    Xs, Ys, Zs = [], [], []
    for pt in PTs:
        Xs.append(pt['X'])
        Ys.append(pt['Y'])
        Zs.append(pt['Z'])
    ax.scatter(Xs, Ys, Zs, marker=pt['marker'], c=pt['color'], s=pt['size'])


def plot3dLINES(ax, line, sym):
    Xs, Ys, Zs = [], [], []
    for l in line:
        Xs.append(l['X'])
        Ys.append(l['Y'])
        Zs.append(l['Z'])
    ax.plot(Xs, Ys, Zs, sym)


def plotLINES(fignum, line, sym, x, y):
    X, Y = [], []
    for l in line:
        X.append(l[x])
        Y.append(l[y])
    pylab.plot(X, Y, sym)


def plotXY(fignum, X, Y, **kwargs):
    pylab.figure(num=fignum)
#    if 'poly' in kwargs.keys():
#          coeffs=numpy.polyfit(X,Y,kwargs['poly'])
#          polynomial=numpy.poly1d(coeffs)
#          xs=numpy.arange(numpy.min(X),numpy.max(X))
#          ys=polynomial(xs)
#          pylab.plot(xs,ys)
#          print coefs
#          print polynomial
    if 'sym' in list(kwargs.keys()):
        sym = kwargs['sym']
    else:
        sym = 'ro'
    if 'lw' in list(kwargs.keys()):
        lw = kwargs['lw']
    else:
        lw = 1
    if 'xerr' in list(kwargs.keys()):
        pylab.errorbar(X, Y, fmt=sym, xerr=kwargs['xerr'])
    if 'yerr' in list(kwargs.keys()):
        pylab.errorbar(X, Y, fmt=sym, yerr=kwargs['yerr'])
    if 'axis' in list(kwargs.keys()):
        if kwargs['axis'] == 'semilogx':
            pylab.semilogx(X, Y, marker=sym[1], markerfacecolor=sym[0])
        if kwargs['axis'] == 'semilogy':
            pylab.semilogy(X, Y, marker=sym[1], markerfacecolor=sym[0])
        if kwargs['axis'] == 'loglog':
            pylab.loglog(X, Y, marker=sym[1], markerfacecolor=sym[0])
    else:
        pylab.plot(X, Y, sym, linewidth=lw)
    if 'xlab' in list(kwargs.keys()):
        pylab.xlabel(kwargs['xlab'])
    if 'ylab' in list(kwargs.keys()):
        pylab.ylabel(kwargs['ylab'])
    if 'title' in list(kwargs.keys()):
        pylab.title(kwargs['title'])
    if 'xmin' in list(kwargs.keys()):
        pylab.axis([kwargs['xmin'], kwargs['xmax'],
                    kwargs['ymin'], kwargs['ymax']])
    if 'notes' in list(kwargs.keys()):
        for note in kwargs['notes']:
            pylab.text(note[0], note[1], note[2])


def plotSITE(fignum, SiteRec, data, key):
    print('Site mean data: ')
    print('   dec    inc n_lines n_planes kappa R alpha_95 comp coord')
    print(SiteRec['site_dec'], SiteRec['site_inc'], SiteRec['site_n_lines'], SiteRec['site_n_planes'], SiteRec['site_k'],
          SiteRec['site_r'], SiteRec['site_alpha95'], SiteRec['site_comp_name'], SiteRec['site_tilt_correction'])
    print('sample/specimen, dec, inc, n_specs/a95,| method codes ')
    for i in range(len(data)):
        print('%s: %s %s %s / %s | %s' % (data[i]['er_' + key + '_name'], data[i][key + '_dec'], data[i]
                                          [key + '_inc'], data[i][key + '_n'], data[i][key + '_alpha95'], data[i]['magic_method_codes']))
    plotSLNP(fignum, SiteRec, data, key)
    plot = input("s[a]ve plot, [q]uit or <return> to continue:   ")
    if plot == 'q':
        print("CUL8R")
        sys.exit()
    if plot == 'a':
        files = {}
        for key in list(EQ.keys()):
            files[key] = site + '_' + key + '.' + fmt
        saveP(EQ, files)


def plotQQnorm(fignum, Y, title):
    pylab.figure(num=fignum)
    Y.sort()  # data
    n = len(Y)
    d, mean, sigma = k_s(Y)
    dc = old_div(0.886, numpy.sqrt(float(n)))
    print('mean,sigma, d, Dc')
    print(mean, sigma, d, dc)
    X = []  # list for normal quantile
    for i in range(1, n + 1):
        p = old_div(float(i), float(n + 1))
        X.append(qsnorm(p))
    pylab.plot(X, Y, 'ro')
    pylab.title(title)
    pylab.xlabel('Normal Quantile')
    pylab.ylabel('Data Quantile')
    bounds = pylab.axis()
    notestr = 'N: ' + '%i' % (n)
    pylab.text(-.9 * bounds[1], .9 * bounds[3], notestr)
    notestr = 'mean: ' + '%8.3e' % (mean)
    pylab.text(-.9 * bounds[1], .8 * bounds[3], notestr)
    notestr = 'std dev: ' + '%8.3e' % (sigma)
    pylab.text(-.9 * bounds[1], .7 * bounds[3], notestr)
    notestr = 'D: ' + '%8.3e' % (d)
    pylab.text(-.9 * bounds[1], .6 * bounds[3], notestr)
    notestr = 'Dc: ' + '%8.3e' % (dc)
    pylab.text(-.9 * bounds[1], .5 * bounds[3], notestr)


def plotQQunf(fignum, D, title, subplot=False):
    """
    plots data against a uniform distribution in 0=>360.
    called with plotQQunf(fignum,D,title).
    """
    if subplot == True:
        pylab.subplot(1, 2, fignum)
    else:
        pylab.figure(num=fignum)
    X, Y, dpos, dneg = [], [], 0., 0.
    for d in D:
        if d < 0:
            d = d + 360.
        if d > 360.:
            d = d - 360.
        X.append(old_div(d, 360.))
    X.sort()
    n = float(len(X))
    for i in range(len(X)):
        # expected value from uniform distribution
        Y.append(old_div((float(i) - 0.5), n))
        ds = old_div(float(i), n) - X[i]  # calculated K-S test statistic
        if dpos < ds:
            dpos = ds
        ds = X[i] - (old_div(float(i - 1.), n))
        if dneg < ds:
            dneg = ds
    pylab.plot(Y, X, 'ro')
    v = dneg + dpos  # kuiper's v
    # Mu of fisher et al. equation 5.16
    Mu = v * (numpy.sqrt(n) - 0.567 + (old_div(1.623, (numpy.sqrt(n)))))
    pylab.axis([0, 1., 0., 1.])
    bounds = pylab.axis()
    notestr = 'N: ' + '%i' % (n)
    pylab.text(.1 * bounds[1], .9 * bounds[3], notestr)
    notestr = 'Mu: ' + '%7.3f' % (Mu)
    pylab.text(.1 * bounds[1], .8 * bounds[3], notestr)
    if Mu > 1.347:
        notestr = "Non-uniform (99%)"
    elif Mu < 1.207:
        notestr = "Uniform (95%)"
    elif Mu > 1.207:
        notestr = "Uniform (99%)"
    pylab.text(.1 * bounds[1], .7 * bounds[3], notestr)
    pylab.text(.1 * bounds[1], .7 * bounds[3], notestr)
    pylab.title(title)
    pylab.xlabel('Uniform Quantile')
    pylab.ylabel('Data Quantile')
    return Mu, 1.207


def plotQQexp(fignum, I, title, subplot=False):
    """
    plots data against an exponential distribution in 0=>90.
    """
    if subplot == True:
        pylab.subplot(1, 2, fignum)
    else:
        pylab.figure(num=fignum)
    X, Y, dpos, dneg = [], [], 0., 0.
    rad = old_div(numpy.pi, 180.)
    xsum = 0
    for i in I:
        theta = (90. - i) * rad
        X.append(1. - numpy.cos(theta))
        xsum += X[-1]
    X.sort()
    n = float(len(X))
    kappa = old_div((n - 1.), xsum)
    for i in range(len(X)):
        p = old_div((float(i) - 0.5), n)
        Y.append(-numpy.log(1. - p))
        f = 1. - numpy.exp(-kappa * X[i])
        ds = old_div(float(i), n) - f
        if dpos < ds:
            dpos = ds
        ds = f - old_div((float(i) - 1.), n)
        if dneg < ds:
            dneg = ds
    if dneg > dpos:
        ds = dneg
    else:
        ds = dpos
    Me = (ds - (old_div(0.2, n))) * (numpy.sqrt(n) + 0.26 +
                                     (old_div(0.5, (numpy.sqrt(n)))))  # Eq. 5.15 from Fisher et al. (1987)

    pylab.plot(Y, X, 'ro')
    bounds = pylab.axis()
    pylab.axis([0, bounds[1], 0., bounds[3]])
    notestr = 'N: ' + '%i' % (n)
    pylab.text(.1 * bounds[1], .9 * bounds[3], notestr)
    notestr = 'Me: ' + '%7.3f' % (Me)
    pylab.text(.1 * bounds[1], .8 * bounds[3], notestr)
    if Me > 1.094:
        notestr = "Not Exponential"
    else:
        notestr = "Exponential (95%)"
    pylab.text(.1 * bounds[1], .7 * bounds[3], notestr)
    pylab.title(title)
    pylab.xlabel('Exponential Quantile')
    pylab.ylabel('Data Quantile')
    return Me, 1.094


def plotNET(fignum):
    """
    draws circle and tick marks for equal area projection
    """
#
# make the perimeter
#
    pylab.figure(num=fignum)
    pylab.clf()
    if not isServer:
        pylab.figtext(.02, .01, version_num)
    pylab.axis("off")
    Dcirc = numpy.arange(0, 361.)
    Icirc = numpy.zeros(361, 'f')
    Xcirc, Ycirc = [], []
    for k in range(361):
        XY = pmag.dimap(Dcirc[k], Icirc[k])
        Xcirc.append(XY[0])
        Ycirc.append(XY[1])
    pylab.plot(Xcirc, Ycirc, 'k')
#
# put on the tick marks
    Xsym, Ysym = [], []
    for I in range(10, 100, 10):
        XY = pmag.dimap(0., I)
        Xsym.append(XY[0])
        Ysym.append(XY[1])
    pylab.plot(Xsym, Ysym, 'k+')
    Xsym, Ysym = [], []
    for I in range(10, 90, 10):
        XY = pmag.dimap(90., I)
        Xsym.append(XY[0])
        Ysym.append(XY[1])
    pylab.plot(Xsym, Ysym, 'k+')
    Xsym, Ysym = [], []
    for I in range(10, 90, 10):
        XY = pmag.dimap(180., I)
        Xsym.append(XY[0])
        Ysym.append(XY[1])
    pylab.plot(Xsym, Ysym, 'k+')
    Xsym, Ysym = [], []
    for I in range(10, 90, 10):
        XY = pmag.dimap(270., I)
        Xsym.append(XY[0])
        Ysym.append(XY[1])
    pylab.plot(Xsym, Ysym, 'k+')
    for D in range(0, 360, 10):
        Xtick, Ytick = [], []
        for I in range(4):
            XY = pmag.dimap(D, I)
            Xtick.append(XY[0])
            Ytick.append(XY[1])
        pylab.plot(Xtick, Ytick, 'k')
    BoxX, BoxY = [-1.1, 1.1, 1.1, -1.1, -1.1], [-1.1, -1.1, 1.1, 1.1, -1.1]
    pylab.plot(BoxX, BoxY, 'k-', linewidth=.5)
    pylab.axis("equal")


def plotDI(fignum, DIblock):
    global globals
    """
    plots directions on equal area net
    """
    X_down, X_up, Y_down, Y_up = [], [], [], []  # initialize some variables
    pylab.figure(num=fignum)
#
#   plot the data - separate upper and lower hemispheres
#
    for rec in DIblock:
        Up, Down = 0, 0
        XY = pmag.dimap(rec[0], rec[1])
        if rec[1] >= 0:
            X_down.append(XY[0])
            Y_down.append(XY[1])
        else:
            X_up.append(XY[0])
            Y_up.append(XY[1])
#
    if len(X_down) > 0:
        #        pylab.scatter(X_down,Y_down,marker='s',c='r')
        pylab.scatter(X_down, Y_down, marker='o', c='blue')
        if globals != 0:
            globals.DIlist = X_down
            globals.DIlisty = Y_down
    if len(X_up) > 0:
        #        pylab.scatter(X_up,Y_up,marker='s',facecolor='none',edgecolor='black')
        pylab.scatter(X_up, Y_up, marker='o', facecolor='white',edgecolor='blue')
        if globals != 0:
            globals.DIlist = X_up
            globals.DIlisty = Y_up


def plotDIsym(fignum, DIblock, sym):
    global globals
    """
    plots directions on equal area net
    """
    X_down, X_up, Y_down, Y_up = [], [], [], []  # initialize some variables
    pylab.figure(num=fignum)
#
#   plot the data - separate upper and lower hemispheres
#
    for rec in DIblock:
        Up, Down = 0, 0
        XY = pmag.dimap(rec[0], rec[1])
        if rec[1] >= 0:
            X_down.append(XY[0])
            Y_down.append(XY[1])
        else:
            X_up.append(XY[0])
            Y_up.append(XY[1])
#
    if 'size' not in list(sym.keys()):
        size = 50
    else:
        size = sym['size']
    if 'edgecolor' not in list(sym.keys()):
        sym['edgecolor'] = 'k'
    if len(X_down) > 0:
        pylab.scatter(X_down, Y_down, marker=sym['lower'][0],
                      c=sym['lower'][1], s=size, edgecolor=sym['edgecolor'])
        if globals != 0:
            globals.DIlist = X_down
            globals.DIlisty = Y_down
    if len(X_up) > 0:
        pylab.scatter(X_up, Y_up, marker=sym['upper'][0],
                      c=sym['upper'][1], s=size, edgecolor=sym['edgecolor'])
        if globals != 0:
            globals.DIlist = X_up
            globals.DIlisty = Y_up


def plotC(fignum, pole, ang, col):
    """
    function to put a small circle on an equal area projection plot, fig,fignum
    """
    pylab.figure(num=fignum)
    D_c, I_c = pmag.circ(pole[0], pole[1], ang)
    X_c_up, Y_c_up = [], []
    X_c_d, Y_c_d = [], []
    for k in range(len(D_c)):
        XY = pmag.dimap(D_c[k], I_c[k])
        if I_c[k] < 0:
            X_c_up.append(XY[0])
            Y_c_up.append(XY[1])
        else:
            X_c_d.append(XY[0])
            Y_c_d.append(XY[1])
    pylab.plot(X_c_d, Y_c_d, col + '.', ms=5)
    pylab.plot(X_c_up, Y_c_up, 'c.', ms=2)


def plotZ(fignum, datablock, angle, s, norm):
    global globals
    """
    function to make Zijderveld diagrams
    """
    pylab.figure(num=fignum)
    pylab.clf()
    if not isServer:
        pylab.figtext(.02, .01, version_num)
    amin, amax = 0., -100.
    fact = old_div(1., datablock[0][3])   # normalize to NRM=1
    if norm == 0:
        fact = 1.
    x, y, z = [], [], []
    xb, yb, zb = [], [], []
    forVDS = []
# convert to cartesian
    recnum, delta = 0, ""
    for plotrec in datablock:
        forVDS.append(
            [plotrec[1], plotrec[2], old_div(plotrec[3], datablock[0][3])])
        rec = pmag.dir2cart(
            [(plotrec[1] - angle), plotrec[2], plotrec[3] * fact])
        if len(plotrec) == 4:
            plotrec.append('0')  # fake the ZI,IZ step for old data
        if len(plotrec) == 5:
            plotrec.append('g')  # assume good measurement if not specified
        if plotrec[5] == 'g':
          #  z.append(-rec[2])
            z.append(rec[2])
            x.append(rec[0])
          #  y.append(-rec[1])
            y.append(rec[1])
            if x[-1] > amax:
                amax = x[-1]
            if y[-1] > amax:
                amax = y[-1]
            if z[-1] > amax:
                amax = z[-1]
            if x[-1] < amin:
                amin = x[-1]
            if y[-1] < amin:
                amin = y[-1]
            if z[-1] < amin:
                amin = z[-1]
            if delta == "":
                delta = .02 * x[-1]
            #if recnum%2==0 and len(x)>0: pylab.text(x[-1]-delta,z[-1]+delta,(' '+str(recnum)),fontsize=9)
            if recnum % 2 == 0 and len(x) > 0:
                pylab.text(x[-1] + delta, z[-1] + delta,
                           (' ' + str(recnum)), fontsize=9)
            recnum += 1
        elif len(plotrec) >= 6 and plotrec[5] == 'b':
          #  zb.append(-rec[2])
            zb.append(rec[2])
            xb.append(rec[0])
          #  yb.append(-rec[1])
            yb.append(rec[1])
            if xb[-1] > amax:
                amax = xb[-1]
            if yb[-1] > amax:
                amax = yb[-1]
            if zb[-1] > amax:
                amax = zb[-1]
            if xb[-1] < amin:
                amin = xb[-1]
            if yb[-1] < amin:
                amin = yb[-1]
            if zb[-1] < amin:
                amin = zb[-1]
            if delta == "":
                delta = .02 * xb[-1]
            pylab.text(xb[-1] - delta, zb[-1] + delta,
                       (' ' + str(recnum)), fontsize=9)
            recnum += 1
# plotting stuff
    if angle != 0:
        tempstr = "\n Declination rotated by: " + str(angle) + '\n'
    if globals != 0:
        globals.text.insert(globals.END, tempstr)
        globals.Zlist = x
        globals.Zlisty = y
        globals.Zlistz = z
    if len(xb) > 0:
        pylab.scatter(xb, yb, marker='d', c='w', s=30)
        pylab.scatter(xb, zb, marker='d', c='w', s=30)
    pylab.plot(x, y, 'r')
    pylab.plot(x, z, 'b')
    pylab.scatter(x, y, marker='o', c='r')
    pylab.scatter(x, z, marker='s', c='w')
    xline = [amin, amax]
   # yline=[-amax,-amin]
    yline = [amax, amin]
    zline = [0, 0]
    pylab.plot(xline, zline)
    pylab.plot(zline, xline)
    if angle != 0:
        xlab = "X: rotated to Dec = " + '%7.1f' % (angle)
    if angle == 0:
        xlab = "X: rotated to Dec = " + '%7.1f' % (angle)
    pylab.xlabel(xlab)
    pylab.ylabel("Circles: Y; Squares: Z")
    tstring = s + ': NRM = ' + '%9.2e' % (datablock[0][3])
    pylab.axis([amin, amax, amax, amin])
    pylab.axis("equal")
    pylab.title(tstring)
#
#


def plotMT(fignum, datablock, s, num, units, norm):
    global globals, graphmenu
    Ints = []
    for plotrec in datablock:
        Ints.append(plotrec[3])
    Ints.sort()
    pylab.figure(num=fignum)
    T, M, Tv, recnum = [], [], [], 0
    Mex, Tex, Vdif = [], [], []
    recbak = []
    for rec in datablock:
        if rec[5] == 'g':
            if units == "T":
                T.append(rec[0] * 1e3)
                Tv.append(rec[0] * 1e3)
                if recnum > 0:
                    Tv.append(rec[0] * 1e3)
            elif units == "U":
                T.append(rec[0])
                Tv.append(rec[0])
                if recnum > 0:
                    Tv.append(rec[0])
            elif units == "K":
                T.append(rec[0] - 273)
                Tv.append(rec[0] - 273)
                if recnum > 0:
                    Tv.append(rec[0] - 273)
            elif "T" in units and "K" in units:
                if rec[0] < 1.:
                    T.append(rec[0] * 1e3)
                    Tv.append(rec[0] * 1e3)
                else:
                    T.append(rec[0] - 273)
                    Tv.append(rec[0] - 273)
                    if recnum > 0:
                        Tv.append(rec[0] - 273)
            else:
                T.append(rec[0])
                Tv.append(rec[0])
                if recnum > 0:
                    Tv.append(rec[0])
            if norm == 1:
                M.append(old_div(rec[3], Ints[-1]))
            else:
                M.append(rec[3])
            if recnum > 0 and len(rec) > 0 and len(recbak) > 0:
                v = []
                if recbak[0] != rec[0]:
                    V0 = pmag.dir2cart([recbak[1], recbak[2], recbak[3]])
                    V1 = pmag.dir2cart([rec[1], rec[2], rec[3]])
                    for el in range(3):
                        v.append(abs(V1[el] - V0[el]))
                    vdir = pmag.cart2dir(v)
                    # append vector difference
                    Vdif.append(old_div(vdir[2], Ints[-1]))
                    Vdif.append(old_div(vdir[2], Ints[-1]))
            recbak = []
            for el in rec:
                recbak.append(el)
            delta = .005 * M[0]
            if num == 1:
                if recnum % 2 == 0:
                    pylab.text(T[-1] + delta, M[-1],
                               (' ' + str(recnum)), fontsize=9)
            recnum += 1
        else:
            if rec[0] < 200:
                Tex.append(rec[0] * 1e3)
            if rec[0] >= 200:
                Tex.append(rec[0] - 273)
            Mex.append(old_div(rec[3], Ints[-1]))
            recnum += 1
    if globals != 0:
        globals.MTlist = T
        globals.MTlisty = M
    if len(Mex) > 0 and len(Tex) > 0:
        pylab.scatter(Tex, Mex, marker='d', color='k')
    if len(Vdif) > 0:
        Vdif.append(old_div(vdir[2], Ints[-1]))
        Vdif.append(0)
    Tv.append(Tv[-1])
    pylab.plot(T, M)
    pylab.plot(T, M, 'ro')
    if len(Tv) == len(Vdif) and norm == 1:
        pylab.plot(Tv, Vdif, 'g-')
    if units == "T":
        pylab.xlabel("Step (mT)")
    elif units == "K":
        pylab.xlabel("Step (C)")
    elif units == "J":
        pylab.xlabel("Step (J)")
    else:
        pylab.xlabel("Step [mT,C]")
    if norm == 1:
        pylab.ylabel("Fractional Magnetization")
    if norm == 0:
        pylab.ylabel("Magnetization")
    pylab.axvline(0, color='k')
    pylab.axhline(0, color='k')
    tstring = s
    pylab.title(tstring)

#
#


def plotZED(ZED, datablock, angle, s, units):
    """
    function to make equal area plot and zijderveld plot
    """
    for fignum in list(ZED.keys()):
        fig = pylab.figure(num=ZED[fignum])
        pylab.clf()
        if not isServer:
            pylab.figtext(.02, .01, version_num)
    DIbad, DIgood = [], []
    for rec in datablock:
        if rec[5] == 'b':
            DIbad.append((rec[1], rec[2]))
        else:
            DIgood.append((rec[1], rec[2]))
    badsym = {'lower': ['+', 'g'], 'upper': ['x', 'c']}
    if len(DIgood) > 0:
        plotEQ(ZED['eqarea'], DIgood, s)
        if len(DIbad) > 0:
            plotDIsym(ZED['eqarea'], DIbad, badsym)
    elif len(DIbad) > 0:
        plotEQsym(ZED['eqarea'], DIbad, badsym)
    AngleX, AngleY = [], []
    XY = pmag.dimap(angle, 90.)
    AngleX.append(XY[0])
    AngleY.append(XY[1])
    XY = pmag.dimap(angle, 0.)
    AngleX.append(XY[0])
    AngleY.append(XY[1])
    pylab.figure(num=ZED['eqarea'])
    # Draw a line for Zijderveld horizontal axis
    pylab.plot(AngleX, AngleY, 'r-')
    if AngleX[-1] == 0:
        AngleX[-1] = 0.01
    pylab.text(AngleX[-1] + (old_div(AngleX[-1], abs(AngleX[-1]))) * .1,
               AngleY[-1] + (old_div(AngleY[-1], abs(AngleY[-1]))) * .1, 'X')
    norm = 1
    #if units=="U": norm=0
    plotMT(ZED['demag'], datablock, s, 1, units, norm)
    plotZ(ZED['zijd'], datablock, angle, s, norm)


def plotDir(ZED, pars, datablock, angle):
    """
    function to put the great circle on the equal area projection
    and plot start and end points of calculation
    """
#
# find start and end points from datablock
#
    if pars["calculation_type"] == 'DE-FM':
        x, y = [], []
        pylab.figure(num=ZED['eqarea'])
        XY = pmag.dimap(pars["specimen_dec"], pars["specimen_inc"])
        x.append(XY[0])
        y.append(XY[1])
        pylab.scatter(x, y, marker='^', s=80, c='r')
        return
    StartDir, EndDir = [0, 0, 1.], [0, 0, 1.]
    for rec in datablock:
        if rec[0] == pars["measurement_step_min"]:
            StartDir[0] = rec[1]
            StartDir[1] = rec[2]
            if pars["specimen_direction_type"] == 'l':
                StartDir[2] = old_div(rec[3], datablock[0][3])
        if rec[0] == pars["measurement_step_max"]:
            EndDir[0] = rec[1]
            EndDir[1] = rec[2]
            if pars["specimen_direction_type"] == 'l':
                EndDir[2] = old_div(rec[3], datablock[0][3])

#
#  put them on the plots
#
    x, y, z, pole = [], [], [], []
    if pars["calculation_type"] != 'DE-BFP':
        pylab.figure(num=ZED['eqarea'])
        XY = pmag.dimap(pars["specimen_dec"], pars["specimen_inc"])
        x.append(XY[0])
        y.append(XY[1])
        pylab.scatter(x, y, marker='d', s=80, c='b')
        x, y, z = [], [], []
        StartDir[0] = StartDir[0] - angle
        EndDir[0] = EndDir[0] - angle
        XYZs = pmag.dir2cart(StartDir)
        x.append(XYZs[0])
      #  y.append(-XYZs[1])
      #  z.append(-XYZs[2])
        y.append(XYZs[1])
        z.append(XYZs[2])
        XYZe = pmag.dir2cart(EndDir)
        x.append(XYZe[0])
      #  y.append(-XYZe[1])
    #   z.append(-XYZe[2])
        y.append(XYZe[1])
        z.append(XYZe[2])
        pylab.figure(num=ZED['zijd'])
        pylab.scatter(x, y, marker='d', s=80, c='g')
        pylab.scatter(x, z, marker='d', s=80, c='g')
        pylab.scatter(x, y, marker='o', c='r', s=20)
        pylab.scatter(x, z, marker='s', c='w', s=20)
#
# put on best fit line
# new way (from Jeff Gee's favorite website http://GET THIS):
#      P1=pmag.dir2cart([(pars["specimen_dec"]-angle),pars["specimen_inc"],1.]) #  princ comp.
#      P2=pmag.dir2cart([(pars["specimen_dec"]-angle-180.),-pars["specimen_inc"],1.]) # antipode of princ comp.
#      P21,Ps,Pe,Xs,Xe=[],[],[],[],[]
#      for i in range(3):
#          P21.append(P2[i]-P1[i])
#          Ps.append(XYZs[i]-P1[i])
#          Pe.append(XYZe[i]-P1[i])
#      norm=pmag.cart2dir(P21)[2]
#      us=(Ps[0]*P21[0]+Ps[1]*P21[1]+Ps[2]*P21[2])/(norm**2)
#      ue=(Pe[0]*P21[0]+Pe[1]*P21[1]+Pe[2]*P21[2])/(norm**2)
#      px,py,pz=[],[],[]
#      for i in range(3):
#          Xs.append(P1[i]+us*(P2[i]-P1[i]))
#          Xe.append(P1[i]+ue*(P2[i]-P1[i]))
#   old way:
        cm = pars["center_of_mass"]
        if cm != [0., 0., 0.]:
            cmDir = pmag.cart2dir(cm)
            cmDir[0] = cmDir[0] - angle
            cmDir[2] = old_div(cmDir[2], (datablock[0][3]))
            cm = pmag.dir2cart(cmDir)
            diff = []
            for i in range(3):
                diff.append(XYZe[i] - XYZs[i])
            R = numpy.sqrt(diff[0]**2 + diff[1]**2 + diff[2]**2)
            P = pmag.dir2cart(
                ((pars["specimen_dec"] - angle), pars["specimen_inc"], old_div(R, 2.5)))
            px, py, pz = [], [], []
            px.append((cm[0] + P[0]))
        #  py.append(-(cm[1]+P[1]))
        #  pz.append(-(cm[2]+P[2]))
            py.append((cm[1] + P[1]))
            pz.append((cm[2] + P[2]))
            px.append((cm[0] - P[0]))
        #  py.append(-(cm[1]-P[1]))
        #  pz.append(-(cm[2]-P[2]))
            py.append((cm[1] - P[1]))
            pz.append((cm[2] - P[2]))

#       px.append(Xs[0]+cm[0])
#       px.append(Xe[0]+cm[0])
#       py.append(-(Xs[1]+cm[1]))
#       py.append(-(Xe[1]+cm[1]))
#       pz.append(-(Xs[2]+cm[2]))
#       pz.append(-(Xe[2]+cm[2]))
        pylab.plot(px, py, 'g', linewidth=2)
        pylab.plot(px, pz, 'g', linewidth=2)
        pylab.axis("equal")
    else:
        pylab.figure(num=ZED['eqarea'])
        XY = pmag.dimap(StartDir[0], StartDir[1])
        x.append(XY[0])
        y.append(XY[1])
        XY = pmag.dimap(EndDir[0], EndDir[1])
        x.append(XY[0])
        y.append(XY[1])
        pylab.scatter(x, y, marker='d', s=80, c='b')
        pole.append(pars["specimen_dec"])
        pole.append(pars["specimen_inc"])
        plotC(ZED['eqarea'], pole, 90., 'g')
        pylab.xlim((-1., 1.))
        pylab.ylim((-1., 1.))
        pylab.axis("equal")


def plotA(fignum, indata, s, units):
    global globals
    pylab.figure(num=fignum)
    pylab.clf()
    if not isServer:
        pylab.figtext(.02, .01, version_num)
    x, y, x_zi, y_zi, x_iz, y_iz, xptrm, yptrm, xptrmt, yptrmt = [
    ], [], [], [], [], [], [], [], [], []
    xzptrm, yzptrm = [], []  # zero field ptrm checks
    zptrm_check = []
    first_Z, first_I, ptrm_check, ptrm_tail, zptrm_check = indata[
        0], indata[1], indata[2], indata[3], indata[4]
    if len(indata) > 6:
        if len(indata[-1]) > 1:
            s = s + ":PERP"  # there are Delta checks, must be a LP-PI-M-S perp experiment
    recnum, yes, Nptrm, Nptrmt, diffcum = 0, 0, 0, 0, 0
# plot the NRM-pTRM data
    forVDS = []
    for zrec in first_Z:
        forVDS.append([zrec[1], zrec[2], old_div(zrec[3], first_Z[0][3])])
        ZI = zrec[4]
        if zrec[0] == '0':
            irec = ['0', 0, 0, 0]
        if zrec[0] == '273' and units == 'K':
            irec = ['273', 0, 0, 0]
        else:
            for irec in first_I:
                if irec[0] == zrec[0]:
                    break
# save the NRM data used for calculation in Vi
        x.append(old_div(irec[3], first_Z[0][3]))
        y.append(old_div(zrec[3], first_Z[0][3]))
        if ZI == 1:
            x_zi.append(old_div(irec[3], first_Z[0][3]))
            y_zi.append(old_div(zrec[3], first_Z[0][3]))
        else:
            x_iz.append(old_div(irec[3], first_Z[0][3]))
            y_iz.append(old_div(zrec[3], first_Z[0][3]))
        pylab.text(x[-1], y[-1], (' ' + str(recnum)), fontsize=9)
        recnum += 1
# now deal with ptrm checks.
    if len(ptrm_check) != 0:
        for prec in ptrm_check:
            step = prec[0]
            for zrec in first_Z:
                if zrec[0] == step:
                    break
            xptrm.append(old_div(prec[3], first_Z[0][3]))
            yptrm.append(old_div(zrec[3], first_Z[0][3]))
# now deal with zptrm checks.
    if len(zptrm_check) != 0:
        for prec in zptrm_check:
            step = prec[0]
            for zrec in first_Z:
                if zrec[0] == step:
                    break
            xzptrm.append(old_div(prec[3], first_Z[0][3]))
            yzptrm.append(old_div(zrec[3], first_Z[0][3]))
# and the pTRM tails
    if len(ptrm_tail) != 0:
        for trec in ptrm_tail:
            step = trec[0]
            for irec in first_I:
                if irec[0] == step:
                    break
            xptrmt.append(old_div(irec[3], first_Z[0][3]))
            yptrmt.append((old_div(trec[3], first_Z[0][3])))
# now plot stuff
    if len(x) == 0:
        print("Can't do nuttin for ya")
        return
    try:
        if len(x_zi) > 0:
            pylab.scatter(x_zi, y_zi, marker='o', c='r',
                          edgecolors="none")  # zero field-infield
        if len(x_iz) > 0:
            pylab.scatter(x_iz, y_iz, marker='s', c='b',
                          faceted="True")  # infield-zerofield
    except:
        if len(x_zi) > 0:
            pylab.scatter(x_zi, y_zi, marker='o', c='r')  # zero field-infield
        if len(x_iz) > 0:
            pylab.scatter(x_iz, y_iz, marker='s', c='b')  # infield-zerofield
    pylab.plot(x, y, 'r')
    if globals != 0:
        globals.MTlist = x
        globals.MTlisty = y
    if len(xptrm) > 0:
        pylab.scatter(xptrm, yptrm, marker='^', c='g', s=80)
    if len(xzptrm) > 0:
        pylab.scatter(xzptrm, yzptrm, marker='v', c='c', s=80)
    if len(xptrmt) > 0:
        pylab.scatter(xptrmt, yptrmt, marker='s', c='b', s=80)
    try:
        pylab.axhline(0, color='k')
        pylab.axvline(0, color='k')
    except:
        pass
    pylab.xlabel("pTRM gained")
    pylab.ylabel("NRM remaining")
    tstring = s + ': NRM = ' + '%9.2e' % (first_Z[0][3])
    pylab.title(tstring)
# put on VDS
    vds = pmag.dovds(forVDS)
    pylab.axhline(vds, color='b')
    pylab.text(1., vds - .1, ('VDS '), fontsize=9)
#    bounds=pylab.axis()
#    if bounds[1]<1:pylab.axis([bounds[0], 1., bounds[2], bounds[3]])
#
#


def plotNP(fignum, indata, s, units):
    global globals
    first_Z, first_I, ptrm_check, ptrm_tail = indata[0], indata[1], indata[2], indata[3]
    pylab.figure(num=fignum)
    pylab.clf()
    if not isServer:
        pylab.figtext(.02, .01, version_num)
    X, Y, recnum = [], [], 0
#
    for rec in first_Z:
        if units == "K":
            if rec[0] != 0:
                X.append(rec[0] - 273.)
            else:
                X.append(rec[0])
        if units == "J":
            X.append(rec[0])
        Y.append(old_div(rec[3], first_Z[0][3]))
        delta = .02 * Y[0]
        if recnum % 2 == 0:
            pylab.text(X[-1] - delta, Y[-1] + delta,
                       (' ' + str(recnum)), fontsize=9)
        recnum += 1
    pylab.plot(X, Y)
    pylab.scatter(X, Y, marker='o', color='b')
    X, Y = [], []
    for rec in first_I:
        if units == "K":
            if rec[0] != 0:
                X.append(rec[0] - 273)
            else:
                X.append(rec[0])
        if units == "J":
            X.append(rec[0])
        Y.append(old_div(rec[3], first_Z[0][3]))
    if globals != 0:
        globals.DIlist = X
        globals.DIlisty = Y
    pylab.plot(X, Y)
    pylab.scatter(X, Y, marker='s', color='r')
    pylab.ylabel("Circles: NRM; Squares: pTRM")
    if units == "K":
        pylab.xlabel("Temperature (C)")
    if units == "J":
        pylab.xlabel("Microwave Energy (J)")
    title = s + ": NRM = " + '%9.2e' % (first_Z[0][3])
    pylab.title(title)
    pylab.axhline(y=0, xmin=0, xmax=1, color='k')
    pylab.axvline(x=0, ymin=0, ymax=1, color='k')


def plotAZ(ZED, araiblock, zijdblock, s, units):
    plotNP(ZED['deremag'], araiblock, s, units)
    angle = zijdblock[0][1]
    norm = 1
    if units == "U":
        norm = 0
    plotZ(ZED['zijd'], zijdblock, angle, s, norm)
    plotA(ZED['arai'], araiblock, s, units)
    plotTEQ(ZED['eqarea'], araiblock, s, "")


def plotSHAW(SHAW, shawblock, zijdblock, field, s):
    angle = zijdblock[0][1]
    plotZ(SHAW['zijd'], zijdblock, angle, s)
    NRM, TRM, ARM1, ARM2 = shawblock[0], shawblock[1], shawblock[2], shawblock[3]
    TRM_ADJ = shawblock[4]
    pylab.figure(num=SHAW['nrmtrm'])
    pylab.clf()
    if not isServer:
        pylab.figtext(.02, .01, version_num)
    X, Y, recnum = [], [], 0
    Nmax = NRM[0][1]
#
    for k in range(len(NRM)):
        Y.append(old_div(NRM[k][1], Nmax))
        X.append(old_div(TRM[k][1], Nmax))
#        delta=.02*Y[0]
#        if recnum%2==0: pylab.text(X[-1]-delta,Y[-1]+delta,(' '+str(recnum)),fontsize=9)
#        recnum+=1
    pylab.scatter(X, Y, marker='o', color='r')
    pylab.plot(X, Y)
    pylab.xlabel("TRM")
    pylab.ylabel("NRM")
    title = s + ": NRM = " + '%9.2e' % (Nmax)
    pylab.title(title)
    pylab.figure(num=SHAW['arm1arm2'])
    pylab.clf()
    if not isServer:
        pylab.figtext(.02, .01, version_num)
    X, Y, recnum = [], [], 0
    Nmax = ARM1[0][1]
#
    for k in range(len(ARM1)):
        Y.append(old_div(ARM2[k][1], Nmax))
        X.append(old_div(ARM1[k][1], Nmax))
#        delta=.02*Y[0]
#        if recnum%2==0: pylab.text(X[-1]-delta,Y[-1]+delta,(' '+str(recnum)),fontsize=9)
#        recnum+=1
    pylab.scatter(X, Y, marker='o', color='r')
    pylab.plot(X, Y)
    pylab.xlabel("ARM2")
    pylab.ylabel("ARM1")
    title = s + ": ARM1 = " + '%9.2e' % (Nmax)
    pylab.title(title)
    pylab.figure(num=SHAW['nrmtrmC'])
    pylab.clf()
    if not isServer:
        pylab.figtext(.02, .01, version_num)
    X, Y, recnum = [], [], 0
    Nmax = NRM[0][1]
#
    for k in range(len(NRM)):
        Y.append(old_div(NRM[k][1], Nmax))
        X.append(old_div(TRM_ADJ[k][1], Nmax))
#        delta=.02*Y[0]
#        if recnum%2==0: pylab.text(X[-1]-delta,Y[-1]+delta,(' '+str(recnum)),fontsize=9)
#        recnum+=1
    pylab.scatter(X, Y, marker='o', color='r')
    pylab.plot(X, Y)
    pylab.xlabel("TRM*")
    pylab.ylabel("NRM")
    spars = pylab.polyfit(X, Y, 1)
    Banc = spars[0] * field
    print(spars[0], field)
    print('Banc= ', Banc * 1e6, ' uT')
    notestr = 'Banc = ' + '%5.1f' % (Banc * 1e6) + ' uT'
    pylab.text(.5 * TRM[-1][1] + .2, .9, notestr)


def plotB(Figs, araiblock, zijdblock, pars):
    angle = zijdblock[0][1]
    plotblock = []
    Dir, zx, zy, zz, ax, ay = [], [], [], [], [], []
    zstart, zend = 0, len(zijdblock)
    first_Z, first_I = araiblock[0], araiblock[1]
    for rec in zijdblock:
        if rec[0] == pars["measurement_step_min"]:
            Dir.append((rec[1] - angle, rec[2],
                        old_div(rec[3], zijdblock[0][3])))
        if rec[0] == pars["measurement_step_max"]:
            Dir.append((rec[1] - angle, rec[2],
                        old_div(rec[3], zijdblock[0][3])))
    for drec in Dir:
        cart = pmag.dir2cart(drec)
        zx.append(cart[0])
      #   zy.append(-cart[1])
      #   zz.append(-cart[2])
        zy.append(cart[1])
        zz.append(cart[2])
    if len(zx) > 0:
        pylab.figure(num=Figs['zijd'])
        pylab.scatter(zx, zy, marker='d', s=100, c='y')
        pylab.scatter(zx, zz, marker='d', s=100, c='y')
        pylab.axis("equal")
    ax.append(old_div(first_I[0][3], first_Z[0][3]))
    ax.append(old_div(first_I[-1][3], first_Z[0][3]))
    ay.append(old_div(first_Z[0][3], first_Z[0][3]))
    ay.append(old_div(first_Z[-1][3], first_Z[0][3]))
    for k in range(len(first_Z)):
        if first_Z[k][0] == pars["measurement_step_min"]:
            ay[0] = (old_div(first_Z[k][3], first_Z[0][3]))
        if first_Z[k][0] == pars["measurement_step_max"]:
            ay[1] = (old_div(first_Z[k][3], first_Z[0][3]))
        if first_I[k][0] == pars["measurement_step_min"]:
            ax[0] = (old_div(first_I[k][3], first_Z[0][3]))
        if first_I[k][0] == pars["measurement_step_max"]:
            ax[1] = (old_div(first_I[k][3], first_Z[0][3]))
    new_Z, new_I = [], []
    for zrec in first_Z:
        if zrec[0] >= pars['measurement_step_min'] and zrec[0] <= pars['measurement_step_max']:
            new_Z.append(zrec)
    for irec in first_I:
        if irec[0] >= pars['measurement_step_min'] and irec[0] <= pars['measurement_step_max']:
            new_I.append(irec)
    newblock = [new_Z, new_I]
    plotTEQ(Figs['eqarea'], newblock, "", pars)
    pylab.figure(num=Figs['arai'])
    pylab.scatter(ax, ay, marker='d', s=100, c='y')
#
#  find midpoint between two endpoints
#
    sy = []
    sy.append((pars["specimen_b"] * ax[0] +
               old_div(pars["specimen_ytot"], first_Z[0][3])))
    sy.append((pars["specimen_b"] * ax[1] +
               old_div(pars["specimen_ytot"], first_Z[0][3])))
    pylab.plot(ax, sy, 'g', linewidth=2)
    bounds = pylab.axis()
    if pars['specimen_grade'] != '':
        notestr = 'Grade: ' + pars["specimen_grade"]
        pylab.text(.7 * bounds[1], .9 * bounds[3], notestr)
    notestr = 'B: ' + '%6.2f' % (pars["specimen_int"] * 1e6) + ' uT'
    pylab.text(.7 * bounds[1], .8 * bounds[3], notestr)


def plotSLNP(fignum, SiteRec, datablock, key):
    """
    plots lines and planes on a great  circle with alpha 95 and mean
    """
# make the stereonet
    pylab.figure(num=fignum)
    plotNET(fignum)
    s = SiteRec['er_site_name']
#
#   plot on the data
#
    coord = SiteRec['site_tilt_correction']
    title = ''
    if coord == '-1':
        title = s + ": specimen coordinates"
    if coord == '0':
        title = s + ": geographic coordinates"
    if coord == '100':
        title = s + ": tilt corrected coordinates"
    DIblock, GCblock = [], []
    for plotrec in datablock:
        if plotrec[key + '_direction_type'] == 'p':  # direction is pole to plane
            GCblock.append(
                (float(plotrec[key + "_dec"]), float(plotrec[key + "_inc"])))
        else:  # assume direction is a directed line
            DIblock.append(
                (float(plotrec[key + "_dec"]), float(plotrec[key + "_inc"])))
    if len(DIblock) > 0:
        plotDI(fignum, DIblock)  # plot directed lines
    if len(GCblock) > 0:
        for pole in GCblock:
            plotC(fignum, pole, 90., 'g')  # plot directed lines
#
# put on the mean direction
#
    x, y = [], []
    XY = pmag.dimap(float(SiteRec["site_dec"]), float(SiteRec["site_inc"]))
    x.append(XY[0])
    y.append(XY[1])
    pylab.scatter(x, y, marker='d', s=80, c='g')
    pylab.title(title)
#
# get the alpha95
#
    Xcirc, Ycirc = [], []
    Da95, Ia95 = pmag.circ(float(SiteRec["site_dec"]), float(
        SiteRec["site_inc"]), float(SiteRec["site_alpha95"]))
    for k in range(len(Da95)):
        XY = pmag.dimap(Da95[k], Ia95[k])
        Xcirc.append(XY[0])
        Ycirc.append(XY[1])
    pylab.plot(Xcirc, Ycirc, 'g')


def plotLNP(fignum, s, datablock, fpars, direction_type_key):
    """
    plots lines and planes on a great  circle with alpha 95 and mean
    """
# make the stereonet
    plotNET(fignum)
#
#   plot on the data
#
    coord = datablock[0]['tilt_correction']
    title = s
    if coord == '-1':
        title = title + ": specimen coordinates"
    if coord == '0':
        title = title + ": geographic coordinates"
    if coord == '100':
        title = title + ": tilt corrected coordinates"
    DIblock, GCblock = [], []
    for plotrec in datablock:
        if plotrec[direction_type_key] == 'p':  # direction is pole to plane
            GCblock.append((float(plotrec["dec"]), float(plotrec["inc"])))
        else:  # assume direction is a directed line
            DIblock.append((float(plotrec["dec"]), float(plotrec["inc"])))
    if len(DIblock) > 0:
        plotDI(fignum, DIblock)  # plot directed lines
    if len(GCblock) > 0:
        for pole in GCblock:
            plotC(fignum, pole, 90., 'g')  # plot directed lines
#
# put on the mean direction
#
    x, y = [], []
    XY = pmag.dimap(float(fpars["dec"]), float(fpars["inc"]))
    x.append(XY[0])
    y.append(XY[1])
    pylab.figure(num=fignum)
    pylab.scatter(x, y, marker='d', s=80, c='g')
    pylab.title(title)
#
# get the alpha95
#
    Xcirc, Ycirc = [], []
    Da95, Ia95 = pmag.circ(float(fpars["dec"]), float(
        fpars["inc"]), float(fpars["alpha95"]))
    for k in range(len(Da95)):
        XY = pmag.dimap(Da95[k], Ia95[k])
        Xcirc.append(XY[0])
        Ycirc.append(XY[1])
    pylab.plot(Xcirc, Ycirc, 'g')


def plotEQ(fignum, DIblock, s):
    """
    plots directions
    """
# make the stereonet
    pylab.figure(num=fignum)
    if len(DIblock) < 1:
        return
    # pylab.clf()
    if not isServer:
        pylab.figtext(.02, .01, version_num)
    plotNET(fignum)
#
#   put on the directions
#
    plotDI(fignum, DIblock)  # plot directions
    pylab.axis("equal")
    pylab.text(-1.1, 1.15, s)


def plotEQsym(fignum, DIblock, s, sym):
    """
    plots directions with specified symbol
    """
# make the stereonet
    pylab.figure(num=fignum)
    if len(DIblock) < 1:
        return
    # pylab.clf()
    if not isServer:
        pylab.figtext(.02, .01, version_num)
    plotNET(fignum)
#
#   put on the directions
#
    plotDIsym(fignum, DIblock, sym)  # plot directions with symbols in sym
    pylab.axis("equal")
    pylab.text(-1.1, 1.15, s)
#


def plotTEQ(fignum, araiblock, s, pars):
    """
    plots directions  of pTRM steps and zero field steps
    """
    first_Z, first_I = araiblock[0], araiblock[1]
# make the stereonet
    pylab.figure(num=fignum)
    pylab.clf()
    ZIblock, IZblock, pTblock = [], [], []
    for zrec in first_Z:  # sort out the zerofield steps
        if zrec[4] == 1:  # this is a ZI step
            ZIblock.append([zrec[1], zrec[2]])
        else:
            IZblock.append([zrec[1], zrec[2]])
    plotNET(fignum)
    if pars != "":
        min, max = float(pars["measurement_step_min"]), float(
            pars["measurement_step_max"])
    else:
        min, max = first_I[0][0], first_I[-1][0]
    for irec in first_I:
        if irec[1] != 0 and irec[1] != 0 and irec[0] >= min and irec[0] <= max:
            pTblock.append([irec[1], irec[2]])
    if len(ZIblock) < 1 and len(IZblock) < 1 and len(pTblock) < 1:
        return
    if not isServer:
        pylab.figtext(.02, .01, version_num)
#
#   put on the directions
#
    sym = {'lower': ['o', 'r'], 'upper': ['o', 'm']}
    if len(ZIblock) > 0:
        plotDIsym(fignum, ZIblock, sym)  # plot ZI directions
    sym = {'lower': ['s', 'b'], 'upper': ['s', 'c']}
    if len(IZblock) > 0:
        plotDIsym(fignum, IZblock, sym)  # plot IZ directions
    sym = {'lower': ['^', 'g'], 'upper': ['^', 'y']}
    if len(pTblock) > 0:
        plotDIsym(fignum, pTblock, sym)  # plot pTRM directions
    pylab.axis("equal")
    pylab.text(-1.1, 1.15, s)


def saveP(Figs, filenames, **kwargs):
    for key in list(Figs.keys()):
        try:
            pylab.figure(num=Figs[key])
            fname = filenames[key]
            if not isServer:  # remove illegal ':' character for windows
                fname = fname.replace(':', '_')
            if 'dpi' in list(kwargs.keys()):
                pylab.savefig(fname.replace('/', '-'), dpi=kwargs['dpi'])
            else:
                pylab.savefig(fname.replace('/', '-'))
            if verbose:
                print(Figs[key], " saved in ", fname.replace('/', '-'))
        except:
            print('could not save: ', Figs[key], filenames[key])
            print("output file format not supported ")
    return
#


def plotEVEC(fignum, Vs, symsize, title):
    """
    plots eigenvector directions of S vectors
    """
#
    pylab.figure(num=fignum)
    pylab.text(-1.1, 1.15, title)
    # plot V1s as squares, V2s as triangles and V3s as circles
    symb, symkey = ['s', 'v', 'o'], 0
    col = ['r', 'b', 'k']  # plot V1s rec, V2s blue, V3s black
    for VEC in range(3):
        X, Y = [], []
        for Vdirs in Vs:
            #
            #
            #   plot the V1 data  first
            #
            XY = pmag.dimap(Vdirs[VEC][0], Vdirs[VEC][1])
            X.append(XY[0])
            Y.append(XY[1])
        pylab.scatter(X, Y, s=symsize,
                      marker=symb[VEC], c=col[VEC], edgecolors='none')
    pylab.axis("equal")
#


def plotELL(fignum, pars, col, lower, plot):
    """
    function to calculate points on an ellipse about Pdec,Pdip with angle beta,gamma
    """
    pylab.figure(num=fignum)
    rad = old_div(numpy.pi, 180.)
    Pdec, Pinc, beta, Bdec, Binc, gamma, Gdec, Ginc = pars[0], pars[
        1], pars[2], pars[3], pars[4], pars[5], pars[6], pars[7]
    if beta > 90. or gamma > 90:
        beta = 180. - beta
        gamma = 180. - gamma
        Pdec = Pdec - 180.
        Pinc = -Pinc
    beta, gamma = beta * rad, gamma * rad  # convert to radians
    X_ell, Y_ell, X_up, Y_up, PTS = [], [], [], [], []
    nums = 201
    xnum = old_div(float(nums - 1.), 2.)
# set up t matrix
    t = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    X = pmag.dir2cart((Pdec, Pinc, 1.0))  # convert to cartesian coordintes
    if lower == 1 and X[2] < 0:
        for i in range(3):
            X[i] = -X[i]
# set up rotation matrix t
    t[0][2] = X[0]
    t[1][2] = X[1]
    t[2][2] = X[2]
    X = pmag.dir2cart((Bdec, Binc, 1.0))
    if lower == 1 and X[2] < 0:
        for i in range(3):
            X[i] = -X[i]
    t[0][0] = X[0]
    t[1][0] = X[1]
    t[2][0] = X[2]
    X = pmag.dir2cart((Gdec, Ginc, 1.0))
    if lower == 1 and X[2] < 0:
        for i in range(3):
            X[i] = -X[i]
    t[0][1] = X[0]
    t[1][1] = X[1]
    t[2][1] = X[2]
# set up v matrix
    v = [0, 0, 0]
    for i in range(nums):  # incremental point along ellipse
        psi = float(i) * numpy.pi / xnum
        v[0] = numpy.sin(beta) * numpy.cos(psi)
        v[1] = numpy.sin(gamma) * numpy.sin(psi)
        v[2] = numpy.sqrt(1. - v[0]**2 - v[1]**2)
        elli = [0, 0, 0]
# calculate points on the ellipse
        for j in range(3):
            for k in range(3):
                # cartesian coordinate j of ellipse
                elli[j] = elli[j] + t[j][k] * v[k]
        PTS.append(pmag.cart2dir(elli))
        # put on an equal area projection
        R = old_div(numpy.sqrt(
            1. - abs(elli[2])), (numpy.sqrt(elli[0]**2 + elli[1]**2)))
        if elli[2] < 0:
            #            for i in range(3): elli[i]=-elli[i]
            X_up.append(elli[1] * R)
            Y_up.append(elli[0] * R)
        else:
            X_ell.append(elli[1] * R)
            Y_ell.append(elli[0] * R)
    if plot == 1:
        if X_ell != []:
            pylab.plot(X_ell, Y_ell, col)
        if X_up != []:
            pylab.plot(X_up, Y_up, 'k-')
    else:
        return PTS


#
#
fig_y_pos = 25


def Vplot_init(fignum, w, h):
    # this is same as plot_init, but stacks things  vertically
    global fig_y_pos
    dpi = 80
    # pylab.ion()
    pylab.figure(num=fignum, figsize=(w, h), dpi=dpi)
#    if not isServer:
#        pylab.get_current_fig_manager().window.wm_geometry('+%d+%d' % (25,fig_y_pos))
#        fig_y_pos = fig_y_pos + dpi*(h) + 25


def plotSTRAT(fignum, data, labels):
    #
    # plots a time/depth series
    #
    Vplot_init(fignum, 10, 3)
    xlab, ylab, title = labels[0], labels[1], labels[2]
    X, Y = [], []
    for rec in data:
        X.append(rec[0])
        Y.append(rec[1])
    pylab.plot(X, Y)
    pylab.plot(X, Y, 'ro')
    pylab.xlabel(xlab)
    pylab.ylabel(ylab)
    pylab.title(title)

#
#


def plotCDF(fignum, data, xlab, sym, title, **kwargs):
    """ Makes a plot of the cumulative distribution function.  Uses the call:
x,y=plotCDF(fignum,data,xlab,sym,title,**kwargs) where fignum is the figure number.
data is a list of data to be plotted, xlab is the label for the x axis.
sym is the desired line style and color, title is the plot title
and **kwargs is a dictionary: {'color': color, 'linewidth':linewidth}
this function returns x and y"""
#
# plots a CDF of data
    #if len(sym)==1:sym=sym+'-'
    fig = pylab.figure(num=fignum)
    # sdata=numpy.array(data).sort()
    sdata = []
    for d in data:
        sdata.append(d)  # have to copy the data to avoid overwriting it!
    sdata.sort()
    X, Y = [], []
    color = ""
    for j in range(len(sdata)):
        Y.append(old_div(float(j), float(len(sdata))))
        X.append(sdata[j])
    if 'color' in list(kwargs.keys()):
        color = kwargs['color']
    if 'linewidth' in list(kwargs.keys()):
        lw = kwargs['linewidth']
    else:
        lw = 1
    if color != "":
        pylab.plot(X, Y, color=sym, linewidth=lw)
    else:
        pylab.plot(X, Y, sym, linewidth=lw)

    pylab.xlabel(xlab)
    pylab.ylabel('Cumulative Distribution')
    pylab.title(title)
    return X, Y
#


def plotHs(fignum, Ys, c, ls):
    fig = pylab.figure(num=fignum)
    for yv in Ys:
        bounds = pylab.axis()
        pylab.axhline(y=yv, xmin=0, xmax=1, linewidth=1, color=c, linestyle=ls)
#


def plotVs(fignum, Xs, c, ls):
    fig = pylab.figure(num=fignum)
    for xv in Xs:
        bounds = pylab.axis()
        pylab.axvline(
            x=xv, ymin=bounds[2], ymax=bounds[3], linewidth=1, color=c, linestyle=ls)


def plotTS(fignum, dates, ts):
    Vplot_init(fignum, 10, 3)
    TS, Chrons = pmag.get_TS(ts)
    p = 1
    X, Y = [], []
    for d in TS:
        if d <= dates[1]:
            if d >= dates[0]:
                if len(X) == 0:
                    ind = TS.index(d)
                    X.append(TS[ind - 1])
                    Y.append(p % 2)
                X.append(d)
                Y.append(p % 2)
                p += 1
                X.append(d)
                Y.append(p % 2)
        else:
            X.append(dates[1])
            Y.append(p % 2)
            pylab.plot(X, Y, 'k')
            plotVs(fignum, dates, 'w', '-')
            plotHs(fignum, [1.1, -.1], 'w', '-')
            pylab.xlabel("Age (Ma): " + ts)
            isign = -1
            for c in Chrons:
                off = -.1
                isign = -1 * isign
                if isign > 0:
                    off = 1.05
                if c[1] >= X[0] and c[1] < X[-1]:
                    pylab.text(c[1] - .2, off, c[0])
            return


def plotHYS(fignum, B, M, s):
    """
   function to plot hysteresis data
    """
    from . import spline
    if fignum != 0:
        pylab.figure(num=fignum)
        pylab.clf()
        if not isServer:
            pylab.figtext(.02, .01, version_num)
    hpars = {}
# close up loop
    Npts = len(M)
    B70 = 0.7 * B[0]  # 70 percent of maximum field
    for b in B:
        if b < B70:
            break
    Nint = B.index(b) - 1
    if Nint > 30:
        Nint = 30
    if Nint < 10:
        Nint = 10
    Bzero, Mzero, Mfix, Mnorm, Madj, MadjN = "", "", [], [], [], []
    Mazero = ""
    m_init = 0.5 * (M[0] + M[1])
    m_fin = 0.5 * (M[-1] + M[-2])
    diff = m_fin - m_init
    Bmin = 0.
    for k in range(Npts):
        frac = old_div(float(k), float(Npts - 1))
        Mfix.append((M[k] - diff * frac))
        if Bzero == "" and B[k] < 0:
            Bzero = k
        if B[k] < Bmin:
            Bmin = B[k]
            kmin = k
    # adjust slope with first 30 data points (throwing out first 3)
    Bslop = B[2:Nint + 2]
    Mslop = Mfix[2:Nint + 2]
    # best fit line to high field points
    polyU = pylab.polyfit(Bslop, Mslop, 1)
    # adjust slope with first 30 points of ascending branch
    Bslop = B[kmin:kmin + (Nint + 1)]
    Mslop = Mfix[kmin:kmin + (Nint + 1)]
    # best fit line to high field points
    polyL = pylab.polyfit(Bslop, Mslop, 1)
    xhf = 0.5 * (polyU[0] + polyL[0])  # mean of two slopes
    # convert B to A/m, high field slope in m^3
    hpars['hysteresis_xhf'] = '%8.2e' % (xhf * 4 * numpy.pi * 1e-7)
    meanint = 0.5 * (polyU[1] + polyL[1])  # mean of two intercepts
    Msat = 0.5 * (polyU[1] - polyL[1])  # mean of saturation remanence
    Moff = []
    for k in range(Npts):
        # take out linear slope and offset (makes symmetric about origin)
        Moff.append((Mfix[k] - xhf * B[k] - meanint))
        if Mzero == "" and Moff[k] < 0:
            Mzero = k
        if Mzero != "" and Mazero == "" and Moff[k] > 0:
            Mazero = k
    hpars['hysteresis_ms_moment'] = '%8.3e' % (Msat)  # Ms in Am^2
#
# split into upper and lower loops for splining
    Mupper, Bupper, Mlower, Blower = [], [], [], []
    deltaM, Bdm = [], []  # diff between upper and lower curves at Bdm
    for k in range(kmin - 2, 0, -1):
        Mupper.append(old_div(Moff[k], Msat))
        Bupper.append(B[k])
    for k in range(kmin + 2, len(B)):
        Mlower.append(old_div(Moff[k], Msat))
        Blower.append(B[k])
    Iupper = spline.Spline(Bupper, Mupper)  # get splines for upper up and down
    Ilower = spline.Spline(Blower, Mlower)  # get splines for lower
    incr = B[0] * .01
    for b in numpy.arange(B[0], step=incr):  # get range of field values
        Mpos = ((Iupper(b) - Ilower(b)))  # evaluate on both sides of B
        Mneg = ((Iupper(-b) - Ilower(-b)))
        Bdm.append(b)
        deltaM.append(0.5 * (Mpos + Mneg))  # take average delta M
    for k in range(Npts):
        MadjN.append(old_div(Moff[k], Msat))
        Mnorm.append(old_div(M[k], Msat))
    if fignum != 0:
        pylab.plot(B, Mnorm, 'r')
        pylab.plot(B, MadjN, 'b')
        pylab.xlabel('B (T)')
        pylab.ylabel("M/Msat")
        pylab.axhline(0, color='k')
        pylab.axvline(0, color='k')
        pylab.title(s)
# find Mr : average of two spline fits evaluted at B=0 (times Msat)
    Mr = Msat * 0.5 * (Iupper(0.) - Ilower(0.))
    hpars['hysteresis_mr_moment'] = '%8.3e' % (Mr)
# find Bc (x intercept), interpolate between two bounding points
    Bz = B[Mzero - 1:Mzero + 1]
    Mz = Moff[Mzero - 1:Mzero + 1]
    Baz = B[Mazero - 1:Mazero + 1]
    Maz = Moff[Mazero - 1:Mazero + 1]
    try:
        # best fit line through two bounding points
        poly = pylab.polyfit(Bz, Mz, 1)
        Bc = old_div(-poly[1], poly[0])  # x intercept
        # best fit line through two bounding points
        poly = pylab.polyfit(Baz, Maz, 1)
        Bac = old_div(-poly[1], poly[0])  # x intercept
        hpars['hysteresis_bc'] = '%8.3e' % (0.5 * (abs(Bc) + abs(Bac)))
    except:
        hpars['hysteresis_bc'] = '0'
    return hpars, deltaM, Bdm
#


def plotDM(fignum, B, DM, Bcr, s):
    """
    function to plot Delta M curves
    """
    pylab.figure(num=fignum)
    pylab.clf()
    if not isServer:
        pylab.figtext(.02, .01, version_num)
    pylab.plot(B, DM, 'b')
    pylab.xlabel('B (T)')
    pylab.ylabel('Delta M')
    linex = [0, Bcr, Bcr]
    liney = [old_div(DM[0], 2.), old_div(DM[0], 2.), 0]
    pylab.plot(linex, liney, 'r')
    pylab.title(s)
#


def plotDDM(fignum, Bdm, DdeltaM, s):
    """
    function to plot d (Delta M)/dB  curves
    """
    pylab.figure(num=fignum)
    pylab.clf()
    if not isServer:
        pylab.figtext(.02, .01, version_num)
    start = len(Bdm) - len(DdeltaM)
    pylab.plot(Bdm[start:], DdeltaM, 'b')
    pylab.xlabel('B (T)')
    pylab.ylabel('d (Delta M)/dB')
    pylab.title(s)
#


def plotIMAG(fignum, Bimag, Mimag, s):
    """
    function to plot d (Delta M)/dB  curves
    """
    pylab.figure(num=fignum)
    pylab.clf()
    if not isServer:
        pylab.figtext(.02, .01, version_num)
    pylab.plot(Bimag, Mimag, 'r')
    pylab.xlabel('B (T)')
    pylab.ylabel('M/Ms')
    pylab.axvline(0, color='k')
    pylab.title(s)
#


def plotHDD(HDD, B, M, s):
    """
    function to make hysteresis, deltaM and DdeltaM plots
    """
    hpars, deltaM, Bdm = plotHYS(
        HDD['hyst'], B, M, s)  # Moff is the "fixed" loop data
    DdeltaM = []
    Mhalf = ""
    for k in range(2, len(Bdm)):
        # differnential
        DdeltaM.append(
            old_div(abs(deltaM[k] - deltaM[k - 2]), (Bdm[k] - Bdm[k - 2])))
    for k in range(len(deltaM)):
        if old_div(deltaM[k], deltaM[0]) < 0.5:
            Mhalf = k
            break
    try:
        Bhf = Bdm[Mhalf - 1:Mhalf + 1]
        Mhf = deltaM[Mhalf - 1:Mhalf + 1]
        # best fit line through two bounding points
        poly = pylab.polyfit(Bhf, Mhf, 1)
        Bcr = old_div((.5 * deltaM[0] - poly[1]), poly[0])
        hpars['hysteresis_bcr'] = '%8.3e' % (Bcr)
        hpars['magic_method_codes'] = "LP-BCR-HDM"
        if HDD['deltaM'] != 0:
            plotDM(HDD['deltaM'], Bdm, deltaM, Bcr, s)
            pylab.axhline(0, color='k')
            pylab.axvline(0, color='k')
            plotDDM(HDD['DdeltaM'], Bdm, DdeltaM, s)
    except:
        hpars['hysteresis_bcr'] = '0'
        hpars['magic_method_codes'] = ""
    return hpars
#


def plotDay(fignum, BcrBc, S, sym, **kwargs):
    """
    function to plot Day plots
    """
    pylab.figure(num=fignum)
    pylab.plot(BcrBc, S, sym)
    pylab.axhline(0, color='k')
    pylab.axhline(.05, color='k')
    pylab.axhline(.5, color='k')
    pylab.axvline(1, color='k')
    pylab.axvline(4, color='k')
    pylab.xlabel('Bcr/Bc')
    pylab.ylabel('Mr/Ms')
    pylab.title('Day Plot')
    pylab.xlim(0, 6)
    #bounds= pylab.axis()
    #pylab.axis([0, bounds[1],0, 1])
    mu_o = 4. * numpy.pi * 1e-7
    Bc_sd = 46e-3  # (MV1H) dunlop and carter-stiglitz 2006 (in T)
    Bc_md = 5.56e-3  # (041183) dunlop and carter-stiglitz 2006 (in T)
    chi_sd = 5.20e6 * mu_o  # now in T
    chi_md = 4.14e6 * mu_o  # now in T
    chi_r_sd = 4.55e6 * mu_o  # now in T
    chi_r_md = 0.88e6 * mu_o  # now in T
    Bcr_sd, Bcr_md = 52.5e-3, 26.1e-3  # (MV1H and 041183 in DC06 in tesla)
    Ms = 480e3  # A/m
    p = .1  # from Dunlop 2002
    N = old_div(1., 3.)  # demagnetizing factor
    f_sd = numpy.arange(1., 0., -.01)  # fraction of sd
    f_md = 1. - f_sd  # fraction of md
    f_sp = 1. - f_sd  # fraction of sp
    # Mr/Ms ratios for USD,MD and Jax shaped
    sdrat, mdrat, cbrat = 0.498, 0.048, 0.6
    Mrat = f_sd * sdrat + f_md * mdrat  # linear mixing - eq. 9 in Dunlop 2002
    Bc = old_div((f_sd * chi_sd * Bc_sd + f_md * chi_md * Bc_md),
                 (f_sd * chi_sd + f_md * chi_md))  # eq. 10 in Dunlop 2002
    Bcr = old_div((f_sd * chi_r_sd * Bcr_sd + f_md * chi_r_md * Bcr_md),
                  (f_sd * chi_r_sd + f_md * chi_r_md))  # eq. 11 in Dunlop 2002
    chi_sps = numpy.arange(1, 5) * chi_sd
    pylab.plot(old_div(Bcr, Bc), Mrat, 'r-')
    if 'names' in list(kwargs.keys()):
        names = kwargs['names']
        for k in range(len(names)):
            pylab.text(BcrBc[k], S[k], names[k])  # ,'ha'='left'


#
def plotSBc(fignum, Bc, S, sym):
    """
    function to plot Squareness,Coercivity
    """
    pylab.figure(num=fignum)
    pylab.plot(Bc, S, sym)
    pylab.xlabel('Bc')
    pylab.ylabel('Mr/Ms')
    pylab.title('Squareness-Coercivity Plot')
    bounds = pylab.axis()
    pylab.axis([0, bounds[1], 0, 1])
#


def plotSBcr(fignum, Bcr, S, sym):
    """
    function to plot Squareness,Coercivity of remanence
    """
    pylab.figure(num=fignum)
    pylab.plot(Bcr, S, sym)
    pylab.xlabel('Bcr')
    pylab.ylabel('Mr/Ms')
    pylab.title('Squareness-Bcr Plot')
    bounds = pylab.axis()
    pylab.axis([0, bounds[1], 0, 1])
#


def plotBcr(fignum, Bcr1, Bcr2):
    """
    function to plot two estimates of Bcr against each other
    """
    pylab.figure(num=fignum)
    pylab.plot(Bcr1, Bcr2, 'ro')
    pylab.xlabel('Bcr1')
    pylab.ylabel('Bcr2')
    pylab.title('Compare coercivity of remanence')


def plotHPARS(HDD, hpars, sym):
    """
    function to plot hysteresis parameters
    """
    pylab.figure(num=HDD['hyst'])
    X, Y = [], []
    X.append(0)
    Y.append(old_div(float(hpars['hysteresis_mr_moment']), float(
        hpars['hysteresis_ms_moment'])))
    X.append(float(hpars['hysteresis_bc']))
    Y.append(0)
    pylab.plot(X, Y, sym)
    bounds = pylab.axis()
    n4 = 'Ms: ' + '%8.2e' % (float(hpars['hysteresis_ms_moment'])) + ' Am^2'
    pylab.text(bounds[1] - .9 * bounds[1], -.9, n4)
    n1 = 'Mr: ' + '%8.2e' % (float(hpars['hysteresis_mr_moment'])) + ' Am^2'
    pylab.text(bounds[1] - .9 * bounds[1], -.7, n1)
    n2 = 'Bc: ' + '%8.2e' % (float(hpars['hysteresis_bc'])) + ' T'
    pylab.text(bounds[1] - .9 * bounds[1], -.5, n2)
    if 'hysteresis_xhf' in list(hpars.keys()):
        n3 = r'Xhf: ' + '%8.2e' % (float(hpars['hysteresis_xhf'])) + ' m^3'
        pylab.text(bounds[1] - .9 * bounds[1], -.3, n3)
    pylab.figure(num=HDD['deltaM'])
    X, Y, Bcr = [], [], ""
    if 'hysteresis_bcr' in list(hpars.keys()):
        X.append(float(hpars['hysteresis_bcr']))
        Y.append(0)
        Bcr = float(hpars['hysteresis_bcr'])
    pylab.plot(X, Y, sym)
    bounds = pylab.axis()
    if Bcr != "":
        n1 = 'Bcr: ' + '%8.2e' % (Bcr) + ' T'
        pylab.text(bounds[1] - .5 * bounds[1], .9 * bounds[3], n1)
#


def plotIRM(fignum, B, M, title):
    """ function to plot IRM backfield curves
    """
    rpars = {}
    Mnorm = []
    backfield = 0
    X, Y = [], []
    for k in range(len(B)):
        if M[k] < 0:
            break
    if k <= 5:
        kmin = 0
    else:
        kmin = k - 5
    for k in range(kmin, k + 1):
        X.append(B[k])
        if B[k] < 0:
            backfield = 1
        Y.append(M[k])
    if backfield == 1:
        poly = pylab.polyfit(X, Y, 1)
        if poly[0] != 0:
            bcr = (old_div(-poly[1], poly[0]))
        else:
            bcr = 0
        rpars['remanence_mr_moment'] = '%8.3e' % (M[0])
        rpars['remanence_bcr'] = '%8.3e' % (-bcr)
        rpars['magic_method_codes'] = 'LP-BCR-BF'
        if M[0] != 0:
            for m in M:
                Mnorm.append(old_div(m, M[0]))  # normalize to unity Msat
            title = title + ':' + '%8.3e' % (M[0])
    else:
        if M[-1] != 0:
            for m in M:
                Mnorm.append(old_div(m, M[-1]))  # normalize to unity Msat
            title = title + ':' + '%8.3e' % (M[-1])
# do plots if desired
    if fignum != 0 and M[0] != 0:  # skip plot for fignum = 0
        pylab.figure(num=fignum)
        pylab.clf()
        if not isServer:
            pylab.figtext(.02, .01, version_num)
        pylab.plot(B, Mnorm)
        pylab.axhline(0, color='k')
        pylab.axvline(0, color='k')
        pylab.xlabel('B (T)')
        pylab.ylabel('M/Mr')
        pylab.title(title)
        if backfield == 1:
            pylab.scatter([bcr], [0], marker='s', c='b')
            bounds = pylab.axis()
            n1 = 'Bcr: ' + '%8.2e' % (-bcr) + ' T'
            pylab.figtext(.2, .5, n1)
            n2 = 'Mr: ' + '%8.2e' % (M[0]) + ' Am^2'
            pylab.figtext(.2, .45, n2)
    elif fignum != 0:
        pylab.figure(num=fignum)
        # pylab.clf()
        if not isServer:
            pylab.figtext(.02, .01, version_num)
        print('M[0]=0,  skipping specimen')
    return rpars


def plotXTF(fignum, XTF, Fs, e, b):
    """ function to plot series of chi measurements as a function of temperature, holding field constant and varying frequency
    """
    pylab.figure(num=fignum)
    pylab.xlabel('Temperature (K)')
    pylab.ylabel('Susceptibility (m^3/kg)')
    k = 0
    Flab = []
    for freq in XTF:
        T, X = [], []
        for xt in freq:
            X.append(xt[0])
            T.append(xt[1])
        pylab.plot(T, X)
        pylab.text(T[-1], X[-1], str(int(Fs[k])) + ' Hz')
#        Flab.append(str(int(Fs[k]))+' Hz')
        k += 1
    pylab.title(e + ': B = ' + '%8.1e' % (b) + ' T')
#    pylab.legend(Flab,'upper left')
#


def plotXTB(fignum, XTB, Bs, e, f):
    """ function to plot series of chi measurements as a function of temperature, holding frequency constant and varying B
    """
    pylab.figure(num=fignum)
    pylab.xlabel('Temperature (K)')
    pylab.ylabel('Susceptibility (m^3/kg)')
    k = 0
    Blab = []
    for field in XTB:
        T, X = [], []
        for xt in field:
            X.append(xt[0])
            T.append(xt[1])
        pylab.plot(T, X)
        pylab.text(T[-1], X[-1], '%8.2e' % (Bs[k]) + ' T')
#        Blab.append('%8.1e'%(Bs[k])+' T')
        k += 1
    pylab.title(e + ': f = ' + '%i' % (int(f)) + ' Hz')
#    pylab.legend(Blab,'upper left')
#


def plotXFT(fignum, XF, T, e, b):
    """ function to plot series of chi measurements as a function of temperature, holding field constant and varying frequency
    """
    pylab.figure(num=fignum)
    pylab.clf()
    if not isServer:
        pylab.figtext(.02, .01, version_num)
    pylab.xlabel('Frequency (Hz)')
    pylab.ylabel('Susceptibility (m^3/kg)')
    k = 0
    F, X = [], []
    for xf in XF:
        X.append(xf[0])
        F.append(xf[1])
    pylab.plot(F, X)
    pylab.semilogx()
    pylab.title(e + ': B = ' + '%8.1e' % (b) + ' T')

    pylab.legend(['%i' % (int(T)) + ' K'])
#


def plotXBT(fignum, XB, T, e, b):
    """ function to plot series of chi measurements as a function of temperature, holding field constant and varying frequency
    """
    pylab.figure(num=fignum)
    pylab.clf()
    if not isServer:
        pylab.figtext(.02, .01, version_num)
    pylab.xlabel('Field (T)')
    pylab.ylabel('Susceptibility (m^3/kg)')
    k = 0
    B, X = [], []
    for xb in XB:
        X.append(xb[0])
        B.append(xb[1])
    pylab.plot(B, X)
    pylab.legend(['%i' % (int(T)) + ' K'])
    pylab.title(e + ': f = ' + '%i' % (int(f)) + ' Hz')
#


def plotzfcfc(MT, e):
    """
    function to plot zero-field cooled, field cooled data
    """
    ZFCM, ZFCT, FCM, FCT, init = MT[0], MT[1], MT[2], MT[3], 0
    leglist = []
    if len(ZFCM) > 2:
        if init == 0:
            plot_init(1, 5, 5)
        pylab.plot(ZFCT, ZFCM, 'b')
        leglist.append('ZFC')
        init = 1
    if len(FCM) > 2:
        if init == 0:
            plot_init(1, 5, 5)
        pylab.plot(FCT, FCM, 'r')
        leglist.append('FC')
    if init != 0:
        pylab.legend(leglist)
        pylab.xlabel('Temperature (K)')
        pylab.ylabel('Magnetization (Am^2/kg)')
        if len(ZFCM) > 2:
            pylab.plot(ZFCT, ZFCM, 'bo')
        if len(FCM) > 2:
            pylab.plot(FCT, FCM, 'ro')
        pylab.title(e)
#


def plotltc(LTC_CM, LTC_CT, LTC_WM, LTC_WT, e):
    """
    function to plot low temperature cycling experiments
    """
    leglist, init = [], 0
    if len(LTC_CM) > 2:
        if init == 0:
            plot_init(1, 5, 5)
        pylab.plot(LTC_CT, LTC_CM, 'b')
        leglist.append('RT SIRM, measured while cooling')
        init = 1
    if len(LTC_WM) > 2:
        if init == 0:
            plot_init(1, 5, 5)
        pylab.plot(LTC_WT, LTC_WM, 'r')
        leglist.append('RT SIRM, measured while warming')
    if init != 0:
        pylab.legend(leglist, 'lower left')
        pylab.xlabel('Temperature (K)')
        pylab.ylabel('Magnetization (Am^2/kg)')
        if len(LTC_CM) > 2:
            pylab.plot(LTC_CT, LTC_CM, 'bo')
        if len(LTC_WM) > 2:
            pylab.plot(LTC_WT, LTC_WM, 'ro')
        pylab.title(e)


def plot_close(plot):
    # pylab.ion()
    pylab.close(plot)
    # pylab.ioff()

#


def plotANIS(ANIS, Ss, iboot, ihext, ivec, ipar, title, plt, comp, vec, Dir, nb):
    imeas, bpars, hpars = 1, [], []
    npts = len(Ss)  # number of data points
    plots = {}
#
# plot eigenvectors:
#
    Vs = []
    for s in Ss:
        tau, V = pmag.doseigs(s)
        Vs.append(V)
    nf, sigma, avs = pmag.sbar(Ss)
    if plt == 1:
        for key in list(ANIS.keys()):
            pylab.figure(num=ANIS[key])
            pylab.clf()
            if not isServer:
                pylab.figtext(.02, .01, version_num)
        plotNET(ANIS['data'])  # draw the net
        plotEVEC(ANIS['data'], Vs, 40, title)  # put on the data eigenvectors
#
# plot mean eigenvectors
#
    Vs = []
    mtau, mV = pmag.doseigs(avs)
    Vs.append(mV)
    hpars = pmag.dohext(nf, sigma, avs)
    if plt == 1:
        title = ''
        if ihext == 1:
            title = title + "Hext"
        if iboot == 1:
            title = title + ":Bootstrap"
        if ipar == 1:
            title = title + ":Parametric"
        if title[0] == ":":
            title = title[1:]
        plotNET(ANIS['conf'])  # draw the net
        plotEVEC(ANIS['conf'], Vs, 36, title)  # put on the mean eigenvectors
#
# plot mean confidence
#
    if iboot == 1:
        print('Doing bootstrap - be patient')
        Tmean, Vmean, Taus, BVs = pmag.s_boot(
            Ss, ipar, nb)  # get eigenvectors of mean tensor
        bpars = pmag.sbootpars(Taus, BVs)
        bpars['t1'] = hpars['t1']
        bpars['t2'] = hpars['t2']
        bpars['t3'] = hpars['t3']
        if plt == 1:
            if ivec == 1:
                # put on the data eigenvectors
                plotEVEC(ANIS['conf'], BVs, 5, '')
            else:
                ellpars = [bpars["v1_dec"], bpars["v1_inc"], bpars["v1_zeta"], bpars["v1_zeta_dec"],
                           bpars["v1_zeta_inc"], bpars["v1_eta"], bpars["v1_eta_dec"], bpars["v1_eta_inc"]]
                plotELL(ANIS['conf'], ellpars, 'r-,', 1, 1)
                ellpars = [bpars["v2_dec"], bpars["v2_inc"], bpars["v2_zeta"], bpars["v2_zeta_dec"],
                           bpars["v2_zeta_inc"], bpars["v2_eta"], bpars["v2_eta_dec"], bpars["v2_eta_inc"]]
                plotELL(ANIS['conf'], ellpars, 'b-,', 1, 1)
                ellpars = [bpars["v3_dec"], bpars["v3_inc"], bpars["v3_zeta"], bpars["v3_zeta_dec"],
                           bpars["v3_zeta_inc"], bpars["v3_eta"], bpars["v3_eta_dec"], bpars["v3_eta_inc"]]
                plotELL(ANIS['conf'], ellpars, 'k-,', 1, 1)
            pylab.figure(num=ANIS['tcdf'])
            pylab.clf()
            if not isServer:
                pylab.figtext(.02, .01, version_num)
            ts = []
            for t in Taus:
                ts.append(t[0])
            plotCDF(ANIS['tcdf'], ts, "", 'r', "")
            ts.sort()
            tminind = int(0.025 * len(ts))
            tmaxind = int(0.975 * len(ts))
            tbounds = []
            tbounds.append(ts[tminind])
            tbounds.append(ts[tmaxind])
            pylab.axvline(x=tbounds[0], linewidth=1, color='r', linestyle='--')
            pylab.axvline(x=tbounds[1], linewidth=1, color='r', linestyle='--')
            # plotVs(ANIS['tcdf'],tbounds,'r','-') # there is some bug in here
            # - can't figure it out
            ts = []
            for t in Taus:
                ts.append(t[1])
            plotCDF(ANIS['tcdf'], ts, "", 'b', "")
            ts.sort()
            tminind = int(0.025 * len(ts))
            tmaxind = int(0.975 * len(ts))
            tbounds = []
            tbounds.append(ts[tminind])
            tbounds.append(ts[tmaxind])
            # plotVs(ANIS['tcdf'],tbounds,'b','-')
            pylab.axvline(x=tbounds[0], linewidth=1, color='b', linestyle='-.')
            pylab.axvline(x=tbounds[1], linewidth=1, color='b', linestyle='-.')
            ts = []
            for t in Taus:
                ts.append(t[2])
            plotCDF(ANIS['tcdf'], ts, "Eigenvalues", 'k', "")
            ts.sort()
            tminind = int(0.025 * len(ts))
            tmaxind = int(0.975 * len(ts))
            tbounds = []
            tbounds.append(ts[tminind])
            tbounds.append(ts[tmaxind])
            plotVs(ANIS['tcdf'], tbounds, 'k', '-')
            pylab.axvline(x=tbounds[0], linewidth=1, color='k', linestyle='-')
            pylab.axvline(x=tbounds[1], linewidth=1, color='k', linestyle='-')
            if comp == 1:  # do eigenvector of choice
                pylab.figure(num=ANIS['conf'])
                XY = pmag.dimap(Dir[0], Dir[1])
                pylab.scatter([XY[0]], [XY[1]], marker='p', c='m', s=100)
                Ccart = pmag.dir2cart(Dir)
                Vxs, Vys, Vzs = [], [], []
                for v in BVs:
                    cart = pmag.dir2cart([v[vec][0], v[vec][1], 1.])
                    Vxs.append(cart[0])
                    Vys.append(cart[1])
                    Vzs.append(cart[2])
                pylab.figure(num=ANIS['vxcdf'])
                pylab.clf()
                if not isServer:
                    pylab.figtext(.02, .01, version_num)
                plotCDF(ANIS['vxcdf'], Vxs, "V_" + str(vec + 1) + "1", 'r', "")
                Vxs.sort()
                vminind = int(0.025 * len(Vxs))
                vmaxind = int(0.975 * len(Vxs))
                vbounds = []
                vbounds.append(Vxs[vminind])
                vbounds.append(Vxs[vmaxind])
                pylab.axvline(x=vbounds[0], linewidth=1,
                              color='r', linestyle='--')
                pylab.axvline(x=vbounds[1], linewidth=1,
                              color='r', linestyle='--')
                # plotVs(ANIS['vxcdf'],vbounds,'r','--')
                # plotVs(ANIS['vxcdf'],[Ccart[0]],'r','-')
                pylab.axvline(x=Ccart[0][0], linewidth=1,
                              color='r', linestyle='-')
                plotCDF(ANIS['vycdf'], Vys, "V_" + str(vec + 1) + "2", 'b', "")
                Vys.sort()
                vminind = int(0.025 * len(Vys))
                vmaxind = int(0.975 * len(Vys))
                vbounds = []
                vbounds.append(Vys[vminind])
                vbounds.append(Vys[vmaxind])
                pylab.axvline(x=vbounds[0], linewidth=1,
                              color='b', linestyle='--')
                pylab.axvline(x=vbounds[1], linewidth=1,
                              color='b', linestyle='--')
                pylab.axvline(x=Ccart[0][1], linewidth=1,
                              color='b', linestyle='-')
                # plotVs(ANIS['vycdf'],vbounds,'b','--')
                # plotVs(ANIS['vycdf'],[Ccart[1]],'b','-')
                plotCDF(ANIS['vzcdf'], Vzs, "V_" + str(vec + 1) + "3", 'k', "")
                Vzs.sort()
                vminind = int(0.025 * len(Vzs))
                vmaxind = int(0.975 * len(Vzs))
                vbounds = []
                vbounds.append(Vzs[vminind])
                vbounds.append(Vzs[vmaxind])
                pylab.axvline(x=vbounds[0], linewidth=1,
                              color='k', linestyle='--')
                pylab.axvline(x=vbounds[1], linewidth=1,
                              color='k', linestyle='--')
                pylab.axvline(x=Ccart[0][2], linewidth=1,
                              color='k', linestyle='-')
                # plotVs(ANIS['vzcdf'],vbounds,'k','--')
                # plotVs(ANIS['vzcdf'],[Ccart[2]],'k','-')
        bpars['v1_dec'] = hpars['v1_dec']
        bpars['v2_dec'] = hpars['v2_dec']
        bpars['v3_dec'] = hpars['v3_dec']
        bpars['v1_inc'] = hpars['v1_inc']
        bpars['v2_inc'] = hpars['v2_inc']
        bpars['v3_inc'] = hpars['v3_inc']
    if ihext == 1 and plt == 1:
        ellpars = [hpars["v1_dec"], hpars["v1_inc"], hpars["e12"], hpars["v2_dec"],
                   hpars["v2_inc"], hpars["e13"], hpars["v3_dec"], hpars["v3_inc"]]
        plotELL(ANIS['conf'], ellpars, 'r-,', 1, 1)
        ellpars = [hpars["v2_dec"], hpars["v2_inc"], hpars["e23"], hpars["v3_dec"],
                   hpars["v3_inc"], hpars["e12"], hpars["v1_dec"], hpars["v1_inc"]]
        plotELL(ANIS['conf'], ellpars, 'b-,', 1, 1)
        ellpars = [hpars["v3_dec"], hpars["v3_inc"], hpars["e13"], hpars["v1_dec"],
                   hpars["v1_inc"], hpars["e23"], hpars["v2_dec"], hpars["v2_inc"]]
        plotELL(ANIS['conf'], ellpars, 'k-,', 1, 1)
    return bpars, hpars
####


def plotPIE(fig, fracs, labels, title):
    explode = []
    for obj in labels:
        explode.append(.05)
    pylab.figure(num=fig)
    pylab.pie(fracs, labels=labels, colors=(
        'r', 'y', 'b', 'g', 'm', 'c', 'w'), explode=explode)
    pylab.title(title)
#


def plotTRM(fig, B, TRM, Bp, Mp, NLpars, title):
    #
    # plots TRM acquisition data and correction to B_estimated to B_ancient
    pylab.figure(num=fig)
    pylab.clf()
    if not isServer:
        pylab.figtext(.02, .01, version_num)
    pylab.xlabel('B (uT)')
    pylab.ylabel('Fractional TRM ')
    pylab.title(title + ':TRM=' + '%8.2e' % (Mp[-1]))
#
# scale data
    Bnorm, Bpnorm = [], []
    Tnorm, Mnorm = [], []
    for b in B:
        Bnorm.append(b * 1e6)
    for b in Bp:
        Bpnorm.append(b * 1e6)
    for t in TRM:
        Tnorm.append(old_div(t, Mp[-1]))
    for t in Mp:
        Mnorm.append(old_div(t, Mp[-1]))
    pylab.plot(Bnorm, Tnorm, 'go')
    pylab.plot(Bpnorm, Mnorm, 'g-')
    if NLpars['banc'] > 0:
        pylab.plot([0, NLpars['best'] * 1e6],
                   [0, old_div(NLpars['banc_npred'], Mp[-1])], 'b--')
        pylab.plot([NLpars['best'] * 1e6, NLpars['banc'] * 1e6], [old_div(
            NLpars['banc_npred'], Mp[-1]), old_div(NLpars['banc_npred'], Mp[-1])], 'r--')
        pylab.plot([NLpars['best'] * 1e6],
                   [old_div(NLpars['banc_npred'], Mp[-1])], 'bd')
        pylab.plot([NLpars['banc'] * 1e6],
                   [old_div(NLpars['banc_npred'], Mp[-1])], 'rs')
    else:
        pylab.plot([0, NLpars['best'] * 1e6],
                   [0, old_div(NLpars['best_npred'], Mp[-1])], 'b--')
        pylab.plot([0, NLpars['best'] * 1e6],
                   [0, old_div(NLpars['best_npred'], Mp[-1])], 'bd')

###


def plotTDS(fig, tdsblock, title):
    pylab.figure(num=fig)
    pylab.clf()
    if not isServer:
        pylab.figtext(.02, .01, version_num)
    pylab.xlabel('Fraction TRM remaining')
    pylab.ylabel('Fraction NRM remaining')
    pylab.title(title)
    X, Y = [], []
    for rec in tdsblock:
        X.append(rec[2])  # TRM on X
        Y.append(rec[1])  # NRM on Y
        pylab.text(X[-1], Y[-1], ' %3.1f' % (float(rec[0]) - 273))
    pylab.plot(X, Y, 'ro')
    pylab.plot(X, Y)


def plotCONF(fignum, s, datablock, pars, new):
    """
    plots directions and confidence ellipses
    """
# make the stereonet
    if new == 1:
        plotNET(fignum)
#
#   plot the data
#
    DIblock = []
    for plotrec in datablock:
        DIblock.append((float(plotrec["dec"]), float(plotrec["inc"])))
    if len(DIblock) > 0:
        plotDI(fignum, DIblock)  # plot directed lines
#
# put on the mean direction
#
    x, y = [], []
    XY = pmag.dimap(float(pars[0]), float(pars[1]))
    x.append(XY[0])
    y.append(XY[1])
    pylab.figure(num=fignum)
    if new == 1:
        pylab.scatter(x, y, marker='d', s=80, c='r')
    else:
        if float(pars[1] > 0):
            pylab.scatter(x, y, marker='^', s=100, c='r')
        else:
            pylab.scatter(x, y, marker='^', s=100, c='y')
    pylab.title(s)
#
# plot the ellipse
#
    plotELL(fignum, pars, 'r-,', 0, 1)


EI_plot_num = 0
maxE, minE, maxI, minI = 0, 10, 0, 90


def plotEI(fignum, E, I, f):
    global EI_plot_num, maxE, minE, minI, maxI
    pylab.figure(num=fignum)
    if EI_plot_num == 0:
        pylab.plot(I, E, 'r')
        pylab.xlabel("Inclination")
        pylab.ylabel("Elongation")
        EI_plot_num += 1
        pylab.text(I[-1], E[-1], ' %3.1f' % (f))
        pylab.text(I[0] - 2, E[0], ' %s' % ('f=1'))
    elif f == 1:
        pylab.plot(I, E, 'g-')
    else:
        pylab.plot(I, E, 'y')


def plotV2s(fignum, V2s, I, f):
    pylab.figure(num=fignum)
    pylab.plot(I, V2s, 'r')
    pylab.xlabel("Inclination")
    pylab.ylabel("Elongation direction")


def plotX(fignum, x, y, xmin, xmax, ymin, ymax, sym):
    pylab.figure(num=fignum)
    X, Y = [x, x], [ymin, ymax]
    pylab.plot(X, Y, sym)
    X, Y = [xmin, xmax], [y, y]
    pylab.plot(X, Y, sym)
    pylab.axis([-5., 90., 0., 3.5])
#


def plotCOM(CDF, BDI1, BDI2, d):
    #
    #   convert to cartesian coordinates X1,X2, Y1,Y2 and Z1, Z2
    #
    cart = pmag.dir2cart(BDI1).transpose()
    X1, Y1, Z1 = cart[0], cart[1], cart[2]
    min = int(0.025 * len(X1))
    max = int(0.975 * len(X1))
    X1, y = plotCDF(CDF['X'], X1, "X component", 'r', "")
    bounds1 = [X1[min], X1[max]]
    plotVs(CDF['X'], bounds1, 'r', '-')
    Y1, y = plotCDF(CDF['Y'], Y1, "Y component", 'r', "")
    bounds1 = [Y1[min], Y1[max]]
    plotVs(CDF['Y'], bounds1, 'r', '-')
    Z1, y = plotCDF(CDF['Z'], Z1, "Z component", 'r', "")
    bounds1 = [Z1[min], Z1[max]]
    plotVs(CDF['Z'], bounds1, 'r', '-')
    # drawFIGS(CDF)
    if d[0] == "":  # repeat for second data set
        bounds2 = []
        cart = pmag.dir2cart(BDI2).transpose()
        X2, Y2, Z2 = cart[0], cart[1], cart[2]
        X2, y = plotCDF(CDF['X'], X2, "X component", 'b', "")
        bounds2 = [X2[min], X2[max]]
        plotVs(CDF['X'], bounds2, 'b', '--')
        Y2, y = plotCDF(CDF['Y'], Y2, "Y component", 'b', "")
        bounds2 = [Y2[min], Y2[max]]
        plotVs(CDF['Y'], bounds2, 'b', '--')
        Z2, y = plotCDF(CDF['Z'], Z2, "Z component", 'b', "")
        bounds2 = [Z2[min], Z2[max]]
        plotVs(CDF['Z'], bounds2, 'b', '--')
    else:
        cart = pmag.dir2cart([d[0], d[1], 1.0])
        plotVs(CDF['X'], [cart[0]], 'k', '--')
        plotVs(CDF['Y'], [cart[1]], 'k', '--')
        plotVs(CDF['Z'], [cart[2]], 'k', '--')
    return

# functions for images - requires additional modules
#
#import Image,os
# def combineFigs(Name,filenames,Ncols):
#    Nfigs=len(filenames.keys())
#    Nrows=Nfigs/Ncols+Nfigs%Ncols
#    print Nrows,Ncols
#    S=500 # fig size
#    size=(S,S)
#    image=Image.new('RGBA',(Ncols*S,Nrows*S))
#    Nrow,row,col,pic=1,1,1,0
#    for key in filenames.keys():
#        pic+=1
#        print  filenames[key]
#        im=Image.open(filenames[key])
#        im.thumbnail(size)
#        image.paste(im,(col,row))
#        print col,row
#        col+=S
#        if pic ==Ncols:
#            col=1
#            Nrow+=1
#            row=Nrow*size
#    image.save(Name+'.png')
#    for key in filenames.keys():
#        os.remove(filenames[key])


def addBorders(Figs, titles, border_color, text_color):

    import datetime
    now = datetime.datetime.now()

    for key in list(Figs.keys()):

        fig = pylab.figure(Figs[key])
        plot_title = titles[key]
        fig.set_figheight(5.5)
        (x, y, w, h) = fig.gca().get_position()
        fig.gca().set_position([x, 1.3 * y, w, old_div(h, 1.1)])

        # add an axis covering the entire figure
        border_ax = fig.add_axes([0, 0, 1, 1])
        border_ax.set_frame_on(False)
        border_ax.set_xticks([])
        border_ax.set_yticks([])

        # add a border
        border_ax.text(-0.02, 1, "|                                                                                                                                                                                         |",
                       horizontalalignment='left',
                       verticalalignment='top',
                       color=text_color,
                       bbox=dict(edgecolor=border_color,
                                 facecolor='#FFFFFF', linewidth=0.25),
                       size=30)
        border_ax.text(-0.02, 0, "|                                                                                                                                                                                         |",
                       horizontalalignment='left',
                       verticalalignment='bottom',
                       color=text_color,
                       bbox=dict(edgecolor=border_color,
                                 facecolor='#FFFFFF', linewidth=0.25),
                       size=18)

        # add text
        border_ax.text((old_div(4, fig.get_figwidth())) * 0.015, 0.03, now.strftime("%d %B %Y, %I:%M:%S %p"),
                       horizontalalignment='left',
                       verticalalignment='top',
                       color=text_color,
                       size=10)
        border_ax.text(0.5, 0.98, plot_title,
                       horizontalalignment='center',
                       verticalalignment='top',
                       color=text_color,
                       size=20)
        border_ax.text(1 - (old_div(4, fig.get_figwidth())) * 0.015, 0.03, 'http://earthref.org/MAGIC',
                       horizontalalignment='right',
                       verticalalignment='top',
                       color=text_color,
                       size=10)
    return Figs


def plotMAP(fignum, lats, lons, Opts):
    """ makes a basemap with lats/lons """
    from mpl_toolkits.basemap import Basemap
    fig = pylab.figure(num=fignum)
    rgba_land = (255, 255, 150, 255)
    rgba_ocean = (200, 250, 255, 255)
    ExMer = ['sinus', 'moll', 'lcc']
    # draw meridian labels on the bottom [left,right,top,bottom]
    mlabels = [0, 0, 0, 1]
    plabels = [1, 0, 0, 0]  # draw parallel labels on the left
    if Opts['proj'] in ExMer:
        mlabels = [0, 0, 0, 0]
    if Opts['proj'] not in ExMer:
        m = Basemap(projection=Opts['proj'], lat_0=Opts['lat_0'],
                    lon_0=Opts['lon_0'], resolution=Opts['res'])
        plabels = [0, 0, 0, 0]
    else:
        m = Basemap(llcrnrlon=Opts['lonmin'], llcrnrlat=Opts['latmin'], urcrnrlat=Opts['latmax'], urcrnrlon=Opts['lonmax'],
                    projection=Opts['proj'], lat_0=Opts['lat_0'], lon_0=Opts['lon_0'], lat_ts=0., resolution=Opts['res'], boundinglat=Opts['boundinglat'])
    if 'details' in list(Opts.keys()):
        if Opts['details']['fancy'] == 1:
            from pylab import meshgrid
            from mpl_toolkits.basemap import basemap_datadir
            EDIR = basemap_datadir + "/"
            etopo = numpy.loadtxt(EDIR + 'etopo20data.gz')
            elons = numpy.loadtxt(EDIR + 'etopo20lons.gz')
            elats = numpy.loadtxt(EDIR + 'etopo20lats.gz')
            x, y = m(*meshgrid(elons, elats))
            cs = m.contourf(x, y, etopo, 30)
        if Opts['details']['coasts'] == 1:
            m.drawcoastlines(color='k')
        if Opts['details']['rivers'] == 1:
            m.drawrivers(color='b')
        if Opts['details']['states'] == 1:
            m.drawstates(color='r')
        if Opts['details']['countries'] == 1:
            m.drawcountries(color='g')
        if Opts['details']['ocean'] == 1:
            try:
                m.drawlsmask(land_color=rgba_land,
                             ocean_color=rgba_ocean, lsmask_lats=None)
            except TypeError:
                # this is caused by basemap function: _readlsmask
                # interacting with numpy
                # (a float is provided, numpy wants an int).
                # hopefully will be fixed eventually.
                pass
    if Opts['pltgrid'] == 0.:
        circles = numpy.arange(Opts['latmin'], Opts['latmax'] + 15., 15.)
        meridians = numpy.arange(Opts['lonmin'], Opts['lonmax'] + 30., 30.)
    elif Opts['pltgrid'] > 0:
        if Opts['proj'] in ExMer or Opts['proj'] == 'lcc':
            circles = numpy.arange(-90, 180. +
                                   Opts['gridspace'], Opts['gridspace'])
            meridians = numpy.arange(0, 360., Opts['gridspace'])
        else:
            g = Opts['gridspace']
            latmin, lonmin = g * \
                int(old_div(Opts['latmin'], g)), g * \
                int(old_div(Opts['lonmin'], g))
            latmax, lonmax = g * \
                int(old_div(Opts['latmax'], g)), g * \
                int(old_div(Opts['lonmax'], g))
            # circles=numpy.arange(latmin-2.*Opts['padlat'],latmax+2.*Opts['padlat'],Opts['gridspace'])
            # meridians=numpy.arange(lonmin-2.*Opts['padlon'],lonmax+2.*Opts['padlon'],Opts['gridspace'])
            meridians = numpy.arange(0, 360, 30)
            circles = numpy.arange(-90, 90, 30)
    if Opts['pltgrid'] >= 0:
        # m.drawparallels(circles,color='black',labels=plabels)
        # m.drawmeridians(meridians,color='black',labels=mlabels)
        # skip the labels - they are ugly
        m.drawparallels(circles, color='black')
        # skip the labels - they are ugly
        m.drawmeridians(meridians, color='black')
        m.drawmapboundary()
    prn_name, symsize = 0, 5
    if 'names' in list(Opts.keys()) > 0:
        names = Opts['names']
        if len(names) > 0:
            prn_name = 1
#
    X, Y, T, k = [], [], [], 0
    if 'symsize' in list(Opts.keys()):
        symsize = Opts['symsize']
    if Opts['sym'][-1] != '-':  # just plot points
        X, Y = m(lons, lats)
        if prn_name == 1:
            for pt in range(len(lats)):
                T.append(pylab.text(X[pt] + 5000, Y[pt] - 5000, names[pt]))
        m.plot(X, Y, Opts['sym'], markersize=symsize)
    else:  # for lines,  need to separate chunks using lat==100.
        chunk = 1
        while k < len(lats) - 1:
            if lats[k] <= 90:  # part of string
                x, y = m(lons[k], lats[k])
                if x < 1e20:
                    X.append(x)
                if y < 1e20:
                    Y.append(y)  # exclude off the map points
                if prn_name == 1:
                    T.append(pylab.text(x + 5000, y - 5000, names[k]))
                k += 1
            else:  # need to skip 100.0s and move to next chunk
                # plot previous chunk
                m.plot(X, Y, Opts['sym'], markersize=symsize)
                chunk += 1
                while lats[k] > 90. and k < len(lats) - 1:
                    k += 1  # skip bad points
                X, Y, T = [], [], []
        if len(X) > 0:
            m.plot(X, Y, Opts['sym'], markersize=symsize)  # plot last chunk


def plotEQcont(fignum, DIblock):
    import random
    pylab.figure(num=fignum)
    pylab.axis("off")
    XY = []
    centres = []
    counter = 0
    for rec in DIblock:
        counter = counter + 1
        X = pmag.dir2cart([rec[0], rec[1], 1.])
        # from Collinson 1983
        R = old_div(numpy.sqrt(1. - X[2]), (numpy.sqrt(X[0]**2 + X[1]**2)))
        XY.append([X[0] * R, X[1] * R])
    # radius of the circle
    radius = (old_div(3., (numpy.sqrt(numpy.pi * (9. + float(counter)))))) + 0.01
    num = 2. * (old_div(1., radius))  # number of circles
    # a,b are the extent of the grids over which the circles are equispaced
    a1, a2 = (0. - (radius * num / 2.)), (0. + (radius * num / 2.))
    b1, b2 = (0. - (radius * num / 2.)), (0. + (radius * num / 2.))
    # this is to get an array (a list of list wont do) of x,y values
    xlist = pylab.linspace(a1, a2, int(pylab.ceil(num)))
    ylist = pylab.linspace(b1, b2, int(pylab.ceil(num)))
    X, Y = pylab.meshgrid(xlist, ylist)
    # to put z in the array I just multiply both x,y with zero.  I will add to
    # the zero values later
    Z = X * Y * 0.
    # keeping the centres of the circles as a separate list instead of in
    # array helps later
    for j in range(len(ylist)):
        for i in range(len(xlist)):
            centres.append([xlist[i], ylist[j]])
    # the following lines are to figure out what happens at the edges where part of a circle might lie outside
    # a thousand random numbers are generated within the x,y limit of the circles and tested whether it is contained in
    # the eq area net space....their ratio gives the fraction of circle
    # contained in the net
    fraction = []
    beta, alpha = 0.001, 0.001  # to avoid those 'division by float' thingy
    for i in range(0, int(pylab.ceil(num))**2):
        if numpy.sqrt(((centres[i][0])**2) + ((centres[i][1])**2)) - 1. < radius:
            for j in range(1, 1000):
                rnd1 = random.uniform(
                    centres[i][0] - radius, centres[i][0] + radius)
                rnd2 = random.uniform(
                    centres[i][1] - radius, centres[i][1] + radius)
                if ((centres[i][0] - rnd1)**2 + (centres[i][1] - rnd2)**2) <= radius**2:
                    if (rnd1**2) + (rnd2**2) < 1.:
                        alpha = alpha + 1.
                        beta = beta + 1.
                    else:
                        alpha = alpha + 1.
            fraction.append(old_div(alpha, beta))
            alpha, beta = 0.001, 0.001
        else:
            fraction.append(1.)  # if the whole circle lies in the net

    # for every circle count the number of points lying in it
    count = 0
    dotspercircle = 0.
    for j in range(0, int(pylab.ceil(num))):
        for i in range(0, int(pylab.ceil(num))):
            for k in range(0, counter):
                if (XY[k][0] - centres[count][0])**2 + (XY[k][1] - centres[count][1])**2 <= radius**2:
                    dotspercircle += 1.
            Z[i][j] = Z[i][j] + (dotspercircle * fraction[count])
            count += 1
            dotspercircle = 0.
    im = pylab.imshow(Z, interpolation='bilinear', origin='lower',
                      cmap=pylab.cm.hot, extent=(-1., 1., -1., 1.))
    pylab.colorbar()
    x, y = [], []
    # Draws the border
    for i in range(0, 360):
        x.append(numpy.sin((old_div(numpy.pi, 180.)) * float(i)))
        y.append(numpy.cos((old_div(numpy.pi, 180.)) * float(i)))
    pylab.plot(x, y, 'w-')
    x, y = [], []
    # the map will be a square of 1X1..this is how I erase the redundant area
    for j in range(1, 4):
        for i in range(0, 360):
            x.append(numpy.sin((old_div(numpy.pi, 180.)) * float(i))
                     * (1. + (old_div(float(j), 10.))))
            y.append(numpy.cos((old_div(numpy.pi, 180.)) * float(i))
                     * (1. + (old_div(float(j), 10.))))
        pylab.plot(x, y, 'w-', linewidth=26)
        x, y = [], []
    # the axes
    pylab.axis("equal")

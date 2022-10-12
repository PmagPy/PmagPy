# /usr/bin/env pythonw

# pylint: skip-file
# pylint: disable-all
# causes too many errors and crashes

import os
import sys
import warnings

from past.utils import old_div
import numpy as np
import pandas as pd
warnings.filterwarnings("ignore")  # what you don't know won't hurt you
from distutils.version import LooseVersion

# no longer setting backend here
from pmag_env import set_env
isServer = set_env.isServer
verbose = set_env.verbose

from pmagpy import pmag
from pmagpy import find_pmag_dir
from pmagpy import contribution_builder as cb
has_cartopy, Cartopy = pmag.import_cartopy()
if has_cartopy:
    import cartopy.crs as ccrs
    from cartopy import config
    from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
    from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
    from cartopy import feature as cfeature
    from cartopy.feature import NaturalEarthFeature, LAND, COASTLINE, OCEAN, LAKES, BORDERS
has_basemap, Basemap = pmag.import_basemap()


import matplotlib
from matplotlib import cm as color_map
from matplotlib import pyplot as plt
from pylab import meshgrid  # matplotlib's meshgrid function
import matplotlib.ticker as mticker
globals = 0
graphmenu = 0
global version_num
version_num = pmag.get_version()

# if running on a server use Agg to avoid $DISPLAY not found errors
if isServer:
    matplotlib.pyplot.switch_backend('Agg')

if matplotlib.__version__ < '2.1':
    print("""-W- Please upgrade to matplotlib >= 2.1
    On the command line, for Anaconda users:
       conda upgrade matplotlib
    For those with an alternative Python distribution:
       pip install matplotlib --upgrade
""")


def show_fig(fig):
    plt.figure(fig)
    plt.show()


def draw_figs(FIGS):
    """
    Can only be used if matplotlib backend is set to TKAgg
    Does not play well with wxPython
    Parameters
    _________
    FIGS : dictionary of figure names as keys and numbers as values

    """
    is_win = True if sys.platform in ['win32', 'win64'] else False
    if not is_win:
        plt.ion()
        for fig in list(FIGS.keys()):
            plt.draw()
            plt.show()
        plt.ioff()
    if is_win:
        # this style basically works for Windows
        plt.draw()
        print("You must manually close all plots to continue")
        plt.show()


def clearFIG(fignum):
    plt.figure(num=fignum)
    plt.clf()
    if not isServer:
        plt.figtext(.02, .01, version_num)

# def gui_init(gvars,interface):
#	global globals, graphmenu
##	globals = gvars
##	graphmenu = interface
#


def click(event):
    print('you clicked', event.xdata, event.ydata)
#
#


def delticks(fig):
    """
     deletes half the x-axis tick marks
    Parameters
    ___________
    fig : matplotlib figure number

    """
    locs = fig.xaxis.get_ticklocs()
    nlocs = np.delete(locs, list(range(0, len(locs), 2)))
    fig.set_xticks(nlocs)


fig_x_pos = 25
fig_y_pos = 25
plt_num = 0


def plot_init(fignum, w, h):
    """
    initializes plot number fignum with width w and height h
    Parameters
    __________
    fignum : matplotlib figure number
    w : width
    h : height
    """
    global fig_x_pos, fig_y_pos, plt_num
    dpi = 80
    if isServer:
        dpi = 240
    # plt.ion()
    plt_num += 1
    fig = plt.figure(num=fignum, figsize=(w, h), dpi=dpi)
    if (not isServer) and (not set_env.IS_NOTEBOOK):
        plt.get_current_fig_manager().show()
        # plt.get_current_fig_manager().window.wm_geometry('+%d+%d' %
        # (fig_x_pos,fig_y_pos)) # this only works with matplotlib.use('TKAgg')
        fig_x_pos = fig_x_pos + dpi * (w) + 25
        if plt_num == 3:
            plt_num = 0
            fig_x_pos = 25
            fig_y_pos = fig_y_pos + dpi * (h) + 25
        plt.figtext(.02, .01, version_num)
# plt.connect('button_press_event',click)
#
    # plt.ioff()
    return fig


def plot3d_init(fignum):
    """
    initializes 3D plot
    """
    from mpl_toolkits.mplot3d import Axes3D
    fig = plt.figure(fignum)
    ax = fig.add_subplot(111, projection='3d')
    return ax


def plot_square(fignum):
    """
    makes the figure square (equal axes)
    Parameters
    __________
    fignum : matplotlib figure number
    """
    plt.figure(num=fignum)
    plt.axis('equal')


def gaussfunc(y, ybar, sigma):
    """
    cumulative normal distribution function of the variable y
    with mean ybar,standard deviation sigma
    uses expression 7.1.26 from Abramowitz & Stegun
    accuracy better than 1.5e-7 absolute
    Parameters
    _________
    y : input variable
    ybar : mean
    sigma : standard deviation

    """
    x = (y - ybar)/(np.sqrt(2.) * sigma)
    t = 1.0/(1.0 + .3275911 * abs(x))
    erf = 1.0 - np.exp(-x * x) * t * (.254829592 - t * (.284496736 -
                                                        t * (1.421413741 - t * (1.453152027 - t * 1.061405429))))
    erf = abs(erf)
    sign = x/abs(x)
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
        b = float(i)/float(len(X))
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
        t2 = -2. * np.log(d)
        t = np.sqrt(t2)
        x = t - ((2.515517 + .802853 * t + .010328 * t2)/
                        (1. + 1.432788 * t + .189269 * t2 + .001308 * t * t2))
        if p < 0.5:
            x = -x
    return x


def show(fig):
    plt.figure(fig)
    plt.show()


def plot_xy(fignum, X, Y, **kwargs):
    """
    deprecated, used in curie
    """
    plt.figure(num=fignum)
#    if 'poly' in kwargs.keys():
#          coeffs=np.polyfit(X,Y,kwargs['poly'])
#          polynomial=np.poly1d(coeffs)
#          xs=np.arange(np.min(X),np.max(X))
#          ys=polynomial(xs)
#          plt.plot(xs,ys)
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
        plt.errorbar(X, Y, fmt=sym, xerr=kwargs['xerr'])
    if 'yerr' in list(kwargs.keys()):
        plt.errorbar(X, Y, fmt=sym, yerr=kwargs['yerr'])
    if 'axis' in list(kwargs.keys()):
        if kwargs['axis'] == 'semilogx':
            plt.semilogx(X, Y, marker=sym[1], markerfacecolor=sym[0])
        if kwargs['axis'] == 'semilogy':
            plt.semilogy(X, Y, marker=sym[1], markerfacecolor=sym[0])
        if kwargs['axis'] == 'loglog':
            plt.loglog(X, Y, marker=sym[1], markerfacecolor=sym[0])
    else:
        plt.plot(X, Y, sym, linewidth=lw)
    if 'xlab' in list(kwargs.keys()):
        plt.xlabel(kwargs['xlab'])
    if 'ylab' in list(kwargs.keys()):
        plt.ylabel(kwargs['ylab'])
    if 'title' in list(kwargs.keys()):
        plt.title(kwargs['title'])
    if 'xmin' in list(kwargs.keys()):
        plt.axis([kwargs['xmin'], kwargs['xmax'],
                  kwargs['ymin'], kwargs['ymax']])
    if 'notes' in list(kwargs.keys()):
        for note in kwargs['notes']:
            plt.text(note[0], note[1], note[2])


def plot_site(fignum, SiteRec, data, key):
    """
    deprecated (used in ipmag)
    """
    print('Site mean data: ')
    print('   dec    inc n_lines n_planes kappa R alpha_95 comp coord')
    print(SiteRec['site_dec'], SiteRec['site_inc'], SiteRec['site_n_lines'], SiteRec['site_n_planes'], SiteRec['site_k'],
          SiteRec['site_r'], SiteRec['site_alpha95'], SiteRec['site_comp_name'], SiteRec['site_tilt_correction'])
    print('sample/specimen, dec, inc, n_specs/a95,| method codes ')
    for i in range(len(data)):
        print('%s: %s %s %s / %s | %s' % (data[i]['er_' + key + '_name'], data[i][key + '_dec'], data[i]
                                          [key + '_inc'], data[i][key + '_n'], data[i][key + '_alpha95'], data[i]['magic_method_codes']))
    plot_slnp(fignum, SiteRec, data, key)
    plot = input("s[a]ve plot, [q]uit or <return> to continue:   ")
    if plot == 'q':
        print("CUL8R")
        sys.exit()
    if plot == 'a':
        files = {}
        for key in list(EQ.keys()):
            files[key] = site + '_' + key + '.' + fmt
        save_plots(EQ, files)


def plot_qq_norm(fignum, Y, title):
    """
    makes a Quantile-Quantile plot for data
    Parameters
    _________
    fignum : matplotlib figure number
    Y : list or array of data
    title : title string for plot

    Returns
    ___________
    d,dc : the values for D and Dc (the critical value)
       if d>dc, likely to be normally distributed (95\% confidence)
    """
    plt.figure(num=fignum)
    if type(Y) == list:
        Y = np.array(Y)
    Y = np.sort(Y)  # sort the data
    n = len(Y)
    d, mean, sigma = k_s(Y)
    dc = 0.886/np.sqrt(float(n))
    X = []  # list for normal quantile
    for i in range(1, n + 1):
        p = float(i)/float(n + 1)
        X.append(qsnorm(p))
    plt.plot(X, Y, 'ro')
    plt.title(title)
    plt.xlabel('Normal Quantile')
    plt.ylabel('Data Quantile')
    bounds = plt.axis()
    notestr = 'N: ' + '%i' % (n)
    plt.text(-.9 * bounds[1], .9 * bounds[3], notestr)
    notestr = 'mean: ' + '%8.3e' % (mean)
    plt.text(-.9 * bounds[1], .8 * bounds[3], notestr)
    notestr = 'std dev: ' + '%8.3e' % (sigma)
    plt.text(-.9 * bounds[1], .7 * bounds[3], notestr)
    notestr = 'D: ' + '%8.3e' % (d)
    plt.text(-.9 * bounds[1], .6 * bounds[3], notestr)
    notestr = 'Dc: ' + '%8.3e' % (dc)
    plt.text(-.9 * bounds[1], .5 * bounds[3], notestr)
    return d, dc


def plot_qq_unf(fignum, D, title, subplot=False, degrees=True):
    """
    plots data against a uniform distribution in 0=>360.
    Parameters
    _________
    fignum : matplotlib figure number
    D : data
    title : title for plot
    subplot : if True, make this number one of two subplots
    degrees : if True, assume that these are degrees

    Return
    Mu : Mu statistic (Fisher et al., 1987)
    Mu_crit : critical value of Mu for uniform distribution

    Effect
    ______
    makes a Quantile Quantile plot of data
    """
    if subplot == True:
        plt.subplot(1, 2, fignum)
    else:
        plt.figure(num=fignum)
    X, Y, dpos, dneg = [], [], 0., 0.
    if degrees:
        D = (np.array(D)) % 360
    X = D/D.max()
    X = np.sort(X)
    n = float(len(D))
    i = np.arange(0, len(D))
    Y = (i-0.5)/n
    ds = (i/n)-X
    ds_neg = X-(i-1)/n # bugfix from Qian (6/17/21)
    dpos = ds.max()
    #dneg = ds.min() # this is wrong
    dneg = ds_neg.max() # bugfix from Qian (6/17/21)
    plt.plot(Y, X, 'ro')
    v = dneg + dpos  # kuiper's v
    # Mu of fisher et al. equation 5.16
    Mu = v * (np.sqrt(n) - 0.567 + 1.623/np.sqrt(n))
    plt.axis([0, 1., 0., 1.])
    bounds = plt.axis()
    notestr = 'N: ' + '%i' % (n)
    plt.text(.1 * bounds[1], .9 * bounds[3], notestr)
    notestr = 'Mu: ' + '%7.3f' % (Mu)
    plt.text(.1 * bounds[1], .8 * bounds[3], notestr)
    if Mu > 1.347:
        notestr = "Non-uniform (99%)"
    elif Mu < 1.207:
        notestr = "Uniform (95%)"
    elif Mu > 1.207:
        notestr = "Uniform (99%)"
    plt.text(.1 * bounds[1], .7 * bounds[3], notestr)
    plt.text(.1 * bounds[1], .7 * bounds[3], notestr)
    plt.title(title)
    plt.xlabel('Uniform Quantile')
    plt.ylabel('Data Quantile')
    #print (v,dneg,dpos)#DEBUG
    return Mu, 1.207


def plot_qq_exp(fignum, I, title, subplot=False):
    """
    plots data against an exponential distribution in 0=>90.

    Parameters
    _________
    fignum : matplotlib figure number
    I : data
    title : plot title
    subplot : boolean, if True plot as subplot with 1 row, two columns with fignum the plot number
    """
    if subplot == True:
        plt.subplot(1, 2, fignum)
    else:
        plt.figure(num=fignum)
    X, Y, dpos, dneg = [], [], 0., 0.
    rad = np.pi/180.
    xsum = 0
    for i in I:
        theta = (90. - i) * rad
        X.append(1. - np.cos(theta))
        xsum += X[-1]
    X.sort()
    n = float(len(X))
    kappa = (n - 1.)/xsum
    for i in range(len(X)):
        p = (float(i) - 0.5)/n
        Y.append(-np.log(1. - p))
        f = 1. - np.exp(-kappa * X[i])
        ds = float(i)/n - f
        if dpos < ds:
            dpos = ds
        ds = f - (float(i) - 1.)/n
        if dneg < ds:
            dneg = ds
    if dneg > dpos:
        ds = dneg
    else:
        ds = dpos
    Me = (ds - (0.2/n)) * (np.sqrt(n) + 0.26 +
                                     (0.5/(np.sqrt(n))))  # Eq. 5.15 from Fisher et al. (1987)

    plt.plot(Y, X, 'ro')
    bounds = plt.axis()
    plt.axis([0, bounds[1], 0., bounds[3]])
    notestr = 'N: ' + '%i' % (n)
    plt.text(.1 * bounds[1], .9 * bounds[3], notestr)
    notestr = 'Me: ' + '%7.3f' % (Me)
    plt.text(.1 * bounds[1], .8 * bounds[3], notestr)
    if Me > 1.094:
        notestr = "Not Exponential"
    else:
        notestr = "Exponential (95%)"
    plt.text(.1 * bounds[1], .7 * bounds[3], notestr)
    plt.title(title)
    plt.xlabel('Exponential Quantile')
    plt.ylabel('Data Quantile')
    return Me, 1.094


def plot_net(fignum):
    """
    draws circle and tick marks for equal area projection
    Parameters
    _________
    fignum : matplotlib figure number
    """
#
# make the perimeter
#
    plt.figure(num=fignum)
    plt.clf()
    if not isServer:
        plt.figtext(.02, .01, version_num)
    plt.axis("off")
    Dcirc = np.arange(0, 361.)
    Icirc = np.zeros(361, 'f')
    Xcirc, Ycirc = [], []
    for k in range(361):
        XY = pmag.dimap(Dcirc[k], Icirc[k])
        Xcirc.append(XY[0])
        Ycirc.append(XY[1])
    plt.plot(Xcirc, Ycirc, 'k')
#
# put on the tick marks
    Xsym, Ysym = [], []
    for I in range(10, 100, 10):
        XY = pmag.dimap(0., I)
        Xsym.append(XY[0])
        Ysym.append(XY[1])
    plt.plot(Xsym, Ysym, 'k+')
    Xsym, Ysym = [], []
    for I in range(10, 90, 10):
        XY = pmag.dimap(90., I)
        Xsym.append(XY[0])
        Ysym.append(XY[1])
    plt.plot(Xsym, Ysym, 'k+')
    Xsym, Ysym = [], []
    for I in range(10, 90, 10):
        XY = pmag.dimap(180., I)
        Xsym.append(XY[0])
        Ysym.append(XY[1])
    plt.plot(Xsym, Ysym, 'k+')
    Xsym, Ysym = [], []
    for I in range(10, 90, 10):
        XY = pmag.dimap(270., I)
        Xsym.append(XY[0])
        Ysym.append(XY[1])
    plt.plot(Xsym, Ysym, 'k+')
    for D in range(0, 360, 10):
        Xtick, Ytick = [], []
        for I in range(4):
            XY = pmag.dimap(D, I)
            Xtick.append(XY[0])
            Ytick.append(XY[1])
        plt.plot(Xtick, Ytick, 'k')
    BoxX, BoxY = [-1.1, 1.1, 1.1, -1.1, -1.1], [-1.1, -1.1, 1.1, 1.1, -1.1]
    plt.plot(BoxX, BoxY, 'k-', linewidth=.5)
    plt.axis("equal")


def plot_di(fignum, DIblock):
    global globals
    """
    plots directions on equal area net
    Parameters
    _________
    fignum : matplotlib figure number
    DIblock : nested list of dec, inc pairs
    """
    X_down, X_up, Y_down, Y_up = [], [], [], []  # initialize some variables
    plt.figure(num=fignum)
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
        #        plt.scatter(X_down,Y_down,marker='s',c='r')
        plt.scatter(X_down, Y_down, marker='o', c='blue')
        if globals != 0:
            globals.DIlist = X_down
            globals.DIlisty = Y_down
    if len(X_up) > 0:
        #        plt.scatter(X_up,Y_up,marker='s',facecolor='none',edgecolor='black')
        plt.scatter(X_up, Y_up, marker='o',
                    facecolor='white', edgecolor='blue')
        if globals != 0:
            globals.DIlist = X_up
            globals.DIlisty = Y_up


def plot_di_sym(fignum, DIblock, sym):
    global globals
    """
    plots directions on equal area net
    Parameters
    _________
    fignum : matplotlib figure number
    DIblock : nested list of dec, inc pairs
    sym : set matplotlib symbol (e.g., 'bo' for blue circles)
    """
    X_down, X_up, Y_down, Y_up = [], [], [], []  # initialize some variables
    plt.figure(num=fignum)
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
        plt.scatter(X_down, Y_down, marker=sym['lower'][0],
                    c=sym['lower'][1], s=size, edgecolor=sym['edgecolor'])
        if globals != 0:
            globals.DIlist = X_down
            globals.DIlisty = Y_down
    if len(X_up) > 0:
        plt.scatter(X_up, Y_up, marker=sym['upper'][0],
                    c=sym['upper'][1], s=size, edgecolor=sym['edgecolor'])
        if globals != 0:
            globals.DIlist = X_up
            globals.DIlisty = Y_up


def plot_circ(fignum, pole, ang, col):
    """
    function to put a small circle on an equal area projection plot, fig,fignum
    Parameters
    __________
    fignum : matplotlib figure number
    pole : dec,inc of center of circle
    ang : angle of circle
    col :
    """
    plt.figure(num=fignum)
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
    plt.plot(X_c_d, Y_c_d, col + '.', ms=5)
    plt.plot(X_c_up, Y_c_up, 'c.', ms=2)


#
#
#
def plot_zij(fignum, datablock, angle, s, norm=True):
    """
    function to make Zijderveld diagrams

    Parameters
    __________
    fignum : matplotlib figure number
    datablock : nested list of [step, dec, inc, M (Am2), type, quality]
                where type is a string, either 'ZI' or 'IZ' for IZZI experiments
    angle : desired rotation in the horizontal plane (0 puts X on X axis)
    s : specimen name
    norm : if True, normalize to initial magnetization = unity

    Effects
    _______
    makes a zijderveld plot

    """
    global globals
    plt.figure(num=fignum)
    plt.clf()
    if not isServer:
        plt.figtext(.02, .01, version_num)
    amin, amax = 0., -100.
    if norm == 0:
        fact = 1.
    else:
        try:
            fact = (1./datablock[0][3])   # normalize to NRM=1
        except ZeroDivisionError:
            fact = 1.
    # convert datablock to DataFrame data with  dec,inc, int
    data = pd.DataFrame(datablock)
    if len(data.columns) == 5:
        data.columns = ['treat', 'dec', 'inc', 'int', 'quality']
    if len(data.columns) == 6:
        data.columns = ['treat', 'dec', 'inc', 'int', 'type', 'quality']
    elif len(data.columns) == 7:
        data.columns = ['treat', 'dec', 'inc', 'int', 'type', 'quality', 'y']
    #print (len(data.columns))
    data['int'] = data['int']*fact  # normalize
    data['dec'] = (data['dec']-angle) % 360  # adjust X axis angle
    gdata = data[data['quality'].str.contains('g')]
    bdata = data[data['quality'].str.contains('b')]
    forVDS = gdata[['dec', 'inc', 'int']].values
    gXYZ = pd.DataFrame(pmag.dir2cart(forVDS))
    gXYZ.columns = ['X', 'Y', 'Z']
    amax = np.maximum(gXYZ.X.max(), gXYZ.Z.max())
    amin = np.minimum(gXYZ.X.min(), gXYZ.Z.min())
    if amin > 0:
        amin = 0
    bXYZ = pmag.dir2cart(bdata[['dec', 'inc', 'int']].values).transpose()
# plotting stuff
    if angle != 0:
        tempstr = "\n Declination rotated by: " + str(angle) + '\n'
    if globals != 0:
        globals.text.insert(globals.END, tempstr)
        globals.Zlist = gXYZ['x'].tolist()
        globals.Zlisty = gXYZ['y'].tolist()
        globals.Zlistz = gXYZ['z'].tolist()
    if len(bXYZ) > 0:
        plt.scatter(bXYZ[0], bXYZ[1], marker='d', c='y', s=30)
        plt.scatter(bXYZ[0], bXYZ[2], marker='d', c='y', s=30)
    plt.plot(gXYZ['X'], gXYZ['Y'], 'ro')
    plt.plot(gXYZ['X'], gXYZ['Z'], 'ws', markeredgecolor='blue')
    plt.plot(gXYZ['X'], gXYZ['Y'], 'r-')
    plt.plot(gXYZ['X'], gXYZ['Z'], 'b-')
    for k in range(len(gXYZ)):
        plt.annotate(str(k), (gXYZ['X'][k], gXYZ['Z']
                              [k]), ha='left', va='bottom')
    if amin > 0 and amax >0:amin=0 # complete the line
    if amin < 0 and amax <0:amax=0 # complete the line
    xline = [amin, amax]
   # yline=[-amax,-amin]
    yline = [amax, amin]
    zline = [0, 0]
    plt.plot(xline, zline, 'k-')
    plt.plot(zline, xline, 'k-')
    if angle != 0:
        xlab = "X: rotated to Dec = " + '%7.1f' % (angle)
    if angle == 0:
        xlab = "X: rotated to Dec = " + '%7.1f' % (angle)
    plt.xlabel(xlab)
    plt.ylabel('Circles: Y; Squares: Z')
    tstring = s + ': NRM = ' + '%9.2e' % (datablock[0][3])
    plt.axis([amin, amax, amax, amin])
    plt.axis("equal")
    plt.title(tstring)
#
#


def plot_mag(fignum, datablock, s, num, units, norm):
    """
    plots magnetization against (de)magnetizing temperature or field

    Parameters
    _________________
    fignum : matplotlib figure number for plotting
    datablock : nested list of [step, 0, 0, magnetization, 1,quality]
    s : string for title
    num : matplotlib figure number, can set to 1
    units : [T,K,U] for tesla, kelvin or arbitrary
    norm : [True,False] if True, normalize

    Effects
    ______
        plots figure
    """
    global globals, graphmenu
    Ints = []
    for plotrec in datablock:
        Ints.append(plotrec[3])
    Ints.sort()
    plt.figure(num=fignum)
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
            if norm:
                M.append(rec[3]/Ints[-1])
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
                    Vdif.append(vdir[2]/Ints[-1])
                    Vdif.append(vdir[2]/Ints[-1])
            recbak = []
            for el in rec:
                recbak.append(el)
            delta = .005 * M[0]
            if num == 1:
                if recnum % 2 == 0:
                    plt.text(T[-1] + delta, M[-1],
                             (' ' + str(recnum)), fontsize=9)
            recnum += 1
        else:
            if rec[0] < 200:
                Tex.append(rec[0] * 1e3)
            if rec[0] >= 200:
                Tex.append(rec[0] - 273)
            Mex.append(rec[3]/Ints[-1])
            recnum += 1
    if globals != 0:
        globals.MTlist = T
        globals.MTlisty = M
    if len(Mex) > 0 and len(Tex) > 0:
        plt.scatter(Tex, Mex, marker='d', color='k')
    if len(Vdif) > 0:
        Vdif.append(vdir[2]/Ints[-1])
        Vdif.append(0)
    if Tv:
        Tv.append(Tv[-1])
    plt.plot(T, M)
    plt.plot(T, M, 'ro')
    if len(Tv) == len(Vdif) and norm:
        plt.plot(Tv, Vdif, 'g-')
    if units == "T":
        plt.xlabel("Step (mT)")
    elif units == "K":
        plt.xlabel("Step (C)")
    elif units == "J":
        plt.xlabel("Step (J)")
    else:
        plt.xlabel("Step [mT,C]")
    if norm == 1:
        plt.ylabel("Fractional Magnetization")
    if norm == 0:
        plt.ylabel("Magnetization")
    plt.axvline(0, color='k')
    plt.axhline(0, color='k')
    tstring = s
    plt.title(tstring)
    plt.draw()

#
#


def plot_zed(ZED, datablock, angle, s, units):
    """
    function to make equal area plot and zijderveld plot

    Parameters
    _________
    ZED : dictionary with keys for plots
        eqarea : figure number for equal area projection
        zijd   : figure number for  zijderveld plot
        demag :  figure number for magnetization against demag step
        datablock : nested list of [step, dec, inc, M (Am2), quality]
        step : units assumed in SI
        M    : units assumed Am2
        quality : [g,b], good or bad measurement; if bad will be marked as such
    angle : angle for X axis in horizontal plane, if 0, x will be 0 declination
    s : specimen name
    units :  SI units ['K','T','U'] for kelvin, tesla or undefined

    Effects
    _______
       calls plotting functions for equal area, zijderveld and demag figures

    """
    for fignum in list(ZED.keys()):
        fig = plt.figure(num=ZED[fignum])
        plt.clf()
        if not isServer:
            plt.figtext(.02, .01, version_num)
    DIbad, DIgood = [], []
    for rec in datablock:
        if cb.is_null(rec[1],zero_as_null=False):
            print('-W- You are missing a declination for specimen', s, ', skipping this row')
            continue
        if cb.is_null(rec[2],zero_as_null=False):
            print('-W- You are missing an inclination for specimen', s, ', skipping this row')
            continue
        if rec[5] == 'b':
            DIbad.append((rec[1], rec[2]))
        else:
            DIgood.append((rec[1], rec[2]))
    badsym = {'lower': ['+', 'g'], 'upper': ['x', 'c']}
    if len(DIgood) > 0:
        plot_eq(ZED['eqarea'], DIgood, s)
        if len(DIbad) > 0:
            plot_di_sym(ZED['eqarea'], DIbad, badsym)
    elif len(DIbad) > 0:
        plot_eq_sym(ZED['eqarea'], DIbad, s, badsym)
    AngleX, AngleY = [], []
    XY = pmag.dimap(angle, 90.)
    AngleX.append(XY[0])
    AngleY.append(XY[1])
    XY = pmag.dimap(angle, 0.)
    AngleX.append(XY[0])
    AngleY.append(XY[1])
    plt.figure(num=ZED['eqarea'])
    # Draw a line for Zijderveld horizontal axis
    plt.plot(AngleX, AngleY, 'r-')
    if AngleX[-1] == 0:
        AngleX[-1] = 0.01
    plt.text(AngleX[-1] + (AngleX[-1]/abs(AngleX[-1])) * .1,
             AngleY[-1] + (AngleY[-1]/abs(AngleY[-1])) * .1, 'X')
    norm = 1
    #if units=="U": norm=0
    # if there are NO good points, don't try to plot
    if DIgood:
        plot_mag(ZED['demag'], datablock, s, 1, units, norm)
        plot_zij(ZED['zijd'], datablock, angle, s, norm)
    else:
        ZED.pop('demag')
        ZED.pop('zijd')
    return ZED


def plot_dir(ZED, pars, datablock, angle):
    """
    function to put the great circle on the equal area projection
    and plot start and end points of calculation

    DEPRECATED (used in zeq_magic)
    """
#
# find start and end points from datablock
#
    if pars["calculation_type"] == 'DE-FM':
        x, y = [], []
        plt.figure(num=ZED['eqarea'])
        XY = pmag.dimap(pars["specimen_dec"], pars["specimen_inc"])
        x.append(XY[0])
        y.append(XY[1])
        plt.scatter(x, y, marker='^', s=80, c='r')
        plt.show()
        return
    StartDir, EndDir = [0, 0, 1.], [0, 0, 1.]
    for rec in datablock:
        if rec[0] == pars["measurement_step_min"]:
            StartDir[0] = rec[1]
            StartDir[1] = rec[2]
            if pars["specimen_direction_type"] == 'l':
                StartDir[2] = rec[3]/datablock[0][3]
        if rec[0] == pars["measurement_step_max"]:
            EndDir[0] = rec[1]
            EndDir[1] = rec[2]
            if pars["specimen_direction_type"] == 'l':
                EndDir[2] = rec[3]/datablock[0][3]

#
#  put them on the plots
#
    x, y, z, pole = [], [], [], []
    if pars["calculation_type"] != 'DE-BFP':
        plt.figure(num=ZED['eqarea'])
        XY = pmag.dimap(pars["specimen_dec"], pars["specimen_inc"])
        x.append(XY[0])
        y.append(XY[1])
        plt.scatter(x, y, marker='d', s=80, c='b')
        x, y, z = [], [], []
        StartDir[0] = StartDir[0] - angle
        EndDir[0] = EndDir[0] - angle
        XYZs = pmag.dir2cart(StartDir)
        x.append(XYZs[0])
        y.append(XYZs[1])
        z.append(XYZs[2])
        XYZe = pmag.dir2cart(EndDir)
        x.append(XYZe[0])
        y.append(XYZe[1])
        z.append(XYZe[2])
        plt.figure(num=ZED['zijd'])
        plt.scatter(x, y, marker='d', s=80, c='g')
        plt.scatter(x, z, marker='d', s=80, c='g')
        plt.scatter(x, y, marker='o', c='r', s=20)
        plt.scatter(x, z, marker='s', c='w', s=20)
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
            cm = np.array(pars["center_of_mass"])/datablock[0][3]
            cmDir = pmag.cart2dir(cm)
            cmDir[0] = cmDir[0] - angle
            cm = pmag.dir2cart(cmDir)
            diff = []
            for i in range(3):
                diff.append(XYZe[i] - XYZs[i])
            R = np.sqrt(diff[0]**2 + diff[1]**2 + diff[2]**2)
            P = pmag.dir2cart(
                ((pars["specimen_dec"] - angle), pars["specimen_inc"], R/2.5))
            px, py, pz = [], [], []
            px.append((cm[0] + P[0]))
            py.append((cm[1] + P[1]))
            pz.append((cm[2] + P[2]))
            px.append((cm[0] - P[0]))
            py.append((cm[1] - P[1]))
            pz.append((cm[2] - P[2]))

        plt.plot(px, py, 'g', linewidth=2)
        plt.plot(px, pz, 'g', linewidth=2)
        plt.axis("equal")
    else:
        plt.figure(num=ZED['eqarea'])
        XY = pmag.dimap(StartDir[0], StartDir[1])
        x.append(XY[0])
        y.append(XY[1])
        XY = pmag.dimap(EndDir[0], EndDir[1])
        x.append(XY[0])
        y.append(XY[1])
        plt.scatter(x, y, marker='d', s=80, c='b')
        pole.append(pars["specimen_dec"])
        pole.append(pars["specimen_inc"])
        plot_circ(ZED['eqarea'], pole, 90., 'g')
        plt.xlim((-1., 1.))
        plt.ylim((-1., 1.))
        plt.axis("equal")
        #plt.draw()


def plot_arai(fignum, indata, s, units):
    """
    makes Arai plots for Thellier-Thellier type experiments

    Parameters
    __________
    fignum : figure number of matplotlib plot object
    indata : nested list of data for Arai plots:
        the araiblock of data prepared by pmag.sortarai()
    s : specimen name
    units : [K, J, ""] (kelvin, joules, unknown)
    Effects
    _______
    makes the Arai plot
    """
    global globals
    plt.figure(num=fignum)
    plt.clf()
    if not isServer:
        plt.figtext(.02, .01, version_num)
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
        forVDS.append([zrec[1], zrec[2], zrec[3]/first_Z[0][3]])
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
        x.append(irec[3]/first_Z[0][3])
        y.append(zrec[3]/first_Z[0][3])
        if ZI == 1:
            x_zi.append(irec[3]/first_Z[0][3])
            y_zi.append(zrec[3]/first_Z[0][3])
        else:
            x_iz.append(irec[3]/first_Z[0][3])
            y_iz.append(zrec[3]/first_Z[0][3])
        plt.text(x[-1], y[-1], (' ' + str(recnum)), fontsize=9)
        recnum += 1
# now deal with ptrm checks.
    if len(ptrm_check) != 0:
        for prec in ptrm_check:
            step = prec[0]
            for zrec in first_Z:
                if zrec[0] == step:
                    break
            xptrm.append(prec[3]/first_Z[0][3])
            yptrm.append(zrec[3]/first_Z[0][3])
# now deal with zptrm checks.
    if len(zptrm_check) != 0:
        for prec in zptrm_check:
            step = prec[0]
            for zrec in first_Z:
                if zrec[0] == step:
                    break
            xzptrm.append(prec[3]/first_Z[0][3])
            yzptrm.append(zrec[3]/first_Z[0][3])
# and the pTRM tails
    if len(ptrm_tail) != 0:
        for trec in ptrm_tail:
            step = trec[0]
            for irec in first_I:
                if irec[0] == step:
                    break
            xptrmt.append(irec[3]/first_Z[0][3])
            yptrmt.append((trec[3]/first_Z[0][3]))
# now plot stuff
    if len(x) == 0:
        print("Can't do nuttin for ya")
        return
    try:
        if len(x_zi) > 0:
            plt.scatter(x_zi, y_zi, marker='o', c='r',
                        edgecolors="none")  # zero field-infield
        if len(x_iz) > 0:
            plt.scatter(x_iz, y_iz, marker='s', c='b',
                        faceted="True")  # infield-zerofield
    except:
        if len(x_zi) > 0:
            plt.scatter(x_zi, y_zi, marker='o', c='r')  # zero field-infield
        if len(x_iz) > 0:
            plt.scatter(x_iz, y_iz, marker='s', c='b')  # infield-zerofield
    plt.plot(x, y, 'r')
    if globals != 0:
        globals.MTlist = x
        globals.MTlisty = y
    if len(xptrm) > 0:
        plt.scatter(xptrm, yptrm, marker='^', c='g', s=80)
    if len(xzptrm) > 0:
        plt.scatter(xzptrm, yzptrm, marker='v', c='c', s=80)
    if len(xptrmt) > 0:
        plt.scatter(xptrmt, yptrmt, marker='s', c='b', s=80)
    try:
        plt.axhline(0, color='k')
        plt.axvline(0, color='k')
    except:
        pass
    plt.xlabel("pTRM gained")
    plt.ylabel("NRM remaining")
    tstring = s + ': NRM = ' + '%9.2e' % (first_Z[0][3])
    plt.title(tstring)
# put on VDS
    vds = pmag.dovds(forVDS)
    plt.axhline(vds, color='b')
    plt.text(1., vds - .1, ('VDS '), fontsize=9)
#    bounds=plt.axis()
#    if bounds[1]<1:plt.axis([bounds[0], 1., bounds[2], bounds[3]])


def plot_np(fignum, indata, s, units):
    """
    makes plot of de(re)magnetization data for Thellier-Thellier type experiment

    Parameters
    __________
    fignum : matplotlib figure number
    indata :  araiblock from, e.g., pmag.sortarai()
    s : specimen name
    units : [K, J, ""] (kelvin, joules, unknown)

    Effect
    _______
    Makes a plot
    """
    global globals
    first_Z, first_I, ptrm_check, ptrm_tail = indata[0], indata[1], indata[2], indata[3]
    plt.figure(num=fignum)
    plt.clf()
    if not isServer:
        plt.figtext(.02, .01, version_num)
    X, Y, recnum = [], [], 0
#
    for rec in first_Z:
        if units == "K":
            if rec[0] != 0:
                X.append(rec[0] - 273.)
            else:
                X.append(rec[0])
        if (units == "J") or (not units) or (units == "T"):
            X.append(rec[0])
        Y.append(old_div(rec[3], first_Z[0][3]))
        delta = .02 * Y[0]
        if recnum % 2 == 0:
            plt.text(X[-1] - delta, Y[-1] + delta,
                     (' ' + str(recnum)), fontsize=9)
        recnum += 1
    plt.plot(X, Y)
    plt.scatter(X, Y, marker='o', color='b')
    X, Y = [], []
    for rec in first_I:
        if units == "K":
            if rec[0] != 0:
                X.append(rec[0] - 273)
            else:
                X.append(rec[0])
        if (units == "J") or (not units) or (units == "T"):
            X.append(rec[0])
        Y.append(old_div(rec[3], first_Z[0][3]))
    if globals != 0:
        globals.DIlist = X
        globals.DIlisty = Y
    plt.plot(X, Y)
    plt.scatter(X, Y, marker='s', color='r')
    plt.ylabel("Circles: NRM; Squares: pTRM")
    if units == "K":
        plt.xlabel("Temperature (C)")
    elif units == "J":
        plt.xlabel("Microwave Energy (J)")
    else:
        plt.xlabel("")
    title = s + ": NRM = " + '%9.2e' % (first_Z[0][3])
    plt.title(title)
    plt.axhline(y=0, xmin=0, xmax=1, color='k')
    plt.axvline(x=0, ymin=0, ymax=1, color='k')


def plot_arai_zij(ZED, araiblock, zijdblock, s, units):
    """
    calls the four plotting programs for Thellier-Thellier experiments

    Parameters
    __________
    ZED : dictionary with plotting figure keys:
        deremag : figure for de (re) magnezation plots
        arai : figure for the Arai diagram
        eqarea : equal area projection of data, color coded by
            red circles: ZI steps
            blue squares: IZ steps
            yellow triangles : pTRM steps
        zijd : Zijderveld diagram color coded by ZI, IZ steps
        deremag : demagnetization and remagnetization versus temperature
    araiblock : nested list of required data from Arai plots
    zijdblock : nested list of required data for Zijderveld plots
    s : specimen name
    units : units for the arai and zijderveld plots

    Effects
    ________
    Makes four plots from the data by calling
    plot_arai : Arai plots
    plot_teq : equal area projection for Thellier data
    plotZ : Zijderveld diagram
    plot_np : de (re) magnetization diagram
    """
    angle = zijdblock[0][1]
    norm = 1
    if units == "U":
        norm = 0
    plot_arai(ZED['arai'], araiblock, s, units)
    plot_teq(ZED['eqarea'], araiblock, s, "")
    plot_zij(ZED['zijd'], zijdblock, angle, s, norm)
    plot_np(ZED['deremag'], araiblock, s, units)
    return ZED


def plot_b(Figs, araiblock, zijdblock, pars):
    """
    deprecated (used in thellier_magic/microwave_magic)
    """
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
        plt.figure(num=Figs['zijd'])
        plt.scatter(zx, zy, marker='d', s=100, c='y')
        plt.scatter(zx, zz, marker='d', s=100, c='y')
        plt.axis("equal")
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
    plot_teq(Figs['eqarea'], newblock, "", pars)
    plt.figure(num=Figs['arai'])
    plt.scatter(ax, ay, marker='d', s=100, c='y')
#
#  find midpoint between two endpoints
#
    sy = []
    sy.append((pars["specimen_b"] * ax[0] +
               old_div(pars["specimen_ytot"], first_Z[0][3])))
    sy.append((pars["specimen_b"] * ax[1] +
               old_div(pars["specimen_ytot"], first_Z[0][3])))
    plt.plot(ax, sy, 'g', linewidth=2)
    bounds = plt.axis()
    if pars['specimen_grade'] != '':
        notestr = 'Grade: ' + pars["specimen_grade"]
        plt.text(.7 * bounds[1], .9 * bounds[3], notestr)
    notestr = 'B: ' + '%6.2f' % (pars["specimen_int"] * 1e6) + ' uT'
    plt.text(.7 * bounds[1], .8 * bounds[3], notestr)


def plot_slnp(fignum, SiteRec, datablock, key):
    """
    plots lines and planes on a great  circle with alpha 95 and mean
    deprecated (used in pmagplotlib)
    """
# make the stereonet
    plt.figure(num=fignum)
    plot_net(fignum)
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
        plot_di(fignum, DIblock)  # plot directed lines
    if len(GCblock) > 0:
        for pole in GCblock:
            plot_circ(fignum, pole, 90., 'g')  # plot directed lines
#
# put on the mean direction
#
    x, y = [], []
    XY = pmag.dimap(float(SiteRec["site_dec"]), float(SiteRec["site_inc"]))
    x.append(XY[0])
    y.append(XY[1])
    plt.scatter(x, y, marker='d', s=80, c='g')
    plt.title(title)
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
    plt.plot(Xcirc, Ycirc, 'g')


def plot_lnp(fignum, s, datablock, fpars, direction_type_key):
    """
    plots lines and planes on a great  circle with alpha 95 and mean

    Parameters
    _________
    fignum : number of plt.figure() object
    s : str
      name of site for title
    datablock : nested list of dictionaries with keys in 3.0 or 2.5 format
        3.0 keys: dir_dec, dir_inc, dir_tilt_correction = [-1,0,100], method_codes =['DE-BFP','DE-BFL']
        2.5 keys: dec, inc, tilt_correction = [-1,0,100],direction_type_key =['p','l']
    fpars : Fisher parameters calculated by, e.g., pmag.dolnp() or pmag.dolnp3_0()
    direction_type_key : key for dictionary direction_type ('specimen_direction_type')
    Effects
    _______
    plots the site level figure
    """
# make the stereonet
    plot_net(fignum)
#
#   plot on the data
#
    dec_key, inc_key, tilt_key = 'dec', 'inc', 'tilt_correction'
    if 'dir_dec' in datablock[0].keys():  # this is data model 3.0
        dec_key, inc_key, tilt_key = 'dir_dec', 'dir_inc', 'dir_tilt_correction'
    coord = datablock[0][tilt_key]
    title = s
    if coord == '-1':
        title = title + ": specimen coordinates"
    if coord == '0':
        title = title + ": geographic coordinates"
    if coord == '100':
        title = title + ": tilt corrected coordinates"
    DIblock, GCblock = [], []
    for plotrec in datablock:
        if ('direction_type_key' in plotrec.keys() and plotrec[direction_type_key] == 'p') or 'DE-BFP' in plotrec['method_codes']:  # direction is pole to plane
       # if plotrec[direction_type_key] == 'p':  # direction is pole to plane
            GCblock.append((float(plotrec[dec_key]), float(plotrec[inc_key])))
        else:  # assume direction is a directed line
            DIblock.append((float(plotrec[dec_key]), float(plotrec[inc_key])))
    if len(DIblock) > 0:
        plot_di(fignum, DIblock)  # plot directed lines
    if len(GCblock) > 0:
        for pole in GCblock:
            plot_circ(fignum, pole, 90., 'g')  # plot directed lines
#
# put on the mean direction
#
    x, y = [], []
    XY = pmag.dimap(float(fpars["dec"]), float(fpars["inc"]))
    x.append(XY[0])
    y.append(XY[1])
    plt.figure(num=fignum)
    plt.scatter(x, y, marker='d', s=80, c='g')
    plt.title(title)
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
    plt.plot(Xcirc, Ycirc, 'g')


def plot_eq(fignum, DIblock, s):
    """
    plots directions on eqarea projection
    Parameters
    __________
    fignum : matplotlib figure number
    DIblock : nested list of dec/inc pairs
    s : specimen name
    """
# make the stereonet
    plt.figure(num=fignum)
    if len(DIblock) < 1:
        return
    # plt.clf()
    if not isServer:
        plt.figtext(.02, .01, version_num)
    plot_net(fignum)
#
#   put on the directions
#
    plot_di(fignum, DIblock)  # plot directions
    plt.axis("equal")
    plt.text(-1.1, 1.15, s)
    plt.draw()


def plot_eq_sym(fignum, DIblock, s, sym):
    """
    plots directions with specified symbol
    Parameters
    __________
    fignum : matplotlib figure number
    DIblock : nested list of dec/inc pairs
    s : specimen name
    sym : matplotlib symbol (e.g., 'bo' for blue circle)
    """
# make the stereonet
    plt.figure(num=fignum)
    if len(DIblock) < 1:
        return
    # plt.clf()
    if not isServer:
        plt.figtext(.02, .01, version_num)
    plot_net(fignum)
#
#   put on the directions
#
    plot_di_sym(fignum, DIblock, sym)  # plot directions with symbols in sym
    plt.axis("equal")
    plt.text(-1.1, 1.15, s)
#


def plot_teq(fignum, araiblock, s, pars):
    """
    plots directions  of pTRM steps and zero field steps

    Parameters
    __________
    fignum : figure number for matplotlib object
    araiblock : nested list of data from pmag.sortarai()
    s : specimen name
    pars : default is "",
        otherwise is dictionary with keys:
        'measurement_step_min' and 'measurement_step_max'

    Effects
    _______
    makes the equal area projection with color coded symbols
        red circles: ZI steps
        blue squares: IZ steps
        yellow : pTRM steps


    """
    first_Z, first_I = araiblock[0], araiblock[1]
# make the stereonet
    plt.figure(num=fignum)
    plt.clf()
    ZIblock, IZblock, pTblock = [], [], []
    for zrec in first_Z:  # sort out the zerofield steps
        if zrec[4] == 1:  # this is a ZI step
            ZIblock.append([zrec[1], zrec[2]])
        else:
            IZblock.append([zrec[1], zrec[2]])
    plot_net(fignum)
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
        plt.figtext(.02, .01, version_num)
#
#   put on the directions
#
    sym = {'lower': ['o', 'r'], 'upper': ['o', 'm']}
    if len(ZIblock) > 0:
        plot_di_sym(fignum, ZIblock, sym)  # plot ZI directions
    sym = {'lower': ['s', 'b'], 'upper': ['s', 'c']}
    if len(IZblock) > 0:
        plot_di_sym(fignum, IZblock, sym)  # plot IZ directions
    sym = {'lower': ['^', 'g'], 'upper': ['^', 'y']}
    if len(pTblock) > 0:
        plot_di_sym(fignum, pTblock, sym)  # plot pTRM directions
    plt.axis("equal")
    plt.text(-1.1, 1.15, s)


def save_plots(Figs, filenames, **kwargs):
    """
    Parameters
    ----------
    Figs : dict
        dictionary of plots, e.g. {'eqarea': 1, ...}
    filenames : dict
        dictionary of filenames, e.g. {'eqarea': 'mc01a_eqarea.svg', ...}
        dict keys should correspond with Figs
    """
    saved = []
    for key in list(Figs.keys()):
        try:
            plt.figure(num=Figs[key])
            fname = filenames[key]
            if set_env.IS_WIN:  # always truncate filenames if on Windows
                fname = os.path.split(fname)[1]
            if not isServer:  # remove illegal ':' character for windows
                fname = fname.replace(':', '_')
            if 'incl_directory' in kwargs.keys() and not set_env.IS_WIN:
                if kwargs['incl_directory']:
                    pass # do not flatten file name
                else:
                    fname = fname.replace('/', '-') # flatten file name
            else:
                fname = fname.replace('/', '-') # flatten file name
            if 'dpi' in list(kwargs.keys()):
                plt.savefig(fname, dpi=kwargs['dpi'])
            elif isServer:
                plt.savefig(fname, dpi=240)
            else:
                plt.savefig(fname)
            if verbose:
                print(Figs[key], " saved in ", fname)
            saved.append(fname)
            plt.close(Figs[key])
        except Exception as ex:
            print(type(ex), ex)
            print('could not save: ', Figs[key], filenames[key])
            print("output file format not supported ")
    return saved
#


def plot_evec(fignum, Vs, symsize, title):
    """
    plots eigenvector directions of S vectors

    Parameters
    ________
    fignum : matplotlib figure number
    Vs : nested list of eigenvectors
    symsize : size in pts for symbol
    title : title for plot
    """
#
    plt.figure(num=fignum)
    plt.text(-1.1, 1.15, title)
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
        plt.scatter(X, Y, s=symsize,
                    marker=symb[VEC], c=col[VEC], edgecolors='none')
    plt.axis("equal")
#


def plot_ell(fignum, pars, col='k', lower=True, plot=True):
    """
    function to calculate/plot points on an ellipse about Pdec,Pdip with angle beta,gamma
    Parameters
    _________
    fignum : matplotlib figure number
    pars : list of [Pdec, Pinc, beta, Bdec, Binc, gamma, Gdec, Ginc ]
         where P is direction, Bdec,Binc are beta direction, and Gdec,Ginc are gamma direction
    col : color for ellipse (default is black 'k')
    lower : boolean, if True, lower hemisphere projection
    plot : boolean, if False, return the points, if True, make the plot
    """
    rad = np.pi/180.
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
        psi = float(i) * np.pi / xnum
        v[0] = np.sin(beta) * np.cos(psi)
        v[1] = np.sin(gamma) * np.sin(psi)
        v[2] = np.sqrt(1. - v[0]**2 - v[1]**2)
        elli = [0, 0, 0]
# calculate points on the ellipse
        for j in range(3):
            for k in range(3):
                # cartesian coordinate j of ellipse
                elli[j] = elli[j] + t[j][k] * v[k]
        pts = pmag.cart2dir(elli)
        PTS.append([pts[0], pts[1]])
        # put on an equal area projection
        R = old_div(np.sqrt(
            1. - abs(elli[2])), (np.sqrt(elli[0]**2 + elli[1]**2)))
        if elli[2] <= 0:
            #            for i in range(3): elli[i]=-elli[i]
            X_up.append(elli[1] * R)
            Y_up.append(elli[0] * R)
        else:
            X_ell.append(elli[1] * R)
            Y_ell.append(elli[0] * R)
    if plot == 1:
        plt.figure(num=fignum)
        col = col[0]+'.'
        if X_ell != []:
            plt.plot(X_ell, Y_ell, col, markersize=3)
        if X_up != []:
            plt.plot(X_up, Y_up, col, markersize=3)
    else:
        return PTS


#
#
fig_y_pos = 25


def vertical_plot_init(fignum, w, h):

    # this is same as plot_init, but stacks things  vertically
    global fig_y_pos
    dpi = 80
    # plt.ion()
    plt.figure(num=fignum, figsize=(w, h), dpi=dpi)
#    if not isServer:
#        plt.get_current_fig_manager().window.wm_geometry('+%d+%d' % (25,fig_y_pos))
#        fig_y_pos = fig_y_pos + dpi*(h) + 25


def plot_strat(fignum, data, labels):
    """
     plots a time/depth series
     Parameters
     _________
     fignum : matplotlib figure number
     data : nested list of [X,Y] pairs
     labels : [xlabel, ylabel, title]
    """
    vertical_plot_init(fignum, 10, 3)
    xlab, ylab, title = labels[0], labels[1], labels[2]
    X, Y = [], []
    for rec in data:
        X.append(rec[0])
        Y.append(rec[1])
    plt.plot(X, Y)
    plt.plot(X, Y, 'ro')
    plt.xlabel(xlab)
    plt.ylabel(ylab)
    plt.title(title)

#
#


def plot_cdf(fignum, data, xlab, sym, title, **kwargs):
    """ Makes a plot of the cumulative distribution function.
    Parameters
    __________
    fignum : matplotlib figure number, if None, then plots on default figure
    data : list of data to be plotted - doesn't need to be sorted
    sym : matplotlib symbol for plotting, e.g., 'r--' for a red dashed line
    **kwargs :  optional dictionary with {'color': color, 'linewidth':linewidth, 'fontsize':fontsize for axes labels}

    Returns
    __________
    x : sorted list of data
    y : fraction of cdf
    """
#
    #if len(sym)==1:sym=sym+'-'
    if fignum != None:
        plt.figure(num=fignum,)
        plt.clf()

    #fig = plt.figure(num=fignum)
    # sdata=np.array(data).sort()
    sdata = []
    for d in data:
        sdata.append(d)  # have to copy the data to avoid overwriting it!
    #sdata.sort()
    X, Y = [], []
    color = ""
    for j in range(len(sdata)):
        Y.append(float(j)/float(len(sdata)))
        X.append(sdata[j])
    if 'color' in list(kwargs.keys()):
        color = kwargs['color']
    if 'linewidth' in list(kwargs.keys()):
        lw = kwargs['linewidth']
    else:
        lw = 1
    if color != "":
        plt.plot(X, Y, color=color, linewidth=lw)
    else:
        plt.plot(X, Y, sym, linewidth=lw)

    plt.xlabel(xlab, fontsize=kwargs.get('fontsize', 12))
    plt.ylabel('Cumulative Distribution', fontsize=kwargs.get('fontsize', 12))
    plt.title(title)
    return X, Y
#


def plot_hs(fignum, Ys, c, ls):
    """
    plots  horizontal lines at Ys values

    Parameters
    _________
    fignum : matplotlib figure number
    Ys : list of Y values for lines
    c : color for lines
    ls : linestyle for lines
    """
    fig = plt.figure(num=fignum)
    for yv in Ys:
        bounds = plt.axis()
        plt.axhline(y=yv, xmin=0, xmax=1, linewidth=1, color=c, linestyle=ls)
#


def plot_vs(fignum, Xs, c, ls):
    """
    plots  vertical lines at Xs values

    Parameters
    _________
    fignum : matplotlib figure number
    Xs : list of X values for lines
    c : color for lines
    ls : linestyle for lines
    """
    fig = plt.figure(num=fignum)
    for xv in Xs:
        bounds = plt.axis()
        plt.axvline(
            x=xv, ymin=bounds[2], ymax=bounds[3], linewidth=1, color=c, linestyle=ls)


def plot_ts(fignum, dates, ts):
    """
    plot the geomagnetic polarity time scale

    Parameters
    __________
    fignum : matplotlib figure number
    dates : bounding dates for plot
    ts : time scale ck95, gts04, or gts12
    """
    vertical_plot_init(fignum, 10, 3)
    TS, Chrons = pmag.get_ts(ts)
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
            plt.plot(X, Y, 'k')
            plot_vs(fignum, dates, 'w', '-')
            plot_hs(fignum, [1.1, -.1], 'w', '-')
            plt.xlabel("Age (Ma): " + ts)
            isign = -1
            for c in Chrons:
                off = -.1
                isign = -1 * isign
                if isign > 0:
                    off = 1.05
                if c[1] >= X[0] and c[1] < X[-1]:
                    plt.text(c[1] - .2, off, c[0])
            return


def plot_hys(fignum, B, M, s):
    """
   function to plot hysteresis data
   Parameters:
   _____________________
   Input :
       fignum : matplotlib figure number
       B : list of field values (in tesla)
       M : list of magnetizations
   Output :
       hpars : dictionary of hysteresis parameters
           keys: ['hysteresis_xhf', 'hysteresis_ms_moment', 'hysteresis_mr_moment', 'hysteresis_bc']
       deltaM : list of differences between down and upgoing loops
       Bdm : field values

    """
    B = list(B)
    from . import spline
    if fignum != 0:
        plt.figure(num=fignum)
        plt.clf()
        if not isServer:
            plt.figtext(.02, .01, version_num)
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
    polyU = np.polyfit(Bslop, Mslop, 1)
    # adjust slope with first 30 points of ascending branch
    Bslop = B[kmin:kmin + (Nint + 1)]
    Mslop = Mfix[kmin:kmin + (Nint + 1)]
    # best fit line to high field points
    polyL = np.polyfit(Bslop, Mslop, 1)
    xhf = 0.5 * (polyU[0] + polyL[0])  # mean of two slopes
    # convert B to A/m, high field slope in m^3
    hpars['hysteresis_xhf'] = '%8.2e' % (xhf * 4 * np.pi * 1e-7)
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
    for b in np.arange(B[0], step=incr):  # get range of field values
        Mpos = ((Iupper(b) - Ilower(b)))  # evaluate on both sides of B
        Mneg = ((Iupper(-b) - Ilower(-b)))
        Bdm.append(b)
        deltaM.append(0.5 * (Mpos + Mneg))  # take average delta M
    for k in range(Npts):
        MadjN.append(old_div(Moff[k], Msat))
        Mnorm.append(old_div(M[k], Msat))
    if fignum != 0:
        plt.plot(B, Mnorm, 'r')
        plt.plot(B, MadjN, 'b')
        plt.xlabel('B (T)')
        plt.ylabel("M/Msat")
        plt.axhline(0, color='k')
        plt.axvline(0, color='k')
        plt.title(s)
# find Mr : average of two spline fits evaluated at B=0 (times Msat)
    Mr = Msat * 0.5 * (Iupper(0.) - Ilower(0.))
    hpars['hysteresis_mr_moment'] = '%8.3e' % (Mr)
# find Bc (x intercept), interpolate between two bounding points
    Bz = B[Mzero - 1:Mzero + 1]
    Mz = Moff[Mzero - 1:Mzero + 1]
    Baz = B[Mazero - 1:Mazero + 1]
    Maz = Moff[Mazero - 1:Mazero + 1]
    try:
        # best fit line through two bounding points
        poly = np.polyfit(Bz, Mz, 1)
        Bc = old_div(-poly[1], poly[0])  # x intercept
        # best fit line through two bounding points
        poly = np.polyfit(Baz, Maz, 1)
        Bac = old_div(-poly[1], poly[0])  # x intercept
        hpars['hysteresis_bc'] = '%8.3e' % (0.5 * (abs(Bc) + abs(Bac)))
    except:
        hpars['hysteresis_bc'] = '0'
    return hpars, deltaM, Bdm
#


def plot_delta_m(fignum, B, DM, Bcr, s):
    """
    function to plot Delta M curves

    Parameters
    __________
    fignum : matplotlib figure number
    B : array of field values
    DM : array of difference between top and bottom curves in hysteresis loop
    Bcr : coercivity of remanence
    s : specimen name
    """
    plt.figure(num=fignum)
    plt.clf()
    if not isServer:
        plt.figtext(.02, .01, version_num)
    plt.plot(B, DM, 'b')
    plt.xlabel('B (T)')
    plt.ylabel('Delta M')
    linex = [0, Bcr, Bcr]
    liney = [old_div(DM[0], 2.), old_div(DM[0], 2.), 0]
    plt.plot(linex, liney, 'r')
    plt.title(s)
#


def plot_d_delta_m(fignum, Bdm, DdeltaM, s):
    """
    function to plot d (Delta M)/dB  curves

    Parameters
    __________
    fignum : matplotlib figure number
    Bdm : change in field
    Ddelta M : change in delta M
    s : specimen name
    """
    plt.figure(num=fignum)
    plt.clf()
    if not isServer:
        plt.figtext(.02, .01, version_num)
    start = len(Bdm) - len(DdeltaM)
    plt.plot(Bdm[start:], DdeltaM, 'b')
    plt.xlabel('B (T)')
    plt.ylabel('d (Delta M)/dB')
    plt.title(s)
#


def plot_imag(fignum, Bimag, Mimag, s):
    """
    function to plot d (Delta M)/dB  curves
    """
    plt.figure(num=fignum)
    plt.clf()
    if not isServer:
        plt.figtext(.02, .01, version_num)
    plt.plot(Bimag, Mimag, 'r')
    plt.xlabel('B (T)')
    plt.ylabel('M/Ms')
    plt.axvline(0, color='k')
    plt.title(s)
#


def plot_hdd(HDD, B, M, s):
    """
    Function to make hysteresis, deltaM and DdeltaM plots
    Parameters:
    _______________
    Input
        HDD :  dictionary with figure numbers for the keys:
            'hyst' : hysteresis plot  normalized to maximum value
            'deltaM' : Delta M plot
            'DdeltaM' : differential of Delta M plot
        B : list of field values in tesla
        M : list of magnetizations in arbitrary units
        s : specimen name string
    Ouput
      hpars : dictionary of hysteresis parameters with keys:
        'hysteresis_xhf', 'hysteresis_ms_moment', 'hysteresis_mr_moment', 'hysteresis_bc'

    """
    hpars, deltaM, Bdm = plot_hys(
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
        poly = np.polyfit(Bhf, Mhf, 1)
        Bcr = old_div((.5 * deltaM[0] - poly[1]), poly[0])
        hpars['hysteresis_bcr'] = '%8.3e' % (Bcr)
        hpars['magic_method_codes'] = "LP-BCR-HDM"
        if HDD['deltaM'] != 0:
            plot_delta_m(HDD['deltaM'], Bdm, deltaM, Bcr, s)
            plt.axhline(0, color='k')
            plt.axvline(0, color='k')
            plot_d_delta_m(HDD['DdeltaM'], Bdm, DdeltaM, s)
    except:
        hpars['hysteresis_bcr'] = '0'
        hpars['magic_method_codes'] = ""
    return hpars
#


def plot_day(fignum, BcrBc, S, sym, **kwargs):
    """
    function to plot Day plots

    Parameters
    _________
    fignum : matplotlib figure number
    BcrBc : list or array ratio of coercivity of remenance to coercivity
    S : list or array ratio of saturation remanence to saturation magnetization (squareness)
    sym : matplotlib symbol (e.g., 'rs' for red squares)
    **kwargs :  dictionary with {'names':[list of names for symbols]}
    """
    plt.figure(num=fignum)
    plt.plot(BcrBc, S, sym)
    plt.axhline(0, color='k')
    plt.axhline(.05, color='k')
    plt.axhline(.5, color='k')
    plt.axvline(1, color='k')
    plt.axvline(4, color='k')
    plt.xlabel('Bcr/Bc')
    plt.ylabel('Mr/Ms')
    plt.title('Day Plot')
    plt.xlim(0, 6)
    #bounds= plt.axis()
    #plt.axis([0, bounds[1],0, 1])
    mu_o = 4. * np.pi * 1e-7
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
    f_sd = np.arange(1., 0., -.01)  # fraction of sd
    f_md = 1. - f_sd  # fraction of md
    f_sp = 1. - f_sd  # fraction of sp
    # Mr/Ms ratios for USD,MD and Jax shaped
    sdrat, mdrat, cbrat = 0.498, 0.048, 0.6
    Mrat = f_sd * sdrat + f_md * mdrat  # linear mixing - eq. 9 in Dunlop 2002
    Bc = old_div((f_sd * chi_sd * Bc_sd + f_md * chi_md * Bc_md),
                 (f_sd * chi_sd + f_md * chi_md))  # eq. 10 in Dunlop 2002
    Bcr = old_div((f_sd * chi_r_sd * Bcr_sd + f_md * chi_r_md * Bcr_md),
                  (f_sd * chi_r_sd + f_md * chi_r_md))  # eq. 11 in Dunlop 2002
    chi_sps = np.arange(1, 5) * chi_sd
    plt.plot(old_div(Bcr, Bc), Mrat, 'r-')
    if 'names' in list(kwargs.keys()):
        names = kwargs['names']
        for k in range(len(names)):
            plt.text(BcrBc[k], S[k], names[k])  # ,'ha'='left'


#
def plot_s_bc(fignum, Bc, S, sym):
    """
    function to plot Squareness,Coercivity

    Parameters
    __________
    fignum : matplotlib figure number
    Bc : list or array coercivity values
    S : list or array of ratio of saturation remanence to saturation
    sym : matplotlib symbol (e.g., 'g^' for green triangles)
    """
    plt.figure(num=fignum)
    plt.plot(Bc, S, sym)
    plt.xlabel('Bc')
    plt.ylabel('Mr/Ms')
    plt.title('Squareness-Coercivity Plot')
    bounds = plt.axis()
    plt.axis([0, bounds[1], 0, 1])
#


def plot_s_bcr(fignum, Bcr, S, sym):
    """
    function to plot Squareness,Coercivity of remanence

    Parameters
    __________
    fignum : matplotlib figure number
    Bcr : list or array coercivity of remenence values
    S : list or array of ratio of saturation remanence to saturation
    sym : matplotlib symbol (e.g., 'g^' for green triangles)
    """
    plt.figure(num=fignum)
    plt.plot(Bcr, S, sym)
    plt.xlabel('Bcr')
    plt.ylabel('Mr/Ms')
    plt.title('Squareness-Bcr Plot')
    bounds = plt.axis()
    plt.axis([0, bounds[1], 0, 1])
#


def plot_bcr(fignum, Bcr1, Bcr2):
    """
    function to plot two estimates of Bcr against each other
    """
    plt.figure(num=fignum)
    plt.plot(Bcr1, Bcr2, 'ro')
    plt.xlabel('Bcr1')
    plt.ylabel('Bcr2')
    plt.title('Compare coercivity of remanence')


def plot_hpars(HDD, hpars, sym):
    """
    function to plot hysteresis parameters
    deprecated (used in hysteresis_magic)
    """
    plt.figure(num=HDD['hyst'])
    X, Y = [], []
    X.append(0)
    Y.append(old_div(float(hpars['hysteresis_mr_moment']), float(
        hpars['hysteresis_ms_moment'])))
    X.append(float(hpars['hysteresis_bc']))
    Y.append(0)
    plt.plot(X, Y, sym)
    bounds = plt.axis()
    n4 = 'Ms: ' + '%8.2e' % (float(hpars['hysteresis_ms_moment'])) + ' Am^2'
    plt.text(bounds[1] - .9 * bounds[1], -.9, n4)
    n1 = 'Mr: ' + '%8.2e' % (float(hpars['hysteresis_mr_moment'])) + ' Am^2'
    plt.text(bounds[1] - .9 * bounds[1], -.7, n1)
    n2 = 'Bc: ' + '%8.2e' % (float(hpars['hysteresis_bc'])) + ' T'
    plt.text(bounds[1] - .9 * bounds[1], -.5, n2)
    if 'hysteresis_xhf' in list(hpars.keys()):
        n3 = r'Xhf: ' + '%8.2e' % (float(hpars['hysteresis_xhf'])) + ' m^3'
        plt.text(bounds[1] - .9 * bounds[1], -.3, n3)
    plt.figure(num=HDD['deltaM'])
    X, Y, Bcr = [], [], ""
    if 'hysteresis_bcr' in list(hpars.keys()):
        X.append(float(hpars['hysteresis_bcr']))
        Y.append(0)
        Bcr = float(hpars['hysteresis_bcr'])
    plt.plot(X, Y, sym)
    bounds = plt.axis()
    if Bcr != "":
        n1 = 'Bcr: ' + '%8.2e' % (Bcr) + ' T'
        plt.text(bounds[1] - .5 * bounds[1], .9 * bounds[3], n1)
#


def plot_irm(fignum, B, M, title):
    """
    function to plot IRM backfield curves

    Parameters
    _________
    fignum : matplotlib figure number
    B : list or array of field values
    M : list or array of magnetizations
    title : string title for plot
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
        poly = np.polyfit(X, Y, 1)
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
        plt.figure(num=fignum)
        plt.clf()
        if not isServer:
            plt.figtext(.02, .01, version_num)
        plt.plot(B, Mnorm)
        plt.axhline(0, color='k')
        plt.axvline(0, color='k')
        plt.xlabel('B (T)')
        plt.ylabel('M/Mr')
        plt.title(title)
        if backfield == 1:
            plt.scatter([bcr], [0], marker='s', c='b')
            bounds = plt.axis()
            n1 = 'Bcr: ' + '%8.2e' % (-bcr) + ' T'
            plt.figtext(.2, .5, n1)
            n2 = 'Mr: ' + '%8.2e' % (M[0]) + ' Am^2'
            plt.figtext(.2, .45, n2)
    elif fignum != 0:
        plt.figure(num=fignum)
        # plt.clf()
        if not isServer:
            plt.figtext(.02, .01, version_num)
        print('M[0]=0,  skipping specimen')
    return rpars


def plot_xtf(fignum, XTF, Fs, e, b):
    """
    function to plot series of chi measurements as a function of temperature, holding field constant and varying frequency
    """
    plt.figure(num=fignum)
    plt.xlabel('Temperature (K)')
    plt.ylabel('Susceptibility (m^3/kg)')
    k = 0
    Flab = []
    for freq in XTF:
        T, X = [], []
        for xt in freq:
            X.append(xt[0])
            T.append(xt[1])
        plt.plot(T, X)
        plt.text(T[-1], X[-1], str(int(Fs[k])) + ' Hz')
#        Flab.append(str(int(Fs[k]))+' Hz')
        k += 1
    plt.title(e + ': B = ' + '%8.1e' % (b) + ' T')
#    plt.legend(Flab,'upper left')
#


def plot_xtb(fignum, XTB, Bs, e, f):
    """ function to plot series of chi measurements as a function of temperature, holding frequency constant and varying B
    """
    plt.figure(num=fignum)
    plt.xlabel('Temperature (K)')
    plt.ylabel('Susceptibility (m^3/kg)')
    k = 0
    Blab = []
    for field in XTB:
        T, X = [], []
        for xt in field:
            X.append(xt[0])
            T.append(xt[1])
        plt.plot(T, X)
        plt.text(T[-1], X[-1], '%8.2e' % (Bs[k]) + ' T')
#        Blab.append('%8.1e'%(Bs[k])+' T')
        k += 1
    plt.title(e + ': f = ' + '%i' % (int(f)) + ' Hz')
#    plt.legend(Blab,'upper left')
#


def plot_xft(fignum, XF, T, e, b):
    """ function to plot series of chi measurements as a function of temperature, holding field constant and varying frequency
    """
    plt.figure(num=fignum)
    plt.clf()
    if not isServer:
        plt.figtext(.02, .01, version_num)
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Susceptibility (m^3/kg)')
    k = 0
    F, X = [], []
    for xf in XF:
        X.append(xf[0])
        F.append(xf[1])
    plt.plot(F, X)
    plt.semilogx()
    plt.title(e + ': B = ' + '%8.1e' % (b) + ' T')

    plt.legend(['%i' % (int(T)) + ' K'])
#


def plot_xbt(fignum, XB, T, e, b):
    """ function to plot series of chi measurements as a function of temperature, holding field constant and varying frequency
    """
    plt.figure(num=fignum)
    plt.clf()
    if not isServer:
        plt.figtext(.02, .01, version_num)
    plt.xlabel('Field (T)')
    plt.ylabel('Susceptibility (m^3/kg)')
    k = 0
    B, X = [], []
    for xb in XB:
        X.append(xb[0])
        B.append(xb[1])
    plt.plot(B, X)
    plt.legend(['%i' % (int(T)) + ' K'])
    plt.title(e + ': f = ' + '%i' % (int(f)) + ' Hz')
#


def plot_ltc(LTC_CM, LTC_CT, LTC_WM, LTC_WT, e):
    """
    function to plot low temperature cycling experiments
    """
    leglist, init = [], 0
    if len(LTC_CM) > 2:
        if init == 0:
            plot_init(1, 5, 5)
        plt.plot(LTC_CT, LTC_CM, 'b')
        leglist.append('RT SIRM, measured while cooling')
        init = 1
    if len(LTC_WM) > 2:
        if init == 0:
            plot_init(1, 5, 5)
        plt.plot(LTC_WT, LTC_WM, 'r')
        leglist.append('RT SIRM, measured while warming')
    if init != 0:
        plt.legend(leglist, 'lower left')
        plt.xlabel('Temperature (K)')
        plt.ylabel('Magnetization (Am^2/kg)')
        if len(LTC_CM) > 2:
            plt.plot(LTC_CT, LTC_CM, 'bo')
        if len(LTC_WM) > 2:
            plt.plot(LTC_WT, LTC_WM, 'ro')
        plt.title(e)


def plot_anis(ANIS, Ss, iboot, ihext, ivec, ipar, title, plot, comp, vec, Dir, nb):
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
    if plot == 1:
        for key in list(ANIS.keys()):
            plt.figure(num=ANIS[key])
            plt.clf()
            if not isServer:
                plt.figtext(.02, .01, version_num)
        plot_net(ANIS['data'])  # draw the net
        plot_evec(ANIS['data'], Vs, 40, title)  # put on the data eigenvectors
#
# plot mean eigenvectors
#
    Vs = []
    mtau, mV = pmag.doseigs(avs)
    Vs.append(mV)
    hpars = pmag.dohext(nf, sigma, avs)
    if plot == 1:
        title = ''
        if ihext == 1:
            title = title + "Hext"
        if iboot == 1:
            title = title + ":Bootstrap"
        if ipar == 1:
            title = title + ":Parametric"
        if title[0] == ":":
            title = title[1:]
        plot_net(ANIS['conf'])  # draw the net
        plot_evec(ANIS['conf'], Vs, 36, title)  # put on the mean eigenvectors
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
        if plot == 1:
            if ivec == 1:
                # put on the data eigenvectors
                plot_evec(ANIS['conf'], BVs, 5, '')
            else:
                ellpars = [hpars["v1_dec"], hpars["v1_inc"], bpars["v1_zeta"], bpars["v1_zeta_dec"],
                           bpars["v1_zeta_inc"], bpars["v1_eta"], bpars["v1_eta_dec"], bpars["v1_eta_inc"]]
                plot_ell(ANIS['conf'], ellpars, 'r-,', 1, 1)
                ellpars = [hpars["v2_dec"], hpars["v2_inc"], bpars["v2_zeta"], bpars["v2_zeta_dec"],
                           bpars["v2_zeta_inc"], bpars["v2_eta"], bpars["v2_eta_dec"], bpars["v2_eta_inc"]]
                plot_ell(ANIS['conf'], ellpars, 'b-,', 1, 1)
                ellpars = [hpars["v3_dec"], hpars["v3_inc"], bpars["v3_zeta"], bpars["v3_zeta_dec"],
                           bpars["v3_zeta_inc"], bpars["v3_eta"], bpars["v3_eta_dec"], bpars["v3_eta_inc"]]
                plot_ell(ANIS['conf'], ellpars, 'k-,', 1, 1)
            plt.figure(num=ANIS['tcdf'])
            plt.clf()
            if not isServer:
                plt.figtext(.02, .01, version_num)
            ts = []
            for t in Taus:
                ts.append(t[0])
            plot_cdf(ANIS['tcdf'], ts, "", 'r', "")
            ts.sort()
            tminind = int(0.025 * len(ts))
            tmaxind = int(0.975 * len(ts))
            tbounds = []
            tbounds.append(ts[tminind])
            tbounds.append(ts[tmaxind])
            plt.axvline(x=tbounds[0], linewidth=1, color='r', linestyle='--')
            plt.axvline(x=tbounds[1], linewidth=1, color='r', linestyle='--')
            # plot_vs(ANIS['tcdf'],tbounds,'r','-') # there is some bug in here
            # - can't figure it out
            ts = []
            for t in Taus:
                ts.append(t[1])
            plot_cdf(ANIS['tcdf'], ts, "", 'b', "")
            ts.sort()
            tminind = int(0.025 * len(ts))
            tmaxind = int(0.975 * len(ts))
            tbounds = []
            tbounds.append(ts[tminind])
            tbounds.append(ts[tmaxind])
            # plot_vs(ANIS['tcdf'],tbounds,'b','-')
            plt.axvline(x=tbounds[0], linewidth=1, color='b', linestyle='-.')
            plt.axvline(x=tbounds[1], linewidth=1, color='b', linestyle='-.')
            ts = []
            for t in Taus:
                ts.append(t[2])
            plot_cdf(ANIS['tcdf'], ts, "Eigenvalues", 'k', "")
            ts.sort()
            tminind = int(0.025 * len(ts))
            tmaxind = int(0.975 * len(ts))
            tbounds = []
            tbounds.append(ts[tminind])
            tbounds.append(ts[tmaxind])
            plot_vs(ANIS['tcdf'], tbounds, 'k', '-')
            plt.axvline(x=tbounds[0], linewidth=1, color='k', linestyle='-')
            plt.axvline(x=tbounds[1], linewidth=1, color='k', linestyle='-')
            if comp == 1:  # do eigenvector of choice
                plt.figure(num=ANIS['conf'])
                XY = pmag.dimap(Dir[0], Dir[1])
                plt.scatter([XY[0]], [XY[1]], marker='p', c='m', s=100)
                Ccart = pmag.dir2cart(Dir)
                Vxs, Vys, Vzs = [], [], []
                for v in BVs:
                    cart = pmag.dir2cart([v[vec][0], v[vec][1], 1.])
                    Vxs.append(cart[0])
                    Vys.append(cart[1])
                    Vzs.append(cart[2])
                plt.figure(num=ANIS['vxcdf'])
                plt.clf()
                if not isServer:
                    plt.figtext(.02, .01, version_num)
                plot_cdf(ANIS['vxcdf'], Vxs, "V_" +
                         str(vec + 1) + "1", 'r', "")
                Vxs.sort()
                vminind = int(0.025 * len(Vxs))
                vmaxind = int(0.975 * len(Vxs))
                vbounds = []
                vbounds.append(Vxs[vminind])
                vbounds.append(Vxs[vmaxind])
                plt.axvline(x=vbounds[0], linewidth=1,
                            color='r', linestyle='--')
                plt.axvline(x=vbounds[1], linewidth=1,
                            color='r', linestyle='--')
                # plot_vs(ANIS['vxcdf'],vbounds,'r','--')
                # plot_vs(ANIS['vxcdf'],[Ccart[0]],'r','-')
                plt.axvline(x=Ccart[0][0], linewidth=1,
                            color='r', linestyle='-')
                plot_cdf(ANIS['vycdf'], Vys, "V_" +
                         str(vec + 1) + "2", 'b', "")
                Vys.sort()
                vminind = int(0.025 * len(Vys))
                vmaxind = int(0.975 * len(Vys))
                vbounds = []
                vbounds.append(Vys[vminind])
                vbounds.append(Vys[vmaxind])
                plt.axvline(x=vbounds[0], linewidth=1,
                            color='b', linestyle='--')
                plt.axvline(x=vbounds[1], linewidth=1,
                            color='b', linestyle='--')
                plt.axvline(x=Ccart[0][1], linewidth=1,
                            color='b', linestyle='-')
                # plot_vs(ANIS['vycdf'],vbounds,'b','--')
                # plot_vs(ANIS['vycdf'],[Ccart[1]],'b','-')
                plot_cdf(ANIS['vzcdf'], Vzs, "V_" +
                         str(vec + 1) + "3", 'k', "")
                Vzs.sort()
                vminind = int(0.025 * len(Vzs))
                vmaxind = int(0.975 * len(Vzs))
                vbounds = []
                vbounds.append(Vzs[vminind])
                vbounds.append(Vzs[vmaxind])
                plt.axvline(x=vbounds[0], linewidth=1,
                            color='k', linestyle='--')
                plt.axvline(x=vbounds[1], linewidth=1,
                            color='k', linestyle='--')
                plt.axvline(x=Ccart[0][2], linewidth=1,
                            color='k', linestyle='-')
                # plot_vs(ANIS['vzcdf'],vbounds,'k','--')
                # plot_vs(ANIS['vzcdf'],[Ccart[2]],'k','-')
        bpars['v1_dec'] = hpars['v1_dec']
        bpars['v2_dec'] = hpars['v2_dec']
        bpars['v3_dec'] = hpars['v3_dec']
        bpars['v1_inc'] = hpars['v1_inc']
        bpars['v2_inc'] = hpars['v2_inc']
        bpars['v3_inc'] = hpars['v3_inc']
    if ihext == 1 and plot == 1:
        ellpars = [hpars["v1_dec"], hpars["v1_inc"], hpars["e12"], hpars["v2_dec"],
                   hpars["v2_inc"], hpars["e13"], hpars["v3_dec"], hpars["v3_inc"]]
        plot_ell(ANIS['conf'], ellpars, 'r-,', 1, 1)
        ellpars = [hpars["v2_dec"], hpars["v2_inc"], hpars["e23"], hpars["v3_dec"],
                   hpars["v3_inc"], hpars["e12"], hpars["v1_dec"], hpars["v1_inc"]]
        plot_ell(ANIS['conf'], ellpars, 'b-,', 1, 1)
        ellpars = [hpars["v3_dec"], hpars["v3_inc"], hpars["e13"], hpars["v1_dec"],
                   hpars["v1_inc"], hpars["e23"], hpars["v2_dec"], hpars["v2_inc"]]
        plot_ell(ANIS['conf'], ellpars, 'k-,', 1, 1)
    return bpars, hpars
####


def plot_trm(fig, B, TRM, Bp, Mp, NLpars, title):
    #
    # plots TRM acquisition data and correction to B_estimated to B_ancient
    plt.figure(num=fig)
    plt.clf()
    if not isServer:
        plt.figtext(.02, .01, version_num)
    plt.xlabel('B (uT)')
    plt.ylabel('Fractional TRM ')
    plt.title(title + ':TRM=' + '%8.2e' % (Mp[-1]))
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
    plt.plot(Bnorm, Tnorm, 'go')
    plt.plot(Bpnorm, Mnorm, 'g-')
    if NLpars['banc'] > 0:
        plt.plot([0, NLpars['best'] * 1e6],
                 [0, old_div(NLpars['banc_npred'], Mp[-1])], 'b--')
        plt.plot([NLpars['best'] * 1e6, NLpars['banc'] * 1e6], [old_div(
            NLpars['banc_npred'], Mp[-1]), old_div(NLpars['banc_npred'], Mp[-1])], 'r--')
        plt.plot([NLpars['best'] * 1e6],
                 [old_div(NLpars['banc_npred'], Mp[-1])], 'bd')
        plt.plot([NLpars['banc'] * 1e6],
                 [old_div(NLpars['banc_npred'], Mp[-1])], 'rs')
    else:
        plt.plot([0, NLpars['best'] * 1e6],
                 [0, old_div(NLpars['best_npred'], Mp[-1])], 'b--')
        plt.plot([0, NLpars['best'] * 1e6],
                 [0, old_div(NLpars['best_npred'], Mp[-1])], 'bd')

###


def plot_tds(fig, tdsblock, title):
    plt.figure(num=fig)
    plt.clf()
    if not isServer:
        plt.figtext(.02, .01, version_num)
    plt.xlabel('Fraction TRM remaining')
    plt.ylabel('Fraction NRM remaining')
    plt.title(title)
    X, Y = [], []
    for rec in tdsblock:
        X.append(rec[2])  # TRM on X
        Y.append(rec[1])  # NRM on Y
        plt.text(X[-1], Y[-1], ' %3.1f' % (float(rec[0]) - 273))
    plt.plot(X, Y, 'ro')
    plt.plot(X, Y)


def plot_conf(fignum, s, datablock, pars, new):
    """
    plots directions and confidence ellipses
    """
# make the stereonet
    if new == 1:
        plot_net(fignum)
#
#   plot the data
#
    DIblock = []
    for plotrec in datablock:
        DIblock.append((float(plotrec["dec"]), float(plotrec["inc"])))
    if len(DIblock) > 0:
        plot_di(fignum, DIblock)  # plot directed lines
#
# put on the mean direction
#
    x, y = [], []
    XY = pmag.dimap(float(pars[0]), float(pars[1]))
    x.append(XY[0])
    y.append(XY[1])
    plt.figure(num=fignum)
    if new == 1:
        plt.scatter(x, y, marker='d', s=80, c='r')
    else:
        if float(pars[1] > 0):
            plt.scatter(x, y, marker='^', s=100, c='r')
        else:
            plt.scatter(x, y, marker='^', s=100, c='y')
    plt.title(s)
#
# plot the ellipse
#
    plot_ell(fignum, pars, 'r-,', 0, 1)


EI_plot_num = 0
maxE, minE, maxI, minI = 0, 10, 0, 90


def plot_ei(fignum, E, I, f):
    global EI_plot_num, maxE, minE, minI, maxI
    plt.figure(num=fignum)
    if EI_plot_num == 0:
        plt.plot(I, E, 'r')
        plt.xlabel("Inclination")
        plt.ylabel("Elongation")
        EI_plot_num += 1
        plt.text(I[-1], E[-1], ' %4.2f' % (f))
        plt.text(I[0] - 2, E[0], ' %s' % ('f=1'))
    elif f == 1:
        plt.plot(I, E, 'g-')
    else:
        plt.plot(I, E, 'y')


def plot_v2s(fignum, V2s, I, f):
    plt.figure(num=fignum)
    plt.plot(I, V2s, 'r')
    plt.xlabel("Inclination")
    plt.ylabel("Elongation direction")


def plot_com(CDF, BDI1, BDI2, d):
    #
    #   convert to cartesian coordinates X1,X2, Y1,Y2 and Z1, Z2
    #
    cart = pmag.dir2cart(BDI1).transpose()
    X1, Y1, Z1 = cart[0], cart[1], cart[2]
    min = int(0.025 * len(X1))
    max = int(0.975 * len(X1))
    X1, y = plot_cdf(CDF['X'], X1, "X component", 'r', "")
    bounds1 = [X1[min], X1[max]]
    plot_vs(CDF['X'], bounds1, 'r', '-')
    Y1, y = plot_cdf(CDF['Y'], Y1, "Y component", 'r', "")
    bounds1 = [Y1[min], Y1[max]]
    plot_vs(CDF['Y'], bounds1, 'r', '-')
    Z1, y = plot_cdf(CDF['Z'], Z1, "Z component", 'r', "")
    bounds1 = [Z1[min], Z1[max]]
    plot_vs(CDF['Z'], bounds1, 'r', '-')
    # draw_figs(CDF)
    if d[0] == "":  # repeat for second data set
        bounds2 = []
        cart = pmag.dir2cart(BDI2).transpose()
        X2, Y2, Z2 = cart[0], cart[1], cart[2]
        X2, y = plot_cdf(CDF['X'], X2, "X component", 'b', "")
        bounds2 = [X2[min], X2[max]]
        plot_vs(CDF['X'], bounds2, 'b', '--')
        Y2, y = plot_cdf(CDF['Y'], Y2, "Y component", 'b', "")
        bounds2 = [Y2[min], Y2[max]]
        plot_vs(CDF['Y'], bounds2, 'b', '--')
        Z2, y = plot_cdf(CDF['Z'], Z2, "Z component", 'b', "")
        bounds2 = [Z2[min], Z2[max]]
        plot_vs(CDF['Z'], bounds2, 'b', '--')
    else:
        cart = pmag.dir2cart([d[0], d[1], 1.0])
        plot_vs(CDF['X'], [cart[0]], 'k', '--')
        plot_vs(CDF['Y'], [cart[1]], 'k', '--')
        plot_vs(CDF['Z'], [cart[2]], 'k', '--')
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


def add_borders(Figs, titles, border_color='#000000', text_color='#800080', con_id=""):

    """
    Formatting for generating plots on the server
    Default border color: black
    Default text color: purple
    """
    def split_title(s):
        """
        Add '\n's to split of overly long titles
        """
        s_list = s.split(",")
        lines = []
        tot = 0
        line = []
        for i in s_list:
            tot += len(i)
            if tot < 30:
                line.append(i + ",")
            else:
                lines.append(" ".join(line))
                line = [i]
                tot = 0
        lines.append(" ".join(line))
        return "\n".join(lines).strip(',')

    # format contribution id if available
    if con_id:
        if not str(con_id).startswith("/"):
            con_id = "/" + str(con_id)

    import datetime
    now = datetime.datetime.utcnow()

    for key in list(Figs.keys()):

        fig = plt.figure(Figs[key])
        plot_title = split_title(titles[key]).strip().strip('\n')
        fig.set_figheight(5.5)
        #get returns Bbox with x0, y0, x1, y1
        pos = fig.gca().get_position()
        # tweak some of the default values
        w = pos.x1 - pos.x0
        h = (pos.y1 - pos.y0) / 1.1
        x = pos.x0
        y = pos.y0 * 1.3
        # set takes: left, bottom, width, height
        fig.gca().set_position([x, y, w, h])

        # add an axis covering the entire figure
        border_ax = fig.add_axes([0, 0, 1, 1])
        border_ax.set_frame_on(False)
        border_ax.set_xticks([])
        border_ax.set_yticks([])
        # add a border
        if "\n" in plot_title:
            y_val = 1.0  # lower border
            #fig.set_figheight(6.25)
        else:
            y_val = 1.04  # higher border
        #border_ax.text(-0.02, y_val, "                                                                                                   #                                                                                      |",
        #               horizontalalignment='left',
        #               verticalalignment='top',
        #               color=text_color,
        #               bbox=dict(edgecolor=border_color,
        #                         facecolor='#FFFFFF', linewidth=0.25),
        #               size=50)
        #border_ax.text(-0.02, 0, "|                                                                                                      #                                                                                   |",
        #               horizontalalignment='left',
        #               verticalalignment='bottom',
        #               color=text_color,
        #               bbox=dict(edgecolor=border_color,
        #                         facecolor='#FFFFFF', linewidth=0.25),
        #               size=20)#18)

        # add text

        border_ax.text((4. / fig.get_figwidth()) * 0.015, 0.03, now.strftime("%Y-%m-%d, %I:%M:%S {}".format('UT')),
                       horizontalalignment='left',
                       verticalalignment='top',
                       color=text_color,
                       size=10)
        border_ax.text(0.5, 0.98, plot_title,
                       horizontalalignment='center',
                       verticalalignment='top',
                       color=text_color,
                       size=20)
        border_ax.text(1 - (4. / fig.get_figwidth()) * 0.015, 0.03, 'earthref.org/MagIC{}'.format(con_id),
                       horizontalalignment='right',
                       verticalalignment='top',
                       color=text_color,
                       size=10)
    return Figs


def plot_map_basemap(fignum, lats, lons, Opts):
    """
    plot_map_basemap(fignum, lats,lons,Opts)
    makes a basemap with lats/lons
        requires working installation of Basemap
    Parameters:
    _______________
    fignum : matplotlib figure number
    lats : array or list of latitudes
    lons : array or list of longitudes
    Opts : dictionary of plotting options:
        Opts.keys=
            latmin : minimum latitude for plot
            latmax : maximum latitude for plot
            lonmin : minimum longitude for plot
            lonmax : maximum longitude
            lat_0 : central latitude
            lon_0 : central longitude
            proj : projection [basemap projections, e.g., moll=Mollweide, merc=Mercator, ortho=orthorhombic,
                lcc=Lambert Conformal]
            sym : matplotlib symbol
            symsize : symbol size in pts
            edge : markeredgecolor
            pltgrid : plot the grid [1,0]
            res :  resolution [c,l,i,h] for crude, low, intermediate, high
            boundinglat : bounding latitude
            sym : matplotlib symbol for plotting
            symsize : matplotlib symbol size for plotting
            names : list of names for lats/lons (if empty, none will be plotted)
            pltgrd : if True, put on grid lines
            padlat : padding of latitudes
            padlon : padding of longitudes
            gridspace : grid line spacing
            details : dictionary with keys:
                coasts : if True, plot coastlines
                rivers : if True, plot rivers
                states : if True, plot states
                countries : if True, plot countries
                ocean : if True, plot ocean
                fancy : if True, plot etopo 20 grid
                    NB:  etopo must be installed
        if Opts keys not set :these are the defaults:
           Opts={'latmin':-90,'latmax':90,'lonmin':0,'lonmax':360,'lat_0':0,'lon_0':0,'proj':'moll','sym':'ro,'symsize':5,'pltgrid':1,'res':'c','boundinglat':0.,'padlon':0,'padlat':0,'gridspace':30,'details':all False,'edge':None}

    """
    if not has_basemap:
        print('-W- Basemap must be installed to run plot_map_basemap')
        return
    fig = plt.figure(num=fignum)
    rgba_land = (255, 255, 150, 255)
    rgba_ocean = (200, 250, 255, 255)
    ExMer = ['sinus', 'moll', 'lcc']
    # draw meridian labels on the bottom [left,right,top,bottom]
    mlabels = [0, 0, 0, 1]
    plabels = [1, 0, 0, 0]  # draw parallel labels on the left
    # set default Options
    Opts_defaults = {'latmin': -90, 'latmax': 90, 'lonmin': 0, 'lonmax': 360,
                     'lat_0': 0, 'lon_0': 0, 'proj': 'moll', 'sym': 'ro', 'symsize': 5,
                     'edge': None, 'pltgrid': 1, 'res': 'c', 'boundinglat': 0.,
                     'padlon': 0, 'padlat': 0, 'gridspace': 30,
                     'details': {'fancy': 0, 'coasts': 0, 'rivers': 0, 'states': 0, 'countries': 0, 'ocean': 0}}
    for key in Opts_defaults.keys():
        if key not in Opts.keys() and key != 'details':
            Opts[key] = Opts_defaults[key]
        if key == 'details':
            if key not in Opts.keys():
                Opts[key] = Opts_defaults[key]
            for detail_key in Opts_defaults[key].keys():
                if detail_key not in Opts[key].keys():
                    Opts[key][detail_key] = Opts_defaults[key][detail_key]

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
            from mpl_toolkits.basemap import basemap_datadir
            EDIR = basemap_datadir + "/"
            etopo = np.loadtxt(EDIR + 'etopo20data.gz')
            elons = np.loadtxt(EDIR + 'etopo20lons.gz')
            elats = np.loadtxt(EDIR + 'etopo20lats.gz')
            x, y = m(*np.meshgrid(elons, elats))
            cs = m.contourf(x, y, etopo, 30, cmap=color_map.jet)
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
        circles = np.arange(Opts['latmin'], Opts['latmax'] + 15., 15.)
        meridians = np.arange(Opts['lonmin'], Opts['lonmax'] + 30., 30.)
    elif Opts['pltgrid'] > 0:
        if Opts['proj'] in ExMer or Opts['proj'] == 'lcc':
            circles = np.arange(-90, 180. +
                                Opts['gridspace'], Opts['gridspace'])
            meridians = np.arange(0, 360., Opts['gridspace'])
        else:
            g = Opts['gridspace']
            latmin, lonmin = g * \
                int(old_div(Opts['latmin'], g)), g * \
                int(old_div(Opts['lonmin'], g))
            latmax, lonmax = g * \
                int(old_div(Opts['latmax'], g)), g * \
                int(old_div(Opts['lonmax'], g))
            # circles=np.arange(latmin-2.*Opts['padlat'],latmax+2.*Opts['padlat'],Opts['gridspace'])
            # meridians=np.arange(lonmin-2.*Opts['padlon'],lonmax+2.*Opts['padlon'],Opts['gridspace'])
            meridians = np.arange(0, 360, 30)
            circles = np.arange(-90, 90, 30)
    if Opts['pltgrid'] >= 0:
        # m.drawparallels(circles,color='black',labels=plabels)
        # m.drawmeridians(meridians,color='black',labels=mlabels)
        # skip the labels - they are ugly
        m.drawparallels(circles, color='black')
        # skip the labels - they are ugly
        m.drawmeridians(meridians, color='black')
        m.drawmapboundary()
    prn_name, symsize = 0, 5
    if 'names' in Opts.keys() and len(Opts['names']) > 0:
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
                T.append(plt.text(X[pt] + 5000, Y[pt] - 5000, names[pt]))
        m.plot(X, Y, Opts['sym'], markersize=symsize,
               markeredgecolor=Opts['edge'])
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
                    T.append(plt.text(x + 5000, y - 5000, names[k]))
                k += 1
            else:  # need to skip 100.0s and move to next chunk
                # plot previous chunk
                m.plot(X, Y, Opts['sym'], markersize=symsize,
                       markeredgecolor=Opts['edge'])
                chunk += 1
                while lats[k] > 90. and k < len(lats) - 1:
                    k += 1  # skip bad points
                X, Y, T = [], [], []
        if len(X) > 0:
            m.plot(X, Y, Opts['sym'], markersize=symsize,
                   markeredgecolor=Opts['edge'])  # plot last chunk


def plot_map(fignum, lats, lons, Opts):
    """
    makes a cartopy map  with lats/lons
    Requires installation of cartopy

    Parameters:
    _______________
    fignum : matplotlib figure number
    lats : array or list of latitudes
    lons : array or list of longitudes
    Opts : dictionary of plotting options:
        Opts.keys=
            proj : projection [supported cartopy projections:
                pc = Plate Carree
                aea = Albers Equal Area
                aeqd = Azimuthal Equidistant
                lcc = Lambert Conformal
                lcyl = Lambert Cylindrical
                merc = Mercator
                mill = Miller Cylindrical
                moll = Mollweide [default]
                ortho = Orthographic
                robin = Robinson
                sinu = Sinusoidal
                stere = Stereographic
                tmerc = Transverse Mercator
                utm = UTM [set zone and south keys in Opts]
                laea = Lambert Azimuthal Equal Area
                geos = Geostationary
                npstere = North-Polar Stereographic
                spstere = South-Polar Stereographic
            latmin : minimum latitude for plot
            latmax : maximum latitude for plot
            lonmin : minimum longitude for plot
            lonmax : maximum longitude
            lat_0 : central latitude
            lon_0 : central longitude
            sym : matplotlib symbol
            symsize : symbol size in pts
            edge : markeredgecolor
            cmap : matplotlib color map
            res :  resolution [c,l,i,h] for low/crude, intermediate, high
            boundinglat : bounding latitude
            sym : matplotlib symbol for plotting
            symsize : matplotlib symbol size for plotting
            names : list of names for lats/lons (if empty, none will be plotted)
            pltgrd : if True, put on grid lines
            padlat : padding of latitudes
            padlon : padding of longitudes
            gridspace : grid line spacing
            global : global projection [default is True]
            oceancolor : 'azure'
            landcolor : 'bisque' [choose any of the valid color names for matplotlib
              see https://matplotlib.org/examples/color/named_colors.html
            details : dictionary with keys:
                coasts : if True, plot coastlines
                rivers : if True, plot rivers
                states : if True, plot states
                countries : if True, plot countries
                ocean : if True, plot ocean
                lakes : if True, plot lakes
                fancy : if True, plot etopo 20 grid
                    NB:  etopo must be installed
        if Opts keys not set :these are the defaults:
           Opts={'latmin':-90,'latmax':90,'lonmin':0,'lonmax':360,'lat_0':0,'lon_0':0,'proj':'moll','sym':'ro,'symsize':5,'edge':'black','pltgrid':1,'res':'c','boundinglat':0.,'padlon':0,'padlat':0,'gridspace':30,'details':all False,'edge':None,'cmap':'jet','fancy':0,'zone':'','south':False,'oceancolor':'azure','landcolor':'bisque'}

    """
    if not has_cartopy:
        print('This function requires installation of cartopy')
        return
    from matplotlib import cm
    # draw meridian labels on the bottom [left,right,top,bottom]
    mlabels = [0, 0, 0, 1]
    plabels = [1, 0, 0, 0]  # draw parallel labels on the left
    Opts_defaults = {'latmin': -90, 'latmax': 90, 'lonmin': 0, 'lonmax': 360,
                     'lat_0': 0, 'lon_0': 0, 'proj': 'moll', 'sym': 'ro', 'symsize': 5,
                     'edge': None, 'pltgrid': 1, 'res': 'c', 'boundinglat': 0.,
                     'padlon': 0, 'padlat': 0, 'gridspace': 30, 'global': 1, 'cmap': 'jet','oceancolor':'azure','landcolor':'bisque',
                     'details': {'fancy': 0, 'coasts': 0, 'rivers': 0, 'states': 0, 'countries': 0, 'ocean': 0, 'lakes': 0},
                     'edgecolor': 'face'}
    for key in Opts_defaults.keys():
        if key not in Opts.keys() and key != 'details':
            Opts[key] = Opts_defaults[key]
        if key == 'details':
            if key not in Opts.keys():
                Opts[key] = Opts_defaults[key]
            for detail_key in Opts_defaults[key].keys():
                if detail_key not in Opts[key].keys():
                    Opts[key][detail_key] = Opts_defaults[key][detail_key]
    if Opts['proj'] == 'pc':
        ax = plt.axes(projection=ccrs.PlateCarree())
        ax.set_extent([Opts['lonmin'], Opts['lonmax'], Opts['latmin'], Opts['latmax']],
                      crs=ccrs.PlateCarree())
    if Opts['proj'] == 'aea':
        ax = plt.axes(projection=ccrs.AlbersEqualArea(
            central_longitude=Opts['lon_0'],
            central_latitude=Opts['lat_0'],
            false_easting=0.0, false_northing=0.0, standard_parallels=(20.0, 50.0),
            globe=None))
    if Opts['proj'] == 'lcc':
        proj = ccrs.LambertConformal(central_longitude=Opts['lon_0'],  central_latitude=Opts['lat_0'],\
               false_easting=0.0, false_northing=0.0, standard_parallels=(20.0, 50.0),
               globe=None)
        fig=plt.figure(fignum,figsize=(6,6),frameon=True)
        ax = plt.axes(projection=proj)
        ax.set_extent([Opts['lonmin'], Opts['lonmax'], Opts['latmin'], Opts['latmax']],
                      crs=ccrs.PlateCarree())
    if Opts['proj'] == 'lcyl':
        ax = plt.axes(projection=ccrs.LambertCylindrical(
            central_longitude=Opts['lon_0']))

    if Opts['proj'] == 'merc':
        ax = plt.axes(projection=ccrs.Mercator(
            central_longitude=Opts['lon_0'], min_latitude=Opts['latmin'],
            max_latitude=Opts['latmax'], latitude_true_scale=0.0, globe=None))
        ax.set_extent([Opts['lonmin'],Opts['lonmax'],\
                     Opts['latmin'],Opts['latmax']])
    if Opts['proj'] == 'mill':
        ax = plt.axes(projection=ccrs.Miller(
            central_longitude=Opts['lon_0']))
    if Opts['proj'] == 'moll':
        ax = plt.axes(projection=ccrs.Mollweide(
            central_longitude=Opts['lat_0'], globe=None))
    if Opts['proj'] == 'ortho':
        ax = plt.axes(projection=ccrs.Orthographic(
            central_longitude=Opts['lon_0'],
            central_latitude=Opts['lat_0']))
    if Opts['proj'] == 'robin':
        ax = plt.axes(projection=ccrs.Robinson(
            central_longitude=Opts['lon_0'],
            globe=None))

    if Opts['proj'] == 'sinu':
        ax = plt.axes(projection=ccrs.Sinusoidal(
            central_longitude=Opts['lon_0'],
            false_easting=0.0, false_northing=0.0,
            globe=None))

    if Opts['proj'] == 'stere':
        ax = plt.axes(projection=ccrs.Stereographic(
            central_longitude=Opts['lon_0'],
            false_easting=0.0, false_northing=0.0,
            true_scale_latitude=None,
            scale_factor=None,
            globe=None))
    if Opts['proj'] == 'tmerc':
        ax = plt.axes(projection=ccrs.TransverseMercator(
            central_longitude=Opts['lon_0'], central_latitude=Opts['lat_0'],
            false_easting=0.0, false_northing=0.0,
            scale_factor=None,
            globe=None))
    if Opts['proj'] == 'utm':
        ax = plt.axes(projection=ccrs.UTM(
            zone=Opts['zone'],
            southern_hemisphere=Opts['south'],
            globe=None))
    if Opts['proj'] == 'geos':
        ax = plt.axes(projection=ccrs.Geostationary(
            central_longitude=Opts['lon_0'],
            false_easting=0.0, false_northing=0.0,
            satellite_height=35785831,
            sweep_axis='y',
            globe=None))
    if Opts['proj'] == 'laea':
        ax = plt.axes(projection=ccrs.LambertAzimuthalEqualArea(
            central_longitude=Opts['lon_0'], central_latitude=Opts['lat_0'],
            false_easting=0.0, false_northing=0.0,
            globe=None))
    if Opts['proj'] == 'npstere':
        ax = plt.axes(projection=ccrs.NorthPolarStereo(
            central_longitude=Opts['lon_0'],
            true_scale_latitude=None,
            globe=None))
    if Opts['proj'] == 'spstere':
        ax = plt.axes(projection=ccrs.SouthPolarStereo(
            central_longitude=Opts['lon_0'],
            true_scale_latitude=None,
            globe=None))

    if 'details' in list(Opts.keys()):
        if Opts['details']['fancy'] == 1:
            pmag_data_dir = find_pmag_dir.get_data_files_dir()
            EDIR = os.path.join(pmag_data_dir, "etopo20")
            etopo_path = os.path.join(EDIR, 'etopo20data.gz')
            etopo = np.loadtxt(os.path.join(EDIR, 'etopo20data.gz'))
            elons = np.loadtxt(os.path.join(EDIR, 'etopo20lons.gz'))
            elats = np.loadtxt(os.path.join(EDIR, 'etopo20lats.gz'))
            xx, yy = np.meshgrid(elons, elats)
            levels = np.arange(-10000, 8000, 500)  # define contour intervals
            m = ax.contourf(xx, yy, etopo, levels,
                            transform=ccrs.PlateCarree(),
                            cmap=Opts['cmap'])
            cbar=plt.colorbar(m)
        if Opts['res']=='c' or Opts['res']=='l':
            resolution='110m'
        elif Opts['res']=='i':
            resolution='50m'
        elif Opts['res']=='h':
            resolution='10m'
        if Opts['details']['coasts'] == 1:
            ax.coastlines(resolution=resolution)
        if Opts['details']['rivers'] == 1:
            ax.add_feature(cfeature.RIVERS)
        if Opts['details']['states'] == 1:
            states_provinces = cfeature.NaturalEarthFeature(
                category='cultural',
                name='admin_1_states_provinces_lines',
                scale=resolution,
                edgecolor='black',
                facecolor='none',
                linestyle='dotted')
            ax.add_feature(states_provinces)
        if Opts['details']['countries'] == 1:
            ax.add_feature(BORDERS.with_scale(resolution), linestyle='-', linewidth=2)
        if Opts['details']['ocean'] == 1:
            ax.add_feature(OCEAN.with_scale(resolution), color=Opts['oceancolor'])
            ax.add_feature(LAND.with_scale(resolution), color=Opts['landcolor'])
            ax.add_feature(LAKES.with_scale(resolution), color=Opts['oceancolor'])
    if Opts['proj'] in ['merc', 'pc','lcc','ortho']:
        if Opts['pltgrid']:
            if Opts['proj']=='lcc':
                fig.canvas.draw()
                #xticks=list(np.arange(Opts['lonmin'],Opts['lonmax']+Opts['gridspace'],Opts['gridspace']))
                #yticks=list(np.arange(Opts['latmin'],Opts['latmax']+Opts['gridspace'],Opts['gridspace']))
                xticks=list(np.arange(-180,180,Opts['gridspace']))
                yticks=list(np.arange(-90,90,Opts['gridspace']))
                ax.gridlines(ylocs=yticks,xlocs=xticks,linewidth=2,
                              linestyle='dotted')
                ax.xaxis.set_major_formatter(LONGITUDE_FORMATTER) # you need this here
                ax.yaxis.set_major_formatter(LATITUDE_FORMATTER)# you need this here, too

                try:
                    import pmagpy.lcc_ticks as lcc_ticks
                    lcc_ticks.lambert_xticks(ax, xticks)
                    lcc_ticks.lambert_yticks(ax, yticks)

                except:
                    print ('plotting of tick marks on Lambert Conformal requires the package "shapely".\n Try importing with "conda install -c conda-forge shapely"')
            else:
                if Opts['proj']=='ortho':
                    draw_labels=False
                else:
                    draw_labels=True
                gl = ax.gridlines(crs=ccrs.PlateCarree(), linewidth=2,
                              linestyle='dotted', draw_labels=draw_labels)
                gl.ylocator = mticker.FixedLocator(np.arange(-80, 81, Opts['gridspace']))
                gl.xlocator = mticker.FixedLocator(np.arange(-180, 181, Opts['gridspace']))
                gl.xformatter = LONGITUDE_FORMATTER
                gl.yformatter = LATITUDE_FORMATTER
                gl.xlabels_top = False
        #else:
        #    gl = ax.gridlines(crs=ccrs.PlateCarree(),
        #                      linewidth=2, linestyle='dotted')
    elif Opts['pltgrid']:
        print('gridlines only supported for PlateCarree, Orthorhombic, Lambert Conformal, and Mercator plots currently')
    prn_name, symsize = 0, 5
    # if 'names' in list(Opts.keys()) > 0:
    #    names = Opts['names']
    #    if len(names) > 0:
    #        prn_name = 1
##
    X, Y, T, k = [], [], [], 0
    if 'symsize' in list(Opts.keys()):
        symsize = Opts['symsize']
    if Opts['sym'][-1] != '-':  # just plot points
        color, symbol = Opts['sym'][0], Opts['sym'][1]
        ax.scatter(lons, lats, s=Opts['symsize'], c=color, marker=symbol,
                   transform=ccrs.PlateCarree(), edgecolors=Opts['edgecolor'])
        if prn_name == 1:
            print('labels not yet implemented in plot_map')
            # for pt in range(len(lats)):
            #    T.append(plt.text(X[pt] + 5000, Y[pt] - 5000, names[pt]))
    else:  # for lines,  need to separate chunks using lat==100.
        ax.plot(lons, lats, Opts['sym'], transform=ccrs.PlateCarree())
    if Opts['global']:
        ax.set_global()


def plot_mag_map_basemap(fignum, element, lons, lats, element_type, cmap='RdYlBu', lon_0=0, date=""):
    """
    makes a color contour map of geomagnetic field element

    Parameters
    ____________
    fignum : matplotlib figure number
    element : field element array from pmag.do_mag_map for plotting
    lons : longitude array from pmag.do_mag_map for plotting
    lats : latitude array from pmag.do_mag_map for plotting
    element_type : [B,Br,I,D] geomagnetic element type
        B : field intensity
        Br : radial field intensity
        I : inclinations
        D : declinations
    Optional
    _________
        cmap : matplotlib color map
        lon_0 : central longitude of the Hammer projection
        date : date used for field evaluation,
               if custom ghfile was used, supply filename


    Effects
    ______________
    plots a Hammer projection color contour with  the desired field element
    """
    if not has_basemap:
        print('-W- Basemap must be installed to run plot_mag_map_basemap')
        return
    from matplotlib import cm  # matplotlib's color map module
    lincr = 1
    if type(date) != str:
        date = str(date)
    fig = plt.figure(fignum)
    m = Basemap(projection='hammer', lon_0=lon_0)
    x, y = m(*meshgrid(lons, lats))
    m.drawcoastlines()
    if element_type == 'B':
        levmax = element.max()+lincr
        levmin = round(element.min()-lincr)
        levels = np.arange(levmin, levmax, lincr)
        cs = m.contourf(x, y, element, levels=levels, cmap=cmap)
        plt.title('Field strength ($\mu$T): '+date)
    if element_type == 'Br':
        levmax = element.max()+lincr
        levmin = round(element.min()-lincr)
        cs = m.contourf(x, y, element, levels=np.arange(
            levmin, levmax, lincr), cmap=cmap)
        plt.title('Radial field strength ($\mu$T): '+date)
    if element_type == 'I':
        levmax = element.max()+lincr
        levmin = round(element.min()-lincr)
        cs = m.contourf(
            x, y, element, levels=np.arange(-90, 100, 20), cmap=cmap)
        m.contour(x, y, element, levels=np.arange(-80, 90, 10), colors='black')
        plt.title('Field inclination: '+date)
    if element_type == 'D':
        # cs=m.contourf(x,y,element,levels=np.arange(-180,180,10),cmap=cmap)
        cs = m.contourf(
            x, y, element, levels=np.arange(-180, 180, 10), cmap=cmap)
        m.contour(x, y, element, levels=np.arange(-180, 180, 10), colors='black')
        plt.title('Field declination: '+date)
    cbar = m.colorbar(cs, location='bottom')


def plot_mag_map(fignum, element, lons, lats, element_type, cmap='coolwarm', lon_0=0, date="", contours=False, proj='PlateCarree', min=False,max=False):
    """
    makes a color contour map of geomagnetic field element

    Parameters
    ____________
    fignum : matplotlib figure number
    element : field element array from pmag.do_mag_map for plotting
    lons : longitude array from pmag.do_mag_map for plotting
    lats : latitude array from pmag.do_mag_map for plotting
    element_type : [B,Br,I,D] geomagnetic element type
        B : field intensity
        Br : radial field intensity
        I : inclinations
        D : declinations
    Optional
    _________
    contours : plot the contour lines on top of the heat map if True
    proj : cartopy projection ['PlateCarree','Mollweide']
           NB: The Mollweide projection can only be reliably with cartopy=0.17.0; otherwise use lon_0=0.  Also, for declinations, PlateCarree is recommended.
    cmap : matplotlib color map - see https://matplotlib.org/examples/color/colormaps_reference.html for options
    lon_0 : central longitude of the Mollweide projection
    date : date used for field evaluation,
           if custom ghfile was used, supply filename
    min : int
        minimum value for color contour on intensity map : default is minimum value  - useful for making many maps with same scale
    max : int
        maximum value for color contour on intensity map : default is maximum value - useful for making many maps with same scale

    Effects
    ______________
    plots a color contour map with  the desired field element
    """

    if not has_cartopy:
        print('This function requires installation of cartopy')
        return
    from matplotlib import cm
    if lon_0 == 180:
        lon_0 = 179.99
    if lon_0 > 180:
        lon_0 = lon_0-360.
    lincr = 1
    if type(date) != str:
        date = str(date)
    if proj == 'PlateCarree':
        fig = plt.figure(fignum)
        ax = plt.axes(projection=ccrs.PlateCarree(central_longitude=lon_0))
    if proj == 'Mollweide':
        fig = plt.figure(fignum)
        # this issue is fixed in >=0.17
        if not LooseVersion(Cartopy.__version__) > LooseVersion('0.16.0'):
            if lon_0 != 0:
                print('This projection requires lon_0=0')
                return

        ax = plt.axes(projection=ccrs.Mollweide(central_longitude=lon_0))
    xx, yy = np.meshgrid(lons, lats)
    levmax = 5*round(element.max()/5)+5
    levmin = 5*round(element.min()/5)-5
    if element_type == 'Br' or element_type == 'B':
        v=np.arange(min,max+5,5)
        if min and max:
            plt.contourf(xx, yy, element,v,
                     vmin=min,vmax=max,
                     cmap=cmap, transform=ccrs.PlateCarree())
        else:
            plt.contourf(xx, yy, element,v,
                     levels=np.arange(levmin, levmax, 1),
                     cmap=cmap, transform=ccrs.PlateCarree())
        cbar = plt.colorbar(orientation='horizontal')
        if contours:
            plt.contour(xx, yy, element, levels=np.arange(levmin, levmax, 10),
                        colors='black', transform=ccrs.PlateCarree())

        if element_type == 'Br':
            plt.title('Radial field strength ($\mu$T): '+date)
        else:
            plt.title('Total field strength ($\mu$T): '+date)
    if element_type == 'I':
        plt.contourf(xx, yy, element,
                     levels=np.arange(-90, 90, lincr),
                     cmap=cmap, transform=ccrs.PlateCarree())
        cbar = plt.colorbar(orientation='horizontal')
        if contours:
            plt.contour(xx, yy, element, levels=np.arange(-80, 90, 10),
                        colors='black', transform=ccrs.PlateCarree())
        plt.title('Field inclination: '+date)
    if element_type == 'D':
        plt.contourf(xx, yy, element,
                     levels=np.arange(-180, 180, 10),
                     cmap=cmap, transform=ccrs.PlateCarree())
        cbar = plt.colorbar(orientation='horizontal')
        if contours:
            plt.contour(xx, yy, element, levels=np.arange(-180, 180, 10),
                        colors='black', transform=ccrs.PlateCarree())
        plt.title('Field declination: '+date)
    ax.coastlines()
    ax.set_global()
    return ax


def plot_eq_cont(fignum, DIblock, color_map='coolwarm'):
    """
    plots dec inc block as a color contour
    Parameters
    __________________
    Input:
        fignum :  figure number
        DIblock : nested pairs of [Declination, Inclination]
        color_map : matplotlib color map [default is coolwarm]
    Output:
        figure
    """
    import random
    plt.figure(num=fignum)
    plt.axis("off")
    XY = []
    centres = []
    counter = 0
    for rec in DIblock:
        counter = counter + 1
        X = pmag.dir2cart([rec[0], rec[1], 1.])
        # from Collinson 1983
        R = old_div(np.sqrt(1. - X[2]), (np.sqrt(X[0]**2 + X[1]**2)))
        XY.append([X[0] * R, X[1] * R])
    # radius of the circle
    radius = (old_div(3., (np.sqrt(np.pi * (9. + float(counter)))))) + 0.01
    num = 2. * (old_div(1., radius))  # number of circles
    # a,b are the extent of the grids over which the circles are equispaced
    a1, a2 = (0. - (radius * num / 2.)), (0. + (radius * num / 2.))
    b1, b2 = (0. - (radius * num / 2.)), (0. + (radius * num / 2.))
    # this is to get an array (a list of list wont do) of x,y values
    xlist = np.linspace(a1, a2, int(np.ceil(num)))
    ylist = np.linspace(b1, b2, int(np.ceil(num)))
    X, Y = np.meshgrid(xlist, ylist)
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
    for i in range(0, int(np.ceil(num))**2):
        if np.sqrt(((centres[i][0])**2) + ((centres[i][1])**2)) - 1. < radius:
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
    for j in range(0, int(np.ceil(num))):
        for i in range(0, int(np.ceil(num))):
            for k in range(0, counter):
                if (XY[k][0] - centres[count][0])**2 + (XY[k][1] - centres[count][1])**2 <= radius**2:
                    dotspercircle += 1.
            Z[i][j] = Z[i][j] + (dotspercircle * fraction[count])
            count += 1
            dotspercircle = 0.
    im = plt.imshow(Z, interpolation='bilinear', origin='lower',
                    # cmap=plt.color_map.hot, extent=(-1., 1., -1., 1.))
                    cmap=color_map, extent=(-1., 1., -1., 1.))
    plt.colorbar(shrink=0.5)
    x, y = [], []
    # Draws the border
    for i in range(0, 360):
        x.append(np.sin((np.pi/180.) * float(i)))
        y.append(np.cos((np.pi/180.) * float(i)))
    plt.plot(x, y, 'w-')
    x, y = [], []
    # the map will be a square of 1X1..this is how I erase the redundant area
    for j in range(1, 4):
        for i in range(0, 360):
            x.append(np.sin((np.pi/180.) * float(i))
                     * (1. + (old_div(float(j), 10.))))
            y.append(np.cos((np.pi/180.) * float(i))
                     * (1. + (old_div(float(j), 10.))))
        plt.plot(x, y, 'w-', linewidth=26)
        x, y = [], []
    # the axes
    plt.axis("equal")


def plot_ts(ax, agemin, agemax, timescale='gts12', ylabel="Age (Ma)"):
    """
    Make a time scale plot between specified ages.

    Parameters:
    ------------
    ax : figure object
    agemin : Minimum age for timescale
    agemax : Maximum age for timescale
    timescale : Time Scale [ default is Gradstein et al., (2012)]
       for other options see pmag.get_ts()
    ylabel : if set, plot as ylabel
    """
    ax.set_title(timescale.upper())
    ax.axis([-.25, 1.5, agemax, agemin])
    ax.axes.get_xaxis().set_visible(False)
    # get dates and chron names for timescale
    TS, Chrons = pmag.get_ts(timescale)
    X, Y, Y2 = [0, 1], [], []
    cnt = 0
    if agemin < TS[1]:  # in the Brunhes
        Y = [agemin, agemin]  # minimum age
        Y1 = [TS[1], TS[1]]  # age of the B/M boundary
        ax.fill_between(X, Y, Y1, facecolor='black')  # color in Brunhes, black
    for d in TS[1:]:
        pol = cnt % 2
        cnt += 1
        if d <= agemax and d >= agemin:
            ind = TS.index(d)
            Y = [TS[ind], TS[ind]]
            Y1 = [TS[ind+1], TS[ind+1]]
            if pol:
                # fill in every other time
                ax.fill_between(X, Y, Y1, facecolor='black')
    ax.plot([0, 1, 1, 0, 0], [agemin, agemin, agemax, agemax, agemin], 'k-')
    plt.yticks(np.arange(agemin, agemax+1, 1))
    if ylabel != "":
        ax.set_ylabel(ylabel)
    ax2 = ax.twinx()
    ax2.axis('off')
    for k in range(len(Chrons)-1):
        c = Chrons[k]
        cnext = Chrons[k+1]
        d = cnext[1]-(cnext[1]-c[1])/3.
        if d >= agemin and d < agemax:
            # make the Chron boundary tick
            ax2.plot([1, 1.5], [c[1], c[1]], 'k-')
            ax2.text(1.05, d, c[0])
    ax2.axis([-.25, 1.5, agemax, agemin])


def save_or_quit(msg="S[a]ve plots - <q> to quit, <return> to continue: "):
    ans = None
    count = 0
    while ans not in ['q', 'a', '']:
        ans = input(msg)
        count += 1
        if count > 5:
            ans = 'q'
    if ans == 'a':
        return('a')
    if ans == 'q':
        print("\n Good bye\n")
        sys.exit()
    if ans == '':
        return

def label_tiepoints(ax,x,tiepoints,levels,color='black',lines=False):
    """
    Puts on labels for tiepoints in an age table on a stratigraphic plot.
    
    Parameters
    _______________________________
        ax : obj
            axis on which to plot the labels
        x : float or integer
            x value for the tiepoint labels
        levels : float
            stratigraphic positions of the tiepoints
        lines : bool
            put on horizontal lines at the tiepoint heights
    Returns
    _______________________________
        ax : obj
            axis  object
    """ 
    if color=='black':
        for c in range(len(tiepoints)):
            ax.text(x,levels[c],'- '+tiepoints[c],va='center',
               color=color)
    else:
        for c in range(len(tiepoints)):
            ax.text(x,levels[c],'('+tiepoints[c]+')',va='center',
               color=color)
    if lines:
        for  c in range(len(tiepoints)):
            if '(' in tiepoints[c]:
                ax.axhline(levels[c],color='green',linewidth=1)
            else:
                ax.axhline(levels[c],color='green',linewidth=3)



def msp_magic(spec_df,axa="",axb="",site='site',labels=['a)','b)'],save_plots=False,fmt ='pdf'):
    """   
    makes plots and calculations for MSP method of Dekkers & Boehnel (2006) (DB) and Fabian and Leonhardt (2010) method
    (DSC) of multi-specimen paleointensity technique. 
    NB: this code requires seaborn and scipy to be installed
    
    Parameters: 
    _____________
    spec_df : pandas dataframe
        data frame with MagIC measurement formatted data for one MSP experiment.
        measurements must have these MagIC method codes: 
        Mo (NRM step): must contain 'LT-NO' 
        M1 (pTRM at T || NRM): must contain 'LT-NRM-PAR' and not 'LT-PTRM-I'
        M2 (pTRM \\ NRM: must contain 'LT-NRM-APAR'
        M3 (heat to T, cool in lab field): must contain 'LT-T-Z-NRM-PAR'
        M4 (repeat of M1): must contain 'LT-PTRM-I'
        lab field must be in 'treat_dc_field'


    axa : matplotlib figure subplot for DB plot, default is to create and return.
    axb : matplotlib figure subplot for DSC plot, default is to create and return.
    site : name of group of specimens for y-axis label, default is generic 'site'
    labels : plot labels as specified. 
    save_plots : bool, default False
        if True, creat and save plot
    fmt : str
        format of saved figure (default is 'pdf')
    
    Returns: 
        B (in uT)
        standard error of slope
        axa, axb    
    """
    try: 
        import seaborn as sns
    except:
        " You must install seaborn to use this " 
        return False,False, axa, axb
    try: 
        import scipy.stats as stats
    except:
        " You must install scipy " 
        return False,False, axa, axb
    fontsize=14
    if axa=="":
        fig=plt.figure(1,(10,5))
        axa=fig.add_subplot(121) 
        axb=fig.add_subplot(122) 
    tinv=lambda p,df:abs(stats.t.ppf(p/2,df))
    M1s=spec_df[(spec_df['method_codes'].str.contains('LT-NRM-PAR'))&
        (spec_df['method_codes'].str.contains('LT-PTRM-I')==False)]

    Mos=spec_df[spec_df['method_codes'].str.contains('LT-NO')]
    Mos=Mos['magn_moment'].values
    
    Bs_uT=M1s['treat_dc_field'].values*1e6

    M1s=M1s['magn_moment'].values
    
    M2s=spec_df[spec_df['method_codes'].str.contains('LT-NRM-APAR')]
    M2s=M2s['magn_moment'].values

    M3s=spec_df[spec_df['method_codes'].str.contains('LT-T-Z-NRM-PAR')]
    M3s=M3s['magn_moment'].values

    M4s=spec_df[spec_df['method_codes'].str.contains('LT-PTRM-I')]
    M4s=M4s['magn_moment'].values
    
    Q_DB=(M1s-Mos)/Mos
    #coeffs=np.polyfit(Bs_uT,Q_DB,1)
    #newYs=np.polyval(coeffs,Bs_uT)
    q_data=pd.DataFrame()
    q_data['Bs_uT']=Bs_uT
    q_data['Q_DB']=Q_DB

    #axa.plot(Bs_uT,Q_DB,'co')
    axa.set_xlabel(r'B$_{lab} (\mu$T)',fontsize=fontsize) 
    axa.set_ylabel(r'Q_${DB}$: '+site,fontsize=fontsize)


    #axa.plot(Bs_uT,newYs,'k-')
    axa.axhline(0,linestyle='dotted')
    axa.axvline(70,linestyle='dashed')
    sns.regplot(data=q_data,x='Bs_uT',y='Q_DB',ax=axa)
    alpha=.5 # per Fabian and Leonhardt 2010
    Q_DSC=2.*((1.+alpha)*M1s-Mos-alpha*M3s)/(2.*Mos-M1s-M2s)
#    print (spec_df['specimen'].unique())
#    print (Q_DSC)
    q_data['Q_DSC']=Q_DSC



    #axb.plot(Bs_uT,Q_DSC,'co')
    axb.set_xlabel(r'B$_{lab} (\mu$T)',fontsize=fontsize)
    axb.set_ylabel(r'Q_${DSC}$: '+site,fontsize=fontsize)

    #coeffs,cov=np.polyfit(Bs_uT,Q_DSC,1,cov=True)
    
    Brange=np.arange(0,100,20)
    #newYs=np.polyval(coeffs,Brange)
    sns.regplot(data=q_data,x='Bs_uT',y='Q_DSC',ax=axb)
    #axb.plot(Brange,newYs,'k-')
    axb.axhline(0,linestyle='dotted')
    axb.axvline(70,linestyle='dashed')
    #axb.text(.2,.9,'B$_{msp}$='+str((-coeffs[1]/coeffs[0]).round(1))+' $\mu$T',
     #        transform=axb.transAxes,fontsize=fontsize)
    res=stats.linregress(Q_DSC,Bs_uT)
    ts=tinv(0.05,len(Q_DSC)-2)
    axb.text(.1,.9,f'Bmsp =: {res.intercept:.1f} $\pm$  {.5*ts*res.intercept_stderr:.1f} $\mu$T',
    #axb.text(.1,.9,f'Bmsp =: {res.intercept:.1f} $\pm$  {res.intercept_stderr:.1f} $\mu$T',
            transform=axb.transAxes,fontsize=fontsize)
    
    print(f"intercept (1 sigma): {res.intercept:.1f} +/- {res.intercept_stderr:.1f}")
    #axb.plot([res.intercept+.5*ts*res.intercept_stderr],[0],'b+')
    #axb.plot([res.intercept-.5*ts*res.intercept_stderr],[0],'b+')    
    axa.text(.9,.1,labels[0],fontsize=fontsize,transform=axa.transAxes)
    axb.text(.9,.1,labels[1],fontsize=fontsize,transform=axb.transAxes)
    if save_plots: 
        plt.tight_layout()
        plt.savefig('site.'+fmt)
    return res.intercept,.5*ts*res.intercept_stderr,res.intercept_stderr,axa,axb


# /usr/bin/env pythonw
    

# pylint: skip-file
# pylint: disable-all
# causes too many errors and crashes

import os
import sys
import warnings

import numpy as np
import pandas as pd
warnings.filterwarnings("ignore")  # what you don't know won't hurt you, or will it?
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
    fig = plt.figure(num=fignum, figsize=(w, h), dpi=dpi, clear=True)
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
        Y.append(rec[3] / first_Z[0][3])
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
        Y.append(rec[3] / first_Z[0][3])
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
                        rec[3] / zijdblock[0][3]))
        if rec[0] == pars["measurement_step_max"]:
            Dir.append((rec[1] - angle, rec[2],
                        rec[3] / zijdblock[0][3]))
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
    ax.append(first_I[0][3] / first_Z[0][3])
    ax.append(first_I[-1][3] / first_Z[0][3])
    ay.append(first_Z[0][3] / first_Z[0][3])
    ay.append(first_Z[-1][3] / first_Z[0][3])
    for k in range(len(first_Z)):
        if first_Z[k][0] == pars["measurement_step_min"]:
            ay[0] = (first_Z[k][3] / first_Z[0][3])
        if first_Z[k][0] == pars["measurement_step_max"]:
            ay[1] = (first_Z[k][3] / first_Z[0][3])
        if first_I[k][0] == pars["measurement_step_min"]:
            ax[0] = (first_I[k][3] / first_Z[0][3])
        if first_I[k][0] == pars["measurement_step_max"]:
            ax[1] = (first_I[k][3] / first_Z[0][3])
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
               pars["specimen_ytot"] / first_Z[0][3]))
    sy.append((pars["specimen_b"] * ax[1] +
               pars["specimen_ytot"] / first_Z[0][3]))
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
    xnum = float(nums - 1.0) / 2.0
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
        R = np.sqrt(1. - abs(elli[2])) / (np.sqrt(elli[0]**2 + elli[1]**2))
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
    plt.figure(num=fignum, figsize=(w, h), dpi=dpi, clear=True)
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
    fignum : matplotlib figure number
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
    fig = plt.figure(num=fignum)
    # sdata=np.array(data).sort()
    sdata = []
    for d in data:
        sdata.append(d)  # have to copy the data to avoid overwriting it!
    sdata.sort()
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


#!/usr/bin/env python
# define some variables
from __future__ import print_function
from builtins import str
import numpy as np
import sys
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")
import pylab as plt
try:
    import cartopy.crs as ccrs
except:
    ccrs = None
from pylab import meshgrid

import pmagpy.pmag as pmag
import pmagpy.pmagplotlib as pmagplotlib
from matplotlib import cm
import warnings
warnings.filterwarnings("ignore")


def main():
    """
    NAME
        plot_magmap.py

    DESCRIPTION
        makes a color contour map of desired field model

    SYNTAX
        plot_magmap.py [command line options]

    OPTIONS
        -h prints help and quits
        -f FILE  specify field model file with format:  l m g h
        -fmt [pdf,eps,svg,png]  specify format for output figure  (default is png)
        -mod [arch3k,cals3k,pfm9k,hfm10k,cals10k_2,shadif14k,cals10k] specify model for 3ka to 1900 CE, default is  cals10k
        -alt ALT;  specify altitude in km, default is sealevel (0)
        -age specify date in decimal year, default is 2016
        -lon0: 0 longitude for map, default is 0
        -el: [D,I,B,Br]  specify element for plotting
        -cm: [see https://matplotlib.org/users/colormaps.html] specify color map for plotting (default is RdYlBu)

    """
    cmap = 'RdYlBu'
    date = 2016.
    if not ccrs:
        print("-W- You must intstall the cartopy module to run plot_magmap.py")
        sys.exit()
    dir_path = '.'
    lincr = 1  # level increment for contours
    if '-WD' in sys.argv:
        ind = sys.argv.index('-WD')
        dir_path = sys.argv[ind+1]
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-fmt' in sys.argv:
        ind = sys.argv.index('-fmt')
        fmt = sys.argv[ind+1]
        if fmt == 'jpg':
            print('jpg not a supported option')
            print(main.__doc__)
            sys.exit()
    else:
        fmt = 'png'
    if '-cm' in sys.argv:
        ind = sys.argv.index('-cm')
        cmap = sys.argv[ind+1]
    if '-el' in sys.argv:
        ind = sys.argv.index('-el')
        el = sys.argv[ind+1]
    else:
        el = 'B'
    if '-alt' in sys.argv:
        ind = sys.argv.index('-alt')
        alt = sys.argv[ind+1]
    else:
        alt = 0
    if '-lon0' in sys.argv:
        ind = sys.argv.index('-lon0')
        lon_0 = float(sys.argv[ind+1])
    else:
        lon_0 = 0
    if '-mod' in sys.argv:
        ind = sys.argv.index('-mod')
        mod = sys.argv[ind+1]
        ghfile = ''
    elif '-f' in sys.argv:
        ind = sys.argv.index('-f')
        ghfile = sys.argv[ind+1]
        mod = 'custom'
        date = ''
    else:
        mod, ghfile = 'cals10k', ''
    if '-age' in sys.argv:
        ind = sys.argv.index('-age')
        date = float(sys.argv[ind+1])
    if '-alt' in sys.argv:
        ind = sys.argv.index('-alt')
        alt = float(sys.argv[ind+1])
    else:
        alt = 0

    # doesn't work correctly with mod other than default
    Ds, Is, Bs, Brs, lons, lats = pmag.do_mag_map(
        date, mod=mod, lon_0=lon_0, alt=alt, file=ghfile)
    ax = plt.axes(projection=ccrs.Mollweide(central_longitude=lon_0))
    ax.coastlines()
    xx, yy = meshgrid(lons, lats)
    if mod == 'custom':
        str_date = 'Custom'
    else:
        str_date = str(date)
    if el == 'B':
        levmax = Bs.max()+lincr
        levmin = round(Bs.min()-lincr)
        levels = np.arange(levmin, levmax, lincr)
        plt.contourf(xx, yy, Bs, levels=levels, cmap=cmap,
                     transform=ccrs.PlateCarree(central_longitude=lon_0))
        plt.title('Field strength ($\mu$T): '+ str_date)
    if el == 'Br':
        levmax = Brs.max()+lincr
        levmin = round(Brs.min()-lincr)
        plt.contourf(xx, yy, Brs,
                     levels=np.arange(levmin, levmax, lincr),
                     cmap=cmap, transform=ccrs.PlateCarree(central_longitude=lon_0))
        plt.title('Radial field strength ($\mu$T): '+ str_date)
    if el == 'I':
        levmax = Is.max()+lincr
        levmin = round(Is.min()-lincr)
        plt.contourf(xx, yy, Is,
                     levels=np.arange(levmin, levmax, lincr),
                     cmap=cmap, transform=ccrs.PlateCarree(central_longitude=lon_0))
        plt.contour(xx, yy, Is, levels=np.arange(-80, 90, 10),
                    colors='black', transform=ccrs.PlateCarree(central_longitude=lon_0))
        plt.title('Field inclination: '+ str_date)
    if el == 'D':
        plt.contourf(xx, yy, Ds,
                     levels=np.arange(-180, 180, 10),
                     cmap=cmap, transform=ccrs.PlateCarree(central_longitude=lon_0))
        plt.contour(xx, yy, Ds, levels=np.arange(-180,
                                                 180, 10), colors='black')
        # cs=m.contourf(x,y,Ds,levels=np.arange(-180,180,10),cmap=cmap)
        # cs=m.contourf(x,y,Ds,levels=np.arange(-180,180,10),cmap=cmap)
        # m.contour(x,y,Ds,levels=np.arange(-180,180,10),colors='black')
        plt.title('Field declination: '+ str_date)
    cbar = plt.colorbar(orientation='horizontal')
    figname = 'geomagnetic_field_' + str_date + '.'+fmt
    plt.savefig(figname)
    print('Figure saved as: ', figname)


if __name__ == "__main__":
    main()

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
  from mpl_toolkits.basemap import Basemap
except ImportError:
  Basemap = None
from pylab import meshgrid

import pmagpy.pmag as pmag
import pmagpy.pmagplotlib as pmagplotlib

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
        -fmt [pdf,jpg,eps,svg]  specify format for output figure  (default is jpg)
        -mod [arch3k,cals3k,pfm9k,hfm10k,cals10k_2,shadif14k,cals10k] specify model for 3ka to 1900 CE, default is  cals10k
        -alt ALT;  specify altitude in km, default is sealevel (0)
        -age specify date in decimal year, default is 2015
        -lon0: 0 longitude for map, default is 0
        -el: [D,I,B,Br]  specify element for plotting, default is B

    """
    if not Basemap:
      print("-W- You must intstall the Basemap module to run plot_magmap.py")
      sys.exit()
    dir_path='.'
    lincr=1 # level increment for contours
    if '-WD' in sys.argv:
        ind = sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-fmt' in sys.argv:
        ind = sys.argv.index('-fmt')
        fmt=sys.argv[ind+1]
    else: fmt='jpg'
    if '-el' in sys.argv:
        ind = sys.argv.index('-el')
        el=sys.argv[ind+1]
    else:
        el='B'
    if '-alt' in sys.argv:
        ind = sys.argv.index('-alt')
        alt=sys.argv[ind+1]
    else: alt=0
    if '-lon0' in sys.argv:
        ind=sys.argv.index('-lon0')
        lon_0=sys.argv[ind+1]
    else: lon_0=0
    if '-mod' in sys.argv:
        ind=sys.argv.index('-mod')
        mod=sys.argv[ind+1]
    else: mod='cals10k'
    if '-age' in sys.argv:
        ind=sys.argv.index('-age')
        date=float(sys.argv[ind+1])
    else: date=2016.
    Ds,Is,Bs,Brs,lons,lats=pmag.do_mag_map(date,mod=mod,lon_0=lon_0,alt=alt,el=el)
    m = Basemap(projection='hammer',lon_0=lon_0)
    x,y=m(*meshgrid(lons,lats))
    m.drawcoastlines()
    if el=='B':
        levmax=Bs.max()+lincr
        levmin=round(Bs.min()-lincr)
        cs=m.contourf(x,y,Bs,levels=np.arange(levmin,levmax,lincr))
        plt.title('Field strength ($\mu$T): '+str(date));
    if el=='Brs':
        levmax=Brs.max()+lincr
        levmin=round(Brs.min()-lincr)
        cs=m.contourf(x,y,Brs,levels=np.arange(levmin,levmax,lincr))
        plt.title('Radial field strength ($\mu$T): '+str(date));
    if el=='I':
        levmax=Is.max()+lincr
        levmin=round(Is.min()-lincr)
        cs=m.contourf(x,y,Is,levels=np.arange(levmin,levmax,lincr))
        m.contour(x,y,Is,levels=np.arange(-80,90,10),colors='black')
        plt.title('Field inclination: '+str(date));
    if el=='D':
        levmax=Ds.max()+lincr
        levmin=round(Ds.min()-lincr)
        cs=m.contourf(x,y,Ds,levels=np.arange(levmin,levmax,lincr))
        m.contour(x,y,Ds,levels=np.arange(0,360,10),colors='black')
        plt.title('Field declination: '+str(date));
    cbar=m.colorbar(cs,location='bottom')
    plt.savefig('igrf'+'%6.1f'%(date)+'.'+fmt)
    print('Figure saved as: ','igrf'+'%6.1f'%(date)+'.'+fmt)

if __name__ == "__main__":
    main()

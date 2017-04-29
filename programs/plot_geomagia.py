#!/usr/bin/env python
# data from http://geomagia.ucsd.edu



from __future__ import print_function
from builtins import input
import matplotlib
import sys
import pylab
import numpy
#matplotlib.use("TkAgg")
import pmagpy.pmagplotlib as pmagplotlib

def main():
    """
    NAME
        plot_geomagia.py

    DESCRIPTION
        makes a map  and VADM plot of geomagia download file 

    SYNTAX
        plot_geomagia.py  [command line options]

    OPTIONS
        -h prints help message and quits
        -f FILE, specify geomagia download file
        -res [c,l,i,h] specify resolution (crude,low,intermediate,high)
        -etp plot the etopo20 topographic mesh
        -pad [LAT LON]  pad bounding box by LAT/LON  (default is [.5 .5] degrees)
        -grd SPACE specify grid spacing
        -prj [lcc] , specify projection (lcc=lambert conic conformable), default is mercator
        -o color ocean blue/land green (default is not)
        -d plot details of rivers, boundaries, etc.
        -sav save plot and quit quietly
        -fmt [png,svg,eps,jpg,pdf] specify format for output, default is pdf
    DEFAULTS
        resolution: intermediate
        saved images are in pdf
    """
    dir_path='.'
    names,res,proj,locs,padlon,padlat,fancy,gridspace,details=[],'l','lcc','',0,0,0,15,1
    Age_bounds=[-5000,2000]
    Lat_bounds=[20,45]
    Lon_bounds=[15,55]
    fmt='pdf'
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-f' in sys.argv:
        ind = sys.argv.index('-f')
        sites_file=sys.argv[ind+1]
    if '-res' in sys.argv:
        ind = sys.argv.index('-res')
        res=sys.argv[ind+1]
    if '-etp' in sys.argv:fancy=1
    if '-o' in sys.argv:ocean=1
    if '-d' in sys.argv:details=1
    if '-prj' in sys.argv:
        ind = sys.argv.index('-prj')
        proj=sys.argv[ind+1]
    if '-fmt' in sys.argv:
        ind = sys.argv.index('-fmt')
        fmt=sys.argv[ind+1]
    verbose=pmagplotlib.verbose
    if '-sav' in sys.argv:
        verbose=0
    if '-pad' in sys.argv:
        ind = sys.argv.index('-pad')
        padlat=float(sys.argv[ind+1])
        padlon=float(sys.argv[ind+2])
    if '-grd' in sys.argv:
        ind = sys.argv.index('-grd')
        gridspace=float(sys.argv[ind+1])
    if '-WD' in sys.argv:
        ind = sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
    sites_file=dir_path+'/'+sites_file
    geo_in=open(sites_file,'r').readlines()
    Age,AgeErr,Vadm,VadmErr,slats,slons=[],[],[],[],[],[]
    for line in geo_in[2:]: # skip top two rows`
        rec=line.split()
        if float(rec[0])>Age_bounds[0] and float(rec[0])<Age_bounds[1] \
           and float(rec[12])>Lat_bounds[0] and float(rec[12]) < Lat_bounds[1]\
            and float(rec[13])>Lon_bounds[0] and float(rec[13])<Lon_bounds[1]:
            Age.append(float(rec[0]))
            AgeErr.append(float(rec[1]))
            Vadm.append(10.*float(rec[6]))
            VadmErr.append(10.*float(rec[7]))
            slats.append(float(rec[12]))
            slons.append(float(rec[13]))
    FIGS={'map':1,'vadms':2}
    pmagplotlib.plot_init(FIGS['map'],6,6)
    pmagplotlib.plot_init(FIGS['vadms'],6,6)
    Opts={'res':res,'proj':proj,'loc_name':locs,'padlon':padlon,'padlat':padlat,'latmin':numpy.min(slats)-padlat,'latmax':numpy.max(slats)+padlat,'lonmin':numpy.min(slons)-padlon,'lonmax':numpy.max(slons)+padlon,'sym':'ro','boundinglat':0.,'pltgrid':1}
    Opts['lon_0']=int(0.5*(numpy.min(slons)+numpy.max(slons)))
    Opts['lat_0']=int(0.5*(numpy.min(slats)+numpy.max(slats)))
    Opts['gridspace']=gridspace
    if details==1:
        Opts['details']={'coasts':1,'rivers':0,'states':1,'countries':1,'ocean':1}
    else:
        Opts['details']={'coasts':1,'rivers':0,'states':0,'countries':0,'ocean':1}
    Opts['details']['fancy']=fancy
    pmagplotlib.plotMAP(FIGS['map'],slats,slons,Opts)
    pmagplotlib.plotXY(FIGS['vadms'],Age,Vadm,sym='bo',xlab='Age (Years CE)',ylab=r'VADM (ZAm$^2$)')
    if verbose:pmagplotlib.drawFIGS(FIGS)
    files={}
    for key in list(FIGS.keys()):
        files[key]=key+'.'+fmt
    if pmagplotlib.isServer:
        black     = '#000000'
        purple    = '#800080'
        titles={}
        titles['map']='Map'
        titles['vadms']='VADMs'
        FIG = pmagplotlib.addBorders(FIGS,titles,black,purple)
        pmagplotlib.saveP(FIGS,files)
    elif verbose:
        ans=input(" S[a]ve to save plot, Return to quit:  ")
        if ans=="a":
            pmagplotlib.saveP(FIGS,files)
    else:
        pmagplotlib.saveP(FIGS,files)

if __name__ == "__main__":
    main() 

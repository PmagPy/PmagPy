#!/usr/bin/env python
# define some variables
from __future__ import print_function
from builtins import input
import sys
import numpy


#from mpl_toolkits.basemap import Basemap
import pmagpy.pmag as pmag
import pmagpy.pmagplotlib as pmagplotlib


import matplotlib.pylab as plt
def main():
    """
    NAME 
        basemap_magic.py
        NB:  this program no longer maintained - use plot_mapPTS.py for greater functionality

    DESCRIPTION
        makes a map of locations in er_sites.txt
 
    SYNTAX
        basemap_magic.py  [command line options]

    OPTIONS
        -h prints help message and quits
        -f SFILE, specify er_sites.txt or pmag_results.txt format file
        -res [c,l,i,h] specify resolution (crude,low,intermediate,high)
        -etp plot the etopo20 topographic mesh
        -pad [LAT LON]  pad bounding box by LAT/LON  (default is [.5 .5] degrees)
        -grd SPACE specify grid spacing
        -prj [lcc] , specify projection (lcc=lambert conic conformable), default is mercator
        -n print site names (default is not)
        -l print location names (default is not)
        -o color ocean blue/land green (default is not)
        -R don't plot details of rivers
        -B don't plot national/state  boundaries, etc.
        -sav save plot and quit quietly
        -fmt [png,svg,eps,jpg,pdf] specify format for output, default is pdf     
    DEFAULTS
        SFILE: 'er_sites.txt'
        resolution: intermediate
        saved images are in pdf
    """
    dir_path='.'
    sites_file='er_sites.txt'
    ocean=0
    res='i'
    proj='merc'
    prn_name=0
    prn_loc=0
    fancy=0
    rivers,boundaries=0,0
    padlon,padlat,gridspace,details=.5,.5,.5,1
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
    if '-n' in sys.argv:prn_name=1
    if '-l' in sys.argv:prn_loc=1
    if '-o' in sys.argv:ocean=1
    if '-R' in sys.argv:rivers=0
    if '-B' in sys.argv:boundaries=0
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
    location=""
    FIG={'map':1}
    pmagplotlib.plot_init(FIG['map'],6,6)
    # read in er_sites file
    Sites,file_type=pmag.magic_read(sites_file)
    if 'results' in file_type:
        latkey='average_lat'
        lonkey='average_lon'
        namekey='pmag_result_name'
        lockey='er_location_names'
    else:
        latkey='site_lat'
        lonkey='site_lon'
        namekey='er_site_name'
        lockey='er_location_name'
    lats,lons=[],[]
    slats,slons=[],[]
    names,locs=[],[]
    for site in Sites:
        if prn_loc==1 and location=="":location=site['er_location_name']
        lats.append(float(site[latkey]))
        l=float(site[lonkey])
        if l<0:l=l+360. # make positive
        lons.append(l)
        if prn_name==1:names.append(site[namekey])
        if prn_loc==1:locs.append(site[lockey])
    for lat in lats:slats.append(lat)
    for lon in lons:slons.append(lon)
    Opts={'res':res,'proj':proj,'loc_name':locs,'padlon':padlon,'padlat':padlat,'latmin':numpy.min(slats)-padlat,'latmax':numpy.max(slats)+padlat,'lonmin':numpy.min(slons)-padlon,'lonmax':numpy.max(slons)+padlon,'sym':'ro','boundinglat':0.,'pltgrid':1.}
    Opts['lon_0']=0.5*(numpy.min(slons)+numpy.max(slons))
    Opts['lat_0']=0.5*(numpy.min(slats)+numpy.max(slats))
    Opts['names']=names
    Opts['gridspace']=gridspace
    Opts['details']={'coasts':1,'rivers':1,'states':1,'countries':1,'ocean':0} 
    if ocean==1:Opts['details']['ocean']=1
    if rivers==1: Opts['details']['rivers']=0
    if boundaries==1:
        Opts['details']['states']=0
        Opts['details']['countries']=0
    Opts['details']['fancy']=fancy
    pmagplotlib.plotMAP(FIG['map'],lats,lons,Opts)
    if verbose:pmagplotlib.drawFIGS(FIG)
    files={}
    for key in list(FIG.keys()):
        files[key]='Site_map'+'.'+fmt
    if pmagplotlib.isServer:
        black     = '#000000'
        purple    = '#800080'
        titles={}
        titles['map']='Site Map'
        FIG = pmagplotlib.addBorders(FIG,titles,black,purple)
        pmagplotlib.saveP(FIG,files)
    elif verbose:
        ans=input(" S[a]ve to save plot, Return to quit:  ")
        if ans=="a":
            pmagplotlib.saveP(FIG,files)
    else:
        pmagplotlib.saveP(FIG,files)
main()

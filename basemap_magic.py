#!/usr/bin/env python
# define some variables
import pmag,sys
import pmagplotlib
import numpy
from mpl_toolkits.basemap import Basemap
import matplotlib.pylab as plt
def main():
    """
    NAME 
        basemap_magic.py

    DESCRIPTION
        makes a map of locations in er_sites.txt
 
    SYNTAX
        basemap_magic.py  [command line options]

    OPTIONS
        -h prints help message and quits
        -f SFILE, specify er_sites.txt format file
        -res [c,l,i,h] specify resolution (crude,low,intermediate,high)
        -pad [LAT LON]  pad bounding box by LAT/LON  (default is [.5 .5] degrees)
        -grd SPACE specify grid spacing
        -prj [lcc] , specify projection (lcc=lambert conic conformable), default is mercator
        -n print site names (default is not)
        -l print location names (default is not)
        -o color ocean blue/land green (default is not)
        -D don't plot details of rivers, boundaries, etc.
    
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
    padlon,padlat,gridspace,details=.5,.5,.5,1
    fmt='pdf'
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-f' in sys.argv:
        ind = sys.argv.index('-f')
        sites_file=sys.argv[ind+1]
    if '-res' in sys.argv:
        ind = sys.argv.index('-res')
        res=sys.argv[ind+1]
    if '-n' in sys.argv:prn_name=1
    if '-l' in sys.argv:prn_loc=1
    if '-o' in sys.argv:ocean=1
    if '-D' in sys.argv:details=0
    if '-prj' in sys.argv:
        ind = sys.argv.index('-prj')
        proj=sys.argv[ind+1]
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
    lats,lons=[],[]
    slats,slons=[],[]
    names,locs=[],[]
    for site in Sites:
        if prn_loc==1 and location=="":location=site['er_location_name']
        lats.append(float(site['site_lat']))
        l=float(site['site_lon'])
        if l<0:l=l+360. # make positive
        lons.append(l)
        if prn_name==1:names.append(site['er_site_name'])
        if prn_loc==1:locs.append(site['er_location_name'])
    for lat in lats:slats.append(lat)
    for lon in lons:slons.append(lon)
    Opts={'res':res,'proj':proj,'loc_name':locs,'padlon':padlon,'padlat':padlat,'latmin':numpy.min(slats)-padlat,'latmax':numpy.max(slats)+padlat,'lonmin':numpy.min(slons)-padlon,'lonmax':numpy.max(slons)+padlon,'sym':'ro','boundinglat':0.,'pltgrid':1.}
    Opts['lon_0']=0.5*(numpy.min(slons)+numpy.max(slons))
    Opts['lat_0']=0.5*(numpy.min(slats)+numpy.max(slats))
    Opts['names']=names
    Opts['gridspace']=gridspace
    if details==1:
        Opts['details']={'coasts':1,'rivers':1,'states':1,'countries':1,'ocean':1} 
    else: 
        Opts['details']={'coasts':1,'rivers':0,'states':0,'countries':0,'ocean':1} 
    pmagplotlib.plotMAP(FIG['map'],lats,lons,Opts)
    pmagplotlib.drawFIGS(FIG)
    files={}
    for key in FIG.keys():
        files[key]='Site_map'+'.'+fmt
    if pmagplotlib.isServer:
        black     = '#000000'
        purple    = '#800080'
        titles={}
        titles['eq']='Site Map'
        FIG = pmagplotlib.addBorders(FIG,titles,black,purple)
        pmagplotlib.saveP(FIG,files)
    else:
        ans=raw_input(" S[a]ve to save plot, Return to quit:  ")
        if ans=="a":
            pmagplotlib.saveP(FIG,files)
main()

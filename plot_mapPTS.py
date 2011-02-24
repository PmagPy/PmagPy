#!/usr/bin/env python
# define some variables
import pmag,sys,pmagplotlib,continents
def main():
    """
    NAME 
        plot_mapPTS.py 

    DESCRIPTION
        plots points on map
 
    SYNTAX
        plot_mapPTS.py [command line options]

    OPTIONS
        -h prints help and quits
        -sym [ro, bs, g^, r., b-, etc.] [1,5,10] symbol and size for points
           colors are r=red,b=blue,g=green, etc.
           symbols are '.' for points, ^, for triangle, s for square, etc.
            -, for lines, -- for dotted lines, see matplotlib online documentation for plot()
        -eye  ELAT ELON [specify eyeball location]
        -f FILE, specify input file
        -res [c,l,i,h] specify resolution (crude, low, intermediate, high]
        -prj PROJ,  specify one of the supported projections: (see basemap.py online documentation)
            aeqd = Azimuthal Equidistant
            poly = Polyconic
            gnom = Gnomonic
            moll = Mollweide
            tmerc = Transverse Mercator
            nplaea = North-Polar Lambert Azimuthal
            mill = Miller Cylindrical
            merc = Mercator
            stere = Stereographic
            npstere = North-Polar Stereographic
            geos = Geostationary
            laea = Lambert Azimuthal Equal Area
            sinu = Sinusoidal
            spstere = South-Polar Stereographic
            lcc = Lambert Conformal
            npaeqd = North-Polar Azimuthal Equidistant
            eqdc = Equidistant Conic
            cyl = Cylindrical Equidistant
            omerc = Oblique Mercator
            aea = Albers Equal Area
            spaeqd = South-Polar Azimuthal Equidistant
            ortho = Orthographic
            cass= Cassini-Soldner
            splaea = South-Polar Lambert Azimuthal
            robin = Robinson
    
    INPUTS
        space delimited LON LAT data
    DEFAULTS
        res:  c
        prj: mollweide 
        ELAT,ELON = 0,0
        NB: high resolution or lines can be very slow
    
    """
    dir_path='.'
    ocean=0
    res='c'
    proj='moll'
    Lats,Lons=[],[]
    lat_0,lon_0=0.,0.
    fmt='pdf'
    sym='ro'
    symsize=5
    if '-WD' in sys.argv:
        ind = sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-res' in sys.argv:
        ind = sys.argv.index('-res')
        res=sys.argv[ind+1]
        if res!= 'c' and res!='l':
            print 'this resolution will take a while - be patient'
    if '-prj' in sys.argv:
        ind = sys.argv.index('-prj')
        proj=sys.argv[ind+1]
    if '-eye' in sys.argv:
        ind = sys.argv.index('-eye')
        lat_0=float(sys.argv[ind+1])
        lon_0=float(sys.argv[ind+2])
    if '-sym' in sys.argv:
        ind = sys.argv.index('-sym')
        sym=sys.argv[ind+1]
        symsize=int(sys.argv[ind+2])
    if '-f' in sys.argv:
        ind = sys.argv.index('-f')
        file=dir_path+'/'+sys.argv[ind+1]
        f=open(file,'rU')
        ptdata=f.readlines()
        for line in ptdata:
            rec=line.split()
            if len(rec)>1:
               Lons.append(float(rec[0]))
               Lats.append(float(rec[1]))
    else:
        print "input file must be specified"
        sys.exit()
    FIG={'map':1}
    pmagplotlib.plot_init(FIG['map'],6,6)
    if res=='c':skip=8
    if res=='l':skip=5
    if res=='i':skip=2
    if res=='h':skip=1
    cnt=0
    Opts={'latmin':-90,'latmax':90,'lonmin':0.,'lonmax':360.,'lat_0':lat_0,'lon_0':lon_0,'proj':proj,'sym':sym,'symsize':3,'pltgrid':0,'res':res,'boundinglat':0.}
    Opts['details']={}
    Opts['details']['coasts']=1
    Opts['details']['rivers']=0
    Opts['details']['states']=0
    Opts['details']['countries']=0
    Opts['details']['ocean']=0

    if proj=='merc':
        Opts['latmin']=-70
        Opts['latmax']=70
        Opts['lonmin']=-180
        Opts['lonmax']=180
    print 'please wait to draw points'
    Opts['sym']=sym
    Opts['symsize']=symsize
    pmagplotlib.plotMAP(FIG['map'],Lats,Lons,Opts)
    pmagplotlib.drawFIGS(FIG)
    files={}
    for key in FIG.keys():
        files[key]='Map_PTS'+'.'+fmt
    if pmagplotlib.isServer:
        black     = '#000000'
        purple    = '#800080'
        titles={}
        titles['eq']='PT Map'
        FIG = pmagplotlib.addBorders(FIG,titles,black,purple)
        pmagplotlib.saveP(FIG,files)
    else:
        ans=raw_input(" S[a]ve to save plot, Return to quit:  ")
        if ans=="a":
            pmagplotlib.saveP(FIG,files)

main()

#!/usr/bin/env python
# define some variables
from __future__ import print_function
from builtins import input
import sys
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")

import pmagpy.pmag as pmag
import pmagpy.pmagplotlib as pmagplotlib
import pmagpy.continents as continents
from pmag_env import set_env
IS_WIN = set_env.IS_WIN


def main():
    """
    NAME
        cont_rot.py

    DESCRIPTION
        rotates continental fragments according to specified Euler pole

    SYNTAX
        cont_rot.py [command line options]

    OPTIONS
        -h prints help and quits
        -con [af, congo, kala, aus, balt, eur, ind, sam, ant, grn, lau, nam, gond] , specify colon delimited list of continents to be displayed, e.g., af, af:aus], etc
        -age use finite rotations of Torsvik et al. 2008 for specific age (5 Ma increments <325Ma)
             rotates to paleomagnetic reference frame
             available conts: [congo kala aus eur ind sam ant grn nam]
        -sac include rotation of south african craton to pmag reference
        -sym [ro, bs, g^, r., b-, etc.] [1,5,10] symbol and size for continent
           colors are r=red,b=blue,g=green, etc.
           symbols are '.' for points, ^, for triangle, s for square, etc.
            -, for lines, -- for dotted lines, see matplotlib online documentation for plot()
        -eye  ELAT ELON [specify eyeball location]
        -pfr  PLAT PLON OMEGA  [specify pole of finite rotation lat,lon and degrees]
        -ffr FFILE, specifies series of finite rotations
           vector in tab delimited file
        -sr treat poles as sequential rotations
        -fpp PFILE, specifies series of paleopoles from which
           euler poles can be calculated: vector in tab delimited file
        -pt LAT LON,  specify a point to rotate along with continent
        -fpt PTFILE, specifies file with a series of points to be plotted
        -res [c,l,i,h] specify resolution (crude, low, intermediate, high]
        -fmt [png,jpg,svg,pdf] format for saved figure - pdf is default
        -sav saves plots and quits
        -prj PROJ,  specify one of the supported projections
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
            utm = UTM
            laea = Lambert Azimuthal Equal Area
            geos = Geostationary
            npstere = North-Polar Stereographic
            spstere = South-Polar Stereographic

    DEFAULTS
        con: nam
        res:  c
        prj: mollweide
        ELAT,ELON = 0,0
        NB: high resolution or lines can be very slow

    """
    dir_path = '.'
    ocean = 0
    res = 'c'
    proj = 'moll'
    euler_file = ''
    Conts = []
    Poles = []
    PTS = []
    lat_0, lon_0 = 0., 0.
    fmt = 'pdf'
    sym = 'r.'
    symsize = 5
    plot = 0
    SEQ, age, SAC = 0, 0, 0
    rconts = ['af', 'congo', 'kala', 'aus',
              'eur', 'ind', 'sam', 'ant', 'grn', 'nam']
    if '-WD' in sys.argv:
        ind = sys.argv.index('-WD')
        dir_path = sys.argv[ind+1]
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-fmt' in sys.argv:
        ind = sys.argv.index('-fmt')
        fmt = sys.argv[ind+1]
    if '-con' in sys.argv:
        ind = sys.argv.index('-con')
        Conts = sys.argv[ind+1].split(':')
    if '-age' in sys.argv:
        ind = sys.argv.index('-age')
        age = int(sys.argv[ind+1])
        if age % 5 != 0 and age > 320:
            print(main.__doc__)
            print('age must be multiple of 5 less than 325')
            sys.exit()
        import pmagpy.frp as frp
    if '-res' in sys.argv:
        ind = sys.argv.index('-res')
        res = sys.argv[ind+1]
        if res != 'c' and res != 'l':
            print('this resolution will take a while - be patient')
    if '-prj' in sys.argv:
        ind = sys.argv.index('-prj')
        proj = sys.argv[ind+1]
    if '-sav' in sys.argv:
        plot = 1
    if '-eye' in sys.argv:
        ind = sys.argv.index('-eye')
        lat_0 = float(sys.argv[ind+1])
        lon_0 = float(sys.argv[ind+2])
    if '-pt' in sys.argv:
        ind = sys.argv.index('-pt')
        pt_lat = float(sys.argv[ind+1])
        pt_lon = float(sys.argv[ind+2])
        PTS.append([pt_lat, pt_lon])
    if '-sym' in sys.argv:
        ind = sys.argv.index('-sym')
        sym = sys.argv[ind+1]
        symsize = int(sys.argv[ind+2])
#    if '-rsym' in sys.argv:
#        ind = sys.argv.index('-rsym')
#        rsym=sys.argv[ind+1]
#        rsymsize=int(sys.argv[ind+2])
    if '-sr' in sys.argv:
        SEQ = 1
    if '-sac' in sys.argv:
        SAC = 1
    if '-pfr' in sys.argv:
        ind = sys.argv.index('-pfr')
        Poles.append(
            [float(sys.argv[ind+1]), float(sys.argv[ind+2]), float(sys.argv[ind+3])])
    elif '-ffr' in sys.argv:
        ind = sys.argv.index('-ffr')
        file = dir_path+'/'+sys.argv[ind+1]
        f = open(file, 'r')
        edata = f.readlines()
        for line in edata:
            rec = line.split()
            Poles.append([float(rec[0]), float(rec[1]), float(rec[2])])
    elif '-fpp' in sys.argv:
        ind = sys.argv.index('-fpp')
        file = dir_path+'/'+sys.argv[ind+1]
        f = open(file, 'r')
        pdata = f.readlines()
        for line in pdata:
            rec = line.split()
# transform paleopole to Euler pole taking shortest route
            Poles.append([0., float(rec[1])-90., 90.-float(rec[0])])
    if '-fpt' in sys.argv:
        ind = sys.argv.index('-fpt')
        file = dir_path+'/'+sys.argv[ind+1]
        f = open(file, 'r')
        ptdata = f.readlines()
        for line in ptdata:
            rec = line.split()
            PTS.append([float(rec[0]), float(rec[1])])
    FIG = {'map': 1}
    pmagplotlib.plot_init(FIG['map'], 6, 6)
    # read in er_sites file
    if res == 'c':
        skip = 8
    if res == 'l':
        skip = 5
    if res == 'i':
        skip = 2
    if res == 'h':
        skip = 1
    cnt = 0
    Opts = {'latmin': -90, 'latmax': 90, 'lonmin': 0., 'lonmax': 360., 'lat_0': lat_0, 'lon_0': lon_0,
            'proj': proj, 'sym': sym, 'symsize': 3, 'pltgrid': 0, 'res': res, 'boundinglat': 0.}
    if proj == 'merc':
        Opts['latmin'] = -70
        Opts['latmax'] = 70
        Opts['lonmin'] = -180
        Opts['lonmax'] = 180
    pmagplotlib.plot_map(FIG['map'], [], [], Opts)  # plot the base map
    Opts['pltgrid'] = -1  # turn off replotting of gridlines
    if '-pt' in sys.argv:
        Opts['sym'] = sym
        Opts['symsize'] = symsize
        pmagplotlib.plot_map(FIG['map'], [pt_lat], [pt_lon], Opts)
        if plot == 0 and not IS_WIN:
            pmagplotlib.draw_figs(FIG)
    for cont in Conts:
        Opts['sym'] = sym
        lats, lons = [], []
        if age != 0:
            Poles = []
            rcont = cont
            if rcont not in rconts:
                print(main.__doc__)
                print(rcont)
                print('continents  must be one of following: ')
                print(rconts)
                sys.exit()
            if rcont == 'congo':
                rcont = 'nwaf'
            if rcont == 'kala':
                rcont = 'neaf'
            if rcont == 'sam':
                rcont = 'sac'
            if rcont == 'ant':
                rcont = 'eant'
            if rcont != 'af':
                Poles.append(frp.get_pole(rcont, age))
            else:
                Poles.append([0, 0, 0])
            if SAC == 1:
                Poles.append(frp.get_pole('saf', age))
            SEQ = 1
            if Poles[-1] == 'NONE':
                print('continent does not exist for rotation, try again ')
                sys.exit()
        data = continents.get_continent(cont+'.asc')
        for line in data:
            if float(line[0]) == 0 and float(line[1]) == 0:
                line[0] = '100.'  # change stupid 0,0s to delimeters with lat=100
            if float(line[0]) > 90:
                lats.append(float(line[0]))
                lons.append(float(line[1]))
            elif cnt % skip == 0:
                lats.append(float(line[0]))
                lons.append(float(line[1]))
            cnt += 1
        if len(lats) > 0 and len(Poles) == 0:
            pmagplotlib.plot_map(FIG['map'], lats, lons, Opts)
            if plot == 0 and not IS_WIN:
                pmagplotlib.draw_figs(FIG)
        newlats, newlons = [], []
        for lat in lats:
            newlats.append(lat)
        for lon in lons:
            newlons.append(lon)
        Opts['pltgrid'] = -1  # turns off replotting of meridians and parallels
        for pole in Poles:
            Rlats, Rlons = pmag.pt_rot(pole, newlats, newlons)
            Opts['sym'] = sym
            Opts['symsize'] = 3
            if SEQ == 0:
                pmagplotlib.plot_map(FIG['map'], Rlats, Rlons, Opts)
            elif pole == Poles[-1]:  # plot only last pole for sequential rotations
                pmagplotlib.plot_map(FIG['map'], Rlats, Rlons, Opts)
            if plot == 0 and not IS_WIN:
                pmagplotlib.draw_figs(FIG)
            if SEQ == 1:  # treat poles as sequential rotations
                newlats, newlons = [], []
                for lat in Rlats:
                    newlats.append(lat)
                for lon in Rlons:
                    newlons.append(lon)
    for pt in PTS:
        pt_lat = pt[0]
        pt_lon = pt[1]
        Opts['sym'] = 'r*'
        Opts['symsize'] = 5
        pmagplotlib.plot_map(FIG['map'], [pt[0]], [pt[1]], Opts)
        if plot == 0 and not IS_WIN:
            pmagplotlib.draw_figs(FIG)
        Opts['pltgrid'] = -1  # turns off replotting of meridians and parallels
        for pole in Poles:
            Opts['sym'] = sym
            Opts['symsize'] = symsize
            Rlats, Rlons = pmag.pt_rot(pole, [pt_lat], [pt_lon])
            print(Rlats, Rlons)
            pmagplotlib.plot_map(FIG['map'], Rlats, Rlons, Opts)
            if plot == 0 and not IS_WIN:
                pmagplotlib.draw_figs(FIG)
        Opts['sym'] = 'g^'
        Opts['symsize'] = 5
        pmagplotlib.plot_map(FIG['map'], [pole[0]], [pole[1]], Opts)
        if plot == 0 and not IS_WIN:
            pmagplotlib.draw_figs(FIG)
    files = {}
    for key in list(FIG.keys()):
        files[key] = 'Cont_rot'+'.'+fmt
    if plot == 0 and not IS_WIN:
        pmagplotlib.draw_figs(FIG)
    if plot == 1:
        pmagplotlib.save_plots(FIG, files)
        sys.exit()
    if pmagplotlib.isServer:
        black = '#000000'
        purple = '#800080'
        titles = {}
        titles['eq'] = 'Site Map'
        FIG = pmagplotlib.add_borders(FIG, titles, black, purple)
        pmagplotlib.save_plots(FIG, files)
    else:
        pmagplotlib.draw_figs(FIG)
        ans = pmagplotlib.save_or_quit()
        if ans == "a":
            pmagplotlib.save_plots(FIG, files)


if __name__ == "__main__":
    main()

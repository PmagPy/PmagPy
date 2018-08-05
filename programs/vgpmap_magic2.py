#!/usr/bin/env python
# define some variables
import sys
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")

import pmagpy.pmag as pmag
import pmagpy.pmagplotlib as pmagplotlib
import pmagpy.continents as continents


def main():
    """
    NAME
        vgpmap_magic.py

    DESCRIPTION
        makes a map of vgps and a95/dp,dm for site means in a pmag_results table

    SYNTAX
        vgpmap_magic.py [command line options]

    OPTIONS
        -h prints help and quits
        -eye  ELAT ELON [specify eyeball location], default is 90., 0.
        -f FILE pmag_results format file, [default is pmag_results.txt]
        -res [c,l,i,h] specify resolution (crude, low, intermediate, high]
        -etp plot the etopo20 topographpy data (requires high resolution data set)
        -prj PROJ,  specify one of the following:
             ortho = orthographic
             lcc = lambert conformal
             moll = molweide
             merc = mercator
        -sym SYM SIZE: choose a symbol and size, examples:
            ro 5 : small red circles
            bs 10 : intermediate blue squares
            g^ 20 : large green triangles
        -ell  plot dp/dm or a95 ellipses
        -rev RSYM RSIZE : flip reverse poles to normal antipode
        -S:  plot antipodes of all poles
        -age : plot the ages next to the poles
        -crd [g,t] : choose coordinate system, default is to plot all site VGPs
        -fmt [pdf, png, eps...] specify output format, default is pdf
        -sav  save and quit
    DEFAULTS
        FILE: pmag_results.txt
        res:  c
        prj: ortho
        ELAT,ELON = 0,0
        SYM SIZE: ro 8
        RSYM RSIZE: g^ 8

    """
    dir_path = '.'
    res, ages = 'c', 0
    plot = 0
    proj = 'ortho'
    results_file = 'pmag_results.txt'
    ell, flip = 0, 0
    lat_0, lon_0 = 90., 0.
    fmt = 'pdf'
    sym, size = 'ro', 8
    rsym, rsize = 'g^', 8
    anti = 0
    fancy = 0
    coord = ""
    if '-WD' in sys.argv:
        ind = sys.argv.index('-WD')
        dir_path = sys.argv[ind+1]
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-S' in sys.argv:
        anti = 1
    if '-fmt' in sys.argv:
        ind = sys.argv.index('-fmt')
        fmt = sys.argv[ind+1]
    if '-sav' in sys.argv:
        plot = 1
    if '-res' in sys.argv:
        ind = sys.argv.index('-res')
        res = sys.argv[ind+1]
    if '-etp' in sys.argv:
        fancy = 1
    if '-prj' in sys.argv:
        ind = sys.argv.index('-prj')
        proj = sys.argv[ind+1]
    if '-rev' in sys.argv:
        flip = 1
        ind = sys.argv.index('-rev')
        rsym = (sys.argv[ind+1])
        rsize = int(sys.argv[ind+2])
    if '-sym' in sys.argv:
        ind = sys.argv.index('-sym')
        sym = (sys.argv[ind+1])
        size = int(sys.argv[ind+2])
    if '-eye' in sys.argv:
        ind = sys.argv.index('-eye')
        lat_0 = float(sys.argv[ind+1])
        lon_0 = float(sys.argv[ind+2])
    if '-ell' in sys.argv:
        ell = 1
    if '-age' in sys.argv:
        ages = 1
    if '-f' in sys.argv:
        ind = sys.argv.index('-f')
        results_file = sys.argv[ind+1]
    if '-crd' in sys.argv:
        ind = sys.argv.index('-crd')
        crd = sys.argv[ind+1]
        if crd == 'g':
            coord = '0'
        if crd == 't':
            coord = '100'
    results_file = dir_path+'/'+results_file
    data, file_type = pmag.magic_read(results_file)
    if file_type != 'pmag_results':
        print("bad results file")
        sys.exit()
    FIG = {'map': 1}
    pmagplotlib.plot_init(FIG['map'], 6, 6)
    # read in er_sites file
    lats, lons, dp, dm, a95 = [], [], [], [], []
    Pars = []
    dates, rlats, rlons = [], [], []
    if 'data_type' in data[0].keys():
        # get all site level data
        Results = pmag.get_dictitem(data, 'data_type', 'i', 'T')
    else:
        Results = data
    # get all non-blank latitudes
    Results = pmag.get_dictitem(Results, 'vgp_lat', '', 'F')
    # get all non-blank longitudes
    Results = pmag.get_dictitem(Results, 'vgp_lon', '', 'F')
    if coord != "":
        # get specified coordinate system
        Results = pmag.get_dictitem(Results, 'tilt_correction', coord, 'T')
    location = ""
    for rec in Results:
        if rec['er_location_names'] not in location:
            location = location+':'+rec['er_location_names']
        if 'average_age' in rec.keys() and rec['average_age'] != "" and ages == 1:
            dates.append(rec['average_age'])
        lat = float(rec['vgp_lat'])
        lon = float(rec['vgp_lon'])
        if flip == 0:
            lats.append(lat)
            lons.append(lon)
        elif flip == 1:
            if lat < 0:
                rlats.append(-lat)
                lon = lon+180.
                if lon > 360:
                    lon = lon-360.
                rlons.append(lon)
            else:
                lats.append(lat)
                lons.append(lon)
        elif anti == 1:
            lats.append(-lat)
            lon = lon+180.
            if lon > 360:
                lon = lon-360.
            lons.append(lon)
        ppars = []
        ppars.append(lon)
        ppars.append(lat)
        ell1, ell2 = "", ""
        if 'vgp_dm' in rec.keys() and rec['vgp_dm'] != "":
            ell1 = float(rec['vgp_dm'])
        if 'vgp_dp' in rec.keys() and rec['vgp_dp'] != "":
            ell2 = float(rec['vgp_dp'])
        if 'vgp_alpha95' in rec.keys() and rec['vgp_alpha95'] != "":
            ell1, ell2 = float(rec['vgp_alpha95']), float(rec['vgp_alpha95'])
        if ell1 != "" and ell2 != "":
            ppars = []
            ppars.append(lons[-1])
            ppars.append(lats[-1])
            ppars.append(ell1)
            ppars.append(lons[-1])
            isign = abs(lats[-1])/lats[-1]
            ppars.append(lats[-1]-isign*90.)
            ppars.append(ell2)
            ppars.append(lons[-1]+90.)
            ppars.append(0.)
            Pars.append(ppars)
    location = location.strip(':')
    Opts = {'latmin': -90, 'latmax': 90, 'lonmin': 0., 'lonmax': 360., 'lat_0': lat_0, 'lon_0': lon_0,
            'proj': proj, 'sym': 'bs', 'symsize': 3, 'pltgrid': 0, 'res': res, 'boundinglat': 0.}
    Opts['details'] = {'coasts': 1, 'rivers': 0, 'states': 0,
                       'countries': 0, 'ocean': 1, 'fancy': fancy}
    # make the base map with a blue triangle at the pole`
    pmagplotlib.plot_map(FIG['map'], [90.], [0.], Opts)
    Opts['pltgrid'] = -1
    Opts['sym'] = sym
    Opts['symsize'] = size
    if len(dates) > 0:
        Opts['names'] = dates
    if len(lats) > 0:
        # add the lats and lons of the poles
        pmagplotlib.plot_map(FIG['map'], lats, lons, Opts)
    Opts['names'] = []
    if len(rlats) > 0:
        Opts['sym'] = rsym
        Opts['symsize'] = rsize
        # add the lats and lons of the poles
        pmagplotlib.plot_map(FIG['map'], rlats, rlons, Opts)
    if plot == 0:
        pmagplotlib.draw_figs(FIG)
    if ell == 1:  # add ellipses if desired.
        Opts['details'] = {'coasts': 0, 'rivers': 0,
                           'states': 0, 'countries': 0, 'ocean': 0}
        Opts['pltgrid'] = -1  # turn off meridian replotting
        Opts['symsize'] = 2
        Opts['sym'] = 'g-'
        for ppars in Pars:
            if ppars[2] != 0:
                PTS = pmagplotlib.plot_ell(FIG['map'], ppars, 'g.', 0, 0)
                elats, elons = [], []
                for pt in PTS:
                    elons.append(pt[0])
                    elats.append(pt[1])
                # make the base map with a blue triangle at the pole`
                pmagplotlib.plot_map(FIG['map'], elats, elons, Opts)
                if plot == 0:
                    pmagplotlib.draw_figs(FIG)
    files = {}
    for key in FIG.keys():
        if pmagplotlib.isServer:  # use server plot naming convention
            files[key] = 'LO:_'+location+'_VGP_map.'+fmt
        else:  # use more readable plot naming convention
            files[key] = '{}_VGP_map.{}'.format(
                location.replace(' ', '_'), fmt)
    if pmagplotlib.isServer:
        black = '#000000'
        purple = '#800080'
        titles = {}
        titles['eq'] = 'LO:_'+location+'_VGP_map'
        FIG = pmagplotlib.add_borders(FIG, titles, black, purple)
        pmagplotlib.save_plots(FIG, files)
    elif plot == 0:
        pmagplotlib.draw_figs(FIG)
        ans = input(" S[a]ve to save plot, Return to quit:  ")
        if ans == "a":
            pmagplotlib.save_plots(FIG, files)
        else:
            print("Good bye")
            sys.exit()
    else:
        pmagplotlib.save_plots(FIG, files)


if __name__ == "__main__":
    main()

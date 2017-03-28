#!/usr/bin/env python
# -*- python-indent-offset: 4; -*-

from __future__ import division
from __future__ import print_function
from builtins import input
from past.utils import old_div
import sys
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")

import pmagpy.pmagplotlib as pmagplotlib
import pmagpy.pmag as pmag
import pmagpy.new_builder as nb


def main():
    """
    NAME
        dayplot_magic.py

    DESCRIPTION
        makes 'day plots' (Day et al. 1977) and squareness/coercivity,
        plots 'linear mixing' curve from Dunlop and Carter-Stiglitz (2006).
          squareness coercivity of remanence (Neel, 1955) plots after
          Tauxe et al. (2002)

    SYNTAX
        dayplot_magic.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f: specify input hysteresis file, default is specimens.txt
        -fmt [svg,png,jpg] format for output plots
        -sav saves plots and quits quietly
    """
    args = sys.argv
    if "-h" in args:
        print(main.__doc__)
        sys.exit()
    verbose = pmagplotlib.verbose
    dir_path = pmag.get_named_arg_from_sys('-WD', '.')
    fmt = pmag.get_named_arg_from_sys('-fmt', 'svg')
    if '-sav' in sys.argv:
        plots = 1
        verbose = False
    else:
        plots = 0
    infile = pmag.get_named_arg_from_sys("-f", "specimens.txt")
    fnames = {'specimens': infile}
    con = nb.Contribution(dir_path, read_tables=['specimens'],
                          custom_filenames=fnames)
    spec_container = con.tables['specimens']
    spec_df = spec_container.df

    #
    # initialize some variables
    # define figure numbers for Day,S-Bc,S-Bcr
    DSC = {}
    DSC['day'], DSC['S-Bc'], DSC['S-Bcr'], DSC['bcr1-bcr2'] = 1, 2, 3, 4
    pmagplotlib.plot_init(DSC['day'], 5, 5)
    pmagplotlib.plot_init(DSC['S-Bc'], 5, 5)
    pmagplotlib.plot_init(DSC['S-Bcr'], 5, 5)
    pmagplotlib.plot_init(DSC['bcr1-bcr2'], 5, 5)
    S, BcrBc, Bcr2, Bc, hsids, Bcr = [], [], [], [], [], []
    Bcr1, Bcr1Bc, S1 = [], [], []
    locations = ''

    if 'location' in spec_df.columns:
        locations = spec_df['location'].unique()
    do_rem = bool('rem_bcr' in spec_df.columns)

    for ind, row in spec_df.iterrows():
        if row['hyst_bcr'] and row['hyst_mr_moment']:
            S.append(old_div(float(row['hyst_mr_moment']), float(row['hyst_ms_moment'])))
            Bcr.append(float(row['hyst_bcr']))
            Bc.append(float(row['hyst_bc']))
            BcrBc.append(old_div(Bcr[-1], Bc[-1]))
            hsids.append(row['specimen'])
        if do_rem:
            if row['rem_bcr'] and float(row['rem_bcr']) > 0:
                try:
                    Bcr1.append(float(row['rem_bcr']))
                    Bcr1Bc.append(old_div(Bcr1[-1], Bc[-1]))
                    S1.append(S[-1])
                    Bcr2.append(Bcr[-1])
                except ValueError:
                    if verbose:
                        print('hysteresis data for ', row['specimen'], end=' ')
                        print(' not found')

    #
    # now plot the day and S-Bc, S-Bcr plots
    #
    if len(Bcr1) > 0:
        pmagplotlib.plotDay(DSC['day'], Bcr1Bc, S1, 'ro')
        pmagplotlib.plotSBcr(DSC['S-Bcr'], Bcr1, S1, 'ro')
        pmagplotlib.plot_init(DSC['bcr1-bcr2'], 5, 5)
        pmagplotlib.plotBcr(DSC['bcr1-bcr2'], Bcr1, Bcr2)
    else:
        del DSC['bcr1-bcr2']
    pmagplotlib.plotDay(DSC['day'], BcrBc, S, 'bs')
    pmagplotlib.plotSBcr(DSC['S-Bcr'], Bcr, S, 'bs')
    pmagplotlib.plotSBc(DSC['S-Bc'], Bc, S, 'bs')
    files = {}
    if len(locations) > 0:
        locations = locations[:-1]
    for key in list(DSC.keys()):
        if pmagplotlib.isServer: # use server plot naming convention
            files[key] = 'LO:_' + locations + '_' + 'SI:__SA:__SP:__TY:_' + key + '_.' + fmt
        else: # use more readable plot naming convention
            files[key] = '{}_{}.{}'.format(locations, key, fmt)
    if verbose:
        pmagplotlib.drawFIGS(DSC)
        ans = input(" S[a]ve to save plots, return to quit:  ")
        if ans == "a":
            pmagplotlib.saveP(DSC, files)
        else:
            sys.exit()
    if plots:
        pmagplotlib.saveP(DSC, files)


if __name__ == "__main__":
    main()

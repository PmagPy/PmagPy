#!/usr/bin/env python
import os
import sys
import numpy as np
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")
import pandas as pd

from matplotlib import pyplot as plt
import pmagpy.pmag as pmag
import pmagpy.pmagplotlib as pmagplotlib
from pmag_env import set_env

import operator
OPS = {'<' : operator.lt, '<=' : operator.le,
       '>' : operator.gt, '>=': operator.ge, '=': operator.eq}

def main():
    """
    NAME
       foldtest_magic.py

    DESCRIPTION
       does a fold test (Tauxe, 2010) on data

    INPUT FORMAT
       pmag_specimens format file, er_samples.txt format file (for bedding)

    SYNTAX
       foldtest_magic.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f sites  formatted file [default for 3.0 is sites.txt, for 2.5, pmag_sites.txt]
        -fsa samples  formatted file
        -fsi sites  formatted file
        -exc use criteria to set acceptance criteria (supported only for data model 3)
        -n NB, set number of bootstraps, default is 1000
        -b MIN, MAX, set bounds for untilting, default is -10, 150
        -fmt FMT, specify format - default is svg
        -sav saves plots and quits
        -DM NUM MagIC data model number (2 or 3, default 3)

    OUTPUT
        Geographic: is an equal area projection of the input data in
                    original coordinates
        Stratigraphic: is an equal area projection of the input data in
                    tilt adjusted coordinates
        % Untilting: The dashed (red) curves are representative plots of
                    maximum eigenvalue (tau_1) as a function of untilting
                    The solid line is the cumulative distribution of the
                    % Untilting required to maximize tau for all the
                    bootstrapped data sets.  The dashed vertical lines
                    are 95% confidence bounds on the % untilting that yields
                   the most clustered result (maximum tau_1).
        Command line: prints out the bootstrapped iterations and
                   finally the confidence bounds on optimum untilting.
        If the 95% conf bounds include 0, then a pre-tilt magnetization is indicated
        If the 95% conf bounds include 100, then a post-tilt magnetization is indicated
        If the 95% conf bounds exclude both 0 and 100, syn-tilt magnetization is
                possible as is vertical axis rotation or other pathologies

    """
    if '-h' in sys.argv:  # check if help is needed
        print(main.__doc__)
        sys.exit()  # graceful quit

    kappa = 0

    dir_path = pmag.get_named_arg("-WD", ".")
    nboot = int(float(pmag.get_named_arg("-n", 1000)))     # number of bootstraps
    fmt = pmag.get_named_arg("-fmt", "svg")
    data_model_num = int(float(pmag.get_named_arg("-DM", 3)))
    if data_model_num == 3:
        infile = pmag.get_named_arg("-f", 'sites.txt')
        orfile = 'samples.txt'
        site_col = 'site'
        dec_col = 'dir_dec'
        inc_col = 'dir_inc'
        tilt_col = 'dir_tilt_correction'
        dipkey, azkey = 'bed_dip', 'bed_dip_direction'
        crit_col = 'criterion'
        critfile = 'criteria.txt'
    else:
        infile = pmag.get_named_arg("-f", 'pmag_sites.txt')
        orfile = 'er_samples.txt'
        site_col = 'er_site_name'
        dec_col = 'site_dec'
        inc_col = 'site_inc'
        tilt_col = 'site_tilt_correction'
        dipkey, azkey = 'sample_bed_dip', 'sample_bed_dip_direction'
        crit_col = 'pmag_criteria_code'
        critfile = 'pmag_criteria.txt'
    if '-sav' in sys.argv:
        plot = 1
    else:
        plot = 0
    if '-b' in sys.argv:
        ind = sys.argv.index('-b')
        untilt_min = int(sys.argv[ind+1])
        untilt_max = int(sys.argv[ind+2])
    else:
        untilt_min, untilt_max = -10, 150
    if '-fsa' in sys.argv:
        orfile = pmag.get_named_arg("-fsa", "")
    elif '-fsi' in sys.argv:
        orfile = pmag.get_named_arg("-fsi", "")
        if data_model_num == 3:
            dipkey, azkey = 'bed_dip', 'bed_dip_direction'
        else:
            dipkey, azkey = 'site_bed_dip', 'site_bed_dip_direction'
    else:
        if data_model_num == 3:
            orfile = 'sites.txt'
        else:
            orfile = 'pmag_sites.txt'
    orfile = pmag.resolve_file_name(orfile, dir_path)
    infile = pmag.resolve_file_name(infile, dir_path)
    critfile = pmag.resolve_file_name(critfile, dir_path)
    df = pd.read_csv(infile, sep='\t', header=1)
    # keep only records with tilt_col
    data = df.copy()
    data = data[data[tilt_col].notnull()]
    data = data.where(data.notnull(), "")
    # turn into pmag data list
    data = list(data.T.apply(dict))
    # get orientation data
    if data_model_num == 3:
        # often orientation will be in infile (sites table)
        if os.path.split(orfile)[1] == os.path.split(infile)[1]:
            ordata = df[df[azkey].notnull()]
            ordata = ordata[ordata[dipkey].notnull()]
            ordata = list(ordata.T.apply(dict))
        # sometimes orientation might be in a sample file instead
        else:
            ordata = pd.read_csv(orfile, sep='\t', header=1)
            ordata = list(ordata.T.apply(dict))
    else:
        ordata, file_type = pmag.magic_read(orfile)

    if '-exc' in sys.argv:
        crits, file_type = pmag.magic_read(critfile)
        SiteCrits = []
        for crit in crits:
            if crit[crit_col] == "DE-SITE":
                SiteCrits.append(crit)
                #break

# get to work
#
    PLTS = {'geo': 1, 'strat': 2, 'taus': 3}  # make plot dictionary
    if not set_env.IS_WIN:
        pmagplotlib.plot_init(PLTS['geo'], 5, 5)
        pmagplotlib.plot_init(PLTS['strat'], 5, 5)
        pmagplotlib.plot_init(PLTS['taus'], 5, 5)
    if data_model_num == 2:
        GEOrecs = pmag.get_dictitem(data, tilt_col, '0', 'T')
    else:
        GEOrecs = data
    if len(GEOrecs) > 0:  # have some geographic data
        num_dropped = 0
        DIDDs = []  # set up list for dec inc  dip_direction, dip
        for rec in GEOrecs:   # parse data
            dip, dip_dir = 0, -1
            Dec = float(rec[dec_col])
            Inc = float(rec[inc_col])
            orecs = pmag.get_dictitem(
                ordata, site_col, rec[site_col], 'T')
            if len(orecs) > 0:
                if orecs[0][azkey] != "":
                    dip_dir = float(orecs[0][azkey])
                if orecs[0][dipkey] != "":
                    dip = float(orecs[0][dipkey])
            if dip != 0 and dip_dir != -1:
                if '-exc' in sys.argv:
                    keep = 1
                    for site_crit in SiteCrits:
                        crit_name = site_crit['table_column'].split('.')[1]
                        if crit_name and crit_name in rec.keys() and rec[crit_name]:
                            # get the correct operation (<, >=, =, etc.)
                            op = OPS[site_crit['criterion_operation']]
                            # then make sure the site record passes
                            if op(float(rec[crit_name]), float(site_crit['criterion_value'])):
                                keep = 0

                    if keep == 1:
                        DIDDs.append([Dec, Inc, dip_dir, dip])
                    else:
                        num_dropped += 1
                else:
                    DIDDs.append([Dec, Inc, dip_dir, dip])
        if num_dropped:
            print("-W- Dropped {} records because each failed one or more criteria".format(num_dropped))
    else:
        print('no geographic directional data found')
        sys.exit()

    pmagplotlib.plot_eq(PLTS['geo'], DIDDs, 'Geographic')
    data = np.array(DIDDs)
    D, I = pmag.dotilt_V(data)
    TCs = np.array([D, I]).transpose()
    pmagplotlib.plot_eq(PLTS['strat'], TCs, 'Stratigraphic')
    if plot == 0:
        pmagplotlib.draw_figs(PLTS)
    Percs = list(range(untilt_min, untilt_max))
    Cdf, Untilt = [], []
    plt.figure(num=PLTS['taus'])
    print('doing ', nboot, ' iterations...please be patient.....')
    for n in range(nboot):  # do bootstrap data sets - plot first 25 as dashed red line
        if n % 50 == 0:
            print(n)
        Taus = []  # set up lists for taus
        PDs = pmag.pseudo(DIDDs)
        if kappa != 0:
            for k in range(len(PDs)):
                d, i = pmag.fshdev(kappa)
                dipdir, dip = pmag.dodirot(d, i, PDs[k][2], PDs[k][3])
                PDs[k][2] = dipdir
                PDs[k][3] = dip
        for perc in Percs:
            tilt = np.array([1., 1., 1., 0.01*perc])
            D, I = pmag.dotilt_V(PDs*tilt)
            TCs = np.array([D, I]).transpose()
            ppars = pmag.doprinc(TCs)  # get principal directions
            Taus.append(ppars['tau1'])
        if n < 25:
            plt.plot(Percs, Taus, 'r--')
        # tilt that gives maximum tau
        Untilt.append(Percs[Taus.index(np.max(Taus))])
        Cdf.append(float(n) / float(nboot))
    plt.plot(Percs, Taus, 'k')
    plt.xlabel('% Untilting')
    plt.ylabel('tau_1 (red), CDF (green)')
    Untilt.sort()  # now for CDF of tilt of maximum tau
    plt.plot(Untilt, Cdf, 'g')
    lower = int(.025*nboot)
    upper = int(.975*nboot)
    plt.axvline(x=Untilt[lower], ymin=0, ymax=1, linewidth=1, linestyle='--')
    plt.axvline(x=Untilt[upper], ymin=0, ymax=1, linewidth=1, linestyle='--')
    tit = '%i - %i %s' % (Untilt[lower], Untilt[upper], 'Percent Unfolding')
    print(tit)
    plt.title(tit)
    if plot == 0:
        pmagplotlib.draw_figs(PLTS)
        ans = input('S[a]ve all figures, <Return> to quit  \n ')
        if ans != 'a':
            print("Good bye")
            sys.exit()
    files = {}
    for key in list(PLTS.keys()):
        files[key] = ('foldtest_'+'%s' % (key.strip()[:2])+'.'+fmt)
    pmagplotlib.save_plots(PLTS, files)


if __name__ == "__main__":
    main()

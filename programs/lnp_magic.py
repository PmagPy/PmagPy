#!/usr/bin/env python
from __future__ import print_function
from builtins import input
import sys
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")

import pmagpy.pmagplotlib as pmagplotlib
import pmagpy.pmag as pmag


def main():
    """
    NAME
        lnp_magic.py

    DESCRIPTION
       makes equal area projections site by site
         from pmag_specimen formatted file with
         Fisher confidence ellipse using McFadden and McElhinny (1988)
         technique for combining lines and planes

    SYNTAX
        lnp_magic [command line options]

    INPUT
       takes magic formatted pmag_specimens file

    OUPUT
        prints site_name n_lines n_planes K alpha95 dec inc R

    OPTIONS
        -h prints help message and quits
        -f FILE: specify input file, default is 'pmag_specimens.txt'
        -crd [s,g,t]: specify coordinate system, [s]pecimen, [g]eographic, [t]ilt adjusted
                default is specimen
        -fmt [svg,png,jpg] format for plots, default is svg
        -sav save plots and quit
        -P: do not plot
        -F FILE, specify output file of dec, inc, alpha95 data for plotting with plotdi_a and plotdi_e
        -exc use criteria in pmag_criteria.txt
        -DM NUMBER MagIC data model (2 or 3, default 3)
    """
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    dir_path = pmag.get_named_arg_from_sys("-WD", ".")
    data_model = int(float(pmag.get_named_arg_from_sys("-DM", 3)))
    fmt = pmag.get_named_arg_from_sys("-fmt", 'svg')
    if data_model == 2:
        in_file = pmag.get_named_arg_from_sys('-f', 'pmag_specimens.txt')
    else:
        in_file = pmag.get_named_arg_from_sys('-f', 'specimens.txt')
    in_file = pmag.resolve_file_name(in_file, dir_path)
    if '-crd' in sys.argv:
        ind = sys.argv.index("-crd")
        crd = sys.argv[ind+1]
        if crd == 's':
            coord = "-1"
        if crd == 'g':
            coord = "0"
        if crd == 't':
            coord = "100"
    else:
        coord = "-1"

    if '-exc' in sys.argv:
        Crits, file_type = pmag.magic_read(dir_path+'/pmag_criteria.txt')
        for crit in Crits:
            if 'specimen_mad' in crit:
                M = float(crit['specimen_mad'])
            if 'specimen_n' in crit:
                N = float(crit['specimen_n'])
            if 'site_alpha95' in crit:
                acutoff = float(crit['site_alpha95'])
            if 'site_k' in crit:
                kcutoff = float(crit['site_k'])
    else:
        Crits = ""

    out_file = pmag.get_named_arg_from_sys('-F', '')
    if out_file:
        out = open(dir_path+'/'+out_file, 'w')
    if '-P' in sys.argv:
        make_plots = 0  # do not plot
    else:
        make_plots = 1  # do plot
    if '-sav' in sys.argv:
        plot = 1  # save plots and quit
    else:
        plot = 0 # show plots intereactively (if make_plots)
#

    Specs, file_type = pmag.magic_read(in_file)
    if 'specimens' not in file_type:
        print('Error opening ', in_file, file_type)
        sys.exit()
    sitelist = []

    # initialize some variables
    FIG = {}  # plot dictionary
    FIG['eqarea'] = 1  # eqarea is figure 1
    M, N, acutoff, kcutoff = 180., 1, 180., 0.

    if data_model == 2:
        site_col = 'er_site_name'
    else:
        site_col = 'site'

    for rec in Specs:
        if rec[site_col] not in sitelist:
            sitelist.append(rec[site_col])
    sitelist.sort()
    if make_plots == 1:
        EQ = {}
        EQ['eqarea'] = 1
    for site in sitelist:
        pmagplotlib.plot_init(EQ['eqarea'], 4, 4)
        print(site)
        data = []
        for spec in Specs:
            if 'specimen_tilt_correction' not in list(spec.keys()):
                spec['specimen_tilt_correction'] = '-1'  # assume unoriented
            if spec['er_site_name'] == site:
                if 'specimen_mad' not in list(spec.keys()) or spec['specimen_mad'] == "":
                    if 'specimen_alpha95' in list(spec.keys()) and spec['specimen_alpha95'] != "":
                        spec['specimen_mad'] = spec['specimen_alpha95']
                    else:
                        spec['specimen_mad'] = '180'
                if spec['specimen_tilt_correction'] == coord and float(spec['specimen_mad']) <= M and float(spec['specimen_n']) >= N:
                    rec = {}
                    for key in list(spec.keys()):
                        rec[key] = spec[key]
                    rec["dec"] = float(spec['specimen_dec'])
                    rec["inc"] = float(spec['specimen_inc'])
                    rec["tilt_correction"] = spec['specimen_tilt_correction']
                    data.append(rec)
        if len(data) > 2:
            fpars = pmag.dolnp(data, 'specimen_direction_type')
            print("Site lines planes  kappa   a95   dec   inc")
            print(site, fpars["n_lines"], fpars["n_planes"], fpars["K"],
                  fpars["alpha95"], fpars["dec"], fpars["inc"], fpars["R"])
            if out_file != "":
                if float(fpars["alpha95"]) <= acutoff and float(fpars["K"]) >= kcutoff:
                    out.write('%s %s %s\n' %
                              (fpars["dec"], fpars['inc'], fpars['alpha95']))
            print('% tilt correction: ', coord)
            if make_plots == 1:
                files = {}
                files['eqarea'] = site+'_'+crd+'_'+'eqarea'+'.'+fmt
                pmagplotlib.plotLNP(EQ['eqarea'], site,
                                    data, fpars, 'specimen_direction_type')
                if plot == 0:
                    pmagplotlib.drawFIGS(EQ)
                    ans = input(
                        "s[a]ve plot, [q]uit, <return> to continue:\n ")
                    if ans == "a":
                        pmagplotlib.saveP(EQ, files)
                    if ans == "q":
                        sys.exit()
                else:
                    pmagplotlib.saveP(EQ, files)
        else:
            print('skipping site - not enough data with specified coordinate system')


if __name__ == "__main__":
    main()

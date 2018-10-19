#!/usr/bin/env python
import sys
import os
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")
import numpy as np

import pmagpy.pmagplotlib as pmagplotlib
import pmagpy.pmag as pmag
from pmagpy import contribution_builder as cb


def main():
    """
    NAME
        lnp_magic.py

    DESCRIPTION
       makes equal area projections site by site
         from specimen formatted file with
         Fisher confidence ellipse using McFadden and McElhinny (1988)
         technique for combining lines and planes

    SYNTAX
        lnp_magic [command line options]

    INPUT
       takes magic formatted specimens file

    OUPUT
        prints site_name n_lines n_planes K alpha95 dec inc R

    OPTIONS
        -h prints help message and quits
        -f FILE: specify input file, default is 'specimens.txt', ('pmag_specimens.txt' for legacy data model 2)
        -fsa FILE: specify samples file, required to plot by site for data model 3 (otherwise will plot by sample)
                default is 'samples.txt'
        -crd [s,g,t]: specify coordinate system, [s]pecimen, [g]eographic, [t]ilt adjusted
                default is specimen
        -fmt [svg,png,jpg] format for plots, default is svg
        -sav save plots and quit
        -P: do not plot
        -F FILE, specify output file of dec, inc, alpha95 data for plotting with plotdi_a and plotdi_e
        -exc use criteria in criteria table # NOT IMPLEMENTED
        -DM NUMBER MagIC data model (2 or 3, default 3)
    """
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    dir_path = pmag.get_named_arg("-WD", ".")
    data_model = int(float(pmag.get_named_arg("-DM", 3)))
    fmt = pmag.get_named_arg("-fmt", 'svg')
    if data_model == 2:
        in_file = pmag.get_named_arg('-f', 'pmag_specimens.txt')
        crit_file = "pmag_criteria.txt"
    else:
        in_file = pmag.get_named_arg('-f', 'specimens.txt')
        samp_file = pmag.get_named_arg('-fsa', 'samples.txt')
        crit_file = "criteria.txt"
    in_file = pmag.resolve_file_name(in_file, dir_path)
    dir_path = os.path.split(in_file)[0]
    if data_model == 3:
        samp_file = pmag.resolve_file_name(samp_file, dir_path)
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


    out_file = pmag.get_named_arg('-F', '')
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


    if data_model == 2:
        Specs, file_type = pmag.magic_read(in_file)
        if 'specimens' not in file_type:
            print('Error opening ', in_file, file_type)
            sys.exit()
    else:
        fnames = {'specimens': in_file, 'samples': samp_file}
        con = cb.Contribution(dir_path, read_tables=['samples', 'specimens'],
                              custom_filenames=fnames)
        con.propagate_name_down('site', 'specimens')
        if 'site' in con.tables['specimens'].df.columns:
            site_col = 'site'
        else:
            site_col = 'sample'
        tilt_corr_col = "dir_tilt_correction"
        mad_col = "dir_mad_free"
        alpha95_col = "dir_alpha95"
        site_alpha95_col = "dir_alpha95"
        dec_col = "dir_dec"
        inc_col = "dir_inc"
        num_meas_col = "dir_n_measurements"
        k_col = "dir_k"
        cols = [site_col, tilt_corr_col, mad_col, alpha95_col, dec_col, inc_col]
        con.tables['specimens'].front_and_backfill(cols)
        con.tables['specimens'].df = con.tables['specimens'].df.where(con.tables['specimens'].df.notnull(), "")
        Specs = con.tables['specimens'].convert_to_pmag_data_list()


    ## using criteria file was never fully implemented
    #if '-exc' in sys.argv:
    #    Crits, file_type = pmag.magic_read(pmag.resolve_file_name(crit_file, dir_path))
    #    for crit in Crits:
    #        if mad_col in crit:
    #            M = float(crit['specimen_mad'])
    #        if num_meas_col in crit:
    #            N = float(crit['specimen_n'])
    #        if site_alpha95_col in crit and 'site' in crit:
    #            acutoff = float(crit['site_alpha95'])
    #        if k_col in crit:
    #            kcutoff = float(crit['site_k'])
    #else:
    #    Crits = ""

    sitelist = []

    # initialize some variables
    FIG = {}  # plot dictionary
    FIG['eqarea'] = 1  # eqarea is figure 1
    M, N, acutoff, kcutoff = 180., 1, 180., 0.

    if data_model == 2:
        site_col = 'er_site_name'
        tilt_corr_col = "specimen_tilt_correction"
        mad_col = "specimen_mad"
        alpha95_col = 'specimen_alpha95'
        dec_col = "specimen_dec"
        inc_col = "specimen_inc"
        num_meas_col = "specimen_n"
        site_alpha95_col = "site_alpha95"
    else: # data model 3
        pass

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
            if tilt_corr_col not in list(spec.keys()):
                spec[tilt_corr_col] = '-1'  # assume unoriented
            if spec[site_col] == site:
                if mad_col not in list(spec.keys()) or spec[mad_col] == "":
                    if alpha95_col in list(spec.keys()) and spec[alpha95_col] != "":
                        spec[mad_col] = spec[alpha95_col]
                    else:
                        spec[mad_col] = '180'
                if not spec[num_meas_col]:
                    continue
                if (float(spec[tilt_corr_col]) == float(coord)) and (float(spec[mad_col]) <= M) and (float(spec[num_meas_col]) >= N):
                    rec = {}
                    for key in list(spec.keys()):
                        rec[key] = spec[key]
                    rec["dec"] = float(spec[dec_col])
                    rec["inc"] = float(spec[inc_col])
                    rec["tilt_correction"] = spec[tilt_corr_col]
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
                pmagplotlib.plot_lnp(EQ['eqarea'], site,
                                    data, fpars, 'specimen_direction_type')
                if plot == 0:
                    pmagplotlib.draw_figs(EQ)
                    ans = input(
                        "s[a]ve plot, [q]uit, <return> to continue:\n ")
                    if ans == "a":
                        pmagplotlib.save_plots(EQ, files)
                    if ans == "q":
                        sys.exit()
                else:
                    pmagplotlib.save_plots(EQ, files)
        else:
            print('skipping site - not enough data with specified coordinate system')


if __name__ == "__main__":
    main()

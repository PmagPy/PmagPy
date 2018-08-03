#!/usr/bin/env python
# -*- python-indent-offset: 4; -*-

# -*- mode: python-mode; python-indent-offset: 4 -*-
import sys
import os
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")

import pmagpy.pmag as pmag
import pmagpy.pmagplotlib as pmagplotlib
import pmagpy.contribution_builder as cb


def main():
    """
    NAME
        dmag_magic.py

    DESCRIPTION
       plots intensity decay curves for demagnetization experiments

    SYNTAX
        dmag_magic -h [command line options]

    INPUT
       takes magic formatted magic_measurements.txt files

    OPTIONS
        -h prints help message and quits
        -f FILE: specify input file, default is: measurements.txt
        -obj OBJ: specify  object  [loc, sit, sam, spc] for plot,
               default is by location
        -LT [AF,T,M]: specify lab treatment type, default AF
        -XLP [PI]: exclude specific  lab protocols,
               (for example, method codes like LP-PI)
        -N do not normalize by NRM magnetization
        -sav save plots silently and quit
        -fmt [svg,jpg,png,pdf] set figure format [default is svg]
    NOTE
        loc: location (study); sit: site; sam: sample; spc: specimen
    """
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    # initialize variables from command line + defaults
    FIG = {}  # plot dictionary
    FIG['demag'] = 1  # demag is figure 1
    in_file = pmag.get_named_arg("-f", default_val="measurements.txt")
    plot_by = pmag.get_named_arg("-obj", default_val="loc")
    name_dict = {'loc': 'location', 'sit': 'site',
                 'sam': 'sample', 'spc': 'specimen'}
    plot_key = name_dict[plot_by]
    LT = "LT-" + pmag.get_named_arg("-LT", "AF") + "-Z"
    if LT == "LT-T-Z":
        units, dmag_key = 'K', 'treat_temp'
    elif LT == "LT-AF-Z":
        units, dmag_key = 'T', 'treat_ac_field'
    elif LT == 'LT-M-Z':
        units, dmag_key = 'J', 'treat_mw_energy'
    else:
        units = 'U'
    no_norm = pmag.get_flag_arg_from_sys("-N")
    norm = 0 if no_norm else 1
    no_plot = pmag.get_flag_arg_from_sys("-sav")
    plot = 0 if no_plot else 1
    fmt = pmag.get_named_arg("-fmt", "svg")
    XLP = pmag.get_named_arg("-XLP", "")
    dir_path = pmag.get_named_arg("-WD", os.getcwd())
    spec_file = pmag.get_named_arg("-fsp", default_val="specimens.txt")
    samp_file = pmag.get_named_arg("-fsa", default_val="samples.txt")
    site_file = pmag.get_named_arg("-fsi", default_val="sites.txt")

    # create contribution and add required headers
    fnames = {"specimens": spec_file, "samples": samp_file, 'sites': site_file}
    contribution = cb.Contribution(dir_path, single_file=in_file,
                                   custom_filenames=fnames)
    file_type = list(contribution.tables.keys())[0]
    print(len(contribution.tables['measurements'].df), ' records read from ', in_file)
    # add plot_key into measurements table
    if plot_key not in contribution.tables['measurements'].df.columns:
        #contribution.propagate_name_down(plot_key, 'measurements')
        contribution.propagate_location_to_measurements()
    data_container = contribution.tables[file_type]
    # pare down to only records with useful data
    # grab records that have the requested code
    data_slice = data_container.get_records_for_code(LT)
    # and don't have the offending code
    data = data_container.get_records_for_code(XLP, incl=False, use_slice=True,
                                               sli=data_slice, strict_match=False)

    # make sure quality is in the dataframe
    if 'quality' not in data.columns:
        data['quality'] = 'g'
    # get intensity key and make sure intensity data is not blank
    intlist = ['magn_moment', 'magn_volume', 'magn_mass']
    IntMeths = [col_name for col_name in data.columns if col_name in intlist]
    # get rid of any entirely blank intensity columns
    for col_name in IntMeths:
        if not data[col_name].any():
            data.drop(col_name, axis=1, inplace=True)
    IntMeths = [col_name for col_name in data.columns if col_name in intlist]
    if len(IntMeths) == 0:
        print('No intensity headers found')
        sys.exit()

    int_key = IntMeths[0] # plot first intensity method found - normalized to initial value anyway - doesn't matter which used
    data = data[data[int_key].notnull()]
    # make list of individual plots
    # by default, will be by location_name
    plotlist = data[plot_key].unique()
    plotlist.sort()
    pmagplotlib.plot_init(FIG['demag'], 5, 5)
    # iterate through and plot the data
    for plt in plotlist:
        plot_data = data[data[plot_key] == plt].copy()
        if plot:
            print(plt, 'plotting by: ', plot_key)
        if len(plot_data) > 2:
            title = plt
            spcs = []
            spcs = plot_data['specimen'].unique()
            for spc in spcs:
                INTblock = []
                spec_data = plot_data[plot_data['specimen'] == spc]
                for ind, rec in spec_data.iterrows():
                    INTblock.append([float(rec[dmag_key]), 0, 0, float(rec[int_key]), 1, rec['quality']])
                if len(INTblock) > 2:
                    pmagplotlib.plot_mag(FIG['demag'], INTblock,
                                       title, 0, units, norm)

            if not plot:
                files = {}
                for key in list(FIG.keys()):
                    files[key] = title + '_' + LT + '.' + fmt
                pmagplotlib.save_plots(FIG, files)
                #sys.exit()
            else:
                pmagplotlib.draw_figs(FIG)
                prompt = " S[a]ve to save plot, [q]uit,  Return to continue:  "
                ans = input(prompt)
                if ans == 'q':
                    sys.exit()
                if ans == "a":
                    files = {}
                    for key in list(FIG.keys()):
                        files[key] = title + '_' + LT + '.' + fmt
                    pmagplotlib.save_plots(FIG, files)
            pmagplotlib.clearFIG(FIG['demag'])

if __name__ == "__main__":
    main()

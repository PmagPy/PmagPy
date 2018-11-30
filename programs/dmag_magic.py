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


def plot(in_file="measurements.txt", dir_path=".", input_dir_path="",
         spec_file="specimens.txt", samp_file="samples.txt",
         site_file="sites.txt", loc_file="locations.txt",
         plot_by="loc", LT="AF", norm=True, XLP="",
         save_plots=True, fmt="svg"):

    """
    plots intensity decay curves for demagnetization experiments

    Parameters
    ----------
    in_file : str, default "measurements.txt"
    dir_path : str
        output directory, default "."
    input_dir_path : str
        input file directory (if different from dir_path), default ""
    spec_file : str
        input specimen file name, default "specimens.txt"
    samp_file: str
        input sample file name, default "samples.txt"
    site_file : str
        input site file name, default "sites.txt"
    loc_file : str
        input location file name, default "locations.txt"
    plot_by : str
        [spc, sam, sit, loc] (specimen, sample, site, location), default "loc"
    LT : str
        lab treatment [T, AF, M], default AF
    norm : bool
        normalize by NRM magnetization, default True
    XLP : str
        exclude specific  lab protocols, (for example, method codes like LP-PI)
        default ""
    save_plots : bool
        plot and save non-interactively, default True
    fmt : str
        ["png", "svg", "pdf", "jpg"], default "svg"

    Returns
    ---------
    type - Tuple : (True or False indicating if conversion was sucessful, file name(s) written)

    """
    dir_path = os.path.realpath(dir_path)
    if not input_dir_path:
        input_dir_path = dir_path
    input_dir_path = os.path.realpath(input_dir_path)

    # format plot_key
    name_dict = {'loc': 'location', 'sit': 'site',
                 'sam': 'sample', 'spc': 'specimen'}
    if plot_by not in name_dict.values():
        try:
            plot_key = name_dict[plot_by]
        except KeyError:
            print('Unrecognized plot_by {}, falling back to plot by location'.format(plot_by))
            plot_key = "loc"
    else:
        plot_key = plot_by


    # figure out what kind of experiment
    LT = "LT-" + LT + "-Z"
    print('LT', LT)
    if LT == "LT-T-Z":
        units, dmag_key = 'K', 'treat_temp'
    elif LT == "LT-AF-Z":
        units, dmag_key = 'T', 'treat_ac_field'
    elif LT == 'LT-M-Z':
        units, dmag_key = 'J', 'treat_mw_energy'
    else:
        units = 'U'


    # init
    FIG = {}  # plot dictionary
    FIG['demag'] = 1  # demag is figure 1
    # create contribution and add required headers
    fnames = {"specimens": spec_file, "samples": samp_file,
              'sites': site_file, 'locations': loc_file}
    if not os.path.exists(pmag.resolve_file_name(in_file, input_dir_path)):
        print('-E- Could not find {}'.format(in_file))
        return False, []
    contribution = cb.Contribution(input_dir_path, single_file=in_file,
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
        print('-E- No intensity headers found')
        return False, []

    int_key = IntMeths[0] # plot first intensity method found - normalized to initial value anyway - doesn't matter which used
    data = data[data[int_key].notnull()]
    # make list of individual plots
    # by default, will be by location_name
    plotlist = data[plot_key].unique()
    plotlist.sort()
    pmagplotlib.plot_init(FIG['demag'], 5, 5)
    last_plot = False
    # iterate through and plot the data
    for plt in plotlist:
        if plt == plotlist[-1]:
            last_plot = True
        plot_data = data[data[plot_key] == plt].copy()
        if not save_plots:
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

            if save_plots:
                files = {}
                for key in list(FIG.keys()):
                    if pmagplotlib.isServer:
                        files[key] = title + '_' + LT + '.' + fmt
                        incl_dir = False
                    else: # if not server, include directory in output path
                        files[key] = os.path.join(dir_path, title + '_' + LT + '.' + fmt)
                        incl_dir = True

                pmagplotlib.save_plots(FIG, files, incl_directory=incl_dir)
            else:
                pmagplotlib.draw_figs(FIG)
                prompt = " S[a]ve to save plot, [q]uit,  Return to continue:  "
                ans = input(prompt)
                if ans == 'q':
                    return True, []
                if ans == "a":
                    files = {}
                    for key in list(FIG.keys()):
                        if pmagplotlib.isServer:
                            files[key] = title + '_' + LT + '.' + fmt
                            incl_dir = False
                        else: # if not server, include directory in output path
                            files[key] = os.path.join(dir_path, title + '_' + LT + '.' + fmt)
                            incl_dir = True
                    pmagplotlib.save_plots(FIG, files, incl_directory=incl_dir)
            pmagplotlib.clearFIG(FIG['demag'])
    if last_plot:
        return True, []



def main():
    """
    NAME
        dmag_magic.py

    DESCRIPTION
       plots intensity decay curves for demagnetization experiments

    SYNTAX
        dmag_magic -h [command line options]

    INPUT
       takes magic formatted measurements.txt files

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
    dir_path = pmag.get_named_arg("-WD", default_val=".")
    input_dir_path = pmag.get_named_arg('-ID', '')
    if not input_dir_path:
        input_dir_path = dir_path
    in_file = pmag.get_named_arg("-f", default_val="measurements.txt")
    in_file = pmag.resolve_file_name(in_file, input_dir_path)
    if "-ID" not in sys.argv:
        input_dir_path = os.path.split(in_file)[0]
    plot_by = pmag.get_named_arg("-obj", default_val="loc")
    LT = pmag.get_named_arg("-LT", "AF")
    no_norm = pmag.get_flag_arg_from_sys("-N")
    norm = False if no_norm else True
    save_plots = pmag.get_flag_arg_from_sys("-sav")
    fmt = pmag.get_named_arg("-fmt", "svg")
    XLP = pmag.get_named_arg("-XLP", "")
    spec_file = pmag.get_named_arg("-fsp", default_val="specimens.txt")
    samp_file = pmag.get_named_arg("-fsa", default_val="samples.txt")
    site_file = pmag.get_named_arg("-fsi", default_val="sites.txt")
    loc_file = pmag.get_named_arg("-flo", default_val="locations.txt")
    plot(in_file, dir_path, input_dir_path, spec_file, samp_file,
         site_file, loc_file, plot_by, LT, norm, XLP,
         save_plots, fmt)

if __name__ == "__main__":
    main()

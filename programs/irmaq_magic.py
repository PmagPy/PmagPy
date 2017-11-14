#!/usr/bin/env python
from __future__ import print_function
from builtins import input
import sys
import os
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")

import pmagpy.pmag as pmag
from pmagpy import new_builder as nb
import pmagpy.pmagplotlib as pmagplotlib


def main():
    """
    NAME
        irmaq_magic.py

    DESCRIPTION
       plots IRM acquisition curves from measurements file

    SYNTAX
        irmaq_magic [command line options]

    INPUT
       takes magic formatted magic_measurements.txt files

    OPTIONS
        -h prints help message and quits
        -f FILE: specify input file, default is: magic_measurements.txt/measurements.txt
        -obj OBJ: specify  object  [loc, sit, sam, spc] for plot, default is by location
        -N ; do not normalize by last point - use original units
        -fmt [png,jpg,eps,pdf] set plot file format [default is svg]
        -sav save plot[s] and quit
        -DM MagIC data model number, default is 3
    NOTE
        loc: location (study); sit: site; sam: sample; spc: specimen
    """
    FIG = {}  # plot dictionary
    FIG['exp'] = 1  # exp is figure 1
    dir_path = './'
    plot, fmt = 0, 'svg'
    units = 'T',
    XLP = []
    norm = 1
    LP = "LP-IRM"
    if len(sys.argv) > 1:
        if '-h' in sys.argv:
            print(main.__doc__)
            sys.exit()
        data_model = int(pmag.get_named_arg_from_sys("-DM", 3))
        if '-N' in sys.argv:
            norm = 0
        if '-sav' in sys.argv:
            plot = 1
        if '-fmt' in sys.argv:
            ind = sys.argv.index("-fmt")
            fmt = sys.argv[ind + 1]
        if data_model == 3:
            in_file = pmag.get_named_arg_from_sys("-f", 'measurements.txt')
        else:
            in_file = pmag.get_named_arg_from_sys("-f", 'magic_measurements.txt')
        if '-WD' in sys.argv:
            ind = sys.argv.index('-WD')
            dir_path = sys.argv[ind + 1]
        dir_path = os.path.realpath(dir_path)
        in_file = pmag.resolve_file_name(in_file, dir_path)
        if '-WD' not in sys.argv:
            dir_path = os.path.split(in_file)[0]
        plot_by = pmag.get_named_arg_from_sys("-obj", "loc")
        if data_model == 3:
            plot_key = 'location'
            if plot_by == 'sit':
                plot_key = 'site'
            if plot_by == 'sam':
                plot_key = 'sample'
            if plot_by == 'spc':
                plot_key = 'specimen'
        else:
            plot_key = 'er_location_name'
            if plot_by == 'sit':
                plot_key = 'er_site_name'
            if plot_by == 'sam':
                plot_key = 'er_sample_name'
            if plot_by == 'spc':
                plot_key = 'er_specimen_name'

    # set defaults and get more information if needed
    if data_model == 3:
        dmag_key = 'treat_dc_field'
    else:
        dmag_key = 'treatment_dc_field'
    #
    if data_model == 3 and plot_key != 'specimen':
        # gonna need to read in more files
        print('-W- You are trying to plot measurements by {}'.format(plot_key))
        print('    By default, this information is not available in your measurement file.')
        print('    Trying to acquire this information from {}'.format(dir_path))
        con = nb.Contribution(dir_path)
        meas_df = con.propagate_location_to_measurements()
        if plot_key not in meas_df.columns:
            print('-W- Could not find required data.')
            print('    Try a different plot key.')
            return
        else:
            print('-I- Found {} information, continuing with plotting'.format(plot_key))
        con.write_table_to_file('measurements')

    # read in data
    data, file_type = pmag.magic_read(in_file)
    sids = pmag.get_specs(data)
    pmagplotlib.plot_init(FIG['exp'], 6, 6)
    #
    #
    # find desired intensity data
    #
    # get plotlist
    #
    plotlist = []
    if data_model == 3:
        intlist = ['magn_moment', 'magn_volume', 'magn_mass', 'magnitude']
    else:
        intlist = ['measurement_magnitude', 'measurement_magn_moment',
                    'measurement_magn_volume', 'measurement_magn_mass']
    IntMeths = []
    # get all the records with this lab protocol
    #print('data', len(data))
    #print('data[0]', data[0])
    if data_model == 3:
        data = pmag.get_dictitem(data, 'method_codes', LP, 'has')
    else:
        data = pmag.get_dictitem(data, 'magic_method_codes', LP, 'has')
    Ints = {}
    NoInts, int_key = 1, ""
    for key in intlist:
        # get all non-blank data for intensity type
        Ints[key] = pmag.get_dictitem(data, key, '', 'F')
        if len(Ints[key]) > 0:
            NoInts = 0
            if int_key == "":
                int_key = key
    if NoInts == 1:
        print('No intensity information found')
        sys.exit()
    for rec in Ints[int_key]:
        if rec[plot_key] not in plotlist:
            plotlist.append(rec[plot_key])
    plotlist.sort()
    for plt in plotlist:
        print(plt)
        INTblock = []
        # get data with right intensity info whose plot_key matches plot
        data = pmag.get_dictitem(Ints[int_key], plot_key, plt, 'T')
        # get a list of specimens with appropriate data
        sids = pmag.get_specs(data)
        if len(sids) > 0:
            title = data[0][plot_key]
        for s in sids:
            INTblock = []
            # get data for each specimen
            if data_model == 3:
                sdata = pmag.get_dictitem(data, 'specimen', s, 'T')
            else:
                sdata = pmag.get_dictitem(data, 'er_specimen_name', s, 'T')
            for rec in sdata:
                INTblock.append([float(rec[dmag_key]), 0, 0,
                                 float(rec[int_key]), 1, 'g'])
            pmagplotlib.plotMT(FIG['exp'], INTblock, title, 0, units, norm)
        files = {}
        for key in list(FIG.keys()):
            files[key] = title + '_' + LP + '.' + fmt
        if plot == 0:
            pmagplotlib.drawFIGS(FIG)
            ans = input(" S[a]ve to save plot, [q]uit,  Return to continue:  ")
            if ans == 'q':
                sys.exit()
            if ans == "a":
                pmagplotlib.saveP(FIG, files)
        else:
            pmagplotlib.saveP(FIG, files)
        pmagplotlib.clearFIG(FIG['exp'])


if __name__ == "__main__":
    main()

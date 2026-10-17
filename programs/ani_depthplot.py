#!/usr/bin/env pythonw

import wx
import os
import sys
import matplotlib
from pmag_env import set_env
set_env.set_backend_if_unset("WXAgg")

import matplotlib.pylab as plt
import pmagpy.command_line_extractor as extractor
import pmagpy.ipmag as ipmag
import dialogs.pmag_widgets as pw
import dialogs.pmag_menu_dialogs as pmag_menu_dialogs

def main():
    """
    NAME
        ani_depthplot.py

    DESCRIPTION
        plots tau, V3_inc, V1_dec, P and chi versus core_depth

    SYNTAX
        ani_depthplot.py [command line optins]
        # or, for Anaconda users:
        ani_depthplot_anaconda [command line options]


    OPTIONS
        -h prints help message and quits
        -f FILE: ignored (formerly the MagIC 2 rmag_anisotropy file)
        -fb FILE: specify input measurements format file from magic
        -fsa FILE: specify input sample format file from magic
        -fsp FILE: specify input specimen file
        -fsum FILE : specify input LIMS database (IODP) core summary csv file
                to print the core names, set lab to 1
        -fa FILE: specify input ages format file from magic
        -d min max [in m] depth range to plot
        -ds [mcd,mbsf], specify depth scale, default is mbsf (core depth)
        -sav save plot without review
        -fmt specfiy format for figures - default is svg
        -DM DATA_MODEL: MagIC Data Model 3 is the only supported model;
            convert Data Model 2 files to Data Model 3 first
     DEFAULTS:
         Anisotropy file: specimens.txt
         Bulk susceptibility file: measurements.txt
         Samples file: samples.txt
    """


    args = sys.argv
    if '-h' in args:
        print(main.__doc__)
        sys.exit()
    # 'f' is required in the extractor's default table, so it stays listed as optional
    dataframe = extractor.command_line_dataframe([['f', False, ''],
                                                  ['fb', False, 'measurements.txt'],
                                                  ['fsa', False, 'samples.txt'],
                                                  ['fa', False, None], ['fsum', False, None],
                                                  ['fmt', False, 'svg'], ['ds', False, 'mbsf'],
                                                  ['d', False, '-1 -1'], ['sav', False, False],
                                                  ['WD', False, '.' ], ['DM', False, 3],
                                                  ['fsp', False, 'specimens.txt']])
        #args = sys.argv
    checked_args = extractor.extract_and_check_args(args, dataframe)
    meas_file, samp_file, age_file, sum_file, fmt, depth_scale, depth, save_quietly, dir_path, data_model, spec_file = extractor.get_vars(['fb', 'fsa', 'fa', 'fsum', 'fmt', 'ds', 'd', 'sav', 'WD', 'DM', 'fsp'], checked_args)

    if int(float(data_model)) != 3:
        raise SystemExit(
            "-E- ani_depthplot supports MagIC Data Model 3 only. "
            "Convert Data Model 2 files to Data Model 3 before plotting."
        )

    # format min/max depth
    try:
        dmin, dmax = depth.split()
        dmin, dmax = float(dmin), float(dmax)
    except Exception:
        print('you must provide depth in this format: -d dmin dmax')
        print('could not parse "{}", defaulting to plotting all depths'.format('-d ' + str(depth)))
        dmin, dmax = -1, -1

    if depth_scale:
        if depth_scale not in ['age', 'mbsf', 'mcd']:
            print('-W- Unrecognized option "{}" provided for depth scale.\n    Options for depth scale are mbsf (meters below sea floor) or mcd (meters composite depth).\n    Alternatively, if you provide an age file the depth scale will be automatically set to plot by age instead.\n    Using default "mbsf"'.format(depth_scale))
            depth_scale = 'sample_core_depth'
        if age_file:
            depth_scale = 'age'
        elif 'mbsf' in depth_scale:
            depth_scale = 'sample_core_depth'
        elif 'mcd' in depth_scale:
            depth_scale = 'sample_composite_depth'

    site_file = 'sites.txt'
    fig, fignames = ipmag.ani_depthplot(spec_file, samp_file, meas_file, site_file, age_file, sum_file, fmt, dmin, dmax, depth_scale, dir_path)
    figname = fignames[0]
    if save_quietly:
        if dir_path == '.':
            dir_path = os.getcwd()
        plt.savefig(figname)
        plt.clf()
        print('Saved file: {}'.format(figname))
        return False

    app = wx.App(redirect=False)
    if not fig:
        pw.simple_warning('No plot was able to be created with the data you provided.\nMake sure you have given all the required information and try again')
        return False

    dpi = fig.get_dpi()
    pixel_width = dpi * fig.get_figwidth()
    pixel_height = dpi * fig.get_figheight()
    figname = os.path.join(dir_path, figname)
    plot_frame = pmag_menu_dialogs.PlotFrame((int(pixel_width), int(pixel_height + 50)),
                                             fig, figname, standalone=True)

    app.MainLoop()

if __name__ == "__main__":
    main()

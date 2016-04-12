#!/usr/bin/env python
import wx
import os
import sys
import matplotlib
if matplotlib.get_backend() != "WXAgg":
  matplotlib.use("WXAgg")

import matplotlib.pyplot as plt
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

    OPTIONS
        -h prints help message and quits
        -f FILE: specify input rmag_anisotropy format file from magic
        -fb FILE: specify input magic_measurements format file from magic
        -fsa FILE: specify input er_samples format file from magic 
        -fsum FILE : specify input LIMS database (IODP) core summary csv file
                to print the core names, set lab to 1
        -fa FILE: specify input er_ages format file from magic 
        -d min max [in m] depth range to plot
        -ds [mcd,mbsf], specify depth scale, default is mbsf
        -sav save plot without review
        -fmt specfiy format for figures - default is svg
     DEFAULTS:
         Anisotropy file: rmag_anisotropy.txt
         Bulk susceptibility file: magic_measurements.txt
         Samples file: er_samples.txt
    """


    args = sys.argv
    if '-h' in args:
        print main.__doc__
        sys.exit()
    dataframe = extractor.command_line_dataframe([['f', False, 'rmag_anisotropy.txt'],
                                                  ['fb', False, 'magic_measurements.txt'],
                                                  ['fsa', False, 'er_samples.txt'],
                                                  ['fa', False, None], ['fsum', False, None],
                                                  ['fmt', False, 'svg'], ['ds', False, 'mbsf'],
                                                  ['d', False, '-1 -1'], ['sav', False, False],
                                                  ['WD', False, '.' ]])
        #args = sys.argv
    checked_args = extractor.extract_and_check_args(args, dataframe)
    ani_file, meas_file, samp_file, age_file, sum_file, fmt, depth_scale, depth, save_quietly, dir_path = extractor.get_vars(['f', 'fb', 'fsa', 'fa', 'fsum', 'fmt', 'ds', 'd', 'sav', 'WD'], checked_args)

    # format min/max depth
    try:
        dmin, dmax = depth.split()
        dmin, dmax = float(dmin), float(dmax)
    except:
        print 'you must provide depth in this format: -d dmin dmax'
        print 'could not parse "{}", defaulting to plotting all depths'.format('-d ' + str(depth))
        dmin, dmax = -1, -1

    if depth_scale:
        if age_file:
            depth_scale = 'age'
        elif 'mbsf' in depth_scale:
            depth_scale = 'sample_core_depth'
        elif 'mcd' in depth_scale:
            depth_scale = 'sample_composite_depth'
        else:
            print 'Warning: Unrecognized option "{}" provided for depth scale.\nOptions for depth scale are mbsf -- meters below sea floor -- or mcd -- meters composite depth.\nAlternatively, if you provide an age file the depth scale will be automatically set to plot by age instead.\nUsing default "mbsf"'.format(depth_scale)
            depth_scale = 'sample_composite_depth'
            
    fig, figname = ipmag.aniso_depthplot(ani_file, meas_file, samp_file, age_file, sum_file, fmt, dmin, dmax, depth_scale, dir_path)
    if save_quietly:
        if dir_path == '.':
            dir_path = os.getcwd()
        plt.savefig(figname)
        plt.clf()
        print 'Saved file: {} in folder: {}'.format(figname, dir_path)
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

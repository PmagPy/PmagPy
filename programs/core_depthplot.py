#!/usr/bin/env python
import sys
import wx
import os

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
        core_depthplot.py

    DESCRIPTION
        plots various measurements versus core_depth or age.  plots data flagged as 'FS-SS-C' as discrete samples.  

    SYNTAX
        core_depthplot.py [command line optins]

    OPTIONS
        -h prints help message and quits
        -f FILE: specify input magic_measurments format file from magi
        -fsum FILE: specify input LIMS database (IODP) core summary csv file
        -fwig FILE: specify input depth,wiggle to plot, in magic format with sample_core_depth key for depth
        -fsa FILE: specify input er_samples format file from magic for depth
        -fa FILE: specify input er_ages format file from magic for age
              NB: must have either -fsa OR -fa (not both)
        -fsp FILE sym size: specify input zeq_specimen format file from magic, sym and size
              NB: PCAs will have specified color, while fisher means will be white with specified color as the edgecolor
        -fres FILE specify input pmag_results file from magic, sym and size
        -LP [AF,T,ARM,IRM, X] step [in mT,C,mT,mT, mass/vol] to plot 
        -S do not plot blanket treatment data (if this is set, you don't need the -LP)
        -sym SYM SIZE, symbol, size for continuous points (e.g., ro 5, bs 10, g^ 10 for red dot, blue square, green triangle), default is blue dot at 5 pt
        -D do not plot declination
        -M do not plot magnetization
        -log  plot magnetization  on a log scale
        -L do not connect dots with a line
        -I do not plot inclination
        -d min max [in m] depth range to plot
        -n normalize by weight in er_specimen table
        -Iex: plot the expected inc at lat - only available for results with lat info in file
        -ts TS amin amax: plot the GPTS for the time interval between amin and amax (numbers in Ma)
           TS: [ck95, gts04, gts12] 
        -ds [mbsf,mcd] specify depth scale, mbsf default 
        -fmt [svg, eps, pdf, png] specify output format for plot (default: svg)
        -sav save plot silently

     DEFAULTS:
         Measurements file: magic_measurements.txt
         Samples file: er_samples.txt
         NRM step
         Summary file: none
    """

    args = sys.argv
    if '-h' in args:
        print main.__doc__
        sys.exit()

    dataframe = extractor.command_line_dataframe([ ['f', False, 'magic_measurements.txt'], ['fsum', False, ''],
                                                   ['fwig', False, ''], ['fsa', False, ''],
                                                   ['fa', False, ''], ['fsp', False, ''],
                                                   ['fres', False, '' ],  ['fmt', False, 'svg'], 
                                                   ['LP', False,  ''], ['n', False, False], 
                                                   ['d', False, '-1 -1'], ['ts', False, ''],
                                                   ['WD', False, '.'], ['L', False, True],
                                                   ['S', False, True], ['D', False, True],
                                                   ['I', False, True], ['M', False, True],
                                                   ['log', False,  0],
                                                   ['ds', False, 'sample_core_depth'],
                                                   ['sym', False, 'bo 5'], ['ID', False, '.'],
                                                   ['sav', False, False]])

    checked_args = extractor.extract_and_check_args(args, dataframe)
    meas_file, sum_file, wig_file, samp_file, age_file, spc_file, res_file, fmt, meth, norm, depth, timescale, dir_path, pltLine, pltSus, pltDec, pltInc, pltMag, logit, depth_scale, symbol, input_dir, save = extractor.get_vars(['f', 'fsum', 'fwig', 'fsa', 'fa', 'fsp', 'fres', 'fmt',  'LP', 'n', 'd', 'ts', 'WD', 'L', 'S', 'D', 'I', 'M', 'log', 'ds', 'sym', 'ID', 'sav'], checked_args)

    # format some variables
    # format symbol/size
    try:
        sym, size = symbol.split()
        size = int(size)
    except:
        print 'you should provide -sym in this format: ro 5'
        print 'using defaults instead'
        sym, size = 'ro', 5

    # format result file, symbol, size
    if res_file:
        try:
            res_file, res_sym, res_size = res_file.split()
        except:
            print 'you must provide -fres in this format: -fres filename symbol size'
            print 'could not parse {}, defaulting to using no result file'.format(res_file)
            res_file, res_sym, res_size = '', '', 0
    else:
        res_file, res_sym, res_size = '', '', 0

    # format specimen file, symbol, size
    if spc_file:
        try:
            spc_file, spc_sym, spc_size = spc_file.split()
        except:
            print 'you must provide -fsp in this format: -fsp filename symbol size'
            print 'could not parse {}, defaulting to using no specimen file'.format(spc_file)
            spc_file, spc_sym, spc_size = '', '', 0
    else:
        spc_file, spc_sym, spc_size = '', '', 0

    # format min/max depth
    try:
        dmin, dmax = depth.split()
    except:
        print 'you must provide -d in this format: -d dmin dmax'
        print 'could not parse {}, defaulting to plotting all depths'.format(depth)
        dmin, dmax = -1, -1

    # format timescale, min/max time
    if timescale:
        try:
            timescale, amin, amax = timescale.split()
            pltTime = True
        except:
            print 'you must provide -ts in this format: -ts timescale minimum_age maximum_age'
            print 'could not parse {}, defaulting to using no timescale'.format(timescale)
            timescale, amin, amax = None, -1, -1
            pltTime = False
    else:
        timescale, amin, amax = None, -1, -1
        pltTime = False
            

    # format norm and wt_file
    if norm and not isinstance(norm, bool):
        wt_file = norm
        norm = True
    else:
        norm = False
        wt_file = ''

    # format list of protcols and step
    try:
        method, step = meth.split()
    except:
        print 'To use the -LP flag you must provide both the protocol and the step in this format:\n-LP [AF,T,ARM,IRM, X] step [in mT,C,mT,mT, mass/vol] to plot'
        print 'Defaulting to using no protocol'
        method, step = 'LT-NO', 0

    # list of varnames
    #['f', 'fsum', 'fwig', 'fsa', 'fa', 'fsp', 'fres', 'fmt',  'LP', 'n', 'd', 'ts', 'WD', 'L', 'S', 'D', 'I', 'M', 'log', 'ds', 'sym' ]
    #meas_file, sum_file, wig_file, samp_file, age_file, spc_file, res_file, fmt, meth, norm, depth, timescale, dir_path, pltLine, pltSus, pltDec, pltInc, pltMag, logit, depth_scale, symbol

    fig, figname = ipmag.core_depthplot(input_dir, meas_file, spc_file, samp_file, age_file, sum_file, wt_file, depth_scale, dmin, dmax, sym, size, spc_sym, spc_size, method, step, fmt, pltDec, pltInc, pltMag, pltLine, pltSus, logit, pltTime, timescale, amin, amax, norm)

    if fig and save:
        plt.savefig(figname)
        return
    
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

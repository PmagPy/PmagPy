#!/usr/bin/env python

#import pandas as pd
#import numpy as np
import sys
import os
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")

from pmagpy import ipmag
from pmagpy import pmag

from pmag_env import set_env
import pmagpy.contribution_builder as cb


def main():
    """
    NAME
        thellier_magic.py

    DESCRIPTION
        plots Thellier-Thellier data in version 3.0 format
        Reads saved interpretations from a specimen formatted table, default: specimens.txt

    SYNTAX
        thellier_magic.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f MEAS, set measurements input file, default is 'measurements.txt'
        -WD: directory to output files to (default : current directory)
             Note: if using Windows, all figures will output to current directory
        -ID: directory to read files from (default : same as -WD)
        -fsp PRIOR, set specimens.txt prior interpretations file, default is 'specimens.txt'
        -fmt [svg,png,jpg], format for images - default is svg
        -sav,  saves plots without review (in format specified by -fmt key or default)
        -spc SPEC, plots single specimen SPEC, saves plot with specified format
            with optional -b bounds and quits
        -n SPECIMENS, number of specimens to plot

    OUTPUT
        figures:
            ALL:  numbers refer to temperature steps in command line window
            1) Arai plot:  closed circles are zero-field first/infield
                           open circles are infield first/zero-field
                           triangles are pTRM checks
                           squares are pTRM tail checks
                           VDS is vector difference sum
                           diamonds are bounds for interpretation
            2) Zijderveld plot:  closed (open) symbols are X-Y (X-Z) planes
                                 X rotated to NRM direction
            3) (De/Re)Magnetization diagram:
                           circles are NRM remaining
                           squares are pTRM gained
            4) equal area projections:
               green triangles are pTRM gained direction
                           red (purple) circles are lower(upper) hemisphere of ZI step directions
                           blue (cyan) squares are lower(upper) hemisphere IZ step directions
            5) Optional:  TRM acquisition
            6) Optional: TDS normalization
        command line window:
            list is: temperature step numbers, temperatures (C), Dec, Inc, Int (units of measuements)
                     list of possible commands: type letter followed by return to select option
                     saving of plots creates image files with specimen, plot type as name
    """

#
# parse command line options
#

    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    dir_path = pmag.get_named_arg("-WD", default_val=".")
    input_dir_path = pmag.get_named_arg('-ID', "")
    input_dir_path, dir_path = pmag.fix_directories(input_dir_path, dir_path)
    meas_file = pmag.get_named_arg(
        "-f", default_val="measurements.txt")
    #spec_file = pmag.get_named_arg(
    #    "-fsp", default_val="specimens.txt")
    #crit_file = pmag.get_named_arg("-fcr", default_val="criteria.txt")
    #spec_file = os.path.join(dir_path, spec_file)
    #crit_file = os.path.join(dir_path, crit_file)
    meas_file = pmag.resolve_file_name(meas_file, input_dir_path)
    fmt = pmag.get_named_arg("-fmt", "svg")
    save_plots = False
    interactive = True
    if '-sav' in sys.argv:
        save_plots = True
        interactive=False
    spec = pmag.get_named_arg("-spc", default_val="")
    n_specs = pmag.get_named_arg("-n", default_val="all")
    try:
        n_specs = int(n_specs)
    except ValueError:
        pass
    ipmag.thellier_magic(meas_file, dir_path, input_dir_path,
                         spec, n_specs, save_plots, fmt, interactive)

# deprecated options
#-fcr CRIT, set criteria file for grading.  # NOT SUPPORTED
#-b BEG END: sets  bounds for calculation    # NOT SUPPORTED
#-z use only z component difference for pTRM calculation # NOT SUPPORTED


if __name__ == "__main__":
    main()

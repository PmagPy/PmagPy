#!/usr/bin/env python

# -*- python-indent-offset: 4; -*-

import pandas as pd
import numpy as np
import sys
import os
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")

import pmagpy.pmag as pmag
import pmagpy.pmagplotlib as pmagplotlib
import pmagpy.contribution_builder as cb
from pmagpy import ipmag
from pmag_env import set_env

def main():
    """
    NAME
        zeq_magic.py
    DESCRIPTION
        reads in a MagIC measurements formatted file, makes plots of remanence decay
        during demagnetization experiments.  Reads in prior interpretations saved in
        a specimens formatted file interpretations in a specimens file.
        interpretations are saved in the coordinate system used.
    SYNTAX
        zeq_magic.py [command line options]
    OPTIONS
        -h prints help message and quits
        -f  MEASFILE: sets measurements format input file, default: measurements.txt
        -fsp SPECFILE: sets specimens format file with prior interpreations, default: specimens.txt
        -fsa SAMPFILE: sets samples format file sample=>site information, default: samples.txt
        -fsi SITEFILE: sets sites format file with site=>location informationprior interpreations, default: samples.txt
        -Fp PLTFILE: sets filename for saved plot, default is name_type.fmt (where type is zijd, eqarea or decay curve)
        -crd [s,g,t]: sets coordinate system,  g=geographic, t=tilt adjusted, default: specimen coordinate system
        -spc SPEC  plots single specimen SPEC, saves plot with specified format
              with optional -dir settings and quits
        -dir [L,P,F][beg][end]: sets calculation type for principal component analysis, default is none
             beg: starting step for PCA calculation
             end: ending step for PCA calculation
             [L,P,F]: calculation type for line, plane or fisher mean
             must be used with -spc option
        -fmt FMT: set format of saved plot [png,svg,jpg]
        -A:  suppresses averaging of  replicate measurements, default is to average
        -sav: saves all plots without review
    """
    if '-h' in sys.argv:
        print(main.__doc__)
        return
    dir_path = pmag.get_named_arg("-WD", default_val=os.getcwd())
    meas_file = pmag.get_named_arg(
        "-f", default_val="measurements.txt")
    spec_file = pmag.get_named_arg(
        "-fsp", default_val="specimens.txt")
    specimen = pmag.get_named_arg(
        "-spc", default_val="")
    samp_file = pmag.get_named_arg("-fsa", default_val="samples.txt")
    site_file = pmag.get_named_arg("-fsi", default_val="sites.txt")
    plot_file = pmag.get_named_arg("-Fp", default_val="")
    crd = pmag.get_named_arg("-crd", default_val="s")
    fmt = pmag.get_named_arg("-fmt", "svg")
    specimen = pmag.get_named_arg("-spc", default_val="")
    interactive = True
    save_plots = False
    if "-sav" in sys.argv:
        interactive = False
        save_plots = True
    ipmag.zeq_magic(meas_file, spec_file, crd, dir_path, n_plots="all",
                    save_plots=save_plots, fmt=fmt, interactive=interactive, specimen=specimen)


#
if __name__ == "__main__":
    main()

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

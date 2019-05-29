#!/usr/bin/env python
# -*- python-indent-offset: 4; -*-

# -*- mode: python-mode; python-indent-offset: 4 -*-
import sys
import os
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")
from pmagpy import ipmag
from pmagpy import pmag


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
    interactive = True
    save_plots = pmag.get_flag_arg_from_sys("-sav")
    if save_plots:
        interactive = False
    fmt = pmag.get_named_arg("-fmt", "svg")
    XLP = pmag.get_named_arg("-XLP", "")
    spec_file = pmag.get_named_arg("-fsp", default_val="specimens.txt")
    samp_file = pmag.get_named_arg("-fsa", default_val="samples.txt")
    site_file = pmag.get_named_arg("-fsi", default_val="sites.txt")
    loc_file = pmag.get_named_arg("-flo", default_val="locations.txt")
    ipmag.dmag_magic(in_file, dir_path, input_dir_path, spec_file, samp_file,
                     site_file, loc_file, plot_by, LT, norm, XLP,
                     save_plots, fmt, interactive, n_plots="all")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
import sys
import numpy
import pmagpy.pmag as pmag
from pmagpy import ipmag
from pmagpy.mapping import map_magic


def main():
    """
    NAME
        atrm_magic.py

    DESCRIPTION
        Converts ATRM  data to best-fit tensor (6 elements plus sigma)
         Original program ARMcrunch written to accomodate ARM anisotropy data
          collected from 6 axial directions (+X,+Y,+Z,-X,-Y,-Z) using the
          off-axis remanence terms to construct the tensor. A better way to
          do the anisotropy of ARMs is to use 9,12 or 15 measurements in
          the Hext rotational scheme.

    SYNTAX
        atrm_magic.py [-h][command line options]

    OPTIONS
        -h prints help message and quits
        -f FILE: specify input file, default is atrm_measurements.txt
        -fsp FILE: specimen input file, default is specimens.txt (optional)
        -Fsp FILE: specify output file, default is specimens.txt (MagIC 3 only)
        -DM DATA_MODEL: specify MagIC 2 or MagIC 3, default is 3

    INPUT
        Input for the present program is a TRM acquisition data with an optional baseline.
      The order of the measurements is:
    Decs=[0,90,0,180,270,0,0,90,0]
    Incs=[0,0,90,0,0,-90,0,0,90]
     The last two measurements are optional

    """
    # initialize some parameters
    args = sys.argv
    if "-h" in args:
        print(main.__doc__)
        sys.exit()


    #if "-Fa" in args:
    #    ind = args.index("-Fa")
    #    rmag_anis = args[ind + 1]
    #if "-Fr" in args:
    #    ind = args.index("-Fr")
    #    rmag_res = args[ind + 1]

    #meas_file = "atrm_measurements.txt"
    #rmag_anis = "trm_anisotropy.txt"
    #rmag_res = "atrm_results.txt"


    dir_path = pmag.get_named_arg("-WD", ".")
    input_dir_path = pmag.get_named_arg("-ID", "")
    meas_file = pmag.get_named_arg("-f", "measurements.txt")
    data_model_num = int(pmag.get_named_arg("-DM", 3))
    spec_outfile = pmag.get_named_arg("-Fsp", "specimens.txt")
    spec_infile = pmag.get_named_arg("-fsp", "specimens.txt")


    ipmag.atrm_magic(meas_file, dir_path, input_dir_path,
                     spec_infile, spec_outfile, data_model_num)




if __name__ == "__main__":
    main()

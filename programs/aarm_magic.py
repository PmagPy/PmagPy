#!/usr/bin/env python
import sys
import pmagpy.pmag as pmag
from pmagpy import ipmag


def main():
    """
    NAME
        aarm_magic.py

    DESCRIPTION
        Converts AARM  data to best-fit tensor (6 elements plus sigma)
         Original program ARMcrunch written to accomodate ARM anisotropy data
          collected from 6 axial directions (+X,+Y,+Z,-X,-Y,-Z) using the
          off-axis remanence terms to construct the tensor. A better way to
          do the anisotropy of ARMs is to use 9,12 or 15 measurements in
          the Hext rotational scheme.

    SYNTAX
        aarm_magic.py [-h][command line options]

    OPTIONS
        -h prints help message and quits
        -f FILE: specify input file, default is aarm_measurements.txt
        -crd [s,g,t] specify coordinate system, requires samples file
        -fsa  FILE: specify er_samples.txt file, default is er_samples.txt (2.5) or samples.txt (3.0)
        -Fa FILE: specify anisotropy output file, default is arm_anisotropy.txt (MagIC 2.5 only)
        -Fr FILE: specify results output file, default is aarm_results.txt (MagIC 2.5 only)
        -Fsi FILE: specify output file, default is specimens.txt (MagIC 3 only)
        -DM DATA_MODEL: specify MagIC 2 or MagIC 3, default is 3

    INPUT
        Input for the present program is a series of baseline, ARM pairs.
      The baseline should be the AF demagnetized state (3 axis demag is
      preferable) for the following ARM acquisition. The order of the
      measurements is:

           positions 1,2,3, 6,7,8, 11,12,13 (for 9 positions)
           positions 1,2,3,4, 6,7,8,9, 11,12,13,14 (for 12 positions)
           positions 1-15 (for 15 positions)
    """
    # initialize some parameters
    args = sys.argv

    if "-h" in args:
        print(main.__doc__)
        sys.exit()

    #meas_file = "aarm_measurements.txt"
    #rmag_anis = "arm_anisotropy.txt"
    #rmag_res = "aarm_results.txt"
    #
    # get name of file from command line
    #
    data_model_num = int(pmag.get_named_arg("-DM", 3))
    spec_file = pmag.get_named_arg("-Fsi", "specimens.txt")
    if data_model_num == 3:
        samp_file = pmag.get_named_arg("-fsa", "samples.txt")
    else:
        samp_file = pmag.get_named_arg("-fsa", "er_samples.txt")
    dir_path = pmag.get_named_arg('-WD', '.')
    input_dir_path = pmag.get_named_arg('-ID', '')
    infile = pmag.get_named_arg('-f', reqd=True)
    coord = pmag.get_named_arg('-crd', '-1')

    #if "-Fa" in args:
    #    ind = args.index("-Fa")
    #    rmag_anis = args[ind + 1]
    #if "-Fr" in args:
    #    ind = args.index("-Fr")
    #    rmag_res = args[ind + 1]
    ipmag.aarm_magic(infile, dir_path, input_dir_path,
            spec_file, samp_file, data_model_num,
            coord)


if __name__ == "__main__":
    main()

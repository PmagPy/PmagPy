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
          from TRMs acquired along 6 axial directions (+X,+Y,+Z,-X,-Y,-Z),
          using the off-axis remanence terms to construct the tensor.

    SYNTAX
        atrm_magic.py [-h][command line options]

    OPTIONS
        -h prints help message and quits
        -f FILE: specify input file, default is atrm_measurements.txt
        -fsp FILE: specimen input file, default is specimens.txt (optional)
        -Fsp FILE: specify output file, default is specimens.txt (optional)
        -WD DIR: output directory, default is current directory
        -ID DIR: input directory, default is the output directory

    INPUT
        A MagIC 3 measurements table with, for each specimen, records with
        method code LP-AN-TRM:
            optional: a zero-field step (LT-T-Z), the baseline, which is
                subtracted from each in-field step; if there is more than
                one, their mean is used
            six in-field steps (LT-T-I) heated to the same temperature, with
                the lab field (treat_dc_field_phi, treat_dc_field_theta) along
                +X (0, 0), +Y (90, 0), +Z (0, 90), -X (180, 0), -Y (270, 0)
                and -Z (0, -90); they may be in any order
            optional: an alteration check (LT-PTRM-I) repeating one of the
                in-field positions, reported as aniso_alt, the percent
                difference of the two TRMs (baseline subtracted)

    OUTPUT
        The tensors (aniso_type ATRM, specimen coordinates) are merged into
        the specimens table. Exits with status 1 if the input is not a
        measurements table or has no LP-AN-TRM records.

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
    meas_file = pmag.get_named_arg("-f", "atrm_measurements.txt")
    spec_outfile = pmag.get_named_arg("-Fsp", "specimens.txt")
    spec_infile = pmag.get_named_arg("-fsp", "specimens.txt")


    ran, message = ipmag.atrm_magic(meas_file, dir_path, input_dir_path,
                                    spec_infile, spec_outfile)
    if not ran:
        sys.exit(1)




if __name__ == "__main__":
    main()

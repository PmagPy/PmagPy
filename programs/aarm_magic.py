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
          do the anisotropy of ARMs is to use 9 or 15 measurements in
          the Hext rotational scheme.

    SYNTAX
        aarm_magic.py [-h][command line options]

    OPTIONS
        -h prints help message and quits
        -f FILE: specify input file, default is aarm_measurements.txt
        -fsp FILE: specimen input file, default is specimens.txt (optional)
        -Fsp FILE: specify output file, default is specimens.txt
        -Fsi FILE: same as -Fsp (retained for backward compatibility)
        -WD DIR: output directory, default is current directory
        -ID DIR: input directory, default is the output directory
        -DM DATA_MODEL: specify MagIC 2 or MagIC 3, default is 3
        MagIC 2 only (legacy):
        -crd [s,g,t] specify coordinate system, requires samples file
        -fsa FILE: specify er_samples.txt file, default is er_samples.txt

    INPUT
        Input for the present program is a series of baseline, ARM pairs.
      The baseline should be the AF demagnetized state (3 axis demag is
      preferable) for the following ARM acquisition. The order of the
      measurements is:

           +X, +Y, +Z, -X, -Y, -Z (for 6 positions)
           positions 1,2,3, 6,7,8, 11,12,13 (for 9 positions)
           positions 1-15 (for 15 positions)

    OUTPUT
        MagIC 3 tensors are written in specimen coordinates
        (aniso_tilt_correction = -1) and merged into the specimen table:
        other records in the input specimen file are retained.
    """
    # initialize some parameters
    args = sys.argv

    if "-h" in args:
        print(main.__doc__)
        sys.exit()

    data_model_num = int(float(pmag.get_named_arg("-DM", 3)))
    dir_path = pmag.get_named_arg('-WD', '.')
    input_dir_path = pmag.get_named_arg('-ID', '')
    infile = pmag.get_named_arg('-f', 'aarm_measurements.txt')

    if data_model_num == 2:
        spec_file = pmag.get_named_arg("-Fsi", "specimens.txt")
        samp_file = pmag.get_named_arg("-fsa", "er_samples.txt")
        coord = pmag.get_named_arg('-crd', '-1')
        ipmag.aarm_magic_dm2(infile=infile, dir_path=dir_path,
                             input_dir_path=input_dir_path, spec_file=spec_file,
                             samp_file=samp_file, data_model_num=data_model_num,
                             coord=coord)
        return

    if "-crd" in args or "-fsa" in args:
        print("-W- -crd and -fsa apply to MagIC 2 only; MagIC 3 AARM "
              "tensors are written in specimen coordinates")
    spec_infile = pmag.get_named_arg("-fsp", "specimens.txt")
    spec_outfile = pmag.get_named_arg(
        "-Fsp", pmag.get_named_arg("-Fsi", "specimens.txt"))
    ipmag.aarm_magic(infile, dir_path, input_dir_path,
                     spec_infile, spec_outfile)


if __name__ == "__main__":
    main()

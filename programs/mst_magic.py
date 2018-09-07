#!/usr/bin/env python
import sys
from pmagpy import pmag
from pmagpy import convert_2_magic as convert


def main():
    """
    NAME
        mst_magic.py

    DESCRIPTION
        converts MsT data (T,M) to measurements format files

    SYNTAX
        mst_magic.py [command line options]

    OPTIONS
        -h: prints the help message and quits.
        -usr USER:   identify user, default is ""
        -f FILE: specify T,M  format input file, required
        -spn SPEC: specimen name, required
        -fsa SFILE: name with sample, site, location information
        -F FILE: specify output file, default is measurements.txt
        -dc H: specify applied field during measurement, default is 0.5 T
        -DM NUM: output to MagIC data model 2.5 or 3, default 3
        -syn  : This is a synthetic specimen and has no sample/site/location information
        -spc NUM : specify number of characters to designate a  specimen, default = 0
        -loc LOCNAME : specify location/study name, must have either LOCNAME or SAMPFILE or be a synthetic
        -ncn NCON:  specify naming convention: default is #1 below
       Sample naming convention:
            [1] XXXXY: where XXXX is an arbitrary length site designation and Y
                is the single character sample designation.  e.g., TG001a is the
                first sample from site TG001.    [default]
            [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
            [5] site name same as sample
            [6] site is entered under a separate column -- NOT CURRENTLY SUPPORTED
            [7-Z] [XXXX]YYY:  XXXX is site designation with Z characters with sample name XXXXYYYY
            NB: all others you will have to customize your self
                 or e-mail ltauxe@ucsd.edu for help.
        INPUT files:
            T M:  T is in Centigrade and M is uncalibrated magnitude

    """
#
# get command line arguments
#

    args = sys.argv
    if "-h" in args:
        print(main.__doc__)
        sys.exit()
    dir_path = pmag.get_named_arg("-WD", ".")
    user = pmag.get_named_arg("-usr", "")
    labfield = pmag.get_named_arg("-dc", '0.5')
    meas_file = pmag.get_named_arg("-F", "measurements.txt")
    samp_file = pmag.get_named_arg("-fsa", "samples.txt")
    try:
        infile = pmag.get_named_arg("-f", reqd=True)
    except pmag.MissingCommandLineArgException:
        print(main.__doc__)
        print("-f  is required option")
        sys.exit()
    specnum = int(pmag.get_named_arg("-spc", 0))
    location = pmag.get_named_arg("-loc", "")
    specimen_name = pmag.get_named_arg("-spn", reqd=True)
    syn = 0
    if "-syn" in args:
        syn = 1
    samp_con = pmag.get_named_arg("-ncn", "1")
    if "-ncn" in args:
        ind = args.index("-ncn")
        samp_con = sys.argv[ind+1]
    data_model_num = int(pmag.get_named_arg("-DM", 3))
    convert.mst(infile, specimen_name, dir_path, "", meas_file, samp_file,
        user, specnum, samp_con, labfield, location, syn, data_model_num)


if __name__ == "__main__":
    main()

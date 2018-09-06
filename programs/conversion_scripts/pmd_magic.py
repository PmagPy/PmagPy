#!/usr/bin/env python
"""
NAME
    pmd_magic.py

DESCRIPTION
    converts PMD (Enkin)  format files to MagIC format files

SYNTAX
    pmd_magic.py [command line options]

OPTIONS
    -h: prints the help message and quits.
    -ID: directory for input file if not included in -f flag
    -f FILE: specify infile file, required
    -WD: directory to output files to (default : current directory)
    -F FILE: specify output file, default is measurements.txt
    -Fsp FILE: specify output specimens.txt file, default is specimens.txt
    -Fsa FILE: specify output samples.txt file, default is samples.txt
    -Fsi FILE: specify output sites.txt file, default is sites.txt # LORI
    -Flo FILE: specify output locations.txt file, default is locations.txt
    -spc NUM : specify number of characters to designate a  specimen, default = 1
    -loc LOCNAME : specify location/study name
    -A: don't average replicate measurements
    -ncn NCON: specify naming convention
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
    -lat: Lattitude of site (if no value given will leave blank)
    -lon: Longitude of site (if no value given will leave blank)
    -mcd [SO-MAG,SO-SUN,SO-SIGHT...] supply how these samples were oriented


        NB: all others you will have to customize your self
             or e-mail ltauxe@ucsd.edu for help.

INPUT
    PMD format files
"""

import sys
from pmagpy import pmag
from pmagpy import convert_2_magic as convert


def do_help():
    return __doc__


def main():
    if "-h" in sys.argv:
        help(__name__)
        sys.exit()
    mag_file = pmag.get_named_arg('-f', reqd=True)
    dir_path = pmag.get_named_arg('-WD', '.')
    input_dir_path = pmag.get_named_arg('-ID', '')
    meas_file = pmag.get_named_arg('-F', 'measurements.txt')
    spec_file = pmag.get_named_arg('-Fsp', 'specimens.txt')
    samp_file = pmag.get_named_arg('-Fsa', 'samples.txt')
    site_file = pmag.get_named_arg('-Fsi', 'sites.txt')
    loc_file = pmag.get_named_arg('-Flo', 'locations.txt')
    lat = pmag.get_named_arg('-lat', '')
    lon = pmag.get_named_arg('-lon', '')
    specnum = pmag.get_named_arg('-spc', 0)
    samp_con = pmag.get_named_arg('-ncn', '1')
    location = pmag.get_named_arg('-loc', 'unknown')
    noave = 0
    if "-A" in sys.argv:
        noave = 1
    meth_code = pmag.get_named_arg('-mcd', "LP-NO")
    convert.pmd(mag_file, dir_path, input_dir_path, meas_file,
                spec_file, samp_file, site_file, loc_file,
                lat, lon, specnum, samp_con, location, noave,
                meth_code)


if __name__ == "__main__":
    main()

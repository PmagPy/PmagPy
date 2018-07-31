#!/usr/bin/env python
"""
NAME
    jr6_jr6_magic.py

DESCRIPTION
    converts JR6 .jr6 format files to magic_measurements format files

SYNTAX
    jr6_jr6_magic.py [command line options]

OPTIONS
    -h: prints the help message and quits.
    -usr USER: Colon delimited list of analysts, default is ""
    -ID: directory for input file if not included in -f flag
    -f FILE: specify  input file, required
    -WD: directory to output files to (default : current directory)
    -F FILE: specify output  measurements file, default is measurements.txt
    -Fsp FILE: specify output specimens.txt file, default is specimens.txt
    -Fsa FILE: specify output samples.txt file, default is samples.txt
    -Fsi FILE: specify output sites.txt file, default is sites.txt # LORI
    -Flo FILE: specify output locations.txt file, default is locations.txt
    -spc NUM : specify number of characters to designate a  specimen, default = 1
    -loc LOCNAME : specify location/study name
    -lat latitude of site (also used as bounding latitude for location)
    -lon longitude of site (also used as bounding longitude for location)
    -A: don't average replicate measurements
    -ncn NCON: specify sample naming convention (6 and 7 not yet implemented)
    -mcd [SO-MAG,SO-SUN,SO-SIGHT...] supply how these samples were oriented
    -JR  IODP samples measured on the JOIDES RESOLUTION
    -v NUM : specify the volume in cc of the sample, default 12cc (rounded one inch diameter core, one inch length)
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

INPUT
    JR6 .jr6 format file
"""
import sys
from pmagpy import convert_2_magic as convert


def do_help():
    return __doc__


def main():
    kwargs = {}
    if "-h" in sys.argv:
        help(__name__)
        sys.exit()
    if "-usr" in sys.argv:
        ind = sys.argv.index("-usr")
        kwargs['user'] = sys.argv[ind+1]
    if '-WD' in sys.argv:
        ind = sys.argv.index('-WD')
        kwargs['dir_path'] = sys.argv[ind+1]
    if '-ID' in sys.argv:
        ind = sys.argv.index('-ID')
        kwargs['input_dir_path'] = sys.argv[ind+1]
    if '-F' in sys.argv:
        ind = sys.argv.index("-F")
        kwargs['meas_file'] = sys.argv[ind+1]
    if '-Fsp' in sys.argv:
        ind = sys.argv.index("-Fsp")
        kwargs['spec_file'] = sys.argv[ind+1]
    if '-Fsa' in sys.argv:
        ind = sys.argv.index("-Fsa")
        kwargs['samp_file'] = sys.argv[ind+1]
    if '-Fsi' in sys.argv:   # LORI addition
        ind = sys.argv.index("-Fsi")
        kwargs['site_file'] = sys.argv[ind+1]
    if '-Flo' in sys.argv:
        ind = sys.argv.index("-Flo")
        kwargs['loc_file'] = sys.argv[ind+1]
    if '-f' in sys.argv:
        ind = sys.argv.index("-f")
        kwargs['mag_file'] = sys.argv[ind+1]
    if "-spc" in sys.argv:
        ind = sys.argv.index("-spc")
        kwargs['specnum'] = sys.argv[ind+1]
    if "-ncn" in sys.argv:
        ind = sys.argv.index("-ncn")
        kwargs['samp_con'] = sys.argv[ind+1]
    if "-loc" in sys.argv:
        ind = sys.argv.index("-loc")
        kwargs['location'] = sys.argv[ind+1]
    if "-lat" in sys.argv:
        ind = sys.argv.index("-lat")
        kwargs['lat'] = sys.argv[ind+1]
    if "-lon" in sys.argv:
        ind = sys.argv.index("-lon")
        kwargs['lon'] = sys.argv[ind+1]
    if "-A" in sys.argv:
        kwargs['noave'] = True
    if "-mcd" in sys.argv:
        ind = sys.argv.index("-mcd")
        kwargs['meth_code'] = sys.argv[ind+1]
    if "-JR" in sys.argv:
        kwargs['JR'] = True
    if "-v" in sys.argv:
        ind = sys.argv.index("-v")
        # enter volume in cc, convert to m^3
        kwargs['volume'] = sys.argv[ind+1]

    convert.jr6_jr6(**kwargs)


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""
NAME
    utrecht_magic.py

DESCRIPTION
    converts Utrecht magnetometer data files to MagIC files

SYNTAX
    utrecht_magic.py [command line options]

OPTIONS
    -h: prints the help message and quits.
    -ID: directory for input file if not included in -f flag
    -f FILE: specify  input file, required
    -WD: directory to output files to (default : current directory)
    -F FILE: specify output  measurements file, default is measurements.txt
    -Fsp FILE: specify output specimens.txt file, default is specimens.txt
    -Fsa FILE: specify output samples.txt file, default is samples.txt
    -Fsi FILE: specify output sites.txt file, default is sites.txt
    -Flo FILE: specify output locations.txt file, default is locations.txt
    -ncn: Site Naming Convention
     Site to Sample naming convention:
        [1] XXXXY: where XXXX is an arbitrary length site designation and Y
            is the single character sample designation.  e.g., TG001a is the
            first sample from site TG001.    [default]
        [2: default] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
        [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
        [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
        [5] site name = sample name
        [6] site name entered in site_name column in the orient.txt format input file  -- NOT CURRENTLY SUPPORTED
        [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY
    -spc: number of characters to remove to generate sample names from specimen names
    -loc LOCNAME : specify location/study name
    -lat LAT: latitude of site (also used as bounding latitude for location)
    -lon LON: longitude of site (also used as bounding longitude for location)
    -A: don't average replicate measurements
    -mcd: [SO-MAG,SO-SUN,SO-SIGHT...] supply how these samples were oriented
    -dc B PHI THETA: dc lab field (in microTesla), phi,and theta (in degrees) must be spaced after flag (i.e -dc 30 0 -90)
    -mno: number of orientations measured (default=8)

INPUT
    Utrecht magnetometer data file
"""
import sys
from pmagpy import convert_2_magic as convert


def do_help():
    return __doc__

def main():
    # get command line arguments
    kwargs = {}
    if "-h" in sys.argv:
        help(__name__)
        sys.exit()
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
    if '-Fsi' in sys.argv:  # LORI addition
        ind = sys.argv.index("-Fsi")
        kwargs['site_file'] = sys.argv[ind+1]
    if '-Flo' in sys.argv:  # Kevin addition
        ind = sys.argv.index("-Flo")
        kwargs['loc_file'] = sys.argv[ind+1]
    if '-f' in sys.argv:
        ind = sys.argv.index("-f")
        kwargs['mag_file'] = sys.argv[ind+1]
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
    if "-ncn" in sys.argv:
        ind = sys.argv.index("-ncn")
        kwargs['samp_con'] = sys.argv[ind+1]
    if '-dc' in sys.argv:
        ind = sys.argv.index('-dc')
        kwargs['labfield'] = sys.argv[ind+1]
        kwargs['phi'] = sys.argv[ind+2]
        kwargs['theta'] = sys.argv[ind+3]
    if '-spc' in sys.argv:
        ind = sys.argv.index("-spc")
        kwargs['specnum'] = sys.argv[ind+1]
    if '-mno' in sys.argv:
        ind = sys.argv.index('-mno')
        kwargs['meas_n_orient'] = sys.argv[ind+1]
    if '-dmy' in sys.argv:
        kwargs['dmy_flag'] = True

    convert.utrecht(**kwargs)


if __name__ == "__main__":
    main()

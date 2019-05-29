#!/usr/bin/env python
"""
NAME
    iodp_dscr_magic.py

DESCRIPTION
    Convert IODP discrete measurement files into MagIC file(s). This program
    assumes that you have created the specimens, samples, sites and locations
    files using convert_2_magic.iodp_samples_csv from files downloaded from the LIMS online
    repository and that all samples are in that file.

SYNTAX
    iodp_dscr_magic.py [command line options]

OPTIONS
    -h: prints the help message and quits.
    -ID: directory for input file if not included in -f flag
    -f FILE: specify input .csv file, default is all in directory
    -WD: directory to output files to (default : current directory)
    -F FILE: specify output  measurements file, default is measurements.txt
    -Fsp FILE: specify output specimens.txt file, default is specimens.txt
    -lat LAT: latitude of site (also used as bounding latitude for location)
    -lon LON: longitude of site (also used as bounding longitude for location)
    -A: don't average replicate measurements
    -v NUM: volume in cc, will be used if there is no volume in the input data (default : 12cc (rounded one inch diameter core, one inch length))

INPUTS
     IODP discrete measurement .csv files
"""
import sys
from pmagpy import convert_2_magic as convert
from pmagpy import pmag

def do_help():
    return __doc__


def main():
    kwargs = {}
    # get command line sys.argv

    if "-h" in sys.argv:
        help(__name__)
        sys.exit()
    if '-ID' in sys.argv:
        ind = sys.argv.index('-ID')
        kwargs['input_dir_path'] = sys.argv[ind+1]
    if '-f' in sys.argv:
        ind = sys.argv.index("-f")
        kwargs['dscr_file'] = sys.argv[ind+1]
    if '-WD' in sys.argv:
        ind = sys.argv.index("-WD")
        kwargs['dir_path'] = sys.argv[ind+1]
    if '-F' in sys.argv:
        ind = sys.argv.index("-F")
        kwargs['meas_file'] = sys.argv[ind+1]
    if '-Fsp' in sys.argv:
        ind = sys.argv.index("-Fsp")
        kwargs['spec_file'] = sys.argv[ind+1]
    if "-A" in sys.argv:
        kwargs['noave'] = True
    if "-lat" in sys.argv:
        ind = sys.argv.index("-lat")
        kwargs['lat'] = sys.argv[ind+1]
    if "-lon" in sys.argv:
        ind = sys.argv.index("-lon")
        kwargs['lon'] = sys.argv[ind+1]
    kwargs['volume'] = pmag.get_named_arg('-v', default_val=7)
    # do conversion
    convert.iodp_dscr_lore(**kwargs)


if __name__ == '__main__':
    main()

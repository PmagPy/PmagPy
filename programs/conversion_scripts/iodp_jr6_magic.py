#!/usr/bin/env python
"""
NAME
    iodp_jr6_magic.py

DESCRIPTION
    converts shipboard .jr6 format files to magic_measurements format files

SYNTAX
    iodp_jr6_magic.py [command line options]

OPTIONS
    -h: prints the help message and quits.
    -ID: directory for input file if not included in -f flag
    -f FILE: specify input .csv file, default is all in directory
    -WD: directory to output files to (default : current directory)
    -F FILE: specify output  measurements file, default is measurements.txt
    -Fsp FILE: specify output specimens.txt file, default is specimens.txt
    -Fsa FILE: specify output samples.txt file, default is samples.txt
    -Fsi FILE: specify output sites.txt file, default is sites.txt
    -Flo FILE: specify output locations.txt file, default is locations.txt
    -lat LAT: latitude of site (also used as bounding latitude for location)
    -lon LON: longitude of site (also used as bounding longitude for location)
    -exp EXPEDITION: specify expedition name (i.e. 312)
    -site HOLE: specify hole name (i.e. U1456A)
    -A: don't average replicate measurements
    -v NUM: volume in cc, will be used if there is no volume in the input data (default : 12cc (rounded one inch diameter core, one inch length))

INPUT
    JR6 .jr6 format file
"""
import sys
from pmagpy import convert_2_magic as convert


def do_help():
    return __doc__


def main():
    kwargs = {}
    # get command line arguments
    if '-WD' in sys.argv:
        ind = sys.argv.index('-WD')
        kwargs['dir_path'] = sys.argv[ind+1]
    if '-ID' in sys.argv:
        ind = sys.argv.index('-ID')
        kwargs['input_dir_path'] = sys.argv[ind+1]
    if "-h" in sys.argv:
        help(__name__)
        sys.exit()
    if '-F' in sys.argv:
        ind = sys.argv.index("-F")
        kwargs['meas_file'] = sys.argv[ind+1]
    if '-Fsp' in sys.argv:
        ind = sys.argv.index("-Fsp")
        kwargs['spec_file'] = sys.argv[ind+1]
    if '-Fsa' in sys.argv:
        ind = sys.argv.index("-Fsa")
        kwargs['samp_file'] = sys.argv[ind+1]
    if '-Fsi' in sys.argv:
        ind = sys.argv.index("-Fsi")
        kwargs['site_file'] = sys.argv[ind+1]
    if '-Flo' in sys.argv:
        ind = sys.argv.index("-Flo")
        kwargs['loc_file'] = sys.argv[ind+1]
    if '-f' in sys.argv:
        ind = sys.argv.index("-f")
        kwargs['mag_file'] = sys.argv[ind+1]
    if "-exp" in sys.argv:
        ind = sys.argv.index("-exp")
        kwargs['expedition'] = sys.argv[ind+1]
    if "-site" in sys.argv:
        ind = sys.argv.index("-site")
        kwargs['site'] = sys.argv[ind+1]
    if "-A" in sys.argv:
        kwargs['noave'] = True
    if "-lat" in sys.argv:
        ind = sys.argv.index("-lat")
        kwargs['lat'] = sys.argv[ind+1]
    if "-lon" in sys.argv:
        ind = sys.argv.index("-lon")
        kwargs['lon'] = sys.argv[ind+1]
    if "-v" in sys.argv:
        ind = sys.argv.index("-v")
        kwargs['volume'] = sys.argv[ind+1]

    convert.iodp_jr6(**kwargs)


if __name__ == '__main__':
    main()

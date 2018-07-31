#!/usr/bin/env python
"""
NAME
    bgc_magic.py

DESCRIPTION
    converts Berkeley Geochronology Center (BGC) format files to measurements format files

SYNTAX
    bgc_magic.py [command line options]

OPTIONS
    -h: prints the help message and quits.
    -usr USER: Colon delimited list of analysts, default is ""
    -ID: directory for input file if not included in -f flag
    -f FILE: specify AUTOCORE format input file, required
    -WD: directory to output files to (default : current directory)
    -F FILE: specify output  measurements file, default is measurements.txt
    -Fsp FILE: specify output specimens.txt file, default is specimens.txt
    -Fsa FILE: specify output samples.txt file, default is samples.txt
    -Fsi FILE: specify output sites.txt file, default is sites.txt
    -Flo FILE: specify output locations.txt file, default is locations.txt
    -spc NUM : specify number of characters to designate a specimen, default = 0
    -loc LOCNAME : specify location/study name
    -site SITENAME : specify site name (if site name can be generated from sample name, see conventions list under the -ncn flag)
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
    -A: don't average replicate measurements
    -mcd [SO-MAG,SO-SUN,SO-SIGHT...] supply how these samples were oriented
    -v NUM : specify the volume in cc of the sample, default 12cc. Will use vol in data file if volume!=0 in file.
    -tz: timezone in pytz library format. list of timzones can be found at http://pytz.sourceforge.net/. (default: US/Pacific)
    -append: append output files to existing files, don't overwrite.

INPUT
    BGC paleomag format file
"""
import sys
from pmagpy import convert_2_magic as convert


def do_help():
    return __doc__

def main():
    kwargs={}
    if "-h" in sys.argv:
        help(__name__)
        sys.exit()
    if "-usr" in sys.argv:
        ind=sys.argv.index("-usr")
        kwargs['user']=sys.argv[ind+1]
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
        ind=sys.argv.index("-Fsp")
        kwargs['spec_file']=sys.argv[ind+1]
    if '-Fsa' in sys.argv:
        ind = sys.argv.index("-Fsa")
        kwargs['samp_file'] = sys.argv[ind+1]
    if '-Fsi' in sys.argv: # LORI addition
        ind=sys.argv.index("-Fsi")
        kwargs['site_file']=sys.argv[ind+1]
    if '-Flo' in sys.argv: # Kevin addition
        ind=sys.argv.index("-Flo")
        kwargs['loc_file']=sys.argv[ind+1]
    if '-f' in sys.argv:
        ind = sys.argv.index("-f")
        kwargs['mag_file'] = sys.argv[ind+1]
    if "-loc" in sys.argv:
        ind = sys.argv.index("-loc")
        kwargs['location'] = sys.argv[ind+1]
    if "-site" in sys.argv:
        ind = sys.argv.index("-site")
        kwargs['site'] = sys.argv[ind+1]
    if "-A" in sys.argv:
        kwargs['noave'] = True
    if "-mcd" in sys.argv:
        ind = sys.argv.index("-mcd")
        kwargs['meth_code'] = sys.argv[ind+1]
    if "-v" in sys.argv:
        ind = sys.argv.index("-v")
        kwargs['volume'] = sys.argv[ind+1] # enter volume in cc, convert to m^3
    if "-ncn" in sys.argv:
        ind=sys.argv.index("-ncn")
        kwargs['samp_con']=sys.argv[ind+1]
    if "-spc" in sys.argv:
        ind=sys.argv.index("-spc")
        kwargs['specnum']=int(sys.argv[ind+1])
    if '-tz' in sys.argv:
        ind=sys.argv.index("-tz")
        kwargs['timezone']=sys.argv[ind+1]
    if '-append' in sys.argv:
        kwargs['append']=True

    convert.bgc(**kwargs)

if  __name__ == "__main__":
    main()

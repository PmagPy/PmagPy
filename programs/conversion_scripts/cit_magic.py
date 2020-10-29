#!/usr/bin/env python
"""
NAME
    cit_magic.py

DESCRIPTION
    converts CIT and .sam  format files to measurements format files

SYNTAX
    cit_magic.py [command line options]

OPTIONS
    -h: prints the help message and quits.
    -usr USER: Colon delimited list of analysts, default is ""
    -ID: directory for input file if not included in -f flag
    -f FILE: specify .sam format input file, required
    -WD: directory to output files to (default : current directory)
    -F FILE: specify output  measurements file, default is measurements.txt
    -Fsp FILE: specify output specimens.txt file, default is specimens.txt
    -Fsa FILE: specify output samples.txt file, default is samples.txt
    -Fsi FILE: specify output sites.txt file, default is sites.txt # LORI
    -Flo FILE: specify output locations.txt file, default is locations.txt
    -n [cc,m3,g,kg]: specify normalization, default is cc.
    -A: don't average replicate measurements
    -spc NUM: specify number of characters to designate a  specimen, default = 0
    -ncn NCON: specify naming convention
    -loc LOCNAME: specify location/study name, must have either LOCNAME or SITEFILE or be a synthetic
    -sn SITENAME: specify site name for all samples
    -sampname SAMPLENAME: specify a sample for all specimens
    -mcd [FS-FD:SO-MAG,.....] colon delimited list for method codes applied to all specimens in .sam file
    -dc B PHI THETA: dc lab field (in microTesla), phi,and theta (in degrees) must be spaced after flag (i.e -dc 30 0 -90)
    -ac B : peak AF field (in mT) for ARM acquisition, default is none
    -mno: specify measurement orientation number (meas_n_orient in data model 3.0) (default = 8)

INPUT
    Best to put separate experiments (all AF, thermal, thellier, trm aquisition, Shaw, etc.)

NOTES:
     Sample naming convention:
    [1] XXXXY: where XXXX is an arbitrary length site designation and Y
        is the single character sample designation.  e.g., TG001a is the
        first sample from site TG001.    [default]
    [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
    [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
    [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
    [5] site name = sample name
    [6] site name entered in sitename column in the orient.txt format input file -- NOT CURRENTLY SUPPORTED
    [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY
    NB: all others you will have to either customize your
        self or e-mail ltauxe@ucsd.edu for help.
"""
import os
import sys
from pmagpy import convert_2_magic as convert


def do_help():
    """
    returns help string of script
    """
    return __doc__


def main():
    kwargs = {}
    if '-WD' in sys.argv:
        ind = sys.argv.index("-WD")
        kwargs['dir_path'] = sys.argv[ind+1]
    if "-h" in sys.argv:
        help(__name__)
        sys.exit()
    if "-usr" in sys.argv:
        ind = sys.argv.index("-usr")
        kwargs['user'] = sys.argv[ind+1]
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
    if '-loc' in sys.argv:
        ind = sys.argv.index("-loc")
        kwargs['locname'] = sys.argv[ind+1]
    if '-mcd' in sys.argv:
        ind = sys.argv.index("-mcd")
        kwargs['methods'] = sys.argv[ind+1]
    else:
        kwargs['methods'] = 'SO-MAG'
    if '-spc' in sys.argv:
        ind = sys.argv.index("-spc")
        kwargs['specnum'] = sys.argv[ind+1]
    if '-n' in sys.argv:
        ind = sys.argv.index("-n")
        kwargs['norm'] = sys.argv[ind+1]
    if "-A" in sys.argv:
        kwargs['noave'] = True
    if '-dc' in sys.argv:
        ind = sys.argv.index('-dc')
        kwargs['labfield'] = sys.argv[ind+1]
        kwargs['phi'] = sys.argv[ind+2]
        kwargs['theta'] = sys.argv[ind+3]
    if "-ncn" in sys.argv:
        ind = sys.argv.index("-ncn")
        kwargs['samp_con'] = sys.argv[ind+1]
    if '-f' in sys.argv:
        ind = sys.argv.index("-f")
        kwargs['magfile'] = sys.argv[ind+1]
    if '-ID' in sys.argv:
        ind = sys.argv.index('-ID')
        kwargs['input_dir_path'] = sys.argv[ind+1]
    else:
        kwargs['input_dir_path'] = os.path.split(kwargs['magfile'])[0]
    if '-mno' in sys.argv:
        ind = sys.argv.index('-mno')
        kwargs['meas_n_orient'] = sys.argv[ind+1]
    if '-sn' in sys.argv:
        ind = sys.argv.index('-sn')
        kwargs['sitename'] = sys.argv[ind+1]
    if '-sampname' in sys.argv:
        ind = sys.argv.index('-sampname')
        kwargs['sampname'] = sys.argv[ind+1]

    convert.cit(**kwargs)


if __name__ == "__main__":
    main()

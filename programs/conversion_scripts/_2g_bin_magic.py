#!/usr/bin/env python
"""
NAME
    _2g_bin_magic.py

DESCRIPTION
    takes the binary 2g format magnetometer files and converts them to measurements, samples, and sites tables

SYNTAX
    _2g_bin_magic.py [command line options]

OPTIONS
    -h: prints the help message and quits.
    -usr USER: Colon delimited list of analysts, default is ""
    -ID: directory for input file if not included in -f flag
    -f FILE: specify input file, required
    -WD: directory to output files to (default : current directory)
    -F FILE: specify output  measurements file, default is measurements.txt
    -Fsp FILE: specify output specimens.txt file, default is specimens.txt
    -Fsa FILE: specify output samples.txt file, default is samples.txt
    -Fsi FILE: specify output sites.txt file, default is sites.txt
    -Flo FILE: specify output locations.txt file, default is locations.txt
    -ncn NCON:  specify naming convention: default is #2 below
    -ocn OCON:  specify orientation convention, default is #5 below
    -mcd: specify sampling method codes as a colon delimited string:  [default is: FS-FD:SO-POM]
         FS-FD field sampling done with a drill
         FS-H field sampling done with hand samples
         FS-LOC-GPS  field location done with GPS
         FS-LOC-MAP  field location done with map
         SO-POM   a Pomeroy orientation device was used
         SO-ASC   an ASC orientation device was used
         SO-MAG   orientation with magnetic compass
         SO-SUN   orientation with sun compass
    -loc: location name, default="unknown"
    -lat latitude of site (also used as bounding latitude for location)
    -lon longitude of site (also used as bounding longitude for location)
    -spc NUM : specify number of characters to designate a  specimen, default = 0
    -ins INST : specify instsrument name
    -A: average replicate measurements

INPUT FORMAT
    Input files are horrible mag binary format (who knows why?)
    Orientation convention:
        [1] Lab arrow azimuth= mag_azimuth; Lab arrow dip=-field_dip
            i.e., field_dip is degrees from vertical down - the hade [default]
        [2] Lab arrow azimuth = mag_azimuth-90; Lab arrow dip = -field_dip
            i.e., mag_azimuth is strike and field_dip is hade
        [3] Lab arrow azimuth = mag_azimuth; Lab arrow dip = 90-field_dip
            i.e.,  lab arrow same as field arrow, but field_dip was a hade.
        [4] lab azimuth and dip are same as mag_azimuth, field_dip
        [5] lab azimuth is same as mag_azimuth,lab arrow dip=field_dip-90
        [6] Lab arrow azimuth = mag_azimuth-90; Lab arrow dip = 90-field_dip
        [7] all others you will have to either customize your
            self or e-mail ltauxe@ucsd.edu for help.

     Magnetic declination convention:
         Az will use supplied declination to correct azimuth

   Sample naming convention:
    [1] XXXXY: where XXXX is an arbitrary length site designation and Y
        is the single character sample designation.  e.g., TG001a is the
        first sample from site TG001.    [default]
    [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
    [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
    [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
    [5] site name = sample name
    [6] site name entered in site_name column in the orient.txt format input file  -- NOT CURRENTLY SUPPORTED
    [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY
    NB: all others you will have to either customize your
        self or e-mail ltauxe@ucsd.edu for help.

OUTPUT
        output saved in measurements & samples formatted files
          will overwrite any existing files
"""
import sys
from pmagpy import convert_2_magic as convert


def do_help():
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
    if "-f" in sys.argv:
        ind = sys.argv.index("-f")
        kwargs['mag_file'] = sys.argv[ind+1]
    if "-F" in sys.argv:
        ind = sys.argv.index("-F")
        kwargs['meas_file'] = sys.argv[ind+1]
    if "-Fsp" in sys.argv:
        ind = sys.argv.index("-Fsp")
        kwargs['spec_file'] = sys.argv[ind+1]
    if "-Fsa" in sys.argv:
        ind = sys.argv.index("-Fsa")
        kwargs['samp_file'] = sys.argv[ind+1]
    if "-Fsi" in sys.argv:
        ind = sys.argv.index("-Fsi")
        kwargs['site_file'] = sys.argv[ind+1]
    if "-Flo" in sys.argv:
        ind = sys.argv.index("-Flo")
        kwargs['loc_file'] = sys.argv[ind+1]
    if "-ocn" in sys.argv:
        ind = sys.argv.index("-ocn")
        kwargs['or_con'] = sys.argv[ind+1]
    if "-ncn" in sys.argv:
        ind = sys.argv.index("-ncn")
        kwargs['samp_con'] = sys.argv[ind+1]
    if "-mcd" in sys.argv:
        ind = sys.argv.index("-mcd")
        kwargs['gmeths'] = (sys.argv[ind+1])
    if "-loc" in sys.argv:
        ind = sys.argv.index("-loc")
        kwargs['location'] = (sys.argv[ind+1])
    if "-spc" in sys.argv:
        ind = sys.argv.index("-spc")
        kwargs['specnum'] = int(sys.argv[ind+1])
    if "-ins" in sys.argv:
        ind = sys.argv.index("-ins")
        kwargs['inst'] = sys.argv[ind+1]
    if "-A" in sys.argv:
        kwargs['noave'] = 1
    if '-ID' in sys.argv:
        ind = sys.argv.index('-ID')
        kwargs['ID'] = sys.argv[ind+1]
    if "-lat" in sys.argv:
        ind = sys.argv.index("-lat")
        kwargs['lat'] = sys.argv[ind+1]
    if "-lon" in sys.argv:
        ind = sys.argv.index("-lon")
        kwargs['lon'] = sys.argv[ind+1]

    convert._2g_bin(**kwargs)


if __name__ == "__main__":
    main()

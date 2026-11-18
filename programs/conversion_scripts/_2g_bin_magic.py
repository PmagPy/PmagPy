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
    -A: do not average replicate measurements (by default they are averaged)
    -sav: keep the last of replicate measurements instead of averaging them
    -fn: name each specimen after its file (the 2G software keeps 8 characters
         of a name, so longer names are cut and can be shared by specimens)
    -exp EXP: experiment type: Demag [default], PI, ATRM 6, AARM 6 or CR
         (put ATRM 6 and AARM 6 in quotes); see the step labels below
    -dc B PHI THETA: lab field in microtesla, and its declination and
         inclination in specimen coordinates (PI, ATRM, AARM, CR)
    -cr RATES: cooling rates in K/min separated by commas, in the order of the
         in-field steps XXX.1, XXX.2, ... (CR)

INPUT FORMAT
    Input files are horrible mag binary format (who knows why?)
    Orientation convention:
        [1] Lab arrow azimuth= mag_azimuth; Lab arrow dip=-field_dip
            i.e., field_dip is degrees from vertical down - the hade
        [2] Lab arrow azimuth = mag_azimuth-90; Lab arrow dip = -field_dip
            i.e., mag_azimuth is strike and field_dip is hade
        [3] Lab arrow azimuth = mag_azimuth; Lab arrow dip = 90-field_dip
            i.e.,  lab arrow same as field arrow, but field_dip was a hade.
        [4] lab azimuth and dip are same as mag_azimuth, field_dip
        [5] lab azimuth is same as mag_azimuth,lab arrow dip=field_dip-90 [default]
            (the convention of the 2G software)
        [6] Lab arrow azimuth = mag_azimuth-90; Lab arrow dip = 90-field_dip
        [7] all others you will have to either customize your
            self or e-mail ltauxe@ucsd.edu for help.

     Magnetic declination convention:
         the declination correction stored in the file is added to the
         azimuth and to the bedding dip direction

   Step labels:
        NRM, a temperature (350C, or 350) or an alternating field (20mT). For
        PI, ATRM 6, AARM 6 and CR the decimal is the step code: PI XXX.0 zero
        field, .1 in field, .2 pTRM check, .3 tail check, .4 additivity check;
        ATRM/AARM XXX.0 baseline, .1 to .6 the lab field along +x, +y, +z, -x,
        -y, -z, ATRM .7 alteration check; CR XXX.0 baseline, .1, .2, ... in
        field with the cooling rates of -cr, .7 alteration check.

   Sample naming convention:
    [1] XXXXY: where XXXX is an arbitrary length site designation and Y
        is the single character sample designation.  e.g., TG001a is the
        first sample from site TG001.
    [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length) [default]
    [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
    [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
    [5] site name = sample name
    [6] site name entered in site_name column in the orient.txt format input file  -- NOT CURRENTLY SUPPORTED
    [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY
    [8] site_sample_specimen: the three are separated by '_'
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
        kwargs['noave'] = True
    if "-sav" in sys.argv:
        kwargs['savelast'] = True
    if "-fn" in sys.argv:
        kwargs['specname'] = True
    if "-exp" in sys.argv:
        ind = sys.argv.index("-exp")
        kwargs['experiment'] = sys.argv[ind+1]
    if "-dc" in sys.argv:
        ind = sys.argv.index("-dc")
        kwargs['labfield'] = float(sys.argv[ind+1])
        kwargs['labfield_phi'] = float(sys.argv[ind+2])
        kwargs['labfield_theta'] = float(sys.argv[ind+3])
    if "-cr" in sys.argv:
        ind = sys.argv.index("-cr")
        kwargs['cooling_times_list'] = sys.argv[ind+1]
    if '-ID' in sys.argv:
        ind = sys.argv.index('-ID')
        kwargs['input_dir'] = sys.argv[ind+1]
    if "-lat" in sys.argv:
        ind = sys.argv.index("-lat")
        kwargs['lat'] = sys.argv[ind+1]
    if "-lon" in sys.argv:
        ind = sys.argv.index("-lon")
        kwargs['lon'] = sys.argv[ind+1]

    program_ran, message = convert._2g_bin(**kwargs)
    if not program_ran:
        print("-E-", message)
        sys.exit(1)


if __name__ == "__main__":
    main()

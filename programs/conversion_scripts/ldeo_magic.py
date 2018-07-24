#!/usr/bin/env python
"""
NAME
    ldeo_magic.py

DESCRIPTION
    converts LDEO  format files to magic_measurements format files

SYNTAX
    ldeo_magic.py [command line options]

OPTIONS
    -h: prints the help message and quits.
    -usr USER:   identify user, default is ""
    -ID: directory for input file if not included in -f flag
    -f FILE: specify  input file, required
    -mv (m or v): specify if the final value in the measurement data is volume or mass (default: v)
    -WD: directory to output files to (default : current directory)
    -F FILE: specify output file, default is magic_measurements.txt
    -F FILE: specify output  measurements file, default is measurements.txt
    -Fsp FILE: specify output specimens.txt file, default is specimens.txt
    -Fsa FILE: specify output samples.txt file, default is samples.txt
    -Fsi FILE: specify output sites.txt file, default is sites.txt # LORI
    -Flo FILE: specify output locations.txt file, default is locations.txt
    -LP [colon delimited list of protocols, include all that apply]
        AF:  af demag
        T: thermal including thellier but not trm acquisition
        S: Shaw method
        I: IRM (acquisition)
        N: NRM only
        TRM: trm acquisition
        ANI: anisotropy experiment
        D: double AF demag
        G: triple AF demag (GRM protocol)
    -V [1,2,3] units of IRM field in volts using ASC coil #1,2 or 3
    -spc NUM : specify number of characters to designate a  specimen, default = 0
    -loc LOCNAME : specify location
    -dc B PHI THETA: dc lab field (in micro tesla) and phi,theta, default is none
          NB: use PHI, THETA = -1 -1 to signal that it changes, i.e. in anisotropy experiment
    -ac B : peak AF field (in mT) for ARM acquisition, default is none

    -ARM_dc # default value is 50e-6
    -ARM_temp # default is 600c

    -ncn NCON:  specify naming convention: default is #1 below
    -A: don't average replicate measurements
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
    Best to put separate experiments (all AF, thermal, thellier, trm aquisition, Shaw, etc.) in
       seperate .mag files (eg. af.mag, thermal.mag, etc.)

    Format of LDEO files:
isaf2.fix
LAT:   .00  LON:    .00
ID     TREAT  I  CD    J    CDECL CINCL  GDECL GINCL  BDECL BINCL  SUSC  M/V
________________________________________________________________________________
is031c2       .0  SD  0 461.600 163.9  17.5  337.1  74.5  319.1  74.4    .0   .0

    ID: specimen name
    TREAT:  treatment step
    I:  Instrument
    CD:  Circular standard devation
    J: intensity.  assumed to be total moment in 10^-4 (emu)
    CDECL:  Declination in specimen coordinate system
    CINCL:  Declination in specimen coordinate system
    GDECL:  Declination in geographic coordinate system
    GINCL:  Declination in geographic coordinate system
    BDECL:  Declination in bedding adjusted coordinate system
    BINCL:  Declination in bedding adjusted coordinate system
    SUSC:  magnetic susceptibility (in micro SI)a
    M/V: mass or volume for nomalizing (0 won't normalize)
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
    if '-Fsi' in sys.argv:  # LORI addition
        ind = sys.argv.index("-Fsi")
        kwargs['site_file'] = sys.argv[ind+1]
    if '-Flo' in sys.argv:  # Kevin addition
        ind = sys.argv.index("-Flo")
        kwargs['loc_file'] = sys.argv[ind+1]
    if '-f' in sys.argv:
        ind = sys.argv.index("-f")
        kwargs['magfile'] = sys.argv[ind+1]
    if "-dc" in sys.argv:
        ind = sys.argv.index("-dc")
        kwargs['labfield'] = float(sys.argv[ind+1])
        kwargs['phi'] = float(sys.argv[ind+2])
        kwargs['theta'] = float(sys.argv[ind+3])
    if "-ac" in sys.argv:
        ind = sys.argv.index("-ac")
        kwargs['peakfield'] = sys.argv[ind+1]
    if "-spc" in sys.argv:
        ind = sys.argv.index("-spc")
        kwargs['specnum'] = int(sys.argv[ind+1])
    if "-loc" in sys.argv:
        ind = sys.argv.index("-loc")
        kwargs['location'] = sys.argv[ind+1]
    if "-A" in sys.argv:
        kwargs['noave'] = True
    if "-ncn" in sys.argv:
        ind = sys.argv.index("-ncn")
        kwargs['samp_con'] = sys.argv[ind+1]
    if '-LP' in sys.argv:
        ind = sys.argv.index("-LP")
        kwargs['codelist'] = sys.argv[ind+1]
    if "-V" in sys.argv:
        ind = sys.argv.index("-V")
        kwargs['coil'] = sys.argv[ind+1]
    if '-ARM_dc' in sys.argv:
        ind = sys.argv.index("-ARM_dc")
        kwargs['arm_labfield'] = sys.argv[ind+1]
    if '-ARM_temp' in sys.argv:
        ind = sys.argv.index('-ARM_temp')
        kwargs['trm_peakT'] = sys.argv[ind+1]
    if '-mv' in sys.argv:
        ind = sys.argv.index('-mv')
        kwargs['mv'] = sys.argv[ind+1]

    convert.ldeo(**kwargs)


if __name__ == '__main__':
    main()

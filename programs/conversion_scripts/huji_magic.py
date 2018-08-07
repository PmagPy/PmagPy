#!/usr/bin/env python
"""

NAME
    huji_magic.py

DESCRIPTION
    converts HUJI format files to measurements format files

SYNTAX
    huji_magic.py [command line options]

OPTIONS
    -h: prints the help message and quits.
    -usr USER: Colon delimited list of analysts, default is ""
    -ID: directory for input file if not included in -f flag
    -f FILE: specify infile file, required
    -fd FILE: specify HUJI datafile with sample orientations
    -WD: directory to output files to (default : current directory)
    -F FILE: specify output  measurements file, default is measurements.txt
    -Fsp FILE: specify output specimens.txt file, default is specimens.txt
    -Fsa FILE: specify output samples.txt file, default is samples.txt
    -Fsi FILE: specify output sites.txt file, default is sites.txt
    -Flo FILE: specify output locations.txt file, default is locations.txt
    -A: don't average replicate measurements
    -LP [colon delimited list of protocols, include all that apply]
        AF:  af demag
        T: thermal including thellier but not trm acquisition
        N: NRM only
        TRM: trm acquisition
        ANI: anisotropy experiment
        CR: cooling rate experiment.
            The treatment coding of the measurement file should be: XXX.00,XXX.10, XXX.20 ...XX.70 etc. (XXX.00 is optional)
            where XXX in the temperature and .10,.20... are running numbers of the cooling rates steps.
            XXX.00 is optional zerofield baseline. XXX.70 is alteration check.
            syntax in sio_magic is: -LP CR xxx,yyy,zzz,.....xx
            where xx, yyy,zzz...xxx  are cooling time in [K/minutes], seperated by comma, ordered at the same order as XXX.10,XXX.20 ...XX.70
            if you use a zerofield step then no need to specify the cooling rate for the zerofield

    -spc NUM : specify number of characters to designate a specimen, default = 0
    -loc LOCNAME : specify location/study name, must have either LOCNAME or SAMPFILE or be a synthetic
    -dc B PHI THETA: dc lab field (in micro tesla) and phi,theta, default is none
          NB: use PHI, THETA = -1 -1 to signal that it changes, i.e. in anisotropy experiment
    # to do! -ac B : peak AF field (in mT) for ARM acquisition, default is none
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
    INPUT
        separate experiments ( AF, thermal, thellier, trm aquisition) should be seperate  files
        (eg. af.txt, thermal.txt, etc.)

        HUJI masurement file format  (space delimited text):
        Spec lab-running-numbe-code  Date Hour Treatment-type(T/N/A) Treatment(XXX.XX) dec(geo) inc(geo) dec(tilt) inc(tilt)

    ---------

    conventions:
    Spec: specimen name
    Treat:  treatment step
        XXX T in Centigrade
        XXX AF in mT
        for special experiments:
          Thellier:
            XXX.0  first zero field step
            XXX.1  first in field step [XXX.0 and XXX.1 can be done in any order]
            XXX.2  second in-field step at lower temperature (pTRM check)

          ATRM:
            X.00 optional baseline
            X.1 ATRM step (+X)
            X.2 ATRM step (+Y)
            X.3 ATRM step (+Z)
            X.4 ATRM step (-X)
            X.5 ATRM step (-Y)
            X.6 ATRM step (-Z)
            X.7 optional alteration check (+X)

          TRM:
            XXX.YYY  XXX is temperature step of total TRM
                     YYY is dc field in microtesla

     Intensity assumed to be total moment in 10^3 Am^2 (emu)
     Declination:  Declination in specimen coordinate system
     Inclination:  Inclination in specimen coordinate system

     Optional metatdata string:  mm/dd/yy;hh:mm;[dC,mT];xx.xx;UNITS;USER;INST;NMEAS
         hh in 24 hours.
         dC or mT units of treatment XXX (see Treat above) for thermal or AF respectively
         xx.xxx   DC field
         UNITS of DC field (microT, mT)
         INST:  instrument code, number of axes, number of positions (e.g., G34 is 2G, three axes, measured in four positions)
         NMEAS: number of measurements in a single position (1,3,200...)
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
    if '-Fsi' in sys.argv:
        ind = sys.argv.index("-Fsi")
        kwargs['site_file'] = sys.argv[ind+1]
    if '-Flo' in sys.argv:
        ind = sys.argv.index("-Flo")
        kwargs['loc_file'] = sys.argv[ind+1]
    if '-f' in sys.argv:
        ind = sys.argv.index("-f")
        kwargs['magfile'] = sys.argv[ind+1]
    if '-fd' in sys.argv:
        ind = sys.argv.index("-fd")
        kwargs['datafile'] = sys.argv[ind+1]
    if "-dc" in sys.argv:
        ind = sys.argv.index("-dc")
        kwargs['labfield'] = float(sys.argv[ind+1])
        kwargs['phi'] = float(sys.argv[ind+2])
        kwargs['theta'] = float(sys.argv[ind+3])
    #if "-ac" in sys.argv:
    #    ind = sys.argv.index("-ac")
    #    kwargs['peakfield'] = float(sys.argv[ind+1])
    if "-spc" in sys.argv:
        ind = sys.argv.index("-spc")
        kwargs['specnum'] = int(sys.argv[ind+1])
    if "-loc" in sys.argv:
        ind = sys.argv.index("-loc")
        kwargs['location'] = sys.argv[ind+1]
    if "-ncn" in sys.argv:
        ind = sys.argv.index("-ncn")
        kwargs['samp_con'] = sys.argv[ind+1]
    if '-LP' in sys.argv:
        ind = sys.argv.index("-LP")
        kwargs['codelist'] = sys.argv[ind+1]
    if '-A' in sys.argv:
        kwargs['noave'] = True

    res, error_message = convert.huji(**kwargs)
    if not res:
        print(__doc__)

if __name__ == "__main__":
    main()

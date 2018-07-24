#!/usr/bin/env python
"""
NAME
    sio_magic.py

DESCRIPTION
    converts SIO .mag format files to magic_measurements format files

SYNTAX
    sio_magic.py [command line options]

OPTIONS
    -h: prints the help message and quits.
    -usr USER: Colon delimited list of analysts, default is ""
    -WD: directory to output files to (default : current directory)
    -f FILE: specify .mag format input file, required
    -fsa SAMPFILE : specify samples.txt file relating samples, site and locations names,default is none -- values in SAMPFILE will override selections for -loc (location), -spc (designate specimen), and -ncn (sample-site naming convention) (DEPRICIATED)
    -Fsp FILE: specify output specimens.txt file, default is specimens.txt
    -Fsa FILE: specify output samples.txt file, default is samples.txt
    -Fsi FILE: specify output sites.txt file, default is sites.txt # LORI
    -Flo FILE: specify output locations.txt file, default is locations.txt
    -LP [colon delimited list of protocols, include all that apply]
        AF:  af demag
        T: thermal including thellier but not trm acquisition
        S: Shaw method
        I: IRM (acquisition)
        I3d: 3D IRM experiment
        N: NRM only
        TRM: trm acquisition
        ANI: anisotropy experiment
        D: double AF demag
        G: triple AF demag (GRM protocol)
        CR: cooling rate experiment.
            The treatment coding of the measurement file should be: XXX.00,XXX.10, XXX.20 ...XX.70 etc. (XXX.00 is optional)
            where XXX in the temperature and .10,.20... are running numbers of the cooling rates steps.
            XXX.00 is optional zerofield baseline. XXX.70 is alteration check.
            syntax in sio_magic is: -LP CR xxx,yyy,zzz,..... xxx -A
            where xxx, yyy, zzz...xxx  are cooling time in [K/minutes], seperated by comma, ordered at the same order as XXX.10,XXX.20 ...XX.70
            if you use a zerofield step then no need to specify the cooling rate for the zerofield
            It is important to add to the command line the -A option so the measurements will not be averaged.
            But users need to make sure that there are no duplicate measurements in the file
    -V [1,2,3] units of IRM field in volts using ASC coil #1,2 or 3
    -spc NUM : specify number of characters to designate a  specimen, default = 0
    -tz TIMEZONE: timezone of measurements used to convert to UTC and format for MagIC database
    -loc LOCNAME : specify location/study name, must have either LOCNAME or SAMPFILE or be a synthetic
    -syn INST TYPE: sets these specimens as synthetics created at institution INST and of type TYPE
    -ins INST : specify which demag instrument was used (e.g, SIO-Suzy or SIO-Odette),default is ""
    -dc B PHI THETA: dc lab field (in micro tesla) and phi,theta, default is none
          NB: use PHI, THETA = -1 -1 to signal that it changes, i.e. in anisotropy experiment
    -ac B : peak AF field (in mT) for ARM acquisition, default is none
    -ncn NCON:  specify naming convention: default is #1 below
    -A: don't average replicate measurements
    -lat: site latitude (will also be used for bounding lattitudes of location)
    -lon: site longitude (will also be used for bounding longitude of location)
   Sample naming convention:
        [1] XXXXY: where XXXX is an arbitrary length site designation and Y
            is the single character sample designation.  e.g., TG001a is the
            first sample from site TG001.    [default]
        [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
        [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
        [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
        [5] site name same as sample
        [6] site is entered under a separate column NOT CURRENTLY SUPPORTED
        [7-Z] [XXXX]YYY:  XXXX is site designation with Z characters with sample name XXXXYYYY
        NB: all others you will have to customize your self
             or e-mail ltauxe@ucsd.edu for help.

        [8] synthetic - has no site name
        [9] ODP naming convention
INPUT
    Best to put separate experiments (all AF, thermal, thellier, trm aquisition, Shaw, etc.) in
       seperate .mag files (eg. af.mag, thermal.mag, etc.)

    Format of SIO .mag files:
    Spec Treat CSD Intensity Declination Inclination [optional metadata string]

    Spec: specimen name
    Treat:  treatment step
        XXX T in Centigrade
        XXX AF in mT
        for special experiments:
          Thellier:
            XXX.0  first zero field step
            XXX.1  first in field step [XXX.0 and XXX.1 can be done in any order]
            XXX.2  second in-field step at lower temperature (pTRM check)
            XXX.3  second zero-field step after infield (pTRM check step)
                   XXX.3 MUST be done in this order [XXX.0, XXX.1 [optional XXX.2] XXX.3]
          AARM:
            X.00  baseline step (AF in zero bias field - high peak field)
            X.1   ARM step (in field step)  where
               X is the step number in the 15 position scheme
                  (see Appendix to Lecture 13 - http://magician.ucsd.edu/Essentials_2)
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
     Inclination:  Declination in specimen coordinate system

     Optional metatdata string:  mm/dd/yy;hh:mm;[dC,mT];xx.xx;UNITS;USER;INST;NMEAS
         hh in 24 hours.
         dC or mT units of treatment XXX (see Treat above) for thermal or AF respectively
         xx.xxx   DC field
         UNITS of DC field (microT, mT)
         INST:  instrument code, number of axes, number of positions (e.g., G34 is 2G, three axes,
                measured in four positions)
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
    if '-WD' in sys.argv:
        ind = sys.argv.index("-WD")
        kwargs['dir_path'] = sys.argv[ind+1]
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
    if '-f' in sys.argv:
        ind = sys.argv.index("-f")
        kwargs['mag_file'] = sys.argv[ind+1]
    if "-dc" in sys.argv:
        ind = sys.argv.index("-dc")
        kwargs['labfield'] = float(sys.argv[ind+1])
        kwargs['phi'] = float(sys.argv[ind+2])
        kwargs['theta'] = float(sys.argv[ind+3])
    if "-ac" in sys.argv:
        ind = sys.argv.index("-ac")
        kwargs['peakfield'] = float(sys.argv[ind+1])
    if "-spc" in sys.argv:
        ind = sys.argv.index("-spc")
        kwargs['specnum'] = int(sys.argv[ind+1])
    if "-loc" in sys.argv:
        ind = sys.argv.index("-loc")
        kwargs['location'] = sys.argv[ind+1]
    if "-fsa" in sys.argv:
        ind = sys.argv.index("-fsa")
        kwargs['samp_infile'] = sys.argv[ind+1]
    if '-syn' in sys.argv:
        syn = 1
        ind = sys.argv.index("-syn")
        kwargs['institution'] = sys.argv[ind+1]
        kwargs['syntype'] = sys.argv[ind+2]
        if '-fsy' in sys.argv:
            ind = sys.argv.index("-fsy")
            synfile = sys.argv[ind+1]
    if "-ins" in sys.argv:
        ind = sys.argv.index("-ins")
        kwargs['instrument'] = sys.argv[ind+1]
    if "-A" in sys.argv:
        kwargs['noave'] = 1
    if "-ncn" in sys.argv:
        ind = sys.argv.index("-ncn")
        kwargs['samp_con'] = sys.argv[ind+1]
    if '-LP' in sys.argv:
        ind = sys.argv.index("-LP")
        kwargs['codelist'] = sys.argv[ind+1]
        if 'CR' in sys.argv:
            ind = sys.argv.index("CR")
            kwargs['cooling_rates'] = sys.argv[ind+1]
    if "-V" in sys.argv:
        ind = sys.argv.index("-V")
        kwargs['coil'] = sys.argv[ind+1]
    if "-lat" in sys.argv:
        ind = sys.argv.index("-lat")
        kwargs["lat"] = sys.argv[ind+1]
    if "-lon" in sys.argv:
        ind = sys.argv.index("-lon")
        kwargs["lon"] = sys.argv[ind+1]
    if "-tz" in sys.argv:
        ind = sys.argv.index("-tz")
        kwargs["timezone"] = sys.argv[ind+1]

    convert.sio(**kwargs)


if __name__ == "__main__":
    main()

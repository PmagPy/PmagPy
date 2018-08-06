#!/usr/bin/env python
"""
NAME
    generic_magic.py

DESCRIPTION
    converts magnetometer files in generic format to MagIC measurements format

SYNTAX
    generic_magic.py [command line options]

OPTIONS
    -h: shows this help message
    -usr USER: identify user, default is ""
    -ID: directory for input file if not included in -f flag
    -f FILE: specify  input file, required
    -WD: directory to output files to (default : current directory)
    -F FILE: specify output  measurements file, default is measurements.txt
    -Fsp FILE: specify output specimens.txt file, default is specimens.txt
    -Fsa FILE: specify output samples.txt file, default is samples.txt
    -Fsi FILE: specify output sites.txt file, default is sites.txt
    -Flo FILE: specify output locations.txt file, default is locations.txt

    -exp EXPERIMENT-TYPE
        Demag:
            AF and/or Thermal
        PI:
            paleointenisty thermal experiment (ZI/IZ/IZZI)
        ATRM n:

            ATRM in n positions (n=6)

        AARM n:
            AARM in n positions
        CR:
            cooling rate experiment
            The treatment coding of the measurement file should be: XXX.00,XXX.10, XXX.20 ...XX.70 etc. (XXX.00 is optional)
            where XXX in the temperature and .10,.20... are running numbers of the cooling rates steps.
            XXX.00 is optional zerofield baseline. XXX.70 is alteration check.
            syntax in sio_magic is: -LP CR xxx,yyy,zzz,.....xx -A
            where xx, yyy,zzz...xxx  are cooling rates in [K/minutes], seperated by comma, ordered at the same order as XXX.10,XXX.20 ...XX.70

            No need to specify the cooling rate for the zerofield
            It is important to add to the command line the -A option so the measurements will not be averaged.
            But users need to make sure that there are no duplicate meaurements in the file

        NLT:
            non-linear-TRM experiment

    -samp X Y
        specimen-sample naming convention.
        X determines which kind of convention (initial characters, terminal characters, or delimiter
        Y determines how many characters to remove to go from specimen --> sample OR which delimiter to use
        X=0 Y=n: specimen is distinguished from sample by n initial characters.
                 (example: "generic_magic.py -samp 0 4"
                  if n=4 then and specimen = mgf13a then sample = mgf13)
        X=1 Y=n: specimen is distiguished from sample by n terminate characters.
                 (example: "generic_magic.py -samp 1 1)
                  if n=1 then and specimen = mgf13a then sample = mgf13)
        X=2 Y=c: specimen is distinguishing from sample by a delimiter.
                 (example: "generic_magic.py -samp 2 -"
                  if c=- then and specimen = mgf13-a then sample = mgf13)
        default: sample is the same as specimen name

    -site X Y
        sample-site naming convention.
        X determines which kind of convention (initial characters, terminal characters, or delimiter
        Y determines how many characters to remove to go from sample --> site OR which delimiter to use
        X=0 Y=n: sample is distiguished from site by n initial characters.
                 (example: "generic_magic.py --site 0 3"
                  if n=3 then and sample = mgf13 then sample = mgf)
        X=1 Y=n: sample is distiguished from site by n terminate characters.
                 (example: "generic_magic.py --site 1 2"
                  if n=2 and sample = mgf13 then site = mgf)
        X=2 Y=c: specimen is distiguishing from sample by a delimiter.
                 (example: "generic_magic.py -site 2 -"
                  if c='-' and sample = 'mgf-13' then site = mgf)
        default: site name is the same as sample name

    -loc LOCNAME: specify location/study name.
    -lat LAT: latitude of site (also used as bounding latitude for location)
    -lon LON: longitude of site (also used as bounding longitude for location)
    -dc B PHI THETA:
        B: dc lab field (in micro tesla)
        PHI (declination). takes numbers from 0 to 360
        THETA (inclination). takes numbers from -90 to 90
        NB: use PHI, THETA = -1 -1 to signal that it changes, i.e. in anisotropy experiment.
    -A: don't average replicate measurements. Take the last measurement from replicate measurements.

INPUT

    A generic file is a tab-delimited file. Each column should have a header.
    The file must include the following headers (the order of the columns is not important):

        specimen
            string specifying specimen name

        treatment:
            a number with one or two decimal point (X.Y)
            coding for thermal demagnetization:
                0.0 or 0 is NRM.
                X is temperature in celsius
                Y is always 0
            coding for AF demagnetization:
                0.0 or 0 is NRM.
                X is AF peak field in mT
                Y is always 0
            coding for Thellier-type experiment:
                0.0 or 0 is NRM
                X is temperature in celsius
                Y=0: zerofield
                Y=1: infield
                Y=2: pTRM check
                Y=3: pTRM tail check
                Y=4: Additivity check
                # Ron, Add also 5 for Thellier protocol
            coding for ATRM experiment (6 poitions):
                X is temperature in celsius
                Y=0: zerofield baseline to be subtracted
                Y=1: +x
                Y=2: -x
                Y=3: +y
                Y=4: -y
                Y=5: +z
                Y=6: -z
                Y=7: alteration check
            coding for NLT experiment:
                X is temperature in celsius
                Y=0: zerofield baseline to be subtracted
                Y!=0: oven field  in microT
            coding for CR experiment:
                see "OPTIONS" list above

        treatment_type:
            N: NRM
            A: AF
            T: Thermal

        moment:
            magnetic moment in emu !!

    In addition, at least one of the following headers are required:

        dec_s:
            declination in specimen coordinate system (0 to 360)
        inc_s:
            inclination in specimen coordinate system (-90 to 90)

        dec_g:
            declination in geographic coordinate system (0 to 360)
        inc_g:
            inclination in geographic coordinate system (-90 to 90)

        dec_t:
            declination in tilt-corrected coordinate system (0 to 360)
        inc_t:
            inclination in tilt-corrected coordinate system (-90 to 90)
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
        ind = sys.argv.index("-WD")
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
    if '-Flo' in sys.argv:  # Kevin addition
        ind = sys.argv.index("-Flo")
        kwargs['loc_file'] = sys.argv[ind+1]
    if '-f' in sys.argv:
        ind = sys.argv.index("-f")
        kwargs['magfile'] = sys.argv[ind+1]
    if "-dc" in sys.argv:
        ind = sys.argv.index("-dc")
        kwargs['labfield'] = sys.argv[ind+1]
        kwargs['labfield_phi'] = sys.argv[ind+2]
        kwargs['labfield_theta'] = sys.argv[ind+3]
    if '-exp' in sys.argv:
        ind = sys.argv.index("-exp")
        kwargs['experiment'] = sys.argv[ind+1]
    if "-samp" in sys.argv:
        ind = sys.argv.index("-samp")
        kwargs['sample_nc'] = []
        kwargs['sample_nc'].append(sys.argv[ind+1])
        kwargs['sample_nc'].append(sys.argv[ind+2])
    if "-site" in sys.argv:
        ind = sys.argv.index("-site")
        kwargs['site_nc'] = []
        kwargs['site_nc'].append(sys.argv[ind+1])
        kwargs['site_nc'].append(sys.argv[ind+2])
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

    res, error = convert.generic(**kwargs)
    if not res:
        print(__doc__)


if __name__ == '__main__':
    main()

#!/usr/bin/env python
"""
NAME
    xpeem_magic.py

DESCRIPTION
    Creates MagIC header file and convert XPEEM text files into a MagIC format measurement file.

SYNTAX
    xpeem_magic.py [command line options]

OPTIONS
    -h: prints the help message and quits
    -ID: directory for input files, default = current directory
    -WD: directory for output files, default = current directory
    -specname SPECIMEN_NAME: specify the specimen full name
    -specid SPECIMEN_ID: specify the specimen identifier (i.e., short name)
    -spectype SPECIMEN_TYPE: specify the specimen type
    -cite CITATION: specify the citation, default = This study
    -specage SPECIMEN_AGE: specify the age of the specimen
    -specage1s SPECIMENT_AGE_UNCERTAINTY: specify the 1-sigma uncertainty on the age of the specimen
    -datemethod DATING_METHOD: specify the dating method, default = GM-ARAR
    -dateunit DATING_UNIT: specify the dating unit, default = Ga
    -method METHOD: specify the experiment method, default = LP-XPEEM-3
    -sitenames SITE_NAMES: colon delimited list of names of sites, which corresponds to the K-T interfaces (i.e., "A,B")
    -samplenb SAMPLES_NUMBERS: colon delimited list of numbers of samples for each site, which corresponds to the locations on each K-T interfaces (i.e., "36,36")
    -int PALEOINTENSITY: colon delimited list of paleointensities for each site (i.e., "31,32")
    -int1s UNCERTAINTY: colon delimited list of 1 sigma uncertainties in paleointensity for each site (i.e., "5,6")
    -x X_PIXEL_SPACING: specify the x spacing of the measurement in meters, default = 9.488e-9
    -y Y_PIXEL_SPACING: specify the y spacing of the measurement in meters, default = 9.709e-9
    -measnum MEAS_NUMBER: specify the starting measurement number, default = 1
    -expnum EXP_NUMBER: specify the starting number for labelling measurement files, default = 1
    
INPUT
    The input text files are created from XPEEM average images.
    Input file naming convention:
        [1] 2-letter-identifier for the meteorite
        [2] interface
        [3] location (2 digit)
        [4] "-"
        [5] rotation (starting with "r")
        [6] energy level (on/off)
        [7] polarization (L/R)
    Example: TeA01-r1offR.txt
    Specimen = TeA01
    Experiment name = TeA01-r1offR
    The measurement files will be put in a directory named "measurements".
    
EXAMPLE
    Command line for the example dataset:
    python xpeem_magic.py -ID "." -WD "." -header -specname "Miles" -specid "Mi" -spectype "IIE iron meteorite" -cite "This study" -specage "4.408" -specage1s "0.009" -datemethod "GM-ARAR" -dateunit "Ga" -method "LP-XPEEM-3" -sitenames "A,B" -samplenb "36,36" -int "32,31" -int1s "5,6" -x 9.488e-9 -y 9.709e-9 -measnum 1 -expnum 1

"""

import sys,os
import numpy as np
from pmagpy import convert_2_magic as convert

def do_help():
    """
    returns help string of script
    """
    return __doc__


def main():
    kwargs = {}
    if '-h' in sys.argv:
        help(__name__)
        sys.exit()
    if '-ID' in sys.argv:
        ind=sys.argv.index('-ID')
        kwargs['input_dir_path'] = sys.argv[ind+1]
    else:
        kwargs['input_dir_path'] = '.'
    if '-WD' in sys.argv:
        ind=sys.argv.index('-WD')
        kwargs['output_dir_path'] = sys.argv[ind+1]
    else:
        kwargs['output_dir_path'] = '.'
    if '-specname' in sys.argv:
        ind=sys.argv.index('-specname')
        kwargs['spec_name'] = sys.argv[ind+1]
    if '-specid' in sys.argv:
        ind=sys.argv.index('-specid')
        kwargs['spec_id'] = sys.argv[ind+1]
    if '-spectype' in sys.argv:
        ind=sys.argv.index('-spectype')
        kwargs['spec_type'] = sys.argv[ind+1]
    if '-cite' in sys.argv:
        ind=sys.argv.index('-cite')
        kwargs['citation'] = sys.argv[ind+1]
    else:
        kwargs['citation'] = 'This study'
    if '-specage' in sys.argv:
        ind=sys.argv.index('-specage')
        kwargs['spec_age'] = sys.argv[ind+1]
    if '-specage1s' in sys.argv:
        ind=sys.argv.index('-specage1s')
        kwargs['spec_age_1s'] = sys.argv[ind+1]
    if '-datemethod' in sys.argv:
        ind=sys.argv.index('-datemethod')
        kwargs['dating_method'] = sys.argv[ind+1]
    else:
        kwargs['dating_method'] = 'GM-ARAR'
    if '-dateunit' in sys.argv:
        ind=sys.argv.index('-dateunit')
        kwargs['dating_unit'] = sys.argv[ind+1]
    else:
        kwargs['dating_unit'] = 'Ga'
    if '-method' in sys.argv:
        ind=sys.argv.index('-method')
        kwargs['method'] = sys.argv[ind+1]
    else:
        kwargs['method'] = 'LP-XPEEM-3'
    if '-sitenames' in sys.argv:
        ind=sys.argv.index('-sitenames')
        kwargs['sitenames'] = sys.argv[ind+1].split(",")
    if '-samplenb' in sys.argv:
        ind=sys.argv.index('-samplenb')
        kwargs['nb_samples'] = sys.argv[ind+1].split(",")
    if '-int' in sys.argv:
        ind=sys.argv.index('-int')
        kwargs['paleoint'] = sys.argv[ind+1].split(",")
    if '-int1s' in sys.argv:
        ind=sys.argv.index('-int1s')
        kwargs['paleoint_1s'] = sys.argv[ind+1].split(",")
    if '-x' in sys.argv:
        ind=sys.argv.index('-x')
        kwargs['x_spacing']=float(sys.argv[ind+1])
    else:
        kwargs['x_spacing']=9.488e-9
    if '-y' in sys.argv:
        ind=sys.argv.index('-y')
        kwargs['y_spacing'] = float(sys.argv[ind+1])
    else:
        kwargs['x_spacing'] = 9.709e-9
    if '-measnum' in sys.argv:
        ind=sys.argv.index('-measnum')
        kwargs['meas_num'] = int(sys.argv[ind+1])
    else:
        kwargs['meas_num'] = 1
    if '-expnum' in sys.argv:
        ind=sys.argv.index('-expnum')
        kwargs['exp_num'] = int(sys.argv[ind+1])
    else:
        kwargs['exp_num'] = 1
        
    convert.xpeem(**kwargs)

if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""
NAME
    irm_magic.py

DESCRIPTION
    Creates MagIC file from an IRM excel file.

SYNTAX
    irm_magic.py [command line options]

OPTIONS
    -h: prints the help message and quits
    -ID DIRECTORY: directory for input files, default = current directory
    -WD DIRECTORY: directory for output files, default = current directory
    -f File: the irm excel data file
    -cite CITATION: specify the citation, default = This study
    
EXAMPLE
    Command line for the example dataset:

"""

import sys
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
        kwargs['input_dir_path'] = './'
    if '-WD' in sys.argv:
        ind=sys.argv.index('-WD')
        kwargs['output_dir_path'] = sys.argv[ind+1]
    else:
        kwargs['output_dir_path'] = './'
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        kwargs['mag_file'] = sys.argv[ind+1]
    else:
        print("You must specify the IRM excel data file name with the -f flag.") 
        exit()
    if '-cit' in sys.argv:
        ind=sys.argv.index('-cit')
        kwargs['citation'] = sys.argv[ind+1]
    else:
        kwargs['citation'] = 'This study'
        
    convert.irm(**kwargs)

if __name__ == "__main__":
    main()

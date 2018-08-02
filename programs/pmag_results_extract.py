#!/usr/bin/env python
from __future__ import print_function
import sys
import os
import pmagpy.pmag as pmag
import pmagpy.ipmag as ipmag

def main():
    """
    NAME 
        pmag_results_extract.py

    DESCRIPTION
        make a tab delimited output file from pmag_results table
 
    SYNTAX
        pmag_results_extract.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f RFILE, specify pmag_results table; default is pmag_results.txt
        -fa AFILE, specify er_ages table; default is NONE
        -fsp SFILE, specify pmag_specimens table, default is NONE
        -fcr CFILE, specify pmag_criteria table, default is NONE
        -g include specimen_grade in table - only works for PmagPy generated pmag_specimen formatted files.
        -tex,  output in LaTeX format
    """
    do_help = pmag.get_flag_arg_from_sys('-h')
    if do_help:
        print(main.__doc__)
        return False
    res_file = pmag.get_named_arg('-f', 'pmag_results.txt')
    crit_file = pmag.get_named_arg('-fcr', '')
    spec_file = pmag.get_named_arg('-fsp', '')
    age_file = pmag.get_named_arg('-fa', '')
    grade = pmag.get_flag_arg_from_sys('-g')
    latex = pmag.get_flag_arg_from_sys('-tex')
    WD = pmag.get_named_arg('-WD', os.getcwd())
    ipmag.pmag_results_extract(res_file, crit_file, spec_file, age_file, latex, grade, WD)

        
if __name__ == "__main__":
    main()

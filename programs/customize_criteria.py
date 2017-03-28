#!/usr/bin/env python
from __future__ import print_function
from builtins import input
import sys
import pmagpy.pmag as pmag

def main():
    """
    NAME
        customize_criteria.py

    DESCRIPTION
        Allows user to specify acceptance criteria, saves them in pmag_criteria.txt

    SYNTAX
        customize_criteria.py [-h][command line options]

    OPTIONS
        -h prints help message and quits
        -f IFILE, reads in existing criteria
        -F OFILE, writes to pmag_criteria format file

    DEFAULTS
         IFILE: pmag_criteria.txt
         OFILE: pmag_criteria.txt
  
    OUTPUT
        creates a pmag_criteria.txt formatted output file
    """
    infile,critout="","pmag_criteria.txt"
# parse command line options
    if  '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        infile=sys.argv[ind+1]
        crit_data,file_type=pmag.magic_read(infile)
        if file_type!='pmag_criteria':
            print('bad input file')
            print(main.__doc__)
            sys.exit()
        print("Acceptance criteria read in from ", infile)
    if '-F' in sys.argv:
        ind=sys.argv.index('-F')
        critout=sys.argv[ind+1]
    Dcrit,Icrit,nocrit=0,0,0
    custom='1'
    crit=input(" [0] Use no acceptance criteria?\n [1] Use default criteria\n [2] customize criteria \n ")
    if crit=='0':
        print('Very very loose criteria saved in ',critout)
        crit_data=pmag.default_criteria(1)
        pmag.magic_write(critout,crit_data,'pmag_criteria')
        sys.exit()
    crit_data=pmag.default_criteria(0)
    if crit=='1':
        print('Default criteria saved in ',critout)
        pmag.magic_write(critout,crit_data,'pmag_criteria')
        sys.exit()
    CritRec=crit_data[0]
    crit_keys=list(CritRec.keys())
    crit_keys.sort()
    print("Enter new threshold value.\n Return to keep default.\n Leave blank to not use as a criterion\n ")
    for key in crit_keys:
        if key!='pmag_criteria_code' and key!='er_citation_names' and key!='criteria_definition' and CritRec[key]!="":
            print(key, CritRec[key])
            new=input('new value: ')
            if new != "": CritRec[key]=(new)
    pmag.magic_write(critout,[CritRec],'pmag_criteria')
    print("Criteria saved in pmag_criteria.txt")

if __name__ == "__main__":
    main()

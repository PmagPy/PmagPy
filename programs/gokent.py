#!/usr/bin/env python
from __future__ import print_function
from builtins import input
import sys
import pmagpy.pmag as pmag

def main():
    """
    NAME
       gokent.py

    DESCRIPTION
       calculates Kent parameters from dec inc data

    INPUT FORMAT
       takes dec/inc as first two columns in space delimited file

    SYNTAX
       gokent.py [options]

    OPTIONS
        -h prints help message and quits
        -i for interactive filename entry
        -f FILE, specify filename
        -F FILE, specifies output file name
        < filename for reading from standard input

    OUTPUT
       mean dec, mean inc, Eta, Deta, Ieta, Zeta, Zdec, Zinc, N
    """
    if len(sys.argv) > 0:
        if '-h' in sys.argv: # check if help is needed
            print(main.__doc__)
            sys.exit() # graceful quit
        if '-f' in sys.argv:
            ind=sys.argv.index('-f')
            file=sys.argv[ind+1]
            f=open(file,'r')
            data=f.readlines()
        elif '-i' in sys.argv: # ask for filename
            file=input("Enter file name with dec, inc data: ")
            f=open(file,'r')
            data=f.readlines()
        else:
#
            data=sys.stdin.readlines() # read in data from standard input
    ofile = ""
    if '-F' in sys.argv:
        ind = sys.argv.index('-F')
        ofile= sys.argv[ind+1]
        out = open(ofile, 'w + a')
    DIs= [] # set up list for dec inc data
    for line in data:   # read in the data from standard input
        if '\t' in line:
            rec=line.split('\t') # split each line on space to get records
        else:
            rec=line.split() # split each line on space to get records
        DIs.append((float(rec[0]),float(rec[1])))
#
    kpars=pmag.dokent(DIs,len(DIs))
    output = '%7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %i' % (kpars["dec"],kpars["inc"],kpars["Eta"],kpars["Edec"],kpars["Einc"],kpars["Zeta"],kpars["Zdec"],kpars["Zinc"],kpars["n"])
    if ofile == "":
        print(output)
    else:
        out.write(output+'\n')
#    print '%7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %i' % (kpars["dec"],kpars["inc"],kpars["Eta"],kpars["Edec"],kpars["Einc"],kpars["Zeta"],kpars["Zdec"],kpars["Zinc"],kpars["n"])
    #
if __name__ == "__main__":
    main()

#!/usr/bin/env python
import sys
import pmagpy.pmag as pmag

def main():
    """
    NAME
       goprinc.py

    DESCRIPTION
       calculates Principal components from dec/iinc data

    INPUT FORMAT
       takes dec/inc as first two columns in space delimited file

    SYNTAX
       goprinc.py [options]  [< filename]

    OPTIONS
        -h prints help message and quits
        -i for interactive filename entry
        -f FILE, specify input file
        -F FILE, specifies output file name
        < filename for reading from standard input

    OUTPUT
       tau_1 V1_Dec, V1_Inc, tau_2 V2_Dec V2_Inc, tau_3 V3_Dec V3_Inc, N

    """
    if len(sys.argv) > 0:
        if '-h' in sys.argv: # check if help is needed
            print main.__doc__
            sys.exit() # graceful quit
        if '-f' in sys.argv:
            ind=sys.argv.index('-f')
            file=sys.argv[ind+1]
            f=open(file,'rU')
            data=f.readlines()
        elif '-i' in sys.argv: # ask for filename
            file=raw_input("Enter file name with dec, inc data: ")
            f=open(file,'rU')
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
    ppars=pmag.doprinc(DIs)
    output = '%7.5f %7.1f %7.1f %7.5f %7.1f %7.1f %7.5f %7.1f %7.1f %i' % (ppars["tau1"],ppars["dec"],ppars["inc"],ppars["tau2"],ppars["V2dec"],ppars["V2inc"],ppars["tau3"],ppars["V3dec"],ppars["V3inc"],ppars["N"])
    if ofile == "":
        print output
    else:
        out.write(output+'\n')
    #
if __name__ == "__main__":
    main()

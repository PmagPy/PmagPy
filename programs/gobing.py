#!/usr/bin/env python
import sys
import pmagpy.pmag as pmag

def main():
    """
    NAME
       gobing.py

    DESCRIPTION
       calculates Bingham parameters from dec inc data

    INPUT FORMAT
       takes dec/inc as first two columns in space delimited file

    SYNTAX
       gobing.py [options]  

    OPTIONS
        -f FILE to read from FILE
        -F, specifies output file name
        < filename for reading from standard input

    OUTPUT
       mean dec, mean inc, Eta, Deta, Ieta, Zeta, Zdec, Zinc, N
    """
    if len(sys.argv) > 0:
        if '-h' in sys.argv: # check if help is needed
            print main.__doc__
            sys.exit() # graceful quit
        if '-f' in sys.argv: # ask for filename
            ind=sys.argv.index('-f')
            file=sys.argv[ind+1]
            f=open(file,'rU')
            data=f.readlines()
        else:
            data=sys.stdin.readlines() # read in data from standard input
    DIs= [] # set up list for dec inc data
    ofile = ""
    if '-F' in sys.argv: # set up output file
        ind = sys.argv.index('-F')
        ofile= sys.argv[ind+1]
        out = open(ofile, 'w + a')
    for line in data:   # read in the data from standard input
        if '\t' in line:
            rec=line.split('\t') # split each line on space to get records
        else:
            rec=line.split() # split each line on space to get records
        DIs.append((float(rec[0]),float(rec[1])))
#
    bpars=pmag.dobingham(DIs)
    output = '%7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %i' % (bpars["dec"],bpars["inc"],bpars["Eta"],bpars["Edec"],bpars["Einc"],bpars["Zeta"],bpars["Zdec"],bpars["Zinc"],bpars["n"])
    if ofile == "":
        print output
    else:
        out.write(output+'\n')
    #print '%7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %i' % (bpars["dec"],bpars["inc"],bpars["Eta"],bpars["Edec"],bpars["Einc"],bpars["Zeta"],bpars["Zdec"],bpars["Zinc"],bpars["n"])
    #

if __name__ == "__main__":
    main()

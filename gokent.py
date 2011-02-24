#!/usr/bin/env python
import pmag,sys
def main():
    """
    NAME
       gokent.py

    DESCRIPTION
       calculates Kent parameters from dec inc data

    INPUT FORMAT
       takes dec/inc as first two columns in space delimited file

    SYNTAX
       gokent.py [-h][-i][command line options]  [< filename]

    OPTIONS
        -h prints help message and quits
        -i for interactive filename entry
        -f FILE, specify filename
        < filename for reading from standard input

    OUTPUT
       mean dec, mean inc, Eta, Deta, Ieta, Zeta, Zdec, Zinc, N
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
    DIs= [] # set up list for dec inc data
    for line in data:   # read in the data from standard input
        if '\t' in line:
            rec=line.split('\t') # split each line on space to get records
        else:
            rec=line.split() # split each line on space to get records
        DIs.append((float(rec[0]),float(rec[1])))
#
    kpars=pmag.dokent(DIs,len(DIs))
    print '%7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %i' % (kpars["dec"],kpars["inc"],kpars["Eta"],kpars["Edec"],kpars["Einc"],kpars["Zeta"],kpars["Zdec"],kpars["Zinc"],kpars["n"])
    #
main()

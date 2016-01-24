#!/usr/bin/env python
import sys
import pmagpy.pmag as pmag

def main():
    """
    NAME
       gofish.py

    DESCRIPTION
       calculates fisher parameters from dec inc data

    INPUT FORMAT
       takes dec/inc as first two columns in space delimited file

    SYNTAX
       gofish.py [options]  [< filename]

    OPTIONS
        -h prints help message and quits
        -i for interactive filename entry
        -f FILE, specify input file
        -F FILE, specifies output file name
        < filename for reading from standard input
   
    OUTPUT
       mean dec, mean inc, N, R, k, a95, csd

    """
    if '-h' in sys.argv: # check if help is needed
        print main.__doc__
        sys.exit() # graceful quit
    if '-i' in sys.argv: # ask for filename
        file=raw_input("Enter file name with dec, inc data: ")
        f=open(file,'rU')
        data=f.readlines()
    elif '-f' in sys.argv:
        dat=[]
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
        f=open(file,'rU')
        data=f.readlines()
    else:
        data = sys.stdin.readlines()  # read from standard input
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
    fpars=pmag.fisher_mean(DIs)
    outstring='%7.1f %7.1f    %i %10.4f %8.1f %7.1f %7.1f'%(fpars['dec'],fpars['inc'],fpars['n'],fpars['r'],fpars['k'],fpars['alpha95'], fpars['csd'])
    if ofile == "":
        print outstring
    else:
        out.write(outstring+'\n')
    #
if __name__ == "__main__":
    main()

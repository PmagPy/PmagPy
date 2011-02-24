#!/usr/bin/env python
import sys,pmag
def main():
    """
    NAME
       vector_mean.py

    DESCRIPTION
       calculates vector mean of vector data

    INPUT FORMAT
       takes dec, inc, int as first three columns in space delimited file

    SYNTAX
       vector_mean.py [command line options]  [< filename]

    OPTIONS
        -h prints help message and quits
        -i for interactive filename entry
        -f FILE, specify input file
        < filename for reading from standard input
   
    OUTPUT
       mean dec, mean inc, R, N

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
    DIIs= [] # set up list for dec inc data
    for line in data:   # read in the data from standard input
        if '\t' in line:
            rec=line.split('\t') # split each line on space to get records
        else:
            rec=line.split() # split each line on space to get records
        DIIs.append([float(rec[0]),float(rec[1]),float(rec[2])])
#
    vpars,R=pmag.vector_mean(DIIs)
    outstring='%7.1f %7.1f   %10.3e %i'%(vpars[0],vpars[1],R,len(DIIs))
    print outstring
    #
main()

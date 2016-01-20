#!/usr/bin/env python
import sys
import pmagpy.pmag as pmag
def main():
    """
    NAME
        stats.py
   
    DEFINITION
        calculates Gauss statistics for input data

    SYNTAX
        stats [command line options][< filename]

    INPUT
        single column of numbers

    OPTIONS
        -h prints help message and quits
        -i interactive entry of file name
        -f input file name
        -F output file name
 
    OUTPUT
      N, mean, sum, sigma, (%) 
      where sigma is the standard deviation
      where % is sigma as percentage of the mean
      stderr is the standard error and 
      95% conf.=  1.96*sigma/sqrt(N)
    """
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-i' in sys.argv:
        file=raw_input("Enter file name: ")
        f=open(file,'rU')
    elif '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
        f=open(file,'rU')
    else:
        f=sys.stdin
    ofile = ""
    if '-F' in sys.argv:
        ind = sys.argv.index('-F')
        ofile= sys.argv[ind+1]
        out = open(ofile, 'w + a')
    data=f.readlines()
    dat=[]
    sum=0
    for line in data:
        rec=line.split()
        dat.append(float(rec[0]))
        sum+=float(float(rec[0]))
    mean,std=pmag.gausspars(dat)
    outdata = len(dat),mean,sum,std,100*std/mean
    if ofile == "":
        print len(dat),mean,sum,std,100*std/mean
    else:
        for i in outdata:
            i = str(i)
            out.write(i + " ")

if __name__ == "__main__":
    main()

#!/usr/bin/env python
import sys,pmag
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
    data=f.readlines()
    dat=[]
    sum=0
    for line in data:
        rec=line.split()
        dat.append(float(rec[0]))
        sum+=float(float(rec[0]))
    mean,std=pmag.gausspars(dat)
    print len(dat),mean,sum,std,100*std/mean
main()

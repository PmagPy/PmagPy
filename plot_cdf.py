#!/usr/bin/env python
import sys,pmag,math,pmagplotlib,exceptions
def main():
    """
    NAME
        plot_cdfs.py

    DESCRIPTION
        makes plots of cdfs of data in input file 

    SYNTAX
        plot_cdfs.py [-h][command line options]

    OPTIONS
        -h prints help message and quits
        -f FILE
        -t TITLE
        
    """
    title=""
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-f' in sys.argv:
       ind=sys.argv.index('-f')
       specfile=sys.argv[ind+1] 
    if '-t' in sys.argv:
       ind=sys.argv.index('-t')
       title=sys.argv[ind+1] 
    X=[]
    f=open(specfile,'rU')
    for line in f.readlines():
        rec=line.split()
        X.append(float(rec[0]))
    CDF={'X':1}
    pmagplotlib.plot_init(CDF['X'],5,5)
    pmagplotlib.plotCDF(CDF['X'],X,title,'r','')
    pmagplotlib.drawFIGS(CDF)
    try:
        raw_input('Return to save all figures, cntl-d to quit')
    except EOFError:
        print "Good bye"
        sys.exit()
    files={}
    for key in CDF.keys():
        files[key]=(key+'.svg')
    pmagplotlib.saveP(CDF,files)
main()

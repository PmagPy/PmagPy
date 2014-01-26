#!/usr/bin/env python
import sys,pmagplotlib,pmag,exceptions
import matplotlib
def main():
    """
    NAME
       revtest.py

    DESCRIPTION
       calculates bootstrap statistics to test for antipodality

    INPUT FORMAT
       takes dec/inc as first two columns in space delimited file
   
    SYNTAX
       revtest.py [-h] [-i] [command line options]
    
    OPTION
       -h prints help message and quits
       -i for interactive entry of file names from command line
       -f FILE, sets input filename on command line
       -fmt [svg,png,jpg], sets format for image output
               

    """
    D,fmt=[],'svg'
    if '-h' in sys.argv: # check if help is needed
        print main.__doc__
        sys.exit() # graceful quit
    if '-i' in sys.argv: # ask for filename
        file=raw_input("Enter file name with dec, inc data: ")
        f=open(file,'rU')
        data=f.readlines()
    elif '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
        f=open(file,'rU')
        data=f.readlines()
        if '-fmt' in sys.argv:
            ind=sys.argv.index('-fmt')
            fmt=sys.argv[ind+1]
    for line in data:
        if '\t' in line:
            rec=line.split('\t') # split each line on space to get records
        else:
            rec=line.split() # split each line on space to get records
        Dec,Inc=float(rec[0]),float(rec[1]) 
        D.append([Dec,Inc,1.])
# set up plots
    d=""
    CDF={'X':1,'Y':2,'Z':3}
    pmagplotlib.plot_init(CDF['X'],5,5)
    pmagplotlib.plot_init(CDF['Y'],5,5)
    pmagplotlib.plot_init(CDF['Z'],5,5)
#
# flip reverse mode
#
    D1,D2=pmag.flip(D)
    counter,NumSims=0,500
#
# get bootstrapped means for each data set
#
    print 'doing first mode, be patient'
    BDI1=pmag.di_boot(D1)
    print 'doing second mode, be patient'
    BDI2=pmag.di_boot(D2)
    pmagplotlib.plotCOM(CDF,BDI1,BDI2,[""])
    pmagplotlib.drawFIGS(CDF)
    ans=  raw_input("s[a]ve plots, [q]uit: ")
    if ans=='a':
        files={}
        for key in CDF.keys():
            files[key]='REV'+'_'+key+'.'+fmt 
        pmagplotlib.saveP(CDF,files)
    else:
        print 'good bye'
        sys.exit()
main()


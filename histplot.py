#!/usr/bin/env python
import sys,pmag,matplotlib
matplotlib.use("TkAgg")
import pylab,numpy
pylab.ion()
def main():
    """
    NAME
       histplot
    
    DESCRIPTION
       makes histograms for data

    OPTIONS
       -h prints help message and quits
       -f input file name
       -b binsize
    
    INPUT FORMAT
        single variable
    
    SYNTAX
       histplot.py [command line options] [<file]
    
    """
    file=""
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    elif '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
    if '-b' in sys.argv:
        ind=sys.argv.index('-b')
        binsize=int(sys.argv[ind+1])
    else:
        binsize=5
    if  file!="":
        f=open(file,'rU')
        data=f.readlines()
    else:
        data=sys.stdin.readlines()
    # read in data
    #
    Dat=[]
    for line in data:
        rec=line.split()
        Dat.append(float(rec[0]))
    Nbins=len(Dat)/binsize
    D=numpy.array(Dat)
    n,bins,patches=pylab.hist(D,bins=Nbins,facecolor='white',histtype='step',color='black',normed=1)
    D=numpy.array(D)
    pylab.axis([D.min(),D.max(),0,n.max()+.1*n.max()]) 
    pylab.xlabel('x')
    pylab.ylabel('Frequency')
    name='N = '+str(len(Dat))
    pylab.title(name)
    pylab.draw()
    p=raw_input('s[a]ve to save plot, [q]uit to exit without saving  ')
    if p=='a': 
        pylab.savefig('hist.svg')
        print 'plot saved in hist.svg'
main()

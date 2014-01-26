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
       -fmt [svg,png,pdf,eps,jpg] specify format for image, default is svg
       -N don't normize
    
    INPUT FORMAT
        single variable
    
    SYNTAX
       histplot.py [command line options] [<file]
    
    """
    file,fmt="",'svg'
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-fmt' in sys.argv:
        ind=sys.argv.index('-fmt')
        fmt=sys.argv[ind+1]
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
    if '-N' in sys.argv:
        norm=0
        ylab='Number'
    else:
        norm=1
        ylab='Frequency'
    if '-b' in sys.argv:
        ind=sys.argv.index('-b')
        binsize=int(sys.argv[ind+1])
    else:
        binsize=5
    if '-xlab' in sys.argv:
        ind=sys.argv.index('-xlab')
        xlab=sys.argv[ind+1]
    else:
        xlab='x'
    if  file!="":
        D=numpy.loadtxt(file)
    else:
        D=numpy.loadtxt(sys.stdin,dtype=numpy.float)
    # read in data
    #
    Nbins=len(D)/binsize
    n,bins,patches=pylab.hist(D,bins=Nbins,facecolor='white',histtype='step',color='black',normed=norm)
    pylab.axis([D.min(),D.max(),0,n.max()+.1*n.max()]) 
    pylab.xlabel(xlab)
    pylab.ylabel(ylab)
    name='N = '+str(len(D))
    pylab.title(name)
    pylab.draw()
    p=raw_input('s[a]ve to save plot, [q]uit to exit without saving  ')
    if p=='a': 
        pylab.savefig('hist.'+fmt)
        print 'plot saved in hist.'+fmt
main()

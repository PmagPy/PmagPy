#!/usr/bin/env python
import sys
import matplotlib
if matplotlib.get_backend() != "TKAgg":
  matplotlib.use("TKAgg")

import numpy
import pylab
pylab.ion()


def main():
    """
    NAME
       histplot.py
    
    DESCRIPTION
       makes histograms for data

    OPTIONS
       -h prints help message and quits
       -f input file name
       -b binsize
       -fmt [svg,png,pdf,eps,jpg] specify format for image, default is svg
       -sav save figure and quit
       -F output file name, default is hist.fmt
       -N don't normalize
       -xlab Label of X axis
       -ylab Label of Y axis
    
    INPUT FORMAT
        single variable
    
    SYNTAX
       histplot.py [command line options] [<file]
    
    """
    file,fmt="",'svg'
    plot=0
    if '-sav' in sys.argv:plot=1
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-fmt' in sys.argv:
        ind=sys.argv.index('-fmt')
        fmt=sys.argv[ind+1]
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
    if '-F' in sys.argv:
        ind=sys.argv.index('-F')
        outfile=sys.argv[ind+1]
        fmt=""
    else:  outfile='hist.'+fmt
    print outfile
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
    if plot==0:
        pylab.draw()
        p=raw_input('s[a]ve to save plot, [q]uit to exit without saving  ')
        if p!='a':  sys.exit()
    pylab.savefig(outfile)
    print 'plot saved in ',outfile

if __name__ == "__main__":
    main()

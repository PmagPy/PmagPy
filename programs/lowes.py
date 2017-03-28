#! /usr/bin/env python
from __future__ import division
from __future__ import print_function
from builtins import input
from builtins import str
from past.utils import old_div
import numpy
import sys


import pylab
import pmagpy.pmag as pmag
pylab.ion()

def main():
    """
    NAME
        lowes.py
    DESCRIPTION
        Plots Lowes spectrum for input IGRF-like file
    SYNTAX
       lowes.py [options]

    OPTIONS:
       -h prints help message and quits
       -f FILE  specify file name with input data
       -d date specify desired date
       -r read desired dates from file
       -n normalize to dipole term
    INPUT FORMAT:
        l m g h
    """
    norm=0
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
        data=numpy.loadtxt(file)
        dates=[2000]
    elif '-d' in sys.argv:
        ind=sys.argv.index('-d')
        dates=[float(sys.argv[ind+1])]
    elif '-r' in sys.argv:
        ind=sys.argv.index('-r')
        dates=numpy.loadtxt(sys.argv[ind+1])
    if '-n' in sys.argv: norm=1
    if len(sys.argv)!=0 and '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    pylab.semilogy()
    pylab.xlabel('Degree (l)')
    pylab.ylabel('Power ($\mu$T$^2$)')
    labels=[]
    for date in dates:
        if date!=2000: 
            gh=pmag.doigrf(0,0,0,date,coeffs=1)
            data=pmag.unpack(gh)
            Ls,Rs=pmag.lowes(data)
            labels.append(str(date))
        print(date,Rs[0])
        if norm==1: 
            Rs=old_div(numpy.array(Rs),Rs[0])
        #pylab.plot(Ls,Rs,'ro')
        pylab.plot(Ls,Rs,linewidth=2)
        pylab.legend(labels,'upper right')
        pylab.draw()
    input()

if __name__ == "__main__":
    main()

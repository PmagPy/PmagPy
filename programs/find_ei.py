#!/usr/bin/env python
from __future__ import print_function
from builtins import input
import sys
import numpy
import matplotlib
if matplotlib.get_backend() != "TKAgg":
  matplotlib.use("TKAgg")

import pmagpy.pmag as pmag
import pmagpy.pmagplotlib as pmagplotlib

def main():
    """
    NAME
        find_EI.py

    DESCRIPTION
        Applies series of assumed flattening factor and "unsquishes" inclinations assuming tangent function.
        Finds flattening factor that gives elongation/inclination pair consistent with TK03.
        Finds bootstrap confidence bounds

    SYNTAX
        find_EI.py [command line options]

    OPTIONS
        -h prints help message and quits
        -i allows interactive input of file name
        -f FILE specify input file name
        -nb N specify number of bootstraps - the more the better, but slower!, default is 1000
        -sc uses a "site-level" correction to a Fisherian distribution instead
            of a "study-level" correction to a TK03-consistent distribution.
            Note that many directions (~ 100) are needed for this correction to be reliable.
        -fmt [svg,png,eps,pdf..] change plot format, default is svg
        -sav  saves the figures and quits

    INPUT
        dec/inc pairs, delimited with space or tabs

    OUTPUT
        four plots:  1) equal area plot of original directions
                      2) Elongation/inclination pairs as a function of f,  data plus 25 bootstrap samples
                      3) Cumulative distribution of bootstrapped optimal inclinations plus uncertainties.
                         Estimate from original data set plotted as solid line
                      4) Orientation of principle direction through unflattening
    NOTE: If distribution does not have a solution, plot labeled: Pathological.  Some bootstrap samples may have
       valid solutions and those are plotted in the CDFs and E/I plot.

    """
    fmt,nb='svg',1000
    plot=0
    if '-i' in sys.argv:
        file=input("Enter file name for processing: ")
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit() # graceful quit
    elif '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
    else:
        print(main.__doc__)
        sys.exit()
    if '-nb' in sys.argv:
        ind=sys.argv.index('-nb')
        nb=int(sys.argv[ind+1])
    if '-sc' in sys.argv:
        site_correction = True
    else:
        site_correction = False
    if '-fmt' in sys.argv:
        ind=sys.argv.index('-fmt')
        fmt=sys.argv[ind+1]
    if '-sav' in sys.argv:plot=1
    data=numpy.loadtxt(file)
    upper,lower=int(round(.975*nb)),int(round(.025*nb))
    E,I=[],[]
    PLTS={'eq':1,'ei':2,'cdf':3,'v2':4}
    pmagplotlib.plot_init(PLTS['eq'],6,6)
    pmagplotlib.plot_init(PLTS['ei'],5,5)
    pmagplotlib.plot_init(PLTS['cdf'],5,5)
    pmagplotlib.plot_init(PLTS['v2'],5,5)
    pmagplotlib.plotEQ(PLTS['eq'],data,'Data')
    if plot==0:pmagplotlib.drawFIGS(PLTS)
    ppars=pmag.doprinc(data)
    Io=ppars['inc']
    n=ppars["N"]
    Es,Is,Fs,V2s=pmag.find_f(data)
    if site_correction:
        Inc,Elong=Is[Es.index(min(Es))],Es[Es.index(min(Es))]
        flat_f = Fs[Es.index(min(Es))]
    else:
        Inc,Elong=Is[-1],Es[-1]
        flat_f = Fs[-1]
    pmagplotlib.plotEI(PLTS['ei'],Es,Is,flat_f)
    pmagplotlib.plotV2s(PLTS['v2'],V2s,Is,flat_f)
    b=0
    print("Bootstrapping.... be patient")
    while b<nb:
        bdata=pmag.pseudo(data)
        Esb,Isb,Fsb,V2sb=pmag.find_f(bdata)
        if b<25:
            pmagplotlib.plotEI(PLTS['ei'],Esb,Isb,Fsb[-1])
        if Esb[-1]!=0:
            ppars=pmag.doprinc(bdata)
            if site_correction:
                I.append(abs(Isb[Esb.index(min(Esb))]))
                E.append(Esb[Esb.index(min(Esb))])
            else:
                I.append(abs(Isb[-1]))
                E.append(Esb[-1])
            b+=1
            if b%25==0:print(b,' out of ',nb)
    I.sort()
    E.sort()
    Eexp=[]
    for i in I:
       Eexp.append(pmag.EI(i))
    if Inc==0:
        title= 'Pathological Distribution: '+'[%7.1f, %7.1f]' %(I[lower],I[upper])
    else:
        title= '%7.1f [%7.1f, %7.1f]' %( Inc, I[lower],I[upper])
    pmagplotlib.plotEI(PLTS['ei'],Eexp,I,1)
    pmagplotlib.plotCDF(PLTS['cdf'],I,'Inclinations','r',title)
    pmagplotlib.plotVs(PLTS['cdf'],[I[lower],I[upper]],'b','--')
    pmagplotlib.plotVs(PLTS['cdf'],[Inc],'g','-')
    pmagplotlib.plotVs(PLTS['cdf'],[Io],'k','-')
    if plot==0:
        pmagplotlib.drawFIGS(PLTS)
        print("Io Inc  I_lower, I_upper, Elon, E_lower, E_upper")
        print('%7.1f %s %7.1f _ %7.1f ^ %7.1f:  %6.4f _ %6.4f ^ %6.4f' %(Io, " => ", Inc, I[lower],I[upper], Elong, E[lower],E[upper]))
        ans= input("S[a]ve plots - <return> to quit:  ")
        if ans!='a':
           print("\n Good bye\n")
           sys.exit()
    files={}
    files['eq']='findEI_eq.'+fmt
    files['ei']='findEI_ei.'+fmt
    files['cdf']='findEI_cdf.'+fmt
    files['v2']='findEI_v2.'+fmt
    pmagplotlib.saveP(PLTS,files)

if __name__ == "__main__":
    main()

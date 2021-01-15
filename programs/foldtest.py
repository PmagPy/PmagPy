#!/usr/bin/env python
import sys
import numpy
import matplotlib
if matplotlib.get_backend() != "TKAgg":
  matplotlib.use("TKAgg")

import pylab
import pmagpy.pmag as pmag
from pmag_env import set_env
import pmagpy.pmagplotlib as pmagplotlib

def main():
    """
    NAME
       foldtest.py

    DESCRIPTION
       does a fold test (Tauxe, 2010) on data

    INPUT FORMAT
       dec inc dip_direction dip

    SYNTAX
       foldtest.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f FILE file with input data
        -F FILE for confidence bounds on fold test
        -u ANGLE (circular standard deviation) for uncertainty on bedding poles
        -b MIN MAX bounds for quick search of percent untilting [default is -10 to 150%]
        -n NB  number of bootstrap samples [default is 1000]
        -fmt FMT, specify format - default is svg
        -sav  save figures and quit
    INPUT FILE
    Dec Inc Dip_Direction Dip  in space delimited file
      where Dec and Inc are the declination and inclination in geographic
      coordinates. 

    OUTPUT PLOTS
        Geographic: is an equal area projection of the input data in
                    original coordinates
        Stratigraphic: is an equal area projection of the input data in
                    tilt adjusted coordinates
        % Untilting: The dashed (red) curves are representative plots of
                    maximum eigenvalue (tau_1) as a function of untilting
                    The solid line is the cumulative distribution of the
                    % Untilting required to maximize tau for all the
                    bootstrapped data sets.  The dashed vertical lines
                    are 95% confidence bounds on the % untilting that yields
                   the most clustered result (maximum tau_1).
        Command line: prints out the bootstrapped iterations and
                   finally the confidence bounds on optimum untilting.
        If the 95% conf bounds include 0, then a post-tilt magnetization is indicated
        If the 95% conf bounds include 100, then a pre-tilt magnetization is indicated
        If the 95% conf bounds exclude both 0 and 100, syn-tilt magnetization is
                possible as is vertical axis rotation or other pathologies
        Geographic: is an equal area projection of the input data in

    OPTIONAL OUTPUT FILE:
       The output file has the % untilting within the 95% confidence bounds
nd the number of bootstrap samples
    """
    kappa=0
    fmt,plot='svg',0
    nb=1000 # number of bootstraps
    min,max=-10,150
    if '-h' in sys.argv: # check if help is needed
        print(main.__doc__)
        sys.exit() # graceful quit
    if '-F' in sys.argv:
        ind=sys.argv.index('-F')
        outfile=open(sys.argv[ind+1],'w')
    else:
        outfile=""
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
        DIDDs=numpy.loadtxt(file)
    else:
        print(main.__doc__)
        sys.exit()
    if '-fmt' in sys.argv:
        ind=sys.argv.index('-fmt')
        fmt=sys.argv[ind+1]
    if '-sav' in sys.argv:plot=1
    if '-b' in sys.argv:
        ind=sys.argv.index('-b')
        min=int(sys.argv[ind+1])
        max=int(sys.argv[ind+2])
    if '-n' in sys.argv:
        ind=sys.argv.index('-n')
        nb=int(sys.argv[ind+1])
    if '-u' in sys.argv:
        ind=sys.argv.index('-u')
        csd=float(sys.argv[ind+1])
        kappa=(81. / csd)**2
    #
    # get to work
    #
    PLTS={'geo':1,'strat':2,'taus':3} # make plot dictionary
    pmagplotlib.plot_init(PLTS['geo'],5,5)
    pmagplotlib.plot_init(PLTS['strat'],5,5)
    pmagplotlib.plot_init(PLTS['taus'],5,5)
    pmagplotlib.plot_eq(PLTS['geo'],DIDDs,'Geographic')
    D,I=pmag.dotilt_V(DIDDs)
    TCs=numpy.array([D,I]).transpose()
    pmagplotlib.plot_eq(PLTS['strat'],TCs,'Stratigraphic')
    if not set_env.IS_WIN:
        if plot==0:pmagplotlib.draw_figs(PLTS)
    Percs=list(range(min,max))
    Cdf,Untilt=[],[]
    pylab.figure(num=PLTS['taus'])
    print('doing ',nb,' iterations...please be patient.....')
    for n in range(nb): # do bootstrap data sets - plot first 25 as dashed red line
            if n%50==0:print(n)
            Taus=[] # set up lists for taus
            PDs=pmag.pseudo(DIDDs)
            if kappa!=0:
                for k in range(len(PDs)):
                    d,i=pmag.fshdev(kappa)
                    dipdir,dip=pmag.dodirot(d,i,PDs[k][2],PDs[k][3])
                    PDs[k][2]=dipdir
                    PDs[k][3]=dip
            for perc in Percs:
                tilt=numpy.array([1.,1.,1.,0.01*perc])
                D,I=pmag.dotilt_V(PDs*tilt)
                TCs=numpy.array([D,I]).transpose()
                ppars=pmag.doprinc(TCs) # get principal directions
                Taus.append(ppars['tau1'])
            if n<25:pylab.plot(Percs,Taus,'r--')
            Untilt.append(Percs[Taus.index(numpy.max(Taus))]) # tilt that gives maximum tau
            Cdf.append(float(n) / float(nb))
    pylab.plot(Percs,Taus,'k')
    pylab.xlabel('% Untilting')
    pylab.ylabel('tau_1 (red), CDF (green)')
    Untilt.sort() # now for CDF of tilt of maximum tau
    pylab.plot(Untilt,Cdf,'g')
    lower=int(.025*nb)
    upper=int(.975*nb)
    pylab.axvline(x=Untilt[lower],ymin=0,ymax=1,linewidth=1,linestyle='--')
    pylab.axvline(x=Untilt[upper],ymin=0,ymax=1,linewidth=1,linestyle='--')
    tit= '%i - %i %s'%(Untilt[lower],Untilt[upper],'Percent Unfolding')
    print(tit)
    print('range of all bootstrap samples: ', Untilt[0], ' - ', Untilt[-1])
    pylab.title(tit)
    outstring= '%i - %i; %i\n'%(Untilt[lower],Untilt[upper],nb)
    if outfile!="":outfile.write(outstring)
    files={}
    for key in list(PLTS.keys()):
        files[key]=('foldtest_'+'%s'%(key.strip()[:2])+'.'+fmt)
    if plot==0:
        pmagplotlib.draw_figs(PLTS)
        ans= input('S[a]ve all figures, <Return> to quit   ')
        if ans!='a':
            print("Good bye")
            sys.exit()
    pmagplotlib.save_plots(PLTS,files)
main()

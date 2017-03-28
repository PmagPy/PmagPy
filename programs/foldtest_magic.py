#!/usr/bin/env python
from __future__ import division
from __future__ import print_function
from builtins import input
from builtins import range
from past.utils import old_div
import sys
import numpy
import matplotlib
if matplotlib.get_backend() != "TKAgg":
  matplotlib.use("TKAgg")

import pylab
import pmagpy.pmag as pmag
import pmagpy.pmagplotlib as pmagplotlib

def main():
    """
    NAME
       foldtest_magic.py

    DESCRIPTION
       does a fold test (Tauxe, 2010) on data

    INPUT FORMAT
       pmag_specimens format file, er_samples.txt format file (for bedding)

    SYNTAX
       foldtest_magic.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f pmag_sites  formatted file [default is pmag_sites.txt]
        -fsa er_samples  formatted file [default is er_samples.txt]
        -fsi er_sites  formatted file 
        -exc use pmag_criteria.txt to set acceptance criteria
        -n NB, set number of bootstraps, default is 1000
        -b MIN, MAX, set bounds for untilting, default is -10, 150
        -fmt FMT, specify format - default is svg
        -sav saves plots and quits
    
    OUTPUT
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
        If the 95% conf bounds include 0, then a pre-tilt magnetization is indicated
        If the 95% conf bounds include 100, then a post-tilt magnetization is indicated
        If the 95% conf bounds exclude both 0 and 100, syn-tilt magnetization is
                possible as is vertical axis rotation or other pathologies

    """
    kappa=0
    nb=1000 # number of bootstraps
    min,max=-10,150
    dir_path='.'
    infile,orfile='pmag_sites.txt','er_samples.txt'
    critfile='pmag_criteria.txt'
    dipkey,azkey='sample_bed_dip','sample_bed_dip_direction'
    fmt='svg'
    plot=0
    if '-WD' in sys.argv:
        ind=sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
    if '-h' in sys.argv: # check if help is needed
        print(main.__doc__)
        sys.exit() # graceful quit
    if '-n' in sys.argv:
        ind=sys.argv.index('-n')
        nb=int(sys.argv[ind+1])
    if '-fmt' in sys.argv:
        ind=sys.argv.index('-fmt')
        fmt=sys.argv[ind+1]
    if '-sav' in sys.argv:plot=1
    if '-b' in sys.argv:
        ind=sys.argv.index('-b')
        min=int(sys.argv[ind+1])
        max=int(sys.argv[ind+2])
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        infile=sys.argv[ind+1] 
    if '-fsa' in sys.argv:
        ind=sys.argv.index('-fsa')
        orfile=sys.argv[ind+1] 
    elif '-fsi' in sys.argv:
        ind=sys.argv.index('-fsi')
        orfile=sys.argv[ind+1] 
        dipkey,azkey='site_bed_dip','site_bed_dip_direction'
    orfile=dir_path+'/'+orfile
    infile=dir_path+'/'+infile
    critfile=dir_path+'/'+critfile
    data,file_type=pmag.magic_read(infile)
    ordata,file_type=pmag.magic_read(orfile)
    if '-exc' in sys.argv:
        crits,file_type=pmag.magic_read(critfile)
        for crit in crits:
             if crit['pmag_criteria_code']=="DE-SITE":
                 SiteCrit=crit
                 break
# get to work
#
    PLTS={'geo':1,'strat':2,'taus':3} # make plot dictionary
    pmagplotlib.plot_init(PLTS['geo'],5,5)
    pmagplotlib.plot_init(PLTS['strat'],5,5)
    pmagplotlib.plot_init(PLTS['taus'],5,5)
    GEOrecs=pmag.get_dictitem(data,'site_tilt_correction','0','T')
    if len(GEOrecs)>0: # have some geographic data
        DIDDs= [] # set up list for dec inc  dip_direction, dip
        for rec in GEOrecs:   # parse data
            dip,dip_dir=0,-1
            Dec=float(rec['site_dec'])
            Inc=float(rec['site_inc'])
            orecs=pmag.get_dictitem(ordata,'er_site_name',rec['er_site_name'],'T')
            if len(orecs)>0:
                    if orecs[0][azkey]!="":dip_dir=float(orecs[0][azkey])
                    if orecs[0][dipkey]!="":dip=float(orecs[0][dipkey])
            if dip!=0 and dip_dir!=-1:
                if  '-exc' in  sys.argv:
                    keep=1
                    for key in list(SiteCrit.keys()):
                        if 'site' in key  and SiteCrit[key]!="" and rec[key]!="" and key!='site_alpha95':
                            if float(rec[key])<float(SiteCrit[key]): 
                                keep=0
                                print(rec['er_site_name'],key,rec[key])
                        if key=='site_alpha95'  and SiteCrit[key]!="" and rec[key]!="":
                            if float(rec[key])>float(SiteCrit[key]): 
                                keep=0
                    if keep==1:  DIDDs.append([Dec,Inc,dip_dir,dip])
                else:
                                DIDDs.append([Dec,Inc,dip_dir,dip])
    else:
        print('no geographic directional data found')
        sys.exit()
    pmagplotlib.plotEQ(PLTS['geo'],DIDDs,'Geographic')
    data=numpy.array(DIDDs)
    D,I=pmag.dotilt_V(data)
    TCs=numpy.array([D,I]).transpose()
    pmagplotlib.plotEQ(PLTS['strat'],TCs,'Stratigraphic')
    if plot==0:pmagplotlib.drawFIGS(PLTS)
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
            Cdf.append(old_div(float(n),float(nb)))
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
    pylab.title(tit)
    if plot==0:
        pmagplotlib.drawFIGS(PLTS)
        ans= input('S[a]ve all figures, <Return> to quit  \n ')
        if ans!='a':
            print("Good bye")
            sys.exit()
    files={}
    for key in list(PLTS.keys()):
        files[key]=('foldtest_'+'%s'%(key.strip()[:2])+'.'+fmt)
    pmagplotlib.saveP(PLTS,files)

if __name__ == "__main__":
    main()

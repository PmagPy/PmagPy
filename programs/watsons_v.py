#!/usr/bin/env python
import sys
import numpy
import matplotlib
if matplotlib.get_backend() != "TKAgg":
  matplotlib.use("TKAgg")

import pmagpy.pmagplotlib as pmagplotlib
import pmagpy.pmag as pmag

def main():
    """
    NAME
       watsons_v.py

    DESCRIPTION
       calculates Watson's V statistic from input files

    INPUT FORMAT
       takes dec/inc as first two columns in two space delimited files
   
    SYNTAX
       watsons_v.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f FILE (with optional second)
        -f2 FILE (second file) 
        -ant,  flip antipodal directions to opposite direction
           in first file if only one file or flip all in second, if two files 
        -P  (don't save or show plot)
        -sav save figure and quit silently
        -fmt [png,svg,eps,pdf,jpg] format for saved figure

    OUTPUT
        Watson's V and the Monte Carlo Critical Value Vc.
        in plot, V is solid and Vc is dashed.

    """
    Flip=0
    show,plot=1,0
    fmt='svg'
    file2=""
    if '-h' in sys.argv: # check if help is needed
        print main.__doc__
        sys.exit() # graceful quit
    if '-ant' in  sys.argv: Flip=1
    if '-sav' in sys.argv: show,plot=0,1 # don't display, but do save plot
    if '-fmt' in sys.argv: 
        ind=sys.argv.index('-fmt')
        fmt=sys.argv[ind+1]
    if '-P' in  sys.argv: show=0 # don't display or save plot
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file1=sys.argv[ind+1]
        data=numpy.loadtxt(file1).transpose()
        D1=numpy.array([data[0],data[1]]).transpose()
    else:
        print "-f is required"
        print main.__doc__
        sys.exit()
    if '-f2' in sys.argv:
        ind=sys.argv.index('-f2')
        file2=sys.argv[ind+1]
        data2=numpy.loadtxt(file2).transpose()
        D2=numpy.array([data2[0],data2[1]]).transpose()
        if Flip==1:
            D2,D=pmag.flip(D2) # D2 are now flipped
            if len(D2)!=0:
                if len(D)!=0: 
                    D2=numpy.concatenate(D,D2) # put all in D2
            elif len(D)!=0:
                D2=D
            else: 
                print 'length of second file is zero'
                sys.exit()
    elif Flip==1:D2,D1=pmag.flip(D1) # peel out antipodal directions, put in D2
#
    counter,NumSims=0,5000
#
# first calculate the fisher means and cartesian coordinates of each set of Directions
#
    pars_1=pmag.fisher_mean(D1)
    pars_2=pmag.fisher_mean(D2)
#
# get V statistic for these
#
    V=pmag.vfunc(pars_1,pars_2)
#
# do monte carlo simulation of datasets with same kappas, but common mean
# 
    Vp=[] # set of Vs from simulations
    if show==1:print "Doing ",NumSims," simulations"
    for k in range(NumSims):
        counter+=1
        if counter==50:
            if show==1:print k+1
            counter=0
        Dirp=[]
# get a set of N1 fisher distributed vectors with k1, calculate fisher stats
        for i in range(pars_1["n"]):
            Dirp.append(pmag.fshdev(pars_1["k"]))
        pars_p1=pmag.fisher_mean(Dirp)
# get a set of N2 fisher distributed vectors with k2, calculate fisher stats
        Dirp=[]
        for i in range(pars_2["n"]):
            Dirp.append(pmag.fshdev(pars_2["k"]))
        pars_p2=pmag.fisher_mean(Dirp)
# get the V for these
        Vk=pmag.vfunc(pars_p1,pars_p2)
        Vp.append(Vk)
#
# sort the Vs, get Vcrit (95th one)
#
    Vp.sort()
    k=int(.95*NumSims)
    if show==1:
        print "Watson's V,  Vcrit: " 
        print '   %10.1f %10.1f'%(V,Vp[k])
    if show==1 or plot==1:
        print "Watson's V,  Vcrit: " 
        print '   %10.1f %10.1f'%(V,Vp[k])
        CDF={'cdf':1}
        pmagplotlib.plot_init(CDF['cdf'],5,5)
        pmagplotlib.plotCDF(CDF['cdf'],Vp,"Watson's V",'r',"")
        pmagplotlib.plotVs(CDF['cdf'],[V],'g','-')
        pmagplotlib.plotVs(CDF['cdf'],[Vp[k]],'b','--')
        if plot==0:pmagplotlib.drawFIGS(CDF)
        files={}
        if file2!="":
            files['cdf']='WatsonsV_'+file1+'_'+file2+'.'+fmt
        else:
            files['cdf']='WatsonsV_'+file1+'.'+fmt
        if pmagplotlib.isServer:
            black     = '#000000'
            purple    = '#800080'
            titles={}
            titles['cdf']='Cumulative Distribution'
            CDF = pmagplotlib.addBorders(CDF,titles,black,purple)
            pmagplotlib.saveP(CDF,files)
        elif plot==0:
            ans=raw_input(" S[a]ve to save plot, [q]uit without saving:  ")
            if ans=="a": pmagplotlib.saveP(CDF,files) 
        if plot==1: # save and quit silently
            pmagplotlib.saveP(CDF,files)

if __name__ == "__main__":
    main()


#!/usr/bin/env python
from __future__ import division
from __future__ import print_function
from builtins import input
from builtins import range
from past.utils import old_div
import sys
import numpy


import pmagpy.pmagplotlib as pmagplotlib
import pmagpy.pmag as pmag
#
#contributed by N. Swanson-Hysell on 5/3/2013 relying heavily on the implementation of the Watson V test developed by L. Tauxe in watsonsV.py
#
def main():
    """
    NAME
       revtest_MM1990.py

    DESCRIPTION
       calculates Watson's V statistic from input files through Monte Carlo simulation in order to test whether normal and reversed populations could have been drawn from a common mean (equivalent to watsonV.py). Also provides the critical angle between the two sample mean directions and the corresponding McFadden and McElhinny (1990) classification.

    INPUT FORMAT
       takes dec/inc as first two columns in two space delimited files (one file for normal directions, one file for reversed directions).

    SYNTAX
       revtest_MM1990.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f FILE
        -f2 FILE
        -P  (don't plot the Watson V cdf)

    OUTPUT
        Watson's V between the two populations and the Monte Carlo Critical Value Vc.
        M&M1990 angle, critical angle and classification
        Plot of Watson's V CDF from Monte Carlo simulation (red line), V is solid and Vc is dashed.

    """
    D1,D2=[],[]
    plot=1
    Flip=1
    if '-h' in sys.argv: # check if help is needed
        print(main.__doc__)
        sys.exit() # graceful quit
    if '-P' in  sys.argv: plot=0
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file1=sys.argv[ind+1]
    f1=open(file1,'r')
    for line in f1.readlines():
        rec=line.split()
        Dec,Inc=float(rec[0]),float(rec[1])
        D1.append([Dec,Inc,1.])
    f1.close()
    if '-f2' in sys.argv:
        ind=sys.argv.index('-f2')
        file2=sys.argv[ind+1]
        f2=open(file2,'r')
        print("be patient, your computer is doing 5000 simulations...")
        for line in f2.readlines():
            rec=line.split()
            Dec,Inc=float(rec[0]),float(rec[1])
            D2.append([Dec,Inc,1.])
        f2.close()
    #take the antipode for the directions in file 2
    D2_flip=[]
    for rec in D2:
        d,i=(rec[0]-180.)%360.,-rec[1]
        D2_flip.append([d,i,1.])

    pars_1=pmag.fisher_mean(D1)
    pars_2=pmag.fisher_mean(D2_flip)

    cart_1=pmag.dir2cart([pars_1["dec"],pars_1["inc"],pars_1["r"]])
    cart_2=pmag.dir2cart([pars_2['dec'],pars_2['inc'],pars_2["r"]])
    Sw=pars_1['k']*pars_1['r']+pars_2['k']*pars_2['r'] # k1*r1+k2*r2
    xhat_1=pars_1['k']*cart_1[0]+pars_2['k']*cart_2[0] # k1*x1+k2*x2
    xhat_2=pars_1['k']*cart_1[1]+pars_2['k']*cart_2[1] # k1*y1+k2*y2
    xhat_3=pars_1['k']*cart_1[2]+pars_2['k']*cart_2[2] # k1*z1+k2*z2
    Rw=numpy.sqrt(xhat_1**2+xhat_2**2+xhat_3**2)
    V=2*(Sw-Rw)
#
#keep weighted sum for later when determining the "critical angle" let's save it as Sr (notation of McFadden and McElhinny, 1990)
#
    Sr=Sw
#
# do monte carlo simulation of datasets with same kappas, but common mean
#
    counter,NumSims=0,5000
    Vp=[] # set of Vs from simulations
    for k in range(NumSims):
#
# get a set of N1 fisher distributed vectors with k1, calculate fisher stats
#
        Dirp=[]
        for i in range(pars_1["n"]):
            Dirp.append(pmag.fshdev(pars_1["k"]))
        pars_p1=pmag.fisher_mean(Dirp)
#
# get a set of N2 fisher distributed vectors with k2, calculate fisher stats
#
        Dirp=[]
        for i in range(pars_2["n"]):
            Dirp.append(pmag.fshdev(pars_2["k"]))
        pars_p2=pmag.fisher_mean(Dirp)
#
# get the V for these
#
        Vk=pmag.vfunc(pars_p1,pars_p2)
        Vp.append(Vk)
#
# sort the Vs, get Vcrit (95th percentile one)
#
    Vp.sort()
    k=int(.95*NumSims)
    Vcrit=Vp[k]
#
# equation 18 of McFadden and McElhinny, 1990 calculates the critical value of R (Rwc)
#
    Rwc=Sr-(old_div(Vcrit,2))
#
#following equation 19 of McFadden and McElhinny (1990) the critical angle is calculated.
#
    k1=pars_1['k']
    k2=pars_2['k']
    R1=pars_1['r']
    R2=pars_2['r']
    critical_angle=numpy.degrees(numpy.arccos(old_div(((Rwc**2)-((k1*R1)**2)-((k2*R2)**2)),(2*k1*R1*k2*R2))))
    D1_mean=(pars_1['dec'],pars_1['inc'])
    D2_mean=(pars_2['dec'],pars_2['inc'])
    angle=pmag.angle(D1_mean,D2_mean)
#
# print the results of the test
#
    print("")
    print("Results of Watson V test: ")
    print("")
    print("Watson's V:           " '%.1f' %(V))
    print("Critical value of V:  " '%.1f' %(Vcrit))

    if V<Vcrit:
        print('"Pass": Since V is less than Vcrit, the null hypothesis that the two populations are drawn from distributions that share a common mean direction (antipodal to one another) cannot be rejected.')
    elif V>Vcrit:
        print('"Fail": Since V is greater than Vcrit, the two means can be distinguished at the 95% confidence level.')
    print("")
    print("M&M1990 classification:")
    print("")
    print("Angle between data set means: " '%.1f'%(angle))
    print("Critical angle of M&M1990:   " '%.1f'%(critical_angle))

    if V>Vcrit:
        print("")
    elif V<Vcrit:
        if critical_angle<5:
            print("The McFadden and McElhinny (1990) classification for this test is: 'A'")
        elif critical_angle<10:
            print("The McFadden and McElhinny (1990) classification for this test is: 'B'")
        elif critical_angle<20:
            print("The McFadden and McElhinny (1990) classification for this test is: 'C'")
        else:
            print("The McFadden and McElhinny (1990) classification for this test is: 'INDETERMINATE;")
    if plot==1:
        CDF={'cdf':1}
        pmagplotlib.plot_init(CDF['cdf'],5,5)
        p1 = pmagplotlib.plot_cdf(CDF['cdf'],Vp,"Watson's V",'r',"")
        p2 = pmagplotlib.plot_vs(CDF['cdf'],[V],'g','-')
        p3 = pmagplotlib.plot_vs(CDF['cdf'],[Vp[k]],'b','--')
        pmagplotlib.draw_figs(CDF)
        files,fmt={},'svg'
        if file2!="":
            files['cdf']='WatsonsV_'+file1+'_'+file2+'.'+fmt
        else:
            files['cdf']='WatsonsV_'+file1+'.'+fmt
        if pmagplotlib.isServer:
            black     = '#000000'
            purple    = '#800080'
            titles={}
            titles['cdf']='Cumulative Distribution'
            CDF = pmagplotlib.add_borders(CDF,titles,black,purple)
            pmagplotlib.save_plots(CDF,files)
        else:
            ans=input(" S[a]ve to save plot, [q]uit without saving:  ")
            if ans=="a": pmagplotlib.save_plots(CDF,files)

if __name__ == "__main__":
    main()

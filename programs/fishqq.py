#!/usr/bin/env python
from __future__ import print_function
from builtins import input
import sys
import matplotlib
if matplotlib.get_backend() != "TKAgg":
  matplotlib.use("TKAgg")

import pmagpy.pmagplotlib as pmagplotlib
import pmagpy.pmag as pmag

def main():
    """
    NAME
       fishqq.py

    DESCRIPTION
       makes qq plot from dec,inc input data

    INPUT FORMAT
       takes dec/inc pairs in space delimited file

    SYNTAX
       fishqq.py [command line options]

    OPTIONS
        -h help message
        -f FILE, specify file on command line
        -F FILE, specify output file for statistics
        -sav save and quit [saves as input file name plus fmt extension]
        -fmt specify format for output [png, eps, svg, pdf] 

    OUTPUT:
        Dec Inc N Mu Mu_crit Me Me_crit Y/N
     where direction is the principal component and Y/N is Fisherian or not
     separate lines for each mode with N >=10 (N and R)
    """
    fmt,plot='svg',0
    outfile=""
    if '-h' in sys.argv: # check if help is needed
        print(main.__doc__)
        sys.exit() # graceful quit
    elif '-f' in sys.argv: # ask for filename
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
        f=open(file,'r')
        data=f.readlines()
    if '-F' in sys.argv:
        ind=sys.argv.index('-F')
        outfile=open(sys.argv[ind+1],'w') # open output file
    if '-sav' in sys.argv: plot=1
    if '-fmt' in sys.argv:
        ind=sys.argv.index('-fmt')
        fmt=sys.argv[ind+1]
    DIs,nDIs,rDIs= [],[],[] # set up list for data
    for line in data:   # read in the data from standard input
        if '\t' in line:
            rec=line.split('\t') # split each line on space to get records
        else:
            rec=line.split() # split each line on space to get records
        DIs.append([float(rec[0]),float(rec[1])]) # append data to Inc
# split into two modes
    ppars=pmag.doprinc(DIs) # get principal directions
    for rec in DIs:
        angle=pmag.angle([rec[0],rec[1]],[ppars['dec'],ppars['inc']])
        if angle>90.:
            rDIs.append(rec)
        else:
            nDIs.append(rec)
    
#
    if len(rDIs) >=10 or len(nDIs) >=10:
        D1,I1=[],[]
        QQ={'unf1':1,'exp1':2}
        pmagplotlib.plot_init(QQ['unf1'],5,5)
        pmagplotlib.plot_init(QQ['exp1'],5,5)
        if len(nDIs) < 10: 
            ppars=pmag.doprinc(rDIs) # get principal directions
            Drbar,Irbar=ppars['dec']-180.,-ppars['inc']
            Nr=len(rDIs)
            for di in rDIs:
                d,irot=pmag.dotilt(di[0],di[1],Drbar-180.,90.-Irbar) # rotate to mean
                drot=d-180.
                if drot<0:drot=drot+360.
                D1.append(drot)           
                I1.append(irot) 
                Dtit='Mode 2 Declinations'
                Itit='Mode 2 Inclinations'
        else:          
            ppars=pmag.doprinc(nDIs) # get principal directions
            Dnbar,Inbar=ppars['dec'],ppars['inc']
            Nn=len(nDIs)
            for di in nDIs:
                d,irot=pmag.dotilt(di[0],di[1],Dnbar-180.,90.-Inbar) # rotate to mean
                drot=d-180.
                if drot<0:drot=drot+360.
                D1.append(drot)
                I1.append(irot)
                Dtit='Mode 1 Declinations'
                Itit='Mode 1 Inclinations'
        Mu_n,Mu_ncr=pmagplotlib.plot_qq_unf(QQ['unf1'],D1,Dtit) # make plot
        Me_n,Me_ncr=pmagplotlib.plot_qq_exp(QQ['exp1'],I1,Itit) # make plot
        #print Mu_n,Mu_ncr,Me_n, Me_ncr
        if outfile!="":
#        Dec Inc N Mu Mu_crit Me Me_crit Y/N
            if Mu_n<=Mu_ncr and Me_n<=Me_ncr:
               F='Y'
            else:
               F='N'
            outstring='%7.1f %7.1f %i %5.3f %5.3f %5.3f %5.3f %s \n'%(Dnbar,Inbar,Nn,Mu_n,Mu_ncr,Me_n,Me_ncr,F)
            outfile.write(outstring)
    else:
        print('you need N> 10 for at least one mode')
        sys.exit()
    if len(rDIs)>10 and len(nDIs)>10:
        D2,I2=[],[]
        QQ['unf2']=3
        QQ['exp2']=4
        pmagplotlib.plot_init(QQ['unf2'],5,5)
        pmagplotlib.plot_init(QQ['exp2'],5,5)
        ppars=pmag.doprinc(rDIs) # get principal directions
        Drbar,Irbar=ppars['dec']-180.,-ppars['inc']
        Nr=len(rDIs)
        for di in rDIs:
            d,irot=pmag.dotilt(di[0],di[1],Drbar-180.,90.-Irbar) # rotate to mean
            drot=d-180.
            if drot<0:drot=drot+360.
            D2.append(drot)           
            I2.append(irot) 
            Dtit='Mode 2 Declinations'
            Itit='Mode 2 Inclinations'
        Mu_r,Mu_rcr=pmagplotlib.plot_qq_unf(QQ['unf2'],D2,Dtit) # make plot
        Me_r,Me_rcr=pmagplotlib.plot_qq_exp(QQ['exp2'],I2,Itit) # make plot
        if outfile!="":
#        Dec Inc N Mu Mu_crit Me Me_crit Y/N
            if Mu_r<=Mu_rcr and Me_r<=Me_rcr:
               F='Y'
            else:
               F='N'
            outstring='%7.1f %7.1f %i %5.3f %5.3f %5.3f %5.3f %s \n'%(Drbar,Irbar,Nr,Mu_r,Mu_rcr,Me_r,Me_rcr,F)
            outfile.write(outstring)
    files={}
    for key in list(QQ.keys()):
        files[key]=file+'_'+key+'.'+fmt 
    if pmagplotlib.isServer:
        black     = '#000000'
        purple    = '#800080'
        titles={}
        titles['eq']='Equal Area Plot'
        EQ = pmagplotlib.add_borders(EQ,titles,black,purple)
        pmagplotlib.save_plots(QQ,files)
    elif plot==1:
        pmagplotlib.save_plots(QQ,files)
    else:
        pmagplotlib.draw_figs(QQ) 
        ans=input(" S[a]ve to save plot, [q]uit without saving:  ")
        if ans=="a": pmagplotlib.save_plots(QQ,files)

if __name__ == "__main__":
    main()

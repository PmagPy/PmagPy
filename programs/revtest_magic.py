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
       revtest_magic.py

    DESCRIPTION
       calculates bootstrap statistics to test for antipodality

    INPUT FORMAT
       takes dec/inc data from pmag_sites table 
   
    SYNTAX
       revtest_magic.py [command line options]
    
    OPTION
       -h prints help message and quits
       -f FILE, sets pmag_sites filename on command line
       -crd [s,g,t], set coordinate system, default is geographic
       -exc use pmag_criteria.txt to set acceptance criteria
       -fmt [svg,png,jpg], sets format for image output
       -sav saves plot and quits               

    """
    D,fmt,plot=[],'svg',0
    coord='0'
    infile='pmag_sites.txt'
    critfile='pmag_criteria.txt'
    dir_path='.'
    if '-h' in sys.argv: # check if help is needed
        print(main.__doc__)
        sys.exit() # graceful quit
    if '-WD' in sys.argv:
        ind=sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
    if '-sav' in sys.argv:plot=1
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        infile=sys.argv[ind+1]
    if '-crd' in sys.argv:
        ind=sys.argv.index('-crd')
        coord=sys.argv[ind+1]
        if coord=='s':coord='-1'
        if coord=='g':coord='0'
        if coord=='t':coord='100'
    if '-fmt' in sys.argv:
        ind=sys.argv.index('-fmt')
        fmt=sys.argv[ind+1]
#
    infile=dir_path+'/'+infile
    critfile=dir_path+'/'+critfile
    Accept=['site_k','site_alpha95','site_n','site_n_lines']
    data,file_type=pmag.magic_read(infile)
    if file_type!='pmag_sites':
        print("Error opening file")
        sys.exit()
#    ordata,file_type=pmag.magic_read(orfile)
    if '-exc' in sys.argv:
        crits,file_type=pmag.magic_read(critfile)
        for crit in crits:
             if crit['pmag_criteria_code']=="DE-SITE":
                 SiteCrit=crit
    for rec in data:
        if rec['site_tilt_correction']==coord:
            Dec=float(rec['site_dec'])
            Inc=float(rec['site_inc'])
            if  '-exc' in  sys.argv:
                for key in Accept:
                    if SiteCrit[key]!="":
                        if float(rec[key])<=float(SiteCrit[key]):     
                            D.append([Dec,Inc,1.])
            else:
                            D.append([Dec,Inc,1.])
# set up plots
    
    d=""
    CDF={'X':1,'Y':2,'Z':3}
    pmagplotlib.plot_init(CDF['X'],5,5)
    pmagplotlib.plot_init(CDF['Y'],5,5)
    pmagplotlib.plot_init(CDF['Z'],5,5)
#
# flip reverse mode
#
    D1,D2=pmag.flip(D)
    counter,NumSims=0,500
#
# get bootstrapped means for each data set
#
    if len(D1) < 5 or len(D2) < 5:
        print('not enough data in two different modes for reversals test')
        sys.exit()
    print('doing first mode, be patient')
    BDI1=pmag.di_boot(D1)
    print('doing second mode, be patient')
    BDI2=pmag.di_boot(D2)
    pmagplotlib.plotCOM(CDF,BDI1,BDI2,[""])
    files={}
    for key in list(CDF.keys()): files[key]='REV'+'_'+key+'.'+fmt 
    if plot==0:
        pmagplotlib.drawFIGS(CDF)
        ans=  input("s[a]ve plots, [q]uit: ")
        if ans=='a':
            pmagplotlib.saveP(CDF,files)
    else:
        pmagplotlib.saveP(CDF,files)
        sys.exit()

if __name__ == "__main__":
    main()

#!/usr/bin/env python
from __future__ import print_function
import sys
import os
import matplotlib
if matplotlib.get_backend() != "TKAgg":
  matplotlib.use("TKAgg")

import pmagpy.pmagplotlib as pmagplotlib
import pmagpy.pmag as pmag

def main():
    """
    NAME
        dayplot_magic.py

    DESCRIPTION
        makes 'day plots' (Day et al. 1977) and squareness/coercivity,
        plots 'linear mixing' curve from Dunlop and Carter-Stiglitz (2006).
          squareness coercivity of remanence (Neel, 1955) plots after
          Tauxe et al. (2002)

    SYNTAX
        dayplot_magic.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f: specify input hysteresis file, default is rmag_hysteresis.txt
        -fr: specify input remanence file, default is rmag_remanence.txt
        -fmt [svg,png,jpg] format for output plots
        -sav saves plots and quits quietly
        -n label specimen names
    """
    args=sys.argv
    hyst_file,rem_file="rmag_hysteresis.txt","rmag_remanence.txt"
    dir_path='.'
    verbose=pmagplotlib.verbose
    fmt='svg' # default file format
    if '-WD' in args:
       ind=args.index('-WD')
       dir_path=args[ind+1]
    if "-h" in args:
        print(main.__doc__)
        sys.exit()
    if '-f' in args:
        ind=args.index("-f")
        hyst_file=args[ind+1]
    if '-fr' in args:
        ind=args.index("-fr")
        rem_file=args[ind+1]
    if '-fmt' in sys.argv:
        ind=sys.argv.index("-fmt")
        fmt=sys.argv[ind+1]
    if '-sav' in sys.argv:
        plots=1
        verbose=0
    else: plots=0
    if '-n' in sys.argv: 
        label=1
    else:
        label=0
    hyst_file = os.path.realpath(os.path.join(dir_path, hyst_file))
    rem_file = os.path.realpath(os.path.join(dir_path, rem_file))
    #
    # initialize some variables
    # define figure numbers for Day,S-Bc,S-Bcr
    DSC={}
    DSC['day'],DSC['S-Bc'],DSC['S-Bcr'],DSC['bcr1-bcr2']=1,2,3,4
    pmagplotlib.plot_init(DSC['day'],5,5)
    pmagplotlib.plot_init(DSC['S-Bc'],5,5)
    pmagplotlib.plot_init(DSC['S-Bcr'],5,5)
    pmagplotlib.plot_init(DSC['bcr1-bcr2'],5,5)
    #
    #
    hyst_data,file_type=pmag.magic_read(hyst_file)
    rem_data,file_type=pmag.magic_read(rem_file)
    #
    S,BcrBc,Bcr2,Bc,hsids,Bcr=[],[],[],[],[],[]
    Ms,Bcr1,Bcr1Bc,S1=[],[],[],[]
    names=[]
    locations=''
    for rec in  hyst_data:
        if 'er_location_name' in rec.keys() and rec['er_location_name'] not in locations: locations=locations+rec['er_location_name']+'_'
        if rec['hysteresis_bcr'] !="" and rec['hysteresis_mr_moment']!="":
            S.append(float(rec['hysteresis_mr_moment'])/float(rec['hysteresis_ms_moment']))
            Bcr.append(float(rec['hysteresis_bcr']))
            Bc.append(float(rec['hysteresis_bc']))
            BcrBc.append(Bcr[-1]/Bc[-1])
            if 'er_synthetic_name' in rec.keys() and rec['er_synthetic_name']!="":
                rec['er_specimen_name']=rec['er_synthetic_name']
            hsids.append(rec['er_specimen_name'])
            names.append(rec['er_specimen_name'])
    if len(rem_data)>0:
        for rec in  rem_data:
            if rec['remanence_bcr'] !="" and float(rec['remanence_bcr'])>0:
                try:
                    ind=hsids.index(rec['er_specimen_name'])
                    Bcr1.append(float(rec['remanence_bcr']))
                    Bcr1Bc.append(Bcr1[-1]/Bc[ind])
                    S1.append(S[ind])
                    Bcr2.append(Bcr[ind])
                except ValueError:
                    if verbose:print('hysteresis data for ',rec['er_specimen_name'],' not found')
    #
    # now plot the day and S-Bc, S-Bcr plots
    #
    leglist=[]
    if label==0:names=[]
    if len(Bcr1)>0:
        pmagplotlib.plotDay(DSC['day'],Bcr1Bc,S1,'ro',names=names)
        pmagplotlib.plotSBcr(DSC['S-Bcr'],Bcr1,S1,'ro')
        pmagplotlib.plot_init(DSC['bcr1-bcr2'],5,5)
        pmagplotlib.plotBcr(DSC['bcr1-bcr2'],Bcr1,Bcr2)
    else:
        del DSC['bcr1-bcr2']
    pmagplotlib.plotDay(DSC['day'],BcrBc,S,'bs',names=names)
    pmagplotlib.plotSBcr(DSC['S-Bcr'],Bcr,S,'bs')
    pmagplotlib.plotSBc(DSC['S-Bc'],Bc,S,'bs')
    files={}
    if len(locations)>0:locations=locations[:-1]
    for key in DSC.keys():
        if pmagplotlib.isServer: # use server plot naming convention
            files[key] = 'LO:_'+locations+'_'+'SI:__SA:__SP:__TY:_'+key+'_.'+fmt
        else:  # use more readable plot naming convention
            files[key] = '{}_{}.{}'.format(locations, key, fmt)
    if verbose:
        pmagplotlib.drawFIGS(DSC)
        ans=raw_input(" S[a]ve to save plots, return to quit:  ")
        if ans=="a":
            pmagplotlib.saveP(DSC,files)
        else: sys.exit()
    if plots:  pmagplotlib.saveP(DSC,files)
    #

if __name__ == "__main__":
    main()

#!/usr/bin/env python
from __future__ import print_function
from builtins import range
import sys
import random
import pandas as pd
import numpy as np
import pylab
import pmagpy.pmag as pmag

def main():
    """
    NAME
        scalc.py
    DESCRIPTION
       calculates Sb from VGP Long,VGP Lat,Directional kappa,Site latitude data
    SYNTAX
        scalc -h [command line options] [< standard input]
    INPUT
       takes space delimited files with PLong, PLat,[kappa, N_site, slat]
    OPTIONS
        -h prints help message and quits
        -f FILE: specify input file
        -c cutoff:  specify VGP colatitude cutoff value
        -k cutoff: specify kappa cutoff
        -v : use the VanDammme criterion
        -a: use antipodes of reverse data: default is to use only normal
        -C:  use all data without regard to polarity
        -b: do a bootstrap for confidence
        -p: do relative to principle axis
        -n: set minimum n for samples (specimens) per site
        -MM97: correct for within site scatter (McElhinny & McFadden, 1997) 
    NOTES
        if kappa, N_site, lat supplied, will consider within site scatter
    OUTPUT
        N Sb  Sb_lower Sb_upper Co-lat. Cutoff
    """
    coord, kappa, cutoff = "0", 0, 90.
    nb, anti, boot = 1000, 0, 0
    all = 0
    n = 0
    v = 0
    spin = 1
    coord_key = 'tilt_correction'
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-f' in sys.argv:
        ind = sys.argv.index("-f")
        in_file = sys.argv[ind + 1]
        vgp_df=pd.read_csv(in_file,delim_whitespace=True,header=None) 
        #f = open(in_file, 'r')
        #lines = f.readlines()
    else:
        vgp_df=pd.read_csv(sys.stdin,delim_whitespace=True,header=None) 
        #lines = sys.stdin.readlines()
    if '-c' in sys.argv:
        ind = sys.argv.index('-c')
        cutoff = float(sys.argv[ind + 1])
    if '-k' in sys.argv:
        ind = sys.argv.index('-k')
        kappa = float(sys.argv[ind + 1])
    if '-n' in sys.argv:
        ind = sys.argv.index('-n')
        n = int(sys.argv[ind + 1])
    if '-a' in sys.argv:
        anti = 1
    if '-C' in sys.argv:
        cutoff = 180.  # no cutoff
    if '-b' in sys.argv:
        boot = 1
    if '-v' in sys.argv:
        v = 1
    if '-p' in sys.argv:
        spin = 0
    if '-mm97' in sys.argv:
        MM97=True
    else:
        MM97=False
    #
    #
    if len(list(vgp_df.columns))==2:
        vgp_df.columns=['vgp_lon','vgp_lat']
        vgp_df['dir_k'],vgp_df['dir_n'],vgp_df['lat']=0,0,0
    else:
        vgp_df.columns=['vgp_lon','vgp_lat','dir_k','dir_n','lat']
    if anti == 1:
        vgp_rev=vgp_df[vgp_df.vgp_lat<0]
        vgp_norm=vgp_df[vgp_df.vgp_lat>=0]
        vgp_anti=vgp_rev
        vgp_anti['vgp_lat']=-vgp_anti['vgp_lat']
        vgp_anti['vgp_lon']=(vgp_anti['vgp_lon']-180)%360
        vgp_df=pd.concat([vgp_norm,vgp_anti])
    # filter by cutoff, kappa, and n
    vgp_df['delta']=90.-vgp_df.vgp_lat.values
    
    vgp_df=vgp_df[vgp_df.delta<=cutoff]
    vgp_df=vgp_df[vgp_df.dir_k>=kappa]
    vgp_df=vgp_df[vgp_df.dir_n>=n]
    if spin == 0:  # do transformation to pole
        Pvgps=vgp_df[['vgp_lon','vgp_lat']].values
        ppars = pmag.doprinc(Pvgps)
        Bdirs=np.full((Pvgps.shape[0]),ppars['dec']-180.)
        Bdips=np.full((Pvgps.shape[0]),90.-ppars['inc'])
        Pvgps=np.column_stack((Pvgps,Bdirs,Bdips))
        lons,lats=pmag.dotilt_V(Pvgps)
        vgp_df['vgp_lon']=lons
        vgp_df['vgp_lat']=lats
        vgp_df['delta']=90.-vgp_df.vgp_lat
    S_v=0
    if v == 1: 
        vgp_df,cutoff,S_v=pmag.dovandamme(vgp_df)
    S_B = pmag.get_sb_df(vgp_df,MM97=MM97)
    print (S_v,S_B)
    N=vgp_df.shape[0]
    SBs=[]
    if boot == 1:
        print('please be patient...   bootstrapping')
        for i in range(nb):  # now do bootstrap
            bs_df=vgp_df.sample(n=N,replace=True)
            Sb_bs = pmag.get_sb_df(bs_df)
            SBs.append(Sb_bs)
        SBs.sort()
        low = int(.025 * nb)
        high = int(.975 * nb)
        print(vgp_df.shape[0], '%7.1f %7.1f  %7.1f %7.1f ' %
              (S_B, SBs[low], SBs[high], cutoff))
    else:
        print(vgp_df.shape[0], '%7.1f  %7.1f ' % (S_B, cutoff))
#    slats=vgp_df.average_lat.values
#    if slats.shape[0] > 2:
#        print('mean lat = ', '%7.1f' % (slats.mean()))


if __name__ == "__main__":
    main()

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
        -r  use only reverse data, default is False
        -b: do a bootstrap for confidence
        -p: do relative to principle axis
        -n: set minimum n for samples (specimens) per site
        -mm97: correct for within site scatter (McElhinny & McFadden, 1997) 
    NOTES
        if kappa, N_site, lat supplied, will consider within site scatter
    OUTPUT
        N Sb  Sb_lower Sb_upper Co-lat. Cutoff
    """
    kappa, cutoff = 0, 180
    rev, anti, boot = 0, 0, 0
    spin,n,v,mm97 = 0,0,0,0
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-f' in sys.argv:
        ind = sys.argv.index("-f")
        in_file = sys.argv[ind + 1]
        vgp_df=pd.read_csv(in_file,delim_whitespace=True,header=None) 
    else:
        vgp_df=pd.read_csv(sys.stdin,delim_whitespace=True,header=None) 
    if '-c' in sys.argv:
        ind = sys.argv.index('-c')
        cutoff = float(sys.argv[ind + 1])
    if '-k' in sys.argv:
        ind = sys.argv.index('-k')
        kappa = float(sys.argv[ind + 1])
    if '-n' in sys.argv:
        ind = sys.argv.index('-n')
        n = int(sys.argv[ind + 1])
    if '-a' in sys.argv: anti = 1
    if '-r' in sys.argv: rev=1
    if '-b' in sys.argv: boot = 1
    if '-v' in sys.argv: v = 1
    if '-p' in sys.argv: spin = 1
    if '-mm97' in sys.argv: mm97=1
    #
    #
    if len(list(vgp_df.columns))==2:
        vgp_df.columns=['vgp_lon','vgp_lat']
        vgp_df['dir_k'],vgp_df['dir_n_samples'],vgp_df['lat']=0,0,0
    else:
        vgp_df.columns=['vgp_lon','vgp_lat','dir_k','dir_n_samples','lat']
    N,S_B,low,high,cutoff=pmag.scalc_vgp_df(vgp_df,anti=anti,rev=rev,cutoff=cutoff,kappa=kappa,n=n,spin=spin,v=v,boot=boot,mm97=mm97)
    if high!=0:
        print(N, '%7.1f %7.1f  %7.1f %7.1f ' % (S_B, low, high, cutoff))
    else:
        print(N, '%7.1f  %7.1f ' % (S_B, cutoff))


if __name__ == "__main__":
    main()

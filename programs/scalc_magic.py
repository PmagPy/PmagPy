#!/usr/bin/env python
import sys
import pandas as pd
from pmagpy import pmag


def main():
    """
    NAME
        scalc_magic.py

    DESCRIPTION
       calculates Sb from pmag_results files

    SYNTAX
        scalc_magic -h [command line options]

    INPUT
       takes magic formatted pmag_results (2.5) or sites (3.0) table
       pmag_result_name (2.5)  must start with "VGP: Site"
       must have average_lat (2.5)  or lat (3.0) if spin axis is reference

    OPTIONS
        -h prints help message and quits
        -f FILE: specify input results file, default is 'sites.txt'
        -c cutoff:  specify VGP colatitude cutoff value, default is no cutoff
        -k cutoff: specify kappa cutoff, default is 0
        -crd [s,g,t]: specify coordinate system, default is geographic
        -v : use the VanDammme criterion
        -a: use antipodes of reverse data: default is to use only normal
        -r:  use reverse data only
        -p: do relative to principle axis
        -b: do bootstrap confidence bounds
        -n: set minimum n for samples (specimens) per site
        -dm: data model [3.0 is default, otherwise, 2.5]
        -mm97: correct for within site scatter (McElhinny & McFadden, 1997)
    NOTES
        if kappa, N_site, lat supplied, will consider within site scatter
    OUTPUT
        N Sb  Sb_lower Sb_upper Co-lat. Cutoff


     OUTPUT:
         if option -b used: N,  S_B, lower and upper bounds
         otherwise: N,  S_B, cutoff
    """
    coord, kappa, cutoff, n = 0, 0, 180., 0
    nb, anti, spin, v, boot = 1000, 0, 0, 0, 0
    data_model = 3
    rev = 0
    if '-dm' in sys.argv:
        ind = sys.argv.index("-dm")
        data_model = int(sys.argv[ind+1])
    if data_model == 2:
        coord_key = 'tilt_correction'
        in_file = 'pmag_results.txt'
        k_key, n_key, lat_key = 'average_k', 'average_nn', 'average_lat'
    else:
        coord_key = 'dir_tilt_correction'
        in_file = 'sites.txt'
        k_key, n_key, lat_key = 'dir_k', 'dir_n_samples`', 'lat'
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-f' in sys.argv:
        ind = sys.argv.index("-f")
        in_file = sys.argv[ind + 1]
        vgp_df = pd.read_csv(in_file, sep='\t', header=1)
    else:
        vgp_df = pd.read_csv(sys.stdin, sep='\t', header=1)
    if '-c' in sys.argv:
        ind = sys.argv.index('-c')
        cutoff = float(sys.argv[ind+1])
    if '-k' in sys.argv:
        ind = sys.argv.index('-k')
        kappa = float(sys.argv[ind+1])
    if '-n' in sys.argv:
        ind = sys.argv.index('-n')
        n = float(sys.argv[ind+1])
    if '-crd' in sys.argv:
        ind = sys.argv.index("-crd")
        coord = sys.argv[ind+1]
        if coord == 's':
            coord = -1
        if coord == 'g':
            coord = 0
        if coord == 't':
            coord = 100
    if '-a' in sys.argv:
        anti = 1
    if '-r' in sys.argv:
        rev = 1
    if '-p' in sys.argv:
        spin = 1
    if '-v' in sys.argv:
        v = 1
    if '-b' in sys.argv:
        boot = 1
    if '-mm97' in sys.argv:
        mm97 = 1
    else:
        mm97 = 0
    #
    # find desired vgp lat,lon, kappa,N_site data:
    #
    vgp_df.dropna(subset=['vgp_lat', 'vgp_lon'])
    keys = [coord_key, k_key, n_key, lat_key]
    for key in keys:
        if key not in vgp_df.columns:
            vgp_df[key] = 0
    vgp_df = vgp_df[vgp_df[coord_key] == coord]
    if data_model != 3:  # convert
        vgp_df['dir_k'] = vgp_df[k_key]
        vgp_df['dir_n_samples'] = vgp_df[n_key]
        vgp_df['lat'] = vgp_df[lat_key]
    N, S_B, low, high, cutoff = pmag.scalc_vgp_df(
        vgp_df, anti=anti, rev=rev, cutoff=cutoff, kappa=kappa, n=n, spin=spin, v=v, boot=boot, mm97=mm97)
    if high != 0:
        print(N, '%7.1f %7.1f  %7.1f %7.1f ' % (S_B, low, high, cutoff))
    else:
        print(N, '%7.1f  %7.1f ' % (S_B, cutoff))


#
if __name__ == "__main__":
    main()

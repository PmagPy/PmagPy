#!/usr/bin/env python
#
from __future__ import print_function
from builtins import range
import sys
import pmagpy.pmag as pmag
#import numpy.linalg

def main():
    """
    NAME
        bootams.py

    DESCRIPTION
      calculates bootstrap statistics for tensor data

    SYNTAX
        bootams.py [-h][command line options]
    
    OPTIONS:
        -h prints help message and quits
        -f FILE specifies input file name
        -par specifies parametric bootstrap [by whole data set]
        -nb N  specifies the number of bootstrap samples, default is N=1000
    
    INPUT
         x11 x22 x33 x12 x23 x13
     
    OUTPUT
     tau_1 tau_1_sigma V1_dec V1_inc V1_eta V1_eta_dec V1_eta_inc V1_zeta V1_zeta_dec V1_zeta_inc
     tau_2 tau_2_sigma V2_dec V2_inc V2_eta V2_eta_dec V2_eta_inc V2_zeta V2_zeta_dec V2_zeta_inc
     tau_3 tau_2_sigma V3_dec V3_inc V3_eta V3_eta_dec V3_eta_inc V3_zeta V3_zeta_dec V3_zeta_inc
    """
# set options
    ipar,nb=0,1000
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
        f=open(file,'r')
        data=f.readlines()
    if '-par' in sys.argv:ipar=1
    if '-nb' in sys.argv:
        ind=sys.argv.index('-nb')
        nb=int(sys.argv[ind+1])
# read in the data
    print("Doing bootstrap - be patient")
    Ss=[]
    for line in data:
        s=[]
        rec=line.split()
        for i in range(6):
            s.append(float(rec[i]))
        Ss.append(s)
    Tmean,Vmean,Taus,Vs=pmag.s_boot(Ss,ipar,nb)
    bpars=pmag.sbootpars(Taus,Vs) # calculate kent parameters for bootstrap
    bpars["v1_dec"]=Vmean[0][0]
    bpars["v1_inc"]=Vmean[0][1]
    bpars["v2_dec"]=Vmean[1][0]
    bpars["v2_inc"]=Vmean[1][1]
    bpars["v3_dec"]=Vmean[2][0]
    bpars["v3_inc"]=Vmean[2][1]
    bpars["t1"]=Tmean[0]
    bpars["t2"]=Tmean[1]
    bpars["t3"]=Tmean[2]
    print("""
tau tau_sigma V_dec V_inc V_eta V_eta_dec V_eta_inc V_zeta V_zeta_dec V_zeta_inc
""")
    outstring='%7.5f %7.5f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f'%(bpars["t1"],bpars["t1_sigma"],bpars["v1_dec"],bpars["v1_inc"],bpars["v1_zeta"],bpars["v1_zeta_dec"],bpars["v1_zeta_inc"],bpars["v1_eta"],bpars["v1_eta_dec"],bpars["v1_eta_inc"])
    print(outstring)
    outstring='%7.5f %7.5f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f'%(bpars["t2"],bpars["t2_sigma"],bpars["v2_dec"],bpars["v2_inc"],bpars["v2_zeta"],bpars["v2_zeta_dec"],bpars["v2_zeta_inc"],bpars["v2_eta"],bpars["v2_eta_dec"],bpars["v2_eta_inc"])
    print(outstring)
    outstring='%7.5f %7.5f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f'%(bpars["t3"],bpars["t3_sigma"],bpars["v3_dec"],bpars["v3_inc"],bpars["v3_zeta"],bpars["v3_zeta_dec"],bpars["v3_zeta_inc"],bpars["v3_eta"],bpars["v3_eta_dec"],bpars["v3_eta_inc"])
    print(outstring)

if __name__ == "__main__":
    main() 


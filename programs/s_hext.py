#!/usr/bin/env python
#
import sys
import pmagpy.pmag as pmag

def main():
    """
    NAME
        s_hext.py

    DESCRIPTION
     calculates Hext statistics for tensor data

    SYNTAX
        s_hext.py [-h][-i][-f file] [<filename]

    OPTIONS
        -h prints help message and quits
        -f file specifies filename on command line
        -l NMEAS do line by line instead of whole file, use number of measurements NMEAS for degrees of freedom
        < filename, reads from standard input (Unix like operating systems only)

    INPUT
        x11,x22,x33,x12,x23,x13,sigma [sigma only if line by line]

    OUTPUT
       F  F12  F23  sigma
       and three sets of:
        tau dec inc Eij dec inc Eik dec inc
    
    DEFAULT
       average whole file
    """
    ave=1
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-l' in sys.argv:
        ind=sys.argv.index('-l')
        npts=int(sys.argv[ind+1])
        ave=0
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
        f=open(file,'rU')
        data=f.readlines()
        f.close()
    else:
        data=sys.stdin.readlines()
    Ss=[]
    for line in data:
        s=[]
        rec=line.split()
        for i in range(6):
            s.append(float(rec[i]))
        if ave==0:
            sig=float(rec[6])
            hpars=pmag.dohext(npts-6,sig,s)
            print '%s %4.2f %s %4.2f %s %4.2f'%('F = ',hpars['F'],'F12 = ',hpars['F12'],'F23 = ',hpars['F23'])
            print '%s %i %s %14.12f'%('Nmeas = ',npts,' sigma = ',sig)
            print '%7.5f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f'%(hpars["t1"],hpars["v1_dec"],hpars["v1_inc"],hpars["e12"],hpars["v2_dec"],hpars["v2_inc"],hpars["e13"],hpars["v3_dec"],hpars["v3_inc"] )
            print '%7.5f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f'%(hpars["t2"],hpars["v2_dec"],hpars["v2_inc"],hpars["e23"],hpars["v3_dec"],hpars["v3_inc"],hpars["e12"],hpars["v1_dec"],hpars["v1_inc"] )
            print '%7.5f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f'%(hpars["t3"],hpars["v3_dec"],hpars["v3_inc"],hpars["e13"],hpars["v1_dec"],hpars["v1_inc"],hpars["e23"],hpars["v2_dec"],hpars["v2_inc"] )
        else:
            Ss.append(s)
    if ave==1:
        npts=len(Ss)
        nf,sigma,avs=pmag.sbar(Ss)
        hpars=pmag.dohext(nf,sigma,avs)
        print '%s %4.2f %s %4.2f %s %4.2f'%('F = ',hpars['F'],'F12 = ',hpars['F12'],'F23 = ',hpars['F23'])
        print '%s %i %s %14.12f'%('N = ',npts,' sigma = ',sigma)
        print '%7.5f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f'%(hpars["t1"],hpars["v1_dec"],hpars["v1_inc"],hpars["e12"],hpars["v2_dec"],hpars["v2_inc"],hpars["e13"],hpars["v3_dec"],hpars["v3_inc"] )
        print '%7.5f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f'%(hpars["t2"],hpars["v2_dec"],hpars["v2_inc"],hpars["e23"],hpars["v3_dec"],hpars["v3_inc"],hpars["e12"],hpars["v1_dec"],hpars["v1_inc"] )
        print '%7.5f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f'%(hpars["t3"],hpars["v3_dec"],hpars["v3_inc"],hpars["e13"],hpars["v1_dec"],hpars["v1_inc"],hpars["e23"],hpars["v2_dec"],hpars["v2_inc"] )

if __name__ == "__main__":
    main()

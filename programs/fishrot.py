#!/usr/bin/env python
import sys
import pmagpy.pmag as pmag

def main():
    """
    NAME
        fishrot.py

    DESCRIPTION
        generates set of Fisher distributed data from specified distribution 

    SYNTAX
        fishrot.py [-h][-i][command line options]

    OPTIONS
        -h prints help message and quits
        -i for interactive  entry
        -k kappa specify kappa, default is 20
        -n N specify N, default is 100
        -D D specify mean Dec, default is 0
        -I I specify mean Inc, default is 90
        where:
            kappa:  fisher distribution concentration parameter
            N:  number of directions desired
    OUTPUT
        dec,  inc   


    """
    N,kappa,D,I=100,20.,0.,90.
    if len(sys.argv)!=0 and  '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    elif '-i' in sys.argv:
        ans=raw_input('    Kappa: ')
        kappa=float(ans)
        ans=raw_input('    N: ')
        N=int(ans)
        ans=raw_input('    Mean Dec: ')
        D=float(ans)
        ans=raw_input('    Mean Inc: ')
        I=float(ans)
    else:
        if '-k' in sys.argv:
            ind=sys.argv.index('-k')
            kappa=float(sys.argv[ind+1])
        if '-n' in sys.argv:
            ind=sys.argv.index('-n')
            N=int(sys.argv[ind+1])
        if '-D' in sys.argv:
            ind=sys.argv.index('-D')
            D=float(sys.argv[ind+1])
        if '-I' in sys.argv:
            ind=sys.argv.index('-I')
            I=float(sys.argv[ind+1])
    for k in range(N): 
        dec,inc= pmag.fshdev(kappa)  # send kappa to fshdev
        drot,irot=pmag.dodirot(dec,inc,D,I)   
        print '%7.1f %7.1f ' % (drot,irot)

if __name__ == "__main__":
    main()

#! /usr/bin/env python
import math,random,pmag,sys,pmagplotlib
#

def main():
    """
    NAME
       probRo.py

    DESCRIPTION
       Calculates Ro as a test for randomness - if R exceeds Ro given N, then set is not random at 95% level of confindence

    SYNTAX
       probRo.py [command line options]

    OPTIONS
        -h prints this help message
        -Nm number of Monte Carlo simulations (default is 10000)
        -Nmax maximum number for dataset (default is 10)
    """
    Ns,Nm=range(4,11),10000
    files,fmt={},'svg'
    if '-h' in sys.argv: # check if help is needed
        print main.__doc__
        sys.exit() # graceful quit
    if '-Nm' in sys.argv: 
        ind=sys.argv.index('-Nm')
        Nm=int(sys.argv[ind+1])
    if '-Nmax' in sys.argv: 
        ind=sys.argv.index('-Nmax')
        Nmax=int(sys.argv[ind+1])
        Ns=range(3,Nmax+1)
    PLT={'plt':1}
    pmagplotlib.plot_init(PLT['plt'],5,5)
    Ro=[]
    for N in Ns:
        Rs=[]
        n=0
        while n<Nm:
            dirs=pmag.get_unf(N)
            pars=pmag.fisher_mean(dirs)
            Rs.append(pars['r'])
            n+=1
        Rs.sort()
        crit=int(.95*Nm)
        Ro.append(Rs[crit])
    pmagplotlib.plotXY(PLT['plt'],Ns,Ro,'-','N','Ro','')
    pmagplotlib.plotXY(PLT['plt'],Ns,Ro,'ro','N','Ro','')
    pmagplotlib.drawFIGS(PLT)
    for key in PLT.keys():
        files[key]=key+'.'+fmt
    ans=raw_input(" S[a]ve to save plot, [q]uit without saving:  ")
    if ans=="a": pmagplotlib.saveP(PLT,files)

main()

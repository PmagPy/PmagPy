#!/usr/bin/env python
import pmag,sys,numpy,pmagplotlib
from numpy import random
def EI(inc):
    poly_tk03= [  3.15976125e-06,  -3.52459817e-04,  -1.46641090e-02,   2.89538539e+00]  
    return poly_tk03[0]*inc**3 + poly_tk03[1]*inc**2+poly_tk03[2]*inc+poly_tk03[3]


def find_f(data):
    rad=numpy.pi/180.
    Es,Is,Fs,V2s=[],[],[],[]
    ppars=pmag.doprinc(data)
    D=ppars['dec']
    Decs,Incs=data.transpose()[0],data.transpose()[1]
    Tan_Incs=numpy.tan(Incs*rad)
    for f in numpy.arange(1.,.2 ,-.01):
        U=numpy.arctan((1./f)*Tan_Incs)/rad
        fdata=numpy.array([Decs,U]).transpose()
        ppars=pmag.doprinc(fdata)
        Fs.append(f)
        Es.append(ppars["tau2"]/ppars["tau3"])
        angle=pmag.angle([D,0],[ppars["V2dec"],0])
        if 180.-angle<angle:angle=180.-angle
        V2s.append(angle)
        Is.append(abs(ppars["inc"]))
        if EI(abs(ppars["inc"]))<=Es[-1]:
            del Es[-1]
            del Is[-1]
            del Fs[-1]
            del V2s[-1]
            if len(Fs)>0:
                for f in numpy.arange(Fs[-1],.2 ,-.005):
                    U=numpy.arctan((1./f)*Tan_Incs)/rad
                    fdata=numpy.array([Decs,U]).transpose()
                    ppars=pmag.doprinc(fdata)
                    Fs.append(f)
                    Es.append(ppars["tau2"]/ppars["tau3"])
                    Is.append(abs(ppars["inc"]))
                    angle=pmag.angle([D,0],[ppars["V2dec"],0])
                    if 180.-angle<angle:angle=180.-angle
                    V2s.append(angle)
                    if EI(abs(ppars["inc"]))<=Es[-1]:
                        return Es,Is,Fs,V2s
    return [0],[0],[0],[0]
def main():
    """
    NAME
        find_EI.py
 
    DESCRIPTION
        Applies series of assumed flattening factor and "unsquishes" inclinations assuming tangent function.
        Finds flattening factor that gives elongation/inclination pair consistent with TK03.  
        Finds bootstrap confidence bounds

    SYNTAX
        find_EI.py [command line options]

    OPTIONS
        -h prints help message and quits
        -i allows interactive input of file name
        -f FILE specify input file name
        -nb N specify number of bootstraps - the more the better, but slower!, default is 1000
        -fmt [svg,png,eps,pdf..] change plot format, default is svg
        -sav  saves the figures and quits

    INPUT
        dec/inc pairs, delimited with space or tabs

    OUTPUT
        four plots:  1) equal area plot of original directions
                      2) Elongation/inclination pairs as a function of f,  data plus 25 bootstrap samples
                      3) Cumulative distribution of bootstrapped optimal inclinations plus uncertainties.
                         Estimate from original data set plotted as solid line
                      4) Orientation of principle direction through unflattening
    NOTE: If distribution does not have a solution, plot labeled: Pathological.  Some bootstrap samples may have
       valid solutions and those are plotted in the CDFs and E/I plot.

    """
    fmt,nb='svg',1000
    plot=0
    if '-i' in sys.argv:
        file=raw_input("Enter file name for processing: ")
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit() # graceful quit
    elif '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
    else:
        print main.__doc__
        sys.exit()
    if '-nb' in sys.argv:
        ind=sys.argv.index('-nb')
        nb=int(sys.argv[ind+1])
    if '-fmt' in sys.argv:
        ind=sys.argv.index('-fmt')
        fmt=sys.argv[ind+1]
    if '-sav' in sys.argv:plot=1
    data=numpy.loadtxt(file)
    upper,lower=int(round(.975*nb)),int(round(.025*nb))
    E,I=[],[]
    PLTS={'eq':1,'ei':2,'cdf':3,'v2':4}
    pmagplotlib.plot_init(PLTS['eq'],6,6) 
    pmagplotlib.plot_init(PLTS['ei'],5,5) 
    pmagplotlib.plot_init(PLTS['cdf'],5,5) 
    pmagplotlib.plot_init(PLTS['v2'],5,5) 
    pmagplotlib.plotEQ(PLTS['eq'],data,'Data')
    if plot==0:pmagplotlib.drawFIGS(PLTS)
    ppars=pmag.doprinc(data)
    Io=ppars['inc']
    n=ppars["N"]
    Es,Is,Fs,V2s=find_f(data)
    Inc,Elong=Is[-1],Es[-1]
    pmagplotlib.plotEI(PLTS['ei'],Es,Is,Fs[-1])
    pmagplotlib.plotV2s(PLTS['v2'],V2s,Is,Fs[-1])
    b=0
    print "Bootstrapping.... be patient"
    while b<nb:
        bdata=pmag.pseudo(data)
        Es,Is,Fs,V2s=find_f(bdata)
        if b<25:
            pmagplotlib.plotEI(PLTS['ei'],Es,Is,Fs[-1])
        if Es[-1]!=0:
            ppars=pmag.doprinc(bdata)
            I.append(abs(Is[-1]))
            E.append(Es[-1])
            b+=1
            if b%25==0:print b,' out of ',nb
    I.sort()
    E.sort()
    Eexp=[]
    for i in I:
       Eexp.append(EI(i)) 
    if Inc==0:
        title= 'Pathological Distribution: '+'[%7.1f, %7.1f]' %(I[lower],I[upper])
    else:
        title= '%7.1f [%7.1f, %7.1f]' %( Inc, I[lower],I[upper])
    pmagplotlib.plotEI(PLTS['ei'],Eexp,I,1)
    pmagplotlib.plotCDF(PLTS['cdf'],I,'Inclinations','r',title)
    pmagplotlib.plotVs(PLTS['cdf'],[I[lower],I[upper]],'b','--')
    pmagplotlib.plotVs(PLTS['cdf'],[Inc],'g','-')
    pmagplotlib.plotVs(PLTS['cdf'],[Io],'k','-')
    if plot==0:
        pmagplotlib.drawFIGS(PLTS)
        print "Io Inc  I_lower, I_upper, Elon, E_lower, E_upper"
        print '%7.1f %s %7.1f _ %7.1f ^ %7.1f:  %6.4f _ %6.4f ^ %6.4f' %(Io, " => ", Inc, I[lower],I[upper], Elong, E[lower],E[upper])
        ans= raw_input("S[a]ve plots - <return> to quit:  ")
        if ans!='a':
           print "\n Good bye\n"
           sys.exit()
    files={}
    files['eq']='findEI_eq.'+fmt
    files['ei']='findEI_ei.'+fmt
    files['cdf']='findEI_cdf.'+fmt
    files['v2']='findEI_v2.'+fmt
    pmagplotlib.saveP(PLTS,files)
main()

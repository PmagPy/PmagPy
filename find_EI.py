#!/usr/bin/env python
import pmag,math,random,sys,numpy,pmagplotlib,exceptions
def EI(inc):
    poly_tk03= [  3.15976125e-06,  -3.52459817e-04,  -1.46641090e-02,   2.89538539e+00]  
    return poly_tk03[0]*inc**3 + poly_tk03[1]*inc**2+poly_tk03[2]*inc+poly_tk03[3]


def find_f(data):
    rad=math.pi/180.
    Es,Is,Fs,V2s=[],[],[],[]
    ppars=pmag.doprinc(data)
    D=ppars['dec']
    for f in numpy.arange(1.,.2 ,-.01):
        fdata=[]
        for rec in data:
            U=math.atan((1./f)*math.tan(rec[1]*rad))/rad
            fdata.append([rec[0],U,1.])
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
                    for rec in data:
                        U=math.atan((1./f)*math.tan(rec[1]*rad))/rad
                        fdata.append([rec[0],U,1.])
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
        Applies assumed flattening factor and "unsquishes" inclinations assuming tangent function.
        Finds flattening factor that gives elongation/inclination pair consistent with TK03.  
        Finds bootstrap confidence bounds

    SYNTAX
        find_EI.py [-h][-i] [-f FILE] 

    INPUT
        dec/inc pairs

    OUTPUT
        three plots:  1) equal area plot of original directions
                      2) Elongation/inclination pairs as a function of f,  data plus 25 bootstrap samples
                      3) Cumulative distribution of bootstrapped optimal inclinations plus uncertainties.
                         Estimate from original data set plotted as solid line

    """
    if '-i' in sys.argv:
        file=raw_input("Enter file name for processing: ")
        f=open(file,'rU') 
    elif '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
        f=open(file,'rU') 
    else:
        print main.__doc__
        sys.exit()
    rseed,nb,data=10,100,[]
    upper,lower=int(round(.975*nb)),int(round(.025*nb))
    E,I=[],[]
    PLTS={'eq':1,'ei':2,'cdf':3,'v2':4}
    pmagplotlib.plot_init(PLTS['eq'],6,6) 
    pmagplotlib.plot_init(PLTS['ei'],5,5) 
    pmagplotlib.plot_init(PLTS['cdf'],5,5) 
    pmagplotlib.plot_init(PLTS['v2'],5,5) 
    random.seed(rseed)
    for line in f.readlines():
        rec=line.split()
        dec=float(rec[0])
        inc=float(rec[1])
        rec=[dec,inc,1.]
        data.append(rec)
    pmagplotlib.plotEQ(PLTS['eq'],data,'Data')
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
        bdata=[]
        for j in range(n):
            boot=random.randint(0,n-1)
            random.jumpahead(rseed)
            bdata.append(data[boot])
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
    title= '%7.1f [%7.1f, %7.1f]' %( Inc, I[lower],I[upper])
    pmagplotlib.plotEI(PLTS['ei'],Eexp,I,1)
    pmagplotlib.plotCDF(PLTS['cdf'],I,'Inclinations','r',title)
    pmagplotlib.plotVs(PLTS['cdf'],[I[lower],I[upper]],'b','--')
    pmagplotlib.plotVs(PLTS['cdf'],[Inc],'g','-')
    pmagplotlib.plotVs(PLTS['cdf'],[Io],'k','-')
    pmagplotlib.drawFIGS(PLTS)
    print "Io Inc  I_lower, I_upper, Elon, E_lower, E_upper"
    print '%7.1f %s %7.1f _ %7.1f ^ %7.1f:  %6.4f _ %6.4f ^ %6.4f' %(Io, " => ", Inc, I[lower],I[upper], Elong, E[lower],E[upper])
    try:
        raw_input("Return to save plots - <return> to quit:  ")
    except EOFError:
       print "\n Good bye\n"
       sys.exit()
    files={}
    files['eq']='findEI_eq.svg'
    files['ei']='findEI_ei.svg'
    files['cdf']='findEI_cdf.svg'
    files['v2']='findEI_v2.svg'
    pmagplotlib.saveP(PLTS,files)
main()

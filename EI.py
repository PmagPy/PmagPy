#!/usr/bin/env python
import pmag,math,random,sys,numpy,pmagplotlib
def EI(inc,poly):
    return poly[0]*inc**3 + poly[1]*inc**2 + poly[2]*inc + poly[3]

def main():
    """
    NAME
        EI.py [command line options]

    DESCRIPTION
        Finds bootstrap confidence bounds on Elongation and Inclination data

    SYNTAX
        EI.py  [command line options]

    OPTIONS
        -h prints help message and quits
        -f FILE specifies input file
        -p do parametric bootstrap

    INPUT
        dec/inc pairs

    OUTPUT
        makes a plot of the E/I pair and bootstrapped confidence bounds
        along with the E/I trend predicted by the TK03 field model
        prints out:
            Io (mean inclination), I_lower and I_upper are 95% confidence bounds on inclination
            Eo (elongation), E_lower and E_upper are 95% confidence bounds on elongation
            Edec,Einc are the elongation direction

    """
    par=0
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=open(sys.argv[ind+1],'rU')
    if '-p' in sys.argv: par=1
    rseed,nb,data=10,5000,[]
    upper,lower=int(round(.975*nb)),int(round(.025*nb))
    Es,Is=[],[]
    PLTS={'eq':1,'ei':2}
    pmagplotlib.plot_init(PLTS['eq'],5,5) 
    pmagplotlib.plot_init(PLTS['ei'],5,5) 
#    poly_tab= [  3.07448925e-06,  -3.49555831e-04,  -1.46990847e-02,   2.90905483e+00]
    poly_new= [  3.15976125e-06,  -3.52459817e-04,  -1.46641090e-02,   2.89538539e+00]
#    poly_cp88= [ 5.34558576e-06,  -7.70922659e-04,   5.18529685e-03,   2.90941351e+00]
#    poly_qc96= [  7.08210133e-06,  -8.79536536e-04,   1.09625547e-03,   2.92513660e+00]
#    poly_cj98=[  6.56675431e-06,  -7.91823539e-04,  -1.08211350e-03,   2.80557710e+00]
#    poly_tk03_g20= [  4.96757685e-06,  -6.02256097e-04,  -5.96103272e-03,   2.84227449e+00]
#    poly_tk03_g30= [  7.82525963e-06,  -1.39781724e-03,   4.47187092e-02,   2.54637535e+00]
#    poly_gr99_g=[  1.24362063e-07,  -1.69383384e-04,  -4.24479223e-03,   2.59257437e+00]
#    poly_gr99_e=[  1.26348154e-07,   2.01691452e-04,  -4.99142308e-02,   3.69461060e+00]
    E_EI,E_tab,E_new,E_cp88,E_cj98,E_qc96,E_tk03_g20=[],[],[],[],[],[],[]
    E_tk03_g30,E_gr99_g,E_gr99_e=[],[],[]
    I2=range(0,90,5)
    for inc in I2:
        E_new.append(EI(inc,poly_new)) # use the polynomial from Tauxe et al. (2008)
    pmagplotlib.plotEI(PLTS['ei'],E_new,I2,1)
    if '-f' in sys.argv:
        random.seed(rseed)
        for line in file.readlines():
            rec=line.split()
            dec=float(rec[0])
            inc=float(rec[1])
            if par==1:
                if  len(rec)==4:
                    N=(int(rec[2]))  # append n
                    K=float(rec[3])  # append k
                    rec=[dec,inc,N,K]
                    data.append(rec)
            else:
                rec=[dec,inc]
                data.append(rec)
        pmagplotlib.plotEQ(PLTS['eq'],data,'Data')
        ppars=pmag.doprinc(data)
        n=ppars["N"]
        Io=ppars['inc']
        Edec=ppars['Edir'][0]
        Einc=ppars['Edir'][1]
        Eo=(ppars['tau2']/ppars['tau3'])
        b=0
        print 'doing bootstrap - be patient'
        while b<nb:
            bdata=[]
            for j in range(n):
                boot=random.randint(0,n-1)
                random.jumpahead(rseed)
                if par==1:
                    DIs=[]
                    D,I,N,K=data[boot][0],data[boot][1],data[boot][2],data[boot][3]
                    for k in range(N):
                        dec,inc=pmag.fshdev(K)
                        drot,irot=pmag.dodirot(dec,inc,D,I)
                        DIs.append([drot,irot])
                    fpars=pmag.fisher_mean(DIs)
                    bdata.append([fpars['dec'],fpars['inc'],1.])  # replace data[boot] with parametric dec,inc    
                else:
                    bdata.append(data[boot])
            ppars=pmag.doprinc(bdata)
            Is.append(ppars['inc'])
            Es.append(ppars['tau2']/ppars['tau3'])
            b+=1
            if b%100==0:print b
        Is.sort()
        Es.sort()
        x,std=pmag.gausspars(Es)
        stderr=std/math.sqrt(len(data))
        pmagplotlib.plotX(PLTS['ei'],Io,Eo,Is[lower],Is[upper],Es[lower],Es[upper],'b-')
#        pmagplotlib.plotX(PLTS['ei'],Io,Eo,Is[lower],Is[upper],Eo-stderr,Eo+stderr,'b-')
        print 'Io, Eo, I_lower, I_upper, E_lower, E_upper, Edec, Einc'
        print '%7.1f %4.2f %7.1f %7.1f %4.2f %4.2f %7.1f %7.1f' %(Io,Eo,Is[lower],Is[upper],Es[lower],Es[upper], Edec,Einc)
#        print '%7.1f %4.2f %7.1f %7.1f %4.2f %4.2f' %(Io,Eo,Is[lower],Is[upper],Eo-stderr,Eo+stderr)
    pmagplotlib.drawFIGS(PLTS)
    files,fmt={},'svg'
    for key in PLTS.keys():
        files[key]=key+'.'+fmt 
    ans=raw_input(" S[a]ve to save plot, [q]uit without saving:  ")
    if ans=="a": pmagplotlib.saveP(PLTS,files) 
main()

#!/usr/bin/env python
import sys,pmag,matplotlib,pmagplotlib
matplotlib.use("TkAgg")
import pylab
def EI(inc):
    return .0004*inc**2 - 0.0154*inc +2.84


def main():
    """
    NAME
       foldtest.py

    DESCRIPTION
       does a fold test (Tauxe, 2007) on data

    INPUT FORMAT
       dec inc dip_direction dip

    SYNTAX
       foldtest.py [-h][-i][command line options]

    OPTIONS
        -h prints help message and quits
        -i for interactive parameter entry
        -f FILE
    
    OUTPUT
        Geographic: is an equal area projection of the input data in 
                    original coordinates
        Stratigraphic: is an equal area projection of the input data in 
                    tilt adjusted coordinates
        % Untilting: The dashed (red) curves are representative plots of 
                    maximum eigenvalue (tau_1) as a function of untilting
                    The solid line is the cumulative distribution of the
                    % Untilting required to maximize tau for all the 
                    bootstrapped data sets.  The dashed vertical lines
                    are 95% confidence bounds on the % untilting that yields 
                   the most clustered result (maximum tau_1).  
        Command line: prints out the bootstrapped iterations and
                   finally the confidence bounds on optimum untilting.
        If the 95% conf bounds include 0, then a pre-tilt magnetization is indicated
        If the 95% conf bounds include 100, then a post-tilt magnetization is indicated
        If the 95% conf bounds exclude both 0 and 100, syn-tilt magnetization is
                possible as is vertical axis rotation or other pathologies

    """
    if '-h' in sys.argv: # check if help is needed
        print main.__doc__
        sys.exit() # graceful quit
    if '-i' in sys.argv: # ask for filename
        file=raw_input("Enter file name with dec, inc dip_direction and dip data: ")
        f=open(file,'rU')
        data=f.readlines()
    elif '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1] 
        f=open(file,'rU')
        data=f.readlines()
    else:
        print main.__doc__
        sys.exit()
#
# get to work
#
    PLTS={'geo':1,'strat':2,'taus':3,'ei':4} # make plot dictionary
    pmagplotlib.plot_init(PLTS['geo'],5,5)
    pmagplotlib.plot_init(PLTS['strat'],5,5)
    pmagplotlib.plot_init(PLTS['taus'],5,5)
    pmagplotlib.plot_init(PLTS['ei'],5,5)
    DIDDs= [] # set up list for dec inc  dip_direction, dip
    nb=100 # number of bootstraps
    for line in data:   # read in the data from standard input
        rec=line.split() # split each line on space to get records
        DIDDs.append([float(rec[0]),float(rec[1]),float(rec[2]),float(rec[3])])
    pmagplotlib.plotEQ(PLTS['geo'],DIDDs,'Geographic')
    TCs,Ps,Taus,Es,Is=[],[],[],[],[]
    for k in range(len(DIDDs)):
        drot,irot=pmag.dotilt(DIDDs[k][0],DIDDs[k][1],DIDDs[k][2],DIDDs[k][3])
        TCs.append([drot,irot,1.])
    pmagplotlib.plotEQ(PLTS['strat'],TCs,'Stratigraphic')
    Percs=range(-10,110)
    for perc in Percs:
        tilt=0.01*perc
        TCs=[]
        for k in range(len(DIDDs)):
            drot,irot=pmag.dotilt(DIDDs[k][0],DIDDs[k][1],DIDDs[k][2],tilt*DIDDs[k][3])
            TCs.append([drot,irot,1.])
        ppars=pmag.doprinc(TCs) # get principal directions
        Taus.append(ppars['tau1'])
        Es.append(ppars["tau2"]/ppars["tau3"])
        Is.append(ppars["inc"])
        if int(10*(EI(ppars["inc"])))==int(10*Es[-1]): 
            print EI(ppars["inc"]),Es[-1],perc
            Ps.append(perc)
    pylab.figure(num=PLTS['taus'])
    pylab.plot(Percs,Taus,'b-')
    pylab.figure(num=PLTS['ei'])
    pylab.plot(Es,Is,'b-')
    Is.sort()
    Eexp=[] 
    for i in Is: Eexp.append(EI(i))
    pylab.plot(Eexp,Is,'g-')
    Cdf,Untilt=[],[]
    print 'doing ',nb,' iterations...please be patient.....'
    for n in range(nb): # do bootstrap data sets - plot first 25 as dashed red line
        Es,Is=[],[]
        if n%50==0:print n
        Taus=[] # set up lists for taus
        PDs=pmag.pseudo(DIDDs)
        for perc in Percs:
            tilt=0.01*perc
            TCs=[]
            for k in range(len(PDs)):
                drot,irot=pmag.dotilt(PDs[k][0],PDs[k][1],PDs[k][2],tilt*PDs[k][3])
                TCs.append([drot,irot,1.])
            ppars=pmag.doprinc(TCs) # get principal directions
            Taus.append(ppars['tau1'])
            Es.append(ppars["tau2"]/ppars["tau3"])
            Is.append(ppars["inc"])
            if int(10*(EI(ppars["inc"])))==int(10*Es[-1]): 
                Ps.append(perc)
        if n<25:
            pylab.figure(num=PLTS['taus'])
            pylab.plot(Percs,Taus,'r--')
            pylab.figure(num=PLTS['ei'])
            pylab.plot(Es,Is,'r--')
        Untilt.append(Percs[Taus.index(pylab.max(Taus))]) # tilt that gives maximum tau
        Cdf.append(float(n)/float(nb))
    pylab.figure(num=PLTS['taus'])
    pylab.plot(Percs,Taus,'k')
    pylab.xlabel('% Untilting')
    pylab.ylabel('tau_1 (red), CDF (green)')
    Untilt.sort() # now for CDF of tilt of maximum tau
    Ps.sort()
    pylab.plot(Untilt,Cdf,'g')
    lower=int(.025*nb)     
    upper=int(.975*nb)
    pylab.axvline(x=Untilt[lower],ymin=0,ymax=1,linewidth=1,linestyle='--')
    pylab.axvline(x=Untilt[upper],ymin=0,ymax=1,linewidth=1,linestyle='--')
    tit= '%i - %i %s'%(Untilt[lower],Untilt[upper],'Percent Unfolding')
    pylab.title(tit)
    print Ps[lower],Ps[upper]
    pmagplotlib.drawFIGS(PLTS)
    try:
        raw_input('Return to save all figures, cntl-d to quit\n')
    except EOFError:
        print "Good bye"
        sys.exit()
    files={}
    for key in PLTS.keys():
        files[key]=('fold_'+'%s'%(key.strip()[:2])+'.svg')
    pmagplotlib.saveP(PLTS,files)
main()

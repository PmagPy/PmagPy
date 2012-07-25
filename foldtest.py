#!/usr/bin/env python
import sys,pmag,matplotlib,pmagplotlib
import exceptions
import pylab,numpy
def main():
    """
    NAME
       foldtest.py

    DESCRIPTION
       does a fold test (Tauxe, 2008) on data

    INPUT FORMAT
       dec inc dip_direction dip

    SYNTAX
       foldtest.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f FILE
        -u ANGLE (circular standard deviation) for uncertainty on bedding poles
        -b MIN MAX bounds for quick search of percent untilting [default is -10 to 150%]
        -n NB  number of bootstrap samples [default is 1000]
    
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
    kappa=0
    nb=1000 # number of bootstraps
    min,max=-10,150
    if '-h' in sys.argv: # check if help is needed
        print main.__doc__
        sys.exit() # graceful quit
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1] 
        f=open(file,'rU')
        data=f.readlines()
    else:
        print main.__doc__
        sys.exit()
    if '-b' in sys.argv:
        ind=sys.argv.index('-b')
        min=float(sys.argv[ind+1])
        max=float(sys.argv[ind+2])
    if '-n' in sys.argv:
        ind=sys.argv.index('-n')
		nb=int(sys.argv[ind+1])
	    if '-u' in sys.argv:
		ind=sys.argv.index('-u')
		csd=float(sys.argv[ind+1])
		kappa=(81./csd)**2
	#
	# get to work
	#
	    PLTS={'geo':1,'strat':2,'taus':3} # make plot dictionary
	    pmagplotlib.plot_init(PLTS['geo'],5,5)
	    pmagplotlib.plot_init(PLTS['strat'],5,5)
	    pmagplotlib.plot_init(PLTS['taus'],5,5)
	    DIDDs= [] # set up list for dec inc  dip_direction, dip
	    for line in data:   # read in the data from standard input
		rec=line.split() # split each line on space to get records
		DIDDs.append([float(rec[0]),float(rec[1]),float(rec[2]),float(rec[3])])
	    pmagplotlib.plotEQ(PLTS['geo'],DIDDs,'Geographic')
	    TCs=[]
	    for k in range(len(DIDDs)):
		drot,irot=pmag.dotilt(DIDDs[k][0],DIDDs[k][1],DIDDs[k][2],DIDDs[k][3])
		TCs.append([drot,irot,1.])
	    pmagplotlib.plotEQ(PLTS['strat'],TCs,'Stratigraphic')
	    pmagplotlib.drawFIGS(PLTS)
	    Percs=range(min,max)
	    Cdf,Untilt=[],[]
	    pylab.figure(num=PLTS['taus'])
	    print 'doing ',nb,' iterations...please be patient.....'
    for n in range(nb): # do bootstrap data sets - plot first 25 as dashed red line
        if n%50==0:print n
        Taus=[] # set up lists for taus
        PDs=pmag.pseudo(DIDDs)
        if kappa!=0:
            for k in range(len(PDs)):
                d,i=pmag.fshdev(kappa)
                dipdir,dip=pmag.dodirot(d,i,PDs[k][2],PDs[k][3])
                PDs[k][2]=dipdir            
                PDs[k][3]=dip
        for perc in Percs:
            tilt=0.01*perc
            TCs=[]
            for k in range(len(PDs)):
                drot,irot=pmag.dotilt(PDs[k][0],PDs[k][1],PDs[k][2],tilt*PDs[k][3])
                TCs.append([drot,irot,1.])
            ppars=pmag.doprinc(TCs) # get principal directions
            Taus.append(ppars['tau1'])
        if n<25:pylab.plot(Percs,Taus,'r--')
        Untilt.append(Percs[Taus.index(numpy.max(Taus))]) # tilt that gives maximum tau
        Cdf.append(float(n)/float(nb))
    pylab.plot(Percs,Taus,'k')
    pylab.xlabel('% Untilting')
    pylab.ylabel('tau_1 (red), CDF (green)')
    Untilt.sort() # now for CDF of tilt of maximum tau
    pylab.plot(Untilt,Cdf,'g')
    lower=int(.025*nb)     
    upper=int(.975*nb)
    pylab.axvline(x=Untilt[lower],ymin=0,ymax=1,linewidth=1,linestyle='--')
    pylab.axvline(x=Untilt[upper],ymin=0,ymax=1,linewidth=1,linestyle='--')
    tit= '%i - %i %s'%(Untilt[lower],Untilt[upper],'Percent Unfolding')
    print tit
    print 'range of all bootstrap samples: ', Untilt[0], ' - ', Untilt[-1]
    pylab.title(tit)
    pylab.ion()
    pylab.draw()
    pylab.ioff()
    try:
        raw_input('Return to save all figures, cntl-d to quit\n')
    except:
        print "Good bye"
        sys.exit()
    files={}
    for key in PLTS.keys():
        files[key]=('fold_'+'%s'%(key.strip()[:2])+'.svg')
    pmagplotlib.saveP(PLTS,files)
main()

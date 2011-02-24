#!/usr/bin/env python
import pmag,sys,exceptions,matplotlib
matplotlib.use("TkAgg")
import pylab
pylab.ion()
def main():
    """
    NAME 
        Core_depthplot.py

    DESCRIPTION
        plots various measurements versus core_depth

    SYNTAX
        Core_depthplot.py [command line optins]

    OPTIONS
        -h prints help message and quits
        -f FILE: specify input magic_measurments format file from magic
        -fsa FILE: specify input er_samples format file from magic
        -AF step [in mT] to plot 
        -T step [in C] to plot 
        -d min max [in m] depth range to plot
        -Iex: plot the expected inc at lat - only available for results with lat info in file
        -ts TS amin amax: plot the GPTS for the time interval between amin and amax (numbers in Ma)
           TS: [ck95, gts04] 

     DEFAULTS:
         Measurements file: magic_measurements.txt
         Samples file: er_samples.txt
         NRM step
    """
    method,fmt="LT-NO",'.svg'
    step=0
    pcol=3
    plotexp,pTS=0,0
    dir_path="./"
    if '-WD' in sys.argv: 
        ind=sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
    meas_file=dir_path+'/magic_measurements.txt'
    samp_file=dir_path+'/er_samples.txt'
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        meas_file=dir_path+'/'+sys.argv[ind+1]
    if '-fsa' in sys.argv:
        ind=sys.argv.index('-fsa')
        samp_file=dir_path+'/'+sys.argv[ind+1]
    if '-fmt' in sys.argv:
        ind=sys.argv.index('-fmt')
        fmt='.'+sys.argv[ind+1]
    if '-AF' in sys.argv:
        ind=sys.argv.index('-AF')
        step=float(sys.argv[ind+1])*1e-3
        method='LT-AF-Z'
    if '-T' in sys.argv:
        ind=sys.argv.index('-T')
        step=float(sys.argv[ind+1])+273
        method='LT-T-Z'
    dmin,dmax=-1,-1
    if '-d' in sys.argv:
        ind=sys.argv.index('-d')
        dmin=float(sys.argv[ind+1])
        dmax=float(sys.argv[ind+2])
    if '-ts' in sys.argv:
        ind=sys.argv.index('-ts')
        ts=sys.argv[ind+1]
        amin=float(sys.argv[ind+2])
        amax=float(sys.argv[ind+3])
        pTS,pcol=1,4
    if '-Iex' in sys.argv: plotexp=1
    #
    #
    # get data read in
    Meas,file_type=pmag.magic_read(meas_file) 
    Samps,file_type=pmag.magic_read(samp_file) 
    Data=[]
    for rec in Meas:
        for samp in Samps:
            if samp['er_sample_name']== rec['er_sample_name'] and 'core_depth' in samp.keys() and samp['core_depth']!="":
                rec['core_depth'] = samp['core_depth']
                Data.append(rec) # fish out data with core_depth
    if plotexp==1:
        for lkey in Lat_keys:
            for key in Results[0].keys():
                if key==lkey:    
                    lat=float(Results[0][lkey])
                    Xinc=[pmag.pinc(lat),-pmag.pinc(lat)]
                    break
        if Xinc=="":
            print 'can not plot expected inc for site - lat unknown'
    xlab="Core Depth (m)"
    # collect the data for plotting declination
    Depths,Decs,Incs,Ints=[],[],[],[]
    maxInt=-1000
    samples=[]
    for rec in Data:
        if "magic_method_codes" in rec.keys():
            meths=rec["magic_method_codes"].split(":")
            if method in meths: # make sure it is desired lab treatment step
                if ('LT-AF-Z' in method and float(rec['treatment_ac_field'])==step) or ('LT-NO' in method and step == 0) or ('LT-T-Z' in method and float(rec['treatment_temp'])==step):
                    Depths.append(float(rec['core_depth']))
                    Decs.append(float(rec['measurement_dec']))
                    Incs.append(float(rec['measurement_inc']))
                    Ints.append(float(rec['measurement_magn_moment']))
                    if len(Ints)>1 and Ints[-1]>maxInt:maxInt=Ints[-1]
    if dmin==-1:
        dmin,dmax=Depths[0],Depths[-1]
    if len(Decs)>0 and len(Depths)>0:
        for pow in range(-10,10):
            if maxInt*10**pow>1:break
        for k in range(len(Ints)):
            Ints[k]=Ints[k]*10**pow
        pylab.figure(1,figsize=(10,8))
        pylab.subplot(1,pcol,1)
        pylab.plot(Decs,Depths,'ro',Decs,Depths,'k') 
        pylab.axis([0,360,dmax,dmin])
        pylab.xlabel('Declination')
        pylab.ylabel('Depth in core (m)')
        pylab.subplot(1,pcol,2)
        pylab.plot(Incs,Depths,'bo',Incs,Depths,'k') 
        pylab.axis([-90,90,dmax,dmin])
        pylab.xlabel('Inclination')
        pylab.ylabel('')
        pylab.subplot(1,pcol,3)
        pylab.plot(Ints,Depths,'ko',Ints,Depths,'k') 
        pylab.axis([0,maxInt*10**pow+.1,dmax,dmin])
        pylab.xlabel('%s %i %s'%('Intensity (x 10^',pow,' Am^2)'))
        if pTS==1:
            pylab.subplot(1,pcol,4)
            TS,Chrons=pmag.get_TS(ts)
            p=1
            X,Y=[],[]
            for d in TS:
                if d<=amax:
                    if d>=amin:
                        if len(X)==0:
                            ind=TS.index(d)
                            X.append(TS[ind-1])
                            Y.append(p%2)
                        X.append(d)
                        Y.append(p%2)
                        p+=1
                        X.append(d)
                        Y.append(p%2)
                else: 
                    X.append(amax)
                    Y.append(p%2)
                    pylab.plot(Y,X,'k')
                    pylab.axvline(x=0,ymin=amin,ymax=amax,linewidth=1,color='w',linestyle='-')
#                    pylab.axhline(y=1.1,xmin=0,xmax=1,linewidth=1,color='w',linestyle='-')
#                    pylab.axvline(y=-.1,xmin=0,xmax=1,linewidth=1,color='w',linestyle='-')
#                    pylab.xlabel("Age (Ma): "+ts) 
                    isign=-1
                    for c in Chrons:
                        off=-.1
                        isign=-1*isign 
                        if isign>0: off=1.05
                        if c[1]>=X[0] and c[1]<X[-1]:
                            pylab.text(c[1]-.2,off,c[0])
                    pylab.axis([-.25,1.25,amax,amin])
        pylab.draw()
        ans=raw_input("Press return to quit  ")
        sys.exit()
    else:
        print "No data points met your criteria - try again"
main()

#!/usr/bin/env python
import pmag,sys,exceptions,pmagplotlib
def main():
    """
    NAME 
        ODP_incplot.py

    DESCRIPTION
        plots various measurements versus core_depth

    SYNTAX
        ODP_incplot.py [command line optins]

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
    dmin,dmax=-1,1e6
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
    XY=[]
    maxInt=-1000
    samples=[]
    for rec in Data:
        if "magic_method_codes" in rec.keys():
            meths=rec["magic_method_codes"].split(":")
            if method in meths: # make sure it is desired lab treatment step
                if float(rec['core_depth'])<dmax and float(rec['core_depth'])>dmin and ('LT-AF-Z' in method and float(rec['treatment_ac_field'])==step) or ('LT-NO' in method and step == 0) or ('LT-T-Z' in method and float(rec['treatment_temp'])==step):
                    XY.append([float(rec['core_depth']),float(rec['measurement_inc'])])
    if len(XY)>0 :
        FIG={'strat':1,'ts':2}
        pmagplotlib.plot_init(FIG['strat'],10,5)
        labels=['Depth below sea floor (m)','Inclination','']
        pmagplotlib.plotSTRAT(FIG['strat'],XY,labels)
        if pTS==1:
            pmagplotlib.plot_init(FIG['ts'],10,5)
            pmagplotlib.plotTS(FIG['ts'],[amin,amax],ts)
    else:
        print "No data points met your criteria - try again"
        sys.exit()
    files,fmt={},'svg'
    for key in FIG.keys():
        files[key]=key+'.'+fmt
    if pmagplotlib.isServer:
        black     = '#000000'
        purple    = '#800080'
        files={}
        files['strat']=xaxis+'_'+yaxis+'_'+fmt
        files['ts']='ts'+fmt
        titles={}
        titles['strat']='Depth/Time Series Plot'
        titles['ts']='Time Series Plot'
        FIG = pmagplotlib.addBorders(FIG,titles,black,purple)
        pmagplotlib.saveP(FIG,files)
    else:
        ans=raw_input(" S[a]ve to save plot, [q]uit without saving:  ")
        if ans=="a": pmagplotlib.saveP(FIG,files)
main()

#!/usr/bin/env python
import sys
import numpy
import matplotlib
if matplotlib.get_backend() != "TKAgg":
  matplotlib.use("TKAgg")

import pmagpy.pmag as pmag
import pmagpy.pmagplotlib as pmagplotlib

def main():
    """
    NAME
        quick_hyst.py

    DESCRIPTION
        makes plots of hysteresis data

    SYNTAX
        quick_hyst.py [command line options]

    OPTIONS
        -h prints help message and quits
        -usr USER:   identify user, default is ""
        -f: specify input file, default is magic_measurements.txt
        -spc SPEC: specify specimen name to plot and quit
        -sav save all plots and quit
        -fmt [png,svg,eps,jpg]
    """
    args=sys.argv
    PLT=1
    plots=0
    user,meas_file="","magic_measurements.txt"
    pltspec=""
    dir_path='.'
    fmt='png'
    verbose=pmagplotlib.verbose
    print 'verbose?', verbose
    version_num=pmag.get_version()
    if '-WD' in args:
        ind=args.index('-WD')
        dir_path=args[ind+1]
    if "-h" in args:
        print main.__doc__
        sys.exit()
    if "-usr" in args:
        ind=args.index("-usr")
        user=args[ind+1]
    if '-f' in args:
        ind=args.index("-f")
        meas_file=args[ind+1]
    if '-sav' in args:
        verbose=0
        plots=1
    if '-spc' in args:
        ind=args.index("-spc")
        pltspec= args[ind+1]
        verbose=0
        plots=1
    if '-fmt' in args:
        ind=args.index("-fmt")
        fmt=args[ind+1]
    meas_file=dir_path+'/'+meas_file
    print 'verbose', verbose
    #
    #
    meas_data,file_type=pmag.magic_read(meas_file)
    if file_type!='magic_measurements':
        print main.__doc__
        print 'bad file'
        sys.exit()
    #
    # initialize some variables
    # define figure numbers for hyst,deltaM,DdeltaM curves
    HystRecs,RemRecs=[],[]
    HDD={}
    HDD['hyst']=1
    pmagplotlib.plot_init(HDD['hyst'],5,5)
    #
    # get list of unique experiment names and specimen names
    #
    experiment_names,sids=[],[]
    hyst_data=pmag.get_dictitem(meas_data,'magic_method_codes','LP-HYS','has') # get all hysteresis data
    for rec in hyst_data:
        if 'er_synthetic_name' in rec.keys() and rec['er_synthetic_name']!="":
            rec['er_specimen_name']=rec['er_synthetic_name']
        if rec['magic_experiment_name'] not in experiment_names:experiment_names.append(rec['magic_experiment_name'])
        if rec['er_specimen_name'] not in sids:sids.append(rec['er_specimen_name'])
        if 'measurement_temp' not in rec.keys(): rec['measurement_temp']='300' # assume room T measurement unless otherwise specified
    #
    k=0
    if pltspec!="":
        k=sids.index(pltspec)
    intlist=['measurement_magnitude','measurement_magn_moment','measurement_magn_volume','measurement_magn_mass']
    while k < len(sids):
        locname,site,sample,synth='','','',''
        s=sids[k]
        hmeths=[]
        if verbose:print s, k+1 , 'out of ',len(sids)
    #
    #
        B,M=[],[] #B,M for hysteresis, Bdcd,Mdcd for irm-dcd data
        spec=pmag.get_dictitem(hyst_data,'er_specimen_name',s,'T') # get all measurements for this specimen
        if 'er_location_name' in spec[0].keys():
            locname=spec[0]['er_location_name']
        if 'er_site_name' in spec[0].keys():
            site=spec[0]['er_site_name']
        if 'er_sample_name' in spec[0].keys():
            sample=spec[0]['er_sample_name']
        if 'er_synthetic_name' in spec[0].keys():
            synth=spec[0]['er_synthetic_name']
        for m in intlist:
            meas_data=pmag.get_dictitem(spec,m,'','F') # get all non-blank data for this specimen
            if len(meas_data)>0: break
        c=['k-','b-','c-','g-','m-','r-','y-']
        cnum=0
        if len(meas_data)>0:
            Temps=[]
            xlab,ylab,title='','',''
            for rec in meas_data: 
                if rec['measurement_temp'] not  in Temps:Temps.append(rec['measurement_temp'])
            for t in Temps:
              print 'working on t: ',t
              t_data=pmag.get_dictitem(meas_data,'measurement_temp',t,'T')
              B,M=[],[]
              for rec in t_data: 
                B.append(float(rec['measurement_lab_field_dc']))
                M.append(float(rec[m]))
    # now plot the hysteresis curve(s)
    #
              if len(B)>0: 
                    B=numpy.array(B)
                    M=numpy.array(M)
                    if t==Temps[-1]:
                        xlab='Field (T)'
                        ylab=m
                        title='Hysteresis: '+s
                    if t==Temps[0]:
                        pmagplotlib.clearFIG(HDD['hyst'])
                    pmagplotlib.plotXY(HDD['hyst'],B,M,sym=c[cnum],xlab=xlab,ylab=ylab,title=title) 
                    pmagplotlib.plotXY(HDD['hyst'],[1.1*B.min(),1.1*B.max()],[0,0],sym='k-',xlab=xlab,ylab=ylab,title=title) 
                    pmagplotlib.plotXY(HDD['hyst'],[0,0],[1.1*M.min(),1.1*M.max()],sym='k-',xlab=xlab,ylab=ylab,title=title) 
                    if verbose:pmagplotlib.drawFIGS(HDD)
                    cnum+=1
                    if cnum==len(c):cnum=0
    #
        files={}
        if plots:
            if pltspec!="":s=pltspec
            files={}
            for key in HDD.keys():
                if synth=='':
                    files[key]="LO:_"+locname+'_SI:_'+site+'_SA:_'+sample+'_SP:_'+s+'_TY:_'+key+'_.'+fmt
                else:
                    files[key]='SY:_'+synth+'_TY:_'+key+'_.'+fmt
            pmagplotlib.saveP(HDD,files)
            if pltspec!="":sys.exit()
        if verbose:
            pmagplotlib.drawFIGS(HDD)
            ans=raw_input("S[a]ve plots, [s]pecimen name, [q]uit, <return> to continue\n ")
            if ans=="a":
                files={}
                for key in HDD.keys():
                    files[key]="LO:_"+locname+'_SI:_'+site+'_SA:_'+sample+'_SP:_'+s+'_TY:_'+key+'_.'+fmt
                pmagplotlib.saveP(HDD,files)
            if ans=='':k+=1
            if ans=="p":
       	        del HystRecs[-1]
    	        k-=1
            if  ans=='q': 
    	        print "Good bye"
    	        sys.exit()
            if ans=='s':
                keepon=1
                specimen=raw_input('Enter desired specimen name (or first part there of): ')
                while keepon==1:
                    try:
                        k =sids.index(specimen)
                        keepon=0
                    except:
                        tmplist=[]
                        for qq in range(len(sids)):
                            if specimen in sids[qq]:tmplist.append(sids[qq])
                        print specimen," not found, but this was: "
                        print tmplist
                        specimen=raw_input('Select one or try again\n ')
                        k =sids.index(specimen)
        else:
            k+=1
        if len(B)==0:
    	    if verbose:print 'skipping this one - no hysteresis data'
       	    k+=1

if __name__ == "__main__":
    main()

#!/usr/bin/env python
from __future__ import division
from __future__ import print_function
from builtins import input
from builtins import str
from builtins import range
from past.utils import old_div
import pmagplotlib
import pmag,sys,exceptions,pylab
pylab.ion()
def main():
    """
    NAME
        core_depthplot.py

    DESCRIPTION
        plots various measurements versus core_depth or age.  plots data flagged as 'FS-SS-C' as discrete samples.

    SYNTAX
        core_depthplot.py [command line optins]

    OPTIONS
        -h prints help message and quits
        -f FILE: specify input magic_measurments format file from magi
        -fsum FILE: specify input LIMS database (IODP) core summary csv file
        -fwig FILE: specify input depth,wiggle to plot, in magic format with sample_core_depth key for depth
        -fsa FILE: specify input er_samples format file from magic for depth
        -fa FILE: specify input er_ages format file from magic for age
              NB: must have either -fsa OR -fa (not both)
        -fsp FILE sym size: specify input zeq_specimen format file from magic, sym and size
              NB: PCAs will have specified color, while fisher means will be white with specified color as the edgecolor
        -fres FILE specify input pmag_results file from magic, sym and size
        -LP [AF,T,ARM,IRM, X] step [in mT,C,mT,mT, mass/vol] to plot
        -S do not plot blanket treatment data (if this is set, you don't need the -LP)
        -sym SYM SIZE, symbol, size for continuous points (e.g., ro 5, bs 10, g^ 10 for red dot, blue square, green triangle), default is blue dot at 5 pt
        -D do not plot declination
        -M do not plot magnetization
        -log  plot magnetization  on a log scale
        -L do not connect dots with a line
        -I do not plot inclination
        -d min max [in m] depth range to plot
        -n normalize by weight in er_specimen table
        -Iex: plot the expected inc at lat - only available for results with lat info in file
        -ts TS amin amax: plot the GPTS for the time interval between amin and amax (numbers in Ma)
           TS: [ck95, gts04, gts12]
        -ds [mbsf,mcd] specify depth scale, mbsf default
        -fmt [svg, eps, pdf, png] specify output format for plot (default: svg)
        -sav save plot silently

     DEFAULTS:
         Measurements file: magic_measurements.txt
         Samples file: er_samples.txt
         NRM step
         Summary file: none
    """
    meas_file='magic_measurements.txt'
    intlist=['measurement_magnitude','measurement_magn_moment','measurement_magn_volume','measurement_magn_mass']
    samp_file='er_samples.txt'
    depth_scale='sample_core_depth'
    wt_file=''
    verbose=pmagplotlib.verbose
    width=10
    sym,size='bo',5
    Ssym,Ssize='cs',5
    method,fmt="LT-NO",'.svg'
    step=0
    pcol=3
    pel=3
    pltD,pltI,pltM,pltL,pltS=1,1,1,1,1
    logit=0
    maxInt=-1000
    minInt=1e10
    maxSuc=-1000
    minSuc=10000
    plotexp,pTS=0,0
    dir_path="."
    sum_file=""
    suc_file=""
    age_file=""
    spc_file=""
    res_file=""
    ngr_file=""
    wig_file=""
    title,location="",""
    if '-WD' in sys.argv:
        ind=sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
    norm=0
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-L' in sys.argv:
        pltL=0
    if '-S' in sys.argv: pltS=0 # don't plot the bulk measurements at all
    if '-D' in sys.argv:
        pltD=0
        pcol-=1
        pel-=1
        width-=2
    if '-I' in sys.argv:
        pltI=0
        pcol-=1
        pel-=1
        width-=2
    if '-M' in sys.argv:
        pltM=0
        pcol-=1
        pel-=1
        width-=2
    if '-log' in sys.argv:logit=1
    if '-ds' in sys.argv and 'mcd' in sys.argv:depth_scale='sample_composite_depth'
    if '-sym' in sys.argv:
        ind=sys.argv.index('-sym')
        sym=sys.argv[ind+1]
        size=float(sys.argv[ind+2])
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        meas_file=sys.argv[ind+1]
    if '-fsa' in sys.argv:
        ind=sys.argv.index('-fsa')
        samp_file=sys.argv[ind+1]
        if '-fa' in sys.argv:
            print(main.__doc__)
            print('only -fsa OR -fa - not both')
            sys.exit()
    elif '-fa' in sys.argv:
        ind=sys.argv.index('-fa')
        age_file=sys.argv[ind+1]
    if '-fsp' in sys.argv:
        ind=sys.argv.index('-fsp')
        spc_file=dir_path+'/'+sys.argv[ind+1]
        spc_sym=sys.argv[ind+2]
        spc_size=float(sys.argv[ind+3])
    if '-fres' in sys.argv:
        ind=sys.argv.index('-fres')
        res_file=dir_path+'/'+sys.argv[ind+1]
        res_sym=sys.argv[ind+2]
        res_size=float(sys.argv[ind+3])
    if '-fwig' in sys.argv:
        ind=sys.argv.index('-fwig')
        wig_file=dir_path+'/'+sys.argv[ind+1]
        pcol+=1
        width+=2
    if '-fsum' in sys.argv:
        ind=sys.argv.index('-fsum')
        sum_file=dir_path+'/'+sys.argv[ind+1]
    if '-fmt' in sys.argv:
        ind=sys.argv.index('-fmt')
        fmt='.'+sys.argv[ind+1]
    if '-sav' in sys.argv:
        plots=1
        verbose=0
    if '-LP' in sys.argv:
        ind=sys.argv.index('-LP')
        meth=sys.argv[ind+1]
        if meth=="AF":
            step=round(float(sys.argv[ind+2])*1e-3,6)
            method='LT-AF-Z'
        elif meth== 'T':
            step=round(float(sys.argv[ind+2])+273,6)
            method='LT-T-Z'
        elif meth== 'ARM':
            method='LT-AF-I'
            step=round(float(sys.argv[ind+2])*1e-3,6)
        elif meth== 'IRM':
            method='LT-IRM'
            step=round(float(sys.argv[ind+2])*1e-3,6)
        elif meth== 'X':
            method='LP-X'
            pcol+=1
            if sys.argv[ind+2]=='mass':
                suc_key='measurement_chi_mass'
            elif sys.argv[ind+2]=='vol':
                suc_key='measurement_chi_volume'
            else:
                print('error in susceptibility units')
                sys.exit()
        else:
           print('method not supported')
           sys.exit()
    if '-n' in sys.argv:
        ind=sys.argv.index('-n')
        wt_file=dir_path+'/'+sys.argv[ind+1]
        norm=1
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
        pTS=1
        pcol+=1
        width+=2
    #
    #
    # get data read in
    meas_file=dir_path+'/'+meas_file
    if age_file=="":
        samp_file=dir_path+'/'+samp_file
        Samps,file_type=pmag.magic_read(samp_file)
    else:
        depth_scale='age'
        age_file=dir_path+'/'+age_file
        Samps,file_type=pmag.magic_read(age_file)
        age_unit=""
    if spc_file!="":Specs,file_type=pmag.magic_read(spc_file)
    if res_file!="":Results,file_type=pmag.magic_read(res_file)
    if norm==1:
        ErSpecs,file_type=pmag.magic_read(wt_file)
        print(len(ErSpecs), ' specimens read in from ',wt_file)
    Cores=[]
    core_depth_key="Top depth cored CSF (m)"
    if sum_file!="":
        input=open(sum_file,'r').readlines()
        if "Core Summary" in input[0]:
            headline=1
        else:
            headline=0
        keys=input[headline].replace('\n','').split(',')
        if "Core Top (m)" in keys:core_depth_key="Core Top (m)"
        if "Core Label" in keys:core_label_key="Core Label"
        if "Core label" in keys:core_label_key="Core label"
        for line in input[2:]:
            if 'TOTALS' not in line:
                CoreRec={}
                for k in range(len(keys)):CoreRec[keys[k]]=line.split(',')[k]
                Cores.append(CoreRec)
        if len(Cores)==0:
            print('no Core depth information available: import core summary file')
            sum_file=""
    Data=[]
    if depth_scale=='sample_core_depth':
        ylab="Depth (mbsf)"
    elif depth_scale=='age':
        ylab="Age"
    else:
        ylab="Depth (mcd)"
    # collect the data for plotting declination
    Depths,Decs,Incs,Ints=[],[],[],[]
    SDepths,SDecs,SIncs,SInts=[],[],[],[]
    SSucs=[]
    samples=[]
    methods,steps,m2=[],[],[]
    if pltS: # plot the bulk measurement data
        Meas,file_type=pmag.magic_read(meas_file)
        meas_key='measurement_magn_moment'
        print(len(Meas), ' measurements read in from ',meas_file)
        for m in intlist: # find the intensity key with data
            meas_data=pmag.get_dictitem(Meas,m,'','F') # get all non-blank data for this specimen
            if len(meas_data)>0:
                meas_key=m
                break
        m1=pmag.get_dictitem(Meas,'magic_method_codes',method,'has') # fish out the desired method code
        if method=='LT-T-Z':
            m2=pmag.get_dictitem(m1,'treatment_temp',str(step),'eval') # fish out the desired step
        elif 'LT-AF' in method:
            m2=pmag.get_dictitem(m1,'treatment_ac_field',str(step),'eval')
        elif 'LT-IRM' in method:
            m2=pmag.get_dictitem(m1,'treatment_dc_field',str(step),'eval')
        elif 'LT-X' in method:
            m2=pmag.get_dictitem(m1,suc_key,'','F')
        if len(m2)>0:
          for rec in m2: # fish out depths and weights
            D=pmag.get_dictitem(Samps,'er_sample_name',rec['er_sample_name'],'T')
            if not D:  # if using an age_file, you may need to sort by site
                D=pmag.get_dictitem(Samps,'er_site_name',rec['er_site_name'],'T')
            depth=pmag.get_dictitem(D,depth_scale,'','F')
            if len(depth)>0:
                if ylab=='Age': ylab=ylab+' ('+depth[0]['age_unit']+')' # get units of ages - assume they are all the same!

                rec['core_depth'] = float(depth[0][depth_scale])
                rec['magic_method_codes'] = rec['magic_method_codes']+':'+depth[0]['magic_method_codes']
                if norm==1:
                    specrecs=pmag.get_dictitem(ErSpecs,'er_specimen_name',rec['er_specimen_name'],'T')
                    specwts=pmag.get_dictitem(specrecs,'specimen_weight',"",'F')
                    if len(specwts)>0:
                        rec['specimen_weight'] = specwts[0]['specimen_weight']
                        Data.append(rec) # fish out data with core_depth and (if needed) weights
                else:
                    Data.append(rec) # fish out data with core_depth and (if needed) weights
                if title=="":
                   pieces=rec['er_sample_name'].split('-')
                   location=rec['er_location_name']
                   title=location

        SData=pmag.sort_diclist(Data,'core_depth')
        for rec in SData: # fish out bulk measurement data from desired depths
            if dmax==-1 or float(rec['core_depth'])<dmax and float(rec['core_depth'])>dmin:
                Depths.append((rec['core_depth']))
                if method=="LP-X":
                    SSucs.append(float(rec[suc_key]))
                else:
                   if pltD==1:Decs.append(float(rec['measurement_dec']))
                   if pltI==1:Incs.append(float(rec['measurement_inc']))
                   if norm==0 and pltM==1:Ints.append(float(rec[meas_key]))
                   if norm==1 and pltM==1:Ints.append(old_div(float(rec[meas_key]),float(rec['specimen_weight'])))
            if len(SSucs)>0:
                maxSuc=max(SSucs)
                minSuc=min(SSucs)
            if len(Ints)>1:
                maxInt=max(Ints)
                minInt=min(Ints)
        if len(Depths)==0:
            print('no bulk measurement data matched your request')
    SpecDepths,SpecDecs,SpecIncs=[],[],[]
    FDepths,FDecs,FIncs=[],[],[]
    if spc_file!="": # add depths to spec data
        print('spec file found')
        BFLs=pmag.get_dictitem(Specs,'magic_method_codes','DE-BFL','has')  # get all the discrete data with best fit lines
        for spec in BFLs:
            if location=="":
               location=spec['er_location_name']
            samp=pmag.get_dictitem(Samps,'er_sample_name',spec['er_sample_name'],'T')
            if len(samp)>0 and depth_scale in list(samp[0].keys()) and samp[0][depth_scale]!="":
              if ylab=='Age': ylab=ylab+' ('+samp[0]['age_unit']+')' # get units of ages - assume they are all the same!
              if dmax==-1 or float(samp[0][depth_scale])<dmax and float(samp[0][depth_scale])>dmin: # filter for depth
                SpecDepths.append(float(samp[0][depth_scale])) # fish out data with core_depth
                SpecDecs.append(float(spec['specimen_dec'])) # fish out data with core_depth
                SpecIncs.append(float(spec['specimen_inc'])) # fish out data with core_depth
            else:
                print('no core_depth found for: ',spec['er_specimen_name'])
        FMs=pmag.get_dictitem(Specs,'magic_method_codes','DE-FM','has')  # get all the discrete data with best fit lines
        for spec in FMs:
            if location=="":
               location=spec['er_location_name']
            samp=pmag.get_dictitem(Samps,'er_sample_name',spec['er_sample_name'],'T')
        if len(samp)>0 and depth_scale in list(samp[0].keys()) and samp[0][depth_scale]!="":
              if ylab=='Age': ylab=ylab+' ('+samp[0]['age_unit']+')' # get units of ages - assume they are all the same!
              if dmax==-1 or float(samp[0][depth_scale])<dmax and float(samp[0][depth_scale])>dmin: # filter for depth
                FDepths.append(float(samp[0][depth_scale]))# fish out data with core_depth
                FDecs.append(float(spec['specimen_dec'])) # fish out data with core_depth
                FIncs.append(float(spec['specimen_inc'])) # fish out data with core_depth
            else:
                print('no core_depth found for: ',spec['er_specimen_name'])
    ResDepths,ResDecs,ResIncs=[],[],[]
    if 'age' in depth_scale: # set y-key
        res_scale='average_age'
    else:
        res_scale='average_height'
    if res_file!="": #creates lists of Result Data
        for res in Results:
            meths=res['magic_method_codes'].split(":")
            if 'DE-FM' in meths:
              if dmax==-1 or float(res[res_scale])<dmax and float(res[res_scale])>dmin: # filter for depth
                ResDepths.append(float(res[res_scale])) # fish out data with core_depth
                ResDecs.append(float(res['average_dec'])) # fish out data with core_depth
                ResIncs.append(float(res['average_inc'])) # fish out data with core_depth
                Susc,Sus_depths=[],[]
    if dmin==-1:
        if len(Depths)>0: dmin,dmax=Depths[0],Depths[-1]
        if len(FDepths)>0: dmin,dmax=Depths[0],Depths[-1]
        if pltS==1 and len(SDepths)>0:
            if SDepths[0]<dmin:dmin=SDepths[0]
            if SDepths[-1]>dmax:dmax=SDepths[-1]
        if len(SpecDepths)>0:
            if min(SpecDepths)<dmin:dmin=min(SpecDepths)
            if max(SpecDepths)>dmax:dmax=max(SpecDepths)
        if len(ResDepths)>0:
            if min(ResDepths)<dmin:dmin=min(ResDepths)
            if max(ResDepths)>dmax:dmax=max(ResDepths)
    if suc_file!="":
        sucdat=open(suc_file,'r').readlines()
        keys=sucdat[0].replace('\n','').split(',') # splits on underscores
        for line in sucdat[1:]:
            SucRec={}
            for k in range(len(keys)):SucRec[keys[k]]=line.split(',')[k]
            if float(SucRec['Top Depth (m)'])<dmax and float(SucRec['Top Depth (m)'])>dmin and SucRec['Magnetic Susceptibility (80 mm)']!="":
                Susc.append(float(SucRec['Magnetic Susceptibility (80 mm)']))
                if Susc[-1]>maxSuc:maxSuc=Susc[-1]
                if Susc[-1]<minSuc:minSuc=Susc[-1]
                Sus_depths.append(float(SucRec['Top Depth (m)']))
    WIG,WIG_depths=[],[]
    if wig_file!="":
        wigdat,file_type=pmag.magic_read(wig_file)
        swigdat=pmag.sort_diclist(wigdat,depth_scale)
        keys=list(wigdat[0].keys())
        for key in keys:
            if key!=depth_scale:
                plt_key=key
                break
        for wig in swigdat:
            if float(wig[depth_scale])<dmax and float(wig[depth_scale])>dmin:
                WIG.append(float(wig[plt_key]))
                WIG_depths.append(float(wig[depth_scale]))
    tint=4.5
    plt=1
    if len(Decs)>0 and len(Depths)>0 or (len(SpecDecs)>0 and len(SpecDepths)>0) or (len(ResDecs)>0 and len(ResDepths)>0) or (len(SDecs)>0 and len(SDepths)>0) or (len(SInts)>0 and len(SDepths)>0) or (len(SIncs)>0 and len(SDepths)>0):
        pylab.figure(1,figsize=(width,8))
        version_num=pmag.get_version()
        pylab.figtext(.02,.01,version_num)
        if pltD==1:
            ax=pylab.subplot(1,pcol,plt)
            if pltL==1:
                pylab.plot(Decs,Depths,'k')
            if len(Decs)>0:
                pylab.plot(Decs,Depths,sym,markersize=size)
            if len(Decs)==0 and pltL==1 and len(SDecs)>0:
                pylab.plot(SDecs,SDepths,'k')
            if len(SDecs)>0:
                pylab.plot(SDecs,SDepths,Ssym,markersize=Ssize)
            if spc_file!="":
                pylab.plot(SpecDecs,SpecDepths,spc_sym,markersize=spc_size)
            if spc_file!="" and len(FDepths)>0:
                pylab.scatter(FDecs,FDepths,marker=spc_sym[-1],edgecolor=spc_sym[0],facecolor='white',s=spc_size**2)
            if res_file!="":
                pylab.plot(ResDecs,ResDepths,res_sym,markersize=res_size)
            if sum_file!="":
                for core in Cores:
                     depth=float(core[core_depth_key])
                     if depth>dmin and depth<dmax:
                        pylab.plot([0,360.],[depth,depth],'b--')
                        if pel==plt:pylab.text(360,depth+tint,core[core_label_key])
            if pel==plt:
                pylab.axis([0,400,dmax,dmin])
            else:
                pylab.axis([0,360.,dmax,dmin])
            pylab.xlabel('Declination')
            pylab.ylabel(ylab)
            plt+=1
            pmagplotlib.delticks(ax) # dec xticks are too crowded otherwise
    if pltI==1:
            pylab.subplot(1,pcol,plt)
            if pltL==1:pylab.plot(Incs,Depths,'k')
            if len(Incs)>0:pylab.plot(Incs,Depths,sym,markersize=size)
            if len(Incs)==0 and pltL==1 and len(SIncs)>0:pylab.plot(SIncs,SDepths,'k')
            if len(SIncs)>0:pylab.plot(SIncs,SDepths,Ssym,markersize=Ssize)
            if spc_file!="" and len(SpecDepths)>0:pylab.plot(SpecIncs,SpecDepths,spc_sym,markersize=spc_size)
            if spc_file!="" and len(FDepths)>0:
                pylab.scatter(FIncs,FDepths,marker=spc_sym[-1],edgecolor=spc_sym[0],facecolor='white',s=spc_size**2)
            if res_file!="":pylab.plot(ResIncs,ResDepths,res_sym,markersize=res_size)
            if sum_file!="":
                for core in Cores:
                     depth=float(core[core_depth_key])
                     if depth>dmin and depth<dmax:
                         if pel==plt:pylab.text(90,depth+tint,core[core_label_key])
                         pylab.plot([-90,90],[depth,depth],'b--')
            pylab.plot([0,0],[dmax,dmin],'k-')
            if pel==plt:
                pylab.axis([-90,110,dmax,dmin])
            else:
                pylab.axis([-90,90,dmax,dmin])
            pylab.xlabel('Inclination')
            pylab.ylabel('')
            plt+=1
    if pltM==1 and len(Ints)>0 or len(SInts)>0:
            pylab.subplot(1,pcol,plt)
            for pow in range(-10,10):
                if maxInt*10**pow>1:break
            if logit==0:
                for k in range(len(Ints)):
                    Ints[k]=Ints[k]*10**pow
                for k in range(len(SInts)):
                    SInts[k]=SInts[k]*10**pow
                if pltL==1 and len(Ints)>0: pylab.plot(Ints,Depths,'k')
                if len(Ints)>0:pylab.plot(Ints,Depths,sym,markersize=size)
                if len(Ints)==0 and pltL==1 and len(SInts)>0:pylab.plot(SInts,SDepths,'k-')
                if len(SInts)>0:pylab.plot(SInts,SDepths,Ssym,markersize=Ssize)
                if sum_file!="":
                    for core in Cores:
                         depth=float(core[core_depth_key])
                         pylab.plot([0,maxInt*10**pow+.1],[depth,depth],'b--')
                         if depth>dmin and depth<dmax:pylab.text(maxInt*10**pow-.2*maxInt*10**pow,depth+tint,core[core_label_key])
                pylab.axis([0,maxInt*10**pow+.1,dmax,dmin])
                if norm==0:
                    pylab.xlabel('%s %i %s'%('Intensity (10^-',pow,' Am^2)'))
                else:
                    pylab.xlabel('%s %i %s'%('Intensity (10^-',pow,' Am^2/kg)'))
            else:
                if pltL==1: pylab.semilogx(Ints,Depths,'k')
                if len(Ints)>0:pylab.semilogx(Ints,Depths,sym,markersize=size)
                if len(Ints)==0 and pltL==1 and len(SInts)>0:pylab.semilogx(SInts,SDepths,'k')
                if len(Ints)==0 and pltL==1 and len(SInts)>0:pylab.semilogx(SInts,SDepths,'k')
                if len(SInts)>0:pylab.semilogx(SInts,SDepths,Ssym,markersize=Ssize)
                if sum_file!="":
                    for core in Cores:
                         depth=float(core[core_depth_key])
                         pylab.semilogx([minInt,maxInt],[depth,depth],'b--')
                         if depth>dmin and depth<dmax:pylab.text(maxInt-.2*maxInt,depth+tint,core[core_label_key])
                pylab.axis([0,maxInt,dmax,dmin])
                if norm==0:
                    pylab.xlabel('Intensity (Am^2)')
                else:
                    pylab.xlabel('Intensity (Am^2/kg)')
            plt+=1
    if suc_file!="" or len(SSucs)>0:
            pylab.subplot(1,pcol,plt)
            if len(Susc)>0:
                if pltL==1:pylab.plot(Susc,Sus_depths,'k')
                if logit==0:pylab.plot(Susc,Sus_depths,sym,markersize=size)
                if logit==1:pylab.semilogx(Susc,Sus_depths,sym,markersize=size)
            if len(SSucs)>0:
                if logit==0:pylab.plot(SSucs,SDepths,sym,markersize=size)
                if logit==1:pylab.semilogx(SSucs,SDepths,sym,markersize=size)
            if sum_file!="":
                for core in Cores:
                     depth=float(core[core_depth_key])
                     if logit==0:pylab.plot([minSuc,maxSuc],[depth,depth],'b--')
                     if logit==1:pylab.semilogx([minSuc,maxSuc],[depth,depth],'b--')
            pylab.axis([minSuc,maxSuc,dmax,dmin])
            pylab.xlabel('Susceptibility')
            plt+=1
    if wig_file!="":
            pylab.subplot(1,pcol,plt)
            pylab.plot(WIG,WIG_depths,'k')
            if sum_file!="":
                for core in Cores:
                     depth=float(core[core_depth_key])
                     pylab.plot([WIG[0],WIG[-1]],[depth,depth],'b--')
            pylab.axis([min(WIG),max(WIG),dmax,dmin])
            pylab.xlabel(plt_key)
            plt+=1
    if pTS==1:
            ax1=pylab.subplot(1,pcol,plt)
            ax1.axis([-.25,1.5,amax,amin])
            plt+=1
            TS,Chrons=pmag.get_ts(ts)
            X,Y,Y2=[0,1],[],[]
            cnt=0
            if amin<TS[1]: # in the Brunhes
                Y=[amin,amin] # minimum age
                Y1=[TS[1],TS[1]] # age of the B/M boundary
                ax1.fill_between(X,Y,Y1,facecolor='black') # color in Brunhes, black
            for d in TS[1:]:
                pol=cnt%2
                cnt+=1
                if d<=amax and d>=amin:
                   ind=TS.index(d)
                   Y=[TS[ind],TS[ind]]
                   Y1=[TS[ind+1],TS[ind+1]]
                   if pol: ax1.fill_between(X,Y,Y1,facecolor='black') # fill in every other time
            ax1.plot([0,1,1,0,0],[amin,amin,amax,amax,amin],'k-')
            ax2=ax1.twinx()
            pylab.ylabel("Age (Ma): "+ts)
            for k in range(len(Chrons)-1):
                c=Chrons[k]
                cnext=Chrons[k+1]
                d=cnext[1]-old_div((cnext[1]-c[1]),3.)
                if d>=amin and d<amax:
                    ax2.plot([1,1.5],[c[1],c[1]],'k-') # make the Chron boundary tick
                    ax2.text(1.05,d,c[0]) #
            ax2.axis([-.25,1.5,amax,amin])
    figname=location+'_m:_'+method+'_core-depthplot'+fmt
    pylab.title(location)
    if verbose:
        pylab.draw()
        ans=input("S[a]ve plot? ")
        if ans=='a':
            pylab.savefig(figname)
            print('Plot saved as ',figname)
    elif plots:
        pylab.savefig(figname)
        print('Plot saved as ',figname)
    sys.exit()
main()

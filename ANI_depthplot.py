#!/usr/bin/env python
import pmag,sys,exceptions,matplotlib,string
matplotlib.use("TkAgg")
import pylab
pylab.ion()
def main():
    """
    NAME 
        ANI_depthplot.py

    DESCRIPTION
        plots tau, V3_inc versus core_depth

    SYNTAX
        ANI_depthplot.py [command line optins]

    OPTIONS
        -h prints help message and quits
        -f FILE: specify input rmag_anisotropy format file from magic
        -fb FILE: specify input magic_measurements format file from magic
        -fsa FILE: specify input er_samples format file from magic 
        -d min max [in m] depth range to plot
        -o plot only oblate specimens with ~vertical minima
     DEFAULTS:
         Anisotropy file: rmag_anisotropy.txt
         Bulk susceptibility file: magic_measurements.txt
         Samples file: er_samples.txt
    """
    fmt='.svg'
    dir_path="./"
    pcol=2
    if '-WD' in sys.argv: 
        ind=sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
    ani_file=dir_path+'/rmag_anisotropy.txt'
    meas_file=dir_path+'/magic_measurements.txt'
    samp_file=dir_path+'/er_samples.txt'
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        ani_file=dir_path+'/'+sys.argv[ind+1]
    if '-fb' in sys.argv:
        ind=sys.argv.index('-fb')
        meas_file=dir_path+'/'+sys.argv[ind+1]
    if '-fsa' in sys.argv:
        ind=sys.argv.index('-fsa')
        samp_file=dir_path+'/'+sys.argv[ind+1]
    if '-fmt' in sys.argv:
        ind=sys.argv.index('-fmt')
        fmt='.'+sys.argv[ind+1]
    dmin,dmax=-1,-1
    if '-d' in sys.argv:
        ind=sys.argv.index('-d')
        dmin=float(sys.argv[ind+1])
        dmax=float(sys.argv[ind+2])
    oblate=0
    if '-o' in sys.argv: oblate=1
    #
    # get data read in
    isbulk=0
    AniData,file_type=pmag.magic_read(ani_file) 
    Samps,file_type=pmag.magic_read(samp_file) 
    Meas,file_type=pmag.magic_read(meas_file) 
    if file_type=='magic_measurements':isbulk=1
    Data=[]
    Bulks=[]
    BulkDepths=[]
    bmin,bmax=1e6,-1e6 
    for rec in AniData:
        for samp in Samps:
            if samp['er_sample_name'].upper()== rec['er_sample_name'].upper() and 'sample_core_depth' in samp.keys() and samp['sample_core_depth']!="":
                rec['core_depth'] = samp['sample_core_depth']
                if dmax==-1 or float(rec['core_depth'])<dmax and float(rec['core_depth'])>dmin: 
                    Data.append(rec) # fish out data with core_depth
                    if isbulk: 
                        thisbulk=[]
                        for meas in Meas:
                            if meas['er_specimen_name']== rec['er_specimen_name'] and 'measurement_chi_volume' in meas.keys() and meas['measurement_chi_volume'].strip()!="" :
                               Bulks.append(1e6*float(meas['measurement_chi_volume']))
                               if Bulks[-1]<bmin:bmin=Bulks[-1]
                               if Bulks[-1]>bmax:bmax=Bulks[-1]
                               BulkDepths.append(float(samp['sample_core_depth']))
    xlab="Depth (m)"
    if len(Data)>0:
        location=Data[0]['er_location_name']
    else:
        print 'no data to plot'
        sys.exit()
    # collect the data for plotting tau and V3_inc
    Depths,Tau1,Tau2,Tau3,V3Incs=[],[],[],[],[]
    tau_min,tau_max=1,0
    if len(Bulks)>0: pcol+=1
    for rec in Data:
        s=[]
        s.append(float(rec['anisotropy_s1']))
        s.append(float(rec['anisotropy_s2']))
        s.append(float(rec['anisotropy_s3']))
        s.append(float(rec['anisotropy_s4']))
        s.append(float(rec['anisotropy_s5']))
        s.append(float(rec['anisotropy_s6']))
        tau,Vdirs=pmag.doseigs(s)
        if Vdirs[2][1]>60 or oblate==0:
            Depths.append(float(rec['core_depth']))
            V3Incs.append(Vdirs[2][1])
            Tau1.append(tau[0])
            Tau2.append(tau[1])
            Tau3.append(tau[2])
            if tau[0]>tau_max:tau_max=tau[0]
            if tau[2]<tau_min:tau_min=tau[2]
    if len(Depths)>0:
        if dmax==-1:
            dmax=max(Depths)
            dmin=min(Depths)
        #dmax=dmax+.05*dmax
        #dmin=dmin-.05*dmax
        pylab.figure(1,figsize=(10,8))
        version_num=pmag.get_version()
        pylab.figtext(.02,.01,version_num)
        pylab.subplot(1,pcol,1)
        pylab.plot(Tau1,Depths,'rs') 
        pylab.plot(Tau2,Depths,'b^') 
        pylab.plot(Tau3,Depths,'ko') 
        pylab.axis([tau_min,tau_max,dmax,dmin])
        pylab.xlabel('Eigenvalues')
        pylab.ylabel('Depth (m)')
        pylab.subplot(1,pcol,2)
        pylab.plot(V3Incs,Depths,'ko') 
        pylab.axis([0,90,dmax,dmin])
        pylab.xlabel('V3 Inclination')
        pylab.title(location)
        if pcol==3:
            pylab.subplot(1,pcol,3)
            pylab.plot(Bulks,BulkDepths,'bo') 
            pylab.axis([bmin-1,bmax+1,dmax,dmin])
            pylab.xlabel('Bulk Susc. (uSI)')
        pylab.draw()
        ans=raw_input("Press return to quit  ")
        sys.exit()
    else:
        print "No data points met your criteria - try again"
main()

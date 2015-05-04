#!/usr/bin/env python
import pmag,sys,exceptions,matplotlib,string
import pmagplotlib
import pylab as pyplot
import numpy as np
# turn interactive mode on
pyplot.ion()


def main():
    """
    NAME 
        ani_depthplot.py

    DESCRIPTION
        plots tau, V3_inc, V1_dec, P and chi versus core_depth

    SYNTAX
        ani_depthplot.py [command line optins]

    OPTIONS
        -h prints help message and quits
        -f FILE: specify input rmag_anisotropy format file from magic
        -fb FILE: specify input magic_measurements format file from magic
        -fsa FILE: specify input er_samples format file from magic 
        -fsum FILE : specify input LIMS database (IODP) core summary csv file
                to print the core names, set lab to 1
        -fa FILE: specify input er_ages format file from magic 
        -d min max [in m] depth range to plot
        -ds [mcd,mbsf], specify depth scale, default is mbsf
        -sav save plot without review
        -fmt specfiy format for figures - default is svg
     DEFAULTS:
         Anisotropy file: rmag_anisotropy.txt
         Bulk susceptibility file: magic_measurements.txt
         Samples file: er_samples.txt
    """
    fmt='.svg'
    dir_path="./"
    pcol=4
    tint=9
    verbose=pmagplotlib.verbose
    plots=0
    age_file=""
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
        if '-fa' in sys.argv:
            print main.__doc__
            print 'only -fsa OR -fa - not both'
            sys.exit()
    elif '-fa' in sys.argv:
        ind=sys.argv.index('-fa')
        age_file=dir_path+"/"+sys.argv[ind+1]
    label=1
    if '-fsum' in sys.argv:
        ind=sys.argv.index('-fsum')
        #label=int(sys.argv[ind+2])
        sum_file=dir_path+'/'+sys.argv[ind+1]
    else:sum_file=""
    if '-fmt' in sys.argv:
        ind=sys.argv.index('-fmt')
        fmt='.'+sys.argv[ind+1]
    dmin,dmax=-1,-1
    if '-d' in sys.argv:
        ind=sys.argv.index('-d')
        dmin=float(sys.argv[ind+1])
        dmax=float(sys.argv[ind+2])
    if '-ds' in sys.argv and 'mcd' in sys.argv: # sets depth scale to meters composite depth (as opposed to meters below sea floor)
        depth_scale='sample_composite_depth'
    elif age_file=="":
        depth_scale='sample_core_depth'
    else:
        depth_scale='age'
    if '-sav' in sys.argv:
        plots=1
        verbose=0
    #
    # get data read in
    isbulk=0 # tests if there are bulk susceptibility measurements
    AniData,file_type=pmag.magic_read(ani_file)  # read in tensor elements
    if age_file=="":
        Samps,file_type=pmag.magic_read(samp_file)  # read in sample depth info from er_sample.txt format file
    else:
        Samps,file_type=pmag.magic_read(age_file)  # read in sample age info from er_ages.txt format file
        age_unit=Samps[0]['age_unit']
    for s in Samps:s['er_sample_name']=s['er_sample_name'].upper() # change to upper case for every sample name
    Meas,file_type=pmag.magic_read(meas_file) 
    if file_type=='magic_measurements':isbulk=1
    Data=[]
    Bulks=[]
    BulkDepths=[]
    for rec in AniData:
        samprecs=pmag.get_dictitem(Samps,'er_sample_name',rec['er_sample_name'].upper(),'T') # look for depth record for this sample
        sampdepths=pmag.get_dictitem(samprecs,depth_scale,'','F') # see if there are non-blank depth data
        if dmax!=-1:
            sampdepths=pmag.get_dictitem(sampdepths,depth_scale,dmax,'max') # fishes out records within depth bounds
            sampdepths=pmag.get_dictitem(sampdepths,depth_scale,dmin,'min')
        if len(sampdepths)>0: # if there are any....
            rec['core_depth'] = sampdepths[0][depth_scale] # set the core depth of this record
            Data.append(rec) # fish out data with core_depth
            if isbulk:  # if there are bulk data
                chis=pmag.get_dictitem(Meas,'er_specimen_name',rec['er_specimen_name'],'T')
                chis=pmag.get_dictitem(chis,'measurement_chi_volume','','F') # get the non-zero values for this specimen
                if len(chis)>0: # if there are any....
                    Bulks.append(1e6*float(chis[0]['measurement_chi_volume'])) # put in microSI
                    BulkDepths.append(float(sampdepths[0][depth_scale]))
    if len(Bulks)>0: # set min and max bulk values
        bmin=min(Bulks)
        bmax=max(Bulks)
    xlab="Depth (m)"
    if len(Data)>0:
        location=Data[0]['er_location_name']
    else:
        print 'no data to plot'
        sys.exit()
    # collect the data for plotting tau  V3_inc and V1_dec
    Depths,Tau1,Tau2,Tau3,V3Incs,P,V1Decs=[],[],[],[],[],[],[]
    F23s=[]
    Axs=[] # collect the plot ids
# START HERE
    if len(Bulks)>0: pcol+=1
    s1=pmag.get_dictkey(Data,'anisotropy_s1','f') # get all the s1 values from Data as floats
    s2=pmag.get_dictkey(Data,'anisotropy_s2','f')
    s3=pmag.get_dictkey(Data,'anisotropy_s3','f')
    s4=pmag.get_dictkey(Data,'anisotropy_s4','f')
    s5=pmag.get_dictkey(Data,'anisotropy_s5','f')
    s6=pmag.get_dictkey(Data,'anisotropy_s6','f')
    nmeas=pmag.get_dictkey(Data,'anisotropy_n','int')
    sigma=pmag.get_dictkey(Data,'anisotropy_sigma','f')
    Depths=pmag.get_dictkey(Data,'core_depth','f')
    #Ss=np.array([s1,s4,s5,s4,s2,s6,s5,s6,s3]).transpose() # make an array
    Ss=np.array([s1,s2,s3,s4,s5,s6]).transpose() # make an array
    #Ts=np.reshape(Ss,(len(Ss),3,-1)) # and re-shape to be n-length array of 3x3 sub-arrays
    for k in range(len(Depths)):
        #tau,Evecs= pmag.tauV(Ts[k]) # get the sorted eigenvalues and eigenvectors
        #v3=pmag.cart2dir(Evecs[2])[1] # convert to inclination of the minimum eigenvector
        fpars=pmag.dohext(nmeas[k]-6,sigma[k],Ss[k])
	V3Incs.append(fpars['v3_inc'])
	V1Decs.append(fpars['v1_dec'])
        Tau1.append(fpars['t1'])
        Tau2.append(fpars['t2'])
        Tau3.append(fpars['t3'])
        P.append(Tau1[-1]/Tau3[-1])
        F23s.append(fpars['F23'])
    if len(Depths)>0:
        if dmax==-1:
            dmax=max(Depths)
            dmin=min(Depths)
        tau_min=1
        for t in Tau3:
            if t>0 and t<tau_min:tau_min=t
        tau_max=max(Tau1)
        #tau_min=min(Tau3)
        P_max=max(P)
        P_min=min(P)
        #dmax=dmax+.05*dmax
        #dmin=dmin-.05*dmax

        main_plot = pyplot.figure(1,figsize=(10,8)) # make the figure
        
        version_num=pmag.get_version()
        pyplot.figtext(.02,.01,version_num) # attach the pmagpy version number
        ax=pyplot.subplot(1,pcol,1) # make the first column
        Axs.append(ax)
        ax.plot(Tau1,Depths,'rs') 
        ax.plot(Tau2,Depths,'b^') 
        ax.plot(Tau3,Depths,'ko')
        if sum_file!="":
            for core in Cores:
                 depth=float(core[core_depth_key])
                 if depth>dmin and depth<dmax:
                    pyplot.plot([0,90],[depth,depth],'b--')
        ax.axis([tau_min,tau_max,dmax,dmin])
        ax.set_xlabel('Eigenvalues')
        if depth_scale=='sample_core_depth':
            ax.set_ylabel('Depth (mbsf)')
        elif depth_scale=='age':
            ax.set_ylabel('Age ('+age_unit+')')
        else:
            ax.set_ylabel('Depth (mcd)')
        ax2=pyplot.subplot(1,pcol,2) # make the second column
        ax2.plot(P,Depths,'rs') 
        ax2.axis([P_min,P_max,dmax,dmin])
        ax2.set_xlabel('P')
        ax2.set_title(location)
        if sum_file!="":
            for core in Cores:
                 depth=float(core[core_depth_key])
                 if depth>dmin and depth<dmax:
                    pyplot.plot([0,90],[depth,depth],'b--')
        Axs.append(ax2)
        ax3=pyplot.subplot(1,pcol,3)
        Axs.append(ax3)
        ax3.plot(V3Incs,Depths,'ko') 
        ax3.axis([0,90,dmax,dmin])
        ax3.set_xlabel('V3 Inclination')
        if sum_file!="":
            for core in Cores:
                 depth=float(core[core_depth_key])
                 if depth>dmin and depth<dmax:
                    pyplot.plot([0,90],[depth,depth],'b--')
        ax4=pyplot.subplot(1,np.abs(pcol),4)
        Axs.append(ax4)
        ax4.plot(V1Decs,Depths,'rs') 
        ax4.axis([0,360,dmax,dmin])
        ax4.set_xlabel('V1 Declination')
        if sum_file!="":
            
            for core in Cores:
                 depth=float(core[core_depth_key])
                 if depth>=dmin and depth<=dmax:
                    pyplot.plot([0,360],[depth,depth],'b--')
                    if pcol==4 and label==1:pyplot.text(360,depth+tint,core[core_label_key])
        #ax5=pyplot.subplot(1,np.abs(pcol),5)
        #Axs.append(ax5)
        #ax5.plot(F23s,Depths,'rs') 
        #bounds=ax5.axis() 
        #ax5.axis([bounds[0],bounds[1],dmax,dmin])
        #ax5.set_xlabel('F_23')
        #ax5.semilogx()
        #if sum_file!="":
        #    for core in Cores:
        #         depth=float(core[core_depth_key])
        #         if depth>=dmin and depth<=dmax:
        #            pyplot.plot([bounds[0],bounds[1]],[depth,depth],'b--')
        #            if pcol==5 and label==1:pyplot.text(bounds[1],depth+tint,core[core_label_key])
        #if pcol==6:
        if pcol==5:
            #ax6=pyplot.subplot(1,pcol,6)
            ax6=pyplot.subplot(1,pcol,5)
            Axs.append(ax6)
            ax6.plot(Bulks,BulkDepths,'bo') 
            ax6.axis([bmin-1,1.1*bmax,dmax,dmin])
            ax6.set_xlabel('Bulk Susc. (uSI)')
            if sum_file!="":
                for core in Cores:
                     depth=float(core[core_depth_key])
                     if depth>=dmin and depth<=dmax:
                        pyplot.plot([0,bmax],[depth,depth],'b--')
                        if label==1:pyplot.text(1.1*bmax,depth+tint,core[core_label_key])
        for x in Axs:
            pmagplotlib.delticks(x) # this makes the x-tick labels more reasonable - they were overcrowded using the defaults
        fig_name = location + '_ani_depthplot.' + fmt
        if verbose:
            pyplot.draw()
            ans=raw_input("S[a]ve plot? Return to quit ")
            if ans=='a':
                pyplot.savefig(figname)
                print 'Plot saved as ',figname
        elif plots:
            pyplot.savefig(figname)
            print 'Plot saved as ',figname
        sys.exit()
           
    else:
        print "No data points met your criteria - try again"
main()

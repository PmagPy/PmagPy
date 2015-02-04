#!/usr/bin/env python
import pmag,sys,exceptions,matplotlib,string,numpy
import pmagplotlib
import pylab
# turn interactive mode on
pylab.ion()


def main():
    """
    NAME 
        ani_depthplot.py

    DESCRIPTION
        plots tau, V3_inc, P and chi versus core_depth

    SYNTAX
        ani_depthplot.py [command line optins]

    OPTIONS
        -h prints help message and quits
        -f FILE: specify input rmag_anisotropy format file from magic
        -fb FILE: specify input magic_measurements format file from magic
        -fsa FILE: specify input er_samples format file from magic 
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
    pcol=3
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
    # collect the data for plotting tau and V3_inc
    Depths,Tau1,Tau2,Tau3,V3Incs,P=[],[],[],[],[],[]
    Axs=[] # collect the plot ids
    if len(Bulks)>0: pcol+=1
    s1=pmag.get_dictkey(Data,'anisotropy_s1','f') # get all the s1 values from Data as floats
    s2=pmag.get_dictkey(Data,'anisotropy_s2','f')
    s3=pmag.get_dictkey(Data,'anisotropy_s3','f')
    s4=pmag.get_dictkey(Data,'anisotropy_s4','f')
    s5=pmag.get_dictkey(Data,'anisotropy_s5','f')
    s6=pmag.get_dictkey(Data,'anisotropy_s6','f')
    Depths=pmag.get_dictkey(Data,'core_depth','f')
    Ss=numpy.array([s1,s4,s5,s4,s2,s6,s5,s6,s3]).transpose() # make an array
    Ts=numpy.reshape(Ss,(len(Ss),3,-1)) # and re-shape to be n-length array of 3x3 sub-arrays
    for k in range(len(Depths)):
        tau,Evecs= pmag.tauV(Ts[k]) # get the sorted eigenvalues and eigenvectors
        v3=pmag.cart2dir(Evecs[2])[1] # convert to inclination of the minimum eigenvector
        V3Incs.append(v3)
        Tau1.append(tau[0])
        Tau2.append(tau[1])
        Tau3.append(tau[2])
        P.append(tau[0]/tau[2])
    if len(Depths)>0:
        if dmax==-1:
            dmax=max(Depths)
            dmin=min(Depths)
        tau_max=max(Tau1)
        tau_min=min(Tau3)
        P_max=max(P)
        P_min=min(P)
        #dmax=dmax+.05*dmax
        #dmin=dmin-.05*dmax
        main_plot = pylab.figure(1,figsize=(10,8)) # make the figure
        version_num=pmag.get_version()
        pylab.figtext(.02,.01,version_num) # attach the pmagpy version number
        ax=pylab.subplot(1,pcol,1) # make the first column
        Axs.append(ax)
        ax.plot(Tau1,Depths,'rs') 
        ax.plot(Tau2,Depths,'b^') 
        ax.plot(Tau3,Depths,'ko') 
        ax.axis([tau_min,tau_max,dmax,dmin])
        ax.set_xlabel('Eigenvalues')
        if depth_scale=='sample_core_depth':
            ax.set_ylabel('Depth (mbsf)')
        elif depth_scale=='age':
            ax.set_ylabel('Age ('+age_unit+')')
        else:
            ax.set_ylabel('Depth (mcd)')
        ax2=pylab.subplot(1,pcol,2) # make the second column
        ax2.plot(P,Depths,'rs') 
        ax2.axis([P_min,P_max,dmax,dmin])
        ax2.set_xlabel('P')
        ax2.set_title(location)
        Axs.append(ax2)
        ax3=pylab.subplot(1,pcol,3)
        Axs.append(ax3)
        ax3.plot(V3Incs,Depths,'ko') 
        ax3.axis([0,90,dmax,dmin])
        ax3.set_xlabel('V3 Inclination')
        if pcol==4:
            ax4=pylab.subplot(1,pcol,4)
            Axs.append(ax4)
            ax4.plot(Bulks,BulkDepths,'bo') 
            ax4.axis([bmin-1,bmax+1,dmax,dmin])
            ax4.set_xlabel('Bulk Susc. (uSI)')
        for x in Axs:pmagplotlib.delticks(x) # this makes the x-tick labels more reasonable - they were overcrowded using the defaults
        figname=location+'_ani-depthplot'+fmt
        if verbose:
            pylab.draw()
            ans=raw_input("S[a]ve plot? Return to quit ")
            if ans=='a':
                pylab.savefig(figname)
                print 'Plot saved as ',figname
        elif plots:
            pylab.savefig(figname)
            print 'Plot saved as ',figname
        sys.exit()
           
    else:
        print "No data points met your criteria - try again"
main()

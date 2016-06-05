#!/usr/bin/env python

# -*- python-indent-offset: 4; -*-

import pandas as pd
import sys
import os
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")

import pmagpy.pmag as pmag
import pmagpy.pmagplotlib as pmagplotlib
import new_builder as nb



def save_redo(SpecRecs,inspec):
    print "Saving changes to specimen file"
    pmag.magic_write(inspec,SpecRecs,'specimens')

def main():
    """
    NAME
        zeq_magic.py

    DESCRIPTION
        reads in magic_measurements formatted file, makes plots of remanence decay
        during demagnetization experiments.  Reads in prior interpretations saved in 
        a pmag_specimens formatted file and  allows re-interpretations of best-fit lines
        and planes and saves (revised or new) interpretations in a pmag_specimens file.  
        interpretations are saved in the coordinate system used. Also allows judicious editting of
        measurements to eliminate "bad" measurements.  These are marked as such in the magic_measurements
        input file.  they are NOT deleted, just ignored. 

    SYNTAX
        zeq_magic.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f  MEASFILE: sets measurements format input file, default: measurements.txt
        -fsp SPECFILE: sets specimens format file with prior interpreations, default: specimens.txt
        -fsa SAMPFILE: sets samples format file with prior interpreations, default: samples.txt
        -Fp PLTFILE: sets filename for saved plot, default is name_type.fmt (where type is zijd, eqarea or decay curve)
        -crd [s,g,t]: sets coordinate system,  g=geographic, t=tilt adjusted, default: specimen coordinate system
        -spc SPEC  plots single specimen SPEC, saves plot with specified format 
              with optional -dir settings and quits
        -dir [L,P,F][beg][end]: sets calculation type for principal component analysis, default is none
             beg: starting step for PCA calculation
             end: ending step for PCA calculation
             [L,P,F]: calculation type for line, plane or fisher mean
             must be used with -spc option
        -fmt FMT: set format of saved plot [png,svg,jpg]
        -A:  suppresses averaging of  replicate measurements, default is to average
        -sav: saves all plots without review
    SCREEN OUTPUT:
        Specimen, N, a95, StepMin, StepMax, Dec, Inc, calculation type

    """
    # initialize some variables
    doave,e,b=1,0,0 # average replicates, initial end and beginning step
    plots,coord=0,'s'
    noorient=0
    version_num=pmag.get_version()
    verbose=pmagplotlib.verbose
    calculation_type,fmt="","svg"
    user,spec_keys,locname="",[],''
    sfile=""
    geo,tilt,ask=0,0,0
    PriorRecs=[] # empty list for prior interpretations
    backup=0
    specimen="" # can skip everything and just plot one specimen with bounds e,b
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    dir_path = pmag.get_named_arg_from_sys("-WD", default_val=os.getcwd())
    meas_file = pmag.get_named_arg_from_sys("-f", default_val="measurements.txt") 
    #full_meas_file=os.path.join(dir_path,meas_file)
    spec_file=pmag.get_named_arg_from_sys("-fsp", default_val="specimens.txt")
    samp_file=pmag.get_named_arg_from_sys("-fsa",default_val="")
    if samp_file!="":sfile='ok'
    samp_file=os.path.join(dir_path,samp_file)
    plot_file=pmag.get_named_arg_from_sys("-Fp",default_val="")
    crd = pmag.get_named_arg_from_sys("-crd", default_val="g")
    if crd == "s":
        coord = "-1"
    elif crd == "t":
        coord = "100"
    else:
        coord = "0"
    fmt = pmag.get_named_arg_from_sys("-fmt", "svg")
    specimen=pmag.get_named_arg_from_sys("-spc",default_val="")
    beg_pca,end_pca,direction_type="","",'L'
    if '-dir' in sys.argv:
        ind=sys.argv.index('-dir')
        direction_type=sys.argv[ind+1]
        beg_pca=int(sys.argv[ind+2])
        end_pca=int(sys.argv[ind+3])
        if direction_type=='L':calculation_type='DE-BFL'
        if direction_type=='P':calculation_type='DE-BFP'
        if direction_type=='F':calculation_type='DE-FM'
    if '-A' in sys.argv: doave=0
    if '-sav' in sys.argv: plots,verbose=1,0
    #
    first_save=1
    fnames = {'measurements': meas_file, 'specimens': spec_file, 'samples': samp_file}
    contribution = nb.Contribution(dir_path, custom_filenames=fnames, read_tables=['measurements', 'specimens', 'samples'])
    meas_container = contribution.tables['measurements']
    meas_data = meas_container.df
    meas_data= meas_data[meas_data['method_codes'].str.contains('LT-NO|LT-AF-Z|LT-T-Z|LT-M-Z')==True] # fish out zero field steps for plotting 
    if 'specimens' in contribution.tables:
        spec_container = contribution.tables['specimens']
        prior_spec_data=spec_container.get_records_for_code('DE-',strict_match=False) # look up all prior directional interpretations
    else:
       	spec_container, prior_spec_data = None, []
    if 'samples' in contribution.tables:
        samp_container = contribution.tables['samples']
        samp_data=samp_container.df
    else:
       	samp_container, samp_data = None, None
    changeM,changeS=0,0 # check if data or interpretations have changed
    #
    # get list of unique specimen names from measurement data
    #
    specimen_names= meas_data.specimen_name.unique()
    # set up new DataFrame for this sessions specimen interpretations
    cols = ['analyst_names', 'aniso_ftest', 'aniso_ftest12', 'aniso_ftest23', 'aniso_s', 'aniso_s_mean', 'aniso_s_n_measurements', 'aniso_s_sigma', 'aniso_s_unit', 'aniso_tilt_correction', 'aniso_type', 'aniso_v1', 'aniso_v2', 'aniso_v3', 'citations', 'description', 'dir_alpha95', 'dir_comp_name', 'dir_dec', 'dir_inc', 'dir_mad_free', 'dir_n_measurements', 'dir_tilt_correction', 'experiment_names', 'geologic_classes', 'geologic_types', 'hyst_bc', 'hyst_bcr', 'hyst_mr_moment', 'hyst_ms_moment', 'int_abs', 'int_b', 'int_b_beta', 'int_b_sigma', 'int_corr', 'int_dang', 'int_drats', 'int_f', 'int_fvds', 'int_gamma', 'int_mad_free', 'int_md', 'int_n_measurements', 'int_n_ptrm', 'int_q', 'int_rsc', 'int_treat_dc_field', 'lithologies', 'meas_step_max', 'meas_step_min', 'meas_step_unit', 'method_codes', 'sample_name', 'software_packages', 'specimen_name']
    dtype = 'specimens'
    data_container = nb.MagicDataFrame(dtype=dtype, columns=cols)
    current_spec_data = data_container.df # this is for current interpretations
    #
    #  set up plots, angle sets X axis to horizontal,  direction_type 'l' is best-fit line
    # direction_type='p' is great circle
    #     
    #
    # draw plots for specimen spec - default is just to step through zijderveld diagrams
    #
    #
    # define figure numbers for equal area, zijderveld,  
    #  and intensity vs. demagnetiztion step respectively
    ZED={}
    ZED['eqarea'],ZED['zijd'],  ZED['demag']=1,2,3 
    pmagplotlib.plot_init(ZED['eqarea'],6,6)
    pmagplotlib.plot_init(ZED['zijd'],6,6)
    pmagplotlib.plot_init(ZED['demag'],6,6)
    save_pca=0
    if specimen=="":
        k = 0
    else:
        k=specimen_names.index(specimen)
    angle,direction_type="",""
    setangle=0
    included_methods=['LT-NO','LT-AF-Z','LT-T-Z','LT-M-Z']
    # let's look at the data now
    while k < len(specimen_names):
        this_specimen=specimen_names[k] # set the current specimen for plotting
        if verbose and  this_specimen!="":print this_specimen, k+1 , 'out of ',len(specimen_names)
        if setangle==0:angle=""
        # create a new specimen record for the interpreation for this specimen
        this_specimen_interpretation={col: "" for col in cols}
        this_specimen_interpretation["analyst_mail_names"]=user
        this_specimen_interpretation['software_packages']=version_num
        this_specimen_interpretation['specimen_name']=version_num
    #
    #  collect info for current_specimen_interpretation dictionary
    #
        this_specimen_measurements= meas_data[meas_data['specimen_name'].str.contains(this_specimen)==True] # fish out this specimen
        if len(this_specimen_measurements)>0:
            units,methods="",""
            meths=this_specimen_measurements.method_codes.tolist()
            for meth in meths:
                for m in meth.split(':'):
                    if m.strip() not in methods and m.strip() in included_methods:
                        methods=methods+':'+m.strip() # make string of methods used
            if 'LT-AF-Z' in methods: units='T' # units include tesla
            if 'LT-T-Z' in methods: units=units+":K" # units include kelvin
            if 'LT-M-Z' in methods: units=units+':J' # units include joules
            units=units.strip(':') # strip off extra colons
            methods=methods.strip(':') # strip off extra colons
            this_specimen_interpretation["method_codes"]= methods
            this_specimen_interpretation["meas_step_unit"]= units
    #
    # find prior interpretation
    #
            if len(current_spec_data)==0: # no interpretations yet for this session
                print "no current interpretation"
                beg_pca,end_pca="",""
                calculation_type=""
                if len(prior_spec_data)!=0:
                  if verbose: print "    looking up previous interpretations..."
                  prior_specimen_interpretations= prior_spec_data[prior_spec_data['specimen_name'].str.contains(this_specimen)==True] # fish out prior interpretations 
                  prior_spec_data= prior_spec_data[prior_spec_data['specimen_name'].str.contains(this_specimen)==False] # remove them from prior recs 
         # get the ones that meet the current coordinate system
                  print 'prior: ',prior_specimen_interpretations['meas_step_min']
                  #    beg_pca=prior_specimen_interpretations.meas_step_min
                  #    end_pca=prior_specimen_interpretations.meas_step_max
                  #    print beg_pca,end_pca,prior_specimen_interpretations.tilt_correction
                  raw_input()
            else:
                 print current_spec_data
        else:
             print "no data"
             raw_input()
        raw_input('Ready for next specimen')
        k+=1

if __name__ == "__main__":
    main()

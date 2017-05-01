#!/usr/bin/env python
from __future__ import division
from __future__ import print_function
from builtins import input
from builtins import range
from past.utils import old_div
import sys
import matplotlib
if matplotlib.get_backend() != "TKAgg":
  matplotlib.use("TKAgg")

import pmagpy.pmagplotlib as pmagplotlib
import pmagpy.pmag as pmag

def main():
    """
    NAME
        hysteresis_magic.py

    DESCRIPTION
        calculates hystereis parameters and saves them in rmag_hystereis format file
        makes plots if option selected

    SYNTAX
        hysteresis_magic.py [command line options]

    OPTIONS
        -h prints help message and quits
        -usr USER:   identify user, default is ""
        -f: specify input file, default is agm_measurements.txt
        -fh: specify rmag_hysteresis.txt input file
        -F: specify output file, default is rmag_hysteresis.txt
        -P: do not make the plots
        -spc SPEC: specify specimen name to plot and quit
        -sav save all plots and quit
        -fmt [png,svg,eps,jpg]
    """
    args=sys.argv
    PLT=1
    plots=0
    user,meas_file,rmag_out,rmag_file="","agm_measurements.txt","rmag_hysteresis.txt",""
    pltspec=""
    dir_path='.'
    fmt='svg'
    verbose=pmagplotlib.verbose
    version_num=pmag.get_version()
    if '-WD' in args:
        ind=args.index('-WD')
        dir_path=args[ind+1]
    if "-h" in args:
        print(main.__doc__)
        sys.exit()
    if "-usr" in args:
        ind=args.index("-usr")
        user=args[ind+1]
    if '-f' in args:
        ind=args.index("-f")
        meas_file=args[ind+1]
    if '-F' in args:
        ind=args.index("-F")
        rmag_out=args[ind+1]
    if '-fh' in args:
        ind=args.index("-fh")
        rmag_file=args[ind+1]
        rmag_file=dir_path+'/'+rmag_file
    if '-P' in args:
        PLT=0
        irm_init,imag_init=-1,-1
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
    rmag_out=dir_path+'/'+rmag_out
    meas_file=dir_path+'/'+meas_file
    rmag_rem=dir_path+"/rmag_remanence.txt"
    #
    #
    meas_data,file_type=pmag.magic_read(meas_file)
    if file_type!='magic_measurements':
        print(main.__doc__)
        print('bad file')
        sys.exit()
    #
    # initialize some variables
    # define figure numbers for hyst,deltaM,DdeltaM curves
    HystRecs,RemRecs=[],[]
    HDD={}
    if verbose:
        if verbose and PLT:print("Plots may be on top of each other - use mouse to place ")
    if PLT:
        HDD['hyst'],HDD['deltaM'],HDD['DdeltaM']=1,2,3
        pmagplotlib.plot_init(HDD['DdeltaM'],5,5)
        pmagplotlib.plot_init(HDD['deltaM'],5,5)
        pmagplotlib.plot_init(HDD['hyst'],5,5)
        imag_init=0
        irm_init=0
    else:
        HDD['hyst'],HDD['deltaM'],HDD['DdeltaM'],HDD['irm'],HDD['imag']=0,0,0,0,0
    #
    if rmag_file!="":hyst_data,file_type=pmag.magic_read(rmag_file)
    #
    # get list of unique experiment names and specimen names
    #
    experiment_names,sids=[],[]
    for rec in meas_data:
      meths=rec['magic_method_codes'].split(':')
      methods=[]
      for meth in meths:
        methods.append(meth.strip())
      if 'LP-HYS' in methods:
        if 'er_synthetic_name' in list(rec.keys()) and rec['er_synthetic_name']!="":
            rec['er_specimen_name']=rec['er_synthetic_name']
        if rec['magic_experiment_name'] not in experiment_names:experiment_names.append(rec['magic_experiment_name'])
        if rec['er_specimen_name'] not in sids:sids.append(rec['er_specimen_name'])
    #
    k=0
    locname=''
    if pltspec!="":
        k=sids.index(pltspec)
        print(sids[k])
    while k < len(sids):
        s=sids[k]
        if verbose and PLT:print(s, k+1 , 'out of ',len(sids))
    #
    #
        B,M,Bdcd,Mdcd=[],[],[],[] #B,M for hysteresis, Bdcd,Mdcd for irm-dcd data
        Bimag,Mimag=[],[] #Bimag,Mimag for initial magnetization curves
        first_dcd_rec,first_rec,first_imag_rec=1,1,1
        for rec in  meas_data:
            methcodes=rec['magic_method_codes'].split(':')
            meths=[]
            for meth in methcodes:
                meths.append(meth.strip())
            if rec['er_specimen_name']==s and "LP-HYS" in meths:
                B.append(float(rec['measurement_lab_field_dc']))
                M.append(float(rec['measurement_magn_moment']))
                if first_rec==1:
                    e=rec['magic_experiment_name']
                    HystRec={}
                    first_rec=0
                    if "er_location_name" in list(rec.keys()):
                        HystRec["er_location_name"]=rec["er_location_name"]
                        locname=rec['er_location_name'].replace('/','-')
                    if "er_sample_name" in list(rec.keys()):HystRec["er_sample_name"]=rec["er_sample_name"]
                    if "er_site_name" in list(rec.keys()):HystRec["er_site_name"]=rec["er_site_name"]
                    if "er_synthetic_name" in list(rec.keys()) and rec['er_synthetic_name']!="":
                        HystRec["er_synthetic_name"]=rec["er_synthetic_name"]
                    else:
                        HystRec["er_specimen_name"]=rec["er_specimen_name"]
            if rec['er_specimen_name']==s and "LP-IRM-DCD" in meths:
                Bdcd.append(float(rec['treatment_dc_field']))
                Mdcd.append(float(rec['measurement_magn_moment']))
                if first_dcd_rec==1:
                    RemRec={}
                    irm_exp=rec['magic_experiment_name']
                    first_dcd_rec=0
                    if "er_location_name" in list(rec.keys()):RemRec["er_location_name"]=rec["er_location_name"]
                    if "er_sample_name" in list(rec.keys()):RemRec["er_sample_name"]=rec["er_sample_name"]
                    if "er_site_name" in list(rec.keys()):RemRec["er_site_name"]=rec["er_site_name"]
                    if "er_synthetic_name" in list(rec.keys()) and rec['er_synthetic_name']!="":
                        RemRec["er_synthetic_name"]=rec["er_synthetic_name"]
                    else:
                        RemRec["er_specimen_name"]=rec["er_specimen_name"]
            if rec['er_specimen_name']==s and "LP-IMAG" in meths:
                if first_imag_rec==1:
                    imag_exp=rec['magic_experiment_name']
                    first_imag_rec=0
                Bimag.append(float(rec['measurement_lab_field_dc']))
                Mimag.append(float(rec['measurement_magn_moment']))
    #
    # now plot the hysteresis curve
    #
        if len(B)>0:
            hmeths=[]
            for meth in meths: hmeths.append(meth)
            hpars=pmagplotlib.plotHDD(HDD,B,M,e)
            if verbose and PLT:pmagplotlib.drawFIGS(HDD)
    #
    # get prior interpretations from hyst_data
            if rmag_file!="":
                hpars_prior={}
                for rec in hyst_data:
                    if rec['magic_experiment_names']==e:
                        if rec['hysteresis_bcr'] !="" and rec['hysteresis_mr_moment']!="":
                            hpars_prior['hysteresis_mr_moment']=rec['hysteresis_mr_moment']
                            hpars_prior['hysteresis_ms_moment']=rec['hysteresis_ms_moment']
                            hpars_prior['hysteresis_bc']=rec['hysteresis_bc']
                            hpars_prior['hysteresis_bcr']=rec['hysteresis_bcr']
                            break
                if verbose:pmagplotlib.plotHPARS(HDD,hpars_prior,'ro')
            else:
                if verbose:pmagplotlib.plotHPARS(HDD,hpars,'bs')
                HystRec['hysteresis_mr_moment']=hpars['hysteresis_mr_moment']
                HystRec['hysteresis_ms_moment']=hpars['hysteresis_ms_moment']
                HystRec['hysteresis_bc']=hpars['hysteresis_bc']
                HystRec['hysteresis_bcr']=hpars['hysteresis_bcr']
                HystRec['hysteresis_xhf']=hpars['hysteresis_xhf']
                HystRec['magic_experiment_names']=e
                HystRec['magic_software_packages']=version_num
                if hpars["magic_method_codes"] not in hmeths:hmeths.append(hpars["magic_method_codes"])
                methods=""
                for meth in hmeths:
                    methods=methods+meth.strip()+":"
                HystRec["magic_method_codes"]=methods[:-1]
                HystRec["er_citation_names"]="This study"
                HystRecs.append(HystRec)
    #
        if len(Bdcd)>0:
            rmeths=[]
            for meth in meths: rmeths.append(meth)
            if verbose and PLT:print('plotting IRM')
            if irm_init==0:
                HDD['irm']=5
                pmagplotlib.plot_init(HDD['irm'],5,5)
                irm_init=1
            rpars=pmagplotlib.plotIRM(HDD['irm'],Bdcd,Mdcd,irm_exp)
            RemRec['remanence_mr_moment']=rpars['remanence_mr_moment']
            RemRec['remanence_bcr']=rpars['remanence_bcr']
            RemRec['magic_experiment_names']=irm_exp
            if rpars["magic_method_codes"] not in meths:meths.append(rpars["magic_method_codes"])
            methods=""
            for meth in rmeths:
                methods=methods+meth.strip()+":"
            RemRec["magic_method_codes"]=methods[:-1]
            RemRec["er_citation_names"]="This study"
            RemRecs.append(RemRec)
        else:
            if irm_init:pmagplotlib.clearFIG(HDD['irm'])
        if len(Bimag)>0:
            if verbose:print('plotting initial magnetization curve')
# first normalize by Ms
            Mnorm=[]
            for m in Mimag: Mnorm.append(old_div(m,float(hpars['hysteresis_ms_moment'])))
            if imag_init==0:
                HDD['imag']=4
                pmagplotlib.plot_init(HDD['imag'],5,5)
                imag_init=1
            pmagplotlib.plotIMAG(HDD['imag'],Bimag,Mnorm,imag_exp)
        else:
            if imag_init:pmagplotlib.clearFIG(HDD['imag'])
    #
        files={}
        if plots:
            if pltspec!="":s=pltspec
            files={}
            for key in list(HDD.keys()):
                files[key]=locname+'_'+s+'_'+key+'.'+fmt
            pmagplotlib.saveP(HDD,files)
            if pltspec!="":sys.exit()
        if verbose and PLT:
            pmagplotlib.drawFIGS(HDD)
            ans=input("S[a]ve plots, [s]pecimen name, [q]uit, <return> to continue\n ")
            if ans=="a":
                files={}
                for key in list(HDD.keys()):
                    files[key]=locname+'_'+s+'_'+key+'.'+fmt
                pmagplotlib.saveP(HDD,files)
            if ans=='':k+=1
            if ans=="p":
                del HystRecs[-1]
                k-=1
            if  ans=='q':
                print("Good bye")
                sys.exit()
            if ans=='s':
                keepon=1
                specimen=input('Enter desired specimen name (or first part there of): ')
                while keepon==1:
                    try:
                        k =sids.index(specimen)
                        keepon=0
                    except:
                        tmplist=[]
                        for qq in range(len(sids)):
                            if specimen in sids[qq]:tmplist.append(sids[qq])
                        print(specimen," not found, but this was: ")
                        print(tmplist)
                        specimen=input('Select one or try again\n ')
                        k =sids.index(specimen)
        else:
            k+=1
        if len(B)==0 and len(Bdcd)==0:
            if verbose:print('skipping this one - no hysteresis data')
            k+=1
    if rmag_out=="" and ans=='s' and verbose:
        really=input(" Do you want to overwrite the existing rmag_hystersis.txt file? 1/[0] ")
        if really=="":
            print('i thought not - goodbye')
            sys.exit()
        rmag_out="rmag_hysteresis.txt"
    if len(HystRecs)>0:
        pmag.magic_write(rmag_out,HystRecs,"rmag_hysteresis")
        if verbose:print("hysteresis parameters saved in ",rmag_out)
    if len(RemRecs)>0:
        pmag.magic_write(rmag_rem,RemRecs,"rmag_remanence")
        if verbose:print("remanence parameters saved in ",rmag_rem)

if __name__ == "__main__":
    main()

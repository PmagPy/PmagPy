#!/usr/bin/env python
from __future__ import print_function
from builtins import input
import sys
import matplotlib
if matplotlib.get_backend() != "TKAgg":
  matplotlib.use("TKAgg")

import pmagpy.pmagplotlib as pmagplotlib
import pmagpy.pmag as pmag
def main():
    """
    NAME
        lnp_magic.py

    DESCRIPTION
       makes equal area projections site by site
         from pmag_specimen formatted file with
         Fisher confidence ellipse using McFadden and McElhinny (1988)
         technique for combining lines and planes

    SYNTAX
        lnp_magic [command line options]

    INPUT
       takes magic formatted pmag_specimens file
    
    OUPUT
        prints site_name n_lines n_planes K alpha95 dec inc R

    OPTIONS
        -h prints help message and quits
        -f FILE: specify input file, default is 'pmag_specimens.txt'
        -crd [s,g,t]: specify coordinate system, [s]pecimen, [g]eographic, [t]ilt adjusted
                default is specimen
        -fmt [svg,png,jpg] format for plots, default is svg
        -sav save plots and quit
        -P: do not plot
        -F FILE, specify output file of dec, inc, alpha95 data for plotting with plotdi_a and plotdi_e
        -exc use criteria in pmag_criteria.txt
    """
    dir_path='.'
    FIG={} # plot dictionary
    FIG['eqarea']=1 # eqarea is figure 1
    in_file,plot_key,coord='pmag_specimens.txt','er_site_name',"-1"
    out_file=""
    fmt,plt,plot='svg',1,0
    Crits=""
    M,N,acutoff,kcutoff=180.,1,180.,0.
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-WD' in sys.argv:
        ind=sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
    if '-f' in sys.argv:
        ind=sys.argv.index("-f")
        in_file=sys.argv[ind+1]
    if '-exc' in sys.argv:
        Crits,file_type=pmag.magic_read(dir_path+'/pmag_criteria.txt')
        for crit in Crits:
            if 'specimen_mad' in crit:   M=float(crit['specimen_mad'])
            if 'specimen_n' in crit:   N=float(crit['specimen_n'])
            if 'site_alpha95' in crit: acutoff=float(crit['site_alpha95'])
            if 'site_k' in crit: kcutoff=float(crit['site_k'])
    if '-F' in sys.argv:
        ind=sys.argv.index("-F")
        out_file=sys.argv[ind+1]
        out=open(dir_path+'/'+out_file,'w')
    if '-crd' in sys.argv:
        ind=sys.argv.index("-crd")
        crd=sys.argv[ind+1]
        if crd=='s':coord="-1"
        if crd=='g':coord="0"
        if crd=='t':coord="100"
    if '-fmt' in sys.argv:
        ind=sys.argv.index("-fmt")
        fmt=sys.argv[ind+1]
    if '-P' in sys.argv:plt=0
    if '-sav' in sys.argv:plot=1
# 
    in_file=dir_path+'/'+in_file
    Specs,file_type=pmag.magic_read(in_file)
    if file_type!='pmag_specimens':
        print('Error opening file')
        sys.exit()
    sitelist=[]
    for rec in Specs:
        if rec['er_site_name'] not in sitelist: sitelist.append(rec['er_site_name'])
    sitelist.sort()
    if plt==1:
        EQ={} 
        EQ['eqarea']=1
        pmagplotlib.plot_init(EQ['eqarea'],4,4)
    for site in sitelist:
        print(site)
        data=[]
        for spec in Specs:
           if 'specimen_tilt_correction' not in list(spec.keys()):spec['specimen_tilt_correction']='-1' # assume unoriented
           if spec['er_site_name']==site:
              if 'specimen_mad' not in list(spec.keys()) or spec['specimen_mad']=="":
                   if 'specimen_alpha95' in list(spec.keys()) and spec['specimen_alpha95']!="":
                       spec['specimen_mad']=spec['specimen_alpha95']
                   else:
                       spec['specimen_mad']='180'
              if spec['specimen_tilt_correction']==coord and float(spec['specimen_mad'])<=M and float(spec['specimen_n'])>=N: 
                   rec={}
                   for key in list(spec.keys()):rec[key]=spec[key]
                   rec["dec"]=float(spec['specimen_dec'])
                   rec["inc"]=float(spec['specimen_inc'])
                   rec["tilt_correction"]=spec['specimen_tilt_correction']
                   data.append(rec)
        if len(data)>2:
            fpars=pmag.dolnp(data,'specimen_direction_type')
            print("Site lines planes  kappa   a95   dec   inc")
            print(site, fpars["n_lines"], fpars["n_planes"], fpars["K"], fpars["alpha95"], fpars["dec"], fpars["inc"], fpars["R"])
            if out_file!="":
                if float(fpars["alpha95"])<=acutoff and float(fpars["K"])>=kcutoff:
                    out.write('%s %s %s\n'%(fpars["dec"],fpars['inc'],fpars['alpha95']))
            print('% tilt correction: ',coord)
            if plt==1:
                files={}
                files['eqarea']=site+'_'+crd+'_'+'eqarea'+'.'+fmt
                pmagplotlib.plotLNP(EQ['eqarea'],site,data,fpars,'specimen_direction_type')
                if plot==0:
                    pmagplotlib.drawFIGS(EQ)
                    ans=input("s[a]ve plot, [q]uit, <return> to continue:\n ")
                    if ans=="a":
                        pmagplotlib.saveP(EQ,files)
                    if ans=="q": sys.exit()
                else:
                    pmagplotlib.saveP(EQ,files)
        else:
            print('skipping site - not enough data with specified coordinate system')

if __name__ == "__main__":
    main()

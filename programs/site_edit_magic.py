#!/usr/bin/env python
from __future__ import print_function
from builtins import input
from builtins import range
import sys


import pmagpy.pmag as pmag
import pmagpy.pmagplotlib as pmagplotlib

def main():
    """
    NAME
        site_edit_magic.py

    DESCRIPTION
       makes equal area projections site by site
         from pmag_specimens.txt file with
         Fisher confidence ellipse using McFadden and McElhinny (1988)
         technique for combining lines and planes
         allows testing and reject specimens for bad orientations

    SYNTAX
        site_edit_magic.py [command line options]

    OPTIONS
       -h: prints help and quits
       -f: specify pmag_specimen format file, default is pmag_specimens.txt
       -fsa: specify er_samples.txt file
       -exc: use existing pmag_criteria.txt file
       -N: reset all sample flags to good
    
    OUPUT
       edited er_samples.txt file

    """
    dir_path='.'
    FIG={} # plot dictionary
    FIG['eqarea']=1 # eqarea is figure 1
    in_file='pmag_specimens.txt'
    sampfile='er_samples.txt'
    out_file=""
    fmt,plot='svg',1
    Crits=""
    M,N=180.,1
    repeat=''
    renew=0
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-WD' in sys.argv:
        ind=sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
    if '-f' in sys.argv:
        ind=sys.argv.index("-f")
        in_file=sys.argv[ind+1]
    if '-fsa' in sys.argv:
        ind=sys.argv.index("-fsa")
        sampfile=sys.argv[ind+1]
    if '-exc' in sys.argv:
        Crits,file_type=pmag.magic_read(dir_path+'/pmag_criteria.txt')
        for crit in Crits:
            if crit['pmag_criteria_code']=='DE-SPEC':
                M=float(crit['specimen_mad'])
                N=float(crit['specimen_n'])
    if '-fmt' in sys.argv:
        ind=sys.argv.index("-fmt")
        fmt=sys.argv[ind+1]
    if '-N' in sys.argv: renew=1
# 
    if in_file[0]!="/":in_file=dir_path+'/'+in_file
    if sampfile[0]!="/":sampfile=dir_path+'/'+sampfile
    crd='s'
    Specs,file_type=pmag.magic_read(in_file)
    if file_type!='pmag_specimens':
        print(' bad pmag_specimen input file')
        sys.exit()
    Samps,file_type=pmag.magic_read(sampfile)
    if file_type!='er_samples':
        print(' bad er_samples input file')
        sys.exit()
    SO_methods=[]
    for rec in Samps:
       if 'sample_orientation_flag' not in list(rec.keys()): rec['sample_orientation_flag']='g'
       if 'sample_description' not in list(rec.keys()): rec['sample_description']=''
       if renew==1:
          rec['sample_orientation_flag']='g'
          description=rec['sample_description']
          if '#' in description:
               newdesc=""
               c=0
               while description[c]!='#' and c<len(description)-1: # look for first pound sign
                   newdesc=newdesc+description[c]
                   c+=1
               while description[c]=='#': 
                   c+=1# skip first set of pound signs
               while description[c]!='#':c+=1 # find second set of pound signs
               while description[c]=='#' and c<len(description)-1:c+=1 # skip second set of pound signs
               while c<len(description)-1: # look for first pound sign
                   newdesc=newdesc+description[c]
                   c+=1
               rec['sample_description']=newdesc # edit out old comment about orientations
       if "magic_method_codes" in rec:
           methlist=rec["magic_method_codes"]
           for meth in methlist.split(":"):
               if "SO" in meth.strip() and "SO-POM" not in meth.strip():
                   if meth.strip() not in SO_methods: SO_methods.append(meth.strip())
    pmag.magic_write(sampfile,Samps,'er_samples')
    SO_priorities=pmag.set_priorities(SO_methods,0)
    sitelist=[]
    for rec in Specs:
        if rec['er_site_name'] not in sitelist: sitelist.append(rec['er_site_name'])
    sitelist.sort()
    EQ={} 
    EQ['eqarea']=1
    pmagplotlib.plot_init(EQ['eqarea'],5,5)
    k=0
    while k<len(sitelist):
        site=sitelist[k]
        print(site)
        data=[]
        ThisSiteSpecs=pmag.get_dictitem(Specs,'er_site_name',site,'T')
        ThisSiteSpecs=pmag.get_dictitem(ThisSiteSpecs,'specimen_tilt_correction','-1','T') # get all the unoriented data
        for spec in ThisSiteSpecs:
                if spec['specimen_mad']!="" and spec['specimen_n']!="" and float(spec['specimen_mad'])<=M and float(spec['specimen_n'])>=N: 
# good spec, now get orientation....
                    redo,p=1,0
                    if len(SO_methods)<=1:
                        az_type=SO_methods[0]
                        orient=pmag.find_samp_rec(spec["er_sample_name"],Samps,az_type)
                        redo=0
                    while redo==1:
                        if p>=len(SO_priorities):
                            print("no orientation data for ",spec['er_sample_name'])
                            orient["sample_azimuth"]=""
                            orient["sample_dip"]=""
                            redo=0
                        else:
                            az_type=SO_methods[SO_methods.index(SO_priorities[p])]
                            orient=pmag.find_samp_rec(spec["er_sample_name"],Samps,az_type)
                            if orient["sample_azimuth"]  !="":
                                redo=0
                        p+=1
                    if orient['sample_azimuth']!="":
                        rec={}
                        for key in list(spec.keys()):rec[key]=spec[key]
                        rec['dec'],rec['inc']=pmag.dogeo(float(spec['specimen_dec']),float(spec['specimen_inc']),float(orient['sample_azimuth']),float(orient['sample_dip']))
                        rec["tilt_correction"]='1'
                        crd='g'
                        rec['sample_azimuth']=orient['sample_azimuth']
                        rec['sample_dip']=orient['sample_dip']
                        data.append(rec)
        if len(data)>2:
            print('specimen, dec, inc, n_meas/MAD,| method codes ')
            for i  in range(len(data)):
                print('%s: %7.1f %7.1f %s / %s | %s' % (data[i]['er_specimen_name'], data[i]['dec'], data[i]['inc'], data[i]['specimen_n'], data[i]['specimen_mad'], data[i]['magic_method_codes']))

            fpars=pmag.dolnp(data,'specimen_direction_type')
            print("\n Site lines planes  kappa   a95   dec   inc")
            print(site, fpars["n_lines"], fpars["n_planes"], fpars["K"], fpars["alpha95"], fpars["dec"], fpars["inc"], fpars["R"])
            if out_file!="":
                if float(fpars["alpha95"])<=acutoff and float(fpars["K"])>=kcutoff:
                    out.write('%s %s %s\n'%(fpars["dec"],fpars['inc'],fpars['alpha95']))
            pmagplotlib.plotLNP(EQ['eqarea'],site,data,fpars,'specimen_direction_type')
            pmagplotlib.drawFIGS(EQ)
            if k!=0 and repeat!='y':
                ans=input("s[a]ve plot, [q]uit, [e]dit specimens, [p]revious site, <return> to continue:\n ")
            elif k==0 and repeat!='y':
                ans=input("s[a]ve plot, [q]uit, [e]dit specimens, <return> to continue:\n ")
            if ans=="p": k-=2
            if ans=="a":
                files={}
                files['eqarea']=site+'_'+crd+'_eqarea'+'.'+fmt
                pmagplotlib.saveP(EQ,files)
            if ans=="q": sys.exit()
            if ans=="e" and Samps==[]:
                print("can't edit samples without orientation file, sorry")
            elif ans=="e": 
#                k-=1
                testspec=input("Enter name of specimen to check: ")
                for spec in data:
                    if spec['er_specimen_name']==testspec:
# first test wrong direction of drill arrows (flip drill direction in opposite direction and re-calculate d,i
                        d,i=pmag.dogeo(float(spec['specimen_dec']),float(spec['specimen_inc']),float(spec['sample_azimuth'])-180.,-float(spec['sample_dip']))
                        XY=pmag.dimap(d,i)
                        pmagplotlib.plotXY(EQ['eqarea'],[XY[0]],[XY[1]],sym='g^')
# first test wrong end of compass (take az-180.)
                        d,i=pmag.dogeo(float(spec['specimen_dec']),float(spec['specimen_inc']),float(spec['sample_azimuth'])-180.,float(spec['sample_dip']))
                        XY=pmag.dimap(d,i)
                        pmagplotlib.plotXY(EQ['eqarea'],[XY[0]],[XY[1]],sym='kv')
# did the sample spin in the hole?  
# now spin around specimen's z
                        X_up,Y_up,X_d,Y_d=[],[],[],[]
                        for incr in range(0,360,5):
                            d,i=pmag.dogeo(float(spec['specimen_dec'])+incr,float(spec['specimen_inc']),float(spec['sample_azimuth']),float(spec['sample_dip']))
                            XY=pmag.dimap(d,i)
                            if i>=0:
                                X_d.append(XY[0])
                                Y_d.append(XY[1])
                            else:
                                X_up.append(XY[0])
                                Y_up.append(XY[1])
                        pmagplotlib.plotXY(EQ['eqarea'],X_d,Y_d,sym='b.')
                        pmagplotlib.plotXY(EQ['eqarea'],X_up,Y_up,sym='c.')
                        pmagplotlib.drawFIGS(EQ)
                        break
                print("Triangle: wrong arrow for drill direction.")
                print("Delta: wrong end of compass.")
                print("Small circle:  wrong mark on sample. [cyan upper hemisphere]")
                deleteme=input("Mark this sample as bad? y/[n]  ")
                if deleteme=='y':
                    reason=input("Reason: [1] broke, [2] wrong drill direction, [3] wrong compass direction, [4] bad mark, [5] displaced block [6] other ")
                    if reason=='1':
                       description=' sample broke while drilling'
                    if reason=='2':
                       description=' wrong drill direction '
                    if reason=='3':
                       description=' wrong compass direction '
                    if reason=='4':
                       description=' bad mark in field'
                    if reason=='5':
                       description=' displaced block'
                    if reason=='6':
                       description=input('Enter brief reason for deletion:   ')
                    for samp in Samps:
                        if samp['er_sample_name']==spec['er_sample_name']:
                            samp['sample_orientation_flag']='b'
                            samp['sample_description']=samp['sample_description']+' ## direction deleted because: '+description+'##' # mark description
                    pmag.magic_write(sampfile,Samps,'er_samples')
                repeat=input("Mark another sample, this site? y/[n]  ")
                if repeat=='y': k-=1
        else:
            print('skipping site - not enough data with specified coordinate system')
        k+=1 
    print("sample flags stored in ",sampfile)

if __name__ == "__main__":
    main()

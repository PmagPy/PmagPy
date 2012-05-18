#!/usr/bin/env python
#
def save(ANIS,fmt,title):
  files={}
  for key in ANIS.keys():
      files[key]=title+'_'+'aniso'+'_'+key+'.'+fmt 
  pmagplotlib.saveP(ANIS,files)

import sys,pmag,math,pmagplotlib
def main():
    """
    NAME
        aniso_magic.py

    DESCRIPTION
        plots anisotropy data with either bootstrap or hext ellipses
    
    SYNTAX
        aniso_magic.py [-h] [command line options]
    OPTIONS 
        -h plots help message and quits
        -usr USER: set the user name
        -f AFILE, specify rmag_anisotropy formatted file for input
        -F RFILE, specify rmag_results formatted file for output
        -x Hext [1963]
        -B DON'T do bootstrap
        -par Tauxe [1998] parametric bootstrap
        -v plot bootstrap eigenvectors instead of ellipses
        -sit plot by site instead of entire file
        -crd [s,g,t] coordinate system, default is specimen (g=geographic, t=tilt corrected)
        -P don't make any plots - just make rmag_results table
        -sav don't make the rmag_results table - just save all the plots
        -fmt [svg, png, jpg] format for output images
     
    DEFAULTS  
       AFILE:  rmag_anisotropy.txt
       RFILE:  rmag_results.txt
       plot bootstrap ellipses of Constable & Tauxe [1987]
    NOTES
       minor axis: circles
       major axis: triangles
       principal axis: squares
       directions are plotted on the lower hemisphere
       for bootstrapped eigenvector components: Xs: blue, Ys: red, Zs: black
"""
#
    dir_path="."
    version_num=pmag.get_version()
    verbose=pmagplotlib.verbose
    args=sys.argv
    ipar,ihext,ivec,iboot,imeas,isite,iplot,vec=0,0,0,1,1,0,1,0
    hpars,bpars=[],[]
    CS,crd='-1','s'
    fmt='svg'
    ResRecs=[]
    orlist=[]
    outfile,comp,Dir,gtcirc,PDir='rmag_results.txt',0,[],0,[]
    infile='rmag_anisotropy.txt'
    if "-h" in args:
        print main.__doc__
        sys.exit()
    if '-WD' in args:
        ind=args.index('-WD')
        dir_path=args[ind+1]
    if '-usr' in args:
        ind=args.index('-usr')
        user=args[ind+1]
    else:
        user=""
    if '-B' in args:iboot=0
    if '-par' in args:ipar=1
    if '-x' in args:ihext=1
    if '-v' in args:ivec=1
    if '-sit' in args:isite=1
    if '-P' in args:iplot=0
    if '-f' in args:
        ind=args.index('-f')
        infile=args[ind+1]
    if '-F' in args:
        ind=args.index('-F')
        outfile=args[ind+1]
    if '-crd' in sys.argv:
        ind=sys.argv.index('-crd')
        crd=sys.argv[ind+1]
        if crd=='g':CS='0'
        if crd=='t': CS='100'
    if '-fmt' in args:
        ind=args.index('-fmt')
        fmt=args[ind+1]
    if '-sav' in args:
        plots=1
        verbose=0
    else:
        plots=0
#
# set up plots
#
    infile=dir_path+'/'+infile
    outfile=dir_path+'/'+outfile
    ANIS={}
    initcdf,inittcdf=0,0
    ANIS['data'],ANIS['conf']=1,2
    if iboot==1: 
        ANIS['tcdf']=3
        if iplot==1:
            inittcdf=1
            pmagplotlib.plot_init(ANIS['tcdf'],5,5)
        if comp==1:
            if iplot==1:
                initcdf=1
                ANIS['vxcdf'],ANIS['vycdf'],ANIS['vzcdf']=4,5,6
                pmagplotlib.plot_init(ANIS['vxcdf'],5,5)
                pmagplotlib.plot_init(ANIS['vycdf'],5,5)
                pmagplotlib.plot_init(ANIS['vzcdf'],5,5)
    if iplot==1:
        pmagplotlib.plot_init(ANIS['conf'],5,5)
        pmagplotlib.plot_init(ANIS['data'],5,5)
# read in the data
    data,ifiletype=pmag.magic_read(infile)
    for rec in data:  # find all the orientation systems
        if 'anisotropy_tilt_correction' not in rec.keys():rec['anisotropy_tilt_correction']='-1'
        if rec['anisotropy_tilt_correction'] not in orlist: 
            orlist.append(rec['anisotropy_tilt_correction'])
    if CS not in orlist:
        if len(orlist)>0:
            CS=orlist[0]
        else:
            CS='-1'   
        if CS=='-1':crd='s'
        if CS=='0':crd='g'
        if CS=='100':crd='t'
        if verbose:print "desired coordinate system not available, using available: ",crd
    if isite==1:
        sitelist=[]
        for rec in data:
            if rec['er_site_name'] not in sitelist:sitelist.append(rec['er_site_name']) 
        sitelist.sort()  
        plt=len(sitelist)
    else:plt=1
    k=0
    while k<plt:
      sdata,Ss=[],[] # list of S format data
      Locs,Sites,Samples,Specimens,Cits=[],[],[],[],[]
      PDir,Dir=[],[]
      if isite==0:
          sdata=data
          title='All'
      else:
          site=sitelist[k]
          title=site
          for rec in data:
              if rec['er_site_name']==site:sdata.append(rec) 
      if CS=="-1":title=title+'_'+crd 
      if CS=="0":title=title+'_'+crd 
      if CS=="100":title=title+'_'+crd 
      anitypes=[]
      for rec in sdata:
        if rec["anisotropy_tilt_correction"]==CS:
            if rec['anisotropy_type'] not in anitypes:anitypes.append(rec['anisotropy_type'])
            if rec['er_location_name'] not in Locs:Locs.append(rec['er_location_name'])
            if rec['er_site_name'] not in Sites:Sites.append(rec['er_site_name'])
            if rec['er_sample_name'] not in Samples:Samples.append(rec['er_sample_name'])
            if rec['er_specimen_name'] not in Specimens:Specimens.append(rec['er_specimen_name'])
            if rec['er_citation_names'] not in Cits:Cits.append(rec['er_citation_names'])
            s=[]
            s.append(float(rec["anisotropy_s1"]))
            s.append(float(rec["anisotropy_s2"]))
            s.append(float(rec["anisotropy_s3"]))
            s.append(float(rec["anisotropy_s4"]))
            s.append(float(rec["anisotropy_s5"]))
            s.append(float(rec["anisotropy_s6"]))
            if s[0]<=1.0:Ss.append(s) # protect against crap
            tau,Vdirs=pmag.doseigs(s)
            ResRec={}
            ResRec['er_location_names']=rec['er_location_name']
            ResRec['er_citation_names']=rec['er_citation_names']
            ResRec['er_site_names']=rec['er_site_name']
            ResRec['er_sample_names']=rec['er_sample_name']
            ResRec['er_specimen_names']=rec['er_specimen_name']
            ResRec['rmag_result_name']=rec['er_specimen_name']+":"+rec['anisotropy_type']
            ResRec["er_analyst_mail_names"]=user
            ResRec["tilt_correction"]=CS
            ResRec["anisotropy_type"]=rec['anisotropy_type']
            ResRec["anisotropy_v1_dec"]='%7.1f'%(Vdirs[0][0])
            ResRec["anisotropy_v2_dec"]='%7.1f'%(Vdirs[1][0])
            ResRec["anisotropy_v3_dec"]='%7.1f'%(Vdirs[2][0])
            ResRec["anisotropy_v1_inc"]='%7.1f'%(Vdirs[0][1])
            ResRec["anisotropy_v2_inc"]='%7.1f'%(Vdirs[1][1])
            ResRec["anisotropy_v3_inc"]='%7.1f'%(Vdirs[2][1])
            ResRec["anisotropy_t1"]='%10.8f'%(tau[0])
            ResRec["anisotropy_t2"]='%10.8f'%(tau[1])
            ResRec["anisotropy_t3"]='%10.8f'%(tau[2])
            ResRecs.append(ResRec) 
      if len(Ss)>1:
          bpars,hpars=pmagplotlib.plotANIS(ANIS,Ss,iboot,ihext,ivec,ipar,title,iplot,comp,vec,Dir)
          if verbose:pmagplotlib.drawFIGS(ANIS)
          if len(PDir)>0:
              pmagplotlib.plotC(ANIS['data'],PDir,90.,'g')

              pmagplotlib.plotC(ANIS['conf'],PDir,90.,'g')
          ResRec['er_location_names']=pmag.makelist(Locs)
          if plots==1:
              if ResRec['er_location_names']!="":
                  title=ResRec['er_location_names']+'_'+title
              save(ANIS,fmt,title)
              sys.exit()
          ResRec={}
          ResRec['er_citation_names']=pmag.makelist(Cits)
          ResRec['er_site_names']=pmag.makelist(Sites)
          ResRec['er_sample_names']=pmag.makelist(Samples)
          ResRec['er_specimen_names']=pmag.makelist(Specimens)
          ResRec['rmag_result_name']=pmag.makelist(Sites)+":"+pmag.makelist(anitypes)
          ResRec["er_analyst_mail_names"]=user
          ResRec["tilt_correction"]=CS
          if isite=="0":ResRec['result_description']="Study average using coordinate system: "+ CS
          if isite=="1":ResRec['result_description']="Site average using coordinate system: " +CS
          if hpars!=[] and ihext==1:
              HextRec={}
              for key in ResRec.keys():HextRec[key]=ResRec[key]   # copy over stuff 
              HextRec["anisotropy_v1_dec"]='%7.1f'%(hpars["v1_dec"])
              HextRec["anisotropy_v2_dec"]='%7.1f'%(hpars["v2_dec"])
              HextRec["anisotropy_v3_dec"]='%7.1f'%(hpars["v3_dec"])
              HextRec["anisotropy_v1_inc"]='%7.1f'%(hpars["v1_inc"])
              HextRec["anisotropy_v2_inc"]='%7.1f'%(hpars["v2_inc"])
              HextRec["anisotropy_v3_inc"]='%7.1f'%(hpars["v3_inc"])
              HextRec["anisotropy_t1"]='%10.8f'%(hpars["t1"])
              HextRec["anisotropy_t2"]='%10.8f'%(hpars["t2"])
              HextRec["anisotropy_t3"]='%10.8f'%(hpars["t3"])
              HextRec["anisotropy_hext_F"]='%7.1f '%(hpars["F"])
              HextRec["anisotropy_hext_F12"]='%7.1f '%(hpars["F12"])
              HextRec["anisotropy_hext_F23"]='%7.1f '%(hpars["F23"])
              HextRec["anisotropy_v1_eta_semi_angle"]='%7.1f '%(hpars["e12"])
              HextRec["anisotropy_v1_eta_dec"]='%7.1f '%(hpars["v2_dec"])
              HextRec["anisotropy_v1_eta_inc"]='%7.1f '%(hpars["v2_inc"])
              HextRec["anisotropy_v1_zeta_semi_angle"]='%7.1f '%(hpars["e13"])
              HextRec["anisotropy_v1_zeta_dec"]='%7.1f '%(hpars["v3_dec"])
              HextRec["anisotropy_v1_zeta_inc"]='%7.1f '%(hpars["v3_inc"])
              HextRec["anisotropy_v2_eta_semi_angle"]='%7.1f '%(hpars["e12"])
              HextRec["anisotropy_v2_eta_dec"]='%7.1f '%(hpars["v1_dec"])
              HextRec["anisotropy_v2_eta_inc"]='%7.1f '%(hpars["v1_inc"])
              HextRec["anisotropy_v2_zeta_semi_angle"]='%7.1f '%(hpars["e23"])
              HextRec["anisotropy_v2_zeta_dec"]='%7.1f '%(hpars["v3_dec"])
              HextRec["anisotropy_v2_zeta_inc"]='%7.1f '%(hpars["v3_inc"])
              HextRec["anisotropy_v3_eta_semi_angle"]='%7.1f '%(hpars["e12"])
              HextRec["anisotropy_v3_eta_dec"]='%7.1f '%(hpars["v1_dec"])
              HextRec["anisotropy_v3_eta_inc"]='%7.1f '%(hpars["v1_inc"])
              HextRec["anisotropy_v3_zeta_semi_angle"]='%7.1f '%(hpars["e23"])
              HextRec["anisotropy_v3_zeta_dec"]='%7.1f '%(hpars["v2_dec"])
              HextRec["anisotropy_v3_zeta_inc"]='%7.1f '%(hpars["v2_inc"])
              HextRec["magic_method_codes"]='LP-AN:AE-H'
              if verbose:
                  print "Hext Statistics: "
                  print " tau_i, V_i_D, V_i_I, V_i_zeta, V_i_zeta_D, V_i_zeta_I, V_i_eta, V_i_eta_D, V_i_eta_I"
                  print HextRec["anisotropy_t1"], HextRec["anisotropy_v1_dec"], HextRec["anisotropy_v1_inc"], HextRec["anisotropy_v1_eta_semi_angle"], HextRec["anisotropy_v1_eta_dec"], HextRec["anisotropy_v1_eta_inc"], HextRec["anisotropy_v1_zeta_semi_angle"], HextRec["anisotropy_v1_zeta_dec"], HextRec["anisotropy_v1_zeta_inc"]
                  print HextRec["anisotropy_t2"],HextRec["anisotropy_v2_dec"], HextRec["anisotropy_v2_inc"], HextRec["anisotropy_v2_eta_semi_angle"], HextRec["anisotropy_v2_eta_dec"], HextRec["anisotropy_v2_eta_inc"], HextRec["anisotropy_v2_zeta_semi_angle"], HextRec["anisotropy_v2_zeta_dec"], HextRec["anisotropy_v2_zeta_inc"]
                  print HextRec["anisotropy_t3"], HextRec["anisotropy_v3_dec"], HextRec["anisotropy_v3_inc"], HextRec["anisotropy_v3_eta_semi_angle"], HextRec["anisotropy_v3_eta_dec"], HextRec["anisotropy_v3_eta_inc"], HextRec["anisotropy_v3_zeta_semi_angle"], HextRec["anisotropy_v3_zeta_dec"], HextRec["anisotropy_v3_zeta_inc"]
              HextRec['magic_software_packages']=version_num
              ResRecs.append(HextRec)
          if bpars!=[]:
              BootRec={}
              for key in ResRec.keys():BootRec[key]=ResRec[key]   # copy over stuff 
              BootRec["anisotropy_v1_dec"]='%7.1f'%(bpars["v1_dec"])
              BootRec["anisotropy_v2_dec"]='%7.1f'%(bpars["v2_dec"])
              BootRec["anisotropy_v3_dec"]='%7.1f'%(bpars["v3_dec"])
              BootRec["anisotropy_v1_inc"]='%7.1f'%(bpars["v1_inc"])
              BootRec["anisotropy_v2_inc"]='%7.1f'%(bpars["v2_inc"])
              BootRec["anisotropy_v3_inc"]='%7.1f'%(bpars["v3_inc"])
              BootRec["anisotropy_t1"]='%10.8f'%(bpars["t1"])
              BootRec["anisotropy_t2"]='%10.8f'%(bpars["t2"])
              BootRec["anisotropy_t3"]='%10.8f'%(bpars["t3"])
              BootRec["anisotropy_v1_eta_inc"]='%7.1f '%(bpars["v1_eta_inc"])
              BootRec["anisotropy_v1_eta_dec"]='%7.1f '%(bpars["v1_eta_dec"])
              BootRec["anisotropy_v1_eta_semi_angle"]='%7.1f '%(bpars["v1_eta"])
              BootRec["anisotropy_v1_zeta_inc"]='%7.1f '%(bpars["v1_zeta_inc"])
              BootRec["anisotropy_v1_zeta_dec"]='%7.1f '%(bpars["v1_zeta_dec"])
              BootRec["anisotropy_v1_zeta_semi_angle"]='%7.1f '%(bpars["v1_zeta"])
              BootRec["anisotropy_v2_eta_inc"]='%7.1f '%(bpars["v2_eta_inc"])
              BootRec["anisotropy_v2_eta_dec"]='%7.1f '%(bpars["v2_eta_dec"])
              BootRec["anisotropy_v2_eta_semi_angle"]='%7.1f '%(bpars["v2_eta"])
              BootRec["anisotropy_v2_zeta_inc"]='%7.1f '%(bpars["v2_zeta_inc"])
              BootRec["anisotropy_v2_zeta_dec"]='%7.1f '%(bpars["v2_zeta_dec"])
              BootRec["anisotropy_v2_zeta_semi_angle"]='%7.1f '%(bpars["v2_zeta"])
              BootRec["anisotropy_v3_eta_inc"]='%7.1f '%(bpars["v3_eta_inc"])
              BootRec["anisotropy_v3_eta_dec"]='%7.1f '%(bpars["v3_eta_dec"])
              BootRec["anisotropy_v3_eta_semi_angle"]='%7.1f '%(bpars["v3_eta"])
              BootRec["anisotropy_v3_zeta_inc"]='%7.1f '%(bpars["v3_zeta_inc"])
              BootRec["anisotropy_v3_zeta_dec"]='%7.1f '%(bpars["v3_zeta_dec"])
              BootRec["anisotropy_v3_zeta_semi_angle"]='%7.1f '%(bpars["v3_zeta"])
              BootRec["anisotropy_hext_F"]=''
              BootRec["anisotropy_hext_F12"]=''
              BootRec["anisotropy_hext_F23"]=''
              BootRec["magic_method_codes"]='LP-AN:AE-H:AE-BS' # regular bootstrap
              if ipar==1:BootRec["magic_method_codes"]='LP-AN:AE-H:AE-BS-P' # parametric bootstrap
              if verbose:
                  print "Boostrap Statistics: "
                  print " tau_i, V_i_D, V_i_I, V_i_zeta, V_i_zeta_D, V_i_zeta_I, V_i_eta, V_i_eta_D, V_i_eta_I"
                  print BootRec["anisotropy_t1"], BootRec["anisotropy_v1_dec"], BootRec["anisotropy_v1_inc"], BootRec["anisotropy_v1_eta_semi_angle"], BootRec["anisotropy_v1_eta_dec"], BootRec["anisotropy_v1_eta_inc"], BootRec["anisotropy_v1_zeta_semi_angle"], BootRec["anisotropy_v1_zeta_dec"], BootRec["anisotropy_v1_zeta_inc"]
                  print BootRec["anisotropy_t2"],BootRec["anisotropy_v2_dec"], BootRec["anisotropy_v2_inc"], BootRec["anisotropy_v2_eta_semi_angle"], BootRec["anisotropy_v2_eta_dec"], BootRec["anisotropy_v2_eta_inc"], BootRec["anisotropy_v2_zeta_semi_angle"], BootRec["anisotropy_v2_zeta_dec"], BootRec["anisotropy_v2_zeta_inc"]
                  print BootRec["anisotropy_t3"], BootRec["anisotropy_v3_dec"], BootRec["anisotropy_v3_inc"], BootRec["anisotropy_v3_eta_semi_angle"], BootRec["anisotropy_v3_eta_dec"], BootRec["anisotropy_v3_eta_inc"], BootRec["anisotropy_v3_zeta_semi_angle"], BootRec["anisotropy_v3_zeta_dec"], BootRec["anisotropy_v3_zeta_inc"]
              BootRec['magic_software_packages']=version_num
              ResRecs.append(BootRec)
          k+=1
          goon=1
          while goon==1 and iplot==1 and verbose: 
              if iboot==1: print "compare with [d]irection "
              print " plot [g]reat circle,  change [c]oord. system, change [e]llipse calculation,  s[a]ve plots, [q]uit "
              if isite==1: print "  [p]revious, [s]ite, [q]uit, <return> for next "
              ans=raw_input("")
              if ans=="q":
                 sys.exit()
              if ans=="e":
                 iboot,ipar,ihext,ivec=1,0,0,0
                 e=raw_input("Do Hext Statistics  1/[0]: ")
                 if e=="1":ihext=1  
                 e=raw_input("Suppress bootstrap 1/[0]: ")
                 if e=="1":iboot=0  
                 if iboot==1:
                     e=raw_input("Parametric bootstrap 1/[0]: ")
                     if e=="1":ipar=1  
                     e=raw_input("Plot bootstrap eigenvectors:  1/[0]: ")
                     if e=="1":ivec=1
                     if iplot==1:
                         if inittcdf==0:
                             ANIS['tcdf']=3
                             pmagplotlib.plot_init(ANIS['tcdf'],5,5)
                             inittcdf=1
                 bpars,hpars=pmagplotlib.plotANIS(ANIS,Ss,iboot,ihext,ivec,ipar,title,iplot,comp,vec,Dir)
                 print 'you may have to click on the figure to refresh'
              if ans=="c":
                  print "Current Coordinate system is: "
                  if CS=='-1':print " Specimen"
                  if CS=='0':print " Geographic"
                  if CS=='100':print " Tilt corrected"
                  key=raw_input(" Enter desired coordinate system: [s]pecimen, [g]eographic, [t]ilt corrected ")
                  if key=='s':CS='-1'
                  if key=='g':CS='0'
                  if key=='t': CS='100'
                  if CS not in orlist:
                      if len(orlist)>0:
                          CS=orlist[0]
                      else:
                          CS='-1'   
                      if CS=='-1':crd='s'
                      if CS=='0':crd='g'
                      if CS=='100':crd='t'
                      print "desired coordinate system not available, using available: ",crd
                  k-=1
                  goon=0
              if ans=="":
                  if isite==1:
                      goon=0
                  else:
                      print "Good bye "
                      sys.exit()
              if ans=='d':
                  if initcdf==0:
                      initcdf=1
                      ANIS['vxcdf'],ANIS['vycdf'],ANIS['vzcdf']=4,5,6
                      pmagplotlib.plot_init(ANIS['vxcdf'],5,5)
                      pmagplotlib.plot_init(ANIS['vycdf'],5,5)
                      pmagplotlib.plot_init(ANIS['vzcdf'],5,5)
                  Dir,comp=[],1
                  print """ 
                      Input: Vi D I to  compare  eigenvector Vi with direction D/I
                             where Vi=1: principal
                                   Vi=2: major
                                   Vi=3: minor
                                   D= declination of comparison direction
                                   I= inclination of comparison direction"""
                  con=1
                  while con==1:
                      try:
                          vdi=raw_input("Vi D I: ").split()
                          vec=int(vdi[0])-1
                          Dir.append(float(vdi[1]))
                          Dir.append(float(vdi[2]))
                          Dir.append(1.)
                          con=0
                      except IndexError:
                          print " Incorrect entry, try again " 
                  bpars,hpars=pmagplotlib.plotANIS(ANIS,Ss,iboot,ihext,ivec,ipar,title,iplot,comp,vec,Dir)
                  Dir,comp=[],0
              if ans=='g':
                  con,cnt=1,0
                  while con==1:
                      try:
                          print " Input:  input pole to great circle ( D I) to  plot a great circle:   "
                          di=raw_input(" D I: ").split()
                          PDir=[]
                          PDir.append(float(di[0]))
                          PDir.append(float(di[1]))
                          con=0
                      except:
                          cnt+=1
                          if cnt<10:
                              print " enter the dec and inc of the pole on one line "
                          else:
                              print "ummm - you are doing something wrong - i give up"
                              sys.exit()
                  pmagplotlib.plotC(ANIS['data'],PDir,90.,'g')
                  pmagplotlib.plotC(ANIS['conf'],PDir,90.,'g')
              if ans=="p": 
                  k-=2
                  goon=0
              if ans=="q": 
                  k=plt
                  goon=0
              if ans=="s":
                  keepon=1
                  site=raw_input(" print site or part of site desired: ")
                  while keepon==1:
                      try:
                          k=sitelist.index(site)
                          keepon=0
                      except:
                          tmplist=[]
                          for qq in range(len(sitelist)):
                              if site in sitelist[qq]:tmplist.append(sitelist[qq])
                          print site," not found, but this was: "
                          print tmplist
                          site=raw_input('Select one or try again\n ')
                          k=sitelist.index(site)
                  goon,ans=0,""
              if ans=="a":
                  save(ANIS,fmt)
                  goon=0
      else:
          if verbose:print 'skipping plot - not enough data points'
          k+=1 
#   put rmag_results stuff here
    if plots==0:
        if len(ResRecs)>0:
            pmag.magic_write(outfile,ResRecs,'rmag_results')
        if verbose:print "Anisotropy results saved in ",outfile
    if verbose:
        print " Good bye "
#
main()

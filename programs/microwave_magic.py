#!/usr/bin/env python
import sys

from pmag_env import set_env
if not set_env.isServer:
    import pmagpy.nlt as nlt
import pmagpy.pmag as pmag
import pmagpy.pmagplotlib as pmagplotlib

# initialize some variables
def save_redo(SpecRecs,inspec):
    pmag.magic_write(inspec,SpecRecs,'pmag_specimens')

def main():
    """
    NAME
        microwave_magic.py
    
    DESCRIPTION
        plots microwave paleointensity data, allowing interactive setting of bounds.
        Saves and reads interpretations
        from a pmag_specimen formatted table, default: microwave_specimens.txt

    SYNTAX 
        microwave_magic.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f MEAS, set magic_measurements input file
        -fsp PRIOR, set pmag_specimen prior interpretations file
        -fcr CRIT, set criteria file for grading.  
        -fmt [svg,png,jpg], format for images - default is svg
        -sav,  saves plots with out review (default format)
        -spc SPEC, plots single specimen SPEC, saves plot with specified format
            with optional -b bounds adn quits
        -b BEG END: sets  bounds for calculation
           BEG: starting step for slope calculation
           END: ending step for slope calculation
        
    DEFAULTS
        MEAS: magic_measurements.txt
        CRIT: NONE
        PRIOR: microwave_specimens.txt
  
    OUTPUT 
        figures:
            ALL:  numbers refer to temperature steps in command line window
            1) Arai plot:  closed circles are zero-field first/infield
                           open circles are infield first/zero-field
                           triangles are pTRM checks
                           squares are pTRM tail checks
                           VDS is vector difference sum
                           diamonds are bounds for interpretation
            2) Zijderveld plot:  closed (open) symbols are X-Y (X-Z) planes
                                 X rotated to NRM direction
            3) (De/Re)Magnetization diagram:
                           circles are NRM remaining
                           squares are pTRM gained
        command line window:
            list is: temperature step numbers, power (J), Dec, Inc, Int (units of magic_measuements)
                     list of possible commands: type letter followed by return to select option
                     saving of plots creates .svg format files with specimen_name, plot type as name
    """ 
#
#   initializations
#
    meas_file,critout,inspec="magic_measurements.txt","","microwave_specimens.txt"
    inlt=0
    version_num=pmag.get_version()
    Tinit,DCZ,field,first_save=0,0,-1,1
    user,comment="",''
    ans,specimen,recnum,start,end=0,0,0,0,0
    plots,pmag_out,samp_file,style=0,"","","svg"
    fmt='.'+style
#
# default acceptance criteria
#
    accept_keys=['specimen_int_ptrm_n','specimen_md','specimen_fvds','specimen_b_beta','specimen_dang','specimen_drats','specimen_Z']
    accept={}
    accept['specimen_int_ptrm_n']=2
    accept['specimen_md']=10
    accept['specimen_fvds']=0.35
    accept['specimen_b_beta']=.1
    accept['specimen_int_mad']=7
    accept['specimen_dang']=10
    accept['specimen_drats']=10
    accept['specimen_Z']=10
#
# parse command line options
#
    spc,BEG,END="","",""
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        meas_file=sys.argv[ind+1]
    if '-fsp' in sys.argv:
        ind=sys.argv.index('-fsp')
        inspec=sys.argv[ind+1]
    if '-fcr' in sys.argv:
        ind=sys.argv.index('-fcr')
        critout=sys.argv[ind+1]
    if '-fmt' in sys.argv:
        ind=sys.argv.index('-fmt')
        fmt='.'+sys.argv[ind+1]
    if '-spc' in sys.argv:
        ind=sys.argv.index('-spc')
        spc=sys.argv[ind+1]
        if '-b' in sys.argv:
            ind=sys.argv.index('-b')
            BEG=int(sys.argv[ind+1])
            END=int(sys.argv[ind+2])
    if critout!="":
        crit_data,file_type=pmag.magic_read(critout)
        if pmagplotlib.verbose:
            print "Acceptance criteria read in from ", critout
        accept={}
        accept['specimen_int_ptrm_n']=2.0
        for critrec in crit_data:
            if critrec["pmag_criteria_code"]=="IE-SPEC": 
                for key in accept_keys:
                    if key not in critrec.keys():
                        accept[key]=-1
                    else:
                        accept[key]=float(critrec[key])
    try:
        open(inspec,'rU')
        PriorRecs,file_type=pmag.magic_read(inspec)
        if file_type != 'pmag_specimens':
            print file_type
            print file_type,inspec," is not a valid pmag_specimens file " 
            sys.exit()
        for rec in PriorRecs:
            if 'magic_software_packages' not in rec.keys():rec['magic_software_packages']=""
    except IOError:
        PriorRecs=[]
        if pmagplotlib.verbose:print "starting new specimen interpretation file: ",inspec
    meas_data,file_type=pmag.magic_read(meas_file)
    if file_type != 'magic_measurements':
        print file_type
        print file_type,"This is not a valid magic_measurements file " 
        sys.exit()
    backup=0
    # define figure numbers for arai, zijderveld and 
    #   de-,re-magization diagrams
    AZD={}
    AZD['deremag'], AZD['zijd'],AZD['arai'],AZD['eqarea']=1,2,3,4
    pmagplotlib.plot_init(AZD['arai'],4,4)
    pmagplotlib.plot_init(AZD['zijd'],4,4)
    pmagplotlib.plot_init(AZD['deremag'],4,4)
    pmagplotlib.plot_init(AZD['eqarea'],4,4)
    #
    #
    #
    # get list of unique specimen names
    #
    CurrRec=[]
    sids=pmag.get_specs(meas_data)
    # get plots for specimen s - default is just to step through arai diagrams
    #
    if spc!="": specimen =sids.index(spc)
    while specimen < len(sids):
        methcodes=[]
        if pmagplotlib.verbose and spc!="":
            print sids[specimen],specimen+1, 'of ', len(sids)
        MeasRecs=[]
        s=sids[specimen]
        datablock,trmblock=[],[]
        PmagSpecRec={}
        PmagSpecRec["er_analyst_mail_names"]=user
        PmagSpecRec["specimen_correction"]='u'
    #
    # find the data from the meas_data file for this specimen
    #
        for rec in meas_data:
            if rec["er_specimen_name"]==s:
                MeasRecs.append(rec)
                methods=rec["magic_method_codes"].split(":")
                meths=[]
                for meth in methods:
                    meths.append(meth.strip()) # take off annoying spaces
                methods=""
                for meth in meths:
                    if meth.strip() not in methcodes and "LP-" in meth:methcodes.append(meth.strip())
                    methods=methods+meth+":"
                methods=methods[:-1]
                rec["magic_method_codes"]=methods 
                if "LP-PI-M" in meths: datablock.append(rec)
                if "LP-MRM" in meths: trmblock.append(rec)
        if len(trmblock)>2 and inspec!="":
            if Tinit==0:
                Tinit=1
                AZD['MRM']=4
                pmagplotlib.plot_init(AZD['MRM'],4,4)
            elif Tinit==1:
                pmagplotlib.clearFIG(AZD['MRM'])
        if len(datablock) <4:
           if backup==0:
               specimen+=1
               if pmagplotlib.verbose:
                   print 'skipping specimen - moving forward ', s
           else:
               specimen-=1
               if pmagplotlib.verbose:
                   print 'skipping specimen - moving backward ', s
    #
    #  collect info for the PmagSpecRec dictionary
    #
        else:
           rec=datablock[0]
           PmagSpecRec["er_citation_names"]="This study"
           PmagSpecRec["er_specimen_name"]=s
           PmagSpecRec["er_sample_name"]=rec["er_sample_name"]
           PmagSpecRec["er_site_name"]=rec["er_site_name"]
           PmagSpecRec["er_location_name"]=rec["er_location_name"]
           if "magic_instrument_codes" not in rec.keys():rec["magic_instrument_codes"]=""
           PmagSpecRec["magic_instrument_codes"]=rec["magic_instrument_codes"]
           PmagSpecRec["measurement_step_unit"]="J"
           if "magic_experiment_name" not in rec.keys():
               rec["magic_experiment_name"]=""
           else:
               PmagSpecRec["magic_experiment_names"]=rec["magic_experiment_name"]
    
           meths=rec["magic_method_codes"].split(':')
       # sort data into types
           if "LP-PI-M-D" in meths: # this is a double heating experiment
               exp_type="LP-PI-M-D"
           elif "LP-PI-M-S" in meths:
               exp_type="LP-PI-M-S"
           else:
               print "experiment type not supported yet "
               break
           araiblock,field=pmag.sortmwarai(datablock,exp_type)
           first_Z=araiblock[0]
           first_I=araiblock[1]
           GammaChecks=araiblock[-3]
           ThetaChecks=araiblock[-2]
           DeltaChecks=araiblock[-1]
           if len(first_Z)<3:
               if backup==0:
                   specimen+=1
                   if pmagplotlib.verbose:
                       print 'skipping specimen - moving forward ', s
               else:
                   specimen-=1
                   if pmagplotlib.verbose:
                       print 'skipping specimen - moving backward ', s
           else:
               backup=0
               zijdblock,units=pmag.find_dmag_rec(s,meas_data)
               if exp_type=="LP-PI-M-D":
                   recnum=0
                   print "ZStep Watts  Dec Inc  Int"
                   for plotrec in zijdblock:
                       if pmagplotlib.verbose:
                           print '%i  %i %7.1f %7.1f %8.3e ' % (recnum,plotrec[0],plotrec[1],plotrec[2],plotrec[3])
                           recnum += 1
                   recnum = 1
                   if GammaChecks!="":
                       print "IStep Watts  Gamma"
                       for gamma in GammaChecks:
                           if pmagplotlib.verbose: print '%i %i %7.1f ' % (recnum, gamma[0],gamma[1])
                           recnum += 1
               if exp_type=="LP-PI-M-S":
                   if pmagplotlib.verbose:
                       print "IStep Watts  Theta"
                       kk=0
                       for theta in ThetaChecks:
                           kk+=1
                           print '%i  %i %7.1f ' % (kk,theta[0],theta[1])
                   if pmagplotlib.verbose:
                       print "Watts  Delta"
                       for delta in DeltaChecks:
                           print '%i %7.1f ' % (delta[0],delta[1])
               pmagplotlib.plotAZ(AZD,araiblock,zijdblock,s,units[0])
               if inspec !="":
                   if pmagplotlib.verbose: print 'Looking up saved interpretation....'
                   found = 0
                   for k in range(len(PriorRecs)):
                       try:
                         if PriorRecs[k]["er_specimen_name"]==s:
                           found =1
                           CurrRec.append(PriorRecs[k])
                           for j in range(len(araiblock[0])):
                               if float(araiblock[0][j][0])==float(PriorRecs[k]["measurement_step_min"]):start=j
                               if float(araiblock[0][j][0])==float(PriorRecs[k]["measurement_step_max"]):end=j
                           pars,errcode=pmag.PintPars(araiblock,zijdblock,start,end)
                           pars['measurement_step_unit']="J"
                           del PriorRecs[k]  # put in CurrRec, take out of PriorRecs
                           if errcode!=1:
                               pars["specimen_lab_field_dc"]=field
                               pars["specimen_int"]=-1*field*pars["specimen_b"]
                               pars["er_specimen_name"]=s
                               if pmagplotlib.verbose:
                                   print 'Saved interpretation: '
                               pars=pmag.scoreit(pars,PmagSpecRec,accept,'',0)
                               pmagplotlib.plotB(AZD,araiblock,zijdblock,pars)
                               if len(trmblock)>2:
                                   blab=field
                                   best=pars["specimen_int"]
                                   Bs,TRMs=[],[]
                                   for trec in trmblock:
                                       Bs.append(float(trec['treatment_dc_field']))
                                       TRMs.append(float(trec['measurement_magn_moment']))
                                   NLpars=nlt.NLtrm(Bs,TRMs,best,blab,0) # calculate best fit parameters through TRM acquisition data, and get new banc
                                   Mp,Bp=[],[]
                                   for k in  range(int(max(Bs)*1e6)):
                                       Bp.append(float(k)*1e-6)
                                       npred=nlt.TRM(Bp[-1],NLpars['xopt'][0],NLpars['xopt'][1]) # predicted NRM for this field
                                       Mp.append(npred)
                                   pmagplotlib.plotTRM(AZD['MRM'],Bs,TRMs,Bp,Mp,NLpars,trec['magic_experiment_name'])
                                   print npred
                                   print 'Banc= ',float(NLpars['banc'])*1e6
                                   if pmagplotlib.verbose:
                                       print 'Banc= ',float(NLpars['banc'])*1e6
                                   pmagplotlib.drawFIGS(AZD)
                           else:
                               print 'error on specimen ',s
                       except:
                         pass
                   if pmagplotlib.verbose and found==0: print  '    None found :(  ' 
               if spc!="":
                   if BEG!="":
                       pars,errcode=pmag.PintPars(araiblock,zijdblock,BEG,END)
                       pars['measurement_step_unit']="J"
                       pars["specimen_lab_field_dc"]=field
                       pars["specimen_int"]=-1*field*pars["specimen_b"]
                       pars["er_specimen_name"]=s
                       pars['specimen_grade']='' # ungraded
                       pmagplotlib.plotB(AZD,araiblock,zijdblock,pars)
                       if len(trmblock)>2:
                           if inlt==0:
                               donlt()
                               inlt=1
                           blab=field
                           best=pars["specimen_int"]
                           Bs,TRMs=[],[]
                           for trec in trmblock:
                               Bs.append(float(trec['treatment_dc_field']))
                               TRMs.append(float(trec['measurement_magn_moment']))
                           NLpars=nlt.NLtrm(Bs,TRMs,best,blab,0) # calculate best fit parameters through TRM acquisition data, and get new banc
    #
                           Mp,Bp=[],[]
                           for k in  range(int(max(Bs)*1e6)):
                               Bp.append(float(k)*1e-6)
                               npred=nlt.TRM(Bp[-1],NLpars['xopt'][0],NLpars['xopt'][1]) # predicted NRM for this field
                   files={}
                   for key in AZD.keys():
                       files[key]=s+'_'+key+fmt 
                   pmagplotlib.saveP(AZD,files)
                   sys.exit()
               if plots==0:
                   ans='b'
                   while ans != "":
                       print """
               s[a]ve plot, set [b]ounds for calculation, [d]elete current interpretation, [p]revious, [s]ample, [q]uit:
               """
                       ans=raw_input('Return for next specimen \n')
                       if ans=="": 
                           specimen +=1
                       if ans=="d": 
                           save_redo(PriorRecs,inspec)
                           CurrRec=[]
                           pmagplotlib.plotAZ(AZD,araiblock,zijdblock,s,units[0])
                           pmagplotlib.drawFIGS(AZD)
                       if ans=='a':
                           files={}
                           for key in AZD.keys():
                               files[key]=s+'_'+key+fmt 
                           pmagplotlib.saveP(AZD,files)
                           ans=""
                       if ans=='q':
                           print "Good bye"
                           sys.exit()
                       if ans=='p':
                           specimen =specimen -1
                           backup = 1
                           ans=""
                       if ans=='s':
                           keepon=1
                           spec=raw_input('Enter desired specimen name (or first part there of): ')
                           while keepon==1:
                               try:
                                   specimen =sids.index(spec)
                                   keepon=0
                               except:
                                   tmplist=[]
                                   for qq in range(len(sids)):
                                       if spec in sids[qq]:tmplist.append(sids[qq])
                                   print specimen," not found, but this was: "
                                   print tmplist
                                   spec=raw_input('Select one or try again\n ')
                           ans=""
                       if  ans=='b':
                           if end==0 or end >=len(araiblock[0]):end=len(araiblock[0])-1
                           GoOn=0
                           while GoOn==0:
                               print 'Enter index of first point for calculation: ','[',start,']'
                               answer=raw_input('return to keep default  ')
                               if answer != "":start=int(answer)
                               print 'Enter index  of last point for calculation: ','[',end,']'
                               answer=raw_input('return to keep default  ')
                               if answer != "":
                                   end=int(answer)
                               if start >=0 and start <len(araiblock[0])-2 and end >0 and end <len(araiblock[0]) and start<end:
                                   GoOn=1
                               else:
                                   print "Bad endpoints - try again! "
                                   start,end=0,len(araiblock)
                           s=sids[specimen]
                           pars,errcode=pmag.PintPars(araiblock,zijdblock,start,end)
                           pars['measurement_step_unit']="J"
                           pars["specimen_lab_field_dc"]=field
                           pars["specimen_int"]=-1*field*pars["specimen_b"]
                           pars["er_specimen_name"]=s
                           pars=pmag.scoreit(pars,PmagSpecRec,accept,'',0)
                           PmagSpecRec["measurement_step_min"]='%8.3e' % (pars["measurement_step_min"])
                           PmagSpecRec["measurement_step_max"]='%8.3e' % (pars["measurement_step_max"])
                           PmagSpecRec["measurement_step_unit"]="J"
                           PmagSpecRec["specimen_int_n"]='%i'%(pars["specimen_int_n"])
                           PmagSpecRec["specimen_lab_field_dc"]='%8.3e'%(pars["specimen_lab_field_dc"])
                           PmagSpecRec["specimen_int"]='%8.3e '%(pars["specimen_int"])
                           PmagSpecRec["specimen_b"]='%5.3f '%(pars["specimen_b"])
                           PmagSpecRec["specimen_q"]='%5.1f '%(pars["specimen_q"])
                           PmagSpecRec["specimen_f"]='%5.3f '%(pars["specimen_f"])
                           PmagSpecRec["specimen_fvds"]='%5.3f'%(pars["specimen_fvds"])
                           PmagSpecRec["specimen_b_beta"]='%5.3f'%(pars["specimen_b_beta"])
                           PmagSpecRec["specimen_int_mad"]='%7.1f'%(pars["specimen_int_mad"])
                           PmagSpecRec["specimen_Z"]='%7.1f'%(pars["specimen_Z"])
                           if pars["method_codes"]!="":
                               tmpcodes=pars["method_codes"].split(":")
                               for t in tmpcodes:
                                   if t.strip() not in methcodes:methcodes.append(t.strip())
                           PmagSpecRec["specimen_dec"]='%7.1f'%(pars["specimen_dec"])
                           PmagSpecRec["specimen_inc"]='%7.1f'%(pars["specimen_inc"])
                           PmagSpecRec["specimen_tilt_correction"]='-1'
                           PmagSpecRec["specimen_direction_type"]='l'
                           PmagSpecRec["direction_type"]='l' # this is redudant, but helpful - won't be imported
                           PmagSpecRec["specimen_dang"]='%7.1f '%(pars["specimen_dang"])
                           PmagSpecRec["specimen_drats"]='%7.1f '%(pars["specimen_drats"])
                           PmagSpecRec["specimen_int_ptrm_n"]='%i '%(pars["specimen_int_ptrm_n"])
                           PmagSpecRec["specimen_rsc"]='%6.4f '%(pars["specimen_rsc"])
                           PmagSpecRec["specimen_md"]='%i '%(int(pars["specimen_md"]))
                           if PmagSpecRec["specimen_md"]=='-1':PmagSpecRec["specimen_md"]=""
                           PmagSpecRec["specimen_b_sigma"]='%5.3f '%(pars["specimen_b_sigma"])
                           if "IE-TT" not in  methcodes:methcodes.append("IE-TT")
                           methods=""
                           for meth in methcodes:
                               methods=methods+meth+":"
                           PmagSpecRec["magic_method_codes"]=methods[:-1]
                           PmagSpecRec["specimen_description"]=comment
                           PmagSpecRec["magic_software_packages"]=version_num
                           pmagplotlib.plotAZ(AZD,araiblock,zijdblock,s,units[0])
                           pmagplotlib.plotB(AZD,araiblock,zijdblock,pars)
                           if len(trmblock)>2:
                               blab=field
                               best=pars["specimen_int"]
                               Bs,TRMs=[],[]
                               for trec in trmblock:
                                   Bs.append(float(trec['treatment_dc_field']))
                                   TRMs.append(float(trec['measurement_magn_moment']))
                               NLpars=nlt.NLtrm(Bs,TRMs,best,blab,0) # calculate best fit parameters through TRM acquisition data, and get new banc
                               Mp,Bp=[],[]
                               for k in  range(int(max(Bs)*1e6)):
                                   Bp.append(float(k)*1e-6)
                                   npred=nlt.TRM(Bp[-1],NLpars['xopt'][0],NLpars['xopt'][1]) # predicted NRM for this field
                                   Mp.append(npred)
                               pmagplotlib.plotTRM(AZD['MRM'],Bs,TRMs,Bp,Mp,NLpars,trec['magic_experiment_name'])
                               print 'Banc= ',float(NLpars['banc'])*1e6
                           pmagplotlib.drawFIGS(AZD)
                           pars["specimen_lab_field_dc"]=field
                           pars["specimen_int"]=-1*field*pars["specimen_b"]
                           saveit=raw_input("Save this interpretation? [y]/n \n")
                           if saveit!='n':
                               specimen+=1
                               PriorRecs.append(PmagSpecRec) # put back an interpretation
                               save_redo(PriorRecs,inspec)
                           ans=""
               else:
                   specimen+=1
                   if fmt != ".pmag":
                       basename=s+'_microwave'+fmt
                       files={}
                       for key in AZD.keys():
                           files[key]=s+'_'+key+fmt 
                       if pmagplotlib.isServer:
                           black     = '#000000'
                           purple    = '#800080'
                           titles={}
                           titles['deremag']='DeReMag Plot'
                           titles['zijd']='Zijderveld Plot'
                           titles['arai']='Arai Plot'
                           AZD = pmagplotlib.addBorders(AZD,titles,black,purple)
                       pmagplotlib.saveP(AZD,files)
    #                   pmagplotlib.combineFigs(s,files,3)
        if len(CurrRec)>0:
            for rec in CurrRec:
                PriorRecs.append(rec)
        CurrRec=[]
    if plots!=1:
        ans=raw_input(" Save last plot? 1/[0] ")
        if ans=="1":
            if fmt != ".pmag":
                files={}
                for key in AZD.keys():
                    files[key]=s+'_'+key+fmt
                pmagplotlib.saveP(AZD,files)
        if len(CurrRec)>0:PriorRecs.append(CurrRec) # put back an interpretation
        if len(PriorRecs)>0:
            save_redo(PriorRecs,inspec)
            print 'Updated interpretations saved in ',inspec
    if pmagplotlib.verbose:
        print "Good bye"

if __name__ == "__main__":
    main()

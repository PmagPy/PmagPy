#!/usr/bin/env python
import sys,pmag,math,pmagplotlib,exceptions
def main():
    """
    NAME
        thellier_magic_cdfs.py

    DESCRIPTION
        makes plots of cdfs of paleointensity parameters plus a pie chart of "killers"

    SYNTAX
        thellier_magic_cdfs.py [-h][command line options]

    OPTIONS
        -h prints help message and quits
        -i allows interactive file name entry
        -f SPEC pmag_specimens format file, default is 'thellier_specimens.txt'
        -exc CRIT existing pmag_criteria format file, default is 'pmag_criteria.txt'
        -cus customize criteria
        
    """
    customize,critout,specfile="",'pmag_criteria.txt','thellier_specimens.txt'
    accept={}
    accept['specimen_int_ptrm_n']=2
    accept['specimen_md']=5
    accept['specimen_fvds']=0.4
    accept['specimen_b_beta']=0.12
    accept['specimen_drats']=15
    accept['specimen_dang']=10
    accept['specimen_int_mad']=7
    accept['specimen_Z']=4
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-f' in sys.argv:
       ind=sys.argv.index('-f')
       specfile=sys.argv[ind+1] 
    if '-exc' in sys.argv:
       ind=sys.argv.index('-exc')
       critout=sys.argv[ind+1] 
    if '-cus' in sys.argv: customize="1"
    if '-i' in sys.argv:
        specfile=raw_input("Input pmag_specimens file name? [thellier_specimens.txt] ")
        if specfile=="":specfile="thellier_specimens.txt" 
    #
    #
        ans=raw_input("Use existing acceptance criteria? 1/[0] ")
        if ans=='1':
            critout="pmag_criteria.txt" 
        customize=raw_input("Customize acceptance criteria? 1/[0] ")
    crit_data,file_type=pmag.magic_read(critout)
    print "Acceptance criteria read in from ", critout
    for critrec in crit_data:
        if critrec["pmag_criteria_code"]=="IE-SPEC": 
            accept['specimen_int_ptrm_n']=float(critrec["specimen_int_ptrm_n"])
            accept['specimen_drats']=float(critrec["specimen_drats"])
            accept['specimen_b_beta']=float(critrec["specimen_b_beta"])
            accept['specimen_md']=float(critrec["specimen_md"])
            accept['specimen_fvds']=float(critrec["specimen_fvds"])
            accept['specimen_dang']=float(critrec["specimen_dang"])
            accept['specimen_int_mad']=float(critrec["specimen_int_mad"])
            accept['specimen_Z']=float(critrec["specimen_Z"])
    while customize=='1':
       for key in accept.keys():
           print '%s %7.2f' % (key, accept[key])
           new=raw_input("Enter new criterion (return to keep default) ")
           if new != "": accept[key]=float(new)
       print accept
       customize=""
       customize=raw_input("Customize acceptance criteria again? 1/[0] ")
    # initialize some variables
    # define figure numbers for cdfs
    MADs,DANGs,BETAs,FVDSs,DRATSs,Zs,MDs=[],[],[],[],[],[],[]
    bMADs,bDANGs,bBETAs,bFVDSs,bDRATSs,bZs,bMDs=[],[],[],[],[],[],[]
    #
    # get name of file from command line
    #
    comment=""
    #
    #
    spec_data,file_type=pmag.magic_read(specfile)
    if file_type != 'pmag_specimens':
        print file_type
        print file_type,"This is not a valid pmag_specimens file " 
        sys.exit()
    Kill_keys=['specimen_int_mad','specimen_dang','specimen_b_beta','specimen_fvds','specimen_drats','specimen_md','specimen_Z']
    cutoff=len(Kill_keys)-1
    Kills={}
    NBs=0
    out=open('KillB.out','w')
    for key in Kill_keys:Kills[key]=0
    for spec in spec_data:
        MADs.append(float(spec['specimen_int_mad']))    
        DANGs.append(float(spec['specimen_dang']))    
        BETAs.append(float(spec['specimen_b_beta']))    
        FVDSs.append(float(spec['specimen_fvds']))    
        DRATSs.append(float(spec['specimen_drats'])) 
        if spec['specimen_md']!='-1':MDs.append(float(spec['specimen_md'])) 
        if spec['specimen_Z']!='-1':Zs.append(float(spec['specimen_Z']))
        grade,kill=pmag.grade(spec,accept)
        if grade==cutoff:
            bMADs.append(float(spec['specimen_int_mad']))    
            bDANGs.append(float(spec['specimen_dang']))    
            bBETAs.append(float(spec['specimen_b_beta']))    
            bFVDSs.append(float(spec['specimen_fvds']))    
            bDRATSs.append(float(spec['specimen_drats'])) 
            bMDs.append(float(spec['specimen_md'])) 
            bZs.append(float(spec['specimen_Z']))
            NBs+=1
            for key in kill.keys():
                if kill[key]==1: 
                    Kills[key]+=1 
                    print spec['er_specimen_name'],key
                    out.write('%s %s\n'%(spec['er_specimen_name'],key))
                    break
    CDF={}
    PLT=0
    if len(MADs)>0:
        PLT+=1
        CDF['MAD']=PLT
        pmagplotlib.plot_init(CDF['MAD'],5,5)
        pmagplotlib.plotCDF(CDF['MAD'],bMADs,'','b')
        pmagplotlib.plotCDF(CDF['MAD'],MADs,'MAD','r')
        pmagplotlib.plotVs(CDF['MAD'],[accept['specimen_int_mad']],'g','--')
    if len(DANGs)>0:
        PLT+=1
        CDF['DANG']=PLT
        pmagplotlib.plot_init(CDF['DANG'],5,5)
        pmagplotlib.plotCDF(CDF['DANG'],bDANGs,'','b')
        pmagplotlib.plotCDF(CDF['DANG'],DANGs,'DANG','r')
        pmagplotlib.plotVs(CDF['DANG'],[accept['specimen_dang']],'g','--')
    if len(DRATSs)>0:
        PLT+=1
        CDF['DRATS']=PLT
        pmagplotlib.plot_init(CDF['DRATS'],5,5)
        pmagplotlib.plotCDF(CDF['DRATS'],bDRATSs,'','b')
        pmagplotlib.plotCDF(CDF['DRATS'],DRATSs,'DRATS','r')
        pmagplotlib.plotVs(CDF['DRATS'],[accept['specimen_drats']],'g','--')
    if len(Zs)>0:
        PLT+=1
        CDF['Z']=PLT
        pmagplotlib.plot_init(CDF['Z'],5,5)
        pmagplotlib.plotCDF(CDF['Z'],bZs,'Z','b')
        pmagplotlib.plotCDF(CDF['Z'],Zs,'Z','r')
        pmagplotlib.plotVs(CDF['Z'],[accept['specimen_Z']],'g','--')
    if len(BETAs)>0:
        PLT+=1
        CDF['BETA']=PLT
        pmagplotlib.plot_init(CDF['BETA'],5,5)
        pmagplotlib.plotCDF(CDF['BETA'],bBETAs,'','b')
        pmagplotlib.plotCDF(CDF['BETA'],BETAs,'BETA','r')
        pmagplotlib.plotVs(CDF['BETA'],[accept['specimen_b_beta']],'g','--')
    if len(FVDSs)>0:
        PLT+=1
        CDF['FVDS']=PLT
        pmagplotlib.plot_init(CDF['FVDS'],5,5)
        pmagplotlib.plotCDF(CDF['FVDS'],bFVDSs,'','b')
        pmagplotlib.plotCDF(CDF['FVDS'],FVDSs,'fvds','r')
        pmagplotlib.plotVs(CDF['FVDS'],[accept['specimen_fvds']],'g','--')
    if len(MDs)>0:
        PLT+=1
        CDF['MD']=PLT
        pmagplotlib.plot_init(CDF['MD'],5,5)
        pmagplotlib.plotCDF(CDF['MD'],bMDs,'MD','b')
        pmagplotlib.plotCDF(CDF['MD'],MDs,'MD','r')
        pmagplotlib.plotVs(CDF['MD'],[accept['specimen_md']],'g','--')
    fracs,labels=[],[]
    for key in Kill_keys:
        if Kills[key]!=0:
            fracs.append(Kills[key])
            labels.append(key.split('_')[-1]+':'+str(int(100*float(Kills[key])/float(NBs)))+'%')
    CDF['PIE']=PLT+1
    pmagplotlib.plot_init(CDF['PIE'],5,5)
    pmagplotlib.plotPIE(CDF['PIE'],fracs,labels,'Grade B: N='+str(NBs))
    pmagplotlib.drawFIGS(CDF)
    print 'N: ',NBs
    for key in Kills.keys():
        if float(NBs)!=0:
            print key,'%7.1f %s'%(100.*float(Kills[key])/(float(NBs)),' %')
    try:
        raw_input('Return to save all figures, cntl-d to quit')
    except EOFError:
        print "Good bye"
        sys.exit()
    files={}
    for key in CDF.keys():
        files[key]=(key+'.svg')
    pmagplotlib.saveP(CDF,files)
main()

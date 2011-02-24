#!/usr/bin/env python
import pmag,sys,string
def main():
    """
    NAME
        TAN_magic.py
    
    DESCRIPTION
        import data files from the Tanaka format to magic

    SYNTAX
        TAN_magic.py -h [command line options]
        -h prints help message and quits
        -f FILE input pi or dmg file name
        -F FILE output magic_measuremetns name (default is magic_measurements.txt)
        -lab LABFIELD PHI THETA lab field in microT oriented phi,theta with respect to X
        -loc LOC location name
        -sam SAMP number of characters used to define specimen from sample
        -sit SITE number of characters used to define sample from site
        -cls [i,s,m], igneous, sedimentary or metamorphic [default is igneous]
        -lth [lithology], default is andesite
        -typ [lava flow, sedimentary layer, etc.], default is lava flow
    """
    specnum,sampnum=1,4 # setting defaults for parsing specimen names to sample and site
    labfield,phi,theta='0','0','90'
    meas_file="magic_measurements.txt"
    cl,litho,tp='igneous','andesite','lava flow'
# setting some variables from command line (sys.argv)
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-cls' in sys.argv:
        ind=sys.argv.index('-cls')
        cl=sys.argv[ind+1]
    if '-lth' in sys.argv:
        ind=sys.argv.index('-lth')
        litho=sys.argv[ind+1]
    if '-typ' in sys.argv:
        ind=sys.argv.index('-typ')
        tp=sys.argv[ind+1]
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
    if '-F' in sys.argv:
        ind=sys.argv.index('-F')
        meas_file=sys.argv[ind+1]
    if '-loc' in sys.argv:
        ind=sys.argv.index('-loc')
        locname=sys.argv[ind+1]
    if '-lab' in sys.argv:
        ind=sys.argv.index('-lab')
        labfield='%10.3e'%(1e-6*float(sys.argv[ind+1])) # assume labfield in microT
        phi=sys.argv[ind+2]
        theta=sys.argv[ind+3]
    if '-sam' in sys.argv:
        ind=sys.argv.index('-sam')
        specnum=int(sys.argv[ind+1])
    if '-sit' in sys.argv:
        ind=sys.argv.index('-sit')
        sampnum=int(sys.argv[ind+1])
    ErSpecs,ErSamps=[],[] # setup lists for dictionaries of specimens and samples
    MeasRecs=[]
    samples=[] # keep a list of unique sample names
    citation="This study" # default citation name
    f=open(file,'rU')
    data=f.readlines() # read in data
    k=0 # line number in datafile (-1)
    while k<len(data):
            line=data[k] # read in next record
            rec=line.split() # split on spaces into list called rec
            if rec[0]=='$':  # new specimen 
                ErSpecRec={} # set up dictionary for this specimen
                name=rec[1][:-1].upper()
                ErSpecRec['er_specimen_alternatives']=name
                treat_type=rec[1][-1].upper()
                sample=name[sampnum:-specnum]
                if len(sample)==1:sample='0'+sample
                ErSpecRec['er_specimen_name']=name[:sampnum]+'-'+sample+'-'+name[-specnum:]
                ErSpecRec['er_sample_name']=name[:sampnum]+'-'+sample
                ErSpecRec['er_site_name']=name[:sampnum]
                print 'processing ',ErSpecRec['er_specimen_name']
                ErSpecRec['er_location_name']=locname
                ErSpecRec['er_citation_names']=citation
                ErSpecRec['specimen_class']=cl
                ErSpecRec['specimen_lithology']=litho
                ErSpecRec['specimen_type']=tp
                if ErSpecRec['er_sample_name'] not in samples: # new sample
                    samples.append(ErSpecRec['er_sample_name']) # append to list
                    azimuth=float(rec[2])+90
                    dip=float(rec[3])
                    ErSampRec={} # set up dictionary for this sample
                    ErSampRec['er_sample_name']=ErSpecRec['er_sample_name']
                    ErSampRec['er_site_name']=ErSpecRec['er_site_name']
                    ErSampRec['er_citation_names']=citation
                    ErSampRec['sample_azimuth']='%7.1f'%(azimuth)
                    ErSampRec['sample_dip']='%7.1f'%(dip)
                    ErSampRec['magic_method_codes']='FS-FD:SO-SM'
                    ErSampRec['er_location_name']=locname
                    ErSampRec['er_citation_names']=citation
                    ErSampRec['sample_class']=cl
                    ErSampRec['sample_lithology']=litho
                    ErSampRec['sample_type']=tp
                    ErSamps.append(ErSampRec) # append to the sample list
                Ts=[] # keep a list of treatment temperatures for paleointensity experiments
                while 1:  # continue until next specimen
                    k+=1
                    if k==len(data):break
                    line=data[k] # read in next record
                    rec=line.split() # split on spaces into list called rec
                    if rec[0]=='$':  break
                    if rec[0][0]!='#': # skip commented out specimens
                        MeasRec={}
                        MeasRec['er_location_name']=locname
                        MeasRec['er_citation_names']=citation
                        MeasRec['er_specimen_name']=ErSpecRec['er_specimen_name']
                        MeasRec['er_sample_name']=ErSpecRec['er_sample_name']
                        MeasRec['er_site_name']=ErSpecRec['er_site_name']
                        MeasRec['measurement_temp']='273'  # assume room T measurements
                        MeasRec['measurement_flag']='g'  # good measurement
                        MeasRec['measurement_standard']='u'  # unknown (not a standard)
                        MeasRec['measurement_number']='1'  # measurement number
                        MeasRec['measurement_magn_moment']='%10.3e'%(1e-3*float(rec[1])) # convert to Am^2
                        MeasRec['measurement_inc']=rec[2]
                        MeasRec['measurement_dec']='%7.1f'%(float(rec[3])-90.)
                        MeasRec['magnetization_chi_volume']=''
                        treat=rec[0]
                        if treat_type=='A':
                            MeasRec['treatment_dc_field']='0'  # zero lab field
                            MeasRec['treatment_dc_field_phi']='0'  # zero lab field
                            MeasRec['treatment_dc_field_theta']='0'  # zero lab field
                            MeasRec['treatment_ac_field']='%8.3e'%(float(treat)*1e-3)
                            MeasRec['treatment_temp']='273' # room temperature treatment
                            if treat!="00":
                                MeasRec['magic_method_codes']='LT-AF-Z' # Af demag step
                            else:
                                MeasRec['magic_method_codes']='LT-NO' # Af demag step
                        elif treat_type=='T':
                            MeasRec['treatment_dc_field']='0'  # zero lab field
                            MeasRec['treatment_dc_field_phi']='0'  # zero lab field
                            MeasRec['treatment_dc_field_theta']='0'  # zero lab field
                            MeasRec['treatment_ac_field']='0'
                            MeasRec['treatment_temp']='%i'%(int(treat)+273) # treatment in kelvin
                            if treat!="00" and treat!="20":
                                MeasRec['magic_method_codes']='LT-T-Z' # Af demag step
                            else:
                                MeasRec['magic_method_codes']='LT-NO' # Af demag step
                        elif treat_type=='P':
                            T=int(treat)
                            MeasRec['treatment_temp']='%i'%(int(treat)+273) # treatment in kelvin
                            if treat[0]=='+': # infield step
                                if T not in Ts: # first infield step
                                    Ts.append(T) # put it in there
                                    MeasRec['magic_method_codes']='LT-T-I' # first infield step
                                    MeasRec['treatment_dc_field']=labfield
                                    MeasRec['treatment_dc_field_phi']=phi  # zero lab field
                                    MeasRec['treatment_dc_field_theta']=theta  # zero lab field
                                    MeasRec['treatment_ac_field']='0'
                                else:
                                    MeasRec['magic_method_codes']='LT-PTRM-I' # ptrm check
                                    MeasRec['treatment_dc_field']=labfield
                                    MeasRec['treatment_dc_field_phi']=phi
                                    MeasRec['treatment_dc_field_theta']=theta
                                    MeasRec['treatment_ac_field']='0'
                            else: # zero field step
                                if treat!="20":
                                    MeasRec['magic_method_codes']='LT-T-Z' # Af demag step
                                else:
                                    MeasRec['magic_method_codes']='LT-NO' # Af demag step
                                MeasRec['treatment_dc_field']='0'
                                MeasRec['treatment_dc_field_phi']=phi
                                MeasRec['treatment_dc_field_theta']=theta
                                MeasRec['treatment_ac_field']='0'
                        if len(rec)>4: MeasRec['magnetization_chi_volume']='%10.3e'%(1e-5*float(rec[4]))
                        MeasRecs.append(MeasRec) # save measurement record
                        ErSpecs.append(ErSpecRec) # save measurement record
    MagOuts=pmag.measurements_methods(MeasRecs,0)  # fix the method codes
    pmag.magic_write(meas_file,MagOuts,'magic_measurements') # set up measurement output file
    print "results put in ",meas_file
    stem=file.split('.')[0]+'_'
    pmag.magic_write(stem+'er_specimens.txt',ErSpecs,'er_specimens') # set up specimens output file
    print "specimens put in ",stem+"er_specimens.txt"
    pmag.magic_write(stem+'er_samples.txt',ErSamps,'er_samples') # set up samples output file
    print "specimens put in" ,stem+"er_specimens.txt"

main()

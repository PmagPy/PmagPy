#!/usr/bin/env python
import sys
import pmagpy.pmag as pmag

def main(command_line=True, **kwargs):
    """
    NAME
        pmd_magic.py
 
    DESCRIPTION
        converts PMD (Enkin)  format files to magic_measurements format files

    SYNTAX
        pmd_magic.py [command line options]

    OPTIONS
        -h: prints the help message and quits.
        -f FILE: specify  input file, or
        -F FILE: specify output file, default is magic_measurements.txt
        -Fsa: specify er_samples format file for appending, default is new er_samples.txt
        -spc NUM : specify number of characters to designate a  specimen, default = 1
        -loc LOCNAME : specify location/study name
        -A: don't average replicate measurements
        -ncn NCON: specify naming convention
        -mcd [SO-MAG,SO-SUN,SO-SIGHT...] supply how these samples were oriented
       Sample naming convention:
            [1] XXXXY: where XXXX is an arbitrary length site designation and Y
                is the single character sample designation.  e.g., TG001a is the
                first sample from site TG001.    [default]
            [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
            [5] site name same as sample
            [6] site is entered under a separate column -- NOT CURRENTLY SUPPORTED
            [7-Z] [XXXX]YYY:  XXXX is site designation with Z characters with sample name XXXXYYYY
            NB: all others you will have to customize your self
                 or e-mail ltauxe@ucsd.edu for help.
 
    INPUT
        PMD format files
    """
# initialize some stuff
    noave=0
    inst=""
    samp_con,Z='1',""
    missing=1
    demag="N"
    er_location_name="unknown"
    citation='This study'
    args=sys.argv
    meth_code="LP-NO"
    specnum=-1
    MagRecs=[]
    version_num=pmag.get_version()
    Samps=[] # keeps track of sample orientations
    DIspec=[]
    MagFiles=[]

    user=""
    mag_file=""
    dir_path='.'
    ErSamps=[]
    SampOuts=[]

    samp_file = 'er_samples.txt'
    meas_file = 'magic_measurements.txt'


    #
    # get command line arguments
    #
    
    if command_line:
        if '-WD' in sys.argv:
            ind = sys.argv.index('-WD')
            dir_path=sys.argv[ind+1]
        if '-ID' in sys.argv:
            ind = sys.argv.index('-ID')
            input_dir_path = sys.argv[ind+1]
        else:
            input_dir_path = dir_path
        output_dir_path = dir_path
        if "-h" in args:
            print main.__doc__
            return False
        if '-F' in args:
            ind=args.index("-F")
            meas_file = args[ind+1]
        if '-Fsa' in args:
            ind = args.index("-Fsa")
            samp_file = args[ind+1]
            #try:
            #    open(samp_file,'rU')
            #    ErSamps,file_type=pmag.magic_read(samp_file)
            #    print 'sample information will be appended to ', samp_file 
            #except:
            #    print samp_file,' not found: sample information will be stored in new er_samples.txt file'
            #    samp_file = output_dir_path+'/er_samples.txt'
        if '-f' in args:
            ind = args.index("-f")
            mag_file= args[ind+1]
        if "-spc" in args:
            ind = args.index("-spc")
            specnum = int(args[ind+1])
        if "-ncn" in args:
            ind=args.index("-ncn")
            samp_con=sys.argv[ind+1]
        if "-loc" in args:
            ind=args.index("-loc")
            er_location_name=args[ind+1]
        if "-A" in args: noave=1
        if "-mcd" in args: 
            ind=args.index("-mcd")
            meth_code=args[ind+1]

    if not command_line:
        dir_path = kwargs.get('dir_path', '.')
        input_dir_path = kwargs.get('input_dir_path', dir_path)
        output_dir_path = dir_path
        meas_file = kwargs.get('meas_file', 'magic_measurements.txt')
        mag_file = kwargs.get('mag_file')
        samp_file = kwargs.get('samp_file', 'er_samples.txt')
        specnum = kwargs.get('specnum', 0)
        samp_con = kwargs.get('samp_con', '1')
        er_location_name = kwargs.get('er_location_name', '')
        noave = kwargs.get('noave', 0) # default (0) means DO average
        meth_code = kwargs.get('meth_code', "LP-NO")

    print samp_con
    # format variables
    mag_file = input_dir_path+"/" + mag_file
    meas_file = output_dir_path+"/" + meas_file
    samp_file = output_dir_path+"/" + samp_file
    if specnum!=0:specnum=-specnum
    if "4" in samp_con:
        if "-" not in samp_con:
            print "naming convention option [4] must be in form 4-Z where Z is an integer"
            return False, "naming convention option [4] must be in form 4-Z where Z is an integer"
        else:
            Z=samp_con.split("-")[1]
            samp_con="4"
    if "7" in samp_con:
        if "-" not in samp_con:
            print "option [7] must be in form 7-Z where Z is an integer"
            return False, "naming convention option [7] must be in form 7-Z where Z is an integer"
        else:
            Z=samp_con.split("-")[1]
            samp_con="7"

    # parse data
    data=open(mag_file,'rU').readlines() # read in data from file
    comment=data[0]
    line=data[1].strip()
    line=line.replace("=","= ")  # make finding orientations easier
    rec=line.split() # read in sample orientation, etc.
    er_specimen_name=rec[0]
    ErSampRec,ErSiteRec={},{} # make a  sample record
    if specnum!=0:
        er_sample_name=rec[0][:specnum]
    else:
        er_sample_name=rec[0]
    if len(ErSamps)>0: # need to copy existing
       for samp in ErSamps:
           if samp['er_sample_name']==er_sample_name:
               ErSampRec=samp  # we'll ammend this one
           else:
               SampOuts.append(samp) # keep all the others
    if int(samp_con)<6:
        er_site_name=pmag.parse_site(er_sample_name,samp_con,Z)
    else:
        if 'er_site_name' in ErSampRec.keys():er_site_name=ErSampREc['er_site_name']
        if 'er_location_name' in ErSampRec.keys():er_location_name=ErSampREc['er_location_name']
    az_ind=rec.index('a=')+1
    ErSampRec['er_sample_name']=er_sample_name
    ErSampRec['er_sample_description']=comment
    ErSampRec['sample_azimuth']=rec[az_ind]
    dip_ind=rec.index('b=')+1
    dip=-float(rec[dip_ind])
    ErSampRec['sample_dip']='%7.1f'%(dip)
    strike_ind=rec.index('s=')+1
    ErSampRec['sample_bed_dip_direction']='%7.1f'%(float(rec[strike_ind])+90.)
    bd_ind=rec.index('d=')+1
    ErSampRec['sample_bed_dip']=rec[bd_ind]
    v_ind=rec.index('v=')+1
    vol=rec[v_ind][:-3]
    date=rec[-2]
    time=rec[-1]
    ErSampRec['magic_method_codes']=meth_code
    if 'er_location_name' not in ErSampRec.keys():ErSampRec['er_location_name']=er_location_name
    if 'er_site_name' not in ErSampRec.keys():ErSampRec['er_site_name']=er_site_name
    if 'er_citation_names' not in ErSampRec.keys():ErSampRec['er_citation_names']='This study'
    if 'magic_method_codes' not in ErSampRec.keys():ErSampRec['magic_method_codes']='SO-NO'
    SampOuts.append(ErSampRec)
    for k in range(3,len(data)): # read in data
      line=data[k]
      rec=line.split()
      if len(rec)>1: # skip blank lines at bottom  
        MagRec={}
        MagRec['measurement_description']='Date: '+date+' '+time
        MagRec["er_citation_names"]="This study"
        MagRec['er_location_name']=er_location_name
        MagRec['er_site_name']=er_site_name
        MagRec['er_sample_name']=er_sample_name
        MagRec['magic_software_packages']=version_num
        MagRec["treatment_temp"]='%8.3e' % (273) # room temp in kelvin
        MagRec["measurement_temp"]='%8.3e' % (273) # room temp in kelvin
        MagRec["measurement_flag"]='g'
        MagRec["measurement_standard"]='u'
        MagRec["measurement_number"]='1'
        MagRec["er_specimen_name"]=er_specimen_name
        if rec[0]=='NRM': 
            meas_type="LT-NO"
        elif rec[0][0]=='M' or rec[0][0]=='H': 
            meas_type="LT-AF-Z"
        elif rec[0][0]=='T': 
            meas_type="LT-T-Z"
        else:
            print "measurement type unknown"
            return False, "measurement type unknown"
        X=[float(rec[1]),float(rec[2]),float(rec[3])]
        Vec=pmag.cart2dir(X)
        MagRec["measurement_magn_moment"]='%10.3e'% (Vec[2]) # Am^2 
        MagRec["measurement_magn_volume"]=rec[4] # A/m 
        MagRec["measurement_dec"]='%7.1f'%(Vec[0])
        MagRec["measurement_inc"]='%7.1f'%(Vec[1])
        MagRec["treatment_ac_field"]='0'
        if meas_type!='LT-NO':
            treat=float(rec[0][1:])
        else:
            treat=0
        if meas_type=="LT-AF-Z":
            MagRec["treatment_ac_field"]='%8.3e' %(treat*1e-3) # convert from mT to tesla
        elif meas_type=="LT-T-Z":
            MagRec["treatment_temp"]='%8.3e' % (treat+273.) # temp in kelvin
        MagRec['magic_method_codes']=meas_type
        MagRecs.append(MagRec) 
    MagOuts=pmag.measurements_methods(MagRecs,noave)
    pmag.magic_write(meas_file,MagOuts,'magic_measurements')
    print "results put in ",meas_file
    pmag.magic_write(samp_file,SampOuts,'er_samples')
    print "sample orientations put in ",samp_file
    return True, meas_file

def do_help():
    return main.__doc__

if __name__ == "__main__":
    main()

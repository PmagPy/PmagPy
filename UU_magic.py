#!/usr/bin/env python
import string,sys,pmag,exceptions
#
#
def main():
    """
    NAME
        UU_magic.py
   
    DESCRIPTION
        takes Fort Hoofddijk (University of Utrecht) format magnetometer files and converts them to magic_measurements and er_samples.txt
 
    SYNTAX
        UU_magic.py [command line options]

    OPTIONS
        -f FILE: specify input file
        -fpos FILE: specify stratigraphic position  file (.saf format)
        -F FILE: specify magic_measurements output file, default is: magic_measurements.txt
        -Fsa FILE: specify output file, default is: er_samples.txt 
        -ncn NCON:  specify naming convention: default is #1 below
        -ocn OCON:  specify orientation convention, default is #1 below
        -mcd: specify sampling method codes as a colon delimited string:  [default is: FS-FD:SO-POM]
             FS-FD field sampling done with a drill
             FS-H field sampling done with hand samples
             FS-LOC-GPS  field location done with GPS
             FS-LOC-MAP  field location done with map
             SO-POM   a Pomeroy orientation device was used
             SO-ASC   an ASC orientation device was used
             SO-MAG   orientation with magnetic compass
             SO-SUN   orientation with sun compass
        -loc: location name, default="unknown"
        -spc NUM : specify number of characters to designate a  specimen, default = 0     
        -ins INST : specify instsrument name

    INPUT FORMAT
        Input files must be colon delimited:
            "file_name", "instrument"
            "specimen name","",az,pl,vol(cc),strike,dip
            treatment,X,Y,Z,CSD,"yy-mm-dd","hh:mm"
        Orientation convention:
            [1] Lab arrow azimuth= mag_azimuth; Lab arrow dip=-dip
                i.e., dip is degrees from vertical down - the hade [default]
            [2] Lab arrow azimuth = mag_azimuth-90; Lab arrow dip = -dip                
                i.e., mag_azimuth is strike and dip is hade
            [3] Lab arrow azimuth = mag_azimuth; Lab arrow dip = dip-90
                e.g. dip is degrees from horizontal of drill direction            
            [4] Lab arrow azimuth = mag_azimuth; Lab arrow dip = dip
            [5] Lab arrow azimuth = mag_azimuth; Lab arrow dip = 90-dip
            [6] all others you will have to either customize your
                self or e-mail ltauxe@ucsd.edu for help. 
       
         Magnetic declination convention:
             Az is already corrected in file 
    
       Sample naming convention:
            [1] XXXXY: where XXXX is an arbitrary length site designation and Y
                is the single character sample designation.  e.g., TG001a is the
                first sample from site TG001.    [default]
            [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
            [5] site name same as sample
            [6] site is entered under a separate column
            [7-Z] [XXXX]YYY:  XXXX is site designation with Z characters with sample name XXXXYYYY
            NB: all others you will have to customize your self
                 or e-mail ltauxe@ucsd.edu for help.
 
    OUTPUT
            output saved in magic_measurements.txt & er_samples.txt formatted files
              will overwrite any existing files 
    """
    #
    # initialize variables
    #
    uu_file,samp_file,or_con,corr,meas_file = "","er_samples.txt","1","1","magic_measurements.txt"
    pos_file=""
    specnum=-1
    args=sys.argv
    bed_dip,bed_dip_dir="",""
    samp_con,Z,average_bedding="1",1,"0"
    meths='FS-FD:SO-POM'
    sclass,lithology,type="","",""
    user,inst="",""
    or_con='1'
    corr=="3"
    DecCorr=0.
    location_name="unknown"
    #
    #
    dir_path='.'
    if '-WD' in args:
        ind=args.index("-WD")
        dir_path=sys.argv[ind+1]
    if "-h" in args:
        print main.__doc__
        sys.exit()
    if "-f" in args:
        ind=args.index("-f")
        uu_file=sys.argv[ind+1]
        d=uu_file.split('.')
        if d[1].upper()=="AF":demag="AF"
        if d[1].upper()=="TH":demag="T"
    if "-fpos" in args:
        ind=args.index("-fpos")
        pos_file=sys.argv[ind+1]
    if "-F" in args:
        ind=args.index("-F")
        meas_file=sys.argv[ind+1]
    if "-Fsa" in args:
        ind=args.index("-Fsa")
        samp_file=sys.argv[ind+1]
    if "-ocn" in args:
        ind=args.index("-ocn")
        or_con=sys.argv[ind+1]
    if "-ncn" in args:
        ind=args.index("-ncn")
        samp_con=sys.argv[ind+1]
        if "4" in samp_con:
            if "-" not in samp_con:
                print "option [4] must be in form 4-Z where Z is an integer"
                sys.exit()
            else:
                Z=samp_con.split("-")[1]
                samp_con="4"
        if "7" in samp_con:
            if "-" not in samp_con:
                print "option [7] must be in form 7-Z where Z is an integer"
                sys.exit()
            else:
                Z=samp_con.split("-")[1]
                samp_con="7"
    if "-mcd" in args:
        ind=args.index("-mcd")
        meths=(sys.argv[ind+1])
    if "-loc" in args:
        ind=args.index("-loc")
        location_name=(sys.argv[ind+1])
    if "-spc" in args:
        ind=args.index("-spc")
        specnum=-int(args[ind+1])
        if specnum!=0:specnum=-specnum
    if "-ins" in args:
        ind=args.index("-ins")
        inst=args[ind+1]
    #
    #
    uu_file=dir_path+'/'+uu_file
    samp_file=dir_path+'/'+samp_file
    meas_file=dir_path+'/'+meas_file
    if pos_file!="":pos_file=dir_path+'/'+pos_file
    samplist=[]
    try:
        SampOut,file_type=pmag.magic_read(samp_file)
        for rec in SampOut:
            if rec['er_sample_name'] not in samplist: samplist.append(rec['er_sample_name'])
    except:
        SampOut=[]
    PosData=[]
    if pos_file != "":
        p=open(pos_file,'rU')
        PosIn=p.readlines()
        p.close()
        for line in PosIn:
            srec=line.split()[0].split(',')
            Prec={'er_site_name':srec[0],'sample_height':srec[1]}
            PosData.append(Prec)
    infile=open(uu_file,'rU')
    Data=infile.readlines()
    infile.close()
    MagRecs=[]
    header=Data[0].split(',')
    if inst=="":inst=header[1].strip('"')
    if inst=='2G DC':
        inst=="FH-2GDC" # Dc Squid machine at Fort Hoofddijk
    else: 
        inst=""
    newsamp=1
    for k in range(1,len(Data)-1):  # step through file, skipping header  and "END" statement
        line=Data[k].split('\n')[0]
        rec=line.split(',')
        if newsamp==1 and rec[0].lower()!='end':
            newsamp=0
            specname=rec[0].strip('"') # take off quotation marks 
            if specnum!=0:
                sample=specname[:specnum]
            else:
                sample=specname
            site=pmag.parse_site(sample,samp_con,Z) # parse out the site name
            SampRec={}
            SampRec["er_sample_name"]=sample
            SampRec["er_location_name"]=location_name
            SampRec["er_citation_names"]="This study"
            labaz,labdip=pmag.orient(float(rec[2]),float(rec[3]),or_con)
            bed_dip=float(rec[6])
            if bed_dip!=0:
                bed_dip_dir=float(rec[5])+90. # assume dip to right of strike
                if bed_dip_dir>=360:bed_dip_dir=bed_dip_dir-360.
            else: 
                bed_dip_dir=float(rec[5]) 
    
    # parse information common to all orientation methods
    #
            SampRec["sample_bed_dip"]='%7.1f'%(bed_dip)
            SampRec["sample_bed_dip_direction"]='%7.1f'%(bed_dip_dir)
            SampRec["sample_dip"]='%7.1f'%(labdip)
            SampRec["sample_azimuth"]='%7.1f'%(labaz)
            vol=float(rec[4])*1e-6
            SampRec["sample_volume"]='%10.3e'%(vol) # convert cc into m^3
            SampRec["sample_class"]=sclass
            SampRec["sample_lithology"]=lithology
            SampRec["sample_type"]=type
            SampRec["magic_method_codes"]=meths
            SampRec["er_site_name"]=site
#
# find position data
#
            if PosData!=[]:
                    for srec in PosData:
                        if srec['er_site_name']==site:
                            SampRec['sample_height']=srec['sample_height']
                            break
            if sample not in samplist:
                samplist.append(sample)
                SampOut.append(SampRec)
        elif rec[0]=='9999': # end of this specimen
            k=k+1 # move on
            newsamp=1
        elif rec[0].lower()!='end' and rec[0]!="":  # got some data
            line=Data[k].split('\n')[0]
            rec=line.split(',')
            MagRec={}
            MagRec["treatment_temp"]='%8.3e' % (273) # room temp in kelvin
            MagRec["measurement_temp"]='%8.3e' % (273) # room temp in kelvin
            MagRec["treatment_ac_field"]='0'
            MagRec["treatment_dc_field"]='0'
            MagRec["treatment_dc_field_phi"]='0'
            MagRec["treatment_dc_field_theta"]='0'
            meas_type="LT-NO"
            MagRec["measurement_flag"]='g'
            MagRec["measurement_standard"]='u'
            MagRec["measurement_number"]='1'
            MagRec["er_specimen_name"]=specname
            MagRec["er_sample_name"]=sample
            MagRec["er_site_name"]=site
            MagRec["er_location_name"]=location_name
            MagRec["measurement_csd"]=rec[4]
            cart=[]
            cart.append(-float(rec[2])) # appending x,y,z from data record
            cart.append(float(rec[3]))
            cart.append(-float(rec[1]))
            Dir=pmag.cart2dir(cart)
            MagRec["measurement_magn_volume"]='%10.3e'% (float(Dir[2])*1e-6) # moment in A/m (from 10^-6 A/m)
            MagRec["measurement_magn_moment"]='%10.3e'% (float(Dir[2])*vol*1e-6) # moment in Am^2  
            MagRec["measurement_dec"]='%7.1f'%(Dir[0])
            MagRec["measurement_inc"]='%7.1f'%(Dir[1])
            MagRec["magic_instrument_codes"]=inst
            MagRec["er_analyst_mail_names"]=""
            MagRec["er_citation_names"]="This study"
            MagRec["magic_method_codes"]=meas_type
            if demag=="AF":
                MagRec["treatment_ac_field"]='%8.3e' %(float(rec[0])*1e-3) # peak field in tesla
                meas_type="LT-AF-Z"
                MagRec["treatment_dc_field"]='0'
            elif demag=="T":
                MagRec["treatment_temp"]='%8.3e' % (float(rec[0])+273.) # temp in kelvin
                meas_type="LT-T-Z"
            MagRec['magic_method_codes']=meas_type
#            date=rec[5].strip('"').split('-')
#            time=rec[6].strip('"')
#            if int(date[0])<50:  # assume this century 
#                yyyy='20'+date[0]
#            else:
#                yyyy='19'+date[0] # assume last century
#            dstring=yyyy+':'+date[1]+':'+date[2]+":"+time
#            MagRec['measurement_date']=dstring
            MagRecs.append(MagRec) 
    MagOuts=pmag.measurements_methods(MagRecs,0)
    pmag.magic_write(meas_file,MagOuts,'magic_measurements')
    print "Measurements put in ",meas_file
    pmag.magic_write(samp_file,SampOut,"er_samples")
    print "Sample orientation info  saved in ", samp_file
    print "Good bye"
main()

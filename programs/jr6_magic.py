#!/usr/bin/env python
import sys
import pmagpy.pmag as pmag

def main(command_line=True, **kwargs):
    """
    NAME
        jr6_magic.py
 
    DESCRIPTION
        converts JR6 format files to magic_measurements format files

    SYNTAX
        jr6_magic.py [command line options]

    OPTIONS
        -h: prints the help message and quits.
        -f FILE: specify  input file, or
        -F FILE: specify output file, default is magic_measurements.txt
#        -Fsa: specify er_samples format file for appending, default is new er_samples.txt
        -spc NUM : specify number of characters to designate a  specimen, default = 1
        -loc LOCNAME : specify location/study name
        -A: don't average replicate measurements
        -ncn NCON: specify sample naming convention (6 and 7 not yet implemented)
        -mcd [SO-MAG,SO-SUN,SO-SIGHT...] supply how these samples were oriented
       Sample naming convention:
            [1] XXXXY: where XXXX is an arbitrary length site designation and Y
                is the single character sample designation.  e.g., TG001a is the
                first sample from site TG001.    [default]
            [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
            [5] site name same as sample
            [6] site is entered under a separate column NOT CURRENTLY SUPPORTED
            [7-Z] [XXXX]YYY:  XXXX is site designation with Z characters with sample name XXXXYYYY
            NB: all others you will have to customize your self
                 or e-mail ltauxe@ucsd.edu for help.
 
    INPUT
        JR6 .txt format file
    """
# initialize some stuff
    noave=0
    samp_con,Z='1',""
    missing=1
    demag="N"
    er_location_name="unknown"
    citation='This study'
    args=sys.argv
    meth_code="LP-NO"
    specnum=1
    MagRecs=[]
    version_num=pmag.get_version()
    Samps=[] # keeps track of sample orientations

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
        if "-A" in args:
            noave=1
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
        specnum = kwargs.get('specnum', 1)
        samp_con = kwargs.get('samp_con', '1')
        er_location_name = kwargs.get('er_location_name', '')
        noave = kwargs.get('noave', 0) # default (0) means DO average
        meth_code = kwargs.get('meth_code', "LP-NO")


    # format variables
    mag_file = input_dir_path+"/" + mag_file
    meas_file = output_dir_path+"/" + meas_file
    samp_file = output_dir_path+"/" + samp_file
    if specnum!=0:
        specnum=-specnum
    if "4" in samp_con:
        if "-" not in samp_con:
            print "option [4] must be in form 4-Z where Z is an integer"
            return False
        else:
            Z=samp_con.split("-")[1]
            samp_con="4"
    if "7" in samp_con:
        if "-" not in samp_con:
            print "option [7] must be in form 7-Z where Z is an integer"
            return False
        else:
            Z=samp_con.split("-")[1]
            samp_con="7"

    ErSampRec,ErSiteRec={},{}

    # parse data
    data=open(mag_file,'rU')
    line=data.readline()
    line=data.readline()
    line=data.readline()
    while line !='':
        parsedLine=line.split()
        sampleName=parsedLine[0]
        demagLevel=parsedLine[2]
        date=parsedLine[3]
        line=data.readline()
        line=data.readline()
        line=data.readline()
        line=data.readline()
        parsedLine=line.split()
        specimenAngleDec=parsedLine[1]
        specimenAngleInc=parsedLine[2]
        while parsedLine[0] != 'MEAN' :
            line=data.readline() 
            parsedLine=line.split()
            if len(parsedLine) == 0:
                parsedLine=["Hello"]
        Mx=parsedLine[1]
        My=parsedLine[2]
        Mz=parsedLine[3]
        line=data.readline() 
        line=data.readline() 
        parsedLine=line.split()
        splitExp = parsedLine[2].split('A')
        intensityStr=parsedLine[1] + splitExp[0]
        intensity = float(intensityStr)

        # check and see if Prec is too big and messes with the parcing.
        precisionStr=''
        if len(parsedLine) == 6:  #normal line
            precisionStr=parsedLine[5][0:-1]
        else:
            precisionStr=parsedLine[4][0:-1]
            
        precisionPer = float(precisionStr)
        precision=intensity*precisionPer/100

        while parsedLine[0] != 'SPEC.' :
            line=data.readline() 
            parsedLine=line.split()
            if len(parsedLine) == 0:
                parsedLine=["Hello"]

        specimenDec=parsedLine[2]    
        specimenInc=parsedLine[3]    
        line=data.readline()
        line=data.readline()
        parsedLine=line.split()
        geographicDec=parsedLine[1]
        geographicInc=parsedLine[2]
    
        # Add data to various MagIC data tables.

        er_specimen_name = sampleName

        if specnum!=0:
            er_sample_name=er_specimen_name[:specnum]
        else:
            er_sample_name=er_specimen_name

        if int(samp_con) in [1, 2, 3, 4, 5, 7]:
            er_site_name=pmag.parse_site(er_sample_name,samp_con,Z)

        # else:
        #     if 'er_site_name' in ErSampRec.keys():er_site_name=ErSampRec['er_site_name']
        #     if 'er_location_name' in ErSampRec.keys():er_location_name=ErSampRec['er_location_name']

        # check sample list(SampOuts) to see if sample already exists in list before adding new sample info
        sampleFlag=0
        for sampRec in SampOuts:
            if sampRec['er_sample_name'] == er_sample_name:
                sampleFlag=1
                break
        if sampleFlag == 0:
            ErSampRec['er_sample_name']=er_sample_name
            ErSampRec['sample_azimuth']=specimenAngleDec
            ErSampRec['sample_dip']=specimenAngleInc
            ErSampRec['magic_method_codes']=meth_code 
            ErSampRec['er_location_name']=er_location_name
            ErSampRec['er_site_name']=er_site_name
            ErSampRec['er_citation_names']='This study'
            SampOuts.append(ErSampRec.copy())

        MagRec={}
        MagRec['measurement_description']='Date: '+date
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
        MagRec["treatment_ac_field"]='0'
        if demagLevel == 'NRM':
            meas_type="LT-NO"
        elif demagLevel[0] == 'A':
            meas_type="LT-AF-Z"
            treat=float(demagLevel[1:])
            MagRec["treatment_ac_field"]='%8.3e' %(treat*1e-3) # convert from mT to tesla
        elif demagLevel[0] == 'T':
            meas_type="LT-T-Z"
            treat=float(demagLevel[1:])
            MagRec["treatment_temp"]='%8.3e' % (treat+273.) # temp in kelvin
        else:
            print "measurement type unknown"
            return False
#        X=[float(Mx),float(My),float(Mz)]
#        Vec=pmag.cart2dir(X)
#        MagRec["measurement_magn_moment"]='%10.3e'% (Vec[2]) # Am^2
        MagRec["measurement_magn_moment"]=str(intensity*0.025*0.025*0.025) # Am^2 assume 2.5cm cube sample
        MagRec["measurement_magn_volume"]=intensityStr
        MagRec["measurement_dec"]=specimenDec
        MagRec["measurement_inc"]=specimenInc
        MagRec['magic_method_codes']=meas_type
        MagRecs.append(MagRec.copy())

        #read lines till end of record
        line=data.readline()
        line=data.readline()
        line=data.readline()
        line=data.readline()
        line=data.readline()

        # read all the rest of the special characters. Some data files not consistantly formatted.
        while (len(line) <=3 and line!=''):
            line=data.readline()
            
        #end of data while loop

    MagOuts=pmag.measurements_methods(MagRecs,noave)
    pmag.magic_write(samp_file,SampOuts,'er_samples') 
    print "sample orientations put in ",samp_file
    pmag.magic_write(meas_file,MagOuts,'magic_measurements')
    print "results put in ",meas_file
    return True

def do_help():
    return main.__doc__

if __name__ == "__main__":
    main()

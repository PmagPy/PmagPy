#!/usr/bin/env python
import string,sys,pmag
def main():
def main():
    """
    NAME
        FLA_magic.py

    DESCRIPTION
        import data files from the Univ. Florida, Gainesvile format to magic

    SYNTAX
        FLA_magic.py 

    """
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    meas_type,methcode,instcode,experiment_name,izzi="LT-NO","","","",0
    phi,theta,peakfield,labfield=0,0,0,0
    pTRM,MD,ispec=0,0,0
    dec=[315,225,180,135,45,90,270,270,270,90,180,180,0,0,0]
    inc=[0,0,0,0,0,-45,-45,0,45,45,45,-45,-90,-45,45]
    er_location_name=raw_input("Enter the location name for this study, or <return> for none ")
    if er_location_name=="":
        er_sites_file=raw_input("Enter site location file name, or <return> for none ")
        if er_sites_file=="": 
            er_location_name="none"
        else:
            site_locations,file_type=pmag.magic_read(er_sites_file)
    magfile=raw_input("Enter florida measurement filename for processing  ")
    print "Enter whether [A]F or [T]hermal de-(re)magnetization  "
    ans=raw_input(" <return> for NRMs only  ")
    inst=""
    methcode="LT-NO"
    if ans=="A":
        inst="UFG-AF"
        methcode="LT-AF-Z"
    if ans=="T":
        inst="UFG-thermal"
        methcode="LT-T-Z"
    if ans=="":methcode="LT-NO"  
    input=open(magfile,'r')
    MagRecs=[]
    for line in input.readlines():
        print line
        MagRec={}
        MagRec["treatment_temp"]='%8.3e' % (273) # room temp in kelvin
        MagRec["measurement_temp"]='%8.3e' % (273) # room temp in kelvin
        MagRec["treatment_ac_field"]='%8.3e' %(peakfield) # peak field in tesla
        MagRec["treatment_dc_field"]='%8.3e' %(labfield) # lab field in tesla
        MagRec["treatment_dc_field_phi"]='%7.1f' %(phi)
        MagRec["treatment_dc_field_theta"]='%7.1f'% (theta)
        rec=line.split()
        MagRec["er_specimen_name"]=rec[0]
        MagRec["er_sample_name"]=rec[0]
        sitetmp=rec[0].split('.') # Florida naming convention splits on '.' between site and sample
        MagRec["er_site_name"]=sitetmp[0]
        MagRec["er_location_name"]="none"
        if er_location_name!="":
            MagRec["er_location_name"]=er_location_name
        else:
            for site in site_locations:
                if site["er_site_name"] == MagRec["er_site_name"]: 
                    MagRec["er_location_name"]=site["er_location_name"]
        if inst=="UFG-AF":
            MagRec["treatment_ac_field"]='%8.3e' % ( float(rec[1])*1e-4) # AF field in tesla from Oersted in Florida convention
            meas_type="LT-AF-Z"
            MagRec["treatment_dc_field"]='0'
        else: 
            MagRec["treatment_temp"]='%8.3e' % (float(rec[1])+273.) # temp in kelvin
            meas_type="LT-T-Z"
        MagRec["measurement_magn_moment"]='%10.3e'% ((float(rec[4])/100)*1e-5) # moment in Am^2 (from 50xA/m and assuming 5cc sample in Florida convention)
        MagRec["measurement_dec"]=rec[7]
        MagRec["measurement_inc"]=rec[8]
        MagRec["magic_method_codes"]=meas_type
        MagRecs.append(MagRec) 
    output=raw_input("Filename for output [magic_measurements.txt] ")
    if output=="":output="magic_measurements.txt"
    MagOuts=pmag.measurements_methods(MagRecs,0)
    pmag.magic_write(output,MagOuts,'magic_measurements')
    print "results put in ",output
main()

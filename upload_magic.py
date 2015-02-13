#!/usr/bin/env python
import pmag,sys
import ipmag
import command_line_extractor as extractor

def main():
    """
    NAME
        upload_magic.py
   
    DESCRIPTION
        This program will prepare your PMAG text files created by the programs nfo_magic.py, 
        zeq_magic.py, thellier_magic.py, mag_magic, specimens_results_magic.py and so on.  
        it will check for all the MagIC text files and skip the missing ones
    
    SYNTAX
        upload_magic.py 

    INPUT
        MagIC txt files

    OPTIONS
        -h prints help message and quits
        -all include all the measurement data, default is only those used in interpretations

    OUTPUT
        upload.txt:  file for uploading to MagIC database
    """    
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    else:
        dataframe = extractor.command_line_dataframe([['all', False, 0], ['cat', False, 0], ['F', False, ''], ['f', False, '']])
        checked_args = extractor.extract_and_check_args(sys.argv, dataframe)
        All, dir_path, concat = extractor.get_vars(['all', 'WD', 'cat'], checked_args)
        ipmag.upload_magic(int(concat), int(All), dir_path[0])
        


"""
def main(command_line=True, **kwargs):

    NAME
        upload_magic.py
   
    DESCRIPTION
        This program will prepare your PMAG text files created by the programs nfo_magic.py, 
        zeq_magic.py, thellier_magic.py, mag_magic, specimens_results_magic.py and so on.  
        it will check for all the MagIC text files and skip the missing ones
    
    SYNTAX
        upload_magic.py 

    INPUT
        MagIC txt files

    OPTIONS
        -h prints help message and quits
        -all include all the measurement data, default is only those used in interpretations

    OUTPUT
        upload.txt:  file for uploading to MagIC database
    

#   set up filenames to upload
    concat,All=0,0
    dir_path='.'
    if command_line:
        if '-h' in sys.argv:
            print main.__doc__
            sys.exit()
        if '-cat' in sys.argv: concat=1
        if '-all' in sys.argv: All=1
        if '-WD' in sys.argv:
            ind=sys.argv.index('-WD')
            dir_path=sys.argv[ind+1]
    if not command_line:
        concat = kwargs.get('concat', 0)
        All = kwargs.get('All', 0)
        dir_path = kwargs.get('dir_path', '.')
    file_names=[]
    file_names.append(dir_path+'/'+"er_expeditions.txt")
    file_names.append(dir_path+'/'+"er_locations.txt")
    file_names.append(dir_path+'/'+"er_samples.txt")
    file_names.append(dir_path+'/'+"er_specimens.txt")
    file_names.append(dir_path+'/'+"er_sites.txt")
    file_names.append(dir_path+'/'+"er_ages.txt")
    file_names.append(dir_path+'/'+"er_citations.txt")
    file_names.append(dir_path+'/'+"er_mailinglist.txt")
    file_names.append(dir_path+'/'+"magic_measurements.txt")
    file_names.append(dir_path+'/'+"rmag_hysteresis.txt")
    file_names.append(dir_path+'/'+"rmag_anisotropy.txt")
    file_names.append(dir_path+'/'+"rmag_remanence.txt")
    file_names.append(dir_path+'/'+"rmag_results.txt")
    file_names.append(dir_path+'/'+"pmag_specimens.txt")
    file_names.append(dir_path+'/'+"pmag_samples.txt")
    file_names.append(dir_path+'/'+"pmag_sites.txt")
    file_names.append(dir_path+'/'+"pmag_results.txt")
    file_names.append(dir_path+'/'+"pmag_criteria.txt")
    file_names.append(dir_path+'/'+"magic_instruments.txt")
    # begin the upload process
    up=dir_path+"/upload.txt"
    RmKeys=['citation_label','compilation','calculation_type','average_n_lines','average_n_planes','specimen_grade','site_vgp_lat','site_vgp_lon','direction_type','specimen_Z','magic_instrument_codes','cooling_rate_corr','cooling_rate_mcd','anisotropy_atrm_alt','anisotropy_apar_perc','anisotropy_F','anisotropy_F_crit','specimen_scat','specimen_gmax','specimen_frac','site_vadm','site_lon','site_vdm','site_lat', 'measurement_chi','specimen_k_prime','external_database_names','external_database_ids']
    print "Removing: ",RmKeys
    last=file_names[-1]
    methods,first_file=[],1
    for file in file_names:
    # read in the data
        Data,file_type=pmag.magic_read(file)
        if file_type!="bad_file":
            print "file ",file," successfully read in"
            if len(RmKeys)>0:
                for rec in Data:
                    for key in RmKeys: 
                        if key=='specimen_Z' and key in rec.keys():
                            rec[key]='specimen_z' # change  # change this to lower case
                        if key in rec.keys():del rec[key] # get rid of unwanted keys
            if file_type=='er_samples': # check to only upload top priority orientation record!
                NewSamps,Done=[],[]
                for rec in Data:
                    if rec['er_sample_name'] not in Done:
                        orient,az_type=pmag.get_orient(Data,rec['er_sample_name'])
                        NewSamps.append(orient)
                        Done.append(rec['er_sample_name'])
                Data=NewSamps           
                print 'only highest priority orientation record from er_samples.txt read in '
            if file_type=='er_specimens': #  only specimens that have sample names
                NewData,SpecDone=[],[]
                for rec in Data:
                    if rec['er_sample_name'] in Done:
                        NewData.append(rec)
                        SpecDone.append(rec['er_specimen_name'])
                    else: 
                        print 'no sample record found for: ' 
                        print rec
                Data=NewData           
                print 'only measurements that have specimen/sample info'
            if file_type=='magic_measurments': #  only measurments that have specimen names
                NewData=[]
                for rec in Data:
                    if rec['er_sample_name'] in SpecDone:
                        NewData.append(rec)
                    else: 
                        print 'no specimen record found for: ' 
                        print rec
                Data=NewData           
    # write out the data
            if len(Data)>0:
                if first_file==1:
                    keystring=pmag.first_rec(up,Data[0],file_type)
                    first_file=0
                else:  
                    keystring=pmag.first_up(up,Data[0],file_type)
                for rec in Data:
    # collect the method codes
                    if "magic_method_codes" in rec.keys():
                        meths=rec["magic_method_codes"].split(':')
                        for meth in meths:
                            if meth.strip() not in methods:
                                if meth.strip()!="LP-DIR-":
                                    methods.append(meth.strip())
                    pmag.putout(up,keystring,rec)

    # write out the file separator
            f=open(up,'a')
            f.write('>>>>>>>>>>\n')
            f.close()
            print file_type, 'written to ',up
        else:
            print file, 'is bad or non-existent - skipping '

    # write out the methods table
    first_rec,MethRec=1,{}
    for meth in methods:
        MethRec["magic_method_code"]=meth
        if first_rec==1:meth_keys=pmag.first_up(up,MethRec,"magic_methods")
        first_rec=0
        pmag.putout(up,meth_keys,MethRec)
    if concat==1:
        f=open(up,'a')
        f.write('>>>>>>>>>>\n')
        f.close()

    # 
    if up:
        import validate_upload
        validated = False
        if validate_upload.read_upload(up):
           validated = True

    else:
        print "no data found, upload file not created"
        return False


    #print "now converting to dos file 'upload_dos.txt'"
    #f=open(up,'rU')
    #o=open(dir_path+'/'+"upload_dos.txt",'w')
    #for line in f.readlines():
    #    line=line[:-1]+'\r\n'
    #    o.write(line)
    
    print "Finished preparing upload.txt file "
    if not validated:
        print "-W- validation of upload file has failed.\nPlease fix above errors and try again.\nYou may run into problems if you try to upload this file to the MagIC database" 
"""

if __name__ == '__main__':
    main()

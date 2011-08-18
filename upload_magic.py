#!/usr/bin/env python
import pmag,sys
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

    OUTPUT
        upload.txt:  Unix formatted file (on Macs, Dos on PCs)
        upload_dos.txt: Dos formated file ready for importing to MagIC Console (v2.2) for checking. 
    
    """
#   set up filenames to upload
    concat=0
    dir_path='.'
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-cat' in sys.argv: concat=1
    if '-WD' in sys.argv:
        ind=sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
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
    RmKeys=['citation_label','compilation','calculation_type','average_n_lines','average_n_planes','specimen_grade','site_vgp_lat','site_vgp_lon','direction_type','specimen_Z','magic_instrument_codes','cooling_rate_corr','cooling_rate_mcd']
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
            if file_type=='er_samples': # check to only upload first orientation record!
                Done,NewData=[],[]
                for rec in Data:
                    if rec['er_sample_name'] not in Done:
                        NewData.append(rec)
                        Done.append(rec['er_sample_name'])
                Data=NewData           
                print 'only first orientation record from er_samples.txt read in '
            if file_type=='magic_measurements': # check to only upload first orientation record!
                NewData=[]
                for rec in Data:
                    if rec['er_sample_name'] in Done:
                        NewData.append(rec)
                    else: 
                        print 'excluded: ' 
                        print rec
                Data=NewData           
                print 'only measurements that are used for interpretations '
            if file_type=='er_specimens': # check to only upload first orientation record!
                NewData=[]
                for rec in Data:
                    if rec['er_sample_name'] in Done:
                        NewData.append(rec)
                    else: 
                        print 'excluded: ' 
                        print rec
                Data=NewData           
                print 'only measurements that are used for interpretations '
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
    
    print "now converting to dos file 'upload_dos.txt'"
    f=open(up,'rU')
    o=open(dir_path+'/'+"upload_dos.txt",'w')
    for line in f.readlines():
        line=line[:-1]+'\r\n'
        o.write(line)
    
    print "Finished preparing upload file "
main()

#!/usr/bin/env python
import pmag,sys,os,exceptions
def main():
    """
    NAME
        download_magic.py

    DESCRIPTION	
        unpacks a magic formatted smartbook .txt file from the MagIC database into the
        tab delimited MagIC format txt files for use with the MagIC-Py programs.

    SYNTAX
        download_magic.py command line options]

    INPUT
        takes either the upload.txt file created by upload_magic.py or the file
        exported by the MagIC v2.2 console software (downloaded from the MagIC database
        or output by the Console on your PC).

    OPTIONS
        -h prints help message and quits
        -i allows interactive entry of filename
        -f FILE specifies input file name
    """
    dir_path='.'
    if '-WD' in sys.argv:
        ind=sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
    if '-ID' in sys.argv:
        ind = sys.argv.index('-ID')
        input_dir_path = sys.argv[ind+1]
    else:
        input_dir_path = dir_path
    if '-i' in sys.argv:
        file=raw_input("Magic txt file for unpacking? ")
    elif '-f' in sys.argv:
        ind=sys.argv.index("-f")
        file=sys.argv[ind+1]
    else:
        print main.__doc__
        sys.exit()
    f=open(input_dir_path+'/'+file,'rU')
    File=f.readlines()
    LN=0
    type_list=[]
    filenum=0
    while LN<len(File)-1:
        line=File[LN]
        file_type=line.split('\t')[1]
        file_type=file_type.lower()
        if file_type=='delimited':file_type=Input[skip].split('\t')[2]
        if file_type[-1]=="\n":file_type=file_type[:-1]
        print 'working on: ',repr(file_type)
        if file_type not in type_list:
            type_list.append(file_type)
        else:
            filenum+=1 
        LN+=1
        line=File[LN]
        keys=line.replace('\n','').split('\t')
        if keys[0][0]=='.':
            keys=line.replace('\n','').replace('.','').split('\t')
            keys.append('RecNo') # cludge for new MagIC download format
        LN+=1
        Recs=[]
        while LN<len(File):
            line=File[LN]
            if line[:4]==">>>>" and len(Recs)>0:
                if filenum==0:
                    outfile=dir_path+"/"+file_type.strip()+'.txt'
                else:
                    outfile=dir_path+"/"+file_type.strip()+'_'+str(filenum)+'.txt' 
                NewRecs=[]
                for rec in Recs:
                    if 'magic_method_codes' in rec.keys():
                        meths=rec['magic_method_codes'].split(":")
                        if len(meths)>0:
                            methods=""
                            for meth in meths: methods=methods+meth.strip()+":" # get rid of nasty spaces!!!!!!
                            rec['magic_method_codes']=methods[:-1]
                    NewRecs.append(rec)
                pmag.magic_write(outfile,Recs,file_type)
                print file_type," data put in ",outfile
                if file_type =='pmag_specimens' and 'magic_measurements.txt' in File and 'measurement_step_min' in File and 'measurement_step_max' in File: # sort out zeq_specimens and thellier_specimens
                    os.system('mk_redo.py')
                    os.system('zeq_magic_redo.py')
                    os.system('thellier_magic_redo.py')
                    type_list.append('zeq_specimens')
                    type_list.append('thellier_specimens')
                Recs=[]
                LN+=1
                break
            else:
                rec=line.split('\t')
                Rec={}
                if len(rec)==len(keys):
                    for k in range(len(rec)):
                       Rec[keys[k]]=rec[k]
                    Recs.append(Rec)
                else:
                    print 'WARNING:  problem in file with line: '
                    print line
                    print 'skipping....'
                LN+=1
    if len(Recs)>0:
        if filenum==0:
            outfile=dir_path+"/"+file_type.strip()+'.txt'
        else:
            outfile=dir_path+"/"+file_type.strip()+'_'+str(filenum)+'.txt' 
        NewRecs=[]
        for rec in Recs:
            if 'magic_method_codes' in rec.keys():
                meths=rec['magic_method_codes'].split(":")
                if len(meths)>0:
                    methods=""
                    for meth in meths: methods=methods+meth.strip()+":" # get rid of nasty spaces!!!!!!
                    rec['magic_method_codes']=methods[:-1]
            NewRecs.append(rec)
        pmag.magic_write(outfile,Recs,file_type)
        print file_type," data put in ",outfile
# look through locations table and create separate directories for each location
    locs,locnum=[],1
    if 'er_locations' in type_list:
        locs,file_type=pmag.magic_read(dir_path+'/er_locations.txt')
    if len(locs)>0: # at least one location
        for loc in locs:
            print 'location_'+str(locnum)+": ",loc['er_location_name']
            lpath=dir_path+'/Location_'+str(locnum)
            locnum+=1
            try:
                os.mkdir(lpath)
            except:
                print 'directory ',lpath,' already exists - overwrite everything [y/n]?'
                ans=raw_input()
                if ans=='n':sys.exit()
            for f in type_list:
                print 'unpacking: ',dir_path+'/'+f+'.txt'
                recs,file_type=pmag.magic_read(dir_path+'/'+f+'.txt')
                print len(recs),' read in'
                if 'results' not in f:
                    lrecs=pmag.get_dictitem(recs,'er_location_name',loc['er_location_name'],'T')
                    if len(lrecs)>0:
                        pmag.magic_write(lpath+'/'+f+'.txt',lrecs,file_type)
                        print len(lrecs),' stored in ',lpath+'/'+f+'.txt'
                else:
                    lrecs=pmag.get_dictitem(recs,'er_location_names',loc['er_location_name'],'T')
                    if len(lrecs)>0:
                        pmag.magic_write(lpath+'/'+f+'.txt',lrecs,file_type)
                        print len(lrecs),' stored in ',lpath+'/'+f+'.txt'
main()

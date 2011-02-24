#!/usr/bin/env python
import pmag,sys,string
def main():
    """ 
    ODP_fix_sample_names.py
    DESCRIPTION:
        pads core to three digits and makes upper case
    OPTIONS:
        -f FILE, input ODP magic file for sample name conversion 
    """
    dir_path='.'
    if '-WD' in sys.argv:
        ind=sys.argv.index("-WD")
        dir_path=sys.argv[ind+1]
    if '-f' in sys.argv:
        ind=sys.argv.index("-f")
        infile=dir_path+'/'+sys.argv[ind+1]
    else:
        print "must specify -f input_file"
        sys.exit()
    Data,file_type=pmag.magic_read(infile)
    Fixed=[]
    for rec in Data:    
        pieces=rec['er_specimen_name'].split('-')
        if len(pieces)==6:
            while len(pieces[2])<4:pieces[2]='0'+pieces[2] # pad core to be 3 characters
            specimen=""
            for piece in pieces:
                specimen=specimen+piece+'-'
            specimen=specimen[:-1].upper()
            rec['er_specimen_name']=specimen 
            rec['er_sample_name']=specimen 
            rec['er_site_name']=specimen 
            rec['er_location_name']=pieces[1] 
            rec['er_expedition_name']=pieces[0] 
            Fixed.append(rec)
        else:
                print 'problem with this data record: ',rec['er_specimen_name']
                print 'deleting from file ', infile
    pmag.magic_write(infile,Fixed,file_type)
    print 'new specimen names written to: ',infile 
main()

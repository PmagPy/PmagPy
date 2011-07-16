#! /usr/bin/env python
import sys,pmag,exceptions,string
def main():
    """
    NAME
        specimen_anis_corr.py
   
    DESCRIPTION
        Calculate principal components through demagnetization data using bounds and calculation type stored in "redo" file
  
    SYNTAX
        specimen_ani_corr.py [command line options]

    OPTIONS
        -h prints help message
        -f: specify input file, default is pmag_specimens.txt
        -F: specify output file, default is AC_specimens.txt
        -fan  FILE: specify rmag_anisotropy file, default is "rmag_anisotropy"
    """
    dir_path='.'
    version_num=pmag.get_version()
    args=sys.argv
    spc_file,ani_file,spc_out='pmag_specimens.txt','rmag_anisotropy.txt','AC_specimens.txt'
    files=[spc_file,ani_file,spc_out]
    SpecOut=[]
    if '-WD' in args:
        ind=args.index('-WD')
        dir_path=args[ind+1]
    for file in files:file=dir_path+"/"+file
    if "-h" in args:
        print main.__doc__
        sys.exit()
    if "-f" in args:
        ind=args.index("-f")
        spc_file=dir_path+'/'+sys.argv[ind+1]
    if "-F" in args:
        ind=args.index("-F")
        spc_file=dir_path+'/'+sys.argv[ind+1]
    if "-fan" in args:
        ind=args.index("-fan")
        ani_file=dir_path+"/"+args[ind+1]
# now get down to bidness
    Specs,file_type=pmag.magic_read(spc_file)
    if file_type != 'pmag_specimens':
            print file_type
            print "This is not a valid specimens file " 
            sys.exit()
    AniSpecs,file_type=pmag.magic_read(ani_file)
    for Spc in Specs:
        anirecs=pmag.get_dictitem(AniSpecs,'er_specimen_name',Spc['er_specimen_name'],'T')
        if len(anirecs)>0:
            if 'specimen_int' not in Spc.keys():
                Spc['specimen_int']='1'
                rmkey=1
            else:rmkey=0
            AniSpec=anirecs[0] # take first one
            ACRec=pmag.doaniscorr(Spc,AniSpec)
            if rmkey==1:
               del ACRec['specimen_int']
            SpecOut.append(ACRec)
    pmag.magic_write(spc_out,SpecOut,'pmag_specimens')
    print "Anisotropy corrected specimen data stored in, ",spc_out
main()

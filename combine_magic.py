#!/usr/bin/env python
import sys,os
import pmag,ipmag
import command_line_extractor as extractor

def main():
    """
    NAME
        combine_magic.py

    DESCRIPTION
        Combines magic format files of the same type together.

    SYNTAX
        combine_magic.py [-h] [-i] -out filename -in file1 file2 ....

    OPTIONS
        -h prints help message
        -i allows interactive  entry of input and output filenames
        -F specify output file name [must come BEFORE input file names]
        -f specify input file names [ must come last]
    """
    if "-h" in sys.argv:
        print main.__doc__
        sys.exit()
    if "-i" in sys.argv: # interactive
        dataset,datasets=[],[]
        while True:
            infile=raw_input('\n\n Enter magic files for combining, <return>  when done: ')
            if infile=='':
                break
            if os.path.isfile(infile):
                filenames.append(infile)
            else:
                print "-W- You have not provided a valid filename.\nIf the file is not in your current working directory, you will need to provide the full path to the file"
        outfile=raw_input('\n\n Enter name for new combined file')
        if not outfile:
            return False
            
    else: # non-interactive

        dataframe = extractor.command_line_dataframe([["F", True, '']])
        args = extractor.extract_and_check_args(sys.argv, dataframe)
        dir_path, outfile, filenames = extractor.get_vars(["WD", "F", "f"], args)
        #dir_path = pmag.get_named_arg_from_sys("-WD", ".")
        #outfile = pmag.get_named_arg_from_sys("-F", reqd=True)
        #if "-f" in sys.argv:
        #    ind=sys.argv.index("-f")
        #    for k in range(ind+1,len(sys.argv)):
        #        filenames.append(os.path.join(dir_path, sys.argv[k]))
        #else:
        #    raise pmag.MissingCommandLineArgException("-f")
                
    ipmag.combine_magic(filenames, outfile[0])

    
main()







"""def old_main():

    NAME
        combine_magic.py

    DESCRIPTION
        Combines magic format files of the same type together.

    SYNTAX
        combine_magic.py [-h] [-i] -out filename -in file1 file2 ....

    OPTIONS
        -h prints help message
        -i allows interactive  entry of input and output filenames
        -F specify output file name [must come BEFORE input file names]
        -f specify input file names [ must come last]

    #
    #  set up magic meta data type requirements
    #
    filenames=[]
    datasets=[]
    dir_path='.'
    #
    if '-WD' in sys.argv:
        ind=sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
    if "-h" in sys.argv:
       print main.__doc__
       sys.exit() 
    if "-F" in sys.argv:
        ind=sys.argv.index("-F")
        output=dir_path+'/'+sys.argv[ind+1]
    if "-f" in sys.argv:
        ind=sys.argv.index("-f")
        for k in range(ind+1,len(sys.argv)):
            filenames.append(dir_path+'/'+sys.argv[k])
        for infile in filenames:
            dataset,file_type=pmag.magic_read(infile)
            print "File ",infile," read in with ",len(dataset), " records"
            for rec in dataset:
                datasets.append(rec)
    if '-i' in sys.argv:
        quit,dataset,datasets=0,[],[]
        while quit==0:
            infile=raw_input('\n\n Enter magic files for combining, <return>  when done: ')
            if infile=='':
                quit = 1
                break
            dataset,file_type=pmag.magic_read(infile)
            print "File ",infile," read in with ",len(dataset), " records"
            for rec in dataset:
                datasets.append(rec)
    #
    # collect all the keys from all the files
    #
    Recs,keys=pmag.fillkeys(datasets)
    #
    # write out the datasets into a combined file
    #
    pmag.magic_write(output,Recs,file_type)
    print "All records stored in ",output
#main()
"""

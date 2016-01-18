#!/usr/bin/env python
import sys
import os
import pmagpy.pmag as pmag
import pmagpy.ipmag as ipmag
import pmagpy.command_line_extractor as extractor

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
                
    ipmag.combine_magic(filenames.split(), outfile)

if __name__ == "__main__":    
    main()

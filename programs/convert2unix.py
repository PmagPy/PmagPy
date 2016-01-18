#!/usr/bin/env python
import sys

def main():
    """
    NAME
        convert2unix.py
    
    DESCRIPTION
      converts mac or dos formatted file to unix file in plac
    
    SYNTAX
        convert2unix.py FILE 
    
    OPTIONS
        -h prints help and quits
    
    """
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    file=sys.argv[1]
    f=open(file,'rU')
    Input=f.readlines()
    f.close()
    out=open(file,'w')
    for line in Input:
        out.write(line)
    out.close()

if __name__ == "__main__":
    main()

#!/usr/bin/env python
from __future__ import print_function
import sys

def main():
    """
    NAME
        convert2unix.py
    
    DESCRIPTION
      converts mac or dos formatted file to unix file in place
    
    SYNTAX
        convert2unix.py FILE 
    
    OPTIONS
        -h prints help and quits
    
    """
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    file=sys.argv[1]
    f=open(file,'r')
    Input=f.readlines()
    f.close()
    out=open(file,'w')
    for line in Input:
        out.write(line)
    out.close()

if __name__ == "__main__":
    main()

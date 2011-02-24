#!/usr/bin/env python
import sys,math,pmag
def main():
    """
    NAME
        find_azpl.py
    
    DESCRIPTION
      finds az,pl that converts CDEC,CINC to GDEC,GINC  
    
    SYNTAX
        find_azpl.py [command line options] [< filename]
    
    OPTIONS
        -f FILE, input file
    INPUT 
        CDEC CINC GDEC GINC
    OUTPUT 
        AZ,PL
    """
    out=""
    UP=0
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-f' in sys.argv:
        dat=[]
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]  
        f=open(file,'rU')
        input=f.readlines()
    else:
        input = sys.stdin.readlines()  # read from standard input
    for line in input:
        rec=line.split()
        cd,ci,gd,gi=float(rec[0]),float(rec[1]),float(rec[2]),float(rec[3])
        az,pl=pmag.get_azpl(cd,ci,gd,gi)
        print '%7.1f %7.1f'%(az,pl)

main() 

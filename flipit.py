#!/usr/bin/env python
import pmag,sys
def spitout(line):
    dat=line.split() # split the data on a space into columns
    dec,inc=float(dat[0]),float(dat[1])
    if inc<0:
        dec,inc=dec-180.,-inc
        if dec<0:dec=dec+360.
    print '%7.1f %7.1f'%(dec,inc) 
    return [dec,inc]
def main():
    """
    NAME
        flipit.py
    
    DESCRIPTION
      converts dec, inc to positive lines (antipodes of negative incs)
    
    INPUT (COMMAND LINE ENTRY) 
           declination inclination 
    OUTPUT
           Dec, Inc 
    
    SYNTAX
        flipit.py [command line options] [< filename]
    
    OPTIONS
        -i for interactive data entry
        -f FILE, input file
        -F FILE, output file
    
    """
    out=""
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-F' in sys.argv:
        ind=sys.argv.index('-F')
        ofile=sys.argv[ind+1]  
        out=open(ofile,'w')
    if '-i' in sys.argv:
        cont=1
        while cont==1:
            try:
                line=''
                ans=raw_input('Declination: [cntrl-D  to quit] ')
                line=line+' '+ans
                ans=raw_input('Inclination: ')
                line=line+' '+ans
                spitout(line)                
            except:
                print '\n Good-bye \n'
                sys.exit()
    elif '-f' in sys.argv:
        dat=[]
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]  
        f=open(file,'rU')
        input=f.readlines()
    else:
        input = sys.stdin.readlines()  # read from standard input
    for line in input:
        flip=spitout(line)
        if out!="":out.write('%7.1f %7.1f \n'%(flip[0],flip[1]))
main() 

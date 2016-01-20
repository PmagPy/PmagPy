#!/usr/bin/env python
import sys
import pmagpy.pmag as pmag

def spitout(line):
    dat=line.split() # split the data on a space into columns
    vdm,lat=float(dat[0]),float(dat[1])
    b= pmag.vdm_b(vdm,lat)  # 
    return b

def main():
    """
    NAME
        vdm_b.py
    
    DESCRIPTION
          converts V(A)DM to B
 
    INPUT (COMMAND LINE ENTRY) 
           V[A]DM (Am^2), latitude (positive north)

    OUTPUT
           B (T)
    
    SYNTAX
        vdm_b.py [command line options] [< filename]
    
    OPTIONS
        -h prints help and quits 
        -i for interactive data entry
        -f FILE input file
        -F FILE output 
    
    """
    input,out="",""
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
        f=open(file,'rU')
        input=f.readlines()
    if '-F' in sys.argv:
        ind=sys.argv.index('-F')
        o=sys.argv[ind+1]
        out=open(o,'w')
    if '-i' in sys.argv:
        cont=1
        while cont==1:
            try:
                vdm=float(raw_input('V[A]DM in Am^2: <cntl-D to quit '))
                lat=float(raw_input('Latitude: '))
            except:
                print "\nGood bye\n"
                sys.exit()
                 
            b= pmag.vdm_b(vdm,lat)
            print '%10.3e '%(b)
    if input=="":
        input = sys.stdin.readlines()  # read from standard input
    for line in input:
        b=spitout(line)
        if out=="":
            print '%10.3e'%(b)
        else:
            out.write('%10.3e \n'%(b))

if __name__ == "__main__":
    main() 

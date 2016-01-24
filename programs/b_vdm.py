#!/usr/bin/env python
import sys
import pmagpy.pmag as pmag

def spitout(line):
    if '\t' in line:
        dat=line.split('\t') # split the data on a space into columns
    else:
        dat=line.split() # split the data on a space into columns
    b,lat=float(dat[0])*1e-6,float(dat[1])
    vdm= pmag.b_vdm(b,lat)  # 
    return vdm

def main():
    """
    NAME
        b_vdm.py
    
    DESCRIPTION
          converts B (in microT) and (magnetic) latitude to V(A)DM
 
    INPUT (COMMAND LINE ENTRY) 
           B (microtesla), latitude (positive north)

    OUTPUT
           V[A]DM
    
    SYNTAX
        b_vdm.py [command line options] [< filename]
    
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
                b=1e-6*float(raw_input('B (in microtesla): <cntl-D to quit '))
                lat=float(raw_input('Latitude: '))
            except:
                print "\nGood bye\n"
                sys.exit()
                 
            vdm= pmag.b_vdm(b,lat)
            print '%10.3e '%(vdm)
    if input=="":
        input = sys.stdin.readlines()  # read from standard input
    for line in input:
        vdm=spitout(line)
        if out=="":
            print '%10.3e'%(vdm)
        else:
            out.write('%10.3e \n'%(vdm))

if __name__ == "__main__":
    main() 

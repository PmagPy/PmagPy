#!/usr/bin/env python
import pmag,sys,exceptions
def spitout(line):
    dir1,dir2=[],[] # initialize list for  d1,i1,d2,i2
    dat=line.split() # split the data on a space into columns
    dir1.append(float(dat[0]))
    dir1.append(float(dat[1]))
    dir2.append(float(dat[2]))
    dir2.append(float(dat[3]))
    ang= pmag.angle(dir1,dir2)  # 
    print '%7.1f '%(ang)
    return ang
def main():
    """
    NAME
        angle.py
    
    DESCRIPTION
      calculates angle between two input directions D1,D2
    
    INPUT (COMMAND LINE ENTRY) 
           D1_dec D1_inc D1_dec D2_inc
    OUTPUT
           angle
    
    SYNTAX
        angle.py [-h][-i] [command line options] [< filename]
    
    OPTIONS
        -h prints help and quits 
        -i for interactive data entry
        -f FILE input filename
        -F FILE output filename (required if -F set)
        Standard I/O 
    """
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
        dat=[]
        f=open(file,'rU')
        if '-F' in sys.argv:
            ind=sys.argv.index('-F')
            o=sys.argv[ind+1]
            out=open(o,'w')
            input=f.readlines()
            for line in input:
                ang=spitout(line)
                out.write('%7.1f \n'%(ang))
            sys.exit()
    elif '-i' in sys.argv:
        cont=1
        while cont==1:
            dir1,dir2=[],[]
            try:
                ans=raw_input('Declination 1: [ctrl-D  to quit] ')
                dir1.append(float(ans))
                ans=raw_input('Inclination 1: ')
                dir1.append(float(ans))
                ans=raw_input('Declination 2: ')
                dir2.append(float(ans))
                ans=raw_input('Inclination 2: ')
                dir2.append(float(ans))
            except:
                print "\nGood bye\n"
                sys.exit()
                 
            ang= pmag.angle(dir1,dir2)  # send dirs  to angle and spit out result
            print '%7.1f '%(ang)
    else:
        input = sys.stdin.readlines()  # read from standard input
        for line in input:   # read in the data (as string variable), line by line
            ang=spitout(line)
main() 

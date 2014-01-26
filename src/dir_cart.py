#!/usr/bin/env python
import pmag,sys,numpy
def main():
    """
    NAME
        dir_cart.py
    
    DESCRIPTION
      converts geomagnetic elements to cartesian coordinates
    
    INPUT (COMMAND LINE ENTRY) 
           declination inclination [magnitude]
          or
           longitude latitude
        if only two columns, assumes magnitude of unity
    OUTPUT
           x1 x2  x3
    
    SYNTAX
        dir_cart.py [command line options] [< filename]
    
    OPTIONS
        -h print help and quit
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
                dir=[]
                ans=raw_input('Declination: [cntrl-D  to quit] ')
                dir.append(float(ans))
                ans=raw_input('Inclination: ')
                dir.append(float(ans))
                ans=raw_input('Intensity [return for unity]: ')
                if ans=='':ans='1'
                dir.append(float(ans))
                cart= pmag.dir2cart(dir)  # send dir to dir2cart and spit out result
                print '%8.4e %8.4e %8.4e'%(cart[0],cart[1],cart[2])
            except:
                print '\n Good-bye \n'
                sys.exit()
    elif '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]  
        input=numpy.loadtxt(file)
    else:
        input=numpy.loadtxt(sys.stdin,dtype=numpy.float)
    cart= pmag.dir2cart(input)
    for line in cart:
        print '%8.4e %8.4e %8.4e'%(line[0],line[1],line[2])
        if out!="":out.write('%8.4e %8.4e %8.4e\n'%(line[0],line[1],line[2]))
main() 

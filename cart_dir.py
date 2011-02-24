#!/usr/bin/env python
import pmag,sys,exceptions
def spitout(line):
    cart=[]  # initialize list for  dec,inc,intensity
    dat=line.split() # split the data on a space into columns
    for element in dat: # step through dec,inc, int
        cart.append(float(element)) # append floating point variable to "cart"
    dir= pmag.cart2dir(cart)  # send cart to cart2dir
    print '%7.1f %7.1f %10.3e'%(dir[0],dir[1],dir[2])
    return dir
def main():
    """
    NAME
        cart_dir.py
    
    DESCRIPTION
      converts artesian coordinates to geomangetic elements
    
    INPUT (COMMAND LINE ENTRY) 
           x1 x2  x3
        if only two columns, assumes magnitude of unity
    OUTPUT
           declination inclination magnitude
    
    SYNTAX
        cart_dir.py [command line options] [< filename]
    
    OPTIONS 
        -h prints help message and quits
        -i for interactive data entry
        -f FILE to specify input filename
        -F OFILE to specify output filename (also prints to screen)
    
    """
    ofile=""
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-F' in sys.argv:
        ind=sys.argv.index('-F')
        ofile=sys.argv[ind+1]
        outfile=open(ofile,'w')
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
        f=open(file,'rU')
        dat=[]
        input=f.readlines()
        for line in input:
            dir=spitout(line)
            if ofile!="":
               outstring='%7.1f %7.1f %10.8e\n' %(dir[0],dir[1],dir[2]) 
               outfile.write(outstring)
        sys.exit()
    elif '-i' in sys.argv:
        cont=1
        while cont==1:
            cart=[]
            try:
                ans=raw_input('X: [ctrl-D  to quit] ')
                cart.append(float(ans))
                ans=raw_input('Y: ')
                cart.append(float(ans))
                ans=raw_input('Z: ')
                cart.append(float(ans))
            except:
                print "\n Good-bye \n"
                sys.exit()
            dir= pmag.cart2dir(cart)  # send dir to dir2cart and spit out result
            print '%7.1f %7.1f %10.3e'%(dir[0],dir[1],dir[2])
    else:
        input = sys.stdin.readlines()  # read from standard input
        for line in input:   # read in the data (as string variable), line by line
            dir=spitout(line)
main() 

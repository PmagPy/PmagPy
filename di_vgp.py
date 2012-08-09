#!/usr/bin/env python
import pmag,sys,numpy
def main():
    """
    NAME
        di_vgp.py
    DESCRIPTION
      converts declination/inclination to virtual geomagnetic pole
    
    SYNTAX
        di_vgp.py [-h] [-i] [-f FILE] [< filename]
    
    OPTIONS
        -h prints help message and quits
        -i interactive data entry
        -f FILE to specify file name on the command line
    
    INPUT 
      for file entry:
        D I SLAT SLON      
      where:
         D: declination
         I: inclination
         SLAT: site latitude (positive north)
         SLON: site longitude (positive east)
               
    OUTPUT
        PLON PLAT
        where:
             PLAT: pole latitude 
             PLON: pole longitude (positive east)
    """
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-F' in sys.argv:
        outfile=sys.argv[sys.arv.index('-F')+1]
    else:
        outfile=''
    if '-i' in sys.argv: # if one is -i
        a95=0
        while 1:
            try:
                ans   = raw_input("Input Declination: <cntrl-D to quit>  ")
                Dec   = float(ans)  # assign input to Dec, after conversion to floating point
                ans   = raw_input("Input Inclination:  ")
                Inc   = float(ans)
                ans   = raw_input("Input Site Latitude:  ")
                slat  = float(ans)
                ans   = raw_input("Input Site Longitude:  ")
                slong = float(ans)     
                output = pmag.dia_vgp(Dec,Inc,a95,slat,slong)
                print output
                print '%7.1f %7.1f'%(output[0],output[1]) 
            except:
                print "\n Good-bye\n"
                sys.exit()
    elif '-f' in sys.argv: # input of file name
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
        data=numpy.loadtxt(file)
    else: #
        data = numpy.loadtxt(sys.stdin,dtype=numpy.float) # read from S/I
    if len(data.shape)>1: # 2-D array
            N=data.shape[0]    
            if data.shape[1]==4:   # only dec,inc,sitelat, site long -no alpha95
                data=data.transpose()
                inlist=numpy.array([data[0],data[1],numpy.zeros(N),data[2],data[3]]).transpose()
            output = pmag.dia_vgp(inlist)
            for k in range(N):
                if outfile=='':
                    print '%7.1f %7.1f'%(output[0][k],output[1][k]) 
                else:
                    outfile.write('%7.1f %7.1f\n'%(output[0][k],output[1][k]))
    else: # single line of data
        if len(data)==4:
            data=[data[0],data[1],0,data[2],data[3]]
        output = pmag.dia_vgp(data)
        if outfile=='': # spit to standard output
            print '%7.1f %7.1f'%(output[0],output[1]) 
        else: # write to file
            outfile.write('%7.1f %7.1f\n'%(output[0],output[1]))
main()

#!/usr/bin/env python
import sys
import pmagpy.pmag as pmag

def main():
   """
   NAME
       eigs_s.py

   DESCRIPTION
     converts eigenparamters format data to s format

   SYNTAX
      eigs_s.py [-h][-i][command line options][<filename]

   OPTIONS
      -h prints help message and quits
      -i allows interactive file name entry
      -f FILE, specifies input file name
      -F FILE, specifies output file name
      < filenmae, reads file from standard input (Unix-like operating systems only)

   INPUT
      tau_i, dec_i inc_i of eigenvectors 
 
   OUTPUT
      x11,x22,x33,x12,x23,x13
   """
   file=""
   if '-h' in sys.argv:
       print main.__doc__
       sys.exit()
   elif '-i' in sys.argv:
       file=raw_input("Enter eigenparameters data file name: ")
       
   elif '-f' in sys.argv:
       ind=sys.argv.index('-f')
       file=sys.argv[ind+1]
   if file!="":
       f=open(file,'rU')
       data=f.readlines()
       f.close()
   else:
       data=sys.stdin.readlines()
   ofile=""
   if '-F' in sys.argv:
      ind = sys.argv.index('-F')
      ofile= sys.argv[ind+1]
      out = open(ofile, 'w + a')
   file_outstring = ""
   for line in data:
       tau,Vdirs=[],[]
       rec=line.split()
       for k in range(0,9,3):
           tau.append(float(rec[k]))
           Vdirs.append((float(rec[k+1]),float(rec[k+2])))
       srot=pmag.doeigs_s(tau,Vdirs) 
       outstring=""
       for s in srot:outstring+='%10.8f '%(s)
       if ofile=="":
           print outstring
       else:
           out.write(outstring+'\n')
#
if __name__ == "__main__":
   main()

#!/usr/bin/env python
import sys,numpy
#
f=float(sys.argv[1])
# read in inclination data
for line in sys.stdin.readlines():
   rec=line.split()
   dec=float(rec[0])
   inc=float(rec[1])*math.pi/180.
   tincnew=(1/f)*math.tan(inc)
   incnew=numpy.atan(tincnew)*180./numpy.pi
   print '%7.1f %7.1f'% (dec,incnew)


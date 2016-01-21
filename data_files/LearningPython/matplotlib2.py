#!/usr/bin/env python
import matplotlib
matplotlib.use("TkAgg")
import pylab,numpy
x=numpy.arange(0,360,10)
r=x*numpy.pi/180.
c=numpy.cos(r)
s=numpy.sin(r)
pylab.plot(x,c,'r--',x,s,'g^')
pylab.show()

#!/usr/bin/env python
import matplotlib
matplotlib.use("TkAgg")
import pylab, numpy
def f(t):
    return numpy.exp(-t)*numpy.cos(2.*numpy.pi*t)
t1= numpy.arange(0.,5.,0.1)
t2= numpy.arange(0.,5.,0.02)
fig=pylab.figure(num=1,figsize=(7,5)) 
fig.add_subplot(211) 
pylab.plot(t1,f(t1),'bo')
pylab.plot(t1,f(t1),'k-') 
fig.add_subplot(212) 
pylab.plot(t2,numpy.cos(2*numpy.pi*t2),'r--')
pylab.xlabel('Time (ms)') # x-label
fig.add_axes([.6,.75,.25,.10])
pylab.plot([0,1],[0,1],'r-',[0,1],[1,0],'r-')
pylab.ylabel('Inset')
pylab.show()

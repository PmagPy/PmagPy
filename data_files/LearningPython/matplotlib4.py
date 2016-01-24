#!/usr/bin/env python
import matplotlib
matplotlib.use("TkAgg")
import pylab,numpy
x=numpy.arange(0,360,10)
r=x*numpy.pi/180.
c=numpy.cos(r)
s=numpy.sin(r)
s2=numpy.sin(r)**2
pylab.plot(x,c,'r--',x,s,'g^',x,s2,'k-')
pylab.legend(['cos(x)',\
    'sin(x)',r'$\sin(x^2$)'],'lower left')
pylab.title('Fun with trig')
pylab.annotate('triangles!',\
  xy=(175,0),xytext=(110,-.25),\
   arrowprops=dict(facecolor='black',\
   shrink=0.05))
pylab.text(250,-.5,'pithy note')
pylab.xlabel(r'$\theta')
pylab.show()

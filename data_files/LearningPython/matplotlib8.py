#!/usr/bin/env python
from __future__ import division
from __future__ import print_function
from builtins import input
from past.utils import old_div
import numpy
import matplotlib
matplotlib.use("TkAgg")
import pylab
G=6.67e-11 # grav constant in Nm^2/kg^2 (SI)
R=2. # radius in meters
z=3. # depth of burial
drho=500 # density contrast in kg/m^3
x=numpy.arange(-2.*z,2.*z,0.1)
y=numpy.arange(-2.*z,2.*z,0.1)
X,Y=pylab.meshgrid(x,y)
h=numpy.sqrt(X**2+Y**2)
g=old_div((G*4.*numpy.pi*R**3.*drho),(3.*(h**2+z**2)))
print(g.ndim)
input()
pylab.imshow(g,interpolation='bilinear',cmap=pylab.cm.Spectral)
pylab.colorbar()
pylab.axis('equal')
pylab.show()

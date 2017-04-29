#!/usr/bin/env python
from __future__ import print_function
from builtins import input
import matplotlib
matplotlib.use("TkAgg")
import pylab, numpy
pylab.ion() # makes plot interactive
fig=pylab.figure() # makes a figure instance
ax=fig.add_subplot(111) # Axes instance
t=numpy.arange(0,1,.01)
s=numpy.sin(2*numpy.pi*t)
c=numpy.cos(2*numpy.pi*t)
ax.plot(t,s,color='blue',lw=2) #Line2D instance
ax.plot(t,c,color='magenta',lw=2)
pylab.draw()
print(ax.lines) # prints all your plot instances
print('last line color: ',ax.lines[-1].get_color())
input("Any key to change last line to red ")
ax.lines[-1].set_color('red') # sets last line to red
pylab.draw()
input()

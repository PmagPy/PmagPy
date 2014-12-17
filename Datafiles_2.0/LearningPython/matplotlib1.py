#!/usr/bin/env python
import matplotlib
matplotlib.use("TkAgg") # my favorite backend
import pylab # module with matplotlib
pylab.plot([1,2,3])  # plot some numbers
pylab.ylabel('Y') # label the y-axis
pylab.show() # reveal the plot

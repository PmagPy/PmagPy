#!/usr/bin/env python
from __future__ import division
from __future__ import print_function
from builtins import input
from builtins import str
from builtins import range
from past.utils import old_div
import sys
import numpy
import matplotlib
if matplotlib.get_backend() != "TKAgg":
  matplotlib.use("TKAgg")

from pylab import *
import pmagpy.pmagplotlib as pmagplotlib


# contributed by Ron Shaar 6/26/08
#
def smooth(x,window_len,window='bartlett'):
    """smooth the data using a sliding window with requested size.

    This method is based on the convolution of a scaled window with the signal.
    The signal is prepared by padding the beginning and the end of the signal
    with average of the first (last) ten values of the signal, to evoid jumps
    at the beggining/end

    input:
        x: the input signal, equaly spaced!
        window_len: the dimension of the smoothing window
        window:  type of window from numpy library ['flat','hanning','hamming','bartlett','blackman']
            -flat window will produce a moving average smoothing.
            -Bartlett window is very similar to triangular window,
                but always ends with zeros at points 1 and n,
            -hanning,hamming,blackman are used for smoothing the Fourier transfrom

            for curie temperature calculation the default is Bartlett

    output:
        aray of the smoothed signal

    """

    if x.ndim != 1:
        raise ValueError("smooth only accepts 1 dimension arrays.")

    if x.size < window_len:
        raise ValueError("Input vector needs to be bigger than window size.")

    if window_len<3:
        return x

    # numpy available windows
    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError("Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'")

    # padding the beggining and the end of the signal with an average value to evoid edge effect
    start=[average(x[0:10])]*window_len
    end=[average(x[-10:])]*window_len
    s=start+list(x)+end


    #s=numpy.r_[2*x[0]-x[window_len:1:-1],x,2*x[-1]-x[-1:-window_len:-1]]
    if window == 'flat': #moving average
        w=ones(window_len,'d')
    else:
        w=eval('numpy.'+window+'(window_len)')
    y=numpy.convolve(old_div(w,w.sum()),s,mode='same')
    return array(y[window_len:-window_len])



def deriv1(x,y,i,n):
    """
    alternative way to smooth the derivative of a noisy signal
    using least square fit.
    x=array of x axis
    y=array of y axis
    n=smoothing factor
    i= position

    in this method the slope in position i is calculated by least square fit of n points
    before and after position.
    """
    m_,x_,y_,xy_,x_2=0.,0.,0.,0.,0.
    for ix in range(i,i+n,1):
        x_=x_+x[ix]
        y_=y_+y[ix]
        xy_=xy_+x[ix]*y[ix]
        x_2=x_2+x[ix]**2
    m= old_div(( (n*xy_) - (x_*y_) ), ( n*x_2-(x_)**2))
    return(m)


def main():
    """
    NAME
        curie.py

    DESCTIPTION
        plots and interprets curie temperature data.
        the 1st derivative is calculated from smoothed M-T curve
            (convolution with trianfular window with width= <-w> degrees)
        the 2nd derivative is calculated from smoothed 1st derivative curve
            ( using the same sliding window width)
        the estinated curie temp. is the maximum of the 2nd derivative

        - the temperature steps should be in multiples of 1.0 degrees

    INPUT
        T,M

    SYNTAX
        curie.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f FILE, sets M,T input file (required)
        -w size of sliding window in degrees (default - 3 degrees)
        -t <min> <max> temperature range (optional)
        -sav save figures and quit
        -fmt [svg,jpg,eps,png,pdf] set format for figure output [default: svg]

    example:
    curie.py -f ex2.1 -w 30 -t 300 700

    """
    plot,fmt=0,'svg'
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        meas_file=sys.argv[ind+1]
    else:
        print("missing -f\n")
        sys.exit()
    if '-w' in sys.argv:
        ind=sys.argv.index('-w')
        window_len=int(sys.argv[ind+1])
    else:
        window_len=3
    if '-t' in sys.argv:
        ind=sys.argv.index('-t')
        t_begin=int(sys.argv[ind+1])
        t_end=int(sys.argv[ind+2])
    else:
        t_begin=''
        t_end=''
    if '-sav' in sys.argv:plot=1
    if '-fmt' in sys.argv:
        ind=sys.argv.index('-fmt')
        fmt=sys.argv[ind+1]


    # read data from file
    Data=numpy.loadtxt(meas_file,dtype=numpy.float)
    T=Data.transpose()[0]
    M=Data.transpose()[1]
    T=list(T)
    M=list(M)
    # cut the data if -t is one of the flags
    if t_begin:
        while T[0]<t_begin:
            M.pop(0);T.pop(0)
        while T[-1]>t_end:
            M.pop(-1);T.pop(-1)


    # prepare the signal:
    # from M(T) array with unequal deltaT
    # to M(T) array with deltaT=(1 degree).
    # if delataT is larger, then points are added using linear fit between
    # consecutive data points.
    # exit if deltaT is not integer
    i=0
    while i<(len(T)-1):
        if (T[i+1]-T[i])%1>0.001:
            print("delta T should be integer, this program will not work!")
            print("temperature range:",T[i],T[i+1])
            sys.exit()
        if (T[i+1]-T[i])==0.:
            M[i]=average([M[i],M[i+1]])
            M.pop(i+1);T.pop(i+1)
        elif (T[i+1]-T[i])<0.:
            M.pop(i+1);T.pop(i+1)
            print("check data in T=%.0f ,M[T] is ignored"%(T[i]))
        elif (T[i+1]-T[i])>1.:
            slope,b=polyfit([T[i],T[i+1]],[M[i],M[i+1]],1)
            for j in range(int(T[i+1])-int(T[i])-1):
                M.insert(i+1,slope*(T[i]+1.)+b)
                T.insert(i+1,(T[i]+1.))
                i=i+1
        i=i+1

    # calculate the smoothed signal
    M=array(M,'f')
    T=array(T,'f')
    M_smooth=[]
    M_smooth=smooth(M,window_len)

    #plot the original data and the smooth data
    PLT={'M_T':1,'der1':2,'der2':3,'Curie':4}
    pmagplotlib.plot_init(PLT['M_T'],5,5)
    string='M-T (sliding window=%i)'%int(window_len)
    pmagplotlib.plotXY(PLT['M_T'],T,M_smooth,sym='-')
    pmagplotlib.plotXY(PLT['M_T'],T,M,sym='--',xlab='Temperature C',ylab='Magnetization',title=string)

    #calculate first derivative
    d1,T_d1=[],[]
    for i in range(len(M_smooth)-1):
        Dy=M_smooth[i-1]-M_smooth[i+1]
        Dx=T[i-1]-T[i+1]
        d1.append(old_div(Dy,Dx))
    T_d1=T[1:len(T-1)]
    d1=array(d1,'f')
    d1_smooth=smooth(d1,window_len)

    #plot the first derivative
    pmagplotlib.plot_init(PLT['der1'],5,5)
    string='1st derivative (sliding window=%i)'%int(window_len)
    pmagplotlib.plotXY(PLT['der1'],T_d1,d1_smooth,sym='-',xlab='Temperature C',title=string)
    pmagplotlib.plotXY(PLT['der1'],T_d1,d1,sym='b--')

    #calculate second derivative
    d2,T_d2=[],[]
    for i in range(len(d1_smooth)-1):
        Dy=d1_smooth[i-1]-d1_smooth[i+1]
        Dx=T[i-1]-T[i+1]
        #print Dy/Dx
        d2.append(old_div(Dy,Dx))
    T_d2=T[2:len(T-2)]
    d2=array(d2,'f')
    d2_smooth=smooth(d2,window_len)

    #plot the second derivative
    pmagplotlib.plot_init(PLT['der2'],5,5)
    string='2nd derivative (sliding window=%i)'%int(window_len)
    pmagplotlib.plotXY(PLT['der2'],T_d2,d2,sym='-',xlab='Temperature C',title=string)
    d2=list(d2)
    print('second derivative maximum is at T=%i'%int(T_d2[d2.index(max(d2))]))

    # calculate Curie temperature for different width of sliding windows
    curie,curie_1=[],[]
    wn=list(range(5,50,1))
    for win in wn:
        # calculate the smoothed signal
        M_smooth=[]
        M_smooth=smooth(M,win)
        #calculate first derivative
        d1,T_d1=[],[]
        for i in range(len(M_smooth)-1):
            Dy=M_smooth[i-1]-M_smooth[i+1]
            Dx=T[i-1]-T[i+1]
            d1.append(old_div(Dy,Dx))
        T_d1=T[1:len(T-1)]
        d1=array(d1,'f')
        d1_smooth=smooth(d1,win)
        #calculate second derivative
        d2,T_d2=[],[]
        for i in range(len(d1_smooth)-1):
            Dy=d1_smooth[i-1]-d1_smooth[i+1]
            Dx=T[i-1]-T[i+1]
            d2.append(old_div(Dy,Dx))
        T_d2=T[2:len(T-2)]
        d2=array(d2,'f')
        d2_smooth=smooth(d2,win)
        d2=list(d2)
        d2_smooth=list(d2_smooth)
        curie.append(T_d2[d2.index(max(d2))])
        curie_1.append(T_d2[d2_smooth.index(max(d2_smooth))])

    #plot Curie temp for different sliding window length
    pmagplotlib.plot_init(PLT['Curie'],5,5)
    pmagplotlib.plotXY(PLT['Curie'],wn,curie,sym='.',xlab='Sliding Window Width (degrees)',ylab='Curie Temp',title='Curie Statistics')
    files = {}
    for key in list(PLT.keys()): files[key]=str(key) + "." +fmt
    if plot==0:
        pmagplotlib.drawFIGS(PLT)
        ans=input(" S[a]ve to save plot, [q]uit, Return to continue:  ")
        if ans=="q": sys.exit()
        if ans=="a": pmagplotlib.saveP(PLT,files)
    else: pmagplotlib.saveP(PLT,files)
    sys.exit()

main()

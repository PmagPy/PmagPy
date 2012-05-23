#!/usr/bin/env python
import sys,pmag,pmagplotlib,numpy,exceptions
from pylab import *

# modified from curie.py by Ron Shaar
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
        raise ValueError, "smooth only accepts 1 dimension arrays."

    if x.size < window_len:
        raise ValueError, "Input vector needs to be bigger than window size."

    if window_len<3:
        return x

    # numpy available windows
    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError, "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"

    # padding the beggining and the end of the signal with an average value to evoid edge effect
    start=[average(x[0:10])]*window_len
    end=[average(x[-10:])]*window_len
    s=start+list(x)+end

        
    #s=numpy.r_[2*x[0]-x[window_len:1:-1],x,2*x[-1]-x[-1:-window_len:-1]]
    if window == 'flat': #moving average
        w=ones(window_len,'d')
    else:
        w=eval('numpy.'+window+'(window_len)')
    y=numpy.convolve(w/w.sum(),s,mode='same')
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
    m= ( (n*xy_) - (x_*y_) ) / ( n*x_2-(x_)**2)
    return(m)
        
   
def main():
    """
    NAME
        curie_magic.py

    DESCTIPTION
        plots and interprets curie temperature data.
        the 1st derivative is calculated from smoothed M-T curve
            (convolution with trianfular window with width= <-w> degrees)
        the 2nd derivative is calculated from smoothed 1st derivative curve
            ( using the same sliding window width)
        the estinated curie temp. is the maximum of the 2nd derivative

        - the temperature steps should be in multiples of 1.0 degrees

    INPUT
        magic_measurements formatted file
  
    SYNTAX
        curie_magic.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f FILE, sets M,T magic_measurements formatted file, default is MsT_measurements.txt
        -F RMAG, sets Rmag_results format file for appending results, default is not
        -w size of sliding window in degrees (default - 3 degrees)
        -t <min> <max> temperature range (optional)

    """
    fmt,dir_path='svg','.'
    if '-WD' in sys.argv:
        ind=sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
    meas_file=dir_path+'/MsT_measurements.txt'
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        meas_file=dir_path+'/'+sys.argv[ind+1]
    Results,rmag_file=[],""
    if '-F' in sys.argv:
        ind=sys.argv.index('-F')
        rmag_file=dir_path+'/'+sys.argv[ind+1]
        try:
            Results,file_type=pmag.magic_read(rmag_file)
            if file_type!='rmag_results':
                print 'bad results file, starting new one'
        except:
            pass
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

    # read data from file
    Data,file_type=pmag.magic_read(meas_file)
    if file_type!='magic_measurements':
        print 'bad measurements file'
        sys.exit()
    specs=[]
    for rec in Data:
        specname=""
        if 'er_specimen_name' in rec.keys() and rec['er_specimen_name']!="": 
            specname=rec['er_specimen_name']
        else: 
            rec['er_specimen_name']=""
        if 'er_synthetic_name' in rec.keys() and rec['er_synthetic_name']!="": 
            specname=rec['er_synthetic_name']
        else: 
            rec['er_synthetic_name']=""
        if specname not in specs:specs.append(specname)
    for spec in specs:
        print 'processing: ',spec
        M,T,curieT=[],[],0
        for rec in Data:
          if rec['er_specimen_name'] or rec['er_synthetic_name']==spec: 
            location,sample,site="","",""
            if 'er_location_name' in rec.keys():location=rec['er_location_name']
            if 'er_sample_name' in rec.keys():sample=rec['er_sample_name']
            if 'er_site_name' in rec.keys():site=rec['er_site_name']
            syn=""
            if 'er_synthetic_name' in rec.keys():syn=rec['er_synthetic_name']
            meths=rec['magic_method_codes'].strip().split(':')
            expnames=rec['magic_experiment_name'].strip().split(':')
            if 'LP-MW-I' in meths and 'Curie' in expnames:
                method=rec['magic_method_codes']
                expname=rec['magic_experiment_name']
                T.append(float(rec['measurment_temp'])-273)
                M.append(float(rec['measurement_magnitude']))
        # cut the data if -t is one of the flags
        if len(M)<10:
            print 'not enough data for processing'
            sys.exit()
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
                print "delta T should be integer, this program will not work!"
                print "temperature range:",T[i],T[i+1]
                sys.exit()
            if (T[i+1]-T[i])==0.:
                M[i]=average([M[i],M[i+1]])
                M.pop(i+1);T.pop(i+1)
            elif (T[i+1]-T[i])<0.:
                M.pop(i+1);T.pop(i+1)
                print "check data in T=%.0f ,M[T] is ignored"%(T[i])
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
        pmagplotlib.plotXY(PLT['M_T'],T,M,'--','Temperature C','Magnetization',string)
        pmagplot.lib.drawFIGS(PLT)
        plot(T,M_smooth,'-')
    
        #calculate first derivative
        d1,T_d1=[],[]
        for i in range(len(M_smooth)-1):
            Dy=M_smooth[i-1]-M_smooth[i+1]
            Dx=T[i-1]-T[i+1]
            d1.append(Dy/Dx)
        T_d1=T[1:len(T-1)]
        d1=array(d1,'f')
        d1_smooth=smooth(d1,window_len)
    
        #plot the first derivative
        pmagplotlib.plot_init(PLT['der1'],5,5)
        string='1st dervative (sliding window=%i)'%int(window_len)
        pmagplotlib.plotXY(PLT['der1'],T_d1,d1_smooth,'-','temperatue C','',string)
        plot(T_d1,d1,'--b')
    
        #calculate second derivative
        d2,T_d2=[],[]
        for i in range(len(d1_smooth)-1):
            Dy=d1_smooth[i-1]-d1_smooth[i+1]
            Dx=T[i-1]-T[i+1]
            #print Dy/Dx
            d2.append(Dy/Dx)
        T_d2=T[2:len(T-2)]
        d2=array(d2,'f')
        d2_smooth=smooth(d2,window_len)
        
        #plot the second derivative
        pmagplotlib.plot_init(PLT['der2'],5,5)
        string='2nd dervative (sliding window=%i)'%int(window_len)
        pmagplotlib.plotXY(PLT['der2'],T_d2,d2,'-','temperatue C','',string)
        d2=list(d2)
        print 'second deriative maximum is at T=%i'%int(T_d2[d2.index(max(d2))])
    
        # calculate Curie temperature for different width of sliding windows
        curie,curie_1=[],[]
        wn=range(5,50,1)
        for win in wn:
            # calculate the smoothed signal
            M_smooth=[]
            M_smooth=smooth(M,win)
            #calculate first derivative
            d1,T_d1=[],[]
            for i in range(len(M_smooth)-1):
                Dy=M_smooth[i-1]-M_smooth[i+1]
                Dx=T[i-1]-T[i+1]
                d1.append(Dy/Dx)
            T_d1=T[1:len(T-1)]
            d1=array(d1,'f')
            d1_smooth=smooth(d1,win)
            #calculate second derivative
            d2,T_d2=[],[]
            for i in range(len(d1_smooth)-1):
                Dy=d1_smooth[i-1]-d1_smooth[i+1]
                Dx=T[i-1]-T[i+1]
                d2.append(Dy/Dx)
            T_d2=T[2:len(T-2)]
            d2=array(d2,'f')
            d2_smooth=smooth(d2,win)
            d2=list(d2)
            d2_smooth=list(d2_smooth)
            curie.append(T_d2[d2.index(max(d2))])    
            if curie[-1]>curieT:curieT=curie[-1] # find maximum curie T
            curie_1.append(T_d2[d2_smooth.index(max(d2_smooth))])    
    
        #plot Curie temp for different sliding window length
        pmagplotlib.plot_init(PLT['Curie'],5,5)
        pmagplotlib.plotXY(PLT['Curie'],wn,curie,'.','sliding window width (degrees)','curie temp','Inferred Curie Temperatures')    
        print 'Curie T is: ',curieT
        pmagplotlib.drawFIGS(PLT)
        files={}
        for key in PLT.keys():
             files[key]=spec+'_'+key+'.'+fmt
        ans=raw_input(" S[a]ve to save plot, [q]uit, or return to continue: ")
        if ans=='q':sys.exit()
        if ans=='a':
            pmagplotlib.saveP(PLT,files)
        if rmag_file!="":
            ResRec={}
            ResRec['rmag_result_name']='Curie T: '+spec
            ResRec['er_location_names']=location
            ResRec['er_sample_names']=sample
            ResRec['er_site_names']=site
            ResRec['er_synthetic_names']=syn
            if syn!="": 
                ResRec['er_specimen_names']=spec
            else:
                ResRec['er_specimen_names']=""
            ResRec['magic_experiment_names']=expname
            ResRec['magic_method_codes']=method+':SM-2DMAX'
            ResRec['critical_temp']='%10.1f'%(curieT)
            ResRec['critical_temp_type']="Curie"
            ResRec['er_citation_names']="This study"
            Results.append(ResRec)
    if len(Results)>0 and rmag_file!="":
        ResOuts,keys=pmag.fillkeys(Results)
        pmag.magic_write(rmag_file,ResOuts,'rmag_results')
        print 'Results stored in ',rmag_file
main()


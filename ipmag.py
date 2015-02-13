import pmag
import pmagplotlib
import pylab
import numpy as np
import random
import matplotlib
import matplotlib.pyplot as plt
import os
import sys

#from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
#from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib.figure import Figure

def igrf(input_list):
    """
    prints out Declination, Inclination, Intensity data from an input list with format: [Date, Altitude, Latitude, Longitude]
    Date must be in format XXXX.XXXX with years and decimals of a year (A.D.)
    """
    x,y,z,f=pmag.doigrf(input_list[3]%360.,input_list[2],input_list[1],input_list[0])
    Dir=pmag.cart2dir((x,y,z))
    return Dir

def fishrot(k=20,n=100,Dec=0,Inc=90):
    """
    Generates Fisher distributed unit vectors from a specified distribution 
    using the pmag.py fshdev and dodirot functions
    
    Arguments
    ----------
    k kappa precision parameter (default is 20) 
    n number of vectors to determine (default is 100)
    Dec mean declination of data set (default is 0)
    Inc mean inclination of data set (default is 90)
    """
    directions=[]
    for data in range(n):
        dec,inc=pmag.fshdev(k) 
        drot,irot=pmag.dodirot(dec,inc,Dec,Inc)
        directions.append([drot,irot,1.])
    return directions

def tk03(n=100,dec=0,lat=0,rev='no',G2=0,G3=0):
    """
    generates set of vectors drawn from the TK03.gad model of 
    secular variation (Tauxe and Kent, 2004) at given latitude and rotated 
    about a vertical axis by the given declination 

    Arguments
    ----------
    n number of vectors to determine (default is 100)
    dec mean declination of data set (default is 0)
    lat latitude at which secular variation is simulated (default is 0)
    rev if reversals are to be included this should be 'yes' (default is 'no')
    G2 specify average g_2^0 fraction (default is 0)
    G3 specify average g_3^0 fraction (default is 0)
    """
    tk_03_output=[]
    for k in range(n): 
        gh=pmag.mktk03(8,k,G2,G3) # terms and random seed
        long=random.randint(0,360) # get a random longitude, between 0 and 359
        vec= pmag.getvec(gh,lat,long)  # send field model and lat to getvec
        vec[0]+=dec
        if vec[0]>=360.:
            vec[0]-=360.
        if k%2==0 and rev=='yes':
           vec[0]+=180.
           vec[1]=-vec[1]
        tk_03_output.append([vec[0],vec[1],vec[2]])    
    return tk_03_output

def flip(D): #function simplified from PmagPy pmag.flip function
    """
    This function returns the antipode (flips) of the unit vectors in D (dec,inc,length).
    """
    Dflip=[]
    for rec in D:
        d,i=(rec[0]-180.)%360.,-rec[1]
        Dflip.append([d,i])
    return Dflip

def bootstrap_fold_test(Data,num_sims=1000,min_untilt=-10,max_untilt=120,bedding_error=0):
    """
    Conduct a bootstrap fold test (Tauxe and Watson, 1994)
    
    Three plots are generated: 1) equal area plot of uncorrected data; 2) tilt-corrected equal area plot; 
    3) bootstrap results showing the trend of the largest eigenvalues for a selection of the 
    pseudo-samples (red dashed lines), the cumulative distribution of the eigenvalue maximum (green line)
    and the confidence bounds that enclose 95% of the pseudo-sample maxima. If the confidence bounds enclose
    100% unfolding, the data "pass" the fold test.
    
    Arguments
    ----------
    Data : a numpy array of directional data [dec,inc,dip_direction,dip]
    NumSims : number of bootstrap samples (default is 1000)
    min_untilt : minimum percent untilting applied to the data (default is -10%)
    max_untilt : maximum percent untilting applied to the data (default is 120%)
    bedding_error : (circular standard deviation) for uncertainty on bedding poles
    """   
    
    print 'doing ',num_sims,' iterations...please be patient.....'

    if bedding_error!=0:
        kappa=(81./bedding_error)**2
    else:
        kappa=0
            
    plt.figure(figsize=[5,5])
    plot_net(1)
    pmagplotlib.plotDI(1,Data)  # plot directions
    plt.text(-1.1,1.15,'Geographic')

    D,I=pmag.dotilt_V(Data)
    TCs=np.array([D,I]).transpose()

    plt.figure(figsize=[5,5])
    plot_net(2)
    pmagplotlib.plotDI(2,TCs)  # plot directions
    plt.text(-1.1,1.15,'Tilt-corrected')
    plt.show()
    
    Percs = range(min_untilt,max_untilt)
    Cdf = []
    Untilt = []
    plt.figure()
    
    for n in range(num_sims): # do bootstrap data sets - plot first 25 as dashed red line
            #if n%50==0:print n
            Taus=[] # set up lists for taus
            PDs=pmag.pseudo(Data)
            if kappa!=0:
                for k in range(len(PDs)):
                    d,i=pmag.fshdev(kappa)
                    dipdir,dip=pmag.dodirot(d,i,PDs[k][2],PDs[k][3])
                    PDs[k][2]=dipdir            
                    PDs[k][3]=dip
            for perc in Percs:
                tilt=np.array([1.,1.,1.,0.01*perc])
                D,I=pmag.dotilt_V(PDs*tilt)
                TCs=np.array([D,I]).transpose()
                ppars=pmag.doprinc(TCs) # get principal directions
                Taus.append(ppars['tau1'])
            if n<25:plt.plot(Percs,Taus,'r--')
            Untilt.append(Percs[Taus.index(np.max(Taus))]) # tilt that gives maximum tau
            Cdf.append(float(n)/float(num_sims))
    plt.plot(Percs,Taus,'k')
    plt.xlabel('% Untilting')
    plt.ylabel('tau_1 (red), CDF (green)')
    Untilt.sort() # now for CDF of tilt of maximum tau
    plt.plot(Untilt,Cdf,'g')
    lower=int(.025*num_sims)     
    upper=int(.975*num_sims)
    plt.axvline(x=Untilt[lower],ymin=0,ymax=1,linewidth=1,linestyle='--')
    plt.axvline(x=Untilt[upper],ymin=0,ymax=1,linewidth=1,linestyle='--')
    title = '%i - %i %s'%(Untilt[lower],Untilt[upper],'percent unfolding')
    print ""
    print 'tightest grouping of vectors obtained at (95% confidence bounds):'
    print title
    print 'range of all bootstrap samples: '
    print Untilt[0], ' - ', Untilt[-1],'percent unfolding'
    plt.title(title)
    plt.show()
        
def bootstrap_common_mean(Data1,Data2,NumSims=1000):
    """
    Conduct a bootstrap test (Tauxe, 2010) for a common mean on two declination,
    inclination data sets
    
    This function modifies code from PmagPy for use calculating and plotting 
    bootstrap statistics. Three plots are generated (one for x, one for y and
    one for z). If the 95 percent confidence bounds for each component overlap
    each other, the two directions are not significantly different.

    Arguments
    ----------
    Data1 : a list of directional data [dec,inc]
    Data2 : a list of directional data [dec,inc]
    NumSims : number of bootstrap samples (default is 1000)
    """         
    counter=0
    BDI1=pmag.di_boot(Data1)
    BDI2=pmag.di_boot(Data2)

    cart1= pmag.dir2cart(BDI1).transpose()
    X1,Y1,Z1=cart1[0],cart1[1],cart1[2]
    cart2= pmag.dir2cart(BDI2).transpose()
    X2,Y2,Z2=cart2[0],cart2[1],cart2[2]
    
    print "Here are the results of the bootstrap test for a common mean:"
    
    fignum = 1
    fig = plt.figure(figsize=(9,3))
    fig = plt.subplot(1,3,1)
    
    minimum = int(0.025*len(X1))
    maximum = int(0.975*len(X1))
    
    X1,y=pmagplotlib.plotCDF(fignum,X1,"X component",'r',"")
    bounds1=[X1[minimum],X1[maximum]]
    pmagplotlib.plotVs(fignum,bounds1,'r','-')

    X2,y=pmagplotlib.plotCDF(fignum,X2,"X component",'b',"")
    bounds2=[X2[minimum],X2[maximum]]
    pmagplotlib.plotVs(fignum,bounds2,'b','--')
    plt.ylim(0,1)
    
    plt.subplot(1,3,2)
    
    Y1,y=pmagplotlib.plotCDF(fignum,Y1,"Y component",'r',"")
    bounds1=[Y1[minimum],Y1[maximum]]
    pmagplotlib.plotVs(fignum,bounds1,'r','-')
    
    Y2,y=pmagplotlib.plotCDF(fignum,Y2,"Y component",'b',"")
    bounds2=[Y2[minimum],Y2[maximum]]
    pmagplotlib.plotVs(fignum,bounds2,'b','--')
    plt.ylim(0,1)
    
    plt.subplot(1,3,3)
    
    Z1,y=pmagplotlib.plotCDF(fignum,Z1,"Z component",'r',"")
    bounds1=[Z1[minimum],Z1[maximum]]
    pmagplotlib.plotVs(fignum,bounds1,'r','-')
    
    Z2,y=pmagplotlib.plotCDF(fignum,Z2,"Z component",'b',"")
    bounds2=[Z2[minimum],Z2[maximum]]
    pmagplotlib.plotVs(fignum,bounds2,'b','--')
    plt.ylim(0,1)
    
    plt.tight_layout()
    plt.show()
    
def watson_common_mean(Data1,Data2,NumSims=5000,plot='no'):
    """
    Conduct a Watson V test for a common mean on two declination, inclination data sets
    
    This function calculates Watson's V statistic from input files through Monte Carlo
    simulation in order to test whether two populations of directional data could have
    been drawn from a common mean. The critical angle between the two sample mean
    directions and the corresponding McFadden and McElhinny (1990) classification is printed.


    Required Arguments
    ----------
    Data1 : a list of directional data [dec,inc]
    Data2 : a list of directional data [dec,inc]
    
    Optional Arguments
    ----------
    NumSims : number of Monte Carlo simulations (default is 5000)
    plot : the default is no plot ('no'). Putting 'yes' will the plot the CDF from
    the Monte Carlo simulations.
    """   
    pars_1=pmag.fisher_mean(Data1)
    pars_2=pmag.fisher_mean(Data2)

    cart_1=pmag.dir2cart([pars_1["dec"],pars_1["inc"],pars_1["r"]])
    cart_2=pmag.dir2cart([pars_2['dec'],pars_2['inc'],pars_2["r"]])
    Sw=pars_1['k']*pars_1['r']+pars_2['k']*pars_2['r'] # k1*r1+k2*r2
    xhat_1=pars_1['k']*cart_1[0]+pars_2['k']*cart_2[0] # k1*x1+k2*x2
    xhat_2=pars_1['k']*cart_1[1]+pars_2['k']*cart_2[1] # k1*y1+k2*y2
    xhat_3=pars_1['k']*cart_1[2]+pars_2['k']*cart_2[2] # k1*z1+k2*z2
    Rw=np.sqrt(xhat_1**2+xhat_2**2+xhat_3**2)
    V=2*(Sw-Rw)
    # keep weighted sum for later when determining the "critical angle" 
    # let's save it as Sr (notation of McFadden and McElhinny, 1990)
    Sr=Sw 
    
    # do monte carlo simulation of datasets with same kappas as data, 
    # but a common mean
    counter=0
    Vp=[] # set of Vs from simulations
    for k in range(NumSims): 
       
    # get a set of N1 fisher distributed vectors with k1,
    # calculate fisher stats
        Dirp=[]
        for i in range(pars_1["n"]):
            Dirp.append(pmag.fshdev(pars_1["k"]))
        pars_p1=pmag.fisher_mean(Dirp)
    # get a set of N2 fisher distributed vectors with k2, 
    # calculate fisher stats
        Dirp=[]
        for i in range(pars_2["n"]):
            Dirp.append(pmag.fshdev(pars_2["k"]))
        pars_p2=pmag.fisher_mean(Dirp)
    # get the V for these
        Vk=pmag.vfunc(pars_p1,pars_p2)
        Vp.append(Vk)

    # sort the Vs, get Vcrit (95th percentile one)

    Vp.sort()
    k=int(.95*NumSims)
    Vcrit=Vp[k]

    # equation 18 of McFadden and McElhinny, 1990 calculates the critical
    # value of R (Rwc)

    Rwc=Sr-(Vcrit/2)

    # following equation 19 of McFadden and McElhinny (1990) the critical
    # angle is calculated. If the observed angle (also calculated below)
    # between the data set means exceeds the critical angle the hypothesis 
    # of a common mean direction may be rejected at the 95% confidence
    # level. The critical angle is simply a different way to present 
    # Watson's V parameter so it makes sense to use the Watson V parameter
    # in comparison with the critical value of V for considering the test
    # results. What calculating the critical angle allows for is the 
    # classification of McFadden and McElhinny (1990) to be made
    # for data sets that are consistent with sharing a common mean.

    k1=pars_1['k']
    k2=pars_2['k']
    R1=pars_1['r']
    R2=pars_2['r']
    critical_angle=np.degrees(np.arccos(((Rwc**2)-((k1*R1)**2)
                                               -((k2*R2)**2))/
                                              (2*k1*R1*k2*R2)))
    D1=(pars_1['dec'],pars_1['inc'])
    D2=(pars_2['dec'],pars_2['inc'])
    angle=pmag.angle(D1,D2)

    print "Results of Watson V test: "
    print "" 
    print "Watson's V:           " '%.1f' %(V)
    print "Critical value of V:  " '%.1f' %(Vcrit)

    if V<Vcrit:
        print '"Pass": Since V is less than Vcrit, the null hypothesis'
        print 'that the two populations are drawn from distributions'
        print 'that share a common mean direction can not be rejected.'
    elif V>Vcrit:
        print '"Fail": Since V is greater than Vcrit, the two means can'
        print 'be distinguished at the 95% confidence level.'
    print ""    
    print "M&M1990 classification:"
    print "" 
    print "Angle between data set means: " '%.1f'%(angle)
    print "Critical angle for M&M1990:   " '%.1f'%(critical_angle)
    
    if V>Vcrit:
        print ""
    elif V<Vcrit:
        if critical_angle<5:
            print "The McFadden and McElhinny (1990) classification for"
            print "this test is: 'A'"
        elif critical_angle<10:
            print "The McFadden and McElhinny (1990) classification for"
            print "this test is: 'B'"
        elif critical_angle<20:
            print "The McFadden and McElhinny (1990) classification for"
            print "this test is: 'C'"
        else:
            print "The McFadden and McElhinny (1990) classification for"
            print "this test is: 'INDETERMINATE;"

    if plot=='yes':
        CDF={'cdf':1}
        #pmagplotlib.plot_init(CDF['cdf'],5,5)
        p1 = pmagplotlib.plotCDF(CDF['cdf'],Vp,"Watson's V",'r',"")
        p2 = pmagplotlib.plotVs(CDF['cdf'],[V],'g','-')
        p3 = pmagplotlib.plotVs(CDF['cdf'],[Vp[k]],'b','--')
        pmagplotlib.drawFIGS(CDF)
            
def lat_from_inc(inc):
    """
    Calculate paleolatitude from inclination using the dipole equation
    """
    rad=np.pi/180.
    paleo_lat=np.arctan(0.5*np.tan(inc*rad))/rad
    return paleo_lat

def inc_from_lat(lat):
    """
    Calculate inclination predicted from latitude using the dipole equation
    """
    rad=np.pi/180.
    inc=np.arctan(2*np.tan(lat*rad))/rad
    return inc

def plot_net(fignum):
    """
    draws circle and tick marks for equal area projection
    """

# make the perimeter
    pylab.figure(num=fignum)
    pylab.clf()
    pylab.axis("off")
    Dcirc=np.arange(0,361.)
    Icirc=np.zeros(361,'f')
    Xcirc,Ycirc=[],[]
    for k in range(361):
        XY= pmag.dimap(Dcirc[k],Icirc[k])
        Xcirc.append(XY[0])
        Ycirc.append(XY[1])
    pylab.plot(Xcirc,Ycirc,'k')

# put on the tick marks
    Xsym,Ysym=[],[]
    for I in range(10,100,10):
        XY=pmag.dimap(0.,I)
        Xsym.append(XY[0])
        Ysym.append(XY[1])
    pylab.plot(Xsym,Ysym,'k+')
    Xsym,Ysym=[],[]
    for I in range(10,90,10):
        XY=pmag.dimap(90.,I)
        Xsym.append(XY[0])
        Ysym.append(XY[1])
    pylab.plot(Xsym,Ysym,'k+')
    Xsym,Ysym=[],[]
    for I in range(10,90,10):
        XY=pmag.dimap(180.,I)
        Xsym.append(XY[0])
        Ysym.append(XY[1])
    pylab.plot(Xsym,Ysym,'k+')
    Xsym,Ysym=[],[]
    for I in range(10,90,10):
        XY=pmag.dimap(270.,I)
        Xsym.append(XY[0])
        Ysym.append(XY[1])
    pylab.plot(Xsym,Ysym,'k+')
    for D in range(0,360,10):
        Xtick,Ytick=[],[]
        for I in range(4):
            XY=pmag.dimap(D,I)
            Xtick.append(XY[0])
            Ytick.append(XY[1])
        pylab.plot(Xtick,Ytick,'k')
    pylab.axis("equal")
    pylab.tight_layout()

def plot_di(dec,inc,color='k',marker='o',markersize=20,legend='no',label=''):
    """
    Plot declination, inclination data on an equal area plot.

    Before this function is called a plot needs to be initialized with code that looks 
    something like:
    >fignum = 1
    >plt.figure(num=fignum,figsize=(10,10),dpi=160)
    >ipmag.plot_net(fignum)

    Required Arguments
    -----------
    dec : declination being plotted
    inc : inclination being plotted

    Optional Arguments
    -----------
    color : the default color is black. Other colors can be chosen (e.g. 'r')
    marker : the default marker is a circle ('o')
    markersize : default size is 20
    label : the default label is blank ('')
    legend : the default is no legend ('no'). Putting 'yes' will plot a legend.
    """
    X_down = []
    X_up = []
    Y_down = []
    Y_up = []
    for n in range(0,len(dec)):
        XY=pmag.dimap(dec[n],inc[n])
        if inc[n] >= 0:         
            X_down.append(XY[0])
            Y_down.append(XY[1])
        else:
            X_up.append(XY[0])
            Y_up.append(XY[1])

    if len(X_up)>0:
        plt.scatter(X_up,Y_up,facecolors='none', edgecolors=color, 
                    s=markersize, marker=marker, label=label)

    if len(X_down)>0: 
        plt.scatter(X_down,Y_down,facecolors=color, edgecolors=color, 
                    s=markersize, marker=marker, label=label)
    if legend=='yes':
        plt.legend(loc=2)
    plt.tight_layout()

def plot_di_mean(Dec,Inc,a95,color='k',marker='o',markersize=20,label='',legend='no'):
    """
    Plot a mean declination, inclination with alpha_95 ellipse on an equal area plot.

    Before this function is called a plot needs to be initialized with code that looks 
    something like:
    >fignum = 1
    >plt.figure(num=fignum,figsize=(10,10),dpi=160)
    >ipmag.plot_net(fignum)

    Required Parameters
    -----------
    Dec : declination of mean being plotted
    Inc : inclination of mean being plotted
    a95 : a95 confidence ellipse of mean being plotted

    Optional Parameters
    -----------
    color : the default color is black. Other colors can be chosen (e.g. 'r')
    marker : the default is a circle. Other symbols can be chose (e.g. 's')
    label : the default is no label. Labels can be assigned.
    legend : the default is no legend ('no'). Putting 'yes' will plot a legend.
    """
    DI_dimap=pmag.dimap(Dec,Inc)
    if Inc < 0:
        plt.scatter(DI_dimap[0],DI_dimap[1],edgecolor=color ,facecolor='white', marker=marker,s=markersize,label=label)
    if Inc >= 0:
        plt.scatter(DI_dimap[0],DI_dimap[1],color=color,marker=marker,s=markersize,label=label)
    Xcirc,Ycirc=[],[]
    Da95,Ia95=pmag.circ(Dec,Inc,a95)
    if legend=='yes':
        plt.legend(loc=2)
    for k in  range(len(Da95)):
        XY=pmag.dimap(Da95[k],Ia95[k])
        Xcirc.append(XY[0])
        Ycirc.append(XY[1])
    plt.plot(Xcirc,Ycirc,color)
    plt.tight_layout()

def plot_pole(mapname,plong,plat,A95,label='',color='k',marker='o',legend='no'):
    """
    This function plots a paleomagnetic pole and A95 error ellipse on whatever 
    current map projection has been set using the basemap plotting library.

    Required Parameters
    -----------
    mapname : the name of the current map that has been developed using basemap
    plong : the longitude of the paleomagnetic pole being plotted (in degrees E)
    plat : the latitude of the paleomagnetic pole being plotted (in degrees)
    A95 : the A_95 confidence ellipse of the paleomagnetic pole (in degrees)
    
    Optional Parameters
    -----------
    label : a string that is the label for the paleomagnetic pole being plotted
    color : the color desired for the symbol and its A95 ellipse (default is 'k' aka black)
    marker : the marker shape desired for the pole mean symbol (default is 'o' aka a circle)
    legend : the default is no legend ('no'). Putting 'yes' will plot a legend.
    """
    centerlon, centerlat = mapname(plong,plat)
    A95_km=A95*111.32
    mapname.scatter(centerlon,centerlat,20,marker=marker,color=color,label=label,zorder=101)
    equi(mapname, plong, plat, A95_km,color)
    if legend=='yes':
        pylab.legend(loc=2)

def plot_vgp(mapname,plong,plat,label='',color='k',marker='o',legend='no'):
    """
    This function plots a paleomagnetic pole on whatever current map projection
    has been set using the basemap plotting library.

    Required Parameters
    -----------
    mapname : the name of the current map that has been developed using basemap
    plong : the longitude of the paleomagnetic pole being plotted (in degrees E)
    plat : the latitude of the paleomagnetic pole being plotted (in degrees)

    Optional Parameters
    -----------
    color : the color desired for the symbol and its A95 ellipse (default is 'k' aka black)
    marker : the marker shape desired for the pole mean symbol (default is 'o' aka a circle)
    label : the default is no label. Labels can be assigned.
    legend : the default is no legend ('no'). Putting 'yes' will plot a legend.
    """
    centerlon, centerlat = mapname(plong,plat)
    mapname.scatter(centerlon,centerlat,20,marker=marker,color=color,label=label,zorder=100)
    if legend=='yes':
        pylab.legend(loc=2)

def vgp_calc(dataframe,tilt_correction='yes'):
    """
    This function calculates paleomagnetic poles using directional data and site location data within a pandas.DataFrame. The function adds the columns 'paleolatitude', 'pole_lat', 'pole_lon', 'pole_lat_rev', and 'pole_lon_rev' to the dataframe. The '_rev' columns allow for subsequent choice as to which polarity will be used for the VGPs.

    Parameters
    ----------- 
    tilt-correction : 'yes' is the default and uses tilt-corrected data (dec_tc, inc_tc), 'no' uses data that is not tilt-corrected and is geographic coordinates
    dataframe : the name of the pandas.DataFrame containing the data
    dataframe['site_lat'] : the latitude of the site
    dataframe['site_lon'] : the longitude of the site
    dataframe['inc_tc'] : the tilt-corrected inclination (used by default tilt-correction='yes')
    dataframe['dec_tc'] : the tilt-corrected declination (used by default tilt-correction='yes')
    dataframe['inc_is'] : the insitu inclination (used when tilt-correction='no')
    dataframe['dec_is'] : the insitu declination (used when tilt-correction='no')
    """
    dataframe.is_copy = False
    if tilt_correction=='yes':
        #calculate the paleolatitude/colatitude
        dataframe['paleolatitude']=np.degrees(np.arctan(0.5*np.tan(np.radians(dataframe['inc_tc']))))
        dataframe['colatitude']=90-dataframe['paleolatitude']
        #calculate the latitude of the pole
        dataframe['vgp_lat']=np.degrees(np.arcsin(np.sin(np.radians(dataframe['site_lat']))*
                                                             np.cos(np.radians(dataframe['colatitude']))+
                                                             np.cos(np.radians(dataframe['site_lat']))*
                                                             np.sin(np.radians(dataframe['colatitude']))*
                                                             np.cos(np.radians(dataframe['dec_tc']))))
        #calculate the longitudinal difference between the pole and the site (beta)
        dataframe['beta']=np.degrees(np.arcsin((np.sin(np.radians(dataframe['colatitude']))*
                                          np.sin(np.radians(dataframe['dec_tc'])))/
                                         (np.cos(np.radians(dataframe['vgp_lat'])))))
        #generate a boolean array (mask) to use to distinguish between the two possibilities for pole longitude
        #and then calculate pole longitude using the site location and calculated beta
        mask = np.cos(np.radians(dataframe['colatitude']))>np.sin(np.radians(dataframe['site_lat']))*np.sin(np.radians(dataframe['vgp_lat']))
        dataframe['vgp_lon']=np.where(mask,(dataframe['site_lon']+dataframe['beta'])%360.,(dataframe['site_lon']+180-dataframe['beta'])%360.)
        #calculate the antipode of the poles
        dataframe['vgp_lat_rev']=-dataframe['vgp_lat']
        dataframe['vgp_lon_rev']=(dataframe['vgp_lon']-180.)%360. 
        #the 'colatitude' and 'beta' columns were created for the purposes of the pole calculations
        #but aren't of further use and are deleted
        del dataframe['colatitude']
        del dataframe['beta']
    if tilt_correction=='no':
        #calculate the paleolatitude/colatitude
        dataframe['paleolatitude']=np.degrees(np.arctan(0.5*np.tan(np.radians(dataframe['inc_is']))))
        dataframe['colatitude']=90-dataframe['paleolatitude']
        #calculate the latitude of the pole
        dataframe['vgp_lat']=np.degrees(np.arcsin(np.sin(np.radians(dataframe['site_lat']))*
                                                             np.cos(np.radians(dataframe['colatitude']))+
                                                             np.cos(np.radians(dataframe['site_lat']))*
                                                             np.sin(np.radians(dataframe['colatitude']))*
                                                             np.cos(np.radians(dataframe['dec_is']))))
        #calculate the longitudinal difference between the pole and the site (beta)
        dataframe['beta']=np.degrees(np.arcsin((np.sin(np.radians(dataframe['colatitude']))*
                                          np.sin(np.radians(dataframe['dec_is'])))/
                                         (np.cos(np.radians(dataframe['vgp_lat'])))))
        #generate a boolean array (mask) to use to distinguish between the two possibilities for pole longitude
        #and then calculate pole longitude using the site location and calculated beta
        mask = np.cos(np.radians(dataframe['colatitude']))>np.sin(np.radians(dataframe['site_lat']))*np.sin(np.radians(dataframe['vgp_lat']))
        dataframe['vgp_lon']=np.where(mask,(dataframe['site_lon']+dataframe['beta'])%360.,(dataframe['site_lon']+180-dataframe['beta'])%360.)
        #calculate the antipode of the poles
        dataframe['vgp_lat_rev']=-dataframe['vgp_lat']
        dataframe['vgp_lon_rev']=(dataframe['vgp_lon']-180.)%360. 
        #the 'colatitude' and 'beta' columns were created for the purposes of the pole calculations
        #but aren't of further use and are deleted
        del dataframe['colatitude']
        del dataframe['beta']

def sb_vgp_calc(dataframe):
    """
    This function calculates the angular dispersion of VGPs and corrects
    for within site dispersion to return a value S_b. The input data
    needs to be within a pandas Dataframe. The function also plots the
    VGPs and their associated Fisher mean on a projection centered on
    the mean.
    
    Parameters
    ----------- 
    dataframe : the name of the pandas.DataFrame containing the data
    
    the data frame needs to contain these columns:
    dataframe['site_lat'] : latitude of the site
    dataframe['site_lon'] : longitude of the site
    dataframe['inc_tc'] : tilt-corrected inclination
    dataframe['dec_tc'] : tilt-corrected declination
    dataframe['k'] : fisher precision parameter for directions
    dataframe['vgp_lat'] : VGP latitude
    dataframe['vgp_lon'] : VGP longitude
    """

    # calculate the mean from the directional data
    dataframe_dirs=[]
    for n in range(0,len(dataframe)): 
        dataframe_dirs.append([dataframe['dec_tc'][n],
                               dataframe['inc_tc'][n],1.])
    dataframe_dir_mean=pmag.fisher_mean(dataframe_dirs)

    # calculate the mean from the vgp data
    dataframe_poles=[]
    dataframe_pole_lats=[]
    dataframe_pole_lons=[]
    for n in range(0,len(dataframe)): 
        dataframe_poles.append([dataframe['vgp_lon'][n],
                                dataframe['vgp_lat'][n],1.])
        dataframe_pole_lats.append(dataframe['vgp_lat'][n])
        dataframe_pole_lons.append(dataframe['vgp_lon'][n])                            
    dataframe_pole_mean=pmag.fisher_mean(dataframe_poles)

    # calculate mean paleolatitude from the directional data
    dataframe['paleolatitude']=ipmag.lat_from_inc(dataframe_dir_mean['inc'])

    angle_list=[]
    for n in range(0,len(dataframe)):
        angle=pmag.angle([dataframe['vgp_lon'][n],dataframe['vgp_lat'][n]],
                         [dataframe_pole_mean['dec'],dataframe_pole_mean['inc']])
        angle_list.append(angle[0])
    dataframe['delta_mean-pole']=angle_list

    # use eq. 2 of Cox (1970) to translate the directional precision parameter
    # into pole coordinates using the assumption of a Fisherian distribution in
    # directional coordinates and the paleolatitude as calculated from mean
    # inclination using the dipole equation
    dataframe['K']=dataframe['k']/(0.125*(5+18*np.sin(np.deg2rad(dataframe['paleolatitude']))**2
                                          +9*np.sin(np.deg2rad(dataframe['paleolatitude']))**4))
    dataframe['Sw']=81/(dataframe['K']**0.5)

    summation=0
    N=0
    for n in range(0,len(dataframe)):
        quantity=dataframe['delta_mean-pole'][n]**2-dataframe['Sw'][n]**2/dataframe['n'][n]
        summation+=quantity
        N+=1

    Sb=((1.0/(N-1.0))*summation)**0.5
    
    plt.figure(figsize=(6, 6))
    m = Basemap(projection='ortho',lat_0=dataframe_pole_mean['inc'],
                lon_0=dataframe_pole_mean['dec'],resolution='c',area_thresh=50000)
    m.drawcoastlines(linewidth=0.25)
    m.fillcontinents(color='bisque',lake_color='white',zorder=1)
    m.drawmapboundary(fill_color='white')
    m.drawmeridians(np.arange(0,360,30))
    m.drawparallels(np.arange(-90,90,30))
    
    ipmag.plot_vgp(m,dataframe_pole_lons,dataframe_pole_lats,dataframe_pole_lons)
    ipmag.plot_pole(m,dataframe_pole_mean['dec'],dataframe_pole_mean['inc'],
                    dataframe_pole_mean['alpha95'],color='r',marker='s')
    return Sb

def make_di_block(dec,inc):
    """
    Some pmag.py functions require a list of unit vectors [dec,inc,1.] as input. This
    function takes declination and inclination data and make it into such a list
    """
    di_block=[]
    for n in range(0,len(dec)):
        di_block.append([dec[n],inc[n],1.0])
    return di_block

def shoot(lon, lat, azimuth, maxdist=None):
    """
    This function enables A95 error ellipses to be drawn in basemap around paleomagnetic
    poles in conjunction with equi
    (from: http://www.geophysique.be/2011/02/20/matplotlib-basemap-tutorial-09-drawing-circles/)
    """
    glat1 = lat * np.pi / 180.
    glon1 = lon * np.pi / 180.
    s = maxdist / 1.852
    faz = azimuth * np.pi / 180.
 
    EPS= 0.00000000005
    if ((np.abs(np.cos(glat1))<EPS) and not (np.abs(np.sin(faz))<EPS)):
        alert("Only N-S courses are meaningful, starting at a pole!")
 
    a=6378.13/1.852
    f=1/298.257223563
    r = 1 - f
    tu = r * np.tan(glat1)
    sf = np.sin(faz)
    cf = np.cos(faz)
    if (cf==0):
        b=0.
    else:
        b=2. * np.arctan2 (tu, cf)
 
    cu = 1. / np.sqrt(1 + tu * tu)
    su = tu * cu
    sa = cu * sf
    c2a = 1 - sa * sa
    x = 1. + np.sqrt(1. + c2a * (1. / (r * r) - 1.))
    x = (x - 2.) / x
    c = 1. - x
    c = (x * x / 4. + 1.) / c
    d = (0.375 * x * x - 1.) * x
    tu = s / (r * a * c)
    y = tu
    c = y + 1
    while (np.abs (y - c) > EPS):
 
        sy = np.sin(y)
        cy = np.cos(y)
        cz = np.cos(b + y)
        e = 2. * cz * cz - 1.
        c = y
        x = e * cy
        y = e + e - 1.
        y = (((sy * sy * 4. - 3.) * y * cz * d / 6. + x) *
              d / 4. - cz) * sy * d + tu
 
    b = cu * cy * cf - su * sy
    c = r * np.sqrt(sa * sa + b * b)
    d = su * cy + cu * sy * cf
    glat2 = (np.arctan2(d, c) + np.pi) % (2*np.pi) - np.pi
    c = cu * cy - su * sy * cf
    x = np.arctan2(sy * sf, c)
    c = ((-3. * c2a + 4.) * f + 4.) * c2a * f / 16.
    d = ((e * cy * c + cz) * sy * c + y) * sa
    glon2 = ((glon1 + x - (1. - c) * d * f + np.pi) % (2*np.pi)) - np.pi    
 
    baz = (np.arctan2(sa, b) + np.pi) % (2 * np.pi)
 
    glon2 *= 180./np.pi
    glat2 *= 180./np.pi
    baz *= 180./np.pi
 
    return (glon2, glat2, baz)

def equi(m, centerlon, centerlat, radius, color):
    """
    This function enables A95 error ellipses to be drawn in basemap around paleomagnetic poles
    in conjunction with shoot
    (from: http://www.geophysique.be/2011/02/20/matplotlib-basemap-tutorial-09-drawing-circles/).
    """
    glon1 = centerlon
    glat1 = centerlat
    X = []
    Y = []
    for azimuth in range(0, 360):
        glon2, glat2, baz = shoot(glon1, glat1, azimuth, radius)
        X.append(glon2)
        Y.append(glat2)
    X.append(X[0])
    Y.append(Y[0])
 
    X,Y = m(X,Y)
    plt.plot(X,Y,color)

def combine_magic(filenames, outfile):
    """
    Takes a list of magic-formatted files, concatenates them, and creates a single file.
    Returns true if the operation was successful.
    
    """
    datasets = []
    if not filenames:
        print "You must provide at least one file"
        return False
    for infile in filenames:
        if not os.path.isfile(infile):
            print "{} is not a valid file name".format(infile)
            return False
        dataset, file_type = pmag.magic_read(infile)
        print "File ",infile," read in with ",len(dataset), " records"
        for rec in dataset:
            datasets.append(rec)

    Recs, keys = pmag.fillkeys(datasets)
    pmag.magic_write(outfile,Recs,file_type)
    print "All records stored in ",outfile
    return True

def make_aniso_depthplot(ani_file, meas_file, samp_file, age_file=None, fmt='svg', dmin=-1, dmax=-1, depth_scale='sample_composite_depth'):
    
    """
    returns matplotlib figure with anisotropy data plotted against depth
    """
    dmin, dmax = float(dmin), float(dmax)
    pcol=3
    isbulk=0 # tests if there are bulk susceptibility measurements
    AniData,file_type=pmag.magic_read(ani_file)  # read in tensor elements
    if not age_file:
        Samps,file_type=pmag.magic_read(samp_file)  # read in sample depth info from er_sample.txt format file
    else:
        Samps,file_type=pmag.magic_read(age_file)  # read in sample age info from er_ages.txt format file
        age_unit=Samps[0]['age_unit']
    for s in Samps:s['er_sample_name']=s['er_sample_name'].upper() # change to upper case for every sample name
    Meas,file_type=pmag.magic_read(meas_file)
    if file_type=='magic_measurements':isbulk=1
    Data=[]
    Bulks=[]
    BulkDepths=[]
    for rec in AniData:
        samprecs=pmag.get_dictitem(Samps,'er_sample_name',rec['er_sample_name'].upper(),'T') # look for depth record for this sample
        sampdepths=pmag.get_dictitem(samprecs,depth_scale,'','F') # see if there are non-blank depth data
        if dmax!=-1:
            sampdepths=pmag.get_dictitem(sampdepths,depth_scale,dmax,'max') # fishes out records within depth bounds
            sampdepths=pmag.get_dictitem(sampdepths,depth_scale,dmin,'min')
        if len(sampdepths)>0: # if there are any....
            rec['core_depth'] = sampdepths[0][depth_scale] # set the core depth of this record
            Data.append(rec) # fish out data with core_depth
            if isbulk:  # if there are bulk data
                chis=pmag.get_dictitem(Meas,'er_specimen_name',rec['er_specimen_name'],'T')
                chis=pmag.get_dictitem(chis,'measurement_chi_volume','','F') # get the non-zero values for this specimen
                if len(chis)>0: # if there are any....
                    Bulks.append(1e6*float(chis[0]['measurement_chi_volume'])) # put in microSI
                    BulkDepths.append(float(sampdepths[0][depth_scale]))
    if len(Bulks)>0: # set min and max bulk values
        bmin=min(Bulks)
        bmax=max(Bulks)
    xlab="Depth (m)"
    if len(Data)>0:
        location=Data[0]['er_location_name']
    else:
        print 'no data to plot'
        return False, False
        #sys.exit()
    # collect the data for plotting tau and V3_inc
    Depths,Tau1,Tau2,Tau3,V3Incs,P=[],[],[],[],[],[]
    Axs=[] # collect the plot ids
    if len(Bulks)>0: pcol+=1
    s1=pmag.get_dictkey(Data,'anisotropy_s1','f') # get all the s1 values from Data as floats
    s2=pmag.get_dictkey(Data,'anisotropy_s2','f')
    s3=pmag.get_dictkey(Data,'anisotropy_s3','f')
    s4=pmag.get_dictkey(Data,'anisotropy_s4','f')
    s5=pmag.get_dictkey(Data,'anisotropy_s5','f')
    s6=pmag.get_dictkey(Data,'anisotropy_s6','f')
    Depths=pmag.get_dictkey(Data,'core_depth','f')
    Ss=np.array([s1,s4,s5,s4,s2,s6,s5,s6,s3]).transpose() # make an array
    Ts=np.reshape(Ss,(len(Ss),3,-1)) # and re-shape to be n-length array of 3x3 sub-arrays
    for k in range(len(Depths)):
        tau,Evecs= pmag.tauV(Ts[k]) # get the sorted eigenvalues and eigenvectors
        v3=pmag.cart2dir(Evecs[2])[1] # convert to inclination of the minimum eigenvector
        V3Incs.append(v3)
        Tau1.append(tau[0])
        Tau2.append(tau[1])
        Tau3.append(tau[2])
        P.append(tau[0]/tau[2])
    if len(Depths)>0:
        if dmax==-1:
            dmax=max(Depths)
            dmin=min(Depths)
        tau_max=max(Tau1)
        tau_min=min(Tau3)
        P_max=max(P)
        P_min=min(P)
        #dmax=dmax+.05*dmax
        #dmin=dmin-.05*dmax

        main_plot = plt.figure(1,figsize=(10,8)) # make the figure
        
        version_num=pmag.get_version()
        plt.figtext(.02,.01,version_num) # attach the pmagpy version number
        ax=plt.subplot(1,pcol,1) # make the first column
        Axs.append(ax)
        ax.plot(Tau1,Depths,'rs') 
        ax.plot(Tau2,Depths,'b^') 
        ax.plot(Tau3,Depths,'ko')
        ax.axis([tau_min,tau_max,dmax,dmin])
        ax.set_xlabel('Eigenvalues')
        if depth_scale=='sample_core_depth':
            ax.set_ylabel('Depth (mbsf)')
        elif depth_scale=='age':
            ax.set_ylabel('Age ('+age_unit+')')
        else:
            ax.set_ylabel('Depth (mcd)')
        ax2=plt.subplot(1,pcol,2) # make the second column
        ax2.plot(P,Depths,'rs') 
        ax2.axis([P_min,P_max,dmax,dmin])
        ax2.set_xlabel('P')
        ax2.set_title(location)
        Axs.append(ax2)
        ax3=plt.subplot(1,pcol,3)
        Axs.append(ax3)
        ax3.plot(V3Incs,Depths,'ko') 
        ax3.axis([0,90,dmax,dmin])
        ax3.set_xlabel('V3 Inclination')
        if pcol==4:
            ax4=plt.subplot(1,pcol,4)
            Axs.append(ax4)
            ax4.plot(Bulks,BulkDepths,'bo') 
            ax4.axis([bmin-1,bmax+1,dmax,dmin])
            ax4.set_xlabel('Bulk Susc. (uSI)')
        for x in Axs:pmagplotlib.delticks(x) # this makes the x-tick labels more reasonable - they were overcrowded using the defaults
        fig_name = location + '_ani_depthplot.' + fmt
        return main_plot, fig_name


def download_magic(infile, dir_path='.', input_dir_path='.'):
    """
    takes the name of a text file downloaded from the MagIC database and unpacks it into magic-formatted files.
    by default, download_magic assumes that you are doing everything in your current directory.
    if not, you may provide optional arguments dir_path (where you want the results to go) and input_dir_path (where the dowloaded file is).
    """
    f=open(input_dir_path+'/'+infile,'rU')
    File=f.readlines()
    LN=0
    type_list=[]
    filenum=0
    while LN<len(File)-1:
        line=File[LN]
        file_type=line.split('\t')[1]
        file_type=file_type.lower()
        if file_type=='delimited':file_type=Input[skip].split('\t')[2]
        if file_type[-1]=="\n":file_type=file_type[:-1]
        print 'working on: ',repr(file_type)
        if file_type not in type_list:
            type_list.append(file_type)
        else:
            filenum+=1 
        LN+=1
        line=File[LN]
        keys=line.replace('\n','').split('\t')
        if keys[0][0]=='.':
            keys=line.replace('\n','').replace('.','').split('\t')
            keys.append('RecNo') # cludge for new MagIC download format
        LN+=1
        Recs=[]
        while LN<len(File):
            line=File[LN]
            if line[:4]==">>>>" and len(Recs)>0:
                if filenum==0:
                    outfile=dir_path+"/"+file_type.strip()+'.txt'
                else:
                    outfile=dir_path+"/"+file_type.strip()+'_'+str(filenum)+'.txt' 
                NewRecs=[]
                for rec in Recs:
                    if 'magic_method_codes' in rec.keys():
                        meths=rec['magic_method_codes'].split(":")
                        if len(meths)>0:
                            methods=""
                            for meth in meths: methods=methods+meth.strip()+":" # get rid of nasty spaces!!!!!!
                            rec['magic_method_codes']=methods[:-1]
                    NewRecs.append(rec)
                pmag.magic_write(outfile,Recs,file_type)
                print file_type," data put in ",outfile
                if file_type =='pmag_specimens' and 'magic_measurements.txt' in File and 'measurement_step_min' in File and 'measurement_step_max' in File: # sort out zeq_specimens and thellier_specimens
                    os.system('mk_redo.py')
                    os.system('zeq_magic_redo.py')
                    os.system('thellier_magic_redo.py')
                    type_list.append('zeq_specimens')
                    type_list.append('thellier_specimens')
                Recs=[]
                LN+=1
                break
            else:
                rec=line.split('\t')
                Rec={}
                if len(rec)==len(keys):
                    for k in range(len(rec)):
                       Rec[keys[k]]=rec[k]
                    Recs.append(Rec)
                else:
                    print 'WARNING:  problem in file with line: '
                    print line
                    print 'skipping....'
                LN+=1
    if len(Recs)>0:
        if filenum==0:
            outfile=dir_path+"/"+file_type.strip()+'.txt'
        else:
            outfile=dir_path+"/"+file_type.strip()+'_'+str(filenum)+'.txt' 
        NewRecs=[]
        for rec in Recs:
            if 'magic_method_codes' in rec.keys():
                meths=rec['magic_method_codes'].split(":")
                if len(meths)>0:
                    methods=""
                    for meth in meths: methods=methods+meth.strip()+":" # get rid of nasty spaces!!!!!!
                    rec['magic_method_codes']=methods[:-1]
            NewRecs.append(rec)
        pmag.magic_write(outfile,Recs,file_type)
        print file_type," data put in ",outfile
# look through locations table and create separate directories for each location
    locs,locnum=[],1
    if 'er_locations' in type_list:
        locs,file_type=pmag.magic_read(dir_path+'/er_locations.txt')
    if len(locs)>0: # at least one location
        for loc in locs:
            print 'location_'+str(locnum)+": ",loc['er_location_name']
            lpath=dir_path+'/Location_'+str(locnum)
            locnum+=1
            try:
                os.mkdir(lpath)
            except:
                print 'directory ',lpath,' already exists - overwrite everything [y/n]?'
                ans=raw_input()
                if ans=='n':sys.exit()
            for f in type_list:
                print 'unpacking: ',dir_path+'/'+f+'.txt'
                recs,file_type=pmag.magic_read(dir_path+'/'+f+'.txt')
                print len(recs),' read in'
                if 'results' not in f:
                    lrecs=pmag.get_dictitem(recs,'er_location_name',loc['er_location_name'],'T')
                    if len(lrecs)>0:
                        pmag.magic_write(lpath+'/'+f+'.txt',lrecs,file_type)
                        print len(lrecs),' stored in ',lpath+'/'+f+'.txt'
                else:
                    lrecs=pmag.get_dictitem(recs,'er_location_names',loc['er_location_name'],'T')
                    if len(lrecs)>0:
                        pmag.magic_write(lpath+'/'+f+'.txt',lrecs,file_type)
                        print len(lrecs),' stored in ',lpath+'/'+f+'.txt'
    return True


def upload_magic(concat=0, All=0, dir_path='.'):
    """
    Finds all magic files in a given directory, and compiles them into an upload.txt file which can be uploaded into the MagIC database.  
    """
    files_list = ["er_expeditions.txt", "er_locations.txt", "er_samples.txt", "er_specimens.txt", "er_sites.txt", "er_ages.txt", "er_citations.txt", "er_mailinglist.txt", "magic_measurements.txt", "rmag_hysteresis.txt", "rmag_anisotropy.txt", "rmag_remanence.txt", "rmag_results.txt", "pmag_specimens.txt", "pmag_samples.txt", "pmag_sites.txt", "pmag_results.txt", "pmag_criteria.txt", "magic_instruments.txt"]
    file_names = [os.path.join(dir_path, f) for f in files_list]
    
    # begin the upload process
    up = os.path.join(dir_path, "upload.txt")
    RmKeys=['citation_label','compilation','calculation_type','average_n_lines','average_n_planes','specimen_grade','site_vgp_lat','site_vgp_lon','direction_type','specimen_Z','magic_instrument_codes','cooling_rate_corr','cooling_rate_mcd','anisotropy_atrm_alt','anisotropy_apar_perc','anisotropy_F','anisotropy_F_crit','specimen_scat','specimen_gmax','specimen_frac','site_vadm','site_lon','site_vdm','site_lat', 'measurement_chi','specimen_k_prime','external_database_names','external_database_ids']
    print "Removing: ",RmKeys
    last=file_names[-1]
    methods,first_file=[],1
    for file in file_names:
    # read in the data
        Data,file_type=pmag.magic_read(file)
        if file_type!="bad_file":
            print "file ",file," successfully read in"
            if len(RmKeys)>0:
                for rec in Data:
                    for key in RmKeys: 
                        if key=='specimen_Z' and key in rec.keys():
                            rec[key]='specimen_z' # change  # change this to lower case
                        if key in rec.keys():del rec[key] # get rid of unwanted keys
            if file_type=='er_samples': # check to only upload top priority orientation record!
                NewSamps,Done=[],[]
                for rec in Data:
                    if rec['er_sample_name'] not in Done:
                        orient,az_type=pmag.get_orient(Data,rec['er_sample_name'])
                        NewSamps.append(orient)
                        Done.append(rec['er_sample_name'])
                Data=NewSamps           
                print 'only highest priority orientation record from er_samples.txt read in '
            if file_type=='er_specimens': #  only specimens that have sample names
                NewData,SpecDone=[],[]
                for rec in Data:
                    if rec['er_sample_name'] in Done:
                        NewData.append(rec)
                        SpecDone.append(rec['er_specimen_name'])
                    else: 
                        print 'no sample record found for: ' 
                        print rec
                Data=NewData           
                print 'only measurements that have specimen/sample info'
            if file_type=='magic_measurments': #  only measurments that have specimen names
                NewData=[]
                for rec in Data:
                    if rec['er_sample_name'] in SpecDone:
                        NewData.append(rec)
                    else: 
                        print 'no specimen record found for: ' 
                        print rec
                Data=NewData           
    # write out the data
            if len(Data)>0:
                if first_file==1:
                    keystring=pmag.first_rec(up,Data[0],file_type)
                    first_file=0
                else:  
                    keystring=pmag.first_up(up,Data[0],file_type)
                for rec in Data:
    # collect the method codes
                    if "magic_method_codes" in rec.keys():
                        meths=rec["magic_method_codes"].split(':')
                        for meth in meths:
                            if meth.strip() not in methods:
                                if meth.strip()!="LP-DIR-":
                                    methods.append(meth.strip())
                    pmag.putout(up,keystring,rec)

    # write out the file separator
            f=open(up,'a')
            f.write('>>>>>>>>>>\n')
            f.close()
            print file_type, 'written to ',up
        else:
            print file, 'is bad or non-existent - skipping '

    # write out the methods table
    first_rec,MethRec=1,{}
    for meth in methods:
        MethRec["magic_method_code"]=meth
        if first_rec==1:meth_keys=pmag.first_up(up,MethRec,"magic_methods")
        first_rec=0
        pmag.putout(up,meth_keys,MethRec)
    if concat==1:
        f=open(up,'a')
        f.write('>>>>>>>>>>\n')
        f.close()

    # 
    if up:
        import validate_upload
        validated = False
        if validate_upload.read_upload(up):
           validated = True

    else:
        print "no data found, upload file not created"
        return False

    print "Finished preparing upload.txt file "
    if not validated:
        print "-W- validation of upload file has failed.\nPlease fix above errors and try again.\nYou may run into problems if you try to upload this file to the MagIC database" 


def make_aniso_depthplot(ani_file, meas_file, samp_file, age_file=None, fmt='svg', dmin=-1, dmax=-1, depth_scale='sample_composite_depth'):
    
    """
    returns matplotlib figure with anisotropy data plotted against depth
    """
    dmin, dmax = float(dmin), float(dmax)
    pcol=3
    isbulk=0 # tests if there are bulk susceptibility measurements
    AniData,file_type=pmag.magic_read(ani_file)  # read in tensor elements
    if not age_file:
        Samps,file_type=pmag.magic_read(samp_file)  # read in sample depth info from er_sample.txt format file
    else:
        Samps,file_type=pmag.magic_read(age_file)  # read in sample age info from er_ages.txt format file
        age_unit=Samps[0]['age_unit']
    for s in Samps:s['er_sample_name']=s['er_sample_name'].upper() # change to upper case for every sample name
    Meas,file_type=pmag.magic_read(meas_file)
    if file_type=='magic_measurements':isbulk=1
    Data=[]
    Bulks=[]
    BulkDepths=[]
    for rec in AniData:
        samprecs=pmag.get_dictitem(Samps,'er_sample_name',rec['er_sample_name'].upper(),'T') # look for depth record for this sample
        sampdepths=pmag.get_dictitem(samprecs,depth_scale,'','F') # see if there are non-blank depth data
        if dmax!=-1:
            sampdepths=pmag.get_dictitem(sampdepths,depth_scale,dmax,'max') # fishes out records within depth bounds
            sampdepths=pmag.get_dictitem(sampdepths,depth_scale,dmin,'min')
        if len(sampdepths)>0: # if there are any....
            rec['core_depth'] = sampdepths[0][depth_scale] # set the core depth of this record
            Data.append(rec) # fish out data with core_depth
            if isbulk:  # if there are bulk data
                chis=pmag.get_dictitem(Meas,'er_specimen_name',rec['er_specimen_name'],'T')
                chis=pmag.get_dictitem(chis,'measurement_chi_volume','','F') # get the non-zero values for this specimen
                if len(chis)>0: # if there are any....
                    Bulks.append(1e6*float(chis[0]['measurement_chi_volume'])) # put in microSI
                    BulkDepths.append(float(sampdepths[0][depth_scale]))
    if len(Bulks)>0: # set min and max bulk values
        bmin=min(Bulks)
        bmax=max(Bulks)
    xlab="Depth (m)"
    if len(Data)>0:
        location=Data[0]['er_location_name']
    else:
        print 'no data to plot'
        return False, False
        #sys.exit()
    # collect the data for plotting tau and V3_inc
    Depths,Tau1,Tau2,Tau3,V3Incs,P=[],[],[],[],[],[]
    Axs=[] # collect the plot ids
    if len(Bulks)>0: pcol+=1
    s1=pmag.get_dictkey(Data,'anisotropy_s1','f') # get all the s1 values from Data as floats
    s2=pmag.get_dictkey(Data,'anisotropy_s2','f')
    s3=pmag.get_dictkey(Data,'anisotropy_s3','f')
    s4=pmag.get_dictkey(Data,'anisotropy_s4','f')
    s5=pmag.get_dictkey(Data,'anisotropy_s5','f')
    s6=pmag.get_dictkey(Data,'anisotropy_s6','f')
    Depths=pmag.get_dictkey(Data,'core_depth','f')
    Ss=np.array([s1,s4,s5,s4,s2,s6,s5,s6,s3]).transpose() # make an array
    Ts=np.reshape(Ss,(len(Ss),3,-1)) # and re-shape to be n-length array of 3x3 sub-arrays
    for k in range(len(Depths)):
        tau,Evecs= pmag.tauV(Ts[k]) # get the sorted eigenvalues and eigenvectors
        v3=pmag.cart2dir(Evecs[2])[1] # convert to inclination of the minimum eigenvector
        V3Incs.append(v3)
        Tau1.append(tau[0])
        Tau2.append(tau[1])
        Tau3.append(tau[2])
        P.append(tau[0]/tau[2])
    if len(Depths)>0:
        if dmax==-1:
            dmax=max(Depths)
            dmin=min(Depths)
        tau_max=max(Tau1)
        tau_min=min(Tau3)
        P_max=max(P)
        P_min=min(P)
        #dmax=dmax+.05*dmax
        #dmin=dmin-.05*dmax

        main_plot = plt.figure(1,figsize=(10,8)) # make the figure
        
        version_num=pmag.get_version()
        plt.figtext(.02,.01,version_num) # attach the pmagpy version number
        ax=plt.subplot(1,pcol,1) # make the first column
        Axs.append(ax)
        ax.plot(Tau1,Depths,'rs') 
        ax.plot(Tau2,Depths,'b^') 
        ax.plot(Tau3,Depths,'ko')
        ax.axis([tau_min,tau_max,dmax,dmin])
        ax.set_xlabel('Eigenvalues')
        if depth_scale=='sample_core_depth':
            ax.set_ylabel('Depth (mbsf)')
        elif depth_scale=='age':
            ax.set_ylabel('Age ('+age_unit+')')
        else:
            ax.set_ylabel('Depth (mcd)')
        ax2=plt.subplot(1,pcol,2) # make the second column
        ax2.plot(P,Depths,'rs') 
        ax2.axis([P_min,P_max,dmax,dmin])
        ax2.set_xlabel('P')
        ax2.set_title(location)
        Axs.append(ax2)
        ax3=plt.subplot(1,pcol,3)
        Axs.append(ax3)
        ax3.plot(V3Incs,Depths,'ko') 
        ax3.axis([0,90,dmax,dmin])
        ax3.set_xlabel('V3 Inclination')
        if pcol==4:
            ax4=plt.subplot(1,pcol,4)
            Axs.append(ax4)
            ax4.plot(Bulks,BulkDepths,'bo') 
            ax4.axis([bmin-1,bmax+1,dmax,dmin])
            ax4.set_xlabel('Bulk Susc. (uSI)')
        for x in Axs:pmagplotlib.delticks(x) # this makes the x-tick labels more reasonable - they were overcrowded using the defaults
        fig_name = location + '_ani_depthplot.' + fmt
        return main_plot, fig_name

def specimens_results_magic(infile='pmag_specimens.txt', measfile='magic_measurements.txt', sampfile='er_samples.txt', sitefile='er_sites.txt', agefile='er_ages.txt', specout='er_specimens.txt', sampout='pmag_samples.txt', siteout='pmag_sites.txt', resout='pmag_results.txt', critout='pmag_criteria.txt', instout='magic_instruments.txt', plotsites = False, fmt='svg', dir_path='.', cors=[], priorities=['DA-AC-ARM','DA-AC-TRM'], coord='g', user='', vgps_level='site', do_site_intensity=True, DefaultAge=["none"], avg_directions_by_sample=False, avg_intensities_by_sample=False, avg_all_components=False, avg_by_polarity=False, skip_directions=False, skip_intensities=False, use_sample_latitude=False, use_paleolatitude=False, use_criteria='default'):
    """
    cors is 'corrections' 
    long docstring goes here
    DefaultAge should be [min, max, units]
    use_criteria may be 'default', 'existing', or 'none'
    """
    # initialize some variables
    Comps=[] # list of components
    version_num=pmag.get_version()
    args=sys.argv
    model_lat_file=""
    Dcrit,Icrit,nocrit=0,0,0
    corrections=[]
    nocorrection=['DA-NL','DA-AC','DA-CR']

    # do some data adjustments
    for cor in cors:
        nocorrection.remove('DA-'+cor)
        corrections.append('DA-'+cor)
            
    for p in priorities:
        if not p.startswith('DA-AC-'):
            p='DA-AC-'+p

    # translate coord into coords
    if coord=='s':coords=['-1']
    if coord=='g':coords=['0']
    if coord=='t':coords=['100']
    if coord=='b':coords=['0','100']

    if vgps_level == 'sample':
        vgps=1 # save sample level VGPS/VADMs
    else:
        vgps = 0 # site level

    if do_site_intensity:
        nositeints=0
    else:
        nositeints=1

    # chagne these all to True/False instead of 1/0

    if not skip_intensities:
        # set model lat and
        if use_sample_latitude and use_paleolatitude:
            print "you should set a paleolatitude file OR use present day lat - not both"
            return False
        elif use_sample_latitude:
            get_model_lat = 1
        elif use_paleolatitude:
            get_model_lat = 2
            try:
                model_lat_file=dir_path+'/'+args[ind+1]
                get_model_lat=2
                mlat=open(model_lat_file,'rU')
                ModelLats=[]
                for line in mlat.readlines():
                    ModelLat={}
                    tmp=line.split()
                    ModelLat["er_site_name"]=tmp[0]
                    ModelLat["site_model_lat"]=tmp[1]
                    ModelLat["er_sample_name"]=tmp[0] 
                    ModelLat["sample_lat"]=tmp[1]
                    ModelLats.append(ModelLat)
            except:
                print "use_paleolatitude option requires a valid paleolatitude file"
        else:
            get_model_lat = 0 # skips VADM calculation entirely
                
                
    if plotsites and not skip_directions: # plot by site - set up plot window
        import pmagplotlib
        EQ={}
        EQ['eqarea']=1
        pmagplotlib.plot_init(EQ['eqarea'],5,5) # define figure 1 as equal area projection
        pmagplotlib.plotNET(EQ['eqarea']) # I don't know why this has to be here, but otherwise the first plot never plots...
        pmagplotlib.drawFIGS(EQ)
            
    infile = os.path.join(dir_path, infile)
    measfile = os.path.join(dir_path, measfile)
    instout = os.path.join(dir_path, instout)
    sampfile = os.path.join(dir_path, sampfile)
    sitefile = os.path.join(dir_path, sitefile)
    agefile = os.path.join(dir_path, agefile)
    specout = os.path.join(dir_path, specout)
    sampout = os.path.join(dir_path, sampout)
    siteout = os.path.join(dir_path, siteout)
    resout = os.path.join(dir_path, resout)
    critout = os.path.join(dir_path, critout)



    if use_criteria == 'none':
        Dcrit,Icrit,nocrit=1,1,1 # no selection criteria
        crit_data=pmag.default_criteria(nocrit)
    elif use_criteria == 'default':
        crit_data=pmag.default_criteria(nocrit) # use default criteria
    elif use_criteria == 'existing':
	crit_data,file_type=pmag.magic_read(critout) # use pmag_criteria file
	print "Acceptance criteria read in from ", critout
    accept={}
    for critrec in crit_data:
        for key in critrec.keys():
# need to migrate specimen_dang to specimen_int_dang for intensity data using old format
            if 'IE-SPEC' in critrec.keys() and 'specimen_dang' in critrec.keys() and 'specimen_int_dang' not in critrec.keys():
                critrec['specimen_int_dang']=critrec['specimen_dang']
                del critrec['specimen_dang']   
# need to get rid of ron shaars sample_int_sigma_uT
            if 'sample_int_sigma_uT' in critrec.keys():
                critrec['sample_int_sigma']='%10.3e'%(eval(critrec['sample_int_sigma_uT'])*1e-6)
            if key not in accept.keys() and critrec[key]!='':
                accept[key]=critrec[key]
    #
    if use_criteria == 'default':
        pmag.magic_write(critout,[accept],'pmag_criteria')
        print "\n Pmag Criteria stored in ",critout,'\n'

        #
# now we're done slow dancing
#
    SiteNFO,file_type=pmag.magic_read(sitefile) # read in site data - has the lats and lons
    SampNFO,file_type=pmag.magic_read(sampfile) # read in site data - has the lats and lons
    height_nfo=pmag.get_dictitem(SiteNFO,'site_height','','F') # find all the sites with height info.  
    if agefile !="":AgeNFO,file_type=pmag.magic_read(agefile) # read in the age information
    Data,file_type=pmag.magic_read(infile) # read in specimen interpretations
    IntData=pmag.get_dictitem(Data,'specimen_int','','F') # retrieve specimens with intensity data
    comment,orient="",[]
    samples,sites=[],[]
    for rec in Data: # run through the data filling in missing keys and finding all components, coordinates available
# fill in missing fields, collect unique sample and site names
	if 'er_sample_name' not in rec.keys():
	    rec['er_sample_name']=""
	elif rec['er_sample_name'] not in samples:
	    samples.append(rec['er_sample_name'])
	if 'er_site_name' not in rec.keys():
	    rec['er_site_name']=""
	elif rec['er_site_name'] not in sites:
	    sites.append(rec['er_site_name'])
	if 'specimen_int' not in rec.keys():rec['specimen_int']=''
	if 'specimen_comp_name' not in rec.keys() or rec['specimen_comp_name']=="":rec['specimen_comp_name']='A'
	if rec['specimen_comp_name'] not in Comps:Comps.append(rec['specimen_comp_name'])
        rec['specimen_tilt_correction']=rec['specimen_tilt_correction'].strip('\n')
	if "specimen_tilt_correction" not in rec.keys(): rec["specimen_tilt_correction"]="-1" # assume sample coordinates
	if rec["specimen_tilt_correction"] not in orient: orient.append(rec["specimen_tilt_correction"])  # collect available coordinate systems
	if "specimen_direction_type" not in rec.keys(): rec["specimen_direction_type"]='l'  # assume direction is line - not plane
	if "specimen_dec" not in rec.keys(): rec["specimen_direction_type"]=''  # if no declination, set direction type to blank
	if "specimen_n" not in rec.keys(): rec["specimen_n"]=''  # put in n
	if "specimen_alpha95" not in rec.keys(): rec["specimen_alpha95"]=''  # put in alpha95 
	if "magic_method_codes" not in rec.keys(): rec["magic_method_codes"]=''
     #
     # start parsing data into SpecDirs, SpecPlanes, SpecInts 
    SpecInts,SpecDirs,SpecPlanes=[],[],[]
    samples.sort() # get sorted list of samples and sites
    sites.sort()
    if not skip_intensities: # don't skip intensities
	IntData=pmag.get_dictitem(Data,'specimen_int','','F') # retrieve specimens with intensity data
	if nocrit==0: # use selection criteria
	    for rec in IntData: # do selection criteria
		kill=pmag.grade(rec,accept,'specimen_int')
		if len(kill)==0: SpecInts.append(rec) # intensity record to be included in sample, site calculations
	else:
	    SpecInts=IntData[:] # take everything - no selection criteria
# check for required data adjustments
        if len(corrections)>0 and len(SpecInts)>0:
            for cor in corrections:
                SpecInts=pmag.get_dictitem(SpecInts,'magic_method_codes',cor,'has') # only take specimens with the required corrections
        if len(nocorrection)>0 and len(SpecInts)>0:
            for cor in nocorrection:
                SpecInts=pmag.get_dictitem(SpecInts,'magic_method_codes',cor,'not') # exclude the corrections not specified for inclusion
# take top priority specimen of its name in remaining specimens (only one per customer)
        PrioritySpecInts=[]
        specimens=pmag.get_specs(SpecInts) # get list of uniq specimen names
        for spec in specimens:
            ThisSpecRecs=pmag.get_dictitem(SpecInts,'er_specimen_name',spec,'T') # all the records for this specimen
            if len(ThisSpecRecs)==1:
                PrioritySpecInts.append(ThisSpecRecs[0])
            elif len(ThisSpecRecs)>1: # more than one
                prec=[]
                for p in priorities:
                    ThisSpecRecs=pmag.get_dictitem(SpecInts,'magic_method_codes',p,'has') # all the records for this specimen
                    if len(ThisSpecRecs)>0:prec.append(ThisSpecRecs[0])
                PrioritySpecInts.append(prec[0]) # take the best one
        SpecInts=PrioritySpecInts # this has the first specimen record 
    if not skip_directions: # don't skip directions
	AllDirs=pmag.get_dictitem(Data,'specimen_direction_type','','F') # retrieve specimens with directed lines and planes
	Ns=pmag.get_dictitem(AllDirs,'specimen_n','','F')  # get all specimens with specimen_n information 
	if nocrit!=1: # use selection criteria
	    for rec in Ns: # look through everything with specimen_n for "good" data
                kill=pmag.grade(rec,accept,'specimen_dir')
                if len(kill)==0: # nothing killed it
			SpecDirs.append(rec)
	else: # no criteria
	    SpecDirs=AllDirs[:] # take them all
# SpecDirs is now the list of all specimen directions (lines and planes) that pass muster
#
    PmagSamps,SampDirs=[],[] # list of all sample data and list of those that pass the DE-SAMP criteria
    PmagSites,PmagResults=[],[] # list of all site data and selected results
    SampInts=[]
    for samp in samples: # run through the sample names
	if avg_directions_by_sample: #  average by sample if desired
	   SampDir=pmag.get_dictitem(SpecDirs,'er_sample_name',samp,'T') # get all the directional data for this sample
	   if len(SampDir)>0: # there are some directions
	       for coord in coords: # step through desired coordinate systems
		   CoordDir=pmag.get_dictitem(SampDir,'specimen_tilt_correction',coord,'T') # get all the directions for this sample
		   if len(CoordDir)>0: # there are some with this coordinate system
		       if not avg_all_components: # look component by component
			   for comp in Comps:
			       CompDir=pmag.get_dictitem(CoordDir,'specimen_comp_name',comp,'T') # get all directions from this component
			       if len(CompDir)>0: # there are some
				   PmagSampRec=pmag.lnpbykey(CompDir,'sample','specimen') # get a sample average from all specimens
				   PmagSampRec["er_location_name"]=CompDir[0]['er_location_name'] # decorate the sample record
				   PmagSampRec["er_site_name"]=CompDir[0]['er_site_name']
				   PmagSampRec["er_sample_name"]=samp
				   PmagSampRec["er_citation_names"]="This study"
				   PmagSampRec["er_analyst_mail_names"]=user
				   PmagSampRec['magic_software_packages']=version_num
				   if nocrit!=1:PmagSampRec['pmag_criteria_codes']="ACCEPT"
				   if agefile != "": PmagSampRec= pmag.get_age(PmagSampRec,"er_site_name","sample_inferred_",AgeNFO,DefaultAge)
				   site_height=pmag.get_dictitem(height_nfo,'er_site_name',PmagSampRec['er_site_name'],'T')
				   if len(site_height)>0:PmagSampRec["sample_height"]=site_height[0]['site_height'] # add in height if available
				   PmagSampRec['sample_comp_name']=comp
				   PmagSampRec['sample_tilt_correction']=coord
				   PmagSampRec['er_specimen_names']= pmag.get_list(CompDir,'er_specimen_name') # get a list of the specimen names used
				   PmagSampRec['magic_method_codes']= pmag.get_list(CompDir,'magic_method_codes') # get a list of the methods used
				   if nocrit!=1: # apply selection criteria
                                       kill=pmag.grade(PmagSampRec,accept,'sample_dir')
                                   else:
                                       kill=[]
				   if len(kill)==0:
					SampDirs.append(PmagSampRec)
					if vgps==1: # if sample level VGP info desired, do that now
					    PmagResRec=pmag.getsampVGP(PmagSampRec,SiteNFO)
					    if PmagResRec!="":PmagResults.append(PmagResRec)
                                        PmagSamps.append(PmagSampRec)
		       if avg_all_components: # average all components together  basically same as above
			   PmagSampRec=pmag.lnpbykey(CoordDir,'sample','specimen')
			   PmagSampRec["er_location_name"]=CoordDir[0]['er_location_name']
			   PmagSampRec["er_site_name"]=CoordDir[0]['er_site_name']
			   PmagSampRec["er_sample_name"]=samp
			   PmagSampRec["er_citation_names"]="This study"
			   PmagSampRec["er_analyst_mail_names"]=user
			   PmagSampRec['magic_software_packages']=version_num
			   if nocrit!=1:PmagSampRec['pmag_criteria_codes']=""
			   if agefile != "": PmagSampRec= pmag.get_age(PmagSampRec,"er_site_name","sample_inferred_",AgeNFO,DefaultAge)
			   site_height=pmag.get_dictitem(height_nfo,'er_site_name',site,'T')
			   if len(site_height)>0:PmagSampRec["sample_height"]=site_height[0]['site_height'] # add in height if available
			   PmagSampRec['sample_tilt_correction']=coord
			   PmagSampRec['sample_comp_name']= pmag.get_list(CoordDir,'specimen_comp_name') # get components used
			   PmagSampRec['er_specimen_names']= pmag.get_list(CoordDir,'er_specimen_name') # get specimne names averaged
			   PmagSampRec['magic_method_codes']= pmag.get_list(CoordDir,'magic_method_codes') # assemble method codes
			   if nocrit!=1: # apply selection criteria
                               kill=pmag.grade(PmagSampRec,accept,'sample_dir')
			       if len(kill)==0: # passes the mustard
				   SampDirs.append(PmagSampRec)
				   if vgps==1:
				       PmagResRec=pmag.getsampVGP(PmagSampRec,SiteNFO)
				       if PmagResRec!="":PmagResults.append(PmagResRec)
			   else: # take everything
			       SampDirs.append(PmagSampRec)
			       if vgps==1:
				   PmagResRec=pmag.getsampVGP(PmagSampRec,SiteNFO)
				   if PmagResRec!="":PmagResults.append(PmagResRec)
			   PmagSamps.append(PmagSampRec)
	if avg_intensities_by_sample: #  average by sample if desired
	   SampI=pmag.get_dictitem(SpecInts,'er_sample_name',samp,'T') # get all the intensity data for this sample
	   if len(SampI)>0: # there are some
	       PmagSampRec=pmag.average_int(SampI,'specimen','sample') # get average intensity stuff
	       PmagSampRec["sample_description"]="sample intensity" # decorate sample record
	       PmagSampRec["sample_direction_type"]=""
	       PmagSampRec['er_site_name']=SampI[0]["er_site_name"]
	       PmagSampRec['er_sample_name']=samp
	       PmagSampRec['er_location_name']=SampI[0]["er_location_name"]
	       PmagSampRec["er_citation_names"]="This study"
	       PmagSampRec["er_analyst_mail_names"]=user
	       if agefile != "":   PmagSampRec=pmag.get_age(PmagSampRec,"er_site_name","sample_inferred_", AgeNFO,DefaultAge)
	       site_height=pmag.get_dictitem(height_nfo,'er_site_name',PmagSampRec['er_site_name'],'T')
	       if len(site_height)>0:PmagSampRec["sample_height"]=site_height[0]['site_height'] # add in height if available
	       PmagSampRec['er_specimen_names']= pmag.get_list(SampI,'er_specimen_name')
	       PmagSampRec['magic_method_codes']= pmag.get_list(SampI,'magic_method_codes')
	       if nocrit!=1:  # apply criteria!
                   kill=pmag.grade(PmagSampRec,accept,'sample_int')
                   if len(kill)==0:
                       PmagSampRec['pmag_criteria_codes']="ACCEPT"
	               SampInts.append(PmagSampRec)
	               PmagSamps.append(PmagSampRec)
                   else:PmagSampRec={} # sample rejected
               else: # no criteria
	           SampInts.append(PmagSampRec)
	           PmagSamps.append(PmagSampRec)
                   PmagSampRec['pmag_criteria_codes']=""
	       if vgps==1 and get_model_lat!=0 and PmagSampRec!={}: #
		  if get_model_lat==1: # use sample latitude
		      PmagResRec=pmag.getsampVDM(PmagSampRec,SampNFO)
                      del(PmagResRec['model_lat']) # get rid of the model lat key
		  elif get_model_lat==2: # use model latitude
		      PmagResRec=pmag.getsampVDM(PmagSampRec,ModelLats)
		      if PmagResRec!={}:PmagResRec['magic_method_codes']=PmagResRec['magic_method_codes']+":IE-MLAT"
		  if PmagResRec!={}:
                      PmagResRec['er_specimen_names']=PmagSampRec['er_specimen_names']
                      PmagResRec['er_sample_names']=PmagSampRec['er_sample_name']
                      PmagResRec['pmag_criteria_codes']='ACCEPT'
                      PmagResRec['average_int_sigma_perc']=PmagSampRec['sample_int_sigma_perc']
                      PmagResRec['average_int_sigma']=PmagSampRec['sample_int_sigma']
                      PmagResRec['average_int_n']=PmagSampRec['sample_int_n']
                      PmagResRec['vadm_n']=PmagSampRec['sample_int_n']
                      PmagResRec['data_type']='i'
                      PmagResults.append(PmagResRec)
    if len(PmagSamps)>0:
	TmpSamps,keylist=pmag.fillkeys(PmagSamps) # fill in missing keys from different types of records       
	pmag.magic_write(sampout,TmpSamps,'pmag_samples') # save in sample output file
	print ' sample averages written to ',sampout
   
#
#create site averages from specimens or samples as specified
#
    for site in sites:
	if not avg_directions_by_sample: key,dirlist='specimen',SpecDirs # if specimen averages at site level desired
	if avg_directions_by_sample: key,dirlist='sample',SampDirs # if sample averages at site level desired
	tmp=pmag.get_dictitem(dirlist,'er_site_name',site,'T') # get all the sites with  directions
	tmp1=pmag.get_dictitem(tmp,key+'_tilt_correction',coords[-1],'T') # use only the last coordinate if avg_all_components==False
	sd=pmag.get_dictitem(SiteNFO,'er_site_name',site,'T') # fish out site information (lat/lon, etc.)
	if len(sd)>0:
            sitedat=sd[0]
	    if not avg_all_components: # do component wise averaging
		for comp in Comps:
		    siteD=pmag.get_dictitem(tmp1,key+'_comp_name',comp,'T') # get all components comp
		    if len(siteD)>0: # there are some for this site and component name
			PmagSiteRec=pmag.lnpbykey(siteD,'site',key) # get an average for this site
			PmagSiteRec['site_comp_name']=comp # decorate the site record
			PmagSiteRec["er_location_name"]=siteD[0]['er_location_name']
			PmagSiteRec["er_site_name"]=siteD[0]['er_site_name']
			PmagSiteRec['site_tilt_correction']=coords[-1]
			PmagSiteRec['site_comp_name']= pmag.get_list(siteD,key+'_comp_name')
                        if avg_directions_by_sample:
			    PmagSiteRec['er_sample_names']= pmag.get_list(siteD,'er_sample_name')
                        else:
			    PmagSiteRec['er_specimen_names']= pmag.get_list(siteD,'er_specimen_name')
# determine the demagnetization code (DC3,4 or 5) for this site
			AFnum=len(pmag.get_dictitem(siteD,'magic_method_codes','LP-DIR-AF','has'))
			Tnum=len(pmag.get_dictitem(siteD,'magic_method_codes','LP-DIR-T','has'))
			DC=3
			if AFnum>0:DC+=1
			if Tnum>0:DC+=1
			PmagSiteRec['magic_method_codes']= pmag.get_list(siteD,'magic_method_codes')+':'+ 'LP-DC'+str(DC)
			PmagSiteRec['magic_method_codes'].strip(":")
			if plotsites:
                            print PmagSiteRec['er_site_name']
                            pmagplotlib.plotSITE(EQ['eqarea'],PmagSiteRec,siteD,key) # plot and list the data
                            pmagplotlib.drawFIGS(EQ)
			PmagSites.append(PmagSiteRec) 
	    else: # last component only
	        siteD=tmp1[:] # get the last orientation system specified
	        if len(siteD)>0: # there are some
	            PmagSiteRec=pmag.lnpbykey(siteD,'site',key) # get the average for this site 
	            PmagSiteRec["er_location_name"]=siteD[0]['er_location_name'] # decorate the record
    		    PmagSiteRec["er_site_name"]=siteD[0]['er_site_name']
		    PmagSiteRec['site_comp_name']=comp
		    PmagSiteRec['site_tilt_correction']=coords[-1]
		    PmagSiteRec['site_comp_name']= pmag.get_list(siteD,key+'_comp_name')
		    PmagSiteRec['er_specimen_names']= pmag.get_list(siteD,'er_specimen_name')
		    PmagSiteRec['er_sample_names']= pmag.get_list(siteD,'er_sample_name')
    		    AFnum=len(pmag.get_dictitem(siteD,'magic_method_codes','LP-DIR-AF','has'))
    	    	    Tnum=len(pmag.get_dictitem(siteD,'magic_method_codes','LP-DIR-T','has'))
	    	    DC=3
		    if AFnum>0:DC+=1
		    if Tnum>0:DC+=1
		    PmagSiteRec['magic_method_codes']= pmag.get_list(siteD,'magic_method_codes')+':'+ 'LP-DC'+str(DC)
		    PmagSiteRec['magic_method_codes'].strip(":")
		    if not avg_directions_by_sample:PmagSiteRec['site_comp_name']= pmag.get_list(siteD,key+'_comp_name')
	    	    if plotsites:
                        pmagplotlib.plotSITE(EQ['eqarea'],PmagSiteRec,siteD,key)
                        pmagplotlib.drawFIGS(EQ)
		    PmagSites.append(PmagSiteRec)
        else:
            print 'site information not found in er_sites for site, ',site,' site will be skipped'
    for PmagSiteRec in PmagSites: # now decorate each dictionary some more, and calculate VGPs etc. for results table
	PmagSiteRec["er_citation_names"]="This study"
	PmagSiteRec["er_analyst_mail_names"]=user
	PmagSiteRec['magic_software_packages']=version_num
	if agefile != "": PmagSiteRec= pmag.get_age(PmagSiteRec,"er_site_name","site_inferred_",AgeNFO,DefaultAge)
	PmagSiteRec['pmag_criteria_codes']='ACCEPT'
	if 'site_n_lines' in PmagSiteRec.keys() and 'site_n_planes' in PmagSiteRec.keys() and PmagSiteRec['site_n_lines']!="" and PmagSiteRec['site_n_planes']!="":
	    if int(PmagSiteRec["site_n_planes"])>0:
		PmagSiteRec["magic_method_codes"]=PmagSiteRec['magic_method_codes']+":DE-FM-LP"
	    elif int(PmagSiteRec["site_n_lines"])>2:
		PmagSiteRec["magic_method_codes"]=PmagSiteRec['magic_method_codes']+":DE-FM"
	    kill=pmag.grade(PmagSiteRec,accept,'site_dir')
            if len(kill)==0: 
		PmagResRec={} # set up dictionary for the pmag_results table entry
		PmagResRec['data_type']='i' # decorate it a bit
		PmagResRec['magic_software_packages']=version_num
		PmagSiteRec['site_description']='Site direction included in results table' 
		PmagResRec['pmag_criteria_codes']='ACCEPT'
		dec=float(PmagSiteRec["site_dec"])
		inc=float(PmagSiteRec["site_inc"])
                if 'site_alpha95' in PmagSiteRec.keys() and PmagSiteRec['site_alpha95']!="": 
		    a95=float(PmagSiteRec["site_alpha95"])
                else:a95=180.
	        sitedat=pmag.get_dictitem(SiteNFO,'er_site_name',PmagSiteRec['er_site_name'],'T')[0] # fish out site information (lat/lon, etc.)
		lat=float(sitedat['site_lat'])
		lon=float(sitedat['site_lon'])
		plong,plat,dp,dm=pmag.dia_vgp(dec,inc,a95,lat,lon) # get the VGP for this site
		if PmagSiteRec['site_tilt_correction']=='-1':C=' (spec coord) '
		if PmagSiteRec['site_tilt_correction']=='0':C=' (geog. coord) '
		if PmagSiteRec['site_tilt_correction']=='100':C=' (strat. coord) '
		PmagResRec["pmag_result_name"]="VGP Site: "+PmagSiteRec["er_site_name"] # decorate some more
		PmagResRec["result_description"]="Site VGP, coord system = "+str(coord)+' component: '+comp
		PmagResRec['er_site_names']=PmagSiteRec['er_site_name']
		PmagResRec['pmag_criteria_codes']='ACCEPT'
		PmagResRec['er_citation_names']='This study'
		PmagResRec['er_analyst_mail_names']=user
		PmagResRec["er_location_names"]=PmagSiteRec["er_location_name"]
                if avg_directions_by_sample:
		    PmagResRec["er_sample_names"]=PmagSiteRec["er_sample_names"]
                else:
		    PmagResRec["er_specimen_names"]=PmagSiteRec["er_specimen_names"]
		PmagResRec["tilt_correction"]=PmagSiteRec['site_tilt_correction']
		PmagResRec["pole_comp_name"]=PmagSiteRec['site_comp_name']
		PmagResRec["average_dec"]=PmagSiteRec["site_dec"]
		PmagResRec["average_inc"]=PmagSiteRec["site_inc"]
		PmagResRec["average_alpha95"]=PmagSiteRec["site_alpha95"]
		PmagResRec["average_n"]=PmagSiteRec["site_n"]
		PmagResRec["average_n_lines"]=PmagSiteRec["site_n_lines"]
		PmagResRec["average_n_planes"]=PmagSiteRec["site_n_planes"]            
		PmagResRec["vgp_n"]=PmagSiteRec["site_n"]
		PmagResRec["average_k"]=PmagSiteRec["site_k"]
		PmagResRec["average_r"]=PmagSiteRec["site_r"]
		PmagResRec["average_lat"]='%10.4f ' %(lat)
		PmagResRec["average_lon"]='%10.4f ' %(lon)
		if agefile != "": PmagResRec= pmag.get_age(PmagResRec,"er_site_names","average_",AgeNFO,DefaultAge)
		site_height=pmag.get_dictitem(height_nfo,'er_site_name',site,'T')
		if len(site_height)>0:PmagResRec["average_height"]=site_height[0]['site_height']
		PmagResRec["vgp_lat"]='%7.1f ' % (plat)
		PmagResRec["vgp_lon"]='%7.1f ' % (plong)
		PmagResRec["vgp_dp"]='%7.1f ' % (dp)
		PmagResRec["vgp_dm"]='%7.1f ' % (dm)
		PmagResRec["magic_method_codes"]= PmagSiteRec["magic_method_codes"]
		if PmagSiteRec['site_tilt_correction']=='0':PmagSiteRec['magic_method_codes']=PmagSiteRec['magic_method_codes']+":DA-DIR-GEO"
                if PmagSiteRec['site_tilt_correction']=='100':PmagSiteRec['magic_method_codes']=PmagSiteRec['magic_method_codes']+":DA-DIR-TILT"
                PmagSiteRec['site_polarity']=""
                if avg_by_polarity: # assign polarity based on angle of pole lat to spin axis - may want to re-think this sometime
                      angle=pmag.angle([0,0],[0,(90-plat)])
                      if angle <= 55.: PmagSiteRec["site_polarity"]='n'
                      if angle > 55. and angle < 125.: PmagSiteRec["site_polarity"]='t'
                      if angle >= 125.: PmagSiteRec["site_polarity"]='r'
                PmagResults.append(PmagResRec)
    if avg_by_polarity:
        crecs=pmag.get_dictitem(PmagSites,'site_tilt_correction','100','T') # find the tilt corrected data
        if len(crecs)<2:crecs=pmag.get_dictitem(PmagSites,'site_tilt_correction','0','T') # if there aren't any, find the geographic corrected data
        if len(crecs)>2: # if there are some, 
            comp=pmag.get_list(crecs,'site_comp_name').split(':')[0] # find the first component 
            crecs=pmag.get_dictitem(crecs,'site_comp_name',comp,'T') # fish out all of the first component
            precs=[]
            for rec in crecs:
                precs.append({'dec':rec['site_dec'],'inc':rec['site_inc'],'name':rec['er_site_name'],'loc':rec['er_location_name']})
            polpars=pmag.fisher_by_pol(precs) # calculate average by polarity
            for mode in polpars.keys(): # hunt through all the modes (normal=A, reverse=B, all=ALL)
                PolRes={}
                PolRes['er_citation_names']='This study'
                PolRes["pmag_result_name"]="Polarity Average: Polarity "+mode # 
                PolRes["data_type"]="a"
                PolRes["average_dec"]='%7.1f'%(polpars[mode]['dec'])
                PolRes["average_inc"]='%7.1f'%(polpars[mode]['inc'])
                PolRes["average_n"]='%i'%(polpars[mode]['n'])
                PolRes["average_r"]='%5.4f'%(polpars[mode]['r'])
                PolRes["average_k"]='%6.0f'%(polpars[mode]['k'])
                PolRes["average_alpha95"]='%7.1f'%(polpars[mode]['alpha95'])
		PolRes['er_site_names']= polpars[mode]['sites']
		PolRes['er_location_names']= polpars[mode]['locs']
		PolRes['magic_software_packages']=version_num
                PmagResults.append(PolRes)
         
    if not skip_intensities and nositeints!=1:
      for site in sites: # now do intensities for each site
        if plotsites:print site
        if not avg_intensities_by_sample: key,intlist='specimen',SpecInts # if using specimen level data
        if avg_intensities_by_sample: key,intlist='sample',PmagSamps # if using sample level data
        Ints=pmag.get_dictitem(intlist,'er_site_name',site,'T') # get all the intensities  for this site
        if len(Ints)>0: # there are some
            PmagSiteRec=pmag.average_int(Ints,key,'site') # get average intensity stuff for site table
            PmagResRec=pmag.average_int(Ints,key,'average') # get average intensity stuff for results table
            if plotsites: # if site by site examination requested - print this site out to the screen
                for rec in Ints:print rec['er_'+key+'_name'],' %7.1f'%(1e6*float(rec[key+'_int']))
                if len(Ints)>1:
                    print 'Average: ','%7.1f'%(1e6*float(PmagResRec['average_int'])),'N: ',len(Ints)
                    print 'Sigma: ','%7.1f'%(1e6*float(PmagResRec['average_int_sigma'])),'Sigma %: ',PmagResRec['average_int_sigma_perc']
                raw_input('Press any key to continue\n')
            er_location_name=Ints[0]["er_location_name"] 
            PmagSiteRec["er_location_name"]=er_location_name # decorate the records
            PmagSiteRec["er_citation_names"]="This study"
            PmagResRec["er_location_names"]=er_location_name
            PmagResRec["er_citation_names"]="This study"
            PmagSiteRec["er_analyst_mail_names"]=user
            PmagResRec["er_analyst_mail_names"]=user
            PmagResRec["data_type"]='i'
            if not avg_intensities_by_sample:
                PmagSiteRec['er_specimen_names']= pmag.get_list(Ints,'er_specimen_name') # list of all specimens used
                PmagResRec['er_specimen_names']= pmag.get_list(Ints,'er_specimen_name')
            PmagSiteRec['er_sample_names']= pmag.get_list(Ints,'er_sample_name') # list of all samples used
            PmagResRec['er_sample_names']= pmag.get_list(Ints,'er_sample_name')
            PmagSiteRec['er_site_name']= site
            PmagResRec['er_site_names']= site
            PmagSiteRec['magic_method_codes']= pmag.get_list(Ints,'magic_method_codes')
            PmagResRec['magic_method_codes']= pmag.get_list(Ints,'magic_method_codes')
            kill=pmag.grade(PmagSiteRec,accept,'site_int')
            if nocrit==1 or len(kill)==0:
                b,sig=float(PmagResRec['average_int']),""
                if(PmagResRec['average_int_sigma'])!="":sig=float(PmagResRec['average_int_sigma'])
                sdir=pmag.get_dictitem(PmagResults,'er_site_names',site,'T') # fish out site direction
                if len(sdir)>0 and  sdir[-1]['average_inc']!="": # get the VDM for this record using last average inclination (hope it is the right one!)
                        inc=float(sdir[0]['average_inc']) # 
                        mlat=pmag.magnetic_lat(inc) # get magnetic latitude using dipole formula
                        PmagResRec["vdm"]='%8.3e '% (pmag.b_vdm(b,mlat)) # get VDM with magnetic latitude
                        PmagResRec["vdm_n"]=PmagResRec['average_int_n']
                        if 'average_int_sigma' in PmagResRec.keys() and PmagResRec['average_int_sigma']!="":
                            vdm_sig=pmag.b_vdm(float(PmagResRec['average_int_sigma']),mlat)
                            PmagResRec["vdm_sigma"]='%8.3e '% (vdm_sig)
                        else:
                            PmagResRec["vdm_sigma"]=""
                mlat="" # define a model latitude
                if get_model_lat==1: # use present site latitude
                    mlats=pmag.get_dictitem(SiteNFO,'er_site_name',site,'T')
                    if len(mlats)>0: mlat=mlats[0]['site_lat']
                elif get_model_lat==2: # use a model latitude from some plate reconstruction model (or something)
                    mlats=pmag.get_dictitem(ModelLats,'er_site_name',site,'T')
                    if len(mlats)>0: PmagResRec['model_lat']=mlats[0]['site_model_lat']
                    mlat=PmagResRec['model_lat']
                if mlat!="":
                    PmagResRec["vadm"]='%8.3e '% (pmag.b_vdm(b,float(mlat))) # get the VADM using the desired latitude
                    if sig!="":
                        vdm_sig=pmag.b_vdm(float(PmagResRec['average_int_sigma']),float(mlat))
                        PmagResRec["vadm_sigma"]='%8.3e '% (vdm_sig)
                        PmagResRec["vadm_n"]=PmagResRec['average_int_n']
                    else:
                        PmagResRec["vadm_sigma"]=""
	        sitedat=pmag.get_dictitem(SiteNFO,'er_site_name',PmagSiteRec['er_site_name'],'T') # fish out site information (lat/lon, etc.)
                if len(sitedat)>0:
                    sitedat=sitedat[0]
                    PmagResRec['average_lat']=sitedat['site_lat']
                    PmagResRec['average_lon']=sitedat['site_lon']
                else:
                    PmagResRec['average_lon']='UNKNOWN'
                    PmagResRec['average_lon']='UNKNOWN'
                PmagResRec['magic_software_packages']=version_num
                PmagResRec["pmag_result_name"]="V[A]DM: Site "+site
                PmagResRec["result_description"]="V[A]DM of site"
                PmagResRec["pmag_criteria_codes"]="ACCEPT"
                if agefile != "": PmagResRec= pmag.get_age(PmagResRec,"er_site_names","average_",AgeNFO,DefaultAge)
                site_height=pmag.get_dictitem(height_nfo,'er_site_name',site,'T')
                if len(site_height)>0:PmagResRec["average_height"]=site_height[0]['site_height']
                PmagSites.append(PmagSiteRec)
                PmagResults.append(PmagResRec)
    if len(PmagSites)>0:
        Tmp,keylist=pmag.fillkeys(PmagSites)         
        pmag.magic_write(siteout,Tmp,'pmag_sites')
        print ' sites written to ',siteout
    else: print "No Site level table"
    if len(PmagResults)>0:
        TmpRes,keylist=pmag.fillkeys(PmagResults)         
        pmag.magic_write(resout,TmpRes,'pmag_results')
        print ' results written to ',resout
    else: print "No Results level table"


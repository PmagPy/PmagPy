import pmag, pmagplotlib
import pylab
import numpy as np
import random
import matplotlib.pyplot as plt

def fishrot(k=20,n=100,Dec=0,Inc=90):
    """
    Generates Fisher distributed unit vectors from a specified distribution 
    using the pmag.py fshdev and dodirot functions
    
    Parameters
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
    secular variation at given latitude and rotated about vertical 
    axis by given declination 

    Parameters
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
        Dflip.append([d,i,1.])
    return Dflip
        
def bootstrap_common_mean(Data1,Data2,NumSims=1000):
    """
    Conduct a bootstrap test (Tauxe, 2010) for a common mean on two declination,
    inclination data sets
    
    This function modifies code from PmagPy for use calculating and plotting 
    bootstrap statistics. Three plots are generated (one for x, one for y and
    one for z). If the 95 percent confidence bounds for each component overlap
    each other, the two directions are not significantly different.

    Parameters
    ----------
    Data1 : a list of directional data [dec,inc]
    Data2 : a list of directional data [dec,inc]
    NumSims : number of bootstrap samples (default is 1000)
    """         
    counter=0
    BDI1=pmag.di_boot(Data1)
    BDI2=pmag.di_boot(Data2)
    print ""
    print "==============="
    print ""
    print "Here are the results of the bootstrap test for a common mean"
    CDF={'X':1,'Y':2,'Z':3}
    pylab.figure(CDF['X'],figsize=(3,3),dpi=160)
    pylab.figure(CDF['Y'],figsize=(3,3),dpi=160)
    pylab.figure(CDF['Z'],figsize=(3,3),dpi=160)
    pmagplotlib.plotCOM(CDF,BDI1,BDI2,["",""])
    
def WatsonV_common_mean(Data1,Data2,NumSims=5000,plot='no'):
    """
    Conduct a Watson V test for a common mean on two declination, inclination data sets
    
    This function calculates Watson's V statistic from input files through Monte Carlo
    simulation in order to test whether two populations of directional data could have
    been drawn from a common mean. The critical angle between the two sample mean
    directions and the corresponding McFadden and McElhinny (1990) classification is printed.


    Required parameters
    ----------
    Data1 : a list of directional data [dec,inc]
    Data2 : a list of directional data [dec,inc]
    
    Optional parameters
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

def plotNET(fignum):
    """
    draws circle and tick marks for equal area projection
    """
#
# make the perimeter
#
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
#
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

def plotDI(DIblock,color='k',marker='o',legend='no',label=''):
    """
    Plot declination, inclination data on an equal area plot

    This function modifies the plotDI function of PmagPy for use in the IPython notebook environment

    Required Parameters
    -----------
    DIblock : a DIblock is comprised of a list of unit vectors [dec,inc,1.]

    Optional Parameters
    -----------
    color : the default color is black. Other colors can be chosen (e.g. 'r')
    marker : the default marker is a circle ('o')
    label : the default label is blank ('')
    legend : the default is no legend ('no'). Putting 'yes' will plot a legend.
    """
    # initialize the variables
    X_down,X_up,Y_down,Y_up=[],[],[],[]
    for rec in DIblock:
        Up,Down=0,0
        XY=pmag.dimap(rec[0],rec[1])
        if rec[1] >= 0:         
            X_down.append(XY[0])
            Y_down.append(XY[1])
        else:
            X_up.append(XY[0])
            Y_up.append(XY[1])

    if len(X_up)>0:
        pylab.scatter(X_up,Y_up,facecolors='none', edgecolors=color, marker=marker, label=label)

    if len(X_down)>0: 
        pylab.scatter(X_down,Y_down,facecolors=color, edgecolors=color, marker=marker, label=label)
    if legend=='yes':
        pylab.legend(loc=2)
    pylab.tight_layout()

def plotDImean(Dec,Inc,a95,color='k',marker='o',label='',legend='no'):
    """
    Plot a mean declination, inclination with alpha_95 ellipse on an equal area plot.

    Before this function is called a plot needs to be initialized with code that looks 
    something like:
    >fignum = 1
    >plt.figure(num=fignum,figsize=(10,10),dpi=160)
    >IPmag.iplotNET(fignum)

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
        pylab.plot(DI_dimap[0],DI_dimap[1],markeredgecolor=color , markerfacecolor='white', marker=marker,label=label)
    if Inc >= 0:
        pylab.plot(DI_dimap[0],DI_dimap[1],color=color,marker=marker,label=label)
    Xcirc,Ycirc=[],[]
    Da95,Ia95=pmag.circ(Dec,Inc,a95)
    if legend=='yes':
        pylab.legend(loc=2)
    for k in  range(len(Da95)):
        XY=pmag.dimap(Da95[k],Ia95[k])
        Xcirc.append(XY[0])
        Ycirc.append(XY[1])
    pylab.plot(Xcirc,Ycirc,color)
    pylab.tight_layout()
    
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

def poleplot(mapname,plong,plat,A95,label='',color='k',marker='o',legend='no'):
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

def vgpplot(mapname,plong,plat,label='',color='k',marker='o',legend='no'):
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

def vgpcalc(dataframe,tilt_correction='yes'):
    """
    This function calculates paleomagnetic poles using directional data and site location data within a pandas.DataFrame. The function adds the columns 'paleolatitude', 'pole_lat', 'pole_long', 'pole_lat_rev', and 'pole_long_rev' to the dataframe. The '_rev' columns allow for subsequent choice as to which polarity will be used for the VGPs.

    Parameters
    ----------- 
    tilt-correction : 'yes' is the default and uses tilt-corrected data (dec_tc, inc_tc), 'no' uses data that is not tilt-corrected and is geographic coordinates
    dataframe : the name of the pandas.DataFrame containing the data
    dataframe['site_lat'] : the latitude of the site
    dataframe['site_long'] : the longitude of the site
    dataframe['inc_tc'] : the tilt-corrected inclination (used by default tilt-correction='yes')
    dataframe['dec_tc'] : the tilt-corrected declination (used by default tilt-correction='yes')
    dataframe['inc_is'] : the insitu inclination (used when tilt-correction='no')
    dataframe['dec_is'] : the insitu declination (used when tilt-correction='no')
    """
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
        dataframe['vgp_long']=np.where(mask,(dataframe['site_long']+dataframe['beta'])%360.,(dataframe['site_long']+180-dataframe['beta'])%360.)
        #calculate the antipode of the poles
        dataframe['vgp_lat_rev']=-dataframe['vgp_lat']
        dataframe['vgp_long_rev']=(dataframe['vgp_long']-180.)%360. 
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
        dataframe['vgp_long']=np.where(mask,(dataframe['site_long']+dataframe['beta'])%360.,(dataframe['site_long']+180-dataframe['beta'])%360.)
        #calculate the antipode of the poles
        dataframe['vgp_lat_rev']=-dataframe['vgp_lat']
        dataframe['vgp_long_rev']=(dataframe['vgp_long']-180.)%360. 
        #the 'colatitude' and 'beta' columns were created for the purposes of the pole calculations
        #but aren't of further use and are deleted
        del dataframe['colatitude']
        del dataframe['beta']
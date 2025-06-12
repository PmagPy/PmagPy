import numpy as np
import math
import scipy as sp
from scipy import special
import matplotlib.pyplot as plt
import pmagpy.pmag as pmag
import pmagpy.ipmag as ipmag
from scipy.interpolate import PchipInterpolator
from scipy.integrate import cumulative_trapezoid
from scipy import interpolate
from scipy.stats.distributions import chi2
import pandas as pd

def P_lm(l,m,theta):
    """
    This function calculates the Associated Legendre Functions.
    
    Parameters:
        l (int): The degree of the associated Legendre function.
        m (int): The order of the associated Legendre function.
        theta (float): The co-latitude in radians.
        
    Returns:
        float: The calculated value of the associated Legendre function.
        
    References:
        3M - page: 441, equation B. 3. 2
    
    Notes:
        - theta represents the co-latitude, which is the complement of the latitude.
        - The function uses the numpy and math modules.
    """
    A = np.sin(theta)**m/2**l
    sum_p_lm = 0.
    for t in range(0,int((l-m)/2)+1):
        #t vai de zero ate o ultimo inteiro menor que l-m /2   
        
        B = (-1)**t*math.factorial(2*l-2*t)
        C = math.factorial(t)*math.factorial(l-t)*math.factorial(l-m-2*t)
        D = l - m - 2*t
        sum_p_lm += (B/C)*np.cos(theta)**D
    return A*sum_p_lm
      
	
def dP_lm_dt(l,m,theta):
    """
    This function calculates the derivative of Associated Legendre Functions with respect to theta.
    
    Parameters:
        l (int): The degree of the associated Legendre function.
        m (int): The order of the associated Legendre function.
        theta (float): The co-latitude in radians.
        
    Returns:
        float: The calculated value of the derivative of the associated Legendre function.
        
    Notes:
        - theta represents the co-latitude, which is the complement of the latitude.
        - The function uses the numpy and math modules.
    """
    A = (np.sin(theta)**m)/(2.**l)

    if m == 0:
        A2 = 0.
    else:
        A2 = m*(np.sin(theta)**(m-1))*np.cos(theta)/2**l
    sum_p_lm = 0.
    sum_p_lm2 = 0.
      
    for t in range(0,int((l-m)/2)+1):
        #t vai de zero ate o ultimo inteiro menor que l-m /2   
        B = ((-1)**t)*math.factorial(2*l-2*t)
        C = math.factorial(t)*math.factorial(l-t)*math.factorial(l-m-2*t)
        D = l - m - 2*t
        
        sum_p_lm += (B/C)*(np.cos(theta)**D)
    
    for t in range(0,int((l-m)/2)+1):
        #t vai de zero ate o ultimo inteiro menor que l-m /2   
        
        B = ((-1)**t)*math.factorial(2*l-2*t)
        C = math.factorial(t)*math.factorial(l-t)*math.factorial(l-m-2*t)
        D = l - m - 2*t
        
        sum_p_lm2 += np.sin(theta)*(B*D/C)*((np.cos(theta))**(D-1))
		
    return (A2*sum_p_lm - A*sum_p_lm2)
	
def s_lm2(l,m,alpha,beta,sig10_2,sig11_2,sig20_2,sig21_2,sig22_2):
    """
        Calculate the variance for each Gauss coefficient.
    
    Parameters:
        l (int): The degree of the Gauss coefficient.
        m (int): The order of the Gauss coefficient.
        alpha (float): The alpha factor since CP88.
        beta (float): The factor from TK03 (can be used as a generic one).
        sig10_2 (float): The squared standard deviation for g10. If sig10_2 is zero, it will be calculated
                         using the same equation as non-dipolar coefficients.
        sig11_2 (float): The squared standard deviation for g11.
        sig20_2 (float): The squared standard deviation for g20.
        sig21_2 (float): The squared standard deviation for g21.
        sig22_2 (float): The squared standard deviation for g22.
        
    Returns:
        float: The calculated variance for the Gauss coefficient.
        
    Notes:
        - l and m are the degree and order of the Gauss coefficient, respectively.
        - alpha is the alpha factor since CP88.
        - beta is a factor from TK03 (can be used as a generic one).
        - If the squared standard deviation for a specific Gauss coefficient is provided, it will be used.
        - The function uses the numpy module.
    """
    c_a = 0.547
    if ((l-m)/2. - int((l-m)/2)) == 0:
        
        s_lm2 = ((c_a**(2*l))*(alpha**2))/((l+1)*(2*l+1))
        
    else:
        
        s_lm2 = (c_a**(2*l))*((alpha*beta)**2)/((l+1)*(2*l+1))
    if (l==1 and m==0):
        if (sig10_2>0):
            #print('sig10=%.2f' % np.sqrt(sig10_2))
            s_lm2 = sig10_2
    if (l==1 and m==1):
        if (sig11_2>0):
            #print('sig11=%.2f' % np.sqrt(sig11_2))
            s_lm2 = sig11_2
    if (l==2 and m==0):
        if (sig20_2>0):
            #print('sig20=%.2f' % np.sqrt(sig20_2))
            s_lm2 = sig20_2
    if (l==2 and m==1):
        if (sig21_2>0):
            #print('sig21=%.2f' % np.sqrt(sig21_2))
            s_lm2 = sig21_2
    if (l==2 and m==2):
        if (sig22_2>0):
            #print('sig22=%.2f' % np.sqrt(sig22_2))
            s_lm2 = sig22_2
        
    return s_lm2


def sig_br2(l,alpha,beta,theta,sig10_2,sig11_2,sig20_2,sig21_2,sig22_2):
    
    """
    Calculate the variance in the r-direction for the magnetic field components.

    Parameters:
        l (int): The maximum degree for calculating.
        alpha (float): The alpha factor since CP88.
        beta (float): The factor from TK03 (can be used as a generic one).
        theta (float): The co-latitude in radians.
        sig10_2 (float): The squared standard deviation for g10.
        sig11_2 (float): The squared standard deviation for g11.
        sig20_2 (float): The squared standard deviation for g20.
        sig21_2 (float): The squared standard deviation for g21.
        sig22_2 (float): The squared standard deviation for g22.

    Returns:
        float: The calculated variance in the r-direction.
     
    Notes:
        - l is the maximum degree for calculating.
        - theta represents the co-latitude, which is the complement of the latitude.
        - The function utilizes the s_lm2() and P_lm() functions.
    """
    sum_l=0
    #print(l,alpha,beta,theta)
    for i in range(1,l+1):
        #print(i)
        A = ((i+1)**2)*s_lm2(i,0,alpha,beta, sig10_2,sig11_2,sig20_2,sig21_2,sig22_2)*(P_lm(i,0,theta)**2)
        
        #print(A)
        sum_m=0.
        for j in range(1,i+1): 
            #print (j)
            B = ((math.factorial(i-j))/(math.factorial(i+j)))*s_lm2(i,j,alpha,beta,sig10_2,sig11_2,sig20_2,sig21_2,sig22_2)*P_lm(i,j,theta)**2
            sum_m = sum_m + B
        #print(((i+1)**2)*2*sum_m)
        sum_l = sum_l + A + ((i+1)**2)*2*sum_m
    return sum_l

def sig_bt2(l,alpha,beta,theta,sig10_2,sig11_2,sig20_2,sig21_2,sig22_2):
    """
    Calculate the variance in the Theta-direction (North-South direction) for the magnetic field components.

    Parameters:
        l (int): The maximum degree for calculating.
        alpha (float): The alpha factor since CP88.
        beta (float): The factor from TK03 (can be used as a generic one).
        theta (float): The co-latitude in radians.
        sig10_2 (float): The squared standard deviation for g10.
        sig11_2 (float): The squared standard deviation for g11.
        sig20_2 (float): The squared standard deviation for g20.
        sig21_2 (float): The squared standard deviation for g21.
        sig22_2 (float): The squared standard deviation for g22.

    Returns:
        float: The calculated variance in the Theta-direction.

    Notes:
        - l is the maximum degree for calculating.
        - theta represents the co-latitude, which is the complement of the latitude.
        - The function utilizes the s_lm2() and dP_lm_dt() functions.
    """
    sum_l = 0
    
    #print(l,alpha,beta,theta)
    for i in range(1,l+1):
        #print(i)
        A = s_lm2(i,0,alpha,beta,sig10_2,sig11_2,sig20_2,sig21_2,sig22_2)*(dP_lm_dt(i,0,theta)**2)
        
        #print(A)
        sum_m=0.
        for j in range(1,i+1): 
            #print (j)
            B = ((math.factorial(i-j))/(math.factorial(i+j)))*s_lm2(i,j,alpha,beta,sig10_2,sig11_2,sig20_2,sig21_2,sig22_2)*dP_lm_dt(i,j,theta)**2
            sum_m = sum_m + B
        #print(((i+1)**2)*2*sum_m)
        sum_l = sum_l + A + 2*sum_m
    return sum_l
	
def sig_bph2(l,alpha,beta,theta,sig10_2,sig11_2,sig20_2,sig21_2,sig22_2):
    """
    Calculate the variance in the Phi direction (East-West direction) for the magnetic field components.

    Parameters:
        l (int): The maximum degree for calculating.
        alpha (float): The alpha factor since CP88.
        beta (float): The factor from TK03 (can be used as a generic one).
        theta (float): The co-latitude in radians.
        sig10_2 (float): The squared standard deviation for g10.
        sig11_2 (float): The squared standard deviation for g11.
        sig20_2 (float): The squared standard deviation for g20.
        sig21_2 (float): The squared standard deviation for g21.
        sig22_2 (float): The squared standard deviation for g22.

    Returns:
        float: The calculated variance in the Phi direction.

    Notes:
        - l is the maximum degree for calculating.
        - theta represents the co-latitude, which is the complement of the latitude.
        - The function utilizes the s_lm2() and P_lm() functions.
        - If theta is 0, it will be approximated to 89.999999 degrees.
    """
    sum_l = 0
    if theta == 0:
        print('lat=90 will be aproximated to 89.999999')
        theta = np.deg2rad(90-89.999999)
    for i in range(1,l+1):
        sum_m=0.
        for j in range(1,i+1): 
            B = (j**2)*((math.factorial(i-j))/(math.factorial(i+j)))*s_lm2(i,j,alpha,beta,sig10_2,sig11_2,sig20_2,sig21_2,sig22_2)*(P_lm(i,j,theta)**2)
            sum_m = sum_m + B
        #print(((i+1)**2)*2*sum_m)
        sum_l = sum_l + 2*sum_m/(np.sin(theta)**2)
    return sum_l



def cov_br_bt(l,alpha, beta, theta,sig10_2,sig11_2,sig20_2,sig21_2,sig22_2):
    """
    Calculate the covariance between Br and Btheta for a given maximum degree and co-latitude.

    Parameters:
        l (int): The maximum degree for calculating.
        alpha (float): The alpha factor since CP88.
        beta (float): The factor from TK03 (can be used as a generic one).
        theta (float): The co-latitude in radians.
        sig10_2 (float): The squared standard deviation for g10.
        sig11_2 (float): The squared standard deviation for g11.
        sig20_2 (float): The squared standard deviation for g20.
        sig21_2 (float): The squared standard deviation for g21.
        sig22_2 (float): The squared standard deviation for g22.

    Returns:
        float: The calculated covariance between Br and Btheta.

    Notes:
        - l is the maximum degree for calculating.
        - theta represents the co-latitude, which is the complement of the latitude.
        - The function utilizes the s_lm2(), P_lm(), and dP_lm_dt() functions.
    """
    sum_l = 0.
    for i in range(1,l+1):
        A = s_lm2(i,0,alpha,beta,sig10_2,sig11_2,sig20_2,sig21_2,sig22_2)*P_lm(i,0,theta)*dP_lm_dt(i,0,theta)
        sum_m = 0.
        for j in range(1,i+1):
            B = (math.factorial(i-j)/math.factorial(i+j))*s_lm2(i,j,alpha,beta,sig10_2,sig11_2,sig20_2,sig21_2,sig22_2)*P_lm(i,j,theta)*dP_lm_dt(i,j,theta)
            sum_m += B
        sum_l = sum_l -(i+1)*(A+2*sum_m)
    return sum_l 

def Cov(alpha,beta,lat, degree,sig10_2,sig11_2,sig20_2,sig21_2,sig22_2):
    """
    Calculate the covariance matrix for a given GGP model at a specified latitude.

    Parameters:
        alpha (float): The alpha factor since CP88.
        beta (float): The factor from TK03 (can be used as a generic one).
        lat (float): The latitude in degrees.
        degree (int): The maximum degree of Gaussian coefficients.
        sig10_2 (float): The squared standard deviation for g10.
        sig11_2 (float): The squared standard deviation for g11.
        sig20_2 (float): The squared standard deviation for g20.
        sig21_2 (float): The squared standard deviation for g21.
        sig22_2 (float): The squared standard deviation for g22.

    Returns:
        numpy.ndarray: The covariance matrix.

    Notes:
        - The latitude is specified in degrees.
        - The function utilizes the sig_bt2(), cov_br_bt(), sig_bph2(), and sig_br2() functions.
    """

    theta = np.deg2rad(90-lat)
    Cov = np.zeros([3,3])
    Cov[0,0] = sig_bt2(degree,alpha,beta,theta,sig10_2,sig11_2,sig20_2,sig21_2,sig22_2) 
    Cov[0,2] = cov_br_bt(degree,alpha,beta,theta,sig10_2,sig11_2,sig20_2,sig21_2,sig22_2) 
    Cov[1,1] = sig_bph2(degree,alpha,beta,theta,sig10_2,sig11_2,sig20_2,sig21_2,sig22_2)
    Cov[2,0] = cov_br_bt(degree,alpha,beta,theta,sig10_2,sig11_2,sig20_2,sig21_2,sig22_2) 
    Cov[2,2] = sig_br2(degree,alpha,beta,theta,sig10_2,sig11_2,sig20_2,sig21_2,sig22_2)
    
    return Cov

def Cov_modelo(GGPmodel,lat, degree):
    """
    Calculate the covariance matrix using the provided GGP model and latitude.

    Parameters:
        GGPmodel (dict): The GGP model dictionary containing the model coefficients and standard deviations.
        lat (float): The latitude in degrees.
        degree (int): The maximum degree of Gaussian coefficients.

    Returns:
        numpy.ndarray: The covariance matrix.

    Notes:
        - The latitude is specified in degrees.
        - The GGPmodel dictionary should contain the following keys: 'g10', 'g20', 'g30', 'sig10', 'sig11', 'sig20', 'sig21', 'sig22', 'alpha', and 'beta'.
        - The function utilizes the sig_bt2(), cov_br_bt(), sig_bph2(), and sig_br2() functions.
    """
    g10 = GGPmodel['g10']
    g20 = GGPmodel['g20']

    g10 = GGPmodel['g10']
    g20 = GGPmodel['g20']
    g30 = GGPmodel['g30']
    sig10_2 = GGPmodel['sig10']**2
    sig11_2 = GGPmodel['sig11']**2
    sig20_2 = GGPmodel['sig20']**2
    sig21_2 = GGPmodel['sig21']**2
    sig22_2 = GGPmodel['sig22']**2
    
    alpha = GGPmodel['alpha']
    beta = GGPmodel['beta']
    
    theta = np.deg2rad(90-lat)
    Cov = np.zeros([3,3])
    Cov[0,0] = sig_bt2(degree,alpha,beta,theta,sig10_2,sig11_2,sig20_2,sig21_2,sig22_2) 
    Cov[0,2] = cov_br_bt(degree,alpha,beta,theta,sig10_2,sig11_2,sig20_2,sig21_2,sig22_2) 
    Cov[1,1] = sig_bph2(degree,alpha,beta,theta,sig10_2,sig11_2,sig20_2,sig21_2,sig22_2)
    Cov[2,0] = cov_br_bt(degree,alpha,beta,theta,sig10_2,sig11_2,sig20_2,sig21_2,sig22_2) 
    Cov[2,2] = sig_br2(degree,alpha,beta,theta,sig10_2,sig11_2,sig20_2,sig21_2,sig22_2)
    return Cov
	
def xy_eq2u_3D(x,y,hem=1):
    """
    Convert a given x, y pair from an equal area plot to the u vector in a 3D coordinate system.

    Parameters:
        x (float): The x-coordinate.
        y (float): The y-coordinate.
        hem (int): The hemisphere indicator. Default is 1.

    Returns:
        numpy.ndarray: The u vector of length 3.

    Notes:
        - The function assumes the vector u = (u1, u2, u3) is unitary (size 1) and points to the Z vertical.
        - The function returns an array of length 3 representing the u vector.
        - The x, y pair is assumed to come from an equal area plot.
        - The hem parameter determines the hemisphere of the u vector (1 for northern hemisphere, -1 for southern hemisphere).
    """
    if x==0 and y==0:
        u[0] = 0.
        u[1] = 0.
    else:
        u[0]=y*np.sqrt(1 - (1 - x**2 - y**2)**2)/np.sqrt(x**2 + y**2)
        u[1]=x*np.sqrt(1 - (1 - x**2 - y**2)**2)/np.sqrt(x**2 + y**2)
    if hem==1:
        u[2] = 1 - x**2 - y**2
    if hem == -1:
        u[2] = -(1 - x**2 - y**2)
    return u

def u3D_2_xyeq(v):
    """
    Convert a given vector in 3D (u = (u0, u1, u2)) to the x and y coordinates of an equal area projection.

    Parameters:
        v (numpy.ndarray): The vector in 3D represented as an array of length 3.

    Returns:
        tuple: A tuple containing the x and y coordinates of the equal area projection.

    Notes:
        - The function assumes the vector u = (u0, u1, u2) is a 3D vector.
        - The function returns a tuple of length 2 representing the x and y coordinates of the equal area projection.
        - The equal area projection is derived from the given 3D vector.
    """
    u = v/np.sqrt(v[0]**2+v[1]**2+v[2]**2)
    x = u[1]*np.sqrt(1 - np.abs(u[2]))/np.sqrt(u[0]**2 + u[1]**2)
    y = u[0]*np.sqrt(1 - np.abs(u[2]))/np.sqrt(u[0]**2 + u[1]**2)
    
    return x,y

def su(x,y,hem,Lamb,m_norm,m):
    """
    Calculate the density function su based on the Khokhlov et al. 2006 model for a given x and y.

    Parameters:
        x (float): The x-coordinate.
        y (float): The y-coordinate.
        hem (int): Hemisphere side indicator. 1 represents the positive hemisphere, -1 represents the negative hemisphere.
        Lamb (numpy.ndarray): The Lamb matrix.
        m_norm (float): The normalized m value.
        m (numpy.ndarray): The m vector.

    Returns:
        float: The value of the density function su.

    Notes:
        - The function calculates the density function su using the Khokhlov et al. 2006 model.
        - The GGPmodel is not used in this function. It's mentioned in the docstring but not used in the code.
        - The degree, dx, and dy variables mentioned in the docstring are not used in this function.
        - The function returns the calculated value of the density function su based on the given inputs.
    """
    u = np.zeros(3)
    if x==0 and y==0:
        u[0] = 0.
        u[1] = 0.
    else:
        u[0] = y*np.sqrt(1 - (1-x**2 - y**2)**2) / np.sqrt(x**2 + y**2)
        u[1] = x*np.sqrt(1 - (1-x**2 - y**2)**2) / np.sqrt(x**2 + y**2)
    if hem==1:
        u[2] = 1 - x**2 - y**2
    if hem == -1:
        u[2] = -(1 - x**2 - y**2)

    u_norm = np.sqrt(np.dot(np.matmul(Lamb,u),u))

    z = (np.dot(np.matmul(Lamb,m),u))/u_norm
    
    s_u1=np.exp(-0.5*m_norm**2)*np.sqrt(np.linalg.det(Lamb))/(4*np.pi*u_norm**3)
    
    s_u2=z*np.sqrt(2/np.pi) + np.exp(0.5*z**2)*(1+z**2)*(1+sp.special.erf(z/np.sqrt(2)))
    
    su = s_u1*s_u2
    
    return su

	
def su_GGPmodel(GGPmodel,lat,degree,dx,dy,hem):
    """
    Calculate the map of the density function su based on the Khokhlov et al. 2013 model.

    Parameters:
        GGPmodel (dict): A dictionary with the parameters of a zonal GGP.
        lat (float): The latitude.
        degree (int): The degree in which the covariance is calculated.
        dx (float): The space in the X-axis of the equal area projection.
        dy (float): The space in the Y-axis of the equal area projection.
        hem (int): Hemisphere side indicator. 1 represents the positive hemisphere, -1 represents the negative hemisphere.

    Returns:
        tuple: A tuple containing the calculated values:
            - m (numpy.ndarray): The m vector.
            - X (numpy.ndarray): The X-coordinates.
            - Y (numpy.ndarray): The Y-coordinates.
            - XX (numpy.ndarray): The meshgrid of X-coordinates.
            - YY (numpy.ndarray): The meshgrid of Y-coordinates.
            - s (numpy.ndarray): The map of the density function su.

    Notes:
        - The function calculates the density function su based on the Khokhlov et al. 2013 model.
        - The GGPmodel dictionary contains the parameters of a zonal GGP.
        - The degree parameter specifies the degree in which the covariance is calculated.
        - The dx and dy parameters determine the spacing in the X and Y axes of the equal area projection.
        - The hem parameter is used to indicate the hemisphere side (positive or negative).
        - The function returns multiple arrays representing different calculated values.
    """
    m = m_TAF(GGPmodel, lat)
    Cov = Cov_modelo(GGPmodel,lat,degree)
    Lamb = np.linalg.inv(Cov)

    m_norm = np.sqrt(np.dot(np.matmul(Lamb,m),m))
    
    n = int(1/dx)
    X = np.arange(-n*dx,n*dx+dx,dx)
    
    n = int(1/dy)
    Y = np.arange(-n*dy,n*dy+dy,dy)

    XX,YY = np.meshgrid(X,Y)
    s = np.zeros(np.shape(XX))
    
    for i in range(np.shape(XX)[0]):
        for j in range(np.shape(XX)[1]):
            if (XX[i,j]**2 + YY[i,j]**2)<=1 :
                s[i,j] = su(XX[i,j],YY[i,j],hem,Lamb,m_norm,m)
    
    return m,X,Y,XX,YY,s

def GGP_LL(GGPmodel,lat,degree,di_block):
    """
    Calculate the log-likelihood of a zonal GGP based on the density function su from Khokhlov et al. 2013.

    Parameters:
        GGPmodel (dict): A dictionary with the parameters of a zonal GGP.
        lat (float): The latitude.
        degree (int): The degree in which the covariance is calculated.
        di_block (list or array-like): The di_block values as a 2D array-like structure with columns [D, I].

    Returns:
        float: The log-likelihood of the zonal GGP.

    Notes:
        - The function calculates the log-likelihood of a zonal GGP based on the density function su from Khokhlov et al. 2013.
        - The GGPmodel dictionary contains the parameters of a zonal GGP.
        - The degree parameter specifies the degree in which the covariance is calculated.
        - The di_block parameter is an array-like structure with columns [D, I] representing direction blocks.
        - The function calculates the Cartesian coordinates (XX, YY) from the given direction blocks.
        - The function calculates the density function su based on the calculated coordinates and other parameters.
        - The log-likelihood is computed by summing the logarithm of the density function values.
    """
    di_block = np.asarray(di_block)
    D = di_block[:,0]
    I = di_block[:,1]

    m = m_TAF(GGPmodel, lat)
    Cov = Cov_modelo(GGPmodel,lat,degree)
    Lamb = np.linalg.inv(Cov)
    m_norm = np.sqrt(np.dot(np.matmul(Lamb,m),m))
    
    hem = np.sign(I)
    n = np.size(D)
    XX = np.zeros(n)
    YY = np.zeros(n)
    for i in range(n):
        u = dir2cart((D[i],I[i]))
        XX[i],YY[i] = u3D_2_xyeq(np.squeeze(u))

    s = np.zeros(np.shape(XX))
    
    for i in range(np.shape(XX)[0]):
        if (XX[i]**2 + YY[i]**2)<=1 :
            s[i] = su(XX[i],YY[i],hem[i],Lamb,m_norm,m)

    return np.sum(np.log(s))

def GGP_pdf(GGPmodel,lat,degree,xyz):
    """
    Calculate the density function values for a zonal GGP based on the su function from Khokhlov et al. 2013.

    Parameters:
        GGPmodel (dict): A dictionary with the parameters of a zonal GGP.
        lat (float): The latitude.
        degree (int): The degree in which the covariance is calculated.
        xyz (array-like): The input vectors in 3D coordinates.

    Returns:
        array-like: The density function values for the zonal GGP.

    Notes:
        - The function calculates the density function values for a zonal GGP based on the su function from Khokhlov et al. 2013.
        - The GGPmodel dictionary contains the parameters of a zonal GGP.
        - The degree parameter specifies the degree in which the covariance is calculated.
        - The xyz parameter is an array-like structure with shape (3, n) representing n input vectors in 3D coordinates.
        - The function calculates the Cartesian coordinates (XX, YY) from the given 3D vectors.
        - The function calculates the density function su based on the calculated coordinates and other parameters.
        - The density function values are returned as an array-like structure.
    """
    m = m_TAF(GGPmodel, lat)
    Cov = Cov_modelo(GGPmodel,lat,degree)
    Lamb = np.linalg.inv(Cov)
    m_norm = np.sqrt(np.dot(np.matmul(Lamb,m),m))
    
    n = np.size(xyz,axis=1)
    hem = np.zeros(n)
    XX = np.zeros(n)
    YY = np.zeros(n)
    
    for i in range(n):
        #u = dir2cart(xyz[:,i])
        u = xyz[:,i]
        hem[i] = np.sign(u[2])
        XX[i],YY[i] = u3D_2_xyeq(np.squeeze(u))

    s = np.zeros(np.shape(XX))
    
    for i in range(np.shape(XX)[0]):
        if (XX[i]**2 + YY[i]**2)<=1 :
            s[i] = su(XX[i],YY[i],hem[i],Lamb,m_norm,m)

    return s

def Rt(theta):
    """
    Calculate the rotation matrix for a given angle theta, only along the plane of north and vertical.

    Parameters:
        theta (float): The angle of rotation in degrees.

    Returns:
        array-like: The 3x3 rotation matrix.

    Notes:
        - The function calculates a rotation matrix for the given angle theta.
        - The rotation is performed only along the plane of north and vertical.
        - The theta parameter specifies the angle of rotation in degrees.
        - The function constructs a 3x3 rotation matrix R based on the calculated values.
        - The rotation matrix is returned as an array-like structure.
    """
    R = np.zeros([3,3])
    R[0,0] = np.cos(np.deg2rad(theta))
    R[0,2] = np.sin(np.deg2rad(theta))
    R[1,1] = 1.0
    R[2,0] = -np.sin(np.deg2rad(theta))
    R[2,2] = np.cos(np.deg2rad(theta))
    
    return R
	
def su_GGPmodel_r(GGPmodel,lat,degree,XX,YY,hem):
    """
    Returns a map of the density function su from Khokhlov et al 2013, rotated to the center of the projection.

    Parameters:
        GGPmodel (dict): Dictionary with the parameters of a zonal GGP.
        lat (float): Latitude value.
        degree (int): The degree in which the covariance is calculated.
        XX (array-like): X-coordinates of the equal area projection.
        YY (array-like): Y-coordinates of the equal area projection.
        hem (int): Hemisphere side (1 means positive, -1 means negative).

    Returns:
        tuple: A tuple containing the magnetic field values (m) and the density function values (s).

    Notes:
        - The function calculates the density function su from Khokhlov et al 2013, rotated to the center of the projection.
        - The GGPmodel parameter is a dictionary containing the parameters of a zonal GGP.
        - The lat parameter specifies the latitude value.
        - The degree parameter determines the degree in which the covariance is calculated.
        - The XX and YY parameters represent the X and Y coordinates of the equal area projection, respectively.
        - The hem parameter indicates the hemisphere side (1 for positive, -1 for negative).
        - The function performs necessary calculations to rotate the density function to the center of the projection.
        - It calculates the rotated magnetic field values (m_r), covariance matrix (Cov_r), and the inverse of Cov_r (Lamb).
        - The m_norm parameter is the magnitude of the rotated magnetic field.
        - The function iterates over the XX and YY arrays and calculates the density function values (s) using the su function.
        - The resulting magnetic field values (m) and density function values (s) are returned as a tuple.
    """
    m = m_TAF(GGPmodel, lat)
    Cov = Cov_modelo(GGPmodel,lat,degree)
    pol=-GGPmodel['g10']/abs(GGPmodel['g10'])
    #print(pol)
    #print(m[0]/abs(m[0]))
    B = np.sqrt(m[0]**2+m[1]**2+m[2]**2)
    m_r = np.zeros(3)
    m_r[2] = B #The total field in the vertical axis - because we want the rotated distribution
    Binc = np.rad2deg(np.arctan(m[2]/np.sqrt(m[0]**2+m[1]**2)))

    Cov_r = np.matmul(np.matmul(Rt(-pol*(90-Binc)),Cov),np.transpose(Rt(-pol*(90-Binc))))
    Lamb = np.linalg.inv(Cov_r)

    m_norm = np.sqrt(np.dot(np.matmul(Lamb,m_r),m_r))
    
    s = np.zeros(np.shape(XX))
    
    for i in range(np.shape(XX)[0]):
        for j in range(np.shape(XX)[1]):
            if (XX[i,j]**2 + YY[i,j]**2)<=1 :
                s[i,j] = su(XX[i,j],YY[i,j],hem,Lamb,m_norm,m_r)
    
    return m,s	

def s_lm(l,m,alpha,beta,sig10_2,sig11_2,sig20_2,sig21_2,sig22_2):
    """
    Calculates the standard deviation for each Gauss coefficient.

    Parameters:
        l (int): The degree.
        m (int): The order.
        alpha (float): The alpha factor since CP88.
        beta (float): The factor from TK03.
        sig10_2 (float): The squared standard deviation for g10. For CP88, if sig10 is 3, sig10_2 should be 9.
        sig11_2 (float): The squared standard deviation for g11.
        sig20_2 (float): The squared standard deviation for g20.
        sig21_2 (float): The squared standard deviation for g21.
        sig22_2 (float): The squared standard deviation for g22.

    Returns:
        float: The calculated standard deviation for the Gauss coefficient.

    Notes:
        - The function calculates the standard deviation for each Gauss coefficient based on the provided inputs.
        - The l and m parameters represent the degree and order, respectively.
        - The alpha parameter is the alpha factor since CP88.
        - The beta parameter is the factor from TK03.
        - The sig10_2, sig11_2, sig20_2, sig21_2, and sig22_2 parameters are squared standard deviations for specific Gauss coefficients.
        - If sig10_2 is zero, the function calculates it using the same equation as non-dipolar coefficients.
        - The function uses conditional statements to check if specific coefficients have non-zero squared standard deviations,
          and if so, it updates the s_lm2 value accordingly.
        - The calculated standard deviation (s_lm2) is returned as the square root of s_lm2.
    """

    c_a = 0.547
    if ((l-m)/2. - int((l-m)/2)) == 0:
        
        s_lm2 = ((c_a**(2*l))*(alpha**2))/((l+1)*(2*l+1))
        
    else:
        
        s_lm2 = (c_a**(2*l))*((alpha*beta)**2)/((l+1)*(2*l+1))
    if (l==1 and m==0):
        if (sig10_2>0):
            s_lm2 = sig10_2
    if (l==1 and m==1):
        if (sig11_2>0):
            s_lm2 = sig11_2
    if (l==2 and m==0):
        if (sig20_2>0):
            s_lm2 = sig20_2
    if (l==2 and m==1):
        if (sig21_2>0):
            s_lm2 = sig21_2
    if (l==2 and m==2):
        if (sig22_2>0):
            s_lm2 = sig22_2
        
    return np.sqrt(s_lm2)

def s_lmGGP(terms,GGPmodel):
    """
    Generates a list of sigma l m drawn from a given GGP model.

    Parameters:
        terms (int): The number of terms.
        GGPmodel (dict): A dictionary containing the GGP model parameters.

    Returns:
        tuple: A tuple containing two lists: all_s (list of standard deviations) and degrees (list of degree and order arrays).

    Notes:
        - The function is modified from pmagpy (mktk03(terms, seed, G2, G3)).
        - The GGPmodel dictionary should contain the following keys:
            - 'g10': g10 value
            - 'g20': g20 value
            - 'g30': g30 value
            - 'sig10': sig10 value
            - 'sig11': sig11 value
            - 'sig20': sig20 value
            - 'sig21': sig21 value
            - 'sig22': sig22 value
            - 'alpha': alpha value
            - 'beta': beta value
        - The function initializes empty lists to store standard deviations (all_s) and degree and order arrays (degrees).
        - It calculates the standard deviation (s) for the l=1, m=0 coefficient and appends it to all_s along with the degree [1, 0].
        - It calculates the standard deviation (s) for the l=1, m=1 coefficient and appends it to all_s along with the degree [1, 1].
        - It appends the same degree [1, 1] and standard deviation (s) to all_s and degrees again.
        - It then iterates over l from 2 to terms and over m from 0 to l.
            - For each combination of l and m, it calculates the standard deviation (s) using the s_lm function and appends it to all_s along with the degree [l, m].
            - If m is non-zero, it appends the same degree [l, m] and standard deviation (s) to all_s and degrees again.
        - Finally, it returns a tuple containing the all_s and degrees lists.
    """
    
    g10 = GGPmodel['g10']
    g20 = GGPmodel['g20']
    g30 = GGPmodel['g30']
    sig10 = GGPmodel['sig10']
    sig11 = GGPmodel['sig11']
    sig20 = GGPmodel['sig20']
    sig21 = GGPmodel['sig21']
    sig22 = GGPmodel['sig22']
    
    alpha = GGPmodel['alpha']
    beta = GGPmodel['beta']

    all_s = []
    degrees = []
    
    s = s_lm(1,0,alpha,beta,sig10**2,sig11**2,sig20**2,sig21**2,sig22**2)
    deg = np.array([1,0])
    
    all_s.append(s)
    degrees.append(deg)
    
    s = s_lm(1,1,alpha,beta,sig10**2,sig11**2,sig20**2,sig21**2,sig22**2)
    deg = np.array([1,1])
    
    all_s.append(s)
    degrees.append(deg)
    
    deg = np.array([1,1])
    all_s.append(s)
    degrees.append(deg)
    
    for l in range(2,terms+1):
        for m in range(l+1):
            s = s_lm(l,m,alpha,beta,sig10**2,sig11**2,sig20**2,sig21**2,sig22**2)
            deg = np.array([l,m])
            all_s.append(s)
            degrees.append(deg)
            if m!=0:
                deg = np.array([l,m])
                all_s.append(s)
                degrees.append(deg)
    return all_s,degrees

def intxy(M,Integ):
    """
    Calculates the integral in the X-Y plane.

    Parameters:
        M (ndarray): The M matrix representing the function.
        Integ (ndarray): The integration matrix with zeros and dx*dy values.

    Returns:
        float: The calculated integral.

    Notes:
        - The function calculates the integral by multiplying the M matrix with the Integ matrix element-wise and then summing the resulting values.
        - The integration is performed only within the circle of radius 1 in the equal area projection.
    """

    integ = 0.
    integ = np.sum(M*Integ)
    
    return integ

def Med_desvxy_mod(sp,sn,XX,YY,Integ):
    """
    Calculates the mean and standard deviation of x and y using a GGP model.
    Considers directional distribution function results from the positive and negative equal area projections.

    Parameters:
        sp (ndarray): Directional distribution function results from the positive equal area projection.
        sn (ndarray): Directional distribution function results from the negative equal area projection.
        XX (ndarray): X coordinates.
        YY (ndarray): Y coordinates.
        Integ (ndarray): Integration matrix.

    Returns:
        tuple: A tuple containing the following values:
            - normp (float): Normalization factor for the positive equal area projection.
            - normn (float): Normalization factor for the negative equal area projection.
            - xm (float): Mean x-coordinate.
            - ym (float): Mean y-coordinate.
            - xstd (float): Standard deviation of x-coordinate.
            - ystd (float): Standard deviation of y-coordinate.
    """

    normp = intxy(sp,Integ)
    normn = intxy(sn,Integ)
	
    xmp = intxy(XX*sp,Integ)
    xmn = intxy(XX*sn,Integ)
    xm = (xmp+xmn)/(normp+normn)
    ymp = intxy(YY*sp,Integ)
    ymn = intxy(YY*sn,Integ)
    ym = (ymp+ymn)/(normp+normn)
    xstd2p = (intxy((XX-xm)*(XX-xm)*sp,Integ))
    xstd2n = (intxy((XX-xm)*(XX-xm)*sn,Integ))
    xstd = np.sqrt((xstd2p+xstd2n)/(normp+normn))
    ystd2p = (intxy((YY-ym)*(YY-ym)*sp,Integ))
    ystd2n = (intxy((YY-ym)*(YY-ym)*sn,Integ))
    ystd = np.sqrt((ystd2p+ystd2n)/(normp+normn))
	
    return normp,normn,xm,ym,xstd,ystd
	
def covxy_mod(sp,sn,XX,YY,Integ):
    """
    Calculates the covariance between x and y (equal area) using a GGP model.
    Considers directional distribution function results from the positive and negative equal area projections.

    Parameters:
        sp (ndarray): Directional distribution function results from the positive equal area projection.
        sn (ndarray): Directional distribution function results from the negative equal area projection.
        XX (ndarray): X coordinates.
        YY (ndarray): Y coordinates.
        Integ (ndarray): Integration matrix.

    Returns:
        float: Covariance between x and y.
    """

    normp = intxy(sp,Integ)
    normn = intxy(sn,Integ)
	
    xmp = intxy(XX*sp,Integ)
    xmn = intxy(XX*sn,Integ)
    xm = (xmp+xmn)/(normp+normn)
    ymp = intxy(YY*sp,Integ)
    ymn = intxy(YY*sn,Integ)
    ym = (ymp+ymn)/(normp+normn)
    
    covxyp = (intxy((XX-xm)*(YY-ym)*sp,Integ))
    covxyn = (intxy((XX-xm)*(YY-ym)*sn,Integ))
    covxy = (covxyp+covxyn)/(normp+normn)
	
	
    
	
    return covxy

def Med_desvxy_covxy_mod(sp,sn,XX,YY,Integ):
    """
    Calculates the mean (x, y), standard deviation of x and y, and covariance of x and y using a GGP model.
    The calculations are based on the directional distribution function results from the positive and negative equal area projections (sp and sn).

    Parameters:
        sp (numpy.ndarray): Positive equal area projection directional distribution function.
        sn (numpy.ndarray): Negative equal area projection directional distribution function.
        XX (numpy.ndarray): Array of x-values.
        YY (numpy.ndarray): Array of y-values.
        Integ (float): Integration value.

    Returns:
        tuple: A tuple containing the following values:
            - normp (float): Normalization factor for the positive equal area projection.
            - normn (float): Normalization factor for the negative equal area projection.
            - xm (float): Mean of x.
            - ym (float): Mean of y.
            - xstd (float): Standard deviation of x.
            - ystd (float): Standard deviation of y.
            - covxy (float): Covariance of x and y.
    """
    normp = intxy(sp,Integ)
    normn = intxy(sn,Integ)
	
    xmp = intxy(XX*sp,Integ)
    xmn = intxy(XX*sn,Integ)
    xm = (xmp+xmn)/(normp+normn)
    ymp = intxy(YY*sp,Integ)
    ymn = intxy(YY*sn,Integ)
    ym = (ymp+ymn)/(normp+normn)
    xstd2p = (intxy((XX-xm)*(XX-xm)*sp,Integ))
    xstd2n = (intxy((XX-xm)*(XX-xm)*sn,Integ))
    xstd = np.sqrt((xstd2p+xstd2n)/(normp+normn))
    ystd2p = (intxy((YY-ym)*(YY-ym)*sp,Integ))
    ystd2n = (intxy((YY-ym)*(YY-ym)*sn,Integ))
    ystd = np.sqrt((ystd2p+ystd2n)/(normp+normn))
	
    covxyp = (intxy((XX-xm)*(YY-ym)*sp,Integ))
    covxyn = (intxy((XX-xm)*(YY-ym)*sn,Integ))
    covxy = (covxyp+covxyn)/(normp+normn)
	
    return normp,normn,xm,ym,xstd,ystd,covxy

def Med_desvxy_sim(lista_xy):
    """
    Calculates the mean x and y and the standard deviation of x and y using a list of results
    in x, y coordinates (equal area coordinates).

    Parameters:
        lista_xy (ndarray): List of results in x, y coordinates.

    Returns:
        tuple: Tuple containing the mean x-coordinate, mean y-coordinate, standard deviation of x,
               and standard deviation of y.
    """
    xm = np.average(lista_xy[:,0])
    ym = np.average(lista_xy[:,1])
    
    xstd = np.std(lista_xy[:,0],ddof=1)
    ystd = np.std(lista_xy[:,1],ddof=1)
    
    return xm,ym,xstd,ystd

def covvxy_sim(lista_xy):
    """
    Calculates the covariance between x and y using a list of results in x, y coordinates (equal area coordinates).

    Parameters:
        lista_xy (ndarray): List of results in x, y coordinates.

    Returns:
        float: Covariance between x and y.

    """

    xm = np.average(lista_xy[:,0])
    ym = np.average(lista_xy[:,1])
    cov_xys = (sum((lista_xy[:,0]-xm)*(lista_xy[:,1]-ym))/len(lista_xy))
    
    return cov_xys
	
def det_cov_xy_sim(lista_xy):
    """
    Calculates the determinant of the covariance matrix between x and y using a list of results in x, y coordinates (equal area coordinates).

    Parameters:
        lista_xy (ndarray): List of results in x, y coordinates.

    Returns:
        float: Determinant of the covariance matrix between x and y.

    """
    xm = np.average(lista_xy[:,0])
    ym = np.average(lista_xy[:,1])
	
    xstd = np.std(lista_xy[:,0],ddof=1)
    ystd = np.std(lista_xy[:,1],ddof=1)
	
    cov_xys = (sum((lista_xy[:,0]-xm)*(lista_xy[:,1]-ym))/len(lista_xy))
	
    det = (xstd**2)*(ystd**2) - cov_xys**2
    
    return det

def integ(dx,dy):
    """
    Calculates the numerical integral of one * dx * dy inside the circle of equal area.

    Parameters:
        dx (float): Step size in the x-direction.
        dy (float): Step size in the y-direction.

    Returns:
        tuple: Tuple containing the following elements:
            - Integ (ndarray): Matrix representing the numerical integral values.
            - XX (ndarray): Meshgrid of X values.
            - YY (ndarray): Meshgrid of Y values.
            - X (ndarray): Array of X values.
            - Y (ndarray): Array of Y values.

    """

    n = int(1/dx)
    X = np.arange(-n*dx,n*dx+dx,dx)
    
    n = int(1/dy)
    Y = np.arange(-n*dy,n*dy+dy,dy)


    XX,YY = np.meshgrid(X,Y)
    Integ = np.zeros(np.shape(XX)) #matrix that will be used every integration
    for i in range(np.shape(XX)[0]):
        for j in range(np.shape(YY)[1]):
            if np.sqrt((XX[i,j]+0.5*dx)**2+(YY[i,j]+0.5*dy)**2)<=1 and np.sqrt((XX[i,j]-0.5*dx)**2+(YY[i,j]-0.5*dy)**2)<=1:
                if np.sqrt((XX[i,j]-0.5*dx)**2+(YY[i,j]+0.5*dy)**2)<=1 and np.sqrt((XX[i,j]+0.5*dx)**2+(YY[i,j]-0.5*dy)**2)<=1:
                    #it will consider only squares inside the equal area circle
                    Integ[i,j] = dx*dy
    return Integ/np.sum(Integ), XX, YY, X, Y

def integ_x(dx,dy):
    """
    Calculates the numerical integral of one * dx inside the circle of equal area.

    Parameters:
        dx (float): Step size in the x-direction.
        dy (float): Step size in the y-direction.

    Returns:
        tuple: Tuple containing the following elements:
            - Integ (ndarray): Matrix representing the numerical integral values.
            - XX (ndarray): Meshgrid of X values.
            - YY (ndarray): Meshgrid of Y values.
            - X (ndarray): Array of X values.
            - Y (ndarray): Array of Y values.

    """
    n = int(1/dx)
    X = np.arange(-n*dx,n*dx+dx,dx)
    
    n = int(1/dy)
    Y = np.arange(-n*dy,n*dy+dy,dy)


    XX,YY = np.meshgrid(X,Y)
    Integ = np.zeros(np.shape(XX)) #matrix that will be used every integration
    for i in range(np.shape(XX)[0]):
        for j in range(np.shape(YY)[1]):
            if np.sqrt((XX[i,j]+0.5*dx)**2+(YY[i,j]+0.5*dy)**2)<=1 and np.sqrt((XX[i,j]-0.5*dx)**2+(YY[i,j]-0.5*dy)**2)<=1:
                if np.sqrt((XX[i,j]-0.5*dx)**2+(YY[i,j]+0.5*dy)**2)<=1 and np.sqrt((XX[i,j]+0.5*dx)**2+(YY[i,j]-0.5*dy)**2)<=1:
                    #it will consider only squares inside the equal area circle
                    Integ[i,j] = dx
    return Integ/np.sum(Integ), XX, YY, X, Y

def integ_y(dx,dy):
    """
    Calculates the numerical integral of one * dy inside the circle of equal area.

    Parameters:
        dx (float): Step size in the x-direction.
        dy (float): Step size in the y-direction.

    Returns:
        tuple: Tuple containing the following elements:
            - Integ (ndarray): Matrix representing the numerical integral values.
            - XX (ndarray): Meshgrid of X values.
            - YY (ndarray): Meshgrid of Y values.
            - X (ndarray): Array of X values.
            - Y (ndarray): Array of Y values.

    """

    n = int(1/dx)
    X = np.arange(-n*dx,n*dx+dx,dx)
    
    n = int(1/dy)
    Y = np.arange(-n*dy,n*dy+dy,dy)


    XX,YY = np.meshgrid(X,Y)
    Integ = np.zeros(np.shape(XX)) #matrix that will be used every integration
    for i in range(np.shape(XX)[0]):
        for j in range(np.shape(YY)[1]):
            if np.sqrt((XX[i,j]+0.5*dx)**2+(YY[i,j]+0.5*dy)**2)<=1 and np.sqrt((XX[i,j]-0.5*dx)**2+(YY[i,j]-0.5*dy)**2)<=1:
                if np.sqrt((XX[i,j]-0.5*dx)**2+(YY[i,j]+0.5*dy)**2)<=1 and np.sqrt((XX[i,j]+0.5*dx)**2+(YY[i,j]-0.5*dy)**2)<=1:
                    #it will consider only squares inside the equal area circle
                    Integ[i,j] = dy
    return Integ/np.sum(Integ), XX, YY, X, Y
	
	
def zonal(lat,g10=-18,G2=0.0,G3=0.0,G4=0.0,a_r=1.0):
    """
    Calculates the zonal field for a given latitude and returns the horizontal and vertical components Btetha, Br.

    Parameters:
        lat (float): Latitude in degrees.
        g10 (float): Gauss coefficient g10 (default: -18).
        G2 (float): Gauss coefficient G2 (default: 0.0).
        G3 (float): Gauss coefficient G3 (default: 0.0).
        G4 (float): Gauss coefficient G4 (default: 0.0).
        a_r (float): Earth radius divided by the distance from the center of the Earth (default: 1.0).

    Returns:
        tuple: Tuple containing the following elements:
            - Bttot (float): Total horizontal component Btetha.
            - Brtot (float): Total vertical component Br.

    """
    
    Theta = 90-lat
    g20 = G2*g10
    g30 = G3*g10
    g40 = G4*g10

    costheta = np.cos(np.deg2rad(Theta))
    sintheta = np.sin(np.deg2rad(Theta))

    Br1 = 2*(a_r**3)*g10*costheta
    Br2 = (3*g20/2)*(a_r**4)*(3*(costheta**2) - 1)
    Br3 = (a_r**5)*(2*g30)*(5*(costheta**3) - 3*costheta)
    Br4 = (a_r**6)*(5*g40/8)*(35*(costheta**4) - 30*(costheta**2)+3)


    Bt1 = (a_r**3)*g10*sintheta
    Bt2 =  (a_r**4)*(3*g20)*sintheta*costheta
    Bt3 = (a_r**5)*(g30/2)*(15*sintheta*(costheta**2) - 3*sintheta)
    Bt4 = (a_r**6)*(g40/2)*(35*sintheta*(costheta**3) - 15*sintheta*costheta)


    Brtot = Br1+Br2+Br3+Br4 
    Bttot = Bt1+Bt2+Bt3+Bt4 
    
    Bx = -Bttot #bx eh bteta negativo
    By = 0
    Bz = -Brtot #bz eh br negativo
    H = np.sqrt(Bx**2 + By**2 )

    Inc = np.rad2deg(np.arctan(Bz/H))
    
    return Bttot, Brtot

def m_TAF(GGPmodel, lat):
    """
    Calculates the Time Average Field (TAF) for a given GGP model dictionary.

    Parameters:
        GGPmodel (dict): GGP model dictionary containing the following keys:
            - 'g10' (float): Gauss coefficient g10.
            - 'g20' (float): Gauss coefficient g20.
            - 'g30' (float): Gauss coefficient g30.

        lat (float): Latitude in degrees.

    Returns:
        ndarray: Array `m` representing the time average field with shape (3,).
            - m[0] (float): Bx component (negative Btetha).
            - m[1] (float): By component (always 0).
            - m[2] (float): Bz component (negative Br).

    """

    m = np.zeros(3)
    Bteta,Br = zonal(lat,GGPmodel['g10'],GGPmodel['g20']/GGPmodel['g10'],GGPmodel['g30']/GGPmodel['g10'])
    m[0] = -Bteta
    m[1] = 0.
    m[2] = -Br
    return m	


def prediction_map_GGP_su_r(lat,GGPmodel,degree=8,dx=0.01,dy=0.01):
    """
    Predicts the map of 'su' rotated to the vertical in an equal-area projection (x, y or x_E and x_N) from a GGP model and a latitude.

    Parameters:
        lat (float): Latitude.
        GGPmodel (dict): A dictionary with information about the GGP model.
        degree (int, optional): Maximum degree for calculating the covariance matrix of the field B. Default is 8.
        dx (float, optional): Spacing for mapping in the x direction. Default is 0.01.
        dy (float, optional): Spacing for mapping in the y direction. Default is 0.01.

    Returns:
        tuple: A tuple containing two arrays, sp and sn.
            - sp: Positive inclination hemisphere 'su' map in the equal-area projection. A 3-column array with x, y, and su.
            - sn: Negative inclination hemisphere 'su' map in the equal-area projection. A 3-column array with x, y, and su.
    """
    n = int(1/dx)
    X = np.arange(-n*dx,n*dx+dx,dx)
    
    n = int(1/dy)
    Y = np.arange(-n*dy,n*dy+dy,dy)


    XX,YY = np.meshgrid(X,Y)
    
   
    hem=1
    m,sp = su_GGPmodel_r(GGPmodel, lat, degree, XX, YY, hem)
    m,sn = su_GGPmodel_r(GGPmodel, lat, degree, XX, YY, -hem)
       
    return sp, sn
    

def prediction_map_GGP_su(lat,GGPmodel,degree=8,dx=0.01,dy=0.01):
    """
    Predicts the map of 'su' in an equal-area projection (x, y or x_E and x_N) from a GGP model and a latitude.

    Parameters:
        lat (float): Latitude.
        GGPmodel (dict): A dictionary with information about the GGP model.
        degree (int, optional): Maximum degree for calculating the covariance matrix of the field B. Default is 8.
        dx (float, optional): Spacing for mapping in the x direction. Default is 0.01.
        dy (float, optional): Spacing for mapping in the y direction. Default is 0.01.

    Returns:
        tuple: A tuple containing four elements.
            - sp: Positive inclination hemisphere 'su' map in the equal-area projection. A 3-column array with x, y, and su.
            - sn: Negative inclination hemisphere 'su' map in the equal-area projection. A 3-column array with x, y, and su.
            - XX: Meshgrid of x values.
            - YY: Meshgrid of y values.
    """
    n = int(1/dx)
    X = np.arange(-n*dx,n*dx+dx,dx)
    
    n = int(1/dy)
    Y = np.arange(-n*dy,n*dy+dy,dy)


    XX,YY = np.meshgrid(X,Y)
    
   
    hem=1
    m,X,Y,XX,YY,sp = su_GGPmodel(GGPmodel, lat, degree, dx, dy, hem)
    m,X,Y,XX,YY,sn = su_GGPmodel(GGPmodel, lat, degree, dx, dy, -hem)
       
    return sp, sn, XX, YY # modified 4/2/23 per Gilder's suggestions
    
def prediction_x_y_std_E_A_GGP(lats,GGPmodel,imprima=False, degree=8,dx=0.01,dy=0.01,hem=1):
    """
    Predicts the x mean, y mean, standard deviation, covariance from a GGP model and a set of latitudes or a single latitude as an array with len=1 -> [lat].
    It returns an array with 7 columns: lat, x, y, sigmax, sigmay, E, Adir.
    If imprima=True, it will print the latitude at each calculation.

    Parameters:
        lats (float or list): Latitude(s).
        GGPmodel (dict): A dictionary with information about the GGP model.
        imprima (bool, optional): Flag to print the latitude at each calculation. Default is False.
        degree (int, optional): Maximum degree for calculating the covariance matrix of the field B. Default is 8.
        dx (float, optional): Spacing for mapping in the x direction. Default is 0.01.
        dy (float, optional): Spacing for mapping in the y direction. Default is 0.01.
        hem (int, optional): Hemisphere (1 for positive inclination, -1 for negative inclination). Default is 1.

    Returns:
        np.ndarray: Array with 7 columns: lat, x, y, sigmax, sigmay, E, Adir.
    """
    n = int(1/dx)
    X = np.arange(-n*dx,n*dx+dx,dx)
    
    n = int(1/dy)
    Y = np.arange(-n*dy,n*dy+dy,dy)


    XX,YY = np.meshgrid(X,Y)
    
    Mod = np.zeros([len(lats),7])
    Mod[:,0] = lats 
    for i in range(len(lats)):
        if imprima==True:
            print('Calculating for the latitude:')
            print(lats[i])
        m,sp = su_GGPmodel_r(GGPmodel, lats[i], degree, XX, YY, hem)
        m,sn = su_GGPmodel_r(GGPmodel, lats[i], degree, XX, YY, -hem)
        
        Integ, XX, YY, X, Y = integ(dx,dy)
                
        normp,normn, xmm, ymm, xstdm, ystdm, covxym = Med_desvxy_covxy_mod(sp,sn,XX, YY, Integ)
        
        Mod[i,1] = xmm
        Mod[i,2] = ymm
        Mod[i,3] = xstdm
        Mod[i,4] = ystdm
        Mod[i,5] = (ystdm**2)/(xstdm**2)
        Mod[i,6] = np.sqrt((ystdm*xstdm)**2 - covxym**2)
        
    return Mod

def plotmap(sp, sn,GGP,lat,dx,dy):
    name = GGP['name']
    n = int(1/dx)
    X = np.arange(-n*dx,n*dx+dx,dx)
    
    n = int(1/dy)
    Y = np.arange(-n*dy,n*dy+dy,dy)


    XX,YY = np.meshgrid(X,Y)
    minp = np.min(sp)
    minn = np.min(sn)
    if minp<minn:
        minimo = minp
    else:
        minimo = minn
    maxp = np.max(sp)
    maxn = np.max(sn)
    if maxp>maxn:
        maximo = maxp
    else:
        maximo = maxn
    fig = plt.figure(figsize=[13,6], dpi=80)
            
    plt.subplot(121)
    xb=np.arange(-1,1.01,0.01)
    ybn=-np.sqrt(abs(1-xb**2))
    ybp=np.sqrt(abs(1-xb**2))
    plt.plot(xb,ybn, '--',c='0.5')
    plt.plot(xb,ybp,'--',c='0.5')
    plt.plot(0,0,'+',c='k')
    plt.axis('off', aspect='equal')
    plt.contour(X,Y,sp,levels=np.linspace(minimo,maximo,8), zorder = 5020)
    plt.text(0.0,0.92,'Lat=%i$^\circ$'%lat,horizontalalignment='center')
    plt.text(0.0,0.85,name,horizontalalignment='center')
    plt.text(0.0,0.78,'Positive inclination', horizontalalignment='center')
                
         
    plt.subplot(122)
    plt.plot(xb,ybn, '--',c='0.5')
    plt.plot(xb,ybp,'--',c='0.5')
    plt.plot(0,0,'+',c='k')
    plt.axis('off', aspect='equal')
    plt.contour(X,Y,sn,levels=np.linspace(minimo,maximo,8),zorder = 5020)
    plt.text(0.0,0.92,'Lat=%i$^\circ$'%lat,horizontalalignment='center')
    plt.text(0.0,0.85,name,horizontalalignment='center')
    plt.text(0.0,0.78,'Negative inclination', horizontalalignment='center')         
     
    plt.show()

def GGPrand(GGPmodel, lat, n,degree=8):
    m = m_TAF(GGPmodel, lat)
    Cov = Cov_modelo(GGPmodel,lat,degree)
    X = np.random.multivariate_normal(m, Cov,n)*1000
    DI = pmag.cart2dir(X)
    return DI

def GGP_vMF_cdfs(GGPmodel, lat, degree,flat=1,kappa=-1,n=2E6):
    
    n = int(n) #size of random samples
    m = m_TAF(GGPmodel, lat) #mean for GGP
    Cov = Cov_modelo(GGPmodel,lat,degree) #covariance matrix for GGP
    XYZ = np.random.multivariate_normal(m, Cov,n)*1000 #GGP random vectos
    XYZ /= np.linalg.norm(XYZ,axis=1)[:,np.newaxis] #normalize to unit length
    
    if flat<1: #perform flattening is required
        DI = pmag.cart2dir(XYZ) #convert to D and I
        DI[:,1] = pmag.squish(DI[:,1],flat) #apply flattening
        #DI[:,1] = pmag.unsquish(DI[:,1],flat) #apply unflattening
        XYZ = pmag.dir2cart(DI) #convert to Cartesian
    
    if kappa>0: #add vMF errors if required
        C = np.eye(3)/kappa #covariance matrix for vMF deviations
        XYZ += np.random.multivariate_normal([0,0,0],C,n) #add vMF deviations to vectors 
        XYZ /= np.linalg.norm(XYZ,axis=1)[:,np.newaxis] #normalize to unit length
    
    DI = pmag.cart2dir(XYZ)
    DI[DI[:,0]>180,0] -=360

    #Estimate ecdfs for inclination and declination 
    nI = 181
    nD = 361
    I0 = np.linspace(-90,90,nI)
    D0 = np.linspace(-180,180,nD)
    Ic = []
    Dc = []

    for I in I0:
        Ic.append(np.sum(DI[:,1]<=I)/n)
    Icdf = PchipInterpolator(np.deg2rad(I0),Ic)
    
    for D in D0:
        Dc.append(np.sum(DI[:,0]<=D)/n)
    Dcdf = PchipInterpolator(np.deg2rad(D0),Dc)
    
    return Icdf, Dcdf
def GGP_cdf(GGPmodel, lat, degree):
    """
    Calculates the cumulative distribution functions (CDFs) of inclinations and declinations for a given GGP model and latitude.

    Parameters:
        GGPmodel (dict): Set of coefficients for a specific GGP model.
        lat (float): Latitude of interest in degrees.
        degree (int): Maximum degree of the GGP model.

    Returns:
        tuple: A tuple containing two PchipInterpolator objects representing the CDFs.
            - Icdf: PchipInterpolator function representing the CDF of inclinations for the given latitude.
            - Dcdf: PchipInterpolator function representing the CDF of declinations for the given latitude.
    """
 
    #set up grid for integration
    nI = 180
    nD = 361
    I0 = np.linspace(-90,90,nI)
    D0 = np.linspace(-180,180,nD)
    z0 = np.cos(np.deg2rad(I0))
    
    #integrate WRT to dec to get marginal distribution as function of inc
    pI = np.zeros(nI)
    for j in range(nI):
        di_block = []

        for i in range(nD):
            di_block.append([D0[i],I0[j]])
    
        xyz = np.asarray(pmag.dir2cart(di_block)).T
        p0 = GGP_pdf(GGPmodel,lat,degree,xyz)
        pI[j] = np.trapz(p0, x=np.deg2rad(D0)*z0[j])

    cI = cumulative_trapezoid(pI, x=np.deg2rad(I0),initial=0)
    Icdf = PchipInterpolator(np.deg2rad(I0),cI) #inclination marginal distribution
    Iinv = PchipInterpolator(cI,np.deg2rad(I0))
    
    #integrate WRT to inc to get marginal distribution as function of dec
    pD = np.zeros(nD)
    for j in range(nD):
        di_block = []

        for i in range(nI):
            di_block.append([D0[j],I0[i]])
    
        xyz = np.asarray(pmag.dir2cart(di_block)).T
        p0 = GGP_pdf(GGPmodel,lat,degree,xyz)
        pD[j] = np.trapz(p0*np.cos(np.deg2rad(I0)), x=np.deg2rad(I0))

    cD = cumulative_trapezoid(pD, x=np.deg2rad(D0),initial=0)
    Dcdf = PchipInterpolator(np.deg2rad(D0),cD) #declination marginal distribution
    Dinv = PchipInterpolator(cD,np.deg2rad(D0))
    
    return Icdf, Dcdf

def AD_inc(Is,Icdf): #AD test for distribution of inclinations
    """
    Anderson-Darling test for the distribution of inclinations.

    Parameters:
        Is (array-like): Array of observed inclinations in degrees.
        Icdf (callable): Pchip function representing the cumulative distribution function (CDF) of inclinations for a given latitude.

    Returns:
        float: Test statistic (A2) for inclinations.

    Notes:
        The Anderson-Darling (AD) test is a statistical test used to assess whether a sample of data comes from a specific probability distribution. This function calculates the AD test statistic for the distribution of inclinations based on the observed inclinations and the CDF of inclinations.

        The AD test statistic measures the discrepancy between the observed data and the expected distribution. A larger AD test statistic indicates a greater discrepancy, suggesting that the observed data may not follow the expected distribution.

        It is important to note that this function assumes the input inclinations are in degrees and converts them to radians internally for consistency with the CDF function.
    """
  
    
    Is = np.deg2rad(np.sort(Is))
    ns = np.size(Is)
    
    #S = 0
    #for i in range(1,ns+1):
    #    S += (2*i-1)/ns*(np.log(Icdf(Is[i-1]))+np.log(1-Icdf(Is[ns-i])))
    
    #A2 = -ns-S
    
    C = Icdf(Is)
    S = np.sum((2*np.arange(1,ns+1)-1)/ns*(np.log(C)+np.log(1-np.flip(C))))
    A2 = -ns-S
    
    return A2

def AD_dec(Ds,Dcdf): #AD test for distribution of declinations
    """
    Anderson-Darling test for the distribution of declinations.

    Parameters:
        Ds (array-like): Array of observed declinations in degrees.
        Dcdf (callable): Pchip function representing the cumulative distribution function (CDF) of declinations for a given latitude.

    Returns:
        float: Test statistic (A2) for declinations.

    Notes:
        The Anderson-Darling (AD) test is a statistical test used to assess whether a sample of data comes from a specific probability distribution. This function calculates the AD test statistic for the distribution of declinations based on the observed declinations and the CDF of declinations.

        The AD test statistic measures the discrepancy between the observed data and the expected distribution. A larger AD test statistic indicates a greater discrepancy, suggesting that the observed data may not follow the expected distribution.

        It is important to note that this function assumes the input declinations are in degrees and converts them to radians internally for consistency with the CDF function. Additionally, if any declinations are greater than 180 degrees, they are adjusted to the range -180 to 180 degrees before performing the test.
    """    
    
    Ds[Ds>180] -=360
    Ds = np.deg2rad(np.sort(Ds))
    ns = np.size(Ds)
    #S = 0
    #for i in range(1,ns+1):
    #    S += (2*i-1)/ns*(np.log(Dcdf(Ds[i-1]))+np.log(1-Dcdf(Ds[ns-i])))
    
    C = Dcdf(Ds)
    S = np.sum((2*np.arange(1,ns+1)-1)/ns*(np.log(C)+np.log(1-np.flip(C))))    
    
    A2 = -ns-S
    
    return A2

def AD_test(Ds,Is,GGPmodel,lat,degree,plot=False,cite="",saveto=False): #perform the AD test on observed incs and decs
    """
    Perform the Anderson-Darling (AD) test on observed inclinations and declinations.

    Parameters:
        Ds (array-like): Array of observed declinations in degrees.
        Is (array-like): Array of observed inclinations in degrees.
        GGPmodel (dict): GGP model definition.
        lat (float): Assumed latitude of the site.
        degree (int): Maximum degree of the GGP model.
        plot (bool, optional): Whether to plot the empirical cumulative distribution functions (ECDFs) and stereonet. Defaults to False.
        cite (str, optional): Reference or citation information. Defaults to an empty string.
        saveto (bool or str, optional): Whether to save the plot to a file. If True, saves as 'AD_test_plot.png'. If a string is provided, saves with the given filename. Defaults to False.

    Returns:
        tuple: A tuple containing the following elements:
            H (int): 0 or 1 indicating whether the null hypothesis cannot (0) or can (1) be rejected.
            A2I (float): Test statistic (A2) for inclinations.
            A2D (float): Test statistic (A2) for declinations.
            pID (float): Representation of combined p-values (can be used for minimization to optimize latitude).

    Notes:
        The Anderson-Darling (AD) test is a statistical test used to assess whether a sample of data comes from a specific probability distribution. This function performs the AD test on the observed inclinations and declinations based on the provided GGP model, latitude, and maximum degree.

        The function calculates the AD test statistics (A2) for inclinations and declinations using the `AD_inc` and `AD_dec` functions, respectively. It also calculates the combined p-value (pID) based on the A2 values and reference data.

        The null hypothesis is that the observations are drawn from the GGP at the specified latitude. The null hypothesis cannot be rejected if both A2I and A2D are less than 3.07.

        If `plot` is set to True, the function generates a plot showing the empirical cumulative distribution functions (ECDFs) for inclinations and declinations, as well as a stereonet plot with contours of the GGP model's probability density function. The plot can be saved to a file by setting `saveto` to True or providing a filename.
    """
    
    ###INPUTS###
    #Ds = array of observed declinations (degrees)
    #Is = array of observed inclinations (degrees)
    #GGPmodel = GGP model definition
    #lat = assumed latitude of site
    #degree = maximum degree of the GGP model
    
    ###OUTPUTS###
    #H = 0/1 indicates null cannot/can be rejected
    #A2I = test statistic for inclinations
    #A2D = test statistic for declinatons
    #pID = representation of combined p-values (can be used for minimization to optimize latitude)
    
    A2ref = np.array([0.025,0.050,0.075,0.100,0.125,0.150,0.175,0.200,0.225,0.250,0.275, \
                      0.300,0.325,0.350,0.375,0.400,0.425,0.450,0.475,0.500,0.525,0.550, \
                      0.575,0.600,0.625,0.650,0.675,0.700,0.750,0.800,0.850,0.900,0.950, \
                      1.000,1.050,1.100,1.150,1.200,1.250,1.300,1.350,1.400,1.450,1.500, \
                      1.550,1.600,1.650,1.700,1.750,1.800,1.850,1.900,1.950,2.000,2.050, \
                      2.100,2.150,2.200,2.250,2.300,2.350,2.400,2.450,2.500,2.550,2.600, \
                      2.650,2.700,2.750,2.800,2.850,2.900,2.950,3.000,3.050,3.100,3.150, \
                      3.200,3.250,3.300,3.350,3.400,3.450,3.500,3.550,3.600,3.650,3.700, \
                      3.750,3.800,3.850,3.900,3.950,4.000,4.050,4.100,4.150,4.200,4.250, \
                      4.300,4.350,4.400,4.500,4.600,4.700,4.800,4.900,5.000,5.500,6.000, \
                      7.000,8.000])
    
    pref = np.array([1.0000,1.0000,1.0000,1.0000,0.9997,0.9986,0.9958,0.9904,0.9820,0.9704, \
                     0.9557,0.9382,0.9183,0.8964,0.8731,0.8487,0.8236,0.7981,0.7724,0.7468, \
                     0.7214,0.6964,0.6719,0.6480,0.6247,0.6070,0.5801,0.5588,0.5185,0.4810, \
                     0.4463,0.4142,0.3846,0.3573,0.3320,0.3088,0.2873,0.2676,0.2497,0.2323, \
                     0.2167,0.2027,0.1889,0.1765,0.1650,0.1543,0.1444,0.1352,0.1266,0.1186, \
                     0.1112,0.1043,0.0979,0.0918,0.0862,0.0810,0.0761,0.0715,0.0672,0.0632, \
                     0.0595,0.0559,0.0526,0.0496,0.0466,0.0439,0.0414,0.0390,0.0367,0.0346, \
                     0.0326,0.0308,0.0290,0.0274,0.0258,0.0244,0.0230,0.0217,0.0205,0.0193, \
                     0.0182,0.0172,0.0163,0.0154,0.0145,0.0137,0.0130,0.0122,0.0116,0.0109, \
                     0.0103,0.0098,0.0092,0.0087,0.0083,0.0078,0.0078,0.0070,0.0066,0.0062, \
                     0.0059,0.0056,0.0050,0.0045,0.0040,0.0036,0.0032,0.0029,0.0017,0.0010, \
                     0.0003,0.0001])
    
    
    
    
    n = np.size(Is)
    if n<5:
        raise ValueError("Insufficient data, N must be 5 or greater")
    
    Icdf, Dcdf = GGP_cdf(GGPmodel, lat, degree) #find marginal distributions
    
    A2I = AD_inc(Is,Icdf)
    pI = np.interp(A2I,A2ref,pref)
    
    
    A2D = AD_dec(Ds,Dcdf)  
    pD = np.interp(A2D,A2ref,pref)
    
    #null hypothesis that observations are drawn from the GGP at the specified latitude
    #cannot be rejected if both pI and pD are <3.07   LT: This is wrong? 
    #cannot be rejected if both A2I and A2D are <3.07   LT: This is right? 
    
    #pID = -2*np.sum(np.log(pI)+np.log(pD)) #metric for minimization to find latitude if unknown.
    #pID=1-chi2.cdf(pID,df=2) # pIDnew
    pID=min(pI,pD) #pID per Heslop, 8/7/23
    if np.logical_and(A2I<3.07, A2D<3.07):
        H = 0
    else:
        H = 1
    #plot ecdf comparison if desired
    if plot:
        I0 = np.linspace(-90,90,180)
        D0 = np.linspace(-180,180,360)
        
        Iecdf = np.zeros(np.size(I0))
        for i in range(np.size(I0)):
            Iecdf[i] = np.mean(Is<=I0[i])
    
        Decdf = np.zeros(np.size(D0))
        for i in range(np.size(D0)):
            Decdf[i] = np.mean(Ds<=D0[i])
        fig=plt.figure(figsize=(8,4))
        ax1=fig.add_subplot(121)
         
        ax1.plot(D0,Dcdf(np.deg2rad(D0)),'r-',linewidth=2)
        ax1.plot(D0,Decdf,'k',linestyle='dotted')
        #ax1.plot(Ds,np.zeros(np.size(Ds))+0.025,'+k')
        ax1.text(-170,.9,'a)',fontsize=14)
        if A2D<3.07:
            ax1.text(-170,.8,'Decs: Pass',color='red',fontsize=14)
        else:
            ax1.text(-170,.8,'Decs: Fail',color='red',fontsize=14)
        ax1.set_xlim([-180,180])
        ax1.set_ylim([0,1])
        ax1.minorticks_on()
        ax1.set_xticks(np.arange(-180, 180+1, 45.0))
        ax1.set_xlabel('Declination[$^o$]',fontsize=14,color='red')
        ax1.set_ylabel('Cumulative Probability',fontsize=14)
        ax2=ax1.twiny()

        ax2.plot(I0,Icdf(np.deg2rad(I0)),'b-',linewidth=2)
        ax2.plot(I0,Iecdf,'k',linestyle='dotted')
        #ax2.plot(Is,np.ones(np.size(Is))+0.025,'+k')
        ax2.set_xlim([-90,90])
        ax2.set_ylim([0,1])
        ax2.minorticks_on()
        ax2.set_xticks(np.arange(-90, 90+1, 30.0))
        ax2.set_xlabel('Inclination[$^o$]',fontsize=14,color='blue')
        if A2I<3.07:
            ax2.text(-85,.7,'Incs: Pass',color='blue',fontsize=14)
        else:
            ax2.text(-85,.7,'Incs: Fail',color='blue',fontsize=14)
        #plt.tight_layout()
        #plt.show()
        
    #plot stereonet with contours if desired
        sp,sn, XX, YY = prediction_map_GGP_su(lat,GGPmodel,degree=degree,dx=0.01,dy=0.01) #map out pdf
        ax3=fig.add_subplot(122)
        ax3.text(-1,.9,'b)',fontsize=14)
        ipmag.plot_net() #create net
        
        levels = np.linspace(np.min(sp),np.max(sp),24)[1::4] #produce contour levels
        ipmag.plot_di(dec=Ds,inc=Is,color='green') #plot data
        plt.contour(XX,YY,sp,levels=levels,colors='grey',linestyle='dotted',linewidth=.1) #plot contours
        #if H:
        #    plt.title(cite+': '+GGPmodel['name']+' : rejected')
        #else:
        #    plt.title(cite+': '+GGPmodel['name']+' : not rejected')
        #plt.tight_layout()
        if saveto:
            plt.savefig(saveto)
        plt.show()
    
    return H,A2I,A2D,pID

def AD_test_w_kappa(Ds,Is,GGPmodel,degree=8,lat=False,kappa=-1,plot=False,cite="",saveto=False): #perform the AD test on observed incs and decs
    """
    Perform the Anderson-Darling (AD) test on observed inclinations and declinations.

    Parameters:
        Ds (array): Array of observed declinations (degrees).
        Is (array): Array of observed inclinations (degrees).
        GGPmodel: GGP model definition.
        degree (int): Maximum degree of the GGP model. Default is 8.
        lat (float): Assumed latitude of the site. If False, use inclinations to calculate the latitude. Default is False.
        kappa (float): The kappa value for Fisher-distributed uncertainties in directions. Default is -1 (infinity)
        plot (bool): Whether to plot the ECDF comparison and stereonet. Default is False.
        cite (str): Citation information for the GGP model. Default is an empty string.
        saveto (bool or str): If provided, save the plot to the specified file path. Default is False.

    Returns:
        H (int): 0 if the null hypothesis cannot be rejected, 1 otherwise.
        A2I (float): Test statistic for inclinations.
        A2D (float): Test statistic for declinations.
        pID (float): Representation of combined p-values (can be used for minimization to optimize latitude).
        lat (float): Latitude of the site.
    """    
    ###INPUTS###
    #Ds = array of observed declinations (degrees)
    #Is = array of observed inclinations (degrees)
    #GGPmodel = GGP model definition
    #lat = assumed latitude of site, if False, use inclinations to get lat
    #degree = maximum degree of the GGP model
    # kappa = the kappa for Fisher distributed uncertainties in directions
    ###OUTPUTS###
    #H = 0/1 indicates null cannot/can be rejected
    #A2I = test statistic for inclinations
    #A2D = test statistic for declinatons
    #pID = representation of ocmbined p-values (can be used for minimization to optimize latitude)
    
    A2ref = np.array([0.025,0.050,0.075,0.100,0.125,0.150,0.175,0.200,0.225,0.250,0.275, \
                      0.300,0.325,0.350,0.375,0.400,0.425,0.450,0.475,0.500,0.525,0.550, \
                      0.575,0.600,0.625,0.650,0.675,0.700,0.750,0.800,0.850,0.900,0.950, \
                      1.000,1.050,1.100,1.150,1.200,1.250,1.300,1.350,1.400,1.450,1.500, \
                      1.550,1.600,1.650,1.700,1.750,1.800,1.850,1.900,1.950,2.000,2.050, \
                      2.100,2.150,2.200,2.250,2.300,2.350,2.400,2.450,2.500,2.550,2.600, \
                      2.650,2.700,2.750,2.800,2.850,2.900,2.950,3.000,3.050,3.100,3.150, \
                      3.200,3.250,3.300,3.350,3.400,3.450,3.500,3.550,3.600,3.650,3.700, \
                      3.750,3.800,3.850,3.900,3.950,4.000,4.050,4.100,4.150,4.200,4.250, \
                      4.300,4.350,4.400,4.500,4.600,4.700,4.800,4.900,5.000,5.500,6.000, \
                      7.000,8.000])
    
    pref = np.array([1.0000,1.0000,1.0000,1.0000,0.9997,0.9986,0.9958,0.9904,0.9820,0.9704, \
                     0.9557,0.9382,0.9183,0.8964,0.8731,0.8487,0.8236,0.7981,0.7724,0.7468, \
                     0.7214,0.6964,0.6719,0.6480,0.6247,0.6070,0.5801,0.5588,0.5185,0.4810, \
                     0.4463,0.4142,0.3846,0.3573,0.3320,0.3088,0.2873,0.2676,0.2497,0.2323, \
                     0.2167,0.2027,0.1889,0.1765,0.1650,0.1543,0.1444,0.1352,0.1266,0.1186, \
                     0.1112,0.1043,0.0979,0.0918,0.0862,0.0810,0.0761,0.0715,0.0672,0.0632, \
                     0.0595,0.0559,0.0526,0.0496,0.0466,0.0439,0.0414,0.0390,0.0367,0.0346, \
                     0.0326,0.0308,0.0290,0.0274,0.0258,0.0244,0.0230,0.0217,0.0205,0.0193, \
                     0.0182,0.0172,0.0163,0.0154,0.0145,0.0137,0.0130,0.0122,0.0116,0.0109, \
                     0.0103,0.0098,0.0092,0.0087,0.0083,0.0078,0.0078,0.0070,0.0066,0.0062, \
                     0.0059,0.0056,0.0050,0.0045,0.0040,0.0036,0.0032,0.0029,0.0017,0.0010, \
                     0.0003,0.0001])
    
    
    di_block=np.column_stack((Ds,Is))
    if not lat: #use incs from data set to determine (paleo)lat
        #Is_f=pmag.unsquish(Is,flat)
        #di_block=np.column_stack((Ds,Is_f))
        pars=pmag.doprinc(di_block) # calculate principal component parameters
        lat=np.absolute(pmag.plat(pars['inc']))
        print ('lat from inc: ',lat)#DEBUG

    n = np.size(Is)
    if n<5:
        raise ValueError("Insufficient data, N must be 5 or greater")
    
    Icdf, Dcdf = GGP_vMF_cdfs(GGPmodel, lat, degree,kappa=kappa) #find marginal distributions
    
    A2I = AD_inc(Is,Icdf)
    pI = np.interp(A2I,A2ref,pref)
    
    
    A2D = AD_dec(Ds,Dcdf)  
    pD = np.interp(A2D,A2ref,pref)
    
    #null hypothesis that observations are drawn from the GGP at the specified latitude
    #cannot be rejected if both pI and pD are <3.07    
    
    #pID = -2*np.sum(np.log(pI)+np.log(pD)) #metric for minimization to find latitude if unknown.
    #pID = 1-chi2.cdf(pID, df=2) #pIDnew
    pID=min(pI,pD) #pID per Heslop, 8/7/23
    
    if np.logical_and(A2I<3.07, A2D<3.07):
        H = 0
    else:
        H = 1
        
    #plot ecdf comparison if desired
    if plot:
    #plot stereonet with contours if desired
        print ('lat: ',lat)#DEBUG
        fig=plt.figure(figsize=(8,4))
        ax1=fig.add_subplot(121)
        sp,sn, XX, YY = prediction_map_GGP_su(lat,GGPmodel,degree=degree,dx=0.01,dy=0.01) #map out pdf
        ax1.text(-1,.9,'a)',fontsize=14)
        ipmag.plot_net() #create net
        
        levels = np.linspace(np.min(sp),np.max(sp),24)[1::4] #produce contour levels
        ipmag.plot_di(dec=Ds,inc=Is,color='green') #plot data
        plt.contour(XX,YY,sp,levels=levels,colors='grey',linestyle='dotted',linewidth=.1) #plot contours
        plt.title('lat='+str(np.round(lat,1))+'; $\kappa$: '+str(kappa))
        I0 = np.linspace(-90,90,180)
        D0 = np.linspace(-180,180,360)
        
        Iecdf = np.zeros(np.size(I0))
        for i in range(np.size(I0)):
            Iecdf[i] = np.mean(Is<=I0[i])
    
        Decdf = np.zeros(np.size(D0))
        for i in range(np.size(D0)):
            Decdf[i] = np.mean(Ds<=D0[i])
        ax2=fig.add_subplot(122)
         
        ax2.plot(D0,Dcdf(np.deg2rad(D0)),'r-',linewidth=2)
        ax2.plot(D0,Decdf,'k',linestyle='dotted')
        #ax1.plot(Ds,np.zeros(np.size(Ds))+0.025,'+k')
        ax2.text(-170,.9,'b)',fontsize=14)
        if A2D<3.07:
            ax2.text(-170,.8,'Decs: Pass',color='red',fontsize=14)
        else:
            ax2.text(-170,.8,'Decs: Fail',color='red',fontsize=14)
        ax2.set_xlim([-180,180])
        ax2.set_ylim([0,1])
        ax2.minorticks_on()
        ax2.set_xticks(np.arange(-180, 180+1, 45.0))
        ax2.set_xlabel('Declination[$^o$]',fontsize=14,color='red')
        ax2.set_ylabel('Cumulative Probability',fontsize=14)
        ax3=ax2.twiny()

        ax3.plot(I0,Icdf(np.deg2rad(I0)),'b-',linewidth=2)
        ax3.plot(I0,Iecdf,'k',linestyle='dotted')
        #ax2.plot(Is,np.ones(np.size(Is))+0.025,'+k')
        ax3.set_xlim([-90,90])
        ax3.set_ylim([0,1])
        ax3.minorticks_on()
        ax3.set_xticks(np.arange(-90, 90+1, 30.0))
        ax3.set_xlabel('Inclination[$^o$]',fontsize=14,color='blue')
        if A2I<3.07:
            ax3.text(-85,.7,'Incs: Pass',color='blue',fontsize=14)
        else:
            ax3.text(-85,.7,'Incs: Fail',color='blue',fontsize=14)
        plt.tight_layout()
        if saveto:
            plt.savefig(saveto)
        plt.show()
        #plt.show()
        
    
    return H,A2I,A2D,pID,lat

def GGPmodels(model='TK03_GAD'):
    """
    Returns dictionary of specified Giant Gaussian Model

    Parameters:
        model (string): name of desired model
        one of the following GGP models
            CP88: from Constable and Parker, 1988
            QC96: Quidelleur and Courtillot
            CJ98: Constable and Johnson
            TK03_GAD:  Tauxe and Kent, 2004
            BCE19_GAD: Brandt et al., 2019 
    Returns:
       dictionary of requested model
    """
    
    CP88 = {"g10" : -30, "g20" : -1.8, "g30" : 0.0, "sig10" : 3.0, "sig11": 3.0,
            "sig20" : 0.0 , "sig21" : 0.0, "sig22" : 0.0, "alpha": 27.7, "beta": 1.0, "name":'CP88'}
    QC96 = {"g10" : -30, "g20" : -1.2, "g30" : 0.0, "sig10" : 3.0, "sig11": 3.0,
            "sig20" : 1.3 , "sig21" : 4.3, "sig22" : 1.3, "alpha": 27.7, "beta": 1.0, "name":'QC96'}
    CJ98 = {"g10" : -30, "g20" : -1.5, "g30" : 0.0, "sig10" : 11.72, "sig11": 1.67,
            "sig20" : 1.16 , "sig21" : 4.06, "sig22" : 1.16, "alpha": 15.0, "beta": 1.0, "name":'CJ98'}
    TK03 =  {"g10" : -18, "g20" : 0.0, "g30" : 0.0, "sig10" : 0.0, "sig11": 0.0,
            "sig20" : 0.0, "sig21" : 0.0, "sig22" : 0.0, "alpha": 7.5, "beta": 3.8, "name":'TK03_GAD'}
    BCE19 = {"g10" : -18, "g20" : 0.0, "g30" : 0.0, "sig10" : 0.0, "sig11": 0.0,
            "sig20" : 0.0, "sig21" : 0.0, "sig22" : 0.0, "alpha": 6.7, "beta": 4.2, "name":'BCE19_GAD'}
    THG24 = {"g10" : -18, "g20" : -.1, "g30" : 0.4, "sig10" : 0.0, "sig11": 0.0,
            "sig20" : 0.0, "sig21" : 0.0, "sig22" : 0.0, "alpha": 7.25, "beta": 3.75, "name":'THG24'}
    models=[BCE19,TK03,QC96,CJ98,CP88,THG24]
    for m in models:
        if m['name']==model:
            return m
    print ('no such model name')
    return False 

def svei_di(di_block,model='TK03_GAD',kappa=-1,lat=False, polarity=False,plot=True,save=False,saveto=""): # tests di_block against model 
        """
    Makes plots from a di_block and performs an AD, E and V2 tests with a specified GGP model.

    Parameters:
        di_block (numpy.ndarray): An array of directional data represented as (declination, inclination) pairs.
        model (str, optional): The name of the GGP model to use. Default is 'TK03_GAD'. 
            options are: 
                CP88: from Constable and Parker, 1988
                QC96: Quidelleur and Courtillot
                CJ98: Constable and Johnson
                TK03_GAD:  Tauxe and Kent, 2004
                BCE19_GAD: Brandt et al., 2019 

        kappa (float, optional): The kappa value for Fisher distribution of directions. Default is -1 (infinity)
        lat (float, optional): The latitude for paleolatitude correction. Default is False., When False, uses the latitude estimated from the dataset inclination
        polarity (bool or str, optional): Determines the polarity of the directional data. Default is False (use all directions).
                                          - False: Combine normal and reverse directions (non-polarized).
                                          - 'N': Use normal directions only.
                                          - 'R': Use reverse directions only.
        plot (bool, optional): Whether to plot the data. Default is True.
        save (bool, optional): Whether to save the plots. Default is False.
        saveto (str, optional): The path to save the plots (if save is True). Default is an empty string.

    Returns:
        tuple: A tuple containing the following elements:
            - H (float): The result of the AD test statistic.
            - A2I (float): The result of the inclination-only AD test statistic.
            - A2D (float): The result of the declination-only AD test statistic.
            - pID (float): The p-value for the inclination and declination AD tests.
            - lat (float): The corrected paleolatitude.
            - di_block (numpy.ndarray): The modified di_block array after transformations.
        """
        GGPmodel=GGPmodels(model=model) # get model dictionary
        
        pars=pmag.doprinc(di_block) # calculate principal component parameters
        # rotate Ds
        if (pars['dec']>90) & (pars['dec']<270):pars['dec']=(pars['dec']-180)%360
        decs,incs=(di_block.transpose()[0]-pars['dec'])%360,di_block.transpose()[1]
        #incs=pmag.unsquish(incs,flat)# do the unflattening requested
        rot_block=np.array((decs,incs)).transpose()
        if not polarity: # combine NR
            flipped=pmag.flip(rot_block,combine=True)
            ppars=pmag.fisher_mean(flipped)
            flipped=np.array(flipped).transpose()
            if (ppars['dec']>90) & (ppars['dec']<270):
                Ds=(flipped[0]-180)%360
            else:
                Ds=(flipped[0])
    #        Ds=flipped[0]-180
            Is=flipped[1]
        else:
            N,R =pmag.flip(rot_block,combine=False)
            if polarity == 'N':     
                ppars=pmag.fisher_mean(N)
                flipped=np.array(N).transpose()
                Ds=(flipped[0])
            else:
                flipped=np.array(R).transpose()
                ppars=pmag.fisher_mean(R)
                if (ppars['dec']>90) & (ppars['dec']<270):
                    Ds=(flipped[0]-180)%360
                else:
                    Ds=(flipped[0])
    #        Ds=flipped[0]-180
            Is=flipped[1]
        di_block=np.column_stack((Ds,Is))
        if save:
            H,A2I,A2D,pID,lat = svei_test(Ds,Is,GGPmodel,lat=lat,kappa=kappa,plot=plot,saveto=saveto)
        else:
            H,A2I,A2D,pID,lat = svei_test(Ds,Is,GGPmodel,lat=lat,kappa=kappa,plot=plot)
        return H,A2I,A2D,pID,lat,di_block

def find_flat(di_block,save=False,polarity=False,plot=False,study=False,kappa=50,saveto='',model_name='THG24',
                   quick=False,verbose=False,num_sims=1000):
    """
    Finds the best unflattening factor for a given di_block and performs analysis.

    Parameters:
        di_block (numpy.ndarray): An array of directional data represented as (declination, inclination) pairs.
        save (bool, optional): Whether to save the plots. Default is False.
        polarity (bool, optional): Determines the polarity of the directional data. Default is False. 
            if polarity =='N', use only normal data
            if polarity =='R', use only reverse data
            if polarity ==False, use all data, flipping reverse to antipode
            
        plot (bool, optional): Whether to plot the data. Default is False.
        study (bool, optional): Whether the analysis is part of a study. Default is False.
        saveto (str, optional): The path to save the plots (if save is True). Default is 'find_flat.pdf'.
        quick (bool, optional): Whether to perform a quick analysis with a larger step size. Default is False as this is just for 
                                 a quick look and does not provide a statistically robust answer.
        num_sims (int, optional): Number of simulations to run (higher number gives more reproducible results). Default is 1000

    Returns:
        pandas.DataFrame: A DataFrame containing the following columns:
            - flat: Unflattening factor values.
            - study: Whether the analysis is part of a study.
            - kappa: The kappa value used.
            - A2D: A2D values.
            - A2I: A2I values.
            - H: AD test statistics.
            - lat: Corrected paleolatitudes.
            - inc: Inclinations.
            - pID: pIDmin values for the inclination and declination AD tests.
            - V2dec (float): Declination of minor principle component of data set. 
            - V2sim_min, V2sim_max (floats): Bounds on V2dec from Monte Carlo simulation
            - V2_result (integer): 0 if V2dec not in bounds, 1 if in bounds (consistent)
            - E (float): Elongation (tau2/tau3) of data set 
            - Esim_min, Esim_max (floats): Bounds on elongation from Monte Carlo simulation
            - E_result (integer): 0 if V2dec not in bounds, 1 if in bounds (consistent)
    """
    model=GGPmodels(model=model_name) # set model to the 'best' one
    print ('using model: ',model_name)
    degree=8 # 
    N=len(di_block)
    As_df=pd.DataFrame(columns=['flat'])
    flat_min=.3
    flat_incr=.01
    flats=np.arange(1,flat_min,-flat_incr)
    if quick:
        flats=np.arange(1,flat_min,-.05)
        #flats=np.arange(1,flat_min,-.2) # for really quick
        #num_sims=10 # this is just for debugging
    A2Is,A2Ds,Hs,lats,incs,pIDs=[],[],[],[],[],[]
    V2s,Es=[],[]
    V2mins,V2maxs,Emins,Emaxs=[],[],[],[]
    V2_results,E_results,kappas=[],[],[]
    # rotate Ds
    pars=pmag.doprinc(di_block) # calculate principal component parameters
    # rotate Ds
    if (pars['dec']>90) & (pars['dec']<270):pars['dec']=(pars['dec']-180)%360
    Ds,Is=(di_block.transpose()[0]-pars['dec'])%360,di_block.transpose()[1]
    #incs=pmag.unsquish(incs,flat)# do the unflattening requested
    rot_block=np.array((Ds,Is)).transpose()
    flipped=pmag.flip(rot_block,combine=True)
    ppars=pmag.fisher_mean(flipped)
    flipped=np.array(flipped).transpose()
    if (ppars['dec']>90) & (ppars['dec']<270):
        Ds=(flipped[0]-180)%360
    else:
        Ds=(flipped[0])
    Is=flipped[1]
    rot_block=np.column_stack((Ds,Is))
    if verbose: print ('Testing distribution against model ',model_name)
    if saveto:
       save_svei=saveto.rstrip('.pdf')+'_svei_test.pdf'
    else:
       save_svei=False
    res_dict=svei_test(rot_block,kappa=kappa,num_sims=num_sims,plot=plot,model_name=model_name,saveto=save_svei)
    if (res_dict['H']==0)&(res_dict['V2_result']==1)&(res_dict['E_result']==1):
        res_dict['flat']=1
        res_dict['study']=study
        res_dict['kappa']=kappa
        if verbose: 
            print ('distribution is consistent with field model ',model_name)
            print ('You are done now')
        return [res_dict] # don't do find_flat if none necessary  
    else:
        if verbose: 
            print ('distribution is not consistent with field model ',model_name)
            print ('proceeding with find_flat routine, be patient')
        for flat in flats:
            if verbose: print ('flat: ',np.round(flat,2))
            Is=rot_block.transpose()[1]
            incs_f=pmag.unsquish(Is,flat)
            unflat_block=np.column_stack((Ds,incs_f))
            res_dict=svei_test(unflat_block,kappa=kappa,num_sims=num_sims,plot=False,model_name=model_name,saveto=False)
            if verbose: print (res_dict)
            lat=res_dict['lat']
            V2mins.append(res_dict['V2sim_min'])
            V2maxs.append(res_dict['V2sim_max'])
            Emins.append(res_dict['Esim_min'])
            Emaxs.append(res_dict['Esim_max'])
            kappas.append(res_dict['kappa']) 
            A2Is.append(res_dict['A2I'])
            A2Ds.append(res_dict['A2D'])
            Hs.append(res_dict['H'])
            lats.append(res_dict['lat'])
            inc=pmag.pinc(lat)
            incs.append(inc)
            pIDs.append(res_dict['pID'])
            V2_results.append(res_dict['V2_result'])
            E_results.append(res_dict['E_result'])
            V2s.append(res_dict['V2dec'])
            Es.append(res_dict['E'])
 
    As_df['flat']=flats
    As_df['study']=study
    As_df['kappa']=kappas
    As_df['A2D']=A2Ds
    As_df['A2I']=A2Is
    As_df['H']=Hs
    As_df['lat']=lats
    As_df['inc']=incs
    As_df['pID']=pIDs
    As_df['V2']=V2s
    As_df['V2min']=V2mins
    As_df['V2max']=V2mins
    As_df['E']=Es
    As_df['Emin']=Emins
    As_df['Emax']=Emaxs

    As_df['V2_results']=V2_results
    As_df['E_results']=E_results
    goodflats=As_df[(As_df['H']==0)&(As_df['V2_results']==1)&(As_df['E_results']==1)]['flat'].values
    goodlats=As_df[(As_df['H']==0)&(As_df['V2_results']==1)&(As_df['E_results']==1)]['lat'].values
    goodincs=As_df[(As_df['H']==0)&(As_df['V2_results']==1)&(As_df['E_results']==1)]['inc'].values
    if len(goodincs)>0:
        pIDmax=np.array(pIDs).max()
        #best=As_df[As_df['pID']==pIDmax]
        #best_flat=np.round(best['flat'].values[0],2)
        #best_inc=np.round(best['inc'].values[0],1)
        best_inc=goodincs.min()+(goodincs.max()-goodincs.min())/2
        best_inc=np.round(best_inc,1)
        best_flat=goodflats.min()+(goodflats.max()-goodflats.min())/2
        best_flat=np.round(best_flat,2)
    if plot:
        fig=plt.figure(figsize=(8,10))
        if kappa ==-1:
            kap='Inf'
        else:
            kap=str(kappa)

        #plt.title('$\kappa$ = '+kap)

        ax1=fig.add_subplot(321) #V2dec  versus flat
        ax2=fig.add_subplot(322) # E versus flat
        ax3=fig.add_subplot(323)# A2I,A2D versus flat
        ax4=fig.add_subplot(324)# pID  versus flat
        ax1.plot(flats,V2s,'r-',label='V2dec')
        ax1.plot(flats,V2mins,'r--',label='bounds')
        ax1.plot(flats,V2maxs,'r--')
        ax1.set_xlim(1,flat_min)
        ax1.set_ylabel('V2dec')
        #ax1.legend(loc='upper right')
        ax2.plot(flats,Es,'b-',label='Es')
        ax2.plot(flats,Emins,'b--',label='bounds')
        ax2.plot(flats,Emaxs,'b--')
        ax2.set_xlim(1,flat_min)
        #ax2.legend(loc='upper right')
        ax2.set_ylabel('E')
    
        ax3.plot(flats,A2Is,'b-',label='A2I')
        ax3.plot(flats,A2Ds,'r-',label='A2D')
        ax3.axhline(3.07,color='black',linestyle='dotted',label='threshold')
        ax3.set_xlim(1,flat_min)
        #ax3.legend(loc='upper center')
        ax3.set_xlabel('Unflattening factor')
        ax3.set_ylabel('A2I, A2D')
        lns1=ax4.plot(flats,pIDs,'g',label='pID_min')  
        #ax4.plot([best_flat],[pIDmax],'b*')  
        #ax4.plot([best_flat],[np.array(pIDs).max()],'g*')
        ax4.axhline(.025,color='blue',linestyle='dotted')
        ax4.set_xlim(1,flat_min)
        ax4.set_ylim(0,np.array(pIDs).max()+.1)
        if np.array(pIDs).max()<.1:
            ax4.set_ylim(0,.1)
        ax4.set_ylabel('pID_min',color='green')
        ax4.set_xlabel('Unflattening factor')
        ax4a=ax4.twinx()

        lns2=ax4a.plot(flats,incs,color='black',linestyle='dashed',label='Inclination')
        ax4a.set_ylabel('Inclination',rotation=270,labelpad=10)
        lns = lns1+lns2
        labs = [l.get_label() for l in lns]
        #ax4.legend(lns,labs,loc='upper center')

        if len(goodflats):
            if verbose:print ('corrected inc: ',best_inc)
            #ax4a.plot([goodflats[0],goodflats[0]],[0,goodincs[0]],linestyle='dashed',color='black')
            #ax4a.plot([goodflats[-1],goodflats[-1]],[0,goodincs[-1]],linestyle='dashed',color='black')
            #ax4.set_title('Unflattening factor: '+str(best_flat)+'; Inc: '+str(best_inc))
    
        ax5=fig.add_subplot(325) # eqarea of original

        ipmag.plot_net(tick_spacing=30)#modified per Enkin request
        ipmag.plot_di(di_block=di_block,color='k')
        ipmag.plot_di(di_block=rot_block,color='b')
        ax5.set_title('Original/Rotated')
        ax6=fig.add_subplot(326)
        if len(goodflats):

            decs=rot_block.transpose()[0]
            incs=rot_block.transpose()[1]
            incs_unflat=pmag.unsquish(incs,best_flat)
            ipmag.plot_net(tick_spacing=30)

            ipmag.plot_di(dec=decs,inc=incs_unflat,color='b')  #modified per Enkin request
            #ax6.set_title('fs= '+str(np.round(goodflats[0],2))+'-'+str(np.round(goodflats[-1],2))+
            #      '; incs= '+str(np.round(goodincs[0],1))+'-'+str(np.round(goodincs[-1],1)),fontsize=14)
            ax6.set_title('fs= '+str(best_flat)+'$_{'+str(np.round(goodflats[0],2))+'}^{'+str(np.round(goodflats[-1],2))+'}$;'
                    +' incs = '+str(best_inc)+'$_{'+str(np.round(goodincs[0],1))+'}^{'+str(np.round(goodincs[-1],1))+'}$')
            ax1.axvline(goodflats[0],color='black',linestyle='dotted')
            ax1.axvline(goodflats[-1],color='black',linestyle='dotted')
            ax2.axvline(goodflats[0],color='black',linestyle='dotted')
            ax2.axvline(goodflats[-1],color='black',linestyle='dotted')
            ax3.axvline(goodflats[0],color='black',linestyle='dotted')
            ax3.axvline(goodflats[-1],color='black',linestyle='dotted')
            ax4.axvline(goodflats[0],color='black',linestyle='dotted')
            ax4.axvline(goodflats[-1],color='black',linestyle='dotted')
        else:
            ax5.set_title('Original - no passing f')
        txtstring='$\kappa$: '+kap+'; model:'+model_name
        ax1.set_title(txtstring)
        ax1.text(.05, .92,'a)',transform=ax1.transAxes)
        ax2.text(.05,.92,'b)',transform=ax2.transAxes)
        ax3.text(.05,.92,'c)',transform=ax3.transAxes)
        ax4.text(.05,.92,'d)',transform=ax4.transAxes)
        ax5.text(.25,.92,'e)',transform=ax5.transAxes)
        ax6.text(.25,.92,'f)',transform=ax6.transAxes)

        plt.tight_layout()
        if save:
            plt.savefig(saveto)
    return(As_df) 

def svei_test(di_block,model_name='TK03_GAD',degree=8,lat=False,kappa=-1,plot=False,cite="",saveto=False,
                      num_sims=1000,verbose=False): #perform the AD test on observed incs and decs
    """
    Perform the Anderson-Darling (AD) test on observed inclinations and declinations and Monte Carlo
       simulation to estimate 95% confidence bounds on V2dec and E

    Parameters:
        di_block=Array of declinations,inclinations (degrees)
        model_name: GGP model name.
        degree (int): Maximum degree of the GGP model. Default is 8.
        lat (float): Assumed latitude of the site. If False, use inclinations to calculate the latitude. Default is False.
        kappa (float): The kappa value for Fisher-distributed uncertainties in directions. Default is -1 (infinity)
        plot (bool): Whether to plot the ECDF comparison, stereonet and CDFs for V2dec and E. Default is False.
        cite (str): Citation information for the GGP model. Default is an empty string.
        saveto (bool or str): If provided, save the plot to the specified file path. Default is False.
        num_sims (int): number of Monte Carlo simulations for V2dec, E bounds calculation
        verbose (bool): if True, print commentary

    Returns:
        res_dict (dict): Dictionary with the following parameters:
            kappa (float): kappa used in simulations
            H (int): 0 if the null hypothesis cannot be rejected, 1 otherwise.
            A2I (float): Test statistic for inclinations.
            A2D (float): Test statistic for declinations.
            pID (float): Representation of combined p-values (can be used for minimization to optimize latitude).
            lat (float): Latitude of the site.
            V2dec (float): Declination of minor principle component of data set. 
            V2sim_min, V2sim_max (floats): Bounds on V2dec from Monte Carlo simulation
            V2_result (integer): 0 if V2dec not in bounds, 1 if in bounds (consistent)
            E (float): Elongation (tau2/tau3) of data set 
            Esim_min, Esim_max (floats): Bounds on elongation from Monte Carlo simulation
            E_result (integer): 0 if V2dec not in bounds, 1 if in bounds (consistent)
    """    
    ###INPUTS###
    #Ds = array of observed declinations (degrees)
    #Is = array of observed inclinations (degrees)
    #model_name = GGP model name
    #lat = assumed latitude of site, if False, use inclinations to get lat
    #degree = maximum degree of the GGP model
    # kappa = the kappa for Fisher distributed uncertainties in directions
    ###OUTPUTS###
    #H = 0/1 indicates null cannot/can be rejected
    #A2I = test statistic for inclinations
    #A2D = test statistic for declinatons
    #pID = representation of ocmbined p-values (can be used for minimization to optimize latitude)
    
    A2ref = np.array([0.025,0.050,0.075,0.100,0.125,0.150,0.175,0.200,0.225,0.250,0.275, \
                      0.300,0.325,0.350,0.375,0.400,0.425,0.450,0.475,0.500,0.525,0.550, \
                      0.575,0.600,0.625,0.650,0.675,0.700,0.750,0.800,0.850,0.900,0.950, \
                      1.000,1.050,1.100,1.150,1.200,1.250,1.300,1.350,1.400,1.450,1.500, \
                      1.550,1.600,1.650,1.700,1.750,1.800,1.850,1.900,1.950,2.000,2.050, \
                      2.100,2.150,2.200,2.250,2.300,2.350,2.400,2.450,2.500,2.550,2.600, \
                      2.650,2.700,2.750,2.800,2.850,2.900,2.950,3.000,3.050,3.100,3.150, \
                      3.200,3.250,3.300,3.350,3.400,3.450,3.500,3.550,3.600,3.650,3.700, \
                      3.750,3.800,3.850,3.900,3.950,4.000,4.050,4.100,4.150,4.200,4.250, \
                      4.300,4.350,4.400,4.500,4.600,4.700,4.800,4.900,5.000,5.500,6.000, \
                      7.000,8.000])
    
    pref = np.array([1.0000,1.0000,1.0000,1.0000,0.9997,0.9986,0.9958,0.9904,0.9820,0.9704, \
                     0.9557,0.9382,0.9183,0.8964,0.8731,0.8487,0.8236,0.7981,0.7724,0.7468, \
                     0.7214,0.6964,0.6719,0.6480,0.6247,0.6070,0.5801,0.5588,0.5185,0.4810, \
                     0.4463,0.4142,0.3846,0.3573,0.3320,0.3088,0.2873,0.2676,0.2497,0.2323, \
                     0.2167,0.2027,0.1889,0.1765,0.1650,0.1543,0.1444,0.1352,0.1266,0.1186, \
                     0.1112,0.1043,0.0979,0.0918,0.0862,0.0810,0.0761,0.0715,0.0672,0.0632, \
                     0.0595,0.0559,0.0526,0.0496,0.0466,0.0439,0.0414,0.0390,0.0367,0.0346, \
                     0.0326,0.0308,0.0290,0.0274,0.0258,0.0244,0.0230,0.0217,0.0205,0.0193, \
                     0.0182,0.0172,0.0163,0.0154,0.0145,0.0137,0.0130,0.0122,0.0116,0.0109, \
                     0.0103,0.0098,0.0092,0.0087,0.0083,0.0078,0.0078,0.0070,0.0066,0.0062, \
                     0.0059,0.0056,0.0050,0.0045,0.0040,0.0036,0.0032,0.0029,0.0017,0.0010, \
                     0.0003,0.0001])
    GGPmodel=GGPmodels(model=model_name)
    Ds=di_block.T[0] 
    Is=di_block.T[1] 
    pars=pmag.doprinc(di_block) # calculate principal component parameters
    if not lat: lat=np.absolute(pmag.plat(pars['inc']))
    if (pars['dec']>90) & (pars['dec']<270):pars['dec']=(pars['dec']-180)%360
    Ds=(Ds-pars['dec'])%360
    rot_block=np.array((Ds,Is)).transpose()
    flipped=pmag.flip(rot_block,combine=True)
    ppars=pmag.fisher_mean(flipped)
    flipped=np.array(flipped).transpose()
    if (ppars['dec']>90) & (ppars['dec']<270):
                Ds=(flipped[0]-180)%360
    else:
                Ds=(flipped[0])
    Is=flipped[1]
    di_block=np.column_stack((Ds,Is))

    n = np.size(Is)
    if n<5:
        raise ValueError("Insufficient data, N must be 5 or greater")
    
    Icdf, Dcdf = GGP_vMF_cdfs(GGPmodel, lat, degree,kappa=kappa) #find marginal distributions
    
    A2I = AD_inc(Is,Icdf)
    pI = np.interp(A2I,A2ref,pref)
    
    
    A2D = AD_dec(Ds,Dcdf)  
    pD = np.interp(A2D,A2ref,pref)
    
    #null hypothesis that observations are drawn from the GGP at the specified latitude
    #cannot be rejected if both pI and pD are <3.07    
    
    #pID = -2*np.sum(np.log(pI)+np.log(pD)) #metric for minimization to find latitude if unknown.
    #pID = 1-chi2.cdf(pID, df=2) #pIDnew
    pID=min(pI,pD) #pID per Heslop, 8/7/23
    
    if np.logical_and(A2I<3.07, A2D<3.07):
        H = 0
    else:
        H = 1
        
    #plot ecdf comparison if desired

    V2dec,E=pars['V2dec'],pars['tau2']/pars['tau3']
    if (V2dec<90) or (V2dec>270):V2dec=(V2dec-180)%360 #flip to south
    N=pars['N']
    if verbose:
        print ('V2dec: ',V2dec)
        print ('E: ',E)
        print ('n, lat: ',N,lat)
        print ('getting Monte Carlo simulations from model....   be patient')

    V2decs,Es=[],[]

    # get model simulations, given lat,n
    for sim in range(num_sims):
        DI=GGPrand(GGPmodel,lat,N,degree)
        if kappa>0:
            fish_DI,decs,incs=[],DI.T[0],DI.T[1]
            for k in range(N):
               di_block=ipmag.fishrot(k=kappa,n=4,dec=decs[k],inc=incs[k],di_block=True)
               pars=pmag.fisher_mean(di_block) 
               #print (decs[k],incs[k],pars['dec'],pars['inc'],kappa)#DEBUG
               fish_DI.append([pars['dec'],pars['inc']])
            DI=fish_DI
            #print (pars) #DEBUG
        mcpars=pmag.doprinc(DI)
        V2dec_sim,E_sim=mcpars['V2dec'],mcpars['tau2']/mcpars['tau3']
        if (V2dec_sim<90) or (V2dec_sim>270):V2dec_sim=(V2dec_sim-180)%360 #flip to south
        V2decs.append(V2dec_sim)
        Es.append(E_sim)
    Es=np.sort(np.array(Es))
    V2decs=np.sort(np.array(V2decs))
    Esim_min=Es[int(num_sims*.025)]
    Esim_max=Es[int(num_sims*.975)]
    V2sim_min=V2decs[int(num_sims*.025)]
    V2sim_max=V2decs[int(num_sims*.975)]
    if verbose:
        print ('A2D, A2I: ',A2D,A2I)
        if A2D<=3.07 and A2I<=3.07:
            print ('Null hyp that directions are consistent with model cannot be rejected')
        else:
            print ('Null hyp that directions are consistent with model can be rejected')
    if (V2dec>=V2sim_min) and (V2dec<=V2sim_max): 

        V2_result=1
        if verbose:
            print ('Null hyp that V2dec is consistent cannot be rejected (95% confidence)')
            print ('V2dec,min,max: ',V2dec,V2sim_min,V2sim_max)
    else:
        V2_result=0
        if verbose:
            print ('Null hyp that V2dec is consistent can be rejected (95% confidence)')
            print ('V2dec,min,max: ',V2dec,V2sim_min,V2sim_max)
    if (E>=Esim_min) and (E<=Esim_max): 
        
            E_result=1
            if verbose:
                print ('Null hyp that E is consistent cannot be rejected (95% confidence)')
                print ('E,min,max: ',E,Esim_min,Esim_max)
    else:
        if verbose:
            print ('Null hyp that E is consistent can be rejected (95% confidence)')
            print ('E,min,max: ',E,Esim_min,Esim_max)
        E_result=0



    if plot:
    #plot stereonet with contours if desired
        fig=plt.figure(figsize=(12,4))
        ax1=fig.add_subplot(141)
        sp,sn, XX, YY = prediction_map_GGP_su(lat,GGPmodel,degree=degree,dx=0.01,dy=0.01) #map out pdf
        if kappa ==-1:
            kap='Inf'
        else:
            kap=str(kappa)
        txtstring='a) Lat.: '+str(np.round(lat,1))+'; $\kappa$: '+kap 
        ax1.text(-1,1.1,txtstring,fontsize=14)
        ax1.text(-.7,-1.2,'model:'+model_name,fontsize=14)
        ipmag.plot_net(tick_spacing=30) #create net
        
        ipmag.plot_di(dec=Ds,inc=Is,color='green',markersize=10) #plot data
        #levels = np.linspace(np.min(sp),np.max(sp),24)[1::4] #produce contour levels
        levels = np.linspace(np.min(sp),np.max(sp),12)[1::4] #produce contour levels
        plt.contour(XX,YY,sp,levels=levels,colors='grey',linestyle='dotted',linewidth=.1) #plot contours
        #plt.title('lat='+str(np.round(lat,1))+'; $\kappa$: '+kap+'; model:'+model_name ) # replace -1 with inf
        I0 = np.linspace(-90,90,180)
        D0 = np.linspace(-180,180,360)
        
        Iecdf = np.zeros(np.size(I0))
        for i in range(np.size(I0)):
            Iecdf[i] = np.mean(Is<=I0[i])
    
        Decdf = np.zeros(np.size(D0))
        for i in range(np.size(D0)):
            Decdf[i] = np.mean(Ds<=D0[i])
        ax2=fig.add_subplot(142)
        ax2.tick_params(axis='x', labelrotation=90)
        ax2.plot(D0,Dcdf(np.deg2rad(D0)),'r-',linewidth=2)
        ax2.plot(D0,Decdf,'k',linestyle='dotted')
        #ax1.plot(Ds,np.zeros(np.size(Ds))+0.025,'+k')
        ax2.text(-170,1.14,'b)',fontsize=14)
        if A2D<3.07:
            ax2.text(-170,.8,'Decs: Pass',color='red',fontsize=14)
        else:
            ax2.text(-170,.8,'Decs: Fail',color='red',fontsize=14)
        ax2.set_xlim([-180,180])
        ax2.set_ylim([0,1])
        ax2.minorticks_on()
        ax2.set_xticks(np.arange(-180, 180+1, 45.0))
        ax2.set_xlabel('Declination[$^o$]',fontsize=14,color='red')
        ax2.set_ylabel('Cumulative Probability',fontsize=14)
        ax3=ax2.twiny()

        ax3.plot(I0,Icdf(np.deg2rad(I0)),'b-',linewidth=2)
        ax3.plot(I0,Iecdf,'k',linestyle='dotted')
        #ax2.plot(Is,np.ones(np.size(Is))+0.025,'+k')
        ax3.set_xlim([-90,90])
        ax3.set_ylim([0,1])
        ax3.minorticks_on()
        ax3.set_xticks(np.arange(-90, 90+1, 30.0))
        ax3.set_xlabel('Inclination[$^o$]',fontsize=14,color='blue')
        if A2I<3.07:
            ax3.text(-85,.7,'Incs: Pass',color='blue',fontsize=14)
        else:
            ax3.text(-85,.7,'Incs: Fail',color='blue',fontsize=14)
        ax4=fig.add_subplot(143)
        X=V2decs
        Y=np.arange(1,len(X)+1)/len(X)
        ax4.plot(X,Y,'r-')
        ax4.axvline(V2dec,label='V2dec of data')
        ax4.axvline(V2sim_min,linestyle='dotted',color='black',label='V2dec bounds of model')
        ax4.axvline(V2sim_max,linestyle='dotted',color='black')
        plt.xlabel('Simulated $V2_{decs}$',fontsize=14)
        plt.ylabel('Cumulative Distribution Function',fontsize=14)
        #plt.legend(loc='lower right')
        v2_pass='['+str(np.round(V2sim_max,1))+'<='+str(np.round(V2dec,1))+'>='+str(np.round(V2sim_min,1))+']'
        if V2sim_max<V2dec:
            v2_fail='['+str(np.round(V2sim_max,1))+'<'+str(np.round(V2dec,1))+']'
        elif V2sim_min>V2dec:
            v2_fail='['+str(np.round(V2dec,1))+'>'+str(np.round(V2sim_min,1))+']'
        if V2_result==1:   
            ax4.text(0,1.14,'c) V2: Pass',transform=ax4.transAxes,fontsize=14)
            ax4.text(0,1.05,v2_pass,transform=ax4.transAxes,fontsize=12)
            #plt.text(.2,.9,'V2: Pass', transform=ax4.transAxes,fontsize=14,color='red')
        else:   
            ax4.text(0,1.14,'c) V2: Fail',transform=ax4.transAxes,fontsize=14)
            ax4.text(0,1.05,v2_fail,transform=ax4.transAxes,fontsize=12)
            #plt.text(.2,.9,'V2: Fail', transform=ax4.transAxes,fontsize=14,color='red')

        ax5=fig.add_subplot(144)
        X=Es
        Y=np.arange(1,len(X)+1)/len(X)
        ax5.plot(X,Y,'b-')

        ax5.axvline(E,label='E of data')
        ax5.axvline(Esim_min,linestyle='dotted',color='black',label='E bounds of model')
        ax5.axvline(Esim_max,linestyle='dotted',color='black')
        plt.xlabel('Simulated $E$',fontsize=14)
        e_pass='['+str(np.round(Esim_max,2))+'<='+str(np.round(E,2))+'>='+str(np.round(Esim_min,2))+']'
        if Esim_max<E:
            e_fail='['+str(np.round(Esim_max,2))+'<'+str(np.round(E,2))+']'
        elif Esim_min>E:
            e_fail='['+str(np.round(E,2))+'>'+np.round(Esim_min,2)+']'
        if E_result==1: 
            ax5.text(0,1.14,'d) E: Pass',transform=ax5.transAxes,fontsize=14)
            ax5.text(0,1.05,e_pass,transform=ax5.transAxes,fontsize=12)
            #plt.text(.2,.9,'E: Pass', transform=ax5.transAxes,fontsize=14,color='blue')
        else:   
            ax5.text(0,1.14,'d) E: Fail',transform=ax5.transAxes,fontsize=14)
            ax5.text(0,1.05,e_fail,transform=ax5.transAxes,fontsize=12)
            #plt.text(.2,.9,'E: Fail', transform=ax5.transAxes,fontsize=14,color='blue')
        #plt.legend(loc='lower right')
        plt.tight_layout()
        if saveto:
            plt.savefig(saveto)
        plt.show()
    res_dict={'kappa':kappa,'lat':round(lat,1),'A2D':round(A2D,4),'A2I':round(A2I,4),'pID':round(pID,4),'H':H,'V2dec':round(V2dec,1)
                  ,'V2sim_min':round(V2sim_min,1),'V2sim_max':round(V2sim_max,1),
                   'E':round(E,4),'Esim_min':round(Esim_min,4),'Esim_max':round(Esim_max,4),'V2_result':V2_result,'E_result':E_result}
        
    
    return res_dict

def svei_test_varkap(di_block,model_name='THG24',degree=8,lat=False,plot=False,cite="",saveto=False,
                      num_sims=1000,verbose=False): #perform the AD test on observed incs and decs
    """
    Calls svei_test to perform the Anderson-Darling (AD) test on observed inclinations and declinations and Monte Carlo
       simulation to estimate 95% confidence bounds on V2dec and E.  Uses kappa = inf to start, then 100, then 50
       to find consistent result.  

    Parameters:
        di_block=Array of declinations,inclinations (degrees)
        model_name: GGP model name.
        degree (int): Maximum degree of the GGP model. Default is 8.
        lat (float): Assumed latitude of the site. If False, use inclinations to calculate the latitude. Default is False.
        plot (bool): Whether to plot the ECDF comparison, stereonet and CDFs for V2dec and E. Default is False.
        cite (str): Citation information for the GGP model. Default is an empty string.
        saveto (bool or str): If provided, save the plot to the specified file path. Default is False.
        num_sims (int): number of Monte Carlo simulations for V2dec, E bounds calculation
        verbose (bool): if True, print commentary

    Returns:
        res_dict (dict): Dictionary with the following parameters:
            kappa (float): kappa used in final simulation
            H (int): 0 if the null hypothesis cannot be rejected, 1 otherwise.
            A2I (float): Test statistic for inclinations.
            A2D (float): Test statistic for declinations.
            pID (float): Representation of combined p-values (can be used for minimization to optimize latitude).
            lat (float): Latitude of the site.
            V2dec (float): Declination of minor principle component of data set. 
            V2sim_min, V2sim_max (floats): Bounds on V2dec from Monte Carlo simulation
            V2_result (integer): 0 if V2dec not in bounds, 1 if in bounds (consistent)
            E (float): Elongation (tau2/tau3) of data set 
            Esim_min, Esim_max (floats): Bounds on elongation from Monte Carlo simulation
            E_result (integer): 0 if V2dec not in bounds, 1 if in bounds (consistent)
    """    
    
    n = len(di_block)
    if n<5:
        raise ValueError("Insufficient data, N must be 5 or greater")
        return {}
    else:
        kappa = -1 # infinite kappa
        res_dict=svei_test(di_block,num_sims=num_sims,plot=plot, kappa=kappa,   
                              model_name=model_name,saveto=saveto)
        res_dict['model']=model_name
        res_dict['N']=len(di_block)
        if res_dict['H']==1 or res_dict['V2_result']==0 or res_dict['E_result']==0:
            kappa=100
            if verbose:print ('svei_test failed, repeating svei_test with kappa ',kappa)
            res_dict=svei_test(di_block,num_sims=num_sims,plot=plot, kappa=kappa,   
                                  model_name=model_name,saveto=saveto)
            if res_dict['H']==1 or res_dict['V2_result']==0 or res_dict['E_result']==0:
                kappa=50
                if verbose:print ('svei_test failed, repeating svei_test with kappa ',kappa)
                res_dict=svei_test(di_block,num_sims=num_sims,plot=plot, kappa=kappa,   
                                      model_name=model_name,saveto=saveto)
        res_dict['kappa']=kappa
        res_dict['N']=len(di_block)
        res_dict['model']=model_name
    return res_dict

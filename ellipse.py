#!/usr/bin/env python
import numpy
def dir2cart(dir):   # subroutine to do conversion
    """
    converts direction in dir to cartesian coordinates in cart
    """
    rad=numpy.pi/180.# define constant to convert from degrees to radians
    cart=[]# initialize list for cartesian coordinates
    cart.append(numpy.cos(dir[0]*rad)*numpy.cos(dir[1]*rad)*dir[2])  # append the x coordinate
    cart.append(numpy.sin(dir[0]*rad)*numpy.cos(dir[1]*rad)*dir[2])# append the y coordinate
    cart.append(numpy.sin(dir[1]*rad)*dir[2])# append the z coordinate
    return cart # return the list of coordinates


def ellipse(pars):
    """
    function to calculate points on an ellipse about Pdec,Pdip with angle beta,gamma
    """
    rad=numpy.pi/180.
    Pdec,Pinc,beta,Bdec,Binc,gamma,Gdec,Ginc=pars[0],pars[1],pars[2],pars[3],pars[4],pars[5],pars[6],pars[7]
    if beta > 90. or gamma>90:
        beta=180.-beta
        gamma=180.-beta
        Pdec=Pdec-180.
        Pinc=-Pinc
    beta,gamma=beta*rad,gamma*rad # convert to radians
    X_ell,Y_ell,X_up,Y_up,PTS=[],[],[],[],[]
    nums=201
    xnum=float(nums-1.)/2.
# set up t matrix
    t=[[0,0,0],[0,0,0],[0,0,0]]
    X=dir2cart((Pdec,Pinc,1.0)) # convert to cartesian coordintes
# set up rotation matrix t
    t[0][2]=X[0]
    t[1][2]=X[1]
    t[2][2]=X[2]
    X=dir2cart((Bdec,Binc,1.0))
    t[0][0]=X[0]
    t[1][0]=X[1]
    t[2][0]=X[2]
    X=dir2cart((Gdec,Ginc,1.0))
    t[0][1]=X[0]
    t[1][1]=X[1]
    t[2][1]=X[2]
# set up v matrix
    v,ELL=[0,0,0],[]
    for i in range(nums):  # incremental point along ellipse
        psi=float(i)*numpy.pi/xnum
        v[0]=numpy.sin(beta)*numpy.cos(psi) 
        v[1]=numpy.sin(gamma)*numpy.sin(psi) 
        v[2]=numpy.sqrt(1.-v[0]**2 - v[1]**2)
        elli=[0,0,0]
# calculate points on the ellipse
        for j in range(3):
            for k in range(3):
                elli[j]=elli[j] + t[j][k]*v[k]  # cartesian coordinate j of ellipse
        ELL.append(elli)
    return ELL

def main():
    dir=[]
    ans=raw_input('Declination: [cntrl-D  to quit] ')
    dir.append(float(ans))
    ans=raw_input('Inclination: ')
    dir.append(float(ans))
    ans=raw_input('beta: ')
    dir.append(float(ans))
    dir.append(0.)
    dir.append(0.)
    ans=raw_input('gamma: ')
    dir.append(float(ans))
    dir.append(90.)
    dir.append(0.)
    print  ellipse(dir)
main()
    

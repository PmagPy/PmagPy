#!/usr/bin/env python 

import numpy
from numpy import *



x = r_[  9., 35., -13.,  10.,  23.,   0.]
y = r_[ 34., 10.,   6., -14.,  27., -10.]
#x = x / max(x)
#y = y / max(y)

# this is the main function which performs the entire curve fitting sequence using algebraic and geometric fitting
def AraiCurvature(x=x,y=y):
    """
    input: list of x points, list of y points
    output: k, a, b, SSE.  curvature, circle center, and SSE
    Function for calculating the radius of the best fit circle to a set of 
    x-y coordinates.
    Paterson, G. A., (2011), A simple test for the presence of multidomain
    behaviour during paleointensity experiments, J. Geophys. Res., in press,
    doi: 10.1029/2011JB008369

    """
    # makes sure all values are floats, then norms them by largest value
    X = numpy.array(map(float, x))
    X = X / max(X)
    Y = numpy.array(map(float, y))
    Y = Y / max(Y)
    XY = numpy.array(zip(X, Y))
                  
    #Provide the intitial estimate
    E1=TaubinSVD(XY);

    #Determine the iterative solution
    E2=LMA(XY, E1);

    estimates=[E2[2], E2[0], E2[1]];
    
    best_a = E2[0]
    best_b = E2[1]
    best_r = E2[2]

    if best_a <= numpy.mean(X) and best_b <= numpy.mean(Y):
        k = -1./best_r
    else:
        k = 1./best_r

    SSE = get_SSE(best_a, best_b, best_r, X, Y)
    return k, best_a, best_b, SSE


def TaubinSVD(XY):
    """
    algebraic circle fit
    input: list [[x_1, y_1], [x_2, y_2], ....]
    output: a, b, r.  a and b are the center of the fitting circle, and r is the radius

     Algebraic circle fit by Taubin
      G. Taubin, "Estimation Of Planar Curves, Surfaces And Nonplanar
                  Space Curves Defined By Implicit Equations, With
                  Applications To Edge And Range Image Segmentation",
      IEEE Trans. PAMI, Vol. 13, pages 1115-1138, (1991)
    """
    XY = numpy.array(XY)
    X = XY[:,0] - numpy.mean(XY[:,0]) # norming points by x avg
    Y = XY[:,1] - numpy.mean(XY[:,1]) # norming points by y avg
    centroid = [numpy.mean(XY[:,0]), numpy.mean(XY[:,1])]
    Z = X * X + Y * Y  
    Zmean = numpy.mean(Z)
    Z0 = (Z - Zmean) / (2. * numpy.sqrt(Zmean))
    ZXY = numpy.array([Z0, X, Y]).T
    U, S, V = numpy.linalg.svd(ZXY, full_matrices=False) # 
    V = V.transpose()
    A = V[:,2]
    A[0] = A[0] / (2. * numpy.sqrt(Zmean))
    A = numpy.concatenate([A, [(-1. * Zmean * A[0])]], axis=0)
    a, b = (-1 * A[1:3]) / A[0] / 2 + centroid 
    r = numpy.sqrt(A[1]*A[1]+A[2]*A[2]-4*A[0]*A[3])/abs(A[0])/2;
    return a,b,r

# VarCircle() is used with the geometric fit function LMA()
def VarCircle(XY, Par):  # must have at least 4 sets of xy points or else division by zero occurs
    """
    computing the sample variance of distances from data points (XY) to the circle Par = [a b R]
    """
    if type(XY) != numpy.ndarray:
        XY = numpy.array(XY)
    n = len(XY)
    if n < 4:
        raise Warning("Circle cannot be calculated with less than 4 data points.  Please include more data")
    Dx = XY[:,0] - Par[0]
    Dy = XY[:,1] - Par[1]
    D = numpy.sqrt(Dx * Dx + Dy * Dy) - Par[2]
    result = numpy.dot(D, D)/(n-3)
    return result


def LMA(XY,ParIni):
    """
    input: list of x and y values [[x_1, y_1], [x_2, y_2], ....], and a tuple containing an initial guess (a, b, r)
           which is acquired by using an algebraic circle fit (TaubinSVD)
    output: a, b, r.  a and b are the center of the fitting circle, and r is the radius
    %     Geometric circle fit (minimizing orthogonal distances)  
    %     based on the Levenberg-Marquardt scheme in the
    %     "algebraic parameters" A,B,C,D  with constraint B*B+C*C-4*A*D=1
    %        N. Chernov and C. Lesort, "Least squares fitting of circles",
    %        J. Math. Imag. Vision, Vol. 23, 239-251 (2005)
    """
    factorUp=10
    factorDown=0.04
    lambda0=0.01
    epsilon=0.000001
    IterMAX = 50
    AdjustMax = 20
    Xshift=0  
    Yshift=0  
    dX=1  
    dY=0;                                                                                    
    n = len(XY);      # number of data points

    anew = ParIni[0] + Xshift
    bnew = ParIni[1] + Yshift
    Anew = 1./(2.*ParIni[2])                                                                              
    aabb = anew*anew + bnew*bnew    
    Fnew = (aabb - ParIni[2]*ParIni[2])*Anew 
    Tnew = numpy.arccos(-anew/numpy.sqrt(aabb)) 
    if bnew > 0:
        Tnew = 2*numpy.pi - Tnew
    VarNew = VarCircle(XY,ParIni) 

    VarLambda = lambda0;  
    finish = 0;  
                                                                                                      
    for it in range(0,IterMAX):
                                                                      
        Aold = Anew  
        Fold = Fnew
        Told = Tnew
        VarOld = VarNew

        H = numpy.sqrt(1+4*Aold*Fold);                                                                 
        aold = -H*numpy.cos(Told)/(Aold+Aold) - Xshift;
        bold = -H*numpy.sin(Told)/(Aold+Aold) - Yshift;
        Rold = 1/abs(Aold+Aold); 

        DD = 1 + 4*Aold*Fold; 
        D = numpy.sqrt(DD);  
        CT = numpy.cos(Told); 
        ST = numpy.sin(Told);    
        H11=0; 
        H12=0; 
        H13=0; 
        H22=0; 
        H23=0; 
        H33=0; 
        F1=0; 
        F2=0; 
        F3=0;           
                                                            
        for i in range(0,n):
            Xi = XY[i,0] + Xshift;   
            Yi = XY[i,1] + Yshift;       
            Zi = Xi*Xi + Yi*Yi;  
            Ui = Xi*CT + Yi*ST;             
            Vi =-Xi*ST + Yi*CT;

            ADF = Aold*Zi + D*Ui + Fold;    
            SQ = numpy.sqrt(4*Aold*ADF + 1);           
            DEN = SQ + 1;                                          
            Gi = 2*ADF/DEN;   
            FACT = 2/DEN*(1 - Aold*Gi/SQ);      
            DGDAi = FACT*(Zi + 2*Fold*Ui/D) - Gi*Gi/SQ;                
            DGDFi = FACT*(2*Aold*Ui/D + 1);
            DGDTi = FACT*D*Vi;    
                                                          
            H11 = H11 + DGDAi*DGDAi;                 
            H12 = H12 + DGDAi*DGDFi;                           
            H13 = H13 + DGDAi*DGDTi;                                          
            H22 = H22 + DGDFi*DGDFi;
            H23 = H23 + DGDFi*DGDTi;                                     
            H33 = H33 + DGDTi*DGDTi;                        
                                                 
            F1 = F1 + Gi*DGDAi; 
            F2 = F2 + Gi*DGDFi;    
            F3 = F3 + Gi*DGDTi;


        for adjust in range(1,AdjustMax):
                                              
#             Cholesly decomposition                                     
                                                                       
            G11 = numpy.sqrt(H11 + VarLambda);
            G12 = H12/G11                                                                              
            G13 = H13/G11
            G22 = numpy.sqrt(H22 + VarLambda - G12*G12);                                                              
            G23 = (H23 - G12*G13)/G22;                                             
            G33 = numpy.sqrt(H33 + VarLambda - G13*G13 - G23*G23);                
                                                                                   
            D1 = F1/G11;                                            
            D2 = (F2 - G12*D1)/G22;                                                              
            D3 = (F3 - G13*D1 - G23*D2)/G33;                

            dT = D3/G33;  
            dF = (D2 - G23*dT)/G22 
            dA = (D1 - G12*dF - G13*dT)/G11 
                                                                                   
#            updating the parameters
                                                                                            
            Anew = Aold - dA;  
            Fnew = Fold - dF;                             
            Tnew = Told - dT;

            if 1+4*Anew*Fnew < epsilon and VarLambda>1:  
                Xshift = Xshift + dX;                                          
                Yshift = Yshift + dY;                                                                               
                                                                                     
                H = numpy.sqrt(1+4*Aold*Fold);                               
                aTemp = -H*numpy.cos(Told)/(Aold+Aold) + dX;                                     
                bTemp = -H*numpy.sin(Told)/(Aold+Aold) + dY;                                      
                rTemp = 1/abs(Aold+Aold);                                       
                                                                             
                Anew = 1/(rTemp + rTemp);                         
                aabb = aTemp*aTemp + bTemp*bTemp;                          
                Fnew = (aabb - rTemp*rTemp)*Anew;                             
                Tnew = numpy.arccos(-aTemp/numpy.sqrt(aabb));                                       
                if bTemp > 0:
                    Tnew = 2*numpy.pi - Tnew;           
                VarNew = VarOld;                                         
                break;                               

            
            if 1+4*Anew*Fnew < epsilon:  
                VarLambda = VarLambda * factorUp;             
                continue;              

            DD = 1 + 4*Anew*Fnew;                  
            D = numpy.sqrt(DD);                                                         
            CT = numpy.cos(Tnew);                                
            ST = numpy.sin(Tnew);    
                    
            GG = 0;                
                            

            for i in range(0, n):
                Xi = XY[i,0] + Xshift;          
                Yi = XY[i,1] + Yshift;    
                Zi = Xi*Xi + Yi*Yi; 
                Ui = Xi*CT + Yi*ST;            
                                                 
                ADF = Anew*Zi + D*Ui + Fnew;                    
                SQ = numpy.sqrt(4*Anew*ADF + 1);               
                DEN = SQ + 1;                   
                Gi = 2*ADF/DEN; 
                GG = GG + Gi*Gi;
                                   
            VarNew = GG/(n-3);    
         
            H = numpy.sqrt(1+4*Anew*Fnew);               
            anew = -H*numpy.cos(Tnew)/(Anew+Anew) - Xshift;  
            bnew = -H*numpy.sin(Tnew)/(Anew+Anew) - Yshift;  
            Rnew = 1/abs(Anew+Anew); 

            if VarNew <= VarOld: 
                progress = (abs(anew-aold) + abs(bnew-bold) + abs(Rnew-Rold))/(Rnew+Rold);      
                if progress < epsilon: 
                    Aold = Anew;          
                    Fold = Fnew;      
                    Told = Tnew;           
                    VarOld = VarNew # %#ok<NASGU>  
                    finish = 1;     
                    break;  

                VarLambda = VarLambda * factorDown
                break  
            else:                 #    %   no improvement  
                VarLambda = VarLambda * factorUp;      
                continue;     

        if finish == 1:
            break

    H = numpy.sqrt(1+4*Aold*Fold);                                                                                        
    result_a = -H*numpy.cos(Told)/(Aold+Aold) - Xshift;                                                      
    result_b = -H*numpy.sin(Told)/(Aold+Aold) - Yshift;                                                 
    result_r = 1/abs(Aold+Aold);       

    return result_a, result_b, result_r



def get_SSE(a,b,r,x,y):
    """
    input: a, b, r, x, y.  circle center, radius, xpts, ypts
    output: SSE
    """
    SSE = 0
    X = numpy.array(x)
    Y = numpy.array(y)
    for i in range(len(X)):
        x = X[i]
        y = Y[i]
        v = (numpy.sqrt( (x -a)**2 + (y - b)**2 ) - r )**2
        SSE += v
    return SSE




if __name__ == "__main__":
    x = numpy.array([  9, 35, -13,  10,  23,   0])
    y = numpy.array([ 34, 10,   6, -14,  27, -10])
    AraiCurvature(x, y)

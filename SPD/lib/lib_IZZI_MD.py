#!/usr/bin/env python

from numpy import *



def rect_area(three_points):
   xA,yA=three_points[0][0],three_points[0][1]
   xB,yB=three_points[1][0],three_points[1][1]
   xC,yC=three_points[2][0],three_points[2][1]
   #area=abs((xB*yA-xA*yB)+(xC*yB-xB*yC)+(xA*yC-xC*yA))/2
   area=abs((xB*yA-xA*yB)+(xC*yB-xB*yC)+(xA*yC-xC*yA))/2
   return area


def get_IZZI_MD(X_arai,Y_arai,Step,start,end):
    if end-start <4:
        return(9999.99)

    else:
        X_IZZI_MD,Y_IZZI_MD,Step_IZZI_MD=[],[],[]

        step_tmp=Step[start]
        X_IZZI_MD.append(X_arai[start])
        Y_IZZI_MD.append(Y_arai[start])
        Step_IZZI_MD.append(step_tmp)

        for i in range(start,end+1,1):
            #if i==0:
            #    step_tmp='ZI'
            #    X_IZZI_MD.append(X_arai[0])
            #    Y_IZZI_MD.append(Y_arai[0])
            #   Step_IZZI_MD.append('ZI')
            #    continue
            if step_tmp=='ZI' and Step[i]=='IZ':
                X_IZZI_MD.append(X_arai[i])
                Y_IZZI_MD.append(Y_arai[i])
                Step_IZZI_MD.append('IZ')
                step_tmp='IZ'
                continue
            if step_tmp=='IZ' and Step[i]=='ZI':
                X_IZZI_MD.append(X_arai[i])
                Y_IZZI_MD.append(Y_arai[i])
                Step_IZZI_MD.append('ZI')
                step_tmp='ZI'
                continue
            # if ZI after ZI or IZ after IZ than
            # take only the last one
            if step_tmp=='ZI' and Step[i]=='ZI':
                X_IZZI_MD[-1]=X_arai[i]
                Y_IZZI_MD[-1]=Y_arai[i]
                step_tmp='ZI'
                continue
            if step_tmp=='IZ' and Step[i]=='IZ':
                X_IZZI_MD[-1]=X_arai[i]
                Y_IZZI_MD[-1]=Y_arai[i]
                step_tmp='IZ'

        total_ZI_curve=0
        total_Z_area=0
        # calculate the area between the IZ and the ZI curve
        # and the length of the ZI curve
        # the IZZI parameter is: IZZI_area/ZI_length
        if len(Step_IZZI_MD) <= 2:
           return 0
        for i in range(len(X_IZZI_MD)-2):

            if Step_IZZI_MD[i]=='ZI' or Step_IZZI_MD[i]=='IZ':
                A=array([X_IZZI_MD[i],Y_IZZI_MD[i]])
                B=array([X_IZZI_MD[i+1],Y_IZZI_MD[i+1]])
                C=array([X_IZZI_MD[i+2],Y_IZZI_MD[i+2]])
                area=rect_area([A,B,C])

                slope_A_C=(C[1]-A[1])/(C[0]-A[0])
                intercept_A_C=A[1]-(slope_A_C*A[0])
                #print 'slope_A_C,intercept_A_C', slope_A_C,intercept_A_C
                #raw_input()
                if B[1] < slope_A_C*B[0]+intercept_A_C:
                    down_triangle=True
                else:
                    down_triangle=False

                # negative for IZ below ZI
                # positive for IZ above IZ
                if (down_triangle and Step_IZZI_MD[i]=='ZI')or (not (down_triangle) and Step_IZZI_MD[i]=='IZ'):                    
                    area=-1*area
                total_Z_area=total_Z_area+area
                if Step_IZZI_MD[i]=='ZI':
                    total_ZI_curve=total_ZI_curve+sqrt( (C[0]-A[0])**2 + (C[1]-A[1])**2)

        if total_ZI_curve == 0:
           return 0
        IZZI_MD=total_Z_area/total_ZI_curve
        return(IZZI_MD)

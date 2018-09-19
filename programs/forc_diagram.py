#!/usr/bin/env python
# --*-- coding:utf-8 --*--
'''
#=================================================
/this is for processing and plotting forc diagrams,
/including the conventional and irregualar forc.

/author: Jiabo
/GFZ potsdam
#=================================================
'''
import sys
import os
import numpy as np
import itertools
import matplotlib
matplotlib.use('TKAgg')
from matplotlib import pyplot as plt
import pandas as pd
from scipy.interpolate import griddata
import time
from pmagpy import pmagplotlib
from pmagpy import pmag


class Forc(object):
    def __init__(self, irData=None, fileAdres=None, SF=None):
        '''
        #=================================================
        /process the raw data
        /do the fit
        #=================================================
        '''
        self.rawData = dataLoad(fileAdres)
        # self.matrix_z,self.x_range,self.y_range=dataLoad(fileAdres).initial()
        if irData != None:
            self.rawData = irData  # dataLoad(fileAdres)
        else:
            self.rawData = dataLoad(fileAdres)

        self.fit(SF=SF,
                 x_range=self.rawData.x_range,
                 y_range=self.rawData.y_range,
                 matrix_z=self.rawData.matrix_z)

    def fit(self, SF, x_range, y_range, matrix_z):
        '''
        #=================================================
        /the main fitting process
        /xx,yy,zz = Hb,Ha,p
        /p is the FORC distribution
        /m0,n0 is the index of values on Ha = Hb
        /then loop m0 and n0
        /based on smooth factor(SF)
        /select data grid from the matrix_z for curve fitting
        #=================================================
        '''
        xx, yy, zz = [], [], []
        m0, n0 = [], []
        for m, n in itertools.product(np.arange(0, len(x_range), step=SF), np.arange(0, len(y_range), step=SF)):
            if x_range[m] > y_range[n]:  # Ha nearly equal Hb
                m0.append(m)
                n0.append(n)

        aa, bb, cc = [], [], []
        for m, n in zip(m0, n0):
            s = 0
            try:
                grid_data = []
                a_ = x_range[m+s]
                b_ = y_range[n-s]
                for i, j in itertools.product(np.arange(3*SF+1), np.arange(3*SF+1)):
                    try:
                        grid_data.append(
                            [x_range[m+s+i], y_range[n-s-j], matrix_z.item(n-s-j, m+s+i)])
                    except:
                        try:
                            for i, j in itertools.product(np.arange(3), np.arange(3)):
                                grid_data.append(
                                    [x_range[m+i], y_range[n-j], matrix_z.item(n-j, m+i)])
                        except:
                            pass
                # print(grid_data)
                '''
                #=================================================
                /when SF = n
                /data grid as (2*n+1)x(2*n+1)
                /grid_list: convert grid to list
                /every grid produce on FORC distritution p
                /the poly fitting use d2_func
                #=================================================
                '''
                x, y, z = grid_list(grid_data)
                try:
                    p = d2_func(x, y, z)
                    # print(p)
                    xx.append((a_-b_)/2)
                    yy.append((a_+b_)/2)
                    zz.append(p)
                except Exception as e:
                    # print(e)
                    pass
            except:
                pass

        '''
        #=================================================
        /the data will be save as pandas dataframe
        /all the data with nan values will be delete be dropna()
        #=================================================
        '''
        # print(zz)
        df = pd.DataFrame({'x': xx, 'y': yy, 'z': zz})
        #df = df.replace(0,np.nan)
        df = df.dropna()
        '''
        #=================================================
        /due to the space near Bc = zero
        /the Bi values when Bc <0.003 will be mirrored to -Bc
        #=================================================
        '''
        df_negative = df[(df.x < 0.03)].copy()
        df_negative.x = df_negative.x*-1
        df = df.append(df_negative)
        df = df.drop_duplicates(['x', 'y'])
        df = df.sort_values('x')
        # plt.scatter(df.x,df.y,c=df.z)
        # plt.show()
        '''
        #=================================================
        /reset the Bc and Bi range by X,Y
        /use linear interpolate to obtain FORC distribution
        #=================================================
        '''
        xrange = [0, int((np.max(df.x)+0.05)*10)/10]
        yrange = [int((np.min(df.y)-0.05)*10)/10,
                  int((np.max(df.y)+0.05)*10)/10]
        X = np.linspace(xrange[0], xrange[1], 200)
        Y = np.linspace(yrange[0], yrange[1], 200)
        self.yi, self.xi = np.mgrid[yrange[0]:yrange[1]:200j, xrange[0]:xrange[1]:200j]

        #self.xi,self.yi = np.mgrid[0:0.2:400j,-0.15:0.15:400j]
        z = df.z/np.max(df.z)
        z = np.asarray(z.tolist())
        self.zi = griddata((df.x, df.y), z, (self.xi, self.yi), method='cubic')

    def plot(self, save=False, fmt="svg"):
        fig = plt.figure(figsize=(6, 5), facecolor='white')
        fig.subplots_adjust(left=0.18, right=0.97,
                            bottom=0.18, top=0.9, wspace=0.5, hspace=0.5)
        #ax = fig.add_subplot(1,1,1)
        plt.contour(self.xi*1000, self.yi*1000, self.zi, 9,
                    colors='k', linewidths=0.5)  # mt to T
        # plt.pcolormesh(X,Y,Z_a,cmap=plt.get_cmap('rainbow'))#vmin=np.min(rho)-0.2)
        plt.pcolormesh(self.xi*1000, self.yi*1000, self.zi,
                       cmap=plt.get_cmap('rainbow'))  # vmin=np.min(rho)-0.2)
        plt.colorbar()
        # plt.xlim(0,0.15)
        # plt.ylim(-0.1,0.1)
        plt.xlabel('B$_{c}$ (mT)', fontsize=12)
        plt.ylabel('B$_{i}$ (mT)', fontsize=12)

        from pmagpy import pmagplotlib
        if save:
            pmagplotlib.save_plots({'forc': 1}, {'forc': 'forc.{}'.format(fmt)})
            return
        else:
            pmagplotlib.draw_figs({'forc': 1})
            res = pmagplotlib.save_or_quit()
            if res == 'a':
                pmagplotlib.save_plots({'forc': 1}, {'forc': 'forc.{}'.format(fmt)})


class dataLoad(object):
    '''
    #=================================================
    /process the measured forc data.
    /convert the raw data into matrix
    /with x range and y range
    /empty postion replaced with np.nan
    #=================================================
    '''

    def __init__(self, fileAdres=None):
        self.rawData(fileAdres)

    def rawData(self, fileAdres=None):
        # skip skiprows
        skiprows = None
        skip_from = [b'Field', b'Moment']
        with open(fileAdres, 'rb') as fr:
            #f = fr.read()
            for i, line in enumerate(fr, 1):
                # print(line.split())
                if skip_from == line.split():
                    skiprows = i+2
                    break
                # else:
                #    print('file format wrong, cannot find the data row.')
        skiprows = 34 if skiprows == None else skiprows
        df = pd.read_csv(fileAdres, skiprows=skiprows, sep='\s+',
                         delimiter=',', names=['H', 'M'], skipfooter=1,
                         engine='python')

        H = df.H  # measured field
        M = df.M  # measured magnetic moment
        '''
        #=================================================
        /datainterval_H/_M
        /slice the measured data into pieces
        /for every measured FORC
        #=================================================
        '''
        dataInterval_H = []
        dataInterval_M = []
        # print(H)
        cretia = df.H.mean()  # edge of linear programing for selecting data
        H0 = df.H.max()  # the maximum field
        self.x, self.y, self.z = [[], [], []]
        for i in np.arange(1, len(H)):
            dataInterval_H.append(H[i])
            dataInterval_M.append(M[i])
            if abs(H[i]-H0) <= 0.001:  # when the filed reach the max, a new forc
                if len(dataInterval_H) >= 0 and len(dataInterval_H) <= 200:
                    # print(dataInterval_H)
                    Ha = dataInterval_H[0]
                    dataInterval_H.pop(-1)
                    dataInterval_M.pop(-1)
                    Hb = dataInterval_H[1:-1]
                    Hm = dataInterval_M[1:-1]
                    for t in np.arange(len(Hb)):
                        self.x.append(Hb[t])
                        self.y.append(Ha)
                        self.z.append(Hm[t])
                        # print(Ha)
                dataInterval_H = []
                dataInterval_M = []
        self.rawdf = df
        '''
        #=================================================
        transfer the data set to matrix as len(x)*len(y) with z value
        /mesh up the rawdata
        /select the data area by X,Y ranges
        /obtain regular spaced data potins by np.linspace
        /use interplote to caculate the Hm values
        /loop Ha(Y),Hb(X)
        /fill every position with Hm, else with np.nan
        #=================================================
        '''
        self.z = self.z/np.max(self.z)
        # print(int(np.min(self.x)*100)/100,np.max(self.x))
        xrange = [int((np.min(self.x)-0.1)*10)/10,
                  int((np.max(self.x)+0.1)*10)/10]
        yrange = [int((np.min(self.y)-0.1)*10)/10,
                  int((np.max(self.y)+0.1)*10)/10]
        X = np.linspace(xrange[0], xrange[1], 200)
        Y = np.linspace(yrange[0], yrange[1], 200)
        yi, xi = np.mgrid[yrange[0]:yrange[1]:200j, xrange[0]:xrange[1]:200j]

        #X = np.linspace(-0.2,0.3,200)
        #Y = np.linspace(-0.2,0.3,200)
        #xi,yi = np.mgrid[-0.2:0.3:200j,-0.2:0.3:200j]

        zi = griddata((self.x, self.y), self.z, (xi, yi),
                      method='linear')  # !!! must linear
        self.matrix_z = zi
        self.x_range = X
        self.y_range = Y


def d2_func(x, y, z):
    '''
    #=================================================
    /poly fit for every SF grid data
    #=================================================
    '''
    X, Y = np.meshgrid(x, y, copy=False)
    X = X.flatten()
    Y = Y.flatten()
    A = np.array([np.ones(len(X)), X, X**2, Y, Y**2, X*Y]).T
    Z = np.array(z)
    B = Z.flatten()
    # print(A.shape,B.shape)
    coeff, r, rank, s = np.linalg.lstsq(A, B, rcond=None)
    return -coeff[5]


def grid_list(data):
    '''
    #=================================================
    /process the grid data
    /convert to list data for poly fitting
    #=================================================
    '''
    a = []
    b = []
    M = []
    for i in data:
        a.append(i[0])  # np.array([i[1] for i in data], dtype=np.float64)
        b.append(i[1])  # np.array([i[0] for i in data], dtype=np.float64)
        M.append(i[2])  # np.array([i[2] for i in data], dtype=np.float64)
    a = np.array(a, dtype=np.float64).tolist()
    b = np.array(b, dtype=np.float64).tolist()
    M = np.array(M, dtype=np.float64).tolist()
    a = list(set(a))
    b = list(set(b))
    return a, b, M


def param_argvs(inputs=None):
    docm = '''
    NAME
        forc_diagram.py

    DESCRIPTION
        This is for FORC diagrams, including conventional and irregualar FORCs.

    OPTIONS
        -h prints help message and quits
        -f input file name
        -sf smooth factor
        -fmt [svg,png,pdf,eps,jpg] specify format for image, default is svg
        -sav save figure and quit

    INPUT FILE:
        the measured FORC data file must contain the line "  Field     Moment  "
        before the measured data.

    SYNTAX
        forc_diagram.py -f path_to_file/file.txt [command line options]

    '''
    fileAdres, SF = None, None
    if '-h' in inputs:
        print(docm)
        sys.exit(0)
    save = False
    if '-sav' in inputs:
        save = True
    fmt = pmag.get_named_arg('-fmt', ".svg")
    fileAdres = pmag.get_named_arg('-f', reqd=True)
    if not os.path.isfile(fileAdres):
        print('-f file not exist')
        return
    SF = pmag.get_named_arg('-sf', reqd=True)
    try:
        SF = int(inputs[4])
    except:
        print('-sf has to be int')
        return
    return fileAdres, SF, save, fmt


def main():
    #start_time = time.time()
    fileAdres, SF, save, fmt = param_argvs(inputs=sys.argv)

    if fileAdres != None:
        try:
            Forc(fileAdres=fileAdres, SF=SF).plot(save, fmt)
            pass
        except Exception as e:
            print(e)
            pass
    else:
        print('!please include filename and smooth_factor, e.g.:\nforc_diagram.py -f /data_path/forc_file_name.text -sf 5')
    #end_time = time.time()
    #print(end_time - start_time)


if __name__ == '__main__':
    main()

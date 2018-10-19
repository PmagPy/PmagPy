#!/usr/bin/env python

# -*- coding:utf-8 -*-
'''
#====================================================================
this is for IRM decompose, based on log gaussian,

this is based on python3.6 and PyQt5

author: Jiabo Liu
GFZ Potsdam
#====================================================================
'''

import sys
import os
import pandas as pd
#import codecs
import matplotlib
matplotlib.use('Qt5Agg')
from PyQt5 import QtCore
from PyQt5.QtWidgets import (QApplication,QMainWindow,QGridLayout,QSizePolicy,
                             QWidget,QAction,QFileDialog,QPushButton,QTextEdit,
                             QLabel,QLineEdit,QVBoxLayout)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
#from lea import Lea
from matplotlib import pyplot as plt
from scipy import interpolate,spatial
from scipy.stats import norm
import numpy as np
try:
    from lmfit.models import GaussianModel
except ImportError:
    print('-E- You must install lmfit to run this program')
    print('    If you have Anaconda Python, you can install with the following command:')
    print('    conda install lmfit --channel conda-forge')
    sys.exit()
try:
    from sklearn.mixture import GaussianMixture as GMM
except ImportError:
    print('-E- You must install scikit-learn to run this program')
    print('    If you have Anaconda Python, you can install with the following command:')
    print('    conda install scikit-learn')

from lmfit import minimize,Parameters

class MyMplCanvas(FigureCanvas):
    '''
    #====================================================================
    this is the parent class for matplotlib plot in PyQt5.
    setting plot properties.
    passing data for plot, for convinience ,the class of dataFit was
    /directly used.
    #====================================================================
    '''
    def __init__(self,parent=None,filePath=None,paramDict=None,groups=None,datafit=None):
        width,hight,dpi=5,4,100
        self.parent=parent
        self.filePath=filePath
        self.fitNumber=3 if groups==None else int(groups)
        self.paramDict=paramDict
        self.datafit = datafit
        plt.ioff()
        self.fig = plt.figure(figsize=(width,hight),dpi=dpi,facecolor='white')
        self.fig.subplots_adjust(left=0.18, right=0.97,
                        bottom=0.18, top=0.9, wspace=0.5, hspace=0.5)
        self.axes = self.fig.add_subplot(111)
        #self.axes.hold(False)
        self.initialplot()
        FigureCanvas.__init__(self,self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def initialplot(self):
        pass

def loadData(filePath=None):
    '''
    #====================================================================
    in:
    read measured raw data file,
    search the line ['    Field       Remanence  '] in measured data file,
    skip all the rows above and the last line,
    otherwise, load data as two columns.
    #
    out:
    rawDf,fitDf are the pandas dataframe of measured raw data, and the
    log10 interploted data
    #====================================================================
    '''
    skip_from = '    Field       Remanence  '
    with open(filePath,'rb') as fr:
        #f = fr.read()
        for i,line in enumerate(fr,1):
            #print(line)
            if skip_from in str(line):
                skiprows=i+2
                break
            else:
                skiprows=None
    skiprows = skiprows if isinstance(skiprows,int) else 1
    rawDf = pd.read_csv(filePath, sep='\s+', delimiter=',', names=['field','remanance'],
                        dtype=np.float64, skiprows=skiprows, skipfooter=1,engine='python')
    rawDf = rawDf[(rawDf['field']>0)]
    rawDf = rawDf.sort_values(by=['field'])
    rawDf['field'] = rawDf['field']*10**3 # mT to # T
    y_measure=rawDf['remanance']
    rawDf = rawDf[(rawDf['field']>=2)]
    rawDf['field_log'] = np.log10(rawDf['field'])
    rawDf['rem_gradient'] = np.gradient(rawDf['remanance'])
    rawDf['rem_grad_norm'] = rawDf['rem_gradient']/rawDf['rem_gradient'].max()
    field_fit = np.linspace(np.log10(rawDf['field'].min()),
                            np.log10(rawDf['field'].max()), 100)
    y_gradient = interpolate.splev(field_fit,
                                   interpolate.splrep(np.log10(rawDf['field']),
                                   np.gradient(rawDf['remanance'])))
    fitDf = pd.DataFrame({'field':field_fit,'remanance':y_gradient})
    fitDf.remanance[fitDf.remanance<=0] = 10**-15
    return rawDf,fitDf

class dataFit():
    '''
    #====================================================================
    this is the main part for data fitting
    #
    raw_data: get the measured and log10 interploted data (rawDf,fitDf)
    #
    rand_data: regarded the IRM acquisition curve as frequency distribution,
               produce random numbers based on the frequency. that is,
               converte IRM acquision to 1Dimensioanl dataset.
    #
    loggausfit: using sklearn GMM model. the GMM defualt using k-mean
                for clustering. then iterate E-M steps to get the best
                fit.

                With specified unmixing numbers, the rand_data run 10 times,
                the GMM run 20 times. for each time, the fitted results are
                recorded in a pandas DataFrame(df).

                After all the iterations. the df id sorted by covariances(max),
                residuals(distance,min), and std(means) (max).

                The best result is base on max covariances, minimum residuals,
                and maximum distince means.
    #
    fitParams: the parameters of the best fit will be recorded and printed
                on the GUI.
    #====================================================================
    '''
    def __init__(self,filePath=None,fitNumber=None):
        self.fitNumber=fitNumber
        self.raw_data(filePath=filePath)
        self.rand_data()
        self.loggausfit()
        self.fitParams()

    def raw_data(self,filePath=None):
        self.rawDf,self.fitDf = loadData(filePath)

    def rand_data(self):
        p = self.fitDf['remanance']/sum(self.fitDf['remanance'])
        data = np.random.choice(a=self.fitDf['field'],size=500,p=p)
        return data.reshape(-1,1)

    def loggausfit(self):
        self.fitDf['IRM_norm'] = self.fitDf['remanance']/self.fitDf['remanance'].max()
        xstd,distance,means,covras,weights,yfits = [],[],[],[],[],[]
        for i in range(10):
            data = self.rand_data()
            for j in range(20):
                gmm = GMM(self.fitNumber, covariance_type='full')
                model = gmm.fit(data)
                xstd.append(np.std(model.means_))
                means.append(model.means_)
                covras.append(model.covariances_)
                weights.append(model.weights_)

                sample = self.fitDf['field'].values.reshape((-1, 1))

                logprob = model.score_samples(sample)  # M_best.eval(x)
                responsibilities = model.predict_proba(sample)
                pdf = np.exp(logprob)
                pdf_individual = responsibilities * pdf[:, np.newaxis]
                pdf_norm = np.sum(pdf_individual,axis=1)/np.max(np.sum(pdf_individual,
                                                                   axis=1))
                #distance.append(np.max([abs(i-j) for i,j in zip(np.sum(pdf_individual,axis=1),p)]))
                distance.append(1 - spatial.distance.cosine(pdf_norm,self.fitDf['IRM_norm']))
                yfits.append(pdf_individual)
            del data
        df = pd.DataFrame({'xstd':xstd, 'distance':distance, 'means':means,
                           'covras':covras, 'yfits':yfits, 'weights':weights})
        df['cov_max'] = [np.min(i) for i in df['covras']]
        df = df.sort_values(by=['distance','cov_max','xstd'], ascending=[False,True,False])
        pdf_best = df['yfits'].iloc[0]
        self.means = df['means'].iloc[0]
        self.covra = df['covras'].iloc[0]#sigma**2
        self.weights = df['weights'].iloc[0]
        self.pdf_best = pdf_best/np.max(np.sum(pdf_best,axis=1))

    def fitParams(self):
        params = Parameters()
        for i in np.arange(self.fitNumber):
            sequence = 'g' + str(i + 1) + '_'
            params.add(sequence+'amplitude', value=self.weights[i])
            params.add(sequence+'center', value=self.means[i][0])
            params.add(sequence+'sigma', value=np.sqrt(self.covra[i][0][0]))
        self.params = params

class lmLeast():
    '''
    #====================================================================
    the func and residuals are functions for lmfit.minimize() in reFit
    #
    func: caculate the gaussian distince
    #
    residuals: caculate the residuals between fit and measured data
    #====================================================================
    '''
    def __init__(self,fitNumber=None):
        self.fitNumber=fitNumber
    def func(self,x,params):
        y_component=[]
        for i in np.arange(self.fitNumber):
            A = 'g'+str(i+1)+'_amplitude'
            s = 'g'+str(i+1)+'_sigma'
            c = 'g'+str(i+1)+'_center'
            A = params[A].value
            s= params[s].value
            c= params[c].value
            #y = A/(s*np.sqrt(2*np.pi))*np.exp(-(x-c)**2/(2*s**2))
            y = A*norm.pdf(x,loc=c,scale=s)
            y_component.append(y)
        return y_component
    def residuals(self,params, x, y):
        y_component = self.func(x, params)
        return y - sum(y_component)

class reFit(MyMplCanvas):
    '''
    #====================================================================
    the child class of MyMplCanvas

    when changed the values of parameters on GUI, and clicked reFit button,
    the dataFit will not work,

    on the other hand, the lmfit.minimize will be used here.

    the parameters on the GUI will be passed here, and based on the least
    square, to caculate the best fit.
    #====================================================================
    '''
    def initialplot(self):
        self.fitResult = self.datafit
        self.replot()
    def replot(self):
        params = Parameters()
        for key,value in self.paramDict.items():
            params.add(key, value=float(value.text()))
        for i in np.arange(self.fitNumber):
            sequence = 'g'+str(i+1)+'_'
            center_value = params[sequence+'center'].value
            params[sequence+'center'].set(center_value, min=center_value-0.05,
                                          max=center_value+0.05)
            sigma_value = params[sequence+'sigma'].value
            params[sequence+'sigma'].set(sigma_value, min=sigma_value-0.05,
                                         max=sigma_value+0.05)
            ampl_value = params[sequence+'amplitude'].value
            params[sequence+'amplitude'].set(ampl_value, min=ampl_value-0.5,
                                             max=ampl_value+0.5)
        result = minimize(lmLeast(self.fitNumber).residuals, params, args=(self.fitResult.fitDf['field'], self.fitResult.fitDf['IRM_norm']),
                          method='cg')
        self.params = result.params
        #FitMplCanvas.fitPlot(self)
        pdf_adjust = lmLeast(self.fitNumber).func(self.fitResult.fitDf['field'].values,self.params)
        pdf_adjust = pdf_adjust/np.max(np.sum(pdf_adjust,axis=0))
        ax=self.axes
        fit_plots(ax=ax,
                   xfit=self.fitResult.fitDf['field'],
                   xraw=self.fitResult.rawDf['field_log'],
                   yfit=np.array(pdf_adjust).transpose(),
                   yraw=self.fitResult.rawDf['rem_grad_norm'])

def fit_plots(ax,xfit,xraw,yfit,yraw):
    '''
    #====================================================================
    plot the fitted results for data fit and refit
    #====================================================================
    '''
    global _yfits_
    _yfits_ = yfit
    ax.plot(xfit, yfit)
    ax.plot(xfit, np.sum(yfit,axis=1))
    ax.scatter(xraw, yraw)
    ax.set_xlabel('Field (log10(mT))')
    ax.set_ylabel('IRM normalization')

class FitMplCanvas(MyMplCanvas):
    '''
    #====================================================================
    this is the ploting part, all the data generated by Datafit are assembled here,

    the best fit from dataFit are ploted here.

    the data for plotting is also for output.
    #====================================================================
    '''
    def __init__(self, *args, **kwargs):
        MyMplCanvas.__init__(self, *args, **kwargs)
    def initialplot(self):
        self.fitResult = self.datafit#dataFit(self.filePath,self.fitNumber)
        self.fitPlot()

    def fitPlot(self):
        ax=self.axes
        fit_plots(ax=ax,
                  xfit=self.fitResult.fitDf['field'],
                  xraw=self.fitResult.rawDf['field_log'],
                  yfit=self.fitResult.pdf_best,
                  yraw=self.fitResult.rawDf['rem_grad_norm'])


class adjustFit(MyMplCanvas):
    '''
    #====================================================================
    when the parameter values on the GUI changed,
    the plot will be replot here
    #====================================================================
    '''
    def initialplot(self):
        self.fitResult = self.datafit
        self.replot()
    def replot(self):
        params = Parameters()
        for key,value in self.paramDict.items():
            params.add(key, value=float(value.text()))
        self.params=params
        pdf_adjust = lmLeast(self.fitNumber).func(self.fitResult.fitDf['field'].values,self.params)
        pdf_adjust = pdf_adjust/np.max(np.sum(pdf_adjust,axis=0))
        ax=self.axes
        fit_plots(ax=ax,
                   xfit=self.fitResult.fitDf['field'],
                   xraw=self.fitResult.rawDf['field_log'],
                   yfit=np.array(pdf_adjust).transpose(),
                   yraw=self.fitResult.rawDf['rem_grad_norm'])

class rawPlot(MyMplCanvas):
    '''
    #====================================================================
    this for plot the raw plot button,
    plot the measured data at the beginning
    #====================================================================
    '''
    def initialplot(self):
        ax=self.axes
        ax.set_xlabel('Field (mT)')
        ax.set_ylabel('IRM normalization')
        if self.filePath != None:
            rawDf,fitDf = loadData(filePath=self.filePath)
            ax.plot(rawDf['field'],rawDf['remanance']/rawDf['remanance'].max())
            ax.scatter(rawDf['field'],rawDf['rem_gradient']/rawDf['rem_gradient'].max())
            ax.set_xscale('log')

class Mainwindow(QMainWindow):
    '''
    #====================================================================
    this is PyQt5 GUI
    #====================================================================
    '''
    def __init__(self):
        super().__init__()
        introducion='''irm_unmix
        this is for rock magnetic irm acquisition curves decompose

        New features: Now you can manually adjust all the parameters and see
        the results immediately, and afterwards, you could try 'refit' button
        to better refine your fittings.
        '''
        self.clickCount=0

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.main_widget = QWidget(self)
        self.grid = QGridLayout(self.main_widget)
        self.vbox = QVBoxLayout()

        btLoad = QPushButton('Load',self.main_widget)
        btRaw = QPushButton('Raw data', self.main_widget)
        #btAdjust = QPushButton(Adjust)
        numberLabel = QLabel('Numbers',self.main_widget)
        self.introdueLabel = QLabel(introducion,self.main_widget)
        self.numberText =QLineEdit('3')
        btFit = QPushButton('Fit',self.main_widget)
        btSaveFig = QPushButton('Save Fig', self.main_widget)
        btSaveData = QPushButton('Save Data', self.main_widget)
        btRefit = QPushButton('reFit', self.main_widget)

        self.dataDisp = QTextEdit(self.main_widget)

        btLoad.clicked.connect(self.loadButton)
        btRaw.clicked.connect(self.rawButton)
        btFit.clicked.connect(self.fitButton)
        btSaveFig.clicked.connect(self.SaveFigButton)
        btSaveData.clicked.connect(self.SaveDataButton)
        btRefit.clicked.connect(self.reFit)

        #self.plotButtom()
        #grid.addWidget(self.plot,1,2,2,1)
        self.plot = rawPlot(parent=self.main_widget)
        self.grid.addWidget(self.plot,1,3,5,2)
        self.grid.addWidget(self.dataDisp,1,1,8,1)
        self.grid.addWidget(self.introdueLabel,6,3,3,2)

        self.vbox.addWidget(btLoad,1)
        self.vbox.addWidget(btRaw,2)
        self.vbox.addWidget(numberLabel,3)
        self.vbox.addWidget(self.numberText,4)
        self.vbox.addWidget(btFit,5)
        self.vbox.addWidget(btSaveFig,6)
        self.vbox.addWidget(btSaveData,7)
        self.vbox.addWidget(btRefit,8)

        self.grid.addLayout(self.vbox,1,2,2,1)


        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)

        self.initUI()

        self.show()

    def initUI(self):
        self.statusBar()

        openfile = QAction('open',self)
        openfile.triggered.connect(self.showDialog)
        quitAction = QAction('quit',self)
        quitAction.triggered.connect(self.fileQuit)

        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        filename = menubar.addMenu('&File')
        filename.addAction(openfile)
        filename.addAction(quitAction)

        quitname = menubar.addMenu('&Help')
        menubar.addSeparator()
        quitname.addAction(quitAction)

        self.setGeometry(300,300,1000,800)
        self.setWindowTitle('irm_unmix')

    def showParams(self):
        subGrid = QGridLayout()
        params = self.datafit.params
        self.paramDict = {}
        for i in range(self.fitNumber):
            A = 'g'+str(i+1)+'_amplitude'
            s = 'g'+str(i+1)+'_sigma'
            c = 'g'+str(i+1)+'_center'
            AA = '%.5f'%params[A].value
            ss= '%.5f'%params[s].value
            cc= '%.5f'%params[c].value
            sigmaLable = QLabel('sigma-'+str(i+1))
            sigmaValue = QLineEdit(str(ss))
            centerLable = QLabel('center-'+str(i+1))
            centerValue = QLineEdit(str(cc))
            amplitudeLable = QLabel('Amplitude'+str(i+1))
            amplitudeValue = QLineEdit(str(AA))
            self.paramDict[A] = amplitudeValue
            self.paramDict[s] = sigmaValue
            self.paramDict[c] = centerValue
            subGrid.addWidget(sigmaLable,i,0,1,1)
            subGrid.addWidget(sigmaValue,i,1,1,1)
            subGrid.addWidget(centerLable,i,2,1,1)
            subGrid.addWidget(centerValue,i,3,1,1)
            subGrid.addWidget(amplitudeLable,i,4,1,1)
            subGrid.addWidget(amplitudeValue,i,5,1,1)
        for key, value in self.paramDict.items():
            value.textChanged.connect(self.adjustPlot)
        return subGrid
    def adjustPlot(self):
        if self.plot:
            plt.close(self.plot.fig)
        self.plot = adjustFit(parent=self.main_widget,filePath=self.filePath,
                              groups=self.fitNumber,paramDict=self.paramDict,datafit=self.datafit)
        try:
            self.grid.addWidget(self.plot,1,3,5,2)
        except Exception as e:
            pass
    def reFit(self):

        self.removeGrid()
        if self.plot:
                plt.close(self.plot.fig)

        if self.paramDict:
            self.plot = reFit(self.main_widget,filePath=self.filePath,
                          groups=self.fitNumber,paramDict=self.paramDict,datafit=self.datafit)
        self.grid.addWidget(self.plot,1,3,5,2)
        self.paramsGrid=self.showParams()
        self.grid.addLayout(self.paramsGrid,6,3,3,2)
    def showDialog(self):
        filename=QFileDialog.getOpenFileName(self,'open file','/home/Documents/')
        if filename[0]:
            f = open(filename[0],'r',encoding='utf-8',errors='ignore')
            with f:
                data=f.read()
                self.dataDisp.setText(data)
                self.filePath=filename[0]
                self.workPath=os.path.dirname(filename[0])
            f.close()

    def fileQuit(self):
        sys.exit(app.exec_())

    def loadButton(self):
        self.statusBar().showMessage(self.sender().text())
        self.showDialog()
    def rawButton(self):
        if self.plot:
            plt.close(self.plot.fig)
        try:
            if self.paramDict:
                import gc
                del self.paramDict
                gc.collect()
        except Exception as e:
            pass
        #self.statusBar().showMessage(self.sender().text())
        self.plot = rawPlot(self.main_widget,filePath=self.filePath)
        self.grid.addWidget(self.plot,1,3,5,2)
    def SaveFigButton(self):
        if self.plot:
            self.plot.fig.savefig(os.path.splitext(self.filePath)[0]+'.png')
        else:
            pass
    def SaveDataButton(self):
        if self.plot:
            #----------------------------------------------------------------------
            yfit=_yfits_#global value in def fit_plots(ax,xfit,xraw,yfit,yraw):
            dfraw = self.datafit.rawDf[['field_log','rem_grad_norm']]
            dfraw.columns = ['measured_field_log','measured_gradient_norm']
            dffit = self.datafit.fitDf[['field']].copy()
            dffit.columns = ['fit_field']
            for i in np.arange(self.fitNumber):

                #fIrmcomp = yfit[i].tolist()
                dffit['fitted IRM comoponent '+str(i+1)] = yfit[:,i].tolist()
            df = dffit.join(dfraw, how='outer')
            fileName = os.path.splitext(self.filePath)[0]+'_fit.csv'
            df.to_csv(fileName)
        else:
            pass
    def fitButton(self):
        if self.clickCount !=0:
            self.removeGrid()
        else:
            self.introdueLabel.deleteLater()
        if self.plot:
            plt.close(self.plot.fig)
        self.statusBar().showMessage(self.sender().text())
        self.fitNumber = int(self.numberText.text())
        self.datafit = dataFit(filePath=self.filePath,fitNumber=self.fitNumber)
        #FitMplCanvas(self.main_widget,width=5,hight=4,dpi=100,filePath=self.filePath,groups=self.groups)
        self.plot = FitMplCanvas(self.main_widget,filePath=self.filePath,groups=self.fitNumber,datafit=self.datafit)
        #self.plot = figure()
        self.grid.addWidget(self.plot,1,3,5,2)
        self.paramsGrid=self.showParams()
        self.grid.addLayout(self.paramsGrid,6,3,3,2)
        self.clickCount +=1
    def removeGrid(self):
        for i in range(int(self.fitNumber)*6):
            self.paramsGrid.takeAt(int(self.paramsGrid.count())-1).widget().close()
        self.grid.removeItem(self.paramsGrid)
    def Adjust(self):
        print('ss')

def main():
    if "-h" in sys.argv:
        print("This is a GUI for IRM decompose, based on log gaussian")
        print("To run:")
        print("irm_unmix.py")
        return
    app = QApplication(sys.argv)
    Mwindow = Mainwindow()
    sys.exit(app.exec_())

if __name__=='__main__':
    main()

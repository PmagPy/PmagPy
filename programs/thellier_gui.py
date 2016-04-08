#!/usr/bin/env pythonw

#============================================================================================
# LOG HEADER:
#============================================================================================
#
# Thellier_GUI Version 2.29 01/29/2015
# 1) fix STDEV-OPT extended error bar plor display bug 
# 2) fix paleointensity plot legend when using extended error bars
# 3) fix non-thellier pmag_specimen competability issue

# Thellier_GUI Version 2.28 12/31/2014
# Fix minor bug in delete interpretation buttonn
#
## Thellier_GUI Version 2.27 11/30/2014
#
# Fix in_sigma bug in change criteria dialog box
#
## Thellier_GUI Version 2.26 11/16/2014
# modify code for thellier interpreter
# Add Consistency Check
#
# Thellier_GUI Version 2.25 08/08/2014
# Bug fixes:
# deal with old foramt pmag_criteria.txt when specimen_dang is used as specimen_int_dang; 
# deal with import pmag_criteria.txt file with statistics that do not appear in original pmag_criteria.txt
#  
#
# Thellier_GUI Version 2.24 05/11/2014
# Fix Pmag results tables issues
#
# Thellier_GUI Version 2.23 05/07/2014
# Fix Pmag results tables issues
#
# Thellier_GUI Version 2.22 04/09/2014
# fix Blab window bug
#
# Thellier_GUI Version 2.21 04/07/2014
# fix bug is scat statistics window
#
# Thellier_GUI Version 2.20 04/04/2014
# add support for pTRM after infield step
#
# Thellier_GUI Version 2.19 03/23/2014
# update dialog boxes with SPD.1.0
#
# Thellier_GUI Version 2.18 03/21/2014
# insert SPD.py.
# some bug fix
#
# Thellier_GUI Version 2.17 03/20/2014
# insert SPD.py.
# merge changes in appearance
#
# Thellier_GUI Version 2.16 03/17/2014
# code cleanup for SPD.1.0 insertion
# change pmag_criteria.txt format to fit MagIC model 2.5

# Thellier_GUI Version 2.15 03/0/2014
# minor changes


# Thellier_GUI Version 2.14 02/28/2014
# minor changes compatibiilty with 64 bit python

# Thellier_GUI Version 2.14 02/28/2014
# minor changes compatibiilty with 64 bit python

# Thellier_GUI Version 2.13 02/25/2014
# Add option for more than one pTRMs one after the other

# Thellier_GUI Version 2.12 0/19/2014
# Fix compatibility issues PC/Mac
# change display preferences
#
# Thellier_GUI Version 2.11 01/13/2014
# adjust diplay to automatically fit screen size
#
# Thellier_GUI Version 2.10 01/13/2014
# Fix compatibility with 64 bit
#
# Thellier_GUI Version 2.09 01/05/2014
# Change STDEV-OPT algorithm from minimizing the standard deviaion to minimzing the precentage of standrd deviation.
# Resize acceptance criterai dialog window
#
# Thellier_GUI Version 2.08 12/04/2013
# Add Additivity checks code
#
# Thellier_GUI Version 2.07 11/04/2013
# Add Thellier-Thellier protocol (thermal, not microwave)
# LP-PI-II
# Add full support to livdb formats TH-PI-IZZI+;MW-PI-C+;MW-PI-C++;MW-PI-IZZI+
#
# Thellier_GUI Version 2.06 10/25/2013
# Add Additivity check (Krasa et al., 2003). Lab treatment code is"
# LT-PTRM-AC
#
# Thellier_GUI Version 2.05 9/02/2013
# Add LP-PI-M-II protocol (microwave Thellier experiment)
#
# Thellier_GUI Version 2.041 7/03/2013
# Bug fix cooling rate corrections
#
# Thellier_GUI Version 2.041 6/14/2013
# Bug fix
#
# Thellier_GUI Version 2.04 6/14/2013
# 1. Add conversion script from generic file format
#
# Thellier_GUI Version 2.03 6/6/2013
# 1. Add cooling rate correction option
#
#
# Thellier_GUI Version 2.02 4/26/2013
# 1. add partial support to Microwave
#
# Thellier_GUI Version 2.01 4/26/2013
# 1. remove defenitions imported from pmag.py, so it can run as stand alone file.
# 2. Add ptrm directions statistics
#
#
#
#-------------------------
#
# Thellier_GUI Version 2.00
# Author: Ron Shaar
# Citation: Shaar and Tauxe (2013)
#
# January 2012: Initial revision
#
#
#============================================================================================

global CURRENT_VRSION
global MICROWAVE
global THERMAL
CURRENT_VRSION = "v.2.29"
MICROWAVE=False
THERMAL=True

#from pmag_env import set_env
#set_env.set_backend(wx=True)
import matplotlib
if not matplotlib.get_backend() == 'WXAgg':
    matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas 

import sys, pylab, scipy, os
#import pdb
import pmagpy.pmag as pmag
from pmagpy import check_updates
try:
    import thellier_gui_preferences
except:
    pass
import stat
import shutil
import time
import wx
import wx.grid
import random
from pylab import * # keep this line for now, but I've tried to add pylab to any pylab functions for better namespacing
from scipy.optimize import curve_fit
import wx.lib.agw.floatspin as FS
try:
    from mpl_toolkits.basemap import Basemap, shiftgrid
except:
    pass

from matplotlib.backends.backend_wx import NavigationToolbar2Wx

import dialogs.thellier_consistency_test as thellier_consistency_test
import copy
from copy import deepcopy

import dialogs.thellier_gui_dialogs as thellier_gui_dialogs
import dialogs.thellier_gui_lib as thellier_gui_lib

matplotlib.rc('xtick', labelsize=10) 
matplotlib.rc('ytick', labelsize=10) 
matplotlib.rc('axes', labelsize=8) 
matplotlib.rcParams['savefig.dpi'] = 300.

#pylab.rcParams.update({"svg.embed_char_paths":False})
pylab.rcParams.update({"svg.fonttype":'none'})



#============================================================================================



    
class Arai_GUI(wx.Frame):
    """ The main frame of the application
    """
    title = "PmagPy Thellier GUI %s"%CURRENT_VRSION
    
    def __init__(self, WD=None, parent=None, standalone=True):

        TEXT="""
        NAME
   	thellier_gui.py
    
        DESCRIPTION
   	GUI for interpreting thellier-type paleointensity data.
   	For tutorial chcek PmagPy cookbook in http://earthref.org/PmagPy/cookbook/   	    
        """  
        args=sys.argv
        if "-h" in args:
	   print TEXT
	   sys.exit()
              
        global FIRST_RUN
        FIRST_RUN = True if standalone else False
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title, name='thellier gui')
        self.redo_specimens={}
        self.currentDirectory = os.getcwd() # get the current working directory
        if WD:
            self.WD = WD
            self.get_DIR(self.WD)
        else:
            self.get_DIR()        # choose directory dialog        
        
         
        # inialize selecting criteria
        self.acceptance_criteria=pmag.initialize_acceptance_criteria()
        self.add_thellier_gui_criteria()
        self.read_criteria_file(os.path.join(self.WD,"pmag_criteria.txt"))
        # preferences

        preferences=self.get_preferences()
        self.dpi = 100
        
        self.preferences=preferences
             
        self.Data,self.Data_hierarchy,self.Data_info={},{},{}
        self.MagIC_directories_list=[]

        self.Data_info=self.get_data_info() # get all ages, locations etc. (from er_ages, er_sites, er_locations)
        self.Data,self.Data_hierarchy=self.get_data() # Get data from magic_measurements and rmag_anistropy if exist.

        if  "-tree" in sys.argv and FIRST_RUN:
            self.open_magic_tree()

        self.Data_samples={} # interpretations of samples are kept here
        self.Data_sites={}   # interpretations of sites are kept here
        #self.Data_samples_or_sites={}   # interpretations of sites are kept here

        self.last_saved_pars={}
        self.specimens=self.Data.keys()         # get list of specimens
        self.specimens.sort()                   # get list of specimens
        self.panel = wx.Panel(self)          # make the Panel
        self.Main_Frame()                   # build the main frame
        self.create_menu() 
        try:
            self.Arai_zoom()
            self.Zij_zoom()
        except:
            pass
        self.arrow_keys()
        FIRST_RUN=False

        self.get_previous_interpretation() # get interpretations from pmag_specimens.txt
        FIRST_RUN=False
        self.Bind(wx.EVT_CLOSE, self.on_menu_exit) 
        self.close_warning=False
                      
    def get_DIR(self, WD=None):
        """ 
        open dialog box for choosing a working directory 
        """
        if "-WD" in sys.argv and FIRST_RUN:
            ind=sys.argv.index('-WD')
            self.WD=sys.argv[ind+1] 
        elif not WD: # if no arg was passed in for WD, make a dialog to choose one   
            dialog = wx.DirDialog(None, "Choose a directory:",defaultPath = self.currentDirectory ,style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON | wx.DD_CHANGE_DIR)
            ok = dialog.ShowModal()
            if ok == wx.ID_OK:
                self.WD=dialog.GetPath()
            else:
                self.WD = os.getcwd()
            dialog.Destroy()
        self.magic_file=os.path.join(self.WD,"magic_measurements.txt")
            #intialize GUI_log
        self.GUI_log=open(os.path.join(self.WD, "thellier_GUI.log"),'w')
        self.GUI_log.write("starting...\n")
        self.GUI_log=open(os.path.join(self.WD, "thellier_GUI.log"),'a')
        os.chdir(self.WD)
        self.WD=os.getcwd()
        
    def Main_Frame(self):
        """ 
        Build main frame od panel: buttons, etc.
        choose the first specimen and display data
        """

        #----------------------------------------------------------------------                     
        # initialize first specimen in list as current specimen
        #----------------------------------------------------------------------                     

        try:
            self.s=self.specimens[0]
        except:
            self.s=""

        #----------------------------------------------------------------------                     
        # create main panel in the right size
        #----------------------------------------------------------------------                     

        dw, dh = wx.DisplaySize() 
        w, h = self.GetSize()
        #print 'diplay', dw, dh
        #print "gui", w, h
        r1=dw/1250.
        r2=dw/750.
        
        #if  dw>w:
        GUI_RESOLUTION=min(r1,r2,1.3)
        if 'gui_resolution' in self.preferences.keys():
            if float(self.preferences['gui_resolution'])!=1:
        #self.GUI_RESOLUTION=0.75
                self.GUI_RESOLUTION=float(self.preferences['gui_resolution'])/100
            else:
                self.GUI_RESOLUTION=min(r1,r2,1.3)
        else:
            self.GUI_RESOLUTION=min(r1,r2,1.3)

        #----------------------------------------------------------------------                     
        # adjust font size
        #----------------------------------------------------------------------                     


        if self.GUI_RESOLUTION >= 1.1 and self.GUI_RESOLUTION <= 1.3:
            font2 = wx.Font(13, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Arial')
        elif self.GUI_RESOLUTION <= 0.9 and self.GUI_RESOLUTION < 1.0 :
            font2 = wx.Font(11, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Arial')
        elif self.GUI_RESOLUTION <= 0.9 :
            font2 = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Arial')
        else:
            font2 = wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Arial')
        print "    self.GUI_RESOLUTION",self.GUI_RESOLUTION

        # set font size and style
        #font1 = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Comic Sans MS')
        FONT_RATIO=self.GUI_RESOLUTION+(self.GUI_RESOLUTION-1)*5
        font1 = wx.Font(9+FONT_RATIO, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Arial')
        # GUI headers
        
        font3 = wx.Font(11+FONT_RATIO, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Arial')
        font = wx.SystemSettings_GetFont(wx.SYS_SYSTEM_FONT)
        font.SetPointSize(10+FONT_RATIO)        
                        
        #----------------------------------------------------------------------                     
        # Create Figures and FigCanvas objects. 
        #----------------------------------------------------------------------                     

        self.fig1 = pylab.Figure((5.*self.GUI_RESOLUTION, 5.*self.GUI_RESOLUTION), dpi=self.dpi)
        self.canvas1 = FigCanvas(self.panel, -1, self.fig1)
        self.fig1.text(0.01,0.98,"Arai plot",{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'left' })
        
        self.fig2 = pylab.Figure((2.5*self.GUI_RESOLUTION, 2.5*self.GUI_RESOLUTION), dpi=self.dpi)
        self.canvas2 = FigCanvas(self.panel, -1, self.fig2)
        self.fig2.text(0.02,0.96,"Zijderveld",{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'left' })

        self.fig3 = pylab.Figure((2.5*self.GUI_RESOLUTION, 2.5*self.GUI_RESOLUTION), dpi=self.dpi)
        self.canvas3 = FigCanvas(self.panel, -1, self.fig3)
        #self.fig3.text(0.02,0.96,"Equal area",{'family':'Arial', 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })

        self.fig4 = pylab.Figure((2.5*self.GUI_RESOLUTION, 2.5*self.GUI_RESOLUTION), dpi=self.dpi)
        self.canvas4 = FigCanvas(self.panel, -1, self.fig4)
        if self.acceptance_criteria['average_by_sample_or_site']['value']=='site':
            TEXT="Site data"
        else:
            TEXT="Sample data"            
        self.fig4.text(0.02,0.96,TEXT,{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'left' })

        self.fig5 = pylab.Figure((2.5*self.GUI_RESOLUTION, 2.5*self.GUI_RESOLUTION), dpi=self.dpi)
        self.canvas5 = FigCanvas(self.panel, -1, self.fig5)
        #self.fig5.text(0.02,0.96,"M/M0",{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'left' })

        # make axes of the figures
        self.araiplot = self.fig1.add_axes([0.1,0.1,0.8,0.8])
        self.zijplot = self.fig2.add_subplot(111)
        self.eqplot = self.fig3.add_subplot(111)
        self.sampleplot = self.fig4.add_axes([0.2,0.3,0.7,0.6],frameon=True,axisbg='None')
        self.mplot = self.fig5.add_axes([0.2,0.15,0.7,0.7],frameon=True,axisbg='None')


        #----------------------------------------------------------------------                     
        # text box displaying measurement data
        #----------------------------------------------------------------------                     

        self.logger = wx.TextCtrl(self.panel, id=-1, size=(200*self.GUI_RESOLUTION,500*self.GUI_RESOLUTION), style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
        self.logger.SetFont(font1)
        
        #----------------------------------------------------------------------                     
        # select a specimen box 
        #----------------------------------------------------------------------                     

        box_sizer_select_specimen = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY,"specimen" ), wx.VERTICAL )

        # Combo-box with a list of specimen
        self.specimens_box = wx.ComboBox(self.panel, -1, self.s, (250*self.GUI_RESOLUTION, 25), wx.DefaultSize,self.specimens, wx.CB_DROPDOWN,name="specimen")
        self.specimens_box.SetFont(font2)
        self.Bind(wx.EVT_COMBOBOX, self.onSelect_specimen,self.specimens_box)
        
        # buttons to move forward and backwards from specimens        
        self.nextbutton = wx.Button(self.panel, id=-1, label='next',size=(75*self.GUI_RESOLUTION, 25))#,style=wx.BU_EXACTFIT)#, size=(175, 28))
        self.Bind(wx.EVT_BUTTON, self.on_next_button, self.nextbutton)
        self.nextbutton.SetFont(font2)
        
        self.prevbutton = wx.Button(self.panel, id=-1, label='previous',size=(75*self.GUI_RESOLUTION, 25))#,style=wx.BU_EXACTFIT)#, size=(175, 28))
        self.prevbutton.SetFont(font2)
        self.Bind(wx.EVT_BUTTON, self.on_prev_button, self.prevbutton)
        
        select_specimen_window = wx.GridSizer(1, 2, 0, 10*self.GUI_RESOLUTION)
        select_specimen_window.AddMany( [(self.prevbutton, wx.ALIGN_LEFT),
            (self.nextbutton, wx.ALIGN_LEFT)])

        select_specimen_window_2 = wx.GridSizer(2, 1, 6, 10*self.GUI_RESOLUTION)
        select_specimen_window_2.AddMany( [(self.specimens_box, wx.ALIGN_LEFT),
            (select_specimen_window, wx.ALIGN_LEFT)])

        box_sizer_select_specimen.Add(select_specimen_window_2, 0, wx.TOP, 0 )        

        #----------------------------------------------------------------------                     
        # select temperature bounds
        #----------------------------------------------------------------------                     

        if  self.s in self.Data.keys() and self.Data[self.s]['T_or_MW']=="T": 
            box_sizer_select_temp = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY,"temperatures" ), wx.HORIZONTAL )
        else: 
            box_sizer_select_temp = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY,"MW power" ), wx.HORIZONTAL )

        try:
            if  self.Data[self.s]['T_or_MW']=="T": 
                self.temperatures=scipy.array(self.Data[self.s]['t_Arai'])-273.
                self.T_list=["%.0f"%T for T in self.temperatures]
            elif  self.Data[self.s]['T_or_MW']=="MW":
                self.temperatures=scipy.array(self.Data[self.s]['t_Arai'])
                self.T_list=["%.0f"%T for T in self.temperatures]
        except:
            self.T_list=[]
        
        self.tmin_box = wx.ComboBox(self.panel, -1 ,size=(100*self.GUI_RESOLUTION, 25),choices=self.T_list, style=wx.CB_DROPDOWN)
        self.Bind(wx.EVT_COMBOBOX, self.get_new_T_PI_parameters,self.tmin_box)

        self.tmax_box = wx.ComboBox(self.panel, -1 ,size=(100*self.GUI_RESOLUTION, 25),choices=self.T_list, style=wx.CB_DROPDOWN)
        self.Bind(wx.EVT_COMBOBOX, self.get_new_T_PI_parameters,self.tmax_box)

        select_temp_window = wx.GridSizer(2, 1, 12, 10*self.GUI_RESOLUTION)
        select_temp_window.AddMany( [(self.tmin_box, wx.ALIGN_LEFT),
            (self.tmax_box, wx.ALIGN_LEFT)])
        box_sizer_select_temp.Add(select_temp_window, 0, wx.TOP, 0 )        


        #----------------------------------------------------------------------                     
        # save/delete buttons
        #----------------------------------------------------------------------                     

        box_sizer_save = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY,"" ), wx.HORIZONTAL )

        # save/delete interpretation buttons
        self.save_interpretation_button = wx.Button(self.panel, id=-1, label='save',size=(75*self.GUI_RESOLUTION,25))#,style=wx.BU_EXACTFIT)#, size=(175, 28))
        self.save_interpretation_button.SetFont(font2)
        self.delete_interpretation_button = wx.Button(self.panel, id=-1, label='delete',size=(75*self.GUI_RESOLUTION,25))#,style=wx.BU_EXACTFIT)#, size=(175, 28))
        self.delete_interpretation_button.SetFont(font2)
        self.Bind(wx.EVT_BUTTON, self.on_save_interpretation_button, self.save_interpretation_button)
        self.Bind(wx.EVT_BUTTON, self.on_delete_interpretation_button, self.delete_interpretation_button)
        
        save_delete_window = wx.GridSizer(2, 1, 14, 20*self.GUI_RESOLUTION)
        save_delete_window.AddMany( [(self.save_interpretation_button, wx.ALIGN_LEFT),
            (self.delete_interpretation_button, wx.ALIGN_LEFT)])
        box_sizer_save.Add(save_delete_window, 0, wx.TOP, 0 )        

        #----------------------------------------------------------------------                     
        # specimen interpretation and statistics window (Blab; Banc, Dec, Inc, correction factors etc.)
        #----------------------------------------------------------------------                     
        
        self.Blab_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50*self.GUI_RESOLUTION,25))
        #self.Blab_window.SetFont(font2)
        self.Banc_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50*self.GUI_RESOLUTION,25))
        #self.Banc_window.SetFont(font2)        
        self.Aniso_factor_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50*self.GUI_RESOLUTION,25))
        #self.Aniso_factor_window.SetFont(font2) 
        self.NLT_factor_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50*self.GUI_RESOLUTION,25))
        #self.NLT_factor_window.SetFont(font2) 
        self.CR_factor_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50*self.GUI_RESOLUTION,25))
        #self.CR_factor_window.SetFont(font2) 
        self.declination_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50*self.GUI_RESOLUTION,25))
        #self.declination_window.SetFont(font2) 
        self.inclination_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50*self.GUI_RESOLUTION,25))
        #self.inclination_window.SetFont(font2) 

        self.Blab_label=wx.StaticText(self.panel,label="\nB_lab",style=wx.ALIGN_CENTRE)
        self.Blab_label.SetFont(font2)
        self.Banc_label=wx.StaticText(self.panel,label="\nB_anc",style=wx.ALIGN_CENTRE)
        self.Banc_label.SetFont(font2)
        self.aniso_corr_label=wx.StaticText(self.panel,label="Aniso\ncorr",style=wx.ALIGN_CENTRE)
        self.aniso_corr_label.SetFont(font2)
        self.nlt_corr_label=wx.StaticText(self.panel,label="NLT\ncorr",style=wx.ALIGN_CENTRE)
        self.nlt_corr_label.SetFont(font2)
        self.cr_corr_label=wx.StaticText(self.panel,label="CR\ncorr",style=wx.ALIGN_CENTRE)
        self.cr_corr_label.SetFont(font2)
        self.dec_label=wx.StaticText(self.panel,label="\nDec",style=wx.ALIGN_CENTRE)
        self.dec_label.SetFont(font2)
        self.inc_label=wx.StaticText(self.panel,label="\nInc",style=wx.ALIGN_CENTRE)
        self.inc_label.SetFont(font2)


        specimen_stat_window = wx.GridSizer(2, 7, 0, 20*self.GUI_RESOLUTION)
        box_sizer_specimen = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY,"specimen results"  ), wx.HORIZONTAL )
        specimen_stat_window.AddMany( [(self.Blab_label, wx.EXPAND),
            ((self.Banc_label), wx.EXPAND),
            ((self.aniso_corr_label), wx.EXPAND),
            ((self.nlt_corr_label),wx.EXPAND),
            ((self.cr_corr_label),wx.EXPAND),
            ((self.dec_label),wx.TE_CENTER),
            ((self.inc_label),wx.EXPAND),                          
            (self.Blab_window, wx.EXPAND),
            (self.Banc_window, wx.EXPAND) ,
            (self.Aniso_factor_window, wx.EXPAND) ,
            (self.NLT_factor_window, wx.EXPAND),
            (self.CR_factor_window, wx.EXPAND),
            (self.declination_window, wx.EXPAND) ,
            (self.inclination_window, wx.EXPAND)])
        box_sizer_specimen.Add( specimen_stat_window, 0, wx.ALIGN_LEFT, 0 )


        #----------------------------------------------------------------------                     
        # Sample interpretation window 
        #----------------------------------------------------------------------                     

        for key in ["sample_int_n","sample_int_uT","sample_int_sigma","sample_int_sigma_perc"]:
            command="self.%s_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50*self.GUI_RESOLUTION,25))"%key
            exec command

        sample_mean_label=wx.StaticText(self.panel,label="\nmean",style=wx.TE_CENTER)
        sample_mean_label.SetFont(font2)
        sample_N_label=wx.StaticText(self.panel,label="\nN ",style=wx.TE_CENTER)
        sample_N_label.SetFont(font2)
        sample_std_label=wx.StaticText(self.panel,label="\n std uT",style=wx.TE_CENTER)
        sample_std_label.SetFont(font2)
        sample_std_per_label=wx.StaticText(self.panel,label="\n std %",style=wx.TE_CENTER)
        sample_std_per_label.SetFont(font2)

        
        sample_stat_window = wx.GridSizer(2, 4, 0, 20*self.GUI_RESOLUTION)


        box_sizer_sample = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY,"sample/site results" ), wx.HORIZONTAL )
        sample_stat_window.AddMany( [(sample_mean_label, wx.EXPAND),
            (sample_N_label, wx.EXPAND),
            (sample_std_label, wx.EXPAND),
            (sample_std_per_label ,wx.EXPAND),
            (self.sample_int_uT_window, wx.EXPAND),
            (self.sample_int_n_window, wx.EXPAND) ,
            (self.sample_int_sigma_window, wx.EXPAND) ,
            (self.sample_int_sigma_perc_window, wx.EXPAND)])
        box_sizer_sample.Add(sample_stat_window, 0, wx.ALIGN_LEFT, 0 )        



        hbox_criteria = wx.BoxSizer(wx.HORIZONTAL)
        TEXT=[" ","Acceptance criteria:","Specimen statistics:"]
        for i in range(len(TEXT)):
            command="self.label_%i=wx.StaticText(self.panel,label='%s',style=wx.ALIGN_CENTER,size=(180,25))"%(i,TEXT[i])
            exec command
        gs1 = wx.GridSizer(3, 1,5*self.GUI_RESOLUTION,5*self.GUI_RESOLUTION)
 
        gs1.AddMany( [(self.label_0,wx.EXPAND),(self.label_1,wx.EXPAND),(self.label_2,wx.EXPAND)])
        
        hbox_criteria.Add(gs1,flag=wx.ALIGN_LEFT)

        for statistic in self.preferences['show_statistics_on_gui']:
            command="self.%s_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50*self.GUI_RESOLUTION,25))"%statistic
            exec command
            command="self.%s_window.SetFont(font2)"%statistic
            exec command
            command="self.%s_threshold_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50*self.GUI_RESOLUTION,25))"%statistic
            exec command
            command="self.%s_threshold_window.SetFont(font2)"%statistic
            exec command
            command="self.%s_threshold_window.SetBackgroundColour(wx.NullColour)"%statistic
            exec command
            command="self.%s_label=wx.StaticText(self.panel,label='%s',style=wx.ALIGN_CENTRE)"%(statistic,statistic.replace("specimen_","").replace("int_",""))
            exec command
            command="self.%s_label.SetFont(font2)"%statistic
            exec command
            
        for statistic in self.preferences['show_statistics_on_gui']:
            command="gs_%s = wx.GridSizer(3, 1,5*self.GUI_RESOLUTION,5*self.GUI_RESOLUTION)"%statistic
            exec command
            command="gs_%s.AddMany( [(self.%s_label,wx.EXPAND),(self.%s_threshold_window,wx.EXPAND),(self.%s_window,wx.EXPAND)])"%(statistic,statistic,statistic,statistic)
            exec command
            command="hbox_criteria.Add(gs_%s,flag=wx.ALIGN_LEFT)"%statistic
            exec command
            hbox_criteria.AddSpacer(12)
           

        # ---------------------------  
        # write acceptance criteria to boxes
        # ---------------------------  
                
        self.write_acceptance_criteria_to_boxes()  # write threshold values to boxes

        
        #----------------------------------------------------------------------                     
        # Design the panel
        #----------------------------------------------------------------------

        
        vbox1 = wx.BoxSizer(wx.VERTICAL)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)

    
        vbox1.AddSpacer(10)
        hbox1.AddSpacer(2)

        hbox1.Add(box_sizer_select_specimen,flag=wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
        hbox1.AddSpacer(2)

        hbox1.Add(box_sizer_select_temp, flag=wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
        hbox1.AddSpacer(2)

        hbox1.Add(box_sizer_save, flag=wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
        hbox1.AddSpacer(2)

        hbox1.Add(box_sizer_specimen, flag=wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
        hbox1.AddSpacer(2)
        hbox1.Add(box_sizer_sample, flag=wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
        hbox1.AddSpacer(2)

        vbox1.Add(hbox1, flag=wx.ALIGN_LEFT, border=8)
        self.panel.SetSizer(vbox1)

        vbox2a=wx.BoxSizer(wx.VERTICAL)
        #vbox2a.Add(self.toolbar1,flag=wx.ALIGN_TOP,border=8)
        vbox2a.Add(self.logger,flag=wx.ALIGN_TOP,border=8)
        
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2.Add(vbox2a,flag=wx.ALIGN_CENTER_HORIZONTAL)#,border=8)        
        hbox2.Add(self.canvas1,flag=wx.ALIGN_CENTER_HORIZONTAL)#,border=8)

        vbox2 = wx.BoxSizer(wx.VERTICAL)        
        vbox2.Add(self.canvas2,flag=wx.ALIGN_LEFT)#,border=8)
        vbox2.Add(self.canvas3,flag=wx.ALIGN_LEFT)#,border=8)

        vbox3 = wx.BoxSizer(wx.VERTICAL)        
        vbox3.Add(self.canvas4,flag=wx.ALIGN_LEFT|wx.ALIGN_TOP)#,border=8)
        vbox3.Add(self.canvas5,flag=wx.ALIGN_LEFT|wx.ALIGN_TOP)#,border=8)
        
        hbox2.Add(vbox2,flag=wx.ALIGN_CENTER_HORIZONTAL)#,border=8)
        hbox2.Add(vbox3,flag=wx.ALIGN_CENTER_HORIZONTAL)#,border=8)

        vbox1.Add(hbox2, flag=wx.LEFT, border=8)

        hbox_test = wx.BoxSizer(wx.HORIZONTAL)
    
        vbox1.AddSpacer(5)
        vbox1.Add(hbox_criteria,flag=wx.LEFT)
        vbox1.AddSpacer(20)

        self.panel.SetSizer(vbox1)
        vbox1.Fit(self)

        #----------------------------------------------------------------------                     
        # Draw figures and add  text
        #----------------------------------------------------------------------
        try:
            self.draw_figure(self.s)        # draw the figures
            self.Add_text(self.s)           # write measurement data to text box
        except:
            pass

    #----------------------------------------------------------------------


    def on_save_interpretation_button(self,event):
        """ 
        save the current interpretation temporarily (not to a file)
        """
        if "specimen_int_uT" not in self.Data[self.s]['pars']:
            return
        self.Data[self.s]['pars']['saved']=True

        # collect all interpretation by sample

        sample=self.Data_hierarchy['specimens'][self.s]
        if sample not in self.Data_samples.keys():
            self.Data_samples[sample]={}
        if self.s not in self.Data_samples[sample].keys():
            self.Data_samples[sample][self.s]={}
        self.Data_samples[sample][self.s]['B']=self.Data[self.s]['pars']["specimen_int_uT"]

        # collect all interpretation by site
        
        #site=thellier_gui_lib.get_site_from_hierarchy(sample,self.Data_hierarchy)
        site=thellier_gui_lib.get_site_from_hierarchy(sample,self.Data_hierarchy)
        if site not in self.Data_sites.keys():
            self.Data_sites[site]={}
        if self.s not in self.Data_sites[site].keys():
            self.Data_sites[site][self.s]={}
        self.Data_sites[site][self.s]['B']=self.Data[self.s]['pars']["specimen_int_uT"]
                                
        self.draw_sample_mean()
        self.write_sample_box()
        self.close_warning=True
        

    def on_delete_interpretation_button(self,event):
        """ 
        delete the current interpretation temporarily (not to a file)
        """

        del self.Data[self.s]['pars']
        self.Data[self.s]['pars']={}
        self.Data[self.s]['pars']['lab_dc_field']=self.Data[self.s]['lab_dc_field']
        self.Data[self.s]['pars']['er_specimen_name']=self.Data[self.s]['er_specimen_name']   
        self.Data[self.s]['pars']['er_sample_name']=self.Data[self.s]['er_sample_name']   
        self.Data[self.s]['pars']['er_sample_name']=self.Data[self.s]['er_sample_name']   
        sample=self.Data_hierarchy['specimens'][self.s]
        if sample in self.Data_samples.keys():
            if self.s in self.Data_samples[sample].keys():
                if 'B' in self.Data_samples[sample][self.s].keys():
                    del self.Data_samples[sample][self.s]['B']
                
        site=thellier_gui_lib.get_site_from_hierarchy(sample,self.Data_hierarchy)                
        if site in self.Data_sites.keys():
            if self.s in self.Data_sites[site].keys():
                del self.Data_sites[site][self.s]['B']
                #if 'B' in self.Data_sites[site][self.s].keys():
                #    del self.Data_sites[site][self.s]['B']

        self.tmin_box.SetValue("")
        self.tmax_box.SetValue("")
        self.clear_boxes()
        self.draw_figure(self.s)
        self.draw_sample_mean()
        self.write_sample_box()
        self.close_warning=True

    #----------------------------------------------------------------------
            
        
    def  write_acceptance_criteria_to_boxes(self):
        """ 
        Update paleointensity statistics in acceptance criteria boxes.
        (after changing temperature bounds or changing specimen)
        """

        self.ignore_parameters={}
        for crit_short_name in self.preferences['show_statistics_on_gui']:
            crit="specimen_"+crit_short_name
            if self.acceptance_criteria[crit]['value']==-999:
                command="self.%s_threshold_window.SetValue(\"\")"%crit_short_name
                exec command
                command="self.%s_threshold_window.SetBackgroundColour(wx.Colour(128, 128, 128))"%crit_short_name
                exec command
                self.ignore_parameters[crit]=True
                continue
            elif crit=="specimen_scat":
                if self.acceptance_criteria[crit]['value'] in ['g',1,'1',True,"True"]:
                    value="True"
                    #self.scat_threshold_window.SetBackgroundColour(wx.Colour(128, 128, 128))
                else:
                    value=""
                    self.scat_threshold_window.SetBackgroundColour(wx.Colour(128, 128, 128))
                   
            elif type(self.acceptance_criteria[crit]['value'])==int:
                value="%i"%self.acceptance_criteria[crit]['value']
            elif type(self.acceptance_criteria[crit]['value'])==float:
                if self.acceptance_criteria[crit]['decimal_points']==-999:
                    value="%.3e"%self.acceptance_criteria[crit]['value']
                else:
                    command="value='%%.%if'%%self.acceptance_criteria[crit]['value']"%(self.acceptance_criteria[crit]['decimal_points'])
                    exec command
            else:
                continue
                    
            command="self.%s_threshold_window.SetValue('%s')"%(crit_short_name,value)
            exec command
            command="self.%s_threshold_window.SetBackgroundColour(wx.WHITE)"%crit_short_name
            exec command
                
                    
    #----------------------------------------------------------------------
    

    def Add_text(self,s):
      """ 
      Add text to measurement data window.
      """

      self.logger.Clear()
      FONT_RATIO=self.GUI_RESOLUTION+(self.GUI_RESOLUTION-1)*5
      if self.GUI_RESOLUTION >1.1:
          font1 = wx.Font(11, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Arial')
      elif self.GUI_RESOLUTION <=0.9:
          font1 = wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Arial')
      else:   
          font1 = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Arial')
          
      #String="Step | Temp |  Dec  |  Inc  | M [Am^2]\n"
      String="  Step\tTemp\t Dec\t Inc\tM [Am^2]\n"
      # microwave
      if "LP-PI-M" in self.Data[self.s]['datablock'][0]['magic_method_codes']:
          MICROWAVE=True; THERMAL=False
          String="  Step\tNumber\t Dec\t Inc\tMoment\n"
      else:
          MICROWAVE=False; THERMAL=True

      self.logger.AppendText(String)

      self.logger.SetFont(font1)
      TEXT=""
      for rec in self.Data[self.s]['datablock']:
          #print rec.keys()
          if "LT-NO" in rec['magic_method_codes']:
              step="N"
          elif "LT-AF-Z" in rec['magic_method_codes']:
              step="AFD"
          elif "LT-T-Z" in rec['magic_method_codes'] or 'LT-M-Z' in rec['magic_method_codes']:
              step="Z"
          elif "LT-T-I" in rec['magic_method_codes'] or 'LT-M-I' in rec['magic_method_codes']:
              step="I"
          elif "LT-PTRM-I" in rec['magic_method_codes'] or "LT-PMRM-I" in rec['magic_method_codes']:
              step="P"
          elif "LT-PTRM-MD" in rec['magic_method_codes'] or "LT-PMRM-MD" in rec['magic_method_codes']:
              step="T"
          elif "LT-PTRM-AC" in rec['magic_method_codes'] or "LT-PMRM-AC" in rec['magic_method_codes']:
              step="A"
          else:
              print "unrecognized step in specimen",self.s,"  Method codes: ", rec['magic_method_codes'] 
          if THERMAL:
               TEXT=TEXT+"   %s\t%3.0f\t%5.1f\t%5.1f\t%.2e\n"%(step,float(rec['treatment_temp'])-273.,float(rec['measurement_dec']),float(rec['measurement_inc']),float(rec['measurement_magn_moment']))

#              TEXT=TEXT+"  %s      %3.0f      %5.1f    %5.1f   %.2e\n"%(step,float(rec['treatment_temp'])-273.,float(rec['measurement_dec']),float(rec['measurement_inc']),float(rec['measurement_magn_moment']))
          elif MICROWAVE: # mcrowave
                if "measurement_description" in rec.keys():
                    MW_step=rec["measurement_description"].strip('\n').split(":")
                    for STEP in MW_step:
                        if "Number" in STEP:
                            temp=float(STEP.split("-")[-1])
              
                            TEXT=TEXT+"   %s\t%1.0f\t%5.1f\t%5.1f\t%.2e\n"%(step,temp,float(rec['measurement_dec']),float(rec['measurement_inc']),float(rec['measurement_magn_moment']))
              
      self.logger.AppendText( TEXT)
      
    #----------------------------------------------------------------------
        
    def create_menu(self):
        """ 
        Create menu bar
        """
        self.menubar = wx.MenuBar()


        menu_preferences = wx.Menu()
        
        m_preferences_apperance = menu_preferences.Append(-1, "&Appearence preferences", "")
        self.Bind(wx.EVT_MENU, self.on_menu_appearance_preferences, m_preferences_apperance)

        m_preferences_spd = menu_preferences.Append(-1, "&Specimen paleointensity statistics (from SPD list)", "")
        self.Bind(wx.EVT_MENU, self.on_menu_m_preferences_spd, m_preferences_spd)

        #m_preferences_stat = menu_preferences.Append(-1, "&Statistical preferences", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_preferences_stat, m_preferences_stat)


        #m_save_preferences = menu_preferences.Append(-1, "&Save preferences", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_save_preferences, m_save_preferences)
        
        menu_file = wx.Menu()
        
        m_change_working_directory = menu_file.Append(-1, "&Change project directory", "")
        self.Bind(wx.EVT_MENU, self.on_menu_change_working_directory, m_change_working_directory)

        #m_add_working_directory = menu_file.Append(-1, "&Add a MagIC project directory", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_add_working_directory, m_add_working_directory)

        m_open_magic_file = menu_file.Append(-1, "&Open MagIC measurement file", "")
        self.Bind(wx.EVT_MENU, self.on_menu_open_magic_file, m_open_magic_file)

        m_open_magic_tree = menu_file.Append(-1, "&Open all MagIC project directories in path", "")
        self.Bind(wx.EVT_MENU, self.on_menu_m_open_magic_tree, m_open_magic_tree)

        menu_file.AppendSeparator()

        m_prepare_MagIC_results_tables= menu_file.Append(-1, "&Save MagIC pmag tables", "")
        self.Bind(wx.EVT_MENU, self.on_menu__prepare_MagIC_results_tables, m_prepare_MagIC_results_tables)

        submenu_save_plots = wx.Menu()

        m_save_Arai_plot = submenu_save_plots.Append(-1, "&Save Arai plot", "")
        self.Bind(wx.EVT_MENU, self.on_save_Arai_plot, m_save_Arai_plot)

        m_save_zij_plot = submenu_save_plots.Append(-1, "&Save Zijderveld plot", "")
        self.Bind(wx.EVT_MENU, self.on_save_Zij_plot, m_save_zij_plot,"Zij")

        m_save_eq_plot = submenu_save_plots.Append(-1, "&Save equal area plot", "")
        self.Bind(wx.EVT_MENU, self.on_save_Eq_plot, m_save_eq_plot,"Eq")

        m_save_M_t_plot = submenu_save_plots.Append(-1, "&Save M-t plot", "")
        self.Bind(wx.EVT_MENU, self.on_save_M_t_plot, m_save_M_t_plot,"M_t")

        m_save_NLT_plot = submenu_save_plots.Append(-1, "&Save NLT plot", "")
        self.Bind(wx.EVT_MENU, self.on_save_NLT_plot, m_save_NLT_plot,"NLT")

        m_save_CR_plot = submenu_save_plots.Append(-1, "&Save cooling rate plot", "")
        self.Bind(wx.EVT_MENU, self.on_save_CR_plot, m_save_CR_plot,"CR")

        m_save_sample_plot = submenu_save_plots.Append(-1, "&Save sample plot", "")
        self.Bind(wx.EVT_MENU, self.on_save_sample_plot, m_save_sample_plot,"Samp")

        #m_save_all_plots = submenu_save_plots.Append(-1, "&Save all plots", "")
        #self.Bind(wx.EVT_MENU, self.on_save_all_plots, m_save_all_plots)

        menu_file.AppendSeparator()

        m_new_sub_plots = menu_file.AppendMenu(-1, "&Save plot", submenu_save_plots)

        
        menu_file.AppendSeparator()
        m_exit = menu_file.Append(wx.ID_EXIT, "Quit", "Quit application")
        self.Bind(wx.EVT_MENU, self.on_menu_exit, m_exit)


        menu_anistropy = wx.Menu()
        
        m_calculate_aniso_tensor = menu_anistropy.Append(-1, "&Calculate anistropy tensors", "")
        self.Bind(wx.EVT_MENU, self.on_menu_calculate_aniso_tensor, m_calculate_aniso_tensor)

        m_show_anisotropy_errors = menu_anistropy.Append(-1, "&Show anisotropy calculation Warnings/Errors", "")
        self.Bind(wx.EVT_MENU, self.on_show_anisotropy_errors, m_show_anisotropy_errors)


        menu_Analysis = wx.Menu()


        submenu_criteria = wx.Menu()

       # m_set_criteria_to_default = submenu_criteria.Append(-1, "&Set acceptance criteria to default", "")
       # self.Bind(wx.EVT_MENU, self.on_menu_default_criteria, m_set_criteria_to_default)

        m_change_criteria_file = submenu_criteria.Append(-1, "&Change acceptance criteria", "")
        self.Bind(wx.EVT_MENU, self.on_menu_criteria, m_change_criteria_file)

        m_import_criteria_file =  submenu_criteria.Append(-1, "&Import criteria file", "")
        self.Bind(wx.EVT_MENU, self.on_menu_criteria_file, m_import_criteria_file)

        
        m_new_sub = menu_Analysis.AppendMenu(-1, "Acceptance criteria", submenu_criteria)


        m_previous_interpretation = menu_Analysis.Append(-1, "&Import previous interpretation from a 'redo' file", "")
        self.Bind(wx.EVT_MENU, self.on_menu_previous_interpretation, m_previous_interpretation)

        m_save_interpretation = menu_Analysis.Append(-1, "&Save current interpretations to a 'redo' file", "")
        self.Bind(wx.EVT_MENU, self.on_menu_save_interpretation, m_save_interpretation)

        m_delete_interpretation = menu_Analysis.Append(-1, "&Clear all current interpretations", "")
        self.Bind(wx.EVT_MENU, self.on_menu_clear_interpretation, m_delete_interpretation)


        menu_Tools = wx.Menu()
        #m_prev_interpretation = menu_file.Append(-1, "&Save plot\tCtrl-S", "Save plot to file")

        menu_Auto_Interpreter = wx.Menu()
        
        m_interpreter = menu_Auto_Interpreter.Append(-1, "&Run Thellier auto interpreter", "Run auto interpter")
        self.Bind(wx.EVT_MENU, self.on_menu_run_interpreter, m_interpreter)

        m_open_interpreter_file = menu_Auto_Interpreter.Append(-1, "&Open auto-interpreter output files", "")
        self.Bind(wx.EVT_MENU, self.on_menu_open_interpreter_file, m_open_interpreter_file)

        m_open_interpreter_log = menu_Auto_Interpreter.Append(-1, "&Open auto-interpreter Warnings/Errors", "")
        self.Bind(wx.EVT_MENU, self.on_menu_open_interpreter_log, m_open_interpreter_log)


        menu_consistency_test = wx.Menu()
        m_run_consistency_test = menu_consistency_test.Append(-1, "&Run Consistency test", "")
        self.Bind(wx.EVT_MENU, self.on_menu_run_consistency_test, m_run_consistency_test)

        #m_run_consistency_test_b = menu_Optimizer.Append(-1, "&Run Consistency test beta version", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_run_consistency_test_b, m_run_consistency_test_b)

        menu_Plot= wx.Menu()
        m_plot_data = menu_Plot.Append(-1, "&Plot paleointensity curve", "")
        self.Bind(wx.EVT_MENU, self.on_menu_plot_data, m_plot_data)

        #menu_results_table= wx.Menu()
        #m_make_results_table = menu_results_table.Append(-1, "&Make results table", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_results_data, m_make_results_table)


        #menu_MagIC= wx.Menu()
        #m_convert_to_magic= menu_MagIC.Append(-1, "&Convert generic files to MagIC format", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_convert_to_magic, m_convert_to_magic)
        #m_build_magic_model= menu_MagIC.Append(-1, "&Run MagIC model builder", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_MagIC_model_builder, m_build_magic_model)
        #m_prepare_MagIC_results_tables= menu_MagIC.Append(-1, "&Make MagIC results Table", "")
        #self.Bind(wx.EVT_MENU, self.on_menu__prepare_MagIC_results_tables, m_prepare_MagIC_results_tables)


        
        #menu_help = wx.Menu()
        #m_about = menu_help.Append(-1, "&About\tF1", "About this program")
        self.menubar.Append(menu_preferences, "& Preferences") 
        self.menubar.Append(menu_file, "&File")
        self.menubar.Append(menu_anistropy, "&Anistropy")
        self.menubar.Append(menu_Analysis, "&Analysis")
        self.menubar.Append(menu_Auto_Interpreter, "&Auto Interpreter")
        self.menubar.Append(menu_consistency_test, "&Consistency Test")
        self.menubar.Append(menu_Plot, "&Plot")
        #self.menubar.Append(menu_results_table, "&Table")
        #self.menubar.Append(menu_MagIC, "&MagIC")
        
        self.SetMenuBar(self.menubar)


    #----------------------------------------------------------------------

    def update_selection(self):
        """ 
        update figures and statistics windows with a new selection of specimen
        """

        # clear all boxes
        self.clear_boxes()
        self.Add_text(self.s)
        self.draw_figure(self.s)
        
        # update temperature list
        if self.Data[self.s]['T_or_MW']=="T":
            self.temperatures=scipy.array(self.Data[self.s]['t_Arai'])-273.
        else:
            self.temperatures=scipy.array(self.Data[self.s]['t_Arai'])
            
        self.T_list=["%.0f"%T for T in self.temperatures]
        self.tmin_box.SetItems(self.T_list)
        self.tmax_box.SetItems(self.T_list)
        self.tmin_box.SetValue("")
        self.tmax_box.SetValue("")
        self.Blab_window.SetValue("%.0f"%(float(self.Data[self.s]['pars']['lab_dc_field'])*1e6))
        if "saved" in self.Data[self.s]['pars']:
            self.pars=self.Data[self.s]['pars']
            self.update_GUI_with_new_interpretation()
        self.write_sample_box()
        

    #----------------------------------------------------------------------
      
    def onSelect_specimen(self, event):
        """ 
        update figures and text when a new specimen is selected
        """        
        self.s=self.specimens_box.GetStringSelection()
        self.update_selection()

    #----------------------------------------------------------------------

    def on_next_button(self,event):
      """ 
      update figures and text when a next button is selected
      """
      if 'saved' not in self.Data[self.s]['pars'] or self.Data[self.s]['pars']['saved']!= True:
            del self.Data[self.s]['pars']
            self.Data[self.s]['pars']={}
            self.Data[self.s]['pars']['lab_dc_field']=self.Data[self.s]['lab_dc_field']
            self.Data[self.s]['pars']['er_specimen_name']=self.Data[self.s]['er_specimen_name']   
            self.Data[self.s]['pars']['er_sample_name']=self.Data[self.s]['er_sample_name']
            # return to last saved interpretation if exist
            if 'er_specimen_name' in self.last_saved_pars.keys() and self.last_saved_pars['er_specimen_name']==self.s:
                for key in self.last_saved_pars.keys():
                    self.Data[self.s]['pars'][key]=self.last_saved_pars[key]
                self.last_saved_pars={}
              
      index=self.specimens.index(self.s)
      if index==len(self.specimens)-1:
        index=0
      else:
        index+=1
      self.s=self.specimens[index]
      self.specimens_box.SetStringSelection(self.s)
      self.update_selection()

    #----------------------------------------------------------------------

    def on_prev_button(self,event):
      """ 
      update figures and text when a previous button is selected
      """
      if 'saved' not in self.Data[self.s]['pars'] or self.Data[self.s]['pars']['saved']!= True:
            del self.Data[self.s]['pars']
            self.Data[self.s]['pars']={}
            self.Data[self.s]['pars']['lab_dc_field']=self.Data[self.s]['lab_dc_field']
            self.Data[self.s]['pars']['er_specimen_name']=self.Data[self.s]['er_specimen_name']   
            self.Data[self.s]['pars']['er_sample_name']=self.Data[self.s]['er_sample_name']
            # return to last saved interpretation if exist
            if 'er_specimen_name' in self.last_saved_pars.keys() and self.last_saved_pars['er_specimen_name']==self.s:
                for key in self.last_saved_pars.keys():
                    self.Data[self.s]['pars'][key]=self.last_saved_pars[key]
                self.last_saved_pars={}
                
                
      index=self.specimens.index(self.s)
      if index==0: index=len(self.specimens)
      index-=1
      self.s=self.specimens[index]
      self.specimens_box.SetStringSelection(self.s)
      self.update_selection()

    #----------------------------------------------------------------------


    #----------------------------------------------------------------------

    def clear_boxes(self):
        """ 
        Clear all boxes
        """        
        self.tmin_box.Clear()
        self.tmin_box.SetItems(self.T_list)
        self.tmin_box.SetSelection(-1)

        self.tmax_box.Clear()
        self.tmax_box.SetItems(self.T_list)
        self.tmax_box.SetSelection(-1)

        self.Blab_window.SetValue("")     
        self.Banc_window.SetValue("")
        self.Banc_window.SetBackgroundColour(wx.NullColour)
        self.Aniso_factor_window.SetValue("")
        self.Aniso_factor_window.SetBackgroundColour(wx.NullColour)    
        self.NLT_factor_window.SetValue("")
        self.NLT_factor_window.SetBackgroundColour(wx.NullColour)    
        self.CR_factor_window.SetValue("")
        self.CR_factor_window.SetBackgroundColour(wx.NullColour)    
        self.declination_window.SetValue("")
        self.declination_window.SetBackgroundColour(wx.NullColour)
        self.inclination_window.SetValue("")
        self.inclination_window.SetBackgroundColour(wx.NullColour)

        window_list=['sample_int_n','sample_int_uT','sample_int_sigma','sample_int_sigma_perc']
        for key in window_list:
            command="self.%s_window.SetValue(\"\")"%key
            exec command
            command="self.%s_window.SetBackgroundColour(wx.NullColour)"%key
            exec command
                                         
        #window_list=['int_n','int_ptrm_n','frac','scat','gmax','f','fvds','b_beta','g','q','int_mad','int_dang','drats','md','ptrms_dec','ptrms_inc','ptrms_mad','ptrms_angle']
        #for key in window_list:
        for key in self.preferences['show_statistics_on_gui']:
            command="self.%s_window.SetValue(\"\")"%key
            exec command
            command="self.%s_window.SetBackgroundColour(wx.NullColour)"%key
            exec command
            
    def write_sample_box(self):
        """ 
        """        

        B=[]
        
        if self.acceptance_criteria['average_by_sample_or_site']['value']=='sample':
            sample=self.Data_hierarchy['specimens'][self.s]
            if sample in self.Data_samples.keys() and len(self.Data_samples[sample].keys())>0:
                if self.s not in self.Data_samples[sample].keys():
                    if 'specimen_int_uT' in self.pars.keys():
                        B.append(self.pars['specimen_int_uT'])
                for specimen in self.Data_samples[sample].keys():
                    if specimen==self.s:
                        if 'specimen_int_uT' in self.pars.keys():
                            B.append(self.pars['specimen_int_uT'])
                    else:
                        if specimen in self.Data_samples[sample].keys() and 'B' in self.Data_samples[sample][specimen].keys():
                            B.append(self.Data_samples[sample][specimen]['B'])
            else:
                if 'specimen_int_uT' in self.pars.keys():
                    B.append(self.pars['specimen_int_uT'])


        # if averaging by site
        else:
            
            sample=self.Data_hierarchy['specimens'][self.s]
            site=thellier_gui_lib.get_site_from_hierarchy(sample,self.Data_hierarchy)
            if site in self.Data_sites.keys() and len(self.Data_sites[site].keys())>0:
                if self.s not in self.Data_sites[site].keys():
                    if 'specimen_int_uT' in self.pars.keys():
                        B.append(self.pars['specimen_int_uT'])
                for specimen in self.Data_sites[site].keys():
                    if specimen==self.s:
                        if 'specimen_int_uT' in self.pars.keys():
                            B.append(self.pars['specimen_int_uT'])
                    else:
                        if specimen in self.Data_sites[site].keys() and 'B' in self.Data_sites[site][specimen].keys():
                            B.append(self.Data_sites[site][specimen]['B'])
            else:
                if 'specimen_int_uT' in self.pars.keys():
                    B.append(self.pars['specimen_int_uT'])
                           
                                                
        if B==[]:
            self.sample_int_n_window.SetValue("")
            self.sample_int_uT_window.SetValue("")
            self.sample_int_sigma_window.SetValue("")
            self.sample_int_sigma_perc_window.SetValue("")
            self.sample_int_uT_window.SetBackgroundColour(wx.NullColour)
            self.sample_int_n_window.SetBackgroundColour(wx.NullColour)
            self.sample_int_sigma_window.SetBackgroundColour(wx.NullColour)
            self.sample_int_sigma_perc_window.SetBackgroundColour(wx.NullColour)

            
            return()

        #print "B is this:", B # shows that the problem happens when B array contains 1 or 2
        N=len(B)
        B_mean=scipy.mean(B)
        B_std=scipy.std(B,ddof=1)
        B_std_perc=100*(B_std/B_mean)
        
        self.sample_int_n_window.SetValue("%i"%(N))
        self.sample_int_uT_window.SetValue("%.1f"%(B_mean))
        self.sample_int_sigma_window.SetValue("%.1f"%(B_std))
        self.sample_int_sigma_perc_window.SetValue("%.1f"%(B_std_perc))
        self.sample_int_n_window.SetBackgroundColour(wx.NullColour)
        self.sample_int_sigma_window.SetBackgroundColour(wx.NullColour)
        self.sample_int_sigma_perc_window.SetBackgroundColour(wx.NullColour)

        fail_flag=False
        fail_int_n=False
        fail_int_sigma=False
        fail_int_sigma_perc=False
        sample_failed=False
        
        if self.acceptance_criteria['sample_int_n']['value'] != -999:
            if N<self.acceptance_criteria['sample_int_n']['value']:
                fail_int_n=True
                sample_failed=True
                self.sample_int_n_window.SetBackgroundColour(wx.RED)
            else:
                self.sample_int_n_window.SetBackgroundColour(wx.GREEN)
        else:
            self.sample_int_n_window.SetBackgroundColour(wx.NullColour)
                   
        
        if self.acceptance_criteria['sample_int_sigma']['value'] != -999:
            if  B_std*1.e-6 > self.acceptance_criteria['sample_int_sigma']['value']:
                fail_int_sigma=True 
                self.sample_int_sigma_window.SetBackgroundColour(wx.RED)
            else:
                self.sample_int_sigma_window.SetBackgroundColour(wx.GREEN)
        else:
            self.sample_int_sigma_window.SetBackgroundColour(wx.NullColour)
 
        if self.acceptance_criteria['sample_int_sigma_perc']['value'] != -999:
            if  B_std_perc > self.acceptance_criteria['sample_int_sigma_perc']:
                fail_int_sigma_perc=True 
                self.sample_int_sigma_perc_window.SetBackgroundColour(wx.RED)
            else:
                self.sample_int_sigma_perc_window.SetBackgroundColour(wx.GREEN)
        else:
            self.sample_int_sigma_perc_window.SetBackgroundColour(wx.NullColour)

                          
        if self.acceptance_criteria['sample_int_sigma']['value']==-999 and fail_int_sigma_perc:
            sample_failed=True
        elif self.acceptance_criteria['sample_int_sigma_perc']['value']==-999 and fail_int_sigma:
            sample_failed=True
        elif self.acceptance_criteria['sample_int_sigma']['value'] !=-999 and self.acceptance_criteria['sample_int_sigma_perc']['value']!=-999:
            if fail_int_sigma and fail_int_sigma_perc:
                sample_failed=True        
        
        if sample_failed:
            self.sample_int_uT_window.SetBackgroundColour(wx.RED) 
        else:
            self.sample_int_uT_window.SetBackgroundColour(wx.GREEN)
            
            #if self.acceptance_criteria['sample_int_sigma']['value'] != -999  or self.acceptance_criteria['sample_int_sigma_perc']['value'] != -999:
            #    if   fail_int_sigma and fail_int_sigma_perc:
            #       self.sample_int_uT_window.SetBackgroundColour(wx.RED) 
            #else:
            #    self.sample_int_uT_window.SetBackgroundColour(wx.GREEN)
                    

        
        #else:
        #    self.sample_int_uT_window.SetBackgroundColour(wx.GREEN)
        #    


    #----------------------------------------------------------------------
    # manu bar options:
    #----------------------------------------------------------------------

    def on_menu_appearance_preferences(self,event):
        class preferences_appearance_dialog(wx.Dialog):
            
            def __init__(self, parent,title,preferences):
                self.preferences=preferences
                super(preferences_appearance_dialog, self).__init__(parent, title=title)
                self.InitUI()

            def InitUI(self):


                pnl1 = wx.Panel(self)

                vbox = wx.BoxSizer(wx.VERTICAL)

                #-----------box1       
                bSizer1 = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "Gui appearance" ), wx.HORIZONTAL )
                self.gui_resolution=wx.TextCtrl(pnl1,style=wx.TE_CENTER,size=(50,20))
                                             
                appearance_window = wx.GridSizer(1, 2, 12, 12)
                appearance_window.AddMany( [(wx.StaticText(pnl1,label="GUI resolution (100% is default size)",style=wx.TE_CENTER), wx.EXPAND),
                    (self.gui_resolution, wx.EXPAND)])
                bSizer1.Add( appearance_window, 0, wx.ALIGN_LEFT|wx.ALL, 5 )

                #-----------box2        

                bSizer2 = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "Arai plot" ), wx.HORIZONTAL )
                self.show_Arai_temperatures=wx.CheckBox(pnl1, -1, '', (50, 50))        
                #self.show_Arai_temperatures_steps=FS.FloatSpin(pnl1, -1, min_val=1, max_val=9,increment=1, value=1, extrastyle=FS.FS_LEFT,size=(50,20))
                #self.show_Arai_temperatures_steps.SetFormat("%f")
                #self.show_Arai_temperatures_steps.SetDigits(0)
                self.show_Arai_temperatures_steps=wx.SpinCtrl(pnl1, -1, '1', (50, 20), (60, -1), min=1, max=9)

                self.show_Arai_pTRM_arrows=wx.CheckBox(pnl1, -1, '', (50, 50))        
                                             
                arai_window = wx.GridSizer(2, 3, 12, 12)
                arai_window.AddMany( [(wx.StaticText(pnl1,label="show temperatures",style=wx.TE_CENTER), wx.EXPAND),
                    (wx.StaticText(pnl1,label="show temperatures but skip steps",style=wx.TE_CENTER), wx.EXPAND),
                    (wx.StaticText(pnl1,label="show pTRM-checks arrows",style=wx.TE_CENTER), wx.EXPAND),                  
                    (self.show_Arai_temperatures, wx.EXPAND),
                    (self.show_Arai_temperatures_steps, wx.EXPAND),                                      
                    (self.show_Arai_pTRM_arrows, wx.EXPAND)])                 
                bSizer2.Add( arai_window, 0, wx.ALIGN_LEFT|wx.ALL, 5 )

                #-----------box3        

                bSizer3 = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "Zijderveld plot" ), wx.HORIZONTAL )
                self.show_Zij_temperatures=wx.CheckBox(pnl1, -1, '', (50, 50))        
                #self.show_Zij_temperatures_steps=FS.FloatSpin(pnl1, -1, min_val=1, max_val=9,increment=1, value=1, extrastyle=FS.FS_LEFT,size=(50,20))
                #self.show_Zij_temperatures_steps.SetFormat("%f")
                #self.show_Zij_temperatures_steps.SetDigits(0)
                self.show_Zij_temperatures_steps=wx.SpinCtrl(pnl1, -1, '1', (50, 20), (60, -1), min=1, max=9)
                                             
                zij_window = wx.GridSizer(2, 2, 12, 12)
                zij_window.AddMany( [(wx.StaticText(pnl1,label="show temperatures",style=wx.TE_CENTER), wx.EXPAND),
                    (wx.StaticText(pnl1,label="show temperatures but skip stpes",style=wx.TE_CENTER), wx.EXPAND),
                    (self.show_Zij_temperatures, wx.EXPAND),               
                    (self.show_Zij_temperatures_steps, wx.EXPAND)])                 
                bSizer3.Add( zij_window, 0, wx.ALIGN_LEFT|wx.ALL, 5 )

                #-----------box4        

                bSizer4 = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "Equal area plot" ), wx.HORIZONTAL )
                self.show_eqarea_temperatures=wx.CheckBox(pnl1, -1, '', (50, 50))        
                self.show_eqarea_pTRMs=wx.CheckBox(pnl1, -1, '', (50, 50))        
                self.show_eqarea_IZZI_colors=wx.CheckBox(pnl1, -1, '', (50, 50))        
                                             
                eqarea_window = wx.GridSizer(2, 3, 12, 12)
                eqarea_window.AddMany( [(wx.StaticText(pnl1,label="show temperatures",style=wx.TE_CENTER), wx.EXPAND),
                    (wx.StaticText(pnl1,label="show pTRMs directions",style=wx.TE_CENTER), wx.EXPAND),                  
                    (wx.StaticText(pnl1,label="show IZ and ZI in different colors",style=wx.TE_CENTER), wx.EXPAND),                  
                    (self.show_eqarea_temperatures, wx.EXPAND),
                    (self.show_eqarea_pTRMs, wx.EXPAND),
                    (self.show_eqarea_IZZI_colors, wx.EXPAND)])                 
                
                bSizer4.Add( eqarea_window, 0, wx.ALIGN_LEFT|wx.ALL, 5 )

                #-----------box5        

                bSizer5 = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "plots" ), wx.HORIZONTAL )
                self.show_NLT_plot=wx.CheckBox(pnl1, -1, '', (50, 50))        
                self.show_CR_plot=wx.CheckBox(pnl1, -1, '', (50, 50))        
                                             
                NLT_window = wx.GridSizer(2, 2, 12, 12)
                NLT_window.AddMany( [(wx.StaticText(pnl1,label="show Non-linear TRM plot instead of M/T plot",style=wx.TE_CENTER), wx.EXPAND),
                    (self.show_NLT_plot, wx.EXPAND),                
                    (wx.StaticText(pnl1,label="show cooling rate plot instead of equal area plot",style=wx.TE_CENTER), wx.EXPAND),                
                    (self.show_CR_plot, wx.EXPAND)])                 
                bSizer5.Add( NLT_window, 0, wx.ALIGN_LEFT|wx.ALL, 5 )

##                #-----------box6        
##
##                bSizer6 = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "Statistical definitions" ), wx.HORIZONTAL )
##                self.bootstrap_N=wx.TextCtrl(pnl1,style=wx.TE_CENTER,size=(80,20))
##                #self.bootstrap_N=FS.FloatSpin(pnl1, -1, min_val=1000, max_val=10000000,increment=1000, value=10000, extrastyle=FS.FS_LEFT,size=(80,20))
##                #self.bootstrap_N.SetFormat("%f")
##                #self.bootstrap_N.SetDigits(0)
##                                             
##                Statistics_definitions_window = wx.GridSizer(1, 2, 12, 12)
##                Statistics_definitions_window.AddMany( [(wx.StaticText(pnl1,label="Bootstrap N",style=wx.TE_CENTER), wx.EXPAND),
##                    (self.bootstrap_N, wx.EXPAND)])                 
##                bSizer6.Add( Statistics_definitions_window, 0, wx.ALIGN_LEFT|wx.ALL, 5 )
                         
                #----------------------

                hbox2 = wx.BoxSizer(wx.HORIZONTAL)
                self.okButton = wx.Button(pnl1, wx.ID_OK, "&OK")
                self.cancelButton = wx.Button(pnl1, wx.ID_CANCEL, '&Cancel')
                hbox2.Add(self.okButton)
                hbox2.Add(self.cancelButton )
                                    
                                    
                #----------------------  
                vbox.AddSpacer(20)
                vbox.Add(bSizer1, flag=wx.ALIGN_CENTER_HORIZONTAL)
                vbox.AddSpacer(20)
                vbox.Add(bSizer2, flag=wx.ALIGN_CENTER_HORIZONTAL)
                vbox.AddSpacer(20)
                vbox.Add(bSizer3, flag=wx.ALIGN_CENTER_HORIZONTAL)
                vbox.AddSpacer(20)
                vbox.Add(bSizer4, flag=wx.ALIGN_CENTER_HORIZONTAL)
                vbox.AddSpacer(20)
                vbox.Add(bSizer5, flag=wx.ALIGN_CENTER_HORIZONTAL)
                vbox.AddSpacer(20)
##                vbox.Add(bSizer6, flag=wx.ALIGN_CENTER_HORIZONTAL)
##                vbox.AddSpacer(20)

                vbox.Add(hbox2, flag=wx.ALIGN_CENTER_HORIZONTAL)
                vbox.AddSpacer(20)
                            
                pnl1.SetSizer(vbox)
                vbox.Fit(self)

                #---------------------- Initialize  values:

                #set default:
                try:
                    self.gui_resolution.SetValue("%.0f"%self.preferences["gui_resolution"])                    
                except:
                    self.gui_resolution.SetValue("100")
                try:
                    self.show_Arai_temperatures.SetValue(self.preferences["show_Arai_temperatures"])
                except:
                    self.show_Arai_temperatures.SetValue(True)
                try:
                    self.show_Arai_temperatures_steps.SetValue(self.preferences["show_Arai_temperatures_steps"])
                except:
                    self.show_Arai_temperatures_steps.SetValue(1.)

                try: 
                    self.show_Arai_pTRM_arrows.SetValue(self.preferences["show_Arai_pTRM_arrows"])
                except:
                    self.show_Arai_pTRM_arrows.SetValue(False)
                try:  
                    self.show_Zij_temperatures.SetValue(self.preferences["show_Zij_temperatures"])
                except:
                    self.show_Zij_temperatures.SetValue(True)
                try:  
                    self.show_Zij_temperatures_steps.SetValue(self.preferences["show_Zij_temperatures_steps"])
                except:
                    self.show_Zij_temperatures_steps.SetValue(1.)
                try:
                    self.show_eqarea_temperatures.SetValue(self.preferences["show_eqarea_temperatures"])
                except:
                    self.show_eqarea_temperatures.SetValue(False)
                try:                    
                    self.show_eqarea_pTRMs.SetValue(self.preferences["show_eqarea_pTRMs"])
                except:
                    self.show_eqarea_pTRMs.SetValue(False)
                try:                    
                    self.show_eqarea_IZZI_colors.SetValue(self.preferences["show_eqarea_IZZI_colors"])
                except:
                    self.show_eqarea_IZZI_colors.SetValue(False)
                try:                    
                    self.show_NLT_plot.SetValue(self.preferences["show_NLT_plot"])
                except:
                    self.show_NLT_plot.SetValue(False)
                try:                    
                    self.show_CR_plot.SetValue(self.preferences["show_CR_plot"])
                except:
                    self.show_CR_plot.SetValue(False)

##                try:                    
##                    self.bootstrap_N.SetValue("%.0f"%(self.preferences["BOOTSTRAP_N"]))
##                except:
##                    self.bootstrap_N.SetValue("10000")
                    
                #----------------------
                    
        dia = preferences_appearance_dialog(None,"Thellier_gui appearance preferences",self.preferences)
        dia.Center()
        if dia.ShowModal() == wx.ID_OK: # Until the user clicks OK, show the message
            #try:
            change_resolution=False
            if float(dia.gui_resolution.GetValue()) != self.preferences['gui_resolution']:
                     change_resolution=True
                     
            self.preferences['gui_resolution']=float(dia.gui_resolution.GetValue())                    

            #except:
            #     self.preferences['gui_resolution']=100.
            self.preferences['show_Arai_temperatures']=dia.show_Arai_temperatures.GetValue()
            self.preferences['show_Arai_temperatures_steps']=dia.show_Arai_temperatures_steps.GetValue()
            self.preferences['show_Arai_pTRM_arrows']=dia.show_Arai_pTRM_arrows.GetValue()
            self.preferences['show_Zij_temperatures']=dia.show_Zij_temperatures.GetValue()
            self.preferences['show_Zij_temperatures_steps']=dia.show_Zij_temperatures_steps.GetValue()
            self.preferences['show_eqarea_temperatures']=dia.show_eqarea_temperatures.GetValue()
            self.preferences['show_eqarea_pTRMs']=dia.show_eqarea_pTRMs.GetValue()
            self.preferences['show_eqarea_IZZI_colors']=dia.show_eqarea_IZZI_colors.GetValue()
            
            self.preferences['show_NLT_plot']=dia.show_NLT_plot.GetValue()
            self.preferences['show_CR_plot']=dia.show_CR_plot.GetValue()
##            try:
##                self.preferences['BOOTSTRAP_N']=float(dia.bootstrap_N.GetValue())
##            except:
##                pass


            self.write_preferences_to_file(change_resolution)

    def write_preferences_to_file(self,need_to_close_frame):
                        
            dlg1 = wx.MessageDialog(self,caption="Message:", message="save the thellier_gui.preferences in PmagPy directory!" ,style=wx.OK|wx.ICON_INFORMATION)
            dlg1.ShowModal()
            dlg1.Destroy()
            PATH="~/PmagPy"
            try:
                PATH = check_updates.get_pmag_dir()
            except:
                pass
            dlg2 = wx.FileDialog(
                self, message="save the thellier_gui_preference.txt in PmagPy directory!",
                defaultDir=PATH, 
                defaultFile="thellier_gui_preferences.py",
                style=wx.FD_SAVE | wx.CHANGE_DIR
                )
            if dlg2.ShowModal() == wx.ID_OK:
                preference_file = dlg2.GetPath()
                fout=open(preference_file,'w')
                String=""

                fout.write("preferences={}\n")

                for key in  self.preferences.keys():
                    if key in ['BOOTSTRAP_N','gui_resolution','show_Zij_temperatures_steps','show_Arai_temperatures_steps']:
                        String="preferences['%s']=%f\n"%(key,self.preferences[key])
                    elif key in ["VDM_or_VADM"]:
                        String="preferences['%s']='%s'\n"%(key,self.preferences[key])
                    elif key in ["show_statistics_on_gui"]:
                        TEXT=""
                        for stat in self.preferences[key]:
                            TEXT=TEXT+"'"+stat+"',"                        
                        String="preferences['%s']=[%s]\n"%(key,TEXT[:-1])
                    else:
                        String="preferences['%s']=%f\n"%(key,self.preferences[key])
                        
                    fout.write(String)    
                fout.close()
                os.chmod(preference_file,0777)            
                
            dlg2.Destroy()

            if need_to_close_frame:
                dlg3 = wx.MessageDialog(self, "You need to restart the program.\n","Confirm Exit", wx.OK|wx.ICON_QUESTION)
                result = dlg3.ShowModal()
                dlg3.Destroy()
                if result == wx.ID_OK:
                    #self.Destroy()
                    sys.exit()

                    

    #-----------------------------------

    def get_preferences(self):
        #default
        preferences={}
        preferences['gui_resolution']=100.
        preferences['show_Arai_temperatures']=True
        preferences['show_Arai_temperatures_steps']=1.            
        preferences['show_Arai_pTRM_arrows']=True
        preferences['show_Zij_temperatures']=False
        preferences['show_Zij_temperatures_steps']=1.
        preferences['show_eqarea_temperatures']=False
        preferences['show_eqarea_pTRMs']=True
        preferences['show_eqarea_IZZI_colors']=False      
        preferences['show_NLT_plot']=True
        preferences['show_CR_plot']=True
        preferences['BOOTSTRAP_N']=1e4
        preferences['VDM_or_VADM']="VADM"
        preferences['show_statistics_on_gui']=["int_n","int_ptrm_n","frac","scat","gmax","b_beta","int_mad","int_dang","f","fvds","g","q","drats"]#,'ptrms_dec','ptrms_inc','ptrms_mad','ptrms_angle']
        #try to read preferences file:
        try:
            import thellier_gui_preferences
            self.GUI_log.write( "-I- thellier_gui.preferences imported\n")
            preferences.update(thellier_gui_preferences.preferences)
        except:
            self.GUI_log.write( " -I- cant find thellier_gui_preferences file, using defualt default \n")
        
        # check pmag_criteria.txt:
        # if a statistic appear in pmag_criteria.txt but does not appear in 
        # preferences['show_statistics_on_gui'] than it is added to ['show_statistics_on_gui']:
        for stat in self.acceptance_criteria.keys():
            if self.acceptance_criteria[stat]['category'] in ['IE-SPEC']:
                if self.acceptance_criteria[stat]['value']!=-999:
                    short_crit=stat.split('specimen_')[-1]
                    if short_crit not in preferences['show_statistics_on_gui']:
                        preferences['show_statistics_on_gui'].append(short_crit)
                        print "-I-",short_crit, " was added to criteria list and will be displayed on screen"
                     
        
        # OLD code,
        #try:
        #    criteria_file=os.path.join(self.WD,"pmag_criteria.txt")
        #    my_acceptance_criteria=pmag.read_criteria_from_file(criteria_file,self.acceptance_criteria)
        #    #    print "-III- Read criteria",my_acceptance_criteria
        #    for crit in my_acceptance_criteria.keys():
        #        if 'specimen' in crit:
        #            if my_acceptance_criteria[crit]['value']!=-999:
        #                short_crit=crit.split('specimen_')[-1]
        #                if short_crit not in preferences['show_statistics_on_gui']:
        #                    preferences['show_statistics_on_gui'].append(short_crit)
        #                    print "-I-",short_crit, " was added to criteria list and will be displayed on screen"
        #except:
        #    pass     
        return(preferences)
        


    #----------------------------------

    def on_menu_preferences_stat(self,event):
                    
        dia = thellier_gui_dialogs.preferences_stats_dialog(None,"Thellier_gui statistical preferences",self.preferences)
        dia.Center()
        if dia.ShowModal() == wx.ID_OK: # Until the user clicks OK, show the message
            try:
                self.preferences['BOOTSTRAP_N']=float(dia.bootstrap_N.GetValue())
            except:
                pass

            self.preferences['VDM_or_VADM']=str(dia.v_adm_box.GetValue())

            dlg1 = wx.MessageDialog(self,caption="Message:", message="save the thellier_gui.preferences in PmagPy directory!" ,style=wx.OK|wx.ICON_INFORMATION)
            dlg1.ShowModal()
            dlg1.Destroy()
        

            dlg2 = wx.FileDialog(
                self, message="save the thellier_gui_preference.txt in PmagPy directory!",
                defaultDir="~/PmagPy", 
                defaultFile="thellier_gui_preferences.py",
                style=wx.FD_SAVE | wx.CHANGE_DIR
                )
            if dlg2.ShowModal() == wx.ID_OK:
                preference_file = dlg2.GetPath()
                fout=open(preference_file,'w')
                String=""

                fout.write("preferences={}\n")
                for key in  self.preferences.keys():
                    if key in ['BOOTSTRAP_N','gui_resolution','show_Zij_temperatures_steps','show_Arai_temperatures_steps']:
                        String="preferences['%s']=%f\n"%(key,self.preferences[key])
                    elif key in ["VDM_or_VADM"]:
                        String="preferences['%s']='%s'\n"%(key,self.preferences[key])
                    elif key in ["show_statistics_on_gui"]:
                        TEXT=""
                        for stat in self.preferences[key]:
                            TEXT=TEXT+"'"+stat+"',"                        
                        String="preferences['%s']=[%s]\n"%(key,TEXT[:-1])
                        
                    else:
                        String="preferences['%s']=%f\n"%(key,self.preferences[key])
                    #print String
                    fout.write(String)    
                    
                fout.close()
                os.chmod(preference_file,0777)            
                
            dlg2.Destroy()

            
            return()  


    def on_menu_m_preferences_spd(self, event):
        
        dia = thellier_gui_dialogs.PI_Statistics_Dialog(None, self.preferences["show_statistics_on_gui"],title='SPD list')
        dia.Center()
        if dia.ShowModal() == wx.ID_OK: # Until the user clicks OK, show the message            
            self.On_close_spd_box(dia)
    
    def On_close_spd_box(self, dia):
        if self.preferences["show_statistics_on_gui"]!=dia.show_statistics_on_gui:
            self.preferences["show_statistics_on_gui"]=dia.show_statistics_on_gui
            self.write_preferences_to_file(True)
        else:
            pass
                
        
        


    #-----------------------------------
        
    def on_menu_exit(self, event):
        if self.close_warning:
            TEXT="Data is not saved to a file yet!\nTo properly save your data:\n1) Analysis --> Save current interpretations to a redo file.\nor\n1) File --> Save MagIC pmag tables.\n\n Press OK to exit without saving."
            dlg1 = wx.MessageDialog(None,caption="Warning:", message=TEXT ,style=wx.OK|wx.CANCEL|wx.ICON_EXCLAMATION)
            if dlg1.ShowModal() == wx.ID_OK:
                dlg1.Destroy()
                self.Destroy()
                #sys.exit()
        else:
            self.Destroy()
            #self.Destroy() # works if matplotlib isn't using 'WXAgg', otherwise doesn't quit fully
            #wx.Exit() # works by itself, but if called in conjunction with self.Destroy you get a seg error
            # wx.Exit() # forces the program to exit, with no clean up.  works, but not an ideal solution
            #sys.exit() # program closes, but with segmentation error
            #self.Close()  # creates infinite recursion error, because we have a binding to wx.EVT_CLOSE


    def on_save_Arai_plot(self, event):
        #search for NRM:
        nrm0=""
        for rec in self.Data[self.s]['datablock']:            
          if "LT-NO" in rec['magic_method_codes']:
              nrm0= "%.2e"%float(rec['measurement_magn_moment'])
              break

        self.fig1.text(0.1,0.93,'$NRM_0 = %s Am^2 $'%(nrm0),{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'left' })
        self.fig1.text(0.9,0.93,'%s'%(self.s),{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'right' })
        #self.canvas1.draw()
        thellier_gui_dialogs.SaveMyPlot(self.fig1,self.pars,"Arai")
        self.fig1.clear()
        self.fig1.text(0.01,0.98,"Arai plot",{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'left' })
        self.araiplot = self.fig1.add_axes([0.1,0.1,0.8,0.8])
        self.draw_figure(self.s)
        self.update_selection()

    def on_save_Zij_plot(self, event):
        self.fig2.text(0.9,0.96,'%s'%(self.s),{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'right' })
        #self.canvas1.draw()
        thellier_gui_dialogs.SaveMyPlot(self.fig2,self.pars,"Zij")
        self.fig2.clear()
        self.fig2.text(0.02,0.96,"Zijderveld",{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'left' })
        self.zijplot = self.fig2.add_subplot(111)
        self.draw_figure(self.s)
        self.update_selection()
        
    def on_save_Eq_plot(self, event):
        self.fig3.text(0.9,0.96,'%s'%(self.s),{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'right' })        
        thellier_gui_dialogs.SaveMyPlot(self.fig3,self.pars,"Eqarea")
        self.fig3.clear()
        self.fig3.text(0.02,0.96,"Equal area",{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'left' })
        self.eqplot = self.fig3.add_subplot(111)
        self.draw_figure(self.s)
        self.update_selection()

    def on_save_M_t_plot(self,event):
        if self.preferences['show_NLT_plot'] ==False or 'NLT_parameters' not in self.Data[self.s].keys():
            self.fig5.text(0.9,0.96,'%s'%(self.s),{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'right' })        
            thellier_gui_dialogs.SaveMyPlot(self.fig5,self.pars,"M_T")
            self.fig5.clear()
            self.mplot = self.fig5.add_axes([0.2,0.15,0.7,0.7],frameon=True,axisbg='None')
            self.fig5.text(0.02,0.96,"M/T",{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'left' })
            self.draw_figure(self.s)
            self.update_selection()
        else:
            return


    def on_save_sample_plot(self,event):
        self.fig4.text(0.9,0.96,'%s'%(self.Data_hierarchy['specimens'][self.s]),{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'right' })        
        thellier_gui_dialogs.SaveMyPlot(self.fig4,self.pars,"Sample")
        self.fig4.clear()
        self.fig4.text(0.02,0.96,"Sample data",{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'left' })
        self.sampleplot = self.fig4.add_axes([0.2,0.3,0.7,0.6],frameon=True,axisbg='None')
        self.draw_figure(self.s)
        self.update_selection()


        
    def on_save_NLT_plot(self,event):
        if self.preferences['show_NLT_plot'] ==True and 'NLT_parameters' in self.Data[self.s].keys():
            self.fig5.text(0.9,0.96,'%s'%(self.s),{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'right' })        
            thellier_gui_dialogs.SaveMyPlot(self.fig5,self.pars,"NLT")
            self.fig5.clear()
            self.mplot = self.fig5.add_axes([0.2,0.15,0.7,0.7],frameon=True,axisbg='None')
            self.fig5.text(0.02,0.96,"Non-linear TRM check",{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'left' })
            self.draw_figure(self.s)
            self.update_selection()
        else:
            return

    def on_save_CR_plot(self,event):
        if self.preferences['show_CR_plot'] ==True and 'cooling_rate_data' in self.Data[self.s].keys():
            self.fig3.text(0.9,0.96,'%s'%(self.s),{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'right' })        
            thellier_gui_dialogs.SaveMyPlot(self.fig3,self.pars,"CR")
            self.fig3.clear()
            self.eqplot = self.fig3.add_axes([0.2,0.15,0.7,0.7],frameon=True,axisbg='None')
            self.fig3.text(0.02,0.96,"Cooling rate correction",{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'left' })
            self.draw_figure(self.s)
            self.update_selection()
        else:
            return




##    def on_save_all_plots(self,event):
##        #search for NRM:
##        nrm0=""
##        for rec in self.Data[self.s]['datablock']:            
##          if "LT-NO" in rec['magic_method_codes']:
##              nrm0= "%.2e"%float(rec['measurement_magn_moment'])
##              break
##
##        self.fig1.text(0.1,0.93,'$NRM_0 = %s Am^2 $'%(nrm0),{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'left' })
##        self.fig1.text(0.9,0.93,'%s'%(self.s),{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'right' })
##        #self.canvas1.draw()
##        SaveAllMyPlot(self.pars)
##        self.fig1.clear()
##        self.fig1.text(0.01,0.98,"Arai plot",{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'left' })
##        self.araiplot = self.fig1.add_axes([0.1,0.1,0.8,0.8])
##        self.draw_figure(self.s)
##        self.update_selection()
        
    def on_menu_previous_interpretation(self, event):
        
        save_current_specimen=self.s
        """
        Create and show the Open FileDialog for upload previous interpretation
        input should be a valid "redo file":
        [specimen name] [tmin(kelvin)] [tmax(kelvin)]
        """
        dlg = wx.FileDialog(
            self, message="choose a file in a pmagpy redo format",
            defaultDir=self.WD, 
            defaultFile="",
            #wildcard=wildcard,
            style=wx.OPEN | wx.CHANGE_DIR
            )
        if dlg.ShowModal() == wx.ID_OK:
            redo_file = dlg.GetPath()
            #print "You chose the following file(s):"
            #for path in paths:
            #print "-I- Read redo file:",redo_file
        dlg.Destroy()
        
        print "redo_file",redo_file
        self.read_redo_file(redo_file)
    #----------------------------------------------------------------------

    def on_menu_change_working_directory(self, event):
        
        self.redo_specimens={}
        self.currentDirectory = os.getcwd() # get the current working directory
        self.get_DIR()                      # choose directory dialog
        #acceptance_criteria_default,acceptance_criteria_null=self.get_default_criteria()    # inialize Null selecting criteria
        acceptance_criteria_default,acceptance_criteria_null=pmag.initialize_acceptance_criteria(),pmag.initialize_acceptance_criteria()    # inialize Null selecting criteria

        self.acceptance_criteria_null=acceptance_criteria_null
        self.acceptance_criteria_default=acceptance_criteria_default
        # inialize Null selecting criteria
        #acceptance_criteria=self.read_criteria_from_file(self.WD+"/pmag_criteria.txt")  
        #acceptance_criteria=pmag.read_criteria_from_file(self.WD+"/pmag_criteria.txt",self.acceptance_criteria_null)        
        #self.acceptance_criteria=acceptance_criteria
        self.Data,self.Data_hierarchy,self.Data_info={},{},{}
        self.Data,self.Data_hierarchy=self.get_data() # Get data from magic_measurements and rmag_anistropy if exist.
        self.Data_info=self.get_data_info() # get all ages, locations etc. (from er_ages, er_sites, er_locations)
        self.Data_samples={}
        self.Data_sites={}
        self.last_saved_pars={}
        self.specimens=self.Data.keys()         # get list of specimens
        self.specimens.sort()                   # get list of specimens


        # updtate plots and data
        self.specimens_box.SetItems(self.specimens)
        self.s=self.specimens[0]
        self.specimens_box.SetStringSelection(self.s)
        self.update_selection()

    #----------------------------------------------------------------------

    def on_menu_add_working_directory(self, event):
        

        #self.redo_specimens={}
        self.currentDirectory = os.getcwd() # get the current working directory
        dialog = wx.DirDialog(None, "Choose a magic project directory:",defaultPath = self.currentDirectory ,style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON | wx.DD_CHANGE_DIR)
        if dialog.ShowModal() == wx.ID_OK:
          new_magic_dir=dialog.GetPath()
        dialog.Destroy()
        

        self.WD=new_magic_dir
        self.magic_file=os.path.join(new_magic_dir, "magic_measurements.txt")

        new_Data,new_Data_hierarchy=self.get_data()
        new_Data_info=self.get_data_info()

        self.Data.update(new_Data)

        self.Data_hierarchy['samples'].update(new_Data_hierarchy['samples'])
        self.Data_hierarchy['specimens'].update(new_Data_hierarchy['specimens'])
        self.Data_info["er_samples"].update(new_Data_info["er_samples"])
        self.Data_info["er_sites"].update(new_Data_info["er_sites"])
        self.Data_info["er_ages"].update(new_Data_info["er_ages"])
        
        #self.Data_samples={}
        #self.last_saved_pars={}
        
        self.specimens=self.Data.keys()         # get list of specimens
        self.specimens.sort()                   # get list of specimens

        
        # updtate plots and data
        self.WD=self.currentDirectory
        self.specimens_box.SetItems(self.specimens)
        self.s=self.specimens[0]
        self.specimens_box.SetStringSelection(self.s)
        self.update_selection()
        
    #----------------------------------------------------------------------

    def on_menu_m_open_magic_tree(self, event):
        self.open_magic_tree()
        
    def open_magic_tree(self):

        busy_frame=wx.BusyInfo("Loading data\n It may take few seconds, depending on the number of specimens ...", self)
        #busy_frame.Center()
        if FIRST_RUN and "-tree" in sys.argv:
            new_dir=self.WD
        else:
            dialog = wx.DirDialog(None, "Choose a path. All magic directories in the path will be imported:",defaultPath = self.currentDirectory ,style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON | wx.DD_CHANGE_DIR)
            ok = dialog.ShowModal()
            if ok == wx.ID_OK:
              new_dir=dialog.GetPath()
            dialog.Destroy()

        #os.chdir(new_dir)
        for FILE in os.listdir(new_dir):
            path=new_dir+"/"+FILE
            if os.path.isdir(path):
                    print "importing from path %s"%path
                #try:
                    self.WD=path
                    self.magic_file = os.path.join(path, "magic_measurements.txt")
                    new_Data_info=self.get_data_info()
                    self.Data_info["er_samples"].update(new_Data_info["er_samples"])
                    self.Data_info["er_sites"].update(new_Data_info["er_sites"])
                    self.Data_info["er_ages"].update(new_Data_info["er_ages"])
                   
                    new_Data,new_Data_hierarchy=self.get_data()
                    if new_Data=={}:
                        print "-E- ERROR importing MagIC data from path."
                        continue                        
                    #for s in new_Data.keys():
                    #    if 'crblock' in new_Data[s].keys():
                    #        print s,': found crblock in new data'
                    #    if 'cooling_rate_data' in new_Data[s].keys():
                    #        print s,': cooling_rate_data in new data'

                    self.Data_hierarchy['samples'].update(new_Data_hierarchy['samples'])
                    self.Data_hierarchy['sites'].update(new_Data_hierarchy['sites'])
                    self.Data_hierarchy['specimens'].update(new_Data_hierarchy['specimens'])
                    self.Data_hierarchy['sample_of_specimen'].update(new_Data_hierarchy['sample_of_specimen']) 
                    self.Data_hierarchy['site_of_specimen'].update(new_Data_hierarchy['site_of_specimen'])   
                    self.Data_hierarchy['site_of_sample'].update(new_Data_hierarchy['site_of_sample'])   

                    self.Data.update(new_Data)
                #except:
        self.specimens=self.Data.keys()         # get list of specimens
        self.specimens.sort()                   # get list of specimens

        #temp patch
        #for s in self.specimens:
        #    if 'crblock' in self.Data[s].keys():
        #        print s,': found crblock'
        #    if 'cooling_rate_data' in self.Data[s].keys():
        #         print s,': cooling_rate_data'
               
        # updtate plots and data
        if not FIRST_RUN:
            self.WD=self.currentDirectory
            self.specimens_box.SetItems(self.specimens)
            self.s=self.specimens[0]
            self.specimens_box.SetStringSelection(self.s)
            self.update_selection()                    
        busy_frame.Destroy()
    #----------------------------------------------------------------------

    def on_menu_open_magic_file(self, event):
        dlg = wx.FileDialog(
            self, message="choose a MagIC format measurement file",
            defaultDir=self.currentDirectory, 
            defaultFile="",
            #wildcard=wildcard,
            style=wx.OPEN | wx.CHANGE_DIR
            )        
        if dlg.ShowModal() == wx.ID_OK:
            new_magic_file = dlg.GetPath()
            #print "You chose the following file(s):"
        dlg.Destroy()
        self.magic_file=new_magic_file
        path=new_magic_file.split("/")
        self.WD=new_magic_file.strip(path[-1])
                                                                
        self.Data,self.Data_hierarchy=self.get_data()
        self.Data_info=self.get_data_info() 

        self.redo_specimens={}
        self.specimens=self.Data.keys()
        self.specimens.sort()
        self.specimens_box.SetItems(self.specimens)
        self.s=self.specimens[0]
        self.update_selection()

    #----------------------------------------------------------------------        

    def on_menu_criteria_file(self, event):
        
        """
        read pmag_criteria.txt file 
        and open change criteria dialog
        """
    
        dlg = wx.FileDialog(
            self, message="choose a file in a pmagpy format",
            defaultDir=self.WD, 
            defaultFile="pmag_criteria.txt",
            #wildcard=wildcard,
            style=wx.OPEN | wx.CHANGE_DIR
            )
        if dlg.ShowModal() == wx.ID_OK:
            criteria_file = dlg.GetPath()
            self.GUI_log.write ("-I- Read new criteria file: %s\n"%criteria_file)
        dlg.Destroy()

        try:        
            replace_acceptance_criteria=pmag.initialize_acceptance_criteria()
            replace_acceptance_criteria=pmag.read_criteria_from_file(criteria_file,replace_acceptance_criteria) # just to see if file exist        
            
        except:
            dlg1 = wx.MessageDialog(self,caption="Error:",message="error in reading file" ,style=wx.OK)
            result = dlg1.ShowModal()
            if result == wx.ID_OK:
                dlg1.Destroy()
                return
        
        self.acceptance_criteria=pmag.initialize_acceptance_criteria()
        self.add_thellier_gui_criteria()
        self.read_criteria_file(criteria_file)     
        # check if some statistics are in the new pmag_criteria_file but not in old. If yes, add to  self.preferences['show_statistics_on_gui']
        crit_list_not_in_pref=[]
        for crit in   self.acceptance_criteria.keys():
            if  self.acceptance_criteria[crit]['category']=="IE-SPEC":
                if self.acceptance_criteria[crit]['value']!=-999:
                    short_crit=crit.split('specimen_')[-1]
                    if short_crit not in self.preferences['show_statistics_on_gui']:
                        print "-I- statitics %s is not in your preferences"%crit
                        self.preferences['show_statistics_on_gui'].append(short_crit)
                        crit_list_not_in_pref.append(crit)
        if  len(crit_list_not_in_pref)>0:
            stat_list=":".join(crit_list_not_in_pref)
            dlg1 = wx.MessageDialog(self,caption="WARNING:", 
            message="statistics '%s' is in the imported pmag_criteria.txt but not in your appearence preferences.\nThis statistic will not appear on the gui panel.\n The program will exit after saving new acceptance criteria, and it will be added automatically the next time you open it "%stat_list ,
            style=wx.OK|wx.ICON_INFORMATION)
            dlg1.ShowModal()
            dlg1.Destroy()
           
        dia = thellier_gui_dialogs.Criteria_Dialog(None, self.acceptance_criteria,self.preferences,title='Acceptance Criteria')
        dia.Center()
        result = dia.ShowModal()
        if result == wx.ID_OK: # Until the user clicks OK, show the message
            self.On_close_criteria_box(dia)
            if len(crit_list_not_in_pref)>0:
                dlg1 = wx.MessageDialog(self,caption="WARNING:", 
                message="Exiting now! When you restart the gui all the new statistics will be added." ,
                style=wx.OK|wx.ICON_INFORMATION)
                dlg1.ShowModal()
                dlg1.Destroy()
                #self.Destroy()
                sys.exit()
                
        if result == wx.ID_CANCEL: # Until the user clicks OK, show the message
            for crit in crit_list_not_in_pref:
               short_crit=crit.split('specimen_')[-1] 
               self.preferences['show_statistics_on_gui'].remove(short_crit)

    #----------------------------------------------------------------------        

    def on_menu_criteria(self, event):
        
        """
        Change acceptance criteria
        and save it to pmag_criteria.txt
        """
                            

        dia = thellier_gui_dialogs.Criteria_Dialog(None, self.acceptance_criteria,self.preferences,title='Set Acceptance Criteria')
        dia.Center()
        result = dia.ShowModal()

        if result == wx.ID_OK: # Until the user clicks OK, show the message
            self.On_close_criteria_box(dia)
                
                        
    def On_close_criteria_box(self,dia):

        """
        after criteria dialog window is closed. 
        Take the acceptance criteria values and update
        self.acceptance_criteria
        """
        criteria_list=self.acceptance_criteria.keys()
        criteria_list.sort()
        
        #---------------------------------------
        # check if averaging by sample or by site
        # and intialize sample/site criteria
        #---------------------------------------
        
        if dia.set_average_by_sample_or_site.GetValue()=='sample':
            for crit in ['site_int_n','site_int_sigma','site_int_sigma_perc','site_aniso_mean','site_int_n_outlier_check']:
                self.acceptance_criteria[crit]['value']=-999
        if dia.set_average_by_sample_or_site.GetValue()=='site':
            for crit in ['sample_int_n','sample_int_sigma','sample_int_sigma_perc','sample_aniso_mean','sample_int_n_outlier_check']:
                self.acceptance_criteria[crit]['value']=-999

        #---------
        
        for i in range(len(criteria_list)):            
            crit=criteria_list[i]
            #---------
            # get the "value" from dialog box
            #---------
                # dealing with sample/site
            if dia.set_average_by_sample_or_site.GetValue()=='sample':
                if crit in ['site_int_n','site_int_sigma','site_int_sigma_perc','site_aniso_mean','site_int_n_outlier_check']:
                    continue
            if dia.set_average_by_sample_or_site.GetValue()=='site':
                if crit in ['sample_int_n','sample_int_sigma','sample_int_sigma_perc','sample_aniso_mean','sample_int_n_outlier_check']:
                    continue
            #------
            if crit in ['site_int_n','site_int_sigma_perc','site_aniso_mean','site_int_n_outlier_check']:
                command="value=dia.set_%s.GetValue()"%crit.replace('site','sample')                
            
            elif crit=='sample_int_sigma' or crit=='site_int_sigma':
                #command="value=float(dia.set_sample_int_sigma_uT.GetValue())*1e-6"            
                command="value=dia.set_sample_int_sigma_uT.GetValue()"
            else:
                command="value=dia.set_%s.GetValue()"%crit
            #------
            try:
                exec command
            except:
                continue
            
            #---------
            # write the "value" to self.acceptance_criteria
            #---------
                        
            if crit=='average_by_sample_or_site': 
                self.acceptance_criteria[crit]['value']=str(value)
                continue 

            if type(value)==bool and value==True:
                self.acceptance_criteria[crit]['value']=True
            elif type(value)==bool and value==False:
                self.acceptance_criteria[crit]['value']=-999                        
            elif type(value)==unicode and str(value)=="":
                self.acceptance_criteria[crit]['value']=-999
            elif type(value)==unicode and str(value)!="": # should be a number
                try:
                    self.acceptance_criteria[crit]['value']=float(value)
                except:
                    self.show_messege(crit) 
            elif type(value)==float or type(value)==int:
                    self.acceptance_criteria[crit]['value']=float(value)         
            else:  
                self.show_messege(crit)
            if ( crit=='sample_int_sigma' or crit=='site_int_sigma' ) and str(value)!="":
                self.acceptance_criteria[crit]['value']=float(value)*1e-6  
            #print crit
            #print value
            #print str(value)==""
        #---------
        # thellier interpreter calculation type
        if dia.set_stdev_opt.GetValue()==True:
            self.acceptance_criteria['interpreter_method']['value']='stdev_opt'
        elif  dia.set_bs.GetValue()==True:
            self.acceptance_criteria['interpreter_method']['value']='bs'            
        elif  dia.set_bs_par.GetValue()==True:
            self.acceptance_criteria['interpreter_method']['value']='bs_par'            
            
                
            
        #  message dialog
        dlg1 = wx.MessageDialog(self,caption="Warning:", message="changes are saved to pmag_criteria.txt\n " ,style=wx.OK)
        result = dlg1.ShowModal()
        if result == wx.ID_OK:
            try:
                self.clear_boxes()
            except:
                pass
            try:
                self.write_acceptance_criteria_to_boxes()
            except:
                pass
            pmag.write_criteria_to_file(os.path.join(self.WD, "pmag_criteria.txt"),self.acceptance_criteria)
            dlg1.Destroy()    
            dia.Destroy()
        self.recaclulate_satistics()
        try:
            self.update_GUI_with_new_interpretation()
        except:
            pass
        
    # only valid naumber can be entered to boxes
    # used by On_close_criteria_box         
 
    def show_messege(self,key):
        dlg1 = wx.MessageDialog(self,caption="Error:",
            message="non-vaild value for box %s"%key ,style=wx.OK)
        result = dlg1.ShowModal()
        if result == wx.ID_OK:
            dlg1.Destroy()
        
    def recaclulate_satistics(self):
        '''
        update self.Data[specimen]['pars'] for all specimens.
        '''
        gframe=wx.BusyInfo("Re-calculating statistics for all specimens\n Please wait..", self)

        for specimen in self.Data.keys():
            if 'pars' not in self.Data[specimen].keys():
                continue
            if 'specimen_int_uT' not in self.Data[specimen]['pars'].keys():
                continue
            tmin=self.Data[specimen]['pars']['measurement_step_min']
            tmax=self.Data[specimen]['pars']['measurement_step_max']
            pars=thellier_gui_lib.get_PI_parameters(self.Data,self.acceptance_criteria,self.preferences,specimen,tmin,tmax,self.GUI_log,THERMAL,MICROWAVE)
            self.Data[specimen]['pars']=pars
            self.Data[specimen]['pars']['lab_dc_field']=self.Data[specimen]['lab_dc_field']
            self.Data[specimen]['pars']['er_specimen_name']=self.Data[specimen]['er_specimen_name']   
            self.Data[specimen]['pars']['er_sample_name']=self.Data[specimen]['er_sample_name']   
        gframe.Destroy()    
                               
        
                


            
    #----------------------------------------------------------------------

    def read_criteria_file(self,criteria_file):
        '''
        read criteria file.
        initialize self.acceptance_criteria
        try to guess if averaging by sample or by site.
        '''

                
        try:
            self.acceptance_criteria=pmag.read_criteria_from_file(criteria_file,self.acceptance_criteria)
        except:
            print "-E- Cant read pmag criteria file"

        # guesss if average by site or sample:
        by_sample=True
        flag=False
        for crit in ['sample_int_n','sample_int_sigma_perc','sample_int_sigma']:
            if self.acceptance_criteria[crit]['value']==-999:
                flag=True
        if flag:
            for crit in ['site_int_n','site_int_sigma_perc','site_int_sigma']:
                if self.acceptance_criteria[crit]['value']!=-999:
                    by_sample=False
        if not by_sample:
            self.acceptance_criteria['average_by_sample_or_site']['value']='site'
        

    def on_menu_save_interpretation(self, event):
 
        '''
        save interpretations to a redo file        
        '''
               
        #thellier_gui_specimen_criteria_list=['specimen_int_n','specimen_int_ptrm_n','specimen_f','specimen_fvds','specimen_frac','specimen_gmax','specimen_b_beta','specimen_scat','specimen_drats','specimen_md','specimen_int_mad','specimen_dang','specimen_q','specimen_g']
        thellier_gui_redo_file=open(os.path.join(self.WD, "thellier_GUI.redo"),'w')
        #thellier_gui_specimen_file=open("%s/thellier_GUI.specimens.txt"%(self.WD),'w')
        #thellier_gui_sample_file=open("%s/thellier_GUI.samples.txt"%(self.WD),'w')

            
        #--------------------------------------------------
        #  write interpretations to thellier_GUI.redo
        #--------------------------------------------------
        spec_list=self.Data.keys()
        spec_list.sort()
        redo_specimens_list=[]
        for sp in spec_list:
            if 'saved' not in self.Data[sp]['pars']:
                continue
            if not self.Data[sp]['pars']['saved']:
                continue
            redo_specimens_list.append(sp)

            thellier_gui_redo_file.write("%s %.0f %.0f\n"%(sp,self.Data[sp]['pars']['measurement_step_min'],self.Data[sp]['pars']['measurement_step_max']))
        dlg1 = wx.MessageDialog(self,caption="Saved:",message="File thellier_GUI.redo is saved in MagIC working folder" ,style=wx.OK)
        result = dlg1.ShowModal()
        if result == wx.ID_OK:
            dlg1.Destroy()
            return
                                
        thellier_gui_redo_file.close()   
        self.close_warning=False    
    def on_menu_clear_interpretation(self, event):
        '''
        clear all current interpretations.
        '''

        #  delete all previous interpretation
        for sp in self.Data.keys():
            del self.Data[sp]['pars']
            self.Data[sp]['pars']={}
            self.Data[sp]['pars']['lab_dc_field']=self.Data[sp]['lab_dc_field']
            self.Data[sp]['pars']['er_specimen_name']=self.Data[sp]['er_specimen_name']   
            self.Data[sp]['pars']['er_sample_name']=self.Data[sp]['er_sample_name']   
        self.Data_samples={}
        self.Data_sites={}
        self.tmin_box.SetValue("")
        self.tmax_box.SetValue("")
        self.clear_boxes()
        self.draw_figure(self.s)

    #--------------------------------------------------------------------


    def on_menu_calculate_aniso_tensor(self, event):

        self.calculate_anistropy_tensors()
        text1="Anisotropy tensors elements are saved in rmag_anistropy.txt\n"
        text2="Other anisotropy statistics are saved in rmag_results.txt\n"
        
        dlg1 = wx.MessageDialog(self,caption="Message:", message=text1+text2 ,style=wx.OK|wx.ICON_INFORMATION)
        dlg1.ShowModal()
        dlg1.Destroy()
        

    #========================================================
    # Anistropy tensors
    #========================================================


    def calculate_anistropy_tensors(self):

        def tauV(T):
            """
            gets the eigenvalues (tau) and eigenvectors (V) from matrix T
            """
            t,V,tr=[],[],0.
            ind1,ind2,ind3=0,1,2
            evalues,evectmps=linalg.eig(T)
            evectors=transpose(evectmps)  # to make compatible with Numeric convention
            for tau in evalues:
                tr+=tau
            if tr!=0:
                for i in range(3):
                    evalues[i]=evalues[i]/tr
            else:
                return t,V
        # sort evalues,evectors
            t1,t2,t3=0.,0.,1.
            for k in range(3):
                if evalues[k] > t1: 
                    t1,ind1=evalues[k],k 
                if evalues[k] < t3: 
                    t3,ind3=evalues[k],k 
            for k in range(3):
                if evalues[k] != t1 and evalues[k] != t3: 
                    t2,ind2=evalues[k],k
            V.append(evectors[ind1])
            V.append(evectors[ind2])
            V.append(evectors[ind3])
            t.append(t1)
            t.append(t2)
            t.append(t3)
            return t,V
        
        #def main():
            

        def calculate_aniso_parameters(B,K):

            aniso_parameters={}
            S_bs=dot(B,K)
            
            # normalize by trace
            trace=S_bs[0]+S_bs[1]+S_bs[2]
            S_bs=S_bs/trace
            s1,s2,s3,s4,s5,s6=S_bs[0],S_bs[1],S_bs[2],S_bs[3],S_bs[4],S_bs[5]
            s_matrix=[[s1,s4,s6],[s4,s2,s5],[s6,s5,s3]]
            
            # calculate eigen vector,
            t,evectors=eig(s_matrix)
            # sort vectors
            t=list(t)
            t1=max(t)
            ix_1=t.index(t1)
            t3=min(t)
            ix_3=t.index(t3)
            for tt in range(3):
                if t[tt]!=t1 and t[tt]!=t3:
                    t2=t[tt]
                    ix_2=t.index(t2)
                    
            v1=[evectors[0][ix_1],evectors[1][ix_1],evectors[2][ix_1]]
            v2=[evectors[0][ix_2],evectors[1][ix_2],evectors[2][ix_2]]
            v3=[evectors[0][ix_3],evectors[1][ix_3],evectors[2][ix_3]]


            DIR_v1=pmag.cart2dir(v1)
            DIR_v2=pmag.cart2dir(v2)
            DIR_v3=pmag.cart2dir(v3)

                               
            aniso_parameters['anisotropy_s1']="%f"%s1
            aniso_parameters['anisotropy_s2']="%f"%s2
            aniso_parameters['anisotropy_s3']="%f"%s3
            aniso_parameters['anisotropy_s4']="%f"%s4
            aniso_parameters['anisotropy_s5']="%f"%s5
            aniso_parameters['anisotropy_s6']="%f"%s6
            aniso_parameters['anisotropy_degree']="%f"%(t1/t3)
            aniso_parameters['anisotropy_t1']="%f"%t1
            aniso_parameters['anisotropy_t2']="%f"%t2
            aniso_parameters['anisotropy_t3']="%f"%t3
            aniso_parameters['anisotropy_v1_dec']="%.1f"%DIR_v1[0]
            aniso_parameters['anisotropy_v1_inc']="%.1f"%DIR_v1[1]
            aniso_parameters['anisotropy_v2_dec']="%.1f"%DIR_v2[0]
            aniso_parameters['anisotropy_v2_inc']="%.1f"%DIR_v2[1]
            aniso_parameters['anisotropy_v3_dec']="%.1f"%DIR_v3[0]
            aniso_parameters['anisotropy_v3_inc']="%.1f"%DIR_v3[1]

            # modified from pmagpy:
            if len(K)/3==9 or len(K)/3==6 or len(K)/3==15:
                n_pos=len(K)/3
                tmpH = Matrices[n_pos]['tmpH']
                a=s_matrix
                S=0.
                comp=zeros((n_pos*3),'f')
                for i in range(n_pos):
                    for j in range(3):
                        index=i*3+j
                        compare=a[j][0]*tmpH[i][0]+a[j][1]*tmpH[i][1]+a[j][2]*tmpH[i][2]
                        comp[index]=compare
                for i in range(n_pos*3):
                    d=K[i]/trace - comp[i] # del values
                    S+=d*d
                nf=float(n_pos*3-6) # number of degrees of freedom
                if S >0: 
                    sigma=pylab.math.sqrt(S/nf)
                hpars=pmag.dohext(nf,sigma,[s1,s2,s3,s4,s5,s6])
                
                aniso_parameters['anisotropy_sigma']="%f"%sigma
                aniso_parameters['anisotropy_ftest']="%f"%hpars["F"]
                aniso_parameters['anisotropy_ftest12']="%f"%hpars["F12"]
                aniso_parameters['anisotropy_ftest23']="%f"%hpars["F23"]
                aniso_parameters['result_description']="Critical F: %s"%(hpars['F_crit'])
                aniso_parameters['anisotropy_F_crit']="%f"%float(hpars['F_crit'])
                aniso_parameters['anisotropy_n']=n_pos
                
            return(aniso_parameters)



        
        aniso_logfile=open(os.path.join(self.WD, "rmag_anisotropy.log"),'w')

        aniso_logfile.write("------------------------\n")
        aniso_logfile.write( "-I- Start rmag anisrotropy script\n")
        aniso_logfile.write( "------------------------\n")



        #-----------------------------------
        # Prepare rmag_anisotropy.txt file for writing
        #-----------------------------------

        rmag_anisotropy_file =open(os.path.join(self.WD, "rmag_anisotropy.txt"),'w')
        rmag_anisotropy_file.write("tab\trmag_anisotropy\n")

        rmag_results_file =open(os.path.join(self.WD, "rmag_results.txt"),'w')
        rmag_results_file.write("tab\trmag_results\n")
        
        rmag_anistropy_header=['er_specimen_name','er_sample_name','er_site_name','anisotropy_type','anisotropy_n','anisotropy_description','anisotropy_s1','anisotropy_s2','anisotropy_s3','anisotropy_s4','anisotropy_s5','anisotropy_s6','anisotropy_sigma','anisotropy_alt','magic_experiment_names','magic_method_codes']

        String=""
        for i in range (len(rmag_anistropy_header)):
            String=String+rmag_anistropy_header[i]+'\t'
        rmag_anisotropy_file.write(String[:-1]+"\n")
        


        rmag_results_header=['er_specimen_names','er_sample_names','er_site_names','anisotropy_type','magic_method_codes','magic_experiment_names','result_description','anisotropy_t1','anisotropy_t2','anisotropy_t3','anisotropy_ftest','anisotropy_ftest12','anisotropy_ftest23',\
                             'anisotropy_v1_dec','anisotropy_v1_inc','anisotropy_v2_dec','anisotropy_v2_inc','anisotropy_v3_dec','anisotropy_v3_inc']


        String=""
        for i in range (len(rmag_results_header)):
            String=String+rmag_results_header[i]+'\t'
        rmag_results_file.write(String[:-1]+"\n")

        #-----------------------------------
        # Matrices definitions:
        # A design matrix
        # B dot(inv(dot(A.transpose(),A)),A.transpose())
        # tmpH is used for sigma calculation (9,15 measurements only)
        # 
        #  Anisotropy tensor:
        #
        # |Mx|   |s1 s4 s6|   |Bx|
        # |My| = |s4 s2 s5| . |By|
        # |Mz|   |s6 s5 s3|   |Bz|
        #
        # A matrix (measurement matrix):
        # Each mesurement yields three lines in "A" matrix
        #
        # |Mi  |   |Bx 0  0   By  0   Bz|   |s1|
        # |Mi+1| = |0  By 0   Bx  Bz  0 | . |s2|
        # |Mi+2|   |0  0  Bz  0   By  Bx|   |s3|
        #                                   |s4|
        #                                   |s5|
        #
        #-----------------------------------

        Matrices={}
        
        for n_pos in [6,9,15]:

            Matrices[n_pos]={}
            
            A=zeros((n_pos*3,6),'f')

            if n_pos==6:
                positions=[[0.,0.,1.],[90.,0.,1.],[0.,90.,1.],\
                     [180.,0.,1.],[270.,0.,1.],[0.,-90.,1.]]

            if n_pos==15:
                positions=[[315.,0.,1.],[225.,0.,1.],[180.,0.,1.],[135.,0.,1.],[45.,0.,1.],\
                     [90.,-45.,1.],[270.,-45.,1.],[270.,0.,1.],[270.,45.,1.],[90.,45.,1.],\
                     [180.,45.,1.],[180.,-45.,1.],[0.,-90.,1.],[0,-45.,1.],[0,45.,1.]]
            if n_pos==9:
                positions=[[315.,0.,1.],[225.,0.,1.],[180.,0.,1.],\
                     [90.,-45.,1.],[270.,-45.,1.],[270.,0.,1.],\
                     [180.,45.,1.],[180.,-45.,1.],[0.,-90.,1.]]

            
            tmpH=zeros((n_pos,3),'f') # define tmpH
            for i in range(len(positions)):
                CART=pmag.dir2cart(positions[i])
                a=CART[0];b=CART[1];c=CART[2]
                A[3*i][0]=a
                A[3*i][3]=b
                A[3*i][5]=c

                A[3*i+1][1]=b
                A[3*i+1][3]=a
                A[3*i+1][4]=c

                A[3*i+2][2]=c
                A[3*i+2][4]=b
                A[3*i+2][5]=a
                
                tmpH[i][0]=CART[0]
                tmpH[i][1]=CART[1]
                tmpH[i][2]=CART[2]

            B=dot(inv(dot(A.transpose(),A)),A.transpose())

            Matrices[n_pos]['A']=A
            Matrices[n_pos]['B']=B
            Matrices[n_pos]['tmpH']=tmpH

        #==================================================================================

        Data_anisotropy={}                
        specimens=self.Data.keys()
        specimens.sort()
        for specimen in specimens:

            if 'atrmblock' in self.Data[specimen].keys():
                
                #-----------------------------------
                # aTRM 6 positions
                #-----------------------------------
                    
                aniso_logfile.write("-I- Start calculating ATRM tensor for specimen %s\n"%specimen)
                atrmblock=self.Data[specimen]['atrmblock']
                trmblock=self.Data[specimen]['trmblock']
                zijdblock=self.Data[specimen]['zijdblock']
                if len(atrmblock)<6:
                    aniso_logfile.write("-W- specimen %s does not have enough measurements for 6 positions ATRM calculation\n"%specimen)
                    continue
                
                B=Matrices[6]['B']
                                    
                Reject_specimen = False

                # The zero field step is a "baseline"
                # and the atrm measurements are substructed from the baseline
                # if there is a zero field is in the atrm block: then use this measurement as a baseline
                # if not, the program searches for the zero-field step in the zijderveld block. 
                # the baseline is the average of all the zero field steps in the same temperature (in case there is more than one)

                # Search the baseline in the ATRM measurement
                # Search the alteration check in the ATRM measurement
                # If there is more than one baseline measurements then avrage all measurements
                
                baseline=""
                Alteration_check=""
                Alteration_check_index=""
                baselines=[]

                # search for baseline in atrm blocks
                for rec in atrmblock:
                    dec=float(rec['measurement_dec'])
                    inc=float(rec['measurement_inc'])
                    moment=float(rec['measurement_magn_moment'])
                    # find the temperature of the atrm
                    if float(rec['treatment_dc_field'])!=0 and float(rec['treatment_temp'])!=273:
                        atrm_temperature=float(rec['treatment_temp'])
                    # find baseline
                    if float(rec['treatment_dc_field'])==0 and float(rec['treatment_temp'])!=273:
                        baselines.append(scipy.array(pmag.dir2cart([dec,inc,moment])))
                    # Find alteration check
                    #print rec['measurement_number']
                
                if len(baselines)!=0:
                    aniso_logfile.write( "-I- found ATRM baseline for specimen %s\n"%specimen)
                    
                else:
                    if len(zijdblock)!=0 :
                        for rec in zijdblock:
                            zij_temp=rec[0]
                            #print rec
                            if zij_temp==atrm_temperature:
                                dec=float(rec[1])
                                inc=float(rec[2])
                                moment=float(rec[3])
                                baselines.append(scipy.array(pmag.dir2cart([dec,inc,moment])))
                                aniso_logfile.write( "-I- Found %i ATRM baselines for specimen %s in Zijderveld block. Averaging measurements\n"%(len(baselines),specimen))
                if  len(baselines)==0:
                    baseline=zeros(3,'f')
                    aniso_logfile.write( "-I- No aTRM baseline for specimen %s\n"%specimen)
                else:
                    baselines=scipy.array(baselines)
                    baseline=scipy.array([scipy.mean(baselines[:,0]),scipy.mean(baselines[:,1]),scipy.mean(baselines[:,2])])                                 
                           
                # sort measurements
                
                M=zeros([6,3],'f')
                
                for rec in atrmblock:

                    dec=float(rec['measurement_dec'])
                    inc=float(rec['measurement_inc'])
                    moment=float(rec['measurement_magn_moment'])
                    CART=scipy.array(pmag.dir2cart([dec,inc,moment]))-baseline
                    
                    if float(rec['treatment_dc_field'])==0: # Ignore zero field steps
                        continue
                    if  "LT-PTRM-I" in rec['magic_method_codes'].split(":"): #  alteration check
                        Alteration_check=CART
                        Alteration_check_dc_field_phi=float(rec['treatment_dc_field_phi'])
                        Alteration_check_dc_field_theta=float(rec['treatment_dc_field_theta'])
                        if Alteration_check_dc_field_phi==0 and Alteration_check_dc_field_theta==0 :
                            Alteration_check_index=0
                        if Alteration_check_dc_field_phi==90 and Alteration_check_dc_field_theta==0 :
                            Alteration_check_index=1
                        if Alteration_check_dc_field_phi==0 and Alteration_check_dc_field_theta==90 :
                            Alteration_check_index=2
                        if Alteration_check_dc_field_phi==180 and Alteration_check_dc_field_theta==0 :
                            Alteration_check_index=3
                        if Alteration_check_dc_field_phi==270 and Alteration_check_dc_field_theta==0 :
                            Alteration_check_index=4
                        if Alteration_check_dc_field_phi==0 and Alteration_check_dc_field_theta==-90 :
                            Alteration_check_index=5
                        aniso_logfile.write(  "-I- found alteration check  for specimen %s\n"%specimen)
                        continue
                    
                    treatment_dc_field_phi=float(rec['treatment_dc_field_phi'])
                    treatment_dc_field_theta=float(rec['treatment_dc_field_theta'])
                    treatment_dc_field=float(rec['treatment_dc_field'])
                    
                    #+x, M[0]
                    if treatment_dc_field_phi==0 and treatment_dc_field_theta==0 :
                        M[0]=CART
                    #+Y , M[1]
                    if treatment_dc_field_phi==90 and treatment_dc_field_theta==0 :
                        M[1]=CART
                    #+Z , M[2]
                    if treatment_dc_field_phi==0 and treatment_dc_field_theta==90 :
                        M[2]=CART
                    #-x, M[3]
                    if treatment_dc_field_phi==180 and treatment_dc_field_theta==0 :
                        M[3]=CART
                    #-Y , M[4]
                    if treatment_dc_field_phi==270 and treatment_dc_field_theta==0 :
                        M[4]=CART
                    #-Z , M[5]
                    if treatment_dc_field_phi==0 and treatment_dc_field_theta==-90 :
                        M[5]=CART
            
                # check if at least one measurement in missing
                for i in range(len(M)):
                    if M[i][0]==0 and M[i][1]==0 and M[i][2]==0: 
                        aniso_logfile.write( "-E- ERROR: missing atrm data for specimen %s\n"%(specimen))
                        Reject_specimen=True

                # alteration check        

                anisotropy_alt=0
                if Alteration_check!="":
                    for i in range(len(M)):
                        if Alteration_check_index==i:
                            M_1=scipy.sqrt(sum((scipy.array(M[i])**2)))
                            M_2=scipy.sqrt(sum(Alteration_check**2))
                            #print specimen
                            #print "M_1,M_2",M_1,M_2
                            diff=abs(M_1-M_2)
                            #print "diff",diff
                            #print "scipy.mean([M_1,M_2])",scipy.mean([M_1,M_2])
                            diff_ratio=diff/scipy.mean([M_1,M_2])
                            diff_ratio_perc=100*diff_ratio
                            if diff_ratio_perc > anisotropy_alt:
                                anisotropy_alt=diff_ratio_perc
                else:
                    aniso_logfile.write( "-W- Warning: no alteration check for specimen %s \n "%specimen )

                # Check for maximum difference in anti parallel directions.
                # if the difference between the two measurements is more than maximum_diff
                # The specimen is rejected
                
                # i.e. +x versus -x, +y versus -y, etc.s

                for i in range(3):
                    M_1=scipy.sqrt(sum(scipy.array(M[i])**2))
                    M_2=scipy.sqrt(sum(scipy.array(M[i+3])**2))
                    
                    diff=abs(M_1-M_2)
                    diff_ratio=diff/scipy.mean([M_1,M_2])
                    diff_ratio_perc=100*diff_ratio
                    
                    if diff_ratio_perc>anisotropy_alt:
                        anisotropy_alt=diff_ratio_perc
                        
                if not Reject_specimen:
                
                    # K vector (18 elements, M1[x], M1[y], M1[z], ... etc.) 
                    K=zeros(18,'f')
                    K[0],K[1],K[2]=M[0][0],M[0][1],M[0][2]
                    K[3],K[4],K[5]=M[1][0],M[1][1],M[1][2]
                    K[6],K[7],K[8]=M[2][0],M[2][1],M[2][2]
                    K[9],K[10],K[11]=M[3][0],M[3][1],M[3][2]
                    K[12],K[13],K[14]=M[4][0],M[4][1],M[4][2]
                    K[15],K[16],K[17]=M[5][0],M[5][1],M[5][2]

                    if specimen not in Data_anisotropy.keys():
                        Data_anisotropy[specimen]={}
                    aniso_parameters=calculate_aniso_parameters(B,K)
                    Data_anisotropy[specimen]['ATRM']=aniso_parameters
                    Data_anisotropy[specimen]['ATRM']['anisotropy_alt']="%.2f"%anisotropy_alt               
                    Data_anisotropy[specimen]['ATRM']['anisotropy_type']="ATRM"
                    Data_anisotropy[specimen]['ATRM']['er_sample_name']=atrmblock[0]['er_sample_name']
                    Data_anisotropy[specimen]['ATRM']['er_specimen_name']=specimen
                    Data_anisotropy[specimen]['ATRM']['er_site_name']=atrmblock[0]['er_site_name']
                    Data_anisotropy[specimen]['ATRM']['anisotropy_description']='Hext statistics adapted to ATRM'
                    Data_anisotropy[specimen]['ATRM']['magic_experiment_names']=specimen+";ATRM"
                    Data_anisotropy[specimen]['ATRM']['magic_method_codes']="LP-AN-TRM:AE-H"
                    #Data_anisotropy[specimen]['ATRM']['rmag_anisotropy_name']=specimen


            if 'aarmblock' in self.Data[specimen].keys():    

                #-----------------------------------
                # AARM - 6, 9 or 15 positions
                #-----------------------------------
                    
                aniso_logfile.write( "-I- Start calculating AARM tensors specimen %s\n"%specimen)

                aarmblock=self.Data[specimen]['aarmblock']
                if len(aarmblock)<12:
                    aniso_logfile.write( "-W- WARNING: not enough aarm measurement for specimen %s\n"%specimen)
                    continue
                elif len(aarmblock)==12:
                    n_pos=6
                    B=Matrices[6]['B']
                    M=zeros([6,3],'f')
                elif len(aarmblock)==18:
                    n_pos=9
                    B=Matrices[9]['B']
                    M=zeros([9,3],'f')
                # 15 positions
                elif len(aarmblock)==30:
                    n_pos=15
                    B=Matrices[15]['B']
                    M=zeros([15,3],'f')
                else:
                    aniso_logfile.write( "-E- ERROR: number of measurements in aarm block is incorrect sample %s\n"%specimen)
                    continue
                    
                Reject_specimen = False

                for i in range(n_pos):
                    for rec in aarmblock:
                        if float(rec['measurement_number'])==i*2+1:
                            dec=float(rec['measurement_dec'])
                            inc=float(rec['measurement_inc'])
                            moment=float(rec['measurement_magn_moment'])                    
                            M_baseline=scipy.array(pmag.dir2cart([dec,inc,moment]))
                            
                        if float(rec['measurement_number'])==i*2+2:
                            dec=float(rec['measurement_dec'])
                            inc=float(rec['measurement_inc'])
                            moment=float(rec['measurement_magn_moment'])                    
                            M_arm=scipy.array(pmag.dir2cart([dec,inc,moment]))
                    M[i]=M_arm-M_baseline

                    
                K=zeros(3*n_pos,'f')
                for i in range(n_pos):
                    K[i*3]=M[i][0]
                    K[i*3+1]=M[i][1]
                    K[i*3+2]=M[i][2]            

                if specimen not in Data_anisotropy.keys():
                    Data_anisotropy[specimen]={}
                aniso_parameters=calculate_aniso_parameters(B,K)
                Data_anisotropy[specimen]['AARM']=aniso_parameters
                Data_anisotropy[specimen]['AARM']['anisotropy_alt']=""               
                Data_anisotropy[specimen]['AARM']['anisotropy_type']="AARM"
                Data_anisotropy[specimen]['AARM']['er_sample_name']=aarmblock[0]['er_sample_name']
                Data_anisotropy[specimen]['AARM']['er_site_name']=aarmblock[0]['er_site_name']
                Data_anisotropy[specimen]['AARM']['er_specimen_name']=specimen
                Data_anisotropy[specimen]['AARM']['anisotropy_description']='Hext statistics adapted to AARM'
                Data_anisotropy[specimen]['AARM']['magic_experiment_names']=specimen+";AARM"
                Data_anisotropy[specimen]['AARM']['magic_method_codes']="LP-AN-ARM:AE-H"
                #Data_anisotropy[specimen]['AARM']['rmag_anisotropy_name']=specimen
                

        #-----------------------------------   

        specimens=Data_anisotropy.keys()
        specimens.sort

        # remove previous anistropy data, and replace with the new one:
        s_list=self.Data.keys()
        for sp in s_list:
            if 'AniSpec' in self.Data[sp].keys():
                del  self.Data[sp]['AniSpec']
        for specimen in specimens:
            # if both AARM and ATRM axist prefer the AARM !!
            if 'AARM' in Data_anisotropy[specimen].keys():
                TYPES=['AARM']
            if 'ATRM' in Data_anisotropy[specimen].keys():
                TYPES=['ATRM']
            if  'AARM' in Data_anisotropy[specimen].keys() and 'ATRM' in Data_anisotropy[specimen].keys():
                TYPES=['ATRM','AARM']
                aniso_logfile.write( "-W- WARNING: both aarm and atrm data exist for specimen %s. using AARM by default. If you prefer using one of them, delete the other!\n"%specimen)
            for TYPE in TYPES:
                String=""
                for i in range (len(rmag_anistropy_header)):
                    try:
                        String=String+Data_anisotropy[specimen][TYPE][rmag_anistropy_header[i]]+'\t'
                    except:
                        String=String+"%f"%(Data_anisotropy[specimen][TYPE][rmag_anistropy_header[i]])+'\t'
                rmag_anisotropy_file.write(String[:-1]+"\n")

                String=""
                Data_anisotropy[specimen][TYPE]['er_specimen_names']=Data_anisotropy[specimen][TYPE]['er_specimen_name']
                Data_anisotropy[specimen][TYPE]['er_sample_names']=Data_anisotropy[specimen][TYPE]['er_sample_name']
                Data_anisotropy[specimen][TYPE]['er_site_names']=Data_anisotropy[specimen][TYPE]['er_site_name']
                for i in range (len(rmag_results_header)):
                    try:
                        String=String+Data_anisotropy[specimen][TYPE][rmag_results_header[i]]+'\t'
                    except:
                        String=String+"%f"%(Data_anisotropy[specimen][TYPE][rmag_results_header[i]])+'\t'
                rmag_results_file.write(String[:-1]+"\n")

                if 'AniSpec' not in self.Data[specimen]:
                    self.Data[specimen]['AniSpec']={}
                self.Data[specimen]['AniSpec'][TYPE]=Data_anisotropy[specimen][TYPE]

        aniso_logfile.write("------------------------\n")
        aniso_logfile.write("-I- Done rmag anisotropy script\n")
        aniso_logfile.write( "------------------------\n")
        
        rmag_anisotropy_file.close()

    #==================================================        


    def on_show_anisotropy_errors(self,event):
        

        dia = thellier_gui_dialogs.MyLogFileErrors( "Anistropy calculation errors",os.path.join(self.WD, "rmag_anisotropy.log"))
        dia.Show()
        dia.Center()
    
        
 
#    #==================================================        
#    # Thellier Auto Interpreter Tool                        
#    #==================================================        

    def on_menu_run_interpreter(self, event):
        import dialogs.thellier_interpreter as thellier_interpreter
        busy_frame=wx.BusyInfo("Running Thellier auto interpreter\n It may take several minutes depending on the number of specimens ...", self)
        wx.Yield()
        thellier_auto_interpreter=thellier_interpreter.thellier_auto_interpreter(self.Data,self.Data_hierarchy,self.WD,self.acceptance_criteria,self.preferences,self.GUI_log,THERMAL,MICROWAVE)
        thellier_auto_interpreter.run_interpreter()
        self.Data={}
        self.Data=copy.deepcopy(thellier_auto_interpreter.Data)
        self.Data_samples=copy.deepcopy(thellier_auto_interpreter.Data_samples)
        self.Data_sites=copy.deepcopy(thellier_auto_interpreter.Data_sites)
        dlg1 = wx.MessageDialog(self,caption="Message:", message="Interpreter finished sucsessfuly\nCheck output files in folder /thellier_interpreter in the current project directory" ,style=wx.OK|wx.ICON_INFORMATION)
        
        # display the interpretation of the current specimen:
        self.pars=self.Data[self.s]['pars']
        self.clear_boxes()
        #print "about to draw figure" # this is where trouble happens when 1 or 2 specimens are accepted
        self.draw_figure(self.s)
        #print "just drew figure"
        self.update_GUI_with_new_interpretation()
        del busy_frame
        dlg1.ShowModal()
        dlg1.Destroy()
        return()
        #self.Data=copy.deepcopy      
#
#        """


#    def find_close_value(self,LIST, value):
#            '''
#            take a LIST and find the nearest value in LIST to 'value'
#            '''
#            diff=inf
#            for a in LIST:
#                if abs(value-a)<diff:
#                    diff=abs(value-a)
#                    result=a
#            return(result)
#
#    def find_sample_min_std (self,Intensities): 
#            '''
#            find the best interpretation with the minimum stratard deviation (in units of percent % !)
#            '''
#                
#            Best_array=[]
#            best_array_std_perc=inf
#            Best_array_tmp=[]
#            Best_interpretations={}
#            Best_interpretations_tmp={}
#            for this_specimen in Intensities.keys():
#                for value in Intensities[this_specimen]:
#                    Best_interpretations_tmp[this_specimen]=value
#                    Best_array_tmp=[value]
#                    all_other_specimens=Intensities.keys()
#                    all_other_specimens.remove(this_specimen)
#                    
#                    for other_specimen in all_other_specimens:
#                        closest_value=self.find_close_value(Intensities[other_specimen], value)
#                        Best_array_tmp.append(closest_value)
#                        Best_interpretations_tmp[other_specimen]=closest_value                   
#
#                    if std(Best_array_tmp,ddof=1)/scipy.mean(Best_array_tmp)<best_array_std_perc:
#                        Best_array=Best_array_tmp
#                        best_array_std_perc=std(Best_array,ddof=1)/scipy.mean(Best_array_tmp)
#                        Best_interpretations=copy.deepcopy(Best_interpretations_tmp)
#                        Best_interpretations_tmp={}
#            return Best_interpretations,scipy.mean(Best_array),std(Best_array,ddof=1)
#                                                               
#    def pass_or_fail_sigma(self,B,int_sigma_cutoff,int_sigma_perc_cutoff):
#        #pass_or_fail='fail'
#        B_mean=scipy.mean(B)
#        B_sigma=std(B,ddof=1)
#        B_sigma_perc=100*(B_sigma/B_mean)
#        
#        if int_sigma_cutoff==-999 and int_sigma_perc_cutoff==-999:
#            return('pass')
#        if  B_sigma<=int_sigma_cutoff*1e6 and int_sigma_cutoff!=-999:
#            pass_sigma=True
#        else:
#            pass_sigma=False
#        if  B_sigma_perc<=int_sigma_perc_cutoff and int_sigma_perc_cutoff!=-999:
#            pass_sigma_perc=True
#        else:
#            pass_sigma_perc=False
#        if pass_sigma or pass_sigma_perc:
#            return('pass')
#        else:
#            return('fail')
#                          
#        
#    def find_sample_min_max_interpretation (self,Intensities):
#
#          '''
#          find the minimum and maximum acceptable sample mean
#          Intensities={}
#          Intensities[specimen_name]=[] array of acceptable interpretations ( units of uT)         
#          '''
#        # acceptance criteria
#          if self.acceptance_criteria['average_by_sample_or_site']['value']=='sample':
#            int_n_cutoff=self.acceptance_criteria['sample_int_n']['value']
#            int_sigma_cutoff=self.acceptance_criteria['sample_int_sigma']['value']
#            int_sigma_perc_cutoff=self.acceptance_criteria['sample_int_sigma_perc']['value']
#          else:
#            int_n_cutoff=self.acceptance_criteria['site_int_n']['value']
#            int_sigma_cutoff=self.acceptance_criteria['site_int_sigma']['value']
#            int_sigma_perc_cutoff=self.acceptance_criteria['site_int_sigma_perc']['value']
#          if int_n_cutoff == -999:
#            int_n_cutoff=2 
#          #if int_sigma_cutoff==-999:
#          #    int_sigma_cutoff=999     
#          #if int_sigma_perc_cutoff==-999:
#          #    int_sigma_perc_cutoff=999     
#          
#          # make a new dictionary named "tmp_Intensities" with all grade A interpretation sorted. 
#          tmp_Intensities={}
#          Acceptable_sample_min_mean,Acceptable_sample_max_mean="",""
#          for this_specimen in Intensities.keys():
#            B_list=[B  for B in Intensities[this_specimen]]
#            if len(B_list)>0:
#                B_list.sort()
#                tmp_Intensities[this_specimen]=B_list
#
#          # find the minmum acceptable values
#          while len(tmp_Intensities.keys())>=int_n_cutoff:
#              B_tmp=[]
#              B_tmp_min=1e10
#              for specimen in tmp_Intensities.keys():
#                  B_tmp.append(min(tmp_Intensities[specimen]))
#                  if min(tmp_Intensities[specimen])<B_tmp_min:
#                      specimen_to_remove=specimen
#                      B_tmp_min=min(tmp_Intensities[specimen])
#              pass_or_fail=self.pass_or_fail_sigma(B_tmp,int_sigma_cutoff,int_sigma_perc_cutoff)
#              if pass_or_fail=='pass':
#                  Acceptable_sample_min_mean=scipy.mean(B_tmp)
#                  Acceptable_sample_min_std=std(B_tmp,ddof=1)
#                  #print "min value,std,",scipy.mean(B_tmp),std(B_tmp),100*(std(B_tmp)/scipy.mean(B_tmp))
#                  break
#              else:
#                  tmp_Intensities[specimen_to_remove].remove(B_tmp_min)
#                  if len(tmp_Intensities[specimen_to_remove])==0:
#                      break
#                  
#                                                                    
#          tmp_Intensities={}
#          for this_specimen in Intensities.keys():
#            B_list=[B  for B in Intensities[this_specimen]]
#            if len(B_list)>0:
#                B_list.sort()
#                tmp_Intensities[this_specimen]=B_list
#
#          while len(tmp_Intensities.keys())>=int_n_cutoff:
#              B_tmp=[]
#              B_tmp_max=0
#              for specimen in tmp_Intensities.keys():
#                  B_tmp.append(max(tmp_Intensities[specimen]))
#                  if max(tmp_Intensities[specimen])>B_tmp_max:
#                      specimen_to_remove=specimen
#                      B_tmp_max=max(tmp_Intensities[specimen])
#
#              pass_or_fail=self.pass_or_fail_sigma(B_tmp,int_sigma_cutoff,int_sigma_perc_cutoff)
#              if pass_or_fail=='pass':                                            
#              #if std(B_tmp,ddof=1)<=int_sigma_cutoff*1e6 or 100*(std(B_tmp,ddof=1)/scipy.mean(B_tmp))<=int_sigma_perc_cutoff:
#                  Acceptable_sample_max_mean=scipy.mean(B_tmp)
#                  Acceptable_sample_max_std=std(B_tmp,ddof=1)
#                  #print "max value,std,",scipy.mean(B_tmp),std(B_tmp),100*(std(B_tmp)/scipy.mean(B_tmp))
#
#                  break
#              else:
#                  tmp_Intensities[specimen_to_remove].remove(B_tmp_max)
#                  if len(tmp_Intensities[specimen_to_remove])<1:
#                      break
#
#          if Acceptable_sample_min_mean=="" or Acceptable_sample_max_mean=="":
#              return(0.,0.,0.,0.)
#          return(Acceptable_sample_min_mean,Acceptable_sample_min_std,Acceptable_sample_max_mean,Acceptable_sample_max_std) 
#
#        ############
#        # End function definitions
#        ############
#
#    def thellier_interpreter_pars_calc(self,Grade_As):
#        '''
#        calcualte sample or site STDEV-OPT paleointensities
#        and statistics 
#        Grade_As={}
#        
#        '''
#        thellier_interpreter_pars={}
#        thellier_interpreter_pars['stdev-opt']={}
#        #thellier_interpreter_pars['stdev-opt']['B']=
#        #thellier_interpreter_pars['stdev-opt']['std']=
#        thellier_interpreter_pars['min-value']={}
#        #thellier_interpreter_pars['min-value']['B']=
#        #thellier_interpreter_pars['min-value']['std']=
#        thellier_interpreter_pars['max-value']={}
#        #thellier_interpreter_pars['max-value']['B']=
#        #thellier_interpreter_pars['max-value']['std']=
#        thellier_interpreter_pars['fail_criteria']=[]
#        thellier_interpreter_pars['pass_or_fail']='pass'
#        
#        # acceptance criteria
#        if self.acceptance_criteria['average_by_sample_or_site']['value']=='sample':
#            int_n_cutoff=self.acceptance_criteria['sample_int_n']['value']
#            int_sigma_cutoff=self.acceptance_criteria['sample_int_sigma']['value']
#            int_sigma_perc_cutoff=self.acceptance_criteria['sample_int_sigma_perc']['value']
#            int_interval_cutoff=self.acceptance_criteria['sample_int_interval_uT']['value']
#            int_interval_perc_cutoff=self.acceptance_criteria['sample_int_interval_perc']['value']
#        else:
#            int_n_cutoff=self.acceptance_criteria['site_int_n']['value']
#            int_sigma_cutoff=self.acceptance_criteria['site_int_sigma']['value']
#            int_sigma_perc_cutoff=self.acceptance_criteria['site_int_sigma_perc']['value']
#            int_interval_cutoff=self.acceptance_criteria['site_int_interval_uT']['value']
#            int_interval_perc_cutoff=self.acceptance_criteria['site_int_interval_perc']['value']
#        
#        N= len(Grade_As.keys())                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   
#        if N <= 1:
#           thellier_interpreter_pars['pass_or_fail']='fail'
#           thellier_interpreter_pars['fail_criteria'].append("int_n")
#           return(thellier_interpreter_pars)
#                                
#        Best_interpretations,best_mean,best_std=self.find_sample_min_std(Grade_As)
#        sample_acceptable_min,sample_acceptable_min_std,sample_acceptable_max,sample_acceptable_max_std = self.find_sample_min_max_interpretation (Grade_As)
#        sample_int_interval_uT=sample_acceptable_max-sample_acceptable_min
#        sample_int_interval_perc=100*((sample_acceptable_max-sample_acceptable_min)/best_mean)       
#        thellier_interpreter_pars['stdev_opt_interpretations']=Best_interpretations
#        thellier_interpreter_pars['stdev-opt']['B']=best_mean
#        thellier_interpreter_pars['stdev-opt']['std']=best_std
#        thellier_interpreter_pars['stdev-opt']['std_perc']=100.*(best_std/best_mean)    
#        thellier_interpreter_pars['min-value']['B']=sample_acceptable_min
#        thellier_interpreter_pars['min-value']['std']=sample_acceptable_min_std
#        thellier_interpreter_pars['max-value']['B']=sample_acceptable_max
#        thellier_interpreter_pars['max-value']['std']=sample_acceptable_max_std
#        thellier_interpreter_pars['sample_int_interval_uT']=sample_int_interval_uT
#        thellier_interpreter_pars['sample_int_interval_perc']=sample_int_interval_perc
#
#        if N < int_n_cutoff:
#           thellier_interpreter_pars['pass_or_fail']='fail'
#           thellier_interpreter_pars['fail_criteria'].append("int_n")
#
#        
#                
#        pass_int_sigma,pass_int_sigma_perc=True,True
#        pass_int_interval,pass_int_interval_perc=True,True
#        
#
#        if not (int_sigma_cutoff==-999 and int_sigma_perc_cutoff)==-999:
#            if  best_std<=int_sigma_cutoff*1e6 and int_sigma_cutoff!=-999:
#                pass_sigma=True
#            else:
#                pass_sigma=False
#            if  100.*(best_std/best_mean)<=int_sigma_perc_cutoff and int_sigma_perc_cutoff!=-999:
#                pass_sigma_perc=True
#            else:
#                pass_sigma_perc=False
#            if not (pass_sigma or pass_sigma_perc):
#                thellier_interpreter_pars['pass_or_fail']='fail'
#                thellier_interpreter_pars['fail_criteria'].append("int_sigma")
#
#        if not (int_interval_cutoff==-999 and int_interval_perc_cutoff)==-999:
#            if  sample_int_interval_uT<=int_interval_perc_cutoff and int_interval_perc_cutoff!=-999:
#                pass_interval=True
#            else:
#                pass_interval=False
#            if  sample_int_interval_perc<=int_interval_perc_cutoff and int_interval_perc_cutoff!=-999:
#                pass_interval_perc=True
#            else:
#                pass_interval_perc=False
#            if not (pass_interval or pass_interval_perc):
#                thellier_interpreter_pars['pass_or_fail']='fail'
#                thellier_interpreter_pars['fail_criteria'].append("int_interval")
#                
#                        
#
#                
#        return(thellier_interpreter_pars )
#           
#                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       
#    def on_menu_run_interpreter(self, event):
#
#        """
#        Run thellier_auto_interpreter
#        """
#
#        import random
#        import copy
#        
#
#
#        start_time=time.time()
#        #------------------------------------------------
#        # Clean work directory
#        #------------------------------------------------
#
#        #self.write_acceptance_criteria_to_file()
#        try:
#            shutil.rmtree(self.WD+"/thellier_interpreter")
#        except:
#            pass
#
#        try:
#            os.mkdir(self.WD+"/thellier_interpreter")
#        except:
#            pass
#
#
#        #------------------------------------------------
#        # Intialize interpreter output files:
#        # Prepare header for "Thellier_auto_interpretation.all.txt" 
#        # All the acceptable interpretation are saved in this file
#        #------------------------------------------------
#
#        # sort acceptance criteria
#        specimen_criteria=[]
#        for crit in self.acceptance_criteria.keys():
#            if 'category' in self.acceptance_criteria[crit].keys():
#                if self.acceptance_criteria[crit]['category']=="IE-SPEC":
#                    if self.acceptance_criteria[crit]['value']!=-999:
#                        specimen_criteria.append(crit)
#
#                                        
#        # sort acceptance criteria
#        sample_criteria=[]
#        for crit in self.acceptance_criteria.keys():
#            if 'category' in self.acceptance_criteria[crit].keys():
#                if self.acceptance_criteria[crit]['category']=="IE-SAMP":
#                    if self.acceptance_criteria[crit]['value']!=-999:
#                        sample_criteria.append(crit)
#
#        # sort acceptance criteria
#        site_criteria=[]
#        for crit in self.acceptance_criteria.keys():
#            if 'category' in self.acceptance_criteria[crit].keys():
#                if self.acceptance_criteria[crit]['category']=="thellier_gui":
#                    if self.acceptance_criteria[crit]['value']!=-999:
#                        site_criteria.append(crit)
#
#        # sort acceptance criteria
#        thellier_gui_criteria=[]
#        for crit in self.acceptance_criteria.keys():
#            if 'category' in self.acceptance_criteria[crit].keys():
#                if self.acceptance_criteria[crit]['category']=="thellier_gui":
#                    if self.acceptance_criteria[crit]['value']!=-999:
#                        thellier_gui_criteria.append(crit)
#                                        
#        #----------------------------
#                                                                    
#        # log file
#        thellier_interpreter_log=open(self.WD+"/"+"/thellier_interpreter//thellier_interpreter.log",'w')
#        thellier_interpreter_log.write("-I- Start auto interpreter\n")
#
#        # "all grade A interpretation
#        thellier_interpreter_all=open(self.WD+"/thellier_interpreter/thellier_interpreter_all.txt",'w')
#        thellier_interpreter_all.write("tab\tpmag_specimens\n")
#        String="er_specimen_name\tmeasurement_step_min\tmeasurement_step_max\tspecimen_lab_field_dc_uT\tspecimen_int_corr_anisotropy\tspecimen_int_corr_nlt\tspecimen_int_corr_cooling_rate\tspecimen_int_uT\t"
#        for crit in specimen_criteria: #+ ["specimen_b"] + ['specimen_cm_x'] + ['specimen_cm_y']:
#            String=String+crit+"\t"
#        String=String[:-1]+"\n"
#        thellier_interpreter_all.write(String)
#
#        #specimen_bound
#        Fout_specimens_bounds=open(self.WD+"/thellier_interpreter/thellier_interpreter_specimens_bounds.txt",'w')
#        String="acceptance criteria:\n"
#        for crit in specimen_criteria:
#                String=String+crit+"\t"
#        Fout_specimens_bounds.write(String[:-1]+"\n")
#        String=""
#        for crit in specimen_criteria:
#            if type(self.acceptance_criteria[crit]['value'])==str:
#                string=self.acceptance_criteria[crit]['value']
#            elif type(self.acceptance_criteria[crit]['value'])==bool:
#                string=str(self.acceptance_criteria[crit]['value'])
#            elif type(self.acceptance_criteria[crit]['value'])==int or type(self.acceptance_criteria[crit]['value'])==float:
#                if self.acceptance_criteria[crit]['decimal_points']==-999:
#                  string="%.3e"%(float(self.acceptance_criteria[crit]['value']))
#                else:
#                    command=  "string='%%.%if'%%(self.acceptance_criteria[crit]['value'])"%int(self.acceptance_criteria[crit]['decimal_points'])
#                    exec command
#            else:
#                string=""
#                
#            String=String+"%s\t"%string               
#        Fout_specimens_bounds.write(String[:-1]+"\n")
#        
#        Fout_specimens_bounds.write("--------------------------------\n")
#        Fout_specimens_bounds.write("er_sample_name\ter_specimen_name\tspecimen_int_corr_anisotropy\tAnisotropy_code\tspecimen_int_corr_nlt\tspecimen_int_corr_cooling_rate\tspecimen_lab_field_dc_uT\tspecimen_int_min_uT\tspecimen_int_max_uT\tWARNING\n")
#
#
#        #----------------------------------
#        
#        criteria_string="acceptance criteria:\n"
#        for crit in specimen_criteria + sample_criteria + site_criteria + thellier_gui_criteria:
#            criteria_string=criteria_string+crit+"\t"
#        criteria_string=criteria_string[:-1]+"\n"
#        for crit in specimen_criteria + sample_criteria + site_criteria + thellier_gui_criteria:
#            if type(self.acceptance_criteria[crit]['value'])==str:
#                string=self.acceptance_criteria[crit]['value']
#            elif type(self.acceptance_criteria[crit]['value'])==bool:
#                string=str(self.acceptance_criteria[crit]['value'])
#            elif type(self.acceptance_criteria[crit]['value'])==int or type(self.acceptance_criteria[crit]['value'])==float:
#                if self.acceptance_criteria[crit]['decimal_points']==-999:
#                  string="%.3e"%(float(self.acceptance_criteria[crit]['value']))
#                else:
#                    command=  "string='%%.%if'%%(self.acceptance_criteria[crit]['value'])"%int(self.acceptance_criteria[crit]['decimal_points'])
#                    exec command
#            else:
#                string=""
#                
#            criteria_string=criteria_string+"%s\t"%string                       
#        criteria_string=criteria_string[:-1]+"\n"
#        criteria_string=criteria_string+"---------------------------------\n"
#        
#               
#        # STDEV-OPT output files
#        if self.acceptance_criteria['interpreter_method']['value']=='stdev_opt':
#            Fout_STDEV_OPT_redo=open(self.WD+"/thellier_interpreter/thellier_interpreter_STDEV-OPT_redo",'w')
#            Fout_STDEV_OPT_specimens=open(self.WD+"/thellier_interpreter/thellier_interpreter_STDEV-OPT_specimens.txt",'w')
#
#            Fout_STDEV_OPT_specimens.write("tab\tpmag_specimens\n")
#            String="er_sample_name\ter_specimen_name\tspecimen_int_uT\tmeasurement_step_min\tmeasurement_step_min\tspecimen_lab_field_dc\tAnisotropy_correction_factor\tNLT_correction_factor\tCooling_rate_correction_factor\t"
#            for crit in specimen_criteria:
#                String=String+crit+"\t"        
#            Fout_STDEV_OPT_specimens.write(String[:-1]+"\n")
#
#            if self.acceptance_criteria['average_by_sample_or_site']['value']=='sample':
#                Fout_STDEV_OPT_samples=open(self.WD+"/thellier_interpreter/thellier_interpreter_STDEV-OPT_samples.txt",'w')
#                Fout_STDEV_OPT_samples.write(criteria_string)
#                Fout_STDEV_OPT_samples.write("er_sample_name\tsample_int_n\tsample_int_uT\tsample_int_sigma_uT\tsample_int_sigma_perc\tsample_int_min_uT\tsample_int_min_sigma_uT\tsample_int_max_uT\tsample_int_max_sigma_uT\tsample_int_interval_uT\tsample_int_interval_perc\tWarning\n")
#            else:
#                Fout_STDEV_OPT_sites=open(self.WD+"/thellier_interpreter/thellier_interpreter_STDEV-OPT_sites.txt",'w')
#                Fout_STDEV_OPT_sites.write(criteria_string)
#                Fout_STDEV_OPT_sites.write("er_site_name\tsite_int_n\tsite_int_uT\tsite_int_sigma_uT\tsite_int_sigma_perc\tsite_int_min_uT\tsite_int_min_sigma_uT\tsite_int_max_uT\tsite_int_max_sigma_uT\tsite_int_interval_uT\tsite_int_interval_perc\tWarning\n")
#                
#        # simple bootstrap output files
#        # Dont supports site yet!
# 
#        if self.acceptance_criteria['interpreter_method']['value']=='bs':
#           Fout_BS_samples=open(self.WD+"/thellier_interpreter/thellier_interpreter_BS_samples.txt",'w')
#           Fout_BS_samples.write(criteria_string)
#           #Fout_BS_samples.write("---------------------------------\n")
#           Fout_BS_samples.write("er_sample_name\tsample_int_n\tsample_int_uT\tsample_int_68_low\tsample_int_68_high\tsample_int_95_low\tsample_int_95_high\tsample_int_sigma_uT\tsample_int_sigma_perc\tWARNING\n")
#        # parameteric bootstrap output files
#
#        if self.acceptance_criteria['interpreter_method']['value']=='bs_par':
#           Fout_BS_PAR_samples=open(self.WD+"/thellier_interpreter/thellier_interpreter_BS-PAR_samples.txt",'w')
#           Fout_BS_PAR_samples.write(criteria_string) 
#           #Fout_BS_PAR_samples.write("---------------------------------\n")
#           Fout_BS_PAR_samples.write("er_sample_name\tsample_int_n\tsample_int_uT\tsample_int_68_low\tsample_int_68_high\tsample_int_95_low\tsample_int_95_high\tsample_int_sigma_uT\tsample_int_sigma_perc\tWARNING\n")
#           
#        thellier_interpreter_log.write("-I- using paleointenisty statistics:\n")
#        thellier_interpreter_log.write(criteria_string)
#                                
#        
#        #------------------------------------------------
#
#        busy_frame=wx.BusyInfo("Running Thellier auto interpreter\n It may take several minutes depending on the number of specimens ...", self)
#
#        specimens_list=self.Data.keys()
#        specimens_list.sort()
#        thellier_interpreter_log.write("-I- Found %i specimens\n"%(len(specimens_list)))
#
#        #try:
#        All_grade_A_Recs={}
#        for s in specimens_list:
#            thellier_interpreter_log.write("-I- doing now specimen %s\n"%s)
#            self.Data[s]['pars']={}
#            self.Data[s]['pars']['lab_dc_field']=self.Data[s]['lab_dc_field']
#            self.Data[s]['pars']['er_specimen_name']=s
#            self.Data[s]['pars']['er_sample_name']=self.Data_hierarchy['specimens'][s]
#            temperatures=self.Data[s]['t_Arai']
#            
#            # check that all temperatures are in right order:
#            ignore_specimen=False
#            for t in range(len(temperatures)-1):
#                if float(temperatures[t+1])<float(temperatures[t]):
#                    thellier_interpreter_log.write("-W- Found problem in the temperature order of specimen %s. skipping specimen\n"%(s))
#                    ignore_specimen=True
#            if ignore_specimen:
#                continue
#            if self.acceptance_criteria['specimen_int_n']['value'] != -999:
#                specimen_int_n=min(3,int(self.acceptance_criteria['specimen_int_n']['value']))
#            else:
#                specimen_int_n=3
#            #-------------------------------------------------            
#            # loop through all possible tmin,tmax and check if pass criteria
#            #-------------------------------------------------
#            #print s
#            for tmin_i in range(len(temperatures)-specimen_int_n+1):
#                # check if to include NRM
#                #print temperatures
#                #print  self.acceptance_criteria['include_nrm']['value']
#                if self.acceptance_criteria['include_nrm']['value']==-999:
#                    #print " Its False"
#                    if temperatures[tmin_i]==273:
#                        continue
#                    #    print "ignoring NRM",tmin_i,temperatures[tmin_i]
#                #print tmin_i
#                for tmax_i in range(tmin_i+specimen_int_n-1,len(temperatures)):
#                    #print tmax_i
#                    #print len(temperatures)
#                    tmin=temperatures[tmin_i]
#                    tmax=temperatures[tmax_i]
#                    pars=self.get_PI_parameters(s,tmin,tmax)
#                    if not pars: # error with getting pars
#                        message_string = '-W- Problem in SPD. Could not calculate any parameters for {} with tmin: {} and tmax {}. Check data for typos, make sure temperatures are correct, etc.'.format(s, tmin, tmax)
#                        thellier_interpreter_log.write(message_string+"\n")
#                        continue
#                    if 'NLT_specimen_correction_factor' not in pars.keys():
#                        # problem in get_PI_parameters (probably with tmin/zdata).  can't run specimen
#                        message_string = '-W- Problem in get_PI_parameters. Could not get all parameters for {} with tmin: {} and tmax: {}. Check data for typos, make sure temperatures are correct, etc.'.format(s, tmin, tmax)
#                        thellier_interpreter_log.write(message_string+"\n")
#                        continue
#                    pars=self.check_specimen_PI_criteria(pars)
#                    #-------------------------------------------------            
#                    # check if pass the criteria
#                    #-------------------------------------------------
#
#                    if  'specimen_fail_criteria' in pars.keys() and len(pars['specimen_fail_criteria'])>0:
#                        # Fail:
#                        message_string= "-I- specimen %s (%.0f-%.0f) FAIL on: "%(s,float(pars["measurement_step_min"])-273, float(pars["measurement_step_max"])-273)
#                        for parameter in pars['specimen_fail_criteria']:
#                            if "scat" not in parameter:
#                                message_string=message_string+parameter + "= %f,  "%pars[parameter]
#                            else:
#                                message_string=message_string+parameter + "= %s,  "%str(pars[parameter])
#                                
#                        thellier_interpreter_log.write(message_string+"\n")        
#                    elif 'specimen_fail_criteria' in pars.keys() and len(pars['specimen_fail_criteria'])==0:
#
#                        # PASS:
#                        message_string = "-I- specimen %s (%.0f-%.0f) PASS"%(s,float(pars["measurement_step_min"])-273, float(pars["measurement_step_max"])-273)
#                        thellier_interpreter_log.write(message_string+"\n")
#                        
#                        #--------------------------------------------------------------
#                        # Save all the grade A interpretation in thellier_interpreter_all.txt
#                        #--------------------------------------------------------------
#
#                        String=s+"\t"
#                        String=String+"%.0f\t"%(float(pars["measurement_step_min"])-273.)
#                        String=String+"%.0f\t"%(float(pars["measurement_step_max"])-273.)
#                        String=String+"%.0f\t"%(float(pars["lab_dc_field"])*1e6)
#
#                        if "Anisotropy_correction_factor" in pars.keys():
#                           String=String+"%.2f\t"%float(pars["Anisotropy_correction_factor"])
#                        else:
#                           String=String+"-\t"
#                        if  float(pars["NLT_specimen_correction_factor"])!=-999:
#                           String=String+"%.2f\t"%float(pars["NLT_specimen_correction_factor"])
#                        else:
#                           String=String+"-\t"
#                        if  float(pars["specimen_int_corr_cooling_rate"])!=-999 and float(pars["specimen_int_corr_cooling_rate"])!=-1 :
#                           String=String+"%.2f\t"%float(pars["specimen_int_corr_cooling_rate"])
#                        else:
#                           String=String+"-\t"
#                        Bancient=float(pars['specimen_int_uT'])
#                        String=String+"%.1f\t"%(Bancient)
#                        for key in specimen_criteria:# + ["specimen_b"] + ["specimen_cm_x"] + ["specimen_cm_y"]:
#                           if type( pars[key])==str:
#                            String=String+pars[key]+"\t"                               
#                           else: 
#                            String=String+"%.3e"%(float(pars[key]))+"\t"
#                        String=String[:-1]+"\n"
#
#                        thellier_interpreter_all.write(String)
#
#
#                        #-------------------------------------------------                    
#                        # save 'acceptable' (grade A) specimen interpretaion
#                        # All_grade_A_Recs={}
#                        # All_grade_A_Recs[specimen_name]["tmin,tmax"]={PI pars sorted in dictionary}
#                        #-------------------------------------------------
#                        
#                        if s not in All_grade_A_Recs.keys():
#                           All_grade_A_Recs[s]={}
#                        new_pars={}
#                        for k in pars.keys():
#                            new_pars[k]=pars[k]
#                        TEMP="%.0f,%.0f"%(float(pars["measurement_step_min"])-273,float(pars["measurement_step_max"])-273)
#                        All_grade_A_Recs[s][TEMP]=new_pars
#
#
#        specimens_list=All_grade_A_Recs.keys()
#        specimens_list.sort()
#        Grade_A_samples={}
#        Grade_A_sites={}
#        Redo_data_specimens={}
#        
#        #--------------------------------------------------------------
#        # specimens bound file
#        #--------------------------------------------------------------
#
#        for s in specimens_list:
#
#            sample=self.Data_hierarchy['specimens'][s]
#            site=thellier_gui_lib.get_site_from_hierarchy(sample,self.Data_hierarchy)
#            B_lab=float(self.Data[s]['lab_dc_field'])*1e6
#            B_min,B_max=1e10,0.
#            NLT_factor_min,NLT_factor_max=1e10,0.
#            all_B_tmp_array=[]
#
#            for TEMP in All_grade_A_Recs[s].keys():
#                pars=All_grade_A_Recs[s][TEMP]
#                if "AC_anisotropy_type" in pars.keys():
#                    AC_correction_factor=pars["Anisotropy_correction_factor"]
#                    AC_correction_type=pars["AC_anisotropy_type"]
#                    WARNING=""
#                    if "AC_WARNING" in pars.keys():
#                        WARNING=WARNING+pars["AC_WARNING"]
#                else:
#                    AC_correction_factor=1.
#                    AC_correction_type="-"
#                    WARNING="WARNING: No anisotropy correction"
#                
#                B_anc=pars['specimen_int_uT']
#                    
#                if B_anc< B_min:
#                    B_min=B_anc
#                if B_anc > B_max:
#                    B_max=B_anc
#                if pars["NLT_specimen_correction_factor"]!=-1:
#                    NLT_f=pars['NLT_specimen_correction_factor']
#                    if NLT_f< NLT_factor_min:
#                        NLT_factor_min=NLT_f
#                    if NLT_f > NLT_factor_max:
#                        NLT_factor_max=NLT_f                
#
#                # sort by samples
#                #--------------------------------------------------------------
#                
#                if sample not in Grade_A_samples.keys():
#                    Grade_A_samples[sample]={}
#                if s not in Grade_A_samples[sample].keys() and len(All_grade_A_Recs[s])>0:
#                    Grade_A_samples[sample][s]=[]
#
#                Grade_A_samples[sample][s].append(B_anc)                
#
#                # sort by sites
#                #--------------------------------------------------------------
#                
#                if site not in Grade_A_sites.keys():
#                    Grade_A_sites[site]={}
#                if s not in Grade_A_sites[site].keys() and len(All_grade_A_Recs[s])>0:
#                    Grade_A_sites[site][s]=[]
#                Grade_A_sites[site][s].append(B_anc)                
#
#                # ? check
#                #--------------------------------------------------------------
#
#                if s not in Redo_data_specimens.keys():
#                    Redo_data_specimens[s]={}
#
#            # write to specimen_bounds
#            #--------------------------------------------------------------
#
#            if pars["NLT_specimen_correction_factor"] != -1:
#                NLT_factor="%.2f"%(NLT_factor_max)
#            else:
#                NLT_factor="-"
#
#            if pars["specimen_int_corr_cooling_rate"] != -1 and pars["specimen_int_corr_cooling_rate"] != -999:
#                CR_factor="%.2f"%(float(pars["specimen_int_corr_cooling_rate"]))
#            else:
#                CR_factor="-"
#            if 'cooling_rate_data' in  self.Data[s].keys():
#                if 'CR_correction_factor_flag' in  self.Data[s]['cooling_rate_data'].keys():
#                    if self.Data[s]['cooling_rate_data']['CR_correction_factor_flag'] != "calculated":
#                        if "inferred" in self.Data[s]['cooling_rate_data']['CR_correction_factor_flag']:
#                            WARNING=WARNING+";"+"cooling rate correction inferred from sister specimens"
#                        if "alteration" in self.Data[s]['cooling_rate_data']['CR_correction_factor_flag']:
#                            WARNING=WARNING+";"+"cooling rate experiment failed alteration"
#                        if "bad" in self.Data[s]['cooling_rate_data']['CR_correction_factor_flag']:
#                            WARNING=WARNING+";"+"cooling rate experiment failed"
#                
#            if AC_correction_type =="-":
#                AC_correction_factor_to_print="-"
#            else:
#                AC_correction_factor_to_print="%.2f"%AC_correction_factor
#            
#            String="%s\t%s\t%s\t%s\t%s\t%s\t%.1f\t%.1f\t%.1f\t%s\n"\
#                    %(sample,s,AC_correction_factor_to_print,AC_correction_type,NLT_factor,CR_factor,B_lab,B_min,B_max,WARNING)
#            Fout_specimens_bounds.write(String)
#
#
#        #--------------------------------------------------------------
#        # Find the STDEV-OPT 'best mean':
#        # the interprettaions that give
#        # the minimum standrad deviation (perc!)
#        # not nesseserily the standrad deviation in microT
#        #
#        #--------------------------------------------------------------
#
#        # Sort all grade A interpretation
#
#        samples=Grade_A_samples.keys()
#        samples.sort()
#
#        sites=Grade_A_sites.keys()
#        sites.sort()
#
#        #--------------------------------------------------------------        
#        # clean workspace: delete all previous interpretation
#        #--------------------------------------------------------------
#       
#        for sp in self.Data.keys():
#            del self.Data[sp]['pars']
#            self.Data[sp]['pars']={}
#            self.Data[sp]['pars']['lab_dc_field']=self.Data[sp]['lab_dc_field']
#            self.Data[sp]['pars']['er_specimen_name']=self.Data[sp]['er_specimen_name']   
#            self.Data[sp]['pars']['er_sample_name']=self.Data[sp]['er_sample_name']
#        self.Data_samples={}
#        self.Data_sites={}
#        interpreter_redo={}
#
#        #--------------------------------------------------------------        
#        # STDEV can work by averaging specimens by sample (default)
#        # or by averaging specimens by site
#        #--------------------------------------------------------------
#
#                
#        if self.acceptance_criteria['average_by_sample_or_site']['value']=='sample':
#            Grade_A_sorted=copy.deepcopy(Grade_A_samples)
#             
#        else:
#            Grade_A_sorted=copy.deepcopy(Grade_A_sites)
#
#        #--------------------------------------------------------------
#        # check for anistropy issue:
#        # If the average anisotropy correction in the sample is larger than a threshold value
#        # and there are enough good specimens with anisotropy correction to pass sample's criteria
#        # then dont use the uncorrected specimens for sample's calculation. 
#        #--------------------------------------------------------------
#        
#        samples_or_sites=Grade_A_sorted.keys()
#        samples_or_sites.sort()
#        #print Grade_A_sorted
#        for sample_or_site in samples_or_sites:
#            if self.acceptance_criteria['average_by_sample_or_site']['value']=='sample':
#                aniso_mean_cutoff = self.acceptance_criteria['sample_aniso_mean']['value']
#            else:
#                aniso_mean_cutoff = self.acceptance_criteria['site_aniso_mean']['value']
#                                
#            if aniso_mean_cutoff != -999:
#                if self.acceptance_criteria['average_by_sample_or_site']['value']=='sample':
#                    int_n = self.acceptance_criteria['sample_int_n']['value']
#                else:
#                    int_n = self.acceptance_criteria['site_int_n']['value']
#                if len(Grade_A_sorted[sample_or_site].keys())>int_n:
#                    aniso_corrections=[]
#                    for specimen in Grade_A_sorted[sample_or_site].keys():
#                        AC_correction_factor_1=0
#                        for k in All_grade_A_Recs[specimen].keys():
#                            pars=All_grade_A_Recs[specimen][k]
#                            if "AC_anisotropy_type" in pars.keys():
#                                if "AC_WARNING" in pars.keys():
#                                    if "TRM" in pars["AC_WARNING"] and pars["AC_anisotropy_type"]== "ATRM" and "alteration" in pars["AC_WARNING"]:
#                                        continue
#                                    AC_correction_factor_1=max(AC_correction_factor,100*abs(1.-pars["Anisotropy_correction_factor"]))
#                        if AC_correction_factor_1!=0:
#                            aniso_corrections.append(AC_correction_factor_1)
#                    if aniso_corrections!=[]:
#                        thellier_interpreter_log.write("sample_or_site %s have anisotropy factor mean of %f\n"%(sample_or_site,scipy.mean(aniso_corrections)))
#
#                    if scipy.mean(aniso_corrections) > aniso_mean_cutoff:
#                        tmp_Grade_A_sorted=copy.deepcopy(Grade_A_sorted)
#                        warning_messeage=""
#                        WARNING_tmp=""
#                        #print "sample %s have anisotropy factor mean of %f"%(sample,scipy.mean(aniso_corrections))
#                        for specimen in Grade_A_sorted[sample_or_site].keys():
#                            ignore_specimen=False
#                            intenstities=All_grade_A_Recs[specimen].keys()
#                            pars=All_grade_A_Recs[specimen][intenstities[0]]
#                            if "AC_anisotropy_type" not in pars.keys():
#                                ignore_specimen=True
#                                warning_messeage = warning_messeage + "-W- WARNING: specimen %s is exluded from sample %s because it doesnt have anisotropy correction, and other specimens are very anistropic\n"%(specimen,sample_or_site)
#                            elif "AC_WARNING" in pars.keys():
#                                #if "alteration check" in pars["AC_WARNING"]:
#                                    if pars["AC_anisotropy_type"]== "ATRM" and "TRM" in pars["AC_WARNING"] and  "alteration" in pars["AC_WARNING"]  : 
#                                       #or "ARM" in pars["AC_WARNING"] and  pars["AC_anisotropy_type"]== "AARM":
#                                        ignore_specimen=True
#                                        warning_messeage = warning_messeage + "-W- WARNING: specimen %s is exluded from sample %s because it failed ATRM alteration check and other specimens are very anistropic\n"%(specimen,sample_or_site)
#                            if ignore_specimen: 
#                                
#                                WARNING_tmp=WARNING_tmp+"excluding specimen %s; "%(specimen)
#                                del tmp_Grade_A_sorted[sample_or_site][specimen]
#
#                                
#                        #--------------------------------------------------------------
#                        # calculate the STDEV-OPT best mean (after possible ignoring of specimens with bad anisotropy)
#                        # and check if pass after ignoring problematic anistopry specimens 
#                        # if pass: delete the problematic specimens from Grade_A_sorted
#                        #--------------------------------------------------------------
#                        
#                        thellier_interpreter_pars=self.thellier_interpreter_pars_calc(tmp_Grade_A_sorted[sample_or_site])
#                        if thellier_interpreter_pars['pass_or_fail']=='pass':
#                            Grade_A_sorted[sample_or_site]=copy.deepcopy(tmp_Grade_A_sorted[sample_or_site])
#                            WARNING=WARNING_tmp
#                            thellier_interpreter_log.write(warning_messeage)
#                        else:
#                            Grade_A_sorted[sample_or_site]=copy.deepcopy(tmp_Grade_A_sorted[sample_or_site])
#                            WARNING=WARNING_tmp + "; sample fail criteria"
#                            thellier_interpreter_log.write(warning_messeage)
#                            
#
#                                
#            #--------------------------------------------------------------
#            # check for outlier specimens
#            # Outlier check is done only if
#            # (1) number of specimen >= acceptance_criteria['sample_int_n_outlier_check']
#            # (2) an outlier exists if one (and only one!) specimen has an outlier result defined
#            # by:
#            # Bmax(specimen_1) < mean[max(specimen_2),max(specimen_3),max(specimen_3)...] - 2*sigma
#            # or
#            # Bmin(specimen_1) < mean[min(specimen_2),min(specimen_3),min(specimen_3)...] + 2*sigma
#            # (3) 2*sigma > 5 microT
#            #--------------------------------------------------------------
#
#            WARNING=""
#            # check for outlier specimen
#            exclude_specimen=""
#            exclude_specimens_list=[]
#            if self.acceptance_criteria['average_by_sample_or_site']['value']=='sample':
#               int_n_outlier_check=self.acceptance_criteria['sample_int_n_outlier_check']['value']
#            else:
#               int_n_outlier_check=self.acceptance_criteria['site_int_n_outlier_check']['value']
#            if int_n_outlier_check==-999:
#                 int_n_outlier_check=9999   
#               
#            if len(Grade_A_sorted[sample_or_site].keys())>=int_n_outlier_check:
#                thellier_interpreter_log.write( "-I- check outlier for sample %s \n"%sample)
#                all_specimens=Grade_A_sorted[sample_or_site].keys()
#                for specimen in all_specimens:
#                    B_min_array,B_max_array=[],[]
#                    for specimen_b in all_specimens:
#                        if specimen_b==specimen: continue
#                        B_min_array.append(min(Grade_A_sorted[sample_or_site][specimen_b]))
#                        B_max_array.append(max(Grade_A_sorted[sample_or_site][specimen_b]))
#                    if max(Grade_A_sorted[sample_or_site][specimen]) < (scipy.mean(B_min_array) - 2*std(B_min_array,ddof=1)):# and 2*std(B_min_array,ddof=1) >3.:
#                        if specimen not in exclude_specimens_list:
#                            exclude_specimens_list.append(specimen)
#                    if min(Grade_A_sorted[sample_or_site][specimen]) > (scipy.mean(B_max_array) + 2*std(B_max_array,ddof=1)):# and 2*std(B_max_array,ddof=1) >3 :
#                           if specimen not in exclude_specimens_list:
#                            exclude_specimens_list.append(specimen)
#                         
#                if len(exclude_specimens_list)>1:
#                    thellier_interpreter_log.write( "-I- specimen %s outlier check: more than one specimen can be outlier. first ones are : %s,%s... \n" %(sample,exclude_specimens_list[0],exclude_specimens_list[1]))
#                    exclude_specimens_list=[]
#
#                if len(exclude_specimens_list)==1 :
#                    #print exclude_specimens_list
#                    exclude_specimen=exclude_specimens_list[0]
#                    del Grade_A_sorted[sample_or_site][exclude_specimen]
#                    thellier_interpreter_log.write( "-W- WARNING: specimen %s is exluded from sample %s because of an outlier result.\n"%(exclude_specimens_list[0],sample))
#                    WARNING=WARNING+"excluding specimen %s; "%(exclude_specimens_list[0])
#
#           
#            #--------------------------------------------------------------
#            #  display all the specimens that passes criteria  after the interpreter ends running.
#            #--------------------------------------------------------------
#
#
#            # if only one specimen pass take the interpretation with maximum frac
#            
#            if len(Grade_A_sorted[sample_or_site].keys()) == 1:
#                specimen=Grade_A_sorted[sample_or_site].keys()[0]
#                frac_max=0
#                for TEMP in All_grade_A_Recs[specimen].keys():
#                    if All_grade_A_Recs[specimen][TEMP]['specimen_frac']>frac_max:
#                        best_intensity=All_grade_A_Recs[specimen][TEMP]['specimen_int_uT']
#                for TEMP in All_grade_A_Recs[specimen].keys():                        
#                    if All_grade_A_Recs[specimen][TEMP]['specimen_int_uT']==best_intensity:
#                        self.Data[specimen]['pars'].update(All_grade_A_Recs[specimen][TEMP])
#                        self.Data[specimen]['pars']['saved']=True
#                        sample=self.Data_hierarchy['specimens'][specimen]
#                        if sample not in self.Data_samples.keys():
#                          self.Data_samples[sample]={}
#                        if specimen not in self.Data_samples[sample].keys():
#                          self.Data_samples[sample][specimen]={}
#                            
#                        self.Data_samples[sample][specimen]['B']=self.Data[specimen]['pars']['specimen_int_uT']
#
#                        site=thellier_gui_lib.get_site_from_hierarchy(sample,self.Data_hierarchy)
#                        if site not in self.Data_sites.keys():
#                          self.Data_sites[site]={}
#                        if specimen not in self.Data_sites[site].keys():
#                          self.Data_sites[site][specimen]={}
#                        self.Data_sites[site][specimen]['B']=self.Data[specimen]['pars']['specimen_int_uT']
#
#                                                
#            if len(Grade_A_sorted[sample_or_site].keys()) > 1:
#                thellier_interpreter_pars=self.thellier_interpreter_pars_calc(Grade_A_sorted[sample_or_site])
#                Best_interpretations,best_mean,best_std=self.find_sample_min_std(Grade_A_sorted[sample_or_site])
#                for specimen in Grade_A_sorted[sample_or_site].keys():
#                    for TEMP in All_grade_A_Recs[specimen].keys():
#                        if All_grade_A_Recs[specimen][TEMP]['specimen_int_uT']==thellier_interpreter_pars['stdev_opt_interpretations'][specimen]:    #Best_interpretations[specimen]:
#                            self.Data[specimen]['pars'].update(All_grade_A_Recs[specimen][TEMP])
#                            self.Data[specimen]['pars']['saved']=True
#                            sample=self.Data_hierarchy['specimens'][specimen]
#                            if sample not in self.Data_samples.keys():
#                              self.Data_samples[sample]={}
#                            if specimen not in self.Data_samples[sample].keys():
#                              self.Data_samples[sample][specimen]={}
#                            self.Data_samples[sample][specimen]['B']=self.Data[specimen]['pars']['specimen_int_uT']
#                            site=thellier_gui_lib.get_site_from_hierarchy(sample,self.Data_hierarchy)
#                            if site not in self.Data_sites.keys():
#                                self.Data_sites[site]={}
#                            if specimen not in self.Data_sites.keys():
#                              self.Data_sites[site][specimen]={}
#                            self.Data_sites[site][specimen]['B']=self.Data[specimen]['pars']['specimen_int_uT']
#                            
#
#             #--------------------------------------------------------------
#             # check if ATRM and cooling rate data exist
#             #--------------------------------------------------------------
#
#
#            if self.acceptance_criteria['interpreter_method']['value']=='stdev_opt':
#                n_anistropy=0
#                n_anistropy_fail=0
#                n_anistropy_pass=0
#                for specimen in Grade_A_sorted[sample_or_site].keys():
#                    if "AniSpec" in self.Data[specimen].keys():
#                        n_anistropy+=1
#                        if 'pars' in self.Data[specimen].keys() and "AC_WARNING" in  self.Data[specimen]['pars'].keys():
#                            #if "F-test" in self.Data[specimen]['pars']["AC_WARNING"] \
#                            if  self.Data[specimen]['pars']["AC_anisotropy_type"]=='ATRM' and "alteration" in self.Data[specimen]['pars']["AC_WARNING"]:
#                                n_anistropy_fail+=1
#                            else:
#                                n_anistropy_pass+=1
#                               
#                                 
#                            
#                no_cooling_rate=True
#                n_cooling_rate=0
#                n_cooling_rate_pass=0
#                n_cooling_rate_fail=0
#                
#                for specimen in Grade_A_sorted[sample_or_site].keys():
#                        if "cooling_rate_data" in self.Data[specimen].keys():
#                            n_cooling_rate+=1
#                            if "CR_correction_factor" in self.Data[specimen]["cooling_rate_data"].keys():
#                                if self.Data[specimen]["cooling_rate_data"]["CR_correction_factor"]!= -1 and self.Data[specimen]["cooling_rate_data"]["CR_correction_factor"]!= -999:
#                                    no_cooling_rate=False
#                                if 'CR_correction_factor_flag' in self.Data[specimen]["cooling_rate_data"].keys():
#                                    if 'calculated' in self.Data[specimen]['cooling_rate_data']['CR_correction_factor_flag']:
#                                        n_cooling_rate_pass+=1
#                                    elif 'failed'  in self.Data[specimen]['cooling_rate_data']['CR_correction_factor_flag']:
#                                        n_cooling_rate_fail+=1 
#                                
# 
#             #--------------------------------------------------------------
#             # calcuate STDEV-OPT 'best means' and write results to files
#             #--------------------------------------------------------------
#                if len(Grade_A_sorted[sample_or_site].keys()) > 1 and "int_n" not in thellier_interpreter_pars['fail_criteria']:
#                #if len(Grade_A_sorted[sample_or_site].keys())>=self.acceptance_criteria['sample_int_n'] and len(Grade_A_sorted[sample_or_site].keys()) > 1:
#                    #Best_interpretations,best_mean,best_std=self.find_sample_min_std(Grade_A_sorted[sample_or_site])
#                    #sample_acceptable_min,sample_acceptable_min_std,sample_acceptable_max,sample_acceptable_max_std = self.find_sample_min_max_interpretation (Grade_A_sorted[sample_or_site],self.acceptance_criteria)
#                    #sample_int_interval_uT=sample_acceptable_max-sample_acceptable_min
#                    #sample_int_interval_perc=100*((sample_acceptable_max-sample_acceptable_min)/best_mean)       
#                    TEXT= "-I- sample %s 'STDEV-OPT interpretation: "%sample
#                    for ss in thellier_interpreter_pars['stdev_opt_interpretations'].keys():
#                        TEXT=TEXT+"%s=%.1f, "%(ss,thellier_interpreter_pars['stdev_opt_interpretations'][ss])
#                    thellier_interpreter_log.write(TEXT+"\n")
#                    thellier_interpreter_log.write("-I- sample %s STDEV-OPT mean=%f, STDEV-OPT std=%f \n"%(sample,thellier_interpreter_pars['stdev-opt']['B'],thellier_interpreter_pars['stdev-opt']['std']))
#                    thellier_interpreter_log.write("-I- sample %s STDEV-OPT minimum/maximum accepted interpretation  %.2f,%.2f\n" %(sample,thellier_interpreter_pars['min-value']['B'],thellier_interpreter_pars['max-value']['B']))
#
#
#                    # check if interpretation pass criteria for samples:
#                    #if ( self.acceptance_criteria['sample_int_sigma_uT'] ==0 and self.acceptance_criteria['sample_int_sigma_perc']==0 ) or \
#                    #   (best_std <= self.acceptance_criteria['sample_int_sigma_uT'] or 100*(best_std/best_mean) <= self.acceptance_criteria['sample_int_sigma_perc']):
#                    #    if sample_int_interval_uT <= self.acceptance_criteria['sample_int_interval_uT'] or sample_int_interval_perc <= self.acceptance_criteria['sample_int_interval_perc']:
#                    if thellier_interpreter_pars['pass_or_fail']=='pass':                
#                            # write the interpretation to a redo file
#                            for specimen in Grade_A_sorted[sample_or_site].keys():
#                                #print Redo_data_specimens[specimen]
#                                for TEMP in All_grade_A_Recs[specimen].keys():
#                                    if All_grade_A_Recs[specimen][TEMP]['specimen_int_uT']==thellier_interpreter_pars['stdev_opt_interpretations'][specimen]:
#                                        t_min=All_grade_A_Recs[specimen][TEMP]['measurement_step_min']
#                                        t_max=All_grade_A_Recs[specimen][TEMP]['measurement_step_max']
#                                        
#                                            
#                                        Fout_STDEV_OPT_redo.write("%s\t%i\t%i\n"%(specimen,t_min,t_max))
#
#                                    # write the interpretation to the specimen file
#                                        #B_lab=float(Redo_data_specimens[specimen][Best_interpretations[specimen]]['lab_dc_field'])*1e6
#                                        B_lab=float(All_grade_A_Recs[specimen][TEMP]['lab_dc_field'])*1e6
#                                        sample=All_grade_A_Recs[specimen][TEMP]['er_sample_name']
#                                        if "Anisotropy_correction_factor" in All_grade_A_Recs[specimen][TEMP].keys():
#                                            Anisotropy_correction_factor="%.2f"%(All_grade_A_Recs[specimen][TEMP]["Anisotropy_correction_factor"])
#                                            #AC_correction_type=pars["AC_anisotropy_type"]
#                                        #if 'AC_specimen_correction_factor' in All_grade_A_Recs[specimen][TEMP].keys():
#                                        #    Anisotropy_correction_factor="%.2f"%float(All_grade_A_Recs[specimen][TEMP]['AC_specimen_correction_factor'])
#                                        else:
#                                            Anisotropy_correction_factor="-"                
#                                        if  All_grade_A_Recs[specimen][TEMP]["NLT_specimen_correction_factor"] != -1:
#                                            NLT_correction_factor="%.2f"%float(All_grade_A_Recs[specimen][TEMP]['NLT_specimen_correction_factor'])
#                                        else:
#                                            NLT_correction_factor="-"
#
#                                        if  All_grade_A_Recs[specimen][TEMP]["specimen_int_corr_cooling_rate"] != -999 and All_grade_A_Recs[specimen][TEMP]["specimen_int_corr_cooling_rate"] != -1:
#                                            CR_correction_factor="%.2f"%float(All_grade_A_Recs[specimen][TEMP]['specimen_int_corr_cooling_rate'])
#                                        else:
#                                            CR_correction_factor="-"
#
#                                        Fout_STDEV_OPT_specimens.write("%s\t%s\t%.2f\t%i\t%i\t%.0f\t%s\t%s\t%s\t"\
#                                                             %(sample_or_site,specimen,float(thellier_interpreter_pars['stdev_opt_interpretations'][specimen]),t_min-273,t_max-273,B_lab,Anisotropy_correction_factor,NLT_correction_factor,CR_correction_factor))
#                                        String=""
#                                        for key in specimen_criteria:
#                                            if type(All_grade_A_Recs[specimen][TEMP][key])==str:
#                                                String=String+All_grade_A_Recs[specimen][TEMP][key]+"\t"
#                                            else:
#                                                String=String+"%.2f"%(All_grade_A_Recs[specimen][TEMP][key])+"\t"
#                                        Fout_STDEV_OPT_specimens.write(String[:-1]+"\n")
#                                                     
#                            # write the interpretation to the sample file
#                          
#                            if n_anistropy == 0:
#                                 WARNING=WARNING+"No anisotropy corrections; "
#                            else:    
#                                 WARNING=WARNING+"%i / %i specimens pass anisotropy criteria; "%(int(n_anistropy)-int(n_anistropy_fail),int(n_anistropy))
#                            
#                            if no_cooling_rate:
#                                 WARNING=WARNING+" No cooling rate corrections; "
#                            else:
#                                 WARNING=WARNING+ "%i / %i specimens pass cooling rate criteria ;"%(int(n_cooling_rate_pass),int(n_cooling_rate))
#                                                      
#                            String="%s\t%i\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.3f\t%.2f\t%.2f\t%s\n"%\
#                            (sample_or_site,len(thellier_interpreter_pars['stdev_opt_interpretations']),\
#                            thellier_interpreter_pars['stdev-opt']['B'],\
#                            thellier_interpreter_pars['stdev-opt']['std'],\
#                            thellier_interpreter_pars['stdev-opt']['std_perc'],\
#                            thellier_interpreter_pars['min-value']['B'],\
#                            thellier_interpreter_pars['min-value']['std'],\
#                            thellier_interpreter_pars['max-value']['B'],\
#                            thellier_interpreter_pars['max-value']['std'],\
#                            thellier_interpreter_pars['sample_int_interval_uT'],\
#                            thellier_interpreter_pars['sample_int_interval_perc'],\
#                            WARNING)
#                            if self.acceptance_criteria['average_by_sample_or_site']['value']=='sample':
#                                Fout_STDEV_OPT_samples.write(String)
#                            else:
#                                Fout_STDEV_OPT_sites.write(String)
#                                
#                    else:
#                         thellier_interpreter_log.write("-I- sample %s FAIL on %s\n"%(sample,":".join(thellier_interpreter_pars['fail_criteria']) ) )                    
#                                                                            
#        #--------------------------------------------------------------
#        # calcuate Bootstarp and write results to files
#        #--------------------------------------------------------------
#            if self.acceptance_criteria['interpreter_method']['value']=='bs' or self.acceptance_criteria['interpreter_method']['value']=='bs_par':
#               if self.acceptance_criteria['interpreter_method']['value']=='bs':
#                    #logfile=thellier_interpreter_log
#                    results_file=Fout_BS_samples
#               if self.acceptance_criteria['interpreter_method']['value']=='bs_par':
#                    #logfile=thellier_interpreter_log
#                    results_file=Fout_BS_PAR_samples
#               BOOTSTRAP_N=int(self.preferences['BOOTSTRAP_N'])
#               String="-I- caclulating bootstrap statistics for sample %s (N=%i)"%(sample,int(BOOTSTRAP_N))
#               #print String
#               thellier_interpreter_log.write(String)
#               
#               Grade_A_samples_BS={} 
#               if len(Grade_A_sorted[sample_or_site].keys()) >= self.acceptance_criteria['sample_int_n']['value']:
#                   for specimen in Grade_A_sorted[sample_or_site].keys():
#                        if specimen not in Grade_A_samples_BS.keys() and len(Grade_A_sorted[sample_or_site][specimen])>0:
#                           Grade_A_samples_BS[specimen]=[]
#                        #for B in Grade_A_samples_BS[sample][specimen]:
#                        for B in Grade_A_sorted[sample_or_site][specimen]:
#                           Grade_A_samples_BS[specimen].append(B)
#                        Grade_A_samples_BS[specimen].sort()
#                        specimen_int_max_slope_diff=max(Grade_A_samples_BS[specimen])/min(Grade_A_samples_BS[specimen])
#                        if specimen_int_max_slope_diff>self.acceptance_criteria['specimen_int_max_slope_diff']:
#                           thellier_interpreter_log.write( "-I- specimen %s Failed specimen_int_max_slope_diff\n"%specimen,Grade_A_samples_BS[specimen])
#                           del Grade_A_samples_BS[specimen]
# 
#               if len(Grade_A_samples_BS.keys())>=self.acceptance_criteria['sample_int_n']['value']:        
#                   BS_means_collection=[]
#                   for i in range(BOOTSTRAP_N):
#                       B_BS=[]
#                       for j in range(len(Grade_A_samples_BS.keys())):
#                           LIST=list(Grade_A_samples_BS.keys())
#                           specimen=random.choice(LIST)
#                           if self.acceptance_criteria['interpreter_method']['value']=='bs':
#                               B=random.choice(Grade_A_samples_BS[specimen])
#                           if self.acceptance_criteria['interpreter_method']['value']=='bs_par':
#                               B=random.uniform(min(Grade_A_samples_BS[specimen]),max(Grade_A_samples_BS[specimen]))
#                           B_BS.append(B)
#                       BS_means_collection.append(scipy.mean(B_BS))
#                       
#                   BS_means=array(BS_means_collection)
#                   BS_means.sort()
#                   sample_median=median(BS_means)
#                   sample_std=std(BS_means,ddof=1)
#                   sample_68=[BS_means[(0.16)*len(BS_means)],BS_means[(0.84)*len(BS_means)]]
#                   sample_95=[BS_means[(0.025)*len(BS_means)],BS_means[(0.975)*len(BS_means)]]
#
#
#                   thellier_interpreter_log.write( "-I-  bootstrap mean sample %s: median=%f, std=%f\n"%(sample,sample_median,sample_std))
#                   String="%s\t%i\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t%s\n"%\
#                           (sample,len(Grade_A_samples_BS.keys()),sample_median,sample_68[0],sample_68[1],sample_95[0],sample_95[1],sample_std,100*(sample_std/sample_median),WARNING)
#                   #print String
#                   #if self.acceptance_criteria['sample_int_bs']:
#                   #    Fout_BS_samples.write(String)
#                   #if self.acceptance_criteria['sample_int_bs_par']:
#                   #    Fout_BS_PAR_samples.write(String)
#                   results_file.write(String)
#               else:
#                   String="-I- sample %s FAIL: not enough specimen int_n= %i < %i "%(sample,len(Grade_A_samples_BS.keys()),int(self.acceptance_criteria['sample_int_n']['value']))
#                   #print String
#                   thellier_interpreter_log.write(String)
#
#                                                  
#        
#        thellier_interpreter_log.write( "-I- Statistics:\n")
#        thellier_interpreter_log.write( "-I- number of specimens analzyed = %i\n" % len(specimens_list)  )
#        thellier_interpreter_log.write( "-I- number of sucsessful 'acceptable' specimens = %i\n" % len(All_grade_A_Recs.keys()))   
#
#        runtime_sec = time.time() - start_time
#        m, s = divmod(runtime_sec, 60)
#        h, m = divmod(m, 60)
#        thellier_interpreter_log.write( "-I- runtime hh:mm:ss is " + "%d:%02d:%02d\n" % (h, m, s))
#        thellier_interpreter_log.write( "-I- Finished sucsessfuly.\n")
#        thellier_interpreter_log.write( "-I- DONE\n")
#
#
#        # close all files
#
#        thellier_interpreter_log.close()
#        thellier_interpreter_all.close()
#        Fout_specimens_bounds.close()
#        if self.acceptance_criteria['interpreter_method']['value']=='stdev_opt': 
#            Fout_STDEV_OPT_redo.close()
#            Fout_STDEV_OPT_specimens.close()
#        if  self.acceptance_criteria['interpreter_method']['value']=='stdev_opt':
#            if self.acceptance_criteria['average_by_sample_or_site']['value']=='sample':
#                Fout_STDEV_OPT_samples.close()
#            else:
#                Fout_STDEV_OPT_sites.close()
#           
#        if self.acceptance_criteria['interpreter_method']['value']=='bs':
#            Fout_BS_samples.close()
#
#        if self.acceptance_criteria['interpreter_method']['value']=='bs_par':
#            Fout_BS_PAR_samples.close()
#        #try:
#        #    os.system('\a')
#        #except:
#        #    pass
#        dlg1 = wx.MessageDialog(self,caption="Message:", message="Interpreter finished sucsessfuly\nCheck output files in folder /thellier_interpreter in the current project directory" ,style=wx.OK|wx.ICON_INFORMATION)
#
#
#        # display the interpretation of the current specimen:
#        self.pars=self.Data[self.s]['pars']
#        self.clear_boxes()
#        #print "about to draw figure" # this is where trouble happens when 1 or 2 specimens are accepted
#        self.draw_figure(self.s)
#        #print "just drew figure"
#        self.update_GUI_with_new_interpretation()
#
#        dlg1.ShowModal()
#        dlg1.Destroy()
#        busy_frame.Destroy()

    #----------------------------------------------------------------------

    def on_menu_open_interpreter_file(self, event):
        #print "self.WD",self.WD
        try:
            dirname=os.path.join(self.WD,"thellier_interpreter")
        except:
            dirname=self.WD
        print "dirname",dirname
        dlg = wx.FileDialog(
            self, message="Choose an auto-interpreter output file",
            defaultDir=dirname, 
            #defaultFile="",
            style=wx.OPEN | wx.CHANGE_DIR
            )
                        
        #dlg = wx.FileDialog(self, "Choose an auto-interpreter output file", defaultDir=dirname, "", "*.*", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            path=dlg.GetPath()
        #print  filename
        #print filename
        if "samples" in filename or "bounds" in filename or "site" in filename:
            ignore_n=4

        elif "specimens" in filename or "all" in filename:
            ignore_n=1
        else:
            return()
        self.frame=thellier_gui_dialogs.MyForm(ignore_n,path)
        self.frame.Show()

    #----------------------------------------------------------------------
      
    def on_menu_open_interpreter_log(self, event):
        dia = thellier_gui_dialogs.MyLogFileErrors("Interpreter errors and warnings", os.path.join(self.WD, "thellier_interpreter/", "thellier_interpreter.log"))
        dia.Show()
        dia.Center()
        


    #----------------------------------------------------------------------
        
    def read_redo_file(self,redo_file):
        """
        Read previous interpretation from a redo file
        and update gui with the new interpretation
        """
        self.GUI_log.write ("-I- read redo file and processing new temperature bounds")
        self.redo_specimens={}
        # first delete all previous interpretation
        for sp in self.Data.keys():
            del self.Data[sp]['pars']
            self.Data[sp]['pars']={}
            self.Data[sp]['pars']['lab_dc_field']=self.Data[sp]['lab_dc_field']
            self.Data[sp]['pars']['er_specimen_name']=self.Data[sp]['er_specimen_name']   
            self.Data[sp]['pars']['er_sample_name']=self.Data[sp]['er_sample_name']
            #print sp
            #print self.Data[sp]['pars']
        self.Data_samples={}
        self.Data_sites={}
        
        fin=open(redo_file,'rU')
        for Line in fin.readlines():
          line=Line.strip('\n').split()
          specimen=line[0]
          tmin_kelvin=float(line[1])
          tmax_kelvin=float(line[2])
          if specimen not in self.redo_specimens.keys():
            self.redo_specimens[specimen]={}
          self.redo_specimens[specimen]['t_min']=float(tmin_kelvin)
          self.redo_specimens[specimen]['t_max']=float(tmax_kelvin)
          if specimen in self.Data.keys():
              if tmin_kelvin not in self.Data[specimen]['t_Arai'] or tmax_kelvin not in self.Data[specimen]['t_Arai'] :
                  self.GUI_log.write ("-W- WARNING: cant fit temperature bounds in the redo file to the actual measurement. specimen %s\n"%specimen)
              else:
                  self.Data[specimen]['pars']=thellier_gui_lib.get_PI_parameters(self.Data,self.acceptance_criteria,self.preferences,specimen,float(tmin_kelvin),float(tmax_kelvin),self.GUI_log,THERMAL,MICROWAVE)
                  try:
                      self.Data[specimen]['pars']=thellier_gui_lib.get_PI_parameters(self.Data,self.acceptance_criteria,self.preferences,specimen,float(tmin_kelvin),float(tmax_kelvin),self.GUI_log,THERMAL,MICROWAVE)
                      self.Data[specimen]['pars']['saved']=True
                      # write intrepretation into sample data
                      sample=self.Data_hierarchy['specimens'][specimen]
                      if sample not in self.Data_samples.keys():
                          self.Data_samples[sample]={}
                      if specimen not in self.Data_samples[sample].keys():
                          self.Data_samples[sample][specimen]={}
                      self.Data_samples[sample][specimen]['B']=self.Data[specimen]['pars']['specimen_int_uT']
                      site=thellier_gui_lib.get_site_from_hierarchy(sample,self.Data_hierarchy)
                      if site not in self.Data_sites.keys():
                          self.Data_sites[site]={}
                      if specimen not in self.Data_sites[site].keys():
                          self.Data_sites[site][specimen]={}
                      self.Data_sites[site][specimen]['B']=self.Data[specimen]['pars']['specimen_int_uT']

                  
                  except:
                      print "-E- ERROR 1"
                      self.GUI_log.write ("-E- ERROR. Cant calculate PI paremeters for specimen %s using redo file. Check!\n"%(specimen))
          else:
              self.GUI_log.write ("-W- WARNING: Cant find specimen %s from redo file in measurement file!\n"%specimen)
              print "-W- WARNING: Cant find specimen %s from redo file in measurement file!\n"%specimen
        fin.close()
        self.pars=self.Data[self.s]['pars']
        self.clear_boxes()
        self.draw_figure(self.s)
        self.update_GUI_with_new_interpretation()

    #----------------------------------------------------------------------            

#    def write_acceptance_criteria_to_file(self):
#        import copy
#        """
#        Write new acceptance criteria to pmag_criteria.txt
#        """
#        # check if an old pmag_criteria.txt exist:
#        other_criteria={}
#        try:
#            fin=open(self.WD+"/"+"pmag_criteria.txt",'rU')
#            lines=""
#            line=fin.readline()
#            line=fin.readline()
#            header=line.strip('\n').split()
#            code_index=header.index("pmag_criteria_code")
#
#            for line in fin.readlines():
#                code=line[code_index]
#                if "IE-" not in code:
#                    for i in range(len(header)):
#                        if line[i]!="":
#                            try:
#                                float(line[i])
#                            except:
#                                continue
#                            other_criteria[code][header[i]]=float(line[i])
#        except:
#             pass
#            
#
#            
#        fout=open(self.WD+"/"+"pmag_criteria.txt",'w')
#        String="tab\tpmag_criteria\n"
#        fout.write(String)
#        specimen_criteria_list=self.criteria_list+["specimen_int_max_slope_diff"]+['check_aniso_ftest']+['anisotropy_alt']
#        sample_criteria_list=[key for key in self.acceptance_criteria.keys() if "sample" in key]
#        if self.acceptance_criteria['sample_int_stdev_opt'] == True:                                      
#            for k in ['sample_int_bs','sample_int_bs_par','sample_int_BS_68_uT','sample_int_BS_68_perc','sample_int_BS_95_uT','sample_int_BS_95_perc']:
#                sample_criteria_list.remove(k)
#                if "specimen_int_max_slope_diff" in specimen_criteria_list:
#                    specimen_criteria_list.remove("specimen_int_max_slope_diff")
#
#        else:
#            for k in ['sample_int_sigma_uT','sample_int_sigma_perc','sample_int_interval_uT','sample_int_stdev_opt','sample_aniso_threshold_perc']:
#                sample_criteria_list.remove(k)
#        for k in ['sample_int_sigma_uT','sample_int_sigma_perc','sample_int_interval_uT','sample_int_interval_perc','sample_aniso_threshold_perc','sample_int_BS_68_uT','sample_int_BS_68_perc','sample_int_BS_95_uT','sample_int_BS_95_perc',]:
#            if  k in sample_criteria_list:
#                if float(self.acceptance_criteria[k]) > 999:
#                    sample_criteria_list.remove(k)
#        if  float(self.acceptance_criteria["sample_int_n_outlier_check"])> 99:
#            sample_criteria_list.remove("sample_int_n_outlier_check")
#
#        if "sample_int_sigma_uT"  in sample_criteria_list and "sample_int_sigma" not in sample_criteria_list:
#            sample_criteria_list.append("sample_int_sigma")
#            self.acceptance_criteria["sample_int_sigma"]=float(self.acceptance_criteria["sample_int_sigma_uT"])*1e-6
#        
#        if "specimen_int_max_slope_diff" in  specimen_criteria_list:
#            if float(self.acceptance_criteria['specimen_int_max_slope_diff'])>999:
#                specimen_criteria_list.remove("specimen_int_max_slope_diff")
#        c_list=copy.copy(specimen_criteria_list)       
#        for criteria in c_list:
#            if criteria in (self.high_threshold_velue_list + ['anisotropy_alt']) and float(self.acceptance_criteria[criteria])>100:
#                specimen_criteria_list.remove(criteria)
#            #if criteria in ['specimen_g'] and float(self.acceptance_criteria[criteria])>100:
#            if criteria in self.low_threshold_velue_list and float(self.acceptance_criteria[criteria])<0.1:
#                specimen_criteria_list.remove(criteria)                
#
#        # special treatment for sample and site criteria:
#        header="pmag_criteria_code\t"
#        for i in range(len(sample_criteria_list)):
#            key=sample_criteria_list[i]
#            if key in ['average_by_sample_or_site','sample_int_sigma_uT','sample_int_stdev_opt','sample_int_n_outlier_check']:
#                continue
#            # special treatment for sample and site criteria:        
#            if self.average_by_sample_or_site=='site':
#                if key == 'sample_int_n' or key == "sample_int_n": key='site_int_nn'
#                if key == 'sample_int_sigma' or key == "sample_int_sigma": key='site_int_sigma'
#                if key == 'sample_int_sigma_perc' or key == "sample_int_sigma_perc": key='site_int_sigma_perc'
#            header=header+key+"\t"
#        for key in specimen_criteria_list:
#            header=header+key+"\t"
#        header=header+"specimen_scat\t"
#
#        # other criteria (not paleointensity)
#        for code in other_criteria.keys():
#            for key in other_criteria[code].keys():
#                header=header+key+"\t"
#        fout.write(header[:-1]+"\n")
#                    
#        line="IE-SPEC:IE-SAMP\t"
#        for key in sample_criteria_list:
#            if key in['average_by_sample_or_site','sample_int_sigma_uT','sample_int_stdev_opt','sample_int_n_outlier_check']:
#                continue
#            if key in ['sample_int_bs','sample_int_bs_par','sample_int_stdev_opt','check_aniso_ftest','average_by_sample_or_site']:
#                line=line+"%s"%str(self.acceptance_criteria[key])+"\t"
#            elif key in ['sample_int_sigma']:
#                line=line+"%.2e"%self.acceptance_criteria[key]+"\t"                
#            else:
#                line=line+"%f"%self.acceptance_criteria[key]+"\t"
#                
#        for key in specimen_criteria_list:
#            if key=='check_aniso_ftest':
#                line=line+str(self.acceptance_criteria[key])+"\t"
#            else:    
#                line=line+"%f"%self.acceptance_criteria[key]+"\t"
#        if self.acceptance_criteria["specimen_scat"]:
#            line=line+"True"+"\t"
#        else:
#            line=line+"False"+"\t"
#
#        # other criteria (not paleointensity)
#        for code in other_criteria.keys():
#            for key in other_criteria[code].keys():
#                line=line+other_criteria[code][key]+"\t"
#    
#        fout.write(line[:-1]+"\n")
#        fout.close()
            
    #----------------------------------------------------------------------            

    def on_menu_run_consistency_test(self, event):
        #dlg1 = wx.MessageDialog(self,caption="Message:",message="Consistency test is no longer supported in this version" ,style=wx.OK)
        #result = dlg1.ShowModal()
        #if result == wx.ID_OK:
        #    dlg1.Destroy()
        #    return
        
        self.GUI_log.write ("-I- running thellier consistency test\n")
        import dialogs.thellier_consistency_test as thellier_consistency_test

        #thellier_gui_dialogs.Consistency_Test(self.Data,self.Data_hierarchy,self.WD,self.acceptance_criteria_default)
        thellier_gui_dialogs.Consistency_Test(self.Data,self.Data_hierarchy,self.WD,self.acceptance_criteria,self.preferences,THERMAL,MICROWAVE)

    def on_menu_run_consistency_test_b(self, event):
        dlg1 = wx.MessageDialog(self,caption="Message:",message="Consistency test is no longer supported in this version" ,style=wx.OK)
        result = dlg1.ShowModal()
        if result == wx.ID_OK:
            dlg1.Destroy()
            return
    #----------------------------------------------------------------------            

    def on_menu_plot_data (self, event):
        #Plot_Dialog(None,self.WD,self.Data,self.Data_info)

        
        dia = thellier_gui_dialogs.Plot_Dialog(None,self.WD,self.Data,self.Data_info)
        dia.Center()
        #result = dia.ShowModal()

        #if result == wx.ID_OK: # Until the user clicks OK, show the message
        #    self.On_close_criteria_box(dia)
        
        if dia.ShowModal() == wx.ID_OK: # Until the user clicks OK, show the message            
            self.On_close_plot_dialog(dia)
        
    #----------------------------------------------------------------------            

#    def on_menu_results_data (self, event):
#        import copy
#        
#        #----------------------------------------------------
#        # Easy tables with the results of all the samples or site that passed the criteria
#        #----------------------------------------------------
#        
#        # search for ages and Latitudes
#        if self.acceptance_criteria['average_by_sample_or_site']['value']=='sample':
#            BY_SITES=False; BY_SAMPLES=True
#        else:
#            BY_SITES=True; BY_SAMPLES=False        
#        
#        if BY_SAMPLES:
#            Data_samples_or_sites=copy.deepcopy(self.Data_samples)
#        else:
#            Data_samples_or_sites=copy.deepcopy(self.Data_sites)
#        samples_or_sites_list=Data_samples_or_sites.keys()
#        samples_or_sites_list.sort()
#        Results_table_data={}
#                
#        for sample_or_site in samples_or_sites_list:
#
#            Age,age_unit,age_range_low,age_range_high="","","",""
#            lat,lon,VADM,VADM_sigma="","","",""
#
#            found_age,found_lat=False,False
#
#            # Find the mean paleointenisty for each sample
#            tmp_B=[]
#            for spec in Data_samples_or_sites[sample_or_site].keys():
#                if 'B' in Data_samples_or_sites[sample_or_site][spec].keys():
#                    tmp_B.append( Data_samples_or_sites[sample_or_site][spec]['B'])
#            if len(tmp_B)<1:
#                continue
#            
#            sample_or_site_pars=self.calculate_sample_mean(Data_samples_or_sites[sample_or_site])        
#            if sample_or_site_pars['pass_or_fail']=='fail':
#                continue
#            
#            N=sample_or_site_pars['N']
#            B_uT=sample_or_site_pars['B_uT']
#            B_std_uT=sample_or_site_pars['B_std_uT']
#            B_std_perc=sample_or_site_pars['B_std_perc']
#            
#            Results_table_data[sample_or_site]={}
#            
#            # search for samples age in er_ages.txt by sample or by site
#            if BY_SAMPLES:
#                site = self.Data_info["er_samples"][sample_or_site]['er_site_name']
#            else:
#                site=sample_or_site
#            found_age=False
#            if sample_or_site in self.Data_info["er_ages"].keys():
#                age_key=sample_or_site
#            elif site in self.Data_info["er_ages"].keys():
#                age_key=site
#            else:
#                age_key=""
#            if age_key !="":
#                try:
#                    age_unit=self.Data_info["er_ages"][age_key]["age_unit"]                
#                except:
#                    age_unit="unknown"               
#                    
#                if self.Data_info["er_ages"][age_key]["age"] !="":
#                    Age = float(self.Data_info["er_ages"][age_key]["age"])
#                    found_age=True
#                    
#                if "age_range_low" in self.Data_info["er_ages"][age_key].keys() and "age_range_high" in self.Data_info["er_ages"][age_key].keys():
#                   age_range_low=float(self.Data_info["er_ages"][age_key]["age_range_low"])
#                   age_range_high=float(self.Data_info["er_ages"][age_key]["age_range_high"])
#                   
#                   if not found_age:
#                       Age=(age_range_low+age_range_high)/2
#                       found_age=True
#
#                elif "age_sigma" in self.Data_info["er_ages"][age_key].keys() and found_age:
#                   age_range_low=Age-float(self.Data_info["er_ages"][age_key]["age_sigma"])
#                   age_range_high= Age+float(self.Data_info["er_ages"][age_key]["age_sigma"])
#
#                elif found_age:
#                   age_range_low=Age
#                   age_range_high=Age
#
#            # convert ages from Years BP to Years Cal AD (+/-)
#                if "Years BP" in age_unit:
#                    Age=1950-Age
#                    age_range_low=1950-age_range_low
#                    age_range_high=1950-age_range_high
#                    age_unit="Years Cal AD (+/-)"             
#            
#            # search for Lon/Lat
#
#            if BY_SAMPLES and sample_or_site in self.Data_info["er_samples"].keys() and "site_lat" in self.Data_info["er_samples"][sample_or_site].keys():
#                lat=float(self.Data_info["er_samples"][sample_or_site]["site_lat"])
#                lon=float(self.Data_info["er_samples"][sample_or_site]["site_lon"])
#                found_lat=True
#                
#            elif site in self.Data_info["er_sites"].keys() and "site_lat" in self.Data_info["er_sites"][site].keys():
#                lat=float(self.Data_info["er_sites"][site]["site_lat"])
#                lon=float(self.Data_info["er_sites"][site]["site_lon"])
#                found_lat=True
#
#            if found_lat:
#                VADM=pmag.b_vdm(B_uT*1e-6,lat)*1e-21
#                VADM_plus=pmag.b_vdm((B_uT+B_std_uT)*1e-6,lat)*1e-21
#                VADM_minus=pmag.b_vdm((B_uT-B_std_uT)*1e-6,lat)*1e-21
#                VADM_sigma=(VADM_plus-VADM_minus)/2
#                
#            Results_table_data[sample_or_site]["N"]="%i"%(int(N))            
#            Results_table_data[sample_or_site]["B_uT"]="%.1f"%(B_uT)
#            Results_table_data[sample_or_site]["B_std_uT"]="%.1f"%(B_std_uT)
#            Results_table_data[sample_or_site]["B_std_perc"]="%.1f"%(B_std_perc)
#            if found_lat:
#                Results_table_data[sample_or_site]["Lat"]="%f"%lat
#                Results_table_data[sample_or_site]["Lon"]="%f"%lon
#                Results_table_data[sample_or_site]["VADM"]="%.1f"%VADM
#                Results_table_data[sample_or_site]["VADM_sigma"]="%.1f"%VADM_sigma
#            else:
#                Results_table_data[sample_or_site]["Lat"]=""
#                Results_table_data[sample_or_site]["Lon"]=""
#                Results_table_data[sample_or_site]["VADM"]=""
#                Results_table_data[sample_or_site]["VADM_sigma"]=""
#            if found_age:
#                Results_table_data[sample_or_site]["Age"]="%.2f"%Age
#                Results_table_data[sample_or_site]["Age_low"]="%.2f"%age_range_low
#                Results_table_data[sample_or_site]["Age_high"]="%.2f"%age_range_high
#            else:
#                Results_table_data[sample_or_site]["Age"]=""
#                Results_table_data[sample_or_site]["Age_low"]=""
#                Results_table_data[sample_or_site]["Age_high"]=""
#            Results_table_data[sample_or_site]["Age_units"]=age_unit
#                
#        sample_or_site_list= Results_table_data.keys()
#        sample_or_site_list.sort()
#        if len(sample_or_site_list) <1:
#            return
#                        
#        fout=open(os.path.join(self.WD, "results_table.txt"),'w')
#        Keys=["sample/site","Lat","Lon","Age","Age_low","Age_high","Age_units","N","B_uT","B_std_uT","VADM","VADM_sigma"]
#        fout.write("\t".join(Keys)+"\n")
#        for sample_or_site in sample_or_site_list:
#            String=sample_or_site+"\t"
#            for k in Keys[1:]:
#                String=String+Results_table_data[sample_or_site][k]+"\t"
#            fout.write(String[:-1]+"\n")
#        fout.close()
#
#
##        #----------------------------------------------------------------------------
##        # Easy tables with the results of all the specimens that passed the criteria
##        #----------------------------------------------------------------------------
##
##        fout=open(self.WD+"/results_table_specimmens.txt",'w')
##        Keys=["specimen","B_raw","B_corrected","ATRM","CR","NLT"]
##        for 
##        fout.write("\t".join(Keys)+"\n")
##        
##        for sample_or_site in samples_or_sites_list:
##            specimens_list=samples_or_sites_list.keys()
##            specimens_list.sort()
##            if len(specimens_list) <1:
##                continue
##            for specimen in specimens_list:
##                if 'specimen_fail_criteria' not in self.Data[specimen]['pars'].keys():
##                    continue
##                if len(self.Data[specimen]['pars']['specimen_fail_criteria'])>0:
##                    continue
##                keys=["sample/site","Lat","Lon","Age","Age_low","Age_high","Age_units","N","B_uT","B_std_uT","VADM","VADM_sigma"]:
##                    for key in Keys:
##                         Results_table_data_specimens[specimen]   
##                    
#                
#
#
#        dlg1 = wx.MessageDialog(self,caption="Message:", message="Output results table is saved in 'results_table.txt'" ,style=wx.OK|wx.ICON_INFORMATION)
#        dlg1.ShowModal()
#        dlg1.Destroy()
#            
#        return

    #----------------------------------------------------------------------            

    def on_menu__prepare_MagIC_results_tables (self, event):

        import copy
        
        
        # write a redo file
        try:
            self.on_menu_save_interpretation(None)
        except:
            pass

        #------------------
        # read existing pmag results data and sort out the directional data. 
        # The directional data will be merged to one combined pmag table. 
        # this data will be marged later  
        #-----------------------.
        
        PmagRecsOld={}
        for FILE in ['pmag_specimens.txt','pmag_samples.txt','pmag_sites.txt','pmag_results.txt']:
            PmagRecsOld[FILE],meas_data=[],[]
            try: 
                meas_data,file_type=pmag.magic_read(os.path.join(self.WD, FILE))
                self.GUI_log.write("-I- Read exiting magic file  %s\n"%(os.path.join(self.WD, FILE)))
                #if FILE !='pmag_specimens.txt':
                os.rename(os.path.join(self.WD, FILE), os.path.join(self.WD, FILE+".backup"))
                self.GUI_log.write("-I- rename old magic file  %s.backup\n"%(os.path.join(self.WD, FILE)))
            except:
                self.GUI_log.write("-I- Cant read existing magic file  %s\n"%(os.path.join(self.WD, FILE)))                
                continue                                                                           
            for rec in meas_data:
                if "magic_method_codes" in rec.keys():
                    if "LP-PI" not in rec['magic_method_codes'] and "IE-" not in rec['magic_method_codes'] :
                        PmagRecsOld[FILE].append(rec)

        pmag_specimens_header_1=["er_location_name","er_site_name","er_sample_name","er_specimen_name"]
        pmag_specimens_header_2=['measurement_step_min','measurement_step_max','specimen_int']        
        pmag_specimens_header_3=["specimen_correction","specimen_int_corr_anisotropy","specimen_int_corr_nlt","specimen_int_corr_cooling_rate"]
        pmag_specimens_header_4=[]
        for short_stat in self.preferences['show_statistics_on_gui']:
            stat="specimen_"+short_stat
            pmag_specimens_header_4.append(stat)
        pmag_specimens_header_5=["magic_experiment_names","magic_method_codes","measurement_step_unit","specimen_lab_field_dc"]
        pmag_specimens_header_6=["er_citation_names"]
        try:
            version= pmag.get_version()
        except:
            version=""
        version=version+": thellier_gui."+CURRENT_VRSION

        specimens_list=[]
        for specimen in self.Data.keys():
            if 'pars' in self.Data[specimen].keys():
                if 'saved' in self.Data[specimen]['pars'].keys() and self.Data[specimen]['pars']['saved']==True:
                    specimens_list.append(specimen)
        
        # Empty pmag tables:
        MagIC_results_data={}
        MagIC_results_data['pmag_specimens']={}
        MagIC_results_data['pmag_samples_or_sites']={}            
        MagIC_results_data['pmag_results']={}

        # write down pmag_specimens.txt        
        specimens_list.sort()
        for specimen in specimens_list:
            
            
            if 'pars' in self.Data[specimen].keys() and 'saved' in self.Data[specimen]['pars'].keys() and self.Data[specimen]['pars']['saved']==True:

                sample_name = self.Data_hierarchy['specimens'][specimen]
                site_name=thellier_gui_lib.get_site_from_hierarchy(sample_name,self.Data_hierarchy)                
                location_name=thellier_gui_lib.get_location_from_hierarchy(site_name,self.Data_hierarchy)                
                
                MagIC_results_data['pmag_specimens'][specimen]={}
                if version!="unknown":
                    MagIC_results_data['pmag_specimens'][specimen]['magic_software_packages']=version
                MagIC_results_data['pmag_specimens'][specimen]['er_citation_names']="This study"
                #MagIC_results_data['pmag_specimens'][specimen]['er_analyst_mail_names']="unknown"
                
                MagIC_results_data['pmag_specimens'][specimen]['er_specimen_name']=specimen
                MagIC_results_data['pmag_specimens'][specimen]['er_sample_name']=sample_name
                MagIC_results_data['pmag_specimens'][specimen]['er_site_name']=site_name
                MagIC_results_data['pmag_specimens'][specimen]['er_location_name']=location_name
                MagIC_results_data['pmag_specimens'][specimen]['magic_method_codes']=self.Data[specimen]['pars']['magic_method_codes']+":IE-TT"
                tmp=MagIC_results_data['pmag_specimens'][specimen]['magic_method_codes'].split(":")
                magic_experiment_names=specimen
                for m in tmp:
                    if "LP-" in m:
                        magic_experiment_names=magic_experiment_names+" : " + m
                MagIC_results_data['pmag_specimens'][specimen]['magic_experiment_names']=magic_experiment_names                
                    
                MagIC_results_data['pmag_specimens'][specimen]['measurement_step_unit']='K'
                MagIC_results_data['pmag_specimens'][specimen]['specimen_lab_field_dc']="%.2e"%(self.Data[specimen]['pars']['lab_dc_field'])
                MagIC_results_data['pmag_specimens'][specimen]['specimen_correction']=self.Data[specimen]['pars']['specimen_correction']
                for key in pmag_specimens_header_4:
                    if key in ['specimen_int_ptrm_n','specimen_int_n']:
                        MagIC_results_data['pmag_specimens'][specimen][key]="%i"%(self.Data[specimen]['pars'][key])     
                    elif key in ['specimen_scat'] and self.Data[specimen]['pars'][key]=="Fail":                            
                        MagIC_results_data['pmag_specimens'][specimen][key]="0"     
                    elif key in ['specimen_scat'] and self.Data[specimen]['pars'][key]=="Pass":                            
                        MagIC_results_data['pmag_specimens'][specimen][key]="1"     
                    else:
                        MagIC_results_data['pmag_specimens'][specimen][key]="%.2f"%(self.Data[specimen]['pars'][key])                             
                                
                MagIC_results_data['pmag_specimens'][specimen]['specimen_int']="%.2e"%(self.Data[specimen]['pars']['specimen_int'])
                MagIC_results_data['pmag_specimens'][specimen]['measurement_step_min']="%i"%(self.Data[specimen]['pars']['measurement_step_min'])
                MagIC_results_data['pmag_specimens'][specimen]['measurement_step_max']="%i"%(self.Data[specimen]['pars']['measurement_step_max'])
                if "specimen_int_corr_anisotropy" in  self.Data[specimen]['pars'].keys():
                    MagIC_results_data['pmag_specimens'][specimen]['specimen_int_corr_anisotropy']="%.2f"%(self.Data[specimen]['pars']['specimen_int_corr_anisotropy'])
                else:
                    MagIC_results_data['pmag_specimens'][specimen]['specimen_int_corr_anisotropy']=""
                if "specimen_int_corr_nlt" in  self.Data[specimen]['pars'].keys():
                    MagIC_results_data['pmag_specimens'][specimen]['specimen_int_corr_nlt']="%.2f"%(self.Data[specimen]['pars']['specimen_int_corr_nlt'])
                else:
                    MagIC_results_data['pmag_specimens'][specimen]['specimen_int_corr_nlt']=""
                if "specimen_int_corr_cooling_rate" in  self.Data[specimen]['pars'].keys() and self.Data[specimen]['pars']['specimen_int_corr_cooling_rate'] != -999:
                    MagIC_results_data['pmag_specimens'][specimen]['specimen_int_corr_cooling_rate']="%.2f"%(self.Data[specimen]['pars']['specimen_int_corr_cooling_rate'])
                else:
                    MagIC_results_data['pmag_specimens'][specimen]['specimen_int_corr_cooling_rate']=""
                    
        # wrire pmag_specimens.txt
        fout=open(os.path.join(self.WD, "pmag_specimens.txt"),'w')
        fout.write("tab\tpmag_specimens\n")
        headers=pmag_specimens_header_1+pmag_specimens_header_2+pmag_specimens_header_3+pmag_specimens_header_4+pmag_specimens_header_5+pmag_specimens_header_6
        String=""
        for key in headers:
            String=String+key+"\t"
        fout.write(String[:-1]+"\n")
        for specimen in specimens_list:
            String=""
            for key in headers:
                String=String+MagIC_results_data['pmag_specimens'][specimen][key]+"\t"
            fout.write(String[:-1]+"\n")
        fout.close()    
        
        
        # merge with non-intensity data
        # read the new pmag_specimens.txt
        meas_data,file_type=pmag.magic_read(os.path.join(self.WD, "pmag_specimens.txt"))
        # add the old non-PI lines from pmag_specimens.txt
        for rec in PmagRecsOld["pmag_specimens.txt"]:
            meas_data.append(rec)
        # fix headers, so all headers in all lines
        meas_data=self.converge_pmag_rec_headers(meas_data)
        # write the combined pmag_specimens.txt
        pmag.magic_write(os.path.join(self.WD, "pmag_specimens.txt"),meas_data,'pmag_specimens')
        try:
            os.remove(os.path.join(self.WD, "pmag_specimens.txt.backup"))
        except:
            pass 

        #-------------
        # message dialog
        #-------------
        TEXT="specimens interpretations are saved in pmag_specimens.txt.\nPress OK for pmag_samples/pmag_sites/pmag_results tables."
        dlg = wx.MessageDialog(self, caption="Saved",message=TEXT,style=wx.OK|wx.CANCEL )
        result = dlg.ShowModal()
        if result == wx.ID_OK:            
            dlg.Destroy()
        if result == wx.ID_CANCEL:            
            dlg.Destroy()
            return()
                
        #-------------
        # pmag_samples.txt or pmag_sites.txt
        #-------------
        if self.acceptance_criteria['average_by_sample_or_site']['value']=='sample':
            BY_SITES=False; BY_SAMPLES=True
        else:
            BY_SITES=True; BY_SAMPLES=False

        pmag_samples_header_1=["er_location_name","er_site_name"]
        if BY_SAMPLES:
           pmag_samples_header_1.append("er_sample_name")
        if BY_SAMPLES:
            pmag_samples_header_2=["er_specimen_names","sample_int","sample_int_n","sample_int_sigma","sample_int_sigma_perc","sample_description"]
        else:
            pmag_samples_header_2=["er_specimen_names","site_int","site_int_n","site_int_sigma","site_int_sigma_perc","site_description"]
        pmag_samples_header_3=["magic_method_codes","magic_software_packages"]
        pmag_samples_header_4=["er_citation_names"]

        pmag_samples_or_sites_list=[]
        
        if BY_SAMPLES:
            samples_or_sites=self.Data_samples.keys()
            Data_samples_or_sites=copy.deepcopy(self.Data_samples)
        else:
            samples_or_sites=self.Data_sites.keys()
            Data_samples_or_sites=copy.deepcopy(self.Data_sites)        
        samples_or_sites.sort()
        for sample_or_site in samples_or_sites:
            if True:
                specimens_names=""
                B=[]
                specimens_LP_codes=[]
                for specimen in Data_samples_or_sites[sample_or_site].keys():
                    B.append(Data_samples_or_sites[sample_or_site][specimen])
                    magic_codes=MagIC_results_data['pmag_specimens'][specimen]['magic_method_codes']
                    codes=magic_codes.replace(" ","").split(":")
                    for code in codes:
                        if "LP-" in code and code not in specimens_LP_codes:
                            specimens_LP_codes.append(code)
                    
                    specimens_names=specimens_names+specimen+":"
                magic_codes=":".join(specimens_LP_codes)+":IE-TT"
                specimens_names=specimens_names[:-1]
                if specimens_names!="":

                    #sample_pass_criteria=False
                    sample_or_site_pars=self.calculate_sample_mean(Data_samples_or_sites[sample_or_site])
                    if sample_or_site_pars['pass_or_fail']=='fail':
                        continue
                    N=sample_or_site_pars['N']
                    B_uT=sample_or_site_pars['B_uT']
                    B_std_uT=sample_or_site_pars['B_std_uT']
                    B_std_perc=sample_or_site_pars['B_std_perc']
                    #if len(B)>=self.acceptance_criteria['sample_int_n']:
                    #    B_std_uT=std(B,ddof=1)
                    #    B_std_perc=std(B,ddof=1)/scipy.mean(B)*100
                    #    if (self.acceptance_criteria['sample_int_sigma_uT']==0 and self.acceptance_criteria['sample_int_sigma_perc']==0) or\
                    #       ( B_std_uT <=self.acceptance_criteria['sample_int_sigma_uT'] or B_std_perc <= self.acceptance_criteria['sample_int_sigma_perc']):
                    #        if ( (max(B)-min(B)) <= self.acceptance_criteria['sample_int_interval_uT'] or 100*((max(B)-min(B))/mean((B))) <= self.acceptance_criteria['sample_int_interval_perc']):
                    #            sample_pass_criteria=True
                    #if not sample_pass_criteria:
                        #print "skipping sample" %sample
                        #continue
                    pmag_samples_or_sites_list.append(sample_or_site)
                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site]={}
                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site]['er_specimen_names']=specimens_names
                    if BY_SAMPLES:
                        name="sample_"
                    else:
                        name="site_"
                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site][name+'int']="%.2e"%(B_uT*1e-6)
                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site][name+'int_n']="%i"%(N)
                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site][name+'int_sigma']="%.2e"%(B_std_uT*1e-6)
                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site][name+'int_sigma_perc']="%.2f"%(B_std_perc)
                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site][name+'description']="paleointensity mean"
                    if BY_SAMPLES:
                        sample_name=sample_or_site
                        site_name=thellier_gui_lib.get_site_from_hierarchy(sample_name,self.Data_hierarchy)
                        location_name=thellier_gui_lib.get_location_from_hierarchy(site_name,self.Data_hierarchy) 
                        MagIC_results_data['pmag_samples_or_sites'][sample_or_site]['er_sample_name']=sample_name
                        
                    if BY_SITES:
                        site_name=sample_or_site
                        location_name=thellier_gui_lib.get_location_from_hierarchy(site_name,self.Data_hierarchy) 
                    
                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site]['er_site_name']=site_name
                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site]['er_location_name']=location_name

                    #for key in pmag_samples_header_1:
                    #        sample_name=sample_or_site
                    #        site_name=thellier_gui_lib.get_site_from_hierarchy(sample_name,self.Data_hierarchy)
                    #        location_name=thellier_gui_lib.get_location_from_hierarchy(site_name,self.Data_hierarchy) 
                            
                                           
                        #else:
                            #MagIC_results_data['pmag_samples_or_sites'][sample_or_site][key]=self.MagIC_model["er_sites"][sample_or_site][key]
                            #MagIC_results_data['pmag_samples_or_sites'][sample_or_site][key]=sample_or_site
                                                
                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site]["pmag_criteria_codes"]=""
                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site]['magic_method_codes']=magic_codes
                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site]["magic_software_packages"]=version
                    
                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site]["er_citation_names"]="This study"
                   
                    
        # wrire pmag_samples.txt
        if BY_SAMPLES:
            fout=open(os.path.join(self.WD, "pmag_samples.txt"),'w')
            fout.write("tab\tpmag_samples\n")
        else:
            fout=open(os.path.join(self.WD, "pmag_sites.txt"),'w')
            fout.write("tab\tpmag_sites\n")
            
        headers=pmag_samples_header_1+pmag_samples_header_2+pmag_samples_header_3+pmag_samples_header_4
        String=""
        for key in headers:
            String=String+key+"\t"
        fout.write(String[:-1]+"\n")

        pmag_samples_or_sites_list.sort()
        for sample_or_site in pmag_samples_or_sites_list:
            String=""
            for key in headers:
                String=String+MagIC_results_data['pmag_samples_or_sites'][sample_or_site][key]+"\t"
            fout.write(String[:-1]+"\n")
        fout.close()
            
        # merge with non-intensity data
        if BY_SAMPLES:
            meas_data,file_type=pmag.magic_read(os.path.join(self.WD, "pmag_samples.txt"))
            for rec in PmagRecsOld["pmag_samples.txt"]:
                meas_data.append(rec)
            meas_data=self.converge_pmag_rec_headers(meas_data)
            pmag.magic_write(os.path.join(self.WD, "pmag_samples.txt"), meas_data,'pmag_samples')
            try:
                os.remove(os.path.join(self.WD, "pmag_samples.txt.backup")) 
            except:
                pass     
            pmag.magic_write(os.path.join(self.WD, "pmag_sites.txt"), PmagRecsOld["pmag_sites.txt"],'pmag_sites')
            try:
                os.remove(os.path.join(self.WD, "pmag_sites.txt.backup"))
            except:
                pass
                  
            #pmag.magic_write(self.WD+"/"+"pmag_samples.txt",PmagRecsOld["pmag_samples.txt"],'pmag_samples')
            #try:
            #    os.rename(self.WD+"/"+"pmag_sites.txt"+".backup",self.WD+"/"+"pmag_sites.txt")
            #except:
            #    pass
        else:
            meas_data,file_type=pmag.magic_read(os.path.join(self.WD, "pmag_sites.txt"))
            for rec in PmagRecsOld["pmag_sites.txt"]:
                meas_data.append(rec)
            meas_data=self.converge_pmag_rec_headers(meas_data)
            pmag.magic_write(os.path.join(self.WD, "pmag_sites.txt"),meas_data,'pmag_sites')
            try:
                os.remove(os.path.join(self.WD, "pmag_sites.txt.backup")) 
            except:
                pass 
            pmag.magic_write(os.path.join(self.WD, "pmag_samples.txt"),PmagRecsOld["pmag_samples.txt"],'pmag_samples')
            try:
                os.remove(os.path.join(self.WD, "pmag_samples.txt.backup"))
            except:
                pass
                  

            #Ery:    
            #    os.rename(self.WD+"/"+"pmag_samples.txt"+".backup",self.WD+"/"+"pmag_samples.txt")
            #except:
            #    pass
            #pmag.magic_write(self.WD+"/"+"pmag_samples.txt",PmagRecsOld["pmag_samples.txt"],'pmag_samples')
            #pmag.magic_write(self.WD+"/"+"pmag_sites.txt",PmagRecsOld["pmag_sites.txt"],'pmag_sites')
                                                        
        #-------------
        # pmag_results.txt
        #-------------

        pmag_results_header_1=["er_location_names","er_site_names"]
        if BY_SAMPLES:
            pmag_results_header_1.append("er_sample_names")
        pmag_results_header_1.append("er_specimen_names")
            
        pmag_results_header_2=["average_lat","average_lon",]
        pmag_results_header_3=["average_int_n","average_int","average_int_sigma","average_int_sigma_perc"]
        if self.preferences['VDM_or_VADM']=="VDM":
            pmag_results_header_4=["vdm","vdm_sigma"]        
        else:    
            pmag_results_header_4=["vadm","vadm_sigma"]
        pmag_results_header_5=[ "data_type","pmag_result_name","magic_method_codes","result_description","er_citation_names","magic_software_packages","pmag_criteria_codes"]                
                
        # for ages, check the er_ages.txt, and take whats theres
        #age_headers=[]
        #for site in self.MagIC_model["er_ages"].keys():
        #    if "age" in self.MagIC_model["er_ages"][site].keys() and self.MagIC_model["er_ages"][site]["age"]!="" and "age" not in age_headers:
        #       age_headers.append("age")
        #    if "age_sigma" in self.MagIC_model["er_ages"][site].keys() and self.MagIC_model["er_ages"][site]["age_sigma"]!="" and "age_sigma" not in age_headers:
        #       age_headers.append("age_sigma")
        #    if "age_range_low" in self.MagIC_model["er_ages"][site].keys() and self.MagIC_model["er_ages"][site]["age_range_low"]!="" and "age_range_low" not in age_headers:
        #       age_headers.append("age_range_low")
        #    if "age_range_high" in self.MagIC_model["er_ages"][site].keys() and self.MagIC_model["er_ages"][site]["age_range_high"]!="" and "age_range_high" not in age_headers:
        #       age_headers.append("age_range_high")
        #    if "age_unit" in self.MagIC_model["er_ages"][site].keys() and self.MagIC_model["er_ages"][site]["age_unit"]!="" and "age_unit" not in age_headers:
        #       age_headers.append("age_unit")
                                             
               
        for sample_or_site in pmag_samples_or_sites_list:       
            MagIC_results_data['pmag_results'][sample_or_site]={}
            MagIC_results_data['pmag_results'][sample_or_site]['pmag_criteria_codes']="ACCEPT"
            MagIC_results_data['pmag_results'][sample_or_site]["er_location_names"]=MagIC_results_data['pmag_samples_or_sites'][sample_or_site]['er_location_name']
            MagIC_results_data['pmag_results'][sample_or_site]["er_site_names"]=MagIC_results_data['pmag_samples_or_sites'][sample_or_site]['er_site_name']
            MagIC_results_data['pmag_results'][sample_or_site]["er_specimen_names"]=MagIC_results_data['pmag_samples_or_sites'][sample_or_site]['er_specimen_names']            

            if BY_SAMPLES:
                MagIC_results_data['pmag_results'][sample_or_site]["er_sample_names"]=MagIC_results_data['pmag_samples_or_sites'][sample_or_site]['er_sample_name']

            site=MagIC_results_data['pmag_results'][sample_or_site]["er_site_names"]
            lat,lon="",""
            if site in self.Data_info["er_sites"].keys() and "site_lat" in self.Data_info["er_sites"][site].keys():
                #MagIC_results_data['pmag_results'][sample_or_site]["average_lat"]=self.Data_info["er_sites"][site]["site_lat"]
                lat=self.Data_info["er_sites"][site]["site_lat"]

            if site in self.Data_info["er_sites"].keys() and "site_lon" in self.Data_info["er_sites"][site].keys():
                #MagIC_results_data['pmag_results'][sample_or_site]["average_lon"]=self.Data_info["er_sites"][site]["site_lon"]
                lon=self.Data_info["er_sites"][site]["site_lon"]
            MagIC_results_data['pmag_results'][sample_or_site]["average_lat"]=lat
            MagIC_results_data['pmag_results'][sample_or_site]["average_lon"]=lon
            if BY_SAMPLES:
                name='sample'
            else:
                name='site'
                
            MagIC_results_data['pmag_results'][sample_or_site]["average_int_n"]=MagIC_results_data['pmag_samples_or_sites'][sample_or_site][name+'_int_n']
            MagIC_results_data['pmag_results'][sample_or_site]["average_int"]=MagIC_results_data['pmag_samples_or_sites'][sample_or_site][name+'_int']
            MagIC_results_data['pmag_results'][sample_or_site]["average_int_sigma"]=MagIC_results_data['pmag_samples_or_sites'][sample_or_site][name+'_int_sigma']
            MagIC_results_data['pmag_results'][sample_or_site]["average_int_sigma_perc"]=MagIC_results_data['pmag_samples_or_sites'][sample_or_site][name+'_int_sigma_perc']

            if self.preferences['VDM_or_VADM']=="VDM":
                pass
                # to be done
            else:
                if lat!="":
                    lat=float(lat)
                    #B=float(MagIC_results_data['pmag_samples_or_sites'][sample_or_site]['sample_int'])
                    B=float(MagIC_results_data['pmag_results'][sample_or_site]["average_int"])
                    #B_sigma=float(MagIC_results_data['pmag_samples_or_sites'][sample_or_site]['sample_int_sigma'])
                    B_sigma=float(MagIC_results_data['pmag_results'][sample_or_site]["average_int_sigma"])
                    VADM=pmag.b_vdm(B,lat)
                    VADM_plus=pmag.b_vdm(B+B_sigma,lat)
                    VADM_minus=pmag.b_vdm(B-B_sigma,lat)
                    VADM_sigma=(VADM_plus-VADM_minus)/2
                    MagIC_results_data['pmag_results'][sample_or_site]["vadm"]="%.2e"%VADM
                    MagIC_results_data['pmag_results'][sample_or_site]["vadm_sigma"]="%.2e"%VADM_sigma
                else:
                    MagIC_results_data['pmag_results'][sample_or_site]["vadm"]=""
                    MagIC_results_data['pmag_results'][sample_or_site]["vadm_sigma"]=""
            if   MagIC_results_data['pmag_results'][sample_or_site]["vadm"]   != "":     
                MagIC_results_data['pmag_results'][sample_or_site]["pmag_result_name"]="Paleointensity;V[A]DM;" +sample_or_site
                MagIC_results_data['pmag_results'][sample_or_site]["result_description"]="Paleointensity; V[A]DM"
            else:
                MagIC_results_data['pmag_results'][sample_or_site]["pmag_result_name"]="Paleointensity;" +sample_or_site
                MagIC_results_data['pmag_results'][sample_or_site]["result_description"]="Paleointensity"
    
            MagIC_results_data['pmag_results'][sample_or_site]["magic_software_packages"]=version
            MagIC_results_data['pmag_results'][sample_or_site]["magic_method_codes"]=magic_codes
            # try to make a more meaningful name
            
            MagIC_results_data['pmag_results'][sample_or_site]["data_type"]="i"
            MagIC_results_data['pmag_results'][sample_or_site]["er_citation_names"]="This study"
            
            # add ages
            found_age=False
            site=MagIC_results_data['pmag_results'][sample_or_site]["er_site_names"]
            if  sample_or_site in self.Data_info["er_ages"].keys():
                sample_or_site_with_age=sample_or_site
                found_age=True
            elif site in self.Data_info["er_ages"].keys():
                sample_or_site_with_age=site
                found_age=True
            if found_age:
                for header in ["age","age_unit","age_sigma","age_range_low","age_range_high"]:
                    if  sample_or_site_with_age in self.Data_info["er_ages"].keys() and  header in self.Data_info["er_ages"][sample_or_site_with_age].keys():
                        if self.Data_info["er_ages"][sample_or_site_with_age][header]!="":
                            value=self.Data_info["er_ages"][sample_or_site_with_age][header]
                            header_result="average_"+header
                            if header_result == "average_age_range_high":
                                header_result="average_age_high"
                            if header_result == "average_age_range_low":
                                header_result="average_age_low"
                            MagIC_results_data['pmag_results'][sample_or_site][header_result]=value
                                
                            if header_result not in pmag_results_header_4:
                               pmag_results_header_4.append(header_result) 
                
                            
        # check for ages:
        
        for sample_or_site in pmag_samples_or_sites_list:
            found_age=False
            if BY_SAMPLES and sample_or_site in self.Data_info["er_ages"].keys():
                element_with_age=sample_or_site
                found_age=True
            elif BY_SAMPLES and sample_or_site not in self.Data_info["er_ages"].keys():
                site=self.Data_hierarchy['site_of_sample'][sample_or_site]
                if site in self.Data_info["er_ages"].keys():
                    element_with_age=site
                    found_age=True
            elif BY_SITES and sample_or_site in self.Data_info["er_ages"].keys():
                element_with_age=sample_or_site
                found_age=True
            else:
                continue
            if not found_age:
                continue
            foundkeys=False       
            #print    "element_with_age",element_with_age                                    
            for key in ['age','age_sigma','age_range_low','age_range_high','age_unit']:
                if "er_ages" in self.Data_info.keys() and element_with_age in self.Data_info["er_ages"].keys():
                    if key in  self.Data_info["er_ages"][element_with_age].keys():
                        if  self.Data_info["er_ages"][element_with_age][key] !="":
                            MagIC_results_data['pmag_results'][sample_or_site][key]=self.Data_info["er_ages"][element_with_age][key]
                            foundkeys=True
            if foundkeys==True:
                if "er_ages" in self.Data_info.keys() and element_with_age in self.Data_info["er_ages"].keys():
                    if 'magic_method_codes' in self.Data_info["er_ages"][element_with_age].keys():
                        methods= self.Data_info["er_ages"][element_with_age]['magic_method_codes'].replace(" ","").strip('\n').split(":")
                        for meth in methods:
                            MagIC_results_data['pmag_results'][sample_or_site]["magic_method_codes"]=MagIC_results_data['pmag_results'][sample_or_site]["magic_method_codes"] + ":"+ meth
                             
                           
        # write pmag_results.txt
        fout=open(os.path.join(self.WD, "pmag_results.txt"),'w')
        fout.write("tab\tpmag_results\n")
        headers=pmag_results_header_1+pmag_results_header_2+pmag_results_header_3+pmag_results_header_4+pmag_results_header_5
        String=""
        for key in headers:
            String=String+key+"\t"
        fout.write(String[:-1]+"\n")

        #pmag_samples_list.sort()
        for sample_or_site in pmag_samples_or_sites_list:
            String=""
            for key in headers:
                if key in MagIC_results_data['pmag_results'][sample_or_site].keys():
                    String=String+MagIC_results_data['pmag_results'][sample_or_site][key]+"\t"
                else:
                    String=String+""+"\t"
            fout.write(String[:-1]+"\n")
        fout.close()
        
        #print "self.WD",self.WD
        # merge with non-intensity data
        meas_data,file_type=pmag.magic_read(os.path.join(self.WD, "pmag_results.txt"))
        for rec in PmagRecsOld["pmag_results.txt"]:
            meas_data.append(rec)
        meas_data=self.converge_pmag_rec_headers(meas_data)
        pmag.magic_write(os.path.join(self.WD, "pmag_results.txt"),meas_data,'pmag_results')
        try:
            os.remove(os.path.join(self.WD, "pmag_results.txt.backup")) 
        except:
            pass     

        
        #-------------
        # MAgic_methods.txt
        #-------------

        # search for all magic_methods in all files:
        magic_method_codes=[]
        for F in ["magic_measurements.txt","rmag_anisotropy.txt","rmag_results.txt","rmag_results.txt","pmag_samples.txt","pmag_specimens.txt","pmag_sites.txt","er_ages.txt"]:
            try:
                fin=open(os.path.join(self.WD, F),'rU')
            except:
                continue
            line=fin.readline()
            line=fin.readline()
            header=line.strip('\n').split('\t')
            if  "magic_method_codes" not in header:
                continue
            else:
                index=header.index("magic_method_codes")
            for line in fin.readlines():
                tmp=line.strip('\n').split('\t')
                if len(tmp) >= index:
                    codes=tmp[index].replace(" ","").split(":")
                    for code in codes:
                        if code !="" and code not in magic_method_codes:
                            magic_method_codes.append(code)
            fin.close()
            
        magic_method_codes.sort()
        #print magic_method_codes
        magic_methods_header_1=["magic_method_code"]
        fout=open(os.path.join(self.WD, "magic_methods.txt"),'w')
        fout.write("tab\tmagic_methods\n")
        fout.write("magic_method_code\n")
        for code in magic_method_codes:
            fout.write("%s\n"%code)
        fout.close
                
        # make pmag_criteria.txt if it does not exist
        if not os.path.isfile(os.path.join(self.WD, "pmag_criteria.txt")):
            Fout=open(os.path.join(self.WD, "pmag_criteria.txt"),'w')
            Fout.write("tab\tpmag_criteria\n")
            Fout.write("er_citation_names\tpmag_criteria_code\n")
            Fout.write("This study\tACCEPT\n")

        dlg1 = wx.MessageDialog(self,caption="Message:", message="MagIC pmag files are saved in MagIC project folder" ,style=wx.OK|wx.ICON_INFORMATION)
        dlg1.ShowModal()
        dlg1.Destroy()
        
        self.close_warning=False  
             
    def converge_pmag_rec_headers(self,old_recs):
        # fix the headers of pmag recs
        recs={}
        recs=copy.deepcopy(old_recs)
        headers=[]
        for rec in recs:
            for key in rec.keys():
                if key not in headers:
                    headers.append(key)
        for rec in recs:
            for header in headers:
                if header not in rec.keys():
                    rec[header]=""
        return recs
    
    '''outdated            
    def read_magic_model (self):
        # Read MagIC Data model:
        

        self.MagIC_model={}
        self.MagIC_model["specimens"]={}
        self.MagIC_model["er_samples"]={}
        self.MagIC_model["er_sites"]={}
        self.MagIC_model["er_locations"]={}
        self.MagIC_model["er_ages"]={}
        fail=[]
        self.MagIC_model["specimens"]=self.read_magic_file(os.path.join(self.WD, "er_specimens.txt"),1,'er_specimen_name')
        try:
            self.MagIC_model["specimens"]=self.read_magic_file(os.path.join(self.WD, "er_specimens.txt"),1,'er_specimen_name')
        except:
            self.GUI_log.write ("-W- Cant find er_specimens.txt in project directory")
            fail.append("er_specimens.txt")
            pass
        try:
            self.MagIC_model["er_samples"]=self.read_magic_file(os.path.join(self.WD, "er_samples.txt"),1,'er_sample_name')
        except:
            self.GUI_log.write ("-W- Cant find er_sample.txt in project directory")
            fail.append("er_sample.txt")
            pass
        try:
            self.MagIC_model["er_sites"]=self.read_magic_file(os.path.join(self.WD, "er_sites.txt"),1,'er_site_name')
        except:
            self.GUI_log.write ("-W- Cant find er_sites.txt in project directory")
            fail.append("er_sites.txt")
            pass
        try:
            self.MagIC_model["er_locations"]=self.read_magic_file(os.path.join(self.WD, "er_locations.txt"),1,'er_location_name')
        except:
            self.GUI_log.write ("-W- Cant find er_locations.txt in project directory")
            fail.append("er_locations.txt")
            pass

        try:
            self.MagIC_model["er_ages"]=self.read_magic_file(os.path.join(self.WD, "er_ages"),1,'er_site_name')
        except:
            self.GUI_log.write ("-W- Cant find er_ages.txt in project directory")
            pass

        return (fail)'''
        
                          
    def read_magic_file(self,path,ignore_lines_n,sort_by_this_name):
        DATA={}
        fin=open(path,'rU')
        #ignore first lines
        for i in range(ignore_lines_n):
            fin.readline()
        #header
        line=fin.readline()
        header=line.strip('\n').split('\t')
        #print header
        for line in fin.readlines():
            if line[0]=="#":
                continue
            tmp_data={}
            tmp_line=line.strip('\n').split('\t')
            #print tmp_line
            for i in range(len(tmp_line)):
                if i>= len(header):
                    continue
                tmp_data[header[i]]=tmp_line[i]
            DATA[tmp_data[sort_by_this_name]]=tmp_data
        fin.close()        
        return(DATA)
                
    def read_er_ages_file(self,path,ignore_lines_n,sort_by_these_names):
        '''
        read er_ages, sort it by site or sample (the header that is not empty)
        and convert ages to calender year
        
        '''
        DATA={}
        fin=open(path,'rU')
        #ignore first lines
        for i in range(ignore_lines_n):
            fin.readline()
        #header
        line=fin.readline()
        header=line.strip('\n').split('\t')
        #print header
        for line in fin.readlines():
            if line[0]=="#":
                continue
            tmp_data={}
            tmp_line=line.strip('\n').split('\t')
            for i in range(len(tmp_line)):
                if i>= len(header):
                    continue
                tmp_data[header[i]]=tmp_line[i]
            for name in sort_by_these_names:
                if name in tmp_data.keys() and   tmp_data[name] !="": 
                    er_ages_rec=self.convert_ages_to_calender_year(tmp_data)
                    DATA[tmp_data[name]]=er_ages_rec
        fin.close()        
        return(DATA)

    def on_menu_convert_to_magic(self,event):
        dia = thellier_gui_dialogs.convert_generic_files_to_MagIC(self.WD)
        dia.Show()
        dia.Center()
        self.magic_file = os.path.join(self.WD, "magic_measurements.txt")
        self.GUI_log=open("%s/Thellier_GUI.log"%self.WD,'w')
        self.Data,self.Data_hierarchy={},{}
        self.Data,self.Data_hierarchy=self.get_data() # Get data from magic_measurements and rmag_anistropy if exist.
        self.Data_info=self.get_data_info() # get all ages, locations etc. (from er_ages, er_sites, er_locations)
        self.redo_specimens={}
        self.specimens=self.Data.keys()
        self.specimens.sort()                                                                
        self.specimens_box.SetItems(self.specimens)
        self.s=self.specimens[0]
        self.update_selection()

    def calculate_sample_mean(self,Data_sample_or_site):#,acceptance_criteria):
        '''
        Data_sample_or_site is a dictonary holding the samples_or_sites mean
        Data_sample_or_site ={}
        Data_sample_or_site[specimen]=B (in units of microT)
        '''
        
        pars={}
        tmp_B=[]
        for spec in Data_sample_or_site.keys():
            if 'B' in Data_sample_or_site[spec].keys():
                tmp_B.append(Data_sample_or_site[spec]['B'])
        if len(tmp_B)<1:
            pars['N']=0
            pars['pass_or_fail']='fail'
            return pars
        
        tmp_B=scipy.array(tmp_B)
        pars['pass_or_fail']='pass'
        pars['N']=len(tmp_B)
        pars['B_uT']=scipy.mean(tmp_B)
        if len(tmp_B)>1:
            pars['B_std_uT'] = scipy.std(tmp_B,ddof=1)
            pars['B_std_perc']=100*(pars['B_std_uT']/pars['B_uT'])    
        else:
            pars['B_std_uT']=0
            pars['B_std_perc']=0    
        pars['sample_int_interval_uT']=(max(tmp_B)-min(tmp_B))
        pars['sample_int_interval_perc']=100*(pars['sample_int_interval_uT']/pars['B_uT'])
        pars['fail_list']=[]
        #check if pass criteria
        #----------
        # int_n
        if self.acceptance_criteria['average_by_sample_or_site']['value']=='sample':
            average_by_sample_or_site='sample'
        else:
            average_by_sample_or_site='site'
            
        if average_by_sample_or_site=='sample':
            cutoff_value=self.acceptance_criteria['sample_int_n']['value']
        else:
            cutoff_value=self.acceptance_criteria['site_int_n']['value']
        if cutoff_value != -999:
            if pars['N']<cutoff_value:
                pars['pass_or_fail']='fail'
                pars['fail_list'].append("int_n")
        #----------        
        # int_sigma ; int_sigma_perc
        pass_sigma,pass_sigma_perc=False,False
        if self.acceptance_criteria['average_by_sample_or_site']['value']=='sample':
            sigma_cutoff_value=self.acceptance_criteria['sample_int_sigma']['value']
        else:
            sigma_cutoff_value=self.acceptance_criteria['site_int_sigma']['value']
        
        if sigma_cutoff_value != -999:
            if pars['B_std_uT']*1e-6<=sigma_cutoff_value:
                pass_sigma=True

        if self.acceptance_criteria['average_by_sample_or_site']['value']=='sample':
            sigma_perc_cutoff_value=self.acceptance_criteria['sample_int_sigma_perc']['value']
        else:
            sigma_perc_cutoff_value=self.acceptance_criteria['site_int_sigma_perc']['value']
        if sigma_perc_cutoff_value != -999:
            if pars['B_std_perc']<=sigma_perc_cutoff_value:
                pass_sigma_perc=True

        if not (sigma_cutoff_value==-999 and sigma_perc_cutoff_value==-999):
            if not (pass_sigma or pass_sigma_perc):
                pars['pass_or_fail']='fail'
                pars['fail_list'].append("int_sigma")
                

        #if sigma_perc_cutoff_value!=-999 or sigma_cutoff_value!=-999:
        #    if not (pass_sigma or pass_sigma_perc):
        #        pars['pass_or_fail']='fail'
        #        pars['fail_list'].append("int_sigma")
           
        #----------        
        # int_sigma ; int_sigma_perc
        pass_int_interval,pass_int_interval_perc=False,False
        if self.acceptance_criteria['average_by_sample_or_site']['value']=='sample':
            cutoff_value=self.acceptance_criteria['sample_int_interval_uT']['value']
            if cutoff_value != -999:
                if pars['sample_int_interval_uT']<=cutoff_value:
                    pass_int_interval=True
    
            cutoff_value_perc=self.acceptance_criteria['sample_int_interval_perc']['value']
            if cutoff_value_perc != -999:
                if pars['sample_int_interval_perc']<=cutoff_value_perc:
                    pass_int_interval_perc=True

            if not (cutoff_value==-999 and cutoff_value_perc==-999):
                if not (pass_int_interval or pass_int_interval_perc):
                    pars['pass_or_fail']='fail'
                    pars['fail_list'].append("int_interval")
            
            
            #if cutoff_value != -999 or cutoff_value_perc != -999:
            #    if not (pass_int_interval or pass_int_interval_perc):
            #        pars['pass_or_fail']='fail'
            #        pars['fail_list'].append("int_interval")
             
            #
            #
            #                        
            #
            #if (acceptance_criteria['sample_int_sigma_uT']==0 and acceptance_criteria['sample_int_sigma_perc']==0) or\
            #    (pars['B_uT'] <= acceptance_criteria['sample_int_sigma_uT'] or pars['B_std_perc'] <= acceptance_criteria['sample_int_sigma_perc']):
            #        if ( pars['sample_int_interval_uT'] <= acceptance_criteria['sample_int_interval_uT'] or pars['sample_int_interval_perc'] <= acceptance_criteria['sample_int_interval_perc']):
            #            pars['pass_or_fail']='pass'
        return(pars)
        
        
    def convert_ages_to_calender_year(self,er_ages_rec):
        '''
        convert all age units to calender year
        '''

        if "age" not in  er_ages_rec.keys():
            return(er_ages_rec)
        if "age_unit" not in er_ages_rec.keys():
            return(er_ages_rec)
        if er_ages_rec["age_unit"]=="":
            return(er_ages_rec)

        if  er_ages_rec["age"]=="":
            if "age_range_high" in er_ages_rec.keys() and "age_range_low" in er_ages_rec.keys():
                if er_ages_rec["age_range_high"] != "" and  er_ages_rec["age_range_low"] != "":
                 er_ages_rec["age"]=scipy.mean([float(er_ages_rec["age_range_high"]),float(er_ages_rec["age_range_low"])])
        if  er_ages_rec["age"]=="":
            return(er_ages_rec)

            #age_descriptier_ages_recon=er_ages_rec["age_description"] 
        
            
        age_unit=er_ages_rec["age_unit"]
        
        # Fix 'age': 
        mutliplier=1
        if age_unit=="Ga":
            mutliplier=-1e9
        if age_unit=="Ma":
            mutliplier=-1e6
        if age_unit=="Ka":
            mutliplier=-1e3
        if age_unit=="Years AD (+/-)" or age_unit=="Years Cal AD (+/-)":
            mutliplier=1
        if age_unit=="Years BP" or age_unit =="Years Cal BP":
            mutliplier=1
        age = float(er_ages_rec["age"])*mutliplier
        if age_unit=="Years BP" or age_unit =="Years Cal BP":
            age=1950-age
        er_ages_rec['age_cal_year']=age   

        # Fix 'age_range_low':                        
        age_range_low=age
        age_range_high=age
        age_sigma=0
        
        if "age_sigma" in er_ages_rec.keys() and er_ages_rec["age_sigma"] !="":
            age_sigma=float(er_ages_rec["age_sigma"])*mutliplier
            if age_unit=="Years BP" or age_unit =="Years Cal BP":
                age_sigma=1950-age_sigma
            age_range_low= age-age_sigma
            age_range_high= age+age_sigma
            
        if "age_range_high" in er_ages_rec.keys() and "age_range_low" in er_ages_rec.keys():
            if er_ages_rec["age_range_high"] != "" and  er_ages_rec["age_range_low"] != "":
                age_range_high=float(er_ages_rec["age_range_high"])*mutliplier
                if age_unit=="Years BP" or age_unit =="Years Cal BP":
                    age_range_high=1950-age_range_high                              
                age_range_low=float(er_ages_rec["age_range_low"])*mutliplier
                if age_unit=="Years BP" or age_unit =="Years Cal BP":
                    age_range_low=1950-age_range_low                              
        er_ages_rec['age_cal_year_range_low']= age_range_low
        er_ages_rec['age_cal_year_range_high']= age_range_high
        
        return(er_ages_rec)
          

    #----------------------------------------------------------------------  
    #---------------------------------------------------------------------- 

    def On_close_plot_dialog(self,dia):
        import copy

        COLORS=['b','g','r','c','m','y','orange','gray','purple','brown','indigo','darkolivegreen','gold','mediumorchid','b','g','r','c','m','y','orange','gray','purple','brown','indigo','darkolivegreen','gold','mediumorchid']
        SYMBOLS=['o','d','h','p','s','*','v','<','>','^','o','d','h','p','s','*','v','<','>','^','o','d','h','p','s','*','v','<','>','^',]

        set_map_lat_min=""
        set_map_lat_max=""                      
        set_map_lat_grid=""                       
        set_map_lon_min=""
        set_map_lon_max=""
        set_map_lon_grid=""


        x_autoscale=dia.set_x_axis_auto.GetValue()
        try:
            x_axis_min=float(dia.set_plot_age_min.GetValue())
            x_axis_max=float(dia.set_plot_age_max.GetValue())
        except:
            pass
        
        y_autoscale=dia.set_y_axis_auto.GetValue()
        try:
            y_axis_min=float(dia.set_plot_intensity_min.GetValue())
            y_axis_max=float(dia.set_plot_intensity_max.GetValue())
        except:
            pass

        #plt_x_years=dia.set_plot_year.GetValue()
        #plt_x_BP=dia.set_plot_BP.GetValue()
        set_age_unit=dia.set_age_unit.GetValue()
        plt_B=dia.set_plot_B.GetValue()
        plt_VADM=dia.set_plot_VADM.GetValue()
        show_sample_labels=dia.show_samples_ID.GetValue()
        show_x_error_bar=dia.show_x_error_bar.GetValue()                                
        show_y_error_bar=dia.show_y_error_bar.GetValue()                                
        show_STDEVOPT=dia.show_STDEVOPT.GetValue()                                
        show_STDEVOPT_extended=dia.show_STDEVOPT_extended.GetValue()                                

        if show_STDEVOPT:
            data2plot={}
            if self.acceptance_criteria['average_by_sample_or_site']['value']=='sample':
                FILE=os.path.join(self.WD, 'thellier_interpreter', 'thellier_interpreter_STDEV-OPT_samples.txt')
                NAME="er_sample_name"
            else:
                FILE=os.path.join(self.WD, 'thellier_interpreter', 'thellier_interpreter_STDEV-OPT_sites.txt')
                NAME="er_site_name"
            try:
                data2plot=self.read_magic_file(FILE,4,NAME)
            except:
                data2plot={}
        else:
            if self.acceptance_criteria['average_by_sample_or_site']['value']=='sample':
                data2plot=copy.deepcopy(self.Data_samples)   
            else:
                data2plot=copy.deepcopy(self.Data_sites)
                #data2plot=copy.deepcopy(Data_samples_or_sites)

       
        show_map=dia.show_map.GetValue()
        set_map_autoscale=dia.set_map_autoscale.GetValue()
        if not set_map_autoscale:
            window_list_commands=["lat_min","lat_max","lat_grid","lon_min","lon_max","lon_grid"]
            for key in window_list_commands:
                try:
                    command="set_map_%s=float(dia.set_map_%s.GetValue())"%(key,key)
                    exec command
                except:
                    command="set_map_%s='' "%key
                    exec command
                    
            
            try:
                set_map_lat_min=float(dia.set_map_lat_min.GetValue())
                set_map_lat_max=float(dia.set_map_lat_max.GetValue() )                       
                set_map_lat_grid=float(dia.set_map_lat_grid.GetValue())                        
                set_map_lon_min=float(dia.set_map_lon_min.GetValue())
                set_map_lon_max=float(dia.set_map_lon_max.GetValue())
                set_map_lon_grid=float(dia.set_map_lon_grid.GetValue())
            except:
                pass
        plot_by_locations={}
 
            
        # search for lat (for VADM calculation) and age:        
        lat_min,lat_max,lon_min,lon_max=90,-90,180,-180
        age_min,age_max=1e10,-1e10
        #if not show_STDEVOPT:
        for sample_or_site in data2plot.keys():

            found_age,found_lat=False,False
            
            if not show_STDEVOPT:
                
                #calculate sample/site mean and check if pass criteria
                sample_or_site_mean_pars=self.calculate_sample_mean(data2plot[sample_or_site])#,sample_or_site,self.acceptance_criteria)
                if sample_or_site_mean_pars['pass_or_fail']!='pass':
                    continue
            else:
                sample_or_site_mean_pars=data2plot[sample_or_site]#,sample_or_site,self.acceptance_criteria)
                            
            # locate site_name
            if self.acceptance_criteria['average_by_sample_or_site']['value']=='sample':
                site_name=self.Data_hierarchy['site_of_sample'][sample_or_site] 
            else:
                site_name=sample_or_site

            #-----  
            # search for age data                                                                   
            #-----  
            er_ages_rec={}
            if sample_or_site in self.Data_info["er_ages"].keys():
                er_ages_rec=self.Data_info["er_ages"][sample_or_site]
            elif  site_name in  self.Data_info["er_ages"].keys():
                er_ages_rec=self.Data_info["er_ages"][site_name]
            if "age" in er_ages_rec.keys() and er_ages_rec["age"]!="":
                found_age=True

            if not found_age:
                continue                
           
            #elif "age_range_low" in er_ages_rec.keys() and er_ages_rec["age_range_low"]!="" and "age_range_high" in er_ages_rec.keys() and er_ages_rec["age_range_high"]!="":                
            #    found_age=True
            #    er_ages_rec["age"]=scipy.mean([float(er_ages_rec["age_range_low"]),float(er_ages_rec["age_range_high"])])
            if "age_description" in er_ages_rec.keys():
                age_description=er_ages_rec["age_description"] 
            else:
                age_description=""

            # ignore "poor" and "controversial" ages
            if "poor" in age_description or "controversial" in age_description:
                print "skipping sample %s because of age quality" %sample_or_site
                self.GUI_log.write( "-W- Plot: skipping sample %s because of age quality\n"%sample_or_site)
                continue

            age_min=min(age_min,float(er_ages_rec["age"]))
            age_max=max(age_max,float(er_ages_rec["age"]))
            #-----  
            # serch for latitude data
            #-----            
            found_lat,found_lon=False,False
            er_sites_rec={}
            if site_name in self.Data_info["er_sites"].keys():
                er_sites_rec=self.Data_info["er_sites"][site_name]
                if "site_lat" in er_sites_rec.keys() and er_sites_rec["site_lat"] != "":
                    found_lat=True
                    lat=float(er_sites_rec["site_lat"])
                else:
                    found_lat=False                     
                if "site_lon" in er_sites_rec.keys() and er_sites_rec["site_lon"] != "":
                    found_lon=True 
                    lon=float(er_sites_rec["site_lon"])
                    if lon >180:
                        lon=lon-360.

                else:
                    found_lon=False
                # convert lon to -180 to +180
            
            # tru searchinh latitude in er_samples.txt
             
            if found_lat==False:
                if sample_or_site in self.Data_info["er_samples"].keys():
                    er_samples_rec=self.Data_info["er_samples"][sample_or_site]
                    if "sample_lat" in er_samples_rec.keys() and er_samples_rec["sample_lat"] != "":
                        found_lat=True
                        lat=float(er_samples_rec["sample_lat"])
                    else:
                        found_lat=False                     
                    if "sample_lon" in er_samples_rec.keys() and er_samples_rec["sample_lon"] != "":
                        found_lon=True 
                        lon=float(er_samples_rec["sample_lon"])
                        if lon >180:
                            lon=lon-360.
    
                    else:
                        found_lon=False
                
            #-----  
            # search for latitude data
            # sort by locations
            # calculate VADM
            #-----

            if sample_or_site in self.Data_info["er_sites"].keys():
                    location=self.Data_info["er_sites"][sample_or_site]["er_location_name"]
            elif sample_or_site in self.Data_info["er_samples"].keys():
                    location=self.Data_info["er_samples"][sample_or_site]["er_location_name"]                            
            else:
                location="unknown"
            
            if location not in plot_by_locations.keys():
                plot_by_locations[location]={}
                plot_by_locations[location]['X_data'],plot_by_locations[location]['Y_data']=[],[]
                plot_by_locations[location]['X_data_plus'],plot_by_locations[location]['Y_data_plus']=[],[]
                plot_by_locations[location]['X_data_minus'],plot_by_locations[location]['Y_data_minus']=[],[]
                if show_STDEVOPT:
                    plot_by_locations[location]['Y_data_minus_extended'],plot_by_locations[location]['Y_data_plus_extended']=[],[]
                plot_by_locations[location]['samples_names']=[]
                plot_by_locations[location]['site_lon'],plot_by_locations[location]['site_lat']=[],[]
                    
            if found_lat:
                plot_by_locations[location]['site_lon']=lon
                plot_by_locations[location]['site_lat']=lat
                lat_min,lat_max=min(lat_min,lat),max(lat_max,lat)
                lon_min,lon_max=min(lon_min,lon),max(lon_max,lon)
            
            if show_STDEVOPT:    
                B_uT=float(sample_or_site_mean_pars['sample_int_uT'])
                B_std_uT=float(sample_or_site_mean_pars['sample_int_sigma_uT'])
                B_max_extended=float(sample_or_site_mean_pars['sample_int_max_uT'])+float(sample_or_site_mean_pars['sample_int_max_sigma_uT'])
                B_min_extended=float(sample_or_site_mean_pars['sample_int_min_uT'])-float(sample_or_site_mean_pars['sample_int_min_sigma_uT'])                    
            else:
                B_uT=float(sample_or_site_mean_pars['B_uT'])
                B_std_uT=float(sample_or_site_mean_pars['B_std_uT'])
                                
            if  plt_B:
                plot_by_locations[location]['Y_data'].append(B_uT)
                plot_by_locations[location]['Y_data_plus'].append(B_std_uT)
                plot_by_locations[location]['Y_data_minus'].append(B_std_uT)
                plot_by_locations[location]['samples_names'].append(sample_or_site)
                
                if show_STDEVOPT:
                    plot_by_locations[location]['Y_data_plus_extended'].append(B_max_extended-B_uT)
                    plot_by_locations[location]['Y_data_minus_extended'].append(B_uT-B_min_extended)
                                                                        
            elif plt_VADM and found_lat: # units of ZAm^2
                VADM=pmag.b_vdm(B_uT*1e-6,lat)*1e-21
                VADM_plus=pmag.b_vdm((B_uT+B_std_uT)*1e-6,lat)*1e-21
                VADM_minus=pmag.b_vdm((B_uT-B_std_uT)*1e-6,lat)*1e-21
                if show_STDEVOPT:
                    VADM_plus_extended= pmag.b_vdm((B_max_extended)*1e-6,lat)*1e-21
                    VADM_minus_extended=pmag.b_vdm((B_min_extended)*1e-6,lat)*1e-21
                
                plot_by_locations[location]['Y_data'].append(VADM)
                plot_by_locations[location]['Y_data_plus'].append(VADM_plus-VADM)
                plot_by_locations[location]['Y_data_minus'].append(VADM-VADM_minus)
                plot_by_locations[location]['samples_names'].append(sample_or_site)
                if show_STDEVOPT:
                    plot_by_locations[location]['Y_data_plus_extended'].append(VADM_plus_extended-VADM)
                    plot_by_locations[location]['Y_data_minus_extended'].append(VADM-VADM_minus_extended)

            elif plt_VADM and not found_lat:
                self.GUI_log.write( "-W- Plot: skipping sample %s because cant find latitude for V[A]DM calculation\n"%sample_or_site)
                print "-W- Plot: skipping sample %s because  cant find latitude for V[A]DM calculation\n"%sample_or_site
                continue

            #-----  
            # assign the right age
            #-----

            age=float(er_ages_rec["age_cal_year"])
            age_range_low=float(er_ages_rec["age_cal_year_range_low"])
            age_range_high = float(er_ages_rec["age_cal_year_range_high"])                                     

            # fix ages:
            if set_age_unit == "Years BP":
                age=1950-age
                age_range_high=1950-age_range_high
                age_range_low=1950-age_range_low
            if set_age_unit == "Ka":
                age=age/-1e3
                age_range_high=age_range_high/-1e3
                age_range_low=age_range_low/-1e3
            if set_age_unit == "Ma":
                age=age/-1e6
                age_range_high=age_range_high/-1e6
                age_range_low=age_range_low/-1e6
            if set_age_unit == "Ga":
                age=age/-1e9
                age_range_high=age_range_high/-1e9
                age_range_low=age_range_low/-1e9

            plot_by_locations[location]['X_data'].append(age)
            plot_by_locations[location]['X_data_plus'].append(age_range_high-age)
            plot_by_locations[location]['X_data_minus'].append(age-age_range_low)
            
            found_age=False
            found_lat=False                            


        #--------
        # map
        #--------
        # read in topo data (on a regular lat/lon grid)
        # longitudes go from 20 to 380.
        Plot_map=show_map
        if Plot_map:
            if True:
                from mpl_toolkits.basemap import Basemap
                from mpl_toolkits.basemap import basemap_datadir
                ion()
                fig2=figure(2)
                clf()
                ioff()

                SiteLat_min=lat_min-5
                SiteLat_max=lat_max+5
                SiteLon_min=lon_min-5
                SiteLon_max=lon_max+5
                
                if not set_map_autoscale:
                    if set_map_lat_min!="":
                        SiteLat_min=set_map_lat_min
                    if set_map_lat_max !="":
                        SiteLat_max=set_map_lat_max
                    if set_map_lon_min !="":
                        SiteLon_min=set_map_lon_min
                    if set_map_lon_max !="":
                        SiteLon_max=set_map_lon_max 
                                        

                m=Basemap(llcrnrlon=SiteLon_min,llcrnrlat=SiteLat_min,urcrnrlon=SiteLon_max,urcrnrlat=SiteLat_max,projection='merc',resolution='i')

                if set_map_lat_grid !="" and set_map_lon_grid!=0:
                    m.drawparallels(np.arange(SiteLat_min,SiteLat_max+set_map_lat_grid,set_map_lat_grid),linewidth=0.5,labels=[1,0,0,0],fontsize=10)
                    m.drawmeridians(np.arange(SiteLon_min,SiteLon_max+set_map_lon_grid,set_map_lon_grid),linewidth=0.5,labels=[0,0,0,1],fontsize=10)

                else:
                    pass
                    '''lat_min_round=SiteLat_min-SiteLat_min%10
                    lat_max_round=SiteLat_max-SiteLat_max%10
                    lon_min_round=SiteLon_min-SiteLon_min%10
                    lon_max_round=SiteLon_max-SiteLon_max%10
                    m.drawparallels(np.arange(lat_min_round,lat_max_round+5,5),linewidth=0.5,labels=[1,0,0,0],fontsize=10)
                    m.drawmeridians(np.arange(lon_min_round,lon_max_round+5,5),linewidth=0.5,labels=[0,0,0,1],fontsize=10)'''

                m.fillcontinents(zorder=0,color='0.9')
                m.drawcoastlines()
                m.drawcountries()
                m.drawmapboundary()
            else:
                print "Cant plot map. Is basemap installed?"
        cnt=0    

        #-----  
        # draw paleointensity errorbar plot
        #-----

        # fix ages
            
        Fig=figure(1,(15,6))
        clf()
        ax = axes([0.3,0.1,0.6,0.8])
        locations =plot_by_locations.keys()
        locations.sort()
        handles_list=[]
        for location in locations:
            figure(1)
            X_data,X_data_minus,X_data_plus=plot_by_locations[location]['X_data'],plot_by_locations[location]['X_data_minus'],plot_by_locations[location]['X_data_plus']
            Y_data,Y_data_minus,Y_data_plus=plot_by_locations[location]['Y_data'],plot_by_locations[location]['Y_data_minus'],plot_by_locations[location]['Y_data_plus']
            if show_STDEVOPT:
                Y_data_minus_extended,Y_data_plus_extended=plot_by_locations[location]['Y_data_minus_extended'],plot_by_locations[location]['Y_data_plus_extended']
                
                                
            if not show_x_error_bar:
                Xerr=None
            else:
                Xerr=[scipy.array(X_data_minus),scipy.array(X_data_plus)]

            if not show_y_error_bar:
                Yerr=None
            else:
                Yerr=[Y_data_minus,Y_data_plus]

            erplot=errorbar(X_data,Y_data,xerr=Xerr,yerr=Yerr,fmt=SYMBOLS[cnt%len(SYMBOLS)],color=COLORS[cnt%len(COLORS)],label=location)
            handles_list.append(erplot)
            if show_STDEVOPT:
                errorbar(X_data,Y_data,xerr=None,yerr=[Y_data_minus_extended,Y_data_plus_extended],fmt='.',ms=0,ecolor='red',label="extended error-bar",zorder=0)
                

            if Plot_map:
                figure(2)
                lat=plot_by_locations[location]['site_lat']
                lon=plot_by_locations[location]['site_lon']
                x1,y1=m([lon],[lat])
                m.scatter(x1,y1,s=[50],marker=SYMBOLS[cnt%len(SYMBOLS)],color=COLORS[cnt%len(COLORS)],edgecolor='black')
            cnt+=1
                
        #fig1=figure(1)#,(15,6))
        
        legend_font_props = matplotlib.font_manager.FontProperties()
        legend_font_props.set_size(12)

        #h,l = ax.get_legend_handles_labels()
        legend(handles=handles_list,loc='center left', bbox_to_anchor=[0, 0, 1, 1],bbox_transform=Fig.transFigure,numpoints=1,prop=legend_font_props)

        #Fig.legend(h,l,loc='center left',fancybox="True",numpoints=1,prop=legend_font_props)
        y_min,y_max=ylim()
        if y_min<0:
            ax.set_ylim(ymin=0)

        if plt_VADM:
            #ylabel("VADM ZAm^2")
            ax.set_ylabel(r'VADM  $Z Am^2$',fontsize=12)

        if plt_B:
            #ylabel("B (microT)")
            ax.set_ylabel(r'B  $\mu T$',fontsize=12)
        #if plt_x_BP:
        #    #xlabel("years BP")
        #    ax.set_xlabel("years BP",fontsize=12)
        #if plt_x_years:
        #    #xlabel("Date")
        #    ax.set_xlabel("Date",fontsize=12)
        if set_age_unit=="Automatic":
            ax.set_xlabel("Age",fontsize=12)
        else:    
            ax.set_xlabel(set_age_unit,fontsize=12)
        
        if not x_autoscale:
            try:
                ax.set_xlim(xmin=x_axis_min)
            except:
                pass
            try:
                ax.set_xlim(xmax=x_axis_max)
            except:
                pass
            

        if not y_autoscale:
            try:
                ax.set_ylim(ymin=y_axis_min)
            except:
                pass
            try:
                ax.set_ylim(ymax=y_axis_max)
            except:
                pass

        
        #Fig.legend(legend_labels,locations,'upper right',numpoints=1,title="Locations")
        if  show_sample_labels:
            for location in locations:
                for i in  range(len(plot_by_locations[location]['samples_names'])):
                    Fig.text(plot_by_locations[location]['X_data'][i],plot_by_locations[location]['Y_data'][i],"  "+ plot_by_locations[location]['samples_names'][i],fontsize=10,color="0.5")

        xmin,xmax=xlim()
        #print "xmin,xmax",xmin,xmax
        if max ([abs(xmin), abs(xmax) ]) > 10000 and set_age_unit=="Automatic":
            gca().ticklabel_format(style='scientific', axis='x',scilimits=(0,0))
       # matplotlib.pyplot.ticklabel_format(style='scientific', axis='x')

        #fr=thellier_gui_dialogs.ShowPlot(None,fig1)
        #panel = CanvasPanel(fr)
        #panel.draw()
        #fr.Show()
        #PI_Fig.Show()
        #Fig.show()
        thellier_gui_dialogs.ShowFigure(Fig)
        dia.Destroy()
        #Fig.show()
    
#===========================================================
# Draw plots
#===========================================================
       
        
    def draw_figure(self,s):
        #start_time = time.time()


        #-----------------------------------------------------------
        # Draw Arai plot
        #-----------------------------------------------------------
        self.s=s

        self.x_Arai_ZI,self.y_Arai_ZI=[],[]
        self.x_Arai_IZ,self.y_Arai_IZ=[],[]
        self.x_Arai=self.Data[self.s]['x_Arai']
        self.y_Arai=self.Data[self.s]['y_Arai']
        self.pars=self.Data[self.s]['pars']
        self.x_tail_check=self.Data[self.s]['x_tail_check']
        self.y_tail_check=self.Data[self.s]['y_tail_check']
        
        #self.x_additivity_check=self.Data[self.s]['x_additivity_check']
        #self.y_additivity_check=self.Data[self.s]['y_additivity_check']

        self.araiplot.clear()        
        self.araiplot.plot(self.Data[self.s]['x_Arai'],self.Data[self.s]['y_Arai'],'0.2',lw=0.75,clip_on=False)

        for i in range(len(self.Data[self.s]['steps_Arai'])):
          if self.Data[self.s]['steps_Arai'][i]=="ZI":
            self.x_Arai_ZI.append(self.Data[self.s]['x_Arai'][i])
            self.y_Arai_ZI.append(self.Data[self.s]['y_Arai'][i])
          elif self.Data[self.s]['steps_Arai'][i]=="IZ":
            self.x_Arai_IZ.append(self.Data[self.s]['x_Arai'][i])
            self.y_Arai_IZ.append(self.Data[self.s]['y_Arai'][i])
          else:
             self.GUI_log.write("-E- Cant plot Arai plot. check the data for specimen %s\n"%s)
        if len(self.x_Arai_ZI)>0:
            self.araiplot.scatter (self.x_Arai_ZI,self.y_Arai_ZI,marker='o',facecolor='r',edgecolor ='k',s=25*self.GUI_RESOLUTION,clip_on=False)
        if len(self.x_Arai_IZ)>0:
            self.araiplot.scatter (self.x_Arai_IZ,self.y_Arai_IZ,marker='o',facecolor='b',edgecolor ='k',s=25*self.GUI_RESOLUTION,clip_on=False)

        # pTRM checks
        if 'x_ptrm_check' in self.Data[self.s]:
            if len(self.Data[self.s]['x_ptrm_check'])>0:
                self.araiplot.scatter (self.Data[self.s]['x_ptrm_check'],self.Data[self.s]['y_ptrm_check'],marker='^',edgecolor='0.1',alpha=1.0, facecolor='None',s=80*self.GUI_RESOLUTION,lw=1)
                if self.preferences['show_Arai_pTRM_arrows']:
                    for i in range(len(self.Data[self.s]['x_ptrm_check'])):
                        xx1,yy1=self.Data[s]['x_ptrm_check_starting_point'][i],self.Data[s]['y_ptrm_check_starting_point'][i]
                        xx2,yy2=self.Data[s]['x_ptrm_check'][i],self.Data[s]['y_ptrm_check'][i]
                        self.araiplot.plot([xx1,xx2],[yy1,yy1],color="0.5",lw=0.5,alpha=0.5,clip_on=False)
                        self.araiplot.plot([xx2,xx2],[yy1,yy2],color="0.5",lw=0.5,alpha=0.5,clip_on=False)

        # Tail checks
        if len(self.x_tail_check >0):
          self.araiplot.scatter (self.x_tail_check,self.y_tail_check,marker='s',edgecolor='0.1',alpha=1.0, facecolor='None',s=80*self.GUI_RESOLUTION,lw=1,clip_on=False)


        # Additivity checks

        # pTRM checks
        if 'x_additivity_check' in self.Data[self.s]:
            if len(self.Data[self.s]['x_additivity_check'])>0:
                self.araiplot.scatter (self.Data[self.s]['x_additivity_check'],self.Data[self.s]['y_additivity_check'],marker='D',edgecolor='0.1',alpha=1.0, facecolor='None',s=80*self.GUI_RESOLUTION,lw=1,clip_on=False)
                if self.preferences['show_Arai_pTRM_arrows']:
                    for i in range(len(self.Data[self.s]['x_additivity_check'])):
                        xx1,yy1=self.Data[s]['x_additivity_check_starting_point'][i],self.Data[s]['y_additivity_check_starting_point'][i]
                        xx2,yy2=self.Data[s]['x_additivity_check'][i],self.Data[s]['y_additivity_check'][i]
                        self.araiplot.plot([xx1,xx1],[yy1,yy2],color="0.5",lw=0.5,alpha=0.5,clip_on=False)
                        self.araiplot.plot([xx1,xx2],[yy2,yy2],color="0.5",lw=0.5,alpha=0.5,clip_on=False)

        # Arai plot temperatures


        for i in range(len(self.Data[self.s]['t_Arai'])):
          if self.Data[self.s]['t_Arai'][i]!=0:
            if self.Data[self.s]['T_or_MW']!="MW":
                self.tmp_c=self.Data[self.s]['t_Arai'][i]-273.
            else:
                self.tmp_c=self.Data[self.s]['t_Arai'][i]
          else:
            self.tmp_c=0.
          if self.preferences['show_Arai_temperatures'] and int(self.preferences['show_Arai_temperatures_steps'])!=1:
              if (i+1)%int(self.preferences['show_Arai_temperatures_steps']) ==0 and i!=0:
                  self.araiplot.text(self.x_Arai[i],self.y_Arai[i],"  %.0f"%self.tmp_c,fontsize=10,color='gray',ha='left',va='center',clip_on=False)                  
          elif not self.preferences['show_Arai_temperatures']:
              continue
          else:
              self.araiplot.text(self.x_Arai[i],self.y_Arai[i],"  %.0f"%self.tmp_c,fontsize=10,color='gray',ha='left',va='center',clip_on=False)





##        if len(self.x_additivity_check >0):
##          self.araiplot.scatter (self.x_additivity_check,self.y_additivity_check,marker='D',edgecolor='0.1',alpha=1.0, facecolor='None',s=80*self.GUI_RESOLUTION,lw=1)


        if   self.GUI_RESOLUTION >1.1:
            FONTSIZE=11
        elif   self.GUI_RESOLUTION <0.9:
            FONTSIZE=9
        else:
            FONTSIZE=10

        if   self.GUI_RESOLUTION >1.1:
            FONTSIZE_1=11
        elif   self.GUI_RESOLUTION <0.9:
            FONTSIZE_1=9
        else:
            FONTSIZE_1=10

                                
        self.araiplot.set_xlabel("TRM / NRM0",fontsize=FONTSIZE)
        self.araiplot.set_ylabel("NRM / NRM0",fontsize=FONTSIZE)
        self.araiplot.set_xlim(xmin=0)
        self.araiplot.set_ylim(ymin=0)


        
        #search for NRM:
        nrm0=""
        for rec in self.Data[self.s]['datablock']:            
          if "LT-NO" in rec['magic_method_codes']:
              nrm0= "%.2e"%float(rec['measurement_magn_moment'])
              break

            
        #self.fig1.text(0.05,0.93,r'$NRM0 = %s Am^2 $'%(nrm0),{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'left' })

        #draw()
        self.canvas1.draw()
        self.arai_xlim_initial=self.araiplot.axes.get_xlim() 
        self.arai_ylim_initial=self.araiplot.axes.get_ylim() 

        #start_time_2=time.time() 
        #runtime_sec2 = start_time_2 - start_time
        #print "-I- draw Arai figures is", runtime_sec2,"seconds"

        #-----------------------------------------------------------
        # Draw Zij plot
        #-----------------------------------------------------------

        self.zijplot.clear()
        self.MS=6*self.GUI_RESOLUTION;self.dec_MEC='k';self.dec_MFC='b'; self.inc_MEC='k';self.inc_MFC='r'
        self.CART_rot=self.Data[self.s]['zij_rotated']
        self.z_temperatures=self.Data[self.s]['z_temp']
        self.vds=self.Data[self.s]['vds']
        self.zijplot.plot(self.CART_rot[:,0],-1* self.CART_rot[:,1],'bo-',mfc=self.dec_MFC,mec=self.dec_MEC,markersize=self.MS,clip_on=False)  #x,y or N,E
        self.zijplot.plot(self.CART_rot[:,0],-1 * self.CART_rot[:,2],'rs-',mfc=self.inc_MFC,mec=self.inc_MEC,markersize=self.MS,clip_on=False)   #x-z or N,D
        #self.zijplot.axhline(0,c='k')
        #self.zijplot.axvline(0,c='k')
        self.zijplot.axis('off')
        self.zijplot.axis('equal')

        #title(Data[s]['pars']['er_specimen_name']+"\nrotated Zijderveld plot",fontsize=12)
        last_cart_1=scipy.array([self.CART_rot[0][0],self.CART_rot[0][1]])
        last_cart_2=scipy.array([self.CART_rot[0][0],self.CART_rot[0][2]])
        if self.Data[self.s]['T_or_MW']!="T":
            K_diff=0
        else:
            K_diff=273
            
        if self.preferences['show_Zij_temperatures'] :
            for i in range(len(self.z_temperatures)):
                if int(self.preferences['show_Zij_temperatures_steps']) !=1:
                    if i!=0  and (i+1)%int(self.preferences['show_Zij_temperatures_steps'])==0:
                        self.zijplot.text(self.CART_rot[i][0],-1*self.CART_rot[i][2]," %.0f"%(self.z_temperatures[i]-K_diff),fontsize=FONTSIZE,color='gray',ha='left',va='center',clip_on=False)   #inc
                else:
                  self.zijplot.text(self.CART_rot[i][0],-1*self.CART_rot[i][2]," %.0f"%(self.z_temperatures[i]-K_diff),fontsize=FONTSIZE,color='gray',ha='left',va='center',clip_on=False)   #inc

        #-----
        xmin, xmax = self.zijplot.get_xlim()
        if xmax <0:
            xmax=0
        if xmin>0:
            xmin=0
        props = dict(color='black', linewidth=0.5, markeredgewidth=0.5)

        #xlocs = [loc for loc in self.zijplot.xaxis.get_majorticklocs()
        #        if loc>=xmin and loc<=xmax]
        xlocs = scipy.arange(xmin,xmax,0.2)
        xtickline, = self.zijplot.plot(xlocs, [0]*len(xlocs),linestyle='',
                marker='+', **props)

        axxline, = self.zijplot.plot([xmin, xmax], [0, 0], **props)
        xtickline.set_clip_on(False)
        axxline.set_clip_on(False)
        self.zijplot.text(xmax,0,' x',fontsize=10,verticalalignment='bottom',clip_on=False)

        #-----

        ymin, ymax = self.zijplot.get_ylim()
        if ymax <0:
            ymax=0
        if ymin>0:
            ymin=0
        
        ylocs = [loc for loc in self.zijplot.yaxis.get_majorticklocs()
                if loc>=ymin and loc<=ymax]
        ylocs = scipy.arange(ymin,ymax,0.2)

        ytickline, = self.zijplot.plot([0]*len(ylocs),ylocs,linestyle='',
                marker='+', **props)

        axyline, = self.zijplot.plot([0, 0],[ymin, ymax], **props)
        ytickline.set_clip_on(False)
        axyline.set_clip_on(False)
        self.zijplot.text(0,ymin,' y,z',fontsize=10,verticalalignment='top',clip_on=False)

        #----


        self.zij_xlim_initial=self.zijplot.axes.get_xlim() 
        self.zij_ylim_initial=self.zijplot.axes.get_ylim() 

        self.canvas2.draw()
        
        #start_time_3=time.time() 
        #runtime_sec3 = start_time_3 - start_time_2
        #print "-I- draw Zij figures is", runtime_sec3,"seconds"

        #-----------------------------------------------------------
        # Draw Cooling rate data
        #-----------------------------------------------------------

        if self.preferences['show_CR_plot'] ==False or 'crblock' not in self.Data[self.s].keys():

            self.fig3.clf()
            self.fig3.text(0.02,0.96,"Equal area",{'family':'Arial', 'fontsize':FONTSIZE, 'style':'normal','va':'center', 'ha':'left' })
            self.eqplot = self.fig3.add_subplot(111)


            self.draw_net()

            self.zij=scipy.array(self.Data[self.s]['zdata'])
            self.zij_norm=scipy.array([row/scipy.sqrt(sum(row**2)) for row in self.zij])

            x_eq=scipy.array([row[0] for row in self.zij_norm])
            y_eq=scipy.array([row[1] for row in self.zij_norm])
            z_eq=abs(scipy.array([row[2] for row in self.zij_norm]))

            R=scipy.array(scipy.sqrt(1-z_eq)/scipy.sqrt(x_eq**2+y_eq**2)) # from Collinson 1983
            eqarea_data_x=y_eq*R
            eqarea_data_y=x_eq*R
            self.eqplot.plot(eqarea_data_x,eqarea_data_y,lw=0.5,color='gray',clip_on=False)
            #self.eqplot.scatter([eqarea_data_x_dn[i]],[eqarea_data_y_dn[i]],marker='o',edgecolor='0.1', facecolor='blue',s=15,lw=1)


            x_eq_dn,y_eq_dn,z_eq_dn,eq_dn_temperatures=[],[],[],[]
            x_eq_dn=scipy.array([row[0] for row in self.zij_norm if row[2]>0])
            y_eq_dn=scipy.array([row[1] for row in self.zij_norm if row[2]>0])
            z_eq_dn=abs(scipy.array([row[2] for row in self.zij_norm if row[2]>0]))
            
            if len(x_eq_dn)>0:
                R=scipy.array(scipy.sqrt(1-z_eq_dn)/scipy.sqrt(x_eq_dn**2+y_eq_dn**2)) # from Collinson 1983
                eqarea_data_x_dn=y_eq_dn*R
                eqarea_data_y_dn=x_eq_dn*R
                self.eqplot.scatter([eqarea_data_x_dn],[eqarea_data_y_dn],marker='o',edgecolor='gray', facecolor='black',s=15*self.GUI_RESOLUTION,lw=1,clip_on=False)
                        
                

            x_eq_up,y_eq_up,z_eq_up=[],[],[]
            x_eq_up=scipy.array([row[0] for row in self.zij_norm if row[2]<=0])
            y_eq_up=scipy.array([row[1] for row in self.zij_norm if row[2]<=0])
            z_eq_up=abs(scipy.array([row[2] for row in self.zij_norm if row[2]<=0]))
            if len(x_eq_up)>0:
                R=scipy.array(scipy.sqrt(1-z_eq_up)/scipy.sqrt(x_eq_up**2+y_eq_up**2)) # from Collinson 1983
                eqarea_data_x_up=y_eq_up*R
                eqarea_data_y_up=x_eq_up*R
                self.eqplot.scatter([eqarea_data_x_up],[eqarea_data_y_up],marker='o',edgecolor='black', facecolor='white',s=15*self.GUI_RESOLUTION,lw=1,clip_on=False)        

            if   self.GUI_RESOLUTION >1.1:
                FONTSIZE_1=9
            elif   self.GUI_RESOLUTION <0.9:
                FONTSIZE_1=8
            else:
                FONTSIZE_1=7
                        
            if self.preferences['show_eqarea_temperatures']:
                for i in range(len(self.z_temperatures)):
                    if self.Data[self.s]['T_or_MW']!="MW":
                        K_dif=0.
                    else:
                        K_dif=273.                    
                    self.eqplot.text(eqarea_data_x[i],eqarea_data_y[i],"%.0f"%(float(self.z_temperatures[i])-K_dif),fontsize=FONTSIZE_1,color="0.5",clip_on=False)
            
            
            #self.eqplot.text(eqarea_data_x[0],eqarea_data_y[0]," NRM",fontsize=8,color='gray',ha='left',va='center')


            # In-field steps" self.preferences["show_eqarea_pTRMs"]
            if self.preferences["show_eqarea_pTRMs"]:
                eqarea_data_x_up,eqarea_data_y_up=[],[]
                eqarea_data_x_dn,eqarea_data_y_dn=[],[]
                PTRMS=self.Data[self.s]['PTRMS'][1:]
                CART_pTRMS_orig=scipy.array([pmag.dir2cart(row[1:4]) for row in PTRMS])
                CART_pTRMS=[row/scipy.sqrt(sum((scipy.array(row)**2))) for row in CART_pTRMS_orig]
                                 
                for i in range(1,len(CART_pTRMS)):
                    if CART_pTRMS[i][2]<=0:
                        R=scipy.sqrt(1.-abs(CART_pTRMS[i][2]))/scipy.sqrt(CART_pTRMS[i][0]**2+CART_pTRMS[i][1]**2)
                        eqarea_data_x_up.append(CART_pTRMS[i][1]*R)
                        eqarea_data_y_up.append(CART_pTRMS[i][0]*R)
                    else:
                        R=scipy.sqrt(1.-abs(CART_pTRMS[i][2]))/scipy.sqrt(CART_pTRMS[i][0]**2+CART_pTRMS[i][1]**2)
                        eqarea_data_x_dn.append(CART_pTRMS[i][1]*R)
                        eqarea_data_y_dn.append(CART_pTRMS[i][0]*R)
                if len(eqarea_data_x_up)>0:
                    self.eqplot.scatter(eqarea_data_x_up,eqarea_data_y_up,marker='^',edgecolor='blue', facecolor='white',s=15*self.GUI_RESOLUTION,lw=1,clip_on=False)
                if len(eqarea_data_x_dn)>0:
                    self.eqplot.scatter(eqarea_data_x_dn,eqarea_data_y_dn,marker='^',edgecolor='gray', facecolor='blue',s=15*self.GUI_RESOLUTION,lw=1,clip_on=False)        
            self.canvas3.draw()
    
        else:

            self.fig3.clf()
            self.fig3.text(0.02,0.96,"Cooling rate experiment",{'family':'Arial', 'fontsize':FONTSIZE, 'style':'normal','va':'center', 'ha':'left' })
            self.eqplot = self.fig3.add_axes([0.2,0.15,0.7,0.7],frameon=True,axisbg='None')

            if 'cooling_rate_data' in self.Data[self.s].keys() and\
            'ancient_cooling_rate' in self.Data[self.s]['cooling_rate_data'].keys() and\
            'lab_cooling_rate' in self.Data[self.s]['cooling_rate_data'].keys():
                ancient_cooling_rate=self.Data[self.s]['cooling_rate_data']['ancient_cooling_rate']
                lab_cooling_rate=self.Data[self.s]['cooling_rate_data']['lab_cooling_rate']
                x0=scipy.math.log(lab_cooling_rate/ancient_cooling_rate)
                y0=1./self.Data[self.s]['cooling_rate_data']['CR_correction_factor']
                lan_cooling_rates=self.Data[self.s]['cooling_rate_data']['lan_cooling_rates']
                moment_norm=self.Data[self.s]['cooling_rate_data']['moment_norm']
                (a,b)=self.Data[self.s]['cooling_rate_data']['polyfit']
                y0=a*x0+b
            
                x=linspace(0,x0,10)
                y=polyval([a,b],x)
                self.eqplot.plot(x,y,"--",color='k')
                
                self.eqplot.scatter(lan_cooling_rates,moment_norm,marker='o',facecolor='b',edgecolor ='k',s=25,clip_on=False)
                self.eqplot.scatter([x0],[y0],marker='s',facecolor='r',edgecolor ='k',s=25,clip_on=False)
    
    
                #self.Data_info["er_samples"][
                self.eqplot.set_ylabel("TRM / TRM[oven]",fontsize=FONTSIZE_1)
                self.eqplot.set_xlabel("ln(CR[oven]/CR)",fontsize=FONTSIZE_1)
                self.eqplot.set_xlim(left=-0.2)
                try:
                    self.eqplot.tick_params(axis='both', which='major', labelsize=8)
                except:
                    pass
                #self.mplot.tick_params(axis='x', which='major', labelsize=8)          
                self.eqplot.spines["right"].set_visible(False)
                self.eqplot.spines["top"].set_visible(False)
                self.eqplot.get_xaxis().tick_bottom()
                self.eqplot.get_yaxis().tick_left()
            
            #draw()
            self.canvas3.draw()

        #-----------------------------------------------------------
        # Draw sample plot (or cooling rate experiment data)
        #-----------------------------------------------------------


        self.draw_sample_mean()
        
        #-----------------------------------------------------------
        # Draw M/M0 plot ( or NLT data on the same area in the GUI)
        #-----------------------------------------------------------
        self.fig5.clf()

        if self.preferences['show_NLT_plot'] ==False or 'NLT_parameters' not in self.Data[self.s].keys():
            self.fig5.clf()
            self.fig5.text(0.02,0.96,"M/T",{'family':'Arial', 'fontsize':FONTSIZE, 'style':'normal','va':'center', 'ha':'left' })
            self.mplot = self.fig5.add_axes([0.2,0.15,0.7,0.7],frameon=True,axisbg='None')
            
            self.mplot.clear()
            NRMS=self.Data[self.s]['NRMS']
            PTRMS=self.Data[self.s]['PTRMS']

            if self.Data[self.s]['T_or_MW']!="MW":
                temperatures_NRMS=scipy.array([row[0]-273. for row in NRMS])
                temperatures_PTRMS=scipy.array([row[0]-273. for row in PTRMS])
                temperatures_NRMS[0]=21
                temperatures_PTRMS[0]=21
            else:
                temperatures_NRMS=scipy.array([row[0] for row in NRMS])
                temperatures_PTRMS=scipy.array([row[0] for row in PTRMS])
            
            if len(temperatures_NRMS)!=len(temperatures_PTRMS):
              self.GUI_log.write("-E- ERROR: NRMS and pTRMS are not equal in specimen %s. Check\n."%self.s)
            else:
              M_NRMS=scipy.array([row[3] for row in NRMS])/NRMS[0][3]
              M_pTRMS=scipy.array([row[3] for row in PTRMS])/NRMS[0][3]

              self.mplot.clear()
              self.mplot.plot(temperatures_NRMS,M_NRMS,'bo-',mec='0.2',markersize=5*self.GUI_RESOLUTION,lw=1,clip_on=False)
              self.mplot.plot(temperatures_NRMS,M_pTRMS,'ro-',mec='0.2',markersize=5*self.GUI_RESOLUTION,lw=1,clip_on=False)
              if self.Data[self.s]['T_or_MW']!="MW":
                  self.mplot.set_xlabel("C",fontsize=FONTSIZE_1)
              else:
                  self.mplot.set_xlabel("Treatment",fontsize=FONTSIZE_1)                  
              self.mplot.set_ylabel("M / NRM0",fontsize=FONTSIZE_1)
              #self.mplot.set_xtick(labelsize=2)
              try:
                  self.mplot.tick_params(axis='both', which='major', labelsize=8)
              except:
                  pass
              #self.mplot.tick_params(axis='x', which='major', labelsize=8)          
              self.mplot.spines["right"].set_visible(False)
              self.mplot.spines["top"].set_visible(False)
              self.mplot.get_xaxis().tick_bottom()
              self.mplot.get_yaxis().tick_left()
              
              #xt=xticks()

            #start_time_6=time.time() 
            #runtime_sec6 = start_time_6 - start_time_5
            #print "-I- draw M-M0 figures is", runtime_sec6,"seconds"

            #runtime_sec = time.time() - start_time
            #print "-I- draw figures is", runtime_sec,"seconds"


        #-----------------------------------------------------------
        # Draw NLT plot
        #-----------------------------------------------------------

        
        else:
            self.fig5.clf()
            self.fig5.text(0.02,0.96,"Non-linear TRM check",{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'left' })
            self.mplot = self.fig5.add_axes([0.2,0.15,0.7,0.7],frameon=True,axisbg='None')
            #self.mplot.clear()
            self.mplot.scatter(scipy.array(self.Data[self.s]['NLT_parameters']['B_NLT'])*1e6,self.Data[self.s]['NLT_parameters']['M_NLT_norm'],marker='o',facecolor='b',edgecolor ='k',s=15,clip_on=False)
            self.mplot.set_xlabel("$\mu$ T",fontsize=8)
            self.mplot.set_ylabel("M / M[%.0f]"%(self.Data[self.s]['lab_dc_field']*1e6),fontsize=8)
            try:
                self.mplot.tick_params(axis='both', which='major', labelsize=8)
            except:
                pass
            #self.mplot.frametick_pa.set_linewidth(0.01)
            self.mplot.set_xlim(xmin=0)
            self.mplot.set_ylim(ymin=0)
            xmin,xmax=self.mplot.get_xlim()
            x=linspace(xmin+0.1,xmax,100)
            alpha=self.Data[self.s]['NLT_parameters']['tanh_parameters'][0][0]
            beta=self.Data[self.s]['NLT_parameters']['tanh_parameters'][0][1]
            y=alpha*(scipy.tanh(x*1e-6*beta))
            labfiled=self.Data[self.s]['lab_dc_field']
            self.mplot.plot(x,x*1e-6*(alpha*(scipy.tanh(labfiled*beta))/labfiled),'--',color='black',linewidth=0.7,clip_on=False)
            self.mplot.plot(x,y,'-',color='green',linewidth=1)
            
            #self.mplot.spines["right"].set_visible(False)
            #self.mplot.spines["top"].set_visible(False)
            #self.mplot.get_xaxis().tick_bottom()
            #self.mplot.get_yaxis().tick_left()

        self.canvas5.draw()
        
        #Data[s]['NLT_parameters']v


    def draw_net(self):
        self.eqplot.clear()
        eq=self.eqplot
        eq.axis((-1,1,-1,1))
        eq.axis('off')
        theta = scipy.arange(0.,2 * scipy.pi, 2 * scipy.pi/1000)
        eq.plot(scipy.cos(theta),scipy.sin(theta),'k',clip_on=False)
        eq.vlines((0,0),(0.9,-0.9),(1.0,-1.0),'k')
        eq.hlines((0,0),(0.9,-0.9),(1.0,-1.0),'k')
        eq.plot([0.0],[0.0],'+k',clip_on=False)
        return()


    #===========================================================
    # Zoom properties 
    #===========================================================
        
    def Arai_zoom(self):
        cursur_entry_arai=self.canvas1.mpl_connect('axes_enter_event', self.on_enter_arai_fig) 
        cursur_leave_arai=self.canvas1.mpl_connect('axes_leave_event', self.on_leave_arai_fig)

    def on_leave_arai_fig(self,event):
        self.canvas1.mpl_disconnect(self.cid1)
        self.canvas1.mpl_disconnect(self.cid2)
        self.canvas1.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
        self.curser_in_arai_figure=False
                
    def on_enter_arai_fig(self,event):
        self.curser_in_arai_figure=True
        self.canvas1.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))
        cid1=self.canvas1.mpl_connect('button_press_event', self.onclick)
        cid2=self.canvas1.mpl_connect('button_release_event', self.onclick_2)

    def onclick(self,event):
        if self.curser_in_arai_figure:
            self.tmp1_x=event.xdata
            self.tmp1_y=event.ydata
        
    def onclick_2(self,event):
        self.canvas1.mpl_connect('axes_leave_event', self.on_leave_arai_fig)
        if self.curser_in_arai_figure:
            try:
                self.tmp2_x=event.xdata
                self.tmp2_y=event.ydata
                if self.tmp1_x < self.tmp2_x and self.tmp1_y > self.tmp2_y:
                    self.araiplot.set_xlim(xmin=self.tmp1_x,xmax=self.tmp2_x)
                    self.araiplot.set_ylim(ymin=self.tmp2_y,ymax=self.tmp1_y)
                else:
                    self.araiplot.set_xlim(xmin=self.arai_xlim_initial[0],xmax=self.arai_xlim_initial[1])
                    self.araiplot.set_ylim(ymin=self.arai_ylim_initial[0],ymax=self.arai_ylim_initial[1])
                self.canvas1.draw()
            except:
                pass
        else:
            return
        
    def Zij_zoom(self):
        cursur_entry_arai=self.canvas1.mpl_connect('axes_enter_event', self.on_enter_zij_fig) 
        cursur_leave_arai=self.canvas2.mpl_connect('axes_leave_event', self.on_leave_zij_fig)

    def on_leave_zij_fig (self,event):
        self.canvas2.mpl_disconnect(self.cid3)
        self.canvas2.mpl_disconnect(self.cid4)
        self.canvas2.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
        self.curser_in_zij_figure=False
                
    def on_enter_zij_fig(self,event):
        self.curser_in_zij_figure=True
        self.canvas2.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))
        cid3=self.canvas2.mpl_connect('button_press_event', self.onclick_z_1)
        cid4=self.canvas2.mpl_connect('button_release_event', self.onclick_z_2)

    def onclick_z_1(self,event):
        if self.curser_in_zij_figure:
            self.tmp3_x=event.xdata
            self.tmp3_y=event.ydata
        
    def onclick_z_2(self,event):
        self.canvas2.mpl_connect('axes_leave_event', self.on_leave_arai_fig)
        if self.curser_in_zij_figure:
            self.tmp4_x=event.xdata
            self.tmp4_y=event.ydata
            if self.tmp3_x < self.tmp4_x and self.tmp3_y > self.tmp4_y:
                self.zijplot.set_xlim(xmin=self.tmp3_x,xmax=self.tmp4_x)
                self.zijplot.set_ylim(ymin=self.tmp4_y,ymax=self.tmp3_y)
            else:
                self.zijplot.set_xlim(xmin=self.zij_xlim_initial[0],xmax=self.zij_xlim_initial[1])
                self.zijplot.set_ylim(ymin=self.zij_ylim_initial[0],ymax=self.zij_ylim_initial[1])
            self.canvas2.draw()
        else:
            return

    def arrow_keys(self):
        self.panel.Bind(wx.EVT_CHAR, self.onCharEvent)

    def onCharEvent(self, event):
        keycode = event.GetKeyCode()
        controlDown = event.CmdDown()
        altDown = event.AltDown()
        shiftDown = event.ShiftDown()
 
        if keycode == wx.WXK_RIGHT or keycode == wx.WXK_NUMPAD_RIGHT or keycode == wx.WXK_WINDOWS_RIGHT:
            #print "you pressed the right!"
            self.on_next_button(None)
        elif keycode == wx.WXK_LEFT or keycode == wx.WXK_NUMPAD_LEFT or keycode == wx.WXK_WINDOWS_LEFT:
            #print "you pressed the right!"
            self.on_prev_button(None)
        event.Skip()
 
        
        
#===========================================================
# Update GUI with new interpretation
#===========================================================

    def check_specimen_critera(self):
        '''
        check if specimen pass acceptance criteria
        '''
        pass
        
        
    def update_GUI_with_new_interpretation(self):
       
        #-------------------------------------------------
        # Updtae GUI
        #-------------------------------------------------
        s=self.s

        # continue only if temperature bouds were asigned

        if "measurement_step_min" not in self.pars.keys() or "measurement_step_max" not in self.pars.keys():
            return(self.pars)
        if self.Data[self.s]['T_or_MW'] != "MW":
            self.tmin_box.SetValue("%.0f"%(float(self.pars['measurement_step_min'])-273.))
            self.tmax_box.SetValue("%.0f"%(float(self.pars['measurement_step_max'])-273.))
        else:
            self.tmin_box.SetValue("%.0f"%(float(self.pars['measurement_step_min'])))
            self.tmax_box.SetValue("%.0f"%(float(self.pars['measurement_step_max'])))
            
        
        # First,re-draw the figures
        self.draw_figure(s)

        # now draw the interpretation
        self.draw_interpretation()
        
        
        # declination/inclination
        self.declination_window.SetValue("%.1f"%(self.pars['specimen_dec']))
        self.inclination_window.SetValue("%.1f"%(self.pars['specimen_inc']))


         
        # PI statsistics
        flag_Fail=False
        for short_stat in self.preferences['show_statistics_on_gui']:
            stat="specimen_"+short_stat
            # ignore unwanted statistics
            if stat=='specimen_scat':
                continue
            if type(self.acceptance_criteria[stat]['decimal_points'])!=float and type(self.acceptance_criteria[stat]['decimal_points'])!=int:
                continue
            if type(self.acceptance_criteria[stat]['value'])!=float and type(self.acceptance_criteria[stat]['value'])!=int:
                continue
                
            # get the value
            if self.acceptance_criteria[stat]['decimal_points']==-999:
                value='%.2e'%self.pars[stat]
            elif type(self.acceptance_criteria[stat]['decimal_points'])==float or type(self.acceptance_criteria[stat]['decimal_points'])==int:
                command="value='%%.%if'%%(float(self.pars[stat]))"%(int(self.acceptance_criteria[stat]['decimal_points']))
                exec command
            #elif  stat=='specimen_scat':
            #    value= str(self.acceptance_criteria[stat]['value'])  
            # write the value
            command= "self.%s_window.SetValue(value)"%stat.split('specimen_')[-1]
            exec command
            
            # set backgound color
            cutoff_value=self.acceptance_criteria[stat]['value']
            if cutoff_value==-999:
                command="self.%s_window.SetBackgroundColour(wx.NullColour)"%stat.split('specimen_')[-1]  # set text color 
            elif stat=="specimen_k" or stat=="specimen_k_prime":
                if abs(self.pars[stat])>cutoff_value:
                    command="self.%s_window.SetBackgroundColour(wx.RED)"%stat.split('specimen_')[-1]  # set text color
                    flag_Fail=True                
            elif self.acceptance_criteria[stat]['threshold_type']=='high' and self.pars[stat]>cutoff_value:
                command="self.%s_window.SetBackgroundColour(wx.RED)"%stat.split('specimen_')[-1]  # set text color
                flag_Fail=True
            elif self.acceptance_criteria[stat]['threshold_type']=='low' and self.pars[stat]<cutoff_value:
                command="self.%s_window.SetBackgroundColour(wx.RED)"%stat.split('specimen_')[-1]  # set text color
                flag_Fail=True
            else:
                command="self.%s_window.SetBackgroundColour(wx.GREEN)"%stat.split('specimen_')[-1]  # set text color
            exec command

        # specimen_scat                
        if 'scat' in     self.preferences['show_statistics_on_gui']:
            if self.acceptance_criteria['specimen_scat']['value'] in ['True','TRUE','1',1,True,'g']:
                if self.pars["specimen_scat"]=='Pass':
                    self.scat_window.SetValue("Pass")
                    self.scat_window.SetBackgroundColour(wx.GREEN) # set text color
                else:
                    self.scat_window.SetValue("Fail")
                    self.scat_window.SetBackgroundColour(wx.RED) # set text color
                                        
            else:        
                self.scat_window.SetValue("")
                self.scat_window.SetBackgroundColour(wx.NullColour) # set text color
                

        # Blab, Banc, correction factors

        self.Blab_window.SetValue("%.0f"%(float(self.Data[self.s]['pars']['lab_dc_field'])*1e6))
        
        self.Banc_window.SetValue("%.1f"%(self.pars['specimen_int_uT']))
        if flag_Fail:
          self.Banc_window.SetBackgroundColour(wx.RED)
        else:
          self.Banc_window.SetBackgroundColour(wx.GREEN)

        if "AniSpec" in self.Data[self.s]:
          self.Aniso_factor_window.SetValue("%.2f"%(self.pars['Anisotropy_correction_factor']))
          if self.pars["AC_WARNING"]!="" and\
              ("TRM" in self.pars["AC_WARNING"] and  self.pars["AC_anisotropy_type"]== "ATRM" and "alteration" in self.pars["AC_WARNING"]) :
                self.Aniso_factor_window.SetBackgroundColour(wx.RED)  
          elif self.pars["AC_WARNING"]!="" and\
             ( ("TRM" in self.pars["AC_WARNING"] and  self.pars["AC_anisotropy_type"]== "ATRM" and "F-test" in self.pars["AC_WARNING"] and "alteration" not in self.pars["AC_WARNING"] ) \
               or\
               ("ARM" in self.pars["AC_WARNING"] and  self.pars["AC_anisotropy_type"]== "AARM" and "F-test" in self.pars["AC_WARNING"])):              
                self.Aniso_factor_window.SetBackgroundColour('#FFFACD')  
          else:
            self.Aniso_factor_window.SetBackgroundColour(wx.GREEN)  

        else:
          self.Aniso_factor_window.SetValue("None")
          self.Aniso_factor_window.SetBackgroundColour(wx.NullColour)  

        
        
        if self.pars['NLT_specimen_correction_factor']!=-1:
          self.NLT_factor_window.SetValue("%.2f"%(self.pars['NLT_specimen_correction_factor']))
        else:
          self.NLT_factor_window.SetValue("None")

        if self.pars['specimen_int_corr_cooling_rate']!=-1 and self.pars['specimen_int_corr_cooling_rate']!=-999: 
          self.CR_factor_window.SetValue("%.2f"%(self.pars['specimen_int_corr_cooling_rate']))
          if 'CR_flag' in self.pars.keys() and self.pars['CR_flag']=="calculated":
            self.CR_factor_window.SetBackgroundColour(wx.GREEN)
          elif  'CR_WARNING' in self.pars.keys() and 'inferred' in self.pars['CR_WARNING']:
            self.CR_factor_window.SetBackgroundColour('#FFFACD')  
          else:
            self.CR_factor_window.SetBackgroundColour(wx.NullColour)  
              
        else:
          self.CR_factor_window.SetValue("None")
          self.CR_factor_window.SetBackgroundColour(wx.NullColour)  

        # sample
        self.write_sample_box()

        


                


#===========================================================
# calculate PI statistics
#===========================================================



    def get_new_T_PI_parameters(self,event):
        
        """
        calcualte statisics when temperatures are selected
        """
    
        #remember the last saved interpretation
        if "saved" in self.pars.keys():
            if self.pars['saved']:
                self.last_saved_pars={}
                for key in self.pars.keys():
                    self.last_saved_pars[key]=self.pars[key]
        self.pars['saved']=False
        t1=self.tmin_box.GetStringSelection()
        t2=self.tmax_box.GetStringSelection()

        if (t1 == "" or t2==""):
          return()
        if float(t2) < float(t1)  :
          return()


        index_1=self.T_list.index(t1)
        index_2=self.T_list.index(t2)
        
        #if (index_2-index_1)+1 >= self.acceptance_criteria['specimen_int_n']:
        if (index_2-index_1)+1 >= 3:
            if self.Data[self.s]['T_or_MW']!="MW":
                self.pars=thellier_gui_lib.get_PI_parameters(self.Data,self.acceptance_criteria, self.preferences,self.s,float(t1)+273.,float(t2)+273.,self.GUI_log,THERMAL,MICROWAVE)
                self.Data[self.s]['pars'] = self.pars
            else:
                self.pars=thellier_gui_lib.get_PI_parameters(self.Data,self.acceptance_criteria, self.preferences,self.s,float(t1),float(t2),self.GUI_log,THERMAL,MICROWAVE)
                self.Data[self.s]['pars'] = self.pars
            self.update_GUI_with_new_interpretation()

            
#    def get_PI_parameters(self,s,tmin,tmax):
#        #print 'calling get_PI_parameters'
#        #print 's: {}, tmin: {}, tmax: {}'.format(s, tmin, tmax)
#
#        
#        #pars=self.Data[s]['pars']
#        datablock = self.Data[s]['datablock']
#        pars=copy.deepcopy(self.Data[s]['pars']) # assignments to pars are assiging to self.Data[s]['pars']
#        # get MagIC mothod codes:
#
#        #pars['magic_method_codes']="LP-PI-TRM" # thellier Method
#        import SPD
#        import SPD.spd as spd
#        Pint_pars = spd.PintPars(self.Data, str(s), tmin, tmax, 'magic', self.preferences['show_statistics_on_gui'])
#        Pint_pars.reqd_stats() # calculate only statistics indicated in self.preferences
#        if not Pint_pars.pars:
#            print "Could not get any parameters for {}".format(Pint_pars)
#            return 0
#        #Pint_pars.calculate_all_statistics() # calculate every statistic available
#        #print "-D- Debag"
#        #print Pint_pars.keys()
#        pars.update(Pint_pars.pars) # 
#
#        t_Arai=self.Data[s]['t_Arai']
#        x_Arai=self.Data[s]['x_Arai']
#        y_Arai=self.Data[s]['y_Arai']
#        x_tail_check=self.Data[s]['x_tail_check']
#        y_tail_check=self.Data[s]['y_tail_check']
#
#        zijdblock=self.Data[s]['zijdblock']        
#        z_temperatures=self.Data[s]['z_temp']
#
#        #print tmin,tmax,z_temperatures
#        # check tmin
#        if tmin not in t_Arai or tmin not in z_temperatures:
#            return(pars)
#        
#        # check tmax
#        if tmax not in t_Arai or tmin not in z_temperatures:
#            return(pars)
#
#        start=t_Arai.index(tmin)
#        end=t_Arai.index(tmax)
#
#        zstart=z_temperatures.index(tmin)
#        zend=z_temperatures.index(tmax)
#
#        zdata_segment=self.Data[s]['zdata'][zstart:zend+1]
#
#
#        # replacing PCA for zdata and for ptrms here
#       
#
### removed a bunch of Ron's commented out old code        
#
##lj
#        #-------------------------------------------------
#        # York regresssion (York, 1967) following Coe (1978)
#        # calculate f,fvds,
#        # modified from pmag.py
#        #-------------------------------------------------               
#
#        x_Arai_segment= x_Arai[start:end+1]
#        y_Arai_segment= y_Arai[start:end+1]
#        # replace thellier_gui code for york regression here
#
#        pars["specimen_int"]=-1*pars['lab_dc_field']*pars["specimen_b"]
#
#
#        # replace thellier_gui code for ptrm checks, DRAT etc. here
#        # also tail checks and SCAT
#
#
#
#        # Ron removed this
#        #-------------------------------------------------  
#        # Check if specimen pass Acceptance criteria
#        #-------------------------------------------------  
#
#        #pars['specimen_fail_criteria']=[]
#        #for key in self.high_threshold_velue_list:
#        #    if key in ['specimen_gmax','specimen_b_beta']:
#        #        value=round(pars[key],5)
#        #    elif key in ['specimen_dang','specimen_int_mad']:
#        #        value=round(pars[key],5)
#        #    else:
#        #        value=pars[key]
#        #        
#        #    if pars[key]>float(self.acceptance_criteria[key]):
#        #        pars['specimen_fail_criteria'].append(key)
#        #for key in self.low_threshold_velue_list:
#        #    if key in ['specimen_f','specimen_fvds','specimen_frac','specimen_g','specimen_q']:
#        #        value=round(pars[key],5)
#        #    else: 
#        #        value=pars[key]
#        #    if pars[key] < float(self.acceptance_criteria[key]):
#        #        pars['specimen_fail_criteria'].append(key)
#        #if 'specimen_scat' in pars.keys():
#        #    if pars["specimen_scat"]=="Fail":
#        #        pars['specimen_fail_criteria'].append('specimen_scat')
#        #if 'specimen_mad_scat' in pars.keys():
#        #    if pars["specimen_mad_scat"]=="Fail":
#        #        pars['specimen_fail_criteria'].append('specimen_mad_scat')
#
#
#        #-------------------------------------------------                     
#        # Add missing parts of code from old get_PI
#        #-------------------------------------------------                     
#
#        if MICROWAVE==True:
#            LP_code="LP-PI-M"
#        else:
#            LP_code="LP-PI-TRM"
#                   
#            
#        count_IZ= self.Data[s]['steps_Arai'].count('IZ')
#        count_ZI= self.Data[s]['steps_Arai'].count('ZI')
#        if count_IZ >1 and count_ZI >1:
#            pars['magic_method_codes']=LP_code+":"+"LP-PI-BT-IZZI"
#        elif count_IZ <1 and count_ZI >1:
#            pars['magic_method_codes']=LP_code+":"+"LP-PI-ZI"
#        elif count_IZ >1 and count_ZI <1:
#            pars['magic_method_codes']=LP_code+":"+"LP-PI-IZ"            
#        else:
#            pars['magic_method_codes']=LP_code
#
#        if 'ptrm_checks_temperatures' in self.Data[s].keys() and len(self.Data[s]['ptrm_checks_temperatures'])>0:
#            if MICROWAVE==True:
#                pars['magic_method_codes']+=":LP-PI-ALT-PMRM"
#            else:
#                pars['magic_method_codes']+=":LP-PI-ALT-PTRM"
#                
#        if 'tail_check_temperatures' in self.Data[s].keys() and len(self.Data[s]['tail_check_temperatures'])>0:
#            pars['magic_method_codes']+=":LP-PI-BT-MD"
#
#        if 'additivity_check_temperatures' in self.Data[s].keys() and len(self.Data[s]['additivity_check_temperatures'])>0:
#            pars['magic_method_codes']+=":LP-PI-BT"
#                        
#        #-------------------------------------------------            
#        # Calculate anistropy correction factor
#        #-------------------------------------------------            
#
#        if "AniSpec" in self.Data[s].keys():
#           pars["AC_WARNING"]=""
#           # if both aarm and atrm tensor axist, try first the aarm. if it fails use the atrm.
#           if 'AARM' in self.Data[s]["AniSpec"].keys() and 'ATRM' in self.Data[s]["AniSpec"].keys():
#               TYPES=['AARM','ATRM']
#           else:
#               TYPES=self.Data[s]["AniSpec"].keys()
#           for TYPE in TYPES:
#               red_flag=False
#               S_matrix=zeros((3,3),'f')
#               S_matrix[0,0]=self.Data[s]['AniSpec'][TYPE]['anisotropy_s1']
#               S_matrix[1,1]=self.Data[s]['AniSpec'][TYPE]['anisotropy_s2']
#               S_matrix[2,2]=self.Data[s]['AniSpec'][TYPE]['anisotropy_s3']
#               S_matrix[0,1]=self.Data[s]['AniSpec'][TYPE]['anisotropy_s4']
#               S_matrix[1,0]=self.Data[s]['AniSpec'][TYPE]['anisotropy_s4']
#               S_matrix[1,2]=self.Data[s]['AniSpec'][TYPE]['anisotropy_s5']
#               S_matrix[2,1]=self.Data[s]['AniSpec'][TYPE]['anisotropy_s5']
#               S_matrix[0,2]=self.Data[s]['AniSpec'][TYPE]['anisotropy_s6']
#               S_matrix[2,0]=self.Data[s]['AniSpec'][TYPE]['anisotropy_s6']
#
#               #self.Data[s]['AniSpec']['anisotropy_type']=self.Data[s]['AniSpec']['anisotropy_type']
#               self.Data[s]['AniSpec'][TYPE]['anisotropy_n']=int(float(self.Data[s]['AniSpec'][TYPE]['anisotropy_n']))
#
#               this_specimen_f_type=self.Data[s]['AniSpec'][TYPE]['anisotropy_type']+"_"+"%i"%(int(self.Data[s]['AniSpec'][TYPE]['anisotropy_n']))
#               
#               Ftest_crit={} 
#               Ftest_crit['ATRM_6']=  3.1059
#               Ftest_crit['AARM_6']=  3.1059
#               Ftest_crit['AARM_9']= 2.6848
#               Ftest_crit['AARM_15']= 2.4558
#
#               # threshold value for Ftest:
#               
#               if 'AniSpec' in self.Data[s].keys() and TYPE in self.Data[s]['AniSpec'].keys()\
#                  and 'anisotropy_sigma' in  self.Data[s]['AniSpec'][TYPE].keys() \
#                  and self.Data[s]['AniSpec'][TYPE]['anisotropy_sigma']!="":
#                  # Calculate Ftest. If Ftest exceeds threshold value: set anistropy tensor to identity matrix
#                   sigma=float(self.Data[s]['AniSpec'][TYPE]['anisotropy_sigma'])             
#                   nf = 3*int(self.Data[s]['AniSpec'][TYPE]['anisotropy_n'])-6
#                   F=thellier_gui_lib.calculate_ftest(S_matrix,sigma,nf)
#                   #print s,"F",F
#                   self.Data[s]['AniSpec'][TYPE]['ftest']=F
#                   #print "s,sigma,nf,F,Ftest_crit[this_specimen_f_type]"
#                   #print s,sigma,nf,F,Ftest_crit[this_specimen_f_type]
#                   if self.acceptance_criteria['anisotropy_ftest_flag']['value'] in ['g','1',1,True,'TRUE','True'] :
#                       Ftest_threshold=Ftest_crit[this_specimen_f_type]
#                       if self.Data[s]['AniSpec'][TYPE]['ftest'] < Ftest_crit[this_specimen_f_type]:
#                           S_matrix=identity(3,'f')
#                           pars["AC_WARNING"]=pars["AC_WARNING"]+"%s tensor fails F-test; "%(TYPE)
#                           red_flag=True
#                           
#               else:
#                   self.Data[s]['AniSpec'][TYPE]['anisotropy_sigma']=""
#                   self.Data[s]['AniSpec'][TYPE]['ftest']=99999
#     
#                
#               if 'anisotropy_alt' in self.Data[s]['AniSpec'][TYPE].keys() and self.Data[s]['AniSpec'][TYPE]['anisotropy_alt']!="":
#                   if self.acceptance_criteria['anisotropy_alt']['value'] != -999 and \
#                   (float(self.Data[s]['AniSpec'][TYPE]['anisotropy_alt']) > float(self.acceptance_criteria['anisotropy_alt']['value'])):
#                       S_matrix=identity(3,'f')
#                       pars["AC_WARNING"]=pars["AC_WARNING"]+"%s tensor fails alteration check: %.1f > %.1f; "%(TYPE,float(self.Data[s]['AniSpec'][TYPE]['anisotropy_alt']),float(self.acceptance_criteria['anisotropy_alt']['value']))
#                       red_flag=True
#               else:
#                   self.Data[s]['AniSpec'][TYPE]['anisotropy_alt']=""
#
#               self.Data[s]['AniSpec'][TYPE]['S_matrix']=S_matrix 
#           #--------------------------  
#           # if AARM passes all, use the AARM.
#           # if ATRM fail alteration use the AARM
#           # if both fail F-test: use AARM
#           if len(TYPES)>1:
#               if "ATRM tensor fails alteration check" in pars["AC_WARNING"]:
#                   TYPE='AARM'
#               elif "ATRM tensor fails F-test" in pars["AC_WARNING"]:
#                   TYPE='AARM'
#               else: 
#                   TYPE=='AARM'
#           S_matrix= self.Data[s]['AniSpec'][TYPE]['S_matrix']
#           #---------------------------        
#           TRM_anc_unit=array(pars['specimen_PCA_v1'])/scipy.sqrt(pars['specimen_PCA_v1'][0]**2+pars['specimen_PCA_v1'][1]**2+pars['specimen_PCA_v1'][2]**2)
#           B_lab_unit=pmag.dir2cart([ self.Data[s]['Thellier_dc_field_phi'], self.Data[s]['Thellier_dc_field_theta'],1])
#           #B_lab_unit=scipy.array([0,0,-1])
#           Anisotropy_correction_factor=linalg.norm(dot(inv(S_matrix),TRM_anc_unit.transpose()))*norm(dot(S_matrix,B_lab_unit))
#           pars["Anisotropy_correction_factor"]=Anisotropy_correction_factor
#           pars["AC_specimen_int"]= pars["Anisotropy_correction_factor"] * float(pars["specimen_int"])
#           
#           pars["AC_anisotropy_type"]=self.Data[s]['AniSpec'][TYPE]["anisotropy_type"]
#           pars["specimen_int_uT"]=float(pars["AC_specimen_int"])*1e6
#           if TYPE=='AARM':
#               if ":LP-AN-ARM" not in pars['magic_method_codes']:
#                  pars['magic_method_codes']+=":LP-AN-ARM:AE-H:DA-AC-AARM"
#                  pars['specimen_correction']='c'
#                  pars['specimen_int_corr_anisotropy']=Anisotropy_correction_factor
#           if TYPE=='ATRM':
#               if ":LP-AN-TRM" not in pars['magic_method_codes']:
#                  pars['magic_method_codes']+=":LP-AN-TRM:AE-H:DA-AC-ATRM"
#                  pars['specimen_correction']='c' 
#                  pars['specimen_int_corr_anisotropy']=Anisotropy_correction_factor
#
# 
#        else:
#           pars["Anisotropy_correction_factor"]=1.0
#           pars["specimen_int_uT"]=float(pars["specimen_int"])*1e6
#           pars["AC_WARNING"]="No anistropy correction"
#           pars['specimen_correction']='u' 
#
#        pars["specimen_int_corr_anisotropy"]=pars["Anisotropy_correction_factor"]   
#        #-------------------------------------------------                    
#        # NLT and anisotropy correction together in one equation
#        # See Shaar et al (2010), Equation (3)
#        #-------------------------------------------------
#
#        if 'NLT_parameters' in self.Data[s].keys():
#
#           alpha=self.Data[s]['NLT_parameters']['tanh_parameters'][0][0]
#           beta=self.Data[s]['NLT_parameters']['tanh_parameters'][0][1]
#           b=float(pars["specimen_b"])
#           Fa=pars["Anisotropy_correction_factor"]
#
#           if ((abs(b)*Fa)/alpha) <1.0:
#               Banc_NLT=math.atanh( ((abs(b)*Fa)/alpha) ) / beta
#               pars["NLTC_specimen_int"]=Banc_NLT
#               pars["specimen_int_uT"]=Banc_NLT*1e6
#
#               if "AC_specimen_int" in pars.keys():
#                   pars["NLT_specimen_correction_factor"]=Banc_NLT/float(pars["AC_specimen_int"])
#               else:                       
#                   pars["NLT_specimen_correction_factor"]=Banc_NLT/float(pars["specimen_int"])
#               if ":LP-TRM" not in pars['magic_method_codes']:
#                  pars['magic_method_codes']+=":LP-TRM:DA-NL"
#               pars['specimen_correction']='c' 
#
#           else:
#               self.GUI_log.write ("-W- WARNING: problematic NLT mesurements for specimens %s. Cant do NLT calculation. check data\n"%s)
#               pars["NLT_specimen_correction_factor"]=-1
#        else:
#           pars["NLT_specimen_correction_factor"]=-1
#
#        #-------------------------------------------------                    
#        # Calculate the final result with cooling rate correction
#        #-------------------------------------------------
#
#        pars["specimen_int_corr_cooling_rate"]=-999
#        if 'cooling_rate_data' in self.Data[s].keys():
#            if 'CR_correction_factor' in self.Data[s]['cooling_rate_data'].keys():
#                if self.Data[s]['cooling_rate_data']['CR_correction_factor'] != -1 and self.Data[s]['cooling_rate_data']['CR_correction_factor'] !=-999:
#                    pars["specimen_int_corr_cooling_rate"]=self.Data[s]['cooling_rate_data']['CR_correction_factor']
#                    pars['specimen_correction']='c'
#                    pars["specimen_int_uT"]=pars["specimen_int_uT"]*pars["specimen_int_corr_cooling_rate"]
#                    if ":DA-CR" not in pars['magic_method_codes']:
#                      pars['magic_method_codes']+=":DA-CR"
#                    if   'CR_correction_factor_flag' in self.Data[s]['cooling_rate_data'].keys():
#                        if self.Data[s]['cooling_rate_data']['CR_correction_factor_flag']=="calculated":
#                            pars['CR_flag']="calculated"
#                        else:
#                            pars['CR_flag']=""
#                    if 'CR_correction_factor_flag' in self.Data[s]['cooling_rate_data'].keys() \
#                       and self.Data[s]['cooling_rate_data']['CR_correction_factor_flag']!="calculated":
#                        pars["CR_WARNING"]="inferred cooling rate correction"
#                    
#                
#        else:
#            pars["CR_WARNING"]="no cooling rate correction"
#            
#
#
#
#        def combine_dictionaries(d1, d2):
#            """
#            combines dict1 and dict2 into a new dict.  
#            if dict1 and dict2 share a key, the value from dict1 is used
#            """
#            for key, value in d2.iteritems():
#                if key not in d1.keys():
#                    d1[key] = value
#            return d1
#
#        
#        self.Data[s]['pars'] = pars
#        #print pars.keys()
#
#        return(pars)
                
    #def check_specimen_PI_criteria(self,pars):
    #    '''
    #    # Check if specimen pass Acceptance criteria
    #    '''
    #    #if 'pars' not in self.Data[specimen].kes():
    #    #    return
    #        
    #    pars['specimen_fail_criteria']=[]
    #    for crit in self.acceptance_criteria.keys():
    #        if crit not in pars.keys():
    #            continue
    #        if self.acceptance_criteria[crit]['value']==-999:
    #            continue
    #        if self.acceptance_criteria[crit]['category']!='IE-SPEC':
    #            continue
    #        cutoff_value=self.acceptance_criteria[crit]['value']
    #        if crit=='specimen_scat':
    #            if pars["specimen_scat"] in ["Fail",'b',0,'0','FALSE',"False",False]:
    #                pars['specimen_fail_criteria'].append('specimen_scat')
    #        elif crit=='specimen_k' or crit=='specimen_k_prime':
    #            if abs(pars[crit])>cutoff_value:
    #                pars['specimen_fail_criteria'].append(crit)
    #        # high threshold value:
    #        elif self.acceptance_criteria[crit]['threshold_type']=="high":
    #            if pars[crit]>cutoff_value:
    #                pars['specimen_fail_criteria'].append(crit)
    #        elif self.acceptance_criteria[crit]['threshold_type']=="low":
    #            if pars[crit]<cutoff_value:
    #                pars['specimen_fail_criteria'].append(crit)
    #    return pars                                                                                     
                
    def  draw_interpretation(self):

        if "measurement_step_min" not in self.pars.keys() or "measurement_step_max" not in self.pars.keys():
            return()

        s=self.s
        pars=self.Data[s]['pars']        
        datablock = self.Data[s]['datablock']
        pars=self.Data[s]['pars']

        t_Arai=self.Data[s]['t_Arai']
        x_Arai=self.Data[s]['x_Arai']
        y_Arai=self.Data[s]['y_Arai']
        x_tail_check=self.Data[s]['x_tail_check']
        y_tail_check=self.Data[s]['y_tail_check']

        zijdblock=self.Data[s]['zijdblock']        
        z_temperatures=self.Data[s]['z_temp']



        start=t_Arai.index(self.pars["measurement_step_min"])
        end=t_Arai.index(self.pars["measurement_step_max"])
        
        x_Arai_segment= x_Arai[start:end+1]
        y_Arai_segment= y_Arai[start:end+1]

        self.araiplot.scatter([x_Arai_segment[0],x_Arai_segment[-1]],[y_Arai_segment[0],y_Arai_segment[-1]],marker='o',facecolor='g',edgecolor ='k',s=30)
        b=pars["specimen_b"]
        a=scipy.mean(y_Arai_segment) - b* scipy.mean(x_Arai_segment)
        xx=scipy.array([x_Arai_segment[0],x_Arai_segment[-1]])
        yy=b*xx+a
        self.araiplot.plot(xx,yy,'g-',lw=2,alpha=0.5)
        if self.acceptance_criteria['specimen_scat']['value'] in [True,"True","TRUE",'1','g']:
            if 'specimen_scat_bounding_line_low' in pars:
                if pars['specimen_scat_bounding_line_low'] != 0: # prevents error if there are no SCAT lines available
                    yy1=xx*pars['specimen_scat_bounding_line_low'][1]+pars['specimen_scat_bounding_line_low'][0]
                    yy2=xx*pars['specimen_scat_bounding_line_high'][1]+pars['specimen_scat_bounding_line_high'][0]
                    self.araiplot.plot(xx,yy1,'--',lw=0.5,alpha=0.5)
                    self.araiplot.plot(xx,yy2,'--',lw=0.5,alpha=0.5)

        self.araiplot.set_xlim(xmin=0)
        self.araiplot.set_ylim(ymin=0)
        
        pylab.draw()
        self.canvas1.draw()

        # plot best fit direction on Equal Area plot
        CART=scipy.array(pars["specimen_PCA_v1"])/scipy.sqrt(sum(scipy.array(pars["specimen_PCA_v1"])**2))
        x=CART[0]
        y=CART[1]
        z=abs(CART[2])
        R=scipy.array(scipy.sqrt(1-z)/scipy.sqrt(x**2+y**2))
        eqarea_x=y*R
        eqarea_y=x*R

        if self.preferences['show_CR_plot'] ==False or 'crblock' not in self.Data[self.s].keys():
            if z>0:
              FC='green';EC='0.1'
            else:
              FC='yellow';EC='green'
            self.eqplot.scatter([eqarea_x],[eqarea_y],marker='o',edgecolor=EC, facecolor=FC,s=30,lw=1)

            self.canvas3.draw()

        # plot Zijderveld

        ymin, ymax = self.zijplot.get_ylim()
        xmin, xmax = self.zijplot.get_xlim()
        
        #rotated zijderveld
        NRM_dir=pmag.cart2dir(self.Data[self.s]['zdata'][0])         
        NRM_dec=NRM_dir[0]

        #PCA direction
        PCA_dir_rotated=pmag.cart2dir(CART)         
        PCA_dir_rotated[0]=PCA_dir_rotated[0]-NRM_dec      
        PCA_CART_rotated=pmag.dir2cart(PCA_dir_rotated)

        tmin_index=self.Data[self.s]['z_temp'].index(self.pars["measurement_step_min"])
        tmax_index=self.Data[self.s]['z_temp'].index(self.pars["measurement_step_max"])
        
        PCA_dir_rotated=pmag.cart2dir(CART)         
        PCA_dir_rotated[0]=PCA_dir_rotated[0]-NRM_dec      
        PCA_CART_rotated=pmag.dir2cart(PCA_dir_rotated)
        
        slop_xy_PCA=-1*PCA_CART_rotated[1]/PCA_CART_rotated[0]
        slop_xz_PCA=-1*PCA_CART_rotated[2]/PCA_CART_rotated[0]

        # Center of mass rotated
        
        CM_x=scipy.mean(self.CART_rot[:,0][tmin_index:tmax_index+1])
        CM_y=scipy.mean(self.CART_rot[:,1][tmin_index:tmax_index+1])
        CM_z=scipy.mean(self.CART_rot[:,2][tmin_index:tmax_index+1])

        # intercpet from the center of mass
        intercept_xy_PCA=-1*CM_y - slop_xy_PCA*CM_x
        intercept_xz_PCA=-1*CM_z - slop_xz_PCA*CM_x

        xmin_zij, xmax_zij = pylab.xlim()
        xx=scipy.array([0,self.CART_rot[:,0][tmin_index]])
        yy=slop_xy_PCA*xx+intercept_xy_PCA
        self.zijplot.plot(xx,yy,'-',color='g',lw=1.5,alpha=0.5)
        zz=slop_xz_PCA*xx+intercept_xz_PCA
        self.zijplot.plot(xx,zz,'-',color='g',lw=1.5,alpha=0.5)

    
        self.zijplot.scatter([self.CART_rot[:,0][tmin_index]],[-1* self.CART_rot[:,1][tmin_index]],marker='o',s=40,facecolor='g',edgecolor ='k',zorder=100)
        self.zijplot.scatter([self.CART_rot[:,0][tmax_index]],[-1* self.CART_rot[:,1][tmax_index]],marker='o',s=40,facecolor='g',edgecolor ='k',zorder=100)
        self.zijplot.scatter([self.CART_rot[:,0][tmin_index]],[-1* self.CART_rot[:,2][tmin_index]],marker='s',s=50,facecolor='g',edgecolor ='k',zorder=100)
        self.zijplot.scatter([self.CART_rot[:,0][tmax_index]],[-1* self.CART_rot[:,2][tmax_index]],marker='s',s=50,facecolor='g',edgecolor ='k',zorder=100)


##        # draw MAD-box
##        self.acceptance_criteria['specimen_mad_scat']=True
##        if 'specimen_mad_scat' in self.acceptance_criteria.keys() and 'specimen_int_mad' in self.acceptance_criteria.keys() :
##            if self.acceptance_criteria['specimen_mad_scat']==True or self.acceptance_criteria['specimen_mad_scat'] in [1,"True","TRUE",'1']:
##
##                # center of mass 
##                CM=scipy.array([CM_x,CM_y,CM_z])
##
##                # threshold value for the distance of the point from a line:
##                # this is depends of MAD
##                # if MAD= tan-1 [ sigma_perpendicular / sigma_max ]
##                # then:
##                # sigma_perpendicular_threshold=tan(MAD_threshold)*sigma_max
##                sigma_perpendicular_threshold=abs(tan(radians(self.acceptance_criteria['specimen_int_mad'])) *  self.pars["specimen_PCA_sigma_max"] )
##                mad_box_xy_x1,mad_box_xy_x2=[],[]                
##                mad_box_xy_y1,mad_box_xy_y2=[],[]                
##                mad_box_xz_x1,mad_box_xz_x2=[],[]                
##                mad_box_xz_y1,mad_box_xz_y2=[],[]                
##
##                for i in range(len(xx)):
##                    #xy_x_plus=scipy.array(xx[i],yy[i])
##                                        
##                    # X-Y projectoin
##                    x_y_projection=cross(scipy.array(PCA_CART_rotated),scipy.array([0,0,1]))
##                    x_y_projection=x_y_projection/scipy.sqrt(sum(x_y_projection**2))
##                    new_vector1=scipy.array([xx[i],yy[i]])+2*sigma_perpendicular_threshold*scipy.array([x_y_projection[0],x_y_projection[1]])
##                    new_vector2=scipy.array([xx[i],yy[i]])-2*sigma_perpendicular_threshold*scipy.array([x_y_projection[0],x_y_projection[1]])
##                    mad_box_xy_x1.append(new_vector1[0])
##                    mad_box_xy_y1.append(new_vector1[1])
##                    mad_box_xy_x2.append(new_vector2[0])
##                    mad_box_xy_y2.append(new_vector2[1])
##                                                            
##
##                    # X-Z projectoin
##                    x_z_projection=cross(scipy.array(PCA_CARTated),scipy.array([0,1,0]))
##                    x_z_projection=x_z_projection/scipy.sqrt(sum(x_z_projection**2))
##                    new_vector1=scipy.array([xx[i],zz[i]])+2*sigma_perpendicular_threshold*scipy.array([x_z_projection[0],x_z_projection[2]])
##                    new_vector2=scipy.array([xx[i],zz[i]])-2*sigma_perpendicular_threshold*scipy.array([x_z_projection[0],x_z_projection[2]])
##                    mad_box_xz_x1.append(new_vector1[0])
##                    mad_box_xz_y1.append(new_vector1[1])
##                    mad_box_xz_x2.append(new_vector2[0])
##                    mad_box_xz_y2.append(new_vector2[1])
##
##
##                #print mad_box_x1,mad_box_y1
##                self.zijplot.plot(mad_box_xy_x1,mad_box_xy_y1,ls="--",c='k',lw=0.5)
##                self.zijplot.plot(mad_box_xy_x2,mad_box_xy_y2,ls="--",c='k',lw=0.5)
##                self.zijplot.plot(mad_box_xz_x1,mad_box_xz_y1,ls="--",c='k',lw=0.5)
##                self.zijplot.plot(mad_box_xz_x2,mad_box_xz_y2,ls="--",c='k',lw=0.5)




        self.zijplot.set_xlim(xmin, xmax)
        self.zijplot.set_ylim(ymin, ymax)
  
        self.canvas2.draw()

        # NLT plot
        if self.preferences['show_NLT_plot'] ==True and 'NLT_parameters' in self.Data[self.s].keys():
           alpha=self.Data[self.s]['NLT_parameters']['tanh_parameters'][0][0]
           beta=self.Data[self.s]['NLT_parameters']['tanh_parameters'][0][1]
           #labfiled=self.Data[self.s]['lab_dc_field']
           Banc=self.pars["specimen_int_uT"]
           self.mplot.scatter([Banc],[alpha*(scipy.tanh(beta*Banc*1e-6))],marker='o',s=30,facecolor='g',edgecolor ='k')

        self.canvas5.draw()
        pylab.draw()

        #------
        # Drow sample mean
        #------

        self.draw_sample_mean()

        
    def draw_sample_mean(self):

        self.sampleplot.clear()
        specimens_id=[]
        specimens_B=[]
        sample=self.Data_hierarchy['specimens'][self.s]
        site=thellier_gui_lib.get_site_from_hierarchy(sample,self.Data_hierarchy)
        
        # average by sample
        #print self.average_by_sample_or_site
        if self.acceptance_criteria['average_by_sample_or_site']['value']=='sample':                         
            if sample in self.Data_samples.keys():
                specimens_list=self.Data_samples[sample].keys()
                if self.s not in specimens_list and 'specimen_int_uT' in self.pars.keys():
                    specimens_list.append(self.s)
                specimens_list.sort()                    
                for spec in specimens_list:
                    if spec==self.s and 'specimen_int_uT' in self.pars.keys():
                        specimens_B.append(self.pars['specimen_int_uT'])
                        specimens_id.append(spec)
                    else:
                        if spec in self.Data_samples[sample].keys() and 'B' in self.Data_samples[sample][spec].keys():
                            specimens_B.append(self.Data_samples[sample][spec]['B'])
                            specimens_id.append(spec)
            else:
                if 'specimen_int_uT' in self.pars.keys():
                    specimens_id=[self.s]
                    specimens_B=[self.pars['specimen_int_uT']]
        # average by site
        else:
            if site in self.Data_sites.keys():
                
                specimens_list=self.Data_sites[site].keys()
                if self.s not in specimens_list and 'specimen_int_uT' in self.pars.keys():
                    specimens_list.append(self.s)
                specimens_list.sort()                    
                for spec in specimens_list:
                    if spec==self.s and 'specimen_int_uT' in self.pars.keys():
                        specimens_B.append(self.pars['specimen_int_uT'])
                        specimens_id.append(spec)
                    else:
                        if spec in self.Data_sites[site].keys() and 'B' in self.Data_sites[site][spec].keys():
                            specimens_B.append(self.Data_sites[site][spec]['B'])
                            specimens_id.append(spec)
            else:
                if 'specimen_int_uT' in self.pars.keys():
                    specimens_id=[self.s]
                    specimens_B=[self.pars['specimen_int_uT']]
            
        if len(specimens_id)>=1:
            self.sampleplot.scatter(scipy.arange(len(specimens_id)),specimens_B ,marker='s',edgecolor='0.2', facecolor='b',s=40*self.GUI_RESOLUTION,lw=1)
            self.sampleplot.axhline(y=scipy.mean(specimens_B)+scipy.std(specimens_B,ddof=1),color='0.2',ls="--",lw=0.75)
            self.sampleplot.axhline(y=scipy.mean(specimens_B)-scipy.std(specimens_B,ddof=1),color='0.2',ls="--",lw=0.75)
            self.sampleplot.axhline(y=scipy.mean(specimens_B),color='0.2',ls="-",lw=0.75,alpha=0.5)
            
            if self.s in specimens_id:
                self.sampleplot.scatter([specimens_id.index(self.s)],[specimens_B[specimens_id.index(self.s)]] ,marker='s',edgecolor='0.2', facecolor='g',s=40*self.GUI_RESOLUTION,lw=1)

            self.sampleplot.set_xticks(scipy.arange(len(specimens_id)))
            self.sampleplot.set_xlim(-0.5,len(specimens_id)-0.5)
            self.sampleplot.set_xticklabels(specimens_id,rotation=90,fontsize=8)
            #ymin,ymax=self.sampleplot.ylim()
            
            #if "sample_int_sigma" in self.acceptance_criteria.keys() and "sample_int_sigma_perc" in self.acceptance_criteria.keys():
            sigma_threshold_for_plot_1,sigma_threshold_for_plot_2=0,0                 
            #    sigma_threshold_for_plot=max(self.acceptance_criteria["sample_int_sigma"]*,0.01*self.acceptance_criteria["sample_int_sigma_perc"]*scipy.mean(specimens_B))
            if self.acceptance_criteria["sample_int_sigma"]["value"]!=-999 and type(self.acceptance_criteria["sample_int_sigma"]["value"])==float:
                sigma_threshold_for_plot_1=self.acceptance_criteria["sample_int_sigma"]["value"]*1e6               
            if self.acceptance_criteria["sample_int_sigma_perc"]["value"]!=-999 and type(self.acceptance_criteria["sample_int_sigma_perc"]["value"])==float:
                sigma_threshold_for_plot_2=scipy.mean(specimens_B)*0.01*self.acceptance_criteria["sample_int_sigma_perc"]['value']
            #sigma_threshold_for_plot 100000
            sigma_threshold_for_plot=max(sigma_threshold_for_plot_1,sigma_threshold_for_plot_2)
            if sigma_threshold_for_plot < 20 and sigma_threshold_for_plot!=0:
                self.sampleplot.axhline(y=scipy.mean(specimens_B)+sigma_threshold_for_plot,color='r',ls="--",lw=0.75)
                self.sampleplot.axhline(y=scipy.mean(specimens_B)-sigma_threshold_for_plot,color='r',ls="--",lw=0.75)
                y_axis_limit=max(sigma_threshold_for_plot,scipy.std(specimens_B,ddof=1),abs(max(specimens_B)-scipy.mean(specimens_B)),abs((min(specimens_B)-scipy.mean(specimens_B))))
            else:
                y_axis_limit=max(scipy.std(specimens_B,ddof=1),abs(max(specimens_B)-scipy.mean(specimens_B)),abs((min(specimens_B)-scipy.mean(specimens_B))))
                
            self.sampleplot.set_ylim(scipy.mean(specimens_B)-y_axis_limit-1,scipy.mean(specimens_B)+y_axis_limit+1)
            self.sampleplot.set_ylabel('uT',fontsize=8)
            try:
                self.sampleplot.tick_params(axis='both', which='major', labelsize=8)
            except:
                pass
            try:
                self.sampleplot.tick_params(axis='y', which='minor', labelsize=0)
            except:
                pass

        self.canvas4.draw()
        #start_time_5=time.time() 
        #runtime_sec5 = start_time_5 - start_time_4
        
    def on_pick(self, event):
        # The event received here is of the type
        # matplotlib.backend_bases.PickEvent
        #
        # It carries lots of information, of which we're using
        # only a small amount here.
        # 
        box_points = event.artist.get_bbox().get_points()
        msg = "You've clicked on a bar with coords:\n %s" % box_points
        
        dlg = wx.MessageDialog(
            self, 
            msg, 
            "Click!",
            wx.OK | wx.ICON_INFORMATION)

        dlg.ShowModal() 
        dlg.Destroy()        
    

    def add_thellier_gui_criteria(self):
        '''criteria used only in thellier gui
        these criteria are not written to pmag_criteria.txt
        '''
        category="thellier_gui"      
        for crit in ['sample_int_n_outlier_check','site_int_n_outlier_check']:
            self.acceptance_criteria[crit]={} 
            self.acceptance_criteria[crit]['category']=category
            self.acceptance_criteria[crit]['criterion_name']=crit
            self.acceptance_criteria[crit]['value']=-999
            self.acceptance_criteria[crit]['threshold_type']="low"
            self.acceptance_criteria[crit]['decimal_points']=0
            
        for crit in ['sample_int_interval_uT','sample_int_interval_perc',\
        'site_int_interval_uT','site_int_interval_perc',\
        'sample_int_BS_68_uT','sample_int_BS_95_uT','sample_int_BS_68_perc','sample_int_BS_95_perc','specimen_int_max_slope_diff']:
            self.acceptance_criteria[crit]={} 
            self.acceptance_criteria[crit]['category']=category
            self.acceptance_criteria[crit]['criterion_name']=crit
            self.acceptance_criteria[crit]['value']=-999
            self.acceptance_criteria[crit]['threshold_type']="high"
            if crit in ['specimen_int_max_slope_diff']:
                self.acceptance_criteria[crit]['decimal_points']=-999
            else:        
                self.acceptance_criteria[crit]['decimal_points']=1
            self.acceptance_criteria[crit]['comments']="thellier_gui_only"

        for crit in ['average_by_sample_or_site','interpreter_method']:
            self.acceptance_criteria[crit]={} 
            self.acceptance_criteria[crit]['category']=category
            self.acceptance_criteria[crit]['criterion_name']=crit
            if crit in ['average_by_sample_or_site']:
                self.acceptance_criteria[crit]['value']='sample'
            if crit in ['interpreter_method']:
                self.acceptance_criteria[crit]['value']='stdev_opt'
            self.acceptance_criteria[crit]['threshold_type']="flag"
            self.acceptance_criteria[crit]['decimal_points']=-999
       
        for crit in ['include_nrm']:
            self.acceptance_criteria[crit]={} 
            self.acceptance_criteria[crit]['category']=category
            self.acceptance_criteria[crit]['criterion_name']=crit
            self.acceptance_criteria[crit]['value']=True
            self.acceptance_criteria[crit]['threshold_type']="bool"
            self.acceptance_criteria[crit]['decimal_points']=-999
                    
        
        # define internal Thellier-GUI definitions:
        self.average_by_sample_or_site='sample'
        self.stdev_opt=True
        self.bs=False
        self.bs_par=False


#    def get_default_criteria(self):
#      #------------------------------------------------
#      # read criteria file
#      # Format is as pmag_criteria.txt
#      #------------------------------------------------
#
#
#      self.criteria_list=['specimen_int_n','specimen_int_ptrm_n','specimen_f','specimen_fvds','specimen_frac','specimen_gmax','specimen_b_beta',
#                     'specimen_dang','specimen_drats','specimen_int_mad','specimen_md','specimen_g','specimen_q']
#      self.high_threshold_velue_list=['specimen_gmax','specimen_b_beta','specimen_dang','specimen_drats','specimen_int_mad','specimen_md']
#      self.low_threshold_velue_list=['specimen_int_n','specimen_int_ptrm_n','specimen_f','specimen_fvds','specimen_frac','specimen_g','specimen_q']
#
#      acceptance_criteria_null={}
#      acceptance_criteria_default={}
#      #  make a list of default parameters
#
#      acceptance_criteria_default['specimen_int_n']=3
#      acceptance_criteria_default['specimen_int_ptrm_n']=2
#      acceptance_criteria_default['specimen_f']=0.
#      acceptance_criteria_default['specimen_fvds']=0.
#      acceptance_criteria_default['specimen_frac']=0.8
#      acceptance_criteria_default['specimen_gmax']=0.6
#      acceptance_criteria_default['specimen_b_beta']=0.1
#      acceptance_criteria_default['specimen_dang']=100000
#      acceptance_criteria_default['specimen_drats']=100000
#      acceptance_criteria_default['specimen_int_mad']=5
#      acceptance_criteria_default['specimen_md']=100000
#      acceptance_criteria_default['specimen_g']=0
#      acceptance_criteria_default['specimen_q']=0
#      acceptance_criteria_default['specimen_scat']=True
#
#      acceptance_criteria_default['sample_int_n']=3
#      acceptance_criteria_default['sample_int_n_outlier_check']=1000
#
#      # anistropy criteria
#      acceptance_criteria_default['anisotropy_alt']=10
#      acceptance_criteria_default['check_aniso_ftest']=True
#
#
#      # Sample mean calculation type 
#      acceptance_criteria_default['sample_int_stdev_opt']=True
#      acceptance_criteria_default['sample_int_bs']=False
#      acceptance_criteria_default['sample_int_bs_par']=False
#
#      # Averaging sample or site calculation type 
#
#      acceptance_criteria_default['average_by_sample_or_site']='sample'
#
#      # STDEV-OPT  
#      acceptance_criteria_default['sample_int_sigma_uT']=6
#      acceptance_criteria_default['sample_int_sigma_perc']=10
#      acceptance_criteria_default['sample_aniso_threshold_perc']=1000000
#      acceptance_criteria_default['sample_int_interval_uT']=10000
#      acceptance_criteria_default['sample_int_interval_perc']=10000
#
#      # BS  
#      acceptance_criteria_default['sample_int_BS_68_uT']=10000
#      acceptance_criteria_default['sample_int_BS_68_perc']=10000
#      acceptance_criteria_default['sample_int_BS_95_uT']=10000
#      acceptance_criteria_default['sample_int_BS_95_perc']=10000
#      acceptance_criteria_default['specimen_int_max_slope_diff']=10000
#
#      # NULL  
#      for key in ( acceptance_criteria_default.keys()):
#          acceptance_criteria_null[key]=acceptance_criteria_default[key]
#      acceptance_criteria_null['sample_int_stdev_opt']=False
#      acceptance_criteria_null['specimen_frac']=0
#      acceptance_criteria_null['specimen_gmax']=10000
#      acceptance_criteria_null['specimen_b_beta']=10000
#      acceptance_criteria_null['specimen_int_mad']=100000
#      acceptance_criteria_null['specimen_scat']=False
#      acceptance_criteria_null['specimen_int_ptrm_n']=0
#      acceptance_criteria_null['anisotropy_alt']=1e10
#      acceptance_criteria_null['check_aniso_ftest']=True
#      acceptance_criteria_default['sample_aniso_threshold_perc']=1000000
#
#      #acceptance_criteria_null['sample_int_sigma_uT']=0
#      #acceptance_criteria_null['sample_int_sigma_perc']=0
#      #acceptance_criteria_null['sample_int_n_outlier_check']=100000
#
#      
#      #print acceptance_criteria_default
#        
#      # A list of all acceptance criteria used by program
#      accept_specimen_keys=['specimen_int_n','specimen_int_ptrm_n','specimen_f','specimen_fvds','specimen_frac','specimen_gmax','specimen_b_beta','specimen_dang','specimen_drats','specimen_int_mad','specimen_md']
#      accept_sample_keys=['sample_int_n','sample_int_sigma_uT','sample_int_sigma_perc','sample_aniso_threshold_perc','sample_int_interval_uT','sample_int_interval_perc']
#      
#      #self.acceptance_criteria_null=acceptance_criteria_null
#      return(acceptance_criteria_default,acceptance_criteria_null)
#      #print acceptance_criteria_default
#      #print "yes"
#
      
    def get_data(self):
      

      def tan_h(x, a, b):
            return a*scipy.tanh(b*x)

      def cart2dir(cart): # OLD ONE
            """
            converts a direction to cartesian coordinates
            """
            Dir=[] # establish a list to put directions in
            rad=pi/180. # constant to convert degrees to radians
            R=scipy.sqrt(cart[0]**2+cart[1]**2+cart[2]**2) # calculate resultant vector length
            if R==0:
               #print 'trouble in cart2dir'
               #print cart
               return [0.0,0.0,0.0]
            D=arctan2(cart[1],cart[0])/rad  # calculate declination taking care of correct quadrants (arctan2)
            if D<0:D=D+360. # put declination between 0 and 360.
            if D>360.:D=D-360.
            Dir.append(D)  # append declination to Dir list
            I=scipy.arcsin(cart[2]/R)/rad # calculate inclination (converting to degrees)
            Dir.append(I) # append inclination to Dir list
            Dir.append(R) # append vector length to Dir list
            return Dir # return the directions list


      def dir2cart(d):
       # converts list or array of vector directions, in degrees, to array of cartesian coordinates, in x,y,z
        ints=ones(len(d)).transpose() # get an array of ones to plug into dec,inc pairs
        d=scipy.array(d)
        rad=pi/180.
        if len(d.shape)>1: # array of vectors
            decs,incs=d[:,0]*rad,d[:,1]*rad
            if d.shape[1]==3: ints=d[:,2] # take the given lengths
        else: # single vector
            decs,incs=scipy.array(d[0])*rad,scipy.array(d[1])*rad
            if len(d)==3: 
                ints=scipy.array(d[2])
            else:
                ints=scipy.array([1.])
        cart= scipy.array([ints*scipy.cos(decs)*scipy.cos(incs),ints*scipy.sin(decs)*scipy.cos(incs),ints*scipy.sin(incs)]).transpose()
        return cart

      #self.dir_pathes=self.WD


      #------------------------------------------------
      # Read magic measurement file and sort to blocks
      #------------------------------------------------

      # All data information is stored in Data[secimen]={}
      Data={}
      Data_hierarchy={}
      Data_hierarchy['locations']={}
      Data_hierarchy['sites']={}
      Data_hierarchy['samples']={}
      Data_hierarchy['specimens']={}
      Data_hierarchy['sample_of_specimen']={} 
      Data_hierarchy['site_of_specimen']={}   
      Data_hierarchy['site_of_sample']={}   

      # add dir to dir pathes for interpterer:
      if self.WD not in self.MagIC_directories_list:
          self.MagIC_directories_list.append(self.WD)
      #for dir_path in self.dir_pathes:
      #print "start Magic read %s " %self.magic_file
      try:
          meas_data,file_type=pmag.magic_read(self.magic_file)
      except:
          print "-E- ERROR: Cant read magic_measurement.txt file. File is corrupted."
          return {},{}

      #print "done Magic read %s " %self.magic_file

      self.GUI_log.write("-I- Read magic file  %s\n"%self.magic_file)

      # get list of unique specimen names
      
      CurrRec=[]
      #print "get sids"
      sids=pmag.get_specs(meas_data) # samples ID's
      #print "done get sids"

      #print "initialize blocks"
      
      for s in sids:
          if s not in Data.keys():
              Data[s]={}
              Data[s]['datablock']=[]
              Data[s]['trmblock']=[]
              Data[s]['zijdblock']=[]
          #zijdblock,units=pmag.find_dmag_rec(s,meas_data)
          #Data[s]['zijdblock']=zijdblock


      #print "done initialize blocks"

      #print "sorting meas data"

      for rec in meas_data:
          s=rec["er_specimen_name"]
          Data[s]['T_or_MW']="T"
          sample=rec["er_sample_name"]
          site=rec["er_site_name"]
          # if "er_site_name" in an empty string: use er_sample_name tp assign site to sample.
          if rec["er_site_name"]=="":
                site=sample
          location=""
          if "er_location_name" in rec.keys():
            location=rec["er_location_name"]   

          if  "LP-PI-M" in rec["magic_method_codes"]:
             Data[s]['T_or_MW']="MW"
          else:
             Data[s]['T_or_MW']="T"

          if "magic_method_codes" not in rec.keys():
              rec["magic_method_codes"]=""
          #methods=rec["magic_method_codes"].split(":")
          if "LP-PI-TRM" in rec["magic_method_codes"] or "LP-PI-M" in rec["magic_method_codes"]:
              Data[s]['datablock'].append(rec)
              # identify the lab DC field
              if (("LT-PTRM-I" in rec["magic_method_codes"] or "LT-T-I" in rec["magic_method_codes"]) and 'LP-TRM' not in rec["magic_method_codes"] )\
                 or "LT-PMRM-I" in rec["magic_method_codes"]:
                  Data[s]['Thellier_dc_field_uT']=float(rec["treatment_dc_field"])
                  Data[s]['Thellier_dc_field_phi']=float(rec['treatment_dc_field_phi'])
                  Data[s]['Thellier_dc_field_theta']=float(rec['treatment_dc_field_theta'])
                  
                
          if "LP-TRM" in rec["magic_method_codes"]:
              Data[s]['trmblock'].append(rec)

          if "LP-AN-TRM" in rec["magic_method_codes"]:
              if 'atrmblock' not in Data[s].keys():
                Data[s]['atrmblock']=[]
              Data[s]['atrmblock'].append(rec)


          if "LP-AN-ARM" in rec["magic_method_codes"]:
              if 'aarmblock' not in Data[s].keys():
                Data[s]['aarmblock']=[]
              Data[s]['aarmblock'].append(rec)

          if "LP-CR-TRM" in rec["magic_method_codes"]:
              if 'crblock' not in Data[s].keys():
                Data[s]['crblock']=[]
              Data[s]['crblock'].append(rec)

          #---- Zijderveld block

          EX=["LP-AN-ARM","LP-AN-TRM","LP-ARM-AFD","LP-ARM2-AFD","LP-TRM-AFD","LP-TRM","LP-TRM-TD","LP-X","LP-CR-TRM"] # list of excluded lab protocols
          #INC=["LT-NO","LT-AF-Z","LT-T-Z", "LT-M-Z", "LP-PI-TRM-IZ", "LP-PI-M-IZ"]
          INC=["LT-NO","LT-T-Z","LT-M-Z","LT-AF-Z"]
          methods=rec["magic_method_codes"].strip('\n').split(":")
          for i in range (len(methods)):
               methods[i]=methods[i].strip()
          if 'measurement_flag' not in rec.keys(): rec['measurement_flag']='g'
          skip=1
          for meth in methods:
               if meth in INC:
                   skip=0
          for meth in EX:
               if meth in methods:
                   skip=1
          if skip==0:
             if  Data[s]['T_or_MW']=="T" and  'treatment_temp' in rec.keys():
                 tr = float(rec["treatment_temp"])
             elif Data[s]['T_or_MW']=="MW" and "measurement_description" in rec.keys():
                    MW_step=rec["measurement_description"].strip('\n').split(":")
                    for STEP in MW_step:
                        if "Number" in STEP:
                            tr=float(STEP.split("-")[-1])
                                  
             if "LP-PI-TRM-IZ" in methods or "LP-PI-M-IZ" in methods:  # looking for in-field first thellier or microwave data - otherwise, just ignore this
                 ZI=0
             else:
                 ZI=1

             Mkeys=['measurement_magnitude','measurement_magn_moment','measurement_magn_volume','measurement_magn_mass']
             if tr !="":
                 dec,inc,int = "","",""
                 if "measurement_dec" in rec.keys() and rec["measurement_dec"] != "":
                     dec=float(rec["measurement_dec"])
                 if "measurement_inc" in rec.keys() and rec["measurement_inc"] != "":
                     inc=float(rec["measurement_inc"])
                 for key in Mkeys:
                     if key in rec.keys() and rec[key]!="":int=float(rec[key])
                 if 'magic_instrument_codes' not in rec.keys():rec['magic_instrument_codes']=''
                 #datablock.append([tr,dec,inc,int,ZI,rec['measurement_flag'],rec['magic_instrument_codes']])
                 if Data[s]['T_or_MW']=="T":
                     if tr==0.: tr=273.
                 # AFD
                 if "LT-AF-Z" in methods and "LP-AN-ARM" not in rec['magic_method_codes'] and "LP-DIR-AF" not in rec['magic_method_codes']:
                     if Data[s]['T_or_MW']=="T":
                         tr=tr-float(rec['treatment_ac_field'])*1e3 # AFD is amrked with negative

                 Data[s]['zijdblock'].append([tr,dec,inc,int,ZI,rec['measurement_flag'],rec['magic_instrument_codes']])
                 #print methods

##          # Fix zijderveld block for Thellier-Thellier protocol (II)
##          # (take the vector subtruction instead of the zerofield steps)
##
##          araiblock,field=self.sortarai(Data[s]['datablock'],s,0)
##          if "LP-PI-II" in Data[s]['datablock'][0]["magic_method_codes"] or "LP-PI-M-II" in Data[s]['datablock'][0]["magic_method_codes"] or "LP-PI-T-II" in Data[s]['datablock'][0]["magic_method_codes"]:
##              for zerofield in araiblock[0]:
##                  Data[s]['zijdblock'].append([zerofield[0],zerofield[1],zerofield[2],zerofield[3],0,'g',""])

       
          if sample not in Data_hierarchy['samples'].keys():
              Data_hierarchy['samples'][sample]=[]

          if site not in Data_hierarchy['sites'].keys():
              Data_hierarchy['sites'][site]=[]         

          if location not in Data_hierarchy['locations'].keys():
              Data_hierarchy['locations'][location]=[]         
          
          if s not in Data_hierarchy['samples'][sample]:
              Data_hierarchy['samples'][sample].append(s)

          if sample not in Data_hierarchy['sites'][site]:
              Data_hierarchy['sites'][site].append(sample)

          if site not in Data_hierarchy['locations'][location]:
              Data_hierarchy['locations'][location].append(site)

          Data_hierarchy['specimens'][s]=sample
          Data_hierarchy['sample_of_specimen'][s]=sample  
          Data_hierarchy['site_of_specimen'][s]=site  
          Data_hierarchy['site_of_sample'][sample]=site
      #print Data_hierarchy['site_of_sample']

          
      #print "done sorting meas data"
      
      self.specimens=Data.keys()
      self.specimens.sort()

      
      #------------------------------------------------
      # Read anisotropy file from rmag_anisotropy.txt
      #------------------------------------------------

      #if self.WD != "":
      rmag_anis_data=[]
      results_anis_data=[]
      try:
          rmag_anis_data,file_type=pmag.magic_read(os.path.join(self.WD, 'rmag_anisotropy.txt'))
          self.GUI_log.write( "-I- Anisotropy data read  %s/from rmag_anisotropy.txt\n"%self.WD)
      except:
          self.GUI_log.write("-W- WARNING cant find rmag_anisotropy in working directory\n")

      try:
          results_anis_data,file_type=pmag.magic_read(os.path.join(self.WD, 'rmag_results.txt'))
          self.GUI_log.write( "-I- Anisotropy data read  %s/from rmag_anisotropy.txt\n"%self.WD)
          
      except:
          self.GUI_log.write("-W- WARNING cant find rmag_anisotropy in working directory\n")

          
      for AniSpec in rmag_anis_data:
          s=AniSpec['er_specimen_name']

          if s not in Data.keys():
              self.GUI_log.write("-W- WARNING: specimen %s in rmag_anisotropy.txt but not in magic_measurement.txt. Check it !\n"%s)
              continue
          if 'AniSpec' in Data[s].keys():
              self.GUI_log.write("-W- WARNING: more than one anisotropy data for specimen %s !\n"%s)
          TYPE=AniSpec['anisotropy_type']
          if 'AniSpec' not in Data[s].keys():
              Data[s]['AniSpec']={}
          Data[s]['AniSpec'][TYPE]=AniSpec
        
      for AniSpec in results_anis_data:
          s=AniSpec['er_specimen_names']
          if s not in Data.keys():
              self.GUI_log.write("-W- WARNING: specimen %s in rmag_results.txt but not in magic_measurement.txt. Check it !\n"%s)
              continue
          TYPE=AniSpec['anisotropy_type']         
          if 'AniSpec' in Data[s].keys() and TYPE in  Data[s]['AniSpec'].keys():
              Data[s]['AniSpec'][TYPE].update(AniSpec)
              if 'result_description' in AniSpec.keys():
                result_description=AniSpec['result_description'].split(";")
                for description in result_description:
                    if "Critical F" in description:
                       desc=description.split(":")
                       Data[s]['AniSpec'][TYPE]['anisotropy_F_crit']=float(desc[1])
                
                          
      #------------------------------------------------
      # Calculate Non Linear TRM parameters
      # Following Shaar et al. (2010):
      #
      # Procedure:
      #
      # A) If there are only 2 NLT measurement: C
      #
      #   Cant do NLT correctio procedure (few data points).
      #   Instead, check the different in the ratio (M/B) in the two measurements.
      #   slop_diff = max(first slope, second slope)/min(first slope, second slope)
      #   if: 1.1 > slop_diff > 1.05 : WARNING
      #   if: > slop_diff > 1s.1 : WARNING
      #
      # B) If there are at least 3 NLT measurement:
      #
      # 1) Read the NLT measurement file
      #   If there is no baseline measurement in the NLT experiment:
      #    then take the baseline from the zero-field step of the IZZI experiment.
      #
      # 2) Fit tanh function of the NLT measurement normalized by M[oven field]
      #   M/M[oven field] = alpha * tanh (beta*B)
      #   alpha and beta are used for the Banc calculation using equation (3) in Shaar et al. (2010):
      #   Banc= tanh^-1[(b*Fa)/alpha]/beta where Fa  is anistropy correction factor and 'b' is the Arai plot slope.
      #
      # 3) If best fit function algorithm does not converge, check NLT data using option (A) above.
      #    If 
      #
      #------------------------------------------------



      # Searching and sorting NLT Data 
      #print "searching NLT data"

      for s in sids:
          datablock = Data[s]['datablock']
          trmblock = Data[s]['trmblock']

          if len(trmblock)<2:
              continue

          B_NLT,M_NLT=[],[]

          # find temperature of NLT acquisition
          NLT_temperature=float(trmblock[0]['treatment_temp'])
          
                 
          # search for Blab used in the IZZI experiment (need it for the following calculation)
          found_labfield=False  
          for rec in datablock:  
              if float(rec['treatment_dc_field'])!=0:
                  labfield=float(rec['treatment_dc_field'])
                  found_labfield=True
                  break
          if not found_labfield:
              continue

          # collect the data from trmblock
          M_baseline=0.
          for rec in trmblock:

              # if there is a baseline in TRM block, then use it 
              if float(rec['treatment_dc_field'])==0:
                  M_baseline=float(rec['measurement_magn_moment'])
              B_NLT.append(float(rec['treatment_dc_field']))
              M_NLT.append(float(rec['measurement_magn_moment']))

          # collect more data from araiblock

          '''
          for rec in datablock:
              if float(rec['treatment_temp'])==NLT_temperature and float(rec['treatment_dc_field']) !=0:
                  B_NLT.append(float(rec['treatment_dc_field']))
                  M_NLT.append(float(rec['measurement_magn_moment']))'''
                  
    
          # If cnat find baseline in trm block
          #  search for baseline in the Data block. 
          if M_baseline==0:
              m_tmp=[]
              for rec in datablock:
                  if float(rec['treatment_temp'])==NLT_temperature and float(rec['treatment_dc_field'])==0:
                     m_tmp.append(float(rec['measurement_magn_moment']))
                     self.GUI_log.write("-I- Found basleine for NLT measurements in datablock, specimen %s\n"%s)         
              if len(m_tmp)>0:
                  M_baseline = scipy.mean(m_tmp)
              

          ####  Ron dont delete it ### print "-I- Found %i NLT datapoints for specimen %s: B="%(len(B_NLT),s),array(B_NLT)*1e6

          #substitute baseline
          M_NLT=scipy.array(M_NLT)-M_baseline
          B_NLT=scipy.array(B_NLT)  
          # calculate M/B ratio for each step, and compare them
          # If cant do NLT correction: check a difference in M/B ratio
          # > 5% : WARNING
          # > 10%: ERROR           

          slopes=M_NLT/B_NLT

          if len(trmblock)==2:
              if max(slopes)/min(slopes)<1.05:
                  self.GUI_log.write("-I- 2 NLT measurement for specimen %s. [max(M/B)/ [min(M/B)] < 1.05.\n"%s)         
              elif max(slopes)/min(slopes)<1.1:
                  self.GUI_log.write("-W- WARNING: 2 NLT measurement for specimen %s. [max(M/B)]/ [min(M/B)] is %.2f  (   > 1.05 and  < 1.1 ). More NLT mrasurements may be required.\n" %(s,max(slopes)/min(slopes)))
                  #self.GUI_log.write("-I- NLT meaurements specime %s: B,M="%s,B_NLT,M_NLT)
              else:
                  self.GUI_log.write("-E- ERROR: 2 NLT measurement for specimen %s. [max(M/B)]/ [min(M/B)] is %.2f  ( > 1.1 ). More NLT mrasurements may be required  !\n" %(s,max(slopes)/min(slopes)))
                  #self.GUI_log.write("-I- NLT meaurements specime %s: B,M="%s,B_NLT,M_NLT)
                  
          # NLT procedure following Shaar et al (2010)        
          
          if len(trmblock)>2:
              red_flag=False

              # check alteration
              B_alterations=[]
              for i in range(len(B_NLT)):
                  if list(B_NLT).count(B_NLT[i])>1:
                      if B_NLT[i] not in B_alterations:
                        B_alterations.append(B_NLT[i]) 
              for B in B_alterations:
                  M=[]
                  for i in range(len(B_NLT)):
                      if B_NLT[i]==B:
                          M.append(M_NLT[i])
                  if (max(M)-min(M))/scipy.mean(M) > 0.05:
                    self.GUI_log.write("-E- ERROR: NLT for specimen %s does not pass 5 perc alteration check: %.3f \n" %(s,(max(M)-min(M))/scipy.mean(M)))
                    red_flag=True
                    
                      
                  
          if len(trmblock)>2 and not red_flag:
           
              B_NLT = pylab.append([0.],B_NLT)
              M_NLT = pylab.append([0.],M_NLT)
              
              try:
                  #print s,B_NLT, M_NLT    
                  # First try to fit tanh function (add point 0,0 in the begining)
                  alpha_0=max(M_NLT)
                  beta_0=2e4
                  popt, pcov = curve_fit(tan_h, B_NLT, M_NLT,p0=(alpha_0,beta_0))
                  M_lab=popt[0]*scipy.math.tanh(labfield*popt[1])

                  # Now  fit tanh function to the normalized curve
                  M_NLT_norm=M_NLT/M_lab
                  popt, pcov = curve_fit(tan_h, B_NLT, M_NLT_norm,p0=(popt[0]/M_lab,popt[1]))
                  Data[s]['NLT_parameters']={}
                  Data[s]['NLT_parameters']['tanh_parameters']=(popt, pcov)
                  Data[s]['NLT_parameters']['B_NLT']=B_NLT
                  Data[s]['NLT_parameters']['M_NLT_norm']=M_NLT_norm
                  
                  self.GUI_log.write("-I-  tanh parameters for specimen %s were calculated sucsessfuly\n"%s)
                                  
              except RuntimeError:
                  self.GUI_log.write( "-W- WARNING: Cant fit tanh function to NLT data specimen %s. Ignore NLT data for specimen %s. Instead check [max(M/B)]/ [min(M/B)] \n"%(s,s))
                  #print "-I- NLT meaurements specime %s: B,M="%s,B_NLT,M_NLT
                  
                  # Cant do NLT correction. Instead, check a difference in M/B ratio
                  # The maximum difference allowd is 5%
                  # if difference is larger than 5%: WARNING            
                  
                  if max(slopes)/min(slopes)<1.05:
                      self.GUI_log.write("-I- 2 NLT measurement for specimen %s. [max(M/B)/ [min(M/B)] < 1.05.\n"%s)         
                  elif max(slopes)/min(slopes)<1.1:
                      self.GUI_log.write("-W- WARNING: 2 NLT measurement for specimen %s. [max(M/B)]/ [min(M/B)] is %.2f  (   > 1.05 and  < 1.1 ). More NLT mrasurements may be required.\n" %(s,max(slopes)/min(slopes)))
                      #print "-I- NLT meaurements specime %s: B,M="%s,B_NLT,M_NLT
                  else:
                      self.GUI_log.write("-E- ERROR: 2 NLT measurement for specimen %s. [max(M/B)]/ [min(M/B)] is %.2f  ( > 1.1 ). More NLT mrasurements may be required  !\n" %(s,max(slopes)/min(slopes)))
                      #print "-I- NLT meaurements specime %s: B,M="%s,B_NLT,M_NLT
                  
      #print "done searching NLT data"
              
      self.GUI_log.write("-I- Done calculating non linear TRM parameters for all specimens\n")


      #------------------------------------------------
      # Calculate cooling rate experiments
      #
      #
      #
      #
      #
      #------------------------------------------------

      for s in sids:
          datablock = Data[s]['datablock']
          trmblock = Data[s]['trmblock']
          if 'crblock' in Data[s].keys():
              if len(Data[s]['crblock'])<3:
                  del Data[s]['crblock']
                  continue

              sample=Data_hierarchy['specimens'][s]
              # in MagIC format that cooling rate is in K/My
##              try:
##                  ancient_cooling_rate=float(self.Data_info["er_samples"][sample]['sample_cooling_rate'])
##                  ancient_cooling_rate=ancient_cooling_rate/(1e6*365*24*60) # change to K/minute
##              except:
##                  self.GUI_log.write("-W- Cant find ancient cooling rate estimation for sample %s"%sample)
##                  continue                  
              try:
                  ancient_cooling_rate=float(self.Data_info["er_samples"][sample]['sample_cooling_rate'])
                  ancient_cooling_rate=ancient_cooling_rate/(1e6*365.*24.*60.) # change to K/minute
              except:
                  self.GUI_log.write("-W- Cant find ancient cooling rate estimation for sample %s\n"%sample)
                  continue
              #self.Data_info["er_samples"]
              cooling_rate_data={}
              cooling_rate_data['pairs']=[]
              cooling_rates_list=[]
              cooling_rate_data['alteration_check']=[]
              for rec in Data[s]['crblock']:
                  magic_method_codes=rec['magic_method_codes'].strip(' ').strip('\n').split(":")
                  measurement_description=rec['measurement_description'].strip(' ').strip('\n').split(":")
                  if "LT-T-Z" in magic_method_codes:
                      cooling_rate_data['baseline']=float(rec['measurement_magn_moment'])
                      continue
                
                  index=measurement_description.index("K/min")
                  cooling_rate=float(measurement_description[index-1])
                  cooling_rates_list.append(cooling_rate)
                  moment=float(rec['measurement_magn_moment'])
                  if "LT-T-I" in magic_method_codes:
                      cooling_rate_data['pairs'].append([cooling_rate,moment])
                  if "LT-PTRM-I" in magic_method_codes:
                      cooling_rate_data['alteration_check']=[cooling_rate,moment]
              lab_cooling_rate=max(cooling_rates_list) 
              cooling_rate_data['lab_cooling_rate']= lab_cooling_rate                  

              #lab_cooling_rate = self.Data[self.s]['cooling_rate_data']['lab_cooling_rate']
              moments=[]
              lab_fast_cr_moments=[]
              lan_cooling_rates=[]
              for pair in cooling_rate_data['pairs']:
                    lan_cooling_rates.append(scipy.math.log(cooling_rate_data['lab_cooling_rate']/pair[0]))
                    moments.append(pair[1])
                    if pair[0]==cooling_rate_data['lab_cooling_rate']:
                        lab_fast_cr_moments.append(pair[1])
              #print s, cooling_rate_data['alteration_check']
              lan_cooling_rates.append(scipy.math.log(cooling_rate_data['lab_cooling_rate']/cooling_rate_data['alteration_check'][0]))
              lab_fast_cr_moments.append(cooling_rate_data['alteration_check'][1])
              moments.append(cooling_rate_data['alteration_check'][1])        

              lab_fast_cr_moment=scipy.mean(lab_fast_cr_moments)
              moment_norm=scipy.array(moments)/lab_fast_cr_moment
              (a,b)=polyfit(lan_cooling_rates, moment_norm, 1)
              #ancient_cooling_rate=0.41
              x0=scipy.math.log(cooling_rate_data['lab_cooling_rate']/ancient_cooling_rate)
              y0=a*x0+b
              MAX=max(lab_fast_cr_moments)
              MIN=min(lab_fast_cr_moments)
              
              #print MAX,MIN
              #print (MAX-MIN)/scipy.mean(MAX,MIN)
              #print abs((MAX-MIN)/scipy.mean(MAX,MIN))
              if  scipy.mean([MAX,MIN])==0:
                  alteration_check_perc=0
              else:
                  alteration_check_perc=100*abs((MAX-MIN)/scipy.mean([MAX,MIN]))
              #print s,alteration_check_perc
              #print "--"
              cooling_rate_data['ancient_cooling_rate']=ancient_cooling_rate
              cooling_rate_data['CR_correction_factor']=-999
              cooling_rate_data['lan_cooling_rates']=lan_cooling_rates
              cooling_rate_data['moment_norm']=moment_norm
              cooling_rate_data['polyfit']=[a,b]
              cooling_rate_data['CR_correction_factor_flag']=""
              cooling_rate_data['x0']=x0
              
              #if y0<=1:
              #    cooling_rate_data['CR_correction_factor_flag']=cooling_rate_data['CR_correction_factor_flag']+"bad CR measurement data "
              #    cooling_rate_data['CR_correction_factor']=-999

              if alteration_check_perc>5:
                  cooling_rate_data['CR_correction_factor_flag']=cooling_rate_data['CR_correction_factor_flag']+"alteration > 5% "
                  cooling_rate_data['CR_correction_factor']=-999
              #if y0>1 and alteration_check_perc<=5:    
              if alteration_check_perc<=5:    
                  cooling_rate_data['CR_correction_factor_flag']="calculated"
                  cooling_rate_data['CR_correction_factor']=1./(y0)
              
              Data[s]['cooling_rate_data']= cooling_rate_data     

              
               
      # go over all specimens. if there is a specimen with no cooling rate data
      # use the mean cooling rate corretion of the other specimens from the same sample
      # this cooling rate correction is flagges as "inferred"

      for sample in Data_hierarchy['samples'].keys():
          CR_corrections=[]
          for s in Data_hierarchy['samples'][sample]:
              if 'cooling_rate_data' in Data[s].keys():
                  if 'CR_correction_factor' in Data[s]['cooling_rate_data'].keys():
                      if 'CR_correction_factor_flag' in Data[s]['cooling_rate_data'].keys():
                          if Data[s]['cooling_rate_data']['CR_correction_factor_flag']=='calculated':
                              CR_corrections.append(Data[s]['cooling_rate_data']['CR_correction_factor'])
          if len(CR_corrections) > 0:
              mean_CR_correction=scipy.mean(CR_corrections)
          else:
              mean_CR_correction=-1
          if mean_CR_correction != -1:
              for s in Data_hierarchy['samples'][sample]:
                  if 'cooling_rate_data' not in Data[s].keys():
                      Data[s]['cooling_rate_data']={}
                  if 'CR_correction_factor' not in Data[s]['cooling_rate_data'].keys() or\
                     Data[s]['cooling_rate_data']['CR_correction_factor_flag']!="calculated":
                        Data[s]['cooling_rate_data']['CR_correction_factor']=mean_CR_correction
                        if 'CR_correction_factor_flag' in Data[s]['cooling_rate_data'].keys():
                            Data[s]['cooling_rate_data']['CR_correction_factor_flag']=Data[s]['cooling_rate_data']['CR_correction_factor_flag']+":"+"inferred"
                        else:
                            Data[s]['cooling_rate_data']['CR_correction_factor_flag']="inferred"
                            
              
      #------------------------------------------------
      # sort Arai block
      #------------------------------------------------

      #print "sort blocks to arai, zij. etc."

      for s in self.specimens:
        # collected the data
        datablock = Data[s]['datablock']

        if len(datablock) <4:
           self.GUI_log.write("-E- ERROR: skipping specimen %s, not enough measurements - moving forward \n"%s)
           del Data[s]
           sample=Data_hierarchy['specimens'][s]
           del Data_hierarchy['specimens'][s]
           Data_hierarchy['samples'][sample].remove(s)
           continue 

        araiblock,field=self.sortarai(datablock,s,0)

        # thermal or microwave
        rec=datablock[0]
        if "treatment_temp" in rec.keys() and rec["treatment_temp"]!="":
            temp=float(rec["treatment_temp"])
            THERMAL=True; MICROWAVE=False
        elif "treatment_mw_power" in rec.keys() and rec["treatment_mw_power"]!="":
            THERMAL=False; MICROWAVE=True
        

        
        # Fix zijderveld block for Thellier-Thellier protocol (II)
        # (take the vector subtruction instead of the zerofield steps)

        if "LP-PI-II" in Data[s]['datablock'][0]["magic_method_codes"] or "LP-PI-M-II" in Data[s]['datablock'][0]["magic_method_codes"] or "LP-PI-T-II" in Data[s]['datablock'][0]["magic_method_codes"]:
          Data[s]['zijdblock']=[]  
          for zerofield in araiblock[0]:
              Data[s]['zijdblock'].append([zerofield[0],zerofield[1],zerofield[2],zerofield[3],0,'g',""])
           
        zijdblock=Data[s]['zijdblock']



        Data[s]['araiblock']=araiblock
        Data[s]['pars']={}
        Data[s]['pars']['lab_dc_field']=field
        Data[s]['pars']['er_specimen_name']=s
        Data[s]['pars']['er_sample_name']=Data_hierarchy['specimens'][s]

        Data[s]['lab_dc_field']=field
        Data[s]['er_specimen_name']=s   
        Data[s]['er_sample_name']=Data_hierarchy['specimens'][s]
        
        first_Z=araiblock[0]
        #if len(first_Z)<3:
            #continue

        if len(araiblock[0])!= len(araiblock[1]):
           self.GUI_log.write( "-E- ERROR: unequal length of Z steps and I steps. Check specimen %s"% s)
           #continue

      # Fix zijderveld block for Thellier-Thellier protocol (II)
      # (take the vector subtruiction instead of the zerofield steps)
      #araiblock,field=self.sortarai(Data[s]['datablock'],s,0)
      #if "LP-PI-II" in Data[s]['datablock'][0]["magic_method_codes"] or "LP-PI-M-II" in Data[s]['datablock'][0]["magic_method_codes"] or "LP-PI-T-II" in Data[s]['datablock'][0]["magic_method_codes"]:
      #    for zerofield in araiblock[0]:
      #        Data[s]['zijdblock'].append([zerofield[0],zerofield[1],zerofield[2],zerofield[3],0,'g',""])
##        if "LP-PI-II" in datablock[0]["magic_method_codes"] or "LP-PI-M-II" in datablock[0]["magic_method_codes"] or "LP-PI-T-II" in datablock[0]["magic_method_codes"]:
##          for zerofield in araiblock[0]:
##              Data[s]['zijdblock'].append([zerofield[0],zerofield[1],zerofield[2],zerofield[3],0,'g',""])


        #--------------------------------------------------------------
        # collect all zijderveld data to array and calculate VDS
        #--------------------------------------------------------------

        z_temperatures=[row[0] for row in zijdblock]
        zdata=[]
        vector_diffs=[]

        # if AFD before the Thellier Experiment: ignore the AF steps in NRM calculation
        #for i in range(len(zijdblock)):
            #if "AFD" not in str(zijdblock[i][0]):
        NRM=zijdblock[0][3]
        for k in range(len(zijdblock)):
            DIR = [zijdblock[k][1],zijdblock[k][2],zijdblock[k][3]/NRM]
            cart = pmag.dir2cart(DIR)
            zdata.append(scipy.array([cart[0],cart[1],cart[2]]))
            if k>0:
                vector_diffs.append(scipy.sqrt(sum((scipy.array(zdata[-2])-scipy.array(zdata[-1]))**2)))
        vector_diffs.append(scipy.sqrt(sum(scipy.array(zdata[-1])**2))) # last vector of the vds
        vds = sum(vector_diffs)  # vds calculation       
        zdata = scipy.array(zdata)

        Data[s]['vector_diffs']=scipy.array(vector_diffs)
        Data[s]['vds']=vds
        Data[s]['zdata']=zdata
        Data[s]['z_temp']=z_temperatures
        Data[s]['NRM']=NRM
        
      #--------------------------------------------------------------    
      # Rotate zijderveld plot
      #--------------------------------------------------------------

        DIR_rot=[]
        CART_rot=[]
        # rotate to be as NRM
        NRM_dir=pmag.cart2dir(Data[s]['zdata'][0])
         
        NRM_dec=NRM_dir[0]
        NRM_dir[0]=0
        CART_rot.append(pmag.dir2cart(NRM_dir))

        
        for i in range(1,len(Data[s]['zdata'])):
          DIR=pmag.cart2dir(Data[s]['zdata'][i])
          DIR[0]=DIR[0]-NRM_dec
          CART_rot.append(scipy.array(pmag.dir2cart(DIR)))
          #print array(dir2cart(DIR))
          
        CART_rot=scipy.array(CART_rot)
        Data[s]['zij_rotated']=CART_rot
        #--------------------------------------------------------------
        # collect all Arai plot data points to array 
        #--------------------------------------------------------------

        # collect Arai data points
        zerofields,infields=araiblock[0],araiblock[1]

        Data[s]['NRMS']=zerofields
        Data[s]['PTRMS']=infields
        
        x_Arai,y_Arai=[],[] # all the data points               
        t_Arai=[]
        steps_Arai=[]              

        #NRM=zerofields[0][3]
        infield_temperatures=[row[0] for row in infields]

        for k in range(len(zerofields)):                  
          index_infield=infield_temperatures.index(zerofields[k][0])
          x_Arai.append(infields[index_infield][3]/NRM)
          y_Arai.append(zerofields[k][3]/NRM)
          t_Arai.append(zerofields[k][0])
          if zerofields[k][4]==1:
            steps_Arai.append('ZI')
          else:
            steps_Arai.append('IZ')        
        x_Arai=scipy.array(x_Arai)
        y_Arai=scipy.array(y_Arai)
        #else:
        #    Data[s]['pars']['magic_method_codes']=""
        Data[s]['x_Arai']=x_Arai
        Data[s]['y_Arai']=y_Arai
        Data[s]['t_Arai']=t_Arai
        Data[s]['steps_Arai']=steps_Arai


        #--------------------------------------------------------------
        # collect all pTRM check to array 
        #--------------------------------------------------------------

        ptrm_checks = araiblock[2]
        zerofield_temperatures=[row[0] for row in zerofields]

        x_ptrm_check,y_ptrm_check,ptrm_checks_temperatures,=[],[],[]
        x_ptrm_check_starting_point,y_ptrm_check_starting_point,ptrm_checks_starting_temperatures=[],[],[]
        for k in range(len(ptrm_checks)):
          if ptrm_checks[k][0] in zerofield_temperatures:
              zero_field_index=ptrm_checks[k][4]
              #print Data[s]['datablock']
              
              # find the starting point of the pTRM check:
              rec=Data[s]['datablock'][zero_field_index]
              if THERMAL:
                    starting_temperature=(float(rec['treatment_temp']))
                    #found_start_temp=True
              elif MICROWAVE:
                    MW_step=rec["measurement_description"].strip('\n').split(":")
                    for STEP in MW_step:
                        if "Number" in STEP:
                            starting_temperature=float(STEP.split("-")[-1])
                            #found_start_temp=True
                      

                  #if MICROWAVE:
                  #  if "measurement_description" in rec.keys():
                  #      MW_step=rec["measurement_description"].strip('\n').split(":")
                  #      for STEP in MW_step:
                  #          if "Number" in STEP:
                  #              this_temp=float(STEP.split("-")[-1])
              #if found_start_temp==False:
              #      continue
              try:
              #if True:
                index=t_Arai.index(starting_temperature)
                x_ptrm_check_starting_point.append(x_Arai[index])
                y_ptrm_check_starting_point.append(y_Arai[index])
                ptrm_checks_starting_temperatures.append(starting_temperature)
                
                #print ptrm_checks[k]
                #print ' ptrm_checks[k][4]', ptrm_checks[k][4]
                if ptrm_checks[k][5]==0:
                    index_zerofield=zerofield_temperatures.index(ptrm_checks[k][0])
                    index_infield=infield_temperatures.index(ptrm_checks[k][0])
                    infield_cart=dir2cart([infields[index_infield][1],infields[index_infield][2],infields[index_infield][3]])
                    ptrm_check_cart=dir2cart([ptrm_checks[k][1],ptrm_checks[k][2],ptrm_checks[k][3]])
                    ptrm_check=cart2dir(scipy.array(infield_cart)-scipy.array(ptrm_check_cart))
                    x_ptrm_check.append(ptrm_check[2]/NRM)
                    y_ptrm_check.append(zerofields[index_zerofield][3]/NRM)
                    ptrm_checks_temperatures.append(ptrm_checks[k][0])
                else:
                    index_zerofield=zerofield_temperatures.index(ptrm_checks[k][0])
                    x_ptrm_check.append(ptrm_checks[k][3]/NRM)
                    y_ptrm_check.append(zerofields[index_zerofield][3]/NRM)
                    ptrm_checks_temperatures.append(ptrm_checks[k][0])
              #else:      
              except:
                pass
                    
                    
        x_ptrm_check=scipy.array(x_ptrm_check)  
        ptrm_check=scipy.array(y_ptrm_check)
        ptrm_checks_temperatures=scipy.array(ptrm_checks_temperatures)
        Data[s]['PTRM_Checks']=ptrm_checks
        Data[s]['x_ptrm_check']=x_ptrm_check
        Data[s]['y_ptrm_check']=y_ptrm_check        
        Data[s]['ptrm_checks_temperatures']=ptrm_checks_temperatures
        Data[s]['x_ptrm_check_starting_point']=scipy.array(x_ptrm_check_starting_point)
        Data[s]['y_ptrm_check_starting_point']=scipy.array(y_ptrm_check_starting_point)               
        Data[s]['ptrm_checks_starting_temperatures']=scipy.array(ptrm_checks_starting_temperatures)
##        if len(ptrm_checks_starting_temperatures) != len(ptrm_checks_temperatures):
##            print s
##            print Data[s]['ptrm_checks_temperatures']
##            print Data[s]['ptrm_checks_starting_temperatures']
##            print "help"
            
        #--------------------------------------------------------------
        # collect tail checks 
        #--------------------------------------------------------------


        ptrm_tail = araiblock[3]
        #print s
        #print ptrm_tail
        #print "-----"
        x_tail_check,y_tail_check,tail_check_temperatures=[],[],[]
        x_tail_check_starting_point,y_tail_check_starting_point,tail_checks_starting_temperatures=[],[],[]
         
        for k in range(len(ptrm_tail)):
          #if float(ptrm_tail[k][0]) in zerofield_temperatures:

            # find the starting point of the pTRM check:
            for i in range(len(datablock)):
                rec=datablock[i]                
                if (THERMAL and "LT-PTRM-MD" in rec['magic_method_codes'] and float(rec['treatment_temp'])==ptrm_tail[k][0])\
                   or\
                   (MICROWAVE and "LT-PMRM-MD" in rec['magic_method_codes'] and "measurement_description" in rec.keys() and "Step Number-%.0f"%float(ptrm_tail[k][0]) in rec["measurement_description"]):
                    if THERMAL:
                        starting_temperature=(float(datablock[i-1]['treatment_temp']))
                    elif MICROWAVE:
                        MW_step=datablock[i-1]["measurement_description"].strip('\n').split(":")
                        for STEP in MW_step:
                            if "Number" in STEP:
                                starting_temperature=float(STEP.split("-")[-1])

                    try:

                        index=t_Arai.index(starting_temperature)
                        x_tail_check_starting_point.append(x_Arai[index])
                        y_tail_check_starting_point.append(y_Arai[index])
                        tail_checks_starting_temperatures.append(starting_temperature)

                        index_infield=infield_temperatures.index(ptrm_tail[k][0])
                        x_tail_check.append(infields[index_infield][3]/NRM)
                        y_tail_check.append(ptrm_tail[k][3]/NRM + zerofields[index_infield][3]/NRM)
                        tail_check_temperatures.append(ptrm_tail[k][0])

                        break
                    except:
                        pass


        x_tail_check=scipy.array(x_tail_check)  
        y_tail_check=scipy.array(y_tail_check)
        tail_check_temperatures=scipy.array(tail_check_temperatures)
        x_tail_check_starting_point=scipy.array(x_tail_check_starting_point)
        y_tail_check_starting_point=scipy.array(y_tail_check_starting_point)
        tail_checks_starting_temperatures=scipy.array(tail_checks_starting_temperatures)

        Data[s]['TAIL_Checks']=ptrm_tail        
        Data[s]['x_tail_check']=x_tail_check
        Data[s]['y_tail_check']=y_tail_check
        Data[s]['tail_check_temperatures']=tail_check_temperatures
        Data[s]['x_tail_check_starting_point']=x_tail_check_starting_point
        Data[s]['y_tail_check_starting_point']=y_tail_check_starting_point
        Data[s]['tail_checks_starting_temperatures']=tail_checks_starting_temperatures


        #--------------------------------------------------------------
        # collect additivity checks 
        #--------------------------------------------------------------


        additivity_checks = araiblock[6]
        x_AC,y_AC,AC_temperatures,AC=[],[],[],[]
        x_AC_starting_point,y_AC_starting_point,AC_starting_temperatures=[],[],[]

        tmp_data_block=list(copy.copy(datablock))
        #print "specimen:",s
        for k in range(len(additivity_checks)):
          if additivity_checks[k][0] in zerofield_temperatures:
            for i in range(len(tmp_data_block)):
                rec=tmp_data_block[i]                
                if "LT-PTRM-AC" in rec['magic_method_codes'] and float(rec['treatment_temp'])==additivity_checks[k][0]:
                    del(tmp_data_block[i])
                    break
                    
            # find the infield step that comes before the additivity check
            foundit=False
            for j in range(i-1,1,-1):
                if "LT-T-I" in tmp_data_block[j]['magic_method_codes']:
                  found_starting_temperature=True
                  starting_temperature=float(tmp_data_block[j]['treatment_temp']);
                  break
            #for j in range(len(Data[s]['t_Arai'])):
            #    print Data[s]['t_Arai'][j]
            #    if float(Data[s]['t_Arai'][j])==additivity_checks[k][0]:
            #      found_zerofield_step=True
            #      pTRM=Data[s]['x_Arai'][j]
            #      AC=Data[s]['x_Arai'][j]-additivity_checks[k][3]/NRM
            #      break
            if found_starting_temperature:
                    try:
                        index=t_Arai.index(starting_temperature)
                        x_AC_starting_point.append(x_Arai[index])
                        y_AC_starting_point.append(y_Arai[index])
                        AC_starting_temperatures.append(starting_temperature)

                        index_zerofield=zerofield_temperatures.index(additivity_checks[k][0])
                        x_AC.append(additivity_checks[k][3]/NRM)
                        y_AC.append(zerofields[index_zerofield][3]/NRM)
                        AC_temperatures.append(additivity_checks[k][0])
                        index_pTRMs=t_Arai.index(additivity_checks[k][0])
                        AC.append(additivity_checks[k][3]/NRM - x_Arai[index_pTRMs])
                        #print "Tmin=",additivity_checks[k][0],"pTRM1= ",x_Arai[index_pTRMs]
                        #print "Tmax=",additivity_checks[k][0],"pTRM2= ",x_Arai[index]
                        #print "pTRM_*=",x_Arai[index]-x_Arai[index_pTRMs]
                        #print "index 1:",index
                        #print "additivity_checks[k][3]/NRM",additivity_checks[k][3]/NRM,pmag.dir2cart([additivity_checks[k][1],additivity_checks[k][2],additivity_checks[k][3]])
                        #print "x_Arai[index_pTRMs]",x_Arai[index_pTRMs]
                        #print "x_AC",x_AC
                        #print "pTRM_j_i", x_Arai[index]-additivity_checks[k][3]/NRM
                        #print "AC",additivity_checks[k][3]/NRM - x_Arai[index_pTRMs]
                        #print "....."
                    except:
                        pass


                

        x_AC=scipy.array(x_AC)  
        y_AC=scipy.array(y_AC)
        AC_temperatures=scipy.array(AC_temperatures)
        x_AC_starting_point=scipy.array(x_AC_starting_point)
        y_AC_starting_point=scipy.array(y_AC_starting_point)
        AC_starting_temperatures=scipy.array(AC_starting_temperatures)
        AC=scipy.array(AC)

        Data[s]['AC']=AC
        #print s
        #print "AC",AC
        #print "x_AC",x_AC
        #print "x_AC",x_AC
        
        Data[s]['x_additivity_check']=x_AC
        Data[s]['y_additivity_check']=y_AC
        Data[s]['additivity_check_temperatures']=AC_temperatures
        Data[s]['x_additivity_check_starting_point']=x_AC_starting_point
        Data[s]['y_additivity_check_starting_point']=y_AC_starting_point
        Data[s]['additivity_check_starting_temperatures']=AC_starting_temperatures

        
        
##        #--------------------------------------------------------------
##        # collect tail checks 
##        #--------------------------------------------------------------
##
##
##        ptrm_tail = araiblock[3]
##        #print ptrm_tail
##        x_tail_check,y_tail_check=[],[]
##
##        for k in range(len(ptrm_tail)):                  
##          index_infield=infield_temperatures.index(ptrm_tail[k][0])
##          x_tail_check.append(infields[index_infield][3]/NRM)
##          y_tail_check.append(ptrm_tail[k][3]/NRM + zerofields[index_infield][3]/NRM)
##          
##
##        x_tail_check=scipy.array(x_tail_check)  
##        y_tail_check=scipy.array(y_tail_check)
##
##        Data[s]['x_tail_check']=x_tail_check
##        Data[s]['y_tail_check']=y_tail_check

      self.GUI_log.write("-I- number of specimens in this project directory: %i\n"%len(self.specimens))
      self.GUI_log.write("-I- number of samples in this project directory: %i\n"%len(Data_hierarchy['samples'].keys()))

      print "done sort blocks to arai, zij. etc."
      return(Data,Data_hierarchy)

      

    #--------------------------------------------------------------    
    # Read all information file (er_locations, er_samples, er_sites, er_ages)
    #--------------------------------------------------------------
    def get_data_info(self):
        Data_info={}
        data_er_samples={}
        data_er_ages={}
        data_er_sites={}

        try:
            data_er_samples=self.read_magic_file(os.path.join(self.WD, "er_samples.txt"),1,'er_sample_name')
        except:
            self.GUI_log.write ("-W- Cant find er_sample.txt in project directory\n")

        try:
            data_er_sites=self.read_magic_file(os.path.join(self.WD, "er_sites.txt"),1,'er_site_name')
        except:
            self.GUI_log.write ("-W- Cant find er_sites.txt in project directory\n")

        try:
            data_er_ages=self.read_er_ages_file(os.path.join(self.WD, "er_ages.txt"),1,["er_site_name","er_sample_name"])
        except:
            self.GUI_log.write ("-W- Cant find er_ages.txt in project directory\n")

            #try:
            #    data_er_ages=read_magic_file(self.WD+"/er_ages.txt",'er_site_name')
            #except:    
            #    self.GUI_log.write ("-W- Cant find er_ages in project directory\n")


        Data_info["er_samples"]=data_er_samples
        Data_info["er_sites"]=data_er_sites
        Data_info["er_ages"]=data_er_ages
        
        
        return(Data_info)


    #def get_site_from_hierarchy(self,sample):
    #    site=""
    #    sites=self.Data_hierarchy['sites'].keys()
    #    for S in sites:
    #        if sample in self.Data_hierarchy['sites'][S]:
    #            site=S
    #            break
    #    return(site)
    
    
    #--------------------------------------------------------------    
    # Read previose interpretation from pmag_specimens.txt (if exist)
    #--------------------------------------------------------------
    
    def get_previous_interpretation(self):
        prev_pmag_specimen=[]
        try:
            prev_pmag_specimen,file_type=pmag.magic_read(os.path.join(self.WD, "pmag_specimens.txt"))
            self.GUI_log.write ("-I- Read pmag_specimens.txt for previous interpretation")
            print "-I- Read pmag_specimens.txt for previous interpretation"
        except:
            self.GUI_log.write ("-I- No pmag_specimens.txt for previous interpretation")
            return
        # first delete all previous interpretation
        for sp in self.Data.keys():
            del self.Data[sp]['pars']
            self.Data[sp]['pars']={}
            self.Data[sp]['pars']['lab_dc_field']=self.Data[sp]['lab_dc_field']
            self.Data[sp]['pars']['er_specimen_name']=self.Data[sp]['er_specimen_name']   
            self.Data[sp]['pars']['er_sample_name']=self.Data[sp]['er_sample_name']
        self.Data_samples={}
        self.Data_sites={}

        #specimens_list=pmag.get_specs(self.WD+"/pmag_specimens.txt")
        #specimens_list.sort()
        for rec in prev_pmag_specimen:
            if "LP-PI" not in rec["magic_method_codes"]:
                continue
            if "measurement_step_min" not in rec.keys() or rec['measurement_step_min']=="":
                continue
            if "measurement_step_max" not in rec.keys() or rec['measurement_step_max']=="":
                continue
                
            specimen=rec['er_specimen_name']
            tmin_kelvin=float(rec['measurement_step_min'])
            tmax_kelvin=float(rec['measurement_step_max'])
            if specimen not in self.redo_specimens.keys():
                self.redo_specimens[specimen]={}
                self.redo_specimens[specimen]['t_min']=float(tmin_kelvin)
                self.redo_specimens[specimen]['t_max']=float(tmax_kelvin)
            if specimen in self.Data.keys():
                if tmin_kelvin not in self.Data[specimen]['t_Arai'] or tmax_kelvin not in self.Data[specimen]['t_Arai'] :
                    self.GUI_log.write ("-W- WARNING: cant fit temperature bounds in the redo file to the actual measurement. specimen %s\n"%specimen)
                else:
                    try:
                        self.Data[specimen]['pars']=thellier_gui_lib.get_PI_parameters(self.Data,self.acceptance_criteria, self.preferences,specimen,float(tmin_kelvin),float(tmax_kelvin),self.GUI_log,THERMAL,MICROWAVE)
                        self.Data[specimen]['pars']['saved']=True
                        # write intrepretation into sample data
                        sample=self.Data_hierarchy['specimens'][specimen]
                        if sample not in self.Data_samples.keys():
                            self.Data_samples[sample]={}
                        if specimen not in self.Data_samples[sample].keys():
                            self.Data_samples[sample][specimen]={}
                        self.Data_samples[sample][specimen]['B']=self.Data[specimen]['pars']['specimen_int_uT']
                        
                        site=thellier_gui_lib.get_site_from_hierarchy(sample,self.Data_hierarchy)
                        if site not in self.Data_sites.keys():
                            self.Data_sites[site]={}
                        if specimen not in self.Data_sites[site].keys():
                            self.Data_sites[site][specimen]={}
                        self.Data_sites[site][specimen]['B']=self.Data[specimen]['pars']['specimen_int_uT']

                    except:
                        self.GUI_log.write ("-E- ERROR. Cant calculate PI paremeters for specimen %s using redo file. Check!"%(specimen))
            else:
                self.GUI_log.write ("-W- WARNING: Cant find specimen %s from redo file in measurement file!\n"%specimen)

        #try:
        #    self.s
        #except:
        try:
            self.s=self.specimens[0]                
            self.pars=self.Data[self.s]['pars']
            self.clear_boxes()
            self.draw_figure(self.s)
            self.update_GUI_with_new_interpretation()
        except:
            pass
        
                    


#===========================================================
#  definitions inherited and mofified from pmag.py
#===========================================================
       
                


    def sortarai(self,datablock,s,Zdiff):

        """
         sorts data block in to first_Z, first_I, etc.
        """
        first_Z,first_I,zptrm_check,ptrm_check,ptrm_tail=[],[],[],[],[]
        field,phi,theta="","",""
        starthere=0
        Treat_I,Treat_Z,Treat_PZ,Treat_PI,Treat_M,Treat_AC=[],[],[],[],[],[]
        ISteps,ZSteps,PISteps,PZSteps,MSteps,ACSteps=[],[],[],[],[],[]
        GammaChecks=[] # comparison of pTRM direction acquired and lab field
        Mkeys=['measurement_magn_moment','measurement_magn_volume','measurement_magn_mass','measurement_magnitude']
        rec=datablock[0]
        for key in Mkeys:
            if key in rec.keys() and rec[key]!="":
                momkey=key
                break
    # first find all the steps
        for k in range(len(datablock)):
            rec=datablock[k]
            if "treatment_temp" in rec.keys() and rec["treatment_temp"]!="":
                temp=float(rec["treatment_temp"])
                THERMAL=True; MICROWAVE=False
            elif "treatment_mw_power" in rec.keys() and rec["treatment_mw_power"]!="":
                THERMAL=False; MICROWAVE=True
                if "measurement_description" in rec.keys():
                    MW_step=rec["measurement_description"].strip('\n').split(":")
                    for STEP in MW_step:
                        if "Number" in STEP:
                            temp=float(STEP.split("-")[-1])

                
            methcodes=[]
            tmp=rec["magic_method_codes"].split(":")
            for meth in tmp:
                methcodes.append(meth.strip())
            # for thellier-thellier
            if 'LT-T-I' in methcodes and 'LP-PI-TRM' in methcodes and 'LP-TRM' not in methcodes :
                Treat_I.append(temp)
                ISteps.append(k)
                if field=="":field=float(rec["treatment_dc_field"])
                if phi=="":
                    phi=float(rec['treatment_dc_field_phi'])
                    theta=float(rec['treatment_dc_field_theta'])
                    
            # for Microwave
            if 'LT-M-I' in methcodes and 'LP-PI-M' in methcodes :
                Treat_I.append(temp)
                ISteps.append(k)
                if field=="":field=float(rec["treatment_dc_field"])
                if phi=="":
                    phi=float(rec['treatment_dc_field_phi'])
                    theta=float(rec['treatment_dc_field_theta'])

    # stick  first zero field stuff into first_Z 
            if 'LT-NO' in methcodes:
                Treat_Z.append(temp)
                ZSteps.append(k)
            if "LT-AF-Z" in methcodes and 'treatment_ac_field' in rec.keys():
                AFD_after_NRM=True
                # consider AFD before T-T experiment ONLY if it comes before the experiment
                for i in range(len(first_I)):
                    if float(first_I[i][3])!=0: # check if there was an infield step before the AFD
                        AFD_after_NRM=False
                    if AFD_after_NRM:
                        AF_field=float(rec['treatment_ac_field'])*1000
                        dec=float(rec["measurement_dec"])
                        inc=float(rec["measurement_inc"])
                        intensity=float(rec[momkey])
                        first_I.append([273.-AF_field,0.,0.,0.,1])
                        first_Z.append([273.-AF_field,dec,inc,intensity,1])  # NRM step
            if 'LT-T-Z' in methcodes or 'LT-M-Z' in methcodes: 
                Treat_Z.append(temp)
                ZSteps.append(k)
            if 'LT-PTRM-Z' :
                Treat_PZ.append(temp)
                PZSteps.append(k)
            if 'LT-PTRM-I' in methcodes or 'LT-PMRM-I' in methcodes:
                Treat_PI.append(temp)
                PISteps.append(k)
            if 'LT-PTRM-MD' in methcodes or 'LT-PMRM-MD' in methcodes:
                Treat_M.append(temp)
                MSteps.append(k)
            if 'LT-PTRM-AC' in methcodes or 'LT-PMRM-AC' in methcodes:
                Treat_AC.append(temp)
                ACSteps.append(k)
            if 'LT-NO' in methcodes:
                dec=float(rec["measurement_dec"])
                inc=float(rec["measurement_inc"])
                moment=float(rec["measurement_magn_moment"])
                if 'LP-PI-M'  not in methcodes:
                    first_I.append([273,0.,0.,0.,1])
                    first_Z.append([273,dec,inc,moment,1])  # NRM step
                else:
                    first_I.append([0,0.,0.,0.,1])
                    first_Z.append([0,dec,inc,moment,1])  # NRM step
                    
        #---------------------
        # find  IZ and ZI
        #---------------------
                    
                
        for temp in Treat_I: # look through infield steps and find matching Z step
            if temp in Treat_Z: # found a match
                istep=ISteps[Treat_I.index(temp)]
                irec=datablock[istep]
                methcodes=[]
                tmp=irec["magic_method_codes"].split(":")
                for meth in tmp: methcodes.append(meth.strip())
                brec=datablock[istep-1] # take last record as baseline to subtract  
                zstep=ZSteps[Treat_Z.index(temp)]
                zrec=datablock[zstep]
        # sort out first_Z records
                # check if ZI/IZ in in method codes:
                ZI=""
                if "LP-PI-TRM-IZ" in methcodes or "LP-PI-M-IZ" in methcodes or "LP-PI-IZ" in methcodes: 
                    ZI=0    
                elif "LP-PI-TRM-ZI" in methcodes or "LP-PI-M-ZI" in methcodes or "LP-PI-ZI" in methcodes:  
                    ZI=1    
                elif "LP-PI-BT-IZZI" in methcodes:
                    ZI==""
                    i_intex,z_intex=0,0
                    foundit=False
                    for i in range(len(datablock)):
                        if THERMAL:
                            if ('treatment_temp' in datablock[i].keys() and float(temp)==float(datablock[i]['treatment_temp'])):
                                foundit=True
                        if MICROWAVE:
                            if ('measurement_description' in datablock[i].keys()):
                                MW_step=datablock[i]["measurement_description"].strip('\n').split(":")
                                for STEP in MW_step:
                                    if "Number" in STEP:
                                        ThisStep=float(STEP.split("-")[-1])
                                        if ThisStep==float(temp):                                    
                                            foundit=True
                        if foundit:                        
                            if "LT-T-Z" in datablock[i]['magic_method_codes'].split(":") or "LT-M-Z" in datablock[i]['magic_method_codes'].split(":"):
                                z_intex=i
                            if "LT-T-I" in datablock[i]['magic_method_codes'].split(":") or "LT-M-I" in datablock[i]['magic_method_codes'].split(":"):
                                i_intex=i
                            foundit=False    
                            
                    if  z_intex < i_intex:
                        ZI=1
                    else:
                        ZI=0
                dec=float(zrec["measurement_dec"])
                inc=float(zrec["measurement_inc"])
                str=float(zrec[momkey])
                first_Z.append([temp,dec,inc,str,ZI])
        # sort out first_I records 
                idec=float(irec["measurement_dec"])
                iinc=float(irec["measurement_inc"])
                istr=float(irec[momkey])
                X=pmag.dir2cart([idec,iinc,istr])
                BL=pmag.dir2cart([dec,inc,str])
                I=[]
                for c in range(3): I.append((X[c]-BL[c]))
                if I[2]!=0:
                    iDir=pmag.cart2dir(I)
                    if Zdiff==0:
                        first_I.append([temp,iDir[0],iDir[1],iDir[2],ZI])
                    else:
                        first_I.append([temp,0.,0.,I[2],ZI])
##                    gamma=angle([iDir[0],iDir[1]],[phi,theta])
                else:
                    first_I.append([temp,0.,0.,0.,ZI])
##                    gamma=0.0
##    # put in Gamma check (infield trm versus lab field)
##                if 180.-gamma<gamma:
##                    gamma=180.-gamma
##                GammaChecks.append([temp-273.,gamma])


        #---------------------
        # find Thellier Thellier protocol
        #---------------------
        if 'LP-PI-II'in methcodes or 'LP-PI-T-II' in methcodes or 'LP-PI-M-II' in methcodes:
            for i in range(1,len(Treat_I)): # look through infield steps and find matching Z step
                if Treat_I[i] == Treat_I[i-1]:
                    # ignore, if there are more than 
                    temp= Treat_I[i]
                    irec1=datablock[ISteps[i-1]]
                    dec1=float(irec1["measurement_dec"])
                    inc1=float(irec1["measurement_inc"])
                    moment1=float(irec1["measurement_magn_moment"])
                    if len(first_I)<2:
                        dec_initial=dec1;inc_initial=inc1
                    cart1=scipy.array(pmag.dir2cart([dec1,inc1,moment1]))
                    irec2=datablock[ISteps[i]]
                    dec2=float(irec2["measurement_dec"])
                    inc2=float(irec2["measurement_inc"])
                    moment2=float(irec2["measurement_magn_moment"])
                    cart2=scipy.array(pmag.dir2cart([dec2,inc2,moment2]))

                    # check if its in the same treatment
                    if Treat_I[i] == Treat_I[i-2] and dec2!=dec_initial and inc2!=inc_initial:
                        continue
                    if dec1!=dec2 and inc1!=inc2:
                        zerofield=(cart2+cart1)/2
                        infield=(cart2-cart1)/2

                        DIR_zerofield=pmag.cart2dir(zerofield)
                        DIR_infield=pmag.cart2dir(infield)

                        first_Z.append([temp,DIR_zerofield[0],DIR_zerofield[1],DIR_zerofield[2],0])
                        first_I.append([temp,DIR_infield[0],DIR_infield[1],DIR_infield[2],0])
                

        #---------------------
        # find  pTRM checks
        #---------------------
                    
        for i in range(len(Treat_PI)): # look through infield steps and find matching Z step

            temp=Treat_PI[i]
            k=PISteps[i]   
            rec=datablock[k]
            dec=float(rec["measurement_dec"])
            inc=float(rec["measurement_inc"])
            moment=float(rec["measurement_magn_moment"])
            phi=float(rec["treatment_dc_field_phi"])
            theta=float(rec["treatment_dc_field_theta"])
            M=scipy.array(pmag.dir2cart([dec,inc,moment]))

            foundit=False
            if 'LP-PI-II' not in methcodes:
                 # Important: suport several pTRM checks in a row, but
                 # does not support pTRM checks after infield step
                 for j in range(k,1,-1):
                     if "LT-M-I" in datablock[j]['magic_method_codes'] or "LT-T-I" in datablock[j]['magic_method_codes']:
                         after_zerofield=0. 
                         foundit=True
                         prev_rec=datablock[j]
                         zerofield_index=j  
                         break                       
                     if float(datablock[j]['treatment_dc_field'])==0:
                         after_zerofield=1.
                         foundit=True
                         prev_rec=datablock[j]
                         zerofield_index=j
                         break
            else: # Thellier-Thellier protocol
                foundit=True
                prev_rec=datablock[k-1]
                zerofield_index=k-1
            
            if foundit:                            
                prev_dec=float(prev_rec["measurement_dec"])
                prev_inc=float(prev_rec["measurement_inc"])
                prev_moment=float(prev_rec["measurement_magn_moment"])
                prev_phi=float(prev_rec["treatment_dc_field_phi"])
                prev_theta=float(prev_rec["treatment_dc_field_theta"])
                prev_M=scipy.array(pmag.dir2cart([prev_dec,prev_inc,prev_moment]))
            
                if  'LP-PI-II' not in methcodes:   
                    diff_cart=M-prev_M
                    diff_dir=pmag.cart2dir(diff_cart)
                    if after_zerofield==0:
                        ptrm_check.append([temp,diff_dir[0],diff_dir[1],diff_dir[2],zerofield_index,after_zerofield])
                    else:
                        ptrm_check.append([temp,diff_dir[0],diff_dir[1],diff_dir[2],zerofield_index,after_zerofield])
                else:           
                    # health check for T-T protocol:
                    if theta!=prev_theta:
                        diff=(M-prev_M)/2
                        diff_dir=pmag.cart2dir(diff)
                        ptrm_check.append([temp,diff_dir[0],diff_dir[1],diff_dir[2],zerofield_index,""])
                    else:
                        print "-W- WARNING: specimen. pTRM check not in place in Thellier Thellier protocol. step please check"
                
                        
                        
                        


        #---------------------
        # find Tail checks
        #---------------------
                    

        for temp in Treat_M:
            #print temp
            step=MSteps[Treat_M.index(temp)]
            rec=datablock[step]
            dec=float(rec["measurement_dec"])
            inc=float(rec["measurement_inc"])
            moment=float(rec["measurement_magn_moment"])
            foundit=False
            for i in range(1,len(datablock)):
                if 'LT-T-Z' in datablock[i]['magic_method_codes'] or 'LT-M-Z' in datablock[i]['magic_method_codes'] :
                    if (THERMAL and "treatment_temp" in datablock[i].keys() and float(datablock[i]["treatment_temp"])==float(temp) )\
                       or (MICROWAVE and "measurement_description" in datablock[i].keys() and "Step Number-%.0f"%float(temp) in datablock[i]["measurement_description"]):
                        prev_rec=datablock[i]
                        prev_dec=float(prev_rec["measurement_dec"])
                        prev_inc=float(prev_rec["measurement_inc"])
                        prev_moment=float(prev_rec["measurement_magn_moment"])
                        foundit=True
                        break

            if foundit:
                    ptrm_tail.append([temp,0,0,moment-prev_moment])
                    
        #print ptrm_tail
    #
    # final check
    #
        if len(first_Z)!=len(first_I):
                   print len(first_Z),len(first_I)
                   print " Something wrong with this specimen! Better fix it or delete it "
                   raw_input(" press return to acknowledge message")


        #---------------------
        # find  Additivity (patch by rshaar)
        #---------------------
                    
        additivity_check=[]
        for i in range(len(Treat_AC)):
            step_0=ACSteps[i]
            temp=Treat_AC[i]
            dec0=float(datablock[step_0]["measurement_dec"])
            inc0=float(datablock[step_0]["measurement_inc"])
            moment0=float(datablock[step_0]['measurement_magn_moment'])
            V0=pmag.dir2cart([dec0,inc0,moment0])
            # find the infield step that comes before the additivity check
            foundit=False
            for j in range(step_0,1,-1):
                if "LT-T-I" in datablock[j]['magic_method_codes']:
                  foundit=True ; break
            if foundit:
                dec1=float(datablock[j]["measurement_dec"])
                inc1=float(datablock[j]["measurement_inc"])
                moment1=float(datablock[j]['measurement_magn_moment'])
                V1=pmag.dir2cart([dec1,inc1,moment1])
                #print "additivity check: ",s
                #print j
                #print "ACC=V1-V0:"
                #print "V1=",[dec1,inc1,moment1],pmag.dir2cart([dec1,inc1,moment1])/float(datablock[0]["measurement_magn_moment"])
                #print "V1=",pmag.dir2cart([dec1,inc1,moment1])/float(datablock[0]["measurement_magn_moment"])
                #print "V0=",[dec0,inc0,moment0],pmag.dir2cart([dec0,inc0,moment0])/float(datablock[0]["measurement_magn_moment"])
                #print "NRM=",float(datablock[0]["measurement_magn_moment"])
                #print "-------"
                
                I=[]
                for c in range(3): I.append(V1[c]-V0[c])
                dir1=pmag.cart2dir(I)
                additivity_check.append([temp,dir1[0],dir1[1],dir1[2]])
                #print "I",scipy.array(I)/float(datablock[0]["measurement_magn_moment"]),dir1,"(dir1 unnormalized)"
                X=scipy.array(I)/float(datablock[0]["measurement_magn_moment"])
                #print "I",scipy.sqrt(sum(X**2))
        araiblock=(first_Z,first_I,ptrm_check,ptrm_tail,zptrm_check,GammaChecks,additivity_check)

        return araiblock,field



            
    
#--------------------------------------------------------------    
# Run the GUI
#--------------------------------------------------------------




def main(WD=None, standalone_app=True, parent=None):
    # to run as module, i.e. with Pmag GUI:
    if not standalone_app:
        wait = wx.BusyInfo('Compiling required data, please wait...')
        wx.Yield()
        frame = Arai_GUI(WD, parent, standalone=False)
        frame.Centre()
        frame.Show()
        del wait
        
    # to run as command line:
    else:
        app = wx.App(redirect=False)#, #filename='py2app_log.log')
        app.frame = Arai_GUI(WD)
        app.frame.Show()
        app.frame.Center()
        app.MainLoop()

    ## use for debugging:
    #if '-i' in sys.argv:
    #    import wx.lib.inspection
    #    wx.lib.inspection.InspectionTool().Show()
        

if __name__ == '__main__':
    main()


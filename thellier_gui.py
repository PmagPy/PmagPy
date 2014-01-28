#!/usr/bin/env python

#============================================================================================
# LOG HEADER:
#============================================================================================
# Thellier_GUI Version 2.11 01/13/2014
# adjust diplay to automatically fit screen size

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
#
#-------------------------
#
# Thellier_GUI Version 2.00
# Author: Ron Shaar
# Citation: Shaar and Tauxe (2013)
#
# January 2012: Initial revision
# To do list:
# 1) calculate MD tail check
#
#
#============================================================================================

global CURRENT_VRSION
CURRENT_VRSION = "v.2.11"
import matplotlib
matplotlib.use('WXAgg')

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas \

import sys,pylab,scipy,os
import pmag
##try:
##    import pmag
##except:
##    pass
try:
    import thellier_gui_preferences
except:
    pass
import stat
import subprocess
import time
import wx
import wx.grid
import random
from pylab import *
from scipy.optimize import curve_fit
import wx.lib.agw.floatspin as FS
try:
    from mpl_toolkits.basemap import Basemap, shiftgrid
except:
    pass

from matplotlib.backends.backend_wx import NavigationToolbar2Wx

import thellier_consistency_test
import copy
from copy import deepcopy

matplotlib.rc('xtick', labelsize=10) 
matplotlib.rc('ytick', labelsize=10) 
matplotlib.rc('axes', labelsize=8) 
matplotlib.rcParams['savefig.dpi'] = 300.

rcParams.update({"svg.embed_char_paths":False})
rcParams.update({"svg.fonttype":'none'})



#============================================================================================



    
class Arai_GUI(wx.Frame):
    """ The main frame of the application
    """
    title = "PmagPy Thellier GUI %s"%CURRENT_VRSION
    
    def __init__(self):

        global FIRST_RUN
        FIRST_RUN=True
        wx.Frame.__init__(self, None, wx.ID_ANY, self.title)
        self.redo_specimens={}
        self.currentDirectory = os.getcwd() # get the current working directory
        self.get_DIR()        # choose directory dialog        
        accept_new_parameters_default,accept_new_parameters_null=self.get_default_criteria()    # inialize Null selecting criteria
        self.accept_new_parameters_null=accept_new_parameters_null
        self.accept_new_parameters_default=accept_new_parameters_default
        #self.accept_new_parameters=copy.deepcopy(accept_new_parameters_default)
        preferences=self.get_preferences()
        self.dpi = 100
        
        self.preferences=preferences
        # inialize selecting criteria
        accept_new_parameters=self.read_criteria_from_file(self.WD+"/pmag_criteria.txt")          
        self.accept_new_parameters=accept_new_parameters
        #self.accept_new_parameters=accept_new_parameters
        self.Data,self.Data_hierarchy,self.Data_info={},{},{}
        self.MagIC_directories_list=[]

        self.Data_info=self.get_data_info() # get all ages, locations etc. (from er_ages, er_sites, er_locations)
        self.Data,self.Data_hierarchy=self.get_data() # Get data from magic_measurements and rmag_anistropy if exist.

        if  "-tree" in sys.argv and FIRST_RUN:
            self.open_magic_tree()

        self.Data_samples={} # interpretations of samples are kept here
        self.Data_sites={}   # interpretations of sites are kept here

        self.last_saved_pars={}
        self.specimens=self.Data.keys()         # get list of specimens
        self.specimens.sort()                   # get list of specimens
        self.panel = wx.Panel(self)          # make the Panel
        self.Main_Frame()                   # build the main frame
        self.create_menu()                  # create manu bar
        self.Arai_zoom()
        self.Zij_zoom()
        self.arrow_keys()

        self.get_previous_interpretation() # get interpretations from pmag_specimens.txt
        FIRST_RUN=False
        
    def get_DIR(self):
        """ Choose a working directory dialog
        """
        if "-WD" in sys.argv and FIRST_RUN:
            ind=sys.argv.index('-WD')
            self.WD=sys.argv[ind+1] 
##        elif "-tree" in sys.argv and first_run:
##            print "Ron"
##            ind=sys.argv.index('-tree')
##            self.WD=sys.argv[ind+1]
##            self.on_menu_m_open_magic_tree("here")
##            self.GUI_log=open("%s/Thellier_GUI.log"%self.WD,'w')
##            return
        else:   
            dialog = wx.DirDialog(None, "Choose a directory:",defaultPath = self.currentDirectory ,style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON | wx.DD_CHANGE_DIR)
            if dialog.ShowModal() == wx.ID_OK:
              self.WD=dialog.GetPath()
            dialog.Destroy()
        self.magic_file=self.WD+"/"+"magic_measurements.txt"
            #intialize GUI_log
        self.GUI_log=open("%s/thellier_GUI.log"%self.WD,'w')
        #self.GUI_log=open("%s/Thellier_GUI.log"%self.WD,'a')
        
##    def add_toolbar(self):
##        self.toolbar = NavigationToolbar2Wx(self.canvas1)
##        
##        self.toolbar.Realize()
##        if wx.Platform == '__WXMAC__':
##            # Mac platform (OSX 10.3, MacPython) does not seem to cope with
##            # having a toolbar in a sizer. This work-around gets the buttons
##            # back, but at the expense of having the toolbar at the top
##            self.SetToolBar(self.toolbar)
##        else:
##            # On Windows platform, default window size is incorrect, so set
##            # toolbar width to figure width.
##            tw, th = self.toolbar.GetSizeTuple()
##            fw, fh = self.canvas.GetSizeTuple()
##            # By adding toolbar in sizer, we are able to put it at the bottom
##            # of the frame - so appearance is closer to GTK version.
##            # As noted above, doesn't work for Mac.
##            self.toolbar.SetSize(wx.Size(fw, th))
##            self.sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
##        # update the axes menu on the toolbar
##        self.toolbar.update()

    def Main_Frame(self):
        """ Build main frame od panel: buttons, etc.
            choose the first specimen and display data
        """

        dw, dh = wx.DisplaySize() 
        w, h = self.GetSize()
        #print 'diplay', dw, dh
        #print "gui", w, h
        r1=dw/1250.
        r2=dw/750.
        
        #if  dw>w:
        self.GUI_RESOLUTION=min(r1,r2,1.3)

        #self.GUI_RESOLUTION=0.75
        #self.GUI_RESOLUTION=float(self.preferences['gui_resolution'])/100
        
        #----------------------------------------------------------------------                     
        # Create the mpl Figure and FigCanvas objects. 
        # 5x4 inches, 100 dots-per-inch
        #----------------------------------------------------------------------                     
        #
        self.fig1 = Figure((5.*self.GUI_RESOLUTION, 5.*self.GUI_RESOLUTION), dpi=self.dpi)
        self.canvas1 = FigCanvas(self.panel, -1, self.fig1)
        self.fig1.text(0.01,0.98,"Arai plot",{'family':'Arial', 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })
        
        self.fig2 = Figure((2.5*self.GUI_RESOLUTION, 2.5*self.GUI_RESOLUTION), dpi=self.dpi)
        self.canvas2 = FigCanvas(self.panel, -1, self.fig2)
        self.fig2.text(0.02,0.96,"Zijderveld",{'family':'Arial', 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })

        self.fig3 = Figure((2.5*self.GUI_RESOLUTION, 2.5*self.GUI_RESOLUTION), dpi=self.dpi)
        self.canvas3 = FigCanvas(self.panel, -1, self.fig3)
        #self.fig3.text(0.02,0.96,"Equal area",{'family':'Arial', 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })

        self.fig4 = Figure((2.5*self.GUI_RESOLUTION, 2.5*self.GUI_RESOLUTION), dpi=self.dpi)
        self.canvas4 = FigCanvas(self.panel, -1, self.fig4)
        self.fig4.text(0.02,0.96,"Sample data",{'family':'Arial', 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })

        self.fig5 = Figure((2.5*self.GUI_RESOLUTION, 2.5*self.GUI_RESOLUTION), dpi=self.dpi)
        self.canvas5 = FigCanvas(self.panel, -1, self.fig5)
        #self.fig5.text(0.02,0.96,"M/M0",{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'left' })

        # make axes of the figures
        self.araiplot = self.fig1.add_axes([0.1,0.1,0.8,0.8])
        self.zijplot = self.fig2.add_subplot(111)
        self.eqplot = self.fig3.add_subplot(111)
        self.sampleplot = self.fig4.add_axes([0.2,0.3,0.7,0.6],frameon=True,axisbg='None')
        self.mplot = self.fig5.add_axes([0.2,0.15,0.7,0.7],frameon=True,axisbg='None')


        #----------------------------------------------------------------------                     
        # bottons, lists, boxes, and features
        #----------------------------------------------------------------------                     

        #wx.StaticBox(self.panel, -1, 'select specimen', (5, 10), size=(160, 107))
        #select_specimen_box = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "select specimen" ), wx.HORIZONTAL )
        #wx.StaticBox(self.panel, -1, 'select temperature bounds', (170, 10), size=(260, 107))
        #select_temperature_box = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "select temperature bounds" ), wx.HORIZONTAL )

        # initialize first specimen in list as current specimen
        try:
            self.s=self.specimens[0]
        except:
            self.s=""


        # set font size and style
        #font1 = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Comic Sans MS')
        FONT_RATIO=self.GUI_RESOLUTION+(self.GUI_RESOLUTION-1)*5
        font1 = wx.Font(9+FONT_RATIO, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Arial')
        # GUI headers
        font2 = wx.Font(12+min(1,FONT_RATIO), wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Arial')
        font3 = wx.Font(11+FONT_RATIO, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Arial')
        font = wx.SystemSettings_GetFont(wx.SYS_SYSTEM_FONT)
        font.SetPointSize(10+FONT_RATIO)        
##        font1 = wx.SystemSettings_GetFont(wx.SYS_SYSTEM_FONT)
##        font1.SetPointSize(max(8,9*self.GUI_RESOLUTION))
##        font2 = wx.SystemSettings_GetFont(wx.SYS_SYSTEM_FONT)
##        font2.SetPointSize(14*self.GUI_RESOLUTION)
##        font3 = wx.SystemSettings_GetFont(wx.SYS_SYSTEM_FONT)
##        font3.SetPointSize(10*self.GUI_RESOLUTION)
           

        # text_box for presenting the measurements
        self.logger = wx.TextCtrl(self.panel, id=-1, size=(200*self.GUI_RESOLUTION,500*self.GUI_RESOLUTION), style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
        self.logger.SetFont(font1)
        



        #   ---------------------------  
        #  select specimen box

        box_sizer_select_specimen = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY,"specimen" ), wx.VERTICAL )

        # Combo-box with a list of specimen
        #self.specimens_box_label = wx.StaticText(self.panel, label=" ")
        self.specimens_box = wx.ComboBox(self.panel, -1, self.s, (250*self.GUI_RESOLUTION, 25), wx.DefaultSize,self.specimens, wx.CB_DROPDOWN,name="specimen")
        self.specimens_box.SetFont(font2)
        self.Bind(wx.EVT_TEXT, self.onSelect_specimen,self.specimens_box)
        
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

        #box_sizer_select_specimen.Add(self.specimens_box, 0, wx.TOP, 0 )        
        #box_sizer_select_specimen.Add(select_specimen_window, 0, wx.TOP, 0 )        




        #   ---------------------------  
        #  select temperatures box

        if  self.s in self.Data.keys() and self.Data[self.s]['T_or_MW']=="T": 
            box_sizer_select_temp = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY,"temperatures" ), wx.HORIZONTAL )
        else: 
            box_sizer_select_temp = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY,"MW power" ), wx.HORIZONTAL )

        try:
            if  self.Data[self.s]['T_or_MW']=="T": 
                self.temperatures=array(self.Data[self.s]['t_Arai'])-273.
                self.T_list=["%.0f"%T for T in self.temperatures]
            elif  self.Data[self.s]['T_or_MW']=="MW":
                self.temperatures=array(self.Data[self.s]['t_Arai'])
                self.T_list=["%.0f"%T for T in self.temperatures]
        except:
            self.T_list=[]
        
        self.tmin_box = wx.ComboBox(self.panel, -1 ,size=(100*self.GUI_RESOLUTION, 25),choices=self.T_list, style=wx.CB_DROPDOWN)
        self.tmin_box.SetFont(font2)
        self.Bind(wx.EVT_COMBOBOX, self.get_new_T_PI_parameters,self.tmin_box)

        self.tmax_box = wx.ComboBox(self.panel, -1 ,size=(100*self.GUI_RESOLUTION, 25),choices=self.T_list, style=wx.CB_DROPDOWN)
        self.Bind(wx.EVT_COMBOBOX, self.get_new_T_PI_parameters,self.tmax_box)

        select_temp_window = wx.GridSizer(3, 1, 12, 10*self.GUI_RESOLUTION)
        select_temp_window.AddMany( [(self.tmin_box, wx.ALIGN_LEFT),
            (self.tmax_box, wx.ALIGN_LEFT)])
        box_sizer_select_temp.Add(select_temp_window, 0, wx.TOP, 0 )        


        #   ---------------------------     

        #  save/delete box

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


        #   ---------------------------  
        # Specimen interpretation window (Blab; Banc, Dec, Inc, correction factors etc.)

        
        self.Blab_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50*self.GUI_RESOLUTION,25))
        self.Blab_window.SetFont(font2)
        self.Banc_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50*self.GUI_RESOLUTION,25))
        self.Banc_window.SetFont(font2)        
        self.Aniso_factor_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50*self.GUI_RESOLUTION,25))
        self.Aniso_factor_window.SetFont(font2) 
        self.NLT_factor_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50*self.GUI_RESOLUTION,25))
        self.NLT_factor_window.SetFont(font2) 
        self.CR_factor_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50*self.GUI_RESOLUTION,25))
        self.CR_factor_window.SetFont(font2) 
        self.declination_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50*self.GUI_RESOLUTION,25))
        self.declination_window.SetFont(font2) 
        self.inclination_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50*self.GUI_RESOLUTION,25))
        self.inclination_window.SetFont(font2) 

        self.Blab_label=wx.StaticText(self.panel,label="\nB_lab",style=wx.ALIGN_CENTRE)
        self.Blab_label.SetFont(font2)
        self.Banc_label=wx.StaticText(self.panel,label="\nB_anc",style=wx.ALIGN_CENTRE)
        self.Banc_label.SetFont(font2)
        self.aniso_corr_label=wx.StaticText(self.panel,label="Aniso\ncorrection",style=wx.ALIGN_CENTRE)
        self.aniso_corr_label.SetFont(font2)
        self.nlt_corr_label=wx.StaticText(self.panel,label="NLT\ncorrection",style=wx.ALIGN_CENTRE)
        self.nlt_corr_label.SetFont(font2)
        self.cr_corr_label=wx.StaticText(self.panel,label="CR\ncorrection",style=wx.ALIGN_CENTRE)
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



        #   ---------------------------  
        #  Sample interpretation window 

        # Sample interpretation window (sample_int_n, sample_int_sigma, sample_int_sigma_perc)

        for key in ["sample_int_n","sample_int_uT","sample_int_sigma","sample_int_sigma_perc"]:
            command="self.%s_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50*self.GUI_RESOLUTION,25))"%key
            exec command
            command = "self.%s_window.SetFont(font2)"%key
            exec command

##        for key in ["sample results","\nmean","\nN","\n std uT","\n std uT"]:
##            K=key.strip("\n");K=K.replace(" ", "_")
##            command="%s_label=wx.StaticBox( self.panel, wx.ID_ANY,'%s',style=wx.TE_CENTER )"%(K,key)
##            print command
##            exec command
##            command="%s_label.SetFont(font3)"%K
##            exec command

        sample_mean_label=wx.StaticText(self.panel,label="\nmean",style=wx.TE_CENTER)
        sample_mean_label.SetFont(font2)
        sample_N_label=wx.StaticText(self.panel,label="\nN ",style=wx.TE_CENTER)
        sample_N_label.SetFont(font2)
        sample_std_label=wx.StaticText(self.panel,label="\n std uT",style=wx.TE_CENTER)
        sample_std_label.SetFont(font2)
        sample_std_per_label=wx.StaticText(self.panel,label="\n std %",style=wx.TE_CENTER)
        sample_std_per_label.SetFont(font2)

        
        sample_stat_window = wx.GridSizer(2, 4, 0, 20*self.GUI_RESOLUTION)


        box_sizer_sample = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY,"sample results" ), wx.HORIZONTAL )
        sample_stat_window.AddMany( [(sample_mean_label, wx.EXPAND),
            (sample_N_label, wx.EXPAND),
            (sample_std_label, wx.EXPAND),
            (sample_std_per_label ,wx.EXPAND),
            (self.sample_int_uT_window, wx.EXPAND),
            (self.sample_int_n_window, wx.EXPAND) ,
            (self.sample_int_sigma_window, wx.EXPAND) ,
            (self.sample_int_sigma_perc_window, wx.EXPAND)])
        box_sizer_sample.Add(sample_stat_window, 0, wx.ALIGN_LEFT, 0 )        





        #   ---------------------------  

        # Specimen paleointensity statistics


        # Specimen statistcis window 
        try:
            if 'specimen_frac' not in self.Data[self.s]['pars'].keys():
              specimen_frac=""
            else:
              specimen_frac="%.2f"%self.Data[self.s]['pars']['specimen_frac']
        except:
            pass

        #self.preferences['show_statistics_on_gui']=["int_n","int_ptrm_n","frac","scat","gmax","b_beta","int_mad","dang","f","fvds","g","q","drats","md"]
        #preperences['show_statistics_on_gui']=["int_n","ptrm_n","frac","scat","gmax","beta","int_mad","dang"]
        Statsitics_labels={}
        Statsitics_labels["int_n"]="n"
        Statsitics_labels["int_ptrm_n"]="n_ptrm"
        Statsitics_labels["frac"]="FRAC"
        Statsitics_labels["scat"]="SCAT"
        Statsitics_labels["gmax"]="GAP-MAX"
        Statsitics_labels["b_beta"]="beta"
        Statsitics_labels["int_mad"]="MAD"
        Statsitics_labels["dang"]="DANG"
        Statsitics_labels["f"]="f"
        Statsitics_labels["fvds"]="fvds"
        Statsitics_labels["g"]="g"
        Statsitics_labels["q"]="q"
        Statsitics_labels["drats"]="DRATS"
        Statsitics_labels["md"]="MD"
        Statsitics_labels["ptrms_inc"]="pTRMs_inc"
        Statsitics_labels["ptrms_dec"]="pTRMs_dec"
        Statsitics_labels["ptrms_mad"]="pTRMs_MAD"
        Statsitics_labels["ptrms_angle"]="pTRMs_angle"

        hbox_criteria = wx.BoxSizer(wx.HORIZONTAL)
        TEXT=[" ","Acceptance criteria:","Specimen statistics:"]
        for i in range(len(TEXT)):
            command="self.label_%i=wx.StaticText(self.panel,label='%s',style=wx.ALIGN_CENTER,size=(180,25))"%(i,TEXT[i])
            #print command
            exec command
            command="self.label_%i.SetFont(font3)"%i
            #print command
            exec command
        gs1 = wx.GridSizer(3, 1,5*self.GUI_RESOLUTION,5*self.GUI_RESOLUTION)
 
        gs1.AddMany( [(self.label_0,wx.EXPAND),(self.label_1,wx.EXPAND),(self.label_2,wx.EXPAND)])
        

                                     
##            command="gs1.AddMany( [(self.%s_label,wx.EXPAND),(self.%s_threshold_window,wx.EXPAND),(self.%s_window,wx.EXPAND)])"%(statistic,statistic,statistic,statistic)
##            exec command
##            command="hbox_criteria.Add(gs_%s,flag=wx.ALIGN_LEFT)"%statistic
##            exec command
##        hbox_criteria.AddSpacer(12)


##        gs1 = wx.GridSizer(3, 1,5*self.GUI_RESOLUTION,5*self.GUI_RESOLUTION)
##        gs1.AddMany( [(wx.StaticText(self.panel,label="",style=wx.ALIGN_CENTER,size=(180,25)),wx.EXPAND),
##            (wx.StaticText(self.panel,label="Acceptance criteria:",style=wx.ALIGN_CENTER,size=(180,25)),wx.EXPAND),
##            (wx.StaticText(self.panel,label="Specimen's statistics:",style=wx.ALIGN_CENTER,size=(180,25)),wx.EXPAND)])
        hbox_criteria.Add(gs1,flag=wx.ALIGN_LEFT)

        for statistic in self.preferences['show_statistics_on_gui']:
            command="self.%s_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50*self.GUI_RESOLUTION,25))"%statistic
            exec command
            command="self.%s_window.SetFont(font3)"%statistic
            exec command
            command="self.%s_threshold_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50*self.GUI_RESOLUTION,25))"%statistic
            exec command
            command="self.%s_threshold_window.SetFont(font3)"%statistic
            exec command
            command="self.%s_threshold_window.SetBackgroundColour(wx.NullColour)"%statistic
            exec command
            command="self.%s_label=wx.StaticText(self.panel,label='%s',style=wx.ALIGN_CENTRE)"%(statistic,Statsitics_labels[statistic])
            exec command
            command="self.%s_label.SetFont(font3)"%statistic
            exec command
            
        for statistic in self.preferences['show_statistics_on_gui']:
            command="gs_%s = wx.GridSizer(3, 1,5*self.GUI_RESOLUTION,5*self.GUI_RESOLUTION)"%statistic
            exec command
            command="gs_%s.AddMany( [(self.%s_label,wx.EXPAND),(self.%s_threshold_window,wx.EXPAND),(self.%s_window,wx.EXPAND)])"%(statistic,statistic,statistic,statistic)
            exec command
            command="hbox_criteria.Add(gs_%s,flag=wx.ALIGN_LEFT)"%statistic
            exec command
            hbox_criteria.AddSpacer(12)
           
        #for statistic in self.preperences['show_statistics_on_gui']
            
##        self.int_n_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50,20))
##        self.int_ptrm_n_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50,20))
##        self.frac_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50,20))
##        self.scat_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
##        self.gmax_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
##        self.f_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
##        self.fds_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
##        self.b_beta_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
##        self.g_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
##        self.q_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
##        self.int_mad_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
##        self.dang_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
##        self.drats_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
##        self.md_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
##
##        self.int_n_threshold_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50,20))
##        self.int_ptrm_n_threshold_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50,20))
##        self.frac_threshold_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50,20))
##        self.scat_threshold_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50,20))
##        self.gmax_threshold_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
##        self.f_threshold_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
##        self.fvds_threshold_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
##        self.b_beta_threshold_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
##        self.g_threshold_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
##        self.q_threshold_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
##        self.int_mad_threshold_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
##        self.dang_threshold_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
##        self.drats_threshold_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
##        self.md_threshold_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))

##        self.int_n_threshold_window.SetBackgroundColour(wx.NullColour)
##        self.int_ptrm_n_threshold_window.SetBackgroundColour(wx.NullColour)
##        self.frac_threshold_window.SetBackgroundColour(wx.NullColour)
##        self.scat_threshold_window.SetBackgroundColour(wx.NullColour)
##        self.gmax_threshold_window.SetBackgroundColour(wx.NullColour)
##        self.f_threshold_window.SetBackgroundColour(wx.NullColour)
##        self.fvds_threshold_window.SetBackgroundColour(wx.NullColour)
##        self.b_beta_threshold_window.SetBackgroundColour(wx.NullColour)
##        self.g_threshold_window.SetBackgroundColour(wx.NullColour)
##        self.q_threshold_window.SetBackgroundColour(wx.NullColour)
##        self.int_mad_threshold_window.SetBackgroundColour(wx.NullColour)
##        self.dang_threshold_window.SetBackgroundColour(wx.NullColour)
##        self.drats_threshold_window.SetBackgroundColour(wx.NullColour)
##        self.md_threshold_window.SetBackgroundColour(wx.NullColour)

##        gs = wx.GridSizer(3, 14, 14, 14)

##        gs=wx.GridSizer(3, len(self.preperences['show_statistics_on_gui']), 14, 14)
##        gs.AddMany( [(wx.StaticText(self.panel,label="int_n",style=wx.ALIGN_CENTER_VERTICAL),wx.ALIGN_CENTER_VERTICAL),
##            (wx.StaticText(self.panel,label="n_pTRM",style=wx.ALIGN_CENTER_VERTICAL),wx.ALIGN_CENTER_VERTICAL),
##            (wx.StaticText(self.panel,label="FRAC",style=wx.ALIGN_CENTER_VERTICAL),wx.ALIGN_CENTER_VERTICAL),
##            (wx.StaticText(self.panel,label="SCAT",style=wx.ALIGN_CENTER_VERTICAL),wx.ALIGN_CENTER_VERTICAL),
##            (wx.StaticText(self.panel,label="gmax",style=wx.ALIGN_CENTER_VERTICAL),wx.ALIGN_CENTER_VERTICAL),
##            (wx.StaticText(self.panel,label="f",style=wx.ALIGN_CENTER_VERTICAL),wx.ALIGN_CENTER_VERTICAL),
##            (wx.StaticText(self.panel,label="fvds",style=wx.ALIGN_CENTER_VERTICAL),wx.ALIGN_CENTER_VERTICAL),
##            (wx.StaticText(self.panel,label="beta",style=wx.ALIGN_CENTER_VERTICAL),wx.ALIGN_CENTER_VERTICAL),
##            (wx.StaticText(self.panel,label="g",style=wx.ALIGN_CENTER_VERTICAL),wx.ALIGN_CENTER_VERTICAL),
##            (wx.StaticText(self.panel,label="q",style=wx.ALIGN_CENTER_VERTICAL),wx.ALIGN_CENTER_VERTICAL),
##            (wx.StaticText(self.panel,label="MAD",style=wx.ALIGN_CENTER_VERTICAL)),
##            (wx.StaticText(self.panel,label="DANG",style=wx.ALIGN_CENTER_VERTICAL)),
##            (wx.StaticText(self.panel,label="DRATS",style=wx.ALIGN_CENTER_VERTICAL)),
##            (wx.StaticText(self.panel,label="MD tail",style=wx.ALIGN_CENTER_VERTICAL)),
##            (self.int_n_threshold_window, wx.EXPAND),
##            (self.int_ptrm_n_threshold_window, wx.EXPAND),                     
##            (self.frac_threshold_window, wx.EXPAND),
##            (self.scat_threshold_window, wx.EXPAND),
##            (self.gmax_threshold_window, wx.EXPAND),
##            (self.f_threshold_window, wx.EXPAND),
##            (self.fvds_threshold_window, wx.EXPAND),
##            (self.b_beta_threshold_window, wx.EXPAND),
##            (self.g_threshold_window, wx.EXPAND),
##            (self.q_threshold_window, wx.EXPAND),
##            (self.int_mad_threshold_window, wx.EXPAND),
##            (self.dang_threshold_window, wx.EXPAND),
##            (self.drats_threshold_window, wx.EXPAND),
##            (self.md_threshold_window, wx.EXPAND),
##            (self.int_n_window, wx.EXPAND),
##            (self.int_ptrm_n_window, wx.EXPAND),
##            (self.frac_window, wx.EXPAND),
##            (self.scat_window, wx.EXPAND),
##            (self.gmax_window, wx.EXPAND),
##            (self.f_window, wx.EXPAND),
##            (self.fvds_window, wx.EXPAND),
##            (self.b_beta_window, wx.EXPAND),
##            (self.g_window, wx.EXPAND),
##            (self.q_window, wx.EXPAND),
##            (self.int_mad_window, wx.EXPAND),
##            (self.dang_window, wx.EXPAND),
##            (self.drats_window, wx.EXPAND),
##            (self.md_window, wx.EXPAND)])
##
##
##        gs1 = wx.GridSizer(3, 1,12*self.GUI_RESOLUTION,12*self.GUI_RESOLUTION)
##        gs1.AddMany( [(wx.StaticText(self.panel,label="",style=wx.ALIGN_CENTER)),
##            (wx.StaticText(self.panel,label="Acceptance criteria:",style=wx.ALIGN_CENTER)),
##            (wx.StaticText(self.panel,label="Specimen's statistics:",style=wx.ALIGN_CENTER))])
        
        self.write_acceptance_criteria_to_boxes()  # write threshold values to boxes

        
        #----------------------------------------------------------------------                     
        # Design the panel
        #----------------------------------------------------------------------

        
        vbox1 = wx.BoxSizer(wx.VERTICAL)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)

        #hbox1a= wx.BoxSizer(wx.HORIZONTAL)
        #hbox1b= wx.BoxSizer(wx.HORIZONTAL)
        #vbox1a=wx.BoxSizer(wx.VERTICAL)

        #hbox1c= wx.BoxSizer(wx.HORIZONTAL)
##        hbox1d= wx.BoxSizer(wx.HORIZONTAL)
##        vbox1b=wx.BoxSizer(wx.VERTICAL)
        
        #hbox1a.Add(self.specimens_box_label, flag=wx.ALIGN_CENTER_VERTICAL,border=2)
        #hbox1a.Add(self.specimens_box, flag=wx.ALIGN_CENTER_VERTICAL | wx.GROW)#, border=10)
        #hbox1b.Add(self.prevbutton,flag=wx.ALIGN_CENTER_VERTICAL)#, border=8)
        #hbox1b.Add(self.nextbutton, flag=wx.ALIGN_CENTER_VERTICAL)#, border=10)
        #vbox1a.Add(hbox1a,flag=wx.ALIGN_RIGHT)
        #vbox1a.AddSpacer(10)
        #vbox1a.Add(hbox1b,flag=wx.ALIGN_RIGHT)
        #select_specimen_box.Add(vbox1a)

##        hbox1c.Add(self.tmin_box_label, flag=wx.ALIGN_CENTER_VERTICAL,border=2)
##        hbox1c.Add(self.tmin_box, flag=wx.ALIGN_CENTER_VERTICAL)#, border=10)
##
##        hbox1c.AddSpacer(10)
##        hbox1c.Add(self.save_interpretation_button,flag=wx.ALIGN_CENTER_VERTICAL)#, border=8)
##
##        hbox1d.Add(self.tmax_box_label,flag=wx.ALIGN_CENTER_VERTICAL)#, border=8)
##        hbox1d.Add(self.tmax_box, flag=wx.ALIGN_CENTER_VERTICAL)#, border=10)
##
##        hbox1d.AddSpacer(10)
##        hbox1d.Add(self.delete_interpretation_button,flag=wx.ALIGN_CENTER_VERTICAL)#, border=8)
        
##        vbox1b.Add(hbox1c,flag=wx.ALIGN_RIGHT)
##        vbox1b.AddSpacer(10)
##        vbox1b.Add(hbox1d,flag=wx.ALIGN_RIGHT)

        #select_temperature_box.Add(vbox1b)
    
        vbox1.AddSpacer(10)
        hbox1.AddSpacer(2)
        #hbox1.Add(vbox1a,flag=wx.ALIGN_CENTER_VERTICAL)#,flag=wx.ALIGN_CENTER_VERTICAL)
        #hbox1.Add(select_specimen_box,flag=wx.ALIGN_CENTER_VERTICAL)
        #hbox1.AddSpacer(10)        
        #hbox1.Add(vbox1b,flag=wx.ALIGN_CENTER_VERTICAL)#,flag=wx.ALIGN_CENTER_VERTICAL)
        #hbox1.Add(select_temperature_box,flag=wx.ALIGN_CENTER_VERTICAL)#,flag=wx.ALIGN_CENTER_VERTICAL)

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
        #hbox2.Add(self.logger,flag=wx.ALIGN_CENTER_HORIZONTAL)#,border=8)        
        hbox2.Add(vbox2a,flag=wx.ALIGN_CENTER_HORIZONTAL)#,border=8)        
        hbox2.Add(self.canvas1,flag=wx.ALIGN_CENTER_HORIZONTAL)#,border=8)

        vbox2 = wx.BoxSizer(wx.VERTICAL)        
        vbox2.Add(self.canvas2,flag=wx.ALIGN_LEFT)#,border=8)
        vbox2.Add(self.canvas3,flag=wx.ALIGN_LEFT)#,border=8)
        #vbox2.Add(

        vbox3 = wx.BoxSizer(wx.VERTICAL)        
        vbox3.Add(self.canvas4,flag=wx.ALIGN_LEFT|wx.ALIGN_TOP)#,border=8)
        vbox3.Add(self.canvas5,flag=wx.ALIGN_LEFT|wx.ALIGN_TOP)#,border=8)
        
        hbox2.Add(vbox2,flag=wx.ALIGN_CENTER_HORIZONTAL)#,border=8)
        hbox2.Add(vbox3,flag=wx.ALIGN_CENTER_HORIZONTAL)#,border=8)

        vbox1.Add(hbox2, flag=wx.LEFT, border=8)


        hbox_test = wx.BoxSizer(wx.HORIZONTAL)
    
                                    

        #hbox1.Add(specimen_stat_window, proportion=1, flag=wx.EXPAND)
##        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
##        hbox3.AddSpacer(10)                            
##        hbox3.Add(gs1,flag=wx.ALIGN_LEFT)
##        hbox3.AddSpacer(10)        
##
##        hbox3.Add(gs,flag=wx.ALIGN_LEFT)
##  
##        vbox1.AddSpacer(20)
##        vbox1.Add(hbox3,flag=wx.LEFT)
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
        """ save the current interpretation.
        """
        #t1=self.tmin_box.GetStringSelection()
        #t2=self.tmax_box.GetStringSelection()
        #if t1=="" or t2=="":
        #    return
        #if self.s not in self.redo_specimens.keys():
        #    self.redo_specimens[self.s]={}
        if "specimen_int_uT" not in self.Data[self.s]['pars']:
            return
        self.Data[self.s]['pars']['saved']=True

        # collect all interpretation by sample

        sample=self.Data_hierarchy['specimens'][self.s]
        if sample not in self.Data_samples.keys():
            self.Data_samples[sample]={}
        self.Data_samples[sample][self.s]=self.Data[self.s]['pars']["specimen_int_uT"]

        # collect all interpretation by site
        
        site=self.get_site_from_hierarchy(sample)
        if site not in self.Data_sites.keys():
            self.Data_sites[site]={}
        self.Data_sites[site][self.s]=self.Data[self.s]['pars']["specimen_int_uT"]
                
        self.draw_sample_mean()
        self.write_sample_box()
        #self.redo_specimens[self.s]['pars']=self.get_PI_parameters(self.s,float(t1)+273,float(t2)+273)
        #self.redo_specimens[self.s]['t_min']=273+float(t1)
        #self.redo_specimens[self.s]['t_max']=273.+float(t2)
        

        #self.tmin_box.SetStringSelection("")

    def on_delete_interpretation_button(self,event):
        """ save the current interpretation.
        """

        #if self.s  in self.redo_specimens.keys():
        #    del self.redo_specimens[self.s]
        del self.Data[self.s]['pars']
        self.Data[self.s]['pars']={}
        self.Data[self.s]['pars']['lab_dc_field']=self.Data[self.s]['lab_dc_field']
        self.Data[self.s]['pars']['er_specimen_name']=self.Data[self.s]['er_specimen_name']   
        self.Data[self.s]['pars']['er_sample_name']=self.Data[self.s]['er_sample_name']   
        self.Data[self.s]['pars']['er_sample_name']=self.Data[self.s]['er_sample_name']   
        sample=self.Data_hierarchy['specimens'][self.s]
        if sample in self.Data_samples.keys():
            if self.s in self.Data_samples[sample].keys():
                del self.Data_samples[sample][self.s]
                
        site=self.get_site_from_hierarchy(sample)                
        if site in self.Data_sites.keys():
            if self.s in self.Data_sites[site].keys():
                del self.Data_sites[site][self.s]

        self.tmin_box.SetValue("")
        self.tmax_box.SetValue("")
        self.clear_boxes()
        self.draw_figure(self.s)
        self.draw_sample_mean()
        self.write_sample_box()

    #----------------------------------------------------------------------
            
        
    def  write_acceptance_criteria_to_boxes(self):
        """ Update paleointensity Acceptance criteria boxes.
        """

##        window_list=['n','int_ptrm_n','frac','gap_max','f','fvds','b_beta','g','q','int_mad','dang','drats','md']
##        for key in window_list:
##            command="self.%s_threshold_window.SetBackgroundColour(wx.WHITE)"%key
##        try:
##            exec   command
##        except:
##            raw_input("check it ")


        high_threshold_velue_list=['specimen_gmax','specimen_b_beta','specimen_dang','specimen_drats','specimen_int_mad','specimen_md']
        low_threshold_velue_list=['specimen_int_n','specimen_int_ptrm_n','specimen_f','specimen_fvds','specimen_frac','specimen_g','specimen_q']
      
        self.ignore_parameters={}
        
        for key in high_threshold_velue_list + low_threshold_velue_list:
            if (key in high_threshold_velue_list and float(self.accept_new_parameters[key]) >100) or\
               (key in low_threshold_velue_list and float(self.accept_new_parameters[key]) <0.1):
                Value=""
                if key.split('specimen_')[-1] in self.preferences['show_statistics_on_gui']:
                    command="self.%s_threshold_window.SetValue(\"\")"%key.split('specimen_')[-1]
                    exec command
                    command="self.%s_threshold_window.SetBackgroundColour(wx.Colour(128, 128, 128))"%key.split('specimen_')[-1]
                    exec command
                self.ignore_parameters[key]=True
                continue
            elif key in ['specimen_int_n','specimen_int_ptrm_n']:
                Value="%.0f"%self.accept_new_parameters[key]
            elif key in ['specimen_dang','specimen_drats','specimen_int_mad','specimen_md','specimen_g','specimen_q']:
                Value="%.1f"%self.accept_new_parameters[key]
            elif key in ['specimen_f','specimen_fvds','specimen_frac','specimen_b_beta','specimen_gmax']:
                Value="%.2f"%self.accept_new_parameters[key]
            if key.split('specimen_')[-1] and key.split('specimen_')[-1] in self.preferences['show_statistics_on_gui']:
                command="self.%s_threshold_window.SetValue(Value)"%key.split('specimen_')[-1]
                exec command
                command="self.%s_threshold_window.SetBackgroundColour(wx.WHITE)"%key.split('specimen_')[-1]            
                exec command
            self.ignore_parameters[key]=False

        # scat parameter
        if self.accept_new_parameters['specimen_scat']==True:
            self.scat_threshold_window.SetValue("True")
            self.scat_threshold_window.SetBackgroundColour(wx.WHITE)           
            self.ignore_parameters['specimen_scat']=False
        else:
            self.scat_threshold_window.SetValue("")
            self.scat_threshold_window.SetBackgroundColour(wx.Colour(128, 128, 128))
            self.ignore_parameters['specimen_scat']=True
            
        for key in ['specimen_ptrms_inc','specimen_ptrms_dec','specimen_ptrms_mad','specimen_ptrms_angle']:
            self.ignore_parameters[key]=True
            if key.split('specimen_')[-1] in self.preferences['show_statistics_on_gui']:
                command="self.%s_threshold_window.SetValue(\"\")"%key.split('specimen_')[-1]
                exec command
                command="self.%s_threshold_window.SetBackgroundColour(wx.Colour(128, 128, 128))"%key.split('specimen_')[-1]
                exec command
                #self.ignore_parameters[key]=True
                    
    #----------------------------------------------------------------------
    

    def Add_text(self,s):
      """ Add text to measurement data wondow.
      """

      self.logger.Clear()
      FONT_RATIO=self.GUI_RESOLUTION+(self.GUI_RESOLUTION-1)*5
      font1 = wx.Font(9+FONT_RATIO, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Arial')
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
        """ Create menu
        """
        self.menubar = wx.MenuBar()


        menu_preferences = wx.Menu()
        
        m_preferences_apperance = menu_preferences.Append(-1, "&Appearence preferences", "")
        self.Bind(wx.EVT_MENU, self.on_menu_appearance_preferences, m_preferences_apperance)

        m_preferences_stat = menu_preferences.Append(-1, "&Statistics preferences", "")
        self.Bind(wx.EVT_MENU, self.on_menu_preferences_stat, m_preferences_stat)

        #m_save_preferences = menu_preferences.Append(-1, "&Save preferences", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_save_preferences, m_save_preferences)
        
        menu_file = wx.Menu()
        
        m_change_working_directory = menu_file.Append(-1, "&Change project directory", "")
        self.Bind(wx.EVT_MENU, self.on_menu_change_working_directory, m_change_working_directory)

        m_add_working_directory = menu_file.Append(-1, "&Add a MagIC project directory", "")
        self.Bind(wx.EVT_MENU, self.on_menu_add_working_directory, m_add_working_directory)

        m_open_magic_file = menu_file.Append(-1, "&Open MagIC measurement file", "")
        self.Bind(wx.EVT_MENU, self.on_menu_open_magic_file, m_open_magic_file)

        m_open_magic_tree = menu_file.Append(-1, "&Open all MagIC project directories in path", "")
        self.Bind(wx.EVT_MENU, self.on_menu_m_open_magic_tree, m_open_magic_tree)

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

        m_new_sub_plots = menu_file.AppendMenu(-1, "&Save plot", submenu_save_plots)

        
        menu_file.AppendSeparator()
        m_exit = menu_file.Append(-1, "E&xit\tCtrl-X", "Exit")
        self.Bind(wx.EVT_MENU, self.on_menu_exit, m_exit)


        menu_anistropy = wx.Menu()
        
        m_calculate_aniso_tensor = menu_anistropy.Append(-1, "&Calculate anistropy tensors", "")
        self.Bind(wx.EVT_MENU, self.on_menu_calculate_aniso_tensor, m_calculate_aniso_tensor)

        m_show_anisotropy_errors = menu_anistropy.Append(-1, "&Show anisotropy calculation Warnings/Errors", "")
        self.Bind(wx.EVT_MENU, self.on_show_anisotropy_errors, m_show_anisotropy_errors)


        menu_Analysis = wx.Menu()
        #m_prev_interpretation = menu_file.Append(-1, "&Save plot\tCtrl-S", "Save plot to file")

##        m_change_criteria_file = menu_Analysis.Append(-1, "&Change acceptance criteria", "")
##        self.Bind(wx.EVT_MENU, self.on_menu_criteria, m_change_criteria_file)
##        
##        m_import_criteria_file = menu_Analysis.Append(-1, "&Import criteria file", "")
##        self.Bind(wx.EVT_MENU, self.on_menu_criteria_file, m_import_criteria_file)

##        m_set_criteria_to_default = menu_Analysis.Append(-1, "&Change criteria to default", "")
##        self.Bind(wx.EVT_MENU, self.on_menu_default_criteria, m_set_criteria_to_default)


        submenu_criteria = wx.Menu()

        m_set_criteria_to_default = submenu_criteria.Append(-1, "&Set acceptance criteria to default", "")
        self.Bind(wx.EVT_MENU, self.on_menu_default_criteria, m_set_criteria_to_default)

        m_change_criteria_file = submenu_criteria.Append(-1, "&Change acceptance criteria", "")
        self.Bind(wx.EVT_MENU, self.on_menu_criteria, m_change_criteria_file)

        m_import_criteria_file =  submenu_criteria.Append(-1, "&Import criteria file", "")
        self.Bind(wx.EVT_MENU, self.on_menu_criteria_file, m_import_criteria_file)

        
##        submenu.Append(-1, "Sub Item 2")
##        submenu.Append(-1, "Sub Item 3")        

        m_new_sub = menu_Analysis.AppendMenu(-1, "Acceptance criteria", submenu_criteria)


        m_previous_interpretation = menu_Analysis.Append(-1, "&Import previous interpretation ('redo' file)", "")
        self.Bind(wx.EVT_MENU, self.on_menu_previous_interpretation, m_previous_interpretation)

        m_save_interpretation = menu_Analysis.Append(-1, "&Save current interpretations", "")
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


        menu_Optimizer = wx.Menu()
        m_run_optimizer = menu_Optimizer.Append(-1, "&Run Consistency test", "")
        self.Bind(wx.EVT_MENU, self.on_menu_run_optimizer, m_run_optimizer)

        m_run_consistency_test_b = menu_Optimizer.Append(-1, "&Run Consistency test beta version", "")
        self.Bind(wx.EVT_MENU, self.on_menu_run_consistency_test_b, m_run_consistency_test_b)

        menu_Plot= wx.Menu()
        m_plot_data = menu_Plot.Append(-1, "&Plot paleointensity curve", "")
        self.Bind(wx.EVT_MENU, self.on_menu_plot_data, m_plot_data)

        menu_results_table= wx.Menu()
        m_make_results_table = menu_results_table.Append(-1, "&Make results table", "")
        self.Bind(wx.EVT_MENU, self.on_menu_results_data, m_make_results_table)


        menu_MagIC= wx.Menu()
        m_convert_to_magic= menu_MagIC.Append(-1, "&Convert generic files to MagIC format", "")
        self.Bind(wx.EVT_MENU, self.on_menu_convert_to_magic, m_convert_to_magic)
        m_build_magic_model= menu_MagIC.Append(-1, "&Run MagIC model builder", "")
        self.Bind(wx.EVT_MENU, self.on_menu_MagIC_model_builder, m_build_magic_model)
        m_prepare_MagIC_results_tables= menu_MagIC.Append(-1, "&Make MagIC results Table", "")
        self.Bind(wx.EVT_MENU, self.on_menu__prepare_MagIC_results_tables, m_prepare_MagIC_results_tables)


        
        #menu_help = wx.Menu()
        #m_about = menu_help.Append(-1, "&About\tF1", "About the demo")
        self.menubar.Append(menu_preferences, "& Preferences") 
        self.menubar.Append(menu_file, "&File")
        self.menubar.Append(menu_anistropy, "&Anistropy")
        self.menubar.Append(menu_Analysis, "&Analysis")
        self.menubar.Append(menu_Auto_Interpreter, "&Auto Interpreter")
        self.menubar.Append(menu_Optimizer, "&Consistency Test")
        self.menubar.Append(menu_Plot, "&Plot")
        self.menubar.Append(menu_results_table, "&Table")
        self.menubar.Append(menu_MagIC, "&MagIC")
        
        self.SetMenuBar(self.menubar)


    #----------------------------------------------------------------------

    def update_selection(self):
        """ update figures and statistics window with a new selection of specimen
        """

        # clear all boxes
        self.clear_boxes()
        self.Add_text(self.s)
        self.draw_figure(self.s)
        
        # update temperature list
        if self.Data[self.s]['T_or_MW']=="T":
            self.temperatures=array(self.Data[self.s]['t_Arai'])-273.
        else:
            self.temperatures=array(self.Data[self.s]['t_Arai'])
            
        self.T_list=["%.0f"%T for T in self.temperatures]
        self.tmin_box.SetItems(self.T_list)
        self.tmax_box.SetItems(self.T_list)
        self.tmin_box.SetStringSelection("")
        self.tmax_box.SetStringSelection("")
        self.Blab_window.SetValue("%.0f"%(float(self.Data[self.s]['pars']['lab_dc_field'])*1e6))
        if "saved" in self.Data[self.s]['pars']:
            self.pars=self.Data[self.s]['pars']
            self.update_GUI_with_new_interpretation()
        self.write_sample_box()
        

    #----------------------------------------------------------------------
      
    def onSelect_specimen(self, event):
        """ update figures and text when a new specimen is selected
        """        
        self.s=self.specimens_box.GetStringSelection()
        self.update_selection()

    #----------------------------------------------------------------------

    def on_next_button(self,event):
      """ update figures and text when a next button is selected
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
      """ update figures and text when a next button is selected
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
        """ Clear all boxes
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
                                         
        window_list=['int_n','int_ptrm_n','frac','scat','gmax','f','fvds','b_beta','g','q','int_mad','dang','drats','md','ptrms_dec','ptrms_inc','ptrms_mad','ptrms_angle']
        for key in window_list:
            if key in self.preferences['show_statistics_on_gui']:
                command="self.%s_window.SetValue(\"\")"%key
                exec command
                command="self.%s_window.SetBackgroundColour(wx.NullColour)"%key
                exec command
            
    def write_sample_box(self):
##       B=[]
##        sample=self.Data_hierarchy['specimens'][self.s]
##        if sample not in self.Data_samples.keys() and 'specimen_int_uT' in self.pars.keys():
##            self.Data_samples[sample]={}
##            
##        if 'specimen_int_uT' in self.pars.keys():
##            if 'saved' in self.Data[self.s]['pars'].keys():
##                if self.Data[self.s]['pars']['saved']==True:
##                    self.Data_samples[sample][self.s]=self.pars['specimen_int_uT']
##            
##        red_flag=True

        B=[]
        
        if self.accept_new_parameters['average_by_sample_or_site']=='sample':
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
                            B.append(self.Data_samples[sample][specimen])
                    else:
                            B.append(self.Data_samples[sample][specimen])
            else:
                if 'specimen_int_uT' in self.pars.keys():
                    B.append(self.pars['specimen_int_uT'])


        # if averaging bu site
        else:
            
            sample=self.Data_hierarchy['specimens'][self.s]
            site=self.get_site_from_hierarchy(sample)
            if site in self.Data_sites.keys() and len(self.Data_sites[site].keys())>0:
                if self.s not in self.Data_sites[site].keys():
                    if 'specimen_int_uT' in self.pars.keys():
                        B.append(self.pars['specimen_int_uT'])
                for specimen in self.Data_sites[site].keys():
                    if specimen==self.s:
                        if 'specimen_int_uT' in self.pars.keys():
                            B.append(self.pars['specimen_int_uT'])
                        else:        
                            B.append(self.Data_sites[site][specimen])
                    else:
                            B.append(self.Data_sites[site][specimen])
            else:
                if 'specimen_int_uT' in self.pars.keys():
                    B.append(self.pars['specimen_int_uT'])
                           
                                                
        if B==[]:
            self.sample_int_n_window.SetValue("")
            self.sample_int_uT_window.SetValue("")
            self.sample_int_sigma_window.SetValue("")
            self.sample_int_sigma_perc_window.SetValue("")
            self.sample_int_uT_window.SetBackgroundColour(wx.NullColour)
            return()
            
        N=len(B)
        B_mean=mean(B)
        B_std=std(B,ddof=1)
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
        
        if N<self.accept_new_parameters['sample_int_n']:
            fail_int_n=True
        if not ( B_std <= self.accept_new_parameters['sample_int_sigma_uT'] or B_std_perc <= self.accept_new_parameters['sample_int_sigma_perc']):            
            if (B_std > self.accept_new_parameters['sample_int_sigma_uT']) :
                fail_int_sigma=True
            if B_std_perc > self.accept_new_parameters['sample_int_sigma_perc']:
                fail_int_sigma_perc=True            

        if fail_int_n or fail_int_sigma or fail_int_sigma_perc:
            self.sample_int_uT_window.SetBackgroundColour(wx.RED)
            
            if  fail_int_n :
                self.sample_int_n_window.SetBackgroundColour(wx.RED)

            if  fail_int_sigma :
                self.sample_int_sigma_window.SetBackgroundColour(wx.RED)

            if  fail_int_sigma_perc :
                self.sample_int_sigma_perc_window.SetBackgroundColour(wx.RED)
        else:
            self.sample_int_uT_window.SetBackgroundColour(wx.GREEN)
            

            
            
        

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
                self.show_Arai_temperatures_steps=FS.FloatSpin(pnl1, -1, min_val=1, max_val=9,increment=1, value=1, extrastyle=FS.FS_LEFT,size=(50,20))
                self.show_Arai_temperatures_steps.SetFormat("%f")
                self.show_Arai_temperatures_steps.SetDigits(0)

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
                self.show_Zij_temperatures_steps=FS.FloatSpin(pnl1, -1, min_val=1, max_val=9,increment=1, value=1, extrastyle=FS.FS_LEFT,size=(50,20))
                self.show_Zij_temperatures_steps.SetFormat("%f")
                self.show_Zij_temperatures_steps.SetDigits(0)
                                             
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
                        
##                        String="preferences['%s']=%f\n"%(key,self.preferences[key
##                for key in  self.preferences.keys():
##                    if key in ['gui_resolution','show_Zij_temperatures_steps','show_Arai_temperatures_steps']:
##                        String="preferences['%s']=%f\n"%(key,self.preferences[key])
##                    else:
##                        String="preferences['%s']=%s\n"%(key,self.preferences[key])
##                    fout.write(String)    
                    fout.write(String)    
                fout.close()
                os.chmod(preference_file,0777)            
                
            dlg2.Destroy()

            if change_resolution:
                dlg3 = wx.MessageDialog(self, "GUI resolution is changed.\nYou will need to restart the program","Confirm Exit", wx.OK|wx.ICON_QUESTION)
                result = dlg3.ShowModal()
                dlg3.Destroy()
                if result == wx.ID_OK:
                    self.Destroy()
                    exit()

            
            return()
        

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
        preferences['show_statistics_on_gui']=["int_n","int_ptrm_n","frac","scat","gmax","b_beta","int_mad","dang","f","fvds","g","q","drats"]#,'ptrms_dec','ptrms_inc','ptrms_mad','ptrms_angle']
        #try to read preferences file:
        try:
            import thellier_gui_preferences
            self.GUI_log.write( "-I- thellier_gui.preferences imported\n")
            preferences.update(thellier_gui_preferences.preferences)
        except:
            self.GUI_log.write( " -I- cant find thellier_gui_preferences file, using defualt default \n")
        return(preferences)
        


    #----------------------------------

    def on_menu_preferences_stat(self,event):
        class preferences_stats_dialog(wx.Dialog):
            
            def __init__(self, parent,title,preferences):
                self.preferences=preferences
                super(preferences_stats_dialog, self).__init__(parent, title=title)
                self.InitUI()

            def on_add_button(self,event):
                selName = str(self.criteria_options.GetStringSelection())
                if selName not in self.preferences['show_statistics_on_gui']:
                  self.preferences['show_statistics_on_gui'].append(selName)
                #self.update_text_box()
                self.criteria_list_window.Set(self.preferences['show_statistics_on_gui'])
                self.criteria_options.Set(self.statistics_options)

            def on_remove_button(self,event):
                selName = str(self.criteria_list_window.GetStringSelection())
                if selName  in self.preferences['show_statistics_on_gui']:
                  self.preferences['show_statistics_on_gui'].remove(selName)
                self.criteria_list_window.Set(self.preferences['show_statistics_on_gui'])
                self.criteria_options.Set(self.statistics_options)
               
##            def update_text_box(self):
##                TEXT=""
##                for key in self.preferences['show_statistics_on_gui']:
##                  TEXT=TEXT+key+"\n"
##                TEXT=TEXT[:-1]
##                self.criteria_list_window.SetValue('')
##                self.criteria_list_window.SetValue(TEXT)
                
            def InitUI(self):

                pnl1 = wx.Panel(self)

                vbox = wx.BoxSizer(wx.VERTICAL)

                #-----------box1        

                bSizer1 = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "Statistical definitions" ), wx.HORIZONTAL )
                self.bootstrap_N=wx.TextCtrl(pnl1,style=wx.TE_CENTER,size=(80,20))
                                             
                Statistics_definitions_window = wx.GridSizer(1, 2, 12, 12)
                Statistics_definitions_window.AddMany( [(wx.StaticText(pnl1,label="Bootstrap N",style=wx.TE_CENTER), wx.EXPAND),
                    (self.bootstrap_N, wx.EXPAND)])                 
                bSizer1.Add( Statistics_definitions_window, 0, wx.ALIGN_LEFT|wx.ALL, 5 )
                
                #-----------box2        

                bSizer2 = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "Dipole Moment" ), wx.HORIZONTAL )

                self.v_adm_box = wx.ComboBox(pnl1, -1, self.preferences['VDM_or_VADM'], (100, 20), wx.DefaultSize, ["VADM","VDM"], wx.CB_DROPDOWN,name="VDM or VADM?")
                                             
                Statistics_VADM = wx.GridSizer(1, 2, 12, 12)
                Statistics_VADM.AddMany( [(wx.StaticText(pnl1,label="VDM or VADM?",style=wx.TE_CENTER), wx.EXPAND),
                    (self.v_adm_box, wx.EXPAND)])                 
                bSizer2.Add( Statistics_VADM, 0, wx.ALIGN_LEFT|wx.ALL, 5 )
                         
                #----------------------
                                    
                bSizer3 = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "Choose statistics to display on GUI" ), wx.VERTICAL )

                self.statistics_options=["int_n","int_ptrm_n","frac","scat","gmax","b_beta","int_mad","dang","f","fvds","g","q","drats","md",'ptrms_dec','ptrms_inc','ptrms_mad','ptrms_angle']
                #self.criteria_list_window = wx.TextCtrl(pnl1, id=-1, size=(200,250), style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
                self.criteria_list_window =wx.ListBox(choices=self.preferences['show_statistics_on_gui'], id=-1,name='listBox1', parent=pnl1, size=wx.Size(150, 150), style=0)
                self.criteria_options = wx.ListBox(choices=self.statistics_options, id=-1,name='listBox1', parent=pnl1, size=wx.Size(150, 150), style=0)
                #self.criteria_options.Bind(wx.EVT_LISTBOX, self.on_choose_criterion,id=-1)
                self.criteria_add =  wx.Button(pnl1, id=-1, label='add')
                self.Bind(wx.EVT_BUTTON, self.on_add_button, self.criteria_add)
                self.criteria_remove =  wx.Button(pnl1, id=-1, label='remove')
                self.Bind(wx.EVT_BUTTON, self.on_remove_button, self.criteria_remove)

                Statistics_criteria_0 = wx.GridSizer(1, 2, 0, 0)
                Statistics_criteria_0.AddMany( [(wx.StaticText(pnl1,label="Options:"), wx.EXPAND),
                    (wx.StaticText(pnl1,label="Statistics displayed:"), wx.EXPAND)])
   
                Statistics_criteria_1 = wx.GridSizer(2, 2, 0, 0)
                Statistics_criteria_1.AddMany( [((self.criteria_options),wx.EXPAND),
                    ((self.criteria_list_window),wx.EXPAND),
                    ((self.criteria_add),wx.EXPAND),
                    ((self.criteria_remove),wx.EXPAND)])


##                bSizer3.Add(self.criteria_options,wx.ALIGN_LEFT)
##                bSizer3.Add(self.criteria_add,wx.ALIGN_LEFT)
##                bSizer3.Add(self.criteria_list_window)
                bSizer3.Add(Statistics_criteria_0, 0, wx.ALIGN_TOP, 0 )
                bSizer3.Add(Statistics_criteria_1, 0, wx.ALIGN_TOP, 0 )
                #self.update_text_box() 

                #----------------------

                hbox2 = wx.BoxSizer(wx.HORIZONTAL)
                self.okButton = wx.Button(pnl1, wx.ID_OK, "&OK")
                self.cancelButton = wx.Button(pnl1, wx.ID_CANCEL, '&Cancel')
                hbox2.Add(self.okButton)
                hbox2.Add(self.cancelButton )

                
                #----------------------  
                vbox.AddSpacer(20)
                vbox.Add(bSizer1, flag=wx.ALIGN_TOP)
                vbox.AddSpacer(20)

                vbox.Add(bSizer2, flag=wx.ALIGN_TOP)
                vbox.AddSpacer(20)

                vbox.Add(bSizer3, flag=wx.ALIGN_TOP)
                vbox.AddSpacer(20)

                vbox.Add(hbox2, flag=wx.ALIGN_TOP)
                vbox.AddSpacer(20)
                            
                pnl1.SetSizer(vbox)
                vbox.Fit(self)


                #---------------------- Initialize  values:

                try:                    
                    self.bootstrap_N.SetValue("%.0f"%(self.preferences["BOOTSTRAP_N"]))
                except:
                    self.bootstrap_N.SetValue("10000")
                    
                #----------------------
                    
        dia = preferences_stats_dialog(None,"Thellier_gui statistical preferences",self.preferences)
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


    #-----------------------------------
        
    def on_menu_exit(self, event):
        self.Destroy()
        exit()


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
        SaveMyPlot(self.fig1,self.pars,"Arai")
        self.fig1.clear()
        self.fig1.text(0.01,0.98,"Arai plot",{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'left' })
        self.araiplot = self.fig1.add_axes([0.1,0.1,0.8,0.8])
        self.draw_figure(self.s)
        self.update_selection()

    def on_save_Zij_plot(self, event):
        self.fig2.text(0.9,0.96,'%s'%(self.s),{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'right' })
        #self.canvas1.draw()
        SaveMyPlot(self.fig2,self.pars,"Zij")
        self.fig2.clear()
        self.fig2.text(0.02,0.96,"Zijderveld",{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'left' })
        self.zijplot = self.fig2.add_subplot(111)
        self.draw_figure(self.s)
        self.update_selection()
        
    def on_save_Eq_plot(self, event):
        self.fig3.text(0.9,0.96,'%s'%(self.s),{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'right' })        
        SaveMyPlot(self.fig3,self.pars,"Eqarea")
        self.fig3.clear()
        self.fig3.text(0.02,0.96,"Equal area",{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'left' })
        self.eqplot = self.fig3.add_subplot(111)
        self.draw_figure(self.s)
        self.update_selection()

    def on_save_M_t_plot(self,event):
        if self.preferences['show_NLT_plot'] ==False or 'NLT_parameters' not in self.Data[self.s].keys():
            self.fig5.text(0.9,0.96,'%s'%(self.s),{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'right' })        
            SaveMyPlot(self.fig5,self.pars,"M_T")
            self.fig5.clear()
            self.mplot = self.fig5.add_axes([0.2,0.15,0.7,0.7],frameon=True,axisbg='None')
            self.fig5.text(0.02,0.96,"M/T",{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'left' })
            self.draw_figure(self.s)
            self.update_selection()
        else:
            return


    def on_save_sample_plot(self,event):
        self.fig4.text(0.9,0.96,'%s'%(self.Data_hierarchy['specimens'][self.s]),{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'right' })        
        SaveMyPlot(self.fig4,self.pars,"Sample")
        self.fig4.clear()
        self.fig4.text(0.02,0.96,"Sample data",{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'left' })
        self.sampleplot = self.fig4.add_axes([0.2,0.3,0.7,0.6],frameon=True,axisbg='None')
        self.draw_figure(self.s)
        self.update_selection()


        
    def on_save_NLT_plot(self,event):
        if self.preferences['show_NLT_plot'] ==True and 'NLT_parameters' in self.Data[self.s].keys():
            self.fig5.text(0.9,0.96,'%s'%(self.s),{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'right' })        
            SaveMyPlot(self.fig5,self.pars,"NLT")
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
            SaveMyPlot(self.fig3,self.pars,"CR")
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
            defaultDir=self.currentDirectory, 
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

        self.read_redo_file(redo_file)
    #----------------------------------------------------------------------

    def on_menu_change_working_directory(self, event):
        
        self.redo_specimens={}
        self.currentDirectory = os.getcwd() # get the current working directory
        self.get_DIR()                      # choose directory dialog
        accept_new_parameters_default,accept_new_parameters_null=self.get_default_criteria()    # inialize Null selecting criteria
        self.accept_new_parameters_null=accept_new_parameters_null
        self.accept_new_parameters_default=accept_new_parameters_default
        # inialize Null selecting criteria
        accept_new_parameters=self.read_criteria_from_file(self.WD+"/pmag_criteria.txt")          
        self.accept_new_parameters=accept_new_parameters
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
        

        #accept_new_parameters_default,accept_new_parameters_null=self.get_default_criteria()    # inialize Null selecting criteria
        #self.accept_new_parameters_null=accept_new_parameters_null
        #self.accept_new_parameters_default=accept_new_parameters_default
        # inialize Null selecting criteria
        #accept_new_parameters=self.read_criteria_from_file(self.WD+"/pmag_criteria.txt")          
        #self.accept_new_parameters=accept_new_parameters
        #self.Data,self.Data_hierarchy,self.Data_info={},{},{}
        self.WD=new_magic_dir
        self.magic_file=new_magic_dir+"/"+"magic_measurements.txt"

        #old_Data=self.Data
        #old_Data_hierarchy=self.Data_hierarchy
        #old_Data_info=self.Data_info
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
            dialog = wx.DirDialog(None, "Choose a path. All magic directories in the pass will be imported:",defaultPath = self.currentDirectory ,style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON | wx.DD_CHANGE_DIR)
            if dialog.ShowModal() == wx.ID_OK:
              new_dir=dialog.GetPath()
            dialog.Destroy()

        #os.chdir(new_dir)
        for FILE in os.listdir(new_dir):
            path=new_dir+"/"+FILE
            if os.path.isdir(path):
                    print "importning from path %s"%path
                #try:
                    self.WD=path
                    self.magic_file=path+"/"+"magic_measurements.txt"
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
        and open changecriteria dialog
        """

    
        dlg = wx.FileDialog(
            self, message="choose a file in a pmagpy format",
            defaultDir=self.currentDirectory, 
            defaultFile="pmag_criteria.txt",
            #wildcard=wildcard,
            style=wx.OPEN | wx.CHANGE_DIR
            )
        if dlg.ShowModal() == wx.ID_OK:
            criteria_file = dlg.GetPath()
            self.GUI_log.write ("-I- Read new criteria file: %s\n"%criteria_file)
        dlg.Destroy()
        
        # inialize with Null values
        tmp_acceptance_criteria,replace_acceptance_criteria=self.get_default_criteria()

        # replace with values from file
        replace_acceptance_criteria=self.read_criteria_from_file(criteria_file)

        dia = Criteria_Dialog(None, replace_acceptance_criteria,title='Set Acceptance Criteria from file')
        dia.Center()
        if dia.ShowModal() == wx.ID_OK: # Until the user clicks OK, show the message            
            self.On_close_criteria_box(dia)



    #----------------------------------------------------------------------        

    def on_menu_criteria(self, event):
        
        """
        Change acceptance criteria
        and save it to pmag_criteria.txt
        """
                            

        dia = Criteria_Dialog(None, self.accept_new_parameters,title='Set Acceptance Criteria')
        dia.Center()
        result = dia.ShowModal()

        if result == wx.ID_OK: # Until the user clicks OK, show the message
            self.On_close_criteria_box(dia)
                
    #----------------------------------------------------------------------
            
    def On_close_criteria_box(self,dia):
        # inialize newcriteria with the default values
        tmp_acceptance_criteria,null_acceptance_criteria=self.get_default_criteria()
        replace_acceptance_criteria={}
        for k in null_acceptance_criteria.keys():
            replace_acceptance_criteria[k]=null_acceptance_criteria[k]
            
        # replace values by the new ones
        
        # specimen's criteria
        for key in self.high_threshold_velue_list + self.low_threshold_velue_list + ['anisotropy_alt']:
            command="replace_acceptance_criteria[\"%s\"]=float(dia.set_%s.GetValue())"%(key,key)
            try:
                exec command
            except:
                command="if dia.set_%s.GetValue() !=\"\" : self.show_messege(\"%s\")  "%(key,key)
                exec command
        if dia.set_specimen_scat.GetValue() == True:
          replace_acceptance_criteria['specimen_scat']=True
        else:
          replace_acceptance_criteria['specimen_scat']=False

        if dia.check_aniso_ftest.GetValue() == True:
          replace_acceptance_criteria['check_aniso_ftest']=True
        else:
          replace_acceptance_criteria['check_aniso_ftest']=False

        # sample calculation method:            
        for key in ['sample_int_stdev_opt','sample_int_bs','sample_int_bs_par']:
            command="replace_acceptance_criteria[\"%s\"]=dia.set_%s.GetValue()"%(key,key)            
            try:
                exec command
            except:
                command="if dia.set_%s.GetValue() !=\"\" : self.show_messege(\"%s\")  "%(key,key)
                exec command


        # sample ceiteria :            

        replace_acceptance_criteria["average_by_sample_or_site"]=dia.set_average_by_sample_or_site.GetValue()
         
        # sample criteria : 
                   
        for key in ['sample_int_n','sample_int_n_outlier_check']:
            command="replace_acceptance_criteria[\"%s\"]=float(dia.set_%s.GetValue())"%(key,key)            
            try:
                exec command
            except:
                command="if dia.set_%s.GetValue() !=\"\" : self.show_messege(\"%s\")  "%(key,key)
                exec command


        # sample ceiteria STDEV-OPT:
        if replace_acceptance_criteria['sample_int_stdev_opt']:
            for key in ['sample_int_sigma_uT','sample_int_sigma_perc','sample_int_interval_uT','sample_int_interval_perc','sample_aniso_threshold_perc']:
                command="replace_acceptance_criteria[\"%s\"]=float(dia.set_%s.GetValue())"%(key,key)            
                try:
                    exec command
                except:
                    command="if dia.set_%s.GetValue() !=\"\" : self.show_messege(\"%s\")  "%(key,key)
                    exec command


        # sample ceiteria BS, PS-PAR:
        if replace_acceptance_criteria['sample_int_bs'] or replace_acceptance_criteria['sample_int_bs_par']:
            for key in ['sample_int_BS_68_uT','sample_int_BS_68_perc','sample_int_BS_95_uT','sample_int_BS_95_perc',"specimen_int_max_slope_diff"]:
                command="replace_acceptance_criteria[\"%s\"]=float(dia.set_%s.GetValue())"%(key,key)            
                try:
                    exec command                    
                except:
                    command="if dia.set_%s.GetValue() !=\"\" : self.show_messege(\"%s\")  "%(key,key)
                    exec command
        

        #  message dialog
        dlg1 = wx.MessageDialog(self,caption="Warning:", message="Canges are saved to pmag_criteria.txt\n " ,style=wx.OK)
        result = dlg1.ShowModal()
        if result == wx.ID_OK:
            self.accept_new_parameters=replace_acceptance_criteria            
            self.clear_boxes()
            self.write_acceptance_criteria_to_boxes()
            self.write_acceptance_criteria_to_file()
            dlg1.Destroy()    
            dia.Destroy()
        self.recaclulate_satistics()
        
    def recaclulate_satistics(self):
        gframe=wx.BusyInfo("Re-calculating statsictics for all specimens\n Please wait..", self)

        for specimen in self.Data.keys():
            if 'pars' not in self.Data[specimen].keys():
                continue
            if 'specimen_int_uT' not in self.Data[specimen]['pars'].keys():
                continue
            tmin=self.Data[specimen]['pars']['measurement_step_min']
            tmax=self.Data[specimen]['pars']['measurement_step_max']
            pars=self.get_PI_parameters(specimen,tmin,tmax)
            self.Data[specimen]['pars']=pars
            self.Data[specimen]['pars']['lab_dc_field']=self.Data[specimen]['lab_dc_field']
            self.Data[specimen]['pars']['er_specimen_name']=self.Data[specimen]['er_specimen_name']   
            self.Data[specimen]['pars']['er_sample_name']=self.Data[specimen]['er_sample_name']   
        gframe.Destroy()    
                
            
        
    
    
        
    # only valid naumber can be entered to boxes        
    def show_messege(self,key):
        dlg1 = wx.MessageDialog(self,caption="Error:",
            message="not a vaild value for box %s"%key ,style=wx.OK)
        #dlg1.ShowModal()
        result = dlg1.ShowModal()
        if result == wx.ID_OK:
            dlg1.Destroy()
                


            
    #----------------------------------------------------------------------

    def read_criteria_from_file(self,criteria_file):

        """
        Try to read pmag_criteria.txt from working directory
        return a full list of acceptance criteria
        If cant read file rerurn the default values 
        """

        # initialize Null and Default 
        default_acceptance_criteria,null_acceptance_criteria=self.get_default_criteria()        # Replace with new parametrs
        replace_acceptance_criteria={}
        for key in null_acceptance_criteria:
            replace_acceptance_criteria[key]=null_acceptance_criteria[key]
        try:
            fin=open(criteria_file,'rU')
            line=fin.readline()
            line=fin.readline()
            header=line.strip('\n').split('\t')
            for L in fin.readlines():
                line=L.strip('\n').split('\t')
                for i in range(len(header)):

                        if header[i] in self.high_threshold_velue_list + ['anisotropy_alt']:
                            try:
                                if float(line[i])<100:
                                    replace_acceptance_criteria[header[i]]=float(line[i])
                            except:
                                pass
                        if header[i] in self.low_threshold_velue_list:
                            try:
                                if float(line[i])>0.01:
                                    replace_acceptance_criteria[header[i]]=float(line[i])
                            except:
                                pass

                        # scat parametr (true/false)
                        if header[i] == 'specimen_scat' and ( line[i]=='True' or line[i]=='TRUE' or line[i]==True):
                                replace_acceptance_criteria['specimen_scat']=True
                        if header[i] == 'specimen_scat' and ( line[i]=='False' or line[i]=='FALSE' or line[i]==False):
                                replace_acceptance_criteria['specimen_scat']=False

                        # aniso parametr (true/false)
                        if header[i] == 'check_aniso_ftest' and ( line[i]=='True' or line[i]=='TRUE' or line[i]==True):
                                replace_acceptance_criteria['check_aniso_ftest']=True
                        if header[i] == 'check_aniso_ftest' and ( line[i]=='False' or line[i]=='FALSE' or line[i]==False):
                                replace_acceptance_criteria['check_aniso_ftest']=False

                        # search for sample criteria:
                        if header[i] in ['sample_int_n','sample_int_sigma_uT','sample_int_sigma_perc','sample_int_interval_uT','sample_int_interval_perc','sample_aniso_threshold_perc','sample_int_n_outlier_check',\
                                         'specimen_int_max_slope_diff','specimen_int_BS_68_uT','specimen_int_BS_95_uT','specimen_int_BS_68_perc','specimen_int_BS_95_perc']:
                            try:
                                replace_acceptance_criteria[header[i]]=float(line[i])
                            except:
                                pass
                        if header[i] == "sample_int_sigma":
                            try:
                                replace_acceptance_criteria['sample_int_sigma']=float(line[i])
                                replace_acceptance_criteria['sample_int_sigma_uT']=float(line[i])*1e6
                            except:
                                pass
                        if header[i] in ["sample_int_bs_par","sample_int_bs","sample_int_stdev_opt"]:
                            if line[i]==True or line[i] in ["True","TRUE","1"]:
                                replace_acceptance_criteria[header[i]]=True

                        # serach for site acceptance criteria. 
                        
                        if header[i] == 'site_int_nn':
                            replace_acceptance_criteria['average_by_sample_or_site']='site'
                            replace_acceptance_criteria['sample_int_n']=float(line[i])
                        if header[i] == 'site_int_sigma':
                            replace_acceptance_criteria['sample_int_sigma']=float(line[i])
                            replace_acceptance_criteria['sample_int_sigma_uT']=float(line[i])*1e6
                        if header[i] == 'site_int_sigma_perc':
                            replace_acceptance_criteria['sample_int_sigma_perc']=float(line[i])
                           
                                
                        
                        # if finding accepatnce criteria for site, replace all acceptance criterai for sample withe site"
                        #if header[i] in ['site_int_n']:
                        #    try:
                        #        if int(line[i])>0:
                        #            replace_acceptance_criteria['average_by_sample_or_site']=='site'
                        #            if 'sample_int_n' in replace_acceptance_criteria
                        #            del  replace_acceptance_criteria['average_by_sample_or_site']
                        #        except:
                        #            pass    
                        #if 'site_int_n' in header and 'sample_int_n' in header:    
                        #    print "-E- ERROR: both criteria for int_sample and int_specimen
                                                                    
            if  replace_acceptance_criteria["sample_int_bs_par"]==False and replace_acceptance_criteria["sample_int_bs"]==False and replace_acceptance_criteria["sample_int_stdev_opt"]==False:
                replace_acceptance_criteria["sample_int_stdev_opt"]=True
            
            fin.close()
            return(replace_acceptance_criteria)
        
        #except:
        #    self.GUI_log.write("-W- Cant read Criteria file from path\n")
        #    self.GUI_log.write("-I- using default criteria\n")
        except:
            return(default_acceptance_criteria)

    #----------------------------------------------------------------------


    def on_menu_default_criteria(self,event):
        """
        Initialize acceptance criteria tp default
        """
        
        default_acceptance_criteria,null_acceptance_criteria=self.get_default_criteria()
        replace_acceptance_criteria={}
        for k in null_acceptance_criteria.keys():
            replace_acceptance_criteria[k]=null_acceptance_criteria[k]
        
        self.accept_new_parameters=default_acceptance_criteria
        self.clear_boxes()
        self.write_acceptance_criteria_to_boxes()
        self.write_acceptance_criteria_to_file()

    #----------------------------------------------------------------------


                
        #self.Fit()
        #self.SetMinSize(self.GetSize())

    #----------------------------------------------------------------------


    def on_menu_save_interpretation(self, event):
        
        thellier_gui_specimen_criteria_list=['specimen_int_n','specimen_int_ptrm_n','specimen_f','specimen_fvds','specimen_frac','specimen_gmax','specimen_b_beta','specimen_scat','specimen_drats','specimen_md','specimen_int_mad','specimen_dang','specimen_q','specimen_g']
        thellier_gui_redo_file=open("%s/thellier_GUI.redo"%(self.WD),'w')
        thellier_gui_specimen_file=open("%s/thellier_GUI.specimens.txt"%(self.WD),'w')
        thellier_gui_sample_file=open("%s/thellier_GUI.samples.txt"%(self.WD),'w')

        #----------------------------
        #    thellier_gui_specimens.txt header
        #----------------------------

        # selection criteria header
        String="Specimen's acceptance criteria:\n"
        String1=""
        for key in self.high_threshold_velue_list+self.low_threshold_velue_list+['specimen_scat']:
            if (key in self.high_threshold_velue_list and float(self.accept_new_parameters[key]) >100) or\
               (key in self.low_threshold_velue_list and float(self.accept_new_parameters[key]) <0.1):
                continue
            else:
                String=String+key+"\t"
                if key in ['specimen_f','specimen_fvds','specimen_gmax','specimen_b_beta','specimen_frac','specimen_drats','specimen_md','specimen_int_mad','specimen_dang']:
                        String1=String1+"%.2f"%self.accept_new_parameters[key]+"\t"

                elif key in ['specimen_int_n','specimen_int_ptrm_n']:
                        String1=String1+"%.0f"%self.accept_new_parameters[key]+"\t"
                elif key in ['specimen_scat']:
                        String1=String1+str(self.accept_new_parameters[key])+"\t"

        thellier_gui_specimen_file.write(String[:-1]+"\n")
        thellier_gui_specimen_file.write(String1[:-1]+"\n")

        thellier_gui_specimen_file.write("---------------------------------\n")

        # acceptance criteria header
        specimen_file_header_list=['er_specimen_name','er_sample_name','specimen_int_uT','measurement_step_min_c','measurement_step_max_c','specimen_lab_field_dc_uT','Anisotropy_correction_factor','NLT_specimen_correction_factor']
        String=""
        for crit in specimen_file_header_list:
            String=String+crit+"\t"
        for crit in thellier_gui_specimen_criteria_list:
            String=String+crit+"\t"

        String=String+"PASS/FAIL criteria\t"
        
        thellier_gui_specimen_file.write(String[:-1]+"\n")

        #----------------------------
        #    thellier_gui_samples.txt header
        #----------------------------

        if self.accept_new_parameters['average_by_sample_or_site']=='sample':

            thellier_gui_sample_file_header=['er_sample_name',  'sample_int_n'  ,'sample_int_uT',	'sample_int_sigma_uT','sample_int_sigma_perc']
            String=""
            for key in thellier_gui_sample_file_header:
                String=String+key+"\t"
            thellier_gui_sample_file.write(String[:-1]+"\n")

                
        #------------------------------------------
        #  write interpretations to thellier_GUI.specimens.txt
        #------------------------------------------


        spec_list=self.Data.keys()
        spec_list.sort()
        redo_specimens_list=[]
        for sp in spec_list:
            if 'saved' not in self.Data[sp]['pars']:
                continue
            if not self.Data[sp]['pars']['saved']:
                continue
            redo_specimens_list.append(sp)
            String=""
            for crit in specimen_file_header_list:
                if crit in ['er_specimen_name','er_sample_name']:
                    String=String+self.Data[sp]['pars'][crit]+"\t"
                elif crit in ['measurement_step_min_c','measurement_step_max_c']:
                    String=String+"%.0f"%(self.Data[sp]['pars'][crit[:-2]]-273.)+"\t"
                elif crit in ['specimen_int_uT']:
                    String=String+"%.1f"%self.Data[sp]['pars'][crit]+"\t"
                elif crit in ['specimen_lab_field_dc_uT']:
                    String=String+"%.1f"%(self.Data[sp]['pars']['lab_dc_field']*1e6)+"\t"
                elif crit in ['Anisotropy_correction_factor','NLT_specimen_correction_factor']:
                    if self.Data[sp]['pars'][crit] == -1:
                        String=String+"N/A" +"\t"
                    else:
                        String=String+"%.2f"%self.Data[sp]['pars'][crit]+"\t"
                           
            for crit in thellier_gui_specimen_criteria_list:
                if crit not in self.Data[sp]['pars'].keys():
                           String=String+"N/A"+"\t"
                elif crit in ['specimen_f','specimen_fvds','specimen_gmax','specimen_b_beta','specimen_frac','specimen_drats','specimen_int_mad','specimen_dang','specimen_q','specimen_g']:
                        String=String+"%.2f"%self.Data[sp]['pars'][crit]+"\t"
                elif crit in ['specimen_md']:
                    if self.Data[sp]['pars']['specimen_md']==-1:
                        String=String+"N/A" +"\t"
                    else:
                        String=String+"%.2f"%self.Data[sp]['pars']['specimen_md']+"\t"
                elif crit in ['specimen_int_n','specimen_int_ptrm_n']:
                        String=String+"%.0f"%self.Data[sp]['pars'][crit]+"\t"
                elif crit in ['specimen_scat']:
                        String=String+self.Data[sp]['pars'][crit]+"\t"

            if  len (self.Data[sp]['pars']['specimen_fail_criteria'])>0:
                String=String+"Fail on: "+ ",".join(self.Data[sp]['pars']['specimen_fail_criteria'])+"\t"
            else:
                String=String+"PASS" + "\t"
            thellier_gui_specimen_file.write(String[:-1]+"\n")
            
        #--------------------------------------------------
        #  write interpretations to thellier_GUI.redo
        #--------------------------------------------------

            thellier_gui_redo_file.write("%s %.0f %.0f\n"%(sp,self.Data[sp]['pars']['measurement_step_min'],self.Data[sp]['pars']['measurement_step_max']))
                                
        #--------------------------------------------------
        #  write interpretations to thellier_GUI.samples.txt
        #--------------------------------------------------

        if self.accept_new_parameters['average_by_sample_or_site']=='sample':
            thellier_gui_sample_file_header=['er_sample_name',  'sample_int_n'  ,'sample_int_uT',	'sample_int_sigma_uT','sample_int_sigma_perc']
            
            saved_samples_list= self.Data_samples.keys()
            saved_samples_list.sort()
            for sample in saved_samples_list:
                sample_Bs=[]
                for spec in self.Data_samples[sample]:
                    sample_Bs.append(self.Data_samples[sample][spec])
                sample_int_n=len(sample_Bs)
                sample_int_uT=mean(sample_Bs)
                sample_int_sigma_uT=std(sample_Bs,ddof=1)
                sample_int_sigma_perc=100*(sample_int_sigma_uT/sample_int_uT)
                
                String="%s\t%i\t%.1f\t%.1f\t%.1f\n"%(sample,sample_int_n,sample_int_uT,sample_int_sigma_uT,sample_int_sigma_perc)
                thellier_gui_sample_file.write(String)
            thellier_gui_sample_file.close()    
        
        thellier_gui_specimen_file.close()
        thellier_gui_redo_file.close()
        
        

    def on_menu_clear_interpretation(self, event):

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


            DIR_v1=self.cart2dir(v1)
            DIR_v2=self.cart2dir(v2)
            DIR_v3=self.cart2dir(v3)

                               
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
                    sigma=math.sqrt(S/nf)
                hpars=self.dohext(nf,sigma,[s1,s2,s3,s4,s5,s6])
                
                aniso_parameters['anisotropy_sigma']="%f"%sigma
                aniso_parameters['anisotropy_ftest']="%f"%hpars["F"]
                aniso_parameters['anisotropy_ftest12']="%f"%hpars["F12"]
                aniso_parameters['anisotropy_ftest23']="%f"%hpars["F23"]
                aniso_parameters['result_description']="Critical F: %s"%(hpars['F_crit'])
                aniso_parameters['anisotropy_F_crit']="%f"%float(hpars['F_crit'])
                aniso_parameters['anisotropy_n']=n_pos
                
            return(aniso_parameters)



        
        aniso_logfile=open(self.WD+"/rmag_anisotropy.log",'w')

        aniso_logfile.write("------------------------\n")
        aniso_logfile.write( "-I- Start rmag anisrotropy script\n")
        aniso_logfile.write( "------------------------\n")



        #-----------------------------------
        # Prepare rmag_anisotropy.txt file for writing
        #-----------------------------------

        rmag_anisotropy_file =open(self.WD+"/rmag_anisotropy.txt",'w')
        rmag_anisotropy_file.write("tab\trmag_anisotropy\n")

        rmag_results_file =open(self.WD+"/rmag_results.txt",'w')
        rmag_results_file.write("tab\trmag_results\n")
        
        rmag_anistropy_header=['er_specimen_name','er_sample_name','er_site_name','anisotropy_type','anisotropy_n','anisotropy_description','anisotropy_s1','anisotropy_s2','anisotropy_s3','anisotropy_s4','anisotropy_s5','anisotropy_s6','anisotropy_sigma','anisotropy_alt','magic_experiment_names','magic_method_codes','rmag_anisotropy_name']

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
                CART=self.dir2cart(positions[i])
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
                    
                aniso_logfile.write("-I- Start calculating ATRM tensor for specimen %s "%specimen)
                atrmblock=self.Data[specimen]['atrmblock']
                trmblock=self.Data[specimen]['trmblock']
                zijdblock=self.Data[specimen]['zijdblock']
                if len(atrmblock)<6:
                    aniso_logfile.write("-W- specimen %s has not enough measurementf for ATRM calculation\n"%specimen)
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
                        baselines.append(array(self.dir2cart([dec,inc,moment])))
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
                                baselines.append(array(self.dir2cart([dec,inc,moment])))
                                aniso_logfile.write( "-I- Found %i ATRM baselines for specimen %s in Zijderveld block. Averaging measurements\n"%(len(baselines),specimen))
                if  len(baselines)==0:
                    baseline=zeros(3,'f')
                    aniso_logfile.write( "-I- No aTRM baseline for specimen %s\n"%specimen)
                else:
                    baselines=array(baselines)
                    baseline=array([mean(baselines[:,0]),mean(baselines[:,1]),mean(baselines[:,2])])                                 
                           
                # sort measurements
                
                M=zeros([6,3],'f')
                
                for rec in atrmblock:

                    dec=float(rec['measurement_dec'])
                    inc=float(rec['measurement_inc'])
                    moment=float(rec['measurement_magn_moment'])
                    CART=array(self.dir2cart([dec,inc,moment]))-baseline
                    
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
                            M_1=sqrt(sum((array(M[i])**2)))
                            M_2=sqrt(sum(Alteration_check**2))
                            diff=abs(M_1-M_2)
                            diff_ratio=diff/max(M_1,M_2)
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
                    M_1=sqrt(sum(array(M[i])**2))
                    M_2=sqrt(sum(array(M[i+3])**2))
                    
                    diff=abs(M_1-M_2)
                    diff_ratio=diff/max(M_1,M_2)
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
                    Data_anisotropy[specimen]['ATRM']['rmag_anisotropy_name']=specimen


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
                            M_baseline=array(self.dir2cart([dec,inc,moment]))
                            
                        if float(rec['measurement_number'])==i*2+2:
                            dec=float(rec['measurement_dec'])
                            inc=float(rec['measurement_inc'])
                            moment=float(rec['measurement_magn_moment'])                    
                            M_arm=array(self.dir2cart([dec,inc,moment]))
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
                Data_anisotropy[specimen]['AARM']['rmag_anisotropy_name']=specimen
                

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
        

        dia = MyLogFileErrors( "Anistropy calculation errors","%s/rmag_anisotropy.log"%(self.WD))
        dia.Show()
        dia.Center()
    
        
 
    #==================================================        
                               
                                
    def on_menu_run_interpreter(self, event):

        import random
        import copy
        """
        Run thellier_auto_interpreter
        """

        ############
        # Function Definitions
        ############

        def find_close_value( LIST, value):
            diff=inf
            for a in LIST:
                if abs(value-a)<diff:
                    diff=abs(value-a)
                    result=a
            return(result)

        def find_sample_min_std (Intensities): 
            #find the best interpretation with the minimum stratard deviation (percent)
                
            Best_array=[]
            best_array_std_perc=inf
            Best_array_tmp=[]
            Best_interpretations={}
            Best_interpretations_tmp={}
            for this_specimen in Intensities.keys():
                for value in Intensities[this_specimen]:
                    Best_interpretations_tmp[this_specimen]=value
                    Best_array_tmp=[value]
                    all_other_specimens=Intensities.keys()
                    all_other_specimens.remove(this_specimen)
                    
                    for other_specimen in all_other_specimens:
                        closest_value=find_close_value(Intensities[other_specimen], value)
                        Best_array_tmp.append(closest_value)
                        Best_interpretations_tmp[other_specimen]=closest_value                   

                    if std(Best_array_tmp,ddof=1)/mean(Best_array_tmp)<best_array_std_perc:
                        Best_array=Best_array_tmp
                        best_array_std_perc=std(Best_array,ddof=1)/mean(Best_array_tmp)
                        Best_interpretations=copy.deepcopy(Best_interpretations_tmp)
                        Best_interpretations_tmp={}
            return Best_interpretations,mean(Best_array),std(Best_array,ddof=1)
            

        def find_sample_min_max_interpretation (Intensities,acceptance_criteria):

          # Find the minimum and maximum acceptable sample mean.

          # make a new dictionary named "tmp_Intensities" with all grade A interpretation sorted. 
          tmp_Intensities={}
          Acceptable_sample_min_mean,Acceptable_sample_max_mean="",""
          for this_specimen in Intensities.keys():
            B_list=[B  for B in Intensities[this_specimen]]
            if len(B_list)>0:
                B_list.sort()
                tmp_Intensities[this_specimen]=B_list

          # find the minmum acceptable values
          while len(tmp_Intensities.keys())>=float(acceptance_criteria["sample_int_n"]):
              B_tmp=[]
              B_tmp_min=1e10
              for specimen in tmp_Intensities.keys():
                  B_tmp.append(min(tmp_Intensities[specimen]))
                  if min(tmp_Intensities[specimen])<B_tmp_min:
                      specimen_to_remove=specimen
                      B_tmp_min=min(tmp_Intensities[specimen])
              if std(B_tmp,ddof=1)<=acceptance_criteria["sample_int_sigma_uT"] or 100*(std(B_tmp,ddof=1)/mean(B_tmp))<=acceptance_criteria["sample_int_sigma_perc"]:
                  Acceptable_sample_min_mean=mean(B_tmp)
                  Acceptable_sample_min_std=std(B_tmp,ddof=1)
                  #print "min value,std,",mean(B_tmp),std(B_tmp),100*(std(B_tmp)/mean(B_tmp))
                  break
              else:
                  tmp_Intensities[specimen_to_remove].remove(B_tmp_min)
                  if len(tmp_Intensities[specimen_to_remove])==0:
                      break
                      
          tmp_Intensities={}
          for this_specimen in Intensities.keys():
            B_list=[B  for B in Intensities[this_specimen]]
            if len(B_list)>0:
                B_list.sort()
                tmp_Intensities[this_specimen]=B_list

          while len(tmp_Intensities.keys())>=float(acceptance_criteria["sample_int_n"]):
              B_tmp=[]
              B_tmp_max=0
              for specimen in tmp_Intensities.keys():
                  B_tmp.append(max(tmp_Intensities[specimen]))
                  if max(tmp_Intensities[specimen])>B_tmp_max:
                      specimen_to_remove=specimen
                      B_tmp_max=max(tmp_Intensities[specimen])
              if std(B_tmp,ddof=1)<=acceptance_criteria["sample_int_sigma_uT"] or 100*(std(B_tmp,ddof=1)/mean(B_tmp))<=acceptance_criteria["sample_int_sigma_perc"]:
                  Acceptable_sample_max_mean=mean(B_tmp)
                  Acceptable_sample_max_std=std(B_tmp,ddof=1)
                  #print "max value,std,",mean(B_tmp),std(B_tmp),100*(std(B_tmp)/mean(B_tmp))

                  break
              else:
                  tmp_Intensities[specimen_to_remove].remove(B_tmp_max)
                  if len(tmp_Intensities[specimen_to_remove])<1:
                      break

          if Acceptable_sample_min_mean=="" or Acceptable_sample_max_mean=="":
              return(0.,0.,0.,0.)
          return(Acceptable_sample_min_mean,Acceptable_sample_min_std,Acceptable_sample_max_mean,Acceptable_sample_max_std) 

        ############
        # End function definitions
        ############

        start_time=time.time()
        #------------------------------------------------
        # Clean work directory
        #------------------------------------------------

        self.write_acceptance_criteria_to_file()
        try:
            shutil.rmtree(self.WD+"/thellier_interpreter")
        except:
            pass

        try:
            os.mkdir(self.WD+"/thellier_interpreter")
        except:
            pass

        parameters_with_upper_bounds= ['specimen_gmax','specimen_b_beta','specimen_dang','specimen_drats','specimen_int_mad','specimen_md']
        parameters_with_lower_bounds= ['specimen_int_n','specimen_int_ptrm_n','specimen_f','specimen_fvds','specimen_frac']
        accept_specimen_keys=['specimen_int_n','specimen_int_ptrm_n','specimen_f','specimen_fvds','specimen_frac','specimen_gmax','specimen_b_beta','specimen_dang','specimen_drats','specimen_int_mad','specimen_md','specimen_g','specimen_q']

        #------------------------------------------------
        # Intialize interpreter output files:
        # Prepare header for "Thellier_auto_interpretation.all.txt" 
        # All the acceptable interpretation are saved in this file
        #------------------------------------------------

        # log file
        thellier_interpreter_log=open(self.WD+"/"+"/thellier_interpreter//thellier_interpreter.log",'w')
        thellier_interpreter_log.write("-I- Start auto interpreter\n")

        # "all grade A interpretation
        thellier_interpreter_all=open(self.WD+"/thellier_interpreter/thellier_interpreter_all.txt",'w')
        thellier_interpreter_all.write("tab\tpmag_specimens\n")
        String="er_specimen_name\tmeasurement_step_min\tmeasurement_step_max\tspecimen_lab_field_dc_uT\tspecimen_int_corr_anisotropy\tspecimen_int_corr_nlt\tspecimen_int_corr_cooling_rate\tspecimen_int_uT\t"
        for key in accept_specimen_keys + ["specimen_b"] + ['specimen_cm_x'] + ['specimen_cm_y']:
            String=String+key+"\t"
        String=String[:-1]+"\n"
        thellier_interpreter_all.write(String)

        #specimen_bound
        Fout_specimens_bounds=open(self.WD+"/thellier_interpreter/thellier_interpreter_specimens_bounds.txt",'w')
        String="Selection criteria:\n"
        for key in accept_specimen_keys:
                String=String+key+"\t"
        Fout_specimens_bounds.write(String[:-1]+"\n")
        String=""
        for key in accept_specimen_keys:
            if key!= "specimen_frac":
                String=String+"%.2f\t"%self.accept_new_parameters[key]
            else:
                String=String+"%s\t"%self.accept_new_parameters[key]                
        Fout_specimens_bounds.write(String[:-1]+"\n")
        
        Fout_specimens_bounds.write("--------------------------------\n")
        Fout_specimens_bounds.write("er_sample_name\ter_specimen_name\tspecimen_int_corr_anisotropy\tAnisotropy_code\tspecimen_int_corr_nlt\tspecimen_int_corr_cooling_rate\tspecimen_lab_field_dc_uT\tspecimen_int_min_uT\tspecimen_int_max_uT\tWARNING\n")


        criteria_string="Selection criteria:\n"
        for key in self.accept_new_parameters.keys():
            if "sample" in key:
                criteria_string=criteria_string+key+"\t"
        for key in accept_specimen_keys:
            if "specimen" in key:
                criteria_string=criteria_string+key+"\t"
        criteria_string=criteria_string[:-1]+"\n"
        for key in self.accept_new_parameters.keys():
            if "sample" in key:
                try:
                    criteria_string=criteria_string+"%.2f"%self.accept_new_parameters[key]+"\t"
                except:
                    criteria_string=criteria_string+"%s"%self.accept_new_parameters[key]+"\t"                
        for key in accept_specimen_keys:
            if "specimen" in key:
                try:
                    criteria_string=criteria_string+"%.2f"%self.accept_new_parameters[key]+"\t"
                except:
                    criteria_string=criteria_string+"%s"%self.accept_new_parameters[key]+"\t"
        criteria_string=criteria_string[:-1]+"\n"
        criteria_string=criteria_string+"---------------------------------\n"

        # STDEV-OPT output files
        if self.accept_new_parameters['sample_int_stdev_opt']:
            Fout_STDEV_OPT_redo=open(self.WD+"/thellier_interpreter/thellier_interpreter_STDEV-OPT_redo",'w')

            Fout_STDEV_OPT_specimens=open(self.WD+"/thellier_interpreter/thellier_interpreter_STDEV-OPT_specimens.txt",'w')
            Fout_STDEV_OPT_specimens.write("tab\tpmag_specimens\n")
            String="er_sample_name\ter_specimen_name\tspecimen_int_uT\tmeasurement_step_min\tmeasurement_step_min\tspecimen_lab_field_dc\tAnisotropy_correction_factor\tNLT_correction_factor\tCooling_rate_correction_factor\t"
            for key in accept_specimen_keys:
                String=String+key+"\t"        
            Fout_STDEV_OPT_specimens.write(String[:-1]+"\n")

            if self.accept_new_parameters['average_by_sample_or_site']=='sample':
                Fout_STDEV_OPT_samples=open(self.WD+"/thellier_interpreter/thellier_interpreter_STDEV-OPT_samples.txt",'w')
                Fout_STDEV_OPT_samples.write(criteria_string)
                Fout_STDEV_OPT_samples.write("er_sample_name\tsample_int_n\tsample_int_uT\tsample_int_sigma_uT\tsample_int_sigma_perc\tsample_int_min_uT\tsample_int_min_sigma_uT\tsample_int_max_uT\tsample_int_max_sigma_uT\tsample_int_interval_uT\tsample_int_interval_perc\tWarning\n")
            else:
                Fout_STDEV_OPT_sites=open(self.WD+"/thellier_interpreter/thellier_interpreter_STDEV-OPT_sites.txt",'w')
                Fout_STDEV_OPT_sites.write(criteria_string)
                Fout_STDEV_OPT_sites.write("er_site_name\tsite_int_n\tsite_int_uT\tsite_int_sigma_uT\tsite_int_sigma_perc\tsite_int_interval_uT\tsite_int_interval_perc\tWarning\n")
                
        # simple bootstrap output files
        # Dont supports site yet!
 
        if self.accept_new_parameters['sample_int_bs']:
           Fout_BS_samples=open(self.WD+"/thellier_interpreter/thellier_interpreter_BS_samples.txt",'w')
           Fout_BS_samples.write(criteria_string)
           #Fout_BS_samples.write("---------------------------------\n")
           Fout_BS_samples.write("er_sample_name\tsample_int_n\tsample_int_uT\tsample_int_68_low\tsample_int_68_high\tsample_int_95_low\tsample_int_95_high\tsample_int_sigma_uT\tsample_int_sigma_perc\tWARNING\n")
        # parameteric bootstrap output files

        if self.accept_new_parameters['sample_int_bs_par']:
           Fout_BS_PAR_samples=open(self.WD+"/thellier_interpreter/thellier_interpreter_BS-PAR_samples.txt",'w')
           Fout_BS_PAR_samples.write(criteria_string) 
           #Fout_BS_PAR_samples.write("---------------------------------\n")
           Fout_BS_PAR_samples.write("er_sample_name\tsample_int_n\tsample_int_uT\tsample_int_68_low\tsample_int_68_high\tsample_int_95_low\tsample_int_95_high\tsample_int_sigma_uT\tsample_int_sigma_perc\tWARNING\n")
           
        thellier_interpreter_log.write("-I- using paleointenisty statistics:\n")
        for key in [key for key in self.accept_new_parameters.keys() if "sample" in key]:
            try:
                thellier_interpreter_log.write("-I- %s=%.2f\n"%(key,self.accept_new_parameters[key]))
            except:
                thellier_interpreter_log.write("-I- %s=%s\n"%(key,self.accept_new_parameters[key]))
                                            
        for key in [key for key in self.accept_new_parameters.keys() if "specimen" in key]:
            try:
                thellier_interpreter_log.write("-I- %s=%.2f\n"%(key,self.accept_new_parameters[key]))
            except:
                thellier_interpreter_log.write("-I- %s=%s\n"%(key,self.accept_new_parameters[key]))
               
                                  

        
        #------------------------------------------------

        busy_frame=wx.BusyInfo("Running Thellier auto interpreter\n It may take several minutes depending on the number of specimens ...", self)

        specimens_list=self.Data.keys()
        specimens_list.sort()
        thellier_interpreter_log.write("-I- Found %i specimens\n"%(len(specimens_list)))

        #try:
        All_grade_A_Recs={}
        for s in specimens_list:
            thellier_interpreter_log.write("-I- doing now specimen %s\n"%s)
            self.Data[s]['pars']={}
            self.Data[s]['pars']['lab_dc_field']=self.Data[s]['lab_dc_field']
            self.Data[s]['pars']['er_specimen_name']=s
            self.Data[s]['pars']['er_sample_name']=self.Data_hierarchy['specimens'][s]
            temperatures=self.Data[s]['t_Arai']
            
            # check that all temperatures are in right order:
            ignore_specimen=False
            for t in range(len(temperatures)-1):
                if float(temperatures[t+1])<float(temperatures[t]):
                    thellier_interpreter_log.write("-W- Found problem in the temperature order of specimen %s. skipping specimen\n"%(s))
                    ignore_specimen=True
            if ignore_specimen:
                continue
            specimen_int_n=int(self.accept_new_parameters['specimen_int_n'])
 
            #-------------------------------------------------            
            # loop through all possible tmin,tmax and check if pass criteria
            #-------------------------------------------------

            for tmin_i in range(len(temperatures)-specimen_int_n+1):
                for tmax_i in range(tmin_i+specimen_int_n-1,len(temperatures)):
                    tmin=temperatures[tmin_i]
                    tmax=temperatures[tmax_i]
                    pars=self.get_PI_parameters(s,tmin,tmax)

                    #-------------------------------------------------            
                    # check if pass the criteria
                    #-------------------------------------------------

                    # distinguish between upper threshold value and lower threshold value

                    if 'specimen_fail_criteria' not in pars:
                        continue
                    if len(pars['specimen_fail_criteria'])>0:
                        # Fail:
                        message_string= "-I- specimen %s (%.0f-%.0f) FAIL on: "%(s,float(pars["measurement_step_min"])-273, float(pars["measurement_step_max"])-273)
                        for parameter in pars['specimen_fail_criteria']:
                            if "scat" not in parameter:
                                message_string=message_string+parameter + "= %f,  "%pars[parameter]
                            else:
                                message_string=message_string+parameter + "= %s,  "%str(pars[parameter])
                                
                        thellier_interpreter_log.write(message_string+"\n")        
                    else:

                        # PASS:
                        message_string = "-I- specimen %s (%.0f-%.0f) PASS"%(s,float(pars["measurement_step_min"])-273, float(pars["measurement_step_max"])-273)
                        thellier_interpreter_log.write(message_string+"\n")
                        
                        #--------------------------------------------------------------
                        # Save all the grade A interpretation in thellier_interpreter_all.txt
                        #--------------------------------------------------------------

                        String=s+"\t"
                        String=String+"%.0f\t"%(float(pars["measurement_step_min"])-273.)
                        String=String+"%.0f\t"%(float(pars["measurement_step_max"])-273.)
                        String=String+"%.0f\t"%(float(pars["lab_dc_field"])*1e6)
                        #if "Anisotropy_correction_factor" in All_grade_A_Recs[specimen][TEMP].keys():
                        #    Anisotropy_correction_factor="%.2f"%(All_grade_A_Recs[specimen][TEMP]["Anisotropy_correction_factor"])
                        #if "AC_specimen_correction_factor" in pars.keys():
                        #   String=String+"%.2f\t"%float(pars["AC_specimen_correction_factor"])
                        if "Anisotropy_correction_factor" in pars.keys():
                           String=String+"%.2f\t"%float(pars["Anisotropy_correction_factor"])
                        else:
                           String=String+"-\t"
                        if  float(pars["NLT_specimen_correction_factor"])!=-999:
                           String=String+"%.2f\t"%float(pars["NLT_specimen_correction_factor"])
                        else:
                           String=String+"-\t"
                        if  float(pars["specimen_int_corr_cooling_rate"])!=-999 and float(pars["specimen_int_corr_cooling_rate"])!=-1 :
                           String=String+"%.2f\t"%float(pars["specimen_int_corr_cooling_rate"])
                        else:
                           String=String+"-\t"
                        Bancient=float(pars['specimen_int_uT'])
                        String=String+"%.1f\t"%(Bancient)
                        for key in accept_specimen_keys + ["specimen_b"] + ["specimen_cm_x"] + ["specimen_cm_y"]:
                           String=String+"%.2f"%(pars[key])+"\t"
                        String=String[:-1]+"\n"

                        thellier_interpreter_all.write(String)


                        #-------------------------------------------------                    
                        # save 'acceptable' (grade A) specimen interpretaion
                        # All_grade_A_Recs={}
                        # All_grade_A_Recs[specimen_name]["tmin,tmax"]={PI pars sorted in dictionary}
                        #-------------------------------------------------
                        
                        if s not in All_grade_A_Recs.keys():
                           All_grade_A_Recs[s]={}
                        new_pars={}
                        for k in pars.keys():
                            new_pars[k]=pars[k]
                        TEMP="%.0f,%.0f"%(float(pars["measurement_step_min"])-273,float(pars["measurement_step_max"])-273)
                        All_grade_A_Recs[s][TEMP]=new_pars


        specimens_list=All_grade_A_Recs.keys()
        specimens_list.sort()
        Grade_A_samples={}
        Grade_A_sites={}
        Redo_data_specimens={}
        
        #--------------------------------------------------------------
        # specimens bound file
        #--------------------------------------------------------------

        for s in specimens_list:

            sample=self.Data_hierarchy['specimens'][s]
            site=self.get_site_from_hierarchy(sample)
            B_lab=float(self.Data[s]['lab_dc_field'])*1e6
            B_min,B_max=1e10,0.
            NLT_factor_min,NLT_factor_max=1e10,0.
            all_B_tmp_array=[]

            for TEMP in All_grade_A_Recs[s].keys():
                pars=All_grade_A_Recs[s][TEMP]
                if "AC_anisotropy_type" in pars.keys():
                    AC_correction_factor=pars["Anisotropy_correction_factor"]
                    AC_correction_type=pars["AC_anisotropy_type"]
                    WARNING=""
                    if "AC_WARNING" in pars.keys():
                        WARNING=WARNING+pars["AC_WARNING"]
                else:
                    AC_correction_factor=1.
                    AC_correction_type="-"
                    WARNING="WARNING: No anisotropy correction"
                
                B_anc=pars['specimen_int_uT']
                    
                if B_anc< B_min:
                    B_min=B_anc
                if B_anc > B_max:
                    B_max=B_anc
                if pars["NLT_specimen_correction_factor"]!=-1:
                    NLT_f=pars['NLT_specimen_correction_factor']
                    if NLT_f< NLT_factor_min:
                        NLT_factor_min=NLT_f
                    if NLT_f > NLT_factor_max:
                        NLT_factor_max=NLT_f                

                # sort by samples
                #--------------------------------------------------------------
                
                if sample not in Grade_A_samples.keys():
                    Grade_A_samples[sample]={}
                if s not in Grade_A_samples[sample].keys() and len(All_grade_A_Recs[s])>0:
                    Grade_A_samples[sample][s]=[]

                Grade_A_samples[sample][s].append(B_anc)                

                # sort by sites
                #--------------------------------------------------------------
                
                if site not in Grade_A_sites.keys():
                    Grade_A_sites[site]={}
                if s not in Grade_A_sites[site].keys() and len(All_grade_A_Recs[s])>0:
                    Grade_A_sites[site][s]=[]
                Grade_A_sites[site][s].append(B_anc)                

                # ? check
                #--------------------------------------------------------------

                if s not in Redo_data_specimens.keys():
                    Redo_data_specimens[s]={}

            # write to specimen_bounds
            #--------------------------------------------------------------

            if pars["NLT_specimen_correction_factor"] != -1:
                NLT_factor="%.2f"%(NLT_factor_max)
            else:
                NLT_factor="-"

            if pars["specimen_int_corr_cooling_rate"] != -1 and pars["specimen_int_corr_cooling_rate"] != -999:
                CR_factor="%.2f"%(float(pars["specimen_int_corr_cooling_rate"]))
            else:
                CR_factor="-"
            if 'cooling_rate_data' in  self.Data[s].keys():
                if 'CR_correction_factor_flag' in  self.Data[s]['cooling_rate_data'].keys():
                    if self.Data[s]['cooling_rate_data']['CR_correction_factor_flag'] != "calculated":
                        if "inferred" in self.Data[s]['cooling_rate_data']['CR_correction_factor_flag']:
                            WARNING=WARNING+";"+"cooling rate correction inferred from sister specimens"
                        if "alteration" in self.Data[s]['cooling_rate_data']['CR_correction_factor_flag']:
                            WARNING=WARNING+";"+"cooling rate experiment failed alteration"
                        if "bad" in self.Data[s]['cooling_rate_data']['CR_correction_factor_flag']:
                            WARNING=WARNING+";"+"cooling rate experiment failed"
                
            if AC_correction_type =="-":
                AC_correction_factor_to_print="-"
            else:
                AC_correction_factor_to_print="%.2f"%AC_correction_factor
            
            String="%s\t%s\t%s\t%s\t%s\t%s\t%.1f\t%.1f\t%.1f\t%s\n"\
                    %(sample,s,AC_correction_factor_to_print,AC_correction_type,NLT_factor,CR_factor,B_lab,B_min,B_max,WARNING)
            Fout_specimens_bounds.write(String)


        #--------------------------------------------------------------
        # Find the STDEV-OPT 'best mean':
        # the interprettaions that give
        # the minimum standrad deviation (perc!)
        # not nesseserily the standrad deviation in microT
        #
        #--------------------------------------------------------------

        # Sort all grade A interpretation

        samples=Grade_A_samples.keys()
        samples.sort()

        sites=Grade_A_sites.keys()
        sites.sort()

        #--------------------------------------------------------------        
        # delete all previous interpretation
        #--------------------------------------------------------------
        for sp in self.Data.keys():
            del self.Data[sp]['pars']
            self.Data[sp]['pars']={}
            self.Data[sp]['pars']['lab_dc_field']=self.Data[sp]['lab_dc_field']
            self.Data[sp]['pars']['er_specimen_name']=self.Data[sp]['er_specimen_name']   
            self.Data[sp]['pars']['er_sample_name']=self.Data[sp]['er_sample_name']
        self.Data_samples={}
        self.Data_sites={}
        interpreter_redo={}


        #--------------------------------------------------------------        
        # STDEV can work by averaging specimens by sample (default)
        # or by averaging specimens by site
        #--------------------------------------------------------------

                
        if self.accept_new_parameters['average_by_sample_or_site']=='sample':
            Grade_A_sorted=copy.deepcopy(Grade_A_samples)
             
        else:
            Grade_A_sorted=copy.deepcopy(Grade_A_sites)

            #--------------------------------------------------------------
            # check for anistropy issue:
            # If the average anisotropy correction in the sample is > 10%,
            # and there are enough good specimens with  anisotropy correction to pass sample's criteria
            # then dont use the uncorrected specimens for sample's calculation. 
            #--------------------------------------------------------------
        samples_or_sites=Grade_A_sorted.keys()
        samples_or_sites.sort()
        #print Grade_A_sorted
        for sample_or_site in samples_or_sites:
            if self.accept_new_parameters['sample_aniso_threshold_perc'] != "" and float(self.accept_new_parameters['sample_aniso_threshold_perc'])<100:
                if len(Grade_A_sorted[sample_or_site].keys())>self.accept_new_parameters['sample_int_n']:
                    aniso_corrections=[]
                    for specimen in Grade_A_sorted[sample_or_site].keys():
                        AC_correction_factor=0
                        for k in All_grade_A_Recs[specimen].keys():
                            pars=All_grade_A_Recs[specimen][k]
                            if "AC_anisotropy_type" in pars.keys():
                                if "AC_WARNING" in pars.keys():
                                    if "TRM" in pars["AC_WARNING"] and pars["AC_anisotropy_type"]== "ATRM" and "alteration" in pars["AC_WARNING"]:
                                        continue
                                    AC_correction_factor=max(AC_correction_factor,pars["Anisotropy_correction_factor"])
                        if AC_correction_factor!=0:
                            aniso_corrections.append(abs(1.-float(AC_correction_factor)))
                    if aniso_corrections!=[]:
                        thellier_interpreter_log.write("sample_or_site %s have anisotropy factor mean of %f\n"%(sample_or_site,mean(aniso_corrections)))

                    if mean(aniso_corrections) > float(self.accept_new_parameters['sample_aniso_threshold_perc'])/100 : # 0.10:
                        tmp_Grade_A_sorted=copy.deepcopy(Grade_A_sorted)
                        warning_messeage=""
                        WARNING_tmp=""
                        #print "sample %s have anisotropy factor mean of %f"%(sample,mean(aniso_corrections))
                        for specimen in Grade_A_sorted[sample_or_site].keys():
                            ignore_specimen=False
                            intenstities=All_grade_A_Recs[specimen].keys()
                            pars=All_grade_A_Recs[specimen][intenstities[0]]
                            if "AC_anisotropy_type" not in pars.keys():
                                ignore_specimen=True
                            elif "AC_WARNING" in pars.keys():
                                #if "alteration check" in pars["AC_WARNING"]:
                                    if pars["AC_anisotropy_type"]== "ATRM" and "TRM" in pars["AC_WARNING"] and  "alteration" in pars["AC_WARNING"]  : 
                                       #or "ARM" in pars["AC_WARNING"] and  pars["AC_anisotropy_type"]== "AARM":
                                        ignore_specimen=True
                            if ignore_specimen: 
                                warning_messeage = warning_messeage + "-W- WARNING: specimen %s is exluded from sample %s because it doesnt have anisotropy correction, and other specimens are very anistropic\n"%(specimen,sample_or_site)
                                WARNING_tmp=WARNING_tmp+"excluding specimen %s; "%(specimen)
                                del tmp_Grade_A_sorted[sample_or_site][specimen]
                                
                        #--------------------------------------------------------------
                        # calculate the STDEV-OPT best mean (after possible ignoring of specimens with bad anisotropy)
                        # and check if pass after ignoring problematic anistopry specimens 
                        # if pass: delete the problematic specimens from Grade_A_sorted
                        #--------------------------------------------------------------
                        
                        if len(tmp_Grade_A_sorted[sample_or_site].keys())>=self.accept_new_parameters['sample_int_n']:
                            Best_interpretations,best_mean,best_std=find_sample_min_std(tmp_Grade_A_sorted[sample_or_site])
                            sample_acceptable_min,sample_acceptable_min_std,sample_acceptable_max,sample_acceptable_max_std = find_sample_min_max_interpretation (tmp_Grade_A_sorted[sample_or_site],self.accept_new_parameters)
                            sample_int_interval_uT=sample_acceptable_max-sample_acceptable_min
                            sample_int_interval_perc=100*((sample_acceptable_max-sample_acceptable_min)/best_mean)       

                            # check if interpretation pass criteria (if yes ignore the specimens). if no, keep it the old way:
                            if ( self.accept_new_parameters['sample_int_sigma_uT'] ==0 and self.accept_new_parameters['sample_int_sigma_perc']==0 ) or \
                               (best_std <= self.accept_new_parameters['sample_int_sigma_uT'] or 100*(best_std/best_mean) <= self.accept_new_parameters['sample_int_sigma_perc']):
                                if sample_int_interval_uT <= self.accept_new_parameters['sample_int_interval_uT'] or sample_int_interval_perc <= self.accept_new_parameters['sample_int_interval_perc']:
                                    Grade_A_sorted[sample_or_site]=copy.deepcopy(tmp_Grade_A_sorted[sample_or_site])
                                    WARNING=WARNING_tmp
                                    thellier_interpreter_log.write(warning_messeage)

                                
            #--------------------------------------------------------------
            # check for outlier specimens
            # Outlier check is done only if
            # (1) number of specimen >= accept_new_parameters['sample_int_n_outlier_check']
            # (2) an outlier exists if one (and only one!) specimen has an outlier result defined
            # by:
            # Bmax(specimen_1) < mean[max(specimen_2),max(specimen_3),max(specimen_3)...] - 2*sigma
            # or
            # Bmin(specimen_1) < mean[min(specimen_2),min(specimen_3),min(specimen_3)...] + 2*sigma
            # (3) 2*sigma > 5 microT
            #--------------------------------------------------------------

            WARNING=""
            # check for outlier specimen
            exclude_specimen=""
            exclude_specimens_list=[]
            if len(Grade_A_sorted[sample_or_site].keys())>=float(self.accept_new_parameters['sample_int_n_outlier_check']):
                thellier_interpreter_log.write( "-I- check outlier for sample %s \n"%sample)
                all_specimens=Grade_A_sorted[sample_or_site].keys()
                for specimen in all_specimens:
                    B_min_array,B_max_array=[],[]
                    for specimen_b in all_specimens:
                        if specimen_b==specimen: continue
                        B_min_array.append(min(Grade_A_sorted[sample_or_site][specimen_b]))
                        B_max_array.append(max(Grade_A_sorted[sample_or_site][specimen_b]))
                    if max(Grade_A_sorted[sample_or_site][specimen]) < (mean(B_min_array) - 2*std(B_min_array,ddof=1)):# and 2*std(B_min_array,ddof=1) >3.:
                        if specimen not in exclude_specimens_list:
                            exclude_specimens_list.append(specimen)
                    if min(Grade_A_sorted[sample_or_site][specimen]) > (mean(B_max_array) + 2*std(B_max_array,ddof=1)):# and 2*std(B_max_array,ddof=1) >3 :
                           if specimen not in exclude_specimens_list:
                            exclude_specimens_list.append(specimen)
                         
                if len(exclude_specimens_list)>1:
                    thellier_interpreter_log.write( "-I- specimen %s outlier check: more than one specimen can be outlier. first ones are : %s,%s... \n" %(sample,exclude_specimens_list[0],exclude_specimens_list[1]))
                    exclude_specimens_list=[]

                if len(exclude_specimens_list)==1 :
                    #print exclude_specimens_list
                    exclude_specimen=exclude_specimens_list[0]
                    del Grade_A_sorted[sample_or_site][exclude_specimen]
                    thellier_interpreter_log.write( "-W- WARNING: specimen %s is exluded from sample %s because of an outlier result.\n"%(exclude_specimens_list[0],sample))
                    WARNING=WARNING+"excluding specimen %s; "%(exclude_specimens_list[0])





                                        
            
            #--------------------------------------------------------------
            #  display all the specimens that passes criteria  after the interpreter ends running.
            #--------------------------------------------------------------


            # if only one specimen pass take the interpretation with maximum frac
            if len(Grade_A_sorted[sample_or_site].keys()) == 1:
                specimen=Grade_A_sorted[sample_or_site].keys()[0]
                frac_max=0
                for TEMP in All_grade_A_Recs[specimen].keys():
                    if All_grade_A_Recs[specimen][TEMP]['specimen_frac']>frac_max:
                        best_intensity=All_grade_A_Recs[specimen][TEMP]['specimen_int_uT']
                for TEMP in All_grade_A_Recs[specimen].keys():                        
                    if All_grade_A_Recs[specimen][TEMP]['specimen_int_uT']==best_intensity:
                        self.Data[specimen]['pars'].update(All_grade_A_Recs[specimen][TEMP])
                        self.Data[specimen]['pars']['saved']=True
                        sample=self.Data_hierarchy['specimens'][specimen]
                        if sample not in self.Data_samples.keys():
                          self.Data_samples[sample]={}
                        self.Data_samples[sample][specimen]=self.Data[specimen]['pars']['specimen_int_uT']

                        site=self.get_site_from_hierarchy(sample)
                        if site not in self.Data_sites.keys():
                          self.Data_sites[site]={}
                        self.Data_sites[site][specimen]=self.Data[specimen]['pars']['specimen_int_uT']

                                                
            if len(Grade_A_sorted[sample_or_site].keys()) > 1:
                Best_interpretations,best_mean,best_std=find_sample_min_std(Grade_A_sorted[sample_or_site])
                for specimen in Grade_A_sorted[sample_or_site].keys():
                    for TEMP in All_grade_A_Recs[specimen].keys():
                        if All_grade_A_Recs[specimen][TEMP]['specimen_int_uT']==Best_interpretations[specimen]:
                            self.Data[specimen]['pars'].update(All_grade_A_Recs[specimen][TEMP])
                            self.Data[specimen]['pars']['saved']=True
                            sample=self.Data_hierarchy['specimens'][specimen]
                            if sample not in self.Data_samples.keys():
                              self.Data_samples[sample]={}
                            self.Data_samples[sample][specimen]=self.Data[specimen]['pars']['specimen_int_uT']
                            site=self.get_site_from_hierarchy(sample)
                            if site not in self.Data_sites.keys():
                                self.Data_sites[site]={}
                            self.Data_sites[site][specimen]=self.Data[specimen]['pars']['specimen_int_uT']
                            

             #--------------------------------------------------------------
             # check if ATRM and cooling rate data exist
             #--------------------------------------------------------------


            if self.accept_new_parameters['sample_int_stdev_opt']:
                n_anistropy=0
                n_anistropy_fail=0
                n_anistropy_pass=0
                for specimen in Grade_A_sorted[sample_or_site].keys():
                    if "AniSpec" in self.Data[specimen].keys():
                        n_anistropy+=1
                        if 'pars' in self.Data[specimen].keys() and "AC_WARNING" in  self.Data[specimen]['pars'].keys():
                            #if "F-test" in self.Data[specimen]['pars']["AC_WARNING"] \
                            if  self.Data[specimen]['pars']["AC_anisotropy_type"]=='ATRM' and "alteration" in self.Data[specimen]['pars']["AC_WARNING"]:
                                n_anistropy_fail+=1
                            else:
                                n_anistropy_pass+=1
                               
                                 
                            
                no_cooling_rate=True
                n_cooling_rate=0
                n_cooling_rate_pass=0
                n_cooling_rate_fail=0
                
                for specimen in Grade_A_sorted[sample_or_site].keys():
                        if "cooling_rate_data" in self.Data[specimen].keys():
                            n_cooling_rate+=1
                            if "CR_correction_factor" in self.Data[specimen]["cooling_rate_data"].keys():
                                if self.Data[specimen]["cooling_rate_data"]["CR_correction_factor"]!= -1 and self.Data[specimen]["cooling_rate_data"]["CR_correction_factor"]!= -999:
                                    no_cooling_rate=False
                                if 'CR_correction_factor_flag' in self.Data[specimen]["cooling_rate_data"].keys():
                                    if 'calculated' in self.Data[specimen]['cooling_rate_data']['CR_correction_factor_flag']:
                                        n_cooling_rate_pass+=1
                                    elif 'failed'  in self.Data[specimen]['cooling_rate_data']['CR_correction_factor_flag']:
                                        n_cooling_rate_fail+=1 
                                
 
             #--------------------------------------------------------------
             # calcuate STDEV-OPT 'best means' and write results to files
             #--------------------------------------------------------------
    
                if len(Grade_A_sorted[sample_or_site].keys())>=self.accept_new_parameters['sample_int_n'] and len(Grade_A_sorted[sample_or_site].keys()) > 1:
                    Best_interpretations,best_mean,best_std=find_sample_min_std(Grade_A_sorted[sample_or_site])
                    sample_acceptable_min,sample_acceptable_min_std,sample_acceptable_max,sample_acceptable_max_std = find_sample_min_max_interpretation (Grade_A_sorted[sample_or_site],self.accept_new_parameters)
                    sample_int_interval_uT=sample_acceptable_max-sample_acceptable_min
                    sample_int_interval_perc=100*((sample_acceptable_max-sample_acceptable_min)/best_mean)       
                    TEXT= "-I- sample %s 'STDEV-OPT interpretation: "%sample
                    for ss in Best_interpretations.keys():
                        TEXT=TEXT+"%s=%.1f, "%(ss,Best_interpretations[ss])
                    thellier_interpreter_log.write(TEXT+"\n")
                    thellier_interpreter_log.write("-I- sample %s STDEV-OPT mean=%f, STDEV-OPT std=%f \n"%(sample,best_mean,best_std))
                    thellier_interpreter_log.write("-I- sample %s STDEV-OPT minimum/maximum accepted interpretation  %.2f,%.2f\n" %(sample,sample_acceptable_min,sample_acceptable_max))


                    # check if interpretation pass criteria for samples:
                    if ( self.accept_new_parameters['sample_int_sigma_uT'] ==0 and self.accept_new_parameters['sample_int_sigma_perc']==0 ) or \
                       (best_std <= self.accept_new_parameters['sample_int_sigma_uT'] or 100*(best_std/best_mean) <= self.accept_new_parameters['sample_int_sigma_perc']):
                        if sample_int_interval_uT <= self.accept_new_parameters['sample_int_interval_uT'] or sample_int_interval_perc <= self.accept_new_parameters['sample_int_interval_perc']:
                            # write the interpretation to a redo file
                            for specimen in Grade_A_sorted[sample_or_site].keys():
                                #print Redo_data_specimens[specimen]
                                for TEMP in All_grade_A_Recs[specimen].keys():
                                    if All_grade_A_Recs[specimen][TEMP]['specimen_int_uT']==Best_interpretations[specimen]:
                                        t_min=All_grade_A_Recs[specimen][TEMP]['measurement_step_min']
                                        t_max=All_grade_A_Recs[specimen][TEMP]['measurement_step_max']
                                        
                                            
                                        Fout_STDEV_OPT_redo.write("%s\t%i\t%i\n"%(specimen,t_min,t_max))

                                    # write the interpretation to the specimen file
                                        #B_lab=float(Redo_data_specimens[specimen][Best_interpretations[specimen]]['lab_dc_field'])*1e6
                                        B_lab=float(All_grade_A_Recs[specimen][TEMP]['lab_dc_field'])*1e6
                                        sample=All_grade_A_Recs[specimen][TEMP]['er_sample_name']
                                        if "Anisotropy_correction_factor" in All_grade_A_Recs[specimen][TEMP].keys():
                                            Anisotropy_correction_factor="%.2f"%(All_grade_A_Recs[specimen][TEMP]["Anisotropy_correction_factor"])
                                            #AC_correction_type=pars["AC_anisotropy_type"]
                                        #if 'AC_specimen_correction_factor' in All_grade_A_Recs[specimen][TEMP].keys():
                                        #    Anisotropy_correction_factor="%.2f"%float(All_grade_A_Recs[specimen][TEMP]['AC_specimen_correction_factor'])
                                        else:
                                            Anisotropy_correction_factor="-"                
                                        if  All_grade_A_Recs[specimen][TEMP]["NLT_specimen_correction_factor"] != -1:
                                            NLT_correction_factor="%.2f"%float(All_grade_A_Recs[specimen][TEMP]['NLT_specimen_correction_factor'])
                                        else:
                                            NLT_correction_factor="-"

                                        if  All_grade_A_Recs[specimen][TEMP]["specimen_int_corr_cooling_rate"] != -999 and All_grade_A_Recs[specimen][TEMP]["specimen_int_corr_cooling_rate"] != -1:
                                            CR_correction_factor="%.2f"%float(All_grade_A_Recs[specimen][TEMP]['specimen_int_corr_cooling_rate'])
                                        else:
                                            CR_correction_factor="-"

                                        Fout_STDEV_OPT_specimens.write("%s\t%s\t%.2f\t%i\t%i\t%.0f\t%s\t%s\t%s\t"\
                                                             %(sample_or_site,specimen,float(Best_interpretations[specimen]),t_min-273,t_max-273,B_lab,Anisotropy_correction_factor,NLT_correction_factor,CR_correction_factor))
                                        String=""
                                        for key in accept_specimen_keys:
                                            String=String+"%.2f"%(All_grade_A_Recs[specimen][TEMP][key])+"\t"
                                        Fout_STDEV_OPT_specimens.write(String[:-1]+"\n")
                                                     
                            # write the interpretation to the sample file
                          
                            if n_anistropy == 0:
                                 WARNING=WARNING+"No anisotropy corrections; "
                            else:    
                                 WARNING=WARNING+"%i / %i specimens pass anisotropy criteria; "%(int(n_anistropy)-int(n_anistropy_fail),int(n_anistropy))
                            
                            if no_cooling_rate:
                                 WARNING=WARNING+" No cooling rate corrections; "
                            else:
                                 WARNING=WARNING+ "%i / %i specimens pass cooling rate criteria ;"%(int(n_cooling_rate_pass),int(n_cooling_rate))
                                                      
                            String="%s\t%i\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.3f\t%.2f\t%.2f\t%s\n"%\
                            (sample_or_site,len(Best_interpretations),best_mean,best_std,100*(best_std/best_mean),\
                            sample_acceptable_min,sample_acceptable_min_std,
                            sample_acceptable_max,sample_acceptable_max_std,\
                            sample_int_interval_uT,sample_int_interval_perc,WARNING)
                            if self.accept_new_parameters['average_by_sample_or_site']=='sample':
                                Fout_STDEV_OPT_samples.write(String)
                            else:
                                Fout_STDEV_OPT_sites.write(String)
                                
                        else:
                         thellier_interpreter_log.write("-I- sample %s FAIL on sample_int_interval_uT or sample_int_interval_perc\n"%sample)                    
                    else:
                         thellier_interpreter_log.write("-I- sample %s FAIL on sample_int_sigma_uT or sample_int_sigma_perc\n"%sample)
                                                                            
        #--------------------------------------------------------------
        # calcuate Bootstarp and write results to files
        #--------------------------------------------------------------
            if self.accept_new_parameters['sample_int_bs'] or self.accept_new_parameters['sample_int_bs_par']:
               BOOTSTRAP_N=self.preferences['BOOTSTRAP_N']
               Grade_A_samples_BS={} 
               if len(Grade_A_sorted[sample_or_site].keys()) >= self.accept_new_parameters['sample_int_n']:
                   for specimen in Grade_A_sorted[sample_or_site].keys():
                        if specimen not in Grade_A_samples_BS.keys() and len(Grade_A_sorted[sample_or_site][specimen])>0:
                           Grade_A_samples_BS[specimen]=[]
                        for B in Grade_A_samples_BS[sample][specimen]:
                           Grade_A_samples_BS[specimen].append(B)
                        Grade_A_samples_BS[specimen].sort()
                        specimen_int_max_slope_diff=max(Grade_A_samples_BS[specimen])/min(Grade_A_samples_BS[specimen])
                        if specimen_int_max_slope_diff>self.accept_new_parameters['specimen_int_max_slope_diff']:
                           thellier_interpreter_log.write( "-I- specimen %s Failed specimen_int_max_slope_diff\n"%specimen,Grade_A_samples_BS[specimen])
                           del Grade_A_samples_BS[specimen]
                
               if len(Grade_A_samples_BS.keys())>=self.accept_new_parameters['sample_int_n']:
        
                   BS_means_collection=[]
                   for i in range(BOOTSTRAP_N):
                       B_BS=[]
                       for j in range(len(Grade_A_samples_BS.keys())):
                           LIST=list(Grade_A_samples_BS.keys())
                           specimen=random.choice(LIST)
                           if self.accept_new_parameters['sample_int_bs']:
                               B=random.choice(Grade_A_samples_BS[specimen])
                           if self.accept_new_parameters['sample_int_bs_par']:
                               B=random.uniform(min(Grade_A_samples_BS[specimen]),max(Grade_A_samples_BS[specimen]))
                           B_BS.append(B)
                       BS_means_collection.append(mean(B_BS))
                       
                   BS_means=array(BS_means_collection)
                   BS_means.sort()
                   sample_median=median(BS_means)
                   sample_std=std(BS_means,ddof=1)
                   sample_68=[BS_means[(0.16)*len(BS_means)],BS_means[(0.84)*len(BS_means)]]
                   sample_95=[BS_means[(0.025)*len(BS_means)],BS_means[(0.975)*len(BS_means)]]


                   thellier_interpreter_log.write( "-I-  bootstrap mean sample %s: median=%f, std=%f\n"%(sample,sample_median,sample_std))
                   String="%s\t%i\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t%s\n"%\
                           (sample,len(Grade_A_samples_BS[sample].keys()),sample_median,sample_68[0],sample_68[1],sample_95[0],sample_95[1],sample_std,100*(sample_std/sample_median),WARNING)
                   if self.accept_new_parameters['sample_int_bs']:
                       Fout_BS_samples.write(String)
                   if self.accept_new_parameters['sample_int_bs_par']:
                       Fout_BS_PAR_samples.write(String)


                                                  
        
        thellier_interpreter_log.write( "-I- Statistics:\n")
        thellier_interpreter_log.write( "-I- number of specimens analzyed = %i\n" % len(specimens_list)  )
        thellier_interpreter_log.write( "-I- number of sucsessful 'acceptable' specimens = %i\n" % len(All_grade_A_Recs.keys()))   

        runtime_sec = time.time() - start_time
        m, s = divmod(runtime_sec, 60)
        h, m = divmod(m, 60)
        thellier_interpreter_log.write( "-I- runtime hh:mm:ss is " + "%d:%02d:%02d\n" % (h, m, s))
        thellier_interpreter_log.write( "-I- Finished sucsessfuly.\n")
        thellier_interpreter_log.write( "-I- DONE\n")


        # close all files

        thellier_interpreter_log.close()
        thellier_interpreter_all.close()
        Fout_specimens_bounds.close()
        if self.accept_new_parameters['sample_int_stdev_opt']: 
            Fout_STDEV_OPT_redo.close()
            Fout_STDEV_OPT_specimens.close()
        if self.accept_new_parameters['average_by_sample_or_site']=='sample':
            Fout_STDEV_OPT_samples.close()
        else:
             Fout_STDEV_OPT_sites.close()
           
        if self.accept_new_parameters['sample_int_bs']:
            Fout_BS_samples.close()
        if self.accept_new_parameters['sample_int_bs_par']:
            Fout_BS_PAR_samples.close()
            
        os.system('\a')
        dlg1 = wx.MessageDialog(self,caption="Message:", message="Interpreter finished sucsessfuly\nCheck output files in folder /thellier_interpreter in the current project directory" ,style=wx.OK|wx.ICON_INFORMATION)


        # display the interpretation of the current specimen:
        self.pars=self.Data[self.s]['pars']
        self.clear_boxes()
        self.draw_figure(self.s)
        self.update_GUI_with_new_interpretation()


        dlg1.ShowModal()
        dlg1.Destroy()
        busy_frame.Destroy()
    #----------------------------------------------------------------------

    def on_menu_open_interpreter_file(self, event):
        try:
            dirname=self.WD + "/thellier_interpreter"
        except:
            dirname=self.WD
            
        dlg = wx.FileDialog(self, "Choose an auto-interpreter output file", dirname, "", "*.*", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            path=dlg.GetPath()
        #print  filename
        #print path
        if "samples" in filename or "bounds" in filename:
            ignore_n=4

        elif "specimens" in filename or "all" in filename:
            ignore_n=1
        else:
            return()
        self.frame=MyForm(ignore_n,path)
        self.frame.Show()

    #----------------------------------------------------------------------
      
    def on_menu_open_interpreter_log(self, event):
        dia = MyLogFileErrors( "Interpreter errors and warnings","%s/thellier_interpreter/thellier_interpreter.log"%(self.WD))
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
                  try:
                      self.Data[specimen]['pars']=self.get_PI_parameters(specimen,float(tmin_kelvin),float(tmax_kelvin))
                      self.Data[specimen]['pars']['saved']=True
                      # write intrepretation into sample data
                      sample=self.Data_hierarchy['specimens'][specimen]
                      if sample not in self.Data_samples.keys():
                          self.Data_samples[sample]={}
                      self.Data_samples[sample][specimen]=self.Data[specimen]['pars']['specimen_int_uT']
                      site=self.get_site_from_hierarchy(sample)
                      if site not in self.Data_sites.keys():
                          self.Data_sites[site]={}
                      self.Data_sites[site][specimen]=self.Data[specimen]['pars']['specimen_int_uT']

                  
                  except:
                      self.GUI_log.write ("-E- ERROR. Cant calculate PI paremeters for specimen %s using redo file. Check!"%(specimen))
          else:
              self.GUI_log.write ("-W- WARNING: Cant find specimen %s from redo file in measurement file!\n"%specimen)
        fin.close()
        self.pars=self.Data[self.s]['pars']
        self.clear_boxes()
        self.draw_figure(self.s)
        self.update_GUI_with_new_interpretation()

    #----------------------------------------------------------------------            

    def write_acceptance_criteria_to_file(self):
        import copy
        """
        Write new acceptance criteria to pmag_criteria.txt
        """
        # check if an old pmag_criteria.txt exist:
        other_criteria={}
        try:
            fin=open(self.WD+"/"+"pmag_criteria.txt",'rU')
            lines=""
            line=fin.readline()
            line=fin.readline()
            header=line.strip('\n').split()
            code_index=header.index("pmag_criteria_code")

            for line in fin.readlines():
                code=line[code_index]
                if "IE-" not in code:
                    for i in range(len(header)):
                        if line[i]!="":
                            try:
                                float(line[i])
                            except:
                                continue
                            other_criteria[code][header[i]]=float(line[i])
        except:
             pass
            

            
        fout=open(self.WD+"/"+"pmag_criteria.txt",'w')
        String="tab\tpmag_criteria\n"
        fout.write(String)
        specimen_criteria_list=self.criteria_list+["specimen_int_max_slope_diff"]+['check_aniso_ftest']+['anisotropy_alt']
        sample_criteria_list=[key for key in self.accept_new_parameters.keys() if "sample" in key]
        if self.accept_new_parameters['sample_int_stdev_opt'] == True:                                      
            for k in ['sample_int_bs','sample_int_bs_par','sample_int_BS_68_uT','sample_int_BS_68_perc','sample_int_BS_95_uT','sample_int_BS_95_perc']:
                sample_criteria_list.remove(k)
                if "specimen_int_max_slope_diff" in specimen_criteria_list:
                    specimen_criteria_list.remove("specimen_int_max_slope_diff")

        else:
            for k in ['sample_int_sigma_uT','sample_int_sigma_perc','sample_int_interval_uT','sample_int_stdev_opt','sample_aniso_threshold_perc']:
                sample_criteria_list.remove(k)
        for k in ['sample_int_sigma_uT','sample_int_sigma_perc','sample_int_interval_uT','sample_int_interval_perc','sample_aniso_threshold_perc','sample_int_BS_68_uT','sample_int_BS_68_perc','sample_int_BS_95_uT','sample_int_BS_95_perc',]:
            if  k in sample_criteria_list:
                if float(self.accept_new_parameters[k]) > 999:
                    sample_criteria_list.remove(k)
        if  float(self.accept_new_parameters["sample_int_n_outlier_check"])> 99:
            sample_criteria_list.remove("sample_int_n_outlier_check")

        if "sample_int_sigma_uT"  in sample_criteria_list and "sample_int_sigma" not in sample_criteria_list:
            sample_criteria_list.append("sample_int_sigma")
            self.accept_new_parameters["sample_int_sigma"]=float(self.accept_new_parameters["sample_int_sigma_uT"])*1e-6
        
        if "specimen_int_max_slope_diff" in  specimen_criteria_list:
            if float(self.accept_new_parameters['specimen_int_max_slope_diff'])>999:
                specimen_criteria_list.remove("specimen_int_max_slope_diff")
        c_list=copy.copy(specimen_criteria_list)       
        for criteria in c_list:
            if criteria in (self.high_threshold_velue_list + ['anisotropy_alt']) and float(self.accept_new_parameters[criteria])>100:
                specimen_criteria_list.remove(criteria)
            #if criteria in ['specimen_g'] and float(self.accept_new_parameters[criteria])>100:
            if criteria in self.low_threshold_velue_list and float(self.accept_new_parameters[criteria])<0.1:
                specimen_criteria_list.remove(criteria)                

        # special treatment for sample and site criteria:
        header="pmag_criteria_code\t"
        for i in range(len(sample_criteria_list)):
            key=sample_criteria_list[i]
            if key in ['average_by_sample_or_site','sample_int_sigma_uT','sample_int_stdev_opt','sample_int_n_outlier_check']:
                continue
            # special treatment for sample and site criteria:        
            if self.accept_new_parameters['average_by_sample_or_site']=='site':
                if key == 'sample_int_n' or key == "sample_int_n": key='site_int_nn'
                if key == 'sample_int_sigma' or key == "sample_int_sigma": key='site_int_sigma'
                if key == 'sample_int_sigma_perc' or key == "sample_int_sigma_perc": key='site_int_sigma_perc'
            header=header+key+"\t"
        for key in specimen_criteria_list:
            header=header+key+"\t"
        header=header+"specimen_scat\t"

        # other criteria (not paleointensity)
        for code in other_criteria.keys():
            for key in other_criteria[code].keys():
                header=header+key+"\t"
        fout.write(header[:-1]+"\n")
                    
        line="IE-SPEC:IE-SAMP\t"
        for key in sample_criteria_list:
            if key in['average_by_sample_or_site','sample_int_sigma_uT','sample_int_stdev_opt','sample_int_n_outlier_check']:
                continue
            if key in ['sample_int_bs','sample_int_bs_par','sample_int_stdev_opt','check_aniso_ftest','average_by_sample_or_site']:
                line=line+"%s"%str(self.accept_new_parameters[key])+"\t"
            elif key in ['sample_int_sigma']:
                line=line+"%.2e"%self.accept_new_parameters[key]+"\t"                
            else:
                line=line+"%f"%self.accept_new_parameters[key]+"\t"
                
        for key in specimen_criteria_list:
            if key=='check_aniso_ftest':
                line=line+str(self.accept_new_parameters[key])+"\t"
            else:    
                line=line+"%f"%self.accept_new_parameters[key]+"\t"
        if self.accept_new_parameters["specimen_scat"]:
            line=line+"True"+"\t"
        else:
            line=line+"False"+"\t"

        # other criteria (not paleointensity)
        for code in other_criteria.keys():
            for key in other_criteria[code].keys():
                line=line+other_criteria[code][key]+"\t"
    
        fout.write(line[:-1]+"\n")
        fout.close()
            
    #----------------------------------------------------------------------            

    def on_menu_run_optimizer(self, event):
        self.GUI_log.write ("-I- running thellier consistency test\n")
        import  thellier_consistency_test

        Consistency_Test(self.Data,self.Data_hierarchy,self.WD,self.accept_new_parameters_default)

    def on_menu_run_consistency_test_b(self, event):
        self.GUI_log.write ("-I- running thellier consistency test beta version\n")
        print "not supported yet"
        pass        
    #----------------------------------------------------------------------            

    def on_menu_plot_data (self, event):
        #Plot_Dialog(None,self.WD,self.Data,self.Data_info)

        
        dia = Plot_Dialog(None,self.WD,self.Data,self.Data_info)
        dia.Center()
        #result = dia.ShowModal()

        #if result == wx.ID_OK: # Until the user clicks OK, show the message
        #    self.On_close_criteria_box(dia)
        
        if dia.ShowModal() == wx.ID_OK: # Until the user clicks OK, show the message            
            self.On_close_plot_dialog(dia)
        
    #----------------------------------------------------------------------            

    def on_menu_results_data (self, event):
        import copy
        
        #----------------------------------------------------
        # Easy tables with the results of all the samples or site that passed the criteria
        #----------------------------------------------------
        
        # search for ages and Latitudes
        if self.accept_new_parameters['average_by_sample_or_site']=='sample':
            BY_SITES=False; BY_SAMPLES=True
        else:
            BY_SITES=True; BY_SAMPLES=False        
        
        if BY_SAMPLES:
            Data_samples_or_sites=copy.deepcopy(self.Data_samples)
        else:
            Data_samples_or_sites=copy.deepcopy(self.Data_sites)
        samples_or_sites_list=Data_samples_or_sites.keys()
        samples_or_sites_list.sort()
        Results_table_data={}

        if self.accept_new_parameters['average_by_sample_or_site']=='sample':
            BY_SITES=False; BY_SAMPLES=True
        else:
            BY_SITES=True; BY_SAMPLES=False        
        
        for sample_or_site in samples_or_sites_list:

            Age,age_unit,age_range_low,age_range_high="","","",""
            lat,lon,VADM,VADM_sigma="","","",""

            found_age,found_lat=False,False

            # Find the mean paleointenisty for each sample
            tmp_B=[]
            for spec in Data_samples_or_sites[sample_or_site].keys():
                tmp_B.append( Data_samples_or_sites[sample_or_site][spec])
            if len(tmp_B)<1:
                continue
            tmp_B=array(tmp_B)
            B_uT=mean(tmp_B)
            B_std_uT=std(tmp_B,ddof=1)
            B_std_perc=100*(B_std_uT/B_uT)
            
            # check if sample passed the criteria
            sample_pass_criteria=False
            if len(tmp_B)>=self.accept_new_parameters['sample_int_n']:
                if (self.accept_new_parameters['sample_int_sigma_uT']==0 and self.accept_new_parameters['sample_int_sigma_perc']==0) or\
                   ( B_std_uT <=self.accept_new_parameters['sample_int_sigma_uT'] or B_std_perc <= self.accept_new_parameters['sample_int_sigma_perc']):
                    if ( (max(tmp_B)-min(tmp_B)) <= self.accept_new_parameters['sample_int_interval_uT'] or 100*((max(tmp_B)-min(tmp_B))/mean((tmp_B))) <= self.accept_new_parameters['sample_int_interval_perc']):
                        sample_pass_criteria=True

            if not sample_pass_criteria:
                continue

            Results_table_data[sample_or_site]={}
            
            # search for samples age in er_ages.txt by sample or by site
            if BY_SAMPLES:
                site = self.Data_info["er_samples"][sample_or_site]['er_site_name']
            else:
                site=sample_or_site
            found_age=False
            if sample_or_site in self.Data_info["er_ages"].keys():
                age_key=sample_or_site
            elif site in self.Data_info["er_ages"].keys():
                age_key=site
            else:
                age_key=""
            if age_key !="":
                try:
                    age_unit=self.Data_info["er_ages"][age_key]["age_unit"]                
                except:
                    age_unit="unknown"               
                    
                if self.Data_info["er_ages"][age_key]["age"] !="":
                    Age = float(self.Data_info["er_ages"][age_key]["age"])
                    found_age=True
                    
                if "age_range_low" in self.Data_info["er_ages"][age_key].keys() and "age_range_high" in self.Data_info["er_ages"][age_key].keys():
                   age_range_low=float(self.Data_info["er_ages"][age_key]["age_range_low"])
                   age_range_high=float(self.Data_info["er_ages"][age_key]["age_range_high"])
                   
                   if not found_age:
                       Age=(age_range_low+age_range_high)/2
                       found_age=True

                elif "age_sigma" in self.Data_info["er_ages"][age_key].keys() and found_age:
                   age_range_low=Age-float(self.Data_info["er_ages"][age_key]["age_sigma"])
                   age_range_high= Age+float(self.Data_info["er_ages"][age_key]["age_sigma"])

                elif found_age:
                   age_range_low=Age
                   age_range_high=Age

            # convert ages from Years BP to Years Cal AD (+/-)
                if "Years BP" in age_unit:
                    Age=1950-Age
                    age_range_low=1950-age_range_low
                    age_range_high=1950-age_range_high
                    age_unit="Years Cal AD (+/-)"             
            
            # search for Lon/Lat

            if BY_SAMPLES and sample_or_site in self.Data_info["er_samples"].keys() and "site_lat" in self.Data_info["er_samples"][sample_or_site].keys():
                lat=float(self.Data_info["er_samples"][sample_or_site]["site_lat"])
                lon=float(self.Data_info["er_samples"][sample_or_site]["site_lon"])
                found_lat=True
                
            elif site in self.Data_info["er_sites"].keys() and "site_lat" in self.Data_info["er_sites"][site].keys():
                lat=float(self.Data_info["er_sites"][site]["site_lat"])
                lon=float(self.Data_info["er_sites"][site]["site_lon"])
                found_lat=True

            if found_lat:
                VADM=self.b_vdm(B_uT*1e-6,lat)*1e-21
                VADM_plus=self.b_vdm((B_uT+B_std_uT)*1e-6,lat)*1e-21
                VADM_minus=self.b_vdm((B_uT-B_std_uT)*1e-6,lat)*1e-21
                VADM_sigma=(VADM_plus-VADM_minus)/2
                
            Results_table_data[sample_or_site]["N"]="%i"%(len(tmp_B))            
            Results_table_data[sample_or_site]["B_uT"]="%.1f"%(B_uT)
            Results_table_data[sample_or_site]["B_std_uT"]="%.1f"%(B_std_uT)
            Results_table_data[sample_or_site]["B_std_perc"]="%.1f"%(B_std_perc)
            if found_lat:
                Results_table_data[sample_or_site]["Lat"]="%f"%lat
                Results_table_data[sample_or_site]["Lon"]="%f"%lon
                Results_table_data[sample_or_site]["VADM"]="%.1f"%VADM
                Results_table_data[sample_or_site]["VADM_sigma"]="%.1f"%VADM_sigma
            else:
                Results_table_data[sample_or_site]["Lat"]=""
                Results_table_data[sample_or_site]["Lon"]=""
                Results_table_data[sample_or_site]["VADM"]=""
                Results_table_data[sample_or_site]["VADM_sigma"]=""
            if found_age:
                Results_table_data[sample_or_site]["Age"]="%.2f"%Age
                Results_table_data[sample_or_site]["Age_low"]="%.2f"%age_range_low
                Results_table_data[sample_or_site]["Age_high"]="%.2f"%age_range_high
            else:
                Results_table_data[sample_or_site]["Age"]=""
                Results_table_data[sample_or_site]["Age_low"]=""
                Results_table_data[sample_or_site]["Age_high"]=""
            Results_table_data[sample_or_site]["Age_units"]=age_unit
                
        sample_or_site_list= Results_table_data.keys()
        sample_or_site_list.sort()
        if len(sample_or_site_list) <1:
            return
                        
        fout=open(self.WD+"/results_table.txt",'w')
        Keys=["sample/site","Lat","Lon","Age","Age_low","Age_high","Age_units","N","B_uT","B_std_uT","VADM","VADM_sigma"]
        fout.write("\t".join(Keys)+"\n")
        for sample_or_site in sample_or_site_list:
            String=sample_or_site+"\t"
            for k in Keys[1:]:
                String=String+Results_table_data[sample_or_site][k]+"\t"
            fout.write(String[:-1]+"\n")
        fout.close()


#        #----------------------------------------------------------------------------
#        # Easy tables with the results of all the specimens that passed the criteria
#        #----------------------------------------------------------------------------
#
#        fout=open(self.WD+"/results_table_specimmens.txt",'w')
#        Keys=["specimen","B_raw","B_corrected","ATRM","CR","NLT"]
#        for 
#        fout.write("\t".join(Keys)+"\n")
#        
#        for sample_or_site in samples_or_sites_list:
#            specimens_list=samples_or_sites_list.keys()
#            specimens_list.sort()
#            if len(specimens_list) <1:
#                continue
#            for specimen in specimens_list:
#                if 'specimen_fail_criteria' not in self.Data[specimen]['pars'].keys():
#                    continue
#                if len(self.Data[specimen]['pars']['specimen_fail_criteria'])>0:
#                    continue
#                keys=["sample/site","Lat","Lon","Age","Age_low","Age_high","Age_units","N","B_uT","B_std_uT","VADM","VADM_sigma"]:
#                    for key in Keys:
#                         Results_table_data_specimens[specimen]   
#                    
                


        dlg1 = wx.MessageDialog(self,caption="Message:", message="Output results table is saved in 'results_table.txt'" ,style=wx.OK|wx.ICON_INFORMATION)
        dlg1.ShowModal()
        dlg1.Destroy()
            
        return

    #----------------------------------------------------------------------            

    def on_menu__prepare_MagIC_results_tables (self, event):

        import copy
        #read MagIC model
        fail_read_magic_model_files=self.read_magic_model()
        if len(fail_read_magic_model_files)>0:
            for F in fail_read_magic_model_files:
                print "-E- Failed reading MagIC Model file %s"%F
            return
        
        #------------------
        # read "old" pmag results data and sort out directional data
        # this data will be marged later with os.
        PmagRecsOld={}
        for FILE in ['pmag_specimens.txt','pmag_samples.txt','pmag_sites.txt','pmag_results.txt']:
            PmagRecsOld[FILE],meas_data=[],[]
            try: 
                meas_data,file_type=pmag.magic_read(self.WD+"/"+FILE)
                self.GUI_log.write("-I- Read old magic file  %s\n"%(self.WD+"/"+FILE))
                #if FILE !='pmag_specimens.txt':
                os.rename(self.WD+"/"+FILE,self.WD+"/"+FILE+".backup")
                self.GUI_log.write("-I- rename old magic file  %s.backup\n"%(self.WD+"/"+FILE))
            except:
                continue                                                                           
            for rec in meas_data:
                if "magic_method_codes" in rec.keys():
                    if "LP-PI" not in rec['magic_method_codes'] and "IE" not in rec['magic_method_codes'] :
                        PmagRecsOld[FILE].append(rec)
            #PmagRecsOld[FILE]=self.converge_pmag_rec_headers(PmagRecsOld[FILE])
        pmag_specimens_header_1=["er_location_name","er_site_name","er_sample_name","er_specimen_name"]
        pmag_specimens_header_2=['measurement_step_min','measurement_step_max','specimen_int']        
        pmag_specimens_header_3=["specimen_correction","specimen_int_corr_anisotropy","specimen_int_corr_nlt","specimen_int_corr_cooling_rate"]
        pmag_specimens_header_4=['specimen_int_n','specimen_int_ptrm_n','specimen_f','specimen_fvds','specimen_frac','specimen_gmax','specimen_b_beta','specimen_scat','specimen_drats','specimen_md','specimen_int_mad','specimen_dang','specimen_q','specimen_g']
        pmag_specimens_header_5=["magic_experiment_names","magic_method_codes","measurement_step_unit","specimen_lab_field_dc"]
        pmag_specimens_header_6=["er_citation_names"]
        try:
            version= pmag.get_version()
        except:
            version=""
        version=version+": thellier_gui."+CURRENT_VRSION
        for k in self.ignore_parameters.keys():
            if k in pmag_specimens_header_4 and self.ignore_parameters[k]==True:
                pmag_specimens_header_4.remove(k)

        specimens_list=[]
        for specimen in self.Data.keys():
            if 'pars' in self.Data[specimen].keys():
                if 'saved' in self.Data[specimen]['pars'].keys() and self.Data[specimen]['pars']['saved']==True:
                    specimens_list.append(specimen)
        MagIC_results_data={}
        MagIC_results_data['pmag_specimens']={}
        #if self.accept_new_parameters['average_by_sample_or_site']=='sample': 
        #    MagIC_results_data['pmag_samples']={}
        #else:
        MagIC_results_data['pmag_samples_or_sites']={}            
        MagIC_results_data['pmag_results']={}
        
        specimens_list.sort()
        #print specimens_list
        for specimen in specimens_list:
            if 'pars' in self.Data[specimen].keys() and 'saved' in self.Data[specimen]['pars'].keys() and self.Data[specimen]['pars']['saved']==True:
                MagIC_results_data['pmag_specimens'][specimen]={}
                if version!="unknown":
                    MagIC_results_data['pmag_specimens'][specimen]['magic_software_packages']=version
                MagIC_results_data['pmag_specimens'][specimen]['er_citation_names']="This study"
                #MagIC_results_data['pmag_specimens'][specimen]['er_analyst_mail_names']="unknown"
                
                MagIC_results_data['pmag_specimens'][specimen]['er_specimen_name']=specimen
                MagIC_results_data['pmag_specimens'][specimen]['er_sample_name']=self.MagIC_model["specimens"][specimen]['er_sample_name']
                MagIC_results_data['pmag_specimens'][specimen]['er_site_name']=self.MagIC_model["specimens"][specimen]['er_site_name']

                
                MagIC_results_data['pmag_specimens'][specimen]['er_location_name']=self.MagIC_model["specimens"][specimen]['er_location_name']
                MagIC_results_data['pmag_specimens'][specimen]['magic_method_codes']=self.Data[specimen]['pars']['magic_method_codes']
                tmp=MagIC_results_data['pmag_specimens'][specimen]['magic_method_codes'].split(":")
                magic_experiment_names=specimen
                for m in tmp:
                    if "LP" in m:
                        magic_experiment_names=magic_experiment_names+" : " + m
                MagIC_results_data['pmag_specimens'][specimen]['magic_experiment_names']=magic_experiment_names                
                    
                #MagIC_results_data['pmag_specimens'][specimen]['magic_instrument_codes']=""               
                MagIC_results_data['pmag_specimens'][specimen]['measurement_step_unit']='K'
                MagIC_results_data['pmag_specimens'][specimen]['specimen_lab_field_dc']="%.2e"%(self.Data[specimen]['pars']['lab_dc_field'])
                MagIC_results_data['pmag_specimens'][specimen]['specimen_correction']=self.Data[specimen]['pars']['specimen_correction']
                for key in pmag_specimens_header_4:
                    #print key
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
                if "specimen_int_corr_cooling_rate" in  self.Data[specimen]['pars'].keys():
                    MagIC_results_data['pmag_specimens'][specimen]['specimen_int_corr_cooling_rate']="%.2f"%(self.Data[specimen]['pars']['specimen_int_corr_cooling_rate'])
                else:
                    MagIC_results_data['pmag_specimens'][specimen]['specimen_int_corr_cooling_rate']=""
                    
        # wrire pmag_specimens.txt
        fout=open(self.WD+"/pmag_specimens.txt",'w')
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
        meas_data,file_type=pmag.magic_read(self.WD+"/pmag_specimens.txt")
        for rec in PmagRecsOld["pmag_specimens.txt"]:
            meas_data.append(rec)
        meas_data=self.converge_pmag_rec_headers(meas_data)
        pmag.magic_write(self.WD+"/"+"pmag_specimens.txt",meas_data,'pmag_specimens')
        os.remove(self.WD+"/pmag_specimens.txt.backup")  
        #-------------
        # pmag_samples.txt or pmag_sites.txt
        #-------------
        if self.accept_new_parameters['average_by_sample_or_site']=='sample':
            BY_SITES=False; BY_SAMPLES=True
        else:
            BY_SITES=True; BY_SAMPLES=False

        pmag_samples_header_1=["er_location_name","er_site_name"]
        if BY_SAMPLES:
           pmag_samples_header_1.append("er_sample_name")
        pmag_samples_header_2=["er_specimen_names","sample_int","sample_int_n","sample_int_sigma","sample_int_sigma_perc"]
        pmag_samples_header_3=["sample_description","magic_method_codes","magic_software_packages"]
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
                for specimen in Data_samples_or_sites[sample_or_site].keys():
                    B.append(Data_samples_or_sites[sample_or_site][specimen])
                    specimens_names=specimens_names+specimen+":"
                specimens_names=specimens_names[:-1]
                if specimens_names!="":

                    sample_pass_criteria=False
                    if len(B)>=self.accept_new_parameters['sample_int_n']:
                        B_std_uT=std(B,ddof=1)
                        B_std_perc=std(B,ddof=1)/mean(B)*100
                        if (self.accept_new_parameters['sample_int_sigma_uT']==0 and self.accept_new_parameters['sample_int_sigma_perc']==0) or\
                           ( B_std_uT <=self.accept_new_parameters['sample_int_sigma_uT'] or B_std_perc <= self.accept_new_parameters['sample_int_sigma_perc']):
                            if ( (max(B)-min(B)) <= self.accept_new_parameters['sample_int_interval_uT'] or 100*((max(B)-min(B))/mean((B))) <= self.accept_new_parameters['sample_int_interval_perc']):
                                sample_pass_criteria=True
                    if not sample_pass_criteria:
                        #print "skipping sample" %sample
                        continue
                    pmag_samples_or_sites_list.append(sample_or_site)
                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site]={}
                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site]['er_specimen_names']=specimens_names
                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site]['sample_int']="%.2e"%(mean(B)*1e-6)
                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site]['sample_int_n']="%i"%(len(B))
                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site]['sample_int_sigma']="%.2e"%(std(B,ddof=1)*1e-6)
                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site]['sample_int_sigma_perc']="%.2f"%(std(B,ddof=1)/mean(B)*100)
                    for key in pmag_samples_header_1:
                        if BY_SAMPLES:
                            MagIC_results_data['pmag_samples_or_sites'][sample_or_site][key]=self.MagIC_model["er_samples"][sample_or_site][key]
                        else:
                            MagIC_results_data['pmag_samples_or_sites'][sample_or_site][key]=self.MagIC_model["er_sites"][sample_or_site][key]
                            
                    
                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site]["pmag_criteria_codes"]=""
                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site]["sample_description"]="Mean of specimens"
                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site]['magic_method_codes']="LP-PI"
                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site]["magic_software_packages"]=version
                    
                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site]["er_citation_names"]="This study"
                   
                    
        # wrire pmag_samples.txt
        if BY_SAMPLES:
            fout=open(self.WD+"/pmag_samples.txt",'w')
            fout.write("tab\tpmag_samples\n")
        else:
            fout=open(self.WD+"/pmag_sites.txt",'w')
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
            meas_data,file_type=pmag.magic_read(self.WD+"/pmag_samples.txt")
            for rec in PmagRecsOld["pmag_samples.txt"]:
                meas_data.append(rec)
            meas_data=self.converge_pmag_rec_headers(meas_data)
            pmag.magic_write(self.WD+"/"+"pmag_samples.txt",meas_data,'pmag_samples')
            try:
                os.remove(self.WD+"/pmag_samples.backup") 
            except:
                pass     
            pmag.magic_write(self.WD+"/"+"pmag_sites.txt",PmagRecsOld["pmag_sites.txt"],'pmag_sites')
        else:
            meas_data,file_type=pmag.magic_read(self.WD+"/pmag_sites.txt")
            for rec in PmagRecsOld["pmag_sites.txt"]:
                meas_data.append(rec)
            meas_data=self.converge_pmag_rec_headers(meas_data)
            pmag.magic_write(self.WD+"/"+"pmag_sites.txt",meas_data,'pmag_sites')
            try:
                os.remove(self.WD+"/pmag_samples.backup") 
            except:
                pass     
    
            pmag.magic_write(self.WD+"/"+"pmag_samples.txt",PmagRecsOld["pmag_samples.txt"],'pmag_samples')
                                                        
        #-------------
        # pmag_results.txt
        #-------------

        pmag_results_header_1=["er_location_names","er_site_names"]
        if BY_SAMPLES:
            pmag_results_header_1.append("er_sample_names")
        pmag_results_header_2=["average_lat","average_lon",]
        pmag_results_header_3=["average_int_n","average_int","average_int_sigma","average_int_sigma_perc"]
        if self.preferences['VDM_or_VADM']=="VDM":
            pmag_results_header_4=["vdm","vdm_sigma"]        
        else:    
            pmag_results_header_4=["vadm","vadm_sigma"]
        pmag_results_header_5=[ "data_type","pmag_result_name","magic_method_codes","result_description","er_citation_names","magic_software_packages"]        
        # for ages, check the er_ages.txt, and take whats theres
        age_headers=[]
        for site in self.MagIC_model["er_ages"].keys():
            if "age" in self.MagIC_model["er_ages"][site].keys() and self.MagIC_model["er_ages"][site]["age"]!="" and "age" not in age_headers:
               age_headers.append("age")
            if "age_sigma" in self.MagIC_model["er_ages"][site].keys() and self.MagIC_model["er_ages"][site]["age_sigma"]!="" and "age_sigma" not in age_headers:
               age_headers.append("age_sigma")
            if "age_range_low" in self.MagIC_model["er_ages"][site].keys() and self.MagIC_model["er_ages"][site]["age_range_low"]!="" and "age_range_low" not in age_headers:
               age_headers.append("age_range_low")
            if "age_range_high" in self.MagIC_model["er_ages"][site].keys() and self.MagIC_model["er_ages"][site]["age_range_high"]!="" and "age_range_high" not in age_headers:
               age_headers.append("age_range_high")
            if "age_unit" in self.MagIC_model["er_ages"][site].keys() and self.MagIC_model["er_ages"][site]["age_unit"]!="" and "age_unit" not in age_headers:
               age_headers.append("age_unit")
                                             
               
        for sample_or_site in pmag_samples_or_sites_list:       
            MagIC_results_data['pmag_results'][sample_or_site]={}
            
            MagIC_results_data['pmag_results'][sample_or_site]["er_location_names"]=MagIC_results_data['pmag_samples_or_sites'][sample_or_site]['er_location_name']
            MagIC_results_data['pmag_results'][sample_or_site]["er_site_names"]=MagIC_results_data['pmag_samples_or_sites'][sample_or_site]['er_site_name']
            if BY_SAMPLES:
                MagIC_results_data['pmag_results'][sample_or_site]["er_sample_names"]=MagIC_results_data['pmag_samples_or_sites'][sample_or_site]['er_sample_name']

            site=MagIC_results_data['pmag_results'][sample_or_site]["er_site_names"]
            lat,lon="",""
            try:
                lat=self.MagIC_model["er_sites"][site]["site_lat"]
                MagIC_results_data['pmag_results'][sample_or_site]["average_lat"]=lat
            except:
                self.GUI_log.write( "-E- MagIC model error: cant find latitude for site %s, sample/site %s\n"%(site,sample_or_site))
            try:    
                lon=self.MagIC_model["er_sites"][site]["site_lon"]
                MagIC_results_data['pmag_results'][sample_or_site]["average_lon"]=lon
            except:
                self.GUI_log.write( "-E- MagIC model error: cant find longitude for site %s, sample/site %s\n"%(site,sample_or_site))

            MagIC_results_data['pmag_results'][sample_or_site]["average_lat"]=lat
            MagIC_results_data['pmag_results'][sample_or_site]["average_lon"]=lon
            
            MagIC_results_data['pmag_results'][sample_or_site]["average_int_n"]=MagIC_results_data['pmag_samples_or_sites'][sample_or_site]['sample_int_n']
            MagIC_results_data['pmag_results'][sample_or_site]["average_int"]=MagIC_results_data['pmag_samples_or_sites'][sample_or_site]['sample_int']
            MagIC_results_data['pmag_results'][sample_or_site]["average_int_sigma"]=MagIC_results_data['pmag_samples_or_sites'][sample_or_site]['sample_int_sigma']
            MagIC_results_data['pmag_results'][sample_or_site]["average_int_sigma_perc"]=MagIC_results_data['pmag_samples_or_sites'][sample_or_site]['sample_int_sigma_perc']

            if self.preferences['VDM_or_VADM']=="VDM":
                pass
                # to be done
            else:
                if lat!="":
                    lat=float(lat)
                    B=float(MagIC_results_data['pmag_samples_or_sites'][sample_or_site]['sample_int'])
                    B_sigma=float(MagIC_results_data['pmag_samples_or_sites'][sample_or_site]['sample_int_sigma'])
                    VADM=self.b_vdm(B,lat)
                    VADM_plus=self.b_vdm(B+B_sigma,lat)
                    VADM_minus=self.b_vdm(B-B_sigma,lat)
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
            MagIC_results_data['pmag_results'][sample_or_site]["magic_method_codes"]="LP-PI"
            MagIC_results_data['pmag_results'][sample_or_site]["data_type"]="a"
            MagIC_results_data['pmag_results'][sample_or_site]["er_citation_names"]="This study"
            
            
                
        # wrire pmag_results.txt
        fout=open(self.WD+"/pmag_results.txt",'w')
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
                String=String+MagIC_results_data['pmag_results'][sample_or_site][key]+"\t"
            fout.write(String[:-1]+"\n")
        fout.close()

        # merge with non-intensity data
        meas_data,file_type=pmag.magic_read(self.WD+"/pmag_results.txt")
        for rec in PmagRecsOld["pmag_results.txt"]:
            meas_data.append(rec)
        meas_data=self.converge_pmag_rec_headers(meas_data)
        pmag.magic_write(self.WD+"/"+"pmag_results.txt",meas_data,'pmag_results')
        try:
            os.remove(self.WD+"/pmag_results.backup") 
        except:
            pass     

        
        #-------------
        # MAgic_methods.txt
        #-------------

        # search for all magic_methods in all files:
        magic_method_codes=[]
        for F in ["magic_measurements.txt","rmag_anisotropy.txt","rmag_results.txt","rmag_results.txt","pmag_samples.txt","pmag_specimens.txt","pmag_sites.txt","er_ages.txt"]:
            try:
                fin=open(self.WD+"/"+F,'rU')
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
                codes=tmp[index].replace(" ","").split(":")
                for code in codes:
                    if code !="" and code not in magic_method_codes:
                        magic_method_codes.append(code)
            fin.close()
            
        magic_method_codes.sort()
        #print magic_method_codes
        magic_methods_header_1=["magic_method_code"]
        fout=open(self.WD+"/magic_methods.txt",'w')
        fout.write("tab\tmagic_methods\n")
        fout.write("magic_method_code\n")
        for code in magic_method_codes:
            fout.write("%s\n"%code)
        fout.close
                

        dlg1 = wx.MessageDialog(self,caption="Message:", message="MagIC results file are saved in MagIC project folder" ,style=wx.OK|wx.ICON_INFORMATION)
        dlg1.ShowModal()
        dlg1.Destroy()
        
        
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
                
    def read_magic_model (self):
        # Read MagIC Data model:

        self.MagIC_model={}
        self.MagIC_model["specimens"]={}
        self.MagIC_model["er_samples"]={}
        self.MagIC_model["er_sites"]={}
        self.MagIC_model["er_locations"]={}
        self.MagIC_model["er_ages"]={}
        fail=[]
        self.MagIC_model["specimens"]=self.read_magic_file(self.WD+"/er_specimens.txt",1,'er_specimen_name')
        try:
            self.MagIC_model["specimens"]=self.read_magic_file(self.WD+"/er_specimens.txt",1,'er_specimen_name')
        except:
            self.GUI_log.write ("-W- Cant find er_specimens.txt in project directory")
            fail.append("er_specimens.txt")
            pass
        try:
            self.MagIC_model["er_samples"]=self.read_magic_file(self.WD+"/er_samples.txt",1,'er_sample_name')
        except:
            self.GUI_log.write ("-W- Cant find er_sample.txt in project directory")
            fail.append("er_sample.txt")
            pass
        try:
            self.MagIC_model["er_sites"]=self.read_magic_file(self.WD+"/er_sites.txt",1,'er_site_name')
        except:
            self.GUI_log.write ("-W- Cant find er_sites.txt in project directory")
            fail.append("er_sites.txt")
            pass
        try:
            self.MagIC_model["er_locations"]=self.read_magic_file(self.WD+"/er_locations.txt",1,'er_location_name')
        except:
            self.GUI_log.write ("-W- Cant find er_locations.txt in project directory")
            fail.append("er_locations.txt")
            pass

        try:
            self.MagIC_model["er_ages"]=self.read_magic_file(self.WD+"/er_ages",1,'er_site_name')
        except:
            self.GUI_log.write ("-W- Cant find er_ages.txt in project directory")
            pass

        return (fail)
        
                          
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
                

    def on_menu_MagIC_model_builder(self,event):
        dia = MagIC_model_builder(self.WD,self.Data,self.Data_hierarchy)
        dia.Show()
        dia.Center()
        self.Data,self.Data_hierarchy,self.Data_info={},{},{}
        self.Data,self.Data_hierarchy=self.get_data() # Get data from magic_measurements and rmag_anistropy if exist.
        self.Data_info=self.get_data_info() # get all ages, locations etc. (from er_ages, er_sites, er_locations)
       
    def on_menu_convert_to_magic(self,event):
        dia = convert_generic_files_to_MagIC(self.WD)
        dia.Show()
        dia.Center()
        self.magic_file=self.WD+"/"+"magic_measurements.txt"
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

        plt_x_years=dia.set_plot_year.GetValue()
        plt_x_BP=dia.set_plot_BP.GetValue()
        
        plt_B=dia.set_plot_B.GetValue()
        plt_VADM=dia.set_plot_VADM.GetValue()
        show_sample_labels=dia.show_samples_ID.GetValue()
        show_x_error_bar=dia.show_x_error_bar.GetValue()                                
        show_y_error_bar=dia.show_y_error_bar.GetValue()                                


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
        #X_data,X_data_plus,X_data_minus=[],[],[]
        #Y_data,Y_data_plus,Y_data_minus=[],[],[]
        samples_names=[]
        samples_or_sites_names=[]
 
        if self.accept_new_parameters['average_by_sample_or_site']=='sample':
            Data_samples_or_sites=copy.deepcopy(self.Data_samples)
             
        else:
            Data_samples_or_sites=copy.deepcopy(self.Data_sites)
       
        # search for ages:
        
        lat_min,lat_max,lon_min,lon_max=90,0,180,-180
        for sample_or_site in Data_samples_or_sites.keys():
            #print sample_or_site
            found_age,found_lat=False,False
            tmp_B=[]
            for spec in Data_samples_or_sites[sample_or_site].keys():
                tmp_B.append( Data_samples_or_sites[sample_or_site][spec])
            if len(tmp_B)<1:
                continue
            tmp_B=array(tmp_B)
            B_uT=mean(tmp_B)
            B_std_uT=std(tmp_B,ddof=1)
            B_std_perc=100*(B_std_uT/B_uT)

            #check if pass criteria
            if len(tmp_B)>=self.accept_new_parameters['sample_int_n']:
                if (self.accept_new_parameters['sample_int_sigma_uT']==0 and self.accept_new_parameters['sample_int_sigma_perc']==0) or\
                   ( B_std_uT <=self.accept_new_parameters['sample_int_sigma_uT'] or B_std_perc <= self.accept_new_parameters['sample_int_sigma_perc']):
                    if ( (max(tmp_B)-min(tmp_B)) <= self.accept_new_parameters['sample_int_interval_uT'] or 100*((max(tmp_B)-min(tmp_B))/mean((tmp_B))) <= self.accept_new_parameters['sample_int_interval_perc']):
                        if sample_or_site in self.Data_hierarchy['sites'].keys():
                            site= sample_or_site
                        elif self.Data_hierarchy['site_of_sample'].keys():
                            site=self.Data_hierarchy['site_of_sample'][sample_or_site]
                        else:
                            site= sample_or_site

                        #-----
                        # serch for age data and
                        # convert all ages to calender age. 
                        # i.e. 300ka would be -300,000
                        # and 2000 BP would be -50

                        #-----
                                                    
                        found_age=False
                        er_ages_rec={}
                        if sample_or_site in self.Data_info["er_ages"].keys() and "age" in self.Data_info["er_ages"][sample_or_site].keys() and self.Data_info["er_ages"][sample_or_site]["age"]!="":
                            er_ages_rec=self.Data_info["er_ages"][sample_or_site]
                            found_age=True 
                        elif site in self.Data_info["er_ages"].keys() and "age" in self.Data_info["er_ages"][site].keys() and self.Data_info["er_ages"][site]["age"]!="":
                            er_ages_rec=self.Data_info["er_ages"][site]
                            found_age=True 
                        if  found_age:
                            age_description=er_ages_rec["age_description"] 
                            age_unit=er_ages_rec["age_unit"]
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
                            age_range_low=age
                            age_range_high=age
                            age_sigma=0
                            
                            if "age_sigma" in er_ages_rec.keys():
                               age_sigma=float(er_ages_rec["age_sigma"])*mutliplier
                               if age_unit=="Years BP" or age_unit =="Years Cal BP":
                                 age_sigma=1950-age_sigma
                               age_range_low= age-age_sigma
                               age_range_high= age+age_sigma
                            else:                              
                                if "age_range_high" in er_ages_rec.keys() and "age_range_low" in er_ages_rec.keys():
                                    age_range_high=float(er_ages_rec["age_range_high"])*mutliplier
                                    if age_unit=="Years BP" or age_unit =="Years Cal BP":
                                        age_range_high=1950-age_range_high                              
                                    age_range_low=float(er_ages_rec["age_range_low"])*mutliplier
                                    if age_unit=="Years BP" or age_unit =="Years Cal BP":
                                        age_range_low=1950-age_range_low                              
                        else:
                            continue
                         
                        #-----  
                        # ignore "poor" and "controversial" ages
                        #-----

                                                               
                        if "poor" in age_description or "controversial" in age_description:
                            print "skipping sample %s because of age quality" %sample_or_site
                            self.GUI_log.write( "-W- Plot: skipping sample %s because of age quality\n"%sample_or_site)
                            continue

                               
                                                                                             
                        #-----  
                        # serch for latitude data
                        #-----
                        
                        found_lat=False
                        er_sites_rec={}
                        if sample_or_site in self.Data_info["er_sites"].keys():
                            er_sites_rec=self.Data_info["er_sites"][sample_or_site]
                            found_lat=True 
                        elif site in self.Data_info["er_sites"].keys():
                            er_sites_rec=self.Data_info["er_sites"][site]
                            found_lat=True 
                        
                        if found_lat:
                            lat=float(er_sites_rec["site_lat"])
                            lon=float(er_sites_rec["site_lon"])
                        

                        #-----  
                        # sort by locations
                        #-----

                        location="unknown"
                        #try: 
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
                            plot_by_locations[location]['samples_names']=[]
                            plot_by_locations[location]['site_lon'],plot_by_locations[location]['site_lat']=[],[]
                            #if found_lat:
                            #    lat_min,lat_max,lon_min,lon_max=lat,lat,lon,lon
                            #else:
                            #    lat_min,lat_max,lon_min,lon_max=0,0,0,0
                                
                        if found_lat:
                           plot_by_locations[location]['site_lon']=lon
                           plot_by_locations[location]['site_lat']=lat
                        if found_lat:
                            lat_min,lat_max=min(lat_min,lat),max(lat_max,lat)
                            lon_min,lon_max=min(lon_min,lon),max(lon_max,lon)
                        if  plt_B:
                            plot_by_locations[location]['Y_data'].append(B_uT)
                            plot_by_locations[location]['Y_data_plus'].append(B_std_uT)
                            plot_by_locations[location]['Y_data_minus'].append(B_std_uT)
                            plot_by_locations[location]['samples_names'].append(sample_or_site)
                            
                        elif plt_VADM and found_lat: # units of ZAm^2
                            VADM=self.b_vdm(B_uT*1e-6,lat)*1e-21
                            VADM_plus=self.b_vdm((B_uT+B_std_uT)*1e-6,lat)*1e-21
                            VADM_minus=self.b_vdm((B_uT-B_std_uT)*1e-6,lat)*1e-21
                            plot_by_locations[location]['Y_data'].append(VADM)
                            plot_by_locations[location]['Y_data_plus'].append(VADM_plus-VADM)
                            plot_by_locations[location]['Y_data_minus'].append(VADM-VADM_minus)
                            plot_by_locations[location]['samples_names'].append(sample_or_site)

                        elif plt_VADM and not found_lat:
                            self.GUI_log.write( "-W- Plot: skipping sample %s because cant find latitude for V[A]DM calculation\n"%sample_or_site)
                            print "-W- Plot: skipping sample %s because  cant find latitude for V[A]DM calculation\n"%sample_or_site
                            continue

                        plot_by_locations[location]['X_data'].append(age)
                        plot_by_locations[location]['X_data_plus'].append(age_range_high-age)
                        plot_by_locations[location]['X_data_minus'].append(age-age_range_low)
                                                                
                        found_age=False
                        found_lat=False
                        
                         
                            


        #----
        # map

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
##                    lat_min_round=SiteLat_min-SiteLat_min%set_map_lat_grid
##                    lat_max_round=SiteLat_max-SiteLat_max%set_map_lat_grid
##                    lon_min_round=SiteLon_min-SiteLon_min%set_map_lat_grid
##                    lon_max_round=SiteLon_max-SiteLon_max%set_map_lat_grid
                    m.drawparallels(np.arange(SiteLat_min,SiteLat_max+set_map_lat_grid,set_map_lat_grid),linewidth=0.5,labels=[1,0,0,0],fontsize=10)
                    m.drawmeridians(np.arange(SiteLon_min,SiteLon_max+set_map_lon_grid,set_map_lon_grid),linewidth=0.5,labels=[0,0,0,1],fontsize=10)

                else:
                    lat_min_round=SiteLat_min-SiteLat_min%10
                    lat_max_round=SiteLat_max-SiteLat_max%10
                    lon_min_round=SiteLon_min-SiteLon_min%10
                    lon_max_round=SiteLon_max-SiteLon_max%10
                    m.drawparallels(np.arange(lat_min_round,lat_max_round+5,5),linewidth=0.5,labels=[1,0,0,0],fontsize=10)
                    m.drawmeridians(np.arange(lon_min_round,lon_max_round+5,5),linewidth=0.5,labels=[0,0,0,1],fontsize=10)

                m.fillcontinents(zorder=0,color='0.9')
                m.drawcoastlines()
                m.drawcountries()
                m.drawmapboundary()
            else:
                print "Cant plot map. Is basemap installed?"
        cnt=0    

        Fig=figure(1,(15,6))
        clf()
        ax = axes([0.3,0.1,0.6,0.8])
        locations =plot_by_locations.keys()
        locations.sort()

        for location in locations:
            figure(1)
            X_data,X_data_minus,X_data_plus=plot_by_locations[location]['X_data'],plot_by_locations[location]['X_data_minus'],plot_by_locations[location]['X_data_plus']
            Y_data,Y_data_minus,Y_data_plus=plot_by_locations[location]['Y_data'],plot_by_locations[location]['Y_data_minus'],plot_by_locations[location]['Y_data_plus']
            if not show_x_error_bar:
                Xerr=None
            else:
                Xerr=[array(X_data_minus),array(X_data_plus)]
            if not show_y_error_bar:
                Yerr=None
            else:
                Yerr=[Y_data_minus,Y_data_plus]
            errorbar(X_data,Y_data,xerr=Xerr,yerr=Yerr,fmt=SYMBOLS[cnt%len(SYMBOLS)],color=COLORS[cnt%len(COLORS)],label=location)
            if Plot_map:
                figure(2)
                lat=plot_by_locations[location]['site_lat']
                lon=plot_by_locations[location]['site_lon']
                x1,y1=m([lon],[lat])
                m.scatter(x1,y1,s=[50],marker=SYMBOLS[cnt%len(SYMBOLS)],color=COLORS[cnt%len(COLORS)],edgecolor='black')
            cnt+=1
                
        figure(1)#,(15,6))
        #figtext(0.05,0.95,"N=%i"%len(X_data))
        
        legend_font_props = matplotlib.font_manager.FontProperties()
        legend_font_props.set_size(12)

        h,l = ax.get_legend_handles_labels()
        legend(h,l,loc='center left', bbox_to_anchor=[0, 0, 1, 1],bbox_transform=Fig.transFigure,numpoints=1,prop=legend_font_props)

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
        if plt_x_BP:
            #xlabel("years BP")
            ax.set_xlabel("years BP",fontsize=12)
        if plt_x_years:
            #xlabel("Date")
            ax.set_xlabel("Date",fontsize=12)

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
                    text(plot_by_locations[location]['X_data'][i],plot_by_locations[location]['Y_data'][i],"  "+ plot_by_locations[location]['samples_names'][i],fontsize=10,color="0.5")


        show()
    
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


              
        self.araiplot.set_xlabel("TRM / NRM$_0$",fontsize=10*self.GUI_RESOLUTION)
        self.araiplot.set_ylabel("NRM / NRM$_0$",fontsize=10*self.GUI_RESOLUTION)
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
        last_cart_1=array([self.CART_rot[0][0],self.CART_rot[0][1]])
        last_cart_2=array([self.CART_rot[0][0],self.CART_rot[0][2]])
        if self.Data[self.s]['T_or_MW']!="T":
            K_diff=0
        else:
            K_diff=273
            
        if self.preferences['show_Zij_temperatures'] :
            for i in range(len(self.z_temperatures)):
                if int(self.preferences['show_Zij_temperatures_steps']) !=1:
                    if i!=0  and (i+1)%int(self.preferences['show_Zij_temperatures_steps'])==0:
                        self.zijplot.text(self.CART_rot[i][0],-1*self.CART_rot[i][2]," %.0f"%(self.z_temperatures[i]-K_diff),fontsize=10*self.GUI_RESOLUTION,color='gray',ha='left',va='center',clip_on=False)   #inc
                else:
                  self.zijplot.text(self.CART_rot[i][0],-1*self.CART_rot[i][2]," %.0f"%(self.z_temperatures[i]-K_diff),fontsize=10*self.GUI_RESOLUTION,color='gray',ha='left',va='center',clip_on=False)   #inc

        #-----
        xmin, xmax = self.zijplot.get_xlim()
        if xmax <0:
            xmax=0
        if xmin>0:
            xmin=0
        props = dict(color='black', linewidth=0.5, markeredgewidth=0.5)

        #xlocs = [loc for loc in self.zijplot.xaxis.get_majorticklocs()
        #        if loc>=xmin and loc<=xmax]
        xlocs=arange(xmin,xmax,0.2)
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
        ylocs=arange(ymin,ymax,0.2)

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
            self.fig3.text(0.02,0.96,"Equal area",{'family':'Arial', 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })
            self.eqplot = self.fig3.add_subplot(111)


            self.draw_net()

            self.zij=array(self.Data[self.s]['zdata'])
            self.zij_norm=array([row/sqrt(sum(row**2)) for row in self.zij])

            x_eq=array([row[0] for row in self.zij_norm])
            y_eq=array([row[1] for row in self.zij_norm])
            z_eq=abs(array([row[2] for row in self.zij_norm]))

            R=array(sqrt(1-z_eq)/sqrt(x_eq**2+y_eq**2)) # from Collinson 1983
            eqarea_data_x=y_eq*R
            eqarea_data_y=x_eq*R
            self.eqplot.plot(eqarea_data_x,eqarea_data_y,lw=0.5,color='gray',clip_on=False)
            #self.eqplot.scatter([eqarea_data_x_dn[i]],[eqarea_data_y_dn[i]],marker='o',edgecolor='0.1', facecolor='blue',s=15,lw=1)


            x_eq_dn,y_eq_dn,z_eq_dn,eq_dn_temperatures=[],[],[],[]
            x_eq_dn=array([row[0] for row in self.zij_norm if row[2]>0])
            y_eq_dn=array([row[1] for row in self.zij_norm if row[2]>0])
            z_eq_dn=abs(array([row[2] for row in self.zij_norm if row[2]>0]))
            
            if len(x_eq_dn)>0:
                R=array(sqrt(1-z_eq_dn)/sqrt(x_eq_dn**2+y_eq_dn**2)) # from Collinson 1983
                eqarea_data_x_dn=y_eq_dn*R
                eqarea_data_y_dn=x_eq_dn*R
                self.eqplot.scatter([eqarea_data_x_dn],[eqarea_data_y_dn],marker='o',edgecolor='gray', facecolor='black',s=15*self.GUI_RESOLUTION,lw=1,clip_on=False)
                        
                

            x_eq_up,y_eq_up,z_eq_up=[],[],[]
            x_eq_up=array([row[0] for row in self.zij_norm if row[2]<=0])
            y_eq_up=array([row[1] for row in self.zij_norm if row[2]<=0])
            z_eq_up=abs(array([row[2] for row in self.zij_norm if row[2]<=0]))
            if len(x_eq_up)>0:
                R=array(sqrt(1-z_eq_up)/sqrt(x_eq_up**2+y_eq_up**2)) # from Collinson 1983
                eqarea_data_x_up=y_eq_up*R
                eqarea_data_y_up=x_eq_up*R
                self.eqplot.scatter([eqarea_data_x_up],[eqarea_data_y_up],marker='o',edgecolor='black', facecolor='white',s=15*self.GUI_RESOLUTION,lw=1,clip_on=False)        
            
            if self.preferences['show_eqarea_temperatures']:
                for i in range(len(self.z_temperatures)):
                    if self.Data[self.s]['T_or_MW']!="MW":
                        K_dif=0.
                    else:
                        K_dif=273.                    
                    self.eqplot.text(eqarea_data_x[i],eqarea_data_y[i],"%.0f"%(float(self.z_temperatures[i])-K_dif),fontsize=8*self.GUI_RESOLUTION,color="0.5",clip_on=False)
            
            
            #self.eqplot.text(eqarea_data_x[0],eqarea_data_y[0]," NRM",fontsize=8,color='gray',ha='left',va='center')


            # In-field steps" self.preferences["show_eqarea_pTRMs"]
            if self.preferences["show_eqarea_pTRMs"]:
                eqarea_data_x_up,eqarea_data_y_up=[],[]
                eqarea_data_x_dn,eqarea_data_y_dn=[],[]
                PTRMS=self.Data[self.s]['PTRMS'][1:]
                CART_pTRMS_orig=array([self.dir2cart(row[1:4]) for row in PTRMS])
                CART_pTRMS=[row/sqrt(sum((array(row)**2))) for row in CART_pTRMS_orig]
                                 
                for i in range(1,len(CART_pTRMS)):
                    if CART_pTRMS[i][2]<=0:
                        R=sqrt(1.-abs(CART_pTRMS[i][2]))/sqrt(CART_pTRMS[i][0]**2+CART_pTRMS[i][1]**2)
                        eqarea_data_x_up.append(CART_pTRMS[i][1]*R)
                        eqarea_data_y_up.append(CART_pTRMS[i][0]*R)
                    else:
                        R=sqrt(1.-abs(CART_pTRMS[i][2]))/sqrt(CART_pTRMS[i][0]**2+CART_pTRMS[i][1]**2)
                        eqarea_data_x_dn.append(CART_pTRMS[i][1]*R)
                        eqarea_data_y_dn.append(CART_pTRMS[i][0]*R)
                if len(eqarea_data_x_up)>0:
                    self.eqplot.scatter(eqarea_data_x_up,eqarea_data_y_up,marker='^',edgecolor='blue', facecolor='white',s=15*self.GUI_RESOLUTION,lw=1,clip_on=False)
                if len(eqarea_data_x_dn)>0:
                    self.eqplot.scatter(eqarea_data_x_dn,eqarea_data_y_dn,marker='^',edgecolor='gray', facecolor='blue',s=15*self.GUI_RESOLUTION,lw=1,clip_on=False)        
            draw()
            self.canvas3.draw()
    
        else:

            self.fig3.clf()
            self.fig3.text(0.02,0.96,"Cooling rate experiment",{'family':'Arial', 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })
            self.eqplot = self.fig3.add_axes([0.2,0.15,0.7,0.7],frameon=True,axisbg='None')

            if 'cooling_rate_data' in self.Data[self.s].keys() and\
            'ancient_cooling_rate' in self.Data[self.s]['cooling_rate_data'].keys() and\
            'lab_cooling_rate' in self.Data[self.s]['cooling_rate_data'].keys():
                ancient_cooling_rate=self.Data[self.s]['cooling_rate_data']['ancient_cooling_rate']
                lab_cooling_rate=self.Data[self.s]['cooling_rate_data']['lab_cooling_rate']
                x0=math.log(lab_cooling_rate/ancient_cooling_rate)
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
                self.eqplot.set_ylabel("TRM / TRM[oven]",fontsize=8)
                self.eqplot.set_xlabel("ln(CR[oven]/CR)",fontsize=8)
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
            draw()
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
            self.fig5.text(0.02,0.96,"M/T",{'family':'Arial', 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })
            self.mplot = self.fig5.add_axes([0.2,0.15,0.7,0.7],frameon=True,axisbg='None')
            
            self.mplot.clear()
            NRMS=self.Data[self.s]['NRMS']
            PTRMS=self.Data[self.s]['PTRMS']

            if self.Data[self.s]['T_or_MW']!="MW":
                temperatures_NRMS=array([row[0]-273. for row in NRMS])
                temperatures_PTRMS=array([row[0]-273. for row in PTRMS])
                temperatures_NRMS[0]=21
                temperatures_PTRMS[0]=21
            else:
                temperatures_NRMS=array([row[0] for row in NRMS])
                temperatures_PTRMS=array([row[0] for row in PTRMS])
            
            if len(temperatures_NRMS)!=len(temperatures_PTRMS):
              self.GUI_log.write("-E- ERROR: NRMS and pTRMS are not equal in specimen %s. Check\n."%self.s)
            else:
              M_NRMS=array([row[3] for row in NRMS])/NRMS[0][3]
              M_pTRMS=array([row[3] for row in PTRMS])/NRMS[0][3]

              self.mplot.clear()
              self.mplot.plot(temperatures_NRMS,M_NRMS,'bo-',mec='0.2',markersize=5*self.GUI_RESOLUTION,lw=1,clip_on=False)
              self.mplot.plot(temperatures_NRMS,M_pTRMS,'ro-',mec='0.2',markersize=5*self.GUI_RESOLUTION,lw=1,clip_on=False)
              if self.Data[self.s]['T_or_MW']!="MW":
                  self.mplot.set_xlabel("C",fontsize=8*self.GUI_RESOLUTION)
              else:
                  self.mplot.set_xlabel("Treatment",fontsize=8*self.GUI_RESOLUTION)                  
              self.mplot.set_ylabel("M / NRM$_0$",fontsize=8*self.GUI_RESOLUTION)
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
              
              xt=xticks()

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
            self.mplot.scatter(array(self.Data[self.s]['NLT_parameters']['B_NLT'])*1e6,self.Data[self.s]['NLT_parameters']['M_NLT_norm'],marker='o',facecolor='b',edgecolor ='k',s=15,clip_on=False)
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
            y=alpha*(tanh(x*1e-6*beta))
            labfiled=self.Data[self.s]['lab_dc_field']
            self.mplot.plot(x,x*1e-6*(alpha*(tanh(labfiled*beta))/labfiled),'--',color='black',linewidth=0.7,clip_on=False)
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
        theta=arange(0.,2*pi,2*pi/1000)
        eq.plot(cos(theta),sin(theta),'k',clip_on=False)
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
        
        window_list=['int_n','int_ptrm_n','frac','gmax','f','fvds','b_beta','g','q','int_mad','dang','drats','md']
        high_threshold_velue_list=['specimen_gmax','specimen_b_beta','specimen_dang','specimen_drats','specimen_int_mad','specimen_md']
        low_threshold_velue_list=['specimen_int_n','specimen_int_ptrm_n','specimen_f','specimen_fvds','specimen_frac','specimen_g','specimen_q']
        flag_Fail=False
    
        for key in  high_threshold_velue_list+low_threshold_velue_list + ["specimen_ptrms_inc","specimen_ptrms_dec","specimen_ptrms_mad","specimen_ptrms_angle"]:
            if key in ['specimen_int_n','specimen_int_ptrm_n']:
                Value="%.0f"%self.pars[key]
            if key in ['specimen_dang','specimen_drats','specimen_int_mad','specimen_md','specimen_g','specimen_q']:
                Value="%.1f"%self.pars[key]
            if key in ['specimen_f','specimen_fvds','specimen_frac','specimen_b_beta','specimen_gmax']:
                Value="%.2f"%self.pars[key]            
            if key in ["specimen_ptrms_inc","specimen_ptrms_dec","specimen_ptrms_mad","specimen_ptrms_angle"]:
                Value="%.2f"%self.pars[key]            
            command= "self.%s_window.SetValue(Value)"%key.split('specimen_')[-1]
            if key.split('specimen_')[-1] in self.preferences['show_statistics_on_gui']:
                exec(command)
            if self.ignore_parameters[key]:
                command="self.%s_window.SetBackgroundColour(wx.NullColour)"%key.split('specimen_')[-1]  # set text color                
            elif (key in high_threshold_velue_list) and (float(self.pars[key])<=float(self.accept_new_parameters[key])):
                command="self.%s_window.SetBackgroundColour(wx.GREEN)"%key.split('specimen_')[-1]  # set text color
            elif (key in low_threshold_velue_list) and (float(self.pars[key])>=float(self.accept_new_parameters[key])):
                command="self.%s_window.SetBackgroundColour(wx.GREEN)"%key.split('specimen_')[-1]  # set text color
            else:
                command="self.%s_window.SetBackgroundColour(wx.RED)"%key.split('specimen_')[-1]  # set text color
                flag_Fail=True
            if key.split('specimen_')[-1] in self.preferences['show_statistics_on_gui']:
                exec command    

        # Scat
        if self.accept_new_parameters['specimen_scat']:
            if self.pars["fail_arai_beta_box_scatter"] or self.pars["fail_ptrm_beta_box_scatter"] or self.pars["fail_tail_beta_box_scatter"]:
              self.scat_window.SetValue("fail")
            else:
              self.scat_window.SetValue("pass")

            if self.ignore_parameters['specimen_scat'] and  "scat" in self.preferences['show_statistics_on_gui']:
              self.scat_window.SetBackgroundColour(wx.NullColour) # set text color
            elif self.pars["fail_arai_beta_box_scatter"] or self.pars["fail_ptrm_beta_box_scatter"] or self.pars["fail_tail_beta_box_scatter"] :
              if "scat" in self.preferences['show_statistics_on_gui']:
                  self.scat_window.SetBackgroundColour(wx.RED) # set text color
              flag_Fail=True
            else :
              if "scat" in self.preferences['show_statistics_on_gui']:
                  self.scat_window.SetBackgroundColour(wx.GREEN) # set text color
        else:
            if "scat" in self.preferences['show_statistics_on_gui']:
                self.scat_window.SetValue("")
                self.scat_window.SetBackgroundColour(wx.NullColour) # set text color


        # Banc, correction factor

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

       
        if (index_2-index_1)+1 >= self.accept_new_parameters['specimen_int_n']:
            if self.Data[self.s]['T_or_MW']!="MW":
                self.pars=self.get_PI_parameters(self.s,float(t1)+273.,float(t2)+273.)
            else:
                self.pars=self.get_PI_parameters(self.s,float(t1),float(t2))
                
            self.update_GUI_with_new_interpretation()
      
    def get_PI_parameters(self,s,tmin,tmax):


        def cart2dir(cart): # OLD ONE
            """
            converts a direction to cartesian coordinates
            """
            Dir=[] # establish a list to put directions in
            rad=pi/180. # constant to convert degrees to radians
            R=sqrt(cart[0]**2+cart[1]**2+cart[2]**2) # calculate resultant vector length
            if R==0:
               #print 'trouble in cart2dir'
               #print cart
               return [0.0,0.0,0.0]
            D=arctan2(cart[1],cart[0])/rad  # calculate declination taking care of correct quadrants (arctan2)
            if D<0:D=D+360. # put declination between 0 and 360.
            if D>360.:D=D-360.
            Dir.append(D)  # append declination to Dir list
            I=arcsin(cart[2]/R)/rad # calculate inclination (converting to degrees)
            Dir.append(I) # append inclination to Dir list
            Dir.append(R) # append vector length to Dir list
            return Dir # return the directions list


        def dir2cart(d):
           # converts list or array of vector directions, in degrees, to array of cartesian coordinates, in x,y,z
            ints=ones(len(d)).transpose() # get an array of ones to plug into dec,inc pairs
            d=array(d)
            rad=pi/180.
            if len(d.shape)>1: # array of vectors
                decs,incs=d[:,0]*rad,d[:,1]*rad
                if d.shape[1]==3: ints=d[:,2] # take the given lengths
            else: # single vector
                decs,incs=array(d[0])*rad,array(d[1])*rad
                if len(d)==3: 
                    ints=array(d[2])
                else:
                    ints=array([1.])
            cart= array([ints*cos(decs)*cos(incs),ints*sin(decs)*cos(incs),ints*sin(incs)]).transpose()
            return cart

        def calculate_ftest(s,sigma,nf):
            chibar=(s[0][0]+s[1][1]+s[2][2])/3.
            t=array(linalg.eigvals(s))
            F=0.4*(t[0]**2+t[1]**2+t[2]**2 - 3*chibar**2)/(float(sigma)**2)

            return(F)

        """
        calcualte statisics 
        """
        pars=self.Data[s]['pars']
        datablock = self.Data[s]['datablock']
        pars=self.Data[s]['pars']
        # get MagIC mothod codes:

        #pars['magic_method_codes']="LP-PI-TRM" # thellier Method
        
        
        t_Arai=self.Data[s]['t_Arai']
        x_Arai=self.Data[s]['x_Arai']
        y_Arai=self.Data[s]['y_Arai']
        x_tail_check=self.Data[s]['x_tail_check']
        y_tail_check=self.Data[s]['y_tail_check']

        zijdblock=self.Data[s]['zijdblock']        
        z_temperatures=self.Data[s]['z_temp']

        #print tmin,tmax,z_temperatures
        # check tmin
        if tmin not in t_Arai or tmin not in z_temperatures:
            return(pars)
        
        # check tmax
        if tmax not in t_Arai or tmin not in z_temperatures:
            return(pars)

        start=t_Arai.index(tmin)
        end=t_Arai.index(tmax)

        if end-start < float(self.accept_new_parameters['specimen_int_n'] -1):
          return(pars)
                                                 
        #-------------------------------------------------
        # calualte PCA of the zerofield steps
        # MAD calculation following Kirschvink (1980)
        # DANG following Tauxe and Staudigel (2004)
        #-------------------------------------------------               
         
        pars["measurement_step_min"]=float(tmin)
        pars["measurement_step_max"]=float(tmax)
 
        zstart=z_temperatures.index(tmin)
        zend=z_temperatures.index(tmax)

        zdata_segment=self.Data[s]['zdata'][zstart:zend+1]

        #  PCA in 2 lines
        M = (zdata_segment-mean(zdata_segment.T,axis=1)).T # subtract the mean (along columns)
        [eigenvalues,eigenvectors] = linalg.eig(cov(M)) # attention:not always sorted

        # sort eigenvectors and eigenvalues
        eigenvalues=list(eigenvalues)
        tmp=[0,1,2]
        t1=max(eigenvalues);index_t1=eigenvalues.index(t1);tmp.remove(index_t1)
        t3=min(eigenvalues);index_t3=eigenvalues.index(t3);tmp.remove(index_t3)
        index_t2=tmp[0];t2=eigenvalues[index_t2]
        v1=real(array(eigenvectors[:,index_t1]))
        v2=real(array(eigenvectors[:,index_t2]))
        v3=real(array(eigenvectors[:,index_t3]))

        # chech if v1 is the "right" polarity
        cm=array(mean(zdata_segment.T,axis=1)) # center of mass
        v1_plus=v1*sqrt(sum(cm**2))
        v1_minus=v1*-1*sqrt(sum(cm**2))
        test_v=zdata_segment[0]-zdata_segment[-1]

        if sqrt(sum((v1_minus-test_v)**2)) < sqrt(sum((v1_plus-test_v)**2)):
         DIR_PCA=self.cart2dir(v1*-1)
         best_fit_vector=v1*-1
        else:
         DIR_PCA=self.cart2dir(v1)
         best_fit_vector=v1

        # MAD Kirschvink (1980)
        MAD=math.degrees(arctan(sqrt((t2+t3)/t1)))

        # DANG Tauxe and Staudigel 2004
        DANG=math.degrees( arccos( ( dot(cm, best_fit_vector) )/( sqrt(sum(cm**2)) * sqrt(sum(best_fit_vector**2)))))


        # best fit PCA direction
        pars["specimen_dec"] =  DIR_PCA[0]
        pars["specimen_inc"] =  DIR_PCA[1]
        pars["specimen_PCA_v1"] =best_fit_vector
        if t1 <0 or t1==0:
            t1=1e-10
        if t2 <0 or t2==0:
            t2=1e-10
        if t3 <0 or t3==0:
            t3=1e-10
            
        pars["specimen_PCA_sigma_max"] =  sqrt(t1)
        pars["specimen_PCA_sigma_int"] =  sqrt(t2)
        pars["specimen_PCA_sigma_min"] =  sqrt(t3)
            

        # MAD Kirschvink (1980)
        pars["specimen_int_mad"]=MAD
        pars["specimen_dang"]=DANG


        #-------------------------------------------------
        # calualte PCA of the pTRMs over the entire temperature range
        # and calculate the angular difference to the lab field
        # MAD calculation following Kirschvink (1980)
        #-------------------------------------------------
        
        PTRMS = self.Data[s]['PTRMS'][1:]
        CART_pTRMS_orig=array([self.dir2cart(row[1:4]) for row in PTRMS])
        #CART_pTRMS=[row/sqrt(sum((array(row)**2))) for row in CART_pTRMS_orig]
##        print "CART_pTRMS_orig",CART_pTRMS_orig
##        print "----"
        
        #  PCA in 2 lines
        M = (CART_pTRMS_orig-mean(CART_pTRMS_orig.T,axis=1)).T # subtract the mean (along columns)
        [eigenvalues,eigenvectors] = linalg.eig(cov(M)) # attention:not always sorted

        # sort eigenvectors and eigenvalues
        eigenvalues=list(eigenvalues)
        tmp=[0,1,2]
        t1=max(eigenvalues);index_t1=eigenvalues.index(t1);tmp.remove(index_t1)
        t3=min(eigenvalues);index_t3=eigenvalues.index(t3);tmp.remove(index_t3)
        index_t2=tmp[0];t2=eigenvalues[index_t2]
        v1=real(array(eigenvectors[:,index_t1]))
        v2=real(array(eigenvectors[:,index_t2]))
        v3=real(array(eigenvectors[:,index_t3]))

        # chech if v1 is the "right" polarity
        cm=array(mean(CART_pTRMS_orig.T,axis=1)) # center of mass
        v1_plus=v1*sqrt(sum(cm**2))
        v1_minus=v1*-1*sqrt(sum(cm**2))
        test_v=CART_pTRMS_orig[0]-CART_pTRMS_orig[-1]

        if sqrt(sum((v1_minus-test_v)**2)) > sqrt(sum((v1_plus-test_v)**2)):
         DIR_PCA=self.cart2dir(v1*-1)
         best_fit_vector=v1*-1
        else:
         DIR_PCA=self.cart2dir(v1)
         best_fit_vector=v1

        # MAD Kirschvink (1980)
        MAD=math.degrees(arctan(sqrt((t2+t3)/t1)))


        # best fit PCA direction
        pars["specimen_ptrms_dec"] =  DIR_PCA[0]
        pars["specimen_ptrms_inc"] =  DIR_PCA[1]
        pars["specimen_ptrms_mad"]=MAD
        B_lab_unit=self.dir2cart([ self.Data[s]['Thellier_dc_field_phi'], self.Data[s]['Thellier_dc_field_theta'],1])
        pars["specimen_ptrms_angle"]=math.degrees(math.acos(dot(best_fit_vector,B_lab_unit)/(sqrt(sum(best_fit_vector**2)) * sqrt(sum(B_lab_unit**2)))))

##        print "specimen_ptrms_dec",pars["specimen_ptrms_dec"]
##        print "specimen_ptrms_inc",pars["specimen_ptrms_inc"]
##        print "B_lab_unit,v1",B_lab_unit,v1
##        print "specimen_ptrms_angle", pars["specimen_ptrms_angle"]

##        #-------------------------------------------------                     
##        # Calculate the new 'MAD box' parameter
##        # all datapoints should be inside teh M"AD box"
##        # defined by the threshold value of MAD
##        # For definitionsee Shaar and Tauxe (2012)
##        #-------------------------------------------------                     
##
##        pars["specimen_mad_scat"]="Pass"
##        self.accept_new_parameters['specimen_mad_scat']=True
##        if 'specimen_mad_scat' in self.accept_new_parameters.keys() and 'specimen_int_mad' in self.accept_new_parameters.keys() :
##            if self.accept_new_parameters['specimen_mad_scat']==True or self.accept_new_parameters['specimen_mad_scat'] in [1,"True","TRUE",'1']:
##
##                # center of mass 
##                CM_x=mean(zdata_segment[:,0])
##                CM_y=mean(zdata_segment[:,1])
##                CM_z=mean(zdata_segment[:,2])
##                CM=array([CM_x,CM_y,CM_z])
##
##                # threshold value for the distance of the point from a line:
##                # this is depends of MAD
##                # if MAD= tan-1 [ sigma_perpendicular / sigma_max ]
##                # then:
##                # sigma_perpendicular_threshold=tan(MAD_threshold)*sigma_max
##                sigma_perpendicular_threshold=abs(tan(radians(self.accept_new_parameters['specimen_int_mad'])) *  pars["specimen_PCA_sigma_max"] )
##                
##                # Line from
##                #print "++++++++++++++++++++++++++++++++++"
##                
##                for P in zdata_segment:
##                    # Find the line  P_CM that connect P to the center of mass
##                    #print "P",P
##                    #print "CM",CM
##                    P_CM=P-CM
##                    #print "P_CM",P_CM
##                    
##                    #  the dot product of vector P_CM with the unit direction vector of the best-fit liene. That's the projection of P_CM on the PCA line 
##                    best_fit_vector_unit=best_fit_vector/sqrt(sum(best_fit_vector**2))
##                    #print "best_fit_vector_unit",best_fit_vector_unit
##                    CM_P_projection_on_PCA_line=dot(best_fit_vector_unit,P_CM)
##                    #print "CM_P_projection_on_PCA_line",CM_P_projection_on_PCA_line
##
##                    # Pythagoras
##                    P_CM_length=sqrt(sum((P_CM)**2))
##                    Point_2_PCA_Distance=sqrt((P_CM_length**2-CM_P_projection_on_PCA_line**2))
##                    #print "Point_2_PCA_Distance",Point_2_PCA_Distance
##
##
##                    #print "sigma_perpendicular_threshold*2",sigma_perpendicular_threshold*2
##                    if Point_2_PCA_Distance > sigma_perpendicular_threshold*2:
##                        pars["specimen_mad_scat"]="Fail"
##                        index=999
##                        for i in range(len(self.Data[s]['zdata'])):
##                        
##                            if P[0] == self.Data[s]['zdata'][i][0] and P[1] == self.Data[s]['zdata'][i][1] and P[2] == self.Data[s]['zdata'][i][2]:
##                                index =i
##                                break
##                        #print "specimen  %s fail on mad_scat,%i"%(s,index)
##                        
##                    
##                    
##                    #CM_P_projection_on_PCA_line_length=sqrt(sum((CM_P_projection_on_PCA_line_length)**2))
        

        #-------------------------------------------------
        # York regresssion (York, 1967) following Coe (1978)
        # calculate f,fvds,
        # modified from pmag.py
        #-------------------------------------------------               

        x_Arai_segment= x_Arai[start:end+1]
        y_Arai_segment= y_Arai[start:end+1]

        x_Arai_mean=mean(x_Arai_segment)
        y_Arai_mean=mean(y_Arai_segment)

        # equations (2),(3) in Coe (1978) for b, sigma
        n=end-start+1
        x_err=x_Arai_segment-x_Arai_mean
        y_err=y_Arai_segment-y_Arai_mean

        # York b
        york_b=-1* sqrt( sum(y_err**2) / sum(x_err**2) )

        # york sigma
        york_sigma= sqrt ( (2 * sum(y_err**2) - 2*york_b*sum(x_err*y_err)) / ( (n-2) * sum(x_err**2) ) )

        # beta  parameter 
        if  york_b!=0:              
            beta_Coe=abs(york_sigma/york_b)
        else:
            beta_Coe=0

        # y_T is the intercept of the extrepolated line
        # through the center of mass (see figure 7 in Coe (1978))
        y_T = y_Arai_mean - york_b* x_Arai_mean

        # calculate the extarplated data points for f and fvds
        # (see figure 7 in Coe (1978))
        x_tag=(y_Arai_segment - y_T ) / york_b
        y_tag=york_b*x_Arai_segment + y_T

        # intersect of the dashed square and the horizontal dahed line  next to delta-y-5 in figure 7, Coe (1978)
        x_prime=(x_Arai_segment+x_tag) / 2
        y_prime=(y_Arai_segment+y_tag) / 2

        f_Coe=abs((y_prime[0]-y_prime[-1])/y_T)

        f_vds=abs((y_prime[0]-y_prime[-1])/self.Data[s]['vds'])

        g_Coe= 1 - (sum((y_prime[:-1]-y_prime[1:])**2) / sum((y_prime[:-1]-y_prime[1:]))**2 )

        q_Coe=abs(york_b)*f_Coe*g_Coe/york_sigma


        count_IZ= self.Data[self.s]['steps_Arai'].count('IZ')
        count_ZI= self.Data[self.s]['steps_Arai'].count('ZI')
        if count_IZ >1 and count_ZI >1:
            pars['magic_method_codes']="LP-PI-BT-IZZI"
        elif count_IZ <1 and count_ZI >1:
            pars['magic_method_codes']="LP-PI-ZI"
        elif count_IZ >1 and count_ZI <1:
            pars['magic_method_codes']="LP-PI-IZ"            
        else:
            pars['magic_method_codes']=""
            
        pars['specimen_int_n']=end-start+1
        pars["specimen_b"]=york_b
        pars["specimen_YT"]=y_T       
        pars["specimen_b_sigma"]=york_sigma
        pars["specimen_b_beta"]=beta_Coe
        pars["specimen_f"]=f_Coe
        pars["specimen_fvds"]=f_vds
        pars["specimen_g"]=g_Coe
        pars["specimen_q"]=q_Coe
        pars["specimen_int"]=-1*pars['lab_dc_field']*pars["specimen_b"]
        pars['magic_method_codes']+=":IE-TT"
        pars["specimen_cm_x"]=x_Arai_mean
        pars["specimen_cm_y"]=y_Arai_mean

        
        if 'x_ptrm_check' in self.Data[self.s].keys():
            if len(self.Data[self.s]['x_ptrm_check'])>0:
                pars['magic_method_codes']+=":LP-PI-ALT-PTRM"
        if 'x_tail_check' in self.Data[self.s].keys():
            if len(self.Data[self.s]['x_tail_check'])>0:
                pars['magic_method_codes']+=":LP-PI-BT-MD"


        #-------------------------------------------------
        # pTRM checks:
        # DRAT ()
        # and
        # DRATS (Tauxe and Staudigel 2004)
        #-------------------------------------------------

        x_ptrm_check_in_0_to_end,y_ptrm_check_in_0_to_end,x_Arai_compare=[],[],[]
        x_ptrm_check_in_start_to_end,y_ptrm_check_in_start_to_end=[],[]
        x_ptrm_check_for_SCAT,y_ptrm_check_for_SCAT=[],[]

        stop_scat_collect=False
        for k in range(len(self.Data[s]['ptrm_checks_temperatures'])):
          if self.Data[s]['ptrm_checks_temperatures'][k]<pars["measurement_step_max"] and self.Data[s]['ptrm_checks_temperatures'][k] in t_Arai:
            x_ptrm_check_in_0_to_end.append(self.Data[s]['x_ptrm_check'][k])
            y_ptrm_check_in_0_to_end.append(self.Data[s]['y_ptrm_check'][k])
            x_Arai_index=t_Arai.index(self.Data[s]['ptrm_checks_temperatures'][k])
            x_Arai_compare.append(x_Arai[x_Arai_index])
            if self.Data[s]['ptrm_checks_temperatures'][k]>=pars["measurement_step_min"]:
                x_ptrm_check_in_start_to_end.append(self.Data[s]['x_ptrm_check'][k])
                y_ptrm_check_in_start_to_end.append(self.Data[s]['y_ptrm_check'][k])
          if self.Data[s]['ptrm_checks_temperatures'][k] >= pars["measurement_step_min"] and self.Data[s]['ptrm_checks_starting_temperatures'][k] <= pars["measurement_step_max"] :
                x_ptrm_check_for_SCAT.append(self.Data[s]['x_ptrm_check'][k])
                y_ptrm_check_for_SCAT.append(self.Data[s]['y_ptrm_check'][k])
          # If triangle is within the interval but started after the upper temperature bound, then one pTRM check is included
          # For example: if T_max=480, the traingle in 450 fall far, and it started at 500, then it is included
          # the ateration occured between 450 and 500, we dont know when.
          if  stop_scat_collect==False and \
             self.Data[s]['ptrm_checks_temperatures'][k] < pars["measurement_step_max"] and self.Data[s]['ptrm_checks_starting_temperatures'][k] > pars["measurement_step_max"] :
                x_ptrm_check_for_SCAT.append(self.Data[s]['x_ptrm_check'][k])
                y_ptrm_check_for_SCAT.append(self.Data[s]['y_ptrm_check'][k])
                stop_scat_collect=True
              
              
        # scat uses a different definistion":
        # use only pTRM that STARTED before the last temperatire step.
        
        x_ptrm_check_in_0_to_end=array(x_ptrm_check_in_0_to_end)  
        y_ptrm_check_in_0_to_end=array(y_ptrm_check_in_0_to_end)
        x_Arai_compare=array(x_Arai_compare)
        x_ptrm_check_in_start_to_end=array(x_ptrm_check_in_start_to_end)
        y_ptrm_check_in_start_to_end=array(y_ptrm_check_in_start_to_end)
        x_ptrm_check_for_SCAT=array(x_ptrm_check_for_SCAT)
        y_ptrm_check_for_SCAT=array(y_ptrm_check_for_SCAT)
                               
        DRATS=100*(abs(sum(x_ptrm_check_in_0_to_end-x_Arai_compare))/(x_Arai[end]))
        int_ptrm_n=len(x_ptrm_check_in_0_to_end)
        if int_ptrm_n > 0:
           pars['specimen_int_ptrm_n']=int_ptrm_n
           pars['specimen_drats']=DRATS
        else:
           pars['specimen_int_ptrm_n']=int_ptrm_n
           pars['specimen_drats']=-1

        #-------------------------------------------------
        # Tail check MD
        #-------------------------------------------------

        # collect tail check data"
        x_tail_check_start_to_end,y_tail_check_start_to_end=[],[]
        x_tail_check_for_SCAT,y_tail_check_for_SCAT=[],[]

        for k in range(len(self.Data[s]['tail_check_temperatures'])):
          if self.Data[s]['tail_check_temperatures'][k] in t_Arai:
              if self.Data[s]['tail_check_temperatures'][k]<=pars["measurement_step_max"] and self.Data[s]['tail_check_temperatures'][k] >=pars["measurement_step_min"]:
                   x_tail_check_start_to_end.append(self.Data[s]['x_tail_check'][k]) 
                   y_tail_check_start_to_end.append(self.Data[s]['y_tail_check'][k]) 
          if self.Data[s]['tail_check_temperatures'][k] >= pars["measurement_step_min"] and self.Data[s]['tail_checks_starting_temperatures'][k] <= pars["measurement_step_max"] :
                x_tail_check_for_SCAT.append(self.Data[s]['x_tail_check'][k])
                y_tail_check_for_SCAT.append(self.Data[s]['y_tail_check'][k])

                
        x_tail_check_start_to_end=array(x_tail_check_start_to_end)
        y_tail_check_start_to_end=array(y_tail_check_start_to_end)
        x_tail_check_for_SCAT=array(x_tail_check_for_SCAT)
        y_tail_check_for_SCAT=array(y_tail_check_for_SCAT)

        #-------------------------------------------------                     
        # Tail check : TO DO !
        pars['specimen_md']=-1  
        #-------------------------------------------------                     

        #-------------------------------------------------                     
        # Calculate the new 'beta box' parameter
        # all datapoints, pTRM checks, and tail-checks, should be inside a "beta box"
        # For definition of "beta box" see Shaar and Tauxe (2012)
        #-------------------------------------------------                     

        if self.accept_new_parameters['specimen_scat']==True or self.accept_new_parameters['specimen_scat'] in [1,"True","TRUE",'1']:
        
            pars["fail_arai_beta_box_scatter"]=False
            pars["fail_ptrm_beta_box_scatter"]=False
            pars["fail_tail_beta_box_scatter"]=False
            
            # best fit line 
            b=pars['specimen_b']
            cm_x=mean(array(x_Arai_segment))
            cm_y=mean(array(y_Arai_segment))
            pars["specimen_cm_x"]=cm_x
            pars["specimen_cm_y"]=cm_y
            a=cm_y-b*cm_x

            # lines with slope = slope +/- 2*(specimen_b_beta)

            if 'specimen_b_beta' not in self.accept_new_parameters.keys():
             self.GUI_log.write ("-E- ERROR: specimen_beta not in pmag_criteria file, cannot calculate 'beta box' scatter\n") 

            b_beta_threshold=self.accept_new_parameters['specimen_b_beta']

            two_sigma_beta_threshold=2*b_beta_threshold
            two_sigma_slope_threshold=abs(two_sigma_beta_threshold*b)
                 
            # a line with a  shallower  slope  (b + 2*beta*b) passing through the center of mass
            b1=b+two_sigma_slope_threshold
            a1=cm_y-b1*cm_x

            # bounding line with steeper  slope (b - 2*beta*b) passing through the center of mass
            b2=b-two_sigma_slope_threshold
            a2=cm_y-b2*cm_x

            # lower bounding line of the 'beta box'
            slop1=a1/((a2/b2))
            intercept1=a1

            # higher bounding line of the 'beta box'
            slop2=a2/((a1/b1))
            intercept2=a2       

            pars['specimen_scat_bounding_line_high']=[intercept2,slop2]
            pars['specimen_scat_bounding_line_low']=[intercept1,slop1]
            
            # check if the Arai data points are in the 'box'

            x_Arai_segment=array(x_Arai_segment)
            y_Arai_segment=array(y_Arai_segment)

            # the two bounding lines
            ymin=intercept1+x_Arai_segment*slop1
            ymax=intercept2+x_Arai_segment*slop2

            # arrays of "True" or "False"
            check_1=y_Arai_segment>ymax
            check_2=y_Arai_segment<ymin

            # check if at least one "True" 
            if (sum(check_1)+sum(check_2))>0:
             pars["fail_arai_beta_box_scatter"]=True
             #print "check, fail beta box"


            # check if the pTRM checks data points are in the 'box'

            # using x_ptrm_check_in_segment (defined above)
            # using y_ptrm_check_in_segment (defined above)


            if len(x_ptrm_check_for_SCAT) > 0:

              # the two bounding lines
              ymin=intercept1+x_ptrm_check_for_SCAT*slop1
              ymax=intercept2+x_ptrm_check_for_SCAT*slop2

              # arrays of "True" or "False"
              check_1=y_ptrm_check_for_SCAT>ymax
              check_2=y_ptrm_check_for_SCAT<ymin


              # check if at least one "True" 
              if (sum(check_1)+sum(check_2))>0:
                pars["fail_ptrm_beta_box_scatter"]=True
                #print "check, fail fail_ptrm_beta_box_scatter"
                
            # check if the tail checks data points are in the 'box'


            if len(x_tail_check_for_SCAT) > 0:

              # the two bounding lines
              ymin=intercept1+x_tail_check_for_SCAT*slop1
              ymax=intercept2+x_tail_check_for_SCAT*slop2

              # arrays of "True" or "False"
              check_1=y_tail_check_for_SCAT>ymax
              check_2=y_tail_check_for_SCAT<ymin


              # check if at least one "True" 
              if (sum(check_1)+sum(check_2))>0:
                pars["fail_tail_beta_box_scatter"]=True
                #print "check, fail fail_ptrm_beta_box_scatter"

            if pars["fail_tail_beta_box_scatter"] or pars["fail_ptrm_beta_box_scatter"] or pars["fail_arai_beta_box_scatter"]:
                  pars["specimen_scat"]="Fail"
            else:
                  pars["specimen_scat"]="Pass"
        else:
            pars["specimen_scat"]="N/A"
        #-------------------------------------------------  
        # Calculate the new FRAC parameter (Shaar and Tauxe, 2012).
        # also check that the 'gap' between consecutive measurements is less than 0.5(VDS)
        #
        #-------------------------------------------------  

        vector_diffs=self.Data[s]['vector_diffs']
        vector_diffs_segment=vector_diffs[zstart:zend]
        FRAC=sum(vector_diffs_segment)/self.Data[s]['vds']
        max_FRAC_gap=max(vector_diffs_segment/sum(vector_diffs_segment))

        pars['specimen_frac']=FRAC
        pars['specimen_gmax']=max_FRAC_gap

        #-------------------------------------------------  
        # Check if specimen pass Acceptance criteria
        #-------------------------------------------------  

        pars['specimen_fail_criteria']=[]
        for key in self.high_threshold_velue_list:
            if key in ['specimen_gmax','specimen_b_beta']:
                value=round(pars[key],5)
            elif key in ['specimen_dang','specimen_int_mad']:
                value=round(pars[key],5)
            else:
                value=pars[key]
                
            if pars[key]>float(self.accept_new_parameters[key]):
                pars['specimen_fail_criteria'].append(key)
        for key in self.low_threshold_velue_list:
            if key in ['specimen_f','specimen_fvds','specimen_frac','specimen_g','specimen_q']:
                value=round(pars[key],5)
            else: 
                value=pars[key]
            if pars[key] < float(self.accept_new_parameters[key]):
                pars['specimen_fail_criteria'].append(key)
        if 'specimen_scat' in pars.keys():
            if pars["specimen_scat"]=="Fail":
                pars['specimen_fail_criteria'].append('specimen_scat')
        if 'specimen_mad_scat' in pars.keys():
            if pars["specimen_mad_scat"]=="Fail":
                pars['specimen_fail_criteria'].append('specimen_mad_scat')


        #-------------------------------------------------                     
        # Calculate the direction of pTMRMS
        #-------------------------------------------------                     


        #-------------------------------------------------            
        # Calculate anistropy correction factor
        #-------------------------------------------------            

        if "AniSpec" in self.Data[s].keys():
           pars["AC_WARNING"]=""
           # if both aarm and atrm tensor axist, try first the aarm. if it fails use the atrm.
           if 'AARM' in self.Data[s]["AniSpec"].keys() and 'ATRM' in self.Data[s]["AniSpec"].keys():
               TYPES=['AARM','ATRM']
           else:
               TYPES=self.Data[s]["AniSpec"].keys()
           for TYPE in TYPES:
               red_flag=False
               S_matrix=zeros((3,3),'f')
               S_matrix[0,0]=self.Data[s]['AniSpec'][TYPE]['anisotropy_s1']
               S_matrix[1,1]=self.Data[s]['AniSpec'][TYPE]['anisotropy_s2']
               S_matrix[2,2]=self.Data[s]['AniSpec'][TYPE]['anisotropy_s3']
               S_matrix[0,1]=self.Data[s]['AniSpec'][TYPE]['anisotropy_s4']
               S_matrix[1,0]=self.Data[s]['AniSpec'][TYPE]['anisotropy_s4']
               S_matrix[1,2]=self.Data[s]['AniSpec'][TYPE]['anisotropy_s5']
               S_matrix[2,1]=self.Data[s]['AniSpec'][TYPE]['anisotropy_s5']
               S_matrix[0,2]=self.Data[s]['AniSpec'][TYPE]['anisotropy_s6']
               S_matrix[2,0]=self.Data[s]['AniSpec'][TYPE]['anisotropy_s6']

               #self.Data[s]['AniSpec']['anisotropy_type']=self.Data[s]['AniSpec']['anisotropy_type']
               self.Data[s]['AniSpec'][TYPE]['anisotropy_n']=int(float(self.Data[s]['AniSpec'][TYPE]['anisotropy_n']))

               this_specimen_f_type=self.Data[s]['AniSpec'][TYPE]['anisotropy_type']+"_"+"%i"%(int(self.Data[s]['AniSpec'][TYPE]['anisotropy_n']))
               
               Ftest_crit={} 
               Ftest_crit['ATRM_6']=  3.1059
               Ftest_crit['AARM_6']=  3.1059
               Ftest_crit['AARM_9']= 2.6848
               Ftest_crit['AARM_15']= 2.4558

               # threshold value for Ftest:
               
               if 'AniSpec' in self.Data[s].keys() and TYPE in self.Data[s]['AniSpec'].keys()\
                  and 'anisotropy_sigma' in  self.Data[s]['AniSpec'][TYPE].keys() \
                  and self.Data[s]['AniSpec'][TYPE]['anisotropy_sigma']!="":
                  # Calculate Ftest. If Ftest exceeds threshold value: set anistropy tensor to identity matrix
                   sigma=float(self.Data[s]['AniSpec'][TYPE]['anisotropy_sigma'])             
                   nf = 3*int(self.Data[s]['AniSpec'][TYPE]['anisotropy_n'])-6
                   F=calculate_ftest(S_matrix,sigma,nf)
                   #print s,"F",F
                   self.Data[s]['AniSpec'][TYPE]['ftest']=F
                   #print "s,sigma,nf,F,Ftest_crit[this_specimen_f_type]"
                   #print s,sigma,nf,F,Ftest_crit[this_specimen_f_type]
                   if self.accept_new_parameters['check_aniso_ftest']:
                       Ftest_threshold=Ftest_crit[this_specimen_f_type]
                       if self.Data[s]['AniSpec'][TYPE]['ftest'] < Ftest_crit[this_specimen_f_type]:
                           S_matrix=identity(3,'f')
                           pars["AC_WARNING"]=pars["AC_WARNING"]+"%s tensor fails F-test; "%(TYPE)
                           red_flag=True
                           
               else:
                   self.Data[s]['AniSpec'][TYPE]['anisotropy_sigma']=""
                   self.Data[s]['AniSpec'][TYPE]['ftest']=99999
     
                
               if 'anisotropy_alt' in self.Data[s]['AniSpec'][TYPE].keys() and self.Data[s]['AniSpec'][TYPE]['anisotropy_alt']!="":
                   if float(self.Data[s]['AniSpec'][TYPE]['anisotropy_alt']) > float(self.accept_new_parameters['anisotropy_alt']):
                       S_matrix=identity(3,'f')
                       pars["AC_WARNING"]=pars["AC_WARNING"]+"%s tensor fails alteration check: %.1f%% > %.1f%%; "%(TYPE,float(self.Data[s]['AniSpec'][TYPE]['anisotropy_alt']),float(self.accept_new_parameters['anisotropy_alt']))
                       red_flag=True
               else:
                   self.Data[s]['AniSpec'][TYPE]['anisotropy_alt']=""

               self.Data[s]['AniSpec'][TYPE]['S_matrix']=S_matrix 
           #--------------------------  
           # if AARM passes all, use the AARM.
           # if ATRM fail alteration use the AARM
           # if both fail F-test: use AARM
           if len(TYPES)>1:
               if "ATRM tensor fails alteration check" in pars["AC_WARNING"]:
                   TYPE='AARM'
               elif "ATRM tensor fails F-test" in pars["AC_WARNING"]:
                   TYPE='AARM'
               else: 
                   TYPE=='AARM'
           S_matrix= self.Data[s]['AniSpec'][TYPE]['S_matrix']
           #---------------------------        
           TRM_anc_unit=array(pars['specimen_PCA_v1'])/sqrt(pars['specimen_PCA_v1'][0]**2+pars['specimen_PCA_v1'][1]**2+pars['specimen_PCA_v1'][2]**2)
           B_lab_unit=self.dir2cart([ self.Data[s]['Thellier_dc_field_phi'], self.Data[s]['Thellier_dc_field_theta'],1])
           #B_lab_unit=array([0,0,-1])
           Anisotropy_correction_factor=linalg.norm(dot(inv(S_matrix),TRM_anc_unit.transpose()))*norm(dot(S_matrix,B_lab_unit))
           pars["Anisotropy_correction_factor"]=Anisotropy_correction_factor
           pars["AC_specimen_int"]= pars["Anisotropy_correction_factor"] * float(pars["specimen_int"])
           
           pars["AC_anisotropy_type"]=self.Data[s]['AniSpec'][TYPE]["anisotropy_type"]
           pars["specimen_int_uT"]=float(pars["AC_specimen_int"])*1e6
           if TYPE=='AARM':
               if ":LP-AN-ARM" not in pars['magic_method_codes']:
                  pars['magic_method_codes']+=":LP-AN-ARM:AE-H:DA-AC-AARM"
                  pars['specimen_correction']='c'
                  pars['specimen_int_corr_anisotropy']=Anisotropy_correction_factor
           if TYPE=='ATRM':
               if ":LP-AN-TRM" not in pars['magic_method_codes']:
                  pars['magic_method_codes']+=":LP-AN-TRM:AE-H:DA-AC-ATRM"
                  pars['specimen_correction']='c' 
                  pars['specimen_int_corr_anisotropy']=Anisotropy_correction_factor

 
        else:
           pars["Anisotropy_correction_factor"]=1.0
           pars["specimen_int_uT"]=float(pars["specimen_int"])*1e6
           pars["AC_WARNING"]="No anistropy correction"
           pars['specimen_correction']='u' 

        pars["specimen_int_corr_anisotropy"]=pars["Anisotropy_correction_factor"]   
        #-------------------------------------------------                    
        # NLT and anisotropy correction together in one equation
        # See Shaar et al (2010), Equation (3)
        #-------------------------------------------------

        if 'NLT_parameters' in self.Data[s].keys():

           alpha=self.Data[s]['NLT_parameters']['tanh_parameters'][0][0]
           beta=self.Data[s]['NLT_parameters']['tanh_parameters'][0][1]
           b=float(pars["specimen_b"])
           Fa=pars["Anisotropy_correction_factor"]

           if ((abs(b)*Fa)/alpha) <1.0:
               Banc_NLT=math.atanh( ((abs(b)*Fa)/alpha) ) / beta
               pars["NLTC_specimen_int"]=Banc_NLT
               pars["specimen_int_uT"]=Banc_NLT*1e6

               if "AC_specimen_int" in pars.keys():
                   pars["NLT_specimen_correction_factor"]=Banc_NLT/float(pars["AC_specimen_int"])
               else:                       
                   pars["NLT_specimen_correction_factor"]=Banc_NLT/float(pars["specimen_int"])
               if ":LP-TRM" not in pars['magic_method_codes']:
                  pars['magic_method_codes']+=":LP-TRM:DA-NL"
               pars['specimen_correction']='c' 

           else:
               self.GUI_log.write ("-W- WARNING: problematic NLT mesurements for specimens %s. Cant do NLT calculation. check data\n"%s)
               pars["NLT_specimen_correction_factor"]=-1
        else:
           pars["NLT_specimen_correction_factor"]=-1

        #-------------------------------------------------                    
        # Calculate the final result with cooling rate correction
        #-------------------------------------------------

        pars["specimen_int_corr_cooling_rate"]=-999
        if 'cooling_rate_data' in self.Data[s].keys():
            if 'CR_correction_factor' in self.Data[s]['cooling_rate_data'].keys():
                if self.Data[s]['cooling_rate_data']['CR_correction_factor'] != -1 and self.Data[s]['cooling_rate_data']['CR_correction_factor'] !=-999:
                    pars["specimen_int_corr_cooling_rate"]=self.Data[s]['cooling_rate_data']['CR_correction_factor']
                    pars['specimen_correction']='c'
                    pars["specimen_int_uT"]=pars["specimen_int_uT"]*pars["specimen_int_corr_cooling_rate"]
                    if ":DA-CR" not in pars['magic_method_codes']:
                      pars['magic_method_codes']+=":DA-CR"
                    if   'CR_correction_factor_flag' in self.Data[s]['cooling_rate_data'].keys():
                        if self.Data[s]['cooling_rate_data']['CR_correction_factor_flag']=="calculated":
                            pars['CR_flag']="calculated"
                        else:
                            pars['CR_flag']=""
                    if 'CR_correction_factor_flag' in self.Data[s]['cooling_rate_data'].keys() \
                       and self.Data[s]['cooling_rate_data']['CR_correction_factor_flag']!="calculated":
                        pars["CR_WARNING"]="inferred cooling rate correction"
                    
                
        else:
            pars["CR_WARNING"]="no cooling rate correction"
            
##            sample=self.Data_hierarchy['specimens'][self.s]
##            if sample in Data_info["er_samples"]:
##                if 'sample_type' in Data_info["er_samples"][sample].keys():
##                    if Data_info["er_samples"][sample]['sample_type'] in ["Baked Clay","Baked Mud",

        return(pars)
        
#    def get_site_means(self):
#
# 
#        if self.accept_new_parameters['average_by_sample_or_site']=='site':
#            AV_BY_SAMPLE=False; AV_BY_SITE=True
#        else:
#            AV_BY_SAMPLE=True; AV_BY_SITE=False
#
#        if AV_BY_SAMPLE:
#        for sample in self.Data_samples.keys():
#                       
#            if sample len(self.Data_samples[sample].keys())>0:
#                if self.s not in self.Data_samples[sample].keys():
#                    if 'specimen_int_uT' in self.pars.keys():
#                        B.append(self.pars['specimen_int_uT'])
#                for specimen in self.Data_samples[sample].keys():
#                    if specimen==self.s:
#                        if 'specimen_int_uT' in self.pars.keys():
#                            B.append(self.pars['specimen_int_uT'])
#                        else:        
#                            B.append(self.Data_samples[sample][specimen])
#                    else:
#                            B.append(self.Data_samples[sample][specimen])
                               
        
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
        a=mean(y_Arai_segment) - b* mean(x_Arai_segment)
        xx=array([x_Arai_segment[0],x_Arai_segment[-1]])
        yy=b*xx+a
        self.araiplot.plot(xx,yy,'g-',lw=2,alpha=0.5)
        if self.accept_new_parameters['specimen_scat']==True:
            yy1=xx*pars['specimen_scat_bounding_line_low'][1]+pars['specimen_scat_bounding_line_low'][0]
            yy2=xx*pars['specimen_scat_bounding_line_high'][1]+pars['specimen_scat_bounding_line_high'][0]
            self.araiplot.plot(xx,yy1,'--',lw=0.5,alpha=0.5)
            self.araiplot.plot(xx,yy2,'--',lw=0.5,alpha=0.5)

        self.araiplot.set_xlim(xmin=0)
        self.araiplot.set_ylim(ymin=0)
        
        draw()
        self.canvas1.draw()

        # plot best fit direction on Equal Area plot
        CART=array(pars["specimen_PCA_v1"])/sqrt(sum(array(pars["specimen_PCA_v1"])**2))
        x=CART[0]
        y=CART[1]
        z=abs(CART[2])
        R=array(sqrt(1-z)/sqrt(x**2+y**2))
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
        NRM_dir=self.cart2dir(self.Data[self.s]['zdata'][0])         
        NRM_dec=NRM_dir[0]

        #PCA direction
        PCA_dir_rotated=self.cart2dir(CART)         
        PCA_dir_rotated[0]=PCA_dir_rotated[0]-NRM_dec      
        PCA_CART_rotated=self.dir2cart(PCA_dir_rotated)

        tmin_index=self.Data[self.s]['z_temp'].index(self.pars["measurement_step_min"])
        tmax_index=self.Data[self.s]['z_temp'].index(self.pars["measurement_step_max"])
        
        PCA_dir_rotated=self.cart2dir(CART)         
        PCA_dir_rotated[0]=PCA_dir_rotated[0]-NRM_dec      
        PCA_CART_rotated=self.dir2cart(PCA_dir_rotated)
        
        slop_xy_PCA=-1*PCA_CART_rotated[1]/PCA_CART_rotated[0]
        slop_xz_PCA=-1*PCA_CART_rotated[2]/PCA_CART_rotated[0]

        # Center of mass rotated
        
        CM_x=mean(self.CART_rot[:,0][tmin_index:tmax_index+1])
        CM_y=mean(self.CART_rot[:,1][tmin_index:tmax_index+1])
        CM_z=mean(self.CART_rot[:,2][tmin_index:tmax_index+1])

        # intercpet from the center of mass
        intercept_xy_PCA=-1*CM_y - slop_xy_PCA*CM_x
        intercept_xz_PCA=-1*CM_z - slop_xz_PCA*CM_x

        xmin_zij, xmax_zij = xlim()
        xx=array([0,self.CART_rot[:,0][tmin_index]])
        yy=slop_xy_PCA*xx+intercept_xy_PCA
        self.zijplot.plot(xx,yy,'-',color='g',lw=1.5,alpha=0.5)
        zz=slop_xz_PCA*xx+intercept_xz_PCA
        self.zijplot.plot(xx,zz,'-',color='g',lw=1.5,alpha=0.5)

    
        self.zijplot.scatter([self.CART_rot[:,0][tmin_index]],[-1* self.CART_rot[:,1][tmin_index]],marker='o',s=40,facecolor='g',edgecolor ='k',zorder=100)
        self.zijplot.scatter([self.CART_rot[:,0][tmax_index]],[-1* self.CART_rot[:,1][tmax_index]],marker='o',s=40,facecolor='g',edgecolor ='k',zorder=100)
        self.zijplot.scatter([self.CART_rot[:,0][tmin_index]],[-1* self.CART_rot[:,2][tmin_index]],marker='s',s=50,facecolor='g',edgecolor ='k',zorder=100)
        self.zijplot.scatter([self.CART_rot[:,0][tmax_index]],[-1* self.CART_rot[:,2][tmax_index]],marker='s',s=50,facecolor='g',edgecolor ='k',zorder=100)


##        # draw MAD-box
##        self.accept_new_parameters['specimen_mad_scat']=True
##        if 'specimen_mad_scat' in self.accept_new_parameters.keys() and 'specimen_int_mad' in self.accept_new_parameters.keys() :
##            if self.accept_new_parameters['specimen_mad_scat']==True or self.accept_new_parameters['specimen_mad_scat'] in [1,"True","TRUE",'1']:
##
##                # center of mass 
##                CM=array([CM_x,CM_y,CM_z])
##
##                # threshold value for the distance of the point from a line:
##                # this is depends of MAD
##                # if MAD= tan-1 [ sigma_perpendicular / sigma_max ]
##                # then:
##                # sigma_perpendicular_threshold=tan(MAD_threshold)*sigma_max
##                sigma_perpendicular_threshold=abs(tan(radians(self.accept_new_parameters['specimen_int_mad'])) *  self.pars["specimen_PCA_sigma_max"] )
##                mad_box_xy_x1,mad_box_xy_x2=[],[]                
##                mad_box_xy_y1,mad_box_xy_y2=[],[]                
##                mad_box_xz_x1,mad_box_xz_x2=[],[]                
##                mad_box_xz_y1,mad_box_xz_y2=[],[]                
##
##                for i in range(len(xx)):
##                    #xy_x_plus=array(xx[i],yy[i])
##                                        
##                    # X-Y projectoin
##                    x_y_projection=cross(array(PCA_CART_rotated),array([0,0,1]))
##                    x_y_projection=x_y_projection/sqrt(sum(x_y_projection**2))
##                    new_vector1=array([xx[i],yy[i]])+2*sigma_perpendicular_threshold*array([x_y_projection[0],x_y_projection[1]])
##                    new_vector2=array([xx[i],yy[i]])-2*sigma_perpendicular_threshold*array([x_y_projection[0],x_y_projection[1]])
##                    mad_box_xy_x1.append(new_vector1[0])
##                    mad_box_xy_y1.append(new_vector1[1])
##                    mad_box_xy_x2.append(new_vector2[0])
##                    mad_box_xy_y2.append(new_vector2[1])
##                                                            
##
##                    # X-Z projectoin
##                    x_z_projection=cross(array(PCA_CARTated),array([0,1,0]))
##                    x_z_projection=x_z_projection/sqrt(sum(x_z_projection**2))
##                    new_vector1=array([xx[i],zz[i]])+2*sigma_perpendicular_threshold*array([x_z_projection[0],x_z_projection[2]])
##                    new_vector2=array([xx[i],zz[i]])-2*sigma_perpendicular_threshold*array([x_z_projection[0],x_z_projection[2]])
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
           self.mplot.scatter([Banc],[alpha*(tanh(beta*Banc*1e-6))],marker='o',s=30,facecolor='g',edgecolor ='k')

        self.canvas5.draw()
        draw()

        #------
        # Drow sample mean
        #------

        self.draw_sample_mean()

        
    def draw_sample_mean(self):

        self.sampleplot.clear()
        specimens_id=[]
        specimens_B=[]
        sample=self.Data_hierarchy['specimens'][self.s]
        site=self.get_site_from_hierarchy(sample)
        
        # average by sample
        #print self.accept_new_parameters['average_by_sample_or_site']
        if self.accept_new_parameters['average_by_sample_or_site']=='sample':
            if sample in self.Data_samples.keys():
                for spec in self.Data_samples[sample].keys():
                    specimens_id.append(spec)
                if self.s not in specimens_id and 'specimen_int_uT' in self.pars.keys():
                    specimens_id.append(self.s)
                specimens_id.sort()
                for spec in specimens_id:
                    if spec==self.s and 'specimen_int_uT' in self.pars.keys():
                        specimens_B.append(self.pars['specimen_int_uT'])
                    else:
                        specimens_B.append(self.Data_samples[sample][spec])
            else:
                if 'specimen_int_uT' in self.pars.keys():
                    specimens_id=[self.s]
                    specimens_B=[self.pars['specimen_int_uT']]
        # average by site
        else:
            if site in self.Data_sites.keys():
                for spec in self.Data_sites[site].keys():
                    specimens_id.append(spec)
                if self.s not in specimens_id and 'specimen_int_uT' in self.pars.keys():
                    specimens_id.append(self.s)
                specimens_id.sort()
                for spec in specimens_id:
                    if spec==self.s and 'specimen_int_uT' in self.pars.keys():
                        specimens_B.append(self.pars['specimen_int_uT'])
                    else:
                        specimens_B.append(self.Data_sites[site][spec])
            else:
                if 'specimen_int_uT' in self.pars.keys():
                    specimens_id=[self.s]
                    specimens_B=[self.pars['specimen_int_uT']]
            
        if len(specimens_id)>=1:
            self.sampleplot.scatter(arange(len(specimens_id)),specimens_B ,marker='s',edgecolor='0.2', facecolor='b',s=40*self.GUI_RESOLUTION,lw=1)
            self.sampleplot.axhline(y=mean(specimens_B)+std(specimens_B,ddof=1),color='0.2',ls="--",lw=0.75)
            self.sampleplot.axhline(y=mean(specimens_B)-std(specimens_B,ddof=1),color='0.2',ls="--",lw=0.75)
            self.sampleplot.axhline(y=mean(specimens_B),color='0.2',ls="-",lw=0.75,alpha=0.5)
            
            if self.s in specimens_id:
                self.sampleplot.scatter([specimens_id.index(self.s)],[specimens_B[specimens_id.index(self.s)]] ,marker='s',edgecolor='0.2', facecolor='g',s=40*self.GUI_RESOLUTION,lw=1)

            self.sampleplot.set_xticks(arange(len(specimens_id)))
            self.sampleplot.set_xlim(-0.5,len(specimens_id)-0.5)
            self.sampleplot.set_xticklabels(specimens_id,rotation=90,fontsize=8)
            #ymin,ymax=self.sampleplot.ylim()
            
            if "sample_int_sigma_uT" in self.accept_new_parameters.keys() and "sample_int_sigma_perc" in self.accept_new_parameters.keys():                
                sigma_threshold_for_plot=max(self.accept_new_parameters["sample_int_sigma_uT"],0.01*self.accept_new_parameters["sample_int_sigma_perc"]*mean(specimens_B))
            elif "sample_int_sigma_uT" in self.accept_new_parameters.keys() :
                sigma_threshold_for_plot=self.accept_new_parameters["sample_int_sigma_uT"]                
            elif "sample_int_sigma_perc" in self.accept_new_parameters.keys() :
                sigma_threshold_for_plot=mean(specimens_B)*0.01*self.accept_new_parameters["sample_int_sigma_perc"]
            else:
                sigma_threshold_for_plot =100000
            if sigma_threshold_for_plot < 20:
                self.sampleplot.axhline(y=mean(specimens_B)+sigma_threshold_for_plot,color='r',ls="--",lw=0.75)
                self.sampleplot.axhline(y=mean(specimens_B)-sigma_threshold_for_plot,color='r',ls="--",lw=0.75)
                y_axis_limit=max(sigma_threshold_for_plot,std(specimens_B,ddof=1),abs(max(specimens_B)-mean(specimens_B)),abs((min(specimens_B)-mean(specimens_B))))
            else:
                y_axis_limit=max(std(specimens_B,ddof=1),abs(max(specimens_B)-mean(specimens_B)),abs((min(specimens_B)-mean(specimens_B))))
                
            self.sampleplot.set_ylim(mean(specimens_B)-y_axis_limit-1,mean(specimens_B)+y_axis_limit+1)
            self.sampleplot.set_ylabel(r'$\mu$ T',fontsize=8)
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
    



    def get_default_criteria(self):
      #------------------------------------------------
      # read criteria file
      # Format is as pmag_criteria.txt
      #------------------------------------------------


      self.criteria_list=['specimen_int_n','specimen_int_ptrm_n','specimen_f','specimen_fvds','specimen_frac','specimen_gmax','specimen_b_beta',
                     'specimen_dang','specimen_drats','specimen_int_mad','specimen_md','specimen_g','specimen_q']
      self.high_threshold_velue_list=['specimen_gmax','specimen_b_beta','specimen_dang','specimen_drats','specimen_int_mad','specimen_md']
      self.low_threshold_velue_list=['specimen_int_n','specimen_int_ptrm_n','specimen_f','specimen_fvds','specimen_frac','specimen_g','specimen_q']

      accept_new_parameters_null={}
      accept_new_parameters_default={}
      #  make a list of default parameters

      accept_new_parameters_default['specimen_int_n']=3
      accept_new_parameters_default['specimen_int_ptrm_n']=2
      accept_new_parameters_default['specimen_f']=0.
      accept_new_parameters_default['specimen_fvds']=0.
      accept_new_parameters_default['specimen_frac']=0.8
      accept_new_parameters_default['specimen_gmax']=0.6
      accept_new_parameters_default['specimen_b_beta']=0.1
      accept_new_parameters_default['specimen_dang']=100000
      accept_new_parameters_default['specimen_drats']=100000
      accept_new_parameters_default['specimen_int_mad']=5
      accept_new_parameters_default['specimen_md']=100000
      accept_new_parameters_default['specimen_g']=0
      accept_new_parameters_default['specimen_q']=0
      accept_new_parameters_default['specimen_scat']=True

      accept_new_parameters_default['sample_int_n']=3
      accept_new_parameters_default['sample_int_n_outlier_check']=1000

      # anistropy criteria
      accept_new_parameters_default['anisotropy_alt']=10
      accept_new_parameters_default['check_aniso_ftest']=True


      # Sample mean calculation type 
      accept_new_parameters_default['sample_int_stdev_opt']=True
      accept_new_parameters_default['sample_int_bs']=False
      accept_new_parameters_default['sample_int_bs_par']=False

      # Averaging sample or site calculation type 

      accept_new_parameters_default['average_by_sample_or_site']='sample'

      # STDEV-OPT  
      accept_new_parameters_default['sample_int_sigma_uT']=6
      accept_new_parameters_default['sample_int_sigma_perc']=10
      accept_new_parameters_default['sample_aniso_threshold_perc']=1000000
      accept_new_parameters_default['sample_int_interval_uT']=10000
      accept_new_parameters_default['sample_int_interval_perc']=10000

      # BS  
      accept_new_parameters_default['sample_int_BS_68_uT']=10000
      accept_new_parameters_default['sample_int_BS_68_perc']=10000
      accept_new_parameters_default['sample_int_BS_95_uT']=10000
      accept_new_parameters_default['sample_int_BS_95_perc']=10000
      accept_new_parameters_default['specimen_int_max_slope_diff']=10000

      # NULL  
      for key in ( accept_new_parameters_default.keys()):
          accept_new_parameters_null[key]=accept_new_parameters_default[key]
      accept_new_parameters_null['sample_int_stdev_opt']=False
      accept_new_parameters_null['specimen_frac']=0
      accept_new_parameters_null['specimen_gmax']=10000
      accept_new_parameters_null['specimen_b_beta']=10000
      accept_new_parameters_null['specimen_int_mad']=100000
      accept_new_parameters_null['specimen_scat']=False
      accept_new_parameters_null['specimen_int_ptrm_n']=0
      accept_new_parameters_null['anisotropy_alt']=1e10
      accept_new_parameters_null['check_aniso_ftest']=True
      accept_new_parameters_default['sample_aniso_threshold_perc']=1000000

      #accept_new_parameters_null['sample_int_sigma_uT']=0
      #accept_new_parameters_null['sample_int_sigma_perc']=0
      #accept_new_parameters_null['sample_int_n_outlier_check']=100000

      
      #print accept_new_parameters_default
        
      # A list of all acceptance criteria used by program
      accept_specimen_keys=['specimen_int_n','specimen_int_ptrm_n','specimen_f','specimen_fvds','specimen_frac','specimen_gmax','specimen_b_beta','specimen_dang','specimen_drats','specimen_int_mad','specimen_md']
      accept_sample_keys=['sample_int_n','sample_int_sigma_uT','sample_int_sigma_perc','sample_aniso_threshold_perc','sample_int_interval_uT','sample_int_interval_perc']
      
      #self.accept_new_parameters_null=accept_new_parameters_null
      return(accept_new_parameters_default,accept_new_parameters_null)
      #print accept_new_parameters_default
      #print "yes"

      
    def get_data(self):
      

      def tan_h(x, a, b):
            return a*tanh(b*x)

      def cart2dir(cart): # OLD ONE
            """
            converts a direction to cartesian coordinates
            """
            Dir=[] # establish a list to put directions in
            rad=pi/180. # constant to convert degrees to radians
            R=sqrt(cart[0]**2+cart[1]**2+cart[2]**2) # calculate resultant vector length
            if R==0:
               #print 'trouble in cart2dir'
               #print cart
               return [0.0,0.0,0.0]
            D=arctan2(cart[1],cart[0])/rad  # calculate declination taking care of correct quadrants (arctan2)
            if D<0:D=D+360. # put declination between 0 and 360.
            if D>360.:D=D-360.
            Dir.append(D)  # append declination to Dir list
            I=arcsin(cart[2]/R)/rad # calculate inclination (converting to degrees)
            Dir.append(I) # append inclination to Dir list
            Dir.append(R) # append vector length to Dir list
            return Dir # return the directions list


      def dir2cart(d):
       # converts list or array of vector directions, in degrees, to array of cartesian coordinates, in x,y,z
        ints=ones(len(d)).transpose() # get an array of ones to plug into dec,inc pairs
        d=array(d)
        rad=pi/180.
        if len(d.shape)>1: # array of vectors
            decs,incs=d[:,0]*rad,d[:,1]*rad
            if d.shape[1]==3: ints=d[:,2] # take the given lengths
        else: # single vector
            decs,incs=array(d[0])*rad,array(d[1])*rad
            if len(d)==3: 
                ints=array(d[2])
            else:
                ints=array([1.])
        cart= array([ints*cos(decs)*cos(incs),ints*sin(decs)*cos(incs),ints*sin(incs)]).transpose()
        return cart

      #self.dir_pathes=self.WD


      #------------------------------------------------
      # Read magic measurement file and sort to blocks
      #------------------------------------------------

      # All data information is stored in Data[secimen]={}
      Data={}
      Data_hierarchy={}
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
          meas_data,file_type=self.magic_read(self.magic_file)
      except:
          print "-E- ERROR: Cant read magic_measurement.txt file. File is corrupted."
          return {},{}

      #print "done Magic read %s " %self.magic_file

      self.GUI_log.write("-I- Read magic file  %s\n"%self.magic_file)

      # get list of unique specimen names
      
      CurrRec=[]
      #print "get sids"
      sids=self.get_specs(meas_data) # samples ID's
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

          EX=["LP-AN-ARM","LP-AN-TRM","LP-ARM-AFD","LP-ARM2-AFD","LP-TRM-AFD","LP-TRM","LP-TRM-TD","LP-X"] # list of excluded lab protocols
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
          
          if s not in Data_hierarchy['samples'][sample]:
              Data_hierarchy['samples'][sample].append(s)

          if sample not in Data_hierarchy['sites'][site]:
              Data_hierarchy['sites'][site].append(sample)

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
          rmag_anis_data,file_type=self.magic_read(self.WD+'/rmag_anisotropy.txt')
          self.GUI_log.write( "-I- Anisotropy data read  %s/from rmag_anisotropy.txt\n"%self.WD)
      except:
          self.GUI_log.write("-W- WARNING cant find rmag_anisotropy in working directory\n")

      try:
          results_anis_data,file_type=self.magic_read(self.WD+'/rmag_results.txt')
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


          for rec in datablock:
              if float(rec['treatment_temp'])==NLT_temperature and float(rec['treatment_dc_field']) !=0:
                  B_NLT.append(float(rec['treatment_dc_field']))
                  M_NLT.append(float(rec['measurement_magn_moment']))
                  
    
          # If cnat find baseline in trm block
          #  search for baseline in the Data block. 
          if M_baseline==0:
              m_tmp=[]
              for rec in datablock:
                  if float(rec['treatment_temp'])==NLT_temperature and float(rec['treatment_dc_field'])==0:
                     m_tmp.append(float(rec['measurement_magn_moment']))
                     self.GUI_log.write("-I- Found basleine for NLT measurements in datablock, specimen %s\n"%s)         
              if len(m_tmp)>0:
                  M_baseline=mean(m_tmp)
              

          ####  Ron dont delete it ### print "-I- Found %i NLT datapoints for specimen %s: B="%(len(B_NLT),s),array(B_NLT)*1e6

          #substitute baseline
          M_NLT=array(M_NLT)-M_baseline
          B_NLT=array(B_NLT)  
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
                  if (max(M)-min(M))/mean(M) > 0.05:
                    self.GUI_log.write("-E- ERROR: NLT for specimen %s does not pass 5 perc alteration check: %.3f \n" %(s,(max(M)-min(M))/mean(M)))
                    red_flag=True
                    
                      
                  
          if len(trmblock)>2 and not red_flag:
           
              B_NLT=append([0.],B_NLT)
              M_NLT=append([0.],M_NLT)
              
              try:
                  #print s,B_NLT, M_NLT    
                  # First try to fit tanh function (add point 0,0 in the begining)
                  alpha_0=max(M_NLT)
                  beta_0=2e4
                  popt, pcov = curve_fit(tan_h, B_NLT, M_NLT,p0=(alpha_0,beta_0))
                  M_lab=popt[0]*math.tanh(labfield*popt[1])

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
                    lan_cooling_rates.append(math.log(cooling_rate_data['lab_cooling_rate']/pair[0]))
                    moments.append(pair[1])
                    if pair[0]==cooling_rate_data['lab_cooling_rate']:
                        lab_fast_cr_moments.append(pair[1])
              #print s, cooling_rate_data['alteration_check']
              lan_cooling_rates.append(math.log(cooling_rate_data['lab_cooling_rate']/cooling_rate_data['alteration_check'][0]))
              lab_fast_cr_moments.append(cooling_rate_data['alteration_check'][1])
              moments.append(cooling_rate_data['alteration_check'][1])        

              lab_fast_cr_moment=mean(lab_fast_cr_moments)
              moment_norm=array(moments)/lab_fast_cr_moment
              (a,b)=polyfit(lan_cooling_rates, moment_norm, 1)
              #ancient_cooling_rate=0.41
              x0=math.log(cooling_rate_data['lab_cooling_rate']/ancient_cooling_rate)
              y0=a*x0+b
              MAX=max(lab_fast_cr_moments)
              MIN=min(lab_fast_cr_moments)
              
              #print MAX,MIN
              #print (MAX-MIN)/mean(MAX,MIN)
              #print abs((MAX-MIN)/mean(MAX,MIN))
              if  mean([MAX,MIN])==0:
                  alteration_check_perc=0
              else:
                  alteration_check_perc=100*abs((MAX-MIN)/mean([MAX,MIN]))
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
              mean_CR_correction=mean(CR_corrections)
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
            DIR=[zijdblock[k][1],zijdblock[k][2],zijdblock[k][3]/NRM]
            cart=self.dir2cart(DIR)
            zdata.append(array([cart[0],cart[1],cart[2]]))
            if k>0:
                vector_diffs.append(sqrt(sum((array(zdata[-2])-array(zdata[-1]))**2)))
        vector_diffs.append(sqrt(sum(array(zdata[-1])**2))) # last vector of the vds
        vds=sum(vector_diffs)  # vds calculation       
        zdata=array(zdata)

        Data[s]['vector_diffs']=array(vector_diffs)
        Data[s]['vds']=vds
        Data[s]['zdata']=zdata
        Data[s]['z_temp']=z_temperatures
        
      #--------------------------------------------------------------    
      # Rotate zijderveld plot
      #--------------------------------------------------------------

        DIR_rot=[]
        CART_rot=[]
        # rotate to be as NRM
        NRM_dir=self.cart2dir(Data[s]['zdata'][0])
         
        NRM_dec=NRM_dir[0]
        NRM_dir[0]=0
        CART_rot.append(self.dir2cart(NRM_dir))

        
        for i in range(1,len(Data[s]['zdata'])):
          DIR=self.cart2dir(Data[s]['zdata'][i])
          DIR[0]=DIR[0]-NRM_dec
          CART_rot.append(array(self.dir2cart(DIR)))
          #print array(dir2cart(DIR))
          
        CART_rot=array(CART_rot)
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
        x_Arai=array(x_Arai)
        y_Arai=array(y_Arai)
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
            # find the starting point of the pTRM check:
            for i in range(len(datablock)):
                rec=datablock[i]

                if MICROWAVE:
                    if "measurement_description" in rec.keys():
                        MW_step=rec["measurement_description"].strip('\n').split(":")
                        for STEP in MW_step:
                            if "Number" in STEP:
                                this_temp=float(STEP.split("-")[-1])
                
                if  (THERMAL and "LT-PTRM-I" in rec['magic_method_codes'] and float(rec['treatment_temp'])==ptrm_checks[k][0])\
                   or (MICROWAVE and "LT-PMRM-I" in rec['magic_method_codes'] and float(this_temp)==float(ptrm_checks[k][0])) :
                    if THERMAL:
                        starting_temperature=(float(datablock[i-1]['treatment_temp']))
                    elif MICROWAVE:
                        MW_step=datablock[i-1]["measurement_description"].strip('\n').split(":")
                        for STEP in MW_step:
                            if "Number" in STEP:
                                starting_temperature=float(STEP.split("-")[-1])
                                                

                    try:
                        index=t_Arai.index(starting_temperature)
                        x_ptrm_check_starting_point.append(x_Arai[index])
                        y_ptrm_check_starting_point.append(y_Arai[index])
                        ptrm_checks_starting_temperatures.append(starting_temperature)

                        index_zerofield=zerofield_temperatures.index(ptrm_checks[k][0])
                        x_ptrm_check.append(ptrm_checks[k][3]/NRM)
                        y_ptrm_check.append(zerofields[index_zerofield][3]/NRM)
                        ptrm_checks_temperatures.append(ptrm_checks[k][0])
                    except:
                        pass
                    
##                # microwave
##                if "LT-PMRM-I" in rec['magic_method_codes'] and float(rec['treatment_mw_power'])==ptrm_checks[k][0]:
##                    starting_temperature=(float(datablock[i-1]['treatment_mw_power']))
##                    
##                    try:
##                        index=t_Arai.index(starting_temperature)
##                        x_ptrm_check_starting_point.append(x_Arai[index])
##                        y_ptrm_check_starting_point.append(y_Arai[index])
##                        ptrm_checks_starting_temperatures.append(starting_temperature)
##
##                        index_zerofield=zerofield_temperatures.index(ptrm_checks[k][0])
##                        x_ptrm_check.append(ptrm_checks[k][3]/NRM)
##                        y_ptrm_check.append(zerofields[index_zerofield][3]/NRM)
##                        ptrm_checks_temperatures.append(ptrm_checks[k][0])
##                    except:
##                        pass

                    
        x_ptrm_check=array(x_ptrm_check)  
        ptrm_check=array(y_ptrm_check)
        ptrm_checks_temperatures=array(ptrm_checks_temperatures)
        Data[s]['PTRM_Checks']=ptrm_checks
        Data[s]['x_ptrm_check']=x_ptrm_check
        Data[s]['y_ptrm_check']=y_ptrm_check        
        Data[s]['ptrm_checks_temperatures']=ptrm_checks_temperatures
        Data[s]['x_ptrm_check_starting_point']=array(x_ptrm_check_starting_point)
        Data[s]['y_ptrm_check_starting_point']=array(y_ptrm_check_starting_point)               
        Data[s]['ptrm_checks_starting_temperatures']=array(ptrm_checks_starting_temperatures)
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


        x_tail_check=array(x_tail_check)  
        y_tail_check=array(y_tail_check)
        tail_check_temperatures=array(tail_check_temperatures)
        x_tail_check_starting_point=array(x_tail_check_starting_point)
        y_tail_check_starting_point=array(y_tail_check_starting_point)
        tail_checks_starting_temperatures=array(tail_checks_starting_temperatures)

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

                    except:
                        pass


                

        x_AC=array(x_AC)  
        y_AC=array(y_AC)
        AC_temperatures=array(AC_temperatures)
        x_AC_starting_point=array(x_AC_starting_point)
        y_AC_starting_point=array(y_AC_starting_point)
        AC_starting_temperatures=array(AC_starting_temperatures)
        AC=array(AC)

        Data[s]['AC']=AC
        #print s
        #print AC
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
##        x_tail_check=array(x_tail_check)  
##        y_tail_check=array(y_tail_check)
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

        # samples
        def read_magic_file(path,sort_by_this_name):
            DATA={}
            fin=open(path,'rU')
            fin.readline()
            line=fin.readline()
            header=line.strip('\n').split('\t')
            for line in fin.readlines():
                tmp_data={}
                tmp_line=line.strip('\n').split('\t')
                for i in range(len(tmp_line)):
                    tmp_data[header[i]]=tmp_line[i]
                DATA[tmp_data[sort_by_this_name]]=tmp_data
            fin.close()        
            return(DATA)
        try:
            data_er_samples=read_magic_file(self.WD+"/er_samples.txt",'er_sample_name')
        except:
            self.GUI_log.write ("-W- Cant find er_sample.txt in project directory\n")

        try:
            data_er_sites=read_magic_file(self.WD+"/er_sites.txt",'er_site_name')
        except:
            self.GUI_log.write ("-W- Cant find er_sites.txt in project directory\n")

        try:
            data_er_ages=read_magic_file(self.WD+"/er_ages.txt",'er_sample_name')
        except:
            try:
                data_er_ages=read_magic_file(self.WD+"/er_ages.txt",'er_site_name')
            except:    
                self.GUI_log.write ("-W- Cant find er_ages in project directory\n")


        Data_info["er_samples"]=data_er_samples
        Data_info["er_sites"]=data_er_sites
        Data_info["er_ages"]=data_er_ages
        
        
        return(Data_info)


    def get_site_from_hierarchy(self,sample):
        site=""
        sites=self.Data_hierarchy['sites'].keys()
        for S in sites:
            if sample in self.Data_hierarchy['sites'][S]:
                site=S
                break
        return(site)
    
    
    #--------------------------------------------------------------    
    # Read previose interpretation from pmag_specimens.txt (if exist)
    #--------------------------------------------------------------
    
    def get_previous_interpretation(self):
        prev_pmag_specimen=[]
        try:
            prev_pmag_specimen,file_type=pmag.magic_read(self.WD+"/pmag_specimens.txt")
            self.GUI_log.write ("-I- Read pmag_specimens.txt for previous interpretation")
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
                        self.Data[specimen]['pars']=self.get_PI_parameters(specimen,float(tmin_kelvin),float(tmax_kelvin))
                        self.Data[specimen]['pars']['saved']=True
                        # write intrepretation into sample data
                        sample=self.Data_hierarchy['specimens'][specimen]
                        if sample not in self.Data_samples.keys():
                            self.Data_samples[sample]={}
                        self.Data_samples[sample][specimen]=self.Data[specimen]['pars']['specimen_int_uT']
                        
                        site=self.get_site_from_hierarchy(sample)
                        if site not in self.Data_sites.keys():
                            self.Data_sites[site]={}
                        self.Data_sites[site][specimen]=self.Data[specimen]['pars']['specimen_int_uT']

                    except:
                        self.GUI_log.write ("-E- ERROR. Cant calculate PI paremeters for specimen %s using redo file. Check!"%(specimen))
            else:
                self.GUI_log.write ("-W- WARNING: Cant find specimen %s from redo file in measurement file!\n"%specimen)

        #try:
        #    self.s
        #except:
        self.s=self.specimens[0]                
        self.pars=self.Data[self.s]['pars']
        self.clear_boxes()
        self.draw_figure(self.s)
        self.update_GUI_with_new_interpretation()
                    


#===========================================================
#  definitions inherited from pmag.py
#===========================================================
       
                
    def cart2dir(self,cart):
        """
        converts a direction to cartesian coordinates
        """
        cart=array(cart)
        rad=pi/180. # constant to convert degrees to radians
        if len(cart.shape)>1:
            Xs,Ys,Zs=cart[:,0],cart[:,1],cart[:,2]
        else: #single vector
            Xs,Ys,Zs=cart[0],cart[1],cart[2]
        Rs=sqrt(Xs**2+Ys**2+Zs**2) # calculate resultant vector length
        Decs=(arctan2(Ys,Xs)/rad)%360. # calculate declination taking care of correct quadrants (arctan2) and making modulo 360.
        try:
            Incs=arcsin(Zs/Rs)/rad # calculate inclination (converting to degrees) # 
        except:
            print 'trouble in cart2dir' # most likely division by zero somewhere
            return zeros(3)
            
        return array([Decs,Incs,Rs]).transpose() # return the directions list


    def dir2cart(self,d):
       # converts list or array of vector directions, in degrees, to array of cartesian coordinates, in x,y,z
        ints=ones(len(d)).transpose() # get an array of ones to plug into dec,inc pairs
        d=array(d)
        rad=pi/180.
        if len(d.shape)>1: # array of vectors
            decs,incs=d[:,0]*rad,d[:,1]*rad
            if d.shape[1]==3: ints=d[:,2] # take the given lengths
        else: # single vector
            decs,incs=array(d[0])*rad,array(d[1])*rad
            if len(d)==3: 
                ints=array(d[2])
            else:
                ints=array([1.])
        cart= array([ints*cos(decs)*cos(incs),ints*sin(decs)*cos(incs),ints*sin(incs)]).transpose()
        return cart


    def b_vdm(self,B,lat):
        """ 
        Converts field values in tesla to v(a)dm in Am^2
        """
        rad=pi/180.
        fact=((6.371e6)**3)*1e7 # changed radius of the earth from 3.367e6 3/12/2010
        colat=(90.-lat) * rad
        return fact*B/(sqrt(1+3*(cos(colat)**2)))

    def dohext(self,nf,sigma,s):
        """
        calculates hext parameters for nf, sigma and s
        """
    #
        if nf==-1:return hextpars 
        f=sqrt(2.*self.fcalc(2,nf))
        t2sum=0
        tau,Vdir=self.doseigs(s)
        for i in range(3): t2sum+=tau[i]**2
        chibar=(s[0]+s[1]+s[2])/3.
        hpars={}
        hpars['F_crit']='%s'%(self.fcalc(5,nf))
        hpars['F12_crit']='%s'%(self.fcalc(2,nf))
        hpars["F"]=0.4*(t2sum-3*chibar**2)/(sigma**2)
        hpars["F12"]=0.5*((tau[0]-tau[1])/sigma)**2
        hpars["F23"]=0.5*((tau[1]-tau[2])/sigma)**2
        hpars["v1_dec"]=Vdir[0][0]
        hpars["v1_inc"]=Vdir[0][1]
        hpars["v2_dec"]=Vdir[1][0]
        hpars["v2_inc"]=Vdir[1][1]
        hpars["v3_dec"]=Vdir[2][0]
        hpars["v3_inc"]=Vdir[2][1]
        hpars["t1"]=tau[0]
        hpars["t2"]=tau[1]
        hpars["t3"]=tau[2]
        hpars["e12"]=arctan((f*sigma)/(2*abs(tau[0]-tau[1])))*180./pi
        hpars["e23"]=arctan((f*sigma)/(2*abs(tau[1]-tau[2])))*180./pi
        hpars["e13"]=arctan((f*sigma)/(2*abs(tau[0]-tau[2])))*180./pi
        return hpars

    def doseigs(self,s):
        """
        convert s format for eigenvalues and eigenvectors
        """
    #
        A=self.s2a(s) # convert s to a (see Tauxe 1998)
        tau,V=self.tauV(A) # convert to eigenvalues (t), eigenvectors (V)
        Vdirs=[]
        for v in V: # convert from cartesian to direction
            Vdir= self.cart2dir(v)
            if Vdir[1]<0:
                Vdir[1]=-Vdir[1]
                Vdir[0]=(Vdir[0]+180.)%360.
            Vdirs.append([Vdir[0],Vdir[1]])
        return tau,Vdirs


    def tauV(self,T):
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


    def s2a(self,s):
        """
         convert 6 element "s" list to 3,3 a matrix (see Tauxe 1998)
        """
        a=zeros((3,3,),'f') # make the a matrix
        for i in range(3):
            a[i][i]=s[i]
        a[0][1],a[1][0]=s[3],s[3]
        a[1][2],a[2][1]=s[4],s[4]
        a[0][2],a[2][0]=s[5],s[5]
        return a

    
    def fcalc(self,col,row):
        """
      looks up f from ftables F(row,col), where row is number of degrees of freedom - this is 95% confidence (p=0.05)
        """
    #
        if row>200:row=200
        if col>20:col=20
        ftest=array([[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
    [1, 161.469, 199.493, 215.737, 224.5, 230.066, 234.001, 236.772, 238.949, 240.496, 241.838, 242.968, 243.88, 244.798, 245.26, 245.956, 246.422, 246.89, 247.36, 247.596, 248.068],
    [2, 18.5128, 18.9995, 19.1642, 19.2467, 19.2969, 19.3299, 19.3536, 19.371, 19.3852, 19.3963, 19.4043, 19.4122, 19.4186, 19.425, 19.4297, 19.4329, 19.4377, 19.4409, 19.4425, 19.4457],
    [3, 10.1278, 9.5522, 9.2767, 9.1173, 9.0133, 8.9408, 8.8868, 8.8452, 8.8124, 8.7857, 8.7635, 8.7446, 8.7287, 8.715, 8.7028, 8.6923, 8.683, 8.6745, 8.667, 8.6602],
    [4, 7.7087, 6.9444, 6.5915, 6.3882, 6.2561, 6.1631, 6.0943, 6.0411, 5.9988, 5.9644, 5.9359, 5.9117, 5.8912, 5.8733, 5.8578, 5.844, 5.8319, 5.8211, 5.8113, 5.8025],
    [5, 6.608, 5.7861, 5.4095, 5.1922, 5.0503, 4.9503, 4.8759, 4.8184, 4.7725, 4.735, 4.7039, 4.6777, 4.6552, 4.6358, 4.6187, 4.6038, 4.5904, 4.5785, 4.5679, 4.5581],
    [6, 5.9874, 5.1433, 4.757, 4.5337, 4.3874, 4.2838, 4.2067, 4.1468, 4.099, 4.06, 4.0275, 3.9999, 3.9764, 3.956, 3.9381, 3.9223, 3.9083, 3.8957, 3.8844, 3.8742],
    [7, 5.5914, 4.7374, 4.3469, 4.1204, 3.9715, 3.866, 3.787, 3.7257, 3.6767, 3.6366, 3.603, 3.5747, 3.5504, 3.5292, 3.5107, 3.4944, 3.4799, 3.4669, 3.4552, 3.4445],
    [8, 5.3177, 4.459, 4.0662, 3.8378, 3.6875, 3.5806, 3.5004, 3.4381, 3.3881, 3.3472, 3.313, 3.2839, 3.259, 3.2374, 3.2184, 3.2017, 3.1867, 3.1733, 3.1613, 3.1503],
    [9, 5.1174, 4.2565, 3.8626, 3.6331, 3.4817, 3.3738, 3.2928, 3.2296, 3.1789, 3.1373, 3.1025, 3.0729, 3.0475, 3.0255, 3.0061, 2.989, 2.9737, 2.96, 2.9476, 2.9365],
    [10, 4.9647, 4.1028, 3.7083, 3.4781, 3.3258, 3.2171, 3.1355, 3.0717, 3.0204, 2.9782, 2.9429, 2.913, 2.8872, 2.8648, 2.845, 2.8276, 2.812, 2.7981, 2.7855, 2.774],
    [11, 4.8443, 3.9823, 3.5875, 3.3567, 3.2039, 3.0946, 3.0123, 2.948, 2.8962, 2.8536, 2.8179, 2.7876, 2.7614, 2.7386, 2.7186, 2.7009, 2.6851, 2.6709, 2.6581, 2.6464],
    [12, 4.7472, 3.8853, 3.4903, 3.2592, 3.1059, 2.9961, 2.9134, 2.8486, 2.7964, 2.7534, 2.7173, 2.6866, 2.6602, 2.6371, 2.6169, 2.5989, 2.5828, 2.5684, 2.5554, 2.5436],
    [13, 4.6672, 3.8055, 3.4106, 3.1791, 3.0255, 2.9153, 2.8321, 2.7669, 2.7144, 2.6711, 2.6347, 2.6037, 2.5769, 2.5536, 2.5331, 2.5149, 2.4987, 2.4841, 2.4709, 2.4589],
    [14, 4.6001, 3.7389, 3.3439, 3.1122, 2.9582, 2.8477, 2.7642, 2.6987, 2.6458, 2.6021, 2.5655, 2.5343, 2.5073, 2.4837, 2.463, 2.4446, 2.4282, 2.4134, 2.4, 2.3879],
    [15, 4.543, 3.6824, 3.2874, 3.0555, 2.9013, 2.7905, 2.7066, 2.6408, 2.5877, 2.5437, 2.5068, 2.4753, 2.4481, 2.4244, 2.4034, 2.3849, 2.3683, 2.3533, 2.3398, 2.3275],
    [16, 4.494, 3.6337, 3.2389, 3.0069, 2.8524, 2.7413, 2.6572, 2.5911, 2.5377, 2.4935, 2.4564, 2.4247, 2.3973, 2.3733, 2.3522, 2.3335, 2.3167, 2.3016, 2.288, 2.2756],
    [17, 4.4513, 3.5916, 3.1968, 2.9647, 2.81, 2.6987, 2.6143, 2.548, 2.4943, 2.4499, 2.4126, 2.3807, 2.3531, 2.329, 2.3077, 2.2888, 2.2719, 2.2567, 2.2429, 2.2303],
    [18, 4.4139, 3.5546, 3.1599, 2.9278, 2.7729, 2.6613, 2.5767, 2.5102, 2.4563, 2.4117, 2.3742, 2.3421, 2.3143, 2.29, 2.2686, 2.2496, 2.2325, 2.2172, 2.2033, 2.1906],
    [19, 4.3808, 3.5219, 3.1274, 2.8951, 2.7401, 2.6283, 2.5435, 2.4768, 2.4227, 2.378, 2.3402, 2.308, 2.28, 2.2556, 2.2341, 2.2149, 2.1977, 2.1823, 2.1683, 2.1555],
    [20, 4.3512, 3.4928, 3.0984, 2.8661, 2.7109, 2.599, 2.514, 2.4471, 2.3928, 2.3479, 2.31, 2.2776, 2.2495, 2.2249, 2.2033, 2.184, 2.1667, 2.1511, 2.137, 2.1242],
    [21, 4.3248, 3.4668, 3.0725, 2.8401, 2.6848, 2.5727, 2.4876, 2.4205, 2.3661, 2.3209, 2.2829, 2.2504, 2.2222, 2.1975, 2.1757, 2.1563, 2.1389, 2.1232, 2.109, 2.096],
    [22, 4.3009, 3.4434, 3.0492, 2.8167, 2.6613, 2.5491, 2.4638, 2.3965, 2.3419, 2.2967, 2.2585, 2.2258, 2.1975, 2.1727, 2.1508, 2.1313, 2.1138, 2.098, 2.0837, 2.0707],
    [23, 4.2794, 3.4221, 3.028, 2.7955, 2.64, 2.5276, 2.4422, 2.3748, 2.3201, 2.2747, 2.2364, 2.2036, 2.1752, 2.1503, 2.1282, 2.1086, 2.091, 2.0751, 2.0608, 2.0476],
    [24, 4.2597, 3.4029, 3.0088, 2.7763, 2.6206, 2.5082, 2.4226, 2.3551, 2.3003, 2.2547, 2.2163, 2.1834, 2.1548, 2.1298, 2.1077, 2.088, 2.0703, 2.0543, 2.0399, 2.0267],
    [25, 4.2417, 3.3852, 2.9913, 2.7587, 2.603, 2.4904, 2.4047, 2.3371, 2.2821, 2.2365, 2.1979, 2.1649, 2.1362, 2.1111, 2.0889, 2.0691, 2.0513, 2.0353, 2.0207, 2.0075],
    [26, 4.2252, 3.369, 2.9752, 2.7426, 2.5868, 2.4741, 2.3883, 2.3205, 2.2655, 2.2197, 2.1811, 2.1479, 2.1192, 2.094, 2.0716, 2.0518, 2.0339, 2.0178, 2.0032, 1.9898],
    [27, 4.21, 3.3542, 2.9603, 2.7277, 2.5719, 2.4591, 2.3732, 2.3053, 2.2501, 2.2043, 2.1656, 2.1323, 2.1035, 2.0782, 2.0558, 2.0358, 2.0179, 2.0017, 1.987, 1.9736],
    [28, 4.196, 3.3404, 2.9467, 2.7141, 2.5581, 2.4453, 2.3592, 2.2913, 2.236, 2.1901, 2.1512, 2.1179, 2.0889, 2.0636, 2.0411, 2.021, 2.0031, 1.9868, 1.972, 1.9586],
    [29, 4.1829, 3.3276, 2.9341, 2.7014, 2.5454, 2.4324, 2.3463, 2.2783, 2.2229, 2.1768, 2.1379, 2.1045, 2.0755, 2.05, 2.0275, 2.0074, 1.9893, 1.973, 1.9582, 1.9446],
    [30, 4.1709, 3.3158, 2.9223, 2.6896, 2.5335, 2.4205, 2.3343, 2.2662, 2.2107, 2.1646, 2.1255, 2.0921, 2.0629, 2.0374, 2.0148, 1.9946, 1.9765, 1.9601, 1.9452, 1.9317],
    [31, 4.1597, 3.3048, 2.9113, 2.6787, 2.5225, 2.4094, 2.3232, 2.2549, 2.1994, 2.1531, 2.1141, 2.0805, 2.0513, 2.0257, 2.003, 1.9828, 1.9646, 1.9481, 1.9332, 1.9196],
    [32, 4.1491, 3.2945, 2.9011, 2.6684, 2.5123, 2.3991, 2.3127, 2.2444, 2.1888, 2.1425, 2.1033, 2.0697, 2.0404, 2.0147, 1.992, 1.9717, 1.9534, 1.9369, 1.9219, 1.9083],
    [33, 4.1392, 3.2849, 2.8915, 2.6589, 2.5027, 2.3894, 2.303, 2.2346, 2.1789, 2.1325, 2.0933, 2.0596, 2.0302, 2.0045, 1.9817, 1.9613, 1.943, 1.9264, 1.9114, 1.8977],
    [34, 4.13, 3.2759, 2.8826, 2.6499, 2.4936, 2.3803, 2.2938, 2.2253, 2.1696, 2.1231, 2.0838, 2.05, 2.0207, 1.9949, 1.972, 1.9516, 1.9332, 1.9166, 1.9015, 1.8877],
    [35, 4.1214, 3.2674, 2.8742, 2.6415, 2.4851, 2.3718, 2.2852, 2.2167, 2.1608, 2.1143, 2.0749, 2.0411, 2.0117, 1.9858, 1.9629, 1.9424, 1.924, 1.9073, 1.8922, 1.8784],
    [36, 4.1132, 3.2594, 2.8663, 2.6335, 2.4771, 2.3637, 2.2771, 2.2085, 2.1526, 2.1061, 2.0666, 2.0327, 2.0032, 1.9773, 1.9543, 1.9338, 1.9153, 1.8986, 1.8834, 1.8696],
    [37, 4.1055, 3.2519, 2.8588, 2.6261, 2.4696, 2.3562, 2.2695, 2.2008, 2.1449, 2.0982, 2.0587, 2.0248, 1.9952, 1.9692, 1.9462, 1.9256, 1.9071, 1.8904, 1.8752, 1.8613],
    [38, 4.0981, 3.2448, 2.8517, 2.619, 2.4625, 2.349, 2.2623, 2.1935, 2.1375, 2.0909, 2.0513, 2.0173, 1.9877, 1.9617, 1.9386, 1.9179, 1.8994, 1.8826, 1.8673, 1.8534],
    [39, 4.0913, 3.2381, 2.8451, 2.6123, 2.4558, 2.3422, 2.2555, 2.1867, 2.1306, 2.0839, 2.0442, 2.0102, 1.9805, 1.9545, 1.9313, 1.9107, 1.8921, 1.8752, 1.8599, 1.8459],
    [40, 4.0848, 3.2317, 2.8388, 2.606, 2.4495, 2.3359, 2.249, 2.1802, 2.124, 2.0773, 2.0376, 2.0035, 1.9738, 1.9476, 1.9245, 1.9038, 1.8851, 1.8682, 1.8529, 1.8389],
    [41, 4.0786, 3.2257, 2.8328, 2.6, 2.4434, 2.3298, 2.2429, 2.174, 2.1178, 2.071, 2.0312, 1.9971, 1.9673, 1.9412, 1.9179, 1.8972, 1.8785, 1.8616, 1.8462, 1.8321],
    [42, 4.0727, 3.2199, 2.8271, 2.5943, 2.4377, 2.324, 2.2371, 2.1681, 2.1119, 2.065, 2.0252, 1.991, 1.9612, 1.935, 1.9118, 1.8909, 1.8722, 1.8553, 1.8399, 1.8258],
    [43, 4.067, 3.2145, 2.8216, 2.5888, 2.4322, 2.3185, 2.2315, 2.1625, 2.1062, 2.0593, 2.0195, 1.9852, 1.9554, 1.9292, 1.9059, 1.885, 1.8663, 1.8493, 1.8338, 1.8197],
    [44, 4.0617, 3.2093, 2.8165, 2.5837, 2.4271, 2.3133, 2.2262, 2.1572, 2.1009, 2.0539, 2.014, 1.9797, 1.9499, 1.9236, 1.9002, 1.8794, 1.8606, 1.8436, 1.8281, 1.8139],
    [45, 4.0566, 3.2043, 2.8115, 2.5787, 2.4221, 2.3083, 2.2212, 2.1521, 2.0958, 2.0487, 2.0088, 1.9745, 1.9446, 1.9182, 1.8949, 1.874, 1.8551, 1.8381, 1.8226, 1.8084],
    [46, 4.0518, 3.1996, 2.8068, 2.574, 2.4174, 2.3035, 2.2164, 2.1473, 2.0909, 2.0438, 2.0039, 1.9695, 1.9395, 1.9132, 1.8898, 1.8688, 1.85, 1.8329, 1.8173, 1.8031],
    [47, 4.0471, 3.1951, 2.8024, 2.5695, 2.4128, 2.299, 2.2118, 2.1427, 2.0862, 2.0391, 1.9991, 1.9647, 1.9347, 1.9083, 1.8849, 1.8639, 1.845, 1.8279, 1.8123, 1.798],
    [48, 4.0426, 3.1907, 2.7981, 2.5653, 2.4085, 2.2946, 2.2074, 2.1382, 2.0817, 2.0346, 1.9946, 1.9601, 1.9301, 1.9037, 1.8802, 1.8592, 1.8402, 1.8231, 1.8075, 1.7932],
    [49, 4.0384, 3.1866, 2.7939, 2.5611, 2.4044, 2.2904, 2.2032, 2.134, 2.0774, 2.0303, 1.9902, 1.9558, 1.9257, 1.8992, 1.8757, 1.8547, 1.8357, 1.8185, 1.8029, 1.7886],
    [50, 4.0343, 3.1826, 2.79, 2.5572, 2.4004, 2.2864, 2.1992, 2.1299, 2.0734, 2.0261, 1.9861, 1.9515, 1.9214, 1.8949, 1.8714, 1.8503, 1.8313, 1.8141, 1.7985, 1.7841],
    [51, 4.0303, 3.1788, 2.7862, 2.5534, 2.3966, 2.2826, 2.1953, 2.126, 2.0694, 2.0222, 1.982, 1.9475, 1.9174, 1.8908, 1.8673, 1.8462, 1.8272, 1.8099, 1.7942, 1.7798],
    [52, 4.0266, 3.1752, 2.7826, 2.5498, 2.3929, 2.2789, 2.1916, 2.1223, 2.0656, 2.0184, 1.9782, 1.9436, 1.9134, 1.8869, 1.8633, 1.8422, 1.8231, 1.8059, 1.7901, 1.7758],
    [53, 4.023, 3.1716, 2.7791, 2.5463, 2.3894, 2.2754, 2.1881, 2.1187, 2.062, 2.0147, 1.9745, 1.9399, 1.9097, 1.8831, 1.8595, 1.8383, 1.8193, 1.802, 1.7862, 1.7718],
    [54, 4.0196, 3.1683, 2.7757, 2.5429, 2.3861, 2.272, 2.1846, 2.1152, 2.0585, 2.0112, 1.971, 1.9363, 1.9061, 1.8795, 1.8558, 1.8346, 1.8155, 1.7982, 1.7825, 1.768],
    [55, 4.0162, 3.165, 2.7725, 2.5397, 2.3828, 2.2687, 2.1813, 2.1119, 2.0552, 2.0078, 1.9676, 1.9329, 1.9026, 1.876, 1.8523, 1.8311, 1.812, 1.7946, 1.7788, 1.7644],
    [56, 4.0129, 3.1618, 2.7694, 2.5366, 2.3797, 2.2656, 2.1781, 2.1087, 2.0519, 2.0045, 1.9642, 1.9296, 1.8993, 1.8726, 1.8489, 1.8276, 1.8085, 1.7912, 1.7753, 1.7608],
    [57, 4.0099, 3.1589, 2.7665, 2.5336, 2.3767, 2.2625, 2.1751, 2.1056, 2.0488, 2.0014, 1.9611, 1.9264, 1.896, 1.8693, 1.8456, 1.8244, 1.8052, 1.7878, 1.772, 1.7575],
    [58, 4.0069, 3.1559, 2.7635, 2.5307, 2.3738, 2.2596, 2.1721, 2.1026, 2.0458, 1.9983, 1.958, 1.9233, 1.8929, 1.8662, 1.8424, 1.8212, 1.802, 1.7846, 1.7687, 1.7542],
    [59, 4.0039, 3.1531, 2.7608, 2.5279, 2.371, 2.2568, 2.1693, 2.0997, 2.0429, 1.9954, 1.9551, 1.9203, 1.8899, 1.8632, 1.8394, 1.8181, 1.7989, 1.7815, 1.7656, 1.751],
    [60, 4.0012, 3.1504, 2.7581, 2.5252, 2.3683, 2.254, 2.1665, 2.097, 2.0401, 1.9926, 1.9522, 1.9174, 1.887, 1.8603, 1.8364, 1.8151, 1.7959, 1.7784, 1.7625, 1.748],
    [61, 3.9985, 3.1478, 2.7555, 2.5226, 2.3657, 2.2514, 2.1639, 2.0943, 2.0374, 1.9899, 1.9495, 1.9146, 1.8842, 1.8574, 1.8336, 1.8122, 1.793, 1.7755, 1.7596, 1.745],
    [62, 3.9959, 3.1453, 2.753, 2.5201, 2.3631, 2.2489, 2.1613, 2.0917, 2.0348, 1.9872, 1.9468, 1.9119, 1.8815, 1.8547, 1.8308, 1.8095, 1.7902, 1.7727, 1.7568, 1.7422],
    [63, 3.9934, 3.1428, 2.7506, 2.5176, 2.3607, 2.2464, 2.1588, 2.0892, 2.0322, 1.9847, 1.9442, 1.9093, 1.8789, 1.852, 1.8282, 1.8068, 1.7875, 1.77, 1.754, 1.7394],
    [64, 3.9909, 3.1404, 2.7482, 2.5153, 2.3583, 2.244, 2.1564, 2.0868, 2.0298, 1.9822, 1.9417, 1.9068, 1.8763, 1.8495, 1.8256, 1.8042, 1.7849, 1.7673, 1.7514, 1.7368],
    [65, 3.9885, 3.1381, 2.7459, 2.513, 2.356, 2.2417, 2.1541, 2.0844, 2.0274, 1.9798, 1.9393, 1.9044, 1.8739, 1.847, 1.8231, 1.8017, 1.7823, 1.7648, 1.7488, 1.7342],
    [66, 3.9862, 3.1359, 2.7437, 2.5108, 2.3538, 2.2395, 2.1518, 2.0821, 2.0251, 1.9775, 1.937, 1.902, 1.8715, 1.8446, 1.8207, 1.7992, 1.7799, 1.7623, 1.7463, 1.7316],
    [67, 3.9841, 3.1338, 2.7416, 2.5087, 2.3516, 2.2373, 2.1497, 2.0799, 2.0229, 1.9752, 1.9347, 1.8997, 1.8692, 1.8423, 1.8183, 1.7968, 1.7775, 1.7599, 1.7439, 1.7292],
    [68, 3.9819, 3.1317, 2.7395, 2.5066, 2.3496, 2.2352, 2.1475, 2.0778, 2.0207, 1.973, 1.9325, 1.8975, 1.867, 1.84, 1.816, 1.7945, 1.7752, 1.7576, 1.7415, 1.7268],
    [69, 3.9798, 3.1297, 2.7375, 2.5046, 2.3475, 2.2332, 2.1455, 2.0757, 2.0186, 1.9709, 1.9303, 1.8954, 1.8648, 1.8378, 1.8138, 1.7923, 1.7729, 1.7553, 1.7393, 1.7246],
    [70, 3.9778, 3.1277, 2.7355, 2.5027, 2.3456, 2.2312, 2.1435, 2.0737, 2.0166, 1.9689, 1.9283, 1.8932, 1.8627, 1.8357, 1.8117, 1.7902, 1.7707, 1.7531, 1.7371, 1.7223],
    [71, 3.9758, 3.1258, 2.7336, 2.5007, 2.3437, 2.2293, 2.1415, 2.0717, 2.0146, 1.9669, 1.9263, 1.8912, 1.8606, 1.8336, 1.8096, 1.7881, 1.7686, 1.751, 1.7349, 1.7202],
    [72, 3.9739, 3.1239, 2.7318, 2.4989, 2.3418, 2.2274, 2.1397, 2.0698, 2.0127, 1.9649, 1.9243, 1.8892, 1.8586, 1.8316, 1.8076, 1.786, 1.7666, 1.7489, 1.7328, 1.7181],
    [73, 3.9721, 3.1221, 2.73, 2.4971, 2.34, 2.2256, 2.1378, 2.068, 2.0108, 1.9631, 1.9224, 1.8873, 1.8567, 1.8297, 1.8056, 1.784, 1.7646, 1.7469, 1.7308, 1.716],
    [74, 3.9703, 3.1204, 2.7283, 2.4954, 2.3383, 2.2238, 2.1361, 2.0662, 2.009, 1.9612, 1.9205, 1.8854, 1.8548, 1.8278, 1.8037, 1.7821, 1.7626, 1.7449, 1.7288, 1.714],
    [75, 3.9685, 3.1186, 2.7266, 2.4937, 2.3366, 2.2221, 2.1343, 2.0645, 2.0073, 1.9595, 1.9188, 1.8836, 1.853, 1.8259, 1.8018, 1.7802, 1.7607, 1.7431, 1.7269, 1.7121],
    [76, 3.9668, 3.117, 2.7249, 2.4921, 2.3349, 2.2204, 2.1326, 2.0627, 2.0055, 1.9577, 1.917, 1.8819, 1.8512, 1.8241, 1.8, 1.7784, 1.7589, 1.7412, 1.725, 1.7102],
    [77, 3.9651, 3.1154, 2.7233, 2.4904, 2.3333, 2.2188, 2.131, 2.0611, 2.0039, 1.956, 1.9153, 1.8801, 1.8494, 1.8223, 1.7982, 1.7766, 1.7571, 1.7394, 1.7232, 1.7084],
    [78, 3.9635, 3.1138, 2.7218, 2.4889, 2.3318, 2.2172, 2.1294, 2.0595, 2.0022, 1.9544, 1.9136, 1.8785, 1.8478, 1.8206, 1.7965, 1.7749, 1.7554, 1.7376, 1.7214, 1.7066],
    [79, 3.9619, 3.1123, 2.7203, 2.4874, 2.3302, 2.2157, 2.1279, 2.0579, 2.0006, 1.9528, 1.912, 1.8769, 1.8461, 1.819, 1.7948, 1.7732, 1.7537, 1.7359, 1.7197, 1.7048],
    [80, 3.9604, 3.1107, 2.7188, 2.4859, 2.3287, 2.2142, 2.1263, 2.0564, 1.9991, 1.9512, 1.9105, 1.8753, 1.8445, 1.8174, 1.7932, 1.7716, 1.752, 1.7342, 1.718, 1.7032],
    [81, 3.9589, 3.1093, 2.7173, 2.4845, 2.3273, 2.2127, 2.1248, 2.0549, 1.9976, 1.9497, 1.9089, 1.8737, 1.8429, 1.8158, 1.7916, 1.77, 1.7504, 1.7326, 1.7164, 1.7015],
    [82, 3.9574, 3.1079, 2.716, 2.483, 2.3258, 2.2113, 2.1234, 2.0534, 1.9962, 1.9482, 1.9074, 1.8722, 1.8414, 1.8143, 1.7901, 1.7684, 1.7488, 1.731, 1.7148, 1.6999],
    [83, 3.956, 3.1065, 2.7146, 2.4817, 2.3245, 2.2099, 2.122, 2.052, 1.9947, 1.9468, 1.906, 1.8707, 1.8399, 1.8127, 1.7886, 1.7669, 1.7473, 1.7295, 1.7132, 1.6983],
    [84, 3.9546, 3.1051, 2.7132, 2.4803, 2.3231, 2.2086, 2.1206, 2.0506, 1.9933, 1.9454, 1.9045, 1.8693, 1.8385, 1.8113, 1.7871, 1.7654, 1.7458, 1.728, 1.7117, 1.6968],
    [85, 3.9532, 3.1039, 2.7119, 2.479, 2.3218, 2.2072, 2.1193, 2.0493, 1.9919, 1.944, 1.9031, 1.8679, 1.8371, 1.8099, 1.7856, 1.7639, 1.7443, 1.7265, 1.7102, 1.6953],
    [86, 3.9519, 3.1026, 2.7106, 2.4777, 2.3205, 2.2059, 2.118, 2.048, 1.9906, 1.9426, 1.9018, 1.8665, 1.8357, 1.8085, 1.7842, 1.7625, 1.7429, 1.725, 1.7088, 1.6938],
    [87, 3.9506, 3.1013, 2.7094, 2.4765, 2.3193, 2.2047, 2.1167, 2.0467, 1.9893, 1.9413, 1.9005, 1.8652, 1.8343, 1.8071, 1.7829, 1.7611, 1.7415, 1.7236, 1.7073, 1.6924],
    [88, 3.9493, 3.1001, 2.7082, 2.4753, 2.318, 2.2034, 2.1155, 2.0454, 1.9881, 1.94, 1.8992, 1.8639, 1.833, 1.8058, 1.7815, 1.7598, 1.7401, 1.7223, 1.706, 1.691],
    [89, 3.9481, 3.0988, 2.707, 2.4741, 2.3169, 2.2022, 2.1143, 2.0442, 1.9868, 1.9388, 1.8979, 1.8626, 1.8317, 1.8045, 1.7802, 1.7584, 1.7388, 1.7209, 1.7046, 1.6896],
    [90, 3.9469, 3.0977, 2.7058, 2.4729, 2.3157, 2.2011, 2.1131, 2.043, 1.9856, 1.9376, 1.8967, 1.8613, 1.8305, 1.8032, 1.7789, 1.7571, 1.7375, 1.7196, 1.7033, 1.6883],
    [91, 3.9457, 3.0965, 2.7047, 2.4718, 2.3146, 2.1999, 2.1119, 2.0418, 1.9844, 1.9364, 1.8955, 1.8601, 1.8292, 1.802, 1.7777, 1.7559, 1.7362, 1.7183, 1.702, 1.687],
    [92, 3.9446, 3.0955, 2.7036, 2.4707, 2.3134, 2.1988, 2.1108, 2.0407, 1.9833, 1.9352, 1.8943, 1.8589, 1.828, 1.8008, 1.7764, 1.7546, 1.735, 1.717, 1.7007, 1.6857],
    [93, 3.9435, 3.0944, 2.7025, 2.4696, 2.3123, 2.1977, 2.1097, 2.0395, 1.9821, 1.934, 1.8931, 1.8578, 1.8269, 1.7996, 1.7753, 1.7534, 1.7337, 1.7158, 1.6995, 1.6845],
    [94, 3.9423, 3.0933, 2.7014, 2.4685, 2.3113, 2.1966, 2.1086, 2.0385, 1.981, 1.9329, 1.892, 1.8566, 1.8257, 1.7984, 1.7741, 1.7522, 1.7325, 1.7146, 1.6982, 1.6832],
    [95, 3.9412, 3.0922, 2.7004, 2.4675, 2.3102, 2.1955, 2.1075, 2.0374, 1.9799, 1.9318, 1.8909, 1.8555, 1.8246, 1.7973, 1.7729, 1.7511, 1.7314, 1.7134, 1.6971, 1.682],
    [96, 3.9402, 3.0912, 2.6994, 2.4665, 2.3092, 2.1945, 2.1065, 2.0363, 1.9789, 1.9308, 1.8898, 1.8544, 1.8235, 1.7961, 1.7718, 1.75, 1.7302, 1.7123, 1.6959, 1.6809],
    [97, 3.9392, 3.0902, 2.6984, 2.4655, 2.3082, 2.1935, 2.1054, 2.0353, 1.9778, 1.9297, 1.8888, 1.8533, 1.8224, 1.7951, 1.7707, 1.7488, 1.7291, 1.7112, 1.6948, 1.6797],
    [98, 3.9381, 3.0892, 2.6974, 2.4645, 2.3072, 2.1925, 2.1044, 2.0343, 1.9768, 1.9287, 1.8877, 1.8523, 1.8213, 1.794, 1.7696, 1.7478, 1.728, 1.71, 1.6936, 1.6786],
    [99, 3.9371, 3.0882, 2.6965, 2.4636, 2.3062, 2.1916, 2.1035, 2.0333, 1.9758, 1.9277, 1.8867, 1.8513, 1.8203, 1.7929, 1.7686, 1.7467, 1.7269, 1.709, 1.6926, 1.6775],
    [100, 3.9361, 3.0873, 2.6955, 2.4626, 2.3053, 2.1906, 2.1025, 2.0323, 1.9748, 1.9267, 1.8857, 1.8502, 1.8193, 1.7919, 1.7675, 1.7456, 1.7259, 1.7079, 1.6915, 1.6764],
    [101, 3.9352, 3.0864, 2.6946, 2.4617, 2.3044, 2.1897, 2.1016, 2.0314, 1.9739, 1.9257, 1.8847, 1.8493, 1.8183, 1.7909, 1.7665, 1.7446, 1.7248, 1.7069, 1.6904, 1.6754],
    [102, 3.9342, 3.0854, 2.6937, 2.4608, 2.3035, 2.1888, 2.1007, 2.0304, 1.9729, 1.9248, 1.8838, 1.8483, 1.8173, 1.7899, 1.7655, 1.7436, 1.7238, 1.7058, 1.6894, 1.6744],
    [103, 3.9333, 3.0846, 2.6928, 2.4599, 2.3026, 2.1879, 2.0997, 2.0295, 1.972, 1.9238, 1.8828, 1.8474, 1.8163, 1.789, 1.7645, 1.7427, 1.7229, 1.7048, 1.6884, 1.6733],
    [104, 3.9325, 3.0837, 2.692, 2.4591, 2.3017, 2.187, 2.0989, 2.0287, 1.9711, 1.9229, 1.8819, 1.8464, 1.8154, 1.788, 1.7636, 1.7417, 1.7219, 1.7039, 1.6874, 1.6723],
    [105, 3.9316, 3.0828, 2.6912, 2.4582, 2.3009, 2.1861, 2.098, 2.0278, 1.9702, 1.922, 1.881, 1.8455, 1.8145, 1.7871, 1.7627, 1.7407, 1.7209, 1.7029, 1.6865, 1.6714],
    [106, 3.9307, 3.082, 2.6903, 2.4574, 2.3, 2.1853, 2.0971, 2.0269, 1.9694, 1.9212, 1.8801, 1.8446, 1.8136, 1.7862, 1.7618, 1.7398, 1.72, 1.702, 1.6855, 1.6704],
    [107, 3.9299, 3.0812, 2.6895, 2.4566, 2.2992, 2.1845, 2.0963, 2.0261, 1.9685, 1.9203, 1.8792, 1.8438, 1.8127, 1.7853, 1.7608, 1.7389, 1.7191, 1.7011, 1.6846, 1.6695],
    [108, 3.929, 3.0804, 2.6887, 2.4558, 2.2984, 2.1837, 2.0955, 2.0252, 1.9677, 1.9195, 1.8784, 1.8429, 1.8118, 1.7844, 1.7599, 1.738, 1.7182, 1.7001, 1.6837, 1.6685],
    [109, 3.9282, 3.0796, 2.6879, 2.455, 2.2976, 2.1828, 2.0947, 2.0244, 1.9669, 1.9186, 1.8776, 1.8421, 1.811, 1.7835, 1.7591, 1.7371, 1.7173, 1.6992, 1.6828, 1.6676],
    [110, 3.9274, 3.0788, 2.6872, 2.4542, 2.2968, 2.1821, 2.0939, 2.0236, 1.9661, 1.9178, 1.8767, 1.8412, 1.8102, 1.7827, 1.7582, 1.7363, 1.7164, 1.6984, 1.6819, 1.6667],
    [111, 3.9266, 3.0781, 2.6864, 2.4535, 2.2961, 2.1813, 2.0931, 2.0229, 1.9653, 1.917, 1.8759, 1.8404, 1.8093, 1.7819, 1.7574, 1.7354, 1.7156, 1.6975, 1.681, 1.6659],
    [112, 3.9258, 3.0773, 2.6857, 2.4527, 2.2954, 2.1806, 2.0924, 2.0221, 1.9645, 1.9163, 1.8751, 1.8396, 1.8085, 1.7811, 1.7566, 1.7346, 1.7147, 1.6967, 1.6802, 1.665],
    [113, 3.9251, 3.0766, 2.6849, 2.452, 2.2946, 2.1798, 2.0916, 2.0213, 1.9637, 1.9155, 1.8744, 1.8388, 1.8077, 1.7803, 1.7558, 1.7338, 1.7139, 1.6958, 1.6793, 1.6642],
    [114, 3.9243, 3.0758, 2.6842, 2.4513, 2.2939, 2.1791, 2.0909, 2.0206, 1.963, 1.9147, 1.8736, 1.8381, 1.8069, 1.7795, 1.755, 1.733, 1.7131, 1.695, 1.6785, 1.6633],
    [115, 3.9236, 3.0751, 2.6835, 2.4506, 2.2932, 2.1784, 2.0902, 2.0199, 1.9623, 1.914, 1.8729, 1.8373, 1.8062, 1.7787, 1.7542, 1.7322, 1.7123, 1.6942, 1.6777, 1.6625],
    [116, 3.9228, 3.0744, 2.6828, 2.4499, 2.2925, 2.1777, 2.0895, 2.0192, 1.9615, 1.9132, 1.8721, 1.8365, 1.8054, 1.7779, 1.7534, 1.7314, 1.7115, 1.6934, 1.6769, 1.6617],
    [117, 3.9222, 3.0738, 2.6821, 2.4492, 2.2918, 2.177, 2.0888, 2.0185, 1.9608, 1.9125, 1.8714, 1.8358, 1.8047, 1.7772, 1.7527, 1.7307, 1.7108, 1.6927, 1.6761, 1.6609],
    [118, 3.9215, 3.0731, 2.6815, 2.4485, 2.2912, 2.1763, 2.0881, 2.0178, 1.9601, 1.9118, 1.8707, 1.8351, 1.804, 1.7765, 1.752, 1.7299, 1.71, 1.6919, 1.6754, 1.6602],
    [119, 3.9208, 3.0724, 2.6808, 2.4479, 2.2905, 2.1757, 2.0874, 2.0171, 1.9594, 1.9111, 1.87, 1.8344, 1.8032, 1.7757, 1.7512, 1.7292, 1.7093, 1.6912, 1.6746, 1.6594],
    [120, 3.9202, 3.0718, 2.6802, 2.4472, 2.2899, 2.175, 2.0868, 2.0164, 1.9588, 1.9105, 1.8693, 1.8337, 1.8026, 1.775, 1.7505, 1.7285, 1.7085, 1.6904, 1.6739, 1.6587],
    [121, 3.9194, 3.0712, 2.6795, 2.4466, 2.2892, 2.1744, 2.0861, 2.0158, 1.9581, 1.9098, 1.8686, 1.833, 1.8019, 1.7743, 1.7498, 1.7278, 1.7078, 1.6897, 1.6732, 1.6579],
    [122, 3.9188, 3.0705, 2.6789, 2.446, 2.2886, 2.1737, 2.0855, 2.0151, 1.9575, 1.9091, 1.868, 1.8324, 1.8012, 1.7736, 1.7491, 1.727, 1.7071, 1.689, 1.6724, 1.6572],
    [123, 3.9181, 3.0699, 2.6783, 2.4454, 2.288, 2.1731, 2.0849, 2.0145, 1.9568, 1.9085, 1.8673, 1.8317, 1.8005, 1.773, 1.7484, 1.7264, 1.7064, 1.6883, 1.6717, 1.6565],
    [124, 3.9176, 3.0693, 2.6777, 2.4448, 2.2874, 2.1725, 2.0842, 2.0139, 1.9562, 1.9078, 1.8667, 1.831, 1.7999, 1.7723, 1.7478, 1.7257, 1.7058, 1.6876, 1.6711, 1.6558],
    [125, 3.9169, 3.0687, 2.6771, 2.4442, 2.2868, 2.1719, 2.0836, 2.0133, 1.9556, 1.9072, 1.866, 1.8304, 1.7992, 1.7717, 1.7471, 1.725, 1.7051, 1.6869, 1.6704, 1.6551],
    [126, 3.9163, 3.0681, 2.6765, 2.4436, 2.2862, 2.1713, 2.083, 2.0126, 1.955, 1.9066, 1.8654, 1.8298, 1.7986, 1.771, 1.7464, 1.7244, 1.7044, 1.6863, 1.6697, 1.6544],
    [127, 3.9157, 3.0675, 2.6759, 2.443, 2.2856, 2.1707, 2.0824, 2.0121, 1.9544, 1.906, 1.8648, 1.8291, 1.7979, 1.7704, 1.7458, 1.7237, 1.7038, 1.6856, 1.669, 1.6538],
    [128, 3.9151, 3.0669, 2.6754, 2.4424, 2.285, 2.1701, 2.0819, 2.0115, 1.9538, 1.9054, 1.8642, 1.8285, 1.7974, 1.7698, 1.7452, 1.7231, 1.7031, 1.685, 1.6684, 1.6531],
    [129, 3.9145, 3.0664, 2.6749, 2.4419, 2.2845, 2.1696, 2.0813, 2.0109, 1.9532, 1.9048, 1.8636, 1.828, 1.7967, 1.7692, 1.7446, 1.7225, 1.7025, 1.6843, 1.6677, 1.6525],
    [130, 3.914, 3.0659, 2.6743, 2.4414, 2.2839, 2.169, 2.0807, 2.0103, 1.9526, 1.9042, 1.863, 1.8273, 1.7962, 1.7685, 1.744, 1.7219, 1.7019, 1.6837, 1.6671, 1.6519],
    [131, 3.9134, 3.0653, 2.6737, 2.4408, 2.2834, 2.1685, 2.0802, 2.0098, 1.9521, 1.9037, 1.8624, 1.8268, 1.7956, 1.768, 1.7434, 1.7213, 1.7013, 1.6831, 1.6665, 1.6513],
    [132, 3.9129, 3.0648, 2.6732, 2.4403, 2.2829, 2.168, 2.0796, 2.0092, 1.9515, 1.9031, 1.8619, 1.8262, 1.795, 1.7674, 1.7428, 1.7207, 1.7007, 1.6825, 1.6659, 1.6506],
    [133, 3.9123, 3.0642, 2.6727, 2.4398, 2.2823, 2.1674, 2.0791, 2.0087, 1.951, 1.9026, 1.8613, 1.8256, 1.7944, 1.7668, 1.7422, 1.7201, 1.7001, 1.6819, 1.6653, 1.65],
    [134, 3.9118, 3.0637, 2.6722, 2.4392, 2.2818, 2.1669, 2.0786, 2.0082, 1.9504, 1.902, 1.8608, 1.8251, 1.7939, 1.7662, 1.7416, 1.7195, 1.6995, 1.6813, 1.6647, 1.6494],
    [135, 3.9112, 3.0632, 2.6717, 2.4387, 2.2813, 2.1664, 2.0781, 2.0076, 1.9499, 1.9015, 1.8602, 1.8245, 1.7933, 1.7657, 1.7411, 1.719, 1.6989, 1.6808, 1.6641, 1.6488],
    [136, 3.9108, 3.0627, 2.6712, 2.4382, 2.2808, 2.1659, 2.0775, 2.0071, 1.9494, 1.901, 1.8597, 1.824, 1.7928, 1.7651, 1.7405, 1.7184, 1.6984, 1.6802, 1.6635, 1.6483],
    [137, 3.9102, 3.0622, 2.6707, 2.4378, 2.2803, 2.1654, 2.077, 2.0066, 1.9488, 1.9004, 1.8592, 1.8235, 1.7922, 1.7646, 1.74, 1.7178, 1.6978, 1.6796, 1.663, 1.6477],
    [138, 3.9098, 3.0617, 2.6702, 2.4373, 2.2798, 2.1649, 2.0766, 2.0061, 1.9483, 1.8999, 1.8586, 1.823, 1.7917, 1.7641, 1.7394, 1.7173, 1.6973, 1.6791, 1.6624, 1.6471],
    [139, 3.9092, 3.0613, 2.6697, 2.4368, 2.2794, 2.1644, 2.0761, 2.0056, 1.9478, 1.8994, 1.8581, 1.8224, 1.7912, 1.7635, 1.7389, 1.7168, 1.6967, 1.6785, 1.6619, 1.6466],
    [140, 3.9087, 3.0608, 2.6692, 2.4363, 2.2789, 2.1639, 2.0756, 2.0051, 1.9473, 1.8989, 1.8576, 1.8219, 1.7907, 1.763, 1.7384, 1.7162, 1.6962, 1.678, 1.6613, 1.646],
    [141, 3.9083, 3.0603, 2.6688, 2.4359, 2.2784, 2.1634, 2.0751, 2.0046, 1.9469, 1.8984, 1.8571, 1.8214, 1.7901, 1.7625, 1.7379, 1.7157, 1.6957, 1.6775, 1.6608, 1.6455],
    [142, 3.9078, 3.0598, 2.6683, 2.4354, 2.2779, 2.163, 2.0747, 2.0042, 1.9464, 1.8979, 1.8566, 1.8209, 1.7897, 1.762, 1.7374, 1.7152, 1.6952, 1.6769, 1.6603, 1.645],
    [143, 3.9073, 3.0594, 2.6679, 2.435, 2.2775, 2.1625, 2.0742, 2.0037, 1.9459, 1.8975, 1.8562, 1.8204, 1.7892, 1.7615, 1.7368, 1.7147, 1.6946, 1.6764, 1.6598, 1.6444],
    [144, 3.9068, 3.0589, 2.6675, 2.4345, 2.277, 2.1621, 2.0737, 2.0033, 1.9455, 1.897, 1.8557, 1.82, 1.7887, 1.761, 1.7364, 1.7142, 1.6941, 1.6759, 1.6592, 1.6439],
    [145, 3.9064, 3.0585, 2.667, 2.4341, 2.2766, 2.1617, 2.0733, 2.0028, 1.945, 1.8965, 1.8552, 1.8195, 1.7882, 1.7605, 1.7359, 1.7137, 1.6936, 1.6754, 1.6587, 1.6434],
    [146, 3.906, 3.0581, 2.6666, 2.4337, 2.2762, 2.1612, 2.0728, 2.0024, 1.9445, 1.8961, 1.8548, 1.819, 1.7877, 1.7601, 1.7354, 1.7132, 1.6932, 1.6749, 1.6582, 1.6429],
    [147, 3.9055, 3.0576, 2.6662, 2.4332, 2.2758, 2.1608, 2.0724, 2.0019, 1.9441, 1.8956, 1.8543, 1.8186, 1.7873, 1.7596, 1.7349, 1.7127, 1.6927, 1.6744, 1.6578, 1.6424],
    [148, 3.9051, 3.0572, 2.6657, 2.4328, 2.2753, 2.1604, 2.072, 2.0015, 1.9437, 1.8952, 1.8539, 1.8181, 1.7868, 1.7591, 1.7344, 1.7123, 1.6922, 1.6739, 1.6573, 1.6419],
    [149, 3.9046, 3.0568, 2.6653, 2.4324, 2.2749, 2.1599, 2.0716, 2.0011, 1.9432, 1.8947, 1.8534, 1.8177, 1.7864, 1.7587, 1.734, 1.7118, 1.6917, 1.6735, 1.6568, 1.6414],
    [150, 3.9042, 3.0564, 2.6649, 2.4319, 2.2745, 2.1595, 2.0711, 2.0006, 1.9428, 1.8943, 1.853, 1.8172, 1.7859, 1.7582, 1.7335, 1.7113, 1.6913, 1.673, 1.6563, 1.641],
    [151, 3.9038, 3.056, 2.6645, 2.4315, 2.2741, 2.1591, 2.0707, 2.0002, 1.9424, 1.8939, 1.8526, 1.8168, 1.7855, 1.7578, 1.7331, 1.7109, 1.6908, 1.6726, 1.6558, 1.6405],
    [152, 3.9033, 3.0555, 2.6641, 2.4312, 2.2737, 2.1587, 2.0703, 1.9998, 1.942, 1.8935, 1.8521, 1.8163, 1.785, 1.7573, 1.7326, 1.7104, 1.6904, 1.6721, 1.6554, 1.64],
    [153, 3.903, 3.0552, 2.6637, 2.4308, 2.2733, 2.1583, 2.0699, 1.9994, 1.9416, 1.8931, 1.8517, 1.8159, 1.7846, 1.7569, 1.7322, 1.71, 1.6899, 1.6717, 1.6549, 1.6396],
    [154, 3.9026, 3.0548, 2.6634, 2.4304, 2.2729, 2.1579, 2.0695, 1.999, 1.9412, 1.8926, 1.8513, 1.8155, 1.7842, 1.7565, 1.7318, 1.7096, 1.6895, 1.6712, 1.6545, 1.6391],
    [155, 3.9021, 3.0544, 2.6629, 2.43, 2.2725, 2.1575, 2.0691, 1.9986, 1.9407, 1.8923, 1.8509, 1.8151, 1.7838, 1.7561, 1.7314, 1.7091, 1.6891, 1.6708, 1.654, 1.6387],
    [156, 3.9018, 3.054, 2.6626, 2.4296, 2.2722, 2.1571, 2.0687, 1.9982, 1.9403, 1.8918, 1.8505, 1.8147, 1.7834, 1.7557, 1.7309, 1.7087, 1.6886, 1.6703, 1.6536, 1.6383],
    [157, 3.9014, 3.0537, 2.6622, 2.4293, 2.2717, 2.1568, 2.0684, 1.9978, 1.94, 1.8915, 1.8501, 1.8143, 1.7829, 1.7552, 1.7305, 1.7083, 1.6882, 1.6699, 1.6532, 1.6378],
    [158, 3.901, 3.0533, 2.6618, 2.4289, 2.2714, 2.1564, 2.068, 1.9974, 1.9396, 1.8911, 1.8497, 1.8139, 1.7826, 1.7548, 1.7301, 1.7079, 1.6878, 1.6695, 1.6528, 1.6374],
    [159, 3.9006, 3.0529, 2.6615, 2.4285, 2.271, 2.156, 2.0676, 1.997, 1.9392, 1.8907, 1.8493, 1.8135, 1.7822, 1.7544, 1.7297, 1.7075, 1.6874, 1.6691, 1.6524, 1.637],
    [160, 3.9002, 3.0525, 2.6611, 2.4282, 2.2706, 2.1556, 2.0672, 1.9967, 1.9388, 1.8903, 1.8489, 1.8131, 1.7818, 1.754, 1.7293, 1.7071, 1.687, 1.6687, 1.6519, 1.6366],
    [161, 3.8998, 3.0522, 2.6607, 2.4278, 2.2703, 2.1553, 2.0669, 1.9963, 1.9385, 1.8899, 1.8485, 1.8127, 1.7814, 1.7537, 1.7289, 1.7067, 1.6866, 1.6683, 1.6515, 1.6361],
    [162, 3.8995, 3.0518, 2.6604, 2.4275, 2.27, 2.155, 2.0665, 1.9959, 1.9381, 1.8895, 1.8482, 1.8124, 1.781, 1.7533, 1.7285, 1.7063, 1.6862, 1.6679, 1.6511, 1.6357],
    [163, 3.8991, 3.0515, 2.6601, 2.4271, 2.2696, 2.1546, 2.0662, 1.9956, 1.9377, 1.8892, 1.8478, 1.812, 1.7806, 1.7529, 1.7282, 1.7059, 1.6858, 1.6675, 1.6507, 1.6353],
    [164, 3.8987, 3.0512, 2.6597, 2.4268, 2.2693, 2.1542, 2.0658, 1.9953, 1.9374, 1.8888, 1.8474, 1.8116, 1.7803, 1.7525, 1.7278, 1.7055, 1.6854, 1.6671, 1.6503, 1.6349],
    [165, 3.8985, 3.0508, 2.6594, 2.4264, 2.2689, 2.1539, 2.0655, 1.9949, 1.937, 1.8885, 1.8471, 1.8112, 1.7799, 1.7522, 1.7274, 1.7052, 1.685, 1.6667, 1.6499, 1.6345],
    [166, 3.8981, 3.0505, 2.6591, 2.4261, 2.2686, 2.1536, 2.0651, 1.9945, 1.9367, 1.8881, 1.8467, 1.8109, 1.7795, 1.7518, 1.727, 1.7048, 1.6846, 1.6663, 1.6496, 1.6341],
    [167, 3.8977, 3.0502, 2.6587, 2.4258, 2.2683, 2.1533, 2.0648, 1.9942, 1.9363, 1.8878, 1.8464, 1.8105, 1.7792, 1.7514, 1.7266, 1.7044, 1.6843, 1.6659, 1.6492, 1.6338],
    [168, 3.8974, 3.0498, 2.6584, 2.4254, 2.268, 2.1529, 2.0645, 1.9939, 1.936, 1.8874, 1.846, 1.8102, 1.7788, 1.7511, 1.7263, 1.704, 1.6839, 1.6656, 1.6488, 1.6334],
    [169, 3.8971, 3.0495, 2.6581, 2.4251, 2.2676, 2.1526, 2.0641, 1.9936, 1.9357, 1.8871, 1.8457, 1.8099, 1.7785, 1.7507, 1.7259, 1.7037, 1.6835, 1.6652, 1.6484, 1.633],
    [170, 3.8967, 3.0492, 2.6578, 2.4248, 2.2673, 2.1523, 2.0638, 1.9932, 1.9353, 1.8868, 1.8454, 1.8095, 1.7781, 1.7504, 1.7256, 1.7033, 1.6832, 1.6648, 1.6481, 1.6326],
    [171, 3.8965, 3.0488, 2.6575, 2.4245, 2.267, 2.152, 2.0635, 1.9929, 1.935, 1.8864, 1.845, 1.8092, 1.7778, 1.75, 1.7252, 1.703, 1.6828, 1.6645, 1.6477, 1.6323],
    [172, 3.8961, 3.0485, 2.6571, 2.4242, 2.2667, 2.1516, 2.0632, 1.9926, 1.9347, 1.8861, 1.8447, 1.8088, 1.7774, 1.7497, 1.7249, 1.7026, 1.6825, 1.6641, 1.6473, 1.6319],
    [173, 3.8958, 3.0482, 2.6568, 2.4239, 2.2664, 2.1513, 2.0628, 1.9923, 1.9343, 1.8858, 1.8443, 1.8085, 1.7771, 1.7493, 1.7246, 1.7023, 1.6821, 1.6638, 1.647, 1.6316],
    [174, 3.8954, 3.0479, 2.6566, 2.4236, 2.266, 2.151, 2.0626, 1.9919, 1.934, 1.8855, 1.844, 1.8082, 1.7768, 1.749, 1.7242, 1.7019, 1.6818, 1.6634, 1.6466, 1.6312],
    [175, 3.8952, 3.0476, 2.6563, 2.4233, 2.2658, 2.1507, 2.0622, 1.9916, 1.9337, 1.8852, 1.8437, 1.8078, 1.7764, 1.7487, 1.7239, 1.7016, 1.6814, 1.6631, 1.6463, 1.6309],
    [176, 3.8948, 3.0473, 2.6559, 2.423, 2.2655, 2.1504, 2.0619, 1.9913, 1.9334, 1.8848, 1.8434, 1.8075, 1.7761, 1.7483, 1.7236, 1.7013, 1.6811, 1.6628, 1.646, 1.6305],
    [177, 3.8945, 3.047, 2.6556, 2.4227, 2.2652, 2.1501, 2.0616, 1.991, 1.9331, 1.8845, 1.8431, 1.8072, 1.7758, 1.748, 1.7232, 1.7009, 1.6808, 1.6624, 1.6456, 1.6302],
    [178, 3.8943, 3.0467, 2.6554, 2.4224, 2.2649, 2.1498, 2.0613, 1.9907, 1.9328, 1.8842, 1.8428, 1.8069, 1.7755, 1.7477, 1.7229, 1.7006, 1.6805, 1.6621, 1.6453, 1.6298],
    [179, 3.8939, 3.0465, 2.6551, 2.4221, 2.2646, 2.1495, 2.0611, 1.9904, 1.9325, 1.8839, 1.8425, 1.8066, 1.7752, 1.7474, 1.7226, 1.7003, 1.6801, 1.6618, 1.645, 1.6295],
    [180, 3.8936, 3.0462, 2.6548, 2.4218, 2.2643, 2.1492, 2.0608, 1.9901, 1.9322, 1.8836, 1.8422, 1.8063, 1.7749, 1.7471, 1.7223, 1.7, 1.6798, 1.6614, 1.6446, 1.6292],
    [181, 3.8933, 3.0458, 2.6545, 2.4216, 2.264, 2.149, 2.0605, 1.9899, 1.9319, 1.8833, 1.8419, 1.806, 1.7746, 1.7468, 1.7219, 1.6997, 1.6795, 1.6611, 1.6443, 1.6289],
    [182, 3.8931, 3.0456, 2.6543, 2.4213, 2.2638, 2.1487, 2.0602, 1.9896, 1.9316, 1.883, 1.8416, 1.8057, 1.7743, 1.7465, 1.7217, 1.6994, 1.6792, 1.6608, 1.644, 1.6286],
    [183, 3.8928, 3.0453, 2.654, 2.421, 2.2635, 2.1484, 2.0599, 1.9893, 1.9313, 1.8827, 1.8413, 1.8054, 1.774, 1.7462, 1.7214, 1.6991, 1.6789, 1.6605, 1.6437, 1.6282],
    [184, 3.8925, 3.045, 2.6537, 2.4207, 2.2632, 2.1481, 2.0596, 1.989, 1.9311, 1.8825, 1.841, 1.8051, 1.7737, 1.7459, 1.721, 1.6987, 1.6786, 1.6602, 1.6434, 1.6279],
    [185, 3.8923, 3.0448, 2.6534, 2.4205, 2.263, 2.1479, 2.0594, 1.9887, 1.9308, 1.8822, 1.8407, 1.8048, 1.7734, 1.7456, 1.7208, 1.6984, 1.6783, 1.6599, 1.643, 1.6276],
    [186, 3.892, 3.0445, 2.6531, 2.4202, 2.2627, 2.1476, 2.0591, 1.9885, 1.9305, 1.8819, 1.8404, 1.8045, 1.7731, 1.7453, 1.7205, 1.6981, 1.678, 1.6596, 1.6428, 1.6273],
    [187, 3.8917, 3.0442, 2.6529, 2.4199, 2.2624, 2.1473, 2.0588, 1.9882, 1.9302, 1.8816, 1.8401, 1.8042, 1.7728, 1.745, 1.7202, 1.6979, 1.6777, 1.6593, 1.6424, 1.627],
    [188, 3.8914, 3.044, 2.6526, 2.4197, 2.2621, 2.1471, 2.0586, 1.9879, 1.9299, 1.8814, 1.8399, 1.804, 1.7725, 1.7447, 1.7199, 1.6976, 1.6774, 1.659, 1.6421, 1.6267],
    [189, 3.8912, 3.0437, 2.6524, 2.4195, 2.2619, 2.1468, 2.0583, 1.9877, 1.9297, 1.8811, 1.8396, 1.8037, 1.7722, 1.7444, 1.7196, 1.6973, 1.6771, 1.6587, 1.6418, 1.6264],
    [190, 3.8909, 3.0435, 2.6521, 2.4192, 2.2617, 2.1466, 2.0581, 1.9874, 1.9294, 1.8808, 1.8393, 1.8034, 1.772, 1.7441, 1.7193, 1.697, 1.6768, 1.6584, 1.6416, 1.6261],
    [191, 3.8906, 3.0432, 2.6519, 2.4189, 2.2614, 2.1463, 2.0578, 1.9871, 1.9292, 1.8805, 1.8391, 1.8032, 1.7717, 1.7439, 1.719, 1.6967, 1.6765, 1.6581, 1.6413, 1.6258],
    [192, 3.8903, 3.043, 2.6516, 2.4187, 2.2611, 2.1461, 2.0575, 1.9869, 1.9289, 1.8803, 1.8388, 1.8029, 1.7714, 1.7436, 1.7188, 1.6964, 1.6762, 1.6578, 1.641, 1.6255],
    [193, 3.8901, 3.0427, 2.6514, 2.4184, 2.2609, 2.1458, 2.0573, 1.9866, 1.9286, 1.88, 1.8385, 1.8026, 1.7712, 1.7433, 1.7185, 1.6961, 1.6759, 1.6575, 1.6407, 1.6252],
    [194, 3.8899, 3.0425, 2.6512, 2.4182, 2.2606, 2.1456, 2.057, 1.9864, 1.9284, 1.8798, 1.8383, 1.8023, 1.7709, 1.7431, 1.7182, 1.6959, 1.6757, 1.6572, 1.6404, 1.6249],
    [195, 3.8896, 3.0422, 2.6509, 2.418, 2.2604, 2.1453, 2.0568, 1.9861, 1.9281, 1.8795, 1.838, 1.8021, 1.7706, 1.7428, 1.7179, 1.6956, 1.6754, 1.657, 1.6401, 1.6247],
    [196, 3.8893, 3.042, 2.6507, 2.4177, 2.2602, 2.1451, 2.0566, 1.9859, 1.9279, 1.8793, 1.8377, 1.8018, 1.7704, 1.7425, 1.7177, 1.6953, 1.6751, 1.6567, 1.6399, 1.6244],
    [197, 3.8891, 3.0418, 2.6504, 2.4175, 2.26, 2.1448, 2.0563, 1.9856, 1.9277, 1.879, 1.8375, 1.8016, 1.7701, 1.7423, 1.7174, 1.6951, 1.6748, 1.6564, 1.6396, 1.6241],
    [198, 3.8889, 3.0415, 2.6502, 2.4173, 2.2597, 2.1446, 2.0561, 1.9854, 1.9274, 1.8788, 1.8373, 1.8013, 1.7699, 1.742, 1.7172, 1.6948, 1.6746, 1.6562, 1.6393, 1.6238],
    [199, 3.8886, 3.0413, 2.65, 2.417, 2.2595, 2.1444, 2.0558, 1.9852, 1.9272, 1.8785, 1.837, 1.8011, 1.7696, 1.7418, 1.7169, 1.6946, 1.6743, 1.6559, 1.6391, 1.6236],
    [200, 3.8883, 3.041, 2.6497, 2.4168, 2.2592, 2.1441, 2.0556, 1.9849, 1.9269, 1.8783, 1.8368, 1.8008, 1.7694, 1.7415, 1.7166, 1.6943, 1.6741, 1.6557, 1.6388, 1.62]])
        return ftest[row][col]



    def magic_read(self,infile):
        """ 
        reads  a Magic template file, puts data in a list of dictionaries
        """
        hold,magic_data,magic_record,magic_keys=[],[],{},[]
        try:
            f=open(infile,"rU")
        except:
            return [],'-E- can oprn MagIc file %s. bad_file'%infile
        firstline = f.readline().strip('\n')
        if firstline[0]=="s":
            delim='space'
        elif 'tab' in  firstline:
            delim='tab'
        else: 
            print 'error reading ', infile
            sys.exit()
        if delim=='space':
            file_type=firstline.split()[1]
        if delim=='tab':
            file_type=firstline.split('\t')[1]
        if file_type=='delimited':
            if delim=='space':file_type=firstline.split()[2]
            if delim=='tab':file_type=firstline.split('\t')[2]
        if delim=='space':
            line =f.readline().strip('\n').split()
        if delim=='tab':
            line =f.readline().strip('\n').split('\t')
        for key in line:
            magic_keys.append(key)
        for Line in f.readlines(): 
            line=Line.strip('\n')
            if delim=='space':
                rec=line.split()
            if delim=='tab':
                rec=line.split('\t')
            hold.append(rec)
        for rec in hold:
            magic_record={}
            if len(magic_keys) != len(rec):                
                print "Warning: Uneven record lengths detected: "
                print "MagIC keys:\n"
                print magic_keys
                print "line:\n"
                print rec
                print "-----"
            for k in range(len(rec)):
               magic_record[magic_keys[k]]=rec[k]   
            magic_data.append(magic_record)
        magictype=file_type.lower().split("_")
        Types=['er','magic','pmag','rmag']
        if magictype in Types:file_type=file_type.lower()
        return magic_data,file_type



    
##    def magic_read(self,infile):
##        """ 
##        reads  a Magic template file, puts data in a list of dictionaries
##        """
##        hold,magic_data,magic_record,magic_keys=[],[],{},[]
##        try:
##            f=open(infile,"rU")
##        except:
##            return [],'bad_file'
##        d = f.readline()[:-1].strip('\n')
##        if d[0]=="s" or d[1]=="s":
##            delim='space'
##        elif d[0]=="t" or d[1]=="t":
##            delim='tab'
##        else: 
##            print 'error reading ', infile
##            sys.exit()
##        if delim=='space':file_type=d.split()[1]
##        if delim=='tab':file_type=d.split('\t')[1]
##        if file_type=='delimited':
##            if delim=='space':file_type=d.split()[2]
##            if delim=='tab':file_type=d.split('\t')[2]
##        if delim=='space':line =f.readline()[:-1].split()
##        if delim=='tab':line =f.readline()[:-1].split('\t')
##        for key in line:
##            magic_keys.append(key)
##        lines=f.readlines()
##        #for line in lines[:-1]:
##        for Line in lines: #rshaar. what happens is that if the last columns is empty it wouldnt take it.            
##            #line.replace('\n','')
##            line=Line.strip('\n')
##            #if delim=='space':rec=line[:-1].split() rshaar
##            #if delim=='tab':rec=line[:-1].split('\t') rshaar
##            if delim=='space':rec=line.split()
##            if delim=='tab':rec=line.split('\t')
##            hold.append(rec)
##        #line = lines[-1].replace('\n','')
##        line = lines[-1].strip('\n') #rshaar
##        #if delim=='space':rec=line[:-1].split() 
##        #if delim=='tab':rec=line.split('\t')
##        if delim=='space':rec=line.split() 
##        if delim=='tab':rec=line.split('\t')
##        hold.append(rec)
##        for rec in hold:
##            magic_record={}
##            if len(magic_keys) != len(rec):
##                
##                print "Warning: Uneven record lengths detected: "
##                print magic_keys
##                print rec
##                print line
##            for k in range(len(rec)):
##               magic_record[magic_keys[k]]=rec[k].strip('\n')
##            magic_data.append(magic_record)
##        magictype=file_type.lower().split("_")
##        Types=['er','magic','pmag','rmag']
##        if magictype in Types:file_type=file_type.lower()
##        return magic_data,file_type


    def get_specs(self,data):
        """
         takes a magic format file and returns a list of unique specimen names
        """
    # sort the specimen names
    #
        speclist=[]
        for rec in data:
          spec=rec["er_specimen_name"]
          if spec not in speclist:speclist.append(spec)
        speclist.sort()
        return speclist



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
                if "LP-PI-TRM-IZ" in methcodes or "LP-PI-M-IZ" in methcodes: 
                    ZI=0    
                elif "LP-PI-TRM-ZI" in methcodes or "LP-PI-M-ZI" in methcodes: 
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
                X=self.dir2cart([idec,iinc,istr])
                BL=self.dir2cart([dec,inc,str])
                I=[]
                for c in range(3): I.append((X[c]-BL[c]))
                if I[2]!=0:
                    iDir=self.cart2dir(I)
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
                    cart1=array(self.dir2cart([dec1,inc1,moment1]))
                    irec2=datablock[ISteps[i]]
                    dec2=float(irec2["measurement_dec"])
                    inc2=float(irec2["measurement_inc"])
                    moment2=float(irec2["measurement_magn_moment"])
                    cart2=array(self.dir2cart([dec2,inc2,moment2]))

                    # check if its in the same treatment
                    if Treat_I[i] == Treat_I[i-2] and dec2!=dec_initial and inc2!=inc_initial:
                        continue
                    if dec1!=dec2 and inc1!=inc2:
                        zerofield=(cart2+cart1)/2
                        infield=(cart2-cart1)/2

                        DIR_zerofield=self.cart2dir(zerofield)
                        DIR_infield=self.cart2dir(infield)

                        first_Z.append([temp,DIR_zerofield[0],DIR_zerofield[1],DIR_zerofield[2],0])
                        first_I.append([temp,DIR_infield[0],DIR_infield[1],DIR_infield[2],0])
                

        #---------------------
        # find  pTRM checks
        #---------------------
                    
        for temp in Treat_PI: # look through infield steps and find matching Z step
            #print temp
            foundit=False
            for i in range(1,len(datablock)): # look through infield steps and find what step was before the pTRM check
                rec=datablock[i]
                dec=float(rec["measurement_dec"])
                inc=float(rec["measurement_inc"])
                moment=float(rec["measurement_magn_moment"])
                phi=float(rec["treatment_dc_field_phi"])
                theta=float(rec["treatment_dc_field_theta"])
                M=array(self.dir2cart([dec,inc,moment]))

                if 'LT-PTRM-I' in rec['magic_method_codes'] or 'LT-PMRM-I' in rec['magic_method_codes'] :
                    if (THERMAL and "treatment_temp" in rec.keys() and float(rec["treatment_temp"])==float(temp) )\
                       or (MICROWAVE and "measurement_description" in rec.keys() and "Step Number-%.0f"%float(temp) in rec["measurement_description"]):
                        prev_rec=datablock[i-1]
                        prev_dec=float(prev_rec["measurement_dec"])
                        prev_inc=float(prev_rec["measurement_inc"])
                        prev_moment=float(prev_rec["measurement_magn_moment"])
                        prev_phi=float(prev_rec["treatment_dc_field_phi"])
                        prev_theta=float(prev_rec["treatment_dc_field_theta"])
                        prev_M=array(self.dir2cart([prev_dec,prev_inc,prev_moment]))
                        foundit=True
                        #print "found it"
                        #print prev_dec,prev_inc,prev_moment
                        break

            if 'LP-PI-II' not in methcodes:
                # previous measurements is either T (tail check) or Z (tail check)
                if foundit:
##                    step=PISteps[Treat_PI.index(temp)]
##                    rec=datablock[step]
    ##                brec=datablock[step-1] # take last record as baseline to subtract
    ##                pdec=float(brec["measurement_dec"])
    ##                pinc=float(brec["measurement_inc"])
    ##                pint=float(brec[momkey])
##                    X=self.dir2cart([dec,inc,str])
##                    prevX=self.dir2cart([prev_dec,prev_inc,prev_moment])

                    diff_cart=M-prev_M
                    diff_dir=self.cart2dir(diff_cart)
                    ptrm_check.append([temp,diff_dir[0],diff_dir[1],diff_dir[2]])


##                    I=[]
##                    for c in range(3): I.append(X[c]-prevX[c])
##                    dir1=self.cart2dir(I)
##                    if Zdiff==0:
##                        ptrm_check.append([temp,dir1[0],dir1[1],dir1[2]])
##                    else:
##                        ptrm_check.append([temp,0.,0.,I[2]])
            else:
                if foundit:
##                    step=PISteps[Treat_PI.index(temp)]
##                    rec=datablock[step]
##                    dec=float(rec["measurement_dec"])
##                    inc=float(rec["measurement_inc"])
##                    moment=float(rec["measurement_magn_moment"])
##                    phi=float(rec["treatment_dc_field_phi"])
##                    theta=float(rec["treatment_dc_field_theta"])
##                    M1=prev_M
##                    #M1=array(self.dir2cart([prev_dec,prev_inc,prev_moment]))
##                    M2=array(self.dir2cart([dec,inc,moment]))

                    if theta!=prev_theta:
                        diff=(M-prev_M)/2
                        diff_dir=self.cart2dir(diff)
                        ptrm_check.append([temp,diff_dir[0],diff_dir[1],diff_dir[2]])
                    else:
                        print "-W- WARNING: specimen. pTRM check not in place in Thellier Thellier protocol. step please check"
                        
                        
                        
    # in case there are zero-field pTRM checks (not the SIO way)
        for temp in Treat_PZ:
            step=PZSteps[Treat_PZ.index(temp)]
            rec=datablock[step]
            dec=float(rec["measurement_dec"])
            inc=float(rec["measurement_inc"])
            str=float(rec[momkey])
            brec=datablock[step-1]
            pdec=float(brec["measurement_dec"])
            pinc=float(brec["measurement_inc"])
            pint=float(brec[momkey])
            X=self.dir2cart([dec,inc,str])
            prevX=self.dir2cart([pdec,pinc,pint])
            I=[]
            for c in range(3): I.append(X[c]-prevX[c])
            dir2=self.cart2dir(I)
            zptrm_check.append([temp,dir2[0],dir2[1],dir2[2]])


##        ## get pTRM tail checks together -
##        for temp in Treat_M:
##            step=MSteps[Treat_M.index(temp)] # tail check step - just do a difference in magnitude!
##            rec=datablock[step]
##            str=float(rec[momkey])
##            if temp in Treat_Z:
##                step=ZSteps[Treat_Z.index(temp)]
##                brec=datablock[step]
##                pint=float(brec[momkey])
##                ptrm_tail.append([temp,0,0,str-pint])  # difference - if negative, negative tail!
##            else:
##                print s, '  has a tail check with no first zero field step - check input file! for step',temp-273.


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
                    #print "yes"
                    #print "Step Number-%.0f"%float(temp)
                    #print rec["measurement_description"]
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
            V0=self.dir2cart([dec0,inc0,moment0])

            # find the infield step that comes before the additivity check
            foundit=False
            for j in range(step_0,1,-1):
                if "LT-T-I" in datablock[j]['magic_method_codes']:
                  foundit=True ; break
            if foundit:
                dec1=float(datablock[j]["measurement_dec"])
                inc1=float(datablock[j]["measurement_inc"])
                moment1=float(datablock[j]['measurement_magn_moment'])
                V1=self.dir2cart([dec1,inc1,moment1])
                
                I=[]
                for c in range(3): I.append(V1[c]-V0[c])
                dir1=self.cart2dir(I)
                additivity_check.append([temp,dir1[0],dir1[1],dir1[2]])

        araiblock=(first_Z,first_I,ptrm_check,ptrm_tail,zptrm_check,GammaChecks,additivity_check)

        
        return araiblock,field



#--------------------------------------------------------------    
# Change Acceptance criteria dialog
#--------------------------------------------------------------


class Criteria_Dialog(wx.Dialog):

    def __init__(self, parent, accept_new_parameters,title):
        style =  wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER  
        super(Criteria_Dialog, self).__init__(parent, title=title,style=style)
        self.accept_new_parameters=accept_new_parameters
        #print self.accept_new_parameters
        self.InitUI(accept_new_parameters)
        #self.SetSize((250, 200))

    def InitUI(self,accept_new_parameters):


        pnl1 = wx.Panel(self)

        vbox = wx.BoxSizer(wx.VERTICAL)

        bSizer1 = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "Specimen acceptance criteria" ), wx.HORIZONTAL )

        # Specimen criteria

        window_list_specimens=['int_n','int_ptrm_n','frac','gmax','f','fvds','b_beta','g','q','int_mad','dang','drats','md']
        for key in window_list_specimens:
            command="self.set_specimen_%s=wx.TextCtrl(pnl1,style=wx.TE_CENTER,size=(50,20))"%key
            exec command
        self.set_specimen_scat=wx.CheckBox(pnl1, -1, '', (50, 50))        
        criteria_specimen_window = wx.GridSizer(2, 14, 6, 6)
        criteria_specimen_window.AddMany( [(wx.StaticText(pnl1,label="int_n",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="int_ptrm_n",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="FRAC",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="SCAT",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="gap_max",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="f",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="fvds",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="beta",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="g",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="q",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="MAD",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="DANG",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="DRATS",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="MD tail",style=wx.TE_CENTER), wx.EXPAND),
            (self.set_specimen_int_n),
            (self.set_specimen_int_ptrm_n),
            (self.set_specimen_frac),
            (self.set_specimen_scat),                        
            (self.set_specimen_gmax),
            (self.set_specimen_f),
            (self.set_specimen_fvds),
            (self.set_specimen_b_beta),
            (self.set_specimen_g),
            (self.set_specimen_q),
            (self.set_specimen_int_mad),
            (self.set_specimen_dang),
            (self.set_specimen_drats),                                
            (self.set_specimen_md)])
                                           

        bSizer1.Add( criteria_specimen_window, 0, wx.ALIGN_LEFT|wx.ALL, 5 )

        #-----------        

        bSizer1a = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "anisotropy criteria" ), wx.HORIZONTAL )
        self.set_anisotropy_alt=wx.TextCtrl(pnl1,style=wx.TE_CENTER,size=(50,20))
        self.check_aniso_ftest= wx.CheckBox(pnl1, -1, '', (10, 10))
        criteria_aniso_window = wx.GridSizer(2, 2, 6, 6)
        criteria_aniso_window.AddMany( [(wx.StaticText(pnl1,label="use F test as acceptance criteria",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="alteration check threshold value (%)",style=wx.TE_CENTER), wx.EXPAND),
            (self.check_aniso_ftest),
            (self.set_anisotropy_alt)])

        bSizer1a.Add( criteria_aniso_window, 0, wx.ALIGN_LEFT|wx.ALL, 5 )


        #-----------        

        #bSizer2 = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "" ), wx.HORIZONTAL )

        bSizer2 = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "Sample/Site acceptance criteria" ), wx.HORIZONTAL )
    
        self.set_average_by_sample_or_site=wx.ComboBox(pnl1, -1,size=(150, -1), value = 'sample', choices=['sample','site'], style=wx.CB_READONLY)
        
        # Sample criteria
        window_list_samples=['int_n','int_n_outlier_check']
        for key in window_list_samples:
            command="self.set_sample_%s=wx.TextCtrl(pnl1,style=wx.TE_CENTER,size=(50,20))"%key
            exec command
        criteria_sample_window = wx.GridSizer(2, 3, 6, 6)
        criteria_sample_window.AddMany( [(wx.StaticText(pnl1,label="Averge by sample/site",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="int_n",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="int_n_outlier_check",style=wx.TE_CENTER), wx.EXPAND),
            (self.set_average_by_sample_or_site),            
            (self.set_sample_int_n),
            (self.set_sample_int_n_outlier_check)])

        bSizer2.Add( criteria_sample_window, 0, wx.ALIGN_LEFT|wx.ALL, 5 )


        #-----------        


        bSizer2a = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "mean calculation algorithm" ), wx.HORIZONTAL )
    
        #self.set_sample_int_stdev_opt=wx.RadioButton(pnl1, -1, 'Enable STDEV-OPT', (10, 10), style=wx.RB_GROUP)
        #self.set_sample_int_bs=wx.RadioButton(pnl1, -1, 'Enable BS ', (10, 30))
        #self.set_sample_int_bs_par=wx.RadioButton(pnl1, -1, 'Enable BS_PAR', (50, 50))

        self.set_sample_int_stdev_opt=wx.RadioButton(pnl1, -1, '', (10, 10), style=wx.RB_GROUP)
        self.set_sample_int_bs=wx.RadioButton(pnl1, -1, ' ', (10, 30))
        self.set_sample_int_bs_par=wx.RadioButton(pnl1, -1, '', (50, 50))

        criteria_sample_window = wx.GridSizer(1, 3, 6, 6)
        criteria_sample_window.AddMany( [(wx.StaticText(pnl1,label="Enable STDEV-OPT",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="Enable BS",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="Enable BS_PAR",style=wx.TE_CENTER), wx.EXPAND),
            (self.set_sample_int_stdev_opt),            
            (self.set_sample_int_bs),
            (self.set_sample_int_bs_par)])

        bSizer2a.Add( criteria_sample_window, 0, wx.ALIGN_LEFT|wx.ALL, 5 )


        #-----------        




        bSizer3 = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "Sample/site acceptance criteria: STDEV-OPT" ), wx.HORIZONTAL )
        # Sample STEV-OPT
        window_list_samples=['int_sigma_uT','int_sigma_perc','int_interval_uT','int_interval_perc','aniso_threshold_perc']
        for key in window_list_samples:
            command="self.set_sample_%s=wx.TextCtrl(pnl1,style=wx.TE_CENTER,size=(50,20))"%key
            exec command
        
        criteria_sample_window_2 = wx.GridSizer(2, 5, 6, 6)
        criteria_sample_window_2.AddMany( [(wx.StaticText(pnl1,label="int_sigma_uT",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="int_sigma_perc",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="int_interval",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="int_interval_perc",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="aniso_threshold_perc",style=wx.TE_CENTER), wx.EXPAND),
            (self.set_sample_int_sigma_uT),
            (self.set_sample_int_sigma_perc),
            (self.set_sample_int_interval_uT),
            (self.set_sample_int_interval_perc),
            (self.set_sample_aniso_threshold_perc)])

        bSizer3.Add( criteria_sample_window_2, 0, wx.ALIGN_LEFT|wx.ALL, 5 )




        #vbox1 = wx.BoxSizer(wx.VERTICAL)
        #vbox1.AddSpacer(10)
        #vbox1.Add(self.set_sample_int_stdev_opt,flag=wx.ALIGN_CENTER_HORIZONTAL)
        #vbox1.AddSpacer(10)
        #vbox1.Add(bSizer3,flag=wx.ALIGN_CENTER_HORIZONTAL)#,flag=wx.ALIGN_CENTER_VERTICAL)
        #vbox1.AddSpacer(10)
        
        
        #-----------        

        bSizer4 = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "Sample Acceptance criteria: BS / BS-PAR" ), wx.HORIZONTAL )
        window_list_samples=['int_BS_68_uT','int_BS_68_perc','int_BS_95_uT','int_BS_95_perc']
        for key in window_list_samples:
            command="self.set_sample_%s=wx.TextCtrl(pnl1,style=wx.TE_CENTER,size=(50,20))"%key
            exec command
        # for bootstarp
        self.set_specimen_int_max_slope_diff=wx.TextCtrl(pnl1,style=wx.TE_CENTER,size=(50,20))
        
        criteria_sample_window_3 = wx.GridSizer(2, 5, 6, 6)
        criteria_sample_window_3.AddMany( [(wx.StaticText(pnl1,label="specimen_int_max_slope_diff",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="int_BS_68_uT",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="int_BS_68_perc",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="int_BS_95_uT",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="int_BS_95_perc",style=wx.TE_CENTER), wx.EXPAND),                                           
            (self.set_specimen_int_max_slope_diff),                                           
            (self.set_sample_int_BS_68_uT),
            (self.set_sample_int_BS_68_perc),
            (self.set_sample_int_BS_95_uT),
            (self.set_sample_int_BS_95_perc)])

        bSizer4.Add( criteria_sample_window_3, 0, wx.ALIGN_LEFT|wx.ALL, 5 )

        #hbox2a = wx.BoxSizer(wx.HORIZONTAL)
        #hbox2a.Add(self.set_sample_int_bs,flag=wx.ALIGN_CENTER_VERTICAL)
        #hbox2a.AddSpacer(10)
        #hbox2a.Add(self.set_sample_int_bs_par,flag=wx.ALIGN_CENTER_VERTICAL)

        #vbox2 = wx.BoxSizer(wx.VERTICAL)
        #vbox2.AddSpacer(10)
        #vbox2.Add(hbox2a,flag=wx.ALIGN_CENTER_HORIZONTAL)#,flag=wx.ALIGN_CENTER_VERTICAL)
        #vbox2.AddSpacer(10)
        #vbox2.Add(bSizer4,flag=wx.ALIGN_CENTER_VERTICAL)#,flag=wx.ALIGN_CENTER_VERTICAL)
        #vbox2.AddSpacer(10)

        #-----------        



        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        self.okButton = wx.Button(pnl1, wx.ID_OK, "&OK")
        self.cancelButton = wx.Button(pnl1, wx.ID_CANCEL, '&Cancel')
        hbox3.Add(self.okButton)
        hbox3.AddSpacer(10)
        hbox3.Add(self.cancelButton )
        #self.okButton.Bind(wx.EVT_BUTTON, self.OnOK)
        #-----------

        

        # Intialize values
        #print self.accept_new_parameters

        for key in window_list_specimens:
            command="self.set_specimen_%s.SetBackgroundColour(wx.NullColour)"%key
        exec command


        # Intialize specimen values
        self.high_threshold_velue_list=['specimen_gmax','specimen_b_beta','specimen_dang','specimen_drats','specimen_int_mad','specimen_md']
        self.low_threshold_velue_list=['specimen_int_n','specimen_int_ptrm_n','specimen_f','specimen_fvds','specimen_frac','specimen_g','specimen_q']
              
        for key in self.high_threshold_velue_list + self.low_threshold_velue_list:
            if key in self.high_threshold_velue_list and float(self.accept_new_parameters[key]) >100 or\
               key in self.low_threshold_velue_list and float(self.accept_new_parameters[key]) <0.1:
                Value=""
                command="self.set_%s.SetValue(\"\")"%key
                exec command
                continue
            elif key in ['specimen_int_n','specimen_int_ptrm_n']:
                Value="%.0f"%self.accept_new_parameters[key]
            elif key in ['specimen_dang','specimen_drats','specimen_int_mad','specimen_md','specimen_g','specimen_q']:
                Value="%.1f"%self.accept_new_parameters[key]
            elif key in ['specimen_f','specimen_fvds','specimen_frac','specimen_b_beta','specimen_gmax']:
                Value="%.2f"%self.accept_new_parameters[key]

            command="self.set_%s.SetValue(Value)"%key
            exec command

        # Intialize scat values
        if self.accept_new_parameters['specimen_scat']==True:
            self.set_specimen_scat.SetValue(True)
        else:
            self.set_specimen_scat.SetValue(False)

        # Intialize anisotropy values

        if float(self.accept_new_parameters['anisotropy_alt']) < 100:
            self.set_anisotropy_alt.SetValue("%.1f"%(float(self.accept_new_parameters['anisotropy_alt'])))
        if self.accept_new_parameters['check_aniso_ftest'] in [True,"TRUE","True",'1',1]:
            self.check_aniso_ftest.SetValue(True)
        else:
            self.check_aniso_ftest.SetValue(False)
            

        if 'average_by_sample_or_site' in self.accept_new_parameters.keys() and self.accept_new_parameters['average_by_sample_or_site']=='site':
            self.set_average_by_sample_or_site.SetValue('site')
            
        # Intialize sample criteria values
        for key in ['sample_int_stdev_opt','sample_int_bs','sample_int_bs_par','sample_int_n','sample_int_sigma_uT','sample_int_sigma_perc','sample_aniso_threshold_perc','sample_int_interval_uT','sample_int_interval_perc','sample_int_n_outlier_check',\
                    'sample_int_BS_68_uT','sample_int_BS_95_uT','sample_int_BS_68_perc','sample_int_BS_95_perc']:
            #print "ron key",key
            if key in ['sample_int_n','sample_int_n_outlier_check']:
                if self.accept_new_parameters[key]<100:
                    Value="%.0f"%self.accept_new_parameters[key]
                else:
                    Value=""
                    
            elif key in ['sample_int_stdev_opt','sample_int_bs','sample_int_bs_par']:
                Value=self.accept_new_parameters[key]
                if Value==False: continue            
            else:
                if float(self.accept_new_parameters[key])>1000:
                    Value=""
                else:
                    Value="%.1f"%float(self.accept_new_parameters[key])                   
            #print "ron key value",key,Value
            command="self.set_%s.SetValue(Value)"%key
            #print command
            exec command
        if self.accept_new_parameters['sample_int_bs'] or self.accept_new_parameters['sample_int_bs_par']:
            if float(self.accept_new_parameters['specimen_int_max_slope_diff'])<100:
                self.set_specimen_int_max_slope_diff.SetValue("%.1f"%(float(self.accept_new_parameters['specimen_int_max_slope_diff'])))
            else:
                self.set_specimen_int_max_slope_diff.SetValue("")

        
        #----------------------  
        vbox.AddSpacer(10)
        vbox.Add(bSizer1, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(10)
        vbox.Add(bSizer1a, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(10)
        vbox.Add(bSizer2, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(10)
        vbox.Add(bSizer2a, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(10)
        vbox.Add(bSizer3, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(10)
        vbox.Add(bSizer4, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(10)
        vbox.Add(hbox3, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(10)
                    
        pnl1.SetSizer(vbox)
        vbox.Fit(self)


#--------------------------------------------------------------    
# Show a table
#--------------------------------------------------------------

class MyForm(wx.Frame):
    """"""
 
    #----------------------------------------------------------------------
    def __init__(self,number_of_rows_to_ignore,file_name):
        """Constructor"""
        wx.Frame.__init__(self, parent=None, title=file_name.split('/')[-1])
        
        panel = wx.Panel(self)

        self.read_the_file(file_name)
        
        self.myGrid = wx.grid.Grid(panel)
        self.myGrid.CreateGrid(len(self.report)-number_of_rows_to_ignore-1, len(self.report[number_of_rows_to_ignore]))
        index=0
        for i in range(len(self.report[number_of_rows_to_ignore])):
          self.myGrid.SetColLabelValue(i, self.report[number_of_rows_to_ignore][i])
        for i in range(1+number_of_rows_to_ignore,len(self.report)):
          for j in range(len(self.report[i])):
            self.myGrid.SetCellValue(index,j, self.report[i][j])
          index+=1
        self.myGrid.SetLabelFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Arial'))
        self.myGrid.SetDefaultCellFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Arial'))

        
        self.myGrid.AutoSize()
        #myGrid.SetRowLabelSize(0)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.myGrid, 1, wx.EXPAND)
        #sizer.Fit(self)
        panel.SetSizer(sizer)



    def  read_the_file(self,file_name):                    

##        dlg = wx.FileDialog(
##            self, message="choose a file in a pmagpy redo format",
##            style=wx.OPEN | wx.CHANGE_DIR
##            )
##        if dlg.ShowModal() == wx.ID_OK:
##            interpreter_output= dlg.GetPath()
##        dlg.Destroy()

        fin=open(str(file_name),'rU')
        self.report=[]
        for L in fin.readlines():
          line=L.strip('\n').split('\t')
          self.report.append(line)


#--------------------------------------------------------------    
# Save plots
#--------------------------------------------------------------

class SaveMyPlot(wx.Frame):
    """"""
    def __init__(self,fig,pars,plot_type):
        """Constructor"""
        wx.Frame.__init__(self, parent=None, title="")

        file_choices="(*.pdf)|*.pdf|(*.svg)|*.svg| (*.png)|*.png"
        default_fig_name="%s_%s.pdf"%(pars['er_specimen_name'],plot_type)
        dlg = wx.FileDialog(
            self, 
            message="Save plot as...",
            defaultDir=os.getcwd(),
            defaultFile=default_fig_name,
            wildcard=file_choices,
            style=wx.SAVE)
        
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            
        title=pars['er_specimen_name']
        self.panel = wx.Panel(self)
        self.dpi=300

        canvas_tmp_1 = FigCanvas(self.panel, -1, fig)
        canvas_tmp_1.print_figure(path, dpi=self.dpi)  

#----------------------------------------------------------------------

#===========================================================
# Consistency Test
#===========================================================
    

class Consistency_Test(wx.Frame):
    """"""
 
    #----------------------------------------------------------------------
    def __init__(self,Data,Data_hierarchy,WD,criteria):
        wx.Frame.__init__(self, parent=None)

        """
        """
        import  thellier_consistency_test        
        self.WD=WD
        self.Data=Data
        self.Data_hierarchy=Data_hierarchy
        self.fixed_criteria=criteria

        self.panel = wx.Panel(self)
        self.make_fixed_criteria()
        self.init_optimizer_frame()                

    def make_fixed_criteria(self):

        Text="Set fixed criteria parameters\n"
        
        dlg = wx.MessageDialog(self, Text, caption="First step", style=wx.OK )
        dlg.ShowModal(); dlg.Destroy()
        self.fixed_criteria['specimen_frac']=0
        self.fixed_criteria['specimen_b_beta']=10000000
        
        dia = Criteria_Dialog(None, self.fixed_criteria,title='Set fixed_criteria_file')
        dia.Center()

        if dia.ShowModal() == wx.ID_OK: # Until the user clicks OK, show the message            
            self.On_close_fixed_criteria_box(dia)
        

    def On_close_fixed_criteria_box(self,dia):
        

        self.high_threshold_velue_list=['specimen_gmax','specimen_b_beta','specimen_dang','specimen_drats','specimen_int_mad','specimen_md']
        self.low_threshold_velue_list=['specimen_int_n','specimen_int_ptrm_n','specimen_f','specimen_fvds','specimen_frac','specimen_g','specimen_q']

        for key in self.high_threshold_velue_list + self.low_threshold_velue_list +['anisotropy_alt']:
            command="self.fixed_criteria[\"%s\"]=float(dia.set_%s.GetValue())"%(key,key)
            try:
                exec command
            except:
                command="if dia.set_%s.GetValue() !=\"\" : self.show_messege(\"%s\")  "%(key,key)
                exec command
                
        if dia.set_specimen_scat.GetValue() == True:
          self.fixed_criteria['specimen_scat']=True
        else:
          self.fixed_criteria['specimen_scat']=False


        if dia.check_aniso_ftest.GetValue() == True:
          self.fixed_criteria['check_aniso_ftest']=True
        else:
          self.fixed_criteria['check_aniso_ftest']=False



        # sample ceiteria:            
        for key in ['sample_int_n','sample_int_sigma_uT','sample_int_sigma_perc','sample_aniso_threshold_perc','sample_int_interval_uT','sample_int_interval_perc','sample_int_n_outlier_check']:
            command="self.fixed_criteria[\"%s\"]=float(dia.set_%s.GetValue())"%(key,key)            
            try:
                exec command
            except:
                command="if dia.set_%s.GetValue() !=\"\" : self.show_messege(\"%s\")  "%(key,key)
                exec command


        #  message dialog
        dlg1 = wx.MessageDialog(self,caption="Warning:", message="Canges are save to consistency_test/pmag_fixed_criteria.txt" ,style=wx.OK|wx.CANCEL)
        result = dlg1.ShowModal()
        if result == wx.ID_CANCEL:

            dlg1.Destroy()

        if result == wx.ID_OK:

            dia.Destroy()
        
            # Write new acceptance criteria to pmag_criteria.txt    
            try:
                #Command_line="mkdir %s" %(self.WD+"/optimizer")
                #os.system(Command_line)
                os.mkdir(self.WD+"/consistency_test")
            except:
                pass
            fout=open(self.WD+"/consistency_test/pmag_fixed_criteria.txt",'w')
            String="tab\tpmag_criteria\n"
            fout.write(String)
            sample_criteria_list=[key for key in self.fixed_criteria.keys() if "sample" in key]
            specimen_criteria_list=self.high_threshold_velue_list + self.low_threshold_velue_list + ["specimen_scat"] +['check_aniso_ftest']+['anisotropy_alt']
            for criteria in specimen_criteria_list:
                if criteria in (self.high_threshold_velue_list + ['anisotropy_alt']) and float(self.fixed_criteria[criteria])>100:
                    specimen_criteria_list.remove(criteria)
                if criteria in self.low_threshold_velue_list and float(self.fixed_criteria[criteria])<0.1:
                    specimen_criteria_list.remove(criteria)
            header=""
            for key in sample_criteria_list:
                header=header+key+"\t"
            for key in specimen_criteria_list:                    
                header=header+key+"\t"
            fout.write(header[:-1]+"\n")

            line=""
            for key in sample_criteria_list:
                line=line+"%f"%self.fixed_criteria[key]+"\t"
            for key in specimen_criteria_list:
                if key=="specimen_scat" or key=="check_aniso_ftest":
                    line=line+"%s"%self.fixed_criteria[key]+"\t"
                else:
                    line=line+"%f"%self.fixed_criteria[key]+"\t"

            fout.write(line[:-1]+"\n")
            fout.close()



    # only valid naumber can be entered to boxes        
    def show_messege(self,key):
        dlg1 = wx.MessageDialog(self,caption="Error:",
            message="not a vaild value for box %s \n Ignore value"%key ,style=wx.OK)
        result = dlg1.ShowModal()
        if result == wx.ID_OK:
            dlg1.Destroy()
        
        
    def init_optimizer_frame(self):

        Text="Set Consistency Test function parameters"
        dlg = wx.MessageDialog(self, Text, caption="Second step", style=wx.OK )
        dlg.ShowModal(); dlg.Destroy()

        """ Build main frame od panel: buttons, etc.
            choose the first specimen and display data
        """

        self.beta_start_window=FS.FloatSpin(self.panel, -1, min_val=0.01, max_val=0.5,increment=0.01, value=0.05, extrastyle=FS.FS_LEFT,size=(50,20))
        self.beta_start_window.SetFormat("%f")
        self.beta_start_window.SetDigits(2)

        self.beta_end_window=FS.FloatSpin(self.panel, -1, min_val=0.01, max_val=0.5,increment=0.01, value=0.2, extrastyle=FS.FS_LEFT,size=(50,20))
        self.beta_end_window.SetFormat("%f")
        self.beta_end_window.SetDigits(2)

        self.beta_step_window=FS.FloatSpin(self.panel, -1, min_val=0.01, max_val=0.1,increment=0.01, value=0.01, extrastyle=FS.FS_LEFT,size=(50,20))
        self.beta_step_window.SetFormat("%f")
        self.beta_step_window.SetDigits(2)
       

        self.frac_start_window=FS.FloatSpin(self.panel, -1, min_val=0.1, max_val=1,increment=0.01, value=0.7, extrastyle=FS.FS_LEFT,size=(50,20))
        self.frac_start_window.SetFormat("%f")
        self.frac_start_window.SetDigits(2)

        self.frac_end_window=FS.FloatSpin(self.panel, -1, min_val=0.1, max_val=1,increment=0.01, value=0.9, extrastyle=FS.FS_LEFT,size=(50,20))
        self.frac_end_window.SetFormat("%f")
        self.frac_end_window.SetDigits(2)

        self.frac_step_window=FS.FloatSpin(self.panel, -1, min_val=0.01, max_val=0.1,increment=0.01, value=0.02, extrastyle=FS.FS_LEFT,size=(50,20))
        self.frac_step_window.SetFormat("%f")
        self.frac_step_window.SetDigits(2)

        
        beta_window = wx.GridSizer(2, 3, 5, 50)
        beta_window.AddMany( [(wx.StaticText(self.panel,label="beta start",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(self.panel,label="beta end",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(self.panel,label="beta step",style=wx.TE_CENTER), wx.EXPAND),
            (self.beta_start_window, wx.EXPAND) ,
            (self.beta_end_window, wx.EXPAND) ,
            (self.beta_step_window, wx.EXPAND) ])

        scat_window = wx.GridSizer(2, 3, 5, 50)
        
        scat_window.AddMany( [(wx.StaticText(self.panel,label="FRAC start",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(self.panel,label="FRAC end",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(self.panel,label="FRAC step",style=wx.TE_CENTER), wx.EXPAND),
            (self.frac_start_window, wx.EXPAND) ,
            (self.frac_end_window, wx.EXPAND) ,
            (self.frac_step_window, wx.EXPAND) ])
        Text1="insert functions in the text window below, each function in a seperate line.\n"
        Text2="Use a valid python syntax with logic or arithmetic operators\n (see example functions)\n\n"
        Text3="List of legal operands:\n"
        Text4="study_sample_n:  Total number of samples in the study that pass the criteria\n"
        Text5="test_group_n:  Number of test groups that have at least one sample that passed acceptance criteria\n" 
        Text6="max_group_int_sigma_uT:  standard deviation of the group with the maximum scatter \n"
        Text7="max_group_int_sigma_perc:  standard deviation of the group with the maximum scatter divided by its mean (in unit of %)\n\n"
        Text8="Check \"Check function syntax\" when done inserting functions.\n\n" 
                    
        self.function_label = wx.StaticText(self.panel, label=Text1+Text2+Text3+Text4+Text5+Text6+Text7+Text8,style=wx.ALIGN_CENTRE)

        # text_box 
        self.text_logger = wx.TextCtrl(self.panel, id=-1, size=(800,200), style= wx.HSCROLL|wx.TE_MULTILINE)
        self.Bind(wx.EVT_TEXT,self.on_change_function,self.text_logger)

        # check function button 
        self.check_button = wx.Button(self.panel, id=-1, label='Check function syntax')#,style=wx.BU_EXACTFIT)#, size=(175, 28))
        self.Bind(wx.EVT_BUTTON, self.on_check_button, self.check_button)

        # check function status 
        self.check_status=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50,20))

        # group definition  button 
#        self.optimizer_make_groups_next_button = wx.Button(self.panel, id=-1, label='Next')#,style=wx.BU_EXACTFIT)#, size=(175, 28))
#        self.Bind(wx.EVT_BUTTON, self.on_optimizer_make_groups_next_button, self.optimizer_make_groups_next_button)
        self.open_existing_optimizer_group_file = wx.Button(self.panel,id=-1, label='Choose a test group file')
        self.Bind(wx.EVT_BUTTON, self.on_open_existing_optimizer_group_file, self.open_existing_optimizer_group_file)

        self.optimizer_group_file_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(800,20))

        #self.make_new_optimizer_group_file = wx.Button(self.panel,id=-1, label='make new group definition file')#,style=wx.BU_EXACTFIT)#, size=(175, 28))
        #self.Bind(wx.EVT_BUTTON, self.on_make_new_optimizer_group_file, self.make_new_optimizer_group_file)

        # Cancel  button 
        self.cancel_optimizer_button = wx.Button(self.panel, id=-1, label='Cancel')#,style=wx.BU_EXACTFIT)#, size=(175, 28))
        self.Bind(wx.EVT_BUTTON, self.on_cancel_optimizer_button, self.cancel_optimizer_button)

        self.run_optimizer_button = wx.Button(self.panel, id=-1, label='Run Consistency Test')#,style=wx.BU_EXACTFIT)#, size=(175, 28))
        self.Bind(wx.EVT_BUTTON, self.on_run_optimizer_button, self.run_optimizer_button)

        # put an example
        try:
            function_in=open(self.WD+"/consistency_test/consistency_test_functions.txt",'rU')
            TEXT=""
            for line in function_in.readlines():
                TEXT=TEXT+line
        except:
            TEXT="study_sample_n\ntest_group_n\nmax_group_int_sigma_uT\nmax_group_int_sigma_perc\n((max_group_int_sigma_uT < 6) or (max_group_int_sigma_perc < 10)) and  int(study_sample_n)"

        self.text_logger.SetValue(TEXT)
            
        #TEXT=Text1+Text2+Text3+Text4+Text5+Text6+Text7+Text8

        #self.text_logger.SetValue()

        box=wx.BoxSizer(wx.wx.HORIZONTAL)
        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox1a = wx.BoxSizer(wx.HORIZONTAL)
        hbox1b = wx.BoxSizer(wx.HORIZONTAL)

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        hbox4 = wx.BoxSizer(wx.HORIZONTAL)
        hbox4a = wx.BoxSizer(wx.HORIZONTAL)
        hbox5 = wx.BoxSizer(wx.HORIZONTAL)
        hbox6 = wx.BoxSizer(wx.HORIZONTAL)
        hbox7 = wx.BoxSizer(wx.HORIZONTAL)
        hbox8 = wx.BoxSizer(wx.HORIZONTAL)


        hbox1a.AddSpacer(10)
        hbox1a.Add(beta_window,flag=wx.ALIGN_CENTER_VERTICAL,border=2)
        hbox1a.AddSpacer(10)

        hbox1b.AddSpacer(10)
        hbox1b.Add(scat_window,flag=wx.ALIGN_CENTER_VERTICAL,border=2)
        hbox1b.AddSpacer(10)

        hbox2.Add(self.function_label,flag=wx.ALIGN_CENTER_VERTICAL,border=2)

        hbox3.Add(self.text_logger,flag=wx.ALIGN_CENTER_HORIZONTAL)#,border=8)        

        hbox4.Add(self.check_button,flag=wx.ALIGN_CENTER_HORIZONTAL)#,border=8)
        hbox4a.Add(self.check_status,flag=wx.ALIGN_CENTER_HORIZONTAL)#,border=8)
        #hbox4.AddSpacer(50)
    
        #hbox6.Add(self.optimizer_make_groups_next_button,flag=wx.ALIGN_CENTER_HORIZONTAL)#,border=8)
        hbox5.Add(self.open_existing_optimizer_group_file,flag=wx.ALIGN_LEFT)
        hbox6.Add(self.optimizer_group_file_window,flag=wx.ALIGN_LEFT)

        hbox7.Add(self.run_optimizer_button,flag=wx.ALIGN_CENTER_HORIZONTAL)#,border=8)

        hbox8.Add(self.cancel_optimizer_button,flag=wx.ALIGN_CENTER_HORIZONTAL)#,border=8)

        vbox.AddSpacer(30)
        vbox.Add(hbox1a, flag=wx.ALIGN_CENTER_HORIZONTAL)#, border=10)
        vbox.AddSpacer(30)
        vbox.Add(hbox1b, flag=wx.ALIGN_CENTER_HORIZONTAL)#, border=10)
        vbox.AddSpacer(30)
        vbox.Add(hbox2, flag=wx.ALIGN_CENTER_HORIZONTAL)#, border=10)
        vbox.Add(hbox3, flag=wx.ALIGN_CENTER_HORIZONTAL)#, border=10)
        vbox.Add(hbox4, flag=wx.ALIGN_CENTER_HORIZONTAL)#, border=10)
        vbox.Add(hbox4a, flag=wx.ALIGN_CENTER_HORIZONTAL)#, border=10)
        vbox.Add(hbox5, flag=wx.ALIGN_CENTER_HORIZONTAL)#, border=10)
        vbox.Add(hbox6, flag=wx.ALIGN_CENTER_HORIZONTAL)#, border=10)
        vbox.AddSpacer(10)
        vbox.Add(hbox7, flag=wx.ALIGN_CENTER_HORIZONTAL)#, border=10)
        vbox.AddSpacer(10)
        vbox.Add(hbox8, flag=wx.ALIGN_CENTER_HORIZONTAL)#, border=10)
        vbox.AddSpacer(30)

        box.AddSpacer(30)
        box.AddSpacer(vbox)
        box.AddSpacer(30)
        
        self.panel.SetSizer(box)
        box.Fit(self)
        
        self.Show()
        self.Centre()


    def on_cancel_optimizer_button (self,event):
        self.Destroy()

    def on_check_button(self,event):
        S1=self.text_logger.GetValue()
        func=S1.split('\n')
        study_sample_n,test_group_n,max_group_int_sigma_uT,max_group_int_sigma_perc,max_sample_accuracy_uT,max_sample_accuracy_perc=10,10.,0.1,0.1,1,0.1
        functions=[]
        OK=True
        for f in func:
            try:
                exec f
            except:
                OK=False
                #  message dialog
                dlg1 = wx.MessageDialog(self, message="Error in function line %i"%(func.index(f)) ,style=wx.OK)
                result = dlg1.ShowModal()
                #if result == wx.ID_OK:
                #    d.Destroy()
        if OK:
            self.check_status.SetValue("PASS")
        else:
            self.check_status.SetValue("FAIL")

    def on_change_function (self,event):
            self.check_status.SetValue("")
         


    #def on_make_new_optimizer_group_file(self,event):
    def on_open_existing_optimizer_group_file(self,event):
        
        dirname=self.WD 
            
        dlg = wx.FileDialog(self, "Choose a test groups file", dirname, "", "*.*", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            self.optimizer_group_file_path=dlg.GetPath()
        ignore_n=1
        self.optimizer_group_file_window.SetValue(self.optimizer_group_file_path)
            
    def on_run_optimizer_button( self,event):
        if self.optimizer_group_file_window.GetValue() != "" and self.check_status.GetValue()=="PASS":
            beta_start=float(self.beta_start_window.GetValue())
            beta_end=float(self.beta_end_window.GetValue())
            beta_step=float(self.beta_step_window.GetValue())
            
            frac_start=float(self.frac_start_window.GetValue())
            frac_end=float(self.frac_end_window.GetValue())
            frac_step=float(self.frac_step_window.GetValue())

            optimizer_function_file=open(self.WD+"/consistency_test/consistency_test_functions.txt",'w')
            TEXT=self.text_logger.GetValue()
            optimizer_function_file.write(TEXT)
            optimizer_function_file.close()

            gframe=wx.BusyInfo("Running Thellier Consistency Test\n It may take a while ....", self)

            optimizer_functions_path="/consistency_test/consistency_test_functions.txt"
            criteria_fixed_paremeters_file="/consistency_test/pmag_fixed_criteria.txt"
            
            beta_range=arange(beta_start,beta_end,beta_step)
            frac_range=arange(frac_start,frac_end,beta_step)
            #try:
            thellier_consistency_test.Thellier_consistency_test(self.WD, self.Data,self.Data_hierarchy,criteria_fixed_paremeters_file,self.optimizer_group_file_path,optimizer_functions_path,beta_range,frac_range)
            #except:
            #    dlg1 = wx.MessageDialog(self,caption="Error:", message="Optimizer finished with Errors" ,style=wx.OK)
                
            #tmp.Thellier_optimizer(self.WD, self.Data,self.optimizer_group_file_path,optimizer_functions_path,beta_range,frac_range)

##            optimizer_output=open(self.WD+"/optimizer/thellier_optimizer.log",'w')
##
##            Command_line=["thellier_optimizer_2d.py","-WD",self.WD,"-optimize_by_list",self.optimizer_group_file_path,\
##                                 "-optimization_functions","/optimizer/optimizer_functions.txt"\
##                                 ,"-beta_range","%.2f,%.2f,%.2f"%(beta_start,beta_end,beta_step),"-f_range","%.2f,%.2f,%.2f"%(frac_start,frac_end,frac_step)]
##            try:
##                subprocess.check_call(Command_line,stdout=optimizer_output)
##                dlg1 = wx.MessageDialog(self,caption="Message:", message="Optimizer finished sucsessfuly\nCheck folder optimizer in working directory" ,style=wx.OK|wx.ICON_INFORMATION)
##                
##            except:
##                dlg1 = wx.MessageDialog(self,caption="Error:", message="Optimizer finished with Errors" ,style=wx.OK)
            

            dlg1 = wx.MessageDialog(self,caption="Message:", message="Consistency Test finished sucsessfuly\nCheck folder consistency_test in working directory" ,style=wx.OK|wx.ICON_INFORMATION)
            dlg1.ShowModal()
            dlg1.Destroy()
            gframe.Destroy()
        

#--------------------------------------------------------------


            
#--------------------------------------------------------------    
# Ploting  dialog
#--------------------------------------------------------------

class Plot_Dialog(wx.Dialog):

    def __init__(self,parent,WD,Data,Data_info):
        super(Plot_Dialog, self).__init__(parent, title="plot paleointensity data")
        self.InitUI()
        #self.SetSize((250, 200))

    def InitUI(self):


        pnl1 = wx.Panel(self)

        vbox = wx.BoxSizer(wx.VERTICAL)

        bSizer1 = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "Age axis" ), wx.HORIZONTAL )
        
        window_list_commands=["age_min","age_max",]
        for key in window_list_commands:
            command="self.set_plot_%s=wx.TextCtrl(pnl1,style=wx.TE_CENTER,size=(50,20))"%key
            exec command
        self.set_x_axis_auto=wx.CheckBox(pnl1, -1, '', (50, 50))
        self.set_x_axis_auto.SetValue(True)

        self.set_plot_year = wx.RadioButton(pnl1, -1, 'timescale = date (year)', (10, 10), style=wx.RB_GROUP)
        self.set_plot_BP = wx.RadioButton(pnl1, -1, 'timescale = BP ', (10, 30))
        self.set_plot_year.SetValue(True)
        
        Plot_age_window = wx.GridSizer(2, 5, 12, 12)
        Plot_age_window.AddMany( [(wx.StaticText(pnl1,label="",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="",style=wx.TE_CENTER), wx.EXPAND),                                  
            (wx.StaticText(pnl1,label="auto scale",style=wx.TE_CENTER), wx.EXPAND),                                  
            (wx.StaticText(pnl1,label="age max",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="age min",style=wx.TE_CENTER), wx.EXPAND),
            (self.set_plot_year),
            (self.set_plot_BP),                                  
            (self.set_x_axis_auto),
            (self.set_plot_age_min),
            (self.set_plot_age_max)])
                                           
        bSizer1.Add( Plot_age_window, 0, wx.ALIGN_LEFT|wx.ALL, 5 )

        #-----------        


        bSizer2 = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "Intensity axis" ), wx.HORIZONTAL )
        
        window_list_commands=["intensity_min","intensity_max"]
        for key in window_list_commands:
            command="self.set_plot_%s=wx.TextCtrl(pnl1,style=wx.TE_CENTER,size=(50,20))"%key
            exec command
        self.set_y_axis_auto=wx.CheckBox(pnl1, -1, '', (50, 50))
        self.set_plot_B = wx.RadioButton(pnl1, -1, 'B (microT)', (10, 10), style=wx.RB_GROUP)
        self.set_plot_VADM = wx.RadioButton(pnl1, -1, 'VADM (ZAm^2)', (10, 30))

        self.set_y_axis_auto.SetValue(True)
        self.set_plot_VADM.SetValue(True)
        
        Plot_intensity_window = wx.GridSizer(2, 5, 12, 12)
        Plot_intensity_window.AddMany( [(wx.StaticText(pnl1,label="",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="auto scale",style=wx.TE_CENTER), wx.EXPAND),                                        
            (wx.StaticText(pnl1,label="min value",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="max value",style=wx.TE_CENTER), wx.EXPAND),
            (self.set_plot_B),
            (self.set_plot_VADM),
            (self.set_y_axis_auto),                        
            (self.set_plot_intensity_min),
            (self.set_plot_intensity_max)])
                                           
        bSizer2.Add( Plot_intensity_window, 0, wx.ALIGN_LEFT|wx.ALL, 5 )

        #-----------  



        bSizer3 = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "more plot options" ), wx.HORIZONTAL )
        
        self.show_samples_ID=wx.CheckBox(pnl1, -1, '', (50, 50))
        self.show_x_error_bar=wx.CheckBox(pnl1, -1, '', (50, 50))
        self.show_y_error_bar=wx.CheckBox(pnl1, -1, '', (50, 50))
        
        self.show_samples_ID.SetValue(True)
        self.show_x_error_bar.SetValue(True)
        self.show_y_error_bar.SetValue(True)

        bsizer_3_window = wx.GridSizer(2, 3, 12, 12)
        bsizer_3_window.AddMany( [(wx.StaticText(pnl1,label="show sample labels",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="show x error bars",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="show y error bars",style=wx.TE_CENTER), wx.EXPAND),
            (self.show_samples_ID),
            (self.show_x_error_bar),                                  
            (self.show_y_error_bar)])
                                           
        bSizer3.Add( bsizer_3_window, 0, wx.ALIGN_LEFT|wx.ALL, 5 )

        #-----------  




        bSizer4 = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "Location map" ), wx.HORIZONTAL )
        
        self.show_map=wx.CheckBox(pnl1, -1, '', (50, 50))
        self.show_map.SetValue(False)
        self.set_map_autoscale=wx.CheckBox(pnl1, -1, '', (50, 50))
        self.set_map_autoscale.SetValue(True)

        window_list_commands=["lat_min","lat_max","lat_grid","lon_min","lon_max","lon_grid"]
        for key in window_list_commands:
            command="self.set_map_%s=wx.TextCtrl(pnl1,style=wx.TE_CENTER,size=(50,20))"%key
            exec command
        bsizer_4_window = wx.GridSizer(2, 8, 12, 12)

        bsizer_4_window.AddMany( [(wx.StaticText(pnl1,label="show location map",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="auto scale",style=wx.TE_CENTER), wx.EXPAND),                      
            (wx.StaticText(pnl1,label="lat min",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="lat max",style=wx.TE_CENTER), wx.EXPAND),                                        
            (wx.StaticText(pnl1,label="lat grid",style=wx.TE_CENTER), wx.EXPAND),                                        
            (wx.StaticText(pnl1,label="lon min",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="lon max",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="lon grid",style=wx.TE_CENTER), wx.EXPAND),
            (self.show_map),
            (self.set_map_autoscale),
            (self.set_map_lat_min),
            (self.set_map_lat_max),                        
            (self.set_map_lat_grid),                        
            (self.set_map_lon_min),
            (self.set_map_lon_max),
            (self.set_map_lon_grid)])

        
                                           
        bSizer4.Add( bsizer_4_window, 0, wx.ALIGN_LEFT|wx.ALL, 5 )

        #-----------  


        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.okButton = wx.Button(pnl1, wx.ID_OK, "&OK")
        self.cancelButton = wx.Button(pnl1, wx.ID_CANCEL, '&Cancel')
        hbox2.Add(self.okButton)
        hbox2.Add(self.cancelButton )
        #self.okButton.Bind(wx.EVT_BUTTON, self.OnOK)
        #-----------  

        
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

        vbox.Add(hbox2, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(20)
                    
        pnl1.SetSizer(vbox)
        vbox.Fit(self)
        

#--------------------------------------------------------------    
# Show a logfile erros
#--------------------------------------------------------------

class MyLogFileErrors(wx.Frame):
    """"""
 
    #----------------------------------------------------------------------
    def __init__(self,title,file_path):
        wx.Frame.__init__(self, parent=None,size=(1000,500))
        
        self.panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.text_log = wx.TextCtrl(self.panel, id=-1, style=wx.TE_MULTILINE | wx.TE_READONLY  | wx.HSCROLL)
        self.sizer.Add(self.text_log, 1, wx.EXPAND)

        fin =open(file_path,'rU')
        for line in fin.readlines():
            if "-E-" in line :
                self.text_log.SetDefaultStyle(wx.TextAttr(wx.RED))
                self.text_log.AppendText(line)
            if "-W-" in line:
                self.text_log.SetDefaultStyle(wx.TextAttr(wx.BLACK))
                self.text_log.AppendText(line)
        fin.close()
        #sizer.Fit(self)
        self.panel.SetSizer(self.sizer)



#--------------------------------------------------------------    
# MagIC model builder
#--------------------------------------------------------------


class MagIC_model_builder(wx.Frame):
    """"""
 
    #----------------------------------------------------------------------
    def __init__(self,WD,Data,Data_hierarchy):
        wx.Frame.__init__(self, parent=None)
        self.panel = wx.Panel(self)
        self.er_specimens_header=['er_citation_names','er_specimen_name','er_sample_name','er_site_name','er_location_name','specimen_class','specimen_lithology','specimen_type']
        self.er_samples_header=['er_citation_names','er_sample_name','er_site_name','er_location_name','sample_class','sample_lithology','sample_type','sample_lat','sample_lon']
        self.er_sites_header=['er_citation_names','er_site_name','er_location_name','site_class','site_lithology','site_type','site_definition','site_lon','site_lat']
        self.er_locations_header=['er_citation_names','er_location_name','location_begin_lon','location_end_lon','location_begin_lat','location_end_lat','location_type']
        self.er_ages_header=['er_citation_names','er_site_name','er_location_name','age_description','magic_method_codes','age','age_unit']
        self.WD=WD
        self.Data,self.Data_hierarchy=Data,Data_hierarchy
        self.read_MagIC_info()
        self.SetTitle("Choose header for each MagIC Table" )
        self.InitUI()

    def InitUI(self):

        er_specimens_optional_header=['er_specimen_alternatives','er_expedition_name','er_formation_name','er_member_name',\
                                      'specimen_texture','specimen_alteration','specimen_alteration_type',\
                                      'specimen_elevation','specimen_height','specimen_core_depth','specimen_composite_depth','specimen_azimuth','specimen_dip',\
                                      'specimen_volume','specimen_weight','specimen_density','specimen_size','specimen_shape','specimen_igsn','specimen_description',\
                                      'magic_method_codes','er_scientist_mail_names']
        er_samples_optional_header=['sample_elevation','er_scientist_mail_names','magic_method_codes','sample_bed_dip','sample_bed_dip_direction','sample_dip',\
                                    'sample_azimuth','sample_declination_correction','sample_orientation_flag','sample_time_zone','sample_date','sample_height',\
                                    'sample_location_precision','sample_location_geoid','sample_composite_depth','sample_core_depth','sample_cooling_rate',\
                                    'er_sample_alternatives','sample_description','er_member_name','er_expedition_name','er_expedition_name','sample_alteration_type',\
                                    'sample_alteration','sample_texture','sample_igsn']

        er_sites_optional_header=['site_location_precision','er_scientist_mail_names','magic_method_codes','site_bed_dip','site_bed_dip_direction','site_height',\
                                  'site_elevation','site_location_geoid','site_composite_depth','site_core_depth','site_cooling_rate','site_description','er_member_name',\
                                  'er_site_alternatives','er_expedition_name','er_formation_name','site_igsn']
                                
          
        er_locations_optional_header=['continent_ocean','location_geoid','location_precision','location_end_elevation','location_begin_elevation','ocean_sea','er_scientist_mail_names',\
                                      'location_lithology','country','region','village_city','plate_block','terrane','geological_province_section','tectonic_setting',\
                                      'location_class','location_description','location_url','er_location_alternatives']

          
        er_ages_optional_header=['er_timescale_citation_names','age_range_low','age_range_high','age_sigma','age_culture_name','oxygen_stage','astronomical_stage','magnetic_reversal_chron',\
                                 'er_sample_name','er_specimen_name','er_fossil_name','er_mineral_name','tiepoint_name','tiepoint_height','tiepoint_height_sigma',\
                                 'tiepoint_elevation','tiepoint_type','timescale_eon','timescale_era','timescale_period','timescale_epoch',\
                                 'timescale_stage','biostrat_zone','conodont_zone','er_formation_name','er_expedition_name','tiepoint_alternatives',\
                                 'er_member_name']

        if len(self.data_er_specimens.keys())>0:
            for key in self.data_er_specimens[self.data_er_specimens.keys()[0]].keys():
                if key not in self.er_specimens_header:
                    self.er_specimens_header.append(key)

        if len(self.data_er_samples.keys()) >0:
            for key in self.data_er_samples[self.data_er_samples.keys()[0]].keys():
                if key not in self.er_samples_header:
                    self.er_samples_header.append(key)

        if len(self.data_er_sites.keys()) >0:
            for key in self.data_er_sites[self.data_er_sites.keys()[0]].keys():
                if key not in self.er_sites_header:
                    self.er_sites_header.append(key)

        if len(self.data_er_locations.keys()) >0:
            for key in self.data_er_locations[self.data_er_locations.keys()[0]].keys():
                if key not in self.er_locations_header:
                    self.er_locations_header.append(key)

        if len(self.data_er_ages.keys())>0:
            #print self.data_er_ages.keys()
            for key in self.data_er_ages[self.data_er_ages.keys()[0]].keys():
                if key not in self.er_ages_header:
                    self.er_ages_header.append(key)
                  
        
        pnl1 = self.panel

        table_list=["er_specimens","er_samples","er_sites","er_locations","er_ages"]
        #table_list=["er_specimens"]

        for table in table_list:
          N=table_list.index(table)
          command="bSizer%i = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, '%s' ), wx.VERTICAL )"%(N,table)
          exec command
          command="self.%s_info = wx.TextCtrl(self.panel, id=-1, size=(200,250), style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)"%table
          exec command
          command = "self.%s_info_options = wx.ListBox(choices=%s_optional_header, id=-1,name='listBox1', parent=self.panel, size=wx.Size(200, 250), style=0)"%(table,table)
          exec command
          command="self.%s_info_add =  wx.Button(self.panel, id=-1, label='add')"%table
          exec command
          command="self.Bind(wx.EVT_BUTTON, self.on_%s_add_button, self.%s_info_add)"%(table,table)
          exec command
          command="self.%s_info_remove =  wx.Button(self.panel, id=-1, label='remove')"%table
          exec command
          command="self.Bind(wx.EVT_BUTTON, self.on_%s_remove_button, self.%s_info_remove)"%(table,table)
          exec command
        
                
        #------
          command="bSizer%i.Add(wx.StaticText(pnl1,label='%s header list:'),wx.ALIGN_TOP)"%(N,table)
          exec command
          command="bSizer%i.Add(self.%s_info,wx.ALIGN_TOP)"%(N,table)
          exec command
          command="bSizer%i.Add(wx.StaticText(pnl1,label='%s optional:'),wx.ALIGN_TOP)"%(N,table)
          exec command
          command="bSizer%i.Add(self.%s_info_options,wx.ALIGN_TOP)"%(N,table)
          exec command
          command="bSizer%i.Add(self.%s_info_add,wx.ALIGN_TOP)"%(N,table)
          exec command
          command="bSizer%i.Add(self.%s_info_remove,wx.ALIGN_TOP)"%(N,table)
          exec command

          
          self.update_text_box(table)
          
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        self.okButton = wx.Button(self.panel, wx.ID_OK, "&OK")
        self.Bind(wx.EVT_BUTTON, self.on_okButton, self.okButton)

        self.cancelButton = wx.Button(self.panel, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)

        hbox1.Add(self.okButton)
        hbox1.Add(self.cancelButton )

        #------
        vbox=wx.BoxSizer(wx.VERTICAL)
        
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.AddSpacer(20)
        hbox.Add(bSizer0, flag=wx.ALIGN_LEFT)
        hbox.AddSpacer(20)
        hbox.Add(bSizer1, flag=wx.ALIGN_LEFT)
        hbox.AddSpacer(20)
        hbox.Add(bSizer2, flag=wx.ALIGN_LEFT)
        hbox.AddSpacer(20)
        hbox.Add(bSizer3, flag=wx.ALIGN_LEFT)
        hbox.AddSpacer(20)
        hbox.Add(bSizer4, flag=wx.ALIGN_LEFT)
        hbox.AddSpacer(20)

        vbox.AddSpacer(20)
        vbox.Add(hbox)
        vbox.AddSpacer(20)
        vbox.Add(hbox1,flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(20)
        
        self.panel.SetSizer(vbox)
        vbox.Fit(self)
        self.Show()
        self.Centre()


    def update_text_box(self,table):
        TEXT=""
        command="keys=self.%s_header"%table
        exec command
        for key in keys:
          TEXT=TEXT+key+"\n"
        TEXT=TEXT[:-1]
        commad="self.%s_info.SetValue('')"%table
        exec command
        command="self.%s_info.SetValue(TEXT)"%table
        exec command

    def on_er_specimens_add_button(self, event):
        selName = str(self.er_specimens_info_options.GetStringSelection())
        if selName not in self.er_specimens_header:
          self.er_specimens_header.append(selName)
        self.update_text_box('er_specimens')
          
    def on_er_samples_add_button(self, event):
        selName = self.er_samples_info_options.GetStringSelection()
        if selName not in self.er_samples_header:
          self.er_samples_header.append(selName)
        self.update_text_box('er_samples')
        
    def on_er_sites_add_button(self, event):
        selName = self.er_sites_info_options.GetStringSelection()
        if selName not in self.er_sites_header:
          self.er_sites_header.append(selName)
        self.update_text_box('er_sites')
        
    def on_er_locations_add_button(self, event):
        selName = self.er_locations_info_options.GetStringSelection()
        if selName not in self.er_locations_header:
          self.er_locations_header.append(selName)
        self.update_text_box('er_locations')
        
    def on_er_ages_add_button(self, event):
        selName = self.er_ages_info_options.GetStringSelection()
        if selName not in self.er_ages_header:
          self.er_ages_header.append(selName)
        self.update_text_box('er_ages')

    def on_er_specimens_remove_button(self, event):
        selName = str(self.er_specimens_info_options.GetStringSelection())
        if selName  in self.er_specimens_header:
          self.er_specimens_header.remove(selName)
        self.update_text_box('er_specimens')
          
    def on_er_samples_remove_button(self, event):
        selName = self.er_samples_info_options.GetStringSelection()
        if selName  in self.er_samples_header:
          self.er_samples_header.remove(selName)
        self.update_text_box('er_samples')
        
    def on_er_sites_remove_button(self, event):
        selName = self.er_sites_info_options.GetStringSelection()
        if selName  in self.er_sites_header:
          self.er_sites_header.remove(selName)
        self.update_text_box('er_sites')
        
    def on_er_locations_remove_button(self, event):
        selName = self.er_locations_info_options.GetStringSelection()
        if selName  in self.er_locations_header:
          self.er_locations_header.remove(selName)
        self.update_text_box('er_locations')
        
    def on_er_ages_remove_button(self, event):
        selName = self.er_ages_info_options.GetStringSelection()
        if selName  in self.er_ages_header:
          self.er_ages_header.remove(selName)
        self.update_text_box('er_ages')

    def on_okButton(self, event):
        specimens_list=self.Data.keys()

        samples_list=self.Data_hierarchy['samples'].keys()
        samples_list.sort()

        specimens_list=self.Data_hierarchy['specimens'].keys()
        specimens_list.sort()

        #---------------------------------------------
        # make er_samples.txt
        #---------------------------------------------

        #header
        er_samples_file=open(self.WD+"er_samples.txt",'w')
        er_samples_file.write("tab\ter_samples\n")
        string=""
        for key in self.er_samples_header:
          string=string+key+"\t"
        er_samples_file.write(string[:-1]+"\n")

        for sample in samples_list:
          string=""
          for key in self.er_samples_header:
            if key=="er_citation_names":
              string=string+"This study"+"\t"
            elif key=="er_sample_name":
              string=string+sample+"\t"
            # try to take lat/lon from er_sites table
            elif (key in ['er_location_name'] and sample in self.data_er_samples.keys()\
                  and "er_site_name" in self.data_er_samples[sample].keys()\
                  and self.data_er_samples[sample]['er_site_name'] in self.data_er_sites.keys()\
                  and key in self.data_er_sites[self.data_er_samples[sample]['er_site_name']].keys()):
              string=string+self.data_er_sites[self.data_er_samples[sample]['er_site_name']][key]+"\t"

            elif (key in ['sample_lon','sample_lat'] and sample in self.data_er_samples.keys()\
                  and "er_site_name" in self.data_er_samples[sample].keys()\
                  and self.data_er_samples[sample]['er_site_name'] in self.data_er_sites.keys()\
                  and "site_"+key.split("_")[1] in self.data_er_sites[self.data_er_samples[sample]['er_site_name']].keys()):
              string=string+self.data_er_sites[self.data_er_samples[sample]['er_site_name']]["site_"+key.split("_")[1]]+"\t"


##            elif (key in ['sample_lon','sample_lat'] and sample in self.data_er_samples.keys()\
##                  and "er_site_name" in self.data_er_samples[sample].keys()\
##                  and self.data_er_samples[sample]['er_site_name'] in self.data_er_sites.keys()\
##                  and key in self.data_er_sites[self.data_er_samples[sample]['er_site_name']].keys()):
##              string=string+self.data_er_sites[self.data_er_samples[sample]['er_site_name']][key]+"\t"

            
            # take information from the existing er_samples table 
            elif sample in self.data_er_samples.keys() and key in self.data_er_samples[sample].keys() and self.data_er_samples[sample][key]!="":
                string=string+self.data_er_samples[sample][key]+"\t"
            else:
              string=string+"\t"
          er_samples_file.write(string[:-1]+"\n")

        #---------------------------------------------
        # make er_specimens.txt
        #---------------------------------------------

        #header
        er_specimens_file=open(self.WD+"er_specimens.txt",'w')
        er_specimens_file.write("tab\ter_specimens\n")
        string=""
        for key in self.er_specimens_header:
          string=string+key+"\t"
        er_specimens_file.write(string[:-1]+"\n")

        #data
        for specimen in specimens_list:
          sample=self.Data_hierarchy['specimens'][specimen]
          string=""
          for key in self.er_specimens_header:
            if key=="er_citation_names":
              string=string+"This study"+"\t"
            elif key=="er_specimen_name":
              string=string+specimen+"\t"
            elif key=="er_sample_name":
              string=string+self.Data_hierarchy['specimens'][specimen]+"\t"
            # take 'er_location_name','er_site_name' from er_sample table
            elif (key in ['er_location_name','er_site_name'] and sample in self.data_er_samples.keys() \
                 and  key in self.data_er_samples[sample] and self.data_er_samples[sample][key]!=""):
              string=string+self.data_er_samples[sample][key]+"\t"
            # take 'specimen_class','specimen_lithology','specimen_type' from er_sample table
            elif key in ['specimen_class','specimen_lithology','specimen_type']:
              sample_key="sample_"+key.split('specimen_')[1]
              if (sample in self.data_er_samples.keys() and sample_key in self.data_er_samples[sample] and self.data_er_samples[sample][sample_key]!=""):
                string=string+self.data_er_samples[sample][sample_key]+"\t"
            # take information from the existing er_samples table             
            elif specimen in self.data_er_specimens.keys() and key in self.data_er_specimens[specimen].keys() and self.data_er_specimens[specimen][key]!="":
                string=string+specimen+self.data_er_specimens[specimen][key]+"\t"
            else:
              string=string+"\t"
          er_specimens_file.write(string[:-1]+"\n")
          

        #---------------------------------------------
        # make er_sites.txt
        #---------------------------------------------

        #header
        er_sites_file=open(self.WD+"er_sites.txt",'w')
        er_sites_file.write("tab\ter_sites\n")
        string=""
        for key in self.er_sites_header:
          string=string+key+"\t"
        er_sites_file.write(string[:-1]+"\n")

        #data
        sites_list=self.data_er_sites.keys()
        for sample in self.data_er_samples.keys():
          if "er_site_name" in self.data_er_samples[sample].keys() and self.data_er_samples[sample]["er_site_name"] not in sites_list:
            sites_list.append(self.data_er_samples[sample]["er_site_name"])
        sites_list.sort()        
        for site in sites_list:
          string=""
          for key in self.er_sites_header:
            if key=="er_citation_names":
              string=string+"This study"+"\t"
            elif key=="er_site_name":
              string=string+site+"\t"
            # take information from the existing er_samples table             
            elif (site in self.data_er_sites.keys() and key in self.data_er_sites[site].keys() and self.data_er_sites[site][key]!=""):
                string=string+self.data_er_sites[site][key]+"\t"
            else:
              string=string+"\t"
          er_sites_file.write(string[:-1]+"\n")

        #---------------------------------------------
        # make er_locations.txt
        #---------------------------------------------

        #header
        er_locations_file=open(self.WD+"er_locations.txt",'w')
        er_locations_file.write("tab\ter_locations\n")
        string=""
        for key in self.er_locations_header:
          string=string+key+"\t"
        er_locations_file.write(string[:-1]+"\n")

        #data
        locations_list=self.data_er_locations.keys()
        for site in self.data_er_sites.keys():
          if "er_location_name" in self.data_er_sites[site].keys() and self.data_er_sites[site]["er_location_name"] not in locations_list:
            locations_list.append(self.data_er_sites[site]["er_location_name"])
        locations_list.sort()        
        for location in locations_list:
          string=""
          for key in self.er_locations_header:
            if key=="er_citation_names":
              string=string+"This study"+"\t"
            elif key=="er_location_name":
              string=string+location+"\t"
            # take information from the existing er_samples table             
            elif (location in self.data_er_locations.keys() and key in self.data_er_locations[location].keys() and self.data_er_locations[location][key]!=""):
                string=string+self.data_er_locations[location][key]+"\t"
            else:
              string=string+"\t"
          er_locations_file.write(string[:-1]+"\n")



        #---------------------------------------------
        # make er_ages.txt
        #---------------------------------------------

        #header
        er_ages_file=open(self.WD+"er_ages.txt",'w')
        er_ages_file.write("tab\ter_ages\n")
        string=""
        for key in self.er_ages_header:
          string=string+key+"\t"
        er_ages_file.write(string[:-1]+"\n")

        #data
        sites_list=self.data_er_sites.keys()
        sites_list.sort()        
        for site in sites_list:
          string=""
          for key in self.er_ages_header:
            if key=="er_site_name":
              string=string+site+"\t"

            elif key=="er_citation_names":
              string=string+"This study"+"\t"

            elif (key in ['er_location_name'] and site in self.data_er_sites.keys() \
                 and  key in self.data_er_sites[site] and self.data_er_sites[site][key]!=""):
              string=string+self.data_er_sites[site][key]+"\t"
              
            # take information from the existing er_samples table             
            elif (site in self.data_er_ages.keys() and key in self.data_er_ages[site].keys() and self.data_er_ages[site][key]!=""):
                string=string+self.data_er_ages[site][key]+"\t"
            else:
              string=string+"\t"
          er_ages_file.write(string[:-1]+"\n")



        #-----------------------------------------------------
        # Fix magic_measurement with sites and locations  
        #-----------------------------------------------------

        f_old=open(self.WD+"/magic_measurements.txt",'rU')
        f_new=open(self.WD+"/magic_measurements.new.tmp.txt",'w')
             
        line=f_old.readline()
        f_new.write(line)

        line=f_old.readline()
        header=line.strip("\n").split('\t')
        f_new.write(line)

        for line in f_old.readlines():
            tmp_line=line.strip('\n').split('\t')
            tmp={}
            for i in range(len(header)):
                tmp[header[i]]=tmp_line[i]
            sample=tmp["er_sample_name"]
            if sample in self.data_er_samples.keys() and "er_site_name" in self.data_er_samples[sample].keys() and self.data_er_samples[sample]["er_site_name"]!="":
                tmp["er_site_name"]=self.data_er_samples[sample]["er_site_name"]
            site=tmp["er_site_name"]
            if site in self.data_er_sites.keys() and "er_location_name" in self.data_er_sites[site].keys() and self.data_er_sites[site]["er_location_name"]!="":
                tmp["er_location_name"]=self.data_er_sites[site]["er_location_name"]

            new_line=""
            for i in range(len(header)):
                new_line=new_line+tmp[header[i]]+"\t"
            #print new_line
            f_new.write(new_line[:-1]+"\n")
        f_new.close()
        os.remove(self.WD+"/magic_measurements.txt")
        os.rename(self.WD+"/magic_measurements.new.tmp.txt",self.WD+"/magic_measurements.txt")
        

                
##        #---------------------------------------------
##        # make er_locations.txt
##        #---------------------------------------------
##
##        #header
##        er_qges_file=open(self.WD+"er_ages.txt",'w')
##        er_ages_file.write("tab\ter_ages\n")
##        string=""
##        for key in self.er_ages_header:
##          string=string+key+"\t"
##        er_ages_file.write(string[:-1]+"\n")
##
##        #data
##        ages_list=self.data_er_ages.keys()
##        ages_list.sort()        
##        for age in ages_list:
##          string=""
##          for key in self.er_locations_header:
##            if key=="er_citation_names":
##              string=string+"This study"+"\t"
##            elif key=="er_location_name":
##              string=string+location+"\t"
##            elif (location in self.data_er_locations.keys() and key in self.data_er_locations[location].keys() and self.data_er_locations[location][key]!=""):
##                string=string+self.data_er_locations[location][key]+"\t"
##            else:
##              string=string+"\t"
##          er_locations_file.write(string[:-1]+"\n")


        
        dlg1 = wx.MessageDialog(self,caption="Message:", message="New MagIC model is saved. deleting All previous interpretations." ,style=wx.OK|wx.ICON_INFORMATION)
        dlg1.ShowModal()
        dlg1.Destroy()
        self.Destroy()

    def on_cancelButton(self,event):
        self.Destroy()
      
    def read_magic_file(self,path,sort_by_this_name):
        DATA={}
        fin=open(path,'rU')
        fin.readline()
        line=fin.readline()
        header=line.strip('\n').split('\t')
        counter=0
        for line in fin.readlines():
            tmp_data={}
            tmp_line=line.strip('\n').split('\t')
            for i in range(len(tmp_line)):
                tmp_data[header[i]]=tmp_line[i]
            if sort_by_this_name=="by_line_number":
              DATA[counter]=tmp_data
              counter+=1
            else:
              DATA[tmp_data[sort_by_this_name]]=tmp_data
        fin.close()        
        return(DATA)


    def read_MagIC_info(self):
        Data_info={}
        #print "-I- read existing MagIC model files"
        self.data_er_specimens,self.data_er_samples,self.data_er_sites,self.data_er_locations,self.data_er_ages={},{},{},{},{}

        try:
            self.data_er_specimens=self.read_magic_file(self.WD+"/er_specimens.txt",'er_specimen_name')
        except:
            #self.GUI_log.write ("-W- Cant find er_sample.txt in project directory")
            pass
        try:
            self.data_er_samples=self.read_magic_file(self.WD+"/er_samples.txt",'er_sample_name')
        except:
            #self.GUI_log.write ("-W- Cant find er_sample.txt in project directory")
            pass
        try:
            self.data_er_sites=self.read_magic_file(self.WD+"/er_sites.txt",'er_site_name')
        except:
            pass
        try:
            self.data_er_locations=self.read_magic_file(self.WD+"/er_locations.txt",'er_location_name')
        except:
            #self.GUI_log.write ("-W- Cant find er_sites.txt in project directory")
            pass
        try:
            self.data_er_ages=self.read_magic_file(self.WD+"/er_ages.txt","er_site_name")
        except:
            try:
                self.data_er_ages=self.read_magic_file(self.WD+"/er_ages.txt","er_sample_name")
            except:
                pass

    
##        Data_info["er_samples"]=data_er_samples
##        Data_info["er_sites"]=data_er_sites
##        Data_info["er_ages"]=data_er_ages
##        
##        
##        return(Data_info)

##    def get_data(self):
##
##
##
##
##      #------------------------------------------------
##      # Read magic measurement file and sort to blocks
##      #------------------------------------------------
##
##      # All data information is stored in Data[secimen]={}
##      Data={}
##      Data_hierarchy={}
##      Data_hierarchy['samples']={}
##      Data_hierarchy['specimens']={}
##      self.magic_file=self.WD + "/magic_measurements.txt"
##      meas_data,file_type=pmag.magic_read(self.magic_file)
##      
##      # get list of unique specimen names
##      
##      CurrRec=[]
##      print "get sids"
##
##      sids=pmag.get_specs(meas_data) # samples ID's
##      print "done get sids"
##
##      print "initialize blocks"
##      
##      for s in sids:
##
##          if s not in Data.keys():
##              Data[s]={}
##              Data[s]['datablock']=[]
##              Data[s]['trmblock']=[]
##              Data[s]['zijdblock']=[]
##
##
##      print "done initialize blocks"
##
##      print "sorting meas data"
##          
##      for rec in meas_data:
##          s=rec["er_specimen_name"]
##          sample=rec["er_sample_name"]
##          if "magic_method_codes" not in rec.keys():
##              rec["magic_method_codes"]=""
##          #methods=rec["magic_method_codes"].split(":")
##          if "LP-PI-TRM" in rec["magic_method_codes"]:
##              Data[s]['datablock'].append(rec)
##              if "LT-PTRM-I" in rec["magic_method_codes"] and 'LP-TRM' not in rec["magic_method_codes"]:
##                  Data[s]['Thellier_dc_field_uT']=float(rec["treatment_dc_field"])
##                  Data[s]['Thellier_dc_field_phi']=float(rec['treatment_dc_field_phi'])
##                  Data[s]['Thellier_dc_field_theta']=float(rec['treatment_dc_field_theta'])
##
##          if "LP-TRM" in rec["magic_method_codes"]:
##              Data[s]['trmblock'].append(rec)
##
##          if "LP-AN-TRM" in rec["magic_method_codes"]:
##              if 'atrmblock' not in Data[s].keys():
##                Data[s]['atrmblock']=[]
##              Data[s]['atrmblock'].append(rec)
##
##
##          if "LP-AN-ARM" in rec["magic_method_codes"]:
##              if 'aarmblock' not in Data[s].keys():
##                Data[s]['aarmblock']=[]
##              Data[s]['aarmblock'].append(rec)
##
##
##          #---- Zijderveld block
##
##          EX=["LP-AN-ARM","LP-AN-TRM","LP-ARM-AFD","LP-ARM2-AFD","LP-TRM-AFD","LP-TRM","LP-TRM-TD","LP-X"] # list of excluded lab protocols
##          INC=["LT-NO","LT-T-Z"]
##          methods=rec["magic_method_codes"].split(":")
##          for i in range (len(methods)):
##               methods[i]=methods[i].strip()
##          if 'measurement_flag' not in rec.keys(): rec['measurement_flag']='g'
##          skip=1
##          for meth in methods:
##               if meth in INC:
##                   skip=0
##          for meth in EX:
##               if meth in methods:skip=1
##          if skip==0:
##             tr = float(rec["treatment_temp"])            
##
##             if "LP-PI-TRM-IZ" in methods or "LP-PI-M-IZ" in methods:  # looking for in-field first thellier or microwave data - otherwise, just ignore this
##                 ZI=0
##             else:
##                 ZI=1
##             Mkeys=['measurement_magnitude','measurement_magn_moment','measurement_magn_volume','measurement_magn_mass']
##             if tr !="":
##                 dec,inc,int = "","",""
##                 if "measurement_dec" in rec.keys() and rec["measurement_dec"] != "":
##                     dec=float(rec["measurement_dec"])
##                 if "measurement_inc" in rec.keys() and rec["measurement_inc"] != "":
##                     inc=float(rec["measurement_inc"])
##                 for key in Mkeys:
##                     if key in rec.keys() and rec[key]!="":int=float(rec[key])
##                 if 'magic_instrument_codes' not in rec.keys():rec['magic_instrument_codes']=''
##                 #datablock.append([tr,dec,inc,int,ZI,rec['measurement_flag'],rec['magic_instrument_codes']])
##                 if tr==0.: tr=273.
##                 Data[s]['zijdblock'].append([tr,dec,inc,int,ZI,rec['measurement_flag'],rec['magic_instrument_codes']])
##                 #print methods
##
##
##                 
##          if sample not in Data_hierarchy['samples'].keys():
##              Data_hierarchy['samples'][sample]=[]
##          if s not in Data_hierarchy['samples'][sample]:
##              Data_hierarchy['samples'][sample].append(s)
##
##          Data_hierarchy['specimens'][s]=sample
##
##
##          
##      print "done sorting meas data"
##                  
##      self.specimens=Data.keys()
##      self.specimens.sort()
##
##      
##      #------------------------------------------------
##      # Read anisotropy file from rmag_anisotropy.txt
##      #------------------------------------------------
##
##      #if self.WD != "":
##      rmag_anis_data=[]
##      results_anis_data=[]
##      try:
##          rmag_anis_data,file_type=self.magic_read(self.WD+'/rmag_anisotropy.txt')
##      except:
##          pass
##
##      try:
##          results_anis_data,file_type=self.magic_read(self.WD+'/rmag_results.txt')          
##      except:
##          pass
##
##          
##      for AniSpec in rmag_anis_data:
##          s=AniSpec['er_specimen_name']
##
##          if s not in Data.keys():
##              continue
##          Data[s]['AniSpec']=AniSpec
##        
##      for AniSpec in results_anis_data:
##          s=AniSpec['er_specimen_names']
##          if s not in Data.keys():
##              continue
##          if 'AniSpec' in Data[s].keys():
##              Data[s]['AniSpec'].update(AniSpec)
##                
##          
##        
##  
##      return(Data,Data_hierarchy)
    

#--------------------------------------------------------------    
# MagIC generic files conversion
#--------------------------------------------------------------


class convert_generic_files_to_MagIC(wx.Frame):
    """"""
    title = "PmagPy Thellier GUI generic file conversion"

    def __init__(self,WD):
        wx.Frame.__init__(self, None, wx.ID_ANY, self.title)
        self.panel = wx.Panel(self)
        self.max_files=10
        self.WD=WD
        self.InitUI()

    def InitUI(self):

        pnl = self.panel

        #---sizer infor ----

        TEXT1="Generic thellier GUI file is a tab-delimited file with the following headers:\n"
        TEXT2="Specimen  Treatment  Declination  Inclination  Moment\n"
        TEXT3="Treatment: XXX.Y or XXX.YY where XXX is temperature in C, and YY is treatment code. See tutorial for explenation. NRM step is 000.00\n" 
        TEXT4="Moment: In units of emu.\n"

        TEXT=TEXT1+TEXT2+TEXT3+TEXT4
        bSizer_info = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.HORIZONTAL )
        bSizer_info.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_LEFT)
            

        #---sizer 0 ----
        TEXT="File:\n Choose measurement file\n No spaces are alowd in path"
        bSizer0 = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.VERTICAL )
        bSizer0.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_TOP)
        bSizer0.AddSpacer(5)
        for i in range(self.max_files):
            command= "self.file_path_%i = wx.TextCtrl(self.panel, id=-1, size=(200,25), style=wx.TE_READONLY)"%i
            exec command
            command= "self.add_file_button_%i =  wx.Button(self.panel, id=-1, label='add',name='add_%i')"%(i,i)
            exec command
            command= "self.Bind(wx.EVT_BUTTON, self.on_add_file_button_i, self.add_file_button_%i)"%i
            #print command
            exec command            
            command="bSizer0_%i = wx.BoxSizer(wx.HORIZONTAL)"%i
            exec command
            command="bSizer0_%i.Add(wx.StaticText(pnl,label=('%i  '[:2])),wx.ALIGN_LEFT)"%(i,i+1)
            exec command
            
            command="bSizer0_%i.Add(self.file_path_%i,wx.ALIGN_LEFT)" %(i,i)
            exec command
            command="bSizer0_%i.Add(self.add_file_button_%i,wx.ALIGN_LEFT)" %(i,i)
            exec command
            command="bSizer0.Add(bSizer0_%i,wx.ALIGN_TOP)" %i
            exec command
            bSizer0.AddSpacer(5)
              
        #---sizer 1 ----

        TEXT="\n\nExperiment:"
        bSizer1 = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.VERTICAL )
        bSizer1.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_TOP)
        self.experiments_names=['IZZI','IZ','ZI','ATRM 6 positions','cooling rate','NLT']
        bSizer1.AddSpacer(5)
        for i in range(self.max_files):
            command="self.protocol_info_%i = wx.ComboBox(self.panel, -1, self.experiments_names[0], size=(100,25), choices=self.experiments_names, style=wx.CB_DROPDOWN)"%i
            #command="self.protocol_info_%i = wx.TextCtrl(self.panel, id=-1, size=(100,20), style=wx.TE_MULTILINE | wx.HSCROLL)"%i
            #print command
            exec command
            command="bSizer1.Add(self.protocol_info_%i,wx.ALIGN_TOP)"%i        
            exec command
            bSizer1.AddSpacer(5)

        #---sizer 2 ----

        TEXT="Blab:\n(microT dec inc)\nexample: 40 0 -90 "
        bSizer2 = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.VERTICAL )
        bSizer2.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_TOP)
        bSizer2.AddSpacer(5)
        for i in range(self.max_files):
            command= "self.file_info_Blab_%i = wx.TextCtrl(self.panel, id=-1, size=(40,25))"%i
            exec command
            command= "self.file_info_Blab_dec_%i = wx.TextCtrl(self.panel, id=-1, size=(40,25))"%i
            exec command
            command= "self.file_info_Blab_inc_%i = wx.TextCtrl(self.panel, id=-1, size=(40,25))"%i
            exec command          
            command="bSizer2_%i = wx.BoxSizer(wx.HORIZONTAL)"%i
            exec command
            command="bSizer2_%i.Add(self.file_info_Blab_%i ,wx.ALIGN_LEFT)" %(i,i)
            exec command
            command="bSizer2_%i.Add(self.file_info_Blab_dec_%i,wx.ALIGN_LEFT)" %(i,i)
            exec command
            command="bSizer2_%i.Add(self.file_info_Blab_inc_%i,wx.ALIGN_LEFT)" %(i,i)
            exec command
            command="bSizer2.Add(bSizer2_%i,wx.ALIGN_TOP)" %i
            exec command
            bSizer2.AddSpacer(5)


        #self.blab_info = wx.TextCtrl(self.panel, id=-1, size=(80,250), style=wx.TE_MULTILINE | wx.HSCROLL)
        #bSizer2.Add(self.blab_info,wx.ALIGN_TOP)        

        #---sizer 3 ----

        TEXT="\nUser\nname:"
        bSizer3 = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.VERTICAL )
        bSizer3.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_TOP)
        bSizer3.AddSpacer(5)
        for i in range(self.max_files):
            command= "self.file_info_user_%i = wx.TextCtrl(self.panel, id=-1, size=(60,25))"%i
            exec command
            command="bSizer3.Add(self.file_info_user_%i,wx.ALIGN_TOP)" %i
            exec command
            bSizer3.AddSpacer(5)

        #---sizer 4 ----

        TEXT="\nSample-specimen\nnaming convention:"
        bSizer4 = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.VERTICAL )
        bSizer4.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_TOP)
        self.sample_naming_conventions=['sample=specimen','no. of terminate characters','charceter delimited']
        bSizer4.AddSpacer(5)
        for i in range(self.max_files):
            command="self.sample_naming_convention_%i = wx.ComboBox(self.panel, -1, self.sample_naming_conventions[0], size=(180,25), choices=self.sample_naming_conventions, style=wx.CB_DROPDOWN)"%i
            exec command            
            command="self.sample_naming_convention_char_%i = wx.TextCtrl(self.panel, id=-1, size=(40,25))"%i
            exec command
            command="bSizer4_%i = wx.BoxSizer(wx.HORIZONTAL)"%i
            exec command
            command="bSizer4_%i.Add(self.sample_naming_convention_%i,wx.ALIGN_LEFT)" %(i,i)
            exec command
            command="bSizer4_%i.Add(self.sample_naming_convention_char_%i,wx.ALIGN_LEFT)" %(i,i)
            exec command
            command="bSizer4.Add(bSizer4_%i,wx.ALIGN_TOP)"%i        
            exec command

            bSizer4.AddSpacer(5)

        #---sizer 5 ----

        TEXT="\nSite-sample\nnaming convention:"
        bSizer5 = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.VERTICAL )
        bSizer5.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_TOP)
        self.site_naming_conventions=['site=sample','no. of terminate characters','charceter delimited']
        bSizer5.AddSpacer(5)
        for i in range(self.max_files):
            command="self.site_naming_convention_char_%i = wx.TextCtrl(self.panel, id=-1, size=(40,25))"%i
            exec command
            command="self.site_naming_convention_%i = wx.ComboBox(self.panel, -1, self.site_naming_conventions[0], size=(180,25), choices=self.site_naming_conventions, style=wx.CB_DROPDOWN)"%i
            exec command
            command="bSizer5_%i = wx.BoxSizer(wx.HORIZONTAL)"%i
            exec command
            command="bSizer5_%i.Add(self.site_naming_convention_%i,wx.ALIGN_LEFT)" %(i,i)
            exec command
            command="bSizer5_%i.Add(self.site_naming_convention_char_%i,wx.ALIGN_LEFT)" %(i,i)
            exec command
            command="bSizer5.Add(bSizer5_%i,wx.ALIGN_TOP)"%i        
            exec command
            bSizer5.AddSpacer(5)




        #------------------

        #self.add_file_button =  wx.Button(self.panel, id=-1, label='add file')
        #self.Bind(wx.EVT_BUTTON, self.on_add_file_button, self.add_file_button)

        #self.remove_file_button =  wx.Button(self.panel, id=-1, label='remove file')

                     
        self.okButton = wx.Button(self.panel, wx.ID_OK, "&OK")
        self.Bind(wx.EVT_BUTTON, self.on_okButton, self.okButton)

        self.cancelButton = wx.Button(self.panel, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)

        hbox1 = wx.BoxSizer(wx.HORIZONTAL)        
        #hbox1.Add(self.add_file_button)
        #hbox1.Add(self.remove_file_button )

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)        
        hbox2.Add(self.okButton)
        hbox2.Add(self.cancelButton )

        #------

        vbox=wx.BoxSizer(wx.VERTICAL)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.AddSpacer(5)
        hbox.Add(bSizer0, flag=wx.ALIGN_LEFT)        
        hbox.AddSpacer(5)
        hbox.Add(bSizer1, flag=wx.ALIGN_LEFT)        
        hbox.AddSpacer(5)
        hbox.Add(bSizer2, flag=wx.ALIGN_LEFT)        
        hbox.AddSpacer(5)
        hbox.Add(bSizer3, flag=wx.ALIGN_LEFT)        
        hbox.AddSpacer(5)
        hbox.Add(bSizer4, flag=wx.ALIGN_LEFT)        
        hbox.AddSpacer(5)
        hbox.Add(bSizer5, flag=wx.ALIGN_LEFT)        
        hbox.AddSpacer(5)

        #-----
        
        vbox.AddSpacer(20)
        vbox.Add(bSizer_info,flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(20)        
        vbox.Add(hbox)
        vbox.AddSpacer(20)
        vbox.Add(hbox1,flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(20)
        vbox.Add(hbox2,flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(20)
        
        self.panel.SetSizer(vbox)
        vbox.Fit(self)
        self.Show()
        self.Centre()


    def cart2dir(cart):
        """
        converts a direction to cartesian coordinates
        """
        cart=array(cart)
        rad=pi/180. # constant to convert degrees to radians
        if len(cart.shape)>1:
            Xs,Ys,Zs=cart[:,0],cart[:,1],cart[:,2]
        else: #single vector
            Xs,Ys,Zs=cart[0],cart[1],cart[2]
        Rs=sqrt(Xs**2+Ys**2+Zs**2) # calculate resultant vector length
        Decs=(arctan2(Ys,Xs)/rad)%360. # calculate declination taking care of correct quadrants (arctan2) and making modulo 360.
        try:
            Incs=arcsin(Zs/Rs)/rad # calculate inclination (converting to degrees) # 
        except:
            print 'trouble in cart2dir' # most likely division by zero somewhere
            return zeros(3)
            
        return array([Decs,Incs,Rs]).transpose() # return the directions list



    def on_add_file_button(self,event):

        dlg = wx.FileDialog(
            None,message="choose file to convert to MagIC",
            defaultDir=self.WD, 
            defaultFile="",
            style=wx.OPEN | wx.CHANGE_DIR
            )        
        if dlg.ShowModal() == wx.ID_OK:
            FILE = dlg.GetPath()
        # fin=open(FILE,'rU')
        self.file_path.AppendText(FILE+"\n")
        self.protocol_info.AppendText("IZZI"+"\n")


    def on_add_file_button_i(self,event):

        dlg = wx.FileDialog(
            None,message="choose file to convert to MagIC",
            defaultDir="./", 
            defaultFile="",
            style=wx.OPEN | wx.CHANGE_DIR
            )        
        if dlg.ShowModal() == wx.ID_OK:
            FILE = dlg.GetPath()
        # fin=open(FILE,'rU')
        button = event.GetEventObject()
        name=button.GetName()
        i=int((name).split("_")[-1])
        #print "The button's name is " + button.GetName()
        
        command="self.file_path_%i.SetValue(FILE)"%i
        exec command

        #self.file_path.AppendText(FILE)
        #self.protocol_info.AppendText("IZZI"+"\n")



    def read_generic_file(self,path):
        Data={}
        Fin=open(path,'rU')
        header=Fin.readline().strip('\n').split('\t')
        
        for line in Fin.readlines():
            tmp_data={}
            l=line.strip('\n').split('\t')
            #print l
            if len(l)<len(header):
                continue
            else:
                for i in range(len(header)):
                    tmp_data[header[i]]=l[i]
                specimen=tmp_data['Specimen']
                if specimen not in Data.keys():
                    Data[specimen]=[]
                # check dupliactes
                if len(Data[specimen]) >0:
                    if tmp_data['Treatment']==Data[specimen][-1]['Treatment']:
                        print "-W- WARNING: duplicate measurements specimen %s, Treatment %s. keeping onlt the last one"%(tmp_data['Specimen'],tmp_data['Treatment'])
                        Data[specimen].pop()
                        
                Data[specimen].append(tmp_data)
        return(Data)               

    def on_okButton(self,event):


        #-----------------------------------
        # Prepare MagIC measurement file
        #-----------------------------------

        # prepare output file
        magic_headers=['er_citation_names','er_specimen_name',"er_sample_name","er_site_name",'er_location_name','er_analyst_mail_names',\
                       "magic_instrument_codes","measurement_flag","measurement_standard","magic_experiment_name","magic_method_codes","measurement_number",'treatment_temp',"measurement_dec","measurement_inc",\
                       "measurement_magn_moment","measurement_temp","treatment_dc_field","treatment_dc_field_phi","treatment_dc_field_theta"]             

        fout=open("magic_measurements.txt",'w')        
        fout.write("tab\tmagic_measurements\n")
        header_string=""
        for i in range(len(magic_headers)):
            header_string=header_string+magic_headers[i]+"\t"
        fout.write(header_string[:-1]+"\n")

        #-----------------------------------
            
        Data={}
        header_codes=[]
        ERROR=""
        datafiles=[]
        for i in range(self.max_files):

            # read data from generic file
            datafile=""
            command="datafile=self.file_path_%i.GetValue()"%i
            exec command
            if datafile!="":
                try:
                    this_file_data= self.read_generic_file(datafile)
                except:
                    print "-E- Cant read file %s" %datafile                
            else:
                continue

                
            # get experiment
            command="experiment=self.protocol_info_%i.GetValue()"%i
            exec command

            # get Blab
            labfield=["0","-1","-1"]
            command="labfield[0]=self.file_info_Blab_%i.GetValue()"%i
            exec command
            command="labfield[1]=self.file_info_Blab_dec_%i.GetValue()"%i
            exec command
            command="labfield[2]=self.file_info_Blab_inc_%i.GetValue()"%i
            exec command
            
            # get User_name
            user_name=""
            command="user_name=self.file_info_user_%i.GetValue()"%i
            exec command
            
            # get sample-specimen naming convention

            sample_naming_convenstion=["",""]
            command="sample_naming_convenstion[0]=self.sample_naming_convention_%i.GetValue()"%i
            exec command
            command="sample_naming_convenstion[1]=self.sample_naming_convention_char_%i.GetValue()"%i
            exec command
            
            # get site-sample naming convention

            site_naming_convenstion=["",""]
            command="site_naming_convenstion[0]=self.site_naming_convention_%i.GetValue()"%i
            exec command
            command="site_naming_convenstion[1]=self.site_naming_convention_char_%i.GetValue()"%i
            exec command

            #-------------------------------
            Magic_lab_protocols={}
            Magic_lab_protocols['IZZI'] = "LP-PI-TRM:LP-PI-BT-IZZI"
            Magic_lab_protocols['IZ'] = "LP-PI-TRM:LP-PI-TRM-IZ"
            Magic_lab_protocols['ZI'] = "LP-PI-TRM:LP-PI-TRM-ZI"
            Magic_lab_protocols['ATRM 6 positions'] = "LP-AN-TRM" # LT-T-I:
            Magic_lab_protocols['cooling rate'] = "LP-CR-TRM" # LT-T-I:
            Magic_lab_protocols['NLT'] = "LP-TRM" # LT-T-I:
            #------------------------------

            for specimen in this_file_data.keys():
                measurement_running_number=0
                this_specimen_teratments=[]
                for meas_line in this_file_data[specimen]:
                    MagRec={}
                    #
                    MagRec["er_specimen_name"]=meas_line['Specimen']
                    MagRec['er_citation_names']="This study"
                    MagRec["er_sample_name"]=self.get_sample_name(MagRec["er_specimen_name"],sample_naming_convenstion)
                    MagRec["er_site_name"]=self.get_site_name(MagRec["er_sample_name"],site_naming_convenstion)
                    MagRec['er_location_name']=""
                    MagRec['er_analyst_mail_names']=user_name 
                    MagRec["magic_instrument_codes"]="" 
                    MagRec["measurement_flag"]='g'
                    MagRec["measurement_number"]="%i"%measurement_running_number
                    MagRec['treatment_temp']="%.2f"%(float(meas_line['Treatment'].split(".")[0])+273.)
                    MagRec["measurement_dec"]=meas_line["Declination"]
                    MagRec["measurement_inc"]=meas_line["Inclination"]
                    MagRec["measurement_magn_moment"]='%10.3e'%(float(meas_line["Moment"])*1e-3) # in Am^2
                    MagRec["measurement_temp"]='273.' # room temp in kelvin
                    MagRec["treatment_dc_field"]='%8.3e'%(float(labfield[0])*1e-6)
                    MagRec["treatment_dc_field_phi"]="%.2f"%(float(labfield[1]))
                    MagRec["treatment_dc_field_theta"]="%.2f"%(float(labfield[2]))
                    MagRec["measurement_standard"]="u"
                    MagRec["magic_experiment_name"]=MagRec["er_specimen_name"]+":"+Magic_lab_protocols[experiment]

                    this_specimen_teratments.append(float(meas_line['Treatment']))                    
                    # fill in LP and LT
                    lab_protocols_string=Magic_lab_protocols[experiment]
                    tr_temp=float(meas_line['Treatment'].split(".")[0])
                    if len(meas_line['Treatment'].split("."))==1:
                        tr_tr=0
                    else:
                        tr_tr=float(meas_line['Treatment'].split(".")[1])
                    
                    # identify the step in the experiment from Experiment_Type,
                    # IZ/ZI/IZZI
                    if experiment in ['IZZI','IZ','ZI']:
                        if float(tr_temp)==0:
                            lab_treatment="LT-NO" # NRM
                        elif float(tr_tr)==0:                            
                            lab_treatment="LT-T-Z"
                            if tr_temp+0.1 in this_specimen_teratments[:-1]:
                                lab_protocols_string="LP-PI-TRM-IZ:"+lab_protocols_string
                            else:
                                lab_protocols_string="LP-PI-TRM-ZI:"+lab_protocols_string
                                                
                        elif float(tr_tr)==10 or float(tr_tr)==1:                            
                            lab_treatment="LT-T-I"
                            if tr_temp+0.0 in this_specimen_teratments[:-1]:
                                lab_protocols_string="LP-PI-TRM-ZI:"+lab_protocols_string
                            else:
                                lab_protocols_string="LP-PI-TRM-IZ:"+lab_protocols_string

                        elif float(tr_tr)==20 or float(tr_tr)==2:                            
                            lab_treatment="LT-PTRM-I"            
                        elif float(tr_tr)==30 or float(tr_tr)==3:                            
                            lab_treatment="LT-PTRM-MD"            
                        elif float(tr_tr)==40 or float(tr_tr)==4:                            
                            lab_treatment="LT-PTRM-AC"            
                        else:                            
                            print "-E- unknown measurement code specimen %s treatmemt %s"%(meas_line['Specimen'],meas_line['Treatment'])
                        
                    elif experiment in ['ATRM 6 positions']:
                        lab_protocols_string="LP-AN-TRM"
                        if float(tr_tr)==0:
                            lab_treatment="LT-T-Z"
                            MagRec["treatment_dc_field_phi"]='0'
                            MagRec["treatment_dc_field_theta"]='0'
                        else:
                                    
                            # find the direction of the lab field in two ways:
                            # (1) using the treatment coding (XX.1=+x, XX.2=+y, XX.3=+z, XX.4=-x, XX.5=-y, XX.6=-z)
                            tdec=[0,90,0,180,270,0,0,90,0]
                            tinc=[0,0,90,0,0,-90,0,0,90]
                            if tr_tr < 10:
                                ipos_code=int(tr_tr)-1
                            else:
                                ipos_code=int(tr_tr/10)-1
                            # (2) using the magnetization
                            DEC=float(meas_line["Declination"])
                            INC=float(meas_line["Inclination"])
                            if INC < 45 and INC > -45:
                                if DEC>315  or DEC<45: ipos_guess=0
                                if DEC>45 and DEC<135: ipos_guess=1
                                if DEC>135 and DEC<225: ipos_guess=3
                                if DEC>225 and DEC<315: ipos_guess=4
                            else:
                                if INC >45: ipos_guess=2
                                if INC <-45: ipos_guess=5
                            # prefer the guess over the code
                            ipos=ipos_guess
                            # check it 
                            if tr_tr!= 7 and tr_tr!= 70:
                                if ipos_guess!=ipos_code:
                                    print "-W- WARNING: check specimen %s step %s, ATRM measurements, coding does not match the direction of the lab field"%(specimen,meas_line['Treatment'])
                            MagRec["treatment_dc_field_phi"]='%7.1f' %(tdec[ipos])
                            MagRec["treatment_dc_field_theta"]='%7.1f'% (tinc[ipos])
                                
                            if float(tr_tr)==70 or float(tr_tr)==7: # alteration check as final measurement
                                    lab_treatment="LT-PTRM-I"
                            else:
                                    lab_treatment="LT-T-I"
                                
                    elif experiment in ['cooling rate']:
                        print "Dont support yet cooling rate experiment file. Contact rshaar@ucsd.edu"
                    elif experiment in ['NLT']:
                        if float(tr_tr)==0:
                            lab_protocols_string="LP-TRM"
                            lab_treatment="LT-T-Z"
                        else:
                            lab_protocols_string="LP-TRM"
                            lab_treatment="LT-T-I"
                            
                    MagRec["magic_method_codes"]=lab_treatment+":"+lab_protocols_string
                    line_string=""
                    for i in range(len(magic_headers)):
                        line_string=line_string+MagRec[magic_headers[i]]+"\t"
                    fout.write(line_string[:-1]+"\n")

        #--
        MSG="files converted to MagIC format and merged into one file:\n magic_measurements.txt\n "            
        dlg1 = wx.MessageDialog(None,caption="Message:", message=MSG ,style=wx.OK|wx.ICON_INFORMATION)
        dlg1.ShowModal()
        dlg1.Destroy()

        self.Destroy()


    def on_cancelButton(self,event):
        self.Destroy()

    def get_sample_name(self,specimen,sample_naming_convenstion):
        if sample_naming_convenstion[0]=="sample=specimen":
            sample=specimen
        elif sample_naming_convenstion[0]=="no. of terminate characters":
            n=int(sample_naming_convenstion[1])*-1
            sample=specimen[:n]
        elif sample_naming_convenstion[0]=="charceter delimited":
            d=sample_naming_convenstion[1]
            sample_splitted=specimen.split(d)
            if len(sample_splitted)==1:
                sample=sample_splitted[0]
            else:
                sample=d.join(sample_splitted[:-1])
        return sample
                            
    def get_site_name(self,sample,site_naming_convenstion):
        if site_naming_convenstion[0]=="site=sample":
            site=sample
        elif site_naming_convenstion[0]=="no. of terminate characters":
            n=int(site_naming_convenstion[1])*-1
            site=sample[:n]
        elif site_naming_convenstion[0]=="charceter delimited":
            d=site_naming_convenstion[1]
            site_splitted=sample.split(d)
            if len(site_splitted)==1:
                site=site_splitted[0]
            else:
                site=d.join(site_splitted[:-1])
        
        return site
            
    
#--------------------------------------------------------------    
# Run the GUI
#--------------------------------------------------------------


if __name__ == '__main__':
    app = wx.PySimpleApp()
    app.frame = Arai_GUI()
    #dw, dh = wx.DisplaySize() 
    #w, h = app.frame.GetSize()
    #print 'display:', dw, dh
    #print "gui:", w, h
    app.frame.Show()
    app.frame.Center()
    app.MainLoop()

    


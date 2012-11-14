#!/usr/bin/env python


#matplotlib.use('WXAgg')
import matplotlib
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas \
#NavigationToolbar2WxAgg as NavigationToolbar

import sys,pylab,scipy,pmag,os,shutil
import subprocess
import time
import wx
import wx.grid
import random
from pylab import *
from scipy.optimize import curve_fit
import wx.lib.agw.floatspin as FS
from mpl_toolkits.basemap import Basemap, shiftgrid

import thellier_optimizer_2d

matplotlib.rc('xtick', labelsize=10) 
matplotlib.rc('ytick', labelsize=10) 
matplotlib.rc('axes', labelsize=8) 
matplotlib.rcParams['savefig.dpi'] = 300.

rcParams.update({"svg.embed_char_paths":False})

# The recommended way to use wx with mpl is with the WXAgg
# backend. 
#


#import pprint
#import random
#import wx
#import wx.lib.sized_controls as sc  

#from matplotlib.figure import Figure



#============================================================================================

class Arai_GUI(wx.Frame):
    """ The main frame of the application
    """
    title = 'PmagPy Thellier GUI'
    
    def __init__(self):
        wx.Frame.__init__(self, None, wx.ID_ANY, self.title)
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
        self.MagIC_directories_list=[]

        self.Data,self.Data_hierarchy=self.get_data() # Get data from magic_measurements and rmag_anistropy if exist.
        self.Data_info=self.get_data_info() # get all ages, locations etc. (from er_ages, er_sites, er_locations)
        self.Data_samples={}
        self.last_saved_pars={}
        self.specimens=self.Data.keys()         # get list of specimens
        self.specimens.sort()                   # get list of specimens
        self.panel = wx.Panel(self)          # make the Panel
        self.Main_Frame()                   # build the main frame
        self.create_menu()                  # create manu bar
        
    def get_DIR(self):
        """ Choose a working directory dialog
        """
        dialog = wx.DirDialog(None, "Choose a directory:",defaultPath = self.currentDirectory ,style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON | wx.DD_CHANGE_DIR)
        if dialog.ShowModal() == wx.ID_OK:
          self.WD=dialog.GetPath()
        self.magic_file=self.WD+"/"+"magic_measurements.txt"
        dialog.Destroy()

        #intialize GUI_log
        self.GUI_log=open("%s/Thellier_GUI.log"%self.WD,'w')
        
    def Main_Frame(self):
        """ Build main frame od panel: buttons, etc.
            choose the first specimen and display data
        """
        #----------------------------------------------------------------------                     
        # Create the mpl Figure and FigCanvas objects. 
        # 5x4 inches, 100 dots-per-inch
        #----------------------------------------------------------------------                     
        #
        self.dpi = 100
        self.fig1 = Figure((5., 5.), dpi=self.dpi)
        self.canvas1 = FigCanvas(self.panel, -1, self.fig1)
        self.fig1.text(0.01,0.98,"Arai plot",{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'left' })

        self.fig2 = Figure((2.5, 2.5), dpi=self.dpi)
        self.canvas2 = FigCanvas(self.panel, -1, self.fig2)
        self.fig2.text(0.02,0.96,"Zijderveld",{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'left' })

        self.fig3 = Figure((2.5, 2.5), dpi=self.dpi)
        self.canvas3 = FigCanvas(self.panel, -1, self.fig3)
        self.fig3.text(0.02,0.96,"Equal area",{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'left' })

        self.fig4 = Figure((2.5, 2.5), dpi=self.dpi)
        self.canvas4 = FigCanvas(self.panel, -1, self.fig4)
        self.fig4.text(0.02,0.96,"Sample data",{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'left' })

        self.fig5 = Figure((2.5, 2.5), dpi=self.dpi)
        self.canvas5 = FigCanvas(self.panel, -1, self.fig5)
        self.fig5.text(0.02,0.96,"M/M0",{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'left' })

        # make axes of the figures
        self.araiplot = self.fig1.add_axes([0.1,0.1,0.8,0.8])
        self.zijplot = self.fig2.add_subplot(111)
        self.eqplot = self.fig3.add_subplot(111)
        self.sampleplot = self.fig4.add_axes([0.2,0.3,0.7,0.6],frameon=True,axisbg='None')
        self.mplot = self.fig5.add_axes([0.2,0.15,0.7,0.7],frameon=True,axisbg='None')


        #----------------------------------------------------------------------                     
        # bottons, lists, boxes, and features
        #----------------------------------------------------------------------                     

        # initialize first specimen in list as current specimen
        try:
            self.s=self.specimens[0]
        except:
            self.s=""


        # set font size and style
        #font1 = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Comic Sans MS')
        font1 = wx.Font(9, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Arial')
        font = wx.SystemSettings_GetFont(wx.SYS_SYSTEM_FONT)
        font.SetPointSize(10)


        # Combo-box with a list of specimen
        self.specimens_box_label = wx.StaticText(self.panel, label=" Specimen")
        self.specimens_box = wx.ComboBox(self.panel, -1, self.s, (100, 20), wx.DefaultSize,self.specimens, wx.CB_DROPDOWN,name="specimen")
        self.Bind(wx.EVT_TEXT, self.onSelect_specimen,self.specimens_box)
        
        # buttons to move forward and backwards from specimens        
        self.nextbutton = wx.Button(self.panel, id=-1, label='next')#,style=wx.BU_EXACTFIT)#, size=(175, 28))
        self.Bind(wx.EVT_BUTTON, self.on_next_button, self.nextbutton)

        self.prevbutton = wx.Button(self.panel, id=-1, label='previous')#,style=wx.BU_EXACTFIT)#, size=(175, 28))
        self.Bind(wx.EVT_BUTTON, self.on_prev_button, self.prevbutton)
        
        #  temperatures bounds
        try:
            self.temperatures=array(self.Data[self.s]['t_Arai'])-273.
            self.T_list=["%.0f"%T for T in self.temperatures]
        except:
            self.T_list=[]
        
        #  Tmin
        self.tmin_box_label = wx.StaticText(self.panel, label=" T min")
        self.tmin_box = wx.ComboBox(self.panel, -1, "" , (100, 20), wx.DefaultSize,self.T_list, wx.CB_DROPDOWN)
        self.Bind(wx.EVT_COMBOBOX, self.get_new_T_PI_parameters,self.tmin_box)

        #  Tmax
        self.tmax_box_label = wx.StaticText(self.panel, label=" T max")
        self.tmax_box = wx.ComboBox(self.panel, -1, "", (100, 20), wx.DefaultSize,self.T_list, wx.CB_DROPDOWN)
        self.Bind(wx.EVT_COMBOBOX, self.get_new_T_PI_parameters,self.tmax_box)

        # text_box for presenting the measurements
        self.logger = wx.TextCtrl(self.panel, id=-1, size=(200,500), style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
        self.logger.SetFont(font1)

        # save/delete interpretation buttons
        self.save_interpretation_button = wx.Button(self.panel, id=-1, label='save')#,style=wx.BU_EXACTFIT)#, size=(175, 28))
        self.delete_interpretation_button = wx.Button(self.panel, id=-1, label='delete')#,style=wx.BU_EXACTFIT)#, size=(175, 28))
        self.Bind(wx.EVT_BUTTON, self.on_save_interpretation_button, self.save_interpretation_button)
        self.Bind(wx.EVT_BUTTON, self.on_delete_interpretation_button, self.delete_interpretation_button)

        # Specimen interpretation window (Blab; Banc, Dec, Inc, correction factors etc.)

        self.Blab_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50,20))
        self.Banc_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50,20))
        self.Aniso_factor_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50,20))
        self.NLT_factor_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50,20))
        self.declination_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50,20))
        self.inclination_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50,20))

        specimen_stat_window = wx.GridSizer(2, 8, 12, 12)
        #try:
        #    labfield=float(self.Data[self.s]['pars']['lab_dc_field'])*1e6
        #    self.Blab_window.SetValue(labfield)
        #except:
        #    labfield=0
        
        specimen_stat_window.AddMany( [(wx.StaticText(self.panel,label="",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(self.panel,label="\nB_lab",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(self.panel,label="\nB_anc",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(self.panel,label="Aniso\ncorrection",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(self.panel,label="NLT\ncorrection", style=wx.TE_CENTER),wx.EXPAND),
            (wx.StaticText(self.panel,label="", style=wx.TE_CENTER),wx.EXPAND),
            (wx.StaticText(self.panel,label="\nDec", style=wx.TE_CENTER),wx.TE_CENTER),
            (wx.StaticText(self.panel,label="\nInc", style=wx.TE_CENTER),wx.EXPAND),                          
            (wx.StaticText(self.panel,label="    "), wx.EXPAND),
            (self.Blab_window, wx.EXPAND),
            (self.Banc_window, wx.EXPAND) ,
            (self.Aniso_factor_window, wx.EXPAND) ,
            (self.NLT_factor_window, wx.EXPAND),
            (wx.StaticText(self.panel,label="    "), wx.EXPAND),
            (self.declination_window, wx.EXPAND) ,
            (self.inclination_window, wx.EXPAND)])


        # Specimen statistcis window 
        try:
            if 'specimen_frac' not in self.Data[self.s]['pars'].keys():
              specimen_frac=""
            else:
              specimen_frac="%.2f"%self.Data[self.s]['pars']['specimen_frac']
        except:
            pass
        
        self.n_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50,20))
        self.int_ptrm_n_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50,20))
        self.frac_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50,20))
        self.scat_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
        self.gap_max_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
        self.f_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
        self.fvds_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
        self.b_beta_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
        self.g_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
        self.q_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
        self.int_mad_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
        self.dang_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
        self.drats_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
        self.md_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))

        self.n_threshold_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50,20))
        self.int_ptrm_n_threshold_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50,20))
        self.frac_threshold_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50,20))
        self.scat_threshold_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50,20))
        self.gap_max_threshold_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
        self.f_threshold_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
        self.fvds_threshold_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
        self.b_beta_threshold_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
        self.g_threshold_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
        self.q_threshold_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
        self.int_mad_threshold_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
        self.dang_threshold_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
        self.drats_threshold_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))
        self.md_threshold_window=wx.TextCtrl(self.panel,style=wx.TE_READONLY|wx.TE_CENTER,size=(50,20))

        self.n_threshold_window.SetBackgroundColour(wx.NullColor)
        self.int_ptrm_n_threshold_window.SetBackgroundColour(wx.NullColor)
        self.frac_threshold_window.SetBackgroundColour(wx.NullColor)
        self.scat_threshold_window.SetBackgroundColour(wx.NullColor)
        self.gap_max_threshold_window.SetBackgroundColour(wx.NullColor)
        self.f_threshold_window.SetBackgroundColour(wx.NullColor)
        self.fvds_threshold_window.SetBackgroundColour(wx.NullColor)
        self.b_beta_threshold_window.SetBackgroundColour(wx.NullColor)
        self.g_threshold_window.SetBackgroundColour(wx.NullColor)
        self.q_threshold_window.SetBackgroundColour(wx.NullColor)
        self.int_mad_threshold_window.SetBackgroundColour(wx.NullColor)
        self.dang_threshold_window.SetBackgroundColour(wx.NullColor)
        self.drats_threshold_window.SetBackgroundColour(wx.NullColor)
        self.md_threshold_window.SetBackgroundColour(wx.NullColor)

        gs = wx.GridSizer(3, 14, 14, 14)

        gs.AddMany( [(wx.StaticText(self.panel,label="n",style=wx.ALIGN_CENTER_VERTICAL),wx.ALIGN_CENTER_VERTICAL),
            (wx.StaticText(self.panel,label="n_pTRM",style=wx.ALIGN_CENTER_VERTICAL),wx.ALIGN_CENTER_VERTICAL),
            (wx.StaticText(self.panel,label="FRAC",style=wx.ALIGN_CENTER_VERTICAL),wx.ALIGN_CENTER_VERTICAL),
            (wx.StaticText(self.panel,label="SCAT",style=wx.ALIGN_CENTER_VERTICAL),wx.ALIGN_CENTER_VERTICAL),
            (wx.StaticText(self.panel,label="gap_max",style=wx.ALIGN_CENTER_VERTICAL),wx.ALIGN_CENTER_VERTICAL),
            (wx.StaticText(self.panel,label="f",style=wx.ALIGN_CENTER_VERTICAL),wx.ALIGN_CENTER_VERTICAL),
            (wx.StaticText(self.panel,label="fvds",style=wx.ALIGN_CENTER_VERTICAL),wx.ALIGN_CENTER_VERTICAL),
            (wx.StaticText(self.panel,label="beta",style=wx.ALIGN_CENTER_VERTICAL),wx.ALIGN_CENTER_VERTICAL),
            (wx.StaticText(self.panel,label="g",style=wx.ALIGN_CENTER_VERTICAL),wx.ALIGN_CENTER_VERTICAL),
            (wx.StaticText(self.panel,label="q",style=wx.ALIGN_CENTER_VERTICAL),wx.ALIGN_CENTER_VERTICAL),
            (wx.StaticText(self.panel,label="MAD",style=wx.ALIGN_CENTER_VERTICAL)),
            (wx.StaticText(self.panel,label="DANG",style=wx.ALIGN_CENTER_VERTICAL)),
            (wx.StaticText(self.panel,label="DRATS",style=wx.ALIGN_CENTER_VERTICAL)),
            (wx.StaticText(self.panel,label="MD tail",style=wx.ALIGN_CENTER_VERTICAL)),
            (self.n_threshold_window, wx.EXPAND),
            (self.int_ptrm_n_threshold_window, wx.EXPAND),                     
            (self.frac_threshold_window, wx.EXPAND),
            (self.scat_threshold_window, wx.EXPAND),
            (self.gap_max_threshold_window, wx.EXPAND),
            (self.f_threshold_window, wx.EXPAND),
            (self.fvds_threshold_window, wx.EXPAND),
            (self.b_beta_threshold_window, wx.EXPAND),
            (self.g_threshold_window, wx.EXPAND),
            (self.q_threshold_window, wx.EXPAND),
            (self.int_mad_threshold_window, wx.EXPAND),
            (self.dang_threshold_window, wx.EXPAND),
            (self.drats_threshold_window, wx.EXPAND),
            (self.md_threshold_window, wx.EXPAND),
            (self.n_window, wx.EXPAND),
            (self.int_ptrm_n_window, wx.EXPAND),
            (self.frac_window, wx.EXPAND),
            (self.scat_window, wx.EXPAND),
            (self.gap_max_window, wx.EXPAND),
            (self.f_window, wx.EXPAND),
            (self.fvds_window, wx.EXPAND),
            (self.b_beta_window, wx.EXPAND),
            (self.g_window, wx.EXPAND),
            (self.q_window, wx.EXPAND),
            (self.int_mad_window, wx.EXPAND),
            (self.dang_window, wx.EXPAND),
            (self.drats_window, wx.EXPAND),
            (self.md_window, wx.EXPAND)])

        gs1 = wx.GridSizer(3, 1,12,12)
        gs1.AddMany( [(wx.StaticText(self.panel,label="",style=wx.ALIGN_CENTER)),
            (wx.StaticText(self.panel,label="Accpetance criteria:",style=wx.ALIGN_CENTER)),
            (wx.StaticText(self.panel,label="Specimen's statistics:",style=wx.ALIGN_CENTER))])
        
        self.write_acceptance_criteria_to_boxes()  # write threshold values to boxes

        
        #----------------------------------------------------------------------                     
        # Design the panel
        #----------------------------------------------------------------------
        
        vbox1 = wx.BoxSizer(wx.VERTICAL)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)

        hbox1a= wx.BoxSizer(wx.HORIZONTAL)
        hbox1b= wx.BoxSizer(wx.HORIZONTAL)
        vbox1a=wx.BoxSizer(wx.VERTICAL)

        hbox1c= wx.BoxSizer(wx.HORIZONTAL)
        hbox1d= wx.BoxSizer(wx.HORIZONTAL)
        vbox1b=wx.BoxSizer(wx.VERTICAL)
        
        hbox1a.Add(self.specimens_box_label, flag=wx.ALIGN_CENTER_VERTICAL,border=2)
        hbox1a.Add(self.specimens_box, flag=wx.ALIGN_CENTER_VERTICAL)#, border=10)
        hbox1b.Add(self.prevbutton,flag=wx.ALIGN_CENTER_VERTICAL)#, border=8)
        hbox1b.Add(self.nextbutton, flag=wx.ALIGN_CENTER_VERTICAL)#, border=10)
        vbox1a.Add(hbox1a,flag=wx.ALIGN_RIGHT)
        vbox1a.Add(hbox1b,flag=wx.ALIGN_RIGHT)


        hbox1c.Add(self.tmin_box_label, flag=wx.ALIGN_CENTER_VERTICAL,border=2)
        hbox1c.Add(self.tmin_box, flag=wx.ALIGN_CENTER_VERTICAL)#, border=10)

        hbox1c.AddSpacer(10)
        hbox1c.Add(self.save_interpretation_button,flag=wx.ALIGN_CENTER_VERTICAL)#, border=8)

        hbox1d.Add(self.tmax_box_label,flag=wx.ALIGN_CENTER_VERTICAL)#, border=8)
        hbox1d.Add(self.tmax_box, flag=wx.ALIGN_CENTER_VERTICAL)#, border=10)

        hbox1d.AddSpacer(10)
        hbox1d.Add(self.delete_interpretation_button,flag=wx.ALIGN_CENTER_VERTICAL)#, border=8)
        
        vbox1b.Add(hbox1c,flag=wx.ALIGN_RIGHT)
        vbox1b.Add(hbox1d,flag=wx.ALIGN_RIGHT)


        vbox1.AddSpacer(10)
        hbox1.AddSpacer(10)
        hbox1.Add(vbox1a,flag=wx.ALIGN_LEFT)#,flag=wx.ALIGN_CENTER_VERTICAL)
        hbox1.Add(vbox1b,flag=wx.ALIGN_LEFT)#,flag=wx.ALIGN_CENTER_VERTICAL)

        vbox1.Add(hbox1, flag=wx.LEFT)#, border=10)
        self.panel.SetSizer(vbox1)


        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2.Add(self.logger,flag=wx.ALIGN_CENTER_HORIZONTAL)#,border=8)        
        hbox2.Add(self.canvas1,flag=wx.ALIGN_CENTER_HORIZONTAL)#,border=8)

        vbox2 = wx.BoxSizer(wx.VERTICAL)        
        vbox2.Add(self.canvas2,flag=wx.ALIGN_LEFT)#,border=8)
        vbox2.Add(self.canvas3,flag=wx.ALIGN_LEFT)#,border=8)

        vbox3 = wx.BoxSizer(wx.VERTICAL)        
        vbox3.Add(self.canvas4,flag=wx.ALIGN_LEFT|wx.ALIGN_TOP,border=8)
        vbox3.Add(self.canvas5,flag=wx.ALIGN_LEFT|wx.ALIGN_TOP,border=8)
        
        hbox2.Add(vbox2,flag=wx.ALIGN_CENTER_HORIZONTAL)#,border=8)
        hbox2.Add(vbox3,flag=wx.ALIGN_CENTER_HORIZONTAL)#,border=8)

        vbox1.Add(hbox2, flag=wx.LEFT)#, border=10)


        hbox_test = wx.BoxSizer(wx.HORIZONTAL)
    
        
        hbox1.AddSpacer(10)                            

        hbox1.Add(specimen_stat_window, proportion=1, flag=wx.EXPAND)


        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        hbox3.AddSpacer(10)                            
        hbox3.Add(gs1,flag=wx.ALIGN_LEFT)
        hbox3.AddSpacer(10)        

        hbox3.Add(gs,flag=wx.ALIGN_LEFT)
  
        vbox1.AddSpacer(20)
        vbox1.Add(hbox3,flag=wx.LEFT)
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
        sample=self.Data_hierarchy['specimens'][self.s]
        if sample not in self.Data_samples.keys():
            self.Data_samples[sample]={}
        self.Data_samples[sample][self.s]=self.Data[self.s]['pars']["specimen_int_uT"]
        
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
        sample=self.Data[self.s]['pars']['er_sample_name']
        if sample in self.Data_samples.keys():
            if self.s in self.Data_samples[sample].keys():
                del self.Data_samples[sample][self.s]
        self.tmin_box.SetValue("")
        self.tmax_box.SetValue("")
        self.clear_boxes()
        self.draw_figure(self.s)
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


        high_threshold_velue_list=['specimen_gap_max','specimen_b_beta','specimen_dang','specimen_drats','specimen_int_mad','specimen_md']
        low_threshold_velue_list=['specimen_n','specimen_int_ptrm_n','specimen_f','specimen_fvds','specimen_frac','specimen_g','specimen_q']
      
        self.ignore_parameters={}
        
        for key in high_threshold_velue_list + low_threshold_velue_list:
            if (key in high_threshold_velue_list and float(self.accept_new_parameters[key]) >100) or\
               (key in low_threshold_velue_list and float(self.accept_new_parameters[key]) <0.1):
                Value=""
                command="self.%s_threshold_window.SetValue(\"\")"%key.split('specimen_')[-1]
                exec command
                command="self.%s_threshold_window.SetBackgroundColour(wx.Colour(128, 128, 128))"%key.split('specimen_')[-1]
                exec command
                self.ignore_parameters[key]=True
                continue
            elif key in ['specimen_n','specimen_int_ptrm_n']:
                Value="%.0f"%self.accept_new_parameters[key]
            elif key in ['specimen_dang','specimen_drats','specimen_int_mad','specimen_md','specimen_g','specimen_q']:
                Value="%.1f"%self.accept_new_parameters[key]
            elif key in ['specimen_f','specimen_fvds','specimen_frac','specimen_b_beta','specimen_gap_max']:
                Value="%.2f"%self.accept_new_parameters[key]

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
            

    #----------------------------------------------------------------------
    

    def Add_text(self,s):
      """ Add text to measurement data wondow.
      """

      self.logger.Clear()
      font1 = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Arial')
      String="  Step\tTemp\t Dec\t Inc\tMoment\n"
      self.logger.AppendText(String)

      self.logger.SetFont(font1)
      for rec in self.Data[self.s]['datablock']:
          #print rec.keys()
          if "LT-NO" in rec['magic_method_codes']:
              step="N"
          if "LT-T-Z" in rec['magic_method_codes']:
              step="Z"
          if "LT-T-I" in rec['magic_method_codes']:
              step="I"
          if "LT-PTRM-I" in rec['magic_method_codes']:
              step="P"
          String="   %s\t%3.0f\t%5.1f\t%5.1f\t%.2e\n"%(step,float(rec['treatment_temp'])-273.,float(rec['measurement_dec']),float(rec['measurement_inc']),float(rec['measurement_magn_moment']))

          self.logger.AppendText( String)
      
    #----------------------------------------------------------------------
        
    def create_menu(self):
        """ Create menu
        """
        self.menubar = wx.MenuBar()
        
        menu_file = wx.Menu()
        
        m_change_working_directory = menu_file.Append(-1, "&Open MagIC project directory", "")
        self.Bind(wx.EVT_MENU, self.on_menu_change_working_directory, m_change_working_directory)

        m_add_working_directory = menu_file.Append(-1, "&Add a MagIC project directory", "")
        self.Bind(wx.EVT_MENU, self.on_menu_add_working_directory, m_add_working_directory)

        m_open_magic_file = menu_file.Append(-1, "&Open MagIC measurement file", "")
        self.Bind(wx.EVT_MENU, self.on_menu_open_magic_file, m_open_magic_file)

        submenu_save_plots = wx.Menu()

        m_save_Arai_plot = submenu_save_plots.Append(-1, "&Save Arai plot", "")
        self.Bind(wx.EVT_MENU, self.on_save_Arai_plot, m_save_Arai_plot)

        m_save_zij_plot = submenu_save_plots.Append(-1, "&Save Zijderveld plot", "")
        self.Bind(wx.EVT_MENU, self.on_save_Zij_plot, m_save_zij_plot,"Zij")

        m_save_eq_plot = submenu_save_plots.Append(-1, "&Save equal area plot", "")
        self.Bind(wx.EVT_MENU, self.on_save_Eq_plot, m_save_eq_plot,"Eq")

        m_save_all_plots = submenu_save_plots.Append(-1, "&Save all plots", "")
        #self.Bind(wx.EVT_MENU, self.on_save_all_plots, m_save_all_plots)

        m_new_sub_plots = menu_file.AppendMenu(-1, "&Save plot", submenu_save_plots)

        
        menu_file.AppendSeparator()
        m_exit = menu_file.Append(-1, "E&xit\tCtrl-X", "Exit")
        self.Bind(wx.EVT_MENU, self.on_menu_exit, m_exit)

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


        menu_Optimizer = wx.Menu()
        m_run_optimizer = menu_Optimizer.Append(-1, "&Run Thellier optimizer", "")
        self.Bind(wx.EVT_MENU, self.on_menu_run_optimizer, m_run_optimizer)

        menu_Plot= wx.Menu()
        m_plot_data = menu_Plot.Append(-1, "&Plot paleointensity curve", "")
        self.Bind(wx.EVT_MENU, self.on_menu_plot_data, m_plot_data)

        
        #menu_help = wx.Menu()
        #m_about = menu_help.Append(-1, "&About\tF1", "About the demo")
        
        self.menubar.Append(menu_file, "&File")
        self.menubar.Append(menu_Analysis, "&Analysis")
        self.menubar.Append(menu_Auto_Interpreter, "&Auto Interpreter")
        self.menubar.Append(menu_Optimizer, "&Optimizer")
        self.menubar.Append(menu_Plot, "&Plot")
        
        #self.menubar.Append(menu_Tools, "&Tools")        
        #self.menubar.Append(menu_help, "&Help")
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
        self.temperatures=array(self.Data[self.s]['t_Arai'])-273.
        self.T_list=["%.0f"%T for T in self.temperatures]
        self.tmin_box.SetItems(self.T_list)
        self.tmax_box.SetItems(self.T_list)
        self.tmin_box.SetStringSelection("")
        self.tmax_box.SetStringSelection("")
        self.Blab_window.SetValue("%.0f"%(float(self.Data[self.s]['pars']['lab_dc_field'])*1e6))
        if "saved" in self.Data[self.s]['pars']:
            self.pars=self.Data[self.s]['pars']
            self.update_GUI_with_new_interpretation()
        
        # if previous interpretation was saved, display the interpretation.
        # else leave it empty
##        if self.s in self.redo_specimens.keys():
##            self.tmin_box.SetStringSelection("%.0f"%(float(self.redo_specimens[self.s]['pars']['measurement_step_min'])-273))
##            self.tmax_box.SetStringSelection("%.0f"%(float(self.redo_specimens[self.s]['pars']['measurement_step_max'])-273))
##            self.pars=self.get_PI_parameters(self.s,float(self.redo_specimens[self.s]['pars']['measurement_step_min']),float(self.redo_specimens[self.s]['pars']['measurement_step_max']))
##            self.update_GUI_with_new_interpretation()
##        else:            
##            self.tmin_box.SetStringSelection("")
##            self.tmax_box.SetStringSelection("")

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

    def clear_boxes(self):
        """ Clear all boxes
        """        
        self.tmin_box.Clear()
        self.tmin_box.SetItems(self.T_list)
        self.tmin_box.SetSelection(-1)

        self.tmax_box.Clear()
        self.tmax_box.SetItems(self.T_list)
        self.tmax_box.SetSelection(-1)
        
        self.Banc_window.SetValue("")
        self.Banc_window.SetBackgroundColour(wx.NullColor)
        self.Aniso_factor_window.SetValue("")
        self.NLT_factor_window.SetValue("")

        window_list=['n','int_ptrm_n','frac','scat','gap_max','f','fvds','b_beta','g','q','int_mad','dang','drats','md']
        for key in window_list:
            command="self.%s_window.SetValue(\"\")"%key
            exec command
            command="self.%s_window.SetBackgroundColour(wx.NullColor)"%key
            exec command
            


    #----------------------------------------------------------------------
    # manu bar options:
    #----------------------------------------------------------------------

    def on_menu_exit(self, event):
        self.Destroy()
        exit()


    def on_save_Arai_plot(self, event):
        SaveMyPlot(self.fig1,self.pars,"Arai")


    def on_save_Zij_plot(self, event):
        SaveMyPlot(self.fig2,self.pars,"Zij")

    def on_save_Eq_plot(self, event):
        SaveMyPlot(self.fig3,self.pars,"Eqarea")

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
            self, message="choose a file in a pmagpy redo format",
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

        dia = Criteria_Dialog(None, replace_acceptance_criteria,title='Set Accpetance Criteria from file')
        dia.Center()
        if dia.ShowModal() == wx.ID_OK: # Until the user clicks OK, show the message            
            self.On_close_criteria_box(dia)



    #----------------------------------------------------------------------        

    def on_menu_criteria(self, event):
        
        """
        Change acceptance criteria
        and save it to pmag_criteria.txt
        """
                            

        dia = Criteria_Dialog(None, self.accept_new_parameters,title='Set Accpetance Criteria')
        dia.Center()
        result = dia.ShowModal()

        if result == wx.ID_OK: # Until the user clicks OK, show the message
##            self.Valid_values=True
##            # check valid values
##            for key in self.high_threshold_velue_list + self.low_threshold_velue_list + ['sample_int_n','sample_int_sigma','sample_int_sigma_perc','sample_int_n_outlier_check']:
##                try:
##                    command="float(dia.set_%s.GetValue())"%(key)
##                    exec command
##                except:
##                    command="if dia.set_%s.GetValue() !=\"\" :  Valid_values=False ; self.show_messege(\"%s\")  "%(key,key)
##                    exec command
##            if self.Valid_values ==True:
            self.On_close_criteria_box(dia)
                
    #----------------------------------------------------------------------
            
    def On_close_criteria_box(self,dia):
        # inialize newcriteria with the default values
        tmp_acceptance_criteria,replace_acceptance_criteria=self.get_default_criteria()
        
        # replace values by the new ones
        
        # specimen's criteria
        for key in self.high_threshold_velue_list + self.low_threshold_velue_list:
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

        # sample calculation method:            
        for key in ['sample_stdev_opt','sample_bs','sample_bs_par']:
            command="replace_acceptance_criteria[\"%s\"]=dia.set_%s.GetValue()"%(key,key)            
            try:
                exec command
            except:
                command="if dia.set_%s.GetValue() !=\"\" : self.show_messege(\"%s\")  "%(key,key)
                exec command


        # sample ceiteria :            
        for key in ['sample_int_n','sample_int_n_outlier_check']:
            command="replace_acceptance_criteria[\"%s\"]=float(dia.set_%s.GetValue())"%(key,key)            
            try:
                exec command
            except:
                command="if dia.set_%s.GetValue() !=\"\" : self.show_messege(\"%s\")  "%(key,key)
                exec command


        # sample ceiteria STDEV-OPT:
        if replace_acceptance_criteria['sample_stdev_opt']:
            for key in ['sample_int_sigma_uT','sample_int_sigma_perc','sample_int_interval_uT','sample_int_interval_perc']:
                command="replace_acceptance_criteria[\"%s\"]=float(dia.set_%s.GetValue())"%(key,key)            
                try:
                    exec command
                except:
                    command="if dia.set_%s.GetValue() !=\"\" : self.show_messege(\"%s\")  "%(key,key)
                    exec command


        # sample ceiteria BS, PS-PAR:
        if replace_acceptance_criteria['sample_bs'] or replace_acceptance_criteria['sample_bs_par']:
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
        default_acceptance_criteria,replace_acceptance_criteria=self.get_default_criteria()
        # Replace with new parametrs
        try:
            fin=open(criteria_file,'rU')
            line=fin.readline()
            line=fin.readline()
            header=line.strip('\n').split('\t')
            for L in fin.readlines():
                line=L.strip('\n').split('\t')
                for i in range(len(header)):
                    if "pmag_criteria_code" in header:
                        index=header.index("pmag_criteria_code")
                        if line[index]=="IE-SPEC":
                         
                            # search for specimens criteria:
                            if header[i] in self.high_threshold_velue_list and float(line[i])<100:
                                replace_acceptance_criteria[header[i]]=float(line[i])                    
                            elif header[i] in self.low_threshold_velue_list and float(line[i])>0.01:
                                replace_acceptance_criteria[header[i]]=float(line[i])

                            # scat parametr (true/false)
                            elif header[i] == 'specimen_scat' and ( line[i]=='True' or line[i]=='TRUE' or line[i]==True):
                                replace_acceptance_criteria[specimen_scat]=True
                            elif header[i] == 'specimen_scat' and ( line[i]=='False' or line[i]=='FALSE' or line[i]==False):
                                replace_acceptance_criteria[specimen_scat]=False
                        if line[index]=="IE-SAMP":
                            # search for sample criteria:
                            if header[i] in ['sample_int_n','sample_int_sigma_uT','sample_int_sigma_perc','sample_int_interval_uT','sample_int_interval_perc','sample_int_n_outlier_check']:
                                replace_acceptance_criteria[header[i]]=float(line[i])
                            if header[i] == "sample_int_sigma":
                                replace_acceptance_criteria['sample_int_sigma']=float(line[i])*1e-6
                                replace_acceptance_criteria['sample_int_sigma_uT']=float(line[i])*1e6
                                                                
                    else:
                        #print header[i],line[i]
                        # search for specimens criteria:
                        if header[i] in self.high_threshold_velue_list and float(line[i])<100:
                            replace_acceptance_criteria[header[i]]=float(line[i])                    
                        if header[i] in self.low_threshold_velue_list and float(line[i])>0.01:
                            replace_acceptance_criteria[header[i]]=float(line[i])

                        # scat parametr (true/false)
                        if header[i] == 'specimen_scat' and ( line[i]=='True' or line[i]=='TRUE' or line[i]==True):
                            replace_acceptance_criteria['specimen_scat']=True
                        if header[i] == 'specimen_scat' and ( line[i]=='False' or line[i]=='FALSE' or line[i]==False):
                            replace_acceptance_criteria['specimen_scat']=False
                            
                        # search for sample criteria:
                        if header[i] in ['sample_int_n','sample_int_sigma_uT','sample_int_sigma_perc','sample_int_interval_uT','sample_int_interval_perc','sample_int_n_outlier_check',\
                                         'specimen_int_max_slope_diff','specimen_int_BS_68_uT','specimen_int_BS_95_uT','specimen_int_BS_68_perc','specimen_int_BS_95_perc']:
                            replace_acceptance_criteria[header[i]]=float(line[i])                    
                        if header[i] == "sample_int_sigma":
                            replace_acceptance_criteria['sample_int_sigma']=float(line[i])*1e-6
                            replace_acceptance_criteria['sample_int_sigma_uT']=float(line[i])*1e6
                        if header[i] in ["sample_bs_par","sample_bs","sample_stdev_opt"]:
                            if line[i]==True or line[i] in ["True","TRUE","1"]:
                                replace_acceptance_criteria[header[i]]=True
                            

            fin.close()
            return(replace_acceptance_criteria)
        
        except:
            self.GUI_log.write("-W- Cant read Criteria file from path\n")
            self.GUI_log.write("-I- using default criteria\n")

            return(default_acceptance_criteria)

    #----------------------------------------------------------------------


    def on_menu_default_criteria(self,event):
        """
        Initialize acceptance criteria tp default
        """
        
        default_acceptance_criteria,replace_acceptance_criteria=self.get_default_criteria()
        self.accept_new_parameters=default_acceptance_criteria
        self.clear_boxes()
        self.write_acceptance_criteria_to_boxes()
        self.write_acceptance_criteria_to_file()

    #----------------------------------------------------------------------


                
        #self.Fit()
        #self.SetMinSize(self.GetSize())

    #----------------------------------------------------------------------


    def on_menu_save_interpretation(self, event):
        
        specimen_criteria_list=['specimen_n','specimen_int_ptrm_n','specimen_f','specimen_fvds','specimen_frac','specimen_gap_max','specimen_b_beta','specimen_scat','specimen_drats','specimen_md','specimen_int_mad','specimen_dang']
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
                if key in ['specimen_f','specimen_fvds','specimen_gap_max','specimen_b_beta','specimen_frac','specimen_drats','specimen_md','specimen_int_mad','specimen_dang']:
                        String1=String1+"%.2f"%self.accept_new_parameters[key]+"\t"

                elif key in ['specimen_n','specimen_int_ptrm_n']:
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
        for crit in specimen_criteria_list:
            String=String+crit+"\t"

        String=String+"PASS/FAIL criteria\t"
        
        thellier_gui_specimen_file.write(String[:-1]+"\n")

        #----------------------------
        #    thellier_gui_samples.txt header
        #----------------------------

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
                           
            for crit in specimen_criteria_list:
                if crit not in self.Data[sp]['pars'].keys():
                           String=String+"N/A"+"\t"
                elif crit in ['specimen_f','specimen_fvds','specimen_gap_max','specimen_b_beta','specimen_frac','specimen_drats','specimen_int_mad','specimen_dang']:
                        String=String+"%.2f"%self.Data[sp]['pars'][crit]+"\t"
                elif crit in ['specimen_md']:
                    if self.Data[sp]['pars']['specimen_md']==-1:
                        String=String+"N/A" +"\t"
                    else:
                        String=String+"%.2f"%self.Data[sp]['pars']['specimen_md']+"\t"
                elif crit in ['specimen_n','specimen_int_ptrm_n']:
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

        thellier_gui_sample_file_header=['er_sample_name',  'sample_int_n'  ,'sample_int_uT',	'sample_int_sigma_uT','sample_int_sigma_perc']
        
        saved_samples_list= self.Data_samples.keys()
        saved_samples_list.sort()
        for sample in saved_samples_list:
            sample_Bs=[]
            for spec in self.Data_samples[sample]:
                sample_Bs.append(c)
            sample_int_n=len(sample_Bs)
            sample_int_uT=mean(sample_Bs)
            sample_int_sigma_uT=std(sample_Bs)
            sample_int_sigma_perc=100*(sample_int_sigma_uT/sample_int_uT)
            
            String="%s\t%i\t%.1f\t%.1f\t%.1f\n"%(sample,sample_int_n,sample_int_uT,sample_int_sigma_uT,sample_int_sigma_perc)
            thellier_gui_sample_file.write(String)
            
        #print "self.Data_samples",self.Data_samples
        
        thellier_gui_specimen_file.close()
        thellier_gui_redo_file.close()
        thellier_gui_sample_file.close()
        

    def on_menu_clear_interpretation(self, event):

        #  delete all previous interpretation
        for sp in self.Data.keys():
            del self.Data[sp]['pars']
            self.Data[sp]['pars']={}
            self.Data[sp]['pars']['lab_dc_field']=self.Data[sp]['lab_dc_field']
            self.Data[sp]['pars']['er_specimen_name']=self.Data[sp]['er_specimen_name']   
            self.Data[sp]['pars']['er_sample_name']=self.Data[sp]['er_sample_name']   
        self.Data_samples={}
        self.tmin_box.SetValue("")
        self.tmax_box.SetValue("")
        self.clear_boxes()
        self.draw_figure(self.s)
                        
    def on_menu_run_interpreter(self, event):

        import random
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
            Best_array=[]
            best_array_std=inf
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

                    if std(Best_array_tmp)<best_array_std:
                        Best_array=Best_array_tmp
                        best_array_std=std(Best_array)
                        Best_interpretations=Best_interpretations_tmp
                        Best_interpretations_tmp={}
            return Best_interpretations,mean(Best_array),std(Best_array)
            

        def find_sample_min_max_interpretation (Intensities,acceptance_criteria):

          # Find the minimum and maximum acceptable sample mean.

          # make a new dictionary named "tmp_Intensities" with all grade A interpretation sorted. 
          tmp_Intensities={}
          Acceptable_sample_min,Acceptable_sample_max="",""
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
              if std(B_tmp)<=acceptance_criteria["sample_int_sigma_uT"] or 100*(std(B_tmp)/mean(B_tmp))<=acceptance_criteria["sample_int_sigma_perc"]:
                  Acceptable_sample_min=mean(B_tmp)
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
              if std(B_tmp)<=acceptance_criteria["sample_int_sigma_uT"] or 100*(std(B_tmp)/mean(B_tmp))<=acceptance_criteria["sample_int_sigma_perc"]:
                  Acceptable_sample_max=mean(B_tmp)
                  #print "max value,std,",mean(B_tmp),std(B_tmp),100*(std(B_tmp)/mean(B_tmp))

                  break
              else:
                  tmp_Intensities[specimen_to_remove].remove(B_tmp_max)
                  if len(tmp_Intensities[specimen_to_remove])<1:
                      break

          if Acceptable_sample_min=="" or Acceptable_sample_max=="":
              return(0.,0.)
          return(Acceptable_sample_min,Acceptable_sample_max) 

        ############
        # End function definitions
        ############

        start_time=time.time()
        #------------------------------------------------
        # Clean work directory
        #------------------------------------------------

        self.write_acceptance_criteria_to_file()
        try:
            shutil.rmtree("./thellier_interpreter")
        except:
            pass

        try:
            os.mkdir("./thellier_interpreter")
        except:
            pass

        parameters_with_upper_bounds= ['specimen_gap_max','specimen_b_beta','specimen_dang','specimen_drats','specimen_int_mad','specimen_md']
        parameters_with_lower_bounds= ['specimen_n','specimen_int_ptrm_n','specimen_f','specimen_fvds','specimen_frac']
        accept_specimen_keys=['specimen_n','specimen_int_ptrm_n','specimen_f','specimen_fvds','specimen_frac','specimen_gap_max','specimen_b_beta','specimen_dang','specimen_drats','specimen_int_mad','specimen_md']

        #------------------------------------------------
        # Intialize interpreter output files:
        # Prepare header for "Thellier_auto_interpretation.all.txt" 
        # All the acceptable interpretation are saved in this file
        #------------------------------------------------

        # log file
        thellier_interpreter_log=open(self.WD+"/"+"./thellier_interpreter//thellier_interpreter.log",'w')
        thellier_interpreter_log.write("-I- Start auto interpreter\n")

        # "all grade A interpretation
        thellier_interpreter_all=open("./"+"/thellier_interpreter/thellier_interpreter_all.txt",'w')
        thellier_interpreter_all.write("tab\tpmag_specimens\n")
        String="er_specimen_name\tmeasurement_step_min\tmeasurement_step_max\tspecimen_lab_field_dc_uT\tspecimen_int_corr_anisotropy\tspecimen_int_corr_nlt\tspecimen_int_uT\t"
        for key in accept_specimen_keys:
            String=String+key+"\t"
        String=String[:-1]+"\n"
        thellier_interpreter_all.write(String)

        #specimen_bound
        Fout_specimens_bounds=open("./"+"/thellier_interpreter/thellier_interpreter_specimens_bounds.txt",'w')
        String="Slecetion criteria:\n"
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
        Fout_specimens_bounds.write("er_sample_name\ter_specimen_name\tspecimen_int_corr_anisotropy\tAnisotropy_code\tspecimen_int_corr_nlt\tspecimen_lab_field_dc_uT\tspecimen_int_min_uT\tspecimen_int_max_uT\tWARNING\n")

        # STDEV-OPT output files
        if self.accept_new_parameters['sample_stdev_opt']:
            Fout_STDEV_OPT_redo=open("./"+"/thellier_interpreter/thellier_interpreter_STDEV-OPT_redo",'w')

            Fout_STDEV_OPT_specimens=open("./"+"/thellier_interpreter/thellier_interpreter_STDEV-OPT_specimens.txt",'w')
            Fout_STDEV_OPT_specimens.write("tab\tpmag_specimens\n")
            String="er_sample_name\ter_specimen_name\tspecimen_int_uT\tmeasurement_step_min\tmeasurement_step_min\tspecimen_lab_field_dc\tAnisotropy_correction_factor\tNLT_correction_factor\t"
            for key in accept_specimen_keys:
                String=String+key+"\t"        
            Fout_STDEV_OPT_specimens.write(String[:-1]+"\n")

            Fout_STDEV_OPT_samples=open("./"+"/thellier_interpreter/thellier_interpreter_STDEV-OPT_samples.txt",'w')
            #Fout_STDEV_OPT_samples.write(String[:-1]+"\n")
            #Fout_STDEV_OPT_samples.write("---------------------------------\n")
            #String=""
            #for key in accept_specimen_keys:
            #    if key!= "specimen_frac":
            #        String=String+"%.2f\t"%self.accept_new_parameters[key]
            #    else:
            #        String=String+"%s\t"%self.accept_new_parameters[key]                
            #Fout_STDEV_OPT_samples.write(String[:-1]+"\n")

            String="Slecetion criteria:\n"
            for key in self.accept_new_parameters.keys():
                if "sample" in key:
                    String=String+key+"\t"
            for key in accept_specimen_keys:
                if "specimen" in key:
                    String=String+key+"\t"
                    
            String=String[:-1]+"\n"
            
            for key in self.accept_new_parameters.keys():
                if "sample" in key:
                    try:
                        String=String+"%.2f"%self.accept_new_parameters[key]+"\t"
                    except:
                        String=String+"%s"%self.accept_new_parameters[key]+"\t"                
            for key in accept_specimen_keys:
                if "specimen" in key:
                    try:
                        String=String+"%.2f"%self.accept_new_parameters[key]+"\t"
                    except:
                        String=String+"%s"%self.accept_new_parameters[key]+"\t"
            String=String[:-1]+"\n"
            Fout_STDEV_OPT_samples.write(String)
            Fout_STDEV_OPT_samples.write("---------------------------------\n")

            Fout_STDEV_OPT_samples.write("er_sample_name\tsample_int_n\tsample_int_uT\tsample_int_sigma_uT\tsample_int_sigma_perc\tsample_int_interval_uT\tsample_int_interval_perc\tWarning\n")
        # simple bootstrap output files
           
        if self.accept_new_parameters['sample_bs']:
           Fout_BS_samples=open("./"+"/thellier_interpreter/thellier_interpreter_BS_samples.txt",'w')
           Fout_BS_samples.write(String[:-1]+"\n")
           Fout_BS_samples.write("---------------------------------\n")
           Fout_BS_samples.write("er_sample_name\tsample_int_n\tsample_int_uT\tsample_int_68_low\tsample_int_68_high\tsample_int_95_low\tsample_int_95_high\tsample_int_sigma_uT\tsample_int_sigma_perc\tWARNING\n")
        # parameteric bootstrap output files

        if self.accept_new_parameters['sample_bs_par']:
           Fout_BS_PAR_samples=open("./"+"/thellier_interpreter/thellier_interpreter_BS-PAR_samples.txt",'w')
           Fout_BS_PAR_samples.write(String[:-1]+"\n") 
           Fout_BS_PAR_samples.write("---------------------------------\n")
           Fout_BS_PAR_samples.write("er_sample_name\tsample_int_n\tsample_int_uT\tsample_int_68_low\tsample_int_68_high\tsample_int_95_low\tsample_int_95_high\tsample_int_sigma_uT\tsample_int_sigma_perc\tWARNING\n")
           
        thellier_interpreter_log.write("-I- using paleointenisty statistics:\n")
        for key in [key for key in self.accept_new_parameters.keys() if "sample" in key]:
            try:
                thellier_interpreter_log.write("-I- %s=%.2f"%(key,self.accept_new_parameters[key]))
            except:
                thellier_interpreter_log.write("-I- %s=%s"%(key,self.accept_new_parameters[key]))
                                            
        for key in [key for key in self.accept_new_parameters.keys() if "specimen" in key]:
            try:
                thellier_interpreter_log.write("-I- %s=%.2f"%(key,self.accept_new_parameters[key]))
            except:
                thellier_interpreter_log.write("-I- %s=%s"%(key,self.accept_new_parameters[key]))
               
                                  

        
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
            specimen_n=int(self.accept_new_parameters['specimen_n'])
            for tmin_i in range(len(temperatures)-specimen_n+1):
                for tmax_i in range(tmin_i+specimen_n-1,len(temperatures)):
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
                        if "AC_specimen_correction_factor" in pars.keys():
                           String=String+"%.2f\t"%float(pars["AC_specimen_correction_factor"])
                        else:
                           String=String+"-\t"
                        if  float(pars["NLT_specimen_correction_factor"])!=-999:
                           String=String+"%.2f\t"%float(pars["NLT_specimen_correction_factor"])
                        else:
                           String=String+"-\t"
##                            if "NLTC_specimen_int" in  pars.keys():
##                               Bancient=float(pars["NLTC_specimen_int"])
##                            elif  "AC_specimen_int" in pars.keys():
##                               Bancient=float(pars["AC_specimen_int"])
##                            else:
##                               Bancient=float(pars["specimen_int"])                   
                        Bancient=float(pars['specimen_int_uT'])
                        String=String+"%.1f\t"%(Bancient)

                        for key in accept_specimen_keys:
                           String=String+"%.2f"%(pars[key])+"\t"
                        String=String[:-1]+"\n"

                        thellier_interpreter_all.write(String)


                        #-------------------------------------------------                    
                        # save 'acceptable' (grade A) specimen interpretaion
                        #-------------------------------------------------
                        
                        if s not in All_grade_A_Recs.keys():
                           All_grade_A_Recs[s]={}
                        new_pars={}
                        for k in pars.keys():
                            new_pars[k]=pars[k]
                        TEMP="%.0f,%.0f"%(float(pars["measurement_step_min"])-273,float(pars["measurement_step_max"])-273)
                        All_grade_A_Recs[s][TEMP]=new_pars
##                        print "================="
##                        for TEMP in All_grade_A_Recs[s].keys():
##                            print TEMP
##                            print All_grade_A_Recs[s][TEMP]
##                            #raw_input("+++")


        specimens_list=All_grade_A_Recs.keys()
        specimens_list.sort()
        Grade_A_samples={}
        Redo_data_specimens={}

        
        #--------------------------------------------------------------
        # specimens bound file
        #--------------------------------------------------------------



        for s in specimens_list:

            sample=self.Data_hierarchy['specimens'][s]
            B_lab=float(self.Data[s]['lab_dc_field'])*1e6
            B_min,B_max=1e10,0.
            NLT_factor_min,NLT_factor_max=1e10,0.
            all_B_tmp_array=[]

            for TEMP in All_grade_A_Recs[s].keys():
                pars=All_grade_A_Recs[s][TEMP]
##                    if "NLTC_specimen_int" in rec.keys():
##                        B_anc=float(rec["NLTC_specimen_int"])*1e6
##                    elif  "AC_specimen_int" in rec.keys():
##                        B_anc=float(rec["AC_specimen_int"])*1e6
##                    else:
##                        #B_anc=float(rec["specimen_int"])*1e6
##                        WARNING="WARNING: No Anistropy correction"
                if "AC_anisotropy_type" in pars.keys():
                    AC_correction_factor=pars["Anisotropy_correction_factor"]
                    AC_correction_type=pars["AC_anisotropy_type"]
                    WARNING=""
                else:
                    AC_correction_factor=1.
                    AC_correction_type="-"
                    WARNING="WARNING: No Anistropy correction"
                
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
                if s not in Redo_data_specimens.keys():
                    Redo_data_specimens[s]={}

                Grade_A_samples[sample][s].append(B_anc)                
                #Redo_data_specimens[s][B_anc]=pars

            # write to specimen_bounds
            #--------------------------------------------------------------

            if pars["NLT_specimen_correction_factor"] != -1:
                NLT_factor="%.2f"%(NLT_factor_max)
            else:
                NLT_factor="-"

            String="%s\t%s\t%.2f\t%s\t%s\t%.1f\t%.1f\t%.1f\t%s\n"\
                    %(sample,s,AC_correction_factor,AC_correction_type,NLT_factor,B_lab,B_min,B_max,WARNING)
            Fout_specimens_bounds.write(String)


        #--------------------------------------------------------------
        # Find the STDEV-OPT 'best mean':
        # the interprettaions that give
        # the minimum standrad deviation.
        #
        #--------------------------------------------------------------

        # Sort all grade A interpretation

        samples=Grade_A_samples.keys()
        samples.sort()

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

        for sample in samples:
            WARNING=""
            # check for outlier specimen
            exclude_specimen=""
            exclude_specimens_list=[]
            if len(Grade_A_samples[sample].keys())>=float(self.accept_new_parameters['sample_int_n_outlier_check']):            
                all_specimens=Grade_A_samples[sample].keys()
                for specimen in all_specimens:
                    B_min_array,B_max_array=[],[]
                    for specimen_b in all_specimens:
                        if specimen_b==specimen: continue
                        B_min_array.append(min(Grade_A_samples[sample][specimen_b]))
                        B_max_array.append(max(Grade_A_samples[sample][specimen_b]))
                    if max(Grade_A_samples[sample][specimen]) < (mean(B_min_array) - 2*std(B_min_array)) and 2*std(B_min_array) >5.:
                        if specimen not in exclude_specimens_list:
                            exclude_specimens_list.append(specimen)
                    if min(Grade_A_samples[sample][specimen]) > (mean(B_max_array) + 2*std(B_max_array)) and 2*std(B_max_array) >5 :
##                           print "Ron, check"
##                           print "excluding specimen",specimen
##                           print "min value",min(Grade_A_samples[sample][specimen])
##                           print "other values:",B_max_array
##                           print "other values std",std(B_max_array)
                           if specimen not in exclude_specimens_list:
                            exclude_specimens_list.append(specimen)
                         
                if len(exclude_specimens_list)>1:
                    #thellier_interpreter_log.write( "-I- checking now if any speimens to exlude due to B_max<average-2*sigma or B_min > average+2*sigma sample %s\n" %s)
                    exclude_specimens_list=[]

                if len(exclude_specimens_list)==1 :
                    #print exclude_specimens_list
                    exclude_specimen=exclude_specimens_list[0]
                    del Grade_A_samples[sample][exclude_specimen]
                    thellier_interpreter_log.write( "-W- WARNING: specimen %s is exluded from sample %s because of an outlier result.\n"%(exclude_specimens_list[0],sample))
                    WARNING=WARNING+"excluding specimen %s; "%(exclude_specimens_list[0])


        #--------------------------------------------------------------
        # calcuate STDEV-OPT 'best means' and write results to files
        #--------------------------------------------------------------

            if self.accept_new_parameters['sample_stdev_opt']:
                n_no_atrm=0
                
                for specimen in Grade_A_samples[sample].keys():
                    if "AniSpec" not in self.Data[specimen].keys():
                        n_no_atrm+=1

                if len(Grade_A_samples[sample].keys())>=self.accept_new_parameters['sample_int_n']:
                    Best_interpretations,best_mean,best_std=find_sample_min_std(Grade_A_samples[sample])
                    sample_acceptable_min,sample_acceptable_max = find_sample_min_max_interpretation (Grade_A_samples[sample],self.accept_new_parameters)
                    sample_int_interval_uT=sample_acceptable_max-sample_acceptable_min
                    sample_int_interval_perc=100*((sample_acceptable_max-sample_acceptable_min)/best_mean)       
                    TEXT= "-I- sample %s 'STDEV-OPT interpretation: "%sample
                    for ss in Best_interpretations.keys():
                        TEXT=TEXT+"%s=%.1f, "%(ss,Best_interpretations[ss])
                    thellier_interpreter_log.write(TEXT+"\n")
                    thellier_interpreter_log.write("-I- sample %s STDEV-OPT mean=%f, STDEV-OPT std=%f \n"%(sample,best_mean,best_std))
                    thellier_interpreter_log.write("-I- sample %s STDEV-OPT minimum/maximum accepted interpretation  %.2f,%.2f\n" %(sample,sample_acceptable_min,sample_acceptable_max))

                    # check if interpretation pass criteria:
                    if ( self.accept_new_parameters['sample_int_sigma_uT'] ==0 and self.accept_new_parameters['sample_int_sigma_perc']==0 ) or \
                       (best_std <= self.accept_new_parameters['sample_int_sigma_uT'] or 100*(best_std/best_mean) <= self.accept_new_parameters['sample_int_sigma_perc']):
                        if sample_int_interval_uT <= self.accept_new_parameters['sample_int_interval_uT'] or sample_int_interval_perc <= self.accept_new_parameters['sample_int_interval_perc']:
                            # write the interpretation to a redo file
                            for specimen in Grade_A_samples[sample].keys():
                                #print Redo_data_specimens[specimen]
                                for TEMP in All_grade_A_Recs[specimen].keys():
                                    if All_grade_A_Recs[specimen][TEMP]['specimen_int_uT']==Best_interpretations[specimen]:
                                        t_min=All_grade_A_Recs[specimen][TEMP]['measurement_step_min']
                                        t_max=All_grade_A_Recs[specimen][TEMP]['measurement_step_max']
                                        
                                #t_min=int(float(Redo_data_specimens[specimen][Best_interpretations[specimen]]['measurement_step_min']))
                                #t_max=int(float(Redo_data_specimens[specimen][Best_interpretations[specimen]]['measurement_step_max']))
                                            
                                        Fout_STDEV_OPT_redo.write("%s\t%i\t%i\n"%(specimen,t_min,t_max))

                                    # write the interpretation to the specimen file
                                        #B_lab=float(Redo_data_specimens[specimen][Best_interpretations[specimen]]['lab_dc_field'])*1e6
                                        B_lab=float(All_grade_A_Recs[specimen][TEMP]['lab_dc_field'])*1e6
                                        sample=All_grade_A_Recs[specimen][TEMP]['er_sample_name']
                                        if 'AC_specimen_correction_factor' in All_grade_A_Recs[specimen][TEMP].keys():
                                            Anisotropy_correction_factor="%.2f"%float(All_grade_A_Recs[specimen][TEMP]['AC_specimen_correction_factor'])
                                        else:
                                            Anisotropy_correction_factor="-"                
                                        if  All_grade_A_Recs[specimen][TEMP]["NLT_specimen_correction_factor"] != -1:
                                            NLT_correction_factor="%.2f"%float(All_grade_A_Recs[specimen][TEMP]['NLT_specimen_correction_factor'])
                                        else:
                                            NLT_correction_factor="-"
                                        Fout_STDEV_OPT_specimens.write("%s\t%s\t%.2f\t%i\t%i\t%.0f\t%s\t%s\t"\
                                                             %(sample,specimen,float(Best_interpretations[specimen]),t_min-273,t_max-273,B_lab,Anisotropy_correction_factor,NLT_correction_factor))
                                        String=""
                                        for key in accept_specimen_keys:
                                            String=String+"%.2f"%(All_grade_A_Recs[specimen][TEMP][key])+"\t"
                                        Fout_STDEV_OPT_specimens.write(String[:-1]+"\n")
                                                     
                            # write the interpretation to the sample file
                          
                            if n_no_atrm>0:
                                 WARNING=WARNING+"% i specimens with no anisotropy correction; "%int(n_no_atrm)
                            String="%s\t%i\t%.2f\t%.2f\t%.3f\t%.2f\t%.2f\t%s\n"%(sample,len(Best_interpretations),best_mean,best_std,100*(best_std/best_mean),sample_int_interval_uT,sample_int_interval_perc,WARNING)
                            Fout_STDEV_OPT_samples.write(String)
                        else:
                         thellier_interpreter_log.write("-I- sample %s FAIL on sample_int_interval_uT or sample_int_interval_perc\n"%sample)                    
                    else:
                         thellier_interpreter_log.write("-I- sample %s FAIL on sample_int_sigma_uT or sample_int_sigma_perc\n"%sample)
                                                                            
        #--------------------------------------------------------------
        # calcuate Bootstarp and write results to files
        #--------------------------------------------------------------

            if self.accept_new_parameters['sample_bs'] or self.accept_new_parameters['sample_bs_par']:
               BOOTSTRAP_N=1000
               Grade_A_samples_BS={} 
               if len(Grade_A_samples[sample].keys()) >= self.accept_new_parameters['sample_int_n']:
                   for specimen in Grade_A_samples[sample].keys():
                        if specimen not in Grade_A_samples_BS.keys() and len(Grade_A_samples[sample][specimen])>0:
                           Grade_A_samples_BS[specimen]=[]
                        for B in Grade_A_samples[sample][specimen]:
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
                           if self.accept_new_parameters['sample_bs']:
                               B=random.choice(Grade_A_samples_BS[specimen])
                           if self.accept_new_parameters['sample_bs_par']:
                               B=random.uniform(min(Grade_A_samples_BS[specimen]),max(Grade_A_samples_BS[specimen]))
                           B_BS.append(B)
                       BS_means_collection.append(mean(B_BS))
                       
                   BS_means=array(BS_means_collection)
                   BS_means.sort()
                   sample_median=median(BS_means)
                   sample_std=std(BS_means)
                   sample_68=[BS_means[(0.16)*len(BS_means)],BS_means[(0.84)*len(BS_means)]]
                   sample_95=[BS_means[(0.025)*len(BS_means)],BS_means[(0.975)*len(BS_means)]]


                   thellier_interpreter_log.write( "-I-  bootstrap mean sample %s: median=%f, std=%f\n"%(sample,sample_median,sample_std))
                   String="%s\t%i\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t%s\n"%\
                           (sample,len(Grade_A_samples[sample].keys()),sample_median,sample_68[0],sample_68[1],sample_95[0],sample_95[1],sample_std,100*(sample_std/sample_median),WARNING)
                   if self.accept_new_parameters['sample_bs']:
                       Fout_BS_samples.write(String)
                   if self.accept_new_parameters['sample_bs_par']:
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
        if self.accept_new_parameters['sample_stdev_opt']: 
            Fout_STDEV_OPT_redo.close()
            Fout_STDEV_OPT_specimens.close()
            Fout_STDEV_OPT_samples.close()
        if self.accept_new_parameters['sample_bs']:
            Fout_BS_samples.close()
        if self.accept_new_parameters['sample_bs_par']:
            Fout_BS_PAR_samples.close()
            

            

        if  self.accept_new_parameters['sample_stdev_opt']:
            self.read_redo_file(self.WD+"/thellier_interpreter/thellier_interpreter_STDEV-OPT_redo")
        dlg1 = wx.MessageDialog(self,caption="Message:", message="Interpreter finished sucsessfuly\nCheck output files in folder /thellier_interpreter in the current project directory" ,style=wx.OK|wx.ICON_INFORMATION)
    
        #except:
        #    dlg1 = wx.MessageDialog(self,caption="Error:", message="Interpreter finished with Errors" ,style=wx.OK)

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
        """
        Write new acceptance criteria to pmag_criteria.txt
        """

        fout=open(self.WD+"/"+"pmag_criteria.txt",'w')
        String="tab\tpmag_criteria\n"
        fout.write(String)
        specimen_criteria_list=self.criteria_list+["specimen_int_max_slope_diff"]
        sample_criteria_list=[key for key in self.accept_new_parameters.keys() if "sample" in key]
        if self.accept_new_parameters['sample_stdev_opt'] == True:                                      
            for k in ['sample_bs','sample_bs_par','sample_int_BS_68_uT','sample_int_BS_68_perc','sample_int_BS_95_uT','sample_int_BS_95_perc']:
                sample_criteria_list.remove(k)
                if "specimen_int_max_slope_diff" in specimen_criteria_list:
                    specimen_criteria_list.remove("specimen_int_max_slope_diff")
        else:
            for k in ['sample_int_sigma_uT','sample_int_sigma_perc','sample_int_interval_uT','sample_stdev_opt']:
                sample_criteria_list.remove(k)
        for k in ['sample_int_sigma_uT','sample_int_sigma_perc','sample_int_interval_uT','sample_int_interval_perc','sample_int_BS_68_uT','sample_int_BS_68_perc','sample_int_BS_95_uT','sample_int_BS_95_perc']:
            if  k in sample_criteria_list:
                if float(self.accept_new_parameters[k]) > 999:
                    sample_criteria_list.remove(k)

        if "specimen_int_max_slope_diff" in  specimen_criteria_list:
            if float(self.accept_new_parameters['specimen_int_max_slope_diff'])>999:
                specimen_criteria_list.remove("specimen_int_max_slope_diff")
                
        for criteria in specimen_criteria_list:
            if criteria in self.high_threshold_velue_list and float(self.accept_new_parameters[criteria])>100:
                specimen_criteria_list.remove(criteria)
            if criteria in self.low_threshold_velue_list and float(self.accept_new_parameters[criteria])<0.1:
                specimen_criteria_list.remove(criteria)                

        header=""
        for key in sample_criteria_list:
            header=header+key+"\t"
        for key in specimen_criteria_list:
            header=header+key+"\t"
        fout.write(header+"specimen_scat\n")

        line=""
        for key in sample_criteria_list:
            if key in ['sample_bs','sample_bs_par','sample_stdev_opt']:
                line=line+"%s"%str(self.accept_new_parameters[key])+"\t"
            else:
                line=line+"%f"%self.accept_new_parameters[key]+"\t"
                
        for key in specimen_criteria_list:
            line=line+"%f"%self.accept_new_parameters[key]+"\t"
        if self.accept_new_parameters["specimen_scat"]:
            line=line+"True"+"\t"
        else:
            line=line+"False"+"\t"
            
        fout.write(line[:-1]+"\n")
        fout.close()
        
        
    #----------------------------------------------------------------------            

    def on_menu_run_optimizer(self, event):
        self.GUI_log.write ("-I- running thellier_optimizer_2D\n")
        

        Optimizer(self.Data,self.Data_hierarchy,self.WD,self.accept_new_parameters_default)
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
        

    def On_close_plot_dialog(self,dia):
        #figure(1)
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

        plot_by_locations={}
        #X_data,X_data_plus,X_data_minus=[],[],[]
        #Y_data,Y_data_plus,Y_data_minus=[],[],[]
        samples_names=[]
        
        # search for ages:
        for sample in self.Data_samples.keys():
            found_age,found_lat=False,False
            #print "check", sample,self.Data_samples[sample]
            tmp_B=[]
            for spec in self.Data_samples[sample].keys():
                tmp_B.append( self.Data_samples[sample][spec])
            if len(tmp_B)<1:
                continue
            tmp_B=array(tmp_B)
            B_uT=mean(tmp_B)
            B_std_uT=std(tmp_B)
            B_std_perc=100*(B_std_uT/B_uT)
            #print "tmp_B",tmp_B,B_uT,B_std_uT,B_std_perc

            if len(tmp_B)>=self.accept_new_parameters['sample_int_n']:
                if (self.accept_new_parameters['sample_int_sigma_uT']==0 and self.accept_new_parameters['sample_int_sigma_perc']==0) or\
                   ( B_std_uT <=self.accept_new_parameters['sample_int_sigma_uT'] or B_std_perc <= self.accept_new_parameters['sample_int_sigma_perc']):
                    if ( (max(tmp_B)-min(tmp_B)) <= self.accept_new_parameters['sample_int_interval_uT'] or 100*((max(tmp_B)-min(tmp_B))/mean(std(tmp_B))) <= self.accept_new_parameters['sample_int_interval_perc']):
                        #print "check, sample %s pass criteria"%sample
                        if sample in self.Data_info["er_ages"].keys():
                            Age = float(self.Data_info["er_ages"][sample]["age"])
                            age_unit=self.Data_info["er_ages"][sample]["age_unit"]
                            
                            if "age_range_low" in self.Data_info["er_ages"][sample].keys() and "age_range_high" in self.Data_info["er_ages"][sample].keys():
                               X_minus=Age-float(self.Data_info["er_ages"][sample]["age_range_low"])
                               X_plus=float(self.Data_info["er_ages"][sample]["age_range_high"])-Age
                            elif "age_sigma" in self.Data_info["er_ages"][sample].keys():
                               X_minus=float(self.Data_info["er_ages"][sample]["age_sigma"])
                               X_plus= float(self.Data_info["er_ages"][sample]["age_sigma"])
                            else:
                               X_minus,X_plus=0,0
                            
                            found_age=True
                        else:
                            site = self.Data_info["er_samples"][sample]['er_site_name']
                            #print "site",site
                            if  site in self.Data_info["er_ages"].keys():
                                Age = float(self.Data_info["er_ages"][site]["age"])
                                age_unit=self.Data_info["er_ages"][site]["age_unit"]
                                if "age_range_low" in self.Data_info["er_ages"][site].keys() and "age_range_high" in self.Data_info["er_ages"][site].keys():
                                   X_minus=Age-float(self.Data_info["er_ages"][site]["age_range_low"])
                                   X_plus=float(self.Data_info["er_ages"][site]["age_range_high"])-Age
                                elif "age_sigma" in self.Data_info["er_ages"][site].keys():
                                   X_minus=float(self.Data_info["er_ages"][site]["age_sigma"])
                                   X_plus= float(self.Data_info["er_ages"][site]["age_sigma"])
                                else:
                                    X_minus,X_plus=0,0
                                found_age=True
                        site = self.Data_info["er_samples"][sample]['er_site_name']
                        if site in self.Data_info["er_sites"].keys() and "site_lat" in self.Data_info["er_sites"][site].keys():
                            lat=float(self.Data_info["er_sites"][site]["site_lat"])
                            lon=float(self.Data_info["er_sites"][site]["site_lon"])

                            found_lat=True

                        location="unknown"
                        try: 
                            if site in self.Data_info["er_sites"].keys():
                                location=self.Data_info["er_sites"][site]["er_location_name"]
                        except:
                            location="unknown"
                            
                        if found_age:
                            
                            if plt_x_years and age_unit=='Years BP':
                                Age=1950-Age
                            if plt_x_BP and "Years Cal" in age_unit:
                                if Age >0:
                                    Age=1950-Age
                                else:
                                    Age=Age-1950


                            if location not in plot_by_locations.keys():
                                plot_by_locations[location]={}
                                plot_by_locations[location]['X_data'],plot_by_locations[location]['Y_data']=[],[]
                                plot_by_locations[location]['X_data_plus'],plot_by_locations[location]['Y_data_plus']=[],[]
                                plot_by_locations[location]['X_data_minus'],plot_by_locations[location]['Y_data_minus']=[],[]
                                plot_by_locations[location]['samples_names']=[]
                                plot_by_locations[location]['site_lon'],plot_by_locations[location]['site_lat']=[],[]
                                lat_min,lat_max,lon_min,lon_max=lat,lat,lon,lon
                            plot_by_locations[location]['site_lon']=lon
                            plot_by_locations[location]['site_lat']=lat
                            plot_by_locations[location]['X_data'].append(Age)
                            plot_by_locations[location]['X_data_plus'].append(X_plus)
                            plot_by_locations[location]['X_data_minus'].append(X_minus)
                            lat_min,lat_max=min(lat_min,lat),max(lat_max,lat)
                            lon_min,lon_max=min(lon_min,lat),max(lon_max,lat)
                            if  plt_B:
                                plot_by_locations[location]['Y_data'].append(B_uT)
                                plot_by_locations[location]['Y_data_plus'].append(B_std_uT)
                                plot_by_locations[location]['Y_data_minus'].append(B_std_uT)
                                plot_by_locations[location]['samples_names'].append(sample)
                                
                            elif plt_VADM and found_lat: # units of ZAm^2
                                VADM=pmag.b_vdm(B_uT*1e-6,lat)*1e-21
                                VADM_plus=pmag.b_vdm((B_uT+B_std_uT)*1e-6,lat)*1e-21
                                VADM_minus=pmag.b_vdm((B_uT-B_std_uT)*1e-6,lat)*1e-21
                                plot_by_locations[location]['Y_data'].append(VADM)
                                plot_by_locations[location]['Y_data_plus'].append(VADM_plus-VADM)
                                plot_by_locations[location]['Y_data_minus'].append(VADM-VADM_minus)
                                plot_by_locations[location]['samples_names'].append(sample)
                                
                            found_age=False
                            found_lat=False
                            
        #print "plot_data",X_data,Y_data,X_data_minus,X_data_plus                                               
        Fig=figure(1,(14,6))
        clf()
        ax = axes([0.3,0.1,0.6,0.8])
        #errorbar(X_data,Y_data,xerr=[X_data_minus,X_data_plus],yerr=[Y_data_minus,Y_data_plus])
        locations =plot_by_locations.keys()
        locations.sort()
        #counter=0
        #legend_labels=[]


        #----
        # map

        # read in topo data (on a regular lat/lon grid)
        # longitudes go from 20 to 380.
        Plot_map=False
        if Plot_map:
            topodatin = np.loadtxt('etopo20data.gz')
            lonsin = np.loadtxt('etopo20lons.gz')
            latsin = np.loadtxt('etopo20lats.gz')

            # draw parallels
            delat = 30.
            circles = np.arange(0.,90.+delat,delat).tolist()+\
                      np.arange(-delat,-90.-delat,-delat).tolist()

            delon = 60.
            meridians = np.arange(-180,180,delon)

            # shift data so lons go from -180 to 180 instead of 20 to 380.
            topoin,lons = shiftgrid(180.,topodatin,lonsin,start=False)
            lats = latsin

            # create new figure
            ion()
            fig2=figure(2)
            ioff()

            SiteLat_min=lat_min-5
            SiteLat_max=lat_max+5
            SiteLon_min=lon_min-5
            SiteLon_max=lon_max+5

            m=Basemap(llcrnrlon=SiteLon_min,llcrnrlat=SiteLat_min,urcrnrlon=SiteLon_max,urcrnrlat=SiteLat_max,projection='merc',resolution='i')

            #m.drawparallels(arange(SiteLat_min,SiteLat_max+5,5),labels=[1,0,0,0],linewidth=0.2)
            #m.drawmeridians(arange(SiteLon_min,SiteLon_max+5,5),labels=[0,0,1,0],linewidth=0.2)

            #m=Basemap(llcrnrlon=SiteLon_min,llcrnrlat=SiteLat_min,urcrnrlon=SiteLon_max,urcrnrlat=SiteLat_max,projection='merc',resolution='l')
            ###x1,y1=m([30],[30])

            m.fillcontinents(zorder=0,color='0.9')
            m.drawcoastlines()
            m.drawcountries()
            m.drawmapboundary()
        
        for location in locations:
            figure(1)
            X_data,X_data_minus,X_data_plus=plot_by_locations[location]['X_data'],plot_by_locations[location]['X_data_minus'],plot_by_locations[location]['X_data_plus']
            Y_data,Y_data_minus,Y_data_plus=plot_by_locations[location]['Y_data'],plot_by_locations[location]['Y_data_minus'],plot_by_locations[location]['Y_data_plus']
            errorbar(X_data,Y_data,xerr=[array(X_data_minus),array(X_data_plus)],yerr=[Y_data_minus,Y_data_plus],fmt='s',label=location)
            if Plot_map:
                figure(2)
                lat=plot_by_locations[location]['site_lat']
                lon=plot_by_locations[location]['site_lon']
##                print "lonlat", lon,lat
                x1,y1=m([lon],[lat])
                m.scatter(x1,y1,s=[50],marker="o")
        figure(1)
        #figtext(0.05,0.95,"N=%i"%len(X_data))
        legend_font_props = matplotlib.font_manager.FontProperties()
        legend_font_props.set_size(12)

        h,l = ax.get_legend_handles_labels()
        Fig.legend(h,l,loc='center left',fancybox="True",numpoints=1,prop=legend_font_props)

        ylim(ymin=0)

        if plt_VADM:
            #ylabel("VADM ZAm^2")
            ax.set_ylabel(r'VADM  $Am^2$',fontsize=12)

        if plt_B:
            #ylabel("B (microT)")
            ax.set_ylabel(r'B  $\mu T$',fontsize=12)
        if plt_x_BP:
            #xlabel("years BP")
            ax.set_xlabel("years BP",fontsize=12)
        if plt_x_years:
            #xlabel("Date")
            ax.set_xlabel("Date",fontsize=12)
        
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
        start_time = time.time()


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

        self.araiplot.clear()        
        self.araiplot.plot(self.Data[self.s]['x_Arai'],self.Data[self.s]['y_Arai'],'0.2',lw=0.75)

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
            self.araiplot.scatter (self.x_Arai_ZI,self.y_Arai_ZI,marker='o',facecolor='r',edgecolor ='k',s=25)
        if len(self.x_Arai_IZ)>0:
            self.araiplot.scatter (self.x_Arai_IZ,self.y_Arai_IZ,marker='o',facecolor='b',edgecolor ='k',s=25)

        # pTRM checks
        if 'x_ptrm_check' in self.Data[self.s]:
            if len(self.Data[self.s]['x_ptrm_check'])>0:
                self.araiplot.scatter (self.Data[self.s]['x_ptrm_check'],self.Data[self.s]['y_ptrm_check'],marker='^',edgecolor='0.1',alpha=1.0, facecolor='None',s=80,lw=1)

        # Tail checks
        if len(self.x_tail_check >0):
          self.araiplot.scatter (self.x_tail_check,self.y_tail_check,marker='s',edgecolor='0.1',alpha=1.0, facecolor='None',s=80,lw=1)

        for i in range(len(self.Data[self.s]['t_Arai'])):
          if self.Data[self.s]['t_Arai'][i]!=0:
            self.tmp_c=self.Data[self.s]['t_Arai'][i]-273.
          else:
            self.tmp_c=0.
            
          self.araiplot.text(self.x_Arai[i],self.y_Arai[i],"  %.0f"%self.tmp_c,fontsize=10,color='gray',ha='left',va='center')
        self.araiplot.set_xlabel("TRM / NRM$_0$",fontsize=10)
        self.araiplot.set_ylabel("NRM / NRM$_0$",fontsize=10)
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

        start_time_2=time.time() 
        runtime_sec2 = start_time_2 - start_time
        #print "-I- draw Arai figures is", runtime_sec2,"seconds"

        #-----------------------------------------------------------
        # Draw Zij plot
        #-----------------------------------------------------------

        self.zijplot.clear()
        self.MS=6;self.dec_MEC='k';self.dec_MFC='b'; self.inc_MEC='k';self.inc_MFC='r'
        self.CART_rot=self.Data[self.s]['zij_rotated']
        self.z_temperatures=self.Data[self.s]['z_temp']
        self.vds=self.Data[self.s]['vds']
        self.zijplot.plot(self.CART_rot[:,0],-1* self.CART_rot[:,1],'bo-',mfc=self.dec_MFC,mec=self.dec_MEC,markersize=self.MS)  #x,y or N,E
        self.zijplot.plot(self.CART_rot[:,0],-1 * self.CART_rot[:,2],'rs-',mfc=self.inc_MFC,mec=self.inc_MEC,markersize=self.MS)   #x-z or N,D
        self.zijplot.axhline(0,c='k')
        self.zijplot.axvline(0,c='k')
        self.zijplot.axis('off')
        self.zijplot.axis('equal')
        #title(Data[s]['pars']['er_specimen_name']+"\nrotated Zijderveld plot",fontsize=12)
        last_cart_1=array([self.CART_rot[0][0],self.CART_rot[0][1]])
        last_cart_2=array([self.CART_rot[0][0],self.CART_rot[0][2]])

        for i in range(len(self.z_temperatures)):
          self.zijplot.text(self.CART_rot[i][0],-1*self.CART_rot[i][2]," %.0f"%(self.z_temperatures[i]-273.),fontsize=10,color='gray',ha='left',va='center')   #inc
        self.canvas2.draw()
        
        start_time_3=time.time() 
        runtime_sec3 = start_time_3 - start_time_2
        #print "-I- draw Zij figures is", runtime_sec3,"seconds"

        #-----------------------------------------------------------
        # Draw Equal area plot
        #-----------------------------------------------------------

        self.draw_net()

        self.zij=array(self.Data[self.s]['zdata'])
        self.zij_norm=array([row/sqrt(sum(row**2)) for row in self.zij])

        x_eq=array([row[0] for row in self.zij_norm])
        y_eq=array([row[1] for row in self.zij_norm])
        z_eq=abs(array([row[2] for row in self.zij_norm]))
        R=array(sqrt(1-z_eq)/sqrt(x_eq**2+y_eq**2)) # from Collinson 1983
        eqarea_data_x=y_eq*R
        eqarea_data_y=x_eq*R
        #self.eqplot.scatter([eqarea_data_x_dn[i]],[eqarea_data_y_dn[i]],marker='o',edgecolor='0.1', facecolor='blue',s=15,lw=1)


        x_eq_dn,y_eq_dn,z_eq_dn=[],[],[]
        x_eq_dn=array([row[0] for row in self.zij_norm if row[2]>0])
        y_eq_dn=array([row[1] for row in self.zij_norm if row[2]>0])
        z_eq_dn=abs(array([row[2] for row in self.zij_norm if row[2]>0]))
        if len(x_eq_dn)>0:
            R=array(sqrt(1-z_eq_dn)/sqrt(x_eq_dn**2+y_eq_dn**2)) # from Collinson 1983
            eqarea_data_x_dn=y_eq_dn*R
            eqarea_data_y_dn=x_eq_dn*R
            self.eqplot.scatter([eqarea_data_x_dn],[eqarea_data_y_dn],marker='o',edgecolor='0.1', facecolor='blue',s=15,lw=1)

        x_eq_up,y_eq_up,z_eq_up=[],[],[]
        x_eq_up=array([row[0] for row in self.zij_norm if row[2]<=0])
        y_eq_up=array([row[1] for row in self.zij_norm if row[2]<=0])
        z_eq_up=abs(array([row[2] for row in self.zij_norm if row[2]<=0]))
        if len(x_eq_up)>0:
            R=array(sqrt(1-z_eq_up)/sqrt(x_eq_up**2+y_eq_up**2)) # from Collinson 1983
            eqarea_data_x_up=y_eq_up*R
            eqarea_data_y_up=x_eq_up*R
            self.eqplot.scatter([eqarea_data_x_up],[eqarea_data_y_up],marker='o',edgecolor='blue', facecolor='white',s=15,lw=1)        

        
        self.eqplot.text(eqarea_data_x[0],eqarea_data_y[0]," NRM",fontsize=8,color='gray',ha='left',va='center')

        draw()
        self.canvas3.draw()

        start_time_4=time.time() 
        runtime_sec4 = start_time_4 - start_time_3
        #print "-I- draw eqarea figures is", runtime_sec4,"seconds"

        #-----------------------------------------------------------
        # Draw sample plot
        #-----------------------------------------------------------


        self.sampleplot.clear()
        specimens_id=[]
        specimens_B=[]
        sample=self.Data_hierarchy['specimens'][self.s]
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

        if len(specimens_id)>1:
            self.sampleplot.scatter(arange(len(specimens_id)),specimens_B ,marker='s',edgecolor='0.2', facecolor='b',s=40,lw=1)
            self.sampleplot.axhline(y=mean(specimens_B)+std(specimens_B),color='0.2',ls="--",lw=0.75)
            self.sampleplot.axhline(y=mean(specimens_B)-std(specimens_B),color='0.2',ls="--",lw=0.75)
            self.sampleplot.axhline(y=mean(specimens_B),color='0.2',ls="-",lw=0.75,alpha=0.5)
            
            if self.s in specimens_id:
                self.sampleplot.scatter([specimens_id.index(self.s)],[specimens_B[specimens_id.index(self.s)]] ,marker='s',edgecolor='0.2', facecolor='r',s=40,lw=1)

            self.sampleplot.set_xticks(arange(len(specimens_id)))
            self.sampleplot.set_xlim(-0.5,len(specimens_id)-0.5)
            self.sampleplot.set_xticklabels(specimens_id,rotation=90,fontsize=8)

            self.sampleplot.set_ylabel(r'$\mu$ T',fontsize=8)
            self.sampleplot.tick_params(axis='both', which='major', labelsize=8)
        self.canvas4.draw()
        start_time_5=time.time() 
        runtime_sec5 = start_time_5 - start_time_4

            

##        self.sampleplot.clear()
##        specimens_id=[]
##        specimens_B=[]
##        #sample=[k for k, v in self.Data_hierarchy.iteritems() if  self.s in v][0]
##        sample=self.Data_hierarchy['specimens'][self.s]
##        #self.Data_hierarchy[sample].sort
##        specimens_list=sorted(self.Data_hierarchy['samples'][sample], key=lambda line: line.rsplit(sample, 1)[-1])
##        for other_specimen in specimens_list:
##            if 'pars' in self.Data[other_specimen]:
##                if 'specimen_int_uT' in self.Data[other_specimen]['pars']:
##                    specimens_id.append(other_specimen)
##                    specimens_B.append(self.Data[other_specimen]['pars']['specimen_int_uT'])
##        
##        if len(specimens_B)>1:
##
##            self.sampleplot.scatter(arange(len(specimens_id)),specimens_B ,marker='s',edgecolor='0.2', facecolor='b',s=40,lw=1)
##
##            self.sampleplot.axhline(y=mean(specimens_B)+std(specimens_B),color='0.2',ls="--",lw=0.75)
##            self.sampleplot.axhline(y=mean(specimens_B)-std(specimens_B),color='0.2',ls="--",lw=0.75)
##            self.remember_last_sample=sample            
##            
##            if self.s in specimens_id:
##                self.sampleplot.scatter([specimens_id.index(self.s)],[specimens_B[specimens_id.index(self.s)]] ,marker='s',edgecolor='0.2', facecolor='r',s=40,lw=1)
##
##            self.sampleplot.set_xticks(arange(len(specimens_id)))
##            self.sampleplot.set_xlim(-0.5,len(specimens_id)-0.5)
##            self.sampleplot.set_xticklabels(specimens_id,rotation=90,fontsize=8)
##
##            
##            #ax.xaxis.set_major_formatter(FormatStrFormatter('%0.1f'))
##        self.sampleplot.set_ylabel("microT",fontsize=8)
##        self.sampleplot.tick_params(axis='both', which='major', labelsize=8)
##        self.canvas4.draw()
##        start_time_5=time.time() 
##        runtime_sec5 = start_time_5 - start_time_4
##        #print "-I- draw sample figures is", runtime_sec5,"seconds"
##        
        #-----------------------------------------------------------
        # Draw M/M0 plot
        #-----------------------------------------------------------

        self.mplot.clear()
        NRMS=self.Data[self.s]['NRMS']
        PTRMS=self.Data[self.s]['PTRMS']

        temperatures_NRMS=array([row[0]-273. for row in NRMS])
        temperatures_PTRMS=array([row[0]-273. for row in PTRMS])
        temperatures_NRMS[0]=21
        temperatures_PTRMS[0]=21
        
        if len(temperatures_NRMS)!=len(temperatures_PTRMS):
          self.GUI_log.write("-E- ERROR: NRMS and pTRMS are not equal in specimen %s. Check\n."%self.s)
        else:
          M_NRMS=array([row[3] for row in NRMS])/NRMS[0][3]
          M_pTRMS=array([row[3] for row in PTRMS])/NRMS[0][3]

          self.mplot.clear()
          self.mplot.plot(temperatures_NRMS,M_NRMS,'bo-',mec='0.2',markersize=5,lw=1)
          self.mplot.plot(temperatures_NRMS,M_pTRMS,'ro-',mec='0.2',markersize=5,lw=1)
          self.mplot.set_xlabel("C",fontsize=8)
          self.mplot.set_ylabel("M / NRM$_0$",fontsize=8)
          #self.mplot.set_xtick(labelsize=2)
          self.mplot.tick_params(axis='both', which='major', labelsize=8)
          #self.mplot.tick_params(axis='x', which='major', labelsize=8)          
          self.mplot.spines["right"].set_visible(False)
          self.mplot.spines["top"].set_visible(False)
          self.mplot.get_xaxis().tick_bottom()
          self.mplot.get_yaxis().tick_left()
          
          xt=xticks()
          self.canvas5.draw()

        start_time_6=time.time() 
        runtime_sec6 = start_time_6 - start_time_5
        #print "-I- draw M-M0 figures is", runtime_sec6,"seconds"

        runtime_sec = time.time() - start_time
        #print "-I- draw figures is", runtime_sec,"seconds"
        

    def draw_net(self):
        self.eqplot.clear()
        eq=self.eqplot
        eq.axis((-1,1,-1,1))
        eq.axis('off')
        theta=arange(0.,2*pi,2*pi/1000)
        eq.plot(cos(theta),sin(theta),'k')
        eq.vlines((0,0),(0.9,-0.9),(1.0,-1.0),'k')
        eq.hlines((0,0),(0.9,-0.9),(1.0,-1.0),'k')
        eq.plot([0.0],[0.0],'+k')

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

        self.tmin_box.SetValue("%.0f"%(float(self.pars['measurement_step_min'])-273.))
        self.tmax_box.SetValue("%.0f"%(float(self.pars['measurement_step_max'])-273.))
        
        # First,re-draw the figures
        self.draw_figure(s)

        # now draw the interpretation
        self.draw_interpretation()

        # declination/inclination
        self.declination_window.SetValue("%.1f"%(self.pars['specimen_dec']))
        self.inclination_window.SetValue("%.1f"%(self.pars['specimen_inc']))


         
        # PI statsistics
        
        window_list=['n','int_ptrm_n','frac','gap_max','f','fvds','b_beta','g','q','int_mad','dang','drats','md']
        high_threshold_velue_list=['specimen_gap_max','specimen_b_beta','specimen_dang','specimen_drats','specimen_int_mad','specimen_md']
        low_threshold_velue_list=['specimen_n','specimen_int_ptrm_n','specimen_f','specimen_fvds','specimen_frac','specimen_g','specimen_q']
        flag_Fail=False
    
        for key in  high_threshold_velue_list+low_threshold_velue_list:
            #if  key == 'specimen_md': cont
            if key in ['specimen_n','specimen_int_ptrm_n']:
                Value="%.0f"%self.pars[key]
            if key in ['specimen_dang','specimen_drats','specimen_int_mad','specimen_md','specimen_g','specimen_q']:
                Value="%.1f"%self.pars[key]
            if key in ['specimen_f','specimen_fvds','specimen_frac','specimen_b_beta','specimen_gap_max']:
                Value="%.2f"%self.pars[key]            
            command= "self.%s_window.SetValue(Value)"%key.split('specimen_')[-1]
            exec(command)

            if self.ignore_parameters[key]:
                command="self.%s_window.SetBackgroundColour(wx.NullColor)"%key.split('specimen_')[-1]  # set text color                
            elif (key in high_threshold_velue_list) and (float(self.pars[key])<=float(self.accept_new_parameters[key])):
                command="self.%s_window.SetBackgroundColour(wx.GREEN)"%key.split('specimen_')[-1]  # set text color
            elif (key in low_threshold_velue_list) and (float(self.pars[key])>=float(self.accept_new_parameters[key])):
                command="self.%s_window.SetBackgroundColour(wx.GREEN)"%key.split('specimen_')[-1]  # set text color
            else:
                command="self.%s_window.SetBackgroundColour(wx.RED)"%key.split('specimen_')[-1]  # set text color
                flag_Fail=True
            exec command    

        # Scat
        if self.accept_new_parameters['specimen_scat']:
            if self.pars["fail_arai_beta_box_scatter"] or self.pars["fail_ptrm_beta_box_scatter"] or self.pars["fail_tail_beta_box_scatter"]:
              self.scat_window.SetValue("fail")
            else:
              self.scat_window.SetValue("pass")

            if self.ignore_parameters['specimen_scat']:
              self.scat_window.SetBackgroundColour(wx.NullColor) # set text color
            elif self.pars["fail_arai_beta_box_scatter"] or self.pars["fail_ptrm_beta_box_scatter"] or self.pars["fail_tail_beta_box_scatter"] :
              self.scat_window.SetBackgroundColour(wx.RED) # set text color
              flag_Fail=True
            else :
              self.scat_window.SetBackgroundColour(wx.GREEN) # set text color
        else:
            self.scat_window.SetValue("")
            self.scat_window.SetBackgroundColour(wx.NullColor) # set text color


        # Banc, correction factor

        self.Banc_window.SetValue("%.1f"%(self.pars['specimen_int_uT']))
        if flag_Fail:
          self.Banc_window.SetBackgroundColour(wx.RED)
        else:
          self.Banc_window.SetBackgroundColour(wx.GREEN)

        if "AniSpec" in self.Data[self.s]:
          self.Aniso_factor_window.SetValue("%.2f"%(self.pars['Anisotropy_correction_factor']))
        else:
          self.Aniso_factor_window.SetValue("None")
        if self.pars['NLT_specimen_correction_factor']!=-1:
          self.NLT_factor_window.SetValue("%.2f"%(self.pars['NLT_specimen_correction_factor']))
        else:
          self.NLT_factor_window.SetValue("None")




                


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
        if float(t2) < float(t1):
          return()

        if float(t2) < float(t1):
          return()

        index_1=self.T_list.index(t1)
        index_2=self.T_list.index(t2)

       
        if (index_2-index_1)+1 >= self.accept_new_parameters['specimen_n']:
            self.pars=self.get_PI_parameters(self.s,float(t1)+273.,float(t2)+273.)
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


        """
        calcualte statisics 
        """
              
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

        # check tmin
        if tmin not in t_Arai or tmin not in z_temperatures:
            return(pars)
        
        # check tmax
        if tmax not in t_Arai or tmin not in z_temperatures:
            return(pars)

        start=t_Arai.index(tmin)
        end=t_Arai.index(tmax)

        if end-start < float(self.accept_new_parameters['specimen_n'] -1):
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
         DIR_PCA=cart2dir(v1*-1)
         best_fit_vector=v1*-1
        else:
         DIR_PCA=cart2dir(v1)
         best_fit_vector=v1

        # MAD Kirschvink (1980)
        MAD=degrees(arctan(sqrt((t2+t3)/t1)))

        # DANG Tauxe and Staudigel 2004
        DANG=degrees( arccos( ( dot(cm, best_fit_vector) )/( sqrt(sum(cm**2)) * sqrt(sum(best_fit_vector**2)))))


        # best fit PCA direction
        pars["specimen_dec"] =  DIR_PCA[0]
        pars["specimen_inc"] =  DIR_PCA[1]
        pars["specimen_PCA_v1"] =  best_fit_vector

        # MAD Kirschvink (1980)
        pars["specimen_int_mad"]=MAD
        pars["specimen_dang"]=DANG


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
        beta_Coe=abs(york_sigma/york_b)

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

        
        pars['specimen_n']=end-start+1
        pars["specimen_b"]=york_b
        pars["specimen_YT"]=y_T       
        pars["specimen_b_sigma"]=york_sigma
        pars["specimen_b_beta"]=beta_Coe
        pars["specimen_f"]=f_Coe
        pars["specimen_fvds"]=f_vds
        pars["specimen_g"]=g_Coe
        pars["specimen_q"]=q_Coe

        pars["specimen_int"]=-1*pars['lab_dc_field']*pars["specimen_b"]

        #-------------------------------------------------
        # pTRM checks:
        # DRAT ()
        # and
        # DRATS (Tauxe and Staudigel 2004)
        #-------------------------------------------------

        x_ptrm_check_in_0_to_end,y_ptrm_check_in_0_to_end,x_Arai_compare=[],[],[]
        x_ptrm_check_in_start_to_end,y_ptrm_check_in_start_to_end=[],[]
        for k in range(len(self.Data[s]['ptrm_checks_temperatures'])):
          if self.Data[s]['ptrm_checks_temperatures'][k]<=pars["measurement_step_max"] and self.Data[s]['ptrm_checks_temperatures'][k] in t_Arai:
            x_ptrm_check_in_0_to_end.append(self.Data[s]['x_ptrm_check'][k])
            y_ptrm_check_in_0_to_end.append(self.Data[s]['y_ptrm_check'][k])
            x_Arai_index=t_Arai.index(self.Data[s]['ptrm_checks_temperatures'][k])
            x_Arai_compare.append(x_Arai[x_Arai_index])
            if self.Data[s]['ptrm_checks_temperatures'][k]>=pars["measurement_step_min"]:
                x_ptrm_check_in_start_to_end.append(self.Data[s]['x_ptrm_check'][k])
                y_ptrm_check_in_start_to_end.append(self.Data[s]['y_ptrm_check'][k])
                
        x_ptrm_check_in_0_to_end=array(x_ptrm_check_in_0_to_end)  
        y_ptrm_check_in_0_to_end=array(y_ptrm_check_in_0_to_end)
        x_Arai_compare=array(x_Arai_compare)
        x_ptrm_check_in_start_to_end=array(x_ptrm_check_in_start_to_end)
        y_ptrm_check_in_start_to_end=array(y_ptrm_check_in_start_to_end)
                                  
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

        for k in range(len(self.Data[s]['tail_check_temperatures'])):
          if self.Data[s]['tail_check_temperatures'][k] in t_Arai:
              if self.Data[s]['tail_check_temperatures'][k]<=pars["measurement_step_max"] and self.Data[s]['tail_check_temperatures'][k] >=pars["measurement_step_min"]:
                   x_tail_check_start_to_end.append(self.Data[s]['x_tail_check'][k]) 
                   y_tail_check_start_to_end.append(self.Data[s]['y_tail_check'][k]) 

        x_tail_check_start_to_end=array(x_tail_check_start_to_end)
        y_tail_check_start_to_end=array(y_tail_check_start_to_end)
        
           
        pars['specimen_md']=-1

        # TO DO !

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


            if len(x_ptrm_check_in_start_to_end) > 0:

              # the two bounding lines
              ymin=intercept1+x_ptrm_check_in_start_to_end*slop1
              ymax=intercept2+x_ptrm_check_in_start_to_end*slop2

              # arrays of "True" or "False"
              check_1=y_ptrm_check_in_start_to_end>ymax
              check_2=y_ptrm_check_in_start_to_end<ymin


              # check if at least one "True" 
              if (sum(check_1)+sum(check_2))>0:
                pars["fail_ptrm_beta_box_scatter"]=True
                #print "check, fail fail_ptrm_beta_box_scatter"
                
            # check if the tail checks data points are in the 'box'


            if len(x_tail_check_start_to_end) > 0:

              # the two bounding lines
              ymin=intercept1+x_tail_check_start_to_end*slop1
              ymax=intercept2+x_tail_check_start_to_end*slop2

              # arrays of "True" or "False"
              check_1=y_tail_check_start_to_end>ymax
              check_2=y_tail_check_start_to_end<ymin


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
        pars['specimen_gap_max']=max_FRAC_gap

        #-------------------------------------------------  
        # Check if specimen pass Acceptance criteria
        #-------------------------------------------------  

        pars['specimen_fail_criteria']=[]
        for key in self.high_threshold_velue_list:
            if pars[key]>float(self.accept_new_parameters[key]):
                pars['specimen_fail_criteria'].append(key)
        for key in self.low_threshold_velue_list:
            if pars[key]<float(self.accept_new_parameters[key]):
                pars['specimen_fail_criteria'].append(key)
        if 'specimen_scat' in pars.keys():
            if pars["specimen_scat"]=="Fail":
                pars['specimen_fail_criteria'].append('specimen_scat')



        #-------------------------------------------------            
        # Calculate anistropy correction factor
        #-------------------------------------------------            

        if "AniSpec" in self.Data[s].keys():
           S_matrix=zeros((3,3),'f')
           S_matrix[0,0]=self.Data[s]['AniSpec']['anisotropy_s1']
           S_matrix[1,1]=self.Data[s]['AniSpec']['anisotropy_s2']
           S_matrix[2,2]=self.Data[s]['AniSpec']['anisotropy_s3']
           S_matrix[0,1]=self.Data[s]['AniSpec']['anisotropy_s4']
           S_matrix[1,0]=self.Data[s]['AniSpec']['anisotropy_s4']
           S_matrix[1,2]=self.Data[s]['AniSpec']['anisotropy_s5']
           S_matrix[2,1]=self.Data[s]['AniSpec']['anisotropy_s5']
           S_matrix[0,2]=self.Data[s]['AniSpec']['anisotropy_s6']
           S_matrix[2,0]=self.Data[s]['AniSpec']['anisotropy_s6']

           TRM_anc_unit=array(pars['specimen_PCA_v1'])/sqrt(pars['specimen_PCA_v1'][0]**2+pars['specimen_PCA_v1'][1]**2+pars['specimen_PCA_v1'][2]**2)
           B_lab_unit=dir2cart([ self.Data[s]['Thellier_dc_field_phi'], self.Data[s]['Thellier_dc_field_theta'],1])
##           print "Quality check"
##           print "phi,thata,1 ",[ self.Data[s]['Thellier_dc_field_phi'], self.Data[s]['Thellier_dc_field_theta'],1]
##           #raw_input("---")
           B_lab_unit=array([0,0,-1])
##           print B_lab_unit
##           print B_anc_unit
##           print "S_matrix",S_matrix
##           print "inv(S_matrix)",inv(S_matrix)
##           print "dot(inv(S_matrix),B_anc_unit)",dot(inv(S_matrix),B_anc_unit)
##           print "norm  dot(inv(S_matrix),B_anc_unit)",linalg.norm(dot(inv(S_matrix),B_anc_unit.transpose()))
##           
##           print "linalg.norm(dot((inv(S_matrix),B_lab_unit.transpose())))",linalg.norm(dot(inv(S_matrix),B_lab_unit))
           Anisotropy_correction_factor=linalg.norm(dot(inv(S_matrix),TRM_anc_unit.transpose()))*norm(dot(S_matrix,B_lab_unit))
           pars["Anisotropy_correction_factor"]=Anisotropy_correction_factor
           #pars["Anisotropy_correction_factor"]= linalg.norm(dot(inv(S_matrix),B_anc_unit.transpose()))/linalg.norm(dot(inv(S_matrix),B_lab_unit))
##           print "aniso_factor", pars["Anisotropy_correction_factor"]
           pars["AC_specimen_int"]= pars["Anisotropy_correction_factor"] * float(pars["specimen_int"])
##           print "aniso_int",pars["AC_specimen_int"]
           
           #AniSpecRec=pmag.doaniscorr(pars,AniSpec)
           #pars["AC_specimen_dec"]=AniSpecRec["specimen_dec"]
           #pars["AC_specimen_inc"]=AniSpecRec["specimen_inc"]
           #pars["AC_specimen_int"]=AniSpecRec["specimen_int"]
           #pars["AC_specimen_int"]=AniSpecRec["specimen_int"]
           #try:
           #    pars["Anisotropy_correction_factor"]=float(pars["AC_specimen_int"])/float(pars["specimen_int"])
           #except:
           #    pars["Anisotropy_correction_factor"]=1.0
           pars["AC_anisotropy_type"]=self.Data[s]['AniSpec']["anisotropy_type"]
           pars["specimen_int_uT"]=float(pars["AC_specimen_int"])*1e6

        else:
           pars["Anisotropy_correction_factor"]=1.0
           pars["specimen_int_uT"]=float(pars["specimen_int"])*1e6

           
        #-------------------------------------------------                    
        # NLT and anisotropy correction together in one equation
        # See Shaar et al (2010), Equation (3)
        #-------------------------------------------------

        if 'NLT_parameters' in self.Data[s].keys():

           alpha=self.Data[s]['NLT_parameters'][0][0]
           beta=self.Data[s]['NLT_parameters'][0][1]
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
           else:
               self.GUI_log.write ("-W- WARNING: problematic NLT mesurements for specimens %s. Cant do NLT calculation. check data\n"%s)
               pars["NLT_specimen_correction_factor"]=-1
        else:
           pars["NLT_specimen_correction_factor"]=-1

        
        return(pars)
        

        
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
        if z>0:
          FC='green';EC='0.1'
        else:
          FC='yellow';EC='green'
        self.eqplot.scatter([eqarea_x],[eqarea_y],marker='s',edgecolor=EC, facecolor=FC,s=50,lw=1)


        draw()
        self.canvas3.draw()


        
    
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


      self.criteria_list=['specimen_n','specimen_int_ptrm_n','specimen_f','specimen_fvds','specimen_frac','specimen_gap_max','specimen_b_beta',
                     'specimen_dang','specimen_drats','specimen_int_mad','specimen_md','specimen_g','specimen_q']
      self.high_threshold_velue_list=['specimen_gap_max','specimen_b_beta','specimen_dang','specimen_drats','specimen_int_mad','specimen_md']
      self.low_threshold_velue_list=['specimen_n','specimen_int_ptrm_n','specimen_f','specimen_fvds','specimen_frac','specimen_g','specimen_q']

      accept_new_parameters_null={}
      accept_new_parameters_default={}
      #  make a list of default parameters

      accept_new_parameters_default['specimen_n']=3
      accept_new_parameters_default['specimen_int_ptrm_n']=2
      accept_new_parameters_default['specimen_f']=0.
      accept_new_parameters_default['specimen_fvds']=0.
      accept_new_parameters_default['specimen_frac']=0.8
      accept_new_parameters_default['specimen_gap_max']=0.6
      accept_new_parameters_default['specimen_b_beta']=0.1
      accept_new_parameters_default['specimen_dang']=100000
      accept_new_parameters_default['specimen_drats']=100000
      accept_new_parameters_default['specimen_int_mad']=5
      accept_new_parameters_default['specimen_md']=100000
      accept_new_parameters_default['specimen_g']=0
      accept_new_parameters_default['specimen_q']=0
      accept_new_parameters_default['specimen_scat']=True

      accept_new_parameters_default['sample_int_n']=3
      accept_new_parameters_default['sample_int_n_outlier_check']=6


      # Sample mean calculation type 
      accept_new_parameters_default['sample_stdev_opt']=True
      accept_new_parameters_default['sample_bs']=False
      accept_new_parameters_default['sample_bs_par']=False

      # STDEV-OPT  
      accept_new_parameters_default['sample_int_sigma_uT']=6
      accept_new_parameters_default['sample_int_sigma_perc']=10
      accept_new_parameters_default['sample_int_interval_uT']=10000
      accept_new_parameters_default['sample_int_interval_perc']=10000

      # BS  
      accept_new_parameters_default['sample_int_BS_68_uT']=10000
      accept_new_parameters_default['sample_int_BS_68_perc']=10000
      accept_new_parameters_default['sample_int_BS_95_uT']=10000
      accept_new_parameters_default['sample_int_BS_95_perc']=10000
      accept_new_parameters_default['specimen_int_max_slope_diff']=10000

      #    
      # NULL  
      for key in ( accept_new_parameters_default.keys()):
          accept_new_parameters_null[key]=accept_new_parameters_default[key]
      accept_new_parameters_default['sample_stdev_opt']=False
      accept_new_parameters_null['specimen_frac']=0
      accept_new_parameters_null['specimen_gap_max']=1000
      accept_new_parameters_null['specimen_b_beta']=10000
      accept_new_parameters_null['specimen_int_mad']=100000
      accept_new_parameters_null['specimen_scat']=False
      accept_new_parameters_null['specimen_int_ptrm_n']=0

      accept_new_parameters_null['sample_int_sigma_uT']=0
      accept_new_parameters_null['sample_int_sigma_perc']=0

      
      #print accept_new_parameters_default
        
      # A list of all acceptance criteria used by program
      accept_specimen_keys=['specimen_n','specimen_int_ptrm_n','specimen_f','specimen_fvds','specimen_frac','specimen_gap_max','specimen_b_beta','specimen_dang','specimen_drats','specimen_int_mad','specimen_md']
      accept_sample_keys=['sample_int_n','sample_int_sigma_uT','sample_int_sigma_perc','sample_int_interval_uT','sample_int_interval_perc']
      
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
      Data_hierarchy['samples']={}
      Data_hierarchy['specimens']={}

      # add dir to dir pathes for interpterer:
      if self.WD not in self.MagIC_directories_list:
          self.MagIC_directories_list.append(self.WD)
      #for dir_path in self.dir_pathes:
      meas_data,file_type=pmag.magic_read(self.magic_file)
      self.GUI_log.write("-I- Read magic file  %s\n"%self.magic_file)

      # get list of unique specimen names
      
      CurrRec=[]
      sids=pmag.get_specs(meas_data) # samples ID's
      
      for s in sids:

          if s not in Data.keys():
              Data[s]={}
              Data[s]['datablock']=[]
              Data[s]['trmblock']=[]

          zijdblock,units=pmag.find_dmag_rec(s,meas_data)
          Data[s]['zijdblock']=zijdblock

          
      for rec in meas_data:
          s=rec["er_specimen_name"]
          sample=rec["er_sample_name"]
          if "magic_method_codes" not in rec.keys():
              rec["magic_method_codes"]=""
          #methods=rec["magic_method_codes"].split(":")
          if "LP-PI-TRM" in rec["magic_method_codes"]:
              Data[s]['datablock'].append(rec)
              if "LT-PTRM-I" in rec["magic_method_codes"] and 'LP-TRM' not in rec["magic_method_codes"]:
                  Data[s]['Thellier_dc_field_uT']=float(rec["treatment_dc_field"])
                  Data[s]['Thellier_dc_field_phi']=float(rec['treatment_dc_field_phi'])
                  Data[s]['Thellier_dc_field_theta']=float(rec['treatment_dc_field_theta'])

          if "LP-TRM" in rec["magic_method_codes"]:
              Data[s]['trmblock'].append(rec)

          if sample not in Data_hierarchy['samples'].keys():
              Data_hierarchy['samples'][sample]=[]
          if s not in Data_hierarchy['samples'][sample]:
              Data_hierarchy['samples'][sample].append(s)

          Data_hierarchy['specimens'][s]=sample

          
                  
      self.specimens=Data.keys()
      self.specimens.sort()

      
      #------------------------------------------------
      # Read anisotropy file from rmag_anisotropy.txt
      #------------------------------------------------

      #if self.WD != "":
      anis_data=[]
      try:
          anis_data,file_type=pmag.magic_read(self.WD+'/rmag_anisotropy.txt')
          self.GUI_log.write( "-I- Anisotropy data read  %s/from rmag_anisotropy.txt\n"%self.WD)
      except:
          self.GUI_log.write("-W- WARNING cant find rmag_anistropy in working directory\n")
          
      for AniSpec in anis_data:
          s=AniSpec['er_specimen_name']

          if s not in Data.keys():
              self.GUI_log.write("-W- WARNING: specimen %s in rmag_anisotropy.txt but not in magic_measurement.txt. Check it !\n"%s)
              continue
          if 'AniSpec' in Data[s].keys():
              self.GUI_log.write("-E- ERROR: more than one anisotropy data for specimen %s Fix it!\n"%s)
          Data[s]['AniSpec']=AniSpec
          
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

      for s in self.specimens:
          datablock = Data[s]['datablock']
          trmblock = Data[s]['trmblock']

          if len(trmblock)<2:
              continue

          B_NLT,M_NLT=[],[]

          # find temperature of NLT acquisition
          NLT_temperature=float(trmblock[0]['treatment_temp'])
          
          # search for baseline in the Data block
          M_baseline=0.
          for rec in datablock:
              if float(rec['treatment_temp'])==NLT_temperature and float(rec['treatment_dc_field'])==0:
                 M_baseline=float(rec['measurement_magn_moment'])
                 
          # search for Blab used in the IZZI experiment (need it for the following calculation)
          found_labfield=False  
          for rec in datablock:  
              if float(rec['treatment_dc_field'])!=0:
                  labfield=float(rec['treatment_dc_field'])
                  found_labfield=True
                  break
          if not found_labfield:
              continue

          for rec in trmblock:

              # if there is a baseline in TRM block, then use it 
              if float(rec['treatment_dc_field'])==0:
                  M_baseline=float(rec['measurement_magn_moment'])
              B_NLT.append(float(rec['treatment_dc_field']))
              M_NLT.append(float(rec['measurement_magn_moment']))
              
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
              B_NLT=append([0.],B_NLT)
              M_NLT=append([0.],M_NLT)
              
              try:
                  # First try to fit tanh function (add point 0,0 in the begining)
                  alpha_0=max(M_NLT)
                  beta_0=2e4
                  popt, pcov = curve_fit(tan_h, B_NLT, M_NLT,p0=(alpha_0,beta_0))
                  M_lab=popt[0]*math.tanh(labfield*popt[1])

                  # Now  fit tanh function to the normalized curve
                  M_NLT_norm=M_NLT/M_lab
                  popt, pcov = curve_fit(tan_h, B_NLT, M_NLT_norm,p0=(popt[0]/M_lab,popt[1]))
                  Data[s]['NLT_parameters']=(popt, pcov)
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
                  
              
      self.GUI_log.write("-I- Done calculating non linear TRM parameters for all specimens\n")
                
      #------------------------------------------------
      # sort Arai block
      #------------------------------------------------


      for s in self.specimens:
        # collected the data
        datablock = Data[s]['datablock']
        zijdblock=Data[s]['zijdblock']

        if len(datablock) <4:
           self.GUI_log.write("-E- ERROR: skipping specimen %s, not enough measurements - moving forward \n"%s)
           del Data[s]
           sample=Data_hierarchy['specimens'][s]
           del Data_hierarchy['specimens'][s]
           Data_hierarchy['samples'][sample].remove(s)
           continue 
        araiblock,field=pmag.sortarai(datablock,s,0)

        Data[s]['araiblok']=araiblock
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

        #--------------------------------------------------------------
        # collect all zijderveld data to array and calculate VDS
        #--------------------------------------------------------------

        z_temperatures=[row[0] for row in zijdblock]
        zdata=[]
        vector_diffs=[]
        NRM=zijdblock[0][3]

        for k in range(len(zijdblock)):
            DIR=[zijdblock[k][1],zijdblock[k][2],zijdblock[k][3]/NRM]
            cart=pmag.dir2cart(DIR)
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
        NRM_dir=cart2dir(Data[s]['zdata'][0])
         
        NRM_dec=NRM_dir[0]
        NRM_dir[0]=0
        CART_rot.append(dir2cart(NRM_dir))

        
        for i in range(1,len(Data[s]['zdata'])):
          DIR=cart2dir(Data[s]['zdata'][i])
          DIR[0]=DIR[0]-NRM_dec
          CART_rot.append(array(dir2cart(DIR)))
          #print array(pmag.dir2cart(DIR))
          
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
        
        Data[s]['x_Arai']=x_Arai
        Data[s]['y_Arai']=y_Arai
        Data[s]['t_Arai']=t_Arai
        Data[s]['steps_Arai']=steps_Arai


        #--------------------------------------------------------------
        # collect all pTRM check to array 
        #--------------------------------------------------------------

        ptrm_checks = araiblock[2]
        zerofield_temperatures=[row[0] for row in zerofields]

        x_ptrm_check,y_ptrm_check,ptrm_checks_temperatures=[],[],[]

        for k in range(len(ptrm_checks)):
          if ptrm_checks[k][0] in zerofield_temperatures:
            index_zerofield=zerofield_temperatures.index(ptrm_checks[k][0])
            x_ptrm_check.append(ptrm_checks[k][3]/NRM)
            y_ptrm_check.append(zerofields[index_zerofield][3]/NRM)
            ptrm_checks_temperatures.append(ptrm_checks[k][0])
          
        x_ptrm_check=array(x_ptrm_check)  
        ptrm_check=array(y_ptrm_check)
        ptrm_checks_temperatures=array(ptrm_checks_temperatures)
        Data[s]['x_ptrm_check']=x_ptrm_check
        Data[s]['y_ptrm_check']=y_ptrm_check
        Data[s]['ptrm_checks_temperatures']=ptrm_checks_temperatures

        #--------------------------------------------------------------
        # collect tail checks 
        #--------------------------------------------------------------


        ptrm_tail = araiblock[3]
        #print ptrm_tail
        x_tail_check,y_tail_check,tail_check_temperatures=[],[],[]

        for k in range(len(ptrm_tail)):
          if ptrm_tail[k][0] in zerofield_temperatures:
              index_infield=infield_temperatures.index(ptrm_tail[k][0])
              x_tail_check.append(infields[index_infield][3]/NRM)
              y_tail_check.append(ptrm_tail[k][3]/NRM + zerofields[index_infield][3]/NRM)
              tail_check_temperatures.append(ptrm_tail[k][0])

        x_tail_check=array(x_tail_check)  
        y_tail_check=array(y_tail_check)
        tail_check_temperatures=array(tail_check_temperatures)
        
        Data[s]['x_tail_check']=x_tail_check
        Data[s]['y_tail_check']=y_tail_check
        Data[s]['tail_check_temperatures']=tail_check_temperatures

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
            self.GUI_log.write ("-W- Cant find er_sample.txt in project directory")

        try:
            data_er_sites=read_magic_file(self.WD+"/er_sites.txt",'er_site_name')
        except:
            self.GUI_log.write ("-W- Cant find er_sites.txt in project directory")

        try:
            data_er_ages=read_magic_file(self.WD+"/er_ages.txt",'er_sample_name')
        except:
            try:
                data_er_ages=read_magic_file(self.WD+"/er_ages.txt",'er_site_name')
            except:    
                self.GUI_log.write ("-W- Cant find er_ages in project directory")



        Data_info["er_samples"]=data_er_samples
        Data_info["er_sites"]=data_er_sites
        Data_info["er_ages"]=data_er_ages
        
        return(Data_info)

#--------------------------------------------------------------    
# Change Acceptance criteria dialog
#--------------------------------------------------------------


class Criteria_Dialog(wx.Dialog):

    def __init__(self, parent, accept_new_parameters,title):
        super(Criteria_Dialog, self).__init__(parent, title=title)
        self.accept_new_parameters=accept_new_parameters
        #print self.accept_new_parameters
        self.InitUI(accept_new_parameters)
        #self.SetSize((250, 200))

    def InitUI(self,accept_new_parameters):


        pnl1 = wx.Panel(self)

        vbox = wx.BoxSizer(wx.VERTICAL)

        bSizer1 = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "Specimen accpetance criteria" ), wx.HORIZONTAL )

        # Specimen criteria

        window_list_specimens=['n','int_ptrm_n','frac','gap_max','f','fvds','b_beta','g','q','int_mad','dang','drats','md']
        for key in window_list_specimens:
            command="self.set_specimen_%s=wx.TextCtrl(pnl1,style=wx.TE_CENTER,size=(50,20))"%key
            exec command
        self.set_specimen_scat=wx.CheckBox(pnl1, -1, '', (50, 50))        
        criteria_specimen_window = wx.GridSizer(2, 14, 12, 12)
        criteria_specimen_window.AddMany( [(wx.StaticText(pnl1,label="n",style=wx.TE_CENTER), wx.EXPAND),
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
            (self.set_specimen_n),
            (self.set_specimen_int_ptrm_n),
            (self.set_specimen_frac),
            (self.set_specimen_scat),                        
            (self.set_specimen_gap_max),
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

        bSizer2 = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "Sample Acceptance criteria" ), wx.HORIZONTAL )
        # Sample criteria
        window_list_samples=['int_n','int_n_outlier_check']
        for key in window_list_samples:
            command="self.set_sample_%s=wx.TextCtrl(pnl1,style=wx.TE_CENTER,size=(50,20))"%key
            exec command
        criteria_sample_window = wx.GridSizer(2, 2, 12, 12)
        criteria_sample_window.AddMany( [(wx.StaticText(pnl1,label="int_n",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="int_n_outlier_check",style=wx.TE_CENTER), wx.EXPAND),
            (self.set_sample_int_n),
            (self.set_sample_int_n_outlier_check)])

        bSizer2.Add( criteria_sample_window, 0, wx.ALIGN_LEFT|wx.ALL, 5 )

        #-----------        

        bSizer3 = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "Sample Acceptance criteria: STDEV-OPT" ), wx.HORIZONTAL )
        # Sample STEV-OPT
        window_list_samples=['int_sigma_uT','int_sigma_perc','int_interval_uT','int_interval_perc']
        for key in window_list_samples:
            command="self.set_sample_%s=wx.TextCtrl(pnl1,style=wx.TE_CENTER,size=(50,20))"%key
            exec command
        self.set_sample_stdev_opt=wx.RadioButton(pnl1, -1, 'Enable STDEV-OPT', (10, 10), style=wx.RB_GROUP)
        self.set_sample_bs=wx.RadioButton(pnl1, -1, 'Enable BS ', (10, 30))
        self.set_sample_bs_par=wx.RadioButton(pnl1, -1, 'Enable BS_PAR', (50, 50))
        
        criteria_sample_window_2 = wx.GridSizer(2, 4, 12, 12)
        criteria_sample_window_2.AddMany( [(wx.StaticText(pnl1,label="int_sigma_uT",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="int_sigma_perc",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="int_interval",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="int_interval_perc",style=wx.TE_CENTER), wx.EXPAND),
            (self.set_sample_int_sigma_uT),
            (self.set_sample_int_sigma_perc),
            (self.set_sample_int_interval_uT),
            (self.set_sample_int_interval_perc)])

        bSizer3.Add( criteria_sample_window_2, 0, wx.ALIGN_LEFT|wx.ALL, 5 )

        vbox1 = wx.BoxSizer(wx.VERTICAL)
        vbox1.AddSpacer(10)
        vbox1.Add(self.set_sample_stdev_opt,flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox1.AddSpacer(10)
        vbox1.Add(bSizer3,flag=wx.ALIGN_CENTER_HORIZONTAL)#,flag=wx.ALIGN_CENTER_VERTICAL)
        vbox1.AddSpacer(10)
        
        
        #-----------        

        bSizer4 = wx.StaticBoxSizer( wx.StaticBox( pnl1, wx.ID_ANY, "Sample Acceptance criteria: BS / BS-PAR" ), wx.HORIZONTAL )
        window_list_samples=['int_BS_68_uT','int_BS_68_perc','int_BS_95_uT','int_BS_95_perc']
        for key in window_list_samples:
            command="self.set_sample_%s=wx.TextCtrl(pnl1,style=wx.TE_CENTER,size=(50,20))"%key
            exec command
        # for bootstarp
        self.set_specimen_int_max_slope_diff=wx.TextCtrl(pnl1,style=wx.TE_CENTER,size=(50,20))
        
        criteria_sample_window_3 = wx.GridSizer(2, 5, 12, 12)
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

        hbox2a = wx.BoxSizer(wx.HORIZONTAL)
        hbox2a.Add(self.set_sample_bs,flag=wx.ALIGN_CENTER_VERTICAL)
        hbox2a.AddSpacer(10)
        hbox2a.Add(self.set_sample_bs_par,flag=wx.ALIGN_CENTER_VERTICAL)

        vbox2 = wx.BoxSizer(wx.VERTICAL)
        vbox2.AddSpacer(10)
        vbox2.Add(hbox2a,flag=wx.ALIGN_CENTER_HORIZONTAL)#,flag=wx.ALIGN_CENTER_VERTICAL)
        vbox2.AddSpacer(10)
        vbox2.Add(bSizer4,flag=wx.ALIGN_CENTER_VERTICAL)#,flag=wx.ALIGN_CENTER_VERTICAL)
        vbox2.AddSpacer(10)

        #-----------        



        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        self.okButton = wx.Button(pnl1, wx.ID_OK, "&OK")
        self.cancelButton = wx.Button(pnl1, wx.ID_CANCEL, '&Cancel')
        hbox3.Add(self.okButton)
        hbox3.Add(self.cancelButton )
        #self.okButton.Bind(wx.EVT_BUTTON, self.OnOK)
        #-----------  

        # Intialize values
        #print self.accept_new_parameters

        for key in window_list_specimens:
            command="self.set_specimen_%s.SetBackgroundColour(wx.NullColor)"%key
        exec command


        # Intialize specimen values
        self.high_threshold_velue_list=['specimen_gap_max','specimen_b_beta','specimen_dang','specimen_drats','specimen_int_mad','specimen_md']
        self.low_threshold_velue_list=['specimen_n','specimen_int_ptrm_n','specimen_f','specimen_fvds','specimen_frac','specimen_g','specimen_q']
              
        for key in self.high_threshold_velue_list + self.low_threshold_velue_list:
            if key in self.high_threshold_velue_list and float(self.accept_new_parameters[key]) >100 or\
               key in self.low_threshold_velue_list and float(self.accept_new_parameters[key]) <0.1:
                Value=""
                command="self.set_%s.SetValue(\"\")"%key
                exec command
                continue
            elif key in ['specimen_n','specimen_int_ptrm_n']:
                Value="%.0f"%self.accept_new_parameters[key]
            elif key in ['specimen_dang','specimen_drats','specimen_int_mad','specimen_md','specimen_g','specimen_q']:
                Value="%.1f"%self.accept_new_parameters[key]
            elif key in ['specimen_f','specimen_fvds','specimen_frac','specimen_b_beta','specimen_gap_max']:
                Value="%.2f"%self.accept_new_parameters[key]

            command="self.set_%s.SetValue(Value)"%key
            exec command

        # Intialize scat values
        if self.accept_new_parameters['specimen_scat']==True:
            self.set_specimen_scat.SetValue(True)
        else:
            self.set_specimen_scat.SetValue(False)
        # Intialize sample criteria values
        for key in ['sample_stdev_opt','sample_bs','sample_bs_par','sample_int_n','sample_int_sigma_uT','sample_int_sigma_perc','sample_int_interval_uT','sample_int_interval_perc','sample_int_n_outlier_check',\
                    'sample_int_BS_68_uT','sample_int_BS_95_uT','sample_int_BS_68_perc','sample_int_BS_95_perc']:
            #print "ron key",key
            if key in ['sample_int_n','sample_int_n_outlier_check']:
                Value="%.0f"%self.accept_new_parameters[key]
            elif key in ['sample_stdev_opt','sample_bs','sample_bs_par']:
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
        if self.accept_new_parameters['sample_bs'] or self.accept_new_parameters['sample_bs_par']:
            if float(self.accept_new_parameters['specimen_int_max_slope_diff'])<100:
                self.set_specimen_int_max_slope_diff.SetValue("%.1f"%(float(self.accept_new_parameters['specimen_int_max_slope_diff'])))
            else:
                self.set_specimen_int_max_slope_diff.SetValue("")

        
        #----------------------  
        vbox.AddSpacer(20)
        vbox.Add(bSizer1, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(20)
        vbox.Add(bSizer2, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(20)
        vbox.Add(vbox1, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(20)
        vbox.Add(vbox2, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(20)
        vbox.Add(hbox3, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(20)
                    
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
    #----------------------------------------------------------------------
    def __init__(self,fig,pars,plot_type):
        """Constructor"""
        wx.Frame.__init__(self, parent=None, title="Thellier Optimizer")

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

#===========================================================
# Optimizer
#===========================================================
    

class Optimizer(wx.Frame):
    """"""
 
    #----------------------------------------------------------------------
    def __init__(self,Data,Data_hierarchy,WD,criteria):
        wx.Frame.__init__(self, parent=None)

        """
        """
        
        self.WD=WD
        self.Data=Data
        self.Data_hierarchy=Data_hierarchy
        self.fixed_criteria=criteria
##        beta_start,beta_end,beta_step,=0.1,0.2,0.2
##        frac_start,frac_end,frac_step=0.6,0.8,0.2
##        beta_range=arange(beta_start,beta_step+beta_end,beta_step)
##        frac_range=arange(frac_start,frac_step+frac_end,beta_step)
##        Optimizer_group_file_path="/Users/ronshaar/geology/Projects/Thellier_GUI/Southern_Levant/Hecht_etal_2012/er_test_groups_hecht_2012.txt"
##        optimizer_functions_path="/optimizer/optimizer_functions.txt"
##        criteria_fixed_paremeters_file="/optimizer/pmag_fixed_criteria.txt"

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
        

        self.high_threshold_velue_list=['specimen_gap_max','specimen_b_beta','specimen_dang','specimen_drats','specimen_int_mad','specimen_md']
        self.low_threshold_velue_list=['specimen_n','specimen_int_ptrm_n','specimen_f','specimen_fvds','specimen_frac','specimen_g','specimen_q']

        for key in self.high_threshold_velue_list + self.low_threshold_velue_list:
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

        # sample ceiteria:            
        for key in ['sample_int_n','sample_int_sigma_uT','sample_int_sigma_perc','sample_int_interval_uT','sample_int_interval_perc','sample_int_n_outlier_check']:
            command="self.fixed_criteria[\"%s\"]=float(dia.set_%s.GetValue())"%(key,key)            
            try:
                exec command
            except:
                command="if dia.set_%s.GetValue() !=\"\" : self.show_messege(\"%s\")  "%(key,key)
                exec command


        #  message dialog
        dlg1 = wx.MessageDialog(self,caption="Warning:", message="Canges are save to optimizer/pmag_fixed_criteria.txt" ,style=wx.OK|wx.CANCEL)
        result = dlg1.ShowModal()
        if result == wx.ID_CANCEL:

            dlg1.Destroy()

        if result == wx.ID_OK:

            dia.Destroy()
        
            # Write new acceptance criteria to pmag_criteria.txt    
            try:
                Command_line="mkdir %s" %(self.WD+"/optimizer")
                os.system(Command_line)
            except:
                ""
            fout=open(self.WD+"/optimizer/pmag_fixed_criteria.txt",'w')
            String="tab\tpmag_criteria\n"
            fout.write(String)
            sample_criteria_list=[key for key in self.fixed_criteria.keys() if "sample" in key]
            specimen_criteria_list=self.high_threshold_velue_list + self.low_threshold_velue_list + ["specimen_scat"]
            for criteria in specimen_criteria_list:
                if criteria in self.high_threshold_velue_list and float(self.fixed_criteria[criteria])>100:
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
                if key=="specimen_scat":
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

        Text="Set optimizer function parameters"
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
        Text1="Inster functions in the text window below, each function in a seperate line.\n"
        Text2="Use a valid python syntax with logic or arithmetic operators\n use the example functions\n\n"
        Text3="List of legal operands:\n"
        Text4="study_sample_n:  Total number of samples in the study that pass the criteria\n"
        Text5="test_group_n:  Number of test groups that have at least one sample that passed the criteria\n" 
        Text6="max_group_int_sigma_uT:  standard deviation of the group with the maximum scatter \n"
        Text7="max_group_int_sigma_perc:  maximum [standard deviation of the group divided by its mean] in unit of %\n"
        Text8="Use \"Check function syntax\" when done.\n\n" 
                    
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
        self.open_existing_optimizer_group_file = wx.Button(self.panel,id=-1, label='Choose optimizer group file')
        self.Bind(wx.EVT_BUTTON, self.on_open_existing_optimizer_group_file, self.open_existing_optimizer_group_file)

        self.optimizer_group_file_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(800,20))

        #self.make_new_optimizer_group_file = wx.Button(self.panel,id=-1, label='make new group definition file')#,style=wx.BU_EXACTFIT)#, size=(175, 28))
        #self.Bind(wx.EVT_BUTTON, self.on_make_new_optimizer_group_file, self.make_new_optimizer_group_file)

        # Cancel  button 
        self.cancel_optimizer_button = wx.Button(self.panel, id=-1, label='Cancel')#,style=wx.BU_EXACTFIT)#, size=(175, 28))
        self.Bind(wx.EVT_BUTTON, self.on_cancel_optimizer_button, self.cancel_optimizer_button)

        self.run_optimizer_button = wx.Button(self.panel, id=-1, label='Run Optimizer')#,style=wx.BU_EXACTFIT)#, size=(175, 28))
        self.Bind(wx.EVT_BUTTON, self.on_run_optimizer_button, self.run_optimizer_button)

        # put an example
        try:
            function_in=open(self.WD+"/optimizer/optimizer_functions.txt",'rU')
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
        study_sample_n,test_group_n,max_group_int_sigma_uT,max_group_int_sigma_perc=10,10.,0.1,0.1
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
         
##    def on_optimizer_make_groups_next_button (self,event):
##        if self.check_status.GetValue()!= "PASS":
##            dlg1 = wx.MessageDialog(self, caption="",message="You must check function syntax first",style=wx.OK)
##            dlg1.ShowModal()            
##            return
##        dlg1 = wx.Dialog(self,title="Optimizer test group definition")
##
##
##        # Opene existing group definition 
##        open_existing_optimizer_group_file = wx.Button(dlg1,id=-1, label='Open existing group definition file')
##        self.Bind(wx.EVT_BUTTON, self.on_open_existing_optimizer_group_file, open_existing_optimizer_group_file)
##
##        
##        make_new_optimizer_group_file = wx.Button(dlg1,id=-1, label='make new group definition file')#,style=wx.BU_EXACTFIT)#, size=(175, 28))
##        #self.Bind(wx.EVT_BUTTON, self.on_make_new_optimizer_group_file, self.make_new_optimizer_group_file)
##
##        Text="explenation"                    
##        TEXT = wx.StaticText(dlg1, label=Text,style=wx.ALIGN_CENTRE)
##
##        
##        box=wx.BoxSizer(wx.wx.VERTICAL)
##        hbox1a = wx.BoxSizer(wx.HORIZONTAL)
##        hbox1b = wx.BoxSizer(wx.HORIZONTAL)
##        hbox1c = wx.BoxSizer(wx.HORIZONTAL)
##
##        hbox1a.Add(TEXT,flag=wx.ALIGN_CENTER_VERTICAL,border=2)        
##        hbox1b.Add(open_existing_optimizer_group_file,flag=wx.ALIGN_CENTER_VERTICAL,border=2)        
##        hbox1c.Add(make_new_optimizer_group_file,flag=wx.ALIGN_CENTER_VERTICAL,border=2)        
##
##        box.AddSpacer(30)
##        box.Add(hbox1a, flag=wx.ALIGN_CENTER_HORIZONTAL)#, border=10)        
##        box.AddSpacer(10)
##        box.Add(hbox1b, flag=wx.ALIGN_CENTER_HORIZONTAL)#, border=10)        
##        box.AddSpacer(10)
##        box.Add(hbox1c, flag=wx.ALIGN_CENTER_HORIZONTAL)#, border=10)        
##        box.AddSpacer(30)
##
##        
##        dlg1.SetSizer(box)
##        box.Fit(dlg1)
##
##        dlg1.Centre()
##        dlg1.Show()


    #def on_make_new_optimizer_group_file(self,event):
    def on_open_existing_optimizer_group_file(self,event):
        
        dirname=self.WD 
            
        dlg = wx.FileDialog(self, "Choose optimizer test groups file", dirname, "", "*.*", wx.OPEN)
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

            optimizer_function_file=open(self.WD+"/optimizer/optimizer_functions.txt",'w')
            TEXT=self.text_logger.GetValue()
            optimizer_function_file.write(TEXT)
            optimizer_function_file.close()

            gframe=wx.BusyInfo("Running Thellier auto optimizer\n It may take a while ....", self)

            optimizer_functions_path="/optimizer/optimizer_functions.txt"
            criteria_fixed_paremeters_file="/optimizer/pmag_fixed_criteria.txt"
            
            beta_range=arange(beta_start,beta_end,beta_step)
            frac_range=arange(frac_start,frac_end,beta_step)

            thellier_optimizer_2d.Thellier_optimizer(self.WD, self.Data,self.Data_hierarchy,criteria_fixed_paremeters_file,self.optimizer_group_file_path,optimizer_functions_path,beta_range,frac_range)

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
            

            dlg1 = wx.MessageDialog(self,caption="Message:", message="Optimizer finished sucsessfuly\nCheck folder optimizer in working directory" ,style=wx.OK|wx.ICON_INFORMATION)
            dlg1.ShowModal()
            dlg1.Destroy()
            gframe.Destroy()
        

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
        self.show_samples_ID.SetValue(True)
        bsizer_3_window = wx.GridSizer(2, 1, 12, 12)
        bsizer_3_window.AddMany( [(wx.StaticText(pnl1,label="show sample labels",style=wx.TE_CENTER), wx.EXPAND),
            (self.show_samples_ID)])
                                           
        bSizer3.Add( bsizer_3_window, 0, wx.ALIGN_LEFT|wx.ALL, 5 )

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

        vbox.Add(hbox2, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(20)
                    
        pnl1.SetSizer(vbox)
        vbox.Fit(self)





#--------------------------------------------------------------    
# Run the GUI
#--------------------------------------------------------------


if __name__ == '__main__':
    app = wx.PySimpleApp()
    app.frame = Arai_GUI()
    app.frame.Show()
    app.MainLoop()

    

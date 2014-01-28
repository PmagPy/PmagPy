#!/usr/bin/env python

#============================================================================================
# LOG HEADER:
#============================================================================================
#
# Demag_GUI Version 0.1 (beta) by Ron Shaar
# 
#
#
#============================================================================================


#--------------------------------------
# definitions
#--------------------------------------


global CURRENT_VRSION
CURRENT_VRSION = "v.0.1"
import matplotlib
matplotlib.use('WXAgg')

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas \

import sys,pylab,scipy,os
try:
    import zeq_gui_preferences
except:
    pass
import stat
import subprocess
import time
import wx
import wx.grid
import random
import numpy
from pylab import *
from scipy.optimize import curve_fit
import wx.lib.agw.floatspin as FS
try:
    from mpl_toolkits.basemap import Basemap, shiftgrid
except:
    pass

import pmag,demag_dialogs
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
import copy
from copy import deepcopy

matplotlib.rc('xtick', labelsize=10) 
matplotlib.rc('ytick', labelsize=10) 
matplotlib.rc('axes', labelsize=8) 
matplotlib.rcParams['savefig.dpi'] = 300.

rcParams.update({"svg.embed_char_paths":False})
rcParams.update({"svg.fonttype":'none'})


#--------------------------------------
# ZEQ GUI FRAME
#--------------------------------------

class Zeq_GUI(wx.Frame):
    """ The main frame of the application
    """
    title = "PmagPy Demag GUI %s (beta)"%CURRENT_VRSION
    
    def __init__(self):

        global FIRST_RUN
        FIRST_RUN=True
        wx.Frame.__init__(self, None, wx.ID_ANY, self.title)
        self.redo_specimens={}
        self.currentDirectory = os.getcwd() # get the current working directory
        self.get_DIR()        # choose directory dialog
                
        #accept_new_parameters_default,accept_new_parameters_null=self.get_default_criteria()    # inialize Null selecting criteria
        #self.accept_new_parameters_null=accept_new_parameters_null
        #self.accept_new_parameters_default=accept_new_parameters_default
        preferences=self.get_preferences()
        self.dpi = 100
        self.preferences={}
        self.preferences=preferences
        # inialize selecting criteria
        #accept_new_parameters=self.read_criteria_from_file(self.WD+"/pmag_criteria.txt")          
        #self.accept_new_parameters=accept_new_parameters
        #self.accept_new_parameters=accept_new_parameters
        #self.Data,self.Data_hierarchy,self.Data_info={},{},{}
        #self.MagIC_directories_list=[]

        self.COORDINATE_SYSTEM='specimen'
        self.Data_info=self.get_data_info() # Read  er_* data
        self.Data,self.Data_hierarchy=self.get_data() # Get data from magic_measurements and rmag_anistropy if exist.
        # ToDo
        # Read Pmag results table
        #self.pmag_specimens_data={}
        #self.pmag_samples_data={}
        #self.pmag_sites_data={}

        
        self.pmag_results_data={}
        for level in ['specimens','samples','sites','lcoations','study']:
            self.pmag_results_data[level]={}
        self.high_level_means={}

        high_level_means={}                                            
        for high_level in ['samples','sites','locations','study']:
            if high_level not in self.high_level_means.keys():
                self.high_level_means[high_level]={}
        
        
        #if  "-tree" in sys.argv and FIRST_RUN:
        #    self.open_magic_tree()

        self.Data_samples={}
        self.last_saved_pars={}
        self.specimens=self.Data.keys()         # get list of specimens
        self.specimens.sort()                   # get list of specimens
        if len(self.specimens)>0:
            self.s=self.specimens[0]
        else:
            self.s=""
        self.samples=self.Data_hierarchy['samples'].keys()         # get list of samples
        self.samples.sort()                   # get list of specimens
        self.sites=self.Data_hierarchy['sites'].keys()         # get list of sites
        self.sites.sort()                   # get list of sites
        self.locations=self.Data_hierarchy['locations'].keys()         # get list of sites
        self.locations.sort()                   # get list of sites

        # check if pmag_specimens.txt exist. If yes, import speci
        #self.get_pmag_tables()
        #self.update_pmag_tables()        
        self.panel = wx.Panel(self)          # make the Panel
        self.Main_Frame()                   # build the main frame
        self.create_menu()                  # create manu bar
        #self.Zij_zoom()
        #self.arrow_keys()

        #self.get_previous_interpretation() # get interpretations from pmag_specimens.txt
        FIRST_RUN=False


    def Main_Frame(self):
        """ Build main frame of panel: buttons, etc.
            choose the first specimen and display data
        """
        #GUI width is 200+100*5+100*5=1202
        #GUI hieght is 640
        
        dw, dh = wx.DisplaySize() 
        w, h = self.GetSize()
        #print 'diplay', dw, dh
        #print "gui", w, h
        r1=dw/1210.
        r2=dw/640.
        
        #if  dw>w:
        self.GUI_RESOLUTION=min(r1,r2,1.3)
        #print "gui resolution 2"
        #self.GUI_RESOLUTION=float(self.preferences['gui_resolution'])/100
        #----------------------------------------------------------------------                     
        # initialize first specimen in list as current specimen
        #----------------------------------------------------------------------                     
        try:
            self.s=self.specimens[0]
        except:
            self.s=""
        try:
            self.sample=self.Data_hierarchy['sample_of_specimen'][self.s]
        except:
            self.sample=""
        try:
            self.site=self.Data_hierarchy['site_of_specimen'][self.s]
        except:
            self.site=""
        #print "self.sample=self.Data_hierarchy['sample_of_specimen'][self.s]",self.Data_hierarchy['sample_of_specimen'][self.s]
        #print ":self.site=self.Data_hierarchy['site_of_specimen'][self.s]",self.Data_hierarchy['site_of_specimen'][self.s]
        #print "first specimen is"
        #print self.s
        #print self.specimens
        #----------------------------------------------------------------------                     
        # Create Figures and FigCanvas objects. 
        #----------------------------------------------------------------------                     
        #
        self.fig1 = Figure((5.*self.GUI_RESOLUTION, 5.*self.GUI_RESOLUTION), dpi=self.dpi)
        self.canvas1 = FigCanvas(self.panel, -1, self.fig1)
        #self.fig1.text(0.01,0.98,"Zijderveld plot",{'family':'Arial', 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })
        
        self.fig2 = Figure((2.5*self.GUI_RESOLUTION, 2.5*self.GUI_RESOLUTION), dpi=self.dpi)
        self.canvas2 = FigCanvas(self.panel, -1, self.fig2)

        self.fig3 = Figure((2.5*self.GUI_RESOLUTION, 2.5*self.GUI_RESOLUTION), dpi=self.dpi)
        self.canvas3 = FigCanvas(self.panel, -1, self.fig3)

        self.fig4 = Figure((2.5*self.GUI_RESOLUTION, 2.5*self.GUI_RESOLUTION), dpi=self.dpi)
        self.canvas4 = FigCanvas(self.panel, -1, self.fig4)

        # make axes of the figures
        self.zijplot = self.fig1.add_axes([0.1,0.1,0.8,0.8])
        #self.specimen_eqarea = self.fig2.add_subplot(111)
        self.m_plot = self.fig3.add_axes([0.2,0.15,0.7,0.7],frameon=True,axisbg='None')
        self.high_level_eqarea = self.fig4.add_subplot(111)


        #----------------------------------------------------------------------                     
        #  set font size and style
        #----------------------------------------------------------------------                     

        #font1 = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Comic Sans MS')
        # FONT_RATIO=self.GUI_RESOLUTION+(self.GUI_RESOLUTION-1)*5
        FONT_RATIO=1
        font1 = wx.Font(9+FONT_RATIO, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Arial')
        # GUI headers
        font2 = wx.Font(12+min(1,FONT_RATIO), wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Arial')
        font3 = wx.Font(11+FONT_RATIO, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Arial')
        font = wx.SystemSettings_GetFont(wx.SYS_SYSTEM_FONT)
        font.SetPointSize(10+FONT_RATIO)        

        #----------------------------------------------------------------------                     
        # Create text_box for presenting the measurements
        #----------------------------------------------------------------------                     

        self.logger = wx.TextCtrl(self.panel, id=-1, size=(200*self.GUI_RESOLUTION,300*self.GUI_RESOLUTION), style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
        self.logger.SetFont(font1)


        #----------------------------------------------------------------------                     
        #  select specimen box
        #----------------------------------------------------------------------                     

        self.box_sizer_select_specimen = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY), wx.VERTICAL )

        # Combo-box with a list of specimen
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
        
        select_specimen_window = wx.GridSizer(1, 2, 5, 10)
        select_specimen_window.AddMany( [(self.prevbutton, wx.ALIGN_LEFT),
            (self.nextbutton, wx.ALIGN_LEFT)])



        #----------------------------------------------------------------------                     
        #  select coordinate box
        #----------------------------------------------------------------------                     
        # stopped here
        # Combo-box with a list of specimen
        self.coordinates_box = wx.ComboBox(self.panel, -1, 'specimen', (300*self.GUI_RESOLUTION, 25), wx.DefaultSize,['specimen','geographic','tilt-corrected'], wx.CB_DROPDOWN,name="coordinates")
        self.coordinates_box.SetFont(font2)
        self.Bind(wx.EVT_TEXT, self.onSelect_coordinates,self.coordinates_box)
        #self.box_sizer_select_coordinate.Add(self.coordinates_box, 0, wx.TOP, 0 )        
        self.orthogonal_box = wx.ComboBox(self.panel, -1, 'Zijderveld', (300*self.GUI_RESOLUTION, 25), wx.DefaultSize,['Zijderveld','orthogonal E-W','orthogonal N-S'], wx.CB_DROPDOWN,name="orthogonal_plot")
        self.orthogonal_box.SetFont(font2)
        self.Bind(wx.EVT_TEXT, self.onSelect_orthogonal_box,self.orthogonal_box)

        self.box_sizer_select_specimen.Add(wx.StaticText(self.panel,label="specimen:",style=wx.TE_CENTER))        
        self.box_sizer_select_specimen.Add(self.specimens_box, 0, wx.TOP, 0 )        
        self.box_sizer_select_specimen.Add(select_specimen_window, 0, wx.TOP, 4 )        
        self.box_sizer_select_specimen.Add(wx.StaticLine(self.panel), 0, wx.ALL|wx.EXPAND, 5)
        self.box_sizer_select_specimen.Add(wx.StaticText(self.panel,label="coordinate system:",style=wx.TE_CENTER))        
        self.box_sizer_select_specimen.Add(self.coordinates_box, 0, wx.TOP, 4 )        
        self.box_sizer_select_specimen.Add(wx.StaticLine(self.panel), 0, wx.ALL|wx.EXPAND, 5)
        self.box_sizer_select_specimen.Add(wx.StaticText(self.panel,label="orthogonal plot:",style=wx.TE_CENTER))        
        self.box_sizer_select_specimen.Add(self.orthogonal_box, 0, wx.TOP, 4 )        

        #----------------------------------------------------------------------                     
        #  select bounds box
        #----------------------------------------------------------------------                     

        self.T_list=[]
        
        self.box_sizer_select_bounds = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY,"bounds" ), wx.HORIZONTAL )
        self.tmin_box = wx.ComboBox(self.panel, -1 ,size=(100*self.GUI_RESOLUTION, 25),choices=self.T_list, style=wx.CB_DROPDOWN)
        self.tmin_box.SetFont(font2)
        self.Bind(wx.EVT_COMBOBOX, self.get_new_PCA_parameters,self.tmin_box)

        self.tmax_box = wx.ComboBox(self.panel, -1 ,size=(100*self.GUI_RESOLUTION, 25),choices=self.T_list, style=wx.CB_DROPDOWN)
        self.Bind(wx.EVT_COMBOBOX, self.get_new_PCA_parameters,self.tmax_box)

        select_temp_window = wx.GridSizer(2, 1, 10*self.GUI_RESOLUTION, 19*self.GUI_RESOLUTION)
        select_temp_window.AddMany( [(self.tmin_box, wx.ALIGN_LEFT),
            (self.tmax_box, wx.ALIGN_LEFT)])
        self.box_sizer_select_bounds.Add(select_temp_window, 0, wx.TOP, 3.5 )        
        

        #----------------------------------------------------------------------                     
        #  save/delete box
        #----------------------------------------------------------------------                     

        self.box_sizer_save = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY,"" ), wx.HORIZONTAL )

        # save/delete interpretation buttons
        self.save_interpretation_button = wx.Button(self.panel, id=-1, label='save',size=(75*self.GUI_RESOLUTION,25))#,style=wx.BU_EXACTFIT)#, size=(175, 28))
        self.save_interpretation_button.SetFont(font2)
        self.delete_interpretation_button = wx.Button(self.panel, id=-1, label='delete',size=(75*self.GUI_RESOLUTION,25))#,style=wx.BU_EXACTFIT)#, size=(175, 28))
        self.delete_interpretation_button.SetFont(font2)
        self.Bind(wx.EVT_BUTTON, self.on_save_interpretation_button, self.save_interpretation_button)
        self.Bind(wx.EVT_BUTTON, self.on_delete_interpretation_button, self.delete_interpretation_button)
        
        save_delete_window = wx.GridSizer(2, 1, 10*self.GUI_RESOLUTION, 19*self.GUI_RESOLUTION)
        save_delete_window.AddMany( [(self.save_interpretation_button, wx.ALIGN_LEFT),
            (self.delete_interpretation_button, wx.ALIGN_LEFT)])
        self.box_sizer_save.Add(save_delete_window, 0, wx.TOP, 5.5 )        
        

        #----------------------------------------------------------------------                     
        # Specimen interpretation window 
        #----------------------------------------------------------------------                     
        self.box_sizer_specimen = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY,"PCA type"  ), wx.HORIZONTAL )                        
        self.PCA_type_box = wx.ComboBox(self.panel, -1, 'line', (100*self.GUI_RESOLUTION, 25), wx.DefaultSize,['line','line-anchored','line-with-origin','plane','Fisher'], wx.CB_DROPDOWN,name="coordinates")
        self.PCA_type_box.SetFont(font2)
        self.Bind(wx.EVT_COMBOBOX, self.get_new_PCA_parameters,self.PCA_type_box)

        specimen_stat_type_window = wx.GridSizer(2, 1, 0, 19*self.GUI_RESOLUTION)
        specimen_stat_type_window.AddMany( [(wx.StaticText(self.panel,label="\n ",style=wx.TE_CENTER), wx.EXPAND),
            (self.PCA_type_box, wx.EXPAND)])
        self.box_sizer_specimen.Add( specimen_stat_type_window, 0, wx.ALIGN_LEFT, 0 )        
 
        self.box_sizer_specimen_stat = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY,"PCA statistics"  ), wx.HORIZONTAL )                        
               
        for parameter in ['dec','inc','n','MAD','DANG']:
            COMMAND="self.%s_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50*self.GUI_RESOLUTION,25))"%parameter
            exec COMMAND
            COMMAND="self.%s_window.SetFont(font2)"%parameter
            exec COMMAND

        specimen_stat_window = wx.GridSizer(2, 5, 0, 19*self.GUI_RESOLUTION)
        specimen_stat_window.AddMany( [(wx.StaticText(self.panel,label="\ndec",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(self.panel,label="\ninc",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(self.panel,label="\nN",style=wx.TE_CENTER),wx.EXPAND),
            (wx.StaticText(self.panel,label="\nMAD",style=wx.TE_CENTER),wx.EXPAND),
            (wx.StaticText(self.panel,label="\nDANG",style=wx.TE_CENTER),wx.TE_CENTER),
            (self.dec_window, wx.EXPAND),
            (self.inc_window, wx.EXPAND) ,
            (self.n_window, wx.EXPAND) ,
            (self.MAD_window, wx.EXPAND),
            (self.DANG_window, wx.EXPAND)])
        self.box_sizer_specimen_stat.Add( specimen_stat_window, 0, wx.ALIGN_LEFT, 0 )

        #----------------------------------------------------------------------                     
        # High level mean window 
        #----------------------------------------------------------------------                     
        self.box_sizer_high_level = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY,"higher level mean"  ), wx.HORIZONTAL )                        
        self.level_box = wx.ComboBox(self.panel, -1, 'site', (100*self.GUI_RESOLUTION, 25), wx.DefaultSize,['sample','site','location','study'], wx.CB_DROPDOWN,name="high_level")
        self.level_box.SetFont(font2)
        self.Bind(wx.EVT_TEXT, self.onSelect_higher_level,self.level_box)

        self.level_names = wx.ComboBox(self.panel, -1,self.site, (100*self.GUI_RESOLUTION, 25), wx.DefaultSize,self.sites, wx.CB_DROPDOWN,name="high_level_names")
        self.level_names.SetFont(font2)
        self.Bind(wx.EVT_TEXT, self.onSelect_level_name,self.level_names)


        self.show_box = wx.ComboBox(self.panel, -1, 'specimens', (100*self.GUI_RESOLUTION, 25), wx.DefaultSize,['specimens','samples','sites','sites-VGP'], wx.CB_DROPDOWN,name="high_elements")
        self.show_box.SetFont(font2)
        self.Bind(wx.EVT_TEXT, self.onSelect_show_box,self.show_box)

        self.mean_type_box = wx.ComboBox(self.panel, -1, 'None', (100*self.GUI_RESOLUTION, 25), wx.DefaultSize,['Fisher','Fisher by polarity','Bingham','None'], wx.CB_DROPDOWN,name="high_type")
        self.mean_type_box.SetFont(font2)
        self.Bind(wx.EVT_TEXT, self.onSelect_mean_type_box,self.mean_type_box)

                
        high_level_window = wx.GridSizer(2, 3, 0, 19*self.GUI_RESOLUTION)
        high_level_window.AddMany( [(self.level_box, wx.EXPAND),
            (wx.StaticText(self.panel,label="\nshow",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(self.panel,label="\nmean",style=wx.TE_CENTER), wx.EXPAND),
            (self.level_names, wx.EXPAND),
            (self.show_box, wx.EXPAND),
            (self.mean_type_box, wx.EXPAND)])
        self.box_sizer_high_level.Add( high_level_window, 0, wx.ALIGN_LEFT, 0 )
                       
        #----------------------------------------------------------------------                     
        # High level text box
        #----------------------------------------------------------------------                     

        self.box_sizer_high_level_text = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY,""  ), wx.HORIZONTAL )                        
        self.high_level_text_box = wx.TextCtrl(self.panel, id=-1, size=(220*self.GUI_RESOLUTION,210*self.GUI_RESOLUTION), style=wx.TE_MULTILINE | wx.TE_READONLY )
        self.high_level_text_box.SetFont(font1)
        self.box_sizer_high_level_text.Add(self.high_level_text_box, 0, wx.ALIGN_LEFT, 0 )                                                               
        #----------------------------------------------------------------------                     
        # Design the panel
        #----------------------------------------------------------------------

        
        vbox1 = wx.BoxSizer(wx.VERTICAL)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        vbox1.AddSpacer(10)

        hbox1.AddSpacer(2)
        hbox1.Add(self.box_sizer_select_bounds,flag=wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
        hbox1.AddSpacer(2)
        hbox1.Add(self.box_sizer_save,flag=wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
        hbox1.AddSpacer(2)
        hbox1.Add(self.box_sizer_specimen, flag=wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
        hbox1.AddSpacer(2)
        hbox1.Add(self.box_sizer_specimen_stat, flag=wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
        hbox1.AddSpacer(2)
        hbox1.Add(self.box_sizer_high_level, flag=wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)

        vbox2a=wx.BoxSizer(wx.VERTICAL)
        vbox2a.Add(self.box_sizer_select_specimen,flag=wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND,border=8)
        vbox2a.Add(self.logger,flag=wx.ALIGN_TOP,border=8)
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2.AddSpacer(2)      
        hbox2.Add(vbox2a,flag=wx.ALIGN_CENTER_HORIZONTAL)#,border=8)        
        hbox2.Add(self.canvas1,flag=wx.ALIGN_CENTER_HORIZONTAL,border=8)

        vbox2 = wx.BoxSizer(wx.VERTICAL)        
        vbox2.Add(self.canvas2,flag=wx.ALIGN_LEFT,border=8)
        vbox2.Add(self.canvas3,flag=wx.ALIGN_LEFT,border=8)
        #vbox2.Add(

        vbox3 = wx.BoxSizer(wx.VERTICAL)        
        vbox3.Add(self.canvas4,flag=wx.ALIGN_LEFT|wx.ALIGN_TOP,border=8)
        vbox3.Add(self.box_sizer_high_level_text,flag=wx.ALIGN_CENTER_VERTICAL,border=8)
       
        hbox2.Add(vbox2,flag=wx.ALIGN_CENTER_HORIZONTAL)#,border=8)
        hbox2.Add(vbox3,flag=wx.ALIGN_CENTER_HORIZONTAL)#,border=8)


        vbox1.Add(hbox1, flag=wx.ALIGN_LEFT)#, border=10)
        vbox1.Add(hbox2, flag=wx.LEFT)#, border=10)

        self.panel.SetSizer(vbox1)
        vbox1.Fit(self)

        # Draw figures and add  text
        #try:
        #self.draw_figure(self.s)        # draw the figures
        #self.Add_text(self.s)           # write measurement data to text box
        #except:
        #    pass
        
        # get previous interpretations from spmag tables
        self.update_pmag_tables()
        # Draw figures and add  text
        self.update_selection()

    #----------------------------------------------------------------------
    # Draw plots
    #----------------------------------------------------------------------
       
        
    def draw_figure(self,s):
        
        #-----------------------------------------------------------
        #  initialization
        #-----------------------------------------------------------
        
        self.s=s
        
        if self.orthogonal_box.GetValue()=="orthogonal E-W":
            self.ORTHO_PLOT_TYPE='E-W'
        elif self.orthogonal_box.GetValue()=="orthogonal N-S":
            self.ORTHO_PLOT_TYPE='N-S'
        else:
            self.ORTHO_PLOT_TYPE='ZIJ'            
        if self.COORDINATE_SYSTEM=='geographic':
            #self.CART_rot=self.Data[self.s]['zij_rotated_geo']
            self.zij=array(self.Data[self.s]['zdata_geo'])
            self.zijblock=self.Data[self.s]['zijdblock_geo']
        elif self.COORDINATE_SYSTEM=='tilt-corrected':
            #self.CART_rot=self.Data[self.s]['zij_rotated_tilt']
            self.zij=array(self.Data[self.s]['zdata_tilt'])        
            self.zijblock=self.Data[self.s]['zijdblock_tilt']
        else:
            #self.CART_rot=self.Data[self.s]['zij_rotated']
            self.zij=array(self.Data[self.s]['zdata'])        
            self.zijblock=self.Data[self.s]['zijdblock']

        if self.COORDINATE_SYSTEM=='geographic':
            if self.ORTHO_PLOT_TYPE=='N-S':
                self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata_geo'],0.)
            elif self.ORTHO_PLOT_TYPE=='E-W':
                self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata_geo'],90.)
            else:#Zijderveld
                self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata_geo'],pmag.cart2dir(self.Data[self.s]['zdata_geo'][0])[0])
                 
        elif self.COORDINATE_SYSTEM=='tilt-corrected':
            if self.ORTHO_PLOT_TYPE=='N-S':
                self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata_tilt'],0.)
            elif self.ORTHO_PLOT_TYPE=='E-W':
                self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata_tilt'],90)
            else:#Zijderveld
                self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata_tilt'],pmag.cart2dir(self.Data[self.s]['zdata_tilt'][0])[0])
        else:
            if self.ORTHO_PLOT_TYPE=='N-S':
                self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata'],0.)
            elif self.ORTHO_PLOT_TYPE=='E-W':
                self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata'],90)
            else:#Zijderveld
                self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata'],pmag.cart2dir(self.Data[self.s]['zdata'][0])[0])


        self.zij_norm=array([row/sqrt(sum(row**2)) for row in self.zij])
        
        #Data[s]['zij_rotated']=self.Rotate_zijderveld(Data[s]['zdata'],pmag.cart2dir(Data[s]['zdata'][0])[0])
        #Data[s]['zij_rotated_geo']=self.Rotate_zijderveld(Data[s]['zdata_geo'],pmag.cart2dir(Data[s]['zdata_geo'][0])[0])
        #Data[s]['zij_rotated_tilt']=self.Rotate_zijderveld(Data[s]['zdata_tilt'],pmag.cart2dir(Data[s]['zdata_tilt'][0])[0])
           
        #-----------------------------------------------------------
        # Draw Zij plot
        #-----------------------------------------------------------
        self.fig1.clf()
        self.zijplot = self.fig1.add_axes([0.1,0.1,0.8,0.8])
        self.zijplot.clear()
        self.MS=6*self.GUI_RESOLUTION;self.dec_MEC='k';self.dec_MFC='r'; self.inc_MEC='k';self.inc_MFC='b'
        self.zijdblock_steps=self.Data[self.s]['zijdblock_steps']
        self.vds=self.Data[self.s]['vds']
        self.zijplot.plot(self.CART_rot[:,0],-1* self.CART_rot[:,1],'ro-',mfc=self.dec_MFC,mec=self.dec_MEC,markersize=self.MS,clip_on=False)  #x,y or N,E
        self.zijplot.plot(self.CART_rot[:,0],-1 * self.CART_rot[:,2],'bs-',mfc=self.inc_MFC,mec=self.inc_MEC,markersize=self.MS,clip_on=False)   #x-z or N,D
        self.zijplot.axis('off')
        self.zijplot.axis('equal')
        last_cart_1=array([self.CART_rot[0][0],self.CART_rot[0][1]])
        last_cart_2=array([self.CART_rot[0][0],self.CART_rot[0][2]])
        #K_diff=0
        if self.preferences['show_Zij_treatments'] :
            for i in range(len(self.zijdblock_steps)):
                if int(self.preferences['show_Zij_treatments_steps']) !=1:
                    if i!=0  and (i+1)%int(self.preferences['show_Zij_treatments_steps'])==0:
                        self.zijplot.text(self.CART_rot[i][0],-1*self.CART_rot[i][2],"  %s"%(self.zijdblock_steps[i]),fontsize=10*self.GUI_RESOLUTION,color='gray',ha='left',va='center')   #inc
                else:
                  self.zijplot.text(self.CART_rot[i][0],-1*self.CART_rot[i][2],"  %s"%(self.zijdblock_steps[i]),fontsize=10*self.GUI_RESOLUTION,color='gray',ha='left',va='center')   #inc

        #-----
        xmin, xmax = self.zijplot.get_xlim()
        if xmax <0:
            xmax=0
        if xmin>0:
            xmin=0
        else:
            xmin=xmin+xmin%0.2
        props = dict(color='black', linewidth=1.0, markeredgewidth=0.5)

        xlocs=arange(xmin,xmax,0.2)
        xtickline, = self.zijplot.plot(xlocs, [0]*len(xlocs),linestyle='',
                marker='+', **props)

        axxline, = self.zijplot.plot([xmin, xmax], [0, 0], **props)
        xtickline.set_clip_on(False)
        axxline.set_clip_on(False)
        
        TEXT=""
        if self.COORDINATE_SYSTEM=='specimen':
            self.zijplot.text(xmax,0,' x',fontsize=10,verticalalignment='bottom')
        else:
            if self.ORTHO_PLOT_TYPE=='N-S':
                TEXT=" N"
            elif self.ORTHO_PLOT_TYPE=='E-W':
                TEXT=" E"
            else:
                TEXT=" x"       
            self.zijplot.text(xmax,0,TEXT,fontsize=10,verticalalignment='bottom')


        #if self.ORTHO_PLOT_TYPE=='N-S' and self.COORDINATE_SYSTEM!="specimen":
        #    TEXT='N'
        #elif self.ORTHO_PLOT_TYPE=='E-W' and  self.COORDINATE_SYSTEM!="specimen":
        #    TEXT='E'
        #else:
        #    TEXT='x'
        #        
        #self.zijplot.text(xmax,0,' x',fontsize=10,verticalalignment='bottom')

        #-----

        ymin, ymax = self.zijplot.get_ylim()
        if ymax <0:
            ymax=0
        if ymin>0:
            ymin=0
        else:
            ymin=ymin+ymin%0.2
        ylocs = [loc for loc in self.zijplot.yaxis.get_majorticklocs()
                if loc>=ymin and loc<=ymax]
        ylocs=arange(ymin,ymax,0.2)

        ytickline, = self.zijplot.plot([0]*len(ylocs),ylocs,linestyle='',
                marker='+', **props)

        axyline, = self.zijplot.plot([0, 0],[ymin, ymax], **props)
        ytickline.set_clip_on(False)
        axyline.set_clip_on(False)
        TEXT1,TEXT2="",""
        if self.COORDINATE_SYSTEM=='specimen':
                TEXT1,TEXT2=" y","      z"  
            #self.zijplot.text(0,ymin,' y,z',fontsize=10,verticalalignment='top')
        else:
            if self.ORTHO_PLOT_TYPE=='N-S':
                TEXT1,TEXT2=" E","     D"
            elif self.ORTHO_PLOT_TYPE=='E-W':
                TEXT1,TEXT2=" S","     D"
            else:
                TEXT1,TEXT2=" y","      z"  
        self.zijplot.text(0,ymin,TEXT1,fontsize=10,color='r',verticalalignment='top')
        self.zijplot.text(0,ymin,'    ,',fontsize=10,color='k',verticalalignment='top')
        self.zijplot.text(0,ymin,TEXT2,fontsize=10,color='b',verticalalignment='top')
        #----


        self.zij_xlim_initial=self.zijplot.axes.get_xlim() 
        self.zij_ylim_initial=self.zijplot.axes.get_ylim() 

        if self.ORTHO_PLOT_TYPE=='N-S':
            STRING=""
            self.fig1.text(0.01,0.98,"N-S orthogonal plot",{'family':'Arial', 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })
        elif self.ORTHO_PLOT_TYPE=='E-W':
            STRING=""
            self.fig1.text(0.01,0.98,"E-W orthogonal plot",{'family':'Arial', 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })
        else:
            self.fig1.text(0.01,0.98,"Zijderveld plot",{'family':'Arial', 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })
            STRING="X-axis rotated to NRM (%.0f); "%(self.zijblock[0][1])
        STRING=STRING+"NRM=%.2e "%(self.zijblock[0][3])+ '$Am^2$'
        
        self.fig1.text(0.01,0.95,STRING,{'family':'Arial', 'fontsize':8*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })
        self.canvas1.draw()

        #-----------------------------------------------------------
        # specimen equal area
        #-----------------------------------------------------------
        self.fig2.clf()
        self.specimen_eqarea = self.fig2.add_subplot(111)
        self.fig2.text(0.02,0.96,"specimen",{'family':'Arial', 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })
        # draw_net
        self.draw_net(self.specimen_eqarea)


        x_eq=array([row[0] for row in self.zij_norm])
        y_eq=array([row[1] for row in self.zij_norm])
        z_eq=abs(array([row[2] for row in self.zij_norm]))

        R=array(sqrt(1-z_eq)/sqrt(x_eq**2+y_eq**2)) # from Collinson 1983
        eqarea_data_x=y_eq*R
        eqarea_data_y=x_eq*R
        self.specimen_eqarea.plot(eqarea_data_x,eqarea_data_y,lw=0.5,color='gray')#,zorder=0)
        #self.eqplot.scatter([eqarea_data_x_dn[i]],[eqarea_data_y_dn[i]],marker='o',edgecolor='0.1', facecolor='blue',s=15,lw=1)


        x_eq_dn,y_eq_dn,z_eq_dn,eq_dn_temperatures=[],[],[],[]
        x_eq_dn=array([row[0] for row in self.zij_norm if row[2]>0])
        y_eq_dn=array([row[1] for row in self.zij_norm if row[2]>0])
        z_eq_dn=abs(array([row[2] for row in self.zij_norm if row[2]>0]))

        
        if len(x_eq_dn)>0:
            R=array(sqrt(1-z_eq_dn)/sqrt(x_eq_dn**2+y_eq_dn**2)) # from Collinson 1983
            eqarea_data_x_dn=y_eq_dn*R
            eqarea_data_y_dn=x_eq_dn*R
            self.specimen_eqarea.scatter([eqarea_data_x_dn],[eqarea_data_y_dn],marker='o',edgecolor='black', facecolor='gray',s=15*self.GUI_RESOLUTION,lw=1,clip_on=False)
                    
           

        x_eq_up,y_eq_up,z_eq_up=[],[],[]
        x_eq_up=array([row[0] for row in self.zij_norm if row[2]<=0])
        y_eq_up=array([row[1] for row in self.zij_norm if row[2]<=0])
        z_eq_up=abs(array([row[2] for row in self.zij_norm if row[2]<=0]))
        if len(x_eq_up)>0:
            R=array(sqrt(1-z_eq_up)/sqrt(x_eq_up**2+y_eq_up**2)) # from Collinson 1983
            eqarea_data_x_up=y_eq_up*R
            eqarea_data_y_up=x_eq_up*R
            self.specimen_eqarea.scatter([eqarea_data_x_up],[eqarea_data_y_up],marker='o',edgecolor='black', facecolor='white',s=15*self.GUI_RESOLUTION,lw=1,clip_on=False)        
        
        #self.preferences['show_eqarea_treatments']=True
        if self.preferences['show_eqarea_treatments']:
            for i in range(len(self.zijdblock_steps)):
                self.specimen_eqarea.text(eqarea_data_x[i],eqarea_data_y[i],"%.0f"%float(self.zijdblock_steps[i]),fontsize=8*self.GUI_RESOLUTION,color="0.5")
        
        
        self.canvas2.draw()


        #-----------------------------------------------------------
        # Draw M/M0 plot ( or NLT data on the same area in the GUI)
        #-----------------------------------------------------------

        self.fig3.clf()
        self.fig3.text(0.02,0.96,'$M/M_0$',{'family':'Arial', 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })
        self.mplot = self.fig3.add_axes([0.2,0.15,0.7,0.7],frameon=True,axisbg='None')        
        
        #fig, ax1 = plt.subplots()
        #print "measurement_step_unit",self.Data[self.s]['measurement_step_unit'] 
        if self.Data[self.s]['measurement_step_unit'] =="mT:C" or self.Data[self.s]['measurement_step_unit'] =="C:mT":
            thermal_x,thermal_y=[],[]
            af_x,af_y=[],[]
            for i in range(len(self.Data[self.s]['zijdblock'])):
           
                step=self.Data[self.s]['zijdblock_steps'][i]
                if step=="0":
                    thermal_x.append(self.Data[self.s]['zijdblock'][i][0])
                    af_x.append(self.Data[self.s]['zijdblock'][i][0])
                    thermal_y.append(self.Data[self.s]['zijdblock'][i][3]/self.Data[self.s]['zijdblock'][0][3])
                    af_y.append(self.Data[self.s]['zijdblock'][i][3]/self.Data[self.s]['zijdblock'][0][3])
                elif "C" in step:
                    thermal_x.append(self.Data[self.s]['zijdblock'][i][0])
                    thermal_y.append(self.Data[self.s]['zijdblock'][i][3]/self.Data[self.s]['zijdblock'][0][3])
                elif "T" in step:
                    af_x.append(self.Data[self.s]['zijdblock'][i][0])
                    af_y.append(self.Data[self.s]['zijdblock'][i][3]/self.Data[self.s]['zijdblock'][0][3])
                else:
                    continue                            
            
            self.mplot.plot(thermal_x, thermal_y, 'ro-',markersize=5*self.GUI_RESOLUTION,lw=1,clip_on=False)            
            self.mplot.set_xlabel('Thermal (C)',color='r')
            for tl in self.mplot.get_xticklabels():
                tl.set_color('r')
            
            
            ax2 = self.mplot.twiny()
            ax2.plot(af_x, af_y, 'bo-',markersize=5*self.GUI_RESOLUTION,lw=1,clip_on=False)
            ax2.set_xlabel('AF (mT)',color='b')
            for tl in ax2.get_xticklabels():
                tl.set_color('b')

            self.mplot.tick_params(axis='both', which='major', labelsize=7)
            ax2.tick_params(axis='both', which='major', labelsize=7)
            self.mplot.spines["right"].set_visible(False)
            ax2.spines["right"].set_visible(False)
            self.mplot.get_xaxis().tick_bottom()
            self.mplot.get_yaxis().tick_left()
            self.mplot.set_ylabel("M / NRM$_0$",fontsize=8*self.GUI_RESOLUTION)
        
        else:
            
 
        
                            
            #self.mplot = self.fig3.add_axes([0.2,0.15,0.7,0.7],frameon=True,axisbg='None')        
            self.mplot.clear()
            x_data,y_data=[],[]
            for i in range(len(self.Data[self.s]['zijdblock'])):
                x_data.append(self.Data[self.s]['zijdblock'][i][0])
                y_data.append(self.Data[self.s]['zijdblock'][i][3]/self.Data[self.s]['zijdblock'][0][3])
    
            self.mplot = self.fig3.add_axes([0.2,0.15,0.7,0.7],frameon=True,axisbg='None')        
            self.mplot.clear()
            self.mplot.plot(x_data,y_data,'bo-',mec='0.2',markersize=5*self.GUI_RESOLUTION,lw=1,clip_on=False)
            self.mplot.set_xlabel("Treatment",fontsize=8*self.GUI_RESOLUTION)                  
            self.mplot.set_ylabel("M / NRM$_0$",fontsize=8*self.GUI_RESOLUTION)
            try:
                self.mplot.tick_params(axis='both', which='major', labelsize=7)
            except:
                pass
            #self.mplot.tick_params(axis='x', which='major', labelsize=8)          
            self.mplot.spines["right"].set_visible(False)
            self.mplot.spines["top"].set_visible(False)
            self.mplot.get_xaxis().tick_bottom()
            self.mplot.get_yaxis().tick_left()
        
        #xt=xticks()

        self.canvas3.draw()

        #-----------------------------------------------------------
        # high level equal area
        #-----------------------------------------------------------
        self.plot_higher_levels_data()
        #self.fig4.clf()
        #what_is_it=self.level_box.GetValue()
        #self.fig4.text(0.02,0.96,what_is_it,{'family':'Arial', 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })
        #self.high_level_eqarea = self.fig4.add_subplot(111)        
        ## draw_net        
        #self.draw_net(self.high_level_eqarea)
        #self.canvas4.draw()

        draw()

    def draw_net(self,FIG):
        FIG.clear()
        eq=FIG
        eq.axis((-1,1,-1,1))
        eq.axis('off')
        theta=arange(0.,2*pi,2*pi/1000)
        eq.plot(cos(theta),sin(theta),'k',clip_on=False,lw=1)
        #eq.vlines((0,0),(0.9,-0.9),(1.0,-1.0),'k')
        #eq.hlines((0,0),(0.9,-0.9),(1.0,-1.0),'k')
        #eq.plot([0.0],[0.0],'+k')

        Xsym,Ysym=[],[]
        for I in range(10,100,10):
            XY=pmag.dimap(0.,I)
            Xsym.append(XY[0])
            Ysym.append(XY[1])
        for I in range(10,90,10):
            XY=pmag.dimap(90.,I)
            Xsym.append(XY[0])
            Ysym.append(XY[1])
        for I in range(10,90,10):
            XY=pmag.dimap(180.,I)
            Xsym.append(XY[0])
            Ysym.append(XY[1])
        for I in range(10,90,10):
            XY=pmag.dimap(270.,I)
            Xsym.append(XY[0])
            Ysym.append(XY[1])
        eq.plot(Xsym,Ysym,'k+',clip_on=False,mew=0.5)
        for D in range(0,360,10):
            Xtick,Ytick=[],[]
            for I in range(4):
                XY=pmag.dimap(D,I)
                Xtick.append(XY[0])
                Ytick.append(XY[1])
            eq.plot(Xtick,Ytick,'k',clip_on=False,lw=0.5)


    #----------------------------------------------------------------------
    # add text to text box
    #----------------------------------------------------------------------
       
        
    def Add_text(self,s):
        
      """ Add text to measurement data wondow.
      """

      self.logger.Clear()
      FONT_RATIO=self.GUI_RESOLUTION+(self.GUI_RESOLUTION-1)*5
      font1 = wx.Font(9+FONT_RATIO, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Arial')
      
      #Header
      String="Step\t Tr\t Dec\t Inc\tM [Am^2]\n"
      self.logger.AppendText(String)

      #Body
      self.logger.SetFont(font1)
      if self.COORDINATE_SYSTEM=='geographic':
          zijdblock=self.Data[self.s]['zijdblock_geo']
      elif self.COORDINATE_SYSTEM=='tilt-corrected':
          zijdblock=self.Data[self.s]['zijdblock_tilt']
      else:
          zijdblock=self.Data[self.s]['zijdblock']
            
          
      TEXT=""
      for i in range(len(zijdblock)):
          lab_treatment=self.Data[self.s]['zijdblock_lab_treatments'][i]
          Step=""
          methods=lab_treatment.split('-')
          if "NO" in methods:
              Step="N "
          elif "T" in  methods:
              Step="T"
          elif "AF" in  methods:
              Step="AF"             
          Tr=zijdblock[i][0]
          Dec=zijdblock[i][1]
          Inc=zijdblock[i][2]
          Int=zijdblock[i][3]
          TEXT=TEXT+"%s\t%3.1f\t%5.1f\t%5.1f\t%.2e\n"%(Step,Tr,Dec,Inc,Int)
              
      self.logger.AppendText( TEXT)
      


    #----------------------------------------------------------------------
      
    def onSelect_specimen(self, event):
        """ update figures and text when a new specimen is selected
        """        
        self.s=self.specimens_box.GetValue()
        #self.pars=self.Data[self.s]['pars'] 
        self.update_selection()

    #----------------------------------------------------------------------

    def onSelect_coordinates(self, event):
        old=self.COORDINATE_SYSTEM
        new=self.coordinates_box.GetValue()
        if new=='geographic' and len(self.Data[self.s]['zijdblock_geo'])==0:
            self.coordinates_box.SetStringSelection(old)
        elif new=='tilt-corrected' and len(self.Data[self.s]['zijdblock_tilt'])==0:
            self.coordinates_box.SetStringSelection(old)
        else:
            self.COORDINATE_SYSTEM=new
        #self.update_selection()

        coordinate_system=self.COORDINATE_SYSTEM
        self.update_selection()
        #self.clear_boxes() 
        #self.Add_text(self.s)
        #self.draw_figure(self.s)
        #if self.pars!={} and 'measurement_step_min' in self.pars.keys() and 'measurement_step_max' in self.pars.keys() :
        #    tmin= "%.0f"%(float(self.pars['measurement_step_min']))       
        #    tmax= "%.0f"%(float(self.pars['measurement_step_max']))
        #    self.tmin_box.SetStringSelection(tmin)
        #    self.tmax_box.SetStringSelection(tmax)  
        #    calculation_type=self.pars['calculation_type']       
        ## calcuate again self.pars and update the figures and the statistics tables.                                
        #    self.pars=self.get_PCA_parameters(self.s,tmin,tmax,coordinate_system,calculation_type)                         
        #    self.update_GUI_with_new_interpretation()

    #----------------------------------------------------------------------

    def onSelect_orthogonal_box(self, event):
        self.clear_boxes() 
        self.Add_text(self.s)
        self.draw_figure(self.s)
        if self.pars!={}:
            #tmin= "%.0f"%(float(self.pars['measurement_step_min']))       
            #tmax= "%.0f"%(float(self.pars['measurement_step_max']))
            #calculation_type=self.pars['calculation_type']       
        # calcuate again self.pars and update the figures and the statistics tables.                                
            #self.pars=self.get_PCA_parameters(self.s,tmin,tmax,coordinate_system,calculation_type)                         
            self.update_GUI_with_new_interpretation()
              
    #----------------------------------------------------------------------

    def on_next_button(self,event):
      """ update figures and text when a next button is selected
      """
      #del self.Data[self.s]['pars']
      #self.Data[self.s]['pars']={}
                 
              
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
      #if 'saved' not in self.Data[self.s]['pars'] or self.Data[self.s]['pars']['saved']!= True:
      #        del self.Data[self.s]['pars']
      #        self.Data[self.s]['pars']={}
      ##       # return to last saved interpretation if exist
      #if 'er_specimen_name' in self.last_saved_pars.keys() and self.last_saved_pars['er_specimen_name']==self.s:
      #           self.Data[self.s]['pars']={}
      #           for key in self.last_saved_pars.keys():
      #               self.Data[self.s]['pars'][key]=self.last_saved_pars[key]
      #           self.last_saved_pars={}
                                
      index=self.specimens.index(self.s)
      if index==0: index=len(self.specimens)
      index-=1
      self.s=self.specimens[index]
      self.specimens_box.SetStringSelection(self.s)
      self.update_selection()

    #----------------------------------------------------------------------


    def update_selection(self):
        """ update figures and statistics window with a new selection of specimen 
        """

        # clear all boxes
        self.clear_boxes() 
        self.Add_text(self.s)
        self.draw_figure(self.s)
        
        # updtaes treatment list
        #--------------------------
        #treatments=[]
        #for i in range(len(self.Data[self.s]['zijdblock'])):
        #    treatments.append("%.1f"%(self.Data[self.s]['zijdblock'][i][0]))
        self.T_list=self.Data[self.s]['zijdblock_steps']
        self.tmin_box.SetItems(self.T_list)
        self.tmax_box.SetItems(self.T_list)
        self.tmin_box.SetStringSelection("")
        self.tmax_box.SetStringSelection("")

        # update high level boxes and figures (if needed)
        #--------------------------

        higher_level=self.level_box.GetValue()
        old_string=self.level_names.GetValue()
        new_string=old_string
        if higher_level=='sample':
            new_string=self.Data_hierarchy['sample_of_specimen'][self.s]
        if higher_level=='site':
            new_string=self.Data_hierarchy['site_of_specimen'][self.s]
        if higher_level=='location':
            new_string=self.Data_hierarchy['location_of_specimen'][self.s]
        self.level_names.SetValue(new_string)

        if new_string!=old_string:
            self.plot_higher_levels_data()
                                        
        # check if specimen's interpretation is saved 
        #--------------------------
        if self.s in self.pmag_results_data['specimens'].keys():
          for dirtype in self.pmag_results_data['specimens'][self.s].keys():
              if 'measurement_step_min' in self.pmag_results_data['specimens'][self.s][dirtype].keys()\
              and 'measurement_step_max' in self.pmag_results_data['specimens'][self.s][dirtype].keys():
                  # updatet min/tmax windows
                  measurement_step_min= float(self.pmag_results_data['specimens'][self.s][dirtype]['measurement_step_min'])
                  measurement_step_max= float(self.pmag_results_data['specimens'][self.s][dirtype]['measurement_step_max'])
                  if measurement_step_min==0:
                      tmin="0"
                  elif self.Data[self.s]['measurement_step_unit']=="C":
                      tmin="%.0fC"%(measurement_step_min)
                  elif self.Data[self.s]['measurement_step_unit']=="mT":
                      tmin="%.0fmT"%(measurement_step_min)
                  else: # combimned experiment T:AF
                    if "%.0fC"%(measurement_step_min) in self.Data[self.s]['zijdblock_steps']:
                        tmin="%.0fC"%(measurement_step_min)
                    elif "%.0fmT"%(measurement_step_min) in self.Data[self.s]['zijdblock_steps']:
                        tmin="%.0fmT"%(measurement_step_min)
                    else:
                        continue
                        
                  if self.Data[self.s]['measurement_step_unit']=="C":
                      tmax="%.0fC"%(measurement_step_max)
                  elif self.Data[self.s]['measurement_step_unit']=="mT":
                      tmax="%.0fmT"%(measurement_step_max)
                  else: # combimned experiment T:AF
                    if "%.0fC"%(measurement_step_max) in self.Data[self.s]['zijdblock_steps']:
                        tmax="%.0fC"%(measurement_step_max)
                    elif "%.0fmT"%(measurement_step_max) in self.Data[self.s]['zijdblock_steps']:
                        tmax="%.0fmT"%(measurement_step_max)
                    else:
                        continue
                                                                    
                  self.tmin_box.SetStringSelection(tmin)
                  self.tmax_box.SetStringSelection(tmax)  
                  
                  # update calculation type windows                                
                  calculation_type=self.pmag_results_data['specimens'][self.s][dirtype]['calculation_type']
                  if calculation_type=="DE-BFL": PCA_type="line"
                  elif calculation_type=="DE-BFL-A": PCA_type="line-anchored"
                  elif calculation_type=="DE-BFL-O": PCA_type="line-with-origin"
                  elif calculation_type=="DE-FM": PCA_type="Fisher"
                  elif calculation_type=="DE-BFP": PCA_type="plane"
                  self.PCA_type_box.SetStringSelection(PCA_type)
                  coordinate_system=self.COORDINATE_SYSTEM
                  
                  # calcuate again self.pars and update the figures and the statistics tables.                                
                  self.pars=self.get_PCA_parameters(self.s,tmin,tmax,coordinate_system,calculation_type) 
                  #self.pars['zijdblock_step_min']=tmin                    
                  #self.pars['zijdblock_step_max']=tmax                        
                  self.update_GUI_with_new_interpretation()

        # check if high level interpretation exists 
        #--------------------------
        dirtype=str(self.coordinates_box.GetValue())
        if dirtype=='specimen':dirtype='DA-DIR'
        if dirtype=='geographic':dirtype='DA-DIR-GEO'
        if dirtype=='tilt-corrected':dirtype='DA-DIR-TILT'
        if self.level_box.GetValue()=='sample': high_level_type='samples' 
        if self.level_box.GetValue()=='site': high_level_type='sites' 
        if self.level_box.GetValue()=='location': high_level_type='locations' 
        if self.level_box.GetValue()=='study': high_level_type='study' 
        high_level_name=str(self.level_names.GetValue())
        elements_type=str(self.show_box.GetValue())
        calculation_type="None"
        self.high_level_text_box.SetValue("")
        if high_level_name in self.high_level_means[high_level_type].keys():
            if dirtype in self.high_level_means[high_level_type][high_level_name].keys():
                mpars=self.high_level_means[high_level_type][high_level_name][dirtype]
                calculation_type= mpars['calculation_type'] 
                self.show_higher_levels_pars(mpars)

              
        self.mean_type_box.SetValue(calculation_type)
        self.plot_higher_levels_data()
        


    #----------------------------------------------------------------------


    def get_DIR(self):
        """ Choose a working directory dialog
        """
        if "-WD" in sys.argv and FIRST_RUN:
            ind=sys.argv.index('-WD')
            self.WD=sys.argv[ind+1] 
        else:   
            dialog = wx.DirDialog(None, "Choose a directory:",defaultPath = self.currentDirectory ,style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON | wx.DD_CHANGE_DIR)
            if dialog.ShowModal() == wx.ID_OK:
              self.WD=dialog.GetPath()
            dialog.Destroy()
        self.magic_file=self.WD+"/"+"magic_measurements.txt"
        self.GUI_log=open("%s/zeq.log"%self.WD,'w')

    #----------------------------------------------------------------------

    def get_new_PCA_parameters(self,event):
        
        """
        calcualte statisics when temperatures are selected
        or PCA type is changes
        """

        #remember the last saved interpretation

        #if "saved" in self.pars.keys():
        #    if self.pars['saved']:
        #        self.last_saved_pars={}
        #        for key in self.pars.keys():
        #            self.last_saved_pars[key]=self.pars[key]
        #self.pars['saved']=False
        tmin=str(self.tmin_box.GetValue())
        #index_min=self.tmin_box.GetSelection()
        tmax=str(self.tmax_box.GetValue())
        #index_max=self.tmax_box.GetSelection()
        if tmin=="" or tmax=="":
            return
       
        if (self.T_list.index(tmax) <= self.T_list.index(tmin)):
            return 
               
        #if (index_2-indparsex_1)+1 >= self.acceptance_criteria['specimen_int_n']:
        PCA_type=self.PCA_type_box.GetValue()
        if PCA_type=="line":calculation_type="DE-BFL"
        elif PCA_type=="line-anchored":calculation_type="DE-BFL-A"
        elif PCA_type=="line-with-origin":calculation_type="DE-BFL-O"
        elif PCA_type=="Fisher":calculation_type="DE-FM"
        elif PCA_type=="plane":calculation_type="DE-BFP"
        coordinate_system=self.COORDINATE_SYSTEM
        self.pars=self.get_PCA_parameters(self.s,tmin,tmax,coordinate_system,calculation_type)        
        self.update_GUI_with_new_interpretation()

    #----------------------------------------------------------------------


    def get_PCA_parameters(self,specimen,tmin,tmax,coordinate_system,calculation_type):
        """
        calcualte statisics 
        """
        #print self.Data[specimen]['z_treatments']
        #print specimen
        #beg_pca=self.Data[specimen]['z_treatments'].index(float(tmin))
        #end_pca=self.Data[specimen]['z_treatments'].index(float(tmax))
        #beg_pca=tmin_index
        #end_pca=tmax_index
        #print self.Data[specimen]['zijdblock_steps']
        beg_pca=self.Data[specimen]['zijdblock_steps'].index(tmin)
        end_pca=self.Data[specimen]['zijdblock_steps'].index(tmax)
        if coordinate_system=='geographic':
            block=self.Data[specimen]['zijdblock_geo']
        elif coordinate_system=='tilt-corrected':
            block=self.Data[specimen]['zijdblock_tilt']
        else:
            block=self.Data[specimen]['zijdblock']
        mpars=pmag.domean(block,beg_pca,end_pca,calculation_type)
        #mpars['calculation_type']=calculation_type
        for k in mpars.keys():
            try:
                if math.isnan(float(mpars[k])):
                    mpars[k]=0
            except:
                pass
        mpars['zijdblock_step_min']=tmin                    
        mpars['zijdblock_step_max']=tmax
                
            

        return(mpars)
 
    #----------------------------------------------------------------------

    def update_GUI_with_new_interpretation(self):
        """
        update statistics boxes and figures with a new interpretatiom
        when selecting new temperature bound
        """
        self.dec_window.SetValue("%.1f"%self.pars['specimen_dec'])
        self.inc_window.SetValue("%.1f"%self.pars['specimen_inc'])
        self.n_window.SetValue("%i"%self.pars['specimen_n'])
        if 'specimen_mad' in self.pars.keys():
            self.MAD_window.SetValue("%.1f"%self.pars['specimen_mad'])
        else:
            self.MAD_window.SetValue("")
        if 'specimen_dang' in self.pars.keys() and float(self.pars['specimen_dang'])!=-1:
            self.DANG_window.SetValue("%.1f"%self.pars['specimen_dang'])
        else:
            self.DANG_window.SetValue("")
        
            
  
        # re-draw the figures
        self.draw_figure(self.s)

        # now draw the interpretation
        self.draw_interpretation()

    #----------------------------------------------------------------------
                       
    def draw_interpretation(self):
        PCA_type=self.PCA_type_box.GetValue()
        
        #tmin=self.pars['measurement_step_min']
        tmin_index=self.Data[self.s]['zijdblock_steps'].index(self.pars['zijdblock_step_min'])
        #tmax=self.pars['measurement_step_max']
        tmax_index=self.Data[self.s]['zijdblock_steps'].index(self.pars['zijdblock_step_max'])

 
        # Zijderveld plot  
        ymin, ymax = self.zijplot.get_ylim()
        xmin, xmax = self.zijplot.get_xlim()
        
        self.zijplot.scatter([self.CART_rot[:,0][tmin_index]],[-1* self.CART_rot[:,1][tmin_index]],marker='o',s=40,facecolor='g',edgecolor ='k',zorder=100,clip_on=False)
        self.zijplot.scatter([self.CART_rot[:,0][tmax_index]],[-1* self.CART_rot[:,1][tmax_index]],marker='o',s=40,facecolor='g',edgecolor ='k',zorder=100,clip_on=False)
        self.zijplot.scatter([self.CART_rot[:,0][tmin_index]],[-1* self.CART_rot[:,2][tmin_index]],marker='s',s=50,facecolor='g',edgecolor ='k',zorder=100,clip_on=False)
        self.zijplot.scatter([self.CART_rot[:,0][tmax_index]],[-1* self.CART_rot[:,2][tmax_index]],marker='s',s=50,facecolor='g',edgecolor ='k',zorder=100,clip_on=False)
    
        if self.pars['calculation_type'] in ['DE-BFL','DE-BFL-A','DE-BFL-O']:
            
            #rotated zijderveld
            if self.COORDINATE_SYSTEM=='geographic':
                first_data=self.Data[self.s]['zdata_geo'][0]
            elif self.COORDINATE_SYSTEM=='tilt-corrected':
                first_data=self.Data[self.s]['zdata_tilt'][0]
            else:
                first_data=self.Data[self.s]['zdata'][0]
            
            if self.ORTHO_PLOT_TYPE=='N-S':
                rotation_declination=0. 
            elif self.ORTHO_PLOT_TYPE=='E-W':
                rotation_declination=90.
            else:#Zijderveld
                rotation_declination=pmag.cart2dir(first_data)[0]
                                                                 
            #NRM_dir=pmag.cart2dir(self.zij[0])         
            #NRM_dec=NRM_dir[0]
            
            #PCA direction
            ####CART=self.dir2cart([self.pars['specimen_dec'],self.pars['specimen_inc'],1])
            PCA_dir=[self.pars['specimen_dec'],self.pars['specimen_inc'],1]         
            PCA_dir_rotated=[PCA_dir[0]-rotation_declination,PCA_dir[1],1]      
            PCA_CART_rotated=pmag.dir2cart(PCA_dir_rotated)
            
            slop_xy_PCA=-1*PCA_CART_rotated[1]/PCA_CART_rotated[0]
            slop_xz_PCA=-1*PCA_CART_rotated[2]/PCA_CART_rotated[0]
    
            # Center of mass rotated        
            CM_x=mean(self.CART_rot[:,0][tmin_index:tmax_index+1])
            CM_y=mean(self.CART_rot[:,1][tmin_index:tmax_index+1])
            CM_z=mean(self.CART_rot[:,2][tmin_index:tmax_index+1])
                    
            # intercpet from the center of mass
            intercept_xy_PCA=-1*CM_y - slop_xy_PCA*CM_x
            intercept_xz_PCA=-1*CM_z - slop_xz_PCA*CM_x
    
            xx=array([0,self.CART_rot[:,0][tmin_index]])
            yy=slop_xy_PCA*xx+intercept_xy_PCA
            self.zijplot.plot(xx,yy,'-',color='g',lw=1.5,alpha=0.5)
            zz=slop_xz_PCA*xx+intercept_xz_PCA
            self.zijplot.plot(xx,zz,'-',color='g',lw=1.5,alpha=0.5)
                    
        self.zijplot.set_xlim(xmin, xmax)
        self.zijplot.set_ylim(ymin, ymax)
        self.canvas1.draw()       
    
        # Equal Area plot
        if self.pars['calculation_type']!='DE-BFP':
            CART=pmag.dir2cart([self.pars['specimen_dec'],self.pars['specimen_inc'],1])    
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
            self.specimen_eqarea.scatter([eqarea_x],[eqarea_y],marker='o',edgecolor=EC, facecolor=FC,s=30,lw=1,clip_on=False)
            self.canvas2.draw()
        
        # draw a best-fit plane
        
        if self.pars['calculation_type']=='DE-BFP':
            
            ymin, ymax = self.specimen_eqarea.get_ylim()
            xmin, xmax = self.specimen_eqarea.get_xlim()
            
            D_c,I_c=pmag.circ(self.pars["specimen_dec"],self.pars["specimen_inc"],90)
            X_c_up,Y_c_up=[],[]
            X_c_d,Y_c_d=[],[]
            for k in range(len(D_c)):
                #print D_c[k],I_c[k]
                XY=pmag.dimap(D_c[k],I_c[k])
                if I_c[k]<0:
                    X_c_up.append(XY[0])
                    Y_c_up.append(XY[1])
                if I_c[k]>0:
                    X_c_d.append(XY[0])
                    Y_c_d.append(XY[1])
            self.specimen_eqarea.plot(X_c_d,Y_c_d,'b')
            self.specimen_eqarea.plot(X_c_up,Y_c_up,'c')
            
            self.specimen_eqarea.set_xlim(xmin, xmax)
            self.specimen_eqarea.set_ylim(ymin, ymax)           
            self.canvas2.draw()
            
                                        
        # M/M0 plot
        ymin, ymax = self.mplot.get_ylim()
        xmin, xmax = self.mplot.get_xlim()
        self.mplot.scatter([self.Data[self.s]['zijdblock'][tmin_index][0]],[self.Data[self.s]['zijdblock'][tmin_index][3]/self.Data[self.s]['zijdblock'][0][3]],marker='o',s=30,facecolor='g',edgecolor ='k',zorder=100,clip_on=False)
        self.mplot.scatter([self.Data[self.s]['zijdblock'][tmax_index][0]],[self.Data[self.s]['zijdblock'][tmax_index][3]/self.Data[self.s]['zijdblock'][0][3]],marker='o',s=30,facecolor='g',edgecolor ='k',zorder=100,clip_on=False)
        self.mplot.set_xlim(xmin, xmax)
        self.mplot.set_ylim(ymin, ymax)
        self.canvas3.draw()

    #----------------------------------------------------------------------

                    
                                
                    
                                                                                                                                                   
    #----------------------------------------------------------------------
                                                                                                                                       
    def on_save_interpretation_button(self,event):

        """
        on the save button
        the interpretation is saved to pmag_results_table data 
        in all coordinate systems
        """
        calculation_type=self.pars['calculation_type']
        tmin_index=str(self.tmin_box.GetSelection())
        tmax_index=str(self.tmax_box.GetSelection())
        tmin=str(self.tmin_box.GetValue())
        tmax=str(self.tmax_box.GetValue())

        self.pmag_results_data['specimens'][self.s]={}
        self.pmag_results_data['specimens'][self.s]['DA-DIR']=self.get_PCA_parameters(self.s,tmin,tmax,'specimen',calculation_type)
        if len(self.Data[self.s]['zijdblock_geo'])>0:      
            self.pmag_results_data['specimens'][self.s]['DA-DIR-GEO']=self.get_PCA_parameters(self.s,tmin,tmax,'geographic',calculation_type)                
        if len(self.Data[self.s]['zijdblock_tilt'])>0:      
            self.pmag_results_data['specimens'][self.s]['DA-DIR-TILT']=self.get_PCA_parameters(self.s,tmin,tmax,'tilt-corrected',calculation_type)                        

        # calculate higher level data
        self.calculate_higher_levels_data()
        #self.plot_higher_levels_data()
        self.update_selection()
        
    #----------------------------------------------------------------------  
   
    #----------------------------------------------------------------------

    def on_delete_interpretation_button(self,event):
        #self.Data[self.s]['pars']={}
        #for dirtype in ['DA-DIR','DA-DIR-GEO','DA-DIR-TILT']:
        #    if dirtype in self.Data[self.s].keys():
        #        del self.Data[self.s][dirtype]
        del(self.pmag_results_data['specimens'][self.s])
        
        self.tmin_box.SetValue("")
        self.tmax_box.SetValue("")
        self.clear_boxes()
        self.onSelect_orthogonal_box(self.s)
        # calculate higher level data
        self.calculate_higher_levels_data()
        #self.plot_higher_levels_data()
        self.update_selection()
        return
 
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

        for parameter in ['dec','inc','n','MAD','DANG']:
            COMMAND="self.%s_window.SetValue('')"%parameter
            exec COMMAND
            COMMAND="self.%s_window.SetBackgroundColour(wx.NullColour)"%parameter
            exec COMMAND
            
    #----------------------------------------------------------------------

    def onSelect_mean_type_box(self,event):
        # calculate higher level data
        self.calculate_higher_levels_data()
        self.update_selection()        

        
    #----------------------------------------------------------------------
        
    def onSelect_higher_level(self,event):
       self.UPPER_LEVEL=self.level_box.GetValue() 
       if self.UPPER_LEVEL=='sample':
           self.show_box.SetItems(['specimens'])
           self.show_box.SetStringSelection('specimens')
           self.level_names.SetItems(self.samples)
           self.level_names.SetStringSelection(self.Data_hierarchy['sample_of_specimen'][self.s])
           
       if self.UPPER_LEVEL=='site':
           self.show_box.SetItems(['specimens','samples'])
           if self.show_box.GetValue() not in ['specimens','samples']:
               self.show_box.SetStringSelection('samples')
           self.level_names.SetItems(self.sites)
           self.level_names.SetStringSelection(self.Data_hierarchy['site_of_specimen'][self.s])
       if self.UPPER_LEVEL=='location':
           self.show_box.SetItems(['specimens','samples','sites','sites VGP'])
           if self.show_box.GetValue() not in ['specimens','samples','sites','sites VGP']:
               self.show_box.SetStringSelection('sites')
           self.level_names.SetItems(self.locations)
           self.level_names.SetStringSelection(self.Data_hierarchy['location_of_specimen'][self.s])
       if self.UPPER_LEVEL=='study':
           self.show_box.SetItems(['specimens','samples','sites','sites VGP'])
           if self.show_box.GetValue() not in ['specimens','samples','sites','sites VGP']:
               self.show_box.SetStringSelection('sites')
           self.level_names.SetItems(['this study'])
           self.level_names.SetStringSelection('this study')
           
       #self.calculate_higher_levels_data()
       self.plot_higher_levels_data()
       self.update_selection()        

    #----------------------------------------------------------------------
        
    def onSelect_level_name(self,event):
       high_level_name=str(self.level_names.GetValue())
       
       if self.level_box.GetValue()=='sample':
           specimen_list=self.Data_hierarchy['samples'][high_level_name]['specimens']
       if self.level_box.GetValue()=='site':
           specimen_list=self.Data_hierarchy['sites'][high_level_name]['specimens']
       if self.level_box.GetValue()=='location':  
           specimen_list=self.Data_hierarchy['locations'][high_level_name]['specimens']
       if self.level_box.GetValue()=='study':
           specimen_list=self.Data_hierarchy['study']['this study']['specimens']
       
       if  self.s not in specimen_list:
           specimen_list.sort()
           self.s=specimen_list[0]
           self.specimens_box.SetStringSelection(self.s)      
           self.update_selection()
           #self.calculate_higher_levels_data()
           #self.plot_higher_levels_data()

    #----------------------------------------------------------------------

    def onSelect_show_box(self,event):

        self.calculate_higher_levels_data()
        self.plot_higher_levels_data()
           
    #----------------------------------------------------------------------


    def calculate_high_level_mean (self,high_level_type,high_level_name,calculation_type,elements_type):
        # high_level_type:'samples','sites','locations','study'
        # calculation_type: 'Bingham','Fisher','Fisher by polarity'
        # elements_type (what to average):'specimens','samples','sites' (Ron. ToDo alos VGP and maybe locations?) 

        # figure out what level to average,and what elements to average (specimen, samples, sites, vgp)        
        self.high_level_means[high_level_type][high_level_name]={}
        for dirtype in ["DA-DIR","DA-DIR-GEO","DA-DIR-TILT"]:
            elements_list=self.Data_hierarchy[high_level_type][high_level_name][elements_type]
            pars_for_mean=[]              
            for element in elements_list:
                if elements_type=='specimens':
                    if element in self.pmag_results_data['specimens'].keys():
                        if dirtype in self.pmag_results_data['specimens'][element].keys():
                            pars=self.pmag_results_data['specimens'][element][dirtype]
                            if "calculation_type" in pars.keys() and pars["calculation_type"] == 'DE-BFP':
                                dec,inc,direction_type=pars["specimen_dec"],pars["specimen_inc"],'p'
                            elif "specimen_dec" in pars.keys() and "specimen_inc" in pars.keys():
                                dec,inc,direction_type=pars["specimen_dec"],pars["specimen_inc"],'l'
                            elif "dec" in pars.keys() and "inc" in pars.keys():
                                dec,inc,direction_type=pars["dec"],pars["inc"],'l'
                            else:
                                print "-E- ERROR: cant find mean for element %s"%element
                                continue 
                    else:
                        continue                                           
                else:
                    if element in self.high_level_means[elements_type].keys():
                        if dirtype in self.high_level_means[elements_type][element].keys():
                            pars=self.high_level_means[elements_type][element][dirtype]
                            if "dec" in pars.keys() and "inc" in pars.keys():
                                dec,inc,direction_type=pars["dec"],pars["inc"],'l'
                            else:
                                print "-E- ERROR: cant find mean for element %s"%element
                                continue                                
                            #pars_for_mean.append({'dec':float(dec),'inc':float(inc),'direction_type':direction_type})
                    else:
                        continue
                        
                pars_for_mean.append({'dec':float(dec),'inc':float(inc),'direction_type':direction_type,'element_name':element})
                                                                                                                                                                      
            if len(pars_for_mean)  > 0 and calculation_type !="None":
                self.high_level_means[high_level_type][high_level_name][dirtype]=self.calculate_mean(pars_for_mean,calculation_type)
                #print "calculate mean for high level",high_level_name,self.high_level_means[high_level_type][high_level_name]
    #----------------------------------------------------------------------

    def calculate_mean(self,pars_for_mean,calculation_type):
        #print "calculate_mean !!"
        #print pars_for_mean,calculation_type
        ''' 
        claculates:
            Fisher mean (lines/planes)
            or Bingham mean
            or Fisher by polarity
        '''
        if len(pars_for_mean)==0:
            return({})
        elif len(pars_for_mean)==1:
            return ({"dec":float(pars_for_mean[0]['dec']),"inc":float(pars_for_mean[0]['inc']),"calculation_type":calculation_type,"n":1})                        
        elif calculation_type =='Bingham':
            data=[]
            for pars in pars_for_mean:
                # ignore great circle
                if 'direction_type' in pars.keys() and 'direction_type'=='p':
                    continue
                else:
                    data.append([pars['dec'],pars['inc']])
            mpars=pmag.dobingham(data)
        elif calculation_type=='Fisher':
            mpars=pmag.dolnp(pars_for_mean,'direction_type')
        elif calculation_type=='Fisher by polarity':
            mpars=pmag.fisher_by_pol(pars_for_mean)
            
        
        # change strigs to floats
        if  calculation_type!='Fisher by polarity':  
            for key in mpars.keys():
                mpars[key]=float( mpars[key] )                
        else:
            for mode in ['A','B','All']:
                for key in mpars[mode].keys():
                    mpars[mode][key]=float(mpars[mode][key])
        mpars['calculation_type']=calculation_type

        return(mpars)
                                                            
                                                                        
    
    def calculate_higher_levels_data(self):

        high_level_type=str(self.level_box.GetValue())
        if high_level_type=='sample':high_level_type='samples'
        if high_level_type=='site':high_level_type='sites'
        if high_level_type=='location':high_level_type='locations'
        high_level_name=str(self.level_names.GetValue())
        calculation_type=str(self.mean_type_box.GetValue())
        elements_type=str(self.show_box.GetValue())
        self.calculate_high_level_mean(high_level_type,high_level_name,calculation_type,elements_type)                
        
                                    

        
                
    def plot_higher_levels_data(self):
       #print " plot_higher_levels_data" 
       
       high_level=self.level_box.GetValue() 
       self.UPPER_LEVEL_NAME=self.level_names.GetValue() 
       self.UPPER_LEVEL_SHOW=self.show_box.GetValue() 
       self.UPPER_LEVEL_MEAN=self.mean_type_box.GetValue() 
       

       self.fig4.clf()
       what_is_it=self.level_box.GetValue()+": "+self.level_names.GetValue()
       self.fig4.text(0.02,0.96,what_is_it,{'family':'Arial', 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })
       self.high_level_eqarea = self.fig4.add_subplot(111)        
       # draw_net        
       self.draw_net(self.high_level_eqarea)
       self.canvas4.draw()

       if self.COORDINATE_SYSTEM=="geographic": dirtype='DA-DIR-GEO'
       elif self.COORDINATE_SYSTEM=="tilt-corrected": dirtype='DA-DIR-TILT'
       else: dirtype='DA-DIR'

       if self.level_box.GetValue()=='sample': high_level_type='samples' 
       if self.level_box.GetValue()=='site': high_level_type='sites' 
       if self.level_box.GetValue()=='location': high_level_type='locations' 
       if self.level_box.GetValue()=='study': high_level_type='study' 

       high_level_name=str(self.level_names.GetValue())
       calculation_type=str(self.mean_type_box.GetValue())
       elements_type=str(self.show_box.GetValue())
       
       #print high_level_type,high_level_name,elements_type
       #print "high_level_type",high_level_type
       #print self.Data_hierarchy[high_level_type]
       elements_list=self.Data_hierarchy[high_level_type][high_level_name][elements_type]
       
       # plot elements directions
       for element in elements_list:
            if elements_type=='specimens':
                if element in self.pmag_results_data['specimens'].keys():
                    if dirtype in self.pmag_results_data['specimens'][element].keys():
                        mpars=self.pmag_results_data['specimens'][element][dirtype]
                        self.plot_eqarea_pars(mpars,self.high_level_eqarea)

            else:
                if element in self.high_level_means[elements_type].keys():
                    if dirtype in self.high_level_means[elements_type][element].keys():
                        mpars=self.high_level_means[elements_type][element][dirtype]
                        self.plot_eqarea_pars(mpars,self.high_level_eqarea)
                        
       # plot elements means
       if calculation_type!="None":
           if high_level_name in self.high_level_means[high_level_type].keys():
               if dirtype in self.high_level_means[high_level_type][high_level_name].keys():
                   self.plot_eqarea_mean( self.high_level_means[high_level_type][high_level_name][dirtype],self.high_level_eqarea)
                        
           
                                    
       self.canvas4.draw()
                        
    def plot_eqarea_pars(self,pars,fig):
        # plot best-fit plane
        if pars=={}:
            return
        if 'calculation_type' in pars.keys() and pars['calculation_type']=='DE-BFP':
            ymin, ymax = fig.get_ylim()
            xmin, xmax = fig.get_xlim()
            
            D_c,I_c=pmag.circ(pars["specimen_dec"],pars["specimen_inc"],90)
            X_c_up,Y_c_up=[],[]
            X_c_d,Y_c_d=[],[]
            for k in range(len(D_c)):
                XY=pmag.dimap(D_c[k],I_c[k])
                if I_c[k]<0:
                    X_c_up.append(XY[0])
                    Y_c_up.append(XY[1])
                if I_c[k]>0:
                    X_c_d.append(XY[0])
                    Y_c_d.append(XY[1])
            fig.plot(X_c_d,Y_c_d,'b',lw=0.5)
            fig.plot(X_c_up,Y_c_up,'c',lw=0.5)
            
            fig.set_xlim(xmin, xmax)
            fig.set_ylim(ymin, ymax)           
        # plot best-fit direction
        else:
            if "specimen_dec" in pars.keys() and "specimen_inc" in pars.keys():
                dec=pars["specimen_dec"];inc=pars["specimen_inc"]
            elif "dec" in pars.keys() and "inc" in pars.keys():
                dec=pars["dec"];inc=pars["inc"]                
            XY=pmag.dimap(dec,inc)                
            if inc>0:
                FC='gray';SIZE=15*self.GUI_RESOLUTION
            else:
                FC='white';SIZE=15*self.GUI_RESOLUTION
            fig.scatter([XY[0]],[XY[1]],marker='o',edgecolor='black', facecolor=FC,s=SIZE,lw=1,clip_on=False)
                            
    def plot_eqarea_mean(self,meanpars,fig):
        mpars_to_plot=[]
        if meanpars=={}:
            return
        if meanpars['calculation_type']=='Fisher by polarity':
            for mode in ['A','B','All']:
                if meanpars[mode]!={}:
                    mpars_to_plot.append(meanpars[mode])
        else:
           mpars_to_plot.append(meanpars)
        ymin, ymax = fig.get_ylim()
        xmin, xmax = fig.get_xlim()
        # put on the mean direction
        for mpars in mpars_to_plot:
            XY=pmag.dimap(float(mpars["dec"]),float(mpars["inc"]))
            if mpars["inc"]>0:
                FC='green';EC='0.1'
            else:
                FC='yellow';EC='green'
            fig.scatter([XY[0]],[XY[1]],marker='o',edgecolor=EC, facecolor=FC,s=30,lw=1,clip_on=False)
            
            #if 'calculation_type' not in mpars.keys():
            #    return
                
            if "alpha95" in mpars.keys():
            # get the alpha95
                Xcirc,Ycirc=[],[]
                Da95,Ia95=pmag.circ(float(mpars["dec"]),float(mpars["inc"]),float(mpars["alpha95"]))
                for k in  range(len(Da95)):
                    XY=pmag.dimap(Da95[k],Ia95[k])
                    Xcirc.append(XY[0])
                    Ycirc.append(XY[1])
                fig.plot(Xcirc,Ycirc,'g')
            elif 'calculation_type' in mpars.keys() and mpars['calculation_type']=='Bingham':
                # copied from plotELL function in pmagplotlib
                rad=numpy.pi/180.
                #Pdec,Pinc,beta,Bdec,Binc,gamma,Gdec,Ginc=pars[0],pars[1],pars[2],pars[3],pars[4],pars[5],pars[6],pars[7]
                Pdec,Pinc,beta,Bdec,Binc,gamma,Gdec,Ginc=\
                mpars['dec'],mpars['inc'],mpars['Zeta'],mpars['Zdec'],mpars['Zinc'],mpars['Eta'],mpars['Edec'],mpars['Einc']
                
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
                X=pmag.dir2cart((Pdec,Pinc,1.0)) # convert to cartesian coordintes
                if  X[2]<0:
                    for i in range(3):
                        X[i]=-X[i]
            # set up rotation matrix t
                t[0][2]=X[0]
                t[1][2]=X[1]
                t[2][2]=X[2]
                X=pmag.dir2cart((Bdec,Binc,1.0))
                if  X[2]<0:
                    for i in range(3):
                        X[i]=-X[i]
                t[0][0]=X[0]
                t[1][0]=X[1]
                t[2][0]=X[2]
                X=pmag.dir2cart((Gdec,Ginc,1.0))
                if X[2]<0:
                    for i in range(3):
                        X[i]=-X[i]
                t[0][1]=X[0]
                t[1][1]=X[1]
                t[2][1]=X[2]
            # set up v matrix
                v=[0,0,0]
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
                    PTS.append(pmag.cart2dir(elli))
                    R=numpy.sqrt( 1.-abs(elli[2]))/(numpy.sqrt(elli[0]**2+elli[1]**2)) # put on an equal area projection
                    if elli[2]<0:
            #            for i in range(3): elli[i]=-elli[i]
                        X_up.append(elli[1]*R)
                        Y_up.append(elli[0]*R)
                    else:
                        X_ell.append(elli[1]*R)
                        Y_ell.append(elli[0]*R)
                #if plot==1:
                if X_ell!=[]:fig.plot(X_ell,Y_ell,'b')
                if X_up!=[]:fig.plot(X_up,Y_up,'g-')
                #pylab.draw()
                #else: 
                #    return PTS
                
        fig.set_xlim(xmin, xmax)
        fig.set_ylim(ymin, ymax)    

    def show_higher_levels_pars(self,mpars):
        self.high_level_text_box.SetValue("")
        FONT_RATIO=self.GUI_RESOLUTION+(self.GUI_RESOLUTION-1)*5
        font2 = wx.Font(12+min(1,FONT_RATIO), wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Arial')
        self.high_level_text_box.SetFont(font2)
        if mpars["calculation_type"]=='Fisher':
            String="Fisher statistics:\n"
            String=String+"dec"+": "+"%.1f\n"%float(mpars['dec'])
            String=String+"inc"+": "+"%.1f\n"%float(mpars['inc'])
            String=String+"alpha95"+": "+"%.1f\n"%float(mpars['alpha95'])
            String=String+"K"+": "+"%.1f\n"%float(mpars['K'])
            String=String+"R"+": "+"%.4f\n"%float(mpars['R'])
            String=String+"n_lines"+": "+"%.0f\n"%float(mpars['n_lines'])
            String=String+"n_planes"+": "+"%.0f\n"%float(mpars['n_planes'])
            self.high_level_text_box.AppendText(String)

        if mpars["calculation_type"]=='Fisher by polarity' :
            for mode in ['A','B','All']:
                if mpars[mode]=={}:
                    continue
                String="Fisher statistics [%s]:\n"%mode
                String=String+"dec"+": "+"%.1f\n"%float(mpars[mode]['dec'])
                String=String+"inc"+": "+"%.1f\n"%float(mpars[mode]['inc'])
                String=String+"alpha95"+": "+"%.1f\n"%float(mpars[mode]['alpha95'])
                String=String+"N"+": "+"%.0f\n"%float(mpars[mode]['n'])
                String=String+"K"+": "+"%.1f\n"%float(mpars[mode]['k'])
                String=String+"R"+": "+"%.4f\n"%float(mpars[mode]['r'])
                self.high_level_text_box.AppendText(String)
                
                                
        if mpars["calculation_type"]=='Bingham':
            String="Bingham statistics:\n"
            self.high_level_text_box.AppendText(String)
            String=""
            String=String+"dec"+": "+"%.1f\n"%float(mpars['dec'])
            String=String+"inc"+": "+"%.1f\n"%float(mpars['inc'])
            String=String+"n"+": "+"%.0f\n"%float(mpars['n'])
            String=String+"Zdec"+": "+"%.0f\n"%float(mpars['Zdec'])
            String=String+"Zinc"+": "+"%.1f\n"%float(mpars['Zinc'])
            String=String+"Zeta"+": "+"%.4f\n"%float(mpars['Zeta'])
            String=String+"Edec"+": "+"%.0f\n"%float(mpars['Edec'])
            String=String+"Einc"+": "+"%.1f\n"%float(mpars['Einc'])
            String=String+"Eta"+": "+"%.1f\n"%float(mpars['Eta'])
            self.high_level_text_box.AppendText(String)
                

                
            
                                                                               
                       
#============================================

    #-------------------------------
    # get_data:
    # Read data from magic_measurements.txt
    #-------------------------------

    def get_data(self):
      

      #def cart2dir(cart): # OLD ONE
      #      """
      #      converts a direction to cartesian coordinates
      #      """
      #      Dir=[] # establish a list to put directions in
      #      rad=pi/180. # constant to convert degrees to radians
      #      R=sqrt(cart[0]**2+cart[1]**2+cart[2]**2) # calculate resultant vector length
      #      if R==0:
      #         #print 'trouble in cart2dir'
      #         #print cart
      #         return [0.0,0.0,0.0]
      #      D=arctan2(cart[1],cart[0])/rad  # calculate declination taking care of correct quadrants (arctan2)
      #      if D<0:D=D+360. # put declination between 0 and 360.
      #      if D>360.:D=D-360.
      #      Dir.append(D)  # append declination to Dir list
      #      I=arcsin(cart[2]/R)/rad # calculate inclination (converting to degrees)
      #      Dir.append(I) # append inclination to Dir list
      #      Dir.append(R) # append vector length to Dir list
      #      return Dir # return the directions list


      #def dir2cart(d):
      # # converts list or array of vector directions, in degrees, to array of cartesian coordinates, in x,y,z
      #  ints=ones(len(d)).transpose() # get an array of ones to plug into dec,inc pairs
      #  d=array(d)
      #  rad=pi/180.
      #  if len(d.shape)>1: # array of vectors
      #      decs,incs=d[:,0]*rad,d[:,1]*rad
      #      if d.shape[1]==3: ints=d[:,2] # take the given lengths
      #  else: # single vector
      #      decs,incs=array(d[0])*rad,array(d[1])*rad
      #      if len(d)==3: 
      #          ints=array(d[2])
      #      else:
      #          ints=array([1.])
      #  cart= array([ints*cos(decs)*cos(incs),ints*sin(decs)*cos(incs),ints*sin(incs)]).transpose()
      #  return cart

      #self.dir_pathes=self.WD


      #------------------------------------------------
      # Read magic measurement file and sort to blocks
      #------------------------------------------------

      # All data information is stored in Data[secimen]={}
      Data={}
      Data_hierarchy={}
      Data_hierarchy['study']={}
      Data_hierarchy['locations']={}
      Data_hierarchy['sites']={}
      Data_hierarchy['samples']={}
      Data_hierarchy['specimens']={}
      Data_hierarchy['sample_of_specimen']={} 
      Data_hierarchy['site_of_specimen']={}   
      Data_hierarchy['site_of_sample']={}   
      Data_hierarchy['location_of_site']={}   
      Data_hierarchy['location_of_specimen']={}   
      Data_hierarchy['study_of_specimen']={}   
      Data_hierarchy['expedition_name_of_specimen']={}
      meas_data,file_type=pmag.magic_read(self.magic_file)

      self.GUI_log.write("-I- Read magic file  %s\n"%self.magic_file)

      # get list of unique specimen names
      
      CurrRec=[]
      # print "-I- get sids"

      sids=pmag.get_specs(meas_data) # samples ID's
      # print "-I- done get sids"

      # print "initialize blocks"
      
      for s in sids:

          if s not in Data.keys():
              Data[s]={}
              Data[s]['zijdblock']=[]
              Data[s]['zijdblock_geo']=[]
              Data[s]['zijdblock_tilt']=[]
              Data[s]['zijdblock_lab_treatments']=[]
              Data[s]['pars']={}
              Data[s]['zijdblock_steps']=[]
              #print "done initialize blocks"

      #print "sorting meas data"
          
      for rec in meas_data:
          s=rec["er_specimen_name"]
          sample=rec["er_sample_name"]
          site=rec["er_site_name"]
          location=rec["er_location_name"]
          expedition_name=""
          if "er_expedition_name" in rec.keys():
              expedition_name=rec["er_expedition_name"]

          #---------------------
          # sort data to Zijderveld block"
          # [tr,dec,inc,int,ZI,rec['measurement_flag'],rec['magic_instrument_codes']\
          # (ZI=0)
          #---------------------
          
          # list of excluded lab protocols. copied from pmag.find_dmag_rec(s,data)  
          EX=["LP-AN-ARM","LP-AN-TRM","LP-ARM-AFD","LP-ARM2-AFD","LP-TRM-AFD","LP-TRM","LP-TRM-TD","LP-X"] 
          INC=["LT-NO","LT-AF-Z","LT-T-Z", "LT-M-Z"]

          methods=rec["magic_method_codes"].split(":")
          for i in range (len(methods)):
               methods[i]=methods[i].strip()
          if 'measurement_flag' not in rec.keys():
              rec['measurement_flag']='g'
          SKIP=True;lab_treatment=""
          for meth in methods:
               if meth in ["LT-NO","LT-AF-Z","LT-T-Z", "LT-M-Z"]:
                   lab_treatment=meth
               if meth in INC:
                   SKIP=False
          for meth in EX:
               if meth in methods:
                   SKIP=True
          if not SKIP:
             tr=""
             if "LT-NO" in methods:
                 tr=0
                 measurement_step_unit=""   
                 LPcode=""
                 for method in methods:
                     if "AF" in method:
                         LPcode="LP-DIR-AF"
                         measurement_step_unit="mT"
                     if "TRM" in method:
                         LPcode="LP-DIR-T"
                         measurement_step_unit="C"
             elif "LT-AF-Z" in  methods:
                 tr = float(rec["treatment_ac_field"])*1e3 #(mT)
                 measurement_step_unit="mT" # in magic its T in GUI its mT
                 LPcode="LP-DIR-AF"
             elif  "LT-T-Z" in  methods:
                 tr = float(rec["treatment_temp"])-273. # celsius
                 measurement_step_unit="C" # in magic its K in GUI its C
                 LPcode="LP-DIR-T"
             elif  "LT-M-Z" in  methods:
                 tr = float(rec["measurement_number"]) # temporary for microwave
             else:
                 tr = float(rec["measurement_number"])
                                
             #if "LP-PI-TRM-IZ" in methods or "LP-PI-M-IZ" in methods:  # looking for in-field first thellier or microwave data - otherwise, just ignore this
             #    ZI=0
             #else:
             #    ZI=1
             ZI=0
             
             if tr !="":
                 Data[s]['zijdblock_lab_treatments'].append(lab_treatment)
                 if measurement_step_unit!="": 
                    if  'measurement_step_unit' in Data[s].keys():
                        if measurement_step_unit not in Data[s]['measurement_step_unit'].split(":"):
                            Data[s]['measurement_step_unit']=Data[s]['measurement_step_unit']+":"+measurement_step_unit
                    else:
                        Data[s]['measurement_step_unit']=measurement_step_unit
                 dec,inc,int = "","",""
                 if "measurement_dec" in rec.keys() and rec["measurement_dec"] != "":
                     dec=float(rec["measurement_dec"])
                 if "measurement_inc" in rec.keys() and rec["measurement_inc"] != "":
                     inc=float(rec["measurement_inc"])
                 if "measurement_magn_moment" in rec.keys() and rec["measurement_magn_moment"] != "":
                     intensity=float(rec["measurement_magn_moment"])
                 if 'magic_instrument_codes' not in rec.keys():
                     rec['magic_instrument_codes']=''
                 Data[s]['zijdblock'].append([tr,dec,inc,intensity,ZI,rec['measurement_flag'],rec['magic_instrument_codes']])
                 if 'magic_experiment_name' in Data[s].keys() and Data[s]['magic_experiment_name']!=rec["magic_experiment_name"]:
                      self.GUI_log.write("-E- ERROR: specimen %s has more than one demagnetization experiment name. You need to merge them to one experiment-name?\n")
                 if float(tr)==0 or float(tr)==273:
                    Data[s]['zijdblock_steps'].append("0")                     
                 else:
                    Data[s]['zijdblock_steps'].append("%.0f%s"%(tr,measurement_step_unit))
                 #--------------
                 Data[s]['magic_experiment_name']=rec["magic_experiment_name"]
                 if "magic_instrument_codes" in rec.keys():
                     Data[s]['magic_instrument_codes']=rec['magic_instrument_codes']
                 Data[s]["magic_method_codes"]=LPcode
                 #if "magic_method_codes" not in Data[s].keys():
                 #     Data[s]["magic_method_codes"]=":".join(methods)
                 #else:
                 #    old_methods=Data[s]["magic_method_codes"].split(":")
                 #    for method in methods:
                 #        if method not in old_methods:
                 #           old_methods.append(method)
                 #    Data[s]["magic_method_codes"]=":".join(old_methods)
                      
                             
                 #
                 
                 # gegraphic coordinates

                                  
                 try:
                    sample_azimuth=float(self.Data_info["er_samples"][sample]['sample_azimuth'])
                    sample_dip=float(self.Data_info["er_samples"][sample]['sample_dip'])                 
                    d_geo,i_geo=pmag.dogeo(dec,inc,sample_azimuth,sample_dip)
                    Data[s]['zijdblock_geo'].append([tr,d_geo,i_geo,intensity,ZI,rec['measurement_flag'],rec['magic_instrument_codes']])
                 except:
                    self.GUI_log.write( "-W- cant find sample_azimuth,sample_dip for sample %s\n"%sample) 

                 # tilt-corrected coordinates

                 try:
                    sample_bed_dip_direction=float(self.Data_info["er_samples"][sample]['sample_bed_dip_direction'])
                    sample_bed_dip=float(self.Data_info["er_samples"][sample]['sample_bed_dip'])                 
                    d_tilt,i_tilt=pmag.dotilt(d_geo,i_geo,sample_bed_dip_direction,sample_bed_dip)
                    Data[s]['zijdblock_tilt'].append([tr,d_tilt,i_tilt,intensity,ZI,rec['measurement_flag'],rec['magic_instrument_codes']])
                 except:
                    self.GUI_log.write("-W- cant find tilt-corrected data for sample %s\n"%sample) 
                    
                    #print methods
        
          #---------------------
          # hierarchy is determined from magic_measurements.txt
          #
          #---------------------
                 
          if sample not in Data_hierarchy['samples'].keys():
              Data_hierarchy['samples'][sample]={}
              Data_hierarchy['samples'][sample]['specimens']=[]
              
          if site not in Data_hierarchy['sites'].keys():
              Data_hierarchy['sites'][site]={}         
              Data_hierarchy['sites'][site]['samples']=[]         
              Data_hierarchy['sites'][site]['specimens']=[]      

          if location not in Data_hierarchy['locations'].keys():
              Data_hierarchy['locations'][location]={}         
              Data_hierarchy['locations'][location]['sites']=[]         
              Data_hierarchy['locations'][location]['samples']=[]         
              Data_hierarchy['locations'][location]['specimens']=[]      
          
          if   'this study' not in Data_hierarchy['study'].keys():
            Data_hierarchy['study']['this study']={}  
            Data_hierarchy['study']['this study']['sites']=[]         
            Data_hierarchy['study']['this study']['samples']=[]         
            Data_hierarchy['study']['this study']['specimens']=[]      
          
          if s not in Data_hierarchy['samples'][sample]['specimens']:
              Data_hierarchy['samples'][sample]['specimens'].append(s)

          if s not in Data_hierarchy['sites'][site]['specimens']:
              Data_hierarchy['sites'][site]['specimens'].append(s)

          if s not in Data_hierarchy['locations'][location]['specimens']:
              Data_hierarchy['locations'][location]['specimens'].append(s)

          if s not in Data_hierarchy['study']['this study']['specimens']:
              Data_hierarchy['study']['this study']['specimens'].append(s)

          if sample not in Data_hierarchy['sites'][site]['samples']:
              Data_hierarchy['sites'][site]['samples'].append(sample)

          if sample not in Data_hierarchy['locations'][location]['samples']:
              Data_hierarchy['locations'][location]['samples'].append(sample)

          if sample not in Data_hierarchy['study']['this study']['samples']:
              Data_hierarchy['study']['this study']['samples'].append(sample)

          if site not in Data_hierarchy['locations'][location]['sites']:
              Data_hierarchy['locations'][location]['sites'].append(site)

          if site not in Data_hierarchy['study']['this study']['sites']:
              Data_hierarchy['study']['this study']['sites'].append(site)

          #Data_hierarchy['specimens'][s]=sample
          Data_hierarchy['sample_of_specimen'][s]=sample  
          Data_hierarchy['site_of_specimen'][s]=site  
          Data_hierarchy['site_of_sample'][sample]=site
          Data_hierarchy['location_of_site'][site]=location
          Data_hierarchy['location_of_specimen'][s]=location
          if expedition_name!="":
            Data_hierarchy['expedition_name_of_specimen'][s]=expedition_name                      
                                                   
                                                                                     
          
      print "done sorting meas data"
      
      self.specimens=Data.keys()
      self.specimens.sort()

      #------------------------------------------------
      # analyze Zij block and save in dictionaries:
      # cartesian coordinates of the different datablocks:
      # Data[s]['zdata'] ;Data[s]['zdata_geo'];Data[s]['zijdblock_tilt']
      # cartesian datablocks Rotated to zijederveld block:
      # Data[s]['zij_rotated'] ;Data[s]['zij_rotated_geo'];Data[s]['zij_rotated_tilt']
      # VDS calculations:
      # Data[s]['vector_diffs']=array(vector_diffs)
      # Data[s]['vds']=vds
      #------------------------------------------------

      for s in self.specimens:
        # collected the data
        zijdblock=Data[s]['zijdblock']
        zijdblock_geo=Data[s]['zijdblock_geo']
        zijdblock_tilt=Data[s]['zijdblock_tilt']
        if len(zijdblock)<3:
            del Data[s]           
            continue

        #--------------------------------------------------------------
        # collect all zijderveld data to array and calculate VDS
        #--------------------------------------------------------------
        #z_treatments=[row[0] for row in zijdblock]
        zdata=[]
        zdata_geo=[]
        zdata_tilt=[]
        vector_diffs=[]
        NRM=zijdblock[0][3]

        for k in range(len(zijdblock)):
            # specimen coordinates
            DIR=[zijdblock[k][1],zijdblock[k][2],zijdblock[k][3]/NRM]
            cart=pmag.dir2cart(DIR)
            zdata.append(array([cart[0],cart[1],cart[2]]))
            # geographic coordinates
            if len(zijdblock_geo)!=0:
                DIR=[zijdblock_geo[k][1],zijdblock_geo[k][2],zijdblock_geo[k][3]/NRM]
                cart=pmag.dir2cart(DIR)
                zdata_geo.append(array([cart[0],cart[1],cart[2]]))
            # tilt-corrected coordinates
            if len(zijdblock_tilt)!=0:
                DIR=[zijdblock_tilt[k][1],zijdblock_tilt[k][2],zijdblock_tilt[k][3]/NRM]
                cart=pmag.dir2cart(DIR)
                zdata_tilt.append(array([cart[0],cart[1],cart[2]]))
            if k>0:
                vector_diffs.append(sqrt(sum((array(zdata[-2])-array(zdata[-1]))**2)))

        vector_diffs.append(sqrt(sum(array(zdata[-1])**2))) # last vector of the vds
        vds=sum(vector_diffs)  # vds calculation       

        Data[s]['vector_diffs']=array(vector_diffs)
        Data[s]['vds']=vds
        #Data[s]['z_treatments']=z_treatments
        Data[s]['zdata']=array(zdata)
        Data[s]['zdata_geo']=array(zdata_geo)
        Data[s]['zdata_tilt']=array(zdata_tilt)
        
        #--------------------------------------------------------------    
        # Rotate zijderveld plot
        #--------------------------------------------------------------
    
        
        #Data[s]['zij_rotated']=self.Rotate_zijderveld(Data[s]['zdata'],pmag.cart2dir(Data[s]['zdata'][0])[0])
        #Data[s]['zij_rotated_geo']=self.Rotate_zijderveld(Data[s]['zdata_geo'],pmag.cart2dir(Data[s]['zdata_geo'][0])[0])
        #Data[s]['zij_rotated_tilt']=self.Rotate_zijderveld(Data[s]['zdata_tilt'],pmag.cart2dir(Data[s]['zdata_tilt'][0])[0])
         
      return(Data,Data_hierarchy)

    def Rotate_zijderveld(self,Zdata,rot_declination):
        if len(Zdata)==0:
            return([])
        CART_rot=[]
        for i in range(0,len(Zdata)):
            DIR=pmag.cart2dir(Zdata[i])
            DIR[0]=(DIR[0]-rot_declination)%360.
            CART_rot.append(array(pmag.dir2cart(DIR)))
        CART_rot=array(CART_rot)        
        return(CART_rot)

    #def Rotate_zijderveld(self,Zdata,declination):
    #    if len(Zdata)==0:
    #        return([])
    #    DIR_rot=[]
    #    CART_rot=[]
    #    # rotate to be as NRM
    #    NRM_dir=pmag.cart2dir(Zdata[0])         
    #    NRM_dec=NRM_dir[0]
    #    NRM_dir[0]=0.
    #    CART_rot.append(pmag.dir2cart(NRM_dir))
    #    
    #    for i in range(1,len(Zdata)):
    #        DIR=pmag.cart2dir(Zdata[i])
    #        DIR[0]=(DIR[0]-NRM_dec)%360
    #        CART_rot.append(array(pmag.dir2cart(DIR)))
    #    CART_rot=array(CART_rot)        
    #    return(CART_rot)

    def read_magic_file(self,path,sort_by_this_name):
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
            if tmp_data[sort_by_this_name] in DATA.keys():
                self.GUI_log.write("-E- ERROR: magic file %s has more than one line for %s %s\n"%(path,sort_by_this_name,tmp_data[sort_by_this_name]))
            DATA[tmp_data[sort_by_this_name]]=tmp_data
        fin.close()        
        return(DATA)


    #-------------------------------
    # get_data_info:
    # Read data from er_* tables
    #-------------------------------

    def get_data_info(self):
        Data_info={}
        data_er_samples={}
        data_er_sites={}
        data_er_locations={}
        data_er_ages={}

        try:
            data_er_samples=self.read_magic_file(self.WD+"/er_samples.txt",'er_sample_name')
        except:
            self.GUI_log.write ("-W- Cant find er_sample.txt in project directory")

        try:
            data_er_sites=self.read_magic_file(self.WD+"/er_sites.txt",'er_site_name')
        except:
            self.GUI_log.write ("-W- Cant find er_sites.txt in project directory")

        try:
            data_er_locations=self.read_magic_file(self.WD+"/er_locations.txt",'er_location_name')
        except:
            self.GUI_log.write ("-W- Cant find er_locations.txt in project directory")

        try:
            data_er_ages=self.read_magic_file(self.WD+"/er_ages.txt",'er_sample_name')
        except:
            try:
                data_er_ages=self.read_magic_file(self.WD+"/er_ages.txt",'er_site_name')
            except:    
                self.GUI_log.write ("-W- Cant find er_ages in project directory")



        Data_info["er_samples"]=data_er_samples
        Data_info["er_sites"]=data_er_sites
        Data_info["er_locations"]=data_er_locations
        Data_info["er_ages"]=data_er_ages
        
        return(Data_info)

#    def get_pmag_table(self,table_name):
#        ''' 
#        read existing pmag table from working directory
#        '''
#        data_pmag_table={}
#        try:
#            data_pmag_table=self.read_magic_file(self.WD+"/"+table_name,'er_specimen_name')
#        except:
#            self.GUI_log.write ("-W- Cant find %s with old interpretation in project directory"%table_name)
#
#        return(data_pmag_table)
        
    def update_pmag_tables(self):
        
        pmag_specimens,file_type=pmag.magic_read(self.WD+"/"+"pmag_specimens.txt")
        pmag_samples,file_type=pmag.magic_read(self.WD+"/"+"pmag_samples.txt")
        pmag_sites,file_type=pmag.magic_read(self.WD+"/"+"pmag_sites.txt")
        self.GUI_log.write ("-I- Reading previous interpretations from pmag* tables\n")        
        #--------------------------
        # reads pmag_specimens.txt and 
        # update pmag_results_data['specimens'][specimen]
        # with the new interpertation
        #--------------------------
        
        #specimens = pmag.get_specs(pmag_specimens)
        #specimens.sort()
        for rec in pmag_specimens:
            specimen=rec['er_specimen_name']
            methods=rec['magic_method_codes'].strip("\n").replace(" ","").split(":")
            LPDIR=False;calculation_type=""
            for method in methods:
                if "LP-DIR" in method:
                    LPDIR=True
                if "DE-" in method:
                    calculation_type=method
            if LPDIR: # this a mean of directions
                if float(rec['measurement_step_min'])==0 or float(rec['measurement_step_min'])==273.:
                    tmin="0"
                elif float(rec['measurement_step_min'])>2: # thermal
                    tmin="%.0fC"%(float(rec['measurement_step_min'])-273.)
                else: # AF
                    tmin="%.0fmT"%(float(rec['measurement_step_min'])*1000.)

                if float(rec['measurement_step_max'])==0 or float(rec['measurement_step_max'])==273.:
                    tmax="0"
                elif float(rec['measurement_step_max'])>2: # thermal
                    tmax="%.0fC"%(float(rec['measurement_step_max'])-273.)
                else: # AF
                    tmax="%.0fmT"%(float(rec['measurement_step_max'])*1000.)
                
                
                #else:
                #    continue
                if calculation_type !="":                              
                    self.pmag_results_data['specimens'][specimen]={}
                    if specimen in self.Data.keys() and 'zijdblock_steps' in self.Data[specimen]\
                    and tmin in self.Data[specimen]['zijdblock_steps']\
                    and tmax in self.Data[specimen]['zijdblock_steps']:                        
                        #print "specimen,tmin,tmax",specimen,tmin,tmax
                        self.pmag_results_data['specimens'][specimen]['DA-DIR']=self.get_PCA_parameters(specimen,tmin,tmax,'specimen',calculation_type)
                        if len(self.Data[self.s]['zijdblock_geo'])>0:      
                            self.pmag_results_data['specimens'][specimen]['DA-DIR-GEO']=self.get_PCA_parameters(specimen,tmin,tmax,'geographic',calculation_type)                
                        if len(self.Data[self.s]['zijdblock_tilt'])>0:      
                            self.pmag_results_data['specimens'][specimen]['DA-DIR-TILT']=self.get_PCA_parameters(specimen,tmin,tmax,'tilt-corrected',calculation_type)                        
                    else:
                        self.GUI_log.write ( "-W- WARNING: Cant find specimen and steps of specimen %s tmin=%s, tmax=%s"%(specimen,tmin,tmax))
                        
        #--------------------------
        # reads pmag_sample.txt and 
        # if finds a mean in pmag_samples.txt
        # calculate the mean for self.high_level_means['samples'][samples]
        # If the program finds a codes "DE-FM","DE-FM-LP","DE-FM-UV"in magic_method_codes
        # then the program repeat teh fisher mean
        #--------------------------
        
        for rec in pmag_samples:
            methods=rec['magic_method_codes'].strip("\n").replace(" ","").split(":")
            sample=rec['er_sample_name'].strip("\n")
            LPDIR=False;calculation_method=""
            for method in methods:
                if "LP-DIR" in method:
                    LPDIR=True
                if "DE-" in method:
                    calculation_method=method
            if LPDIR: # this a mean of directions
                #if  calculation_method in ["DE-FM","DE-FM-LP","DE-FM-UV"]:
                    calculation_type="Fisher"
                    for dirtype in ['DA-DIR','DA-DIR-GEO','DA-DIR-TILT']: 
                        self.calculate_high_level_mean('samples',sample,calculation_type,'specimens')
        #--------------------------
        # reads pmag_sites.txt and 
        # if finds a mean in pmag_sites.txt
        # calculate the mean for self.high_level_means['sites'][site]
        # using specimens or samples, depends on the er_specimen_names or er_samples_names
        #  The program repeat the fisher calculation and oevrwrites it
        #--------------------------
        
        for rec in pmag_sites:
            methods=rec['magic_method_codes'].strip("\n").replace(" ","").split(":")
            site=rec['er_site_name'].strip("\n")
            LPDIR=False;calculation_method=""
            for method in methods:
                if "LP-DIR" in method or "DA-DIR" in method or "DE-FM" in method:
                    LPDIR=True
                if "DE-" in method:
                    calculation_method=method
            if LPDIR: # this a mean of directions
                if  calculation_method in ["DE-BS"]:
                    calculation_type="Bingham"
                else:
                    calculation_type="Fisher"
                if 'er_sample_names' in rec.keys() and len(rec['er_sample_names'].strip('\n').replace(" ","").split(":"))>0:
                    elements_type='samples'
                if 'er_specimen_names' in rec.keys() and len(rec['er_specimen_names'].strip('\n').replace(" ","").split(":"))>0:
                    elements_type='specimens'
                self.calculate_high_level_mean('sites',site,calculation_type,elements_type)
                #print "found previose interpretation",site,calculation_type,elements_type
            #print "this is sites"
            #print self.high_level_means['sites']        
               
                    
                
                    
            

    #-----------------------------------

    def get_preferences(self):
        #default
        preferences={}
        preferences['gui_resolution']=100.
        preferences['show_Zij_treatments']=True
        preferences['show_Zij_treatments_steps']=2.
        preferences['show_eqarea_treatments']=False
        #preferences['show_statistics_on_gui']=["int_n","int_ptrm_n","frac","scat","gmax","b_beta","int_mad","dang","f","fvds","g","q","drats"]#,'ptrms_dec','ptrms_inc','ptrms_mad','ptrms_angle']
        #try to read preferences file:
        try:
            import zeq_gui_preferences
            self.GUI_log.write( "-I- zeq_gui.preferences imported\n")
            preferences.update(thellier_gui_preferences.preferences)
        except:
            self.GUI_log.write( " -I- cant find zeq_gui_preferences file, using defualt default \n")
        return(preferences)

#==============================================================
# Menu Bar functions
#==============================================================

    #----------------------------------------------------------------------
        
    def create_menu(self):
        """ Create menu
        """
        self.menubar = wx.MenuBar()

        #-----------------                            

        #menu_preferences = wx.Menu()

        #m_preferences_apperance = menu_preferences.Append(-1, "&Appearence preferences", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_appearance_preferences, m_preferences_apperance)
        
        #m_preferences_stat = menu_preferences.Append(-1, "&Statistics preferences", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_preferences_stat, m_preferences_stat)

        #-----------------                            

        menu_file = wx.Menu()
        
        #m_change_working_directory = menu_file.Append(-1, "&Change project directory", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_change_working_directory, m_change_working_directory)

        #m_open_magic_file = menu_file.Append(-1, "&Open MagIC measurement file", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_open_magic_file, m_open_magic_file)

        submenu_save_plots = wx.Menu()

        m_save_zij_plot = submenu_save_plots.Append(-1, "&Save Zijderveld plot", "")
        self.Bind(wx.EVT_MENU, self.on_save_Zij_plot, m_save_zij_plot,"Zij")

        m_save_eq_plot = submenu_save_plots.Append(-1, "&Save specimen equal area plot", "")
        self.Bind(wx.EVT_MENU, self.on_save_Eq_plot, m_save_eq_plot,"specimen-Eq")

        m_save_M_t_plot = submenu_save_plots.Append(-1, "&Save M-t plot", "")
        self.Bind(wx.EVT_MENU, self.on_save_M_t_plot, m_save_M_t_plot,"M_t")

        m_save_high_level = submenu_save_plots.Append(-1, "&Save high level plot", "")
        self.Bind(wx.EVT_MENU, self.on_save_high_level, m_save_high_level,"Eq")

        #m_save_all_plots = submenu_save_plots.Append(-1, "&Save all plots", "")
        #self.Bind(wx.EVT_MENU, self.on_save_all_plots, m_save_all_plots)

        m_new_sub_plots = menu_file.AppendMenu(-1, "&Save plot", submenu_save_plots)

        
        menu_file.AppendSeparator()
        m_exit = menu_file.Append(-1, "E&xit\tCtrl-X", "Exit")
        self.Bind(wx.EVT_MENU, self.on_menu_exit, m_exit)
                                                                                                                                                                                                           
        #-----------------                            

        menu_Analysis = wx.Menu()

        submenu_criteria = wx.Menu()

        #m_set_criteria_to_default = submenu_criteria.Append(-1, "&Set acceptance criteria to default", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_default_criteria, m_set_criteria_to_default)

        m_change_criteria_file = submenu_criteria.Append(-1, "&Change acceptance criteria", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_criteria, m_change_criteria_file)

        m_import_criteria_file =  submenu_criteria.Append(-1, "&Import criteria file", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_criteria_file, m_import_criteria_file)

        m_new_sub = menu_Analysis.AppendMenu(-1, "Acceptance criteria", submenu_criteria)


        m_previous_interpretation = menu_Analysis.Append(-1, "&Import previous interpretation ('redo' file)", "")
        self.Bind(wx.EVT_MENU, self.on_menu_previous_interpretation, m_previous_interpretation)

        m_save_interpretation = menu_Analysis.Append(-1, "&Save current interpretations to a redo file", "")
        self.Bind(wx.EVT_MENU, self.on_menu_save_interpretation, m_save_interpretation)

        m_delete_interpretation = menu_Analysis.Append(-1, "&Clear all current interpretations", "")
        self.Bind(wx.EVT_MENU, self.on_menu_clear_interpretation, m_delete_interpretation)

        #-----------------                            

        menu_Tools = wx.Menu()
        m_prev_interpretation = menu_Tools.Append(-1, "&Blanket demagnetization", "")

        #-------------------
        
        menu_Plot= wx.Menu()
        m_plot_data = menu_Plot.Append(-1, "&Plot ...", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_plot_data, m_plot_data)

        #-------------------

        #menu_results_table= wx.Menu()
        #m_make_results_table = menu_results_table.Append(-1, "&Make results table", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_results_data, m_make_results_table)
        
        #menu_Auto_Interpreter = wx.Menu()
        
        #m_interpreter = menu_Auto_Interpreter.Append(-1, "&Run Thellier auto interpreter", "Run auto interpter")
        #self.Bind(wx.EVT_MENU, self.on_menu_run_interpreter, m_interpreter)

        #m_open_interpreter_file = menu_Auto_Interpreter.Append(-1, "&Open auto-interpreter output files", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_open_interpreter_file, m_open_interpreter_file)

        #m_open_interpreter_log = menu_Auto_Interpreter.Append(-1, "&Open auto-interpreter Warnings/Errors", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_open_interpreter_log, m_open_interpreter_log)

        #-----------------                            

        menu_MagIC= wx.Menu()
        #m_convert_to_magic= menu_MagIC.Append(-1, "&Convert generic files to MagIC format", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_convert_to_magic, m_convert_to_magic)
        #m_build_magic_model= menu_MagIC.Append(-1, "&Run MagIC model builder", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_MagIC_model_builder, m_build_magic_model)
        m_make_MagIC_results_tables= menu_MagIC.Append(-1, "&Save MagIC results tables", "")
        self.Bind(wx.EVT_MENU, self.on_menu_make_MagIC_results_tables, m_make_MagIC_results_tables)

        #-----------------                            
        
        #self.menubar.Append(menu_preferences, "& Preferences") 
        self.menubar.Append(menu_file, "&File")
        self.menubar.Append(menu_Analysis, "&Analysis")
        self.menubar.Append(menu_Tools, "&Tools")
        self.menubar.Append(menu_Plot, "&Plot")
        #self.menubar.Append(menu_results_table, "&Table")        
        self.menubar.Append(menu_MagIC, "&MagIC")        
        self.SetMenuBar(self.menubar)

    #============================================

    #--------------------------------------------------------------
    # File menu 
    #--------------------------------------------------------------

    def on_menu_exit(self, event):
        self.Destroy()
        exit()

    def on_save_Zij_plot(self, event):
        self.fig1.text(0.9,0.98,'%s'%(self.s),{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'right' })
        SaveMyPlot(self.fig1,self.s,"Zij")
        self.fig1.clear()
        self.draw_figure(self.s)
        self.update_selection()

    def on_save_Eq_plot(self, event):
        self.fig2.text(0.9,0.96,'%s'%(self.s),{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'right' })
        SaveMyPlot(self.fig2,self.s,"EqArea")
        self.fig2.clear()
        self.draw_figure(self.s)
        self.update_selection()
        
    def on_save_M_t_plot(self, event):
        self.fig3.text(0.9,0.96,'%s'%(self.s),{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'right' })
        SaveMyPlot(self.fig3,self.s,"M_M0")
        self.fig3.clear()
        self.draw_figure(self.s)
        self.update_selection()

    def on_save_high_level(self, event):
        #self.fig4.text(0.9,0.96,'%s'%(self.s),{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'right' })
        SaveMyPlot(self.fig4,str(self.level_names.GetValue()),str(self.level_box.GetValue())  )
        self.fig4.clear()
        self.draw_figure(self.s)
        self.update_selection()

    #--------------------------------------------------------------
    # Analysis menu Bar functions
    #--------------------------------------------------------------


    def on_menu_previous_interpretation(self,event):
        
        save_current_specimen=self.s
        """
        Create and show the Open FileDialog for upload previous interpretation
        input should be a valid "redo file":
        [specimen name] [tmin(kelvin)] [tmax(kelvin)]
        or 
        [specimen name] [tmin(Tesla)] [tmax(Tesla)]
        There is a problem with experiment that combines AF and thermal
        """
        dlg = wx.FileDialog(
            self, message="choose a file in a pmagpy redo format",
            defaultDir=self.currentDirectory, 
            defaultFile="",
            style=wx.OPEN | wx.CHANGE_DIR
            )
        if dlg.ShowModal() == wx.ID_OK:
            redo_file = dlg.GetPath()
        dlg.Destroy()

        self.read_redo_file(redo_file)    
    

    #----------------------------------------------------------------------

    def clear_interpretations(self):
        
        for specimen in self.pmag_results_data['specimens'].keys():
            del(self.pmag_results_data['specimens'][specimen])
            for high_level_type in ['samples','sites','locations','study']:
                self.high_level_means[high_level_type]={}
    #----------------------------------------------------------------------
            
    def read_redo_file(self,redo_file):
        """
        Read previous interpretation from a redo file
        and update gui with the new interpretation
        """
        self.GUI_log.write ("-I- read redo file and processing new bounds")
        self.redo_specimens={}
        # first delete all previous interpretation
        self.clear_interpretations
        fin=open(redo_file,'rU')
        for Line in fin.readlines():
            line=Line.strip('\n').split()
            specimen=line[0]
            tmin,tmax="",""
            if specimen in self.pmag_results_data['specimens'].keys() and 'DA-DIR' in self.pmag_results_data['specimens'][specimen].keys():
                print "-W- WARNING: more than one interpretations for specimen %s"%specimen
            calculation_type=line[1]
            if self.Data[specimen]['measurement_step_unit']=="C":
                if float(line[2])==0 or float(line[2])==273:
                    tmin="0"
                else:
                    tmin="%.0fC"%(float(line[2])-273)
                if float(line[3])==0 or float(line[3])==273:
                    tmax="0"
                else:
                    tmax="%.0fC"%(float(line[3])-273)
            elif self.Data[specimen]['measurement_step_unit']=="mT":
                if float(line[2])==0:
                    tmin="0"
                else:
                    tmin="%.0fmT"%(float(line[2])*1000)
                if float(line[3])==0:
                    tmax="0"
                else:
                    tmax="%.0fmT"%(float(line[3])*1000)
            else: # combimned experiment T:AF
                if float(line[2])==0:
                    tmin="0"
                elif "%.0fC"%(float(line[2])-273) in self.Data[specimen]['zijdblock_steps']:
                    tmin="%.0fC"%(float(line[2])-273)
                elif "%.0fmT"%(float(line[2])*1000) in self.Data[specimen]['zijdblock_steps']:
                    tmin="%.0fmT"%(float(line[2])*1000)
                else:
                    continue
                if float(line[3])==0:
                    tmax="0"
                elif "%.0fC"%(float(line[3])-273) in self.Data[specimen]['zijdblock_steps']:
                    tmax="%.0fC"%(float(line[3])-273)
                elif "%.0fmT"%(float(line[3])*1000) in self.Data[specimen]['zijdblock_steps']:
                    tmax="%.0fmT"%(float(line[3])*1000)
                else:
                    continue
            if tmin not in self.Data[specimen]['zijdblock_steps'] or  tmax not in self.Data[specimen]['zijdblock_steps']:
                print "-E- ERROR in redo file specimen %s. Cant find treatment steps"%specimen      
                                
            self.pmag_results_data['specimens'][specimen]={}             
            self.pmag_results_data['specimens'][specimen]['DA-DIR']=self.get_PCA_parameters(specimen,tmin,tmax,'specimen',calculation_type)
            if len(self.Data[self.s]['zijdblock_geo'])>0:      
                self.pmag_results_data['specimens'][specimen]['DA-DIR-GEO']=self.get_PCA_parameters(specimen,tmin,tmax,'geographic',calculation_type)                
            if len(self.Data[self.s]['zijdblock_tilt'])>0:      
                self.pmag_results_data['specimens'][specimen]['DA-DIR-TILT']=self.get_PCA_parameters(specimen,tmin,tmax,'tilt-corrected',calculation_type)                        
          
        fin.close()
        self.s=self.specimens_box.GetValue()
        self.update_selection()


    #----------------------------------------------------------------------

    def on_menu_save_interpretation(self,event):
        fout=open("demag_gui.redo",'w')
        specimens_list=self.pmag_results_data['specimens'].keys()
        specimens_list.sort()
        for specimen in specimens_list:
            if "DA-DIR" in self.pmag_results_data['specimens'][specimen].keys():
                STRING=specimen+"\t"
                STRING=STRING+self.pmag_results_data['specimens'][specimen]["DA-DIR"]["calculation_type"]+"\t"
                if self.pmag_results_data['specimens'][specimen]["DA-DIR"]['zijdblock_step_min']=="0":
                    tmin="0"
                elif "C" in self.pmag_results_data['specimens'][specimen]["DA-DIR"]['zijdblock_step_min']:
                    tmin="%.0f"%(float(self.pmag_results_data['specimens'][specimen]["DA-DIR"]['zijdblock_step_min'].split("C")[0])+273.)
                elif "mT" in self.pmag_results_data['specimens'][specimen]["DA-DIR"]['zijdblock_step_min']:
                    tmin="%.2e"%(float(self.pmag_results_data['specimens'][specimen]["DA-DIR"]['zijdblock_step_min'].split("mT")[0])/1000)
                if self.pmag_results_data['specimens'][specimen]["DA-DIR"]['zijdblock_step_max']=="0":
                    tmax="0"
                elif "C" in self.pmag_results_data['specimens'][specimen]["DA-DIR"]['zijdblock_step_max']:
                    tmax="%.0f"%(float(self.pmag_results_data['specimens'][specimen]["DA-DIR"]['zijdblock_step_max'].split("C")[0])+273.)
                elif "mT" in self.pmag_results_data['specimens'][specimen]["DA-DIR"]['zijdblock_step_max']:
                    tmax="%.2e"%(float(self.pmag_results_data['specimens'][specimen]["DA-DIR"]['zijdblock_step_max'].split("mT")[0])/1000)
                    
                STRING=STRING+tmin+"\t"+tmax+"\n"
                fout.write(STRING)
        TEXT="specimens interpretations are saved in demag_gui.redo"                
        dlg = wx.MessageDialog(self, caption="Saved",message=TEXT,style=wx.OK|wx.CANCEL )
        result = dlg.ShowModal()
        if result == wx.ID_OK:            
            dlg.Destroy()
               
     #----------------------------------------------------------------------
               
                
        
                
                                
    def on_menu_clear_interpretation(self,event):
        self.clear_interpretations()
        self.s=self.specimens_box.GetValue()
        self.update_selection()
        
    #--------------------------------------------------------------
    # MagIC menu 
    #--------------------------------------------------------------
    
    def  on_menu_make_MagIC_results_tables(self,event):

        #---------------------------------------            
        # 1. read pmag_specimens.txt, pmag_samples.txt, pmag_sites.txt, and sort out lines with LP-DIR in magic_codes 
        # 2. saves a clean pmag_*.txt files without LP-DIR stuff as pmag_*.txt.tmp .
        # 3. write a new file pmag_specimens.txt
        # 4. merge pmag_specimens.txt and pmag_specimens.txt.tmp using combine_magic.py 
        # 5. delete pmag_specimens.txt.tmp
        
        # 6 (optional) extracting new pag_*.txt files (except pmag_specimens.txt) using specimens_results_magic.py
        # 7: if #6: merge pmag_*.txt and pmag_*.txt.tmp using combine_magic.py 
        #    if not #6: save pmag_*.txt.tmp as pmag_*.txt
        #---------------------------------------            

        #---------------------------------------
        # save pmag_*.txt.tmp without directional data           
        #---------------------------------------  
        
        PmagRecsOld={}
        for FILE in ['pmag_specimens.txt','pmag_samples.txt','pmag_sites.txt','pmag_results']:
            PmagRecsOld[FILE]=[]
            try: 
                meas_data,file_type=pmag.magic_read(self.WD+"/"+FILE)
                self.GUI_log.write("-I- Read old magic file  %s\n"%self.WD+"/"+FILE)
                if FILE !='pmag_specimens.txt':
                    os.remove(self.WD+"/"+FILE)
                    self.GUI_log.write("-I- Delete old magic file  %s\n"%self.WD+"/"+FILE)
                               
            except:
                continue                                                                           
            for rec in meas_data:
                if "magic_method_codes" in rec.keys():
                    if "LP-DIR" not in rec['magic_method_codes'] and "DE-" not in  rec['magic_method_codes']:
                        PmagRecsOld[FILE].append(rec)
            #pmag.magic_write(self.WD+"/"+FILE+".tmp",PmagRecs,FILE.split(".")[0])
            #self.GUI_log.write("-I- Write magic file  %s\n"%self.WD+"/"+FILE+".tmp") 

        #---------------------------------------
        # write a new pmag_specimens.txt       
        #---------------------------------------  
                                  
        specimens_list=self.pmag_results_data['specimens'].keys()
        specimens_list.sort()
        PmagSpecs=[]
        for specimen in specimens_list:
            if 'DA-DIR' not in self.pmag_results_data['specimens'][specimen].keys() or self.pmag_results_data['specimens'][specimen]['DA-DIR']=={}:
                continue
            for dirtype in ['DA-DIR','DA-DIR-GEO','DA-DIR-TILT']:
                PmagSpecRec={}
                user="" # Todo
                PmagSpecRec["er_analyst_mail_names"]=user
                PmagSpecRec["magic_software_packages"]=pmag.get_version()
                PmagSpecRec["er_specimen_name"]=specimen
                PmagSpecRec["er_sample_name"]=self.Data_hierarchy['sample_of_specimen'][specimen]
                PmagSpecRec["er_site_name"]=self.Data_hierarchy['site_of_specimen'][specimen]
                PmagSpecRec["er_location_name"]=self.Data_hierarchy['location_of_specimen'][specimen]
                if specimen in self.Data_hierarchy['expedition_name_of_specimen'].keys():
                    PmagSpecRec["er_expedition_name"]=self.Data_hierarchy['expedition_name_of_specimen'][specimen]
                #else:
                #    PmagSpecRec["er_expedition_name"]=""
                PmagSpecRec["er_citation_names"]="This study"
                PmagSpecRec["magic_experiment_names"]=self.Data[specimen]["magic_experiment_name"]
                if 'magic_instrument_codes' in self.Data[specimen].keys():
                    PmagSpecRec["magic_instrument_codes"]= self.Data[specimen]['magic_instrument_codes']
                #magic_method_codes=[]
                #all_methods=self.Data[specimen]['magic_method_codes'].strip('\n').replace(" ","").split(":")
                #for method in all_methods:
                #    if "LP" in method:
                #        magic_method_codes.append(method)
                #if 
                #-------
                OK=False
                if dirtype in self.pmag_results_data['specimens'][specimen].keys():
                    if  self.pmag_results_data['specimens'][specimen][dirtype]!={}:
                        OK=True
                if not OK:
                    continue
                #if self.Data[specimen]['measurement_step_unit']=="C":
                #     PmagSpecRec['measurement_step_unit']="K"
                #else:
                #     PmagSpecRec['measurement_step_unit']="T"
                    
                #PmagSpecRec['measurement_step_unit']=self.Data[specimen]['measurement_step_unit'] 
                PmagSpecRec['specimen_correction']='u'
                mpars=self.pmag_results_data['specimens'][specimen][dirtype]
                PmagSpecRec['specimen_direction_type'] = mpars["specimen_direction_type"]
                PmagSpecRec['specimen_dec'] = "%.1f"%mpars["specimen_dec"]
                PmagSpecRec['specimen_inc'] = "%.1f"%mpars["specimen_inc"]
                
                if  mpars['zijdblock_step_min'] =="0":
                     PmagSpecRec['measurement_step_min'] ="0"
                elif "C" in mpars['zijdblock_step_min']:
                    PmagSpecRec['measurement_step_min'] = "%.0f"%(mpars["measurement_step_min"]+273.)
                else:
                    PmagSpecRec['measurement_step_min'] = "%8.3e"%(mpars["measurement_step_min"]*1e-3)
                
                if  mpars['zijdblock_step_max'] =="0":
                     PmagSpecRec['measurement_step_max'] ="0"
                elif "C" in mpars['zijdblock_step_max']:
                    PmagSpecRec['measurement_step_max'] = "%.0f"%(mpars["measurement_step_max"]+273.)
                else:
                    PmagSpecRec['measurement_step_max'] = "%8.3e"%(mpars["measurement_step_max"]*1e-3)
                if "C" in   mpars['zijdblock_step_min']  or "C" in mpars['zijdblock_step_min']:
                    PmagSpecRec['measurement_step_unit']="C"
                else:
                    PmagSpecRec['measurement_step_unit']="T"                                  
                PmagSpecRec['specimen_n'] = "%.0f"%mpars["specimen_n"]
                calculation_type=mpars['calculation_type']
                PmagSpecRec["magic_method_codes"]=self.Data[specimen]['magic_method_codes']+":"+calculation_type+":"+dirtype               
                if calculation_type in ["DE-BFL","DE-BFL-A","DE-BFL-O"]:
                    PmagSpecRec['specimen_direction_type']='l'
                    PmagSpecRec['specimen_mad']="%.1f"%float(mpars["specimen_mad"])
                    PmagSpecRec['specimen_dang']="%.1f"%float(mpars['specimen_dang'])
                    PmagSpecRec['specimen_alpha95']=""
                elif calculation_type in ["DE-BFP"]:
                    PmagSpecRec['specimen_direction_type']='p'
                    PmagSpecRec['specimen_mad']="%.1f"%float(mpars['specimen_mad'])
                    PmagSpecRec['specimen_dang']=""
                    PmagSpecRec['specimen_alpha95']=""
                elif calculation_type in ["DE-FM"]:
                    PmagSpecRec['specimen_direction_type']='l'
                    PmagSpecRec['specimen_mad']=""
                    PmagSpecRec['specimen_dang']=""
                    PmagSpecRec['specimen_alpha95']="%.1f"%float(mpars['specimen_alpha95'])
                if dirtype=='DA-DIR-TILT':
                    PmagSpecRec['specimen_tilt_correction']="100"
                elif dirtype=='DA-DIR-GEO':
                    PmagSpecRec['specimen_tilt_correction']="0"
                else:
                    PmagSpecRec['specimen_tilt_correction']="-1"
                PmagSpecs.append(PmagSpecRec)    
        # add the 'old' lines with no "LP-DIR" in 
        for rec in PmagRecsOld['pmag_specimens.txt']:
            PmagSpecs.append(rec)
        PmagSpecs_fixed=self.merge_pmag_recs(PmagSpecs)
        pmag.magic_write(self.WD+"/"+"pmag_specimens.txt",PmagSpecs_fixed,'pmag_specimens')
        self.GUI_log.write( "specimen data stored in %s\n"%self.WD+"/"+"pmag_specimens.txt")
        
        TEXT="specimen results are saved in pmag_specimens.txt.\nPress OK for MagIC results tables options."
        dlg = wx.MessageDialog(self, caption="Saved",message=TEXT,style=wx.OK|wx.CANCEL )
        result = dlg.ShowModal()
        if result == wx.ID_OK:            
            dlg.Destroy()
        if result == wx.ID_CANCEL:            
            dlg.Destroy()
            return
            
        #--------------------------------
                
        dia = demag_dialogs.magic_pmag_tables_dialog(None,self.WD,self.Data,self.Data_info)
        dia.Center()

        if dia.ShowModal() == wx.ID_OK: # Until the user clicks OK, show the message            
            self.On_close_MagIC_dialog(dia)
                                                      
    def On_close_MagIC_dialog(self,dia):
        # run specimens_results_magic.py
        
        #-- acceptance criteria
        run_script_flags=["specimens_results_magic.py","-fsp", "pmag_specimens.txt", "-xI", "-WD", str(self.WD)]
        if dia.cb_acceptance_criteria.GetValue()==True:
            run_script_flags.append("-exc")
        else:
            run_script_flags.append("-C")

        #-- coordinate system
        if dia.rb_spec_coor.GetValue()==True:
            run_script_flags.append("-crd");  run_script_flags.append("s")       
        if dia.rb_geo_coor.GetValue()==True:
            run_script_flags.append("-crd");  run_script_flags.append("g")       
        if dia.rb_tilt_coor.GetValue()==True:
            run_script_flags.append("-crd");  run_script_flags.append("t")       
        if dia.rb_geo_tilt_coor.GetValue()==True:
            rb_geo_tilt_coor.append("-crd");  run_script_flags.append("b")       
        
        #-- default age options 
        if dia.cb_default_age.GetValue()==True:
            try:
                min_age="%f"%float(dia.default_age_min.GetValue()) 
                max_age="%f"%float(dia.default_age_max.GetValue())
            except:
                pass
            age_units= dia.default_age_unit.GetValue()       
            run_script_flags.append("-age"); run_script_flags.append(min_age)
            run_script_flags.append(max_age); run_script_flags.append(age_units)

        #-- sample mean 
        if dia.cb_sample_mean.GetValue()==True:
            run_script_flags.append("-aD") 
                
        if dia.cb_sample_mean_VGP.GetValue()==True:
            run_script_flags.append("-sam") 

        #-- site mean
         
        if dia.cb_site_mean.GetValue()==True:
            pass
            
        #-- location mean
         
        if dia.cb_location_mean.GetValue()==True:
            run_script_flags.append("-pol")
            
        #print  run_script_flags
        subprocess.call(run_script_flags, shell=True)
        print "-I- running python script:\n %s"%(" ".join(run_script_flags))
        # reads new pmag tables, and merge the old lines:
        for FILE in ['pmag_samples.txt','pmag_sites.txt','pmag_results.txt']:
            pmag_data=[]
            try:
                pmag_data,file_type=pmag.magic_read(self.WD+"/"+FILE)
                for rec in PmagRecsOld[FILE]:
                    pmag_data.append(rec)
                pmag_data_fixed=self.merge_pmag_recs(pmag_data)
                pmag.magic_write(self.WD+"/"+FILE,pmag_data_fixed,FILE.split(".")[0])
                self.GUI_log.write( "write new interpretations in %s\n"%(self.WD+"/"+FILE))
            except:
                self.GUI_log.write( "ignore file when writing results tables: %s\n"%(self.WD+"/"+FILE))

        self.update_pmag_tables()
        self.update_selection()
        TEXT="interpretations are saved in pmag tables\n"
        dlg = wx.MessageDialog(self, caption="Saved",message=TEXT,style=wx.OK)
        result = dlg.ShowModal()
        if result == wx.ID_OK:            
            dlg.Destroy()
                        

    def merge_pmag_recs(self,old_recs):
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
            
                        
#--------------------------------------------------------------    
# Save plots
#--------------------------------------------------------------

class SaveMyPlot(wx.Frame):
    """"""
    def __init__(self,fig,name,plot_type):
        """Constructor"""
        wx.Frame.__init__(self, parent=None, title="")

        file_choices="(*.pdf)|*.pdf|(*.svg)|*.svg| (*.png)|*.png"
        default_fig_name="%s_%s.pdf"%(name,plot_type)
        dlg = wx.FileDialog(
            self, 
            message="Save plot as...",
            defaultDir=os.getcwd(),
            defaultFile=default_fig_name,
            wildcard=file_choices,
            style=wx.SAVE)
        
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            
        title=name
        self.panel = wx.Panel(self)
        self.dpi=300

        canvas_tmp_1 = FigCanvas(self.panel, -1, fig)
        canvas_tmp_1.print_figure(path, dpi=self.dpi)  




#--------------------------------------------------------------    
# Run the GUI
#--------------------------------------------------------------
def alignToTop(win):
    dw, dh = wx.DisplaySize() 
    w, h = win.GetSize() 
    #x = dw - w
    #y = dh - h
    
    win.SetPosition(((dw-w)/2.,0 ))

#def resize(win):
#    dw, dh = wx.DisplaySize() 
#    w, h = win.GetSize()
#    if  dw>w:
#        #win.GUI_RESOLUTION=1.5
#        print "gui respoluyion"
    


if __name__ == '__main__':
    app = wx.PySimpleApp()
    app.frame = Zeq_GUI()
    app.frame.Center()
    #alignToTop(app.frame)
    dw, dh = wx.DisplaySize() 
    w, h = app.frame.GetSize()
    #print 'display 2', dw, dh
    #print "gui 2", w, h
    app.frame.Show()
    app.MainLoop()

        

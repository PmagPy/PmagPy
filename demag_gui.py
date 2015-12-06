#!/bin/env pythonw

#============================================================================================
# LOG HEADER:
#============================================================================================
#
# Demag_GUI Version 0.33 add interpretation editor, plane plotting functionality and more
# propose merging development fork to main PmagPy repository (11/09/2015)
#
# Demag_GUI Version 0.32 added multiple interpretations and new plot functionality by Kevin Gaastra (05/03/2015)
#
# Demag_GUI Version 0.31 save MagIC tables option: add dialog box to choose coordinates system for pmag_specimens.txt 04/26/2015
#
# Demag_GUI Version 0.30 fix backward compatibility with strange pmag_specimens.txt 01/29/2015
#
# Demag_GUI Version 0.29 fix on_close_event 23/12/2014
#
# Demag_GUI Version 0.28 fix on_close_event 12/12/2014
#
# Demag_GUI Version 0.27 some minor bug fix
#
# Demag_GUI Version 0.26 (version for MagIC workshop) by Ron Shaar 5/8/2014
#
# Demag_GUI Version 0.25 (beta) by Ron Shaar
#
# Demag_GUI Version 0.24 (beta) by Ron Shaar
#
# Demag_GUI Version 0.23 (beta) by Ron Shaar
#
# Demag_GUI Version 0.22 (beta) by Ron Shaar
#
# Demag_GUI Version 0.21 (beta) by Ron Shaar
#
#============================================================================================


#--------------------------------------
# definitions
#--------------------------------------

import os
global CURRENT_VERSION, PMAGPY_DIRECTORY
CURRENT_VERSION = "v.0.33"
path = os.path.abspath(__file__)
PMAGPY_DIRECTORY = os.path.dirname(path)
import matplotlib
#import matplotlib.font_manager as font_manager
matplotlib.use('WXAgg')

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar

import sys,os
try:
    import zeq_gui_preferences
except:
    pass
import stat
import subprocess
import time
from datetime import datetime
import wx
import wx.grid
import wx.lib.scrolledpanel
import random
import re
import numpy
from pylab import rcParams,Figure,arange,pi,cos,sin,array,sqrt,mean
from scipy.optimize import curve_fit
import wx.lib.agw.floatspin as FS
import webbrowser
try:
    from mpl_toolkits.basemap import Basemap, shiftgrid
except:
    pass

import pmag,demag_dialogs,ipmag
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
import copy
from copy import deepcopy


matplotlib.rc('xtick', labelsize=10)
matplotlib.rc('ytick', labelsize=10)
matplotlib.rc('axes', labelsize=8)
matplotlib.rcParams['savefig.dpi'] = 300.

#rcParams.update({"svg.embed_char_paths":False})
rcParams.update({"svg.fonttype":'svgfont'})


#--------------------------------------
# ZEQ GUI FRAME
#--------------------------------------

class Zeq_GUI(wx.Frame):
    """
    The main frame of the application
    """
    title = "PmagPy Demag GUI %s (beta)"%CURRENT_VERSION

    def __init__(self, WD, parent=None):

        TEXT="""
        NAME:
   	demag_gui.py

        DESCRIPTION:
   	GUI for interpreting demagnetization data (AF and/or thermal).
   	For tutorial chcek PmagPy cookbook in http://earthref.org/PmagPy/cookbook/
        """
        args=sys.argv
        if "-h" in args:
            print TEXT
            sys.exit()

        global FIRST_RUN
        FIRST_RUN=True

        # wx.Frame.__init__(self, None, wx.ID_ANY, self.title) merge confilct testing

        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title, name='demag gui')
        self.parent = parent #BLARGE

        self.redo_specimens={}
        self.currentDirectory = os.getcwd() # get the current working directory
        if WD:
            self.WD = WD
            self.get_DIR(WD)        # initialize directory variables
        else:
            self.get_DIR()        # choose directory dialog, then initialize directory variables

        #set icon
        icon = wx.EmptyIcon()
        icon.CopyFromBitmap(wx.Bitmap(os.path.join(PMAGPY_DIRECTORY, "images/PmagPy.ico"), wx.BITMAP_TYPE_ANY))
        self.SetIcon(icon)

        # initialize acceptence criteria with NULL values
        self.acceptance_criteria=pmag.initialize_acceptance_criteria()
        try:
            self.acceptance_criteria=pmag.read_criteria_from_file(os.path.join(self.WD, "pmag_criteria.txt"), self.acceptance_criteria)
        except:
            print "-I- Cant find/read file  pmag_criteria.txt"


        preferences=self.get_preferences()
        self.dpi = 100
        self.preferences={}
        self.preferences=preferences

        # initialize selecting criteria
        self.COORDINATE_SYSTEM='geographic'
        self.UPPER_LEVEL_SHOW='specimens'
        self.Data_info=self.get_data_info() # Read  er_* data
        self.Data,self.Data_hierarchy=self.get_data() # Get data from magic_measurements and rmag_anistropy if exist.


        self.pmag_results_data={}
        for level in ['specimens','samples','sites','lcoations','study']:
            self.pmag_results_data[level]={}

        self.high_level_means={}
        for high_level in ['samples','sites','locations','study']:
            if high_level not in self.high_level_means.keys():
                self.high_level_means[high_level]={}

        #BLARGE
        self.interpretation_editor_open = False
        self.color_dict = {'green':'g','yellow':'y','maroon':'m','cyan':'c','black':'k','brown':(139./255.,69./255.,19./255.),'orange':(255./255.,127./255.,0./255.),'pink':(255./255.,20./255.,147./255.),'violet':(153./255.,50./255.,204./255.),'grey':(84./255.,84./255.,84./255.)}
        self.colors = ['g','y','m','c','k',(139./255.,69./255.,19./255.),(255./255.,127./255.,0./255.),(255./255.,20./255.,147./255.),(153./255.,50./255.,204./255.),(84./255.,84./255.,84./255.)] #for fits
        self.current_fit = None
        self.dirtypes = ['DA-DIR','DA-DIR-GEO','DA-DIR-TILT']
        self.bad_fits = []

        self.Data_samples={}
        self.last_saved_pars={}
        self.specimens=self.Data.keys()         # get list of specimens
        self.specimens.sort(cmp=specimens_comparator) # get list of specimens
        if len(self.specimens)>0:
            self.s=str(self.specimens[0])
        else:
            self.s=""
        self.samples=self.Data_hierarchy['samples'].keys()         # get list of samples
        self.samples.sort()                   # get list of specimens
        self.sites=self.Data_hierarchy['sites'].keys()         # get list of sites
        self.sites.sort()                   # get list of sites
        self.locations=self.Data_hierarchy['locations'].keys()      # get list of sites
        self.locations.sort()                   # get list of sites

        w, h = self.GetSize()
        self.panel = wx.lib.scrolledpanel.ScrolledPanel(self,-1,size=(w,h)) # make the Panel
        self.panel.SetupScrolling()
        self.Main_Frame()                   # build the main frame
        self.create_menu()                  # create manu bar
        self.arrow_keys()
        self.Bind(wx.EVT_CLOSE, self.on_menu_exit)
        FIRST_RUN=False
        self.close_warning=False


    def Main_Frame(self):
        """
        Build main frame of panel: buttons, etc.
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
            self.s=str(self.specimens[0])
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

        self.fig1 = Figure((5.*self.GUI_RESOLUTION, 5.*self.GUI_RESOLUTION), dpi=self.dpi)
        self.canvas1 = FigCanvas(self.panel, -1, self.fig1)
        self.toolbar1 = NavigationToolbar(self.canvas1)
        self.toolbar1.Hide()
        self.zijderveld_setting = "Zoom"
        self.toolbar1.zoom()
        self.canvas1.Bind(wx.EVT_RIGHT_DOWN,self.right_click_zijderveld)
        self.canvas1.Bind(wx.EVT_MIDDLE_DOWN,self.home_zijderveld)
#        self.canvas1.Bind(wx.EVT_LEFT_DCLICK,self.pick_bounds)
        #self.fig1.text(0.01,0.98,"Zijderveld plot",{'family':'Arial', 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })

        self.fig2 = Figure((2.5*self.GUI_RESOLUTION, 2.5*self.GUI_RESOLUTION), dpi=self.dpi)
        self.specimen_eqarea_net = self.fig2.add_subplot(111)
        self.draw_net(self.specimen_eqarea_net)
        self.specimen_eqarea = self.fig2.add_axes(self.specimen_eqarea_net.get_position(), frameon=False,axisbg='None')
        self.specimen_eqarea_interpretation = self.fig2.add_axes(self.specimen_eqarea_net.get_position(), frameon=False,axisbg='None')
        self.specimen_eqarea_interpretation.axes.set_aspect('equal')
        self.specimen_eqarea_interpretation.axis('off')
        self.canvas2 = FigCanvas(self.panel, -1, self.fig2)
        self.toolbar2 = NavigationToolbar(self.canvas2)
        self.toolbar2.Hide()
        self.toolbar2.zoom()
        self.specimen_EA_setting = "Zoom"
        self.canvas2.Bind(wx.EVT_LEFT_DCLICK,self.on_equalarea_specimen_select)
        self.canvas2.Bind(wx.EVT_RIGHT_DOWN,self.right_click_specimen_equalarea)
        self.canvas2.Bind(wx.EVT_MOTION,self.on_change_specimen_mouse_cursor)
        self.canvas2.Bind(wx.EVT_MIDDLE_DOWN,self.home_specimen_equalarea)
        self.specimen_EA_xdata = []
        self.specimen_EA_ydata = []

        self.fig3 = Figure((2.5*self.GUI_RESOLUTION, 2.5*self.GUI_RESOLUTION), dpi=self.dpi)
        self.canvas3 = FigCanvas(self.panel, -1, self.fig3)
        self.toolbar3 = NavigationToolbar(self.canvas3)
        self.toolbar3.Hide()
        self.toolbar3.zoom()
        self.MM0_setting = "Zoom"
        self.canvas3.Bind(wx.EVT_RIGHT_DOWN, self.right_click_MM0)
        self.canvas3.Bind(wx.EVT_MIDDLE_DOWN, self.home_MM0)

        self.fig4 = Figure((2.5*self.GUI_RESOLUTION, 2.5*self.GUI_RESOLUTION), dpi=self.dpi)
        self.canvas4 = FigCanvas(self.panel, -1, self.fig4)
        self.toolbar4 = NavigationToolbar(self.canvas4)
        self.toolbar4.Hide()
        self.toolbar4.zoom()
        self.higher_EA_setting = "Zoom"
        self.canvas4.Bind(wx.EVT_LEFT_DCLICK,self.on_equalarea_higher_select)
        self.canvas4.Bind(wx.EVT_RIGHT_DOWN,self.right_click_higher_equalarea)
        self.canvas4.Bind(wx.EVT_MOTION,self.on_change_higher_mouse_cursor)
        self.canvas4.Bind(wx.EVT_MIDDLE_DOWN,self.home_higher_equalarea)
        self.old_pos = None
        self.higher_EA_xdata = []
        self.higher_EA_ydata = []



        self.high_level_eqarea_net = self.fig4.add_subplot(111)
        self.draw_net(self.high_level_eqarea_net)
        self.high_level_eqarea = self.fig4.add_axes(self.high_level_eqarea_net.get_position(), frameon=False,axisbg='None')
        self.high_level_eqarea_interpretation = self.fig4.add_axes(self.high_level_eqarea_net.get_position(), frameon=False,axisbg='None')
        self.high_level_eqarea_interpretation.axis('equal')
        self.high_level_eqarea_interpretation.axis('off')


 #----------------------------------------------------------------------
        #  set font size and style
 #----------------------------------------------------------------------

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

        self.logger = wx.ListCtrl(self.panel, -1, size=(200*self.GUI_RESOLUTION,300*self.GUI_RESOLUTION),style=wx.LC_REPORT)
        self.logger.SetFont(font1)
        self.logger.InsertColumn(0, 'i',width=25*self.GUI_RESOLUTION)
        self.logger.InsertColumn(1, 'Step',width=25*self.GUI_RESOLUTION)
        self.logger.InsertColumn(2, 'Tr',width=35*self.GUI_RESOLUTION)
        self.logger.InsertColumn(3, 'Dec',width=35*self.GUI_RESOLUTION)
        self.logger.InsertColumn(4, 'Inc',width=35*self.GUI_RESOLUTION)
        self.logger.InsertColumn(5, 'M',width=45*self.GUI_RESOLUTION)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnClick_listctrl, self.logger)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK,self.OnRightClickListctrl,self.logger)

 #----------------------------------------------------------------------
        #  select specimen box
 #----------------------------------------------------------------------

        self.box_sizer_select_specimen = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY), wx.VERTICAL )

        # Combo-box with a list of specimen
        self.specimens_box = wx.ComboBox(self.panel, -1, value=self.s,choices=self.specimens, style=wx.CB_DROPDOWN,name="specimen")
        self.Bind(wx.EVT_COMBOBOX, self.onSelect_specimen,self.specimens_box)

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
        self.coordinate_list = ['specimen']
        intial_coordinate = 'specimen'
        for specimen in self.specimens:
            if 'geographic' not in self.coordinate_list and self.Data[specimen]['zijdblock_geo']:
                self.coordinate_list.append('geographic')
                intial_coordinate = 'geographic'
            if 'tilt-corrected' not in self.coordinate_list and self.Data[specimen]['zijdblock_tilt']:
                self.coordinate_list.append('tilt-corrected')
        self.coordinates_box = wx.ComboBox(self.panel, -1, choices=self.coordinate_list, value=intial_coordinate,style=wx.CB_DROPDOWN,name="coordinates")
        self.Bind(wx.EVT_COMBOBOX, self.onSelect_coordinates,self.coordinates_box)
        self.orthogonal_box = wx.ComboBox(self.panel, -1, value='X=East', choices=['X=NRM dec','X=East','X=North','X=best fit line dec'], style=wx.CB_DROPDOWN,name="orthogonal_plot")
        self.Bind(wx.EVT_COMBOBOX, self.onSelect_orthogonal_box,self.orthogonal_box)

        self.box_sizer_select_specimen.Add(wx.StaticText(self.panel,label="specimen:",style=wx.TE_CENTER))
        self.box_sizer_select_specimen.Add(self.specimens_box, 0, wx.TOP, 0 )
        self.box_sizer_select_specimen.Add(select_specimen_window, 0, wx.TOP, 4 )
        self.box_sizer_select_specimen.Add(wx.StaticLine(self.panel), 0, wx.ALL|wx.EXPAND, 5)
        self.box_sizer_select_specimen.Add(wx.StaticText(self.panel,label="coordinate system:",style=wx.TE_CENTER))
        self.box_sizer_select_specimen.Add(self.coordinates_box, 0, wx.TOP, 4 )
        self.box_sizer_select_specimen.Add(wx.StaticLine(self.panel), 0, wx.ALL|wx.EXPAND, 5)
        self.box_sizer_select_specimen.Add(wx.StaticText(self.panel,label="Zijderveld plot options:",style=wx.TE_CENTER))
        self.box_sizer_select_specimen.Add(self.orthogonal_box, 0, wx.TOP, 4 )

 #----------------------------------------------------------------------
        #  fit box
 #----------------------------------------------------------------------

        list_fits = []

        self.box_sizer_fit = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "interpretations" ), wx.VERTICAL )

        self.fit_box = wx.ComboBox(self.panel, -1 ,size=(100*self.GUI_RESOLUTION, 25),choices=list_fits, style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_COMBOBOX, self.on_select_fit,self.fit_box)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_enter_fit_name, self.fit_box)

        self.add_fit_button = wx.Button(self.panel, id=-1, label='add fit',size=(100*self.GUI_RESOLUTION,25))
        self.add_fit_button.SetFont(font2)
        self.Bind(wx.EVT_BUTTON, self.add_fit, self.add_fit_button)

        fit_window = wx.GridSizer(2, 1, 10*self.GUI_RESOLUTION, 19*self.GUI_RESOLUTION)
        fit_window.AddMany( [(self.add_fit_button, wx.ALIGN_LEFT),
            (self.fit_box, wx.ALIGN_LEFT)])
        self.box_sizer_fit.Add(fit_window, 0, wx.TOP, 5.5 )

 #----------------------------------------------------------------------
        #  select bounds box
 #----------------------------------------------------------------------

        self.T_list=[]

        self.box_sizer_select_bounds = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY,"bounds" ), wx.VERTICAL )
        self.tmin_box = wx.ComboBox(self.panel, -1 ,size=(100*self.GUI_RESOLUTION, 25),choices=self.T_list, style=wx.CB_DROPDOWN)
        self.Bind(wx.EVT_COMBOBOX, self.get_new_PCA_parameters,self.tmin_box)

        self.tmax_box = wx.ComboBox(self.panel, -1 ,size=(100*self.GUI_RESOLUTION, 25),choices=self.T_list, style=wx.CB_DROPDOWN)
        self.Bind(wx.EVT_COMBOBOX, self.get_new_PCA_parameters,self.tmax_box)

        select_temp_window = wx.GridSizer(2, 1, 10*self.GUI_RESOLUTION, 0)
        select_temp_window.AddMany( [(self.tmin_box, wx.ALIGN_LEFT),
            (self.tmax_box, wx.ALIGN_LEFT)])
        self.box_sizer_select_bounds.Add(select_temp_window, 0, wx.ALIGN_LEFT, 3.5 )

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
        self.Bind(wx.EVT_BUTTON, self.delete_fit, self.delete_interpretation_button)

        save_delete_window = wx.GridSizer(2, 1, 10*self.GUI_RESOLUTION, 19*self.GUI_RESOLUTION)
        save_delete_window.AddMany( [(self.save_interpretation_button, wx.ALIGN_LEFT),
            (self.delete_interpretation_button, wx.ALIGN_LEFT)])
        self.box_sizer_save.Add(save_delete_window, 0, wx.TOP, 5.5 )

 #----------------------------------------------------------------------
        # Specimen interpretation window
 #----------------------------------------------------------------------

        self.box_sizer_specimen = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY,"specimen mean type"  ), wx.HORIZONTAL )

        self.PCA_type_box = wx.ComboBox(self.panel, -1, size=(100*self.GUI_RESOLUTION, 25), value='line',choices=['line','line-anchored','line-with-origin','plane','Fisher'], style=wx.CB_DROPDOWN,name="coordinates")
        self.Bind(wx.EVT_COMBOBOX, self.on_select_specimen_mean_type_box,self.PCA_type_box)

        #Plane displays box
#        self.plane_display_sizer = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY,"plane display type"  ), wx.HORIZONTAL )

        self.plane_display_box = wx.ComboBox(self.panel, -1, size=(100*self.GUI_RESOLUTION, 25), value='show whole plane',choices=['show whole plane','show u. hemisphere', 'show l. hemisphere','show poles'], style=wx.CB_DROPDOWN,name="PlaneType")
        self.Bind(wx.EVT_COMBOBOX, self.on_select_plane_display_box, self.plane_display_box)

        specimen_stat_type_window = wx.GridSizer(2, 1, 10*self.GUI_RESOLUTION, 19*self.GUI_RESOLUTION)
        specimen_stat_type_window.AddMany([(self.PCA_type_box, wx.ALIGN_LEFT),
                                           (self.plane_display_box, wx.ALIGN_LEFT)])
        self.box_sizer_specimen.Add(specimen_stat_type_window, 0, wx.ALIGN_LEFT, 0 )

        self.box_sizer_specimen_stat = wx.StaticBoxSizer(wx.StaticBox(self.panel, wx.ID_ANY,"specimen fit statistics"), wx.HORIZONTAL )

        for parameter in ['dec','inc','n','mad','dang','alpha95']:
            COMMAND="self.s%s_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50*self.GUI_RESOLUTION,25))"%parameter
            exec COMMAND
            COMMAND="self.s%s_window.SetBackgroundColour(wx.WHITE)"%parameter
            exec COMMAND
            COMMAND="self.s%s_window.SetFont(font2)"%parameter
            exec COMMAND

        specimen_stat_window = wx.GridSizer(2, 6, 0, 15*self.GUI_RESOLUTION)
        specimen_stat_window.AddMany( [(wx.StaticText(self.panel,label="\ndec",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(self.panel,label="\ninc",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(self.panel,label="\nn",style=wx.TE_CENTER),wx.EXPAND),
            (wx.StaticText(self.panel,label="\nmad",style=wx.TE_CENTER),wx.EXPAND),
            #(wx.StaticText(self.panel,label="\nmad-anc",style=wx.TE_CENTER),wx.EXPAND),
            (wx.StaticText(self.panel,label="\ndang",style=wx.TE_CENTER),wx.TE_CENTER),
            (wx.StaticText(self.panel,label="\na95",style=wx.TE_CENTER),wx.TE_CENTER),
            (self.sdec_window, wx.EXPAND),
            (self.sinc_window, wx.EXPAND) ,
            (self.sn_window, wx.EXPAND) ,
            (self.smad_window, wx.EXPAND),
            #(self.mad_anc_window, wx.EXPAND),
            (self.sdang_window, wx.EXPAND),
            (self.salpha95_window, wx.EXPAND)])
        self.box_sizer_specimen_stat.Add( specimen_stat_window, 0, wx.ALIGN_LEFT, 0)

#----------------------------------------------------------------------
# High level mean window
 #----------------------------------------------------------------------

        self.box_sizer_high_level = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY,"higher level mean"  ), wx.HORIZONTAL )

        self.level_box = wx.ComboBox(self.panel, -1, size=(100*self.GUI_RESOLUTION, 25),value='site',  choices=['sample','site','location','study'], style=wx.CB_DROPDOWN,name="high_level")
        self.Bind(wx.EVT_COMBOBOX, self.onSelect_higher_level,self.level_box)

        self.level_names = wx.ComboBox(self.panel, -1,size=(100*self.GUI_RESOLUTION, 25), value=self.site,choices=self.sites, style=wx.CB_DROPDOWN,name="high_level_names")
        self.Bind(wx.EVT_COMBOBOX, self.onSelect_level_name,self.level_names)

        high_level_window = wx.GridSizer(2, 1, 10*self.GUI_RESOLUTION, 19*self.GUI_RESOLUTION)
        high_level_window.AddMany( [(self.level_box, wx.ALIGN_LEFT),
            (self.level_names, wx.ALIGN_LEFT)])
        self.box_sizer_high_level.Add( high_level_window, 0, wx.TOP, 5.5 )

#----------------------------------------------------------------------
# mean types box
 #----------------------------------------------------------------------

        self.box_sizer_mean_types = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "mean options" ), wx.VERTICAL )

        self.mean_type_box = wx.ComboBox(self.panel, -1, size=(120*self.GUI_RESOLUTION, 25), value='None', choices=['Fisher','Fisher by polarity','None'], style=wx.CB_DROPDOWN,name="high_type")
        self.Bind(wx.EVT_COMBOBOX, self.onSelect_mean_type_box,self.mean_type_box)

        self.mean_fit_box = wx.ComboBox(self.panel, -1, size=(120*self.GUI_RESOLUTION, 25), value='None', choices=['All'] + list_fits, style=wx.CB_DROPDOWN,name="high_type")
        self.Bind(wx.EVT_COMBOBOX, self.onSelect_mean_fit_box,self.mean_fit_box)
        self.mean_fit = 'None'

        mean_types_window = wx.GridSizer(2, 1, 10*self.GUI_RESOLUTION, 19*self.GUI_RESOLUTION)
        mean_types_window.AddMany([(self.mean_type_box,wx.ALIGN_LEFT),
            (self.mean_fit_box,wx.ALIGN_LEFT)])
        self.box_sizer_mean_types.Add(mean_types_window, 0, wx.TOP, 5.5 )

 #----------------------------------------------------------------------
# High level text box
 #----------------------------------------------------------------------
        self.stats_sizer = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY,"mean statistics"  ), wx.VERTICAL)

        for parameter in ['mean_type','dec','inc','alpha95','K','R','n_lines','n_planes']:
            COMMAND="self.%s_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(75*self.GUI_RESOLUTION,35))"%parameter
            exec COMMAND
            COMMAND="self.%s_window.SetBackgroundColour(wx.WHITE)"%parameter
            exec COMMAND
            COMMAND="self.%s_window.SetFont(font2)"%parameter
            exec COMMAND
            COMMAND="self.%s_outer_window = wx.GridSizer(1,2,5*self.GUI_RESOLUTION,15*self.GUI_RESOLUTION)"%parameter
            exec COMMAND
            COMMAND="""self.%s_outer_window.AddMany([
                    (wx.StaticText(self.panel,label='%s',style=wx.TE_CENTER),wx.EXPAND),
                    (self.%s_window, wx.EXPAND)])"""%(parameter,parameter,parameter)
            exec COMMAND
            COMMAND="self.stats_sizer.Add(self.%s_outer_window, 0, wx.ALIGN_LEFT, 0)"%parameter
            exec COMMAND

        self.switch_stats_button = wx.SpinButton(self.panel, id=wx.ID_ANY, style=wx.SP_HORIZONTAL|wx.SP_ARROW_KEYS|wx.SP_WRAP, name="change stats")
        self.Bind(wx.EVT_SPIN, self.on_select_stats_button,self.switch_stats_button)

#        self.box_sizer_high_level_text = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY,""  ), wx.HORIZONTAL )
#        self.high_level_text_box = wx.TextCtrl(self.panel, id=-1, size=(220*self.GUI_RESOLUTION,210*self.GUI_RESOLUTION), style=wx.TE_MULTILINE | wx.TE_READONLY )
#        self.high_level_text_box.SetFont(font1)
#        self.box_sizer_high_level_text.Add(self.high_level_text_box, 0, wx.ALIGN_LEFT, 0 )

 #----------------------------------------------------------------------
# Design the panel
#----------------------------------------------------------------------

        vbox1 = wx.BoxSizer(wx.VERTICAL)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        vbox1.AddSpacer(10)

        hbox1.AddSpacer(2)
        hbox1.Add(self.box_sizer_select_bounds,flag=wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
        hbox1.AddSpacer(2)
        hbox1.Add(self.box_sizer_fit,flag=wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
        hbox1.AddSpacer(2)
        hbox1.Add(self.box_sizer_save,flag=wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
        hbox1.AddSpacer(2)
        hbox1.Add(self.box_sizer_specimen, flag=wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
        hbox1.AddSpacer(2)
        hbox1.Add(self.box_sizer_specimen_stat, flag=wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
        hbox1.AddSpacer(2)
        hbox1.Add(self.box_sizer_high_level, flag=wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
        hbox1.Add(self.box_sizer_mean_types, flag=wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)

        vbox2a=wx.BoxSizer(wx.VERTICAL)
        vbox2a.Add(self.box_sizer_select_specimen,flag=wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND,border=8)
        vbox2a.Add(self.logger,flag=wx.ALIGN_TOP,border=8)
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2.AddSpacer(2)
        hbox2.Add(vbox2a,flag=wx.ALIGN_CENTER_HORIZONTAL)
        hbox2.Add(self.canvas1,flag=wx.ALIGN_CENTER_HORIZONTAL,border=8)

        vbox2 = wx.BoxSizer(wx.VERTICAL)
        vbox2.Add(self.canvas2,flag=wx.ALIGN_LEFT,border=8)
        vbox2.Add(self.canvas3,flag=wx.ALIGN_LEFT,border=8)

        vbox3 = wx.BoxSizer(wx.VERTICAL)
        vbox3.Add(self.canvas4,flag=wx.ALIGN_LEFT|wx.ALIGN_TOP,border=8)

        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        hbox3.Add(self.stats_sizer,flag=wx.ALIGN_CENTER_VERTICAL,border=8)
        hbox3.Add(self.switch_stats_button,flag=wx.ALIGN_CENTER_VERTICAL,border=8)

        vbox3.Add(hbox3,flag=wx.ALIGN_CENTER_VERTICAL,border=8)

        hbox2.Add(vbox2,flag=wx.ALIGN_CENTER_HORIZONTAL)
        hbox2.Add(vbox3,flag=wx.ALIGN_CENTER_HORIZONTAL)

        vbox1.Add(hbox1, flag=wx.ALIGN_LEFT)
        vbox1.Add(hbox2, flag=wx.LEFT)

        self.panel.SetSizer(vbox1)
        vbox1.Fit(self)

        self.GUI_SIZE = self.GetSize()

        # get previous interpretations from pmag tables
        # Draw figures and add text
        if self.Data:
            self.update_pmag_tables()
            if not self.current_fit:
                self.update_selection()
            else:
                self.Add_text()
                self.update_fit_boxs()
        else:
            print("------------------------------ no magic_measurements.txt found---------------------------------------")
            self.Destroy()

    #----------------------------------------------------------------------
    # Arrow keys control
    #----------------------------------------------------------------------

    def arrow_keys(self):
        self.panel.Bind(wx.EVT_CHAR, self.onCharEvent)

    def onCharEvent(self, event):
        keycode = event.GetKeyCode()
        #controlDown = event.CmdDown()
        #altDown = event.AltDown()
        #shiftDown = event.ShiftDown()

        if keycode == wx.WXK_RIGHT or keycode == wx.WXK_NUMPAD_RIGHT or keycode == wx.WXK_WINDOWS_RIGHT:
            #print "you pressed the right!"
            self.on_next_button(None)
        elif keycode == wx.WXK_LEFT or keycode == wx.WXK_NUMPAD_LEFT or keycode == wx.WXK_WINDOWS_LEFT:
            #print "you pressed the right!"
            self.on_prev_button(None)
        event.Skip()

    #----------------------------------------------------------------------
    # Plot Events
    #----------------------------------------------------------------------

    def right_click_zijderveld(self,event):
        """
        toggles between zoom and pan effects for the zijderveld on right click
        @param: event -> the wx.MouseEvent that triggered the call of this function
        @alters: zijderveld_setting, toolbar1 setting
        """
        if event.LeftIsDown() or event.ButtonDClick():
            return
        elif self.zijderveld_setting == "Zoom":
            self.zijderveld_setting = "Pan"
            try: self.toolbar1.pan('off')
            except TypeError: pass
        elif self.zijderveld_setting == "Pan":
            self.zijderveld_setting = "Zoom"
            try: self.toolbar1.zoom()
            except TypeError: pass

    def home_zijderveld(self,event):
        """
        homes zijderveld to original position
        @param: event -> the wx.MouseEvent that triggered the call of this function
        @alters: toolbar1 setting
        """
        try: self.toolbar1.home()
        except TypeError: pass

    def pick_bounds(self,event):
        """
        (unsupported)
        attempt at a functionality to pick bounds by clicking on the zijderveld
        @param: event -> the wx.MouseEvent that triggered the call of this function
        @alters: ...
        """
        pos=event.GetPosition()
        e = 1e-2
        l = len(self.CART_rot_good[:,0])
        def distance(p1,p2):
            return sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)
        points = []
        inv = self.zijplot.transData.inverted()
        reverse = inv.transform(numpy.vstack([pos[0],pos[1]]).T)
        xpick_data,ypick_data = reverse.T
        pos = (xpick_data,ypick_data)
        for data in [self.zij_xy_points,self.zij_xz_points]:
            x, y = data.get_data()
#            xy_pixels = self.zijplot.transData.transform(numpy.vstack([x,y]).T)
#            xpix, ypix = xy_pixels.T
#            width, height = self.canvas1.get_width_height()
#            y_pix = height - ypix
            points += [(x[i],y[i]) for i in range(len(x))]
        index = None
#        reverse = inv.transform(numpy.vstack([xpix,ypix]).T)
#        xprime, yprime = reverse.T
#        self.zijplot.plot(xprime,yprime,'k*-',mfc=self.dec_MFC,mec=self.dec_MEC,markersize=self.MS,clip_on=False,picker=True)
        print("getting nearest step at: " + str(pos))
        print(points)
        for point in points:
#            print(map(int,point))
            if 0 <= distance(pos,point) <= e:
                index = points.index(point)%l
                step = self.Data[self.s]['zijdblock_steps'][index]
                print(step)
                break
        class Dumby_Event:
            def __init__(self,text):
                self.text = text
            def GetText(self):
                return self.text
        if index:
            dumby_event = Dumby_Event(index)
            self.OnClick_listctrl(dumby_event)
        self.zoom(event)

    def right_click_specimen_equalarea(self,event):
        """
        toggles between zoom and pan effects for the specimen equal area on right click
        @param: event -> the wx.MouseEvent that triggered the call of this function
        @alters: specimen_EA_setting, toolbar2 setting
        """
        if event.LeftIsDown() or event.ButtonDClick():
            return
#        elif self.specimen_EA_setting == "Zoom":
#            self.specimen_EA_setting = "Pan"
#            try: self.toolbar2.pan('off')
#            except TypeError: pass
#        elif self.specimen_EA_setting == "Pan":
#            self.specimen_EA_setting = "Zoom"
#            try: self.toolbar2.zoom()
#            except TypeError: pass

    def home_specimen_equalarea(self,event):
        """
        returns the equal specimen area plot to it's original position
        @param: event -> the wx.MouseEvent that triggered the call of this function
        @alters: toolbar2 setting
        """
        self.toolbar2.home()

    def on_change_specimen_mouse_cursor(self,event):
        """
        If mouse is over data point making it selectable change the shape of the cursor
        @param: event -> the wx Mouseevent for that click
        """
        if not self.specimen_EA_xdata or not self.specimen_EA_ydata: return
        pos=event.GetPosition()
        width, height = self.canvas2.get_width_height()
        pos[1] = height - pos[1]
#        inv = self.specimen_eqarea_interpretation.transData.inverted()
#        reverse = inv.transform(numpy.vstack([pos[0],pos[1]]).T)
#        xpick_data,ypick_data = map(float,reverse.T)
#        xdata = self.specimen_EA_xdata
#        ydata = self.specimen_EA_ydata
#        e = 5e-2
        xpick_data,ypick_data = pos
        xdata_org = self.specimen_EA_xdata
        ydata_org = self.specimen_EA_ydata
        data_corrected = self.specimen_eqarea_interpretation.transData.transform(numpy.vstack([xdata_org,ydata_org]).T)
        xdata,ydata = data_corrected.T
        xdata = map(float,xdata)
        ydata = map(float,ydata)
        e = 4e0

#        if event.LeftIsDown(): # and self.old_pos==None:
#            self.toolbar2.draw_rubberband(event)

        if self.specimen_EA_setting == "Zoom":
            self.canvas2.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))
        elif self.specimen_EA_setting == "Pan":
            self.canvas2.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
        else:
            self.canvas2.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
        for i,(x,y) in enumerate(zip(xdata,ydata)):
            if 0 < numpy.sqrt((x-xpick_data)**2. + (y-ypick_data)**2.) < e:
                self.canvas2.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
                break

    def on_equalarea_specimen_select(self,event):
        """
        Get mouse position on double click find the nearest interpretation to the mouse
        position then select that interpretation
        @param: event -> the wx Mouseevent for that click
        @alters: current_fit
        """
        if not self.specimen_EA_xdata or not self.specimen_EA_ydata: return
        pos=event.GetPosition()
        width, height = self.canvas2.get_width_height()
        pos[1] = height - pos[1]
#        inv = self.specimen_eqarea_interpretation.transData.inverted()
#        reverse = inv.transform(numpy.vstack([pos[0],pos[1]]).T)
#        xpick_data,ypick_data = map(float,reverse.T)
#        xdata = self.specimen_EA_xdata
#        ydata = self.specimen_EA_ydata
#        e = 5e-2
        xpick_data,ypick_data = pos
        xdata_org = self.specimen_EA_xdata
        ydata_org = self.specimen_EA_ydata
        data_corrected = self.specimen_eqarea_interpretation.transData.transform(numpy.vstack([xdata_org,ydata_org]).T)
        xdata,ydata = data_corrected.T
        xdata = map(float,xdata)
        ydata = map(float,ydata)
        e = 4e0

        index = None
        for i,(x,y) in enumerate(zip(xdata,ydata)):
            if 0 < numpy.sqrt((x-xpick_data)**2. + (y-ypick_data)**2.) < e:
                index = i
                break
        if index != None:
            self.fit_box.SetSelection(index)
            self.on_select_fit(event)

    def right_click_higher_equalarea(self,event):
        """
        toggles between zoom and pan effects for the higher equal area on right click
        @param: event -> the wx.MouseEvent that triggered the call of this function
        @alters: higher_EA_setting, toolbar4 setting
        """
        if event.LeftIsDown():
            return
#        elif self.higher_EA_setting == "Zoom":
#            self.higher_EA_setting = "Pan"
#            try: self.toolbar4.pan('off')
#            except TypeError: pass
#        elif self.higher_EA_setting == "Pan":
#            self.higher_EA_setting = "Zoom"
#            try: self.toolbar4.zoom()
#            except TypeError: pass

    def home_higher_equalarea(self,event):
        """
        returns higher equal area to it's original position
        @param: event -> the wx.MouseEvent that triggered the call of this function
        @alters: toolbar4 setting
        """
        self.toolbar4.home()

    def on_change_higher_mouse_cursor(self,event):
        """
        If mouse is over data point making it selectable change the shape of the cursor
        @param: event -> the wx Mouseevent for that click
        """
        if self.interpretation_editor_open and self.interpretation_editor.show_box.GetValue() != "specimens": return
        pos=event.GetPosition()
        width, height = self.canvas4.get_width_height()
        pos[1] = height - pos[1]
#        inv = self.high_level_eqarea.transData.inverted()
#        reverse = inv.transform(numpy.vstack([pos[0],pos[1]]).T)
#        xpick_data,ypick_data = map(float,reverse.T)
#        xdata = self.higher_EA_xdata
#        ydata = self.higher_EA_ydata
        xpick_data,ypick_data = pos
        xdata_org = self.higher_EA_xdata
        ydata_org = self.higher_EA_ydata
        data_corrected = self.high_level_eqarea.transData.transform(numpy.vstack([xdata_org,ydata_org]).T)
        xdata,ydata = data_corrected.T
        xdata = map(float,xdata)
        ydata = map(float,ydata)
        e = 4e0

        #prelimenary rectangle drawing mechanism for the zoom feature (not currently opperational)
#        if event.LeftIsDown() and self.old_pos==None:
#            self.old_pos = event.GetPosition()
#            inv = self.high_level_eqarea.transData.inverted()
#            reverse = inv.transform(numpy.vstack([self.old_pos[0],self.old_pos[1]]).T)
#            self.old_pos = map(float,reverse.T)
#        elif not event.LeftIsDown() and self.old_pos!=None:
#            self.old_pos = None
#        if self.old_pos!=None:
#            mat_event = matplotlib.backend_bases.MouseEvent('motion_notify_event',self.canvas4,xpick_data,ypick_data,guiEvent=event)
#            self.toolbar4.draw_rubberband(mat_event, self.old_pos[0], self.old_pos[1], xpick_data, ypick_data)
#            self.canvas4.draw()
#            print("is doing stuff")
#            print(array(self.old_pos[0],self.old_pos[1]),array(self.old_pos[0],ydata))
#            self.high_level_eqarea.plot(ndarray(self.old_pos),ndarray(self.old_pos[0],ydata),'k-')
#            self.high_level_eqarea.plot(ndarray(self.old_pos),ndarray(xdata,self.old_pos[1]),'k-')
#            self.high_level_eqarea.plot(ndarray(xdata,self.old_pos[1]),ndarray(xdata,ydata),'k-')
#            self.high_level_eqarea.plot(ndarray(self.old_pos[0],ydata),ndarray(xdata,ydata),'k-')
#            self.canvas4.draw()

        if self.higher_EA_setting == "Zoom":
            self.canvas4.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))
        elif self.higher_EA_setting == "Pan":
            self.canvas4.SetCursor(wx.StockCursor(wx.CURSOR_WATCH))
        else:
            self.canvas4.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
        if not self.higher_EA_xdata or not self.higher_EA_ydata: return
        for i,(x,y) in enumerate(zip(xdata,ydata)):
            if 0 < numpy.sqrt((x-xpick_data)**2. + (y-ypick_data)**2.) < e:
                self.canvas4.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
                break

    def on_equalarea_higher_select(self,event):
        """
        Get mouse position on double click find the nearest interpretation to the mouse
        position then select that interpretation
        @param: event -> the wx Mouseevent for that click
        @alters: current_fit, s, mean_fit, fit_box selection, mean_fit_box selection, specimens_box selection, tmin_box selection, tmax_box selection,
        """
        if self.interpretation_editor_open and self.interpretation_editor.show_box.GetValue() != "specimens": return
        if not self.higher_EA_xdata or not self.higher_EA_ydata: return
        pos=event.GetPosition()
        width, height = self.canvas4.get_width_height()
        pos[1] = height - pos[1]
        xpick_data,ypick_data = pos
        xdata_org = self.higher_EA_xdata
        ydata_org = self.higher_EA_ydata
        data_corrected = self.high_level_eqarea.transData.transform(numpy.vstack([xdata_org,ydata_org]).T)
        xdata,ydata = data_corrected.T
        xdata = map(float,xdata)
        ydata = map(float,ydata)
        e = 4e0

        index = None
        for i,(x,y) in enumerate(zip(xdata,ydata)):
            if 0 < numpy.sqrt((x-xpick_data)**2. + (y-ypick_data)**2.) < e:
                index = i
                break
        if index != None:
            disp_fit_name = self.mean_fit_box.GetValue()

            if self.level_box.GetValue()=='sample': high_level_type='samples'
            if self.level_box.GetValue()=='site': high_level_type='sites'
            if self.level_box.GetValue()=='location': high_level_type='locations'
            if self.level_box.GetValue()=='study': high_level_type='study'

            high_level_name=str(self.level_names.GetValue())
            calculation_type=str(self.mean_type_box.GetValue())
            elements_type=self.UPPER_LEVEL_SHOW

            elements_list=self.Data_hierarchy[high_level_type][high_level_name][elements_type]

            new_fit_index=0
            for i,specimen in enumerate(elements_list):
                if disp_fit_name=="All" and \
                   specimen in self.pmag_results_data[elements_type]:
                    l = 0
                    for fit in self.pmag_results_data[elements_type][specimen]:
                        l += 1
#                        if fit in self.bad_fits:
#                            l -= 1
                else:
                    try:
                        disp_fit_index = map(lambda x: x.name, self.pmag_results_data[elements_type][specimen]).index(disp_fit_name)
                        if self.pmag_results_data[elements_type][specimen][disp_fit_index] in self.bad_fits:
                            l = 0
                        else:
                            l = 1
                    except IndexError: l = 0
                    except KeyError: l = 0
                    except ValueError: l = 0

                if index < l:
                    self.specimens_box.SetStringSelection(specimen)
                    self.select_specimen(specimen)
                    self.draw_figure(specimen, False)
                    if disp_fit_name == "All":
                        new_fit_index = index
                    else:
                        new_fit_index = disp_fit_index
                    break

                index -= l
            self.update_fit_box()
            self.fit_box.SetSelection(new_fit_index)
            self.on_select_fit(event)
            if disp_fit_name!="All":
                self.mean_fit = self.current_fit.name
                self.mean_fit_box.SetSelection(2+new_fit_index)
                self.update_selection()
            else:
                self.Add_text()
            if self.interpretation_editor_open:
                self.interpretation_editor.change_selected(self.current_fit)

    def Zij_zoom(self):
        #cursur_entry_zij=self.canvas1.mpl_connect('axes_enter_event', self.on_enter_zij_fig_new)
        cursur_entry_zij=self.canvas1.mpl_connect('axes_enter_event', self.on_enter_zij_fig)
        cursur_leave_zij=self.canvas1.mpl_connect('axes_leave_event', self.on_leave_zij_fig)

    def on_enter_zij_fig_new(self,event):
        #self.toolbar1.zoom()
        self.curser_in_zij_figure=True
        self.canvas2.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))
        cid3=self.canvas1.mpl_connect('button_press_event', self.onclick_z_11)
        cid4=self.canvas1.mpl_connect('button_release_event', self.onclick_z_22)


    def onclick_z_11(self,event):
        #if self.curser_in_zij_figure:
        self.tmp_x_press=event.xdata
        self.tmp_y_press=event.ydata

    def onclick_z_22(self,event):
        self.tmp_x_release=event.xdata
        self.tmp_y_release=event.ydata
        if abs(self.tmp_x_press-self.tmp_x_release)<0.05 and abs(self.tmp_y_press-self.tmp_y_release)<0.05:
                self.zijplot.set_xlim(xmin=self.zij_xlim_initial[0],xmax=self.zij_xlim_initial[1])
                self.zijplot.set_ylim(ymin=self.zij_ylim_initial[0],ymax=self.zij_ylim_initial[1])
                self.canvas1.draw()


    def on_leave_zij_fig (self,event):
        self.canvas1.mpl_disconnect(self.cid3)
        self.canvas1.mpl_disconnect(self.cid4)
        self.canvas1.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
        self.curser_in_zij_figure=False


    def on_enter_zij_fig(self,event):
        #AX=gca(label='zig_orig')
        #print AX
        self.fig1.sca(self.zijplot)
        self.curser_in_zij_figure=True
        self.canvas1.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))
        cid3=self.canvas1.mpl_connect('button_press_event', self.onclick_z_1)
        cid4=self.canvas1.mpl_connect('button_release_event', self.onclick_z_2)

    def onclick_z_1(self,event):
        if self.curser_in_zij_figure:
            self.tmp3_x=event.xdata
            self.tmp3_y=event.ydata

    def onclick_z_2(self,event):
        self.canvas1.mpl_connect('axes_leave_event', self.on_leave_zij_fig)
        if self.curser_in_zij_figure:
            self.tmp4_x=event.xdata
            self.tmp4_y=event.ydata
            try:
                delta_x=abs(self.tmp3_x - self.tmp4_x )
                delta_y=abs(self.tmp3_y - self.tmp4_y )
            except:
                return

            if self.tmp3_x < self.tmp4_x and self.tmp3_y > self.tmp4_y:
                self.zijplot.set_xlim(xmin=self.tmp3_x,xmax=self.tmp4_x)
                self.zijplot.set_ylim(ymin=self.tmp4_y,ymax=self.tmp3_y)
            else:
                self.zijplot.set_xlim(xmin=self.zij_xlim_initial[0],xmax=self.zij_xlim_initial[1])
                self.zijplot.set_ylim(ymin=self.zij_ylim_initial[0],ymax=self.zij_ylim_initial[1])

            self.canvas1.draw()
        else:
            return

    def right_click_MM0(self,event):
        if self.MM0_setting == "Zoom":
            self.MM0_setting = "Pan"
            self.toolbar3.pan()
        elif self.MM0_setting == "Pan":
            self.MM0_setting = "Zoom"
            self.toolbar3.zoom()

    def home_MM0(self,event):
        self.toolbar3.home()

    #----------------------------------------------------------------------
    # Picking bounds from Zijderveld plot
    #----------------------------------------------------------------------

    def Zij_picker(self):
       self.canvas1.mpl_connect('pick_event', self.onpick)
       #self.canvas1.mpl_connect('pick_event', self.onpick())

    def onpick(self,event):
        self.second_click=time.time()
        try:
            if self.second_click-self.first_click > 1:
                self.first_click=self.second_click
                return
        except:
            self.first_click= self.second_click
            return
#Blarge
        index = event.ind[0]

        # delete previose interpretation on screen
        for fit in self.pmag_results_data['specimens'][self.s]['fits']:
            for line in fit.lines:
                if line in self.zijplot.lines:
                    self.zijplot.lines.remove(line)

        # clear selection in measurement window
        for item in range(self.logger.GetItemCount()):
            self.logger.SetItemBackgroundColour(item,"WHITE")
            self.logger.Select(item, on=0)

        # clear equal area plot
        self.specimen_eqarea_interpretation.clear()   # equal area
        self.mplot_interpretation.clear() # M / M0

        tmin_index,tmax_index="",""
        if str(self.tmin_box.GetValue())!="":
            tmin_index=self.tmin_box.GetSelection()
        if str(self.tmax_box.GetValue())!="":
            tmax_index=self.tmax_box.GetSelection()


        # set slection in
        if tmin_index !="" and tmax_index =="":
            if index<tmin_index:
                self.tmin_box.SetSelection(index)
                self.tmax_box.SetSelection(tmin_index)
            else:
                self.tmax_box.SetSelection(index)
            self.logger.Select(index, on=0)
            self.get_new_PCA_parameters(-1)

        elif tmin_index =="" and tmax_index !="":
            if index>tmax_index:
                self.tmin_box.SetSelection(tmax_index)
                self.tmax_box.SetSelection(index)
            else:
                self.tmin_box.SetSelection(index)
            self.logger.Select(index, on=0)
            self.get_new_PCA_parameters(-1)
        else:
            if int(index) > (self.logger.GetItemCount())/2.:
                self.tmin_box.SetValue("")
                self.tmax_box.SetSelection(int(index))
            else:
                self.tmin_box.SetSelection(int(index))
                self.tmax_box.SetValue("")

            self.logger.Select(index, on=1)
            self.zijplot.scatter([self.CART_rot[:,0][index]],[-1* self.CART_rot[:,1][index]],marker='o',s=40,facecolor='g',edgecolor ='k',zorder=100,clip_on=False)
            self.zijplot.scatter([self.CART_rot[:,0][index]],[-1* self.CART_rot[:,2][index]],marker='s',s=50,facecolor='g',edgecolor ='k',zorder=100,clip_on=False)

            self.mplot_interpretation.scatter([self.Data[self.s]['zijdblock'][index][0]],[self.Data[self.s]['zijdblock'][index][3]/self.Data[self.s]['zijdblock'][0][3]],marker='o',s=30,facecolor='g',edgecolor ='k',zorder=100,clip_on=False)
        self.canvas1.draw()
        self.canvas2.draw()
        self.canvas3.draw()

    def initialize_CART_rot(self,s):

        #-----------------------------------------------------------
        #  initialization
        #-----------------------------------------------------------

        self.s = s

        if self.orthogonal_box.GetValue()=="X=East":
            self.ORTHO_PLOT_TYPE='E-W'
        elif self.orthogonal_box.GetValue()=="X=North":
            self.ORTHO_PLOT_TYPE='N-S'
        elif self.orthogonal_box.GetValue()=="X=best fit line dec":
            self.ORTHO_PLOT_TYPE='PCA_dec'
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
            elif self.ORTHO_PLOT_TYPE=='PCA_dec':
                if 'specimen_dec' in self.current_fit.pars.keys() and type(self.current_fit.pars['specimen_dec'])!=str:
                    self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata_geo'],self.current_fit.pars['specimen_dec'])
                else:
                    self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata_geo'],pmag.cart2dir(self.Data[self.s]['zdata_geo'][0])[0])
            else:
                self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata_geo'],pmag.cart2dir(self.Data[self.s]['zdata_geo'][0])[0])

        elif self.COORDINATE_SYSTEM=='tilt-corrected':
            if self.ORTHO_PLOT_TYPE=='N-S':
                self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata_tilt'],0.)
            elif self.ORTHO_PLOT_TYPE=='E-W':
                self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata_tilt'],90)
            elif self.ORTHO_PLOT_TYPE=='PCA_dec':
                if 'specimen_dec' in self.current_fit.pars.keys() and type(self.current_fit.pars['specimen_dec'])!=str:
                    self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata_tilt'],self.current_fit.pars['specimen_dec'])
                else:
                    self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata_tilt'],pmag.cart2dir(self.Data[self.s]['zdata_tilt'][0])[0])
            else:
                self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata_tilt'],pmag.cart2dir(self.Data[self.s]['zdata_tilt'][0])[0])
        else:
            if self.ORTHO_PLOT_TYPE=='N-S':
                self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata'],0.)
            elif self.ORTHO_PLOT_TYPE=='E-W':
                self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata'],90)
            elif self.ORTHO_PLOT_TYPE=='PCA_dec':
                if 'specimen_dec' in self.current_fit.pars.keys() and type(self.current_fit.pars['specimen_dec'])!=str:
                    self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata'],self.current_fit.pars['specimen_dec'])
                else:#Zijderveld
                    self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata'],pmag.cart2dir(self.Data[self.s]['zdata'][0])[0])

            else:#Zijderveld
                self.CART_rot=self.Rotate_zijderveld(self.Data[self.s]['zdata'],pmag.cart2dir(self.Data[self.s]['zdata'][0])[0])


        self.zij_norm=array([row/sqrt(sum(row**2)) for row in self.zij])

        #-----------------------------------------------------------
        # remove bad data from plotting:
        #-----------------------------------------------------------

        self.CART_rot_good=[]
        self.CART_rot_bad=[]
        for i in range(len(self.CART_rot)):
            if self.Data[self.s]['measurement_flag'][i]=='g':
                self.CART_rot_good.append(list(self.CART_rot[i]))
            else:
                self.CART_rot_bad.append(list(self.CART_rot[i]))

        self.CART_rot_good=array(self.CART_rot_good)
        self.CART_rot_bad=array(self.CART_rot_bad)

    #----------------------------------------------------------------------
    # Draw plots
    #----------------------------------------------------------------------

    def draw_figure(self,s,update_higher_plots=True):

        self.initialize_CART_rot(s)

        #-----------------------------------------------------------
        # Draw Zij plot
        #-----------------------------------------------------------
        self.fig1.clf()
        axis_bounds = [0,.1,1,.85]
        self.zijplot = self.fig1.add_axes(axis_bounds,frameon=False, axisbg='None',label='zig_orig',zorder=0)
        self.zijplot.clear()
        self.zijplot.axis('equal')
        self.zijplot.xaxis.set_visible(False)
        self.zijplot.yaxis.set_visible(False)
        #self.zijplot_interpretation = self.fig1.add_axes(self.zijplot.get_position(), frameon=False,axisbg='None',label='zij_interpretation',zorder=1)
        #self.zijplot_interpretation.clear()
        #self.zijplot_interpretation.axis('equal')
        #self.zijplot_interpretation.xaxis.set_visible(False)
        #self.zijplot_interpretation.yaxis.set_visible(False)

        self.MS=6*self.GUI_RESOLUTION;self.dec_MEC='k';self.dec_MFC='r'; self.inc_MEC='k';self.inc_MFC='b'
        self.zijdblock_steps=self.Data[self.s]['zijdblock_steps']
        self.vds=self.Data[self.s]['vds']

        #self.zijplot.scatter(self.CART_rot[:,0],-1* self.CART_rot[:,1],marker="o",s=self.MS,c='r',clip_on=False,picker=True)
        #self.zijplot.plot(self.CART_rot[:,0],-1* self.CART_rot[:,1],'ro-',mfc=self.dec_MFC,mec=self.dec_MEC,markersize=self.MS,clip_on=False,picker=True)  #x,y or N,E
        #self.zijplot.plot(self.CART_rot[:,0],-1 * self.CART_rot[:,2],'bs-',mfc=self.inc_MFC,mec=self.inc_MEC,markersize=self.MS,clip_on=False,picker=True)   #x-z or N,D
        #self.zijplot.plot(self.CART_rot_clean[:,0],-1* self.CART_rot_clean[:,1],'r-')  #x,y or N,E
        #self.zijplot.plot(self.CART_rot_clean[:,0],-1 * self.CART_rot_clean[:,2],'b-')   #x-z or N,D
        #self.zijplot.scatter(self.CART_rot[:,0],-1* self.CART_rot[:,1],marker="o",s=20,c='r',clip_on=False,picker=True)

        self.zij_xy_points, = self.zijplot.plot(self.CART_rot_good[:,0], -1*self.CART_rot_good[:,1], 'ro-', mfc=self.dec_MFC, mec=self.dec_MEC, markersize=self.MS, clip_on=False, picker=True) #x,y or N,E
        self.zij_xz_points, = self.zijplot.plot(self.CART_rot_good[:,0], -1*self.CART_rot_good[:,2], 'bs-', mfc=self.inc_MFC, mec=self.inc_MEC, markersize=self.MS, clip_on=False, picker=True) #x-z or N,D

        for i in range(len( self.CART_rot_bad)):
            self.zijplot.plot(self.CART_rot_bad[:,0][i],-1* self.CART_rot_bad[:,1][i],'o',mfc='None',mec=self.dec_MEC,markersize=self.MS,clip_on=False,picker=False) #x,y or N,E
            self.zijplot.plot(self.CART_rot_bad[:,0][i],-1 * self.CART_rot_bad[:,2][i],'s',mfc='None',mec=self.inc_MEC,markersize=self.MS,clip_on=False,picker=False) #x-z or N,D

        #self.zijplot.axis('off')
        #last_cart_1=array([self.CART_rot[0][0],self.CART_rot[0][1]])
        #last_cart_2=array([self.CART_rot[0][0],self.CART_rot[0][2]])
        #K_diff=0
        if self.preferences['show_Zij_treatments'] :
            for i in range(len(self.zijdblock_steps)):
                if int(self.preferences['show_Zij_treatments_steps']) !=1:
                    if i!=0  and (i+1)%int(self.preferences['show_Zij_treatments_steps'])==0:
                        self.zijplot.text(self.CART_rot[i][0], -1*self.CART_rot[i][2], "  %s"%(self.zijdblock_steps[i]), fontsize=8*self.GUI_RESOLUTION, color='gray', ha='left', va='center')   #inc
                else:
                  self.zijplot.text(self.CART_rot[i][0], -1*self.CART_rot[i][2], "  %s"%(self.zijdblock_steps[i]), fontsize=10*self.GUI_RESOLUTION, color='gray', ha='left', va='center')   #inc

        #-----

        xmin, xmax = self.zijplot.get_xlim()
        if xmax < 0:
            xmax=0
        if xmin > 0:
            xmin=0
        #else:
        #    xmin=xmin+xmin%0.2

        props = dict(color='black', linewidth=1.0, markeredgewidth=0.5)

        xlocs=array(list(arange(0.2,xmax,0.2)) + list(arange(-0.2,xmin,-0.2)))
        if len(xlocs)>0:
            xtickline, = self.zijplot.plot(xlocs, [0]*len(xlocs),linestyle='',marker='+', **props)
            xtickline.set_clip_on(False)

        axxline, = self.zijplot.plot([xmin, xmax], [0, 0], **props)
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



        #-----

        ymin, ymax = self.zijplot.get_ylim()
        if ymax < 0:
            ymax=0
        if ymin > 0:
            ymin=0

        ylocs=array(list(arange(0.2,ymax,0.2)) + list(arange(-0.2,ymin,-0.2)))
        if len(ylocs)>0:
            ytickline, = self.zijplot.plot([0]*len(ylocs),ylocs, linestyle='',marker='+', **props)
            ytickline.set_clip_on(False)

        axyline, = self.zijplot.plot([0, 0],[ymin, ymax], **props)
        axyline.set_clip_on(False)

        TEXT1,TEXT2="",""
        if self.COORDINATE_SYSTEM=='specimen':
                TEXT1,TEXT2=" y","      z"
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

        if self.ORTHO_PLOT_TYPE=='N-S':
            STRING=""
            #STRING1="N-S orthogonal plot"
            self.fig1.text(0.01,0.98,"Zijderveld plot: x = North",{'family':'Arial', 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })
        elif self.ORTHO_PLOT_TYPE=='E-W':
            STRING=""
            #STRING1="E-W orthogonal plot"
            self.fig1.text(0.01,0.98,"Zijderveld plot:: x = East",{'family':'Arial', 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })

        elif self.ORTHO_PLOT_TYPE=='PCA_dec':
            self.fig1.text(0.01,0.98,"Zijderveld plot",{'family':'Arial', 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })
            if 'specimen_dec' in self.current_fit.pars.keys() and type(self.current_fit.pars['specimen_dec'])!=str:
                STRING="X-axis rotated to best fit line declination (%.0f); "%(self.current_fit.pars['specimen_dec'])
            else:
                STRING="X-axis rotated to NRM (%.0f); "%(self.zijblock[0][1])
        else:
            self.fig1.text(0.01,0.98,"Zijderveld plot",{'family':'Arial', 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })
            STRING="X-axis rotated to NRM (%.0f); "%(self.zijblock[0][1])
            #STRING1="Zijderveld plot"


        STRING=STRING+"NRM=%.2e "%(self.zijblock[0][3])+ 'Am^2'
        self.fig1.text(0.01,0.95,STRING, {'family':'Arial', 'fontsize':8*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })

        xmin, xmax = self.zijplot.get_xlim()
        ymin, ymax = self.zijplot.get_ylim()

        self.zij_xlim_initial=(xmin, xmax)
        self.zij_ylim_initial=(ymin, ymax)

        self.canvas1.draw()

        #-----------------------------------------------------------
        # specimen equal area
        #-----------------------------------------------------------

        self.specimen_eqarea.clear()
        self.specimen_eqarea_interpretation.clear()
        self.specimen_eqarea.text(-1.2,1.15,"specimen: %s"%self.s,{'family':'Arial', 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })

        x_eq=array([row[0] for row in self.zij_norm])
        y_eq=array([row[1] for row in self.zij_norm])
        z_eq=abs(array([row[2] for row in self.zij_norm]))

        # remove bad data from plotting:
        x_eq_good,y_eq_good,z_eq_good=[],[],[]
        x_eq_bad,y_eq_bad,z_eq_bad=[],[],[]
        for i in range(len(list(self.zij_norm))):
            if self.Data[self.s]['measurement_flag'][i]=='g':
                x_eq_good.append(self.zij_norm[i][0])
                y_eq_good.append(self.zij_norm[i][1])
                z_eq_good.append(abs(self.zij_norm[i][2]))
            else:
                x_eq_bad.append(self.zij_norm[i][0])
                y_eq_bad.append(self.zij_norm[i][1])
                z_eq_bad.append(abs(self.zij_norm[i][2]))

        x_eq_good,y_eq_good,z_eq_good=array(x_eq_good),array(y_eq_good),array(z_eq_good)
        x_eq_bad,y_eq_bad,z_eq_bad=array(x_eq_bad),array(y_eq_bad),array(z_eq_bad)

        R_good=array(sqrt(1-z_eq_good)/sqrt(x_eq_good**2+y_eq_good**2)) # from Collinson 1983
        R_bad=array(sqrt(1-z_eq_bad)/sqrt(x_eq_bad**2+y_eq_bad**2)) # from Collinson 1983

        eqarea_data_x_good=y_eq_good*R_good
        eqarea_data_y_good=x_eq_good*R_good

        eqarea_data_x_bad=y_eq_bad*R_bad
        eqarea_data_y_bad=x_eq_bad*R_bad

        self.specimen_eqarea.plot(eqarea_data_x_good,eqarea_data_y_good,lw=0.5,color='gray')#,zorder=0)

        #--------------------
        # scatter plot
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
                self.specimen_eqarea.text(eqarea_data_x[i],eqarea_data_y[i],"%.1f"%float(self.zijdblock_steps[i]),fontsize=8*self.GUI_RESOLUTION,color="0.5")

        # add line to show the direction of the x axis in the Zijderveld plot

        if str(self.orthogonal_box.GetValue()) in ["X=best fit line dec","X=NRM dec"]:
            XY=[]
            if str(self.orthogonal_box.GetValue())=="X=NRM dec":
                dec_zij=self.zijblock[0][1]
                XY=pmag.dimap(dec_zij,0)
            if str(self.orthogonal_box.GetValue())=="X=best fit line dec":
                if 'specimen_dec' in self.current_fit.pars.keys() and  type(self.current_fit.pars['specimen_dec'])!=str:
                    dec_zij=self.current_fit.pars['specimen_dec']
                    XY=pmag.dimap(dec_zij,0)
            if XY!=[]:
                self.specimen_eqarea.plot([0,XY[0]],[0,XY[1]],ls='-',c='gray',lw=0.5)#,zorder=0)

        self.specimen_eqarea.set_xlim(-1., 1.)
        self.specimen_eqarea.set_ylim(-1., 1.)
        self.specimen_eqarea.axes.set_aspect('equal')
        self.specimen_eqarea.axis('off')

        self.specimen_eqarea_interpretation.set_xlim(-1., 1.)
        self.specimen_eqarea_interpretation.set_ylim(-1., 1.)
        self.specimen_eqarea_interpretation.axes.set_aspect('equal')
        self.specimen_eqarea_interpretation.axis('off')

        self.canvas2.draw()

        #start_time_2=time.time()
        #runtime_sec2 = start_time_2 - start_time_1
        #print "-I- draw eqarea figures is", runtime_sec2,"seconds"

        #-----------------------------------------------------------
        # Draw M/M0 plot ( or NLT data on the same area in the GUI)
        #-----------------------------------------------------------

        self.fig3.clf()
        self.fig3.text(0.02,0.96,'M/M0',{'family':'Arial', 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })
        self.mplot = self.fig3.add_axes([0.2,0.15,0.7,0.7],frameon=True,axisbg='None')
        self.mplot_interpretation = self.fig3.add_axes(self.mplot.get_position(), frameon=False,axisbg='None')
        self.mplot_interpretation.xaxis.set_visible(False)
        self.mplot_interpretation.yaxis.set_visible(False)

        #fig, ax1 = plt.subplots()
        #print "measurement_step_unit",self.Data[self.s]['measurement_step_unit']
        if self.Data[self.s]['measurement_step_unit'] =="mT:C" or self.Data[self.s]['measurement_step_unit'] =="C:mT":
            thermal_x,thermal_y=[],[]
            thermal_x_bad,thermal_y_bad=[],[]
            af_x,af_y=[],[]
            af_x_bad,af_y_bad=[],[]
            for i in range(len(self.Data[self.s]['zijdblock'])):
                # bad point
                if self.Data[self.s]['measurement_flag'][i]=='b':

                    if step=="0":
                        thermal_x_bad.append(self.Data[self.s]['zijdblock'][i][0])
                        af_x_bad.append(self.Data[self.s]['zijdblock'][i][0])
                        thermal_y_bad.append(self.Data[self.s]['zijdblock'][i][3]/self.Data[self.s]['zijdblock'][0][3])
                        af_y_bad.append(self.Data[self.s]['zijdblock'][i][3]/self.Data[self.s]['zijdblock'][0][3])
                    elif "C" in step:
                        thermal_x_bad.append(self.Data[self.s]['zijdblock'][i][0])
                        thermal_y_bad.append(self.Data[self.s]['zijdblock'][i][3]/self.Data[self.s]['zijdblock'][0][3])
                    elif "T" in step:
                        af_x_bad.append(self.Data[self.s]['zijdblock'][i][0])
                        af_y_bad.append(self.Data[self.s]['zijdblock'][i][3]/self.Data[self.s]['zijdblock'][0][3])
                    else:
                        continue

                else:
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
            for i in range(len(thermal_x_bad)):
                self.mplot.plot([thermal_x_bad[i]], [thermal_y_bad[i]],'o',mfc='None',mec='k',markersize=self.MS,clip_on=False)

            self.mplot.set_xlabel('Thermal (C)',color='r')
            for tl in self.mplot.get_xticklabels():
                tl.set_color('r')

            ax2 = self.mplot.twiny()
            ax2.plot(af_x, af_y, 'bo-',markersize=5*self.GUI_RESOLUTION,lw=1,clip_on=False)
            for i in range(len(af_x_bad)):
                ax2.plot([af_x_bad[i]], [af_y_bad[i]],'o',mfc='None',mec='k',markersize=self.MS,clip_on=False)

            ax2.set_xlabel('AF (mT)',color='b')
            for tl in ax2.get_xticklabels():
                tl.set_color('b')

            self.mplot.tick_params(axis='both', which='major', labelsize=7)
            ax2.tick_params(axis='both', which='major', labelsize=7)
            self.mplot.spines["right"].set_visible(False)
            ax2.spines["right"].set_visible(False)
            self.mplot.get_xaxis().tick_bottom()
            self.mplot.get_yaxis().tick_left()
            self.mplot.set_ylabel("M / NRM0",fontsize=8*self.GUI_RESOLUTION)

        else:
            self.mplot.clear()
            x_data,y_data=[],[]
            x_data_bad,y_data_bad=[],[]
            for i in range(len(self.Data[self.s]['zijdblock'])):
                # bad point
                if self.Data[self.s]['measurement_flag'][i]=='b':
                    x_data_bad.append(self.Data[self.s]['zijdblock'][i][0])
                    y_data_bad.append(self.Data[self.s]['zijdblock'][i][3]/self.Data[self.s]['zijdblock'][0][3])
                else:
                    x_data.append(self.Data[self.s]['zijdblock'][i][0])
                    y_data.append(self.Data[self.s]['zijdblock'][i][3]/self.Data[self.s]['zijdblock'][0][3])

            self.mplot = self.fig3.add_axes([0.2,0.15,0.7,0.7],frameon=True,axisbg='None')
            self.mplot.clear()
            self.mplot.plot(x_data,y_data,'bo-',mec='0.2',markersize=5*self.GUI_RESOLUTION,lw=1,clip_on=False)
            for i in range(len(x_data_bad)):
                self.mplot.plot([x_data_bad[i]], [y_data_bad[i]],'o',mfc='None',mec='k',markersize=self.MS,clip_on=False)
            self.mplot.set_xlabel("Treatment",fontsize=8*self.GUI_RESOLUTION)
            self.mplot.set_ylabel("M / NRM_0",fontsize=8*self.GUI_RESOLUTION)
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
        #start_time_3=time.time()
        #runtime_sec3 = start_time_3 - start_time_2
        #print "-I- draw M_M0 figures is", runtime_sec3,"seconds"

        #-----------------------------------------------------------
        # high level equal area
        #-----------------------------------------------------------
        if update_higher_plots:
            self.plot_higher_levels_data()
        #self.fig4.clf()
        #what_is_it=self.level_box.GetValue()
        #self.fig4.text(0.02,0.96,what_is_it,{'family':'Arial', 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })
        #self.high_level_eqarea = self.fig4.add_subplot(111)
        ## draw_net
        #self.draw_net(self.high_level_eqarea)
        #self.canvas4.draw()

        self.canvas4.draw()
        #start_time_4=time.time()
        #runtime_sec4 = start_time_4 - start_time_3
        #print "-I- draw high level figures is", runtime_sec4,"seconds"

    def draw_net_new(self,ax):
        FIG.clear()
        eq=FIG
        host = fig.add_subplot(111)
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
        eq.axes.set_aspect('equal')


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
        eq.axes.set_aspect('equal')

    #----------------------------------------------------------------------
    # add text to text box
    #----------------------------------------------------------------------

    def Add_text(self):
      """
      Add measurement data lines to the text window.
      """

      if self.COORDINATE_SYSTEM=='geographic':
          zijdblock=self.Data[self.s]['zijdblock_geo']
      elif self.COORDINATE_SYSTEM=='tilt-corrected':
          zijdblock=self.Data[self.s]['zijdblock_tilt']
      else:
          zijdblock=self.Data[self.s]['zijdblock']

      tmin_index,tmax_index = -1,-1
      if self.current_fit and self.current_fit.tmin and self.current_fit.tmax:
        tmin_index,tmax_index = self.get_temp_indecies(self.current_fit)

      TEXT=""
      self.logger.DeleteAllItems()
      for i in range(len(zijdblock)):
          lab_treatment=self.Data[self.s]['zijdblock_lab_treatments'][i]
          Step=""
          methods=lab_treatment.split('-')
          if "NO" in methods:
              Step="N"
          elif "AF" in  methods:
              Step="AF"
          elif "T" in  methods or "LT" in methods:
              Step="T"
          Tr=zijdblock[i][0]
          Dec=zijdblock[i][1]
          Inc=zijdblock[i][2]
          Int=zijdblock[i][3]
          self.logger.InsertStringItem(i, "%i"%i)
          self.logger.SetStringItem(i, 1, Step)
          self.logger.SetStringItem(i, 2, "%.1f"%Tr)
          self.logger.SetStringItem(i, 3, "%.1f"%Dec)
          self.logger.SetStringItem(i, 4, "%.1f"%Inc)
          self.logger.SetStringItem(i, 5, "%.2e"%Int)
          self.logger.SetItemBackgroundColour(i,"WHITE")
          if i >= tmin_index and i <= tmax_index:
            self.logger.SetItemBackgroundColour(i,"LIGHT BLUE")
          if self.Data[self.s]['measurement_flag'][i]=='b':
            self.logger.SetItemBackgroundColour(i,"YELLOW")

    #----------------------------------------------------------------------

    def onSelect_specimen(self, event):
        """
        update figures and text when a new specimen is selected
        """
        self.select_specimen(str(self.specimens_box.GetValue()))
        if self.interpretation_editor_open:
            self.interpretation_editor.change_selected(self.current_fit)
        self.update_selection()

    def select_specimen(self, specimen):
        try: fit_index = self.pmag_results_data['specimens'][self.s].index(self.current_fit)
        except KeyError: fit_index = None
        except ValueError: fit_index = None
        self.initialize_CART_rot(specimen) #sets self.s to specimen calculates params etc.
        if fit_index != None and self.s in self.pmag_results_data['specimens']:
          try: self.current_fit = self.pmag_results_data['specimens'][self.s][fit_index]
          except IndexError: self.current_fit = None
        else: self.current_fit = None

    #----------------------------------------------------------------------

    def onSelect_coordinates(self, event):
        old=self.COORDINATE_SYSTEM
        new=self.coordinates_box.GetValue()
        if new=='geographic' and len(self.Data[self.s]['zijdblock_geo'])==0:
            self.coordinates_box.SetStringSelection(old)
            print("-E- ERROR: could not switch to geographic coordinates reverting back to " + old + " coordinates")
        elif new=='tilt-corrected' and len(self.Data[self.s]['zijdblock_tilt'])==0:
            self.coordinates_box.SetStringSelection(old)
            print("-E- ERROR: could not switch to tilt-corrected coordinates reverting back to " + old + " coordinates")
        else:
            self.COORDINATE_SYSTEM=new

        for specimen in self.pmag_results_data['specimens'].keys():
            for fit in self.pmag_results_data['specimens'][specimen]:
                fit.put(specimen,self.COORDINATE_SYSTEM,self.get_PCA_parameters(specimen,fit.tmin,fit.tmax,self.COORDINATE_SYSTEM,fit.PCA_type))

        if self.interpretation_editor_open:
            self.interpretation_editor.coordinates_box.SetStringSelection(new)
            self.interpretation_editor.update_editor(True)
        self.update_selection()

    #----------------------------------------------------------------------

    def onSelect_orthogonal_box(self, event):
        self.clear_boxes()
        self.Add_text()
        self.draw_figure(self.s)
        self.update_selection()
        if self.current_fit:
            if self.current_fit.get(self.COORDINATE_SYSTEM):
                self.update_GUI_with_new_interpretation()

    #----------------------------------------------------------------------

    def on_next_button(self,event):
      """
      update figures and text when a next button is selected
      """
      index=self.specimens.index(self.s)
      try: fit_index = self.pmag_results_data['specimens'][self.s].index(self.current_fit)
      except KeyError: fit_index = None
      except ValueError: fit_index = None
      if index==len(self.specimens)-1:
        index=0
      else:
        index+=1
      self.initialize_CART_rot(str(self.specimens[index])) #sets self.s calculates params etc.
      self.specimens_box.SetStringSelection(str(self.s))
      if fit_index != None and self.s in self.pmag_results_data['specimens']:
        try: self.current_fit = self.pmag_results_data['specimens'][self.s][fit_index]
        except IndexError: self.current_fit = None
      else: self.current_fit = None
      if self.interpretation_editor_open:
        self.interpretation_editor.change_selected(self.current_fit)
      self.update_selection()

    #----------------------------------------------------------------------

    def on_prev_button(self,event):
      """
      update figures and text when a next button is selected
      """
      index=self.specimens.index(self.s)
      try: fit_index = self.pmag_results_data['specimens'][self.s].index(self.current_fit)
      except KeyError: fit_index = None
      except ValueError: fit_index = None
      if index==0: index=len(self.specimens)
      index-=1
      self.initialize_CART_rot(str(self.specimens[index])) #sets self.s calculates params etc.
      self.specimens_box.SetStringSelection(str(self.s))
      if fit_index != None and self.s in self.pmag_results_data['specimens']:
        try: self.current_fit = self.pmag_results_data['specimens'][self.s][fit_index]
        except IndexError: self.current_fit = None
      else: self.current_fit = None
      if self.interpretation_editor_open:
        self.interpretation_editor.change_selected(self.current_fit)
      self.update_selection()

    #----------------------------------------------------------------------

    def update_selection(self):
        """
        update display (figures, text boxes and statistics windows) with a new selection of specimen
        """

        self.clear_boxes()
        self.clear_higher_level_pars()

        if self.UPPER_LEVEL_SHOW != "specimens":
            self.mean_type_box.SetValue("None")

        #--------------------------
        # check if the coordinate system in the window exists (if not change to "specimen" coordinate system)
        #--------------------------

        coordinate_system=self.coordinates_box.GetValue()
        if coordinate_system=='tilt-corrected' and \
           len(self.Data[self.s]['zijdblock_tilt'])==0:
            self.coordinates_box.SetStringSelection('specimen')
        elif coordinate_system=='geographic' and \
             len(self.Data[self.s]['zijdblock_geo'])==0:
            self.coordinates_box.SetStringSelection("specimen")
        coordinate_system=self.coordinates_box.GetValue()
        self.COORDINATE_SYSTEM=coordinate_system

        #--------------------------
        # update treatment list
        #--------------------------

        self.update_temp_boxes()

        #--------------------------
        # update high level boxes
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

        self.update_PCA_box()

        if self.current_fit:
            self.draw_figure(self.s,False)
        else:
            self.draw_figure(self.s,True)

        self.update_fit_boxs()
        # measurements text box
        self.Add_text()
        #update higher level stats
        self.update_higher_level_stats()
        #redraw interpretations
        self.update_GUI_with_new_interpretation()

    #--------------------------
    # check if high level interpretation exists and display it
    #--------------------------

    def update_higher_level_stats(self):
        dirtype=str(self.coordinates_box.GetValue())
        if dirtype=='specimen':dirtype='DA-DIR'
        elif dirtype=='geographic':dirtype='DA-DIR-GEO'
        elif dirtype=='tilt-corrected':dirtype='DA-DIR-TILT'
        if str(self.level_box.GetValue())=='sample': high_level_type='samples'
        elif str(self.level_box.GetValue())=='site': high_level_type='sites'
        elif str(self.level_box.GetValue())=='location': high_level_type='locations'
        elif str(self.level_box.GetValue())=='study': high_level_type='study'
        high_level_name=str(self.level_names.GetValue())
        elements_type=self.UPPER_LEVEL_SHOW
#        self.high_level_text_box.SetValue("")
        if high_level_name in self.high_level_means[high_level_type].keys():
            if dirtype in self.high_level_means[high_level_type][high_level_name].keys():
                mpars=self.high_level_means[high_level_type][high_level_name][dirtype]
                self.show_higher_levels_pars(mpars)

    #--------------------------
    # update treatment list
    #--------------------------

    def update_temp_boxes(self):
        if self.s not in self.Data.keys():
            self.s = self.Data.keys()[0]
        self.T_list=self.Data[self.s]['zijdblock_steps']
        if self.current_fit:
            self.tmin_box.SetItems(self.T_list)
            self.tmax_box.SetItems(self.T_list)
#            self.tmin_box.SetSelection(-1) #made an edit from SetStringSelection("")
#            self.tmax_box.SetSelection(-1) #made an edit from SetStringSelection("")
            if type(self.current_fit.tmin)==str and type(self.current_fit.tmax)==str:
                self.tmin_box.SetStringSelection(self.current_fit.tmin)
                self.tmax_box.SetStringSelection(self.current_fit.tmax)

    def update_PCA_box(self):
        if self.s in self.pmag_results_data['specimens'].keys():

            if self.current_fit:
                tmin = self.current_fit.tmin
                tmax = self.current_fit.tmax
                calculation_type=self.current_fit.PCA_type
            else:
                calculation_type=self.PCA_type_box.GetValue()
                PCA_type = "None"

            # update calculation type windows
            if calculation_type=="DE-BFL": PCA_type="line"
            elif calculation_type=="DE-BFL-A": PCA_type="line-anchored"
            elif calculation_type=="DE-BFL-O": PCA_type="line-with-origin"
            elif calculation_type=="DE-FM": PCA_type="Fisher"
            elif calculation_type=="DE-BFP": PCA_type="plane"
            self.PCA_type_box.SetStringSelection(PCA_type)


    def get_DIR(self, WD=None):
        """
        Choose a working directory dialog
        """
        if not WD and "-WD" in sys.argv and FIRST_RUN:
            ind=sys.argv.index('-WD')
            self.WD=sys.argv[ind+1]
            #self.WD=os.getcwd()+"/"

        elif not WD:
            dialog = wx.DirDialog(None, "Choose a directory:",defaultPath = self.currentDirectory ,style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON | wx.DD_CHANGE_DIR)
            ok = dialog.ShowModal()
            if ok == wx.ID_OK:
                self.WD=dialog.GetPath()
            else:
                self.WD = os.getcwd()
            dialog.Destroy()
        os.chdir(self.WD)
        self.WD=os.getcwd()
        self.magic_file=os.path.join(self.WD, "magic_measurements.txt")
        self.GUI_log=open(os.path.join(self.WD, "demag_gui.log"),'w')
        self.GUI_log.write("start gui\n")
        self.GUI_log.close()
        self.GUI_log=open(os.path.join(self.WD, "demag_gui.log"),'a')

    #----------------------------------------------------------------------

    def OnClick_listctrl(self,event):

        if not self.current_fit:
            self.add_fit(1)

        for item in range(self.logger.GetItemCount()):
            self.logger.SetItemBackgroundColour(item,"WHITE")

        index=int(event.GetText())
        tmin_index,tmax_index="",""

        if str(self.tmin_box.GetValue())!="":
            tmin_index=self.tmin_box.GetSelection()
        if str(self.tmax_box.GetValue())!="":
            tmax_index=self.tmax_box.GetSelection()

        if tmin_index !="" and tmax_index =="":
            if index<tmin_index:
                self.tmin_box.SetSelection(index)
                self.tmax_box.SetSelection(tmin_index)
            else:
                self.tmax_box.SetSelection(index)
            self.logger.Select(index, on=0)
            self.get_new_PCA_parameters(-1)

        elif tmin_index =="" and tmax_index !="":
            if index>tmax_index:
                self.tmin_box.SetSelection(tmax_index)
                self.tmax_box.SetSelection(index)
            else:
                self.tmin_box.SetSelection(index)
            self.logger.Select(index, on=0)
            self.get_new_PCA_parameters(-1)

        else:
            if index > (self.logger.GetItemCount())/2.:
                self.tmin_box.SetValue("")
                self.tmax_box.SetSelection(index)
            else:
                self.tmin_box.SetSelection(index)
                self.tmax_box.SetValue("")
            return

    def OnRightClickListctrl(self,event): #BLARGE FIX
        '''
        right click on the listctrl opens a popup menu for
        changing the measurement line from "g" to "b"

        If there is  change, the program rewrirte magic_measurements.txt a
        and reads it again.
        '''
        #print "dialogs"
        #y_offset=300*self.GUI_RESOLUTION
        position=event.GetPosition()
        position[1]=position[1]+300*self.GUI_RESOLUTION
        #print position
        g_index=event.GetIndex()

        meas_index = 0
        for i,meas_data in enumerate(self.mag_meas_data):
            if meas_data['er_specimen_name'] == self.s:
                meas_index = i
                break
        meas_index += g_index

        if self.Data[self.s]['measurement_flag'][g_index] == 'g':
            self.Data[self.s]['measurement_flag'][g_index] = 'b'
            self.Data[self.s]['zijdblock'][g_index][5] = 'b'
            if 'zijdblock_geo' in self.Data[self.s] and g_index < len(self.Data[self.s]['zijdblock_geo']):
                self.Data[self.s]['zijdblock_geo'][g_index][5] = 'b'
            if 'zijdblock_tilt' in self.Data[self.s] and g_index < len(self.Data[self.s]['zijdblock_tilt']):
                self.Data[self.s]['zijdblock_tilt'][g_index][5] = 'b'
            self.mag_meas_data[meas_index]['measurement_flag'] = 'b'
        else:
            self.Data[self.s]['measurement_flag'][g_index] = 'g'
            self.Data[self.s]['zijdblock'][g_index][5] = 'g'
            if 'zijdblock_geo' in self.Data[self.s] and g_index < len(self.Data[self.s]['zijdblock_geo']):
                self.Data[self.s]['zijdblock_geo'][g_index][5] = 'g'
            if 'zijdblock_tilt' in self.Data[self.s] and g_index < len(self.Data[self.s]['zijdblock_tilt']):
                self.Data[self.s]['zijdblock_tilt'][g_index][5] = 'g'
            self.mag_meas_data[meas_index]['measurement_flag'] = 'g'

        pmag.magic_write(os.path.join(self.WD, "magic_measurements.txt"),self.mag_meas_data,"magic_measurements")

        self.initialize_CART_rot(self.s)
        if str(self.s) in self.pmag_results_data['specimens']:
            for fit in self.pmag_results_data['specimens'][self.s]:
                if fit.get('specimen') and 'calculation_type' in fit.get('specimen'):
                    fit.put(self.s,'specimen',self.get_PCA_parameters(self.s,fit.tmin,fit.tmax,'specimen',fit.get('specimen')['calculation_type']))
                if len(self.Data[self.s]['zijdblock_geo'])>0 and fit.get('geographic') and 'calculation_type' in fit.get('geographic'):
                    fit.put(self.s,'geographic',self.get_PCA_parameters(self.s,fit.tmin,fit.tmax,'geographic',fit.get('geographic')['calculation_type']))
                if len(self.Data[self.s]['zijdblock_tilt'])>0 and fit.get('tilt-corrected') and 'calculation_type' in fit.get('tilt-corrected'):
                    fit.put(self.s,'tilt-corrected',self.get_PCA_parameters(self.s,fit.tmin,fit.tmax,'tilt-corrected',fit.get('tilt-corrected')['calculation_type']))
        if self.interpretation_editor_open:
            self.interpretation_editor.update_current_fit_data()
        self.calculate_higher_levels_data()
        self.update_selection()


    #----------------------------------------------------------------------

    def on_select_specimen_mean_type_box(self,event):
        self.get_new_PCA_parameters(event)
        if self.interpretation_editor_open:
            self.interpretation_editor.update_logger_entry(self.interpretation_editor.current_fit_index)

    def get_new_PCA_parameters(self,event):  #BLARGE
        """
        calculate statistics when temperatures are selected
        or PCA type is changed
        """

        #remember the last saved interpretation

        #if "saved" in self.pars.keys():
        #    if self.pars['saved']:
        #        self.last_saved_pars={}
        #        for key in self.pars.keys():
        #            self.last_saved_pars[key]=self.pars[key]
        #self.pars['saved']=False
        tmin=str(self.tmin_box.GetValue())
        tmax=str(self.tmax_box.GetValue())
        if tmin=="" or tmax=="":
            return

        if tmin in self.T_list and tmax in self.T_list and \
           (self.T_list.index(tmax) <= self.T_list.index(tmin)):
            return

        PCA_type=self.PCA_type_box.GetValue()
        if PCA_type=="line":calculation_type="DE-BFL"
        elif PCA_type=="line-anchored":calculation_type="DE-BFL-A"
        elif PCA_type=="line-with-origin":calculation_type="DE-BFL-O"
        elif PCA_type=="Fisher":calculation_type="DE-FM"
        elif PCA_type=="plane":calculation_type="DE-BFP"
        coordinate_system=self.COORDINATE_SYSTEM
        if self.current_fit:
            self.current_fit.put(self.s,coordinate_system,self.get_PCA_parameters(self.s,tmin,tmax,coordinate_system,calculation_type))
        if self.interpretation_editor_open:
            self.interpretation_editor.update_current_fit_data()
        self.update_GUI_with_new_interpretation()

    #----------------------------------------------------------------------

    def SortOutBadData(self,block_name): #BLARGE data removal bug
        """
        sort out datpoints marked with 'b' flag
        """
        blockin=self.Data[self.s][block_name]
        blockout=[]
        for i in range(len(blockin)):
            if self.Data[self.s]['measurement_flag'][i]=='g':
               blockout.append(blockin[i])
        return(blockout)


    def get_PCA_parameters(self,specimen,tmin,tmax,coordinate_system,calculation_type):
        """
        calculate statisics
        """

        beg_pca,end_pca = self.get_temp_indecies(None, tmin, tmax, specimen)
        if coordinate_system=='geographic':
            block=self.Data[specimen]['zijdblock_geo']
        elif coordinate_system=='tilt-corrected':
            block=self.Data[specimen]['zijdblock_tilt']
        else:
            block=self.Data[specimen]['zijdblock']
        if  end_pca > beg_pca and   end_pca - beg_pca > 1:
#            print("------------Input Data--------------") #BLARGE
#            print("length of block: " + str(len(block)))
#            print(beg_pca)
#            print("start: " + str(block[beg_pca][0]))
#            print(block[beg_pca][5])
#            print(end_pca)
#            print("end: " + str(block[end_pca][0]))
#            print(block[end_pca][5])
#            print("length: " + str(len(block[beg_pca:end_pca+1])))
#            print("good steps: " + str(sum(map(lambda x: x[5]=='g', block[beg_pca:end_pca+1]))))
#            if block[beg_pca][5]=='b':
#                import pdb
#                pdb.set_trace()
#            print(len(block[beg_pca][5]), len(block[end_pca][5]))
#            print(block[beg_pca][5], block[end_pca][5])
#            print(map(lambda x: [x[0],x[5]],block[beg_pca:end_pca+1]))
            mpars=pmag.domean(block,beg_pca,end_pca,calculation_type) #preformes regression
#            print("included steps: " + str(mpars['specimen_n']))
#            print(mpars['measurement_step_min'],mpars['measurement_step_max'])
        else:
            mpars={}
        for k in mpars.keys():
            try:
                if math.isnan(float(mpars[k])):
                    mpars[k]=0
            except:
                pass
        if "DE-BFL" in calculation_type and 'specimen_dang' not in mpars.keys():
             mpars['specimen_dang']=0

        return(mpars)

    #----------------------------------------------------------------------

    def update_GUI_with_new_interpretation(self): #BLARGE
        """
        update statistics boxes and figures with a new interpretatiom
        when selecting new temperature bound
        """

        if self.current_fit:
            mpars = self.current_fit.get(self.COORDINATE_SYSTEM)
            if self.current_fit.tmin and self.current_fit.tmax:
                self.tmin_box.SetStringSelection(self.current_fit.tmin)
                self.tmax_box.SetStringSelection(self.current_fit.tmax)
            else:
                self.tmin_box.SetStringSelection('None')
                self.tmax_box.SetStringSelection('None')
        else:
            mpars = {}
            self.tmin_box.SetStringSelection('None')
            self.tmax_box.SetStringSelection('None')

        if mpars and 'specimen_dec' in mpars.keys():
            self.sdec_window.SetValue("%.1f"%mpars['specimen_dec'])
            self.sdec_window.SetBackgroundColour(wx.WHITE)
        else:
            self.sdec_window.SetValue("")
            self.sdec_window.SetBackgroundColour(wx.NullColour)

        if mpars and 'specimen_inc' in mpars.keys():
            self.sinc_window.SetValue("%.1f"%mpars['specimen_inc'])
            self.sinc_window.SetBackgroundColour(wx.WHITE)
        else:
            self.sinc_window.SetValue("")
            self.sinc_window.SetBackgroundColour(wx.NullColour)

        if mpars and 'specimen_n' in mpars.keys():
            self.sn_window.SetValue("%i"%mpars['specimen_n'])
            self.sn_window.SetBackgroundColour(wx.WHITE)
        else:
            self.sn_window.SetValue("")
            self.sn_window.SetBackgroundColour(wx.NullColour)

        if mpars and 'specimen_mad' in mpars.keys():
            self.smad_window.SetValue("%.1f"%mpars['specimen_mad'])
            self.smad_window.SetBackgroundColour(wx.WHITE)
        else:
            self.smad_window.SetValue("")
            self.smad_window.SetBackgroundColour(wx.NullColour)

        if mpars and 'specimen_dang' in mpars.keys() and float(mpars['specimen_dang'])!=-1:
            self.sdang_window.SetValue("%.1f"%mpars['specimen_dang'])
            self.sdang_window.SetBackgroundColour(wx.WHITE)
        else:
            self.sdang_window.SetValue("")
            self.sdang_window.SetBackgroundColour(wx.NullColour)

        if mpars and 'specimen_alpha95' in mpars.keys() and float(mpars['specimen_alpha95'])!=-1:
            self.salpha95_window.SetValue("%.1f"%mpars['specimen_alpha95'])
            self.salpha95_window.SetBackgroundColour(wx.WHITE)
        else:
            self.salpha95_window.SetValue("")
            self.salpha95_window.SetBackgroundColour(wx.NullColour)

        if self.orthogonal_box.GetValue()=="X=best fit line dec":
            if mpars and 'specimen_dec' in mpars.keys():
                self.draw_figure(self.s)

        self.draw_interpretation()
        self.calculate_higher_levels_data()
        self.plot_higher_levels_data()

    #----------------------------------------------------------------------

    def draw_interpretation(self): #BLARGE
        """
        draw the specimen interpretations on the zijderveld and the specimen equal area
        @alters: fit.lines, zijplot, specimen_eqarea_interpretation, mplot_interpretation
        """

        self.zijplot.collections=[] # delete fit points
        self.specimen_eqarea_interpretation.clear() #clear equal area
        self.mplot_interpretation.clear() #clear Mplot
        self.specimen_EA_xdata = [] #clear saved x positions on specimen equal area
        self.specimen_EA_ydata = [] #clear saved y positions on specimen equal area

        #check to see if there's a results log or not
        if not (self.s in self.pmag_results_data['specimens'].keys()):
            self.pmag_results_data['specimens'][self.s] = []

        for fit in self.pmag_results_data['specimens'][self.s]:

            pars = fit.get(self.COORDINATE_SYSTEM)

            if (fit.tmin == None or fit.tmax == None or not pars):
                print(fit.tmin,fit.tmax,len(fit.pars))
                continue

            for line in fit.lines:
                if line in self.zijplot.lines:
                    self.zijplot.lines.remove(line)

            PCA_type=fit.PCA_type

            tmin_index,tmax_index = self.get_temp_indecies(fit);

            marker_shape = 'o'
            SIZE = 30
            if fit == self.current_fit:
                marker_shape = 'D'
            if pars['calculation_type'] == "DE-BFP":
                marker_shape = 's'
            if fit in self.bad_fits:
                marker_shape = (4,1,0)
                SIZE=25*self.GUI_RESOLUTION

            # Zijderveld plot

            ymin, ymax = self.zijplot.get_ylim()
            xmin, xmax = self.zijplot.get_xlim()

            for i in range(1):
                if (len(self.CART_rot[:,i]) <= tmin_index or \
                    len(self.CART_rot[:,i]) <= tmax_index):
                    self.Add_text()

            self.zijplot.scatter([self.CART_rot[:,0][tmin_index],self.CART_rot[:,0][tmax_index]],[-1* self.CART_rot[:,1][tmin_index],-1* self.CART_rot[:,1][tmax_index]],marker=marker_shape,s=40,facecolor=fit.color,edgecolor ='k',zorder=100,clip_on=False)
            self.zijplot.scatter([self.CART_rot[:,0][tmin_index],self.CART_rot[:,0][tmax_index]],[-1* self.CART_rot[:,2][tmin_index],-1* self.CART_rot[:,2][tmax_index]],marker=marker_shape,s=50,facecolor=fit.color,edgecolor ='k',zorder=100,clip_on=False)

            if pars['calculation_type'] in ['DE-BFL','DE-BFL-A','DE-BFL-O']:

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
                elif self.ORTHO_PLOT_TYPE=='PCA_dec':
                    if 'specimen_dec' in pars.keys() and type(pars['specimen_dec'])!=str:
                        rotation_declination=pars['specimen_dec']
                    else:
                        rotation_declination=pmag.cart2dir(first_data)[0]
                else:#Zijderveld
                    rotation_declination=pmag.cart2dir(first_data)[0]

#                print(reduce(lambda x,y: x+y,map(lambda x: 'key: ' + str(x[0]) + '\n' + 'data: ' + str(x[1]) + '\n',[[i,self.pars[i]] for i in self.pars])))

                PCA_dir=[pars['specimen_dec'],pars['specimen_inc'],1]
                PCA_dir_rotated=[PCA_dir[0]-rotation_declination,PCA_dir[1],1]
                PCA_CART_rotated=pmag.dir2cart(PCA_dir_rotated)

                slop_xy_PCA=-1*PCA_CART_rotated[1]/PCA_CART_rotated[0]
                slop_xz_PCA=-1*PCA_CART_rotated[2]/PCA_CART_rotated[0]

                # Center of mass rotated for plotting
                # (self.CART_rot_good) ignoring the bad points
                CM_x=mean(self.CART_rot_good[:,0][tmin_index:tmax_index+1])
                CM_y=mean(self.CART_rot_good[:,1][tmin_index:tmax_index+1])
                CM_z=mean(self.CART_rot_good[:,2][tmin_index:tmax_index+1])

                # intercpet from the center of mass
                intercept_xy_PCA=-1*CM_y - slop_xy_PCA*CM_x
                intercept_xz_PCA=-1*CM_z - slop_xz_PCA*CM_x

                xx=array([self.CART_rot[:,0][tmax_index],self.CART_rot[:,0][tmin_index]])
                yy=slop_xy_PCA*xx+intercept_xy_PCA
                zz=slop_xz_PCA*xx+intercept_xz_PCA

                if (pars['calculation_type'] in ['DE-BFL-A','DE-BFL-O']): ###CHECK
                    xx[0] = 0.
                    yy[0] = 0.
                    zz[0] = 0.

                self.zijplot.plot(xx,yy,'-',color=fit.color,lw=3,alpha=0.5,zorder=0)
                self.zijplot.plot(xx,zz,'-',color=fit.color,lw=3,alpha=0.5,zorder=0)

                fit.lines[0] = self.zijplot.lines[-2]
                fit.lines[1] = self.zijplot.lines[-1]

            # Equal Area plot
            self.toolbar2.home()

            # draw a best-fit plane

            if pars['calculation_type']=='DE-BFP' and \
               self.plane_display_box.GetValue() != "show poles":

                ymin, ymax = self.specimen_eqarea.get_ylim()
                xmin, xmax = self.specimen_eqarea.get_xlim()

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

                if self.plane_display_box.GetValue() == "show u. hemisphere" or \
                   self.plane_display_box.GetValue() == "show whole plane":
                    self.specimen_eqarea_interpretation.plot(X_c_d,Y_c_d,'b')
                if self.plane_display_box.GetValue() == "show l. hemisphere" or \
                   self.plane_display_box.GetValue() == "show whole plane":
                    self.specimen_eqarea_interpretation.plot(X_c_up,Y_c_up,'c')

                self.specimen_eqarea_interpretation.set_xlim(-1., 1.)
                self.specimen_eqarea_interpretation.set_ylim(-1., 1.)
                self.specimen_eqarea_interpretation.axes.set_aspect('equal')
                self.specimen_eqarea_interpretation.axis('off')

            else:
                CART=pmag.dir2cart([pars['specimen_dec'],pars['specimen_inc'],1])
                x=CART[0]
                y=CART[1]
                z=abs(CART[2])
                R=array(sqrt(1-z)/sqrt(x**2+y**2))
                eqarea_x=y*R
                eqarea_y=x*R
                self.specimen_EA_xdata.append(eqarea_x)
                self.specimen_EA_ydata.append(eqarea_y)

                if z>0:
                    FC=fit.color;EC='0.1'
                else:
                    FC=fit.color;EC='green'
                self.specimen_eqarea_interpretation.scatter([eqarea_x],[eqarea_y],marker=marker_shape,edgecolor=EC, facecolor=FC,s=SIZE,lw=1,clip_on=False)
                self.specimen_eqarea_interpretation.set_xlim(-1., 1.)
                self.specimen_eqarea_interpretation.set_ylim(-1., 1.)
                self.specimen_eqarea_interpretation.axes.set_aspect('equal')
                self.specimen_eqarea_interpretation.axis('off')

            # M/M0 plot (only if C or mT - not both)
            if self.Data[self.s]['measurement_step_unit'] !="mT:C" and self.Data[self.s]['measurement_step_unit'] !="C:mT":
                ymin, ymax = self.mplot.get_ylim()
                xmin, xmax = self.mplot.get_xlim()
                self.mplot_interpretation.scatter([self.Data[self.s]['zijdblock'][tmin_index][0]],[self.Data[self.s]['zijdblock'][tmin_index][3]/self.Data[self.s]['zijdblock'][0][3]],marker=marker_shape,s=30,facecolor=fit.color,edgecolor ='k',zorder=100,clip_on=False)
                self.mplot_interpretation.scatter([self.Data[self.s]['zijdblock'][tmax_index][0]],[self.Data[self.s]['zijdblock'][tmax_index][3]/self.Data[self.s]['zijdblock'][0][3]],marker=marker_shape,s=30,facecolor=fit.color,edgecolor ='k',zorder=100,clip_on=False)
                self.mplot_interpretation.set_xlim(xmin, xmax)
                self.mplot_interpretation.set_ylim(ymin, ymax)

            # logger
            if fit == self.current_fit:
                for item in range(self.logger.GetItemCount()):
                    if item >= tmin_index and item <= tmax_index:
                        self.logger.SetItemBackgroundColour(item,"LIGHT BLUE")
                    else:
                        self.logger.SetItemBackgroundColour(item,"WHITE")
                    try:
                        relability = self.Data[self.s]['measurement_flag'][item]
                    except IndexError:
                        relability = 'b'
                        print('-E- IndexError in bad data')
                    if relability=='b':
                        self.logger.SetItemBackgroundColour(item,"YELLOW")

        self.canvas1.draw()
        self.canvas2.draw()
        self.canvas3.draw()

    #----------------------------------------------------------------------

    def on_menu_autointerpret(self,event):
        """
        first attempt at an autointerpret functionallity that will find linear segments in the zijderveld to pick out the primary and secondary components.
        @param: event -> the wx.MenuEvent that triggered this event
        """

        for specimen in self.specimens:
            self.initialize_CART_rot(specimen)
            self.pmag_results_data['specimens'][self.s] = []
            self.current_fit = None
            fit_min = 0
            old_direction = self.CART_rot[:,0][1] - self.CART_rot[:,0][0]
            denom = self.CART_rot[:,0][1] - self.CART_rot[:,0][0]
            numer = self.CART_rot[:,1][1] - self.CART_rot[:,1][0]
            old_slope_xy = numer/denom
            numer = self.CART_rot[:,2][1] - self.CART_rot[:,2][0]
            old_slope_xz = numer/denom
            for fit_max in range(2,len(self.CART_rot)):
                direction = self.CART_rot[:,0][fit_max] - self.CART_rot[:,0][fit_max-1]

                y_dist = self.CART_rot[:,1][fit_max] - self.CART_rot[:,1][fit_max-1]

                z_dist = self.CART_rot[:,2][fit_max] - self.CART_rot[:,2][fit_max-1]

                denom = self.CART_rot[:,0][fit_max] - self.CART_rot[:,0][fit_max-1]
                numer = self.CART_rot[:,1][fit_max] - self.CART_rot[:,1][fit_max-1]
                slope_xy = numer/denom
                numer = self.CART_rot[:,2][fit_max] - self.CART_rot[:,2][fit_max-1]
                slope_xz = numer/denom

                old_direction = self.CART_rot[:,0][fit_max] - self.CART_rot[:,0][fit_min]

                denom = self.CART_rot[:,0][fit_max] - self.CART_rot[:,0][fit_min]
                numer = self.CART_rot[:,1][fit_max] - self.CART_rot[:,1][fit_min]
                old_slope_xy = numer/denom
                numer = self.CART_rot[:,2][fit_max] - self.CART_rot[:,2][fit_min]
                old_slope_xz = numer/denom

#                print('----------------CALCULATIONS-----------------')
#                print('fit_max: ' + str(fit_max))
#                print('slope_xy: ' + str(slope_xy))
#                print('slope_xz: ' + str(slope_xz))
#                print('y_dist: ' + str(y_dist))
#                print('z_dist: ' + str(z_dist))

                if (direction < 0 and old_direction > 0) or \
                   (direction > 0 and old_direction < 0) or \
                   (slope_xy < 0 and old_slope_xy > 0) or \
                   (slope_xy > 0 and old_slope_xy < 0) or \
                   (slope_xz < 0 and old_slope_xz > 0) or \
                   (slope_xz > 0 and old_slope_xz < 0) or \
                   abs(y_dist) > .5 or abs(z_dist) > .5 or \
                   1e-2 > slope_xy > -1e-2 or 1e-2 > slope_xz > -1e-2 or \
                   fit_max == len(self.CART_rot)-1:

                    if (slope_xy < 0 and old_slope_xy > 0) or \
                       (slope_xy > 0 and old_slope_xy < 0) or \
                       (slope_xz < 0 and old_slope_xz > 0) or \
                       (slope_xz > 0 and old_slope_xz < 0):
                        fit_max -= 1

                    length_xy = sqrt((self.CART_rot[:,0][fit_max] - self.CART_rot[:,0][fit_min])**2 + (self.CART_rot[:,1][fit_max] - self.CART_rot[:,1][fit_min])**2)
                    length_xz = sqrt((self.CART_rot[:,0][fit_max] - self.CART_rot[:,0][fit_min])**2 + (self.CART_rot[:,2][fit_max] - self.CART_rot[:,2][fit_min])**2)

#                    if self.Data[self.s]['zijdblock'][fit_max][5] == 'b' or \
#                       self.Data[self.s]['zijdblock_geo'][fit_max][5] == 'b' or \
#                       self.Data[self.s]['zijdblock_tilt'][fit_max][5] == 'b' or \
                    if self.Data[self.s]['measurement_flag'][fit_max] == 'b' or \
                       fit_max - fit_min <= 3 or \
                       length_xy < .2 or length_xz < .2:
                            if fit_max - fit_min > 3: fit_min = fit_max
                            continue

                    next_fit = str(len(self.pmag_results_data['specimens'][self.s]) + 1)
                    new_fit_name = 'Fit ' + next_fit
                    new_fit_number = int(next_fit)-1
                    new_fit_tmin = self.Data[self.s]['zijdblock_steps'][fit_min]
                    new_fit_tmax = self.Data[self.s]['zijdblock_steps'][fit_max]
                    new_fit_color = self.colors[(int(next_fit)-1) % len(self.colors)]
                    new_fit = Fit(new_fit_name, new_fit_tmin, new_fit_tmax, new_fit_color, self)
                    self.pmag_results_data['specimens'][self.s].append(new_fit)
                    PCA_type=self.PCA_type_box.GetValue()
                    if PCA_type=="line":calculation_type="DE-BFL"
                    elif PCA_type=="line-anchored":calculation_type="DE-BFL-A"
                    elif PCA_type=="line-with-origin":calculation_type="DE-BFL-O"
                    elif PCA_type=="Fisher":calculation_type="DE-FM"
                    elif PCA_type=="plane":calculation_type="DE-BFP"
                    coordinate_system=self.COORDINATE_SYSTEM
                    if new_fit:
                        new_fit.put(self.s,coordinate_system,self.get_PCA_parameters(self.s,new_fit_tmin,new_fit_tmax,coordinate_system,calculation_type))
                    fit_min = fit_max+1

        self.s = self.specimens[0]
        self.specimens_box.SetSelection(0)

        if self.pmag_results_data['specimens'][self.s]:
            self.current_fit = self.pmag_results_data['specimens'][self.s][-1]

        self.update_selection()


    #----------------------------------------------------------------------

    def on_save_interpretation_button(self,event):

        """
        on the save button
        the interpretation is saved to pmag_results_table data
        in all coordinate systems
        """

        if self.current_fit:
            calculation_type=self.current_fit.get(self.COORDINATE_SYSTEM)['calculation_type']
            tmin=str(self.tmin_box.GetValue())
            tmax=str(self.tmax_box.GetValue())

            self.current_fit.put(self.s,'specimen',self.get_PCA_parameters(self.s,tmin,tmax,'specimen',calculation_type))
            if len(self.Data[self.s]['zijdblock_geo'])>0:
                self.current_fit.put(self.s,'geographic',self.get_PCA_parameters(self.s,tmin,tmax,'geographic',calculation_type))
            if len(self.Data[self.s]['zijdblock_tilt'])>0:
                self.current_fit.put(self.s,'tilt-corrected',self.get_PCA_parameters(self.s,tmin,tmax,'tilt-corrected',calculation_type))

        # calculate higher level data
        self.calculate_higher_levels_data()
        self.plot_higher_levels_data()
        self.on_menu_save_interpretation(-1)
        self.update_selection()
        self.close_warning=True

    #----------------------------------------------------------------------

    #----------------------------------------------------------------------

    def clear_boxes(self):
        """
        Clear all boxes
        """
        self.tmin_box.Clear()
        self.tmin_box.SetStringSelection("")
        if self.current_fit:
            self.tmin_box.SetItems(self.T_list)
            self.tmin_box.SetSelection(-1)

        self.tmax_box.Clear()
        self.tmax_box.SetStringSelection("")
        if self.current_fit:
            self.tmax_box.SetItems(self.T_list)
            self.tmax_box.SetSelection(-1)

        self.fit_box.Clear()
        self.fit_box.SetStringSelection("")
        if self.s in self.pmag_results_data['specimens'] and self.pmag_results_data['specimens'][self.s]:
            self.fit_box.SetItems(list(map(lambda x: x.name, self.pmag_results_data['specimens'][self.s])))

        for parameter in ['dec','inc','n','mad','dang','alpha95']:
            COMMAND="self.s%s_window.SetValue('')"%parameter
            exec COMMAND
            COMMAND="self.s%s_window.SetBackgroundColour(wx.NullColour)"%parameter
            exec COMMAND

    #----------------------------------------------------------------------

    def onSelect_mean_type_box(self,event):
        # calculate higher level data
        self.calculate_higher_levels_data()
        self.update_selection()

    def onSelect_mean_fit_box(self,event):
        #get new fit to display
        new_fit = self.mean_fit_box.GetValue()
        self.mean_fit = new_fit
        if self.interpretation_editor_open:
            self.interpretation_editor.mean_fit_box.SetStringSelection(new_fit)
        # calculate higher level data
        self.calculate_higher_levels_data()
        self.update_higher_level_stats()
        self.plot_higher_levels_data()

    #----------------------------------------------------------------------

    def onSelect_higher_level(self,event,called_by_interp_editor=False):
       self.UPPER_LEVEL=self.level_box.GetValue()
       if self.UPPER_LEVEL=='sample':
           if self.interpretation_editor_open:
               self.interpretation_editor.show_box.SetItems(['specimens'])
               self.interpretation_editor.show_box.SetStringSelection('specimens')
           if self.UPPER_LEVEL_SHOW not in ['specimens']: self.UPPER_LEVEL_SHOW = u'specimens'
           self.level_names.SetItems(self.samples)
           self.level_names.SetStringSelection(self.Data_hierarchy['sample_of_specimen'][self.s])

       elif self.UPPER_LEVEL=='site':
           if self.interpretation_editor_open:
               self.interpretation_editor.show_box.SetItems(['specimens','samples'])
               if self.interpretation_editor.show_box.GetValue() not in ['specimens','samples']:
                   self.interpretation_editor.show_box.SetStringSelection('samples')
           if self.UPPER_LEVEL_SHOW not in ['specimens','samples']: self.UPPER_LEVEL_SHOW = u'specimens'
           self.level_names.SetItems(self.sites)
           self.level_names.SetStringSelection(self.Data_hierarchy['site_of_specimen'][self.s])

       elif self.UPPER_LEVEL=='location':
           if self.interpretation_editor_open:
               self.interpretation_editor.show_box.SetItems(['specimens','samples','sites'])#,'sites VGP'])
               if self.interpretation_editor.show_box.GetValue() not in ['specimens','samples','sites']:#,'sites VGP']:
                   self.interpretation_editor.show_box.SetStringSelection('sites')
           self.level_names.SetItems(self.locations)
           self.level_names.SetStringSelection(self.Data_hierarchy['location_of_specimen'][self.s])

       elif self.UPPER_LEVEL=='study':
           if self.interpretation_editor_open:
               self.interpretation_editor.show_box.SetItems(['specimens','samples','sites'])#,'sites VGP'])
               if self.interpretation_editor.show_box.GetValue() not in ['specimens','samples','sites']:#,'sites VGP']:
                   self.interpretation_editor.show_box.SetStringSelection('sites')
           self.level_names.SetItems(['this study'])
           self.level_names.SetStringSelection('this study')

       if not called_by_interp_editor:
           if self.interpretation_editor_open:
               self.interpretation_editor.level_box.SetStringSelection(self.UPPER_LEVEL)
               self.interpretation_editor.on_select_higher_level(event,True)
           else:
               self.update_selection()

    #----------------------------------------------------------------------

    def onSelect_level_name(self,event,called_by_interp_editor=False):
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
           specimen_list.sort(cmp=specimens_comparator)
           self.s=str(specimen_list[0])
           self.specimens_box.SetStringSelection(str(self.s))

       if self.interpretation_editor_open and not called_by_interp_editor:
           self.interpretation_editor.level_names.SetStringSelection(high_level_name)
           self.interpretation_editor.on_select_level_name(event,True)

       self.update_selection()


    def calculate_high_level_mean (self,high_level_type,high_level_name,calculation_type,elements_type):
        """
        high_level_type:'samples','sites','locations','study'
        calculation_type: 'Bingham','Fisher','Fisher by polarity'
        elements_type (what to average):'specimens','samples','sites' (Ron. ToDo alos VGP and maybe locations?)
        figure out what level to average,and what elements to average (specimen, samples, sites, vgp)
        """

        if calculation_type == "None": return

        if high_level_type not in self.high_level_means: self.high_level_means[high_level_type] = {}
        self.high_level_means[high_level_type][high_level_name]={}
        for dirtype in ["DA-DIR","DA-DIR-GEO","DA-DIR-TILT"]:
            if high_level_name not in self.Data_hierarchy[high_level_type].keys():
                continue

            elements_list=self.Data_hierarchy[high_level_type][high_level_name][elements_type]
            pars_for_mean={}
            pars_for_mean["All"] = []
            colors_for_means={}

            for element in elements_list:
                if elements_type=='specimens' and element in self.pmag_results_data['specimens']:
                    for fit in self.pmag_results_data['specimens'][element]:
                        if fit in self.bad_fits:
                            continue
                        if fit.name not in pars_for_mean.keys():
                            pars_for_mean[fit.name] = []
                            colors_for_means[fit.name] = fit.color
                        try:
                            #is this fit to be included in mean
                            if self.mean_fit == 'All' or self.mean_fit == fit.name:
                                pars = fit.get(dirtype)
                                if pars == {}:
                                    pars = self.get_PCA_parameters(element,fit.tmin,fit.tmax,dirtype,fit.PCA_type)
                                    fit.put(element,dirtype,pars)
                            else:
                                continue
                            if "calculation_type" in pars.keys() and pars["calculation_type"] == 'DE-BFP':
                                dec,inc,direction_type=pars["specimen_dec"],pars["specimen_inc"],'p'
                            elif "specimen_dec" in pars.keys() and "specimen_inc" in pars.keys():
                                dec,inc,direction_type=pars["specimen_dec"],pars["specimen_inc"],'l'
                            elif "dec" in pars.keys() and "inc" in pars.keys():
                                dec,inc,direction_type=pars["dec"],pars["inc"],'l'
                            else:
                                print "-E- ERROR: cant find mean for specimen interpertation: %s , %s"%(element,fit.name)
                                print(dec,inc,direction_type)
                                print(pars)
                                continue
                            #add for calculation
                            pars_for_mean[fit.name].append({'dec':float(dec),'inc':float(inc),'direction_type':direction_type,'element_name':element})
                            pars_for_mean["All"].append({'dec':float(dec),'inc':float(inc),'direction_type':direction_type,'element_name':element})
                        except KeyError:
                            print("KeyError in calculate_high_level_mean for element: " + str(element))
                            continue
                else:
                    try:
                        pars=self.high_level_means[elements_type][element][dirtype]
                        if "dec" in pars.keys() and "inc" in pars.keys():
                            dec,inc,direction_type=pars["dec"],pars["inc"],'l'
                        else:
#                            print "-E- ERROR: cant find mean for element %s"%element
                            continue 
                    except KeyError:
#                        print("KeyError in calculate_high_level_mean for element: " + str(element) + " please report to a dev")
                        continue

            for key in pars_for_mean.keys():
                if len(pars_for_mean[key]) > 0 and key != "All":
<<<<<<< HEAD
                    if high_level_name not in self.pmag_results_data[self.UPPER_LEVEL_SHOW].keys():
                        self.pmag_results_data[self.UPPER_LEVEL_SHOW][high_level_name] = []
                    if key not in map(lambda x: x.name, self.pmag_results_data[self.UPPER_LEVEL_SHOW][high_level_name]):
                        self.pmag_results_data[self.UPPER_LEVEL_SHOW][high_level_name].append(Fit(key, None, None, colors_for_means[key], self))
                        key_index = -1
                    else:
                        key_index = map(lambda x: x.name, self.pmag_results_data[self.UPPER_LEVEL_SHOW][high_level_name]).index(key)
=======
                    if high_level_name not in self.pmag_results_data[high_level_type].keys():
                        self.pmag_results_data[high_level_type][high_level_name] = []
                    if key not in map(lambda x: x.name, self.pmag_results_data[high_level_type][high_level_name]):
                        self.pmag_results_data[high_level_type][high_level_name].append(Fit(key, None, None, colors_for_means[key], self))
                        key_index = -1
                    else:
                        key_index = map(lambda x: x.name, self.pmag_results_data[high_level_type][high_level_name]).index(key)
>>>>>>> origin/master
                    new_pars = self.calculate_mean(pars_for_mean[key],calculation_type)
                    map_keys = new_pars.keys()
                    map_keys.remove("calculation_type")
                    if calculation_type == "Fisher":
                        for mkey in map_keys:
                            new_pars[mkey] = float(new_pars[mkey])
<<<<<<< HEAD
                    self.pmag_results_data[self.UPPER_LEVEL_SHOW][high_level_name][key_index].put(None, dirtype,new_pars)
=======
                    self.pmag_results_data[high_level_type][high_level_name][key_index].put(None, dirtype,new_pars)
>>>>>>> origin/master
                if len(pars_for_mean[key]) > 0 and key == "All":
                    self.high_level_means[high_level_type][high_level_name][dirtype] = self.calculate_mean(pars_for_mean["All"],calculation_type)

    #----------------------------------------------------------------------

    def calculate_mean(self,pars_for_mean,calculation_type):
        '''
        calculates:
            Fisher mean (lines/planes)
            or Fisher by polarity
        '''

        if len(pars_for_mean)==0:
            return({})

        elif len(pars_for_mean)==1:
            return ({"dec":float(pars_for_mean[0]['dec']),"inc":float(pars_for_mean[0]['inc']),"calculation_type":calculation_type,"n":1})

#        elif calculation_type =='Bingham':
#            data=[]
#            for pars in pars_for_mean:
#                # ignore great circle
#                if 'direction_type' in pars.keys() and 'direction_type'=='p':
#                    continue
#                else:
#                    data.append([pars['dec'],pars['inc']])
#            mpars=pmag.dobingham(data)
#            self.switch_stats_button.SetRange(0,0)

        elif calculation_type=='Fisher':
            mpars=pmag.dolnp(pars_for_mean,'direction_type')
            self.switch_stats_button.SetRange(0,0)
            if self.interpretation_editor_open:
                self.interpretation_editor.switch_stats_button.SetRange(0,0)

        elif calculation_type=='Fisher by polarity':
            mpars=pmag.fisher_by_pol(pars_for_mean)
            self.switch_stats_button.SetRange(0,len(mpars.keys())-1)
            if self.interpretation_editor_open:
                self.interpretation_editor.switch_stats_button.SetRange(0,len(mpars.keys())-1)
            for key in mpars.keys():
                mpars[key]['n_planes'] = 0
                mpars[key]['calculation_type'] = 'Fisher'

        mpars['calculation_type']=calculation_type

        return(mpars)


    def calculate_higher_levels_data(self):

        high_level_type=str(self.level_box.GetValue())
        if high_level_type=='sample':high_level_type='samples'
        if high_level_type=='site':high_level_type='sites'
        if high_level_type=='location':high_level_type='locations'
        high_level_name=str(self.level_names.GetValue())
        calculation_type=str(self.mean_type_box.GetValue())
        elements_type=self.UPPER_LEVEL_SHOW
        if self.interpretation_editor_open: self.interpretation_editor.mean_type_box.SetStringSelection(calculation_type)
        self.calculate_high_level_mean(high_level_type,high_level_name,calculation_type,elements_type)

    def on_select_plane_display_box(self,event):
        self.draw_interpretation()
        self.plot_higher_levels_data()

    def plot_higher_levels_data(self):

       self.toolbar4.home()

       high_level=self.level_box.GetValue()
       self.UPPER_LEVEL_NAME=self.level_names.GetValue()
       self.UPPER_LEVEL_MEAN=self.mean_type_box.GetValue()

       self.high_level_eqarea.clear()
       what_is_it=self.level_box.GetValue()+": "+self.level_names.GetValue()
       self.high_level_eqarea.text(-1.2,1.15,what_is_it,{'family':'Arial', 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })

       if self.COORDINATE_SYSTEM=="geographic": dirtype='DA-DIR-GEO'
       elif self.COORDINATE_SYSTEM=="tilt-corrected": dirtype='DA-DIR-TILT'
       else: dirtype='DA-DIR'

       if self.level_box.GetValue()=='sample': high_level_type='samples'
       if self.level_box.GetValue()=='site': high_level_type='sites'
       if self.level_box.GetValue()=='location': high_level_type='locations'
       if self.level_box.GetValue()=='study': high_level_type='study'

       high_level_name=str(self.level_names.GetValue())
       calculation_type=str(self.mean_type_box.GetValue())
       elements_type=self.UPPER_LEVEL_SHOW

       elements_list=self.Data_hierarchy[high_level_type][high_level_name][elements_type]

       self.higher_EA_xdata = [] #clear saved x positions on higher equal area
       self.higher_EA_ydata = [] #clear saved y positions on higher equal area

       # plot elements directions
       for element in elements_list:
            if element not in self.pmag_results_data[elements_type].keys():
                self.calculate_high_level_mean(elements_type,element,"Fisher","specimens")
            if element in self.pmag_results_data[elements_type].keys():
                self.plot_higher_level_equalarea(element)

            else:
                if element in self.high_level_means[elements_type].keys():
                    if dirtype in self.high_level_means[elements_type][element].keys():
                        mpars=self.high_level_means[elements_type][element][dirtype]
                        self.plot_eqarea_pars(mpars,self.high_level_eqarea)

       # plot elements means
       if calculation_type!="None":
           if high_level_name in self.high_level_means[high_level_type].keys():
               if dirtype in self.high_level_means[high_level_type][high_level_name].keys():
                   self.plot_eqarea_mean(self.high_level_means[high_level_type][high_level_name][dirtype],self.high_level_eqarea)


       self.high_level_eqarea.set_xlim(-1., 1.)
       self.high_level_eqarea.set_ylim(-1., 1.)
       self.high_level_eqarea.axes.set_aspect('equal')
       self.high_level_eqarea.axis('off')
       self.canvas4.draw()
       if self.interpretation_editor_open:
           self.update_higher_level_stats()
           self.interpretation_editor.update_editor(False)

    def plot_higher_level_equalarea(self,element): #BLARGE
        if self.interpretation_editor_open:
            higher_level = self.interpretation_editor.show_box.GetValue()
        else: higher_level = self.UPPER_LEVEL_SHOW
        fits = []
        if higher_level not in self.pmag_results_data: print("no level: " + str(higher_level)); return
        if element not in self.pmag_results_data[higher_level]: print("no element: " + str(element)); return
        if self.mean_fit == 'All':
            fits = self.pmag_results_data[higher_level][element]
        elif self.mean_fit != 'None' and self.mean_fit != None:
#             if self.s not in self.pmag_results_data['specimens'] or \
# self.mean_fit not in map(lambda x: x.name, self.pmag_results_data['specimens'][self.s]):
#                 self.mean_fit_box.SetStringSelection('None')
#                 self.mean_fits = 'None'
#             else:
            #by name fit grouping
            fits = [fit for fit in self.pmag_results_data[higher_level][element] if fit.name == self.mean_fit]
            #by index fit grouping
            # fit_index = map(lambda x: x.name, self.pmag_results_data['specimens'][self.s]).index(self.mean_fit)
            # try: fits = [self.pmag_results_data['specimens'][specimen][fit_index]]
            # except IndexError: pass #print('-W- Not all specimens have this fit');
        else:
            fits = []
        fig = self.high_level_eqarea
        if fits:
            for fit in fits:
                pars = fit.get(self.COORDINATE_SYSTEM)
                if not pars: print('no parameters to plot for: ' + fit.name); return
                if "specimen_dec" in pars.keys() and "specimen_inc" in pars.keys():
                    dec=pars["specimen_dec"];inc=pars["specimen_inc"]
                elif "dec" in pars.keys() and "inc" in pars.keys():
                    dec=pars["dec"];inc=pars["inc"]
                else:
                    print("-E- no dec and inc values for:\n" + str(fit))
                XY=pmag.dimap(dec,inc)
                if inc>0:
                    FC=fit.color;SIZE=15*self.GUI_RESOLUTION
                else:
                    FC='white';SIZE=15*self.GUI_RESOLUTION
                marker_shape = 'o'
                SIZE = 30
                if fit == self.current_fit:
                    marker_shape = 'D'
                if pars['calculation_type'] == "DE-BFP":
                    marker_shape = 's'
                if fit in self.bad_fits:
                    marker_shape = (4,1,0)
                    SIZE=25*self.GUI_RESOLUTION

                # draw a best-fit plane
                if pars['calculation_type']=='DE-BFP' and \
                   self.plane_display_box.GetValue() != "show poles":
                    ymin, ymax = self.specimen_eqarea.get_ylim()
                    xmin, xmax = self.specimen_eqarea.get_xlim()

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

                    if self.plane_display_box.GetValue() == "show u. hemisphere" or \
                       self.plane_display_box.GetValue() == "show whole plane":
                        fig.plot(X_c_d,Y_c_d,'b')
                    if self.plane_display_box.GetValue() == "show l. hemisphere" or \
                       self.plane_display_box.GetValue() == "show whole plane":
                        fig.plot(X_c_up,Y_c_up,'c')
                    fig.set_xlim(-1., 1.)
                    fig.set_ylim(-1., 1.)
                    fig.axes.set_aspect('equal')
                    fig.axis('off')
                    continue

                self.higher_EA_xdata.append(XY[0])
                self.higher_EA_ydata.append(XY[1])
                fig.scatter([XY[0]],[XY[1]],marker=marker_shape,edgecolor=fit.color, facecolor=FC,s=SIZE,lw=1,clip_on=False)

    def plot_eqarea_pars(self,pars,fig):
        # plot best-fit plane
        #fig.clear()
        if pars=={}:
            pass
        elif 'calculation_type' in pars.keys() and pars['calculation_type']=='DE-BFP':
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
        #fig.clear()
        mpars_to_plot=[]
        if meanpars=={}:
            return
        if meanpars['calculation_type']=='Fisher by polarity':
            for mode in meanpars.keys():
                if type(meanpars[mode])==dict and meanpars[mode]!={}:
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

            if "alpha95" in mpars.keys():
            # get the alpha95
                Xcirc,Ycirc=[],[]
                Da95,Ia95=pmag.circ(float(mpars["dec"]),float(mpars["inc"]),float(mpars["alpha95"]))
                for k in  range(len(Da95)):
                    XY=pmag.dimap(Da95[k],Ia95[k])
                    Xcirc.append(XY[0])
                    Ycirc.append(XY[1])
                fig.plot(Xcirc,Ycirc,'g')

        fig.set_xlim(xmin, xmax)
        fig.set_ylim(ymin, ymax)

    def on_select_stats_button(self,events):
        i = self.switch_stats_button.GetValue()
        self.update_higher_level_stats()

    def clear_higher_level_pars(self):
        for val in ['mean_type','dec','inc','alpha95','K','R','n_lines','n_planes']:
            COMMAND = """self.%s_window.SetValue("")"""%(val)
            exec COMMAND
        if self.interpretation_editor_open:
            ie = self.interpretation_editor
            for val in ['mean_type','dec','inc','alpha95','K','R','n_lines','n_planes']:
                COMMAND = """ie.%s_window.SetValue("")"""%(val)
                exec COMMAND

    def show_higher_levels_pars(self,mpars):

        FONT_RATIO=self.GUI_RESOLUTION+(self.GUI_RESOLUTION-1)*5
        font2 = wx.Font(12+min(1,FONT_RATIO), wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Arial')

        if mpars["calculation_type"]=='Fisher':
            if mpars["calculation_type"]=='Fisher' and "alpha95" in mpars.keys():
                for val in ['mean_type:calculation_type','dec:dec','inc:inc','alpha95:alpha95','K:K','R:R','n_lines:n_lines','n_planes:n_planes']:
                    val,ind = val.split(":")
                    COMMAND = """self.%s_window.SetValue(str(mpars['%s']))"""%(val,ind)
                    exec COMMAND

            if self.interpretation_editor_open:
                ie = self.interpretation_editor
                if mpars["calculation_type"]=='Fisher' and "alpha95" in mpars.keys():
                    for val in ['mean_type:calculation_type','dec:dec','inc:inc','alpha95:alpha95','K:K','R:R','n_lines:n_lines','n_planes:n_planes']:
                        val,ind = val.split(":")
                        COMMAND = """ie.%s_window.SetValue(str(mpars['%s']))"""%(val,ind)
                        exec COMMAND

        if mpars["calculation_type"]=='Fisher by polarity':
            i = self.switch_stats_button.GetValue()
            keys = mpars.keys()
            keys.remove('calculation_type')
            keys.sort()
            name = keys[i%len(keys)]
            mpars = mpars[name]
            if type(mpars) != dict: print("error in showing higher level mean"); return
            if mpars["calculation_type"]=='Fisher' and "alpha95" in mpars.keys():
                for val in ['mean_type:calculation_type','dec:dec','inc:inc','alpha95:alpha95','K:k','R:r','n_lines:n','n_planes:n_planes']:
                    val,ind = val.split(":")
                    if val == 'mean_type':
                        COMMAND = """self.%s_window.SetValue('%s')"""%(val,mpars[ind] + ":" + name)
                    else:
                        COMMAND = """self.%s_window.SetValue(str(mpars['%s']))"""%(val,ind)
                    exec COMMAND

            if self.interpretation_editor_open:
                ie = self.interpretation_editor
                if mpars["calculation_type"]=='Fisher' and "alpha95" in mpars.keys():
                    for val in ['mean_type:calculation_type','dec:dec','inc:inc','alpha95:alpha95','K:k','R:r','n_lines:n','n_planes:n_planes']:
                        val,ind = val.split(":")
                        if val == 'mean_type':
                            COMMAND = """ie.%s_window.SetValue('%s')"""%(val,mpars[ind] + ":" + name)
                        else:
                            COMMAND = """ie.%s_window.SetValue(str(mpars['%s']))"""%(val,ind)
                        exec COMMAND

#            if mpars["calculation_type"]=='Bingham':
#                String="Bingham statistics:\n"
#    #            self.high_level_text_box.AppendText(String)
#                String=""
#                String=String+"dec"+": "+"%.1f\n"%float(mpars['dec'])
#                String=String+"inc"+": "+"%.1f\n"%float(mpars['inc'])
#                String=String+"n"+": "+"%.0f\n"%float(mpars['n'])
#                String=String+"Zdec"+": "+"%.0f\n"%float(mpars['Zdec'])
#                String=String+"Zinc"+": "+"%.1f\n"%float(mpars['Zinc'])
#                String=String+"Zeta"+": "+"%.4f\n"%float(mpars['Zeta'])
#                String=String+"Edec"+": "+"%.0f\n"%float(mpars['Edec'])
#                String=String+"Einc"+": "+"%.1f\n"%float(mpars['Einc'])
#                String=String+"Eta"+": "+"%.1f\n"%float(mpars['Eta'])
    #            self.high_level_text_box.AppendText(String)

    #def initialize_acceptence_criteria (self):
    #    self.acceptance_criteria={}
    #    self.acceptance_criteria=self.pmag.initialize_acceptence_criteria()

#============================================

    #-------------------------------
    # get_data:
    # Read data from magic_measurements.txt
    #-------------------------------

    def get_data(self):

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
      mag_meas_data,file_type=pmag.magic_read(self.magic_file) #BLARGE
      self.mag_meas_data=copy.deepcopy(self.merge_pmag_recs(mag_meas_data))

      self.GUI_log.write("-I- Read magic file  %s\n"%self.magic_file)

      # get list of unique specimen names

      CurrRec=[]
      #print "-I- get sids"

      sids=pmag.get_specs(self.mag_meas_data) # samples ID's
      #print "-I- done get sids"

      #print "initialize blocks"

      for s in sids:

          if s not in Data.keys():
              Data[s]={}
              Data[s]['zijdblock']=[]
              Data[s]['zijdblock_geo']=[]
              Data[s]['zijdblock_tilt']=[]
              Data[s]['zijdblock_lab_treatments']=[]
              Data[s]['pars']={}
              Data[s]['zijdblock_steps']=[]
              Data[s]['measurement_flag']=[]# a list of points 'g' or 'b'
              Data[s]['mag_meas_data_index']=[]  # index in original magic_measurements.txt
              #print "done initialize blocks"

      #print "sorting meas data"
      cnt=-1
      for rec in self.mag_meas_data: #BLARGE MEASUREMENT READ IN
          cnt+=1 #index counter
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
          INC=["LT-NO","LT-AF-Z","LT-T-Z", "LT-M-Z","LT-LT-Z"]

          methods=rec["magic_method_codes"].replace(" ","").strip("\n").split(":")
          LP_methods=[]
          LT_methods=[]

          for i in range (len(methods)):
               methods[i]=methods[i].strip()
          if 'measurement_flag' not in rec.keys():
              rec['measurement_flag']='g'
          SKIP=True;lab_treatment=""
          for meth in methods:
               if meth in ["LT-NO","LT-AF-Z","LT-T-Z", "LT-M-Z","LT-LT-Z"]:
                   lab_treatment=meth
                   SKIP=False
               if "LP" in meth:
                   LP_methods.append(meth)
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
             elif  "LT-T-Z" in  methods or "LT-LT-Z" in methods:
                 tr = float(rec["treatment_temp"])-273. # celsius
                 measurement_step_unit="C" # in magic its K in GUI its C
                 LPcode="LP-DIR-T"
             elif  "LT-M-Z" in  methods:
                 tr = float(rec["measurement_number"]) # temporary for microwave
             else:
                 tr = float(rec["measurement_number"])

             ZI=0

             if tr !="":
                 Data[s]['mag_meas_data_index'].append(cnt) # magic_measurement file intex
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
                 else:
                     continue
                 if "measurement_inc" in rec.keys() and rec["measurement_inc"] != "":
                     inc=float(rec["measurement_inc"])
                 else:
                     continue
                 if "measurement_magn_moment" in rec.keys() and rec["measurement_magn_moment"] != "":
                     intensity=float(rec["measurement_magn_moment"])
                 else:
                     continue
                 if 'magic_instrument_codes' not in rec.keys():
                     rec['magic_instrument_codes']=''
                 Data[s]['zijdblock'].append([tr,dec,inc,intensity,ZI,rec['measurement_flag'],rec['magic_instrument_codes']])
                 if 'magic_experiment_name' in Data[s].keys() and Data[s]['magic_experiment_name']!=rec["magic_experiment_name"]:
                      self.GUI_log.write("-E- ERROR: specimen %s has more than one demagnetization experiment name. You need to merge them to one experiment-name?\n")
                 if float(tr)==0 or float(tr)==273:
                    Data[s]['zijdblock_steps'].append("0")
                 elif measurement_step_unit=="C":
                    Data[s]['zijdblock_steps'].append("%.0f%s"%(tr,measurement_step_unit))
                 else:
                    Data[s]['zijdblock_steps'].append("%.1f%s"%(tr,measurement_step_unit))
                 #--------------
                 Data[s]['magic_experiment_name']=rec["magic_experiment_name"]
                 if "magic_instrument_codes" in rec.keys():
                     Data[s]['magic_instrument_codes']=rec['magic_instrument_codes']
                 Data[s]["magic_method_codes"]=LPcode

                 #--------------
                 # ""good" or "bad" data
                 #--------------

                 flag='g'
                 if 'measurement_flag' in rec.keys():
                     if str(rec["measurement_flag"])=='b':
                         flag='b'
                 Data[s]['measurement_flag'].append(flag)

                 # gegraphic coordinates

                 try:
                    sample_azimuth=float(self.Data_info["er_samples"][sample]['sample_azimuth'])
                    sample_dip=float(self.Data_info["er_samples"][sample]['sample_dip'])
                    sample_orientation_flag='g'
                    if 'sample_orientation_flag' in  self.Data_info["er_samples"][sample].keys():
                        if str(self.Data_info["er_samples"][sample]['sample_orientation_flag'])=='b':
                            sample_orientation_flag='b'
                    if sample_orientation_flag!='b':
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


          #---------------------
          # hierarchy is determined from magic_measurements.txt
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

          if 'this study' not in Data_hierarchy['study'].keys():
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



      print "-I- done sorting meas data"

      self.specimens=Data.keys()
#      self.specimens.sort(cmp=specimens_comparator)

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
        Data[s]['zdata']=array(zdata)
        Data[s]['zdata_geo']=array(zdata_geo)
        Data[s]['zdata_tilt']=array(zdata_tilt)

        #--------------------------------------------------------------
        # Rotate zijderveld plot
        #--------------------------------------------------------------

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

    def read_magic_file(self,path,sort_by_this_name): #BLARGE
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
            data_er_samples=self.read_magic_file(os.path.join(self.WD, "er_samples.txt"),'er_sample_name')
        except:
            self.GUI_log.write ("-W- Cant find er_sample.txt in project directory")

        try:
            data_er_sites=self.read_magic_file(os.path.join(self.WD, "er_sites.txt"),'er_site_name')
        except:
            self.GUI_log.write ("-W- Cant find er_sites.txt in project directory")

        try:
            data_er_locations=self.read_magic_file(os.path.join(self.WD, "er_locations.txt"), 'er_location_name')
        except:
            self.GUI_log.write ("-W- Cant find er_locations.txt in project directory")

        try:
            data_er_ages=self.read_magic_file(os.path.join(self.WD, "er_ages.txt"),'er_sample_name')
        except:
            try:
                data_er_ages=self.read_magic_file(os.path.join(self.WD, "er_ages.txt"),'er_site_name')
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

        pmag_specimens,pmag_samples,pmag_sites=[],[],[]
        try:
            pmag_specimens,file_type=pmag.magic_read(os.path.join(self.WD, "pmag_specimens.txt"))
        except:
            print "-I- Cant read pmag_specimens.txt"
        try:
            pmag_samples,file_type=pmag.magic_read(os.path.join(self.WD, "pmag_samples.txt"))
        except:
            print "-I- Cant read pmag_samples.txt"
        try:
            pmag_sites,file_type=pmag.magic_read(os.path.join(self.WD, "pmag_sites.txt"))
        except:
            print "-I- Cant read pmag_sites.txt"
        self.GUI_log.write ("-I- Reading previous interpretations from pmag* tables\n")
        #--------------------------
        # reads pmag_specimens.txt and
        # update pmag_results_data['specimens'][specimen] BLARGE
        # with the new interpretation
        #--------------------------

        self.pmag_results_data['specimens'] = {}
        for rec in pmag_specimens:
            if 'er_specimen_name' in rec:
                specimen=rec['er_specimen_name']
            else:
                continue

            #initialize list of interpretations
            if specimen in self.pmag_results_data['specimens'].keys():
                pass
            else:
                self.pmag_results_data['specimens'][specimen] = []

            self.s = specimen

            #if interpretation doesn't exsist create it.
            if 'specimen_comp_name' in rec.keys():
                if rec['specimen_comp_name'] not in map(lambda x: x.name, self.pmag_results_data['specimens'][specimen]):
                    next_fit = str(len(self.pmag_results_data['specimens'][self.s]) + 1)
                    color = self.colors[(int(next_fit)-1) % len(self.colors)]
                    self.pmag_results_data['specimens'][self.s].append(Fit(rec['specimen_comp_name'], None, None, color, self))
                    fit = self.pmag_results_data['specimens'][specimen][-1]
                else:
                    fit = None
            else:
                next_fit = str(len(self.pmag_results_data['specimens'][self.s]) + 1)
                color = self.colors[(int(next_fit)-1) % len(self.colors)]
                self.pmag_results_data['specimens'][self.s].append(Fit('Fit ' + next_fit, None, None, color, self))
                fit = self.pmag_results_data['specimens'][specimen][-1]


            if 'specimen_flag' in rec and rec['specimen_flag'] == 'b':
                self.bad_fits.append(fit)

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
                    tmin="%.1fmT"%(float(rec['measurement_step_min'])*1000.)

                if float(rec['measurement_step_max'])==0 or float(rec['measurement_step_max'])==273.:
                    tmax="0"
                elif float(rec['measurement_step_max'])>2: # thermal
                    tmax="%.0fC"%(float(rec['measurement_step_max'])-273.)
                else: # AF
                    tmax="%.1fmT"%(float(rec['measurement_step_max'])*1000.)

                if calculation_type !="":

                    if specimen in self.Data.keys() and 'zijdblock_steps' in self.Data[specimen]\
                    and tmin in self.Data[specimen]['zijdblock_steps']\
                    and tmax in self.Data[specimen]['zijdblock_steps']:

                        if fit:
                            fit.put(specimen,'specimen',self.get_PCA_parameters(specimen,tmin,tmax,'specimen',calculation_type))

                            if len(self.Data[specimen]['zijdblock_geo'])>0:
                                fit.put(specimen,'geographic',self.get_PCA_parameters(specimen,tmin,tmax,'geographic',calculation_type))

                            if len(self.Data[specimen]['zijdblock_tilt'])>0:
                                fit.put(specimen,'tilt-corrected',self.get_PCA_parameters(specimen,tmin,tmax,'tilt-corrected',calculation_type))

                    else:
                        self.GUI_log.write ( "-W- WARNING: Cant find specimen and steps of specimen %s tmin=%s, tmax=%s"%(specimen,tmin,tmax))

        #BUG FIX-almost replaced first sample with last due to above assignment to self.s
        if pmag_specimens:
            self.s = pmag_specimens[0]['er_specimen_name']
            self.specimens_box.SetSelection(0)
        if self.s in self.pmag_results_data['specimens'] and self.pmag_results_data['specimens'][self.s]:
            self.pmag_results_data['specimens'][self.s][-1].select()



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
                    for dirtype in self.dirtypes:
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
        """
        Create menu
        """
        self.menubar = wx.MenuBar()

        #------------------------------------------------------------------------------

        menu_file = wx.Menu()

        m_make_MagIC_results_tables= menu_file.Append(-1, "&Save MagIC pmag tables\tCtrl-Shift-S", "")
        self.Bind(wx.EVT_MENU, self.on_menu_make_MagIC_results_tables, m_make_MagIC_results_tables)

        submenu_save_plots = wx.Menu()

        m_save_zij_plot = submenu_save_plots.Append(-1, "&Save Zijderveld plot", "")
        self.Bind(wx.EVT_MENU, self.on_save_Zij_plot, m_save_zij_plot,"Zij")

        m_save_eq_plot = submenu_save_plots.Append(-1, "&Save specimen equal area plot", "")
        self.Bind(wx.EVT_MENU, self.on_save_Eq_plot, m_save_eq_plot,"specimen-Eq")

        m_save_M_t_plot = submenu_save_plots.Append(-1, "&Save M-t plot", "")
        self.Bind(wx.EVT_MENU, self.on_save_M_t_plot, m_save_M_t_plot,"M_t")

        m_save_high_level = submenu_save_plots.Append(-1, "&Save high level plot", "")
        self.Bind(wx.EVT_MENU, self.on_save_high_level, m_save_high_level,"Eq")

        m_save_all_plots = submenu_save_plots.Append(-1, "&Save all plots", "")
        self.Bind(wx.EVT_MENU, self.on_save_all_figures, m_save_all_plots)

        m_new_sub_plots = menu_file.AppendMenu(-1, "&Save plot", submenu_save_plots)

        menu_file.AppendSeparator()
        m_exit = menu_file.Append(-1, "E&xit\tCtrl-Q", "Exit")
        self.Bind(wx.EVT_MENU, self.on_menu_exit, m_exit)
        #-------------------------------------------------------------------------------

        menu_Analysis = wx.Menu()

        submenu_criteria = wx.Menu()

        m_change_criteria_file = submenu_criteria.Append(-1, "&Change acceptance criteria", "")
        self.Bind(wx.EVT_MENU, self.on_menu_change_criteria, m_change_criteria_file)

        m_import_criteria_file =  submenu_criteria.Append(-1, "&Import criteria file", "")
        self.Bind(wx.EVT_MENU, self.on_menu_criteria_file, m_import_criteria_file)

        m_new_sub = menu_Analysis.AppendMenu(-1, "Acceptance criteria", submenu_criteria)

        m_previous_interpretation = menu_Analysis.Append(-1, "&Import previous interpretation from a redo file\tCtrl-R", "")
        self.Bind(wx.EVT_MENU, self.on_menu_previous_interpretation, m_previous_interpretation)

        m_save_interpretation = menu_Analysis.Append(-1, "&Save current interpretations to a redo file\tCtrl-S", "")
        self.Bind(wx.EVT_MENU, self.on_menu_save_interpretation, m_save_interpretation)

        #m_delete_interpretation = menu_Analysis.Append(-1, "&Clear all current interpretations\tCtrl-Shift-D", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_clear_interpretation, m_delete_interpretation)

        #-----------------

        menu_Tools = wx.Menu()

        #m_bulk_demagnetization = menu_Tools.Append(-1, "&Bulk demagnetization\tCtrl-B", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_bulk_demagnetization, m_bulk_demagnetization)

        #m_auto_interpret = menu_Tools.Append(-1, "&Auto interpret (alpha version)\tCtrl-A", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_autointerpret, m_auto_interpret)

        m_edit_interpretations = menu_Tools.Append(-1, "&Interpretation editor\tCtrl-E", "")
        self.Bind(wx.EVT_MENU, self.on_menu_edit_interpretations, m_edit_interpretations)

        #-------------------

        #menu_Plot= wx.Menu()
        #m_plot_data = menu_Plot.Append(-1, "&Plot ...", "")
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

#        menu_MagIC= wx.Menu()
#        m_convert_to_magic= menu_MagIC.Append(-1, "&Convert generic files to MagIC format", "")
#        self.Bind(wx.EVT_MENU, self.on_menu_generic_to_magic, m_convert_to_magic)
#        m_samples_orientation= menu_MagIC.Append(-1, "&Sample orientation", "")
#        self.Bind(wx.EVT_MENU, self.on_menu_samples_orientation, m_samples_orientation)
#
#        m_build_magic_model= menu_MagIC.Append(-1, "&Run MagIC model builder", "")
#        self.Bind(wx.EVT_MENU, self.on_menu_MagIC_model_builder, m_build_magic_model)
#        m_make_MagIC_results_tables= menu_MagIC.Append(-1, "&Save MagIC results tables", "")
#        self.Bind(wx.EVT_MENU, self.on_menu_make_MagIC_results_tables, m_make_MagIC_results_tables)

        #-----------------
        # Help Menu
        #-----------------

        menu_Help = wx.Menu()

        m_cookbook = menu_Help.Append(-1, "&PmagPy Cookbook\tCtrl-Shift-H", "")
        self.Bind(wx.EVT_MENU, self.on_menu_cookbook, m_cookbook)

        m_docs = menu_Help.Append(-1, "&Usage and Tips\tCtrl-H", "")
        self.Bind(wx.EVT_MENU, self.on_menu_docs, m_docs)

        m_git = menu_Help.Append(-1, "&Github Page\tCtrl-Shift-G", "")
        self.Bind(wx.EVT_MENU, self.on_menu_git, m_git)

        #-----------------
        # Edit Menu
        #-----------------

        menu_edit = wx.Menu()

        m_new = menu_edit.Append(-1, "&New interpretation\tCtrl-N", "")
        self.Bind(wx.EVT_MENU, self.add_fit, m_new)

        m_delete = menu_edit.Append(-1, "&Delete interpretation\tCtrl-D", "")
        self.Bind(wx.EVT_MENU, self.delete_fit, m_delete)

        m_next_interp = menu_edit.Append(-1, "&Next interpretation\tCtrl-Up", "")
        self.Bind(wx.EVT_MENU, self.on_menu_next_interp, m_next_interp)

        m_previous_interp = menu_edit.Append(-1, "&Previous interpretation\tCtrl-Down", "")
        self.Bind(wx.EVT_MENU, self.on_menu_prev_interp, m_previous_interp)

        m_next_specimen = menu_edit.Append(-1, "&Next Specimen\tCtrl-Right", "")
        self.Bind(wx.EVT_MENU, self.on_next_button, m_next_specimen)

        m_previous_specimen = menu_edit.Append(-1, "&Previous Specimen\tCtrl-Left", "")
        self.Bind(wx.EVT_MENU, self.on_prev_button, m_previous_specimen)

#        m_next_sample = menu_edit.Append(-1, "&Next Sample\tCtrl-PageUp", "")
#        self.Bind(wx.EVT_MENU, self.on_menu_next_sample, m_next_sample)

#        m_previous_sample = menu_edit.Append(-1, "&Previous Sample\tCtrl-PageDown", "")
#        self.Bind(wx.EVT_MENU, self.on_menu_prev_sample, m_previous_sample)

        menu_coordinates = wx.Menu()

        m_speci = menu_coordinates.Append(-1, "&Specimen Coordinates\tCtrl-P", "")
        self.Bind(wx.EVT_MENU, self.on_menu_change_speci_coord, m_speci)
        if "geographic" in self.coordinate_list:
            m_geo = menu_coordinates.Append(-1, "&Geographic Coordinates\tCtrl-G", "")
            self.Bind(wx.EVT_MENU, self.on_menu_change_geo_coord, m_geo)
        if "tilt-corrected" in self.coordinate_list:
            m_tilt = menu_coordinates.Append(-1, "&Tilt-Corrected Coordinates\tCtrl-T", "")
            self.Bind(wx.EVT_MENU, self.on_menu_change_tilt_coord, m_tilt)

        m_coords = menu_edit.AppendMenu(-1, "&Coordinate Systems", menu_coordinates)

        #-----------------

        #self.menubar.Append(menu_preferences, "& Preferences")
        self.menubar.Append(menu_file, "&File")
        self.menubar.Append(menu_edit, "&Edit")
        self.menubar.Append(menu_Analysis, "&Analysis")
        self.menubar.Append(menu_Tools, "&Tools")
        self.menubar.Append(menu_Help, "&Help")
        #self.menubar.Append(menu_Plot, "&Plot")
        #self.menubar.Append(menu_results_table, "&Table")
        #self.menubar.Append(menu_MagIC, "&MagIC")
        self.SetMenuBar(self.menubar)

    #============================================

    def reset(self):
        '''
        reset the GUI like restarting it (almost same as __init__)
        '''
        #global FIRST_RUN
        FIRST_RUN=False
        self.currentDirectory = os.getcwd() # get the current working directory
        self.get_DIR()        # choose directory dialog

        #preferences=self.get_preferences()
        #self.dpi = 100
        #self.preferences={}
        #self.preferences=preferences

        self.COORDINATE_SYSTEM='specimen'
        self.Data_info=self.get_data_info() # Read  er_* data
        self.Data,self.Data_hierarchy=self.get_data() # Get data from magic_measurements and rmag_anistropy if exist.

        self.pmag_results_data={}
        for level in ['specimens','samples','sites','lcoations','study']:
            self.pmag_results_data[level]={}
        self.high_level_means={}

        high_level_means={}
        for high_level in ['samples','sites','locations','study']:
            if high_level not in self.high_level_means.keys():
                self.high_level_means[high_level]={}


        self.Data_samples={}
        self.last_saved_pars={}
        self.specimens=self.Data.keys()         # get list of specimens
        self.specimens.sort(cmp=specimens_comparator) # get list of specimens
        if len(self.specimens)>0:
            self.s=str(self.specimens[0])
        else:
            self.s=""
        for fit in self.pmag_results_data['specimens'][self.s]:
            fit.pars={}
        self.samples=self.Data_hierarchy['samples'].keys()         # get list of samples
        self.samples.sort()                   # get list of specimens
        self.sites=self.Data_hierarchy['sites'].keys()         # get list of sites
        self.sites.sort()                   # get list of sites
        self.locations=self.Data_hierarchy['locations'].keys()         # get list of sites
        self.locations.sort()                   # get list of sites

        #----------------------------------------------------------------------
        # initialize first specimen in list as current specimen
        #----------------------------------------------------------------------
        try:
            self.s=str(self.specimens[0])
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

        #self.get_previous_interpretation() # get interpretations from pmag_specimens.txt

        self.specimens_box.SetItems(self.specimens)
        self.specimens_box.SetStringSelection(str(self.s))
        self.update_pmag_tables()
        # Draw figures and add  text
        try:
            self.update_selection()
        except:
            pass

        FIRST_RUN=False

    #--------------------------------------------------------------
    # File menu
    #--------------------------------------------------------------

    def on_menu_exit(self, event):

        #check if interpretations have changed and were not saved
        write_session_to_failsafe = False
        try:
            number_saved_fits = sum(1 for line in open("demag_gui.redo"))
            number_current_fits = sum(len(self.pmag_results_data['specimens'][specimen]) for specimen in self.pmag_results_data['specimens'].keys())
            #break if there are no fits there's no need to save an empty file
            if number_current_fits == 0: raise RuntimeError("get out and don't write")
            write_session_to_failsafe = (number_saved_fits != number_current_fits)
            default_redo = open("demag_gui.redo")
            i,specimen = 0,None
            for line in default_redo:
                if line == None:
                    write_session_to_failsafe = True
                vals = line.strip("\n").split("\t")
                if vals[0] != specimen:
                    i = 0
                specimen = vals[0]
                tmin,tmax = self.parse_bound_data(vals[2],vals[3],specimen)
                if specimen in self.pmag_results_data['specimens']:
                    fit = self.pmag_results_data['specimens'][specimen][i]
                if write_session_to_failsafe:
                    break
                write_session_to_failsafe = ((specimen not in self.specimens) or \
                                             (tmin != fit.tmin or tmax != fit.tmax) or \
                                             (vals[4] != fit.name))
                i += 1
        except IOError: write_session_to_failsafe = True
        except IndexError: write_session_to_failsafe = True
        except RuntimeError: write_session_to_failsafe = False

        if write_session_to_failsafe:
            self.on_menu_save_interpretation(event,"demag_last_session.redo")

        if self.close_warning:
            TEXT="Data is not saved to a file yet!\nTo properly save your data:\n1) Analysis --> Save current interpretations to a redo file.\nor\n1) File --> Save MagIC pmag tables.\n\n Press OK to exit without saving."

            #Save all interpretation to a 'redo' file or to MagIC specimens result table\n\nPress OK to exit"
            dlg1 = wx.MessageDialog(None,caption="Warning:", message=TEXT ,style=wx.OK|wx.CANCEL|wx.ICON_EXCLAMATION)
            if dlg1.ShowModal() == wx.ID_OK:
                dlg1.Destroy()
                if self.interpretation_editor_open:
                    self.interpretation_editor.on_close_edit_window(event)
                self.Destroy()
                #sys.exit()
        else:
            if self.interpretation_editor_open:
                self.interpretation_editor.on_close_edit_window(event)
            self.Destroy()
            #sys.exit()

#        dlg1 = wx.MessageDialog(None,caption="Warning:", message="Exiting program.\nSave all interpretation to a 'redo' file or to MagIC specimens result table\n\nPress OK to exit" ,style=wx.OK|wx.CANCEL|wx.ICON_INFORMATION)
#        if dlg1.ShowModal() == wx.ID_OK:
#            dlg1.Destroy()
#            self.Destroy()
#            exit()
#
    def on_save_Zij_plot(self, event):
        self.current_fit = None
        self.draw_interpretation()
        self.plot_higher_levels_data()
        self.fig1.text(0.9,0.98,'%s'%(self.s),{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'right' })
        SaveMyPlot(self.fig1,self.s,"Zij",self.WD)
#        self.fig1.clear()
        self.draw_figure(self.s)
        self.update_selection()

    def on_save_Eq_plot(self, event):
        self.current_fit = None
        self.draw_interpretation()
        self.plot_higher_levels_data()
        #self.fig2.text(0.9,0.96,'%s'%(self.s),{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'right' })
        #self.canvas4.print_figure("./tmp.pdf")#, dpi=self.dpi)
        SaveMyPlot(self.fig2,self.s,"EqArea",self.WD)
#        self.fig2.clear()
        self.draw_figure(self.s)
        self.update_selection()

    def on_save_M_t_plot(self, event):
        self.current_fit = None
        self.draw_interpretation()
        self.plot_higher_levels_data()
        self.fig3.text(0.9,0.96,'%s'%(self.s),{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'right' })
        SaveMyPlot(self.fig3,self.s,"M_M0",self.WD)
#        self.fig3.clear()
        self.draw_figure(self.s)
        self.update_selection()

    def on_save_high_level(self, event):
        self.current_fit = None
        self.draw_interpretation()
        self.plot_higher_levels_data()
        SaveMyPlot(self.fig4,str(self.level_names.GetValue()),str(self.level_box.GetValue()), self.WD )
#        self.fig4.clear()
        self.draw_figure(self.s)
        self.update_selection()
        self.plot_higher_levels_data()

    def on_save_all_figures(self, event):
        temp_fit = self.current_fit
        self.current_fit = None
        self.draw_interpretation()
        self.plot_higher_levels_data()
        dialog = wx.DirDialog(None, "choose a folder:",defaultPath = self.WD ,style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON | wx.DD_CHANGE_DIR)
        if dialog.ShowModal() == wx.ID_OK:
              dir_path=dialog.GetPath()
              dialog.Destroy()

        #figs=[self.fig1,self.fig2,self.fig3,self.fig4]
        plot_types=["Zij","EqArea","M_M0",str(self.level_box.GetValue())]
        #elements=[self.s,self.s,self.s,str(self.level_names.GetValue())]
        for i in range(4):
            try:
                if plot_types[i]=="Zij":
                    self.fig1.text(0.9,0.98,'%s'%(self.s),{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'right' })
                    SaveMyPlot(self.fig1,self.s,"Zij",dir_path)
                if plot_types[i]=="EqArea":
                    SaveMyPlot(self.fig2,self.s,"EqArea",dir_path)
                if plot_types[i]=="M_M0":
                    self.fig3.text(0.9,0.96,'%s'%(self.s),{'family':'Arial', 'fontsize':10, 'style':'normal','va':'center', 'ha':'right' })
                    SaveMyPlot(self.fig3,self.s,"M_M0",dir_path)
                if plot_types[i]==str(self.level_box.GetValue()):
                    SaveMyPlot(self.fig4,str(self.level_names.GetValue()),str(self.level_box.GetValue()),dir_path )
            except:
                pass

        self.fig1.clear()
        self.fig3.clear()
        self.draw_figure(self.s)
        self.update_selection()

    def on_menu_change_working_directory(self, event):
        self.reset()

    #--------------------------------------------------------------
    # Edit menu Bar functions
    #--------------------------------------------------------------

    def on_menu_change_speci_coord(self, event):
        if self.COORDINATE_SYSTEM != "specimen":
            self.coordinates_box.SetStringSelection("specimen")
            self.onSelect_coordinates(event)

    def on_menu_change_geo_coord(self, event):
        if self.COORDINATE_SYSTEM != "geographic":
            self.coordinates_box.SetStringSelection("geographic")
            self.onSelect_coordinates(event)

    def on_menu_change_tilt_coord(self, event):
        if self.COORDINATE_SYSTEM != "tilt-corrected":
            self.coordinates_box.SetStringSelection("tilt-corrected")
            self.onSelect_coordinates(event)

    def on_menu_next_interp(self, event):
        f_index = self.fit_box.GetSelection()
        if f_index <= 0:
            f_index = self.fit_box.GetCount()-1
        else:
            f_index -= 1
        self.fit_box.SetSelection(f_index)
        self.on_select_fit(event)

    def on_menu_prev_interp(self, event):
        f_index = self.fit_box.GetSelection()
        if f_index >= len(self.pmag_results_data['specimens'][self.s])-1:
             f_index = 0
        else:
            f_index += 1
        self.fit_box.SetSelection(f_index)
        self.on_select_fit(event)

    def on_menu_next_sample(self, event):
        s_index = self.specimens.index(self.s)
        print(s_index)

    def on_menu_prev_sample(self, event):
        s_index = self.specimens.index(self.s)
        print(s_index)

    #--------------------------------------------------------------
    # Analysis menu Bar functions
    #--------------------------------------------------------------

    def on_menu_edit_interpretations(self,event):
        if not self.interpretation_editor_open:
            self.interpretation_editor = EditFitFrame(self)
            self.interpretation_editor_open = True
            self.update_higher_level_stats()
            self.interpretation_editor.Center()
            self.interpretation_editor.Show(True)
            if self.parent==None and sys.platform.startswith('darwin'):
                TEXT="This is a refresher window for mac os to insure that wx opens the new window"
                dlg = wx.MessageDialog(self, caption="Open",message=TEXT,style=wx.OK | wx.ICON_INFORMATION | wx.STAY_ON_TOP )
                dlg.ShowModal()
                dlg.Destroy()
        else:
            self.interpretation_editor.ToggleWindowStyle(wx.STAY_ON_TOP)
            self.interpretation_editor.ToggleWindowStyle(wx.STAY_ON_TOP)

    def on_menu_previous_interpretation(self,event):
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
            defaultDir=self.WD,
            defaultFile="demag_gui.redo",
            wildcard="*.redo",
            style=wx.OPEN | wx.CHANGE_DIR
            )
        if dlg.ShowModal() == wx.ID_OK:
            redo_file = dlg.GetPath()
        else:
            redo_file = None
        dlg.Destroy()

        if redo_file:
            self.read_redo_file(redo_file)


    #----------------------------------------------------------------------

    def clear_interpretations(self):

        for specimen in self.pmag_results_data['specimens'].keys():
            del(self.pmag_results_data['specimens'][specimen])
            for high_level_type in ['samples','sites','locations','study']:
                self.high_level_means[high_level_type]={}
        if self.interpretation_editor_open:
            self.interpretation_editor.update_editor(True)

    #----------------------------------------------------------------------

    def read_redo_file(self,redo_file): #BLARGE
        """
        Read previous interpretation from a redo file
        and update gui with the new interpretation
        """
        self.clear_interpretations()
        self.GUI_log.write ("-I- read redo file and processing new bounds")
        fin=open(redo_file,'rU')

        for Line in fin.readlines():
            line=Line.strip('\n').split('\t')
            specimen=line[0]
            self.s = specimen
            if not (self.s in self.pmag_results_data['specimens'].keys()):
                self.pmag_results_data['specimens'][self.s] = []

            tmin,tmax="",""

            calculation_type=line[1]
            tmin,tmax = self.parse_bound_data(line[2],line[3],specimen)
            if tmin == None or tmax == None:
                continue
            if tmin not in self.Data[specimen]['zijdblock_steps'] or  tmax not in self.Data[specimen]['zijdblock_steps']:
                print "-E- ERROR in redo file specimen %s. Cant find treatment steps"%specimen

            if len(line) >= 6:
                fit_index = -1
                if specimen in self.pmag_results_data['specimens']:
                    bool_list = map(lambda x: x.has_values(line[4], tmin, tmax), self.pmag_results_data['specimens'][specimen])
                else:
                    bool_list = [False]
                if any(bool_list):
                    fit_index = bool_list.index(True)
                else:
                    next_fit = str(len(self.pmag_results_data['specimens'][self.s]) + 1)
                    try: color = line[5]
                    except IndexError: color = self.colors[(int(next_fit)-1) % len(self.colors)]
                    if ',' in color:
                        color = map(float,color.strip('( ) [ ]').split(','))
                    self.pmag_results_data['specimens'][self.s].append(Fit('Fit ' + next_fit, None, None, color, self))
                fit = self.pmag_results_data['specimens'][specimen][fit_index];
                fit.name = line[4]
                try:
                    if line[6] == "b":
                        self.bad_fits.append(fit)
                except IndexError: pass
            else:
                next_fit = str(len(self.pmag_results_data['specimens'][self.s]) + 1)
                self.pmag_results_data['specimens'][self.s].append(Fit('Fit ' + next_fit, None, None, self.colors[(int(next_fit)-1) % len(self.colors)], self))
                fit = self.pmag_results_data['specimens'][specimen][-1]

            fit.put(self.s,self.COORDINATE_SYSTEM,self.get_PCA_parameters(specimen,tmin,tmax,self.COORDINATE_SYSTEM,calculation_type))

        fin.close()
        self.s=str(self.specimens_box.GetValue())
        if (self.s not in self.pmag_results_data['specimens']) or (not self.pmag_results_data['specimens'][self.s]):
            self.current_fit = None
        else:
            self.current_fit = self.pmag_results_data['specimens'][self.s][-1]
        self.calculate_higher_levels_data()
        if self.interpretation_editor_open:
            self.interpretation_editor.update_editor()
        self.update_selection()


    #----------------------------------------------------------------------

    def parse_bound_data(self,tmin0,tmax0,specimen):
        """converts Kelvin/Tesla temperature/AF data from the MagIC/Redo format to that
           of Celsius/milliTesla which is used by the GUI as it is often more intuitive
           @param tmin0 -> the input temperature/AF lower bound value to convert
           @param tmax0 -> the input temperature/AF upper bound value to convert
           @param specimen -> the specimen these bounds are for
           @return tmin -> the converted lower bound temperature/AF or None if input
                           format was wrong
           @return tmax -> the converted upper bound temperature/AF or None if the input
                           format was wrong
        """
        if self.Data[specimen]['measurement_step_unit']=="C":
            if float(tmin0)==0 or float(tmin0)==273:
                tmin="0"
            else:
                tmin="%.0fC"%(float(tmin0)-273)
            if float(tmax0)==0 or float(tmax0)==273:
                tmax="0"
            else:
                tmax="%.0fC"%(float(tmax0)-273)
        elif self.Data[specimen]['measurement_step_unit']=="mT":
            if float(tmin0)==0:
                tmin="0"
            else:
                tmin="%.1fmT"%(float(tmin0)*1000)
            if float(tmax0)==0:
                tmax="0"
            else:
                tmax="%.1fmT"%(float(tmax0)*1000)
        else: # combimned experiment T:AF
            if float(tmin0)==0:
                tmin="0"
            elif "%.0fC"%(float(tmin0)-273) in self.Data[specimen]['zijdblock_steps']:
                tmin="%.0fC"%(float(tmin0)-273)
            elif "%.1fmT"%(float(tmin0)*1000) in self.Data[specimen]['zijdblock_steps']:
                tmin="%.1fmT"%(float(tmin0)*1000)
            else:
                tmin=None
            if float(tmax0)==0:
                tmax="0"
            elif "%.0fC"%(float(tmax0)-273) in self.Data[specimen]['zijdblock_steps']:
                tmax="%.0fC"%(float(tmax0)-273)
            elif "%.1fmT"%(float(tmax0)*1000) in self.Data[specimen]['zijdblock_steps']:
                tmax="%.1fmT"%(float(tmax0)*1000)
            else:
                tmax=None
        return tmin,tmax

    #----------------------------------------------------------------------

    def on_menu_save_interpretation(self,event,redo_file_name = "demag_gui.redo"):
        fout=open(redo_file_name,'w')
        specimens_list=self.pmag_results_data['specimens'].keys()
        specimens_list.sort()
        for specimen in specimens_list:
            for fit in self.pmag_results_data['specimens'][specimen]:
                if fit.tmin==None or fit.tmax==None:
                    continue
                if type(fit.tmin)!=str or type(fit.tmax)!=str:
                    print(type(fit.tmin),fit.tmin,type(fit.tmax),fit.tmax)
                STRING=specimen+"\t"
                STRING=STRING+fit.PCA_type+"\t"
                fit_flag = "g"
                if "C" in fit.tmin:
                    tmin="%.0f"%(float(fit.tmin.strip("C"))+273.)
                elif "mT" in fit.tmin:
                    tmin="%.2e"%(float(fit.tmin.strip("mT"))/1000)
                else:
                    tmin="0"
                if "C" in fit.tmax:
                    tmax="%.0f"%(float(fit.tmax.strip("C"))+273.)
                elif "mT" in fit.tmax:
                    tmax="%.2e"%(float(fit.tmax.strip("mT"))/1000)
                else:
                    tmax="0"
                if fit in self.bad_fits:
                    fit_flag = "b"

                STRING=STRING+tmin+"\t"+tmax+"\t"+fit.name+"\t"+str(fit.color)+"\t"+fit_flag+"\n"
                fout.write(STRING)
        TEXT="specimens interpretations are saved in " + redo_file_name
        dlg = wx.MessageDialog(self, caption="Saved",message=TEXT,style=wx.OK|wx.CANCEL )
        result = dlg.ShowModal()
        if result == wx.ID_OK:
            dlg.Destroy()

     #----------------------------------------------------------------------

    def on_menu_clear_interpretation(self,event):
        self.clear_interpretations()
        self.s=str(self.specimens_box.GetValue())
        self.update_selection()


    #----------------------------------------------------------------------

    def on_menu_change_criteria(self, event):
        dia=demag_dialogs.demag_criteria_dialog(None,self.acceptance_criteria,title='PmagPy Demag Gui Acceptance Criteria')
        dia.Center()
        if dia.ShowModal() == wx.ID_OK: # Until the user clicks OK, show the message
            self.on_close_criteria_box(dia)

    def on_close_criteria_box (self,dia):

        window_list_specimens=['specimen_n','specimen_mad','specimen_dang','specimen_alpha95']
        window_list_samples=['sample_n','sample_n_lines','sample_n_planes','sample_k','sample_r','sample_alpha95']
        window_list_sites=['site_n','site_n_lines','site_n_planes','site_k','site_r','site_alpha95']
        demag_gui_supported_criteria= window_list_specimens+ window_list_samples+window_list_sites

        for crit in demag_gui_supported_criteria:
            command="new_value=dia.set_%s.GetValue()"%(crit)
            exec command
            # empty box
            if new_value=="":
                self.acceptance_criteria[crit]['value']=-999
                continue
            # box with no valid number
            try:
                float(new_value)
            except:
                self.show_crit_window_err_messege(crit)
                continue
            self.acceptance_criteria[crit]['value']=float(new_value)

        #  message dialog
        dlg1 = wx.MessageDialog(self,caption="Warning:", message="Canges are saved to pmag_criteria.txt\n " ,style=wx.OK)
        result = dlg1.ShowModal()
        if result == wx.ID_OK:
            self.write_acceptance_criteria_to_file()
            dlg1.Destroy()
            dia.Destroy()
        #self.recaclulate_satistics()

    # only valid naumber can be entered to boxes
    def show_crit_window_err_messege(self,crit):
        '''
        error message if a valid naumber is not entered to criteria dialog boxes
        '''
        dlg1 = wx.MessageDialog(self,caption="Error:",message="not a vaild value for statistic %s\n ignoring value"%crit ,style=wx.OK)
        result = dlg1.ShowModal()
        if result == wx.ID_OK:
            dlg1.Destroy()

    def write_acceptance_criteria_to_file(self):
        crit_list=self.acceptance_criteria.keys()
        crit_list.sort()
        rec={}
        rec['pmag_criteria_code']="ACCEPT"
        #rec['criteria_definition']=""
        rec['criteria_definition']="acceptance criteria for study"
        rec['er_citation_names']="This study"

        for crit in crit_list:
            if type(self.acceptance_criteria[crit]['value'])==str:
                if self.acceptance_criteria[crit]['value'] != "-999" and self.acceptance_criteria[crit]['value'] != "":
                    rec[crit]=self.acceptance_criteria[crit]['value']
            elif type(self.acceptance_criteria[crit]['value'])==int:
                if self.acceptance_criteria[crit]['value'] !=-999:
                    rec[crit]="%.i"%(self.acceptance_criteria[crit]['value'])
            elif type(self.acceptance_criteria[crit]['value'])==float:
                if float(self.acceptance_criteria[crit]['value'])==-999:
                    continue
                decimal_points=self.acceptance_criteria[crit]['decimal_points']
                if decimal_points != -999:
                    command="rec[crit]='%%.%sf'%%(self.acceptance_criteria[crit]['value'])"%(decimal_points)
                    exec command
                else:
                    rec[crit]="%e"%(self.acceptance_criteria[crit]['value'])
        pmag.magic_write(os.path.join(self.WD, "pmag_criteria.txt"),[rec],"pmag_criteria")


    #--------------------------------------------------------------

    def on_menu_criteria_file (self, event):
        """
        read pmag_criteria.txt file
        and open changecriteria dialog
        """
        read_sucsess=False
        dlg = wx.FileDialog(
            self, message="choose pmag criteria file",
            defaultDir=self.WD,
            defaultFile="pmag_criteria.txt",
            style=wx.OPEN | wx.CHANGE_DIR
            )
        if dlg.ShowModal() == wx.ID_OK:
            criteria_file = dlg.GetPath()
            self.GUI_log.write ("-I- Read new criteria file: %s\n"%criteria_file)

            # check if this is a valid pmag_criteria file
            try:
                mag_meas_data,file_type=pmag.magic_read(criteria_file)
            except:
                dlg1 = wx.MessageDialog(self, caption="Error",message="not a valid pmag_criteria file",style=wx.OK)
                result = dlg1.ShowModal()
                if result == wx.ID_OK:
                    dlg1.Destroy()
                dlg.Destroy()
                return

            # initialize criteria
            self.acceptance_criteria=pmag.initialize_acceptance_criteria()
            self.acceptance_criteria=pmag.read_criteria_from_file(criteria_file,self.acceptance_criteria)
            read_sucsess=True

        dlg.Destroy()
        if read_sucsess:
            self.on_menu_change_criteria(None)

    #--------------------------------------------------------------
    # Tools menu
    #--------------------------------------------------------------


    def on_menu_bulk_demagnetization (self,event):

        dlg1 = wx.MessageDialog(self, caption="message",message="tool not supported in this beta version",style=wx.OK)
        result = dlg1.ShowModal()
        if result == wx.ID_OK:
            dlg1.Destroy()

    #--------------------------------------------------------------
    # MagIC menu
    #--------------------------------------------------------------

    def on_menu_make_MagIC_results_tables(self,event): #BLARGE
        """
         1. read pmag_specimens.txt, pmag_samples.txt, pmag_sites.txt, and sort out lines with LP-DIR in magic_codes
         2. saves a clean pmag_*.txt files without LP-DIR stuff as pmag_*.txt.tmp .
         3. write a new file pmag_specimens.txt
         4. merge pmag_specimens.txt and pmag_specimens.txt.tmp using combine_magic.py
         5. delete pmag_specimens.txt.tmp
         6 (optional) extracting new pag_*.txt files (except pmag_specimens.txt) using specimens_results_magic.py
         7: if #6: merge pmag_*.txt and pmag_*.txt.tmp using combine_magic.py
            if not #6: save pmag_*.txt.tmp as pmag_*.txt
        """


        #---------------------------------------
        # save pmag_*.txt.tmp without directional data
        #---------------------------------------
        self.on_menu_save_interpretation(None)

        #---------------------------------------
        # dialog box to choose coordinate systems for pmag_specimens.txt
        #---------------------------------------
        dia = demag_dialogs.magic_pmag_specimens_table_dialog(None)
        dia.Center()

        CoorTypes=['DA-DIR','DA-DIR-GEO','DA-DIR-TILT']
        if dia.ShowModal() == wx.ID_OK: # Until the user clicks OK, show the message
            CoorTypes=[]
            if dia.cb_spec_coor.GetValue()==True:
                CoorTypes.append('DA-DIR')
            if dia.cb_geo_coor.GetValue()==True:
                CoorTypes.append('DA-DIR-GEO')
            if dia.cb_tilt_coor.GetValue()==True:
                CoorTypes.append('DA-DIR-TILT')
        #------------------------------


        self.PmagRecsOld={}
        for FILE in ['pmag_specimens.txt']:
            self.PmagRecsOld[FILE]=[]
            meas_data=[]
            try:
                meas_data,file_type=pmag.magic_read(os.path.join(self.WD, FILE))
                self.GUI_log.write("-I- Read old magic file  %s\n"%os.path.join(self.WD, FILE))
                #if FILE !='pmag_specimens.txt':
                os.remove(os.path.join(self.WD,FILE))
                self.GUI_log.write("-I- Delete old magic file  %s\n"%os.path.join(self.WD,FILE))

            except:
                continue

            for rec in meas_data:
                if "magic_method_codes" in rec.keys():
                    if "LP-DIR" not in rec['magic_method_codes'] and "DE-" not in  rec['magic_method_codes']:
                        self.PmagRecsOld[FILE].append(rec)

        #---------------------------------------
        # write a new pmag_specimens.txt
        #---------------------------------------

        specimens_list=self.pmag_results_data['specimens'].keys()
        specimens_list.sort()
        PmagSpecs=[]
        for specimen in specimens_list:
            for dirtype in CoorTypes:
                i = 0
                for fit in self.pmag_results_data['specimens'][specimen]:

                    mpars = fit.get(dirtype)
                    if not mpars:
                        mpars = self.get_PCA_parameters(specimen,fit.tmin,fit.tmax,dirtype,fit.PCA_type)
                        if not mpars: continue

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
                    PmagSpecRec["er_citation_names"]="This study"
                    PmagSpecRec["magic_experiment_names"]=self.Data[specimen]["magic_experiment_name"]
                    if 'magic_instrument_codes' in self.Data[specimen].keys():
                        PmagSpecRec["magic_instrument_codes"]= self.Data[specimen]['magic_instrument_codes']
                    PmagSpecRec['specimen_correction']='u'
                    PmagSpecRec['specimen_direction_type'] = mpars["specimen_direction_type"]
                    PmagSpecRec['specimen_dec'] = "%.1f"%mpars["specimen_dec"]
                    PmagSpecRec['specimen_inc'] = "%.1f"%mpars["specimen_inc"]
                    PmagSpecRec['specimen_flag'] = "g"
                    if fit in self.bad_fits:
                        PmagSpecRec['specimen_flag'] = "b"

                    #magic_ood_codes=[]
                    #all_methods=self.Data[specimen]['magic_method_codes'].strip('\n').replace(" ","").split(":")
                    #for method in all_methods:
                    #    if "LP" in method:
                    #        magic_method_codes.append(method)
                    #if
                    #-------
                    #if self.Data[specimen]['measurement_step_unit']=="C":
                    #     PmagSpecRec['measurement_step_unit']="K"
                    #else:
                    #     PmagSpecRec['measurement_step_unit']="T"

                    if  fit.tmin =="0":
                         PmagSpecRec['measurement_step_min'] ="0"
                    elif "C" in fit.tmin:
                        PmagSpecRec['measurement_step_min'] = "%.0f"%(mpars["measurement_step_min"]+273.)
                    else:
                        PmagSpecRec['measurement_step_min'] = "%8.3e"%(mpars["measurement_step_min"]*1e-3)

                    if  fit.tmax =="0":
                         PmagSpecRec['measurement_step_max'] ="0"
                    elif "C" in fit.tmax:
                        PmagSpecRec['measurement_step_max'] = "%.0f"%(mpars["measurement_step_max"]+273.)
                    else:
                        PmagSpecRec['measurement_step_max'] = "%8.3e"%(mpars["measurement_step_max"]*1e-3)
                    if "C" in   fit.tmin  or "C" in fit.tmax:
                        PmagSpecRec['measurement_step_unit']="K"
                    else:
                        PmagSpecRec['measurement_step_unit']="T"
                    PmagSpecRec['specimen_n'] = "%.0f"%mpars["specimen_n"]
                    calculation_type=mpars['calculation_type']
                    PmagSpecRec["magic_method_codes"]=self.Data[specimen]['magic_method_codes']+":"+calculation_type+":"+dirtype
                    PmagSpecRec["specimen_comp_n"] = str(len(self.pmag_results_data["specimens"][specimen]))
                    PmagSpecRec["specimen_comp_name"] = fit.name
                    if fit in self.bad_fits:
                        PmagSpecRec["specimen_flag"] = "b"
                    else:
                        PmagSpecRec["specimen_flag"] = "g"
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
                    i += 1

        # add the 'old' lines with no "LP-DIR" in
        for rec in self.PmagRecsOld['pmag_specimens.txt']:
            PmagSpecs.append(rec)
        PmagSpecs_fixed=self.merge_pmag_recs(PmagSpecs)
        pmag.magic_write(os.path.join(self.WD, "pmag_specimens.txt"),PmagSpecs_fixed,'pmag_specimens')
        self.GUI_log.write( "specimen data stored in %s\n"%os.path.join(self.WD, "pmag_specimens.txt"))

        TEXT="specimens interpretations are saved in pmag_specimens.txt.\nPress OK for pmag_samples/pmag_sites/pmag_results tables."
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

#        run_script_flags=["specimens_results_magic.py","-fsp","pmag_specimens.txt", "-xI",  "-WD", str(self.WD)]
        if dia.cb_acceptance_criteria.GetValue()==True:
#            run_script_flags.append("-exc")
            use_criteria='existing'
        else:
#            run_script_flags.append("-C")
            use_criteria='none'

        #-- coordinate system
        if dia.rb_spec_coor.GetValue()==True:
#            run_script_flags.append("-crd");  run_script_flags.append("s")
            coord = "s"
        if dia.rb_geo_coor.GetValue()==True:
#            run_script_flags.append("-crd");  run_script_flags.append("g")
            coord = "g"
        if dia.rb_tilt_coor.GetValue()==True:
#            run_script_flags.append("-crd");  run_script_flags.append("t")
            coord = "t"
        if dia.rb_geo_tilt_coor.GetValue()==True:
#            run_script_flags.append("-crd");  run_script_flags.append("b")
            coord = "b"

        #-- default age options
        DefaultAge= ["none"]
#        if dia.cb_default_age.GetValue()==True:
        try:
            age_units= dia.default_age_unit.GetValue()
            min_age="%f"%float(dia.default_age_min.GetValue())
            max_age="%f"%float(dia.default_age_max.GetValue())
        except:
            min_age="0"
            if age_units=="Ga":
                max_age="4.56"
            elif age_units=="Ma":
                max_age="%f"%(4.56*1e3)
            elif age_units=="Ka":
                max_age="%f"%(4.56*1e6)
            elif age_units=="Years AD (+/-)":
                max_age="%f"%((time.time()/3.15569e7)+1970)
            elif age_units=="Years BP":
                max_age="%f"%((time.time()/3.15569e7)+1950)
            elif age_units=="Years Cal AD (+/-)":
                max_age=str(datetime.now())
            elif age_units=="Years Cal BP":
                max_age=((time.time()/3.15569e7)+1950)
            else:
                max_age="4.56"
                age_units="Ga"
#        run_script_flags.append("-age"); run_script_flags.append(min_age)
#        run_script_flags.append(max_age); run_script_flags.append(age_units)
        DefaultAge=[min_age, max_age, age_units]

        #-- sample mean
        avg_directions_by_sample = False
        if dia.cb_sample_mean.GetValue()==True:
#            run_script_flags.append("-aD")
            avg_directions_by_sample = True

        vgps_level = 'site'
        if dia.cb_sample_mean_VGP.GetValue()==True:
#            run_script_flags.append("-sam")
            vgps_level = 'sample'

        #-- site mean

        if dia.cb_site_mean.GetValue()==True:
            pass

        #-- location mean
        avg_by_polarity=False
        if dia.cb_location_mean.GetValue()==True:
#            run_script_flags.append("-pol")
            avg_by_polarity=True

        for FILE in ['pmag_samples.txt','pmag_sites.txt','pmag_results.txt']:
            self.PmagRecsOld[FILE]=[]
            try:
                meas_data,file_type=pmag.magic_read(os.path.join(self.WD, FILE))
                self.GUI_log.write("-I- Read old magic file  %s\n"%os.path.join(self.WD, FILE))
                if FILE !='pmag_specimens.txt':
                    os.remove(os.path.join(self.WD, FILE))
                    self.GUI_log.write("-I- Delete old magic file  %s\n"%os.path.join(self.WD,FILE))
            except:
                continue

            for rec in meas_data:
                if "magic_method_codes" in rec.keys():
                    if "LP-DIR" not in rec['magic_method_codes'] and "DE-" not in  rec['magic_method_codes']:
                        self.PmagRecsOld[FILE].append(rec)


        #print  run_script_flags
#        outstring=" ".join(run_script_flags)
#        print "-I- running python script:\n %s"%(outstring)
        #os.system(outstring)

        print 'coord', coord, 'vgps_level', vgps_level, 'DefaultAge', DefaultAge, 'avg_directions_by_sample', avg_directions_by_sample, 'avg_by_polarity', avg_by_polarity, 'use_criteria', use_criteria
        ipmag.specimens_results_magic(coord=coord, vgps_level=vgps_level, DefaultAge=DefaultAge, avg_directions_by_sample=avg_directions_by_sample, avg_by_polarity=avg_by_polarity, use_criteria=use_criteria)


        # subprocess.call(run_script_flags, shell=True)
        # reads new pmag tables, and merge the old lines:
        for FILE in ['pmag_samples.txt','pmag_sites.txt','pmag_results.txt']:
            pmag_data=[]
            try:
                pmag_data,file_type=pmag.magic_read(os.path.join(self.WD,FILE))
            except:
                pass
            if FILE in self.PmagRecsOld.keys():
                for rec in self.PmagRecsOld[FILE]:
                    pmag_data.append(rec)
            if len(pmag_data) >0:
                pmag_data_fixed=self.merge_pmag_recs(pmag_data)
                pmag.magic_write(os.path.join(self.WD, FILE), pmag_data_fixed, FILE.split(".")[0])
                self.GUI_log.write( "write new interpretations in %s\n"%(os.path.join(self.WD, FILE)))

        # make pmag_criteria.txt if it does not exist
        if not os.path.isfile(os.path.join(self.WD, "pmag_criteria.txt")):
            Fout=open(os.path.join(self.WD, "pmag_criteria.txt"),'w')
            Fout.write("tab\tpmag_criteria\n")
            Fout.write("er_citation_names\tpmag_criteria_code\n")
            Fout.write("This study\tACCEPT\n")


        self.update_pmag_tables()
        self.update_selection()
        TEXT="interpretations are saved in pmag tables.\n"
        dlg = wx.MessageDialog(self, caption="Saved",message=TEXT,style=wx.OK)
        result = dlg.ShowModal()
        if result == wx.ID_OK:
            dlg.Destroy()

        self.close_warning=False

    def merge_pmag_recs(self,old_recs):
        # fix the headers of pmag recs
        # make sure that all headers appear in all recs
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
                    #print "found a problmem in rec: ",rec
                    #print "missing: ", header
                    rec[header]=""
        return recs



    def on_menu_MagIC_model_builder(self,event):

        import MagIC_Model_Builder
        foundHTML=False
        try:
            PATH= sys.modules['MagIC_Model_Builder'].__file__
            HTML_PATH="/".join(PATH.split("/")[:-1]+["MagICModlBuilderHelp.html"])
            foundHTML=True
        except:
            pass
        if foundHTML:
            help_window=MagIC_Model_Builder.MyHtmlPanel(None,HTML_PATH)
            help_window.Show()

        #dia = MagIC_Model_Builder.MagIC_model_builder(self.WD,self.Data,self.Data_hierarchy)
        dia = MagIC_Model_Builder.MagIC_model_builder(self.WD)#,self.Data,self.Data_hierarchy)
        dia.Show()
        dia.Center()
        print "OK"
        #help_window.Close()
        self.Data,self.Data_hierarchy,self.Data_info={},{},{}
        self.Data_info=self.get_data_info() # get all ages, locations etc. (from er_ages, er_sites, er_locations)
        self.Data,self.Data_hierarchy=self.get_data() # Get data from magic_measurements and rmag_anistropy if exist.
        self.update_selection()

    def on_menu_samples_orientation(self,event):
        TEXT="A template for file demag_orient.txt, which contains samples orientation data was created in MagIC working directory.\n\n"
        TEXT=TEXT+"You can view/modify the orientation data using the demag-gui frame, or using Excel.\n\n"
        TEXT=TEXT+"If you choose to use Excel:\n"
        TEXT=TEXT+"1) save demag_orient.txt as 'tab delimited'\n"
        TEXT=TEXT+"2) Import demag_orient.txt to the demag-gui frame by choosing from the menu-bar: File -> Open orientation file\n\n"
        TEXT=TEXT+"After filling orientation data choose from the menu-bar: File -> Calculate samples orientations"

        SIZE=self.GetSize()
        frame = demag_dialogs.OrientFrameGrid (None, -1, 'demag_orient.txt',self.WD,self.Data_hierarchy,SIZE)

        frame.Show(True)
        frame.Centre()
        dlg1 = wx.MessageDialog(self,caption="Message:", message=TEXT ,style=wx.OK)
        result = dlg1.ShowModal()
        if result == wx.ID_OK:
            dlg1.Destroy()


    def on_menu_generic_to_magic(self,event):
        import demag_dialogs
        f=demag_dialogs.convert_generic_files_to_MagIC(self.WD)
        #def MyOnClose(evt):
        #    print "My onclose called"
        #    f.MakeModal(False)
        #    self.on_close_generic_file(self.WD)
        #    evt.Skip()
        #f.Bind(wx.EVT_CLOSE, MyOnClose)
        #f.MakeModal()
        #if f.END==True:
        #    self.on_close_generic_file(self.WD)
        #    f.Close()
        #self.on_close_generic_file(self.WD)
   # def on_close_generic_file(self,WD):
   #     print "Closed"
   #     print WD

    def on_menu_docs(self,event):
        """
        opens in library documentation for the usage of demag gui in a pdf/latex form
        @param: event -> the wx.MenuEvent that triggered this function
        """
        if sys.platform.startswith("darwin"):
            os.system("open " + os.path.join(PMAGPY_DIRECTORY + '/help_files/demag_gui_doc.pdf'))
        elif sys.platform.startswith("linux"):
            os.system("xdg-open " + os.path.join(PMAGPY_DIRECTORY + '/help_files/demag_gui_doc.pdf'))
        else:
            os.system("start " + os.path.join(PMAGPY_DIRECTORY + '/help_files/demag_gui_doc.pdf'))

    def on_menu_cookbook(self,event):
        webbrowser.open("http://earthref.org/PmagPy/cookbook/#x1-70002.4", new = 2)

    def on_menu_git(self,event):
        webbrowser.open("https://github.com/ltauxe/PmagPy", new = 2)

    def get_temp_indecies(self, fit = None, tmin = None, tmax = None, specimen = None):
        """
        Finds the appropriate indecies in self.Data[self.s]['zijdplot_steps'] given a set of upper/lower bounds. This is to resolve duplicate steps using the convention that the first good step of that name is the indicated step by that bound if there are no steps of the names tmin or tmax then it complains and reutrns a tuple (None,None).
        @param: fit -> the fit who's bounds to find the indecies of if no upper or lower bounds are specified
        @param: tmin -> the lower bound to find the index of
        @param: tmax -> the upper bound to find the index of
        @param: specimen -> the specimen who's steps to search for indecies (defaults to currently selected specimen)
        @return: a tuple with the lower bound index then the upper bound index
        """
        if specimen==None:
            specimen = self.s
        if fit and not tmin and not tmax:
            tmin = fit.tmin
            tmax = fit.tmax
        if tmin in self.Data[specimen]['zijdblock_steps']:
            tmin_index=self.Data[specimen]['zijdblock_steps'].index(tmin)
        elif type(tmin) == str or type(tmin) == unicode and tmin != '':
            int_steps = map(lambda x: int(x.strip("C mT")), self.Data[specimen]['zijdblock_steps'])
            int_tmin = int(tmin.strip("C mT"))
            diffs = map(lambda x: abs(x-int_tmin),int_steps)
            tmin_index = diffs.index(min(diffs))
        else: tmin_index=self.tmin_box.GetSelection()
        if tmax in self.Data[specimen]['zijdblock_steps']:
            tmax_index=self.Data[specimen]['zijdblock_steps'].index(tmax)
        elif type(tmax) == str or type(tmax) == unicode and tmax != '':
            int_steps = map(lambda x: int(x.strip("C mT")), self.Data[specimen]['zijdblock_steps'])
            int_tmax = int(tmax.strip("C mT"))
            diffs = map(lambda x: abs(x-int_tmax),int_steps)
            tmax_index = diffs.index(min(diffs))
        else: tmax_index=self.tmin_box.GetSelection()

        max_index = len(self.Data[specimen]['zijdblock_steps'])-1
        while (self.Data[specimen]['measurement_flag'][max_index] == 'b' and \
               max_index-1 > 0):
            max_index -= 1

        if tmin_index >= max_index:
            print("lower bound is greater or equal to max step cannot determine bounds for specimen: " + specimen)
            return (None,None)

        if (tmin_index > 0):
            while (self.Data[specimen]['measurement_flag'][tmin_index] == 'b' and \
                   tmin_index+1 < len(self.Data[specimen]['zijdblock_steps'])):
                if (self.Data[specimen]['zijdblock_steps'][tmin_index+1] == tmin):
                    tmin_index += 1
                else:
                    print("For specimen " + str(specimen) + " there are no good measurement steps with value - " + str(tmin))
                    break

        if (tmax_index < max_index):
            while (self.Data[specimen]['measurement_flag'][tmax_index] == 'b' and \
                   tmax_index+1 < len(self.Data[specimen]['zijdblock_steps'])):
                if (self.Data[specimen]['zijdblock_steps'][tmax_index+1] == tmax):
                    tmax_index += 1
                else:
                    print("For specimen " + str(specimen) + " there are no good measurement steps with value - " + str(tmax))
                    break

        if (tmin_index < 0): tmin_index = 0
        if (tmax_index > max_index): tmax_index = max_index

        return (tmin_index,tmax_index)

    def on_select_fit(self,event):
        """
        Picks out the fit selected in the fit combobox and sets it to the current fit of the GUI then calls the select function of the fit to set the GUI's bounds boxes and alter other such parameters
        @param: event -> the wx.ComboBoxEvent that triggers this function
        @alters: current_fit, fit_box selection, tmin_box selection, tmax_box selection
        """
        fit_val = self.fit_box.GetValue()
        if self.s not in self.pmag_results_data['specimens'] or not self.pmag_results_data['specimens'][self.s] or fit_val == 'None':
            self.clear_boxes()
            self.current_fit = None
            self.fit_box.SetStringSelection('None')
            self.tmin_box.SetStringSelection('')
            self.tmax_box.SetStringSelection('')
        else:
            try:
                fit_num = map(lambda x: x.name, self.pmag_results_data['specimens'][self.s]).index(fit_val)
            except ValueError:
                fit_num = -1
            self.pmag_results_data['specimens'][self.s][fit_num].select()
        if self.interpretation_editor_open:
            self.interpretation_editor.change_selected(self.current_fit)

    def on_enter_fit_name(self,event):
        """
        Allows the entering of new fit names in the fit combobox
        @param: event -> the wx.ComboBoxEvent that triggers this function
        @alters: current_fit.name
        """
        if self.current_fit == None:
            self.add_fit(event)
        value = self.fit_box.GetValue()
        if ':' in value: name,color = value.split(':')
        else: name,color = value,None
        if name in map(lambda x: x.name, self.pmag_results_data['specimens'][self.s]): print('bad name'); return
        self.current_fit.name = name
        if color in self.color_dict.keys(): self.current_fit.color = self.color_dict[color]
        self.update_fit_boxs()
        self.plot_higher_levels_data()

    def add_fit(self,event):
        """
        add a new interpretation to the current specimen
        @param: event -> the wx.ButtonEvent that triggered this function
        @alters: pmag_results_data
        """
        if not (self.s in self.pmag_results_data['specimens'].keys()):
            self.pmag_results_data['specimens'][self.s] = []
        next_fit = str(len(self.pmag_results_data['specimens'][self.s]) + 1)
        if ('Fit ' + next_fit) in map(lambda x: x.name, self.pmag_results_data['specimens'][self.s]): print('bad name'); return
        self.pmag_results_data['specimens'][self.s].append(Fit('Fit ' + next_fit, None, None, self.colors[(int(next_fit)-1) % len(self.colors)], self))
#        print("New Fit for sample: " + str(self.s) + '\n' + reduce(lambda x,y: x+'\n'+y, map(str,self.pmag_results_data['specimens'][self.s]['fits'])))
        self.new_fit()

    def delete_fit(self,event):
        """
        removes the current interpretation
        @param: event -> the wx.ButtonEvent that triggered this function
        """
        if not self.s in self.pmag_results_data['specimens']: return
        if self.current_fit in self.pmag_results_data['specimens'][self.s]:
            self.pmag_results_data['specimens'][self.s].remove(self.current_fit)
        if self.pmag_results_data['specimens'][self.s]:
            self.pmag_results_data['specimens'][self.s][-1].select()
        else:
            self.current_fit = None
        self.close_warning = True
        self.calculate_higher_levels_data()
        self.update_selection()

    def remove_replace_fit(self,event):
        """
        Remove or replace interpretations from higher order equal area plot and mean
        @param: event -> the wx.ButtonEvent that triggered this function
        @alters: bad_fits,
        """
        fit_val = self.mean_fit_box.GetValue()
        if fit_val == "None":
            return
        elif fit_val == "All":
            if all([(not (fit in self.bad_fits)) for fit in self.pmag_results_data['specimens'][self.s]]):
                for fit in self.pmag_results_data['specimens'][self.s]:
                    self.bad_fits.append(fit)
            else:
                for fit in self.pmag_results_data['specimens'][self.s]:
#                    print(fit in self.bad_fits)
                    if fit in self.bad_fits:
                        self.bad_fits.remove(fit)
        else:
            fit_index = map(lambda x: x.name, self.pmag_results_data['specimens'][self.s]).index(fit_val)
            bad_fit = self.pmag_results_data['specimens'][self.s][fit_index]
            if bad_fit in self.bad_fits:
                self.bad_fits.remove(bad_fit)
            else:
                self.bad_fits.append(bad_fit)
       #update the interpretation_editor to reflect bad interpretations
        if self.interpretation_editor_open:
            self.interpretation_editor.update_editor()
        self.close_warning = True
        self.calculate_higher_levels_data()
        self.update_selection()

    def new_fit(self):
        """
        finds the bounds of a new fit and calls update_fit_box adding it to the fit comboboxes
        """
        fit = self.pmag_results_data['specimens'][self.s][-1]
        self.current_fit = fit #update current fit to new fit

        if self.interpretation_editor_open:
            self.interpretation_editor.update_editor(True)

        self.update_fit_boxs(True)

        #Draw figures and add  text
        self.get_new_PCA_parameters(1)

    def update_fit_boxs(self, new_fit = False):
        """
        alters fit_box and mean_fit_box lists to match with changes in specimen or new/removed interpretations
        @param: new_fit -> boolean representing if there is a new fit
        @alters: fit_box selection, tmin_box selection, tmax_box selection, mean_fit_box selection, current_fit
        """
        #update the fit box
        self.update_fit_box(new_fit)
        #select new fit
        self.on_select_fit(None)
        #update the higher level fits box
        self.update_mean_fit_box()

    def update_fit_box(self, new_fit = False):
        """
        alters fit_box lists to match with changes in specimen or new/removed interpretations
        @param: new_fit -> boolean representing if there is a new fit
        @alters: fit_box selection and choices, current_fit
        """
        #get new fit data
        if self.s in self.pmag_results_data['specimens'].keys(): self.fit_list=list(map(lambda x: x.name, self.pmag_results_data['specimens'][self.s]))
        else: self.fit_list = []
        #find new index to set fit_box to
        if not self.fit_list: new_index = 'None'
        elif new_fit: new_index = len(self.fit_list) - 1
        else:
            if self.fit_box.GetValue() in self.fit_list:
                new_index = self.fit_list.index(self.fit_box.GetValue());
            else:
                new_index = 'None'
        #clear old box
        self.fit_box.Clear()
        #update fit box
        self.fit_box.SetItems(self.fit_list)
        fit_index = None
        #select defaults
        if new_index == 'None': self.fit_box.SetStringSelection('None')
        else: self.fit_box.SetSelection(new_index)

    def update_mean_fit_box(self):
        """
        alters mean_fit_box list to match with changes in specimen or new/removed interpretations
        @alters: mean_fit_box selection and choices, mean_types_box string selection
        """
        #get new fit data
        #if self.s in self.pmag_results_data['specimens'].keys(): self.fit_list=list(map(lambda x: x.name, self.pmag_results_data['specimens'][self.s]))
        #else: self.fit_list = []
        #clear old box
        self.mean_fit_box.Clear()
        #update higher level mean fit box
        self.all_fits_list = []
        fit_index = None
        if self.mean_fit in self.all_fits_list: fit_index = self.all_fits_list.index(self.mean_fit)
        for specimen in self.specimens:
            if specimen in self.pmag_results_data['specimens']:
                for name in map(lambda x: x.name, self.pmag_results_data['specimens'][specimen]):
                    if name not in self.all_fits_list: self.all_fits_list.append(name)
        self.mean_fit_box.SetItems(['None','All'] + self.all_fits_list)
        #select defaults
        if fit_index: self.mean_fit_box.SetSelection(fit_index+2)
        if self.mean_fit_box.GetValue() == 'None': self.mean_type_box.SetStringSelection('None')
        if self.interpretation_editor_open:
            self.interpretation_editor.mean_fit_box.Clear()
            self.interpretation_editor.mean_fit_box.SetItems(['None','All'] + self.all_fits_list)
            if fit_index: self.interpretation_editor.mean_fit_box.SetSelection(fit_index+2)
            if self.mean_fit_box.GetValue() == 'None': self.interpretation_editor.mean_type_box.SetStringSelection('None')

    def MacReopenApp(self):
        """Called when the doc icon is clicked"""
        self.GetTopWindow().Raise()




#--------------------------------------------------------------
# Save plots
#--------------------------------------------------------------

class SaveMyPlot(wx.Frame):
    """"""
    def __init__(self,fig,name,plot_type,dir_path):
        """Constructor"""
        wx.Frame.__init__(self, parent=None, title="")

        file_choices="(*.pdf)|*.pdf|(*.svg)|*.svg| (*.png)|*.png"
        default_fig_name="%s_%s.pdf"%(name,plot_type)
        dlg = wx.FileDialog(
            self,
            message="Save plot as...",
            defaultDir=dir_path,
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

#----------------------------------------------------------------------------------------

class EditFitFrame(wx.Frame):

    #########################Init Funcions#############################

    def __init__(self,parent):
        """Constructor"""
        #set parent and resolution
        self.parent = parent
        self.GUI_RESOLUTION=self.parent.GUI_RESOLUTION
        #call init of super class
        wx.Frame.__init__(self, self.parent, title="Interpretation Editor",size=(675*self.GUI_RESOLUTION,425*self.GUI_RESOLUTION))
        self.Bind(wx.EVT_CLOSE, self.on_close_edit_window)
        #make the Panel
        self.panel = wx.Panel(self,-1,size=(700*self.GUI_RESOLUTION,450*self.GUI_RESOLUTION))
        #set icon
        icon = wx.EmptyIcon()
        icon.CopyFromBitmap(wx.Bitmap(os.path.join(PMAGPY_DIRECTORY, "images/PmagPy.ico"), wx.BITMAP_TYPE_ANY))
        self.SetIcon(icon)
        self.specimens_list=self.parent.specimens
        self.specimens_list.sort(cmp=specimens_comparator)
        self.current_fit_index = None
        self.search_query = ""
        #build UI
        self.init_UI()
        #update with stuff
        self.on_select_level_name(None)

    def init_UI(self):
        """
        Builds User Interface for the interpretation Editor
        """

        #set fonts
        font1 = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Arial')
        font2 = wx.Font(13, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Arial')

        #if you're on mac do some funny stuff to make it look okay
        is_mac = False
        if sys.platform.startswith("darwin"):
            is_mac = True

        self.search_bar = wx.SearchCtrl(self.panel, size=(350*self.GUI_RESOLUTION,25) ,style=wx.TE_PROCESS_ENTER | wx.TE_PROCESS_TAB | wx.TE_NOHIDESEL)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_enter_search_bar,self.search_bar)
        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.on_enter_search_bar,self.search_bar)
#        self.Bind(wx.EVT_TEXT, self.on_complete_search_bar,self.search_bar)

        #build logger
        self.logger = wx.ListCtrl(self.panel, -1, size=(350*self.GUI_RESOLUTION,475*self.GUI_RESOLUTION),style=wx.LC_REPORT)
        self.logger.SetFont(font1)
        self.logger.InsertColumn(0, 'specimen',width=55*self.GUI_RESOLUTION)
        self.logger.InsertColumn(1, 'fit name',width=45*self.GUI_RESOLUTION)
        self.logger.InsertColumn(2, 'max',width=35*self.GUI_RESOLUTION)
        self.logger.InsertColumn(3, 'min',width=35*self.GUI_RESOLUTION)
        self.logger.InsertColumn(4, 'n',width=25*self.GUI_RESOLUTION)
        self.logger.InsertColumn(5, 'fit type',width=60*self.GUI_RESOLUTION)
        self.logger.InsertColumn(6, 'dec',width=35*self.GUI_RESOLUTION)
        self.logger.InsertColumn(7, 'inc',width=35*self.GUI_RESOLUTION)
        self.logger.InsertColumn(8, 'mad',width=35*self.GUI_RESOLUTION)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnClick_listctrl, self.logger)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK,self.OnRightClickListctrl,self.logger)

        #set fit attributes box
        self.display_sizer = wx.StaticBoxSizer(wx.StaticBox(self.panel, wx.ID_ANY, "display options"), wx.HORIZONTAL)
        self.name_sizer = wx.StaticBoxSizer(wx.StaticBox(self.panel, wx.ID_ANY, "fit name/color"), wx.VERTICAL)
        self.bounds_sizer = wx.StaticBoxSizer(wx.StaticBox(self.panel, wx.ID_ANY, "fit bounds"), wx.VERTICAL)
        self.buttons_sizer = wx.StaticBoxSizer(wx.StaticBox(self.panel, wx.ID_ANY), wx.VERTICAL)

        #logger display selection box
        UPPER_LEVEL = self.parent.level_box.GetValue()
        if UPPER_LEVEL=='sample':
            name_choices = self.parent.samples
        if UPPER_LEVEL=='site':
            name_choices = self.parent.sites
        if UPPER_LEVEL=='location':
            name_choices = self.parent.locations
        if UPPER_LEVEL=='study':
            name_choices = ['this study']

        self.level_box = wx.ComboBox(self.panel, -1, size=(100*self.GUI_RESOLUTION, 25), value=UPPER_LEVEL, choices=['sample','site','location','study'], style=wx.CB_DROPDOWN)
        self.Bind(wx.EVT_COMBOBOX, self.on_select_higher_level,self.level_box)

        self.level_names = wx.ComboBox(self.panel, -1, size=(100*self.GUI_RESOLUTION, 25), value=self.parent.level_names.GetValue(), choices=name_choices, style=wx.CB_DROPDOWN)
        self.Bind(wx.EVT_COMBOBOX, self.on_select_level_name,self.level_names)

        #mean type and plot display boxes
        self.mean_type_box = wx.ComboBox(self.panel, -1, size=(100*self.GUI_RESOLUTION, 25), value=self.parent.mean_type_box.GetValue(), choices=['Fisher','Fisher by polarity','None'], style=wx.CB_DROPDOWN,name="high_type")
        self.Bind(wx.EVT_COMBOBOX, self.on_select_mean_type_box,self.mean_type_box)

        self.mean_fit_box = wx.ComboBox(self.panel, -1, size=(100*self.GUI_RESOLUTION, 25), value=self.parent.mean_fit, choices=(['None','All'] + self.parent.fit_list), style=wx.CB_DROPDOWN,name="high_type")
        self.Bind(wx.EVT_COMBOBOX, self.on_select_mean_fit_box,self.mean_fit_box)

        #show box
        if UPPER_LEVEL == "study" or UPPER_LEVEL == "location":
            show_box_choices = ['specimens','samples','sites']
        if UPPER_LEVEL == "site":
            show_box_choices = ['specimens','samples']
        if UPPER_LEVEL == "sample":
            show_box_choices = ['specimens']

        self.show_box = wx.ComboBox(self.panel, -1, size=(100*self.GUI_RESOLUTION, 25), value='specimens', choices=show_box_choices, style=wx.CB_DROPDOWN,name="high_elements")
        self.Bind(wx.EVT_COMBOBOX, self.on_select_show_box,self.show_box)

        #coordinates box
        self.coordinates_box = wx.ComboBox(self.panel, -1, size=(100*self.GUI_RESOLUTION, 25), choices=self.parent.coordinate_list, value=self.parent.coordinates_box.GetValue(), style=wx.CB_DROPDOWN, name="coordinates")
        self.Bind(wx.EVT_COMBOBOX, self.on_select_coordinates,self.coordinates_box)

        #bounds select boxes
        self.tmin_box = wx.ComboBox(self.panel, -1, size=(80*self.GUI_RESOLUTION, 25), choices=[''] + self.parent.T_list, style=wx.CB_DROPDOWN, name="lower bound")

        self.tmax_box = wx.ComboBox(self.panel, -1, size=(80*self.GUI_RESOLUTION, 25), choices=[''] + self.parent.T_list, style=wx.CB_DROPDOWN, name="upper bound")

        #color box
        self.color_dict = self.parent.color_dict
        self.color_box = wx.ComboBox(self.panel, -1, size=(80*self.GUI_RESOLUTION, 25), choices=[''] + self.color_dict.keys(), style=wx.TE_PROCESS_ENTER, name="color")
        self.Bind(wx.EVT_TEXT_ENTER, self.add_new_color, self.color_box)

        #name box
        self.name_box = wx.TextCtrl(self.panel, -1, size=(80*self.GUI_RESOLUTION, 25), style=wx.HSCROLL, name="name")

        #more mac stuff
        h_size_buttons,button_spacing = 25,5.5
        if is_mac: h_size_buttons,button_spacing = 18,0.

        self.add_fit_button = wx.Button(self.panel, id=-1, label='add to selected',size=(160*self.GUI_RESOLUTION,h_size_buttons))
        self.add_fit_button.SetFont(font1)
        self.Bind(wx.EVT_BUTTON, self.add_highlighted_fits, self.add_fit_button)

        self.delete_fit_button = wx.Button(self.panel, id=-1, label='delete selected',size=(160*self.GUI_RESOLUTION,h_size_buttons))
        self.delete_fit_button.SetFont(font1)
        self.Bind(wx.EVT_BUTTON, self.delete_highlighted_fits, self.delete_fit_button)

        self.apply_changes_button = wx.Button(self.panel, id=-1, label='apply changes',size=(160*self.GUI_RESOLUTION,h_size_buttons))
        self.apply_changes_button.SetFont(font1)
        self.Bind(wx.EVT_BUTTON, self.apply_changes, self.apply_changes_button)

        display_window_0 = wx.GridSizer(2, 1, 10*self.GUI_RESOLUTION, 19*self.GUI_RESOLUTION)
        display_window_1 = wx.GridSizer(2, 1, 10*self.GUI_RESOLUTION, 19*self.GUI_RESOLUTION)
        display_window_2 = wx.GridSizer(2, 1, 10*self.GUI_RESOLUTION, 19*self.GUI_RESOLUTION)
        name_window = wx.GridSizer(2, 1, 10*self.GUI_RESOLUTION, 19*self.GUI_RESOLUTION)
        bounds_window = wx.GridSizer(2, 1, 10*self.GUI_RESOLUTION, 19*self.GUI_RESOLUTION)
        buttons1_window = wx.GridSizer(2, 1, 10*self.GUI_RESOLUTION, 19*self.GUI_RESOLUTION)
        buttons2_window = wx.GridSizer(2, 1, 10*self.GUI_RESOLUTION, 19*self.GUI_RESOLUTION)
        buttons3_window = wx.GridSizer(2, 1, 10*self.GUI_RESOLUTION, 19*self.GUI_RESOLUTION)
        display_window_0.AddMany( [(self.coordinates_box, wx.ALIGN_LEFT),
                                   (self.show_box, wx.ALIGN_LEFT)] )
        display_window_1.AddMany( [(self.level_box, wx.ALIGN_LEFT),
                                   (self.mean_type_box, wx.ALIGN_LEFT)] )
        display_window_2.AddMany( [(self.level_names, wx.ALIGN_LEFT),
                                   (self.mean_fit_box, wx.ALIGN_LEFT)] )
        name_window.AddMany( [(self.name_box, wx.ALIGN_LEFT),
                                (self.color_box, wx.ALIGN_LEFT)] )
        bounds_window.AddMany( [(self.tmin_box, wx.ALIGN_LEFT),
                                (self.tmax_box, wx.ALIGN_LEFT)] )
        buttons1_window.Add(self.add_fit_button, wx.ALIGN_TOP)
        buttons2_window.Add(self.delete_fit_button, wx.ALIGN_TOP)
        buttons3_window.Add(self.apply_changes_button, wx.ALIGN_TOP)
        self.display_sizer.Add(display_window_0, 0, wx.TOP, 8)
        self.display_sizer.Add(display_window_1, 0, wx.TOP | wx.LEFT, 8)
        self.display_sizer.Add(display_window_2, 0, wx.TOP | wx.LEFT, 8)
        self.name_sizer.Add(name_window, 0, wx.TOP, 5.5)
        self.bounds_sizer.Add(bounds_window, 0, wx.TOP, 5.5)
        self.buttons_sizer.Add(buttons1_window, 0, wx.TOP, button_spacing)
        self.buttons_sizer.Add(buttons2_window, 0, wx.TOP, button_spacing)
        self.buttons_sizer.Add(buttons3_window, 0, wx.TOP, button_spacing)

        #duplicate higher levels plot
        self.fig = copy.copy(self.parent.fig4)
        self.canvas = FigCanvas(self.panel, -1, self.fig)
        self.toolbar = NavigationToolbar(self.canvas)
        self.toolbar.Hide()
        self.toolbar.zoom()
        self.higher_EA_setting = "Zoom"
        self.canvas.Bind(wx.EVT_LEFT_DCLICK,self.parent.on_equalarea_higher_select)
        self.canvas.Bind(wx.EVT_MOTION,self.on_change_higher_mouse_cursor)
        self.canvas.Bind(wx.EVT_MIDDLE_DOWN,self.home_higher_equalarea)

        #Higher Level Statistics Box
        self.stats_sizer = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY,"mean statistics"  ), wx.VERTICAL)

        for parameter in ['mean_type','dec','inc','alpha95','K','R','n_lines','n_planes']:
            COMMAND="self.%s_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(75*self.GUI_RESOLUTION,25))"%parameter
            exec COMMAND
            COMMAND="self.%s_window.SetBackgroundColour(wx.WHITE)"%parameter
            exec COMMAND
            COMMAND="self.%s_window.SetFont(font2)"%parameter
            exec COMMAND
            COMMAND="self.%s_outer_window = wx.GridSizer(1,2,5*self.GUI_RESOLUTION,15*self.GUI_RESOLUTION)"%parameter
            exec COMMAND
            COMMAND="""self.%s_outer_window.AddMany([
                    (wx.StaticText(self.panel,label='%s',style=wx.TE_CENTER),wx.EXPAND),
                    (self.%s_window, wx.EXPAND)])"""%(parameter,parameter,parameter)
            exec COMMAND
            COMMAND="self.stats_sizer.Add(self.%s_outer_window, 0, wx.ALIGN_LEFT, 0)"%parameter
            exec COMMAND

        self.switch_stats_button = wx.SpinButton(self.panel, id=wx.ID_ANY, style=wx.SP_HORIZONTAL|wx.SP_ARROW_KEYS|wx.SP_WRAP, name="change stats")
        self.Bind(wx.EVT_SPIN, self.on_select_stats_button,self.switch_stats_button)

        #construct panel
        hbox0 = wx.BoxSizer(wx.HORIZONTAL)
        hbox0.Add(self.name_sizer,flag=wx.ALIGN_TOP,border=8)
        hbox0.Add(self.bounds_sizer,flag=wx.ALIGN_TOP,border=8)

        vbox0 = wx.BoxSizer(wx.VERTICAL)
        vbox0.Add(hbox0,flag=wx.ALIGN_TOP,border=8)
        vbox0.Add(self.buttons_sizer,flag=wx.ALIGN_TOP,border=8)

        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(vbox0,flag=wx.ALIGN_TOP,border=8)
        hbox1.Add(self.stats_sizer,flag=wx.ALIGN_TOP,border=8)
        hbox1.Add(self.switch_stats_button,flag=wx.ALIGN_TOP,border=8)

        vbox1 = wx.BoxSizer(wx.VERTICAL)
        vbox1.Add(self.display_sizer,flag=wx.ALIGN_TOP,border=8)
        vbox1.Add(hbox1,flag=wx.ALIGN_TOP,border=8)
        vbox1.Add(self.canvas,flag=wx.ALIGN_TOP,border=8)

        vbox2 = wx.BoxSizer(wx.VERTICAL)
        vbox2.Add(self.search_bar,flag=wx.ALIGN_LEFT | wx.ALIGN_BOTTOM,border=8)
        vbox2.Add(self.logger,flag=wx.ALIGN_LEFT,border=8)

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2.Add(vbox2,flag=wx.ALIGN_LEFT,border=8)
        hbox2.Add(vbox1,flag=wx.ALIGN_TOP,border=8)

        self.panel.SetSizer(hbox2)
        hbox2.Fit(self)

    ################################Logger Functions##################################

    def update_editor(self,changed_interpretation_parameters=True):
        """
        updates the logger and plot on the interpretation editor window
        @param: changed_interpretation_parameters -> if the logger should be whipped and completely recalculated from scratch or not (default = True)
        """

        if changed_interpretation_parameters:
            self.fit_list = []
            self.search_choices = []
            for specimen in self.specimens_list:
                if specimen not in self.parent.pmag_results_data['specimens']: continue
                self.fit_list += [(fit,specimen) for fit in self.parent.pmag_results_data['specimens'][specimen]]

            self.logger.DeleteAllItems()
            offset = 0
            for i in range(len(self.fit_list)):
                i -= offset
                v = self.update_logger_entry(i)
                if v == "s": offset += 1

        #use copy so that the fig doesn't close when the editor closes
        self.toolbar.home()
        self.fig = copy.copy(self.parent.fig4)
        self.canvas.draw()

    def update_logger_entry(self,i):
        """
        helper function that given a index in this objects fit_list parameter inserts a entry at that index
        @param: i -> index in fit_list to find the (specimen_name,fit object) tup that determines all the data for this logger entry.
        """
        if i < len(self.fit_list):
            tup = self.fit_list[i]
        elif i < self.logger.GetItemCount():
            self.logger.DeleteItem(i)
            return
        else: return

        fit = tup[0]
        pars = fit.get(self.parent.COORDINATE_SYSTEM)
        fmin,fmax,n,ftype,dec,inc,mad = "","","","","","",""

        specimen = tup[1]
        name = fit.name
        if 'measurement_step_min' in pars.keys(): fmin = str(fit.tmin)
        if 'measurement_step_max' in pars.keys(): fmax = str(fit.tmax)
        if 'specimen_n' in pars.keys(): n = str(pars['specimen_n'])
        if 'calculation_type' in pars.keys(): ftype = pars['calculation_type']
        if 'specimen_dec' in pars.keys(): dec = "%.1f"%pars['specimen_dec']
        if 'specimen_inc' in pars.keys(): inc = "%.1f"%pars['specimen_inc']
        if 'specimen_mad' in pars.keys(): mad = "%.1f"%pars['specimen_mad']

        if self.search_query != "":
            entry = (specimen+name+fmin+fmax+n+ftype+dec+inc+mad).lower()
            if self.search_query not in entry:
                self.fit_list.pop(i)
                if i < self.logger.GetItemCount():
                    self.logger.DeleteItem(i)
                return "s"
        for e in (specimen,name,fmin,fmax,n,ftype,dec,inc,mad):
            if e not in self.search_choices:
                self.search_choices.append(e)

        if i < self.logger.GetItemCount():
            self.logger.DeleteItem(i)
        self.logger.InsertStringItem(i, str(specimen))
        self.logger.SetStringItem(i, 1, name)
        self.logger.SetStringItem(i, 2, fmin)
        self.logger.SetStringItem(i, 3, fmax)
        self.logger.SetStringItem(i, 4, n)
        self.logger.SetStringItem(i, 5, ftype)
        self.logger.SetStringItem(i, 6, dec)
        self.logger.SetStringItem(i, 7, inc)
        self.logger.SetStringItem(i, 8, mad)
        self.logger.SetItemBackgroundColour(i,"WHITE")
        a,b = False,False
        if fit in self.parent.bad_fits:
            self.logger.SetItemBackgroundColour(i,"YELLOW")
            b = True
        if self.parent.current_fit == fit:
            self.logger.SetItemBackgroundColour(i,"LIGHT BLUE")
            self.logger_focus(i)
            self.current_fit_index = i
            a = True
        if a and b:
            self.logger.SetItemBackgroundColour(i,"GREEN")

    def update_current_fit_data(self):
        """
        updates the current_fit of the parent Zeq_GUI entry in the case of it's data being changed
        """
        if self.current_fit_index:
            self.update_logger_entry(self.current_fit_index)

    def change_selected(self,new_fit):
        """
        updates passed in fit or index as current fit for the editor (does not affect parent),
        if no parameters are passed in it sets first fit as current and complains.
        @param: new_fit -> fit object to highlight as selected
        """
        if self.search_query and self.parent.current_fit not in map(lambda x: x[0], self.fit_list): return
        if self.current_fit_index == None:
            if not self.parent.current_fit: return
            for i,(fit,specimen) in enumerate(self.fit_list):
                if fit == self.parent.current_fit:
                    self.current_fit_index = i
                    break
        i = 0
        if isinstance(new_fit, Fit):
            for i, (fit,speci) in enumerate(self.fit_list):
                if fit == new_fit:
                    break
        elif type(new_fit) is int:
            i = new_fit
        elif new_fit != None:
            print('cannot select fit of type: ' + str(type(new_fit)))
        if self.current_fit_index != None and \
        len(self.fit_list) > 0 and \
        self.fit_list[self.current_fit_index][0] in self.parent.bad_fits:
            self.logger.SetItemBackgroundColour(self.current_fit_index,"YELLOW")
        else:
            self.logger.SetItemBackgroundColour(self.current_fit_index,"WHITE")
        self.current_fit_index = i
        if self.fit_list[self.current_fit_index][0] in self.parent.bad_fits:
            self.logger.SetItemBackgroundColour(self.current_fit_index,"GREEN")
        else:
            self.logger.SetItemBackgroundColour(self.current_fit_index,"LIGHT BLUE")

    def logger_focus(self,i,focus_shift=16):
        """
        focuses the logger on an index 12 entries below i
        @param: i -> index to focus on
        """
        if self.logger.GetItemCount()-1 > i+focus_shift:
            i += focus_shift
        else:
            i = self.logger.GetItemCount()-1
        self.logger.Focus(i)

    def OnClick_listctrl(self, event):
        """
        Edits the logger and the Zeq_GUI parent object to select the fit that was newly selected by a double click
        @param: event -> wx.ListCtrlEvent that triggered this function
        """
        i = event.GetIndex()
        if self.parent.current_fit == self.fit_list[i][0]: return
        si = self.parent.specimens.index(self.fit_list[i][1])
        self.parent.specimens_box.SetSelection(si)
        self.parent.select_specimen(self.fit_list[i][1])
        self.parent.draw_figure(self.fit_list[i][1], False)
        self.change_selected(i)
        fi = 0
        while (self.parent.s == self.fit_list[i][1] and i >= 0): i,fi = (i-1,fi+1)
        self.parent.update_fit_box()
        self.parent.fit_box.SetSelection(fi-1)
        self.parent.update_fit_boxs(False)
        self.parent.Add_text()


    def OnRightClickListctrl(self, event):
        """
        Edits the logger and the Zeq_GUI parent object so that the selected interpretation is now marked as bad
        @param: event -> wx.ListCtrlEvent that triggered this function
        """
        i = event.GetIndex()
        fit = self.fit_list[i][0]
        if fit in self.parent.bad_fits:
            self.parent.bad_fits.remove(fit)
            if i == self.current_fit_index:
                self.logger.SetItemBackgroundColour(i,"LIGHT BLUE")
            else:
                self.logger.SetItemBackgroundColour(i,"WHITE")
        else:
            self.parent.bad_fits.append(fit)
            if i == self.current_fit_index:
                self.logger.SetItemBackgroundColour(i,"GREEN")
            else:
                self.logger.SetItemBackgroundColour(i,"YELLOW")
        self.parent.calculate_higher_levels_data()
        self.parent.plot_higher_levels_data()
        self.logger_focus(i)

    ##################################Search Bar Functions###############################

    def on_enter_search_bar(self,event):
        self.search_query = self.search_bar.GetValue().replace(" ","").lower()
        self.update_editor(True)

#    def on_complete_search_bar(self,event):
#        self.search_bar.AutoComplete(self.search_choices)

    ###################################ComboBox Functions################################

    def add_new_color(self,event):
        new_color = self.color_box.GetValue()
        if ':' in new_color:
            color_list = new_color.split(':')
            color_name = color_list[0]
            color_val = map(eval, tuple(color_list[1].strip('( )').split(',')))
        else:
            return
        self.color_dict[color_name] = color_val
        #clear old box
        self.color_box.Clear()
        #update fit box
        self.color_box.SetItems([''] + self.color_dict.keys())

    def on_select_coordinates(self,event):
        self.parent.coordinates_box.SetStringSelection(self.coordinates_box.GetStringSelection())
        self.parent.onSelect_coordinates(event)

    def on_select_show_box(self,event):
        """

        """
        self.parent.UPPER_LEVEL_SHOW=self.show_box.GetValue()
        self.parent.calculate_higher_levels_data()
        self.parent.update_selection()


    def on_select_higher_level(self,event,called_by_parent=False):
        """
        alters the possible entries in level_names combobox to give the user selections for which specimen interpretations to display in the logger
        @param: event -> the wx.COMBOBOXEVENT that triggered this function
        """
        UPPER_LEVEL=self.level_box.GetValue()

        if UPPER_LEVEL=='sample':
            self.level_names.SetItems(self.parent.samples)
            self.level_names.SetStringSelection(self.parent.Data_hierarchy['sample_of_specimen'][self.parent.s])

        if UPPER_LEVEL=='site':
            self.level_names.SetItems(self.parent.sites)
            self.level_names.SetStringSelection(self.parent.Data_hierarchy['site_of_specimen'][self.parent.s])

        if UPPER_LEVEL=='location':
            self.level_names.SetItems(self.parent.locations)
            self.level_names.SetStringSelection(self.parent.Data_hierarchy['location_of_specimen'][self.parent.s])

        if UPPER_LEVEL=='study':
            self.level_names.SetItems(['this study'])
            self.level_names.SetStringSelection('this study')

        if not called_by_parent:
            self.parent.level_box.SetStringSelection(UPPER_LEVEL)
            self.parent.onSelect_higher_level(event,True)

        self.on_select_level_name(event)

    def on_select_level_name(self,event,called_by_parent=False):
        """
        change this objects specimens_list to control which specimen interpretatoins are displayed in this objects logger
        @param: event -> the wx.ComboBoxEvent that triggered this function
        """
        high_level_name=str(self.level_names.GetValue())

        if self.level_box.GetValue()=='sample':
            self.specimens_list=self.parent.Data_hierarchy['samples'][high_level_name]['specimens']
        elif self.level_box.GetValue()=='site':
            self.specimens_list=self.parent.Data_hierarchy['sites'][high_level_name]['specimens']
        elif self.level_box.GetValue()=='location':
            self.specimens_list=self.parent.Data_hierarchy['locations'][high_level_name]['specimens']
        elif self.level_box.GetValue()=='study':
            self.specimens_list=self.parent.Data_hierarchy['study']['this study']['specimens']

        if not called_by_parent:
            self.parent.level_names.SetStringSelection(high_level_name)
            self.parent.onSelect_level_name(event,True)

        self.specimens_list.sort(cmp=specimens_comparator)
        self.update_editor()

    def on_select_mean_type_box(self, event):
        """
        set parent Zeq_GUI to reflect change in this box and change the
        @param: event -> the wx.ComboBoxEvent that triggered this function
        """
        new_mean_type = self.mean_type_box.GetValue()
        if new_mean_type == "None":
            self.parent.clear_higher_level_pars()
        self.parent.mean_type_box.SetStringSelection(new_mean_type)
        self.parent.onSelect_mean_type_box(event)

    def on_select_mean_fit_box(self, event):
        """
        set parent Zeq_GUI to reflect the change in this box then replot the high level means plot
        @param: event -> the wx.COMBOBOXEVENT that triggered this function
        """
        new_mean_fit = self.mean_fit_box.GetValue()
        self.parent.mean_fit_box.SetStringSelection(new_mean_fit)
        self.parent.onSelect_mean_fit_box(event)

    ###################################Button Functions##################################

    def on_select_stats_button(self,event):
        """

        """
        i = self.switch_stats_button.GetValue()
        self.parent.switch_stats_button.SetValue(i)
        self.parent.update_higher_level_stats()

    def add_highlighted_fits(self, evnet):
        """
        adds a new interpretation to each specimen highlighted in logger if multiple interpretations are highlighted of the same specimen only one new interpretation is added
        @param: event -> the wx.ButtonEvent that triggered this function
        """

        specimens = []
        next_i = self.logger.GetNextSelected(-1)
        if next_i == -1: specimens = self.parent.specimens
        else:
            while next_i != -1:
                fit,specimen = self.fit_list[next_i]
                if specimen in specimens:
                    next_i = self.logger.GetNextSelected(next_i)
                    continue
                else: specimens.append(specimen)
                next_i = self.logger.GetNextSelected(next_i)

        for specimen in specimens:

            if specimen not in self.parent.pmag_results_data['specimens']:
                self.parent.pmag_results_data['specimens'][specimen] = []

            new_name = self.name_box.GetLineText(0)
            new_color = self.color_box.GetValue()
            new_tmin = self.tmin_box.GetValue()
            new_tmax = self.tmax_box.GetValue()

            if not new_name:
                next_fit = str(len(self.parent.pmag_results_data['specimens'][specimen]) + 1)
                while ("Fit " + next_fit) in map(lambda x: x.name, self.parent.pmag_results_data['specimens'][specimen]):
                    next_fit = str(int(next_fit) + 1)
                new_name = ("Fit " + next_fit)
            if not new_color:
                next_fit = str(len(self.parent.pmag_results_data['specimens'][specimen]) + 1)
                new_color = self.parent.colors[(int(next_fit)-1) % len(self.parent.colors)]
            else: new_color = self.color_dict[new_color]
            if not new_tmin: new_tmin = None
            if not new_tmax: new_tmax = None

            if new_name in map(lambda x: x.name, self.parent.pmag_results_data['specimens'][specimen]):
                print('-E- interpretation called ' + new_name + ' already exsists for specimen ' + specimen)
                continue

            new_fit = Fit(new_name, new_tmin, new_tmax, new_color, self.parent)
            new_fit.put(specimen,self.parent.COORDINATE_SYSTEM,self.parent.get_PCA_parameters(specimen,new_tmin,new_tmax,self.parent.COORDINATE_SYSTEM,"DE-BFL"))

            self.parent.pmag_results_data['specimens'][specimen].append(new_fit)
        self.update_editor(True)
        self.parent.update_selection()

    def delete_highlighted_fits(self, event):
        """
        iterates through all highlighted fits in the logger of this object and removes them from the logger and the Zeq_GUI parent object
        @param: event -> the wx.ButtonEvent that triggered this function
        """

        next_i = -1
        deleted_items = []
        while True:
            next_i = self.logger.GetNextSelected(next_i)
            if next_i == -1:
                break
            deleted_items.append(next_i)
        deleted_items.sort(cmp=lambda x,y: y - x)
        for item in deleted_items:
            self.delete_entry(index=item)
        self.parent.update_selection()

    def delete_entry(self, fit = None, index = None):
        """
        deletes the single item from the logger of this object that corrisponds to either the passed in fit or index. Note this function mutaits the logger of this object if deleting more than one entry be sure to pass items to delete in from highest index to lowest or else odd things can happen.
        @param: fit -> Fit object to delete from this objects logger
        @param: index -> integer index of the entry to delete from this objects logger
        """
        if type(index) == int and not fit:
            fit,specimen = self.fit_list[index]
        if fit and type(index) == int:
            for i, (f,s) in enumerate(self.fit_list):
                if fit == f:
                    index,specimen = i,s
                    break

        if index == self.current_fit_index: self.current_fit_index = None
        if fit not in self.parent.pmag_results_data['specimens'][specimen]:
            print("cannot remove item (entry #: " + str(index) + ") as it doesn't exist, this is a dumb bug contact devs")
            self.logger.DeleteItem(index)
            return
        self.parent.pmag_results_data['specimens'][specimen].remove(fit)
        del self.fit_list[index]
        self.logger.DeleteItem(index)

    def apply_changes(self, event):
        """
        applies the changes in the various attribute boxes of this object to all highlighted fit objects in the logger, these changes are reflected both in this object and in the Zeq_GUI parent object.
        @param: event -> the wx.ButtonEvent that triggered this function
        """

        new_name = self.name_box.GetLineText(0)
        new_color = self.color_box.GetValue()
        new_tmin = self.tmin_box.GetValue()
        new_tmax = self.tmax_box.GetValue()

        next_i = -1
        changed_i = []
        while True:
            next_i = self.logger.GetNextSelected(next_i)
            if next_i == -1:
                break
            specimen = self.fit_list[next_i][1]
            fit = self.fit_list[next_i][0]
            if new_name:
                if new_name not in map(lambda x: x.name, self.parent.pmag_results_data['specimens'][specimen]): fit.name = new_name
            if new_color:
                fit.color = self.color_dict[new_color]
            #testing
            not_both = True
            if new_tmin and new_tmax:
                if fit == self.parent.current_fit:
                    self.parent.tmin_box.SetStringSelection(new_tmin)
                    self.parent.tmax_box.SetStringSelection(new_tmax)
                fit.put(specimen,self.parent.COORDINATE_SYSTEM, self.parent.get_PCA_parameters(specimen,new_tmin,new_tmax,self.parent.COORDINATE_SYSTEM,fit.PCA_type))
                not_both = False
            if new_tmin and not_both:
                if fit == self.parent.current_fit:
                    self.parent.tmin_box.SetStringSelection(new_tmin)
                fit.put(specimen,self.parent.COORDINATE_SYSTEM, self.parent.get_PCA_parameters(specimen,new_tmin,fit.tmax,self.parent.COORDINATE_SYSTEM,fit.PCA_type))
            if new_tmax and not_both:
                if fit == self.parent.current_fit:
                    self.parent.tmax_box.SetStringSelection(new_tmax)
                fit.put(specimen,self.parent.COORDINATE_SYSTEM, self.parent.get_PCA_parameters(specimen,fit.tmin,new_tmax,self.parent.COORDINATE_SYSTEM,fit.PCA_type))
            changed_i.append(next_i)

        offset = 0
        for i in changed_i:
            i -= offset
            v = self.update_logger_entry(i)
            if v == "s":
                offset += 1

        self.parent.update_selection()

    ###################################Canvas Functions##################################

    def home_higher_equalarea(self,event):
        """
        returns higher equal area to it's original position
        @param: event -> the wx.MouseEvent that triggered the call of this function
        @alters: toolbar setting
        """
        self.toolbar.home()

    def on_change_higher_mouse_cursor(self,event):
        """
        If mouse is over data point making it selectable change the shape of the cursor
        @param: event -> the wx Mouseevent for that click
        """
        if self.show_box.GetValue() != "specimens": return
        pos=event.GetPosition()
        width, height = self.canvas.get_width_height()
        pos[1] = height - pos[1]
        xpick_data,ypick_data = pos
        xdata_org = self.parent.higher_EA_xdata
        ydata_org = self.parent.higher_EA_ydata
        data_corrected = self.parent.high_level_eqarea.transData.transform(numpy.vstack([xdata_org,ydata_org]).T)
        xdata,ydata = data_corrected.T
        xdata = map(float,xdata)
        ydata = map(float,ydata)
        e = 4e0

        if self.higher_EA_setting == "Zoom":
            self.canvas.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))
        elif self.higher_EA_setting == "Pan":
            self.canvas.SetCursor(wx.StockCursor(wx.CURSOR_WATCH))
        else:
            self.canvas.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
        if not self.parent.higher_EA_xdata or not self.parent.higher_EA_ydata: return
        for i,(x,y) in enumerate(zip(xdata,ydata)):
            if 0 < numpy.sqrt((x-xpick_data)**2. + (y-ypick_data)**2.) < e:
                self.canvas.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
                break

    ###############################Window Functions######################################

    def on_close_edit_window(self, event):
        """
        the function that is triggered on the close of the interpretation editor window
        @param: event -> wx.WindowEvent that triggered this function
        """

        self.parent.interpretation_editor_open = False
        self.Destroy()


#----------------------------------------------------------------------------------------

class Fit():

    def __init__(self, name, tmax, tmin, color, GUI):
        """
        The Data Structure that represents an interpretation
        @param: name -> the name of the fit as it will be displayed to the user
        @param: tmax -> the upper bound of the fit
        @param: tmin -> the lower bound of the fit
        @param: color -> the color of the fit when it is graphed
        @param: GUI -> the Zeq_GUI on which this fit is drawn
        """
        self.name = name
        if type(tmax) != str:
            self.tmax = ""
        else:
            self.tmax = tmax
        if type(tmin) != str:
            self.tmin = ""
        else:
            self.tmin = tmin
        self.color = color
        calculation_type = GUI.PCA_type_box.GetValue()
        if calculation_type=="line": PCA_type="DE-BFL"
        elif calculation_type=="line-anchored": PCA_type="DE-BFL-A"
        elif calculation_type=="line-with-origin": PCA_type="DE-BFL-O"
        elif calculation_type=="Fisher": PCA_type="DE-FM"
        elif calculation_type=="plane": PCA_type="DE-BFP"
        else: raise ValueError("No PCA type selected for new fit")
        self.PCA_type = PCA_type
        self.lines = [None,None]
        self.GUI = GUI
        self.pars = {}
        self.geopars = {}
        self.tiltpars = {}

    def select(self):
        """
        Makes this fit the selected fit on the GUI that is it's parent
        (Note: may be moved into GUI soon)
        """
        self.GUI.current_fit = self
        if self.tmax != None and self.tmin != None:
            self.GUI.update_temp_boxes()
        if self.PCA_type != None:
            self.GUI.update_PCA_box()
        try: self.GUI.zijplot
        except AttributeError: self.GUI.draw_figure(self.GUI.s)
        self.GUI.fit_box.SetStringSelection(self.name)
        self.GUI.get_new_PCA_parameters(-1)

    def get(self,coordinate_system):
        """
        Return the pmagpy paramters dictionary associated with this fit and the given
        coordinate system
        @param: coordinate_system -> the coordinate system who's parameters to return
        """
        if coordinate_system == 'DA-DIR' or coordinate_system == 'specimen':
            return self.pars
        elif coordinate_system == 'DA-DIR-GEO' or coordinate_system == 'geographic':
            return self.geopars
        elif coordinate_system == 'DA-DIR-TILT' or coordinate_system == 'tilt-corrected':
            return self.tiltpars
        else:
            print("-E- no such parameters to fetch for " + coordinate_system + " in fit: " + self.name)
            return None

    def put(self,specimen,coordinate_system,new_pars):
        """
        Given a coordinate system and a new parameters dictionary that follows pmagpy
        convention given by the pmag.py/domean function it alters this fit's bounds and
        parameters such that it matches the new data.
        @param: specimen -> None if fit is for a site or a sample or a valid specimen from self.GUI
        @param: coordinate_system -> the coordinate system to alter
        @param: new_pars -> the new paramters to change your fit to
        @alters: tmin, tmax, pars, geopars, tiltpars, PCA_type
        """

        if specimen != None:
            if type(new_pars) != dict or 'measurement_step_min' not in new_pars.keys() or 'measurement_step_max' not in new_pars.keys() or 'calculation_type' not in new_pars.keys():
                print("-E- invalid parameters cannot assign to fit - was given:\n"+str(new_pars))
                return {}

            self.tmin = new_pars['measurement_step_min']
            self.tmax = new_pars['measurement_step_max']
            self.PCA_type = new_pars['calculation_type']

            steps = self.GUI.Data[specimen]['zijdblock_steps']
            tl = [self.tmin,self.tmax]
            for i,t in enumerate(tl):
                if str(t) in steps: tl[i] = str(t)
                elif "%.1fmT"%t in steps: tl[i] = "%.1fmT"%t
                elif "%.0fC"%t in steps: tl[i] = "%.0fC"%t
                else: 
                    print("-E- Step " + str(tl[i]) + " does not exsist (func: Fit.put)")
                    tl[i] = str(t)
            self.tmin,self.tmax = tl

        if coordinate_system == 'DA-DIR' or coordinate_system == 'specimen':
            self.pars = new_pars
        elif coordinate_system == 'DA-DIR-GEO' or coordinate_system == 'geographic':
            self.geopars = new_pars
        elif coordinate_system == 'DA-DIR-TILT' or coordinate_system == 'tilt-corrected':
            self.tiltpars = new_pars
        else:
            print('-E- no such coordinate system could not assign those parameters to fit')

    def has_values(self, name, tmin, tmax):
        """
        A basic fit equality checker compares name and bounds of 2 fits
        @param: name -> name of the other fit
        @param: tmin -> lower bound of the other fit
        @param: tmax -> upper bound of the other fit
        @return: boolean comaparing 2 fits
        """
        return str(self.name) == str(name) and str(self.tmin) == str(tmin) and str(self.tmax) == str(tmax)

    def __str__(self):
        """
        Readable printing method for fit to turn it into a string
        @return: string representing fit
        """
        try: return self.name + ": \n" + "Tmax = " + self.tmax + ", Tmin = " + self.tmin + "\n" + "Color = " + str(self.color)
        except ValueError: return self.name + ": \n" + " Color = " + self.color

#--------------------------------------------------------------
# Run the GUI
#--------------------------------------------------------------
def specimens_comparator(s1,s2):
    l1 = map(int, re.findall('\d+', s1))
    l2 = map(int, re.findall('\d+', s2))
    for i1,i2 in zip(l1,l2):
        if i1-i2 != 0:
            return i1-i2
    return 0

def alignToTop(win):
    dw, dh = wx.DisplaySize()
    w, h = win.GetSize()
    #x = dw - w
    #y = dh - h

    win.SetPosition(((dw-w)/2.,0 ))



def do_main(WD=None, standalone_app=True, parent=None):
    # to run as module:
    if not standalone_app:
        frame = Zeq_GUI(WD, parent)
        frame.Center()
        frame.Show()

    # to run as command_line:
    else:
        app = wx.App()
        app.frame = Zeq_GUI(WD)
        app.frame.Center()
        #alignToTop(app.frame)
        #dw, dh = wx.DisplaySize()
        #w, h = app.frame.GetSize()
        #print 'display 2', dw, dh
        #print "gui 2", w, h
        app.frame.Show()
        app.MainLoop()

if __name__ == '__main__':
    do_main()

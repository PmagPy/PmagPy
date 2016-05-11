#!/usr/bin/env pythonw

#============================================================================================
# LOG HEADER:
#============================================================================================
#
# Demag_GUI Version 0.33 add interpretation editor, plane plotting functionality and more
# propose merging development fork to main PmagPy repository by Kevin Gaastra (11/09/2015)
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
# Module Imports
#--------------------------------------

import matplotlib
if not matplotlib.get_backend() == 'WXAgg':
    matplotlib.use('WXAgg')

import os,sys,pdb
global CURRENT_VERSION, PMAGPY_DIRECTORY
CURRENT_VERSION = "v.0.33"
# get directory in a way that works whether being used
# on the command line or in a frozen binary
import pmagpy.check_updates as check_updates
PMAGPY_DIRECTORY = os.path.split(check_updates.get_pmag_dir())[0]

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar

try:
    import zeq_gui_preferences
except:
    pass
from time import time
from datetime import datetime
import wx
import wx.lib.scrolledpanel
from numpy import vstack,sqrt,arange,array
from pylab import rcParams,Figure,arange,pi,cos,sin,array,mean
from scipy.optimize import curve_fit
from scipy.signal import find_peaks_cwt
from webbrowser import open as webopen
from pkg_resources import resource_filename

import pmagpy.pmag as pmag
import pmagpy.ipmag as ipmag
from dialogs.demag_interpretation_editor import InterpretationEditorFrame
from pmagpy.demag_gui_utilities import *
from pmagpy.Fit import *
import dialogs.demag_dialogs as demag_dialogs
from copy import deepcopy,copy
import cit_magic as cit_magic


matplotlib.rc('xtick', labelsize=10)
matplotlib.rc('ytick', labelsize=10)
matplotlib.rc('axes', labelsize=8)
matplotlib.rcParams['savefig.dpi'] = 300.

rcParams.update({"svg.fonttype":'svgfont'})

class Demag_GUI(wx.Frame):
    """
    The main frame of the application
    """
    title = "PmagPy Demag GUI %s (beta)"%CURRENT_VERSION

#==========================================================================================#
#============================Initalization Functions=======================================#
#==========================================================================================#

    def __init__(self, WD=None, parent=None):
        """
        NAME:
    demag_gui.py

        DESCRIPTION:
    GUI for interpreting demagnetization data (AF and/or thermal).
    For tutorial on usage see the PmagPy cookbook at http://earthref.org/PmagPy/cookbook/
        """

        args=sys.argv
        if "-h" in args:
            help(self)
            sys.exit()

        default_style = wx.MINIMIZE_BOX | wx.MAXIMIZE_BOX | wx.RESIZE_BORDER | wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX | wx.CLIP_CHILDREN | wx.NO_FULL_REPAINT_ON_RESIZE
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title, style = default_style, name='demag gui')
        self.parent = parent

        self.currentDirectory = os.getcwd() # get the current working directory
        if "-WD" in sys.argv:
            ind=sys.argv.index('-WD')
            WD = sys.argv[ind+1]
        if WD != None:
            if not os.path.isdir(WD):
                print("There is no directory %s using current directory"%(WD))
                WD = os.getcwd()
            self.change_WD(WD)
        else:
            new_WD = self.get_DIR() # choose directory dialog, then initialize directory variables
            if new_WD == self.currentDirectory and sys.version.split()[0] == '2.7.11':
                new_WD = self.get_DIR()
            self.change_WD(new_WD)
        self.init_log_file()

        #init wait dialog
        disableAll = wx.WindowDisabler()
        wait = wx.BusyInfo('Compiling required data, please wait...')
        wx.Yield()

        #set icon
        icon = wx.EmptyIcon()
        icon_path = os.path.join(PMAGPY_DIRECTORY, 'programs', 'images', 'PmagPy.ico')
        if os.path.exists(icon_path):
            icon.CopyFromBitmap(wx.Bitmap(icon_path, wx.BITMAP_TYPE_ANY))
            self.SetIcon(icon)
        else:
            print("-I- PmagPy icon file not found -- skipping")

        # initialize acceptence criteria with NULL values
        self.acceptance_criteria=pmag.initialize_acceptance_criteria()
        try:
            self.acceptance_criteria=pmag.read_criteria_from_file(os.path.join(self.WD, "pmag_criteria.txt"), self.acceptance_criteria)
        except IOError:
            print("-I- Cant find/read file  pmag_criteria.txt")


        self.font_type = "Arial"
        if sys.platform.startswith("linux"): self.font_type = "Liberation Serif"

        self.preferences=self.get_preferences()
        self.dpi = 100

        # initialize selecting criteria
        self.COORDINATE_SYSTEM='geographic'
        self.UPPER_LEVEL_SHOW='specimens'
        self.Data_info=self.get_data_info() # Read  er_* data
        self.Data,self.Data_hierarchy=self.get_data() # Get data from magic_measurements and rmag_anistropy if exist.

        self.all_fits_list = []
        
        self.pmag_results_data={}
        for level in ['specimens','samples','sites','locations','study']:
            self.pmag_results_data[level]={}

        self.high_level_means={}
        for high_level in ['samples','sites','locations','study']:
            if high_level not in self.high_level_means.keys():
                self.high_level_means[high_level]={}

        self.interpretation_editor_open = False
        self.color_dict = {'green':'g','yellow':'y','maroon':'m','cyan':'c','blue':'b','red':'r','brown':(139./255.,69./255.,19./255.),'orange':(255./255.,127./255.,0./255.),'pink':(255./255.,20./255.,147./255.),'violet':(153./255.,50./255.,204./255.),'grey':(84./255.,84./255.,84./255.),'goldenrod':'goldenrod'}
        self.colors = ['g','y','m','c','b','r',(139./255.,69./255.,19./255.),(255./255.,127./255.,0./255.),(255./255.,20./255.,147./255.),(153./255.,50./255.,204./255.),(84./255.,84./255.,84./255.), 'goldenrod']
        self.current_fit = None
        self.dirtypes = ['DA-DIR','DA-DIR-GEO','DA-DIR-TILT']
        self.bad_fits = []

        self.specimens=self.Data.keys()         # get list of specimens
        self.specimens.sort(cmp=specimens_comparator) # sort list of specimens
        if len(self.specimens)>0:
            self.s=str(self.specimens[0])
        else:
            self.s=""
        self.samples=self.Data_hierarchy['samples'].keys()         # get list of samples
        self.samples.sort(cmp=specimens_comparator)                   # get list of specimens
        self.sites=self.Data_hierarchy['sites'].keys()         # get list of sites
        self.sites.sort(cmp=specimens_comparator)                   # get list of sites
        self.locations=self.Data_hierarchy['locations'].keys()      # get list of sites
        self.locations.sort()                   # get list of sites

        self.panel = wx.lib.scrolledpanel.ScrolledPanel(self,-1) # make the Panel
        self.panel.SetupScrolling()
        self.init_UI()                   # build the main frame
        self.create_menu()                  # create manu bar

        # get previous interpretations from pmag tables
        # Draw figures and add text
        if self.Data:
            self.update_pmag_tables()
            if not self.current_fit:
                self.update_selection()
            else:
                self.Add_text()
                self.update_fit_boxes()
        else:
            print("---------------------------no magic_measurements.txt found----------------------------------")
            self.Destroy()

        self.arrow_keys()
        self.Bind(wx.EVT_CLOSE, self.on_menu_exit)
        self.close_warning=False
        wait.Destroy()

    def init_UI(self):
        """
        Build main frame of panel: buttons, etc.
        choose the first specimen and display data
        """

        dw, dh = wx.DisplaySize()
        w, h = self.GetSize()
        r1=dw/1210.
        r2=dw/640.

        self.GUI_RESOLUTION=min(r1,r2,1.3)

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

        self.fig2 = Figure((2.5*self.GUI_RESOLUTION, 2.5*self.GUI_RESOLUTION), dpi=self.dpi)
        self.specimen_eqarea_net = self.fig2.add_subplot(111)
        self.draw_net(self.specimen_eqarea_net)
        self.specimen_eqarea = self.fig2.add_axes(self.specimen_eqarea_net.get_position(), frameon=False,axisbg='None')
        self.specimen_eqarea.axes.set_aspect('equal')
        self.specimen_eqarea.axis('off')
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
        font1 = wx.Font(9+FONT_RATIO, wx.SWISS, wx.NORMAL, wx.NORMAL, False, self.font_type)
        # GUI headers
        font2 = wx.Font(12+min(1,FONT_RATIO), wx.SWISS, wx.NORMAL, wx.NORMAL, False, self.font_type)
        font3 = wx.Font(11+FONT_RATIO, wx.SWISS, wx.NORMAL, wx.NORMAL, False, self.font_type)
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
        self.specimens_box = wx.ComboBox(self.panel, -1, value=self.s, size=(150*self.GUI_RESOLUTION,25), choices=self.specimens, style=wx.CB_DROPDOWN,name="specimen")
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

        self.coordinate_list = ['specimen']
        intial_coordinate = 'specimen'
        for specimen in self.specimens:
            if 'geographic' not in self.coordinate_list and self.Data[specimen]['zijdblock_geo']:
                self.coordinate_list.append('geographic')
                intial_coordinate = 'geographic'
            if 'tilt-corrected' not in self.coordinate_list and self.Data[specimen]['zijdblock_tilt']:
                self.coordinate_list.append('tilt-corrected')

        self.COORDINATE_SYSTEM = intial_coordinate
        self.coordinates_box = wx.ComboBox(self.panel, -1, size=(150*self.GUI_RESOLUTION,25), choices=self.coordinate_list, value=intial_coordinate,style=wx.CB_DROPDOWN,name="coordinates")
        self.Bind(wx.EVT_COMBOBOX, self.onSelect_coordinates,self.coordinates_box)

        self.orthogonal_box = wx.ComboBox(self.panel, -1, value='X=East', size=(150*self.GUI_RESOLUTION,25), choices=['X=NRM dec','X=East','X=North'], style=wx.CB_DROPDOWN,name="orthogonal_plot")
        #remove 'X=best fit line dec' as option given that is isn't implemented for multiple components
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

        self.box_sizer_specimen = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY,"interpretation type"  ), wx.HORIZONTAL )

        self.PCA_type_box = wx.ComboBox(self.panel, -1, size=(100*self.GUI_RESOLUTION, 25), value='line',choices=['line','line-anchored','line-with-origin','plane','Fisher'], style=wx.CB_DROPDOWN,name="coordinates")
        self.Bind(wx.EVT_COMBOBOX, self.on_select_specimen_mean_type_box,self.PCA_type_box)

        self.plane_display_box = wx.ComboBox(self.panel, -1, size=(100*self.GUI_RESOLUTION, 25), value='show whole plane',choices=['show whole plane','show u. hemisphere', 'show l. hemisphere','show poles'], style=wx.CB_DROPDOWN,name="PlaneType")
        self.Bind(wx.EVT_COMBOBOX, self.on_select_plane_display_box, self.plane_display_box)

        specimen_stat_type_window = wx.GridSizer(2, 1, 10*self.GUI_RESOLUTION, 19*self.GUI_RESOLUTION)
        specimen_stat_type_window.AddMany([(self.PCA_type_box, wx.ALIGN_LEFT),
                                           (self.plane_display_box, wx.ALIGN_LEFT)])
        self.box_sizer_specimen.Add(specimen_stat_type_window, 0, wx.ALIGN_LEFT, 0 )

        self.box_sizer_specimen_stat = wx.StaticBoxSizer(wx.StaticBox(self.panel, wx.ID_ANY,"interpretation direction and statistics"), wx.HORIZONTAL )

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
            (wx.StaticText(self.panel,label="\ndang",style=wx.TE_CENTER),wx.TE_CENTER),
            (wx.StaticText(self.panel,label="\na95",style=wx.TE_CENTER),wx.TE_CENTER),
            (self.sdec_window, wx.EXPAND),
            (self.sinc_window, wx.EXPAND) ,
            (self.sn_window, wx.EXPAND) ,
            (self.smad_window, wx.EXPAND),
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

    #----------------------------------------------------------------------
        # Design the panel
    #----------------------------------------------------------------------

        outer_sizer = wx.BoxSizer(wx.HORIZONTAL)
        outer_sizer.Add(self.panel)
        self.SetSizerAndFit(outer_sizer)

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
        self.panel.SetSizeHints(self.GUI_SIZE[0],self.GUI_SIZE[1])

    def create_menu(self):
        """
        Create menu
        """
        self.menubar = wx.MenuBar()

        #------------------------------------------------------------------------------

        menu_file = wx.Menu()

        m_change_WD = menu_file.Append(-1, "Change Working Directory\tCtrl-W","")
        self.Bind(wx.EVT_MENU, self.on_menu_change_working_directory, m_change_WD)

        m_make_MagIC_results_tables = menu_file.Append(-1, "&Save MagIC pmag tables\tCtrl-Shift-S", "")
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

        m_read = wx.Menu()

        m_choose_inp = m_read.Append(-1, "&Read in Data Using Single .inp File\tCtrl-O", "")
        self.Bind(wx.EVT_MENU, self.on_menu_pick_read_inp, m_choose_inp)

        m_read_all_inp = m_read.Append(-1, "&Read in all .inp files from sub-directories\tCtrl-Shift-O", "")
        self.Bind(wx.EVT_MENU, self.on_menu_read_all_inp, m_read_all_inp)

#        menu_Analysis.AppendMenu(-1, "&Convert and Combine MagFiles", m_read)

        m_import_LSQ = menu_Analysis.Append(-1, "&Import Interpretations from LSQ file\tCtrl-L", "")
        self.Bind(wx.EVT_MENU, self.on_menu_read_from_LSQ, m_import_LSQ)

        m_previous_interpretation = menu_Analysis.Append(-1, "&Import previous interpretations from a redo file\tCtrl-R", "")
        self.Bind(wx.EVT_MENU, self.on_menu_previous_interpretation, m_previous_interpretation)

        m_save_interpretation = menu_Analysis.Append(-1, "&Save current interpretations to a redo file\tCtrl-S", "")
        self.Bind(wx.EVT_MENU, self.on_menu_save_interpretation, m_save_interpretation)

        #m_delete_interpretation = menu_Analysis.Append(-1, "&Clear all current interpretations\tCtrl-Shift-D", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_clear_interpretation, m_delete_interpretation)

        #-----------------
        # Tools Menu
        #-----------------

        menu_Tools = wx.Menu()

        #m_bulk_demagnetization = menu_Tools.Append(-1, "&Bulk demagnetization\tCtrl-B", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_bulk_demagnetization, m_bulk_demagnetization)

#        m_auto_interpret = menu_Tools.Append(-1, "&Auto interpret (alpha version)\tCtrl-A", "")
#        self.Bind(wx.EVT_MENU, self.autointerpret, m_auto_interpret)

        m_edit_interpretations = menu_Tools.Append(-1, "&Interpretation editor\tCtrl-E", "")
        self.Bind(wx.EVT_MENU, self.on_menu_edit_interpretations, m_edit_interpretations)

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

        m_debug = menu_Help.Append(-1, "&Open Debugger\tCtrl-Shift-D", "")
        self.Bind(wx.EVT_MENU, self.on_menu_debug, m_debug)

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

        menu_flag_meas = wx.Menu()

        m_good = menu_flag_meas.Append(-1, "&Good Measurement\tCtrl-Alt-G", "")
        self.Bind(wx.EVT_MENU, self.on_menu_flag_meas_good, m_good)
        m_bad = menu_flag_meas.Append(-1, "&Bad Measurement\tCtrl-Alt-B", "")
        self.Bind(wx.EVT_MENU, self.on_menu_flag_meas_bad, m_bad)

        m_flag_meas = menu_edit.AppendMenu(-1, "&Flag Measurement Data", menu_flag_meas)

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

#==========================================================================================#
#===========================Figure Plotting Functions======================================#
#==========================================================================================#

    def draw_figure(self,s,update_higher_plots=True):
        step = ""
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

        self.zij_xy_points, = self.zijplot.plot(self.CART_rot_good[:,0], -1*self.CART_rot_good[:,1], 'ro-', mfc=self.dec_MFC, mec=self.dec_MEC, markersize=self.MS, clip_on=False, picker=True) #x,y or N,E
        self.zij_xz_points, = self.zijplot.plot(self.CART_rot_good[:,0], -1*self.CART_rot_good[:,2], 'bs-', mfc=self.inc_MFC, mec=self.inc_MEC, markersize=self.MS, clip_on=False, picker=True) #x-z or N,D

        for i in range(len( self.CART_rot_bad)):
            self.zijplot.plot(self.CART_rot_bad[:,0][i],-1* self.CART_rot_bad[:,1][i],'o',mfc='None',mec=self.dec_MEC,markersize=self.MS,clip_on=False,picker=False) #x,y or N,E
            self.zijplot.plot(self.CART_rot_bad[:,0][i],-1 * self.CART_rot_bad[:,2][i],'s',mfc='None',mec=self.inc_MEC,markersize=self.MS,clip_on=False,picker=False) #x-z or N,D

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
            self.fig1.text(0.01,0.98,"Zijderveld plot: x = North",{'family':self.font_type, 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })
        elif self.ORTHO_PLOT_TYPE=='E-W':
            STRING=""
            #STRING1="E-W orthogonal plot"
            self.fig1.text(0.01,0.98,"Zijderveld plot:: x = East",{'family':self.font_type, 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })

        elif self.ORTHO_PLOT_TYPE=='PCA_dec':
            self.fig1.text(0.01,0.98,"Zijderveld plot",{'family':self.font_type, 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })
            if 'specimen_dec' in self.current_fit.pars.keys() and type(self.current_fit.pars['specimen_dec'])!=str:
                STRING="X-axis rotated to best fit line declination (%.0f); "%(self.current_fit.pars['specimen_dec'])
            else:
                STRING="X-axis rotated to NRM (%.0f); "%(self.zijblock[0][1])
        else:
            self.fig1.text(0.01,0.98,"Zijderveld plot",{'family':self.font_type, 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })
            STRING="X-axis rotated to NRM (%.0f); "%(self.zijblock[0][1])
            #STRING1="Zijderveld plot"


        STRING=STRING+"NRM=%.2e "%(self.zijblock[0][3])+ 'Am^2'
        self.fig1.text(0.01,0.95,STRING, {'family':self.font_type, 'fontsize':8*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })

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
        self.specimen_eqarea.text(-1.2,1.15,"specimen: %s"%self.s,{'family':self.font_type, 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })

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
        #--------------------

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

        #-----------------------------------------------------------
        # Draw M/M0 plot ( or NLT data on the same area in the GUI)
        #-----------------------------------------------------------

        self.fig3.clf()
        self.fig3.text(0.02,0.96,'M/M0',{'family':self.font_type, 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })
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
        #start_time_3=time()
        #runtime_sec3 = start_time_3 - start_time_2
        #print "-I- draw M_M0 figures is", runtime_sec3,"seconds"

        #-----------------------------------------------------------
        # high level equal area
        #-----------------------------------------------------------
        if update_higher_plots:
            self.plot_higher_levels_data()
        self.canvas4.draw()

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

    def draw_interpretation(self):
        """
        draw the specimen interpretations on the zijderveld and the specimen equal area
        @alters: fit.lines, zijplot, specimen_eqarea_interpretation, mplot_interpretation
        """

        if self.s in self.pmag_results_data['specimens'] and \
            self.pmag_results_data['specimens'][self.s] != []:
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

            tmin_index,tmax_index = self.get_indices(fit);

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

                PCA_dir=[pars['specimen_dec'],pars['specimen_inc'],1]
                PCA_dir_rotated=[PCA_dir[0]-rotation_declination,PCA_dir[1],1]
                PCA_CART_rotated=pmag.dir2cart(PCA_dir_rotated)

                slop_xy_PCA=-1*PCA_CART_rotated[1]/PCA_CART_rotated[0]
                slop_xz_PCA=-1*PCA_CART_rotated[2]/PCA_CART_rotated[0]

                # Center of mass rotated for plotting
                CM_x=mean(self.CART_rot_good[:,0][tmin_index:tmax_index+1])
                CM_y=mean(self.CART_rot_good[:,1][tmin_index:tmax_index+1])
                CM_z=mean(self.CART_rot_good[:,2][tmin_index:tmax_index+1])

                # intercpet from the center of mass
                intercept_xy_PCA=-1*CM_y - slop_xy_PCA*CM_x
                intercept_xz_PCA=-1*CM_z - slop_xz_PCA*CM_x

                xx=array([self.CART_rot[:,0][tmax_index],self.CART_rot[:,0][tmin_index]])
                yy=slop_xy_PCA*xx+intercept_xy_PCA
                zz=slop_xz_PCA*xx+intercept_xz_PCA

                if (pars['calculation_type'] in ['DE-BFL-A']): ###CHECK
                    xx = [0.] + xx
                    yy = [0.] + yy
                    zz = [0.] + zz

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

            self.specimen_eqarea.set_xlim(-1., 1.)
            self.specimen_eqarea.set_ylim(-1., 1.)
            self.specimen_eqarea.axes.set_aspect('equal')
            self.specimen_eqarea.axis('off')
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
                        self.logger.SetItemBackgroundColour(item,"red")

        self.canvas1.draw()
        self.canvas2.draw()
        self.canvas3.draw()

    def plot_higher_levels_data(self):

       self.toolbar4.home()

       high_level=self.level_box.GetValue()
       self.UPPER_LEVEL_NAME=self.level_names.GetValue()
       self.UPPER_LEVEL_MEAN=self.mean_type_box.GetValue()

       self.high_level_eqarea.clear()
       what_is_it=self.level_box.GetValue()+": "+self.level_names.GetValue()
       self.high_level_eqarea.text(-1.2,1.15,what_is_it,{'family':self.font_type, 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })

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
            if element not in self.pmag_results_data[elements_type].keys() and self.UPPER_LEVEL_SHOW == 'specimens':
                self.calculate_high_level_mean(elements_type,element,"Fisher","specimens",self.mean_fit)
            if element in self.pmag_results_data[elements_type].keys():
                self.plot_higher_level_equalarea(element)

            else:
                if element not in self.high_level_means[elements_type].keys():
                    self.calculate_high_level_mean(elements_type,element,"Fisher",'specimens',self.mean_fit)
                if self.mean_fit not in self.high_level_means[elements_type][element].keys():
                    self.calculate_high_level_mean(elements_type,element,"Fisher",'specimens',self.mean_fit)
                if element in self.high_level_means[elements_type].keys():
                    if self.mean_fit != "All" and self.mean_fit in self.high_level_means[elements_type][element].keys():
                        if dirtype in self.high_level_means[elements_type][element][self.mean_fit].keys():
                            mpars=self.high_level_means[elements_type][element][self.mean_fit][dirtype]
                            self.plot_eqarea_pars(mpars,self.high_level_eqarea)
                    else:
                        for mf in self.all_fits_list:
                            if mf not in self.high_level_means[elements_type][element].keys():
                                self.calculate_high_level_mean(elements_type,element,"Fisher",'specimens',mf)
                            if mf in self.high_level_means[elements_type][element].keys():
                                if dirtype in self.high_level_means[elements_type][element][mf].keys():
                                    mpars=self.high_level_means[elements_type][element][mf][dirtype]
                                    self.plot_eqarea_pars(mpars,self.high_level_eqarea)

       # plot elements means
       if calculation_type!="None":
           if high_level_name in self.high_level_means[high_level_type].keys():
                if self.mean_fit in self.high_level_means[high_level_type][high_level_name].keys():
                    if dirtype in self.high_level_means[high_level_type][high_level_name][self.mean_fit].keys():
                        self.plot_eqarea_mean(self.high_level_means[high_level_type][high_level_name][self.mean_fit][dirtype],self.high_level_eqarea)


       self.high_level_eqarea.set_xlim(-1., 1.)
       self.high_level_eqarea.set_ylim(-1., 1.)
       self.high_level_eqarea.axes.set_aspect('equal')
       self.high_level_eqarea.axis('off')
       self.canvas4.draw()
       if self.interpretation_editor_open:
           self.update_higher_level_stats()
           self.interpretation_editor.update_editor(False)

    def plot_higher_level_equalarea(self,element):
        if self.interpretation_editor_open:
            higher_level = self.interpretation_editor.show_box.GetValue()
        else: higher_level = self.UPPER_LEVEL_SHOW
        fits = []
        if higher_level not in self.pmag_results_data: print("no level: " + str(higher_level)); return
        if element not in self.pmag_results_data[higher_level]: print("no element: " + str(element)); return
        if self.mean_fit == 'All':
            fits = self.pmag_results_data[higher_level][element]
        elif self.mean_fit != 'None' and self.mean_fit != None:
            fits = [fit for fit in self.pmag_results_data[higher_level][element] if fit.name == self.mean_fit]
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
            XY=pmag.dimap(float(dec),float(inc))
            if inc>0:
                if 'color' in pars.keys(): FC=pars['color'];EC=pars['color'];SIZE=15*self.GUI_RESOLUTION
                else: FC='grey';EC='grey';SIZE=15*self.GUI_RESOLUTION
            else:
                if 'color' in pars.keys(): FC='white';EC=pars['color'];SIZE=15*self.GUI_RESOLUTION
                else: FC='white';EC='grey';SIZE=15*self.GUI_RESOLUTION
            fig.scatter([XY[0]],[XY[1]],marker='o',edgecolor=EC, facecolor=FC,s=SIZE,lw=1,clip_on=False)

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
            if float(mpars["inc"])>0:
                FC='black';EC='0.1'
            else:
                FC='white';EC='black'
            fig.scatter([XY[0]],[XY[1]],marker='o',edgecolor=EC, facecolor=FC,s=30,lw=1,clip_on=False)

            if "alpha95" in mpars.keys():
            # get the alpha95
                Xcirc,Ycirc=[],[]
                Da95,Ia95=pmag.circ(float(mpars["dec"]),float(mpars["inc"]),float(mpars["alpha95"]))
                for k in  range(len(Da95)):
                    XY=pmag.dimap(Da95[k],Ia95[k])
                    Xcirc.append(XY[0])
                    Ycirc.append(XY[1])
                fig.plot(Xcirc,Ycirc,'black')

        fig.set_xlim(xmin, xmax)
        fig.set_ylim(ymin, ymax)

#==========================================================================================#
#========================Backend Data Processing Functions=================================#
#==========================================================================================#

    #---------------------------------------------#
    #Data Calculation Function
    #---------------------------------------------#

    def initialize_CART_rot(self,s):

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

        # remove bad data from plotting:

        self.CART_rot_good=[]
        self.CART_rot_bad=[]
        for i in range(len(self.CART_rot)):
            if self.Data[self.s]['measurement_flag'][i]=='g':
                self.CART_rot_good.append(list(self.CART_rot[i]))
            else:
                self.CART_rot_bad.append(list(self.CART_rot[i]))

        self.CART_rot_good=array(self.CART_rot_good)
        self.CART_rot_bad=array(self.CART_rot_bad)

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

    def get_PCA_parameters(self,specimen,fit,tmin,tmax,coordinate_system,calculation_type):
        """
        calculate statisics
        """
        if tmin == '' or tmax == '': return
        beg_pca,end_pca = self.get_indices(fit, tmin, tmax, specimen)

        if beg_pca == None or end_pca == None: print("%s to %s are invalid bounds, to fit %s for specimen %s"%(tmin,tmax,fit.name,specimen)); return
        check_duplicates = []
        for s,f in zip(self.Data[specimen]['zijdblock_steps'][beg_pca:end_pca+1],self.Data[specimen]['measurement_flag'][beg_pca:end_pca+1]):
            if f == 'g' and [s,'g'] in check_duplicates:
                if s == tmin: print("There are multiple good %s steps. The first measurement will be used for lower bound of fit %s for specimen %s."%(tmin,fit.name,specimen))
                if s == tmax: print("There are multiple good %s steps. The first measurement will be used for upper bound of fit %s for specimen %s."%(tmax,fit.name,specimen))
                else: print("Within Fit %s on specimen %s, there are multiple good measurements at the %s step. Both measurements are included in the fit."%(fit.name,specimen,s))
            else:
                check_duplicates.append([s,f])

        if coordinate_system=='geographic':
            block=self.Data[specimen]['zijdblock_geo']
        elif coordinate_system=='tilt-corrected':
            block=self.Data[specimen]['zijdblock_tilt']
        else:
            block=self.Data[specimen]['zijdblock']
        if  end_pca > beg_pca and end_pca - beg_pca > 1:
            mpars=pmag.domean(block,beg_pca,end_pca,calculation_type) #preformes regression
            if 'specimen_direction_type' in mpars and mpars['specimen_direction_type']=='Error':
                print("-E- no measurement data for specimen %s in coordinate system %s"%(specimen, coordinate_system))
                return {}
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

    def autointerpret(self,event,step_size=None,calculation_type="DE-BFL"):

        sucess = self.clear_interpretations()

        if not sucess: return

        print("Autointerpretation Start")

        prev_speci = self.s

        for specimen in self.specimens:

            self.s = specimen

            if self.COORDINATE_SYSTEM=='geographic':
                block=self.Data[specimen]['zijdblock_geo']
            elif self.COORDINATE_SYSTEM=='tilt-corrected':
                block=self.Data[specimen]['zijdblock_tilt']
            else:
                block=self.Data[specimen]['zijdblock']
            if step_size==None:
                step_size = int(len(block)/10 + .5)
                if step_size < 3: step_size = 3
            temps = []
            mads = []
            for i in range(len(block)-step_size):
                if block[i][5] == 'b': continue
                try: mpars = pmag.domean(block,i,i+step_size,calculation_type)
                except TypeError: continue
                except IndexError: continue
                if 'specimen_mad' in mpars.keys():
                    temps.append(block[i][0])
                    mads.append(mpars['specimen_mad'])

            peaks = find_peaks_cwt(array(mads),arange(5,10))
            len_temps = len(self.Data[specimen]['zijdblock_steps'])
            peaks = [0] + peaks + [len(temps)]

            prev_peak = peaks[0]
            for peak in peaks[1:]:
                if peak - prev_peak < 3: prev_peak = peak; continue
                tmin = self.Data[specimen]['zijdblock_steps'][prev_peak]
                tmax = self.Data[specimen]['zijdblock_steps'][peak]
                if calculation_type=="DE-BFL": PCA_type="line"
                elif calculation_type=="DE-BFL-A": PCA_type="line-anchored"
                elif calculation_type=="DE-BFL-O": PCA_type="line-with-origin"
                elif calculation_type=="DE-FM": PCA_type="Fisher"
                elif calculation_type=="DE-BFP": PCA_type="plane"
                self.PCA_type_box.SetValue(PCA_type)
                self.add_fit(event,plot_new_fit=False)
                new_fit = self.pmag_results_data['specimens'][specimen][-1]
                new_fit.put(specimen,self.COORDINATE_SYSTEM,self.get_PCA_parameters(specimen,new_fit,tmin,tmax,self.COORDINATE_SYSTEM,calculation_type))
                prev_peak = peak

        self.s = prev_speci
        if self.pmag_results_data['specimens'][self.s] != []:
            self.current_fit = self.pmag_results_data['specimens'][self.s][-1]
        else: self.current_fit = None
        print("Autointerpretation Complete")
        self.update_selection()

    def calculate_high_level_mean (self,high_level_type,high_level_name,calculation_type,elements_type,mean_fit):
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
                            if mean_fit == 'All' or mean_fit == fit.name:
                                pars = fit.get(dirtype)
                                if pars == {} or pars == None:
                                    pars = self.get_PCA_parameters(element,fit,fit.tmin,fit.tmax,dirtype,fit.PCA_type)
                                    if pars == {} or pars == None:
                                        print("cannot calculate parameters for element %s and fit %s in calculate_high_level_mean leaving out of fisher mean, please check this value."%(element,fit.name))
                                        continue
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
                                print("-E- ERROR: cant find mean for specimen interpertation: %s , %s"%(element,fit.name))
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
                        pars=self.high_level_means[elements_type][element][mean_fit][dirtype]
                        if "dec" in pars.keys() and "inc" in pars.keys():
                            dec,inc,direction_type=pars["dec"],pars["inc"],'l'
                        else:
#                            print "-E- ERROR: cant find mean for element %s"%element
                            continue
                    except KeyError:
#                        print("KeyError in calculate_high_level_mean for element: " + str(element) + " please report to a dev")
                        continue

            for key in pars_for_mean.keys():
#                if len(pars_for_mean[key]) > 0 and key != "All":
#                    if high_level_name not in self.pmag_results_data[high_level_type].keys():
#                        self.pmag_results_data[high_level_type][high_level_name] = []
#                    if key not in map(lambda x: x.name, self.pmag_results_data[high_level_type][high_level_name]):
#                        self.pmag_results_data[high_level_type][high_level_name].append(Fit(key, None, None, colors_for_means[key], self))
#                        key_index = -1
#                    else:
#                        key_index = map(lambda x: x.name, self.pmag_results_data[high_level_type][high_level_name]).index(key)
#                    new_pars = self.calculate_mean(pars_for_mean[key],calculation_type)
#                    map_keys = new_pars.keys()
#                    map_keys.remove("calculation_type")
#                    if calculation_type == "Fisher":
#                        for mkey in map_keys:
#                            new_pars[mkey] = float(new_pars[mkey])
#                    print(high_level_type,high_level_name,key_index)
#                    self.pmag_results_data[high_level_type][high_level_name][key_index].put(None, dirtype,new_pars)
                if len(pars_for_mean[key]) > 0:# and key == "All":
                    if mean_fit not in self.high_level_means[high_level_type][high_level_name].keys():
                        self.high_level_means[high_level_type][high_level_name][mean_fit] = {}
                    self.high_level_means[high_level_type][high_level_name][mean_fit][dirtype] = self.calculate_mean(pars_for_mean["All"],calculation_type)
                    color = "black"
                    for specimen in self.pmag_results_data['specimens']:
                        colors = [f.color for f in self.pmag_results_data['specimens'][specimen] if f.name == mean_fit]
                        if colors != []: color = colors[0]
                    self.high_level_means[high_level_type][high_level_name][mean_fit][dirtype]['color'] = color

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

        return mpars

    def calculate_higher_levels_data(self):

        high_level_type=str(self.level_box.GetValue())
        if high_level_type=='sample': high_level_type='samples'
        if high_level_type=='site': high_level_type='sites'
        if high_level_type=='location': high_level_type='locations'
        high_level_name=str(self.level_names.GetValue())
        calculation_type=str(self.mean_type_box.GetValue())
        elements_type=self.UPPER_LEVEL_SHOW
        if self.interpretation_editor_open:
             self.interpretation_editor.mean_type_box.SetStringSelection(calculation_type)
        self.calculate_high_level_mean(high_level_type,high_level_name,calculation_type,elements_type,self.mean_fit)

    def reset_backend(self):
        if not self.data_loss_warning(): return False

        new_Data_info=self.get_data_info()
        new_Data,new_Data_hierarchy=self.get_data()

        if not new_Data:
            print("Data read in failed reseting to old data")
            return
        else:
            self.Data,self.Data_hierarchy,self.Data_info = new_Data,new_Data_hierarchy,new_Data_info

        self.pmag_results_data={}
        for level in ['specimens','samples','sites','locations','study']:
            self.pmag_results_data[level]={}
        self.high_level_means={}

        high_level_means={}
        for high_level in ['samples','sites','locations','study']:
            if high_level not in self.high_level_means.keys():
                self.high_level_means[high_level]={}

        self.specimens=self.Data.keys()         # get list of specimens
        self.specimens.sort(cmp=specimens_comparator) # sort list of specimens
        if len(self.specimens)>0:
            self.s=str(self.specimens[0])
        else:
            self.s=""
        self.samples=self.Data_hierarchy['samples'].keys()         # get list of samples
        self.samples.sort(cmp=specimens_comparator)                   # get list of specimens
        self.sites=self.Data_hierarchy['sites'].keys()         # get list of sites
        self.sites.sort(cmp=specimens_comparator)                   # get list of sites
        self.locations=self.Data_hierarchy['locations'].keys()         # get list of sites
        self.locations.sort()                   # get list of sites

        #----------------------------------------------------------------------
        # initialize first specimen in list as current specimen
        #----------------------------------------------------------------------
        try:
            self.s=str(self.specimens[0])
        except IndexError:
            self.s=""
        try:
            self.sample=self.Data_hierarchy['sample_of_specimen'][self.s]
        except KeyError:
            self.sample=""
        try:
            self.site=self.Data_hierarchy['site_of_specimen'][self.s]
        except KeyError:
            self.site=""

        self.specimens_box.SetItems(self.specimens)
        self.specimens_box.SetStringSelection(str(self.s))

        if self.Data:
            self.update_pmag_tables()
            if not self.current_fit:
                self.update_selection()
            else:
                self.Add_text()
                self.update_fit_boxes()

        if self.interpretation_editor_open:
            self.interpretation_editor.specimens_list = self.specimens
            self.interpretation_editor.update_editor()

    def recalculate_current_specimen_interpreatations(self):
        self.initialize_CART_rot(self.s)
        if str(self.s) in self.pmag_results_data['specimens']:
            for fit in self.pmag_results_data['specimens'][self.s]:
                if fit.get('specimen') and 'calculation_type' in fit.get('specimen'):
                    fit.put(self.s,'specimen',self.get_PCA_parameters(self.s,fit,fit.tmin,fit.tmax,'specimen',fit.get('specimen')['calculation_type']))
                if len(self.Data[self.s]['zijdblock_geo'])>0 and fit.get('geographic') and 'calculation_type' in fit.get('geographic'):
                    fit.put(self.s,'geographic',self.get_PCA_parameters(self.s,fit,fit.tmin,fit.tmax,'geographic',fit.get('geographic')['calculation_type']))
                if len(self.Data[self.s]['zijdblock_tilt'])>0 and fit.get('tilt-corrected') and 'calculation_type' in fit.get('tilt-corrected'):
                    fit.put(self.s,'tilt-corrected',self.get_PCA_parameters(self.s,fit,fit.tmin,fit.tmax,'tilt-corrected',fit.get('tilt-corrected')['calculation_type']))

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
        if specimen not in self.Data:
            print("no measurement data found loaded for specimen %s and will be ignored"%(specimen))
            return (None,None)
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

    def get_indices(self, fit = None, tmin = None, tmax = None, specimen = None):
        """
        Finds the appropriate indices in self.Data[self.s]['zijdplot_steps'] given a set of upper/lower bounds. This is to resolve duplicate steps using the convention that the first good step of that name is the indicated step by that bound if there are no steps of the names tmin or tmax then it complains and reutrns a tuple (None,None).
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
        if specimen not in self.Data.keys(): self.user_warning("No data for specimen " + specimen)
        if tmin in self.Data[specimen]['zijdblock_steps']:
            tmin_index=self.Data[specimen]['zijdblock_steps'].index(tmin)
        elif type(tmin) == str or type(tmin) == unicode and tmin != '':
            int_steps = map(lambda x: float(x.strip("C mT")), self.Data[specimen]['zijdblock_steps'])
            if tmin == '':
                tmin = self.Data[specimen]['zijdblock_steps'][0]
                print("No lower bound for %s on specimen %s using lowest step (%s) for lower bound"%(fit.name, specimen, tmin))
                if fit!=None: fit.tmin = tmin
            int_tmin = float(tmin.strip("C mT"))
            diffs = map(lambda x: abs(x-int_tmin),int_steps)
            tmin_index = diffs.index(min(diffs))
        else: tmin_index=self.tmin_box.GetSelection()
        if tmax in self.Data[specimen]['zijdblock_steps']:
            tmax_index=self.Data[specimen]['zijdblock_steps'].index(tmax)
        elif type(tmax) == str or type(tmax) == unicode and tmax != '':
            int_steps = map(lambda x: float(x.strip("C mT")), self.Data[specimen]['zijdblock_steps'])
            if tmax == '':
                tmax = self.Data[specimen]['zijdblock_steps'][-1]
                print("No upper bound for fit %s on specimen %s using last step (%s) for upper bound"%(fit.name, specimen, tmax))
                if fit!=None: fit.tmax = tmax
            int_tmax = float(tmax.strip("C mT"))
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

        if (tmin_index >= 0):
            while (self.Data[specimen]['measurement_flag'][tmin_index] == 'b' and \
                   tmin_index+1 < len(self.Data[specimen]['zijdblock_steps'])):
                if (self.Data[specimen]['zijdblock_steps'][tmin_index+1] == tmin):
                    tmin_index += 1
                else:
                    tmin_old = tmin
                    while (self.Data[specimen]['measurement_flag'][tmin_index] == 'b' and \
                           tmin_index+1 < len(self.Data[specimen]['zijdblock_steps'])):
                        tmin_index += 1
                    tmin = self.Data[specimen]['zijdblock_steps'][tmin_index]
                    if fit != None: fit.tmin = tmin
                    self.tmin_box.SetStringSelection(tmin)
                    print("For specimen " + str(specimen) + " there are no good measurement steps with value - " + str(tmin_old) + " using step " + str(tmin) + " as lower bound instead")
                    break

        if (tmax_index < max_index):
            while (self.Data[specimen]['measurement_flag'][tmax_index] == 'b' and \
                   tmax_index+1 < len(self.Data[specimen]['zijdblock_steps'])):
                if (self.Data[specimen]['zijdblock_steps'][tmax_index+1] == tmax):
                    tmax_index += 1
                else:
                    tmax_old = tmax
                    while (self.Data[specimen]['measurement_flag'][tmax_index] == 'b' and \
                           tmax_index >= 0):
                        tmax_index -= 1
                    tmax = self.Data[specimen]['zijdblock_steps'][tmax_index]
                    if fit != None: fit.tmax = tmax
                    self.tmax_box.SetStringSelection(tmax)
                    print("For specimen " + str(specimen) + " there are no good measurement steps with value - " + str(tmax_old) + " using step " + str(tmax) + " as upper bound instead")
                    break

        if (tmin_index < 0): tmin_index = 0
        if (tmax_index > max_index): tmax_index = max_index

        return (tmin_index,tmax_index)

    def merge_pmag_recs(self,old_recs):
        # fix the headers of pmag recs
        # make sure that all headers appear in all recs
        recs={}
        recs=deepcopy(old_recs)
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

    #---------------------------------------------#
    #Specimen, Interpretation, & Measurement Alteration
    #---------------------------------------------#

    def select_specimen(self, specimen):
        try: fit_index = self.pmag_results_data['specimens'][self.s].index(self.current_fit)
        except KeyError: fit_index = None
        except ValueError: fit_index = None
        self.initialize_CART_rot(specimen) #sets self.s to specimen calculates params etc.
        if fit_index != None and self.s in self.pmag_results_data['specimens']:
          try: self.current_fit = self.pmag_results_data['specimens'][self.s][fit_index]
          except IndexError: self.current_fit = None
        else: self.current_fit = None

    def new_fit(self):
        """
        finds the bounds of a new fit and calls update_fit_box adding it to the fit comboboxes
        """
        fit = self.pmag_results_data['specimens'][self.s][-1]
        self.current_fit = fit #update current fit to new fit

        if self.interpretation_editor_open:
            self.interpretation_editor.update_editor(True)

        self.update_fit_boxes(True)

        #Draw figures and add  text
        self.get_new_PCA_parameters(1)

    def clear_interpretations(self):

        if self.total_num_of_interpertations() == 0:
            print("There are no interpretations")
            return True

        TEXT="All interpretations will be deleted all unsaved data will be irretrievable"
        self.dlg = wx.MessageDialog(self, caption="Delete?",message=TEXT,style=wx.OK|wx.CANCEL)
        result = self.dlg.ShowModal()
        self.dlg.Destroy()
        if result != wx.ID_OK:
            return False

        for specimen in self.pmag_results_data['specimens'].keys():
            self.pmag_results_data['specimens'][specimen] = []
            ##later on when higher level means are fixed remove the bellow loop and loop over pmag_results_data
            for high_level_type in ['samples','sites','locations','study']:
                self.high_level_means[high_level_type]={}
        if self.interpretation_editor_open:
            self.interpretation_editor.update_editor(True)
        return True

    def mark_meas_good(self,g_index):

        meas_index,ind_data = 0,[]
        for i,meas_data in enumerate(self.mag_meas_data):
            if meas_data['er_specimen_name'] == self.s:
                ind_data.append(i)
        meas_index = ind_data[g_index]

        self.Data[self.s]['measurement_flag'][g_index] = 'g'
        self.Data[self.s]['zijdblock'][g_index][5] = 'g'
        if 'zijdblock_geo' in self.Data[self.s] and g_index < len(self.Data[self.s]['zijdblock_geo']):
            self.Data[self.s]['zijdblock_geo'][g_index][5] = 'g'
        if 'zijdblock_tilt' in self.Data[self.s] and g_index < len(self.Data[self.s]['zijdblock_tilt']):
            self.Data[self.s]['zijdblock_tilt'][g_index][5] = 'g'
        self.mag_meas_data[meas_index]['measurement_flag'] = 'g'

    def mark_meas_bad(self,g_index):

        meas_index,ind_data = 0,[]
        for i,meas_data in enumerate(self.mag_meas_data):
            if meas_data['er_specimen_name'] == self.s:
                ind_data.append(i)
        meas_index = ind_data[g_index]

        self.Data[self.s]['measurement_flag'][g_index] = 'b'
        self.Data[self.s]['zijdblock'][g_index][5] = 'b'
        if 'zijdblock_geo' in self.Data[self.s] and g_index < len(self.Data[self.s]['zijdblock_geo']):
            self.Data[self.s]['zijdblock_geo'][g_index][5] = 'b'
        if 'zijdblock_tilt' in self.Data[self.s] and g_index < len(self.Data[self.s]['zijdblock_tilt']):
            self.Data[self.s]['zijdblock_tilt'][g_index][5] = 'b'
        self.mag_meas_data[meas_index]['measurement_flag'] = 'b'

    #---------------------------------------------#
    #Data Read and Location Alteration Functions
    #---------------------------------------------#

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
      try:
        print("-I- Read magic file  %s"%self.magic_file)
      except ValueError:
        self.magic_measurement = self.choose_meas_file()
        print("-I- Read magic file  %s"%self.magic_file)
      mag_meas_data,file_type=pmag.magic_read(self.magic_file)
      self.mag_meas_data=deepcopy(self.merge_pmag_recs(mag_meas_data))

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
      for rec in self.mag_meas_data:
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
                      print("-E- ERROR: specimen %s has more than one demagnetization experiment name. You need to merge them to one experiment-name?\n")
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
                    print( "-W- cant find sample_azimuth,sample_dip for sample %s\n"%sample)

                 # tilt-corrected coordinates

                 try:
                    sample_bed_dip_direction=float(self.Data_info["er_samples"][sample]['sample_bed_dip_direction'])
                    sample_bed_dip=float(self.Data_info["er_samples"][sample]['sample_bed_dip'])
                    d_tilt,i_tilt=pmag.dotilt(d_geo,i_geo,sample_bed_dip_direction,sample_bed_dip)
                    Data[s]['zijdblock_tilt'].append([tr,d_tilt,i_tilt,intensity,ZI,rec['measurement_flag'],rec['magic_instrument_codes']])
                 except:
                    print("-W- cant find tilt-corrected data for sample %s\n"%sample)


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



      print("-I- done sorting meas data")

      self.specimens=Data.keys()

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
        if NRM == 0: self.user_warning("-E- NRM is 0 cannot normalize magnetic vector magnitude by NRM.")
        for k in range(len(zijdblock)):
            # specimen coordinates
            if len(zijdblock[k]) < 4:
                print("-E- Speciemen measurement data incomplete on entry #%d. Skipping data point"%(k))
                self.user_warning("Speciemen measurement data incomplete on entry #%d. Skipping data point"%(k))
                continue
            DIR=[zijdblock[k][1],zijdblock[k][2],zijdblock[k][3]/NRM]
            cart=pmag.dir2cart(DIR)
            zdata.append(array([cart[0],cart[1],cart[2]]))
            # geographic coordinates
            if len(zijdblock_geo)!=0:
                if len(zijdblock_geo[k]) < 4:
                    print("-E- Geographic measurement data incomplete on entry #%d. Skipping data point"%(k))
                    self.user_warning("Geographic measurement data incomplete on entry #%d. Skipping data point"%(k))
                    continue
                DIR=[zijdblock_geo[k][1],zijdblock_geo[k][2],zijdblock_geo[k][3]/NRM]
                cart=pmag.dir2cart(DIR)
                zdata_geo.append(array([cart[0],cart[1],cart[2]]))
            # tilt-corrected coordinates
            if len(zijdblock_tilt)!=0:
                if len(zijdblock_tilt[k]) < 4:
                    print("-E- Tilt-Corrected measurement data incomplete on entry #%d. Skipping data point"%(k))
                    self.user_warning("Til-Corrected measurement data incomplete on entry #%d. Skipping data point"%(k))
                    continue
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

      return(Data,Data_hierarchy)

    def get_data_info(self):
        Data_info={}
        data_er_samples={}
        data_er_sites={}
        data_er_locations={}
        data_er_ages={}

        try:
            data_er_samples=self.read_magic_file(os.path.join(self.WD, "er_samples.txt"),'er_sample_name')
        except:
            print("-W- Cant find er_sample.txt in project directory")

        try:
            data_er_sites=self.read_magic_file(os.path.join(self.WD, "er_sites.txt"),'er_site_name')
        except:
            print("-W- Cant find er_sites.txt in project directory")

        try:
            data_er_locations=self.read_magic_file(os.path.join(self.WD, "er_locations.txt"), 'er_location_name')
        except:
            print("-W- Cant find er_locations.txt in project directory")

        try:
            data_er_ages=self.read_magic_file(os.path.join(self.WD, "er_ages.txt"),'er_sample_name')
        except:
            try:
                data_er_ages=self.read_magic_file(os.path.join(self.WD, "er_ages.txt"),'er_site_name')
            except:
                print("-W- Cant find er_ages in project directory")



        Data_info["er_samples"]=data_er_samples
        Data_info["er_sites"]=data_er_sites
        Data_info["er_locations"]=data_er_locations
        Data_info["er_ages"]=data_er_ages

        return(Data_info)

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
            print( "-I- zeq_gui.preferences imported")
            preferences.update(thellier_gui_preferences.preferences)
        except:
            print( "-I- cant find zeq_gui_preferences file, using defualt default")
        return(preferences)

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
                print("-E- ERROR: magic file %s has more than one line for %s %s"%(path,sort_by_this_name,tmp_data[sort_by_this_name]))
            DATA[tmp_data[sort_by_this_name]]=tmp_data
        fin.close()
        return(DATA)

    def read_from_LSQ(self,LSQ_file):
        cont = self.user_warning("LSQ import only works if magic_measurements file all measurements are present and not averaged during import from magnetometer files. Do you wish to continue reading interpretations?")
        if not cont: return
        print("Reading LSQ file")
        interps = read_LSQ(LSQ_file)
        for interp in interps:
            specimen = interp['er_specimen_name']
            if specimen not in self.specimens: continue
            PCA_type = interp['magic_method_codes'].split(':')[0]
            tmin = self.Data[specimen]['zijdblock_steps'][interp['measurement_min_index']]
            tmax = self.Data[specimen]['zijdblock_steps'][interp['measurement_max_index']]
            if specimen not in self.pmag_results_data['specimens'].keys():
                self.pmag_results_data['specimens'][specimen] = []
            next_fit = str(len(self.pmag_results_data['specimens'][specimen]) + 1)
            while ('Fit ' + next_fit) in map(lambda x: x.name, self.pmag_results_data['specimens'][specimen]):
                next_fit = str(int(next_fit)+1)
            if 'specimen_comp_name' in interp.keys() and interp['specimen_comp_name'] not in map(lambda x: x.name, self.pmag_results_data['specimens'][specimen]):
                name = interp['specimen_comp_name']
            else:
                name = 'Fit ' + next_fit
            new_fit = Fit(name, tmin, tmax, self.colors[(int(next_fit)-1) % len(self.colors)], self, PCA_type)
            self.pmag_results_data['specimens'][specimen].append(new_fit)
            new_fit.put(specimen,self.COORDINATE_SYSTEM,self.get_PCA_parameters(specimen,new_fit,tmin,tmax,self.COORDINATE_SYSTEM,PCA_type))
            if 'bad_measurement_index' in interp.keys():
                old_s = self.s
                self.s = specimen
                for bmi in interp["bad_measurement_index"]:
                    try: self.mark_meas_bad(bmi)
                    except IndexError: print("Magic Measurments length does not match that recorded in LSQ file")
                self.s = old_s
        self.update_selection()

    def read_redo_file(self,redo_file):
        """
        Read previous interpretation from a redo file
        and update gui with the new interpretation
        """
        if not self.clear_interpretations(): return
        print("-I- read redo file and processing new bounds")
        fin=open(redo_file,'rU')

        for Line in fin.readlines():
            line=Line.strip('\n').split('\t')
            specimen=line[0]
            if specimen not in self.specimens:
                print("specimen %s not found in this data set and will be ignored"%(specimen))
                continue
            self.s = specimen
            if not (self.s in self.pmag_results_data['specimens'].keys()):
                self.pmag_results_data['specimens'][self.s] = []

            tmin,tmax="",""

            calculation_type=line[1]
            tmin,tmax = self.parse_bound_data(line[2],line[3],specimen)
            if tmin == None or tmax == None:
                continue
            if tmin not in self.Data[specimen]['zijdblock_steps'] or  tmax not in self.Data[specimen]['zijdblock_steps']:
                print("-E- ERROR in redo file specimen %s. Cant find treatment steps"%specimen)

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
                    self.pmag_results_data['specimens'][self.s].append(Fit('Fit ' + next_fit, tmax, tmin, color, self))
                fit = self.pmag_results_data['specimens'][specimen][fit_index];
                fit.name = line[4]
                try:
                    if line[6] == "b":
                        self.bad_fits.append(fit)
                except IndexError: pass
            else:
                next_fit = str(len(self.pmag_results_data['specimens'][self.s]) + 1)
                self.pmag_results_data['specimens'][self.s].append(Fit('Fit ' + next_fit, tmax, tmin, self.colors[(int(next_fit)-1) % len(self.colors)], self))
                fit = self.pmag_results_data['specimens'][specimen][-1]

            fit.put(specimen,self.COORDINATE_SYSTEM,self.get_PCA_parameters(specimen,fit,tmin,tmax,self.COORDINATE_SYSTEM,calculation_type))

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

    def read_inp(self,inp_file_name,magic_files):
        inp_file = open(inp_file_name, "r")
        new_inp_file = ""

        lines = inp_file.read().split("\n")
        if len(lines) < 3: print(".inp file improperly formated"); return
        new_inp_file = lines[0] + "\n" + lines[1] + "\n"
        [lines.remove('') for i in range(lines.count(''))]
        format = lines[0].strip()
        header = lines[1].split('\t')
        update_files = lines[2:]
        for i,update_file in enumerate(update_files):
            update_lines = update_file.split('\t')
            if not os.path.isfile(update_lines[0]):
                print("%s does not exist and will be skipped"%(update_lines[0]))
                continue
            d = reduce(lambda x,y: x+"/"+y, update_lines[0].split("/")[:-1])+"/"
            f = update_lines[0].split("/")[-1].split(".")[0] + ".magic"
            if (d+f) in magic_files:
                new_inp_file += update_file+"\n"
                continue
            if float(update_lines[-1]) >= os.path.getctime(update_lines[0]):
                if os.path.isfile(d+f):
                    magic_files.append(d+f)
                    new_inp_file += update_file+"\n"
                    continue
            if len(header) != len(update_lines):
                print("length of header and length of enteries for the file %s are different and will be skipped"%(update_lines[0]))
                new_inp_file += update_file+"\n"
                continue
            update_dict = {}
            for head,entry in zip(header,update_lines):
                update_dict[head] = entry
            if format == "CIT":
                CIT_kwargs = {}
                CIT_name = update_dict["sam_path"].split("/")[-1].split(".")[0]

                CIT_kwargs["dir_path"] = self.WD + "/"#reduce(lambda x,y: x+"/"+y, update_dict["sam_path"].split("/")[:-1])
                CIT_kwargs["user"] = ""
                CIT_kwargs["meas_file"] = CIT_name + ".magic"
                CIT_kwargs["spec_file"] = CIT_name + "_er_specimens.txt"
                CIT_kwargs["samp_file"] = CIT_name + "_er_samples.txt"
                CIT_kwargs["site_file"] = CIT_name + "_er_sites.txt"
                CIT_kwargs["locname"] = update_dict["location"]
                CIT_kwargs["methods"] = update_dict["field_magic_codes"]
                CIT_kwargs["specnum"] = update_dict["num_terminal_char"]
                CIT_kwargs["avg"] = update_dict["dont_average_replicate_measurements"]
                CIT_kwargs["samp_con"] = update_dict["naming_convention"]
                CIT_kwargs["peak_AF"] = update_dict["peak_AF"]
                CIT_kwargs["magfile"] = update_dict["sam_path"].split("/")[-1]
                CIT_kwargs["input_dir_path"] = reduce(lambda x,y: x+"/"+y, update_dict["sam_path"].split("/")[:-1])

                program_ran, error_message = cit_magic.main(command_line=False, **CIT_kwargs)

                if program_ran:
                    update_lines[-1] = time()
                    new_inp_file += reduce(lambda x,y: str(x)+"\t"+str(y), update_lines)+"\n"
                    magic_files.append(CIT_kwargs["dir_path"]+CIT_kwargs["meas_file"])
                else:
                    new_inp_file += update_file
                    if os.path.isfile(CIT_kwargs["dir_path"]+CIT_kwargs["meas_file"]):
                        magic_files.append(CIT_kwargs["dir_path"]+CIT_kwargs["meas_file"])

        inp_file.close()
        out_file = open(inp_file_name, "w")
        out_file.write(new_inp_file)

    def get_all_inp_files(self,WD=None):
        if WD == None: WD = self.WD
        try:
            all_inp_files = []
            for root, dirs, files in os.walk(WD):
                for d in dirs:
                    all_inp_files += self.get_all_inp_files(d)
                for f in files:
                    if f.endswith(".inp"):
                         all_inp_files.append(os.path.join(root, f))
            return all_inp_files
        except RuntimeError:
            print("Recursion depth exceded, please use different working directory there are too many sub-directeries to walk")

    def change_WD(self,new_WD):
        if not os.path.isdir(new_WD): return
        self.WD = new_WD
        os.chdir(self.WD)
        self.WD=os.getcwd()
        meas_file = os.path.join(self.WD, "magic_measurements.txt")
        if os.path.isfile(meas_file): self.magic_file=meas_file
        else: self.magic_file = self.choose_meas_file()

    #---------------------------------------------#
    #Data Writing Functions
    #---------------------------------------------#

    def init_log_file(self):
        """
        redirects stdout to a log file to prevent printing to a hanging terminal when dealing with the compiled binary.
        """
        #redirect terminal output
        self.old_stdout = sys.stdout
        sys.stdout = open(os.path.join(self.WD, "demag_gui.log"),'w+')

    def close_log_file(self):
        """
        if log file has been opened and you wish to stop printing to file but back to terminal this function redirects stdout back to origional output.
        """
        try:
            sys.stdout = self.old_stdout
        except AttributeError:
            print("Log file was never openned it cannot be closed")

    def update_pmag_tables(self):

        pmag_specimens,pmag_samples,pmag_sites=[],[],[]
        try:
            pmag_specimens,file_type=pmag.magic_read(os.path.join(self.WD, "pmag_specimens.txt"))
        except:
            print("-I- Cant read pmag_specimens.txt")
        try:
            pmag_samples,file_type=pmag.magic_read(os.path.join(self.WD, "pmag_samples.txt"))
        except:
            print("-I- Cant read pmag_samples.txt")
        try:
            pmag_sites,file_type=pmag.magic_read(os.path.join(self.WD, "pmag_sites.txt"))
        except:
            print("-I- Cant read pmag_sites.txt")
        print("-I- Reading previous interpretations from pmag* tables\n")
        #--------------------------
        # reads pmag_specimens.txt and
        # update pmag_results_data['specimens'][specimen]
        # with the new interpretation
        #--------------------------

        if self.COORDINATE_SYSTEM == 'geographic': current_tilt_correction = 0
        elif self.COORDINATE_SYSTEM == 'tilt-corrected': current_tilt_correction = 100
        else: current_tilt_correction = -1

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

            methods=rec['magic_method_codes'].strip("\n").replace(" ","").split(":")
            LPDIR=False;calculation_type=""

            for method in methods:
                if "LP-DIR" in method:
                    LPDIR=True
                if "DE-" in method:
                    calculation_type=method

            if LPDIR: # this a mean of directions

                #if interpretation doesn't exsist create it.
                if 'specimen_comp_name' in rec.keys():
                    if rec['specimen_comp_name'] not in map(lambda x: x.name, self.pmag_results_data['specimens'][specimen]) and int(rec['specimen_tilt_correction']) == current_tilt_correction:
                        next_fit = str(len(self.pmag_results_data['specimens'][self.s]) + 1)
                        color = self.colors[(int(next_fit)-1) % len(self.colors)]
                        self.pmag_results_data['specimens'][self.s].append(Fit(rec['specimen_comp_name'], None, None, color, self))
                        fit = self.pmag_results_data['specimens'][specimen][-1]
                    else:
                        fit = None
                else:
                    if int(rec['specimen_tilt_correction']) == current_tilt_correction:
                        next_fit = str(len(self.pmag_results_data['specimens'][self.s]) + 1)
                        color = self.colors[(int(next_fit)-1) % len(self.colors)]
                        self.pmag_results_data['specimens'][self.s].append(Fit('Fit ' + next_fit, None, None, color, self))
                        fit = self.pmag_results_data['specimens'][specimen][-1]
                    else: fit = None


                if 'specimen_flag' in rec and rec['specimen_flag'] == 'b':
                    self.bad_fits.append(fit)

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
                            fit.put(specimen,'specimen',self.get_PCA_parameters(specimen,fit,tmin,tmax,'specimen',calculation_type))

                            if len(self.Data[specimen]['zijdblock_geo'])>0:
                                fit.put(specimen,'geographic',self.get_PCA_parameters(specimen,fit,tmin,tmax,'geographic',calculation_type))

                            if len(self.Data[specimen]['zijdblock_tilt'])>0:
                                fit.put(specimen,'tilt-corrected',self.get_PCA_parameters(specimen,fit,tmin,tmax,'tilt-corrected',calculation_type))

                    else:
                        print( "-W- WARNING: Cant find specimen and steps of specimen %s tmin=%s, tmax=%s"%(specimen,tmin,tmax))

        #BUG FIX-almost replaced first sample with last due to above assignment to self.s
        if self.specimens:
            self.s = self.specimens[0]
            self.specimens_box.SetSelection(0)
        if self.s in self.pmag_results_data['specimens'] and self.pmag_results_data['specimens'][self.s]:
            self.initialize_CART_rot(self.specimens[0])
            self.pmag_results_data['specimens'][self.s][-1].select()



        #--------------------------
        # reads pmag_sample.txt and
        # if finds a mean in pmag_samples.txt
        # calculate the mean for self.high_level_means['samples'][samples]
        # If the program finds a codes "DE-FM","DE-FM-LP","DE-FM-UV"in magic_method_codes
        # then the program repeat teh fisher mean
        #--------------------------

        for rec in pmag_samples:
            if "magic_method_codes" in rec.keys():
                methods=rec['magic_method_codes'].strip("\n").replace(" ","").split(":")
            else:
                methods=""
            sample=rec['er_sample_name'].strip("\n")
            LPDIR=False;calculation_method=""
            for method in methods:
                if "LP-DIR" in method:
                    LPDIR=True
                if "DE-" in method:
                    calculation_method=method
            if LPDIR: # this a mean of directions
                calculation_type="Fisher"
                for dirtype in self.dirtypes:
                    self.calculate_high_level_mean('samples',sample,calculation_type,'specimens',self.mean_fit)

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
            elements_type = "specimens"
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
                self.calculate_high_level_mean('sites',site,calculation_type,elements_type,self.mean_fit)

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

    def combine_magic_files(self,magic_files):
        if ipmag.combine_magic(magic_files, self.WD+"/magic_measurements.txt"):
            print("recalculated magic files have been recombine to %s"%(self.WD+"/magic_measurements.txt"))
        else: print("trouble combining magic files to %s"%(self.WD+"/magic_measurements.txt"))

#==========================================================================================#
#============================Interal Dialog Functions======================================#
#==========================================================================================#

    def get_DIR(self):
        """
        Choose a working directory dialog
        """

        self.dlg = wx.DirDialog(self, "Choose a directory:",defaultPath = self.currentDirectory ,style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON | wx.DD_CHANGE_DIR)
        ok = self.dlg.ShowModal()
        if ok == wx.ID_OK:
            new_WD=self.dlg.GetPath()
            self.dlg.Destroy()
        else:
            new_WD = os.getcwd()
            self.dlg.Destroy()
        return new_WD

    def choose_meas_file(self):
        self.dlg = wx.FileDialog(
            self, message="No magic_measurements.txt found. Please choose a magic measurement file",
            defaultDir=self.WD,
            defaultFile="magic_measurements.txt",
            wildcard="*.magic|*.txt",
            style=wx.OPEN | wx.CHANGE_DIR
            )
        if self.dlg.ShowModal() == wx.ID_OK:
            meas_file = self.dlg.GetPath()
            self.dlg.Destroy()
        else:
            meas_file = None
            self.dlg.Destroy()
        return meas_file

    def user_warning(self, message, caption = 'Warning!'):
        dlg = wx.MessageDialog(self, message, caption, wx.OK | wx.CANCEL | wx.ICON_WARNING)
        if dlg.ShowModal() == wx.ID_OK:
            continue_bool = True
        else:
            continue_bool = False
        dlg.Destroy()
        return continue_bool

    def data_loss_warning(self):
        TEXT="This action could result in a loss of all unsaved data. Would you like to continue"
        self.dlg = wx.MessageDialog(self,caption="Warning:", message=TEXT ,style=wx.OK|wx.CANCEL|wx.ICON_EXCLAMATION)
        if self.dlg.ShowModal() == wx.ID_OK:
            continue_bool = True
        else:
            continue_bool = False
        self.dlg.Destroy()
        return continue_bool

    def pick_inp(self):
        self.dlg = wx.FileDialog(
            self, message="choose .inp file",
            defaultDir=self.WD,
            defaultFile="magic.inp",
            wildcard="*.inp",
            style=wx.OPEN
            )
        if self.dlg.ShowModal() == wx.ID_OK:
            inp_file_name = self.dlg.GetPath()
        else:
            inp_file_name = None
        self.dlg.Destroy()
        return inp_file_name

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
        self.dlg = wx.MessageDialog(self,caption="Warning:", message="Canges are saved to pmag_criteria.txt\n " ,style=wx.OK)
        result = self.dlg.ShowModal()
        if result == wx.ID_OK:
            self.write_acceptance_criteria_to_file()
            self.dlg.Destroy()
            dia.Destroy()

    def show_crit_window_err_messege(self,crit):
        '''
        error message if a valid naumber is not entered to criteria dialog boxes
        '''
        self.dlg = wx.MessageDialog(self,caption="Error:",message="not a vaild value for statistic %s\n ignoring value"%crit ,style=wx.OK)
        result = self.dlg.ShowModal()
        if result == wx.ID_OK:
            self.dlg.Destroy()

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
                max_age="%f"%((time()/3.15569e7)+1970)
            elif age_units=="Years BP":
                max_age="%f"%((time()/3.15569e7)+1950)
            elif age_units=="Years Cal AD (+/-)":
                max_age=str(datetime.now())
            elif age_units=="Years Cal BP":
                max_age=((time()/3.15569e7)+1950)
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
                print("-I- Read old magic file  %s\n"%os.path.join(self.WD, FILE))
                if FILE !='pmag_specimens.txt':
                    os.remove(os.path.join(self.WD, FILE))
                    print("-I- Delete old magic file  %s\n"%os.path.join(self.WD,FILE))
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

        print('coord', coord, 'vgps_level', vgps_level, 'DefaultAge', DefaultAge, 'avg_directions_by_sample', avg_directions_by_sample, 'avg_by_polarity', avg_by_polarity, 'use_criteria', use_criteria)
        ipmag.specimens_results_magic(coord=coord, vgps_level=vgps_level, DefaultAge=DefaultAge, avg_directions_by_sample=avg_directions_by_sample, avg_by_polarity=avg_by_polarity, use_criteria=use_criteria)

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
                print( "write new interpretations in %s\n"%(os.path.join(self.WD, FILE)))

        # make pmag_criteria.txt if it does not exist
        if not os.path.isfile(os.path.join(self.WD, "pmag_criteria.txt")):
            Fout=open(os.path.join(self.WD, "pmag_criteria.txt"),'w')
            Fout.write("tab\tpmag_criteria\n")
            Fout.write("er_citation_names\tpmag_criteria_code\n")
            Fout.write("This study\tACCEPT\n")


        self.update_pmag_tables()
        self.update_selection()
        TEXT="interpretations are saved in pmag tables.\n"
        self.dlg = wx.MessageDialog(self, caption="Saved",message=TEXT,style=wx.OK)
        result = self.dlg.ShowModal()
        if result == wx.ID_OK:
            self.dlg.Destroy()

        self.close_warning=False

#==========================================================================================#
#=============================Update Panel Functions=======================================#
#==========================================================================================#

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
        if self.interpretation_editor_open and new_string!=old_string:
            self.interpretation_editor.level_names.SetValue(new_string)
            self.interpretation_editor.on_select_level_name(-1,True)

        self.update_PCA_box()

        if self.current_fit:
            self.draw_figure(self.s,False)
        else:
            self.draw_figure(self.s,True)

        self.update_fit_boxes()
        # measurements text box
        self.Add_text()
        #update higher level stats
        self.update_higher_level_stats()
        #redraw interpretations
        self.update_GUI_with_new_interpretation()

    def update_GUI_with_new_interpretation(self):
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
        if high_level_name in self.high_level_means[high_level_type].keys():
            if self.mean_fit in self.high_level_means[high_level_type][high_level_name].keys():
                if dirtype in self.high_level_means[high_level_type][high_level_name][self.mean_fit].keys():
                    mpars=self.high_level_means[high_level_type][high_level_name][self.mean_fit][dirtype]
                    self.show_higher_levels_pars(mpars)

    def update_temp_boxes(self):
        if self.s not in self.Data.keys():
            self.s = self.Data.keys()[0]
        self.T_list=self.Data[self.s]['zijdblock_steps']
        if self.current_fit:
            self.tmin_box.SetItems(self.T_list)
            self.tmax_box.SetItems(self.T_list)
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

    def update_fit_boxes(self, new_fit = False):
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

    def show_higher_levels_pars(self,mpars):

        FONT_RATIO=self.GUI_RESOLUTION+(self.GUI_RESOLUTION-1)*5
        font2 = wx.Font(12+min(1,FONT_RATIO), wx.SWISS, wx.NORMAL, wx.NORMAL, False, self.font_type)

        if not mpars or len(mpars)==1: print("No parameters to display for higher level mean"); return

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

    def clear_higher_level_pars(self):
        for val in ['mean_type','dec','inc','alpha95','K','R','n_lines','n_planes']:
            COMMAND = """self.%s_window.SetValue("")"""%(val)
            exec COMMAND
        if self.interpretation_editor_open:
            ie = self.interpretation_editor
            for val in ['mean_type','dec','inc','alpha95','K','R','n_lines','n_planes']:
                COMMAND = """ie.%s_window.SetValue("")"""%(val)
                exec COMMAND

    def MacReopenApp(self):
        """Called when the doc icon is clicked"""
        self.GetTopWindow().Raise()

#==========================================================================================#
#=================================Menu Functions===========================================#
#==========================================================================================#

    #---------------------------------------------#
    #File Menu Functions
    #---------------------------------------------#

    def on_menu_pick_read_inp(self, event):
        inp_file_name = self.pick_inp()
        if inp_file_name == None: return
        magic_files = []
        self.read_inp(inp_file_name,magic_files)
        self.combine_magic_files(magic_files)
        self.reset_backend()

    def on_menu_read_all_inp(self, event):
        inp_file_names = self.get_all_inp_files()
        if inp_file_name == []: return

        magic_files = []
        for inp_file_name in inp_file_names:
            self.read_inp(inp_file_name,magic_files)
        self.combine_magic_files(magic_files)
        self.reset_backend()

    def on_menu_make_MagIC_results_tables(self,event):
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
                print("-I- Read old magic file  %s\n"%os.path.join(self.WD, FILE))
                #if FILE !='pmag_specimens.txt':
                os.remove(os.path.join(self.WD,FILE))
                print("-I- Delete old magic file  %s\n"%os.path.join(self.WD,FILE))

            except OSError:
                continue
            except IOError:
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
                        mpars = self.get_PCA_parameters(specimen,fit,fit.tmin,fit.tmax,dirtype,fit.PCA_type)
                        if not mpars: print("Could not calculate interpretation for specimen %s and fit %s while exporting pmag tables, skipping"%(specimen,fit.name));continue

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
        print( "specimen data stored in %s\n"%os.path.join(self.WD, "pmag_specimens.txt"))

        TEXT="specimens interpretations are saved in pmag_specimens.txt.\nPress OK for pmag_samples/pmag_sites/pmag_results tables."
        self.dlg = wx.MessageDialog(self, caption="Saved",message=TEXT,style=wx.OK|wx.CANCEL)
        result = self.dlg.ShowModal()
        if result == wx.ID_OK:
            self.dlg.Destroy()
        if result == wx.ID_CANCEL:
            self.dlg.Destroy()
            return

        #--------------------------------

        dia = demag_dialogs.magic_pmag_tables_dialog(None,self.WD,self.Data,self.Data_info)
        dia.Center()

        if dia.ShowModal() == wx.ID_OK: # Until the user clicks OK, show the message
            self.On_close_MagIC_dialog(dia)

    def on_save_Zij_plot(self, event):
        self.current_fit = None
        self.draw_interpretation()
        self.plot_higher_levels_data()
        self.fig1.text(0.9,0.98,'%s'%(self.s),{'family':self.font_type, 'fontsize':10, 'style':'normal','va':'center', 'ha':'right' })
        SaveMyPlot(self.fig1,self.s,"Zij",self.WD)
#        self.fig1.clear()
        self.draw_figure(self.s)
        self.update_selection()

    def on_save_Eq_plot(self, event):
        self.current_fit = None
        self.draw_interpretation()
        self.plot_higher_levels_data()
        #self.fig2.text(0.9,0.96,'%s'%(self.s),{'family':self.font_type, 'fontsize':10, 'style':'normal','va':'center', 'ha':'right' })
        #self.canvas4.print_figure("./tmp.pdf")#, dpi=self.dpi)
        SaveMyPlot(self.fig2,self.s,"EqArea",self.WD)
#        self.fig2.clear()
        self.draw_figure(self.s)
        self.update_selection()

    def on_save_M_t_plot(self, event):
        self.current_fit = None
        self.draw_interpretation()
        self.plot_higher_levels_data()
        self.fig3.text(0.9,0.96,'%s'%(self.s),{'family':self.font_type, 'fontsize':10, 'style':'normal','va':'center', 'ha':'right' })
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
        self.dlg = wx.DirDialog(self, "choose a folder:",defaultPath = self.WD ,style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON | wx.DD_CHANGE_DIR)
        if self.dlg.ShowModal() == wx.ID_OK:
              dir_path=self.dlg.GetPath()
              self.dlg.Destroy()

        #figs=[self.fig1,self.fig2,self.fig3,self.fig4]
        plot_types=["Zij","EqArea","M_M0",str(self.level_box.GetValue())]
        #elements=[self.s,self.s,self.s,str(self.level_names.GetValue())]
        for i in range(4):
            try:
                if plot_types[i]=="Zij":
                    self.fig1.text(0.9,0.98,'%s'%(self.s),{'family':self.font_type, 'fontsize':10, 'style':'normal','va':'center', 'ha':'right' })
                    SaveMyPlot(self.fig1,self.s,"Zij",dir_path)
                if plot_types[i]=="EqArea":
                    SaveMyPlot(self.fig2,self.s,"EqArea",dir_path)
                if plot_types[i]=="M_M0":
                    self.fig3.text(0.9,0.96,'%s'%(self.s),{'family':self.font_type, 'fontsize':10, 'style':'normal','va':'center', 'ha':'right' })
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
        old_WD = self.WD
        new_WD = self.get_DIR()
        self.change_WD(new_WD)
        print("Working Directory altered from %s to %s, all output will be sent here"%(old_WD,new_WD))

    def on_menu_exit(self, event):

        #check if interpretations have changed and were not saved
        write_session_to_failsafe = False
        try:
            number_saved_fits = sum(1 for line in open("demag_gui.redo"))
            number_current_fits = sum(len(self.pmag_results_data['specimens'][specimen]) for specimen in self.pmag_results_data['specimens'].keys())
            #break if there are no fits there's no need to save an empty file
            if number_current_fits == 0: raise RuntimeError("get out and don't write, lol this is such a hack")
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
            self.dlg = wx.MessageDialog(self,caption="Warning:", message=TEXT ,style=wx.OK|wx.CANCEL|wx.ICON_EXCLAMATION)
            if self.dlg.ShowModal() == wx.ID_OK:
                self.dlg.Destroy()
                if self.interpretation_editor_open:
                    self.interpretation_editor.on_close_edit_window(event)
                self.Destroy()
        else:
            if self.interpretation_editor_open:
                self.interpretation_editor.on_close_edit_window(event)
            self.close_log_file()
            self.Destroy()

    #---------------------------------------------#
    #Edit Menu Functions
    #---------------------------------------------#

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

    def on_menu_flag_meas_good(self, event):
        next_i = self.logger.GetNextSelected(-1)
        while next_i != -1:
            self.mark_meas_good(next_i)
            next_i = self.logger.GetNextSelected(next_i)

        pmag.magic_write(os.path.join(self.WD, "magic_measurements.txt"),self.mag_meas_data,"magic_measurements")

        self.recalculate_current_specimen_interpreatations()

        if self.interpretation_editor_open:
            self.interpretation_editor.update_current_fit_data()
        self.calculate_higher_levels_data()
        self.update_selection()

    def on_menu_flag_meas_bad(self, event):
        next_i = self.logger.GetNextSelected(-1)
        while next_i != -1:
            self.mark_meas_bad(next_i)
            next_i = self.logger.GetNextSelected(next_i)

        pmag.magic_write(os.path.join(self.WD, "magic_measurements.txt"),self.mag_meas_data,"magic_measurements")

        self.recalculate_current_specimen_interpreatations()

        if self.interpretation_editor_open:
            self.interpretation_editor.update_current_fit_data()
        self.calculate_higher_levels_data()
        self.update_selection()

    #---------------------------------------------#
    #Analysis Menu Functions
    #---------------------------------------------#

    def on_menu_previous_interpretation(self,event):
        """
        Create and show the Open FileDialog for upload previous interpretation
        input should be a valid "redo file":
        [specimen name] [tmin(kelvin)] [tmax(kelvin)]
        or
        [specimen name] [tmin(Tesla)] [tmax(Tesla)]
        There is a problem with experiment that combines AF and thermal
        """
        self.dlg = wx.FileDialog(
            self, message="choose a file in a pmagpy redo format",
            defaultDir=self.WD,
            defaultFile="demag_gui.redo",
            wildcard="*.redo",
            style=wx.OPEN | wx.CHANGE_DIR
            )
        if self.dlg.ShowModal() == wx.ID_OK:
            redo_file = self.dlg.GetPath()
        else:
            redo_file = None
        self.dlg.Destroy()

        if redo_file:
            self.read_redo_file(redo_file)

    def on_menu_read_from_LSQ(self,event):
        self.dlg = wx.FileDialog(
            self, message="choose a LSQ file",
            defaultDir=self.WD,
            wildcard="*.LSQ",
            style=wx.OPEN
            )
        if self.dlg.ShowModal() == wx.ID_OK:
            LSQ_file = self.dlg.GetPath()
        else:
            LSQ_file = None
        self.dlg.Destroy()

        self.read_from_LSQ(LSQ_file)

    def on_menu_save_interpretation(self,event,redo_file_name = "demag_gui.redo"):
        fout=open(redo_file_name,'w')
        specimens_list=self.pmag_results_data['specimens'].keys()
        specimens_list.sort(cmp=specimens_comparator)
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
        fout.close()
        TEXT="specimens interpretations are saved in " + redo_file_name
        self.dlg = wx.MessageDialog(self, caption="Saved",message=TEXT,style=wx.OK|wx.CANCEL )
        result = self.dlg.ShowModal()
        if result == wx.ID_OK:
            self.dlg.Destroy()

    def on_menu_change_criteria(self, event):
        dia=demag_dialogs.demag_criteria_dialog(None,self.acceptance_criteria,title='PmagPy Demag Gui Acceptance Criteria')
        dia.Center()
        if dia.ShowModal() == wx.ID_OK: # Until the user clicks OK, show the message
            self.on_close_criteria_box(dia)

    def on_menu_criteria_file (self, event):
        """
        read pmag_criteria.txt file
        and open changecriteria dialog
        """
        read_sucsess=False
        self.dlg = wx.FileDialog(
            self, message="choose pmag criteria file",
            defaultDir=self.WD,
            defaultFile="pmag_criteria.txt",
            style=wx.OPEN | wx.CHANGE_DIR
            )
        if self.dlg.ShowModal() == wx.ID_OK:
            criteria_file = self.dlg.GetPath()
            print("-I- Read new criteria file: %s"%criteria_file)

            # check if this is a valid pmag_criteria file
            try:
                mag_meas_data,file_type=pmag.magic_read(criteria_file)
            except:
                self.dlg = wx.MessageDialog(self, caption="Error",message="not a valid pmag_criteria file",style=wx.OK)
                result = self.dlg.ShowModal()
                if result == wx.ID_OK:
                    self.dlg.Destroy()
                self.dlg.Destroy()
                return

            # initialize criteria
            self.acceptance_criteria=pmag.initialize_acceptance_criteria()
            self.acceptance_criteria=pmag.read_criteria_from_file(criteria_file,self.acceptance_criteria)
            read_sucsess=True

        self.dlg.Destroy()
        if read_sucsess:
            self.on_menu_change_criteria(None)

    #---------------------------------------------#
    #Tools Menu  Functions
    #---------------------------------------------#

    def on_menu_edit_interpretations(self,event):
        if not self.interpretation_editor_open:
            self.interpretation_editor = InterpretationEditorFrame(self)
            self.interpretation_editor_open = True
            self.update_higher_level_stats()
            self.interpretation_editor.Center()
            self.interpretation_editor.Show(True)
            if self.parent==None and sys.platform.startswith('darwin'):
                TEXT="This is a refresher window for mac os to insure that wx opens the new window"
                self.dlg = wx.MessageDialog(self, caption="Open",message=TEXT,style=wx.OK | wx.ICON_INFORMATION | wx.STAY_ON_TOP )
                self.dlg.ShowModal()
                self.dlg.Destroy()
        else:
            self.interpretation_editor.ToggleWindowStyle(wx.STAY_ON_TOP)
            self.interpretation_editor.ToggleWindowStyle(wx.STAY_ON_TOP)

    #---------------------------------------------#
    #Help Menu Functions
    #---------------------------------------------#

    def on_menu_docs(self,event):
        """
        opens in library documentation for the usage of demag gui in a pdf/latex form
        @param: event -> the wx.MenuEvent that triggered this function
        """
        webopen("http://earthref.org/PmagPy/cookbook/#demag_gui.py", new=2)

    def on_menu_cookbook(self,event):
        webopen("http://earthref.org/PmagPy/cookbook/", new=2)

    def on_menu_git(self,event):
        webopen("https://github.com/ltauxe/PmagPy", new=2)

    def on_menu_debug(self,event):
        self.close_log_file()
        pdb.set_trace()

#==========================================================================================#
#===========================Panel Interaction Functions====================================#
#==========================================================================================#

    #---------------------------------------------#
    #Arrow Key Binding Functions
    #---------------------------------------------#

    def arrow_keys(self):
        self.panel.Bind(wx.EVT_CHAR, self.onCharEvent)

    def onCharEvent(self, event):
        keycode = event.GetKeyCode()

        if keycode == wx.WXK_RIGHT or keycode == wx.WXK_NUMPAD_RIGHT or keycode == wx.WXK_WINDOWS_RIGHT:
            self.on_next_button(None)
        elif keycode == wx.WXK_LEFT or keycode == wx.WXK_NUMPAD_LEFT or keycode == wx.WXK_WINDOWS_LEFT:
            self.on_prev_button(None)
        event.Skip()

    #---------------------------------------------#
    #Figure Control Functions
    #---------------------------------------------#

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
        (currently unsupported)
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
        reverse = inv.transform(vstack([pos[0],pos[1]]).T)
        xpick_data,ypick_data = reverse.T
        pos = (xpick_data,ypick_data)
        for data in [self.zij_xy_points,self.zij_xz_points]:
            x, y = data.get_data()
            points += [(x[i],y[i]) for i in range(len(x))]
        index = None
        print("getting nearest step at: " + str(pos))
        print(points)
        for point in points:
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
        elif self.specimen_EA_setting == "Zoom":
            self.specimen_EA_setting = "Pan"
            try: self.toolbar2.pan('off')
            except TypeError: pass
        elif self.specimen_EA_setting == "Pan":
            self.specimen_EA_setting = "Zoom"
            try: self.toolbar2.zoom()
            except TypeError: pass

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
        xpick_data,ypick_data = pos
        xdata_org = self.specimen_EA_xdata
        ydata_org = self.specimen_EA_ydata
        data_corrected = self.specimen_eqarea_interpretation.transData.transform(vstack([xdata_org,ydata_org]).T)
        xdata,ydata = data_corrected.T
        xdata = map(float,xdata)
        ydata = map(float,ydata)
        e = 4e0

        if self.specimen_EA_setting == "Zoom":
            self.canvas2.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))
        else:
            self.canvas2.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
        for i,(x,y) in enumerate(zip(xdata,ydata)):
            if 0 < sqrt((x-xpick_data)**2. + (y-ypick_data)**2.) < e:
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
        xpick_data,ypick_data = pos
        xdata_org = self.specimen_EA_xdata
        ydata_org = self.specimen_EA_ydata
        data_corrected = self.specimen_eqarea_interpretation.transData.transform(vstack([xdata_org,ydata_org]).T)
        xdata,ydata = data_corrected.T
        xdata = map(float,xdata)
        ydata = map(float,ydata)
        e = 4e0

        index = None
        for i,(x,y) in enumerate(zip(xdata,ydata)):
            if 0 < sqrt((x-xpick_data)**2. + (y-ypick_data)**2.) < e:
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
        elif self.higher_EA_setting == "Zoom":
            self.higher_EA_setting = "Pan"
            try: self.toolbar4.pan('off')
            except TypeError: pass
        elif self.higher_EA_setting == "Pan":
            self.higher_EA_setting = "Zoom"
            try: self.toolbar4.zoom()
            except TypeError: pass

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
        xpick_data,ypick_data = pos
        xdata_org = self.higher_EA_xdata
        ydata_org = self.higher_EA_ydata
        data_corrected = self.high_level_eqarea.transData.transform(vstack([xdata_org,ydata_org]).T)
        xdata,ydata = data_corrected.T
        xdata = map(float,xdata)
        ydata = map(float,ydata)
        e = 4e0

        if self.higher_EA_setting == "Zoom":
            self.canvas4.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))
        else:
            self.canvas4.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
        if not self.higher_EA_xdata or not self.higher_EA_ydata: return
        for i,(x,y) in enumerate(zip(xdata,ydata)):
            if 0 < sqrt((x-xpick_data)**2. + (y-ypick_data)**2.) < e:
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
        data_corrected = self.high_level_eqarea.transData.transform(vstack([xdata_org,ydata_org]).T)
        xdata,ydata = data_corrected.T
        xdata = map(float,xdata)
        ydata = map(float,ydata)
        e = 4e0

        index = None
        for i,(x,y) in enumerate(zip(xdata,ydata)):
            if 0 < sqrt((x-xpick_data)**2. + (y-ypick_data)**2.) < e:
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

    def right_click_MM0(self,event):
        if self.MM0_setting == "Zoom":
            self.MM0_setting = "Pan"
            self.toolbar3.pan()
        elif self.MM0_setting == "Pan":
            self.MM0_setting = "Zoom"
            self.toolbar3.zoom()

    def home_MM0(self,event):
        self.toolbar3.home()

    #---------------------------------------------#
    #Measurement ListControl Functions
    #---------------------------------------------#

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
        tmin_index,tmax_index = self.get_indices(self.current_fit)

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
          elif "ARM" in methods:
              Step="ARM"
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
            self.logger.SetItemBackgroundColour(i,"red")

    def OnClick_listctrl(self,event):

        if not self.current_fit:
            self.add_fit(1)

        for item in range(self.logger.GetItemCount()):
            if self.Data[self.s]['measurement_flag'][item] == 'b':
                self.logger.SetItemBackgroundColour(item,"red")
            else:
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

    def OnRightClickListctrl(self,event):
        '''
        right click on the listctrl opens a popup menu for
        changing the measurement line from "g" to "b"

        If there is  change, the program rewrirte magic_measurements.txt a
        and reads it again.
        '''
        position=event.GetPosition()
        position[1]=position[1]+300*self.GUI_RESOLUTION
        g_index=event.GetIndex()

        if self.Data[self.s]['measurement_flag'][g_index] == 'g':
            self.mark_meas_bad(g_index)
        else:
            self.mark_meas_good(g_index)

        pmag.magic_write(os.path.join(self.WD, "magic_measurements.txt"),self.mag_meas_data,"magic_measurements")

        self.recalculate_current_specimen_interpreatations()

        if self.interpretation_editor_open:
            self.interpretation_editor.update_current_fit_data()
        self.calculate_higher_levels_data()
        self.update_selection()

    #---------------------------------------------#
    #ComboBox Functions
    #---------------------------------------------#

    def onSelect_specimen(self, event):
        """
        update figures and text when a new specimen is selected
        """
        self.select_specimen(str(self.specimens_box.GetValue()))
        if self.interpretation_editor_open:
            self.interpretation_editor.change_selected(self.current_fit)
        self.update_selection()

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
                fit.put(specimen,self.COORDINATE_SYSTEM,self.get_PCA_parameters(specimen,fit,fit.tmin,fit.tmax,self.COORDINATE_SYSTEM,fit.PCA_type))

        if self.interpretation_editor_open:
            self.interpretation_editor.coordinates_box.SetStringSelection(new)
            self.interpretation_editor.update_editor(True)
        self.update_selection()

    def onSelect_orthogonal_box(self, event):
        self.clear_boxes()
        self.Add_text()
        self.draw_figure(self.s)
        self.update_selection()
        if self.current_fit:
            if self.current_fit.get(self.COORDINATE_SYSTEM):
                self.update_GUI_with_new_interpretation()

    def on_select_specimen_mean_type_box(self,event):
        self.get_new_PCA_parameters(event)
        if self.interpretation_editor_open:
            self.interpretation_editor.update_logger_entry(self.interpretation_editor.current_fit_index)

    def get_new_PCA_parameters(self,event):
        """
        calculate statistics when temperatures are selected
        or PCA type is changed
        """

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
            self.current_fit.put(self.s,coordinate_system,self.get_PCA_parameters(self.s,self.current_fit,tmin,tmax,coordinate_system,calculation_type))
        if self.interpretation_editor_open:
            self.interpretation_editor.update_current_fit_data()
        self.update_GUI_with_new_interpretation()

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

    def on_select_plane_display_box(self,event):
        self.draw_interpretation()
        self.plot_higher_levels_data()

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
        self.update_fit_boxes()
        self.plot_higher_levels_data()

    #---------------------------------------------#
    #Button Functions
    #---------------------------------------------#

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

            self.current_fit.put(self.s,'specimen',self.get_PCA_parameters(self.s,self.current_fit,tmin,tmax,'specimen',calculation_type))
            if len(self.Data[self.s]['zijdblock_geo'])>0:
                self.current_fit.put(self.s,'geographic',self.get_PCA_parameters(self.s,self.current_fit,tmin,tmax,'geographic',calculation_type))
            if len(self.Data[self.s]['zijdblock_tilt'])>0:
                self.current_fit.put(self.s,'tilt-corrected',self.get_PCA_parameters(self.s,self.current_fit,tmin,tmax,'tilt-corrected',calculation_type))

        # calculate higher level data
        self.calculate_higher_levels_data()
        self.plot_higher_levels_data()
        self.on_menu_save_interpretation(-1)
        self.update_selection()
        self.close_warning=True

    def add_fit(self,event,plot_new_fit=True):
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
        if plot_new_fit:
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

    def on_select_stats_button(self,events):
        i = self.switch_stats_button.GetValue()
        self.update_higher_level_stats()

#==========================================================================================#
#==============================GUI Status Functions========================================#
#==========================================================================================#

    def __str__(self):
        out_str=""

        out_str += "Demag_GUI instance: %s\n"%(hex(id(self)))
        out_str += "Global Variables\n"
        out_str += "\tcoordinate system: %s\n"%(self.COORDINATE_SYSTEM)
        num_interp = self.total_num_of_interpertations()
        out_str += "\tthere are %d interpretations in pmag_results\n"%(num_interp)
        out_str += "Current Specimen and Interpretation\n"
        if self.current_fit != None:
            out_str += "\tcurrent fit is: %s for specimen %s\n"%(self.current_fit.name,self.s)
            out_str += "\tvalues of this interpretation for coordinate system %s\n"%(self.COORDINATE_SYSTEM)
            pars = self.current_fit.get(self.COORDINATE_SYSTEM)
            out_str += str(pars)
        else:
            out_str += "\tcurrent fit is: %s for specimen %s\n"%("None",self.s)

        return out_str

    def total_num_of_interpertations(self):
        num_interp = 0
        for specimen in self.specimens:
            if specimen in self.pmag_results_data['specimens']:
                num_interp += len(self.pmag_results_data['specimens'][specimen])
        return num_interp


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
        else:
            return

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

def main(WD=None, standalone_app=True, parent=None):
    # to run as module:
    if not standalone_app:
        disableAll = wx.WindowDisabler()
        frame = Demag_GUI(WD, parent)
        frame.Center()
        frame.Show()
        frame.Raise()

    # to run as command_line:
    else:
        app = wx.App()
        app.frame = Demag_GUI(WD)
        app.frame.Center()
        app.frame.Show()
        app.MainLoop()

if __name__ == '__main__':
    main()

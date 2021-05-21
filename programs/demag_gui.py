#!/usr/bin/env pythonw
"""
Runs Demag GUI PmagPy's main analysis GUI for demagnetization data. This
can be used for PCA of both AF and Thermal demag data, and calculation
of VGP's. It allows export of figures and analysis results for upload to
the MagIC database and/or publication. For more information on how to interpret or use the GUI's many functions see the Help menu in the open GUI. More documentation can be found on all of PmagPy's functionality at the PmagPy cookbook which can be found here: earthref.org/PmagPy/cookbook/

SYNTAX
    demag_gui.py [command line options]
    # or, for Anaconda users:
    demag_gui_anaconda [command line options]


OPTIONS
    -h : opens this help message
    -v : enable verbose mode, demag GUI does not open a log file and instead
         prints to command line
    -WD : specify working directory
    -DM : specify MagIC data model (options : 3 or 2.x)

AUTHORS
    Ron Shaar and Kevin Gaastra
"""
# ============================================================================================
# LOG HEADER:
# ============================================================================================
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
# ============================================================================================
import matplotlib
from functools import reduce
matplotlib.use('WXAgg')
import os
import sys
import pandas as pd
import pdb
import shutil
import pmagpy.pmag as pmag
import pmagpy.ipmag as ipmag
global CURRENT_VERSION, PMAGPY_DIRECTORY
CURRENT_VERSION = pmag.get_version()
import pmagpy.find_pmag_dir as find_pmag_dir
PMAGPY_DIRECTORY = find_pmag_dir.get_pmag_dir()
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar
# try: import zeq_gui_preferences
# except ImportError: pass
from time import time
from datetime import datetime
import wx
import wx.lib.scrolledpanel
import numpy as np
from numpy import vstack, sqrt, arange, array, pi, cos, sin, mean, exp, linspace, convolve, nan
from matplotlib import rcParams
from matplotlib.figure import Figure
from scipy.optimize import curve_fit
from scipy.signal import find_peaks_cwt
from webbrowser import open as webopen
from pkg_resources import resource_filename
from dialogs.demag_interpretation_editor import InterpretationEditorFrame
from dialogs import pmag_widgets as pw
from pmagpy.demag_gui_utilities import *
from pmagpy.Fit import *
import dialogs.demag_dialogs as demag_dialogs
from copy import deepcopy, copy
import pmagpy.contribution_builder as cb
from pandas import DataFrame, Series
from pmagpy.mapping import map_magic
import help_files.demag_gui_help as dgh
from re import findall

matplotlib.rc('xtick', labelsize=10)
matplotlib.rc('ytick', labelsize=10)
matplotlib.rc('axes', labelsize=8)
matplotlib.rcParams['savefig.dpi'] = 300.

# https://github.com/matplotlib/matplotlib/issues/10063
# rcParams.update({"svg.fonttype":'svgfont'})


class Demag_GUI(wx.Frame):
    """
    GUI for interpreting demagnetization data (AF and/or thermal)
    """
    title = "Demag GUI version:%s" % CURRENT_VERSION

#==========================================================================================#
#============================Initalization Functions=======================================#
#==========================================================================================#

    def __init__(self, WD=None, parent=None, write_to_log_file=True,
                 test_mode_on=False, data_model=None, evt_quit=None,
                 meas_file=None):
        """
        Initializes the GUI by creating necessary variables, importing data,
        setting icon, and initializing the UI and menu

        Parameters
        ----------
        WD : Working directory where data files will be written to
        and read from if None will prompt user for location (default: None)
        parent : wx.Frame object that is already running in a wx.App
        or NoneType object if this is the top level window (default: None)
        write_to_log_file : verbal or non-verbal GUI modes True will
        redirect stdout to a .log file False will print to stdout as normal
        (default: True)
        test_mode_on : used for unit testing if True all dialogs
        will return with AffermativeID (default: False)

        Returns
        -------
        Instance of Demag_GUI class
        """
        default_style = wx.MINIMIZE_BOX | wx.MAXIMIZE_BOX | wx.RESIZE_BORDER | wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX | wx.CLIP_CHILDREN | wx.NO_FULL_REPAINT_ON_RESIZE | wx.WS_EX_CONTEXTHELP | wx.FRAME_EX_CONTEXTHELP
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title,
                          style=default_style, name='demag gui')
        self.parent = parent
        self.set_test_mode(test_mode_on)
        self.evt_quit = evt_quit
        self.data_model = data_model
        # default intensity column
        self.intensity_col = "measurement_magn_moment"

        # setup wx help provider class to give help messages
        provider = wx.SimpleHelpProvider()
        wx.HelpProvider.Set(provider)
        self.helper = wx.ContextHelp(doNow=False)

        self.currentDirectory = os.getcwd()  # get the current working directory

        if WD != None:
            if not os.path.isdir(WD):
                print(("There is no directory %s using current directory" % (WD)))
                WD = os.getcwd()
            if not meas_file:
                self.change_WD(WD)
            else:
                wd = os.path.split(meas_file)[0]
                self.change_WD(wd, meas_file)
        else:
            new_WD = self.get_DIR()  # choose directory dialog, then initialize directory variables
            if new_WD == self.currentDirectory and 'Anaconda' in sys.version.split()[1]:
                new_WD = self.get_DIR()
            self.change_WD(new_WD, meas_file)
        if write_to_log_file:
            self.init_log_file()

        # init wait dialog
        disableAll = wx.WindowDisabler()
        wait = wx.BusyInfo('Compiling required data, please wait...')
        wx.SafeYield()

        try:
            data_model = int(float(self.data_model))
            if data_model not in [2, 3]:
                print('-W- Could not parse provided data model:', data_model)
                print('    Assuming you want data model 3.0')
                self.data_model = 3.0
            self.data_model = float(self.data_model)
        except:
            print('-W- Could not parse provided data model:', data_model)
            print('    Assuming you want data model 3.0')
            self.data_model = 3.0
        # set icon
        if not self.parent:
            self.icon = wx.Icon()
            icon_path = os.path.join(
                PMAGPY_DIRECTORY, 'programs', 'images', 'PmagPy.ico')
            if os.path.isfile(icon_path):
                self.icon.CopyFromBitmap(
                    wx.Bitmap(icon_path, wx.BITMAP_TYPE_ANY))
                self.SetIcon(self.icon)
            else:
                print("-I- PmagPy icon file not found -- skipping")
        else:
            self.icon = self.parent.icon
            self.SetIcon(self.parent.icon)

        # initialize acceptence criteria with NULL values
        self.acceptance_criteria = self.read_criteria_file()

        # initalize starting variables and structures
        self.font_type = "Arial"
        if sys.platform.startswith("linux"):
            self.font_type = "Liberation Serif"

        self.preferences = self.get_preferences()
        self.dpi = 100

        self.all_fits_list = []

        self.pmag_results_data = {}
        for level in ['specimens', 'samples', 'sites', 'locations', 'study']:
            self.pmag_results_data[level] = {}

        self.high_level_means = {}
        for high_level in ['samples', 'sites', 'locations', 'study']:
            if high_level not in list(self.high_level_means.keys()):
                self.high_level_means[high_level] = {}

        self.ie_open,self.vgp_open = False,False
        self.check_orient_on = False
        self.list_bound_loc = 0
        self.color_dict = {}
        self.colors = ['#4ED740', '#9840D7', '#FFBD4C',
                       '#398AAD', '#E96640', "#CB1A9F", "55C2B6", "FFD44C"]
        for name, hexval in matplotlib.colors.cnames.items():
            if name == 'black' or name == 'blue' or name == 'red':
                continue
            elif name == 'green' or name == 'yellow' or name == 'maroon' or name == 'cyan':
                self.color_dict[name] = hexval
            else:
                self.color_dict[name] = hexval
                self.colors.append(hexval)
        self.all_fits_list = []
        self.current_fit = None
        self.selected_meas = []
        self.selected_meas_artists = []
        self.displayed_means = []
        self.selected_meas_called = False
        self.dirtypes = ['DA-DIR', 'DA-DIR-GEO', 'DA-DIR-TILT']
        self.bad_fits = []
        self.CART_rot, self.CART_rot_good, self.CART_rot_bad = array(
            []), array([]), array([])

        # initialize selecting criteria
        self.COORDINATE_SYSTEM = 'geographic'
        self.UPPER_LEVEL_SHOW = 'specimens'

        if not self.magic_file:
            return
        # Get data
        self.Data_info = self.get_data_info()  # Read  er_* data
        # Get data from magic_measurements and rmag_anistropy if exist.
        self.Data, self.Data_hierarchy = self.get_data()
        if not self.Data:
            self.Destroy()
            if self.evt_quit:
                event = self.evt_quit(self.GetId())
                self.GetEventHandler().ProcessEvent(event)

            return


        # get list of sites
        self.locations = list(self.Data_hierarchy['locations'].keys())
        self.locations.sort()  # get list of sites
        # get list of sites
        self.sites = list(self.Data_hierarchy['sites'].keys())
        self.sites.sort(key=spec_key_func)  # get list of sites
        self.samples = []  # sort the samples within each site
        for site in self.sites:
            self.samples.extend(
                sorted(self.Data_hierarchy['sites'][site]['samples'], key=spec_key_func))
        self.specimens = []  # sort the specimens within each sample
        for samp in self.samples:
            self.specimens.extend(
                sorted(self.Data_hierarchy['samples'][samp]['specimens'], key=spec_key_func))

        # first initialization of self.s only place besides init_cart_rot where it can be set without calling select_specimen
        if len(self.specimens) > 0:
            self.s = str(self.specimens[0])
        else:
            self.s = ""
        try:
            self.sample = self.Data_hierarchy['sample_of_specimen'][self.s]
        except KeyError:
            self.sample = ""
        try:
            self.site = self.Data_hierarchy['site_of_specimen'][self.s]
        except KeyError:
            self.site = ""

        self.scrolled_panel = wx.lib.scrolledpanel.ScrolledPanel(
            self, wx.ID_ANY)  # make the Panel
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.side_panel = wx.Panel(self, wx.ID_ANY)
        self.init_UI()  # build the main frame
        self.create_menu()  # create manu bar
        self.scrolled_panel.SetAutoLayout(True)
        self.scrolled_panel.SetupScrolling()  # endable scrolling

        # Draw figures and add text
        if self.Data and any(self.Data[s][k] if not isinstance(self.Data[s][k], type(array([]))) else self.Data[s][k].any() for s in self.Data for k in self.Data[s]):
            # get previous interpretations from pmag tables
            if self.data_model == 3.0 and 'specimens' in self.con.tables:
                self.get_interpretations3()
            if self.data_model == 2.5:
                self.update_pmag_tables()
            if not self.current_fit:
                self.update_selection()
            else:
                self.Add_text()
                self.update_fit_boxes()
                self.update_high_level_stats()
        else:
            pass

        self.running = True
        self.arrow_keys()
        self.Bind(wx.EVT_CLOSE, self.on_menu_exit)
        self.close_warning = False
        del wait

    def init_UI(self):
        """
        Set display variables (font, resolution of GUI, sizer proportions)
        then builds the Side bar panel, Top bar panel, and Plots scrolleing
        panel which are then placed placed together in a sizer and fit to
        the GUI wx.Frame
        """
# --------------------------------------------------------------------------
    # Setup ScrolledPanel Ctrls---------------------------------------------
# --------------------------------------------------------------------------

    # ----------------------------------------------------------------------
        #  set ctrl size and style variables
    # ----------------------------------------------------------------------
        dw, dh = wx.DisplaySize()
        r1 = dw/1210.
        r2 = dw/640.

        self.GUI_RESOLUTION = min(r1, r2, 1)
        top_bar_2v_space = 5
        top_bar_h_space = 10
        spec_button_space = 10
        side_bar_v_space = 10

    # ----------------------------------------------------------------------
        #  set font size and style
    # ----------------------------------------------------------------------

        FONT_WEIGHT = 1
        if sys.platform.startswith('win'):
            FONT_WEIGHT = -1
        font1 = wx.Font(9+FONT_WEIGHT, wx.SWISS, wx.NORMAL,
                        wx.NORMAL, False, self.font_type)
        font2 = wx.Font(12+FONT_WEIGHT, wx.SWISS, wx.NORMAL,
                        wx.NORMAL, False, self.font_type)
        font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT)
        font.SetPointSize(10+FONT_WEIGHT)

# --------------------------------------------------------------------------
    # Setup ScrolledPanel Ctrls---------------------------------------------
# --------------------------------------------------------------------------

    # ----------------------------------------------------------------------
        # Create Figures and FigCanvas objects.
    # ----------------------------------------------------------------------

        self.fig1 = Figure((5.*self.GUI_RESOLUTION, 5. *
                            self.GUI_RESOLUTION), dpi=self.dpi)
        self.canvas1 = FigCanvas(self.scrolled_panel, -1, self.fig1)
        self.toolbar1 = NavigationToolbar(self.canvas1)
        self.toolbar1.Hide()
        self.zijderveld_setting = "Zoom"
        self.toolbar1.zoom()
        self.canvas1.Bind(wx.EVT_RIGHT_DOWN, self.right_click_zijderveld)
        self.canvas1.Bind(wx.EVT_MIDDLE_DOWN, self.home_zijderveld)
        self.canvas1.Bind(wx.EVT_LEFT_DCLICK, self.on_zijd_select)
        self.canvas1.Bind(wx.EVT_RIGHT_DCLICK, self.on_zijd_mark)
        self.canvas1.Bind(wx.EVT_MOTION, self.on_change_zijd_mouse_cursor)
        self.canvas1.SetHelpText(dgh.zij_help)

        self.fig2 = Figure((2.5*self.GUI_RESOLUTION, 2.5 *
                            self.GUI_RESOLUTION), dpi=self.dpi)
        self.specimen_eqarea = self.fig2.add_subplot(111)
        draw_net(self.specimen_eqarea)
        self.canvas2 = FigCanvas(self.scrolled_panel, -1, self.fig2)
        self.toolbar2 = NavigationToolbar(self.canvas2)
        self.toolbar2.Hide()
        self.toolbar2.zoom()
        self.specimen_EA_setting = "Zoom"
        self.canvas2.Bind(wx.EVT_LEFT_DCLICK,
                          self.on_equalarea_specimen_select)
        self.canvas2.Bind(wx.EVT_RIGHT_DOWN,
                          self.right_click_specimen_equalarea)
        self.canvas2.Bind(wx.EVT_MOTION, self.on_change_specimen_mouse_cursor)
        self.canvas2.Bind(wx.EVT_MIDDLE_DOWN, self.home_specimen_equalarea)
        self.canvas2.SetHelpText(dgh.spec_eqarea_help)
        self.specimen_EA_xdata = []
        self.specimen_EA_ydata = []

        self.fig3 = Figure((2.5*self.GUI_RESOLUTION, 2.5 *
                            self.GUI_RESOLUTION), dpi=self.dpi)
        self.mplot = self.fig3.add_axes(
            [0.2, 0.15, 0.7, 0.7], frameon=True, facecolor='None')
        self.canvas3 = FigCanvas(self.scrolled_panel, -1, self.fig3)
        self.toolbar3 = NavigationToolbar(self.canvas3)
        self.toolbar3.Hide()
        self.toolbar3.zoom()
        self.MM0_setting = "Zoom"
        self.canvas3.Bind(wx.EVT_RIGHT_DOWN, self.right_click_MM0)
        self.canvas3.Bind(wx.EVT_MIDDLE_DOWN, self.home_MM0)
        self.canvas3.SetHelpText(dgh.MM0_help)

        self.fig4 = Figure((2.5*self.GUI_RESOLUTION, 2.5 *
                            self.GUI_RESOLUTION), dpi=self.dpi)
        self.canvas4 = FigCanvas(self.scrolled_panel, -1, self.fig4)
        self.toolbar4 = NavigationToolbar(self.canvas4)
        self.toolbar4.Hide()
        self.toolbar4.zoom()
        self.high_EA_setting = "Zoom"
        self.canvas4.Bind(wx.EVT_LEFT_DCLICK, self.on_equalarea_high_select)
        self.canvas4.Bind(wx.EVT_RIGHT_DOWN, self.right_click_high_equalarea)
        self.canvas4.Bind(wx.EVT_MOTION, self.on_change_high_mouse_cursor)
        self.canvas4.Bind(wx.EVT_MIDDLE_DOWN, self.home_high_equalarea)
        self.canvas4.SetHelpText(dgh.high_level_eqarea_help)
        self.old_pos = None
        self.high_EA_xdata = []
        self.high_EA_ydata = []
        self.high_level_eqarea = self.fig4.add_subplot(111)
        draw_net(self.high_level_eqarea)

    # ----------------------------------------------------------------------
        # High level Stats Sizer and Switch Stats Button
    # ----------------------------------------------------------------------

        self.stats_sizer = wx.StaticBoxSizer(wx.StaticBox(
            self.panel, wx.ID_ANY, "mean statistics"), wx.VERTICAL)

        for parameter in ['mean_type', 'dec', 'inc', 'alpha95', 'K', 'R', 'n_lines', 'n_planes']:
            COMMAND = "self.%s_window=wx.TextCtrl(self.scrolled_panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50*self.GUI_RESOLUTION,25))" % parameter
            exec(COMMAND)
            COMMAND = "self.%s_window.SetBackgroundColour(wx.WHITE)" % parameter
            exec(COMMAND)
            COMMAND = "self.%s_window.SetFont(font2)" % parameter
            exec(COMMAND)
            COMMAND = "self.%s_outer_window = wx.GridSizer(1,2,5*self.GUI_RESOLUTION,15*self.GUI_RESOLUTION)" % parameter
            exec(COMMAND)
            COMMAND = """self.%s_outer_window.AddMany([
                    (wx.StaticText(self.scrolled_panel,label='%s',style=wx.TE_CENTER),1,wx.EXPAND),
                    (self.%s_window, 1, wx.EXPAND)])""" % (parameter, parameter, parameter)
            exec(COMMAND)
            COMMAND = "self.stats_sizer.Add(self.%s_outer_window, 1, wx.EXPAND)" % parameter
            exec(COMMAND)

        self.switch_stats_button = wx.SpinButton(
            self.scrolled_panel, id=wx.ID_ANY, style=wx.SP_HORIZONTAL | wx.SP_ARROW_KEYS | wx.SP_WRAP, name="change stats")
        self.Bind(wx.EVT_SPIN, self.on_select_stats_button,
                  self.switch_stats_button)
        self.switch_stats_button.SetHelpText(dgh.switch_stats_btn_help)

# --------------------------------------------------------------------------
    #  Side Bar Options and Logger-----------------------------------------
# --------------------------------------------------------------------------

    # ----------------------------------------------------------------------
        # Create text_box for presenting the measurements
    # ----------------------------------------------------------------------

        self.logger = wx.ListCtrl(self.side_panel, id=wx.ID_ANY, size=(
            100*self.GUI_RESOLUTION, 100*self.GUI_RESOLUTION), style=wx.LC_REPORT)
        self.logger.SetFont(font1)
        self.logger.InsertColumn(0, 'i', width=25*self.GUI_RESOLUTION)
        self.logger.InsertColumn(1, 'Step', width=25*self.GUI_RESOLUTION)
        self.logger.InsertColumn(2, 'Tr', width=35*self.GUI_RESOLUTION)
        self.logger.InsertColumn(3, 'Dec', width=35*self.GUI_RESOLUTION)
        self.logger.InsertColumn(4, 'Inc', width=35*self.GUI_RESOLUTION)
        self.logger.InsertColumn(5, 'M', width=45*self.GUI_RESOLUTION)
        self.logger.InsertColumn(6, 'csd', width=45*self.GUI_RESOLUTION)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED,
                  self.on_click_listctrl, self.logger)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK,
                  self.on_right_click_listctrl, self.logger)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED,
                  self.on_select_measurement, self.logger)
        self.logger.SetHelpText(dgh.logger_help)

    # ----------------------------------------------------------------------
        #  select specimen box
    # ----------------------------------------------------------------------

        # Combo-box with a list of specimen
        self.specimens_box = wx.ComboBox(self.side_panel, id=wx.ID_ANY, value=self.s, size=(
            200*self.GUI_RESOLUTION, 25), choices=self.specimens, style=wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER, name="specimen")
        self.Bind(wx.EVT_COMBOBOX, self.onSelect_specimen, self.specimens_box)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_enter_specimen,
                  self.specimens_box)
        self.specimens_box.SetHelpText(dgh.specimens_box_help)

        # buttons to move forward and backwards from specimens
        self.nextbutton = wx.Button(
            self.side_panel, id=wx.ID_ANY, label='next', size=(100*self.GUI_RESOLUTION, 25))
        self.Bind(wx.EVT_BUTTON, self.on_next_button, self.nextbutton)
        self.nextbutton.SetFont(font2)
        self.nextbutton.SetHelpText(dgh.nextbutton_help)

        self.prevbutton = wx.Button(
            self.side_panel, id=wx.ID_ANY, label='previous', size=(100*self.GUI_RESOLUTION, 25))
        self.prevbutton.SetFont(font2)
        self.Bind(wx.EVT_BUTTON, self.on_prev_button, self.prevbutton)
        self.prevbutton.SetHelpText(dgh.prevbutton_help)

    # ----------------------------------------------------------------------
        #  select coordinate box
    # ----------------------------------------------------------------------

        self.COORDINATE_SYSTEM, self.coordinate_list = self.get_coordinate_system()
        self.coordinates_box = wx.ComboBox(self.side_panel, id=wx.ID_ANY, size=(
            200*self.GUI_RESOLUTION, 25), choices=self.coordinate_list, value=self.COORDINATE_SYSTEM, style=wx.CB_DROPDOWN | wx.TE_READONLY, name="coordinates")
        self.Bind(wx.EVT_COMBOBOX, self.onSelect_coordinates,
                  self.coordinates_box)
        self.coordinates_box.SetHelpText(dgh.coordinates_box_help)

    # ----------------------------------------------------------------------
        #  Orthogonal Zijderveld Options box
    # ----------------------------------------------------------------------

        self.orthogonal_box = wx.ComboBox(self.side_panel, id=wx.ID_ANY, value='X=East', size=(
            200*self.GUI_RESOLUTION, 25), choices=['X=NRM dec', 'X=East', 'X=North'], style=wx.CB_DROPDOWN | wx.TE_READONLY, name="orthogonal_plot")
        # remove 'X=best fit line dec' as option given that is isn't implemented for multiple components
        self.Bind(wx.EVT_COMBOBOX, self.onSelect_orthogonal_box,
                  self.orthogonal_box)
        self.orthogonal_box.SetHelpText(dgh.orthogonal_box_help)

# --------------------------------------------------------------------------
    #  Top Bar Options ----------------------------------------------------
# --------------------------------------------------------------------------

    # ----------------------------------------------------------------------
        #  select bounds box
    # ----------------------------------------------------------------------

        self.T_list = []

        self.tmin_box = wx.ComboBox(self.panel, id=wx.ID_ANY, size=(
            50*self.GUI_RESOLUTION, 25), choices=self.T_list, style=wx.CB_DROPDOWN | wx.TE_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.get_new_PCA_parameters, self.tmin_box)
        self.tmin_box.SetHelpText(dgh.tmin_box_help)

        self.tmax_box = wx.ComboBox(self.panel, id=wx.ID_ANY, size=(
            50*self.GUI_RESOLUTION, 25), choices=self.T_list, style=wx.CB_DROPDOWN | wx.TE_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.get_new_PCA_parameters, self.tmax_box)
        self.tmax_box.SetHelpText(dgh.tmax_box_help)

    # ----------------------------------------------------------------------
        #  Specimens interpretations Management box
    # ----------------------------------------------------------------------

        list_fits = []

        self.fit_box = wx.ComboBox(self.panel, id=wx.ID_ANY, size=(
            50*self.GUI_RESOLUTION, 25), choices=list_fits, style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_COMBOBOX, self.on_select_fit, self.fit_box)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_enter_fit_name, self.fit_box)
        self.fit_box.SetHelpText(dgh.fit_box_help)

        self.add_fit_button = wx.Button(
            self.panel, id=wx.ID_ANY, label='add fit', size=(50*self.GUI_RESOLUTION, 25))
        self.add_fit_button.SetFont(font2)
        self.Bind(wx.EVT_BUTTON, self.on_btn_add_fit, self.add_fit_button)
        self.add_fit_button.SetHelpText(dgh.add_fit_button_help)

        # save/delete interpretation buttons
        self.save_fit_button = wx.Button(self.panel, id=wx.ID_ANY, label='save', size=(
            50*self.GUI_RESOLUTION, 25))  # ,style=wx.BU_EXACTFIT)#, size=(175, 28))
        self.save_fit_button.SetFont(font2)
        self.save_fit_button.SetHelpText(dgh.save_fit_btn_help)

        self.delete_fit_button = wx.Button(self.panel, id=wx.ID_ANY, label='delete fit', size=(
            50*self.GUI_RESOLUTION, 25))  # ,style=wx.BU_EXACTFIT)#, size=(175, 28))
        self.delete_fit_button.SetFont(font2)
        self.delete_fit_button.SetHelpText(dgh.delete_fit_btn_help)

        self.Bind(wx.EVT_BUTTON, self.on_save_interpretation_button,
                  self.save_fit_button)
        self.Bind(wx.EVT_BUTTON, self.on_btn_delete_fit,
                  self.delete_fit_button)

        # auto-save interpretation buttons
        self.auto_save = wx.CheckBox(self.panel, wx.ID_ANY, 'auto-save')
        if self.preferences['auto_save']:
            self.auto_save.SetValue(True)

        self.auto_save_info = wx.Button(self.panel, wx.ID_ANY, "?")
        self.Bind(wx.EVT_BUTTON, self.on_btn_info_click, self.auto_save_info)

    # ----------------------------------------------------------------------
        # Interpretation Type and Display window
    # ----------------------------------------------------------------------

        self.PCA_type_box = wx.ComboBox(self.panel, id=wx.ID_ANY, size=(50*self.GUI_RESOLUTION, 25), value='line', choices=[
                                        'line', 'line-anchored', 'line-with-origin', 'plane', 'Fisher'], style=wx.CB_DROPDOWN | wx.TE_READONLY, name="coordinates")
        self.Bind(wx.EVT_COMBOBOX,
                  self.on_select_specimen_mean_type_box, self.PCA_type_box)
        self.PCA_type_box.SetHelpText(dgh.PCA_type_help)

        self.plane_display_box = wx.ComboBox(self.panel, id=wx.ID_ANY, size=(50*self.GUI_RESOLUTION, 25), value='whole plane', choices=[
                                             'whole plane', 'u. hemisphere', 'l. hemisphere', 'poles', 'bfv', 'wp + bfv'], style=wx.CB_DROPDOWN | wx.TE_READONLY, name="PlaneType")
        self.Bind(wx.EVT_COMBOBOX, self.on_select_plane_display_box,
                  self.plane_display_box)
        self.plane_display_box.SetHelpText(dgh.plane_display_help)

    # ----------------------------------------------------------------------
        # Interpretation Statistics StaticSizer
    # ----------------------------------------------------------------------

        box_sizer_specimen_stat = wx.StaticBoxSizer(wx.StaticBox(
            self.panel, wx.ID_ANY, "Interpretation Direction and Statistics"), wx.HORIZONTAL)

        for parameter in ['dec', 'inc', 'n', 'mad', 'dang', 'alpha95']:
            COMMAND = "self.s%s_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(25*self.GUI_RESOLUTION,25))" % parameter
            exec(COMMAND)
            COMMAND = "self.s%s_window.SetBackgroundColour(wx.WHITE)" % parameter
            exec(COMMAND)
            COMMAND = "self.s%s_window.SetFont(font2)" % parameter
            exec(COMMAND)

        specimen_stat_window = wx.GridSizer(2, 6, 0, 5)
        specimen_stat_window.AddMany([(wx.StaticText(self.panel, label="dec", style=wx.TE_CENTER), 1, wx.EXPAND | wx.TOP, 2*top_bar_2v_space),
                                      (wx.StaticText(self.panel, label="inc", style=wx.TE_CENTER),
                                       1, wx.EXPAND | wx.TOP, 2*top_bar_2v_space),
                                      (wx.StaticText(self.panel, label="n", style=wx.TE_CENTER),
                                       1, wx.EXPAND | wx.TOP, 2*top_bar_2v_space),
                                      (wx.StaticText(self.panel, label="mad", style=wx.TE_CENTER),
                                       1, wx.EXPAND | wx.TOP, 2*top_bar_2v_space),
                                      (wx.StaticText(self.panel, label="dang", style=wx.TE_CENTER),
                                       1, wx.TE_CENTER | wx.EXPAND | wx.TOP, 2*top_bar_2v_space),
                                      (wx.StaticText(self.panel, label="a95", style=wx.TE_CENTER),
                                       1, wx.TE_CENTER | wx.EXPAND | wx.TOP, 2*top_bar_2v_space),
                                      (self.sdec_window, 1, wx.EXPAND),
                                      (self.sinc_window, 1, wx.EXPAND),
                                      (self.sn_window, 1, wx.EXPAND),
                                      (self.smad_window, 1, wx.EXPAND),
                                      (self.sdang_window, 1, wx.EXPAND),
                                      (self.salpha95_window, 1, wx.EXPAND)])
        box_sizer_specimen_stat.Add(
            specimen_stat_window, 1,  wx.EXPAND)

    # ----------------------------------------------------------------------
        # High level mean window
    # ----------------------------------------------------------------------

        self.level_box = wx.ComboBox(self.panel, id=wx.ID_ANY, size=(50*self.GUI_RESOLUTION, 25), value='site',  choices=[
                                     'sample', 'site', 'location', 'study'], style=wx.CB_DROPDOWN | wx.TE_READONLY, name="high_level")
        self.Bind(wx.EVT_COMBOBOX, self.onSelect_high_level, self.level_box)
        self.level_box.SetHelpText(dgh.level_box_help)

        self.level_names = wx.ComboBox(self.panel, id=wx.ID_ANY, size=(
            50*self.GUI_RESOLUTION, 25), value=self.site, choices=self.sites, style=wx.CB_DROPDOWN | wx.TE_READONLY, name="high_level_names")
        self.Bind(wx.EVT_COMBOBOX, self.onSelect_level_name, self.level_names)
        self.level_names.SetHelpText(dgh.level_names_help)

    # ----------------------------------------------------------------------
        # mean types box
    # ----------------------------------------------------------------------

        self.mean_type_box = wx.ComboBox(self.panel, id=wx.ID_ANY, size=(50*self.GUI_RESOLUTION, 25), value='None', choices=[
                                         'Fisher', 'Fisher by polarity', 'None'], style=wx.CB_DROPDOWN | wx.TE_READONLY, name="high_type")
        self.Bind(wx.EVT_COMBOBOX, self.onSelect_mean_type_box,
                  self.mean_type_box)
        self.mean_type_box.SetHelpText(dgh.mean_type_help)

        self.mean_fit_box = wx.ComboBox(self.panel, id=wx.ID_ANY, size=(50*self.GUI_RESOLUTION, 25), value='None', choices=[
                                        'None', 'All'] + list_fits, style=wx.CB_DROPDOWN | wx.TE_READONLY, name="high_type")
        self.Bind(wx.EVT_COMBOBOX, self.onSelect_mean_fit_box,
                  self.mean_fit_box)
        self.mean_fit_box.SetHelpText(dgh.mean_fit_help)
        self.mean_fit = 'None'

    # ----------------------------------------------------------------------
        # Warnings TextCtrl
    # ----------------------------------------------------------------------
        warning_sizer = wx.StaticBoxSizer(wx.StaticBox(
            self.panel, wx.ID_ANY, "Current Data Warnings"), wx.VERTICAL)

        self.warning_box = wx.TextCtrl(self.panel, id=wx.ID_ANY, size=(50*self.GUI_RESOLUTION, 50 + 2*top_bar_2v_space),
                                       value="No Problems", style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL, name="warning_box")
        self.warning_box.SetHelpText(dgh.warning_help)

        warning_sizer.Add(self.warning_box, 1, wx.TOP | wx.EXPAND)

    # ----------------------------------------------------------------------
        # Design the panel
    # ----------------------------------------------------------------------

        # Top Bar-----------------------------------------------------------
        top_bar_sizer = wx.BoxSizer(wx.HORIZONTAL)

        bounds_sizer = wx.StaticBoxSizer(wx.StaticBox(
            self.panel, wx.ID_ANY, "Bounds"), wx.VERTICAL)
        bounds_sizer.AddMany([(self.tmin_box, 1,  wx.EXPAND | wx.BOTTOM, top_bar_2v_space),
                              (self.tmax_box, 1,  wx.EXPAND | wx.TOP, top_bar_2v_space)])
        top_bar_sizer.Add(bounds_sizer, 1)

        fit_sizer = wx.StaticBoxSizer(wx.StaticBox(
            self.panel, wx.ID_ANY, "Interpretation Options"), wx.VERTICAL)
        fit_grid = wx.GridSizer(2, 3, top_bar_h_space, 2*top_bar_2v_space)
        fit_grid.AddMany([(self.add_fit_button, 1,   wx.EXPAND),
                          (self.save_fit_button, 1,
                            wx.EXPAND),
                          (self.auto_save, 1),
                          (self.fit_box, 1,
                            wx.EXPAND),
                          (self.delete_fit_button, 1,   wx.EXPAND),
                          (self.auto_save_info, 1)])
        fit_sizer.Add(fit_grid, 1, wx.EXPAND)
        top_bar_sizer.Add(fit_sizer, 2,
                          wx.LEFT, top_bar_h_space)

        fit_type_sizer = wx.StaticBoxSizer(wx.StaticBox(
            self.panel, wx.ID_ANY, "Interpretation Type"), wx.VERTICAL)
        fit_type_sizer.AddMany([(self.PCA_type_box, 1,  wx.EXPAND | wx.BOTTOM, top_bar_2v_space),
                                (self.plane_display_box, 1,  wx.EXPAND | wx.TOP, top_bar_2v_space)])
        top_bar_sizer.Add(fit_type_sizer, 1,
                          wx.LEFT, top_bar_h_space)

        top_bar_sizer.Add(box_sizer_specimen_stat, 3,
                           wx.LEFT, top_bar_h_space)

        level_sizer = wx.StaticBoxSizer(wx.StaticBox(
            self.panel, wx.ID_ANY, "Display Level"), wx.VERTICAL)
        level_sizer.AddMany([(self.level_box, 1,  wx.EXPAND | wx.BOTTOM, top_bar_2v_space),
                             (self.level_names, 1,  wx.EXPAND | wx.TOP, top_bar_2v_space)])
        top_bar_sizer.Add(level_sizer, 1,
                          wx.LEFT, top_bar_h_space)

        mean_options_sizer = wx.StaticBoxSizer(wx.StaticBox(
            self.panel, wx.ID_ANY, "Mean Options"), wx.VERTICAL)
        mean_options_sizer.AddMany([(self.mean_type_box, 1,  wx.EXPAND | wx.BOTTOM, top_bar_2v_space),
                                    (self.mean_fit_box, 1,  wx.EXPAND | wx.TOP, top_bar_2v_space)])
        top_bar_sizer.Add(mean_options_sizer, 1,
                           wx.LEFT, top_bar_h_space)

        top_bar_sizer.Add(warning_sizer, 2,
                          wx.LEFT, top_bar_h_space)

        # Side Bar------------------------------------------------------------
        side_bar_sizer = wx.BoxSizer(wx.VERTICAL)

        spec_sizer = wx.StaticBoxSizer(wx.StaticBox(
            self.side_panel, wx.ID_ANY, "Specimen"), wx.VERTICAL)
        spec_buttons_sizer = wx.GridSizer(1, 2, 0, spec_button_space)
        spec_buttons_sizer.AddMany([(self.prevbutton, 1,  wx.EXPAND),
                                    (self.nextbutton, 1, wx.EXPAND)])
        spec_sizer.AddMany([(self.specimens_box, 1,  wx.EXPAND | wx.BOTTOM, side_bar_v_space/2),
                            (spec_buttons_sizer, 1,  wx.EXPAND | wx.TOP, side_bar_v_space/2)])
        side_bar_sizer.Add(spec_sizer, .5,  wx.EXPAND)
        side_bar_sizer.Add(wx.StaticLine(self.side_panel), .5,
                           wx.ALL | wx.EXPAND, side_bar_v_space)

        coordinate_sizer = wx.StaticBoxSizer(wx.StaticBox(
            self.side_panel, wx.ID_ANY, "Coordinate System"), wx.VERTICAL)
        coordinate_sizer.Add(self.coordinates_box, .5, wx.EXPAND)
        side_bar_sizer.Add(coordinate_sizer, .5,  wx.EXPAND)
        side_bar_sizer.Add(wx.StaticLine(self.side_panel), .5,
                           wx.ALL | wx.EXPAND, side_bar_v_space)

        zijderveld_option_sizer = wx.StaticBoxSizer(wx.StaticBox(
            self.side_panel, wx.ID_ANY, "Zijderveld Plot Options"), wx.VERTICAL)
        zijderveld_option_sizer.Add(self.orthogonal_box, 1, wx.EXPAND)
        side_bar_sizer.Add(zijderveld_option_sizer, .5,
                            wx.EXPAND)

        side_bar_sizer.Add(self.logger, proportion=1,
                           flag= wx.TOP | wx.EXPAND, border=8)

        # Mean Stats and button Sizer-----------------------------------------
        stats_and_button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        stats_and_button_sizer.AddMany([(self.stats_sizer, 1,  wx.EXPAND),
                                        (self.switch_stats_button, .3,  wx.EXPAND)])

        # EQ area MM0 and stats sizer-----------------------------------------
        eqarea_MM0_stats_sizer = wx.GridSizer(2, 2, 0, 0)
        eqarea_MM0_stats_sizer.AddMany([(self.canvas2, 1,  wx.EXPAND),
                                        (self.canvas4, 1,  wx.EXPAND),
                                        (self.canvas3, 1,  wx.EXPAND),
                                        (stats_and_button_sizer, 1,  wx.EXPAND)])

        # Plots and Stats Sizer-----------------------------------------------
        full_plots_sizer = wx.BoxSizer(wx.HORIZONTAL)
        full_plots_sizer.Add(self.canvas1, 1,  wx.EXPAND)
        full_plots_sizer.Add(eqarea_MM0_stats_sizer, 1.5,
                              wx.EXPAND)

        self.panel.SetSizerAndFit(top_bar_sizer)
        self.side_panel.SetSizerAndFit(side_bar_sizer)
        self.scrolled_panel.SetSizer(full_plots_sizer)

        # Outer Sizer---------------------------------------------------------
        add_side_bar_sizer = wx.BoxSizer(wx.HORIZONTAL)
        add_side_bar_sizer.Add(self.side_panel, 1,  wx.EXPAND)
        add_side_bar_sizer.Add(self.scrolled_panel, 5,
                                wx.EXPAND)

        outersizer = wx.BoxSizer(wx.VERTICAL)
        outersizer.Add(self.panel, .2,  wx.EXPAND)
        outersizer.Add(add_side_bar_sizer, 1,  wx.EXPAND)

        self.SetSizer(outersizer)
        outersizer.Fit(self)

        self.GUI_SIZE = self.GetSize()


    def get_coordinate_system(self):
        """
        Check self.Data for available coordinate systems.

        Returns
        ---------
        initial_coordinate, coordinate_list : str, list
        i.e., 'geographic', ['specimen', 'geographic']
        """
        coordinate_list = ['specimen']
        initial_coordinate = 'specimen'
        for specimen in self.specimens:
            if 'geographic' not in coordinate_list and self.Data[specimen]['zijdblock_geo']:
                coordinate_list.append('geographic')
                initial_coordinate = 'geographic'
            if 'tilt-corrected' not in coordinate_list and self.Data[specimen]['zijdblock_tilt']:
                coordinate_list.append('tilt-corrected')
        return initial_coordinate, coordinate_list


    def create_menu(self):
        """
        Create the MenuBar for the GUI current structure is:
        File : Change Working Directory, Import Interpretations from LSQ
        file, Import interpretations from a redo file, Save interpretations
        to a redo file, Save MagIC tables, Save Plots
        Edit : New Interpretation, Delete Interpretation, Next
        Interpretation, Previous Interpretation, Next Specimen, Previous
        Speciemen, Flag Measurement Data, Coordinate Systems
        Analysis : Acceptance Criteria, Sample Orientation, Flag
        Interpretaions
        Tools : Interpretation Editor, VGP Viewer
        Help : Usage and Tips, PmagPy Cookbook, Open Docs, Github Page, Open
        Debugger
        """
        self.menubar = wx.MenuBar()

        # -----------------
        # File Menu
        # -----------------

        menu_file = wx.Menu()

        m_change_WD = menu_file.Append(-1,
                                       "Change Working Directory\tCtrl-W", "")
        self.Bind(wx.EVT_MENU, self.on_menu_change_working_directory, m_change_WD)



        m_import_meas_file = menu_file.Append(-1,
                                        "Change measurements file", "")

        self.Bind(wx.EVT_MENU, self.on_menu_import_meas_file, m_import_meas_file)

        m_import_LSQ = menu_file.Append(-1,
                                        "&Import Interpretations from LSQ file\tCtrl-L", "")
        self.Bind(wx.EVT_MENU, self.on_menu_read_from_LSQ, m_import_LSQ)

        m_previous_interpretation = menu_file.Append(
            -1, "&Import interpretations from a redo file\tCtrl-R", "")
        self.Bind(wx.EVT_MENU, self.on_menu_previous_interpretation,
                  m_previous_interpretation)

        m_save_interpretation = menu_file.Append(
            -1, "&Save interpretations to a redo file\tCtrl-S", "")
        self.Bind(wx.EVT_MENU, self.on_menu_save_interpretation,
                  m_save_interpretation)

        m_make_MagIC_results_tables = menu_file.Append(
            -1, "&Save MagIC tables\tCtrl-Shift-S", "")
        self.Bind(wx.EVT_MENU, self.on_menu_make_MagIC_results_tables,
                  m_make_MagIC_results_tables)

        submenu_save_plots = wx.Menu()

        m_save_zij_plot = submenu_save_plots.Append(
            -1, "&Save Zijderveld plot", "")
        self.Bind(wx.EVT_MENU, self.on_save_Zij_plot, m_save_zij_plot, "Zij")

        m_save_eq_plot = submenu_save_plots.Append(
            -1, "&Save specimen equal area plot", "")
        self.Bind(wx.EVT_MENU, self.on_save_Eq_plot,
                  m_save_eq_plot, "specimen-Eq")

        m_save_M_t_plot = submenu_save_plots.Append(-1, "&Save M-t plot", "")
        self.Bind(wx.EVT_MENU, self.on_save_M_t_plot, m_save_M_t_plot, "M_t")

        m_save_high_level = submenu_save_plots.Append(
            -1, "&Save high level plot", "")
        self.Bind(wx.EVT_MENU, self.on_save_high_level,
                  m_save_high_level, "Eq")

        m_save_all_plots = submenu_save_plots.Append(-1, "&Save all plots", "")
        self.Bind(wx.EVT_MENU, self.on_save_all_figures, m_save_all_plots)

        m_new_sub_plots = menu_file.AppendSubMenu(submenu_save_plots, "&Save plot")

        menu_file.AppendSeparator()
        m_exit = menu_file.Append(-1, "E&xit\tCtrl-Q", "Exit")
        self.Bind(wx.EVT_MENU, self.on_menu_exit, m_exit)

        # -----------------
        # Edit Menu
        # -----------------

        menu_edit = wx.Menu()

        m_new = menu_edit.Append(-1, "&New interpretation\tCtrl-N", "")
        self.Bind(wx.EVT_MENU, self.on_btn_add_fit, m_new)

        m_delete = menu_edit.Append(-1, "&Delete interpretation\tCtrl-D", "")
        self.Bind(wx.EVT_MENU, self.on_btn_delete_fit, m_delete)

        m_next_interp = menu_edit.Append(-1,
                                         "&Next interpretation\tCtrl-Up", "")
        self.Bind(wx.EVT_MENU, self.on_menu_next_interp, m_next_interp)

        m_previous_interp = menu_edit.Append(-1,
                                             "&Previous interpretation\tCtrl-Down", "")
        self.Bind(wx.EVT_MENU, self.on_menu_prev_interp, m_previous_interp)

        m_next_specimen = menu_edit.Append(-1,
                                           "&Next Specimen\tCtrl-Right", "")
        self.Bind(wx.EVT_MENU, self.on_next_button, m_next_specimen)

        m_previous_specimen = menu_edit.Append(-1,
                                               "&Previous Specimen\tCtrl-Left", "")
        self.Bind(wx.EVT_MENU, self.on_prev_button, m_previous_specimen)

        menu_flag_meas = wx.Menu()

        m_good = menu_flag_meas.Append(-1, "&Good Measurement\tCtrl-Alt-G", "")
        self.Bind(wx.EVT_MENU, self.on_menu_flag_meas_good, m_good)
        m_bad = menu_flag_meas.Append(-1, "&Bad Measurement\tCtrl-Alt-B", "")
        self.Bind(wx.EVT_MENU, self.on_menu_flag_meas_bad, m_bad)

        m_flag_meas = menu_edit.AppendSubMenu(menu_flag_meas, "&Flag Measurement Data")

        menu_coordinates = wx.Menu()

        m_speci = menu_coordinates.Append(-1,
                                          "&Specimen Coordinates\tCtrl-P", "")
        self.Bind(wx.EVT_MENU, self.on_menu_change_speci_coord, m_speci)
        if "geographic" in self.coordinate_list:
            m_geo = menu_coordinates.Append(-1,
                                            "&Geographic Coordinates\tCtrl-G", "")
            self.Bind(wx.EVT_MENU, self.on_menu_change_geo_coord, m_geo)
        if "tilt-corrected" in self.coordinate_list:
            m_tilt = menu_coordinates.Append(-1,
                                             "&Tilt-Corrected Coordinates\tCtrl-T", "")
            self.Bind(wx.EVT_MENU, self.on_menu_change_tilt_coord, m_tilt)

        m_coords = menu_edit.AppendSubMenu(menu_coordinates, "&Coordinate Systems")

        # -----------------
        # Analysis Menu
        # -----------------

        menu_Analysis = wx.Menu()

        submenu_criteria = wx.Menu()

        m_change_criteria_file = submenu_criteria.Append(
            -1, "&Change acceptance criteria", "")
        self.Bind(wx.EVT_MENU, self.on_menu_change_criteria,
                  m_change_criteria_file)

        m_import_criteria_file = submenu_criteria.Append(
            -1, "&Import criteria file", "")
        self.Bind(wx.EVT_MENU, self.on_menu_criteria_file,
                  m_import_criteria_file)

        m_new_sub = menu_Analysis.AppendSubMenu(submenu_criteria, "Acceptance criteria")

        menu_flag_fit = wx.Menu()

        m_good_fit = menu_flag_fit.Append(-1,
                                          "&Good Interpretation\tCtrl-Shift-G", "")
        self.Bind(wx.EVT_MENU, self.on_menu_flag_fit_good, m_good_fit)
        m_bad_fit = menu_flag_fit.Append(-1,
                                         "&Bad Interpretation\tCtrl-Shift-B", "")
        self.Bind(wx.EVT_MENU, self.on_menu_flag_fit_bad, m_bad_fit)

        m_flag_fit = menu_Analysis.AppendSubMenu(menu_flag_fit, "&Flag Interpretations")

        submenu_sample_check = wx.Menu()

        m_check_orient = submenu_sample_check.Append(
            -1, "&Check Sample Orientations\tCtrl-O", "")
        self.Bind(wx.EVT_MENU, self.on_menu_check_orient, m_check_orient)

        m_mark_samp_bad = submenu_sample_check.Append(
            -1, "&Mark Sample Bad\tCtrl-.", "")
        self.Bind(wx.EVT_MENU, self.on_menu_mark_samp_bad, m_mark_samp_bad)

        m_mark_samp_good = submenu_sample_check.Append(
            -1, "&Mark Sample Good\tCtrl-,", "")
        self.Bind(wx.EVT_MENU, self.on_menu_mark_samp_good, m_mark_samp_good)

        m_submenu = menu_Analysis.AppendSubMenu(submenu_sample_check, "Sample Orientation")

        submenu_toggle_mean_display = wx.Menu()

        lines = ["m_%s_toggle_mean = submenu_toggle_mean_display.AppendCheckItem(-1, '&%s', ''); self.Bind(wx.EVT_MENU, self.on_menu_toggle_mean, m_%s_toggle_mean)" % (
            f, f) for f in self.all_fits_list]

        for line in lines:
            exec(line)

        menu_Analysis.AppendSubMenu(submenu_toggle_mean_display, "Toggle Mean Display")


        # -----------------
        # Tools Menu
        # -----------------

        menu_Tools = wx.Menu()

#        m_auto_interpret = menu_Tools.Append(-1, "&Auto interpret (alpha version)\tCtrl-A", "")
#        self.Bind(wx.EVT_MENU, self.autointerpret, m_auto_interpret)

        m_edit_interpretations = menu_Tools.Append(
            -1, "&Interpretation editor\tCtrl-E", "")
        self.Bind(wx.EVT_MENU, self.on_menu_edit_interpretations,
                  m_edit_interpretations)

        m_view_VGP = menu_Tools.Append(-1, "&View VGPs\tCtrl-Shift-V", "")
        self.Bind(wx.EVT_MENU, self.on_menu_view_vgps, m_view_VGP)

        # -----------------
        # Help Menu
        # -----------------

        menu_Help = wx.Menu()

        m_help = menu_Help.Append(-1, "&Usage and Tips\tCtrl-H", "")
        self.Bind(wx.EVT_MENU, self.on_menu_help, m_help)

        m_cookbook = menu_Help.Append(-1, "&PmagPy Cookbook\tCtrl-Shift-W", "")
        self.Bind(wx.EVT_MENU, self.on_menu_cookbook, m_cookbook)

        m_docs = menu_Help.Append(-1, "&Open Docs\tCtrl-Shift-H", "")
        self.Bind(wx.EVT_MENU, self.on_menu_docs, m_docs)

        m_git = menu_Help.Append(-1, "&Github Page\tCtrl-Shift-G", "")
        self.Bind(wx.EVT_MENU, self.on_menu_git, m_git)

        m_debug = menu_Help.Append(-1, "&Open Debugger\tCtrl-Shift-D", "")
        self.Bind(wx.EVT_MENU, self.on_menu_debug, m_debug)

        # -----------------

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

    def draw_figure(self, s, update_high_plots=True):
        """
        Convenience function that sets current specimen to s and calculates
        data for that specimen then redraws all plots.

        Parameters
        ----------
        s : specimen to set current specimen too
        update_high_plots : bool which decides if high level mean plot
            updates (default: False)
        """
        self.initialize_CART_rot(s)

        # Draw Zij plot
        self.draw_zijderveld()

        # Draw specimen equal area
        self.draw_spec_eqarea()

        # Draw M/M0 plot ( or NLT data on the same area in the GUI)
        self.draw_MM0()

        # If measurements are selected redisplay selected data
        if len(self.selected_meas) > 0:
            self.plot_selected_meas()

        # Draw high level equal area
        if update_high_plots:
            self.plot_high_levels_data()
        self.canvas4.draw()

    def draw_zijderveld(self):
        """
        Draws the zijderveld plot in the GUI on canvas1
        """
        self.fig1.clf()
        axis_bounds = [0, .1, 1, .85]
        self.zijplot = self.fig1.add_axes(
            axis_bounds, frameon=False, facecolor='None', label='zig_orig', zorder=0)
        self.zijplot.clear()
        self.zijplot.axis('equal')
        self.zijplot.xaxis.set_visible(False)
        self.zijplot.yaxis.set_visible(False)

        self.MS = 6*self.GUI_RESOLUTION
        self.dec_MEC = 'k'
        self.dec_MFC = 'r'
        self.inc_MEC = 'k'
        self.inc_MFC = 'b'
        self.MS = 6*self.GUI_RESOLUTION
        self.zijdblock_steps = self.Data[self.s]['zijdblock_steps']
        self.vds = self.Data[self.s]['vds']

        self.zijplot.plot(self.CART_rot_good[:, 0], -1*self.CART_rot_good[:, 1], 'ro-',
                          markersize=self.MS, clip_on=False, picker=True, zorder=1)  # x,y or N,E
        self.zijplot.plot(self.CART_rot_good[:, 0], -1*self.CART_rot_good[:, 2], 'bs-',
                          markersize=self.MS, clip_on=False, picker=True, zorder=1)  # x-z or N,D

        for i in range(len(self.CART_rot_bad)):
            self.zijplot.plot(self.CART_rot_bad[:, 0][i], -1 * self.CART_rot_bad[:, 1][i], 'o', mfc='None',
                              mec=self.dec_MEC, markersize=self.MS, clip_on=False, picker=False)  # x,y or N,E
            self.zijplot.plot(self.CART_rot_bad[:, 0][i], -1 * self.CART_rot_bad[:, 2][i], 's', mfc='None',
                              mec=self.inc_MEC, markersize=self.MS, clip_on=False, picker=False)  # x-z or N,D

        if self.preferences['show_Zij_treatments']:
            for i in range(len(self.zijdblock_steps)):
                if int(self.preferences['show_Zij_treatments_steps']) != 1:
                    if i != 0 and (i+1) % int(self.preferences['show_Zij_treatments_steps']) == 0:
                        self.zijplot.text(self.CART_rot[i][0], -1*self.CART_rot[i][2], "  %s" % (
                            self.zijdblock_steps[i]), fontsize=8*self.GUI_RESOLUTION, color='gray', ha='left', va='center')  # inc
                else:
                    self.zijplot.text(self.CART_rot[i][0], -1*self.CART_rot[i][2], "  %s" % (
                        self.zijdblock_steps[i]), fontsize=10*self.GUI_RESOLUTION, color='gray', ha='left', va='center')  # inc

        # -----

        xmin, xmax = self.zijplot.get_xlim()
        if xmax < 0:
            xmax = 0
        if xmin > 0:
            xmin = 0
        # else:
        #    xmin=xmin+xmin%0.2

        props = dict(color='black', linewidth=1.0, markeredgewidth=0.5)

        xlocs = array(list(arange(0.2, xmax, 0.2)) +
                      list(arange(-0.2, xmin, -0.2)))
        if len(xlocs) > 0:
            xtickline, = self.zijplot.plot(
                xlocs, [0]*len(xlocs), linestyle='', marker='+', **props)
            xtickline.set_clip_on(False)

        axxline, = self.zijplot.plot([xmin, xmax], [0, 0], **props)
        axxline.set_clip_on(False)

        TEXT = ""
        if self.COORDINATE_SYSTEM == 'specimen':
            self.zijplot.text(xmax, 0, ' x', fontsize=10,
                              verticalalignment='bottom')
        else:
            if self.ORTHO_PLOT_TYPE == 'N-S':
                TEXT = " N"
            elif self.ORTHO_PLOT_TYPE == 'E-W':
                TEXT = " E"
            else:
                TEXT = " x"
            self.zijplot.text(xmax, 0, TEXT, fontsize=10,
                              verticalalignment='bottom')

        # -----

        ymin, ymax = self.zijplot.get_ylim()
        if ymax < 0:
            ymax = 0
        if ymin > 0:
            ymin = 0

        ylocs = array(list(arange(0.2, ymax, 0.2)) +
                      list(arange(-0.2, ymin, -0.2)))
        if len(ylocs) > 0:
            ytickline, = self.zijplot.plot(
                [0]*len(ylocs), ylocs, linestyle='', marker='+', **props)
            ytickline.set_clip_on(False)

        axyline, = self.zijplot.plot([0, 0], [ymin, ymax], **props)
        axyline.set_clip_on(False)

        TEXT1, TEXT2 = "", ""
        if self.COORDINATE_SYSTEM == 'specimen':
            TEXT1, TEXT2 = " y", "      z"
        else:
            if self.ORTHO_PLOT_TYPE == 'N-S':
                TEXT1, TEXT2 = " E", "     D"
            elif self.ORTHO_PLOT_TYPE == 'E-W':
                TEXT1, TEXT2 = " S", "     D"
            else:
                TEXT1, TEXT2 = " y", "      z"
        self.zijplot.text(0, ymin, TEXT1, fontsize=10,
                          color='r', verticalalignment='top')
        self.zijplot.text(0, ymin, '    ,', fontsize=10,
                          color='k', verticalalignment='top')
        self.zijplot.text(0, ymin, TEXT2, fontsize=10,
                          color='b', verticalalignment='top')

        # ----

        if self.ORTHO_PLOT_TYPE == 'N-S':
            STRING = ""
            #STRING1="N-S orthogonal plot"
            self.fig1.text(0.01, 0.98, "Zijderveld plot: x = North", {
                           'family': self.font_type, 'fontsize': 10*self.GUI_RESOLUTION, 'style': 'normal', 'va': 'center', 'ha': 'left'})
        elif self.ORTHO_PLOT_TYPE == 'E-W':
            STRING = ""
            #STRING1="E-W orthogonal plot"
            self.fig1.text(0.01, 0.98, "Zijderveld plot:: x = East", {
                           'family': self.font_type, 'fontsize': 10*self.GUI_RESOLUTION, 'style': 'normal', 'va': 'center', 'ha': 'left'})

        elif self.ORTHO_PLOT_TYPE == 'PCA_dec':
            self.fig1.text(0.01, 0.98, "Zijderveld plot", {
                           'family': self.font_type, 'fontsize': 10*self.GUI_RESOLUTION, 'style': 'normal', 'va': 'center', 'ha': 'left'})
            if 'specimen_dec' in list(self.current_fit.pars.keys()) and type(self.current_fit.pars['specimen_dec']) != str:
                STRING = "X-axis rotated to best fit line declination (%.0f); " % (
                    self.current_fit.pars['specimen_dec'])
            else:
                STRING = "X-axis rotated to NRM (%.0f); " % (
                    self.zijblock[0][1])
        else:
            self.fig1.text(0.01, 0.98, "Zijderveld plot", {
                           'family': self.font_type, 'fontsize': 10*self.GUI_RESOLUTION, 'style': 'normal', 'va': 'center', 'ha': 'left'})
            STRING = "X-axis rotated to NRM (%.0f); " % (self.zijblock[0][1])
            #STRING1="Zijderveld plot"

        STRING = STRING+"NRM=%.2e " % (self.zijblock[0][3]) + 'Am^2'
        self.fig1.text(0.01, 0.95, STRING, {'family': self.font_type, 'fontsize': 8 *
                                            self.GUI_RESOLUTION, 'style': 'normal', 'va': 'center', 'ha': 'left'})

        xmin, xmax = self.zijplot.get_xlim()
        ymin, ymax = self.zijplot.get_ylim()

        self.zij_xlim_initial = (xmin, xmax)
        self.zij_ylim_initial = (ymin, ymax)

        self.canvas1.draw()

    def draw_spec_eqarea(self):
        """
        Calculates point positions and draws the Specimen eqarea plot on
        canvas2
        """
        draw_net(self.specimen_eqarea)
        self.specimen_eqarea.text(-1.2, 1.15, "specimen: %s" % self.s, {
                                  'family': self.font_type, 'fontsize': 10*self.GUI_RESOLUTION, 'style': 'normal', 'va': 'center', 'ha': 'left'})

        x_eq = array([row[0] for row in self.zij_norm])
        y_eq = array([row[1] for row in self.zij_norm])
        z_eq = abs(array([row[2] for row in self.zij_norm]))

        # remove bad data from plotting:
        x_eq_good, y_eq_good, z_eq_good = [], [], []
        x_eq_bad, y_eq_bad, z_eq_bad = [], [], []
        for i in range(len(list(self.zij_norm))):
            if self.Data[self.s]['measurement_flag'][i] == 'g':
                x_eq_good.append(self.zij_norm[i][0])
                y_eq_good.append(self.zij_norm[i][1])
                z_eq_good.append(abs(self.zij_norm[i][2]))
            else:
                x_eq_bad.append(self.zij_norm[i][0])
                y_eq_bad.append(self.zij_norm[i][1])
                z_eq_bad.append(abs(self.zij_norm[i][2]))

        x_eq_good, y_eq_good, z_eq_good = array(
            x_eq_good), array(y_eq_good), array(z_eq_good)
        x_eq_bad, y_eq_bad, z_eq_bad = array(
            x_eq_bad), array(y_eq_bad), array(z_eq_bad)

        R_good = array(sqrt(1-z_eq_good)/sqrt(x_eq_good**2 +
                                              y_eq_good**2))  # from Collinson 1983
        # from Collinson 1983
        R_bad = array(sqrt(1-z_eq_bad)/sqrt(x_eq_bad**2+y_eq_bad**2))

        eqarea_data_x_good = y_eq_good*R_good
        eqarea_data_y_good = x_eq_good*R_good

        eqarea_data_x_bad = y_eq_bad*R_bad
        eqarea_data_y_bad = x_eq_bad*R_bad

        self.specimen_eqarea.plot(
            eqarea_data_x_good, eqarea_data_y_good, lw=0.5, color='gray')  # ,zorder=0)

        # --------------------
        # scatter plot
        # --------------------

        x_eq_dn, y_eq_dn, z_eq_dn, eq_dn_temperatures = [], [], [], []
        x_eq_dn = array([row[0] for row in self.zij_norm if row[2] > 0])
        y_eq_dn = array([row[1] for row in self.zij_norm if row[2] > 0])
        z_eq_dn = abs(array([row[2] for row in self.zij_norm if row[2] > 0]))

        if len(x_eq_dn) > 0:
            # from Collinson 1983
            R = array(sqrt(1-z_eq_dn)/sqrt(x_eq_dn**2+y_eq_dn**2))
            eqarea_data_x_dn = y_eq_dn*R
            eqarea_data_y_dn = x_eq_dn*R
            self.specimen_eqarea.scatter([eqarea_data_x_dn], [eqarea_data_y_dn], marker='o',
                                         edgecolor='black', facecolor="#808080", s=15*self.GUI_RESOLUTION, lw=1, clip_on=False)

        x_eq_up, y_eq_up, z_eq_up = [], [], []
        x_eq_up = array([row[0] for row in self.zij_norm if row[2] <= 0])
        y_eq_up = array([row[1] for row in self.zij_norm if row[2] <= 0])
        z_eq_up = abs(array([row[2] for row in self.zij_norm if row[2] <= 0]))
        if len(x_eq_up) > 0:
            # from Collinson 1983
            R = array(sqrt(1-z_eq_up)/sqrt(x_eq_up**2+y_eq_up**2))
            eqarea_data_x_up = y_eq_up*R
            eqarea_data_y_up = x_eq_up*R
            self.specimen_eqarea.scatter([eqarea_data_x_up], [eqarea_data_y_up], marker='o',
                                         edgecolor='black', facecolor="#FFFFFF", s=15*self.GUI_RESOLUTION, lw=1, clip_on=False)

        # self.preferences['show_eqarea_treatments']=True
        if self.preferences['show_eqarea_treatments']:
            for i in range(len(self.zijdblock_steps)):
                self.specimen_eqarea.text(eqarea_data_x[i], eqarea_data_y[i], "%.1f" % float(
                    self.zijdblock_steps[i]), fontsize=8*self.GUI_RESOLUTION, color="0.5")

        # add line to show the direction of the x axis in the Zijderveld plot

        if str(self.orthogonal_box.GetValue()) in ["X=best fit line dec", "X=NRM dec"]:
            XY = []
            if str(self.orthogonal_box.GetValue()) == "X=NRM dec":
                dec_zij = self.zijblock[0][1]
                XY = pmag.dimap(dec_zij, 0)
            if str(self.orthogonal_box.GetValue()) == "X=best fit line dec":
                if 'specimen_dec' in list(self.current_fit.pars.keys()) and type(self.current_fit.pars['specimen_dec']) != str:
                    dec_zij = self.current_fit.pars['specimen_dec']
                    XY = pmag.dimap(dec_zij, 0)
            if XY != []:
                self.specimen_eqarea.plot(
                    [0, XY[0]], [0, XY[1]], ls='-', c='gray', lw=0.5)  # ,zorder=0)

        self.canvas2.draw()

    def draw_MM0(self):
        """
        Draws the M/M0 plot in the GUI on canvas3
        """
        self.fig3.clf()
        self.fig3.text(0.02, 0.96, 'M/M0', {'family': self.font_type, 'fontsize': 10 *
                                            self.GUI_RESOLUTION, 'style': 'normal', 'va': 'center', 'ha': 'left'})
        self.mplot = self.fig3.add_axes(
            [0.2, 0.15, 0.7, 0.7], frameon=True, facecolor='None')

        thermal_x, thermal_y = [], []
        thermal_x_bad, thermal_y_bad = [], []
        af_x, af_y = [], []
        af_x_bad, af_y_bad = [], []
        for i in range(len(self.Data[self.s]['zijdblock'])):
            step = self.Data[self.s]['zijdblock_steps'][i]
            # bad point
            if self.Data[self.s]['measurement_flag'][i] == 'b':
                if step == "0":
                    thermal_x_bad.append(self.Data[self.s]['zijdblock'][i][0])
                    af_x_bad.append(self.Data[self.s]['zijdblock'][i][0])
                    thermal_y_bad.append(
                        self.Data[self.s]['zijdblock'][i][3]/self.Data[self.s]['zijdblock'][0][3])
                    af_y_bad.append(
                        self.Data[self.s]['zijdblock'][i][3]/self.Data[self.s]['zijdblock'][0][3])
                elif "C" in step:
                    thermal_x_bad.append(self.Data[self.s]['zijdblock'][i][0])
                    thermal_y_bad.append(
                        self.Data[self.s]['zijdblock'][i][3]/self.Data[self.s]['zijdblock'][0][3])
                elif "T" in step:
                    af_x_bad.append(self.Data[self.s]['zijdblock'][i][0])
                    af_y_bad.append(
                        self.Data[self.s]['zijdblock'][i][3]/self.Data[self.s]['zijdblock'][0][3])
                else:
                    continue

            else:
                if step == "0":
                    thermal_x.append(self.Data[self.s]['zijdblock'][i][0])
                    af_x.append(self.Data[self.s]['zijdblock'][i][0])
                    thermal_y.append(
                        self.Data[self.s]['zijdblock'][i][3]/self.Data[self.s]['zijdblock'][0][3])
                    af_y.append(self.Data[self.s]['zijdblock'][i]
                                [3]/self.Data[self.s]['zijdblock'][0][3])
                elif "C" in step:
                    thermal_x.append(self.Data[self.s]['zijdblock'][i][0])
                    thermal_y.append(
                        self.Data[self.s]['zijdblock'][i][3]/self.Data[self.s]['zijdblock'][0][3])
                elif "T" in step:
                    af_x.append(self.Data[self.s]['zijdblock'][i][0])
                    af_y.append(self.Data[self.s]['zijdblock'][i]
                                [3]/self.Data[self.s]['zijdblock'][0][3])
                else:
                    continue

        if len(thermal_x)+len(thermal_x_bad) > self.Data[self.s]['zijdblock_steps'].count('0'):
            self.mplot.plot(thermal_x, thermal_y, 'ro-',
                            markersize=self.MS, lw=1, clip_on=False, zorder=1)
            for i in range(len(thermal_x_bad)):
                self.mplot.plot([thermal_x_bad[i]], [thermal_y_bad[i]], 'o',
                                mfc='None', mec='k', markersize=self.MS, clip_on=False, zorder=1)

        self.mplot.set_xlabel('Thermal (C)', color='r')
        for tl in self.mplot.get_xticklabels():
            tl.set_color('r')

        self.mplot_af = self.mplot.twiny()
        if len(af_x)+len(af_x_bad) > self.Data[self.s]['zijdblock_steps'].count('0'):
            self.mplot_af.plot(
                af_x, af_y, 'bo-', markersize=self.MS, lw=1, clip_on=False, zorder=1)
            for i in range(len(af_x_bad)):
                self.mplot_af.plot([af_x_bad[i]], [
                                   af_y_bad[i]], 'o', mfc='None', mec='k', markersize=self.MS, clip_on=False, zorder=1)

        self.mplot_af.set_xlabel('AF (mT)', color='b')
        for tl in self.mplot_af.get_xticklabels():
            tl.set_color('b')

        self.mplot.tick_params(axis='both', which='major', labelsize=7)
        self.mplot_af.tick_params(axis='both', which='major', labelsize=7)
        self.mplot.spines["right"].set_visible(False)
        self.mplot_af.spines["right"].set_visible(False)
        self.mplot.get_xaxis().tick_bottom()
        self.mplot.get_yaxis().tick_left()
        self.mplot.set_ylabel("M / NRM0", fontsize=8*self.GUI_RESOLUTION)

        self.canvas3.draw()

    def plot_selected_meas(self):
        """
        Goes through all measurements selected in logger and draws darker
        marker over all specimen plots to display which measurements have
        been selected
        """
        self.close_warning = True
        # set hex colors for cover and size of selected meas marker
        blue_cover = "#9999FF"
        red_cover = "#FF9999"
        eqarea_outline = "#FF0000"
        MS_selected = 40

        # remove old selected points
        for a in self.selected_meas_artists:
            if a in self.zijplot.collections:
                self.zijplot.collections.remove(a)
            if a in self.specimen_eqarea.collections:
                self.specimen_eqarea.collections.remove(a)
            if a in self.mplot.collections:
                self.mplot.collections.remove(a)
            if a in self.mplot_af.collections:
                self.mplot_af.collections.remove(a)

        # do zijderveld plot
        self.selected_meas_artists = []
        x, y, z = self.CART_rot[self.selected_meas,
                                0], self.CART_rot[self.selected_meas, 1], self.CART_rot[self.selected_meas, 2]
        self.selected_meas_artists.append(self.zijplot.scatter(
            x, -1*y, c=red_cover, marker='o', s=MS_selected, zorder=2))
        self.selected_meas_artists.append(self.zijplot.scatter(
            x, -1*z, c=blue_cover, marker='s', s=MS_selected, zorder=2))

        # do down data for eqarea
        x_eq = array([row[0] for i, row in enumerate(self.zij_norm)
                      if i in self.selected_meas and row[2] > 0])
        y_eq = array([row[1] for i, row in enumerate(self.zij_norm)
                      if i in self.selected_meas and row[2] > 0])
        z_eq = abs(array([row[2] for i, row in enumerate(
            self.zij_norm) if i in self.selected_meas and row[2] > 0]))
        if len(x_eq) > 0:
            # from Collinson 1983
            R = array(sqrt(1-z_eq)/sqrt(x_eq**2+y_eq**2))
            eqarea_data_x = y_eq*R
            eqarea_data_y = x_eq*R
            self.selected_meas_artists.append(self.specimen_eqarea.scatter([eqarea_data_x], [
                                              eqarea_data_y], marker='o', edgecolor=eqarea_outline, facecolor="#808080", s=15*self.GUI_RESOLUTION, lw=1, clip_on=False))

        # do up data for eqarea
        x_eq = array([row[0] for i, row in enumerate(self.zij_norm)
                      if i in self.selected_meas and row[2] < 0])
        y_eq = array([row[1] for i, row in enumerate(self.zij_norm)
                      if i in self.selected_meas and row[2] < 0])
        z_eq = abs(array([row[2] for i, row in enumerate(
            self.zij_norm) if i in self.selected_meas and row[2] < 0]))
        if len(x_eq) > 0:
            # from Collinson 1983
            R = array(sqrt(1-z_eq)/sqrt(x_eq**2+y_eq**2))
            eqarea_data_x = y_eq*R
            eqarea_data_y = x_eq*R
            self.selected_meas_artists.append(self.specimen_eqarea.scatter([eqarea_data_x], [
                                              eqarea_data_y], marker='o', edgecolor=eqarea_outline, facecolor="#FFFFFF", s=15*self.GUI_RESOLUTION, lw=1, clip_on=False))

        # do M/M0 plot
        steps = self.Data[self.s]['zijdblock_steps']
        flags = self.Data[self.s]['measurement_flag']
        selected_af_meas = [
            i for i in self.selected_meas if "T" in steps[i] or steps[i] == "0" and flags[i] != "b"]
        selected_T_meas = [i for i in self.selected_meas if "C" in steps[i]
                           or steps[i] == "0" and flags[i] != "b"]
        data = array(self.Data[self.s]['zijdblock'])
        af_x = array(list(map(float, data[selected_af_meas, 0])))
        af_y = array(
            list(map(float, data[selected_af_meas, 3])))/float(data[0, 3])
        T_x = array(list(map(float, data[selected_T_meas, 0])))
        T_y = array(
            list(map(float, data[selected_T_meas, 3])))/float(data[0, 3])

        xmin, xmax = self.mplot.get_xlim()
        ymin, ymax = self.mplot.get_ylim()
        if T_x.astype(float).any() or T_y.astype(float).any():
            self.selected_meas_artists.append(self.mplot.scatter(
                T_x, T_y, facecolor=red_cover, edgecolor="#000000", marker='o', s=30, lw=1, clip_on=False, zorder=3))
        self.mplot.set_xlim([xmin, xmax])
        self.mplot.set_ylim([ymin, ymax])

        xmin, xmax = self.mplot_af.get_xlim()
        ymin, ymax = self.mplot_af.get_ylim()
        if af_x.astype(float).any() or af_y.astype(float).any():
            self.selected_meas_artists.append(self.mplot_af.scatter(
                af_x, af_y, facecolor=blue_cover, edgecolor="#000000", marker='o', s=30, lw=1, clip_on=False, zorder=3))
        self.mplot_af.set_xlim([xmin, xmax])
        self.mplot_af.set_ylim([ymin, ymax])

        self.canvas1.draw()
        self.canvas2.draw()
        self.canvas3.draw()

    def draw_interpretations(self):
        """
        draw the specimen interpretations on the zijderveld, the specimen
        equal area, and the M/M0 plots

        Alters
        ------
        fit.lines, fit.points, fit.eqarea_data, fit.mm0_data,
        zijplot, specimen_eqarea_interpretation, mplot_interpretation
        """

        problems = {}

        if self.s in self.pmag_results_data['specimens'] and \
                self.pmag_results_data['specimens'][self.s] != []:
            #            self.zijplot.collections=[] # delete fit points
            self.specimen_EA_xdata = []  # clear saved x positions on specimen equal area
            self.specimen_EA_ydata = []  # clear saved y positions on specimen equal area

        # check to see if there's a results log or not
        if not (self.s in list(self.pmag_results_data['specimens'].keys())):
            self.pmag_results_data['specimens'][self.s] = []

        for fit in self.pmag_results_data['specimens'][self.s]:

            pars = fit.get(self.COORDINATE_SYSTEM)

            if (fit.tmin == None or fit.tmax == None or not pars):
                if 'no bounds' not in list(problems.keys()):
                    problems['no bounds'] = []
                problems['no bounds'].append(fit)
                continue

            for line in fit.lines:
                if line in self.zijplot.lines:
                    self.zijplot.lines.remove(line)
            for point in fit.points:
                if point in self.zijplot.collections:
                    self.zijplot.collections.remove(point)

            PCA_type = fit.PCA_type

            tmin_index, tmax_index = self.get_indices(fit)

            marker_shape = 'o'
            SIZE = 20
            if fit == self.current_fit:
                marker_shape = 'D'
            if pars['calculation_type'] == "DE-BFP":
                marker_shape = 's'
                if "bfv" in self.plane_display_box.GetValue():
                    marker_shape = '>'
            if fit in self.bad_fits:
                marker_shape = (4, 1, 0)
                SIZE = 30*self.GUI_RESOLUTION

            # Zijderveld plot

            ymin, ymax = self.zijplot.get_ylim()
            xmin, xmax = self.zijplot.get_xlim()

            for i in range(1):
                if (len(self.CART_rot[:, i]) <= tmin_index or
                        len(self.CART_rot[:, i]) <= tmax_index):
                    self.Add_text()

            self.zijplot.scatter([self.CART_rot[:, 0][tmin_index], self.CART_rot[:, 0][tmax_index]], [-1 * self.CART_rot[:, 1][tmin_index], -
                                                                                                      1 * self.CART_rot[:, 1][tmax_index]], marker=marker_shape, s=40, facecolor=fit.color, edgecolor='k', zorder=100, clip_on=False)
            self.zijplot.scatter([self.CART_rot[:, 0][tmin_index], self.CART_rot[:, 0][tmax_index]], [-1 * self.CART_rot[:, 2][tmin_index], -
                                                                                                      1 * self.CART_rot[:, 2][tmax_index]], marker=marker_shape, s=40, facecolor=fit.color, edgecolor='k', zorder=100, clip_on=False)
            fit.points[0] = self.zijplot.collections[-1]
            fit.points[1] = self.zijplot.collections[-2]

            if pars['calculation_type'] in ['DE-BFL', 'DE-BFL-A', 'DE-BFL-O']:

                # rotated zijderveld
                if self.COORDINATE_SYSTEM == 'geographic' and len(self.Data[self.s]['zdata_geo']) > 0:
                    first_data = self.Data[self.s]['zdata_geo'][0]
                elif self.COORDINATE_SYSTEM == 'tilt-corrected' and len(self.Data[self.s]['zdata_tilt']) > 0:
                    first_data = self.Data[self.s]['zdata_tilt'][0]
                else:
                    first_data = self.Data[self.s]['zdata'][0]
                    if self.COORDINATE_SYSTEM != 'specimen':
                        self.on_menu_change_speci_coord(-1)
                        pars = fit.get(self.COORDINATE_SYSTEM)

                if self.ORTHO_PLOT_TYPE == 'N-S':
                    rotation_declination = 0.
                elif self.ORTHO_PLOT_TYPE == 'E-W':
                    rotation_declination = 90.
                elif self.ORTHO_PLOT_TYPE == 'PCA_dec':
                    if 'specimen_dec' in list(pars.keys()) and type(pars['specimen_dec']) != str:
                        rotation_declination = pars['specimen_dec']
                    else:
                        rotation_declination = pmag.cart2dir(first_data)[0]
                else:  # Zijderveld
                    rotation_declination = pmag.cart2dir(first_data)[0]

                PCA_dir = [pars['specimen_dec'], pars['specimen_inc'], 1]
                PCA_dir_rotated = [PCA_dir[0] -
                                   rotation_declination, PCA_dir[1], 1]
                PCA_CART_rotated = pmag.dir2cart(PCA_dir_rotated)

                slop_xy_PCA = -1*PCA_CART_rotated[1]/PCA_CART_rotated[0]
                slop_xz_PCA = -1*PCA_CART_rotated[2]/PCA_CART_rotated[0]

                # Center of mass rotated for plotting
                CM_x = mean(self.CART_rot_good[:, 0][tmin_index:tmax_index+1])
                CM_y = mean(self.CART_rot_good[:, 1][tmin_index:tmax_index+1])
                CM_z = mean(self.CART_rot_good[:, 2][tmin_index:tmax_index+1])

                # intercpet from the center of mass
                intercept_xy_PCA = -1*CM_y - slop_xy_PCA*CM_x
                intercept_xz_PCA = -1*CM_z - slop_xz_PCA*CM_x

                xx = array([self.CART_rot[:, 0][tmax_index],
                            self.CART_rot[:, 0][tmin_index]])
                yy = slop_xy_PCA*xx+intercept_xy_PCA
                zz = slop_xz_PCA*xx+intercept_xz_PCA

                if (pars['calculation_type'] in ['DE-BFL-A']):  # CHECK
                    xx = [0.] + xx
                    yy = [0.] + yy
                    zz = [0.] + zz

                self.zijplot.plot(xx, yy, '-', color=fit.color,
                                  lw=3, alpha=0.5, zorder=0)
                self.zijplot.plot(xx, zz, '-', color=fit.color,
                                  lw=3, alpha=0.5, zorder=0)

                fit.lines[0] = self.zijplot.lines[-2]
                fit.lines[1] = self.zijplot.lines[-1]

            # Equal Area plot
            self.toolbar2.home()

            # delete old interpretation data
            for d in fit.eqarea_data:
                if d in self.specimen_eqarea.lines:
                    self.specimen_eqarea.lines.remove(d)
                if d in self.specimen_eqarea.collections:
                    self.specimen_eqarea.collections.remove(d)

            if pars['calculation_type'] == 'DE-BFP' and \
               self.plane_display_box.GetValue() != "poles":

                # draw a best-fit plane
                ymin, ymax = self.specimen_eqarea.get_ylim()
                xmin, xmax = self.specimen_eqarea.get_xlim()

                D_c, I_c = pmag.circ(
                    pars["specimen_dec"], pars["specimen_inc"], 90)
                X_c_up, Y_c_up = [], []
                X_c_d, Y_c_d = [], []
                for k in range(len(D_c)):
                    XY = pmag.dimap(D_c[k], I_c[k])
                    if I_c[k] < 0:
                        X_c_up.append(XY[0])
                        Y_c_up.append(XY[1])
                    if I_c[k] > 0:
                        X_c_d.append(XY[0])
                        Y_c_d.append(XY[1])

                if self.plane_display_box.GetValue() == "u. hemisphere" or \
                   self.plane_display_box.GetValue() == "whole plane" or \
                   "wp" in self.plane_display_box.GetValue():
                    self.specimen_eqarea.plot(X_c_d, Y_c_d, 'b')
                if self.plane_display_box.GetValue() == "l. hemisphere" or \
                   self.plane_display_box.GetValue() == "whole plane" or \
                   "wp" in self.plane_display_box.GetValue():
                    self.specimen_eqarea.plot(X_c_up, Y_c_up, 'c')
                eqarea_x = XY[0]
                eqarea_y = XY[1]
                z = 1
                fit.eqarea_data[0] = self.specimen_eqarea.lines[-1]
                fit.eqarea_data[1] = self.specimen_eqarea.lines[-2]

                if "bfv" in self.plane_display_box.GetValue():
                    if 'bfv_dec' not in list(pars.keys()) or 'bfv_inc' not in list(pars.keys()):
                        self.calculate_best_fit_vectors()
                        pars = fit.get(self.COORDINATE_SYSTEM)
                    try:
                        CART = pmag.dir2cart(
                            [pars['bfv_dec'], pars['bfv_inc'], 1])
                        x = CART[0]
                        y = CART[1]
                        z = CART[2]
                        R = array(sqrt(1-abs(z))/sqrt(x**2+y**2))
                        eqarea_x = y*R
                        eqarea_y = x*R
                    except KeyError:
                        print(("specimen %s fit %s is marked bad or there was an error calculating bfv pole will be displayed instead" % (
                            element, fit.name)))

            else:
                CART = pmag.dir2cart(
                    [pars['specimen_dec'], pars['specimen_inc'], 1])
                x = CART[0]
                y = CART[1]
                z = CART[2]
                R = array(sqrt(1-abs(z))/sqrt(x**2+y**2))
                eqarea_x = y*R
                eqarea_y = x*R

            self.specimen_EA_xdata.append(eqarea_x)
            self.specimen_EA_ydata.append(eqarea_y)
            if z > 0:
                FC = fit.color
                EC = '0.1'
            else:
                FC = (1, 1, 1)
                EC = fit.color
            self.specimen_eqarea.scatter([eqarea_x], [
                                         eqarea_y], marker=marker_shape, edgecolor=EC, facecolor=FC, s=SIZE, lw=1, clip_on=False)
            fit.eqarea_data[0] = self.specimen_eqarea.collections[-1]

            # M/M0 plot (only if C or mT - not both)
            for d in fit.mm0_data:
                if d in self.mplot.collections:
                    self.mplot.collections.remove(d)
                elif d in self.mplot_af.collections:
                    self.mplot_af.collections.remove(d)
            temp_data_exists = any(
                ['C' in step for step in self.Data[self.s]['zijdblock_steps']])
            af_data_exists = any(
                ['T' in step for step in self.Data[self.s]['zijdblock_steps']])
            if "C" in fit.tmin and temp_data_exists:
                tmin_ax = self.mplot
            elif af_data_exists:
                tmin_ax = self.mplot_af
            else:
                tmin_ax = self.mplot
            if "C" in fit.tmax and temp_data_exists:
                tmax_ax = self.mplot
            elif af_data_exists:
                tmax_ax = self.mplot_af
            else:
                tmax_ax = self.mplot
            tmin_ymin, tmin_ymax = tmin_ax.get_ylim()
            tmin_xmin, tmin_xmax = tmin_ax.get_xlim()
            tmax_ymin, tmax_ymax = tmax_ax.get_ylim()
            tmax_xmin, tmax_xmax = tmax_ax.get_xlim()
            fit.mm0_data[0] = tmin_ax.scatter([self.Data[self.s]['zijdblock'][tmin_index][0]], [self.Data[self.s]['zijdblock'][tmin_index][3] /
                                                                                                self.Data[self.s]['zijdblock'][0][3]], marker=marker_shape, s=30, facecolor=fit.color, edgecolor='k', zorder=10000, clip_on=False)
            fit.mm0_data[1] = tmax_ax.scatter([self.Data[self.s]['zijdblock'][tmax_index][0]], [self.Data[self.s]['zijdblock'][tmax_index][3] /
                                                                                                self.Data[self.s]['zijdblock'][0][3]], marker=marker_shape, s=30, facecolor=fit.color, edgecolor='k', zorder=10000, clip_on=False)
            tmin_ax.set_xlim(tmin_xmin, tmin_xmax)
            tmin_ax.set_ylim(tmin_ymin, tmin_ymax)
            tmax_ax.set_xlim(tmax_xmin, tmax_xmax)
            tmax_ax.set_ylim(tmax_ymin, tmax_ymax)

            # logger
            if fit == self.current_fit:
                for item in range(self.logger.GetItemCount()):
                    if item >= tmin_index and item <= tmax_index:
                        self.logger.SetItemBackgroundColour(item, "LIGHT BLUE")
                    else:
                        self.logger.SetItemBackgroundColour(item, "WHITE")
                    try:
                        relability = self.Data[self.s]['measurement_flag'][item]
                    except IndexError:
                        relability = 'b'
                    if relability == 'b':
                        self.logger.SetItemBackgroundColour(item, "red")

        if problems != {}:
            if 'no bounds' in list(problems.keys()):
                text = "Fits "
                for problem in problems['no bounds']:
                    text += fit.name + ' '
                text += " for the current specimen are missing bounds and will not be displayed."

        self.canvas1.draw()
        self.canvas2.draw()
        self.canvas3.draw()

    def plot_high_levels_data(self):
        """
        Complicated function that draws the high level mean plot on canvas4,
        draws all specimen, sample, or site interpretations according to the
        UPPER_LEVEL_SHOW variable, draws the fisher mean or fisher mean by
        polarity of all interpretations displayed, draws sample orientation
        check if on, and if interpretation editor is open it calls the
        interpretation editor to have it draw the same things.
        """
#        self.toolbar4.home()
        high_level = self.level_box.GetValue()
        self.UPPER_LEVEL_NAME = self.level_names.GetValue()
        self.UPPER_LEVEL_MEAN = self.mean_type_box.GetValue()

        draw_net(self.high_level_eqarea)
        what_is_it = self.level_box.GetValue()+": "+self.level_names.GetValue()
        self.high_level_eqarea.text(-1.2, 1.15, what_is_it, {
                                    'family': self.font_type, 'fontsize': 10*self.GUI_RESOLUTION, 'style': 'normal', 'va': 'center', 'ha': 'left'})
        if self.ie_open:
            self.ie.draw_net()
            self.ie.write(what_is_it)

        # plot elements directions
        self.plot_high_level_elements()

        # plot elements means
        self.plot_high_level_means()

        # update high level stats after plotting in case of change
        self.update_high_level_stats()

        # check sample orietation
        if self.check_orient_on:
            self.calc_and_plot_sample_orient_check()

        self.canvas4.draw()

        if self.ie_open:
            self.ie.draw()

    def get_levels_and_coordinates_names(self):
        """
        Get the current level of the high level mean plot and the name of
        the corrisponding site, study, etc. As well as the code for the
        current coordinate system.

        Returns
        -------
        (high_level_type,high_level_name,coordinate_system) : tuple object
            containing current high level type, name, and coordinate system
            being analyzed
        """
        if self.COORDINATE_SYSTEM == "geographic":
            dirtype = 'DA-DIR-GEO'
        elif self.COORDINATE_SYSTEM == "tilt-corrected":
            dirtype = 'DA-DIR-TILT'
        else:
            dirtype = 'DA-DIR'

        if self.level_box.GetValue() == 'sample':
            high_level_type = 'samples'
        if self.level_box.GetValue() == 'site':
            high_level_type = 'sites'
        if self.level_box.GetValue() == 'location':
            high_level_type = 'locations'
        if self.level_box.GetValue() == 'study':
            high_level_type = 'study'
        high_level_name = str(self.level_names.GetValue())
        return (high_level_type, high_level_name, dirtype)

    def plot_high_level_elements(self):
        elements_type = self.UPPER_LEVEL_SHOW
        (high_level_type, high_level_name,
         dirtype), mean_fit = self.get_levels_and_coordinates_names(), self.mean_fit
        elements_list = self.Data_hierarchy[high_level_type][high_level_name][elements_type]

        self.high_EA_xdata = []  # clear saved x positions on high equal area
        self.high_EA_ydata = []  # clear saved y positions on high equal area

        for element in elements_list:
            if element not in list(self.pmag_results_data[elements_type].keys()) and elements_type == 'specimens':
                self.calculate_high_level_mean(
                    elements_type, element, "Fisher", "specimens", mean_fit)
            if element in list(self.pmag_results_data[elements_type].keys()):
                self.plot_high_level_equalarea(element)
            else:
                if element not in list(self.high_level_means[elements_type].keys()):
                    self.calculate_high_level_mean(
                        elements_type, element, "Fisher", 'specimens', mean_fit)
                if mean_fit not in list(self.high_level_means[elements_type][element].keys()):
                    self.calculate_high_level_mean(
                        elements_type, element, "Fisher", 'specimens', mean_fit)
                if element in list(self.high_level_means[elements_type].keys()):
                    if mean_fit != "All" and mean_fit in list(self.high_level_means[elements_type][element].keys()):
                        if dirtype in list(self.high_level_means[elements_type][element][mean_fit].keys()):
                            mpars = self.high_level_means[elements_type][element][mean_fit][dirtype]
                            self.plot_eqarea_pars(
                                mpars, self.high_level_eqarea)
                    else:
                        for mf in self.all_fits_list:
                            if mf not in list(self.high_level_means[elements_type][element].keys()):
                                self.calculate_high_level_mean(
                                    elements_type, element, "Fisher", 'specimens', mf)
                            if mf in list(self.high_level_means[elements_type][element].keys()):
                                if dirtype in list(self.high_level_means[elements_type][element][mf].keys()):
                                    mpars = self.high_level_means[elements_type][element][mf][dirtype]
                                    self.plot_eqarea_pars(
                                        mpars, self.high_level_eqarea)

    def remove_previously_displayed_means(self):
        for dm in self.displayed_means:
            if not hasattr(dm, '__iter__'):
                dm = [dm]
            for d in dm:
                if d in self.high_level_eqarea.lines:
                    self.high_level_eqarea.lines.remove(d)
                elif self.ie_open and d in self.ie.eqarea.lines:
                    self.ie.eqarea.lines.remove(d)
                elif d in self.high_level_eqarea.collections:
                    self.high_level_eqarea.collections.remove(d)
                elif self.ie_open and d in self.ie.eqarea.collections:
                    self.ie.eqarea.collections.remove(d)
        self.displayed_means = []

    def plot_high_level_means(self):
        self.remove_previously_displayed_means()
        if self.UPPER_LEVEL_SHOW != "specimens":
            self.mean_type_box.SetValue("None")
            if self.ie_open:
                self.ie.mean_type_box.SetValue("None")
            return
        calculation_type = str(self.mean_type_box.GetValue())
        (high_level_type, high_level_name,
         dirtype), mean_fit = self.get_levels_and_coordinates_names(), self.mean_fit
        if calculation_type == "None":
            return
        elif high_level_name not in list(self.high_level_means[high_level_type].keys()):
            return
        if mean_fit != "All":
            if mean_fit in list(self.high_level_means[high_level_type][high_level_name].keys()) and dirtype in list(self.high_level_means[high_level_type][high_level_name][mean_fit].keys()):
                self.plot_eqarea_mean(
                    self.high_level_means[high_level_type][high_level_name][mean_fit][dirtype], self.high_level_eqarea)
        else:
            means_to_plot = self.get_means_to_plot()
            for mf in means_to_plot+['All']:
                if mf not in list(self.high_level_means[high_level_type][high_level_name].keys()) or (dirtype in self.high_level_means[high_level_type][high_level_name][mf] and 'calculation_type' in self.high_level_means[high_level_type][high_level_name][mf][dirtype] and self.high_level_means[high_level_type][high_level_name][mf][dirtype]['calculation_type'] != calculation_type):
                    self.calculate_high_level_mean(
                        high_level_type, high_level_name, calculation_type, self.UPPER_LEVEL_SHOW, mf)
                if mf in list(self.high_level_means[high_level_type][high_level_name].keys()) and dirtype in list(self.high_level_means[high_level_type][high_level_name][mf].keys()):
                    self.plot_eqarea_mean(
                        self.high_level_means[high_level_type][high_level_name][mf][dirtype], self.high_level_eqarea)

    def get_means_to_plot(self):
        mb = self.GetMenuBar()
        am = mb.GetMenu(2)
        toggleable_means = am.GetMenuItems()[3].SubMenu.GetMenuItems()
        means_to_plot = []
        for tm in toggleable_means:
            if not tm.IsChecked():
                means_to_plot.append(tm.GetLabel())
        return means_to_plot

    def calc_and_plot_sample_orient_check(self):
        """
        If sample orientation is on plots the wrong arrow, wrong compass,
        and rotated sample error directions for the current specimen
        interpretation on the high level mean plot so that you can check
        sample orientation good/bad.
        """
        fit = self.current_fit
        if fit == None:
            return
        pars = fit.get('specimen')
        if 'specimen_dec' not in list(pars.keys()) or 'specimen_inc' not in list(pars.keys()):
            fit.put(self.s, 'specimen', self.get_PCA_parameters(
                self.s, fit, fit.tmin, fit.tmax, 'specimen', fit.PCA_type))
            pars = fit.get('specimen')
            if not pars:
                self.user_warning(
                    "could not calculate fit %s for specimen %s in specimen coordinate system while checking sample orientation please check data" % (fit.name, self.s))
                return
        dec, inc = pars['specimen_dec'], pars['specimen_inc']
        sample = self.Data_hierarchy['sample_of_specimen'][self.s]
        if sample not in list(self.Data_info["er_samples"].keys()) or "sample_azimuth" not in list(self.Data_info["er_samples"][sample].keys()) or "sample_dip" not in list(self.Data_info["er_samples"][sample].keys()):
            self.user_warning(
                "Could not display sample orientation checks because sample azimuth or sample dip is missing from er_samples table for sample %s" % sample)
            self.check_orient_on = False  # stop trying because this raises a ton of warnings
            return
        try:
            azimuth = float(self.Data_info["er_samples"][sample]['sample_azimuth'])
            dip = float(self.Data_info["er_samples"][sample]['sample_dip'])
        except TypeError:
            self.user_warning(
                "Could not display sample orientation checks because azimuth or dip is missing (or invalid) for sample %s" % sample)
            self.check_orient_on = False # stop trying because this raises a ton of warnings
            return

        # first test wrong direction of drill arrows (flip drill direction in opposite direction and re-calculate d,i)
        d, i = pmag.dogeo(dec, inc, azimuth-180., -dip)
        XY = pmag.dimap(d, i)
        if i > 0:
            FC = fit.color
            SIZE = 15*self.GUI_RESOLUTION
        else:
            FC = 'white'
            SIZE = 15*self.GUI_RESOLUTION
        self.high_level_eqarea.scatter([XY[0]], [
                                       XY[1]], marker='^', edgecolor=fit.color, facecolor=FC, s=SIZE, lw=1, clip_on=False)
        if self.ie_open:
            self.ie.scatter([XY[0]], [XY[1]], marker='^', edgecolor=fit.color,
                            facecolor=FC, s=SIZE, lw=1, clip_on=False)
        # Then test wrong end of compass (take az-180.)
        d, i = pmag.dogeo(dec, inc, azimuth-180., dip)
        XY = pmag.dimap(d, i)
        if i > 0:
            FC = fit.color
            SIZE = 15*self.GUI_RESOLUTION
        else:
            FC = 'white'
            SIZE = 15*self.GUI_RESOLUTION
        self.high_level_eqarea.scatter([XY[0]], [
                                       XY[1]], marker='v', edgecolor=fit.color, facecolor=FC, s=SIZE, lw=1, clip_on=False)
        if self.ie_open:
            self.ie.scatter([XY[0]], [XY[1]], marker='v', edgecolor=fit.color,
                            facecolor=FC, s=SIZE, lw=1, clip_on=False)
        # did the sample spin in the hole?
        # now spin around specimen's z
        X_up, Y_up, X_d, Y_d = [], [], [], []
        for incr in range(0, 360, 5):
            d, i = pmag.dogeo(dec+incr, inc, azimuth, dip)
            XY = pmag.dimap(d, i)
            if i >= 0:
                X_d.append(XY[0])
                Y_d.append(XY[1])
            else:
                X_up.append(XY[0])
                Y_up.append(XY[1])
        self.high_level_eqarea.scatter(
            X_d, Y_d, marker='.', color=fit.color, alpha=.5, s=SIZE/2, lw=1, clip_on=False)
        self.high_level_eqarea.scatter(
            X_up, Y_up, marker='.', color=fit.color, s=SIZE/2, lw=1, clip_on=False)
        if self.ie_open:
            self.ie.scatter(X_d, Y_d, marker='.', color=fit.color,
                            alpha=.5, s=SIZE/2, lw=1, clip_on=False)
            self.ie.scatter(X_up, Y_up, marker='.',
                            color=fit.color, s=SIZE/2, lw=1, clip_on=False)

    def plot_high_level_equalarea(self, element):
        """
        Given a GUI element such as a sample or specimen tries to plot to
        high level mean plot
        """
        if self.ie_open:
            high_level = self.ie.show_box.GetValue()
        else:
            high_level = self.UPPER_LEVEL_SHOW
        fits = []
        if high_level not in self.pmag_results_data:
            print(("no level: " + str(high_level)))
            return
        if element not in self.pmag_results_data[high_level]:
            print(("no element: " + str(element)))
            return
        if self.mean_fit == 'All':
            fits = self.pmag_results_data[high_level][element]
        elif self.mean_fit != 'None' and self.mean_fit != None:
            fits = [fit for fit in self.pmag_results_data[high_level]
                    [element] if fit.name == self.mean_fit]
        else:
            fits = []
        fig = self.high_level_eqarea
        if fits:
            for fit in fits:
                pars = fit.get(self.COORDINATE_SYSTEM)
                if not pars:
                    if element in self.specimens:
                        fit.put(element, self.COORDINATE_SYSTEM, self.get_PCA_parameters(
                            element, fit, fit.tmin, fit.tmax, self.COORDINATE_SYSTEM, self.PCA_type_box.GetValue()))
                    pars = fit.get(self.COORDINATE_SYSTEM)
                    if not pars:
                        print(("No data for %s on element %s" %
                               (fit.name, element)))
                        return
                if "specimen_dec" in list(pars.keys()) and "specimen_inc" in list(pars.keys()):
                    dec = pars["specimen_dec"]
                    inc = pars["specimen_inc"]
                elif "dec" in list(pars.keys()) and "inc" in list(pars.keys()):
                    dec = pars["dec"]
                    inc = pars["inc"]
                else:
                    print(("-E- no dec and inc values for:\n" + str(fit)))
                XY = pmag.dimap(dec, inc)
                if inc > 0:
                    FC = fit.color
                    SIZE = 15*self.GUI_RESOLUTION
                else:
                    FC = 'white'
                    SIZE = 15*self.GUI_RESOLUTION
                marker_shape = 'o'
                if pars['calculation_type'] == "DE-BFP":
                    marker_shape = 's'
                    if 'bfv' in self.plane_display_box.GetValue():
                        marker_shape = '>'
                        SIZE = 25*self.GUI_RESOLUTION
                if fit == self.current_fit:
                    marker_shape = 'D'
                if fit in self.bad_fits:
                    marker_shape = (4, 1, 0)
                    SIZE = 25*self.GUI_RESOLUTION

                # draw a best-fit plane
                if pars['calculation_type'] == 'DE-BFP' and \
                   self.plane_display_box.GetValue() != "poles":

                    if "plane" in self.plane_display_box.GetValue() or "hemisphere" in self.plane_display_box.GetValue() or "wp" in self.plane_display_box.GetValue():

                        ymin, ymax = self.specimen_eqarea.get_ylim()
                        xmin, xmax = self.specimen_eqarea.get_xlim()

                        D_c, I_c = pmag.circ(
                            pars["specimen_dec"], pars["specimen_inc"], 90)
                        X_c_up, Y_c_up = [], []
                        X_c_d, Y_c_d = [], []
                        for k in range(len(D_c)):
                            XY = pmag.dimap(D_c[k], I_c[k])
                            if I_c[k] < 0:
                                X_c_up.append(XY[0])
                                Y_c_up.append(XY[1])
                            if I_c[k] > 0:
                                X_c_d.append(XY[0])
                                Y_c_d.append(XY[1])

                        if self.plane_display_box.GetValue() == "u. hemisphere" or \
                           self.plane_display_box.GetValue() == "whole plane" or \
                           self.plane_display_box.GetValue() == "wp + bfv":
                            fig.plot(X_c_d, Y_c_d, 'b')
                            if self.ie_open:
                                self.ie.plot(X_c_d, Y_c_d, 'b')
                        if self.plane_display_box.GetValue() == "l. hemisphere" or \
                           self.plane_display_box.GetValue() == "whole plane" or \
                           self.plane_display_box.GetValue() == "wp + bfv":
                            fig.plot(X_c_up, Y_c_up, 'c')
                            if self.ie_open:
                                self.ie.plot(X_c_up, Y_c_up, 'c')

                    if "bfv" in self.plane_display_box.GetValue():
                        if 'bfv_dec' not in list(pars.keys()) or 'bfv_inc' not in list(pars.keys()):
                            self.calculate_best_fit_vectors()
                            pars = fit.get(self.COORDINATE_SYSTEM)
                        try:
                            XY = pmag.dimap(pars['bfv_dec'], pars['bfv_inc'])
                        except KeyError:
                            print(("specimen %s fit %s is marked bad or there was an error calculating bfv pole will be displayed instead" % (
                                element, fit.name)))
#                            self.user_warning("There was an error calculating bfv for %s of %s, please raise an issue on github and/or contact a dev about this problem and restart the GUI"%(fit.name,element))
                        if inc > 0:
                            FC = fit.color
                        else:
                            FC = 'white'

                self.high_EA_xdata.append(XY[0])
                self.high_EA_ydata.append(XY[1])
                fig.scatter([XY[0]], [XY[1]], marker=marker_shape,
                            edgecolor=fit.color, facecolor=FC, s=SIZE, lw=1, clip_on=False)
                if self.ie_open:
                    self.ie.scatter([XY[0]], [XY[1]], marker=marker_shape,
                                    edgecolor=fit.color, facecolor=FC, s=SIZE, lw=1, clip_on=False)

    def plot_eqarea_pars(self, pars, fig):
        """
        Given a dictionary of parameters (pars) that is returned from
        pmag.domean plots those pars to the given fig
        """
        if pars == {}:
            pass
        elif 'calculation_type' in list(pars.keys()) and pars['calculation_type'] == 'DE-BFP':
            ymin, ymax = fig.get_ylim()
            xmin, xmax = fig.get_xlim()

            D_c, I_c = pmag.circ(pars["specimen_dec"],
                                 pars["specimen_inc"], 90)
            X_c_up, Y_c_up = [], []
            X_c_d, Y_c_d = [], []
            for k in range(len(D_c)):
                XY = pmag.dimap(D_c[k], I_c[k])
                if I_c[k] < 0:
                    X_c_up.append(XY[0])
                    Y_c_up.append(XY[1])
                if I_c[k] > 0:
                    X_c_d.append(XY[0])
                    Y_c_d.append(XY[1])
            fig.plot(X_c_d, Y_c_d, 'b', lw=0.5)
            fig.plot(X_c_up, Y_c_up, 'c', lw=0.5)
            if self.ie_open:
                self.ie.plot(X_c_d, Y_c_d, 'b', lw=0.5)
                self.ie.plot(X_c_up, Y_c_up, 'c', lw=0.5)

            fig.set_xlim(xmin, xmax)
            fig.set_ylim(ymin, ymax)
        # plot best-fit direction
        else:
            if "specimen_dec" in list(pars.keys()) and "specimen_inc" in list(pars.keys()):
                dec = pars["specimen_dec"]
                inc = pars["specimen_inc"]
            elif "dec" in list(pars.keys()) and "inc" in list(pars.keys()):
                dec = pars["dec"]
                inc = pars["inc"]
            else:
                print(("either dec or inc missing from values recived for high level plot, was given %s, aborting" % (
                    str(pars))))
                return
            XY = pmag.dimap(float(dec), float(inc))
            if inc > 0:
                if 'color' in list(pars.keys()):
                    FC = pars['color']
                    EC = pars['color']
                    SIZE = 15*self.GUI_RESOLUTION
                else:
                    FC = 'grey'
                    EC = 'grey'
                    SIZE = 15*self.GUI_RESOLUTION
            else:
                if 'color' in list(pars.keys()):
                    FC = 'white'
                    EC = pars['color']
                    SIZE = 15*self.GUI_RESOLUTION
                else:
                    FC = 'white'
                    EC = 'grey'
                    SIZE = 15*self.GUI_RESOLUTION
            fig.scatter([XY[0]], [XY[1]], marker='o', edgecolor=EC,
                        facecolor=FC, s=SIZE, lw=1, clip_on=False)
            if self.ie_open:
                self.ie.scatter([XY[0]], [XY[1]], marker='o', edgecolor=EC,
                                facecolor=FC, s=SIZE, lw=1, clip_on=False)

    def plot_eqarea_mean(self, meanpars, fig):
        """
        Given a dictionary of parameters from pmag.dofisher, pmag.dolnp, or
        pmag.dobingham (meanpars) plots parameters to fig
        """
        mpars_to_plot = []
        if meanpars == {}:
            return
        if meanpars['calculation_type'] == 'Fisher by polarity':
            for mode in list(meanpars.keys()):
                if type(meanpars[mode]) == dict and meanpars[mode] != {}:
                    mpars_to_plot.append(meanpars[mode])
        else:
            mpars_to_plot.append(meanpars)
        ymin, ymax = fig.get_ylim()
        xmin, xmax = fig.get_xlim()
        if 'color' in meanpars:
            color = meanpars['color']
        else:
            color = 'black'
        size, alpha = 30, 1.
        # put on the mean direction
        for mpars in mpars_to_plot:
            XYM = pmag.dimap(float(mpars["dec"]), float(mpars["inc"]))
            if float(mpars["inc"]) > 0:
                FC = color
                EC = 'black'
            else:
                FC = 'white'
                EC = color
            self.displayed_means.append(fig.scatter([XYM[0]], [
                                        XYM[1]], marker='o', edgecolor=EC, facecolor=FC, s=size, lw=1, clip_on=False, alpha=alpha))

            if "alpha95" in list(mpars.keys()):
                # get the alpha95
                Xcirc, Ycirc = [], []
                Da95, Ia95 = pmag.circ(float(mpars["dec"]), float(
                    mpars["inc"]), float(mpars["alpha95"]))
                for k in range(len(Da95)):
                    XY = pmag.dimap(Da95[k], Ia95[k])
                    Xcirc.append(XY[0])
                    Ycirc.append(XY[1])
                self.displayed_means.append(
                    fig.plot(Xcirc, Ycirc, color, alpha=alpha))

            if self.ie_open:
                self.displayed_means.append(self.ie.scatter([XYM[0]], [
                                            XYM[1]], marker='o', edgecolor=EC, facecolor=FC, s=size, lw=1, clip_on=False, alpha=alpha))
                if "alpha95" in list(mpars.keys()):
                    self.displayed_means.append(
                        self.ie.plot(Xcirc, Ycirc, color, alpha=alpha))
                self.ie.eqarea.set_xlim(xmin, xmax)
                self.ie.eqarea.set_ylim(ymin, ymax)

        fig.set_xlim(xmin, xmax)
        fig.set_ylim(ymin, ymax)

#==========================================================================================#
#========================Backend Data Processing Functions=================================#
#==========================================================================================#

    #---------------------------------------------#
    # Data Calculation Function
    #---------------------------------------------#

    def initialize_CART_rot(self, s):
        """
        Sets current specimen to s and calculates the data necessary to plot
        the specimen plots (zijderveld, specimen eqarea, M/M0)

        Parameters
        ----------
        s: specimen to set as the GUI's current specimen
        """
        self.s = s  # only place in code where self.s is to be set directly
        if self.orthogonal_box.GetValue() == "X=East":
            self.ORTHO_PLOT_TYPE = 'E-W'
        elif self.orthogonal_box.GetValue() == "X=North":
            self.ORTHO_PLOT_TYPE = 'N-S'
        elif self.orthogonal_box.GetValue() == "X=best fit line dec":
            self.ORTHO_PLOT_TYPE = 'PCA_dec'
        else:
            self.ORTHO_PLOT_TYPE = 'ZIJ'
        if self.COORDINATE_SYSTEM == 'geographic':
            # self.CART_rot=self.Data[self.s]['zij_rotated_geo']
            self.zij = array(self.Data[self.s]['zdata_geo'])
            self.zijblock = self.Data[self.s]['zijdblock_geo']
        elif self.COORDINATE_SYSTEM == 'tilt-corrected':
            # self.CART_rot=self.Data[self.s]['zij_rotated_tilt']
            self.zij = array(self.Data[self.s]['zdata_tilt'])
            self.zijblock = self.Data[self.s]['zijdblock_tilt']
        else:
            # self.CART_rot=self.Data[self.s]['zij_rotated']
            self.zij = array(self.Data[self.s]['zdata'])
            self.zijblock = self.Data[self.s]['zijdblock']

        if self.COORDINATE_SYSTEM == 'geographic':
            if self.ORTHO_PLOT_TYPE == 'N-S':
                self.CART_rot = Rotate_zijderveld(
                    self.Data[self.s]['zdata_geo'], 0.)
            elif self.ORTHO_PLOT_TYPE == 'E-W':
                self.CART_rot = Rotate_zijderveld(
                    self.Data[self.s]['zdata_geo'], 90.)
            elif self.ORTHO_PLOT_TYPE == 'PCA_dec':
                if 'specimen_dec' in list(self.current_fit.pars.keys()) and type(self.current_fit.pars['specimen_dec']) != str:
                    self.CART_rot = Rotate_zijderveld(
                        self.Data[self.s]['zdata_geo'], self.current_fit.pars['specimen_dec'])
                else:
                    self.CART_rot = Rotate_zijderveld(self.Data[self.s]['zdata_geo'], pmag.cart2dir(
                        self.Data[self.s]['zdata_geo'][0])[0])
            else:
                self.CART_rot = Rotate_zijderveld(self.Data[self.s]['zdata_geo'], pmag.cart2dir(
                    self.Data[self.s]['zdata_geo'][0])[0])

        elif self.COORDINATE_SYSTEM == 'tilt-corrected':
            if self.ORTHO_PLOT_TYPE == 'N-S':
                self.CART_rot = Rotate_zijderveld(
                    self.Data[self.s]['zdata_tilt'], 0.)
            elif self.ORTHO_PLOT_TYPE == 'E-W':
                self.CART_rot = Rotate_zijderveld(
                    self.Data[self.s]['zdata_tilt'], 90)
            elif self.ORTHO_PLOT_TYPE == 'PCA_dec':
                if 'specimen_dec' in list(self.current_fit.pars.keys()) and type(self.current_fit.pars['specimen_dec']) != str:
                    self.CART_rot = Rotate_zijderveld(
                        self.Data[self.s]['zdata_tilt'], self.current_fit.pars['specimen_dec'])
                else:
                    self.CART_rot = Rotate_zijderveld(self.Data[self.s]['zdata_tilt'], pmag.cart2dir(
                        self.Data[self.s]['zdata_tilt'][0])[0])
            else:
                self.CART_rot = Rotate_zijderveld(self.Data[self.s]['zdata_tilt'], pmag.cart2dir(
                    self.Data[self.s]['zdata_tilt'][0])[0])
        else:
            if self.ORTHO_PLOT_TYPE == 'N-S':
                self.CART_rot = Rotate_zijderveld(
                    self.Data[self.s]['zdata'], 0.)
            elif self.ORTHO_PLOT_TYPE == 'E-W':
                self.CART_rot = Rotate_zijderveld(
                    self.Data[self.s]['zdata'], 90)
            elif self.ORTHO_PLOT_TYPE == 'PCA_dec':
                if 'specimen_dec' in list(self.current_fit.pars.keys()) and type(self.current_fit.pars['specimen_dec']) != str:
                    self.CART_rot = Rotate_zijderveld(
                        self.Data[self.s]['zdata'], self.current_fit.pars['specimen_dec'])
                else:  # Zijderveld
                    self.CART_rot = Rotate_zijderveld(
                        self.Data[self.s]['zdata'], pmag.cart2dir(self.Data[self.s]['zdata'][0])[0])

            else:  # Zijderveld
                self.CART_rot = Rotate_zijderveld(
                    self.Data[self.s]['zdata'], pmag.cart2dir(self.Data[self.s]['zdata'][0])[0])

        self.zij_norm = array([row/sqrt(sum(row**2)) for row in self.zij])

        # remove bad data from plotting:
        self.CART_rot_good = []
        self.CART_rot_bad = []
        for i in range(len(self.CART_rot)):
            if self.Data[self.s]['measurement_flag'][i] == 'g':
                self.CART_rot_good.append(list(self.CART_rot[i]))
            else:
                self.CART_rot_bad.append(list(self.CART_rot[i]))

        self.CART_rot = array(self.CART_rot)
        self.CART_rot_good = array(self.CART_rot_good)
        self.CART_rot_bad = array(self.CART_rot_bad)

    def add_fit(self, specimen, name, fmin, fmax, PCA_type="DE-BFL", color=None, suppress_warnings=False, saved=True):
        """
        Goes through the data checks required to add an interpretation to
        the param specimen with the name param name, the bounds param fmin
        and param fmax, and calculation type param PCA_type.

        Parameters
        ----------
        specimen : specimen with measurement data to add the
        interpretation to
        name : name of the new interpretation
        fmin : lower bound of new interpretation
        fmax : upper bound of new interpretation
        PCA_type : type of regression or mean for new interpretaion
        (default: DE-BFL or line)
        color : color to plot the new interpretation in

        Returns
        -------
        new Fit object or None if fit could not be added
        """
        if specimen not in list(self.Data.keys()) and not suppress_warnings:
            self.user_warning(
                "there is no measurement data for %s and therefore no interpretation can be created for this specimen" % (specimen))
            return
        if fmax != None and fmax not in self.Data[specimen]['zijdblock_steps'] or fmin != None and fmin not in self.Data[specimen]['zijdblock_steps']:
            return
        if not (specimen in list(self.pmag_results_data['specimens'].keys())):
            self.pmag_results_data['specimens'][specimen] = []
        next_fit = str(len(self.pmag_results_data['specimens'][specimen]) + 1)
        if name == None or name in [x.name for x in self.pmag_results_data['specimens'][specimen]] or name == "" or name.replace(" ", "") == "":
            name = ('Fit ' + next_fit)
            if name in [x.name for x in self.pmag_results_data['specimens'][specimen]]:
                print('bad name')
                return
        if color == None:
            color = self.colors[(int(next_fit)-1) % len(self.colors)]
        new_fit = Fit(name, fmax, fmin, color, self, PCA_type, saved)
        if fmin != None and fmax != None:
            new_fit.put(specimen, self.COORDINATE_SYSTEM, self.get_PCA_parameters(
                specimen, new_fit, fmin, fmax, self.COORDINATE_SYSTEM, PCA_type))
            if ('specimen_dec' not in list(new_fit.get(self.COORDINATE_SYSTEM).keys())
                    or 'specimen_inc' not in list(new_fit.get(self.COORDINATE_SYSTEM).keys()))\
                    and not suppress_warnings:
                TEXT = "Could not calculate dec or inc for specimen %s component %s with bounds %s and %s in coordinate_system %s, component not added" % (
                    specimen, name, fmin, fmax, self.COORDINATE_SYSTEM)
                self.user_warning(TEXT)
                print(TEXT)
                return
        self.pmag_results_data['specimens'][specimen].append(new_fit)
        samp = self.Data_hierarchy['sample_of_specimen'][specimen]
        if samp in list(self.Data_info['er_samples'].keys()):
            if 'sample_orientation_flag' not in self.Data_info['er_samples'][samp]:
                self.Data_info['er_samples'][samp]['sample_orientation_flag'] = 'g'
            samp_flag = self.Data_info['er_samples'][samp]['sample_orientation_flag']
            if samp_flag == 'b':
                self.mark_fit_bad(new_fit)
        self.close_warning = True
        return new_fit

    def delete_fit(self, fit, specimen=None):
        """
        removes fit from GUI results data

        Parameters
        ----------
        fit : fit to remove
        specimen : specimen of fit to remove, if not provided and
        set to None then the function will find the specimen itself
        """
        if specimen == None:
            for spec in self.pmag_results_data['specimens']:
                if fit in self.pmag_results_data['specimens'][spec]:
                    specimen = spec
                    break
        if specimen not in self.pmag_results_data['specimens']:
            return
        if fit in self.pmag_results_data['specimens'][specimen]:
            self.pmag_results_data['specimens'][specimen].remove(fit)
        if fit == self.current_fit:
            if self.pmag_results_data['specimens'][specimen]:
                self.pmag_results_data['specimens'][specimen][-1].select()
            else:
                self.current_fit = None
        self.close_warning = True
        self.calculate_high_levels_data()
        if self.ie_open:
            self.ie.update_editor()
        self.update_selection()

    def calculate_vgp_data(self):
        """
        Calculates VGPS for all samples, sites, and locations

        Returns
        -------
        VGP_Data : dictionary of structure {sample: {comp: data},
            site: {comp: data}, location: {comp: data}}
        """
        # get criteria if it exists else use default
        crit_data = self.read_criteria_file()
        if crit_data == None:
            crit_data = pmag.default_criteria(0)
        accept = {}
        for critrec in crit_data:
            if type(critrec) != dict:
                continue
            for key in list(critrec.keys()):
                # need to migrate specimen_dang to specimen_int_dang
                if 'IE-SPEC' in list(critrec.keys()) and 'specimen_dang' in list(critrec.keys()) and 'specimen_int_dang' not in list(critrec.keys()):
                    critrec['specimen_int_dang'] = critrec['specimen_dang']
                    del critrec['specimen_dang']
                # need to get rid of ron shaars sample_int_sigma_uT
                if 'sample_int_sigma_uT' in list(critrec.keys()):
                    critrec['sample_int_sigma'] = '%10.3e' % (
                        eval(critrec['sample_int_sigma_uT'])*1e-6)
                if key not in list(accept.keys()) and critrec[key] != '':
                    accept[key] = critrec[key]

        Ns = []
        # retrieve specimen data to calculate VGPS with
        for s in list(self.pmag_results_data['specimens'].keys()):
            for fit in self.pmag_results_data['specimens'][s]:
                if fit in self.bad_fits:
                    continue
                pars = fit.get(self.COORDINATE_SYSTEM)
                # check for interpretation data for fit
                if not pars:
                    pars = self.get_PCA_parameters(
                        s, fit, fit.tmin, fit.tmax, self.COORDINATE_SYSTEM, fit.PCA_type)
                    if not pars or 'specimen_dec' not in list(pars.keys()) or 'specimen_inc' not in list(pars.keys()):
                        print(("Could not calculate interpretation for specimen %s and fit %s while calculating VGP data, skipping this component" % (
                            s, fit.name)))
                        continue
                    pars['er_specimen_name'] = s
                    pars['specimen_comp_name'] = fit.name
                Ns.append(pars)

        SpecDirs = []
        if crit_data != None:  # use selection criteria
            for rec in Ns:  # look through everything with specimen_n for "good" data
                kill = pmag.grade(rec, accept, 'specimen_dir', data_model=2.5)
                if len(kill) == 0:  # nothing killed it
                    SpecDirs.append(rec)
        else:  # no criteria
            SpecDirs = Ns[:]  # take them all

        for i in range(len(SpecDirs)):
            if SpecDirs[i] == {}:
                continue
            specimen = SpecDirs[i]['er_specimen_name']
            SpecDirs[i]['er_sample_name'] = self.Data_hierarchy['sample_of_specimen'][specimen]
            SpecDirs[i]['er_site_name'] = self.Data_hierarchy['site_of_specimen'][specimen]
            SpecDirs[i]['er_location_name'] = self.Data_hierarchy['location_of_specimen'][specimen]

        # init VGP data
        VGP_Data = {'samples': [], 'sites': [], 'locations': []}

        # obtain lat lon data
        SiteNFO = list(self.Data_info['er_sites'].values())
        for val in SiteNFO:
            site = val['er_site_name']
            not_found = []
            # check that lat/lon columns are present and non-null
            if 'site_lat' not in val:
                not_found.append('latitude')
            elif not val['site_lat'] and val['site_lat'] is not 0:
                not_found.append('latitude')
            if 'site_lon' not in val:
                not_found.append('longitude')
            elif not val['site_lon'] and val['site_lon'] is not 0:
                not_found.append('longitude')
            if not_found == []:
                continue
            TEXT = "%s not found for site %s. Select 'yes' to enter the values now or 'no' to skip this site and all samples contained in it." % (
                str(not_found), val['er_site_name'])
            dlg = wx.MessageDialog(
                self, caption="Missing Data", message=TEXT, style=wx.YES_NO | wx.ICON_QUESTION)
            result = self.show_dlg(dlg)
            dlg.Destroy()
            if result == wx.ID_YES:
                ui_dialog = demag_dialogs.user_input(self, ['Latitude', 'Longitude'], parse_funcs=[
                                                     float, float], heading="Missing Latitude or Longitude data for site: %s" % val['er_site_name'])
                self.show_dlg(ui_dialog)
                ui_data = ui_dialog.get_values()
                if ui_data[0]:
                    self.Data_info['er_sites'][site]['site_lat'] = ui_data[1]['Latitude']
                    self.Data_info['er_sites'][site]['site_lon'] = ui_data[1]['Longitude']
                    val['site_lat'] = ui_data[1]['Latitude']
                    val['site_lon'] = ui_data[1]['Longitude']

        # calculate sample vgps
        for samp in self.samples:
            SampDir = pmag.get_dictitem(SpecDirs, 'er_sample_name', samp, 'T')
            if len(SampDir) <= 0:
                continue
            for comp in self.all_fits_list:
                CompDir = pmag.get_dictitem(
                    SampDir, 'specimen_comp_name', comp, 'T')
                if len(CompDir) <= 0:
                    continue  # no data for comp
                samp_mean = pmag.lnpbykey(CompDir, 'sample', 'specimen')
                site = pmag.get_dictitem(
                    SiteNFO, 'er_site_name', CompDir[0]['er_site_name'], 'T')
                dec = float(samp_mean['sample_dec'])
                inc = float(samp_mean['sample_inc'])
                if 'sample_alpha95' in samp_mean and samp_mean['sample_alpha95'] != "":
                    a95 = float(samp_mean['sample_alpha95'])
                else:
                    a95 = 180.
                try:
                    lat = float(site[0]['site_lat'])
                    lon = float(site[0]['site_lon'])
                except (KeyError, IndexError, ValueError, TypeError) as e:
                    continue
                plong, plat, dp, dm = pmag.dia_vgp(dec, inc, a95, lat, lon)
                PmagResRec = {}
                PmagResRec['name'] = samp
                PmagResRec['comp_name'] = comp
                PmagResRec['n'] = len(CompDir)
                PmagResRec['color'] = [e.color for sl in list(self.pmag_results_data['specimens'].values(
                )) for e in sl if e not in self.bad_fits and e.name == comp][0]
                PmagResRec['vgp_lon'] = plong
                PmagResRec['vgp_lat'] = plat
                PmagResRec['lon'] = lon
                PmagResRec['lat'] = lat
                PmagResRec['vgp_dp'] = dp
                PmagResRec['vgp_dm'] = dm
                VGP_Data['samples'].append(PmagResRec)

        for site in self.sites:
            SiteDir = pmag.get_dictitem(SpecDirs, 'er_site_name', site, 'T')
            erSite = pmag.get_dictitem(SiteNFO, 'er_site_name', site, 'T')
            for comp in self.all_fits_list:
                siteD = pmag.get_dictitem(
                    SiteDir, 'specimen_comp_name', comp, 'T')
                if len(siteD) <= 0:
                    print(("no data for comp %s and site %s" % (comp, site)))
                    continue
                SiteData = pmag.lnpbykey(siteD, 'site', 'specimen')
                dec = float(SiteData['site_dec'])
                inc = float(SiteData['site_inc'])
                if 'site_alpha95' in SiteData and SiteData['site_alpha95'] != "":
                    a95 = float(SiteData['site_alpha95'])
                else:
                    a95 = 180.
                try:
                    lat = float(erSite[0]['site_lat'])
                    lon = float(erSite[0]['site_lon'])
                except (KeyError, IndexError, TypeError) as e:
                    continue
                plong, plat, dp, dm = pmag.dia_vgp(dec, inc, a95, lat, lon)
                SiteData['name'] = site
                SiteData['comp_name'] = comp
                SiteData['n'] = len(siteD)
                SiteData['vgp_lon'] = plong
                SiteData['vgp_lat'] = plat
                SiteData['lon'] = lon
                SiteData['lat'] = lat
                SiteData['vgp_dp'] = dp
                SiteData['vgp_dm'] = dm
                SiteData['color'] = [e.color for sl in list(self.pmag_results_data['specimens'].values(
                )) for e in sl if e not in self.bad_fits and e.name == comp][0]
                VGP_Data['sites'].append(SiteData)

        for loc in self.locations:
            LocDir = pmag.get_dictitem(SpecDirs, 'er_location_name', loc, 'T')
            for comp in self.all_fits_list:
                LocCompData = pmag.get_dictitem(
                    LocDir, 'specimen_comp_name', comp, 'T')
                if len(LocCompData) < 3:
                    print(("insufficient data for comp %s" % comp))
                    continue
                precs = []
                for rec in LocCompData:
                    prec = {'dec': rec['specimen_dec'], 'inc': rec['specimen_inc'],
                            'name': rec['er_site_name'], 'loc': rec['er_location_name']}
                    prec = {k: v if v != None else '' for k,
                            v in list(prec.items())}
                    precs.append(prec)
                # you need at least 3 records to get anything back from pmag.fisher_by_pol
                polpars = pmag.fisher_by_pol(precs)
                # hunt through all the modes (normal=A, reverse=B, all=ALL)
                for mode in list(polpars.keys()):
                    PolRes = {}
                    PolRes['name'] = polpars[mode]['locs']
                    PolRes["comp_name"] = comp+':'+mode
                    PolRes["dec"] = '%7.1f' % (polpars[mode]['dec'])
                    PolRes["inc"] = '%7.1f' % (polpars[mode]['inc'])
                    PolRes["n"] = '%i' % (polpars[mode]['n'])
                    PolRes["r"] = '%5.4f' % (polpars[mode]['r'])
                    PolRes["k"] = '%6.0f' % (polpars[mode]['k'])
                    PolRes['a95'] = '%7.1f' % (polpars[mode]['alpha95'])
                    dec, inc, a95 = PolRes["dec"], PolRes["inc"], PolRes["a95"]
                    lat, lon, loc_data = "", "", self.Data_info['er_locations']
                    if loc in loc_data and 'location_begin_lat' in loc_data[loc]:
                        lat = loc_data[loc]['location_begin_lat']
                    elif loc in loc_data and 'location_end_lat' in loc_data[loc]:
                        lat = loc_data[loc]['location_end_lat']
                    if loc in loc_data and 'location_begin_lon' in loc_data[loc]:
                        lon = loc_data[loc]['location_begin_lon']
                    elif loc in loc_data and 'location_end_lon' in loc_data[loc]:
                        lon = loc_data[loc]['location_end_lon']
                    if lat == "" or lon == "" or lat == None or lon == None:
                        ui_dialog = demag_dialogs.user_input(self, ['Latitude', 'Longitude'], parse_funcs=[
                                                             float, float], heading="Missing Latitude or Longitude data for location: %s" % loc)
                        self.show_dlg(ui_dialog)
                        ui_data = ui_dialog.get_values()
                        if ui_data[0]:
                            lat = ui_data[1]['Latitude']
                            lon = ui_data[1]['Longitude']
                            if loc not in loc_data:
                                loc_data[loc] = {}
                            if len(loc_data) > 0:
                                loc_data[loc]['location_begin_lat'] = lat
                                loc_data[loc]['location_begin_lon'] = lon
                        else:
                            continue
                    try:
                        plong, plat, dp, dm = pmag.dia_vgp(
                            *list(map(float, [dec, inc, a95, lat, lon])))
                    except TypeError:
                        print(("Not valid parameters for vgp calculation on location: %s" %
                               loc, dec, inc, a95, lat, lon))
                        continue
                    PolRes['vgp_lon'] = plong
                    PolRes['vgp_lat'] = plat
                    PolRes['lon'] = lon
                    PolRes['lat'] = lat
                    PolRes['vgp_dp'] = dp
                    PolRes['vgp_dm'] = dm
                    PolRes['color'] = [e.color for sl in list(self.pmag_results_data['specimens'].values(
                    )) for e in sl if e not in self.bad_fits and e.name == comp][0]
                    VGP_Data['locations'].append(PolRes)

        return VGP_Data

    def convert_ages_to_calendar_year(self, er_ages_rec):
        """
        convert all age units to calendar year

        Parameters
        ----------
        er_ages_rec : Dict type object containing preferbly at least keys
            'age', 'age_unit', and either 'age_range_high', 'age_range_low'
            or 'age_sigma'

        Returns
        -------
        er_ages_rec : Same dict object input but altered to have new records
            'age_cal_year_range_low' and 'age_cal_year_range_high'
        """
        if "age" not in list(er_ages_rec.keys()):
            return(er_ages_rec)
        if "age_unit" not in list(er_ages_rec.keys()):
            return(er_ages_rec)
        if er_ages_rec["age_unit"] == "":
            return(er_ages_rec)

        if er_ages_rec["age"] == "":
            if "age_range_high" in list(er_ages_rec.keys()) and "age_range_low" in list(er_ages_rec.keys()):
                if er_ages_rec["age_range_high"] != "" and er_ages_rec["age_range_low"] != "":
                    er_ages_rec["age"] = scipy.mean(
                        [float(er_ages_rec["age_range_high"]), float(er_ages_rec["age_range_low"])])
        if er_ages_rec["age"] == "":
            return(er_ages_rec)

        age_unit = er_ages_rec["age_unit"]

        # Fix 'age':
        mutliplier = 1
        if age_unit == "Ga":
            mutliplier = -1e9
        if age_unit == "Ma":
            mutliplier = -1e6
        if age_unit == "Ka":
            mutliplier = -1e3
        if age_unit == "Years AD (+/-)" or age_unit == "Years Cal AD (+/-)":
            mutliplier = 1
        if age_unit == "Years BP" or age_unit == "Years Cal BP":
            mutliplier = 1
        age = float(er_ages_rec["age"])*mutliplier
        if age_unit == "Years BP" or age_unit == "Years Cal BP":
            age = 1950-age
        er_ages_rec['age_cal_year'] = age

        # Fix 'age_range_low':
        age_range_low = age
        age_range_high = age
        age_sigma = 0

        if "age_sigma" in list(er_ages_rec.keys()) and er_ages_rec["age_sigma"] != "":
            age_sigma = float(er_ages_rec["age_sigma"])*mutliplier
            if age_unit == "Years BP" or age_unit == "Years Cal BP":
                age_sigma = 1950-age_sigma
            age_range_low = age-age_sigma
            age_range_high = age+age_sigma

        if "age_range_high" in list(er_ages_rec.keys()) and "age_range_low" in list(er_ages_rec.keys()):
            if er_ages_rec["age_range_high"] != "" and er_ages_rec["age_range_low"] != "":
                age_range_high = float(
                    er_ages_rec["age_range_high"])*mutliplier
                if age_unit == "Years BP" or age_unit == "Years Cal BP":
                    age_range_high = 1950-age_range_high
                age_range_low = float(er_ages_rec["age_range_low"])*mutliplier
                if age_unit == "Years BP" or age_unit == "Years Cal BP":
                    age_range_low = 1950-age_range_low
        er_ages_rec['age_cal_year_range_low'] = age_range_low
        er_ages_rec['age_cal_year_range_high'] = age_range_high

        return(er_ages_rec)

    def generate_warning_text(self):
        """
        generates warnings for the current specimen then adds them to the
        current warning text for the GUI which will be rendered on a call to
        update_warning_box.
        """
        self.warning_text = ""
        if self.s in list(self.pmag_results_data['specimens'].keys()):
            for fit in self.pmag_results_data['specimens'][self.s]:
                beg_pca, end_pca = self.get_indices(
                    fit, fit.tmin, fit.tmax, self.s)
                if beg_pca == None or end_pca == None:
                    self.warning_text += "%s to %s are invalid bounds, to fit %s.\n" % (
                        fit.tmin, fit.tmax, fit.name)
                elif end_pca - beg_pca < 2:
                    self.warning_text += "there are not enough points between %s to %s, on fit %s.\n" % (
                        fit.tmin, fit.tmax, fit.name)
                else:
                    check_duplicates = []
                    warning_issued = []  # keep track of warnings issued to avoid redundant warnings

                    # if within range, attempt to go one additional step beyond
                    # tmax so that duplicates at the upper bound are caught
                    if (end_pca + 2) < len(self.Data[self.s]['zijdblock_steps']):
                        check_endpoint = end_pca + 2
                    else:
                        check_endpoint = end_pca + 1

                    for s, f in zip(self.Data[self.s]['zijdblock_steps'][beg_pca:check_endpoint],
                                    self.Data[self.s]['measurement_flag'][beg_pca:check_endpoint]):
                        if f == 'g' and [s, 'g'] in check_duplicates:
                            if s == fit.tmin and s not in warning_issued:
                                self.warning_text += ("There are multiple good %s " +
                                                      "steps at the upper bound of Fit %s. The first " +
                                                      "measurement will be used as the lower bound.\n") % (
                                                          s, fit.name)
                                # warning_issued_low.append(s)
                                warning_issued.append(s)
                            elif s == fit.tmax and s not in warning_issued:
                                self.warning_text += ("There are multiple good %s " +
                                                      "steps at the upper bound of Fit %s. The first " +
                                                      "measurement will be used as the upper bound.\n") % (
                                                          s, fit.name)
                                # warning_issued_high.append(s)
                                warning_issued.append(s)
                            elif s not in warning_issued:
                                self.warning_text += ("Within Fit %s, there are " +
                                                      "multiple good measurements at the %s step. All " +
                                                      "good measurements are included in the fit.\n") % (
                                                          fit.name, s)
                                warning_issued.append(s)
                            else:
                                pass
                        else:
                            check_duplicates.append([s, f])
        if self.s in list(self.Data.keys()):
            if not self.Data[self.s]['zijdblock_geo']:
                self.warning_text += "There is no geographic data for this specimen.\n"
            if not self.Data[self.s]['zijdblock_tilt']:
                self.warning_text += "There is no tilt-corrected data for this specimen.\n"

    def read_criteria_file(self, criteria_file_name=None):
        """
        reads 2.5 or 3.0 formatted PmagPy criteria file and returns a set of
        nested dictionary 2.5 formated criteria data that can be passed into
        pmag.grade to filter data.

        Parameters
        ----------
        criteria_file : name of criteria file to read in

        Returns
        -------
        nested dictionary 2.5 formated criteria data
        """
#        import pdb; pdb.set_trace()
        acceptance_criteria = pmag.initialize_acceptance_criteria()
        if self.data_model == 3:
            if criteria_file_name == None:
                criteria_file_name = "criteria.txt"
            contribution = cb.Contribution(self.WD, read_tables=[
                                           'criteria'], custom_filenames={'criteria': criteria_file_name})
            if 'criteria' in contribution.tables:
                crit_container = contribution.tables['criteria']
                crit_data = crit_container.df
                crit_data = crit_data.to_dict('records')
                for crit in crit_data:
                    m2_name = map_magic.convert_direction_criteria(
                        'magic2', crit['table_column'])
                    if m2_name != "":
                        try:
                            if crit['criterion_value'] == 'True':
                                acceptance_criteria[m2_name]['value'] = 1
                            else:
                                acceptance_criteria[m2_name]['value'] = 0
                            acceptance_criteria[m2_name]['value'] = float(
                                crit['criterion_value'])
                        except ValueError:
                            self.user_warning("%s is not a valid comparitor for %s, skipping this criteria" % (
                                str(crit['criterion_value']), m2_name))
                            continue
                        acceptance_criteria[m2_name]['pmag_criteria_code'] = crit['criterion']
            return acceptance_criteria
        else:
            if criteria_file_name == None:
                criteria_file_name = "pmag_criteria.txt"
            try:
                acceptance_criteria = pmag.read_criteria_from_file(
                    os.path.join(self.WD, criteria_file_name), acceptance_criteria)
            except (IOError, OSError) as e:
                self.user_warning("File %s not found in directory %s aborting opperation" % (
                    criteria_file_name, self.WD))
            return acceptance_criteria

    def get_PCA_parameters(self, specimen, fit, tmin, tmax, coordinate_system, calculation_type):
        """
        Uses pmag.domean to preform a line, line-with-origin, line-anchored,
        or plane least squared regression or a fisher mean on the
        measurement data of specimen in coordinate system between bounds
        tmin to tmax

        Parameters
        ----------
        specimen : specimen with measurement data in self.Data
        fit : fit for which the regression or mean is being applied
            (used for calculating measurement index of tmin and tmax)
        tmin : lower bound of measurement data
        tmax : upper bound of measurement data
        coordinate_system : which coordinate system the measurement data
            should be in
        calculation_type : type of regression or mean to preform
            (options - DE-BFL:line,DE-BFL-A:line-anchored,DE-BFL-O:line-with-
            origin,DE-FM:fisher,DE-BFP:plane)

        Returns
        -------
        mpars : a 2.5 data model dictionary type specimen record of the dec,
            inc, etc of the regression or mean
        """
        if tmin == '' or tmax == '':
            return
        beg_pca, end_pca = self.get_indices(fit, tmin, tmax, specimen)

        if coordinate_system == 'geographic' or coordinate_system == 'DA-DIR-GEO':
            block = self.Data[specimen]['zijdblock_geo']
        elif coordinate_system == 'tilt-corrected' or coordinate_system == 'DA-DIR-TILT':
            block = self.Data[specimen]['zijdblock_tilt']
        else:
            block = self.Data[specimen]['zijdblock']
        if block == []:
            print(("-E- no measurement data for specimen %s in coordinate system %s" %
                   (specimen, coordinate_system)))
            mpars = {}
        elif end_pca > beg_pca and end_pca - beg_pca > 1:

            try:
                # preformes regression
                mpars = pmag.domean(block, beg_pca, end_pca, calculation_type)
            except:
                print((block, beg_pca, end_pca, calculation_type,
                       specimen, fit.name, tmin, tmax, coordinate_system))
                return

            if 'specimen_direction_type' in mpars and mpars['specimen_direction_type'] == 'Error':
                print(("-E- no measurement data for specimen %s in coordinate system %s" %
                       (specimen, coordinate_system)))
                return {}
        else:
            mpars = {}
        for k in list(mpars.keys()):
            try:
                if math.isnan(float(mpars[k])):
                    mpars[k] = 0
            except:
                pass
        if "DE-BFL" in calculation_type and 'specimen_dang' not in list(mpars.keys()):
            mpars['specimen_dang'] = 0

        if 'best fit vector' in self.plane_display_box.GetValue():
            self.calculate_best_fit_vectors()

        return(mpars)

    def autointerpret(self, event, step_size=None, calculation_type="DE-BFL"):
        """
        Clears current interpretations and adds interpretations to every
        specimen of type = calculation_type by attempting fits of size =
        step size and type = calculation_type and testing the mad or a95
        then finding peaks in these to note areas of maximum error then fits
        between these peaks excluding them.

        Parameters
        ----------
        step_size : int that is the size of fits to make while stepping
            through data if None then step size = len(meas data for
            specimen)/10 rounded up if that value is greater than 3 else it
            is 3 (default: None)
        calculation_type : type of fit to make (default: DE-BFL or line)
        """
        if not self.user_warning("This feature is in ALPHA and still in development and testing. It is subject to bugs and will often create a LOT of new interpretations. This feature should only be used to get a general idea of the trend of the data before actually mannuely interpreting the data and the output of this function should certainly not be trusted as 100% accurate and useable for publication. Would you like to continue?"):
            return
        if not self.clear_interpretations():
            return

        print("Autointerpretation Start")

        self.set_test_mode(True)
        for specimen in self.specimens:
            self.autointerpret_specimen(specimen, step_size, calculation_type)
        self.set_test_mode(False)

        if self.pmag_results_data['specimens'][self.s] != []:
            self.current_fit = self.pmag_results_data['specimens'][self.s][-1]
        else:
            self.current_fit = None
        print("Autointerpretation Complete")
        self.update_selection()
        if self.ie_open:
            self.ie.update_editor()

    def autointerpret_specimen(self, specimen, step_size, calculation_type):
        """In Dev"""
        if self.COORDINATE_SYSTEM == 'geographic':
            block = self.Data[specimen]['zijdblock_geo']
        elif self.COORDINATE_SYSTEM == 'tilt-corrected':
            block = self.Data[specimen]['zijdblock_tilt']
        else:
            block = self.Data[specimen]['zijdblock']
        if step_size == None:
            step_size = int(len(block)/10 + .5)
            if step_size < 3:
                step_size = 3
        temps = []
        mads = []
        for i in range(len(block)-step_size):
            if block[i][5] == 'b':
                return
            try:
                mpars = pmag.domean(block, i, i+step_size, calculation_type)
            except (IndexError, TypeError) as e:
                return
            if 'specimen_mad' in list(mpars.keys()):
                temps.append(block[i][0])
                mads.append(mpars['specimen_mad'])
        if mads == []:
            return

        peaks = find_peaks_cwt(array(mads), arange(5, 10))
        len_temps = len(self.Data[specimen]['zijdblock_steps'])
        peaks = [0] + peaks + [len(temps)]

        prev_peak = peaks[0]
        for peak in peaks[1:]:
            if peak - prev_peak < 3:
                prev_peak = peak
                continue
            tmin = self.Data[specimen]['zijdblock_steps'][prev_peak]
            tmax = self.Data[specimen]['zijdblock_steps'][peak]
            self.add_fit(specimen, None, tmin, tmax, calculation_type)
            prev_peak = peak+1

    def get_high_level_mean_pars(self, high_level_type, high_level_name, calculation_type, elements_type, mean_fit, dirtype):
        """
        Gets the Parameters of a mean of lower level data such as a Site
        level Fisher mean of Specimen interpretations

        Parameters
        ----------
        high_level_type : 'samples','sites','locations','study'
        high_level_name : sample, site, location, or study whose
            data to which to apply the mean
        calculation_type : 'Bingham','Fisher','Fisher by polarity'
        elements_type : what to average: 'specimens', 'samples',
            'sites' (Ron. ToDo allow VGP and maybe locations?)
        mean_fit : name of interpretation to average if All uses all
            figure out what level to average,and what elements to average
            (specimen, samples, sites, vgp)
        """

        elements_list = self.Data_hierarchy[high_level_type][high_level_name][elements_type]
        pars_for_mean = {}
        pars_for_mean["All"] = []

        for element in elements_list:
            if elements_type == 'specimens' and element in self.pmag_results_data['specimens']:
                for fit in self.pmag_results_data['specimens'][element]:
                    if fit in self.bad_fits:
                        continue
                    if fit.name not in list(pars_for_mean.keys()):
                        pars_for_mean[fit.name] = []
                    try:
                        # is this fit to be included in mean
                        if mean_fit == 'All' or mean_fit == fit.name:
                            pars = fit.get(dirtype)
                            if pars == {} or pars == None:
                                pars = self.get_PCA_parameters(
                                    element, fit, fit.tmin, fit.tmax, dirtype, fit.PCA_type)
                                if pars == {} or pars == None:
                                    print(("cannot calculate parameters for element %s and fit %s in calculate_high_level_mean leaving out of fisher mean, please check this value." % (
                                        element, fit.name)))
                                    continue
                                fit.put(element, dirtype, pars)
                        else:
                            continue
                        if "calculation_type" in list(pars.keys()) and pars["calculation_type"] == 'DE-BFP':
                            dec, inc, direction_type = pars["specimen_dec"], pars["specimen_inc"], 'p'
                        elif "specimen_dec" in list(pars.keys()) and "specimen_inc" in list(pars.keys()):
                            dec, inc, direction_type = pars["specimen_dec"], pars["specimen_inc"], 'l'
                        elif "dec" in list(pars.keys()) and "inc" in list(pars.keys()):
                            dec, inc, direction_type = pars["dec"], pars["inc"], 'l'
                        else:
                            print(
                                ("-E- ERROR: can't find mean for specimen interpertation: %s , %s" % (element, fit.name)))
                            print(pars)
                            continue
                        # add for calculation
                        pars_for_mean[fit.name].append({'dec': float(dec), 'inc': float(
                            inc), 'direction_type': direction_type, 'element_name': element})
                        pars_for_mean["All"].append({'dec': float(dec), 'inc': float(
                            inc), 'direction_type': direction_type, 'element_name': element})
                    except KeyError:
                        print(
                            ("KeyError in calculate_high_level_mean for element: " + str(element)))
                        continue
            else:
                try:
                    pars = self.high_level_means[elements_type][element][mean_fit][dirtype]
                    if "dec" in list(pars.keys()) and "inc" in list(pars.keys()):
                        dec, inc, direction_type = pars["dec"], pars["inc"], 'l'
                    else:
                        #                            print "-E- ERROR: can't find mean for element %s"%element
                        continue
                except KeyError:
                    #                        print("KeyError in calculate_high_level_mean for element: " + str(element) + " please report to a dev")
                    continue

        return pars_for_mean

    def calculate_high_level_mean(self, high_level_type, high_level_name, calculation_type, elements_type, mean_fit):
        if calculation_type == "None":
            return

        if high_level_type not in self.high_level_means:
            self.high_level_means[high_level_type] = {}
        if high_level_name not in self.high_level_means[high_level_type]:
            self.high_level_means[high_level_type][high_level_name] = {}
        for dirtype in ["DA-DIR", "DA-DIR-GEO", "DA-DIR-TILT"]:
            if high_level_name not in list(self.Data_hierarchy[high_level_type].keys()):
                continue

            pars_for_mean = self.get_high_level_mean_pars(
                high_level_type, high_level_name, calculation_type, elements_type, mean_fit, dirtype)

            for key in list(pars_for_mean.keys()):
                if len(pars_for_mean[key]) > 0:  # and key == "All":
                    if mean_fit not in list(self.high_level_means[high_level_type][high_level_name].keys()):
                        self.high_level_means[high_level_type][high_level_name][mean_fit] = {
                        }
                    self.high_level_means[high_level_type][high_level_name][mean_fit][dirtype] = self.calculate_mean(
                        pars_for_mean["All"], calculation_type)
                    color = "black"
                    for specimen in self.pmag_results_data['specimens']:
                        colors = [
                            f.color for f in self.pmag_results_data['specimens'][specimen] if f.name == mean_fit]
                        if colors != []:
                            color = colors[0]
                    self.high_level_means[high_level_type][high_level_name][mean_fit][dirtype]['color'] = color
            if 'best fit vector' in self.plane_display_box.GetValue():
                self.calculate_best_fit_vectors(
                    high_level_type, high_level_name)

    def calculate_mean(self, pars_for_mean, calculation_type):
        """
        Uses pmag.dolnp or pmag.fisher_by_pol to do a fisher mean or fisher
        mean by polarity on the list of dictionaries in pars for mean

        Parameters
        ----------
        pars_for_mean : list of dictionaries with all data to average
        calculation_type : type of mean to take (options: Fisher,
        Fisher by polarity)

        Returns
        -------
        mpars : dictionary with information of mean or empty dictionary

        TODO : put Bingham statistics back in once a method for displaying
        them is figured out
        """

        if len(pars_for_mean) == 0:
            return({})

        elif len(pars_for_mean) == 1:
            return ({"dec": float(pars_for_mean[0]['dec']), "inc": float(pars_for_mean[0]['inc']), "calculation_type": calculation_type, "n": 1})

#        elif calculation_type =='Bingham':
#            data=[]
#            for pars in pars_for_mean:
#                # ignore great circle
#                if 'direction_type' in pars.keys() and 'direction_type'=='p':
#                    continue
#                else:
#                    data.append([pars['dec'],pars['inc']])
#            mpars=pmag.dobingham(data)

        elif calculation_type == 'Fisher':
            mpars = pmag.dolnp(pars_for_mean, 'direction_type')

        elif calculation_type == 'Fisher by polarity':
            mpars = pmag.fisher_by_pol(pars_for_mean)
            for key in list(mpars.keys()):
                mpars[key]['n_planes'] = 0
                mpars[key]['calculation_type'] = 'Fisher'

        mpars['calculation_type'] = calculation_type

        return mpars

    def calculate_best_fit_vectors(self, high_level_type=None, high_level_name=None, dirtype=None):
        cur_high_level_type, cur_high_level_name, cur_dirtype = self.get_levels_and_coordinates_names()
        if dirtype == None:
            dirtype = cur_dirtype
        if high_level_name == None:
            high_level_name = cur_high_level_name
        if high_level_type == None:
            high_level_type = cur_high_level_type
        pars_for_mean = self.get_high_level_mean_pars(
            high_level_type, high_level_name, 'Fisher', 'specimens', 'All', dirtype)
        for fname in self.all_fits_list:
            if fname not in list(pars_for_mean.keys()):
                print(("No fits %s in level %s" % (fname, high_level_name)))
                continue
            fdata, n_lines, L, n_planes, E = pmag.process_data_for_mean(
                pars_for_mean[fname], 'direction_type')
            if n_planes == 0:
                continue
            if n_lines == 0:
                # set the initial direction arbitrarily
                V = dir2cart([180., -45., 1.])
            else:
                R = sqrt(E[0]**2+E[1]**2+E[2]**2)
                V = [c/R for c in E]  # set initial direction as mean of lines
            bfvs_cart = pmag.calculate_best_fit_vectors(L, E, V, n_planes)
            bfvs = [pmag.cart2dir(bfv) for bfv in bfvs_cart]
            plane_fits = []
            for par in pars_for_mean[fname]:
                spec = par['element_name']
                for fit in self.pmag_results_data['specimens'][spec]:
                    if fit.PCA_type != "DE-BFP":
                        continue
                    if fit.name == fname:
                        plane_fits.append((spec, fit))
            for (spec, fit), bfv in zip(plane_fits, bfvs):
                fpars = fit.get(dirtype)
                fpars['bfv_dec'] = bfv[0]
                fpars['bfv_inc'] = bfv[1]
                fit.put(spec, dirtype, fpars)

    def calculate_high_levels_data(self):
        """
        calculates high level mean data for the high level mean plot using
        information in level_box, level_names, mean_type_box, and
        mean_fit_box also updates the information in the ie to match high
        level mean data in main GUI.
        """
        high_level_type = str(self.level_box.GetValue())
        if high_level_type == 'sample':
            high_level_type = 'samples'
        if high_level_type == 'site':
            high_level_type = 'sites'
        if high_level_type == 'location':
            high_level_type = 'locations'
        high_level_name = str(self.level_names.GetValue())
        calculation_type = str(self.mean_type_box.GetValue())
        elements_type = self.UPPER_LEVEL_SHOW
        if self.ie_open:
            self.ie.mean_type_box.SetStringSelection(calculation_type)
        self.calculate_high_level_mean(
            high_level_type, high_level_name, calculation_type, elements_type, self.mean_fit)

    def quiet_reset_backend(self, reset_interps=True):
        """
        Doesn't update plots or logger or any visable data but resets all
        measurement data, hierarchy data, and optionally resets
        intepretations.

        Parameters
        ----------
        reset_interps : bool to tell the function to reset fits or
        not.
        """
        new_Data_info = self.get_data_info()
        new_Data, new_Data_hierarchy = self.get_data()

        if not new_Data:
            print("Data read in failed when reseting, aborting reset")
            return
        else:
            self.Data, self.Data_hierarchy, self.Data_info = new_Data, new_Data_hierarchy, new_Data_info

        if reset_interps:
            self.pmag_results_data = {}
            for level in ['specimens', 'samples', 'sites', 'locations', 'study']:
                self.pmag_results_data[level] = {}
            self.high_level_means = {}

            high_level_means = {}
            for high_level in ['samples', 'sites', 'locations', 'study']:
                if high_level not in list(self.high_level_means.keys()):
                    self.high_level_means[high_level] = {}

        # get list of sites
        self.locations = list(self.Data_hierarchy['locations'].keys())
        self.locations.sort()  # get list of sites
        # get list of sites
        self.sites = list(self.Data_hierarchy['sites'].keys())
        self.sites.sort(key=spec_key_func)  # get list of sites
        self.samples = []  # sort the samples within each site
        for site in self.sites:
            self.samples.extend(
                sorted(self.Data_hierarchy['sites'][site]['samples'], key=spec_key_func))
        self.specimens = []  # sort the specimens within each sample
        for samp in self.samples:
            self.specimens.extend(
                sorted(self.Data_hierarchy['samples'][samp]['specimens'], key=spec_key_func))

        # --------------------------------------------------------------------
        # initialize first specimen in list as current specimen
        # --------------------------------------------------------------------
        if self.s in self.specimens:
            pass
        elif len(self.specimens) > 0:
            self.select_specimen(str(self.specimens[0]))
        else:
            self.select_specimen("")
        try:
            self.sample = self.Data_hierarchy['sample_of_specimen'][self.s]
        except KeyError:
            self.sample = ""
        try:
            self.site = self.Data_hierarchy['site_of_specimen'][self.s]
        except KeyError:
            self.site = ""

        if self.Data and reset_interps:
            self.update_pmag_tables()

        if self.ie_open:
            self.ie.specimens_list = self.specimens

    def reset_backend(self, warn_user=True, reset_interps=True):
        """
        Resets GUI data and updates GUI displays such as plots, boxes, and
        logger

        Parameters
        ----------
        warn_user : bool which decides if a warning dialog is displayed to
            the user to ask about reseting data
        reset_interps : bool which decides if interpretations are read in
            for pmag tables or left alone
        """
        if warn_user and not self.data_loss_warning():
            return False

        # reset backend, including get_data(), get_data_info()
        self.quiet_reset_backend(reset_interps=reset_interps)

        # reset specimens box
        self.specimens_box.SetItems(self.specimens)
        self.specimens_box.SetStringSelection(str(self.s))

        # reset site level means box
        self.level_names.Clear()
        self.level_names.AppendItems(self.sites)
        if self.sites:
            self.level_names.SetSelection(0)

        # reset coordinate system
        self.COORDINATE_SYSTEM, self.coordinate_list = self.get_coordinate_system()
        self.coordinates_box.Clear()
        self.coordinates_box.AppendItems(self.coordinate_list)
        self.coordinates_box.SetStringSelection(self.COORDINATE_SYSTEM)

        # get cart rot
        self.initialize_CART_rot(str(self.s))

        # draw everything
        if self.Data:
            if not self.current_fit:
                self.draw_figure(self.s)
                self.update_selection()
            else:
                self.Add_text()
                self.update_fit_boxes()

        if self.ie_open:
            self.ie.update_editor()

    def recalculate_current_specimen_interpreatations(self):
        """
        recalculates all interpretations on all specimens for all coordinate
        systems. Does not display recalcuated data.
        """
        self.initialize_CART_rot(self.s)
        if str(self.s) in self.pmag_results_data['specimens']:
            for fit in self.pmag_results_data['specimens'][self.s]:
                if fit.get('specimen') and 'calculation_type' in fit.get('specimen'):
                    fit.put(self.s, 'specimen', self.get_PCA_parameters(
                        self.s, fit, fit.tmin, fit.tmax, 'specimen', fit.get('specimen')['calculation_type']))
                if len(self.Data[self.s]['zijdblock_geo']) > 0 and fit.get('geographic') and 'calculation_type' in fit.get('geographic'):
                    fit.put(self.s, 'geographic', self.get_PCA_parameters(
                        self.s, fit, fit.tmin, fit.tmax, 'geographic', fit.get('geographic')['calculation_type']))
                if len(self.Data[self.s]['zijdblock_tilt']) > 0 and fit.get('tilt-corrected') and 'calculation_type' in fit.get('tilt-corrected'):
                    fit.put(self.s, 'tilt-corrected', self.get_PCA_parameters(self.s, fit, fit.tmin,
                                                                              fit.tmax, 'tilt-corrected', fit.get('tilt-corrected')['calculation_type']))

    def parse_bound_data(self, tmin0, tmax0, specimen):
        """
        converts Kelvin/Tesla temperature/AF data from the MagIC/Redo format
        to that of Celsius/milliTesla which is used by the GUI as it is
        often more intuitive

        Parameters
        ----------
        tmin0 : the input temperature/AF lower bound value to convert
        tmax0 : the input temperature/AF upper bound value to convert
        specimen : the specimen these bounds are for

        tmin : the converted lower bound temperature/AF or None if input
            format was wrong
        tmax : the converted upper bound temperature/AF or None if the input
            format was wrong
        """
        if specimen not in self.Data:
            print(
                ("no measurement data found loaded for specimen %s and will be ignored" % (specimen)))
            return (None, None)
        if self.Data[specimen]['measurement_step_unit'] == "C":
            if float(tmin0) == 0 or float(tmin0) == 273:
                tmin = "0"
            else:
                tmin = "%.0fC" % (float(tmin0)-273)
            if float(tmax0) == 0 or float(tmax0) == 273:
                tmax = "0"
            else:
                tmax = "%.0fC" % (float(tmax0)-273)
        elif self.Data[specimen]['measurement_step_unit'] == "mT":
            if float(tmin0) == 0:
                tmin = "0"
            else:
                tmin = "%.1fmT" % (float(tmin0)*1000)
            if float(tmax0) == 0:
                tmax = "0"
            else:
                tmax = "%.1fmT" % (float(tmax0)*1000)
        else:  # combimned experiment T:AF
            if float(tmin0) == 0:
                tmin = "0"
            elif "%.0fC" % (float(tmin0)-273) in self.Data[specimen]['zijdblock_steps']:
                tmin = "%.0fC" % (float(tmin0)-273)
            elif "%.1fmT" % (float(tmin0)*1000) in self.Data[specimen]['zijdblock_steps']:
                tmin = "%.1fmT" % (float(tmin0)*1000)
            else:
                tmin = None
            if float(tmax0) == 0:
                tmax = "0"
            elif "%.0fC" % (float(tmax0)-273) in self.Data[specimen]['zijdblock_steps']:
                tmax = "%.0fC" % (float(tmax0)-273)
            elif "%.1fmT" % (float(tmax0)*1000) in self.Data[specimen]['zijdblock_steps']:
                tmax = "%.1fmT" % (float(tmax0)*1000)
            else:
                tmax = None
        return tmin, tmax

    def get_indices(self, fit=None, tmin=None, tmax=None, specimen=None):
        """
        Finds the appropriate indices in self.Data[self.s]['zijdplot_steps']
        given a set of upper/lower bounds. This is to resolve duplicate
        steps using the convention that the first good step of that name is
        the indicated step by that bound if there are no steps of the names
        tmin or tmax then it complains and reutrns a tuple (None,None).

        Parameters
        ----------
        fit : the fit who's bounds to find the indecies of if no upper or
            lower bounds are specified
        tmin : the lower bound to find the index of
        tmax : the upper bound to find the index of
        specimen : the specimen who's steps to search for indecies (defaults
            to currently selected specimen)

        Returns
        -------
        (tmin_index, tmax_index) : a tuple with the lower bound index then
            the upper bound index
        """
        if specimen == None:
            specimen = self.s
        if fit and not tmin and not tmax:
            tmin = fit.tmin
            tmax = fit.tmax
        if specimen not in list(self.Data.keys()):
            self.user_warning("No data for specimen " + specimen)
        if tmin in self.Data[specimen]['zijdblock_steps']:
            tmin_index = self.Data[specimen]['zijdblock_steps'].index(tmin)
        elif type(tmin) == str or type(tmin) == str and tmin != '':
            int_steps = [float(x.strip("C mT"))
                         for x in self.Data[specimen]['zijdblock_steps']]
            if tmin == '':
                tmin = self.Data[specimen]['zijdblock_steps'][0]
                print(("No lower bound for %s on specimen %s using lowest step (%s) for lower bound" % (
                    fit.name, specimen, tmin)))
                if fit != None:
                    fit.tmin = tmin
            int_tmin = float(tmin.strip("C mT"))
            diffs = [abs(x-int_tmin) for x in int_steps]
            tmin_index = diffs.index(min(diffs))
        else:
            tmin_index = self.tmin_box.GetSelection()
        if tmax in self.Data[specimen]['zijdblock_steps']:
            tmax_index = self.Data[specimen]['zijdblock_steps'].index(tmax)
        elif type(tmax) == str or type(tmax) == str and tmax != '':
            int_steps = [float(x.strip("C mT"))
                         for x in self.Data[specimen]['zijdblock_steps']]
            if tmax == '':
                tmax = self.Data[specimen]['zijdblock_steps'][-1]
                print(("No upper bound for fit %s on specimen %s using last step (%s) for upper bound" % (
                    fit.name, specimen, tmax)))
                if fit != None:
                    fit.tmax = tmax
            int_tmax = float(tmax.strip("C mT"))
            diffs = [abs(x-int_tmax) for x in int_steps]
            tmax_index = diffs.index(min(diffs))
        else:
            tmax_index = self.tmin_box.GetSelection()

        max_index = len(self.Data[specimen]['zijdblock_steps'])-1
        while (self.Data[specimen]['measurement_flag'][max_index] == 'b' and max_index-1 > 0):
            max_index -= 1

        if tmin_index >= max_index:
            print(("lower bound is greater or equal to max step cannot determine bounds for specimen: " + specimen))
            return (None, None)

        if (tmin_index >= 0):
            while (self.Data[specimen]['measurement_flag'][tmin_index] == 'b' and
                   tmin_index+1 < len(self.Data[specimen]['zijdblock_steps'])):
                if (self.Data[specimen]['zijdblock_steps'][tmin_index+1] == tmin):
                    tmin_index += 1
                else:
                    tmin_old = tmin
                    while (self.Data[specimen]['measurement_flag'][tmin_index] == 'b' and
                           tmin_index+1 < len(self.Data[specimen]['zijdblock_steps'])):
                        tmin_index += 1
                    tmin = self.Data[specimen]['zijdblock_steps'][tmin_index]
                    if fit != None:
                        fit.tmin = tmin
                    self.tmin_box.SetStringSelection(tmin)
                    print(("For specimen " + str(specimen) + " there are no good measurement steps with value - " +
                           str(tmin_old) + " using step " + str(tmin) + " as lower bound instead"))
                    break

        if (tmax_index < max_index):
            while (self.Data[specimen]['measurement_flag'][tmax_index] == 'b' and
                   tmax_index+1 < len(self.Data[specimen]['zijdblock_steps'])):
                if (self.Data[specimen]['zijdblock_steps'][tmax_index+1] == tmax):
                    tmax_index += 1
                else:
                    tmax_old = tmax
                    while (self.Data[specimen]['measurement_flag'][tmax_index] == 'b' and
                           tmax_index >= 0):
                        tmax_index -= 1
                    tmax = self.Data[specimen]['zijdblock_steps'][tmax_index]
                    if fit != None:
                        fit.tmax = tmax
                    self.tmax_box.SetStringSelection(tmax)
                    print(("For specimen " + str(specimen) + " there are no good measurement steps with value - " +
                           str(tmax_old) + " using step " + str(tmax) + " as upper bound instead"))
                    break

        if (tmin_index < 0):
            tmin_index = 0
        if (tmax_index > max_index):
            tmax_index = max_index

        return (tmin_index, tmax_index)

    def merge_pmag_recs(self, old_recs):
        """
        Takes in a list of dictionaries old_recs and returns a list of
        dictionaries where every dictionary in the returned list has the
        same keys as all the others.

        Parameters
        ----------
        old_recs : list of dictionaries to fix

        Returns
        -------
        recs : list of dictionaries with same keys
        """
        recs = {}
        recs = deepcopy(old_recs)
        headers = []
        for rec in recs:
            for key in list(rec.keys()):
                if key not in headers:
                    headers.append(key)
        for rec in recs:
            for header in headers:
                if header not in list(rec.keys()):
                    rec[header] = ""
        return recs

    #---------------------------------------------#
    # Specimen, Interpretation, & Measurement Alteration
    #---------------------------------------------#

    def select_specimen(self, specimen):
        """
        Goes through the calculations necessary to plot measurement data for
        specimen and sets specimen as current GUI specimen, also attempts to
        handle changing current fit.
        """
        try:
            fit_index = self.pmag_results_data['specimens'][self.s].index(
                self.current_fit)
        except KeyError:
            fit_index = None
        except ValueError:
            fit_index = None
        # sets self.s to specimen calculates params etc.
        self.initialize_CART_rot(specimen)
        self.list_bound_loc = 0
        if fit_index != None and self.s in self.pmag_results_data['specimens']:
            try:
                self.current_fit = self.pmag_results_data['specimens'][self.s][fit_index]
            except IndexError:
                self.current_fit = None
        else:
            self.current_fit = None
        if self.s != self.specimens_box.GetValue():
            self.specimens_box.SetValue(self.s)

    def clear_interpretations(self, message=None):
        """
        Clears all specimen interpretations

        Parameters
        ----------
        message : message to display when warning the user that all
        fits will be deleted. If None default message is used (None is
        default)
        """
        if self.total_num_of_interpertations() == 0:
            print("There are no interpretations")
            return True

        if message == None:
            message = "All interpretations will be deleted all unsaved data will be irretrievable, continue?"
        dlg = wx.MessageDialog(self, caption="Delete?",
                               message=message, style=wx.OK | wx.CANCEL)
        result = self.show_dlg(dlg)
        dlg.Destroy()
        if result != wx.ID_OK:
            return False

        for specimen in list(self.pmag_results_data['specimens'].keys()):
            self.pmag_results_data['specimens'][specimen] = []
            # later on when high level means are fixed remove the bellow loop and loop over pmag_results_data
            for high_level_type in ['samples', 'sites', 'locations', 'study']:
                self.high_level_means[high_level_type] = {}
        self.current_fit = None
        if self.ie_open:
            self.ie.update_editor()
        return True

    def set_test_mode(self, on_off):
        """
        Sets GUI test mode on or off

        Parameters
        ----------
        on_off : bool value to set test mode to
        """
        if type(on_off) != bool:
            print("test mode must be a bool")
            return
        self.test_mode = on_off

    def mark_meas_good(self, g_index):
        """
        Marks the g_index'th measuremnt of current specimen good

        Parameters
        ----------
        g_index : int that gives the index of the measurement to mark good,
            indexed from 0
        """
        meas_index, ind_data = 0, []
        for i, meas_data in enumerate(self.mag_meas_data):
            if meas_data['er_specimen_name'] == self.s:
                ind_data.append(i)
        meas_index = ind_data[g_index]

        self.Data[self.s]['measurement_flag'][g_index] = 'g'
        if len(self.Data[self.s]['zijdblock'][g_index]) < 6:
            self.Data[self.s]['zijdblock'][g_index].append('g')
        self.Data[self.s]['zijdblock'][g_index][5] = 'g'
        if 'zijdblock_geo' in self.Data[self.s] and g_index < len(self.Data[self.s]['zijdblock_geo']):
            if len(self.Data[self.s]['zijdblock_geo'][g_index]) < 6:
                self.Data[self.s]['zijdblock_geo'][g_index].append('g')
            self.Data[self.s]['zijdblock_geo'][g_index][5] = 'g'
        if 'zijdblock_tilt' in self.Data[self.s] and g_index < len(self.Data[self.s]['zijdblock_tilt']):
            if len(self.Data[self.s]['zijdblock_tilt'][g_index]) < 6:
                self.Data[self.s]['zijdblock_tilt'][g_index].append('g')
            self.Data[self.s]['zijdblock_tilt'][g_index][5] = 'g'
        self.mag_meas_data[meas_index]['measurement_flag'] = 'g'

        if self.data_model == 3.0:
            meas_name = str(self.Data[self.s]['measurement_names'][g_index])
            mdf = self.con.tables['measurements'].df
            # check for multiple measurements with the same name
            if not isinstance(mdf.loc[meas_name], pd.Series):
                res = self.user_warning("Your measurements table has non-unique measurement names.\nYou may end up marking more than one measurement as good.\nRight click this measurement again to undo.")
            # mark measurement as good
            mdf.loc[meas_name, 'quality'] = 'g'


    def mark_meas_bad(self, g_index):
        """
        Marks the g_index'th measuremnt of current specimen bad

        Parameters
        ----------
        g_index : int that gives the index of the measurement to mark bad,
            indexed from 0
        """
        meas_index, ind_data = 0, []
        for i, meas_data in enumerate(self.mag_meas_data):
            if meas_data['er_specimen_name'] == self.s:
                ind_data.append(i)
        meas_index = ind_data[g_index]

        self.Data[self.s]['measurement_flag'][g_index] = 'b'
        if len(self.Data[self.s]['zijdblock'][g_index]) < 6:
            self.Data[self.s]['zijdblock'][g_index].append('g')
        self.Data[self.s]['zijdblock'][g_index][5] = 'b'
        if 'zijdblock_geo' in self.Data[self.s] and g_index < len(self.Data[self.s]['zijdblock_geo']):
            if len(self.Data[self.s]['zijdblock_geo'][g_index]) < 6:
                self.Data[self.s]['zijdblock_geo'][g_index].append('g')
            self.Data[self.s]['zijdblock_geo'][g_index][5] = 'b'
        if 'zijdblock_tilt' in self.Data[self.s] and g_index < len(self.Data[self.s]['zijdblock_tilt']):
            if len(self.Data[self.s]['zijdblock_tilt'][g_index]) < 6:
                self.Data[self.s]['zijdblock_tilt'][g_index].append('g')
            self.Data[self.s]['zijdblock_tilt'][g_index][5] = 'b'
        self.mag_meas_data[meas_index]['measurement_flag'] = 'b'

        if self.data_model == 3.0:
            meas_name = str(self.Data[self.s]['measurement_names'][g_index])
            mdf = self.con.tables['measurements'].df
            # check for multiple measurements with the same name
            if not isinstance(mdf.loc[meas_name], pd.Series):
                res = self.user_warning("Your measurements table has non-unique measurement names.\nYou may end up marking more than one measurement as bad.\nRight click this measurement again to undo.")
            # mark measurement as bad
            mdf.loc[meas_name, 'quality'] = 'b'

    def mark_fit_good(self, fit, spec=None):
        """
        Marks fit good so it is used in high level means

        Parameters
        ----------
        fit : fit to mark good
        spec : specimen of fit to mark good (optional though runtime will
            increase if not provided)
        """
        if spec == None:
            for spec, fits in list(self.pmag_results_data['specimens'].items()):
                if fit in fits:
                    break
        samp = self.Data_hierarchy['sample_of_specimen'][spec]
        if 'sample_orientation_flag' not in self.Data_info['er_samples'][samp]:
            self.Data_info['er_samples'][samp]['sample_orientation_flag'] = 'g'
        samp_flag = self.Data_info['er_samples'][samp]['sample_orientation_flag']
        if samp_flag == 'g':
            self.bad_fits.remove(fit)
            return True
        else:
            self.user_warning(
                "Cannot mark this interpretation good its sample orientation has been marked bad")
            return False

    def mark_fit_bad(self, fit):
        """
        Marks fit bad so it is excluded from high level means

        Parameters
        ----------
        fit : fit to mark bad
        """
        if fit not in self.bad_fits:
            self.bad_fits.append(fit)
            return True
        else:
            return False

    #---------------------------------------------#
    # Data Read and Location Alteration Functions
    #---------------------------------------------#

    def get_data(self):
        """
        reads data from current WD measurement.txt or magic_measurements.txt
        depending on data model and sorts it into main measurements data
        structures given bellow:
        Data - {specimen: {
                zijdblock:[[treatment temp-str,dec-float, inc-float,
                        mag_moment-float, ZI-float, meas_flag-str ('b','g'),
                        method_codes-str]],
                zijdblock_geo:[[treatment temp-str,dec-float, inc-float,
                        mag_moment-float, ZI-float, meas_flag-str ('b','g'),
                        method_codes-str]],
                zijdblock_tilt:[[treatment temp-str,dec-float, inc-float,
                        mag_moment-float, ZI-float, meas_flag-str ('b','g'),
                        method_codes-str]],
                zijdblock_lab_treatments: [str],
                zijdblock_steps: [str],
                measurement_flag: [str ('b','g')],
                mag_meas_data_index: [int],
                csds: [float],
                pars: {},
                zdata: array.shape = 2x2 (float),
                zdata_geo: array.shape = 2x2 (float),
                zdata_tilt: array.shape = 2x2 (float),
                vector_diffs: [float],
                vds: float }}
        Data_hierarchy - {specimen: {
                            study: {}
                            locations: {}
                            sites: {}
                            samples: {}
                            specimens: {}
                            sample_of_specimen: {}
                            site_of_specimen: {}
                            site_of_sample: {}
                            location_of_site: {}
                            location_of_specimen: {}
                            study_of_specimen: {}
                            expedition_name_of_specimen: {} }}
        """
        # ------------------------------------------------
        # Read magic measurement file and sort to blocks
        # ------------------------------------------------

        # All meas data information is stored in Data[secimen]={}
        Data = {}
        Data_hierarchy = {}
        Data_hierarchy['study'] = {}
        Data_hierarchy['locations'] = {}
        Data_hierarchy['sites'] = {}
        Data_hierarchy['samples'] = {}
        Data_hierarchy['specimens'] = {}
        Data_hierarchy['sample_of_specimen'] = {}
        Data_hierarchy['site_of_specimen'] = {}
        Data_hierarchy['site_of_sample'] = {}
        Data_hierarchy['location_of_site'] = {}
        Data_hierarchy['location_of_specimen'] = {}
        Data_hierarchy['study_of_specimen'] = {}
        Data_hierarchy['expedition_name_of_specimen'] = {}

        if self.data_model == 3:

            if 'measurements' not in self.con.tables:
                self.user_warning(
                    "Measurement data file is empty and the GUI cannot start, aborting")
                return Data, Data_hierarchy

            if self.con.tables['measurements'].df.empty:
                self.user_warning(
                    "Measurement data file is empty and the GUI cannot start, aborting")
                return Data, Data_hierarchy

            # extract specimen data from measurements table
            if not len(self.spec_data):
                specs = self.con.tables['measurements'].df['specimen'].unique()
                df = pd.DataFrame(index=specs, columns=['specimen'])
                df.index.name = 'specimen_name'
                df['specimen'] = specs
                self.con.tables['specimens'].df = df
                self.spec_data = df

            if not len(self.spec_data):
                self.user_warning(
                    "Measurement data file does not seem to have specimen data and the GUI cannot start, aborting")
                return Data, Data_hierarchy


            if 'sample' not in self.spec_data.columns or 'sample' not in self.samp_data.columns:
                if 'specimen' not in self.spec_data.columns:
                    self.spec_data['specimen'] = self.con.tables['measurements'].df['specimen']
                    self.spec_data.set_index('specimen', inplace=True)
                    self.spec_data['specimen'] = self.spec_data.index

                ui_dialog = demag_dialogs.user_input(
                    self, ["# of characters to remove"], heading="Sample data could not be found attempting to generate sample names by removing characters from specimen names")
                self.show_dlg(ui_dialog)
                ui_data = ui_dialog.get_values()
                try:
                    samp_ncr = int(ui_data[1]["# of characters to remove"])
                except ValueError:
                    self.user_warning(
                        "Invalid input, specimen names will be used for sample names instead")
                    samp_ncr = 0
                self.spec_data['sample'] = [x[:-samp_ncr]
                                            for x in self.spec_data['specimen']]

                self.samp_data['sample'] = self.spec_data['sample']
                self.samp_data.set_index('sample', inplace=True)
                self.samp_data['sample'] = self.samp_data.index

            if 'site' not in self.samp_data.columns or 'site' not in self.site_data.columns:
                ui_dialog = demag_dialogs.user_input(
                    self, ["# of characters to remove", "site delimiter"], heading="No Site Data found attempting to create site names from specimen names")
                self.show_dlg(ui_dialog)
                ui_data = ui_dialog.get_values()
                try:
                    site_ncr = int(ui_data[1]["# of characters to remove"])
                    self.samp_data['site'] = [x[:-site_ncr]
                                              for x in self.spec_data['specimen']]
                except ValueError:
                    try:
                        sd = ui_data[1]["site delimiter"]
                        self.samp_data['site'] = [
                            x.split(sd)[0] for x in self.spec_data['specimen']]
                    except ValueError:
                        self.samp_data['site'] = [
                            x for x in self.spec_data['specimen']]

                self.site_data['site'] = self.samp_data['site']
                self.site_data.drop_duplicates(inplace=True)
                self.site_data.set_index('site', inplace=True)
                self.site_data['site'] = self.site_data.index

            if 'location' not in self.site_data.columns or 'location' not in self.loc_data.columns:
                ui_dialog = demag_dialogs.user_input(
                    self, ["location name for all sites"], heading="No Location found")
                self.show_dlg(ui_dialog)
                ui_data = ui_dialog.get_values()
                self.site_data['location'] = ui_data[1]["location name for all sites"]

                self.loc_data['location'] = self.site_data['location']
                self.loc_data.drop_duplicates(inplace=True)
                self.loc_data.set_index('location', inplace=True)
                self.loc_data['location'] = self.loc_data.index

            # add data to other dataframes
            self.con.propagate_location_to_measurements()
            self.con.propagate_location_to_specimens()

            # get measurement data from contribution object
            meas_container = self.con.tables['measurements']
            meas_data3_0 = meas_container.df

            meas_data3_0.replace({'specimen': {nan: 'unknown'}, 'sample': {nan: 'unknown'}, 'site': {
                                 nan: 'unknown'}, 'location': {nan: 'unknown'}}, inplace=True)
            meas_data3_0['specimen'] = meas_data3_0['specimen'].apply(str)
            meas_data3_0['sample'] = meas_data3_0['sample'].apply(str)
            meas_data3_0['site'] = meas_data3_0['site'].apply(str)
            meas_data3_0['location'] = meas_data3_0['location'].apply(str)

            # do some filtering
#            if 'location' in meas_data3_0.columns:
#                if any(meas_data3_0['location'].isnull()):
#                    print("-W- Some measurements are missing location data, and will not be used")
#                meas_data3_0 = meas_data3_0[meas_data3_0['location'].notnull()]
# meas_data3_0.replace({'location':float('nan')},'unknown',inplace=True)
#            if 'site' in meas_data3_0.columns:
#                if any(meas_data3_0['site'].isnull()):
#                    print("-W- Some measurements are missing site data, and will not be used")
#                meas_data3_0 = meas_data3_0[meas_data3_0['site'].notnull()]
# meas_data3_0.replace({'site':float('nan')},'unknown',inplace=True)
#            if 'sample' in meas_data3_0.columns:
#                if any(meas_data3_0['sample'].isnull()):
#                    print("-W- Some measurements are missing sample data, and will not be used")
#                meas_data3_0 = meas_data3_0[meas_data3_0['sample'].notnull()]
# meas_data3_0.replace({'sample':float('nan')},'unknown',inplace=True)
#            if 'specimen' in meas_data3_0.columns:
#                missing = meas_data3_0[meas_data3_0['specimen'].isnull()]
#                if len(missing):
#                    print("-W- {} measurements are missing specimen data, and will not be used".format(missing))
#                meas_data3_0 = meas_data3_0[meas_data3_0['specimen'].notnull()]
# meas_data3_0.replace({'specimen':float('nan')},'unknown',inplace=True)

#            col_names = ['specimen', 'sample', 'site', 'location']
#            for col_name in col_names:
#                if col_name in meas_data3_0.columns:
#                    pruned = meas_data3_0[meas_data3_0[col_name].apply(cb.not_null)]
#                    num_missing = len(meas_data3_0) - len(pruned)
#                    if num_missing:
#                        msg = "{} measurements cannot be associated with a {} and will be excluded\nTry using Pmag GUI (step 3) to make sure you have provided the full chain from specimen to location.".format(num_missing, col_name)
#                        pw.simple_warning(msg)
#                        print("-W- {} measurements are missing {} data and will be excluded".format(num_missing, col_name))
#                        meas_data3_0 = pruned
            Mkeys = ['magn_moment', 'magn_volume', 'magn_mass']
# fish out all the relavent data
            meas_data3_0 = meas_data3_0[meas_data3_0['method_codes'].str.contains(
                'LT-NO|LT-AF-Z|LT-T-Z|LT-M-Z|LT-LT-Z') == True]
            if not len(meas_data3_0):
                self.user_warning("Your measurements table contains none of the required method codes to run Demag GUI: [LT-NO, LT-AF-Z, LT-T-Z, LT-M-Z, LT-LT-Z]")
                return {}, {}
# now convert back to 2.5  changing only those keys that are necessary for thellier_gui
            meas_con_dict = map_magic.get_thellier_gui_meas_mapping(
                meas_data3_0, output=2)
            intensity_col = cb.get_intensity_col(meas_data3_0)
            if not intensity_col:
                self.user_warning("Your measurements table must have one of the following columns to run Demag GUI: 'magn_moment', 'magn_volume', 'magn_mass',or 'magn_uncal'")
                return {}, {}

            print('-I- Using {} for intensity'.format(intensity_col))
            self.intensity_col = meas_con_dict[intensity_col]
            meas_data2_5 = meas_data3_0.rename(columns=meas_con_dict)
            # make a list of dictionaries to maintain backward compatibility
            mag_meas_data = meas_data2_5.to_dict("records")

        else:  # data model 2.5
            try:
                print(("-I- Read magic file %s" % self.magic_file))
            except ValueError:
                self.magic_measurement = self.choose_meas_file()
                print(("-I- Read magic file %s" % self.magic_file))
            mag_meas_data, file_type = pmag.magic_read(self.magic_file)
            if file_type != "magic_measurements":
                self.user_warning("You have selected data model 2.5, but your measurements file is either not in 2.5, or is not a measurements file.\n{} has file type: {}".format(self.magic_file, file_type))
                return {}, {}


        self.mag_meas_data = self.merge_pmag_recs(mag_meas_data)

        # get list of unique specimen names with measurement data
        CurrRec = []
        sids = pmag.get_specs(self.mag_meas_data)  # specimen ID's
        for s in sids:
            if s not in list(Data.keys()):
                Data[s] = {}
                Data[s]['zijdblock'] = []
                Data[s]['zijdblock_geo'] = []
                Data[s]['zijdblock_tilt'] = []
                Data[s]['zijdblock_lab_treatments'] = []
                Data[s]['pars'] = {}
                Data[s]['csds'] = []
                Data[s]['zijdblock_steps'] = []
                Data[s]['measurement_flag'] = []  # a list of points 'g' or 'b'
                # index in original magic_measurements.txt
                Data[s]['mag_meas_data_index'] = []
                Data[s]['measurement_names'] = []

        prev_s = None
        cnt = -1
        # list of excluded lab protocols. copied from pmag.find_dmag_rec(s,data)
        self.excluded_methods = ["LP-AN-ARM", "LP-AN-TRM", "LP-ARM-AFD",
                                 "LP-ARM2-AFD", "LP-TRM-AFD", "LP-TRM", "LP-TRM-TD", "LP-X", "LP-PI-ARM"]
        self.included_methods = [
            "LT-NO", "LT-AF-Z", "LT-T-Z", "LT-M-Z", "LT-LT-Z"]
#        self.mag_meas_data.sort(key=meas_key)
        # asiigned default values for NRM
        if len(self.mag_meas_data) > 0 and self.intensity_col in list(self.mag_meas_data[0].keys()):
            NRM = float(self.mag_meas_data[0][self.intensity_col])
        for rec in self.mag_meas_data:
            # if "measurement_number" in rec.keys() and str(rec['measurement_number']) == '1' and "magic_method_codes" in rec.keys() and "LT-NO" not in rec["magic_method_codes"].split(':'):
            #    NRM = 1 #not really sure how to handle this case but assume that data is already normalized
            cnt += 1  # index counter
            s = rec["er_specimen_name"]
            if "er_sample_name" in list(rec.keys()):
                sample = rec["er_sample_name"]
            else:
                sample = ''
            if "er_site_name" in list(rec.keys()):
                site = rec["er_site_name"]
            else:
                site = ''
            if "er_location_name" in list(rec.keys()):
                location = rec["er_location_name"]
            else:
                location = ''
            expedition_name = ""
            if "er_expedition_name" in list(rec.keys()):
                expedition_name = rec["er_expedition_name"]

            methods = rec["magic_method_codes"].replace(
                " ", "").strip("\n").split(":")
            LP_methods = []
            LT_methods = []

            for k in ['zdata', 'zdata_geo', 'zdata_tilt', 'vector_diffs']:
                if k not in Data[s]:
                    Data[s][k] = []

            for i in range(len(methods)):
                methods[i] = methods[i].strip()
            if 'measurement_flag' not in list(rec.keys()):
                rec['measurement_flag'] = 'g'
            SKIP = True
            lab_treatment = ""
            for meth in methods:
                if 'DIR' in meth:
                    SKIP = False
                if meth in self.included_methods:
                    lab_treatment = meth
                    SKIP = False
                if "LP" in meth:
                    LP_methods.append(meth)
            for meth in self.excluded_methods:
                if meth in methods:
                    SKIP = True
                    break
            if SKIP:
                continue
            tr, LPcode, measurement_step_unit = "", "", ""
            if "LT-NO" in methods:
                tr = 0
                if prev_s != s and self.intensity_col in rec:
                    try:
                        NRM = float(rec[self.intensity_col])
                    except ValueError:
                        NRM = 1
                for method in methods:
                    if "AF" in method:
                        LPcode = "LP-DIR-AF"
                        measurement_step_unit = "mT"
                    if "TRM" in method:
                        LPcode = "LP-DIR-T"
                        measurement_step_unit = "C"
            elif "LT-AF-Z" in methods:
                try:
                    tr = float(rec["treatment_ac_field"])*1e3  # (mT)
                except ValueError:
                    print(("Could not convert ac field for measurement, was given %s, skipping" %
                           rec["treatment_ac_field"]))
                    continue
                measurement_step_unit = "mT"  # in magic its T in GUI its mT
                LPcode = "LP-DIR-AF"
            elif "LT-T-Z" in methods or "LT-LT-Z" in methods:
                try:
                    tr = float(rec["treatment_temp"])-273.  # celsius
                except ValueError:
                    print(
                        ("Could not convert temperature for measurement, was given %s, skipping" % rec["treatment_temp"]))
                    continue
                measurement_step_unit = "C"  # in magic its K in GUI its C
                LPcode = "LP-DIR-T"
            elif "LT-M-Z" in methods:
                # temporary for microwave
                tr = float(rec["measurement_number"])
            else:
                # attempt to determine from treatment data
                if all(im not in methods for im in self.included_methods):
                    if 'treatment_temp' in list(rec.keys()) and not str(rec['treatment_temp']).isalpha() and rec['treatment_temp'] != '' and float(rec['treatment_temp']) > 0:
                        tr = float(rec["treatment_temp"])-273.  # celsius
                        measurement_step_unit = "C"  # in magic its K in GUI its C
                        LPcode = "LP-DIR-T"
                    elif 'treatment_ac_field' in list(rec.keys()) and not str(rec['treatment_ac_field']).isalpha() and rec['treatment_ac_field'] != '' and float(rec['treatment_ac_field']) > 0:
                        tr = float(rec["treatment_ac_field"])*1e3  # (mT)
                        measurement_step_unit = "mT"  # in magic its T in GUI its mT
                        LPcode = "LP-DIR-AF"
                    else:
                        tr = 0
                        if prev_s != s and self.intensity_col in rec:
                            try:
                                NRM = float(rec[self.intensity_col])
                            except ValueError:
                                NRM = 1
                        for method in methods:
                            if "AF" in method:
                                LPcode = "LP-DIR-AF"
                                measurement_step_unit = "mT"
                            if "TRM" in method:
                                LPcode = "LP-DIR-T"
                                measurement_step_unit = "C"
                else:
                    tr = float(rec["measurement_number"])
            if prev_s != s and len(Data[s]['zijdblock']) > 0:
                NRM = Data[s]['zijdblock'][0][3]

            ZI = 0
            if tr != "":
                Data[s]['mag_meas_data_index'].append(
                    cnt)  # magic_measurement file intex
                if not int(self.data_model) == 2:
                    try:
                        Data[s]['measurement_names'].append(rec['measurement'])
                    except KeyError:
                        Data[s]['measurement_names'].append(rec['measurement_number'])
                Data[s]['zijdblock_lab_treatments'].append(lab_treatment)
                if measurement_step_unit != "":
                    if 'measurement_step_unit' in list(Data[s].keys()):
                        if measurement_step_unit not in Data[s]['measurement_step_unit'].split(":"):
                            Data[s]['measurement_step_unit'] = Data[s]['measurement_step_unit'] + \
                                ":"+measurement_step_unit
                    else:
                        Data[s]['measurement_step_unit'] = measurement_step_unit
                dec, inc, inten = "", "", ""
                if "measurement_dec" in list(rec.keys()) and cb.not_null(rec["measurement_dec"], False):
                    dec = float(rec["measurement_dec"])
                else:
                    continue
                if "measurement_inc" in list(rec.keys()) and cb.not_null(rec["measurement_inc"], False):
                    inc = float(rec["measurement_inc"])
                else:
                    continue
                if self.intensity_col in list(rec.keys()) and cb.not_null(rec[self.intensity_col], False):
                    intensity = float(rec[self.intensity_col])
                else:
                    intensity = 1.  # just assume a normal vector
                if 'magic_instrument_codes' not in list(rec.keys()):
                    rec['magic_instrument_codes'] = ''
                if 'measurement_csd' in list(rec.keys()):
                    csd = str(rec['measurement_csd'])
                else:
                    csd = ''
                Data[s]['zijdblock'].append(
                    [tr, dec, inc, intensity, ZI, rec['measurement_flag'], rec['magic_instrument_codes']])
                Data[s]['csds'].append(csd)
                DIR = [dec, inc, intensity/NRM]
                cart = pmag.dir2cart(DIR)
                Data[s]['zdata'].append(array([cart[0], cart[1], cart[2]]))

                if 'magic_experiment_name' in list(Data[s].keys()) and Data[s]['magic_experiment_name'] != rec["magic_experiment_name"]:
                    print(("-E- ERROR: specimen %s has more than one demagnetization experiment name. You need to merge them to one experiment-name?" % (s)))
                if float(tr) == 0 or float(tr) == 273:
                    Data[s]['zijdblock_steps'].append("0")
                elif measurement_step_unit == "C":
                    Data[s]['zijdblock_steps'].append(
                        "%.0f%s" % (tr, measurement_step_unit))
                else:
                    Data[s]['zijdblock_steps'].append(
                        "%.1f%s" % (tr, measurement_step_unit))
                # --------------
                if 'magic_experiment_name' in list(rec.keys()):
                    Data[s]['magic_experiment_name'] = rec["magic_experiment_name"]
                if "magic_instrument_codes" in list(rec.keys()):
                    Data[s]['magic_instrument_codes'] = rec['magic_instrument_codes']
                Data[s]["magic_method_codes"] = LPcode

                # --------------
                # ""good" or "bad" data
                # --------------

                flag = 'g'
                if 'measurement_flag' in list(rec.keys()):
                    if str(rec["measurement_flag"]) == 'b':
                        flag = 'b'
                Data[s]['measurement_flag'].append(flag)

                # gegraphic coordinates
                try:
                    sample_azimuth = float(
                        self.Data_info["er_samples"][sample]['sample_azimuth'])
                    sample_dip = float(
                        self.Data_info["er_samples"][sample]['sample_dip'])
                    d_geo, i_geo = pmag.dogeo(
                        dec, inc, sample_azimuth, sample_dip)
                    # if d_geo or i_geo is null, we can't do geographic coordinates
                    # otherwise, go ahead
                    if not any([np.isnan(val) for val in [d_geo, i_geo]]):
                        Data[s]['zijdblock_geo'].append(
                            [tr, d_geo, i_geo, intensity, ZI, rec['measurement_flag'], rec['magic_instrument_codes']])
                        DIR = [d_geo, i_geo, intensity/NRM]
                        cart = pmag.dir2cart(DIR)
                        Data[s]['zdata_geo'].append([cart[0], cart[1], cart[2]])
                except (IOError, KeyError, ValueError, TypeError) as e:
                    pass
                #                    if prev_s != s:
                #                        print( "-W- can't find sample_azimuth,sample_dip for sample %s"%sample)

                # tilt-corrected coordinates
                try:
                    sample_bed_dip_direction = float(
                        self.Data_info["er_samples"][sample]['sample_bed_dip_direction'])
                    sample_bed_dip = float(
                        self.Data_info["er_samples"][sample]['sample_bed_dip'])
                    d_tilt, i_tilt = pmag.dotilt(
                        d_geo, i_geo, sample_bed_dip_direction, sample_bed_dip)
                    Data[s]['zijdblock_tilt'].append(
                        [tr, d_tilt, i_tilt, intensity, ZI, rec['measurement_flag'], rec['magic_instrument_codes']])
                    DIR = [d_tilt, i_tilt, intensity/NRM]
                    cart = pmag.dir2cart(DIR)
                    Data[s]['zdata_tilt'].append([cart[0], cart[1], cart[2]])
                except (IOError, KeyError, TypeError, ValueError, UnboundLocalError) as e:
                    pass
                #                    if prev_s != s:
                #                        printd("-W- can't find tilt-corrected data for sample %s"%sample)

                if len(Data[s]['zdata']) > 1:
                    Data[s]['vector_diffs'].append(
                        sqrt(sum((array(Data[s]['zdata'][-2])-array(Data[s]['zdata'][-1]))**2)))

            # ---------------------
            # hierarchy is determined from magic_measurements.txt
            # ---------------------

            if sample not in list(Data_hierarchy['samples'].keys()):
                Data_hierarchy['samples'][sample] = {}
                Data_hierarchy['samples'][sample]['specimens'] = []

            if site not in list(Data_hierarchy['sites'].keys()):
                Data_hierarchy['sites'][site] = {}
                Data_hierarchy['sites'][site]['samples'] = []
                Data_hierarchy['sites'][site]['specimens'] = []

            if location not in list(Data_hierarchy['locations'].keys()):
                Data_hierarchy['locations'][location] = {}
                Data_hierarchy['locations'][location]['sites'] = []
                Data_hierarchy['locations'][location]['samples'] = []
                Data_hierarchy['locations'][location]['specimens'] = []

            if 'this study' not in list(Data_hierarchy['study'].keys()):
                Data_hierarchy['study']['this study'] = {}
                Data_hierarchy['study']['this study']['sites'] = []
                Data_hierarchy['study']['this study']['samples'] = []
                Data_hierarchy['study']['this study']['specimens'] = []

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

            # Data_hierarchy['specimens'][s]=sample
            Data_hierarchy['sample_of_specimen'][s] = sample
            Data_hierarchy['site_of_specimen'][s] = site
            Data_hierarchy['site_of_sample'][sample] = site
            Data_hierarchy['location_of_site'][site] = location
            Data_hierarchy['location_of_specimen'][s] = location
            if expedition_name != "":
                Data_hierarchy['expedition_name_of_specimen'][s] = expedition_name
            prev_s = s

        print("-I- done sorting meas data")
        self.specimens = list(Data.keys())

        for s in self.specimens:
            if len(Data[s]['zdata']) > 0:
                Data[s]['vector_diffs'].append(
                    sqrt(sum(array(Data[s]['zdata'][-1])**2)))  # last vector of the vds
            vds = sum(Data[s]['vector_diffs'])  # vds calculation
            Data[s]['vector_diffs'] = array(Data[s]['vector_diffs'])
            Data[s]['vds'] = vds
            Data[s]['zdata'] = array(Data[s]['zdata'])
            Data[s]['zdata_geo'] = array(Data[s]['zdata_geo'])
            Data[s]['zdata_tilt'] = array(Data[s]['zdata_tilt'])
        return(Data, Data_hierarchy)

    def get_interpretations3(self):
        """
        Used instead of update_pmag_tables in data model 3.0 to fetch
        interpretations from contribution objects
        """
        if "specimen" not in self.spec_data.columns or \
           "meas_step_min" not in self.spec_data.columns or \
           "meas_step_max" not in self.spec_data.columns or \
           "meas_step_unit" not in self.spec_data.columns or \
           "method_codes" not in self.spec_data.columns:
               return
        if "dir_comp" in self.spec_data.columns:
            fnames = 'dir_comp'
        elif "dir_comp_name" in self.spec_data.columns:
            fnames = 'dir_comp_name'
        else:
            fnames = 'dir_comp'
            self.spec_data['dir_comp'] = 'Fit 1'
            #print("No specimen interpretation name found in specimens.txt")
            #return
        if "result_quality" not in self.spec_data.columns:
            self.spec_data["result_quality"] = "g"
        if "dir_tilt_correction" not in self.spec_data.columns:
            self.spec_data["dir_tilt_correction"] = ""
        fdict = self.spec_data[['specimen', fnames, 'meas_step_min', 'meas_step_max', 'meas_step_unit',
                                'dir_tilt_correction', 'method_codes', 'result_quality']].to_dict("records")
        for i in range(len(fdict)):
            spec = fdict[i]['specimen']
            if spec not in self.specimens:
                print(("-E- specimen %s does not exist in measurement data" % (spec)))
                continue
            fname = fdict[i][fnames]
            if fname == None or (spec in list(self.pmag_results_data['specimens'].keys()) and fname in [x.name for x in self.pmag_results_data['specimens'][spec]]):
                continue
            if fdict[i]['meas_step_unit'] == "K":
                fmin = int(float(fdict[i]['meas_step_min'])-273)
                fmax = int(float(fdict[i]['meas_step_max'])-273)
                if fmin == 0:
                    fmin = str(fmin)
                else:
                    fmin = str(fmin)+"C"
                if fmax == 0:
                    fmax = str(fmax)
                else:
                    fmax = str(fmax)+"C"
            elif fdict[i]['meas_step_unit'] == "T":
                fmin = float(fdict[i]['meas_step_min'])*1000
                fmax = float(fdict[i]['meas_step_max'])*1000
                if fmin == 0:
                    fmin = str(int(fmin))
                else:
                    fmin = str(fmin)+"mT"
                if fmax == 0:
                    fmax = str(int(fmax))
                else:
                    fmax = str(fmax)+"mT"
            else:
                fmin = fdict[i]['meas_step_min']
                fmax = fdict[i]['meas_step_max']

            PCA_types = ["DE-BFL", "DE-BFL-A", "DE-BFL-O", "DE-FM", "DE-BFP"]
            PCA_type_list = [x for x in str(fdict[i]['method_codes']).split(
                ':') if x.strip() in PCA_types]
            if len(PCA_type_list) > 0:
                PCA_type = PCA_type_list[0].strip()
            else:
                PCA_type = "DE-BFL"

            fit = self.add_fit(spec, fname, fmin, fmax, PCA_type)

            if fdict[i]['result_quality'] == 'b':
                self.bad_fits.append(fit)

    def get_data_info(self):
        """
        imports er tables and places data into Data_info data structure
        outlined bellow:
        Data_info - {er_samples: {er_samples.txt info}
                     er_sites: {er_sites.txt info}
                     er_locations: {er_locations.txt info}
                     er_ages: {er_ages.txt info}}
        """
        Data_info = {}
        data_er_samples = {}
        data_er_sites = {}
        data_er_locations = {}
        data_er_ages = {}

        if self.data_model == 3.0:
            print(("data model: %1.1f" % (self.data_model)))
            Data_info["er_samples"] = []
            Data_info["er_sites"] = []
            Data_info["er_locations"] = []
            Data_info["er_ages"] = []

            # self.magic_file may have a full path, but this breaks cb.Contribution
            # determine if magic_file exists in WD, and if it doesn't, copy it in

            magic_file_real = os.path.realpath(self.magic_file)
            magic_file_short = os.path.split(self.magic_file)[1]
            WD_file_real = os.path.realpath(
                os.path.join(self.WD, magic_file_short))
            if magic_file_real == WD_file_real:
                fnames = {'measurements': magic_file_short}
            else:
                # copy measurements file to WD, keeping original name
                shutil.copy(magic_file_real, WD_file_real)
                fnames = {'measurements': magic_file_short}
            self.con = cb.Contribution(self.WD, custom_filenames=fnames, read_tables=[
                                       'measurements', 'specimens', 'samples', 'sites', 'locations', 'criteria', 'ages'])
            if 'specimens' in self.con.tables:
                spec_container = self.con.tables['specimens']
                self.spec_data = spec_container.df
            else:
                self.con.add_empty_magic_table('specimens')
                self.spec_data = self.con.tables['specimens'].df
            if 'samples' in self.con.tables:
                samp_container = self.con.tables['samples']
                samp_container.front_and_backfill(['azimuth', 'dip'])
                self.samp_data = samp_container.df
                samp_data2 = self.samp_data.rename(
                    columns=map_magic.samp_magic3_2_magic2_map)
                data_er_samples = samp_data2.T.to_dict()
            else:
                self.con.add_empty_magic_table('samples')
                self.samp_data = self.con.tables['samples'].df
            if 'sites' in self.con.tables:
                site_container = self.con.tables['sites']
                self.site_data = site_container.df
                if 'age' in self.site_data.columns:
                    self.site_data = self.site_data[self.site_data['age'].notnull(
                    )]
                    age_ids = [col for col in self.site_data.columns if col.startswith(
                        "age") or col == "site"]
                    age_data = self.site_data[age_ids].rename(
                        columns=map_magic.site_magic3_2_magic2_map)
                    # save this in 2.5 format
                    er_ages = age_data.to_dict('records')
                    data_er_ages = {}
                    for s in er_ages:
                        s = self.convert_ages_to_calendar_year(s)
                        data_er_ages[s['er_site_name']] = s
                sites = self.site_data.rename(
                    columns=map_magic.site_magic3_2_magic2_map)
                # pick out what is needed by thellier_gui and put in 2.5 format
                er_sites = sites.to_dict('records')
                data_er_sites = {}
                for s in er_sites:
                    data_er_sites[s['er_site_name']] = s
            else:
                self.con.add_empty_magic_table('sites')
                self.site_data = self.con.tables['sites'].df
            if 'locations' in self.con.tables:
                location_container = self.con.tables["locations"]
                self.loc_data = location_container.df  # only need this for saving tables
                if self.loc_data['location'].isnull().any():
                    self.loc_data.replace(
                        {'location': {None: 'unknown'}}, inplace=True)
                    self.loc_data.set_index('location', inplace=True)
                    self.loc_data['location'] = self.loc_data.index
                loc2_data = self.loc_data.rename(
                    columns=map_magic.loc_magic3_2_magic2_map)
     # there were problems with this command in some contributions:
                #data_er_locations = loc2_data.to_dict('index') #TRY
            else:
                self.con.add_empty_magic_table('locations')
                self.loc_data = self.con.tables['locations'].df

        else:  # try 2.5 data model

            print(("data model: %1.1f" % (self.data_model)))
            self.read_magic_file(os.path.join(
                self.WD, "er_samples.txt"), 'er_sample_name')

            try:
                data_er_samples = self.read_magic_file(
                    os.path.join(self.WD, "er_samples.txt"), 'er_sample_name')
            except:
                print("-W- Can't find er_sample.txt in project directory")

            try:
                data_er_sites = self.read_magic_file(
                    os.path.join(self.WD, "er_sites.txt"), 'er_site_name')
            except:
                print("-W- Can't find er_sites.txt in project directory")

            try:
                data_er_locations = self.read_magic_file(os.path.join(
                    self.WD, "er_locations.txt"), 'er_location_name')
            except:
                print("-W- Can't find er_locations.txt in project directory")

            try:
                data_er_ages = self.read_magic_file(
                    os.path.join(self.WD, "er_ages.txt"), 'er_sample_name')
            except:
                try:
                    data_er_ages = self.read_magic_file(
                        os.path.join(self.WD, "er_ages.txt"), 'er_site_name')
                except:
                    print("-W- Can't find er_ages in project directory")

        Data_info["er_samples"] = data_er_samples
        Data_info["er_sites"] = data_er_sites
        Data_info["er_locations"] = data_er_locations
        Data_info["er_ages"] = data_er_ages

        return(Data_info)

    def get_preferences(self):
        """
        Gets preferences for certain display variables from
        zeq_gui_preferences.
        """
        # default
        preferences = {}
        preferences['gui_resolution'] = 100.
        preferences['show_Zij_treatments'] = True
        preferences['show_Zij_treatments_steps'] = 2.
        preferences['show_eqarea_treatments'] = False
        preferences['auto_save'] = True
        # preferences['show_statistics_on_gui']=["int_n","int_ptrm_n","frac","scat","gmax","b_beta","int_mad","dang","f","fvds","g","q","drats"]#,'ptrms_dec','ptrms_inc','ptrms_mad','ptrms_angle']
        #
        # try to read preferences file:
        #user_data_dir = find_pmag_dir.find_user_data_dir("demag_gui")
        # if not user_data_dir:
        #    return preferences
        # if os.path.exists(user_data_dir):
        #    pref_file = os.path.join(user_data_dir, "demag_gui_preferences.json")
        #    if os.path.exists(pref_file):
        #        with open(pref_file, "r") as pfile:
        #            return json.load(pfile)
        return preferences

    def read_magic_file(self, path, sort_by_this_name):
        """
        reads a magic formated data file from path and sorts the keys
        according to sort_by_this_name

        Parameters
        ----------
        path : path to file to read
        sort_by_this_name : variable to sort data by
        """
        DATA = {}
        try:
            with open(path, 'r') as finput:
                lines = list(finput.readlines()[1:])
        except FileNotFoundError:
            return []
        # fin=open(path,'r')
        # fin.readline()
        line = lines[0]
        header = line.strip('\n').split('\t')
        error_strings = []
        for line in lines[1:]:
            tmp_data = {}
            tmp_line = line.strip('\n').split('\t')
            for i in range(len(tmp_line)):
                tmp_data[header[i]] = tmp_line[i]
            if tmp_data[sort_by_this_name] in list(DATA.keys()):
                error_string = "-E- ERROR: magic file %s has more than one line for %s %s" % (
                    path, sort_by_this_name, tmp_data[sort_by_this_name])
                # only print each error message once
                if error_string not in error_strings:
                    print(error_string)
                    error_strings.append(error_string)
            DATA[tmp_data[sort_by_this_name]] = tmp_data
        # fin.close()
        finput.close()
        return(DATA)

    def read_from_LSQ(self, LSQ_file):
        """
        Clears all current interpretations and replaces them with
        interpretations read from LSQ file.

        Parameters
        ----------
        LSQ_file : path to LSQ file to read in
        """
        cont = self.user_warning(
            "LSQ import only works if all measurements are present and not averaged during import from magnetometer files to magic format. Do you wish to continue reading interpretations?")
        if not cont:
            return
        self.clear_interpretations(
            message="""Do you wish to clear all previous interpretations on import?""")
        old_s = self.s
        for specimen in self.specimens:
            self.select_specimen(specimen)
            for i in range(len(self.Data[specimen]['zijdblock'])):
                self.mark_meas_good(i)
        self.select_specimen(old_s)
        print("Reading LSQ file")
        interps = read_LSQ(LSQ_file)
        for interp in interps:
            specimen = interp['er_specimen_name']
            if specimen not in self.specimens:
                print(
                    ("specimen %s has no registered measurement data, skipping interpretation import" % specimen))
                continue
            PCA_type = interp['magic_method_codes'].split(':')[0]
            tmin = self.Data[specimen]['zijdblock_steps'][interp['measurement_min_index']]
            tmax = self.Data[specimen]['zijdblock_steps'][interp['measurement_max_index']]
            if 'specimen_comp_name' in list(interp.keys()):
                name = interp['specimen_comp_name']
            else:
                name = None
            new_fit = self.add_fit(specimen, name, tmin, tmax, PCA_type)
            if 'bad_measurement_index' in list(interp.keys()):
                old_s = self.s
                self.select_specimen(specimen)
                for bmi in interp["bad_measurement_index"]:
                    try:
                        self.mark_meas_bad(bmi)
                    except IndexError:
                        print(
                            "Magic Measurments length does not match that recorded in LSQ file")
                self.select_specimen(old_s)
        if self.ie_open:
            self.ie.update_editor()
        self.update_selection()

    def read_redo_file(self, redo_file):
        """
        Reads a .redo formated file and replaces all current interpretations
        with interpretations taken from the .redo file

        Parameters
        ----------
        redo_file : path to .redo file to read
        """
        if not self.clear_interpretations():
            return
        print("-I- read redo file and processing new bounds")
        fin = open(redo_file, 'r')

        new_s = ""
        for Line in fin.read().splitlines():
            line = Line.split('\t')
            specimen = line[0]
            if specimen.startswith("current_"):
                specimen = specimen.lstrip("current_")
                new_s = specimen
                if len(line) < 6:
                    continue

            if len(line) < 6:
                print(("insuffecent data for specimen %s and fit %s" %
                       (line[0], line[4])))
                continue
            if len(line) == 6:
                line.append('g')
            if specimen not in self.specimens:
                print(
                    ("specimen %s not found in this data set and will be ignored" % (specimen)))
                continue

            tmin, tmax = self.parse_bound_data(line[2], line[3], specimen)
            new_fit = self.add_fit(
                specimen, line[4], tmin, tmax, line[1], line[5])

            if line[6] == 'b' and new_fit != None:
                self.bad_fits.append(new_fit)

        fin.close()

        if new_s != "":
            self.select_specimen(new_s)
        if (self.s not in self.pmag_results_data['specimens']) or (not self.pmag_results_data['specimens'][self.s]):
            self.current_fit = None
        else:
            self.current_fit = self.pmag_results_data['specimens'][self.s][-1]
        self.calculate_high_levels_data()
        if self.ie_open:
            self.ie.update_editor()
        self.update_selection()

    def change_WD(self, new_WD, meas_file=""):
        """
        Changes Demag GUI's current WD to new_WD if possible

        Parameters
        ----------
        new_WD : WD to change to current GUI's WD
        """
        new_WD = os.path.abspath(new_WD)
        if not os.path.isdir(new_WD):
            return
        self.WD = new_WD
        if not meas_file:
            if self.data_model == None:
                if os.path.isfile(os.path.join(self.WD, "measurements.txt")) and os.path.isfile(os.path.join(self.WD, "magic_measurements.txt")):
                    ui_dialog = demag_dialogs.user_input(self, ['data_model'], parse_funcs=[
                                                         float], heading="More than one measurement file found in CWD with different data models please input prefered data model (2.5,3.0)", values=[3])
                    self.show_dlg(ui_dialog)
                    ui_data = ui_dialog.get_values()
                    self.data_model = ui_data[1]['data_model']
                elif os.path.isfile(os.path.join(self.WD, "measurements.txt")):
                    self.data_model = 3.0
                elif os.path.isfile(os.path.join(self.WD, "magic_measurements.txt")):
                    self.data_model = 2.5
                else:
                    self.user_warning(
                        "No measurement file found in chosen directory")
                    self.data_model = 3
            try:
                self.data_model = float(self.data_model)
                if int(self.data_model) == 3:
                    meas_file = os.path.join(self.WD, "measurements.txt")
                elif int(self.data_model) == 2:
                    meas_file = os.path.join(self.WD, "magic_measurements.txt")
                else:
                    meas_file = ''
                    self.data_model = 3
            except (ValueError, TypeError) as e:
                self.user_warning(
                    "Provided data model is unrecognized or invalid, assuming you want data model 3")
                self.data_model = 3

        if os.path.isfile(meas_file):
            self.magic_file = meas_file
        else:
            self.magic_file = self.choose_meas_file()

        if not self.data_model:
            self.data_model = 3

    #---------------------------------------------#
    # Data Writing Functions
    #---------------------------------------------#

    def init_log_file(self):
        """
        redirects stdout to a log file to prevent printing to a hanging
        terminal when dealing with the compiled binary.
        """
        # redirect terminal output
        self.old_stdout = sys.stdout
        sys.stdout = open(os.path.join(self.WD, "demag_gui.log"), 'w+')

    def close_log_file(self):
        """
        if log file has been opened and you wish to stop printing to file
        but back to terminal this function redirects stdout back to
        origional output.
        """
        try:
            sys.stdout = self.old_stdout
        except AttributeError:
            print("Log file was never opened it cannot be closed")

    def update_pmag_tables(self):
        """
        Reads pmag tables from data model 2.5 and updates them with updates
        their data
        """
        pmag_specimens, pmag_samples, pmag_sites = [], [], []
        print("-I- Reading previous interpretations from specimen/sample/site tables")
        try:
            pmag_specimens, file_type = pmag.magic_read(
                os.path.join(self.WD, "pmag_specimens.txt"))
        except:
            print("-I- Can't read pmag_specimens.txt")
        try:
            pmag_samples, file_type = pmag.magic_read(
                os.path.join(self.WD, "pmag_samples.txt"))
        except:
            print("-I- Can't read pmag_samples.txt")
        try:
            pmag_sites, file_type = pmag.magic_read(
                os.path.join(self.WD, "pmag_sites.txt"))
        except:
            print("-I- Can't read pmag_sites.txt")
        # --------------------------
        # reads pmag_specimens.txt and
        # update pmag_results_data['specimens'][specimen]
        # with the new interpretation
        # --------------------------

        if self.COORDINATE_SYSTEM == 'geographic':
            current_tilt_correction = 0
        elif self.COORDINATE_SYSTEM == 'tilt-corrected':
            current_tilt_correction = 100
        else:
            current_tilt_correction = -1

        if 'specimens' not in list(self.pmag_results_data.keys()):
            self.pmag_results_data['specimens'] = {}
        for rec in pmag_specimens:
            if 'er_specimen_name' in rec:
                specimen = rec['er_specimen_name']
            else:
                continue

            # initialize list of interpretations
            if specimen not in list(self.pmag_results_data['specimens'].keys()):
                self.pmag_results_data['specimens'][specimen] = []

            if any(k not in list(rec.keys()) for k in ['measurement_step_min', 'measurement_step_max']):
                continue

            methods = rec['magic_method_codes'].strip(
                "\n").replace(" ", "").split(":")
            LPDIR = False
            calculation_type = ""

            for method in methods:
                if "LP-DIR" in method:
                    LPDIR = True
                if "DE-" in method:
                    calculation_type = method

            msu = ''
            if 'measurement_step_unit' in list(rec.keys()):
                msu = rec['measurement_step_unit']

            # if interpretation doesn't exsist create it.
            if float(rec['measurement_step_min']) == 0. or float(rec['measurement_step_min']) == 273.:
                tmin = "0"
            elif msu == 'K' or float(rec['measurement_step_min']) > 3.:  # thermal
                tmin = "%.0fC" % (float(rec['measurement_step_min'])-273.)
            else:  # AF
                tmin = "%.1fmT" % (float(rec['measurement_step_min'])*1000.)

            if float(rec['measurement_step_max']) == 0. or float(rec['measurement_step_max']) == 273.:
                tmax = "0"
            elif msu == 'K' or float(rec['measurement_step_max']) > 3.:  # thermal
                tmax = "%.0fC" % (float(rec['measurement_step_max'])-273.)
            else:  # AF
                tmax = "%.1fmT" % (float(rec['measurement_step_max'])*1000.)

            if 'specimen_comp_name' in list(rec.keys()):
                fname = rec['specimen_comp_name']
            else:
                fname = None
            if calculation_type == "":
                calculation_type = "DE-BFL"

            if (tmin, tmax) in [(f.tmin, f.tmax) for f in self.pmag_results_data['specimens'][specimen]] and calculation_type in [f.PCA_type for f in self.pmag_results_data['specimens'][specimen]]:
                fit = None
            else:
                fit = self.add_fit(specimen, fname, tmin,
                                   tmax, calculation_type)

            if 'specimen_flag' in list(rec.keys()) and rec['specimen_flag'] == 'b':
                self.bad_fits.append(fit)

        # BUG FIX-almost replaced first sample with last due to above assignment to self.s
        if self.specimens:
            self.select_specimen(self.specimens[0])
            self.specimens_box.SetSelection(0)
        if self.s in self.pmag_results_data['specimens'] and self.pmag_results_data['specimens'][self.s]:
            self.initialize_CART_rot(self.specimens[0])
            self.pmag_results_data['specimens'][self.s][-1].select()

        # --------------------------
        # reads pmag_sample.txt and
        # if finds a mean in pmag_samples.txt
        # calculate the mean for self.high_level_means['samples'][samples]
        # If the program finds a codes "DE-FM","DE-FM-LP","DE-FM-UV"in magic_method_codes
        # then the program repeat teh fisher mean
        # --------------------------

        for rec in pmag_samples:
            if "magic_method_codes" in list(rec.keys()):
                methods = rec['magic_method_codes'].strip(
                    "\n").replace(" ", "").split(":")

            else:
                methods = ""
            sample = rec['er_sample_name'].strip("\n")
            LPDIR = False
            calculation_method = ""
            for method in methods:
                if "LP-DIR" in method:
                    LPDIR = True
                if "DE-" in method:
                    calculation_method = method
            if LPDIR:  # this a mean of directions
                calculation_type = "Fisher"
                for dirtype in self.dirtypes:
                    self.calculate_high_level_mean(
                        'samples', sample, calculation_type, 'specimens', self.mean_fit)

        # --------------------------
        # reads pmag_sites.txt and
        # if finds a mean in pmag_sites.txt
        # calculate the mean for self.high_level_means['sites'][site]
        # using specimens or samples, depends on the er_specimen_names or er_samples_names
        #  The program repeat the fisher calculation and oevrwrites it
        # --------------------------

        for rec in pmag_sites:
            methods = rec['magic_method_codes'].strip(
                "\n").replace(" ", "").split(":")
            site = rec['er_site_name'].strip("\n")
            LPDIR = False
            calculation_method = ""
            elements_type = "specimens"
            for method in methods:
                if "LP-DIR" in method or "DA-DIR" in method or "DE-FM" in method:
                    LPDIR = True
                if "DE-" in method:
                    calculation_method = method
            if LPDIR:  # this a mean of directions
                if calculation_method in ["DE-BS"]:
                    calculation_type = "Bingham"
                else:
                    calculation_type = "Fisher"
                if 'er_sample_names' in list(rec.keys()) and len(rec['er_sample_names'].strip('\n').replace(" ", "").split(":")) > 0:
                    elements_type = 'samples'
                if 'er_specimen_names' in list(rec.keys()) and len(rec['er_specimen_names'].strip('\n').replace(" ", "").split(":")) > 0:
                    elements_type = 'specimens'
                self.calculate_high_level_mean(
                    'sites', site, calculation_type, elements_type, self.mean_fit)

    def write_acceptance_criteria_to_file(self):
        """
        Writes current GUI acceptance criteria to criteria.txt or
        pmag_criteria.txt depending on data model
        """
        crit_list = list(self.acceptance_criteria.keys())
        crit_list.sort()
        rec = {}
        rec['pmag_criteria_code'] = "ACCEPT"
        # rec['criteria_definition']=""
        rec['criteria_definition'] = "acceptance criteria for study"
        rec['er_citation_names'] = "This study"

        for crit in crit_list:
            if type(self.acceptance_criteria[crit]['value']) == str:
                if self.acceptance_criteria[crit]['value'] != "-999" and self.acceptance_criteria[crit]['value'] != "":
                    rec[crit] = self.acceptance_criteria[crit]['value']
            elif type(self.acceptance_criteria[crit]['value']) == int:
                if self.acceptance_criteria[crit]['value'] != -999:
                    rec[crit] = "%.i" % (
                        self.acceptance_criteria[crit]['value'])
            elif type(self.acceptance_criteria[crit]['value']) == float:
                if float(self.acceptance_criteria[crit]['value']) == -999:
                    continue
                decimal_points = self.acceptance_criteria[crit]['decimal_points']
                if decimal_points != -999:
                    command = "rec[crit]='%%.%sf'%%(self.acceptance_criteria[crit]['value'])" % (
                        decimal_points)
                    exec(command)
                else:
                    rec[crit] = "%e" % (
                        self.acceptance_criteria[crit]['value'])
        pmag.magic_write(os.path.join(self.WD, "pmag_criteria.txt"), [
                         rec], "pmag_criteria")

#==========================================================================================#
#============================Internal Dialog Functions======================================#
#==========================================================================================#

    def show_dlg(self, dlg):
        """
        Abstraction function that is to be used instead of dlg.ShowModal

        Parameters
        ----------
        dlg : dialog to ShowModal if possible
        """
        if not self.test_mode:
            dlg.Center()
            return dlg.ShowModal()
        else:
            return dlg.GetAffirmativeId()

    def get_DIR(self):
        """
        Dialog that allows user to choose a working directory
        """
        dlg = wx.DirDialog(self, "Choose a directory:", defaultPath=self.currentDirectory,
                           style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON | wx.DD_CHANGE_DIR)
        ok = self.show_dlg(dlg)
        if ok == wx.ID_OK:
            new_WD = dlg.GetPath()
            dlg.Destroy()
        else:
            new_WD = os.getcwd()
            dlg.Destroy()
        return new_WD

    def choose_meas_file(self, event=None):
        """
        Opens a dialog allowing the user to pick a measurement file
        """
        dlg = wx.FileDialog(
            self, message="Please choose a measurement file",
            defaultDir=self.WD,
            defaultFile="measurements.txt",
            wildcard="measurement files (*.magic,*.txt)|*.magic;*.txt",
            style=wx.FD_OPEN | wx.FD_CHANGE_DIR
        )
        if self.show_dlg(dlg) == wx.ID_OK:
            meas_file = dlg.GetPath()
            dlg.Destroy()
        else:
            meas_file = ''
            self.data_model = 2.5
            dlg.Destroy()
        return meas_file

    def saved_dlg(self, message, caption='Saved:'):
        """
        Shows a dialog that tells the user that a file has been saved

        Parameters
        ----------
        message : message to display to user
        caption : title for dialog (default: "Saved:")
        """
        dlg = wx.MessageDialog(self, caption=caption,
                               message=message, style=wx.OK)
        result = self.show_dlg(dlg)
        dlg.Destroy()

    def user_warning(self, message, caption='Warning!'):
        """
        Shows a dialog that warns the user about some action

        Parameters
        ----------
        message : message to display to user
        caption : title for dialog (default: "Warning!")

        Returns
        -------
        continue_bool : True or False
        """
        dlg = wx.MessageDialog(self, message, caption,
                               wx.OK | wx.CANCEL | wx.ICON_WARNING)
        if self.show_dlg(dlg) == wx.ID_OK:
            continue_bool = True
        else:
            continue_bool = False
        dlg.Destroy()
        return continue_bool

    def data_loss_warning(self):
        """
        Convenience function that displays a generic data loss warning dialog
        """
        TEXT = "This action could result in a loss of all unsaved data. Would you like to continue"
        return self.user_warning(TEXT)

    def on_close_criteria_box(self, dia):
        """
        Function called on close of change acceptance criteria dialog that
        writes new criteria to the hardrive and sets new criteria as GUI's
        current criteria.

        Parameters
        ----------
        dia : closed change criteria dialog
        """
        window_list_specimens = [
            'specimen_n', 'specimen_mad', 'specimen_dang', 'specimen_alpha95']
        window_list_samples = ['sample_n', 'sample_n_lines',
                               'sample_n_planes', 'sample_k', 'sample_r', 'sample_alpha95']
        window_list_sites = ['site_n', 'site_n_lines',
                             'site_n_planes', 'site_k', 'site_r', 'site_alpha95']
        demag_gui_supported_criteria = window_list_specimens + \
            window_list_samples+window_list_sites

        if self.data_model == 3:
            new_crits = []
            for crit in demag_gui_supported_criteria:
                new_crit = {}
                command = "dia.set_%s.GetValue()" % (crit)
                new_value = pmag.execute(command, dia=dia)
                if new_value == None or new_value == '':
                    continue
                d = findall(r"[-+]?\d*\.\d+|\d+", new_value)
                if len(d) > 0:
                    d = d[0]
                comp = new_value.strip(str(d))
                if comp == '':
                    comp = '>='
                if 'specimen' in crit:
                    col = "specimens."+map_magic.spec_magic2_2_magic3_map[crit]
                elif 'sample' in crit:
                    col = "samples."+map_magic.samp_magic2_2_magic3_map[crit]
                elif 'site' in crit:
                    col = "sites."+map_magic.site_magic2_2_magic3_map[crit]
                else:
                    print("no way this like is impossible")
                    continue
                new_crit['criterion'] = "ACCEPT"
                new_crit['criterion_value'] = d
                new_crit['criterion_operation'] = comp
                new_crit['table_column'] = col
                new_crit['citations'] = "This study"
                new_crit['description'] = ''
                new_crits.append(new_crit)
            cdf = DataFrame(new_crits)
            cdf = cdf.set_index("table_column")
            cdf["table_column"] = cdf.index
            #cdf = cdf.reindex_axis(sorted(cdf.columns), axis=1)
            cdf = cdf.reindex(sorted(cdf.columns), axis=1) # reindex_axis is gone
            if 'criteria' not in self.con.tables:
                cols = ['criterion', 'criterion_value', 'criterion_operation',
                        'table_column', 'citations', 'description']
                self.con.add_empty_magic_table('criteria', col_names=cols)
            self.con.tables['criteria'].df = cdf
            self.con.tables['criteria'].write_magic_file(dir_path=self.WD)
        else:
            for crit in demag_gui_supported_criteria:
                command = "new_value=dia.set_%s.GetValue()" % (crit)
                exec(command)
                # empty box
                if new_value == "":
                    self.acceptance_criteria[crit]['value'] = -999
                    continue
                # box with no valid number
                try:
                    float(new_value)
                except:
                    self.show_crit_window_err_messege(crit)
                    continue
                self.acceptance_criteria[crit]['value'] = float(new_value)

            #  message dialog
            self.saved_dlg(message="changes saved to criteria")
            self.write_acceptance_criteria_to_file()
            dia.Destroy()

    def show_crit_window_err_messege(self, crit):
        """
        error message if a valid naumber is not entered to criteria dialog
        boxes
        """
        dlg = wx.MessageDialog(
            self, caption="Error:", message="not a vaild value for statistic %s\n ignoring value" % crit, style=wx.OK)
        result = self.show_dlg(dlg)
        if result == wx.ID_OK:
            dlg.Destroy()

    def On_close_MagIC_dialog(self, dia):
        """
        Function called after save high level pmag table dialog. It
        calculates VGPs, high level means, and saves them the hard drive.

        Parameters
        ----------
        dia : save higher level pmag tables
        """

        def add_missing_ages(df):
            """
            Take a dataframe and add min/max age, age, age_sigma, age_units.
            Use values gained from dialog, but don't overwrite values already
            in the dataframe.
            """
            age_columns = df.columns[df.columns.str.startswith('age')]
            for col, value in {'age_high': max_age, 'age_low': min_age,
                            'age': age, 'age_sigma': age_sigma, 'age_unit': age_units}.items():
                if cb.not_null(value):
                    if col in age_columns:
                        df[col] = np.where(df[col].apply(cb.not_null), df[col], value)
                    else:
                        df[col] = value
            return df


        if dia.cb_acceptance_criteria.GetValue():
            use_criteria = 'existing'
        else:
            use_criteria = 'none'

        # -- coordinate system
        if dia.rb_spec_coor.GetValue():
            coord = "s"
        elif dia.rb_geo_coor.GetValue():
            coord = "g"
        elif dia.rb_tilt_coor.GetValue():
            coord = "t"
        elif dia.rb_geo_tilt_coor.GetValue():
            coord = "b"
        else:
            coord = "s"

        # -- default age options
        DefaultAge = ["none"]
        add_ages = dia.add_ages.GetValue()
        if add_ages:
            age_units = dia.default_age_unit.GetValue()
            min_age = dia.default_age_min.GetValue()
            max_age = dia.default_age_max.GetValue()
            age = dia.default_age.GetValue()
            age_sigma = dia.default_age_sigma.GetValue()
            if (min_age and max_age) or age:
                # enough age data provided
                pass
            else:
                go_on = self.user_warning("Not enough age data provided (you must provide lower and upper bound, or age).\nPress OK to skip ages for now, or cancel to end this process.")
                if not go_on:
                    self.user_warning("Aborting, please try again.", caption="Message")
                    return
                add_ages = False

            if min_age and max_age:
                DefaultAge = [min_age, max_age, age_units]

        # -- sample mean
        avg_directions_by_sample = False
        if dia.cb_sample_mean.GetValue():
            avg_directions_by_sample = True

        vgps_level = 'site'
        if dia.cb_sample_mean_VGP.GetValue():
            vgps_level = 'sample'

        # -- site mean

        if dia.cb_site_mean.GetValue():
            pass

        # -- location mean
        avg_by_polarity = False
        if dia.cb_location_mean.GetValue():
            avg_by_polarity = True

        if self.data_model == 3.0:
            # update or add age data to the sites table, but don't overwrite existing data
            if add_ages:
                site_df = self.con.tables['sites'].df
                self.con.tables['sites'].df = add_missing_ages(site_df)
                self.con.write_table_to_file("sites")

            # set some variables
            priorities = ['DA-AC-ARM', 'DA-AC-TRM']
            for p in priorities:
                if not p.startswith('DA-AC-'):
                    p = 'DA-AC-'+p
            # translate coord into coords
            if coord == 's':
                coords = ['-1']
            elif coord == 'g':
                coords = ['0']
            elif coord == 't':
                coords = ['100']
            elif coord == 'b':
                coords = ['0', '100']
            else:
                coords = ['-1']

            if vgps_level == 'sample':
                vgps = 1  # save sample level VGPS/VADMs
            else:
                vgps = 0  # site level

            nositeints = 0
            version_num = pmag.get_version()
            get_model_lat = 0  # skips VADM calculation entirely
            Dcrit, Icrit, nocrit = 0, 0, 0  # default criteria input

            # still broken (needs translation or determination of translation necessity)
            if use_criteria == 'none':
                Dcrit, Icrit, nocrit = 1, 1, 1  # no selection criteria
                crit_data = pmag.default_criteria(nocrit)
            elif use_criteria == 'existing':
                crit_data = self.read_criteria_file()
                if crit_data == None:
                    crit_data = pmag.default_criteria(nocrit)
                    print(
                        "No acceptance criteria found in criteria.txt defualt PmagPy criteria used instead")
                else:
                    print("Acceptance criteria from criteria.txt used")
            else:
                # use default criteria
                crit_data = pmag.default_criteria(nocrit)
                print("PmagPy default criteria used")

            accept = {}
            for critrec in crit_data:
                if type(critrec) != dict:
                    continue
                for key in list(critrec.keys()):
                    # need to migrate specimen_dang to specimen_int_dang for intensity data using old format
                    if 'IE-SPEC' in list(critrec.keys()) and 'specimen_dang' in list(critrec.keys()) and 'specimen_int_dang' not in list(critrec.keys()):
                        critrec['specimen_int_dang'] = critrec['specimen_dang']
                        del critrec['specimen_dang']
                    # need to get rid of ron shaars sample_int_sigma_uT
                    if 'sample_int_sigma_uT' in list(critrec.keys()):
                        critrec['sample_int_sigma'] = '%10.3e' % (
                            eval(critrec['sample_int_sigma_uT'])*1e-6)
                    if key not in list(accept.keys()) and critrec[key] != '':
                        accept[key] = critrec[key]

            if use_criteria == 'default':
                pmag.magic_write(critout, [accept], 'pmag_criteria')
                print("\n Pmag Criteria stored in ", critout, '\n')

            if 'specimens' not in self.con.tables:
                self.user_warning(
                    "No specimen interpretations found in the current contribution samples, sites, and locations cannot be exported, aborting")
                return
            spec_df = self.con.tables['specimens'].df
            if 'sites' not in self.con.tables:
                self.con.add_empty_magic_table('sites')
            site_df = self.con.tables['sites'].df
            SiteNFO = site_df.to_dict("records")
            Data = spec_df.to_dict("records")

            comment = ""
            orient = list(spec_df[spec_df['dir_tilt_correction'].notnull(
            )]['dir_tilt_correction'].drop_duplicates())
            samples = sorted(list(spec_df['sample'].dropna().drop_duplicates()))
            sites = sorted(list(spec_df['site'].dropna().drop_duplicates()))
            locations = sorted(list(spec_df['location'].dropna().drop_duplicates()))
            Comps = sorted(
                list(spec_df[spec_df['dir_comp'].notnull()]['dir_comp'].drop_duplicates()))
            Comps = [c for c in Comps if type(c) == str]
            # find all the sites with height info.
            height_info = pmag.get_dictitem(SiteNFO, 'height', '', 'F')

            nocorrection = ['DA-NL', 'DA-AC', 'DA-CR']
            SpecInts = []
            # retrieve specimens with intensity data
            IntData = pmag.get_dictitem(Data, 'int_abs', '', 'F')
            if nocrit == 0:  # use selection criteria
                for rec in IntData:  # do selection criteria
                    kill = pmag.grade(
                        rec, accept, 'specimen_int', data_model=3.0)
                    if len(kill) == 0:
                        # intensity record to be included in sample, site calculations
                        SpecInts.append(rec)
            else:
                # take everything - no selection criteria
                SpecInts = IntData[:]
            # check for required data adjustments
            if len(nocorrection) > 0 and len(SpecInts) > 0:
                for cor in nocorrection:
                    # exclude the corrections not specified for inclusion
                    SpecInts = pmag.get_dictitem(
                        SpecInts, 'method_codes', cor, 'not')
            # take top priority specimen of its name in remaining specimens (only one per customer)
            PrioritySpecInts = []
            # get list of uniq specimen names
            specimens = pmag.get_specs(SpecInts)
            for spec in specimens:
                # all the records for this specimen
                ThisSpecRecs = pmag.get_dictitem(
                    SpecInts, 'specimen', spec, 'T')
                if len(ThisSpecRecs) == 1:
                    PrioritySpecInts.append(ThisSpecRecs[0])
                elif len(ThisSpecRecs) > 1:  # more than one
                    prec = []
                    for p in priorities:
                        # all the records for this specimen
                        ThisSpecRecs = pmag.get_dictitem(
                            SpecInts, 'method_codes', p, 'has')
                        if len(ThisSpecRecs) > 0:
                            prec.append(ThisSpecRecs[0])
                            PrioritySpecInts.append(
                                prec[0])  # take the best one
            SpecInts = PrioritySpecInts  # this has the first specimen record

            # apply criteria to directional data
            # retrieve specimens with directed lines and planes and some measuremnt data
            Ns = spec_df[spec_df['dir_n_measurements']
                         != ''].to_dict("records")
            SpecDirs = []
            if nocrit != 1:  # use selection criteria
                for rec in Ns:  # look through everything with specimen_n for "good" data
                    kill = pmag.grade(
                        rec, accept, 'specimen_dir', data_model=3.0)
                    if len(kill) == 0:  # nothing killed it
                        SpecDirs.append(rec)
            else:  # no criteria
                SpecDirs = Ns[:]  # take them all

            # list of all sample data and list of those that pass the DE-SAMP criteria
            PmagSamps, SampDirs = [], []
            PmagSites = []  # list of all site data
            SampInts = []
            renamelnp = {'R': 'dir_r', 'n': 'dir_n_samples', 'n_total': 'dir_n_specimens', 'alpha95': 'dir_alpha95',
                         'n_lines': 'dir_n_specimens_lines', 'K': 'dir_k', 'dec': 'dir_dec', 'n_planes': 'dir_n_specimens_planes', 'inc': 'dir_inc'}
            for samp in samples:  # run through the sample names
                if not avg_directions_by_sample:
                    break
                # get all the directional data for this sample
                SampDir = pmag.get_dictitem(SpecDirs, 'sample', samp, 'T')
                if len(SampDir) <= 0:
                    continue  # if no directions
                for coord in coords:  # step through desired coordinate systems
                    # get all the directions for this sample
                    CoordDir = pmag.get_dictitem(
                        SampDir, 'dir_tilt_correction', coord, 'T')
                    if len(CoordDir) <= 0:
                        continue  # no data for this coordinate system
                    for comp in Comps:
                        # get all directions from this component
                        CompDir = pmag.get_dictitem(
                            CoordDir, 'dir_comp', comp, 'T')
                        CompDir = [
                            x for x in CompDir if 'result_quality' in x and x['result_quality'] == 'g']
                        if len(CompDir) <= 0:
                            continue  # no data for comp
                        PmagSampRec = pmag.dolnp3_0(CompDir)
                        for k, v in list(renamelnp.items()):
                            if k in PmagSampRec:
                                PmagSampRec[v] = PmagSampRec[k]
                                del PmagSampRec[k]
                        # decorate the sample record
                        PmagSampRec["location"] = CompDir[0]['location']
                        PmagSampRec["site"] = CompDir[0]['site']
                        PmagSampRec["sample"] = samp
                        PmagSampRec["citations"] = "This study"
                        PmagSampRec['software_packages'] = version_num + \
                            ': demag_gui.v.3.0'
                        if CompDir[0]['result_quality'] == 'g':
                            PmagSampRec['result_quality'] = 'g'
                        else:
                            PmagSampRec['result_quality'] = 'b'
                        if nocrit != 1:
                            PmagSampRec['criteria'] = "ACCEPT"
                        site_height = pmag.get_dictitem(
                            height_info, 'site', PmagSampRec['site'], 'T')
                        if len(site_height) > 0:
                            # add in height if available
                            PmagSampRec["height"] = site_height[0]['height']
                        PmagSampRec['dir_comp_name'] = comp
                        PmagSampRec['dir_tilt_correction'] = coord
                        specs = [d['specimen'] for d in CompDir]
                        if 'dir_n_specimens' not in PmagSampRec:
                            PmagSampRec['dir_n_specimens'] = len(specs)
                        # get a list of the specimen names used
                        PmagSampRec['specimens'] = reduce(
                            lambda x, y: str(x)+':'+str(y), specs)
                        # get old method codes
                        prev_meth_codes = self.con.tables['samples'].df.loc[samp]['method_codes']
                        # get a list of the methods used
                        new_meth_codes = pmag.get_list(CompDir, 'method_codes')
                        if isinstance(prev_meth_codes, Series):
                            merged_meths = self.merge_meth_codes(
                                prev_meth_codes.iloc[0], new_meth_codes)
                        else:
                            merged_meths = self.merge_meth_codes(
                                prev_meth_codes, new_meth_codes)
                        PmagSampRec['method_codes'] = merged_meths
                        if nocrit != 1:  # apply selection criteria
                            kill = pmag.grade(
                                PmagSampRec, accept, 'sample_dir', data_model=3.0)
                        else:
                            kill = []
                        if len(kill) > 0:
                            PmagSampRec['result_quality'] = 'b'
                        else:
                            SampDirs.append(PmagSampRec)
                        if vgps == 1:  # if sample level VGP info desired, do that now
                            try:
                                PmagResRec = pmag.getsampVGP(
                                    PmagSampRec, SiteNFO, data_model=self.data_model)
                            except KeyError:
                                print(
                                    ("no lat lon data for sample %s skipping VGP calculation" % samp))
                                PmagResRec = ""
                            if PmagResRec != "":
                                for k in ['vgp_dp', 'vgp_dm', 'vgp_lat', 'vgp_lon']:
                                    PmagSampRec[k] = PmagResRec[k]
                        PmagSamps.append(PmagSampRec)

            # removed average_all_components check because demag GUI never averages directional components
            # removed intensity average portion as demag GUI has no need of this also cause translating this is a bitch

            if len(PmagSamps) > 0:
                if 'samples' not in self.con.tables:
                    self.con.add_empty_magic_table('samples')
                for dc in ['magic_method_codes']:
                    if dc in self.con.tables['samples'].df:
                        del self.con.tables['samples'].df[dc]
                samps_df = DataFrame(PmagSamps)
                samps_df = samps_df.set_index('sample')
                samps_df['sample'] = samps_df.index
                nsdf = self.con.tables['samples'].merge_dfs(samps_df)
                if not vgps == 1:
                    nsdf.drop([col for col in nsdf.columns if type(
                        col) == str and col.startswith('vgp')], axis=1, inplace=True)
                #nsdf = nsdf.reindex_axis(sorted(nsdf.columns), axis=1)
                nsdf = nsdf.reindex(sorted(nsdf.columns), axis=1)
                self.con.tables['samples'].df = nsdf
                self.con.tables['samples'].write_magic_file(dir_path=self.WD)

            # create site averages from specimens or samples as specified
            for site in sites:
                for coord in coords:
                    if dia.combo_site_mean.GetValue() == 'samples' and avg_directions_by_sample:
                        # if sample averages at site level desired
                        key, comp_key, dirlist = 'sample', 'dir_comp_name', SampDirs
                    else:
                        # if specimen averages at site level desired
                        key, comp_key, dirlist = 'specimen', 'dir_comp', SpecDirs
                    # get all the sites with  directions
                    tmp = pmag.get_dictitem(dirlist, 'site', site, 'T')
                    tmp1 = pmag.get_dictitem(
                        tmp, 'dir_tilt_correction', coord, 'T', float_to_int=True)
                    # fish out site information (lat/lon, etc.)
                    sd = pmag.get_dictitem(SiteNFO, 'site', site, 'T')
                    if len(sd) <= 0:  # no data for this site
                        print(
                            ('site information not found in sites.txt for site, %s. skipping.' % site))
                        continue
                    for comp in Comps:
                        # get all components comp
                        siteD = pmag.get_dictitem(tmp1, comp_key, comp, 'T')
                        # remove bad data from means
                        siteD = [
                            x for x in siteD if 'result_quality' in x and x['result_quality'] == 'g']
                        if len(siteD) <= 0:
                            # print("no data for comp %s in site %s. skipping"%(comp,site))
                            continue
                        PmagSiteRec = PmagSampRec = pmag.dolnp3_0(
                            siteD)  # get an average for this site
                        for k, v in list(renamelnp.items()):
                            if k in PmagSiteRec:
                                PmagSiteRec[v] = PmagSiteRec[k]
                                del PmagSiteRec[k]
                        # decorate the site record
                        PmagSiteRec['dir_comp_name'] = comp
                        PmagSiteRec["location"] = siteD[0]['location']
                        PmagSiteRec["site"] = siteD[0]['site']
                        PmagSiteRec['dir_tilt_correction'] = coord
                        PmagSiteRec['samples'] = pmag.get_list(siteD, 'sample')
                        if dia.combo_site_mean.GetValue() == 'samples' and avg_directions_by_sample:
                            PmagSiteRec['specimens'] = pmag.get_list(
                                siteD, 'specimens')
                        else:
                            PmagSiteRec['specimens'] = pmag.get_list(
                                siteD, 'specimen')
                        if 'dir_n_samples' not in list(PmagSiteRec.keys()):
                            PmagSiteRec['dir_n_samples'] = len(
                                PmagSiteRec['samples'].split(':'))
                        if 'dir_n_specimens' not in list(PmagSiteRec.keys()):
                            PmagSiteRec['dir_n_specimens'] = len(
                                PmagSiteRec['specimens'].split(':'))
                        # determine the demagnetization code (DC3,4 or 5) for this site
                        AFnum = len(pmag.get_dictitem(
                            siteD, 'method_codes', 'LP-DIR-AF', 'has'))
                        Tnum = len(pmag.get_dictitem(
                            siteD, 'method_codes', 'LP-DIR-T', 'has'))
                        DC = 3
                        if AFnum > 0:
                            DC += 1
                        if Tnum > 0:
                            DC += 1
                        PmagSiteRec['method_codes'] = pmag.get_list(
                            siteD, 'method_codes')+':' + 'LP-DC'+str(DC)
                        PmagSiteRec['method_codes'].strip(":")

                        PmagSiteRec["citations"] = "This study"
                        PmagSiteRec['software_packages'] = version_num + \
                            ': demag_gui.v.3.0'

                        # here we need to grab ages from sites or ages
                        site_age_rec = Series()
                        if 'ages' in self.con.tables:
                            ages_df = self.con.tables['ages'].df
                            if 'site' in ages_df.columns:
                                site_age_records = ages_df[ages_df['site'] == site]
                                if len(site_age_records):
                                    if isinstance(site_age_records, Series):
                                        site_age_rec = site_age_records
                                    else:
                                        site_age_rec = site_age_records.iloc[0]
                        if not len(site_age_rec):
                            sites_df = self.con.tables['sites'].df
                            site_age_records = sites_df.loc[site]
                            if len(site_age_records):
                                if isinstance(site_age_records, Series):
                                    site_age_rec = site_age_records
                                else:
                                    site_age_rec = site_age_records.iloc[0]

                        PmagSiteRec['criteria'] = 'ACCEPT'
                        if 'dir_n_specimens_lines' in list(PmagSiteRec.keys()) and 'dir_n_specimens_planes' in list(PmagSiteRec.keys()) and PmagSiteRec['dir_n_specimens_lines'] != "" and PmagSiteRec['dir_n_specimens_planes'] != "":
                            if int(PmagSiteRec["dir_n_specimens_planes"]) > 0:
                                PmagSiteRec["method_codes"] = PmagSiteRec['method_codes']+":DE-FM-LP"
                            elif int(PmagSiteRec["dir_n_specimens_lines"]) > 2:
                                PmagSiteRec["method_codes"] = PmagSiteRec['method_codes']+":DE-FM"

                        site_height = pmag.get_dictitem(
                            height_info, 'site', site, 'T')
                        if len(site_height) > 0:
                            PmagSiteRec["height"] = site_height[0]['height']
                        if '0' in PmagSiteRec['dir_tilt_correction'] and "DA-DIR-GEO" not in PmagSiteRec['method_codes']:
                            PmagSiteRec['method_codes'] = PmagSiteRec['method_codes']+":DA-DIR-GEO"
                        if '100' in PmagSiteRec['dir_tilt_correction'] and "DA-DIR-TILT" not in PmagSiteRec['method_codes']:
                            PmagSiteRec['method_codes'] = PmagSiteRec['method_codes'] + \
                                ":DA-DIR-TILT"
                        PmagSiteRec['dir_polarity'] = ""
# assign polarity based on angle of pole lat to spin axis - may want to re-think this sometime

                        if dia.cb_site_mean_VGP.GetValue():
                            dec = float(PmagSiteRec["dir_dec"])
                            inc = float(PmagSiteRec["dir_inc"])
                            if 'dir_alpha95' in list(PmagSiteRec.keys()) and PmagSiteRec['dir_alpha95'] != "":
                                a95 = float(PmagSiteRec["dir_alpha95"])
                            else:
                                a95 = 180.
                            # fish out site information (lat/lon, etc.)
                            sitedat = [x for x in pmag.get_dictitem(
                                SiteNFO, 'site', PmagSiteRec['site'], 'T') if x['lat'] != None and x['lon'] != None]
                            if len(sitedat) != 0:
                                sitedat = sitedat[0]
                            else:
                                sitedat = {}
                            try:
                                PmagSiteRec['lat'] = float(sitedat['lat'])
                                PmagSiteRec['lon'] = float(sitedat['lon'])
                                lat, lon = PmagSiteRec['lat'], PmagSiteRec['lon']
                                calculate = True
                            except (KeyError, ValueError, TypeError) as e:
                                calculate = False
                                ui_dialog = demag_dialogs.user_input(self, ['Latitude', 'Longitude'], parse_funcs=[
                                                                     float, float], heading="Missing Latitude or Longitude data for site: %s" % site)
                                self.show_dlg(ui_dialog)
                                ui_data = ui_dialog.get_values()
                                if ui_data[0]:
                                    PmagSiteRec['lat'] = ui_data[1]['Latitude']
                                    PmagSiteRec['lon'] = ui_data[1]['Longitude']
                                    lat, lon = PmagSiteRec['lat'], PmagSiteRec['lon']
                                    calculate = True
                                else:
                                    self.user_warning(
                                        "insuffecent data provided skipping VGP calculation for site %s and comp %s" % (site, comp))
                            if calculate:
                                plong, plat, dp, dm = pmag.dia_vgp(
                                    dec, inc, a95, lat, lon)  # get the VGP for this site
                                PmagSiteRec["vgp_lat"] = '%7.1f ' % (plat)
                                PmagSiteRec["vgp_lon"] = '%7.1f ' % (plong)
                                PmagSiteRec["vgp_dp"] = '%7.1f ' % (dp)
                                PmagSiteRec["vgp_dm"] = '%7.1f ' % (dm)

                                angle = pmag.angle([0, 0], [0, (90-plat)])
                                if angle <= 55.:
                                    PmagSiteRec["dir_polarity"] = 'n'
                                if angle > 55. and angle < 125.:
                                    PmagSiteRec["dir_polarity"] = 't'
                                if angle >= 125.:
                                    PmagSiteRec["dir_polarity"] = 'r'

                        kill = pmag.grade(PmagSiteRec, accept, 'site_dir')
                        if len(kill) > 0:
                            PmagSiteRec['result_quality'] = 'b'
                        else:
                            PmagSiteRec['result_quality'] = 'g'

                        # Carry over data from previous sites
                        prev_dat = pmag.get_dictitem(
                            SiteNFO, 'site', PmagSiteRec['site'], 'T')
                        if len(prev_dat) != 0:
                            for ndd in set(PmagSiteRec.keys()).symmetric_difference(set(prev_dat[0].keys())):
                                sitedat = [
                                    x for x in prev_dat if ndd in x and x[ndd] != None]
                                if len(sitedat) != 0:
                                    sitedat = sitedat[0]
                                else:
                                    continue
                                PmagSiteRec[ndd] = sitedat[ndd]

                        PmagSites.append(PmagSiteRec)

            if len(PmagSites) > 0:
                if 'sites' not in self.con.tables:
                    self.con.tables.add_empty_magic_table('sites')
                sites_df = DataFrame(PmagSites)
                if 'tilt_correction' in sites_df.columns:
                    sites_df.drop('tilt_correction', axis=1, inplace=True)
                sites_df = sites_df.set_index('site')
                sites_df['site'] = sites_df.index
                nsdf = self.con.tables['sites'].merge_dfs(sites_df)
                if not dia.cb_site_mean_VGP.GetValue():
                    nsdf.drop([col for col in nsdf.columns if type(
                        col) == str and col.startswith('vgp')], axis=1, inplace=True)
                #nsdf = nsdf.reindex_axis(sorted(nsdf.columns), axis=1)
                nsdf = nsdf.reindex(sorted(nsdf.columns), axis=1)
                self.con.tables['sites'].df = nsdf
                self.con.tables['sites'].write_magic_file(dir_path=self.WD)

            # location mean section
            PmagLocs = []
            for location in locations:
                if not avg_by_polarity:
                    break
                locrecs = pmag.get_dictitem(
                    PmagSites, 'location', location, 'T')
                if len(locrecs) < 2:
                    print(("no data for location %s" % location))
                    continue
                for coord in coords:
                    # find the tilt corrected data
                    coordrecs = pmag.get_dictitem(
                        locrecs, 'dir_tilt_correction', coord, 'T')
                    if len(coordrecs) < 2:
                        print(
                            ("not enough data of %s percent tilt corrected data in sites to calculate locations mean or vgp" % coord))
                        continue
                    for comp in Comps:
                        # fish out all of the component
                        crecs = pmag.get_dictitem(
                            coordrecs, 'dir_comp_name', comp, 'T')
                        if len(crecs) < 2:
                            print(
                                ("insuffecent data for comp %s when calculating location" % comp))
                            continue
                        precs = []
                        for rec in crecs:
                            prec = {'dec': rec['dir_dec'], 'inc': rec['dir_inc'],
                                    'name': rec['site'], 'loc': rec['location']}
                            prec = {k: v if v != None else 'None' for k,
                                    v in list(prec.items())}
                            precs.append(prec)
                        # calculate average by polarity
                        polpars = pmag.fisher_by_pol(precs)
                        # hunt through all the modes (normal=A, reverse=B, all=ALL)
                        for mode in list(polpars.keys()):
                            PolRes = {}
                            PolRes['citations'] = 'This study'
                            PolRes["result_name"] = "Polarity Average: Polarity "+mode
                            PolRes["pole_comp_name"] = comp+':'+mode
                            PolRes["dir_dec"] = '%7.1f' % (
                                polpars[mode]['dec'])
                            PolRes["dir_inc"] = '%7.1f' % (
                                polpars[mode]['inc'])
                            PolRes["dir_n_sites"] = '%i' % (polpars[mode]['n'])
                            PolRes["dir_r"] = '%5.4f' % (polpars[mode]['r'])
                            PolRes["dir_k"] = '%6.0f' % (polpars[mode]['k'])
                            PolRes["dir_alpha95"] = '%7.1f' % (
                                polpars[mode]['alpha95'])
                            PolRes['sites'] = polpars[mode]['sites']
                            sites_dat = self.con.tables['sites'].df
                            for e in ['samples', 'specimens']:
                                PolRes[e] = reduce(lambda x, y: x+':'+y, [sites_dat.loc[site][e].iloc[0] if isinstance(
                                    sites_dat.loc[site][e], Series) else sites_dat.loc[site][e] for site in PolRes['sites'].split(':')])
                            PolRes['dir_n_samples'] = len(
                                PolRes['samples'].split(':'))
                            PolRes['dir_n_specimens'] = len(
                                PolRes['specimens'].split(':'))
                            PolRes['location'] = polpars[mode]['locs']
                            PolRes['software_packages'] = version_num + \
                                ': demag_gui.v.3.0'
                            PolRes['dir_tilt_correction'] = coord
                            if add_ages:
                                loc_rec = {}
                                if 'locations' in self.con.tables:
                                    locs_df = self.con.tables['locations'].df
                                    self.con.tables['locations'].df = add_missing_ages(locs_df)
                                    loc_recs = locs_df.loc[location]
                                    if len(loc_recs):
                                        if isinstance(loc_recs, Series):
                                            loc_rec = loc_recs
                                        else:
                                            loc_rec = loc_recs.iloc[0]
                                PolRes['age_high'] = loc_rec.get('age_high', max_age)
                                PolRes['age_low'] = loc_rec.get('age_low', min_age)
                                PolRes['age'] = loc_rec.get('age', age)
                                PolRes['age_sigma'] = loc_rec.get('age_sigma', age_sigma)
                                PolRes['age_unit'] = loc_rec.get('age_unit', age_units)
                            if dia.cb_location_mean_VGP.GetValue():
                                sucess_lat_lon_info = True
                                if 'locations' in self.con.tables:
                                    locs_dat = self.con.tables['locations'].df
                                    if 'lat_n' in locs_dat.columns:
                                        lat = locs_dat['lat_n'][location].iloc[0] if isinstance(
                                            locs_dat['lat_n'][location], Series) else locs_dat['lat_n'][location]
                                    elif 'lat_s' in locs_dat.columns:
                                        lat = locs_dat['lat_s'][location].iloc[0] if isinstance(
                                            locs_dat['lat_s'][location], Series) else locs_dat['lat_s'][location]
                                    else:
                                        sucess_lat_lon_info = False
                                    if 'lon_e' in locs_dat.columns:
                                        lon = locs_dat['lon_e'][location].iloc[0] if isinstance(
                                            locs_dat['lon_e'][location], Series) else locs_dat['lon_e'][location]
                                    elif 'lon_w' in locs_dat.columns:
                                        lon = locs_dat['lon_w'][location].iloc[0] if isinstance(
                                            locs_dat['lon_w'][location], Series) else locs_dat['lon_w'][location]
                                    else:
                                        sucess_lat_lon_info = False
                                if not sucess_lat_lon_info:
                                    ui_dialog = demag_dialogs.user_input(self, ['North Boundary Latitude', 'South Boundary Latitude', 'East Boundary Longitude', 'West Boundary Longitude'], parse_funcs=[
                                                                         float, float, float, float], heading="Missing Latitude or Longitude data for location %s please define the boundary of this region so VGP calculations can be preformed" % location)
                                    ui_data = ui_dialog.get_values()
                                    if ui_data[0]:
                                        PolRes['lat_n'] = ui_data[1]['North Boundary Latitude']
                                        PolRes['lat_s'] = ui_data[1]['South Boundary Latitude']
                                        PolRes['lon_e'] = ui_data[1]['East Boundary Longitude']
                                        PolRes['lon_w'] = ui_data[1]['West Boundary Longitude']
                                        lat, lon = PolRes['lat_n'], PolRes['lon_e']
                                        sucess_lat_lon_info = True
                                    else:
                                        self.user_warning(
                                            "insuffecent data provided skipping VGP calculation for location %s" % location)
                                try:
                                    dec, inc, a95, lat, lon = float(polpars[mode]['dec']), float(
                                        polpars[mode]['inc']), float(polpars[mode]['alpha95']), float(lat), float(lon)
                                except (UnboundLocalError, TypeError):
                                    print(
                                        "unable to obtain all data needed for VGP calculation, skipping")
                                    sucess_lat_lon_info = False
                                if sucess_lat_lon_info:
                                    # get the VGP for this pole component
                                    plong, plat, dp, dm = pmag.dia_vgp(
                                        dec, inc, a95, lat, lon)
                                    PolRes["pole_lat"] = '%7.1f ' % (plat)
                                    PolRes["pole_lon"] = '%7.1f ' % (plong)
                                    PolRes["pole_dp"] = '%7.1f ' % (dp)
                                    PolRes["pole_dm"] = '%7.1f ' % (dm)
                                    PolRes["pole_alpha95"] = PolRes['dir_alpha95']
                                    PolRes["pole_r"] = PolRes['dir_r']
                                    PolRes["pole_k"] = PolRes['dir_k']
                                    angle = pmag.angle([0, 0], [0, (90-plat)])
                                    if angle <= 55.:
                                        PolRes["dir_polarity"] = 'n'
                                    if angle > 55. and angle < 125.:
                                        PolRes["dir_polarity"] = 't'
                                    if angle >= 125.:
                                        PolRes["dir_polarity"] = 'r'

                            # fix not duplicating data
                            prev_dat = pmag.get_dictitem(locs_dat.to_dict(
                                'records'), 'location', location, 'T')
                            # merge method codes
                            methods = []
                            for prd in prev_dat:
                                if 'method_codes' not in list(prd.keys()) or prd['method_codes'] == None:
                                    continue
                                for mc in prd['method_codes'].split(':'):
                                    if mc not in methods:
                                        methods.append(mc)
                            if len(methods) > 1:
                                PolRes['method_codes'] = reduce(
                                    lambda x, y: x+':'+y, methods)
                            elif len(methods) > 0:
                                PolRes['method_codes'] = methods[0]
                            else:
                                PolRes['method_codes'] = ''
                            if len(prev_dat) != 0:
                                for ndd in set(PolRes.keys()).symmetric_difference(set(prev_dat[0].keys())):
                                    dat = [
                                        x for x in prev_dat if ndd in x and x[ndd] != None]
                                    if len(dat) != 0:
                                        dat = dat[0]
                                    else:
                                        continue
                                    PolRes[ndd] = dat[ndd]

                            PmagLocs.append(PolRes)

            if len(PmagLocs) > 0:
                locs_df = DataFrame(PmagLocs)
                locs_df = locs_df.set_index('location')
                locs_df['location'] = locs_df.index
                nsdf = self.con.tables['locations'].merge_dfs(locs_df)
                if not dia.cb_location_mean_VGP.GetValue():
                    nsdf.drop([col for col in nsdf.columns if type(col) == str and col.startswith(
                        'pole') and col != 'pol_comp_name'], axis=1, inplace=True)
                #nsdf = nsdf.reindex_axis(sorted(nsdf.columns), axis=1)
                nsdf = nsdf.reindex(sorted(nsdf.columns), axis=1)
                self.con.tables['locations'].df = nsdf
                self.con.tables['locations'].write_magic_file(dir_path=self.WD)

        else:
            for FILE in ['pmag_samples.txt', 'pmag_sites.txt', 'pmag_results.txt']:
                self.PmagRecsOld[FILE] = []
                try:
                    meas_data, file_type = pmag.magic_read(
                        os.path.join(self.WD, FILE))
                    print(("-I- Read old magic file  %s" %
                           os.path.join(self.WD, FILE)))
                    if FILE != 'pmag_specimens.txt':
                        os.remove(os.path.join(self.WD, FILE))
                        print(("-I- Delete old magic file  %s" %
                               os.path.join(self.WD, FILE)))
                except:
                    continue

            for rec in meas_data:
                if "magic_method_codes" in list(rec.keys()):
                    if "LP-DIR" not in rec['magic_method_codes'] and "DE-" not in rec['magic_method_codes']:
                        self.PmagRecsOld[FILE].append(rec)

            print(('coord', coord, 'vgps_level', vgps_level, 'DefaultAge', DefaultAge, 'avg_directions_by_sample',
                   avg_directions_by_sample, 'avg_by_polarity', avg_by_polarity, 'use_criteria', use_criteria))
            prev_cwd = os.getcwd()
            os.chdir(self.WD)
            ipmag.specimens_results_magic(coord=coord, vgps_level=vgps_level, DefaultAge=DefaultAge,
                                          avg_directions_by_sample=avg_directions_by_sample, avg_by_polarity=avg_by_polarity, use_criteria=use_criteria)
            os.chdir(prev_cwd)

            # reads new pmag tables, and merge the old lines:
            for FILE in ['pmag_samples.txt', 'pmag_sites.txt', 'pmag_results.txt']:
                pmag_data = []
                try:
                    pmag_data, file_type = pmag.magic_read(
                        os.path.join(self.WD, FILE))
                except:
                    pass
                if FILE in list(self.PmagRecsOld.keys()):
                    for rec in self.PmagRecsOld[FILE]:
                        pmag_data.append(rec)
                if len(pmag_data) > 0:
                    pmag_data_fixed = self.merge_pmag_recs(pmag_data)
                    pmag.magic_write(os.path.join(self.WD, FILE),
                                     pmag_data_fixed, FILE.split(".")[0])
                    print(("write new interpretations in %s\n" %
                           (os.path.join(self.WD, FILE))))

            # make pmag_criteria.txt if it does not exist
            if not os.path.isfile(os.path.join(self.WD, "pmag_criteria.txt")):
                Fout = open(os.path.join(self.WD, "pmag_criteria.txt"), 'w')
                Fout.write("tab\tpmag_criteria\n")
                Fout.write("er_citation_names\tpmag_criteria_code\n")
                Fout.write("This study\tACCEPT\n")

            self.update_pmag_tables()
            self.update_selection()

        TEXT = "interpretations saved"
        self.saved_dlg(TEXT)
        self.close_warning = False

    def merge_meth_codes(self, meths1, meths2):
        if not isinstance(meths1, str) or not meths1:
            return meths2
        elif not isinstance(meths2, str) or not meths2:
            return meths1
        merged_meths = []
        for meth in meths1.split(':'):
            if meth not in merged_meths:
                merged_meths.append(meth)
        for meth in meths2.split(':'):
            if meth not in merged_meths:
                merged_meths.append(meth)
        if len(merged_meths) > 1:
            return reduce(lambda x, y: x+':'+y, merged_meths)
        elif len(merged_meths) > 0:
            return merged_meths[0]
        else:
            return ''

#==========================================================================================#
#=============================Update Panel Functions=======================================#
#==========================================================================================#

    def update_selection(self):
        """
        Convenience function update display (figures, text boxes and
        statistics windows) with a new selection of specimen
        """

        self.clear_boxes()
        # commented out to allow propogation of higher level viewing state
        self.clear_high_level_pars()

        if self.UPPER_LEVEL_SHOW != "specimens":
            self.mean_type_box.SetValue("None")

        # --------------------------
        # check if the coordinate system in the window exists (if not change to "specimen" coordinate system)
        # --------------------------

        coordinate_system = self.coordinates_box.GetValue()
        if coordinate_system == 'tilt-corrected' and \
           len(self.Data[self.s]['zijdblock_tilt']) == 0:
            self.coordinates_box.SetStringSelection('specimen')
        elif coordinate_system == 'geographic' and \
                len(self.Data[self.s]['zijdblock_geo']) == 0:
            self.coordinates_box.SetStringSelection("specimen")
        if coordinate_system != self.coordinates_box.GetValue() and self.ie_open:
            self.ie.coordinates_box.SetStringSelection(
                self.coordinates_box.GetValue())
            self.ie.update_editor()
        coordinate_system = self.coordinates_box.GetValue()
        self.COORDINATE_SYSTEM = coordinate_system

        # --------------------------
        # update treatment list
        # --------------------------

        self.update_bounds_boxes()

        # --------------------------
        # update high level boxes
        # --------------------------

        high_level = self.level_box.GetValue()
        old_string = self.level_names.GetValue()
        new_string = old_string
        if high_level == 'sample':
            if self.s in self.Data_hierarchy['sample_of_specimen']:
                new_string = self.Data_hierarchy['sample_of_specimen'][self.s]
            else:
                new_string = ''
        if high_level == 'site':
            if self.s in self.Data_hierarchy['site_of_specimen']:
                new_string = self.Data_hierarchy['site_of_specimen'][self.s]
            else:
                new_string = ''
        if high_level == 'location':
            if self.s in self.Data_hierarchy['location_of_specimen']:
                new_string = self.Data_hierarchy['location_of_specimen'][self.s]
            else:
                new_string = ''
        self.level_names.SetValue(new_string)
        if self.ie_open and new_string != old_string:
            self.ie.level_names.SetValue(new_string)
            self.ie.on_select_level_name(-1, True)

        # --------------------------
        # update PCA box
        # --------------------------

        self.update_PCA_box()

        # update warning
        self.generate_warning_text()
        self.update_warning_box()
        # update choices in the fit box
        self.update_fit_boxes()
        self.update_mean_fit_box()
        # measurements text box
        self.Add_text()
        # draw figures
        if self.current_fit:
            self.draw_figure(self.s, False)
        else:
            self.draw_figure(self.s, True)
        # update high level stats
        self.update_high_level_stats()
        # redraw interpretations
        self.update_GUI_with_new_interpretation()

    def update_warning_box(self):
        """
        updates the warning box with whatever the warning_text variable
        contains for this specimen
        """
        self.warning_box.Clear()
        if self.warning_text == "":
            self.warning_box.AppendText("No Problems")
        else:
            self.warning_box.AppendText(self.warning_text)

    def update_GUI_with_new_interpretation(self):
        """
        update statistics boxes and figures with a new interpretatiom when
        selecting new temperature bound
        """

        self.update_fit_bounds_and_statistics()
        self.draw_interpretations()
        self.calculate_high_levels_data()
        self.plot_high_levels_data()

    def update_fit_bounds_and_statistics(self):
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

        if mpars and 'specimen_dec' in list(mpars.keys()):
            dec_key = 'specimen_dec'
            if 'best fit' in self.plane_display_box.GetValue() and \
               mpars['calculation_type'] == 'DE-BFP' and \
               self.current_fit not in self.bad_fits:
                dec_key = 'bfv_dec'
                if 'bfv_dec' not in list(mpars.keys()):
                    self.calculate_best_fit_vectors()
            self.sdec_window.SetValue("%.1f" % mpars[dec_key])
            self.sdec_window.SetBackgroundColour(wx.WHITE)
        else:
            self.sdec_window.SetValue("")
            self.sdec_window.SetBackgroundColour(wx.Colour('grey'))

        if mpars and 'specimen_inc' in list(mpars.keys()):
            inc_key = 'specimen_inc'
            if 'best fit' in self.plane_display_box.GetValue() and \
               mpars['calculation_type'] == 'DE-BFP' and \
               self.current_fit not in self.bad_fits:
                inc_key = 'bfv_inc'
                if 'bfv_inc' not in list(mpars.keys()):
                    self.calculate_best_fit_vectors()
            self.sinc_window.SetValue("%.1f" % mpars[inc_key])
            self.sinc_window.SetBackgroundColour(wx.WHITE)
        else:
            self.sinc_window.SetValue("")
            self.sinc_window.SetBackgroundColour(wx.Colour('grey'))

        if mpars and 'specimen_n' in list(mpars.keys()):
            self.sn_window.SetValue("%i" % mpars['specimen_n'])
            self.sn_window.SetBackgroundColour(wx.WHITE)
        else:
            self.sn_window.SetValue("")
            self.sn_window.SetBackgroundColour(wx.Colour('grey'))

        if mpars and 'specimen_mad' in list(mpars.keys()):
            self.smad_window.SetValue("%.1f" % mpars['specimen_mad'])
            self.smad_window.SetBackgroundColour(wx.WHITE)
        else:
            self.smad_window.SetValue("")
            self.smad_window.SetBackgroundColour(wx.Colour('grey'))

        if mpars and 'specimen_dang' in list(mpars.keys()) and float(mpars['specimen_dang']) != -1:
            self.sdang_window.SetValue("%.1f" % mpars['specimen_dang'])
            self.sdang_window.SetBackgroundColour(wx.WHITE)
        else:
            self.sdang_window.SetValue("")
            self.sdang_window.SetBackgroundColour(wx.Colour('grey'))

        if mpars and 'specimen_alpha95' in list(mpars.keys()) and float(mpars['specimen_alpha95']) != -1:
            self.salpha95_window.SetValue("%.1f" % mpars['specimen_alpha95'])
            self.salpha95_window.SetBackgroundColour(wx.WHITE)
        else:
            self.salpha95_window.SetValue("")
            self.salpha95_window.SetBackgroundColour(wx.Colour('grey'))

        if self.orthogonal_box.GetValue() == "X=best fit line dec":
            if mpars and 'specimen_dec' in list(mpars.keys()):
                self.draw_figure(self.s)

    def update_high_level_stats(self):
        """
        updates high level statistics in bottom left of GUI.
        """
        self.clear_high_level_pars()
        dirtype = str(self.coordinates_box.GetValue())
        if dirtype == 'specimen':
            dirtype = 'DA-DIR'
        elif dirtype == 'geographic':
            dirtype = 'DA-DIR-GEO'
        elif dirtype == 'tilt-corrected':
            dirtype = 'DA-DIR-TILT'
        if str(self.level_box.GetValue()) == 'sample':
            high_level_type = 'samples'
        elif str(self.level_box.GetValue()) == 'site':
            high_level_type = 'sites'
        elif str(self.level_box.GetValue()) == 'location':
            high_level_type = 'locations'
        elif str(self.level_box.GetValue()) == 'study':
            high_level_type = 'study'
        high_level_name = str(self.level_names.GetValue())
        elements_type = self.UPPER_LEVEL_SHOW
        if high_level_name in list(self.high_level_means[high_level_type].keys()):
            mpars = []
            for mf in list(self.high_level_means[high_level_type][high_level_name].keys()):
                if mf in list(self.high_level_means[high_level_type][high_level_name].keys()) and self.mean_fit == 'All' or mf == self.mean_fit:
                    if dirtype in list(self.high_level_means[high_level_type][high_level_name][mf].keys()):
                        mpar = deepcopy(
                            self.high_level_means[high_level_type][high_level_name][mf][dirtype])
                        if 'n' in mpar and mpar['n'] == 1:
                            mpar['calculation_type'] = "Fisher:"+mf
                            mpars.append(mpar)
                        elif mpar['calculation_type'] == 'Fisher by polarity':
                            for k in list(mpar.keys()):
                                if k == 'color' or k == 'calculation_type':
                                    continue
                                mpar[k]['calculation_type'] += ':'+k+':'+mf
                                mpar[k]['color'] = mpar['color']
                                if 'K' not in mpar[k] and 'k' in mpar[k]:
                                    mpar[k]['K'] = mpar[k]['k']
                                if 'R' not in mpar[k] and 'r' in mpar[k]:
                                    mpar[k]['R'] = mpar[k]['r']
                                if 'n_lines' not in mpar[k] and 'n' in mpar[k]:
                                    mpar[k]['n_lines'] = mpar[k]['n']
                                mpars.append(mpar[k])
                        else:
                            mpar['calculation_type'] += ":"+mf
                            mpars.append(mpar)
            self.switch_stats_button.SetRange(0, len(mpars)-1)
            self.show_high_levels_pars(mpars)
            if self.ie_open:
                self.ie.switch_stats_button.SetRange(0, len(mpars)-1)

    def update_bounds_boxes(self):
        """
        updates bounds boxes with bounds of current specimen and fit
        """
        if self.s not in list(self.Data.keys()):
            self.select_specimen(list(self.Data.keys())[0])
        self.T_list = self.Data[self.s]['zijdblock_steps']
        if self.current_fit:
            self.tmin_box.SetItems(self.T_list)
            self.tmax_box.SetItems(self.T_list)
            if type(self.current_fit.tmin) == str and type(self.current_fit.tmax) == str:
                self.tmin_box.SetStringSelection(self.current_fit.tmin)
                self.tmax_box.SetStringSelection(self.current_fit.tmax)
        if self.ie_open:
            self.ie.update_bounds_boxes(self.T_list)

    def update_PCA_box(self):
        """
        updates PCA box with current fit's PCA type
        """
        if self.s in list(self.pmag_results_data['specimens'].keys()):

            if self.current_fit:
                tmin = self.current_fit.tmin
                tmax = self.current_fit.tmax
                calculation_type = self.current_fit.PCA_type
            else:
                calculation_type = self.PCA_type_box.GetValue()
                PCA_type = "None"

            # update calculation type windows
            if calculation_type == "DE-BFL":
                PCA_type = "line"
            elif calculation_type == "DE-BFL-A":
                PCA_type = "line-anchored"
            elif calculation_type == "DE-BFL-O":
                PCA_type = "line-with-origin"
            elif calculation_type == "DE-FM":
                PCA_type = "Fisher"
            elif calculation_type == "DE-BFP":
                PCA_type = "plane"
            else:
                print("no PCA type found setting to line")
                PCA_type = "line"
            self.PCA_type_box.SetStringSelection(PCA_type)

    def update_fit_boxes(self, new_fit=False):
        """
        alters fit_box and mean_fit_box lists to match with changes in
        specimen or new/removed interpretations

        Parameters
        ----------
        new_fit : boolean representing if there is a new fit

        Alters
        ------
        fit_box selection, tmin_box selection, tmax_box selection,
        mean_fit_box selection, current_fit
        """
        # update the fit box
        self.update_fit_box(new_fit)
        # select new fit
        self.on_select_fit(None)
        # update the high level fits box
        self.update_mean_fit_box()

    def update_fit_box(self, new_fit=False):
        """
        alters fit_box lists to match with changes in specimen or new/
        removed interpretations

        Parameters
        ----------
        new_fit : boolean representing if there is a new fit

        Alters
        ------
        fit_box selection and choices, current_fit
        """
        # get new fit data
        if self.s in list(self.pmag_results_data['specimens'].keys()):
            self.fit_list = list(
                [x.name for x in self.pmag_results_data['specimens'][self.s]])
        else:
            self.fit_list = []
        # find new index to set fit_box to
        if not self.fit_list:
            new_index = 'None'
        elif new_fit:
            new_index = len(self.fit_list) - 1
        else:
            if self.fit_box.GetValue() in self.fit_list:
                new_index = self.fit_list.index(self.fit_box.GetValue())
            else:
                new_index = 'None'
        # clear old box
        self.fit_box.Clear()
        # update fit box
        self.fit_box.SetItems(self.fit_list)
        fit_index = None
        # select defaults
        if new_index == 'None':
            self.fit_box.SetStringSelection('None')
        else:
            self.fit_box.SetSelection(new_index)

    def update_mean_fit_box(self):
        """
        alters mean_fit_box list to match with changes in specimen or new/
        removed interpretations

        Alters
        ------
        mean_fit_box selection and choices, mean_types_box string selection
        """
        self.mean_fit_box.Clear()
        # update high level mean fit box
        fit_index = None
        if self.mean_fit in self.all_fits_list:
            fit_index = self.all_fits_list.index(self.mean_fit)
        self.all_fits_list = []
        for specimen in self.specimens:
            if specimen in self.pmag_results_data['specimens']:
                for name in [x.name for x in self.pmag_results_data['specimens'][specimen]]:
                    if name not in self.all_fits_list:
                        self.all_fits_list.append(name)
        self.mean_fit_box.SetItems(['None', 'All'] + self.all_fits_list)
        # select defaults
        if not isinstance(fit_index, type(None)):
            self.mean_fit_box.SetValue(self.all_fits_list[fit_index])
        elif self.mean_fit == 'All':
            self.mean_fit_box.SetValue('All')
        else:
            self.mean_fit_box.SetValue('None')
            self.mean_type_box.SetValue('None')
            self.clear_high_level_pars()
        self.update_toggleable_means_menu()
        if self.ie_open:
            self.ie.mean_fit_box.Clear()
            self.ie.mean_fit_box.SetItems(['None', 'All'] + self.all_fits_list)
            if fit_index:
                self.ie.mean_fit_box.SetValue(self.all_fits_list[fit_index])
            elif self.mean_fit == 'All':
                self.ie.mean_fit_box.SetValue('All')
            else:
                self.ie.mean_fit_box.SetValue('None')
                self.ie.mean_type_box.SetValue('None')

    def update_toggleable_means_menu(self):
        mb = self.GetMenuBar()
        am = mb.GetMenu(2)
        submenu_toggle_mean_display = wx.Menu()
        lines = ["m_%s_toggle_mean = submenu_toggle_mean_display.AppendCheckItem(-1, '&%s', '%s'); self.Bind(wx.EVT_MENU, self.on_menu_toggle_mean, m_%s_toggle_mean)" % (f.replace(
            ' ', '').replace('-', '_'), f.replace(' ', '').replace('-', '_'), f.replace(' ', '').replace('-', '_'), f.replace(' ', '').replace('-', '_')) for f in self.all_fits_list]

        for line in lines:
            exec(line)

        am.DestroyItem(am.GetMenuItems()[3])
        am.AppendSubMenu(submenu_toggle_mean_display, "Toggle Mean Display")

    def show_high_levels_pars(self, mpars):
        """
        shows in the high level mean display area in the bottom left of the
        GUI the data in mpars.
        """
        FONT_WEIGHT = self.GUI_RESOLUTION+(self.GUI_RESOLUTION-1)*5
        font2 = wx.Font(12+min(1, FONT_WEIGHT), wx.SWISS,
                        wx.NORMAL, wx.NORMAL, False, self.font_type)

        if self.mean_type_box.GetValue() != "None" and self.mean_fit_box.GetValue() != "None" and mpars:

            if isinstance(mpars, list):
                i = self.switch_stats_button.GetValue()
                if i >= len(mpars):
                    print(("Cannot display statistics as mpars does not have index %d. Was given mpars %s, aborting." % (
                        i, str(mpars))))
                    return
                self.show_high_levels_pars(mpars[i])
            elif mpars["calculation_type"].startswith('Fisher'):
                if "alpha95" in list(mpars.keys()):
                    for val in ['mean_type:calculation_type', 'dec:dec', 'inc:inc', 'alpha95:alpha95', 'K:K', 'R:R', 'n_lines:n_lines', 'n_planes:n_planes']:
                        val, ind = val.split(":")
                        COMMAND = """self.%s_window.SetValue(str(mpars['%s']))""" % (
                            val, ind)
                        exec(COMMAND)

                if self.ie_open:
                    ie = self.ie
                    if "alpha95" in list(mpars.keys()):
                        for val in ['mean_type:calculation_type', 'dec:dec', 'inc:inc', 'alpha95:alpha95', 'K:K', 'R:R', 'n_lines:n_lines', 'n_planes:n_planes']:
                            val, ind = val.split(":")
                            COMMAND = """ie.%s_window.SetValue(str(mpars['%s']))""" % (
                                val, ind)
                            exec(COMMAND)

            elif mpars["calculation_type"].startswith('Fisher by polarity'):
                i = self.switch_stats_button.GetValue()
                keys = list(mpars.keys())
                keys.remove('calculation_type')
                if 'color' in keys:
                    keys.remove('color')
                keys.sort()
                name = keys[i % len(keys)]
                mpars = mpars[name]
                if type(mpars) != dict:
                    print(
                        ("error in showing high level mean, reseaved %s" % str(mpars)))
                    return
                if mpars["calculation_type"] == 'Fisher' and "alpha95" in list(mpars.keys()):
                    for val in ['mean_type:calculation_type', 'dec:dec', 'inc:inc', 'alpha95:alpha95', 'K:k', 'R:r', 'n_lines:n', 'n_planes:n_planes']:
                        val, ind = val.split(":")
                        if val == 'mean_type':
                            COMMAND = """self.%s_window.SetValue('%s')""" % (
                                val, mpars[ind] + ":" + name)
                        else:
                            COMMAND = """self.%s_window.SetValue(str(mpars['%s']))""" % (
                                val, ind)
                        exec(COMMAND)

                if self.ie_open:
                    ie = self.ie
                    if mpars["calculation_type"] == 'Fisher' and "alpha95" in list(mpars.keys()):
                        for val in ['mean_type:calculation_type', 'dec:dec', 'inc:inc', 'alpha95:alpha95', 'K:k', 'R:r', 'n_lines:n', 'n_planes:n_planes']:
                            val, ind = val.split(":")
                            if val == 'mean_type':
                                COMMAND = """ie.%s_window.SetValue('%s')""" % (
                                    val, mpars[ind] + ":" + name)
                            else:
                                COMMAND = """ie.%s_window.SetValue(str(mpars['%s']))""" % (
                                    val, ind)
                            exec(COMMAND)

        self.set_mean_stats_color()

    def set_mean_stats_color(self):
        for val in ['mean_type', 'dec', 'inc', 'alpha95', 'K', 'R', 'n_lines', 'n_planes']:
            command = """
if self.%s_window.GetValue()=="": self.%s_window.SetBackgroundColour(wx.Colour('grey'))
else: self.%s_window.SetBackgroundColour(wx.WHITE)
            """ % (val, val, val)
            exec(command)
        if self.ie_open:
            for val in ['mean_type', 'dec', 'inc', 'alpha95', 'K', 'R', 'n_lines', 'n_planes']:
                command = """
if self.ie.%s_window.GetValue()=="": self.ie.%s_window.SetBackgroundColour(wx.Colour('grey'))
else: self.ie.%s_window.SetBackgroundColour(wx.WHITE)
                """ % (val, val, val)
                exec(command)

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
            self.fit_box.SetItems(
                list([x.name for x in self.pmag_results_data['specimens'][self.s]]))

        for parameter in ['dec', 'inc', 'n', 'mad', 'dang', 'alpha95']:
            COMMAND = "self.s%s_window.SetValue('')" % parameter
            exec(COMMAND)
            COMMAND = "self.s%s_window.SetBackgroundColour(wx.Colour('grey'))" % parameter
            exec(COMMAND)

    def clear_high_level_pars(self):
        """
        clears all high level pars display boxes
        """
        for val in ['mean_type', 'dec', 'inc', 'alpha95', 'K', 'R', 'n_lines', 'n_planes']:
            COMMAND = """self.%s_window.SetValue("")""" % (val)
            exec(COMMAND)
        if self.ie_open:
            for val in ['mean_type', 'dec', 'inc', 'alpha95', 'K', 'R', 'n_lines', 'n_planes']:
                COMMAND = """self.ie.%s_window.SetValue("")""" % (val)
                exec(COMMAND)
        self.set_mean_stats_color()

    def MacReopenApp(self):
        """
        Called when the doc icon is clicked
        """
        self.GetTopWindow().Raise()

#==========================================================================================#
#=================================Menu Functions===========================================#
#==========================================================================================#

    #---------------------------------------------#
    # File Menu Functions
    #---------------------------------------------#

    def on_menu_pick_read_inp(self, event):
        inp_file_name = pick_inp(self, self.WD)
        if inp_file_name == None:
            return
        magic_files = {}
        read_inp(self.WD, inp_file_name, magic_files)
        combine_magic_files(self.WD, magic_files)
        self.reset_backend()

    def on_menu_read_all_inp(self, event):
        inp_file_names = get_all_inp_files(self.WD)
        if inp_file_names == []:
            return

        magic_files = {}
        for inp_file_name in inp_file_names:
            read_inp(self.WD, inp_file_name, magic_files)
        combine_magic_files(self.WD, magic_files)
        self.reset_backend()

    def on_menu_make_MagIC_results_tables(self, event):
        """
         Creates or Updates Specimens or Pmag Specimens MagIC table,
         overwrites .redo file for safety, and starts User dialog to
         generate other MagIC tables for later contribution to the MagIC
         database. The following describes the steps used in the 2.5 data
         format to do this:

         1. read pmag_specimens.txt, pmag_samples.txt, pmag_sites.txt, and
            sort out lines with LP-DIR in magic_codes
         2. saves a clean pmag_*.txt files without LP-DIR stuff as
            pmag_*.txt.tmp
         3. write a new file pmag_specimens.txt
         4. merge pmag_specimens.txt and pmag_specimens.txt.tmp using
            combine_magic.py
         5. delete pmag_specimens.txt.tmp
         6 (optional) extracting new pag_*.txt files (except
            pmag_specimens.txt) using specimens_results_magic.py
         7: if #6: merge pmag_*.txt and pmag_*.txt.tmp using combine_magic.py
            if not #6: save pmag_*.txt.tmp as pmag_*.txt
        """

        # ---------------------------------------
        # save pmag_*.txt.tmp without directional data
        # ---------------------------------------
        self.on_menu_save_interpretation(None)

        # ---------------------------------------
        # dialog box to choose coordinate systems for pmag_specimens.txt
        # ---------------------------------------
        dia = demag_dialogs.magic_pmag_specimens_table_dialog(None)
        CoorTypes = []
        if self.test_mode:
            CoorTypes = ['DA-DIR']
        elif dia.ShowModal() == wx.ID_OK:  # Until the user clicks OK, show the message
            if dia.cb_spec_coor.GetValue() == True:
                CoorTypes.append('DA-DIR')
            if dia.cb_geo_coor.GetValue() == True:
                CoorTypes.append('DA-DIR-GEO')
            if dia.cb_tilt_coor.GetValue() == True:
                CoorTypes.append('DA-DIR-TILT')
        else:
            self.user_warning("MagIC tables not saved")
            print("MagIC tables not saved")
            return
        # ------------------------------

        self.PmagRecsOld = {}
        if self.data_model == 3.0:
            FILES = []
        else:
            FILES = ['pmag_specimens.txt']
        for FILE in FILES:
            self.PmagRecsOld[FILE] = []
            meas_data = []
            try:
                meas_data, file_type = pmag.magic_read(
                    os.path.join(self.WD, FILE))
                print(("-I- Read old magic file  %s\n" %
                       os.path.join(self.WD, FILE)))
                # if FILE !='pmag_specimens.txt':
                os.remove(os.path.join(self.WD, FILE))
                print(("-I- Delete old magic file  %s\n" %
                       os.path.join(self.WD, FILE)))

            except (OSError, IOError) as e:
                continue

            for rec in meas_data:
                if "magic_method_codes" in list(rec.keys()):
                    if "LP-DIR" not in rec['magic_method_codes'] and "DE-" not in rec['magic_method_codes']:
                        self.PmagRecsOld[FILE].append(rec)

        # ---------------------------------------
        # write a new pmag_specimens.txt
        # ---------------------------------------

        specimens_list = list(self.pmag_results_data['specimens'].keys())
        specimens_list.sort()
        PmagSpecs = []
        for specimen in specimens_list:
            for dirtype in CoorTypes:
                i = 0
                for fit in self.pmag_results_data['specimens'][specimen]:
                    mpars = fit.get(dirtype)
                    if not mpars:
                        mpars = self.get_PCA_parameters(
                            specimen, fit, fit.tmin, fit.tmax, dirtype, fit.PCA_type)
                        if not mpars or 'specimen_dec' not in list(mpars.keys()):
                            self.user_warning("Could not calculate interpretation for specimen %s and fit %s in coordinate system %s while exporting pmag tables, skipping" % (
                                specimen, fit.name, dirtype))
                            continue

                    PmagSpecRec = {}
                    PmagSpecRec["magic_software_packages"] = pmag.get_version(
                    ) + ': demag_gui'
                    PmagSpecRec["er_specimen_name"] = specimen
                    PmagSpecRec["er_sample_name"] = self.Data_hierarchy['sample_of_specimen'][specimen]
                    PmagSpecRec["er_site_name"] = self.Data_hierarchy['site_of_specimen'][specimen]
                    PmagSpecRec["er_location_name"] = self.Data_hierarchy['location_of_specimen'][specimen]
                    if specimen in list(self.Data_hierarchy['expedition_name_of_specimen'].keys()):
                        PmagSpecRec["er_expedition_name"] = self.Data_hierarchy['expedition_name_of_specimen'][specimen]
                    PmagSpecRec["er_citation_names"] = "This study"
                    if "magic_experiment_name" in self.Data[specimen]:
                        PmagSpecRec["magic_experiment_names"] = self.Data[specimen]["magic_experiment_name"]
                    if 'magic_instrument_codes' in list(self.Data[specimen].keys()):
                        PmagSpecRec["magic_instrument_codes"] = self.Data[specimen]['magic_instrument_codes']
                    PmagSpecRec['specimen_correction'] = 'u'
                    PmagSpecRec['specimen_direction_type'] = mpars["specimen_direction_type"]
                    PmagSpecRec['specimen_dec'] = "%.1f" % mpars["specimen_dec"]
                    PmagSpecRec['specimen_inc'] = "%.1f" % mpars["specimen_inc"]
                    PmagSpecRec['specimen_flag'] = "g"
                    if fit in self.bad_fits:
                        PmagSpecRec['specimen_flag'] = "b"

                    if "C" in fit.tmin or "C" in fit.tmax:
                        PmagSpecRec['measurement_step_unit'] = "K"
                    else:
                        PmagSpecRec['measurement_step_unit'] = "T"

                    if "C" in fit.tmin:
                        PmagSpecRec['measurement_step_min'] = "%.0f" % (
                            mpars["measurement_step_min"]+273.)
                    elif "mT" in fit.tmin:
                        PmagSpecRec['measurement_step_min'] = "%8.3e" % (
                            mpars["measurement_step_min"]*1e-3)
                    else:
                        if PmagSpecRec['measurement_step_unit'] == "K":
                            PmagSpecRec['measurement_step_min'] = "%.0f" % (
                                mpars["measurement_step_min"]+273.)
                        else:
                            PmagSpecRec['measurement_step_min'] = "%8.3e" % (
                                mpars["measurement_step_min"]*1e-3)

                    if "C" in fit.tmax:
                        PmagSpecRec['measurement_step_max'] = "%.0f" % (
                            mpars["measurement_step_max"]+273.)
                    elif "mT" in fit.tmax:
                        PmagSpecRec['measurement_step_max'] = "%8.3e" % (
                            mpars["measurement_step_max"]*1e-3)
                    else:
                        if PmagSpecRec['measurement_step_unit'] == "K":
                            PmagSpecRec['measurement_step_min'] = "%.0f" % (
                                mpars["measurement_step_min"]+273.)
                        else:
                            PmagSpecRec['measurement_step_min'] = "%8.3e" % (
                                mpars["measurement_step_min"]*1e-3)

                    PmagSpecRec['specimen_n'] = "%.0f" % mpars["specimen_n"]
                    calculation_type = mpars['calculation_type']
                    PmagSpecRec["magic_method_codes"] = self.Data[specimen]['magic_method_codes'] + \
                        ":"+calculation_type+":"+dirtype
                    PmagSpecRec["specimen_comp_n"] = str(
                        len(self.pmag_results_data["specimens"][specimen]))
                    PmagSpecRec["specimen_comp_name"] = fit.name
                    if fit in self.bad_fits:
                        PmagSpecRec["specimen_flag"] = "b"
                    else:
                        PmagSpecRec["specimen_flag"] = "g"
                    if calculation_type in ["DE-BFL", "DE-BFL-A", "DE-BFL-O"]:
                        PmagSpecRec['specimen_direction_type'] = 'l'
                        PmagSpecRec['specimen_mad'] = "%.1f" % float(
                            mpars["specimen_mad"])
                        PmagSpecRec['specimen_dang'] = "%.1f" % float(
                            mpars['specimen_dang'])
                        PmagSpecRec['specimen_alpha95'] = ""
                    elif calculation_type in ["DE-BFP"]:
                        PmagSpecRec['specimen_direction_type'] = 'p'
                        PmagSpecRec['specimen_mad'] = "%.1f" % float(
                            mpars['specimen_mad'])
                        PmagSpecRec['specimen_dang'] = ""
                        PmagSpecRec['specimen_alpha95'] = ""
                        if self.data_model == 3.0:
                            if 'bfv_dec' not in list(mpars.keys()) or \
                               'bfv_inc' not in list(mpars.keys()):
                                self.calculate_best_fit_vectors(
                                    high_level_type="sites", high_level_name=PmagSpecRec["er_site_name"], dirtype=dirtype)
                                mpars = fit.get(dirtype)
                            try:
                                PmagSpecRec['dir_bfv_dec'] = "%.1f" % mpars['bfv_dec']
                                PmagSpecRec['dir_bfv_inc'] = "%.1f" % mpars['bfv_inc']
                            except KeyError:
                                print("Error calculating BFV during export of interpretations for %s, %s, %s" % (
                                    fit.name, specimen, dirtype))
                    elif calculation_type in ["DE-FM"]:
                        PmagSpecRec['specimen_direction_type'] = 'l'
                        PmagSpecRec['specimen_mad'] = ""
                        PmagSpecRec['specimen_dang'] = ""
                        PmagSpecRec['specimen_alpha95'] = "%.1f" % float(
                            mpars['specimen_alpha95'])
                    if dirtype == 'DA-DIR-TILT':
                        PmagSpecRec['specimen_tilt_correction'] = "100"
                    elif dirtype == 'DA-DIR-GEO':
                        PmagSpecRec['specimen_tilt_correction'] = "0"
                    else:
                        PmagSpecRec['specimen_tilt_correction'] = "-1"
                    PmagSpecs.append(PmagSpecRec)
                    i += 1

        # add the 'old' lines with no "LP-DIR" in
        if 'pmag_specimens.txt' in list(self.PmagRecsOld.keys()):
            for rec in self.PmagRecsOld['pmag_specimens.txt']:
                PmagSpecs.append(rec)
        PmagSpecs_fixed = self.merge_pmag_recs(PmagSpecs)

        if len(PmagSpecs_fixed) == 0:
            self.user_warning(
                "No data to save to MagIC tables please create some interpretations before saving")
            print("No data to save, MagIC tables not written")
            return

        if self.data_model == 3.0:

            # translate demag_gui output to 3.0 DataFrame
            ndf2_5 = DataFrame(PmagSpecs_fixed)
            if 'specimen_direction_type' in ndf2_5.columns:
                # doesn't exist in new model
                del ndf2_5['specimen_direction_type']
            ndf3_0 = ndf2_5.rename(columns=map_magic.spec_magic2_2_magic3_map)
            if 'specimen' in ndf3_0.columns:
                ndf3_0 = ndf3_0.set_index("specimen")
                # replace the removed specimen column
                ndf3_0['specimen'] = ndf3_0.index
            # prefer keeping analyst_names in txt
            if 'analyst_names' in ndf3_0:
                del ndf3_0['analyst_names']

            # get current 3.0 DataFrame from contribution object
            if 'specimens' not in self.con.tables:
                cols = ndf3_0.columns
                self.con.add_empty_magic_table('specimens', col_names=cols)
            spmdf = self.con.tables['specimens']
            # remove translation collisions or deprecated terms
            for dc in ["dir_comp_name", "magic_method_codes"]:
                if dc in spmdf.df.columns:
                    del spmdf.df[dc]

            # merge previous df with new interpretations DataFrame
            # (do not include non-directional data in the merge or else it
            # will be overwritten)

            # fix index names
            spmdf.df.index.name = "specimen_name"
            ndf3_0.index.name = "specimen_name"
            # pull out directional/non-directional data
            if 'method_codes' not in spmdf.df:
                spmdf.df['method_codes'] = ''
            directional = spmdf.df['method_codes'].str.contains('LP-DIR').astype(bool)
            non_directional_df = spmdf.df[~directional]
            spmdf.df = spmdf.df[directional]
            # merge new interpretations with old specimen information
            directional_df = spmdf.merge_dfs(ndf3_0)
            # add any missing columns to non_directional_df
            for col in directional_df.columns:
                if col not in non_directional_df.columns:
                    non_directional_df[col] = ""
            # make sure columns are ordered the same so that we can concatenate
            non_directional_df.sort_index(axis='columns', inplace=True)
            directional_df.sort_index(axis='columns', inplace=True)
            # put directional/non-directional data back together
            merged = pd.concat([non_directional_df, directional_df])
            merged.sort_index(inplace=True)
            spmdf.df = merged

            # write to disk
            spmdf.write_magic_file(dir_path=self.WD)

            TEXT = "specimens interpretations are saved in specimens.txt.\nPress OK to save to samples/sites/locations/ages tables."
            self.dlg = wx.MessageDialog(
                self, caption="Other Tables", message=TEXT, style=wx.OK | wx.CANCEL)
            result = self.show_dlg(self.dlg)
            if result == wx.ID_OK:
                self.dlg.Destroy()
            else:
                self.dlg.Destroy()
                return

        else:
            pmag.magic_write(os.path.join(
                self.WD, "pmag_specimens.txt"), PmagSpecs_fixed, 'pmag_specimens')
            print(("specimen data stored in %s\n" %
                   os.path.join(self.WD, "pmag_specimens.txt")))

            TEXT = "specimens interpretations are saved in pmag_specimens.txt.\nPress OK for pmag_samples/pmag_sites/pmag_results tables."
            dlg = wx.MessageDialog(
                self, caption="Other Pmag Tables", message=TEXT, style=wx.OK | wx.CANCEL)
            result = self.show_dlg(dlg)
            if result == wx.ID_OK:
                dlg.Destroy()
            else:
                dlg.Destroy()
                return

        # --------------------------------

        dia = demag_dialogs.magic_pmag_tables_dialog(
            None, self.WD, self.Data, self.Data_info)

        if self.show_dlg(dia) == wx.ID_OK:  # Until the user clicks OK, show the message
            self.On_close_MagIC_dialog(dia)

    def on_save_Zij_plot(self, event):
        self.current_fit = None
        self.draw_interpretations()
        self.plot_high_levels_data()
        self.fig1.text(0.9, 0.98, '%s' % (self.s), {
                       'family': self.font_type, 'fontsize': 10, 'style': 'normal', 'va': 'center', 'ha': 'right'})
        demag_dialogs.SaveMyPlot(
            self.fig1, self.s, "Zij", self.WD, test_mode=self.test_mode)
#        self.fig1.clear()
        self.draw_figure(self.s)
        self.update_selection()

    def on_save_Eq_plot(self, event):
        self.current_fit = None
        self.draw_interpretations()
        self.plot_high_levels_data()
        #self.fig2.text(0.9,0.96,'%s'%(self.s),{'family':self.font_type, 'fontsize':10, 'style':'normal','va':'center', 'ha':'right' })
        # self.canvas4.print_figure("./tmp.pdf")#, dpi=self.dpi)
        demag_dialogs.SaveMyPlot(
            self.fig2, self.s, "EqArea", self.WD, test_mode=self.test_mode)
#        self.fig2.clear()
        self.draw_figure(self.s)
        self.update_selection()

    def on_save_M_t_plot(self, event):
        self.current_fit = None
        self.draw_interpretations()
        self.plot_high_levels_data()
        self.fig3.text(0.9, 0.96, '%s' % (self.s), {
                       'family': self.font_type, 'fontsize': 10, 'style': 'normal', 'va': 'center', 'ha': 'right'})
        demag_dialogs.SaveMyPlot(
            self.fig3, self.s, "M_M0", self.WD, test_mode=self.test_mode)
#        self.fig3.clear()
        self.draw_figure(self.s)
        self.update_selection()

    def on_save_high_level(self, event):
        self.current_fit = None
        self.draw_interpretations()
        self.plot_high_levels_data()
        demag_dialogs.SaveMyPlot(self.fig4, str(self.level_names.GetValue()), str(
            self.level_box.GetValue()), self.WD, test_mode=self.test_mode)
#        self.fig4.clear()
        self.draw_figure(self.s)
        self.update_selection()
        self.plot_high_levels_data()

    def on_save_all_figures(self, event):
        temp_fit = self.current_fit
        self.current_fit = None
        self.draw_interpretations()
        self.plot_high_levels_data()
        dlg = wx.DirDialog(self, "choose a folder:", defaultPath=self.WD,
                           style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON | wx.DD_CHANGE_DIR)
        if self.show_dlg(dlg) == wx.ID_OK:
            dir_path = dlg.GetPath()
            dlg.Destroy()

        # figs=[self.fig1,self.fig2,self.fig3,self.fig4]
        plot_types = ["Zij", "EqArea", "M_M0", str(self.level_box.GetValue())]
        # elements=[self.s,self.s,self.s,str(self.level_names.GetValue())]
        for i in range(4):
            try:
                if plot_types[i] == "Zij":
                    self.fig1.text(0.9, 0.98, '%s' % (self.s), {
                                   'family': self.font_type, 'fontsize': 10, 'style': 'normal', 'va': 'center', 'ha': 'right'})
                    demag_dialogs.SaveMyPlot(
                        self.fig1, self.s, "Zij", dir_path, test_mode=self.test_mode)
                if plot_types[i] == "EqArea":
                    demag_dialogs.SaveMyPlot(
                        self.fig2, self.s, "EqArea", dir_path, test_mode=self.test_mode)
                if plot_types[i] == "M_M0":
                    self.fig3.text(0.9, 0.96, '%s' % (self.s), {
                                   'family': self.font_type, 'fontsize': 10, 'style': 'normal', 'va': 'center', 'ha': 'right'})
                    demag_dialogs.SaveMyPlot(
                        self.fig3, self.s, "M_M0", dir_path, test_mode=self.test_mode)
                if plot_types[i] == str(self.level_box.GetValue()):
                    demag_dialogs.SaveMyPlot(self.fig4, str(self.level_names.GetValue()), str(
                        self.level_box.GetValue()), dir_path, test_mode=self.test_mode)
            except:
                pass

        self.fig1.clear()
        self.fig3.clear()
        self.draw_figure(self.s)
        self.update_selection()

    def on_menu_import_meas_file(self, event):
        """
        Open measurement file, reset self.magic_file
        and self.WD, and reset everything.
        """
        # use new measurement file and corresponding WD
        meas_file = self.choose_meas_file()
        WD = os.path.split(meas_file)[0]
        self.WD = WD
        self.magic_file = meas_file
        # reset backend with new files
        self.reset_backend()

    def on_menu_change_working_directory(self, event):
        old_WD = self.WD
        new_WD = self.get_DIR()
        self.change_WD(new_WD)
        print(("Working Directory altered from %s to %s, all output will be sent here" % (
            old_WD, new_WD)))

    def on_menu_exit(self, event):
        # check if interpretations have changed and were not saved
        write_session_to_failsafe = False
        try:
            number_saved_fits = sum(1 for line in open("demag_gui.redo"))
            number_current_fits = sum(len(self.pmag_results_data['specimens'][specimen]) for specimen in list(
                self.pmag_results_data['specimens'].keys()))
            # break if there are no fits there's no need to save an empty file
            if number_current_fits == 0:
                raise RuntimeError(
                    "get out and don't write, lol this is such a hack")
            write_session_to_failsafe = (
                number_saved_fits != number_current_fits)
            default_redo = open("demag_gui.redo")
            i, specimen = 0, None
            for line in default_redo:
                if line == None:
                    write_session_to_failsafe = True
                vals = line.strip("\n").split("\t")
                if vals[0] != specimen:
                    i = 0
                specimen = vals[0]
                tmin, tmax = self.parse_bound_data(vals[2], vals[3], specimen)
                if specimen in self.pmag_results_data['specimens']:
                    fit = self.pmag_results_data['specimens'][specimen][i]
                if write_session_to_failsafe:
                    break
                write_session_to_failsafe = ((specimen not in self.specimens) or
                                             (tmin != fit.tmin or tmax != fit.tmax) or
                                             (vals[4] != fit.name))
                i += 1
        except IOError:
            write_session_to_failsafe = True
        except IndexError:
            write_session_to_failsafe = True
        except RuntimeError:
            write_session_to_failsafe = False

        if write_session_to_failsafe:
            self.on_menu_save_interpretation(event, "demag_last_session.redo")


        if self.close_warning:
            if self.close_warning == "redo only":

                TEXT = "Data are only saved to a .redo file.\nTo fully save your data:\nFile --> Save MagIC tables.\n\n Press OK to exit without saving."
            else:
                TEXT = "Data are not saved to a file yet!\nTo properly save your data:\n1) Analysis --> Save current interpretations to a redo file.\nor\n1) File --> Save MagIC tables.\n\n Press OK to exit without saving."

            # Save all interpretation to a 'redo' file or to MagIC specimens result table\n\nPress OK to exit"
            dlg = wx.MessageDialog(
                self, caption="Warning:", message=TEXT, style=wx.OK | wx.CANCEL | wx.ICON_EXCLAMATION)
            if self.show_dlg(dlg) == wx.ID_OK:
                dlg.Destroy()
                if self.ie_open:
                    self.ie.on_close_edit_window(event)
                self.Destroy()
                if self.evt_quit:
                    event = self.evt_quit(self.GetId())
                    self.GetEventHandler().ProcessEvent(event)

        else:
            if self.ie_open:
                self.ie.on_close_edit_window(event)
            self.close_log_file()
            self.Destroy()
            if self.evt_quit:
                event = self.evt_quit(self.GetId())
                self.GetEventHandler().ProcessEvent(event)

        self.running = False

    #---------------------------------------------#
    # Edit Menu Functions
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

        pmag.magic_write(os.path.join(
            self.WD, "magic_measurements.txt"), self.mag_meas_data, "magic_measurements")

        self.recalculate_current_specimen_interpreatations()

        if self.ie_open:
            self.ie.update_current_fit_data()
        self.calculate_high_levels_data()
        self.update_selection()

    def on_menu_flag_meas_bad(self, event):
        next_i = self.logger.GetNextSelected(-1)
        while next_i != -1:
            self.mark_meas_bad(next_i)
            next_i = self.logger.GetNextSelected(next_i)

        pmag.magic_write(os.path.join(
            self.WD, "magic_measurements.txt"), self.mag_meas_data, "magic_measurements")

        self.recalculate_current_specimen_interpreatations()

        if self.ie_open:
            self.ie.update_current_fit_data()
        self.calculate_high_levels_data()
        self.update_selection()

    #---------------------------------------------#
    # Analysis Menu Functions
    #---------------------------------------------#

    def on_menu_previous_interpretation(self, event):
        """
        Create and show the Open FileDialog for upload previous
        interpretation
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
            style=wx.FD_OPEN | wx.FD_CHANGE_DIR
        )
        if self.show_dlg(dlg) == wx.ID_OK:
            redo_file = dlg.GetPath()
        else:
            redo_file = None
        dlg.Destroy()

        if redo_file:
            self.read_redo_file(redo_file)

    def on_menu_read_from_LSQ(self, event):
        dlg = wx.FileDialog(
            self, message="choose a LSQ file",
            defaultDir=self.WD,
            wildcard="*.LSQ",
            style=wx.FD_OPEN
        )
        if self.show_dlg(dlg) == wx.ID_OK:
            LSQ_file = dlg.GetPath()
        else:
            LSQ_file = None
        dlg.Destroy()

        self.read_from_LSQ(LSQ_file)

    def on_menu_save_interpretation(self, event, redo_file_name="demag_gui.redo"):
        fout = open(os.path.join(self.WD, redo_file_name), 'w')
        specimens_list = list(self.pmag_results_data['specimens'].keys())
        specimens_list.sort(key=spec_key_func)
        if self.s not in specimens_list:
            fout.write("current_"+self.s+"\n")
        for specimen in specimens_list:
            for fit in self.pmag_results_data['specimens'][specimen]:
                if fit.tmin == None or fit.tmax == None:
                    continue
                if type(fit.tmin) != str or type(fit.tmax) != str:
                    print(("-E- in on_menu_save_interpretation",
                           type(fit.tmin), fit.tmin, type(fit.tmax), fit.tmax))
                if specimen == self.s:
                    STRING = "current_"+specimen+"\t"
                else:
                    STRING = specimen+"\t"
                STRING = STRING+fit.PCA_type+"\t"
                fit_flag = "g"
                if "C" in fit.tmin:
                    tmin = "%.0f" % (float(fit.tmin.strip("C"))+273.)
                elif "mT" in fit.tmin:
                    tmin = "%.2e" % (float(fit.tmin.strip("mT"))/1000)
                else:
                    tmin = "0"
                if "C" in fit.tmax:
                    tmax = "%.0f" % (float(fit.tmax.strip("C"))+273.)
                elif "mT" in fit.tmax:
                    tmax = "%.2e" % (float(fit.tmax.strip("mT"))/1000)
                else:
                    tmax = "0"
                if fit in self.bad_fits:
                    fit_flag = "b"

                STRING = STRING+tmin+"\t"+tmax+"\t"+fit.name + \
                    "\t"+str(fit.color)+"\t"+fit_flag+"\n"
                fout.write(STRING)
        fout.close()
        TEXT = "specimen interpretations are saved in {}\n\nTo reload these interpretations next time, go to:\nFile --> Import interpretations from a redo file and select {}.".format(redo_file_name, redo_file_name)
        self.saved_dlg(TEXT)
        if self.close_warning:
            self.close_warning = "redo only"

    def on_menu_change_criteria(self, event):
        dia = demag_dialogs.demag_criteria_dialog(
            None, self.acceptance_criteria, title='PmagPy Demag Gui Acceptance Criteria')
        if self.show_dlg(dia) == wx.ID_OK:  # Until the user clicks OK, show the message
            self.on_close_criteria_box(dia)

    def on_menu_criteria_file(self, event):
        """
        read pmag_criteria.txt file
        and open changecriteria dialog
        """
        if self.data_model == 3:
            default_file = "criteria.txt"
        else:
            default_file = "pmag_criteria.txt"
        read_sucsess = False
        dlg = wx.FileDialog(
            self, message="choose pmag criteria file",
            defaultDir=self.WD,
            defaultFile=default_file,
            style=wx.FD_OPEN | wx.FD_CHANGE_DIR
        )
        if self.show_dlg(dlg) == wx.ID_OK:
            criteria_file = dlg.GetPath()
            print(("-I- Read new criteria file: %s" % criteria_file))

            # check if this is a valid pmag_criteria file
            try:
                mag_meas_data, file_type = pmag.magic_read(criteria_file)
            except:
                dlg = wx.MessageDialog(
                    self, caption="Error", message="not a valid pmag_criteria file", style=wx.OK)
                result = self.show_dlg(dlg)
                if result == wx.ID_OK:
                    dlg.Destroy()
                dlg.Destroy()
                return

            # initialize criteria
            self.acceptance_criteria = self.read_criteria_file(criteria_file)
            read_sucsess = True

        dlg.Destroy()
        if read_sucsess:
            self.on_menu_change_criteria(None)

    def on_menu_check_orient(self, event):
        if not isinstance(self.current_fit, Fit):
            print('-W- You must "add fit" first!')
            self.check_orient_on = False
            return
        if self.check_orient_on:
            self.check_orient_on = False
            self.plot_high_levels_data()
            return
        else:
            self.check_orient_on = True

        if self.level_box.GetValue() != "site":
            self.level_box.SetValue("site")
            self.onSelect_high_level(event)
        sites_with_data = []
        for site in self.sites:
            specs = self.Data_hierarchy['sites'][site]['specimens']
            if any([spec in self.pmag_results_data['specimens'] for spec in specs]):
                sites_with_data.append(site)
        if len(sites_with_data) == 0:
            self.user_warning(
                "can not check sample orientation without any interpretations, please fit data before using this function")
            return
        self.level_names.SetValue(sites_with_data[0])
        self.onSelect_level_name(event)

        if self.mean_fit_box.GetValue() == "None" or self.mean_fit_box.GetValue() == None:
            self.mean_fit_box.SetValue("All")
            self.onSelect_mean_fit_box(event)
        self.mean_type_box.SetValue("Fisher")
        self.onSelect_mean_type_box(event)

    def on_menu_mark_samp_bad(self, event):
        if not self.user_warning("This will mark the sample orietation flag for this sample to bad which will prevent you marking the specimen interpretations for this sample as good, do you want to continue?"):
            return
        samp = self.Data_hierarchy['sample_of_specimen'][self.s]
        specs = self.Data_hierarchy['samples'][samp]['specimens']
        for spec in specs:
            if spec not in self.pmag_results_data['specimens']:
                continue
            for comp in self.pmag_results_data['specimens'][spec]:
                if comp not in self.bad_fits:
                    self.bad_fits.append(comp)
        if self.data_model == 3.0:
            if 'orientation_flag' not in self.con.tables['samples'].df.columns:
                self.con.tables['samples'].df['orientation_flag'] = 'g'
            self.con.tables['samples'].df.loc[samp]['orientation_flag'] = 'b'
            self.Data_info['er_samples'][samp]['sample_orientation_flag'] = 'b'
            self.con.tables['samples'].write_magic_file(dir_path=self.WD)
        else:
            orecs = []
            for k, val in list(self.Data_info['er_samples'].items()):
                if 'sample_orientation_flag' not in val:
                    val['sample_orientation_flag'] = 'g'
                if k == samp:
                    val['sample_orientation_flag'] = 'b'
                orecs.append(val)
            pmag.magic_write('er_samples.txt', orecs, 'er_samples')
        self.update_selection()

    def on_menu_mark_samp_good(self, event):
        if not self.user_warning("This will mark all specimen interpretations in the sample of the current specimen as good as well as setting the sample orientation flag to good, do you want to continue?"):
            return
        samp = self.Data_hierarchy['sample_of_specimen'][self.s]
        specs = self.Data_hierarchy['samples'][samp]['specimens']
        for spec in specs:
            if spec not in self.pmag_results_data['specimens']:
                continue
            for comp in self.pmag_results_data['specimens'][spec]:
                if comp in self.bad_fits:
                    self.bad_fits.remove(comp)
        if self.data_model == 3.0:
            if 'orientation_flag' not in self.con.tables['samples'].df.columns:
                self.con.tables['samples'].df['orientation_flag'] = 'g'
            self.con.tables['samples'].df.loc[samp]['orientation_flag'] = 'g'
            self.Data_info['er_samples'][samp]['sample_orientation_flag'] = 'g'
            self.con.tables['samples'].write_magic_file(dir_path=self.WD)
        else:
            orecs = []
            for k, val in list(self.Data_info['er_samples'].items()):
                if 'sample_orientation_flag' not in val:
                    val['sample_orientation_flag'] = 'g'
                if k == samp:
                    val['sample_orientation_flag'] = 'g'
                orecs.append(val)
            pmag.magic_write('er_samples.txt', orecs, 'er_samples')
        self.update_selection()

    def on_menu_flag_fit_bad(self, event):
        if self.current_fit not in self.bad_fits:
            self.bad_fits.append(self.current_fit)

    def on_menu_flag_fit_good(self, event):
        if self.current_fit in self.bad_fits:
            self.bad_fits.remove(self.current_fit)

    def on_menu_toggle_mean(self, event):
        self.plot_high_level_means()
        self.canvas4.draw()
        if self.ie_open:
            self.ie.draw()

    #---------------------------------------------#
    # Tools Menu  Functions
    #---------------------------------------------#

    def on_menu_edit_interpretations(self, event):
        if not self.ie_open:
            self.ie = InterpretationEditorFrame(self)
            self.ie_open = True
            self.update_high_level_stats()
            self.ie.Center()
            if not self.test_mode:
                self.ie.Show(True)
            if self.parent == None and sys.platform.startswith('darwin'):
                TEXT = "This is a refresher window for mac os to insure that wx opens the new window"
                dlg = wx.MessageDialog(
                    self, caption="Open", message=TEXT, style=wx.OK | wx.ICON_INFORMATION | wx.STAY_ON_TOP)
                self.show_dlg(dlg)
                dlg.Destroy()
            if self.mean_fit != None and self.mean_fit != 'None':
                self.plot_high_levels_data()
        else:
            self.ie.ToggleWindowStyle(wx.STAY_ON_TOP)
            self.ie.ToggleWindowStyle(wx.STAY_ON_TOP)

    def on_menu_view_vgps(self, event):
        if not self.vgp_open:
            VGP_Data = self.calculate_vgp_data()
            vgpdia = demag_dialogs.VGP_Dialog(self, VGP_Data)
            if vgpdia.failed_init:
                return
            else:
                self.vgp_open=True
            vgpdia.Show()
#        self.show_dlg(vgpdia)

    #---------------------------------------------#
    # Help Menu Functions
    #---------------------------------------------#

    def on_menu_help(self, event):
        """
        Toggles the GUI's help mode which allows user to click on any part
        of the dialog and get help

        Parameters
        ----------
        event : wx.MenuEvent that triggers this function
        """
        self.helper.BeginContextHelp(self)

    def on_menu_docs(self, event):
        webopen("https://earthref.org/PmagPy/cookbook/#x1-350005.1.1", new=2)

    def on_menu_cookbook(self, event):
        webopen("http://earthref.org/PmagPy/cookbook/", new=2)

    def on_menu_git(self, event):
        webopen("https://github.com/ltauxe/PmagPy", new=2)

    def on_menu_debug(self, event):
        self.close_log_file()
        pdb.set_trace()

#==========================================================================================#
#===========================Panel Interaction Functions====================================#
#==========================================================================================#

    #---------------------------------------------#
    # Arrow Key Binding Functions
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
    # Figure Control Functions
    #---------------------------------------------#

    def right_click_zijderveld(self, event):
        """
        toggles between zoom and pan effects for the zijderveld on right
        click

        Parameters
        ----------
        event : the wx.MouseEvent that triggered the call of this function

        Alters
        ------
        zijderveld_setting, toolbar1 setting
        """
        if event.LeftIsDown() or event.ButtonDClick():
            return
        elif self.zijderveld_setting == "Zoom":
            self.zijderveld_setting = "Pan"
            try:
                self.toolbar1.pan('off')
            except TypeError:
                pass
        elif self.zijderveld_setting == "Pan":
            self.zijderveld_setting = "Zoom"
            try:
                self.toolbar1.zoom()
            except TypeError:
                pass

    def home_zijderveld(self, event):
        """
        homes zijderveld to original position

        Parameters
        ----------
        event : the wx.MouseEvent that triggered the call of this
        function

        Alters
        ------
        toolbar1 setting
        """
        try:
            self.toolbar1.home()
        except TypeError:
            pass

    def on_change_zijd_mouse_cursor(self, event):
        """
        If mouse is over data point making it selectable change the shape of
        the cursor

        Parameters
        ----------
        event : the wx Mouseevent for that click
        """
        if not array(self.CART_rot).any():
            return
        pos = event.GetPosition()
        width, height = self.canvas1.get_width_height()
        pos[1] = height - pos[1]
        xpick_data, ypick_data = pos
        xdata_org = list(self.CART_rot[:, 0]) + list(self.CART_rot[:, 0])
        ydata_org = list(-1*self.CART_rot[:, 1]) + list(-1*self.CART_rot[:, 2])
        data_corrected = self.zijplot.transData.transform(
            vstack([xdata_org, ydata_org]).T)
        xdata, ydata = data_corrected.T
        xdata = list(map(float, xdata))
        ydata = list(map(float, ydata))
        e = 4e0

        if self.zijderveld_setting == "Zoom":
            self.canvas1.SetCursor(wx.Cursor(wx.CURSOR_CROSS))
        else:
            self.canvas1.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
        for i, (x, y) in enumerate(zip(xdata, ydata)):
            if 0 < sqrt((x-xpick_data)**2. + (y-ypick_data)**2.) < e:
                self.canvas1.SetCursor(wx.Cursor(wx.CURSOR_HAND))
                break
        event.Skip()

    def on_zijd_select(self, event):
        """
        Get mouse position on double click find the nearest interpretation
        to the mouse
        position then select that interpretation

        Parameters
        ----------
        event : the wx Mouseevent for that click

        Alters
        ------
        current_fit
        """
        if not array(self.CART_rot_good).any():
            return
        pos = event.GetPosition()
        width, height = self.canvas1.get_width_height()
        pos[1] = height - pos[1]
        xpick_data, ypick_data = pos
        xdata_org = list(
            self.CART_rot_good[:, 0]) + list(self.CART_rot_good[:, 0])
        ydata_org = list(-1*self.CART_rot_good[:, 1]) + \
            list(-1*self.CART_rot_good[:, 2])
        data_corrected = self.zijplot.transData.transform(
            vstack([xdata_org, ydata_org]).T)
        xdata, ydata = data_corrected.T
        xdata = list(map(float, xdata))
        ydata = list(map(float, ydata))
        e = 4.0

        index = None
        for i, (x, y) in enumerate(zip(xdata, ydata)):
            if 0 < sqrt((x-xpick_data)**2. + (y-ypick_data)**2.) < e:
                index = i
                break
        if index != None:
            steps = self.Data[self.s]['zijdblock_steps']
            bad_count = self.Data[self.s]['measurement_flag'][:index].count(
                'b')
            if index > len(steps):
                bad_count *= 2
            if not self.current_fit:
                self.on_btn_add_fit(event)
            self.select_bounds_in_logger((index+bad_count) % len(steps))

    def on_zijd_mark(self, event):
        """
        Get mouse position on double right click find the interpretation in
        range of mouse
        position then mark that interpretation bad or good

        Parameters
        ----------
        event : the wx Mouseevent for that click

        Alters
        ------
        current_fit
        """
        if not array(self.CART_rot).any():
            return
        pos = event.GetPosition()
        width, height = self.canvas1.get_width_height()
        pos[1] = height - pos[1]
        xpick_data, ypick_data = pos
        xdata_org = list(self.CART_rot[:, 0]) + list(self.CART_rot[:, 0])
        ydata_org = list(-1*self.CART_rot[:, 1]) + list(-1*self.CART_rot[:, 2])
        data_corrected = self.zijplot.transData.transform(
            vstack([xdata_org, ydata_org]).T)
        xdata, ydata = data_corrected.T
        xdata = list(map(float, xdata))
        ydata = list(map(float, ydata))
        e = 4e0

        index = None
        for i, (x, y) in enumerate(zip(xdata, ydata)):
            if 0 < sqrt((x-xpick_data)**2. + (y-ypick_data)**2.) < e:
                index = i
                break
        if index != None:
            steps = self.Data[self.s]['zijdblock']
            if self.Data[self.s]['measurement_flag'][index % len(steps)] == "g":
                self.mark_meas_bad(index % len(steps))
            else:
                self.mark_meas_good(index % len(steps))
            pmag.magic_write(os.path.join(
                self.WD, "magic_measurements.txt"), self.mag_meas_data, "magic_measurements")

            self.recalculate_current_specimen_interpreatations()

            if self.ie_open:
                self.ie.update_current_fit_data()
            self.calculate_high_levels_data()
            self.update_selection()

    def right_click_specimen_equalarea(self, event):
        """
        toggles between zoom and pan effects for the specimen equal area on
        right click

        Parameters
        ----------
        event : the wx.MouseEvent that triggered the call of this function

        Alters
        ------
        specimen_EA_setting, toolbar2 setting
        """
        if event.LeftIsDown() or event.ButtonDClick():
            return
        elif self.specimen_EA_setting == "Zoom":
            self.specimen_EA_setting = "Pan"
            try:
                self.toolbar2.pan('off')
            except TypeError:
                pass
        elif self.specimen_EA_setting == "Pan":
            self.specimen_EA_setting = "Zoom"
            try:
                self.toolbar2.zoom()
            except TypeError:
                pass

    def home_specimen_equalarea(self, event):
        """
        returns the equal specimen area plot to it's original position

        Parameters
        ----------
        event : the wx.MouseEvent that triggered the call of this function

        Alters
        ------
        toolbar2 setting
        """
        self.toolbar2.home()

    def on_change_specimen_mouse_cursor(self, event):
        """
        If mouse is over data point making it selectable change the shape of
        the cursor

        Parameters
        ----------
        event : the wx Mouseevent for that click
        """
        if not self.specimen_EA_xdata or not self.specimen_EA_ydata:
            return
        pos = event.GetPosition()
        width, height = self.canvas2.get_width_height()
        pos[1] = height - pos[1]
        xpick_data, ypick_data = pos
        xdata_org = self.specimen_EA_xdata
        ydata_org = self.specimen_EA_ydata
        data_corrected = self.specimen_eqarea.transData.transform(
            vstack([xdata_org, ydata_org]).T)
        xdata, ydata = data_corrected.T
        xdata = list(map(float, xdata))
        ydata = list(map(float, ydata))
        e = 4e0

        if self.specimen_EA_setting == "Zoom":
            self.canvas2.SetCursor(wx.Cursor(wx.CURSOR_CROSS))
        else:
            self.canvas2.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
        for i, (x, y) in enumerate(zip(xdata, ydata)):
            if 0 < sqrt((x-xpick_data)**2. + (y-ypick_data)**2.) < e:
                self.canvas2.SetCursor(wx.Cursor(wx.CURSOR_HAND))
                break
        event.Skip()

    def on_equalarea_specimen_select(self, event):
        """
        Get mouse position on double click find the nearest interpretation
        to the mouse
        position then select that interpretation

        Parameters
        ----------
        event : the wx Mouseevent for that click

        Alters
        ------
        current_fit
        """
        if not self.specimen_EA_xdata or not self.specimen_EA_ydata:
            return
        pos = event.GetPosition()
        width, height = self.canvas2.get_width_height()
        pos[1] = height - pos[1]
        xpick_data, ypick_data = pos
        xdata_org = self.specimen_EA_xdata
        ydata_org = self.specimen_EA_ydata
        data_corrected = self.specimen_eqarea.transData.transform(
            vstack([xdata_org, ydata_org]).T)
        xdata, ydata = data_corrected.T
        xdata = list(map(float, xdata))
        ydata = list(map(float, ydata))
        e = 4e0

        index = None
        for i, (x, y) in enumerate(zip(xdata, ydata)):
            if 0 < sqrt((x-xpick_data)**2. + (y-ypick_data)**2.) < e:
                index = i
                break
        if index != None:
            self.fit_box.SetSelection(index)
            self.draw_figure(self.s, True)
            self.on_select_fit(event)

    def right_click_high_equalarea(self, event):
        """
        toggles between zoom and pan effects for the high equal area on
        right click

        Parameters
        ----------
        event : the wx.MouseEvent that triggered the call of this function

        Alters
        ------
        high_EA_setting, toolbar4 setting
        """
        if event.LeftIsDown():
            return
        elif self.high_EA_setting == "Zoom":
            self.high_EA_setting = "Pan"
            try:
                self.toolbar4.pan('off')
            except TypeError:
                pass
        elif self.high_EA_setting == "Pan":
            self.high_EA_setting = "Zoom"
            try:
                self.toolbar4.zoom()
            except TypeError:
                pass

    def home_high_equalarea(self, event):
        """
        returns high equal area to it's original position

        Parameters
        ----------
        event : the wx.MouseEvent that triggered the call of this function

        Alters
        ------
        toolbar4 setting
        """
        self.toolbar4.home()

    def on_change_high_mouse_cursor(self, event):
        """
        If mouse is over data point making it selectable change the shape of
        the cursor

        Parameters
        ----------
        event : the wx Mouseevent for that click
        """
        if self.ie_open and self.ie.show_box.GetValue() != "specimens":
            return
        pos = event.GetPosition()
        width, height = self.canvas4.get_width_height()
        pos[1] = height - pos[1]
        xpick_data, ypick_data = pos
        xdata_org = self.high_EA_xdata
        ydata_org = self.high_EA_ydata
        data_corrected = self.high_level_eqarea.transData.transform(
            vstack([xdata_org, ydata_org]).T)
        xdata, ydata = data_corrected.T
        xdata = list(map(float, xdata))
        ydata = list(map(float, ydata))
        e = 4e0

        if self.high_EA_setting == "Zoom":
            self.canvas4.SetCursor(wx.Cursor(wx.CURSOR_CROSS))
        else:
            self.canvas4.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
        if not self.high_EA_xdata or not self.high_EA_ydata:
            return
        for i, (x, y) in enumerate(zip(xdata, ydata)):
            if 0 < sqrt((x-xpick_data)**2. + (y-ypick_data)**2.) < e:
                self.canvas4.SetCursor(wx.Cursor(wx.CURSOR_HAND))
                break
        event.Skip()

    def on_equalarea_high_select(self, event, fig=None, canvas=None):
        """
        Get mouse position on double click find the nearest interpretation
        to the mouse position then select that interpretation

        Parameters
        ----------
        event : the wx Mouseevent for that click

        Alters
        ------
        current_fit, s, mean_fit, fit_box selection, mean_fit_box selection,
        specimens_box selection, tmin_box selection, tmax_box selection
        """
        if self.ie_open and self.ie.show_box.GetValue() != "specimens":
            return
        if not self.high_EA_xdata or not self.high_EA_ydata:
            return
        if fig == None:
            fig = self.high_level_eqarea
        if canvas == None:
            canvas = self.canvas4
        pos = event.GetPosition()
        width, height = canvas.get_width_height()
        pos[1] = height - pos[1]
        xpick_data, ypick_data = pos
        xdata_org = self.high_EA_xdata
        ydata_org = self.high_EA_ydata
        data_corrected = fig.transData.transform(
            vstack([xdata_org, ydata_org]).T)
        xdata, ydata = data_corrected.T
        xdata = list(map(float, xdata))
        ydata = list(map(float, ydata))
        e = 4e0

        index = None
        for i, (x, y) in enumerate(zip(xdata, ydata)):
            if 0 < sqrt((x-xpick_data)**2. + (y-ypick_data)**2.) < e:
                index = i
                break
        if index != None:
            disp_fit_name = self.mean_fit_box.GetValue()

            if self.level_box.GetValue() == 'sample':
                high_level_type = 'samples'
            if self.level_box.GetValue() == 'site':
                high_level_type = 'sites'
            if self.level_box.GetValue() == 'location':
                high_level_type = 'locations'
            if self.level_box.GetValue() == 'study':
                high_level_type = 'study'

            high_level_name = str(self.level_names.GetValue())
            calculation_type = str(self.mean_type_box.GetValue())
            elements_type = self.UPPER_LEVEL_SHOW

            elements_list = self.Data_hierarchy[high_level_type][high_level_name][elements_type]

            new_fit_index = 0
            for i, specimen in enumerate(elements_list):
                if disp_fit_name == "All" and \
                   specimen in self.pmag_results_data[elements_type]:
                    l = 0
                    for fit in self.pmag_results_data[elements_type][specimen]:
                        l += 1
                else:
                    try:
                        disp_fit_index = map(
                            lambda x: x.name, self.pmag_results_data[elements_type][specimen]).index(disp_fit_name)
                        if self.pmag_results_data[elements_type][specimen][disp_fit_index] in self.bad_fits:
                            l = 0
                        else:
                            l = 1
                    except IndexError:
                        l = 0
                    except KeyError:
                        l = 0
                    except ValueError:
                        l = 0

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
            if disp_fit_name != "All":
                self.mean_fit = self.current_fit.name
                self.mean_fit_box.SetSelection(2+new_fit_index)
                self.update_selection()
            else:
                self.Add_text()
            if self.ie_open:
                self.ie.change_selected(self.current_fit)

    def right_click_MM0(self, event):
        if self.MM0_setting == "Zoom":
            self.MM0_setting = "Pan"
            self.toolbar3.pan()
        elif self.MM0_setting == "Pan":
            self.MM0_setting = "Zoom"
            self.toolbar3.zoom()

    def home_MM0(self, event):
        self.toolbar3.home()

    #---------------------------------------------#
    # Measurement ListControl Functions
    #---------------------------------------------#

    def Add_text(self):
        """
        Add measurement data lines to the text window.
        """
        self.selected_meas = []
        if self.COORDINATE_SYSTEM == 'geographic':
            zijdblock = self.Data[self.s]['zijdblock_geo']
        elif self.COORDINATE_SYSTEM == 'tilt-corrected':
            zijdblock = self.Data[self.s]['zijdblock_tilt']
        else:
            zijdblock = self.Data[self.s]['zijdblock']

        tmin_index, tmax_index = -1, -1
        if self.current_fit and self.current_fit.tmin and self.current_fit.tmax:
            tmin_index, tmax_index = self.get_indices(self.current_fit)

        TEXT = ""
        self.logger.DeleteAllItems()
        for i in range(len(zijdblock)):
            lab_treatment = self.Data[self.s]['zijdblock_lab_treatments'][i]
            Step = ""
            methods = lab_treatment.split('-')
            if "NO" in methods:
                Step = "N"
            elif "AF" in methods:
                Step = "AF"
            elif "ARM" in methods:
                Step = "ARM"
            elif "IRM" in methods:
                Step = "IRM"
            elif "T" in methods:
                Step = "T"
            elif "LT" in methods:
                Step = "LT"
            Tr = zijdblock[i][0]
            Dec = zijdblock[i][1]
            Inc = zijdblock[i][2]
            Int = zijdblock[i][3]
            csd = self.Data[self.s]['csds'][i]
            self.logger.InsertItem(i, "%i" % i)
            self.logger.SetItem(i, 1, Step)
            self.logger.SetItem(i, 2, "%.1f" % Tr)
            self.logger.SetItem(i, 3, "%.1f" % Dec)
            self.logger.SetItem(i, 4, "%.1f" % Inc)
            self.logger.SetItem(i, 5, "%.2e" % Int)
            self.logger.SetItem(i, 6, csd)
            self.logger.SetItemBackgroundColour(i, "WHITE")
            if i >= tmin_index and i <= tmax_index:
                self.logger.SetItemBackgroundColour(i, "LIGHT BLUE")
            if self.Data[self.s]['measurement_flag'][i] == 'b':
                self.logger.SetItemBackgroundColour(i, "red")

    def on_click_listctrl(self, event):
        if not self.current_fit:
            self.on_btn_add_fit(event)

        index = int(event.GetText())
        self.select_bounds_in_logger(index)
        self.selected_meas = []
        self.plot_selected_meas()

    def select_bounds_in_logger(self, index):
        """
        sets index as the upper or lower bound of a fit based on what the
        other bound is and selects it in the logger. Requires 2 calls to
        completely update a interpretation. NOTE: Requires an interpretation
        to exist before it is called.

        Parameters
        ----------
        index : index of the step to select in the logger
        """
        tmin_index, tmax_index = "", ""
        if str(self.tmin_box.GetValue()) != "":
            tmin_index = self.tmin_box.GetSelection()
        if str(self.tmax_box.GetValue()) != "":
            tmax_index = self.tmax_box.GetSelection()

        if self.list_bound_loc != 0:
            if self.list_bound_loc == 1:
                if index < tmin_index:
                    self.tmin_box.SetSelection(index)
                    self.tmax_box.SetSelection(tmin_index)
                elif index == tmin_index:
                    pass
                else:
                    self.tmax_box.SetSelection(index)
            else:
                if index > tmax_index:
                    self.tmin_box.SetSelection(tmax_index)
                    self.tmax_box.SetSelection(index)
                elif index == tmax_index:
                    pass
                else:
                    self.tmin_box.SetSelection(index)
            self.list_bound_loc = 0
        else:
            if index < tmax_index:
                self.tmin_box.SetSelection(index)
                self.list_bound_loc = 1
            else:
                self.tmax_box.SetSelection(index)
                self.list_bound_loc = 2

#        if tmin_index=="" or index<tmin_index:
#            if tmax_index=="" and tmin_index!="":
#                self.tmax_box.SetSelection(tmin_index)
#            self.tmin_box.SetSelection(index)
#        elif tmax_index=="" or index>tmax_index:
#            self.tmax_box.SetSelection(index)
#        else:
#            self.tmin_box.SetSelection(index)
#            self.tmax_box.SetValue("")

        self.logger.Select(index, on=0)
        self.get_new_PCA_parameters(-1)

    def on_right_click_listctrl(self, event):
        """
        right click on the listctrl toggles measurement bad
        """
        g_index = event.GetIndex()

        if self.Data[self.s]['measurement_flag'][g_index] == 'g':
            self.mark_meas_bad(g_index)
        else:
            self.mark_meas_good(g_index)

        if self.data_model == 3.0:
            self.con.tables['measurements'].write_magic_file(dir_path=self.WD)
        else:
            pmag.magic_write(os.path.join(
                self.WD, "magic_measurements.txt"), self.mag_meas_data, "magic_measurements")

        self.recalculate_current_specimen_interpreatations()

        if self.ie_open:
            self.ie.update_current_fit_data()
        self.calculate_high_levels_data()
        self.update_selection()

    def on_select_measurement(self, event):
        self.selected_meas = []
        next_i = self.logger.GetNextSelected(-1)
        if next_i == -1:
            return
        while next_i != -1:
            self.selected_meas.append(next_i)
            next_i = self.logger.GetNextSelected(next_i)
        if self.selected_meas_called:
            return
        self.selected_meas_called = True
        wx.CallAfter(self.plot_selected_meas)
        wx.CallAfter(self.turn_off_repeat_variables)

    def turn_off_repeat_variables(self):
        self.selected_meas_called = False

    #---------------------------------------------#
    # ComboBox Functions
    #---------------------------------------------#

    def onSelect_specimen(self, event):
        """
        update figures and text when a new specimen is selected
        """
        self.selected_meas = []
        self.select_specimen(str(self.specimens_box.GetValue()))
        if self.ie_open:
            self.ie.change_selected(self.current_fit)
        self.update_selection()

    def on_enter_specimen(self, event):
        """
        upon enter on the specimen box it makes that specimen the current
        specimen
        """
        new_specimen = self.specimens_box.GetValue()
        if new_specimen not in self.specimens:
            self.user_warning(
                "%s is not a valid specimen with measurement data, aborting" % (new_specimen))
            self.specimens_box.SetValue(self.s)
            return
        self.select_specimen(new_specimen)
        if self.ie_open:
            self.ie.change_selected(self.current_fit)
        self.update_selection()

    def onSelect_coordinates(self, event):
        old = self.COORDINATE_SYSTEM
        new = self.coordinates_box.GetValue()
        if new == 'geographic' and len(self.Data[self.s]['zijdblock_geo']) == 0:
            self.coordinates_box.SetStringSelection(old)
            print(("-E- ERROR: could not switch to geographic coordinates reverting back to " + old + " coordinates"))
        elif new == 'tilt-corrected' and len(self.Data[self.s]['zijdblock_tilt']) == 0:
            self.coordinates_box.SetStringSelection(old)
            print(("-E- ERROR: could not switch to tilt-corrected coordinates reverting back to " + old + " coordinates"))
        else:
            self.COORDINATE_SYSTEM = new

        for specimen in list(self.pmag_results_data['specimens'].keys()):
            for fit in self.pmag_results_data['specimens'][specimen]:
                fit.put(specimen, self.COORDINATE_SYSTEM, self.get_PCA_parameters(
                    specimen, fit, fit.tmin, fit.tmax, self.COORDINATE_SYSTEM, fit.PCA_type))

        if self.ie_open:
            self.ie.coordinates_box.SetStringSelection(new)
            self.ie.update_editor()
        self.update_selection()

    def onSelect_orthogonal_box(self, event):
        self.clear_boxes()
        self.Add_text()
        self.update_selection()
        if self.current_fit:
            if self.current_fit.get(self.COORDINATE_SYSTEM):
                self.update_GUI_with_new_interpretation()

    def on_select_specimen_mean_type_box(self, event):
        self.get_new_PCA_parameters(event)
        if self.ie_open:
            self.ie.update_logger_entry(self.ie.current_fit_index)

    def get_new_PCA_parameters(self, event):
        """
        calculate statistics when temperatures are selected
        or PCA type is changed
        """

        tmin = str(self.tmin_box.GetValue())
        tmax = str(self.tmax_box.GetValue())
        if tmin == "" or tmax == "":
            return

        if tmin in self.T_list and tmax in self.T_list and \
           (self.T_list.index(tmax) <= self.T_list.index(tmin)):
            return

        PCA_type = self.PCA_type_box.GetValue()
        if PCA_type == "line":
            calculation_type = "DE-BFL"
        elif PCA_type == "line-anchored":
            calculation_type = "DE-BFL-A"
        elif PCA_type == "line-with-origin":
            calculation_type = "DE-BFL-O"
        elif PCA_type == "Fisher":
            calculation_type = "DE-FM"
        elif PCA_type == "plane":
            calculation_type = "DE-BFP"
        coordinate_system = self.COORDINATE_SYSTEM
        if self.current_fit:
            self.current_fit.put(self.s, coordinate_system, self.get_PCA_parameters(
                self.s, self.current_fit, tmin, tmax, coordinate_system, calculation_type))
        if self.ie_open:
            self.ie.update_current_fit_data()
        self.update_GUI_with_new_interpretation()

    def onSelect_mean_type_box(self, event):
        # calculate high level data
        if self.UPPER_LEVEL_SHOW != "specimens" or self.mean_fit_box.GetValue() == 'None':
            self.clear_high_level_pars()
            self.mean_type_box.SetValue("None")
            return
        self.calculate_high_levels_data()
        self.update_high_level_stats()
        self.plot_high_level_means()
        self.canvas4.draw()
        if self.ie_open:
            self.ie.draw()

    def onSelect_mean_fit_box(self, event):
        if self.mean_fit_box.GetValue() == 'None' and self.mean_type_box.GetValue() != 'None':
            self.mean_type_box.SetValue('None')
        # get new fit to display
        new_fit = self.mean_fit_box.GetValue()
        self.mean_fit = new_fit
        if self.ie_open:
            self.ie.mean_fit_box.SetStringSelection(new_fit)
        # calculate high level data
        self.calculate_high_levels_data()
        self.plot_high_levels_data()

    def onSelect_high_level(self, event, called_by_interp_editor=False):
        self.UPPER_LEVEL = self.level_box.GetValue()
        if self.UPPER_LEVEL == 'sample':
            if self.ie_open:
                self.ie.show_box.SetItems(['specimens'])
                self.ie.show_box.SetValue('specimens')
            if self.UPPER_LEVEL_SHOW not in ['specimens']:
                self.UPPER_LEVEL_SHOW = 'specimens'
            self.level_names.SetItems(self.samples)
            self.level_names.SetStringSelection(
                self.Data_hierarchy['sample_of_specimen'][self.s])

        elif self.UPPER_LEVEL == 'site':
            if self.ie_open:
                self.ie.show_box.SetItems(['specimens', 'samples'])
                if self.ie.show_box.GetValue() not in ['specimens', 'samples']:
                    self.ie.show_box.SetValue('specimens')
            if self.UPPER_LEVEL_SHOW not in ['specimens', 'samples']:
                self.UPPER_LEVEL_SHOW = 'specimens'
            self.level_names.SetItems(self.sites)
            self.level_names.SetStringSelection(
                self.Data_hierarchy['site_of_specimen'][self.s])

        elif self.UPPER_LEVEL == 'location':
            if self.ie_open:
                # ,'sites VGP'])
                self.ie.show_box.SetItems(['specimens', 'samples', 'sites'])
                # ,'sites VGP']:
                if self.ie.show_box.GetValue() not in ['specimens', 'samples', 'sites']:
                    self.ie.show_box.SetValue(self.UPPER_LEVEL_SHOW)
            self.level_names.SetItems(self.locations)
            self.level_names.SetStringSelection(
                self.Data_hierarchy['location_of_specimen'][self.s])

        elif self.UPPER_LEVEL == 'study':
            if self.ie_open:
                # ,'sites VGP'])
                self.ie.show_box.SetItems(['specimens', 'samples', 'sites'])
                # ,'sites VGP']:
                if self.ie.show_box.GetValue() not in ['specimens', 'samples', 'sites']:
                    self.ie.show_box.SetValue(self.UPPER_LEVEL_SHOW)
            self.level_names.SetItems(['this study'])
            self.level_names.SetStringSelection('this study')

        if not called_by_interp_editor:
            if self.ie_open:
                self.ie.level_box.SetStringSelection(self.UPPER_LEVEL)
                self.ie.on_select_high_level(event, True)
            else:
                self.update_selection()

    def onSelect_level_name(self, event, called_by_interp_editor=False):
        high_level_name = str(self.level_names.GetValue())

        if self.level_box.GetValue() == 'sample':
            specimen_list = self.Data_hierarchy['samples'][high_level_name]['specimens']
        if self.level_box.GetValue() == 'site':
            specimen_list = self.Data_hierarchy['sites'][high_level_name]['specimens']
        if self.level_box.GetValue() == 'location':
            specimen_list = self.Data_hierarchy['locations'][high_level_name]['specimens']
        if self.level_box.GetValue() == 'study':
            specimen_list = self.Data_hierarchy['study']['this study']['specimens']

        if self.s not in specimen_list:
            specimen_list.sort(key=spec_key_func)
            self.select_specimen(str(specimen_list[0]))
            self.specimens_box.SetStringSelection(str(self.s))

        if self.ie_open and not called_by_interp_editor:
            self.ie.level_names.SetStringSelection(high_level_name)
            self.ie.on_select_level_name(event, True)

        self.update_selection()

    def on_select_plane_display_box(self, event):
        if "best fit vector" in self.plane_display_box.GetValue():
            self.calculate_best_fit_vectors()
        self.update_fit_bounds_and_statistics()
        self.draw_figure(self.s, True)
        self.draw_interpretations()
        self.plot_high_levels_data()

    def on_select_fit(self, event):
        """
        Picks out the fit selected in the fit combobox and sets it to the
        current fit of the GUI then calls the select function of the fit to
        set the GUI's bounds boxes and alter other such parameters

        Parameters
        ----------
        event : the wx.ComboBoxEvent that triggers this function

        Alters
        ------
        current_fit, fit_box selection, tmin_box selection, tmax_box
        selection
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
                fit_num = list(
                    map(lambda x: x.name, self.pmag_results_data['specimens'][self.s])).index(fit_val)
            except ValueError:
                fit_num = -1
            self.pmag_results_data['specimens'][self.s][fit_num].select()
        if self.ie_open:
            self.ie.change_selected(self.current_fit)

    def on_enter_fit_name(self, event):
        """
        Allows the entering of new fit names in the fit combobox

        Parameters
        ----------
        event : the wx.ComboBoxEvent that triggers this function

        Alters
        ------
        current_fit.name
        """
        if self.current_fit == None:
            self.on_btn_add_fit(event)
        value = self.fit_box.GetValue()
        if ':' in value:
            name, color = value.split(':')
        else:
            name, color = value, None
        if name in [x.name for x in self.pmag_results_data['specimens'][self.s]]:
            print('bad name')
            return
        self.current_fit.name = name
        if color in list(self.color_dict.keys()):
            self.current_fit.color = self.color_dict[color]
        self.update_fit_boxes()
        self.plot_high_levels_data()

    #---------------------------------------------#
    # Button Functions
    #---------------------------------------------#

    def on_save_interpretation_button(self, event):
        """
        on the save button the interpretation is saved to pmag_results_table
        data in all coordinate systems
        """

        if self.current_fit:
            self.current_fit.saved = True
            calculation_type = self.current_fit.get(self.COORDINATE_SYSTEM)[
                'calculation_type']
            tmin = str(self.tmin_box.GetValue())
            tmax = str(self.tmax_box.GetValue())

            self.current_fit.put(self.s, 'specimen', self.get_PCA_parameters(
                self.s, self.current_fit, tmin, tmax, 'specimen', calculation_type))
            if len(self.Data[self.s]['zijdblock_geo']) > 0:
                self.current_fit.put(self.s, 'geographic', self.get_PCA_parameters(
                    self.s, self.current_fit, tmin, tmax, 'geographic', calculation_type))
            if len(self.Data[self.s]['zijdblock_tilt']) > 0:
                self.current_fit.put(self.s, 'tilt-corrected', self.get_PCA_parameters(
                    self.s, self.current_fit, tmin, tmax, 'tilt-corrected', calculation_type))

        # calculate high level data
        self.calculate_high_levels_data()
        self.plot_high_levels_data()
        self.on_menu_save_interpretation(event)
        self.update_selection()
        self.close_warning = True

    def on_btn_add_fit(self, event):
        """
        add a new interpretation to the current specimen

        Parameters
        ----------
        event : the wx.ButtonEvent that triggered this function

        Alters
        ------
        pmag_results_data
        """
        if self.auto_save.GetValue():
            self.current_fit = self.add_fit(self.s, None, None, None, saved=True)
        else:
            self.current_fit = self.add_fit(self.s, None, None, None, saved=False)
        self.generate_warning_text()
        self.update_warning_box()

        if self.ie_open:
            self.ie.update_editor()

        self.update_fit_boxes(True)
        # Draw figures and add  text
        self.get_new_PCA_parameters(event)

    def on_btn_delete_fit(self, event):
        """
        removes the current interpretation

        Parameters
        ----------
        event : the wx.ButtonEvent that triggered this function
        """
        self.delete_fit(self.current_fit, specimen=self.s)

    def on_btn_info_click(self, event):
        """
        Show popup info window when user clicks "?"
        """
        def on_close(event, wind):
            wind.Close()
            wind.Destroy()
        event.Skip()
        wind = wx.PopupTransientWindow(self, wx.RAISED_BORDER)
        if self.auto_save.GetValue():
            info = "'auto-save' is currently selected. Temperature bounds will be saved when you click 'next' or 'back'."
        else:
            info = "'auto-save' is not selected.  Temperature bounds will only be saved when you click 'save'."
        text = wx.StaticText(wind, -1, info)
        box = wx.StaticBox(wind, -1, 'Info:')
        boxSizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        boxSizer.Add(text, 5, wx.ALL | wx.CENTER)
        exit_btn = wx.Button(wind, wx.ID_EXIT, 'Close')
        wind.Bind(wx.EVT_BUTTON, lambda evt: on_close(evt, wind), exit_btn)
        boxSizer.Add(exit_btn, 5, wx.ALL | wx.CENTER)
        wind.SetSizer(boxSizer)
        wind.Layout()
        wind.Popup()


    def do_auto_save(self):
        """
        Delete current fit if auto_save==False,
        unless current fit has explicitly been saved.
        """
        if not self.auto_save.GetValue():
            if self.current_fit:
                if not self.current_fit.saved:
                    self.delete_fit(self.current_fit, specimen=self.s)


    def on_next_button(self, event):
        """
        update figures and text when a next button is selected
        """
        self.do_auto_save()
        self.selected_meas = []
        index = self.specimens.index(self.s)
        try:
            fit_index = self.pmag_results_data['specimens'][self.s].index(
                self.current_fit)
        except KeyError:
            fit_index = None
        except ValueError:
            fit_index = None
        if index == len(self.specimens)-1:
            index = 0
        else:
            index += 1
        # sets self.s calculates params etc.
        self.initialize_CART_rot(str(self.specimens[index]))
        self.specimens_box.SetStringSelection(str(self.s))
        if fit_index != None and self.s in self.pmag_results_data['specimens']:
            try:
                self.current_fit = self.pmag_results_data['specimens'][self.s][fit_index]
            except IndexError:
                self.current_fit = None
        else:
            self.current_fit = None
        if self.ie_open:
            self.ie.change_selected(self.current_fit)
        self.update_selection()

    def on_prev_button(self, event):
        """
        update figures and text when a next button is selected
        """
        self.do_auto_save()
        self.selected_meas = []
        index = self.specimens.index(self.s)
        try:
            fit_index = self.pmag_results_data['specimens'][self.s].index(
                self.current_fit)
        except KeyError:
            fit_index = None
        except ValueError:
            fit_index = None
        if index == 0:
            index = len(self.specimens)
        index -= 1
        # sets self.s calculates params etc.
        self.initialize_CART_rot(str(self.specimens[index]))
        self.specimens_box.SetStringSelection(str(self.s))
        if fit_index != None and self.s in self.pmag_results_data['specimens']:
            try:
                self.current_fit = self.pmag_results_data['specimens'][self.s][fit_index]
            except IndexError:
                self.current_fit = None
        else:
            self.current_fit = None
        if self.ie_open:
            self.ie.change_selected(self.current_fit)
        self.update_selection()

    def on_select_stats_button(self, events):
        i = self.switch_stats_button.GetValue()
        self.update_high_level_stats()

#==========================================================================================#
#==============================GUI Status Functions========================================#
#==========================================================================================#

    def __str__(self):
        out_str = ""
        out_str += "Demag_GUI instance: %s\n" % (hex(id(self)))
        out_str += "Global Variables\n"
        out_str += "\tcoordinate system: %s\n" % (self.COORDINATE_SYSTEM)
        num_interp = self.total_num_of_interpertations()
        out_str += "\tthere are %d interpretations in pmag_results\n" % (
            num_interp)
        out_str += "Current Specimen and Interpretation\n"
        if self.current_fit != None:
            out_str += "\tcurrent fit is: %s for specimen %s\n" % (
                self.current_fit.name, self.s)
            out_str += "\tvalues of this interpretation for coordinate system %s\n" % (
                self.COORDINATE_SYSTEM)
            pars = self.current_fit.get(self.COORDINATE_SYSTEM)
            out_str += str(pars)
        else:
            out_str += "\tcurrent fit is: %s for specimen %s\n" % (
                "None", self.s)
        return out_str

    def get_test_mode(self):
        return self.test_mode

    def total_num_of_interpertations(self):
        num_interp = 0
        for specimen in self.specimens:
            if specimen in self.pmag_results_data['specimens']:
                num_interp += len(
                    self.pmag_results_data['specimens'][specimen])
        return num_interp

# --------------------------------------------------------------
# Run the GUI
# --------------------------------------------------------------


def start(WD=None, standalone_app=True, parent=None, write_to_log_file=True,
          DM=None, meas_file=None):
    # to run as module:
    if not standalone_app:
        disableAll = wx.WindowDisabler()
        frame = Demag_GUI(
            WD, parent, write_to_log_file=write_to_log_file,
            data_model=DM, meas_file=meas_file)
        frame.Center()
        frame.Show()
        frame.Raise()
    # to run as command_line:
    else:
        app = wx.App()
        app.frame = Demag_GUI(
            WD, write_to_log_file=write_to_log_file, data_model=DM,
            meas_file=meas_file)
        app.frame.Center()
        app.frame.Show()
        app.MainLoop()


def main():
    if "-h" in sys.argv:
        help(__name__)
        sys.exit()
    write_to_log_file = True
    if '-v' in sys.argv or '--verbose' in sys.argv:
        write_to_log_file = False
    else:
        print('-I- You are in log mode.')
        print('    You can check your log output in "demag_gui.log"')
        print('    If you prefer verbose output to your Terminal/Command prompt, run "demag_gui.py -v"')

    WD = None
    if "-WD" in sys.argv:
        ind = sys.argv.index('-WD')
        WD = sys.argv[ind+1]
    data_model = None
    if '-DM' in sys.argv:
        dm_index = sys.argv.index('-DM')
        if len(sys.argv) >= dm_index+2:
            data_model = sys.argv[dm_index+1]
    meas_file = pmag.get_named_arg('-f')
    start(WD=WD, write_to_log_file=write_to_log_file, DM=data_model, meas_file=meas_file)


if __name__ == '__main__':
    main()

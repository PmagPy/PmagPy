#!/usr/bin/env pythonw
"""
Runs Thellier GUI PmagPy's main analysis GUI for thellier-type
paleointensity data. This can be used to obtain intensities for Thermal and
Microwave data. It allows export of figures and analysis results for upload
to the MagIC database and/or publication. For more information on how to
interpret or use the GUI's many functions see the Help menu in the open GUI.
More documentation can be found on all of PmagPy's functionality at the
PmagPy cookbook which can be found here: earthref.org/PmagPy/cookbook/

SYNTAX
    thellier_gui.py [command line options]
    # or, for Anaconda users:
    thellier_gui_anaconda [command line options]


OPTIONS
    -h : opens this help message
    -WD : specify working directory
    -DM : specify MagIC data model (options : 3 or 2.x)

AUTHORS
    Ron Shaar and Lisa Tauxe
"""
#=========================================================================
# LOG HEADER:
#=========================================================================
# Version 3.1 8/11/16 (Lisa Tauxe)
#    Fixed code for importing criteria file in data model 3.0
# TODO:
#    1) need to thoroughly test and finalize output format (esp.  vdms/vadms)
#    2) add result_quality flag to specimens, samples, sites tables based on criteria
#    3) rename code thellier_gui.py
#
# Thellier_GUI Version 3.0  8/2/16 (Lisa Tauxe)
# Adding in the ability to read in and write out
# Data model 3.0 data sets
# so far for command line option -DM 3 (program works the same as always for no -DM switch):
#   1) data read in as 3.0  and converted to 2.5
#   2) acceptance criteria read in and converted to 2.5
#   3) previous interpretations read  in  and converted to 2.5
#   4) saves acceptance criteria in data model 3.0
#   5) reads in age, lat, lon into data_info - makes plots
#   6) does the anisotropy calculation and saves to specimens.txt in 3.0
#   7) does cooling rate calculation
#   8) does  NLT correction
#   9) saves specimen data to specimens.txt in 3.0
#   10) saves samples/sites tables in 3.0 format
#
# Thellier_GUI Version 2.29 01/29/2015
# 1) fix STDEV-OPT extended error bar plor display bug
# 2) fix paleointensity plot legend when using extended error bars
# 3) fix non-thellier pmag_specimen competability issue

# Thellier_GUI Version 2.28 12/31/2014
# Fix minor bug in delete interpretation button
#
# Thellier_GUI Version 2.27 11/30/2014
#
# Fix in_sigma bug in change criteria dialog box
#
# Thellier_GUI Version 2.26 11/16/2014
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
# Resize acceptance criteria dialog window
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
#=========================================================================

global CURRENT_VERSION
global PMAGPY_DIRECTORY
global MICROWAVE
global THERMAL
MICROWAVE = False
THERMAL = True

#from pmag_env import set_env
# set_env.set_backend(wx=True)
import matplotlib
if not matplotlib.get_backend() == 'WXAgg':
    matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar
from pmag_env import set_env


import matplotlib.pyplot as plt
import json
import sys
import os
import copy
import pdb
from webbrowser import open as webopen
import pmagpy.pmag as pmag
#has_basemap, Basemap = pmag.import_basemap()
#if has_basemap:
#    from mpl_toolkits.basemap import shiftgrid, basemap_datadir
import pmagpy.find_pmag_dir as find_pmag_dir
import pmagpy.contribution_builder as cb
from pmagpy.mapping import map_magic
import pmagpy.controlled_vocabularies3 as cv
import pandas as pd
import numpy as np
from numpy.linalg import inv, eig
from numpy import sqrt, append
from scipy.optimize import curve_fit
import stat
import shutil
import random
import time
import wx
import wx.lib.scrolledpanel
import wx.grid
import wx.lib.agw.floatspin as FS
from dialogs import demag_dialogs
from dialogs import pmag_widgets as pw
import dialogs.thellier_consistency_test as thellier_consistency_test
import dialogs.thellier_gui_dialogs as thellier_gui_dialogs
import dialogs.thellier_gui_lib as thellier_gui_lib
import dialogs.thellier_interpreter as thellier_interpreter
import dialogs.thellier_consistency_test as thellier_consistency_test

CURRENT_VERSION = pmag.get_version()
PMAGPY_DIRECTORY = find_pmag_dir.get_pmag_dir()

matplotlib.rc('xtick', labelsize=10)
matplotlib.rc('ytick', labelsize=10)
matplotlib.rc('axes', labelsize=8)
matplotlib.rcParams['savefig.dpi'] = 300.

# https://github.com/matplotlib/matplotlib/issues/10063
#matplotlib.rcParams.update({"svg.fonttype": 'none'})

try:
    version = pmag.get_version()
except ImportError:
    version = ""
version = version + ": thellier_gui." + CURRENT_VERSION

has_basemap, Basemap = pmag.import_basemap()
has_cartopy, cartopy = pmag.import_cartopy()
if has_cartopy:
    # import some cartopy stuff
    import cartopy.crs as ccrs
    from cartopy import config
    from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
    from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
    from cartopy import feature as cfeature
    from cartopy.feature import NaturalEarthFeature, LAND, COASTLINE, OCEAN, LAKES, BORDERS
    import matplotlib.ticker as mticker



#=========================================================================


class Arai_GUI(wx.Frame):
    """
    The main frame of the application
    """
    title = "Thellier GUI version:%s" % CURRENT_VERSION

    def __init__(self, WD=None, parent=None, standalone=True, DM=0, test_mode=False, evt_quit=None):

        TEXT = """

Runs Thellier GUI PmagPy's main analysis GUI for thellier-type
paleointensity data. This can be used to obtain intensities for Thermal and
Microwave data. It allows export of figures and analysis results for upload
to the MagIC database and/or publication. For more information on how to
interpret or use the GUI's many functions see the Help menu in the open GUI.
More documentation can be found on all of PmagPy's functionality at the
PmagPy cookbook which can be found here: earthref.org/PmagPy/cookbook/

SYNTAX
    thellier_gui.py [command line options]
    # or, for Anaconda users:
    thellier_gui_anaconda [command line options]


OPTIONS
    -h : opens this help message
    -WD : specify working directory
    -DM : specify MagIC data model (options : 3 or 2.x)

AUTHORS
    Ron Shaar and Lisa Tauxe

DESCRIPTION
    GUI for interpreting thellier-type paleointensity data.
    For tutorial check PmagPy cookbook in http://earthref.org/PmagPy/cookbook/

        """
        args = sys.argv

        if "-h" in args:
            print(TEXT)
            sys.exit()
        self.standalone = standalone
        global FIRST_RUN
        FIRST_RUN = True if standalone else False
        wx.Frame.__init__(self, parent, wx.ID_ANY,
                          self.title, name='thellier gui')
        self.set_test_mode(test_mode)
        self.redo_specimens = {}
        self.evt_quit = evt_quit
        self.close_warning = False
        self.parent = parent
        self.crit_data = {}

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

        # get DM number (2 or 3)
        # if DM was provided
        if DM:
            self.data_model = int(DM)
        # otherwise try to get it from command line:
        elif '-DM' in args:
            self.data_model = int(pmag.get_named_arg('-DM', 0))
        # otherwise get it from the user
        else:
            ui_dialog = demag_dialogs.user_input(self, ['data_model'], parse_funcs=[
                                                 float], heading="Please input prefered data model (2.5,3.0).  Note: 2.5 is for legacy projects only, if you have new data please use 3.0.", values=[3])
#            res = ui_dialog.ShowModal()
            vals = ui_dialog.get_values()
            self.data_model = int(vals[1]['data_model'])

        # get working directory
        self.currentDirectory = os.getcwd()  # get the current working directory
        if WD:
            self.WD = WD
            self.get_DIR(self.WD)
        else:
            self.get_DIR()  # choose directory dialog

        # init wait dialog
        disableAll = wx.WindowDisabler()
        wait = wx.BusyInfo('Compiling required data, please wait...')
        wx.SafeYield()

        # initalize necessary variables
        self.list_bound_loc = 0

        # inialize selecting criteria
        self.acceptance_criteria = pmag.initialize_acceptance_criteria(
            data_model=self.data_model)
        self.add_thellier_gui_criteria()
        if self.data_model == 3:
            self.crit_file = 'criteria.txt'
        else:
            self.crit_file = 'pmag_criteria.txt'
        self.read_criteria_file(os.path.join(self.WD, self.crit_file))

        # preferences
        preferences = self.get_preferences()
        self.dpi = 100

        self.preferences = preferences

        self.Data, self.Data_hierarchy, self.Data_info = {}, {}, {}
        self.MagIC_directories_list = []

        # stop if there is no measurement file
        if self.data_model == 3:
            if not 'measurements.txt' in os.listdir(self.WD):
                print('-W- No measurements.txt file found in {}'.format(self.WD))
                self.on_menu_exit(-1)
                return
        elif self.data_model == 2:
            if not 'magic_measurements.txt' in os.listdir(self.WD):
                print('-W- No magic_measurements.txt file found in {}'.format(self.WD))
                self.on_menu_exit(-1)
                return

        # start grabbing data
        self.Data_info = self.get_data_info()  # get all ages, locations etc.
        # Get data from measurements and specimens or rmag_anisotropy (data
        # model 2.5 if they exist.)
        self.Data, self.Data_hierarchy = self.get_data()

        if "-tree" in sys.argv and FIRST_RUN:
            self.open_magic_tree()

        self.Data_samples = {}  # interpretations of samples are kept here
        self.Data_sites = {}  # interpretations of sites are kept here
        # self.Data_samples_or_sites={}   # interpretations of sites are kept
        # here

        self.last_saved_pars = {}
        self.specimens = list(self.Data.keys())  # get list of specimens
        self.specimens.sort()  # get list of specimens

        # dicts to contain statistic windows
        # (removes need for many exec statements)
        # self.stat_windows['scat'] is equivalent to old self.scat_window
        self.stat_windows = {}
        self.threshold_windows = {}
        self.stat_labels = {}

        self.InitUI()
        del wait
        FIRST_RUN = False

    def InitUI(self):
        # make Panels
        self.plot_panel = wx.lib.scrolledpanel.ScrolledPanel(self, wx.ID_ANY)
        self.top_panel = wx.Panel(self, wx.ID_ANY)
        self.side_panel = wx.Panel(self, wx.ID_ANY)
        self.bottom_panel = wx.Panel(self, wx.ID_ANY)
        self.Main_Frame()  # build the main frame
        self.plot_panel.SetAutoLayout(1)
        self.plot_panel.SetupScrolling()  # endable scrolling
        self.create_menu()
        self.arrow_keys()
        FIRST_RUN = False

        if self.Data:
            self.write_acceptance_criteria_to_boxes()  # write threshold values to boxes
            self.draw_figure(self.s)  # draw the figures
            self.get_previous_interpretation()  # get interpretations from specimens file
            self.Add_text(self.s)  # write measurement data to text box
        FIRST_RUN = False
        self.Bind(wx.EVT_CLOSE, self.on_menu_exit)
        self.close_warning = False
        # try to read redo file if one exists
        if os.path.exists(os.path.join(self.WD, 'thellier_GUI.redo')):
            self.read_redo_file(os.path.join(self.WD, 'thellier_GUI.redo'))
            if self.Data:
                self.get_previous_interpretation()  # get interpretations from specimens file
        if self.s:
            self.update_selection()


    def get_DIR(self, WD=None):
        """
        open dialog box for choosing a working directory
        """

        if "-WD" in sys.argv and FIRST_RUN:
            ind = sys.argv.index('-WD')
            self.WD = sys.argv[ind + 1]
        elif not WD:  # if no arg was passed in for WD, make a dialog to choose one
            dialog = wx.DirDialog(None, "Choose a directory:", defaultPath=self.currentDirectory,
                                  style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON | wx.DD_CHANGE_DIR)
            ok = self.show_dlg(dialog)
            if ok == wx.ID_OK:
                self.WD = dialog.GetPath()
            else:
                self.WD = os.getcwd()
            dialog.Destroy()
        self.WD = os.path.realpath(self.WD)
        # name measurement file
        if self.data_model == 3:
            meas_file = 'measurements.txt'
        else:
            meas_file = 'magic_measurements.txt'
        self.magic_file = os.path.join(self.WD, meas_file)
        # intialize GUI_log
        self.GUI_log = open(os.path.join(self.WD, "thellier_GUI.log"), 'w+')
        self.GUI_log.write("starting...\n")
        self.GUI_log.close()
        self.GUI_log = open(os.path.join(self.WD, "thellier_GUI.log"), 'a')
        os.chdir(self.WD)
        self.WD = os.getcwd()

    def Main_Frame(self):
        """
        Build main frame od panel: buttons, etc.
        choose the first specimen and display data
        """

        #--------------------------------------------------------------------
        # initialize first specimen in list as current specimen
        #--------------------------------------------------------------------

        try:
            self.s = self.specimens[0]
        except:
            self.s = ""
            print("No specimens during UI build")

        #--------------------------------------------------------------------
        # create main panel in the right size
        #--------------------------------------------------------------------

        dw, dh = wx.DisplaySize()
        w, h = self.GetSize()
        r1 = dw / 1250.
        r2 = dw / 750.

        GUI_RESOLUTION = min(r1, r2, 1.3)
        if 'gui_resolution' in list(self.preferences.keys()):
            if float(self.preferences['gui_resolution']) != 1:
                self.GUI_RESOLUTION = float(
                    self.preferences['gui_resolution']) / 100
            else:
                self.GUI_RESOLUTION = min(r1, r2, 1.3)
        else:
            self.GUI_RESOLUTION = min(r1, r2, 1.3)

        #--------------------------------------------------------------------
        # adjust font size
        #--------------------------------------------------------------------

        self.font_type = "Arial"
        if sys.platform.startswith("linux"):
            self.font_type = "Liberation Serif"

        if self.GUI_RESOLUTION >= 1.1 and self.GUI_RESOLUTION <= 1.3:
            font2 = wx.Font(13, wx.SWISS, wx.NORMAL,
                            wx.NORMAL, False, self.font_type)
        elif self.GUI_RESOLUTION <= 0.9 and self.GUI_RESOLUTION < 1.0:
            font2 = wx.Font(11, wx.SWISS, wx.NORMAL,
                            wx.NORMAL, False, self.font_type)
        elif self.GUI_RESOLUTION <= 0.9:
            font2 = wx.Font(10, wx.SWISS, wx.NORMAL,
                            wx.NORMAL, False, self.font_type)
        else:
            font2 = wx.Font(12, wx.SWISS, wx.NORMAL,
                            wx.NORMAL, False, self.font_type)
        print("    self.GUI_RESOLUTION", self.GUI_RESOLUTION)

        h_space = 4
        v_space = 4

        # set font size and style
        #font1 = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Comic Sans MS')
        FONT_RATIO = self.GUI_RESOLUTION + (self.GUI_RESOLUTION - 1) * 5
        font1 = wx.Font(9 + FONT_RATIO, wx.SWISS, wx.NORMAL,
                        wx.NORMAL, False, self.font_type)
        # GUI headers

        font3 = wx.Font(11 + FONT_RATIO, wx.SWISS, wx.NORMAL,
                        wx.NORMAL, False, self.font_type)
        font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT)
        font.SetPointSize(10 + FONT_RATIO)

        #--------------------------------------------------------------------
        # Create Figures and FigCanvas objects.
        #--------------------------------------------------------------------

        self.fig1 = Figure((5. * self.GUI_RESOLUTION, 5. *
                            self.GUI_RESOLUTION), dpi=self.dpi)
        self.canvas1 = FigCanvas(self.plot_panel, wx.ID_ANY, self.fig1)
        self.fig1.text(0.01, 0.98, "Arai plot", {
                       'family': self.font_type, 'fontsize': 10, 'style': 'normal', 'va': 'center', 'ha': 'left'})
        self.toolbar1 = NavigationToolbar(self.canvas1)
        self.toolbar1.Hide()
        self.fig1_setting = "Zoom"
        self.toolbar1.zoom()
        self.canvas1.Bind(wx.EVT_RIGHT_DOWN, self.on_right_click_fig)
        self.canvas1.Bind(wx.EVT_MIDDLE_DOWN, self.on_home_fig)

        self.fig2 = Figure((2.5 * self.GUI_RESOLUTION, 2.5 *
                            self.GUI_RESOLUTION), dpi=self.dpi)
        self.canvas2 = FigCanvas(self.plot_panel, wx.ID_ANY, self.fig2)
        self.fig2.text(0.02, 0.96, "Zijderveld", {
                       'family': self.font_type, 'fontsize': 10, 'style': 'normal', 'va': 'center', 'ha': 'left'})
        self.toolbar2 = NavigationToolbar(self.canvas2)
        self.toolbar2.Hide()
        self.fig2_setting = "Zoom"
        self.toolbar2.zoom()
        self.canvas2.Bind(wx.EVT_RIGHT_DOWN, self.on_right_click_fig)
        self.canvas2.Bind(wx.EVT_MIDDLE_DOWN, self.on_home_fig)

        self.fig3 = Figure((2.5 * self.GUI_RESOLUTION, 2.5 *
                            self.GUI_RESOLUTION), dpi=self.dpi)
        self.canvas3 = FigCanvas(self.plot_panel, wx.ID_ANY, self.fig3)
        #self.fig3.text(0.02,0.96,"Equal area",{'family':self.font_type, 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })
        self.toolbar3 = NavigationToolbar(self.canvas3)
        self.toolbar3.Hide()
        self.fig3_setting = "Zoom"
        self.toolbar3.zoom()
        self.canvas3.Bind(wx.EVT_RIGHT_DOWN, self.on_right_click_fig)
        self.canvas3.Bind(wx.EVT_MIDDLE_DOWN, self.on_home_fig)

        self.fig4 = Figure((2.5 * self.GUI_RESOLUTION, 2.5 *
                            self.GUI_RESOLUTION), dpi=self.dpi)
        self.canvas4 = FigCanvas(self.plot_panel, wx.ID_ANY, self.fig4)
        if self.acceptance_criteria['average_by_sample_or_site']['value'] == 'site':
            TEXT = "Site data"
        else:
            TEXT = "Sample data"
        self.fig4.text(0.02, 0.96, TEXT, {
                       'family': self.font_type, 'fontsize': 10, 'style': 'normal', 'va': 'center', 'ha': 'left'})
        self.toolbar4 = NavigationToolbar(self.canvas4)
        self.toolbar4.Hide()
        self.fig4_setting = "Zoom"
        self.toolbar4.zoom()
        self.canvas4.Bind(wx.EVT_RIGHT_DOWN, self.on_right_click_fig)
        self.canvas4.Bind(wx.EVT_MIDDLE_DOWN, self.on_home_fig)

        self.fig5 = Figure((2.5 * self.GUI_RESOLUTION, 2.5 *
                            self.GUI_RESOLUTION), dpi=self.dpi)
        self.canvas5 = FigCanvas(self.plot_panel, wx.ID_ANY, self.fig5)
        #self.fig5.text(0.02,0.96,"M/M0",{'family':self.font_type, 'fontsize':10, 'style':'normal','va':'center', 'ha':'left' })
        self.toolbar5 = NavigationToolbar(self.canvas5)
        self.toolbar5.Hide()
        self.fig5_setting = "Zoom"
        self.toolbar5.zoom()
        self.canvas5.Bind(wx.EVT_RIGHT_DOWN, self.on_right_click_fig)
        self.canvas5.Bind(wx.EVT_MIDDLE_DOWN, self.on_home_fig)

        # make axes of the figures
        self.araiplot = self.fig1.add_axes([0.1, 0.1, 0.8, 0.8])
        self.zijplot = self.fig2.add_subplot(111)
        self.eqplot = self.fig3.add_subplot(111)
        self.sampleplot = self.fig4.add_axes(
            [0.2, 0.3, 0.7, 0.6], frameon=True, facecolor='None')
        self.mplot = self.fig5.add_axes(
            [0.2, 0.15, 0.7, 0.7], frameon=True, facecolor='None')

        #--------------------------------------------------------------------
        # text box displaying measurement data
        #--------------------------------------------------------------------

        self.logger = wx.ListCtrl(self.side_panel, id=wx.ID_ANY, size=(
            100 * self.GUI_RESOLUTION, 100 * self.GUI_RESOLUTION), style=wx.LC_REPORT)
        self.logger.SetFont(font1)
        self.logger.InsertColumn(0, 'i', width=45 * self.GUI_RESOLUTION)
        self.logger.InsertColumn(1, 'Step', width=45 * self.GUI_RESOLUTION)
        self.logger.InsertColumn(2, 'Tr', width=65 * self.GUI_RESOLUTION)
        self.logger.InsertColumn(3, 'Dec', width=65 * self.GUI_RESOLUTION)
        self.logger.InsertColumn(4, 'Inc', width=65 * self.GUI_RESOLUTION)
        self.logger.InsertColumn(5, 'M', width=75 * self.GUI_RESOLUTION)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED,
                  self.on_click_listctrl, self.logger)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK,
                  self.on_right_click_listctrl, self.logger)

        #--------------------------------------------------------------------
        # select a specimen box
        #--------------------------------------------------------------------

        # Combo-box with a list of specimen
        self.specimens_box = wx.ComboBox(self.top_panel, wx.ID_ANY, self.s, (250 * self.GUI_RESOLUTION, 25),
                                         wx.DefaultSize, self.specimens, wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER, name="specimen")
        self.specimens_box.SetFont(font2)
        self.Bind(wx.EVT_COMBOBOX, self.onSelect_specimen, self.specimens_box)
        self.Bind(wx.EVT_TEXT_ENTER, self.onSelect_specimen,
                  self.specimens_box)

        # buttons to move forward and backwards from specimens
        nextbutton = wx.Button(self.top_panel, id=wx.ID_ANY, label='next', size=(
            75 * self.GUI_RESOLUTION, 25))  # ,style=wx.BU_EXACTFIT)#, size=(175, 28))
        self.Bind(wx.EVT_BUTTON, self.on_next_button, nextbutton)
        nextbutton.SetFont(font2)

        prevbutton = wx.Button(self.top_panel, id=wx.ID_ANY, label='previous', size=(
            75 * self.GUI_RESOLUTION, 25))  # ,style=wx.BU_EXACTFIT)#, size=(175, 28))
        prevbutton.SetFont(font2)
        self.Bind(wx.EVT_BUTTON, self.on_prev_button, prevbutton)

        #--------------------------------------------------------------------
        # select temperature bounds
        #--------------------------------------------------------------------

        try:
            if self.Data[self.s]['T_or_MW'] == "T":
                self.temperatures = np.array(
                    self.Data[self.s]['t_Arai']) - 273.
                self.T_list = ["%.0f" % T for T in self.temperatures]
            elif self.Data[self.s]['T_or_MW'] == "MW":
                self.temperatures = np.array(self.Data[self.s]['t_Arai'])
                self.T_list = ["%.0f" % T for T in self.temperatures]
        except (ValueError, TypeError, KeyError) as e:
            self.T_list = []

        self.tmin_box = wx.ComboBox(self.top_panel, wx.ID_ANY, size=(
            100 * self.GUI_RESOLUTION, 25), choices=self.T_list, style=wx.CB_DROPDOWN | wx.TE_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.get_new_T_PI_parameters, self.tmin_box)

        self.tmax_box = wx.ComboBox(self.top_panel, -1, size=(100 * self.GUI_RESOLUTION, 25),
                                    choices=self.T_list, style=wx.CB_DROPDOWN | wx.TE_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.get_new_T_PI_parameters, self.tmax_box)

        #--------------------------------------------------------------------
        # save/delete buttons
        #--------------------------------------------------------------------

        # save/delete interpretation buttons
        self.save_interpretation_button = wx.Button(self.top_panel, id=-1, label='save', size=(
            75 * self.GUI_RESOLUTION, 25))  # ,style=wx.BU_EXACTFIT)#, size=(175, 28))
        self.save_interpretation_button.SetFont(font2)
        self.delete_interpretation_button = wx.Button(self.top_panel, id=-1, label='delete', size=(
            75 * self.GUI_RESOLUTION, 25))  # ,style=wx.BU_EXACTFIT)#, size=(175, 28))
        self.delete_interpretation_button.SetFont(font2)
        self.Bind(wx.EVT_BUTTON, self.on_save_interpretation_button,
                  self.save_interpretation_button)
        self.Bind(wx.EVT_BUTTON, self.on_delete_interpretation_button,
                  self.delete_interpretation_button)

        self.auto_save = wx.CheckBox(self.top_panel, wx.ID_ANY, 'auto-save')
        self.auto_save_info = wx.Button(self.top_panel, wx.ID_ANY, "?")
        self.Bind(wx.EVT_BUTTON, self.on_info_click, self.auto_save_info)
        #self.auto_save_text = wx.StaticText(self.top_panel, wx.ID_ANY, label="(saves with 'next')")


        #--------------------------------------------------------------------
        # specimen interpretation and statistics window (Blab; Banc, Dec, Inc, correction factors etc.)
        #--------------------------------------------------------------------

        self.Blab_window = wx.TextCtrl(
            self.top_panel, style=wx.TE_CENTER | wx.TE_READONLY, size=(50 * self.GUI_RESOLUTION, 25))
        self.Banc_window = wx.TextCtrl(
            self.top_panel, style=wx.TE_CENTER | wx.TE_READONLY, size=(50 * self.GUI_RESOLUTION, 25))
        self.Aniso_factor_window = wx.TextCtrl(
            self.top_panel, style=wx.TE_CENTER | wx.TE_READONLY, size=(50 * self.GUI_RESOLUTION, 25))
        self.NLT_factor_window = wx.TextCtrl(
            self.top_panel, style=wx.TE_CENTER | wx.TE_READONLY, size=(50 * self.GUI_RESOLUTION, 25))
        self.CR_factor_window = wx.TextCtrl(
            self.top_panel, style=wx.TE_CENTER | wx.TE_READONLY, size=(50 * self.GUI_RESOLUTION, 25))
        self.declination_window = wx.TextCtrl(
            self.top_panel, style=wx.TE_CENTER | wx.TE_READONLY, size=(50 * self.GUI_RESOLUTION, 25))
        self.inclination_window = wx.TextCtrl(
            self.top_panel, style=wx.TE_CENTER | wx.TE_READONLY, size=(50 * self.GUI_RESOLUTION, 25))

        for stat in ['Blab', 'Banc', 'Aniso_factor', 'NLT_factor', 'CR_factor', 'declination', 'inclination']:
            exec("self.%s_window.SetBackgroundColour(wx.WHITE)" % stat)

        self.Blab_label = wx.StaticText(
            self.top_panel, label="\nB_lab", style=wx.ALIGN_CENTRE)
        self.Blab_label.SetFont(font2)
        self.Banc_label = wx.StaticText(
            self.top_panel, label="\nB_anc", style=wx.ALIGN_CENTRE)
        self.Banc_label.SetFont(font2)
        self.aniso_corr_label = wx.StaticText(
            self.top_panel, label="Aniso\ncorr", style=wx.ALIGN_CENTRE)
        self.aniso_corr_label.SetFont(font2)
        self.nlt_corr_label = wx.StaticText(
            self.top_panel, label="NLT\ncorr", style=wx.ALIGN_CENTRE)
        self.nlt_corr_label.SetFont(font2)
        self.cr_corr_label = wx.StaticText(
            self.top_panel, label="CR\ncorr", style=wx.ALIGN_CENTRE)
        self.cr_corr_label.SetFont(font2)
        self.dec_label = wx.StaticText(
            self.top_panel, label="\nDec", style=wx.ALIGN_CENTRE)
        self.dec_label.SetFont(font2)
        self.inc_label = wx.StaticText(
            self.top_panel, label="\nInc", style=wx.ALIGN_CENTRE)
        self.inc_label.SetFont(font2)

        # handle Specimen Results Sizer
        sizer_specimen_results = wx.StaticBoxSizer(wx.StaticBox(
            self.top_panel, wx.ID_ANY, "specimen results"), wx.HORIZONTAL)
        specimen_stat_window = wx.GridSizer(2, 7, h_space, v_space)
        specimen_stat_window.AddMany([(self.Blab_label, 1, wx.ALIGN_BOTTOM),
                                      ((self.Banc_label), 1, wx.ALIGN_BOTTOM),
                                      ((self.aniso_corr_label), 1, wx.ALIGN_BOTTOM),
                                      ((self.nlt_corr_label), 1, wx.ALIGN_BOTTOM),
                                      ((self.cr_corr_label), 1, wx.ALIGN_BOTTOM),
                                      ((self.dec_label), 1,
                                       wx.TE_CENTER | wx.ALIGN_BOTTOM),
                                      ((self.inc_label), 1, wx.ALIGN_BOTTOM),
                                      (self.Blab_window, 1, wx.EXPAND),
                                      (self.Banc_window, 1, wx.EXPAND),
                                      (self.Aniso_factor_window, 1, wx.EXPAND),
                                      (self.NLT_factor_window, 1, wx.EXPAND),
                                      (self.CR_factor_window, 1, wx.EXPAND),
                                      (self.declination_window, 1, wx.EXPAND),
                                      (self.inclination_window, 1, wx.EXPAND)])
        sizer_specimen_results.Add(
            specimen_stat_window, 1, wx.EXPAND | wx.ALIGN_LEFT, 0)

        #--------------------------------------------------------------------
        # Sample interpretation window
        #--------------------------------------------------------------------

        for key in ["sample_int_n", "sample_int_uT", "sample_int_sigma", "sample_int_sigma_perc"]:
            command = "self.%s_window=wx.TextCtrl(self.top_panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(50*self.GUI_RESOLUTION,25))" % key
            exec(command)
            exec("self.%s_window.SetBackgroundColour(wx.WHITE)" % key)

        sample_mean_label = wx.StaticText(
            self.top_panel, label="\nmean", style=wx.TE_CENTER)
        sample_mean_label.SetFont(font2)
        sample_N_label = wx.StaticText(
            self.top_panel, label="\nN ", style=wx.TE_CENTER)
        sample_N_label.SetFont(font2)
        sample_std_label = wx.StaticText(
            self.top_panel, label="\nstd uT", style=wx.TE_CENTER)
        sample_std_label.SetFont(font2)
        sample_std_per_label = wx.StaticText(
            self.top_panel, label="\nstd %", style=wx.TE_CENTER)
        sample_std_per_label.SetFont(font2)

        # handle samples/sites results sizers
        sizer_sample_results = wx.StaticBoxSizer(wx.StaticBox(
            self.top_panel, wx.ID_ANY, "sample/site results"), wx.HORIZONTAL)
        sample_stat_window = wx.GridSizer(2, 4, h_space, v_space)
        sample_stat_window.AddMany([(sample_mean_label, 1, wx.ALIGN_BOTTOM),
                                    (sample_N_label, 1, wx.ALIGN_BOTTOM),
                                    (sample_std_label, 1, wx.ALIGN_BOTTOM),
                                    (sample_std_per_label, 1, wx.ALIGN_BOTTOM),
                                    (self.sample_int_uT_window, 1, wx.EXPAND),
                                    (self.sample_int_n_window, 1, wx.EXPAND),
                                    (self.sample_int_sigma_window, 1, wx.EXPAND),
                                    (self.sample_int_sigma_perc_window, 1, wx.EXPAND)])
        sizer_sample_results.Add(
            sample_stat_window, 1, wx.EXPAND | wx.ALIGN_LEFT, 0)

        #--------------------------------------------------------------------

        label_0 = wx.StaticText(
            self.bottom_panel, label="                    ", style=wx.ALIGN_CENTER, size=(180, 25))
        label_1 = wx.StaticText(
            self.bottom_panel, label="Acceptance criteria:", style=wx.ALIGN_CENTER, size=(180, 25))
        label_2 = wx.StaticText(
            self.bottom_panel, label="Specimen statistics:", style=wx.ALIGN_CENTER, size=(180, 25))

        for statistic in self.preferences['show_statistics_on_gui']:
            self.stat_windows[statistic] = wx.TextCtrl(
                self.bottom_panel, style=wx.TE_CENTER | wx.TE_READONLY, size=(50 * self.GUI_RESOLUTION, 25))
            self.stat_windows[statistic].SetBackgroundColour(wx.WHITE)
            self.stat_windows[statistic].SetFont(font2)
            self.threshold_windows[statistic] = wx.TextCtrl(
                self.bottom_panel, style=wx.TE_CENTER | wx.TE_READONLY, size=(50 * self.GUI_RESOLUTION, 25))
            self.threshold_windows[statistic].SetFont(font2)
            self.threshold_windows[statistic].SetBackgroundColour(wx.WHITE)
            label = statistic.replace("specimen_", "").replace("int_", "")
            self.stat_labels[statistic] = wx.StaticText(
                self.bottom_panel, label=label, style=wx.ALIGN_CENTRE_HORIZONTAL | wx.ALIGN_BOTTOM)
            self.stat_labels[statistic].SetFont(font2)

        #-------------------------------------------------------------------
        # Design the panels
        #-------------------------------------------------------------------

        # Plots Panel--------------------------------------------------------
        sizer_grid_plots = wx.GridSizer(2, 2, 0, 0)
        sizer_grid_plots.AddMany([(self.canvas2, 1, wx.EXPAND),
                                  (self.canvas4, 1, wx.EXPAND),
                                  (self.canvas3, 1, wx.EXPAND),
                                  (self.canvas5, 1, wx.EXPAND)])

        sizer_plots_outer = wx.BoxSizer(wx.HORIZONTAL)
        sizer_plots_outer.Add(self.canvas1, 1, wx.EXPAND)
        sizer_plots_outer.Add(sizer_grid_plots, 1, wx.EXPAND)

        # Top Bar Sizer-------------------------------------------------------
        #-------------Specimens Sizer----------------------------------------
        sizer_prev_next_btns = wx.BoxSizer(wx.HORIZONTAL)
        sizer_prev_next_btns.Add(prevbutton, 1, wx.EXPAND | wx.RIGHT, h_space)
        sizer_prev_next_btns.Add(nextbutton, 1, wx.EXPAND | wx.LEFT, h_space)

        sizer_select_specimen = wx.StaticBoxSizer(wx.StaticBox(
            self.top_panel, wx.ID_ANY, "specimen"), wx.VERTICAL)
        sizer_select_specimen.Add(
            self.specimens_box, 1, wx.EXPAND | wx.BOTTOM, v_space)
        sizer_select_specimen.Add(
            sizer_prev_next_btns, 1, wx.EXPAND | wx.TOP, v_space)

        #-------------Bounds Sizer----------------------------------------
        sizer_grid_bounds_btns = wx.GridSizer(2, 3, 2 * h_space, 2 * v_space)
        sizer_grid_bounds_btns.AddMany([(self.tmin_box, 1, wx.EXPAND),
                                        (self.save_interpretation_button,
                                         1, wx.EXPAND), (self.auto_save, 1, wx.EXPAND),
                                        (self.tmax_box, 1, wx.EXPAND),
                                        (self.delete_interpretation_button, 1, wx.EXPAND),
                                        (self.auto_save_info, 1, wx.EXPAND)])


        if self.s in list(self.Data.keys()) and self.Data[self.s]['T_or_MW'] == "T":
            sizer_select_temp = wx.StaticBoxSizer(wx.StaticBox(
                self.top_panel, wx.ID_ANY, "temperatures"), wx.HORIZONTAL)
        else:
            sizer_select_temp = wx.StaticBoxSizer(wx.StaticBox(
                self.top_panel, wx.ID_ANY, "MW power"), wx.HORIZONTAL)
        sizer_select_temp.Add(sizer_grid_bounds_btns, 1, wx.EXPAND)

        #-------------Top Bar Outer Sizer------------------------------------
        sizer_top_bar = wx.BoxSizer(wx.HORIZONTAL)
        sizer_top_bar.AddMany([(sizer_select_specimen, 1, wx.EXPAND | wx.ALIGN_LEFT | wx.RIGHT, 2 * h_space),
                               (sizer_select_temp, 1, wx.EXPAND |
                                wx.ALIGN_LEFT | wx.RIGHT, 2 * h_space),
                               (sizer_specimen_results, 2, wx.EXPAND |
                                wx.ALIGN_LEFT | wx.RIGHT, 2 * h_space),
                               (sizer_sample_results, 1, wx.EXPAND | wx.ALIGN_LEFT | wx.RIGHT, 0)])

        # Bottom Bar Sizer----------------------------------------------------
        #----------------Criteria Labels Sizer-------------------------------
        sizer_criteria_labels = wx.BoxSizer(wx.HORIZONTAL)
        sizer_criteria_labels.Add(label_0, 3, wx.EXPAND | wx.LEFT, 2 * h_space)
        sizer_criteria_boxes = wx.BoxSizer(wx.HORIZONTAL)
        sizer_criteria_boxes.Add(label_1, 3, wx.EXPAND | wx.LEFT, 2 * h_space)
        sizer_stats_boxes = wx.BoxSizer(wx.HORIZONTAL)
        sizer_stats_boxes.Add(label_2, 3, wx.EXPAND | wx.LEFT, 2 * h_space)
        for statistic in self.preferences['show_statistics_on_gui']:
            sizer_criteria_labels.Add(
                self.stat_labels[statistic], 1, wx.ALIGN_BOTTOM, 0)

        #----------------Acceptance Criteria Boxes---------------------------
            sizer_criteria_boxes.Add(
                self.threshold_windows[statistic], 1, wx.EXPAND | wx.LEFT, h_space)

        #----------------Specimen Statistics Boxes---------------------------
            sizer_stats_boxes.Add(
                self.stat_windows[statistic], 1, wx.EXPAND | wx.LEFT, h_space)

        #----------------Bottom Outer Sizer----------------------------------
        sizer_bottom_bar = wx.BoxSizer(wx.VERTICAL)
        sizer_bottom_bar.AddMany([(sizer_criteria_labels, 1, wx.EXPAND | wx.ALIGN_BOTTOM | wx.BOTTOM, v_space),
                                  (sizer_criteria_boxes, 1, wx.EXPAND |
                                   wx.BOTTOM | wx.ALIGN_TOP, v_space),
                                  (sizer_stats_boxes, 1, wx.EXPAND | wx.ALIGN_TOP)])

        # Logger Sizer--------------------------------------------------------
        sizer_logger = wx.BoxSizer(wx.HORIZONTAL)
        sizer_logger.Add(self.logger, 1, wx.EXPAND)

        # Set Panel Sizers----------------------------------------------------
        self.plot_panel.SetSizer(sizer_plots_outer)
        self.side_panel.SetSizerAndFit(sizer_logger)
        self.top_panel.SetSizerAndFit(sizer_top_bar)
        self.bottom_panel.SetSizerAndFit(sizer_bottom_bar)

        # Outer Sizer for Frame-----------------------------------------------
        sizer_logger_plots = wx.BoxSizer(wx.HORIZONTAL)
        sizer_logger_plots.Add(self.side_panel, 1, wx.EXPAND | wx.ALIGN_LEFT)
        sizer_logger_plots.Add(self.plot_panel, 3, wx.EXPAND | wx.ALIGN_LEFT)

        sizer_outer = wx.BoxSizer(wx.VERTICAL)
        sizer_outer.AddMany([(self.top_panel, 1, wx.EXPAND | wx.ALIGN_TOP | wx.BOTTOM, v_space / 2),
                             (sizer_logger_plots, 4, wx.EXPAND |
                              wx.ALIGN_TOP | wx.BOTTOM, v_space / 2),
                             (self.bottom_panel, 1, wx.EXPAND | wx.ALIGN_TOP)])

        self.SetSizer(sizer_outer)
        sizer_outer.Fit(self)
        self.Layout()

    def on_save_interpretation_button(self, event):
        """
        save the current interpretation temporarily (not to a file)
        """
        if "specimen_int_uT" not in self.Data[self.s]['pars']:
            return
        if 'deleted' in self.Data[self.s]['pars']:
            self.Data[self.s]['pars'].pop('deleted')
        self.Data[self.s]['pars']['saved'] = True

        # collect all interpretation by sample
        sample = self.Data_hierarchy['specimens'][self.s]
        if sample not in list(self.Data_samples.keys()):
            self.Data_samples[sample] = {}
        if self.s not in list(self.Data_samples[sample].keys()):
            self.Data_samples[sample][self.s] = {}
        self.Data_samples[sample][self.s]['B'] = self.Data[self.s]['pars']["specimen_int_uT"]

        # collect all interpretation by site
        # site=thellier_gui_lib.get_site_from_hierarchy(sample,self.Data_hierarchy)
        site = thellier_gui_lib.get_site_from_hierarchy(
            sample, self.Data_hierarchy)
        if site not in list(self.Data_sites.keys()):
            self.Data_sites[site] = {}
        if self.s not in list(self.Data_sites[site].keys()):
            self.Data_sites[site][self.s] = {}
        self.Data_sites[site][self.s]['B'] = self.Data[self.s]['pars']["specimen_int_uT"]

        self.draw_sample_mean()
        self.write_sample_box()
        self.close_warning = True

    def on_delete_interpretation_button(self, event):
        """
        delete the current interpretation temporarily (not to a file)
        """

        del self.Data[self.s]['pars']
        self.Data[self.s]['pars'] = {}
        self.Data[self.s]['pars']['deleted'] = True
        self.Data[self.s]['pars']['lab_dc_field'] = self.Data[self.s]['lab_dc_field']
        self.Data[self.s]['pars']['er_specimen_name'] = self.Data[self.s]['er_specimen_name']
        self.Data[self.s]['pars']['er_sample_name'] = self.Data[self.s]['er_sample_name']
        self.Data[self.s]['pars']['er_sample_name'] = self.Data[self.s]['er_sample_name']
        sample = self.Data_hierarchy['specimens'][self.s]
        if sample in list(self.Data_samples.keys()):
            if self.s in list(self.Data_samples[sample].keys()):
                if 'B' in list(self.Data_samples[sample][self.s].keys()):
                    del self.Data_samples[sample][self.s]['B']

        site = thellier_gui_lib.get_site_from_hierarchy(
            sample, self.Data_hierarchy)
        if site in list(self.Data_sites.keys()):
            if self.s in list(self.Data_sites[site].keys()):
                del self.Data_sites[site][self.s]['B']
                # if 'B' in self.Data_sites[site][self.s].keys():
                #    del self.Data_sites[site][self.s]['B']

        self.tmin_box.SetValue("")
        self.tmax_box.SetValue("")
        self.clear_boxes()
        self.draw_figure(self.s)
        self.draw_sample_mean()
        self.write_sample_box()
        self.close_warning = True

    #----------------------------------------------------------------------
    # Plot and Figure interaction functions
    #----------------------------------------------------------------------

    def on_right_click_fig(self, event):
        if event.LeftIsDown() or event.ButtonDClick():
            return
        event_canvas = event.EventObject
        canvas_num = self.get_canvas_number_from_event(event)

        COMMAND = """
if self.fig%d_setting == "Zoom":
    self.fig%d_setting = "Pan"
    try: event_canvas.toolbar.pan('off')
    except TypeError: pass
else:
    self.fig%d_setting = "Zoom"
    try: event_canvas.toolbar.zoom()
    except TypeError: pass
""" % (canvas_num, canvas_num, canvas_num)
        exec(COMMAND)
        event.Skip()

    def on_home_fig(self, event):
        if event.LeftIsDown() or event.ButtonDClick():
            return
        event_canvas = event.EventObject
        try:
            event_canvas.toolbar.home()
        except TypeError:
            pass

    def get_canvas_number_from_event(self, event):
        event_canvas = event.EventObject
        if event_canvas == self.canvas1:
            return 1
        elif event_canvas == self.canvas2:
            return 2
        elif event_canvas == self.canvas3:
            return 3
        elif event_canvas == self.canvas4:
            return 4
        elif event_canvas == self.canvas5:
            return 5
        else:
            raise TypeError(
                "Honestly not sure how you got here...WELL there's a big bug in get_canvas_number_from_event, good luck")

    #----------------------------------------------------------------------

    def write_acceptance_criteria_to_boxes(self):
        """
        Update paleointensity statistics in acceptance criteria boxes.
        (after changing temperature bounds or changing specimen)
        """

        self.ignore_parameters, value = {}, ''
        for crit_short_name in self.preferences['show_statistics_on_gui']:
            crit = "specimen_" + crit_short_name
            if self.acceptance_criteria[crit]['value'] == -999:
                self.threshold_windows[crit_short_name].SetValue("")
                self.threshold_windows[crit_short_name].SetBackgroundColour(
                    wx.Colour(128, 128, 128))
                self.ignore_parameters[crit] = True
                continue
            elif crit == "specimen_scat":
                if self.acceptance_criteria[crit]['value'] in ['g', 1, '1', True, "True"]:
                    value = "True"
                    #self.scat_threshold_window.SetBackgroundColour(wx.SetBackgroundColour(128, 128, 128))
                else:
                    value = ""
                    self.threshold_windows['scat'].SetBackgroundColour(
                        (128, 128, 128))
                    #self.scat_threshold_window.SetBackgroundColour((128, 128, 128))

            elif type(self.acceptance_criteria[crit]['value']) == int:
                value = "%i" % self.acceptance_criteria[crit]['value']
            elif type(self.acceptance_criteria[crit]['value']) == float:
                if self.acceptance_criteria[crit]['decimal_points'] == -999:
                    value = "%.3e" % self.acceptance_criteria[crit]['value']
                else:
                    value = "{:.{}f}".format(self.acceptance_criteria[crit]['value'],
                                             self.acceptance_criteria[crit]['decimal_points'])
            else:
                continue

            self.threshold_windows[crit_short_name].SetValue(value)
            self.threshold_windows[crit_short_name].SetBackgroundColour(
                wx.WHITE)

    #----------------------------------------------------------------------

    def Add_text(self, s):
        """
        Add text to measurement data window.
        """
        self.logger.DeleteAllItems()
        FONT_RATIO = self.GUI_RESOLUTION + (self.GUI_RESOLUTION - 1) * 5
        if self.GUI_RESOLUTION > 1.1:
            font1 = wx.Font(11, wx.SWISS, wx.NORMAL,
                            wx.NORMAL, False, self.font_type)
        elif self.GUI_RESOLUTION <= 0.9:
            font1 = wx.Font(8, wx.SWISS, wx.NORMAL,
                            wx.NORMAL, False, self.font_type)
        else:
            font1 = wx.Font(10, wx.SWISS, wx.NORMAL,
                            wx.NORMAL, False, self.font_type)

        # get temperature indecies to display current interp steps in logger
        t1 = self.tmin_box.GetValue()
        t2 = self.tmax_box.GetValue()

        # microwave or thermal
        if "LP-PI-M" in self.Data[s]['datablock'][0]['magic_method_codes']:
            MICROWAVE = True
            THERMAL = False

            steps_tr = []
            for rec in self.Data[s]['datablock']:

                if "measurement_description" in rec:
                    MW_step = rec["measurement_description"].strip(
                        '\n').split(":")
                    for STEP in MW_step:
                        if "Number" in STEP:
                            temp = float(STEP.split("-")[-1])
                            steps_tr.append(temp)

                else:
                    power = rec['treatment_mw_power']
                    if '-' in str(power):
                        power = power.split('-')[-1]
                    steps_tr.append(int(power))



            #steps_tr = [float(d['treatment_mw_power'].split("-")[-1])
            #            for d in self.Data[s]['datablock']]
        else:
            MICROWAVE = False
            THERMAL = True
            steps_tr = [float(d['treatment_temp']) -
                        273 for d in self.Data[s]['datablock']]

        if (t1 == "" or t2 == "") or float(t2) < float(t1):
            tmin_index, tmax_index = -1, -1
        else:
            tmin_index = steps_tr.index(int(t1))
            tmax_index = steps_tr.index(int(t2))

        self.logger.SetFont(font1)
        for i, rec in enumerate(self.Data[s]['datablock']):
            if "LT-NO" in rec['magic_method_codes']:
                step = "N"
            elif "LT-AF-Z" in rec['magic_method_codes']:
                step = "AFD"
            elif "LT-T-Z" in rec['magic_method_codes'] or 'LT-M-Z' in rec['magic_method_codes']:
                step = "Z"
            elif "LT-T-I" in rec['magic_method_codes'] or 'LT-M-I' in rec['magic_method_codes']:
                step = "I"
            elif "LT-PTRM-I" in rec['magic_method_codes'] or "LT-PMRM-I" in rec['magic_method_codes']:
                step = "P"
            elif "LT-PTRM-MD" in rec['magic_method_codes'] or "LT-PMRM-MD" in rec['magic_method_codes']:
                step = "T"
            elif "LT-PTRM-AC" in rec['magic_method_codes'] or "LT-PMRM-AC" in rec['magic_method_codes']:
                step = "A"
            else:
                print(("unrecognized step in specimen %s Method codes: %s" %
                       (str(rec['magic_method_codes']), s)))
            if THERMAL:
                self.logger.InsertItem(i, "%i" % i)
                self.logger.SetItem(i, 1, step)
                self.logger.SetItem(i, 2, "%1.0f" %
                                    (float(rec['treatment_temp']) - 273.))
                self.logger.SetItem(i, 3, "%.1f" %
                                    float(rec['measurement_dec']))
                self.logger.SetItem(i, 4, "%.1f" %
                                    float(rec['measurement_inc']))
                self.logger.SetItem(i, 5, "%.2e" %
                                    float(rec['measurement_magn_moment']))
            elif MICROWAVE:  # mcrowave
                if "measurement_description" in list(rec.keys()):
                    MW_step = rec["measurement_description"].strip(
                        '\n').split(":")
                    for STEP in MW_step:
                        if "Number" not in STEP:
                            continue
                        temp = float(STEP.split("-")[-1])

                        self.logger.InsertItem(i, "%i" % i)
                        self.logger.SetItem(i, 1, step)
                        self.logger.SetItem(i, 2, "%1.0f" % temp)
                        self.logger.SetItem(i, 3, "%.1f" %
                                            float(rec['measurement_dec']))
                        self.logger.SetItem(i, 4, "%.1f" %
                                            float(rec['measurement_inc']))
                        self.logger.SetItem(i, 5, "%.2e" % float(
                            rec['measurement_magn_moment']))
            self.logger.SetItemBackgroundColour(i, "WHITE")
            if i >= tmin_index and i <= tmax_index:
                self.logger.SetItemBackgroundColour(i, "LIGHT BLUE")
            if 'measurement_flag' not in list(rec.keys()):
                rec['measurement_flag'] = 'g'
#            elif rec['measurement_flag'] != 'g':
#                self.logger.SetItemBackgroundColour(i,"red")

    def on_click_listctrl(self, event):
        meas_i = int(event.GetText())
        step_key = 'treatment_temp'
        if MICROWAVE:
            step_key = 'treatment_mw_power'
        m_step = self.Data[self.s]['datablock'][meas_i][step_key]
        index = self.Data[self.s]['t_Arai'].index(float(m_step))
        self.select_bounds_in_logger(index)

    def select_bounds_in_logger(self, index):
        """
        sets index as the upper or lower bound of a fit based on what the other bound is and selects it in the logger. Requires 2 calls to completely update a interpretation. NOTE: Requires an interpretation to exist before it is called.
        @param: index - index of the step to select in the logger
        """
        tmin_index, tmax_index = "", ""
        if str(self.tmin_box.GetValue()) != "":
            tmin_index = self.tmin_box.GetSelection()
        if str(self.tmax_box.GetValue()) != "":
            tmax_index = self.tmax_box.GetSelection()
        # if there is no prior interpretation, assume first click is
        # tmin and set highest possible temp as tmax
        if not tmin_index and not tmax_index:
            tmin_index = index
            self.tmin_box.SetSelection(index)
            # set to the highest step
            max_step_data = self.Data[self.s]['datablock'][-1]
            step_key = 'treatment_temp'
            if MICROWAVE:
                step_key = 'treatment_mw_power'
            max_step = max_step_data[step_key]
            tmax_index = self.tmax_box.GetCount() - 1
            self.tmax_box.SetSelection(tmax_index)
        elif self.list_bound_loc != 0:
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

        self.logger.Select(index, on=0)
        self.get_new_T_PI_parameters(-1)


    def on_right_click_listctrl(self, event):
        self.user_warning("Thellier GUI cannot handle data marked bad yet so this function does not work. This feature is in development and will hopefully be included in future versions. Currently bad data must be marked 'b' in  measurement file manually.")
        return
        index = int(event.GetText())
        current_flag = self.Data[self.s]['datablock'][index]['measurement_flag']

        if current_flag == "g":
            self.mark_meas_bad(index)
        else:
            self.mark_meas_good(index)

        if self.data_model == 3.0:
            self.contribution.tables['measurements'].write_magic_file(
                dir_path=self.WD)
        else:
            pmag.magic_write(os.path.join(self.WD, "magic_measurements.txt"),
                             self.Data[self.s]['datablock'], "magic_measurements")

        self.update_selection()

    def mark_meas_good(self, index):
        self.Data[self.s]['datablock'][index]['measurement_flag'] = 'g'

        if self.data_model == 3.0:
            mdf = self.contribution.tables['measurements'].df
            a_index = self.Data[self.s]['magic_experiment_name'] + \
                str(index + 1)
            try:
                mdf.loc[a_index, 'quality'] = 'g'
            except ValueError:
                self.user_warning(
                    "cannot find valid measurement data to mark bad, this feature is still under development. please report this error to a developer")

    def mark_meas_bad(self, index):
        self.Data[self.s]['datablock'][index]['measurement_flag'] = 'b'

        if self.data_model == 3.0:
            mdf = self.contribution.tables['measurements'].df
            a_index = self.Data[self.s]['magic_experiment_name'] + \
                str(index + 1)
            try:
                mdf.loc[a_index, 'quality'] = 'b'
            except ValueError:
                self.user_warning(
                    "cannot find valid measurement data to mark bad, this feature is still under development please report this error to a developer")

    def get_meas_flags(self):  # under dev
        dblock = self.Data[self.s]['datablock']
        in_z_flags = []
        ptrm_flags = []
        tail_flags = []

    #----------------------------------------------------------------------

    def create_menu(self):
        """
        Create menu bar
        """
        self.menubar = wx.MenuBar()

        menu_preferences = wx.Menu()

        m_preferences_apperance = menu_preferences.Append(
            -1, "&Appearence preferences", "")
        self.Bind(wx.EVT_MENU, self.on_menu_appearance_preferences,
                  m_preferences_apperance)

        m_preferences_spd = menu_preferences.Append(
            -1, "&Specimen paleointensity statistics (from SPD list)", "")
        self.Bind(wx.EVT_MENU, self.on_menu_m_preferences_spd,
                  m_preferences_spd)

        #m_preferences_stat = menu_preferences.Append(-1, "&Statistical preferences", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_preferences_stat, m_preferences_stat)

        #m_save_preferences = menu_preferences.Append(-1, "&Save preferences", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_save_preferences, m_save_preferences)

        menu_file = wx.Menu()

        m_change_working_directory = menu_file.Append(
            -1, "&Change project directory", "")
        self.Bind(wx.EVT_MENU, self.on_menu_change_working_directory,
                  m_change_working_directory)

        #m_add_working_directory = menu_file.Append(-1, "&Add a MagIC project directory", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_add_working_directory, m_add_working_directory)

        m_open_magic_file = menu_file.Append(-1,
                                             "&Open MagIC measurement file", "")
        self.Bind(wx.EVT_MENU, self.on_menu_open_magic_file, m_open_magic_file)

        m_open_magic_tree = menu_file.Append(
            -1, "&Open all MagIC project directories in path", "")
        self.Bind(wx.EVT_MENU, self.on_menu_m_open_magic_tree,
                  m_open_magic_tree)

        menu_file.AppendSeparator()

        m_prepare_MagIC_results_tables = menu_file.Append(
            -1, "&Save MagIC tables", "")
        self.Bind(wx.EVT_MENU, self.on_menu_prepare_magic_results_tables,
                  m_prepare_MagIC_results_tables)

        submenu_save_plots = wx.Menu()

        m_save_Arai_plot = submenu_save_plots.Append(-1, "&Save Arai plot", "")
        self.Bind(wx.EVT_MENU, self.on_save_Arai_plot, m_save_Arai_plot)

        m_save_zij_plot = submenu_save_plots.Append(
            -1, "&Save Zijderveld plot", "")
        self.Bind(wx.EVT_MENU, self.on_save_Zij_plot, m_save_zij_plot, "Zij")

        m_save_eq_plot = submenu_save_plots.Append(
            -1, "&Save equal area plot", "")
        self.Bind(wx.EVT_MENU, self.on_save_Eq_plot, m_save_eq_plot, "Eq")

        m_save_M_t_plot = submenu_save_plots.Append(-1, "&Save M-t plot", "")
        self.Bind(wx.EVT_MENU, self.on_save_M_t_plot, m_save_M_t_plot, "M_t")

        m_save_NLT_plot = submenu_save_plots.Append(-1, "&Save NLT plot", "")
        self.Bind(wx.EVT_MENU, self.on_save_NLT_plot, m_save_NLT_plot, "NLT")

        m_save_CR_plot = submenu_save_plots.Append(
            -1, "&Save cooling rate plot", "")
        self.Bind(wx.EVT_MENU, self.on_save_CR_plot, m_save_CR_plot, "CR")

        m_save_sample_plot = submenu_save_plots.Append(
            -1, "&Save sample plot", "")
        self.Bind(wx.EVT_MENU, self.on_save_sample_plot,
                  m_save_sample_plot, "Samp")

        #m_save_all_plots = submenu_save_plots.Append(-1, "&Save all plots", "")
        #self.Bind(wx.EVT_MENU, self.on_save_all_plots, m_save_all_plots)

        menu_file.AppendSeparator()

        m_new_sub_plots = menu_file.AppendSubMenu(submenu_save_plots,
                                                  "&Save plot")

        menu_file.AppendSeparator()
        m_exit = menu_file.Append(wx.ID_EXIT, "Quit", "Quit application")
        self.Bind(wx.EVT_MENU, self.on_menu_exit, m_exit)

        menu_anisotropy = wx.Menu()

        m_calculate_aniso_tensor = menu_anisotropy.Append(
            -1, "&Calculate anisotropy tensors", "")
        self.Bind(wx.EVT_MENU, self.on_menu_calculate_aniso_tensor,
                  m_calculate_aniso_tensor)

        m_show_anisotropy_errors = menu_anisotropy.Append(
            -1, "&Show anisotropy calculation Warnings/Errors", "")
        self.Bind(wx.EVT_MENU, self.on_show_anisotropy_errors,
                  m_show_anisotropy_errors)

        menu_Analysis = wx.Menu()

        submenu_criteria = wx.Menu()

       # m_set_criteria_to_default = submenu_criteria.Append(-1, "&Set acceptance criteria to default", "")
       # self.Bind(wx.EVT_MENU, self.on_menu_default_criteria, m_set_criteria_to_default)

        m_change_criteria_file = submenu_criteria.Append(
            -1, "&Change acceptance criteria", "")
        self.Bind(wx.EVT_MENU, self.on_menu_criteria, m_change_criteria_file)

        m_import_criteria_file = submenu_criteria.Append(
            -1, "&Import criteria file", "")
        self.Bind(wx.EVT_MENU, self.on_menu_criteria_file,
                  m_import_criteria_file)

        m_new_sub = menu_Analysis.AppendSubMenu(submenu_criteria,
                                         "Acceptance criteria")

        m_previous_interpretation = menu_Analysis.Append(
            -1, "&Import previous interpretation from a 'redo' file", "")
        self.Bind(wx.EVT_MENU, self.on_menu_previous_interpretation,
                  m_previous_interpretation)

        m_save_interpretation = menu_Analysis.Append(
            -1, "&Save current interpretations to a 'redo' file", "")
        self.Bind(wx.EVT_MENU, self.on_menu_save_interpretation,
                  m_save_interpretation)

        m_delete_interpretation = menu_Analysis.Append(
            -1, "&Clear all current interpretations", "")
        self.Bind(wx.EVT_MENU, self.on_menu_clear_interpretation,
                  m_delete_interpretation)

        menu_Tools = wx.Menu()
        #m_prev_interpretation = menu_file.Append(-1, "&Save plot\tCtrl-S", "Save plot to file")

        menu_Auto_Interpreter = wx.Menu()

        m_interpreter = menu_Auto_Interpreter.Append(
            -1, "&Run Thellier auto interpreter", "Run auto interpter")
        self.Bind(wx.EVT_MENU, self.on_menu_run_interpreter, m_interpreter)

        m_open_interpreter_file = menu_Auto_Interpreter.Append(
            -1, "&Open auto-interpreter output files", "")
        self.Bind(wx.EVT_MENU, self.on_menu_open_interpreter_file,
                  m_open_interpreter_file)

        m_open_interpreter_log = menu_Auto_Interpreter.Append(
            -1, "&Open auto-interpreter Warnings/Errors", "")
        self.Bind(wx.EVT_MENU, self.on_menu_open_interpreter_log,
                  m_open_interpreter_log)

        #menu_consistency_test = wx.Menu()
        #m_run_consistency_test = menu_consistency_test.Append(
        #    -1, "&Run Consistency test", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_run_consistency_test,
        #          m_run_consistency_test)

        #m_run_consistency_test_b = menu_Optimizer.Append(-1, "&Run Consistency test beta version", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_run_consistency_test_b, m_run_consistency_test_b)

        menu_Plot = wx.Menu()
        m_plot_data = menu_Plot.Append(-1, "&Plot paleointensity curve", "")
        self.Bind(wx.EVT_MENU, self.on_menu_plot_data, m_plot_data)

        menu_Help = wx.Menu()

        m_cookbook = menu_Help.Append(-1, "&PmagPy Cookbook\tCtrl-Shift-W", "")
        self.Bind(wx.EVT_MENU, self.on_menu_cookbook, m_cookbook)

        m_docs = menu_Help.Append(-1, "&Open Docs\tCtrl-Shift-H", "")
        self.Bind(wx.EVT_MENU, self.on_menu_docs, m_docs)

        m_git = menu_Help.Append(-1, "&Github Page\tCtrl-Shift-G", "")
        self.Bind(wx.EVT_MENU, self.on_menu_git, m_git)

        m_debug = menu_Help.Append(-1, "&Open Debugger\tCtrl-Shift-D", "")
        self.Bind(wx.EVT_MENU, self.on_menu_debug, m_debug)

        #menu_results_table= wx.Menu()
        #m_make_results_table = menu_results_table.Append(-1, "&Make results table", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_results_data, m_make_results_table)

        #menu_MagIC= wx.Menu()
        #m_convert_to_magic= menu_MagIC.Append(-1, "&Convert generic files to MagIC format", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_convert_to_magic, m_convert_to_magic)
        #m_build_magic_model= menu_MagIC.Append(-1, "&Run MagIC model builder", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_MagIC_model_builder, m_build_magic_model)
        #m_prepare_MagIC_results_tables= menu_MagIC.Append(-1, "&Make MagIC results Table", "")
        #self.Bind(wx.EVT_MENU, self.on_menu_prepare_magic_results_tables, m_prepare_MagIC_results_tables)

        #menu_help = wx.Menu()
        #m_about = menu_help.Append(-1, "&About\tF1", "About this program")
        self.menubar.Append(menu_preferences, "& Preferences")
        self.menubar.Append(menu_file, "&File")
        self.menubar.Append(menu_anisotropy, "&Anisotropy")
        self.menubar.Append(menu_Analysis, "&Analysis")
        self.menubar.Append(menu_Auto_Interpreter, "&Auto Interpreter")
        #self.menubar.Append(menu_consistency_test, "&Consistency Test")
        self.menubar.Append(menu_Plot, "&Plot")
        self.menubar.Append(menu_Help, "&Help")
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
        self.draw_figure(self.s)

        # update temperature list
        if self.Data[self.s]['T_or_MW'] == "T":
            self.temperatures = np.array(self.Data[self.s]['t_Arai']) - 273.
        else:
            self.temperatures = np.array(self.Data[self.s]['t_Arai'])

        self.T_list = ["%.0f" % T for T in self.temperatures]
        self.tmin_box.SetItems(self.T_list)
        self.tmax_box.SetItems(self.T_list)
        self.tmin_box.SetValue("")
        self.tmax_box.SetValue("")
        self.Blab_window.SetValue(
            "%.0f" % (float(self.Data[self.s]['pars']['lab_dc_field']) * 1e6))
        if "saved" in self.Data[self.s]['pars']:
            self.pars = self.Data[self.s]['pars']
            self.update_GUI_with_new_interpretation()
        self.Add_text(self.s)
        self.write_sample_box()

    #----------------------------------------------------------------------

    def show_dlg(self, dlg):
        """
        Abstraction function that is to be used instead of dlg.ShowModal
        @param: dlg - dialog to ShowModal if possible
        """
        if not self.test_mode:
            dlg.Center()
            return dlg.ShowModal()
        else:
            return dlg.GetAffirmativeId()

    def set_test_mode(self, on_off):
        """
        Sets GUI test mode on or off
        @param: on_off - bool value to set test mode to
        """
        if type(on_off) != bool:
            print("test mode must be a bool")
            return
        self.test_mode = on_off

    def onSelect_specimen(self, event):
        """
        update figures and text when a new specimen is selected
        """
        new_s = self.specimens_box.GetValue()
        if self.select_specimen(new_s):
            self.update_selection()
        else:
            self.specimens_box.SetValue(self.s)
            self.user_warning(
                "no specimen %s reverting to old specimen %s" % (new_s, self.s))

    def select_specimen(self, s):
        if s in self.specimens:
            self.s = s
            return True
        else:
            return False

    def user_warning(self, message, caption='Warning!'):
        """
        Shows a dialog that warns the user about some action
        @param: message - message to display to user
        @param: caption - title for dialog (default: "Warning!")
        @return: True or False
        """
        dlg = wx.MessageDialog(self, message, caption,
                               wx.OK | wx.CANCEL | wx.ICON_WARNING)
        if self.show_dlg(dlg) == wx.ID_OK:
            continue_bool = True
        else:
            continue_bool = False
        dlg.Destroy()
        return continue_bool

    def on_next_button(self, event):
        """
        update figures and text when a next button is selected
        """
        if 'saved' not in self.Data[self.s]['pars'] or self.Data[self.s]['pars']['saved'] != True:
            # check preferences
            if self.auto_save.GetValue():
                self.on_save_interpretation_button(None)
            else:
                del self.Data[self.s]['pars']
                self.Data[self.s]['pars'] = {}
                self.Data[self.s]['pars']['lab_dc_field'] = self.Data[self.s]['lab_dc_field']
                self.Data[self.s]['pars']['er_specimen_name'] = self.Data[self.s]['er_specimen_name']
                self.Data[self.s]['pars']['er_sample_name'] = self.Data[self.s]['er_sample_name']
                # return to last saved interpretation if exist
                if 'er_specimen_name' in list(self.last_saved_pars.keys()) and self.last_saved_pars['er_specimen_name'] == self.s:
                    for key in list(self.last_saved_pars.keys()):
                        self.Data[self.s]['pars'][key] = self.last_saved_pars[key]
                    self.last_saved_pars = {}

        index = self.specimens.index(self.s)
        if index == len(self.specimens) - 1:
            index = 0
        else:
            index += 1
        self.s = self.specimens[index]
        self.specimens_box.SetStringSelection(self.s)
        if self.s:
            self.update_selection()

    #----------------------------------------------------------------------


    def on_info_click(self, event):
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

    def on_prev_button(self, event):
        """
        update figures and text when a previous button is selected
        """
        if 'saved' not in self.Data[self.s]['pars'] or self.Data[self.s]['pars']['saved'] != True:
            # check preferences
            if self.auto_save.GetValue():
                self.on_save_interpretation_button(None)
            else:
                del self.Data[self.s]['pars']
                self.Data[self.s]['pars'] = {}
                self.Data[self.s]['pars']['lab_dc_field'] = self.Data[self.s]['lab_dc_field']
                self.Data[self.s]['pars']['er_specimen_name'] = self.Data[self.s]['er_specimen_name']
                self.Data[self.s]['pars']['er_sample_name'] = self.Data[self.s]['er_sample_name']
                # return to last saved interpretation if exist
                if 'er_specimen_name' in list(self.last_saved_pars.keys()) and self.last_saved_pars['er_specimen_name'] == self.s:
                    for key in list(self.last_saved_pars.keys()):
                        self.Data[self.s]['pars'][key] = self.last_saved_pars[key]
                    self.last_saved_pars = {}

        index = self.specimens.index(self.s)
        if index == 0:
            index = len(self.specimens)
        index -= 1
        self.s = self.specimens[index]
        self.specimens_box.SetStringSelection(self.s)
        self.update_selection()

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
        self.Banc_window.SetBackgroundColour(wx.Colour('grey'))
        self.Aniso_factor_window.SetValue("")
        self.Aniso_factor_window.SetBackgroundColour(wx.Colour('grey'))
        self.NLT_factor_window.SetValue("")
        self.NLT_factor_window.SetBackgroundColour(wx.Colour('grey'))
        self.CR_factor_window.SetValue("")
        self.CR_factor_window.SetBackgroundColour(wx.Colour('grey'))
        self.declination_window.SetValue("")
        self.declination_window.SetBackgroundColour(wx.Colour('grey'))
        self.inclination_window.SetValue("")
        self.inclination_window.SetBackgroundColour(wx.Colour('grey'))

        window_list = ['sample_int_n', 'sample_int_uT',
                       'sample_int_sigma', 'sample_int_sigma_perc']
        for key in window_list:
            command = "self.%s_window.SetValue(\"\")" % key
            exec(command)
            command = "self.%s_window.SetBackgroundColour(wx.Colour('grey'))" % key
            exec(command)

        # window_list=['int_n','int_ptrm_n','frac','scat','gmax','f','fvds','b_beta','g','q','int_mad','int_dang','drats','md','ptrms_dec','ptrms_inc','ptrms_mad','ptrms_angle']
        # for key in window_list:
        for key in self.preferences['show_statistics_on_gui']:
            self.stat_windows[key].SetValue("")
            self.stat_windows[key].SetBackgroundColour(wx.Colour('grey'))

    def write_sample_box(self):
        """
        """

        B = []

        if self.acceptance_criteria['average_by_sample_or_site']['value'] == 'sample':
            sample = self.Data_hierarchy['specimens'][self.s]
            if sample in list(self.Data_samples.keys()) and len(list(self.Data_samples[sample].keys())) > 0:
                if self.s not in list(self.Data_samples[sample].keys()):
                    if 'specimen_int_uT' in list(self.pars.keys()):
                        B.append(self.pars['specimen_int_uT'])
                for specimen in list(self.Data_samples[sample].keys()):
                    if specimen == self.s:
                        if 'specimen_int_uT' in list(self.pars.keys()):
                            B.append(self.pars['specimen_int_uT'])
                    else:
                        if specimen in list(self.Data_samples[sample].keys()) and 'B' in list(self.Data_samples[sample][specimen].keys()):
                            B.append(self.Data_samples[sample][specimen]['B'])
            else:
                if 'specimen_int_uT' in list(self.pars.keys()):
                    B.append(self.pars['specimen_int_uT'])

        # if averaging by site
        else:

            sample = self.Data_hierarchy['specimens'][self.s]
            site = thellier_gui_lib.get_site_from_hierarchy(
                sample, self.Data_hierarchy)
            if site in list(self.Data_sites.keys()) and len(list(self.Data_sites[site].keys())) > 0:
                if self.s not in list(self.Data_sites[site].keys()):
                    if 'specimen_int_uT' in list(self.pars.keys()):
                        B.append(self.pars['specimen_int_uT'])
                for specimen in list(self.Data_sites[site].keys()):
                    if specimen == self.s:
                        if 'specimen_int_uT' in list(self.pars.keys()):
                            B.append(self.pars['specimen_int_uT'])
                    else:
                        if specimen in list(self.Data_sites[site].keys()) and 'B' in list(self.Data_sites[site][specimen].keys()):
                            B.append(self.Data_sites[site][specimen]['B'])
            else:
                if 'specimen_int_uT' in list(self.pars.keys()):
                    B.append(self.pars['specimen_int_uT'])

        if B == []:
            self.sample_int_n_window.SetValue("")
            self.sample_int_uT_window.SetValue("")
            self.sample_int_sigma_window.SetValue("")
            self.sample_int_sigma_perc_window.SetValue("")
            self.sample_int_uT_window.SetBackgroundColour(wx.Colour('grey'))
            self.sample_int_n_window.SetBackgroundColour(wx.Colour('grey'))
            self.sample_int_sigma_window.SetBackgroundColour(wx.Colour('grey'))
            self.sample_int_sigma_perc_window.SetBackgroundColour(
                wx.Colour('grey'))

            return()

        # print "B is this:", B # shows that the problem happens when B array
        # contains 1 or 2
        N = len(B)
        B_mean = np.mean(B)
        # B_std=np.std(B,ddof=1)
        # B_std_perc=100*(B_std/B_mean)
        if N > 1:
            B_std = np.std(B, ddof=1)
            B_std_perc = 100 * (B_std / B_mean)
        else:
            B_std, B_std_perc = np.nan, np.nan

        self.sample_int_n_window.SetValue("%i" % (N))
        self.sample_int_uT_window.SetValue("%.1f" % (B_mean))
        self.sample_int_sigma_window.SetValue("%.1f" % (B_std))
        self.sample_int_sigma_perc_window.SetValue("%.1f" % (B_std_perc))
        self.sample_int_n_window.SetBackgroundColour(wx.WHITE)
        self.sample_int_uT_window.SetBackgroundColour(wx.WHITE)
        self.sample_int_sigma_window.SetBackgroundColour(wx.WHITE)
        self.sample_int_sigma_perc_window.SetBackgroundColour(wx.WHITE)

        fail_flag = False
        fail_int_n = False
        fail_int_sigma = False
        fail_int_sigma_perc = False
        sample_failed = False

        if self.acceptance_criteria['sample_int_n']['value'] != -999:
            if N < self.acceptance_criteria['sample_int_n']['value']:
                fail_int_n = True
                sample_failed = True
                self.sample_int_n_window.SetBackgroundColour(wx.RED)
            else:
                self.sample_int_n_window.SetBackgroundColour(wx.GREEN)
        else:
            self.sample_int_n_window.SetBackgroundColour(wx.WHITE)

        if self.acceptance_criteria['sample_int_sigma']['value'] != -999:
            if B_std * 1.e-6 > self.acceptance_criteria['sample_int_sigma']['value']:
                fail_int_sigma = True
                self.sample_int_sigma_window.SetBackgroundColour(wx.RED)
            else:
                self.sample_int_sigma_window.SetBackgroundColour(wx.GREEN)
        else:
            self.sample_int_sigma_window.SetBackgroundColour(wx.WHITE)

        if self.acceptance_criteria['sample_int_sigma_perc']['value'] != -999:
            if B_std_perc > self.acceptance_criteria['sample_int_sigma_perc']['value']:
                fail_int_sigma_perc = True
                self.sample_int_sigma_perc_window.SetBackgroundColour(wx.RED)
            else:
                self.sample_int_sigma_perc_window.SetBackgroundColour(wx.GREEN)
        else:
            self.sample_int_sigma_perc_window.SetBackgroundColour(wx.WHITE)

        if self.acceptance_criteria['sample_int_sigma']['value'] == -999 and fail_int_sigma_perc:
            sample_failed = True
        elif self.acceptance_criteria['sample_int_sigma_perc']['value'] == -999 and fail_int_sigma:
            sample_failed = True
        elif self.acceptance_criteria['sample_int_sigma']['value'] != -999 and self.acceptance_criteria['sample_int_sigma_perc']['value'] != -999:
            if fail_int_sigma and fail_int_sigma_perc:
                sample_failed = True

        if sample_failed:
            self.sample_int_uT_window.SetBackgroundColour(wx.RED)
        else:
            self.sample_int_uT_window.SetBackgroundColour(wx.GREEN)

    #----------------------------------------------------------------------
    # menu bar options:
    #----------------------------------------------------------------------

    def on_menu_appearance_preferences(self, event):
        class preferences_appearance_dialog(wx.Dialog):

            def __init__(self, parent, title, preferences):
                self.preferences = preferences
                super(preferences_appearance_dialog,
                      self).__init__(parent, title=title)
                self.InitUI()

            def InitUI(self):

                pnl1 = wx.Panel(self)

                vbox = wx.BoxSizer(wx.VERTICAL)

                #-----------box1
                bSizer1 = wx.StaticBoxSizer(wx.StaticBox(
                    pnl1, wx.ID_ANY, "Gui appearance"), wx.HORIZONTAL)
                self.gui_resolution = wx.TextCtrl(
                    pnl1, style=wx.TE_CENTER, size=(50, 20))

                appearance_window = wx.GridSizer(1, 2, 12, 12)
                appearance_window.AddMany([(wx.StaticText(pnl1, label="GUI resolution (100% is default size)", style=wx.TE_CENTER), wx.EXPAND),
                                           (self.gui_resolution, wx.EXPAND)])
                bSizer1.Add(appearance_window, 0, wx.ALIGN_LEFT | wx.ALL, 5)

                #-----------box2

                bSizer2 = wx.StaticBoxSizer(wx.StaticBox(
                    pnl1, wx.ID_ANY, "Arai plot"), wx.HORIZONTAL)
                self.show_Arai_temperatures = wx.CheckBox(
                    pnl1, -1, '', (50, 50))
                #self.show_Arai_temperatures_steps=FS.FloatSpin(pnl1, -1, min_val=1, max_val=9,increment=1, value=1, extrastyle=FS.FS_LEFT,size=(50,20))
                # self.show_Arai_temperatures_steps.SetFormat("%f")
                # self.show_Arai_temperatures_steps.SetDigits(0)
                self.show_Arai_temperatures_steps = wx.SpinCtrl(
                    pnl1, -1, '1', (50, 20), (60, -1), min=1, max=9)

                self.show_Arai_pTRM_arrows = wx.CheckBox(
                    pnl1, -1, '', (50, 50))

                arai_window = wx.GridSizer(2, 3, 12, 12)
                arai_window.AddMany([(wx.StaticText(pnl1, label="show temperatures", style=wx.TE_CENTER), wx.EXPAND),
                                     (wx.StaticText(
                                         pnl1, label="show temperatures but skip steps", style=wx.TE_CENTER), wx.EXPAND),
                                     (wx.StaticText(pnl1, label="show pTRM-checks arrows",
                                                    style=wx.TE_CENTER), wx.EXPAND),
                                     (self.show_Arai_temperatures, wx.EXPAND),
                                     (self.show_Arai_temperatures_steps, wx.EXPAND),
                                     (self.show_Arai_pTRM_arrows, wx.EXPAND)])
                bSizer2.Add(arai_window, 0, wx.ALIGN_LEFT | wx.ALL, 5)

                #-----------box3

                bSizer3 = wx.StaticBoxSizer(wx.StaticBox(
                    pnl1, wx.ID_ANY, "Zijderveld plot"), wx.HORIZONTAL)
                self.show_Zij_temperatures = wx.CheckBox(
                    pnl1, -1, '', (50, 50))
                #self.show_Zij_temperatures_steps=FS.FloatSpin(pnl1, -1, min_val=1, max_val=9,increment=1, value=1, extrastyle=FS.FS_LEFT,size=(50,20))
                # self.show_Zij_temperatures_steps.SetFormat("%f")
                # self.show_Zij_temperatures_steps.SetDigits(0)
                self.show_Zij_temperatures_steps = wx.SpinCtrl(
                    pnl1, -1, '1', (50, 20), (60, -1), min=1, max=9)

                zij_window = wx.GridSizer(2, 2, 12, 12)
                zij_window.AddMany([(wx.StaticText(pnl1, label="show temperatures", style=wx.TE_CENTER), wx.EXPAND),
                                    (wx.StaticText(
                                        pnl1, label="show temperatures but skip steps", style=wx.TE_CENTER), wx.EXPAND),
                                    (self.show_Zij_temperatures, wx.EXPAND),
                                    (self.show_Zij_temperatures_steps, wx.EXPAND)])
                bSizer3.Add(zij_window, 0, wx.ALIGN_LEFT | wx.ALL, 5)

                #-----------box4

                bSizer4 = wx.StaticBoxSizer(wx.StaticBox(
                    pnl1, wx.ID_ANY, "Equal area plot"), wx.HORIZONTAL)
                self.show_eqarea_temperatures = wx.CheckBox(
                    pnl1, -1, '', (50, 50))
                self.show_eqarea_pTRMs = wx.CheckBox(pnl1, -1, '', (50, 50))
                self.show_eqarea_IZZI_colors = wx.CheckBox(
                    pnl1, -1, '', (50, 50))

                eqarea_window = wx.GridSizer(2, 3, 12, 12)
                eqarea_window.AddMany([(wx.StaticText(pnl1, label="show temperatures", style=wx.TE_CENTER), wx.EXPAND),
                                       (wx.StaticText(
                                           pnl1, label="show pTRMs directions", style=wx.TE_CENTER), wx.EXPAND),
                                       (wx.StaticText(pnl1, label="show IZ and ZI in different colors",
                                                      style=wx.TE_CENTER), wx.EXPAND),
                                       (self.show_eqarea_temperatures, wx.EXPAND),
                                       (self.show_eqarea_pTRMs, wx.EXPAND),
                                       (self.show_eqarea_IZZI_colors, wx.EXPAND)])

                bSizer4.Add(eqarea_window, 0, wx.ALIGN_LEFT | wx.ALL, 5)

                #-----------box5

                bSizer5 = wx.StaticBoxSizer(wx.StaticBox(
                    pnl1, wx.ID_ANY, "plots"), wx.HORIZONTAL)
                self.show_NLT_plot = wx.CheckBox(pnl1, -1, '', (50, 50))
                self.show_CR_plot = wx.CheckBox(pnl1, -1, '', (50, 50))

                NLT_window = wx.GridSizer(2, 2, 12, 12)
                NLT_window.AddMany([(wx.StaticText(pnl1, label="show Non-linear TRM plot instead of M/T plot", style=wx.TE_CENTER), wx.EXPAND),
                                    (self.show_NLT_plot, wx.EXPAND),
                                    (wx.StaticText(
                                        pnl1, label="show cooling rate plot instead of equal area plot", style=wx.TE_CENTER), wx.EXPAND),
                                    (self.show_CR_plot, wx.EXPAND)])
                bSizer5.Add(NLT_window, 0, wx.ALIGN_LEFT | wx.ALL, 5)

                #----------------------

                hbox2 = wx.BoxSizer(wx.HORIZONTAL)
                self.okButton = wx.Button(pnl1, wx.ID_OK, "&OK")
                self.cancelButton = wx.Button(pnl1, wx.ID_CANCEL, '&Cancel')
                hbox2.Add(self.okButton)
                hbox2.Add(self.cancelButton)

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
# vbox.AddSpacer(20)

                vbox.Add(hbox2, flag=wx.ALIGN_CENTER_HORIZONTAL)
                vbox.AddSpacer(20)

                pnl1.SetSizer(vbox)
                vbox.Fit(self)

                #---------------------- Initialize  values:

                # set default:
                try:
                    self.gui_resolution.SetValue(
                        "%.0f" % self.preferences["gui_resolution"])
                except:
                    self.gui_resolution.SetValue("100")
                try:
                    self.show_Arai_temperatures.SetValue(
                        self.preferences["show_Arai_temperatures"])
                except:
                    self.show_Arai_temperatures.SetValue(True)
                try:
                    self.show_Arai_temperatures_steps.SetValue(
                        self.preferences["show_Arai_temperatures_steps"])
                except:
                    self.show_Arai_temperatures_steps.SetValue(1.)

                try:
                    self.show_Arai_pTRM_arrows.SetValue(
                        self.preferences["show_Arai_pTRM_arrows"])
                except:
                    self.show_Arai_pTRM_arrows.SetValue(False)
                try:
                    self.show_Zij_temperatures.SetValue(
                        self.preferences["show_Zij_temperatures"])
                except:
                    self.show_Zij_temperatures.SetValue(True)
                try:
                    self.show_Zij_temperatures_steps.SetValue(
                        self.preferences["show_Zij_temperatures_steps"])
                except:
                    self.show_Zij_temperatures_steps.SetValue(1.)
                try:
                    self.show_eqarea_temperatures.SetValue(
                        self.preferences["show_eqarea_temperatures"])
                except:
                    self.show_eqarea_temperatures.SetValue(False)
                try:
                    self.show_eqarea_pTRMs.SetValue(
                        self.preferences["show_eqarea_pTRMs"])
                except:
                    self.show_eqarea_pTRMs.SetValue(False)
                try:
                    self.show_eqarea_IZZI_colors.SetValue(
                        self.preferences["show_eqarea_IZZI_colors"])
                except:
                    self.show_eqarea_IZZI_colors.SetValue(False)
                try:
                    self.show_NLT_plot.SetValue(
                        self.preferences["show_NLT_plot"])
                except:
                    self.show_NLT_plot.SetValue(False)
                try:
                    self.show_CR_plot.SetValue(
                        self.preferences["show_CR_plot"])
                except:
                    self.show_CR_plot.SetValue(False)

# try:
# self.bootstrap_N.SetValue("%.0f"%(self.preferences["BOOTSTRAP_N"]))
# except:
# self.bootstrap_N.SetValue("10000")

                #----------------------

        dia = preferences_appearance_dialog(
            None, "Thellier_gui appearance preferences", self.preferences)
        dia.Center()
        if self.show_dlg(dia) == wx.ID_OK:  # Until the user clicks OK, show the message
            # try:
            change_resolution = False
            if float(dia.gui_resolution.GetValue()) != self.preferences['gui_resolution']:
                change_resolution = True

            self.preferences['gui_resolution'] = float(
                dia.gui_resolution.GetValue())

            # except:
            #     self.preferences['gui_resolution']=100.
            self.preferences['show_Arai_temperatures'] = dia.show_Arai_temperatures.GetValue(
            )
            self.preferences['show_Arai_temperatures_steps'] = dia.show_Arai_temperatures_steps.GetValue(
            )
            self.preferences['show_Arai_pTRM_arrows'] = dia.show_Arai_pTRM_arrows.GetValue(
            )
            self.preferences['show_Zij_temperatures'] = dia.show_Zij_temperatures.GetValue(
            )
            self.preferences['show_Zij_temperatures_steps'] = dia.show_Zij_temperatures_steps.GetValue(
            )
            self.preferences['show_eqarea_temperatures'] = dia.show_eqarea_temperatures.GetValue(
            )
            self.preferences['show_eqarea_pTRMs'] = dia.show_eqarea_pTRMs.GetValue(
            )
            self.preferences['show_eqarea_IZZI_colors'] = dia.show_eqarea_IZZI_colors.GetValue(
            )

            self.preferences['show_NLT_plot'] = dia.show_NLT_plot.GetValue()
            self.preferences['show_CR_plot'] = dia.show_CR_plot.GetValue()
# try:
# self.preferences['BOOTSTRAP_N']=float(dia.bootstrap_N.GetValue())
# except:
# pass

            self.write_preferences_to_file(change_resolution)

    def write_preferences_to_file(self, need_to_close_frame):

        dlg1 = wx.MessageDialog(
            self, caption="Message:", message="Update Thellier GUI preferences?",
            style=wx.OK | wx.CANCEL |wx.ICON_INFORMATION)
        res = self.show_dlg(dlg1)
        dlg1.Destroy()

        if res == wx.ID_OK:
            self.write_preferences_file()

        if need_to_close_frame:
            dlg3 = wx.MessageDialog(
                self, "You need to restart the program.\n", "Confirm Exit", wx.OK | wx.ICON_QUESTION)
            result = self.show_dlg(dlg3)
            dlg3.Destroy()
            if result == wx.ID_OK:
                self.on_menu_exit(None)
                # self.Destroy()
                # sys.exit()

    #-----------------------------------

    def read_preferences_file(self):
        """
        If json preferences file exists, read it in.
        """
        user_data_dir = find_pmag_dir.find_user_data_dir("thellier_gui")
        if not user_data_dir:
            return {}
        if os.path.exists(user_data_dir):
            pref_file = os.path.join(user_data_dir, "thellier_gui_preferences.json")
            if os.path.exists(pref_file):
                with open(pref_file, "r") as pfile:
                    return json.load(pfile)
        return {}

    def write_preferences_file(self):
        """
        Write json preferences file to (platform specific) user data directory,
        or PmagPy directory if appdirs module is missing.
        """
        user_data_dir = find_pmag_dir.find_user_data_dir("thellier_gui")
        if not os.path.exists(user_data_dir):
            find_pmag_dir.make_user_data_dir(user_data_dir)
        pref_file = os.path.join(user_data_dir, "thellier_gui_preferences.json")
        with open(pref_file, "w+") as pfile:
            print('-I- writing preferences to {}'.format(pref_file))
            json.dump(self.preferences, pfile)


    def get_preferences(self):
        # default
        preferences = {}
        preferences['gui_resolution'] = 100.
        preferences['show_Arai_temperatures'] = True
        preferences['show_Arai_temperatures_steps'] = 1.
        preferences['show_Arai_pTRM_arrows'] = True
        preferences['show_Zij_temperatures'] = False
        preferences['show_Zij_temperatures_steps'] = 1.
        preferences['show_eqarea_temperatures'] = False
        preferences['show_eqarea_pTRMs'] = True
        preferences['show_eqarea_IZZI_colors'] = False
        preferences['show_NLT_plot'] = True
        preferences['show_CR_plot'] = True
        preferences['BOOTSTRAP_N'] = 1e4
        preferences['VDM_or_VADM'] = "VADM"
        preferences['show_statistics_on_gui'] = ["int_n", "int_ptrm_n", "frac", "scat", "gmax", "b_beta", "int_mad",
                                                 "int_dang", "f", "fvds", "g", "q", "drats"]  # ,'ptrms_dec','ptrms_inc','ptrms_mad','ptrms_angle']
        # try to read preferences file (new way)
        saved_preferences = self.read_preferences_file()
        preferences.update(saved_preferences)

        # check criteria file
        # if a statistic appear in the criteria file  but does not appear in
        # preferences['show_statistics_on_gui'] than it is added to
        # ['show_statistics_on_gui']:
        for stat in list(self.acceptance_criteria.keys()):
            if self.acceptance_criteria[stat]['category'] in ['IE-SPEC']:
                if self.acceptance_criteria[stat]['value'] != -999:
                    short_crit = stat.split('specimen_')[-1]
                    if short_crit not in preferences['show_statistics_on_gui']:
                        preferences['show_statistics_on_gui'].append(
                            short_crit)
                        print(
                            "-I-", short_crit, " was added to criteria list and will be displayed on screen")

        return(preferences)

    #----------------------------------

    def on_menu_preferences_stat(self, event):

        dia = thellier_gui_dialogs.preferences_stats_dialog(
            None, "Thellier_gui statistical preferences", self.preferences)
        dia.Center()
        if self.show_dlg(dia) == wx.ID_OK:  # Until the user clicks OK, show the message
            try:
                self.preferences['BOOTSTRAP_N'] = float(
                    dia.bootstrap_N.GetValue())
            except:
                pass

            self.preferences['VDM_or_VADM'] = str(dia.v_adm_box.GetValue())

            dlg1 = wx.MessageDialog(
                self, caption="Message:", message="Update Thellier GUI preferences?", style=wx.OK | wx.ICON_INFORMATION)
            res = self.show_dlg(dlg1)
            dlg1.Destroy()

            if res == wx.ID_OK:
                self.write_preferences_file()

            return()

    def on_menu_m_preferences_spd(self, event):

        dia = thellier_gui_dialogs.PI_Statistics_Dialog(
            None, self.preferences["show_statistics_on_gui"], title='SPD list')
        dia.Center()
        if self.show_dlg(dia) == wx.ID_OK:  # Until the user clicks OK, show the message
            self.On_close_spd_box(dia)

    def On_close_spd_box(self, dia):
        if self.preferences["show_statistics_on_gui"] != dia.show_statistics_on_gui:
            self.preferences["show_statistics_on_gui"] = dia.show_statistics_on_gui
            self.write_preferences_to_file(True)
        else:
            pass

    #-----------------------------------

    def on_menu_exit(self, event):
        """
        Runs whenever Thellier GUI exits
        """
        if self.close_warning:
            TEXT = "Data is not saved to a file yet!\nTo properly save your data:\n1) Analysis --> Save current interpretations to a redo file.\nor\n1) File --> Save MagIC tables.\n\n Press OK to exit without saving."
            dlg1 = wx.MessageDialog(
                None, caption="Warning:", message=TEXT, style=wx.OK | wx.CANCEL | wx.ICON_EXCLAMATION)
            if self.show_dlg(dlg1) == wx.ID_OK:
                dlg1.Destroy()
                self.GUI_log.close()
                self.Destroy()
                # if a custom quit event is specified, fire it
                if self.evt_quit:
                    event = self.evt_quit(self.GetId())
                    self.GetEventHandler().ProcessEvent(event)
                if self.standalone:
                    sys.exit()
        else:
            self.GUI_log.close()
            self.Destroy()
            # if a custom quit event is specified, fire it
            if self.evt_quit:
                event = self.evt_quit(self.GetId())
                self.GetEventHandler().ProcessEvent(event)
            if self.standalone:
                sys.exit()

            # self.Destroy() # works if matplotlib isn't using 'WXAgg', otherwise doesn't quit fully
            # wx.Exit() # works by itself, but if called in conjunction with self.Destroy you get a seg error
            # wx.Exit() # forces the program to exit, with no clean up.  works, but not an ideal solution
            # sys.exit() # program closes, but with segmentation error
            # self.Close()  # creates infinite recursion error, because we have
            # a binding to wx.EVT_CLOSE

    def on_save_Arai_plot(self, event):
        # search for NRM:
        nrm0 = ""
        for rec in self.Data[self.s]['datablock']:
            if "LT-NO" in rec['magic_method_codes']:
                nrm0 = "%.2e" % float(rec['measurement_magn_moment'])
                break

        self.fig1.text(0.1, 0.93, '$NRM_0 = %s Am^2 $' % (nrm0), {
                       'family': self.font_type, 'fontsize': 10, 'style': 'normal', 'va': 'center', 'ha': 'left'})
        self.fig1.text(0.9, 0.93, '%s' % (self.s), {
                       'family': self.font_type, 'fontsize': 10, 'style': 'normal', 'va': 'center', 'ha': 'right'})
        # self.canvas1.draw()
        thellier_gui_dialogs.SaveMyPlot(self.fig1, self.pars, "Arai")
        self.fig1.clear()
        self.fig1.text(0.01, 0.98, "Arai plot", {
                       'family': self.font_type, 'fontsize': 10, 'style': 'normal', 'va': 'center', 'ha': 'left'})
        self.araiplot = self.fig1.add_axes([0.1, 0.1, 0.8, 0.8])
        self.draw_figure(self.s)
        self.update_selection()

    def on_save_Zij_plot(self, event):
        self.fig2.text(0.9, 0.96, '%s' % (self.s), {
                       'family': self.font_type, 'fontsize': 10, 'style': 'normal', 'va': 'center', 'ha': 'right'})
        # self.canvas1.draw()
        thellier_gui_dialogs.SaveMyPlot(self.fig2, self.pars, "Zij")
        self.fig2.clear()
        self.fig2.text(0.02, 0.96, "Zijderveld", {
                       'family': self.font_type, 'fontsize': 10, 'style': 'normal', 'va': 'center', 'ha': 'left'})
        self.zijplot = self.fig2.add_subplot(111)
        self.draw_figure(self.s)
        self.update_selection()

    def on_save_Eq_plot(self, event):
        self.fig3.text(0.9, 0.96, '%s' % (self.s), {
                       'family': self.font_type, 'fontsize': 10, 'style': 'normal', 'va': 'center', 'ha': 'right'})
        thellier_gui_dialogs.SaveMyPlot(self.fig3, self.pars, "Eqarea")
        self.fig3.clear()
        self.fig3.text(0.02, 0.96, "Equal area", {
                       'family': self.font_type, 'fontsize': 10, 'style': 'normal', 'va': 'center', 'ha': 'left'})
        self.eqplot = self.fig3.add_subplot(111)
        self.draw_figure(self.s)
        self.update_selection()

    def on_save_M_t_plot(self, event):
        if self.preferences['show_NLT_plot'] == False or 'NLT_parameters' not in list(self.Data[self.s].keys()):
            self.fig5.text(0.9, 0.96, '%s' % (self.s), {
                           'family': self.font_type, 'fontsize': 10, 'style': 'normal', 'va': 'center', 'ha': 'right'})
            thellier_gui_dialogs.SaveMyPlot(self.fig5, self.pars, "M_T")
            self.fig5.clear()
            self.mplot = self.fig5.add_axes(
                [0.2, 0.15, 0.7, 0.7], frameon=True, facecolor='None')
            self.fig5.text(0.02, 0.96, "M/T", {'family': self.font_type,
                                               'fontsize': 10, 'style': 'normal', 'va': 'center', 'ha': 'left'})
            self.draw_figure(self.s)
            self.update_selection()
        else:
            return

    def on_save_sample_plot(self, event):
        self.fig4.text(0.9, 0.96, '%s' % (self.Data_hierarchy['specimens'][self.s]), {
                       'family': self.font_type, 'fontsize': 10, 'style': 'normal', 'va': 'center', 'ha': 'right'})
        thellier_gui_dialogs.SaveMyPlot(self.fig4, self.pars, "Sample")
        self.fig4.clear()
        self.fig4.text(0.02, 0.96, "Sample data", {
                       'family': self.font_type, 'fontsize': 10, 'style': 'normal', 'va': 'center', 'ha': 'left'})
        self.sampleplot = self.fig4.add_axes(
            [0.2, 0.3, 0.7, 0.6], frameon=True, facecolor='None')
        self.draw_figure(self.s)
        self.update_selection()

    def on_save_NLT_plot(self, event):
        if self.preferences['show_NLT_plot'] == True and 'NLT_parameters' in list(self.Data[self.s].keys()):
            self.fig5.text(0.9, 0.96, '%s' % (self.s), {
                           'family': self.font_type, 'fontsize': 10, 'style': 'normal', 'va': 'center', 'ha': 'right'})
            thellier_gui_dialogs.SaveMyPlot(self.fig5, self.pars, "NLT")
            self.fig5.clear()
            self.mplot = self.fig5.add_axes(
                [0.2, 0.15, 0.7, 0.7], frameon=True, facecolor='None')
            self.fig5.text(0.02, 0.96, "Non-linear TRM check", {
                           'family': self.font_type, 'fontsize': 10, 'style': 'normal', 'va': 'center', 'ha': 'left'})
            self.draw_figure(self.s)
            self.update_selection()
        else:
            return

    def on_save_CR_plot(self, event):
        if self.preferences['show_CR_plot'] == True and 'cooling_rate_data' in list(self.Data[self.s].keys()):
            self.fig3.text(0.9, 0.96, '%s' % (self.s), {
                           'family': self.font_type, 'fontsize': 10, 'style': 'normal', 'va': 'center', 'ha': 'right'})
            thellier_gui_dialogs.SaveMyPlot(self.fig3, self.pars, "CR")
            self.fig3.clear()
            self.eqplot = self.fig3.add_axes(
                [0.2, 0.15, 0.7, 0.7], frameon=True, facecolor='None')
            self.fig3.text(0.02, 0.96, "Cooling rate correction", {
                           'family': self.font_type, 'fontsize': 10, 'style': 'normal', 'va': 'center', 'ha': 'left'})
            self.draw_figure(self.s)
            self.update_selection()
        else:
            pw.simple_warning("No cooling rate plot available to save")
            return

    def on_menu_previous_interpretation(self, event):
        """
        Create and show the Open FileDialog for upload previous interpretation
        input should be a valid "redo file":
        [specimen name] [tmin(kelvin)] [tmax(kelvin)]
        """
        save_current_specimen = self.s
        dlg = wx.FileDialog(
            self, message="choose a file in a pmagpy redo format",
            defaultDir=self.WD,
            defaultFile="thellier_GUI.redo",
            wildcard="*.redo",
            style=wx.FD_OPEN | wx.FD_CHANGE_DIR
        )
        if self.show_dlg(dlg) == wx.ID_OK:
            redo_file = dlg.GetPath()
            if self.test_mode:
                redo_file = "thellier_GUI.redo"
        else:
            redo_file = None
        dlg.Destroy()

        print("redo_file", redo_file)
        if redo_file:
            self.read_redo_file(redo_file)
    #----------------------------------------------------------------------

    def on_menu_change_working_directory(self, event):

        self.redo_specimens = {}
        self.currentDirectory = os.getcwd()  # get the current working directory
        self.get_DIR()  # choose directory dialog
        acceptance_criteria_default, acceptance_criteria_null = pmag.initialize_acceptance_criteria(
            data_model=self.data_model), pmag.initialize_acceptance_criteria(data_model=self.data_model)  # inialize Null selecting criteria

        self.acceptance_criteria_null = acceptance_criteria_null
        self.acceptance_criteria_default = acceptance_criteria_default
        self.Data, self.Data_hierarchy, self.Data_info = {}, {}, {}
        # get all ages, locations etc. (from er_ages, er_sites, er_locations)
        self.Data_info = self.get_data_info()
        # Get data from magic_measurements and rmag_anisotropy if exist.
        self.Data, self.Data_hierarchy = self.get_data()
        self.Data_samples = {}
        self.Data_sites = {}
        self.last_saved_pars = {}
        self.specimens = list(self.Data.keys())         # get list of specimens
        self.specimens.sort()                   # get list of specimens

        # updtate plots and data
        self.specimens_box.SetItems(self.specimens)
        self.s = self.specimens[0]
        self.specimens_box.SetStringSelection(self.s)
        self.update_selection()

    #----------------------------------------------------------------------

    def on_menu_add_working_directory(self, event):

        # self.redo_specimens={}
        self.currentDirectory = os.getcwd()  # get the current working directory
        dialog = wx.DirDialog(None, "Choose a magic project directory:", defaultPath=self.currentDirectory,
                              style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON | wx.DD_CHANGE_DIR)
        if self.show_dlg(dialog) == wx.ID_OK:
            new_magic_dir = dialog.GetPath()
        dialog.Destroy()

        self.WD = new_magic_dir
        self.magic_file = os.path.join(new_magic_dir, "magic_measurements.txt")

        new_Data_info = self.get_data_info()
        new_Data, new_Data_hierarchy = self.get_data()

        self.Data.update(new_Data)

        self.Data_hierarchy['samples'].update(new_Data_hierarchy['samples'])
        self.Data_hierarchy['specimens'].update(
            new_Data_hierarchy['specimens'])
        self.Data_info["er_samples"].update(new_Data_info["er_samples"])
        self.Data_info["er_sites"].update(new_Data_info["er_sites"])
        self.Data_info["er_ages"].update(new_Data_info["er_ages"])

        # self.Data_samples={}
        # self.last_saved_pars={}

        self.specimens = list(self.Data.keys())         # get list of specimens
        self.specimens.sort()                   # get list of specimens

        # updtate plots and data
        self.WD = self.currentDirectory
        self.specimens_box.SetItems(self.specimens)
        self.s = self.specimens[0]
        self.specimens_box.SetStringSelection(self.s)
        self.update_selection()

    #----------------------------------------------------------------------

    def on_menu_m_open_magic_tree(self, event):
        if self.data_model == 3:
            pw.simple_warning("""This functionality is not currently available.
You can combine multiple measurement files into one measurement file using Pmag GUI.""")
        else:
            self.open_magic_tree()

    def open_magic_tree(self):
        # busy_frame.Center()
        if FIRST_RUN and "-tree" in sys.argv:
            new_dir = self.WD
        else:
            dialog = wx.DirDialog(None, "Choose a path. All magic directories in the path will be imported:",
                                  defaultPath=self.currentDirectory, style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON | wx.DD_CHANGE_DIR)
            ok = self.show_dlg(dialog)
            if ok == wx.ID_OK:
                new_dir = dialog.GetPath()
            dialog.Destroy()

        busy_frame = wx.BusyInfo(
            "Loading data\n It may take few seconds, depending on the number of specimens ...", self)
        # os.chdir(new_dir)
        if self.data_model == 3:
            meas_file = 'measurements.txt'
        else:
            meas_file = 'magic_measurements.txt'
        for FILE in os.listdir(new_dir):
            path = new_dir + "/" + FILE
            if os.path.isdir(path) and not path.startswith('.'):
                print("importing from path %s" % path)
                # try:
                self.WD = path
                self.magic_file = os.path.join(path, meas_file)
                new_Data_info = self.get_data_info()
                self.Data_info["er_samples"].update(
                    new_Data_info["er_samples"])
                self.Data_info["er_sites"].update(new_Data_info["er_sites"])
                self.Data_info["er_ages"].update(new_Data_info["er_ages"])
                new_Data, new_Data_hierarchy = self.get_data()
                if new_Data == {}:
                    print("-E- ERROR importing MagIC data from path.")
                    continue

                self.Data_hierarchy['samples'].update(
                    new_Data_hierarchy['samples'])
                self.Data_hierarchy['sites'].update(
                    new_Data_hierarchy['sites'])
                self.Data_hierarchy['specimens'].update(
                    new_Data_hierarchy['specimens'])
                self.Data_hierarchy['sample_of_specimen'].update(
                    new_Data_hierarchy['sample_of_specimen'])
                self.Data_hierarchy['site_of_specimen'].update(
                    new_Data_hierarchy['site_of_specimen'])
                self.Data_hierarchy['site_of_sample'].update(
                    new_Data_hierarchy['site_of_sample'])

                self.Data.update(new_Data)
                # except:
        self.specimens = list(self.Data.keys())         # get list of specimens
        self.specimens.sort()                   # get list of specimens

        # updtate plots and data
        if not FIRST_RUN:
            self.WD = self.currentDirectory
            self.specimens_box.SetItems(self.specimens)
            self.s = self.specimens[0]
            self.specimens_box.SetStringSelection(self.s)
            self.update_selection()
        del busy_frame
    #----------------------------------------------------------------------

    def on_menu_open_magic_file(self, event):
        dlg = wx.FileDialog(
            self, message="choose a MagIC format measurement file",
            defaultDir=self.currentDirectory,
            defaultFile="",
            # wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_CHANGE_DIR
        )
        if self.show_dlg(dlg) == wx.ID_OK:
            new_magic_file = dlg.GetPath()
            # print "You chose the following file(s):"
        dlg.Destroy()
        self.magic_file = new_magic_file
        path = new_magic_file.split("/")
        self.WD = new_magic_file.strip(path[-1])

        # self.Data,self.Data_hierarchy=self.get_data(self.data_model)
        # self.Data_info=self.get_data_info()
        self.Data_info = self.get_data_info()
        self.Data, self.Data_hierarchy = self.get_data()

        self.redo_specimens = {}
        self.specimens = list(self.Data.keys())
        self.specimens.sort()
        self.specimens_box.SetItems(self.specimens)
        self.s = self.specimens[0]
        self.update_selection()

    #----------------------------------------------------------------------

    def on_menu_criteria_file(self, event):
        """
        read pmag_criteria.txt file
        and open change criteria dialog
        """
        if self.data_model == 3:
            dlg = wx.FileDialog(
                self, message="choose a file in MagIC Data Model 3.0  format",
                defaultDir=self.WD,
                defaultFile="criteria.txt",
                style=wx.FD_OPEN | wx.FD_CHANGE_DIR
            )
        else:
            dlg = wx.FileDialog(
                self, message="choose a file in a MagIC Data Model 2.5 pmagpy format",
                defaultDir=self.WD,
                defaultFile="pmag_criteria.txt",
                # wildcard=wildcard,
                style=wx.FD_OPEN | wx.FD_CHANGE_DIR
            )

        if self.show_dlg(dlg) == wx.ID_OK:
            criteria_file = dlg.GetPath()
            self.GUI_log.write(
                "-I- Read new criteria file: %s\n" % criteria_file)
        dlg.Destroy()
        replace_acceptance_criteria = pmag.initialize_acceptance_criteria(
            data_model=self.data_model)
        try:
            if self.data_model == 3:
                self.read_criteria_file(criteria_file)
                replace_acceptance_criteria = self.acceptance_criteria
                # replace_acceptance_criteria=pmag.read_criteria_from_file(criteria_file,replace_acceptance_criteria,data_model=self.data_model)
                # # just to see if file exists
                print(replace_acceptance_criteria)
            else:
                replace_acceptance_criteria = pmag.read_criteria_from_file(
                    criteria_file, replace_acceptance_criteria, data_model=self.data_model)  # just to see if file exists
        except Exception as ex:
            print('-W-', ex)
            dlg1 = wx.MessageDialog(
                self, caption="Error:", message="error in reading file", style=wx.OK)
            result = self.show_dlg(dlg1)
            if result == wx.ID_OK:
                dlg1.Destroy()
                return
        self.add_thellier_gui_criteria()
        self.read_criteria_file(criteria_file)
        # check if some statistics are in the new criteria but not in old. If
        # yes, add to  self.preferences['show_statistics_on_gui']
        crit_list_not_in_pref = []
        for crit in list(self.acceptance_criteria.keys()):
            if self.acceptance_criteria[crit]['category'] == "IE-SPEC":
                if self.acceptance_criteria[crit]['value'] != -999:
                    short_crit = crit.split('specimen_')[-1]
                    if short_crit not in self.preferences['show_statistics_on_gui']:
                        print("-I- statistic %s is not in your preferences" % crit)
                        self.preferences['show_statistics_on_gui'].append(
                            short_crit)
                        crit_list_not_in_pref.append(crit)
        if len(crit_list_not_in_pref) > 0:
            stat_list = ":".join(crit_list_not_in_pref)
            dlg1 = wx.MessageDialog(self, caption="WARNING:",
                                    message="statistics '%s' is in the imported criteria file but not in your appearence preferences.\nThis statistic will not appear on the gui panel.\n The program will exit after saving new acceptance criteria, and it will be added automatically the next time you open it " % stat_list,
                                    style=wx.OK | wx.ICON_INFORMATION)
            self.show_dlg(dlg1)
            dlg1.Destroy()

        dia = thellier_gui_dialogs.Criteria_Dialog(
            None, self.acceptance_criteria, self.preferences, title='Acceptance Criteria')
        dia.Center()
        result = self.show_dlg(dia)
        if result == wx.ID_OK:  # Until the user clicks OK, show the message
            self.On_close_criteria_box(dia)
            if len(crit_list_not_in_pref) > 0:
                dlg1 = wx.MessageDialog(self, caption="WARNING:",
                                        message="Exiting now! When you restart the gui all the new statistics will be added.",
                                        style=wx.OK | wx.ICON_INFORMATION)
                self.show_dlg(dlg1)
                dlg1.Destroy()
                self.on_menu_exit(None)
                # self.Destroy()
                # sys.exit()

        if result == wx.ID_CANCEL:  # Until the user clicks OK, show the message
            for crit in crit_list_not_in_pref:
                short_crit = crit.split('specimen_')[-1]
                self.preferences['show_statistics_on_gui'].remove(short_crit)

    #----------------------------------------------------------------------

    def on_menu_criteria(self, event):
        """
        Change acceptance criteria
        and save it to the criteria file (data_model=2: pmag_criteria.txt; data_model=3: criteria.txt)
        """

        dia = thellier_gui_dialogs.Criteria_Dialog(
            None, self.acceptance_criteria, self.preferences, title='Set Acceptance Criteria')
        dia.Center()
        result = self.show_dlg(dia)

        if result == wx.ID_OK:  # Until the user clicks OK, show the message
            self.On_close_criteria_box(dia)

    def On_close_criteria_box(self, dia):
        """
        after criteria dialog window is closed.
        Take the acceptance criteria values and update
        self.acceptance_criteria
        """
        criteria_list = list(self.acceptance_criteria.keys())
        criteria_list.sort()

        #---------------------------------------
        # check if averaging by sample or by site
        # and intialize sample/site criteria
        #---------------------------------------
        avg_by = dia.set_average_by_sample_or_site.GetValue()
        if avg_by == 'sample':
            for crit in ['site_int_n', 'site_int_sigma', 'site_int_sigma_perc', 'site_aniso_mean', 'site_int_n_outlier_check']:
                self.acceptance_criteria[crit]['value'] = -999

        if avg_by == 'site':
            for crit in ['sample_int_n', 'sample_int_sigma', 'sample_int_sigma_perc', 'sample_aniso_mean', 'sample_int_n_outlier_check']:
                self.acceptance_criteria[crit]['value'] = -999

        #---------
        # get value for each criterion
        for i in range(len(criteria_list)):
            crit = criteria_list[i]
            value, accept = dia.get_value_for_crit(crit, self.acceptance_criteria)
            if accept:
                self.acceptance_criteria.update(accept)
        #---------
        # thellier interpreter calculation type
        if dia.set_stdev_opt.GetValue() == True:
            self.acceptance_criteria['interpreter_method']['value'] = 'stdev_opt'
        elif dia.set_bs.GetValue() == True:
            self.acceptance_criteria['interpreter_method']['value'] = 'bs'
        elif dia.set_bs_par.GetValue() == True:
            self.acceptance_criteria['interpreter_method']['value'] = 'bs_par'

        #  message dialog
        dlg1 = wx.MessageDialog(
            self, caption="Warning:", message="changes are saved to the criteria file\n ", style=wx.OK)
        result = self.show_dlg(dlg1)
        if result == wx.ID_OK:
            try:
                self.clear_boxes()
            except IndexError:
                pass
            try:
                self.write_acceptance_criteria_to_boxes()
            except IOError:
                pass
            if self.data_model == 3:
                crit_file = 'criteria.txt'
            else:
                crit_file = 'pmag_criteria.txt'
            try:
                pmag.write_criteria_to_file(os.path.join(
                    self.WD, crit_file), self.acceptance_criteria, data_model=self.data_model, prior_crits=self.crit_data)
            except AttributeError as ex:
                print(ex)
                print("no criteria given to save")
            dlg1.Destroy()
            dia.Destroy()

        self.fig4.texts[0].remove()
        txt = "{} data".format(avg_by).capitalize()
        self.fig4.text(0.02, 0.96, txt, {
                       'family': self.font_type, 'fontsize': 10, 'style': 'normal', 'va': 'center', 'ha': 'left'})
        self.recalculate_satistics()
        try:
            self.update_GUI_with_new_interpretation()
        except KeyError:
            pass

    # only a valid number can be entered to boxes
    # used by On_close_criteria_box


    def recalculate_satistics(self):
        '''
        update self.Data[specimen]['pars'] for all specimens.
        '''
        gframe = wx.BusyInfo(
            "Re-calculating statistics for all specimens\n Please wait..", self)

        for specimen in list(self.Data.keys()):
            if 'pars' not in list(self.Data[specimen].keys()):
                continue
            if 'specimen_int_uT' not in list(self.Data[specimen]['pars'].keys()):
                continue
            tmin = self.Data[specimen]['pars']['measurement_step_min']
            tmax = self.Data[specimen]['pars']['measurement_step_max']
            pars = thellier_gui_lib.get_PI_parameters(
                self.Data, self.acceptance_criteria, self.preferences, specimen, tmin, tmax, self.GUI_log, THERMAL, MICROWAVE)
            self.Data[specimen]['pars'] = pars
            self.Data[specimen]['pars']['lab_dc_field'] = self.Data[specimen]['lab_dc_field']
            self.Data[specimen]['pars']['er_specimen_name'] = self.Data[specimen]['er_specimen_name']
            self.Data[specimen]['pars']['er_sample_name'] = self.Data[specimen]['er_sample_name']
        del gframe

    #----------------------------------------------------------------------

    def read_criteria_file(self, criteria_file):
        '''
        read criteria file.
        initialize self.acceptance_criteria
        try to guess if averaging by sample or by site.
        '''
        if self.data_model == 3:
            self.acceptance_criteria = pmag.initialize_acceptance_criteria(
                data_model=self.data_model)
            self.add_thellier_gui_criteria()
            fnames = {'criteria': criteria_file}
            contribution = cb.Contribution(
                self.WD, custom_filenames=fnames, read_tables=['criteria'])
            if 'criteria' in contribution.tables:
                crit_container = contribution.tables['criteria']
                crit_data = crit_container.df
                crit_data['definition'] = 'acceptance criteria for study'
                # convert to list of dictionaries
                self.crit_data = crit_data.to_dict('records')
                for crit in self.crit_data:  # step through and rename every f-ing one
                    # magic2[magic3.index(crit['table_column'])] # find data
                    # model 2.5 name
                    m2_name = map_magic.convert_intensity_criteria(
                        'magic2', crit['table_column'])
                    if not m2_name:
                        pass
                    elif m2_name not in self.acceptance_criteria:
                        print('-W- Your criteria file contains {}, which is not currently supported in Thellier GUI.'.format(m2_name))
                        print('    This record will be skipped:\n    {}'.format(crit))
                    else:
                        if m2_name != crit['table_column'] and 'scat' not in m2_name != "":
                            self.acceptance_criteria[m2_name]['value'] = float(
                                crit['criterion_value'])
                            self.acceptance_criteria[m2_name]['pmag_criteria_code'] = crit['criterion']
                        if m2_name != crit['table_column'] and 'scat' in m2_name != "":
                            if crit['criterion_value'] == 'True':
                                self.acceptance_criteria[m2_name]['value'] = 1
                            else:
                                self.acceptance_criteria[m2_name]['value'] = 0
            else:
                print("-E- Can't read criteria file")

        else:  # Do it the data model 2.5 way:
            self.crit_data = {}
            try:
                self.acceptance_criteria = pmag.read_criteria_from_file(
                    criteria_file, self.acceptance_criteria)
            except:
                print("-E- Can't read pmag criteria file")
        # guesss if average by site or sample:
        by_sample = True
        flag = False
        for crit in ['sample_int_n', 'sample_int_sigma_perc', 'sample_int_sigma']:
            if self.acceptance_criteria[crit]['value'] == -999:
                flag = True
        if flag:
            for crit in ['site_int_n', 'site_int_sigma_perc', 'site_int_sigma']:
                if self.acceptance_criteria[crit]['value'] != -999:
                    by_sample = False
        if not by_sample:
            self.acceptance_criteria['average_by_sample_or_site']['value'] = 'site'

    def on_menu_save_interpretation(self, event):
        '''
        save interpretations to a redo file
        '''

        thellier_gui_redo_file = open(
            os.path.join(self.WD, "thellier_GUI.redo"), 'w')

        #--------------------------------------------------
        #  write interpretations to thellier_GUI.redo
        #--------------------------------------------------
        spec_list = list(self.Data.keys())
        spec_list.sort()
        redo_specimens_list = []
        for sp in spec_list:
            if 'saved' not in self.Data[sp]['pars']:
                continue
            if not self.Data[sp]['pars']['saved']:
                continue
            redo_specimens_list.append(sp)

            thellier_gui_redo_file.write("%s %.0f %.0f\n" % (
                sp, self.Data[sp]['pars']['measurement_step_min'], self.Data[sp]['pars']['measurement_step_max']))
        dlg1 = wx.MessageDialog(
            self, caption="Saved:", message="File thellier_GUI.redo is saved in MagIC working folder", style=wx.OK)
        result = self.show_dlg(dlg1)
        if result == wx.ID_OK:
            dlg1.Destroy()
            thellier_gui_redo_file.close()
            return

        thellier_gui_redo_file.close()
        self.close_warning = False

    def on_menu_clear_interpretation(self, event):
        '''
        clear all current interpretations.
        '''

        #  delete all previous interpretation
        for sp in list(self.Data.keys()):
            del self.Data[sp]['pars']
            self.Data[sp]['pars'] = {}
            self.Data[sp]['pars']['lab_dc_field'] = self.Data[sp]['lab_dc_field']
            self.Data[sp]['pars']['er_specimen_name'] = self.Data[sp]['er_specimen_name']
            self.Data[sp]['pars']['er_sample_name'] = self.Data[sp]['er_sample_name']
        self.Data_samples = {}
        self.Data_sites = {}
        self.tmin_box.SetValue("")
        self.tmax_box.SetValue("")
        self.clear_boxes()
        self.draw_figure(self.s)

    #--------------------------------------------------------------------

    def on_menu_calculate_aniso_tensor(self, event):
        res, error = self.calculate_anisotropy_tensors(data_model=self.data_model)
        if res:
            if self.data_model == 3:
                text1 = "Anisotropy elements and statistics are saved in specimens.txt\n"
                text2 = ""
            else:
                text1 = "Anisotropy tensors elements are saved in rmag_anisotropy.txt\n"
                text2 = "Other anisotropy statistics are saved in rmag_results.txt\n"
        else:
            if self.data_model == 3:
                text1 = error
                text2 = ""
            else:
                text1 = error
                text2 = ""

        dlg1 = wx.MessageDialog(
            self, caption="Message:", message=text1 + text2, style=wx.OK | wx.ICON_INFORMATION)
        self.show_dlg(dlg1)
        dlg1.Destroy()

    #========================================================
    # Anisotropy tensors
    #========================================================

    def calculate_anisotropy_tensors(self, **kwargs):

        # removed function tauV because it wasn't used


        def calculate_aniso_parameters(B, K):
            """
            Menubar --> Anisotropy --> Calculate anisotropy tensors
            """

            aniso_parameters = {}
            S_bs = np.dot(B, K)

            # normalize by trace
            trace = S_bs[0] + S_bs[1] + S_bs[2]
            S_bs = S_bs / trace
            s1, s2, s3, s4, s5, s6 = S_bs[0], S_bs[1], S_bs[2], S_bs[3], S_bs[4], S_bs[5]
            s_matrix = [[s1, s4, s6], [s4, s2, s5], [s6, s5, s3]]

            # calculate eigen vector,
            t, evectors = eig(s_matrix)
            # sort vectors
            t = list(t)
            t1 = max(t)
            ix_1 = t.index(t1)
            t3 = min(t)
            ix_3 = t.index(t3)
            for tt in range(3):
                if t[tt] != t1 and t[tt] != t3:
                    t2 = t[tt]
                    ix_2 = t.index(t2)

            v1 = [evectors[0][ix_1], evectors[1][ix_1], evectors[2][ix_1]]
            v2 = [evectors[0][ix_2], evectors[1][ix_2], evectors[2][ix_2]]
            v3 = [evectors[0][ix_3], evectors[1][ix_3], evectors[2][ix_3]]

            DIR_v1 = pmag.cart2dir(v1)
            DIR_v2 = pmag.cart2dir(v2)
            DIR_v3 = pmag.cart2dir(v3)

            aniso_parameters['anisotropy_s1'] = "%f" % s1
            aniso_parameters['anisotropy_s2'] = "%f" % s2
            aniso_parameters['anisotropy_s3'] = "%f" % s3
            aniso_parameters['anisotropy_s4'] = "%f" % s4
            aniso_parameters['anisotropy_s5'] = "%f" % s5
            aniso_parameters['anisotropy_s6'] = "%f" % s6
            aniso_parameters['anisotropy_degree'] = "%f" % (t1 / t3)
            aniso_parameters['anisotropy_t1'] = "%f" % t1
            aniso_parameters['anisotropy_t2'] = "%f" % t2
            aniso_parameters['anisotropy_t3'] = "%f" % t3
            aniso_parameters['anisotropy_v1_dec'] = "%.1f" % DIR_v1[0]
            aniso_parameters['anisotropy_v1_inc'] = "%.1f" % DIR_v1[1]
            aniso_parameters['anisotropy_v2_dec'] = "%.1f" % DIR_v2[0]
            aniso_parameters['anisotropy_v2_inc'] = "%.1f" % DIR_v2[1]
            aniso_parameters['anisotropy_v3_dec'] = "%.1f" % DIR_v3[0]
            aniso_parameters['anisotropy_v3_inc'] = "%.1f" % DIR_v3[1]

            # modified from pmagpy:
            if len(K) / 3 == 9 or len(K) / 3 == 6 or len(K) / 3 == 15:
                n_pos = len(K) / 3
                tmpH = Matrices[n_pos]['tmpH']
                a = s_matrix
                S = 0.
                comp = np.zeros((int(n_pos) * 3), 'f')
                for i in range(int(n_pos)):
                    for j in range(3):
                        index = i * 3 + j
                        compare = a[j][0] * tmpH[i][0] + a[j][1] * \
                            tmpH[i][1] + a[j][2] * tmpH[i][2]
                        comp[index] = compare
                for i in range(int(n_pos * 3)):
                    d = K[i] / trace - comp[i]  # del values
                    S += d * d
                nf = float(n_pos * 3 - 6)  # number of degrees of freedom
                if S > 0:
                    sigma = np.sqrt(S / nf)
                hpars = pmag.dohext(nf, sigma, [s1, s2, s3, s4, s5, s6])

                aniso_parameters['anisotropy_sigma'] = "%f" % sigma
                aniso_parameters['anisotropy_ftest'] = "%f" % hpars["F"]
                aniso_parameters['anisotropy_ftest12'] = "%f" % hpars["F12"]
                aniso_parameters['anisotropy_ftest23'] = "%f" % hpars["F23"]
                aniso_parameters['result_description'] = "Critical F: %s" % (
                    hpars['F_crit'])
                aniso_parameters['anisotropy_F_crit'] = "%f" % float(
                    hpars['F_crit'])
                aniso_parameters['anisotropy_n'] = '%i' % (n_pos)
                if float(hpars["F"]) > float(hpars['F_crit']):
                    aniso_parameters['result_quality'] = 'g'
                else:
                    aniso_parameters['result_quality'] = 'b'
            return(aniso_parameters)

        if self.data_model == 3:
            aniso_logfile = open(os.path.join(self.WD, "anisotropy.log"), 'w')
        else:
            aniso_logfile = open(os.path.join(
                self.WD, "rmag_anisotropy.log"), 'w')

        aniso_logfile.write("------------------------\n")
        aniso_logfile.write("-I- Start anisotropy script\n")
        aniso_logfile.write("------------------------\n")

        #-----------------------------------
        # If data_model=2.5: Prepare anisotropy file for writing (data_model=3 anisotropy data go in the specimens.txt file)
        #-----------------------------------
        if self.data_model != 3:
            rmag_anisotropy_file = open(os.path.join(
                self.WD, "rmag_anisotropy.txt"), 'w')
            rmag_anisotropy_file.write("tab\trmag_anisotropy\n")

            rmag_results_file = open(os.path.join(
                self.WD, "rmag_results.txt"), 'w')
            rmag_results_file.write("tab\trmag_results\n")

            rmag_anisotropy_header = ['er_specimen_name', 'er_sample_name', 'er_site_name', 'anisotropy_type', 'anisotropy_n', 'anisotropy_description', 'anisotropy_s1',
                                      'anisotropy_s2', 'anisotropy_s3', 'anisotropy_s4', 'anisotropy_s5', 'anisotropy_s6', 'anisotropy_sigma', 'anisotropy_alt', 'magic_experiment_names', 'magic_method_codes']

            String = ""
            for i in range(len(rmag_anisotropy_header)):
                String = String + rmag_anisotropy_header[i] + '\t'
            rmag_anisotropy_file.write(String[:-1] + "\n")

            rmag_results_header = ['er_specimen_names', 'er_sample_names', 'er_site_names', 'anisotropy_type', 'magic_method_codes', 'magic_experiment_names', 'result_description', 'anisotropy_t1', 'anisotropy_t2', 'anisotropy_t3', 'anisotropy_ftest', 'anisotropy_ftest12', 'anisotropy_ftest23',
                                   'anisotropy_v1_dec', 'anisotropy_v1_inc', 'anisotropy_v2_dec', 'anisotropy_v2_inc', 'anisotropy_v3_dec', 'anisotropy_v3_inc']

            String = ""
            for i in range(len(rmag_results_header)):
                String = String + rmag_results_header[i] + '\t'
            rmag_results_file.write(String[:-1] + "\n")

        #-----------------------------------
        # Matrices definitions:
        # A design matrix
        # B np.dot(inv(np.dot(A.transpose(),A)),A.transpose())
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

        Matrices = {}

        for n_pos in [6, 9, 15]:

            Matrices[n_pos] = {}

            A = np.zeros((n_pos * 3, 6), 'f')

            if n_pos == 6:
                positions = [[0., 0., 1.], [90., 0., 1.], [0., 90., 1.],
                             [180., 0., 1.], [270., 0., 1.], [0., -90., 1.]]

            if n_pos == 15:
                positions = [[315., 0., 1.], [225., 0., 1.], [180., 0., 1.], [135., 0., 1.], [45., 0., 1.],
                             [90., -45., 1.], [270., -45., 1.], [270.,
                                                                 0., 1.], [270., 45., 1.], [90., 45., 1.],
                             [180., 45., 1.], [180., -45., 1.], [0., -90., 1.], [0, -45., 1.], [0, 45., 1.]]
            if n_pos == 9:
                positions = [[315., 0., 1.], [225., 0., 1.], [180., 0., 1.],
                             [90., -45., 1.], [270., -45., 1.], [270., 0., 1.],
                             [180., 45., 1.], [180., -45., 1.], [0., -90., 1.]]

            tmpH = np.zeros((n_pos, 3), 'f')  # define tmpH
            for i in range(len(positions)):
                CART = pmag.dir2cart(positions[i])
                a = CART[0]
                b = CART[1]
                c = CART[2]
                A[3 * i][0] = a
                A[3 * i][3] = b
                A[3 * i][5] = c

                A[3 * i + 1][1] = b
                A[3 * i + 1][3] = a
                A[3 * i + 1][4] = c

                A[3 * i + 2][2] = c
                A[3 * i + 2][4] = b
                A[3 * i + 2][5] = a

                tmpH[i][0] = CART[0]
                tmpH[i][1] = CART[1]
                tmpH[i][2] = CART[2]

            B = np.dot(inv(np.dot(A.transpose(), A)), A.transpose())

            Matrices[n_pos]['A'] = A
            Matrices[n_pos]['B'] = B
            Matrices[n_pos]['tmpH'] = tmpH

        #====================================================================

        Data_anisotropy = {}
        specimens = list(self.Data.keys())
        specimens.sort()
        for specimen in specimens:

            if 'atrmblock' in list(self.Data[specimen].keys()):
                experiment = self.Data[specimen]['atrmblock'][0]['magic_experiment_name']

                #-----------------------------------
                # aTRM 6 positions
                #-----------------------------------

                aniso_logfile.write(
                    "-I- Start calculating ATRM tensor for specimen %s\n" % specimen)
                atrmblock = self.Data[specimen]['atrmblock']
                trmblock = self.Data[specimen]['trmblock']
                zijdblock = self.Data[specimen]['zijdblock']
                if len(atrmblock) < 6:
                    aniso_logfile.write(
                        "-W- specimen %s does not have enough measurements for 6 positions ATRM calculation\n" % specimen)
                    continue

                B = Matrices[6]['B']

                Reject_specimen = False

                # The zero field step is a "baseline"
                # and the atrm measurements are substructed from the baseline
                # if there is a zero field is in the atrm block: then use this measurement as a baseline
                # if not, the program searches for the zero-field step in the zijderveld block.
                # the baseline is the average of all the zero field steps in
                # the same temperature (in case there is more than one)

                # Search the baseline in the ATRM measurement
                # Search the alteration check in the ATRM measurement
                # If there is more than one baseline measurements then avrage
                # all measurements

                baseline = ""
                Alteration_check = ""
                Alteration_check_index = ""
                baselines = []

                # search for baseline in atrm blocks
                for rec in atrmblock:
                    dec = float(rec['measurement_dec'])
                    inc = float(rec['measurement_inc'])
                    moment = float(rec['measurement_magn_moment'])
                    # find the temperature of the atrm
                    if float(rec['treatment_dc_field']) != 0 and float(rec['treatment_temp']) != 273:
                        atrm_temperature = float(rec['treatment_temp'])
                    # find baseline
                    if float(rec['treatment_dc_field']) == 0 and float(rec['treatment_temp']) != 273:
                        baselines.append(
                            np.array(pmag.dir2cart([dec, inc, moment])))
                    # Find alteration check
                    # print rec['measurement_number']

                if len(baselines) != 0:
                    aniso_logfile.write(
                        "-I- found ATRM baseline for specimen %s\n" % specimen)

                else:
                    if len(zijdblock) != 0:
                        for rec in zijdblock:
                            zij_temp = rec[0]
                            # print rec
                            if zij_temp == atrm_temperature:
                                dec = float(rec[1])
                                inc = float(rec[2])
                                moment = float(rec[3])
                                baselines.append(
                                    np.array(pmag.dir2cart([dec, inc, moment])))
                                aniso_logfile.write(
                                    "-I- Found %i ATRM baselines for specimen %s in Zijderveld block. Averaging measurements\n" % (len(baselines), specimen))
                if len(baselines) == 0:
                    baseline = np.zeros(3, 'f')
                    aniso_logfile.write(
                        "-I- No aTRM baseline for specimen %s\n" % specimen)
                else:
                    baselines = np.array(baselines)
                    baseline = np.array([np.mean(baselines[:, 0]), np.mean(
                        baselines[:, 1]), np.mean(baselines[:, 2])])

                # sort measurements

                M = np.zeros([6, 3], 'f')

                for rec in atrmblock:

                    dec = float(rec['measurement_dec'])
                    inc = float(rec['measurement_inc'])
                    moment = float(rec['measurement_magn_moment'])
                    CART = np.array(pmag.dir2cart(
                        [dec, inc, moment])) - baseline

                    if float(rec['treatment_dc_field']) == 0:  # Ignore zero field steps
                        continue
                    # alteration check
                    if "LT-PTRM-I" in rec['magic_method_codes'].split(":"):
                        Alteration_check = CART
                        Alteration_check_dc_field_phi = float(
                            rec['treatment_dc_field_phi'])
                        Alteration_check_dc_field_theta = float(
                            rec['treatment_dc_field_theta'])
                        if Alteration_check_dc_field_phi == 0 and Alteration_check_dc_field_theta == 0:
                            Alteration_check_index = 0
                        if Alteration_check_dc_field_phi == 90 and Alteration_check_dc_field_theta == 0:
                            Alteration_check_index = 1
                        if Alteration_check_dc_field_phi == 0 and Alteration_check_dc_field_theta == 90:
                            Alteration_check_index = 2
                        if Alteration_check_dc_field_phi == 180 and Alteration_check_dc_field_theta == 0:
                            Alteration_check_index = 3
                        if Alteration_check_dc_field_phi == 270 and Alteration_check_dc_field_theta == 0:
                            Alteration_check_index = 4
                        if Alteration_check_dc_field_phi == 0 and Alteration_check_dc_field_theta == -90:
                            Alteration_check_index = 5
                        aniso_logfile.write(
                            "-I- found alteration check  for specimen %s\n" % specimen)
                        continue

                    treatment_dc_field_phi = float(
                        rec['treatment_dc_field_phi'])
                    treatment_dc_field_theta = float(
                        rec['treatment_dc_field_theta'])
                    treatment_dc_field = float(rec['treatment_dc_field'])

                    #+x, M[0]
                    if treatment_dc_field_phi == 0 and treatment_dc_field_theta == 0:
                        M[0] = CART
                    #+Y , M[1]
                    if treatment_dc_field_phi == 90 and treatment_dc_field_theta == 0:
                        M[1] = CART
                    #+Z , M[2]
                    if treatment_dc_field_phi == 0 and treatment_dc_field_theta == 90:
                        M[2] = CART
                    #-x, M[3]
                    if treatment_dc_field_phi == 180 and treatment_dc_field_theta == 0:
                        M[3] = CART
                    #-Y , M[4]
                    if treatment_dc_field_phi == 270 and treatment_dc_field_theta == 0:
                        M[4] = CART
                    #-Z , M[5]
                    if treatment_dc_field_phi == 0 and treatment_dc_field_theta == -90:
                        M[5] = CART

                # check if at least one measurement in missing
                for i in range(len(M)):
                    if M[i][0] == 0 and M[i][1] == 0 and M[i][2] == 0:
                        aniso_logfile.write(
                            "-E- ERROR: missing atrm data for specimen %s\n" % (specimen))
                        Reject_specimen = True

                # alteration check

                anisotropy_alt = 0
                if str(Alteration_check) != "":
                    for i in range(len(M)):
                        if Alteration_check_index == i:
                            M_1 = np.sqrt(sum((np.array(M[i])**2)))
                            M_2 = np.sqrt(sum(Alteration_check**2))
                            # print specimen
                            # print "M_1,M_2",M_1,M_2
                            diff = abs(M_1 - M_2)
                            # print "diff",diff
                            # print "np.mean([M_1,M_2])",np.mean([M_1,M_2])
                            diff_ratio = diff / np.mean([M_1, M_2])
                            diff_ratio_perc = 100 * diff_ratio
                            if diff_ratio_perc > anisotropy_alt:
                                anisotropy_alt = diff_ratio_perc
                else:
                    aniso_logfile.write(
                        "-W- Warning: no alteration check for specimen %s \n " % specimen)

                # Check for maximum difference in anti parallel directions.
                # if the difference between the two measurements is more than maximum_diff
                # The specimen is rejected

                # i.e. +x versus -x, +y versus -y, etc.s

                for i in range(3):
                    M_1 = np.sqrt(sum(np.array(M[i])**2))
                    M_2 = np.sqrt(sum(np.array(M[i + 3])**2))

                    diff = abs(M_1 - M_2)
                    diff_ratio = diff / np.mean([M_1, M_2])
                    diff_ratio_perc = 100 * diff_ratio

                    if diff_ratio_perc > anisotropy_alt:
                        anisotropy_alt = diff_ratio_perc

                if not Reject_specimen:

                    # K vector (18 elements, M1[x], M1[y], M1[z], ... etc.)
                    K = np.zeros(18, 'f')
                    K[0], K[1], K[2] = M[0][0], M[0][1], M[0][2]
                    K[3], K[4], K[5] = M[1][0], M[1][1], M[1][2]
                    K[6], K[7], K[8] = M[2][0], M[2][1], M[2][2]
                    K[9], K[10], K[11] = M[3][0], M[3][1], M[3][2]
                    K[12], K[13], K[14] = M[4][0], M[4][1], M[4][2]
                    K[15], K[16], K[17] = M[5][0], M[5][1], M[5][2]

                    if specimen not in list(Data_anisotropy.keys()):
                        Data_anisotropy[specimen] = {}
                    aniso_parameters = calculate_aniso_parameters(B, K)
                    Data_anisotropy[specimen]['ATRM'] = aniso_parameters
                    Data_anisotropy[specimen]['ATRM']['anisotropy_alt'] = "%.2f" % anisotropy_alt
                    Data_anisotropy[specimen]['ATRM']['anisotropy_type'] = "ATRM"
                    Data_anisotropy[specimen]['ATRM']['er_sample_name'] = atrmblock[0]['er_sample_name']
                    Data_anisotropy[specimen]['ATRM']['er_specimen_name'] = specimen
                    Data_anisotropy[specimen]['ATRM']['er_site_name'] = atrmblock[0]['er_site_name']
                    Data_anisotropy[specimen]['ATRM']['anisotropy_description'] = 'Hext statistics adapted to ATRM'
                   # Data_anisotropy[specimen]['ATRM']['magic_experiment_names']=specimen+";ATRM"
                   # # this is wrong!  should be from the measurement table
                    Data_anisotropy[specimen]['ATRM']['magic_experiment_names'] = experiment
                    Data_anisotropy[specimen]['ATRM']['magic_method_codes'] = "LP-AN-TRM:AE-H"
                    # Data_anisotropy[specimen]['ATRM']['rmag_anisotropy_name']=specimen

            if 'aarmblock' in list(self.Data[specimen].keys()):

                #-----------------------------------
                # AARM - 6, 9 or 15 positions
                #-----------------------------------

                aniso_logfile.write(
                    "-I- Start calculating AARM tensors for specimen %s\n" % specimen)
                experiment = self.Data[specimen]['aarmblock'][0]['magic_experiment_name']
                aarmblock = self.Data[specimen]['aarmblock']
                if len(aarmblock) < 12:
                    aniso_logfile.write(
                        "-W- WARNING: not enough aarm measurements for specimen %s\n" % specimen)
                    continue
                elif len(aarmblock) == 12:
                    n_pos = 6
                    B = Matrices[6]['B']
                    M = np.zeros([6, 3], 'f')
                elif len(aarmblock) == 18:
                    n_pos = 9
                    B = Matrices[9]['B']
                    M = np.zeros([9, 3], 'f')
                # 15 positions
                elif len(aarmblock) == 30:
                    n_pos = 15
                    B = Matrices[15]['B']
                    M = np.zeros([15, 3], 'f')
                else:
                    aniso_logfile.write(
                        "-E- ERROR: number of measurements in aarm block is incorrect for sample %s\n" % specimen)
                    continue

                Reject_specimen = False

                for i in range(n_pos):
                    for rec in aarmblock:
                        try:
                            float(rec['measurement_number'])
                        except ValueError:
                            print('-W- treat_step_num column must be provided to run "Calculate anisotropy tensors"')
                            return False, 'The treat_step_num column must be provided to run "Calculate anisotropy tensors"'
                        if float(rec['measurement_number']) == i * 2 + 1:
                            dec = float(rec['measurement_dec'])
                            inc = float(rec['measurement_inc'])
                            moment = float(rec['measurement_magn_moment'])
                            M_baseline = np.array(
                                pmag.dir2cart([dec, inc, moment]))

                        if float(rec['measurement_number']) == i * 2 + 2:
                            dec = float(rec['measurement_dec'])
                            inc = float(rec['measurement_inc'])
                            moment = float(rec['measurement_magn_moment'])
                            M_arm = np.array(pmag.dir2cart([dec, inc, moment]))
                    M[i] = M_arm - M_baseline

                K = np.zeros(3 * n_pos, 'f')
                for i in range(n_pos):
                    K[i * 3] = M[i][0]
                    K[i * 3 + 1] = M[i][1]
                    K[i * 3 + 2] = M[i][2]

                if specimen not in list(Data_anisotropy.keys()):
                    Data_anisotropy[specimen] = {}
                aniso_parameters = calculate_aniso_parameters(B, K)
                Data_anisotropy[specimen]['AARM'] = aniso_parameters
                Data_anisotropy[specimen]['AARM']['anisotropy_alt'] = ""
                Data_anisotropy[specimen]['AARM']['anisotropy_type'] = "AARM"
                Data_anisotropy[specimen]['AARM']['er_sample_name'] = aarmblock[0]['er_sample_name']
                Data_anisotropy[specimen]['AARM']['er_site_name'] = aarmblock[0]['er_site_name']
                Data_anisotropy[specimen]['AARM']['er_specimen_name'] = specimen
                Data_anisotropy[specimen]['AARM']['anisotropy_description'] = 'Hext statistics adapted to AARM'
                Data_anisotropy[specimen]['AARM']['magic_experiment_names'] = experiment
                Data_anisotropy[specimen]['AARM']['magic_method_codes'] = "LP-AN-ARM:AE-H"
                # Data_anisotropy[specimen]['AARM']['rmag_anisotropy_name']=specimen

        #-----------------------------------

        specimens = list(Data_anisotropy.keys())
        specimens.sort

        # remove previous anisotropy data, and replace with the new one:
        s_list = list(self.Data.keys())
        for sp in s_list:
            if 'AniSpec' in list(self.Data[sp].keys()):
                del self.Data[sp]['AniSpec']
        for specimen in specimens:
            # if both AARM and ATRM axist prefer the AARM !!
            if 'AARM' in list(Data_anisotropy[specimen].keys()):
                TYPES = ['AARM']
            if 'ATRM' in list(Data_anisotropy[specimen].keys()):
                TYPES = ['ATRM']
            if 'AARM' in list(Data_anisotropy[specimen].keys()) and 'ATRM' in list(Data_anisotropy[specimen].keys()):
                TYPES = ['ATRM', 'AARM']
                aniso_logfile.write(
                    "-W- WARNING: both aarm and atrm data exist for specimen %s. using AARM by default. If you prefer using one of them, delete the other!\n" % specimen)
            for TYPE in TYPES:
                Data_anisotropy[specimen][TYPE]['er_specimen_names'] = Data_anisotropy[specimen][TYPE]['er_specimen_name']
                Data_anisotropy[specimen][TYPE]['er_sample_names'] = Data_anisotropy[specimen][TYPE]['er_sample_name']
                Data_anisotropy[specimen][TYPE]['er_site_names'] = Data_anisotropy[specimen][TYPE]['er_site_name']
                if self.data_model == 3:  # prepare data for 3.0

                    new_aniso_parameters = Data_anisotropy[specimen][TYPE]
                    # reformat all the anisotropy related keys # START HERE
                    new_data = map_magic.convert_aniso(
                        'magic3', new_aniso_parameters)  # turn new_aniso data to 3.0
                    self.spec_data = self.spec_container.df

           # edit first of existing anisotropy data for this specimen of this
           # TYPE from self.spec_data
                    cond1 = self.spec_data['specimen'].str.contains(
                        specimen + "$") == True
                    meths = new_aniso_parameters['magic_method_codes']
                    for key in list(new_data.keys()):
                        if key not in self.spec_data.columns:
                            self.spec_data[key] = ""

                    # new_data['method_codes']=self.spec_data[self.spec_data['specimen'].str.contains(specimen+"$")==True].method_codes+':'+new_aniso_parameters['magic_method_codes']
                    cond3 = self.spec_data['aniso_s'].notnull() == True
                    cond2 = self.spec_data['aniso_type'] == TYPE
                    condition = (cond1 & cond2 & cond3)
                    # need to add in method codes for LP-AN...
                    old_meths = self.spec_data[condition]['method_codes'].values.tolist(
                    )
                    if len(old_meths) > 0:
                        try:
                            if ":" in old_meths[0]:  # breaks if old_meths is NoneType
                                if 'LP-AN' in old_meths[0]:
                                    methparts = old_meths[0].split(":")
                                    me = ""
                                    for m in methparts:
                                        if 'LP-AN' not in m and 'AE-H' not in m:
                                            me = me + m + ':'
                                    me = me.strip(":")
                                else:
                                    me = old_meths[0]
                                new_meths = me + ':' + meths
                        except:
                            new_meths = meths
                    else:
                        new_meths = meths
                    new_data['method_codes'] = new_meths
                    # try to get the sample name for the updated record
                    try:
                        samples = self.spec_container.df.loc[specimen, 'sample'].unique(
                        )
                        mask = pd.notnull(samples)
                        samples = samples[mask]
                        sample = samples[0]
                    except AttributeError as ex:
                        sample = self.spec_container.df.loc[specimen, 'sample']
                    except (IndexError, KeyError) as ex:
                        sample = ''
                    new_data['sample'] = sample
                    self.spec_data = self.spec_container.update_record(
                        specimen, new_data, condition)
                    for col in ['site', 'location']:  # remove unwanted columns
                        if col in list(self.spec_data.keys()):
                            del self.spec_data[col]
                    self.spec_data['software_packages'] = version

                else:  # write it to 2.5 version files
                    String = ""
                    for i in range(len(rmag_anisotropy_header)):
                        try:
                            String = String + \
                                Data_anisotropy[specimen][TYPE][rmag_anisotropy_header[i]] + '\t'
                        except:
                            String = String + \
                                "%f" % (
                                    Data_anisotropy[specimen][TYPE][rmag_anisotropy_header[i]]) + '\t'
                    rmag_anisotropy_file.write(String[:-1] + "\n")
                    String = ""
                    for i in range(len(rmag_results_header)):
                        try:
                            String = String + \
                                Data_anisotropy[specimen][TYPE][rmag_results_header[i]] + '\t'
                        except:
                            String = String + \
                                "%f" % (
                                    Data_anisotropy[specimen][TYPE][rmag_results_header[i]]) + '\t'
                    rmag_results_file.write(String[:-1] + "\n")
                if 'AniSpec' not in self.Data[specimen]:
                    self.Data[specimen]['AniSpec'] = {}
                self.Data[specimen]['AniSpec'][TYPE] = Data_anisotropy[specimen][TYPE]

        aniso_logfile.write("------------------------\n")
        aniso_logfile.write("-I- Done anisotropy script\n")
        aniso_logfile.write("------------------------\n")
        if self.data_model == 3:
            #  drop any stub rows (mostly empty rows)
            self.spec_container.drop_stub_rows()
            #  write out the data
            self.spec_container.write_magic_file(dir_path=self.WD)
        else:
            rmag_anisotropy_file.close()
        if self.data_model==2:
            rmag_results_file.close()
            rmag_anisotropy_file.close()
            aniso_logfile.close()
        return True, ""

    #==================================================

    def on_show_anisotropy_errors(self, event):
        fname = "rmag_anisotropy.log" if self.data_model == 2 else "anisotropy.log"
        try:
            dia = thellier_gui_dialogs.MyLogFileErrors(
                "Anisotropy calculation errors", os.path.join(self.WD, fname))
            dia.Show()
            dia.Center()
        except IOError:
            self.user_warning(
                "There is no {} in the current WD and therefore this function cannot work".format(fname))

#    #==================================================
#    # Thellier Auto Interpreter Tool
#    #==================================================

    def on_menu_run_interpreter(self, event):
        busy_frame = wx.BusyInfo(
            "Running Thellier auto interpreter\n It may take several minutes depending on the number of specimens ...", self)
        wx.SafeYield()
        thellier_auto_interpreter = thellier_interpreter.thellier_auto_interpreter(
            self.Data, self.Data_hierarchy, self.WD, self.acceptance_criteria, self.preferences, self.GUI_log, THERMAL, MICROWAVE)
        thellier_auto_interpreter.run_interpreter()
        self.Data = {}
        self.Data = copy.deepcopy(thellier_auto_interpreter.Data)
        self.Data_samples = copy.deepcopy(
            thellier_auto_interpreter.Data_samples)
        self.Data_sites = copy.deepcopy(thellier_auto_interpreter.Data_sites)
        dlg1 = wx.MessageDialog(
            self, caption="Message:", message="Interpreter finished successfully\nCheck output files in folder /thellier_interpreter in the current project directory", style=wx.OK | wx.ICON_INFORMATION)

        # display the interpretation of the current specimen:
        self.pars = self.Data[self.s]['pars']
        self.clear_boxes()
        # print "about to draw figure" # this is where trouble happens when 1
        # or 2 specimens are accepted
        self.draw_figure(self.s)
        # print "just drew figure"
        self.update_GUI_with_new_interpretation()
        del busy_frame
        self.show_dlg(dlg1)
        dlg1.Destroy()
        return()
        # self.Data=copy.deepcopy

    #----------------------------------------------------------------------

    def on_menu_open_interpreter_file(self, event):
        # print "self.WD",self.WD
        try:
            dirname = os.path.join(self.WD, "thellier_interpreter")
        except:
            dirname = self.WD
        print("dirname", dirname)
        dlg = wx.FileDialog(
            self, message="Choose an auto-interpreter output file",
            defaultDir=dirname,
            # defaultFile="",
            style=wx.FD_OPEN | wx.FD_CHANGE_DIR
        )

        # dlg = wx.FileDialog(self, "Choose an auto-interpreter output file",
        # defaultDir=dirname, "", "*.*", wx.FD_OPEN)
        if self.show_dlg(dlg) == wx.ID_OK:
            filename = dlg.GetFilename()
            path = dlg.GetPath()
        else:
            return
        # print  filename
        # print filename
        if "samples" in filename or "bounds" in filename or "site" in filename:
            ignore_n = 4

        elif "specimens" in filename or "all" in filename:
            ignore_n = 1
        else:
            return()
        self.frame = thellier_gui_dialogs.MyForm(ignore_n, path)
        self.frame.Show()

    #----------------------------------------------------------------------

    def on_menu_open_interpreter_log(self, event):
        dia = thellier_gui_dialogs.MyLogFileErrors("Interpreter errors and warnings", os.path.join(
            self.WD, "thellier_interpreter/", "thellier_interpreter.log"))
        dia.Show()
        dia.Center()

    #----------------------------------------------------------------------

    def read_redo_file(self, redo_file):
        """
        Read previous interpretation from a redo file
        and update gui with the new interpretation
        """
        self.GUI_log.write(
            "-I- reading redo file and processing new temperature bounds")
        self.redo_specimens = {}
        # first delete all previous interpretation
        for sp in list(self.Data.keys()):
            del self.Data[sp]['pars']
            self.Data[sp]['pars'] = {}
            self.Data[sp]['pars']['lab_dc_field'] = self.Data[sp]['lab_dc_field']
            self.Data[sp]['pars']['er_specimen_name'] = self.Data[sp]['er_specimen_name']
            self.Data[sp]['pars']['er_sample_name'] = self.Data[sp]['er_sample_name']
            # print sp
            # print self.Data[sp]['pars']
        self.Data_samples = {}
        self.Data_sites = {}

        fin = open(redo_file, 'r')
        lines = fin.readlines()
        fin.close()
        for Line in lines:
            line = Line.strip('\n').split()
            specimen = line[0]
            tmin_kelvin = float(line[1])
            tmax_kelvin = float(line[2])
            if specimen not in list(self.redo_specimens.keys()):
                self.redo_specimens[specimen] = {}
            self.redo_specimens[specimen]['t_min'] = float(tmin_kelvin)
            self.redo_specimens[specimen]['t_max'] = float(tmax_kelvin)
            if specimen in list(self.Data.keys()):
                if tmin_kelvin not in self.Data[specimen]['t_Arai'] or tmax_kelvin not in self.Data[specimen]['t_Arai']:
                    self.GUI_log.write(
                        "-W- WARNING: can't fit temperature bounds in the redo file to the actual measurement. specimen %s\n" % specimen)
                else:
                    self.Data[specimen]['pars'] = thellier_gui_lib.get_PI_parameters(
                        self.Data, self.acceptance_criteria, self.preferences, specimen, float(tmin_kelvin), float(tmax_kelvin), self.GUI_log, THERMAL, MICROWAVE)
                    try:
                        self.Data[specimen]['pars'] = thellier_gui_lib.get_PI_parameters(
                            self.Data, self.acceptance_criteria, self.preferences, specimen, float(tmin_kelvin), float(tmax_kelvin), self.GUI_log, THERMAL, MICROWAVE)
                        self.Data[specimen]['pars']['saved'] = True
                        # write intrepretation into sample data
                        sample = self.Data_hierarchy['specimens'][specimen]
                        if sample not in list(self.Data_samples.keys()):
                            self.Data_samples[sample] = {}
                        if specimen not in list(self.Data_samples[sample].keys()):
                            self.Data_samples[sample][specimen] = {}
                        self.Data_samples[sample][specimen]['B'] = self.Data[specimen]['pars']['specimen_int_uT']
                        site = thellier_gui_lib.get_site_from_hierarchy(
                            sample, self.Data_hierarchy)
                        if site not in list(self.Data_sites.keys()):
                            self.Data_sites[site] = {}
                        if specimen not in list(self.Data_sites[site].keys()):
                            self.Data_sites[site][specimen] = {}
                        self.Data_sites[site][specimen]['B'] = self.Data[specimen]['pars']['specimen_int_uT']

                    except:
                        print("-E- ERROR 1")
                        self.GUI_log.write(
                            "-E- ERROR. Can't calculate PI paremeters for specimen %s using redo file. Check!\n" % (specimen))
            else:
                self.GUI_log.write(
                    "-W- WARNING: Can't find specimen %s from redo file in measurement file!\n" % specimen)
                print(
                    "-W- WARNING: Can't find specimen %s from redo file in measurement file!\n" % specimen)
        if not fin.closed:
            fin.close()
        self.pars = self.Data[self.s]['pars']
        self.clear_boxes()
        self.draw_figure(self.s)
        self.update_GUI_with_new_interpretation()

    #----------------------------------------------------------------------

    def on_menu_run_consistency_test(self, event):

        self.GUI_log.write("-I- running thellier consistency test\n")
        # thellier_gui_dialogs.Consistency_Test(self.Data,self.Data_hierarchy,self.WD,self.acceptance_criteria_default)
        thellier_gui_dialogs.Consistency_Test(
            self.Data, self.Data_hierarchy, self.WD, self.acceptance_criteria, self.preferences, THERMAL, MICROWAVE)

    def on_menu_run_consistency_test_b(self, event):
        dlg1 = wx.MessageDialog(
            self, caption="Message:", message="Consistency test is no longer supported in this version", style=wx.OK)
        result = self.show_dlg(dlg1)
        if result == wx.ID_OK:
            dlg1.Destroy()
            return
    #----------------------------------------------------------------------

    def on_menu_plot_data(self, event):
        # Plot_Dialog(None,self.WD,self.Data,self.Data_info)

        dia = thellier_gui_dialogs.Plot_Dialog(
            None, self.WD, self.Data, self.Data_info)
        dia.Center()
        #result = self.show_dlg(dia)

        # if result == wx.ID_OK: # Until the user clicks OK, show the message
        #    self.On_close_criteria_box(dia)

        if self.show_dlg(dia) == wx.ID_OK:  # Until the user clicks OK, show the message
            self.On_close_plot_dialog(dia)

    #----------------------------------------------------------------------

    def on_menu_prepare_magic_results_tables(self, event):
        """
        Menubar --> File --> Save MagIC tables
        """
        # write a redo file
        try:
            self.on_menu_save_interpretation(None)
        except Exception as ex:
            print('-W-', ex)
            pass
        if self.data_model != 3:  # data model 3 data already read in to contribution
            #------------------
            # read existing pmag results data and sort out the directional data.
            # The directional data will be merged to one combined pmag table.
            # these data will be merged later
            #-----------------------.

            PmagRecsOld = {}
            for FILE in ['pmag_specimens.txt', 'pmag_samples.txt', 'pmag_sites.txt', 'pmag_results.txt']:
                PmagRecsOld[FILE], meas_data = [], []
                try:
                    meas_data, file_type = pmag.magic_read(
                        os.path.join(self.WD, FILE))
                    self.GUI_log.write(
                        "-I- Read existing magic file  %s\n" % (os.path.join(self.WD, FILE)))
                    # if FILE !='pmag_specimens.txt':
                    os.rename(os.path.join(self.WD, FILE),
                              os.path.join(self.WD, FILE + ".backup"))
                    self.GUI_log.write(
                        "-I- rename old magic file  %s.backup\n" % (os.path.join(self.WD, FILE)))
                except:
                    self.GUI_log.write(
                        "-I- Can't read existing magic file  %s\n" % (os.path.join(self.WD, FILE)))
                    continue
                for rec in meas_data:
                    if "magic_method_codes" in list(rec.keys()):
                        if "LP-PI" not in rec['magic_method_codes'] and "IE-" not in rec['magic_method_codes']:
                            PmagRecsOld[FILE].append(rec)

        pmag_specimens_header_1 = [
            "er_location_name", "er_site_name", "er_sample_name", "er_specimen_name"]
        pmag_specimens_header_2 = [
            'measurement_step_min', 'measurement_step_max', 'specimen_int']
        pmag_specimens_header_3 = ["specimen_correction", "specimen_int_corr_anisotropy",
                                   "specimen_int_corr_nlt", "specimen_int_corr_cooling_rate"]
        pmag_specimens_header_4 = []
        for short_stat in self.preferences['show_statistics_on_gui']:
            stat = "specimen_" + short_stat
            pmag_specimens_header_4.append(stat)
        pmag_specimens_header_5 = [
            "magic_experiment_names", "magic_method_codes", "measurement_step_unit", "specimen_lab_field_dc"]
        pmag_specimens_header_6 = ["er_citation_names"]

        specimens_list = []
        for specimen in list(self.Data.keys()):
            if 'pars' in list(self.Data[specimen].keys()):
                if 'saved' in self.Data[specimen]['pars'] and self.Data[specimen]['pars']['saved']:
                    specimens_list.append(specimen)
                elif 'deleted' in self.Data[specimen]['pars'] and self.Data[specimen]['pars']['deleted']:
                    specimens_list.append(specimen)

        # Empty pmag tables:
        MagIC_results_data = {}
        MagIC_results_data['pmag_specimens'] = {}
        MagIC_results_data['pmag_samples_or_sites'] = {}
        MagIC_results_data['pmag_results'] = {}

        # write down pmag_specimens.txt
        specimens_list.sort()
        for specimen in specimens_list:
            if 'pars' in self.Data[specimen] and 'deleted' in self.Data[specimen]['pars'] and self.Data[specimen]['pars']['deleted']:
                print('-I- Deleting interpretation for {}'.format(specimen))
                this_spec_data = self.spec_data.loc[specimen]
                # there are multiple rows for this specimen
                if isinstance(this_spec_data, pd.DataFrame):
                    # delete the intensity rows for specimen
                    cond1 = self.spec_container.df.specimen == specimen
                    cond2 = self.spec_container.df.int_abs.notnull()
                    cond = cond1 & cond2
                    self.spec_container.df = self.spec_container.df[-cond]
                # there is only one record for this specimen
                else:
                    # delete all intensity data for that specimen
                    columns = list(self.contribution.data_model.get_group_headers('specimens', 'Paleointensity'))
                    columns.extend(list(self.contribution.data_model.get_group_headers('specimens', 'Paleointensity pTRM Check Statistics')))
                    columns.extend(list(self.contribution.data_model.get_group_headers('specimens', 'Paleointensity pTRM Tail Check Statistics')))
                    columns.extend(list(self.contribution.data_model.get_group_headers('specimens', 'Paleointensity pTRM Additivity Check Statistics')))
                    columns.extend(list(self.contribution.data_model.get_group_headers('specimens', 'Paleointensity Arai Statistics')))
                    columns.extend(list(self.contribution.data_model.get_group_headers('specimens', 'Paleointensity Directional Statistics')))
                    int_columns = set(columns).intersection(self.spec_data.columns)
                    int_columns.update(['method_codes', 'result_quality', 'meas_step_max', 'meas_step_min', 'software_packages', 'meas_step_unit', 'experiments'])
                    new_data = {col: "" for col in int_columns}
                    cond1 = self.spec_container.df.specimen == specimen
                    for col in int_columns:
                        self.spec_container.df.loc[specimen, col] = ""

            elif 'pars' in self.Data[specimen] and 'saved' in self.Data[specimen]['pars'] and self.Data[specimen]['pars']['saved']:
                sample_name = self.Data_hierarchy['specimens'][specimen]
                site_name = thellier_gui_lib.get_site_from_hierarchy(
                    sample_name, self.Data_hierarchy)
                location_name = thellier_gui_lib.get_location_from_hierarchy(
                    site_name, self.Data_hierarchy)

                MagIC_results_data['pmag_specimens'][specimen] = {}
                if version != "unknown":
                    MagIC_results_data['pmag_specimens'][specimen]['magic_software_packages'] = version
                MagIC_results_data['pmag_specimens'][specimen]['er_citation_names'] = "This study"
                # MagIC_results_data['pmag_specimens'][specimen]['er_analyst_mail_names']="unknown"

                MagIC_results_data['pmag_specimens'][specimen]['er_specimen_name'] = specimen
                MagIC_results_data['pmag_specimens'][specimen]['er_sample_name'] = sample_name
                MagIC_results_data['pmag_specimens'][specimen]['er_site_name'] = site_name
                MagIC_results_data['pmag_specimens'][specimen]['er_location_name'] = location_name
                MagIC_results_data['pmag_specimens'][specimen]['magic_method_codes'] = self.Data[
                    specimen]['pars']['magic_method_codes'] + ":IE-TT"
                tmp = MagIC_results_data['pmag_specimens'][specimen]['magic_method_codes'].split(
                    ":")
                # magic_experiment_names=specimen
                magic_experiment_names = ""
                # for m in tmp: # this is incorrect - it should be a concatenated list of the experiment names from the measurement table.
                #    if "LP-" in m:
                #        magic_experiment_names=magic_experiment_names+":" + m
                MagIC_results_data['pmag_specimens'][specimen]['magic_experiment_names'] = magic_experiment_names
                MagIC_results_data['pmag_specimens'][specimen]['measurement_step_unit'] = 'K'
                MagIC_results_data['pmag_specimens'][specimen]['specimen_lab_field_dc'] = "%.2e" % (
                    self.Data[specimen]['pars']['lab_dc_field'])
                MagIC_results_data['pmag_specimens'][specimen]['specimen_correction'] = self.Data[specimen]['pars']['specimen_correction']
                for key in pmag_specimens_header_4:
                    if key in ['specimen_int_ptrm_n', 'specimen_int_n']:
                        MagIC_results_data['pmag_specimens'][specimen][key] = "%i" % (
                            self.Data[specimen]['pars'][key])
                    elif key in ['specimen_scat'] and self.Data[specimen]['pars'][key] == "Fail":
                        MagIC_results_data['pmag_specimens'][specimen][key] = "0"
                    elif key in ['specimen_scat'] and self.Data[specimen]['pars'][key] == "Pass":
                        MagIC_results_data['pmag_specimens'][specimen][key] = "1"
                    else:
                        MagIC_results_data['pmag_specimens'][specimen][key] = "%.2f" % (
                            self.Data[specimen]['pars'][key])

                MagIC_results_data['pmag_specimens'][specimen]['specimen_int'] = "%.2e" % (
                    self.Data[specimen]['pars']['specimen_int'])
                MagIC_results_data['pmag_specimens'][specimen]['measurement_step_min'] = "%i" % (
                    self.Data[specimen]['pars']['measurement_step_min'])
                MagIC_results_data['pmag_specimens'][specimen]['measurement_step_max'] = "%i" % (
                    self.Data[specimen]['pars']['measurement_step_max'])
                if "specimen_int_corr_anisotropy" in list(self.Data[specimen]['pars'].keys()):
                    MagIC_results_data['pmag_specimens'][specimen]['specimen_int_corr_anisotropy'] = "%.2f" % (
                        self.Data[specimen]['pars']['specimen_int_corr_anisotropy'])
                else:
                    MagIC_results_data['pmag_specimens'][specimen]['specimen_int_corr_anisotropy'] = ""
                if "specimen_int_corr_nlt" in list(self.Data[specimen]['pars'].keys()):
                    MagIC_results_data['pmag_specimens'][specimen]['specimen_int_corr_nlt'] = "%.2f" % (
                        self.Data[specimen]['pars']['specimen_int_corr_nlt'])
                else:
                    MagIC_results_data['pmag_specimens'][specimen]['specimen_int_corr_nlt'] = ""
                if "specimen_int_corr_cooling_rate" in list(self.Data[specimen]['pars'].keys()) and self.Data[specimen]['pars']['specimen_int_corr_cooling_rate'] != -999:
                    MagIC_results_data['pmag_specimens'][specimen]['specimen_int_corr_cooling_rate'] = "%.2f" % (
                        self.Data[specimen]['pars']['specimen_int_corr_cooling_rate'])
                else:
                    MagIC_results_data['pmag_specimens'][specimen]['specimen_int_corr_cooling_rate'] = ""
                MagIC_results_data['pmag_specimens'][specimen]['criteria'] = "IE-SPEC"

                if self.data_model == 3:   # convert pmag_specimen format to data model 3 and replace existing specimen record or add new & delete blank records
                    new_spec_data = MagIC_results_data['pmag_specimens'][specimen]
                    # turn new_specimen data to 3.0
                    new_data = map_magic.convert_spec('magic3', new_spec_data)
                    # check if interpretation passes criteria and set flag
                    spec_pars = thellier_gui_lib.check_specimen_PI_criteria(
                        self.Data[specimen]['pars'], self.acceptance_criteria)
                    if len(spec_pars['specimen_fail_criteria']) > 0:
                        new_data['result_quality'] = 'b'
                    else:
                        new_data['result_quality'] = 'g'
                    # reformat all the keys
                    cond1 = self.spec_container.df['specimen'].str.contains(
                        specimen + "$") == True
                    if 'int_abs' not in self.spec_container.df.columns:
                        self.spec_container.df['int_abs'] = None
                        print("-W- No intensity data found for specimens")
                    cond2 = self.spec_container.df['int_abs'].apply(lambda x: cb.not_null(x, False)) #notnull() == True
                    condition = (cond1 & cond2)
                    # update intensity records
                    self.spec_data = self.spec_container.update_record(
                        specimen, new_data, condition)
                    ## delete essentially blank records
                    #condition = self.spec_data['method_codes'].isnull().astype(
                    #bool)  # find the blank records
                    #info_str = "specimen rows with blank method codes"
                    #self.spec_data = self.spec_container.delete_rows(
                    #    condition, info_str)  # delete them

        if self.data_model != 3:  # write out pmag_specimens.txt file
            fout = open(os.path.join(self.WD, "pmag_specimens.txt"), 'w')
            fout.write("tab\tpmag_specimens\n")
            headers = pmag_specimens_header_1 + pmag_specimens_header_2 + pmag_specimens_header_3 + \
                pmag_specimens_header_4 + pmag_specimens_header_5 + pmag_specimens_header_6
            String = ""
            for key in headers:
                String = String + key + "\t"
            fout.write(String[:-1] + "\n")
            for specimen in specimens_list:
                String = ""
                for key in headers:
                    String = String + \
                        MagIC_results_data['pmag_specimens'][specimen][key] + "\t"
                fout.write(String[:-1] + "\n")
            fout.close()
            # merge with non-intensity data
            # read the new pmag_specimens.txt
            meas_data, file_type = pmag.magic_read(
                os.path.join(self.WD, "pmag_specimens.txt"))
            # add the old non-PI lines from pmag_specimens.txt
            for rec in PmagRecsOld["pmag_specimens.txt"]:
                meas_data.append(rec)
            # fix headers, so all headers in all lines
            meas_data = self.converge_pmag_rec_headers(meas_data)
            # write the combined pmag_specimens.txt
            pmag.magic_write(os.path.join(
                self.WD, "pmag_specimens.txt"), meas_data, 'pmag_specimens')
            try:
                os.remove(os.path.join(self.WD, "pmag_specimens.txt.backup"))
            except:
                pass

            #-------------
            # message dialog
            #-------------
            TEXT = "specimens interpretations are saved in pmag_specimens.txt.\nPress OK for pmag_samples/pmag_sites/pmag_results tables."
        else:  # data model 3, so merge with spec_data  and save as specimens.txt file
            # remove unwanted columns (site, location).
            for col in ['site', 'location']:
                if col in self.spec_data.columns:
                    del self.spec_data[col]

            self.spec_container.drop_duplicate_rows()
            #  write out the data
            self.spec_container.write_magic_file(dir_path=self.WD)
            TEXT = "specimens interpretations are saved in specimens.txt.\nPress OK for samples/sites tables."

        dlg = wx.MessageDialog(self, caption="Saved",
                               message=TEXT, style=wx.OK | wx.CANCEL)
        result = self.show_dlg(dlg)
        if result == wx.ID_OK:
            dlg.Destroy()
        if result == wx.ID_CANCEL:
            dlg.Destroy()
            return()
        #-------------
        # pmag_samples.txt or pmag_sites.txt
        #-------------
        if self.acceptance_criteria['average_by_sample_or_site']['value'] == 'sample':
            BY_SITES = False
            BY_SAMPLES = True
        else:
            BY_SITES = True
            BY_SAMPLES = False

        pmag_samples_header_1 = ["er_location_name", "er_site_name"]
        if BY_SAMPLES:
            pmag_samples_header_1.append("er_sample_name")
        if BY_SAMPLES:
            pmag_samples_header_2 = ["er_specimen_names", "sample_int", "sample_int_n",
                                     "sample_int_sigma", "sample_int_sigma_perc", "sample_description"]
        else:
            pmag_samples_header_2 = ["er_specimen_names", "site_int", "site_int_n",
                                     "site_int_sigma", "site_int_sigma_perc", "site_description"]
        pmag_samples_header_3 = [
            "magic_method_codes", "magic_software_packages"]
        pmag_samples_header_4 = ["er_citation_names"]

        pmag_samples_or_sites_list = []

        if BY_SAMPLES:
            samples_or_sites = list(self.Data_samples.keys())
            Data_samples_or_sites = copy.deepcopy(self.Data_samples)
        else:
            samples_or_sites = list(self.Data_sites.keys())
            Data_samples_or_sites = copy.deepcopy(self.Data_sites)
        samples_or_sites.sort()
        for sample_or_site in samples_or_sites:
            if True:
                specimens_names = ""
                B = []
                specimens_LP_codes = []
                for specimen in list(Data_samples_or_sites[sample_or_site].keys()):
                    B.append(Data_samples_or_sites[sample_or_site][specimen])
                    if specimen not in MagIC_results_data['pmag_specimens']:
                        continue
                    magic_codes = MagIC_results_data['pmag_specimens'][specimen]['magic_method_codes']
                    codes = magic_codes.replace(" ", "").split(":")
                    for code in codes:
                        if "LP-" in code and code not in specimens_LP_codes:
                            specimens_LP_codes.append(code)

                    specimens_names = specimens_names + specimen + ":"
                magic_codes = ":".join(specimens_LP_codes) + ":IE-TT"
                specimens_names = specimens_names[:-1]
                if specimens_names != "":

                    # sample_pass_criteria=False
                    sample_or_site_pars = self.calculate_sample_mean(
                        Data_samples_or_sites[sample_or_site])
                    if sample_or_site_pars['pass_or_fail'] == 'fail':
                        continue
                    N = sample_or_site_pars['N']
                    B_uT = sample_or_site_pars['B_uT']
                    B_std_uT = sample_or_site_pars['B_std_uT']
                    B_std_perc = sample_or_site_pars['B_std_perc']
                    pmag_samples_or_sites_list.append(sample_or_site)
                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site] = {
                    }
                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site]['er_specimen_names'] = specimens_names
                    if BY_SAMPLES:
                        name = "sample_"
                    else:
                        name = "site_"
                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site][name +
                                                                                'int'] = "%.2e" % (B_uT * 1e-6)
                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site][name +
                                                                                'int_n'] = "%i" % (N)
                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site][name +
                                                                                'int_sigma'] = "%.2e" % (B_std_uT * 1e-6)
                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site][name +
                                                                                'int_sigma_perc'] = "%.2f" % (B_std_perc)
                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site][name +
                                                                                'description'] = "paleointensity mean"
                    if BY_SAMPLES:
                        sample_name = sample_or_site
                        site_name = thellier_gui_lib.get_site_from_hierarchy(
                            sample_name, self.Data_hierarchy)
                        location_name = thellier_gui_lib.get_location_from_hierarchy(
                            site_name, self.Data_hierarchy)
                        MagIC_results_data['pmag_samples_or_sites'][sample_or_site]['er_sample_name'] = sample_name

                    if BY_SITES:
                        site_name = sample_or_site
                        location_name = thellier_gui_lib.get_location_from_hierarchy(
                            site_name, self.Data_hierarchy)

                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site]['er_site_name'] = site_name
                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site]['er_location_name'] = location_name
                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site]["pmag_criteria_codes"] = ""
                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site]['magic_method_codes'] = magic_codes
                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site]["magic_software_packages"] = version

                    MagIC_results_data['pmag_samples_or_sites'][sample_or_site]["er_citation_names"] = "This study"

        # prepare pmag_samples.txt
        pmag_samples_or_sites_list.sort()
        if self.data_model != 3:  # save 2.5 way
            if BY_SAMPLES:
                fout = open(os.path.join(self.WD, "pmag_samples.txt"), 'w')
                fout.write("tab\tpmag_samples\n")
            else:
                fout = open(os.path.join(self.WD, "pmag_sites.txt"), 'w')
                fout.write("tab\tpmag_sites\n")

            headers = pmag_samples_header_1 + pmag_samples_header_2 + \
                pmag_samples_header_3 + pmag_samples_header_4
            String = ""
            for key in headers:
                String = String + key + "\t"
            fout.write(String[:-1] + "\n")

            for sample_or_site in pmag_samples_or_sites_list:
                String = ""
                for key in headers:
                    String = String + \
                        MagIC_results_data['pmag_samples_or_sites'][sample_or_site][key] + "\t"
                fout.write(String[:-1] + "\n")
            fout.close()

        # merge with non-intensity data
            if BY_SAMPLES:
                meas_data, file_type = pmag.magic_read(
                    os.path.join(self.WD, "pmag_samples.txt"))
                for rec in PmagRecsOld["pmag_samples.txt"]:
                    meas_data.append(rec)
                meas_data = self.converge_pmag_rec_headers(meas_data)
                pmag.magic_write(os.path.join(
                    self.WD, "pmag_samples.txt"), meas_data, 'pmag_samples')
                try:
                    os.remove(os.path.join(self.WD, "pmag_samples.txt.backup"))
                except:
                    pass
                pmag.magic_write(os.path.join(
                    self.WD, "pmag_sites.txt"), PmagRecsOld["pmag_sites.txt"], 'pmag_sites')
                try:
                    os.remove(os.path.join(self.WD, "pmag_sites.txt.backup"))
                except:
                    pass

            else:
                meas_data, file_type = pmag.magic_read(
                    os.path.join(self.WD, "pmag_sites.txt"))
                for rec in PmagRecsOld["pmag_sites.txt"]:
                    meas_data.append(rec)
                meas_data = self.converge_pmag_rec_headers(meas_data)
                pmag.magic_write(os.path.join(
                    self.WD, "pmag_sites.txt"), meas_data, 'pmag_sites')
                try:
                    os.remove(os.path.join(self.WD, "pmag_sites.txt.backup"))
                except:
                    pass
                pmag.magic_write(os.path.join(
                    self.WD, "pmag_samples.txt"), PmagRecsOld["pmag_samples.txt"], 'pmag_samples')
                try:
                    os.remove(os.path.join(self.WD, "pmag_samples.txt.backup"))
                except:
                    pass

        else:  # don't do anything yet = need vdm data
            pass

        #-------------
        # pmag_results.txt
        #-------------

        pmag_results_header_1 = ["er_location_names", "er_site_names"]
        if BY_SAMPLES:
            pmag_results_header_1.append("er_sample_names")
        pmag_results_header_1.append("er_specimen_names")

        pmag_results_header_2 = ["average_lat", "average_lon", ]
        pmag_results_header_3 = [
            "average_int_n", "average_int", "average_int_sigma", "average_int_sigma_perc"]
        if self.preferences['VDM_or_VADM'] == "VDM":
            pmag_results_header_4 = ["vdm", "vdm_sigma"]
        else:
            pmag_results_header_4 = ["vadm", "vadm_sigma"]
        pmag_results_header_5 = ["data_type", "pmag_result_name", "magic_method_codes",
                                 "result_description", "er_citation_names", "magic_software_packages", "pmag_criteria_codes"]

        for sample_or_site in pmag_samples_or_sites_list:
            if sample_or_site is None:
                continue
            if isinstance(sample_or_site, type(np.nan)):
                continue
            MagIC_results_data['pmag_results'][sample_or_site] = {}
            if self.data_model == 3:
                if BY_SAMPLES:
                    if len(self.test_for_criteria()):
                        MagIC_results_data['pmag_results'][sample_or_site]['pmag_criteria_codes'] = "IE-SPEC:IE-SAMP"
                if BY_SITES:
                    if len(self.test_for_criteria()):
                        MagIC_results_data['pmag_results'][sample_or_site]['pmag_criteria_codes'] = "IE-SPEC:IE-SITE"
            else:
                MagIC_results_data['pmag_results'][sample_or_site]['pmag_criteria_codes'] = "ACCEPT"
            MagIC_results_data['pmag_results'][sample_or_site]["er_location_names"] = MagIC_results_data[
                'pmag_samples_or_sites'][sample_or_site]['er_location_name']
            MagIC_results_data['pmag_results'][sample_or_site]["er_site_names"] = MagIC_results_data[
                'pmag_samples_or_sites'][sample_or_site]['er_site_name']
            MagIC_results_data['pmag_results'][sample_or_site]["er_specimen_names"] = MagIC_results_data[
                'pmag_samples_or_sites'][sample_or_site]['er_specimen_names']

            if BY_SAMPLES:
                MagIC_results_data['pmag_results'][sample_or_site]["er_sample_names"] = MagIC_results_data[
                    'pmag_samples_or_sites'][sample_or_site]['er_sample_name']

            site = MagIC_results_data['pmag_results'][sample_or_site]["er_site_names"]
            lat, lon = "", ""
            if site in list(self.Data_info["er_sites"].keys()) and "site_lat" in list(self.Data_info["er_sites"][site].keys()):
                # MagIC_results_data['pmag_results'][sample_or_site]["average_lat"]=self.Data_info["er_sites"][site]["site_lat"]
                lat = self.Data_info["er_sites"][site]["site_lat"]

            if site in list(self.Data_info["er_sites"].keys()) and "site_lon" in list(self.Data_info["er_sites"][site].keys()):
                # MagIC_results_data['pmag_results'][sample_or_site]["average_lon"]=self.Data_info["er_sites"][site]["site_lon"]
                lon = self.Data_info["er_sites"][site]["site_lon"]
            MagIC_results_data['pmag_results'][sample_or_site]["average_lat"] = lat
            MagIC_results_data['pmag_results'][sample_or_site]["average_lon"] = lon
            if BY_SAMPLES:
                name = 'sample'
            else:
                name = 'site'

            MagIC_results_data['pmag_results'][sample_or_site]["average_int_n"] = MagIC_results_data[
                'pmag_samples_or_sites'][sample_or_site][name + '_int_n']
            MagIC_results_data['pmag_results'][sample_or_site]["average_int"] = MagIC_results_data[
                'pmag_samples_or_sites'][sample_or_site][name + '_int']
            MagIC_results_data['pmag_results'][sample_or_site]["average_int_sigma"] = MagIC_results_data[
                'pmag_samples_or_sites'][sample_or_site][name + '_int_sigma']
            MagIC_results_data['pmag_results'][sample_or_site]["average_int_sigma_perc"] = MagIC_results_data[
                'pmag_samples_or_sites'][sample_or_site][name + '_int_sigma_perc']

            if self.preferences['VDM_or_VADM'] == "VDM":
                pass
                # to be done
            else:
                if lat != "":
                    lat = float(lat)
                    # B=float(MagIC_results_data['pmag_samples_or_sites'][sample_or_site]['sample_int'])
                    B = float(
                        MagIC_results_data['pmag_results'][sample_or_site]["average_int"])
                    # B_sigma=float(MagIC_results_data['pmag_samples_or_sites'][sample_or_site]['sample_int_sigma'])
                    B_sigma = float(
                        MagIC_results_data['pmag_results'][sample_or_site]["average_int_sigma"])
                    VADM = pmag.b_vdm(B, lat)
                    VADM_plus = pmag.b_vdm(B + B_sigma, lat)
                    VADM_minus = pmag.b_vdm(B - B_sigma, lat)
                    VADM_sigma = (VADM_plus - VADM_minus) / 2
                    MagIC_results_data['pmag_results'][sample_or_site]["vadm"] = "%.2e" % VADM
                    MagIC_results_data['pmag_results'][sample_or_site]["vadm_sigma"] = "%.2e" % VADM_sigma
                    if self.data_model == 3:  # stick vadm into site_or_sample record
                        MagIC_results_data['pmag_samples_or_sites'][sample_or_site]["vadm"] = "%.2e" % VADM
                        MagIC_results_data['pmag_samples_or_sites'][sample_or_site]["vadm_sigma"] = "%.2e" % VADM_sigma
                else:
                    MagIC_results_data['pmag_results'][sample_or_site]["vadm"] = ""
                    MagIC_results_data['pmag_results'][sample_or_site]["vadm_sigma"] = ""
                    if self.data_model == 3:  # stick vadm into site_or_sample record
                        MagIC_results_data['pmag_samples_or_sites'][sample_or_site]["vadm"] = ""
                        MagIC_results_data['pmag_samples_or_sites'][sample_or_site]["vadm_sigma"] = ""
            if MagIC_results_data['pmag_results'][sample_or_site]["vadm"] != "":
                MagIC_results_data['pmag_results'][sample_or_site]["pmag_result_name"] = "Paleointensity;V[A]DM;" + sample_or_site
                MagIC_results_data['pmag_results'][sample_or_site]["result_description"] = "Paleointensity; V[A]DM"
            else:
                MagIC_results_data['pmag_results'][sample_or_site]["pmag_result_name"] = "Paleointensity;" + sample_or_site
                MagIC_results_data['pmag_results'][sample_or_site]["result_description"] = "Paleointensity"

            MagIC_results_data['pmag_results'][sample_or_site]["magic_software_packages"] = version
            MagIC_results_data['pmag_results'][sample_or_site]["magic_method_codes"] = magic_codes
            # try to make a more meaningful name

            MagIC_results_data['pmag_results'][sample_or_site]["data_type"] = "i"
            MagIC_results_data['pmag_results'][sample_or_site]["er_citation_names"] = "This study"
            if self.data_model != 3:  # look for ages in er_ages - otherwise they are in sites.txt already
                # add ages
                found_age = False
                site = MagIC_results_data['pmag_results'][sample_or_site]["er_site_names"]
                if sample_or_site in list(self.Data_info["er_ages"].keys()):
                    sample_or_site_with_age = sample_or_site
                    found_age = True
                elif site in list(self.Data_info["er_ages"].keys()):
                    sample_or_site_with_age = site
                    found_age = True
                if found_age:
                    for header in ["age", "age_unit", "age_sigma", "age_range_low", "age_range_high"]:
                        if sample_or_site_with_age in list(self.Data_info["er_ages"].keys()) and header in list(self.Data_info["er_ages"][sample_or_site_with_age].keys()):
                            if self.Data_info["er_ages"][sample_or_site_with_age][header] != "":
                                value = self.Data_info["er_ages"][sample_or_site_with_age][header]
                                header_result = "average_" + header
                                if header_result == "average_age_range_high":
                                    header_result = "average_age_high"
                                if header_result == "average_age_range_low":
                                    header_result = "average_age_low"
                                MagIC_results_data['pmag_results'][sample_or_site][header_result] = value

                                if header_result not in pmag_results_header_4:
                                    pmag_results_header_4.append(header_result)

            else:

                found_age = False
                if BY_SAMPLES and sample_or_site in list(self.Data_info["er_ages"].keys()):
                    element_with_age = sample_or_site
                    found_age = True
                elif BY_SAMPLES and sample_or_site not in list(self.Data_info["er_ages"].keys()):
                    site = self.Data_hierarchy['site_of_sample'][sample_or_site]
                    if site in list(self.Data_info["er_ages"].keys()):
                        element_with_age = site
                        found_age = True
                elif BY_SITES and sample_or_site in list(self.Data_info["er_ages"].keys()):
                    element_with_age = sample_or_site
                    found_age = True
                else:
                    continue
                if not found_age:
                    continue
                foundkeys = False
            # print    "element_with_age",element_with_age
                for key in ['age', 'age_sigma', 'age_range_low', 'age_range_high', 'age_unit']:
                    # print "Ron debug"
                    # print element_with_age
                    # print sample_or_site
                    if "er_ages" in list(self.Data_info.keys()) and element_with_age in list(self.Data_info["er_ages"].keys()):
                        if key in list(self.Data_info["er_ages"][element_with_age].keys()):
                            if self.Data_info["er_ages"][element_with_age][key] != "":
                                # print self.Data_info["er_ages"][element_with_age]
                                # print  self.Data_info["er_ages"][element_with_age][key]
                                # print
                                # MagIC_results_data['pmag_results'][sample_or_site]
                                MagIC_results_data['pmag_results'][sample_or_site][
                                    key] = self.Data_info["er_ages"][element_with_age][key]
                                foundkeys = True
                if foundkeys == True:
                    if "er_ages" in list(self.Data_info.keys()) and element_with_age in list(self.Data_info["er_ages"].keys()):
                        if 'magic_method_codes' in list(self.Data_info["er_ages"][element_with_age].keys()):
                            methods = self.Data_info["er_ages"][element_with_age]['magic_method_codes'].replace(
                                " ", "").strip('\n').split(":")
                            for meth in methods:
                                MagIC_results_data['pmag_results'][sample_or_site]["magic_method_codes"] = MagIC_results_data[
                                    'pmag_results'][sample_or_site]["magic_method_codes"] + ":" + meth

        if self.data_model != 3:
            # write pmag_results.txt
            fout = open(os.path.join(self.WD, "pmag_results.txt"), 'w')
            fout.write("tab\tpmag_results\n")
            headers = pmag_results_header_1 + pmag_results_header_2 + \
                pmag_results_header_3 + pmag_results_header_4 + pmag_results_header_5
            String = ""
            for key in headers:
                String = String + key + "\t"
            fout.write(String[:-1] + "\n")

            # pmag_samples_list.sort()
            for sample_or_site in pmag_samples_or_sites_list:
                if sample_or_site is None:
                    continue
                if isinstance(sample_or_site, type(np.nan)):
                    continue
                String = ""
                for key in headers:
                    if key in list(MagIC_results_data['pmag_results'][sample_or_site].keys()):
                        String = String + \
                            MagIC_results_data['pmag_results'][sample_or_site][key] + "\t"
                    else:
                        String = String + "" + "\t"
                fout.write(String[:-1] + "\n")
            fout.close()

            # merge with non-intensity data
            meas_data, file_type = pmag.magic_read(
                os.path.join(self.WD, "pmag_results.txt"))
            for rec in PmagRecsOld["pmag_results.txt"]:
                meas_data.append(rec)
            meas_data = self.converge_pmag_rec_headers(meas_data)
            pmag.magic_write(os.path.join(
                self.WD, "pmag_results.txt"), meas_data, 'pmag_results')
            try:
                os.remove(os.path.join(self.WD, "pmag_results.txt.backup"))
            except:
                pass

        else:  # write out samples/sites in data model 3.0
            for sample_or_site in pmag_samples_or_sites_list:
                if sample_or_site is None:
                    continue
                if isinstance(sample_or_site, type(np.nan)):
                    continue

                # convert, delete, add and save
                new_sample_or_site_data = MagIC_results_data['pmag_samples_or_sites'][sample_or_site]

                if BY_SAMPLES:
                    new_data = map_magic.convert_samp(
                        'magic3', new_sample_or_site_data)  # convert to 3.0
                    if len(self.test_for_criteria()):
                        new_data['criteria'] = 'IE-SPEC:IE-SAMP'
                    new_data['result_quality'] = 'g'
                    self.samp_data = self.samp_container.df
                    cond1 = self.samp_data['sample'].str.contains(
                        sample_or_site + "$") == True
                    if 'int_abs' not in self.samp_data.columns:
                        self.samp_data['int_abs'] = None
                        print('-W- No intensity data found for samples')
                    cond2 = self.samp_data['int_abs'].notnull() == True
                    condition = (cond1 & cond2)
                    # update record
                    self.samp_data = self.samp_container.update_record(
                        sample_or_site, new_data, condition)
                    self.site_data = self.site_container.df
                    # remove intensity data from site level.
                    if 'int_abs' not in self.site_data.columns:
                        self.site_data['int_abs'] = None
                        print('-W- No intensity data found for sites')
                    site = self.Data_hierarchy['site_of_sample'][sample_or_site]
                    try:  # if site name is blank will skip
                        cond1 = self.site_data['site'].str.contains(
                            site + "$") == True
                        cond2 = self.site_data['int_abs'].notnull() == True
                        condition = (cond1 & cond2)
                        site_keys = ['samples', 'int_abs', 'int_sigma', 'int_n_samples', 'int_sigma_perc', 'specimens',
                                     'int_abs_sigma', 'int_abs_sigma_perc', 'vadm']  # zero these out but keep the rest
                        blank_data = {}
                        for key in site_keys:
                            blank_data[key] = ""
                        self.site_data = self.site_container.update_record(
                            site, blank_data, condition, update_only=True)
                    # add record for sample in the site table
                        cond1 = self.site_data['site'].str.contains(
                            sample_or_site + "$") == True
                        cond2 = self.site_data['int_abs'].notnull() == True
                        condition = (cond1 & cond2)
                    # change 'site' column to reflect sample name,
                    # since we are putting this sample at the site level
                        new_data['site'] = sample_or_site
                        new_data['samples'] = sample_or_site
                        new_data['int_n_samples'] = '1'
                        # get rid of this key for site table
                        del new_data['sample']
                        new_data['vadm'] = MagIC_results_data['pmag_results'][sample_or_site]["vadm"]
                        new_data['vadm_sigma'] = MagIC_results_data['pmag_results'][sample_or_site]["vadm_sigma"]
                        new_data['result_quality'] = 'g'
                        self.site_data = self.site_container.update_record(
                            sample_or_site, new_data, condition, debug=True)
                    except:
                        pass  # no site
                else:  # do this by site and not by sample START HERE
                    cond1 = self.site_data['site'].str.contains(
                        sample_or_site + "$") == True
                    if 'int_abs' not in self.site_data.columns:
                        self.site_data['int_abs'] = None
                    cond2 = self.site_data['int_abs'].notnull() == True
                    condition = (cond1 & cond2)
                    loc = None
                    locs = self.site_data[cond1]['location']
                    if any(locs):
                        loc = locs.values[0]
                    new_data['site'] = sample_or_site
                    new_data['location'] = loc
                    self.site_data = self.site_container.update_record(
                        sample_or_site, new_data, condition)
                    # remove intensity data from sample level.   # need to look
                    # up samples from this site
                    cond1 = self.samp_data['site'].str.contains(
                        sample_or_site + "$") == True
                    if 'int_abs' not in self.samp_data.columns:
                        self.samp_data['int_abs'] = None
                    cond2 = self.samp_data['int_abs'].notnull() == True
                    condition = (cond1 & cond2)
                    new_data = {}  # zero these out but keep the rest
                    # zero these out but keep the rest
                    samp_keys = ['int_abs', 'int_sigma',
                                 'int_n_specimens', 'int_sigma_perc']
                    for key in samp_keys:
                        new_data[key] = ""
                    samples = self.samp_data[condition].index.unique()
                    for samp_name in samples:
                        self.samp_container.update_record(
                            samp_name, new_data, cond2)
            for col in ['location']:
                if col in list(self.samp_data.keys()):
                    del self.samp_data[col]
            # if BY_SAMPLES: # replace 'site' with 'sample'
            #    self.samp_data['site']=self.samp_data['sample']
            #    condition= self.samp_container.df['specimens'].notnull()==True  # find all the blank specimens rows
            #    self.samp_container.df = self.samp_container.df.loc[condition]



            # remove sample only columns that have been put into sites
            if BY_SAMPLES:
                #ignore = ['cooling_rate_corr', 'cooling_rate_mcd']
                self.site_container.remove_non_magic_cols_from_table(ignore_cols=[]) #ignore)
            #  write out the data
            self.samp_container.write_magic_file(dir_path=self.WD)
            self.site_container.write_magic_file(dir_path=self.WD)

        #-------------
        # MagIC_methods.txt
        #-------------

        # search for all magic_methods in all files:
        magic_method_codes = []
        for F in ["magic_measurements.txt", "rmag_anisotropy.txt", "rmag_results.txt", "rmag_results.txt", "pmag_samples.txt", "pmag_specimens.txt", "pmag_sites.txt", "er_ages.txt"]:
            try:
                fin = open(os.path.join(self.WD, F), 'r')
            except:
                continue
            line = fin.readline()
            line = fin.readline()
            header = line.strip('\n').split('\t')
            if "magic_method_codes" not in header:
                continue
            else:
                index = header.index("magic_method_codes")
            for line in fin.readlines():
                tmp = line.strip('\n').split('\t')
                if len(tmp) >= index:
                    codes = tmp[index].replace(" ", "").split(":")
                    for code in codes:
                        if code != "" and code not in magic_method_codes:
                            magic_method_codes.append(code)
            fin.close()

        if self.data_model == 2:
            magic_method_codes.sort()
            # print magic_method_codes
            magic_methods_header_1 = ["magic_method_code"]
            fout = open(os.path.join(self.WD, "magic_methods.txt"), 'w')
            fout.write("tab\tmagic_methods\n")
            fout.write("magic_method_code\n")
            for code in magic_method_codes:
                fout.write("%s\n" % code)
            fout.close

            # make pmag_criteria.txt if it does not exist
            if not os.path.isfile(os.path.join(self.WD, "pmag_criteria.txt")):
                Fout = open(os.path.join(self.WD, "pmag_criteria.txt"), 'w')
                Fout.write("tab\tpmag_criteria\n")
                Fout.write("er_citation_names\tpmag_criteria_code\n")
                Fout.write("This study\tACCEPT\n")

        dlg1 = wx.MessageDialog(
            self, caption="Message:", message="MagIC files are saved in MagIC project folder", style=wx.OK | wx.ICON_INFORMATION)
        self.show_dlg(dlg1)
        dlg1.Destroy()

        self.close_warning = False

    def converge_pmag_rec_headers(self, old_recs):
        # fix the headers of pmag recs
        recs = {}
        recs = copy.deepcopy(old_recs)
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

    def read_magic_file(self, path, ignore_lines_n, sort_by_this_name):
        DATA = {}
        fin = open(path, 'r')
        # ignore first lines
        for i in range(ignore_lines_n):
            fin.readline()
        # header
        line = fin.readline()
        header = line.strip('\n').split('\t')
        # print header
        for line in fin.readlines():
            if line[0] == "#":
                continue
            tmp_data = {}
            tmp_line = line.strip('\n').split('\t')
            # print tmp_line
            for i in range(len(tmp_line)):
                if i >= len(header):
                    continue
                tmp_data[header[i]] = tmp_line[i]
            DATA[tmp_data[sort_by_this_name]] = tmp_data
        fin.close()
        return(DATA)

    def read_er_ages_file(self, path, ignore_lines_n, sort_by_these_names):
        '''
        read er_ages, sort it by site or sample (the header that is not empty)
        and convert ages to calendar year

        '''
        DATA = {}
        fin = open(path, 'r')
        # ignore first lines
        for i in range(ignore_lines_n):
            fin.readline()
        # header
        line = fin.readline()
        header = line.strip('\n').split('\t')
        # print header
        for line in fin.readlines():
            if line[0] == "#":
                continue
            tmp_data = {}
            tmp_line = line.strip('\n').split('\t')
            for i in range(len(tmp_line)):
                if i >= len(header):
                    continue
                tmp_data[header[i]] = tmp_line[i]
            for name in sort_by_these_names:
                if name in list(tmp_data.keys()) and tmp_data[name] != "":
                    er_ages_rec = self.convert_ages_to_calendar_year(tmp_data)
                    DATA[tmp_data[name]] = er_ages_rec
        fin.close()
        return(DATA)

    def on_menu_docs(self, event):
        webopen("https://earthref.org/PmagPy/cookbook/#x1-560005.1.2", new=2)

    def on_menu_cookbook(self, event):
        webopen("http://earthref.org/PmagPy/cookbook/", new=2)

    def on_menu_git(self, event):
        webopen("https://github.com/PmagPy/PmagPy", new=2)

    def on_menu_debug(self, event):
        pdb.set_trace()

    # ,acceptance_criteria):
    def calculate_sample_mean(self, Data_sample_or_site):
        '''
        Data_sample_or_site is a dictonary holding the samples_or_sites mean
        Data_sample_or_site ={}
        Data_sample_or_site[specimen]=B (in units of microT)
        '''

        pars = {}
        tmp_B = []
        for spec in list(Data_sample_or_site.keys()):
            if 'B' in list(Data_sample_or_site[spec].keys()):
                tmp_B.append(Data_sample_or_site[spec]['B'])
        if len(tmp_B) < 1:
            pars['N'] = 0
            pars['pass_or_fail'] = 'fail'
            return pars

        tmp_B = np.array(tmp_B)
        pars['pass_or_fail'] = 'pass'
        pars['N'] = len(tmp_B)
        pars['B_uT'] = np.mean(tmp_B)
        if len(tmp_B) > 1:
            pars['B_std_uT'] = np.std(tmp_B, ddof=1)
            pars['B_std_perc'] = 100 * (pars['B_std_uT'] / pars['B_uT'])
        else:
            pars['B_std_uT'] = 0
            pars['B_std_perc'] = 0
        pars['sample_int_interval_uT'] = (max(tmp_B) - min(tmp_B))
        pars['sample_int_interval_perc'] = 100 * \
            (pars['sample_int_interval_uT'] / pars['B_uT'])
        pars['fail_list'] = []
        # check if pass criteria
        #----------
        # int_n
        if self.acceptance_criteria['average_by_sample_or_site']['value'] == 'sample':
            average_by_sample_or_site = 'sample'
        else:
            average_by_sample_or_site = 'site'

        if average_by_sample_or_site == 'sample':
            cutoff_value = self.acceptance_criteria['sample_int_n']['value']
        else:
            cutoff_value = self.acceptance_criteria['site_int_n']['value']
        if cutoff_value != -999:
            if pars['N'] < cutoff_value:
                pars['pass_or_fail'] = 'fail'
                pars['fail_list'].append("int_n")
        #----------
        # int_sigma ; int_sigma_perc
        pass_sigma, pass_sigma_perc = False, False
        if self.acceptance_criteria['average_by_sample_or_site']['value'] == 'sample':
            sigma_cutoff_value = self.acceptance_criteria['sample_int_sigma']['value']
        else:
            sigma_cutoff_value = self.acceptance_criteria['site_int_sigma']['value']

        if sigma_cutoff_value != -999:
            if pars['B_std_uT'] * 1e-6 <= sigma_cutoff_value:
                pass_sigma = True

        if self.acceptance_criteria['average_by_sample_or_site']['value'] == 'sample':
            sigma_perc_cutoff_value = self.acceptance_criteria['sample_int_sigma_perc']['value']
        else:
            sigma_perc_cutoff_value = self.acceptance_criteria['site_int_sigma_perc']['value']
        if sigma_perc_cutoff_value != -999:
            if pars['B_std_perc'] <= sigma_perc_cutoff_value:
                pass_sigma_perc = True

        if not (sigma_cutoff_value == -999 and sigma_perc_cutoff_value == -999):
            if not (pass_sigma or pass_sigma_perc):
                pars['pass_or_fail'] = 'fail'
                pars['fail_list'].append("int_sigma")

        pass_int_interval, pass_int_interval_perc = False, False
        if self.acceptance_criteria['average_by_sample_or_site']['value'] == 'sample':
            cutoff_value = self.acceptance_criteria['sample_int_interval_uT']['value']
            if cutoff_value != -999:
                if pars['sample_int_interval_uT'] <= cutoff_value:
                    pass_int_interval = True

            cutoff_value_perc = self.acceptance_criteria['sample_int_interval_perc']['value']
            if cutoff_value_perc != -999:
                if pars['sample_int_interval_perc'] <= cutoff_value_perc:
                    pass_int_interval_perc = True

            if not (cutoff_value == -999 and cutoff_value_perc == -999):
                if not (pass_int_interval or pass_int_interval_perc):
                    pars['pass_or_fail'] = 'fail'
                    pars['fail_list'].append("int_interval")

            # if cutoff_value != -999 or cutoff_value_perc != -999:
            #    if not (pass_int_interval or pass_int_interval_perc):
            #        pars['pass_or_fail']='fail'
            #        pars['fail_list'].append("int_interval")

            #
            #
            #
            #
            # if (acceptance_criteria['sample_int_sigma_uT']==0 and acceptance_criteria['sample_int_sigma_perc']==0) or\
            #    (pars['B_uT'] <= acceptance_criteria['sample_int_sigma_uT'] or pars['B_std_perc'] <= acceptance_criteria['sample_int_sigma_perc']):
            #        if ( pars['sample_int_interval_uT'] <= acceptance_criteria['sample_int_interval_uT'] or pars['sample_int_interval_perc'] <= acceptance_criteria['sample_int_interval_perc']):
            #            pars['pass_or_fail']='pass'
        return(pars)

    def convert_ages_to_calendar_year(self, er_ages_rec):
        '''
        convert all age units to calendar year
        '''
        if ("age" not in list(er_ages_rec.keys())) or (cb.is_null(er_ages_rec['age'], False)):
            return(er_ages_rec)
        if ("age_unit" not in list(er_ages_rec.keys())) or (cb.is_null(er_ages_rec['age_unit'])):
            return(er_ages_rec)
        if cb.is_null(er_ages_rec["age"], False):
            if "age_range_high" in list(er_ages_rec.keys()) and "age_range_low" in list(er_ages_rec.keys()):
                if cb.not_null(er_ages_rec["age_range_high"], False) and cb.not_null(er_ages_rec["age_range_low"], False):
                    er_ages_rec["age"] = np.mean(
                        [float(er_ages_rec["age_range_high"]), float(er_ages_rec["age_range_low"])])
        if cb.is_null(er_ages_rec["age"], False):
            return(er_ages_rec)

            # age_descriptier_ages_recon=er_ages_rec["age_description"]

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
        age = float(er_ages_rec["age"]) * mutliplier
        if age_unit == "Years BP" or age_unit == "Years Cal BP":
            age = 1950 - age
        er_ages_rec['age_cal_year'] = age

        # Fix 'age_range_low':
        age_range_low = age
        age_range_high = age
        age_sigma = 0

        if "age_sigma" in list(er_ages_rec.keys()) and cb.not_null(er_ages_rec["age_sigma"], False):
            age_sigma = float(er_ages_rec["age_sigma"]) * mutliplier
            if age_unit == "Years BP" or age_unit == "Years Cal BP":
                age_sigma = 1950 - age_sigma
            age_range_low = age - age_sigma
            age_range_high = age + age_sigma

        if "age_range_high" in list(er_ages_rec.keys()) and "age_range_low" in list(er_ages_rec.keys()):
            if cb.not_null(er_ages_rec["age_range_high"], False) and cb.not_null(er_ages_rec["age_range_low"], False):
                age_range_high = float(
                    er_ages_rec["age_range_high"]) * mutliplier
                if age_unit == "Years BP" or age_unit == "Years Cal BP":
                    age_range_high = 1950 - age_range_high
                age_range_low = float(
                    er_ages_rec["age_range_low"]) * mutliplier
                if age_unit == "Years BP" or age_unit == "Years Cal BP":
                    age_range_low = 1950 - age_range_low
        er_ages_rec['age_cal_year_range_low'] = age_range_low
        er_ages_rec['age_cal_year_range_high'] = age_range_high

        return(er_ages_rec)

    #----------------------------------------------------------------------
    #----------------------------------------------------------------------

    def On_close_plot_dialog(self, dia):

        COLORS = ['b', 'g', 'r', 'c', 'm', 'y', 'orange', 'gray', 'purple', 'brown', 'indigo', 'darkolivegreen', 'gold', 'mediumorchid',
                  'b', 'g', 'r', 'c', 'm', 'y', 'orange', 'gray', 'purple', 'brown', 'indigo', 'darkolivegreen', 'gold', 'mediumorchid']
        SYMBOLS = ['o', 'd', 'h', 'p', 's', '*', 'v', '<', '>', '^', 'o', 'd', 'h', 'p',
                   's', '*', 'v', '<', '>', '^', 'o', 'd', 'h', 'p', 's', '*', 'v', '<', '>', '^', ]

        set_map_lat_min = ""
        set_map_lat_max = ""
        set_map_lat_grid = ""
        set_map_lon_min = ""
        set_map_lon_max = ""
        set_map_lon_grid = ""

        set_map = {'lat_min': set_map_lat_min, 'lat_max': set_map_lat_max,
                   'lat_grid': set_map_lat_grid, 'lon_min': set_map_lon_min,
                   'lon_max': set_map_lon_max, 'lon_grid': set_map_lon_grid}

        x_autoscale = dia.set_x_axis_auto.GetValue()
        try:
            x_axis_min = float(dia.set_plot_age_min.GetValue())
            x_axis_max = float(dia.set_plot_age_max.GetValue())
        except ValueError:
            pass

        y_autoscale = dia.set_y_axis_auto.GetValue()
        try:
            y_axis_min = float(dia.set_plot_intensity_min.GetValue())
            y_axis_max = float(dia.set_plot_intensity_max.GetValue())
        except ValueError:
            pass

        avg_by = self.acceptance_criteria['average_by_sample_or_site']['value']

        # plt_x_years=dia.set_plot_year.GetValue()
        # plt_x_BP=dia.set_plot_BP.GetValue()
        set_age_unit = dia.set_age_unit.GetValue()
        plt_B = dia.set_plot_B.GetValue()
        plt_VADM = dia.set_plot_VADM.GetValue()
        show_sample_labels = dia.show_samples_ID.GetValue()
        show_x_error_bar = dia.show_x_error_bar.GetValue()
        show_y_error_bar = dia.show_y_error_bar.GetValue()
        show_STDEVOPT = dia.show_STDEVOPT.GetValue()
        show_STDEVOPT_extended = dia.show_STDEVOPT_extended.GetValue()

        if show_STDEVOPT:
            data2plot = {}
            if avg_by == "sample":
                FILE = os.path.join(
                    self.WD, 'thellier_interpreter', 'thellier_interpreter_STDEV-OPT_samples.txt')
                NAME = "er_sample_name"
            else:
                FILE = os.path.join(
                    self.WD, 'thellier_interpreter', 'thellier_interpreter_STDEV-OPT_sites.txt')
                NAME = "er_site_name"
            try:
                data2plot = self.read_magic_file(FILE, 4, NAME)
            except Exception as ex:
                print("-W- Couldn't read file {}".format(FILE), type(ex), ex)
                data2plot = {}
        else:
            if avg_by == 'sample':
                data2plot = copy.deepcopy(self.Data_samples)
            else:
                data2plot = copy.deepcopy(self.Data_sites)
                # data2plot=copy.deepcopy(Data_samples_or_sites)

        Plot_map = dia.show_map.GetValue()
        set_map_autoscale = dia.set_map_autoscale.GetValue()
        set_map['set_map_autoscale'] = set_map_autoscale
        if not set_map_autoscale:
            window_list_commands = ["lat_min", "lat_max",
                                    "lat_grid", "lon_min", "lon_max", "lon_grid"]
            for key in window_list_commands:
                set_map[key] = dia.set_map[key].GetValue()
                if set_map[key] != '':
                    set_map[key] = float(set_map[key])

        plot_by_locations = {}

        # search for lat (for VADM calculation) and age:
        lat_min, lat_max, lon_min, lon_max = 90, -90, 180, -180
        age_min, age_max = 1e10, -1e10
        lats,lons=[],[]
        # if not show_STDEVOPT:
        for sample_or_site in list(data2plot.keys()):
            found_age, found_lat = False, False

            if not show_STDEVOPT:

                # calculate sample/site mean and check if pass criteria
                sample_or_site_mean_pars = self.calculate_sample_mean(
                    data2plot[sample_or_site])  # ,sample_or_site,self.acceptance_criteria)
                if sample_or_site_mean_pars['pass_or_fail'] != 'pass':
                    continue
            else:
                # ,sample_or_site,self.acceptance_criteria)
                sample_or_site_mean_pars = data2plot[sample_or_site]

            # locate site_name
            if avg_by == 'sample':
                site_name = self.Data_hierarchy['site_of_sample'][sample_or_site]
            else:
                site_name = sample_or_site

            #-----
            # search for age data
            #-----

            er_ages_rec = {}
            if sample_or_site in list(self.Data_info["er_ages"].keys()):
                er_ages_rec = self.Data_info["er_ages"][sample_or_site]
            elif site_name in list(self.Data_info["er_ages"].keys()):
                er_ages_rec = self.Data_info["er_ages"][site_name]
            elif sample_or_site in list(self.Data_info["er_{}s".format(avg_by)]):
                er_ages_rec = self.Data_info["er_{}s".format(avg_by)][sample_or_site]
            if "age" in list(er_ages_rec.keys()) and er_ages_rec["age"] != "":
                found_age = True

            if not found_age:
                continue

            # elif "age_range_low" in er_ages_rec.keys() and er_ages_rec["age_range_low"]!="" and "age_range_high" in er_ages_rec.keys() and er_ages_rec["age_range_high"]!="":
            #    found_age=True
            #    er_ages_rec["age"]=np.mean([float(er_ages_rec["age_range_low"]),float(er_ages_rec["age_range_high"])])
            if "age_description" in list(er_ages_rec.keys()):
                age_description = er_ages_rec["age_description"]
            else:
                age_description = ""

            # ignore "poor" and "controversial" ages
            if "poor" in age_description or "controversial" in age_description:
                print("skipping sample %s because of age quality" %
                      sample_or_site)
                self.GUI_log.write(
                    "-W- Plot: skipping sample %s because of age quality\n" % sample_or_site)
                continue

            age_min = min(age_min, float(er_ages_rec["age"]))
            age_max = max(age_max, float(er_ages_rec["age"]))
            #-----
            # search for latitude data
            #-----
            found_lat, found_lon = False, False
            er_sites_rec = {}
            if site_name in list(self.Data_info["er_sites"].keys()):
                er_sites_rec = self.Data_info["er_sites"][site_name]
                if "site_lat" in list(er_sites_rec.keys()) and er_sites_rec["site_lat"] != "":
                    found_lat = True
                    lat = float(er_sites_rec["site_lat"])
                    lats.append(lat)
                else:
                    found_lat = False
                if "site_lon" in list(er_sites_rec.keys()) and er_sites_rec["site_lon"] != "":
                    found_lon = True
                    lon = float(er_sites_rec["site_lon"])
                    if lon > 180:
                        lon = lon - 360.
                    lons.append(lon)

                else:
                    found_lon = False
                # convert lon to -180 to +180

            # try searching for latitude in er_samples.txt

            if found_lat == False:
                if sample_or_site in list(self.Data_info["er_samples"].keys()):
                    er_samples_rec = self.Data_info["er_samples"][sample_or_site]
                    if "sample_lat" in list(er_samples_rec.keys()) and er_samples_rec["sample_lat"] != "":
                        found_lat = True
                        lat = float(er_samples_rec["sample_lat"])
                        lats.append(lat)
                    else:
                        found_lat = False
                    if "sample_lon" in list(er_samples_rec.keys()) and er_samples_rec["sample_lon"] != "":
                        found_lon = True
                        lon = float(er_samples_rec["sample_lon"])
                        if lon > 180:
                            lon = lon - 360.
                        lons.append(lon)

                    else:
                        found_lon = False

            #-----
            # search for latitude data
            # sort by locations
            # calculate VADM
            #-----

            if sample_or_site in list(self.Data_info["er_sites"].keys()):
                location = self.Data_info["er_sites"][sample_or_site]["er_location_name"]
            elif sample_or_site in list(self.Data_info["er_samples"].keys()):
                location = self.Data_info["er_samples"][sample_or_site]["er_location_name"]
            else:
                location = "unknown"

            if cb.is_null(location):
                location = "unknown"

            if location not in list(plot_by_locations.keys()):
                plot_by_locations[location] = {}
                plot_by_locations[location]['X_data'], plot_by_locations[location]['Y_data'] = [
                ], []
                plot_by_locations[location]['X_data_plus'], plot_by_locations[location]['Y_data_plus'] = [
                ], []
                plot_by_locations[location]['X_data_minus'], plot_by_locations[location]['Y_data_minus'] = [
                ], []
                if show_STDEVOPT:
                    plot_by_locations[location]['Y_data_minus_extended'], plot_by_locations[location]['Y_data_plus_extended'] = [
                    ], []
                plot_by_locations[location]['samples_names'] = []
                plot_by_locations[location]['site_lon'], plot_by_locations[location]['site_lat'] = [
                ], []

            if found_lat:
                plot_by_locations[location]['site_lon'] = lon
                plot_by_locations[location]['site_lat'] = lat
                lat_min, lat_max = min(lat_min, lat), max(lat_max, lat)
                lon_min, lon_max = min(lon_min, lon), max(lon_max, lon)

            if show_STDEVOPT:
                B_uT = float(sample_or_site_mean_pars['sample_int_uT'])
                B_std_uT = float(
                    sample_or_site_mean_pars['sample_int_sigma_uT'])
                B_max_extended = float(sample_or_site_mean_pars['sample_int_max_uT']) + float(
                    sample_or_site_mean_pars['sample_int_max_sigma_uT'])
                B_min_extended = float(sample_or_site_mean_pars['sample_int_min_uT']) - float(
                    sample_or_site_mean_pars['sample_int_min_sigma_uT'])
            else:
                B_uT = float(sample_or_site_mean_pars['B_uT'])
                B_std_uT = float(sample_or_site_mean_pars['B_std_uT'])

            if plt_B:
                plot_by_locations[location]['Y_data'].append(B_uT)
                plot_by_locations[location]['Y_data_plus'].append(B_std_uT)
                plot_by_locations[location]['Y_data_minus'].append(B_std_uT)
                plot_by_locations[location]['samples_names'].append(
                    sample_or_site)

                if show_STDEVOPT:
                    plot_by_locations[location]['Y_data_plus_extended'].append(
                        B_max_extended - B_uT)
                    plot_by_locations[location]['Y_data_minus_extended'].append(
                        B_uT - B_min_extended)

            elif plt_VADM and found_lat:  # units of ZAm^2
                VADM = pmag.b_vdm(B_uT * 1e-6, lat) * 1e-21
                VADM_plus = pmag.b_vdm((B_uT + B_std_uT) * 1e-6, lat) * 1e-21
                VADM_minus = pmag.b_vdm((B_uT - B_std_uT) * 1e-6, lat) * 1e-21
                if show_STDEVOPT:
                    VADM_plus_extended = pmag.b_vdm(
                        (B_max_extended) * 1e-6, lat) * 1e-21
                    VADM_minus_extended = pmag.b_vdm(
                        (B_min_extended) * 1e-6, lat) * 1e-21

                plot_by_locations[location]['Y_data'].append(VADM)
                plot_by_locations[location]['Y_data_plus'].append(
                    VADM_plus - VADM)
                plot_by_locations[location]['Y_data_minus'].append(
                    VADM - VADM_minus)
                plot_by_locations[location]['samples_names'].append(
                    sample_or_site)
                if show_STDEVOPT:
                    plot_by_locations[location]['Y_data_plus_extended'].append(
                        VADM_plus_extended - VADM)
                    plot_by_locations[location]['Y_data_minus_extended'].append(
                        VADM - VADM_minus_extended)

            elif plt_VADM and not found_lat:
                self.GUI_log.write(
                    "-W- Plot: skipping sample %s because can't find latitude for V[A]DM calculation\n" % sample_or_site)
                print(
                    "-W- Plot: skipping sample %s because  can't find latitude for V[A]DM calculation\n" % sample_or_site)
                continue

            #-----
            # assign the right age
            #-----

            age = float(er_ages_rec["age_cal_year"])
            age_range_low = float(er_ages_rec["age_cal_year_range_low"])
            age_range_high = float(er_ages_rec["age_cal_year_range_high"])

            # fix ages:
            if set_age_unit == "Years BP":
                age = 1950 - age
                age_range_high = 1950 - age_range_high
                age_range_low = 1950 - age_range_low
            if set_age_unit == "Ka":
                age = age / -1e3
                age_range_high = age_range_high / -1e3
                age_range_low = age_range_low / -1e3
            if set_age_unit == "Ma":
                age = age / -1e6
                age_range_high = age_range_high / -1e6
                age_range_low = age_range_low / -1e6
            if set_age_unit == "Ga":
                age = age / -1e9
                age_range_high = age_range_high / -1e9
                age_range_low = age_range_low / -1e9

            plot_by_locations[location]['X_data'].append(age)
            plot_by_locations[location]['X_data_plus'].append(
                age_range_high - age)
            plot_by_locations[location]['X_data_minus'].append(
                age - age_range_low)

            found_age = False
            found_lat = False

        #--------
        # map
        #--------
        # read in topo data (on a regular lat/lon grid)
        # longitudes go from 20 to 380.
        if Plot_map:
            SiteLat_min = lat_min - 5
            SiteLat_max = lat_max + 5
            SiteLon_min = lon_min - 5
            SiteLon_max = lon_max + 5
            if has_basemap or has_cartopy:
                fig2 = plt.figure(2)
                plt.ion()
                plt.clf()
                plt.ioff()
            if has_cartopy: # make a cartopy basemap
                ax1 = plt.axes(projection=ccrs.PlateCarree())
                ax1.set_extent([SiteLon_min,SiteLon_max,SiteLat_min,SiteLat_max], crs=ccrs.PlateCarree())
                ax1.coastlines(resolution='50m')
                ax1.add_feature(BORDERS,linestyle='--',linewidth=1)
                gl=ax1.gridlines(crs=ccrs.PlateCarree(),linewidth=2,linestyle='dotted',draw_labels=True)
                gl.ylocator=mticker.FixedLocator(np.arange(-80,81,20))
                gl.xlocator=mticker.FixedLocator(np.arange(-180,181,30))
                gl.xformatter = LONGITUDE_FORMATTER
                gl.yformatter = LATITUDE_FORMATTER
                gl.xlabels_top = False
            elif has_basemap: # make a basemap base map
                 if not set_map_autoscale:
                     if set_map_lat_min != "":
                         SiteLat_min = set_map_lat_min
                     if set_map_lat_max != "":
                         SiteLat_max = set_map_lat_max
                     if set_map_lon_min != "":
                         SiteLon_min = set_map_lon_min
                     if set_map_lon_max != "":
                         SiteLon_max = set_map_lon_max

                 m = Basemap(llcrnrlon=SiteLon_min, llcrnrlat=SiteLat_min, urcrnrlon=SiteLon_max,
                             urcrnrlat=SiteLat_max, projection='merc', resolution='i')

                 if set_map_lat_grid != "" and set_map_lon_grid != 0:
                     m.drawparallels(np.arange(SiteLat_min, SiteLat_max + set_map_lat_grid,
                                               set_map_lat_grid), linewidth=0.5, labels=[1, 0, 0, 0], fontsize=10)
                     m.drawmeridians(np.arange(SiteLon_min, SiteLon_max + set_map_lon_grid,
                                               set_map_lon_grid), linewidth=0.5, labels=[0, 0, 0, 1], fontsize=10)

                 else:
                     pass
                     '''lat_min_round=SiteLat_min-SiteLat_min%10
                     lat_max_round=SiteLat_max-SiteLat_max%10
                     lon_min_round=SiteLon_min-SiteLon_min%10
                     lon_max_round=SiteLon_max-SiteLon_max%10
                     m.drawparallels(np.arange(lat_min_round,lat_max_round+5,5),linewidth=0.5,labels=[1,0,0,0],fontsize=10)
                     m.drawmeridians(np.arange(lon_min_round,lon_max_round+5,5),linewidth=0.5,labels=[0,0,0,1],fontsize=10)'''

                 m.fillcontinents(zorder=0, color='0.9')
                 m.drawcoastlines()
                 m.drawcountries()
                 m.drawmapboundary()
# work through sites to make intensity versus age and put locations on basemap
        cnt = 0

        #-----
        # draw paleointensity errorbar plot
        #-----

        # fix ages

        Fig = plt.figure(1, (15, 6))
        plt.clf()
        ax = plt.axes([0.3, 0.1, 0.6, 0.8])
        locations = list(plot_by_locations.keys())
        locations.sort()
        handles_list = []
        for location in locations:
            plt.figure(1)
            X_data, X_data_minus, X_data_plus = plot_by_locations[location]['X_data'], plot_by_locations[
                location]['X_data_minus'], plot_by_locations[location]['X_data_plus']
            Y_data, Y_data_minus, Y_data_plus = plot_by_locations[location]['Y_data'], plot_by_locations[
                location]['Y_data_minus'], plot_by_locations[location]['Y_data_plus']
            if show_STDEVOPT:
                Y_data_minus_extended, Y_data_plus_extended = plot_by_locations[location][
                    'Y_data_minus_extended'], plot_by_locations[location]['Y_data_plus_extended']

            if not show_x_error_bar:
                Xerr = None
            else:
                Xerr = [np.array(X_data_minus), np.array(X_data_plus)]

            if not show_y_error_bar:
                Yerr = None
            else:
                Yerr = [Y_data_minus, Y_data_plus]

            erplot = plt.errorbar(X_data, Y_data, xerr=Xerr, yerr=Yerr, fmt=SYMBOLS[cnt % len(
                SYMBOLS)], color=COLORS[cnt % len(COLORS)], label=location)
            handles_list.append(erplot)
            if show_STDEVOPT:
                plt.errorbar(X_data, Y_data, xerr=None, yerr=[
                             Y_data_minus_extended, Y_data_plus_extended], fmt='.', ms=0, ecolor='red', label="extended error-bar", zorder=0)

            if Plot_map and (has_basemap or has_cartopy):
                #plt.figure(2)
                lat = plot_by_locations[location]['site_lat']
                lon = plot_by_locations[location]['site_lon']
                if has_cartopy:
                    ax1.plot(lon,lat,marker=SYMBOLS[cnt % len(
                        SYMBOLS)], color=COLORS[cnt % len(COLORS)],
                        transform=ccrs.Geodetic(),markeredgecolor='black')
                elif has_basemap:
                    x1, y1 = m([lon], [lat])
                    m.scatter(x1, y1, s=[50], marker=SYMBOLS[cnt % len(
                        SYMBOLS)], color=COLORS[cnt % len(COLORS)], edgecolor='black')
            cnt += 1

        # fig1=figure(1)#,(15,6))

        legend_font_props = matplotlib.font_manager.FontProperties()
        legend_font_props.set_size(12)

        #h,l = ax.get_legend_handles_labels()
        plt.figure(1)
        plt.legend(handles=handles_list, loc='center left', bbox_to_anchor=[
                   0, 0, 1, 1], bbox_transform=Fig.transFigure, numpoints=1, prop=legend_font_props)

        #Fig.legend(h,l,loc='center left',fancybox="True",numpoints=1,prop=legend_font_props)
        y_min, y_max = ax.get_ylim()
        if y_min < 0:
            ax.set_ylim(ymin=0)

        if plt_VADM:
            #ylabel("VADM ZAm^2")
            ax.set_ylabel(r'VADM  $Z Am^2$', fontsize=12)

        if plt_B:
            #ylabel("B (microT)")
            ax.set_ylabel(r'B  $\mu T$', fontsize=12)
        # if plt_x_BP:
        #    #xlabel("years BP")
        #    ax.set_xlabel("years BP",fontsize=12)
        # if plt_x_years:
        #    #xlabel("Date")
        #    ax.set_xlabel("Date",fontsize=12)
        if set_age_unit == "Automatic":
            ax.set_xlabel("Age", fontsize=12)
        else:
            ax.set_xlabel(set_age_unit, fontsize=12)

        if not x_autoscale:
            try:
                ax.set_xlim(xmin=x_axis_min)
            except Exception as ex:
                print(type(ex), ex)
            try:
                ax.set_xlim(xmax=x_axis_max)
            except Exception as ex:
                print(type(ex), ex)

        if not y_autoscale:
            try:
                ax.set_ylim(ymin=y_axis_min)
            except Exception as ex:
                print(type(ex), ex)
            try:
                ax.set_ylim(ymax=y_axis_max)
            except Exception as ex:
                print(type(ex), ex)

        if show_sample_labels:
            xmin, xmax, ymin, ymax = ax.axis()
            for location in locations:
                for i in range(len(plot_by_locations[location]['samples_names'])):
                    x = plot_by_locations[location]['X_data'][i]
                    y = plot_by_locations[location]['Y_data'][i]
                    item_label = "  " + plot_by_locations[location]['samples_names'][i]
                    # don't add sample name if out of plot bounds
                    if x < xmin or x > xmax or y < ymin or y > ymax:
                        continue
                    ax.text(x, y, item_label, fontsize=10, color="0.5")

        xmin, xmax = ax.get_xlim()
        if max([abs(xmin), abs(xmax)]) > 10000 and set_age_unit == "Automatic":
            plt.gca().ticklabel_format(style='scientific', axis='x', scilimits=(0, 0))

        thellier_gui_dialogs.ShowFigure(Fig)
        # if a map figure was made, show it
        try:
            thellier_gui_dialogs.ShowFigure(fig2)
        except UnboundLocalError:
            pass
        dia.Destroy()

#===========================================================
# Draw plots
#===========================================================

    def draw_figure(self, s):
        #start_time = time.time()

        #-----------------------------------------------------------
        # Draw Arai plot
        #-----------------------------------------------------------
        self.s = s

        x_Arai_ZI, y_Arai_ZI = [], []
        x_Arai_IZ, y_Arai_IZ = [], []
        x_Arai = self.Data[self.s]['x_Arai']
        y_Arai = self.Data[self.s]['y_Arai']
        self.pars = self.Data[self.s]['pars']
        x_tail_check = self.Data[self.s]['x_tail_check']
        y_tail_check = self.Data[self.s]['y_tail_check']

        # self.x_additivity_check=self.Data[self.s]['x_additivity_check']
        # self.y_additivity_check=self.Data[self.s]['y_additivity_check']

        self.araiplot.clear()
        self.araiplot.plot(x_Arai, y_Arai, '0.2', lw=0.75, clip_on=False)

        for i in range(len(self.Data[self.s]['steps_Arai'])):
            if self.Data[self.s]['steps_Arai'][i] == "ZI":
                x_Arai_ZI.append(x_Arai[i])
                y_Arai_ZI.append(y_Arai[i])
            elif self.Data[self.s]['steps_Arai'][i] == "IZ":
                x_Arai_IZ.append(x_Arai[i])
                y_Arai_IZ.append(y_Arai[i])
            else:
                self.user_warning(
                    "-E- Can't plot Arai plot. check the data for specimen %s\n" % s)
                self.GUI_log.write(
                    "-E- Can't plot Arai plot. check the data for specimen %s\n" % s)
        if len(x_Arai_ZI) > 0:
            self.araiplot.scatter(x_Arai_ZI, y_Arai_ZI, marker='o', facecolor='r',
                                  edgecolor='k', s=25 * self.GUI_RESOLUTION, clip_on=False)
        if len(x_Arai_IZ) > 0:
            self.araiplot.scatter(x_Arai_IZ, y_Arai_IZ, marker='o', facecolor='b',
                                  edgecolor='k', s=25 * self.GUI_RESOLUTION, clip_on=False)

        # pTRM checks
        if 'x_ptrm_check' in self.Data[self.s]:
            if len(self.Data[self.s]['x_ptrm_check']) > 0:
                self.araiplot.scatter(self.Data[self.s]['x_ptrm_check'], self.Data[self.s]['y_ptrm_check'],
                                      marker='^', edgecolor='0.1', alpha=1.0, facecolor='None', s=80 * self.GUI_RESOLUTION, lw=1)
                if self.preferences['show_Arai_pTRM_arrows']:
                    for i in range(len(self.Data[self.s]['x_ptrm_check'])):
                        xx1, yy1 = self.Data[s]['x_ptrm_check_starting_point'][i], self.Data[s]['y_ptrm_check_starting_point'][i]
                        xx2, yy2 = self.Data[s]['x_ptrm_check'][i], self.Data[s]['y_ptrm_check'][i]
                        self.araiplot.plot(
                            [xx1, xx2], [yy1, yy1], color="0.5", lw=0.5, alpha=0.5, clip_on=False)
                        self.araiplot.plot(
                            [xx2, xx2], [yy1, yy2], color="0.5", lw=0.5, alpha=0.5, clip_on=False)

        # Tail checks
        if len(x_tail_check > 0):
            self.araiplot.scatter(x_tail_check, y_tail_check, marker='s', edgecolor='0.1',
                                  alpha=1.0, facecolor='None', s=80 * self.GUI_RESOLUTION, lw=1, clip_on=False)

        # Additivity checks

        # pTRM checks
        if 'x_additivity_check' in self.Data[self.s]:
            if len(self.Data[self.s]['x_additivity_check']) > 0:
                self.araiplot.scatter(self.Data[self.s]['x_additivity_check'], self.Data[self.s]['y_additivity_check'],
                                      marker='D', edgecolor='0.1', alpha=1.0, facecolor='None', s=80 * self.GUI_RESOLUTION, lw=1, clip_on=False)
                if self.preferences['show_Arai_pTRM_arrows']:
                    for i in range(len(self.Data[self.s]['x_additivity_check'])):
                        xx1, yy1 = self.Data[s]['x_additivity_check_starting_point'][
                            i], self.Data[s]['y_additivity_check_starting_point'][i]
                        xx2, yy2 = self.Data[s]['x_additivity_check'][i], self.Data[s]['y_additivity_check'][i]
                        self.araiplot.plot(
                            [xx1, xx1], [yy1, yy2], color="0.5", lw=0.5, alpha=0.5, clip_on=False)
                        self.araiplot.plot(
                            [xx1, xx2], [yy2, yy2], color="0.5", lw=0.5, alpha=0.5, clip_on=False)

        # Arai plot temperatures

        for i in range(len(self.Data[self.s]['t_Arai'])):
            if self.Data[self.s]['t_Arai'][i] != 0:
                if self.Data[self.s]['T_or_MW'] != "MW":
                    self.tmp_c = self.Data[self.s]['t_Arai'][i] - 273.
                else:
                    self.tmp_c = self.Data[self.s]['t_Arai'][i]
            else:
                self.tmp_c = 0.
            if self.preferences['show_Arai_temperatures'] and int(self.preferences['show_Arai_temperatures_steps']) != 1:
                if (i + 1) % int(self.preferences['show_Arai_temperatures_steps']) == 0 and i != 0:
                    self.araiplot.text(x_Arai[i], y_Arai[i], "  %.0f" % self.tmp_c,
                                       fontsize=10, color='gray', ha='left', va='center', clip_on=False)
            elif not self.preferences['show_Arai_temperatures']:
                continue
            else:
                self.araiplot.text(x_Arai[i], y_Arai[i], "  %.0f" % self.tmp_c,
                                   fontsize=10, color='gray', ha='left', va='center', clip_on=False)


# if len(self.x_additivity_check >0):
##          self.araiplot.scatter (self.x_additivity_check,self.y_additivity_check,marker='D',edgecolor='0.1',alpha=1.0, facecolor='None',s=80*self.GUI_RESOLUTION,lw=1)

        if self.GUI_RESOLUTION > 1.1:
            FONTSIZE = 11
        elif self.GUI_RESOLUTION < 0.9:
            FONTSIZE = 9
        else:
            FONTSIZE = 10

        if self.GUI_RESOLUTION > 1.1:
            FONTSIZE_1 = 11
        elif self.GUI_RESOLUTION < 0.9:
            FONTSIZE_1 = 9
        else:
            FONTSIZE_1 = 10

        self.araiplot.set_xlabel("TRM / NRM0", fontsize=FONTSIZE)
        self.araiplot.set_ylabel("NRM / NRM0", fontsize=FONTSIZE)
        self.araiplot.set_xlim(xmin=0)
        self.araiplot.set_ylim(ymin=0)

        # search for NRM:
        nrm0 = ""
        for rec in self.Data[self.s]['datablock']:
            if "LT-NO" in rec['magic_method_codes']:
                nrm0 = "%.2e" % float(rec['measurement_magn_moment'])
                break

        #self.fig1.text(0.05,0.93,r'$NRM0 = %s Am^2 $'%(nrm0),{'family':self.font_type, 'fontsize':10, 'style':'normal','va':'center', 'ha':'left' })

        # draw()
        self.canvas1.draw()
        self.arai_xlim_initial = self.araiplot.axes.get_xlim()
        self.arai_ylim_initial = self.araiplot.axes.get_ylim()

        # start_time_2=time.time()
        #runtime_sec2 = start_time_2 - start_time
        # print "-I- draw Arai figures is", runtime_sec2,"seconds"

        #-----------------------------------------------------------
        # Draw Zij plot
        #-----------------------------------------------------------

        self.zijplot.clear()
        self.MS = 6 * self.GUI_RESOLUTION
        self.dec_MEC = 'k'
        self.dec_MFC = 'b'
        self.inc_MEC = 'k'
        self.inc_MFC = 'r'
        self.CART_rot = self.Data[self.s]['zij_rotated']
        self.z_temperatures = self.Data[self.s]['z_temp']
        self.vds = self.Data[self.s]['vds']
        self.zijplot.plot(self.CART_rot[:, 0], -1 * self.CART_rot[:, 1], 'bo-', mfc=self.dec_MFC,
                          mec=self.dec_MEC, markersize=self.MS, clip_on=False)  # x,y or N,E
        self.zijplot.plot(self.CART_rot[:, 0], -1 * self.CART_rot[:, 2], 'rs-', mfc=self.inc_MFC,
                          mec=self.inc_MEC, markersize=self.MS, clip_on=False)  # x-z or N,D
        # self.zijplot.axhline(0,c='k')
        # self.zijplot.axvline(0,c='k')
        self.zijplot.axis('off')
        self.zijplot.axis('equal')

        #title(Data[s]['pars']['er_specimen_name']+"\nrotated Zijderveld plot",fontsize=12)
        last_cart_1 = np.array([self.CART_rot[0][0], self.CART_rot[0][1]])
        last_cart_2 = np.array([self.CART_rot[0][0], self.CART_rot[0][2]])
        if self.Data[self.s]['T_or_MW'] != "T":
            K_diff = 0
        else:
            K_diff = 273

        if self.preferences['show_Zij_temperatures']:
            for i in range(len(self.z_temperatures)):
                if int(self.preferences['show_Zij_temperatures_steps']) != 1:
                    if i != 0 and (i + 1) % int(self.preferences['show_Zij_temperatures_steps']) == 0:
                        self.zijplot.text(self.CART_rot[i][0], -1 * self.CART_rot[i][2], " %.0f" % (
                            self.z_temperatures[i] - K_diff), fontsize=FONTSIZE, color='gray', ha='left', va='center', clip_on=False)  # inc
                else:
                    self.zijplot.text(self.CART_rot[i][0], -1 * self.CART_rot[i][2], " %.0f" % (
                        self.z_temperatures[i] - K_diff), fontsize=FONTSIZE, color='gray', ha='left', va='center', clip_on=False)  # inc

        #-----
        xmin, xmax = self.zijplot.get_xlim()
        if xmax < 0:
            xmax = 0
        if xmin > 0:
            xmin = 0
        props = dict(color='black', linewidth=0.5, markeredgewidth=0.5)

        # xlocs = [loc for loc in self.zijplot.xaxis.get_majorticklocs()
        #        if loc>=xmin and loc<=xmax]
        xlocs = np.arange(xmin, xmax, 0.2)
        xtickline, = self.zijplot.plot(xlocs, [0] * len(xlocs), linestyle='',
                                       marker='+', **props)

        axxline, = self.zijplot.plot([xmin, xmax], [0, 0], **props)
        xtickline.set_clip_on(False)
        axxline.set_clip_on(False)
        self.zijplot.text(xmax, 0, ' x', fontsize=10,
                          verticalalignment='bottom', clip_on=False)

        #-----

        ymin, ymax = self.zijplot.get_ylim()
        if ymax < 0:
            ymax = 0
        if ymin > 0:
            ymin = 0

        ylocs = [loc for loc in self.zijplot.yaxis.get_majorticklocs()
                 if loc >= ymin and loc <= ymax]
        ylocs = np.arange(ymin, ymax, 0.2)

        ytickline, = self.zijplot.plot([0] * len(ylocs), ylocs, linestyle='',
                                       marker='+', **props)

        axyline, = self.zijplot.plot([0, 0], [ymin, ymax], **props)
        ytickline.set_clip_on(False)
        axyline.set_clip_on(False)
        self.zijplot.text(0, ymin, ' y,z', fontsize=10,
                          verticalalignment='top', clip_on=False)

        #----

        self.zij_xlim_initial = self.zijplot.axes.get_xlim()
        self.zij_ylim_initial = self.zijplot.axes.get_ylim()

        self.canvas2.draw()

        # start_time_3=time.time()
        #runtime_sec3 = start_time_3 - start_time_2
        # print "-I- draw Zij figures is", runtime_sec3,"seconds"

        #-----------------------------------------------------------
        # Draw Cooling rate data
        #-----------------------------------------------------------

        if self.preferences['show_CR_plot'] == False or 'crblock' not in list(self.Data[self.s].keys()):

            self.fig3.clf()
            self.fig3.text(0.02, 0.96, "Equal area", {
                           'family': self.font_type, 'fontsize': FONTSIZE, 'style': 'normal', 'va': 'center', 'ha': 'left'})
            self.eqplot = self.fig3.add_subplot(111)

            self.draw_net()

            self.zij = np.array(self.Data[self.s]['zdata'])
            self.zij_norm = np.array(
                [row / np.sqrt(sum(row**2)) for row in self.zij])

            x_eq = np.array([row[0] for row in self.zij_norm])
            y_eq = np.array([row[1] for row in self.zij_norm])
            z_eq = abs(np.array([row[2] for row in self.zij_norm]))

            # from Collinson 1983
            R = np.array(np.sqrt(1 - z_eq) / np.sqrt(x_eq**2 + y_eq**2))
            eqarea_data_x = y_eq * R
            eqarea_data_y = x_eq * R
            self.eqplot.plot(eqarea_data_x, eqarea_data_y,
                             lw=0.5, color='gray', clip_on=False)
            #self.eqplot.scatter([eqarea_data_x_dn[i]],[eqarea_data_y_dn[i]],marker='o',edgecolor='0.1', facecolor='blue',s=15,lw=1)

            x_eq_dn, y_eq_dn, z_eq_dn, eq_dn_temperatures = [], [], [], []
            x_eq_dn = np.array([row[0] for row in self.zij_norm if row[2] > 0])
            y_eq_dn = np.array([row[1] for row in self.zij_norm if row[2] > 0])
            z_eq_dn = abs(np.array([row[2]
                                    for row in self.zij_norm if row[2] > 0]))

            if len(x_eq_dn) > 0:
                # from Collinson 1983
                R = np.array(np.sqrt(1 - z_eq_dn) /
                             np.sqrt(x_eq_dn**2 + y_eq_dn**2))
                eqarea_data_x_dn = y_eq_dn * R
                eqarea_data_y_dn = x_eq_dn * R
                self.eqplot.scatter([eqarea_data_x_dn], [eqarea_data_y_dn], marker='o', edgecolor='gray',
                                    facecolor='black', s=15 * self.GUI_RESOLUTION, lw=1, clip_on=False)

            x_eq_up, y_eq_up, z_eq_up = [], [], []
            x_eq_up = np.array([row[0]
                                for row in self.zij_norm if row[2] <= 0])
            y_eq_up = np.array([row[1]
                                for row in self.zij_norm if row[2] <= 0])
            z_eq_up = abs(np.array([row[2]
                                    for row in self.zij_norm if row[2] <= 0]))
            if len(x_eq_up) > 0:
                # from Collinson 1983
                R = np.array(np.sqrt(1 - z_eq_up) /
                             np.sqrt(x_eq_up**2 + y_eq_up**2))
                eqarea_data_x_up = y_eq_up * R
                eqarea_data_y_up = x_eq_up * R
                self.eqplot.scatter([eqarea_data_x_up], [eqarea_data_y_up], marker='o', edgecolor='black',
                                    facecolor='white', s=15 * self.GUI_RESOLUTION, lw=1, clip_on=False)

            if self.GUI_RESOLUTION > 1.1:
                FONTSIZE_1 = 9
            elif self.GUI_RESOLUTION < 0.9:
                FONTSIZE_1 = 8
            else:
                FONTSIZE_1 = 7

            if self.preferences['show_eqarea_temperatures']:
                for i in range(len(self.z_temperatures)):
                    if self.Data[self.s]['T_or_MW'] != "MW":
                        K_dif = 0.
                    else:
                        K_dif = 273.
                    self.eqplot.text(eqarea_data_x[i], eqarea_data_y[i], "%.0f" % (float(
                        self.z_temperatures[i]) - K_dif), fontsize=FONTSIZE_1, color="0.5", clip_on=False)

            #self.eqplot.text(eqarea_data_x[0],eqarea_data_y[0]," NRM",fontsize=8,color='gray',ha='left',va='center')

            # In-field steps" self.preferences["show_eqarea_pTRMs"]
            if self.preferences["show_eqarea_pTRMs"]:
                eqarea_data_x_up, eqarea_data_y_up = [], []
                eqarea_data_x_dn, eqarea_data_y_dn = [], []
                PTRMS = self.Data[self.s]['PTRMS'][1:]
                CART_pTRMS_orig = np.array(
                    [pmag.dir2cart(row[1:4]) for row in PTRMS])
                CART_pTRMS = [row / np.sqrt(sum((np.array(row)**2)))
                              for row in CART_pTRMS_orig]

                for i in range(1, len(CART_pTRMS)):
                    if CART_pTRMS[i][2] <= 0:
                        R = np.sqrt(
                            1. - abs(CART_pTRMS[i][2])) / np.sqrt(CART_pTRMS[i][0]**2 + CART_pTRMS[i][1]**2)
                        eqarea_data_x_up.append(CART_pTRMS[i][1] * R)
                        eqarea_data_y_up.append(CART_pTRMS[i][0] * R)
                    else:
                        R = np.sqrt(
                            1. - abs(CART_pTRMS[i][2])) / np.sqrt(CART_pTRMS[i][0]**2 + CART_pTRMS[i][1]**2)
                        eqarea_data_x_dn.append(CART_pTRMS[i][1] * R)
                        eqarea_data_y_dn.append(CART_pTRMS[i][0] * R)
                if len(eqarea_data_x_up) > 0:
                    self.eqplot.scatter(eqarea_data_x_up, eqarea_data_y_up, marker='^', edgecolor='blue',
                                        facecolor='white', s=15 * self.GUI_RESOLUTION, lw=1, clip_on=False)
                if len(eqarea_data_x_dn) > 0:
                    self.eqplot.scatter(eqarea_data_x_dn, eqarea_data_y_dn, marker='^', edgecolor='gray',
                                        facecolor='blue', s=15 * self.GUI_RESOLUTION, lw=1, clip_on=False)
            self.canvas3.draw()

        else:  # draw cooling rate data
            self.fig3.clf()
            self.fig3.text(0.02, 0.96, "Cooling rate experiment", {
                           'family': self.font_type, 'fontsize': FONTSIZE, 'style': 'normal', 'va': 'center', 'ha': 'left'})
            self.eqplot = self.fig3.add_axes(
                [0.2, 0.15, 0.7, 0.7], frameon=True, facecolor='None')
            if 'cooling_rate_data' in list(self.Data[self.s].keys()) and\
                'ancient_cooling_rate' in list(self.Data[self.s]['cooling_rate_data'].keys()) and\
                    'lab_cooling_rate' in list(self.Data[self.s]['cooling_rate_data'].keys()):
                ancient_cooling_rate = self.Data[self.s]['cooling_rate_data']['ancient_cooling_rate']
                lab_cooling_rate = self.Data[self.s]['cooling_rate_data']['lab_cooling_rate']
                x0 = np.math.log(lab_cooling_rate / ancient_cooling_rate)
                y0 = 1. / \
                    self.Data[self.s]['cooling_rate_data']['CR_correction_factor']
                lan_cooling_rates = self.Data[self.s]['cooling_rate_data']['lan_cooling_rates']
                moment_norm = self.Data[self.s]['cooling_rate_data']['moment_norm']
                (a, b) = self.Data[self.s]['cooling_rate_data']['polyfit']
                y0 = a * x0 + b

                x = np.linspace(0, x0, 10)
                y = np.polyval([a, b], x)
                self.eqplot.plot(x, y, "--", color='k')

                self.eqplot.scatter(lan_cooling_rates, moment_norm, marker='o',
                                    facecolor='b', edgecolor='k', s=25, clip_on=False)
                self.eqplot.scatter(
                    [x0], [y0], marker='s', facecolor='r', edgecolor='k', s=25, clip_on=False)

                # self.Data_info["er_samples"][
                self.eqplot.set_ylabel("TRM / TRM[oven]", fontsize=FONTSIZE_1)
                self.eqplot.set_xlabel("ln(CR[oven]/CR)", fontsize=FONTSIZE_1)
                self.eqplot.set_xlim(left=-0.2)
                try:
                    self.eqplot.tick_params(
                        axis='both', which='major', labelsize=8)
                except Exception as ex:
                    print(type(ex), ex)
                #self.mplot.tick_params(axis='x', which='major', labelsize=8)
                self.eqplot.spines["right"].set_visible(False)
                self.eqplot.spines["top"].set_visible(False)
                self.eqplot.get_xaxis().tick_bottom()
                self.eqplot.get_yaxis().tick_left()

            # draw()
            self.canvas3.draw()

        #-----------------------------------------------------------
        # Draw sample plot (or cooling rate experiment data)
        #-----------------------------------------------------------

        self.draw_sample_mean()

        #-----------------------------------------------------------
        # Draw M/M0 plot ( or NLT data on the same area in the GUI)
        #-----------------------------------------------------------
        self.fig5.clf()

        if self.preferences['show_NLT_plot'] == False or 'NLT_parameters' not in list(self.Data[self.s].keys()):
            self.fig5.clf()
            self.fig5.text(0.02, 0.96, "M/T", {'family': self.font_type,
                                               'fontsize': FONTSIZE, 'style': 'normal', 'va': 'center', 'ha': 'left'})
            self.mplot = self.fig5.add_axes(
                [0.2, 0.15, 0.7, 0.7], frameon=True, facecolor='None')

            self.mplot.clear()
            NRMS = self.Data[self.s]['NRMS']
            PTRMS = self.Data[self.s]['PTRMS']

            if self.Data[self.s]['T_or_MW'] != "MW":
                temperatures_NRMS = np.array([row[0] - 273. for row in NRMS])
                temperatures_PTRMS = np.array([row[0] - 273. for row in PTRMS])
                temperatures_NRMS[0] = 21
                temperatures_PTRMS[0] = 21
            else:
                temperatures_NRMS = np.array([row[0] for row in NRMS])
                temperatures_PTRMS = np.array([row[0] for row in PTRMS])

            if len(temperatures_NRMS) != len(temperatures_PTRMS):
                self.GUI_log.write(
                    "-E- ERROR: NRMS and pTRMS are not equal in specimen %s. Check\n." % self.s)
            else:
                M_NRMS = np.array([row[3] for row in NRMS]) / NRMS[0][3]
                M_pTRMS = np.array([row[3] for row in PTRMS]) / NRMS[0][3]

                self.mplot.clear()
                self.mplot.plot(temperatures_NRMS, M_NRMS, 'bo-', mec='0.2',
                                markersize=5 * self.GUI_RESOLUTION, lw=1, clip_on=False)
                self.mplot.plot(temperatures_NRMS, M_pTRMS, 'ro-', mec='0.2',
                                markersize=5 * self.GUI_RESOLUTION, lw=1, clip_on=False)
                if self.Data[self.s]['T_or_MW'] != "MW":
                    self.mplot.set_xlabel("C", fontsize=FONTSIZE_1)
                else:
                    self.mplot.set_xlabel("Treatment", fontsize=FONTSIZE_1)
                self.mplot.set_ylabel("M / NRM0", fontsize=FONTSIZE_1)
                # self.mplot.set_xtick(labelsize=2)
                try:
                    self.mplot.tick_params(
                        axis='both', which='major', labelsize=8)
                except Exception as ex:
                    print(type(ex), ex)
                #self.mplot.tick_params(axis='x', which='major', labelsize=8)
                self.mplot.spines["right"].set_visible(False)
                self.mplot.spines["top"].set_visible(False)
                self.mplot.get_xaxis().tick_bottom()
                self.mplot.get_yaxis().tick_left()

                # xt=xticks()

            # start_time_6=time.time()
            #runtime_sec6 = start_time_6 - start_time_5
            # print "-I- draw M-M0 figures is", runtime_sec6,"seconds"

            #runtime_sec = time.time() - start_time
            # print "-I- draw figures is", runtime_sec,"seconds"

        #-----------------------------------------------------------
        # Draw NLT plot
        #-----------------------------------------------------------

        else:
            self.fig5.clf()
            self.fig5.text(0.02, 0.96, "Non-linear TRM check", {
                           'family': self.font_type, 'fontsize': 10, 'style': 'normal', 'va': 'center', 'ha': 'left'})
            self.mplot = self.fig5.add_axes(
                [0.2, 0.15, 0.7, 0.7], frameon=True, facecolor='None')
            # self.mplot.clear()
            self.mplot.scatter(np.array(self.Data[self.s]['NLT_parameters']['B_NLT']) * 1e6, self.Data[self.s]
                               ['NLT_parameters']['M_NLT_norm'], marker='o', facecolor='b', edgecolor='k', s=15, clip_on=False)
            self.mplot.set_xlabel("$\mu$ T", fontsize=8)
            self.mplot.set_ylabel(
                "M / M[%.0f]" % (self.Data[self.s]['lab_dc_field'] * 1e6), fontsize=8)
            try:
                self.mplot.tick_params(axis='both', which='major', labelsize=8)
            except Exception as ex:
                print(type(ex), ex)
            # self.mplot.frametick_pa.set_linewidth(0.01)
            self.mplot.set_xlim(xmin=0)
            self.mplot.set_ylim(ymin=0)
            xmin, xmax = self.mplot.get_xlim()
            x = np.linspace(xmin + 0.1, xmax, 100)
            alpha = self.Data[self.s]['NLT_parameters']['tanh_parameters'][0][0]
            beta = self.Data[self.s]['NLT_parameters']['tanh_parameters'][0][1]
            y = alpha * (np.tanh(x * 1e-6 * beta))
            labfiled = self.Data[self.s]['lab_dc_field']
            self.mplot.plot(x, x * 1e-6 * (alpha * (np.tanh(labfiled * beta)) /
                                           labfiled), '--', color='black', linewidth=0.7, clip_on=False)
            self.mplot.plot(x, y, '-', color='green', linewidth=1)

            # self.mplot.spines["right"].set_visible(False)
            # self.mplot.spines["top"].set_visible(False)
            # self.mplot.get_xaxis().tick_bottom()
            # self.mplot.get_yaxis().tick_left()

        self.canvas5.draw()

        # Data[s]['NLT_parameters']v

    def draw_net(self):
        self.eqplot.clear()
        eq = self.eqplot
        eq.axis((-1, 1, -1, 1))
        eq.axis('off')
        theta = np.arange(0., 2 * np.pi, 2 * np.pi / 1000)
        eq.plot(np.cos(theta), np.sin(theta), 'k', clip_on=False)
        eq.vlines((0, 0), (0.9, -0.9), (1.0, -1.0), 'k')
        eq.hlines((0, 0), (0.9, -0.9), (1.0, -1.0), 'k')
        eq.plot([0.0], [0.0], '+k', clip_on=False)
        return()

    def arrow_keys(self):
        self.Bind(wx.EVT_CHAR, self.onCharEvent)

    def onCharEvent(self, event):
        keycode = event.GetKeyCode()
        controlDown = event.CmdDown()
        altDown = event.AltDown()
        shiftDown = event.ShiftDown()

        if keycode == wx.WXK_RIGHT or keycode == wx.WXK_NUMPAD_RIGHT or keycode == wx.WXK_WINDOWS_RIGHT:
            # print "you pressed the right!"
            self.on_next_button(None)
        elif keycode == wx.WXK_LEFT or keycode == wx.WXK_NUMPAD_LEFT or keycode == wx.WXK_WINDOWS_LEFT:
            # print "you pressed the right!"
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
        # Update GUI
        #-------------------------------------------------
        s = self.s

        # continue only if temperature bounds were assigned

        if "measurement_step_min" not in list(self.pars.keys()) or "measurement_step_max" not in list(self.pars.keys()):
            return(self.pars)
        if self.Data[self.s]['T_or_MW'] != "MW":
            self.tmin_box.SetValue(
                "%.0f" % (float(self.pars['measurement_step_min']) - 273.))
            self.tmax_box.SetValue(
                "%.0f" % (float(self.pars['measurement_step_max']) - 273.))
        else:
            self.tmin_box.SetValue(
                "%.0f" % (float(self.pars['measurement_step_min'])))
            self.tmax_box.SetValue(
                "%.0f" % (float(self.pars['measurement_step_max'])))

        # First,re-draw the figures
        self.draw_figure(s)

        # now draw the interpretation
        self.draw_interpretation()

        # declination/inclination
        if 'specimen_dec' in list(self.pars.keys()):
            self.declination_window.SetValue(
                "%.1f" % (self.pars['specimen_dec']))
            self.declination_window.SetBackgroundColour(wx.WHITE)
        else:
            self.declination_window.SetValue("")
            self.declination_window.SetBackgroundColour(wx.Colour('grey'))
        if 'specimen_inc' in list(self.pars.keys()):
            self.inclination_window.SetValue(
                "%.1f" % (self.pars['specimen_inc']))
            self.inclination_window.SetBackgroundColour(wx.WHITE)
        else:
            self.inclination_window.SetValue("")
            self.inclination_window.SetBackgroundColour(wx.Colour('grey'))

        # PI statsistics
        flag_Fail = False
        for short_stat in self.preferences['show_statistics_on_gui']:
            stat = "specimen_" + short_stat
            # ignore unwanted statistics
            if stat == 'specimen_scat':
                continue
            if type(self.acceptance_criteria[stat]['decimal_points']) != float and type(self.acceptance_criteria[stat]['decimal_points']) != int:
                continue
            if type(self.acceptance_criteria[stat]['value']) != float and type(self.acceptance_criteria[stat]['value']) != int:
                continue

            # get the value
            value = ''
            if self.acceptance_criteria[stat]['decimal_points'] == -999:
                value = '%.2e' % self.pars[stat]
            elif type(self.acceptance_criteria[stat]['decimal_points']) == float or type(self.acceptance_criteria[stat]['decimal_points']) == int:
                value = "{:.{}f}".format(self.pars[stat],
                                         int(self.acceptance_criteria[stat]['decimal_points']))
            # elif  stat=='specimen_scat':
            #    value= str(self.acceptance_criteria[stat]['value'])
            # write the value
            self.stat_windows[short_stat].SetValue(value)

            # set backgound color
            cutoff_value = self.acceptance_criteria[stat]['value']
            if cutoff_value == -999:
                self.stat_windows[short_stat].SetBackgroundColour(wx.WHITE)
                # # set text color
            elif stat == "specimen_k" or stat == "specimen_k_prime":
                if abs(self.pars[stat]) > cutoff_value:
                    self.stat_windows[short_stat].SetBackgroundColour(wx.RED)
                    # # set text color
                    flag_Fail = True
                else:
                    self.stat_windows[short_stat].SetBackgroundColour(wx.GREEN)
                    # # set text color
            elif self.acceptance_criteria[stat]['threshold_type'] == 'high' and self.pars[stat] > cutoff_value:
                self.stat_windows[short_stat].SetBackgroundColour(wx.RED)
                # # set text color
                flag_Fail = True
            elif self.acceptance_criteria[stat]['threshold_type'] == 'low' and self.pars[stat] < cutoff_value:
                self.stat_windows[short_stat].SetBackgroundColour(wx.RED)
                # # set text color
                flag_Fail = True
            else:
                self.stat_windows[short_stat].SetBackgroundColour(wx.GREEN)

        # specimen_scat
        # if 'scat' in self.preferences['show_statistics_on_gui']:
        if "specimen_scat" in self.pars:
            scat_window = self.stat_windows['scat']
            in_acceptance = self.acceptance_criteria['specimen_scat']['value'] in [
                'True', 'TRUE', '1', 1, True, 'g']
            if self.pars["specimen_scat"] == 'Pass':
                scat_window.SetValue("Pass")
                if in_acceptance:
                    scat_window.SetBackgroundColour(
                        wx.GREEN)  # set background color
                else:
                    scat_window.SetBackgroundColour(wx.WHITE)
            else:
                scat_window.SetValue("Fail")
                if in_acceptance:
                    scat_window.SetBackgroundColour(
                        wx.RED)  # set background color
                else:
                    scat_window.SetBackgroundColour(wx.WHITE)

        else:
            try:
                scat_window.SetValue("")
                scat_window.SetBackgroundColour(
                    wx.Colour('grey'))  # set text color
            # don't break if SCAT is not displayed
            except UnboundLocalError:
                pass

        # Blab, Banc, correction factors

        self.Blab_window.SetValue(
            "%.0f" % (float(self.Data[self.s]['pars']['lab_dc_field']) * 1e6))

        self.Banc_window.SetValue("%.1f" % (self.pars['specimen_int_uT']))
        if flag_Fail:
            self.Banc_window.SetBackgroundColour(wx.RED)
        else:
            self.Banc_window.SetBackgroundColour(wx.GREEN)

        if "AniSpec" in self.Data[self.s]:
            self.Aniso_factor_window.SetValue(
                "%.2f" % (self.pars['Anisotropy_correction_factor']))
            if self.pars["AC_WARNING"] != "" and\
                    ("TRM" in self.pars["AC_WARNING"] and self.pars["AC_anisotropy_type"] == "ATRM" and "alteration" in self.pars["AC_WARNING"]):
                self.Aniso_factor_window.SetBackgroundColour(wx.RED)
            elif self.pars["AC_WARNING"] != "" and\
                    (("TRM" in self.pars["AC_WARNING"] and self.pars["AC_anisotropy_type"] == "ATRM" and "F-test" in self.pars["AC_WARNING"] and "alteration" not in self.pars["AC_WARNING"])
                     or
                     ("ARM" in self.pars["AC_WARNING"] and self.pars["AC_anisotropy_type"] == "AARM" and "F-test" in self.pars["AC_WARNING"])):
                self.Aniso_factor_window.SetBackgroundColour('#FFFACD')
            else:
                self.Aniso_factor_window.SetBackgroundColour(wx.GREEN)

        else:
            self.Aniso_factor_window.SetValue("")
            self.Aniso_factor_window.SetBackgroundColour(wx.Colour('grey'))

        if self.pars['NLT_specimen_correction_factor'] != -1:
            self.NLT_factor_window.SetValue(
                "%.2f" % (self.pars['NLT_specimen_correction_factor']))
        else:
            self.NLT_factor_window.SetValue("")
            self.NLT_factor_window.SetBackgroundColour(wx.Colour("grey"))

        if self.pars['specimen_int_corr_cooling_rate'] != -1 and self.pars['specimen_int_corr_cooling_rate'] != -999:
            self.CR_factor_window.SetValue(
                "%.2f" % (self.pars['specimen_int_corr_cooling_rate']))
            if 'CR_flag' in list(self.pars.keys()) and self.pars['CR_flag'] == "calculated":
                self.CR_factor_window.SetBackgroundColour(wx.GREEN)
            elif 'CR_WARNING' in list(self.pars.keys()) and 'inferred' in self.pars['CR_WARNING']:
                self.CR_factor_window.SetBackgroundColour('#FFFACD')
            else:
                self.CR_factor_window.SetBackgroundColour(wx.WHITE)

        else:
            self.CR_factor_window.SetValue("")
            self.CR_factor_window.SetBackgroundColour(wx.Colour('grey'))

        # sample
        self.write_sample_box()


#===========================================================
# calculate PI statistics
#===========================================================

    def get_new_T_PI_parameters(self, event):
        """
        calcualte statisics when temperatures are selected
        """

        # remember the last saved interpretation
        if "saved" in list(self.pars.keys()):
            if self.pars['saved']:
                self.last_saved_pars = {}
                for key in list(self.pars.keys()):
                    self.last_saved_pars[key] = self.pars[key]
        self.pars['saved'] = False
        t1 = self.tmin_box.GetValue()
        t2 = self.tmax_box.GetValue()

        if (t1 == "" or t2 == ""):
            print("empty interpretation bounds")
            return
        if float(t2) < float(t1):
            print("upper bound less than lower bound")
            return

        index_1 = self.T_list.index(t1)
        index_2 = self.T_list.index(t2)

        # if (index_2-index_1)+1 >= self.acceptance_criteria['specimen_int_n']:
        if (index_2 - index_1) + 1 >= 3:
            if self.Data[self.s]['T_or_MW'] != "MW":
                self.pars = thellier_gui_lib.get_PI_parameters(self.Data, self.acceptance_criteria, self.preferences, self.s, float(
                    t1) + 273., float(t2) + 273., self.GUI_log, THERMAL, MICROWAVE)
                self.Data[self.s]['pars'] = self.pars
            else:
                self.pars = thellier_gui_lib.get_PI_parameters(
                    self.Data, self.acceptance_criteria, self.preferences, self.s, float(t1), float(t2), self.GUI_log, THERMAL, MICROWAVE)
                self.Data[self.s]['pars'] = self.pars
            self.update_GUI_with_new_interpretation()
            self.Add_text(self.s)

    def draw_interpretation(self):

        if "measurement_step_min" not in list(self.pars.keys()) or "measurement_step_max" not in list(self.pars.keys()):
            return()

        s = self.s
        pars = self.Data[s]['pars']
        datablock = self.Data[s]['datablock']
        pars = self.Data[s]['pars']

        t_Arai = self.Data[s]['t_Arai']
        x_Arai = self.Data[s]['x_Arai']
        y_Arai = self.Data[s]['y_Arai']
        x_tail_check = self.Data[s]['x_tail_check']
        y_tail_check = self.Data[s]['y_tail_check']

        zijdblock = self.Data[s]['zijdblock']
        z_temperatures = self.Data[s]['z_temp']

        start = t_Arai.index(self.pars["measurement_step_min"])
        end = t_Arai.index(self.pars["measurement_step_max"])

        x_Arai_segment = x_Arai[start:end + 1]
        y_Arai_segment = y_Arai[start:end + 1]

        self.araiplot.scatter([x_Arai_segment[0], x_Arai_segment[-1]], [y_Arai_segment[0],
                                                                        y_Arai_segment[-1]], marker='o', facecolor='g', edgecolor='k', s=30)
        b = pars["specimen_b"]
        a = np.mean(y_Arai_segment) - b * np.mean(x_Arai_segment)
        xx = np.array([x_Arai_segment[0], x_Arai_segment[-1]])
        yy = b * xx + a
        self.araiplot.plot(xx, yy, 'g-', lw=2, alpha=0.5)
        if self.acceptance_criteria['specimen_scat']['value'] in [True, "True", "TRUE", '1', 'g']:
            if 'specimen_scat_bounding_line_low' in pars:
                # prevents error if there are no SCAT lines available
                if pars['specimen_scat_bounding_line_low'] != 0:
                    yy1 = xx * pars['specimen_scat_bounding_line_low'][1] + \
                        pars['specimen_scat_bounding_line_low'][0]
                    yy2 = xx * pars['specimen_scat_bounding_line_high'][1] + \
                        pars['specimen_scat_bounding_line_high'][0]
                    self.araiplot.plot(xx, yy1, '--', lw=0.5, alpha=0.5)
                    self.araiplot.plot(xx, yy2, '--', lw=0.5, alpha=0.5)

        self.araiplot.set_xlim(xmin=0)
        self.araiplot.set_ylim(ymin=0)

#        pylab.draw()
        self.canvas1.draw()

        # plot best fit direction on Equal Area plot
        CART = np.array(pars["specimen_PCA_v1"]) / \
            np.sqrt(sum(np.array(pars["specimen_PCA_v1"])**2))
        x = CART[0]
        y = CART[1]
        z = abs(CART[2])
        R = np.array(np.sqrt(1 - z) / np.sqrt(x**2 + y**2))
        eqarea_x = y * R
        eqarea_y = x * R

        if self.preferences['show_CR_plot'] == False or 'crblock' not in list(self.Data[self.s].keys()):
            if z > 0:
                FC = 'green'
                EC = '0.1'
            else:
                FC = 'yellow'
                EC = 'green'
            self.eqplot.scatter(
                [eqarea_x], [eqarea_y], marker='o', edgecolor=EC, facecolor=FC, s=30, lw=1)

            self.canvas3.draw()

        # plot Zijderveld

        ymin, ymax = self.zijplot.get_ylim()
        xmin, xmax = self.zijplot.get_xlim()

        # rotated zijderveld
        NRM_dir = pmag.cart2dir(self.Data[self.s]['zdata'][0])
        NRM_dec = NRM_dir[0]

        # PCA direction
        PCA_dir_rotated = pmag.cart2dir(CART)
        PCA_dir_rotated[0] = PCA_dir_rotated[0] - NRM_dec
        PCA_CART_rotated = pmag.dir2cart(PCA_dir_rotated)

        tmin_index = self.Data[self.s]['z_temp'].index(
            self.pars["measurement_step_min"])
        tmax_index = self.Data[self.s]['z_temp'].index(
            self.pars["measurement_step_max"])

        PCA_dir_rotated = pmag.cart2dir(CART)
        PCA_dir_rotated[0] = PCA_dir_rotated[0] - NRM_dec
        PCA_CART_rotated = pmag.dir2cart(PCA_dir_rotated)

        slop_xy_PCA = -1 * PCA_CART_rotated[1] / PCA_CART_rotated[0]
        slop_xz_PCA = -1 * PCA_CART_rotated[2] / PCA_CART_rotated[0]

        # Center of mass rotated

        CM_x = np.mean(self.CART_rot[:, 0][tmin_index:tmax_index + 1])
        CM_y = np.mean(self.CART_rot[:, 1][tmin_index:tmax_index + 1])
        CM_z = np.mean(self.CART_rot[:, 2][tmin_index:tmax_index + 1])

        # intercpet from the center of mass
        intercept_xy_PCA = -1 * CM_y - slop_xy_PCA * CM_x
        intercept_xz_PCA = -1 * CM_z - slop_xz_PCA * CM_x

        xmin_zij, xmax_zij = self.zijplot.get_xlim()
        xx = np.array([0, self.CART_rot[:, 0][tmin_index]])
        yy = slop_xy_PCA * xx + intercept_xy_PCA
        self.zijplot.plot(xx, yy, '-', color='g', lw=1.5, alpha=0.5)
        zz = slop_xz_PCA * xx + intercept_xz_PCA
        self.zijplot.plot(xx, zz, '-', color='g', lw=1.5, alpha=0.5)

        self.zijplot.scatter([self.CART_rot[:, 0][tmin_index]], [-1 * self.CART_rot[:, 1]
                                                                 [tmin_index]], marker='o', s=40, facecolor='g', edgecolor='k', zorder=100)
        self.zijplot.scatter([self.CART_rot[:, 0][tmax_index]], [-1 * self.CART_rot[:, 1]
                                                                 [tmax_index]], marker='o', s=40, facecolor='g', edgecolor='k', zorder=100)
        self.zijplot.scatter([self.CART_rot[:, 0][tmin_index]], [-1 * self.CART_rot[:, 2]
                                                                 [tmin_index]], marker='s', s=50, facecolor='g', edgecolor='k', zorder=100)
        self.zijplot.scatter([self.CART_rot[:, 0][tmax_index]], [-1 * self.CART_rot[:, 2]
                                                                 [tmax_index]], marker='s', s=50, facecolor='g', edgecolor='k', zorder=100)

        self.zijplot.set_xlim(xmin, xmax)
        self.zijplot.set_ylim(ymin, ymax)
        self.zijplot.axis("equal")

        self.canvas2.draw()

        # NLT plot
        if self.preferences['show_NLT_plot'] == True and 'NLT_parameters' in list(self.Data[self.s].keys()):
            alpha = self.Data[self.s]['NLT_parameters']['tanh_parameters'][0][0]
            beta = self.Data[self.s]['NLT_parameters']['tanh_parameters'][0][1]
            # labfiled=self.Data[self.s]['lab_dc_field']
            Banc = self.pars["specimen_int_uT"]
            self.mplot.scatter([Banc], [alpha * (np.tanh(beta * Banc * 1e-6))],
                               marker='o', s=30, facecolor='g', edgecolor='k')

        self.canvas5.draw()
#        pylab.draw()

        #------
        # Drow sample mean
        #------

        self.draw_sample_mean()

    def draw_sample_mean(self):

        self.sampleplot.clear()
        specimens_id = []
        specimens_B = []
        sample = self.Data_hierarchy['specimens'][self.s]
        site = thellier_gui_lib.get_site_from_hierarchy(
            sample, self.Data_hierarchy)

        # average by sample
        # print self.average_by_sample_or_site
        if self.acceptance_criteria['average_by_sample_or_site']['value'] == 'sample':
            if sample in list(self.Data_samples.keys()):
                specimens_list = list(self.Data_samples[sample].keys())
                if self.s not in specimens_list and 'specimen_int_uT' in list(self.pars.keys()):
                    specimens_list.append(self.s)
                specimens_list.sort()
                for spec in specimens_list:
                    if spec == self.s and 'specimen_int_uT' in list(self.pars.keys()):
                        specimens_B.append(self.pars['specimen_int_uT'])
                        specimens_id.append(spec)
                    else:
                        if spec in list(self.Data_samples[sample].keys()) and 'B' in list(self.Data_samples[sample][spec].keys()):
                            specimens_B.append(
                                self.Data_samples[sample][spec]['B'])
                            specimens_id.append(spec)
            else:
                if 'specimen_int_uT' in list(self.pars.keys()):
                    specimens_id = [self.s]
                    specimens_B = [self.pars['specimen_int_uT']]
        # average by site
        else:
            if site in list(self.Data_sites.keys()):

                specimens_list = list(self.Data_sites[site].keys())
                if self.s not in specimens_list and 'specimen_int_uT' in list(self.pars.keys()):
                    specimens_list.append(self.s)
                specimens_list.sort()
                for spec in specimens_list:
                    if spec == self.s and 'specimen_int_uT' in list(self.pars.keys()):
                        specimens_B.append(self.pars['specimen_int_uT'])
                        specimens_id.append(spec)
                    else:
                        if spec in list(self.Data_sites[site].keys()) and 'B' in list(self.Data_sites[site][spec].keys()):
                            specimens_B.append(
                                self.Data_sites[site][spec]['B'])
                            specimens_id.append(spec)
            else:
                if 'specimen_int_uT' in list(self.pars.keys()):
                    specimens_id = [self.s]
                    specimens_B = [self.pars['specimen_int_uT']]

        if len(specimens_id) > 1:
            self.sampleplot.scatter(np.arange(len(specimens_id)), specimens_B, marker='s',
                                    edgecolor='0.2', facecolor='b', s=40 * self.GUI_RESOLUTION, lw=1)
            self.sampleplot.axhline(y=np.mean(
                specimens_B) + np.std(specimens_B, ddof=1), color='0.2', ls="--", lw=0.75)
            self.sampleplot.axhline(y=np.mean(
                specimens_B) - np.std(specimens_B, ddof=1), color='0.2', ls="--", lw=0.75)
            self.sampleplot.axhline(
                y=np.mean(specimens_B), color='0.2', ls="-", lw=0.75, alpha=0.5)

            if self.s in specimens_id:
                self.sampleplot.scatter([specimens_id.index(self.s)], [specimens_B[specimens_id.index(
                    self.s)]], marker='s', edgecolor='0.2', facecolor='g', s=40 * self.GUI_RESOLUTION, lw=1)

            self.sampleplot.set_xticks(np.arange(len(specimens_id)))
            self.sampleplot.set_xlim(-0.5, len(specimens_id) - 0.5)
            self.sampleplot.set_xticklabels(
                specimens_id, rotation=90, fontsize=8)
            # ymin,ymax=self.sampleplot.ylim()

            # if "sample_int_sigma" in self.acceptance_criteria.keys() and
            # "sample_int_sigma_perc" in self.acceptance_criteria.keys():
            sigma_threshold_for_plot_1, sigma_threshold_for_plot_2 = 0, 0
            #    sigma_threshold_for_plot=max(self.acceptance_criteria["sample_int_sigma"]*,0.01*self.acceptance_criteria["sample_int_sigma_perc"]*np.mean(specimens_B))
            if self.acceptance_criteria["sample_int_sigma"]["value"] != -999 and type(self.acceptance_criteria["sample_int_sigma"]["value"]) == float:
                sigma_threshold_for_plot_1 = self.acceptance_criteria["sample_int_sigma"]["value"] * 1e6
            if self.acceptance_criteria["sample_int_sigma_perc"]["value"] != -999 and type(self.acceptance_criteria["sample_int_sigma_perc"]["value"]) == float:
                sigma_threshold_for_plot_2 = np.mean(
                    specimens_B) * 0.01 * self.acceptance_criteria["sample_int_sigma_perc"]['value']
            # sigma_threshold_for_plot 100000
            sigma_threshold_for_plot = max(
                sigma_threshold_for_plot_1, sigma_threshold_for_plot_2)
            if sigma_threshold_for_plot < 20 and sigma_threshold_for_plot != 0:
                self.sampleplot.axhline(
                    y=np.mean(specimens_B) + sigma_threshold_for_plot, color='r', ls="--", lw=0.75)
                self.sampleplot.axhline(
                    y=np.mean(specimens_B) - sigma_threshold_for_plot, color='r', ls="--", lw=0.75)
                y_axis_limit = max(sigma_threshold_for_plot, np.std(specimens_B, ddof=1), abs(max(
                    specimens_B) - np.mean(specimens_B)), abs((min(specimens_B) - np.mean(specimens_B))))
            else:
                y_axis_limit = max(np.std(specimens_B, ddof=1), abs(max(
                    specimens_B) - np.mean(specimens_B)), abs((min(specimens_B) - np.mean(specimens_B))))

            self.sampleplot.set_ylim(np.mean(
                specimens_B) - y_axis_limit - 1, np.mean(specimens_B) + y_axis_limit + 1)
            self.sampleplot.set_ylabel('uT', fontsize=8)
            try:
                self.sampleplot.tick_params(
                    axis='both', which='major', labelsize=8)
            except Exception as ex:
                print(type(ex), ex)
            try:
                self.sampleplot.tick_params(
                    axis='y', which='minor', labelsize=0)
            except Exception as ex:
                print(ex, type(ex))

        self.canvas4.draw()
        # start_time_5=time.time()
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

        self.show_dlg(dlg)
        dlg.Destroy()

    def add_thellier_gui_criteria(self):
        '''criteria used only in thellier gui
        these criteria are not written to pmag_criteria.txt
        '''
        category = "thellier_gui"
        for crit in ['sample_int_n_outlier_check', 'site_int_n_outlier_check']:
            self.acceptance_criteria[crit] = {}
            self.acceptance_criteria[crit]['category'] = category
            self.acceptance_criteria[crit]['criterion_name'] = crit
            self.acceptance_criteria[crit]['value'] = -999
            self.acceptance_criteria[crit]['threshold_type'] = "low"
            self.acceptance_criteria[crit]['decimal_points'] = 0

        for crit in ['sample_int_interval_uT', 'sample_int_interval_perc',
                     'site_int_interval_uT', 'site_int_interval_perc',
                     'sample_int_BS_68_uT', 'sample_int_BS_95_uT', 'sample_int_BS_68_perc', 'sample_int_BS_95_perc', 'specimen_int_max_slope_diff']:
            self.acceptance_criteria[crit] = {}
            self.acceptance_criteria[crit]['category'] = category
            self.acceptance_criteria[crit]['criterion_name'] = crit
            self.acceptance_criteria[crit]['value'] = -999
            self.acceptance_criteria[crit]['threshold_type'] = "high"
            if crit in ['specimen_int_max_slope_diff']:
                self.acceptance_criteria[crit]['decimal_points'] = -999
            else:
                self.acceptance_criteria[crit]['decimal_points'] = 1
            self.acceptance_criteria[crit]['comments'] = "thellier_gui_only"

        for crit in ['average_by_sample_or_site', 'interpreter_method']:
            self.acceptance_criteria[crit] = {}
            self.acceptance_criteria[crit]['category'] = category
            self.acceptance_criteria[crit]['criterion_name'] = crit
            if crit in ['average_by_sample_or_site']:
                self.acceptance_criteria[crit]['value'] = 'sample'
            if crit in ['interpreter_method']:
                self.acceptance_criteria[crit]['value'] = 'stdev_opt'
            self.acceptance_criteria[crit]['threshold_type'] = "flag"
            self.acceptance_criteria[crit]['decimal_points'] = -999

        for crit in ['include_nrm']:
            self.acceptance_criteria[crit] = {}
            self.acceptance_criteria[crit]['category'] = category
            self.acceptance_criteria[crit]['criterion_name'] = crit
            self.acceptance_criteria[crit]['value'] = True
            self.acceptance_criteria[crit]['threshold_type'] = "bool"
            self.acceptance_criteria[crit]['decimal_points'] = -999

        # define internal Thellier-GUI definitions:
        self.average_by_sample_or_site = 'sample'
        self.stdev_opt = True
        self.bs = False
        self.bs_par = False

    def get_data(self):

        def tan_h(x, a, b):
            return a * np.tanh(b * x)

        def cart2dir(cart):  # OLD ONE
            """
            converts a direction to cartesian coordinates
            """
            Dir = []  # establish a list to put directions in
            rad = pi / 180.  # constant to convert degrees to radians
            # calculate resultant vector length
            R = np.sqrt(cart[0]**2 + cart[1]**2 + cart[2]**2)
            if R == 0:
                # print 'trouble in cart2dir'
                # print cart
                return [0.0, 0.0, 0.0]
            # calculate declination taking care of correct quadrants (arctan2)
            D = arctan2(cart[1], cart[0]) / rad
            if D < 0:
                D = D + 360.  # put declination between 0 and 360.
            if D > 360.:
                D = D - 360.
            Dir.append(D)  # append declination to Dir list
            # calculate inclination (converting to degrees)
            I = np.arcsin(cart[2] / R) / rad
            Dir.append(I)  # append inclination to Dir list
            Dir.append(R)  # append vector length to Dir list
            return Dir  # return the directions list

        def dir2cart(d):
           # converts list or array of vector directions, in degrees, to array
           # of cartesian coordinates, in x,y,z
            # get an array of ones to plug into dec,inc pairs
            ints = ones(len(d)).transpose()
            d = np.array(d)
            rad = pi / 180.
            if len(d.shape) > 1:  # array of vectors
                decs, incs = d[:, 0] * rad, d[:, 1] * rad
                if d.shape[1] == 3:
                    ints = d[:, 2]  # take the given lengths
            else:  # single vector
                decs, incs = np.array(d[0]) * rad, np.array(d[1]) * rad
                if len(d) == 3:
                    ints = np.array(d[2])
                else:
                    ints = np.array([1.])
            cart = np.array([ints * np.cos(decs) * np.cos(incs), ints *
                             np.sin(decs) * np.cos(incs), ints * np.sin(incs)]).transpose()
            return cart

        # self.dir_pathes=self.WD

        #------------------------------------------------
        # Read measurement file and sort to blocks
        #------------------------------------------------

        # All data information is stored in Data[secimen]={}
        Data = {}
        Data_hierarchy = {}
        Data_hierarchy['locations'] = {}
        Data_hierarchy['sites'] = {}
        Data_hierarchy['samples'] = {}
        Data_hierarchy['specimens'] = {}
        Data_hierarchy['sample_of_specimen'] = {}
        Data_hierarchy['site_of_specimen'] = {}
        Data_hierarchy['site_of_sample'] = {}

        # add dir to dir pathes for interpterer:
        if self.WD not in self.MagIC_directories_list:
            self.MagIC_directories_list.append(self.WD)
        # for dir_path in self.dir_pathes:
        # print "start Magic read %s " %self.magic_file
        if self.data_model == 3:
            if 'measurements' not in self.contribution.tables:
                print("-W- No meaurements found")
                return ({}, {})
            self.contribution.propagate_location_to_measurements()
            meas_container = self.contribution.tables['measurements']
            meas_data3_0 = meas_container.df
# do some filtering
            Mkeys = ['magn_moment', 'magn_volume', 'magn_mass']
            if meas_data3_0.empty:
                self.user_warning(
                    "Measurement data is empty and GUI cannot start, aborting")
                return ({}, {})
            elif 'method_codes' not in meas_data3_0.columns:
                self.user_warning(
                    "Method codes are required to sort directional and intensity data in measurements file, but no method codes were found, aborting")
                return ({}, {})
            quality_flag = ''
            if 'quality' in meas_data3_0.columns:
                quality_flag = 'quality'
            elif 'flag' in meas_data3_0.columns:
                quality_flag = 'flag'

            if quality_flag:
                # exclude 'bad' measurements
                meas_data3_0 = meas_data3_0[-meas_data3_0[quality_flag].str.contains('b').astype(bool)]
            # fish out all the relavent data
            meas_data3_0 = meas_data3_0[meas_data3_0['method_codes'].str.contains(
                'LP-PI-TRM|LP-TRM|LP-PI-M|LP-AN|LP-CR-TRM') == True]
            intensity_types = [
                col_name for col_name in meas_data3_0.columns if col_name in Mkeys]
            # drop any intensity columns with no data
            intensity_types = meas_data3_0[intensity_types].dropna(
                axis='columns').columns
            # plot first intensity method found - normalized to initial value
            # anyway - doesn't matter which used
            if not len(intensity_types):
                print('-E- No intensity columns found')
                return {}, {}
            int_key = intensity_types[0]
            # get all the non-null intensity records of the same type
            meas_data3_0 = meas_data3_0[meas_data3_0[int_key].notnull()]
            # now convert back to 2.5  changing only those keys that are
            # necessary for thellier_gui

            meas_data2_5 = map_magic.convert_meas_df_thellier_gui(meas_data3_0, output=2)

            # make a list of dictionaries to maintain backward compatibility
            meas_data = meas_data2_5.to_dict("records")
        else:
            try:
                meas_data, file_type = pmag.magic_read(self.magic_file)
            except:
                print("-E- ERROR: Can't read measurement file. ")
                return {}, {}

        # print "done Magic read %s " %self.magic_file

        self.GUI_log.write("-I- Read magic file  %s\n" % self.magic_file)

        # get list of unique specimen names

        CurrRec = []
        # print "get sids"
        sids = pmag.get_specs(meas_data)  # samples ID's
        # print "done get sids"

        # print "initialize blocks"

        for s in sids:
            # initialize some variables
            # for calculating measurement_number for anisotropy
            saved_exp_name = ""
            aarm_num = 0
            # add specimen to Data
            if s not in list(Data.keys()):
                Data[s] = {}
                Data[s]['datablock'] = []
                Data[s]['trmblock'] = []
                Data[s]['zijdblock'] = []
            # zijdblock,units=pmag.find_dmag_rec(s,meas_data)
            # Data[s]['zijdblock']=zijdblock

        # print "done initialize blocks"

        # print "sorting meas data"

        for rec in meas_data:
            s = rec["er_specimen_name"]
            Data[s]['T_or_MW'] = "T"
            sample = rec.get("er_sample_name", '')
            site = rec.get("er_site_name", '')
            rec['er_sample_name'], rec['er_site_name'] = sample, site
            # if "er_site_name" in an empty string: use er_sample_name tp
            # assign site to sample.
            if rec["er_site_name"] == "":
                site = sample
            location = ""
            if "er_location_name" in list(rec.keys()):
                location = rec["er_location_name"]

            if "LP-PI-M" in rec["magic_method_codes"]:
                Data[s]['T_or_MW'] = "MW"
            else:
                Data[s]['T_or_MW'] = "T"

            if "magic_method_codes" not in list(rec.keys()):
                rec["magic_method_codes"] = ""
            # methods=rec["magic_method_codes"].split(":")
            if "LP-PI-TRM" in rec["magic_method_codes"] or "LP-PI-M" in rec["magic_method_codes"]:
                Data[s]['datablock'].append(rec)
                # identify the lab DC field
                if (("LT-PTRM-I" in rec["magic_method_codes"] or "LT-T-I" in rec["magic_method_codes"]) and 'LP-TRM' not in rec["magic_method_codes"])\
                   or "LT-PMRM-I" in rec["magic_method_codes"]:
                    Data[s]['Thellier_dc_field_uT'] = float(
                        rec["treatment_dc_field"])
                    Data[s]['Thellier_dc_field_phi'] = float(
                        rec['treatment_dc_field_phi'])
                    Data[s]['Thellier_dc_field_theta'] = float(
                        rec['treatment_dc_field_theta'])

            if "LP-TRM" in rec["magic_method_codes"]:
                Data[s]['trmblock'].append(rec)

            if "LP-AN-TRM" in rec["magic_method_codes"]:
                if 'atrmblock' not in list(Data[s].keys()):
                    Data[s]['atrmblock'] = []
                Data[s]['atrmblock'].append(rec)

            if "LP-AN-ARM" in rec["magic_method_codes"]:
                # anisotropy calculations require a numeric measurement_number
                # so go ahead and generate that if it is not provided
                exp_name = rec['magic_experiment_name']
                aarm_num += 1
                aarm_rec = rec.copy()
                if saved_exp_name != exp_name:
                    saved_exp_name = exp_name
                    aarm_num = 0
                try:
                    float(rec['measurement_number'])
                except ValueError:
                    aarm_rec['measurement_number'] = aarm_num

                if 'aarmblock' not in list(Data[s].keys()):
                    Data[s]['aarmblock'] = []

                Data[s]['aarmblock'].append(aarm_rec)

            if "LP-CR-TRM" in rec["magic_method_codes"] and rec['measurement_description'] != "":
                if 'crblock' not in list(Data[s].keys()):
                    Data[s]['crblock'] = []
                Data[s]['crblock'].append(rec)

            #---- Zijderveld block

            EX = ["LP-AN-ARM", "LP-AN-TRM", "LP-ARM-AFD", "LP-ARM2-AFD", "LP-TRM-AFD",
                  "LP-TRM", "LP-TRM-TD", "LP-X", "LP-CR-TRM"]  # list of excluded lab protocols
            #INC=["LT-NO","LT-AF-Z","LT-T-Z", "LT-M-Z", "LP-PI-TRM-IZ", "LP-PI-M-IZ"]
            INC = ["LT-NO", "LT-T-Z", "LT-M-Z", "LT-AF-Z"]
            methods = rec["magic_method_codes"].strip('\n').split(":")
            for i in range(len(methods)):
                methods[i] = methods[i].strip()
            if 'measurement_flag' not in list(rec.keys()):
                rec['measurement_flag'] = 'g'
            skip = 1
            for meth in methods:
                if meth in INC:
                    skip = 0
            for meth in EX:
                if meth in methods:
                    skip = 1
            if skip == 0:
                if Data[s]['T_or_MW'] == "T" and 'treatment_temp' in list(rec.keys()):
                    tr = float(rec["treatment_temp"])
                elif Data[s]['T_or_MW'] == "MW" and "measurement_description" in list(rec.keys()):
                    MW_step = rec["measurement_description"].strip(
                        '\n').split(":")
                    for STEP in MW_step:
                        if "Number" in STEP:
                            tr = float(STEP.split("-")[-1])

                # looking for in-field first thellier or microwave data -
                # otherwise, just ignore this
                if "LP-PI-TRM-IZ" in methods or "LP-PI-M-IZ" in methods:
                    ZI = 0
                else:
                    ZI = 1

                Mkeys = ['measurement_magnitude', 'measurement_magn_moment',
                         'measurement_magn_volume', 'measurement_magn_mass']
                if tr != "":
                    dec, inc, int = "", "", ""
                    if "measurement_dec" in list(rec.keys()) and rec["measurement_dec"] != "":
                        dec = float(rec["measurement_dec"])
                    if "measurement_inc" in list(rec.keys()) and rec["measurement_inc"] != "":
                        inc = float(rec["measurement_inc"])
                    for key in Mkeys:
                        if key in list(rec.keys()) and rec[key] != "" and rec[key] is not None:
                            int = float(rec[key])
                    if 'magic_instrument_codes' not in list(rec.keys()):
                        rec['magic_instrument_codes'] = ''
                    # datablock.append([tr,dec,inc,int,ZI,rec['measurement_flag'],rec['magic_instrument_codes']])
                    if Data[s]['T_or_MW'] == "T":
                        if tr == 0.:
                            tr = 273.
                    # AFD
                    if "LT-AF-Z" in methods and "LP-AN-ARM" not in rec['magic_method_codes'] and "LP-DIR-AF" not in rec['magic_method_codes']:
                        if Data[s]['T_or_MW'] == "T":
                            if 'treatment_ac_field' not in rec:
                                rec['treatment_ac_field'] = ''
                            try:
                                # AFD is amrked with negative
                                tr = tr - \
                                    float(rec['treatment_ac_field']) * 1e3
                            except ValueError:
                                print(("could not convert ac treatment field intensity to a floating point number, was given %s, this entry for specimen %s will be skipped" % (
                                    str(rec['treatment_ac_field']), s)))
                                continue

                    Data[s]['zijdblock'].append(
                        [tr, dec, inc, int, ZI, rec['measurement_flag'], rec['magic_instrument_codes']])
                    # print methods

            if sample not in list(Data_hierarchy['samples'].keys()):
                Data_hierarchy['samples'][sample] = []

            if site not in list(Data_hierarchy['sites'].keys()):
                Data_hierarchy['sites'][site] = []

            if location not in list(Data_hierarchy['locations'].keys()):
                Data_hierarchy['locations'][location] = []

            if s not in Data_hierarchy['samples'][sample]:
                Data_hierarchy['samples'][sample].append(s)

            if sample not in Data_hierarchy['sites'][site]:
                Data_hierarchy['sites'][site].append(sample)

            if site not in Data_hierarchy['locations'][location]:
                Data_hierarchy['locations'][location].append(site)

            Data_hierarchy['specimens'][s] = sample
            Data_hierarchy['sample_of_specimen'][s] = sample
            Data_hierarchy['site_of_specimen'][s] = site
            Data_hierarchy['site_of_sample'][sample] = site
        # print Data_hierarchy['site_of_sample']

        # print "done sorting meas data"
        self.specimens = list(Data.keys())
        self.specimens.sort()

        #------------------------------------------------
        # Read anisotropy file from rmag_anisotropy.txt (only data model 2.5) -data_model 3.0 reads from specimen table
        #------------------------------------------------
        if self.data_model == 3:
            #
            # make a specimen container and dataframe for anisotropy and elsewhere specimen interpretations
            #
            if 'specimens' in self.contribution.tables and len(self.spec_data) > 0 and 'method_codes' in self.spec_data.columns and 'aniso_s' in self.spec_data.columns:
                anis_data = self.spec_data[self.spec_data['method_codes'].str.contains(
                    'LP-AN') == True]  # get the anisotropy records
                # get the ones with anisotropy tensors that aren't blank
                anis_data = anis_data[anis_data['aniso_s'].notnull()]
                anis_cols = ['specimen', 'aniso_s', 'aniso_ftest',
                             'aniso_ftest12', 'aniso_s_n_measurements',
                             'aniso_s_sigma', 'aniso_type', 'description']
                missing_anis_cols = set(anis_cols).difference(anis_data.columns)
                if any(missing_anis_cols):
                    print('-W- Incomplete anisotropy data found, missing the following columns: {}'.format(', '.join(missing_anis_cols)))
                    print('    Ignoring anisotropy data')
                    anis_data = []
                else:
                    print('-I- Using anisotropy data')
                    if 'aniso_alt' in anis_data.columns:
                        anis_cols.append('aniso_alt')
                    anis_data = anis_data[anis_cols]
                    # rename column headers to 2.5
                    #anis_data = anis_data.rename(columns=map_magic.aniso_magic3_2_magic2_map)
                    # convert to list of dictionaries
                    anis_dict = anis_data.to_dict("records")
                    for AniSpec in anis_dict:  # slip aniso data into Data[s]
                        AniSpec = map_magic.convert_aniso(
                            'magic2', AniSpec)  # unpack aniso_s
                        s = AniSpec['er_specimen_name']
                        if 'aniso_alt' in list(AniSpec.keys()) and type(AniSpec['aniso_alt']) == float:
                            AniSpec['anisotropy_alt'] = AniSpec['aniso_alt']
                        elif 'aniso_alt' in list(AniSpec.keys()) and type(AniSpec['aniso_alt']) != float:
                            AniSpec['anisotropy_alt'] = ""

                        if 'AniSpec' not in list(Data[s].keys()):
                            Data[s]['AniSpec'] = {}  # make a blank
                        TYPE = AniSpec['anisotropy_type']
                        Data[s]['AniSpec'][TYPE] = AniSpec
                        if AniSpec['anisotropy_F_crit'] != "":
                            Data[s]['AniSpec'][TYPE]['anisotropy_F_crit'] = AniSpec['anisotropy_F_crit']
        else:  # do data_model=2.5 way...
            rmag_anis_data = []
            results_anis_data = []
            try:
                rmag_anis_data, file_type = pmag.magic_read(
                    os.path.join(self.WD, 'rmag_anisotropy.txt'))
                self.GUI_log.write(
                    "-I- Anisotropy data read  %s/from rmag_anisotropy.txt\n" % self.WD)
            except:
                self.GUI_log.write(
                    "-W- WARNING can't find rmag_anisotropy in working directory\n")

            try:
                results_anis_data, file_type = pmag.magic_read(
                    os.path.join(self.WD, 'rmag_results.txt'))
                self.GUI_log.write(
                    "-I- Anisotropy data read  %s/from rmag_anisotropy.txt\n" % self.WD)

            except:
                self.GUI_log.write(
                    "-W- WARNING can't find rmag_anisotropy in working directory\n")

            for AniSpec in rmag_anis_data:
                s = AniSpec['er_specimen_name']
                if s not in list(Data.keys()):
                    self.GUI_log.write(
                        "-W- WARNING: specimen %s in rmag_anisotropy.txt but not in magic_measurement.txt. Check it !\n" % s)
                    continue
                if 'AniSpec' in list(Data[s].keys()):
                    self.GUI_log.write(
                        "-W- WARNING: more than one anisotropy data for specimen %s !\n" % s)
                TYPE = AniSpec['anisotropy_type']
                if 'AniSpec' not in list(Data[s].keys()):
                    Data[s]['AniSpec'] = {}
                Data[s]['AniSpec'][TYPE] = AniSpec

            for AniSpec in results_anis_data:
                s = AniSpec['er_specimen_names']
                if s not in list(Data.keys()):
                    self.GUI_log.write(
                        "-W- WARNING: specimen %s in rmag_results.txt but not in magic_measurement.txt. Check it !\n" % s)
                    continue
                TYPE = AniSpec['anisotropy_type']
                if 'AniSpec' in list(Data[s].keys()) and TYPE in list(Data[s]['AniSpec'].keys()):
                    Data[s]['AniSpec'][TYPE].update(AniSpec)
                    if 'result_description' in list(AniSpec.keys()):
                        result_description = AniSpec['result_description'].split(
                            ";")
                        for description in result_description:
                            if "Critical F" in description:
                                desc = description.split(":")
                                Data[s]['AniSpec'][TYPE]['anisotropy_F_crit'] = float(
                                    desc[1])

        #------------------------------------------------
        # Calculate Non Linear TRM parameters
        # Following Shaar et al. (2010):
        #
        # Procedure:
        #
        # A) If there are only 2 NLT measurement: C
        #
        #   Can't do NLT correctio procedure (few data points).
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
        #   Banc= tanh^-1[(b*Fa)/alpha]/beta where Fa  is anisotropy correction factor and 'b' is the Arai plot slope.
        #
        # 3) If best fit function algorithm does not converge, check NLT data using option (A) above.
        #    If
        #
        #------------------------------------------------

        # Searching and sorting NLT Data

        for s in sids:
            datablock = Data[s]['datablock']
            trmblock = Data[s]['trmblock']

            if len(trmblock) < 2:
                continue

            B_NLT, M_NLT = [], []

            # find temperature of NLT acquisition
            NLT_temperature = float(trmblock[0]['treatment_temp'])

            # search for Blab used in the IZZI experiment (need it for the
            # following calculation)
            found_labfield = False
            for rec in datablock:
                if float(rec['treatment_dc_field']) != 0:
                    labfield = float(rec['treatment_dc_field'])
                    found_labfield = True
                    break
            if not found_labfield:
                continue

            # collect the data from trmblock
            M_baseline = 0.
            for rec in trmblock:

                # if there is a baseline in TRM block, then use it
                if float(rec['treatment_dc_field']) == 0:
                    M_baseline = float(rec['measurement_magn_moment'])
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
            if M_baseline == 0:
                m_tmp = []
                for rec in datablock:
                    if float(rec['treatment_temp']) == NLT_temperature and float(rec['treatment_dc_field']) == 0:
                        m_tmp.append(float(rec['measurement_magn_moment']))
                        self.GUI_log.write(
                            "-I- Found baseline for NLT measurements in datablock, specimen %s\n" % s)
                if len(m_tmp) > 0:
                    M_baseline = np.mean(m_tmp)

            # Ron dont delete it ### print "-I- Found %i NLT datapoints for
            # specimen %s: B="%(len(B_NLT),s),array(B_NLT)*1e6

            # substitute baseline
            M_NLT = np.array(M_NLT) - M_baseline
            B_NLT = np.array(B_NLT)
            # calculate M/B ratio for each step, and compare them
            # If can't do NLT correction: check a difference in M/B ratio
            # > 5% : WARNING
            # > 10%: ERROR

            slopes = M_NLT / B_NLT

            if len(trmblock) == 2:
                if max(slopes) / min(slopes) < 1.05:
                    self.GUI_log.write(
                        "-I- 2 NLT measurement for specimen %s. [max(M/B)/ [min(M/B)] < 1.05.\n" % s)
                elif max(slopes) / min(slopes) < 1.1:
                    self.GUI_log.write(
                        "-W- WARNING: 2 NLT measurement for specimen %s. [max(M/B)]/ [min(M/B)] is %.2f  (   > 1.05 and  < 1.1 ). More NLT mrasurements may be required.\n" % (s, max(slopes) / min(slopes)))
                    #self.GUI_log.write("-I- NLT meaurements specime %s: B,M="%s,B_NLT,M_NLT)
                else:
                    self.GUI_log.write(
                        "-E- ERROR: 2 NLT measurement for specimen %s. [max(M/B)]/ [min(M/B)] is %.2f  ( > 1.1 ). More NLT mrasurements may be required  !\n" % (s, max(slopes) / min(slopes)))
                    #self.GUI_log.write("-I- NLT meaurements specime %s: B,M="%s,B_NLT,M_NLT)

            # NLT procedure following Shaar et al (2010)

            if len(trmblock) > 2:
                red_flag = False

                # check alteration
                B_alterations = []
                for i in range(len(B_NLT)):
                    if list(B_NLT).count(B_NLT[i]) > 1:
                        if B_NLT[i] not in B_alterations:
                            B_alterations.append(B_NLT[i])
                for B in B_alterations:
                    M = []
                    for i in range(len(B_NLT)):
                        if B_NLT[i] == B:
                            M.append(M_NLT[i])
                    if (max(M) - min(M)) / np.mean(M) > 0.05:
                        self.GUI_log.write(
                            "-E- ERROR: NLT for specimen %s does not pass 5 perc alteration check: %.3f \n" % (s, (max(M) - min(M)) / np.mean(M)))
                        red_flag = True

            if len(trmblock) > 2 and not red_flag:

                B_NLT = append([0.], B_NLT)
                M_NLT = append([0.], M_NLT)

                try:
                    # print s,B_NLT, M_NLT
                    # First try to fit tanh function (add point 0,0 in the
                    # begining)
                    alpha_0 = max(M_NLT)
                    beta_0 = 2e4
                    popt, pcov = curve_fit(
                        tan_h, B_NLT, M_NLT, p0=(alpha_0, beta_0))
                    M_lab = popt[0] * np.math.tanh(labfield * popt[1])

                    # Now  fit tanh function to the normalized curve
                    M_NLT_norm = M_NLT / M_lab
                    popt, pcov = curve_fit(
                        tan_h, B_NLT, M_NLT_norm, p0=(popt[0] / M_lab, popt[1]))
                    Data[s]['NLT_parameters'] = {}
                    Data[s]['NLT_parameters']['tanh_parameters'] = (popt, pcov)
                    Data[s]['NLT_parameters']['B_NLT'] = B_NLT
                    Data[s]['NLT_parameters']['M_NLT_norm'] = M_NLT_norm

                    self.GUI_log.write(
                        "-I-  tanh parameters for specimen %s were calculated successfully\n" % s)

                except RuntimeError:
                    self.GUI_log.write(
                        "-W- WARNING: Can't fit tanh function to NLT data specimen %s. Ignore NLT data for specimen %s. Instead check [max(M/B)]/ [min(M/B)] \n" % (s, s))
                    # print "-I- NLT meaurements specime %s:
                    # B,M="%s,B_NLT,M_NLT

                    # Can't do NLT correction. Instead, check a difference in M/B ratio
                    # The maximum difference allowd is 5%
                    # if difference is larger than 5%: WARNING

                    if max(slopes) / min(slopes) < 1.05:
                        self.GUI_log.write(
                            "-I- 2 NLT measurement for specimen %s. [max(M/B)/ [min(M/B)] < 1.05.\n" % s)
                    elif max(slopes) / min(slopes) < 1.1:
                        self.GUI_log.write(
                            "-W- WARNING: 2 NLT measurement for specimen %s. [max(M/B)]/ [min(M/B)] is %.2f  (   > 1.05 and  < 1.1 ). More NLT mrasurements may be required.\n" % (s, max(slopes) / min(slopes)))
                        # print "-I- NLT meaurements specime %s:
                        # B,M="%s,B_NLT,M_NLT
                    else:
                        self.GUI_log.write(
                            "-E- ERROR: 2 NLT measurement for specimen %s. [max(M/B)]/ [min(M/B)] is %.2f  ( > 1.1 ). More NLT measurements may be required  !\n" % (s, max(slopes) / min(slopes)))
                        # print "-I- NLT meaurements specime %s:
                        # B,M="%s,B_NLT,M_NLT

        # print "done searching NLT data"

        self.GUI_log.write(
            "-I- Done calculating non linear TRM parameters for all specimens\n")

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
            if 'crblock' in list(Data[s].keys()):
                if len(Data[s]['crblock']) < 3:
                    del Data[s]['crblock']
                    continue
                sample = Data_hierarchy['specimens'][s]
                # in MagIC format that cooling rate is in K/My
                try:
                    ancient_cooling_rate = float(
                        self.Data_info["er_samples"][sample]['sample_cooling_rate'])
                    ancient_cooling_rate = ancient_cooling_rate / \
                        (1e6 * 365. * 24. * 60.)  # change to K/minute
                except:
                    self.GUI_log.write(
                        "-W- Can't find ancient cooling rate estimation for sample %s\n" % sample)
                    continue
                # self.Data_info["er_samples"]
                cooling_rate_data = {}
                cooling_rate_data['pairs'] = []
                cooling_rates_list = []
                cooling_rate_data['alteration_check'] = []
                for rec in Data[s]['crblock']:
                    magic_method_codes = rec['magic_method_codes'].strip(
                        ' ').strip('\n').split(":")
                    try:
                        measurement_description = rec['measurement_description'].strip(
                            ' ').strip('\n').split(":")
                        index = measurement_description.index("K/min")
                        cooling_rate = float(
                            measurement_description[index - 1])
                        cooling_rates_list.append(cooling_rate)
                    except:
                        measurement_description = []
                    if "LT-T-Z" in magic_method_codes:
                        cooling_rate_data['baseline'] = float(
                            rec['measurement_magn_moment'])
                        continue
                    moment = float(rec['measurement_magn_moment'])
                    if "LT-T-I" in magic_method_codes:
                        cooling_rate_data['pairs'].append(
                            [cooling_rate, moment])
                    if "LT-PTRM-I" in magic_method_codes:
                        cooling_rate_data['alteration_check'] = [
                            cooling_rate, moment]
                lab_cooling_rate = max(cooling_rates_list)
                cooling_rate_data['lab_cooling_rate'] = lab_cooling_rate
                #lab_cooling_rate = self.Data[self.s]['cooling_rate_data']['lab_cooling_rate']
                moments = []
                lab_fast_cr_moments = []
                lan_cooling_rates = []
                for pair in cooling_rate_data['pairs']:
                    lan_cooling_rates.append(np.math.log(
                        cooling_rate_data['lab_cooling_rate'] / pair[0]))
                    moments.append(pair[1])
                    if pair[0] == cooling_rate_data['lab_cooling_rate']:
                        lab_fast_cr_moments.append(pair[1])
                # print s, cooling_rate_data['alteration_check']
                lan_cooling_rates.append(np.math.log(
                    cooling_rate_data['lab_cooling_rate'] / cooling_rate_data['alteration_check'][0]))
                lab_fast_cr_moments.append(
                    cooling_rate_data['alteration_check'][1])
                moments.append(cooling_rate_data['alteration_check'][1])

                lab_fast_cr_moment = np.mean(lab_fast_cr_moments)
                moment_norm = np.array(moments) / lab_fast_cr_moment
                (a, b) = np.polyfit(lan_cooling_rates, moment_norm, 1)
                # ancient_cooling_rate=0.41
                x0 = np.math.log(
                    cooling_rate_data['lab_cooling_rate'] / ancient_cooling_rate)
                y0 = a * x0 + b
                MAX = max(lab_fast_cr_moments)
                MIN = min(lab_fast_cr_moments)

                if np.mean([MAX, MIN]) == 0:
                    alteration_check_perc = 0
                else:
                    alteration_check_perc = 100 * \
                        abs((MAX - MIN) / np.mean([MAX, MIN]))
                cooling_rate_data['ancient_cooling_rate'] = ancient_cooling_rate
                cooling_rate_data['CR_correction_factor'] = -999
                cooling_rate_data['lan_cooling_rates'] = lan_cooling_rates
                cooling_rate_data['moment_norm'] = moment_norm
                cooling_rate_data['polyfit'] = [a, b]
                cooling_rate_data['CR_correction_factor_flag'] = ""
                cooling_rate_data['x0'] = x0

                if alteration_check_perc > 5:
                    cooling_rate_data['CR_correction_factor_flag'] = cooling_rate_data['CR_correction_factor_flag'] + "alteration > 5% "
                    cooling_rate_data['CR_correction_factor'] = -999
                # if y0>1 and alteration_check_perc<=5:
                if alteration_check_perc <= 5:
                    cooling_rate_data['CR_correction_factor_flag'] = "calculated"
                    cooling_rate_data['CR_correction_factor'] = 1. / (y0)
                Data[s]['cooling_rate_data'] = cooling_rate_data

        # go over all specimens. if there is a specimen with no cooling rate data
        # use the mean cooling rate corretion of the other specimens from the same sample
        # this cooling rate correction is flagges as "inferred"

        for sample in list(Data_hierarchy['samples'].keys()):
            CR_corrections = []
            for s in Data_hierarchy['samples'][sample]:
                if 'cooling_rate_data' in list(Data[s].keys()):
                    if 'CR_correction_factor' in list(Data[s]['cooling_rate_data'].keys()):
                        if 'CR_correction_factor_flag' in list(Data[s]['cooling_rate_data'].keys()):
                            if Data[s]['cooling_rate_data']['CR_correction_factor_flag'] == 'calculated':
                                CR_corrections.append(
                                    Data[s]['cooling_rate_data']['CR_correction_factor'])
            if len(CR_corrections) > 0:
                mean_CR_correction = np.mean(CR_corrections)
            else:
                mean_CR_correction = -1
            if mean_CR_correction != -1:
                for s in Data_hierarchy['samples'][sample]:
                    if 'cooling_rate_data' not in list(Data[s].keys()):
                        Data[s]['cooling_rate_data'] = {}
                    if 'CR_correction_factor' not in list(Data[s]['cooling_rate_data'].keys()) or\
                       Data[s]['cooling_rate_data']['CR_correction_factor_flag'] != "calculated":
                        Data[s]['cooling_rate_data']['CR_correction_factor'] = mean_CR_correction
                        if 'CR_correction_factor_flag' in list(Data[s]['cooling_rate_data'].keys()):
                            Data[s]['cooling_rate_data']['CR_correction_factor_flag'] = Data[s][
                                'cooling_rate_data']['CR_correction_factor_flag'] + ":" + "inferred"
                        else:
                            Data[s]['cooling_rate_data']['CR_correction_factor_flag'] = "inferred"

        #------------------------------------------------
        # sort Arai block
        #------------------------------------------------

        # print "sort blocks to arai, zij. etc."

        for s in self.specimens:
            # collected the data
            datablock = Data[s]['datablock']

            if len(datablock) < 4:
                self.GUI_log.write(
                    "-E- ERROR: skipping specimen %s, not enough measurements - moving forward \n" % s)
                del Data[s]
                try:
                    sample = Data_hierarchy['specimens'][s]
                    del Data_hierarchy['specimens'][s]
                    Data_hierarchy['samples'][sample].remove(s)
                except KeyError:
                    pass
                continue

            araiblock, field = self.sortarai(datablock, s, 0)

            # thermal or microwave
            rec = datablock[0]
            if "treatment_temp" in list(rec.keys()) and rec["treatment_temp"] != "":
                temp = float(rec["treatment_temp"])
                THERMAL = True
                MICROWAVE = False
            elif "treatment_mw_power" in list(rec.keys()) and rec["treatment_mw_power"] != "":
                THERMAL = False
                MICROWAVE = True

            # Fix zijderveld block for Thellier-Thellier protocol (II)
            # (take the vector subtruction instead of the zerofield steps)

            if "LP-PI-II" in Data[s]['datablock'][0]["magic_method_codes"] or "LP-PI-M-II" in Data[s]['datablock'][0]["magic_method_codes"] or "LP-PI-T-II" in Data[s]['datablock'][0]["magic_method_codes"]:
                Data[s]['zijdblock'] = []
                for zerofield in araiblock[0]:
                    Data[s]['zijdblock'].append(
                        [zerofield[0], zerofield[1], zerofield[2], zerofield[3], 0, 'g', ""])

            zijdblock = Data[s]['zijdblock']

            Data[s]['araiblock'] = araiblock
            Data[s]['pars'] = {}
            Data[s]['pars']['lab_dc_field'] = field
            Data[s]['pars']['er_specimen_name'] = s
            Data[s]['pars']['er_sample_name'] = Data_hierarchy['specimens'][s]

            Data[s]['lab_dc_field'] = field
            Data[s]['er_specimen_name'] = s
            Data[s]['er_sample_name'] = Data_hierarchy['specimens'][s]

            first_Z = araiblock[0]
            # if len(first_Z)<3:
            # continue

            if len(araiblock[0]) != len(araiblock[1]):
                self.GUI_log.write(
                    "-E- ERROR: unequal length of Z steps and I steps. Check specimen %s" % s)
                # continue

        # Fix zijderveld block for Thellier-Thellier protocol (II)
        # (take the vector subtruiction instead of the zerofield steps)
        # araiblock,field=self.sortarai(Data[s]['datablock'],s,0)
        # if "LP-PI-II" in Data[s]['datablock'][0]["magic_method_codes"] or "LP-PI-M-II" in Data[s]['datablock'][0]["magic_method_codes"] or "LP-PI-T-II" in Data[s]['datablock'][0]["magic_method_codes"]:
        #    for zerofield in araiblock[0]:
        #        Data[s]['zijdblock'].append([zerofield[0],zerofield[1],zerofield[2],zerofield[3],0,'g',""])
# if "LP-PI-II" in datablock[0]["magic_method_codes"] or "LP-PI-M-II" in datablock[0]["magic_method_codes"] or "LP-PI-T-II" in datablock[0]["magic_method_codes"]:
# for zerofield in araiblock[0]:
# Data[s]['zijdblock'].append([zerofield[0],zerofield[1],zerofield[2],zerofield[3],0,'g',""])

            #--------------------------------------------------------------
            # collect all zijderveld data to array and calculate VDS
            #--------------------------------------------------------------

            z_temperatures = [row[0] for row in zijdblock]
            zdata = []
            vector_diffs = []

            # if AFD before the Thellier Experiment: ignore the AF steps in NRM calculation
            # for i in range(len(zijdblock)):
            # if "AFD" not in str(zijdblock[i][0]):
            NRM = zijdblock[0][3]
            for k in range(len(zijdblock)):
                DIR = [zijdblock[k][1], zijdblock[k][2], zijdblock[k][3] / NRM]
                cart = pmag.dir2cart(DIR)
                zdata.append(np.array([cart[0], cart[1], cart[2]]))
                if k > 0:
                    vector_diffs.append(
                        np.sqrt(sum((np.array(zdata[-2]) - np.array(zdata[-1]))**2)))
            # last vector of the vds
            vector_diffs.append(np.sqrt(sum(np.array(zdata[-1])**2)))
            vds = sum(vector_diffs)  # vds calculation
            zdata = np.array(zdata)

            Data[s]['vector_diffs'] = np.array(vector_diffs)
            Data[s]['vds'] = vds
            Data[s]['zdata'] = zdata
            Data[s]['z_temp'] = z_temperatures
            Data[s]['NRM'] = NRM

        #--------------------------------------------------------------
        # Rotate zijderveld plot
        #--------------------------------------------------------------

            DIR_rot = []
            CART_rot = []
            # rotate to be as NRM
            NRM_dir = pmag.cart2dir(Data[s]['zdata'][0])

            NRM_dec = NRM_dir[0]
            NRM_dir[0] = 0
            CART_rot.append(pmag.dir2cart(NRM_dir))

            for i in range(1, len(Data[s]['zdata'])):
                DIR = pmag.cart2dir(Data[s]['zdata'][i])
                DIR[0] = DIR[0] - NRM_dec
                CART_rot.append(np.array(pmag.dir2cart(DIR)))
                # print array(dir2cart(DIR))

            CART_rot = np.array(CART_rot)
            Data[s]['zij_rotated'] = CART_rot
            #--------------------------------------------------------------
            # collect all Arai plot data points to array
            #--------------------------------------------------------------

            # collect Arai data points
            zerofields, infields = araiblock[0], araiblock[1]

            Data[s]['NRMS'] = zerofields
            Data[s]['PTRMS'] = infields

            x_Arai, y_Arai = [], []  # all the data points
            t_Arai = []
            steps_Arai = []

            # NRM=zerofields[0][3]
            infield_temperatures = [row[0] for row in infields]

            for k in range(len(zerofields)):
                index_infield = infield_temperatures.index(zerofields[k][0])
                x_Arai.append(infields[index_infield][3] / NRM)
                y_Arai.append(zerofields[k][3] / NRM)
                t_Arai.append(zerofields[k][0])
                if zerofields[k][4] == 1:
                    steps_Arai.append('ZI')
                else:
                    steps_Arai.append('IZ')
            x_Arai = np.array(x_Arai)
            y_Arai = np.array(y_Arai)
            # else:
            #    Data[s]['pars']['magic_method_codes']=""
            Data[s]['x_Arai'] = x_Arai
            Data[s]['y_Arai'] = y_Arai
            Data[s]['t_Arai'] = t_Arai
            Data[s]['steps_Arai'] = steps_Arai

            #--------------------------------------------------------------
            # collect all pTRM check to array
            #--------------------------------------------------------------

            ptrm_checks = araiblock[2]
            zerofield_temperatures = [row[0] for row in zerofields]

            x_ptrm_check, y_ptrm_check, ptrm_checks_temperatures, = [], [], []
            x_ptrm_check_starting_point, y_ptrm_check_starting_point, ptrm_checks_starting_temperatures = [], [], []
            for k in range(len(ptrm_checks)):
                if ptrm_checks[k][0] in zerofield_temperatures:
                    zero_field_index = ptrm_checks[k][4]
                    # print Data[s]['datablock']

                    # find the starting point of the pTRM check:
                    rec = Data[s]['datablock'][zero_field_index]
                    if THERMAL:
                        starting_temperature = (float(rec['treatment_temp']))
                        # found_start_temp=True
                    elif MICROWAVE:
                        MW_step = rec["measurement_description"].strip(
                            '\n').split(":")
                        for STEP in MW_step:
                            if "Number" in STEP:
                                starting_temperature = float(
                                    STEP.split("-")[-1])
                                # found_start_temp=True

                    # if MICROWAVE:
                    #  if "measurement_description" in rec.keys():
                    #      MW_step=rec["measurement_description"].strip('\n').split(":")
                    #      for STEP in MW_step:
                    #          if "Number" in STEP:
                    #              this_temp=float(STEP.split("-")[-1])
                    # if found_start_temp==False:
                    #      continue
                    try:
                        # if True:
                        index = t_Arai.index(starting_temperature)
                        x_ptrm_check_starting_point.append(x_Arai[index])
                        y_ptrm_check_starting_point.append(y_Arai[index])
                        ptrm_checks_starting_temperatures.append(
                            starting_temperature)

                        # print ptrm_checks[k]
                        # print ' ptrm_checks[k][4]', ptrm_checks[k][4]
                        if ptrm_checks[k][5] == 0:
                            index_zerofield = zerofield_temperatures.index(
                                ptrm_checks[k][0])
                            index_infield = infield_temperatures.index(
                                ptrm_checks[k][0])
                            infield_cart = dir2cart(
                                [infields[index_infield][1], infields[index_infield][2], infields[index_infield][3]])
                            ptrm_check_cart = dir2cart(
                                [ptrm_checks[k][1], ptrm_checks[k][2], ptrm_checks[k][3]])
                            ptrm_check = cart2dir(
                                np.array(infield_cart) - np.array(ptrm_check_cart))
                            x_ptrm_check.append(ptrm_check[2] / NRM)
                            y_ptrm_check.append(
                                zerofields[index_zerofield][3] / NRM)
                            ptrm_checks_temperatures.append(ptrm_checks[k][0])
                        else:
                            index_zerofield = zerofield_temperatures.index(
                                ptrm_checks[k][0])
                            x_ptrm_check.append(ptrm_checks[k][3] / NRM)
                            y_ptrm_check.append(
                                zerofields[index_zerofield][3] / NRM)
                            ptrm_checks_temperatures.append(ptrm_checks[k][0])
                    # else:
                    except:
                        pass

            x_ptrm_check = np.array(x_ptrm_check)
            ptrm_check = np.array(y_ptrm_check)
            ptrm_checks_temperatures = np.array(ptrm_checks_temperatures)
            Data[s]['PTRM_Checks'] = ptrm_checks
            Data[s]['x_ptrm_check'] = x_ptrm_check
            Data[s]['y_ptrm_check'] = y_ptrm_check
            Data[s]['ptrm_checks_temperatures'] = ptrm_checks_temperatures
            Data[s]['x_ptrm_check_starting_point'] = np.array(
                x_ptrm_check_starting_point)
            Data[s]['y_ptrm_check_starting_point'] = np.array(
                y_ptrm_check_starting_point)
            Data[s]['ptrm_checks_starting_temperatures'] = np.array(
                ptrm_checks_starting_temperatures)
# if len(ptrm_checks_starting_temperatures) != len(ptrm_checks_temperatures):
# print s
# print Data[s]['ptrm_checks_temperatures']
# print Data[s]['ptrm_checks_starting_temperatures']
# print "help"

            #--------------------------------------------------------------
            # collect tail checks
            #--------------------------------------------------------------

            ptrm_tail = araiblock[3]
            # print s
            # print ptrm_tail
            # print "-----"
            x_tail_check, y_tail_check, tail_check_temperatures = [], [], []
            x_tail_check_starting_point, y_tail_check_starting_point, tail_checks_starting_temperatures = [], [], []

            for k in range(len(ptrm_tail)):
                # if float(ptrm_tail[k][0]) in zerofield_temperatures:

                    # find the starting point of the pTRM check:
                for i in range(len(datablock)):
                    rec = datablock[i]
                    if (THERMAL and "LT-PTRM-MD" in rec['magic_method_codes'] and float(rec['treatment_temp']) == ptrm_tail[k][0])\
                       or\
                       (MICROWAVE and "LT-PMRM-MD" in rec['magic_method_codes'] and "measurement_description" in list(rec.keys()) and "Step Number-%.0f" % float(ptrm_tail[k][0]) in rec["measurement_description"]):
                        if THERMAL:
                            starting_temperature = (
                                float(datablock[i - 1]['treatment_temp']))
                        elif MICROWAVE:
                            MW_step = datablock[i -
                                                1]["measurement_description"].strip('\n').split(":")
                            for STEP in MW_step:
                                if "Number" in STEP:
                                    starting_temperature = float(
                                        STEP.split("-")[-1])

                        try:

                            index = t_Arai.index(starting_temperature)
                            x_tail_check_starting_point.append(x_Arai[index])
                            y_tail_check_starting_point.append(y_Arai[index])
                            tail_checks_starting_temperatures.append(
                                starting_temperature)

                            index_infield = infield_temperatures.index(
                                ptrm_tail[k][0])
                            x_tail_check.append(
                                infields[index_infield][3] / NRM)
                            y_tail_check.append(
                                ptrm_tail[k][3] / NRM + zerofields[index_infield][3] / NRM)
                            tail_check_temperatures.append(ptrm_tail[k][0])

                            break
                        except:
                            pass

            x_tail_check = np.array(x_tail_check)
            y_tail_check = np.array(y_tail_check)
            tail_check_temperatures = np.array(tail_check_temperatures)
            x_tail_check_starting_point = np.array(x_tail_check_starting_point)
            y_tail_check_starting_point = np.array(y_tail_check_starting_point)
            tail_checks_starting_temperatures = np.array(
                tail_checks_starting_temperatures)

            Data[s]['TAIL_Checks'] = ptrm_tail
            Data[s]['x_tail_check'] = x_tail_check
            Data[s]['y_tail_check'] = y_tail_check
            Data[s]['tail_check_temperatures'] = tail_check_temperatures
            Data[s]['x_tail_check_starting_point'] = x_tail_check_starting_point
            Data[s]['y_tail_check_starting_point'] = y_tail_check_starting_point
            Data[s]['tail_checks_starting_temperatures'] = tail_checks_starting_temperatures

            #--------------------------------------------------------------
            # collect additivity checks
            #--------------------------------------------------------------

            additivity_checks = araiblock[6]
            x_AC, y_AC, AC_temperatures, AC = [], [], [], []
            x_AC_starting_point, y_AC_starting_point, AC_starting_temperatures = [], [], []

            tmp_data_block = list(copy.copy(datablock))
            # print "specimen:",s
            for k in range(len(additivity_checks)):
                if additivity_checks[k][0] in zerofield_temperatures:
                    for i in range(len(tmp_data_block)):
                        rec = tmp_data_block[i]
                        if "LT-PTRM-AC" in rec['magic_method_codes'] and float(rec['treatment_temp']) == additivity_checks[k][0]:
                            del(tmp_data_block[i])
                            break

                    # find the infield step that comes before the additivity
                    # check
                    foundit = False
                    for j in range(i - 1, 1, -1):
                        if "LT-T-I" in tmp_data_block[j]['magic_method_codes']:
                            found_starting_temperature = True
                            starting_temperature = float(
                                tmp_data_block[j]['treatment_temp'])
                            break
                    # for j in range(len(Data[s]['t_Arai'])):
                    #    print Data[s]['t_Arai'][j]
                    #    if float(Data[s]['t_Arai'][j])==additivity_checks[k][0]:
                    #      found_zerofield_step=True
                    #      pTRM=Data[s]['x_Arai'][j]
                    #      AC=Data[s]['x_Arai'][j]-additivity_checks[k][3]/NRM
                    #      break
                    if found_starting_temperature:
                        try:
                            index = t_Arai.index(starting_temperature)
                            x_AC_starting_point.append(x_Arai[index])
                            y_AC_starting_point.append(y_Arai[index])
                            AC_starting_temperatures.append(
                                starting_temperature)

                            index_zerofield = zerofield_temperatures.index(
                                additivity_checks[k][0])
                            x_AC.append(additivity_checks[k][3] / NRM)
                            y_AC.append(zerofields[index_zerofield][3] / NRM)
                            AC_temperatures.append(additivity_checks[k][0])
                            index_pTRMs = t_Arai.index(additivity_checks[k][0])
                            AC.append(
                                additivity_checks[k][3] / NRM - x_Arai[index_pTRMs])
                        except:
                            pass

            x_AC = np.array(x_AC)
            y_AC = np.array(y_AC)
            AC_temperatures = np.array(AC_temperatures)
            x_AC_starting_point = np.array(x_AC_starting_point)
            y_AC_starting_point = np.array(y_AC_starting_point)
            AC_starting_temperatures = np.array(AC_starting_temperatures)
            AC = np.array(AC)

            Data[s]['AC'] = AC

            Data[s]['x_additivity_check'] = x_AC
            Data[s]['y_additivity_check'] = y_AC
            Data[s]['additivity_check_temperatures'] = AC_temperatures
            Data[s]['x_additivity_check_starting_point'] = x_AC_starting_point
            Data[s]['y_additivity_check_starting_point'] = y_AC_starting_point
            Data[s]['additivity_check_starting_temperatures'] = AC_starting_temperatures

        self.GUI_log.write(
            "-I- number of specimens in this project directory: %i\n" % len(self.specimens))
        self.GUI_log.write("-I- number of samples in this project directory: %i\n" %
                           len(list(Data_hierarchy['samples'].keys())))

        print("done sort blocks to arai, zij. etc.")
        return(Data, Data_hierarchy)

    #--------------------------------------------------------------
    # Read all information from magic files
    #--------------------------------------------------------------
    def get_data_info(self):
        Data_info = {}
        data_er_samples = {}
        data_er_ages = {}
        data_er_sites = {}
        if self.data_model == 3:  # pick out desired data and refactor to data model 2.5
            Data_info["er_samples"] = []
            Data_info["er_sites"] = []
            Data_info["er_ages"] = []

            # separate out the magic_file full path from the filename
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
            # create MagIC contribution
            self.contribution = cb.Contribution(self.WD, custom_filenames=fnames, read_tables=[
                                                'measurements', 'specimens', 'samples', 'sites'])
            if 'measurements' not in self.contribution.tables:
                print("-W- No measurements found")
                return Data_info

            # propagate data from measurements table into other tables
            self.contribution.propagate_measurement_info()
            self.contribution.propagate_name_down('location', 'samples')

            # make backup files
            if 'specimens' in self.contribution.tables:
                self.spec_container = self.contribution.tables['specimens']
                self.spec_container.write_magic_file(
                    custom_name='specimens.bak', dir_path=self.WD)  # create backup file with original
            else:
                self.spec_container = cb.MagicDataFrame(
                    dtype='specimens', columns=['specimen', 'aniso_type'])
            self.spec_data = self.spec_container.df
            if 'samples' in self.contribution.tables:
                self.contribution.tables['samples'].drop_duplicate_rows(ignore_cols=['sample', 'site', 'citations', 'software_packages'])
                self.samp_container = self.contribution.tables['samples']
                self.samp_container.write_magic_file(
                    custom_name='samples.bak', dir_path=self.WD)  # create backup file with original

            else:
                self.samp_container = cb.MagicDataFrame(dtype='samples',
                                                        columns=['sample', 'site', 'cooling_rate'])

            self.samp_data = self.samp_container.df  # only need this for saving tables
            if 'cooling_rate' not in self.samp_data.columns:
                self.samp_data['cooling_rate'] = None
                print('-W- Your sample file has no cooling rate data.')


            # maybe need to propagate ages here....?
            self.contribution.propagate_ages()

            # gather data for samples
            if len(self.samp_container.df):
                cols = ['sample', 'site', 'cooling_rate']

                if 'location' in self.samp_data.columns:
                    cols.append('location')
                if 'age' in self.samp_data.columns:
                    cols.append('age')
                samples = self.samp_data[cols]
                samples = samples.rename(columns={'site': 'er_site_name',
                                                  'sample': 'er_sample_name',
                                                  'cooling_rate': 'sample_cooling_rate',
                                                  'location': 'er_location_name'})
                # in case of multiple rows with same sample name, make sure cooling rate date propagates

                # to all samples with the same name
                # (sometimes fails due to pandas bug:
                #  https://github.com/pandas-dev/pandas/issues/14955,
                #  hence the try/except)
                try:
                    samples = samples.groupby(samples.index, sort=False).fillna(
                        method='ffill').groupby(samples.index, sort=False).fillna(method='bfill')
                except ValueError:
                    pass
                # then get rid of any duplicates
                samples = samples.drop_duplicates()
                # pick out what is needed by thellier_gui and put in 2.5 format
                er_samples = samples.to_dict('records')
                data_er_samples = {}
                for samp_rec in er_samples:
                    name = samp_rec['er_sample_name']
                    # combine two records for the same sample
                    if name in data_er_samples:
                        old_values = data_er_samples[name]
                        new_values = samp_rec
                        new_rec = {}
                        for k, v in old_values.items():
                            if cb.not_null(v, False):
                                new_rec[k] = v
                            else:
                                new_rec[k] = new_values[k]
                        data_er_samples[name] = new_rec
                    else:
                        data_er_samples[name] = samp_rec

            # if there is no data for samples:
            else:
                er_samples = {}
                data_er_samples = {}
            #
            age_headers = ['site', 'location', 'age',
                           'age_high', 'age_low', 'age_unit']
            if 'sites' in self.contribution.tables:
                # drop stub rows
                self.contribution.tables['sites'].drop_duplicate_rows(ignore_cols=['site', 'location', 'citations', 'software_packages'])
                # get lat/lon info from sites table
                self.contribution.propagate_average_up(cols=['lat', 'lon'],
                                                       target_df_name='sites',
                                                       source_df_name='samples')
                # get sample table
                self.site_container = self.contribution.tables['sites']
                # create backup file with original
                self.site_container.write_magic_file(
                    custom_name='sites.bak', dir_path=self.WD)
                self.site_data = self.site_container.df
                # get required data
                if 'lat' not in self.site_data.columns:
                    self.site_data['lat'] = None
                    print('-W- Your site file has no latitude data.')
                if 'lon' not in self.site_data.columns:
                    self.site_data['lon'] = None
                    print('-W- Your site file has no longitude data.')
                self.site_data = self.site_data[self.site_data['lat'].notnull(
                )]
                self.site_data = self.site_data[self.site_data['lon'].notnull(
                )]
                # if 'age' in self.site_data.columns:
                #    self.site_data = self.site_data[self.site_data['age'].notnull()]
                #self.site_container.df = self.site_data
                # update container df to ignore above null values
                site_headers = ['site', 'int_abs', 'int_abs_sigma',
                                'int_abs_sigma_perc', 'int_n_samples', 'int_n_specimens']
                for head in site_headers:
                    if head not in self.site_data:
                        self.site_data[head] = None
                for header in age_headers:
                    # check for missing age headers
                    if header not in self.site_data.columns:
                        # create blank column for this header

                        self.site_data[header] = None
                age_data = self.site_data[age_headers]
                age_data = age_data[age_data['age'].notnull()]
                age_data = age_data.rename(columns={'site': 'er_site_name',
                                                    'location': 'er_location_name'})
                # save this in 2.5 format
                er_ages = age_data.to_dict('records')
                data_er_ages = {}
                for s in er_ages:
                    s = self.convert_ages_to_calendar_year(s)
                    data_er_ages[s['er_site_name']] = s
                sites = self.site_data[['site', 'location', 'lat', 'lon']]
                sites = sites.rename(
                    columns={'site': 'er_site_name', 'lat': 'site_lat',
                             'lon': 'site_lon', 'location': 'er_location_name'})
                # pick out what is needed by thellier_gui and put in 2.5 format
                er_sites = sites.to_dict('records')
                data_er_sites = {}
                for site_rec in er_sites:
                    name = site_rec['er_site_name']
                    # combine two records for the same site
                    if name in data_er_sites:
                        old_values = data_er_sites[name]
                        new_values = site_rec
                        new_rec = {}
                        for k, v in old_values.items():
                            if cb.not_null(v, False):
                                new_rec[k] = v
                            else:
                                new_rec[k] = new_values[k]
                        data_er_sites[name] = new_rec
                    # no need to combine
                    else:
                        data_er_sites[name] = site_rec
            else:
                self.site_container = cb.MagicDataFrame(
                    dtype='sites', columns=['site'])
            self.site_data = self.site_container.df  # only need this for saving tables

        else:  # read from 2.5 formatted files
            try:
                data_er_samples = self.read_magic_file(os.path.join(
                    self.WD, "er_samples.txt"), 1, 'er_sample_name')
            except:
                self.GUI_log.write(
                    "-W- Can't find er_samples.txt in project directory\n")

            try:
                data_er_sites = self.read_magic_file(os.path.join(
                    self.WD, "er_sites.txt"), 1, 'er_site_name')
            except:
                self.GUI_log.write(
                    "-W- Can't find er_sites.txt in project directory\n")

            try:
                data_er_ages = self.read_er_ages_file(os.path.join(self.WD, "er_ages.txt"), 1, [
                                                      "er_site_name", "er_sample_name"])
            except:
                self.GUI_log.write(
                    "-W- Can't find er_ages.txt in project directory\n")
        Data_info["er_samples"] = data_er_samples
        Data_info["er_sites"] = data_er_sites
        Data_info["er_ages"] = data_er_ages

        return(Data_info)

    #--------------------------------------------------------------
    # Read previous interpretation from specimen file (if it exists)
    #--------------------------------------------------------------

    def get_previous_interpretation(self):
        # first delete all previous interpretation
        for sp in list(self.Data.keys()):
            del self.Data[sp]['pars']
            self.Data[sp]['pars'] = {}
            self.Data[sp]['pars']['lab_dc_field'] = self.Data[sp]['lab_dc_field']
            self.Data[sp]['pars']['er_specimen_name'] = self.Data[sp]['er_specimen_name']
            self.Data[sp]['pars']['er_sample_name'] = self.Data[sp]['er_sample_name']
        self.Data_samples = {}
        self.Data_sites = {}
  # read in data
        prev_pmag_specimen = []
        if self.data_model == 3:  # data model 3.0
            if len(self.spec_data) > 0:  # there are previous measurements
                if 'int_abs' in self.spec_data.columns:
                    # add in these columns if missing, otherwise can throw
                    # errors
                    for col in ['meas_step_min', 'meas_step_max', 'method_codes']:
                        if col not in self.spec_data.columns:
                            self.spec_data[col] = None
                    # get the previous intensity interpretations
                    prev_specs = self.spec_data[self.spec_data['int_abs'].notnull(
                    )]
                    # eliminate ones without bounds
                    prev_specs = prev_specs[prev_specs['meas_step_min'].notnull(
                    )]
                    prev_specs = prev_specs[prev_specs['meas_step_max'].notnull(
                    )]
                    prev_specs = prev_specs[[
                        'specimen', 'meas_step_min', 'meas_step_max', 'method_codes']]
                    # rename column headers to 2.5
                    prev_specs = prev_specs.rename(
                        columns=map_magic.spec_magic3_2_magic2_map)
                    prev_pmag_specimen = prev_specs.to_dict("records")
                else:
                    print('-W- No intensity data found for specimens')
                    self.spec_data['int_abs'] = None
                    prev_pmag_specimen = {}
        else:
            try:
                prev_pmag_specimen, file_type = pmag.magic_read(
                    os.path.join(self.WD, "pmag_specimens.txt"))
                self.GUI_log.write(
                    "-I- Read pmag_specimens.txt for previous interpretation")
                print("-I- Read pmag_specimens.txt for previous interpretation")
            except:
                self.GUI_log.write(
                    "-I- No pmag_specimens.txt for previous interpretation")
                return

        # specimens_list=pmag.get_specs(self.WD+"/pmag_specimens.txt")
        # specimens_list.sort()
        for rec in prev_pmag_specimen:
            if "LP-PI" not in rec["magic_method_codes"]:
                continue
            if "measurement_step_min" not in list(rec.keys()) or rec['measurement_step_min'] == "":
                continue
            if "measurement_step_max" not in list(rec.keys()) or rec['measurement_step_max'] == "":
                continue

            specimen = rec['er_specimen_name']
            tmin_kelvin = float(rec['measurement_step_min'])
            tmax_kelvin = float(rec['measurement_step_max'])
            if specimen not in list(self.redo_specimens.keys()):
                self.redo_specimens[specimen] = {}
                self.redo_specimens[specimen]['t_min'] = float(tmin_kelvin)
                self.redo_specimens[specimen]['t_max'] = float(tmax_kelvin)
            if specimen in list(self.Data.keys()):
                if tmin_kelvin not in self.Data[specimen]['t_Arai'] or tmax_kelvin not in self.Data[specimen]['t_Arai']:
                    self.GUI_log.write(
                        "-W- WARNING: can't fit temperature bounds in the redo file to the actual measurement. specimen %s\n" % specimen)
                else:
                    try:
                        self.Data[specimen]['pars'] = thellier_gui_lib.get_PI_parameters(
                            self.Data, self.acceptance_criteria, self.preferences, specimen, float(tmin_kelvin), float(tmax_kelvin), self.GUI_log, THERMAL, MICROWAVE)
                        self.Data[specimen]['pars']['saved'] = True
                        # write intrepretation into sample data
                        sample = self.Data_hierarchy['specimens'][specimen]
                        if sample not in list(self.Data_samples.keys()):
                            self.Data_samples[sample] = {}
                        if specimen not in list(self.Data_samples[sample].keys()):
                            self.Data_samples[sample][specimen] = {}
                        self.Data_samples[sample][specimen]['B'] = self.Data[specimen]['pars']['specimen_int_uT']

                        site = thellier_gui_lib.get_site_from_hierarchy(
                            sample, self.Data_hierarchy)
                        if site not in list(self.Data_sites.keys()):
                            self.Data_sites[site] = {}
                        if specimen not in list(self.Data_sites[site].keys()):
                            self.Data_sites[site][specimen] = {}
                        self.Data_sites[site][specimen]['B'] = self.Data[specimen]['pars']['specimen_int_uT']

                    except:
                        self.GUI_log.write(
                            "-E- ERROR. Can't calculate PI paremeters for specimen %s using redo file. Check!" % (specimen))
            else:
                self.GUI_log.write(
                    "-W- WARNING: Can't find specimen %s from redo file in measurement file!\n" % specimen)

        try:
            self.s = self.specimens[0]
            self.pars = self.Data[self.s]['pars']
            self.clear_boxes()
            self.draw_figure(self.s)
            self.update_GUI_with_new_interpretation()
        except:
            pass


#===========================================================
#  functions inherited and modified from pmag.py
#===========================================================

    def sortarai(self, datablock, s, Zdiff):
        """
        sorts data block in to first_Z, first_I, etc.
        """

        first_Z, first_I, zptrm_check, ptrm_check, ptrm_tail = [], [], [], [], []
        field, phi, theta = "", "", ""
        starthere = 0
        Treat_I, Treat_Z, Treat_PZ, Treat_PI, Treat_M, Treat_AC = [], [], [], [], [], []
        ISteps, ZSteps, PISteps, PZSteps, MSteps, ACSteps = [], [], [], [], [], []
        GammaChecks = []  # comparison of pTRM direction acquired and lab field
        Mkeys = ['measurement_magn_moment', 'measurement_magn_volume',
                 'measurement_magn_mass', 'measurement_magnitude']
        rec = datablock[0]
        for key in Mkeys:
            if key in list(rec.keys()) and rec[key] != "":
                momkey = key
                break
    # first find all the steps
        for k in range(len(datablock)):
            rec = datablock[k]
            if "treatment_temp" in list(rec.keys()) and rec["treatment_temp"] != "":
                temp = float(rec["treatment_temp"])
                THERMAL = True
                MICROWAVE = False
            elif "treatment_mw_power" in list(rec.keys()) and rec["treatment_mw_power"] != "":
                THERMAL = False
                MICROWAVE = True
                if "measurement_description" in list(rec.keys()):
                    MW_step = rec["measurement_description"].strip(
                        '\n').split(":")
                    for STEP in MW_step:
                        if "Number" in STEP:
                            temp = float(STEP.split("-")[-1])

            methcodes = []
            tmp = rec["magic_method_codes"].split(":")
            for meth in tmp:
                methcodes.append(meth.strip())
            # for thellier-thellier
            if 'LT-T-I' in methcodes and 'LP-PI-TRM' in methcodes and 'LP-TRM' not in methcodes:
                Treat_I.append(temp)
                ISteps.append(k)
                if field == "":
                    field = float(rec["treatment_dc_field"])
                if phi == "":
                    phi = float(rec['treatment_dc_field_phi'])
                    theta = float(rec['treatment_dc_field_theta'])

            # for Microwave
            if 'LT-M-I' in methcodes and 'LP-PI-M' in methcodes:
                Treat_I.append(temp)
                ISteps.append(k)
                if field == "":
                    field = float(rec["treatment_dc_field"])
                if phi == "":
                    phi = float(rec['treatment_dc_field_phi'])
                    theta = float(rec['treatment_dc_field_theta'])

    # stick  first zero field stuff into first_Z
            if 'LT-NO' in methcodes:
                Treat_Z.append(temp)
                ZSteps.append(k)
            if "LT-AF-Z" in methcodes and 'treatment_ac_field' in list(rec.keys()):
                if rec['treatment_ac_field'] != "":
                    AFD_after_NRM = True
                    # consider AFD before T-T experiment ONLY if it comes before
                    # the experiment
                    for i in range(len(first_I)):
                        # check if there was an infield step before the AFD
                        if float(first_I[i][3]) != 0:
                            AFD_after_NRM = False
                        if AFD_after_NRM:
                            AF_field = 0
                            if 'treatment_ac_field' in rec:
                                try:
                                    AF_field = float(rec['treatment_ac_field']) * 1000
                                except ValueError:
                                    pass

                            dec = float(rec["measurement_dec"])
                            inc = float(rec["measurement_inc"])
                            intensity = float(rec[momkey])
                            first_I.append([273. - AF_field, 0., 0., 0., 1])
                            first_Z.append(
                                [273. - AF_field, dec, inc, intensity, 1])  # NRM step
            if 'LT-T-Z' in methcodes or 'LT-M-Z' in methcodes:
                Treat_Z.append(temp)
                ZSteps.append(k)
            if 'LT-PTRM-Z':
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
                dec = float(rec["measurement_dec"])
                inc = float(rec["measurement_inc"])
                moment = float(rec["measurement_magn_moment"])
                if 'LP-PI-M' not in methcodes:
                    first_I.append([273, 0., 0., 0., 1])
                    first_Z.append([273, dec, inc, moment, 1])  # NRM step
                else:
                    first_I.append([0, 0., 0., 0., 1])
                    first_Z.append([0, dec, inc, moment, 1])  # NRM step

        #---------------------
        # find  IZ and ZI
        #---------------------

        for temp in Treat_I:  # look through infield steps and find matching Z step
            if temp in Treat_Z:  # found a match
                istep = ISteps[Treat_I.index(temp)]
                irec = datablock[istep]
                methcodes = []
                tmp = irec["magic_method_codes"].split(":")
                for meth in tmp:
                    methcodes.append(meth.strip())
                # take last record as baseline to subtract
                brec = datablock[istep - 1]
                zstep = ZSteps[Treat_Z.index(temp)]
                zrec = datablock[zstep]
        # sort out first_Z records
                # check if ZI/IZ in in method codes:
                ZI = ""
                if "LP-PI-TRM-IZ" in methcodes or "LP-PI-M-IZ" in methcodes or "LP-PI-IZ" in methcodes:
                    ZI = 0
                elif "LP-PI-TRM-ZI" in methcodes or "LP-PI-M-ZI" in methcodes or "LP-PI-ZI" in methcodes:
                    ZI = 1
                elif "LP-PI-BT-IZZI" in methcodes:
                    ZI == ""
                    i_intex, z_intex = 0, 0
                    foundit = False
                    for i in range(len(datablock)):
                        if THERMAL:
                            if ('treatment_temp' in list(datablock[i].keys()) and float(temp) == float(datablock[i]['treatment_temp'])):
                                foundit = True
                        if MICROWAVE:
                            if ('measurement_description' in list(datablock[i].keys())):
                                MW_step = datablock[i]["measurement_description"].strip(
                                    '\n').split(":")
                                for STEP in MW_step:
                                    if "Number" in STEP:
                                        ThisStep = float(STEP.split("-")[-1])
                                        if ThisStep == float(temp):
                                            foundit = True
                        if foundit:
                            if "LT-T-Z" in datablock[i]['magic_method_codes'].split(":") or "LT-M-Z" in datablock[i]['magic_method_codes'].split(":"):
                                z_intex = i
                            if "LT-T-I" in datablock[i]['magic_method_codes'].split(":") or "LT-M-I" in datablock[i]['magic_method_codes'].split(":"):
                                i_intex = i
                            foundit = False

                    if z_intex < i_intex:
                        ZI = 1
                    else:
                        ZI = 0
                dec = float(zrec["measurement_dec"])
                inc = float(zrec["measurement_inc"])
                str = float(zrec[momkey])
                first_Z.append([temp, dec, inc, str, ZI])
        # sort out first_I records
                idec = float(irec["measurement_dec"])
                iinc = float(irec["measurement_inc"])
                istr = float(irec[momkey])
                X = pmag.dir2cart([idec, iinc, istr])
                BL = pmag.dir2cart([dec, inc, str])
                I = []
                for c in range(3):
                    I.append((X[c] - BL[c]))
                if I[2] != 0:
                    iDir = pmag.cart2dir(I)
                    if Zdiff == 0:
                        first_I.append([temp, iDir[0], iDir[1], iDir[2], ZI])
                    else:
                        first_I.append([temp, 0., 0., I[2], ZI])
# gamma=angle([iDir[0],iDir[1]],[phi,theta])
                else:
                    first_I.append([temp, 0., 0., 0., ZI])
# gamma=0.0
# put in Gamma check (infield trm versus lab field)
# if 180.-gamma<gamma:
# gamma=180.-gamma
# GammaChecks.append([temp-273.,gamma])

        #---------------------
        # find Thellier Thellier protocol
        #---------------------
        if 'LP-PI-II'in methcodes or 'LP-PI-T-II' in methcodes or 'LP-PI-M-II' in methcodes:
            # look through infield steps and find matching Z step
            for i in range(1, len(Treat_I)):
                if Treat_I[i] == Treat_I[i - 1]:
                    # ignore, if there are more than
                    temp = Treat_I[i]
                    irec1 = datablock[ISteps[i - 1]]
                    dec1 = float(irec1["measurement_dec"])
                    inc1 = float(irec1["measurement_inc"])
                    moment1 = float(irec1["measurement_magn_moment"])
                    if len(first_I) < 2:
                        dec_initial = dec1
                        inc_initial = inc1
                    cart1 = np.array(pmag.dir2cart([dec1, inc1, moment1]))
                    irec2 = datablock[ISteps[i]]
                    dec2 = float(irec2["measurement_dec"])
                    inc2 = float(irec2["measurement_inc"])
                    moment2 = float(irec2["measurement_magn_moment"])
                    cart2 = np.array(pmag.dir2cart([dec2, inc2, moment2]))

                    # check if its in the same treatment
                    if Treat_I[i] == Treat_I[i - 2] and dec2 != dec_initial and inc2 != inc_initial:
                        continue
                    if dec1 != dec2 and inc1 != inc2:
                        zerofield = (cart2 + cart1) / 2
                        infield = (cart2 - cart1) / 2

                        DIR_zerofield = pmag.cart2dir(zerofield)
                        DIR_infield = pmag.cart2dir(infield)

                        first_Z.append(
                            [temp, DIR_zerofield[0], DIR_zerofield[1], DIR_zerofield[2], 0])
                        first_I.append(
                            [temp, DIR_infield[0], DIR_infield[1], DIR_infield[2], 0])

        #---------------------
        # find  pTRM checks
        #---------------------

        for i in range(len(Treat_PI)):  # look through infield steps and find matching Z step

            temp = Treat_PI[i]
            k = PISteps[i]
            rec = datablock[k]
            dec = float(rec["measurement_dec"])
            inc = float(rec["measurement_inc"])
            moment = float(rec["measurement_magn_moment"])
            phi = float(rec["treatment_dc_field_phi"])
            theta = float(rec["treatment_dc_field_theta"])
            M = np.array(pmag.dir2cart([dec, inc, moment]))

            foundit = False
            if 'LP-PI-II' not in methcodes:
                    # Important: suport several pTRM checks in a row, but
                    # does not support pTRM checks after infield step
                for j in range(k, 1, -1):
                    if "LT-M-I" in datablock[j]['magic_method_codes'] or "LT-T-I" in datablock[j]['magic_method_codes']:
                        after_zerofield = 0.
                        foundit = True
                        prev_rec = datablock[j]
                        zerofield_index = j
                        break
                    if float(datablock[j]['treatment_dc_field']) == 0:
                        after_zerofield = 1.
                        foundit = True
                        prev_rec = datablock[j]
                        zerofield_index = j
                        break
            else:  # Thellier-Thellier protocol
                foundit = True
                prev_rec = datablock[k - 1]
                zerofield_index = k - 1

            if foundit:
                prev_dec = float(prev_rec["measurement_dec"])
                prev_inc = float(prev_rec["measurement_inc"])
                prev_moment = float(prev_rec["measurement_magn_moment"])
                prev_phi = float(prev_rec["treatment_dc_field_phi"])
                prev_theta = float(prev_rec["treatment_dc_field_theta"])
                prev_M = np.array(pmag.dir2cart(
                    [prev_dec, prev_inc, prev_moment]))

                if 'LP-PI-II' not in methcodes:
                    diff_cart = M - prev_M
                    diff_dir = pmag.cart2dir(diff_cart)
                    if after_zerofield == 0:
                        ptrm_check.append(
                            [temp, diff_dir[0], diff_dir[1], diff_dir[2], zerofield_index, after_zerofield])
                    else:
                        ptrm_check.append(
                            [temp, diff_dir[0], diff_dir[1], diff_dir[2], zerofield_index, after_zerofield])
                else:
                    # health check for T-T protocol:
                    if theta != prev_theta:
                        diff = (M - prev_M) / 2
                        diff_dir = pmag.cart2dir(diff)
                        ptrm_check.append(
                            [temp, diff_dir[0], diff_dir[1], diff_dir[2], zerofield_index, ""])
                    else:
                        print(
                            "-W- WARNING: specimen. pTRM check not in place in Thellier Thellier protocol. step please check")

        #---------------------
        # find Tail checks
        #---------------------

        for temp in Treat_M:
            # print temp
            step = MSteps[Treat_M.index(temp)]
            rec = datablock[step]
            dec = float(rec["measurement_dec"])
            inc = float(rec["measurement_inc"])
            moment = float(rec["measurement_magn_moment"])
            foundit = False
            for i in range(1, len(datablock)):
                if 'LT-T-Z' in datablock[i]['magic_method_codes'] or 'LT-M-Z' in datablock[i]['magic_method_codes']:
                    if (THERMAL and "treatment_temp" in list(datablock[i].keys()) and float(datablock[i]["treatment_temp"]) == float(temp))\
                       or (MICROWAVE and "measurement_description" in list(datablock[i].keys()) and "Step Number-%.0f" % float(temp) in datablock[i]["measurement_description"]):
                        prev_rec = datablock[i]
                        prev_dec = float(prev_rec["measurement_dec"])
                        prev_inc = float(prev_rec["measurement_inc"])
                        prev_moment = float(
                            prev_rec["measurement_magn_moment"])
                        foundit = True
                        break

            if foundit:
                ptrm_tail.append([temp, 0, 0, moment - prev_moment])

    #
    # final check
    #
        if len(first_Z) != len(first_I):
            print(len(first_Z), len(first_I))
            print(" Something wrong with this specimen! Better fix it or delete it ")
            input(" press return to acknowledge message")

        #---------------------
        # find  Additivity (patch by rshaar)
        #---------------------

        additivity_check = []
        for i in range(len(Treat_AC)):
            step_0 = ACSteps[i]
            temp = Treat_AC[i]
            dec0 = float(datablock[step_0]["measurement_dec"])
            inc0 = float(datablock[step_0]["measurement_inc"])
            moment0 = float(datablock[step_0]['measurement_magn_moment'])
            V0 = pmag.dir2cart([dec0, inc0, moment0])
            # find the infield step that comes before the additivity check
            foundit = False
            for j in range(step_0, 1, -1):
                if "LT-T-I" in datablock[j]['magic_method_codes']:
                    foundit = True
                    break
            if foundit:
                dec1 = float(datablock[j]["measurement_dec"])
                inc1 = float(datablock[j]["measurement_inc"])
                moment1 = float(datablock[j]['measurement_magn_moment'])
                V1 = pmag.dir2cart([dec1, inc1, moment1])
                # print "additivity check: ",s
                # print j
                # print "ACC=V1-V0:"
                # print "V1=",[dec1,inc1,moment1],pmag.dir2cart([dec1,inc1,moment1])/float(datablock[0]["measurement_magn_moment"])
                # print "V1=",pmag.dir2cart([dec1,inc1,moment1])/float(datablock[0]["measurement_magn_moment"])
                # print "V0=",[dec0,inc0,moment0],pmag.dir2cart([dec0,inc0,moment0])/float(datablock[0]["measurement_magn_moment"])
                # print "NRM=",float(datablock[0]["measurement_magn_moment"])
                # print "-------"

                I = []
                for c in range(3):
                    I.append(V1[c] - V0[c])
                dir1 = pmag.cart2dir(I)
                additivity_check.append([temp, dir1[0], dir1[1], dir1[2]])
                # print
                # "I",np.array(I)/float(datablock[0]["measurement_magn_moment"]),dir1,"(dir1
                # unnormalized)"
                X = np.array(I) / \
                    float(datablock[0]["measurement_magn_moment"])
                # print "I",np.sqrt(sum(X**2))
        araiblock = (first_Z, first_I, ptrm_check, ptrm_tail,
                     zptrm_check, GammaChecks, additivity_check)

        return araiblock, field

    def user_warning(self, message, caption='Warning!'):
        """
        Shows a dialog that warns the user about some action
        @param: message - message to display to user
        @param: caption - title for dialog (default: "Warning!")
        @return: True or False
        """
        dlg = wx.MessageDialog(self, message, caption,
                               wx.OK | wx.CANCEL | wx.ICON_WARNING)
        if self.show_dlg(dlg) == wx.ID_OK:
            continue_bool = True
        else:
            continue_bool = False
        dlg.Destroy()
        return continue_bool


    def test_for_criteria(self):
        """
        Return any criteria values that have actually been set,
        not just "empty" values of -999.
        Ignore interpreter_method, average_by_sample_or_site, and include_nrm,
        becuase these have default values other than -999 and are only used
        internal to Thellier GUI.

        Returns
        ---------
        values : list
            list of non -999 values in self.acceptance_criteria values
        """
        ignore = ['interpreter_method', 'average_by_sample_or_site', 'include_nrm']
        values = ([dic['value'] for dic in self.acceptance_criteria.values() if (dic['criterion_name'] not in ignore and dic['value'] != -999)])
        return values


#--------------------------------------------------------------
# Run the GUI
#--------------------------------------------------------------


def main(WD=None, standalone_app=True, parent=None, DM=2.5):
    # to run as module, i.e. with Pmag GUI:
    if not standalone_app:
        wait = wx.BusyInfo('Compiling required data, please wait...')
        wx.SafeYield()
        frame = Arai_GUI(WD, parent, standalone=False, DM=DM)
        frame.Centre()
        frame.Show()
        del wait
    # to run as command line:
    else:
        app = wx.App(redirect=False)  # , #filename='py2app_log.log')
        app.frame = Arai_GUI(WD)
        app.frame.Show()
        app.frame.Center()
        app.MainLoop()


if __name__ == '__main__':
    main()

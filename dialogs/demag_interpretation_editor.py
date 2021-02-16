import wx, os, sys
import pmagpy.find_pmag_dir as find_pmag_dir
from copy import copy
from numpy import vstack,sqrt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar
from matplotlib.figure import Figure
import help_files.demag_interpretation_editor_help as dieh
from pmagpy.demag_gui_utilities import *
from pmagpy.Fit import *
from pmagpy.pmag import get_version

global CURRENT_VERSION, PMAGPY_DIRECTORY
CURRENT_VERSION = get_version()
PMAGPY_DIRECTORY = find_pmag_dir.get_pmag_dir()
IMG_DIRECTORY = os.path.join(PMAGPY_DIRECTORY, 'dialogs', 'images')


class InterpretationEditorFrame(wx.Frame):

    #########################Init Funcions#############################

    def __init__(self,parent):
        """Constructor"""
        #set parent and resolution
        self.parent = parent
        self.GUI_RESOLUTION=self.parent.GUI_RESOLUTION
        #call init of super class
        default_style = wx.MINIMIZE_BOX | wx.MAXIMIZE_BOX | wx.RESIZE_BORDER | wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX | wx.CLIP_CHILDREN | wx.NO_FULL_REPAINT_ON_RESIZE | wx.WS_EX_CONTEXTHELP | wx.FRAME_EX_CONTEXTHELP
        wx.Frame.__init__(self, self.parent, title="Interpretation Editor version:%s"%CURRENT_VERSION,style=default_style, size=(675*self.GUI_RESOLUTION,425*self.GUI_RESOLUTION))
        self.Bind(wx.EVT_CLOSE, self.on_close_edit_window)
        #setup wx help provider class to give help messages
        provider = wx.SimpleHelpProvider()
        wx.HelpProvider.Set(provider)
        self.helper = wx.ContextHelp(doNow=False)
        #make the Panel
        self.panel = wx.Panel(self,-1,size=(700*self.GUI_RESOLUTION,450*self.GUI_RESOLUTION))
        #set icon
        self.SetIcon(self.parent.icon)
#        icon = wx.Icon()
#        icon_path = os.path.join(IMG_DIRECTORY, 'PmagPy.ico')
#        if os.path.exists(icon_path):
#            icon.CopyFromBitmap(wx.Bitmap(icon_path), wx.BITMAP_TYPE_ANY)
#            self.SetIcon(icon)
        self.specimens_list=self.parent.specimens
        self.current_fit_index = None
        self.search_query = ""
        self.font_type = self.parent.font_type
        #build UI and menu
        self.init_UI()
        self.create_menu()
        #update with stuff
        self.on_select_level_name(None)

    def init_UI(self):
        """
        Builds User Interface for the interpretation Editor
        """

        #set fonts
        FONT_WEIGHT=1
        if sys.platform.startswith('win'): FONT_WEIGHT=-1
        font1 = wx.Font(9+FONT_WEIGHT, wx.SWISS, wx.NORMAL, wx.NORMAL, False, self.font_type)
        font2 = wx.Font(12+FONT_WEIGHT, wx.SWISS, wx.NORMAL, wx.NORMAL, False, self.font_type)

        #if you're on mac do some funny stuff to make it look okay
        is_mac = False
        if sys.platform.startswith("darwin"):
            is_mac = True

        self.search_bar = wx.SearchCtrl(self.panel, size=(350*self.GUI_RESOLUTION,25) ,style=wx.TE_PROCESS_ENTER | wx.TE_PROCESS_TAB | wx.TE_NOHIDESEL)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_enter_search_bar,self.search_bar)
        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.on_enter_search_bar,self.search_bar)
        self.search_bar.SetHelpText(dieh.search_help)
#        self.Bind(wx.EVT_TEXT, self.on_complete_search_bar,self.search_bar)

        #build logger
        self.logger = wx.ListCtrl(self.panel, -1, size=(100*self.GUI_RESOLUTION,475*self.GUI_RESOLUTION),style=wx.LC_REPORT)
        self.logger.SetFont(font1)
        self.logger.InsertColumn(0, 'specimen',width=75*self.GUI_RESOLUTION)
        self.logger.InsertColumn(1, 'fit name',width=65*self.GUI_RESOLUTION)
        self.logger.InsertColumn(2, 'max',width=55*self.GUI_RESOLUTION)
        self.logger.InsertColumn(3, 'min',width=55*self.GUI_RESOLUTION)
        self.logger.InsertColumn(4, 'n',width=25*self.GUI_RESOLUTION)
        self.logger.InsertColumn(5, 'fit type',width=60*self.GUI_RESOLUTION)
        self.logger.InsertColumn(6, 'dec',width=45*self.GUI_RESOLUTION)
        self.logger.InsertColumn(7, 'inc',width=45*self.GUI_RESOLUTION)
        self.logger.InsertColumn(8, 'mad',width=45*self.GUI_RESOLUTION)
        self.logger.InsertColumn(9, 'dang',width=45*self.GUI_RESOLUTION)
        self.logger.InsertColumn(10, 'a95',width=45*self.GUI_RESOLUTION)
        self.logger.InsertColumn(11, 'K',width=45*self.GUI_RESOLUTION)
        self.logger.InsertColumn(12, 'R',width=45*self.GUI_RESOLUTION)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnClick_listctrl, self.logger)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK,self.OnRightClickListctrl,self.logger)
        self.logger.SetHelpText(dieh.logger_help)

        #set fit attributes boxsizers
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

        self.level_box = wx.ComboBox(self.panel, -1, size=(110*self.GUI_RESOLUTION, 25), value=UPPER_LEVEL, choices=['sample','site','location','study'], style=wx.CB_DROPDOWN|wx.TE_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.on_select_high_level,self.level_box)
        self.level_box.SetHelpText(dieh.level_box_help)

        self.level_names = wx.ComboBox(self.panel, -1, size=(110*self.GUI_RESOLUTION, 25), value=self.parent.level_names.GetValue(), choices=name_choices, style=wx.CB_DROPDOWN|wx.TE_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.on_select_level_name,self.level_names)
        self.level_names.SetHelpText(dieh.level_names_help)

        #mean type and plot display boxes
        self.mean_type_box = wx.ComboBox(self.panel, -1, size=(110*self.GUI_RESOLUTION, 25), value=self.parent.mean_type_box.GetValue(), choices=['Fisher','Fisher by polarity','None'], style=wx.CB_DROPDOWN|wx.TE_READONLY, name="high_type")
        self.Bind(wx.EVT_COMBOBOX, self.on_select_mean_type_box,self.mean_type_box)
        self.mean_type_box.SetHelpText(dieh.mean_type_help)

        self.mean_fit_box = wx.ComboBox(self.panel, -1, size=(110*self.GUI_RESOLUTION, 25), value=self.parent.mean_fit, choices=(['None','All'] + self.parent.fit_list), style=wx.CB_DROPDOWN|wx.TE_READONLY, name="high_type")
        self.Bind(wx.EVT_COMBOBOX, self.on_select_mean_fit_box,self.mean_fit_box)
        self.mean_fit_box.SetHelpText(dieh.mean_fit_help)

        #show box
        if UPPER_LEVEL == "study" or UPPER_LEVEL == "location":
            show_box_choices = ['specimens','samples','sites']
        if UPPER_LEVEL == "site":
            show_box_choices = ['specimens','samples']
        if UPPER_LEVEL == "sample":
            show_box_choices = ['specimens']

        self.show_box = wx.ComboBox(self.panel, -1, size=(110*self.GUI_RESOLUTION, 25), value='specimens', choices=show_box_choices, style=wx.CB_DROPDOWN|wx.TE_READONLY,name="high_elements")
        self.Bind(wx.EVT_COMBOBOX, self.on_select_show_box,self.show_box)
        self.show_box.SetHelpText(dieh.show_help)

        #coordinates box
        self.coordinates_box = wx.ComboBox(self.panel, -1, size=(110*self.GUI_RESOLUTION, 25), choices=self.parent.coordinate_list, value=self.parent.coordinates_box.GetValue(), style=wx.CB_DROPDOWN|wx.TE_READONLY, name="coordinates")
        self.Bind(wx.EVT_COMBOBOX, self.on_select_coordinates,self.coordinates_box)
        self.coordinates_box.SetHelpText(dieh.coordinates_box_help)

        #bounds select boxes
        self.tmin_box = wx.ComboBox(self.panel, -1, size=(80*self.GUI_RESOLUTION, 25), choices=[''] + self.parent.T_list, style=wx.CB_DROPDOWN|wx.TE_READONLY, name="lower bound")
        self.tmin_box.SetHelpText(dieh.tmin_box_help)

        self.tmax_box = wx.ComboBox(self.panel, -1, size=(80*self.GUI_RESOLUTION, 25), choices=[''] + self.parent.T_list, style=wx.CB_DROPDOWN|wx.TE_READONLY, name="upper bound")
        self.tmax_box.SetHelpText(dieh.tmax_box_help)

        #color box
        self.color_dict = self.parent.color_dict
        self.color_box = wx.ComboBox(self.panel, -1, size=(80*self.GUI_RESOLUTION, 25), choices=[''] + sorted(self.color_dict.keys()), style=wx.CB_DROPDOWN|wx.TE_PROCESS_ENTER, name="color")
        self.Bind(wx.EVT_TEXT_ENTER, self.add_new_color, self.color_box)
        self.color_box.SetHelpText(dieh.color_box_help)

        #name box
        self.name_box = wx.TextCtrl(self.panel, -1, size=(80*self.GUI_RESOLUTION, 25), name="name")
        self.name_box.SetHelpText(dieh.name_box_help)

        #more mac stuff
        h_size_buttons,button_spacing = 25,5.5
        if is_mac: h_size_buttons,button_spacing = 18,0.

        #buttons
        self.add_all_button = wx.Button(self.panel, id=-1, label='add new fit to all specimens',size=(160*self.GUI_RESOLUTION,h_size_buttons))
        self.add_all_button.SetFont(font1)
        self.Bind(wx.EVT_BUTTON, self.add_fit_to_all, self.add_all_button)
        self.add_all_button.SetHelpText(dieh.add_all_help)

        self.add_fit_button = wx.Button(self.panel, id=-1, label='add fit to highlighted specimens',size=(160*self.GUI_RESOLUTION,h_size_buttons))
        self.add_fit_button.SetFont(font1)
        self.Bind(wx.EVT_BUTTON, self.add_highlighted_fits, self.add_fit_button)
        self.add_fit_button.SetHelpText(dieh.add_fit_btn_help)

        self.delete_fit_button = wx.Button(self.panel, id=-1, label='delete highlighted fits',size=(160*self.GUI_RESOLUTION,h_size_buttons))
        self.delete_fit_button.SetFont(font1)
        self.Bind(wx.EVT_BUTTON, self.delete_highlighted_fits, self.delete_fit_button)
        self.delete_fit_button.SetHelpText(dieh.delete_fit_btn_help)

        self.apply_changes_button = wx.Button(self.panel, id=-1, label='apply changes to highlighted fits',size=(160*self.GUI_RESOLUTION,h_size_buttons))
        self.apply_changes_button.SetFont(font1)
        self.Bind(wx.EVT_BUTTON, self.apply_changes, self.apply_changes_button)
        self.apply_changes_button.SetHelpText(dieh.apply_changes_help)

        #windows
        display_window_0 = wx.GridSizer(2, 1, 10*self.GUI_RESOLUTION, 19*self.GUI_RESOLUTION)
        display_window_1 = wx.GridSizer(2, 1, 10*self.GUI_RESOLUTION, 19*self.GUI_RESOLUTION)
        display_window_2 = wx.GridSizer(2, 1, 10*self.GUI_RESOLUTION, 19*self.GUI_RESOLUTION)
        name_window = wx.GridSizer(2, 1, 10*self.GUI_RESOLUTION, 19*self.GUI_RESOLUTION)
        bounds_window = wx.GridSizer(2, 1, 10*self.GUI_RESOLUTION, 19*self.GUI_RESOLUTION)
        buttons1_window = wx.GridSizer(4, 1, 5*self.GUI_RESOLUTION, 19*self.GUI_RESOLUTION)
        display_window_0.AddMany( [(self.coordinates_box),
                                   (self.show_box)] )
        display_window_1.AddMany( [(self.level_box),
                                   (self.level_names)] )
        display_window_2.AddMany( [(self.mean_type_box),
                                   (self.mean_fit_box)] )
        name_window.AddMany( [(self.name_box),
                                (self.color_box)] )
        bounds_window.AddMany( [(self.tmin_box),
                                (self.tmax_box)] )
        buttons1_window.AddMany( [(self.add_fit_button, wx.ALL|wx.SHAPED, 0),
                                  (self.add_all_button, wx.ALL|wx.SHAPED, 0),
                                  (self.delete_fit_button, wx.ALL|wx.SHAPED, 0),
                                  (self.apply_changes_button, wx.ALL|wx.SHAPED, 0)])
        self.display_sizer.Add(display_window_0, 1, wx.TOP | wx.EXPAND, 8)
        self.display_sizer.Add(display_window_1, 1, wx.TOP | wx.LEFT| wx.EXPAND, 8)
        self.display_sizer.Add(display_window_2, 1, wx.TOP | wx.LEFT| wx.EXPAND, 8)
        self.name_sizer.Add(name_window, 1, wx.TOP, 5.5)
        self.bounds_sizer.Add(bounds_window, 1, wx.TOP, 5.5)
        self.buttons_sizer.Add(buttons1_window, 1, wx.TOP, 0)

        #duplicate high levels plot
        self.fig = Figure((2.5*self.GUI_RESOLUTION, 2.5*self.GUI_RESOLUTION), dpi=100)
        self.canvas = FigCanvas(self.panel, -1, self.fig, )
        self.toolbar = NavigationToolbar(self.canvas)
        self.toolbar.Hide()
        self.toolbar.zoom()
        self.high_EA_setting = "Zoom"
        self.canvas.Bind(wx.EVT_LEFT_DCLICK,self.on_equalarea_high_select)
        self.canvas.Bind(wx.EVT_MOTION,self.on_change_high_mouse_cursor)
        self.canvas.Bind(wx.EVT_MIDDLE_DOWN,self.home_high_equalarea)
        self.canvas.Bind(wx.EVT_RIGHT_DOWN,self.pan_zoom_high_equalarea)
        self.canvas.SetHelpText(dieh.eqarea_help)

        self.eqarea = self.fig.add_subplot(111)
        draw_net(self.eqarea)

        #Higher Level Statistics Box
        self.stats_sizer = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY,"mean statistics"  ), wx.VERTICAL)

        for parameter in ['mean_type','dec','inc','alpha95','K','R','n_lines','n_planes']:
            COMMAND="self.%s_window=wx.TextCtrl(self.panel,style=wx.TE_CENTER|wx.TE_READONLY,size=(100*self.GUI_RESOLUTION,25))"%parameter
            exec(COMMAND)
            COMMAND="self.%s_window.SetBackgroundColour(wx.WHITE)"%parameter
            exec(COMMAND)
            COMMAND="self.%s_window.SetFont(font2)"%parameter
            exec(COMMAND)
            COMMAND="self.%s_outer_window = wx.GridSizer(1,2,5*self.GUI_RESOLUTION,15*self.GUI_RESOLUTION)"%parameter
            exec(COMMAND)
            COMMAND="""self.%s_outer_window.AddMany([
                    (wx.StaticText(self.panel,label='%s',style=wx.TE_CENTER),wx.EXPAND),
                    (self.%s_window, wx.EXPAND)])"""%(parameter,parameter,parameter)
            exec(COMMAND)
            COMMAND="self.stats_sizer.Add(self.%s_outer_window, 1|wx.EXPAND, 0)"%parameter
            exec(COMMAND)

        self.switch_stats_button = wx.SpinButton(self.panel, id=wx.ID_ANY, style=wx.SP_HORIZONTAL|wx.SP_ARROW_KEYS|wx.SP_WRAP, name="change stats")
        self.Bind(wx.EVT_SPIN, self.on_select_stats_button,self.switch_stats_button)
        self.switch_stats_button.SetHelpText(dieh.switch_stats_btn_help)

        #construct panel
        hbox0 = wx.BoxSizer(wx.HORIZONTAL)
        hbox0.Add(self.name_sizer,flag=wx.EXPAND,border=8)
        hbox0.Add(self.bounds_sizer,flag=wx.EXPAND,border=8)

        vbox0 = wx.BoxSizer(wx.VERTICAL)
        vbox0.Add(hbox0,border=8)
        vbox0.Add(self.buttons_sizer,border=8)

        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(vbox0,border=8)
        hbox1.Add(self.stats_sizer,border=8)
        hbox1.Add(self.switch_stats_button,flag=wx.EXPAND,border=8)

        vbox1 = wx.BoxSizer(wx.VERTICAL)
        vbox1.Add(self.display_sizer,border=8)
        vbox1.Add(hbox1,border=8)
        vbox1.Add(self.canvas,proportion=1,flag= wx.EXPAND,border=8)

        vbox2 = wx.BoxSizer(wx.VERTICAL)
        vbox2.Add(self.search_bar,proportion=.5,flag= wx.EXPAND, border=8)
        vbox2.Add(self.logger,proportion=1,flag=wx.EXPAND,border=8)

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2.Add(vbox2,proportion=1,flag=wx.EXPAND)
        hbox2.Add(vbox1,flag=wx.EXPAND)

        self.panel.SetSizerAndFit(hbox2)
        hbox2.Fit(self)

    def create_menu(self):

        menubar = wx.MenuBar()

        #--------------------------------------------------------------------

        menu_file = wx.Menu()

        m_change_WD = menu_file.Append(-1, "Change Working Directory\tCtrl-W","")
        self.Bind(wx.EVT_MENU, self.parent.on_menu_change_working_directory, m_change_WD)

        m_make_MagIC_results_tables = menu_file.Append(-1, "&Save MagIC pmag tables\tCtrl-Shift-S", "")
        self.Bind(wx.EVT_MENU, self.parent.on_menu_make_MagIC_results_tables, m_make_MagIC_results_tables)

        submenu_save_plots = wx.Menu()

        m_save_high_level = submenu_save_plots.Append(-1, "&Save high level plot", "")
        self.Bind(wx.EVT_MENU, self.parent.on_save_high_level, m_save_high_level,"Eq")

        m_new_sub_plots = menu_file.AppendSubMenu(submenu_save_plots, "&Save plot")

        menu_file.AppendSeparator()
        m_exit = menu_file.Append(-1, "E&xit\tCtrl-Q", "Exit")
        self.Bind(wx.EVT_MENU, self.on_close_edit_window, m_exit)

        #--------------------------------------------------------------------

        menu_Analysis = wx.Menu()

        submenu_criteria = wx.Menu()

        m_change_criteria_file = submenu_criteria.Append(-1, "&Change acceptance criteria", "")
        self.Bind(wx.EVT_MENU, self.parent.on_menu_change_criteria, m_change_criteria_file)

        m_import_criteria_file =  submenu_criteria.Append(-1, "&Import criteria file", "")
        self.Bind(wx.EVT_MENU, self.parent.on_menu_criteria_file, m_import_criteria_file)

        m_new_sub = menu_Analysis.AppendSubMenu(submenu_criteria, "Acceptance criteria")

        m_import_LSQ = menu_Analysis.Append(-1, "&Import Interpretations from LSQ file\tCtrl-L", "")
        self.Bind(wx.EVT_MENU, self.parent.on_menu_read_from_LSQ, m_import_LSQ)

        m_previous_interpretation = menu_Analysis.Append(-1, "&Import previous interpretations from a redo file\tCtrl-R", "")
        self.Bind(wx.EVT_MENU, self.parent.on_menu_previous_interpretation, m_previous_interpretation)

        m_save_interpretation = menu_Analysis.Append(-1, "&Save current interpretations to a redo file\tCtrl-S", "")
        self.Bind(wx.EVT_MENU, self.parent.on_menu_save_interpretation, m_save_interpretation)

        #--------------------------------------------------------------------

        menu_Tools = wx.Menu()

        m_view_VGP = menu_Tools.Append(-1, "&View VGPs\tCtrl-Shift-V", "")
        self.Bind(wx.EVT_MENU, self.parent.on_menu_view_vgps, m_view_VGP)

        #--------------------------------------------------------------------

        menu_Help = wx.Menu()

        m_help = menu_Help.Append(-1, "&Usage and Tips\tCtrl-H", "")
        self.Bind(wx.EVT_MENU, self.on_menu_help, m_help)

        m_cookbook = menu_Help.Append(-1, "&PmagPy Cookbook\tCtrl-Shift-W", "")
        self.Bind(wx.EVT_MENU, self.parent.on_menu_cookbook, m_cookbook)

        m_docs = menu_Help.Append(-1, "&Open Docs\tCtrl-Shift-H", "")
        self.Bind(wx.EVT_MENU, self.parent.on_menu_docs, m_docs)

        m_git = menu_Help.Append(-1, "&Github Page\tCtrl-Shift-G", "")
        self.Bind(wx.EVT_MENU, self.parent.on_menu_git, m_git)

        m_debug = menu_Help.Append(-1, "&Open Debugger\tCtrl-Shift-D", "")
        self.Bind(wx.EVT_MENU, self.parent.on_menu_debug, m_debug)

        #--------------------------------------------------------------------

        menu_edit = wx.Menu()

        m_new = menu_edit.Append(-1, "&New interpretation\tCtrl-N", "")
        self.Bind(wx.EVT_MENU, self.parent.on_btn_add_fit, m_new)

        m_delete = menu_edit.Append(-1, "&Delete interpretation\tCtrl-D", "")
        self.Bind(wx.EVT_MENU, self.parent.on_btn_delete_fit, m_delete)

        m_next_interp = menu_edit.Append(-1, "&Next interpretation\tCtrl-Up", "")
        self.Bind(wx.EVT_MENU, self.parent.on_menu_next_interp, m_next_interp)

        m_previous_interp = menu_edit.Append(-1, "&Previous interpretation\tCtrl-Down", "")
        self.Bind(wx.EVT_MENU, self.parent.on_menu_prev_interp, m_previous_interp)

        m_next_specimen = menu_edit.Append(-1, "&Next Specimen\tCtrl-Right", "")
        self.Bind(wx.EVT_MENU, self.parent.on_next_button, m_next_specimen)

        m_previous_specimen = menu_edit.Append(-1, "&Previous Specimen\tCtrl-Left", "")
        self.Bind(wx.EVT_MENU, self.parent.on_prev_button, m_previous_specimen)

        menu_coordinates = wx.Menu()

        m_speci = menu_coordinates.Append(-1, "&Specimen Coordinates\tCtrl-P", "")
        self.Bind(wx.EVT_MENU, self.parent.on_menu_change_speci_coord, m_speci)
        if "geographic" in self.parent.coordinate_list:
            m_geo = menu_coordinates.Append(-1, "&Geographic Coordinates\tCtrl-G", "")
            self.Bind(wx.EVT_MENU, self.parent.on_menu_change_geo_coord, m_geo)
        if "tilt-corrected" in self.parent.coordinate_list:
            m_tilt = menu_coordinates.Append(-1, "&Tilt-Corrected Coordinates\tCtrl-T", "")
            self.Bind(wx.EVT_MENU, self.parent.on_menu_change_tilt_coord, m_tilt)

        m_coords = menu_edit.AppendSubMenu(menu_coordinates, "&Coordinate Systems")

        #--------------------------------------------------------------------

        #self.menubar.Append(menu_preferences, "& Preferences")
        menubar.Append(menu_file, "&File")
        menubar.Append(menu_edit, "&Edit")
        menubar.Append(menu_Analysis, "&Analysis")
        menubar.Append(menu_Tools, "&Tools")
        menubar.Append(menu_Help, "&Help")
        self.SetMenuBar(menubar)

    ################################Logger Functions##################################

    def update_editor(self):
        """
        updates the logger and plot on the interpretation editor window
        """

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

        coordinate_system = self.parent.COORDINATE_SYSTEM
        fit = tup[0]
        pars = fit.get(coordinate_system)
        fmin,fmax,n,ftype,dec,inc,mad,dang,a95,sk,sr2 = "","","","","","","","","","",""

        specimen = tup[1]
        if coordinate_system=='geographic':
            block_key = 'zijdblock_geo'
        elif coordinate_system=='tilt-corrected':
            block_key = 'zijdblock_tilt'
        else:
            block_key = 'zijdblock'

        name = fit.name
        if pars == {} and self.parent.Data[specimen][block_key] != []:
            fit.put(specimen, coordinate_system, self.parent.get_PCA_parameters(specimen,fit,fit.tmin,fit.tmax,coordinate_system,fit.PCA_type))
            pars = fit.get(coordinate_system)
        if self.parent.Data[specimen][block_key]==[]:
            spars = fit.get('specimen')
            fmin = fit.tmin
            fmax = fit.tmax
            if 'specimen_n' in list(spars.keys()): n = str(spars['specimen_n'])
            else: n = 'No Data'
            if 'calculation_type' in list(spars.keys()): ftype = spars['calculation_type']
            else: ftype = 'No Data'
            dec = 'No Data'
            inc = 'No Data'
            mad = 'No Data'
            dang = 'No Data'
            a95 = 'No Data'
            sk = 'No Data'
            sr2 = 'No Data'
        else:
            if 'measurement_step_min' in list(pars.keys()): fmin = str(fit.tmin)
            else: fmin = "N/A"
            if 'measurement_step_max' in list(pars.keys()): fmax = str(fit.tmax)
            else: fmax = "N/A"
            if 'specimen_n' in list(pars.keys()): n = str(pars['specimen_n'])
            else: n = "N/A"
            if 'calculation_type' in list(pars.keys()): ftype = pars['calculation_type']
            else: ftype = "N/A"
            if 'specimen_dec' in list(pars.keys()): dec = "%.1f"%pars['specimen_dec']
            else: dec = "N/A"
            if 'specimen_inc' in list(pars.keys()): inc = "%.1f"%pars['specimen_inc']
            else: inc = "N/A"
            if 'specimen_mad' in list(pars.keys()): mad = "%.1f"%pars['specimen_mad']
            else: mad = "N/A"
            if 'specimen_dang' in list(pars.keys()): dang = "%.1f"%pars['specimen_dang']
            else: dang = "N/A"
            if 'specimen_alpha95' in list(pars.keys()): a95 = "%.1f"%pars['specimen_alpha95']
            else: a95 = "N/A"
            if 'specimen_k' in list(pars.keys()): sk = "%.1f"%pars['specimen_k']
            else: sk = "N/A"
            if 'specimen_r' in list(pars.keys()): sr2 = "%.1f"%pars['specimen_r']
            else: sr2 = "N/A"

        if self.search_query != "":
            entry = (specimen+name+fmin+fmax+n+ftype+dec+inc+mad+dang+a95+sk+sr2).replace(" ","").lower()
            if self.search_query not in entry:
                self.fit_list.pop(i)
                if i < self.logger.GetItemCount():
                    self.logger.DeleteItem(i)
                return "s"
        for e in (specimen,name,fmin,fmax,n,ftype,dec,inc,mad,dang,a95,sk,sr2):
            if e not in self.search_choices:
                self.search_choices.append(e)

        if i < self.logger.GetItemCount():
            self.logger.DeleteItem(i)
        self.logger.InsertItem(i, str(specimen))
        self.logger.SetItem(i, 1, name)
        self.logger.SetItem(i, 2, fmin)
        self.logger.SetItem(i, 3, fmax)
        self.logger.SetItem(i, 4, n)
        self.logger.SetItem(i, 5, ftype)
        self.logger.SetItem(i, 6, dec)
        self.logger.SetItem(i, 7, inc)
        self.logger.SetItem(i, 8, mad)
        self.logger.SetItem(i, 9, dang)
        self.logger.SetItem(i, 10, a95)
        self.logger.SetItem(i, 11, sk)
        self.logger.SetItem(i, 12, sr2)
        self.logger.SetItemBackgroundColour(i,"WHITE")
        a,b = False,False
        if fit in self.parent.bad_fits:
            self.logger.SetItemBackgroundColour(i,"red")
            b = True
        if self.parent.current_fit == fit:
            self.logger.SetItemBackgroundColour(i,"LIGHT BLUE")
            self.logger_focus(i)
            self.current_fit_index = i
            a = True
        if a and b:
            self.logger.SetItemBackgroundColour(i,"red")

    def update_current_fit_data(self):
        """
        updates the current_fit of the parent Zeq_GUI entry in the case of it's data being changed
        """
        if self.current_fit_index:
            self.update_logger_entry(self.current_fit_index)

    def change_selected(self,new_fit):
        """
        updates passed in fit or index as current fit for the editor (does not affect parent),
        if no parameters are passed in it sets first fit as current
        @param: new_fit -> fit object to highlight as selected
        """
        if len(self.fit_list)==0: return
        if self.search_query and self.parent.current_fit not in [x[0] for x in self.fit_list]: return
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
            print(('cannot select fit of type: ' + str(type(new_fit))))
        if self.current_fit_index != None and \
        len(self.fit_list) > 0 and \
        self.fit_list[self.current_fit_index][0] in self.parent.bad_fits:
            self.logger.SetItemBackgroundColour(self.current_fit_index,"")
        else:
            self.logger.SetItemBackgroundColour(self.current_fit_index,"WHITE")
        self.current_fit_index = i
        if self.fit_list[self.current_fit_index][0] in self.parent.bad_fits:
            self.logger.SetItemBackgroundColour(self.current_fit_index,"red")
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
        self.parent.initialize_CART_rot(self.fit_list[i][1])
        si = self.parent.specimens.index(self.fit_list[i][1])
        self.parent.specimens_box.SetSelection(si)
        self.parent.select_specimen(self.fit_list[i][1])
        self.change_selected(i)
        fi = 0
        while (self.parent.s == self.fit_list[i][1] and i >= 0): i,fi = (i-1,fi+1)
        self.parent.update_fit_box()
        self.parent.fit_box.SetSelection(fi-1)
        self.parent.update_selection()

    def OnRightClickListctrl(self, event):
        """
        Edits the logger and the Zeq_GUI parent object so that the selected interpretation is now marked as bad
        @param: event -> wx.ListCtrlEvent that triggered this function
        """
        i = event.GetIndex()
        fit,spec = self.fit_list[i][0],self.fit_list[i][1]
        if fit in self.parent.bad_fits:
            if not self.parent.mark_fit_good(fit,spec=spec): return
            if i == self.current_fit_index:
                self.logger.SetItemBackgroundColour(i,"LIGHT BLUE")
            else:
                self.logger.SetItemBackgroundColour(i,"WHITE")
        else:
            if not self.parent.mark_fit_bad(fit): return
            if i == self.current_fit_index:
                self.logger.SetItemBackgroundColour(i,"red")
            else:
                self.logger.SetItemBackgroundColour(i,"red")
        self.parent.calculate_high_levels_data()
        self.parent.plot_high_levels_data()
        self.logger_focus(i)

    ##################################Search Bar Functions###############################

    def on_enter_search_bar(self,event):
        self.search_query = self.search_bar.GetValue().replace(" ","").lower()
        self.update_editor()

#    def on_complete_search_bar(self,event):
#        self.search_bar.AutoComplete(self.search_choices)

    ###################################ComboBox Functions################################

    def update_bounds_boxes(self,B_list):
        self.tmin_box.SetItems(B_list)
        self.tmax_box.SetItems(B_list)

    def add_new_color(self,event):
        new_color = self.color_box.GetValue()
        if ':' in new_color:
            color_list = new_color.split(':')
            color_name = color_list[0]
            if len(color_list[1])==7 and color_list[1].startswith('#'):
                for c in color_list[1][1:]:
                    if ord(c) < 48 or ord(c) > 70:
                        self.parent.user_warning('invalid hex color must be of form #0F0F0F');return
                color_val = color_list[1]
            elif '(' in color_list[1] and ')' in color_list[1]:
                color_val = list(map(eval, tuple(color_list[1].strip('( )').split(','))))
                for val in color_val:
                    if val > 1 or val < 0: self.parent.user_warning("invalid RGB sequence"); return
            else: self.parent.user_warning("colors must be given as a valid hex color or rgb tuple"); return
        else:
            self.parent.user_warning("New colors must be passed in as $colorname:$colorval where $colorval is a valid hex color or rgb tuple"); return
        self.color_dict[color_name] = color_val
        #clear old box
        self.color_box.Clear()
        #update fit box
        self.color_box.SetItems([''] + sorted(self.color_dict.keys()))

    def on_select_coordinates(self,event):
        self.parent.coordinates_box.SetStringSelection(self.coordinates_box.GetStringSelection())
        self.parent.onSelect_coordinates(event)

    def on_select_show_box(self,event):
        """
        Changes the type of mean shown on the high levels mean plot so that single dots represent one of whatever the value of this box is.
        @param: event -> the wx.COMBOBOXEVENT that triggered this function
        """
        self.parent.UPPER_LEVEL_SHOW=self.show_box.GetValue()
        self.parent.calculate_high_levels_data()
        self.parent.plot_high_levels_data()


    def on_select_high_level(self,event,called_by_parent=False):
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
            self.parent.onSelect_high_level(event,True)

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

        self.specimens_list.sort(key=spec_key_func)
        self.update_editor()

    def on_select_mean_type_box(self, event):
        """
        set parent Zeq_GUI to reflect change in this box and change the
        @param: event -> the wx.ComboBoxEvent that triggered this function
        """
        new_mean_type = self.mean_type_box.GetValue()
        if new_mean_type == "None":
            self.parent.clear_high_level_pars()
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
        self.parent.update_high_level_stats()

    def add_highlighted_fits(self, evnet):
        """
        adds a new interpretation to each specimen highlighted in logger if multiple interpretations are highlighted of the same specimen only one new interpretation is added
        @param: event -> the wx.ButtonEvent that triggered this function
        """

        specimens = []
        next_i = self.logger.GetNextSelected(-1)
        if next_i == -1: return
        while next_i != -1:
            fit,specimen = self.fit_list[next_i]
            if specimen in specimens:
                next_i = self.logger.GetNextSelected(next_i)
                continue
            else: specimens.append(specimen)
            next_i = self.logger.GetNextSelected(next_i)

        for specimen in specimens:
            self.add_fit_to_specimen(specimen)

        self.update_editor()
        self.parent.update_selection()

    def add_fit_to_all(self,event):
        for specimen in self.parent.specimens:
            self.add_fit_to_specimen(specimen)

        self.update_editor()
        self.parent.update_selection()

    def add_fit_to_specimen(self,specimen):
        if specimen not in self.parent.pmag_results_data['specimens']:
            self.parent.pmag_results_data['specimens'][specimen] = []

        new_name = self.name_box.GetLineText(0)
        new_color = self.color_box.GetValue()
        new_tmin = self.tmin_box.GetValue()
        new_tmax = self.tmax_box.GetValue()

        if not new_name:
            next_fit = str(len(self.parent.pmag_results_data['specimens'][specimen]) + 1)
            while ("Fit " + next_fit) in [x.name for x in self.parent.pmag_results_data['specimens'][specimen]]:
                next_fit = str(int(next_fit) + 1)
            new_name = ("Fit " + next_fit)
        if not new_color:
            next_fit = str(len(self.parent.pmag_results_data['specimens'][specimen]) + 1)
            new_color = self.parent.colors[(int(next_fit)-1) % len(self.parent.colors)]
        else: new_color = self.color_dict[new_color]
        if not new_tmin: new_tmin = None
        if not new_tmax: new_tmax = None

        if new_name in [x.name for x in self.parent.pmag_results_data['specimens'][specimen]]:
            print(('-E- interpretation called ' + new_name + ' already exsists for specimen ' + specimen))
            return

        self.parent.add_fit(specimen, new_name, new_tmin, new_tmax, color=new_color,suppress_warnings=True)

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
        deleted_items.sort(reverse=True)
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
            print(("cannot remove item (entry #: " + str(index) + ") as it doesn't exist, this is a dumb bug contact devs"))
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
                if new_name not in [x.name for x in self.parent.pmag_results_data['specimens'][specimen]]: fit.name = new_name
            if new_color:
                fit.color = self.color_dict[new_color]
            #testing
            not_both = True
            if new_tmin and new_tmax:
                if fit == self.parent.current_fit:
                    self.parent.tmin_box.SetStringSelection(new_tmin)
                    self.parent.tmax_box.SetStringSelection(new_tmax)
                fit.put(specimen,self.parent.COORDINATE_SYSTEM, self.parent.get_PCA_parameters(specimen,fit,new_tmin,new_tmax,self.parent.COORDINATE_SYSTEM,fit.PCA_type))
                not_both = False
            if new_tmin and not_both:
                if fit == self.parent.current_fit:
                    self.parent.tmin_box.SetStringSelection(new_tmin)
                fit.put(specimen,self.parent.COORDINATE_SYSTEM, self.parent.get_PCA_parameters(specimen,fit,new_tmin,fit.tmax,self.parent.COORDINATE_SYSTEM,fit.PCA_type))
            if new_tmax and not_both:
                if fit == self.parent.current_fit:
                    self.parent.tmax_box.SetStringSelection(new_tmax)
                fit.put(specimen,self.parent.COORDINATE_SYSTEM, self.parent.get_PCA_parameters(specimen,fit,fit.tmin,new_tmax,self.parent.COORDINATE_SYSTEM,fit.PCA_type))
            changed_i.append(next_i)

        offset = 0
        for i in changed_i:
            i -= offset
            v = self.update_logger_entry(i)
            if v == "s":
                offset += 1

        self.parent.update_selection()

    ###################################Canvas Functions##################################

    def scatter(self,*args,**kwargs):
#        args_corrected = self.eqarea.transAxes.transform(vstack(args).T)
#        x,y = args_corrected.T
        return self.eqarea.scatter(*args,**kwargs)

    def plot(self,*args,**kwargs):
#        args_corrected = self.eqarea.transAxes.transform(vstack(args).T)
#        x,y = args_corrected.T
        return self.eqarea.plot(*args,**kwargs)

    def write(self,text):
        return self.eqarea.text(-1.2,1.15,text,{'family':self.font_type, 'fontsize':10*self.GUI_RESOLUTION, 'style':'normal','va':'center', 'ha':'left' })

    def draw_net(self):
        draw_net(self.eqarea)

    def draw(self):
        self.toolbar.home()
        self.eqarea.set_xlim(-1., 1.)
        self.eqarea.set_ylim(-1., 1.)
        self.eqarea.axes.set_aspect('equal')
        self.eqarea.axis('off')
        self.canvas.draw()

    def pan_zoom_high_equalarea(self,event):
        """
        Uses the toolbar for the canvas to change the function from zoom to pan or pan to zoom
        @param: event -> the wx.MouseEvent that triggered this funciton
        """
        if event.LeftIsDown() or event.ButtonDClick():
            return
        elif self.high_EA_setting == "Zoom":
            self.high_EA_setting = "Pan"
            try: self.toolbar.pan('off')
            except TypeError: pass
        elif self.high_EA_setting == "Pan":
            self.high_EA_setting = "Zoom"
            try: self.toolbar.zoom()
            except TypeError: pass
        else:
            self.high_EA_setting = "Zoom"
            try: self.toolbar.zoom()
            except TypeError: pass

    def home_high_equalarea(self,event):
        """
        returns high equal area to it's original position
        @param: event -> the wx.MouseEvent that triggered the call of this function
        @alters: toolbar setting
        """
        self.toolbar.home()

    def on_change_high_mouse_cursor(self,event):
        """
        If mouse is over data point making it selectable change the shape of the cursor
        @param: event -> the wx Mouseevent for that click
        """
        if self.show_box.GetValue() != "specimens": return
        if not self.parent.high_EA_xdata or not self.parent.high_EA_ydata: return
        pos=event.GetPosition()
        width, height = self.canvas.get_width_height()
        pos[1] = height - pos[1]
        xpick_data,ypick_data = pos
        xdata_org = self.parent.high_EA_xdata
        ydata_org = self.parent.high_EA_ydata
        data_corrected = self.eqarea.transData.transform(vstack([xdata_org,ydata_org]).T)
        xdata,ydata = data_corrected.T
        xdata = list(map(float,xdata))
        ydata = list(map(float,ydata))
        e = 4e0

        if self.high_EA_setting == "Zoom":
            self.canvas.SetCursor(wx.Cursor(wx.CURSOR_CROSS))
        else:
            self.canvas.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
        for i,(x,y) in enumerate(zip(xdata,ydata)):
            if 0 < sqrt((x-xpick_data)**2. + (y-ypick_data)**2.) < e:
                self.canvas.SetCursor(wx.Cursor(wx.CURSOR_HAND))
                break
        event.Skip()

    def on_equalarea_high_select(self,event):
        self.parent.on_equalarea_high_select(event,fig = self.eqarea, canvas = self.canvas)

    ###############################Menu Functions######################################

    def on_menu_help(self,event):
        """
        Toggles the GUI's help mode which allows user to click on any part of the dialog and get help
        @param: event -> wx.MenuEvent that triggers this function
        """
        self.helper.BeginContextHelp(None)

    ###############################Window Functions######################################

    def on_close_edit_window(self, event):
        """
        the function that is triggered on the close of the interpretation editor window
        @param: event -> wx.WindowEvent that triggered this function
        """

        self.parent.ie_open = False
        self.Destroy()

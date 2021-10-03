#!/usr/bin/env pythonw
"""
doc string
"""

# pylint: disable=C0103,E402
print('-I- Importing MagIC GUI dependencies')
import matplotlib
matplotlib.use('WXAgg')
import wx
import wx.lib.buttons as buttons
import sys
import os
from pmagpy import data_model3
from pmag_env import set_env
from pmagpy import validate_upload3 as val_up3
from pmagpy import pmag
from pmagpy import ipmag

from dialogs import pmag_widgets as pw
from dialogs import pmag_menu_dialogs
from dialogs import grid_frame3 as grid_frame
from pmagpy import contribution_builder as cb


class MainFrame(wx.Frame):
    """
    MagIC GUI
    """

    def __init__(self, WD=None, name='Main Frame', dmodel=None, title=None, contribution=None, errors={}):
        try:
            version = pmag.get_version()
        except:
            version = ""
        if not title:
            title = "MagIC GUI   version: %s" % version
        wx.Frame.__init__(self, None, wx.ID_ANY, title, name=name)
        #
        self.grid_frame = None
        self.panel = wx.Panel(self, size=wx.GetDisplaySize(), name='main panel')
        print('-I- Fetching working directory')
        self.WD = os.path.realpath(WD) or os.getcwd()

        print('-I- Initializing magic data model')
        if dmodel is None:
            dmodel = data_model3.DataModel()
        self.data_model = dmodel

        self.edited = False

        # process the errors into a nicer format
        self.errors = {}
        for table_name in ['measurements', 'specimens', 'samples',
                           'sites', 'locations', 'ages']:
            self.errors[table_name] = list(self.get_table_errors(table_name, errors))
            if not self.errors[table_name]:
                self.errors.pop(table_name)
        self.validation_mode = self.errors.keys()

        print('-I- Initializing interface')
        self.InitUI()

        print('-I- Completed interface')
        if contribution:
            self.contribution = contribution
        else:
            print("-E- Something went really wrong.  Try again or make a bug report.")

    def get_wd_data(self):
        self.edited = False
        self.validation_mode = False

        wait = wx.BusyInfo('Reading in data from current working directory, please wait...')
        wx.SafeYield()
        print('-I- Read in any available data from working directory')
        self.contribution = cb.Contribution(self.WD, dmodel=self.data_model)
        # propagate names from measurements into other tables
        if "measurements" in self.contribution.tables:
            self.contribution.propagate_measurement_info()
        # propagate names from any table into other tables
        # (i.e., site name from samples)
        self.contribution.propagate_all_tables_info()
        # extract average lats/lons from sites table
        self.contribution.get_min_max_lat_lon()
        # extract age info from ages table and put into other tables
        self.contribution.propagate_ages()
        # finish up
        self.edited = False
        del wait


    def InitUI(self):
        """
        Make main user interface
        """
        bSizer0 = wx.StaticBoxSizer(
            wx.StaticBox(self.panel, wx.ID_ANY, "Choose MagIC project directory", name='bSizer0'), wx.HORIZONTAL
        )
        self.dir_path = wx.TextCtrl(self.panel, id=-1, size=(600, 25), style=wx.TE_READONLY)
        self.dir_path.SetValue(self.WD)
        bSizer0.AddSpacer(40)
        bSizer0.Add(self.dir_path, wx.ALIGN_CENTER_VERTICAL)

        self.bSizer_msg = wx.StaticBoxSizer(wx.StaticBox(
            self.panel, wx.ID_ANY, "Message", name='bsizer_msg'),
                                            wx.HORIZONTAL)
        self.message = wx.StaticText(self.panel, -1,
                                     label="The following table(s) have incorrect or incomplete data:\nmeasurements, specimens, samples, sites, locations, ages.",
                                     name='messages', style=wx.ST_NO_AUTORESIZE)
        self.bSizer_msg.Add(self.message)

        #---sizer 1 ----
        bSizer1 = wx.StaticBoxSizer(wx.StaticBox(
            self.panel, wx.ID_ANY, "Add information to the data model", name='bSizer1'),
                                    wx.HORIZONTAL)

        text = "1. add location data"
        self.btn1 = buttons.GenButton(self.panel, id=-1, label=text,
                                      size=(300, 50), name='locations_btn')
        self.btn1.SetBackgroundColour("#FDC68A")
        self.btn1.InitColours()
        self.Bind(wx.EVT_BUTTON, self.make_grid_frame, self.btn1)

        text = "2. add site data"
        self.btn2 = buttons.GenButton(self.panel, id=-1, label=text,
                                      size=(300, 50), name='sites_btn')
        self.btn2.SetBackgroundColour("#6ECFF6")
        self.btn2.InitColours()
        self.Bind(wx.EVT_BUTTON, self.make_grid_frame, self.btn2)


        text = "3. add sample data"
        self.btn3 = buttons.GenButton(self.panel, id=-1, label=text,
                                      size=(300, 50), name='samples_btn')
        self.btn3.SetBackgroundColour("#C4DF9B")
        self.btn3.InitColours()
        self.Bind(wx.EVT_BUTTON, self.make_grid_frame, self.btn3)


        text = "4. add specimen data"
        self.btn4 = buttons.GenButton(self.panel, id=-1,
                                      label=text, size=(300, 50), name='specimens_btn')
        self.btn4.SetBackgroundColour("#FDC68A")
        self.btn4.InitColours()
        self.Bind(wx.EVT_BUTTON, self.make_grid_frame, self.btn4)


        text = "5. add age data"
        self.btn5 = buttons.GenButton(self.panel, id=-1, label=text,
                                      size=(300, 50), name='ages_btn')
        self.btn5.SetBackgroundColour("#6ECFF6")
        self.btn5.InitColours()
        self.Bind(wx.EVT_BUTTON, self.make_grid_frame, self.btn5)

        text = "6. add measurements data"
        self.btn6 = buttons.GenButton(self.panel, id=-1, label=text,
                                      size=(300, 50), name='measurements_btn')
        self.btn6.SetBackgroundColour("#C4DF9B")
        self.btn6.InitColours()
        self.Bind(wx.EVT_BUTTON, self.make_grid_frame, self.btn6)

        bsizer1a = wx.BoxSizer(wx.VERTICAL)
        bsizer1a.AddSpacer(20)
        bsizer1a.Add(self.btn1, wx.ALIGN_TOP)
        bsizer1a.AddSpacer(20)
        bsizer1a.Add(self.btn2, wx.ALIGN_TOP)
        bsizer1a.AddSpacer(20)
        bsizer1a.Add(self.btn3, wx.ALIGN_TOP)
        bsizer1a.AddSpacer(20)

        bSizer1.Add(bsizer1a, wx.ALIGN_CENTER, wx.EXPAND)
        bSizer1.AddSpacer(20)

        #bSizer1.Add(OR, 0, wx.ALIGN_CENTER, 0)
        bSizer1.AddSpacer(20)
        bsizer1b = wx.BoxSizer(wx.VERTICAL)
        #__init__(self, parent, id, label, pos, size, style, validator, name
        bsizer1b.Add(self.btn4, flag=wx.ALIGN_CENTER|wx.BOTTOM, border=20)
        bsizer1b.Add(self.btn5, 0, flag=wx.ALIGN_CENTER|wx.BOTTOM, border=20)
        bsizer1b.Add(self.btn6, 0, wx.ALIGN_CENTER, 0)
        bSizer1.Add(bsizer1b, 0, wx.ALIGN_CENTER, 0)
        bSizer1.AddSpacer(20)

        #---sizer 2 ----

        self.bSizer2 = wx.StaticBoxSizer(wx.StaticBox(self.panel, wx.ID_ANY, "Return to main GUI", name='bSizer2'), wx.HORIZONTAL)
        self.return_btn = buttons.GenButton(self.panel, id=-1, label="Return to Pmag GUI",
                                        size=(300, 50), name='return_btn')
        self.return_btn.SetBackgroundColour("#C4DF9B")
        self.bSizer2.Add(self.return_btn, 0, wx.ALIGN_CENTER, 0)
        self.bSizer2.AddSpacer(20)


        #---arrange sizers ----

        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.AddSpacer(5)
        #vbox.Add(self.logo,0,wx.ALIGN_CENTER,0)
        vbox.AddSpacer(5)
        vbox.Add(bSizer0, 0, wx.ALIGN_CENTER, 0)
        vbox.AddSpacer(10)
        #vbox.Add(bSizer0_1, 0, wx.ALIGN_CENTER, 0)
        #vbox.AddSpacer(10)
        vbox.Add(self.bSizer_msg, 0, wx.ALIGN_CENTER, 0)
        #self.bSizer_msg.ShowItems(False)
        vbox.Add(bSizer1, 0, wx.ALIGN_CENTER, 0)
        vbox.AddSpacer(10)
        vbox.AddSpacer(10)
        self.hbox.AddSpacer(10)
        vbox.Add(self.bSizer2, 0, wx.ALIGN_CENTER, 0)
        vbox.AddSpacer(10)

        self.hbox.Add(vbox, 0, wx.ALIGN_CENTER, 0)
        self.hbox.AddSpacer(5)

        self.panel.SetSizer(self.hbox)
        self.hbox.Fit(self)

        # do menu
        print("-I- Initializing menu")
        menubar = MagICMenu(self)
        self.SetMenuBar(menubar)
        self.menubar = menubar


    def on_open_grid_frame(self):
        self.Hide()

    def on_close_grid_frame(self, event=None):
        if self.grid_frame != None and self.grid_frame.grid.changes:
            self.edited = True
        # we used to re-run partial validations here, but since we're now doing this
        # on the server, that's not going to work
        if self.grid_frame.error_frame:
            self.grid_frame.error_frame.Destroy()
        self.grid_frame = None
        try: self.Show()
        except RuntimeError: pass
        if event:
            event.Skip()

    def make_grid_frame(self, event):
        """
        Create a GridFrame for data type of the button that was clicked
        """
        if self.grid_frame:
            print('-I- You already have a grid frame open')
            pw.simple_warning("You already have a grid open")
            return

        try:
            grid_type = event.GetButtonObj().Name[:-4] # remove '_btn'
        except AttributeError:
            grid_type = self.FindWindowById(event.Id).Name[:-4] # remove ('_btn')
        wait = wx.BusyInfo('Making {} grid, please wait...'.format(grid_type))
        wx.SafeYield()
        # propagate site lat/lon info into locations if necessary
        if grid_type == 'locations' and 'sites' in self.contribution.tables:
            self.contribution.get_min_max_lat_lon()
            self.contribution.propagate_cols_up(['lithologies',
                                                 'geologic_classes'],
                                                'locations', 'sites')
        # propagate lithologies/type/class information from sites to samples/specimens
        if grid_type in ['specimens', 'samples']:
            self.contribution.propagate_lithology_cols()
        # propagate average lat/lon info from samples table if
        # available in samples and missing in sites
        if grid_type == 'sites':
            self.contribution.propagate_average_up(cols=['lat', 'lon', 'height'],
                                           target_df_name='sites',
                                           source_df_name='samples')
            self.contribution.propagate_lithology_cols()
        # hide mainframe
        self.on_open_grid_frame()
        # choose appropriate size for grid
        if grid_type == 'measurements':
            huge = True
        else:
            huge = False
        # make grid frame
        self.grid_frame = grid_frame.GridFrame(self.contribution, self.WD,
                                               grid_type, grid_type,
                                               self.panel, huge=huge)
        # paint validations if appropriate
        if self.validation_mode:
            if grid_type in self.validation_mode:
                if grid_type == 'measurements':
                    skip_cell_render = True
                else:
                    skip_cell_render = False
                self.grid_frame.toggle_help(None, "open")
                # put all the errors into the help message box
                if len(self.errors[grid_type]) > 20:
                    text = "\n".join([dic['message'] for dic in self.errors[grid_type][:20]])
                    text += "\nNote: There were too many errors to fit in this interface."
                    text += "\nPlease check your Terminal/Command Prompt for the rest.\n"
                else:
                    text = "\n".join([dic['message'] for dic in self.errors[grid_type]])
                self.grid_frame.msg_text.SetLabel(text)
                self.grid_frame.help_msg_boxsizer.Fit(self.grid_frame.help_msg_boxsizer.GetStaticBox())
                self.grid_frame.main_sizer.Fit(self.grid_frame)
                # paint boxes around the problem cells
                for err in self.errors[grid_type]:
                    col_name = err['column']
                    try:
                        col_ind = self.grid_frame.grid.col_labels.index(col_name)
                    except ValueError:
                        continue
                    rows = err['rows']
                    for row in rows:
                        self.grid_frame.grid.paint_invalid_cell(row - 1, col_ind,
                                                                skip_cell=skip_cell_render)
            else:
                self.grid_frame.msg_text.SetLabel("No problems here. Hooray!")
                self.grid_frame.help_msg_boxsizer.Fit(self.grid_frame.help_msg_boxsizer.GetStaticBox())
                self.grid_frame.main_sizer.Fit(self.grid_frame)

        self.grid_frame.do_fit(None)
        del wait


    def get_table_errors(self, table, errors):
        """
        Input: table name (i.e., specimens)
               errors (errors as formatted from upload_magic validation)
        """
        for error_dict in errors:
            if error_dict['table'] == table:
                yield error_dict

    def highlight_problems(self):
        """
        Outline grid buttons in red if they have validation errors
        """
        if self.validation_mode:
            self.message.SetLabel('The following table(s) have incorrect or incomplete data:\n{}'.format(', '.join(self.validation_mode)))
            #self.bSizer_msg.ShowItems(True)
        else:
            self.message.SetLabel("No errors here!")
            self.bSizer_msg.ShowItems(True)
        self.hbox.Fit(self)


class MagICMenu(wx.MenuBar):
    """
    initialize menu bar for GUI
    """
    #pylint: disable=R0904
    #pylint: disable=R0914
    def __init__(self, parent):
        self.parent = parent
        super(MagICMenu, self).__init__()

        file_menu = wx.Menu()
        file_quit = file_menu.Append(wx.ID_EXIT, 'Quit', 'Quit application')
        self.file_quit = file_quit
        file_clear = file_menu.Append(wx.ID_ANY, 'Clear directory', 'Delete all files from working directory')
        #file_help = file_menu.Append(wx.ID_ANY, 'Help', 'More information about creating a MagIC contribution')
        file_show = file_menu.Append(wx.ID_ANY, 'Show main window', 'Show main window')
        file_close_grid = file_menu.Append(wx.ID_ANY, 'Close current grid', 'Close current grid')
        parent.Bind(wx.EVT_MENU, self.on_quit, file_quit)
        parent.Bind(wx.EVT_MENU, self.on_clear, file_clear)
        #parent.Bind(wx.EVT_MENU, self.on_help, file_help)
        parent.Bind(wx.EVT_MENU, self.on_show_mainframe, file_show)
        parent.Bind(wx.EVT_MENU, self.on_close_grid, file_close_grid)
        self.Append(file_menu, 'File')

        help_menu = wx.Menu()
        help_cookbook = help_menu.Append(wx.ID_ANY, '&PmagPy Cookbook\tCtrl-Shift-H',
                                         'Access the online documentation')
        help_git = help_menu.Append(wx.ID_ANY, '&Github Page\tCtrl-Shift-G',
                                    'Access the PmagPy repository')
        parent.Bind(wx.EVT_MENU, pw.on_cookbook, help_cookbook)
        parent.Bind(wx.EVT_MENU, pw.on_git, help_git)
        if pw.get_output_frame():
            help_show = help_menu.Append(wx.ID_ANY, 'Show output', 'Show help')
            help_hide = help_menu.Append(wx.ID_ANY, 'Hide output', 'Hide output')
            parent.Bind(wx.EVT_MENU, pw.on_show_output, help_show)
            parent.Bind(wx.EVT_MENU, pw.on_hide_output, help_hide)
        self.Append(help_menu, 'Help ')

    def on_quit(self, event):
        """
        shut down application
        """
        if self.parent.grid_frame:
            if self.parent.grid_frame.grid.changes:
                dlg = wx.MessageDialog(self,caption="Message:", message="Are you sure you want to exit the program?\nYou have a grid open with unsaved changes.\n ", style=wx.OK|wx.CANCEL)
                result = dlg.ShowModal()
                if result == wx.ID_OK:
                    dlg.Destroy()
                else:
                    dlg.Destroy()
                    return
        if self.parent.grid_frame:
            self.parent.grid_frame.Destroy()
            return
        self.parent.Close()
        try:
            sys.exit()
        except TypeError:
            pass

    def on_clear(self, event):
        """
        initialize window to allow user to empty the working directory
        """
        dia = pmag_menu_dialogs.ClearWD(self.parent, self.parent.WD)
        clear = dia.do_clear()
        if clear:
            print('-I- Clear data object')
            self.contribution = cb.Contribution(self.WD, dmodel=self.data_model)
            self.edited = False



    #def on_help(self, event):
    #    """
    #    point user to Cookbook help
    #    """
    #    #for use on the command line
    #    path = find_pmag_dir.get_pmag_dir()
    #
    #    # for use with pyinstaller:
    #    #path = self.Parent.resource_dir
    #
    #    html_frame = pw.HtmlFrame(self, page=(os.path.join(path, "documentation", #"magic_gui.html")))
    #    html_frame.Center()
    #    html_frame.Show()

    def on_show_mainframe(self, event):
        """
        Show main magic_gui window
        """
        self.parent.Show()
        self.parent.Raise()

    def on_close_grid(self, event):
        """
        If there is an open grid, save its data and close it.
        """
        if self.parent.grid_frame:
            self.parent.grid_frame.onSave(None)
            self.parent.grid_frame.Destroy()

def main():
    if '-h' in sys.argv:
        help_msg = """
MagIC GUI is for creating and uploading contributions to the MagIC database.
Note: if you are starting with a measurement file, it is better to use
Pmag GUI instead.
MagIC GUI is mainly meant for contributions with specimen-level data and higher.

SYNTAX
    magic_gui.py [command line options]
    # or, for Anaconda users:
    magic_gui_anaconda [command line options]

OPTIONS
    -WD DIR: working directory, default current directory

EXAMPLE
    magic_gui.py -WD projects/my_project

INFORMATION
    See https://earthref.org/PmagPy/cookbook/#magic_gui.py for a complete tutorial
"""
        print(help_msg)
        sys.exit()
    print('-I- Starting MagIC GUI - please be patient')

    # if redirect is true, wxpython makes its own output window for stdout/stderr
    if 'darwin' in sys.platform and (not set_env.IS_FROZEN):
        app = wx.App(redirect=False)
    else:
        app = wx.App(redirect=True)

    working_dir = pmag.get_named_arg('-WD', '')
    app.frame = MainFrame(working_dir)
    app.frame.Show()
    app.frame.Center()
    ## use for debugging:
    #if '-i' in sys.argv:
    #    import wx.lib.inspection
    #    wx.lib.inspection.InspectionTool().Show()
    app.MainLoop()



if __name__ == "__main__":
    main()

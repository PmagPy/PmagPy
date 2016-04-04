"""
dialogs for ErMagicBuilder
"""
# pylint: disable=W0612,C0111,C0103,W0201,C0301
import wx
import wx.grid
#import sys
import os
import drop_down_menus
import pmag_widgets as pw
import magic_grid
import grid_frame
import pmagpy.check_updates as check_updates


class ErMagicCheckFrame(wx.Frame):

    def __init__(self, parent, title, WD, magic_data): # magic_data was ErMagic
        wx.Frame.__init__(self, parent, -1, title)
        self.WD = WD
        self.main_frame = self.Parent
        self.er_magic_data = magic_data
        self.er_magic_data.no_pmag_data = set(['specimen', 'sample', 'site', 'location'])

        self.temp_data = {}
        self.drop_down_menu = None
        # sample window must be displayed (differently) twice, so it is useful to keep track
        self.sample_window = 0
        self.grid = None
        self.deleteRowButton = None
        self.selected_rows = set()
        self.InitSpecCheck()


    def InitSpecCheck(self):
        """make an interactive grid in which users can edit specimen names
        as well as which sample a specimen belongs to"""

        self.panel = wx.Panel(self, style=wx.SIMPLE_BORDER)
        #import wx.lib.scrolledpanel as libpanel # does not work well
        #self.panel = libpanel.ScrolledPanel(self, style=wx.SIMPLE_BORDER)

        text = """Step 1:
Check that all specimens belong to the correct sample
(if sample name is simply wrong, that will be fixed in step 2)"""
        label = wx.StaticText(self.panel, label=text)
        self.grid_builder = grid_frame.GridBuilder(self.er_magic_data, 'specimen',
                                                   self.er_magic_data.headers, self.panel,
                                                   'sample')
        self.spec_grid = self.grid_builder.make_grid(incl_pmag=False)
        self.grid = self.spec_grid

        self.spec_grid.InitUI()

        self.grid_builder.add_data_to_grid(self.spec_grid, 'specimen', incl_pmag=False)

        samples = self.er_magic_data.make_name_list(self.er_magic_data.samples)
        self.drop_down_menu = drop_down_menus.Menus("specimen", self, self.spec_grid, samples)


        #### Create Buttons ####
        hbox_one = wx.BoxSizer(wx.HORIZONTAL)
        self.addSampleButton = wx.Button(self.panel, label="Add a new sample")
        self.samples = [name for name in self.er_magic_data.samples]
        self.Bind(wx.EVT_BUTTON, self.on_addSampleButton, self.addSampleButton)
        self.helpButton = wx.Button(self.panel, label="Help")
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_helpButton(event, "ErMagicSpecimenHelp.html"), self.helpButton)
        hbox_one.Add(self.addSampleButton, flag=wx.ALIGN_LEFT|wx.RIGHT, border=10)
        hbox_one.Add(self.helpButton)

        #
        hboxok = wx.BoxSizer(wx.HORIZONTAL)
        self.saveButton = wx.Button(self.panel, id=-1, label='Save')
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_saveButton(event, self.spec_grid), self.saveButton)
        self.cancelButton = wx.Button(self.panel, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)
        self.continueButton = wx.Button(self.panel, id=-1, label='Save and continue')
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_continueButton(event, self.spec_grid, next_dia=self.InitSampCheck), self.continueButton)

        hboxok.Add(self.saveButton, flag=wx.ALIGN_LEFT|wx.RIGHT, border=10)
        hboxok.Add(self.cancelButton, flag=wx.ALIGN_LEFT|wx.RIGHT, border=10)
        hboxok.Add(self.continueButton, flag=wx.ALIGN_LEFT)

        #
        hboxgrid = pw.hbox_grid(self.panel, self.onDeleteRow, 'specimen', self.grid)
        self.deleteRowButton = hboxgrid.deleteRowButton

        self.panel.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.onLeftClickLabel, self.grid)

        ### Create Containers ###
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.AddSpacer(10)
        vbox.Add(label, flag=wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, border=10)

        vbox.Add(hbox_one, flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=10)
        vbox.Add(hboxok, flag=wx.BOTTOM|wx.LEFT, border=10)
        vbox.Add(hboxgrid, flag=wx.BOTTOM|wx.LEFT, border=10)
        vbox.Add(self.spec_grid, flag=wx.ALL, border=10)#|wx.EXPAND, border=30)
        vbox.AddSpacer(20)

        hbox_all = wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.AddSpacer(vbox)
        hbox_all.AddSpacer(20)

        self.panel.SetSizer(hbox_all)
        #self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Centre()
        self.Show()
        self.Hide()
        self.Show()


    def InitSampCheck(self):
        """make an interactive grid in which users can edit sample names
        as well as which site a sample belongs to"""
        self.sample_window += 1
        self.panel = wx.Panel(self, style=wx.SIMPLE_BORDER)

        if self.sample_window == 1:
            text = """Step 2:
Check that all samples are correctly named,
and that they belong to the correct site
(if site name is simply wrong, that will be fixed in step 3)"""
            step_label = wx.StaticText(self.panel, label=text)#, size=(900, 100))
        else:
            text = """Step 4:
Some of the data from the er_sites table has propogated into er_samples.
Check that these data are correct, and fill in missing cells using controlled vocabularies.
The columns for class, lithology, and type can take multiple values in the form of a colon-delimited list.
You may use the drop-down menus to add as many values as needed in these columns.  
(see Help button for more details)\n\n** Denotes controlled vocabulary"""
            step_label = wx.StaticText(self.panel, label=text)#, size=(900, 100))
        
        if self.sample_window == 1:
            # provide no extra headers
            headers = {'sample': {'er': [[], [], []],
                                  'pmag': [[], [], []]}}
            self.grid_builder = grid_frame.GridBuilder(self.er_magic_data, 'sample',
                                                       headers, self.panel,
                                                       'site')

        if self.sample_window > 1:
            self.grid_builder = grid_frame.GridBuilder(self.er_magic_data, 'sample',
                                           self.er_magic_data.headers, self.panel,
                                           'site')

        self.samp_grid = self.grid_builder.make_grid(incl_pmag=False)
        self.samp_grid.InitUI()
        self.grid_builder.add_data_to_grid(self.samp_grid, 'sample', incl_pmag=False)
        self.grid = self.samp_grid

        sites = sorted(self.er_magic_data.make_name_list(self.er_magic_data.sites))
        self.drop_down_menu = drop_down_menus.Menus("sample", self, self.samp_grid, sites) # initialize all needed drop-down menus

        ### Create Buttons ###
        hbox_one = wx.BoxSizer(wx.HORIZONTAL)
        self.addSiteButton = wx.Button(self.panel, label="Add a new site")
        self.Bind(wx.EVT_BUTTON, self.on_addSiteButton, self.addSiteButton)
        hbox_one.Add(self.addSiteButton, flag=wx.RIGHT, border=10)
        if self.sample_window == 1:
            html_help = "ErMagicSampleHelp1.html"
        if self.sample_window > 1:
            html_help = "ErMagicSampleHelp.html"
        self.helpButton = wx.Button(self.panel, label="Help")
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_helpButton(event, html_help), self.helpButton)
        hbox_one.Add(self.helpButton)

        hboxok = wx.BoxSizer(wx.HORIZONTAL)
        self.saveButton = wx.Button(self.panel, id=-1, label='Save')
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_saveButton(event, self.samp_grid), self.saveButton)
        self.cancelButton = wx.Button(self.panel, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)
        self.continueButton = wx.Button(self.panel, id=-1, label='Save and continue')
        next_dia = self.InitSiteCheck if self.sample_window < 2 else self.InitLocCheck
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_continueButton(event, self.samp_grid, next_dia=next_dia), self.continueButton)
        self.backButton = wx.Button(self.panel, wx.ID_ANY, "&Back")
        previous_dia = self.InitSpecCheck if self.sample_window < 2 else self.InitSiteCheck
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_backButton(event, previous_dia=previous_dia), self.backButton)

        hboxok.Add(self.saveButton, flag=wx.RIGHT, border=10)
        hboxok.Add(self.cancelButton, flag=wx.RIGHT, border=10)
        hboxok.Add(self.continueButton, flag=wx.RIGHT, border=10)
        hboxok.Add(self.backButton)

        hboxgrid = pw.hbox_grid(self.panel, self.onDeleteRow, 'sample', self.grid)
        self.deleteRowButton = hboxgrid.deleteRowButton

        self.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.onLeftClickLabel, self.grid)
        
        ### Make Containers ###
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(step_label, flag=wx.ALIGN_LEFT|wx.TOP|wx.BOTTOM, border=20)

        vbox.Add(hbox_one, flag=wx.BOTTOM|wx.LEFT, border=10)
        vbox.Add(hboxok, flag=wx.BOTTOM|wx.LEFT, border=10)
        vbox.Add(hboxgrid, flag=wx.BOTTOM|wx.LEFT, border=10)
        vbox.Add(self.samp_grid, flag=wx.ALL, border=10) # using wx.EXPAND or not does not affect re-size problem
        vbox.AddSpacer(20)

        hbox_all = wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.AddSpacer(vbox)
        hbox_all.AddSpacer(20)

        self.panel.SetSizer(hbox_all)
        #if sys.platform in ['win32', 'win64']:
        #    self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)

        self.Centre()
        self.Show()

        ## this combination may prevent a display error that (without the fix) only resolves on manually resizing the window
        self.panel.Refresh()
        self.samp_grid.ForceRefresh()
        self.panel.Refresh()
        self.Refresh()

        # this prevents display errors
        self.Hide()
        self.Show()

        #self.Fit() # this make it worse!
        #self.Layout() # doesn't fix display resize error

        #self.panel.Layout() # doesn't fix display resize error
        #self.main_frame.Layout()# doesn't fix display resize error


    def InitSiteCheck(self):
        """make an interactive grid in which users can edit site names
        as well as which location a site belongs to"""
        self.panel = wx.Panel(self, style=wx.SIMPLE_BORDER)

        text = """Step 3:
Check that all sites are correctly named, and that they belong to the correct location.
Fill in the additional columns with controlled vocabularies.
The columns for class, lithology, and type can take multiple values in the form of a colon-delimited list.
You may use the drop-down menus to add as many values as needed in these columns.  
(see the help button for more details)
note: Changes to site_class, site_lithology, or site_type will overwrite er_samples.txt
However, you will be able to edit sample_class, sample_lithology, and sample_type in step 4

**Denotes controlled vocabulary"""
        label = wx.StaticText(self.panel, label=text)
        #self.Data_hierarchy = self.ErMagic.Data_hierarchy
        self.sites = sorted(self.er_magic_data.make_name_list(self.er_magic_data.sites))

        #for val in ['er_citation_names', 'er_location_name', 'er_site_name', 'site_class', 'site_lithology', 'site_type', 'site_definition', 'site_lat', 'site_lon']: #
        #    try:
        #        self.er_magic_data.headers['site']['er'][0].remove(val)
        #    except ValueError:
        #        pass

        self.grid_builder = grid_frame.GridBuilder(self.er_magic_data, 'site',
                               self.er_magic_data.headers, self.panel,
                               'location')

        self.site_grid = self.grid_builder.make_grid(incl_pmag=False)
        self.site_grid.InitUI()
        self.grid_builder.add_data_to_grid(self.site_grid, 'site', incl_pmag=False)
        self.grid = self.site_grid

        # populate site_definition as 's' by default if no value is provided (indicates that site is single, not composite)
        rows = self.site_grid.GetNumberRows()
        col = 6
        for row in range(rows):
            cell = self.site_grid.GetCellValue(row, col)
            if not cell:
                self.site_grid.SetCellValue(row, col, 's')

        # initialize all needed drop-down menus
        locations = sorted(self.er_magic_data.make_name_list(self.er_magic_data.locations))
        self.drop_down_menu = drop_down_menus.Menus("site", self, self.site_grid, locations)

        ### Create Buttons ###
        hbox_one = wx.BoxSizer(wx.HORIZONTAL)
        self.addLocButton = wx.Button(self.panel, label="Add a new location")

        self.Bind(wx.EVT_BUTTON, self.on_addLocButton, self.addLocButton)
        hbox_one.Add(self.addLocButton, flag=wx.RIGHT, border=10)

        self.helpButton = wx.Button(self.panel, label="Help")
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_helpButton(event, "ErMagicSiteHelp.html"), self.helpButton)
        hbox_one.Add(self.helpButton)

        hboxok = wx.BoxSizer(wx.HORIZONTAL)
        self.saveButton = wx.Button(self.panel, id=-1, label='Save')
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_saveButton(event, self.site_grid), self.saveButton)
        self.cancelButton = wx.Button(self.panel, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)
        self.continueButton = wx.Button(self.panel, id=-1, label='Save and continue')
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_continueButton(event, self.site_grid, next_dia=self.InitSampCheck), self.continueButton)
        self.backButton = wx.Button(self.panel, wx.ID_ANY, "&Back")
        previous_dia = self.InitSampCheck
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_backButton(event, previous_dia=previous_dia), self.backButton)

        hboxok.Add(self.saveButton, flag=wx.RIGHT, border=10)
        hboxok.Add(self.cancelButton, flag=wx.RIGHT, border=10)
        hboxok.Add(self.continueButton, flag=wx.RIGHT, border=10)
        hboxok.Add(self.backButton)

        #
        hboxgrid = pw.hbox_grid(self.panel, self.onDeleteRow, 'site', self.grid)
        self.deleteRowButton = hboxgrid.deleteRowButton

        self.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.onLeftClickLabel, self.grid)


        ### Make Containers ###
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(label, flag=wx.ALIGN_CENTER|wx.BOTTOM|wx.TOP, border=20)
        vbox.Add(hbox_one, flag=wx.BOTTOM|wx.LEFT, border=10)
        vbox.Add(hboxok, flag=wx.BOTTOM|wx.LEFT, border=10)
        vbox.Add(hboxgrid, flag=wx.BOTTOM|wx.LEFT, border=10)
        vbox.Add(self.site_grid, flag=wx.ALL|wx.EXPAND, border=10) # EXPAND ??
        vbox.AddSpacer(20)

        hbox_all = wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.AddSpacer(vbox)
        hbox_all.AddSpacer(20)

        self.panel.SetSizer(hbox_all)
        #if sys.platform in ['win32', 'win64']:
        #    self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Centre()
        self.Show()
        # this combination prevents a display error that (without the fix) only resolves on manually resizing the window
        self.site_grid.ForceRefresh()
        self.panel.Refresh()
        self.Hide()
        self.Show()



    def InitLocCheck(self):
        """make an interactive grid in which users can edit specimen names
        as well as which sample a specimen belongs to"""
        self.panel = wx.Panel(self, style=wx.SIMPLE_BORDER)

        text = """Step 5:
Check that locations are correctly named.
Fill in any blank cells using controlled vocabularies.
(See Help button for details)

** Denotes controlled vocabulary"""
        label = wx.StaticText(self.panel, label=text)
        #self.Data_hierarchy = self.ErMagic.Data_hierarchy
        self.locations = self.er_magic_data.locations
        #
        if not self.er_magic_data.locations:
            msg = "You have no data in er_locations, so we are skipping step 5.\n Note that location names must be entered at the measurements level,so you may need to re-import your data, or you can add a location in step 3"
            dlg = wx.MessageDialog(None, caption="Message:", message=msg, style=wx.OK|wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.panel.Destroy()
            self.InitAgeCheck()
            return

        self.grid_builder = grid_frame.GridBuilder(self.er_magic_data, 'location',
                                                   self.er_magic_data.headers, self.panel)
        self.loc_grid = self.grid_builder.make_grid(incl_pmag=False)
        self.loc_grid.InitUI()
        self.grid_builder.add_data_to_grid(self.loc_grid, 'location', incl_pmag=False)
        self.grid = self.loc_grid
        # initialize all needed drop-down menus
        self.drop_down_menu = drop_down_menus.Menus("location", self, self.loc_grid, None)

        # need to find max/min lat/lon here IF they were added in the previous grid
        sites = self.er_magic_data.sites
        location_lat_lon = self.er_magic_data.get_min_max_lat_lon(self.er_magic_data.locations)

        col_names = ('location_begin_lat', 'location_end_lat', 'location_begin_lon', 'location_end_lon')
        col_inds = [self.grid.col_labels.index(name) for name in col_names]
        col_info = zip(col_names, col_inds)
        for loc in self.er_magic_data.locations:
            row_ind = self.grid.row_labels.index(loc.name)
            for col_name, col_ind in col_info:
                info = location_lat_lon[loc.name][col_name]
                self.grid.SetCellValue(row_ind, col_ind, str(info))

        ### Create Buttons ###
        hbox_one = wx.BoxSizer(wx.HORIZONTAL)
        self.helpButton = wx.Button(self.panel, label="Help")
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_helpButton(event, "ErMagicLocationHelp.html"), self.helpButton)
        hbox_one.Add(self.helpButton)

        hboxok = wx.BoxSizer(wx.HORIZONTAL)
        self.saveButton = wx.Button(self.panel, id=-1, label='Save')
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_saveButton(event, self.loc_grid), self.saveButton)
        self.cancelButton = wx.Button(self.panel, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)
        self.continueButton = wx.Button(self.panel, id=-1, label='Save and continue')
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_continueButton(event, self.loc_grid, next_dia=self.InitAgeCheck), self.continueButton)
        self.backButton = wx.Button(self.panel, wx.ID_ANY, "&Back")
        previous_dia = self.InitSampCheck
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_backButton(event, previous_dia, current_dia=self.InitLocCheck), self.backButton)

        hboxok.Add(self.saveButton, flag=wx.RIGHT, border=10)
        hboxok.Add(self.cancelButton, flag=wx.RIGHT, border=10)
        hboxok.Add(self.continueButton, flag=wx.RIGHT, border=10)
        hboxok.Add(self.backButton)

        #
        hboxgrid = pw.hbox_grid(self.panel, self.onDeleteRow, 'location', self.grid)
        self.deleteRowButton = hboxgrid.deleteRowButton

        self.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.onLeftClickLabel, self.grid)


        ### Make Containers ###
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(label, flag=wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, border=20)
        vbox.Add(hbox_one, flag=wx.BOTTOM|wx.ALIGN_LEFT, border=10)
        vbox.Add(hboxok, flag=wx.BOTTOM|wx.ALIGN_LEFT, border=10)
        vbox.Add(hboxgrid, flag=wx.BOTTOM|wx.ALIGN_LEFT, border=10)
        vbox.Add(self.loc_grid, flag=wx.TOP|wx.BOTTOM, border=10)
        vbox.AddSpacer(20)

        hbox_all = wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.AddSpacer(vbox)
        hbox_all.AddSpacer(20)

        self.panel.SetSizer(hbox_all)
        #if sys.platform in ['win32', 'win64']:
        #    self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Centre()
        self.Show()
        self.Hide()
        self.Show()


    def InitAgeCheck(self):
        """make an interactive grid in which users can edit ages"""
        self.panel = wx.Panel(self, style=wx.SIMPLE_BORDER)

        text = """Step 6:
Fill in or correct any cells with information about ages.
The column for magic_method_codes can take multiple values in the form of a colon-delimited list.
You may use the drop-down menus to add as many values as needed in these columns.  
(See Help button for details)

**Denotes controlled vocabulary """
        label = wx.StaticText(self.panel, label=text)

        self.items = self.er_magic_data.data_lists[self.er_magic_data.age_type][0]

        self.grid_builder = grid_frame.GridBuilder(self.er_magic_data, 'age',
                                                   self.er_magic_data.headers, self.panel, 'location')
        self.age_grid = self.grid_builder.make_grid(incl_pmag=False)
        self.age_grid.InitUI()
        self.grid_builder.add_data_to_grid(self.age_grid, 'age', incl_pmag=False)
        self.grid_builder.add_age_data_to_grid()
        
        self.grid = self.age_grid
        #
        # make it impossible to edit the 1st and 3rd columns
        for row in range(self.age_grid.GetNumberRows()):
            for col in (0, 2):
                self.age_grid.SetReadOnly(row, col, True)

        # initialize all needed drop-down menus
        self.drop_down_menu = drop_down_menus.Menus("age", self, self.age_grid, None)

        # re-set first column name
        self.age_grid.SetColLabelValue(0, 'er_site_name')

        ### Create Buttons ###
        hbox_one = wx.BoxSizer(wx.HORIZONTAL)
        self.helpButton = wx.Button(self.panel, label="Help")
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_helpButton(event, "ErMagicAgeHelp.html"), self.helpButton)
        hbox_one.Add(self.helpButton)

        hboxok = wx.BoxSizer(wx.HORIZONTAL)
        self.saveButton = wx.Button(self.panel, id=-1, label='Save')
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_saveButton(event, self.age_grid), self.saveButton)
        self.cancelButton = wx.Button(self.panel, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)
        self.continueButton = wx.Button(self.panel, id=-1, label='Save and continue')
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_continueButton(event, self.age_grid, next_dia=None), self.continueButton)
        self.backButton = wx.Button(self.panel, wx.ID_ANY, "&Back")
        previous_dia = self.InitLocCheck
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_backButton(event, previous_dia), self.backButton)

        self.panel.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.onLeftClickLabel, self.grid)

        hboxok.Add(self.saveButton, flag=wx.RIGHT, border=10)
        hboxok.Add(self.cancelButton, flag=wx.RIGHT, border=10)
        hboxok.Add(self.continueButton, flag=wx.RIGHT, border=10)
        hboxok.Add(self.backButton)

        ### Make Containers ###
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(label, flag=wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, border=20)#, flag=wx.ALIGN_LEFT|wx.BOTTOM, border=20)
        vbox.Add(hbox_one, flag=wx.BOTTOM, border=10)
        vbox.Add(hboxok, flag=wx.BOTTOM, border=10)
        vbox.Add(self.age_grid, flag=wx.TOP|wx.BOTTOM, border=10) # EXPAND ??
        vbox.AddSpacer(20)

        hbox_all = wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.AddSpacer(vbox)
        hbox_all.AddSpacer(20)

        self.panel.SetSizer(hbox_all)
        #if sys.platform in ['win32', 'win64']:
        #    self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Centre()
        self.Show()
        self.Hide()
        self.Show()


    ### Grid methods ###
    def make_simple_table(self, column_labels, data_dict, grid_name):
        row_labels = sorted(data_dict.keys())
        if len(row_labels) in range(1, 4):
            num_rows = len(row_labels)
            height = {1: 70, 2: 90, 3: 110, 4: 130}
            grid = magic_grid.MagicGrid(self.panel, grid_name, row_labels, column_labels, (-1, height[num_rows])) # autosizes width, but enforces fixed pxl height to prevent display problems
        else:
            grid = magic_grid.MagicGrid(self.panel, grid_name, row_labels, column_labels)

        data = grid.InitUI()

        if grid_name == 'ages':
            temp_data_key = 'ages'
        else:
            temp_data_key = column_labels[0]
        self.temp_data[temp_data_key] = data

        grid.add_data(data_dict)

        grid.size_grid()

        grid.do_event_bindings()
        return grid

    def onMouseOver(self, event, grid):
        """
        Displays a tooltip over any cell in a certain column
        """
        x, y = grid.CalcUnscrolledPosition(event.GetX(), event.GetY())
        coords = grid.XYToCell(x, y)
        col = coords[1]
        row = coords[0]

        # creates tooltip message for cells with long values
        # note: this works with EPD for windows, and modern wxPython, but not with Canopy Python
        msg = grid.GetCellValue(row, col)
        if len(msg) > 15:
            event.GetEventObject().SetToolTipString(msg)
        else:
            event.GetEventObject().SetToolTipString('')

    def validate(self, grid):
        validations = ['er_specimen_name', 'er_sample_name', 'er_site_name', 'er_location_name', 'site_class', 'site_lithology', 'site_type', 'site_definition', 'site_lon', 'site_lat', 'sample_class', 'sample_lithology', 'sample_type', 'sample_lat', 'sample_lon', 'location_type', 'age_unit', 'age']#, 'magic_method_codes']
        cols = range(grid.GetNumberCols())
        rows = range(grid.GetNumberRows())
        data_missing = []
        for col in cols:
            col_label = str(grid.GetColLabelValue(col))
            if col_label in validations:
                for row in rows:
                    value = grid.GetCellValue(row, col)
                    if not value:
                        data_missing.append(col_label)
                        break
        return data_missing


    ### Button methods ###

    def on_addSampleButton(self, event):

        def add_sample(sample, site):
            add_sample_data(sample, site)

        sites = self.er_magic_data.make_name_list(self.er_magic_data.sites)
        pw.AddItem(self, 'Sample', add_sample, owner_items=sites, belongs_to='site') # makes window for adding new data

        def add_sample_data(sample, site):
            # add sample
            self.er_magic_data.add_sample(sample, site)
            # re-Bind so that the updated samples list shows up on a left click
            samples = sorted(self.er_magic_data.make_name_list(self.er_magic_data.samples))
            choices = self.drop_down_menu.choices
            choices[1] = (samples, False)
            self.drop_down_menu.update_drop_down_menu(self.spec_grid, choices)


    def on_addSiteButton(self, event):

        def add_site(site, location):
            add_site_data(site, location)

        locations = self.er_magic_data.make_name_list(self.er_magic_data.locations)
        pw.AddItem(self, 'Site', add_site, locations, 'location')

        def add_site_data(site, location):
            # add site
            self.er_magic_data.add_site(site, location)
            # re-Bind so that the updated sites list shows up on a left click
            sites = sorted(self.er_magic_data.make_name_list(self.er_magic_data.sites))
            self.drop_down_menu.update_drop_down_menu(self.samp_grid, {1: (sites, False)})


    def on_addLocButton(self, event):

        def add_loc(loc):
            add_loc_data(loc)

        #def __init__(self, parent, title, data_items, data_method):

        if not self.er_magic_data.locations:
            pass

        pw.AddItem(self, 'Location', add_loc, owner_items=None, belongs_to=None) # makes window for adding new data

        def add_loc_data(loc):
            # add location
            self.er_magic_data.add_location(loc)
            # re-Bind so that the updated locations list shows up on a left click
            locations = self.er_magic_data.make_name_list(self.er_magic_data.locations)
            choices = self.drop_down_menu.choices
            choices[1] = (locations, False)
            self.drop_down_menu.update_drop_down_menu(self.site_grid, choices)

    def on_helpButton(self, event, page=None):
        """shows html help page"""
        # for use on the command line:
        path = check_updates.get_pmag_dir()
        # for use with pyinstaller
        #path = self.main_frame.resource_dir
        help_page = os.path.join(path, 'dialogs', 'help_files', page)
        # if using with py2app, the directory structure is flat,
        # so check to see where the resource actually is
        if not os.path.exists(help_page):
            help_page = os.path.join(path, 'help_files', page)
        html_frame = pw.HtmlFrame(self, page=help_page)
        html_frame.Show()

    def on_continueButton(self, event, grid, next_dia=None):
        """
        pulls up next dialog, if there is one.
        gets any updated information from the current grid and runs ErMagicBuilder
        """
        #wait = wx.BusyInfo("Please wait, working...")

        # unhighlight selected columns, etc.
        if self.drop_down_menu:
            self.drop_down_menu.clean_up()

        # remove '**' from col names
        #self.remove_starred_labels(grid)
        grid.remove_starred_labels()

        grid.SaveEditControlValue() # locks in value in cell currently edited
        grid_name = str(grid.GetName())

        # check that all required data are present
        validation_errors = self.validate(grid)
        if validation_errors:
            result = pw.warning_with_override("You are missing required data in these columns: {}\nAre you sure you want to continue without these data?".format(', '.join(validation_errors)))
            if result == wx.ID_YES:
                pass
            else:
                return False

        if grid.changes:
            self.onSave(grid)

        self.deleteRowButton = None
        self.panel.Destroy()

        # make sure that specimens get propagated with
        # any default sample info
        if next_dia == self.InitLocCheck:
            if self.er_magic_data.specimens:
                for spec in self.er_magic_data.specimens:
                    spec.propagate_data()
        
        if next_dia:
            wait = wx.BusyInfo("Please wait, working...")
            wx.Yield()
            next_dia()
            del wait
        else:
            wait = wx.BusyInfo("Please wait, writing data to files...")
            wx.Yield()
            # actually write data:
            self.er_magic_data.write_files()
            self.Destroy()
            del wait


    def on_saveButton(self, event, grid):
        """saves any editing of the grid but does not continue to the next window"""
        wait = wx.BusyInfo("Please wait, working...")
        wx.Yield()

        if self.drop_down_menu:  # unhighlight selected columns, etc.
            self.drop_down_menu.clean_up()

        # remove '**' from col labels
        starred_cols = grid.remove_starred_labels()

        grid.SaveEditControlValue() # locks in value in cell currently edited
        grid.HideCellEditControl() # removes focus from cell that was being edited

        if grid.changes:
            self.onSave(grid)

        for col in starred_cols:
            label = grid.GetColLabelValue(col)
            grid.SetColLabelValue(col, label + '**')
        del wait

    def on_cancelButton(self, event):

        dlg = pw.YesNoCancelDialog(self, "Your changes so far have not been written to file.\nSave changes?", "Not so fast")
        res = dlg.ShowModal()
        dlg.Destroy()
        if res == wx.ID_YES:
            self.onSave(self.grid)
            self.er_magic_data.write_files()
            self.Destroy()
        if res == wx.ID_NO:
            self.Destroy()
        if res == wx.ID_CANCEL:
            pass

    def on_backButton(self, event, previous_dia, current_dia=None):
        wait = wx.BusyInfo("Please wait, working...")
        wx.Yield()
        if current_dia == self.InitLocCheck:
            pass
        elif previous_dia == self.InitSpecCheck or previous_dia == self.InitSampCheck:
            self.sample_window = 0
        self.panel.Destroy()
        previous_dia()
        del wait


    def onDeleteRow(self, event, data_type):
        """
        On button click, remove relevant object from both the data model and the grid.
        """
        ancestry = self.er_magic_data.ancestry
        child_type = ancestry[ancestry.index(data_type) - 1]
        names = [self.grid.GetCellValue(row, 0) for row in self.selected_rows]
        if data_type == 'site':
            how_to_fix = 'Make sure to select a new site for each orphaned sample in the next step'
        else:
            how_to_fix = 'Go back a step and select a new {} for each orphaned {}'.format(data_type, child_type)

        orphans = []
        for name in names:
            row = self.grid.row_labels.index(name)
            orphan = self.er_magic_data.delete_methods[data_type](name)
            if orphan:
                orphans.extend(orphan)
            self.grid.remove_row(row)
        if orphans:
            orphan_names = self.er_magic_data.make_name_list(orphans)
            pw.simple_warning('You have deleted:\n\n  {}\n\nthe parent(s) of {}(s):\n\n  {}\n\n{}'.format(', '.join(names), child_type, ', '.join(orphan_names), how_to_fix))

        self.selected_rows = set()

        # update grid and data model
        self.update_grid(self.grid)#, grids[grid_name])

        self.grid.Refresh()


    def onLeftClickLabel(self, event):
        """
        When user clicks on a grid label, determine if it is a row label or a col label.
        Pass along the event to the appropriate function.
        (It will either highlight a column for editing all values, or highlight a row for deletion).
        """
        if event.Col == -1 and event.Row == -1:
            pass
        elif event.Col < 0:
            self.onSelectRow(event)
        elif event.Row < 0:
            self.drop_down_menu.on_label_click(event)


    def onSelectRow(self, event):
        """
        Highlight or unhighlight a row for possible deletion.
        """
        grid = self.grid
        row = event.Row
        default = (255, 255, 255, 255)
        highlight = (191, 216, 216, 255)
        cell_color = grid.GetCellBackgroundColour(row, 0)
        attr = wx.grid.GridCellAttr()
        if cell_color == default:
            attr.SetBackgroundColour(highlight)
            self.selected_rows.add(row)
        else:
            attr.SetBackgroundColour(default)
            try:
                self.selected_rows.remove(row)
            except KeyError:
                pass
        if self.selected_rows and self.deleteRowButton:
            self.deleteRowButton.Enable()
        else:
            self.deleteRowButton.Disable()
        grid.SetRowAttr(row, attr)
        grid.Refresh()

    ### Manage data methods ###
    def update_grid(self, grid):
        """
        takes in wxPython grid and ErMagic data object to be updated
        """
        data_methods = {'specimen': self.er_magic_data.change_specimen,
                        'sample': self.er_magic_data.change_sample,
                        'site': self.er_magic_data.change_site,
                        'location': self.er_magic_data.change_location,
                        'age': self.er_magic_data.change_age}

        grid_name = str(grid.GetName())

        cols = range(grid.GetNumberCols())

        col_labels = []
        for col in cols:
            col_labels.append(grid.GetColLabelValue(col))

        for row in grid.changes: # go through changes and update data structures
            if row == -1:
                continue
            else:
                data_dict = {}
                for num, label in enumerate(col_labels):
                    if label:
                        data_dict[str(label)] = str(grid.GetCellValue(row, num))
                new_name = str(grid.GetCellValue(row, 0))
                old_name = self.temp_data[grid_name][row]
                data_methods[grid_name](new_name, old_name, data_dict)

        grid.changes = False


    def onSave(self, grid):#, age_data_type='site'):
        """
        Save grid data in the data object
        """
        # deselect column, including remove 'EDIT ALL' label
        if self.drop_down_menu:
            self.drop_down_menu.clean_up()

        # save all changes to er_magic data object
        self.grid_builder.save_grid_data()

        # don't actually write data in this step (time-consuming)
        # instead, write to files when user is done editing
        #self.er_magic_data.write_files()

        wx.MessageBox('Saved!', 'Info',
                      style=wx.OK | wx.ICON_INFORMATION)

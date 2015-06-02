import wx
import sys
import drop_down_menus
import pmag_widgets as pw

class ErMagicCheck(wx.Frame):

    def __init__(self, parent, id, title, WD, magic_data): # magic_data was ErMagic
        wx.Frame.__init__(self, parent, -1, title)
        self.WD = WD
        self.main_frame = self.Parent
        self.ErMagic = magic_data
        self.temp_data = {}
        self.drop_down_menu = None
        self.sample_window = 0 # sample window must be displayed (differently) twice, so it is useful to keep track
        self.InitSpecCheck()
        

    def InitSpecCheck(self):
        """make an interactive grid in which users can edit specimen names
        as well as which sample a specimen belongs to"""
        self.ErMagic.read_MagIC_info() # 

        # using ScrolledWindow works on up to date wxPython and is necessary for windows
        # it breaks with Canopy wxPython, so for Mac we just use Panel

        if sys.platform in ['win32', 'win64']:
            self.panel = wx.ScrolledWindow(self, style=wx.SIMPLE_BORDER)
        else:
            self.panel = wx.Panel(self, style=wx.SIMPLE_BORDER)

        #import wx.lib.scrolledpanel as libpanel # does not work well
        #self.panel = libpanel.ScrolledPanel(self, style=wx.SIMPLE_BORDER)

        TEXT = """Step 1:
Check that all specimens belong to the correct sample
(if sample name is simply wrong, that will be fixed in step 2)"""
        label = wx.StaticText(self.panel,label=TEXT)
        self.Data_hierarchy = self.ErMagic.Data_hierarchy
        self.specimens = sorted(self.Data_hierarchy['specimens'].keys())
        samples = self.Data_hierarchy['samples'].keys()
        samples = sorted(list(set(samples).union(self.ErMagic.data_er_samples.keys()))) # adds in any additional samples we might have information about (from er_samples.txt file) even if currently that sample does not show up in the magic_measurements file

        # create the grid and also a record of the initial values for specimens/samples as a reference
        # to tell if we've had any changes

        col_labels = self.ErMagic.data_er_specimens[self.ErMagic.data_er_specimens.keys()[0]].keys()
        for val in ['er_citation_names', 'er_location_name', 'er_site_name', 'er_sample_name', 'er_specimen_name', 'specimen_class', 'specimen_lithology', 'specimen_type']: #
            col_labels.remove(val)
        col_labels = sorted(col_labels)
        col_labels[:0] = ['specimens', '', 'er_sample_name']

        self.spec_grid = self.make_simple_table(col_labels, self.ErMagic.data_er_specimens, "specimen")

        self.changes = False

        self.Bind(wx.grid.EVT_GRID_EDITOR_CREATED, lambda event: self.on_edit_grid(event, self.spec_grid), self.spec_grid) # if user begins to edit, self.changes will be set to True
        self.drop_down_menu = drop_down_menus.Menus("specimen", self, self.spec_grid, samples) # initialize all needed drop-down menus


        #### Create Buttons ####
        hbox_one = wx.BoxSizer(wx.HORIZONTAL)
        self.addSampleButton = wx.Button(self.panel, label="Add a new sample")
        self.sites = list(set(self.Data_hierarchy['sites'].keys()).union(self.ErMagic.data_er_sites.keys())) # adds in any additional samples we might have information about (from er_sites.txt file) even if currently that sample does not show up in the magic_measurements file
        self.Bind(wx.EVT_BUTTON, self.on_addSampleButton, self.addSampleButton)
        self.helpButton = wx.Button(self.panel, label="Help")
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_helpButton(event, "ErMagicSpecimenHelp.html"), self.helpButton)
        hbox_one.Add(self.addSampleButton, flag=wx.ALIGN_LEFT|wx.RIGHT, border=10)
        hbox_one.Add(self.helpButton)

        #
        hboxok = wx.BoxSizer(wx.HORIZONTAL)
        self.saveButton =  wx.Button(self.panel, id=-1, label='Save')
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_saveButton(event, self.spec_grid), self.saveButton)
        self.cancelButton = wx.Button(self.panel, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)
        self.continueButton = wx.Button(self.panel, id=-1, label='Save and continue')
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_continueButton(event, self.spec_grid, next_dia=self.InitSampCheck), self.continueButton)
        hboxok.Add(self.saveButton, flag=wx.ALIGN_LEFT|wx.RIGHT, border=10)
        hboxok.Add(self.cancelButton, flag=wx.ALIGN_LEFT|wx.RIGHT, border=10) 
        hboxok.Add(self.continueButton, flag=wx.ALIGN_LEFT )


        ### Create Containers ###
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.AddSpacer(10)
        vbox.Add(label, flag=wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, border=10)

        vbox.Add(hbox_one, flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=10)
        vbox.Add(hboxok, flag=wx.BOTTOM|wx.LEFT, border=10)
        vbox.Add(self.spec_grid, flag=wx.ALL, border=10)#|wx.EXPAND, border=30)
        
        hbox_all= wx.BoxSizer(wx.HORIZONTAL)
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
        
        ## this combination prevents a display error that (without the fix) only resolves on manually resizing the window
        #print "about to refresh spec_grid"
        #print self.panel
        #print self.spec_grid
        #self.panel.Refresh()
        #self.spec_grid.ForceRefresh()
        #self.panel.Refresh()
        #print "refreshed spec_grid"



    def InitSampCheck(self):
        """make an interactive grid in which users can edit sample names
        as well as which site a sample belongs to"""
        
        self.sample_window += 1 

        # using ScrolledWindow works on up to date wxPython and is necessary for windows
        # it breaks with Canopy wxPython, so for Mac we just use Panel
        if sys.platform in ['win32', 'win64']:
            self.panel = wx.ScrolledWindow(self, style=wx.SIMPLE_BORDER)
        else:
            self.panel = wx.Panel(self, style=wx.SIMPLE_BORDER)

        if self.sample_window == 1:
            TEXT = """Step 2:
Check that all samples are correctly named,
and that they belong to the correct site
(if site name is simply wrong, that will be fixed in step 3)"""
            step_label = wx.StaticText(self.panel,label=TEXT)#, size=(900, 100))
        else:
            self.ErMagic.read_MagIC_info() # ensures that changes from step 3 propagate
            TEXT = """Step 4:
Some of the data from the er_sites table has propogated into er_samples.
Check that this data is correct, and fill in missing cells using controlled vocabularies.
The columns for class, lithology, and type can take multiple values in the form of a colon-delimited list.
You may use the drop-down menus to add as many values as needed in these columns.  
(see Help button for more details)\n\n** Denotes controlled vocabulary"""
            step_label = wx.StaticText(self.panel,label=TEXT)#, size=(900, 100))
        self.Data_hierarchy = self.ErMagic.Data_hierarchy
        self.samples = sorted(self.Data_hierarchy['samples'].keys())
        sites = sorted(self.Data_hierarchy['sites'].keys())
        self.locations = sorted(list(set(self.Data_hierarchy['locations'].keys()).union(self.ErMagic.data_er_locations.keys())))

        if self.sample_window == 1:
            self.samp_grid = self.make_simple_table(['samples', '', 'er_site_name'], self.ErMagic.data_er_samples, 'sample')
            
        if self.sample_window > 1:
            col_labels = self.ErMagic.data_er_samples[self.ErMagic.data_er_samples.keys()[0]].keys()
            for val in ['er_citation_names', 'er_location_name', 'er_site_name', 'er_sample_name', 'sample_class', 'sample_lithology', 'sample_type', 'sample_lat', 'sample_lon']:
                col_labels.remove(val)
            col_labels = sorted(col_labels)
            col_labels[:0] = ['samples', '', 'er_site_name', 'sample_class', 'sample_lithology', 'sample_type', 'sample_lat', 'sample_lon']
            self.samp_grid = self.make_simple_table(col_labels, self.ErMagic.data_er_samples, 'sample')

        self.changes = False
        self.Bind(wx.grid.EVT_GRID_EDITOR_CREATED, lambda event: self.on_edit_grid(event, self.samp_grid), self.samp_grid)
        sites = sorted(list(set(sites).union(self.ErMagic.data_er_sites.keys()))) # adds in any additional sets we might have information about (from er_sites.txt file) even if currently that site does not show up in the magic_measurements file
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
        self.saveButton =  wx.Button(self.panel, id=-1, label='Save')
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
        hboxok.Add(self.cancelButton, flag=wx.RIGHT, border=10 )
        hboxok.Add(self.continueButton, flag=wx.RIGHT, border=10 )
        hboxok.Add(self.backButton)


        ### Make Containers ###
        vbox = wx.BoxSizer(wx.VERTICAL)
        #vbox.Add(step_label, flag=wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, border=20)
        vbox.Add(step_label, flag=wx.ALIGN_LEFT|wx.TOP|wx.BOTTOM, border=20)

        vbox.Add(hbox_one, flag=wx.BOTTOM|wx.LEFT, border=10)
        vbox.Add(hboxok, flag=wx.BOTTOM|wx.LEFT, border=10)
        vbox.Add(self.samp_grid, flag=wx.ALL, border=10) # using wx.EXPAND or not does not affect re-size problem

        hbox_all= wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.AddSpacer(vbox)
        hbox_all.AddSpacer(20)

        self.panel.SetSizer(hbox_all)
        if sys.platform in ['win32', 'win64']:
            self.panel.SetScrollbars(20, 20, 50, 50)
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

        # using ScrolledWindow works on up to date wxPython and is necessary for windows
        # it breaks with Canopy wxPython, so for Mac we just use Panel
        if sys.platform in ['win32', 'win64']:
            self.panel = wx.ScrolledWindow(self, style=wx.SIMPLE_BORDER)
        else:
            self.panel = wx.Panel(self, style=wx.SIMPLE_BORDER)

        TEXT = """Step 3:
Check that all sites are correctly named, and that they belong to the correct location.
Fill in the additional columns with controlled vocabularies.
The columns for class, lithology, and type can take multiple values in the form of a colon-delimited list.
You may use the drop-down menus to add as many values as needed in these columns.  
(see the help button for more details)
note: Changes to site_class, site_lithology, or site_type will overwrite er_samples.txt
However, you will be able to edit sample_class, sample_lithology, and sample_type in step 4

**Denotes controlled vocabulary"""
        label = wx.StaticText(self.panel,label=TEXT)
        self.Data_hierarchy = self.ErMagic.Data_hierarchy
        self.sites = sorted(self.Data_hierarchy['sites'].keys())

        col_labels = self.ErMagic.data_er_sites[self.ErMagic.data_er_sites.keys()[0]].keys()
        for val in ['er_citation_names', 'er_location_name', 'er_site_name', 'site_class', 'site_lithology', 'site_type', 'site_definition', 'site_lat', 'site_lon']: #
            col_labels.remove(val)
        col_labels = sorted(col_labels)
        col_labels[:0] = ['sites', '', 'er_location_name', 'site_class', 'site_lithology', 'site_type', 'site_definition', 'site_lon', 'site_lat']

        self.site_grid = self.make_simple_table(col_labels, self.ErMagic.data_er_sites, 'site')

        self.changes = False
        self.Bind(wx.grid.EVT_GRID_EDITOR_CREATED, lambda event: self.on_edit_grid(event, self.site_grid), self.site_grid)

        # populate site_definition as 's' by default if no value is provided (indicates that site is single, not composite)
        rows = self.site_grid.GetNumberRows()
        col = 6
        for row in range(rows):
            cell = self.site_grid.GetCellValue(row, col)
            if not cell:
                self.site_grid.SetCellValue(row, col, 's')

        locations = sorted(set(self.ErMagic.data_er_locations.keys()))
        self.drop_down_menu = drop_down_menus.Menus("site", self, self.site_grid, locations) # initialize all needed drop-down menus


        ### Create Buttons ###
        hbox_one = wx.BoxSizer(wx.HORIZONTAL)
        self.addLocButton = wx.Button(self.panel, label="Add a new location")
        self.locations = list(set(self.Data_hierarchy['sites'].keys()).union(self.ErMagic.data_er_locations.keys()))
        self.Bind(wx.EVT_BUTTON, self.on_addLocButton, self.addLocButton)
        hbox_one.Add(self.addLocButton, flag=wx.RIGHT, border=10)

        self.helpButton = wx.Button(self.panel, label="Help")
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_helpButton(event, "ErMagicSiteHelp.html"), self.helpButton)
        hbox_one.Add(self.helpButton)

        hboxok = wx.BoxSizer(wx.HORIZONTAL)
        self.saveButton =  wx.Button(self.panel, id=-1, label='Save')
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_saveButton(event, self.site_grid), self.saveButton)
        self.cancelButton = wx.Button(self.panel, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)
        self.continueButton = wx.Button(self.panel, id=-1, label='Save and continue')
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_continueButton(event, self.site_grid, next_dia=self.InitSampCheck), self.continueButton)
        self.backButton = wx.Button(self.panel, wx.ID_ANY, "&Back")
        previous_dia = self.InitSampCheck
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_backButton(event, previous_dia=previous_dia), self.backButton)

        hboxok.Add(self.saveButton, flag=wx.RIGHT, border=10)
        hboxok.Add(self.cancelButton, flag=wx.RIGHT, border=10 )
        hboxok.Add(self.continueButton, flag=wx.RIGHT, border=10 )
        hboxok.Add(self.backButton)


        ### Make Containers ###
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(label, flag=wx.ALIGN_CENTER|wx.BOTTOM|wx.TOP, border=20)#, flag=wx.ALIGN_LEFT|wx.BOTTOM, border=20)
        vbox.Add(hbox_one, flag=wx.BOTTOM|wx.LEFT, border=10)
        vbox.Add(hboxok, flag=wx.BOTTOM|wx.LEFT, border=10)
        vbox.Add(self.site_grid, flag=wx.ALL|wx.EXPAND, border=10) # EXPAND ??

        hbox_all= wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.AddSpacer(vbox)
        hbox_all.AddSpacer(20)

        self.panel.SetSizer(hbox_all)
        if sys.platform in ['win32', 'win64']:                
            self.panel.SetScrollbars(20, 20, 50, 50)
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

        # using ScrolledWindow works on up to date wxPython and is necessary for windows
        # it breaks with Canopy wxPython, so for Mac we just use Panel
        if sys.platform in ['win32', 'win64']:
            self.panel = wx.ScrolledWindow(self, style=wx.SIMPLE_BORDER)
        else:
            self.panel = wx.Panel(self, style=wx.SIMPLE_BORDER)

        TEXT = """Step 5:
Check that locations are correctly named.
Fill in any blank cells using controlled vocabularies.
(See Help button for details)

** Denotes controlled vocabulary"""
        label = wx.StaticText(self.panel,label=TEXT)
        self.Data_hierarchy = self.ErMagic.Data_hierarchy
        self.locations = self.Data_hierarchy['locations']
        #
        try:
            key1 = self.ErMagic.data_er_locations.keys()[0]
        except IndexError:
            MSG = "You have no data in er_locations, so we are skipping step 5.\n Note that location names must be entered at the measurements level,so you may need to re-import your data, or you can add a location in step 3"
            dlg = wx.MessageDialog(None,caption="Message:", message=MSG ,style=wx.OK|wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.panel.Destroy()
            self.InitAgeCheck()
            return
            
            #self.ErMagic.data_er_locations = {" ": {"er_citation_names": "This study", "er_location_name": "", "location_begin_lon": "", "location_end_lon": "", "location_begin_lat": "", "location_end_lat": "", "location_type": ""}}
            #key1 = self.ErMagic.data_er_locations.keys()[0]
        col_labels = sorted(self.ErMagic.data_er_locations[key1].keys())
        try:
            col_labels.remove('er_location_name')
            col_labels.remove('location_type')
            col_labels[:0] = ['er_location_name', 'location_type']
        except:
            pass

        self.loc_grid = self.make_simple_table(col_labels, self.ErMagic.data_er_locations, "location")

        self.Bind(wx.grid.EVT_GRID_EDITOR_CREATED, lambda event: self.on_edit_grid(event, self.loc_grid), self.loc_grid)

        self.drop_down_menu = drop_down_menus.Menus("location", self, self.loc_grid, None) # initialize all needed drop-down menus

        ### Create Buttons ###
        hbox_one = wx.BoxSizer(wx.HORIZONTAL)
        self.helpButton = wx.Button(self.panel, label="Help")
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_helpButton(event, "ErMagicLocationHelp.html"), self.helpButton)
        hbox_one.Add(self.helpButton)

        hboxok = wx.BoxSizer(wx.HORIZONTAL)
        self.saveButton =  wx.Button(self.panel, id=-1, label='Save')
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_saveButton(event, self.loc_grid), self.saveButton)
        self.cancelButton = wx.Button(self.panel, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)
        self.continueButton = wx.Button(self.panel, id=-1, label='Save and continue')
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_continueButton(event, self.loc_grid, next_dia=self.InitAgeCheck), self.continueButton)
        self.backButton = wx.Button(self.panel, wx.ID_ANY, "&Back")
        previous_dia = self.InitSampCheck
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_backButton(event, previous_dia, current_dia = self.InitLocCheck), self.backButton)

        hboxok.Add(self.saveButton, flag=wx.RIGHT, border=10)
        hboxok.Add(self.cancelButton, flag=wx.RIGHT, border=10 )
        hboxok.Add(self.continueButton, flag=wx.RIGHT, border=10 )
        hboxok.Add(self.backButton)

        ### Make Containers ###
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(label, flag=wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, border=20)
        vbox.Add(hbox_one, flag=wx.BOTTOM|wx.ALIGN_LEFT, border=10)
        vbox.Add(hboxok, flag=wx.BOTTOM|wx.ALIGN_LEFT, border=10)
        vbox.Add(self.loc_grid, flag=wx.TOP|wx.BOTTOM, border=10)

        hbox_all= wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.AddSpacer(vbox)
        hbox_all.AddSpacer(20)

        self.panel.SetSizer(hbox_all)
        if sys.platform in ['win32', 'win64']:
            self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Centre()
        self.Show()
        self.Hide()
        self.Show()


    def InitAgeCheck(self):
        """make an interactive grid in which users can edit ages"""

        # using ScrolledWindow works on up to date wxPython and is necessary for windows
        # it breaks with Canopy wxPython, so for Mac we just use Panel
        if sys.platform in ['win32', 'win64']:
            self.panel = wx.ScrolledWindow(self, style=wx.SIMPLE_BORDER)
        else:
            self.panel = wx.Panel(self, style=wx.SIMPLE_BORDER)

        TEXT = """Step 6:
Fill in or correct any cells with information about ages.
The column for magic_method_codes can take multiple values in the form of a colon-delimited list.
You may use the drop-down menus to add as many values as needed in these columns.  
(See Help button for details)

**Denotes controlled vocabulary """
        label = wx.StaticText(self.panel,label=TEXT)
        self.Data_hierarchy = self.ErMagic.Data_hierarchy
        self.sites = self.Data_hierarchy['sites']
        #
        key1 = self.ErMagic.data_er_ages.keys()[0]
        col_labels = sorted(self.ErMagic.data_er_ages[key1].keys())
        try:
            for col_label in ['er_site_name', 'er_location_name', 'er_citation_names', 'magic_method_codes', 'age_description', 'age_unit', 'age']:
                col_labels.remove(col_label)
            col_labels[:0] = ['er_site_name', 'er_citation_names', 'er_location_name', 'magic_method_codes', 'age_description', 'age_unit', 'age']
        except:
            pass
        # only use sites that are associated with actual samples/specimens
        

        #ages_data_dict = {k: v for k, v in self.ErMagic.data_er_ages.items() if k in self.sites} # fails in Python 2.6
        ages_data_dict = {}
        for k, v in self.ErMagic.data_er_ages.items():
            if k in self.sites:
                ages_data_dict[k] = v

        self.age_grid = self.make_simple_table(col_labels, ages_data_dict, "age")
        #
        # make it impossible to edit the 1st and 3rd columns
        for row in range(self.age_grid.GetNumberRows()):
            for col in (0, 2):
                self.age_grid.SetReadOnly(row, col, True)
        #
        #self.Bind(wx.grid.EVT_GRID_EDITOR_SHOWN, self.on_edit_grid, self.age_grid) 
        self.Bind(wx.grid.EVT_GRID_EDITOR_CREATED, lambda event: self.on_edit_grid(event, self.age_grid), self.age_grid)
        self.drop_down_menu = drop_down_menus.Menus("age", self, self.age_grid, None) # initialize all needed drop-down menus

        ### Create Buttons ###
        hbox_one = wx.BoxSizer(wx.HORIZONTAL)
        self.helpButton = wx.Button(self.panel, label="Help")
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_helpButton(event, "ErMagicAgeHelp.html"), self.helpButton)
        hbox_one.Add(self.helpButton)

        hboxok = wx.BoxSizer(wx.HORIZONTAL)
        self.saveButton =  wx.Button(self.panel, id=-1, label='Save')
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_saveButton(event, self.age_grid), self.saveButton)
        self.cancelButton = wx.Button(self.panel, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)
        self.continueButton = wx.Button(self.panel, id=-1, label='Save and continue')
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_continueButton(event, self.age_grid, next_dia=None), self.continueButton)
        self.backButton = wx.Button(self.panel, wx.ID_ANY, "&Back")
        previous_dia = self.InitLocCheck
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_backButton(event, previous_dia), self.backButton)

        hboxok.Add(self.saveButton, flag=wx.RIGHT, border=10)
        hboxok.Add(self.cancelButton, flag=wx.RIGHT, border=10 )
        hboxok.Add(self.continueButton, flag=wx.RIGHT, border=10 )
        hboxok.Add(self.backButton)

        ### Make Containers ###
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(label, flag=wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, border=20)#, flag=wx.ALIGN_LEFT|wx.BOTTOM, border=20)
        vbox.Add(hbox_one, flag=wx.BOTTOM, border=10)
        vbox.Add(hboxok, flag=wx.BOTTOM, border=10)
        vbox.Add(self.age_grid, flag=wx.TOP|wx.BOTTOM, border=10) # EXPAND ??

        hbox_all= wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.AddSpacer(vbox)
        hbox_all.AddSpacer(20)

        self.panel.SetSizer(hbox_all)
        if sys.platform in ['win32', 'win64']:
            self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Centre()
        self.Show()
        self.Hide()
        self.Show()


    ### Grid methods ###
    def make_simple_table(self, column_labels, data_dict, grid_name):
        row_labels = sorted(data_dict.keys())
        if len(row_labels) in range(1,4):
            num_rows = len(row_labels)
            height = {1: 70, 2: 90, 3: 110, 4: 130}
            grid = wx.grid.Grid(self.panel, -1, name=grid_name, size=(-1, height[num_rows]))# autosizes width, but enforces fixed pxl height to prevent display problems
        else:
            grid = wx.grid.Grid(self.panel, -1, name=grid_name)

        grid.ClearGrid()
        grid.CreateGrid(len(row_labels), len(column_labels))

        self.temp_data[column_labels[0]] = []
        # set row labels
        for n, row in enumerate(row_labels):
            grid.SetRowLabelValue(n, str(n+1))
            grid.SetCellValue(n, 0, row)
            self.temp_data[column_labels[0]].append(row)
        # set column labels
        for n, col in enumerate(column_labels):
            grid.SetColLabelValue(n, col)
        # set values in each cell (other than 1st column)
        for num, row in enumerate(row_labels):
            for n, col in enumerate(column_labels[1:]):
                if col in data_dict[row].keys():
                    value = data_dict[row][col]
                else:
                    value = ''
                if value:
                    grid.SetCellValue(num, n+1, value)
        grid.AutoSizeColumns(True)

        grid.AutoSize() # prevents display failure

        for n, col in enumerate(column_labels):
            # adjust column widths to be a little larger then auto for nicer editing
            orig_size = grid.GetColSize(n)
            if orig_size > 110:
                size = orig_size * 1.1
            else:
                size = orig_size * 1.6
            grid.SetColSize(n, size)
        return grid
        

    def onMouseOver(self, event, grid):
        """
        Displays a tooltip over any cell in a certain column
        """
        print "doing onMouseOver"
        x, y = grid.CalcUnscrolledPosition(event.GetX(),event.GetY())
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

        
    def on_edit_grid(self, event, grid):
        """sets self.changes to true when user edits the grid.
        provides down and up key functionality for exiting the editor"""
        self.changes = True
        editor = event.GetControl()
        editor.Bind(wx.EVT_KEY_DOWN, lambda event: self.onEditorKey(event, grid))

    def onEditorKey(self, event, grid):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_UP:
            grid.MoveCursorUp(False)
            grid.MoveCursorDown(False)# have this in because otherwise cursor moves up 2 rows
        elif keycode == wx.WXK_DOWN:
            grid.MoveCursorDown(False)
            grid.MoveCursorUp(False) # have this in because otherwise cursor moves down 2 rows
        #elif keycode == wx.WXK_LEFT:
        #    grid.MoveCursorLeft(False)
        #elif keycode == wx.WXK_RIGHT:
        #    grid.MoveCursorRight(False)
        else:
            pass
        event.Skip()


    def validate(self, grid):
        validations = ['specimens', 'samples', 'site_class', 'site_lithology', 'site_type', 'site_definition', 'site_lon', 'site_lat', 'sample_class', 'sample_lithology', 'sample_type', 'sample_lat', 'sample_lon', 'location_type', 'age_unit', 'age']#, 'magic_method_codes']
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



    def remove_starred_labels(self, grid):
        cols_with_stars = []
        for col in range(grid.GetNumberCols()):
            label = grid.GetColLabelValue(col)
            if '**' in label:
                grid.SetColLabelValue(col, label.strip('**'))
                cols_with_stars.append(col)
        return cols_with_stars


    ### Button methods ###

    def on_addSampleButton(self, event):

        def add_sample(sample, site):
            add_sample_data(sample, site)

        #def __init__(self, parent, title, data_items, data_method):

        if not self.ErMagic.data_er_samples:
            self.ErMagic.read_MagIC_info()

        pw.AddItem(self, 'Sample', add_sample, self.sites, 'site') # makes window for adding new data

        def add_sample_data(sample, site):
            self.ErMagic.change_sample
            keys = self.ErMagic.er_samples_header
            self.ErMagic.data_er_samples[sample] = dict(zip(keys, ["" for key in keys]))
            self.ErMagic.data_er_samples[sample]['er_sample_name'] = sample
            self.ErMagic.data_er_samples[sample]['er_site_name'] = site

            self.Data_hierarchy['samples'][sample] = []
            self.Data_hierarchy['site_of_sample'][sample] = site
            self.Data_hierarchy['location_of_sample'][sample] = ''
            # if that site didn't already exist in Data_hierarchy:
            if not site in self.Data_hierarchy['sites'].keys():
                self.Data_hierarchy['sites'][site] = []
            self.Data_hierarchy['sites'][site].append(sample)

            # re-Bind so that the updated samples list shows up on a left click
            samples = sorted(self.Data_hierarchy['samples'].keys())
            samples = sorted(list(set(samples).union(self.ErMagic.data_er_samples.keys())))
            choices = self.drop_down_menu.choices
            choices[2] = (samples, False)
            self.drop_down_menu.update_drop_down_menu(self.spec_grid, choices)



    def on_addSiteButton(self, event):
        
        def add_site(site, location):
            add_site_data(site, location)

        pw.AddItem(self, 'Site', add_site, self.locations, 'location')

        def add_site_data(site, location):
            keys = self.ErMagic.er_sites_header
            self.ErMagic.data_er_sites[site] = dict(zip(keys, ["" for key in keys]))
            self.ErMagic.data_er_sites[site]['er_site_name'] = site
            self.ErMagic.data_er_sites[site]['er_location_name'] = location

            self.Data_hierarchy['sites'][site] = []
            self.Data_hierarchy['location_of_site'][site] = location
            
            # re-Bind so that the updated sites list shows up on a left click
            sites = sorted(self.Data_hierarchy['sites'].keys())
            sites = sorted(list(set(sites).union(self.ErMagic.data_er_sites.keys())))
            self.drop_down_menu.update_drop_down_menu(self.samp_grid, {2: (sites, False)})


    def on_addLocButton(self, event):

        def add_loc(loc):
            add_loc_data(loc)

        #def __init__(self, parent, title, data_items, data_method):

        if not self.ErMagic.data_er_locations:
            pass
            

        pw.AddItem(self, 'Location', add_loc, owner_items=None, belongs_to=None) # makes window for adding new data

        def add_loc_data(loc):
            # this is not dialed in yet
            keys = self.ErMagic.er_locations_header
            self.ErMagic.data_er_locations[loc] = {key: "" for key in keys}
            self.Data_hierarchy['locations'][loc] = []

            # re-Bind so that the updated locations list shows up on a left click
            locations = sorted(self.Data_hierarchy['locations'].keys())
            locations = sorted(list(set(locations).union(self.ErMagic.data_er_locations.keys())))
            choices = self.drop_down_menu.choices
            choices[2] = (locations, False)
            self.drop_down_menu.update_drop_down_menu(self.site_grid, choices)


    def on_helpButton(self, event, page=None):
        """shows html help page"""
        # for use on the command line:
        path = check_updates.get_pmag_dir()

        # for use with pyinstaller
        #path = self.main_frame.resource_dir
        
        html_frame = pw.HtmlFrame(self, page=(os.path.join(path, 'help_files', page)))
        html_frame.Show()

    def on_continueButton(self, event, grid, next_dia=None):
        """pulls up next dialog, if there is one.
        gets any updated information from the current grid and runs ErMagicBuilder"""
        #wait = wx.BusyInfo("Please wait, working...")

        # unhighlight selected columns, etc.
        if self.drop_down_menu:  
            self.drop_down_menu.clean_up(grid)

        # remove '**' from col names
        self.remove_starred_labels(grid)

        if self.ErMagic.data_er_specimens:
            pass
        else:
            self.ErMagic.read_MagIC_info()
        grid.SaveEditControlValue() # locks in value in cell currently edited
        simple_grids = {"location": self.ErMagic.data_er_locations, "age": self.ErMagic.data_er_ages}
        grid_name = grid.GetName()

        # check that all required data is present
        validation_errors = self.validate(grid)
        if validation_errors:
            result = pw.warning_with_override("You are missing required data in these columns: {}\nAre you sure you want to continue without this data?".format(str(validation_errors)))
            if result == wx.ID_YES:
                pass
            else:
                return False

        if self.changes:
            #if grid_name in simple_grids:
            #    self.update_simple_grid_data(grid, simple_grids[grid_name])
            #else:
            #    self.update_orient_data(grid)

            self.ErMagic.update_ErMagic()
            
            self.changes = False # resets

        self.panel.Destroy()
        if next_dia:
            wait = wx.BusyInfo("Please wait, working...")
            next_dia()
            del wait
        else:
            self.final_update()
            self.Destroy()
        

    def on_saveButton(self, event, grid):
        """saves any editing of the grid but does not continue to the next window"""
        wait = wx.BusyInfo("Please wait, working...")

        
        if self.drop_down_menu:  # unhighlight selected columns, etc.
            self.drop_down_menu.clean_up(grid)
            
        # remove '**' from col labels
        starred_cols = self.remove_starred_labels(grid)
            
        if self.ErMagic.data_er_specimens:
            pass
        else:
            self.ErMagic.read_MagIC_info()
        grid.SaveEditControlValue() # locks in value in cell currently edited
        grid.HideCellEditControl() # removes focus from cell that was being edited
        simple_grids = {"location": self.ErMagic.data_er_locations, "age": self.ErMagic.data_er_ages}
        grid_name = grid.GetName()
        if self.changes:
            print "there were changes, so we are updating the data"
            if grid_name in simple_grids:
                self.update_simple_grid_data(grid, simple_grids[grid_name])
            else:
                self.update_orient_data(grid)

            self.ErMagic.update_ErMagic()
            self.changes = False

        for col in starred_cols:
            label = grid.GetColLabelValue(col)
            grid.SetColLabelValue(col, label+'**')
        del wait


    def on_cancelButton(self, event):
        self.Destroy()

    def on_backButton(self, event, previous_dia, current_dia = None):
        wait = wx.BusyInfo("Please wait, working...")
        if current_dia == self.InitLocCheck:
            pass
        elif previous_dia == self.InitSpecCheck or previous_dia == self.InitSampCheck:
            self.sample_window = 0
        self.panel.Destroy()
        previous_dia()
        del wait

        
    ### Manage data methods ###

    
    """
    def update_simple_grid_data(self, grid, data):
        grid_name = grid.GetName()
        rows = range(grid.GetNumberRows())
        cols = range(grid.GetNumberCols())
        updated_items = []
        for row in rows:
            item = str(grid.GetCellValue(row, 0))
            updated_items.append(item)
        if grid_name == "location":
            self.update_locations(updated_items)
        for row in rows:
            item = str(grid.GetCellValue(row, 0))
            for col in cols[1:]:
                category = str(grid.GetColLabelValue(col))
                value = str(grid.GetCellValue(row, col))
                data[item][category] = value
        self.temp_data[grid_name] = updated_items


    def update_orient_data(self, grid):

        col1_updated, col2_updated, col1_old, col2_old, type1, type2 = self.get_old_and_new_data(grid, 0, 2)
        if len(set(col1_updated)) != len(col1_updated):
            print "Duplicate {} detected.  Please ensure that all {} names are unique".format(type1, type1[:-1])
            return 0
        if type1 == 'specimens':
            self.update_specimens(self.spec_grid, col1_updated, col1_old, col2_updated, col2_old, type1, type2)
        if type1 == 'samples':
            cols = range(3, grid.GetNumberCols())
            col_labels = []
            for col in cols:
                col_labels.append(grid.GetColLabelValue(col))
            self.update_samples(grid, col1_updated, col1_old, col2_updated, col2_old, *col_labels)
        if type1 == 'sites':
            self.update_sites(grid, col1_updated, col1_old, col2_updated, col2_old)#, *col_labels)

        # updates the holder data so that when we save again, we will only update what is new as of the last save
        self.temp_data[type1] = col1_updated 
        self.temp_data[type2] = col2_updated


    def update_locations(self, updated_locations):
        original_locations = self.temp_data['er_location_name']
        changed = [(original_locations[num], new_loc) for (num, new_loc) in enumerate(updated_locations) if new_loc != original_locations[num]]
        for change in changed:
            old_loc, new_loc = change
            sites = self.Data_hierarchy['locations'].pop(old_loc)
            self.Data_hierarchy['locations'][new_loc] = sites
            #
            data = self.ErMagic.data_er_locations.pop(old_loc)
            self.ErMagic.data_er_locations[new_loc] = data
            self.ErMagic.data_er_locations[new_loc]['er_location_name'] = new_loc
            #
            for site in sites:
                self.Data_hierarchy['location_of_site'][site] = new_loc
                self.ErMagic.data_er_sites[site]['er_location_name'] = new_loc
                self.ErMagic.data_er_ages[site]['er_location_name'] = new_loc
                samples = self.Data_hierarchy['sites'][site]
                for sample in samples:
                    self.Data_hierarchy['location_of_sample'][sample] = new_loc
                    self.ErMagic.data_er_samples[sample]['er_location_name'] = new_loc
                    specimens = self.Data_hierarchy['samples'][sample]
                    for spec in specimens:
                        self.Data_hierarchy['location_of_specimen'][spec] = new_loc
                        self.ErMagic.data_er_specimens[spec]['er_location_name'] = new_loc

    def update_sites(self, grid, col1_updated, col1_old, col2_updated, col2_old):#, *args):
        changed = [(old_value, col1_updated[num]) for (num, old_value) in enumerate(col1_old) if old_value != col1_updated[num]]
        # find where changes have occurred
        for change in changed:
            old_site, new_site = change
            samples = self.Data_hierarchy['sites'].pop(old_site)
            location = self.Data_hierarchy['location_of_site'].pop(old_site)
            if location == " ": # prevents error
                location = ""
            self.Data_hierarchy['sites'][new_site] = samples
            # fix extra temp_data to have updated site names
            info = self.extra_site_temp_data.pop(old_site)
            self.extra_site_temp_data[new_site] = info
            # do locations
            ind = self.Data_hierarchy['locations'][location].index(old_site)
            self.Data_hierarchy['locations'][location][ind] = new_site
            self.Data_hierarchy['location_of_site'][new_site] = location
            # adjust for renamed sites
            for samp in samples:
                specimens = self.Data_hierarchy['samples'][samp]
                self.Data_hierarchy['site_of_sample'][samp] = new_site
                self.ErMagic.data_er_samples[samp]['er_site_name'] = new_site
                for spec in specimens:
                    self.Data_hierarchy['site_of_specimen'][spec] = new_site
                    self.ErMagic.data_er_specimens[spec]['er_site_name'] = new_site
            data = self.ErMagic.data_er_sites.pop(old_site)
            self.ErMagic.data_er_sites[new_site] = data
            self.ErMagic.data_er_sites[new_site]['er_site_name'] = new_site

        # now do the "which site belongs to which location" part
        for num, value in enumerate(col2_updated):
            # find where changes have occurred
            if value != col2_old[num]:
                #print "CHANGE!", "new", value, "old", col2_old[num]
                old_loc = col2_old[num]
                new_loc = col2_updated[num]
                if old_loc == " ": 
                    old_loc = ""
                if new_loc == " ":
                    new_loc = ""
                site = col1_updated[num]
                #
                self.Data_hierarchy['location_of_site'][site] = new_loc
                #
                if old_loc in self.Data_hierarchy['locations']:
                    self.Data_hierarchy['locations'][old_loc].remove(site)
                self.Data_hierarchy['locations'][new_loc].append(site)
                #
                for samp in self.Data_hierarchy['sites'][site]:
                    self.Data_hierarchy['location_of_sample'][samp] = new_loc
                    self.ErMagic.data_er_samples[samp]['er_location_name'] = new_loc
                    for spec in self.Data_hierarchy['samples'][samp]:
                        self.Data_hierarchy['location_of_specimen'][spec] = new_loc
                        self.ErMagic.data_er_specimens[spec]['er_location_name'] = new_loc
                #
                self.ErMagic.data_er_sites[site]['er_location_name'] = new_loc
                #


        # check if any locations no longer have any site assigned to them, and destroy them if so.
        # this means they won't show up in the check locations grid
        locations = self.ErMagic.data_er_locations.keys()
        for loc in locations:
            #print self.Data_hierarchy['sites'][site]
            if loc in self.Data_hierarchy['locations'].keys():
                if not self.Data_hierarchy['locations'][loc]:
                    self.Data_hierarchy['locations'].pop(loc)
                    self.ErMagic.data_er_locations.pop(loc)
         
        # now fill in all the other columns, using extra temp_data to update only
        # data for cells that have been changed
        columns = grid.GetNumberCols()
        col_labels = []
        for col in range(columns):
            col_labels.append(grid.GetColLabelValue(col))
        for num_site, site in enumerate(col1_updated):
            for num, arg in enumerate(col_labels[3:]):
                old_value = self.extra_site_temp_data[site][num]
                num += 3 # ignore first 3 rows
                value = str(grid.GetCellValue(num_site, num))
                if old_value == value:
                    continue
                self.ErMagic.data_er_sites[site][arg] = value
                # update data_er_samples where appropriate 
                # (i.e., change er_sample_type if er_site_type is changed here)
                samples = self.Data_hierarchy['sites'][site]
                for sample in samples:
                    arg = arg.replace('site', 'sample')
                    self.ErMagic.data_er_samples[sample][arg] = value

    
    def update_samples(self, grid, col1_updated, col1_old, col2_updated, col2_old, *args):
        changed = [(old_value, col1_updated[num]) for (num, old_value) in enumerate(col1_old) if old_value != col1_updated[num]]  
        for change in changed:
            old_sample, new_sample = change
            specimens = self.Data_hierarchy['samples'].pop(old_sample)
            site = self.Data_hierarchy['site_of_sample'].pop(old_sample)
            location = self.Data_hierarchy['location_of_sample'].pop(old_sample)
            
            self.Data_hierarchy['samples'][new_sample] = specimens
            
            for spec in specimens:
                self.Data_hierarchy['sample_of_specimen'][spec] = new_sample
                self.Data_hierarchy['specimens'][spec] = new_sample
            #
            self.Data_hierarchy['site_of_sample'][new_sample] = site
            #
            self.Data_hierarchy['location_of_sample'][new_sample] = location
            #
            ind = self.Data_hierarchy['sites'][site].index(old_sample)
            self.Data_hierarchy['sites'][site][ind] = new_sample
            # updating self.ErMagic.data_er_samples
            #print "in update_samples, self.ErMagic.data_er_specimens", self.ErMagic.data_er_specimens
            #print "in update_samples, self.ErMagic.data_er_samples.keys()", self.ErMagic.data_er_samples
            #print "-"
            sample_data = self.ErMagic.data_er_samples.pop(old_sample)
            self.ErMagic.data_er_samples[new_sample] = sample_data
            self.ErMagic.data_er_samples[new_sample]['er_sample_name'] = new_sample
            for spec in self.ErMagic.data_er_specimens:
                if self.ErMagic.data_er_specimens[spec]['er_sample_name'] == old_sample:
                    self.ErMagic.data_er_specimens[spec]['er_sample_name'] = new_sample
        
        # now do the site changes
        for num, value in enumerate(col2_updated):
            # find where changes have occurred
            if value != col2_old[num]:
                #print "CHANGE!", "new", value, "old", col2_old[num]
                sample = col1_updated[num]
                specimens = self.Data_hierarchy['samples'][sample]
                old_site = col2_old[num]
                new_site = value
                try:
                    loc = self.Data_hierarchy['location_of_site'][new_site]
                except:
                    loc = self.ErMagic.data_er_sites[new_site]['er_location_name']
                    self.Data_hierarchy['location_of_site'][new_site] = loc
                samples = self.Data_hierarchy['sites'][old_site]
                #
                self.Data_hierarchy['site_of_sample'][sample] = new_site
                #
                self.Data_hierarchy['location_of_sample'][sample] = loc
                #
                if new_site not in self.Data_hierarchy['sites'].keys():
                    self.Data_hierarchy['sites'][new_site] = []
                self.Data_hierarchy['sites'][new_site].append(sample)
                try:
                    self.Data_hierarchy['sites'][old_site].remove(sample)
                except ValueError: # if sample was not already in old_site, don't worry about it
                    pass
                for spec in specimens:
                    # specimens belonging to a sample which has been reassigned to a different site correspondingly must change site and location
                    self.Data_hierarchy['site_of_specimen'][spec] = new_site
                    self.Data_hierarchy['location_of_specimen'][spec] = loc
                
                if not sample in self.ErMagic.data_er_samples.keys():
                    keys = self.ErMagic.er_samples_header
                    self.ErMagic.data_er_samples[sample] = dict(zip(keys, ["" for key in keys]))
                    self.ErMagic.data_er_samples[sample]['er_sample_name'] = sample
                self.ErMagic.data_er_samples[sample]['er_site_name'] = new_site
                self.ErMagic.data_er_samples[sample]['er_location_name'] = loc

        # check if any sites no longer have any sample assigned to them, and destroy them if so
        sites = self.ErMagic.data_er_sites.keys()
        for site in sites:
            #print self.Data_hierarchy['sites'][site]
            if site in self.Data_hierarchy['sites'].keys():
                if not self.Data_hierarchy['sites'][site]:
                    self.Data_hierarchy['sites'].pop(site)
                    #self.ErMagic.data_er_sites.pop(site) # DON'T do this.  we want to leave all the original information in data_er_sites
                    print "site {} is empty".format(site)

        # now fill in all the other columns
        for num_sample, sample in enumerate(col1_updated):
            for num, arg in enumerate(args):
                num += 3
                value = str(grid.GetCellValue(num_sample, num))
                self.ErMagic.data_er_samples[sample][arg] = value
                #print "sample: {}, arg: {}, value {}".format(sample, arg, value)
                
      

    def update_specimens(self, grid, col1_updated, col1_old, col2_updated, col2_old, type1, type2):
        for num, value in enumerate(col2_updated):
            # find where changes have occurred
            if value != col2_old[num]:
                old_samp = col2_old[num]
                samp = value
                spec = col1_updated[num]
                # some of the sample data could exist only in the er_samples.txt file (so in data_er_samples and not Data_hierarchy)
                # if the user selects a sample that does not exist in Data_hierarchy, we will propagate it in (below)
                try:
                    site = self.Data_hierarchy['site_of_sample'][samp] 
                except KeyError:
                    site = self.ErMagic.data_er_samples[samp]['er_site_name']
                    self.Data_hierarchy['site_of_sample'][samp] = site
                old_site = self.Data_hierarchy['site_of_sample'][old_samp]
                try:
                    location = self.Data_hierarchy['location_of_sample'][samp] 
                except KeyError:
                    location = ""
                    self.Data_hierarchy['location_of_sample'][samp] = location
                self.Data_hierarchy['specimens'][spec] = samp
                self.Data_hierarchy['sample_of_specimen'][spec] = samp
                self.Data_hierarchy['site_of_specimen'][spec] = site
                self.Data_hierarchy['location_of_specimen'][spec] = location
                #
                if samp not in self.Data_hierarchy['samples'].keys():
                    self.Data_hierarchy['samples'][samp] = []
                self.Data_hierarchy['samples'][samp].append(spec)
                self.Data_hierarchy['samples'][old_samp].remove(spec)

                #
                # 
                # delete any samples which no longer have specimens from Data_hierarchy['sites'] list
                if old_samp in self.Data_hierarchy['samples'].keys(): # if old_samp is in Data_hierarchy
                    if not self.Data_hierarchy['samples'][old_samp]: # but it is empty (having no specimens)
                        print "removing {} from {}".format(old_samp, old_site) 
                        self.Data_hierarchy['sites'][old_site].remove(old_samp) # get rid of it

                #
                # do the ErMagic.data_er_samples part
                self.ErMagic.data_er_specimens[spec]['er_sample_name'] = samp
                self.ErMagic.data_er_specimens[spec]['er_site_name'] = site
                self.ErMagic.data_er_specimens[spec]['er_locations_name'] = location
                
                    
        columns = grid.GetNumberCols()
        col_labels = []
        for col in range(columns):
            col_labels.append(grid.GetColLabelValue(col))
        for num_specimen, specimen in enumerate(col1_updated):
            for num, arg in enumerate(col_labels[3:]):
                old_value = self.extra_specimen_temp_data[specimen][num]
                num += 3 # ignore first 3 rows
                value = str(grid.GetCellValue(num_specimen, num))
                if old_value == value:
                    continue
                self.ErMagic.data_er_specimens[specimen][arg] = value
                
                # ADD IN THE REST OF IT HERE
                


        # if (through editing) a sample no longer has any specimens, remove it
        samples = self.ErMagic.data_er_samples.keys()
        for sample in samples:
            if sample in self.Data_hierarchy['samples'].keys():
                if not self.Data_hierarchy['samples'][sample]:
                    #print "removing sample: {}", sample
                    self.Data_hierarchy['samples'].pop(sample)
                    self.ErMagic.data_er_samples.pop(sample)

        # check if any sites no longer have any sample assigned to them, and destroy them if so
        sites = self.ErMagic.data_er_sites.keys()
        if False:
        #for site in sites:
            if not self.Data_hierarchy['sites'][site]:
                self.Data_hierarchy['sites'].pop(site)
                self.ErMagic.data_er_sites.pop(site)

        #keys = ['sample_of_specimen', 'site_of_sample', 'location_of_specimen', 'locations', 'sites', 'site_of_specimen', 'samples', 'location_of_sample', 'location_of_site', 'specimens']


    def get_old_and_new_data(self, grid, col1_num, col2_num):
        cols = grid.GetNumberCols()
        rows = grid.GetNumberRows()
        type1 = grid.GetColLabelValue(col1_num)
        type2 = grid.GetColLabelValue(col2_num)
        old_1 = self.temp_data[type1]
        old_2 = self.temp_data[type2]
        update_1 = []
        update_2 = []
        for r in range(rows):
            # gets edited values from grid
            one = grid.GetCellValue(r, 0)
            update_1.append(str(one))
            two = grid.GetCellValue(r, 2)
            update_2.append(str(two))
        return update_1, update_2, old_1, old_2, type1, type2
    """

    def final_update(self):
        """
        Updates er_*.txt files to delete any specimens, samples, or sites that are no longer included
        """

        def remove_extras(long_dict, short_dict):
            """
            remove any key/value pairs from the long_dictionary if that key is not present in the short_dictionary
            """
            for dict_item in long_dict.keys():
                if dict_item not in short_dict.keys():
                    long_dict.pop(dict_item)
            return long_dict
        remove_extras(self.ErMagic.data_er_specimens, self.Data_hierarchy['specimens'])
        remove_extras(self.ErMagic.data_er_samples, self.Data_hierarchy['samples'])
        remove_extras(self.ErMagic.data_er_sites, self.Data_hierarchy['sites'])
        #remove_extras(self.ErMagic.data_er_locations, self.Data_hierarchy['locations'])
        remove_extras(self.Data_hierarchy['locations'], self.ErMagic.data_er_locations)
        remove_extras(self.ErMagic.data_er_ages, self.Data_hierarchy['sites'])
        self.ErMagic.update_ErMagic()
        


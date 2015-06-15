"""
dialogs for ErMagicBuilder
"""
# pylint: disable=W0612,C0111,C0103,W0201
import wx
import wx.grid
import sys
import drop_down_menus
import pmag_widgets as pw
import check_updates

class ErMagicCheckFrame(wx.Frame):

    def __init__(self, parent, title, WD, magic_data): # magic_data was ErMagic
        wx.Frame.__init__(self, parent, -1, title)
        self.WD = WD
        self.main_frame = self.Parent
        self.ErMagic_data = magic_data

        self.temp_data = {}
        self.drop_down_menu = None
        self.sample_window = 0 # sample window must be displayed (differently) twice, so it is useful to keep track
        self.InitSpecCheck()


    def InitSpecCheck(self):
        """make an interactive grid in which users can edit specimen names
        as well as which sample a specimen belongs to"""

        # using ScrolledWindow works on up to date wxPython and is necessary for windows
        # it breaks with Canopy wxPython, so for Mac we just use Panel

        # make sure we are up to date
        self.ErMagic_data.read_MagIC_info()
        
        if sys.platform in ['win32', 'win64']:
            self.panel = wx.ScrolledWindow(self, style=wx.SIMPLE_BORDER)
        else:
            self.panel = wx.Panel(self, style=wx.SIMPLE_BORDER)

        #import wx.lib.scrolledpanel as libpanel # does not work well
        #self.panel = libpanel.ScrolledPanel(self, style=wx.SIMPLE_BORDER)

        text = """Step 1:
Check that all specimens belong to the correct sample
(if sample name is simply wrong, that will be fixed in step 2)"""
        label = wx.StaticText(self.panel, label=text)
        #self.Data_hierarchy = self.ErMagic_data.Data_hierarchy

        self.specimens = sorted(self.ErMagic_data.Data_hierarchy['specimens'].keys())
        samples = self.ErMagic_data.Data_hierarchy['samples'].keys()
        # add in any additional samples we might have information about (from er_samples.txt file) even if currently that sample does not show up in the magic_measurements file
        samples = sorted(list(set(samples).union(self.ErMagic_data.data_er_samples.keys()))) 

        # create the grid and also a record of the initial values for specimens/samples as a reference
        # to tell if we've had any changes

        for val in ['er_citation_names', 'er_location_name', 'er_site_name', 'er_sample_name', 'er_specimen_name', 'specimen_class', 'specimen_lithology', 'specimen_type']: #
            try:
                self.ErMagic_data.er_specimens_header.remove(val)
            except ValueError:
                pass
        self.ErMagic_data.er_specimens_header.sort()
        self.ErMagic_data.er_specimens_header[:0] = ['er_specimen_name', 'er_sample_name']

        self.spec_grid = self.make_simple_table(self.ErMagic_data.er_specimens_header, self.ErMagic_data.data_er_specimens, "er_specimen_name")
        # initialize all needed drop-down menus
        self.drop_down_menu = drop_down_menus.Menus("specimen", self, self.spec_grid, samples) 

        #### Create Buttons ####
        hbox_one = wx.BoxSizer(wx.HORIZONTAL)
        self.addSampleButton = wx.Button(self.panel, label="Add a new sample")
        self.sites = list(set(self.ErMagic_data.Data_hierarchy['sites'].keys()).union(self.ErMagic_data.data_er_sites.keys())) # adds in any additional samples we might have information about (from er_sites.txt file) even if currently that sample does not show up in the magic_measurements file
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

        ### Create Containers ###
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.AddSpacer(10)
        vbox.Add(label, flag=wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, border=10)

        vbox.Add(hbox_one, flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=10)
        vbox.Add(hboxok, flag=wx.BOTTOM|wx.LEFT, border=10)
        vbox.Add(self.spec_grid, flag=wx.ALL, border=10)#|wx.EXPAND, border=30)
        
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

        # using ScrolledWindow works on up to date wxPython and is necessary for windows
        # it breaks with Canopy wxPython, so for Mac we just use Panel
        if sys.platform in ['win32', 'win64']:
            self.panel = wx.ScrolledWindow(self, style=wx.SIMPLE_BORDER)
        else:
            self.panel = wx.Panel(self, style=wx.SIMPLE_BORDER)

        if self.sample_window == 1:
            text = """Step 2:
Check that all samples are correctly named,
and that they belong to the correct site
(if site name is simply wrong, that will be fixed in step 3)"""
            step_label = wx.StaticText(self.panel, label=text)#, size=(900, 100))
        else:
            self.ErMagic_data.read_MagIC_info() # ensures that changes from step 3 propagate

            text = """Step 4:
Some of the data from the er_sites table has propogated into er_samples.
Check that this data is correct, and fill in missing cells using controlled vocabularies.
The columns for class, lithology, and type can take multiple values in the form of a colon-delimited list.
You may use the drop-down menus to add as many values as needed in these columns.  
(see Help button for more details)\n\n** Denotes controlled vocabulary"""
            step_label = wx.StaticText(self.panel, label=text)#, size=(900, 100))
        #self.Data_hierarchy = self.ErMagic.Data_hierarchy
        self.samples = sorted(self.ErMagic_data.Data_hierarchy['samples'].keys())
        sites = sorted(self.ErMagic_data.Data_hierarchy['sites'].keys())
        self.locations = sorted(list(set(self.ErMagic_data.Data_hierarchy['locations'].keys()).union(self.ErMagic_data.data_er_locations.keys())))

        if self.sample_window == 1:
            self.samp_grid = self.make_simple_table(['er_sample_name', 'er_site_name'], self.ErMagic_data.data_er_samples, 'er_sample_name')

        if self.sample_window > 1:
            for val in ['er_citation_names', 'er_location_name', 'er_site_name', 'er_sample_name', 'sample_class', 'sample_lithology', 'sample_type', 'sample_lat', 'sample_lon']:
                try:
                    self.ErMagic_data.er_samples_header.remove(val)
                except ValueError:
                    pass
            self.ErMagic_data.er_samples_header.sort()
            self.ErMagic_data.er_samples_header[:0] = ['er_sample_name', 'er_site_name', 'er_citation_names', 'sample_class', 'sample_lithology', 'sample_type', 'sample_lat', 'sample_lon', 'er_location_name']
            self.samp_grid = self.make_simple_table(self.ErMagic_data.er_samples_header, self.ErMagic_data.data_er_samples, 'er_sample_name')

        # add in any additional sets we might have information about (from er_sites.txt file) even if currently that site does not show up in the magic_measurements file
        sites = sorted(list(set(sites).union(self.ErMagic_data.data_er_sites.keys()))) 
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


        ### Make Containers ###
        vbox = wx.BoxSizer(wx.VERTICAL)
        #vbox.Add(step_label, flag=wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, border=20)
        vbox.Add(step_label, flag=wx.ALIGN_LEFT|wx.TOP|wx.BOTTOM, border=20)

        vbox.Add(hbox_one, flag=wx.BOTTOM|wx.LEFT, border=10)
        vbox.Add(hboxok, flag=wx.BOTTOM|wx.LEFT, border=10)
        vbox.Add(self.samp_grid, flag=wx.ALL, border=10) # using wx.EXPAND or not does not affect re-size problem

        hbox_all = wx.BoxSizer(wx.HORIZONTAL)
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
        self.sites = sorted(self.ErMagic_data.Data_hierarchy['sites'].keys())

        for val in ['er_citation_names', 'er_location_name', 'er_site_name', 'site_class', 'site_lithology', 'site_type', 'site_definition', 'site_lat', 'site_lon']: #
            try:
                self.ErMagic_data.er_sites_header.remove(val)
            except ValueError:
                pass
        self.ErMagic_data.er_sites_header.sort()
        self.ErMagic_data.er_sites_header[:0] = ['er_site_name', 'er_location_name', 'er_citation_names', 'site_class', 'site_lithology', 'site_type', 'site_definition', 'site_lon', 'site_lat']

        self.site_grid = self.make_simple_table(self.ErMagic_data.er_sites_header, self.ErMagic_data.data_er_sites, 'er_site_name')

        # populate site_definition as 's' by default if no value is provided (indicates that site is single, not composite)
        rows = self.site_grid.GetNumberRows()
        col = 6
        for row in range(rows):
            cell = self.site_grid.GetCellValue(row, col)
            if not cell:
                self.site_grid.SetCellValue(row, col, 's')

        # initialize all needed drop-down menus
        locations = sorted(set(self.ErMagic_data.data_er_locations.keys()))
        self.drop_down_menu = drop_down_menus.Menus("site", self, self.site_grid, locations) 

        ### Create Buttons ###
        hbox_one = wx.BoxSizer(wx.HORIZONTAL)
        self.addLocButton = wx.Button(self.panel, label="Add a new location")
        self.locations = list(set(self.ErMagic_data.Data_hierarchy['sites'].keys()).union(self.ErMagic_data.data_er_locations.keys()))
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


        ### Make Containers ###
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(label, flag=wx.ALIGN_CENTER|wx.BOTTOM|wx.TOP, border=20)
        vbox.Add(hbox_one, flag=wx.BOTTOM|wx.LEFT, border=10)
        vbox.Add(hboxok, flag=wx.BOTTOM|wx.LEFT, border=10)
        vbox.Add(self.site_grid, flag=wx.ALL|wx.EXPAND, border=10) # EXPAND ??

        hbox_all = wx.BoxSizer(wx.HORIZONTAL)
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

        text = """Step 5:
Check that locations are correctly named.
Fill in any blank cells using controlled vocabularies.
(See Help button for details)

** Denotes controlled vocabulary"""
        label = wx.StaticText(self.panel, label=text)
        #self.Data_hierarchy = self.ErMagic.Data_hierarchy
        self.locations = self.ErMagic_data.Data_hierarchy['locations']
        #
        try:
            key1 = self.ErMagic_data.data_er_locations.keys()[0]
        except IndexError:
            msg = "You have no data in er_locations, so we are skipping step 5.\n Note that location names must be entered at the measurements level,so you may need to re-import your data, or you can add a location in step 3"
            dlg = wx.MessageDialog(None, caption="Message:", message=msg, style=wx.OK|wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.panel.Destroy()
            self.InitAgeCheck()
            return

        for val in ['er_location_name', 'location_type']:
            try:
                self.ErMagic_data.er_locations_header.remove(val)
            except ValueError:
                pass
        self.ErMagic_data.er_locations_header[:0] = ['er_location_name', 'location_type']

        self.loc_grid = self.make_simple_table(self.ErMagic_data.er_locations_header, self.ErMagic_data.data_er_locations, "er_location_name")
        # initialize all needed drop-down menus
        self.drop_down_menu = drop_down_menus.Menus("location", self, self.loc_grid, None) 

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

        ### Make Containers ###
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(label, flag=wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, border=20)
        vbox.Add(hbox_one, flag=wx.BOTTOM|wx.ALIGN_LEFT, border=10)
        vbox.Add(hboxok, flag=wx.BOTTOM|wx.ALIGN_LEFT, border=10)
        vbox.Add(self.loc_grid, flag=wx.TOP|wx.BOTTOM, border=10)

        hbox_all = wx.BoxSizer(wx.HORIZONTAL)
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

        text = """Step 6:
Fill in or correct any cells with information about ages.
The column for magic_method_codes can take multiple values in the form of a colon-delimited list.
You may use the drop-down menus to add as many values as needed in these columns.  
(See Help button for details)

**Denotes controlled vocabulary """
        label = wx.StaticText(self.panel, label=text)
        #self.Data_hierarchy = self.ErMagic.Data_hierarchy
        self.sites = self.ErMagic_data.Data_hierarchy['sites']
        #
        #key1 = self.ErMagic_data.data_er_ages.keys()[0]

        for col_label in ['er_site_name', 'er_location_name', 'er_citation_names', 'magic_method_codes', 'age_description', 'age_unit', 'age']:
            try:
                self.ErMagic_data.er_ages_header.remove(col_label)
            except ValueError:
                pass

        self.ErMagic_data.er_ages_header[:0] = ['er_site_name', 'er_location_name', 'er_citation_names', 'magic_method_codes', 'age_description', 'age_unit', 'age']
        # only use sites that are associated with actual samples/specimens

        #ages_data_dict = {k: v for k, v in self.ErMagic.data_er_ages.items() if k in self.sites} # fails in Python 2.6
        ages_data_dict = {}
        for k, v in self.ErMagic_data.data_er_ages.items():
            if k in self.sites:
                ages_data_dict[k] = v

        self.age_grid = self.make_simple_table(self.ErMagic_data.er_ages_header, ages_data_dict, "ages")
        #
        # make it impossible to edit the 1st and 3rd columns
        for row in range(self.age_grid.GetNumberRows()):
            for col in (0, 2):
                self.age_grid.SetReadOnly(row, col, True)

        # initialize all needed drop-down menus
        self.drop_down_menu = drop_down_menus.Menus("age", self, self.age_grid, None)

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

        hbox_all = wx.BoxSizer(wx.HORIZONTAL)
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
        if len(row_labels) in range(1, 4):
            num_rows = len(row_labels)
            height = {1: 70, 2: 90, 3: 110, 4: 130}
            grid = MagicGrid(self.panel, grid_name, row_labels, column_labels, (-1, height[num_rows])) # autosizes width, but enforces fixed pxl height to prevent display problems
        else:
            grid = MagicGrid(self.panel, grid_name, row_labels, column_labels)

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

        #if not self.ErMagic_data.data_er_samples:
        #    self.ErMagic_data.read_MagIC_info()

        pw.AddItem(self, 'Sample', add_sample, self.sites, 'site') # makes window for adding new data

        def add_sample_data(sample, site):
            # add sample
            self.ErMagic_data.add_sample(sample, site)
            # re-Bind so that the updated samples list shows up on a left click
            samples = sorted(self.ErMagic_data.Data_hierarchy['samples'].keys())
            samples = sorted(list(set(samples).union(self.ErMagic_data.data_er_samples.keys())))
            choices = self.drop_down_menu.choices
            choices[2] = (samples, False)
            self.drop_down_menu.update_drop_down_menu(self.spec_grid, choices)
            # update ErMagic files
            self.ErMagic_data.update_ErMagic()

            
    def on_addSiteButton(self, event):
        
        def add_site(site, location):
            add_site_data(site, location)

        pw.AddItem(self, 'Site', add_site, self.locations, 'location')

        def add_site_data(site, location):
            # add site
            self.ErMagic_data.add_site(site, location)
            # re-Bind so that the updated sites list shows up on a left click
            sites = sorted(self.ErMagic_data.Data_hierarchy['sites'].keys())
            sites = sorted(list(set(sites).union(self.ErMagic_data.data_er_sites.keys())))
            self.drop_down_menu.update_drop_down_menu(self.samp_grid, {2: (sites, False)})
            # update ErMagic files
            self.ErMagic_data.update_ErMagic()


    def on_addLocButton(self, event):

        def add_loc(loc):
            add_loc_data(loc)

        #def __init__(self, parent, title, data_items, data_method):

        if not self.ErMagic_data.data_er_locations:
            pass
            
        pw.AddItem(self, 'Location', add_loc, owner_items=None, belongs_to=None) # makes window for adding new data

        def add_loc_data(loc):
            # add location
            self.ErMagic_data.add_location(loc)
            # re-Bind so that the updated locations list shows up on a left click
            locations = sorted(self.ErMagic_data.Data_hierarchy['locations'].keys())
            locations = sorted(list(set(locations).union(self.ErMagic_data.data_er_locations.keys())))
            choices = self.drop_down_menu.choices
            choices[2] = (locations, False)
            self.drop_down_menu.update_drop_down_menu(self.site_grid, choices)
            # update ErMagic files
            self.ErMagic_data.update_ErMagic()


    def on_helpButton(self, event, page=None):
        """shows html help page"""
        # for use on the command line:
        path = check_updates.get_pmag_dir()

        # for use with pyinstaller
        #path = self.main_frame.resource_dir
        
        html_frame = pw.HtmlFrame(self, page=(os.path.join(path, 'help_files', page)))
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
        self.remove_starred_labels(grid)

        if self.ErMagic_data.data_er_specimens:
            pass
        else:
            self.ErMagic_data.read_MagIC_info()
        grid.SaveEditControlValue() # locks in value in cell currently edited
        grids = {"er_specimen_name": self.ErMagic_data.data_er_specimens, "er_sample_name": self.ErMagic_data.data_er_samples, "er_site_name": self.ErMagic_data.data_er_sites, "er_location_name": self.ErMagic_data.data_er_locations, "ages": self.ErMagic_data.data_er_ages}
        grid_name = str(grid.GetName())

        # check that all required data is present
        validation_errors = self.validate(grid)
        if validation_errors:
            result = pw.warning_with_override("You are missing required data in these columns: {}\nAre you sure you want to continue without this data?".format(str(validation_errors)))
            if result == wx.ID_YES:
                pass
            else:
                return False

        if grid.changes:
            self.update_grid(grid)#, grids[grid_name])

            # possibly optimize this so that it only updates the required files
            self.ErMagic_data.update_ErMagic()
            
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
            self.drop_down_menu.clean_up()

        # remove '**' from col labels
        starred_cols = self.remove_starred_labels(grid)

        if self.ErMagic_data.data_er_specimens:
            pass
        else:
            self.ErMagic_data.read_MagIC_info()
        grid.SaveEditControlValue() # locks in value in cell currently edited
        grid.HideCellEditControl() # removes focus from cell that was being edited

        if grid.changes:
            self.update_grid(grid)#, grids[grid_name])

            # possibly optimize this so that it only updates the required files
            self.ErMagic_data.update_ErMagic()

        for col in starred_cols:
            label = grid.GetColLabelValue(col)
            grid.SetColLabelValue(col, label+'**')
        del wait

    def on_cancelButton(self, event):
        self.Destroy()

    def on_backButton(self, event, previous_dia, current_dia=None):
        wait = wx.BusyInfo("Please wait, working...")
        if current_dia == self.InitLocCheck:
            pass
        elif previous_dia == self.InitSpecCheck or previous_dia == self.InitSampCheck:
            self.sample_window = 0
        self.panel.Destroy()
        previous_dia()
        del wait


    ### Manage data methods ###
    def update_grid(self, grid):#, data):
        """
        takes in wxPython grid and ErMagic data object to be updated
        """
        data_methods = {'er_specimen_name': self.ErMagic_data.change_specimen, 'er_sample_name': self.ErMagic_data.change_sample, 'er_site_name': self.ErMagic_data.change_site, 'er_location_name': self.ErMagic_data.change_location, 'ages': self.ErMagic_data.change_age}

        grid_name = str(grid.GetName())

        #rows = range(grid.GetNumberRows())
        cols = range(grid.GetNumberCols())

        col_labels = []
        for col in cols:
            col_labels.append(grid.GetColLabelValue(col))

        for row in grid.changes: # go through changes and update data structures
            data_dict = {}
            for num, label in enumerate(col_labels):
                if label:
                    data_dict[str(label)] = str(grid.GetCellValue(row, num))
            new_name = str(grid.GetCellValue(row, 0))
            old_name = self.temp_data[grid_name][row]
            data_methods[grid_name](new_name, old_name, data_dict)

        grid.changes = False


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
        remove_extras(self.ErMagic_data.data_er_specimens, self.ErMagic_data.Data_hierarchy['specimens'])
        remove_extras(self.ErMagic_data.data_er_samples, self.ErMagic_data.Data_hierarchy['samples'])
        remove_extras(self.ErMagic_data.data_er_sites, self.ErMagic_data.Data_hierarchy['sites'])
        remove_extras(self.ErMagic_data.data_er_locations, self.ErMagic_data.Data_hierarchy['locations'])
        #remove_extras(self.Data_hierarchy['locations'], self.ErMagic.data_er_locations)
        remove_extras(self.ErMagic_data.data_er_ages, self.ErMagic_data.Data_hierarchy['sites'])
        self.ErMagic_data.update_ErMagic()

        

class MagicGrid(wx.grid.Grid):
    """
    grid class
    """

    def __init__(self, parent, name, row_labels, col_labels, size=0):
        self.changes = None
        self.row_labels = row_labels
        self.col_labels = col_labels
        if not size:
            super(MagicGrid, self).__init__(parent, -1, name=name)
        if size:
            super(MagicGrid, self).__init__(parent, -1, name=name, size=size)
        #self.InitUI()

    def InitUI(self):
        data = []
        num_rows = len(self.row_labels)
        num_cols = len(self.col_labels)
        self.ClearGrid()
        self.CreateGrid(num_rows, num_cols)
        for n, row in enumerate(self.row_labels):
            self.SetRowLabelValue(n, str(n+1))
            self.SetCellValue(n, 0, row)
            data.append(row)
        # set column labels
        for n, col in enumerate(self.col_labels):
            self.SetColLabelValue(n, str(col))
        return data

    def add_data(self, data_dict):
        for num, row in enumerate(self.row_labels):
            for n, col in enumerate(self.col_labels[1:]):
                if col in data_dict[row].keys():
                    value = data_dict[row][col]
                else:
                    value = ''
                if value:
                    self.SetCellValue(num, n+1, value)

    def size_grid(self):
        self.AutoSizeColumns(True)

        ## this doesn't seem to be necessary, actually
        self.AutoSize() # prevents display failure

        for col in range(len(self.col_labels)):
            # adjust column widths to be a little larger then auto for nicer editing
            orig_size = self.GetColSize(col)
            if orig_size > 110:
                size = orig_size * 1.1
            else:
                size = orig_size * 1.6
            self.SetColSize(col, size)

    def do_event_bindings(self):
        self.Bind(wx.grid.EVT_GRID_EDITOR_CREATED, self.on_edit_grid)
        self.Bind(wx.grid.EVT_GRID_EDITOR_SHOWN, self.on_edit_grid)

    def on_edit_grid(self, event):
        """sets self.changes to true when user edits the grid.
        provides down and up key functionality for exiting the editor"""
        if not self.changes:
            self.changes = {event.Row}
        else:
            self.changes.add(event.Row)
        #self.changes = True
        try:
            editor = event.GetControl()
            editor.Bind(wx.EVT_KEY_DOWN, self.onEditorKey)
        except AttributeError:
            # if it's a EVT_GRID_EDITOR_SHOWN, it doesn't have the GetControl method
            pass

    def onEditorKey(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_UP:
            self.MoveCursorUp(False)
            self.MoveCursorDown(False)# have this in because otherwise cursor moves up 2 rows
        elif keycode == wx.WXK_DOWN:
            self.MoveCursorDown(False)
            self.MoveCursorUp(False) # have this in because otherwise cursor moves down 2 rows
        #elif keycode == wx.WXK_LEFT:
        #    grid.MoveCursorLeft(False)
        #elif keycode == wx.WXK_RIGHT:
        #    grid.MoveCursorRight(False)
        else:
            pass
        event.Skip()


    def add_row(self, label=''):
        self.AppendRows(1)
        last_row = self.GetNumberRows() - 1
        self.SetCellValue(last_row, 0, label)
        self.row_labels.append(label)

    def remove_row(self, row_num=None):
        #DeleteRows(self, pos, numRows, updateLabel
        if not row_num:
            row_num = self.GetNumberRows() - 1
        label = self.GetCellValue(row_num, 0)
        self.DeleteRows(pos=row_num, numRows=1, updateLabels=True)
        self.row_labels.remove(label)

        
    def add_col(self, label):
        self.AppendCols(1)
        last_col = self.GetNumberCols() - 1
        self.SetColLabelValue(last_col, label)
        self.col_labels.append(label)

        # after adding, either:
        self.size_grid()
        # or perhaps self.InitUI() and self.size_grid()

    def remove_col(self, col_num):
        print 'REMOVING COL'
        label_value = self.GetColLabelValue(col_num)
        print 'label_value', label_value
        print 'col_num', col_num
        self.col_labels.remove(label_value)
        result = self.DeleteCols(pos=col_num, numCols=1, updateLabels=True) # ??
        self.size_grid()
        return result


    ### Grid methods ###
    """
    def onMouseOver(self, event, grid):
      "
        Displays a tooltip over any cell in a certain column

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
        sets self.changes to true when user edits the grid.
        provides down and up key functionality for exiting the editor
        if not self.changes:
            self.changes = {event.Row}
        else:
            self.changes.add(event.Row)
        #self.changes = True
        try:
            editor = event.GetControl()
            editor.Bind(wx.EVT_KEY_DOWN, lambda event: self.onEditorKey(event, grid))
        except AttributeError: # if it's a EVT_GRID_EDITOR_SHOWN, it doesn't have the GetControl method
            pass

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
    """

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


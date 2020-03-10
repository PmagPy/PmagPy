"""
dialogs for ErMagicBuilder
"""
# pylint: disable=W0612,C0111,C0103,W0201,C0301

import wx
import wx.grid
import numpy as np
from pmagpy import contribution_builder as cb
from . import pmag_widgets as pw
from . import grid_frame3



class ErMagicCheckFrame3(wx.Frame):

    def __init__(self, parent, title, WD, contribution):
        wx.Frame.__init__(self, parent, -1, title)
        self.WD = WD
        self.main_frame = self.Parent
        self.contribution = contribution
        self.temp_data = {}
        self.grid = None
        self.deleteRowButton = None
        self.selected_rows = set()
        self.min_size = (1160, 350)
        self.contribution.propagate_ages()
        # re-do the 'quit' binding so that it only closes the current window
        self.main_frame.Bind(wx.EVT_MENU, lambda event: self.main_frame.menubar.on_quit(event, self), self.main_frame.menubar.file_quit)
        self.InitSpecCheck()


    def InitSpecCheck(self):
        """
        make an interactive grid in which users can edit specimen names
        as well as which sample a specimen belongs to
        """
        #wait = wx.BusyInfo("Please wait, working...")
        #wx.SafeYield()
        self.contribution.propagate_lithology_cols()
        spec_df = self.contribution.tables['specimens'].df
        self.panel = wx.Panel(self, style=wx.SIMPLE_BORDER)
        self.grid_frame = grid_frame3.GridFrame(self.contribution, self.WD,
                                                'specimens', 'specimens', self.panel,
                                                 main_frame=self.main_frame)
        # redefine default 'save & exit grid' button to go to next dialog instead
        self.grid_frame.exitButton.SetLabel('Save and continue')
        grid = self.grid_frame.grid
        self.grid_frame.Bind(wx.EVT_BUTTON,
                             lambda event: self.onContinue(event, grid, self.InitSampCheck),
                             self.grid_frame.exitButton)

            # add back button
        self.backButton = wx.Button(self.grid_frame.panel, id=-1, label='Back',
                                      name='back_btn')
        self.backButton.Disable()
        self.grid_frame.main_btn_vbox.Add(self.backButton, flag=wx.ALL, border=5)
        # re-do fit
        self.grid_frame.do_fit(None, self.min_size)
        # center
        self.grid_frame.Centre()
        return


    def InitSampCheck(self):
        """
        make an interactive grid in which users can edit sample names
        as well as which site a sample belongs to
        """
        # propagate any type/lithology/class data from sites to samples table
        # will only overwrite if sample values are blank
        self.contribution.propagate_lithology_cols()
        samp_df = self.contribution.tables['samples'].df
        self.panel = wx.Panel(self, style=wx.SIMPLE_BORDER)
        self.grid_frame = grid_frame3.GridFrame(self.contribution, self.WD,
                                                'samples', 'samples', self.panel,
                                                main_frame=self.main_frame)
        # redefine default 'save & exit grid' button to go to next dialog instead
        self.grid_frame.exitButton.SetLabel('Save and continue')
        next_dia = self.InitSiteCheck
        prev_dia = self.InitSpecCheck
        grid = self.grid_frame.grid
        self.grid_frame.Bind(wx.EVT_BUTTON,
                             lambda event: self.onContinue(event, grid, next_dia),
                             self.grid_frame.exitButton)
        # add back button
        self.backButton = wx.Button(self.grid_frame.panel, id=-1, label='Back',
                                      name='back_btn')
        self.Bind(wx.EVT_BUTTON,
                  lambda event: self.onbackButton(event, prev_dia),
                  self.backButton)
        self.grid_frame.main_btn_vbox.Add(self.backButton, flag=wx.ALL, border=5)
        # re-do fit
        self.grid_frame.do_fit(None, self.min_size)
        # center
        self.grid_frame.Centre()
        return


    def InitSiteCheck(self):
        """
        make an interactive grid in which users can edit site names
        as well as which location a site belongs to
        """
        # propagate average lat/lon info from samples table if
        # available in samples and missing in sites
        self.contribution.propagate_average_up(cols=['lat', 'lon', 'height'],
                                       target_df_name='sites',
                                       source_df_name='samples')
        # propagate lithology columns
        self.contribution.propagate_lithology_cols()

        site_df = self.contribution.tables['sites'].df
        self.panel = wx.Panel(self, style=wx.SIMPLE_BORDER)
        self.grid_frame = grid_frame3.GridFrame(self.contribution, self.WD,
                                                'sites', 'sites', self.panel,
                                                 main_frame=self.main_frame)
        # redefine default 'save & exit grid' button to go to next dialog instead
        self.grid_frame.exitButton.SetLabel('Save and continue')
        grid = self.grid_frame.grid
        self.grid_frame.Bind(wx.EVT_BUTTON,
                             lambda event: self.onContinue(event, grid, self.InitLocCheck),
                             self.grid_frame.exitButton)
        # add back button
        self.backButton = wx.Button(self.grid_frame.panel, id=-1, label='Back',
                                      name='back_btn')
        self.Bind(wx.EVT_BUTTON,
                  lambda event: self.onbackButton(event, self.InitSampCheck),
                  self.backButton)
        self.grid_frame.main_btn_vbox.Add(self.backButton, flag=wx.ALL, border=5)
        # re-do fit
        self.grid_frame.do_fit(None, self.min_size)
        # center
        self.grid_frame.Centre()
        return


    def InitLocCheck(self):
        """
        make an interactive grid in which users can edit locations
        """
        # if there is a location without a name, name it 'unknown'
        self.contribution.rename_item('locations', 'nan', 'unknown')
        # propagate lat/lon values from sites table
        self.contribution.get_min_max_lat_lon()
        # propagate lithologies & geologic classes from sites table
        self.contribution.propagate_cols_up(['lithologies',
                                             'geologic_classes'], 'locations', 'sites')
        res = self.contribution.propagate_min_max_up()
        if cb.not_null(res):
            self.contribution.propagate_cols_up(['age_unit'], 'locations', 'sites')

        # set up frame
        self.panel = wx.Panel(self, style=wx.SIMPLE_BORDER)
        self.grid_frame = grid_frame3.GridFrame(self.contribution, self.WD,
                                                'locations', 'locations', self.panel,
                                                main_frame=self.main_frame)
        # redefine default 'save & exit grid' button to go to next dialog instead
        self.grid_frame.exitButton.SetLabel('Save and continue')
        grid = self.grid_frame.grid
        self.grid_frame.Bind(wx.EVT_BUTTON,
                             lambda event: self.onContinue(event, grid, self.InitAgeCheck),
                             self.grid_frame.exitButton)
        # add back button
        self.backButton = wx.Button(self.grid_frame.panel, id=-1, label='Back',
                                      name='back_btn')
        self.Bind(wx.EVT_BUTTON,
                  lambda event: self.onbackButton(event, self.InitSiteCheck),
                  self.backButton)
        self.grid_frame.main_btn_vbox.Add(self.backButton, flag=wx.ALL, border=5)
        # re-do fit
        self.grid_frame.do_fit(None, min_size=self.min_size)
        # center
        self.grid_frame.Centre()
        return


    def InitAgeCheck(self):
        """make an interactive grid in which users can edit ages"""
        age_df = self.contribution.tables['ages'].df
        self.panel = wx.Panel(self, style=wx.SIMPLE_BORDER)
        self.grid_frame = grid_frame3.GridFrame(self.contribution, self.WD,
                                                'ages', 'ages', self.panel,
                                                 main_frame=self.main_frame)
        self.grid_frame.exitButton.SetLabel('Save and continue')
        grid = self.grid_frame.grid
        self.grid_frame.Bind(wx.EVT_BUTTON, lambda event: self.onContinue(event, grid, None),
                             self.grid_frame.exitButton)
        # add back button
        self.backButton = wx.Button(self.grid_frame.panel, id=-1, label='Back',
                                      name='back_btn')
        self.Bind(wx.EVT_BUTTON,
                  lambda event: self.onbackButton(event, self.InitLocCheck),
                  self.backButton)
        self.grid_frame.main_btn_vbox.Add(self.backButton, flag=wx.ALL, border=5)
        # re-do fit
        self.grid_frame.do_fit(None, self.min_size)
        # center
        self.grid_frame.Centre()
        return

    def on_close_grid_frame(self, event=None):
        # required placeholder
        pass

    def onContinue(self, event, grid, next_dia=None):#, age_data_type='site'):
        """
        Save grid data in the data object
        """
        # deselect column, including remove 'EDIT ALL' label
        if self.grid_frame.drop_down_menu:
            self.grid_frame.drop_down_menu.clean_up()

        # remove '**' and '^^' from col names
        #self.remove_starred_labels(grid)
        grid.remove_starred_labels()

        grid.SaveEditControlValue() # locks in value in cell currently edited
        grid_name = str(grid.GetName())

        # save all changes to data object and write to file
        self.grid_frame.grid_builder.save_grid_data()

        # check that all required data are present
        validation_errors = self.validate(grid)
        if validation_errors:
            warn_string = ""
            for error_name, error_cols in list(validation_errors.items()):
                if error_cols:
                    warn_string += "You have {}: {}.\n\n".format(error_name, ", ".join(error_cols))
            warn_string += "Are you sure you want to continue?"
            result = pw.warning_with_override(warn_string)
            if result == wx.ID_YES:
                pass
            else:
                return False
        else:
            wx.MessageBox('Saved!', 'Info',
                          style=wx.OK | wx.ICON_INFORMATION)

        self.panel.Destroy()
        if next_dia:
            next_dia()
        else:
            # propagate any type/lithology/class data from sites to samples table
            # will only overwrite if sample values are blank or "Not Specified"
            self.contribution.propagate_lithology_cols()
            wx.MessageBox('Done!', 'Info',
                          style=wx.OK | wx.ICON_INFORMATION)
            # show main frame
            self.main_frame.Show()


    def onbackButton(self, event=None, prev_dia=None):
        if prev_dia:
            alert = True if self.grid_frame.grid.changes else False
            self.grid_frame.onSave(event=None, alert=alert, destroy=True)
            #if self.grid_frame.grid.name == 'samples':
            #    self.sample_window -= 2
            self.panel.Destroy()
            prev_dia()


    def validate(self, grid):
        """
        Using the MagIC data model, generate validation errors on a MagicGrid.

        Parameters
        ----------
        grid : dialogs.magic_grid3.MagicGrid
               The MagicGrid to be validated

        Returns
        ---------
        warnings: dict
                  Empty dict if no warnings, otherwise a dict with format {name of problem: [problem_columns]}
        """
        grid_name = str(grid.GetName())
        dmodel = self.contribution.dmodel
        reqd_headers = dmodel.get_reqd_headers(grid_name)
        df = self.contribution.tables[grid_name].df
        df = df.replace('', np.nan) # python does not view empty strings as null
        if df.empty:
            return {}
        col_names = set(df.columns)
        missing_headers = set(reqd_headers) - col_names
        present_headers = set(reqd_headers) - set(missing_headers)
        non_null_headers = df.dropna(how='all', axis='columns').columns
        null_reqd_headers = present_headers - set(non_null_headers)
        if any(missing_headers) or any (null_reqd_headers):
            warnings = {'missing required column(s)': sorted(missing_headers),
                        'no data in required column(s)': sorted(null_reqd_headers)}
        else:
            warnings = {}
        return warnings


    def on_saveButton(self, event, grid):
        """saves any editing of the grid but does not continue to the next window"""
        wait = wx.BusyInfo("Please wait, working...")
        wx.SafeYield()

        if self.grid_frame.drop_down_menu:  # unhighlight selected columns, etc.
            self.grid_frame.drop_down_menu.clean_up()

        # remove '**' and '^^' from col labels
        starred_cols, hatted_cols = grid.remove_starred_labels()

        grid.SaveEditControlValue() # locks in value in cell currently edited
        grid.HideCellEditControl() # removes focus from cell that was being edited

        if grid.changes:
            self.onSave(grid)

        for col in starred_cols:
            label = grid.GetColLabelValue(col)
            grid.SetColLabelValue(col, label + '**')
        for col in hatted_cols:
            label = grid.GetColLabelValue(col)
            grid.SetColLabelValue(col, label + '^^')
        del wait


    def on_backButton(self, event, previous_dia, current_dia=None):
        # save first?
        if self.grid.changes:
            result = pw.warning_with_override("You have unsaved data which will be lost. Are you sure you want to go back?")
            if result == wx.ID_NO:
                return
        # go back to previous grid
        wait = wx.BusyInfo("Please wait, working...")
        wx.SafeYield()
        if current_dia == self.InitLocCheck:
            pass
        #elif previous_dia == self.InitSpecCheck or previous_dia == self.InitSampCheck:
        #    self.sample_window = 0
        self.panel.Destroy()
        previous_dia()
        del wait


    ### Manage data methods ###

    def onSave(self, grid):#, age_data_type='site'):
        """
        Save grid data in the data object
        """
        # deselect column, including remove 'EDIT ALL' label
        if self.grid_frame.drop_down_menu:
            self.grid_frame.drop_down_menu.clean_up()

        # save all changes to data object and write to file
        self.grid_builder.save_grid_data()

        wx.MessageBox('Saved!', 'Info',
                      style=wx.OK | wx.ICON_INFORMATION)

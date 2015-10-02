import wx
#import wx.lib.buttons as buttons
#import sys
#import os
#import ErMagicBuilder
import builder
import pmag
#import ipmag
import drop_down_menus
import pmag_widgets as pw
import magic_grid
#import pmag_menu_dialogs
#import validate_upload



class GridFrame(wx.Frame):
    """
    make_magic
    """

    def __init__(self, ErMagic, WD=None, frame_name="grid frame",
                 panel_name="grid panel", parent=None):
        self.parent = parent
        wx.GetDisplaySize()
        title = 'Edit {} data'.format(panel_name)
        wx.Frame.__init__(self, parent=parent, id=wx.ID_ANY, name=frame_name, title=title)

        self.remove_cols_mode = False
        self.deleteRowButton = None
        self.selected_rows = set()

        self.er_magic = ErMagic

        self.panel = wx.Panel(self, name=panel_name, size=wx.GetDisplaySize())
        self.grid_type = panel_name

        if self.parent:
            self.Bind(wx.EVT_WINDOW_DESTROY, self.parent.Parent.on_close_grid_frame)

        if self.grid_type == 'age':
            ancestry_ind = self.er_magic.ancestry.index(self.er_magic.age_type)
            self.child_type = self.er_magic.ancestry[ancestry_ind-1]#'sample'
            self.parent_type = self.er_magic.ancestry[ancestry_ind+1]#'location'
        else:
            try:
                self.child_type = self.er_magic.ancestry[self.er_magic.ancestry.index(self.grid_type) - 1]
                self.parent_type = self.er_magic.ancestry[self.er_magic.ancestry.index(self.grid_type) + 1]
            except ValueError:
                self.child_type = None
                self.parent_type = None

        #self.current_age_type = 'site'
        self.WD = WD
        self.InitUI()


    ## Initialization functions
    
    def InitUI(self):
        """
        initialize window
        """
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.init_grid_headers()
        self.grid_builder = GridBuilder(self.er_magic, self.grid_type, self.grid_headers,
                                        self.panel, self.parent_type)
        self.grid = self.grid_builder.make_grid()
        self.grid.InitUI()

        self.add_cols_button = wx.Button(self.panel, label="Add additional columns", name='add_cols_btn')
        self.Bind(wx.EVT_BUTTON, self.on_add_cols, self.add_cols_button)
        self.remove_cols_button = wx.Button(self.panel, label="Remove columns", name='remove_cols_btn')
        self.Bind(wx.EVT_BUTTON, self.on_remove_cols, self.remove_cols_button)
        self.remove_row_button = wx.Button(self.panel, label="Remove last row", name='remove_last_row_btn')
        self.Bind(wx.EVT_BUTTON, self.on_remove_row, self.remove_row_button)
        many_rows_box = wx.BoxSizer(wx.HORIZONTAL)
        self.add_many_rows_button = wx.Button(self.panel, label="Add row(s)", name='add_many_rows_btn')
        self.rows_spin_ctrl = wx.SpinCtrl(self.panel, value='1', initial=1, name='rows_spin_ctrl')
        many_rows_box.Add(self.add_many_rows_button, flag=wx.ALIGN_CENTRE)
        many_rows_box.Add(self.rows_spin_ctrl)
        self.Bind(wx.EVT_BUTTON, self.on_add_rows, self.add_many_rows_button)

        #hbox_grid = pw.hbox_grid(self.panel, self.on_remove_row, self.panel.Name, self.grid)
        self.deleteRowButton = wx.Button(self.panel, id=-1, label='Delete selected row(s)', name='delete_row_btn')
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_remove_row(event, False), self.deleteRowButton)
        self.deleteRowButton.Disable()
        #self.deleteRowButton = hbox_grid.deleteRowButton

        self.msg_boxsizer = wx.StaticBoxSizer(wx.StaticBox(self.panel, -1, name='msg_boxsizer'), wx.VERTICAL)
        self.default_msg_text = 'Edit {} here.\nYou can add or remove both rows and columns, however required columns may not be deleted.\nControlled vocabularies are indicated by **, and will have drop-down-menus.\nTo edit all values in a column, click the column header.\nYou can cut and paste a block of cells from an Excel-like file.\nJust click the top left cell and use command "v".'.format(self.grid_type + 's')
        txt = ''
        
        if self.grid_type == 'location':
            txt = '\n\nNote: you can fill in location start/end latitude/longitude here.\nHowever, if you add sites in step 2, the program will calculate those values automatically,\nbased on site latitudes/logitudes.\nThese values will be written to your upload file.'

        if self.grid_type == 'sample':
            txt = "\n\nNote: you can fill in lithology, class, and type for each sample here.\nHowever, if the sample's class, lithology, and type are the same as its parent site, those values will propagate down,\nand will be written to your sample file automatically."

        if self.grid_type == 'specimen':
            txt = "\n\nNote: you can fill in lithology, class, and type for each specimen here.\nHowever, if the specimen's class, lithology, and type are the same as its parent sample, those values will propagate down,\nand will be written to your specimen file automatically."

        if self.grid_type == 'age':
            txt = "\n\nNote: only ages for which you provide data will be written to your upload file."

        self.default_msg_text += txt

        self.msg_text = wx.StaticText(self.panel, label=self.default_msg_text,
                                      style=wx.TE_CENTER, name='msg text')
        self.msg_boxsizer.Add(self.msg_text)

        self.toggle_help_btn = wx.Button(self.panel, id=-1, label="Show help", name='toggle_help_btn')
        self.Bind(wx.EVT_BUTTON, self.toggle_help, self.toggle_help_btn)
        self.msg_boxsizer.ShowItems(False)

        self.importButton = wx.Button(self.panel, id=-1, label='Import MagIC-format file', name='import_btn')
        self.Bind(wx.EVT_BUTTON, self.onImport, self.importButton)
        self.exitButton = wx.Button(self.panel, id=-1, label='Save and close grid', name='save_and_quit_btn')
        self.Bind(wx.EVT_BUTTON, self.onSave, self.exitButton)
        self.cancelButton = wx.Button(self.panel, id=-1, label='Cancel', name='cancel_btn')
        self.Bind(wx.EVT_BUTTON, self.onCancelButton, self.cancelButton)
        #self.pmag_checkbox = pw.check_box(self.panel,
        #                                 "Interpretations at {} level".format(self.grid_type))
        #if self.grid_type in ('location', 'age', 'result'):
        #    self.pmag_checkbox.cb.SetValue(False)
        #    self.pmag_checkbox.cb.Disable()
        #    self.pmag_checkbox.ShowItems(False)
        #else:
        #    if self.grid_type not in self.er_magic.no_pmag_data:
        #        self.pmag_checkbox.cb.SetValue(True)
        #    self.Bind(wx.EVT_CHECKBOX, self.on_pmag_checkbox, self.pmag_checkbox.cb)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        col_btn_vbox = wx.StaticBoxSizer(wx.StaticBox(self.panel, -1, label='Columns'), wx.VERTICAL)
        row_btn_vbox = wx.StaticBoxSizer(wx.StaticBox(self.panel, -1, label='Rows'), wx.VERTICAL)
        main_btn_vbox = wx.StaticBoxSizer(wx.StaticBox(self.panel, -1, label='Manage data'), wx.VERTICAL)
        col_btn_vbox.Add(self.add_cols_button, flag=wx.ALL, border=5)
        col_btn_vbox.Add(self.remove_cols_button, flag=wx.ALL, border=5)
        row_btn_vbox.Add(many_rows_box, flag=wx.ALL, border=5)
        row_btn_vbox.Add(self.remove_row_button, flag=wx.ALL, border=5)
        row_btn_vbox.Add(self.deleteRowButton, flag=wx.ALL, border=5)
        main_btn_vbox.Add(self.importButton, flag=wx.ALL, border=5)
        main_btn_vbox.Add(self.exitButton, flag=wx.ALL, border=5)
        main_btn_vbox.Add(self.cancelButton, flag=wx.ALL, border=5)
        #main_btn_vbox.Add(self.pmag_checkbox, flag=wx.ALL, border=5)
        hbox.Add(col_btn_vbox)
        hbox.Add(row_btn_vbox)
        hbox.Add(main_btn_vbox)

        self.panel.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.onLeftClickLabel, self.grid)

        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.panel.Bind(wx.EVT_TEXT_PASTE, self.do_fit)

        # add actual data!
        self.grid_builder.add_data_to_grid(self.grid, self.grid_type)
        
        if self.grid_type == 'age':
            self.grid_builder.add_age_data_to_grid()

        # add drop_down menus
        if self.parent_type:
            belongs_to = sorted(self.er_magic.data_lists[self.parent_type][0], key=lambda item: item.name)
        else:
            belongs_to = ''
        self.drop_down_menu = drop_down_menus.Menus(self.grid_type, self, self.grid, belongs_to)
        
        self.grid_box = wx.StaticBoxSizer(wx.StaticBox(self.panel, -1), wx.VERTICAL)
        self.grid_box.Add(self.grid, flag=wx.ALL, border=5)

        # a few special touches if it is a location grid
        if self.grid_type == 'location':
            for loc in self.er_magic.locations:
                # try to fill in min/max latitudes/longitudes from sites
                d = self.er_magic.get_min_max_lat_lon(loc.sites)
                col_labels = [self.grid.GetColLabelValue(col) for col in xrange(self.grid.GetNumberCols())]
                row_labels = [self.grid.GetCellValue(row, 0) for row in xrange(self.grid.GetNumberRows())]
                for key, value in d.items():
                    if value:
                        if str(loc.er_data[key]) == str(value):
                            # no need to update
                            pass
                        else:
                            # update
                            loc.er_data[key] = value
                            col_ind = col_labels.index(key)
                            row_ind = row_labels.index(loc.name)
                            self.grid.SetCellValue(row_ind, col_ind, str(value))
                            if not self.grid.changes:
                                self.grid.changes = set([row_ind])
                            else:
                                self.grid.changes.add(row_ind)

        # a few special touches if it is an age grid
        if self.grid_type == 'age':
            self.remove_row_button.Disable()
            self.add_many_rows_button.Disable()
            self.grid.SetColLabelValue(0, 'er_site_name')
            toggle_box = wx.StaticBoxSizer(wx.StaticBox(self.panel, -1, label='Ages level'), wx.VERTICAL)

            levels = ['specimen', 'sample', 'site', 'location']
            age_level = pw.radio_buttons(self.panel, levels, 'Choose level to assign ages')
            level_ind = levels.index(self.er_magic.age_type)
            age_level.radio_buttons[level_ind].SetValue(True)
            
            toggle_box.Add(age_level)

            self.Bind(wx.EVT_RADIOBUTTON, self.toggle_ages)
            hbox.Add(toggle_box)

        # a few special touches if it is a result grid
        if self.grid_type == 'result':
            # populate specimen_names, sample_names, etc.
            self.drop_down_menu.choices[2] = [sorted([spec.name for spec in self.er_magic.specimens if spec]), False]
            self.drop_down_menu.choices[3] = [sorted([samp.name for samp in self.er_magic.samples if samp]), False]
            self.drop_down_menu.choices[4] = [sorted([site.name for site in self.er_magic.sites if site]), False]
            self.drop_down_menu.choices[5] = [sorted([loc.name for loc in self.er_magic.locations if loc]), False]
            for row in xrange(self.grid.GetNumberRows()):
                result_name = self.grid.GetCellValue(row, 0)
                result = self.er_magic.find_by_name(result_name, self.er_magic.results)
                if result:
                    if result.specimens:
                        self.grid.SetCellValue(row, 2, ' : '.join([pmag.get_attr(spec) for spec in result.specimens]))
                    if result.samples:
                        self.grid.SetCellValue(row, 3, ' : '.join([pmag.get_attr(samp) for samp in result.samples]))
                    if result.sites:
                        self.grid.SetCellValue(row, 4, ' : '.join([pmag.get_attr(site) for site in result.sites]))
                    if result.locations:
                        self.grid.SetCellValue(row, 5, ' : '.join([pmag.get_attr(loc) for loc in result.locations]))
                    self.drop_down_menu.choices[5] = [sorted([loc.name for loc in self.er_magic.locations if loc]), False]

        # final layout, set size
        self.main_sizer.Add(hbox, flag=wx.ALL, border=20)
        self.main_sizer.Add(self.toggle_help_btn, flag=wx.BOTTOM|wx.ALIGN_CENTRE, border=5)
        self.main_sizer.Add(self.msg_boxsizer, flag=wx.BOTTOM|wx.ALIGN_CENTRE, border=10)
        self.main_sizer.Add(self.grid_box, flag=wx.ALL, border=10)
        self.panel.SetSizer(self.main_sizer)
        self.main_sizer.Fit(self)
        ## this keeps sizing correct if the user resizes the window manually
        self.Bind(wx.EVT_SIZE, self.do_fit)
        self.Centre()
        self.Show()


    def on_key_down(self, event):
        """
        If user does command v, re-size window in case pasting has changed the content size.
        """
        keycode = event.GetKeyCode()
        meta_down = event.MetaDown() or event.GetCmdDown()
        if keycode == 86 and meta_down:
            # treat it as if it were a wx.EVT_TEXT_SIZE
            self.do_fit(event)

        
    def do_fit(self, event):
        """
        Re-fit the window to the size of the content.
        """
        #self.grid.ShowScrollbars(wx.SHOW_SB_NEVER, wx.SHOW_SB_NEVER)
        if event:
            event.Skip()
        self.main_sizer.Fit(self)
        self.Centre()

    def toggle_help(self, event):
        btn = event.GetEventObject()
        if btn.Label == 'Show help':
            self.msg_boxsizer.ShowItems(True)
            btn.SetLabel('Hide help')
        else:
            self.msg_boxsizer.ShowItems(False)
            btn.SetLabel('Show help')
        self.do_fit(None)
        
    def toggle_ages(self, event):
        """
        Switch the type of grid between site/sample
        (Users may add ages at either level)
        """
        if self.grid.changes:
            self.onSave(None)

        label = event.GetEventObject().Label

        self.er_magic.age_type = label
        self.grid.Destroy()

        # normally grid_frame is reset to None when grid is destroyed
        # in this case we are simply replacing the grid, so we need to
        # reset grid_frame
        self.parent.Parent.grid_frame = self
        self.parent.Parent.Hide()
        self.grid = self.grid_builder.make_grid()
        self.grid.InitUI()
        self.panel.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.onLeftClickLabel, self.grid)
        self.grid_builder.add_data_to_grid(self.grid, self.grid_type)
        self.grid_builder.add_age_data_to_grid()
        self.drop_down_menu = drop_down_menus.Menus(self.grid_type, self, self.grid, None)
        self.grid.SetColLabelValue(0, 'er_' + label + '_name')
        self.grid.size_grid()
        self.grid_box.Add(self.grid, flag=wx.ALL, border=5)
        self.main_sizer.Fit(self)
        if self.parent.Parent.validation_mode:
            if 'age' in self.parent.Parent.validation_mode:
                self.grid.paint_invalid_cells(self.parent.Parent.warn_dict['age'])
                self.grid.ForceRefresh()


    def init_grid_headers(self):
        self.grid_headers = self.er_magic.headers


    ##  Grid event methods

    def remove_col_label(self, event):#, include_pmag=True):
        """
        check to see if column is required
        if it is not, delete it from grid
        """
        #include_pmag = self.pmag_checkbox.cb.IsChecked()
        #include_pmag = True
        er_possible_headers = self.grid_headers[self.grid_type]['er'][2]
        pmag_possible_headers = self.grid_headers[self.grid_type]['pmag'][2]
        er_actual_headers = self.grid_headers[self.grid_type]['er'][0]
        pmag_actual_headers = self.grid_headers[self.grid_type]['pmag'][0]
        col = event.GetCol()
        label = self.grid.GetColLabelValue(col)
        if '**' in label:
            label = label.strip('**')
        if label in self.grid_headers[self.grid_type]['er'][1]:
            pw.simple_warning("That header is required, and cannot be removed")
            return False
        #elif include_pmag and label in self.grid_headers[self.grid_type]['pmag'][1]:
        #    pw.simple_warning("That header is required, and cannot be removed")
        #    return False
        else:
            print 'That header is not required:', label
            self.grid.remove_col(col)
            if label in er_possible_headers:
                try:
                    er_actual_headers.remove(label)
                except ValueError:
                    pass
            if label in pmag_possible_headers:
                try:
                    pmag_actual_headers.remove(label)
                except ValueError:
                    pass
        # causes resize on each column header delete
        # can leave this out if we want.....
        self.main_sizer.Fit(self)    

    def on_add_cols(self, event):
        """
        Show simple dialog that allows user to add a new column name
        """
        col_labels = self.grid.col_labels
        er_items = [head for head in self.grid_headers[self.grid_type]['er'][2] if head not in col_labels]
        er_items = builder.remove_list_headers(er_items)
        #include_pmag = self.pmag_checkbox.cb.IsChecked()
        include_pmag = True
        if include_pmag or self.grid_type == 'result':
            pmag_items = [head for head in self.grid_headers[self.grid_type]['pmag'][2] if head not in er_items and head not in col_labels]
            pmag_items = builder.remove_list_headers(pmag_items)
        else:
            pmag_items = []
        dia = pw.HeaderDialog(self, 'columns to add', er_items, pmag_items)
        result = dia.ShowModal()
        new_headers = []
        if result == 5100:
            new_headers = dia.text_list
        if not new_headers:
            return
        for name in new_headers:
            if name:
                if name not in self.grid.col_labels:
                    col_number = self.grid.add_col(name)
                    # add to appropriate headers list
                    if name in er_items:
                        self.grid_headers[self.grid_type]['er'][0].append(str(name))
                    if name in pmag_items:
                        self.grid_headers[self.grid_type]['pmag'][0].append(str(name))
                    import controlled_vocabularies as vocabulary
                    from controlled_vocabularies import vocabularies as vocab
                    if name in vocabulary.possible_vocabularies:
                        self.drop_down_menu.add_drop_down(col_number, name)
                else:
                    pw.simple_warning('You are already using column header: {}'.format(name))
        self.main_sizer.Fit(self)
        self.grid.changes = set(range(self.grid.GetNumberRows()))


    def on_remove_cols(self, event):
        """
        enter 'remove columns' mode
        """
        # first unselect any selected cols/cells
        self.remove_cols_mode = True
        self.grid.ClearSelection()
        self.remove_cols_button.SetLabel("end delete column mode")
        # change button to exit the delete columns mode
        self.Unbind(wx.EVT_BUTTON, self.remove_cols_button)
        self.Bind(wx.EVT_BUTTON, self.exit_col_remove_mode, self.remove_cols_button)
        # then disable all other buttons
        for btn in [self.add_cols_button, self.remove_row_button, self.add_many_rows_button]:
            btn.Disable()
        # then make some visual changes
        self.msg_text.SetLabel("Remove grid columns: click on a column header to delete it.  Required headers for {}s may not be deleted.".format(self.grid_type))
        self.msg_boxsizer.Fit(self.msg_boxsizer.GetStaticBox())
        self.main_sizer.Fit(self)
        self.grid.SetWindowStyle(wx.DOUBLE_BORDER)
        self.grid_box.GetStaticBox().SetWindowStyle(wx.DOUBLE_BORDER)
        self.grid.Refresh()
        self.main_sizer.Fit(self) # might not need this one
        self.grid.changes = set(range(self.grid.GetNumberRows()))


    def on_add_rows(self, event):
        """
        add rows to grid
        """
        num_rows = self.rows_spin_ctrl.GetValue()
        last_row = self.grid.GetNumberRows()
        for row in xrange(num_rows):
            self.grid.add_row()
            #if not self.grid.changes:
            #    self.grid.changes = set([])
            #self.grid.changes.add(last_row)
            #last_row += 1
        self.main_sizer.Fit(self)

    def on_remove_row(self, event, row_num=-1):
        """
        Remove specified grid row.
        If no row number is given, remove the last row.
        """
        #data_type = self.Name
        if row_num == -1:
            default = (255, 255, 255, 255)
            # unhighlight any selected rows:
            for row in self.selected_rows:
                attr = wx.grid.GridCellAttr()
                attr.SetBackgroundColour(default)
                self.grid.SetRowAttr(row, attr)
            row_num = self.grid.GetNumberRows() - 1
            self.deleteRowButton.Disable()
            self.selected_rows = {row_num}
            
        function_mapping = {'specimen': self.er_magic.delete_specimen,
                            'sample': self.er_magic.delete_sample,
                            'site': self.er_magic.delete_site,
                            'location': self.er_magic.delete_location,
                            'result': self.er_magic.delete_result}
        
        names = [self.grid.GetCellValue(row, 0) for row in self.selected_rows]
        orphans = []
        for name in names:
            if name:
                try:
                    row = self.grid.row_labels.index(name)
                    function_mapping[self.grid_type](name)
                    orphans.extend([name])
                # if user entered a name, then deletes the row before saving,
                # there will be a ValueError
                except ValueError:
                    pass
            self.grid.remove_row(row)
        self.selected_rows = set()

        self.deleteRowButton.Disable()
        self.grid.Refresh()

        self.main_sizer.Fit(self)

    def exit_col_remove_mode(self, event):
        """
        go back from 'remove cols' mode to normal
        """
        self.remove_cols_mode = False
        # re-enable all buttons
        for btn in [self.add_cols_button, self.remove_row_button, self.add_many_rows_button]:
            btn.Enable()

        # unbind grid click for deletion
        self.Unbind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK)
        # undo visual cues
        self.grid.SetWindowStyle(wx.DEFAULT)
        self.grid_box.GetStaticBox().SetWindowStyle(wx.DEFAULT)
        self.msg_text.SetLabel(self.default_msg_text)
        self.msg_boxsizer.Fit(self.msg_boxsizer.GetStaticBox())
        self.main_sizer.Fit(self)
        # re-bind self.remove_cols_button
        self.Bind(wx.EVT_BUTTON, self.on_remove_cols, self.remove_cols_button)
        self.remove_cols_button.SetLabel("Remove columns")


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

    def onLeftClickLabel(self, event):
        """
        When user clicks on a grid label, determine if it is a row label or a col label.
        Pass along the event to the appropriate function.
        (It will either highlight a column for editing all values, or highlight a row for deletion).
        """
        if event.Col == -1 and event.Row == -1:
            pass
        if event.Row < 0:
            if self.remove_cols_mode:
                self.remove_col_label(event)
            else:
                self.drop_down_menu.on_label_click(event)
        else:
            if event.Col < 0  and self.grid_type != 'age':
                self.onSelectRow(event)


    ## Meta buttons -- cancel & save functions

    def onImport(self, event):
        openFileDialog = wx.FileDialog(self, "Open MagIC-format file", self.WD, "",
                                       "MagIC file|*.*", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        result = openFileDialog.ShowModal()

        if result == wx.ID_OK:
            if self.grid_type == 'age':
                import_type = 'age'
                parent_type = None
                filename = openFileDialog.GetPath()
                file_type = self.er_magic.get_age_info(filename)
                import_type = file_type.split('_')[1][:-1]
            elif self.grid_type == 'result':
                import_type = 'result'
                parent_type = None
                try:
                    filename = openFileDialog.GetPath()
                    self.er_magic.get_results_info(filename)
                except Exception as ex:
                    print '-W- ', ex
                    print '-W- Could not read file:\n{}\nFile may be corrupted, or may not be a results format file.'.format(filename)
                    pw.simple_warning('Could not read file:\n{}\nFile may be corrupted, or may not be a results format file.'.format(filename))
                    return
            else:
                parent_ind = self.er_magic.ancestry.index(self.grid_type)
                parent_type = self.er_magic.ancestry[parent_ind+1]

                # get filename and file data
                filename = openFileDialog.GetPath()
                import_type = self.er_magic.get_magic_info(self.grid_type, parent_type,
                                                           filename=filename, sort_by_file_type=True)
            # add any additional headers to the grid, while preserving all old headers
            current_headers = self.grid_headers[self.grid_type]['er'][0]
            self.er_magic.init_actual_headers()
            er_headers = list(set(self.er_magic.headers[self.grid_type]['er'][0]).union(current_headers))
            self.er_magic.headers[self.grid_type]['er'][0] = er_headers

            #include_pmag = self.pmag_checkbox.cb.IsChecked()
            include_pmag = True
            if include_pmag:
                pmag_headers = self.er_magic.headers[self.grid_type]['pmag'][0]
                headers = set(er_headers).union(pmag_headers)
            else:
                headers = er_headers
            for head in sorted(list(headers)):
                if head not in self.grid.col_labels:
                    self.grid.add_col(head)
            # add age data
            if import_type == 'age' and self.grid_type == 'age':
                self.grid_builder.add_age_data_to_grid()
                self.grid.size_grid()
                self.main_sizer.Fit(self)
            # if imported data will not show up in current grid,
            # warn user
            elif import_type == self.grid_type:
                self.grid_builder.add_data_to_grid(self.grid, import_type)
                self.grid.size_grid()
                self.main_sizer.Fit(self)
            else:
                pw.simple_warning('You have imported a {} type file.\nYou\'ll need to open up your {} grid to see this data'.format(import_type, import_type))

    """
    def on_pmag_checkbox(self, event):

        Called when user changes status of pmag_checkbox.
        Removes pmag-specific columns if box is unchecked.
        Adds in pmag-specific columns if box is checked.

        num_cols = self.grid.GetNumberCols()
        current_grid_col_labels = [self.grid.GetColLabelValue(num) for num in xrange(num_cols)]
        do_pmag = self.pmag_checkbox.cb.IsChecked()
        # add in pmag-specific headers
        if do_pmag:
            if self.grid_type in self.er_magic.no_pmag_data:
                self.er_magic.no_pmag_data.remove(self.grid_type)
            for col_label in self.er_magic.headers[self.grid_type]['pmag'][0]:
                if col_label not in current_grid_col_labels:
                    self.grid.add_col(col_label)
        # remove pmag-specific headers
        if not do_pmag:
            self.er_magic.no_pmag_data.add(self.grid_type)
            for col_label in self.er_magic.headers[self.grid_type]['pmag'][0]:
                if col_label not in self.er_magic.headers[self.grid_type]['er'][0]:
                    num_cols = self.grid.GetNumberCols()
                    current_grid_col_labels = [self.grid.GetColLabelValue(num) for num in xrange(num_cols)]
                    ind = current_grid_col_labels.index(col_label)
                    self.grid.remove_col(ind)
        self.main_sizer.Fit(self)
        """
    
    def onCancelButton(self, event):
        if self.grid.changes:
            dlg1 = wx.MessageDialog(self,caption="Message:", message="Are you sure you want to exit this grid?\nYour changes will not be saved.\n ", style=wx.OK|wx.CANCEL)
            result = dlg1.ShowModal()
            if result == wx.ID_OK:
                dlg1.Destroy()    
                self.Destroy()
        else:
            self.Destroy()

    def onSave(self, event):#, age_data_type='site'):
        # first, see if there's any pmag_* data
        # set er_magic.incl_pmag_data accordingly
        pmag_header_found = False
        actual_er_headers = self.er_magic.headers[self.grid_type]['er'][0]
        actual_pmag_headers = self.er_magic.headers[self.grid_type]['pmag'][0]
        for col in self.grid.col_labels:
            if col not in actual_er_headers:
                if col in actual_pmag_headers:
                    pmag_header_found = True
                    break
        if pmag_header_found:
            self.er_magic.incl_pmag_data.add(self.grid_type)
        else:
            try:
                self.er_magic.incl_pmag_data.remove(self.grid_type)
            except KeyError:
                pass
        # then, tidy up drop_down menu
        if self.drop_down_menu:
            self.drop_down_menu.clean_up()
        # then save actual data
        self.grid_builder.save_grid_data()
        if not event:
            return
        # then alert user
        wx.MessageBox('Saved!', 'Info',
                      style=wx.OK | wx.ICON_INFORMATION)
        self.Destroy()


class GridBuilder(object):
    
    def __init__(self, er_magic, grid_type, grid_headers, panel, parent_type=None):
        self.er_magic = er_magic
        self.grid_type = grid_type
        self.grid_headers = grid_headers
        self.panel = panel
        self.parent_type = parent_type
        self.grid = None
    
    def make_grid(self):
        """
        return grid
        """
        er_header = self.grid_headers[self.grid_type]['er'][0]
        if self.grid_type in self.er_magic.incl_pmag_data:
            pmag_header = self.grid_headers[self.grid_type]['pmag'][0]
        else:
            pmag_header = []
        header = sorted(list(set(er_header).union(pmag_header)))
        first_headers = []
        for string in ['citation', '{}_class'.format(self.grid_type),
                       '{}_lithology'.format(self.grid_type), '{}_type'.format(self.grid_type),
                      'site_definition']:
            for head in header[:]:
                if string in head:
                    header.remove(head)
                    first_headers.append(head)

        # the way we work it, each specimen is assigned to a sample
        # each sample is assigned to a site
        # specimens can not be added en masse to a site object, for example
        # this data will be written in
        for string in ['er_specimen_names', 'er_sample_names', 'er_site_names']:
            for head in header[:]:
                if string in head:
                    header.remove(head)
            
        # do headers for results type grid
        if self.grid_type == 'result':
            #header.remove('pmag_result_name')
            header[:0] = ['pmag_result_name', 'er_citation_names', 'er_specimen_names',
                          'er_sample_names', 'er_site_names', 'er_location_names']

        elif self.grid_type == 'age':
            for header_type in self.er_magic.first_age_headers:
                if header_type in header:
                    header.remove(header_type)
            lst = ['er_' + self.grid_type + '_name']
            lst.extend(self.er_magic.first_age_headers)
            header[:0] = lst

        # do headers for all other data types without parents
        elif not self.parent_type:
            lst = ['er_' + self.grid_type + '_name']
            lst.extend(first_headers)
            header[:0] = lst
        # do headers for all data types with parents
        else:
            lst = ['er_' + self.grid_type + '_name', 'er_' + self.parent_type + '_name']
            lst.extend(first_headers)
            header[:0] = lst
        
        grid = magic_grid.MagicGrid(parent=self.panel, name=self.grid_type,
                                    row_labels=[], col_labels=header)
        grid.do_event_bindings()

        self.grid = grid
        return grid

    def add_data_to_grid(self, grid, grid_type=None, incl_pmag=True):
        incl_parents = True
        if not grid_type:
            grid_type = self.grid_type
        if grid_type == 'age':
            grid_type = self.er_magic.age_type
            incl_parents = False
            incl_pmag = False
        # the two loops below may be overly expensive operations
        # consider doing this another way
        if grid_type == 'sample':
            for sample in self.er_magic.samples:
                sample.propagate_data()
        if grid_type == 'specimen':
            for specimen in self.er_magic.specimens:
                specimen.propagate_data()
        rows = self.er_magic.data_lists[grid_type][0]
        grid.add_items(rows, incl_pmag=incl_pmag, incl_parents=incl_parents)
        grid.size_grid()

        # always start with at least one row:
        if not grid.row_labels:
            grid.add_row()

    def add_age_data_to_grid(self):
        dtype = self.er_magic.age_type
        row_labels = [self.grid.GetCellValue(row, 0) for row in xrange(self.grid.GetNumberRows())]
        items_list = self.er_magic.data_lists[dtype][0]
        items = [self.er_magic.find_by_name(label, items_list) for label in row_labels if label]

        col_labels = self.grid.col_labels[1:]
        if not any(items):
            return
        for row_num, item in enumerate(items):
            for col_num, label in enumerate(col_labels):
                col_num += 1
                if item:
                    if not label in item.age_data.keys():
                        item.age_data[label] = ''
                    cell_value = item.age_data[label]
                    if cell_value:
                        self.grid.SetCellValue(row_num, col_num, cell_value)


    def save_grid_data(self):
        """
        Save grid data in the data object
        """
        if not self.grid.changes:
            print '-I- No changes to save'
            return

        if self.grid_type == 'age':
            age_data_type = self.er_magic.age_type
            self.er_magic.write_ages = True

        starred_cols = self.grid.remove_starred_labels()

        self.grid.SaveEditControlValue() # locks in value in cell currently edited
        
        if self.grid.changes:
            num_cols = self.grid.GetNumberCols()

            for change in self.grid.changes:
                if change == -1:
                    continue
                else:
                    old_item = self.grid.row_items[change]
                    new_item_name = self.grid.GetCellValue(change, 0)
                    new_er_data = {}
                    new_pmag_data = {}
                    er_header = self.grid_headers[self.grid_type]['er'][0]
                    pmag_header = self.grid_headers[self.grid_type]['pmag'][0]
                    start_num = 2 if self.parent_type else 1
                    result_data = {}

                    for col in xrange(start_num, num_cols):
                        col_label = str(self.grid.GetColLabelValue(col))
                        value = str(self.grid.GetCellValue(change, col))
                        #new_data[col_label] = value
                        if value == '\t':
                            value = ''
                        if er_header and col_label in er_header:
                            new_er_data[col_label] = value

                        if pmag_header and col_label in pmag_header:
                            new_pmag_data[col_label] = value

                        if col_label in ['er_specimen_names', 'er_sample_names',
                                         'er_site_names', 'er_location_names']:
                            result_data[col_label] = value

                    # if there is an item
                    if isinstance(old_item, str):
                        old_item_name = None
                    else:
                        old_item_name = self.grid.row_items[change].name

                    if self.parent_type:
                        new_parent_name = self.grid.GetCellValue(change, 1)
                    else:
                        new_parent_name = ''

                    # create a new item
                    if new_item_name and not old_item_name:
                        print '-I- make new item named', new_item_name
                        if self.grid_type == 'result':
                            specs, samps, sites, locs = self.get_result_children(result_data)
                            item = self.er_magic.add_result(new_item_name, specs, samps, sites,
                                                            locs, new_pmag_data)
                        else:
                            item = self.er_magic.add_methods[self.grid_type](new_item_name, new_parent_name,
                                                                             new_er_data, new_pmag_data)

                    # update an existing item
                    elif new_item_name and old_item_name:
                        print '-I- update existing {} formerly named {} to {}'.format(self.grid_type,
                                                                                  old_item_name,
                                                                                  new_item_name)
                        if self.grid_type == 'result':
                            specs, samps, sites, locs = self.get_result_children(result_data)
                            item = self.er_magic.update_methods['result'](old_item_name, new_item_name,
                                                                          new_er_data=None,
                                                                          new_pmag_data=new_pmag_data,
                                                                          spec_names=specs,
                                                                          samp_names=samps,
                                                                          site_names=sites,
                                                                          loc_names=locs,
                                                                          replace_data=True)
                        elif self.grid_type == 'age':
                            item_type = age_data_type
                            item = self.er_magic.update_methods['age'](old_item_name, new_er_data,
                                                                       item_type, replace_data=True)
                            
                        else:
                            item = self.er_magic.update_methods[self.grid_type](old_item_name, new_item_name,
                                                                                new_parent_name, new_er_data,
                                                                                new_pmag_data, replace_data=True)

    def get_result_children(self, result_data):
        """
        takes in dict in form of {'er_specimen_names': 'name1:name2:name3'}
        and so forth.
        returns lists of specimens, samples, sites, and locations
        """
        if result_data['er_specimen_names']:
            specimens = result_data['er_specimen_names'].split(":")
        else:
            specimens = ''
        if result_data['er_sample_names']:
            samples = result_data['er_sample_names'].split(":")
        else:
            samples = ''
        if result_data['er_site_names']:
            sites = result_data['er_site_names'].split(":")
        else:
            sites = ''
        if result_data['er_location_names']:
            locations = result_data['er_location_names'].split(":")
        else:
            locations = ''
        return specimens, samples, sites, locations

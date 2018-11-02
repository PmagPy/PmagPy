"""
GridFrame -- subclass of wx.Frame.  Contains grid and buttons to manipulate it.
GridBuilder -- data methods for GridFrame (add data to frame, save it, etc.)
"""
import wx
import pandas as pd
import numpy as np
from dialogs import drop_down_menus3 as drop_down_menus
from dialogs import pmag_widgets as pw
from dialogs import magic_grid3 as magic_grid
#from pmagpy.controlled_vocabularies3 import vocab
import pmagpy.contribution_builder as cb


class GridFrame(wx.Frame):  # class GridFrame(wx.ScrolledWindow):
    """
    make_magic
    """
    def __init__(self, contribution, WD=None, frame_name="grid frame",
                 panel_name="grid panel", parent=None, exclude_cols=(),
                 huge=False, main_frame=None):
        self.parent = parent
        self.main_frame = main_frame
        wx.GetDisplaySize()
        title = 'Edit {} data'.format(panel_name)
        super(GridFrame, self).__init__(parent=parent, id=wx.ID_ANY,
                                        name=frame_name, title=title)
        wait = wx.BusyInfo("Please wait, working...")
        wx.SafeYield()
        self.remove_cols_mode = False
        self.deleteRowButton = None
        self.selected_rows = set()

        self.contribution = contribution
        self.huge = huge
        self.df_slice = None
        self.exclude_cols = exclude_cols
        self.error_frame = None

        self.panel = wx.Panel(self, name=panel_name, size=wx.GetDisplaySize())
        self.grid_type = str(panel_name)
        dm = self.contribution.data_model.dm[self.grid_type]
        dm['str_validations'] = dm['validations'].str.join(", ")
        # these are the headers that are required no matter what for this datatype
        self.reqd_headers = dm[dm['str_validations'].str.contains("required\(\)").fillna(False)].index
        self.dm = dm

        if self.parent:
            self.Bind(wx.EVT_WINDOW_DESTROY, self.parent.Parent.on_close_grid_frame)

        if self.grid_type == 'ages':
            self.child_type = None
            self.parent_type = None
        else:
            try:
                child_ind = self.contribution.ancestry.index(self.grid_type) - 1
                if child_ind < 0:
                    self.child_type = None
                self.child_type = self.contribution.ancestry[child_ind]
                parent_ind = self.contribution.ancestry.index(self.grid_type) + 1
                if parent_ind >= len(self.contribution.ancestry):
                    self.parent_type = None
                else:
                    self.parent_type = self.contribution.ancestry[parent_ind]
            except ValueError:
                self.child_type = None
                self.parent_type = None


        self.WD = WD
        self.InitUI()

        # remove 'level' column from age grid if present
        if self.grid_type == 'ages':
            try:
                ind = self.grid.col_labels.index('level')
                self.remove_col_label(col=ind)
            except ValueError:
                pass

        # if grid is empty except for defaults, reset grid.changes
        if self.grid_builder.current_grid_empty():
            self.grid.changes = set()

        del wait


    ## Initialization functions
    def InitUI(self):
        """
        initialize window
        """
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        if self.grid_type in self.contribution.tables:
            dataframe = self.contribution.tables[self.grid_type]
        else:
            dataframe = None
        self.grid_builder = GridBuilder(self.contribution, self.grid_type,
                                        self.panel, parent_type=self.parent_type,
                                        reqd_headers=self.reqd_headers,
                                        exclude_cols=self.exclude_cols,
                                        huge=self.huge)

        self.grid = self.grid_builder.make_grid()
        self.grid.InitUI()


        ## Column management buttons
        self.add_cols_button = wx.Button(self.panel, label="Add additional columns",
                                         name='add_cols_btn',
                                         size=(170, 20))
        self.Bind(wx.EVT_BUTTON, self.on_add_cols, self.add_cols_button)
        self.remove_cols_button = wx.Button(self.panel, label="Remove columns",
                                            name='remove_cols_btn',
                                            size=(170, 20))

        self.Bind(wx.EVT_BUTTON, self.on_remove_cols, self.remove_cols_button)

        ## Row management buttons
        self.remove_row_button = wx.Button(self.panel, label="Remove last row",
                                           name='remove_last_row_btn')
        self.Bind(wx.EVT_BUTTON, self.on_remove_row, self.remove_row_button)
        many_rows_box = wx.BoxSizer(wx.HORIZONTAL)
        self.add_many_rows_button = wx.Button(self.panel, label="Add row(s)",
                                              name='add_many_rows_btn')
        self.rows_spin_ctrl = wx.SpinCtrl(self.panel, value='1', initial=1,
                                          name='rows_spin_ctrl')
        many_rows_box.Add(self.add_many_rows_button, flag=wx.ALIGN_CENTRE)
        many_rows_box.Add(self.rows_spin_ctrl)
        self.Bind(wx.EVT_BUTTON, self.on_add_rows, self.add_many_rows_button)

        self.deleteRowButton = wx.Button(self.panel, id=-1,
                                         label='Delete selected row(s)',
                                         name='delete_row_btn')
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_remove_row(event, False), self.deleteRowButton)
        self.deleteRowButton.Disable()

        # measurements table should not be able to add new rows
        # that should be done elsewhere
        if self.huge:
            self.add_many_rows_button.Disable()
            self.rows_spin_ctrl.Disable()
            self.remove_row_button.Disable()
            # can't remove cols (seg fault), but can add them
            #self.add_cols_button.Disable()
            self.remove_cols_button.Disable()


        ## Data management buttons
        self.importButton = wx.Button(self.panel, id=-1,
                                      label='Import MagIC-format file',
                                      name='import_btn')
        self.Bind(wx.EVT_BUTTON, self.onImport, self.importButton)
        self.exitButton = wx.Button(self.panel, id=-1,
                                    label='Save and close grid',
                                    name='save_and_quit_btn')
        self.Bind(wx.EVT_BUTTON, self.onSave, self.exitButton)
        self.cancelButton = wx.Button(self.panel, id=-1, label='Cancel',
                                      name='cancel_btn')
        self.Bind(wx.EVT_BUTTON, self.onCancelButton, self.cancelButton)
        self.Bind(wx.EVT_CLOSE, self.onCancelButton)

        ## Input/output buttons
        self.copyButton = wx.Button(self.panel, id=-1,
                                     label="Start copy mode",
                                     name="copy_mode_btn")
        self.Bind(wx.EVT_BUTTON, self.onCopyMode, self.copyButton)
        self.selectAllButton = wx.Button(self.panel, id=-1,
                                         label="Copy all cells",
                                         name="select_all_btn")
        self.Bind(wx.EVT_BUTTON, self.onSelectAll, self.selectAllButton)
        self.copySelectionButton = wx.Button(self.panel, id=-1,
                                         label="Copy selected cells",
                                         name="copy_selection_btn")
        self.Bind(wx.EVT_BUTTON, self.onCopySelection, self.copySelectionButton)
        self.copySelectionButton.Disable()

        ## Help message and button
        # button
        self.toggle_help_btn = wx.Button(self.panel, id=-1, label="Show help",
                                         name='toggle_help_btn')
        self.Bind(wx.EVT_BUTTON, self.toggle_help, self.toggle_help_btn)
        # message
        self.help_msg_boxsizer = wx.StaticBoxSizer(wx.StaticBox(self.panel, -1, name='help_msg_boxsizer'), wx.VERTICAL)

        if self.grid_type == 'measurements':
            self.default_msg_text = "Edit measurements here.\nIn general, measurements should be imported directly into Pmag GUI,\nwhich has protocols for converting many lab formats into the MagIC format.\nIf we are missing your particular lab format, please let us know: https://github.com/PmagPy/PmagPy/issues.\nThis grid is just meant for looking at your measurements and doing small edits.\nCurrently, you can't add/remove rows here.  You can add columns and edit cell values."
        else:
            self.default_msg_text = 'Edit {} here.\nYou can add or remove both rows and columns, however required columns may not be deleted.\nControlled vocabularies are indicated by **, and will have drop-down-menus.\nSuggested vocabularies are indicated by ^^, and also have drop-down-menus.\nTo edit all values in a column, click the column header.\nYou can cut and paste a block of cells from an Excel-like file.\nJust click the top left cell and use command "v".'.format(self.grid_type)
        txt = ''
        if self.grid_type == 'locations':
            txt = '\n\nNote: you can fill in location start/end latitude/longitude here.\nHowever, if you add sites in step 2, the program will calculate those values automatically,\nbased on site latitudes/logitudes.\nThese values will be written to your upload file.'
        if self.grid_type == 'samples':
            txt = "\n\nNote: you can fill in lithology, class, and type for each sample here.\nHowever, if the sample's class, lithology, and type are the same as its parent site,\nthose values will propagate down, and will be written to your sample file automatically."
        if self.grid_type == 'specimens':
            txt = "\n\nNote: you can fill in lithology, class, and type for each specimen here.\nHowever, if the specimen's class, lithology, and type are the same as its parent sample,\nthose values will propagate down, and will be written to your specimen file automatically."
        if self.grid_type == 'ages':
            txt = "\n\nNote: only ages for which you provide data will be written to your upload file."
        self.default_msg_text += txt
        self.msg_text = wx.StaticText(self.panel, label=self.default_msg_text,
                                      style=wx.TE_CENTER, name='msg text')
        self.help_msg_boxsizer.Add(self.msg_text)
        self.help_msg_boxsizer.ShowItems(False)

        ## Code message and button
        # button
        self.toggle_codes_btn = wx.Button(self.panel, id=-1,
                                          label="Show method codes",
                                          name='toggle_codes_btn')
        self.Bind(wx.EVT_BUTTON, self.toggle_codes, self.toggle_codes_btn)
        # message
        self.code_msg_boxsizer = pw.MethodCodeDemystifier(self.panel, self.contribution.vocab)
        self.code_msg_boxsizer.ShowItems(False)

        ## Add content to sizers
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        col_btn_vbox = wx.StaticBoxSizer(wx.StaticBox(self.panel, -1, label='Columns',
                                                      name='manage columns'), wx.VERTICAL)
        row_btn_vbox = wx.StaticBoxSizer(wx.StaticBox(self.panel, -1, label='Rows',
                                                      name='manage rows'), wx.VERTICAL)
        self.main_btn_vbox = wx.StaticBoxSizer(wx.StaticBox(self.panel, -1, label='Manage data',
                                                            name='manage data'), wx.VERTICAL)
        input_output_vbox = wx.StaticBoxSizer(wx.StaticBox(self.panel, -1, label='In/Out',
                                                           name='manage in out'), wx.VERTICAL)
        col_btn_vbox.Add(self.add_cols_button, flag=wx.ALL, border=5)
        col_btn_vbox.Add(self.remove_cols_button, flag=wx.ALL, border=5)
        row_btn_vbox.Add(many_rows_box, flag=wx.ALL, border=5)
        row_btn_vbox.Add(self.remove_row_button, flag=wx.ALL, border=5)
        row_btn_vbox.Add(self.deleteRowButton, flag=wx.ALL, border=5)
        self.main_btn_vbox.Add(self.importButton, flag=wx.ALL, border=5)
        self.main_btn_vbox.Add(self.exitButton, flag=wx.ALL, border=5)
        self.main_btn_vbox.Add(self.cancelButton, flag=wx.ALL, border=5)
        input_output_vbox.Add(self.copyButton, flag=wx.ALL, border=5)
        input_output_vbox.Add(self.selectAllButton, flag=wx.ALL, border=5)
        input_output_vbox.Add(self.copySelectionButton, flag=wx.ALL, border=5)
        self.hbox.Add(col_btn_vbox)
        self.hbox.Add(row_btn_vbox)
        self.hbox.Add(self.main_btn_vbox)
        self.hbox.Add(input_output_vbox)

        #self.panel.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.onLeftClickLabel, self.grid)
        self.grid.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.onLeftClickLabel, self.grid)
        #
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.panel.Bind(wx.EVT_TEXT_PASTE, self.do_fit)
        # add actual data!
        self.grid_builder.add_data_to_grid(self.grid, self.grid_type)
        # fill in some default values
        self.grid_builder.fill_defaults()
        # set scrollbars
        self.grid.set_scrollbars()

        ## this would be a way to prevent editing
        ## some cells in age grid.
        ## with multiple types of ages, though,
        ## this doesn't make much sense
        #if self.grid_type == 'ages':
        #    attr = wx.grid.GridCellAttr()
        #    attr.SetReadOnly(True)
        #    self.grid.SetColAttr(1, attr)

        self.drop_down_menu = drop_down_menus.Menus(self.grid_type, self.contribution, self.grid)
        self.grid_box = wx.StaticBoxSizer(wx.StaticBox(self.panel, -1, name='grid container'), wx.VERTICAL)
        self.grid_box.Add(self.grid, 1, flag=wx.ALL|wx.EXPAND, border=5)

        # final layout, set size
        self.main_sizer.Add(self.hbox, flag=wx.ALL|wx.ALIGN_CENTER,#|wx.SHAPED,
                            border=20)
        self.main_sizer.Add(self.toggle_help_btn, 0,
                            flag=wx.BOTTOM|wx.ALIGN_CENTRE,#|wx.SHAPED,
                            border=5)
        self.main_sizer.Add(self.help_msg_boxsizer, 0,
                            flag=wx.BOTTOM|wx.ALIGN_CENTRE,
                            border=10)
        self.main_sizer.Add(self.toggle_codes_btn, 0,
                            flag=wx.BOTTOM|wx.ALIGN_CENTRE,#|wx.SHAPED,
                            border=5)
        self.main_sizer.Add(self.code_msg_boxsizer, 0,
                            flag=wx.BOTTOM|wx.ALIGN_CENTRE,#|wx.SHAPED,
                            border=5)
        self.main_sizer.Add(self.grid_box, 2, flag=wx.ALL|wx.ALIGN_CENTER|wx.EXPAND, border=10)
        self.panel.SetSizer(self.main_sizer)
        panel_sizer = wx.BoxSizer(wx.VERTICAL)
        panel_sizer.Add(self.panel, 1, wx.EXPAND)
        self.SetSizer(panel_sizer)
        panel_sizer.Fit(self)
        ## this keeps sizing correct if the user resizes the window manually
        #self.Bind(wx.EVT_SIZE, self.do_fit)
#        self.Centre()
        self.Show()

    def on_key_down(self, event):
        """
        If user does command v,
        re-size window in case pasting has changed the content size.
        """
        keycode = event.GetKeyCode()
        meta_down = event.MetaDown() or event.GetCmdDown()
        if keycode == 86 and meta_down:
            # treat it as if it were a wx.EVT_TEXT_SIZE
            self.do_fit(event)

    def do_fit(self, event, min_size=None):
        """
        Re-fit the window to the size of the content.
        """
        #self.grid.ShowScrollbars(wx.SHOW_SB_NEVER, wx.SHOW_SB_NEVER)
        if event:
            event.Skip()
        self.main_sizer.Fit(self)
        disp_size = wx.GetDisplaySize()
        actual_size = self.GetSize()
        # if there isn't enough room to display new content
        # resize the frame
        if disp_size[1] - 75 < actual_size[1]:
            self.SetSize((actual_size[0], disp_size[1] * .95))
        # make sure you adhere to a minimum size
        if min_size:
            actual_size = self.GetSize()
            larger_width = max([actual_size[0], min_size[0]])
            larger_height = max([actual_size[1], min_size[1]])
            if larger_width > actual_size[0] or larger_height > actual_size[1]:
                self.SetSize((larger_width, larger_height))
        self.Centre()

    def toggle_help(self, event, mode=None):
        """
        Show/hide help message on help button click.
        """
        # if mode == 'open', show no matter what.
        # if mode == 'close', close.  otherwise, change state
        btn = self.toggle_help_btn
        shown = self.help_msg_boxsizer.GetStaticBox().IsShown()
        # if mode is specified, do that mode
        if mode == 'open':
            self.help_msg_boxsizer.ShowItems(True)
            btn.SetLabel('Hide help')
        elif mode == 'close':
            self.help_msg_boxsizer.ShowItems(False)
            btn.SetLabel('Show help')
        # otherwise, simply toggle states
        else:
            if shown:
                self.help_msg_boxsizer.ShowItems(False)
                btn.SetLabel('Show help')
            else:
                self.help_msg_boxsizer.ShowItems(True)
                btn.SetLabel('Hide help')
        self.do_fit(None)


    def toggle_codes(self, event):
        """
        Show/hide method code explanation widget on button click
        """
        btn = event.GetEventObject()
        if btn.Label == 'Show method codes':
            self.code_msg_boxsizer.ShowItems(True)
            btn.SetLabel('Hide method codes')
        else:
            self.code_msg_boxsizer.ShowItems(False)
            btn.SetLabel('Show method codes')
        self.do_fit(None)

    def show_errors(self, event):
        from dialogs import thellier_gui_dialogs
        import os
        error_file = os.path.join(self.WD, self.grid_type + "_errors.txt")
        if not os.path.exists(error_file):
            pw.simple_warning("No error file for this grid")
            return
        frame = thellier_gui_dialogs.MyForm(0, error_file)
        frame.Show()
        self.error_frame = frame
        # frame should be destroyed when grid frame is


    ##  Grid event methods

    def remove_col_label(self, event=None, col=None):
        """
        check to see if column is required
        if it is not, delete it from grid
        """
        if event:
            col = event.GetCol()
        if not col:
            return
        label = self.grid.GetColLabelValue(col)
        if '**' in label:
            label = label.strip('**')
        elif '^^' in label:
            label = label.strip('^^')
        if label in self.reqd_headers:
            pw.simple_warning("That header is required, and cannot be removed")
            return False
        else:
            print('That header is not required:', label)
            # remove column from wxPython grid
            self.grid.remove_col(col)
            # remove column from DataFrame if present
            if self.grid_type in self.contribution.tables:
                if label in self.contribution.tables[self.grid_type].df.columns:
                    del self.contribution.tables[self.grid_type].df[label]
        # causes resize on each column header delete
        # can leave this out if we want.....
        self.main_sizer.Fit(self)

    def on_add_cols(self, event):
        """
        Show simple dialog that allows user to add a new column name
        """
        col_labels = self.grid.col_labels
        dia = pw.ChooseOne(self, yes="Add single columns", no="Add groups")
        result1 = dia.ShowModal()
        if result1 == wx.ID_CANCEL:
            return
        elif result1 == wx.ID_YES:
            items = sorted([col_name for col_name in self.dm.index if col_name not in col_labels])
            dia = pw.HeaderDialog(self, 'columns to add',
                                  items1=list(items), groups=[])
            dia.Centre()
            result2 = dia.ShowModal()
        else:
            groups = self.dm['group'].unique()
            dia = pw.HeaderDialog(self, 'groups to add',
                                  items1=list(groups), groups=True)
            dia.Centre()
            result2 = dia.ShowModal()
        new_headers = []
        if result2 == 5100:
            new_headers = dia.text_list
        # if there is nothing to add, quit
        if not new_headers:
            return
        if result1 == wx.ID_YES:
            # add individual headers
            errors = self.add_new_grid_headers(new_headers)
        else:
            # add header groups
            errors = self.add_new_header_groups(new_headers)
        if errors:
            errors_str = ', '.join(errors)
            pw.simple_warning('You are already using the following headers: {}\nSo they will not be added'.format(errors_str))

        # problem: if widgets above the grid are too wide,
        # the grid does not re-size when adding columns
        # awkward solution (causes flashing):
        if self.grid.GetWindowStyle() != wx.DOUBLE_BORDER:
            self.grid.SetWindowStyle(wx.DOUBLE_BORDER)
        self.main_sizer.Fit(self)
        self.grid.SetWindowStyle(wx.NO_BORDER)
        self.Centre()
        self.main_sizer.Fit(self)
        #
        self.grid.changes = set(range(self.grid.GetNumberRows()))
        dia.Destroy()

    def add_new_header_groups(self, groups):
        """
        compile list of all headers belonging to all specified groups
        eliminate all headers that are already included
        add any req'd drop-down menus
        return errors
        """
        already_present = []
        for group in groups:
            col_names = self.dm[self.dm['group'] == group].index
            for col in col_names:
                if col not in self.grid.col_labels:
                    col_number = self.grid.add_col(col)
                    # add to appropriate headers list
                    # add drop down menus for user-added column
                    if col in self.contribution.vocab.vocabularies:
                        self.drop_down_menu.add_drop_down(col_number, col)
                    elif col in self.contribution.vocab.suggested:
                        self.drop_down_menu.add_drop_down(col_number, col)
                    elif col in ['specimen', 'sample', 'site', 'location',
                                 'specimens', 'samples', 'sites']:
                        self.drop_down_menu.add_drop_down(col_number, col)
                    elif col == 'experiments':
                        self.drop_down_menu.add_drop_down(col_number, col)
                    if col == "method_codes":
                        self.drop_down_menu.add_method_drop_down(col_number, col)
                else:
                    already_present.append(col)
        return already_present

    def add_new_grid_headers(self, new_headers):
        """
        Add in all user-added headers.
        If those new headers depend on other headers,
        add the other headers too.
        """
        already_present = []
        for name in new_headers:
            if name:
                if name not in self.grid.col_labels:
                    col_number = self.grid.add_col(name)
                    # add to appropriate headers list
                    # add drop down menus for user-added column
                    if name in self.contribution.vocab.vocabularies:
                        self.drop_down_menu.add_drop_down(col_number, name)
                    elif name in self.contribution.vocab.suggested:
                        self.drop_down_menu.add_drop_down(col_number, name)
                    elif name in ['specimen', 'sample', 'site',
                                  'specimens', 'samples', 'sites']:
                        self.drop_down_menu.add_drop_down(col_number, name)
                    elif name == 'experiments':
                        self.drop_down_menu.add_drop_down(col_number, name)
                    if name == "method_codes":
                        self.drop_down_menu.add_method_drop_down(col_number, name)
                else:
                    already_present.append(name)
                    #pw.simple_warning('You are already using column header: {}'.format(name))
        return already_present

    def on_remove_cols(self, event):
        """
        enter 'remove columns' mode
        """
        # open the help message
        self.toggle_help(event=None, mode='open')
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
        self.msg_text.SetLabel("Remove grid columns: click on a column header to delete it.\nRequired headers for {} may not be deleted.".format(self.grid_type))
        self.help_msg_boxsizer.Fit(self.help_msg_boxsizer.GetStaticBox())
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
        #last_row = self.grid.GetNumberRows()
        for row in range(num_rows):
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
        text = "Are you sure?  If you select delete you won't be able to retrieve these rows..."
        dia = pw.ChooseOne(self, "Yes, delete rows", "Leave rows for now", text)
        dia.Centre()
        result = dia.ShowModal()
        if result == wx.ID_NO:
            return
        default = (255, 255, 255, 255)
        if row_num == -1:
            # unhighlight any selected rows:
            for row in self.selected_rows:
                attr = wx.grid.GridCellAttr()
                attr.SetBackgroundColour(default)
                self.grid.SetRowAttr(row, attr)
            row_num = self.grid.GetNumberRows() - 1
            self.deleteRowButton.Disable()
            self.selected_rows = {row_num}
        # remove row(s) from the contribution
        df = self.contribution.tables[self.grid_type].df
        row_nums = list(range(len(df)))
        df = df.iloc[[i for i in row_nums if i not in self.selected_rows]]
        self.contribution.tables[self.grid_type].df = df
        # now remove row(s) from grid
        # delete rows, adjusting the row # appropriately as you delete
        for num, row in enumerate(self.selected_rows):
            row -= num
            if row < 0:
                row = 0
            self.grid.remove_row(row)
            attr = wx.grid.GridCellAttr()
            attr.SetBackgroundColour(default)
            self.grid.SetRowAttr(row, attr)
        # reset the grid
        self.selected_rows = set()
        self.deleteRowButton.Disable()
        self.grid.Refresh()
        self.main_sizer.Fit(self)

    def exit_col_remove_mode(self, event):
        """
        go back from 'remove cols' mode to normal
        """
        # close help messge
        self.toggle_help(event=None, mode='close')
        # update mode
        self.remove_cols_mode = False
        # re-enable all buttons
        for btn in [self.add_cols_button, self.remove_row_button, self.add_many_rows_button]:
            btn.Enable()

        # unbind grid click for deletion
        self.grid.Unbind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK)
        # undo visual cues
        self.grid.SetWindowStyle(wx.DEFAULT)
        self.grid_box.GetStaticBox().SetWindowStyle(wx.DEFAULT)
        self.msg_text.SetLabel(self.default_msg_text)
        self.help_msg_boxsizer.Fit(self.help_msg_boxsizer.GetStaticBox())
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
        When user clicks on a grid label,
        determine if it is a row label or a col label.
        Pass along the event to the appropriate function.
        (It will either highlight a column for editing all values,
        or highlight a row for deletion).
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
        """
        Import a MagIC-format file
        """
        if self.grid.changes:
            print("-W- Your changes will be overwritten...")
            wind = pw.ChooseOne(self, "Import file anyway", "Save grid first",
                                "-W- Your grid has unsaved changes which will be overwritten if you import a file now...")
            wind.Centre()
            res = wind.ShowModal()
            # save grid first:
            if res == wx.ID_NO:
                self.onSave(None, alert=True, destroy=False)
                # reset self.changes
                self.grid.changes = set()

        openFileDialog = wx.FileDialog(self, "Open MagIC-format file", self.WD, "",
                                       "MagIC file|*.*", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        result = openFileDialog.ShowModal()
        if result == wx.ID_OK:
            # get filename
            filename = openFileDialog.GetPath()
            # make sure the dtype is correct
            f = open(filename)
            line = f.readline()
            if line.startswith("tab"):
                delim, dtype = line.split("\t")
            else:
                delim, dtype = line.split("")
            f.close()
            dtype = dtype.strip()
            if (dtype != self.grid_type) and (dtype + "s" != self.grid_type):
                text = "You are currently editing the {} grid, but you are trying to import a {} file.\nPlease open the {} grid and then re-try this import.".format(self.grid_type, dtype, dtype)
                pw.simple_warning(text)
                return
            # grab old data for concatenation
            if self.grid_type in self.contribution.tables:
                old_df_container = self.contribution.tables[self.grid_type]
            else:
                old_df_container = None
            old_col_names = self.grid.col_labels
            # read in new file and update contribution
            df_container = cb.MagicDataFrame(filename, dmodel=self.dm,
                                             columns=old_col_names)
            # concatenate if possible
            if not isinstance(old_df_container, type(None)):
                df_container.df = pd.concat([old_df_container.df, df_container.df],
                                            axis=0, sort=True)
            self.contribution.tables[df_container.dtype] = df_container
            self.grid_builder = GridBuilder(self.contribution, self.grid_type,
                                            self.panel, parent_type=self.parent_type,
                                            reqd_headers=self.reqd_headers)
            # delete old grid
            self.grid_box.Hide(0)
            self.grid_box.Remove(0)
            # create new, updated grid
            self.grid = self.grid_builder.make_grid()
            self.grid.InitUI()
            # add data to new grid
            self.grid_builder.add_data_to_grid(self.grid, self.grid_type)
            # add new grid to sizer and fit everything
            self.grid_box.Add(self.grid, flag=wx.ALL, border=5)
            self.main_sizer.Fit(self)
            self.Centre()
            # add any needed drop-down-menus
            self.drop_down_menu = drop_down_menus.Menus(self.grid_type,
                                                        self.contribution,
                                                        self.grid)
            # done!
        return

    def onCancelButton(self, event):
        """
        Quit grid with warning if unsaved changes present
        """
        if self.grid.changes:
            dlg1 = wx.MessageDialog(self, caption="Message:",
                                    message="Are you sure you want to exit this grid?\nYour changes will not be saved.\n ",
                                    style=wx.OK|wx.CANCEL)
            result = dlg1.ShowModal()
            if result == wx.ID_OK:
                dlg1.Destroy()
                self.Destroy()
        else:
            self.Destroy()
        if self.main_frame:
            self.main_frame.Show()
            self.main_frame.Raise()


    def onSave(self, event, alert=False, destroy=True):
        """
        Save grid data
        """
        # tidy up drop_down menu
        if self.drop_down_menu:
            self.drop_down_menu.clean_up()
        # then save actual data
        self.grid_builder.save_grid_data()
        if not event and not alert:
            return
        # then alert user
        wx.MessageBox('Saved!', 'Info',
                      style=wx.OK | wx.ICON_INFORMATION)
        if destroy:
            self.Destroy()

    ### Custom copy/paste functionality

    def onCopyMode(self, event):
        # first save all grid data
        self.grid_builder.save_grid_data()
        self.drop_down_menu.clean_up()
        # enable and un-grey the exit copy mode button
        self.copyButton.SetLabel('End copy mode')
        self.Bind(wx.EVT_BUTTON, self.onEndCopyMode, self.copyButton)
        # disable and grey out other buttons
        btn_list = [self.add_cols_button, self.remove_cols_button,
                    self.remove_row_button, self.add_many_rows_button,
                    self.importButton, self.cancelButton, self.exitButton]
        for btn in btn_list:
            btn.Disable()
        self.copySelectionButton.Enable()
        # next, undo useless bindings (mostly for drop-down-menus)
        # this one works:
        self.drop_down_menu.EndUI()
        # these ones don't work: (it doesn't matter which one you bind to)
        #self.grid.Unbind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK)
        #self.Unbind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK)
        #self.panel.Unbind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK)
        # this works hack-like:
        self.grid.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.do_nothing)
        # this one is irrelevant (it just deals with resizing)
        #self.Unbind(wx.EVT_KEY_DOWN)
        #
        # make grid uneditable
        self.grid.EnableEditing(False)
        self.Refresh()
        # change and show help message
        copy_text = """You are now in 'copy' mode.  To return to 'editing' mode, click 'End copy mode'.
To copy the entire grid, click the 'Copy all cells' button.
To copy a selection of the grid, you must first make a selection by either clicking and dragging, or using Shift click.
Once you have your selection, click the 'Copy selected cells' button, or hit 'Ctrl c'.
You may then paste into a text document or spreadsheet!
"""
        self.toggle_help_btn.SetLabel('Hide help')
        self.msg_text.SetLabel(copy_text)
        self.help_msg_boxsizer.Fit(self.help_msg_boxsizer.GetStaticBox())
        self.main_sizer.Fit(self)
        self.help_msg_boxsizer.ShowItems(True)
        self.do_fit(None)
        # then bind for selecting cells in multiple columns
        self.grid.Bind(wx.grid.EVT_GRID_RANGE_SELECT, self.onDragSelection)
        # bind Cmd c for copy
        self.grid.Bind(wx.EVT_KEY_DOWN, self.onKey)
        # done!

    def onDragSelection(self, event):
        """
        Set self.df_slice based on user's selection
        """
        if self.grid.GetSelectionBlockTopLeft():
            #top_left = self.grid.GetSelectionBlockTopLeft()
            #bottom_right = self.grid.GetSelectionBlockBottomRight()
            # awkward hack to fix wxPhoenix memory problem, (Github issue #221)
            bottom_right = eval(repr(self.grid.GetSelectionBlockBottomRight()).replace("GridCellCoordsArray: ", "").replace("GridCellCoords", ""))
            top_left = eval(repr(self.grid.GetSelectionBlockTopLeft()).replace("GridCellCoordsArray: ", "").replace("GridCellCoords", ""))
            #
            top_left = top_left[0]
            bottom_right = bottom_right[0]
        else:
            return
        # GetSelectionBlock returns (row, col)
        min_col = top_left[1]
        max_col = bottom_right[1]
        min_row = top_left[0]
        max_row = bottom_right[0]
        self.df_slice = self.contribution.tables[self.grid_type].df.iloc[min_row:max_row+1, min_col:max_col+1]


    def do_nothing(self, event):
        """
        Dummy method to prevent default header-click behavior
        while in copy mode
        """
        pass

    def onKey(self, event):
        """
        Copy selection if control down and 'c'
        """
        if event.CmdDown() or event.ControlDown():
            if event.GetKeyCode() == 67:
                self.onCopySelection(None)

    def onSelectAll(self, event):
        """
        Selects full grid and copies it to the Clipboard
        """
        # do clean up here!!!
        if self.drop_down_menu:
            self.drop_down_menu.clean_up()
        # save all grid data
        self.grid_builder.save_grid_data()
        df = self.contribution.tables[self.grid_type].df
        # write df to clipboard for pasting
        # header arg determines whether columns are taken
        # index arg determines whether index is taken
        pd.DataFrame.to_clipboard(df, header=False, index=False)
        print('-I- You have copied all cells! You may paste them into a text document or spreadsheet using Command v.')
        # done!

    def onCopySelection(self, event):
        """
        Copies self.df_slice to the Clipboard if slice exists
        """
        if self.df_slice is not None:
            pd.DataFrame.to_clipboard(self.df_slice, header=False, index=False)
            self.grid.ClearSelection()
            self.df_slice = None
            print('-I- You have copied the selected cells.  You may paste them into a text document or spreadsheet using Command v.')
        else:
            print('-W- No cells were copied! You must highlight a selection cells before hitting the copy button.  You can do this by clicking and dragging, or by using the Shift key and click.')

    def onEndCopyMode(self, event):
        # enable/disable buttons as needed
        btn_list = [self.add_cols_button, self.remove_cols_button,
                    self.remove_row_button, self.add_many_rows_button,
                    self.importButton, self.cancelButton, self.exitButton]
        for btn in btn_list:
            btn.Enable()
        self.copySelectionButton.Disable()
        self.copyButton.SetLabel('Start copy mode')
        self.Bind(wx.EVT_BUTTON, self.onCopyMode, self.copyButton)
        # get rid of special help message
        self.toggle_help_btn.SetLabel('Show help')
        self.msg_text.SetLabel(self.default_msg_text)
        self.help_msg_boxsizer.Fit(self.help_msg_boxsizer.GetStaticBox())
        self.main_sizer.Fit(self)
        self.help_msg_boxsizer.ShowItems(False)
        self.do_fit(None)

        # re-init normal grid UI
        self.drop_down_menu.InitUI()
        self.grid.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.onLeftClickLabel, self.grid)
        self.grid.EnableEditing(True)
        # deselect any cells selected during copy mode
        self.grid.ClearSelection()
        self.df_slice = None
        # get rid of special copy binding
        self.grid.Unbind(wx.EVT_KEY_DOWN)#, self.onKey)


class GridBuilder(object):
    """
    Takes MagIC data and puts them into a MagicGrid
    """

    def __init__(self, contribution, grid_type, panel,
                 parent_type=None, reqd_headers=None,
                 exclude_cols=(), huge=False):
        self.contribution = contribution
        self.exclude_cols = exclude_cols
        if grid_type in contribution.tables:
            self.magic_dataframe = contribution.tables[grid_type]
        else:
            self.magic_dataframe = cb.MagicDataFrame(dtype=grid_type)
        self.grid_type = grid_type
        self.data_model = contribution.data_model
        self.reqd_headers = reqd_headers

        self.panel = panel
        self.parent_type = parent_type
        self.huge=huge
        self.grid = None

    def make_grid(self):
        """
        return grid
        """
        changes = None
        # if there is a MagicDataFrame, extract data from it
        if isinstance(self.magic_dataframe, cb.MagicDataFrame):
            # get columns and reorder slightly
            col_labels = list(self.magic_dataframe.df.columns)
            for ex_col in self.exclude_cols:
                col_labels.pop(ex_col)
            if self.grid_type == 'ages':
                levels = ['specimen', 'sample', 'site', 'location']
                for label in levels[:]:
                    if label in col_labels:
                        col_labels.remove(label)
                    else:
                        levels.remove(label)
                col_labels[:0] = levels
            else:
                if self.parent_type:
                    if self.parent_type[:-1] in col_labels:
                        col_labels.remove(self.parent_type[:-1])
                    col_labels[:0] = [self.parent_type[:-1]]
                if self.grid_type[:-1] in col_labels:
                    col_labels.remove(self.grid_type[:-1])
                col_labels[:0] = (self.grid_type[:-1],)
            for col in col_labels:
                if col not in self.magic_dataframe.df.columns:
                    self.magic_dataframe.df[col] = None
            self.magic_dataframe.df = self.magic_dataframe.df[col_labels]
            self.magic_dataframe.sort_dataframe_cols()
            col_labels = list(self.magic_dataframe.df.columns)
            row_labels = self.magic_dataframe.df.index
            # make sure minimum defaults are present
            for header in self.reqd_headers:
                if header not in col_labels:
                    changes = set([1])
                    col_labels.append(header)
        # if there is no pre-existing MagicDataFrame,
        # make a blank grid with do some defaults:
        else:
            # default headers
            #col_labels = list(self.data_model.get_headers(self.grid_type, 'Names'))
            #col_labels[:0] = self.reqd_headers
            col_labels = list(self.reqd_headers)
            if self.grid_type in ['specimens', 'samples', 'sites']:
                col_labels.extend(['age', 'age_sigma'])
            ## use the following line if you want sorted column labels:
            #col_labels = sorted(set(col_labels))
            # defaults are different for ages
            if self.grid_type == 'ages':
                levels = ['specimen', 'sample', 'site', 'location']
                for label in levels:
                    if label in col_labels:
                        col_labels.remove(label)
                col_labels[:0] = levels
            else:
                if self.parent_type:
                    col_labels.remove(self.parent_type[:-1])
                    col_labels[:0] = [self.parent_type[:-1]]
                col_labels.remove(self.grid_type[:-1])
                col_labels[:0] = [self.grid_type[:-1]]
        # make sure all reqd cols are in magic_dataframe
        for col in col_labels:
            if col not in self.magic_dataframe.df.columns:
                self.magic_dataframe.df[col] = None
        # make the grid
        if not self.huge:
            grid = magic_grid.MagicGrid(parent=self.panel, name=self.grid_type,
                                        row_labels=[], col_labels=col_labels)
        # make the huge grid
        else:
            row_labels = self.magic_dataframe.df.index
            grid = magic_grid.HugeMagicGrid(parent=self.panel, name=self.grid_type,
                            row_labels=row_labels, col_labels=col_labels)
        grid.do_event_bindings()
        grid.changes = changes

        self.grid = grid
        return grid

    def add_data_to_grid(self, grid, grid_type=None):
        if isinstance(self.magic_dataframe, cb.MagicDataFrame):
            grid.add_items(self.magic_dataframe.df, self.exclude_cols)

        if not self.huge:
            grid.size_grid()

        if not self.huge:
            # always start with at least one row:
            if not grid.GetNumberRows():
                grid.add_row()
            # if adding actual data, remove the blank row
            else:
                values = [grid.GetCellValue(0, num) for num in range(grid.GetNumberCols())]
                if not any(values):
                    grid.remove_row(0)
            # include horizontal scrollbar unless grid has less than 5 rows
            grid.set_scrollbars()

        # add sensible defaults for an empty age grid
        if self.grid_type == 'ages':
            if self.current_grid_empty():
                self.add_age_defaults()

    def add_age_defaults(self):
        """
        Add columns as needed:
        age, age_unit, specimen, sample, site, location.
        """
        if isinstance(self.magic_dataframe, cb.MagicDataFrame):
            for col in ['age', 'age_unit']:
                if col not in self.grid.col_labels:
                    self.grid.add_col(col)
            for level in ['locations', 'sites', 'samples', 'specimens']:
                if level in self.contribution.tables:
                    if level[:-1] not in self.grid.col_labels:
                        self.grid.add_col(level[:-1])

    def current_grid_empty(self):
        """
        Check to see if grid is empty except for default values
        """
        empty = True
        # df IS empty if there are no rows
        if not any(self.magic_dataframe.df.index):
            empty = True
        # df is NOT empty if there are at least two rows
        elif len(self.grid.row_labels) > 1:
            empty = False
        # if there is one row, df MIGHT be empty
        else:
            # check all the non-null values
            non_null_vals = [val for val in self.magic_dataframe.df.values[0] if cb.not_null(val, False)]
            for val in non_null_vals:
                if not isinstance(val, str):
                    empty = False
                    break
                # if there are any non-default values, grid is not empty
                if val.lower() not in ['this study', 'g', 'i']:
                    empty = False
                    break
        return empty


    def save_grid_data(self):
        """
        Save grid data in the data object
        """
        if not self.grid.changes:
            print('-I- No changes to save')
            return

        starred_cols = self.grid.remove_starred_labels()
        # locks in value in cell currently edited
        self.grid.SaveEditControlValue()
        # changes is a dict with key values == row number
        if self.grid.changes:
            new_data = self.grid.save_items()
            # HugeMagicGrid will return a pandas dataframe
            if self.huge:
                self.magic_dataframe.df = new_data
            # MagicGrid will return a dictionary with
            # new/updated data that must be incorporated
            # into the dataframe
            else:
                for key in new_data:
                    data = new_data[key]
                    # update the row if it exists already,
                    # otherwise create a new row

                    updated = self.magic_dataframe.update_row(key, data)
                    if not isinstance(updated, pd.DataFrame):
                        if self.grid_type == 'ages':
                            label = key
                        else:
                            label = self.grid_type[:-1]
                        self.magic_dataframe.add_row(label, data,
                                                     self.grid.col_labels)
            # update the contribution with the new dataframe
            self.contribution.tables[self.grid_type] = self.magic_dataframe
            # *** probably don't actually want to write to file, here (but maybe)

            self.contribution.write_table_to_file(self.grid_type)
            #self.magic_dataframe.write_magic_file("{}.txt".format(self.grid_type),
            #                                      self.contribution.directory)
            # propagate age info if age table was edited
            if self.grid_type == 'ages':
                self.contribution.propagate_ages()
            return

    def fill_defaults(self):
        """
        Fill in self.grid with default values in certain columns.
        Only fill in new values if grid is missing those values.
        """
        defaults = {'result_quality': 'g',
                    'result_type': 'i',
                    'orientation_quality': 'g',
                    'citations': 'This study'}
        for col_name in defaults:
            if col_name in self.grid.col_labels:
                # try to grab existing values from contribution
                if self.grid_type in self.contribution.tables:
                    if col_name in self.contribution.tables[self.grid_type].df.columns:
                        old_vals = self.contribution.tables[self.grid_type].df[col_name]
                        # if column is completely filled in, skip
                        if all([cb.not_null(val, False) for val in old_vals]):
                            continue
                        new_val = defaults[col_name]
                        vals = list(np.where((old_vals.notnull()) & (old_vals != ''), old_vals, new_val))
                    else:
                        vals = [defaults[col_name]] * self.grid.GetNumberRows()
                # if values not available in contribution, use defaults
                else:
                    vals = [defaults[col_name]] * self.grid.GetNumberRows()
            # if col_name not present in grid, skip
            else:
                vals = None
            #
            if vals:
                print('-I- Updating column "{}" with default values'.format(col_name))
                if self.huge:
                    self.grid.SetColumnValues(col_name, vals)
                else:
                    col_ind = self.grid.col_labels.index(col_name)
                    for row, val in enumerate(vals):
                        self.grid.SetCellValue(row, col_ind, val)
                        self.grid.changes = set(range(self.grid.GetNumberRows()))

    def get_result_children(self, result_data):
        """
        takes in dict in form of {'er_specimen_names': 'name1:name2:name3'}
        and so forth.
        returns lists of specimens, samples, sites, and locations
        """
        specimens, samples, sites, locations = "", "", "", ""
        children = {'specimen': specimens, 'sample': samples,
                    'site': sites, 'location': locations}
        for dtype in children:
            header_name = 'er_' + dtype + '_names'
            if result_data[header_name]:
                children[dtype] = result_data[header_name].split(":")
                # make sure there are no extra spaces in names
                children[dtype] = [child.strip() for child in children[dtype]]

        return children['specimen'], children['sample'], children['site'], children['location']

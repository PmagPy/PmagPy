import wx
import wx.grid


class MagicGrid(wx.grid.Grid):
    """
    grid class
    """

    def __init__(self, parent, name, row_labels, col_labels, row_items=None, size=0):
        # row_items is an optional list of Pmag_objects
        self.row_items = []
        if row_items:
            self.row_items = row_items
        else:
            self.row_items = ['' for label in row_labels]
        self.changes = None
        self.row_labels = sorted(row_labels)
        self.col_labels = col_labels
        if not size:
            super(MagicGrid, self).__init__(parent, -1, name=name)
        if size:
            super(MagicGrid, self).__init__(parent, -1, name=name, size=size)

        ### the next few lines may prove unnecessary
        ancestry = ['specimen', 'sample', 'site', 'location', None]

        if name == 'age':
            self.parent_type = 'location'
        else:
            try:
                self.parent_type = ancestry[ancestry.index(name) + 1]
            except ValueError:
                self.parent_type = None
        ###
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
        self.ShowScrollbars(wx.SHOW_SB_NEVER, wx.SHOW_SB_DEFAULT)
        return data


    def add_items(self, items_list):
        er_data = {item.name: item.er_data for item in items_list}
        pmag_data = {item.name: item.pmag_data for item in items_list}
        items_list = sorted(items_list, key=lambda item: item.name)

        for item in items_list[:]:
            self.add_row(item.name, item)
        self.add_data(er_data)
        self.add_data(pmag_data)
        self.add_parents()
        
        
    def add_data(self, data_dict):
        # requires dict in this this format:
        # {spec_name: {}, spec2_name: {}}
        for num, row in enumerate(self.row_labels):
            if row:
                for n, col in enumerate(self.col_labels[1:]):
                    if col in data_dict[row].keys():
                        value = data_dict[row][col]
                        # set defaults
                        if col == 'er_citation_names' and not value:
                            value = 'This study'
                    else:
                        value = ''
                    if value:
                        self.SetCellValue(num, n+1, value)

    def add_parents(self, col_num=1):
        if self.parent_type and self.row_items:
            for num, row in enumerate(self.row_items):
                if row:
                    parent = row.get_parent()
                    if parent:
                        self.SetCellValue(num, col_num, parent.name)
                

    def size_grid(self, event=None):
        self.AutoSizeColumns(True)

        ## this doesn't seem to be necessary, actually
        ## actually is bad???
        #self.AutoSize() # prevents display failure

        for col in range(len(self.col_labels)):
            # adjust column widths to be a little larger then auto for nicer editing
            orig_size = self.GetColSize(col)
            if orig_size > 110:
                size = orig_size * 1.1
            else:
                size = orig_size * 1.6
            self.SetColSize(col, size)

        self.ForceRefresh()


    def do_event_bindings(self):
        self.Bind(wx.grid.EVT_GRID_EDITOR_CREATED, self.on_edit_grid)
        self.Bind(wx.grid.EVT_GRID_EDITOR_SHOWN, self.on_edit_grid)
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        #self.Bind(wx.EVT_TEXT, self.on_key_down_in_editor)
        #self.Bind(wx.EVT_CHAR, self.on_key_down)
        self.Bind(wx.EVT_TEXT_PASTE, self.on_paste_in_editor)

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

    def on_key_down(self, event):
        keycode = event.GetKeyCode()
        meta_down = event.MetaDown()
        if keycode == 86 and meta_down:
            # treat it as if it were a wx.EVT_TEXT_SIZE
            paste_event = wx.CommandEvent(wx.wxEVT_COMMAND_TEXT_PASTE,
                                          self.GetId())
            self.GetEventHandler().ProcessEvent(paste_event)
        else:
            event.Skip()

    def on_paste_in_editor(self, event):
        self.do_paste(event)

    def do_paste(self, event):
        data_obj = wx.TextDataObject()
        col = self.GetGridCursorCol()
        row = self.GetGridCursorRow()
        num_cols = self.GetNumberCols()

        if wx.TheClipboard.Open():
            wx.TheClipboard.GetData(data_obj)
            text = data_obj.GetText().strip('\r')
            if '\r' in text or '\t' in text:
                # split text into a list
                text_list = text.split('\r')
                self.SetCellValue(row, col, text)
                num_rows = self.GetNumberRows()
                for text_row in text_list:
                    # extra rows if needed
                    if row > num_rows - 1:
                        self.add_row()
                        num_rows += 1
                    # split row data into cols
                    if '\t' in text_row.strip('\t'):
                        text_items = text_row.split('\t')
                        for num, item in enumerate(text_items):
                            if (col + num) < num_cols:
                                self.SetCellValue(row, col + num, item)
                    # unless there is only one column
                    else:
                        self.SetCellValue(row, col, text_row)
                    # note changes
                    if not self.changes:
                        self.changes = set()
                    self.changes.add(row)
                    row += 1

            else:
                # simple pasting
                self.SetCellValue(row, col, text)
                self.ForceRefresh()
        self.size_grid()
        wx.TheClipboard.Close()
        event.Skip()


    def add_row(self, label='', item=''):
        """
        Add a row to the grid
        """
        self.AppendRows(1)
        last_row = self.GetNumberRows() - 1
        self.SetCellValue(last_row, 0, str(label))
        self.row_labels.append(label)
        self.row_items.append(item)

    def remove_row(self, row_num=None):
        """
        Remove a row from the grid
        """
        #DeleteRows(self, pos, numRows, updateLabel
        if not row_num and row_num != 0:
            row_num = self.GetNumberRows() - 1
        label = self.GetCellValue(row_num, 0)
        self.DeleteRows(pos=row_num, numRows=1, updateLabels=True)

        # remove label from row_labels
        try:
            self.row_labels.remove(label)
        except ValueError:
            # if label name hasn't been saved yet, simply truncate row_labels
            self.row_labels = self.row_labels[:-1]
        self.row_items.pop(row_num)
        if not self.changes:
            self.changes = set()
        self.changes.add(-1)
        # fix #s for rows edited:
        self.update_changes_after_row_delete(row_num)

    def update_changes_after_row_delete(self, row_num):
        """
        Update self.changes so that row numbers for edited rows are still correct.
        I.e., if row 4 was edited and then row 2 was deleted, row 4 becomes row 3.
        This function updates self.changes to reflect that. 
        """
        if row_num in self.changes.copy():
            self.changes.remove(row_num)
        updated_rows = []
        for changed_row in self.changes:
            if changed_row == -1:
                updated_rows.append(-1)
            if changed_row > row_num:
                updated_rows.append(changed_row - 1)
            if changed_row < row_num:
                updated_rows.append(changed_row)
        self.changes = set(updated_rows)

    def add_col(self, label):
        """
        Add a new column to the grid.
        Resize grid to display the column.
        """
        self.AppendCols(1)
        last_col = self.GetNumberCols() - 1
        self.SetColLabelValue(last_col, label)
        self.col_labels.append(label)
        self.size_grid()
        return last_col


    def remove_col(self, col_num):
        """
        Remove a column from the grid.
        Resize grid to display correctly.
        """
        label_value = self.GetColLabelValue(col_num)
        self.col_labels.remove(label_value)
        result = self.DeleteCols(pos=col_num, numCols=1, updateLabels=True)
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

    def remove_starred_labels(self):#, grid):
        cols_with_stars = []
        for col in range(self.GetNumberCols()):
            label = self.GetColLabelValue(col)
            if '**' in label:
                self.SetColLabelValue(col, label.strip('**'))
                cols_with_stars.append(col)
        return cols_with_stars


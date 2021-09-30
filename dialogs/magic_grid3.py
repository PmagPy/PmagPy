#import matplotlib
#matplotlib.use('WXAgg')
import sys
import numpy as np
import pandas as pd
import wx
import wx.grid as gridlib
import wx.lib.mixins.gridlabelrenderer as gridlabelrenderer


class HugeTable(gridlib.GridTableBase):

    """
    Table class for virtual grid
    """

    def __init__(self, log, num_rows, num_cols):
        gridlib.GridTableBase.__init__(self)
        self.log = log

        self.odd=gridlib.GridCellAttr()
        #self.odd.SetBackgroundColour("sky blue")
        self.even=gridlib.GridCellAttr()
        #self.even.SetBackgroundColour("sea green")
        self.num_rows = num_rows
        self.num_cols = num_cols
        self.dataframe = []

    def GetAttr(self, row, col, kind):
        attr = [self.even, self.odd][row % 2]
        attr.IncRef()
        return attr

    def GetNumberRows(self):
        return self.num_rows

    def GetNumberCols(self):
        return self.num_cols

    def IsEmptyCell(self, row, col):
        return False

    def GetValue(self, row, col):
        """
        Find the matching value from pandas DataFrame,
        return it.
        """
        if len(self.dataframe):
            return str(self.dataframe.iloc[row, col])
        return ''

    def SetValue(self, row, col, value):
        """
        Set value in the pandas DataFrame
        """
        self.dataframe.iloc[row, col] = value

    def SetColumnValues(self, col, value):
        """
        Custom method to efficiently set all values
        in a column.

        Parameters
        ----------
        col : str or int
            name or index position of column
        value : list-like
            values to assign to all cells in the column
        """
        try:
            self.dataframe.iloc[:, col] = value
        except ValueError:
            self.dataframe.loc[:, col] = value

    def GetColLabelValue(self, col):
        """
        Get col label from dataframe
        """
        if len(self.dataframe):
            return self.dataframe.columns[col]
        return ''

    def SetColLabelValue(self, col, value):
        """
        Set col label value in dataframe
        """
        if len(self.dataframe):
            col_name = str(self.dataframe.columns[col])
            self.dataframe.rename(columns={col_name: str(value)}, inplace=True)
        return None

    def AppendCols(self, *args):
        self.num_cols += 1
        msg = gridlib.GridTableMessage(self,  # The table
                               gridlib.GRIDTABLE_NOTIFY_COLS_APPENDED, # what we did to it
                               1)                                       # how many
        self.GetView().ProcessTableMessage(msg)
        return True

    # this currently fails with segfault
    def DeleteCols(self, pos, numCols, updateLabels=True):
        self.num_cols -= 1
        grid = self.GetView()
        grid.BeginBatch()
        msg = gridlib.GridTableMessage(self,
                                       gridlib.GRIDTABLE_NOTIFY_COLS_DELETED,
                                       numCols)
        grid.ProcessTableMessage(msg)
        grid.EndBatch()
        return True


class BaseMagicGrid(gridlib.Grid, gridlabelrenderer.GridWithLabelRenderersMixin):
    """
    grid class
    """

    def __init__(self, parent, name, row_labels, col_labels, size=0):
        self.name = name
        self.changes = None
        self.row_labels = sorted(row_labels)
        self.col_labels = col_labels
        if not size:
            super(BaseMagicGrid, self).__init__(parent, -1, name=name)
        if size:
            super(BaseMagicGrid, self).__init__(parent, -1, name=name, size=size)
        gridlabelrenderer.GridWithLabelRenderersMixin.__init__(self)
        ### the next few lines may prove unnecessary
        ancestry = ['specimen', 'sample', 'site', 'location', None]

        if name == 'age':
            self.parent_type = None
        else:
            try:
                self.parent_type = ancestry[ancestry.index(name) + 1]
            except ValueError:
                self.parent_type = None
        ###
        #self.InitUI()

    def InitUI(self):
        pass

    def set_scrollbars(self):
        """
        Set to always have vertical scrollbar.
        Have horizontal scrollbar unless grid has very few rows.
        Older versions of wxPython will choke on this,
        in which case nothing happens.
        """
        try:
            if len(self.row_labels) < 5:
                show_horizontal = wx.SHOW_SB_NEVER
            else:
                show_horizontal = wx.SHOW_SB_DEFAULT
            self.ShowScrollbars(show_horizontal, wx.SHOW_SB_DEFAULT)
        except AttributeError:
            pass

    def add_items(self, dataframe, hide_cols=()):
        """
        Add items and/or update existing items in grid
        """
        # replace "None" values with ""
        dataframe = dataframe.fillna("")
        # remove any columns that shouldn't be shown
        for col in hide_cols:
            if col in dataframe.columns:
                del dataframe[col]
        # add more rows
        self.AppendRows(len(dataframe))
        columns = dataframe.columns
        row_num = -1
        # fill in all rows with appropriate values
        for ind, row in dataframe.iterrows():
            row_num += 1
            for col_num, col in enumerate(columns):
                value = row[col]
                self.SetCellValue(row_num, col_num, str(value))
                # set citation default value
                if col == 'citations':
                    citation = row['citations']
                    if (citation is None) or (citation is np.nan):
                            self.SetCellValue(row_num, col_num, 'This study')
                    else:
                        if 'This study' not in citation:
                            if len(citation):
                                citation += ':'
                            citation += 'This study'
                            self.SetCellValue(row_num, col_num, citation)
        self.row_labels.extend(dataframe.index)


    def save_items(self, rows=None, verbose=False):
        """
        Return a dictionary of row data for selected rows:
        {1: {col1: val1, col2: val2}, ...}
        If a list of row numbers isn't provided, get data for all.
        """
        if rows:
            rows = rows
        else:
            rows = list(range(self.GetNumberRows()))
        cols = list(range(self.GetNumberCols()))
        data = {}
        for row in rows:
            data[row] = {}
            for col in cols:
                col_name = self.GetColLabelValue(col)
                if verbose:
                    print(col_name, ":", self.GetCellValue(row, col))
                data[row][col_name] = self.GetCellValue(row, col)
        return data

    def size_grid(self, event=None):
        self.AutoSizeColumns(True)
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
        self.Bind(gridlib.EVT_GRID_EDITOR_CREATED, self.on_edit_grid)
        self.Bind(gridlib.EVT_GRID_EDITOR_SHOWN, self.on_edit_grid)
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
        meta_down = event.MetaDown() or event.CmdDown()
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
        """
        Read clipboard into dataframe
        Paste data into grid, adding extra rows if needed
        and ignoring extra columns.
        """
        # find where the user has clicked
        col_ind = self.GetGridCursorCol()
        row_ind = self.GetGridCursorRow()
        # read in clipboard text
        text_df = pd.read_clipboard(header=None, sep='\t').fillna('')
        # add extra rows if need to accomadate clipboard text
        row_length_diff = len(text_df) - (len(self.row_labels) - row_ind)
        if row_length_diff > 0:
            for n in range(row_length_diff):
                self.add_row()
        # ignore excess columns if present
        col_length_diff = len(text_df.columns) - (len(self.col_labels) - col_ind)
        if col_length_diff > 0:
            text_df = text_df.iloc[:, :-col_length_diff].copy()
        # go through copied text and parse it into the grid rows
        for label, row_data in text_df.iterrows():
            col_range = list(range(col_ind, col_ind + len(row_data)))
            if len(row_data) > 1:
                cols = list(zip(col_range, row_data.index))
                for column in cols:
                    value = row_data[column[1]]
                    this_col = column[0]
                    self.SetCellValue(row_ind, this_col, str(value))
            else:
                value = row_data[0]
                self.SetCellValue(row_ind, col_ind, str(value))
            row_ind += 1
        # could instead use wxPython clipboard here
        # see old git history for that
        self.size_grid()
        event.Skip()

    def add_row(self, label=""):
        """
        Add a row to the grid
        """
        self.AppendRows(1)
        last_row = self.GetNumberRows() - 1
        self.SetCellValue(last_row, 0, str(label))
        self.row_labels.append(label)

    def remove_row(self, row_num=None):
        """
        Remove a row from the grid
        """
        if not row_num and row_num != 0:
            row_num = self.GetNumberRows() - 1
        label = self.GetCellValue(row_num, 0)
        self.DeleteRows(pos=row_num, numRows=1, updateLabels=True)

        # remove label from row_labels
        self.row_labels.pop(row_num)
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


    def remove_col(self, col_num):
        """
        Remove a column from the grid.
        Resize grid to display correctly.
        """
        label_value = self.GetColLabelValue(col_num).strip('**').strip('^^')
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
        cols_with_hats = []
        for col in range(self.GetNumberCols()):
            label = self.GetColLabelValue(col)
            if '**' in label:
                self.SetColLabelValue(col, label.strip('**'))
                cols_with_stars.append(col)
            if '^^' in label:
                self.SetColLabelValue(col, label.strip('^^'))
                cols_with_hats.append(col)
        return cols_with_stars, cols_with_hats

    def paint_invalid_row(self, row, color="LIGHT BLUE"):
        self.SetRowLabelRenderer(row, MyRowLabelRenderer(color))

    def paint_invalid_cell(self, row, col, color='MEDIUM VIOLET RED',
                           skip_cell=False):
        """
        Take row, column, and turn it color
        """
        self.SetColLabelRenderer(col, MyColLabelRenderer('#1101e0'))
        self.SetRowLabelRenderer(row, MyRowLabelRenderer('#1101e0'))
        # SetCellRenderer doesn't work with table-based grid (HugeGrid class)
        if not skip_cell:
            self.SetCellRenderer(row, col, MyCustomRenderer(color))


class MagicGrid(BaseMagicGrid):
    """
    grid class
    """
    def __init__(self, parent, name, row_labels, col_labels, size=0):
        super(MagicGrid, self).__init__(parent, name, row_labels, col_labels, size=0)

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
        # set scrollbars
        self.set_scrollbars()

    def add_col(self, label):
        """
        Add a new column to the grid.
        Resize grid to display the column.

        Parameters
        ----------
        label : str

        Returns
        ---------
        last_col: int
            index column number of added col

        """
        self.AppendCols(1, updateLabels=False)
        last_col = self.GetNumberCols() - 1
        self.SetColLabelValue(last_col, label)
        self.col_labels.append(label)
        self.size_grid()
        return last_col

    def add_items(self, dataframe, hide_cols=()):
        """
        Add items and/or update existing items in grid
        """
        # replace "None" values with ""
        dataframe = dataframe.fillna("")
        # remove any columns that shouldn't be shown
        for col in hide_cols:
            if col in dataframe.columns:
                del dataframe[col]
        # add more rows
        self.AppendRows(len(dataframe))
        columns = dataframe.columns
        row_num = -1
        # fill in all rows with appropriate values
        for ind, row in dataframe.iterrows():
            row_num += 1
            for col_num, col in enumerate(columns):
                value = row[col]
                self.SetCellValue(row_num, col_num, str(value))
                # set citation default value
                if col == 'citations':
                    citation = row['citations']
                    if (citation is None) or (citation is np.nan):
                            self.SetCellValue(row_num, col_num, 'This study')
                    else:
                        if 'This study' not in citation:
                            if len(citation):
                                citation += ':'
                            citation += 'This study'
                            self.SetCellValue(row_num, col_num, citation)
        self.row_labels.extend(dataframe.index)


    def save_items(self, rows=None, verbose=False):
        """
        Return a dictionary of row data for selected rows:
        {1: {col1: val1, col2: val2}, ...}
        If a list of row numbers isn't provided, get data for all.
        """
        if rows:
            rows = rows
        else:
            rows = range(self.GetNumberRows())
        cols = range(self.GetNumberCols())
        data = {}
        for row in rows:
            data[row] = {}
            for col in cols:
                col_name = self.GetColLabelValue(col)
                if verbose:
                    print(col_name, ":", self.GetCellValue(row, col))
                data[row][col_name] = self.GetCellValue(row, col)
        return data



class HugeMagicGrid(BaseMagicGrid):

    def __init__(self, parent, name, row_labels, col_labels, size=0):
        super(HugeMagicGrid, self).__init__(parent, name, row_labels, col_labels, size=0)
        # add table
        table = HugeTable(sys.stdout, len(row_labels), len(col_labels))
        self.table = table

        # The second parameter means that the grid is to take ownership of the
        # table and will destroy it when done.  Otherwise you would need to keep
        # a reference to it and call it's Destroy method later.
        self.SetTable(table, True)

        self.Bind(gridlib.EVT_GRID_CELL_RIGHT_CLICK, self.OnRightDown)
        #self.InitUI()

    def InitUI(self):
        self.size_grid()

    def add_items(self, dataframe, hide_cols=()):
        # replace "None" values with ""
        dataframe = dataframe.fillna("")
        # remove any columns that shouldn't be shown
        for col in hide_cols:
            if col in dataframe.columns:
                del dataframe[col]
        self.table.dataframe = dataframe

    def save_items(self):
        """
        Return dataframe so that a contribution can update
        """
        return self.table.dataframe

    def SetColumnValues(self, col, data):
        """
        Set a whole column worth of values
        in self.table
        """
        self.table.SetColumnValues(col, data)

    def add_col(self, label):
        """
        Update table dataframe, and append a new column

        Parameters
        ----------
        label : str

        Returns
        ---------
        last_col: int
            index column number of added col
        """
        self.table.dataframe[label] = ''
        self.AppendCols(1, updateLabels=False)
        last_col = self.table.GetNumberCols() - 1
        self.SetColLabelValue(last_col, label)
        self.col_labels.append(label)
        self.size_grid()
        return last_col

    # this currently fails with segfault
    def remove_col(self, col_num):
        """
        update table dataframe, and remove a column.
        resize grid to display correctly
        """
        label_value = self.GetColLabelValue(col_num).strip('**').strip('^^')
        self.col_labels.remove(label_value)
        del self.table.dataframe[label_value]
        result = self.DeleteCols(pos=col_num, numCols=1, updateLabels=True)
        self.size_grid()
        return result


    def OnRightDown(self, event):
        print(self.GetSelectedRows())


class MyCustomRenderer(gridlib.GridCellRenderer):
    def __init__(self, color='MEDIUM VIOLET RED'):
        gridlib.GridCellRenderer.__init__(self)
        self.color = color

    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        #print 'grid', grid
        #print 'attr', attr
        #print 'dc', dc
        #print 'rect', rect
        #print 'row', row
        #print 'col', col
        #print 'isSelected', isSelected
        #dc.SetPen(wx.TRANSPARENT_PEN)
        #  do it like this for filling in background:
        dc.SetBackgroundMode(wx.SOLID)
        dc.SetBrush(wx.Brush(self.color, wx.BDIAGONAL_HATCH))
        # or do it like this for highlighting the cell:
        #dc.SetPen(wx.Pen(self.color, 5, wx.SOLID))
        dc.DrawRectangle(rect)

        dc.SetBackgroundMode(wx.TRANSPARENT)
        dc.SetFont(attr.GetFont())

        text = grid.GetCellValue(row, col)
        #colors = ["RED", "WHITE", "SKY BLUE"]
        x = rect.x + 1
        y = rect.y + 1

        for ch in text:
            dc.SetTextForeground("BLACK")
            dc.DrawText(ch, x, y)
            w, h = dc.GetTextExtent(ch)
            x = x + w
            if x > rect.right - 5:
                break


    def GetBestSize(self, grid, attr, dc, row, col):
        text = grid.GetCellValue(row, col)
        dc.SetFont(attr.GetFont())
        w, h = dc.GetTextExtent(text)
        return wx.Size(w, h)


    def Clone(self):
        return MyCustomRenderer()


class MyColLabelRenderer(gridlabelrenderer.GridLabelRenderer):
    def __init__(self, bgcolor):
        self._bgcolor = bgcolor

    def Draw(self, grid, dc, rect, col):
        dc.SetBrush(wx.Brush(self._bgcolor))
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        #dc.SetPen(wx.TRANSPARENT_PEN)
        dc.SetPen(wx.Pen('blue', 5, wx.DOT_DASH))
        dc.DrawRectangle(rect)
        hAlign, vAlign = grid.GetColLabelAlignment()
        text = grid.GetColLabelValue(col)
        self.DrawBorder(grid, dc, rect)
        self.DrawText(grid, dc, rect, text, hAlign, vAlign)

class MyRowLabelRenderer(gridlabelrenderer.GridLabelRenderer):
    def __init__(self, bgcolor):
        self._bgcolor = bgcolor

    def Draw(self, grid, dc, rect, row):
        #dc.SetBrush(wx.Brush(self._bgcolor))
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.SetPen(wx.Pen('blue', 5, wx.SHORT_DASH))
        #dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRectangle(rect)
        hAlign, vAlign = grid.GetRowLabelAlignment()
        text = grid.GetRowLabelValue(row)
        self.DrawBorder(grid, dc, rect)
        self.DrawText(grid, dc, rect, text, hAlign, vAlign)

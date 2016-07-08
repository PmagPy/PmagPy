import matplotlib
#matplotlib.use('WXAgg')
import wx
import wx.grid
import wx.lib.mixins.gridlabelrenderer as gridlabelrenderer
#import pdb

class MagicGrid(wx.grid.Grid, gridlabelrenderer.GridWithLabelRenderersMixin):
    """
    grid class
    """

    def __init__(self, parent, name, row_labels, col_labels, row_items=None, size=0, double=None):
        # row_items is an optional list of Pmag_objects
        self.name = name
        self.row_items = []
        if row_items:
            self.row_items = row_items
        else:
            self.row_items = ['' for label in row_labels]
        # list of headers that are different in the er_XXX table vs. the pmag_XXX table
        if not double:
            self.double = []
        else:
            self.double = double
        self.changes = None
        self.row_labels = sorted(row_labels)
        self.col_labels = col_labels
        if not size:
            super(MagicGrid, self).__init__(parent, -1, name=name)
        if size:
            super(MagicGrid, self).__init__(parent, -1, name=name, size=size)
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
        # prevent horizontal scrollbar from showing up
        # this doesn't work with all versions of wx
        # so skip it if it's an older version
        try:
            self.ShowScrollbars(wx.SHOW_SB_NEVER, wx.SHOW_SB_DEFAULT)
        except AttributeError:
            pass
        return data


    def add_items(self, items_list, incl_pmag=True, incl_parents=True):
        """
        Add items and/or update existing items in grid
        """
        num_rows = self.GetNumberRows()
        current_grid_rows = [self.GetCellValue(num, 0) for num in xrange(num_rows)]
        er_data = {item.name: item.er_data for item in items_list}
        pmag_data = {item.name: item.pmag_data for item in items_list}
        items_list = sorted(items_list, key=lambda item: item.name)
        for item in items_list[:]:
            if item.name in current_grid_rows:
                pass
            else:
                self.add_row(item.name, item)
        self.add_data(er_data)#, pmag=False)
        if incl_pmag:
            self.add_data(pmag_data, pmag=True)
        if incl_parents:
            self.add_parents()
        
        
    def add_data(self, data_dict, pmag=False):
        # requires dict in this this format:
        # {spec_name: {}, spec2_name: {}}
        for num, row in enumerate(self.row_labels):
            if row:
                for n, col in enumerate(self.col_labels[1:]):
                    value = ''
                    ## catch pmag double codes
                    # in specimen, sample, and site grids,
                    # if we have a column name like 'magic_method_codes++'
                    # we need to strip the '++'
                    if '++' in col:
                        if pmag:
                            col_name = col[:-2]
                            if col_name in data_dict[row].keys():
                                value = data_dict[row][col_name]
                    # in pmag_results, magic_method_codes won't have '++'
                    # so we have to handle it separately
                    elif col == 'magic_method_codes' and pmag and self.name == 'result':
                        value = data_dict[row]['magic_method_codes']
                    # if we're doing pmag data, don't fill in magic_method_codes
                    # (for pmag we use 'magic_method_codes++' and skip plain magic_method_codes
                    elif col in self.double and pmag:
                        continue
                    elif col in data_dict[row].keys():
                        value = data_dict[row][col]
                        # set defaults
                        if col == 'er_citation_names':
                            if value == 'This study':
                                current_val = self.GetCellValue(num, n+1).strip()
                                if current_val:
                                    value = current_val
                                else:
                                    value = "This study"
                    else:
                        value = ''
                    if value:
                        self.SetCellValue(num, n+1, str(value))

    def add_parents(self, col_num=1):
        if self.parent_type and self.row_items:
            for num, row in enumerate(self.row_items):
                if row:
                    parent = row.get_parent()
                    if parent:
                        self.SetCellValue(num, col_num, parent.name)
                

    def size_grid(self, event=None):
        self.AutoSizeColumns(True)
        for col in xrange(len(self.col_labels)):
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
        data_obj = wx.TextDataObject()
        col = self.GetGridCursorCol()
        row = self.GetGridCursorRow()
        num_cols = self.GetNumberCols()

        if wx.TheClipboard.Open():
            wx.TheClipboard.GetData(data_obj)
            text = data_obj.GetText()
            # if text ends with a newline, strip that away
            if text.endswith('\n'):
                text = text[:-1]
            if text.endswith('\r'):
                text = text[:-1]
            # find newline character delimiter
            if '\r\n' in text:
                newline_char = '\r\n'
            elif '\r' in text:
                newline_char = '\r'
            elif '\n' in text:
                newline_char = '\n'
            else:
                newline_char = '\n'
            # split text and write it to the appropriate cells
            if newline_char in text or '\t' in text:
                # split text into a list of row data
                text_list = text.split(newline_char)
                num_rows = self.GetNumberRows()
                for text_row in text_list:
                    # add an extra row if needed
                    if row > num_rows - 1:
                        self.add_row()
                        num_rows += 1
                    # split row data into cols
                    if text_row.endswith('\t'):
                        text_row = text_row[:-1]
                    if '\t' in text_row:
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
        label_value = self.GetColLabelValue(col_num).strip('**')
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
        for col in xrange(self.GetNumberCols()):
            label = self.GetColLabelValue(col)
            if '**' in label:
                self.SetColLabelValue(col, label.strip('**'))
                cols_with_stars.append(col)
        return cols_with_stars

    def paint_invalid_cells(self, warn_dict):
        """
        """
        def highlight(problem_type, item, row_ind, cell_color):
            """
            """
            col_ind = None
            for col_name in warn_dict[item][problem_type]:
                if col_name in ('er_location_name', 'er_site_name', 'er_sample_name'):
                    continue
                if col_name in ('lithology', 'type', 'class'):
                    dtype = self.GetColLabelValue(0)
                    dtype = dtype[3:-5]
                    col_name = dtype + "_" + col_name
                # in result grid, magic_method_codes doesn't have ++
                stripped_name = col_name.strip('++')
                if stripped_name in self.double:
                    if stripped_name == 'magic_method_codes' and self.name not in ['age', 'result']:
                        col_name = 'magic_method_codes++'
                    elif stripped_name == 'magic_method_codes' and self.name in ['age', 'result']:
                        pass
                    else:
                        continue
                col_ind = self.col_labels.index(col_name)
                self.SetColLabelRenderer(col_ind, MyColLabelRenderer('#1101e0'))
                self.SetCellRenderer(row_ind, col_ind, MyCustomRenderer(cell_color))
                
        def highlight_parent(item, row_ind, cell_color):
            parent_type = self.parent_type
            parent_label = 'er_' + parent_type + '_name'
            col_ind = self.col_labels.index(parent_label)
            self.SetColLabelRenderer(col_ind, MyColLabelRenderer('#1101e0'))
            self.SetCellRenderer(row_ind, col_ind, MyCustomRenderer(cell_color))

        def highlight_child(item, row_ind, cell_color):
            ancestry = ['specimen', 'sample', 'site', 'location']
            ind = ancestry.index(self.parent_type)
            try:
                child_type = ancestry[ind-2]
            except ValueError:
                return
            child_label = 'er_' + child_type + '_name'
            col_ind = self.col_labels.index(child_label)
            self.SetColLabelRenderer(col_ind, MyColLabelRenderer('#1101e0'))
            self.SetCellRenderer(row_ind, col_ind, MyCustomRenderer(cell_color))

        def highlight_names(problem, row_ind, cell_color):
            col_ind = self.col_labels.index('er_' + problem + '_names')
            self.SetColLabelRenderer(col_ind, MyColLabelRenderer('#1101e0'))
            self.SetCellRenderer(row_ind, col_ind, MyCustomRenderer(cell_color))

        # begin main function
        grid_names = self.row_labels
        col_labels = self.col_labels

        for item in warn_dict:
            item_name = str(item)
            try:
                row_ind = grid_names.index(item_name)
            except ValueError:
                continue
            self.SetRowLabelRenderer(row_ind, MyRowLabelRenderer('#1101e0'))
            for problem in warn_dict[item]:
                if problem in ('missing_data'):
                    highlight('missing_data', item, row_ind, 'MEDIUM VIOLET RED')
                elif problem in ('number_fail'):
                    highlight('number_fail', item, row_ind, 'blue')
                elif problem in ('parent'):
                    highlight_parent(item, row_ind, 'green')
                elif problem in ('invalid_col'):
                    highlight('invalid_col', item, row_ind, 'LIGHT GREY')
                elif problem in ('child'):
                    # this will never work.....
                    highlight_child(item, row_ind, 'GOLDENROD')
                elif problem in ('type'):
                    pass
                elif problem in ('specimen', 'sample', 'site', 'location'):
                    highlight_names(problem, row_ind, 'purple')
                elif problem in 'coordinates':
                    highlight('coordinates', item, row_ind, 'GOLDENROD')
                elif problem in 'vocab_problem':
                    highlight('vocab_problem', item, row_ind, 'WHITE')
                else:
                    print 'other problem', problem
        #  looks like we can do tooltips over cells using techniques in
        #  simple_examples/highlight_grid and simple_examples/tooltip_grid
        #  but these only work with brew python (wxPython version)
        #  don't know when Canopy will become more up to date : (

                        


class MyCustomRenderer(wx.grid.PyGridCellRenderer):
    def __init__(self, color='MEDIUM VIOLET RED'):
        wx.grid.PyGridCellRenderer.__init__(self)
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
        dc.DrawRectangleRect(rect)
        
        
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
        dc.DrawRectangleRect(rect)
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
        dc.DrawRectangleRect(rect)
        hAlign, vAlign = grid.GetRowLabelAlignment()
        text = grid.GetRowLabelValue(row)
        self.DrawBorder(grid, dc, rect)
        self.DrawText(grid, dc, rect, text, hAlign, vAlign)


#!/usr/bin/env python

"""
provides all the functionality for the drop-down controlled vocabulary menus
used in MagIC grids
"""
# pylint: disable=W0612,C0111,C0301

import wx
from dialogs import magic_grid3


class Menus(object):
    """
    Drop-down controlled vocabulary menus for wxPython grid
    """
    def __init__(self, data_type, contribution, grid):
        """
        take: data_type (string), MagIC contribution,
        & grid (grid object)
        """
        self.contribution = contribution

        self.data_type = data_type
        if self.data_type in self.contribution.tables:
            self.magic_dataframe = self.contribution.tables[self.data_type]
        else:
            self.magic_dataframe = None
        if self.data_type == 'ages':
            parent_ind, parent_table, self.parent_type = None, None, None
        elif self.data_type == 'orient':
            pass
        else:
            parent_ind = self.contribution.ancestry.index(self.data_type)
            parent_table, self.parent_type = self.contribution.get_table_name(parent_ind+1)

        self.grid = grid
        self.huge_grid = True if isinstance(self.grid, magic_grid3.HugeMagicGrid) else False
        self.window = grid.Parent  # parent window in which grid resides
        #self.headers = headers
        self.selected_col = None
        self.selection = [] # [(row, col), (row, col)], sequentially down a column
        self.dispersed_selection = [] # [(row, col), (row, col)], not sequential
        self.col_color = None
        self.colon_delimited_lst = ['geologic_types', 'geologic_classes',
                                    'lithologies', 'specimens', 'samples',
                                    'sites', 'locations', 'method_codes']
        self.InitUI()


    def InitUI(self):
        """
        Initialize interface for drop down menu
        """
        if self.data_type in ['orient', 'ages']:
            belongs_to = []
        else:
            parent_table_name = self.parent_type + "s"
            if parent_table_name in self.contribution.tables:
                belongs_to = sorted(self.contribution.tables[parent_table_name].df.index.unique())
            else:
                belongs_to = []

        self.choices = {}
        if self.data_type in ['specimens', 'samples', 'sites']:
            self.choices = {1: (belongs_to, False)}
        if self.data_type == 'orient':
            self.choices = {1: (['g', 'b'], False)}
        if self.data_type == 'ages':
            for level in ['specimen', 'sample', 'site', 'location']:
                if level in self.grid.col_labels:
                    level_names = []
                    if level + "s" in self.contribution.tables:
                        level_names = list(self.contribution.tables[level+"s"].df.index.unique())
                    num = self.grid.col_labels.index(level)
                    self.choices[num] = (level_names, False)
        # Bind left click to drop-down menu popping out
        self.grid.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK,
                       lambda event: self.on_left_click(event, self.grid, self.choices))

        cols = self.grid.GetNumberCols()
        col_labels = [self.grid.GetColLabelValue(col) for col in range(cols)]

        # check if any additional columns have controlled vocabularies
        # if so, get the vocabulary list
        for col_number, label in enumerate(col_labels):
            self.add_drop_down(col_number, label)

    def EndUI(self):
        """
        prevent drop-down menu from popping up
        """
        self.grid.Unbind(wx.grid.EVT_GRID_CELL_LEFT_CLICK)


    def add_drop_down(self, col_number, col_label):
        """
        Add a correctly formatted drop-down-menu for given col_label,
        if required or suggested.
        Otherwise do nothing.

        Parameters
        ----------
        col_number : int
                grid position at which to add a drop down menu
        col_label : str
                column name
        """
        if col_label.endswith('**') or col_label.endswith('^^'):
            col_label = col_label[:-2]
        # add drop-down for experiments
        if col_label == "experiments":
            if 'measurements' in self.contribution.tables:
                meas_table = self.contribution.tables['measurements'].df
                if 'experiment' in meas_table.columns:
                    exps = meas_table['experiment'].unique()
                    self.choices[col_number] = (sorted(exps), False)
                    self.grid.SetColLabelValue(col_number, col_label + "**")
            return
        #
        if col_label == 'method_codes':
            self.add_method_drop_down(col_number, col_label)
        elif col_label == 'magic_method_codes':
            self.add_method_drop_down(col_number, 'method_codes')
        elif col_label in ['specimens', 'samples', 'sites', 'locations']:
            if col_label in self.contribution.tables:
                item_df = self.contribution.tables[col_label].df
                item_names = item_df.index.unique() #[col_label[:-1]].unique()
                self.choices[col_number] = (sorted(item_names), False)
        elif col_label in ['specimen', 'sample', 'site', 'location']:
            if col_label + "s" in self.contribution.tables:
                item_df = self.contribution.tables[col_label + "s"].df
                item_names = item_df.index.unique() #[col_label[:-1]].unique()
                self.choices[col_number] = (sorted(item_names), False)
        # add vocabularies
        if col_label in self.contribution.vocab.suggested:
            typ = 'suggested'
        elif col_label in self.contribution.vocab.vocabularies:
            typ = 'controlled'
        else:
            return

        # add menu, if not already set
        if col_number not in list(self.choices.keys()):
            if typ == 'suggested':
                self.grid.SetColLabelValue(col_number, col_label + "^^")
                controlled_vocabulary = self.contribution.vocab.suggested[col_label]
            else:
                self.grid.SetColLabelValue(col_number, col_label + "**")
                controlled_vocabulary = self.contribution.vocab.vocabularies[col_label]
            #
            stripped_list = []
            for item in controlled_vocabulary:
                try:
                    stripped_list.append(str(item))
                except UnicodeEncodeError:
                    # skips items with non ASCII characters
                    pass

            if len(stripped_list) > 100:
            # split out the list alphabetically, into a dict of lists {'A': ['alpha', 'artist'], 'B': ['beta', 'beggar']...}
                dictionary = {}
                for item in stripped_list:
                    letter = item[0].upper()
                    if letter not in list(dictionary.keys()):
                        dictionary[letter] = []
                    dictionary[letter].append(item)
                stripped_list = dictionary

            two_tiered = True if isinstance(stripped_list, dict) else False
            self.choices[col_number] = (stripped_list, two_tiered)
        return

    def add_method_drop_down(self, col_number, col_label):
        """
        Add drop-down-menu options for magic_method_codes columns
        """
        if self.data_type == 'ages':
            method_list = self.contribution.vocab.age_methods
        else:
            method_list = self.contribution.vocab.methods
        self.choices[col_number] = (method_list, True)

    def on_label_click(self, event):
        """
        When a grid column or row label is clicked,
        provide the appropriate behavior.
        If there is a drop-down menu, it should pop up
        for assigning to the entire column.
        Otherwise user should be able to edit the entire column
        by entering text.
        If Menus are attached to a HugeMagicGrid, don't try to do
        highlighting of a column, it doesn't work.
        """
        col = event.GetCol()
        color = self.grid.GetCellBackgroundColour(0, col)
        if color != (191, 216, 216, 255): # light blue
            self.col_color = color
        if col not in (-1, 0):
            # if a new column was chosen without de-selecting the previous column, deselect the old selected_col
            if self.selected_col is not None and self.selected_col != col:
                col_label_value = self.grid.GetColLabelValue(self.selected_col)
                self.grid.SetColLabelValue(self.selected_col, col_label_value[:-10])
                if not self.huge_grid:
                    for row in range(self.grid.GetNumberRows()):
                        self.grid.SetCellBackgroundColour(row, self.selected_col, self.col_color)# 'white'
                self.grid.ForceRefresh()
            # deselect col if user is clicking on it a second time
            if col == self.selected_col:
                col_label_value = self.grid.GetColLabelValue(col)
                self.grid.SetColLabelValue(col, col_label_value[:-10])
                if not self.huge_grid:
                    for row in range(self.grid.GetNumberRows()):
                        self.grid.SetCellBackgroundColour(row, col, self.col_color) # 'white'
                self.grid.ForceRefresh()
                self.selected_col = None
            # otherwise, select (highlight) col
            else:
                self.selected_col = col
                col_label_value = self.grid.GetColLabelValue(col)
                self.grid.SetColLabelValue(col, col_label_value + " \nEDIT ALL")
                if not self.huge_grid:
                    for row in range(self.grid.GetNumberRows()):
                        self.grid.SetCellBackgroundColour(row, col, 'light blue')
                self.grid.ForceRefresh()
        has_dropdown = False
        if col in list(self.choices.keys()):
            has_dropdown = True

        # if the column has no drop-down list, allow user to edit all cells in the column through text entry
        if not has_dropdown and col != 0:
            if self.selected_col == col:
                col_label = self.grid.GetColLabelValue(col)
                if col_label.endswith(" \nEDIT ALL"):
                    col_label = col_label[:-10]
                default_value = self.grid.GetCellValue(0, col)
                data = None
                dialog = wx.TextEntryDialog(None, "Enter value for all cells in the column {}\nNote: this will overwrite any existing cell values".format(col_label_value), "Edit All", default_value, style=wx.OK|wx.CANCEL)
                dialog.Centre()
                if dialog.ShowModal() == wx.ID_OK:
                    data = dialog.GetValue()
                    # with HugeMagicGrid, you can add a new value to a column
                    # all at once
                    if self.huge_grid:
                        self.grid.SetColumnValues(col, str(data))
                        if self.grid.changes:
                            self.grid.changes.add(0)
                        else:
                            self.grid.changes = {0}
                    # with MagicGrid, you must add a new value
                    # one row at a time
                    else:
                        for row in range(self.grid.GetNumberRows()):
                            self.grid.SetCellValue(row, col, str(data))
                            if self.grid.changes:
                                self.grid.changes.add(row)
                            else:
                                self.grid.changes = {row}
                dialog.Destroy()
                # then deselect column
                col_label_value = self.grid.GetColLabelValue(col)
                self.grid.SetColLabelValue(col, col_label_value[:-10])
                if not self.huge_grid:
                    for row in range(self.grid.GetNumberRows()):
                        self.grid.SetCellBackgroundColour(row, col, self.col_color) # 'white'
                self.grid.ForceRefresh()
                self.selected_col = None


    def clean_up(self):#, grid):
        """
        de-select grid cols, refresh grid
        """
        if self.selected_col:
            col_label_value = self.grid.GetColLabelValue(self.selected_col)
            col_label_value = col_label_value.strip('\nEDIT ALL')
            self.grid.SetColLabelValue(self.selected_col, col_label_value)
            for row in range(self.grid.GetNumberRows()):
                self.grid.SetCellBackgroundColour(row, self.selected_col, 'white')
        self.selected_col = None
        self.grid.ForceRefresh()

    def on_left_click(self, event, grid, choices):
        """
        creates popup menu when user clicks on the column
        if that column is in the list of choices that get a drop-down menu.
        allows user to edit the column, but only from available values
        """
        row, col = event.GetRow(), event.GetCol()
        if col == 0 and self.grid.name != 'ages':
            default_val = self.grid.GetCellValue(row, col)
            msg = "Choose a new name for {}.\nThe new value will propagate throughout the contribution.".format(default_val)
            dia = wx.TextEntryDialog(self.grid, msg,
                                     "Rename {}".format(self.grid.name, default_val),
                                     default_val)
            res = dia.ShowModal()
            if res == wx.ID_OK:
                new_val = dia.GetValue()
                # update the contribution with new name
                self.contribution.rename_item(self.grid.name,
                                              default_val, new_val)
                # don't propagate changes if we are just assigning a new name
                # and not really renaming
                # (i.e., if a blank row was added then named)
                if default_val == '':
                    self.grid.SetCellValue(row, 0, new_val)
                    return

                # update the current grid with new name
                for row in range(self.grid.GetNumberRows()):
                    cell_value = self.grid.GetCellValue(row, 0)
                    if cell_value == default_val:
                        self.grid.SetCellValue(row, 0, new_val)
                    else:
                        continue
            return
        color = self.grid.GetCellBackgroundColour(event.GetRow(), event.GetCol())
        # allow user to cherry-pick cells for editing.
        # gets selection of meta key for mac, ctrl key for pc
        if event.ControlDown() or event.MetaDown():
            row, col = event.GetRow(), event.GetCol()
            if (row, col) not in self.dispersed_selection:
                self.dispersed_selection.append((row, col))
                self.grid.SetCellBackgroundColour(row, col, 'light blue')
            else:
                self.dispersed_selection.remove((row, col))
                self.grid.SetCellBackgroundColour(row, col, color)# 'white'
            self.grid.ForceRefresh()
            return
        if event.ShiftDown(): # allow user to highlight multiple consecutive cells in a column
            previous_col = self.grid.GetGridCursorCol()
            previous_row = self.grid.GetGridCursorRow()
            col = event.GetCol()
            row = event.GetRow()
            if col != previous_col:
                return
            else:
                if row > previous_row:
                    row_range = list(range(previous_row, row+1))
                else:
                    row_range = list(range(row, previous_row+1))
            for r in row_range:
                self.grid.SetCellBackgroundColour(r, col, 'light blue')
                self.selection.append((r, col))
            self.grid.ForceRefresh()
            return

        selection = False

        if self.dispersed_selection:
            is_dispersed = True
            selection = self.dispersed_selection

        if self.selection:
            is_dispersed = False
            selection = self.selection

        try:
            col = event.GetCol()
            row = event.GetRow()
        except AttributeError:
            row, col = selection[0][0], selection[0][1]

        self.grid.SetGridCursor(row, col)

        if col in list(choices.keys()): # column should have a pop-up menu
            menu = wx.Menu()
            two_tiered = choices[col][1]
            choices = choices[col][0]
            if not two_tiered: # menu is one tiered
                if 'CLEAR cell of all values' not in choices:
                    choices.insert(0, 'CLEAR cell of all values')
                for choice in choices:
                    if not choice:
                        choice = " " # prevents error if choice is an empty string
                    menuitem = menu.Append(wx.ID_ANY, str(choice))
                    self.window.Bind(wx.EVT_MENU, lambda event: self.on_select_menuitem(event, grid, row, col, selection), menuitem)
                self.show_menu(event, menu)
            else: # menu is two_tiered
                clear = menu.Append(-1, 'CLEAR cell of all values')
                self.window.Bind(wx.EVT_MENU, lambda event: self.on_select_menuitem(event, grid, row, col, selection), clear)
                for choice in sorted(choices.items()):
                    submenu = wx.Menu()
                    for item in choice[1]:
                        menuitem = submenu.Append(-1, str(item))
                        self.window.Bind(wx.EVT_MENU, lambda event: self.on_select_menuitem(event, grid, row, col, selection), menuitem)
                    menu.AppendMenu(-1, choice[0], submenu)
                self.show_menu(event, menu)

        if selection:
            # re-whiten the cells that were previously highlighted
            for row, col in selection:
                self.grid.SetCellBackgroundColour(row, col, self.col_color)
            self.dispersed_selection = []
            self.selection = []
            self.grid.ForceRefresh()


    def show_menu(self, event, menu):
        """
        Show drop-down menu
        """
        position = event.GetPosition()
        horizontal, vertical = position
        grid_horizontal, grid_vertical = self.grid.GetSize()
        if grid_vertical - vertical < 30 and self.grid.GetNumberRows() > 4:
            self.grid.PopupMenu(menu, (horizontal+20, 100))
        else:
            self.window.PopupMenu(menu)
        menu.Destroy()

    def update_drop_down_menu(self, grid, choices):
        """
        Update drop-down-menus with a new dict of options

        Parameters
        ----------
        grid : magic_grid3.MagicGrid
        choices : list or dict
            in format: {column_number: ([value1, value2, ...], two_tiered), ... }
        """
        self.window.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, lambda event: self.on_left_click(event, grid, choices), grid)
        self.choices = choices

    def on_select_menuitem(self, event, grid, row, col, selection):
        """
        sets value of selected cell to value selected from menu
        """
        if self.grid.changes:  # if user selects a menuitem, that is an edit
            self.grid.changes.add(row)
        else:
            self.grid.changes = {row}

        item_id = event.GetId()
        item = event.EventObject.FindItemById(item_id)
        label = item.Label
        cell_value = grid.GetCellValue(row, col)
        if str(label) == "CLEAR cell of all values":
            label = ""

        col_label = grid.GetColLabelValue(col).strip('\nEDIT ALL').strip('**').strip('^^')
        if col_label in self.colon_delimited_lst and label:
            if not label.lower() in cell_value.lower():
                label += (":" + cell_value).rstrip(':')
            else:
                label = cell_value

        if self.selected_col and self.selected_col == col:
            for row in range(self.grid.GetNumberRows()):
                grid.SetCellValue(row, col, label)
                if self.grid.changes:
                    self.grid.changes.add(row)
                else:
                    self.grid.changes = {row}

                #self.selected_col = None
        else:
            grid.SetCellValue(row, col, label)

        if selection:
            for cell in selection:
                row = cell[0]
                grid.SetCellValue(row, col, label)
            return

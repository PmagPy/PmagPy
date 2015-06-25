#!/usr/bin/env python

# pylint: disable=W0612,C0111,C0301

import wx
import pandas as pd
from controlled_vocabularies import vocabularies as vocab
import controlled_vocabularies as vocabulary


# this module will provide all the functionality for the drop-down controlled vocabulary menus


class Menus(object):
    """
    Drop-down controlled vocabulary menus for wxPython grid
    """
    def __init__(self, data_type, ErMagicCheck, grid, belongs_to):
        """
        take: data_type (string), ErMagicCheck (top level class object for ErMagic steps 1-6), grid (grid object), belongs_to (options for data object to belong to, i.e. locations for the site Menus)
        """
        self.data_type = data_type
        self.check = ErMagicCheck # check is top level class object for entire ErMagic steps 1-6
        self.grid = grid
        self.window = grid.Parent # parent window in which grid resides
        self.belongs_to = belongs_to
        #self.headers = headers
        self.selected_col = None
        self.selection = [] # [(row, col), (row, col)], sequentially down a column
        self.dispersed_selection = [] # [(row, col), (row, col)], not sequential
        self.col_color = None
        self.InitUI()

    def InitUI(self):
        belongs_to = self.belongs_to
        if self.data_type == 'specimen':
            self.choices = {1: (belongs_to, False)}
        if self.data_type == 'sample' or self.data_type == 'site':
            self.choices = {1: (belongs_to, False), 3: (vocab['class'], False), 4: (vocab['lithology'], True), 5: (vocab['type'], False)}
            if self.data_type == 'sample':
                map(lambda (x, y): self.grid.SetColLabelValue(x, y), [(3, 'sample_class**'), (4, 'sample_lithology**'), (5, 'sample_type**')])
            elif self.data_type == 'site':
                map(lambda (x, y): self.grid.SetColLabelValue(x, y), [(3, 'site_class**'), (4, 'site_lithology**'), (5, 'site_type**')])
        if self.data_type == 'site':
            self.choices[6] = (vocab['site_definition'], False)
            self.grid.SetColLabelValue(6, 'site_definition**')
        if self.data_type == 'location':
            self.choices = {1: (vocab['location_type'], False)}
            self.grid.SetColLabelValue(1, 'location_type**')
        if self.data_type == 'age':
            self.choices = {3: (vocabulary.geochronology_method_codes, False), 5: (vocab['age_unit'], False)}
            map(lambda (x, y): self.grid.SetColLabelValue(x, y), [(3, 'magic_method_codes**'), (5, 'age_unit**')])
        if self.data_type == 'orient':
            self.choices = {1: (['g', 'b'], False)}
        self.window.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, lambda event: self.on_left_click(event, self.grid, self.choices), self.grid)
        ## now doing the binding below in pmag_er_magic_dialogs:
        #self.window.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.on_label_click, self.grid)

        #
        cols = self.grid.GetNumberCols()
        col_labels = [self.grid.GetColLabelValue(col) for col in range(cols)]

        # check if any additional columns have associated controlled vocabularies
        # if so, get the vocabulary list from the MagIC API
        for col_number, label in enumerate(col_labels):
            if label in vocabulary.possible_vocabularies:
                if col_number not in self.choices.keys(): # if not already assigned above
                    self.grid.SetColLabelValue(col_number, label + "**") # mark it as using a controlled vocabulary
                    url = 'http://api.earthref.org/MAGIC/vocabularies/{}.json'.format(label)
                    controlled_vocabulary = pd.io.json.read_json(url)
                    stripped_list = []
                    for item in controlled_vocabulary[label][0]:
                        try:
                            stripped_list.append(str(item['item']))
                        except UnicodeEncodeError:
                            # skips items with non ASCII characters
                            pass
                    #stripped_list = [item['item'] for item in controlled_vocabulary[label][0]]
                    
                    if len(stripped_list) > 100:
                    # split out the list alphabetically, into a dict of lists {'A': ['alpha', 'artist'], 'B': ['beta', 'beggar']...}
                        dictionary = {}
                        for item in stripped_list:
                            letter = item[0].upper()
                            if letter not in dictionary.keys():
                                dictionary[letter] = []
                            dictionary[letter].append(item)

                        stripped_list = dictionary

                    two_tiered = True if isinstance(stripped_list, dict) else False
                    self.choices[col_number] = (stripped_list, two_tiered)


    def on_label_click(self, event):
        col = event.GetCol()
        color = self.grid.GetCellBackgroundColour(0, col)
        if color != (191, 216, 216, 255): # light blue
            self.col_color = color
        if col not in (-1, 0):
            # if a new column was chosen without de-selecting the previous column, deselect the old selected_col
            if self.selected_col != None and self.selected_col != col:
                col_label_value = self.grid.GetColLabelValue(self.selected_col)
                self.grid.SetColLabelValue(self.selected_col, col_label_value[:-10])
                for row in range(self.grid.GetNumberRows()):
                    self.grid.SetCellBackgroundColour(row, self.selected_col, self.col_color)# 'white'
                self.grid.ForceRefresh()
            # deselect col if user is clicking on it a second time
            if col == self.selected_col:
                col_label_value = self.grid.GetColLabelValue(col)
                self.grid.SetColLabelValue(col, col_label_value[:-10])
                for row in range(self.grid.GetNumberRows()):
                    self.grid.SetCellBackgroundColour(row, col, self.col_color) # 'white'
                self.grid.ForceRefresh()
                self.selected_col = None
            # otherwise, select (highlight) col
            else:
                self.selected_col = col
                col_label_value = self.grid.GetColLabelValue(col)
                self.grid.SetColLabelValue(col, col_label_value + " \nEDIT ALL")
                for row in range(self.grid.GetNumberRows()):
                    self.grid.SetCellBackgroundColour(row, col, 'light blue')
                self.grid.ForceRefresh()
        #has_dropdown = ((col == 2 and self.data_type is 'specimen') or (col in range(2, 6) and self.data_type in ['site', 'sample']) or (col in (3, 5) and self.data_type == 'age') or (col == 6 and self.data_type == 'site') or (col == 1 and self.data_type in ['location']))
        has_dropdown = False
        if col in self.choices.keys():
            has_dropdown = True

        # if the column has no drop-down list, allow user to edit all cells in the column through text entry
        if not has_dropdown and col != 0:
            if self.selected_col == col:
                default_value = self.grid.GetCellValue(0, col)
                data = None
                dialog = wx.TextEntryDialog(None, "Enter value for all cells in the column\nNote: this will overwrite any existing cell values", "Edit All", default_value, style=wx.OK|wx.CANCEL)
                dialog.Centre()
                if dialog.ShowModal() == wx.ID_OK:
                    data = dialog.GetValue()
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
            self.grid.SetColLabelValue(self.selected_col, col_label_value[:-10])
            for row in range(self.grid.GetNumberRows()):
                self.grid.SetCellBackgroundColour(row, self.selected_col, 'white')
        self.grid.ForceRefresh()


    def on_left_click(self, event, grid, choices):
        """
        creates popup menu when user clicks on the column
        if that column is in the list of choices that get a drop-down menu.
        allows user to edit the column, but only from available values
        """
        color = self.grid.GetCellBackgroundColour(event.GetRow(), event.GetCol())
        if event.CmdDown(): # allow user to cherry-pick cells for editing.  gets selection of meta key for mac, ctrl key for pc
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
                    row_range = range(previous_row, row+1)
                else:
                    row_range = range(row, previous_row+1)
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

        if col in choices.keys(): # column should have a pop-up menu
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
                self.window.PopupMenu(menu)
                menu.Destroy()
            else: # menu is two_tiered
                clear = menu.Append(-1, 'CLEAR cell of all values')
                self.window.Bind(wx.EVT_MENU, lambda event: self.on_select_menuitem(event, grid, row, col, selection), clear)
                for choice in sorted(choices.items()):
                    submenu = wx.Menu()
                    for item in choice[1]:
                        menuitem = submenu.Append(-1, str(item))
                        self.window.Bind(wx.EVT_MENU, lambda event: self.on_select_menuitem(event, grid, row, col, selection), menuitem)
                    menu.AppendMenu(-1, choice[0], submenu)
                self.window.PopupMenu(menu)
                menu.Destroy()

        if selection:
            # re-whiten the cells that were previously highlighted
            for row, col in selection:
                self.grid.SetCellBackgroundColour(row, col, self.col_color)
            self.dispersed_selection = []
            self.selection = []
            self.grid.ForceRefresh()


    def update_drop_down_menu(self, grid, choices):
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
        elif (col in range(3, 6) and self.data_type in ['site', 'sample']) or (col == 3 and self.data_type == 'age'):
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

#!/usr/bin/env python

# pylint: disable=W0612,C0111,C0301

import wx
import pandas as pd
from pmagpy.controlled_vocabularies2 import vocab


# this module will provide all the functionality for the drop-down controlled vocabulary menus


class Menus(object):
    """
    Drop-down controlled vocabulary menus for wxPython grid
    """
    def __init__(self, data_type, ErMagicCheck, grid, belongs_to):
        """
        take: data_type (string), ErMagicCheck (top level class object for ErMagic steps 1-6),
        grid (grid object), belongs_to (list of options for data object to belong to, i.e. locations for the site Menus)
        """
        # if controlled vocabularies haven't already been grabbed from earthref
        # do so now
        if not any(vocab.vocabularies):
            vocab.get_all_vocabulary()

        self.data_type = data_type
        self.check = ErMagicCheck # check is top level class object for entire ErMagic steps 1-6
        self.grid = grid
        self.window = grid.Parent # parent window in which grid resides
        self.belongs_to = []
        # belongs_to can either be a list of strings OR a list of Pmag_objects
        if belongs_to:
            for item in belongs_to:
                try:
                    self.belongs_to.append(item.name)
                except AttributeError:
                    self.belongs_to.append(item)
        #self.headers = headers
        self.selected_col = None
        self.selection = [] # [(row, col), (row, col)], sequentially down a column
        self.dispersed_selection = [] # [(row, col), (row, col)], not sequential
        self.col_color = None
        self.colon_delimited_lst = ['specimen_type', 'specimen_class', 'specimen_lithology',
                                    'sample_type', 'sample_class', 'sample_lithology',
                                    'site_type', 'site_class', 'site_lithology',
                                    'er_specimen_names', 'er_sample_names', 'er_site_names',
                                    'er_location_names', 'magic_method_codes', 'magic_method_codes++']
        self.InitUI()

    def InitUI(self):
        belongs_to = self.belongs_to
        self.choices = {}
        if self.data_type == 'specimen':
            self.choices = {1: (belongs_to, False), 3: (vocab.vocabularies['class'], False), 4: (vocab.vocabularies['lithology'], True), 5: (vocab.vocabularies['type'], False)}
        if self.data_type == 'sample' or self.data_type == 'site':
            self.choices = {1: (belongs_to, False), 3: (vocab.vocabularies['class'], False), 4: (vocab.vocabularies['lithology'], True), 5: (vocab.vocabularies['type'], False)}
        if self.data_type in ['specimen', 'sample', 'site']:
            list(map(lambda x_y: self.grid.SetColLabelValue(x_y[0], x_y[1]), [(3, '{}_class**'.format(self.data_type)), (4, '{}_lithology**'.format(self.data_type)), (5, '{}_type**'.format(self.data_type))]))
        if self.data_type == 'site':
            self.choices[6] = (vocab.vocabularies['site_definition'], False)
            self.grid.SetColLabelValue(6, 'site_definition**')
        if self.data_type == 'location':
            self.choices = {2: (vocab.vocabularies['location_type'], False)}
            self.grid.SetColLabelValue(2, 'location_type**')
        if self.data_type == 'age':
            #self.choices = {2: (vocab.vocabulariesulary.age_methods, False), 3: (vocab['age_unit'], False)}
            self.choices = {3: (vocab.vocabularies['age_unit'], False)}
            #map(lambda (x, y): self.grid.SetColLabelValue(x, y), [(2, 'magic_method_codes**'), (3, 'age_unit**')])
            list(map(lambda x_y1: self.grid.SetColLabelValue(x_y1[0], x_y1[1]), [(3, 'age_unit**')]))
            for row in range(self.grid.GetNumberRows()):
                self.grid.SetReadOnly(row, 0)
        if self.data_type == 'orient':
            self.choices = {1: (['g', 'b'], False)}
        if self.data_type == 'result':
            self.choices = {}

        self.window.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, lambda event: self.on_left_click(event, self.grid, self.choices), self.grid)

        #
        cols = self.grid.GetNumberCols()
        col_labels = [self.grid.GetColLabelValue(col) for col in range(cols)]

        # check if any additional columns have associated controlled vocabularies
        # if so, get the vocabulary list from the MagIC API
        for col_number, label in enumerate(col_labels):
            self.add_drop_down(col_number, label)


    def add_drop_down(self, col_number, col_label):
        """
        Add a correctly formatted drop-down-menu for given col_label, if required.
        Otherwise do nothing.
        """
        if col_label in ['magic_method_codes', 'magic_method_codes++']:
            self.add_method_drop_down(col_number, col_label)
        if col_label in vocab.possible_vocabularies:
            if col_number not in list(self.choices.keys()): # if not already assigned above
                self.grid.SetColLabelValue(col_number, col_label + "**") # mark it as using a controlled vocabulary
                url = 'https://api.earthref.org/MagIC/vocabularies/{}.json'.format(col_label)
                controlled_vocabulary = pd.io.json.read_json(url)
                stripped_list = []
                for item in controlled_vocabulary[col_label][0]:
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
                        if letter not in list(dictionary.keys()):
                            dictionary[letter] = []
                        dictionary[letter].append(item)

                    stripped_list = dictionary

                two_tiered = True if isinstance(stripped_list, dict) else False
                self.choices[col_number] = (stripped_list, two_tiered)


    def add_method_drop_down(self, col_number, col_label):
        """
        Add drop-down-menu options for magic_method_codes columns
        """
        if self.data_type == 'age':
            method_list = vocab.age_methods
        elif '++' in col_label:
            method_list = vocab.pmag_methods
        elif self.data_type == 'result':
            method_list = vocab.pmag_methods
        else:
            method_list = vocab.er_methods
        self.choices[col_number] = (method_list, True)

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
        has_dropdown = False
        if col in list(self.choices.keys()):
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
            col_label_value = col_label_value.strip('\nEDIT ALL')
            self.grid.SetColLabelValue(self.selected_col, col_label_value)
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
        # allow user to cherry-pick cells for editing.  gets selection of meta key for mac, ctrl key for pc
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
        position = event.GetPosition()
        horizontal, vertical = position
        grid_horizontal, grid_vertical = self.grid.GetSize()
        if grid_vertical - vertical < 30 and self.grid.GetNumberRows() > 4:
            self.grid.PopupMenu(menu, (horizontal+20, 100))
        else:
            self.window.PopupMenu(menu)
        menu.Destroy()

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

        col_label = grid.GetColLabelValue(col).strip('\nEDIT ALL').strip('**')
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

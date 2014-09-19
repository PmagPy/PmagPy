#!/usr/bin/env python

import wx
import controlled_vocabularies as vocab

# this module will provide all the functionality for the drop-down controlled vocabulary menus
# ideally, these classes should take in a grid item and then provide the functionality


class Menus():

    def __init__(self, data_type, check, grid, belongs_to, headers=['site_class', 'site_lithology', 'site_type', 'site_definition']):
        """take: data_type (string), check (top level class object for ErMagic steps 1-6), grid (grid object), belongs_to (options for data object to belong to, i.e. locations for the site Menus)"""
        self.data_type = data_type
        self.check = check # check is top level class object for entire ErMagic steps 1-6
        self.grid = grid
        self.window = grid.Parent
        self.belongs_to = belongs_to
        self.headers = headers
        self.InitUI()

    def InitUI(self):
        belongs_to = self.belongs_to
        print "self.data_type", self.data_type
        if self.data_type == 'sample' or self.data_type == 'site':
            choices = {2: belongs_to, 3: vocab.site_class, 4: vocab.site_lithology, 5: vocab.site_type, 6: vocab.site_definition}
        self.window.Bind(wx.grid.EVT_GRID_SELECT_CELL, lambda event: self.on_left_click(event, self.grid, choices), self.grid) 

    def on_left_click(self, event, grid, choices):
        """creates popup menu when user clicks on the third column
        allows user to edit third column, but only from available values"""
        col = event.GetCol()
        if col in range(2, 7):
            row = event.GetRow()
            menu = wx.Menu()
            choices = sorted(set(choices[col]))
            if col in range(3, 6):
                choices.insert(0, 'CLEAR cell of all values')
            for choice in choices:
                if not choice: choice = " " # prevents error if choice is an empty string
                menuitem = menu.Append(wx.ID_ANY, choice)
                self.window.Bind(wx.EVT_MENU, lambda event: self.on_select_menuitem(event, grid, row, col), menuitem)
            self.window.PopupMenu(menu)
            menu.Destroy()

    def on_select_menuitem(self, event, grid, row, col):
        """sets value of selected cell to value selected from menu
        (doesn't require column info because only third column works this way"""

        self.check.changes = True # if user selects a menuitem, that is an edit
        item_id =  event.GetId()
        item = event.EventObject.FindItemById(item_id)
        label = item.Label
        cell_value = grid.GetCellValue(row, col)
        if col in range(3, 6):
            if str(label) == "CLEAR cell of all values":
                print "clear"
                label = ""
            elif not label in cell_value:
                label += (":" + cell_value).rstrip(':')
            else:
                label = cell_value
        grid.SetCellValue(row, col, label)




    # double clicking brings up cell editor
    # single click brings up drop-down menu
    # users should be able to select a bunch of cells and edit them all at once



def on_edit_grid(self, event):
    """sets self.changes to true when user edits the grid"""
    self.changes = True

def on_left_click(self, event, grid, choices):
    """creates popup menu when user clicks on the third column
    allows user to edit third column, but only from available values"""
    row, col = event.GetRow(), event.GetCol()
    if col == 2:
        menu = wx.Menu()
        for choice in sorted(set(choices)): # NOT OPTIMAL to run this every time
            if not choice: choice = " " # prevents error if choice is an empty string
            menuitem = menu.Append(wx.ID_ANY, choice)
            self.Bind(wx.EVT_MENU, lambda event: self.on_select_menuitem(event, grid, row), menuitem)
        self.PopupMenu(menu)
        menu.Destroy()

def on_select_menuitem(self, event, grid, row):
    """sets value of selected cell to value selected from menu
    (doesn't require column info because only third column works this way"""
    self.changes = True # if user selects a menuitem, that is an edit
    item_id =  event.GetId()
    item = event.EventObject.FindItemById(item_id)
    label= item.Label
    grid.SetCellValue(row, 2, label)


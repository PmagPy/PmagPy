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
        if self.data_type == 'sample' or self.data_type == 'site':
            choices = {2: (belongs_to, False), 3: (vocab.site_class, False), 4: (vocab.site_lithology, True), 5: (vocab.site_type, False), 6: (vocab.site_definition, False)}
        if self.data_type == 'location':
            choices = {1: (vocab.location_type, False)}
        if self.data_type == 'age':
            choices = {3: (vocab.geochronology_method_codes, False), 5: (vocab.age_units, False)}
        self.window.Bind(wx.grid.EVT_GRID_SELECT_CELL, lambda event: self.on_left_click(event, self.grid, choices), self.grid) 

    def on_left_click(self, event, grid, choices):
        """creates popup menu when user clicks on the third column
        allows user to edit third column, but only from available values"""
        col = event.GetCol()
        if col in choices.keys(): # column should have a pop-up menu
            row = event.GetRow()
            menu = wx.Menu()
            two_tiered = choices[col][1]
            choices = choices[col][0]
            if not two_tiered: # menu is one tiered
                # insert CLEAR option as first choice
                if 'CLEAR cell of all values' not in choices:
                    choices.insert(0, 'CLEAR cell of all values')
                for choice in choices:
                    if not choice: choice = " " # prevents error if choice is an empty string
                    menuitem = menu.Append(wx.ID_ANY, choice)
                    self.window.Bind(wx.EVT_MENU, lambda event: self.on_select_menuitem(event, grid, row, col), menuitem)
                self.window.PopupMenu(menu)
                menu.Destroy()
            else: # menu is two_tiered
                # insert CLEAR option as first menuitem
                clear = menu.Append(-1, 'CLEAR cell of all values')
                self.window.Bind(wx.EVT_MENU, lambda event: self.on_select_menuitem(event, grid, row, col), clear)
                for choice in sorted(choices.items()):
                    submenu = wx.Menu()
                    for item in choice[1]:
                        menuitem = submenu.Append(-1, item)
                        self.window.Bind(wx.EVT_MENU, lambda event: self.on_select_menuitem(event, grid, row, col), menuitem)
                    menu.AppendMenu(-1, choice[0], submenu)
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
        if str(label) == "CLEAR cell of all values":
            label = ""
        elif (col in range(3, 6) and self.data_type in ['site', 'sample']) or (col == 3 and self.data_type == 'age'):
        #if True:
            if not label in cell_value:
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


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
        self.window = grid.Parent # parent window in which grid resides
        self.belongs_to = belongs_to
        self.headers = headers
        self.selected_col = None
        self.selection = None # (top_left, bottom_right) of selection when there is a selection of cells
        self.dispersed_selection = [] # [(row, col), (row, col)]
        self.InitUI()

    def InitUI(self):
        belongs_to = self.belongs_to
        if self.data_type == 'specimen':
            self.choices = {2: (belongs_to, False)}
        if self.data_type == 'sample' or self.data_type == 'site':
            self.choices = {2: (belongs_to, False), 3: (vocab.site_class, False), 4: (vocab.site_lithology, True), 5: (vocab.site_type, False)}
        if self.data_type == 'site':
            self.choices[6] = (vocab.site_definition, False)
        if self.data_type == 'location':
            self.choices = {1: (vocab.location_type, False)}
        if self.data_type == 'age':
            self.choices = {3: (vocab.geochronology_method_codes, False), 5: (vocab.age_units, False)}
        self.window.Bind(wx.grid.EVT_GRID_SELECT_CELL, lambda event: self.on_left_click(event, self.grid, self.choices), self.grid) 
        self.window.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.on_label_click, self.grid)
        self.window.Bind(wx.grid.EVT_GRID_RANGE_SELECT, self.on_select_range, self.grid)
        #self.window.Bind(wx.grid.EVT_GRID_CELL_RIGHT_DCLICK, self.on_right_dclick, self.grid)
        #self.window.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.on_right_click, self.grid)
        #self.window.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.on_left_dclick, self.grid)

        #self.window.Bind(wx.grid.EVT_GRID_CMD_CELL_LEFT_CLICK, self.on_left_cmd_click, self.grid) # this calls EVT_GRID_RANGE_SELECT, so you might have to evt.Veto or something tos top propagation



    def on_right_click(self, event):
        print "you clicked right"
        print "event.ControlDown()", event.ControlDown()
        print "event.AltDown()", event.AltDown()
        print "event.MetaDown()", event.MetaDown()

    def on_right_dclick(self, event):
        print "you double clicked right"

    def on_left_dclick(self, event):
        print "you double clicked left"

    def on_select_range(self, event):
        print "select range"
        if event.MetaDown():
            print "meta down"
            #print dir(event)
            #print self.grid.GetSelectionBlockTopLeft()
            row, col = event.BottomRightCoords
            if (row, col) in self.dispersed_selection:
                self.dispersed_selection.remove((row, col))
                self.grid.SetCellBackgroundColour(row, col, 'white')
            else:
                self.dispersed_selection.append((row, col))
                #self.grid.SetCellBackgroundColour(row, col, 'light blue')
            print self.dispersed_selection
            event.Veto()
            self.grid.ForceRefresh()
            return 0
        
        if self.dispersed_selection:
            self.on_left_click_dispersed_selection(event)

        if self.grid.GetSelectionBlockTopLeft():
            top_left = self.grid.GetSelectionBlockTopLeft()[0]
            bottom_right = self.grid.GetSelectionBlockBottomRight()[0]
            if top_left[1] == bottom_right[1]: # only allow multi-cell editing if selection is all in one column
                self.selection = (top_left, bottom_right)
                self.window.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.on_left_click_selection, self.grid)


    def on_left_click_selection(self, event):
        print "doing on_left_click_selection"
        col = self.selection[0][1]
        for row in range(self.selection[0][0], self.selection[1][0]+1):
            self.grid.SetCellBackgroundColour(row, col, 'light blue')
        self.grid.ForceRefresh()
        self.on_left_click(event, self.grid, self.choices, self.selection)
        self.window.Unbind(wx.grid.EVT_GRID_SELECT_CELL, self.grid)
        self.window.Bind(wx.grid.EVT_GRID_SELECT_CELL, lambda event: self.on_left_click(event, self.grid, self.choices), self.grid) 
        for row in range(self.selection[0][0], self.selection[1][0]+1):
            self.grid.SetCellBackgroundColour(row, col, 'white')
        self.selection = None

    def on_left_click_dispersed_selection(self, event):
        print "doing on_left_click_dispersed_selection"
        for (row, col) in self.dispersed_selection:
            self.grid.SetCellBackgroundColour(row, col, 'light blue')
        self.grid.ForceRefresh()
        print "about to do regular on_left_click, with extra choices"
        self.window.Unbind(wx.grid.EVT_GRID_SELECT_CELL, self.grid)
        self.on_left_click(event, self.grid, self.choices, self.dispersed_selection, True)
        print "done with on purpose on left click"
        self.window.Bind(wx.grid.EVT_GRID_SELECT_CELL, lambda event: self.on_left_click(event, self.grid, self.choices), self.grid) 
        for (row, col) in self.dispersed_selection:
            self.grid.SetCellBackgroundColour(row, col, 'white')
        self.grid.ForceRefresh()
        self.dispersed_selection = []
        print "all done with on_left_click_dispersed_selection"
        return 



    def on_label_click(self, event):
        col = event.GetCol()
        if col == -1:
            return 0
        if col == 2 and self.data_type == 'age':
            return 0
        if (col not in (-1, 0, 1)) or (col == 1 and self.data_type in ['location', 'age']):
        # if a new column was chosen without de-selecting the previous column, deselect the old selected_col
            if self.selected_col != None and self.selected_col != col: 
                col_label_value = self.grid.GetColLabelValue(self.selected_col)
                self.grid.SetColLabelValue(self.selected_col, col_label_value[:-10])
                for row in range(self.grid.GetNumberRows()):
                    self.grid.SetCellBackgroundColour(row, self.selected_col, 'white')
                self.grid.ForceRefresh()
            # deselect col if user is clicking on it a second time
            if col == self.selected_col:  
                col_label_value = self.grid.GetColLabelValue(col)
                self.grid.SetColLabelValue(col, col_label_value[:-10])
                for row in range(self.grid.GetNumberRows()):
                    self.grid.SetCellBackgroundColour(row, col, 'white')
                self.grid.ForceRefresh()
                self.selected_col = None
            else:
                self.selected_col = col
                col_label_value = self.grid.GetColLabelValue(col)
                self.grid.SetColLabelValue(col, col_label_value + " \nEDIT ALL")
                for row in range(self.grid.GetNumberRows()):
                    self.grid.SetCellBackgroundColour(row, col, 'light blue')
                self.grid.ForceRefresh()
        has_dropdown = ((col == 2 and self.data_type is 'specimen') or (col in range(2, 6) and self.data_type in ['site', 'sample']) or (col in (3, 5) and self.data_type == 'age') or (col == 6 and self.data_type == 'site') or (col == 1 and self.data_type in ['location']))

        # if the column has no drop-down list, allow user to edit all cells in the column through text entry
        if (not has_dropdown and col not in (0, 1)) or (col == 1 and self.data_type in ['age']):  
            if self.selected_col == col:
                self.check.changes = True
                default_value = self.grid.GetCellValue(0, col)
                #data = wx.GetTextFromUser("Enter value for all cells in the column\nNote: this will overwrite any existing cell values", "Edit All", default_value)
                data = None
                dialog = wx.TextEntryDialog(None, "Enter value for all cells in the column\nNote: this will overwrite any existing cell values", "Edit All", default_value, style=wx.OK|wx.CANCEL)
                dialog.Centre()
                if dialog.ShowModal() == wx.ID_OK: 
                    data = dialog.GetValue() 
                    for row in range(self.grid.GetNumberRows()):
                        self.grid.SetCellValue(row, col, str(data))
                dialog.Destroy()
                # then deselect column
                col_label_value = self.grid.GetColLabelValue(col)
                self.grid.SetColLabelValue(col, col_label_value[:-10])
                for row in range(self.grid.GetNumberRows()):
                    self.grid.SetCellBackgroundColour(row, col, 'white')
                self.grid.ForceRefresh()
                self.selected_col = None

            
    def clean_up(self, grid):
        if self.selected_col:
            col_label_value = self.grid.GetColLabelValue(self.selected_col)
            self.grid.SetColLabelValue(self.selected_col, col_label_value[:-10])
            for row in range(self.grid.GetNumberRows()):
                self.grid.SetCellBackgroundColour(row, self.selected_col, 'white')
        self.grid.ForceRefresh()


    def on_left_click(self, event, grid, choices, selection=False, dispersed_selection=False):
        """creates popup menu when user clicks on the column
        if that column is in the list of choices that get a drop-down menu.
        allows user to edit the column, but only from available values"""
        print "doing on left click"
        #print dir(event)
        #print "event.WasProcessed()", event.WasProcessed()
        #print "event.Position", event.Position
        #print "event.ResumePropagation", event.ResumePropagation() # requires level argument, or something

        #event.Veto() # prevents border from being drawn
        print "selection:", selection
        print "dispersed:", dispersed_selection
        try:
            col = event.GetCol()
            row = event.GetRow()
        except AttributeError:
            row, col = selection[0][0], selection[0][1]

        is_dispersed = dispersed_selection

        #print "row", row
        #print "col", col
        #self.grid.SetGridCursor(row, col) # causes infinite recursion error
        print "choices:", choices
        print "col", col
        if col in choices.keys(): # column should have a pop-up menu
            print "make a pop-up menu"
            menu = wx.Menu()
            two_tiered = choices[col][1]
            choices = choices[col][0]
            if not two_tiered: # menu is one tiered
                if 'CLEAR cell of all values' not in choices:
                    choices.insert(0, 'CLEAR cell of all values')
                for choice in choices:
                    if not choice: choice = " " # prevents error if choice is an empty string
                    menuitem = menu.Append(wx.ID_ANY, str(choice))
                    self.window.Bind(wx.EVT_MENU, lambda event: self.on_select_menuitem(event, grid, row, col, selection, is_dispersed), menuitem)
                self.window.PopupMenu(menu)
                menu.Destroy()
            else: # menu is two_tiered
                clear = menu.Append(-1, 'CLEAR cell of all values')
                self.window.Bind(wx.EVT_MENU, lambda event: self.on_select_menuitem(event, grid, row, col, selection, is_dispersed), clear)
                for choice in sorted(choices.items()):
                    submenu = wx.Menu()
                    for item in choice[1]:
                        menuitem = submenu.Append(-1, str(item))
                        self.window.Bind(wx.EVT_MENU, lambda event: self.on_select_menuitem(event, grid, row, col, selection, is_dispersed), menuitem)
                    menu.AppendMenu(-1, choice[0], submenu)
                self.window.PopupMenu(menu)
                menu.Destroy()

    def update_drop_down_menu(self, grid, choices):
        self.window.Bind(wx.grid.EVT_GRID_SELECT_CELL, lambda event: self.on_left_click(event, grid, choices), grid) 
        self.choices = choices

    def on_select_menuitem(self, event, grid, row, col, selection, dispersed=False):
        """
        sets value of selected cell to value selected from menu
        """
        print "on_select_menuitem"
        print "selection:", selection
        print "dispersed:", dispersed
        self.check.changes = True # if user selects a menuitem, that is an edit
        item_id =  event.GetId()
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
                #self.selected_col = None
        else:
            grid.SetCellValue(row, col, label)
        
        if selection and dispersed:
            print "selection AND dispersed"
            for cell in selection:
                row = cell[0]
                grid.SetCellValue(row, col, label)
            return

        if selection:
            print "selection"
            for r in range(selection[0][0], selection[1][0]+1):
                grid.SetCellValue(r, col, label)

#!/usr/bin/env pythonw
"""
doc string
"""

# pylint: disable=C0103

import wx
import sys
import ErMagicBuilder
import pmag
import pmag_er_magic_dialogs
import pmag_widgets as pw


class MainFrame(wx.Frame):
    """
    make_magic
    """

    def __init__(self, WD=None, panel_name="panel"):
        wx.GetDisplaySize()
        wx.Frame.__init__(self, None, wx.ID_ANY, 'Title')
        self.panel = wx.Panel(self, name=panel_name, size=wx.GetDisplaySize())
        self.WD = WD
        self.InitUI()


    def InitUI(self):
        """
        initialize window
        """
        self.bsizer = wx.BoxSizer(wx.VERTICAL)
        self.ErMagic = ErMagicBuilder.ErMagicBuilder(self.WD)#,self.Data,self.Data_hierarchy)
        self.ErMagic.init_default_headers()
        self.grid = self.make_loc_grid()

        self.grid.InitUI()
        add_col_button = wx.Button(self.panel, label="Add additional column")
        self.Bind(wx.EVT_BUTTON, self.on_add_col, add_col_button)
        add_row_button = wx.Button(self.panel, label="Add additional row")
        self.Bind(wx.EVT_BUTTON, self.on_add_row, add_row_button)
        remove_row_button = wx.Button(self.panel, label="Remove last row")
        self.Bind(wx.EVT_BUTTON, self.on_remove_row, remove_row_button)
        add_many_rows_button = wx.Button(self.panel, label="Add many rows")
        rows = 10
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_add_many_rows(event, rows), add_many_rows_button)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        col_btn_vbox = wx.StaticBoxSizer(wx.StaticBox(self.panel, -1), wx.VERTICAL)
        row_btn_vbox = wx.StaticBoxSizer(wx.StaticBox(self.panel, -1), wx.VERTICAL)
        col_btn_vbox.Add(add_col_button, flag=wx.ALL, border=10)
        row_btn_vbox.Add(add_row_button, flag=wx.ALL, border=10)
        row_btn_vbox.Add(add_many_rows_button, flag=wx.ALL, border=10)
        row_btn_vbox.Add(remove_row_button, flag=wx.ALL, border=10)
        hbox.Add(col_btn_vbox)
        hbox.Add(row_btn_vbox)

        self.grid.size_grid()
        self.bsizer.Add(hbox, flag=wx.ALL, border=20)
        self.bsizer.Add(self.grid, flag=wx.ALL, border=10)
        self.panel.SetSizer(self.bsizer)
        self.bsizer.Fit(self)


    def make_loc_grid(self):
        """
        return grid for adding locations
        """
        col_labels = self.ErMagic.er_locations_header
        grid = pmag_er_magic_dialogs.MagicGrid(self.panel, 'grid_name', ['1'], col_labels)#, (300, 300))
        return grid


    def on_add_col(self, event):
        """
        Show simple dialog that allows user to add a new column name
        """
        dia = pw.TextDialog(self, 'column name: ')
        result = dia.ShowModal()
        if result == wx.ID_OK:
            name = dia.text_ctrl.return_value()
            self.grid.add_col(name)
        self.bsizer.Fit(self)

    def on_add_row(self, event):
        """
        method for add row button
        """
        self.grid.add_row()
        self.bsizer.Fit(self)

    def on_add_many_rows(self, event, num_rows):
        for row in range(num_rows):
            self.grid.add_row()
        self.bsizer.Fit(self)

    def on_remove_row(self, event):
        self.grid.remove_row()
        self.bsizer.Fit(self)






if __name__ == "__main__":
    #app = wx.App(redirect=True, filename="beta_log.log")
    # if redirect is true, wxpython makes its own output window for stdout/stderr
    app = wx.PySimpleApp(redirect=False)
    working_dir = pmag.get_named_arg_from_sys('-WD', '.')
    app.frame = MainFrame(working_dir)
    app.frame.Show()
    app.frame.Center()
    if '-i' in sys.argv:
        import wx.lib.inspection
        wx.lib.inspection.InspectionTool().Show()
    app.MainLoop()


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
        self.grid = pmag_er_magic_dialogs.MagicGrid(self.panel, 'grid_name', ['alpha', 'bravo', 'charlie', 'delta', 'echo'], range(10))#, (300, 300))
        self.grid.InitUI()
        add_col_button = wx.Button(self.panel, label="Add additional column")
        self.Bind(wx.EVT_BUTTON, self.on_add_col, add_col_button)

        self.grid.size_grid()
        self.bsizer.Add(add_col_button, flag=wx.ALL, border=20)
        self.bsizer.Add(self.grid, flag=wx.ALL, border=10)
        self.panel.SetSizer(self.bsizer)
        self.bsizer.Fit(self)

    def on_add_col(self, event):
        """
        Show simple dialog that allows user to add a new column name
        """
        dia = pw.TextDialog(self, 'column name: ')
        result = dia.ShowModal()
        if result == wx.ID_OK:
            name = dia.text_ctrl.return_value()
            self.grid.add_col(name)
        self.Refresh()
        self.panel.Refresh()
        self.grid.Refresh()
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


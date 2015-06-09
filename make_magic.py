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
        self.remove_cols_button = wx.Button(self.panel, label="Remove columns")
        self.Bind(wx.EVT_BUTTON, self.on_remove_cols, self.remove_cols_button)
        remove_row_button = wx.Button(self.panel, label="Remove last row")
        self.Bind(wx.EVT_BUTTON, self.on_remove_row, remove_row_button)
        many_rows_box = wx.BoxSizer(wx.HORIZONTAL)
        add_many_rows_button = wx.Button(self.panel, label="Add row(s)")
        self.rows_spin_ctrl = wx.SpinCtrl(self.panel, value='1', initial=1)
        many_rows_box.Add(add_many_rows_button, flag=wx.ALIGN_CENTRE)
        many_rows_box.Add(self.rows_spin_ctrl)
        self.Bind(wx.EVT_BUTTON, self.on_add_rows, add_many_rows_button)

        self.msg_boxsizer = wx.StaticBoxSizer(wx.StaticBox(self.panel, -1), wx.VERTICAL)
        self.msg_text = wx.StaticText(self.panel, label='blah blah blah', style=wx.TE_CENTER, name='msg text')
        self.msg_boxsizer.Add(self.msg_text)
        self.msg_boxsizer.ShowItems(False)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        col_btn_vbox = wx.StaticBoxSizer(wx.StaticBox(self.panel, -1), wx.VERTICAL)
        row_btn_vbox = wx.StaticBoxSizer(wx.StaticBox(self.panel, -1), wx.VERTICAL)
        col_btn_vbox.Add(add_col_button, flag=wx.ALL, border=5)
        col_btn_vbox.Add(self.remove_cols_button, flag=wx.ALL, border=5)
        row_btn_vbox.Add(many_rows_box, flag=wx.ALL, border=5)
        row_btn_vbox.Add(remove_row_button, flag=wx.ALL, border=5)
        hbox.Add(col_btn_vbox)
        hbox.Add(row_btn_vbox)

        self.grid.size_grid()
        self.bsizer.Add(hbox, flag=wx.ALL, border=20)
        self.bsizer.Add(self.msg_boxsizer, flag=wx.BOTTOM|wx.ALIGN_CENTRE, border=10)
        self.bsizer.Add(self.grid, flag=wx.ALL, border=10)
        self.panel.SetSizer(self.bsizer)

        self.bsizer.Fit(self)


        #wind = self.grid.GetGridColLabelWindow()
        #print "wind", wind
        #print "dir(wind)", dir(wind)
        #print "wind.GetChildren()", wind.GetChildren()
        #print "wind.ContainingSizer", wind.ContainingSizer
        #print "wind.GetBorder()", wind.GetBorder()
        #print "wind.GetBestSize()", wind.GetBestSize()
        #print "wind.GetSize()", wind.GetSize()
        #print "wind.Position", wind.Position

        #col_sizes = []
        #for col in range(self.grid.GetNumberCols()):
        #    size = self.grid.GetColSize(col)
        #    col_sizes.append(size)
        #print "self.grid.GetColLabelSize()", self.grid.GetColLabelSize()
        #print 'col_sizes', col_sizes
        #print "self.grid.GetColAt(3)", self.grid.GetColAt(3)
        #print "self.grid.GetColPos(self.grid.GetColAt(3))", self.grid.GetColPos(self.grid.GetColAt(3))

    def remove_col_label(self, event):
        """
        check to see if column is required
        if it is not, delete it from grid
        """
        col = event.GetCol()
        print col

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

    def on_remove_cols(self, event):
        # first unselect any selected cols/cells
        self.grid.ClearSelection()
        # then make some visual change
        self.msg_text.SetLabel("Click on a column to delete it")
        self.msg_boxsizer.ShowItems(True)
        self.bsizer.Fit(self)
        # then make binding so that clicking on a label makes that column disappear
        self.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.remove_col_label)
        # make sure reqd cols do not disappear, or at least come with a warning
        # unbind wx.grid.EVT_GRID_LABEL_LEFT_CLICK

    def on_add_rows(self, event):
        """
        add rows to grid
        """
        num_rows = self.rows_spin_ctrl.GetValue()
        for row in range(num_rows):
            self.grid.add_row()
        self.bsizer.Fit(self)

    def on_remove_row(self, event):
        """
        remove the last row in the grid
        """
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


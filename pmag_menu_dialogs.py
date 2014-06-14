#!/usr/bin/env pythonw

#--------------------------------------------------------------
# converting magnetometer files to MagIC format
#--------------------------------------------------------------
import wx
import os
import pmag
import subprocess
import pmag_widgets as pw
import wx.grid
import subprocess


class ImportOrientFile(wx.Frame):

    """ """
    title = "Import orient.txt file"

    def __init__(self, parent, WD):
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title)
        self.panel = wx.ScrolledWindow(self)
        self.WD = WD
        self.InitUI()

    def InitUI(self):

        pnl = self.panel

        TEXT = "Hello here is a bunch of text"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0 ----
        self.bSizer0 = pw.choose_file(pnl, 'add', method = self.on_add_file_button)

        #---sizer 1 ----
        self.bSizer1 = pw.select_specimen_ncn(pnl)
        
        #---sizer 2 ----
        self.bSizer2 = pw.select_specimen_ocn(pnl)

        #---sizer 3 ----
        self.bSizer3 = pw.select_declination(pnl)
        # need new widget for declination
        

        #---sizer 4 ----
        TEXT = "Hours to SUBTRACT from local time for GMT, default is 0:"
        self.bSizer4 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 5 ---

        #---sizer 6 ----

        #---sizer 7 ---


        #---buttons ---
        self.okButton = wx.Button(pnl, wx.ID_OK, "&OK")
        self.Bind(wx.EVT_BUTTON, self.on_okButton, self.okButton)

        self.cancelButton = wx.Button(pnl, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)

        self.helpButton = wx.Button(pnl, wx.ID_ANY, '&Help')
        self.Bind(wx.EVT_BUTTON, self.on_helpButton, self.helpButton)

        hboxok = wx.BoxSizer(wx.HORIZONTAL)
        hboxok.Add(self.okButton, 0, wx.ALL, 5)
        hboxok.Add(self.cancelButton, 0, wx.ALL, 5)
        hboxok.Add(self.helpButton, 0, wx.ALL, 5)

        #------
        vbox=wx.BoxSizer(wx.VERTICAL)

        vbox.AddSpacer(10)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer5, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer6, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer7, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.AddSpacer(10)
        #vbox.Add(wx.StaticLine(pnl), 0, wx.ALL|wx.EXPAND, 5)
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)        
        vbox.AddSpacer(20)

        hbox_all= wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.AddSpacer(vbox)
        hbox_all.AddSpacer(20)
        
        self.panel.SetSizer(hbox_all)
        self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()


    def on_add_file_button(self,event):
        text = "choose file to convert to MagIC"
        pw.on_add_file_button(self.panel, self.WD, event, text)

    def on_okButton(self, event):
        COMMAND = ""
        print COMMAND
        #pw.run_command_and_close_window(self, COMMAND, outfile)

    def on_cancelButton(self,event):
        self.Destroy()
        self.Parent.Raise()

    def on_helpButton(self, event):
        pw.on_helpButton("-h")



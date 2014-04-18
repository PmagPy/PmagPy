#!/usr/bin/env python

import wx


# make library for commonly used widgets.  


# this isn't right yet, but you can make it work

class choose_file(wx.StaticBox):
    
#    __init__(self, parent, id, pos, size, style, validator, name) 
    def __init__(self, parent, btn_text='add', method=None):
        print 'init choose file'
        super(choose_file, self).__init__(parent)
        self.parent = parent
        self.bSizer0 =  wx.StaticBoxSizer( wx.StaticBox( self.parent, wx.ID_ANY, "" ), wx.VERTICAL )
        self.file_path = wx.TextCtrl(parent, id=-1, size=(400,25), style=wx.TE_READONLY)
        self.add_file_button = wx.Button(parent, id=-1, label=btn_text,name='add')
        if method:
            self.Bind(wx.EVT_BUTTON, method, self.add_file_button)
        TEXT="Choose file (no spaces are allowed in path):"
        self.bSizer0.Add(wx.StaticText(self.parent, label=TEXT),wx.ALIGN_LEFT)
        self.bSizer0.AddSpacer(5)
        bSizer0_1=wx.BoxSizer(wx.HORIZONTAL)
        bSizer0_1.Add(self.add_file_button,wx.ALIGN_LEFT)
        bSizer0_1.AddSpacer(5)
        bSizer0_1.Add(self.file_path,wx.ALIGN_LEFT)
        self.bSizer0.Add(bSizer0_1,wx.ALIGN_LEFT)

    def sizer(self):
        return self.bSizer0

    
class labeled_text_field(wx.StaticBox):
    def __init__(self, parent, label="User name (optional)"):
        super(labeled_text_field, self).__init__(parent)
        self.parent = parent
        TEXT= label
        self.bSizer1 = wx.StaticBoxSizer( wx.StaticBox( self.parent, wx.ID_ANY, "" ), wx.HORIZONTAL )
        self.bSizer1.Add(wx.StaticText(self.parent, label=TEXT),wx.ALIGN_LEFT)
        self.bSizer1.AddSpacer(5)
        self.file_info_user = wx.TextCtrl(self.parent, id=-1, size=(100,25))
        self.bSizer1.Add(self.file_info_user,wx.ALIGN_LEFT)

    def sizer(self):
        return self.bSizer1




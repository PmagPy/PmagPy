#!/usr/bin/env python

import wx


# library for commonly used widgets.  




class choose_file(wx.StaticBoxSizer):

    def __init__(self, parent, orient=wx.VERTICAL, btn_text='add', method=None):
        #__init__ (self, box, orient=HORIZONTAL)
        box = wx.StaticBox( parent, wx.ID_ANY, "" )
        super(choose_file, self).__init__(box, orient=wx.VERTICAL)
        self.btn_text = btn_text
        self.method = method
        self.parent = parent

        self.file_path = wx.TextCtrl(self.parent, id=-1, size=(400,25), style=wx.TE_READONLY)
        self.add_file_button = wx.Button(self.parent, id=-1, label=btn_text,name='add')
        if method:
            self.parent.Bind(wx.EVT_BUTTON, method, self.add_file_button)
        TEXT="Choose file (no spaces are allowed in path):"
        self.Add(wx.StaticText(self.parent, label=TEXT),wx.ALIGN_LEFT)
        self.AddSpacer(5)
        bSizer0_1=wx.BoxSizer(wx.HORIZONTAL)
        bSizer0_1.Add(self.add_file_button, wx.ALIGN_LEFT)
        bSizer0_1.AddSpacer(5)
        bSizer0_1.Add(self.file_path, wx.ALIGN_LEFT)
        self.Add(bSizer0_1, wx.ALIGN_LEFT)




"""
class choose_file(wx.StaticBox):
    
#    __init__(self, parent, id, pos, size, style, validator, name) 
    def __init__(self, parent, btn_text='add', method=None):
        print 'init choose file'
        print 'method for binding', method
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
        bSizer0_1.Add(self.add_file_button, wx.ALIGN_LEFT)
        bSizer0_1.AddSpacer(5)
        bSizer0_1.Add(self.file_path, wx.ALIGN_LEFT)
        self.bSizer0.Add(bSizer0_1, wx.ALIGN_LEFT)

    def sizer(self):
        return self.bSizer0
"""

class choose_dir(wx.StaticBox):
    
#    __init__(self, parent, id, pos, size, style, validator, name) 
    def __init__(self, parent, btn_text='add', method=None):
        #print 'init choose file'
        self.parent = parent
        self.bSizer0 =  wx.StaticBoxSizer( wx.StaticBox( self.parent, wx.ID_ANY, "" ), wx.VERTICAL )
        self.file_path = wx.TextCtrl(parent, id=-1, size=(400,25), style=wx.TE_READONLY)
        self.add_file_button = wx.Button(parent, id=-1, label=btn_text,name='add')
        if method:
            self.Bind(wx.EVT_BUTTON, method, self.add_file_button)
        TEXT="Choose folder (no spaces are allowed in path):"
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
        self.parent = parent
        TEXT= label
        self.bSizer1 = wx.StaticBoxSizer( wx.StaticBox( self.parent, wx.ID_ANY, "" ), wx.HORIZONTAL )
        self.bSizer1.Add(wx.StaticText(self.parent, label=TEXT),wx.ALIGN_LEFT)
        self.bSizer1.AddSpacer(5)
        self.file_info_user = wx.TextCtrl(self.parent, id=-1, size=(100,25))
        self.bSizer1.Add(self.file_info_user,wx.ALIGN_LEFT)

    def sizer(self):
        return self.bSizer1



class select_specimen_ncn():  # possibly will need to add "self" to more of these things to add functionality, but maybe not
    """provides box sizer with a drop down menu for the standard specimen naming conventions"""
    def __init__(self, parent):
        self.bSizer3 = wx.StaticBoxSizer( wx.StaticBox( parent, wx.ID_ANY, "" ), wx.VERTICAL )
        ncn_keys = ['XXXXY', 'XXXX-YY', 'XXXX.YY', 'XXXX[YYY] where YYY is sample designation, enter number of Y', 'sample name=site name', 'Site names in orient.txt file', '[XXXX]YYY where XXXX is the site name, enter number of X', 'this is a synthetic and hasno site name']
        ncn_values = range(1,9)
        sample_naming_conventions = dict(zip(ncn_keys, ncn_values))
        select_naming_convention = wx.ComboBox(parent, -1, ncn_keys[0], size=(250,25), choices=ncn_keys, style=wx.CB_DROPDOWN)
        sample_naming_convention_char = wx.TextCtrl(parent, id=-1, size=(40,25))
        gridbSizer4 = wx.GridSizer(2, 2, 5, 10)
        gridbSizer4.AddMany( [(wx.StaticText(parent,label="specimen-sample naming convention",style=wx.TE_CENTER),wx.ALIGN_LEFT),
                      (wx.StaticText(parent, label="delimiter (if necessary)", style=wx.TE_CENTER),wx.ALIGN_LEFT),
                      (select_naming_convention,wx.ALIGN_LEFT),
                      (sample_naming_convention_char,wx.ALIGN_LEFT)])
        #bSizer4.Add(self.sample_specimen_text,wx.ALIGN_LEFT)                                                
        self.bSizer3.AddSpacer(8)
        self.bSizer3.Add(gridbSizer4,wx.ALIGN_LEFT)

    def sizer(self):
        return self.bSizer3


class replicate_measurements():

    def __init__(self, parent):
        self.bSizer6 = wx.StaticBoxSizer( wx.StaticBox( parent, wx.ID_ANY, "" ), wx.HORIZONTAL )
        TEXT="replicate measurements:"
        replicate_text = wx.StaticText(parent,label=TEXT,style=wx.TE_CENTER)
        self.replicate_rb1 = wx.RadioButton(parent, -1, 'Average replicate measurements', style=wx.RB_GROUP)
        self.replicate_rb1.SetValue(True)
        self.replicate_rb2 = wx.RadioButton(parent, -1, 'take only last measurement from replicate measurements')
        self.bSizer6.Add(replicate_text,wx.ALIGN_LEFT)
        self.bSizer6.AddSpacer(10)
        self.bSizer6.Add(self.replicate_rb1,wx.ALIGN_LEFT)
        self.bSizer6.AddSpacer(10)
        self.bSizer6.Add(self.replicate_rb2,wx.ALIGN_LEFT)

    def sizer(self):
        return self.bSizer6



class check_boxes():
    
    def __init__(self, parent, gridsize, choices, text):
        box = wx.StaticBox(parent, wx.ID_ANY, "")
        gridSizer2 = wx.GridSizer(gridsize[0], gridsize[1], gridsize[2], gridsize[3])
        for n, choice in enumerate(choices):
            cb = wx.CheckBox(parent, -1, choice)
            gridSizer2.Add(cb, wx.ALIGN_RIGHT)
        self.bSizer2 = wx.StaticBoxSizer(box, wx.VERTICAL)
        self.bSizer2.Add(wx.StaticText(parent, label = text), wx.ALIGN_LEFT)
        self.bSizer2.Add(gridSizer2, wx.ALIGN_RIGHT)
        self.bSizer2.AddSpacer(4)

    def sizer(self):
        return self.bSizer2

class lab_field():
    
    def __init__(self, parent):
        TEXT="Lab field (leave blank if unnecessary). Example: 40 0 -90"
        self.bSizer3 = wx.StaticBoxSizer( wx.StaticBox( parent, wx.ID_ANY, "", size=(100, 100) ), wx.VERTICAL )
        self.file_info_text=wx.StaticText(parent,label=TEXT,style=wx.TE_CENTER)
        self.file_info_Blab = wx.TextCtrl(parent, id=-1, size=(40,25))
        self.file_info_Blab_dec = wx.TextCtrl(parent, id=-1, size=(40,25))
        self.file_info_Blab_inc = wx.TextCtrl(parent, id=-1, size=(40,25))
        gridbSizer3 = wx.GridSizer(2, 3, 0, 10)
        gridbSizer3.AddMany( [(wx.StaticText(parent,label="B (uT)",style=wx.TE_CENTER),wx.ALIGN_LEFT),
            (wx.StaticText(parent,label="dec",style=wx.TE_CENTER),wx.ALIGN_LEFT),
            (wx.StaticText(parent,label="inc",style=wx.TE_CENTER),wx.ALIGN_LEFT),
            (self.file_info_Blab,wx.ALIGN_LEFT),
            (self.file_info_Blab_dec,wx.ALIGN_LEFT),
            (self.file_info_Blab_inc,wx.ALIGN_LEFT)])
        self.bSizer3.Add(self.file_info_text,wx.ALIGN_LEFT)
        self.bSizer3.AddSpacer(8)
        self.bSizer3.Add(gridbSizer3,wx.ALIGN_LEFT)

    def sizer(self):
        return self.bSizer3
        





def on_add_file_button(SELF, event, text):
    dlg = wx.FileDialog(
            None, message=text,
        defaultDir=SELF.WD,
            defaultFile="",
        style=wx.OPEN | wx.CHANGE_DIR
            )
    if dlg.ShowModal() == wx.ID_OK:
            SELF.file_path.SetValue(str(dlg.GetPath()))
"""
def on_add_file_button(SELF,event, text):

   dlg = wx.FileDialog(
           None,message=text,
           defaultDir=SELF.WD,
        defaultFile="",
        style=wx.OPEN | wx.CHANGE_DIR
        )
   if dlg.ShowModal() == wx.ID_OK:
        #SELF.box_sizer_high_level_text.Add(SELF.high_level_text_box, 0, wx.ALIGN_LEFT, 0 )                                       
        SELF.file_pathes.AppendText(str(dlg.GetPath())+"\n")
"""

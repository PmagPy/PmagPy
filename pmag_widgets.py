#!/usr/bin/env python

import os
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
        print 'self.parent', self.parent
        self.parent.file_path = wx.TextCtrl(self.parent, id=-1, size=(400,25), style=wx.TE_READONLY)
        print 'excalibur'
        self.add_file_button = wx.Button(self.parent, id=-1, label=btn_text,name='add')
        print 'hooray'
        if method:
            self.parent.Bind(wx.EVT_BUTTON, method, self.add_file_button)
        TEXT="Choose file (no spaces are allowed in path):"
        self.Add(wx.StaticText(self.parent, label=TEXT),wx.ALIGN_LEFT)
        self.AddSpacer(4)
        bSizer0_1=wx.BoxSizer(wx.HORIZONTAL)
        bSizer0_1.Add(self.add_file_button, wx.ALIGN_LEFT)
        bSizer0_1.AddSpacer(4)
        bSizer0_1.Add(self.parent.file_path, wx.ALIGN_LEFT)
        self.Add(bSizer0_1, wx.ALIGN_LEFT)

    def return_value(self):
        return self.parent.file_path.GetValue()


class choose_dir(wx.StaticBox):
    
    def __init__(self, parent, btn_text='add', method=None):
        self.parent = parent
        self.bSizer0 =  wx.StaticBoxSizer( wx.StaticBox( self.parent, wx.ID_ANY, "" ), wx.VERTICAL )
        self.file_path = wx.TextCtrl(parent, id=-1, size=(400,25), style=wx.TE_READONLY)
        self.add_file_button = wx.Button(parent, id=-1, label=btn_text,name='add')
        if method:
            self.Bind(wx.EVT_BUTTON, method, self.add_file_button)
        TEXT="Choose folder (no spaces are allowed in path):"
        self.bSizer0.Add(wx.StaticText(self.parent, label=TEXT),wx.ALIGN_LEFT)
        self.bSizer0.AddSpacer(4)
        bSizer0_1=wx.BoxSizer(wx.HORIZONTAL)
        bSizer0_1.Add(self.add_file_button,wx.ALIGN_LEFT)
        bSizer0_1.AddSpacer(4)
        bSizer0_1.Add(self.file_path,wx.ALIGN_LEFT)
        self.bSizer0.Add(bSizer0_1,wx.ALIGN_LEFT)

    def sizer(self):
        return self.bSizer0


class labeled_text_field(wx.StaticBoxSizer):
    def __init__(self, parent, label="User name (optional)"):
        self.parent = parent
        box = wx.StaticBox( self.parent, wx.ID_ANY, "" )
        super(labeled_text_field, self).__init__(box, orient=wx.HORIZONTAL)
        TEXT= label
        self.Add(wx.StaticText(self.parent, label=TEXT),wx.ALIGN_LEFT)
        self.AddSpacer(4)
        self.text_field = wx.TextCtrl(self.parent, id=-1, size=(100,25))
        self.Add(self.text_field,wx.ALIGN_LEFT)
        
    def return_value(self):
        return self.text_field.GetValue()



class select_specimen_ncn(wx.StaticBoxSizer):  
    """provides box sizer with a drop down menu for the standard specimen naming conventions"""
    def __init__(self, parent):
        self.parent = parent
        box = wx.StaticBox( parent, wx.ID_ANY, "" )
        super(select_specimen_ncn, self).__init__(box, orient=wx.VERTICAL)
        ncn_keys = ['XXXXY', 'XXXX-YY', 'XXXX.YY', 'XXXX[YYY] where YYY is sample designation, enter number of Y', 'sample name=site name', 'Site names in orient.txt file', '[XXXX]YYY where XXXX is the site name, enter number of X', 'this is a synthetic and has no site name']
        ncn_values = range(1,9)
        self.sample_naming_conventions = dict(zip(ncn_keys, ncn_values))
        self.select_naming_convention = wx.ComboBox(parent, -1, ncn_keys[0], size=(250,25), choices=ncn_keys, style=wx.CB_DROPDOWN)
        self.sample_naming_convention_char = wx.TextCtrl(parent, id=-1, size=(40,25))
        gridbSizer = wx.GridSizer(2, 2, 5, 10)
        gridbSizer.AddMany( [(wx.StaticText(parent,label="specimen-sample naming convention",style=wx.TE_CENTER),wx.ALIGN_LEFT),
                      (wx.StaticText(parent, label="delimiter (if necessary)", style=wx.TE_CENTER),wx.ALIGN_LEFT),
                      (self.select_naming_convention,wx.ALIGN_LEFT),
                      (self.sample_naming_convention_char,wx.ALIGN_LEFT)])
        self.AddSpacer(8)
        self.Add(gridbSizer,wx.ALIGN_LEFT)

    def return_value(self):
        print self.select_naming_convention.GetValue()
        selected_ncn = str(self.select_naming_convention.GetValue())
        ncn_number = self.sample_naming_conventions[selected_ncn]
        if ncn_number == 4 or ncn_number == 7: # these are the only two that require a delimiter
            return str(ncn_number) + '-' + str(self.sample_naming_convention_char.GetValue())
        else:
            return str(ncn_number)


class replicate_measurements(wx.StaticBoxSizer):
    
    def __init__(self, parent):
        box = wx.StaticBox( parent, wx.ID_ANY, "" )
        super(replicate_measurements, self).__init__(box, orient=wx.HORIZONTAL)
        TEXT="replicate measurements:"
        replicate_text = wx.StaticText(parent,label=TEXT,style=wx.TE_CENTER)
        self.replicate_rb1 = wx.RadioButton(parent, -1, 'Average replicate measurements', style=wx.RB_GROUP)
        self.replicate_rb1.SetValue(True)
        self.replicate_rb2 = wx.RadioButton(parent, -1, 'take only last measurement from replicate measurements')
        self.Add(replicate_text,wx.ALIGN_LEFT)
        self.AddSpacer(8)
        self.Add(self.replicate_rb1,wx.ALIGN_LEFT)
        self.AddSpacer(8)
        self.Add(self.replicate_rb2,wx.ALIGN_LEFT)

    def return_value(self):
        if self.replicate_rb1.GetValue():
            return True
        else:
            return False

class check_boxes(wx.StaticBoxSizer):
    
    def __init__(self, parent, gridsize, choices, text):
        box = wx.StaticBox(parent, wx.ID_ANY, "")
        super(check_boxes, self).__init__(box, orient=wx.VERTICAL)
        
        gridSizer2 = wx.GridSizer(gridsize[0], gridsize[1], gridsize[2], gridsize[3])
        self.boxes = []
        for n, choice in enumerate(choices):
            cb = wx.CheckBox(parent, -1, choice)
            self.boxes.append(cb)
            gridSizer2.Add(cb, wx.ALIGN_RIGHT)
        self.Add(wx.StaticText(parent, label = text), wx.ALIGN_LEFT)
        self.Add(gridSizer2, wx.ALIGN_RIGHT)
        self.AddSpacer(4)

    def return_value(self):
        checked = []
        for cb in self.boxes:
            if cb.GetValue():
                checked.append(str(cb.Label))
        return checked


class lab_field(wx.StaticBoxSizer):
    
    def __init__(self, parent):
        box = wx.StaticBox( parent, wx.ID_ANY, "", size=(100, 100) )
        super(lab_field, self).__init__(box, orient=wx.VERTICAL)
        TEXT="Lab field (leave blank if unnecessary). Example: 40 0 -90"
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
        self.Add(self.file_info_text,wx.ALIGN_LEFT)
        self.AddSpacer(8)
        self.Add(gridbSizer3,wx.ALIGN_LEFT)

    def return_value(self):
        lab_field = "{} {} {}".format(self.file_info_Blab.GetValue(), self.file_info_Blab_dec.GetValue(), self.file_info_Blab_inc.GetValue())
        if lab_field.isspace():
            return ''
        return lab_field



# methods!





def on_add_file_button(SELF, WD, event, text):
    print 'SELF', SELF
#    print 'dir(SELF)', dir(SELF)
    dlg = wx.FileDialog(
            None, message=text,
        defaultDir=WD,
            defaultFile="",
        style=wx.OPEN | wx.CHANGE_DIR
            )
    if dlg.ShowModal() == wx.ID_OK:
            SELF.file_path.SetValue(str(dlg.GetPath()))

"""
def on_add_file_button(SELF, event, text):
    print 'SELF', SELF
#    print 'dir(SELF)', dir(SELF)
    dlg = wx.FileDialog(
            None, message=text,
        defaultDir=SELF.WD,
            defaultFile="",
        style=wx.OPEN | wx.CHANGE_DIR
            )
    if dlg.ShowModal() == wx.ID_OK:
            SELF.file_path.SetValue(str(dlg.GetPath()))
"""

def run_command_and_close_window(SELF, command, outfile):
    print "-I- Running Python command:\n %s"%command
    os.system(command)                                          
    MSG="file converted to MagIC format file:\n%s.\n\n See Termimal (Mac) or command prompt (windows) for errors"% outfile
    dlg = wx.MessageDialog(None,caption="Message:", message=MSG ,style=wx.OK|wx.ICON_INFORMATION)
    dlg.ShowModal()
    dlg.Destroy()
    SELF.Destroy()


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

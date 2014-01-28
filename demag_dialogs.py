#!/usr/bin/env python

import matplotlib
matplotlib.use('WXAgg')
import wx


#--------------------------------------------------------------    
# Dialogs boxes for demag_gui.py
#--------------------------------------------------------------


#--------------------------------------------------------------    
# MagIc results tables dialog
#--------------------------------------------------------------

class magic_pmag_tables_dialog(wx.Dialog):
    def __init__(self,parent,WD,Data,Data_info):
        super(magic_pmag_tables_dialog, self).__init__(parent, title="MagIC results table Dialog")
        self.InitUI()

    def InitUI(self):

        pnl1 = wx.Panel(self)
        vbox = wx.StaticBoxSizer(wx.StaticBox( pnl1, wx.ID_ANY, "MagIC result tables options" ), wx.VERTICAL)        

        #---------------------
        # Acceptance criteria
        #---------------------
        #self.acceptance_criteria_text=wx.StaticText(pnl1,label="apply acceptance criteria from pmag_criteria.txt:",style=wx.TE_CENTER)        
        self.cb_acceptance_criteria= wx.CheckBox(pnl1, -1, 'apply acceptance criteria from pmag_criteria.txt', (10, 30))

        #---------------------
        # choose coordinate system
        #---------------------
        self.coor_text=wx.StaticText(pnl1,label="coordinate system:",style=wx.TE_CENTER)
        self.rb_spec_coor = wx.RadioButton(pnl1, -1, 'specimen', (10, 10), style=wx.RB_GROUP)
        self.rb_geo_coor = wx.RadioButton(pnl1, -1, 'geographic', (10, 30))
        self.rb_tilt_coor = wx.RadioButton(pnl1, -1, 'tilt-corrected', (10, 30))
        self.rb_geo_tilt_coor = wx.RadioButton(pnl1, -1, 'geographic and tilt-corrected', (10, 30))
        
        self.rb_geo_coor.SetValue(True)
        coordinates_window = wx.GridSizer(1, 4, 6, 6)
        coordinates_window.AddMany( [(self.rb_spec_coor),            
            (self.rb_geo_coor),
            (self.rb_tilt_coor),
            (self.rb_geo_tilt_coor)])

        #---------------------
        # default age
        #---------------------
        self.default_age_text=wx.StaticText(pnl1,label="default age if site age does not exist in er_ages.txt:",style=wx.TE_CENTER)        
        self.cb_default_age = wx.CheckBox(pnl1, -1, 'use default age', (10, 30))

        self.default_age_min=wx.TextCtrl(pnl1,style=wx.TE_CENTER,size=(50,20))
        self.default_age_max=wx.TextCtrl(pnl1,style=wx.TE_CENTER,size=(50,20))
        age_unit_choices=['Years Cal BP','Years Cal AD (+/-)','Years BP','Years AD (+/-)','Ma','Ka','Ga']
        self.default_age_unit=wx.ComboBox(pnl1, -1,size=(150, -1), value = '', choices=age_unit_choices, style=wx.CB_READONLY)
        
        default_age_window = wx.GridSizer(2, 4, 6, 6)
        default_age_window.AddMany( [(wx.StaticText(pnl1,label="",style=wx.TE_CENTER), wx.EXPAND),            
            (wx.StaticText(pnl1,label="min age",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="max age",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="units",style=wx.TE_CENTER), wx.EXPAND),
            (self.cb_default_age,wx.EXPAND),
            (self.default_age_min,wx.EXPAND),
            (self.default_age_max,wx.EXPAND),
            (self.default_age_unit,wx.EXPAND)])
            
        
        #---------------------
        # sample 
        #---------------------
        self.cb_sample_mean=wx.CheckBox(pnl1, -1, 'calculate sample mean  ', (10, 30))
        self.cb_sample_mean.SetValue(False)  
        sample_mean_choices=['specimens']
        self.combo_sample_mean=wx.ComboBox(pnl1, -1,size=(150, -1), value = 'specimens', choices=sample_mean_choices, style=wx.CB_READONLY)
        sample_mean_types=['Fisher']
        self.combo_sample_type=wx.ComboBox(pnl1, -1,size=(150, -1), value = 'Fisher', choices=sample_mean_types, style=wx.CB_READONLY)
        self.cb_sample_mean_VGP=wx.CheckBox(pnl1, -1, 'calculate sample VGP', (10, 30))
        self.cb_sample_mean_VGP.SetValue(False)  
        self.Bind(wx.EVT_CHECKBOX,self.on_change_cb_sample_mean_VGP,self.cb_sample_mean_VGP)
   
        sample_mean_window = wx.GridSizer(2, 4, 6, 6)
        sample_mean_window.AddMany( [(wx.StaticText(pnl1,label="",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="average sample by:",style=wx.TE_CENTER), wx.EXPAND),            
            (wx.StaticText(pnl1,label="calculation type",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="",style=wx.TE_CENTER), wx.EXPAND),
            (self.cb_sample_mean,wx.EXPAND),            
            (self.combo_sample_mean,wx.EXPAND),
            (self.combo_sample_type,wx.EXPAND),
            (self.cb_sample_mean_VGP,wx.EXPAND)])

        #---------------------
        # site 
        #---------------------
        self.cb_site_mean=wx.CheckBox(pnl1, -1, 'calculate site mean    ', (10, 30))
        self.cb_site_mean.SetValue(True)         
        site_mean_choices=['specimens','samples']
        self.combo_site_mean=wx.ComboBox(pnl1, -1,size=(150, -1), value = 'specimens', choices=site_mean_choices, style=wx.CB_READONLY)
        site_mean_types=['Fisher']
        self.combo_site_type=wx.ComboBox(pnl1, -1,size=(150, -1), value = 'Fisher', choices=site_mean_types, style=wx.CB_READONLY)
        self.cb_site_mean_VGP=wx.CheckBox(pnl1, -1, 'calculate site VGP', (10, 30))
        self.cb_site_mean_VGP.SetValue(True)         
        self.Bind(wx.EVT_CHECKBOX,self.on_change_cb_site_mean_VGP,self.cb_site_mean_VGP)

        site_mean_window = wx.GridSizer(2, 4, 6, 6)
        site_mean_window.AddMany( [(wx.StaticText(pnl1,label="",style=wx.TE_CENTER), wx.EXPAND), 
            (wx.StaticText(pnl1,label="average site by:",style=wx.TE_CENTER), wx.EXPAND),           
            (wx.StaticText(pnl1,label="calculation type",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="",style=wx.TE_CENTER), wx.EXPAND),
            (self.cb_site_mean,wx.EXPAND),
            (self.combo_site_mean,wx.EXPAND),
            (self.combo_site_type,wx.EXPAND),
            (self.cb_site_mean_VGP,wx.EXPAND)])

        #---------------------
        # location 
        #---------------------
        self.cb_location_mean=wx.CheckBox(pnl1, -1, 'calculate location mean', (10, 30))
        self.cb_location_mean.SetValue(False)
        location_mean_choices=['sites']
        self.combo_location_mean=wx.ComboBox(pnl1, -1,size=(150, -1), value = 'sites', choices=location_mean_choices, style=wx.CB_READONLY)
        location_mean_types=['Fisher-separate polarities']
        self.combo_loction_type=wx.ComboBox(pnl1, -1,size=(150, -1), value = 'Fisher-separate polarities', choices=location_mean_types, style=wx.CB_READONLY)
        self.cb_location_mean_VGP=wx.CheckBox(pnl1, -1, 'calculate location VGP', (10, 30))
        self.cb_location_mean_VGP.SetValue(True)
        #self.Bind(wx.EVT_CHECKBOX,self.on_change_cb_location_mean_VGP,self.cb_location_mean_VGP)
   
         
        loaction_mean_window = wx.GridSizer(2, 4, 6, 6)
        loaction_mean_window.AddMany( [(wx.StaticText(pnl1,label="",style=wx.TE_CENTER), wx.EXPAND), 
            (wx.StaticText(pnl1,label="average location by:",style=wx.TE_CENTER), wx.EXPAND),            
            (wx.StaticText(pnl1,label="calculation type",style=wx.TE_CENTER), wx.EXPAND),
            (wx.StaticText(pnl1,label="",style=wx.TE_CENTER), wx.EXPAND),
            (self.cb_location_mean,wx.EXPAND),
            (self.combo_location_mean,wx.EXPAND),
            (self.combo_loction_type,wx.EXPAND),
            (self.cb_location_mean_VGP,wx.EXPAND)])

        #---------------------
        # OK/Cancel buttons 
        #---------------------
                
        hboxok = wx.BoxSizer(wx.HORIZONTAL)
        self.okButton = wx.Button(pnl1, wx.ID_OK, "&OK")
        self.cancelButton = wx.Button(pnl1, wx.ID_CANCEL, '&Cancel')
        hboxok.Add(self.okButton)
        hboxok.AddSpacer(20)
        hboxok.Add(self.cancelButton )
                
        #---------------------

        vbox.Add(wx.StaticLine(pnl1), 0, wx.ALL|wx.EXPAND, 5)  
        vbox.AddSpacer(10)

        vbox.Add(self.cb_acceptance_criteria,flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(10)
        vbox.Add(wx.StaticLine(pnl1), 0, wx.ALL|wx.EXPAND, 5)  
        vbox.AddSpacer(10)
        
        vbox.Add(self.coor_text,flag=wx.ALIGN_CENTER_HORIZONTAL, border=100)
        vbox.AddSpacer(10)
        vbox.Add(coordinates_window,flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(10)
        vbox.Add(wx.StaticLine(pnl1), 0, wx.ALL|wx.EXPAND, 5)  
        vbox.AddSpacer(10)

        vbox.Add(self.default_age_text,flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(10)
        vbox.Add(default_age_window,flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(10)
        vbox.Add(wx.StaticLine(pnl1), 0, wx.ALL|wx.EXPAND, 5)  
        vbox.AddSpacer(10)


        vbox.Add(sample_mean_window,flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(10)
        vbox.Add(wx.StaticLine(pnl1), 0, wx.ALL|wx.EXPAND, 5)  
        vbox.AddSpacer(10)

        vbox.Add(site_mean_window,flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(10)
        vbox.Add(wx.StaticLine(pnl1), 0, wx.ALL|wx.EXPAND, 5)  
        vbox.AddSpacer(10)

        vbox.Add(loaction_mean_window,flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(10)
        vbox.Add(wx.StaticLine(pnl1), 0, wx.ALL|wx.EXPAND, 5)  
        vbox.AddSpacer(10)

        #-------------
        vbox1=wx.BoxSizer(wx.VERTICAL)
        vbox1.AddSpacer(10)
        vbox1.Add(vbox)
        vbox1.AddSpacer(10)
        vbox1.Add(hboxok,flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox1.AddSpacer(10)


#vbox.Add(wx.StaticLine(pnl1), 0, wx.ALL|wx.EXPAND, 5)  
        #vbox.AddSpacer(10)
        
        #pnl1.SetSizer(vbox)        
        #hbox = wx.BoxSizer(wx.HORIZONTAL)        
        #hbox.AddSpacer(50)
        #hbox.Add(vbox,border=100)
        #hbox.AddSpacer(50)
        pnl1.SetSizer(vbox1)
        vbox1.Fit(self)
    
    def on_change_cb_sample_mean_VGP(self,event):
        if self.cb_sample_mean_VGP.GetValue()==True:
            self.cb_site_mean_VGP.SetValue(False)

    def on_change_cb_site_mean_VGP(self,event):
        if self.cb_site_mean_VGP.GetValue()==True:
            self.cb_sample_mean_VGP.SetValue(False)
        
    def on_change_cb_location_mean_VGP(self,event):
        if self.cb_location_mean_VGP.GetValue()==True:
            self.cb_location_mean_VGP.SetValue(False)
                    
#if __name__ == '__main__':
#    app = wx.PySimpleApp()
#    app.frame = magic_pmag_tables_dialog(None,"./",{},{})
#    app.frame.Center()
#    #alignToTop(app.frame)
#    #dw, dh = wx.DisplaySize() 
#    #w, h = app.frame.GetSize()
#    #print 'display 2', dw, dh
#    #print "gui 2", w, h
#    app.frame.Show()
#    app.MainLoop()

#!/usr/bin/env python

#--------------------------------------------------------------
# converting magnetometer files to MagIC format
#--------------------------------------------------------------
import wx
import os
import subprocess
import pmag_widgets as pw

class import_magnetometer_data(wx.Dialog):
    
    def __init__(self,parent,id,title,WD):
        wx.Dialog.__init__(self, parent, id, title)#, size=(300, 300))
        #super(import_magnetometer_data, self).__init__(*args, **kw)
        self.WD=WD
        self.InitUI()
        self.SetTitle(title)
        
    def InitUI(self):

        pnl = wx.Panel(self)
        vbox=wx.BoxSizer(wx.VERTICAL)

        formats=['generic format','SIO format','CIT format','2G-binary format','HUJI format','LDEO format','IODP SRM (csv) format','PMD (ascii) format','TDT format']
        sbs = wx.StaticBoxSizer( wx.StaticBox( pnl, wx.ID_ANY, 'step 1: choose file format' ), wx.VERTICAL )

        sbs.AddSpacer(5)
        self.oc_rb0 = wx.RadioButton(pnl, -1,label=formats[0],name='0', style=wx.RB_GROUP)
        sbs.Add(self.oc_rb0)
        sbs.AddSpacer(5)
        sbs.Add(wx.StaticLine(pnl), 0, wx.ALL|wx.EXPAND, 5)
        sbs.AddSpacer(5)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioButtonSelect, self.oc_rb0)
        

        for i in range(1,len(formats)):
            command="self.oc_rb%i = wx.RadioButton(pnl, -1, label='%s', name='%i')"%(i,formats[i],i)
            exec command
            command="sbs.Add(self.oc_rb%i)"%(i)
            exec command
            sbs.AddSpacer(5)
            #
            command = "self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioButtonSelect, self.oc_rb%i)" % (i)
            exec command
            #

        self.oc_rb0.SetValue(True)
        self.checked_rb = self.oc_rb0


        
        #---------------------
        # OK/Cancel buttons
        #---------------------
                
        hboxok = wx.BoxSizer(wx.HORIZONTAL)
        self.okButton =  wx.Button(pnl, id=-1, label='Import file')
        self.Bind(wx.EVT_BUTTON, self.on_okButton, self.okButton)
        self.cancelButton = wx.Button(pnl, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)
        self.nextButton = wx.Button(pnl, id=-1, label='Next step')
        self.Bind(wx.EVT_BUTTON, self.on_nextButton, self.nextButton)
        hboxok.Add(self.okButton)
        hboxok.AddSpacer(20)
        hboxok.Add(self.cancelButton )
        hboxok.AddSpacer(20)
        hboxok.Add(self.nextButton )

        #-----------------------
        # design the frame
        #-----------------------
        
        vbox.AddSpacer(10)
        vbox.Add(sbs)
        vbox.AddSpacer(10)
        vbox.Add(hboxok)
        vbox.AddSpacer(10)

        hbox1=wx.BoxSizer(wx.HORIZONTAL)
        hbox1.AddSpacer(10)
        hbox1.Add(vbox)
        hbox1.AddSpacer(10)

        pnl.SetSizer(hbox1)
        hbox1.Fit(self)

    def on_cancelButton(self,event):
        self.Destroy()

    def on_okButton(self,event):
        #print 'self.checked', self.checked_rb
        file_type = self.checked_rb.Label.split()[0] # extracts name of the checked radio button
        #print 'file_type', file_type
        if file_type == 'generic':
            dia = convert_generic_files_to_MagIC(self.WD)
        elif file_type == 'SIO':
            dia = convert_SIO_files_to_MagIC(self.WD)
        elif file_type == 'CIT':
            dia = convert_CIT_files_to_MagIC(self.WD)
        dia.Center()
        dia.Show()


    def OnRadioButtonSelect(self, event):
        #print 'calling OnRadioButtonSelect'
        self.checked_rb = event.GetEventObject()
        #print 'current self.checked_rb', self.checked_rb.Label
#        print '-------------'

    def on_nextButton(self,event):
        self.Destroy()
        combine_dia = combine_magic_dialog(self.WD)
        combine_dia.Show()
        combine_dia.Center()
        
#--------------------------------------------------------------
# MagIC generic files conversion
#--------------------------------------------------------------


class convert_generic_files_to_MagIC(wx.Frame):
    """"""
    title = "PmagPy generic file conversion"

    def __init__(self,WD):
        wx.Frame.__init__(self, None, wx.ID_ANY, self.title)
        self.panel = wx.Panel(self)
        self.max_files=1
        self.WD=WD
        #print 'self.WD on init generic files', self.WD
        self.InitUI()

    def InitUI(self):

        pnl = self.panel

        #---sizer infor ----

        TEXT="A generic file template can be found in www.xxxxx"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_LEFT)
            

        #---sizer 0 ----
        bSizer0 =  wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.VERTICAL )
        self.file_path = wx.TextCtrl(self.panel, id=-1, size=(400,25), style=wx.TE_READONLY)
        self.add_file_button = wx.Button(self.panel, id=-1, label='add',name='add')
        self.Bind(wx.EVT_BUTTON, self.on_add_file_button, self.add_file_button)    
        TEXT="Choose file (no spaces are allowed in path):"
        bSizer0.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_LEFT)
        bSizer0.AddSpacer(5)
        bSizer0_1=wx.BoxSizer(wx.HORIZONTAL)
        bSizer0_1.Add(self.add_file_button,wx.ALIGN_LEFT)
        bSizer0_1.AddSpacer(5)
        bSizer0_1.Add(self.file_path,wx.ALIGN_LEFT)
        bSizer0.Add(bSizer0_1,wx.ALIGN_LEFT)
        
        #---sizer 1 ----
        TEXT="User name (optional):"
        bSizer1 = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.HORIZONTAL )
        bSizer1.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_LEFT)
        bSizer1.AddSpacer(5)
        self.file_info_user = wx.TextCtrl(self.panel, id=-1, size=(100,25))
        bSizer1.Add(self.file_info_user,wx.ALIGN_LEFT)

        #---sizer 2 ----
        TEXT="Experiment:"
        bSizer2 = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.HORIZONTAL )
        self.experiments_names=['Demag (AF and/or Thermal)','Paleointensity-IZZI/ZI/ZI','ATRM 6 positions','AARM 6 positions','cooling rate','NLT']
        self.protocol_info = wx.ComboBox(self.panel, -1, self.experiments_names[0], size=(300,25),choices=self.experiments_names, style=wx.CB_DROPDOWN)
        bSizer2.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_LEFT)
        bSizer2.AddSpacer(5)
        bSizer2.Add(self.protocol_info,wx.ALIGN_LEFT)

        #---sizer 3 ----
        TEXT="Lab field (leave blank if unnecessary). Example: 40 0 -90"
        bSizer3 = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.VERTICAL )
        self.file_info_text=wx.StaticText(self.panel,label=TEXT,style=wx.TE_CENTER)
        self.file_info_Blab = wx.TextCtrl(self.panel, id=-1, size=(40,25))
        self.file_info_Blab_dec = wx.TextCtrl(self.panel, id=-1, size=(40,25))
        self.file_info_Blab_inc = wx.TextCtrl(self.panel, id=-1, size=(40,25))
        gridbSizer3 = wx.GridSizer(2, 3, 0, 10)
        gridbSizer3.AddMany( [(wx.StaticText(self.panel,label="B (uT)",style=wx.TE_CENTER),wx.ALIGN_LEFT),
            (wx.StaticText(self.panel,label="dec",style=wx.TE_CENTER),wx.ALIGN_LEFT),
            (wx.StaticText(self.panel,label="inc",style=wx.TE_CENTER),wx.ALIGN_LEFT),
            (self.file_info_Blab,wx.ALIGN_LEFT),
            (self.file_info_Blab_dec,wx.ALIGN_LEFT),
            (self.file_info_Blab_inc,wx.ALIGN_LEFT)])
        bSizer3.Add(self.file_info_text,wx.ALIGN_LEFT)
        bSizer3.AddSpacer(10)
        bSizer3.Add(gridbSizer3,wx.ALIGN_LEFT)

        #---sizer 4 ----

        #TEXT="Sample-specimen naming convention:"
        bSizer4 = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.VERTICAL )
        #self.sample_specimen_text=wx.StaticText(self.panel,label=TEXT)
        self.sample_naming_conventions=['sample=specimen','no. of initial characters','no. of terminate characters','charceter delimited']
        self.sample_naming_convention = wx.ComboBox(self.panel, -1, self.sample_naming_conventions[0], size=(250,25), choices=self.sample_naming_conventions, style=wx.CB_DROPDOWN)
        self.sample_naming_convention_char = wx.TextCtrl(self.panel, id=-1, size=(40,25))
        gridbSizer4 = wx.GridSizer(2, 2, 0, 10)
        gridbSizer4.AddMany( [(wx.StaticText(self.panel,label="specimen-sample naming convention",style=wx.TE_CENTER),wx.ALIGN_LEFT),
            (wx.StaticText(self.panel,label="delimiter (if necessary)",style=wx.TE_CENTER),wx.ALIGN_LEFT),
            (self.sample_naming_convention,wx.ALIGN_LEFT),
            (self.sample_naming_convention_char,wx.ALIGN_LEFT)])
        #bSizer4.Add(self.sample_specimen_text,wx.ALIGN_LEFT)
        bSizer4.AddSpacer(10)
        bSizer4.Add(gridbSizer4,wx.ALIGN_LEFT)
        
        #---sizer 5 ----

        bSizer5 = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.VERTICAL )
        #bSizer5.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_TOP)
        self.site_naming_conventions=['site=sample','no. of initial characters','no. of terminate characters','charceter delimited']
        self.site_naming_convention_char = wx.TextCtrl(self.panel, id=-1, size=(40,25))
        self.site_naming_convention = wx.ComboBox(self.panel, -1, self.site_naming_conventions[0], size=(250,25), choices=self.site_naming_conventions, style=wx.CB_DROPDOWN)
        gridbSizer5 = wx.GridSizer(2, 2, 0, 10)
        gridbSizer5.AddMany( [(wx.StaticText(self.panel,label="sample-site naming convention",style=wx.TE_CENTER),wx.ALIGN_LEFT),
            (wx.StaticText(self.panel,label="delimiter (if necessary)",style=wx.TE_CENTER),wx.ALIGN_LEFT),
            (self.site_naming_convention,wx.ALIGN_LEFT),
            (self.site_naming_convention_char,wx.ALIGN_LEFT)])
        #bSizer4.Add(self.sample_specimen_text,wx.ALIGN_LEFT)
        bSizer5.AddSpacer(10)
        bSizer5.Add(gridbSizer5,wx.ALIGN_LEFT)

        #---sizer 6 ----
        TEXT="Location name (optional):"
        bSizer6 = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.HORIZONTAL )
        bSizer6.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_LEFT)
        bSizer6.AddSpacer(5)
        self.location= wx.TextCtrl(self.panel, id=-1, size=(100,25))
        bSizer6.Add(self.location,wx.ALIGN_LEFT)


        #---sizer 7 ----
        bSizer7 = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.VERTICAL )
        TEXT="replicate measurements:"
        self.replicate_text=wx.StaticText(self.panel,label=TEXT,style=wx.TE_CENTER)
        self.replicate_rb1 = wx.RadioButton(self.panel, -1, 'Average replicate measurements', style=wx.RB_GROUP)
        self.replicate_rb1.SetValue(True)
        self.replicate_rb2 = wx.RadioButton(self.panel, -1, 'take only last measurement from replicate measurements')
        bSizer7.Add(self.replicate_text,wx.ALIGN_LEFT)
        bSizer7.Add(self.replicate_rb1,wx.ALIGN_LEFT)
        bSizer7.Add(self.replicate_rb2,wx.ALIGN_LEFT)

        #------------------

                     
        self.okButton = wx.Button(self.panel, wx.ID_OK, "&OK")
        self.Bind(wx.EVT_BUTTON, self.on_okButton, self.okButton)

        self.cancelButton = wx.Button(self.panel, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)

        hboxok = wx.BoxSizer(wx.HORIZONTAL)
        hboxok.Add(self.okButton)
        hboxok.Add(self.cancelButton )

        #------
        vbox=wx.BoxSizer(wx.VERTICAL)
        vbox.AddSpacer(10)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(10)
        vbox.Add(bSizer0, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(10)
        vbox.Add(bSizer1, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(10)
        vbox.Add(bSizer2, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(10)
        vbox.Add(bSizer3, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(10)
        vbox.Add(bSizer4, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(10)
        vbox.Add(bSizer5, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(10)
        vbox.Add(bSizer6, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(10)
        vbox.Add(bSizer7, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(10)
        vbox.Add(wx.StaticLine(self.panel), 0, wx.ALL|wx.EXPAND, 5)
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)        
        vbox.AddSpacer(5)

        hbox_all= wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.AddSpacer(vbox)
        hbox_all.AddSpacer(20)
        
        self.panel.SetSizer(hbox_all)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()


    def on_add_file_button(self,event):
        text = "choose file to convert to MagIC"
        pw.on_add_file_button(self, event, text)
#        dlg = wx.FileDialog(
#            None,message="choose file to convert to MagIC",
#            defaultDir=self.WD,
#            defaultFile="",
#            style=wx.OPEN | wx.CHANGE_DIR
#            style=wx.CHANGE_DIR | wx.OPEN
#            )
#        print 'dlg.GetDirectory()', dlg.GetDirectory()
#        if dlg.ShowModal() == wx.ID_OK:
#            self.file_path.SetValue(str(dlg.GetPath()))


    def on_okButton(self,event):

        # generic_magic.py -WD WD - f FILE -fsa er_samples.txt -F OUTFILE.magic -exp [Demag/PI/ATRM 6/AARM 6/CR  -samp X Y -site  X Y -loc LOCNAME -dc B PHI THETA [-A] -WD path 
        
        ErrorMessage=""
        #-----------
        FILE=str(self.file_path.GetValue())
        #-----------
        # WD="/".join(FILE.split("/")[:-1])
        WD=self.WD
        #-----------
        OUTFILE=FILE+".magic"
        #-----------
        EXP=""
        exp=str(self.protocol_info.GetValue())
        if exp=='Demag (AF and/or Thermal)': 
            EXP='Demag'
        elif exp=='Paleointensity-IZZI/ZI/ZI': 
            EXP='PI'
        elif exp=='ATRM 6 positions': 
            EXP='ATRM 6'
        elif exp=='AARM 6 positions': 
            EXP='AARM 6'
        elif exp=='cooling rate': 
            EXP='CR'
        #-----------
        SAMP="1 0" #default
        
        samp_naming_convention=str(self.sample_naming_convention.GetValue())
        try:
            samp_naming_convention_char=int(self.sample_naming_convention_char.GetValue())
        except:
             samp_naming_convention_char="0"
                    
        if samp_naming_convention=='sample=specimen':
            SAMP="1 0"
        elif samp_naming_convention=='no. of initial characters':
            SAMP="0 %i"%int(samp_naming_convention_char)
        elif samp_naming_convention=='no. of terminate characters':
            SAMP="1 %s"%samp_naming_convention_char
        elif samp_naming_convention=='charceter delimited':
            SAMP="2 %s"%samp_naming_convention_char
                        
        #-----------
        
        SITE="1 0" #default
        
        sit_naming_convention=str(self.site_naming_convention.GetValue())
        try:
            sit_naming_convention_char=int(self.site_naming_convention_char.GetValue())
        except:
             sit_naming_convention_char="0"
                    
        if sit_naming_convention=='sample=specimen':
            SITE="1 0"
        elif sit_naming_convention=='no. of initial characters':
            SITE="0 %i"%int(sit_naming_convention_char)
        elif sit_naming_convention=='no. of terminate characters':
            SITE="1 %s"%sit_naming_convention_char
        elif sit_naming_convention=='charceter delimited':
            SITE="2 %s"%sit_naming_convention_char
        
        #-----------        

        if str(self.location.GetValue()) != "":
            LOC="-loc %s"%str(self.location.GetValue())
        else:
            LOC=""
        #-----------        
        
        LABFIELD=" "
        
        B_uT=str(self.file_info_Blab.GetValue())
        DEC=str(self.file_info_Blab_dec.GetValue())
        INC=str(self.file_info_Blab_inc.GetValue())
        
        if EXP != "Demag":
            LABFIELD="-dc "  +B_uT+ " " + DEC + " " + INC

        #-----------        

        DONT_AVERAGE=" "
        if  self.replicate_rb2==True:
            DONT_AVERAGE="-A"   

        #-----------   
        # some special  
                
        COMMAND="generic_magic.py -WD %s -f %s -fsa er_samples.txt -F %s -exp %s  -samp %s -site %s %s %s %s"\
        %(WD,FILE,OUTFILE,EXP,SAMP,SITE,LOC,LABFIELD,DONT_AVERAGE)
       
        print "-I- Running Python command:\n %s"%COMMAND

        #subprocess.call(COMMAND, shell=True)        
        os.system(COMMAND)                                          
        #--
        MSG="file converted to MagIC format file:\n%s.\n\n See Termimal (Mac) or command prompt (windows) for errors"% OUTFILE
        dlg1 = wx.MessageDialog(None,caption="Message:", message=MSG ,style=wx.OK|wx.ICON_INFORMATION)
        dlg1.ShowModal()
        dlg1.Destroy()

        self.Destroy()


    def on_cancelButton(self,event):
        self.Destroy()

    def get_sample_name(self,specimen,sample_naming_convenstion):
        if sample_naming_convenstion[0]=="sample=specimen":
            sample=specimen
        elif sample_naming_convenstion[0]=="no. of terminate characters":
            n=int(sample_naming_convenstion[1])*-1
            sample=specimen[:n]
        elif sample_naming_convenstion[0]=="charceter delimited":
            d=sample_naming_convenstion[1]
            sample_splitted=specimen.split(d)
            if len(sample_splitted)==1:
                sample=sample_splitted[0]
            else:
                sample=d.join(sample_splitted[:-1])
        return sample
                            
    def get_site_name(self,sample,site_naming_convenstion):
        if site_naming_convenstion[0]=="site=sample":
            site=sample
        elif site_naming_convenstion[0]=="no. of terminate characters":
            n=int(site_naming_convenstion[1])*-1
            site=sample[:n]
        elif site_naming_convenstion[0]=="charceter delimited":
            d=site_naming_convenstion[1]
            site_splitted=sample.split(d)
            if len(site_splitted)==1:
                site=site_splitted[0]
            else:
                site=d.join(site_splitted[:-1])
        
        return site
        
#--------------------------------------------------------------
# dialog for combine_magic.py 
#--------------------------------------------------------------


class combine_magic_dialog(wx.Frame):
    """"""
    title = "Combine magic files"

    def __init__(self,WD):
        wx.Frame.__init__(self, None, wx.ID_ANY, self.title)
        self.panel = wx.Panel(self)
        self.max_files = 1
        self.WD=WD
        self.InitUI()

    def InitUI(self):

        pnl = self.panel

        #---sizer infor ----

        TEXT="Step 2: \nCombine different MagIC formatted files to one file name 'magic_measurements.txt'"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_LEFT)
            

        #---sizer 0 ----
        bSizer0 =  wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.HORIZONTAL )
        #self.file_path = wx.TextCtrl(self.panel, id=-1, size=(400,25), style=wx.TE_READONLY)
        self.add_file_button = wx.Button(self.panel, id=-1, label='add file',name='add')
        self.Bind(wx.EVT_BUTTON, self.on_add_file_button, self.add_file_button)    
        self.add_all_files_button = wx.Button(self.panel, id=-1, label="add all files with '.magic' suffix",name='add_all')
        self.Bind(wx.EVT_BUTTON, self.on_add_all_files_button, self.add_all_files_button)    
        #TEXT="Choose file (no spaces are alowd in path):"
        #bSizer0.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_CENTER)
        bSizer0.AddSpacer(5)
        bSizer0.Add(self.add_file_button,wx.ALIGN_LEFT)
        bSizer0.AddSpacer(5)
        bSizer0.Add(self.add_all_files_button,wx.ALIGN_LEFT)
        bSizer0.AddSpacer(5)
                
        #------------------

        bSizer1 =  wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.VERTICAL )
        self.file_pathes = wx.TextCtrl(self.panel, id=-1, size=(800,500), style=wx.TE_MULTILINE)
        #self.add_file_button = wx.Button(self.panel, id=-1, label='add',name='add')
        #self.Bind(wx.EVT_BUTTON, self.on_add_file_button, self.add_file_button)    
        TEXT="files list:"
        bSizer1.AddSpacer(5)
        bSizer1.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_LEFT)        
        bSizer1.AddSpacer(5)
        bSizer1.Add(self.file_pathes,wx.ALIGN_LEFT)
        bSizer1.AddSpacer(5)
                
        #------------------
                     
        self.okButton = wx.Button(self.panel, wx.ID_OK, "&OK")
        self.Bind(wx.EVT_BUTTON, self.on_okButton, self.okButton)

        self.cancelButton = wx.Button(self.panel, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)

        hboxok = wx.BoxSizer(wx.HORIZONTAL)
        hboxok.Add(self.okButton)
        hboxok.Add(self.cancelButton )

        #------
        vbox=wx.BoxSizer(wx.VERTICAL)
        vbox.AddSpacer(10)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(10)
        vbox.Add(bSizer0, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(10)
        vbox.Add(bSizer1, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(10)
        vbox.Add(wx.StaticLine(self.panel), 0, wx.ALL|wx.EXPAND, 5)
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)        
        vbox.AddSpacer(5)

        hbox_all= wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.AddSpacer(vbox)
        hbox_all.AddSpacer(20)
        
        self.panel.SetSizer(hbox_all)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()
                        
    
    def on_add_file_button(self,event):

        dlg = wx.FileDialog(
            None,message="choose MagIC formatted measurement file",
            defaultDir=self.WD,
            defaultFile="",
            style=wx.OPEN | wx.CHANGE_DIR
            )
        if dlg.ShowModal() == wx.ID_OK:
            #self.box_sizer_high_level_text.Add(self.high_level_text_box, 0, wx.ALIGN_LEFT, 0 )  
            self.file_pathes.AppendText(str(dlg.GetPath())+"\n")

    def on_add_all_files_button(self,event):
        all_files=os.listdir(self.WD)
        for F in all_files:
            F=str(F)
            if len(F)>6:
                if F[-6:]==".magic":
                    self.file_pathes.AppendText(F+"\n")
                     
        
        
        
    def on_cancelButton(self,event):
        self.Destroy()

    def on_okButton(self,event):
        files_text=self.file_pathes.GetValue()
        files=files_text.replace(" ","").split('\n')
        print files
        COMMAND="combine_magic.py -F magic_measurements.txt -f %s"%(" ".join(files) )       
        print "-I- Running Python command:\n %s"%COMMAND
        #subprocess.call(COMMAND, shell=True)        
        os.system(COMMAND)                                          
        
        MSG="%i file are merged to one MagIC format file:\n magic_measurements.txt.\n\n See Termimal (Mac) or command prompt (windows) for errors"%(len(files))
        dlg1 = wx.MessageDialog(None,caption="Message:", message=MSG ,style=wx.OK|wx.ICON_INFORMATION)
        dlg1.ShowModal()
        dlg1.Destroy()
        self.Destroy()


class convert_SIO_files_to_MagIC(wx.Frame):
    """stuff"""
    title = "PmagPy SIO file conversion"

    def __init__(self,WD):
        wx.Frame.__init__(self, None, wx.ID_ANY, self.title)
        self.panel = wx.Panel(self)
        self.max_files = 1 # but maybe it could take more??
        self.WD=WD
        self.InitUI()


    def InitUI(self):
        #print 'initializing UI for SIO file conversion'

        #pnl = self.panel

        TEXT = "SIO Format file"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(self, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0 ----
        #replacing self.panel with self for a minute
        
        self.bSizer0 = pw.choose_file(self, method = self.on_add_file_button)

        #---sizer 1 ----
        self.bSizer1 = pw.labeled_text_field(self)

        #---sizer 2 ----
        TEXT = "Experiment type (select all that apply):"
        experiments_names=['Demag', 'Thermal(includes thellier but not trm)', 'Shaw method', 'IRM (acquisition)', '3D IRM experiment', 'NRM only', 'TRM acquisition', 'double AF demag', 'triple AF demag (GRM protocol)', 'Cooling rate experiment']
        self.bSizer2 = pw.check_boxes(self, (5, 3, 0, 0), experiments_names, TEXT)

        #---sizer 3 ----
        self.bSizer3 = pw.lab_field(self)

        #---sizer 4 ----
        self.bSizer4 = pw.select_specimen_ncn(self)

        #---sizer 5 ----
        TEXT="Location name (optional):"
        self.bSizer5 = pw.labeled_text_field(self, TEXT)

        #---sizer 6 ---
        TEXT="Instrument name:"
        self.bSizer6 = pw.labeled_text_field(self, TEXT)

        #---sizer 7 ----
        self.bSizer7 = pw.replicate_measurements(self)

        #---sizer 8 ----

        TEXT = "peak AF field (mT) if ARM: "
        self.bSizer8 = pw.labeled_text_field(self, TEXT)

        #---sizer 9 ----

        TEXT = "Coil number for ASC impulse coil (if treatment units in Volts): "
        self.bSizer9 = pw.labeled_text_field(self, TEXT)

        #---buttons ----

        self.okButton = wx.Button(self, wx.ID_OK, "&OK")
        self.Bind(wx.EVT_BUTTON, self.on_okButton, self.okButton)

        self.cancelButton = wx.Button(self, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)

        hboxok = wx.BoxSizer(wx.HORIZONTAL)
        hboxok.Add(self.okButton)
        hboxok.Add(self.cancelButton )

        #------
        vbox=wx.BoxSizer(wx.VERTICAL)
        vbox.AddSpacer(8)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(8)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(8)
        vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(8)
        vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(8)
        vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(8)
        vbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(8)
        vbox.Add(self.bSizer5, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(8)
        vbox.Add(self.bSizer6, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(8)
        vbox.Add(self.bSizer7, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(8)
        vbox.Add(self.bSizer8, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(8)
        vbox.Add(self.bSizer9, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(8)
        vbox.Add(wx.StaticLine(self), 0, wx.ALL|wx.EXPAND, 5)
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)        
        vbox.AddSpacer(4)

        hbox_all= wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.AddSpacer(vbox)
        hbox_all.AddSpacer(20)
        
        self.SetSizer(hbox_all)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()
        
    def on_cancelButton(self,event):
        self.Destroy()

    def on_add_file_button(self,event):
        text = "choose file to convert to MagIC"
        pw.on_add_file_button(self, event, text)

    def on_okButton(self, event):
        SIO_file = self.bSizer0.return_value()
        user = self.bSizer1.return_value()
        experiment_type = self.bSizer2.return_value()
        lab_field = self.bSizer3.return_value()
        ncn = self.bSizer4.return_value()
        loc_name = self.bSizer5.return_value()
        replicate = self.bSizer6.return_value()
        instrument = self.bSizer7.return_value()
        peak_AF = self.bSizer8.return_value()
        coil_number = self.bSizer9.return_value()
        print "file: {}".format(SIO_file)
        print "user: {}, experiment: {}, lab_field: {}, ncn: {}, loc: {}, replicate: {}, instrument: {}, peak AF: {}, coil number: {}".format(user, experiment_type, lab_field, ncn, loc_name, replicate, instrument, peak_AF, coil_number)
        
        """sio_magic.py  -F /Users/nebula/Desktop/Measurement_Import/CIT_magic/sio_af_example.dat.magic -f /Users/nebula/Desktop/Measurement_Import/CIT_magic/sio_af_example.dat -LP AF -spc 2 -loc "unknown" -ins 2 -ncn 2"""
                        


class convert_CIT_files_to_MagIC(wx.Frame):
    """stuff"""
    title = "PmagPy CIT file conversion"

    def __init__(self,WD):
        wx.Frame.__init__(self, None, wx.ID_ANY, self.title)
        #self.panel = wx.Panel(self)
        self.max_files = 1 # but maybe it could take more??
        self.WD = WD
        self.InitUI()


    def InitUI(self):
        #print 'initializing UI for CIT file conversion'

        #pnl = self.panel

        TEXT = "CIT Format file"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(self, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0 ----
        self.bSizer0 = pw.choose_file(self, 'add', method = self.on_add_file_button)

        #---sizer 1 ----
        TEXT="Measurer (optional):"
        self.bSizer1 = pw.labeled_text_field(self, TEXT)
        
        #---sizer 2 ----
        TEXT = "Sampling Particulars (select all that apply):"
        particulars = ["FS-FD: field sampling done with a drill", "FS-H: field sampling done with hand samples", "FS-LOC-GPS: field location done with GPS", "FS-LOC-MAP:  field location done with map", "SO-POM:  a Pomeroy orientation device was used", "SO-ASC:  an ASC orientation device was used", "SO-MAG: magnetic compass used for all orientations", "SO-SUN: sun compass used for all orientations", "SO-SM: either magnetic or sun used on all orientations", "SO-SIGHT: orientation from sighting"]
        self.bSizer2 = pw.check_boxes(self, (6, 2, 0, 0), particulars, TEXT)
        #print 'dir(bSizer2)', dir(bSizer2)

        #---sizer 3 ----
        self.bSizer3 = pw.lab_field(self)

        #---sizer 4 ----
        self.bSizer4 = pw.select_specimen_ncn(self)

        #---sizer 5 ---
        TEXT = "specify number of characters to designate a specimen, default = 0"
        self.bSizer5 = pw.labeled_text_field(self, TEXT)

        #---sizer 6 ----
        TEXT="Location name (optional):"
        self.bSizer6 = pw.labeled_text_field(self, TEXT)

        #---sizer 7 ---
        TEXT = "peak AF field (mT) if ARM: "
        self.bSizer7 = pw.labeled_text_field(self, TEXT)


        #---buttons ---
        self.okButton = wx.Button(self, wx.ID_OK, "&OK")
        self.Bind(wx.EVT_BUTTON, self.on_okButton, self.okButton)

        self.cancelButton = wx.Button(self, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)

        hboxok = wx.BoxSizer(wx.HORIZONTAL)
        hboxok.Add(self.okButton)
        hboxok.Add(self.cancelButton )

        #------
        vbox=wx.BoxSizer(wx.VERTICAL)
        vbox.AddSpacer(10)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(10)
        vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(10)
        vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(10)
        vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(10)
        vbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(10)
        vbox.Add(self.bSizer5, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(10)
        vbox.Add(self.bSizer6, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(10)
        vbox.Add(self.bSizer7, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(10)
        vbox.Add(wx.StaticLine(self), 0, wx.ALL|wx.EXPAND, 5)
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)        
        vbox.AddSpacer(5)

        hbox_all= wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.AddSpacer(vbox)
        hbox_all.AddSpacer(20)
        
        self.SetSizer(hbox_all)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()


    def on_add_file_button(self,event):
        text = "choose file to convert to MagIC"
        pw.on_add_file_button(self, event, text)

    def on_okButton(self, event):
        wd = self.WD
        full_file = self.bSizer0.return_value()
        ind = full_file.rfind('/')
        CIT_file = full_file[ind+1:] 
        outfile = CIT_file + ".magic"
        user = self.bSizer1.return_value() or "None" # defaults to empty string
        spec_num = self.bSizer5.return_value() or 1 # defaults to 1 if user doesn't provide a number
        loc_name = self.bSizer6.return_value() or "None" # defaults to empty string
        ncn = self.bSizer4.return_value()
        particulars = [p.split(':')[0] for p in self.bSizer2.return_value()]
        particulars = ':'.join(particulars)
        lab_field = self.bSizer3.return_value()
        peak_AF = self.bSizer7.return_value()
        COMMAND = "CIT_magic.py -WD {} -f {} -F {}  -mcd {} -spc {} -loc {} -usr {} -ncn {} -ac {} -dc {}".format(wd, CIT_file, outfile, particulars, spec_num, loc_name, user, ncn, peak_AF, lab_field)
        pw.run_command_and_close_window(self, COMMAND, outfile)

        #print "-I- Running Python command:\n %s"%COMMAND
#        os.system(COMMAND)                                          
#        MSG="file converted to MagIC format file:\n%s.\n\n See Termimal (Mac) or command prompt (windows) for errors"% outfile
#        dlg = wx.MessageDialog(None,caption="Message:", message=MSG ,style=wx.OK|wx.ICON_INFORMATION)
#        dlg.ShowModal()
#        dlg.Destroy()

#        self.Destroy()




    def on_cancelButton(self,event):
        self.Destroy()



#if __name__ == '__main__':
#    print "Hi"
#    app = wx.PySimpleApp()
#    app.frame = combine_magic_dialog( "./")
#    app.frame.Show()
#    app.frame.Center()
#    app.MainLoop()


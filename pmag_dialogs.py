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

class import_magnetometer_data(wx.Dialog):
    def __init__(self,parent,id,title,WD):
        wx.Dialog.__init__(self, parent, id, title)#, size=(300, 300))
        self.WD=WD
        self.InitUI()
        self.SetTitle(title)
        self.parent=parent
        
    def InitUI(self):

        self.panel = wx.Panel(self)
        vbox=wx.BoxSizer(wx.VERTICAL)

        formats=['generic format','SIO format','CIT format','2G-binary format','HUJI format','LDEO format','IODP SRM (csv) format','PMD (ascii) format','TDT format']
        sbs = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, 'step 1: choose file format' ), wx.VERTICAL )

        sbs.AddSpacer(5)
        self.oc_rb0 = wx.RadioButton(self.panel, -1,label=formats[0],name='0', style=wx.RB_GROUP)
        sbs.Add(self.oc_rb0)
        sbs.AddSpacer(5)
        sbs.Add(wx.StaticLine(self.panel), 0, wx.ALL|wx.EXPAND, 5)
        sbs.AddSpacer(5)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioButtonSelect, self.oc_rb0)
        

        for i in range(1,len(formats)):
            command="self.oc_rb%i = wx.RadioButton(self.panel, -1, label='%s', name='%i')"%(i,formats[i],i)
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
        self.okButton =  wx.Button(self.panel, id=-1, label='Import file')
        self.Bind(wx.EVT_BUTTON, self.on_okButton, self.okButton)
        self.cancelButton = wx.Button(self.panel, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)
        self.nextButton = wx.Button(self.panel, id=-1, label='Next step')
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

        self.panel.SetSizer(hbox1)
        hbox1.Fit(self)
    def on_cancelButton(self,event):
        #print 'canceling select file type import dialogue'
        self.Destroy()
    def on_okButton(self,event):
        #print 'self.checked', self.checked_rb
        file_type = self.checked_rb.Label.split()[0] # extracts name of the checked radio button
        #print 'file_type', file_type
        if file_type == 'generic':
            dia = convert_generic_files_to_MagIC(self,self.WD)
        elif file_type == 'SIO':
            dia = convert_SIO_files_to_MagIC(self.WD)
        elif file_type == 'CIT':
            dia = convert_CIT_files_to_MagIC(self.WD)
        elif file_type == '2G-binary':
            dia = convert_2G_binary_files_to_MagIC(self.WD)
        elif file_type == 'HUJI':
            dia = convert_HUJI_files_to_MagIC(self.WD)
        elif file_type == 'LDEO':
            dia = convert_LDEO_files_to_MagIC(self.WD)
        elif file_type == 'IODP':
            dia = convert_IODP_csv_files_to_MagIC(self.WD)
        elif file_type == 'PMD':
            dia = convert_PMD_files_to_MagIC(self.WD)
        #print 'dia', dia, file_type
        dia.Center()
        dia.Show()
        #print 'showed dia'


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

    def __init__(self,parent,WD):
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title)
#        self.panel = wx.Panel(self)
        self.panel = wx.ScrolledWindow(self)
        self.panel.SetScrollbars(20, 20, 50, 50)
        self.max_files=1
        self.WD=WD
        self.parent=parent
        ##print 'self.WD on init generic files', self.WD
        self.InitUI()

    def InitUI(self):

        pnl = self.panel

        #---sizer infor ----

        TEXT="convert generic file to MagIC format"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_LEFT)
            

        #---sizer 0 ----
        bSizer0 = pw.choose_file(pnl, 'add', method = self.on_add_file_button)
        
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
        self.experiments_names=['Demag (AF and/or Thermal)','Paleointensity-IZZI/ZI/ZI','ATRM 6 positions','AARM 6 positions','cooling rate','TRM']
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
        self.sample_naming_conventions=['sample=specimen','no. of initial characters','no. of terminal characters','character delimited']
        self.sample_naming_convention = wx.ComboBox(self.panel, -1, self.sample_naming_conventions[0], size=(250,25), choices=self.sample_naming_conventions, style=wx.CB_DROPDOWN)
        self.sample_naming_convention_char = wx.TextCtrl(self.panel, id=-1, size=(40,25))
        gridbSizer4 = wx.GridSizer(2, 2, 0, 10)
        gridbSizer4.AddMany( [(wx.StaticText(self.panel,label="specimen-sample naming convention",style=wx.TE_CENTER),wx.ALIGN_LEFT),
            (wx.StaticText(self.panel,label="delimiter/number (if necessary)",style=wx.TE_CENTER),wx.ALIGN_LEFT),
            (self.sample_naming_convention,wx.ALIGN_LEFT),
            (self.sample_naming_convention_char,wx.ALIGN_LEFT)])
        #bSizer4.Add(self.sample_specimen_text,wx.ALIGN_LEFT)
        bSizer4.AddSpacer(10)
        bSizer4.Add(gridbSizer4,wx.ALIGN_LEFT)
        
        #---sizer 5 ----

        bSizer5 = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.VERTICAL )
        #bSizer5.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_TOP)
        self.site_naming_conventions=['site=sample','no. of initial characters','no. of terminal characters','character delimited']
        self.site_naming_convention_char = wx.TextCtrl(self.panel, id=-1, size=(40,25))
        self.site_naming_convention = wx.ComboBox(self.panel, -1, self.site_naming_conventions[0], size=(250,25), choices=self.site_naming_conventions, style=wx.CB_DROPDOWN)
        gridbSizer5 = wx.GridSizer(2, 2, 0, 10)
        gridbSizer5.AddMany( [(wx.StaticText(self.panel,label="sample-site naming convention",style=wx.TE_CENTER),wx.ALIGN_LEFT),
            (wx.StaticText(self.panel,label="delimiter/number (if necessary)",style=wx.TE_CENTER),wx.ALIGN_LEFT),
            (self.site_naming_convention,wx.ALIGN_LEFT),
            (self.site_naming_convention_char,wx.ALIGN_LEFT)])
        #bSizer4.Add(self.sample_specimen_text,wx.ALIGN_LEFT)
        bSizer5.AddSpacer(10)
        bSizer5.Add(gridbSizer5,wx.ALIGN_LEFT)

        #---sizer 6 ----
        TEXT="Location name:"
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

        self.helpButton = wx.Button(pnl, wx.ID_ANY, '&Help')
        self.Bind(wx.EVT_BUTTON, self.on_helpButton, self.helpButton)


        hboxok = wx.BoxSizer(wx.HORIZONTAL)
        hboxok.Add(self.okButton, 0, wx.ALL, 5)
        hboxok.Add(self.cancelButton, 0, wx.ALL, 5 )
        hboxok.Add(self.helpButton, 0, wx.ALL, 5)

        #------
        vbox=wx.BoxSizer(wx.VERTICAL)
        vbox.AddSpacer(5)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(5)
        vbox.Add(bSizer0, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(5)
        vbox.Add(bSizer1, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(5)
        vbox.Add(bSizer2, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(5)
        vbox.Add(bSizer3, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(5)
        vbox.Add(bSizer4, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(5)
        vbox.Add(bSizer5, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(5)
        vbox.Add(bSizer6, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(5)
        vbox.Add(bSizer7, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(5)
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
        pw.on_add_file_button(self.panel, self.WD, event, text)
#        dlg = wx.FileDialog(
#            None,message="choose file to convert to MagIC",
#            defaultDir=self.WD,
#            defaultFile="",
#            style=wx.OPEN | wx.CHANGE_DIR
#            style=wx.CHANGE_DIR | wx.OPEN
#            )
#        #print 'dlg.GetDirectory()', dlg.GetDirectory()
#        if dlg.ShowModal() == wx.ID_OK:
#            self.file_path.SetValue(str(dlg.GetPath()))


    def on_okButton(self,event):

        # generic_magic.py -WD WD - f FILE -fsa er_samples.txt -F OUTFILE.magic -exp [Demag/PI/ATRM 6/AARM 6/CR  -samp X Y -site  X Y -loc LOCNAME -dc B PHI THETA [-A] -WD path 
        
        ErrorMessage=""
        #-----------
        FILE=str(self.panel.file_path.GetValue())
        #-----------
        # WD="/".join(FILE.split("/")[:-1])
        WD=self.WD
        magicoutfile=os.path.split(FILE)[1]+".magic"
        OUTFILE=os.path.join(self.WD,magicoutfile)
        #-----------
        #OUTFILE=self.WD+"/"+FILE.split('/')[-1]+".magic"
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
        elif samp_naming_convention=='no. of terminal characters':
            SAMP="1 %s"%samp_naming_convention_char
        elif samp_naming_convention=='character delimited':
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
        elif sit_naming_convention=='no. of terminal characters':
            SITE="1 %s"%sit_naming_convention_char
        elif sit_naming_convention=='character delimited':
            SITE="2 %s"%sit_naming_convention_char
        
        #-----------        

        if str(self.location.GetValue()) != "":
            LOC="-loc \"%s\""%str(self.location.GetValue())
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
        self.parent.Destroy()


    def on_cancelButton(self,event):
        self.Destroy()
        self.parent.Destroy()
        #self.parent.Show()
        #self.parent.Center()
        
    def on_helpButton(self, event):
        pw.on_helpButton("generic_magic.py -h")


    def get_sample_name(self,specimen,sample_naming_convenstion):
        if sample_naming_convenstion[0]=="sample=specimen":
            sample=specimen
        elif sample_naming_convenstion[0]=="no. of terminal characters":
            n=int(sample_naming_convenstion[1])*-1
            sample=specimen[:n]
        elif sample_naming_convenstion[0]=="character delimited":
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
        elif site_naming_convenstion[0]=="no. of terminal characters":
            n=int(site_naming_convenstion[1])*-1
            site=sample[:n]
        elif site_naming_convenstion[0]=="character delimited":
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
        self.panel =  wx.ScrolledWindow(self) #wx.Panel(self)
        self.panel.SetScrollbars(20, 20, 50, 50)
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
        self.file_pathes = wx.TextCtrl(self.panel, id=-1, size=(500,200), style=wx.TE_MULTILINE)
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
        files=files_text.strip('\n').replace(" ","").split('\n')
        COMMAND="combine_magic.py -F magic_measurements.txt -f %s"%(" ".join(files) )       
        print "-I- Running Python command:\n %s"%COMMAND
        #subprocess.call(COMMAND, shell=True)   
        os.chdir(self.WD)     
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
        #print 'init SIO conversion'
        wx.Frame.__init__(self, None, wx.ID_ANY, self.title)
        self.panel = wx.ScrolledWindow(self)
        self.panel.SetScrollbars(20, 20, 50, 50)
        self.max_files = 1 # but maybe it could take more??
        self.WD=WD
        self.InitUI()


    def InitUI(self):
        #print 'init UI'
        pnl = self.panel

        TEXT = "SIO Format file"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)
#        bSizer_info.Add(wx.StaticText(self), wx.ALIGN_LEFT)

        self.bSizer0 = pw.choose_file(pnl, method = self.on_add_file_button)

        #---sizer 1 ----
        self.bSizer1 = pw.labeled_text_field(pnl)

        #---sizer 2 ----
        self.bSizer2 = pw.experiment_type(pnl)

        #---sizer 3 ----
        self.bSizer3 = pw.lab_field(pnl)

        #---sizer 4 ----
        self.bSizer4 = pw.select_specimen_ncn(pnl)

        #---sizer 5 ----
        TEXT="Location name:"
        self.bSizer5 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 6 ---
        TEXT="Instrument name (optional):"
        self.bSizer6 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 7 ----
        self.bSizer7 = pw.replicate_measurements(pnl)

        #---sizer 8 ----

        TEXT = "peak AF field (mT) if ARM: "
        self.bSizer8 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 9 ----

        TEXT = "Coil number for ASC impulse coil (if treatment units in Volts): "
        self.bSizer9 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 10 ---
        self.bSizer10 = pw.synthetic(pnl)

        #---buttons ----

        self.okButton = wx.Button(pnl, wx.ID_OK, "&OK")
        self.Bind(wx.EVT_BUTTON, self.on_okButton, self.okButton)

        self.cancelButton = wx.Button(pnl, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)
        
        self.helpButton = wx.Button(pnl, wx.ID_ANY, '&Help')
        self.Bind(wx.EVT_BUTTON, self.on_helpButton, self.helpButton)

        hboxok = wx.BoxSizer(wx.HORIZONTAL)
        hboxok.Add(self.okButton, 0, wx.ALL, 5)
        hboxok.Add(self.cancelButton, 0, wx.ALL, 5 )
        hboxok.Add(self.helpButton, 0, wx.ALL, 5)

        #------
        vbox=wx.BoxSizer(wx.VERTICAL)
        hbox0 = wx.BoxSizer(wx.HORIZONTAL)
        hbox0.Add(self.bSizer5, flag=wx.ALIGN_LEFT)
        hbox0.Add(self.bSizer6, flag=wx.ALIGN_LEFT|wx.LEFT, border=5)
        hbox1 =wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(self.bSizer8, flag=wx.ALIGN_LEFT)
        hbox1.Add(self.bSizer9, flag=wx.ALIGN_LEFT|wx.LEFT, border=5)

        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=8)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=8)
        vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=8)
        vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=8)
        vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=8)
        vbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.TOP, border=8)
        vbox.Add(hbox0, flag=wx.ALIGN_LEFT|wx.TOP, border=8)
        vbox.Add(self.bSizer7, flag=wx.ALIGN_LEFT|wx.TOP, border=8)
        vbox.Add(hbox1, flag=wx.ALIGN_LEFT|wx.TOP, border=8)
        vbox.Add(self.bSizer10, flag=wx.ALIGN_LEFT|wx.TOP, border=8)
        vbox.Add(wx.StaticLine(pnl), 0, wx.ALL|wx.EXPAND, 5)
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)        
        vbox.Add(wx.StaticLine(pnl), 0, wx.ALL|wx.EXPAND, 5)
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
        SIO_file = self.bSizer0.return_value()
        #outfile = SIO_file + '.magic'
        magicoutfile=os.path.split(SIO_file)[1]+".magic"
        outfile =os.path.join(self.WD,magicoutfile)
        user = self.bSizer1.return_value()
        if user:
            user = "-usr " + user
        experiment_type = self.bSizer2.return_value()
        lab_field = self.bSizer3.return_value()
        if lab_field:
            lab_field = "-dc " + lab_field
        ncn = self.bSizer4.return_value()
        loc_name = self.bSizer5.return_value()
        if loc_name:
            loc_name = "-loc " + loc_name
        #print "loc_name", loc_name
        instrument = self.bSizer6.return_value()
        #print "instrument", instrument
        if instrument:
            instrument = "-ins " + instrument
        replicate = self.bSizer7.return_value()
        if replicate:
            replicate = ''
        else:
            replicate = '-A'
        peak_AF = self.bSizer8.return_value()
        if peak_AF:
            peak_AF = "-ac " + peak_AF
        #print "peak_AF", peak_AF
        coil_number = self.bSizer9.return_value()
        if coil_number:
            coil_number = "-V " + coil_number
        synthetic = self.bSizer10.return_value()
        if synthetic:
            synthetic = '-syn ' + synthetic
        else:
            synthetic = ''
        COMMAND = "sio_magic.py -F {0} -f {1} {2} -LP {3} {4} -ncn {5} {6} {7} {8} {9} {10} {11}".format(outfile, SIO_file, user, experiment_type, loc_name, ncn, lab_field, peak_AF, coil_number, instrument, replicate, synthetic)
        pw.run_command_and_close_window(self, COMMAND, outfile)

    def on_cancelButton(self,event):
        self.Destroy()

    def on_helpButton(self, event):
        pw.on_helpButton("sio_magic.py -h")



class convert_CIT_files_to_MagIC(wx.Frame):
    """stuff"""
    title = "PmagPy CIT file conversion"

    def __init__(self,WD):
        wx.Frame.__init__(self, None, wx.ID_ANY, self.title)
        self.panel = wx.ScrolledWindow(self)
        self.max_files = 1 # but maybe it could take more??
        self.WD = WD
        self.InitUI()


    def InitUI(self):
        #print 'initializing UI for CIT file conversion'

        pnl = self.panel

        TEXT = "CIT Format file"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0 ----
        self.bSizer0 = pw.choose_file(pnl, 'add', method = self.on_add_file_button)

        #---sizer 1 ----
        TEXT="Measurer (optional):"
        self.bSizer1 = pw.labeled_text_field(pnl, TEXT)
        
        #---sizer 2 ----
        TEXT = "Sampling Particulars (select all that apply):"
        particulars = ["FS-FD: field sampling done with a drill", "FS-H: field sampling done with hand samples", "FS-LOC-GPS: field location done with GPS", "FS-LOC-MAP:  field location done with map", "SO-POM:  a Pomeroy orientation device was used", "SO-ASC:  an ASC orientation device was used", "SO-MAG: magnetic compass used for all orientations", "SO-SUN: sun compass used for all orientations", "SO-SM: either magnetic or sun used on all orientations", "SO-SIGHT: orientation from sighting"]
        self.bSizer2 = pw.check_boxes(pnl, (6, 2, 0, 0), particulars, TEXT)

        #---sizer 3 ----
        self.bSizer3 = pw.lab_field(pnl)

        #---sizer 4 ----
        self.bSizer4 = pw.select_specimen_ncn(pnl)

        #---sizer 5 ---
        TEXT = "specify number of characters to designate a specimen, default = 0"
        self.bSizer5 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 6 ----
        TEXT="Location name:"
        self.bSizer6 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 7 ---
        TEXT = "peak AF field (mT) if ARM: "
        self.bSizer7 = pw.labeled_text_field(pnl, TEXT)


        #---buttons ---
        self.okButton = wx.Button(pnl, wx.ID_OK, "&OK")
        self.Bind(wx.EVT_BUTTON, self.on_okButton, self.okButton)

        self.cancelButton = wx.Button(pnl, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)

        self.helpButton = wx.Button(pnl, wx.ID_ANY, '&Help')
        self.Bind(wx.EVT_BUTTON, self.on_helpButton, self.helpButton)

        hboxok = wx.BoxSizer(wx.HORIZONTAL)
        hboxok.Add(self.okButton, 0, wx.ALL, 5)
        hboxok.Add(self.cancelButton, 0, wx.ALL, 5 )
        hboxok.Add(self.helpButton, 0, wx.ALL, 5)

        #------
        vbox=wx.BoxSizer(wx.VERTICAL)

        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer5, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer6, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer7, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.AddSpacer(10)
        vbox.Add(wx.StaticLine(self.panel), 0, wx.ALL|wx.EXPAND, 5)
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
        wd = self.WD
        full_file = self.bSizer0.return_value()
        ind = full_file.rfind('/')
        CIT_file = full_file[ind+1:] 
        magicoutfile=os.path.split(CIT_file)[1]+".magic"
        outfile =os.path.join(self.WD,magicoutfile)

        #outfile = CIT_file + ".magic"
        user = self.bSizer1.return_value()
        if user:
            user = "-usr " + user
        spec_num = self.bSizer5.return_value()
        if spec_num:
            spec_num = "-spc " + spec_num
        else:
            spec_num = "-spc 0" # defaults to 0 if user doesn't choose number
        loc_name = self.bSizer6.return_value()
        if loc_name:
            loc_name = "-loc " + loc_name
        ncn = self.bSizer4.return_value()
        particulars = [p.split(':')[0] for p in self.bSizer2.return_value()]
        particulars = ':'.join(particulars)
        lab_field = self.bSizer3.return_value()
        if lab_field:
            lab_field = "-dc " + lab_field
        peak_AF = self.bSizer7.return_value()
        if peak_AF:
            peak_AF = "-ac " + peak_AF
        COMMAND = "CIT_magic.py -WD {} -f {} -F {}  -mcd {} {} {} {} -ncn {} {} {}".format(wd, CIT_file, outfile, particulars, spec_num, loc_name, user, ncn, peak_AF, lab_field)
        #print COMMAND
        pw.run_command_and_close_window(self, COMMAND, outfile)

    def on_cancelButton(self,event):
        self.Destroy()

    def on_helpButton(self, event):
        pw.on_helpButton("CIT_magic.py -h")



class convert_HUJI_files_to_MagIC(wx.Frame):

    """ """
    title = "PmagPy HUJI file conversion"

    def __init__(self,WD):
        wx.Frame.__init__(self, None, wx.ID_ANY, self.title)
        self.panel = wx.ScrolledWindow(self)
        self.WD = WD
        self.InitUI()

    def InitUI(self):

        pnl = self.panel

        TEXT = "HUJI format file"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0 ----
        self.bSizer0 = pw.choose_file(pnl, 'add', method = self.on_add_file_button)

        #---sizer 1 ----
        self.bSizer1 = pw.labeled_text_field(pnl)

        #---sizer 2 ----
        self.bSizer2 = pw.experiment_type(pnl)

        #---sizer 3 ----
        self.bSizer3 = pw.lab_field(pnl)

        #---sizer 4 ----
        self.bSizer4 = pw.select_specimen_ncn(pnl)

        #---sizer 5 ---
        TEXT = "specify number of characters to designate a specimen, default = 0"
        self.bSizer5 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 6 ----
        TEXT="Location name:"
        self.bSizer6 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 7 ---
        TEXT = "peak AF field (mT) if ARM: "
        self.bSizer7 = pw.labeled_text_field(pnl, TEXT)

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

        #vbox.AddSpacer(10)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.AddSpacer(10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.AddSpacer(10)
        vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.AddSpacer(10)
        vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.AddSpacer(10)
        vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.AddSpacer(10)
        vbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.AddSpacer(10)
        vbox.Add(self.bSizer5, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.AddSpacer(10)
        vbox.Add(self.bSizer6, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.AddSpacer(10)
        vbox.Add(self.bSizer7, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.AddSpacer(10)
        vbox.Add(wx.StaticLine(pnl), 0, wx.ALL|wx.EXPAND, 5)
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
        """
        grab user input values, format them, and run HUJI_magic.py with the appropriate flags
        """
        HUJI_file = self.bSizer0.return_value()
        magicoutfile=os.path.split(HUJI_file)[1]+".magic"
        outfile=os.path.join(self.WD,magicoutfile)
        
        #outfile = HUJI_file + '.magic'
        user = self.bSizer1.return_value()
        if user:
            user = '-usr ' + user
        experiment_type = self.bSizer2.return_value()
        lab_field = self.bSizer3.return_value()
        if lab_field:
            #print 'lab field', lab_field
            lab_field = '-dc ' + lab_field
        ncn = self.bSizer4.return_value()
        spc = self.bSizer5.return_value()
        if not spc:
            spc = '-spc 0'
        else:
            spc = '-spc ' + spc
        loc_name = self.bSizer6.return_value()
        if loc_name:
            loc_name = '-loc ' + loc_name
        peak_AF = self.bSizer7.return_value()
        COMMAND = "HUJI_magic.py -f {} -F {} -LP {} {} {} -ncn {} {} {} {}".format(HUJI_file, outfile, user, experiment_type, loc_name, ncn, lab_field, spc, peak_AF)
        #print 'COMMAND', COMMAND
        pw.run_command_and_close_window(self, COMMAND, outfile)

    def on_cancelButton(self,event):
        self.Destroy()

    def on_helpButton(self, event):
        pw.on_helpButton("HUJI_magic.py -h")


class convert_2G_binary_files_to_MagIC(wx.Frame):

    """PmagPy 2G-binary conversion """
    title = "PmagPy 2G-binary file conversion"

    def __init__(self,WD):
        wx.Frame.__init__(self, None, wx.ID_ANY, self.title)
        self.panel = wx.ScrolledWindow(self)
        self.WD = WD
        self.InitUI()

    def InitUI(self):

        pnl = self.panel

        TEXT = "2G-binary format file"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0 ----
        self.bSizer0 = pw.choose_file(pnl, 'add', method = self.on_add_file_button)

        #---sizer 1 ----
        TEXT = "Sampling Particulars (select all that apply):"
        particulars = ["FS-FD: field sampling done with a drill", "FS-H: field sampling done with hand samples", "FS-LOC-GPS: field location done with GPS", "FS-LOC-MAP:  field location done with map", "SO-POM:  a Pomeroy orientation device was used", "SO-ASC:  an ASC orientation device was used", "SO-MAG: magnetic compass used for all orientations", "SO-SUN: sun compass used for all orientations", "SO-SM: either magnetic or sun used on all orientations", "SO-SIGHT: orientation from sighting"]
        self.bSizer1 = pw.check_boxes(pnl, (6, 2, 0, 0), particulars, TEXT)


        #---sizer 2 ----
        self.bSizer2 = pw.select_specimen_ncn(pnl)

        #---sizer 3 ----
        TEXT = "specify number of characters to designate a specimen, default = 0"
        self.bSizer3 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 4 ----
        self.bSizer4 = pw.select_specimen_ocn(pnl)

        #---sizer 5 ----
        TEXT="Location name:"
        self.bSizer5 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 6 ---
        TEXT="Instrument name (optional):"
        self.bSizer6 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 7 ----
        self.bSizer7 = pw.replicate_measurements(pnl)


        #---buttons ---
        self.okButton = wx.Button(pnl, wx.ID_OK, "&OK")
        self.Bind(wx.EVT_BUTTON, self.on_okButton, self.okButton)

        self.cancelButton = wx.Button(pnl, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)

        self.helpButton = wx.Button(pnl, wx.ID_ANY, '&Help')
        self.Bind(wx.EVT_BUTTON, self.on_helpButton, self.helpButton)

        hboxok = wx.BoxSizer(wx.HORIZONTAL)
        hboxok.Add(self.okButton, 0, wx.ALL, 5)
        hboxok.Add(self.cancelButton, 0, wx.ALL, 5 )
        hboxok.Add(self.helpButton, 0, wx.ALL, 5)

        #------
        vbox=wx.BoxSizer(wx.VERTICAL)

        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer5, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer6, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer7, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(wx.StaticLine(pnl), 0, wx.ALL|wx.EXPAND, 5)
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
        wd = self.WD
        full_file = self.bSizer0.return_value()
        index = full_file.rfind('/')
        file_2G_bin = full_file[index+1:]
        #outfile = file_2G_bin + '.magic'
        magicoutfile=os.path.split(file_2G_bin)[1]+".magic"
        outfile=os.path.join(self.WD,magicoutfile)
        
        sampling = self.bSizer1.return_value()
        ncn = self.bSizer2.return_value()
        spc = self.bSizer3.return_value()
        if not spc:
            spc = '-spc 0'
        else:
            spc = '-spc ' + spc
        ocn = self.bSizer4.return_value()
        loc_name = self.bSizer5.return_value()
        if loc_name:
            loc_name = "-loc " + loc_name
        instrument = self.bSizer6.return_value()
        if instrument:
            instrument = "-ins " + instrument
        replicate = self.bSizer7.return_value()
        if replicate:
            replicate = '-a'
        COMMAND = "2G_bin_magic.py -WD {} -f {} -F {} -ncn {} {} -ocn {} {} {}".format(wd, file_2G_bin, outfile, ncn, spc, ocn, loc_name, replicate)
        #print COMMAND
        pw.run_command_and_close_window(self, COMMAND, outfile)

    def on_cancelButton(self,event):
        self.Destroy()

    def on_helpButton(self, event):
        pw.on_helpButton("2G_bin_magic.py -h")



class convert_LDEO_files_to_MagIC(wx.Frame):

    """ """
    title = "PmagPy LDEO file conversion"

    def __init__(self,WD):
        wx.Frame.__init__(self, None, wx.ID_ANY, self.title)
        self.panel = wx.ScrolledWindow(self)
        self.WD = WD
        self.InitUI()

    def InitUI(self):

        pnl = self.panel

        TEXT = "LDEO format file"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0 ----
        self.bSizer0 = pw.choose_file(pnl, 'add', method = self.on_add_file_button)

        #---sizer 1 ----
        self.bSizer1 = pw.labeled_text_field(pnl)

        #---sizer 2 ---
        self.bSizer2 = pw.experiment_type(pnl)
        
        #---sizer 3 ----
        self.bSizer3 = pw.lab_field(pnl)

        #---sizer 4 ----
        self.bSizer4 = pw.select_specimen_ncn(pnl)

        #---sizer 5 ----
        TEXT = "specify number of characters to designate a specimen, default = 0"
        self.bSizer5 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 6 ---
        TEXT="Location name:"
        self.bSizer6 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 7 ---
        TEXT="Instrument name (optional):"
        self.bSizer7 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 8 ---
        self.bSizer8 = pw.replicate_measurements(pnl)

        #---sizer 9 ----
        TEXT = "peak AF field (mT) if ARM: "
        self.bSizer9 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 10 ---
        TEXT = "Coil number for ASC impulse coil (if treatment units in Volts): "
        self.bSizer10 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 11 ---
        self.bSizer11 = pw.synthetic(pnl)
        

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
        hbox0 = wx.BoxSizer(wx.HORIZONTAL)
        hbox0.Add(self.bSizer6, flag=wx.ALIGN_LEFT|wx.RIGHT, border=5)
        hbox0.Add(self.bSizer7, flag=wx.ALIGN_LEFT)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(self.bSizer9, flag=wx.ALIGN_LEFT|wx.RIGHT, border=5)
        hbox1.Add(self.bSizer10, flag=wx.ALIGN_LEFT)

        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer5, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(hbox0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer8, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(hbox1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer11, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.AddSpacer(10)
        vbox.Add(wx.StaticLine(pnl), 0, wx.ALL|wx.EXPAND, 5)
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER|wx.BOTTOM, border=20)

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
        LDEO_file = self.bSizer0.return_value()
        magicoutfile=os.path.split(LDEO_file)[1]+".magic"
        outfile=os.path.join(self.WD,magicoutfile)
        #outfile = LDEO_file + ".magic"
        user = self.bSizer1.return_value()
        if user:
            user = "-usr " + user
        experiment_type = self.bSizer2.return_value()
        #print experiment_type
        lab_field = self.bSizer3.return_value()
        if lab_field:
            lab_field = "-dc " + lab_field
        ncn = self.bSizer4.return_value()
        spc = self.bSizer5.return_value()
        if spc:
            spc = "-spc " + spc
        else:
            spc = "-spc 0"
        loc_name = self.bSizer6.return_value()
        if loc_name:
            loc_name = "-loc " + loc_name
        instrument = self.bSizer7.return_value()
        if instrument:
            instrument = "-ins " + instrument
        replicate = self.bSizer8.return_value()
        if replicate:
            replicate = ""
        else:
            replicate = "-A"
        AF_field = self.bSizer9.return_value()
        if AF_field:
            AF_field = "-ac " + AF_field
        coil_number = self.bSizer10.return_value()
        if coil_number:
            coil_number = "-V " + coil_number
        synthetic = self.bSizer11.return_value()
        if synthetic:
            synthetic = '-syn ' + synthetic
        else:
            synthetic = ''
        COMMAND = "LDEO_magic.py -f {0} -F {1} {2} -LP {3} {4} -ncn {5} {6} {7} {8} {9} {10} {11} {12}".format(LDEO_file, outfile, user, experiment_type, lab_field, ncn, spc, loc_name, instrument, replicate, AF_field, coil_number, synthetic)
        #print COMMAND
        pw.run_command_and_close_window(self, COMMAND, outfile)

    def on_cancelButton(self,event):
        self.Destroy()

    def on_helpButton(self, event):
        pw.on_helpButton("LDEO_magic.py -h")




class convert_IODP_csv_files_to_MagIC(wx.Frame):

    """ """
    title = "PmagPy IODP csv conversion"

    def __init__(self,WD):
        wx.Frame.__init__(self, None, wx.ID_ANY, self.title)
        self.panel = wx.ScrolledWindow(self)
        self.WD = WD
        self.InitUI()

    def InitUI(self):

        pnl = self.panel

        TEXT = "IODP csv format file"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0 ----
        self.bSizer0 = pw.choose_file(pnl, 'add', method = self.on_add_file_button)

        #---sizer 1 ----
        self.bSizer1 = pw.replicate_measurements(pnl)
        
        #---sizer 2 ----

        #---sizer 3 ----

        #---sizer 4 ----

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
        #vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
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
        wd = self.WD
        full_file = self.bSizer0.return_value()
        index = full_file.rfind('/')
        IODP_file = full_file[index+1:]
        #outfile = IODP_file + ".magic"
        magicoutfile=os.path.split(IODP_file)[1]+".magic"
        outfile=os.path.join(self.WD,magicoutfile)
        replicate = self.bSizer1.return_value()
        if replicate:
            replicate = ''
        else:
            replicate = "-A"
        COMMAND = "IODP_csv_magic.py -WD {0} -f {1} -F {2} {3}".format(wd, IODP_file, outfile, replicate)
        #print COMMAND
        pw.run_command_and_close_window(self, COMMAND, outfile)

    def on_cancelButton(self,event):
        self.Destroy()

    def on_helpButton(self, event):
        pw.on_helpButton("-h")



# template for an import window
class convert_PMD_files_to_MagIC(wx.Frame):

    """ """
    title = "PmagPy PMD (ascii) file conversion"

    def __init__(self,WD):
        wx.Frame.__init__(self, None, wx.ID_ANY, self.title)
        self.panel = wx.ScrolledWindow(self)
        self.WD = WD
        self.InitUI()

    def InitUI(self):

        pnl = self.panel

        TEXT = "PMD format file"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0 ----
        self.bSizer0 = pw.choose_file(pnl, 'add', method = self.on_add_file_button)

        #---sizer 1 ----
        self.bSizer1 = pw.labeled_text_field(pnl)
        
        #---sizer 2 ----
        self.bSizer2 = pw.select_specimen_ncn(pnl)

        #---sizer 3 ---
        TEXT = "specify number of characters to designate a specimen, default = 0"
        self.bSizer3 = pw.labeled_text_field(pnl, TEXT)


        #---sizer 4 ----
        TEXT="Location name:"
        self.bSizer4 = pw.labeled_text_field(pnl, TEXT)


        #---sizer 5 ----
        TEXT = "Sampling Particulars (select all that apply):"
        particulars = ["FS-FD: field sampling done with a drill", "FS-H: field sampling done with hand samples", "FS-LOC-GPS: field location done with GPS", "FS-LOC-MAP:  field location done with map", "SO-POM:  a Pomeroy orientation device was used", "SO-ASC:  an ASC orientation device was used", "SO-MAG: magnetic compass used for all orientations", "SO-SUN: sun compass used for all orientations", "SO-SM: either magnetic or sun used on all orientations", "SO-SIGHT: orientation from sighting"]
        self.bSizer5 = pw.check_boxes(pnl, (6, 2, 0, 0), particulars, TEXT)


        #---sizer 6 ---
        self.bSizer6 = pw.replicate_measurements(pnl)

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
        vbox.Add(self.bSizer5, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer6, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
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
        #print 'doing ok button'
        wd = self.WD
        full_file = self.bSizer0.return_value()
        ind = full_file.rfind('/')
        PMD_file = full_file[ind+1:] 
        magicoutfile=os.path.split(PMD_file)[1]+".magic"
        outfile=os.path.join(self.WD,magicoutfile)
        #outfile = PMD_file + ".magic"
        user = self.bSizer1.return_value()
        if user:
            user = "-usr " + user
        ncn = self.bSizer2.return_value()
        spc = self.bSizer3.return_value()
        loc_name = self.bSizer4.return_value()
        if loc_name:
            loc_name = "-loc " + loc_name
        particulars = self.bSizer5.return_value()
        #print particulars
        replicate = self.bSizer6.return_value()
        COMMAND = "PMD_magic.py -WD {} -f {} {} -ncn {} -spc {} {}".format(wd, PMD_file, user, ncn, spc, replicate)
        print COMMAND
        #pw.run_command_and_close_window(self, COMMAND, outfile)

    def on_cancelButton(self,event):
        self.Destroy()

    def on_helpButton(self, event):
        pw.on_helpButton("PMD_magic.py -h")





#if __name__ == '__main__':
#    print "Hi"
#    app = wx.PySimpleApp()
#    app.frame = combine_magic_dialog( "./")
#    app.frame.Show()
#    app.frame.Center()
#    app.MainLoop()


# template for an import window
class something(wx.Frame):

    """ """
    title = "PmagPy ___ file conversion"

    def __init__(self,WD):
        wx.Frame.__init__(self, None, wx.ID_ANY, self.title)
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
        
        #---sizer 2 ----

        #---sizer 3 ----

        #---sizer 4 ----

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
        #vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
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
        pw.run_command_and_close_window(self, COMMAND, outfile)

    def on_cancelButton(self,event):
        self.Destroy()

    def on_helpButton(self, event):
        pw.on_helpButton("-h")


#=================================================================
# demag_orient:
# read/write demag_orient.txt
# calculate sample orientation
#=================================================================

class OrientFrameGrid(wx.Frame):

    def __init__(self,parent,id,title,WD,Data_hierarchy,size):
        wx.Frame.__init__(self, parent, -1, title, size=size)
        
        #--------------------
        # initialize stuff
        #--------------------
        
        self.WD=WD
        self.Data_hierarchy=Data_hierarchy
        
        #--------------------
        # menu bar
        #--------------------
        
        self.menubar = wx.MenuBar()
        menu_file = wx.Menu()
        m_open_file = menu_file.Append(-1, "&Open orientation file", "")
        self.Bind(wx.EVT_MENU, self.on_m_open_file, m_open_file)
        m_save_file = menu_file.Append(-1, "&Save orientation file", "")
        self.Bind(wx.EVT_MENU, self.on_m_save_file, m_save_file)
        m_calc_orient = menu_file.Append(-1, "&Calculate samples orientation", "")
        self.Bind(wx.EVT_MENU, self.on_m_calc_orient, m_calc_orient)
        self.menubar.Append(menu_file, "&File")
        self.SetMenuBar(self.menubar)

        #--------------------
        # get the orientation data
        # 1) from file  demag_orient.txt
        # 2) from Data_hierarchy
        # and save it to self.orient_data={}
        #--------------------

        self.samples_list=self.Data_hierarchy['samples']         
        self.orient_data={}
        try:
            self.orient_data=self.read_magic_file(self.WD+"/demag_orient.txt",1,"sample_name")  
        except:
            pass
        for sample in self.samples_list:
            if sample not in self.orient_data.keys():
               self.orient_data[sample]={} 
               self.orient_data[sample]["sample_name"]=sample
               
            if sample in Data_hierarchy['site_of_sample'].keys():
                self.orient_data[sample]["site_name"]=Data_hierarchy['site_of_sample'][sample]
            else:
                self.orient_data[sample]["site_name"]=""

        #--------------------
        # create the grid sheet
        #--------------------
                                    
        self.create_sheet()
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        # save the template
        self.on_m_save_file(None)
        self.Show()                

        TEXT="A template for a file named 'demag_orient.txt', which contains samples orientation data was created in MagIC working directory.\n\n"
        TEXT=TEXT+"You can view/modify demag_orient.txt using this Python frame, or using Excel.\n\n"
        TEXT=TEXT+"If you choose to use Excel:\n"
        TEXT=TEXT+"1) Fill in data.\n"        
        TEXT=TEXT+"2) Save file as 'tab delimited'\n"
        TEXT=TEXT+"3) Import demag_orient.txt to the Python frame by choosing from the menu-bar: File -> Open orientation file\n\n"
        TEXT=TEXT+"After orientation data is filled in the Python frame choose from the menu-bar: File -> Calculate samples orientations"
        dlg1 = wx.MessageDialog(self,caption="Message:", message=TEXT ,style=wx.OK)
        result = dlg1.ShowModal()
        if result == wx.ID_OK:
            dlg1.Destroy()    
    
            
    def create_sheet(self):    
        '''
        creat an editable grid showing deamg_orient.txt 
        '''
        #--------------------------------
        # orient.tx support many other headers
        # but here I put only 
        # the essential headers for 
        # sample orientation
        #--------------------------------
        
        self.headers=["sample_orientation_flag",
                 "sample_name",
                 #"site_name",
                 "mag_azimuth",
                 "field_dip",
                 "bedding_dip_direction",
                 "bedding_dip",
                 "shadow_angle",
                 "lat",
                 "long",
                 "date",
                 "hhmm",
                 "GPS_baseline",
                 "GPS_Az",
                 #"participants",
                 #"magic_method_codes"
                 ]

        #--------------------------------
        # creat the grid
        #--------------------------------
        
        samples_list=self.orient_data.keys()
        samples_list.sort()
        self.samples_list = [ sample for sample in samples_list if sample is not "" ] 
        self.grid = wx.grid.Grid(self, -1)        
        self.grid.ClearGrid()
        self.grid.CreateGrid(len(self.samples_list), len(self.headers))

        #--------------------------------
        # color the columns by groups 
        #--------------------------------
        
        for i in range(len(self.samples_list)):
            self.grid.SetCellBackgroundColour(i, 0, "LIGHT GREY")
            self.grid.SetCellBackgroundColour(i, 1, "LIGHT STEEL BLUE")
            self.grid.SetCellBackgroundColour(i, 2, "YELLOW")
            self.grid.SetCellBackgroundColour(i, 3, "YELLOW")
            self.grid.SetCellBackgroundColour(i, 4, "PALE GREEN")
            self.grid.SetCellBackgroundColour(i, 5, "PALE GREEN")
            self.grid.SetCellBackgroundColour(i, 6, "LIGHT BLUE")
            self.grid.SetCellBackgroundColour(i, 7, "LIGHT BLUE")
            self.grid.SetCellBackgroundColour(i, 8, "LIGHT BLUE")
            self.grid.SetCellBackgroundColour(i, 9, "LIGHT BLUE")
            self.grid.SetCellBackgroundColour(i, 10, "LIGHT BLUE")
            self.grid.SetCellBackgroundColour(i, 11, "LIGHT MAGENTA")
            self.grid.SetCellBackgroundColour(i, 12, "LIGHT MAGENTA")
        
        #--------------------------------
        # fill headers names
        #--------------------------------
        
        for i in range(len(self.headers)):
            self.grid.SetColLabelValue(i, self.headers[i])

        #--------------------------------
        # fill data from self.orient_data
        #--------------------------------
        
        for sample in self.samples_list:
            for key in self.orient_data[sample].keys():
                if key in self.headers:
                    sample_index=self.samples_list.index(sample)
                    i=self.headers.index(key)
                    self.grid.SetCellValue(sample_index,i, self.orient_data[sample][key])
                        
        #--------------------------------

        self.grid.AutoSize()
        
                
    def on_m_open_file(self,event):
        '''
        open orient.txt
        read the data
        display the data from the file in a new grid
        '''
        dlg = wx.FileDialog(
            self, message="choose orient file",
            defaultDir=self.WD, 
            defaultFile="",
            style=wx.OPEN | wx.CHANGE_DIR
            )
        if dlg.ShowModal() == wx.ID_OK:
            orient_file = dlg.GetPath()
            dlg.Destroy()
            new_data=self.read_magic_file(orient_file,1,"sample_name") 
            if len(new_data)>0:
                self.orient_data={}
                self.orient_data=new_data
            self.create_sheet()

    def on_m_save_file(self,event):
        
        '''
        save demag_orient.txt
        (only the columns that appear on the grid frame)
        '''
        
        fout=open(self.WD+"/demag_orient.txt",'w')
        STR="tab\tdemag_orient\n"
        fout.write(STR)
        STR="\t".join(self.headers)+"\n"
        fout.write(STR)
        for sample in self.samples_list:
            STR=""
            for header in self.headers:                
                sample_index=self.samples_list.index(sample)
                i=self.headers.index(header)
                value=self.grid.GetCellValue(sample_index,i)
                STR=STR+value+"\t"
            fout.write(STR[:-1]+"\n")
        if event!=None: 
            dlg1 = wx.MessageDialog(None,caption="Message:", message="data saved in file demag_orient.txt" ,style=wx.OK|wx.ICON_INFORMATION)
            dlg1.ShowModal()
            dlg1.Destroy()
        
    def read_magic_file(self,path,ignore_lines_n,sort_by_this_name):
        '''
        read magic file and store the data in dictionary:
        Data={}
        Data[sort_by_this_name]={}
        '''

        DATA={}
        fin=open(path,'rU')
        #ignore first lines
        for i in range(ignore_lines_n):
            fin.readline()
        #header
        line=fin.readline()
        header=line.strip('\n').split('\t')
        #print header
        for line in fin.readlines():
            if line[0]=="#":
                continue
            tmp_data={}
            tmp_line=line.strip('\n').split('\t')
            #print tmp_line
            for i in range(len(tmp_line)):
                if i>= len(header):
                    continue
                tmp_data[header[i]]=tmp_line[i]
            DATA[tmp_data[sort_by_this_name]]=tmp_data
        fin.close()        
        return(DATA)
                

    def on_m_calc_orient(self,event):    
        '''
        This fucntion does exactly what the 'import orientation' fuction does in MagIC.py 
        after some dialog boxes the fucntio calls orientation_magic.py 
        '''
        
        # first see if demag_orient.txt
        self.on_m_save_file(None)
        orient_convention_dia=orient_convention(None)
        orient_convention_dia.Center()
        #orient_convention_dia.ShowModal()
        if orient_convention_dia.ShowModal() == wx.ID_OK:
            ocn_flag=orient_convention_dia.ocn_flag
            dcn_flag=orient_convention_dia.dcn_flag
            gmt_flags=orient_convention_dia.gmt_flags
            orient_convention_dia.Destroy()
        
        method_code_dia=method_code_dialog(None)
        method_code_dia.Center()
        if method_code_dia.ShowModal()== wx.ID_OK:
            bedding_codes_flags=method_code_dia.bedding_codes_flags
            methodcodes_flags=method_code_dia.methodcodes_flags
            method_code_dia.Destroy()
        #logfile=open(self.WD+"/orientation_magic.log",'w')
        command_args=['orientation_magic.py']
        command_args.append("-WD %s"%self.WD)
        command_args.append("-Fsa er_samples_orient.txt")
        command_args.append("-Fsi er_sites_orient.txt ")
        command_args.append("-f %s"%"demag_orient.txt")
        command_args.append(ocn_flag)
        command_args.append(dcn_flag)
        command_args.append(gmt_flags)
        command_args.append(bedding_codes_flags)
        command_args.append(methodcodes_flags) 
        commandline=" ".join(command_args)
        
                 
        #command= "orientation_magic.py -WD %s -Fsa er_samples_orient.txt -Fsi er_sites_orient.txt -f  %s %s %s %s %s %s > ./orientation_magic.log " \
        #%(self.WD,\
        #"demag_orient.txt",\
        #ocn_flag,\
        #dcn_flag,\
        #gmt_flags,\
        #bedding_codes_flags,\
        #methodcodes_flags)
        
        #orient_convention_dia.Destroy()
        #method_code_dia.Destroy()  
        
        fail_comamnd=False
        
        print "-I- executing command: %s" %commandline
        os.chdir(self.WD)
        try:
             os.system(commandline)
             #subprocess.call(command_args,shell=True,stdout=logfile)
             #logfile.close()
        except:
            fail_comamnd=True
        
        if fail_comamnd:
            print "-E- ERROR: Error in running orientation_magic.py"
            return
 
        # check if orientation_magic.py finished sucsessfuly
        data_saved=False
        if os.path.isfile(self.WD+"/er_samples_orient.txt"):
            data_saved=True
            #fin=open(self.WD+"/orientation_magic.log",'r')
            #for line in fin.readlines():
            #    if "Data saved in" in line:
            #        data_saved=True
            #        break 
        
        if not data_saved:
            return
        
        # check if er_samples.txt exists. 
        # If yes add/change the following columns:
        # 1) sample_azimuth,sample_dip
        # 2) sample_bed_dip, sample_bed_dip_direction
        # 3) sample_date,
        # 4) sample_declination_correction
        # 5) add magic_method_codes
        
        er_samples_data={}
        er_samples_orient_data={}
        if os.path.isfile(self.WD+"/er_samples.txt"):
            er_samples_file=self.WD+"/er_samples.txt"
            er_samples_data=self.read_magic_file(er_samples_file,1,"er_sample_name")
        
        if os.path.isfile(self.WD+"/er_samples_orient.txt"):             
            er_samples_orient_file=self.WD+"/er_samples_orient.txt"
            er_samples_orient_data=self.read_magic_file(er_samples_orient_file,1,"er_sample_name")
        new_samples_added=[]
        for sample in er_samples_orient_data.keys():
            if sample not in er_samples_data.keys():
                new_samples_added.append(sample)
                er_samples_data[sample]={}
                er_samples_data[sample]['er_sample_name']=sample
              #er_samples_data[sample]['er_citation_names']=
                #continue
                #er_samples_data[sample]={}
                #er_samples_data[sample]["er_sample_name"]=sample
            for key in ["sample_orientation_flag","sample_azimuth","sample_dip","sample_bed_dip","sample_bed_dip_direction","sample_date","sample_declination_correction"]:
                if key in er_samples_orient_data[sample].keys():
                    er_samples_data[sample][key]=er_samples_orient_data[sample][key]
            if "magic_method_codes" in er_samples_orient_data[sample].keys():
                if "magic_method_codes" in er_samples_data[sample].keys():
                    codes=er_samples_data[sample]["magic_method_codes"].strip("\n").replace(" ","").replace("::",":").split(":")
                else:
                    codes=[]
                new_codes=er_samples_orient_data[sample]["magic_method_codes"].strip("\n").replace(" ","").replace("::",":").split(":")
                all_codes=codes+new_codes
                all_codes=list(set(all_codes)) # remove duplicates
                er_samples_data[sample]["magic_method_codes"]=":".join(all_codes)
        samples=er_samples_data.keys()
        samples.sort()
        er_recs=[]
        for sample in samples:
            er_recs.append(er_samples_data[sample])
            pmag.magic_write(self.WD+"/er_samples.txt",er_recs,"er_samples")
       
        dlg1 = wx.MessageDialog(None,caption="Message:", message="orientation data is saved/appended to er_samples.txt" ,style=wx.OK|wx.ICON_INFORMATION)
        dlg1.ShowModal()
        dlg1.Destroy()
        
        if len(new_samples_added)>0:
            dlg1 = wx.MessageDialog(None,caption="Warning:", message="The following samples were added to er_samples.txt:\n %s "%(" , ".join(new_samples_added)) ,style=wx.OK|wx.ICON_INFORMATION)
            dlg1.ShowModal()
            dlg1.Destroy()
            
        self.Destroy()    
                    
        
    def OnCloseWindow(self,event):   
        dlg1 = wx.MessageDialog(self,caption="Message:", message="Save changes to demag_orient.txt?\n " ,style=wx.OK|wx.CANCEL)
        result = dlg1.ShowModal()
        if result == wx.ID_OK:
            self.on_m_save_file(None)
            dlg1.Destroy()    
            self.Destroy()
        if result == wx.ID_CANCEL:
            dlg1.Destroy()    
            self.Destroy()

                     

                


class orient_convention(wx.Dialog):
    
    def __init__(self, *args, **kw):
        super(orient_convention, self).__init__(*args, **kw) 
            
        self.InitUI()
        #self.SetSize((250, 200))
        self.SetTitle("set orientation convention")
        
    def InitUI(self):


        pnl = wx.Panel(self)        
        vbox=wx.BoxSizer(wx.VERTICAL)

        #-----------------------
        # orientation convention
        #-----------------------

        sbs = wx.StaticBoxSizer( wx.StaticBox( pnl, wx.ID_ANY, 'orientation convention' ), wx.VERTICAL )

        sbs.AddSpacer(5)
        self.oc_rb1 = wx.RadioButton(pnl, -1,label='Pomeroy: Lab arrow azimuth = mag_azimuth; Lab arrow dip=-field_dip (field_dip is hade)',name='1', style=wx.RB_GROUP)
        sbs.Add(self.oc_rb1)             
        sbs.AddSpacer(5)
        self.oc_rb2 = wx.RadioButton(pnl, -1, label='Lab arrow azimuth = mag_azimuth-90 (mag_azimuth is strike); Lab arrow dip = -field_dip', name='2')
        sbs.Add(self.oc_rb2)             
        sbs.AddSpacer(5)
        self.oc_rb3 = wx.RadioButton(pnl, -1, label='Lab arrow azimuth = mag_azimuth; Lab arrow dip = 90-field_dip (field_dip is inclination of lab arrow)', name='3')        
        sbs.Add(self.oc_rb3)             
        sbs.AddSpacer(5)
        self.oc_rb4 = wx.RadioButton(pnl, -1, label='Lab arrow azimuth and dip are same as mag_azimuth, field_dip',  name='4')        
        sbs.Add(self.oc_rb4)             
        sbs.AddSpacer(5)
        self.oc_rb5 = wx.RadioButton(pnl, -1, label='ASC: Lab arrow azimuth and dip are mag_azimuth, field_dip-90 (field arrow is inclination of specimen Z direction)',name='5')        
        sbs.Add(self.oc_rb5)             
        sbs.AddSpacer(5)
        self.oc_rb6 = wx.RadioButton(pnl, -1, label='Lab arrow azimuth = mag_azimuth-90 (mag_azimuth is strike); Lab arrow dip = 90-field_dip', name='6')        
        sbs.Add(self.oc_rb6)             
        sbs.AddSpacer(5)        
        
         
        #-----------------------
        # declination correction
        #-----------------------                
        sbs2 = wx.StaticBoxSizer( wx.StaticBox( pnl, wx.ID_ANY, 'declination correction' ), wx.VERTICAL )
        hbox_dc1 = wx.BoxSizer(wx.HORIZONTAL)

        sbs2.AddSpacer(5)
        self.dc_rb1 = wx.RadioButton(pnl, -1, 'Use the IGRF DEC value at the lat/long and date supplied', (10, 50), style=wx.RB_GROUP)        
        self.dc_rb2 = wx.RadioButton(pnl, -1, 'Use this DEC:', (10, 50))        
        self.dc_tb2 = wx.TextCtrl(pnl,style=wx.CENTER)
        self.dc_rb3 = wx.RadioButton(pnl, -1, 'DEC=0, mag_az is already corrected in file', (10, 50))        
        
        sbs2.Add(self.dc_rb1)
        sbs2.AddSpacer(5)
        hbox_dc1.Add(self.dc_rb2)
        hbox_dc1.AddSpacer(5)
        hbox_dc1.Add(self.dc_tb2)
        sbs2.Add(hbox_dc1)
        
        sbs2.AddSpacer(5)
        sbs2.Add(self.dc_rb3)
        sbs2.AddSpacer(5)
        
        
        #-----------------------
        # orienation priority
        #-----------------------                
        sbs3 = wx.StaticBoxSizer( wx.StaticBox( pnl, wx.ID_ANY, 'orientation priority' ), wx.VERTICAL )

        sbs3.AddSpacer(5)
        self.op_rb1 = wx.RadioButton(pnl, -1, label='1) differential GPS 2) sun compass 3) magnetic compass',name='1', style=wx.RB_GROUP)
        sbs3.Add(self.op_rb1)             
        sbs3.AddSpacer(5)
        self.op_rb2 = wx.RadioButton(pnl, -1, label='1) differential GPS 2) magnetic compass 3) sun compass ', name='2')
        sbs3.Add(self.op_rb2)             
        sbs3.AddSpacer(5)


        #-----------------------
        #  add local time for GMT
        #-----------------------                

        sbs4 = wx.StaticBoxSizer( wx.StaticBox( pnl, wx.ID_ANY, 'add local time' ), wx.HORIZONTAL )
        #hbox_alt = wx.BoxSizer(wx.HORIZONTAL)
        
        sbs4.AddSpacer(5)
        self.dc_alt = wx.TextCtrl(pnl,style=wx.CENTER)
        #alt_txt = wx.StaticText(pnl,label="Hours to ADD local time for GMT, default is 0",style=wx.TE_CENTER)
        alt_txt = wx.StaticText(pnl,label="Hours to SUBTRACT from local time for GMT, default is 0",style=wx.TE_CENTER)        
        sbs4.Add(alt_txt)
        sbs4.AddSpacer(5)
        sbs4.Add(self.dc_alt)

        #-----------------------
        # OK button
        #-----------------------                
              
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.okButton = wx.Button(pnl, wx.ID_OK, "&OK")
        self.Bind(wx.EVT_BUTTON, self.OnOK, self.okButton)
        hbox2.Add(self.okButton)
        
        #-----------------------
        # design the frame
        #-----------------------                
        
        vbox.AddSpacer(10)
        vbox.Add(sbs)
        vbox.AddSpacer(10)
        vbox.Add(sbs2)
        vbox.AddSpacer(10)
        vbox.Add(sbs3)
        vbox.AddSpacer(10)
        vbox.Add(sbs4)
        vbox.AddSpacer(10)
        vbox.Add(hbox2)
        vbox.AddSpacer(10)

        hbox1=wx.BoxSizer(wx.HORIZONTAL)        
        hbox1.AddSpacer(10)
        hbox1.Add(vbox)
        hbox1.AddSpacer(10)

        pnl.SetSizer(hbox1)
        hbox1.Fit(self)


        #-----------------------                
        # intialize defalut value
        #-----------------------                
        
        self.oc_rb4.SetValue(True)
        self.dc_rb1.SetValue(True)        
        self.op_rb1.SetValue(True)   
        
    def OnOK(self, e):
        self.ocn=""
        if self.oc_rb1.GetValue()==True:self.ocn="1"
        if self.oc_rb2.GetValue()==True:self.ocn="2"
        if self.oc_rb3.GetValue()==True:self.ocn="3"
        if self.oc_rb4.GetValue()==True:self.ocn="4"
        if self.oc_rb5.GetValue()==True:self.ocn="5"
        if self.oc_rb6.GetValue()==True:self.ocn="6"

        self.dcn=""
        if self.dc_rb1.GetValue()==True:self.dcn="1"
        if self.dc_rb2.GetValue()==True:
            self.dcn="2"
            try:
                float(self.dc_tb2.GetValue())
            except:
                dlg1 = wx.MessageDialog(None,caption="Error:", message="Add declination" ,style=wx.OK|wx.ICON_INFORMATION)
                dlg1.ShowModal()
                dlg1.Destroy()
                
        if self.dc_rb3.GetValue()==True:self.dcn="3"
        
        if self.op_rb1.GetValue()==True:self.op="1"
        if self.op_rb2.GetValue()==True:self.op="2"
        
        if self.dc_alt.GetValue()!="":
            try:
                float(self.dc_alt.GetValue())
                gmt_flags="-gmt " + self.dc_alt.GetValue()
            except:
                gmt_flags=""
        else:
            gmt_flags=""        
        #-------------
        self.ocn_flag="-ocn "+ self.ocn
        self.dcn_flag="-dcn "+ self.dcn
        self.gmt_flags=gmt_flags
        self.EndModal(wx.ID_OK)
        #self.Close()


class method_code_dialog(wx.Dialog):
    
    def __init__(self, *args, **kw):
        super(method_code_dialog, self).__init__(*args, **kw) 
            
        self.InitUI()
        self.SetTitle("additional required information")
        
    def InitUI(self):

        pnl = wx.Panel(self)        
        vbox=wx.BoxSizer(wx.VERTICAL)

        #-----------------------
        # MagIC codes
        #-----------------------
        
        sbs1 = wx.StaticBoxSizer( wx.StaticBox( pnl, wx.ID_ANY, 'MagIC codes' ), wx.VERTICAL )
        self.cb1 = wx.CheckBox(pnl, -1, 'FS-FD: field sampling done with a drill')
        self.cb2 = wx.CheckBox(pnl, -1, 'FS-H: field sampling done with hand sample')
        self.cb3 = wx.CheckBox(pnl, -1, 'FS-LOC-GPS: field location done with GPS')
        self.cb4 = wx.CheckBox(pnl, -1, 'FS-LOC-MAP:  field location done with map')
        self.cb5 = wx.CheckBox(pnl, -1, 'SO-POM:  a Pomeroy orientation device was used')
        self.cb6 = wx.CheckBox(pnl, -1, 'SO-ASC:  an ASC orientation device was used')
        self.cb7 = wx.CheckBox(pnl, -1, 'SO-MAG: magnetic compass used for all orientations')
        self.cb8 = wx.CheckBox(pnl, -1, 'SO-SUN: sun compass used for all orientations')
        self.cb9 = wx.CheckBox(pnl, -1, 'SO-SM: either magnetic or sun used on all orientations    ')
        self.cb10 = wx.CheckBox(pnl, -1, 'SO-SIGHT: orientation from sighting')

        sbs1.Add(self.cb1);sbs1.AddSpacer(5)
        sbs1.Add(self.cb2);sbs1.AddSpacer(5)
        sbs1.Add(self.cb3);sbs1.AddSpacer(5)
        sbs1.Add(self.cb4);sbs1.AddSpacer(5)
        sbs1.Add(self.cb5);sbs1.AddSpacer(5)
        sbs1.Add(self.cb6);sbs1.AddSpacer(5)
        sbs1.Add(self.cb7);sbs1.AddSpacer(5)
        sbs1.Add(self.cb8);sbs1.AddSpacer(5)
        sbs1.Add(self.cb9);sbs1.AddSpacer(5)
        sbs1.Add(self.cb10);sbs1.AddSpacer(5)

        #-----------------------
        # Bedding convention
        #-----------------------
        
        sbs2 = wx.StaticBoxSizer( wx.StaticBox( pnl, wx.ID_ANY, 'bedding convention' ), wx.VERTICAL )
        self.bed_con1 = wx.CheckBox(pnl, -1, 'Take fisher mean of bedding poles?')
        self.bed_con2 = wx.CheckBox(pnl, -1, "Don't correct bedding dip direction with declination - already correct")

        sbs2.Add(self.bed_con1);sbs1.AddSpacer(5)
        sbs2.Add(self.bed_con2);sbs1.AddSpacer(5)

        #-----------------------
        # OK button
        #-----------------------                
              
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.okButton = wx.Button(pnl, wx.ID_OK, "&OK")
        self.Bind(wx.EVT_BUTTON, self.OnOK, self.okButton)
        hbox2.Add(self.okButton)

        #-----------------------
        # design the frame
        #-----------------------                
        vbox.Add(sbs1)
        vbox.AddSpacer(5)
        vbox.Add(sbs2)
        vbox.AddSpacer(5)
        vbox.Add(hbox2)
        vbox.AddSpacer(10)
        
        hbox1=wx.BoxSizer(wx.HORIZONTAL)        
        hbox1.AddSpacer(10)
        hbox1.Add(vbox)
        hbox1.AddSpacer(10)

        pnl.SetSizer(hbox1)
        hbox1.Fit(self)

    def OnOK(self, e):
        methodcodes=[]
        if self.cb1.GetValue() ==True:
            methodcodes.append('FS-FD')
        if self.cb2.GetValue() ==True:
            methodcodes.append('FS-H')
        if self.cb3.GetValue() ==True:
            methodcodes.append('FS-LOC-GPS')
        if self.cb4.GetValue() ==True:
            methodcodes.append('FS-LOC-MAP')
        if self.cb5.GetValue() ==True:
            methodcodes.append('SO-POM')
        if self.cb6.GetValue() ==True:
            methodcodes.append('SO-ASC')
        if self.cb7.GetValue() ==True:
            methodcodes.append('SO-MAG')
        if self.cb8.GetValue() ==True:
            methodcodes.append('SO-SUN')
        if self.cb9.GetValue() ==True:
            methodcodes.append('SO-SM')
        if self.cb10.GetValue() ==True:
            methodcodes.append('SO-SIGHT')
        
        if methodcodes==[]:
            self.methodcodes_flags=""
        else:
            self.methodcodes_flags="-mcd "+":".join(methodcodes)
        
        bedding_codes=[]
        
        if self.bed_con1.GetValue() ==True:
            bedding_codes.append("-a")
        if self.bed_con2.GetValue() ==True:
            bedding_codes.append("-BCN")
        
        self.bedding_codes_flags=" ".join(bedding_codes)   
        self.EndModal(wx.ID_OK) 
        #self.Close()



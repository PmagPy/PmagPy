#!/usr/bin/env pythonw

#--------------------------------------------------------------
# converting magnetometer files to MagIC format
#--------------------------------------------------------------
import wx
import wx.grid
import os
import subprocess
import sys
import pmagpy.pmag as pmag
import pmagpy.ipmag as ipmag
import pmagpy.check_updates as check_updates
import dialogs.pmag_widgets as pw
import dialogs.drop_down_menus as drop_down_menus
import dialogs.magic_grid as magic_grid
sys.path.append("../programs") #later fix imports further down in code to "from programs import ...." also imports should be moved to top of file unless import is so large it slows down the program


class import_magnetometer_data(wx.Dialog):
    def __init__(self, parent, id, title, WD):
        wx.Dialog.__init__(self, parent, id, title, name='import_magnetometer_data')
        self.WD = WD
        self.InitUI()
        self.SetTitle(title)
        self.parent = parent

    def InitUI(self):
        self.panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        formats = ['generic format','SIO format','CIT format','2G-binary format',
                   'HUJI format','LDEO format','IODP SRM (csv) format','PMD (ascii) format',
                   'TDT format', 'JR6 format', "BGC format"]
        sbs = wx.StaticBoxSizer(wx.StaticBox(self.panel, wx.ID_ANY, 'step 1: choose file format'), wx.VERTICAL)
        sbs.AddSpacer(5)

        radio_buttons = []
        for fmt in formats:
            radio_button = wx.RadioButton(self.panel, -1, label=fmt, name=fmt)
            radio_buttons.append(radio_button)
            sbs.Add(radio_button, flag=wx.BOTTOM, border=5)
            if len(radio_buttons) == 1:
                sbs.Add(wx.StaticLine(self.panel), 0, wx.ALL|wx.EXPAND, 5)
            #sbs.AddSpacer(5)
            self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioButtonSelect, radio_button)

        radio_buttons[0].SetValue(True)
        self.checked_rb = radio_buttons[0]

        #---------------------
        # OK/Cancel buttons
        #---------------------

        hboxok = wx.BoxSizer(wx.HORIZONTAL)
        self.okButton = wx.Button(self.panel, id=-1, label='Import file')
        self.okButton.SetDefault()
        self.Bind(wx.EVT_BUTTON, self.on_okButton, self.okButton)
        self.cancelButton = wx.Button(self.panel, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)
        self.nextButton = wx.Button(self.panel, id=-1, label='Skip to next step')
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
    
    #-----------------------
    # button methods
    #-----------------------

    def on_cancelButton(self,event):
        self.Destroy()
        self.Parent.Show()
        self.Parent.Raise()

    def on_okButton(self,event):
        os.chdir(self.WD)
        file_type = self.checked_rb.Label.split()[0] # extracts name of the checked radio button
        if file_type == 'generic':
            dia = convert_generic_files_to_MagIC(self, self.WD, "PmagPy generic file conversion")
        elif file_type == 'SIO':
            dia = convert_SIO_files_to_MagIC(self, self.WD, "PmagPy SIO file conversion")
        elif file_type == 'CIT':
            dia = convert_CIT_files_to_MagIC(self, self.WD, "PmagPy CIT file conversion")
        elif file_type == '2G-binary':
            dia = convert_2G_binary_files_to_MagIC(self, self.WD, "PmagPy 2G-binary file conversion")
        elif file_type == 'HUJI':
            dia = convert_HUJI_files_to_MagIC(self, self.WD, "PmagPy HUJI file conversion")
        elif file_type == 'LDEO':
            dia = convert_LDEO_files_to_MagIC(self, self.WD, "PmagPy LDEO file conversion")
        elif file_type == 'IODP':
            dia = convert_IODP_files_to_MagIC(self, self.WD, "PmagPy IODP csv conversion")
        elif file_type == 'PMD':
            dia = convert_PMD_files_to_MagIC(self, self.WD, "PmagPy PMD conversion")
        elif file_type == 'BGC':
            dia = convert_BGC_files_to_magic(self, self.WD, "PmagPy BGC conversion")
        elif file_type == 'TDT':
            import programs.TDT_magic as TDT_magic
            TDT_magic.main(False, self.WD)
            return True
        elif file_type == 'JR6':
            dia = convert_JR6_files_to_MagIC(self, self.WD)
        dia.Center()
        dia.Show()


    def OnRadioButtonSelect(self, event):
        self.checked_rb = event.GetEventObject()

    def on_nextButton(self,event):
        self.Destroy()
        combine_dia = combine_magic_dialog(self.WD, self.parent)
        combine_dia.Show()
        combine_dia.Center()

#--------------------------------------------------------------
# dialog for combine_magic.py
#--------------------------------------------------------------


class combine_magic_dialog(wx.Frame):
    """"""
    title = "Combine magic files"

    def __init__(self, WD, parent):
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title)
        self.panel =  wx.ScrolledWindow(self) #wx.Panel(self)
        self.panel.SetScrollbars(20, 20, 50, 50)
        self.WD=WD
        self.InitUI()

    def InitUI(self):
        pnl = self.panel

        #---sizer information ----

        TEXT="Step 2: \nCombine different MagIC formatted files to one file named 'magic_measurements.txt'"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_LEFT)


        #---sizer 0 ----
        self.bSizer0 = pw.combine_files(self, ".magic")
        #------------------

        self.okButton = wx.Button(self.panel, wx.ID_OK, "&OK")
        self.Bind(wx.EVT_BUTTON, self.on_okButton, self.okButton)

        self.cancelButton = wx.Button(self.panel, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)

        self.nextButton = wx.Button(self.panel, id=-1, label='Skip to last step')
        self.Bind(wx.EVT_BUTTON, self.on_nextButton, self.nextButton)

        hboxok = wx.BoxSizer(wx.HORIZONTAL)
        hboxok.Add(self.okButton)
        hboxok.Add(self.cancelButton, flag=wx.LEFT, border=5)
        hboxok.Add(self.nextButton, flag=wx.LEFT, border=5)

        #------
        vbox=wx.BoxSizer(wx.VERTICAL)
        vbox.AddSpacer(10)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(10)
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
        self.Centre()
        self.Show()


    def on_cancelButton(self,event):
        self.Parent.Show()
        self.Parent.Raise()
        self.Destroy()

    def on_nextButton(self, event):
        combine_dia = combine_everything_dialog(self.WD, self.Parent)
        combine_dia.Show()
        combine_dia.Center()
        self.Destroy()

    def on_okButton(self,event):
        os.chdir(self.WD) # make sure OS is working in self.WD (Windows issue)
        files_text=self.bSizer0.file_paths.GetValue()
        files=files_text.strip('\n').replace(" ","")
        if files:
            files = files.split('\n')
            files = [os.path.join(self.WD, f) for f in files]
        COMMAND="combine_magic.py -F magic_measurements.txt -f %s"%(" ".join(files) )

        # to run as module:
        #print "-I- Running equivalent of Python command:\n %s"%COMMAND

        if ipmag.combine_magic(files, 'magic_measurements.txt'):
            #pw.close_window(self.panel, COMMAND, 'magic_measurements.txt')
            MSG="%i file are merged to one MagIC format file:\n magic_measurements.txt.\n\nSee Terminal (Mac) or command prompt (Windows) for errors"%(len(files))
            dlg1 = wx.MessageDialog(None,caption="Message:", message=MSG ,style=wx.OK|wx.ICON_INFORMATION)
            dlg1.ShowModal()
            dlg1.Destroy()
        else:
            pw.simple_warning()
            return

        self.on_nextButton(event)
        self.Destroy()


class combine_everything_dialog(wx.Frame):
    """"""
    title = "Combine MagIC files"

    def __init__(self, WD, parent):
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title)
        self.panel =  wx.ScrolledWindow(self) #wx.Panel(self)
        self.panel.SetScrollbars(20, 20, 50, 50)
        self.WD=WD
        self.InitUI()

    def InitUI(self):

        pnl = self.panel

        #---sizer information ----

        TEXT="Step 3: \nCombine different MagIC formatted files to one file name (if necessary).  All files should be from the working directory."
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_LEFT)

        possible_file_dias = ['er_specimens.txt', 'er_samples.txt', 'er_sites.txt', 'rmag_anisotropy.txt', 'rmag_results.txt', 'rmag_hysteresis.txt']
        self.file_dias = []
        all_files = os.listdir(self.WD)
        for dia in possible_file_dias:
            for f in all_files:
                if dia in f:
                    bSizer = pw.combine_files(self, dia)
                    self.file_dias.append(bSizer)
                    break
        if not self.file_dias:
            file_string = ', '.join(possible_file_dias)
            MSG = "You have no more files that can be combined.\nFile types that can be combined are:\n{}\nNote that your file name must end with the file type, i.e.:\nsomething_something_er_specimens.txt".format(file_string)
            dlg = wx.MessageDialog(None,caption="Message:", message=MSG ,style=wx.OK|wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            # deleted by rshaar 10.11.2015
            #self.Destroy()

        #------------------

        self.okButton = wx.Button(self.panel, wx.ID_OK, "&OK")
        self.Bind(wx.EVT_BUTTON, self.on_okButton, self.okButton)

        self.cancelButton = wx.Button(self.panel, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)

        hboxok = wx.BoxSizer(wx.HORIZONTAL)
        hboxok.Add(self.okButton)
        hboxok.Add(self.cancelButton, flag=wx.LEFT, border=5 )

        #file_dias = [self.bSizer0, self.bSizer1, self.bSizer2]
        if len(self.file_dias) == 4:
            num_cols, num_rows = 2, 2
        else:
            num_cols = min(len(self.file_dias), 3)
            num_rows = 2 if len(self.file_dias) > 3 else 1
        hboxfiles = wx.GridSizer(num_rows, num_cols, 1, 1)
        hboxfiles.AddMany(self.file_dias)

        #hboxfiles = wx.BoxSizer(wx.HORIZONTAL)
        #hboxfiles.AddMany([self.bSizer0, self.bSizer1, self.bSizer2])

        #------
        vbox=wx.BoxSizer(wx.VERTICAL)
        vbox.AddSpacer(10)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.BOTTOM, border=5)
        vbox.AddSpacer(10)
        vbox.Add(hboxfiles, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(10)
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
        self.Centre()
        self.Show()

    def on_cancelButton(self,event):
        self.Parent.Show()
        self.Parent.Raise()
        self.Destroy()

    def on_okButton(self,event):
        os.chdir(self.WD)
        success = True
        new_files = []
        # go through each pw.combine_files sizer, extract the files, try to combine them into one:
        for bSizer in self.file_dias:
            full_list = bSizer.file_paths.GetValue()
            file_name = bSizer.text
            files = full_list.strip('\n').replace(" ", "")
            if files:
                files = files.split('\n')
            if ipmag.combine_magic(files, file_name):
                new_files.append(file_name)  # add to the list of successfully combined files
            else:
                success = False
        if success:
            new = '\n' + '\n'.join(new_files)
            MSG = "Created new file(s): {} \nSee Terminal (Mac) or command prompt (Windows) for details and errors".format(new)
            dlg1 = wx.MessageDialog(None,caption="Message:", message=MSG ,style=wx.OK|wx.ICON_INFORMATION)
            dlg1.ShowModal()
            dlg1.Destroy()
            self.Parent.Show()
            self.Parent.Raise()
            self.Destroy()
        else:
            pw.simple_warning()


#--------------------------------------------------------------
# MagIC generic files conversion
#--------------------------------------------------------------


class convert_files_to_MagIC(wx.Frame):
    """
    Base class for file conversion frames
    """

    def __init__(self, parent, WD, title):
        self.parent = parent
        self.WD = WD
        self.title = title
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title)
        self.panel = wx.ScrolledWindow(self)
        self.panel.SetScrollbars(20, 20, 50, 50)
        self.InitUI()

    def InitUI(self):
        pass

    def on_cancelButton(self, event):
        self.Destroy()
        self.parent.Show()
        self.parent.Raise()

    def on_add_file_button(self, event):
        text = "choose file to convert to MagIC"
        pw.on_add_file_button(self.bSizer0, text)

    def on_add_dir_button(self, event):
        text = "choose directory of files to convert to MagIC"
        pw.on_add_dir_button(self.bSizer0, text)


class convert_generic_files_to_MagIC(convert_files_to_MagIC):
    """"""
    title = "PmagPy generic file conversion"

    #def __init__(self,parent,WD):
    #    wx.Frame.__init__(self, parent, wx.ID_ANY, self.title)
    #    self.panel = wx.ScrolledWindow(self)
    #    self.panel.SetScrollbars(20, 20, 50, 50)
    #    self.WD = WD
    #    self.parent = parent
    #    self.InitUI()

    def InitUI(self):

        pnl = self.panel

        #---sizer infor ----

        TEXT = "convert generic file to MagIC format"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_LEFT)


        #---sizer 0 ----
        self.bSizer0 = pw.choose_file(pnl, 'add', method = self.on_add_file_button)

        #---sizer 1 ----
        self.bSizer1 = pw.labeled_text_field(pnl)

        #---sizer 2 ----
        # unique because only accepts 1 experiment type
        TEXT="Experiment:"
        self.bSizer2 = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.HORIZONTAL)
        self.gridBSizer = wx.GridBagSizer(5, 10)
        self.label1 = wx.StaticText(pnl, label=TEXT)
        self.experiments_names=['Demag (AF and/or Thermal)','Paleointensity-IZZI/ZI/ZI','ATRM 6 positions','AARM 6 positions','cooling rate','TRM']
        self.protocol_info = wx.ComboBox(self.panel, -1, self.experiments_names[0], size=(300,25),choices=self.experiments_names, style=wx.CB_READONLY)
        self.gridBSizer.Add(self.label1, (0, 0))
        self.gridBSizer.Add(self.protocol_info, (1, 0))
        self.bSizer2.Add(self.gridBSizer, wx.ALIGN_LEFT)
        #
        self.Bind(wx.EVT_COMBOBOX, self.on_select_protocol, self.protocol_info)
        self.bSizer2a = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.HORIZONTAL )
        text = 'Cooling Rate, format is xxx,yyy,zzz with no spaces  '
        self.cooling_rate = wx.TextCtrl(pnl)
        self.bSizer2a.AddMany([wx.StaticText(pnl, label=text), self.cooling_rate])

        #---sizer 3 ----
        self.bSizer3 = pw.lab_field(pnl)

        #---sizer 4 ----
        # unique because only allows 4 choices (most others have ncn choices)
        self.bSizer4 = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.VERTICAL )
        self.sample_naming_conventions=['sample=specimen','no. of initial characters','no. of terminal characters','character delimited']
        self.sample_naming_convention = wx.ComboBox(self.panel, -1, self.sample_naming_conventions[0], size=(250,25), choices=self.sample_naming_conventions, style=wx.CB_READONLY)
        self.sample_naming_convention_char = wx.TextCtrl(self.panel, id=-1, size=(40,25))
        gridbSizer4 = wx.GridSizer(2, 2, 0, 10)
        gridbSizer4.AddMany( [(wx.StaticText(self.panel,label="specimen-sample naming convention",style=wx.TE_CENTER),wx.ALIGN_LEFT),
            (wx.StaticText(self.panel,label="delimiter/number (if necessary)",style=wx.TE_CENTER),wx.ALIGN_LEFT),
            (self.sample_naming_convention,wx.ALIGN_LEFT),
            (self.sample_naming_convention_char,wx.ALIGN_LEFT)])
        #bSizer4.Add(self.sample_specimen_text,wx.ALIGN_LEFT)
        self.bSizer4.AddSpacer(10)
        self.bSizer4.Add(gridbSizer4,wx.ALIGN_LEFT)

        #---sizer 5 ----
        self.bSizer5 = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.VERTICAL )
        self.site_naming_conventions=['site=sample','no. of initial characters','no. of terminal characters','character delimited']
        self.site_naming_convention_char = wx.TextCtrl(self.panel, id=-1, size=(40,25))
        self.site_naming_convention = wx.ComboBox(self.panel, -1, self.site_naming_conventions[0], size=(250,25), choices=self.site_naming_conventions, style=wx.CB_READONLY)
        gridbSizer5 = wx.GridSizer(2, 2, 0, 10)
        gridbSizer5.AddMany( [(wx.StaticText(self.panel,label="sample-site naming convention",style=wx.TE_CENTER),wx.ALIGN_LEFT),
            (wx.StaticText(self.panel,label="delimiter/number (if necessary)",style=wx.TE_CENTER),wx.ALIGN_LEFT),
            (self.site_naming_convention,wx.ALIGN_LEFT),
            (self.site_naming_convention_char,wx.ALIGN_LEFT)])
        self.bSizer5.AddSpacer(10)
        self.bSizer5.Add(gridbSizer5,wx.ALIGN_LEFT)

        #---sizer 6 ----
        TEXT="Location name:"
        self.bSizer6 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 7 ----
        self.bSizer7 = pw.replicate_measurements(pnl)

        #---buttons ---
        hboxok = pw.btn_panel(self, pnl)

        #------
        vbox=wx.BoxSizer(wx.VERTICAL)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=5)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=5)
        vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=5)
        vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=5)
        vbox.Add(self.bSizer2a, flag=wx.ALIGN_LEFT|wx.TOP, border=5)

        vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=5)
        vbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.TOP, border=5)
        vbox.Add(self.bSizer5, flag=wx.ALIGN_LEFT|wx.TOP, border=5)
        vbox.Add(self.bSizer6, flag=wx.ALIGN_LEFT|wx.TOP, border=5)
        vbox.Add(self.bSizer7, flag=wx.ALIGN_LEFT|wx.TOP|wx.BOTTOM, border=5)
        vbox.Add(wx.StaticLine(self.panel), 0, wx.ALL|wx.EXPAND, 5)
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)
        vbox.AddSpacer(5)


        self.hbox_all= wx.BoxSizer(wx.HORIZONTAL)
        self.hbox_all.AddSpacer(20)
        self.hbox_all.AddSpacer(vbox)
        self.hbox_all.AddSpacer(20)

        self.panel.SetSizer(self.hbox_all)
        self.bSizer2a.ShowItems(False)
        self.hbox_all.Fit(self)
        self.Centre()
        self.Show()


    def on_select_protocol(self, event):
        if self.protocol_info.GetValue() == "cooling rate":
            self.bSizer2a.ShowItems(True)
        else:
            self.bSizer2a.ShowItems(False)
        self.hbox_all.Fit(self)


    def on_add_file_button(self,event):
        text = "choose file to convert to MagIC"
        pw.on_add_file_button(self.bSizer0, text)


    def on_okButton(self,event):
        os.chdir(self.WD)
        # generic_magic.py -WD WD - f FILE -fsa er_samples.txt -F OUTFILE.magic -exp [Demag/PI/ATRM 6/AARM 6/CR  -samp X Y -site  X Y -loc LOCNAME -dc B PHI THETA [-A] -WD path
        options = {}

        ErrorMessage = ""
        #-----------
        if not self.bSizer0.file_path.GetValue():
            pw.simple_warning('You must provide a generic format file')
            return False
        FILE = str(self.bSizer0.file_path.GetValue())
        options['magfile'] = FILE

        #-----------
        # WD="/".join(FILE.split("/")[:-1])
        WD=self.WD
        options['WD'] = WD
        input_dir = os.path.split(FILE)[0]
        magicoutfile=os.path.split(FILE)[1]+".magic"
        options['meas_file'] = magicoutfile
        print "magicoutfile", magicoutfile
        OUTFILE=os.path.join(self.WD,magicoutfile)
        #-----------
        #OUTFILE=self.WD+"/"+FILE.split('/')[-1]+".magic"
        #-----------
        EXP = ""
        exp = str(self.protocol_info.GetValue())
        if exp == 'Demag (AF and/or Thermal)':
            EXP = 'Demag'
        elif exp == 'Paleointensity-IZZI/ZI/ZI':
            EXP = 'PI'
        elif exp == 'ATRM 6 positions':
            EXP ='ATRM 6'
        elif exp == 'AARM 6 positions':
            EXP = 'AARM 6'
        elif exp == 'cooling rate':
            cooling = self.cooling_rate.GetValue()
            if not cooling:
                text = "You must provide cooling rate for this experiment type!\nThe format is: xxx, yyy,zzz...\nThis should be cooling rates in [K/minutes], seperated by comma, ordered at the same order as XXX.10,XXX.20 ...XX.70"
                pw.simple_warning(text)
                return False
            EXP = 'CR {}'.format(cooling)
        if 'CR' in EXP:
            options['experiment'], options['cooling_times_list'] = EXP.split()
        elif 'AARM' in EXP:
            options['experiment'], options['aarm_n_pos'] = EXP.split()
        elif 'ATRM' in EXP:
            options['experiment'], options['atrm_n_pos'] = EXP.split()
        else:
            options['experiment'] = EXP
        #-----------
        SAMP="1 0" #default

        samp_naming_convention = str(self.sample_naming_convention.GetValue())
        try:
            samp_naming_convention_char=int(self.sample_naming_convention_char.GetValue())
        except:
             samp_naming_convention_char = "0"

        if samp_naming_convention == 'sample=specimen':
            SAMP = "1 0"
        elif samp_naming_convention == 'no. of initial characters':
            SAMP = "0 %i" % int(samp_naming_convention_char)
        elif samp_naming_convention == 'no. of terminal characters':
            SAMP = "1 %s" % samp_naming_convention_char
        elif samp_naming_convention == 'character delimited':
            SAMP = "2 %s" % samp_naming_convention_char

        options['sample_nc'] = SAMP.split()
        #-----------

        SITE = "1 0" #default

        site_naming_convention = str(self.site_naming_convention.GetValue())
        try:
            site_naming_convention_char = int(self.site_naming_convention_char.GetValue())
        except:
             site_naming_convention_char = "0"

        if site_naming_convention == 'sample=specimen':
            SITE = "1 0"
        elif site_naming_convention == 'no. of initial characters':
            SITE = "0 %i" % int(site_naming_convention_char)
        elif site_naming_convention == 'no. of terminal characters':
            SITE = "1 %s" % site_naming_convention_char
        elif site_naming_convention == 'character delimited':
            SITE = "2 %s" % site_naming_convention_char

        options['site_nc'] = SITE.split()

        #-----------

        LOC = str(self.bSizer6.return_value())
        options['er_location_name'] = LOC

        if str(self.bSizer6.return_value()) != "":
            LOC="-loc \"%s\""%LOC
        else:
            LOC=""

        #-----------

        LABFIELD=" "
        try:
            B_uT, DEC, INC = self.bSizer3.return_value().split()
        except ValueError:
            B_uT, DEC, INC = '0', '0', '0'

        #print "B_uT, DEC, INC", B_uT, DEC, INC
        options['labfield'], options['labfield_phi'], options['labfield_theta'] = B_uT, DEC, INC

        if EXP != "Demag":
            LABFIELD="-dc "  +B_uT+ " " + DEC + " " + INC

        #-----------

        DONT_AVERAGE = " "
        if not self.bSizer7.return_value():
            DONT_AVERAGE = "-A"
            options['noave'] = 1
        else:
            options['noave'] = 0

        #-----------
        # some special

        SAMP_OUTFILE =  magicoutfile[:magicoutfile.find('.')] + "_er_samples.txt"
        options['samp_file'] = SAMP_OUTFILE

        COMMAND="generic_magic.py -WD %s -f %s -fsa er_samples.txt -F %s -exp %s  -samp %s -site %s %s %s %s -Fsa %s"\
        %(WD,FILE,OUTFILE,EXP,SAMP,SITE,LOC,LABFIELD,DONT_AVERAGE, SAMP_OUTFILE)

        print "-I- Running Python command:\n %s"%COMMAND
        import programs.generic_magic as generic_magic
        program_run, error_message = generic_magic.main(False, **options)

        if program_run:
            pw.close_window(self, COMMAND, OUTFILE)
        else:
            pw.simple_warning(error_message)
            return False

        self.Destroy()
        self.parent.Raise()

    #def on_cancelButton(self,event):
    #    self.Destroy()
    #    self.parent.Raise()

    def on_helpButton(self, event):
        import programs.generic_magic as generic_magic
        pw.on_helpButton(text=generic_magic.do_help())

    def get_sample_name(self, specimen, sample_naming_convenstion):
        if sample_naming_convenstion[0] == "sample=specimen":
            sample = specimen
        elif sample_naming_convenstion[0] == "no. of terminal characters":
            n = int(sample_naming_convenstion[1]) * -1
            sample = specimen[:n]
        elif sample_naming_convenstion[0] == "character delimited":
            d = sample_naming_convenstion[1]
            sample_splitted = specimen.split(d)
            if len(sample_splitted) == 1:
                sample = sample_splitted[0]
            else:
                sample = d.join(sample_splitted[:-1])
        return sample

    def get_site_name(self, sample, site_naming_convention):
        if site_naming_convention[0] == "site=sample":
            site = sample
        elif site_naming_convention[0] == "no. of terminal characters":
            n = int(site_naming_convention[1])*-1
            site = sample[:n]
        elif site_naming_convention[0] == "character delimited":
            d = site_naming_convention[1]
            site_splitted = sample.split(d)
            if len(site_splitted) == 1:
                site = site_splitted[0]
            else:
                site = d.join(site_splitted[:-1])

        return site

class convert_SIO_files_to_MagIC(convert_files_to_MagIC):
    """
    convert SIO formatted measurement file to MagIC formated files
    """

    def InitUI(self):
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
        self.bSizer4 = pw.specimen_n(pnl)

        #---sizer 4a ----
        self.bSizer4a = pw.select_ncn(pnl)

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
        #self.bSizer10 = pw.synthetic(pnl)

        #---sizer 10 ---
        TEXT = "cooling rates [K/minutes] (seperated by comma) for cooling rate experiment:"
        self.bSizer10 = pw.labeled_text_field(pnl, TEXT)

        #---buttons ----
        hboxok = pw.btn_panel(self, pnl)

        #------
        vbox=wx.BoxSizer(wx.VERTICAL)
        hbox0 = wx.BoxSizer(wx.HORIZONTAL)
        hbox0.Add(self.bSizer5, flag=wx.ALIGN_LEFT)
        hbox0.Add(self.bSizer6, flag=wx.ALIGN_LEFT|wx.LEFT, border=5)
        hbox1 =wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(self.bSizer8, flag=wx.ALIGN_LEFT)
        hbox1.Add(self.bSizer9, flag=wx.ALIGN_LEFT|wx.LEFT, border=5)
        hbox2 =wx.BoxSizer(wx.HORIZONTAL)
        hbox2.Add(self.bSizer10, flag=wx.ALIGN_LEFT|wx.LEFT, border=5)

        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=8)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=8)
        vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=8)
        vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=8)
        vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=8)
        vbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.TOP, border=8)
        vbox.Add(self.bSizer4a, flag=wx.ALIGN_LEFT|wx.TOP, border=8)
        vbox.Add(hbox0, flag=wx.ALIGN_LEFT|wx.TOP, border=8)
        vbox.Add(self.bSizer7, flag=wx.ALIGN_LEFT|wx.TOP, border=8)
        vbox.Add(hbox1, flag=wx.ALIGN_LEFT|wx.TOP, border=8)
        vbox.Add(wx.StaticLine(pnl), 0, wx.ALL|wx.EXPAND, 5)
        vbox.Add(hbox2, flag=wx.ALIGN_LEFT|wx.TOP, border=8)
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
        self.Centre()
        self.Show()


    def on_okButton(self, event):
        os.chdir(self.WD)
        options_dict = {}
        SIO_file = self.bSizer0.return_value()
        if not SIO_file:
            pw.simple_warning('You must provide a SIO format file')
            return False
        options_dict['mag_file'] = str(SIO_file)
        magicoutfile=os.path.split(SIO_file)[1]+".magic"
        outfile =os.path.join(self.WD, magicoutfile)
        options_dict['meas_file'] = str(outfile)
        user = self.bSizer1.return_value()
        options_dict['user'] = str(user)
        if user:
            user = "-usr " + user
        experiment_type = self.bSizer2.return_value()
        options_dict['codelist'] = str(experiment_type)
        if experiment_type:
            experiment_type = "-LP " + experiment_type
        lab_field = self.bSizer3.return_value()
        if not lab_field:
            lab_field = ""
            options_dict['labfield'] = 0
            options_dict['phi'] = 0
            options_dict['theta'] = 0
        else:
            lab_field_list = str(lab_field).split()
            options_dict['labfield'] = lab_field_list[0]
            options_dict['phi'] = lab_field_list[1]
            options_dict['theta'] = lab_field_list[2]
            lab_field = "-dc " + lab_field
        spc = self.bSizer4.return_value()
        options_dict['specnum'] = spc
        ncn = self.bSizer4a.return_value()
        options_dict['samp_con'] = ncn
        loc_name = self.bSizer5.return_value()
        options_dict['er_location_name'] = str(loc_name)
        if loc_name:
            loc_name = "-loc " + loc_name
        instrument = self.bSizer6.return_value()
        options_dict['inst'] = str(instrument)
        if instrument:
            instrument = "-ins " + instrument
        replicate = self.bSizer7.return_value()
        if replicate:
            options_dict['noave'] = 0
        else:
            options_dict['noave'] = 1
        if replicate:
            replicate = ''
        else:
            replicate = '-A'
        peak_AF = self.bSizer8.return_value()
        options_dict['peakfield'] = peak_AF
        if peak_AF:
            peak_AF = "-ac " + peak_AF
        coil_number = self.bSizer9.return_value()
        options_dict['coil'] = coil_number
        if coil_number:
            coil_number = "-V " + coil_number
        cooling_rates=""
        cooling_rates = self.bSizer10.return_value()
        options_dict['cooling_rates'] = cooling_rates

        COMMAND = "sio_magic.py -F {0} -f {1} {2} {3} {4} {5} -spc {6} -ncn {7} {8} {9} {10} {11} {12}".format(outfile, SIO_file, user, experiment_type, cooling_rates, loc_name,spc, ncn, lab_field, peak_AF, coil_number, instrument, replicate)
        print "COMMAND", COMMAND
        # to run as module:
        import programs.sio_magic as sio_magic
        if sio_magic.main(command_line=False, **options_dict):
            pw.close_window(self, COMMAND, outfile)
        else:
            pw.simple_warning()

    def on_helpButton(self, event):
        import programs.sio_magic as sio_magic
        pw.on_helpButton(text=sio_magic.do_help())


class convert_CIT_files_to_MagIC(convert_files_to_MagIC):
    """stuff"""

    def InitUI(self):
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
        self.bSizer2 = pw.sampling_particulars(pnl)

        #---sizer 3 ----
        #self.bSizer3 = pw.lab_field(pnl)

        #---sizer 4 ----
        self.bSizer4 = pw.select_ncn(pnl)

        #---sizer 5 ---
        TEXT = "specify number of characters to designate a specimen, default = 0"
        self.bSizer5 = pw.specimen_n(pnl)

        #---sizer 6 ----
        TEXT="Location name:"
        self.bSizer6 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 7 ----
        self.bSizer7 = pw.replicate_measurements(pnl)

        #---sizer 8 ---
        TEXT = "peak AF field (mT) if ARM: "
        self.bSizer8 = pw.labeled_text_field(pnl, TEXT)

        #---buttons ---
        hboxok = pw.btn_panel(self, pnl)

        #------
        vbox=wx.BoxSizer(wx.VERTICAL)

        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer5, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer6, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer7, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer8, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
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
        self.Centre()
        self.Show()

    def on_okButton(self, event):
        os.chdir(self.WD)
        options_dict = {}
        wd = self.WD
        options_dict['dir_path'] = wd
        full_file = self.bSizer0.return_value()
        if not full_file:
            pw.simple_warning('You must provide a CIT format file')
            return False
        input_directory, CIT_file = os.path.split(full_file)
        options_dict['magfile'] = CIT_file
        options_dict['input_dir_path'] = input_directory
        if input_directory:
            ID = "-ID " + input_directory
        else:
            ID = ''
        outfile = CIT_file + ".magic"
        options_dict['meas_file'] = outfile
        samp_outfile = CIT_file[:CIT_file.find('.')] + "_er_samples.txt"
        options_dict['samp_file'] = samp_outfile
        spec_outfile = CIT_file[:CIT_file.find('.')] + "_er_specimens.txt"
        options_dict['spec_file'] = spec_outfile
        site_outfile = CIT_file[:CIT_file.find('.')] + "_er_sites.txt"
        options_dict['site_file'] = site_outfile
        user = self.bSizer1.return_value()
        options_dict['user'] = user
        if user:
            user = "-usr " + user
        spec_num = self.bSizer5.return_value()
        options_dict['specnum'] = spec_num
        if spec_num:
            spec_num = "-spc " + str(spec_num)
        else:
            spec_num = "-spc 0" # defaults to 0 if user doesn't choose number
        loc_name = self.bSizer6.return_value()
        options_dict['locname'] = loc_name
        if loc_name:
            loc_name = "-loc " + loc_name
        ncn = self.bSizer4.return_value()
        options_dict['samp_con'] = ncn
        particulars = self.bSizer2.return_value()
        options_dict['methods'] = particulars
        if particulars:
            particulars = "-mcd " + particulars
        peak_AF = self.bSizer8.return_value()
        options_dict['peak_AF'] = peak_AF
        if peak_AF:
            peak_AF = "-ac " + peak_AF

        replicate = self.bSizer7.return_value()
        if replicate:
            options_dict['avg'] = 0
            replicate = ''
        else:
            options_dict['avg'] = 1
            replicate = '-A'

        COMMAND = "CIT_magic.py -WD {} -f {} -F {} {} {} {} {} -ncn {} {} {} -Fsp {} -Fsi {} -Fsa {} {}".format(wd, CIT_file, outfile, particulars, spec_num, loc_name, user, ncn, peak_AF, ID, spec_outfile, site_outfile, samp_outfile, replicate)
        # to run as module:
        import programs.CIT_magic as CIT_magic
        program_ran, error_message = CIT_magic.main(command_line=False, **options_dict)
        if program_ran:
            pw.close_window(self, COMMAND, outfile)
        else:
            pw.simple_warning(error_message)

    def on_helpButton(self, event):
        import programs.CIT_magic as CIT_magic
        pw.on_helpButton(text=CIT_magic.do_help())


class convert_HUJI_files_to_MagIC(convert_files_to_MagIC):
    """ """
    def InitUI(self):

        pnl = self.panel

        TEXT = "HUJI format file"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0a ----

        TEXT = "HUJI file Type"
        label1 = "Old"
        label2 = "New"
        self.bSizer0a = pw.labeled_yes_or_no(pnl, TEXT, label1, label2)

        #---sizer 0 ----
        self.bSizer0 = pw.choose_file(pnl, 'add', method = self.on_add_file_button)

        #---sizer 1 ----
        self.bSizer1 = pw.labeled_text_field(pnl)

        #---sizer 2 ----
        exp_names=['AF Demag', 'Thermal (includes thellier but not trm)', 'NRM only', 'TRM acquisition', 'Anisotropy experiment', 'Cooling rate experiment']
        self.bSizer2 = pw.experiment_type(pnl, exp_names)

        #---sizer 2a ---
        #for box in self.bSizer2.boxes:
        #    self.Bind(wx.EVT_CHECKBOX, self.on_select_protocol, box)
        self.bSizer2a = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.HORIZONTAL )
        text = 'Cooling Rate (required only for cooling rate type experiments)\nformat is xxx,yyy,zzz with no spaces  '
        self.cooling_rate = wx.TextCtrl(pnl)
        self.bSizer2a.AddMany([wx.StaticText(pnl, label=text), self.cooling_rate])

        #---sizer 3 ----
        self.bSizer3 = pw.lab_field(pnl)

        #---sizer 4 ---
        TEXT = "specify number of characters to designate a specimen, default = 0"
        self.bSizer4 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 5 ----
        self.bSizer5 = pw.select_ncn(pnl)

        #---sizer 6 ----
        TEXT="Location name:"
        self.bSizer6 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 7 ---
        TEXT = "peak AF field (mT) if ARM: "
        self.bSizer7 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 8 ---
        self.bSizer8 = pw.replicate_measurements(pnl)


        #---buttons ---
        hboxok = pw.btn_panel(self, pnl)

        #------
        vbox=wx.BoxSizer(wx.VERTICAL)

        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0a, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer2a, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer5, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer6, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer7, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer8, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(wx.StaticLine(pnl), 0, wx.ALL|wx.EXPAND, 5)
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)
        vbox.AddSpacer(20)

        self.hbox_all= wx.BoxSizer(wx.HORIZONTAL)
        self.hbox_all.AddSpacer(20)
        self.hbox_all.AddSpacer(vbox)
        self.hbox_all.AddSpacer(20)

        self.panel.SetSizer(self.hbox_all)
        self.bSizer2a.ShowItems(True)
        self.hbox_all.Fit(self)
        self.Centre()
        self.Show()


    #def on_select_protocol(self, event):
    #     if event.GetEventObject().Label == "Cooling rate experiment":
    #         self.bSizer2a.ShowItems(True)
    #     else:
    #         self.bSizer2a.ShowItems(False)
    #     self.hbox_all.Fit(self)


    def on_okButton(self, event):
        """
        grab user input values, format them, and run HUJI_magic.py with the appropriate flags
        """
        os.chdir(self.WD)
        options = {}
        HUJI_file = self.bSizer0.return_value()
        if not HUJI_file:
            pw.simple_warning("You must select a HUJI format file")
            return False
        options['magfile'] = HUJI_file
        magicoutfile=os.path.split(HUJI_file)[1]+".magic"
        outfile=os.path.join(self.WD, magicoutfile)
        options['meas_file'] = outfile
        user = self.bSizer1.return_value()
        options['user'] = user
        if user:
            user = '-usr ' + user
        experiment_type = self.bSizer2.return_value()
        options['codelist'] = experiment_type
        if not experiment_type:
            pw.simple_warning("You must select an experiment type")
            return False
        cooling_rate = self.cooling_rate.GetValue() or 0
        if cooling_rate:
            experiment_type = experiment_type + " " + cooling_rate
        lab_field = self.bSizer3.return_value()
        if not lab_field:
            lab_field = "0 0 0"
        lab_field_list = lab_field.split()
        options['labfield'] = lab_field_list[0]
        options['phi'] = lab_field_list[1]
        options['theta'] = lab_field_list[2]
        lab_field = '-dc ' + lab_field
        spc = self.bSizer4.return_value()
        options['specnum'] = spc or 0
        if not spc:
            spc = '-spc 0'
        else:
            spc = '-spc ' + spc
        ncn = self.bSizer5.return_value()
        options['samp_con'] = ncn
        loc_name = self.bSizer6.return_value()
        options['er_location_name'] = loc_name
        if loc_name:
            loc_name = '-loc ' + loc_name
        peak_AF = self.bSizer7.return_value()
        options['peakfield'] = peak_AF

        replicate = self.bSizer8.return_value()
        if replicate:
            options['noave'] = 0
            replicate = ''
        else:
            options['noave'] = 1
            replicate = '-A'

        old_format= self.bSizer0a.return_value()

        if old_format:
            COMMAND = "HUJI_magic.py -f {} -F {} {} -LP {} {} -ncn {} {} {} {} {}".format(HUJI_file, outfile, user, experiment_type, loc_name, ncn, lab_field, spc, peak_AF, replicate)
            import programs.HUJI_magic as HUJI_magic
            program_ran, error_message = HUJI_magic.main(False, **options)
            if program_ran:
                pw.close_window(self, COMMAND, outfile)
            else:
                pw.simple_warning(error_message)

        else: # new format
            COMMAND = "HUJI_magic_new.py -f {} -F {} {} -LP {} {} -ncn {} {} {} {}".format(HUJI_file, outfile, user, experiment_type, loc_name, ncn, lab_field, spc, peak_AF)
            import programs.HUJI_magic_new as HUJI_magic_new
            program_ran, error_message = HUJI_magic_new.main(False, **options)
            if program_ran:
                pw.close_window(self, COMMAND, outfile)
            else:
                pw.simple_warning(error_message)

    def on_helpButton(self, event):
        old_format= self.bSizer0a.return_value()
        if old_format:
            import programs.HUJI_magic as HUJI
        else:
            import programs.HUJI_magic_new as HUJI
        pw.on_helpButton(text=HUJI.do_help())


class convert_2G_binary_files_to_MagIC(convert_files_to_MagIC):

    def InitUI(self):

        pnl = self.panel

        TEXT = "Folder containing one or more 2G-binary format files"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0 ----
        #self.bSizer0 = pw.choose_file(pnl, 'add', method = self.on_add_file_button)
        self.bSizer0 = pw.choose_dir(pnl, btn_text = 'add', method = self.on_add_dir_button)

        #---sizer 1 ----
        self.bSizer1 = pw.sampling_particulars(pnl)

        #---sizer 2 ----
        ncn_keys = ['XXXXY', 'XXXX-YY', 'XXXX.YY', 'XXXX[YYY] where YYY is sample designation, enter number of Y', 'sample name=site name', 'Site is entered under a separate column', '[XXXX]YYY where XXXX is the site name, enter number of X']
        self.bSizer2 = pw.select_ncn(pnl, ncn_keys)

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
        hboxok = pw.btn_panel(self, pnl) # creates ok, cancel, help buttons and binds them to appropriate methods

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
        self.Centre()
        self.Show()


    #---button methods ---

    def on_okButton(self, event):
        os.chdir(self.WD)
        options_dict = {}
        WD = self.WD
        options_dict['dir_path'] = WD
        directory = self.bSizer0.return_value()
        options_dict['ID'] = directory
        if not directory:
            pw.simple_warning('You must select a directory containing 2G binary files')
            return False
        files = os.listdir(directory)
        files = [str(f) for f in files if str(f).endswith('.dat')]
        if not files:
            pw.simple_warning('No .dat files found in {}'.format(directory))
            return False
        ID = "-ID " + directory
        if self.bSizer1.return_value():
            particulars = self.bSizer1.return_value()
            options_dict['gmeths'] = particulars
            mcd = '-mcd ' + particulars
        else:
            mcd = ''
        ncn = self.bSizer2.return_value()
        options_dict['samp_con'] = ncn
        spc = self.bSizer3.return_value()
        options_dict['specnum'] = spc or 0
        if not spc:
            spc = '-spc 1'
        else:
            spc = '-spc ' + spc
        ocn = self.bSizer4.return_value()
        options_dict['or_con'] = ocn
        loc_name = self.bSizer5.return_value()
        options_dict['location_name'] = loc_name
        if loc_name:
            loc_name = "-loc " + loc_name
        instrument = self.bSizer6.return_value()
        options_dict['inst'] = instrument
        if instrument:
            instrument = "-ins " + instrument
        replicate = self.bSizer7.return_value()
        if replicate:
            replicate = '-a'
            options_dict['noave'] = 0
        else:
            replicate = ''
            options_dict['noave'] = 1
        samp_outfile = files[0][:files[0].find('.')] + "_" + files[-1][:files[-1].find('.')] + "_er_samples.txt"
        options_dict['samp_file'] = samp_outfile
        sites_outfile = files[0][:files[0].find('.')] + "_" + files[-1][:files[-1].find('.')] + "_er_sites.txt"
        options_dict['site_file'] = sites_outfile
        import programs._2G_bin_magic as _2G_bin_magic
        for f in files:
            file_2G_bin = f
            outfile = file_2G_bin + ".magic"
            options_dict['meas_file'] = outfile
            options_dict['mag_file'] = f
            COMMAND = "_2G_bin_magic.py -WD {} -f {} -F {} -Fsa {} -Fsi {} -ncn {} {} {} -ocn {} {} {} {} {}".format(WD, file_2G_bin, outfile, samp_outfile, sites_outfile, ncn, mcd, spc, ocn, loc_name, replicate, ID, instrument)
            if files.index(f) == (len(files) - 1): # terminate process on last file call
                # to run as module:
                if _2G_bin_magic.main(False, **options_dict):
                    pw.close_window(self, COMMAND, outfile)
                else:
                    pw.simple_warning()

            else:
                print "Running equivalent of python command: ", COMMAND
                if _2G_bin_magic.main(False, **options_dict):
                    pass # success, continue on to next file
                else:
                    pw.simple_warning()

    def on_helpButton(self, event):
        # to run as module:
        import programs._2G_bin_magic as _2G_bin_magic
        pw.on_helpButton(text=_2G_bin_magic.do_help())

        # to run as command line:
        #pw.on_helpButton("_2G_bin_magic.py -h")



class convert_LDEO_files_to_MagIC(convert_files_to_MagIC):

    """ """
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
        exp_names=['AF Demag', 'Thermal (includes thellier but not trm)', 'Shaw method', 'IRM (acquisition)', 'NRM only', 'TRM acquisition', 'double AF demag', 'triple AF demag (GRM protocol)', 'Anisotropy experiment']
        self.bSizer2 = pw.experiment_type(pnl, exp_names)

        #---sizer 2a ---
        # add conditional boxsizer for Shaw experiments
        # if arm_labfield and trm_peakT are properly added into LDEO_magic

        #---sizer 3 ----
        self.bSizer3 = pw.lab_field(pnl)

        #---sizer 4 ----
        self.bSizer4 = pw.select_ncn(pnl)

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
        #self.bSizer11 = pw.synthetic(pnl)

        #---buttons ---
        hboxok = pw.btn_panel(self, pnl)

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
        #vbox.Add(self.bSizer11, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
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
        self.Centre()
        self.Show()

    def on_okButton(self, event):
        os.chdir(self.WD)
        options_dict = {}
        LDEO_file = self.bSizer0.return_value()
        if not LDEO_file:
            pw.simple_warning("You must provide a LDEO format file")
            return False
        options_dict['magfile'] = LDEO_file
        magicoutfile=os.path.split(LDEO_file)[1]+".magic"
        outfile=os.path.join(self.WD, magicoutfile)
        options_dict['meas_file'] = outfile
        synthetic_outfile = os.path.join(self.WD, magicoutfile[:magicoutfile.find('.')] + '_er_synthetics.txt')
        options_dict['synfile'] = synthetic_outfile
        user = self.bSizer1.return_value()
        options_dict['user'] = user
        if user:
            user = "-usr " + user
        experiment_type = self.bSizer2.return_value()
        options_dict['codelist'] = experiment_type
        if experiment_type:
            experiment_type = "-LP " + experiment_type
        lab_field = self.bSizer3.return_value()
        if lab_field:
            options_dict['labfield'], options_dict['phi'], options_dict['theta'] = lab_field.split()
            lab_field = "-dc " + lab_field
        ncn = self.bSizer4.return_value()
        options_dict['samp_con'] = ncn
        spc = self.bSizer5.return_value()
        options_dict['specnum'] = spc or 0
        if spc:
            spc = "-spc " + spc
        else:
            spc = "-spc 0"
        loc_name = self.bSizer6.return_value()
        options_dict['er_location_name'] = loc_name
        if loc_name:
            loc_name = "-loc " + loc_name
        instrument = self.bSizer7.return_value()
        options_dict['inst'] = instrument
        if instrument:
            instrument = "-ins " + instrument
        replicate = self.bSizer8.return_value()
        if replicate:
            replicate = ""
            options_dict['noave'] = 0 # do average
        else:
            replicate = "-A"
            options_dict['noave'] = 1 # don't average
        AF_field = self.bSizer9.return_value()
        options_dict['peakfield'] = AF_field or 0
        if AF_field:
            AF_field = "-ac " + AF_field
        coil_number = self.bSizer10.return_value()
        options_dict['coil'] = coil_number
        if coil_number:
            coil_number = "-V " + coil_number
        #synthetic = self.bSizer11.return_value()
        #if synthetic:
        #    options_dict['institution'] = synthetic[1]
        #    options_dict['syntype'] = synthetic[0]
        #    synthetic = '-syn ' + synthetic
        #else:
        #    synthetic = ''
        COMMAND = "LDEO_magic.py -f {0} -F {1} {2} {3} {4} -ncn {5} {6} {7} {8} {9} {10} {11}".format(LDEO_file, outfile, user, experiment_type, lab_field, ncn, spc, loc_name, instrument, replicate, AF_field, coil_number)
        # to run as module:
        import programs.LDEO_magic as LDEO_magic
        program_ran, error_message = LDEO_magic.main(False, **options_dict)
        if program_ran:
            pw.close_window(self, COMMAND, outfile)
        else:
            pw.simple_warning(error_message)


    def on_helpButton(self, event):
        import programs.LDEO_magic as LDEO_magic
        pw.on_helpButton(text=LDEO_magic.do_help())


class convert_IODP_files_to_MagIC(convert_files_to_MagIC):

    """ """

    def InitUI(self):

        pnl = self.panel

        TEXT = "IODP csv format file"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0a ---
        TEXT = "IODP file type"
        label1 = "SRM section"
        label2 = "SRM discrete"

        self.bSizer0a = pw.labeled_yes_or_no(pnl, TEXT, label1, label2)
        #self.bSizer0a = pw.radio_buttons(pnl, ['old format', 'srm', 'discrete'], 'IODP file type')

        #---sizer 0b ---
        TEXT = "If you don't choose a file, Pmag GUI will try to import any .csv files in your working directory into one MagIC format file"
        self.bSizer0b = pw.simple_text(pnl, TEXT)

        #---sizer 0 ----
        self.bSizer0 = pw.choose_file(pnl, 'add', method = self.on_add_file_button)

        #---sizer 1 ----
        self.bSizer1 = pw.replicate_measurements(pnl)

        #---buttons ---
        hboxok = pw.btn_panel(self, pnl)

        #------
        vbox=wx.BoxSizer(wx.VERTICAL)

        vbox.AddSpacer(10)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0a, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0b, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
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
        self.Centre()
        self.Show()

    def on_okButton(self, event):
        os.chdir(self.WD)
        wait = wx.BusyInfo("Please wait, working...")
        options = {}
        wd = self.WD
        options['dir_path'] = wd
        is_section = self.bSizer0a.return_value()
        full_file = self.bSizer0.return_value()
        ID, IODP_file = os.path.split(full_file)
        if not ID:
            ID = '.'
        options['csv_file'] = IODP_file
        options['input_dir_path'] = ID
        outfile = IODP_file + ".magic"
        options['meas_file'] = outfile
        spec_outfile = IODP_file[:IODP_file.find('.')] + "_er_specimens.txt"
        options['spec_file'] = spec_outfile
        samp_outfile = IODP_file[:IODP_file.find('.')] + "_er_samples.txt"
        options['samp_file'] = samp_outfile
        site_outfile = IODP_file[:IODP_file.find('.')] + "_er_sites.txt"
        options['site_file'] = site_outfile
        replicate = self.bSizer1.return_value()
        if replicate: # do average
            replicate = ''
            options['noave'] = 0
        else: # don't average
            replicate = "-A"
            options['noave'] = 1

        COMMAND = "IODP_srm_magic.py -WD {0} -f {1} -F {2} {3} -ID {4} -Fsp {5} -Fsa {6} -Fsi {7}".format(wd, IODP_file, outfile, replicate, ID, spec_outfile, samp_outfile, site_outfile)

        if is_section: # SRM section
            import programs.IODP_srm_magic as IODP_srm_magic
            program_ran, error_message = IODP_srm_magic.main(False, **options)
            if program_ran:
                pw.close_window(self, COMMAND, outfile)
            else:
                pw.simple_warning(error_message)
        else: # SRM discrete
            import programs.IODP_dscr_magic as IODP_dscr_magic
            program_ran, error_message = IODP_dscr_magic.main(False, **options)
            if program_ran:
                pw.close_window(self, COMMAND, outfile)
            else:
                pw.simple_warning(error_message)

        del wait

    def on_helpButton(self, event):
        is_section = self.bSizer0a.return_value()
        if is_section:
            import programs.IODP_srm_magic as IODP_srm_magic
            pw.on_helpButton(text=IODP_srm_magic.do_help())
        else:
            import programs.IODP_dscr_magic as IODP_dscr_magic
            pw.on_helpButton(text=IODP_dscr_magic.do_help())



class convert_PMD_files_to_MagIC(convert_files_to_MagIC):

    """ """
    def InitUI(self):

        pnl = self.panel

        TEXT = "Folder containing one or more PMD format files"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0 ----
        self.bSizer0 = pw.choose_dir(pnl, 'add', method = self.on_add_dir_button)

        #---sizer 2 ----
        ncn_keys = ['XXXXY', 'XXXX-YY', 'XXXX.YY', 'XXXX[YYY] where YYY is sample designation, enter number of Y', 'sample name=site name', 'Site is entered under a separate column', '[XXXX]YYY where XXXX is the site name, enter number of X']
        self.bSizer2 = pw.select_ncn(pnl, ncn_keys)

        #---sizer 3 ---
        #        TEXT = "specify number of characters to designate a specimen, default = 0"
        #        self.bSizer3 = pw.labeled_text_field(pnl, TEXT)
        self.bSizer3 = pw.specimen_n(pnl)


        #---sizer 4 ----
        TEXT="Location name:"
        self.bSizer4 = pw.labeled_text_field(pnl, TEXT)


        #---sizer 5 ----

        self.bSizer5 = pw.sampling_particulars(pnl)

        #---sizer 6 ---
        self.bSizer6 = pw.replicate_measurements(pnl)

        #---buttons ---
        hboxok = pw.btn_panel(self, pnl)

        #------
        vbox=wx.BoxSizer(wx.VERTICAL)

        vbox.AddSpacer(10)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer5, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer6, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)
        vbox.AddSpacer(20)

        hbox_all= wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.AddSpacer(vbox)
        hbox_all.AddSpacer(20)

        self.panel.SetSizer(hbox_all)
        self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Centre()
        self.Show()


    def on_okButton(self, event):
        os.chdir(self.WD)
        options = {}
        WD = self.WD
        options['dir_path'] = WD
        directory = self.bSizer0.return_value() or '.'
        options['input_dir_path'] = directory
        files = os.listdir(directory)
        files = [str(f) for f in files if str(f).endswith('.pmd')]
        if files:
            samp_outfile = files[0][:files[0].find('.')] + files[-1][:files[-1].find('.')] + "_er_samples.txt"
            options['samp_file'] = samp_outfile
        else:
            #raise Exception("No pmd files found in {}, try a different directory".format(WD))
            pw.simple_warning("No pmd files found in {}, try a different directory".format(WD))
        ID = "-ID " + directory
        ncn = self.bSizer2.return_value()
        options['samp_con'] = ncn
        spc = self.bSizer3.return_value() or 0
        options['specnum'] = spc
        loc_name = self.bSizer4.return_value()
        options['er_location_name'] = loc_name
        if loc_name:
            location = loc_name
            loc_name = "-loc " + loc_name
        particulars = self.bSizer5.return_value()
        options['meth_code'] = particulars
        if particulars:
            particulars = "-mcd " + particulars
        replicate = self.bSizer6.return_value()
        if replicate:
            replicate = ''
        else:
            replicate = '-A'
            options['noave'] = 1 # don't average
        import programs.PMD_magic as PMD_magic
        for f in files:
            options['mag_file'] = f
            outfile = f + ".magic"
            options['meas_file'] = outfile
            samp_outfile = f[:f.find('.')] + "_er_samples.txt"
            options['samp_file'] = samp_outfile
            COMMAND = "PMD_magic.py -WD {} -f {} -F {} -Fsa {} -ncn {} {} -spc {} {} {} {}".format(WD, f, outfile, samp_outfile, ncn, particulars, spc, replicate, ID, loc_name)

            # to run as command_line:
            #if files.index(f) == len(files) -1:
            #    pw.run_command_and_close_window(self, COMMAND, outfile)
            #else:
            #    pw.run_command(self, COMMAND, outfile)

            # to run as module:
            program_ran, error_message = PMD_magic.main(False, **options)
            if not program_ran:
                pw.simple_warning(error_message)
                return False
            elif files.index(f) == len(files) -1:
                pw.close_window(self, COMMAND, outfile)
            else:
                print "Just ran equivalent of Python command: ", COMMAND


    def on_helpButton(self, event):
        # to run as module:
        import programs.PMD_magic as PMD_magic
        pw.on_helpButton(text=PMD_magic.do_help())

        # to run as command line:
        #pw.on_helpButton("PMD_magic.py -h")


class convert_JR6_files_to_MagIC(wx.Frame):

    """ """
    title = "PmagPy JR6 file conversion"

    def __init__(self, parent, WD):
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title)
        self.panel = wx.ScrolledWindow(self)
        self.WD = WD
        self.InitUI()

    def InitUI(self):

        pnl = self.panel
        TEXT = "JR6 format file (currently .txt format only)"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0a ----
        TEXT = "JR6 file Type"
        label1 = ".txt format"
        label2 = ".jr6 format"
        self.bSizer0a = pw.labeled_yes_or_no(pnl, TEXT, label1, label2)

        #---sizer 0b ---
        self.bSizer0b = pw.check_box(pnl, 'Joides Resolution')
        self.Bind(wx.EVT_CHECKBOX, self.on_check_joides, self.bSizer0b.cb)

        #---sizer 0c ---
        #self.bSizer0c = pw.simple_text(pnl, "You must have an er_samples.txt file in the same directory as your .jr6 file")
        self.bSizer0c = pw.choose_file(pnl, btn_text='add er_samples.txt file', method=self.on_add_sampfile_button)

        self.bSizer0c.ShowItems(False)

        #---sizer 0 ----
        self.bSizer0 = pw.choose_file(pnl, btn_text='add measurement file', method = self.on_add_file_button)

        #---sizer 1 ----
        self.bSizer1 = pw.sampling_particulars(pnl)

        #---sizer 1a ---
        self.bSizer1a = pw.labeled_text_field(pnl, 'Specimen volume, default is 2.5 cc.\nPlease provide volume in cc.')

        #---sizer 2 ---
        self.bSizer2 = pw.specimen_n(pnl)

        #---sizer 3 ----
        ncn_keys = ['XXXXY', 'XXXX-YY', 'XXXX.YY', 'XXXX[YYY] where YYY is sample designation, enter number of Y', 'sample name=site name']#, These options are not yet implemented:   'Site names in orient.txt file', '[XXXX]YYY where XXXX is the site name, enter number of X']#, 'this is a synthetic and has no site name']
        self.bSizer3 = pw.select_ncn(pnl, ncn_keys)

        #---sizer 4 ----
        TEXT="Location name:"
        self.bSizer4 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 5 ----
        self.bSizer5 = pw.replicate_measurements(pnl)

        #---buttons ---
        hboxok = pw.btn_panel(self, pnl)

        #------
        vbox=wx.BoxSizer(wx.VERTICAL)
        hbox0 = wx.BoxSizer(wx.HORIZONTAL)
        hbox0.AddMany([self.bSizer0a, self.bSizer0b, self.bSizer0c])

        vbox.AddSpacer(10)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer0a, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(hbox0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer1a, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer5, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.AddSpacer(10)
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
        self.Centre()
        self.Show()

    def on_check_joides(self, event):
        if self.bSizer0b.cb.IsChecked():
            self.bSizer0c.ShowItems(True)
            self.bSizer0a.ShowItems(False)
            self.bSizer1.ShowItems(False)
            self.bSizer1a.ShowItems(False)
            self.bSizer2.ShowItems(False)
            self.bSizer3.ShowItems(False)
        else:
            self.bSizer0c.ShowItems(False)
            self.bSizer0a.ShowItems(True)
            self.bSizer1.ShowItems(True)
            self.bSizer1a.ShowItems(True)
            self.bSizer2.ShowItems(True)
            self.bSizer3.ShowItems(True)
        self.panel.Layout()

    def on_add_file_button(self,event):
        text = "choose file to convert to MagIC"
        pw.on_add_file_button(self.bSizer0, text)

    def on_add_sampfile_button(self, event):
        text = "choose er_samples type file"
        pw.on_add_file_button(self.bSizer0c, text)

    def on_okButton(self, event):
        samp_file = ''
        options = {}
        input_format = self.bSizer0a.return_value()
        JR = self.bSizer0b.return_value()
        if JR:
            samp_file = self.bSizer0c.return_value()
            if not samp_file:
                samp_file = os.path.join(self.WD, 'er_samples.txt')
                if not os.path.isfile(samp_file):
                    pw.simple_warning("er_samples file is a required option for Joides Resolution.\nYou must either provide the name of the file, or have a file named 'er_samples.txt' in your working directory.")
                    return False
        if input_format:
            input_format = 'txt'
        else:
            input_format = 'jr6'
        output_dir_path = self.WD
        options['dir_path'] = str(output_dir_path)
        input_dir_path, mag_file = os.path.split(self.bSizer0.return_value())
        if not mag_file:
            pw.simple_warning("You must select a JR6 format file")
            return False
        options['input_dir_path'], options['mag_file'] = str(input_dir_path), str(mag_file)
        meas_file = os.path.split(mag_file)[1]+".magic"
        options['meas_file'] = str(meas_file)
        #samp_file = os.path.splitext(os.path.splitext(meas_file)[0])[0] + "_er_samples.txt"
        if not samp_file:
            options['samp_file'] = 'er_samples.txt'
        else:
            options['samp_file'] = samp_file
        specnum = self.bSizer2.return_value()
        options['specnum'] = specnum
        samp_con = self.bSizer3.return_value()
        options['samp_con'] = samp_con
        er_location_name = self.bSizer4.return_value()
        options['er_location_name'] = str(er_location_name)
        average = self.bSizer5.return_value()
        if average:
            noave = 0
        else:
            noave = 1
        options['noave'] = noave
        meth_code = self.bSizer1.return_value()
        options['meth_code'] = meth_code
        volume = self.bSizer1a.return_value()
        os.chdir(self.WD)
        COMMAND = ""

        # validate arguments;
        if volume:
            try:
                volume = float(volume)
            except:
                pw.simple_warning("You must provide a valid quanity for volume")
                return False
            else:
                options['volume'] = volume

        # validate file type and run jr6_magic:
        if not JR:
            if 'jr6' in input_format and 'jr6' not in mag_file.lower():
                pw.simple_warning("You must provide a .jr6 format file")
                return False
            elif 'txt' in input_format and 'txt' not in mag_file.lower():
                pw.simple_warning("You must provide a .txt format file")
                return False
            if input_format == 'txt': # .txt format
                import programs.JR6_txt_magic as JR6_txt_magic
                program_ran, error_message = JR6_txt_magic.main(False, **options)
                if program_ran:
                    COMMAND = "options={}\nJR6_txt_magic.main(False, **options)".format(str(options))
                    pw.close_window(self, COMMAND, meas_file)
                else:
                    pw.simple_warning(error_message)
            else:
                import programs.JR6_jr6_magic as JR6_jr6_magic
                program_ran, error_message = JR6_jr6_magic.main(False, **options)
                if program_ran:
                    pw.close_window(self, COMMAND, meas_file)
                else:
                    pw.simple_warning(error_message)
        if JR: # Joides Resolution
            if not mag_file:
                pw.simple_warning('You must provide a valid IODP JR6 file')
            if not os.path.isfile(options['samp_file']):
                pw.simple_warning("No 'er_samples.txt' file was provided or found in your input directory:\n{}\nYou can download the csv sample file and import it to MagIC.\nIn the menubar, use Import -> orientation/location/stratigraphic files -> ODP sample summary csv file".format(input_dir_path))
                return False
            import programs.IODP_jr6_magic as IODP_jr6_magic
            program_ran, error_message = IODP_jr6_magic.main(False, **options)
            if program_ran:
                COMMAND = "options={}\nIODP_jr6_magic.main(False, **options)".format(str(options))
                pw.close_window(self, COMMAND, meas_file)
            else:
                pw.simple_warning(error_message)


    def on_cancelButton(self,event):
        self.Destroy()
        self.Parent.Raise()

    def on_helpButton(self, event):
        input_format = self.bSizer0a.return_value()
        if input_format:
            input_format = 'txt'
        else:
            input_format = 'jr6'
        if input_format == 'txt': # .txt format
            import programs.JR6_txt_magic as JR6_txt_magic
            pw.on_helpButton(text=JR6_txt_magic.do_help())
        else:
            import programs.JR6_jr6_magic as JR6_jr6_magic
            pw.on_helpButton(text=JR6_jr6_magic.do_help())


class convert_BGC_files_to_magic(wx.Frame):

    """ """
    title = "PmagPy BGC file conversion"

    def __init__(self, parent, WD, title):
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title)
        self.panel = wx.ScrolledWindow(self)
        self.WD = WD
        self.InitUI()

    def InitUI(self):

        pnl = self.panel

        text = "convert Berkeley Geochronology Center file to MagIC format"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=text), wx.ALIGN_LEFT)

        #---sizer 0 ----
        self.bSizer0 = pw.choose_file(pnl, 'add', method = self.on_add_file_button)

        #---sizer 1 ----
        self.bSizer1 = pw.labeled_text_field(pnl, 'Location name:')
        # locname

        #---sizer 2 ----
        self.bSizer2 = pw.labeled_text_field(pnl, 'Site name (required):')
        # sitename

        #---sizer 3 ----
        self.bSizer3 = pw.sampling_particulars(pnl)
        # meth codes

        #---sizer 4 ----
        self.bSizer4 = pw.replicate_measurements(pnl)
        # average replicates

        #---sizer 5 ---
        self.bSizer5 = pw.labeled_text_field(pnl, 'Provide specimen volume in cubic centimeters\nNote: the volume given in data file will be used unless it equals 0.0 ')

        #---sizer 6 ----

        #---sizer 7 ---


        #---buttons ---
        hboxok = pw.btn_panel(self, pnl)


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
        self.Centre()
        self.Show()


    def on_add_file_button(self,event):
        text = "choose file to convert to MagIC"
        pw.on_add_file_button(self.bSizer0, text)

    def on_okButton(self, event):
        os.chdir(self.WD)

        options = {}
        full_file = self.bSizer0.return_value()
        if not full_file:
            pw.simple_warning("You must provide a BGC format file")
            return False

        ID, infile = os.path.split(full_file)
        options['dir_path'] = self.WD
        options['input_dir_path'] = ID
        options['mag_file'] = infile
        outfile = infile + ".magic"
        options['meas_file'] = outfile

        loc_name = str(self.bSizer1.return_value())
        options['er_location_name'] = str(loc_name)
        site_name = self.bSizer2.return_value()
        if not site_name:
            pw.simple_warning('You must provide a site name')
            return False
        options['er_site_name'] = str(site_name)

        meth_code = self.bSizer3.return_value()
        options['meth_code'] = meth_code

        average = self.bSizer4.return_value()
        options['noave'] = average

        volume = self.bSizer5.return_value()
        if volume:
            try:
                options['volume'] = float(volume)
            except ValueError:
                pw.simple_warning('You must provide a valid numerical value for specimen volume')
                return False

        for key, value in options.items():
            print key, value

        import programs.BGC_magic as BGC_magic
        COMMAND = "options = {}\nBGC_magic.main(False, **options)".format(str(options))
        program_ran, error_message = BGC_magic.main(False, **options)

        if program_ran:
            pw.close_window(self, COMMAND, outfile)
        else:
            pw.simple_warning(error_message)

    def on_cancelButton(self,event):
        self.Destroy()
        self.Parent.Raise()

    def on_helpButton(self, event):
        import programs.BGC_magic as BGC_magic
        pw.on_helpButton(text=BGC_magic.do_help())

# template for an import window
class something(wx.Frame):

    """ """
    def InitUI(self):

        pnl = self.panel

        text = "Hello here is a bunch of text"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=text), wx.ALIGN_LEFT)

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
        hboxok = pw.btn_panel(self, pnl)


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
        self.Centre()
        self.Show()

    def on_add_file_button(self,event):
        text = "choose file to convert to MagIC"
        pw.on_add_file_button(self.bSizer0, self.WD, event, text)

    def on_okButton(self, event):
        os.chdir(self.WD)
        COMMAND = ""
        pw.run_command_and_close_window(self, COMMAND, outfile)

    def on_helpButton(self, event):
        pw.on_helpButton(text='')


#=================================================================
# demag_orient:
# read/write demag_orient.txt
# calculate sample orientation
#=================================================================

class OrientFrameGrid(wx.Frame):

    def __init__(self, parent, id, title, WD, ErMagic, size):
        wx.Frame.__init__(self, parent, -1, title, size=size, name='calculate geographic directions')

        #--------------------
        # initialize stuff
        #--------------------
        if sys.platform in ['win32', 'win64']:
            self.panel = wx.ScrolledWindow(self, style=wx.SIMPLE_BORDER|wx.ALWAYS_SHOW_SB)
        else:
            self.panel = wx.Panel(self, style=wx.SIMPLE_BORDER)

        self.WD = WD
        #self.Data_hierarchy = Data_hierarchy
        self.er_magic_data = ErMagic
        self.grid = None


        #--------------------
        # get the orientation data
        # 1) from file  demag_orient.txt
        # 2) from Data_hierarchy
        # and save it to self.orient_data={}
        #--------------------

        empty = True
        self.er_magic_data.get_data()

        self.samples_name_list = self.er_magic_data.make_name_list(self.er_magic_data.samples)
        self.orient_data = {}
        try:
            self.orient_data = self.er_magic_data.read_magic_file(os.path.join(self.WD, "demag_orient.txt"), "sample_name")[0]
        except Exception as ex:
            pass
        for sample_name in self.samples_name_list:
            if sample_name not in self.orient_data.keys():
                sample = self.er_magic_data.find_by_name(sample_name, self.er_magic_data.samples)
                self.orient_data[sample_name]={}
                self.orient_data[sample_name]["sample_name"] = sample_name
                if sample:
                    self.orient_data[sample_name]["site_name"] = sample.site
                else:
                    self.orient_data[sample_name]["site_name"] = ''

        #--------------------
        # create the grid sheet
        #--------------------

        self.create_sheet()

        TEXT = """
        A template for a file named 'demag_orient.txt', which contains samples orientation data, was created in MagIC working directory.
        You can view/modify demag_orient.txt using this Python frame, or you can use Excel/Open Office.
        If you use Excel, save the file as 'tab delimited' and then use the 'Import Orientation File' button below to import the data into Pmag GUI.
        If you use the Python frame, you can edit all the values in a column by clicking on the column header and then entering your desired value.
        After orientation data is filled in, you can Calculate sample orientations.
"""

        label = wx.StaticText(self.panel, label=TEXT)
        btn_box = wx.BoxSizer(wx.HORIZONTAL)
        save_btn = wx.Button(self.panel, wx.ID_ANY, "Save Orientation File")
        self.Bind(wx.EVT_BUTTON, self.on_m_save_file, save_btn)
        import_btn = wx.Button(self.panel, wx.ID_ANY, "Import Orientation File")
        self.Bind(wx.EVT_BUTTON, self.on_m_open_file, import_btn)
        calculate_btn = wx.Button(self.panel, wx.ID_ANY, "Calculate Sample Orientations")
        self.Bind(wx.EVT_BUTTON, self.on_m_calc_orient, calculate_btn)
        btn_box.Add(save_btn)
        btn_box.Add(import_btn, flag=wx.LEFT, border=5)
        btn_box.Add(calculate_btn, flag=wx.LEFT, border=5)
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(label, flag=wx.CENTRE)
        self.vbox.Add(btn_box, flag=wx.CENTRE)
        self.vbox.Add(self.grid, flag=wx.ALL, border=20)
        self.hbox_all = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox_all.Add(self.vbox)
        if sys.platform in ['win32', 'win64']:
            self.panel.SetScrollbars(20, 20, 50, 50)
        self.panel.SetSizer(self.hbox_all)
        self.hbox_all.Fit(self)

        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        # save the template
        self.on_m_save_file(None)
        self.Centre()
        self.Show()

    def create_sheet(self):
        '''
        creat an editable grid showing deamg_orient.txt
        '''
        #--------------------------------
        # orient.txt support many other headers
        # but here I put only
        # the essential headers for
        # sample orientation
        #--------------------------------

        # self.headers is a list of two-item tuples.
        #the first is the proper column name as understood by orientation_magic.py
        # the second is the name for display in the GUI
        self.headers=[("sample_name","sample_name"),
                ("sample_orientation_flag","sample_orientation_flag"),
                 #"site_name",
                ("mag_azimuth","mag_azimuth"),
                ("field_dip","field_dip"),
                ("bedding_dip_direction", "bedding_dip_direction"),
                ("bedding_dip", "bedding_dip"),
                ("shadow_angle", "shadow_angle"),
                ("lat", "latitude"),
                ("long", "longitude"),
                ("date", "mm/dd/yy"),
                ("hhmm", "hh:mm"),
                ("GPS_baseline","GPS_baseline"),
                ("GPS_Az", "GPS_Az"),
                 #"participants",
                ("magic_method_codes", "magic_method_codes")
                 ]

        #--------------------------------
        # create the grid
        #--------------------------------

        samples_list = self.orient_data.keys()
        samples_list.sort()
        self.samples_list = [ sample for sample in samples_list if sample is not "" ]
        display_headers = [header[1] for header in self.headers]
        self.grid = magic_grid.MagicGrid(self.panel, 'orient grid', self.samples_list, display_headers)
        self.grid.InitUI()

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
            self.grid.SetCellBackgroundColour(i, 6, "KHAKI")
            self.grid.SetCellBackgroundColour(i, 7, "KHAKI")
            self.grid.SetCellBackgroundColour(i, 8, "KHAKI")
            self.grid.SetCellBackgroundColour(i, 9, "KHAKI")
            self.grid.SetCellBackgroundColour(i, 10, "KHAKI")
            self.grid.SetCellBackgroundColour(i, 11, "LIGHT MAGENTA")
            self.grid.SetCellBackgroundColour(i, 12, "LIGHT MAGENTA")


        #--------------------------------
        # fill data from self.orient_data
        #--------------------------------

        headers = [header[0] for header in self.headers]
        for sample in self.samples_name_list:
            for key in self.orient_data[sample].keys():
                if key in headers:
                    sample_index = self.samples_list.index(sample)
                    i = headers.index(key)
                    self.grid.SetCellValue(sample_index, i, self.orient_data[sample][key])

        #--------------------------------

        #--------------------------------
        # fill in some default values
        #--------------------------------
        for row in range(self.grid.GetNumberRows()):
            col = 1
            if not self.grid.GetCellValue(row, col):
                self.grid.SetCellValue(row, col, 'g')

        #--------------------------------

        # temporary trick to get drop-down-menus to work
        self.grid.changes = {'a'}

        self.grid.AutoSize()
        self.drop_down_menu = drop_down_menus.Menus("orient", self, self.grid, '')


    def update_sheet(self):
        self.grid.Destroy()
        self.create_sheet()
        self.vbox.Add(self.grid, flag=wx.ALL, border=20)
        #self.Hide()
        #self.Show()
        self.hbox_all.Fit(self.panel)
        #self.panel.Refresh()
        self.Hide()
        self.Show()

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
            new_data = self.er_magic_data.read_magic_file(orient_file, "sample_name")[0]
            if len(new_data) > 0:
                self.orient_data={}
                self.orient_data=new_data
            #self.create_sheet()
            self.update_sheet()

    def on_m_save_file(self,event):

        '''
        save demag_orient.txt
        (only the columns that appear on the grid frame)
        '''
        fout = open(os.path.join(self.WD, "demag_orient.txt"), 'w')
        STR = "tab\tdemag_orient\n"
        fout.write(STR)
        headers = [header[0] for header in self.headers]
        STR = "\t".join(headers) + "\n"
        fout.write(STR)
        for sample in self.samples_list:
            STR = ""
            for header in headers:
                sample_index = self.samples_list.index(sample)
                i = headers.index(header)
                value = self.grid.GetCellValue(sample_index, i)
                STR = STR + value + "\t"
            fout.write(STR[:-1] + "\n")
        if event != None:
            dlg1 = wx.MessageDialog(None,caption="Message:", message="data saved in file demag_orient.txt" ,style=wx.OK|wx.ICON_INFORMATION)
            dlg1.ShowModal()
            dlg1.Destroy()


    def on_m_calc_orient(self,event):
        '''
        This fucntion does exactly what the 'import orientation' fuction does in MagIC.py
        after some dialog boxes the function calls orientation_magic.py
        '''
        # first see if demag_orient.txt
        self.on_m_save_file(None)
        orient_convention_dia = orient_convention(None)
        orient_convention_dia.Center()
        #orient_convention_dia.ShowModal()
        if orient_convention_dia.ShowModal() == wx.ID_OK:
            ocn_flag = orient_convention_dia.ocn_flag
            dcn_flag = orient_convention_dia.dcn_flag
            gmt_flags = orient_convention_dia.gmt_flags
            orient_convention_dia.Destroy()


        or_con = orient_convention_dia.ocn
        dec_correction_con = int(orient_convention_dia.dcn)
        try:
            hours_from_gmt = float(orient_convention_dia.gmt)
        except:
            hours_from_gmt = 0
        try:
            dec_correction = float(orient_convention_dia.correct_dec)
        except:
            dec_correction = 0

        method_code_dia=method_code_dialog(None)
        method_code_dia.Center()
        if method_code_dia.ShowModal()== wx.ID_OK:
            bedding_codes_flags=method_code_dia.bedding_codes_flags
            methodcodes_flags=method_code_dia.methodcodes_flags
            method_code_dia.Destroy()

        method_codes = method_code_dia.methodcodes
        average_bedding = method_code_dia.average_bedding
        bed_correction = method_code_dia.bed_correction

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
        commandline = " ".join(command_args)

        print "-I- executing command: %s" %commandline
        os.chdir(self.WD)

        ran_successfully, error_message = ipmag.orientation_magic(or_con, dec_correction_con, dec_correction, bed_correction, hours_from_gmt=hours_from_gmt, method_codes=method_codes, average_bedding=average_bedding, orient_file='demag_orient.txt', samp_file='er_samples_orient.txt', site_file='er_sites_orient.txt', input_dir_path=self.WD, output_dir_path=self.WD)

        if not ran_successfully:
            dlg1 = wx.MessageDialog(None,caption="Message:", message="-E- ERROR: Error in running orientation_magic.py\n{}".format(error_message) ,style=wx.OK|wx.ICON_INFORMATION)
            dlg1.ShowModal()
            dlg1.Destroy()

            print "-E- ERROR: Error in running orientation_magic.py"
            return

        # check if orientation_magic.py finished sucsessfuly
        data_saved = False
        if os.path.isfile(os.path.join(self.WD, "er_samples_orient.txt")):
            data_saved = True
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
        if os.path.isfile(os.path.join(self.WD, "er_samples.txt")):
            er_samples_file=os.path.join(self.WD, "er_samples.txt")
            er_samples_data=self.er_magic_data.read_magic_file(er_samples_file, "er_sample_name")[0]

        if os.path.isfile(os.path.join(self.WD, "er_samples_orient.txt")):
            er_samples_orient_file=os.path.join(self.WD, "er_samples_orient.txt")
            er_samples_orient_data=self.er_magic_data.read_magic_file(er_samples_orient_file, "er_sample_name")[0]
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
            for key in ["sample_orientation_flag","sample_azimuth","sample_dip","sample_bed_dip","sample_bed_dip_direction","sample_date","sample_declination_correction", "sample_lat", "sample_lon"]:
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
        er_recs=pmag.merge_recs_headers(er_recs)
        pmag.magic_write(os.path.join(self.WD, "er_samples.txt"),er_recs,"er_samples")

        #------------
        # now er_sites.txt
        er_sites_data={}
        if os.path.isfile(os.path.join(self.WD, "er_sites.txt")):
            er_sites_file = os.path.join(self.WD, "er_sites.txt")
            er_sites_data = self.er_magic_data.read_magic_file(er_sites_file, "er_site_name")[0]
        er_sites_orient_data={}
        if os.path.isfile(os.path.join(self.WD, "er_sites_orient.txt")):
            er_sites_orient_file = os.path.join(self.WD, "er_sites_orient.txt")
            er_sites_orient_data = self.er_magic_data.read_magic_file(er_sites_orient_file, "er_site_name")[0]
        new_sites_added = []
        for site in er_sites_orient_data.keys():
            if site not in er_sites_data.keys():
                new_sites_added.append(site)
                er_sites_data[site] = {}
                er_sites_data[site]['er_site_name'] = site
            for key in ["site_definition", "site_lat", "site_lon"]:
                if key in er_sites_orient_data[site].keys():
                    er_sites_data[site][key] = er_sites_orient_data[site][key]
        sites = er_sites_data.keys()
        sites.sort()
        er_recs = []
        for site in sites:
            er_recs.append(er_sites_data[site])
        er_recs = pmag.merge_recs_headers(er_recs)
        pmag.magic_write(os.path.join(self.WD, "er_sites.txt"), er_recs, "er_sites")

            #pmag.magic_write(os.path.join(self.WD, "er_samples.txt"),er_recs,"er_samples")

        dlg1 = wx.MessageDialog(None, caption="Message:", message="orientation data is saved/appended to er_samples.txt", style=wx.OK|wx.ICON_INFORMATION)
        dlg1.ShowModal()
        dlg1.Destroy()

        if len(new_samples_added) > 0:
            dlg1 = wx.MessageDialog(None, caption="Warning:", message="The following samples were added to er_samples.txt:\n %s "%(" , ".join(new_samples_added)), style=wx.OK|wx.ICON_INFORMATION)
            dlg1.ShowModal()
            dlg1.Destroy()

        self.Parent.Show()
        self.Parent.Raise()
        self.Destroy()


    def OnCloseWindow(self,event):
        dlg1 = wx.MessageDialog(self,caption="Message:", message="Save changes to demag_orient.txt?\n " ,style=wx.OK|wx.CANCEL)
        result = dlg1.ShowModal()
        if result == wx.ID_OK:
            self.on_m_save_file(None)
            dlg1.Destroy()
            self.Parent.Show()
            self.Parent.Raise()
            self.Destroy()
        if result == wx.ID_CANCEL:
            dlg1.Destroy()
            self.Parent.Show()
            self.Parent.Raise()
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
        self.op_rb1 = wx.RadioButton(pnl, -1, label='1) differential GPS 2) sun compass 3) magnetic compass',
                                     name='1', style=wx.RB_GROUP)
        sbs3.Add(self.op_rb1)
        sbs3.AddSpacer(5)
        self.op_rb2 = wx.RadioButton(pnl, -1, label='1) differential GPS 2) magnetic compass 3) sun compass ',
                                     name='2')
        sbs3.Add(self.op_rb2)
        sbs3.AddSpacer(5)


        #-----------------------
        #  add local time for GMT
        #-----------------------

        sbs4 = wx.StaticBoxSizer( wx.StaticBox( pnl, wx.ID_ANY, 'add local time' ), wx.HORIZONTAL )
        #hbox_alt = wx.BoxSizer(wx.HORIZONTAL)

        sbs4.AddSpacer(5)
        self.dc_alt = wx.TextCtrl(pnl,style=wx.CENTER)
        alt_txt = wx.StaticText(pnl, label="Hours to SUBTRACT from local time for GMT, default is 0",
                                style=wx.TE_CENTER)
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
        self.ocn = ""
        if self.oc_rb1.GetValue() == True:
            self.ocn = "1"
        if self.oc_rb2.GetValue() == True:
            self.ocn="2"
        if self.oc_rb3.GetValue() == True:
            self.ocn="3"
        if self.oc_rb4.GetValue() == True:
            self.ocn = "4"
        if self.oc_rb5.GetValue() == True:
            self.ocn="5"
        if self.oc_rb6.GetValue() == True:
            self.ocn="6"

        self.dcn = ""
        self.correct_dec = ""
        if self.dc_rb1.GetValue() == True:
            self.dcn = "1"
        if self.dc_rb2.GetValue() == True:
            self.dcn="2"
            try:
                self.correct_dec = float(self.dc_tb2.GetValue())
            except:
                dlg1 = wx.MessageDialog(None, caption="Error:", message="Add declination", style=wx.OK|wx.ICON_INFORMATION)
                dlg1.ShowModal()
                dlg1.Destroy()

        if self.dc_rb3.GetValue()==True:
            self.dcn = "3"

        if self.op_rb1.GetValue() == True:
            self.op = "1"
        if self.op_rb2.GetValue() == True:
            self.op = "2"

        if self.dc_alt.GetValue() != "":
            try:
                self.gmt = float(self.dc_alt.GetValue())
                gmt_flags = "-gmt " + self.dc_alt.GetValue()
            except:
                gmt_flags=""
        else:
            self.gmt = ""
            gmt_flags = ""
        #-------------
        self.ocn_flag = "-ocn "+ self.ocn
        self.dcn_flag = "-dcn "+ self.dcn
        self.gmt_flags = gmt_flags
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

        for cb in [self.cb1, self.cb2, self.cb3, self.cb4, self.cb5,
                   self.cb6, self.cb7, self.cb8, self.cb9, self.cb10]:
            sbs1.Add(cb, flag=wx.BOTTOM, border=5)

        #-----------------------
        # Bedding convention
        #-----------------------

        sbs2 = wx.StaticBoxSizer(wx.StaticBox(pnl, wx.ID_ANY, 'bedding convention'), wx.VERTICAL)
        self.bed_con1 = wx.CheckBox(pnl, -1, 'Take fisher mean of bedding poles?')
        self.bed_con2 = wx.CheckBox(pnl, -1, "Don't correct bedding dip direction with declination - already correct")

        sbs2.Add(self.bed_con1, flag=wx.BOTTOM, border=5)
        sbs2.Add(self.bed_con2, flag=wx.BOTTOM, border=5)

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
        if self.cb1.GetValue() == True:
            methodcodes.append('FS-FD')
        if self.cb2.GetValue() == True:
            methodcodes.append('FS-H')
        if self.cb3.GetValue() == True:
            methodcodes.append('FS-LOC-GPS')
        if self.cb4.GetValue() == True:
            methodcodes.append('FS-LOC-MAP')
        if self.cb5.GetValue() == True:
            methodcodes.append('SO-POM')
        if self.cb6.GetValue() == True:
            methodcodes.append('SO-ASC')
        if self.cb7.GetValue() == True:
            methodcodes.append('SO-MAG')
        if self.cb8.GetValue() == True:
            methodcodes.append('SO-SUN')
        if self.cb9.GetValue() == True:
            methodcodes.append('SO-SM')
        if self.cb10.GetValue() == True:
            methodcodes.append('SO-SIGHT')

        if methodcodes == []:
            self.methodcodes_flags=""
            self.methodcodes = ""
        else:
            self.methodcodes_flags = "-mcd " + ":".join(methodcodes)
            self.methodcodes = ":".join(methodcodes)

        bedding_codes=[]

        if self.bed_con1.GetValue() == True:
            bedding_codes.append("-a")
            self.average_bedding = True
        else:
            self.average_bedding = False
        if self.bed_con2.GetValue() ==True:
            bedding_codes.append("-BCN")
            self.bed_correction = False
        else:
            self.bed_correction = True
        self.bedding_codes_flags = " ".join(bedding_codes)
        self.EndModal(wx.ID_OK)
        #self.Close()

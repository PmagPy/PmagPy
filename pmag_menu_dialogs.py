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

        TEXT = "Import an orient.txt file into your working directory"
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
        self.bSizer3 = pw.select_specimen_ocn(pnl)

        #---sizer 4 ----
        self.bSizer4 = pw.select_declination(pnl)
        
        #---sizer 5 ----
        TEXT = "Hours to SUBTRACT from local time for GMT, default is 0:"
        self.bSizer5 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 6 ----
        # figure out proper formatting for this.  maybe 2 radio buttons?  option1: overwrite option2: update and append.
        TEXT = "Overwrite er_samples.txt file?"
        label1 = "yes, overwrite file in working directory"
        label2 = "no, update existing er_samples file"
        er_samples_file_present = True
        try:
            open(self.WD + "/er_samples.txt", "rU")
        except Exception as ex:
            er_samples_file_present = False
        if er_samples_file_present:
            self.bSizer6 = pw.labeled_yes_or_no(pnl, TEXT, label1, label2)

        #---sizer 7 ---
        label = "Select bedding conventions (if needed)"
        gridsize = (1, 2, 0, 5)
        choices = "averages all bedding poles and uses average for all samples: default is NO", "Don't correct bedding dip with declination -- already correct"
        self.bSizer7 = pw.check_boxes(pnl, gridsize, choices, label)
        #def __init__(self, parent, gridsize, choices, text):


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
        try:
            vbox.Add(self.bSizer6, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        except AttributeError:
            pass
        vbox.Add(self.bSizer7, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
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
        pw.on_add_file_button(self.bSizer0, self.WD, event, text)

    def on_okButton(self, event):
        WD = self.WD
        full_infile = self.bSizer0.return_value()
        #os.system('cp {} {}'.format(full_infile, WD))
        ind = full_infile.rfind('/')
        infile = full_infile[ind+1:]
        ID = full_infile[:ind+1]
        particulars = [p.split(':')[0] for p in self.bSizer1.return_value()]
        mcd = ':'.join(particulars)
        ncn = self.bSizer2.return_value()
        ocn = self.bSizer3.return_value()
        dcn = self.bSizer4.return_value()
        gmt = self.bSizer5.return_value() or 0
        try:
            app = self.bSizer6.return_value()
            if app:
                app = "" # overwrite is True
            else:
                app = "-app" # overwrite is False, append instead
        except AttributeError:
            app = ""
        COMMAND = "orientation_magic.py -WD {} -f {} -ncn {} -ocn {} -dcn {} -gmt {} -mcd {} {} -ID {}".format(WD, infile, ncn, ocn, dcn, gmt, mcd, app, ID)
        pw.run_command_and_close_window(self, COMMAND, None)

    def on_cancelButton(self,event):
        self.Destroy()
        self.Parent.Raise()

    def on_helpButton(self, event):
        pw.on_helpButton("orientation_magic.py -h")


class ImportAzDipFile(wx.Frame):

    title = "Import AzDip format file"
    
    def __init__(self, parent, WD):
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title)
        self.panel = wx.ScrolledWindow(self)
        self.WD = WD
        self.InitUI()

    def InitUI(self):
        pnl = self.panel
        TEXT = "Import an AzDip format file into your working directory"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0 ----
        self.bSizer0 = pw.choose_file(pnl, 'add', method = self.on_add_file_button)

        #---sizer 1 ----
        self.bSizer1 = pw.sampling_particulars(pnl)

        #---sizer 2 ---
        self.bSizer2 = pw.select_specimen_ncn(pnl)

        #---sizer 3 ---
        self.bSizer3 = pw.labeled_text_field(pnl, "Location:")

        #---sizer 4 ----
        TEXT = "Overwrite er_samples.txt file?"
        label1 = "yes, overwrite file in working directory"
        label2 = "no, update existing er_samples file"
        er_samples_file_present = True
        try:
            open(self.WD + "/er_samples.txt", "rU")
        except Exception as ex:
            er_samples_file_present = False
        if er_samples_file_present:
            self.bSizer4 = pw.labeled_yes_or_no(pnl, TEXT, label1, label2)

        #---buttons ---
        hboxok = pw.btn_panel(self, pnl)


        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        try:
            vbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        except AttributeError:
            pass
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)        
        vbox.AddSpacer(20)

        hbox_all = wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.AddSpacer(vbox)

        self.panel.SetSizer(hbox_all)
        self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()

    def on_add_file_button(self,event):
        text = "choose file to convert to MagIC"
        pw.on_add_file_button(self.bSizer0, self.WD, event, text)

    def on_okButton(self, event):
        WD = self.WD
        full_infile = self.bSizer0.return_value()
        #ind = full_infile.rfind('/')
        #infile = full_infile[ind+1:]
        #ID = full_infile[:ind+1]
        particulars = [p.split(':')[0] for p in self.bSizer1.return_value()]
        mcd = ':'.join(particulars)
        ncn = self.bSizer2.return_value()
        loc = self.bSizer3.return_value()
        if loc:
            loc = "-loc " + loc
        try:
            app = self.bSizer4.return_value()
            if app:
                app = "" # overwrite is True
            else:
                app = "-app" # overwrite is False, append instead
        except AttributeError:
            app = ""
        COMMAND = "azdip_magic.py -f {} -ncn {} {} -mcd {} {}".format(full_infile, ncn, loc, mcd, app)
        #print COMMAND
        pw.run_command_and_close_window(self, COMMAND, "er_samples.txt")

    def on_cancelButton(self,event):
        self.Destroy()
        self.Parent.Raise()

    def on_helpButton(self, event):
        pw.on_helpButton("azdip_magic.py -h")


class ImportODPCoreSummary(wx.Frame):

    title = "Import ODP Core Summary csv file"
    
    def __init__(self, parent, WD):
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title)
        self.panel = wx.ScrolledWindow(self)
        self.WD = WD
        self.InitUI()

    def InitUI(self):
        pnl = self.panel
        TEXT = "ODP Core Summary csv file"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0 ----
        self.bSizer0 = pw.choose_file(pnl, 'add', method = self.on_add_file_button)

        #---sizer 1 ----
        TEXT = "Overwrite er_samples.txt file?"
        label1 = "yes, overwrite file in working directory"
        label2 = "no, update existing er_samples file"
        er_samples_file_present = True
        try:
            open(self.WD + "/er_samples.txt", "rU")
        except Exception as ex:
            er_samples_file_present = False
        if er_samples_file_present:
            self.bSizer1 = pw.labeled_yes_or_no(pnl, TEXT, label1, label2)

        #---buttons ---
        hboxok = pw.btn_panel(self, pnl)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        try:
            vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        except AttributeError:
            pass
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)        
        vbox.AddSpacer(20)

        hbox_all = wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.AddSpacer(vbox)

        self.panel.SetSizer(hbox_all)
        self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()

    def on_add_file_button(self,event):
        text = "choose file to convert to MagIC"
        pw.on_add_file_button(self.bSizer0, self.WD, event, text)

    def on_okButton(self, event):
        WD = self.WD
        full_infile = self.bSizer0.return_value()
        index = full_infile.rfind('/')
        infile = full_infile[index+1:]
        ID = full_infile[:index+1]
        try:
            Fsa = self.bSizer1.return_value()
            if Fsa:
                Fsa = ''
            else:
                Fsa = "-Fsa er_samples.txt"
        except AttributeError:
            Fsa = ''
        COMMAND = "?? -WD {} -f {} {} -ID {}".format(WD, infile, Fsa, ID)
        print COMMAND, "seems in MagIC.py to just copy this file in?"
        #pw.run_command_and_close_window(self, COMMAND, "er_samples.txt")

    def on_cancelButton(self,event):
        self.Destroy()
        self.Parent.Raise()

    def on_helpButton(self, event):
        pw.on_helpButton("?? -h")




class ImportODPSampleSummary(wx.Frame):

    title = "Import ODP Sample Summary csv file"
    
    def __init__(self, parent, WD):
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title)
        self.panel = wx.ScrolledWindow(self)
        self.WD = WD
        self.InitUI()

    def InitUI(self):
        pnl = self.panel
        TEXT = "ODP Sample Summary csv file"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0 ----
        self.bSizer0 = pw.choose_file(pnl, 'add', method = self.on_add_file_button)

        #---sizer 1 ----
        TEXT = "Overwrite er_samples.txt file?"
        label1 = "yes, overwrite file in working directory"
        label2 = "no, update existing er_samples file"
        er_samples_file_present = True
        try:
            open(self.WD + "/er_samples.txt", "rU")
        except Exception as ex:
            er_samples_file_present = False
        if er_samples_file_present:
            self.bSizer1 = pw.labeled_yes_or_no(pnl, TEXT, label1, label2)

        #---buttons ---
        hboxok = pw.btn_panel(self, pnl)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        try:
            vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        except AttributeError:
            pass
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)        
        vbox.AddSpacer(20)

        hbox_all = wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.AddSpacer(vbox)

        self.panel.SetSizer(hbox_all)
        self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()

    def on_add_file_button(self,event):
        text = "choose file to convert to MagIC"
        pw.on_add_file_button(self.bSizer0, self.WD, event, text)

    def on_okButton(self, event):
        WD = self.WD
        full_infile = self.bSizer0.return_value()
        index = full_infile.rfind('/')
        infile = full_infile[index+1:]
        ID = full_infile[:index+1]
        try:
            Fsa = self.bSizer1.return_value()
            if Fsa:
                Fsa = ''
            else:
                Fsa = "-Fsa er_samples.txt"
        except AttributeError:
            Fsa = ''
        COMMAND = "ODP_samples_magic.py -WD {} -f {} {} -ID {}".format(WD, infile, Fsa, ID)
        print COMMAND
        #pw.run_command_and_close_window(self, COMMAND, "er_samples.txt")

    def on_cancelButton(self,event):
        self.Destroy()
        self.Parent.Raise()

    def on_helpButton(self, event):
        pw.on_helpButton("ODP_samples_magic.py -h")



class ImportModelLatitude(wx.Frame):

    title = "Import Model Latitude data file"
    
    def __init__(self, parent, WD):
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title)
        self.panel = wx.ScrolledWindow(self)
        self.WD = WD
        self.InitUI()

    def InitUI(self):
        pnl = self.panel
        TEXT = "Model latitude data"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0 ----
        self.bSizer0 = pw.choose_file(pnl, 'add', method = self.on_add_file_button)

        hboxok = pw.btn_panel(self, pnl)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)        
        vbox.AddSpacer(20)

        hbox_all = wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.AddSpacer(vbox)

        self.panel.SetSizer(hbox_all)
        self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()

    def on_add_file_button(self,event):
        text = "choose file to convert to MagIC"
        pw.on_add_file_button(self.bSizer0, self.WD, event, text)

    def on_okButton(self, event):
        infile = self.bSizer0.return_value()
        outfile = self.WD + infile[infile.rfind('/'):]
        COMMAND = "cp {} {}".format(infile, self.WD)
        pw.run_command_and_close_window(self, COMMAND, outfile)

    def on_cancelButton(self,event):
        self.Destroy()
        self.Parent.Raise()

    def on_helpButton(self, event):
        pw.on_helpButton(".py -h")



class ImportKly4s(wx.Frame):

    title = "kly4s format"
    
    def __init__(self, parent, WD):
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title)
        self.panel = wx.ScrolledWindow(self)
        self.WD = WD
        self.InitUI()

    def InitUI(self):
        pnl = self.panel
        TEXT = "kly4s format"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0 ----
        self.bSizer0 = pw.choose_file(pnl, btn_text="Add kly4s format file", method = self.on_add_file_button)
        """
        -fad AZDIP: specify AZDIP file with orientations, will create er_samples.txt file                                           
        -fsa SFILE: specify existing er_samples.txt file with orientation information                                             
        -fsp SPFILE: specify existing er_specimens.txt file for appending                                                         
        -F MFILE: specify magic_measurements output file                                                                             
        -Fa AFILE: specify rmag_anisotropy output file                                                                                
        -ocn ORCON:  specify orientation convention: default is #3 below -only with AZDIP file                                     
        -usr USER: specify who made the measurements                                                                                    
        -loc LOC: specify location name for study                                                                                      
        -ins INST: specify instrument used                                                                                      
        -spc SPEC: specify number of characters to specify specimen from sample   
        -ncn NCON:  specify naming convention: default is #1 below 
        """

        #---sizer 1 ---
        self.bSizer1 = pw.choose_file(pnl, btn_text='add AZDIP file (optional)', method = self.on_add_AZDIP_file_button)
        self.bSizer1a = pw.select_specimen_ocn(pnl)
        

        #---sizer 2 ----
        self.bSizer2 = pw.labeled_text_field(pnl)

        #---sizer 3 ---
        self.bSizer3 = pw.specimen_n(pnl)

        #---sizer 4 ---
        self.bSizer4 = pw.select_specimen_ncn(pnl)

        #---sizer 5 ---
        self.bSizer5 = pw.select_specimen_ocn(pnl)
        self.bSizer5.select_orientation_convention.SetSelection(2)

        #---sizer 6 ---
        self.bSizer6 = pw.labeled_text_field(pnl, "Location name:")

        #---sizer 7 ---
        self.bSizer7 = pw.labeled_text_field(pnl, "Instrument name (optional):")


        #---buttons ---
        hboxok = pw.btn_panel(self, pnl)

        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(self.bSizer6, flag=wx.ALIGN_LEFT|wx.RIGHT, border=5)
        hbox1.Add(self.bSizer7, flag=wx.ALIGN_LEFT)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer1a, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer5, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(hbox1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer5, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer6, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #try:
        #    vbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #except AttributeError:
        #    pass
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)        
        vbox.AddSpacer(20)

        self.hbox_all = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox_all.AddSpacer(20)
        self.hbox_all.AddSpacer(vbox)

        self.panel.SetSizer(self.hbox_all)
        self.panel.SetScrollbars(20, 20, 50, 50)
        self.bSizer1a.ShowItems(False)
        self.hbox_all.Fit(self)
        self.Show()
        self.Centre()

    def on_add_file_button(self,event):
        text = "choose file to convert to MagIC"
        #pw.on_add_file_button(self.panel, self.WD, event, text)
        pw.on_add_file_button(self.bSizer0, self.WD, event, text)

    def on_add_AZDIP_file_button(self,event):
        text = "choose AZDIP file (optional)"
        pw.on_add_file_button(self.bSizer1, self.WD, event, text)
        # show ocn widget


    def on_okButton(self, event):
        WD = self.WD
        full_infile = self.bSizer0.return_value()
        infile = full_infile[full_infile.rfind('/')+1:]
        outfile = infile + ".magic"
        full_azdip_file = self.bSizer1.return_value()
        azdip_file = full_azdip_file[full_azdip_file.rfind('/')+1:]
        ID = full_infile[:full_infile.rfind('/')+1]
        if azdip_file:
            azdip_file = "-fad " + azdip_file
        try:
            ocn = "-ocn" + self.bSizer1a.return_value()
        except:
            ocn = ""
        user = self.bSizer2.return_value()
        if user:
            user = "-usr " + user
        n = self.bSizer3.return_value()
        if n:
            n = "-spc " + str(n)
        ncn = self.bSizer4.return_value()
        #
        loc = self.bSizer6.return_value()
        if loc:
            loc = "-loc " + loc
        ins = self.bSizer7.return_value()
        if ins:
            ins = "-ins " + ins
        COMMAND = "kly4s_magic.py -WD {} -f {} -F {} {} -ncn {} -ocn {} {} {} {} {} -ID {}".format(self.WD, infile, outfile, azdip_file, ncn, ocn, user, n, loc, ins, ID)
        print COMMAND
        pw.run_command_and_close_window(self, COMMAND, outfile)

    def on_cancelButton(self,event):
        self.Destroy()
        self.Parent.Raise()

    def on_helpButton(self, event):
        pw.on_helpButton("kly4s_magic.py -h")


class something(wx.Frame):

    title = ""
    
    def __init__(self, parent, WD):
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title)
        self.panel = wx.ScrolledWindow(self)
        self.WD = WD
        self.InitUI()

    def InitUI(self):
        pnl = self.panel
        TEXT = "some text"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0 ----
        self.bSizer0 = pw.choose_file(pnl, 'add', method = self.on_add_file_button)

        #---sizer 1 ----


        #---sizer 2 ---


        #---sizer 3 ---


        #---sizer 4 ----
        #try:
        #    open(self.WD + "/er_samples.txt", "rU")
        #except Exception as ex:
        #    er_samples_file_present = False
        #if er_samples_file_present:
        #    self.bSizer4 = pw.labeled_yes_or_no(pnl, TEXT, label1, label2)

        #---buttons ---
        hboxok = pw.btn_panel(self, pnl)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #try:
        #    vbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #except AttributeError:
        #    pass
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)        
        vbox.AddSpacer(20)

        hbox_all = wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.AddSpacer(vbox)

        self.panel.SetSizer(hbox_all)
        self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()

    def on_add_file_button(self,event):
        text = "choose file to convert to MagIC"
        pw.on_add_file_button(self.bSizer0, self.WD, event, text)

    def on_okButton(self, event):
        COMMAND = ""
        print COMMAND
        #pw.run_command_and_close_window(self, COMMAND, "er_samples.txt")

    def on_cancelButton(self,event):
        self.Destroy()
        self.Parent.Raise()

    def on_helpButton(self, event):
        pw.on_helpButton(".py -h")



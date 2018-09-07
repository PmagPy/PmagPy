#!/usr/bin/env pythonw

#--------------------------------------------------------------
# converting magnetometer files to MagIC format
#--------------------------------------------------------------

import wx
import os
import sys
import shutil
import subprocess
import wx.grid
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib import pyplot as plt
import pmagpy.pmag as pmag
import pmagpy.ipmag as ipmag
import dialogs.pmag_widgets as pw
from programs.conversion_scripts import agm_magic
from pmagpy import convert_2_magic as convert

class ImportAzDipFile(wx.Frame):

    title = "Import AzDip format file"

    def __init__(self, parent, WD):
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title, name='azdip_window')
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
        self.bSizer2 = pw.select_ncn(pnl)

        #---sizer 3 ---
        self.bSizer3 = pw.labeled_text_field(pnl, "Location:")

        #---sizer 4 ----
        TEXT = "Overwrite er_samples.txt file?"
        label1 = "yes, overwrite file in working directory"
        label2 = "no, update existing er_samples file"
        er_samples_file_present = True
        try:
            er_samp_file = open(os.path.join(self.WD, "er_samples.txt"), "r")
            er_samp_file.close()
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
        hbox_all.Add(vbox)

        self.panel.SetSizer(hbox_all)
        self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()

    def on_add_file_button(self,event):
        text = "choose file to convert to MagIC"
        pw.on_add_file_button(self.bSizer0, text)

    def on_okButton(self, event):
        options = {}
        os.chdir(self.WD)
        output_dir = self.WD
        full_infile = self.bSizer0.return_value()
        input_dir, infile = os.path.split(full_infile)
        data_model_num = self.Parent.data_model_num
        if data_model_num == 2:
            Fsa = os.path.splitext(infile)[0] + "_er_samples.txt"
        else:
            Fsa = os.path.splitext(infile)[0] + "_samples.txt"
        mcd = self.bSizer1.return_value()
        ncn = self.bSizer2.return_value()
        loc = self.bSizer3.return_value()
        try:
            app = self.bSizer4.return_value()
            if app:
                app = False #"" # overwrite is True
            else:
                app = True #"-app" # overwrite is False, append instead
        except AttributeError:
            app = ""
        #COMMAND = "azdip_magic.py -f {} -Fsa {} -ncn {} {} {} {}".format(full_infile, Fsa, ncn, loc, mcd, app)

        if len(str(ncn)) > 1:
            ncn, Z = ncn.split('-')
        else:
            Z = 1

        program_completed, error_message = ipmag.azdip_magic(infile, Fsa, ncn, Z, mcd, loc,
                                                             app, output_dir, input_dir, data_model_num)
        if program_completed:
            args = [str(arg) for arg in [infile, Fsa, ncn, Z, mcd, loc, app] if arg]
            pw.close_window(self, 'ipmag.azdip_magic({}))'.format(", ".join(args)), Fsa)
            pw.simple_warning('You have created new MagIC files.\nMake sure to go to Pmag GUI step 1 to combine and rename them before proceeding to analysis or upload!')
        else:
            pw.simple_warning(error_message)


    def on_cancelButton(self,event):
        self.Destroy()
        self.Parent.Raise()

    def on_helpButton(self, event):
        pw.on_helpButton(text=ipmag.azdip_magic.__doc__)


#class ImportODPCoreSummary(wx.Frame):
class MoveFileIntoWD(wx.Frame):

    title = "Import any file into your working directory"

    def __init__(self, parent, WD):
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title, name='any file')
        self.panel = wx.ScrolledWindow(self)
        self.WD = WD
        self.InitUI()

    def InitUI(self):
        pnl = self.panel
        TEXT = "Any file type"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0 ----
        self.bSizer0 = pw.choose_file(pnl, 'add', method = self.on_add_file_button)

        #---buttons ---
        hboxok = pw.btn_panel(self, pnl)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)
        vbox.AddSpacer(20)

        hbox_all = wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.Add(vbox)

        self.panel.SetSizer(hbox_all)
        self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()

    def on_add_file_button(self,event):
        text = "choose file to copy to working directory"
        pw.on_add_file_button(self.bSizer0, text)

    def on_okButton(self, event):
        os.chdir(self.WD)
        WD = self.WD
        full_infile = self.bSizer0.return_value()
        if not full_infile:
            pw.simple_warning('You must provide a file')
            return False
        infile = os.path.join(WD, os.path.split(full_infile)[1])
        shutil.copyfile(full_infile, os.path.join(WD, infile))
        pw.close_window(self, 'Copy infile to {}'.format(WD), infile)


    def on_cancelButton(self,event):
        self.Destroy()
        self.Parent.Raise()

    def on_helpButton(self, event):
        dlg = wx.MessageDialog(self, "Unaltered file will be copied to working directory", "Help", style=wx.OK|wx.ICON_EXCLAMATION)
        dlg.ShowModal()
        dlg.Destroy()


class ImportIODPSampleSummary(wx.Frame):

    title = "Import IODP Sample Summary csv file"

    def __init__(self, parent, WD):
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title, name='IODP_samples')
        self.panel = wx.ScrolledWindow(self)
        self.WD = WD
        self.InitUI()

    def InitUI(self):
        pnl = self.panel
        TEXT = "IODP Sample Summary csv file"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0 ----
        self.bSizer0 = pw.choose_file(pnl, 'add', method = self.on_add_file_button)

        #---buttons ---
        hboxok = pw.btn_panel(self, pnl)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)
        vbox.AddSpacer(20)

        hbox_all = wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.Add(vbox)

        self.panel.SetSizer(hbox_all)
        self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()

    def on_add_file_button(self,event):
        text = "choose file to convert to MagIC"
        pw.on_add_file_button(self.bSizer0, text)

    def on_okButton(self, event):
        os.chdir(self.WD)
        WD = self.WD
        full_infile = self.bSizer0.return_value()
        ID, infile = os.path.split(full_infile)
        Fsa = infile[:infile.find('.')] + "_er_samples.txt"
        program_ran, error_message = convert.iodp_samples(infile, Fsa, WD, ID)
        if not program_ran:
            pw.simple_warning(error_message)
        else:
            COMMAND = "iodp_samples_magic.py -WD {} -f {} -Fsa {} -ID {}".format(WD, infile, Fsa, ID)
            pw.close_window(self, COMMAND, Fsa)
            pw.simple_warning('You have created new MagIC files.\nMake sure to go to Pmag GUI step 1 to combine and rename them before proceeding to analysis or upload!')
        #pw.run_command_and_close_window(self, COMMAND, Fsa)

    def on_cancelButton(self,event):
        self.Destroy()
        self.Parent.Raise()

    def on_helpButton(self, event):
        pw.on_helpButton(text=convert.iodp_samples.__doc__)


"""
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
        hbox_all.Add(vbox)

        self.panel.SetSizer(hbox_all)
        self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()

    def on_add_file_button(self,event):
        text = "choose file to convert to MagIC"
        pw.on_add_file_button(self.bSizer0, text)

    def on_okButton(self, event):
        os.chdir(self.WD)
        infile = os.path.split(self.bSizer0.return_value())[1]
        outfile = os.path.join(self.WD, infile)
        COMMAND = "cp {} {}".format(infile, self.WD)
        pw.run_command_and_close_window(self, COMMAND, outfile)

    def on_cancelButton(self,event):
        self.Destroy()
        self.Parent.Raise()

    def on_helpButton(self, event):
        dlg = wx.MessageDialog(self, "Unaltered file will be copied to working directory", "Help", style=wx.OK|wx.ICON_EXCLAMATION)
        dlg.ShowModal()
        dlg.Destroy()
"""

class ImportKly4s(wx.Frame):

    title = "kly4s format"

    def __init__(self, parent, WD):
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title, name='kly4s')
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

        #---sizer 1 ---
        # changed to er_samples only, not azdip
        self.bSizer1 = pw.choose_file(pnl, btn_text='add samples file (optional)', method = self.on_add_AZDIP_file_button)

        #---sizer 2 ----
        self.bSizer2 = pw.labeled_text_field(pnl)

        #---sizer 3 ---
        self.bSizer3 = pw.specimen_n(pnl)

        #---sizer 4 ---
        self.bSizer4 = pw.select_ncn(pnl)

        #---sizer 5 ---
        #self.bSizer5 = pw.select_specimen_ocn(pnl)

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
        vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(hbox1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)
        vbox.AddSpacer(20)

        self.hbox_all = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox_all.AddSpacer(20)
        self.hbox_all.Add(vbox)

        self.panel.SetSizer(self.hbox_all)
        self.panel.SetScrollbars(20, 20, 50, 50)
        self.hbox_all.Fit(self)
        self.Show()
        self.Centre()

    def on_add_file_button(self,event):
        text = "choose file to convert to MagIC"
        pw.on_add_file_button(self.bSizer0, text)

    def on_add_AZDIP_file_button(self,event):
        text = "choose samples file (optional)"
        pw.on_add_file_button(self.bSizer1, text)

    def on_okButton(self, event):
        os.chdir(self.WD)
        WD = self.WD
        full_infile = self.bSizer0.return_value()
        ID, infile = os.path.split(full_infile)
        outfile = infile + ".magic"
        if self.Parent.data_model_num == 2:
            spec_outfile = infile[:infile.find('.')] + "_er_specimens.txt"
            ani_outfile = infile[:infile.find('.')] + "_rmag_anisotropy.txt"
            site_outfile = ''
        else:
            spec_outfile = infile[:infile.find('.')] + "_specimens.txt"
            ani_outfile = ''
            site_outfile = infile[:infile.find('.')] + "_sites.txt"
        full_samp_file = self.bSizer1.return_value()
        samp_file = os.path.split(full_samp_file)[1]
        if not samp_file:
            samp_outfile = infile[:infile.find('.')] + "_samples.txt"
        else:
            samp_outfile = samp_file
        user = self.bSizer2.return_value()
        if user:
            user = "-usr " + user
        specnum = self.bSizer3.return_value()
        n = "-spc " + str(specnum)
        ncn = self.bSizer4.return_value()
        loc = self.bSizer6.return_value()
        if loc:
            location = loc
            loc = "-loc " + loc
        else:
            location = ''
        ins = self.bSizer7.return_value()
        if ins:
            instrument = ins
            ins = "-ins " + ins
        else:
            instrument='SIO-KLY4S'
        COMMAND = "kly4s_magic.py -WD {} -f {} -F {} -fsa {} -ncn {} {} {} {} {} -ID {} -fsp {} -DM {}".format(self.WD, infile, outfile, samp_file, ncn, user, n, loc, ins, ID, spec_outfile, self.Parent.data_model_num)
        program_ran, error_message = convert.kly4s(infile, specnum=specnum,
                                                   locname=location, inst=instrument,
                                                   samp_con=ncn, user=user, measfile=outfile,
                                                   aniso_outfile=ani_outfile,
                                                   samp_infile=samp_file, spec_infile='',
                                                   spec_outfile=spec_outfile,
                                                   dir_path=self.WD, input_dir_path=ID,
                                                   data_model_num=self.Parent.data_model_num,
                                                   samp_outfile=samp_outfile,
                                                   site_outfile=site_outfile)
        if program_ran:
            pw.close_window(self, COMMAND, outfile)
            outfiles = [f for f in [outfile, spec_outfile, ani_outfile] if f]
            pw.simple_warning('You have created the following files: {}\nMake sure to go to Pmag GUI step 1 to combine and rename them before proceeding to analysis or upload!'.format(", ".join(outfiles)))
        else:
            pw.simple_warning(error_message)

    def on_cancelButton(self,event):
        self.Destroy()
        self.Parent.Raise()

    def on_helpButton(self, event):
        pw.on_helpButton(text=convert.kly4s.__doc__)


class ImportK15(wx.Frame):

    title = "Import K15 format file"

    def __init__(self, parent, WD):
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title)
        self.panel = wx.ScrolledWindow(self)
        self.WD = WD
        self.InitUI()

    def InitUI(self):
        pnl = self.panel
        TEXT = "Import K15 format file"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)


        #---sizer 0 ----
        self.bSizer0 = pw.choose_file(pnl, 'add', method = self.on_add_file_button)

        #---sizer 1 ----
        self.bSizer1 = pw.specimen_n(pnl)

        #---sizer 2 ---
        self.bSizer2 = pw.select_ncn(pnl)

        #---sizer 3 ---
        self.bSizer3 = pw.labeled_text_field(pnl, label="Location name:")

        #---sizer 4 ---
        #self.bSizer4 = pw.labeled_text_field(pnl, label="Instrument name (optional):")

        #---buttons ---
        hboxok = pw.btn_panel(self, pnl)

        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.LEFT, border=5)
        #hbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(hbox, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)
        vbox.AddSpacer(20)

        hbox_all = wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.Add(vbox)

        self.panel.SetSizer(hbox_all)
        self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()

    def on_add_file_button(self,event):
        text = "choose file to convert to MagIC"
        pw.on_add_file_button(self.bSizer0, text)

    def on_okButton(self, event):
        data_model_num = self.Parent.data_model_num
        os.chdir(self.WD)
        full_infile = self.bSizer0.return_value()
        ID, infile = os.path.split(full_infile)
        outfile = infile + ".magic"
        if data_model_num == 3:
            samp_outfile = infile[:infile.find('.')] + "_samples.txt"
        else:
            samp_outfile = infile[:infile.find('.')] + "_er_samples.txt"
        WD = self.WD
        specnum = self.bSizer1.return_value()
        ncn = self.bSizer2.return_value()
        loc = self.bSizer3.return_value()
        if loc:
            location = loc
            loc = "-loc " + loc
        else:
            location = "unknown"
        if data_model_num == 3:
            aniso_outfile = infile + '_specimens.txt'
        else:
            aniso_outfile = infile + '_rmag_anisotropy.txt'
        # result file is only used in data model 3, otherwise ignored
        aniso_results_file = infile + '_rmag_results.txt'
        DM = ""
        if data_model_num == 2:
            DM = "-DM 2"
        COMMAND = "k15_magic.py -WD {} -f {} -F {} -ncn {} -spc {} {} -ID {} -Fsa {} -Fa {} -Fr {} {}".format(WD, infile, outfile, ncn, specnum, loc, ID, samp_outfile, aniso_outfile, aniso_results_file, DM)
        program_ran, error_message = convert.k15(infile, WD, ID, outfile, aniso_outfile, samp_outfile,
                                                 aniso_results_file, specnum, ncn, location, data_model_num)
        print(COMMAND)
        if program_ran:
            pw.close_window(self, COMMAND, outfile)
            outfiles = [f for f in [outfile, samp_outfile, aniso_outfile] if f]
            pw.simple_warning('You have created the following files: {}\nMake sure to go to Pmag GUI step 1 to combine and rename them before proceeding to analysis or upload!'.format(", ".join(outfiles)))
        else:
            pw.simple_warning(error_message)
        #print COMMAND
        #pw.run_command_and_close_window(self, COMMAND, outfile)

    def on_cancelButton(self,event):
        self.Destroy()
        self.Parent.Raise()

    def on_helpButton(self, event):
        pw.on_helpButton(text=convert.k15_magic.__doc__)


class ImportSufarAscii(wx.Frame):

    title = "Import Sufar Ascii format file"

    def __init__(self, parent, WD):
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title, name='Sufar')
        self.panel = wx.ScrolledWindow(self)
        self.WD = WD
        self.InitUI()

    def InitUI(self):
        pnl = self.panel
        TEXT = "Sufar Ascii format file"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0 ----
        self.bSizer0 = pw.choose_file(pnl, 'add', method = self.on_add_file_button)

        #---sizer 1 ----
        self.bSizer1 = pw.labeled_text_field(pnl)

        #---sizer 2 ----
        self.bSizer2 = pw.specimen_n(pnl)

        #---sizer 3 ---
        self.bSizer3 = pw.select_ncn(pnl)

        #---sizer 4 ---
        self.bSizer4 = pw.labeled_text_field(pnl, label="Location name:")

        #---sizer 5 ---
        self.bSizer5 = pw.labeled_text_field(pnl, label="Instrument name (optional):")

        #---sizer 6 ---
        TEXT = "Use default mode?"
        label1 = "spinning (default)"
        label2 = "static 15 position mode"
        self.bSizer6 = pw.labeled_yes_or_no(pnl, TEXT, label1, label2)

        #---buttons ---
        hboxok = pw.btn_panel(self, pnl)

        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.LEFT, border=5)
        hbox.Add(self.bSizer5, flag=wx.ALIGN_LEFT)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(hbox, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer6, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #try:
        #    vbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #except AttributeError:
        #    pass
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)
        vbox.AddSpacer(20)

        hbox_all = wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.Add(vbox)

        self.panel.SetSizer(hbox_all)
        self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()

    def on_add_file_button(self,event):
        text = "choose file to convert to MagIC"
        pw.on_add_file_button(self.bSizer0, text)

    def on_okButton(self, event):
        os.chdir(self.WD)
        WD = self.WD
        full_infile = self.bSizer0.return_value()
        ID, infile = os.path.split(full_infile)
        meas_outfile = infile[:infile.find('.')] + ".magic"
        if self.Parent.data_model_num == 2:
            aniso_outfile = infile[:infile.find('.')] + "_rmag_anisotropy.txt"
            spec_outfile = infile[:infile.find('.')] + "_er_specimens.txt"
            samp_outfile = infile[:infile.find('.')] + "_er_samples.txt"
            site_outfile = infile[:infile.find('.')] + "_er_sites.txt"
        else:
            aniso_outfile = ''
            spec_outfile = infile[:infile.find('.')] + "_specimens.txt"
            samp_outfile = infile[:infile.find('.')] + "_samples.txt"
            site_outfile = infile[:infile.find('.')] + "_sites.txt"


        usr = self.bSizer1.return_value()
        if usr:
            user = usr
            usr = "-usr " + usr
        else:
            user = ""

        specnum = self.bSizer2.return_value()
        ncn = self.bSizer3.return_value()
        loc = self.bSizer4.return_value()
        if loc:
            location = loc
            loc = "-loc " + loc
        else:
            location = "unknown"
        instrument = self.bSizer5.return_value()
        if instrument:
            ins = "-ins " + instrument
        else:
            ins = ''
        k15 = self.bSizer6.return_value()
        if k15:
            k15 = ""
            static_15_position_mode = False
        else:
            k15 = "-k15"
            static_15_position_mode = True
        spec_infile = None
        data_model_num = self.Parent.data_model_num
        COMMAND = "SUFAR4-asc_magic.py -WD {} -f {} -F {} {} -spc {} -ncn {} {} {} {} -ID {} -DM {}".format(WD, infile, meas_outfile, usr, specnum, ncn, loc, ins, k15, ID, data_model_num)
        program_ran, error_message = convert.sufar4(infile, meas_outfile, aniso_outfile,
                                                    spec_infile, spec_outfile, samp_outfile,
                                                    site_outfile, specnum, ncn, user,
                                                    location, instrument,static_15_position_mode,
                                                    WD, ID, data_model_num)
        if program_ran:
            pw.close_window(self, COMMAND, meas_outfile)
            outfiles = [meas_outfile, spec_outfile, samp_outfile, site_outfile]
            pw.simple_warning('You have created the following files: {}\nMake sure to go to Pmag GUI step 1 to combine and rename them before proceeding to analysis or upload!'.format(", ".join(outfiles)))

        else:
            pw.simple_warning(error_message)

    def on_cancelButton(self,event):
        self.Destroy()
        self.Parent.Raise()

    def on_helpButton(self, event):
        pw.on_helpButton(text=convert.sufar4.__doc__)



class ImportAgmFile(wx.Frame):

    title = "Import single .agm file"

    def __init__(self, parent, WD):
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title, name='agm_file')
        self.panel = wx.ScrolledWindow(self)
        self.WD = WD
        self.InitUI()

    def InitUI(self):
        pnl = self.panel
        TEXT = "Micromag agm format file"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0 ----
        self.bSizer0 = pw.choose_file(pnl, 'add', method = self.on_add_file_button)

        #---sizer 1 ---
        self.bSizer1 = pw.labeled_text_field(pnl)

        #---sizer 2 ----
        self.bSizer2 = pw.specimen_n(pnl)

        #---sizer 3 ---
        self.bSizer3 = pw.select_ncn(pnl)

        #---sizer 4 ---
        self.bSizer4 = pw.labeled_text_field(pnl, label="Location name:")

        #---sizer 5 ---
        self.bSizer5 = pw.labeled_text_field(pnl, label="Instrument name (optional):")

        #---sizer 6---
        self.bSizer6 = pw.labeled_yes_or_no(pnl, "Units", "CGS units (default)", "SI units")

        #---sizer 7 ---
        self.bSizer7 = pw.check_box(pnl, "backfield curve")

        #---buttons ---
        hboxok = pw.btn_panel(self, pnl)

        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.LEFT, border=5)
        hbox1.Add(self.bSizer5, flag=wx.ALIGN_LEFT)
        hbox2.Add(self.bSizer6, flag=wx.ALIGN_LEFT|wx.LEFT, border=5)
        hbox2.Add(self.bSizer7, flag=wx.ALIGN_LEFT)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(hbox1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(hbox2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)
        vbox.AddSpacer(20)

        hbox_all = wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.Add(vbox)

        self.panel.SetSizer(hbox_all)
        self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()

    def on_add_file_button(self,event):
        text = "choose file to convert to MagIC"
        pw.on_add_file_button(self.bSizer0, text)

    def on_okButton(self, event):
        os.chdir(self.WD)
        options_dict={}
        WD = self.WD
        full_infile = self.bSizer0.return_value()
        ID, infile = os.path.split(full_infile)
        outfile = infile + ".magic"
        #spec_outfile = infile[:infile.find('.')] + "_er_specimens.txt"
        spec_outfile = infile[:infile.find('.')] + "_specimens.txt"
        usr = self.bSizer1.return_value()
        user = usr
        if usr:
            usr = "-usr " + usr
        spc = self.bSizer2.return_value()
        ncn = self.bSizer3.return_value()
        loc = self.bSizer4.return_value()
        location = loc
        if loc:
            loc = "-loc " + loc
        ins = self.bSizer5.return_value()
        #if ins:
        #    ins = "-ins " + ins
        units = self.bSizer6.return_value()
        if units:
            units = 'cgs'
        else:
            units = 'SI'
        bak = ''
        backfield_curve = False
        if self.bSizer7.return_value():
            bak = "-bak"
            backfield_curve = True
        magicoutfile=os.path.split(infile)[1]+".magic"

        SPEC_OUTFILE =  magicoutfile[:magicoutfile.find('.')] + "_specimens.txt"
        SAMP_OUTFILE =  magicoutfile[:magicoutfile.find('.')] + "_samples.txt"
        SITE_OUTFILE =  magicoutfile[:magicoutfile.find('.')] + "_sites.txt"
        LOC_OUTFILE =  magicoutfile[:magicoutfile.find('.')] + "_locations.txt"
        options_dict['meas_outfile'] = outfile
        options_dict['agm_file'] = infile
        options_dict['spec_outfile'] = SPEC_OUTFILE
        options_dict['samp_outfile'] = SAMP_OUTFILE
        options_dict['site_outfile'] = SITE_OUTFILE
        options_dict['loc_outfile'] = LOC_OUTFILE
        options_dict['specnum'] =spc
        COMMAND = "agm_magic.py -WD {} -ID {} -f {} -F {} -Fsp {} {} -spc {} -ncn {} {} {} -u {} {}".format(WD, ID, infile, outfile, spec_outfile, usr, spc, ncn, loc, ins, units, bak)
        samp_infile = None
        print("COMMAND: ",COMMAND)
        if convert.agm(**options_dict):
            pw.close_window(self,COMMAND,outfile)
            pw.simple_warning('You have created the following files: {}\nMake sure to go to Pmag GUI step 1 to combine and rename them before proceeding to analysis or upload!'.format(outfile))
        else:
            pw.simple_warning()


    def on_cancelButton(self,event):
        self.Destroy()
        self.Parent.Raise()

    def on_helpButton(self, event):
        pw.on_helpButton(text=agm_magic.do_help())


class ImportAgmFolder(wx.Frame):

    title = "Import folder of Micromag agm files"

    def __init__(self, parent, WD):
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title, name='agm_directory')
        self.panel = wx.ScrolledWindow(self)
        self.WD = WD
        self.InitUI()

    def InitUI(self):
        pnl = self.panel
        TEXT = "Folder of agm files"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0 ----
        self.bSizer0 = pw.choose_dir(pnl, 'add', method = self.on_add_dir_button)

        #---sizer 0a ----
        text = "Note on input directory:\nAll file names must be SPECIMEN_NAME.AGM for hysteresis\nor SPECIMEN_NAME.IRM for backfield (case insensitive)"
        self.bSizer0a = pw.simple_text(pnl, text)

        #---sizer 1 ----
        self.bSizer1 = pw.labeled_text_field(pnl)

        #---sizer 2 ----
        self.bSizer2 = pw.specimen_n(pnl)

        #---sizer 3 ---
        self.bSizer3 = pw.select_ncn(pnl)

        #---sizer 4 ---
        self.bSizer4 = pw.labeled_text_field(pnl, label="Location name:")

        #---sizer 5 ---
        self.bSizer5 = pw.labeled_text_field(pnl, label="Instrument name (optional):")

        #---sizer 6---
        self.bSizer6 = pw.labeled_yes_or_no(pnl, "Units", "CGS units (default)", "SI units")

        #---sizer 7---
        self.bSizer7 = pw.labeled_yes_or_no(pnl, "Format", "New (default)", "Old")


        #---buttons ---
        hboxok = pw.btn_panel(self, pnl)

        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.LEFT, border=5)
        hbox1.Add(self.bSizer5, flag=wx.ALIGN_LEFT)
        hbox2.Add(self.bSizer6, flag=wx.ALIGN_LEFT|wx.LEFT, border=5)
        hbox2.Add(self.bSizer7, flag=wx.ALIGN_LEFT)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0a, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(hbox1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(hbox2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)
        vbox.AddSpacer(20)
        #
        hbox_all = wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.Add(vbox)

        self.panel.SetSizer(hbox_all)
        self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()

    def on_add_dir_button(self,event):
        text = "choose directory of files to convert to MagIC"
        pw.on_add_dir_button(self.bSizer0, text)

    def on_okButton(self, event):
        os.chdir(self.WD)
        WD = self.WD
        ID = self.bSizer0.return_value()
        files = os.listdir(ID)
        files = [str(f) for f in files if str(f).endswith('.agm') or str(f).endswith('.irm')]
        usr = self.bSizer1.return_value()
        #if usr:
        #    usr = "-usr " + usr
        spc = self.bSizer2.return_value()
        ncn = self.bSizer3.return_value()
        loc_name = self.bSizer4.return_value()
        if loc_name:
            loc = "-loc " + loc_name
        else:
            loc=""
        ins = self.bSizer5.return_value()
        #if ins:
        #    ins = "-ins " + ins
        units = self.bSizer6.return_value()
        if units:
            units = 'cgs'
        else:
            units = 'SI'
        fmt = self.bSizer7.return_value()
        if fmt:
            fmt = "new"
        else:
            fmt = "old"

        # loop through all .agm and .irm files
        warn = False
        outfiles = []
        for f in files:
            if f.endswith('.irm'):
                bak = "-bak"
                bak_curve = True
            else:
                bak = ""
                bak_curve = False
            infile = os.path.join(ID, f)
            outfile = f + ".magic"
            outfiles.append(outfile)
            stem = infile.split('.')[0]
            SPEC_OUTFILE =  stem + "_specimens.txt"
            SAMP_OUTFILE =  stem + "_samples.txt"
            SITE_OUTFILE =  stem + "_sites.txt"
            LOC_OUTFILE =  stem + "_locations.txt"
            options_dict={}
            options_dict['meas_outfile'] = outfile
            options_dict['agm_file'] = infile
            options_dict['spec_outfile'] = SPEC_OUTFILE
            options_dict['samp_outfile'] = SAMP_OUTFILE
            options_dict['site_outfile'] = SITE_OUTFILE
            options_dict['fmt'] = fmt
            COMMAND = "agm_magic.py -WD {} -ID {} -f {} -F {} -Fsp {} {} -spc {} -ncn {} {} {} -u {} {}".format(WD, ID, f, outfile, SPEC_OUTFILE, usr, spc, ncn, loc, ins, units, bak)
            samp_infile = None
            print("COMMAND: ",COMMAND)
            print('options_dict', options_dict)
            program_ran, error_msg = convert.agm(**options_dict)
            if program_ran:
                pass
                #pw.close_window(self,COMMAND,outfile)
            else:
                warn = True
                pw.simple_warning("Something went wrong.\n{}".format(error_msg))
        if not warn:
            ellipses = False
            if len(outfiles) >= 8:
                outfiles = outfiles[:8]
                ellipses = True
            pw.close_window(self,COMMAND,outfiles,ellipses)
            pw.simple_warning('You have created MagIC files.  Make sure to go to Pmag GUI step 1 to combine and rename them before proceeding to analysis or upload!')

    def on_cancelButton(self,event):
        self.Destroy()
        self.Parent.Raise()

    def on_helpButton(self, event):
        pw.on_helpButton(text=agm_magic.do_help())


class ExportResults(wx.Frame):

    title = "Extract results"

    def __init__(self, parent, WD):
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title)
        self.panel = wx.ScrolledWindow(self)
        self.WD = WD
        self.InitUI()

    def InitUI(self):
        pnl = self.panel
        TEXT = "Generate tab delimited text or LaTeX files with result data"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0 ----
        self.bSizer0 = pw.choose_file(pnl, 'add result file', method=self.on_add_file_button)
        res_file = os.path.join(self.WD, 'pmag_results.txt')
        self.check_and_add_file(res_file, self.bSizer0.file_path)

        #---sizer 1 ----
        self.bSizer1 = pw.choose_file(pnl, 'add criteria file', method=self.on_add_crit_button,
                                      remove_button="Don't use criteria file")
        crit_file = os.path.join(self.WD, 'pmag_criteria.txt')
        self.check_and_add_file(crit_file, self.bSizer1.file_path)

        #---sizer 2 ---
        self.bSizer2 = pw.choose_file(pnl, 'add specimen file', method=self.on_add_spec_button,
                                      remove_button="Don't use specimen file")
        spec_file = os.path.join(self.WD, 'pmag_specimens.txt')
        self.check_and_add_file(spec_file, self.bSizer2.file_path)

        #---sizer 3 ---
        self.bSizer3 = pw.choose_file(pnl, 'add age file', method=self.on_add_age_button,
                                      remove_button="Don't use age file")
        age_file = os.path.join(self.WD, 'er_ages.txt')
        self.check_and_add_file(age_file, self.bSizer3.file_path)

        #---sizer 4 ---
        self.bSizer4 = pw.check_box(pnl, "output LaTeX-formatted files")

        #---sizer 5 ---
        self.bSizer5 = pw.check_box(pnl, "grade specimens (only works with PmagPy generated specimen files")

        #---buttons ---
        hboxok = pw.btn_panel(self, pnl)

        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.LEFT, border=5)
        hbox.Add(self.bSizer5, flag=wx.ALIGN_LEFT)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(hbox, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)
        vbox.AddSpacer(20)

        hbox_all = wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.Add(vbox)

        self.panel.SetSizer(hbox_all)
        self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()

    def check_and_add_file(self, infile, add_here):
        if os.path.isfile(infile):
            add_here.SetValue(infile)

    def on_add_file_button(self,event):
        text = "choose file to convert to MagIC"
        pw.on_add_file_button(self.bSizer0, text)

    def on_add_crit_button(self, event):
        text = "choose criteria file"
        pw.on_add_file_button(self.bSizer1, text)

    def on_add_spec_button(self, event):
        text = "choose specimen file"
        pw.on_add_file_button(self.bSizer2, text)

    def on_add_age_button(self, event):
        text = "choose age file"
        pw.on_add_file_button(self.bSizer3, text)

    def on_okButton(self, event):
        os.chdir(self.WD)
        COMMAND = ""
        print(COMMAND)
        res_file = self.bSizer0.return_value()
        if not os.path.isfile(res_file):
            pw.simple_warning("You must have a result file to run this step")
            return
        res_file = os.path.split(res_file)[1]
        crit_file = self.bSizer1.return_value()
        if crit_file:
            crit_file = os.path.split(crit_file)[1]
        spec_file = self.bSizer2.return_value()
        if spec_file:
            spec_file = os.path.split(spec_file)[1]
        age_file = self.bSizer3.return_value()
        if age_file:
            age_file = os.path.split(age_file)[1]
        latex = self.bSizer4.return_value()
        grade = self.bSizer5.return_value()
        WD = self.WD
        COMMAND = "ipmag.pmag_results_extract(res_file='{}', crit_file='{}', spec_file='{}', age_file='{}', latex='{}' grade='{}', WD='{}')".format(res_file, crit_file, spec_file, age_file, latex, grade, WD)
        print(COMMAND)
        res, outfiles = ipmag.pmag_results_extract(res_file, crit_file, spec_file, age_file,
                                                   latex, grade, WD)
        outfiles = [os.path.split(f)[1] for f in outfiles]
        ipmag.pmag_results_extract(res_file, crit_file, spec_file, age_file, latex, grade, WD)
        pw.close_window(self, COMMAND, ", ".join(outfiles))
        #pw.run_command_and_close_window(self, COMMAND, "er_samples.txt")

    def on_cancelButton(self,event):
        self.Destroy()
        self.Parent.Raise()

    def on_helpButton(self, event):
        pw.on_helpButton(text=ipmag.pmag_results_extract.__doc__)




### Analysis and plots

class CustomizeCriteria(wx.Frame):

    title = "Customize Criteria"

    def __init__(self, parent, WD):
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title)
        self.panel = wx.ScrolledWindow(self)
        self.WD = WD
        self.InitUI()

    def InitUI(self):
        pnl = self.panel
        TEXT = "Update your criteria"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0 ----
        choices = ['Use default criteria', 'Update default criteria', 'Use no criteria', 'Update existing criteria']
        self.bSizer0 = pw.radio_buttons(pnl, choices)

        #---buttons ---
        hboxok = pw.btn_panel(self, pnl)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(hbox, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #try:
        #    vbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #except AttributeError:
        #    pass
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)
        vbox.AddSpacer(20)

        hbox_all = wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.Add(vbox)

        self.panel.SetSizer(hbox_all)
        self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()

    def on_add_file_button(self,event):
        text = "choose file to convert to MagIC"
        pw.on_add_file_button(self.bSizer0, text)

    def on_okButton(self, event):
        os.chdir(self.WD)
        choice = self.bSizer0.return_value()
        critout = os.path.join(self.WD, 'pmag_criteria.txt')
        if choice == 'Use default criteria' or choice == 'Use no criteria':
            if choice == 'Use default criteria':
                crit_data=pmag.default_criteria(0)
                crit_data,critkeys=pmag.fillkeys(crit_data)
                pmag.magic_write(critout,crit_data,'pmag_criteria')
                # pop up instead of print
                MSG="Default criteria saved in {}/pmag_criteria.txt".format(self.WD)
            elif choice == 'Use no criteria':
                crit_data = pmag.default_criteria(1)
                pmag.magic_write(critout,crit_data,'pmag_criteria')
                MSG="Extremely loose criteria saved in {}/pmag_criteria.txt".format(self.WD)

            dia = wx.MessageDialog(None,caption="Message:", message=MSG ,style=wx.OK|wx.ICON_INFORMATION)
            dia.ShowModal()
            dia.Destroy()
            self.Parent.Raise()
            self.Destroy()
            return
        if choice == "Update existing criteria":
            try:
                crit_data, file_type = pmag.magic_read(os.path.join(self.WD, "pmag_criteria.txt"))
                if file_type != "pmag_criteria":
                    raise Exception
            except Exception as ex:
                print("exception", ex)
                MSG = "No pmag_criteria.txt file found in working directory ({})".format(self.WD)
                dia = wx.MessageDialog(None,caption="Message:", message=MSG ,style=wx.OK|wx.ICON_INFORMATION)
                return 0
            default_criteria = pmag.default_criteria(1)[0]
            crit_data = crit_data[0]
            crit_data = dict(default_criteria, **crit_data)
        elif choice == "Update default criteria":
            crit_data = pmag.default_criteria(0)[0]

        frame = wx.Frame(self)
        window = wx.ScrolledWindow(frame)
        self.boxes = pw.large_checkbox_window(window, crit_data)
        bSizer = wx.BoxSizer(wx.VERTICAL)
        bSizer.Add(self.boxes)

        hboxok = wx.BoxSizer(wx.HORIZONTAL)
        edit_okButton = wx.Button(window, wx.ID_ANY, "&OK")
        edit_cancelButton = wx.Button(window, wx.ID_ANY, '&Cancel')
        hboxok.Add(edit_okButton, 0, wx.ALL, 5)
        hboxok.Add(edit_cancelButton, 0, wx.ALL, 5 )
        window.Bind(wx.EVT_BUTTON, self.on_cancelButton, edit_cancelButton)
        window.Bind(wx.EVT_BUTTON, self.on_edit_okButton, edit_okButton)

        bSizer.Add(hboxok)
        window.SetSizer(bSizer)
        bSizer.Fit(frame)
        window.SetScrollbars(20, 20, 50, 50)
        frame.Centre()
        frame.Show()


    def on_edit_okButton(self, event):
        print(self.boxes.return_value())
        crit_data = self.boxes.return_value()
        critout = os.path.join(self.WD, '/pmag_criteria.txt')
        pmag.magic_write(critout, crit_data, 'pmag_criteria')
        MSG = "pmag_criteria.txt file has been updated"
        dia = wx.MessageDialog(None,caption="Message:", message=MSG ,style=wx.OK|wx.ICON_INFORMATION)
        dia.ShowModal()
        dia.Destroy()
        self.on_cancelButton(None)

    def on_cancelButton(self, event):
        for child in self.GetChildren():
            child.Destroy()
            #child_window = child.GetWindow()
            #print child_window
        self.Destroy()
        self.Parent.Raise()

    def on_helpButton(self, event):
        print("do help button")
        # have a little info thing pop up





def add_thellier_gui_criteria(acceptance_criteria):
    '''criteria used only in thellier gui
    these criteria are not written to pmag_criteria.txt
    '''
    category="thellier_gui"
    for crit in ['sample_int_n_outlier_check','site_int_n_outlier_check']:
        acceptance_criteria[crit]={}
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        acceptance_criteria[crit]['threshold_type']="low"
        acceptance_criteria[crit]['decimal_points']=0

    for crit in ['sample_int_interval_uT','sample_int_interval_perc',\
    'site_int_interval_uT','site_int_interval_perc',\
    'sample_int_BS_68_uT','sample_int_BS_95_uT','sample_int_BS_68_perc','sample_int_BS_95_perc','specimen_int_max_slope_diff']:
        acceptance_criteria[crit]={}
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=-999
        acceptance_criteria[crit]['threshold_type']="high"
        if crit in ['specimen_int_max_slope_diff']:
            acceptance_criteria[crit]['decimal_points']=-999
        else:
            acceptance_criteria[crit]['decimal_points']=1
        acceptance_criteria[crit]['comments']="thellier_gui_only"

    for crit in ['average_by_sample_or_site','interpreter_method']:
        acceptance_criteria[crit]={}
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        if crit in ['average_by_sample_or_site']:
            acceptance_criteria[crit]['value']='sample'
        if crit in ['interpreter_method']:
            acceptance_criteria[crit]['value']='stdev_opt'
        acceptance_criteria[crit]['threshold_type']="flag"
        acceptance_criteria[crit]['decimal_points']=-999

    for crit in ['include_nrm']:
        acceptance_criteria[crit]={}
        acceptance_criteria[crit]['category']=category
        acceptance_criteria[crit]['criterion_name']=crit
        acceptance_criteria[crit]['value']=True
        acceptance_criteria[crit]['threshold_type']="bool"
        acceptance_criteria[crit]['decimal_points']=-999


    # define internal Thellier-GUI definitions:
    #self.average_by_sample_or_site='sample'
    #self.stdev_opt=True
    #self.bs=False
    #self.bs_par=False







class ZeqMagic(wx.Frame):

    title = "Zeq Magic"

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
        #self.bSizer1 = pw.specimen_n(pnl)

        #---sizer 2 ---
        #self.bSizer2 = pw.select_ncn(pnl)

        #---sizer 3 ---
        #self.bSizer3 = pw.labeled_text_field(pnl, label="Location name:")

        #---sizer 4 ---
        #self.bSizer4 = pw.labeled_text_field(pnl, label="Instrument name (optional):")


        #---sizer 4 ----
        #try:
        #    open(self.WD + "/er_samples.txt", "r")
        #except Exception as ex:
        #    er_samples_file_present = False
        #if er_samples_file_present:
        #    self.bSizer4 = pw.labeled_yes_or_no(pnl, TEXT, label1, label2)

        #---buttons ---
        hboxok = pw.btn_panel(self, pnl)

        vbox = wx.BoxSizer(wx.VERTICAL)
        #hbox = wx.BoxSizer(wx.HORIZONTAL)
        #hbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.LEFT, border=5)
        #hbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(hbox, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #try:
        #    vbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #except AttributeError:
        #    pass
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)
        vbox.AddSpacer(20)

        hbox_all = wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.Add(vbox)

        self.panel.SetSizer(hbox_all)
        self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()

    def on_add_file_button(self,event):
        text = "choose file to convert to MagIC"
        pw.on_add_file_button(self.bSizer0, text)

    def on_okButton(self, event):
        os.chdir(self.WD)
        COMMAND = "zeq_magic.py -WD {}".format(self.WD)
        print(COMMAND)
        #pw.run_command_and_close_window(self, COMMAND, "er_samples.txt")

    def on_cancelButton(self,event):
        self.Destroy()
        self.Parent.Raise()

    def on_helpButton(self, event):
        pw.on_helpButton(text='')




class Core_depthplot(wx.Frame):

    title = "Remanence data vs. depth/height/age"

    def __init__(self, parent, WD):
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title, name='core_depthplot')
        self.panel = wx.ScrolledWindow(self)
        self.WD = WD
        self.InitUI()

    def InitUI(self):
        pnl = self.panel
        TEXT = "This program allows you to plot various measurement data versus sample depth.\nYou must provide either a magic_measurements file or a pmag_specimens file (or, you can use both)."
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0 ----
        self.bSizer0 = pw.choose_file(pnl, btn_text='add measurements file',
                                      method=self.on_add_measurements_button,
                                      remove_button="Don't use measurements file")

        meas_file = os.path.join(self.WD, 'magic_measurements.txt')
        self.check_and_add_file(meas_file, self.bSizer0.file_path)


        #---sizer 4 ---
        color_choices = ['blue', 'green','red','cyan','magenta', 'yellow', 'black','white']
        self.bSizer4 = pw.radio_buttons(pnl, color_choices, "choose color for plot points")

        #---sizer 5 ---
        shape_choices = ['circle', 'triangle_down','triangle_up','square', 'star','hexagon','+','x','diamond']
        shape_symbols =['o', 'v', '^', 's', '*', 'h', '+', 'x', 'd']
        self.shape_choices_dict = dict(list(zip(shape_choices, shape_symbols)))
        self.bSizer5 = pw.radio_buttons(pnl, shape_choices, "choose shape for plot points")

        #---sizer 5a---
        #self.bSizer5a = pw.labeled_text_field(pnl, "point size (default is 5)")
        self.bSizer5a = pw.labeled_spin_ctrl(pnl, "point size (default is 5): ")
        self.bSizer5b = pw.check_box(pnl, "Show lines connecting points")
        self.bSizer5b.cb.SetValue(True)

        self.Bind(wx.EVT_TEXT, self.change_file_path, self.bSizer0.file_path)


        #---sizer 0a---
        self.bSizer0a = pw.choose_file(pnl, btn_text='add pmag_specimens file', method = self.on_add_pmag_specimens_button, remove_button="Don't use pmag specimens file")
        pmag_spec_file = os.path.join(self.WD, 'pmag_specimens.txt')
        self.check_and_add_file(pmag_spec_file, self.bSizer0a.file_path)

        #--- plotting stuff for pmag_specimens
        self.bSizer0a1 = pw.radio_buttons(pnl, color_choices, "choose color for plot points")

        # set default color to red
        self.bSizer0a1.radio_buttons[2].SetValue(True)

        self.bSizer0a2 = pw.radio_buttons(pnl, shape_choices, "choose shape for plot points")

        # set default symbol:
        self.bSizer0a2.radio_buttons[2].SetValue(True)

        self.bSizer0a3 = pw.labeled_spin_ctrl(pnl, "point size (default is 5): ")

        self.Bind(wx.EVT_TEXT, self.change_results_path, self.bSizer0a.file_path)


        #---sizer 1 ---
        self.bSizer1a = pw.labeled_yes_or_no(pnl, "Choose file to provide sample data", "er_samples", "er_ages")
        self.Bind(wx.EVT_RADIOBUTTON, self.on_sample_or_age, self.bSizer1a.rb1)
        self.Bind(wx.EVT_RADIOBUTTON, self.on_sample_or_age, self.bSizer1a.rb2)

        self.bSizer1 = pw.choose_file(pnl, btn_text='add er_samples file', method = self.on_add_samples_button)
        sampfile = os.path.join(self.WD, 'er_samples.txt')
        self.check_and_add_file(sampfile, self.bSizer1.file_path)

        #---sizer 2 ----
        self.bSizer2 = pw.choose_file(pnl, btn_text='add IODP core summary csv file (optional)', method = self.on_add_csv_button)

        #---sizer 3 ---
        plot_choices = ['Plot declination', 'Plot inclination', 'Plot magnetization', 'Plot magnetization on log scale']
        self.bSizer3 = pw.check_boxes(pnl, (5, 1, 0, 0), plot_choices, "Choose what to plot:")
        self.bSizer3.boxes[0].SetValue(True)
        self.bSizer3.boxes[1].SetValue(True)
        self.bSizer3.boxes[2].SetValue(True)
        self.bSizer3.boxes[3].SetValue(True)


        #---sizer 13---
        protocol_choices = ['AF', 'T', 'ARM', 'IRM']#, 'X'] not supporting susceptibility at the moment
        self.bSizer13 = pw.radio_buttons(pnl, protocol_choices, "Lab Protocol:  ", orientation=wx.HORIZONTAL)

        self.bSizer14 = pw.labeled_text_field(pnl, "Step:  ")

        #self.bSizer15 = pw.check_box(pnl, "Do not plot blanket treatment data")

        self.bSizer16 = pw.radio_buttons(pnl, ['svg', 'eps', 'pdf', 'png'], "Save plot in this format:")

        #---sizer 8 ---
        self.bSizer8 = pw.labeled_yes_or_no(pnl, "Depth scale", "Meters below sea floor (mbsf)", "Meters composite depth (mcd)")


        #---sizer 6 ---
        self.bSizer6 = pw.labeled_text_field(pnl, label="minimum depth to plot (in meters)")

        #---sizer  7---
        self.bSizer7 = pw.labeled_text_field(pnl, label="maximum depth to plot (in meters)")

        #---sizer 9 ---
        self.bSizer9 = pw.check_box(pnl, "Plot GPTS?")
        self.Bind(wx.EVT_CHECKBOX, self.on_checkbox, self.bSizer9.cb)

        # if plotting GPTS, these sizers will be shown:
        #self.bSizer10 = pw.labeled_yes_or_no(pnl, "Time scale", "gts04", "ck95")
        choices = ["gts12", "gts04", "ck95"]
        self.bSizer10 = pw.radio_buttons(pnl, choices, label="Time scale")

        self.bSizer11 = pw.labeled_text_field(pnl, label="Minimum age (in Ma)")

        self.bSizer12 = pw.labeled_text_field(pnl, label="Maximum age (in Ma)")


        #---buttons ---
        hboxok = pw.btn_panel(self, pnl)

        #---make all the smaller container boxes---
        vbox = wx.BoxSizer(wx.VERTICAL)
        box1 = wx.StaticBox(pnl)
        box2 = wx.StaticBox(pnl)
        box3 = wx.StaticBox(pnl)
        box4 = wx.StaticBox(pnl)
        box5 = wx.StaticBox(pnl)
        self.vbox1 = wx.StaticBoxSizer(box1, wx.VERTICAL)
        vbox2 = wx.StaticBoxSizer(box2, wx.VERTICAL)
        vbox3 = wx.StaticBoxSizer(box3, wx.VERTICAL)
        vbox4 = wx.StaticBoxSizer(box4, wx.VERTICAL)
        self.vbox5 = wx.StaticBoxSizer(box5, wx.VERTICAL)
        mini_vbox = wx.BoxSizer(wx.VERTICAL)
        hbox0 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        hbox4 = wx.BoxSizer(wx.HORIZONTAL)
        hbox5 = wx.BoxSizer(wx.HORIZONTAL)

        #---Plot type and format ---
        hbox0.AddMany([self.bSizer3, self.bSizer16])

        #---Plot display options---
        mini_vbox.AddMany([self.bSizer5a, self.bSizer5b])
        hbox1.Add(self.bSizer4)
        hbox1.Add(self.bSizer5, flag=wx.ALIGN_LEFT)
        hbox1.Add(mini_vbox, flag=wx.ALIGN_LEFT)
        self.vbox1.Add(wx.StaticText(pnl, label="Plot display options for measurements data"))
        self.vbox1.Add(hbox1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)

        # more plot display options

        hbox5.AddMany([self.bSizer0a1, self.bSizer0a2, self.bSizer0a3])
        self.vbox5.Add(wx.StaticText(pnl, label="Plot display options for specimens data"))
        self.vbox5.Add(hbox5)


        #---depths to plot ---
        hbox2.Add(self.bSizer6, flag=wx.ALIGN_LEFT)#|wx.LEFT, border=5)
        hbox2.Add(self.bSizer7, flag=wx.ALIGN_LEFT)
        vbox2.Add(wx.StaticText(pnl, label="Specify depths to plot (optional)"))
        vbox2.Add(hbox2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)

        #---time scale ----
        hbox3.Add(self.bSizer9, flag=wx.ALIGN_LEFT)
        hbox3.Add(self.bSizer10, flag=wx.ALIGN_LEFT)#|wx.LEFT, border=5)
        hbox3.Add(self.bSizer11, flag=wx.ALIGN_LEFT)
        hbox3.Add(self.bSizer12, flag=wx.ALIGN_LEFT)
        vbox3.Add(wx.StaticText(pnl, label="Specify time scale to plot (optional)"))
        vbox3.Add(hbox3)

        #---experiment type and step
        hbox4.Add(self.bSizer13, flag=wx.ALIGN_LEFT)
        hbox4.Add(self.bSizer14, flag=wx.ALIGN_LEFT)
        vbox4.Add(wx.StaticText(pnl, label="Experiment type"))
        vbox4.Add(hbox4)
        #vbox4.Add(self.bSizer15)

        #---add all widgets to main container---
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.vbox1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)

        vbox.Add(self.bSizer0a, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.vbox5, flag=wx.ALIGN_LEFT|wx.TOP, border=10)

        vbox.Add(self.bSizer1a, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(hbox0)

        vbox.Add(vbox4, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer8, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(vbox2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(vbox3, flag=wx.ALIGN_LEFT|wx.TOP, border=10)

        #--- add buttons ---
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)
        vbox.AddSpacer(20)

        self.hbox_all = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox_all.AddSpacer(20)
        self.hbox_all.Add(vbox)

        self.panel.SetSizer(self.hbox_all)
        self.panel.SetScrollbars(20, 20, 50, 50)


        # hide plotting stuff
        # no longer hiding this initially -- it causes a sizing nightmare
        #if not self.bSizer0.file_path.GetValue():
            #self.vbox1.ShowItems(False)

        #if not self.bSizer0a.file_path.GetValue():
            #self.vbox5.ShowItems(False)


        self.hbox_all.Fit(self)

        # hide gpts stuff
        self.bSizer10.ShowItems(False)
        self.bSizer11.ShowItems(False)
        self.bSizer12.ShowItems(False)
        self.Show()
        self.Centre()


    def change_results_path(self, event):
        txt_ctrl = event.GetEventObject()
        if txt_ctrl.GetValue():
            self.vbox5.ShowItems(True)
            self.panel.Layout() # resizes scrolled window
            #self.hbox_all.Fit(self) # resizes entire frame
        else:
            self.vbox5.ShowItems(False)
            self.panel.Layout()

    def change_file_path(self, event):
        txt_ctrl = event.GetEventObject()
        if txt_ctrl.GetValue():
            self.vbox1.ShowItems(True)
            self.panel.Layout() # resizes scrolled window
            #self.hbox_all.Fit(self) # resizes entire frame

        else:
            self.vbox1.ShowItems(False)
            self.panel.Layout()


    def on_add_measurements_button(self, event):
        text = "choose file to convert to MagIC"
        pw.on_add_file_button(self.bSizer0, text)

    def on_add_pmag_specimens_button(self, event):
        text = "choose file to convert to MagIC"
        pw.on_add_file_button(self.bSizer0a, text)

    def on_sample_or_age(self, event):
        if event.GetId() == self.bSizer1a.rb1.GetId():
            self.bSizer1.add_file_button.SetLabel('add er_samples_file')
            self.check_and_add_file(os.path.join(self.WD, 'er_samples.txt'), self.bSizer1.file_path)
        else:
            self.bSizer1.add_file_button.SetLabel('add er_ages_file')
            self.check_and_add_file(os.path.join(self.WD, 'er_ages.txt'), self.bSizer1.file_path)

    def check_and_add_file(self, infile, add_here):
        if os.path.isfile(infile):
            add_here.SetValue(infile)

    def on_add_samples_button(self, event):
        text = "provide er_samples/er_ages file"
        pw.on_add_file_button(self.bSizer1, text)

    def on_add_csv_button(self, event):
        text = "provide csv file (optional)"
        pw.on_add_file_button(self.bSizer2, text)

    def on_checkbox(self, event):
        if event.Checked():
            self.bSizer10.ShowItems(True)
            self.bSizer11.ShowItems(True)
            self.bSizer12.ShowItems(True)
        else:
            self.bSizer10.ShowItems(False)
            self.bSizer11.ShowItems(False)
            self.bSizer12.ShowItems(False)
        self.panel.Layout()
        #self.hbox_all.Fit(self)

    def on_okButton(self, event):
        """
        meas_file # -f magic_measurements_file
        samp_file #-fsa er_samples_file
        age_file # -fa er_ages_file
        depth_scale # -ds scale
        dmin, dmax # -d 1 50  # depth to plot
        timescale, amin, amax (also sets pTS, pcol, width) =  # -ts scale min max
        sym, size # -sym symbol size
        method, step (also may set suc_key) # -LP protocol step
        pltDec (also sets pcol, pel, width)# -D (don't plot dec)
        pltInc (also sets pcol, pel, width)# -I (don't plot inc)
        pltMag (also sets pcol, pel, width)# -M (don't plot intensity)
        logit # -log ( plot log scale)
        fmt # -fmt format
        """
        def check_input_dir_path(input_dir_path, new_dir_path):
            if input_dir_path and input_dir_path != new_dir_path:
                pw.simple_warning("Please make sure that all input files come from the same directory")
                return False
            if not input_dir_path and new_dir_path:
                return new_dir_path
            elif input_dir_path == new_dir_path:
                return input_dir_path

        wait = wx.BusyInfo('Making plots, please wait...')
        wx.SafeYield()

        os.chdir(self.WD)
        input_dir_path = None
        meas_file = self.bSizer0.return_value()
        if meas_file:
            input_dir_path, meas_file = os.path.split(meas_file)
        pmag_spec_file = self.bSizer0a.return_value()
        if pmag_spec_file:
            new_dir_path, pmag_spec_file = os.path.split(pmag_spec_file)
            input_dir_path = check_input_dir_path(input_dir_path, new_dir_path)
            if not input_dir_path:
                del wait
                return False
        sum_file = self.bSizer2.return_value()
        if sum_file:
            new_dir_path, sum_file = os.path.split(sum_file)
            input_dir_path = check_input_dir_path(input_dir_path, new_dir_path)
            if not input_dir_path:
                del wait
                return False

        spec_sym, spec_sym_shape, spec_sym_color, spec_sym_size = "", "", "", ""

        if pmag_spec_file:
            # get symbol/size for dots
            spec_sym_shape = self.shape_choices_dict[self.bSizer0a2.return_value()]
            spec_sym_color = self.bSizer0a1.return_value()[0]
            spec_sym_size = self.bSizer0a3.return_value()
            spec_sym = str(spec_sym_color) + str(spec_sym_shape)

        use_sampfile = self.bSizer1a.return_value()
        if use_sampfile:
            new_dir_path, samp_file = os.path.split(str(self.bSizer1.return_value()))
            age_file = ''
            input_dir_path = check_input_dir_path(input_dir_path, new_dir_path)
            if not input_dir_path:
                del wait
                return False
        else:
            samp_file = ''
            new_dir_path, age_file = os.path.split(self.bSizer1.return_value())
            input_dir_path = check_input_dir_path(input_dir_path, new_dir_path)
            if not input_dir_path:
                del wait
                return False

        depth_scale = self.bSizer8.return_value()
        if age_file:
            depth_scale='age'
        elif depth_scale:
            depth_scale = 'sample_core_depth' #'mbsf'
        else:
            depth_scale = 'sample_composite_depth' #'mcd'
        dmin = self.bSizer6.return_value()
        dmax = self.bSizer7.return_value()
        if self.bSizer9.return_value(): # if plot GPTS is checked
            pltTime = 1
            timescale = self.bSizer10.return_value()
            amin = self.bSizer11.return_value()
            amax = self.bSizer12.return_value()
            if not amin or not amax:
                del wait
                pw.simple_warning("If plotting timescale, you must provide both a lower and an upper bound.\nIf you don't want to plot timescale, uncheck the 'Plot GPTS' checkbox")
                return False
        else: # if plot GPTS is not checked
            pltTime, timescale, amin, amax = 0, '', -1, -1
        sym_shape = self.shape_choices_dict[self.bSizer5.return_value()]
        sym_color = self.bSizer4.return_value()[0]
        sym = sym_color + sym_shape
        size = self.bSizer5a.return_value()
        pltLine = self.bSizer5b.return_value()
        if pltLine:
            pltLine = 1
        else:
            pltLine = 0
        method = str(self.bSizer13.return_value())
        step = self.bSizer14.return_value()
        if not step:
            step = 0
            method = 'LT-NO'
        #if not step:
        #    #-LP [AF,T,ARM,IRM, X] step [in mT,C,mT,mT, mass/vol] to plot
        #    units_dict = {'AF': 'millitesla', 'T': 'degrees C', 'ARM': 'millitesla', 'IRM': 'millitesla', 'X': 'mass/vol'}
            #unit = units_dict[method]
            #pw.simple_warning("You must provide the experiment step in {}".format(unit))
            #return False
        pltDec, pltInc, pltMag, logit = 0, 0, 0, 0
        for val in self.bSizer3.return_value():
            if 'declination' in val:
                pltDec = 1
            if 'inclination' in val:
                pltInc = 1
            if 'magnetization' in val:
                pltMag = 1
            if 'log' in val:
                logit = 1

        #pltSus = self.bSizer15.return_value()
        #if pltSus:
        #    pltSus = 0
        #else:
        #    pltSus = 1

        fmt = self.bSizer16.return_value()
        #print "meas_file", meas_file, "pmag_spec_file", pmag_spec_file, "spec_sym_shape", spec_sym_shape, "spec_sym_color", spec_sym_color, "spec_sym_size", spec_sym_size, "samp_file", samp_file, "age_file", age_file, "depth_scale", depth_scale, "dmin", dmin, "dmax", dmax, "timescale", timescale, "amin", amin, "amax", amax, "sym", sym, "size", size, "method", method, "step", step, "pltDec", pltDec, "pltInc", pltInc, "pltMag", pltMag, "pltTime", pltTime, "logit", logit, "fmt", fmt

        # for use as module:
        #print "pltLine:", pltLine
        #print "pltSus:", pltSus

        fig, figname = ipmag.core_depthplot(input_dir_path or self.WD, meas_file, pmag_spec_file, samp_file, age_file, sum_file, '', depth_scale, dmin, dmax, sym, size, spec_sym, spec_sym_size, method, step, fmt, pltDec, pltInc, pltMag, pltLine, 1, logit, pltTime, timescale, amin, amax)
        if fig:
            self.Destroy()
            dpi = fig.get_dpi()
            pixel_width = dpi * fig.get_figwidth()
            pixel_height = dpi * fig.get_figheight()
            plot_frame = PlotFrame((pixel_width, pixel_height + 50), fig, figname)
            del wait
            return plot_frame
        else:
            del wait
            pw.simple_warning("No data points met your criteria - try again\nError message: {}".format(figname))
            return False


        # for use as command_line:
        if meas_file:
            meas_file = os.path.split(meas_file)[1]
        meas_file = pmag.add_flag(meas_file, '-f')
        if pmag_spec_file:
            pmag_spec_file = os.path.split(pmag_spec_file)[1]
        pmag_spec_file = pmag.add_flag(pmag_spec_file, '-fsp')
        pmag_spec_file = pmag_spec_file + ' ' + spec_sym_color + spec_sym_shape + ' ' + str(spec_sym_size)
        sym = '-sym ' + sym + ' ' + str(size)
        if samp_file:
            samp_file = os.path.split(samp_file)[1]
        samp_file = pmag.add_flag(samp_file, '-fsa')
        if age_file:
            age_file = os.path.split(age_file)[1]
        age_file = pmag.add_flag(age_file, '-fa')
        depth_scale = pmag.add_flag(depth_scale, '-ds')
        depth_range = ''
        if dmin and dmax:
            depth_range = '-d ' + str(dmin) + ' ' + str(dmax)
        if pltTime and amin and amax:
            timescale = '-ts ' + timescale + ' ' + str(amin) + ' ' + str(amax)
        else:
            timescale = ''
        method = pmag.add_flag(method, '-LP') + ' ' + str(step)
        #if not pltSus:
        #    pltSus = "-L"
        #else:
        #    pltSus = ''
        if not pltDec:
            pltDec = "-D"
        else:
            pltDec = ''
        if not pltInc:
            pltInc = "-I"
        else:
            pltInc = ''
        if not pltMag:
            pltMag = "-M"
        else:
            pltMag = ''
        if pltLine:
            pltLine = ""
        else:
            pltLine = '-L' # suppress line
        if logit:
            logit = "-log"
        else:
            logit = ''
        fmt = pmag.add_flag(fmt, '-fmt')

        COMMAND = "core_depthplot.py {meas_file} {pmag_spec_file} {sym} {samp_file} {age_file} {depth_scale} {depth_range} {timescale} {method} {pltDec} {pltInc} {pltMag} {logit} {fmt} {pltLine} -WD {WD}".format(meas_file=meas_file, pmag_spec_file=pmag_spec_file, sym=sym, samp_file=samp_file, age_file=age_file, depth_scale=depth_scale, depth_range=depth_range, timescale=timescale, method=method, pltDec=pltDec, pltInc=pltInc, pltMag=pltMag, logit=logit, fmt=fmt, pltLine=pltLine, WD=self.WD)
        print(COMMAND)
        #os.system(COMMAND)


        """
        haven't done these options yet
        wt_file (also sets norm)# -n specimen_filename
        spc_file, spc_sym, spc_size # -fsp spec_file symbol_shape symbol_size
        res_file, res_sym, res_size # -fres pmag_results_file symbol_shape symbol_size
        wig_file (also sets pcol, width) # -fwig wiggle_file(???)
        sum_file # -fsum IODP_core_summary_csv_file

        (sets plots & verbose) # -sav
        """

        #pw.run_command_and_close_window(self, COMMAND, "er_samples.txt")

    def on_cancelButton(self,event):
        self.Destroy()
        self.Parent.Raise()

    def on_helpButton(self, event):
        pw.on_helpButton(text=ipmag.core_depthplot.__doc__)



class Ani_depthplot(wx.Frame):

    title = "Plot anisotropoy vs. depth/height/age"

    def __init__(self, parent, WD):
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title, name='aniso_depthplot')
        self.panel = wx.ScrolledWindow(self)
        self.WD = WD
        self.InitUI()

    def InitUI(self):
        pnl = self.panel
        TEXT = "Anisotropy data can be plotted versus depth.\nThe program ANI_depthplot.py uses MagIC formatted data tables of the rmag_anisotropy.txt and er_samples.txt types.\nrmag_anisotropy.txt stores the tensor elements and measurement meta-data while er_samples.txt stores the depths, location and other information.\nBulk susceptibility measurements can also be plotted if they are available in a magic_measurements.txt formatted file."
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0 ----
        self.bSizer0 = pw.choose_file(pnl, btn_text='add rmag_anisotropy file', method = self.on_add_rmag_button, remove_button='remove rmag_anisotropy file')
        self.check_and_add_file(os.path.join(self.WD, 'rmag_anisotropy.txt'), self.bSizer0.file_path)

        #---sizer 1 ----
        self.bSizer1 = pw.choose_file(pnl, btn_text='add magic_measurements file', method = self.on_add_measurements_button, remove_button='remove magic_measurements file')
        self.check_and_add_file(os.path.join(self.WD, 'magic_measurements.txt'), self.bSizer1.file_path)

        #---sizer 2 ---
        self.bSizer2a = pw.labeled_yes_or_no(pnl, "Choose file to provide sample data", "er_samples", "er_ages")
        self.Bind(wx.EVT_RADIOBUTTON, self.on_sample_or_age, self.bSizer2a.rb1)
        self.Bind(wx.EVT_RADIOBUTTON, self.on_sample_or_age, self.bSizer2a.rb2)

        self.bSizer2 = pw.choose_file(pnl, btn_text='add er_samples file', method = self.on_add_samples_button)
        sampfile = os.path.join(self.WD, 'er_samples.txt')
        self.check_and_add_file(sampfile, self.bSizer2.file_path)

        #---sizer 2b---
        self.bSizer2b = pw.choose_file(pnl, btn_text="Add core summary file (optional)", method = self.on_add_summary_button)

        #---sizer 3---
        self.bSizer3 = pw.radio_buttons(pnl, ['svg', 'eps', 'pdf', 'png'], "Save plot in this format:")

        #---sizer 4 ---
        self.bSizer4 = pw.labeled_yes_or_no(pnl, "Depth scale", "Meters below sea floor (mbsf)", "Meters composite depth (mcd)")

        #---sizer 5 ---
        self.bSizer5 = pw.labeled_text_field(pnl, label="minimum depth to plot (in meters)")

        #---sizer  6---
        self.bSizer6 = pw.labeled_text_field(pnl, label="maximum depth to plot (in meters)")

        #---buttons ---
        hboxok = pw.btn_panel(self, pnl)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer2a, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer2b, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.AddMany([self.bSizer5, self.bSizer6])
        vbox.Add(hbox1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)

        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)
        vbox.AddSpacer(20)

        hbox_all = wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.Add(vbox)

        self.panel.SetSizer(hbox_all)
        self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()

    def on_add_rmag_button(self,event):
        text = "choose rmag_anisotropy file"
        pw.on_add_file_button(self.bSizer0, text)

    def on_add_measurements_button(self,event):
        text = "choose magic_measurements file"
        pw.on_add_file_button(self.bSizer1, text)

    def on_add_samples_button(self, event):
        text = "provide er_samples/er_ages file"
        pw.on_add_file_button(self.bSizer2, text)

    def on_sample_or_age(self, event):
        if event.GetId() == self.bSizer2a.rb1.GetId():
            self.bSizer2.add_file_button.SetLabel('add er_samples_file')
            self.check_and_add_file(os.path.join(self.WD, 'er_samples.txt'), self.bSizer2.file_path)
        else:
            self.bSizer2.add_file_button.SetLabel('add er_ages_file')
            self.check_and_add_file(os.path.join(self.WD, 'er_ages.txt'), self.bSizer2.file_path)

    def on_add_summary_button(self, event):
        pw.on_add_file_button(self.bSizer2b, text="provide csv format core summary file")


    def check_and_add_file(self, infile, add_here):
        if os.path.isfile(infile):
            add_here.SetValue(infile)

    def on_okButton(self, event):
        wait = wx.BusyInfo('Making plots, please wait...')
        wx.SafeYield()

        os.chdir(self.WD)
        ani_file = self.bSizer0.return_value()
        meas_file = self.bSizer1.return_value()
        use_sampfile = self.bSizer2a.return_value()
        samp_file, age_file = None, None
        if use_sampfile:
            samp_file = self.bSizer2.return_value()
        else:
            age_file = self.bSizer2.return_value()

        sum_file = self.bSizer2b.return_value()
        if sum_file:
            sum_file = os.path.split(sum_file)[1]

        fmt = self.bSizer3.return_value()
        depth_scale = self.bSizer4.return_value()
        print('age_file', age_file)
        if age_file:
            depth_scale='age'
        elif depth_scale:
            depth_scale = 'sample_core_depth' #'mbsf'
        else:
            depth_scale = 'sample_composite_depth' #'mcd'
        dmin = self.bSizer5.return_value() or -1
        dmax = self.bSizer6.return_value() or -1

        # for use as module:
        fig, figname = ipmag.ani_depthplot2(ani_file, meas_file, samp_file, age_file, sum_file, fmt, float(dmin), float(dmax), depth_scale)
        if fig:
            self.Destroy()
            dpi = fig.get_dpi()
            pixel_width = dpi * fig.get_figwidth()
            pixel_height = dpi * fig.get_figheight()
            del wait
            plot_frame = PlotFrame((pixel_width, pixel_height + 50), fig, figname)
        else:
            del wait
            pw.simple_warning("No data points met your criteria - try again\nError message: {}".format(figname))


    def on_cancelButton(self,event):
        self.Destroy()
        self.Parent.Raise()

    def on_helpButton(self, event):
        pw.on_helpButton(text=ipmag.ani_depthplot2.__doc__)




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
        self.bSizer1 = pw.specimen_n(pnl)

        #---sizer 2 ---
        self.bSizer2 = pw.select_ncn(pnl)

        #---sizer 3 ---
        self.bSizer3 = pw.labeled_text_field(pnl, label="Location name:")

        #---sizer 4 ---



        #---sizer 4 ----
        #try:
        #    open(self.WD + "/er_samples.txt", "r")
        #except Exception as ex:
        #    er_samples_file_present = False
        #if er_samples_file_present:
        #    self.bSizer4 = pw.labeled_yes_or_no(pnl, TEXT, label1, label2)

        #---buttons ---
        hboxok = pw.btn_panel(self, pnl)

        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.LEFT, border=5)
        hbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(hbox, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #try:
        #    vbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #except AttributeError:
        #    pass
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)
        vbox.AddSpacer(20)

        hbox_all = wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.Add(vbox)

        self.panel.SetSizer(hbox_all)
        self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()

    def on_add_file_button(self,event):
        text = "choose file to convert to MagIC"
        pw.on_add_file_button(self.bSizer0, text)

    def on_okButton(self, event):
        os.chdir(self.WD)
        COMMAND = ""
        print(COMMAND)
        #pw.run_command_and_close_window(self, COMMAND, "er_samples.txt")

    def on_cancelButton(self,event):
        self.Destroy()
        self.Parent.Raise()

    def on_helpButton(self, event):
        pw.on_helpButton(text='')






# File

class ClearWD(wx.MessageDialog):

    def __init__(self, parent, WD):
        msg = "Are you sure you want to delete the contents of:\n{} ?\nThis action cannot be undone".format(WD)
        super(ClearWD, self).__init__(None, caption="Not so fast", message=msg, style=wx.YES_NO|wx.NO_DEFAULT|wx.ICON_EXCLAMATION)
        self.WD = WD

    def do_clear(self):
        result = self.ShowModal()
        self.Destroy()
        if result == wx.ID_YES:
            os.chdir('..')
            import shutil
            shutil.rmtree(self.WD)
            os.mkdir(self.WD)
            os.chdir(self.WD)
            return True
        else:
            print("{} has not been emptied".format(self.WD))
            return False


#consider using this instead (will preserve permissions of directory, but this may or may not be crucial)
#def emptydir(top):
#    if(top == '/' or top == "\\"): return
#    else:
#        for root, dirs, files in os.walk(top, topdown=False):
#            for name in files:
#                os.remove(os.path.join(root, name))
#            for name in dirs:
#                os.rmdir(os.path.join(root, name))


class PlotFrame(wx.Frame):
    def __init__(self, size, figure, figname, standalone=False):
        super(PlotFrame, self).__init__(None, -1, size=size)
        self.figure = figure
        self.figname = figname
        self.standalone = standalone
        panel = wx.Panel(self, -1)
        canvas = FigureCanvas(panel, -1, self.figure)
        btn_panel = self.make_btn_panel(panel)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(canvas, 1, wx.LEFT | wx.TOP | wx.GROW) # having/removing wx.GROW doesn't matter
        sizer.Add(btn_panel, flag=wx.CENTRE|wx.ALL, border=5)
        panel.SetSizer(sizer)
        sizer.Fit(panel) # MIGHT HAVE TO TAKE THIS LINE OUT!!!
        self.Centre()
        self.Show()


    def make_btn_panel(self, parent):
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        btn_save = wx.Button(parent, -1, "Save plot")
        self.Bind(wx.EVT_BUTTON, self.on_save, btn_save)
        btn_discard = wx.Button(parent, -1, "Discard plot")
        self.Bind(wx.EVT_BUTTON, self.on_discard, btn_discard)
        hbox.AddMany([(btn_save, 1, wx.RIGHT, 5), (btn_discard)])
        return hbox

    def on_save(self, event):
        plt.savefig(self.figname)
        plt.clf() # clear figure
        dir_path, figname = os.path.split(self.figname)
        if not dir_path:
            dir_path = os.getcwd()
        dir_path = os.path.abspath(dir_path)
        dlg = wx.MessageDialog(None, message="Plot saved in directory:\n{}\nas {}".format(dir_path, figname), style=wx.OK)
        dlg.ShowModal()
        dlg.Destroy()
        self.Destroy()
        if self.standalone:
            sys.exit()

    def on_discard(self, event):
        dlg = wx.MessageDialog(self, "Are you sure you want to delete this plot?", "Not so fast", style=wx.YES_NO|wx.NO_DEFAULT|wx.ICON_EXCLAMATION)
        response = dlg.ShowModal()
        if response == wx.ID_YES:
            plt.clf() # clear figure
            dlg.Destroy()
            self.Destroy()
            if self.standalone:
                sys.exit()

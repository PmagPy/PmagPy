#!/usr/bin/env pythonw
# -*- coding: utf-8 -*-
import wx
import sys
import os
import scipy
from scipy import *
# need to set matplotlib backend to WXAgg or else the program just hangs
import matplotlib
matplotlib.use('WXAgg')
from pmagpy import pmag
from pmagpy import convert_2_magic as convert
from pmagpy import contribution_builder as cb
from dialogs import pmag_widgets as pw
from pmagpy import ipmag


# ------


# ===========================================
# GUI
# ===========================================


class convert_livdb_files_to_MagIC(wx.Frame):
    """"""
    title = "Convert Livdb files to MagIC format"

    def __init__(self, WD):
        wx.Frame.__init__(self, None, wx.ID_ANY, self.title)
        self.panel = wx.Panel(self)
        self.max_files = 10
        self.WD = WD
        self.create_menu()
        self.InitUI()
        self.data_model_num = int(pmag.get_named_arg("-DM", 3))

        if "-WD" in sys.argv:
            ind = sys.argv.index('-WD')
            self.WD = sys.argv[ind+1]
        else:
            self.WD = "."
        self.WD = os.path.realpath(self.WD)
        os.chdir(self.WD)


    def create_menu(self):
        """ Create menu
        """
        self.menubar = wx.MenuBar()

        menu_about = wx.Menu()
        menu_help = menu_about.Append(-1, "&Some notes", "")
        self.Bind(wx.EVT_MENU, self.on_menu_help, menu_help)

        self.menubar.Append(menu_about, "& Instructions")

        self.SetMenuBar(self.menubar)

    def on_menu_help(self, event):

        dia = message_box("Instructions")
        dia.Show()
        dia.Center()

    def InitUI(self):

        pnl = self.panel

        # ---sizer infor ----

        TEXT1 = "Instructions:\n"
        TEXT2 = "Put all livdb files of the same Location in one folder\n"
        TEXT3 = "If there is a more than one location, use multiple folders\n"
        TEXT4 = "Each measurement file must end with '.livdb' or .livdb.csv\n"

        TEXT = TEXT1+TEXT2+TEXT3+TEXT4
        bSizer_info = wx.StaticBoxSizer(wx.StaticBox(
            self.panel, wx.ID_ANY, ""), wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        # ---sizer 1 ----
        TEXT = "File:\n Choose a working directory path\n No spaces are allowed in path"
        bSizer1 = wx.StaticBoxSizer(wx.StaticBox(
            self.panel, wx.ID_ANY, ""), wx.VERTICAL)
        bSizer1.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_TOP)
        bSizer1.AddSpacer(5)
        self.dir_paths = {}
        self.add_dir_btns = {}
        self.bSizers_1 = {}
        self.bSizers_2 = {}
        for i in range(self.max_files):
            self.dir_paths[i] = wx.TextCtrl(self.panel, id=-1, size=(200,25), style=wx.TE_READONLY)
            self.add_dir_btns[i] = wx.Button(self.panel, id=-1, label='add',name='add_{}'.format(i))
            self.Bind(wx.EVT_BUTTON, self.on_add_dir_button_i, self.add_dir_btns[i])
            self.bSizers_1[i] = wx.BoxSizer(wx.HORIZONTAL)
            self.bSizers_1[i].Add(wx.StaticText(pnl,label=('{}  '.format(i)[:2])),wx.ALIGN_LEFT)
            self.bSizers_1[i].Add(self.dir_paths[i], wx.ALIGN_LEFT)
            self.bSizers_1[i].Add(self.add_dir_btns[i], wx.ALIGN_LEFT)
            bSizer1.Add(self.bSizers_1[i], wx.ALIGN_TOP)
            bSizer1.AddSpacer(5)

        # ---sizer 2 ----

        TEXT = "\nLocation:\n"
        bSizer2 = wx.StaticBoxSizer(wx.StaticBox(
            self.panel, wx.ID_ANY, ""), wx.VERTICAL)
        bSizer2.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_TOP)
        bSizer2.AddSpacer(5)
        self.file_locations = {}
        for i in range(self.max_files):
            self.file_locations[i] = wx.TextCtrl(self.panel, id=-1, size=(60,25))
            bSizer2.Add(self.file_locations[i], wx.ALIGN_TOP)
            bSizer2.AddSpacer(5)

# ---sizer 3 ----
##
# missing

        # ---sizer 4 ----

        TEXT = "\nSample-specimen\nnaming convention:"
        bSizer4 = wx.StaticBoxSizer(wx.StaticBox(
            self.panel, wx.ID_ANY, ""), wx.VERTICAL)
        bSizer4.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_TOP)
        self.sample_naming_conventions = [
            'sample=specimen', 'no. of terminate characters', 'character delimited']
        bSizer4.AddSpacer(5)
        self.naming_con_boxes = {}
        self.naming_con_char = {}
        for i in range(self.max_files):
            self.naming_con_boxes[i] = wx.ComboBox(self.panel, -1, self.sample_naming_conventions[0], size=(180,25), choices=self.sample_naming_conventions, style=wx.CB_DROPDOWN)
            self.naming_con_char[i] = wx.TextCtrl(self.panel, id=-1, size=(40,25))
            bSizer = wx.BoxSizer(wx.HORIZONTAL)
            bSizer.Add(self.naming_con_boxes[i], wx.ALIGN_LEFT)
            bSizer.Add(self.naming_con_char[i], wx.ALIGN_LEFT)
            bSizer4.Add(bSizer, wx.ALIGN_TOP)
            bSizer4.AddSpacer(5)

        # ---sizer 5 ----

        TEXT = "\nSite-sample\nnaming convention:"
        bSizer5 = wx.StaticBoxSizer(wx.StaticBox(
            self.panel, wx.ID_ANY, ""), wx.VERTICAL)
        bSizer5.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_TOP)
        self.site_naming_conventions = [
            'site=sample', 'no. of terminate characters', 'character delimited']
        bSizer5.AddSpacer(5)
        self.site_name_conventions = {}
        self.site_name_chars = {}
        for i in range(self.max_files):
            self.site_name_chars[i] = wx.TextCtrl(self.panel, id=-1, size=(40,25))
            self.site_name_conventions[i] = wx.ComboBox(self.panel, -1, self.site_naming_conventions[0], size=(180,25), choices=self.site_naming_conventions, style=wx.CB_DROPDOWN)
            bSizer = wx.BoxSizer(wx.HORIZONTAL)
            bSizer.Add(self.site_name_conventions[i], wx.ALIGN_LEFT)
            bSizer.Add(self.site_name_chars[i], wx.ALIGN_LEFT)
            bSizer5.Add(bSizer, wx.ALIGN_TOP)
            bSizer5.AddSpacer(5)

        # ------------------

        self.okButton = wx.Button(self.panel, wx.ID_OK, "&OK")
        self.Bind(wx.EVT_BUTTON, self.on_okButton, self.okButton)

        self.cancelButton = wx.Button(self.panel, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)

        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        # hbox1.Add(self.add_file_button)
        #hbox1.Add(self.remove_file_button )

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2.Add(self.okButton)
        hbox2.Add(self.cancelButton)

        # ------

        vbox = wx.BoxSizer(wx.VERTICAL)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.AddSpacer(5)
        hbox.Add(bSizer1, flag=wx.ALIGN_LEFT)
        hbox.AddSpacer(5)
        hbox.Add(bSizer2, flag=wx.ALIGN_LEFT)
        hbox.AddSpacer(5)
##        hbox.Add(bSizer3, flag=wx.ALIGN_LEFT)
# hbox.AddSpacer(5)
        hbox.Add(bSizer4, flag=wx.ALIGN_LEFT)
        hbox.AddSpacer(5)
        hbox.Add(bSizer5, flag=wx.ALIGN_LEFT)
        hbox.AddSpacer(5)

        # -----

        vbox.AddSpacer(20)
        vbox.Add(bSizer_info, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(20)
        vbox.Add(hbox)
        vbox.AddSpacer(20)
        vbox.Add(hbox1, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(20)
        vbox.Add(hbox2, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(20)

        self.panel.SetSizer(vbox)
        vbox.Fit(self)
        self.Show()
        self.Centre()

    def on_add_dir_button_i(self, event):

        dlg = wx.DirDialog(
            None, message="choose directory with livdb files",
            defaultPath=self.WD,
            style=wx.FD_OPEN | wx.FD_CHANGE_DIR
        )
        if dlg.ShowModal() == wx.ID_OK:
            FILE = dlg.GetPath()
        # fin=open(FILE,'r')
        button = event.GetEventObject()
        name = button.GetName()
        i = int((name).split("_")[-1])
        # print "The button's name is " + button.GetName()

        self.dir_paths[i].SetValue(FILE)

    def read_generic_file(self, path):
        Data = {}
        Fin = open(path, 'r')
        header = Fin.readline().strip('\n').split('\t')

        for line in Fin.readlines():
            tmp_data = {}
            l = line.strip('\n').split('\t')
            if len(l) < len(header):
                continue
            else:
                for i in range(len(header)):
                    tmp_data[header[i]] = l[i]
                specimen = tmp_data['Specimen']
                if specimen not in list(Data.keys()):
                    Data[specimen] = []
                # check dupliactes
                if len(Data[specimen]) > 0:
                    if tmp_data['Treatment (aka field)'] == Data[specimen][-1]['Treatment (aka field)']:
                        print("-W- WARNING: duplicate measurements specimen %s, Treatment %s. keeping onlt the last one" %
                              (tmp_data['Specimen'], tmp_data['Treatment (aka field)']))
                        Data[specimen].pop()

                Data[specimen].append(tmp_data)
        return(Data)

    def on_okButton(self, event):

        meas_files = []
        spec_files = []
        samp_files = []
        site_files = []
        loc_files = []

        for i in range(self.max_files):

            # read directory path
            dirpath = self.dir_paths[i].GetValue()
            if dirpath != "":
                dir_name = os.path.realpath(dirpath)
                #dir_name = str(dirpath.split("/")[-1])
            else:
                continue

            # get location
            location_name = self.file_locations[i].GetValue()
            # get sample-specimen naming convention
            samp_con = str(self.naming_con_boxes[i].GetValue())
            samp_chars = str(self.naming_con_char[i].GetValue())
            samp_chars = samp_chars.strip('"').strip("'")
            if samp_con == "character delimited" and not samp_chars:
                pw.simple_warning("To delimit samples by character, you must provide the delimiter, (eg. \"-\" or \"_\")!")
                return
            # get site-sample naming convention
            site_con = str(self.site_name_conventions[i].GetValue())
            site_chars = str(self.site_name_chars[i].GetValue())
            site_chars = site_chars.strip('"').strip("'")
            if site_con == "character delimited" and not site_chars:
                pw.simple_warning("To delimit sites by character, you must provide the delimiter, (eg. \"-\" or \"_\")!")
                return

            # name output files
            if self.data_model_num == 2:
                meas_out = "magic_measurements_{}.txt".format(i)
                spec_out = "er_specimens_{}.txt".format(i)
                samp_out = "er_samples_{}.txt".format(i)
                site_out = "er_sites_{}.txt".format(i)
                loc_out = "er_locations_{}.txt".format(i)
            else:
                meas_out = "measurements_{}.txt".format(i)
                spec_out = "specimens_{}.txt".format(i)
                samp_out = "samples_{}.txt".format(i)
                site_out = "sites_{}.txt".format(i)
                loc_out = "locations_{}.txt".format(i)
            # do conversion

            convert.livdb(dir_name, self.WD, meas_out, spec_out,
                          samp_out, site_out, loc_out,
                          samp_con, samp_chars, site_con,
                          site_chars, location_name)
            meas_files.append(meas_out)
            spec_files.append(spec_out)
            samp_files.append(samp_out)
            site_files.append(site_out)
            loc_files.append(loc_out)

        if self.data_model_num == 2:
            res = ipmag.combine_magic(meas_files, "magic_measurements.txt", 2)
            ipmag.combine_magic(spec_files, "er_specimens.txt", 2)
        else:
            res = ipmag.combine_magic(meas_files, "measurements.txt", 3)
            ipmag.combine_magic(spec_files, "specimens.txt", 3)
            ipmag.combine_magic(samp_files, "samples.txt", 3)
            ipmag.combine_magic(site_files, "sites.txt", 3)
            ipmag.combine_magic(loc_files, "locations.txt", 3)


        pmag.remove_files(meas_files)
        pmag.remove_files(spec_files)
        pmag.remove_files(samp_files)
        pmag.remove_files(site_files)
        pmag.remove_files(loc_files)
        if res:
            self.after_convert_dia()
        else:
            pw.simple_warning("Something when wrong with one or more of your files.\nSee Terminal/Command Prompt output for more details")


    def after_convert_dia(self):
        dlg1 = wx.MessageDialog(
            None, caption="Message:", message="file converted!\n you can try running thellier gui...\n", style=wx.OK | wx.ICON_INFORMATION)
        dlg1.ShowModal()
        dlg1.Destroy()
        self.Destroy()


    def on_cancelButton(self, event):
        self.Destroy()




class message_box(wx.Frame):
    """"""

    # ----------------------------------------------------------------------
    def __init__(self, title):
        wx.Frame.__init__(self, parent=None, size=(1000, 500))

        self.panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.text_log = wx.TextCtrl(
            self.panel, id=-1, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
        self.sizer.Add(self.text_log, 1, wx.EXPAND)
        TEXT = '''
            #--------------------------------------
            #
            # Livdb Database structure
            #
            # HEADER:
            # 1) First line is the header.
            #    The header includes 19 fields delimited by comma (',')
            #    Notice: space is not a delimiter !
            #    In the list below the delimiter is not used, and the concersion script assumes comma delimited file
            #
            # Header fields:
            # Sample code (string): (delimiter = space+)
            # Sample Dip (degrees): (delimiter = space)
            # Sample Dec (degrees): (delimiter = space)
            # Height (meters): (delimiter = space)
            # Position (no units): (delimiter = space)
            # Thickness (meters): (delimiter = space)
            # Unit Dip (aka tilt) (degrees): (delimiter = space)
            # Unit Dip Direction (aka Direction) (degrees): (delimiter = space)
            # Site Latitude (decimal degrees): (delimiter = space)
            # Site Longitude (decimal degrees): (delimiter = space)
            # Experiment Type (string): (delimiter = |)
            # Name of measurer (string): (delimiter = |)
            # Magnetometer name  (string): (delimiter = |)
            # Demagnetiser name  (string): (delimiter = |)
            # Specimen/Experiment Comment  (string): (delimiter = |)
            # Database version (integer): (delimiter = |)
            # Conversion Version (string): (delimiter = |)
            # Sample Volume (cc): (delimiter = |)
            # Sample Density  (kg/m^3): (delimiter = |)
            #
            #
            # BODY:
            # 1) Body includes 22 fields delimited by comma (',')
            # 2) Body ends with an "END" statment
            #
            # Body fields:
            # Treatment (aka field) (mT / deg C / 10-2 W): (delimiter = space)
            # Microwave Power (W) : (delimiter = space)
            # Microwave Time (s) : (delimiter = space)
            # X (nAm^2): (delimiter = space)
            # Y (nAm^2): (delimiter = space)
            # Z (nAm^2): (delimiter = space)
            # Mass g: (delimiter = space)
            # Applied field intensity (micro_T): (delimiter = space)
            # Applied field Dec (degrees): (delimiter = space)
            # Applied Field Inc (degrees): (delimiter = space)
            # Measurement Date (DD-MM-YYYY)  or (DD/MM/YYYY) #### CHECK !! ## (delimiter = |)
            # Measurement Time (HH:SS:MM) (delimiter = |)
            # Measurement Remark (string) (delimiter = |)
            # Step Number (integer) (delimiter = |)
            # Step Type (string) (Z/I/P/T/O/NRM) (delimiter = |)
            # Tristan Gain (integer) (delimiter = |)
            # Microwave Power Integral (W.s) (delimiter = |)
            # JR6 Error(percent %) (delimiter = |)
            # FiT Smm (?) (delimiter = |)
            # Utrecht Error (percent %) (delimiter = |)
            # AF Demag/Remag Peak Field (mT) (delimiter = |)
            # TH Demag/Remag Peak Temperature (deg C) (delimiter = |)
            # -------------------------------------------------------------


            #--------------------------------------
            # Important assumptions:
            # (1) The program checks if the same treatment appears more than once (a measurement is repeated twice).
            #       If yes, then it takes only the second one and ignores the first.
            # (2) –99 and 999 are codes for N/A
            # (3) The "treatment step" for Thermal Thellier experiment is taken from the "TH Demag/Remag Peak Temperature"
            # (4) The "treatment step" for Microwave Thellier experiment is taken from the "Step Number"
            # (5) As there might be contradiction between the expected treatment (i.e. Z,I,P,T,A assumed by the experiment type)
            #       and "Step Type" field due to typos or old file formats:
            #       The program concludes the expected treatment from the following:
            #       ("Experiment Type) + ("Step Number" or "TH Demag/Remag Peak Temperature") + (the order of the measurements).
            #       The conversion script will spit out a WARNING message in a case of contradiction.
            # (6) If the program finds AF demagnetization before the infield ot zerofield steps:
            #       then assumes that this is an AFD step domne before the experiment.
            # (7) The prgram ignores microwave fields (aka field,Microwave Power,Microwave Time) in Thermal experiments. And these fields will not be converted
            #     to MagIC.
            # (8) NRM step: NRM step is regonized either by "Applied field intensity"=0 and "Applied field Dec" =0 and "Applied Field Inc"=0
            #               or if "Step Type" = NRM
            #
            #
            #
            # -------------------------------------------------------------


            #--------------------------------------
            # Script was tested on the following protocols:
            # TH-PI-IZZI+ [November 2013, rshaar]
            # MW-PI-C++ [November 2013, rshaar]
            # MW-PI-IZZI+ ]November 2013, rshaar]
            #
            # Other protocols should be tested before use.
            #
            #
            #
            # -------------------------------------------------------------
            '''

        self.text_log.AppendText(TEXT)
        self.panel.SetSizer(self.sizer)



    # ===========================================
    # Convert to MagIC format
    # ===========================================





"""
NAME
    livdb_magic.py

DESCRIPTION
    converts Livdb format files to magic_measurements format files


"""


def main():
    if '-h' in sys.argv:
        print("Convert Livdb files to MagIC format")
        sys.exit()
    app = wx.App()
    app.frame = convert_livdb_files_to_MagIC("./")
    app.frame.Show()
    app.frame.Center()
    app.MainLoop()


if __name__ == '__main__':
    main()


# main()

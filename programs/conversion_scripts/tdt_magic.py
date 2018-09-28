#!/usr/bin/env pythonw
# -*- coding: utf-8 -*-
"""
NAME
    tdt_magic.py

DESCRIPTION
    converts TDT formatted files to measurements format files

SYNTAX
    tdt_magic.py -WD <PATH>

INPUT:
    TDT formatted files with suffix .tdt

OUTPUT:
    combined measurement file saved in <PATH>


Log:
    Initial revision 4/24/2014
    some bug fix 06/12/2015
"""
# setting backend to wx somehow prevents this import from hanging
import matplotlib
matplotlib.use('WXAgg')

import wx
import sys
import os
from dialogs import pmag_widgets as pw
from pmagpy import convert_2_magic as convert
import pmagpy.contribution_builder as cb
import pmagpy.pmag as pmag
from pmagpy import ipmag
from pmagpy import convert_2_magic

# ===========================================
# GUI
# ===========================================


class convert_tdt_files_to_MagIC(wx.Frame):
    """"""
    title = "Convert tdt files to MagIC format"

    def __init__(self, WD, noave=False):
        wx.Frame.__init__(self, None, wx.ID_ANY, self.title)
        self.panel = wx.Panel(self)
        self.max_files = 10

        os.chdir(WD)
        self.WD = os.getcwd()+"/"
        self.noave = noave
        self.create_menu()
        self.InitUI()

    def InitUI(self):

        pnl = self.panel

        # ---sizer infor ----

        TEXT1 = "Instructions:\n"
        TEXT2 = "1. Put all individual tdt files from the same location in one folder.\n"
        TEXT3 = "   Each tdt file file should end with '.tdt'\n"
        TEXT4 = "2. If there are more than one location use multiple folders. One folder for each location.\n"
        TEXT5 = "3. If the magnetization in in units are mA/m (as in the original TT program) volume is required to convert to moment.\n\n"
        TEXT6 = "For more information check the help menubar option.\n"

        TEXT7 = "(for support contact ron.shaar@mail.huji.ac.il)"

        TEXT = TEXT1+TEXT2+TEXT3+TEXT4+TEXT5+TEXT6+TEXT7
        bSizer_info = wx.StaticBoxSizer(wx.StaticBox(
            self.panel, wx.ID_ANY, ""), wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        # ---sizer 0 ----
        TEXT = "output file:"
        bSizer0 = wx.StaticBoxSizer(wx.StaticBox(
            self.panel, wx.ID_ANY, ""), wx.VERTICAL)
        bSizer0.Add(wx.StaticText(self.panel, label=TEXT), wx.ALIGN_LEFT)
        bSizer0.AddSpacer(5)
        self.output_file_path = wx.TextCtrl(self.panel, id=-1, size=(1000, 25))
        # self.output_file_path.SetEditable(False)
        bSizer0.Add(self.output_file_path, wx.ALIGN_LEFT)
        self.output_file_path.SetValue(
            os.path.join(self.WD, "measurements.txt"))
        # ---sizer 1 ----
        TEXT = "\n choose a path\n with no spaces in name"
        bSizer1 = wx.StaticBoxSizer(wx.StaticBox(
            self.panel, wx.ID_ANY, ""), wx.VERTICAL)
        bSizer1.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_TOP)
        bSizer1.AddSpacer(5)

        self.dir_paths = {}
        self.add_dir_buttons = {}
        self.bsizers = {}
        for i in range(self.max_files):
            self.dir_paths[i] = wx.TextCtrl(
                self.panel, id=-1, size=(100, 25), style=wx.TE_READONLY)
            self.add_dir_buttons[i] = wx.Button(
                self.panel, id=-1, label='add', name='add_{}'.format(i))
            self.Bind(wx.EVT_BUTTON, self.on_add_dir_button,
                      self.add_dir_buttons[i])
            self.bsizers[i] = wx.BoxSizer(wx.HORIZONTAL)
            self.bsizers[i].Add(wx.StaticText(
                pnl, label=('{}  '.format(i+1))), wx.ALIGN_LEFT)
            self.bsizers[i].Add(self.dir_paths[i], wx.ALIGN_LEFT)
            self.bsizers[i].Add(self.add_dir_buttons[i], wx.ALIGN_LEFT)
            bSizer1.Add(self.bsizers[i], wx.ALIGN_TOP)
            bSizer1.AddSpacer(5)

        # ---sizer 1a ----

        TEXT = "\n\nexperiment:"
        bSizer1a = wx.StaticBoxSizer(wx.StaticBox(
            self.panel, wx.ID_ANY, ""), wx.VERTICAL)
        bSizer1a.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_TOP)
        self.experiments_names = ['Thellier', 'ATRM 6 positions', 'NLT']
        bSizer1a.AddSpacer(5)
        self.protocol_infos = {}
        for i in range(self.max_files):
            self.protocol_infos[i] = wx.ComboBox(self.panel, -1, self.experiments_names[0], size=(
                100, 25), choices=self.experiments_names, style=wx.CB_DROPDOWN | wx.CB_READONLY)
            bSizer1a.Add(self.protocol_infos[i], wx.ALIGN_TOP)
            bSizer1a.AddSpacer(5)

        # ---sizer 1b ----

        TEXT = "\nBlab direction\n dec, inc: "
        bSizer1b = wx.StaticBoxSizer(wx.StaticBox(
            self.panel, wx.ID_ANY, ""), wx.VERTICAL)
        bSizer1b.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_TOP)
        bSizer1b.AddSpacer(5)
        self.file_info_Blab_dec = {}
        self.file_info_Blab_inc = {}
        self.bsizers_Blab = {}
        for i in range(self.max_files):
            self.file_info_Blab_dec[i] = wx.TextCtrl(
                self.panel, id=-1, size=(40, 25))
            self.file_info_Blab_dec[i].SetValue('0')
            self.file_info_Blab_inc[i] = wx.TextCtrl(
                self.panel, id=-1, size=(40, 25))
            self.file_info_Blab_inc[i].SetValue('90')
            self.bsizers_Blab[i] = wx.BoxSizer(wx.HORIZONTAL)
            self.bsizers_Blab[i].Add(self.file_info_Blab_dec[i], wx.ALIGN_LEFT)
            self.bsizers_Blab[i].Add(self.file_info_Blab_inc[i], wx.ALIGN_LEFT)
            bSizer1b.Add(self.bsizers_Blab[i], wx.ALIGN_TOP)
            bSizer1b.AddSpacer(5)

        # ---sizer 1c ----

        TEXT = "\nmoment\nunits:"
        bSizer1c = wx.StaticBoxSizer(wx.StaticBox(
            self.panel, wx.ID_ANY, ""), wx.VERTICAL)
        bSizer1c.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_TOP)
        self.moment_units_names = ['mA/m', 'emu', 'Am^2']
        bSizer1c.AddSpacer(5)
        self.moment_units = {}
        for i in range(self.max_files):
            self.moment_units[i] = wx.ComboBox(self.panel, -1, self.moment_units_names[0], size=(
                80, 25), choices=self.moment_units_names, style=wx.CB_DROPDOWN | wx.CB_READONLY)
            bSizer1c.Add(self.moment_units[i], wx.ALIGN_TOP)
            bSizer1c.AddSpacer(5)

        # ---sizer 1d ----

        TEXT = "\nvolume\n[cc]:"
        bSizer1d = wx.StaticBoxSizer(wx.StaticBox(
            self.panel, wx.ID_ANY, ""), wx.VERTICAL)
        bSizer1d.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_TOP)
        bSizer1d.AddSpacer(5)
        self.volumes = {}
        for i in range(self.max_files):
            self.volumes[i] = wx.TextCtrl(self.panel, id=-1, size=(80, 25))
            self.volumes[i].SetValue('12.')
            bSizer1d.Add(self.volumes[i], wx.ALIGN_TOP)
            bSizer1d.AddSpacer(5)

        # ---sizer 1e ----

        TEXT = "\nuser\nname:"
        bSizer1e = wx.StaticBoxSizer(wx.StaticBox(
            self.panel, wx.ID_ANY, ""), wx.VERTICAL)
        bSizer1e.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_TOP)
        bSizer1e.AddSpacer(5)
        self.file_info_users = {}
        for i in range(self.max_files):
            self.file_info_users[i] = wx.TextCtrl(
                self.panel, id=-1, size=(60, 25))
            bSizer1e.Add(self.file_info_users[i], wx.ALIGN_TOP)
            bSizer1e.AddSpacer(5)

        # ---sizer 2 ----

        TEXT = "\nlocation\nname:"
        bSizer2 = wx.StaticBoxSizer(wx.StaticBox(
            self.panel, wx.ID_ANY, ""), wx.VERTICAL)
        bSizer2.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_TOP)
        bSizer2.AddSpacer(5)
        self.file_locations = {}
        for i in range(self.max_files):
            self.file_locations[i] = wx.TextCtrl(
                self.panel, id=-1, size=(60, 25))
            bSizer2.Add(self.file_locations[i], wx.ALIGN_TOP)
            bSizer2.AddSpacer(5)

# ---sizer 3 ----
##
# missing

        # ---sizer 4 ----

        TEXT = "\nsample-specimen\nnaming convention:"
        bSizer4 = wx.StaticBoxSizer(wx.StaticBox(
            self.panel, wx.ID_ANY, ""), wx.VERTICAL)
        bSizer4.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_TOP)
        self.sample_naming_conventions = [
            'sample=specimen', 'no. of terminate characters', 'charceter delimited']
        bSizer4.AddSpacer(5)
        self.sample_naming = {}
        self.sample_naming_char = {}
        self.bSizer4 = {}
        for i in range(self.max_files):
            self.sample_naming[i] = wx.ComboBox(self.panel, -1, self.sample_naming_conventions[0], size=(
                150, 25), choices=self.sample_naming_conventions, style=wx.CB_DROPDOWN | wx.CB_READONLY)
            self.sample_naming_char[i] = wx.TextCtrl(
                self.panel, id=-1, size=(40, 25))
            self.bSizer4[i] = wx.BoxSizer(wx.HORIZONTAL)
            self.bSizer4[i].Add(self.sample_naming[i], wx.ALIGN_LEFT)
            self.bSizer4[i].Add(self.sample_naming_char[i], wx.ALIGN_LEFT)
            bSizer4.Add(self.bSizer4[i], wx.ALIGN_TOP)

            bSizer4.AddSpacer(5)

        # ---sizer 5 ----

        TEXT = "\nsite-sample\nnaming convention:"
        bSizer5 = wx.StaticBoxSizer(wx.StaticBox(
            self.panel, wx.ID_ANY, ""), wx.VERTICAL)
        bSizer5.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_TOP)
        self.site_naming_conventions = [
            'site=sample', 'no. of terminate characters', 'charceter delimited']
        bSizer5.AddSpacer(5)
        self.site_naming = {}
        self.site_naming_char = {}
        self.bSizer5 = {}
        for i in range(self.max_files):
            self.site_naming_char[i] = wx.TextCtrl(
                self.panel, id=-1, size=(40, 25))
            self.site_naming[i] = wx.ComboBox(self.panel, -1, self.site_naming_conventions[0], size=(
                150, 25), choices=self.site_naming_conventions, style=wx.CB_DROPDOWN | wx.CB_READONLY)
            self.bSizer5[i] = wx.BoxSizer(wx.HORIZONTAL)
            self.bSizer5[i].Add(self.site_naming[i])
            self.bSizer5[i].Add(self.site_naming_char[i], wx.ALIGN_LEFT)
            bSizer5.Add(self.bSizer5[i], wx.ALIGN_TOP)
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
        hbox.AddSpacer(1)
        hbox.Add(bSizer1, flag=wx.ALIGN_LEFT)
        hbox.AddSpacer(1)
        hbox.Add(bSizer1a, flag=wx.ALIGN_LEFT)
        hbox.AddSpacer(1)
        hbox.Add(bSizer1b, flag=wx.ALIGN_LEFT)
        hbox.AddSpacer(1)
        hbox.Add(bSizer1c, flag=wx.ALIGN_LEFT)
        hbox.AddSpacer(1)
        hbox.Add(bSizer1d, flag=wx.ALIGN_LEFT)
        hbox.AddSpacer(1)
        hbox.Add(bSizer1e, flag=wx.ALIGN_LEFT)
        hbox.AddSpacer(1)
        hbox.Add(bSizer2, flag=wx.ALIGN_LEFT)
        hbox.AddSpacer(1)
##        hbox.Add(bSizer3, flag=wx.ALIGN_LEFT)
# hbox.AddSpacer(5)
        hbox.Add(bSizer4, flag=wx.ALIGN_LEFT)
        hbox.AddSpacer(1)
        hbox.Add(bSizer5, flag=wx.ALIGN_LEFT)
        hbox.AddSpacer(1)

        # -----

        vbox.AddSpacer(5)
        vbox.Add(bSizer_info, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(2)
        vbox.Add(hbox)
        vbox.AddSpacer(5)
        vbox.Add(hbox1, flag=wx.ALIGN_CENTER_HORIZONTAL)
        # vbox.AddSpacer(20)
        vbox.AddSpacer(5)
        vbox.Add(bSizer0, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.Add(hbox2, flag=wx.ALIGN_CENTER_HORIZONTAL)
        vbox.AddSpacer(5)

        self.panel.SetSizer(vbox)
        vbox.Fit(self)
        self.Show()
        self.Centre()

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

        dia = message_box("Help")
        dia.Show()
        dia.Center()

    def on_add_dir_button(self, event):

        dlg = wx.DirDialog(
            None, message="choose directtory with tdt files",
            defaultPath="./",
            style=wx.FD_OPEN | wx.FD_CHANGE_DIR
        )
        if dlg.ShowModal() == wx.ID_OK:
            FILE = dlg.GetPath()
        else:
            return
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
        Fin.close()
        return(Data)

    def on_okButton(self, event):

        outfiles = []

        for i in range(self.max_files):

            # read directiory path
            dir_path = self.dir_paths[i].GetValue()
            if not os.path.exists(dir_path):
                continue

            # get experiment
            experiment = self.protocol_infos[i].GetValue()

            # get location/user name
            user_name = self.file_info_users[i].GetValue()
            location_name = self.file_locations[i].GetValue()

            # get Blab direction
            lab_dec = self.file_info_Blab_dec[i].GetValue()
            lab_inc = self.file_info_Blab_inc[i].GetValue()

            # get Moment units
            moment_units = self.moment_units[i].GetValue()

            # get sample volume
            volume = self.volumes[i].GetValue()

            # get sample-specimen naming convention
            samp_name_con = str(self.sample_naming[i].GetValue())
            samp_name_chars = str(
                self.sample_naming_char[i].GetValue())

            # get site-sample naming convention
            site_name_con  = str(self.site_naming[i].GetValue())
            site_name_chars = str(
                self.site_naming_char[i].GetValue())

            # create temporary outfile name
            meas_file = os.path.join(self.WD, 'measurements_{}.txt'.format(i))
            spec_file = os.path.join(self.WD, 'specimens_{}.txt'.format(i))
            samp_file = os.path.join(self.WD, 'samples_{}.txt'.format(i))
            site_file = os.path.join(self.WD, 'sites_{}.txt'.format(i))
            loc_file = os.path.join(self.WD, 'locations_{}.txt'.format(i))

            if dir_path:
                res, fname = convert_2_magic.tdt(dir_path, experiment, meas_file,
                                                 spec_file, samp_file,
                                                 site_file, loc_file,
                                                 user_name, location_name, lab_dec, lab_inc, moment_units,
                                                 samp_name_con, samp_name_chars,
                                                 site_name_con, site_name_chars, volume,
                                                 output_dir_path=self.WD)
                outfiles.append(fname)

        # combine measurement files
        ipmag.combine_magic(outfiles, self.output_file_path.GetValue(), magic_table="measurements")
        for fname in outfiles:
            os.remove(os.path.join(self.WD, fname))

        # combine other types of files
        fnames = os.listdir(self.WD)
        for dtype in ['specimens', 'samples', 'sites', 'locations']:
            outfile = os.path.join(self.WD, dtype + ".txt")
            files = [f for f in fnames if dtype + "_" in f]
            ipmag.combine_magic(files, outfile, magic_table=dtype)
            for fname in files:
                os.remove(os.path.join(self.WD, fname))

        if res:
            dlg1 = wx.MessageDialog(None, caption="Message:", message="file converted to {}\n you can try running thellier gui...\n".format(
                self.output_file_path.GetValue()), style=wx.OK | wx.ICON_INFORMATION)
        else:
            dlg1 = wx.MessageDialog(
                None, caption="Warning:", message="No file was created.  Make sure you have selected folders that contain .tdt format files")
        dlg1.ShowModal()
        dlg1.Destroy()
        self.Destroy()


    def on_cancelButton(self, event):
        self.Destroy()


    # ===========================================
    # Convert to MagIC format
    # ===========================================




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
        # -------------------------------------
        #
        # Programs assumptions:
        #
        # 1) Each file contains the data one specimen
        # 2) First line is the header: "Thellier-tdt"
        # 3) Second line in header inlucdes 4 fields:
        #    [Blab] ,['core_azimuth'] , ['core_plunge'] , ['bedding_dip_direction'] , ['bedding_dip']
        # 4) Body includes 5 fields
        #    [specimen_name], [treatments], [moment],[meas_dec],[meas_inc]
        # -------------------------------------
        # Thellier experiment:
        #
        # Tretments: XXX.0 (zerofield)
        #            XXX.1 (infield)
        #            XXX.2 (pTRM check)
        #            XXX.3 (Tail check)
        #            XXX.4 (Additivity check; Krasa et al., 2003)
        #            XXX.5 (Original Thellier-Thellier protocol. )
        #                 (where .5 is for the second direction and .1 in the first)
        # XXX = temperature in degrees
        #
        #
        # 1) If if XXX <50 then assuming that this is NRM (273K)
        # 2) Lab field defaul is Z direction (theta=0, phi=90)
        # 3) The program does not support Thermal demagnetization
        #
        # -------------------------------------
        #
        #   ATRM in six positions
        #
        # Tretments: XXX.0 zerofield
        #            XXX.1 +x
        #            XXX.2 +y
        #            XXX.3 +z
        #            XXX.4 -x
        #            XXX.5 -y
        #            XXX.6 -z
        #            XXX.7 alteration check
        #
        #
        # 1) The program checks if the direction of the magnetization fits the coding above.
        #    If not: an error message will appear
        # 2) Alteration check can be in any direction
        # 3) The order of the measurements is not important
        #
        # For questions and support: rshaar@ucsd.edu
        # -------------------------------------'''

        self.text_log.AppendText(TEXT)
##        fin =open(file_path,'r')
# for line in fin.readlines():
# if "-E-" in line :
# self.text_log.SetDefaultStyle(wx.TextAttr(wx.RED))
# self.text_log.AppendText(line)
# if "-W-" in line:
# self.text_log.SetDefaultStyle(wx.TextAttr(wx.BLACK))
# self.text_log.AppendText(line)
# fin.close()
        # sizer.Fit(self)
        self.panel.SetSizer(self.sizer)


def convert(wd=None, noave=False):
    if not wd:
        WD = os.getcwd()
    else:
        WD = wd
    app = wx.App()
    app.frame = convert_tdt_files_to_MagIC(WD, noave)
    app.frame.Show()
    app.frame.Center()
    app.MainLoop()


def main():
    kwargs = {}
    if '-h' in sys.argv:
        help(__name__)
        sys.exit()
    # if "-WD" in sys.argv:
    #    ind=sys.argv.index("-WD")
    #    kwargs['wd']=sys.argv[ind+1]
    wd = pmag.get_named_arg('-WD', '.')
    kwargs['wd'] = wd
    if "-A" in sys.argv:
        kwargs['noave'] = True
    #convert_tdt_files_to_MagIC(wd, **kwargs)
    convert(**kwargs)


if __name__ == '__main__':
    main()
